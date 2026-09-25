import os
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_from_directory
from sqlalchemy import func, desc

def get_utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

from config import Config
from database import db, User, StudentProfile, MoodLog, AssessmentResult, Appointment, WellnessTip
from seed_data import seed_database

def create_app(test_config=None):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, 'templates'),
        static_folder=os.path.join(base_dir, 'static')
    )
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    # Initialize extensions
    db.init_app(app)

    with app.app_context():
        try:
            db.create_all()
            seed_database()
        except Exception as e:
            app.logger.error(f"Database initialization error: {e}")

    # Authentication Decorators
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': 'Authentication required', 'code': 'UNAUTHORIZED'}), 401
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function

    def counselor_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session or session.get('role') != 'counselor':
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': 'Counselor access privileges required', 'code': 'FORBIDDEN'}), 403
                return redirect(url_for('counselor_login'))
            return f(*args, **kwargs)
        return decorated_function

    # =========================================================================
    # Page Template Routes
    # =========================================================================
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/login')
    def login():
        if 'user_id' in session:
            if session.get('role') == 'counselor':
                return redirect(url_for('counselor_dashboard'))
            return redirect(url_for('student_dashboard'))
        return render_template('login.html')

    @app.route('/counselor-login')
    def counselor_login():
        if 'user_id' in session and session.get('role') == 'counselor':
            return redirect(url_for('counselor_dashboard'))
        return render_template('counselor_login.html')

    @app.route('/student/dashboard')
    @login_required
    def student_dashboard():
        if session.get('role') == 'counselor':
            return redirect(url_for('counselor_dashboard'))
        user = db.session.get(User, session['user_id'])
        return render_template('student_dashboard.html', user=user)

    @app.route('/assessment')
    @login_required
    def assessment_page():
        return render_template('assessment.html')

    @app.route('/wellness-hub')
    @login_required
    def wellness_hub():
        return render_template('wellness_hub.html')

    @app.route('/counselor/dashboard')
    @counselor_required
    def counselor_dashboard():
        user = db.session.get(User, session['user_id'])
        return render_template('counselor_dashboard.html', user=user)

    # =========================================================================
    # Auth API Endpoints
    # =========================================================================
    @app.route('/api/auth/register', methods=['POST'])
    def register():
        data = request.get_json() or {}
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        full_name = data.get('full_name', '').strip()
        student_id = data.get('student_id', '').strip()
        department = data.get('department', '').strip()
        academic_year = data.get('academic_year', '').strip()
        phone = data.get('phone', '').strip()
        emergency_contact = data.get('emergency_contact', '').strip()

        if not email or not password or not full_name or not student_id or not department:
            return jsonify({'error': 'Please provide all required fields.'}), 400

        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters.'}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'An account with this email address already exists.'}), 409

        if StudentProfile.query.filter_by(student_id=student_id).first():
            return jsonify({'error': 'A student with this Student ID is already registered.'}), 409

        try:
            new_user = User(email=email, role='student')
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.flush()

            profile = StudentProfile(
                user_id=new_user.id,
                full_name=full_name,
                student_id=student_id,
                department=department,
                academic_year=academic_year or 'Freshman',
                phone=phone,
                emergency_contact=emergency_contact
            )
            db.session.add(profile)
            db.session.commit()

            # Set session
            session['user_id'] = new_user.id
            session['role'] = 'student'
            session['email'] = new_user.email
            session.permanent = True

            return jsonify({
                'message': 'Registration successful! Welcome to Serene Minds.',
                'user': new_user.to_dict(),
                'redirect': url_for('student_dashboard')
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Failed to create account: {str(e)}'}), 500

    @app.route('/api/auth/login', methods=['POST'])
    def login_api():
        data = request.get_json() or {}
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({'error': 'Email and password are required.'}), 400

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid email or password.'}), 401

        session['user_id'] = user.id
        session['role'] = user.role
        session['email'] = user.email
        session.permanent = True

        target_url = url_for('counselor_dashboard') if user.role == 'counselor' else url_for('student_dashboard')
        return jsonify({
            'message': 'Login successful.',
            'user': user.to_dict(),
            'redirect': target_url
        }), 200

    @app.route('/api/auth/counselor-login', methods=['POST'])
    def counselor_login_api():
        """Strict validation for counselor portal credentials."""
        data = request.get_json() or {}
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({'error': 'Counselor email and password are required.'}), 400

        counselor = User.query.filter_by(email=email, role='counselor').first()
        if not counselor or not counselor.check_password(password):
            return jsonify({'error': 'Invalid counselor credentials. Access denied.'}), 401

        session['user_id'] = counselor.id
        session['role'] = 'counselor'
        session['email'] = counselor.email
        session.permanent = True

        return jsonify({
            'message': 'Counselor authentication verified.',
            'user': counselor.to_dict(),
            'redirect': url_for('counselor_dashboard')
        }), 200

    @app.route('/api/auth/logout', methods=['POST', 'GET'])
    def logout():
        session.clear()
        if request.is_json:
            return jsonify({'message': 'Logged out successfully', 'redirect': url_for('index')}), 200
        return redirect(url_for('index'))

    @app.route('/api/auth/me', methods=['GET'])
    def current_user():
        if 'user_id' not in session:
            return jsonify({'authenticated': False, 'user': None}), 200
        user = db.session.get(User, session['user_id'])
        if not user:
            session.clear()
            return jsonify({'authenticated': False, 'user': None}), 200
        return jsonify({'authenticated': True, 'user': user.to_dict()}), 200

    # =========================================================================
    # Student Mood Tracker API
    # =========================================================================
    @app.route('/api/mood/log', methods=['POST'])
    @login_required
    def log_mood():
        data = request.get_json() or {}
        try:
            mood_score = int(data.get('mood_score', 3))
            sleep_hours = float(data.get('sleep_hours', 7.0))
            academic_stress = int(data.get('academic_stress', 5))
            energy_level = int(data.get('energy_level', 3))
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid numerical inputs for mood tracking'}), 400

        emotion_tags = data.get('emotion_tags', [])
        if isinstance(emotion_tags, list):
            emotion_tags_str = ','.join([str(t).strip() for t in emotion_tags if str(t).strip()])
        else:
            emotion_tags_str = str(emotion_tags).strip()

        notes = data.get('notes', '').strip()

        mood_entry = MoodLog(
            user_id=session['user_id'],
            mood_score=max(1, min(5, mood_score)),
            sleep_hours=max(0.0, min(24.0, sleep_hours)),
            academic_stress=max(1, min(10, academic_stress)),
            energy_level=max(1, min(5, energy_level)),
            emotion_tags=emotion_tags_str,
            notes=notes,
            logged_at=get_utc_now()
        )
        db.session.add(mood_entry)
        db.session.commit()

        return jsonify({
            'message': 'Daily mood logged successfully! Thank you for checking in with yourself.',
            'log': mood_entry.to_dict()
        }), 201

    @app.route('/api/mood/history', methods=['GET'])
    @login_required
    def mood_history():
        user_id = session['user_id']
        logs = MoodLog.query.filter_by(user_id=user_id).order_by(MoodLog.logged_at.desc()).limit(30).all()
        
        # Calculate weekly stats
        week_ago = get_utc_now() - timedelta(days=7)
        recent_logs = [l for l in logs if l.logged_at >= week_ago]
        
        avg_mood = round(sum(l.mood_score for l in recent_logs) / len(recent_logs), 1) if recent_logs else 0
        avg_sleep = round(sum(l.sleep_hours for l in recent_logs) / len(recent_logs), 1) if recent_logs else 0
        avg_stress = round(sum(l.academic_stress for l in recent_logs) / len(recent_logs), 1) if recent_logs else 0

        return jsonify({
            'logs': [l.to_dict() for l in logs],
            'stats': {
                'total_logs': len(logs),
                'avg_mood': avg_mood,
                'avg_sleep': avg_sleep,
                'avg_stress': avg_stress
            }
        }), 200

    # =========================================================================
    # Self-Assessment & Surveys API
    # =========================================================================
    @app.route('/api/assessment/submit', methods=['POST'])
    @login_required
    def submit_assessment():
        data = request.get_json() or {}
        assessment_type = data.get('assessment_type', 'GAD-7')
        answers = data.get('answers', {})

        if not answers:
            return jsonify({'error': 'Assessment answers are missing'}), 400

        total_score = 0
        max_score = 21
        risk_level = "Minimal"
        recommendations = ""

        # GAD-7 Anxiety Scale (7 questions, each 0 to 3, total 0-21)
        if assessment_type == 'GAD-7':
            max_score = 21
            for k, val in answers.items():
                try:
                    total_score += int(val)
                except (ValueError, TypeError):
                    pass
            
            if total_score <= 4:
                risk_level = "Minimal"
                recommendations = "Your anxiety levels appear minimal. Continue healthy routines, active rest, and open connections."
            elif total_score <= 9:
                risk_level = "Mild"
                recommendations = "Mild anxiety detected. Daily mindfulness breathing, limiting late caffeine, and regular sleep can help ground your nervous system."
            elif total_score <= 14:
                risk_level = "Moderate"
                recommendations = "Moderate anxiety indicated. Consider scheduling a student counseling session to explore supportive coping tools and academic adjustments."
            else:
                risk_level = "Severe / High Risk"
                recommendations = "Severe anxiety score flagged. We strongly encourage you to book a confidential consultation with our wellness counseling team today. Support is always available."

        # Perceived Stress Scale (PSS-10, scored 0-40)
        elif assessment_type == 'PSS Stress Scale':
            max_score = 40
            for k, val in answers.items():
                try:
                    total_score += int(val)
                except (ValueError, TypeError):
                    pass

            if total_score <= 13:
                risk_level = "Minimal"
                recommendations = "Low perceived stress. You are managing academic and personal demands effectively."
            elif total_score <= 26:
                risk_level = "Moderate"
                recommendations = "Moderate stress levels. Try breaking large study projects into 30-minute intervals and protect your evening wind-down time."
            else:
                risk_level = "Severe / High Risk"
                recommendations = "High perceived stress. Persistent high stress impacts cognitive function and emotional well-being. Please connect with our counselors."

        # Student Academic Burnout Inventory (Scores 0-30)
        elif assessment_type == 'Burnout Index':
            max_score = 30
            for k, val in answers.items():
                try:
                    total_score += int(val)
                except (ValueError, TypeError):
                    pass

            if total_score <= 10:
                risk_level = "Minimal"
                recommendations = "Healthy energy and engagement. Keep honoring your study-life boundaries."
            elif total_score <= 20:
                risk_level = "Moderate"
                recommendations = "Moderate academic fatigue. Make deliberate time for social replenishment and physical activity outside study halls."
            else:
                risk_level = "Severe / High Risk"
                recommendations = "High academic burnout risk detected. It is crucial to rest, speak with an academic advisor, and consult a wellness counselor."

        assessment = AssessmentResult(
            user_id=session['user_id'],
            assessment_type=assessment_type,
            total_score=total_score,
            max_score=max_score,
            risk_level=risk_level,
            details_json=data.get('details_json', '{}'),
            recommendations=recommendations,
            created_at=get_utc_now()
        )
        db.session.add(assessment)
        db.session.commit()

        return jsonify({
            'message': 'Assessment submitted and scored successfully.',
            'result': assessment.to_dict()
        }), 201

    @app.route('/api/assessment/history', methods=['GET'])
    @login_required
    def assessment_history():
        user_id = session['user_id']
        results = AssessmentResult.query.filter_by(user_id=user_id).order_by(AssessmentResult.created_at.desc()).all()
        return jsonify({
            'assessments': [r.to_dict() for r in results]
        }), 200

    # =========================================================================
    # Appointments & Counselor Connection API
    # =========================================================================
    @app.route('/api/appointment/create', methods=['POST'])
    @login_required
    def create_appointment():
        data = request.get_json() or {}
        preferred_date = data.get('preferred_date', '').strip()
        preferred_time_slot = data.get('preferred_time_slot', '').strip()
        category = data.get('category', 'Academic Stress').strip()
        urgency = data.get('urgency', 'Standard').strip()
        student_notes = data.get('student_notes', '').strip()

        if not preferred_date or not preferred_time_slot:
            return jsonify({'error': 'Please select your preferred date and time slot.'}), 400

        appointment = Appointment(
            user_id=session['user_id'],
            preferred_date=preferred_date,
            preferred_time_slot=preferred_time_slot,
            category=category,
            urgency=urgency,
            student_notes=student_notes,
            status='Pending',
            created_at=get_utc_now()
        )
        db.session.add(appointment)
        db.session.commit()

        return jsonify({
            'message': 'Your appointment request has been submitted to the counseling team.',
            'appointment': appointment.to_dict()
        }), 201

    @app.route('/api/appointment/my', methods=['GET'])
    @login_required
    def my_appointments():
        user_id = session['user_id']
        appointments = Appointment.query.filter_by(user_id=user_id).order_by(Appointment.created_at.desc()).all()
        return jsonify({
            'appointments': [a.to_dict() for a in appointments]
        }), 200

    # =========================================================================
    # Personalized Wellness Hub & Tips API
    # =========================================================================
    @app.route('/api/wellness/recommendations', methods=['GET'])
    @login_required
    def personalized_recommendations():
        user_id = session['user_id']
        latest_mood = MoodLog.query.filter_by(user_id=user_id).order_by(MoodLog.logged_at.desc()).first()
        latest_assessment = AssessmentResult.query.filter_by(user_id=user_id).order_by(AssessmentResult.created_at.desc()).first()

        recommendations = []
        is_high_risk = False

        if latest_mood and latest_mood.mood_score <= 2:
            is_high_risk = True
            recommendations.append({
                'title': 'Emotional Grounding & Warm Support',
                'description': 'Your recent check-in shows you are feeling down or overwhelmed. Remember that you do not have to carry this alone.',
                'action_label': 'Book Priority Session',
                'action_target': '#appointment-section',
                'type': 'alert'
            })

        if latest_mood and latest_mood.academic_stress >= 8:
            recommendations.append({
                'title': 'High Academic Pressure Management',
                'description': 'Your stress level was reported as high. Try taking a micro-break using the 4-7-8 breathing circle to reset your nervous system.',
                'action_label': 'Try 4-7-8 Breathwork',
                'action_target': '/wellness-hub#breathing',
                'type': 'practice'
            })

        if latest_mood and latest_mood.sleep_hours < 6.0:
            recommendations.append({
                'title': 'Sleep Restoration Routine',
                'description': 'You reported fewer than 6 hours of sleep. Try dimming lights and listening to calming ambient soundscapes before bed.',
                'action_label': 'Open Soundscapes',
                'action_target': '/wellness-hub#soundscapes',
                'type': 'tip'
            })

        if latest_assessment and 'Severe' in latest_assessment.risk_level:
            is_high_risk = True
            recommendations.insert(0, {
                'title': 'Confidential Counselor Connection Recommended',
                'description': f'Your recent {latest_assessment.assessment_type} scored in the high-risk range. Our campus counselors are available to support you in a safe, confidential environment.',
                'action_label': 'Connect With Counselor',
                'action_target': '#appointment-section',
                'type': 'urgent'
            })

        # Default recommendation if none triggered
        if not recommendations:
            recommendations.append({
                'title': 'Daily Mindfulness Check-In',
                'description': 'Continue your great momentum with daily grounding exercises, intentional hydration, and regular restorative breaks.',
                'action_label': 'Explore Mindfulness Tools',
                'action_target': '/wellness-hub',
                'type': 'practice'
            })

        return jsonify({
            'recommendations': recommendations,
            'is_high_risk': is_high_risk,
            'latest_mood': latest_mood.to_dict() if latest_mood else None,
            'latest_assessment': latest_assessment.to_dict() if latest_assessment else None
        }), 200

    @app.route('/api/wellness/tips', methods=['GET'])
    def wellness_tips():
        tips = WellnessTip.query.all()
        return jsonify({'tips': [t.to_dict() for t in tips]}), 200

    # =========================================================================
    # Counselor / Admin Management API
    # =========================================================================
    @app.route('/api/counselor/overview', methods=['GET'])
    @counselor_required
    def counselor_overview():
        total_students = User.query.filter_by(role='student').count()
        total_mood_logs = MoodLog.query.count()
        pending_appointments = Appointment.query.filter_by(status='Pending').count()
        total_appointments = Appointment.query.count()

        # Flagged students calculation
        # A student is flagged if:
        # 1. Latest mood <= 2, OR
        # 2. Avg of last 3 mood logs < 2.5, OR
        # 3. Any assessment flagged as 'Severe / High Risk', OR
        # 4. Academic stress >= 8 with sleep <= 5 hours
        students = User.query.filter_by(role='student').all()
        flagged_count = 0
        distribution = {'thriving': 0, 'stable': 0, 'vulnerable': 0, 'high_risk': 0}

        for st in students:
            logs = MoodLog.query.filter_by(user_id=st.id).order_by(MoodLog.logged_at.desc()).limit(3).all()
            latest_assessment = AssessmentResult.query.filter_by(user_id=st.id).order_by(AssessmentResult.created_at.desc()).first()

            is_risk = False
            avg_mood = sum(l.mood_score for l in logs) / len(logs) if logs else 3.0

            if (latest_assessment and 'Severe' in latest_assessment.risk_level) or (logs and avg_mood < 2.3) or (logs and logs[0].academic_stress >= 8 and logs[0].sleep_hours <= 5.0):
                is_risk = True
                flagged_count += 1
                distribution['high_risk'] += 1
            elif avg_mood < 3.0:
                distribution['vulnerable'] += 1
            elif avg_mood >= 4.0:
                distribution['thriving'] += 1
            else:
                distribution['stable'] += 1

        # Mood trends over last 7 days
        seven_days_ago = get_utc_now() - timedelta(days=7)
        daily_trends = []
        for i in range(7):
            day_start = (get_utc_now() - timedelta(days=6 - i)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            day_logs = MoodLog.query.filter(MoodLog.logged_at >= day_start, MoodLog.logged_at < day_end).all()
            avg = round(sum(l.mood_score for l in day_logs) / len(day_logs), 2) if day_logs else None
            daily_trends.append({
                'date': day_start.strftime('%a, %b %d'),
                'avg_mood': avg
            })

        # Category distribution of appointments
        categories = db.session.query(Appointment.category, func.count(Appointment.id)).group_by(Appointment.category).all()
        appointment_categories = [{'category': c[0], 'count': c[1]} for c in categories]

        return jsonify({
            'total_students': total_students,
            'total_mood_logs': total_mood_logs,
            'pending_appointments': pending_appointments,
            'total_appointments': total_appointments,
            'flagged_students_count': flagged_count,
            'distribution': distribution,
            'daily_trends': daily_trends,
            'appointment_categories': appointment_categories
        }), 200

    @app.route('/api/counselor/risk-alerts', methods=['GET'])
    @counselor_required
    def counselor_risk_alerts():
        students = User.query.filter_by(role='student').all()
        alerts = []

        for st in students:
            profile = st.profile
            logs = MoodLog.query.filter_by(user_id=st.id).order_by(MoodLog.logged_at.desc()).limit(5).all()
            latest_assessment = AssessmentResult.query.filter_by(user_id=st.id).order_by(AssessmentResult.created_at.desc()).first()

            risk_reasons = []
            if logs:
                recent_avg = sum(l.mood_score for l in logs[:3]) / min(len(logs), 3)
                if recent_avg <= 2.2:
                    risk_reasons.append(f"Persistent low mood score (Avg: {round(recent_avg, 1)}/5)")
                if logs[0].academic_stress >= 8 and logs[0].sleep_hours <= 5:
                    risk_reasons.append(f"Critical stress ({logs[0].academic_stress}/10) & low sleep ({logs[0].sleep_hours}h)")

            if latest_assessment and ('Severe' in latest_assessment.risk_level or latest_assessment.total_score >= 14):
                risk_reasons.append(f"Flagged assessment: {latest_assessment.assessment_type} ({latest_assessment.risk_level})")

            # Check if student has pending urgent appointment
            pending_urgent = Appointment.query.filter_by(user_id=st.id, status='Pending').filter(
                (Appointment.urgency == 'Immediate Support') | (Appointment.urgency == 'Priority')
            ).first()
            if pending_urgent:
                risk_reasons.append(f"Unresolved {pending_urgent.urgency} appointment request")

            if risk_reasons:
                alerts.append({
                    'student_id': profile.student_id if profile else f"SM-{st.id:04d}",
                    'user_id': st.id,
                    'full_name': profile.full_name if profile else st.email.split('@')[0],
                    'email': st.email,
                    'department': profile.department if profile else 'General',
                    'academic_year': profile.academic_year if profile else 'N/A',
                    'reasons': risk_reasons,
                    'severity': 'Critical' if len(risk_reasons) >= 2 else 'Moderate',
                    'last_logged': logs[0].logged_at.strftime('%b %d, %Y') if logs else 'No logs yet',
                    'emergency_contact': profile.emergency_contact if profile else 'None'
                })

        return jsonify({'alerts': alerts}), 200

    @app.route('/api/counselor/appointments', methods=['GET'])
    @counselor_required
    def counselor_appointments():
        status_filter = request.args.get('status')
        urgency_filter = request.args.get('urgency')

        query = Appointment.query
        if status_filter and status_filter != 'All':
            query = query.filter_by(status=status_filter)
        if urgency_filter and urgency_filter != 'All':
            query = query.filter_by(urgency=urgency_filter)

        appointments = query.order_by(Appointment.created_at.desc()).all()
        return jsonify({'appointments': [a.to_dict() for a in appointments]}), 200

    @app.route('/api/counselor/appointments/<int:appointment_id>', methods=['PUT'])
    @counselor_required
    def update_appointment(appointment_id):
        appointment = db.session.get(Appointment, appointment_id)
        if not appointment:
            return jsonify({'error': 'Appointment record not found'}), 404
        data = request.get_json() or {}

        if 'status' in data:
            appointment.status = data['status']
        if 'counselor_notes' in data:
            appointment.counselor_notes = data['counselor_notes']
        if 'meeting_details' in data:
            appointment.meeting_details = data['meeting_details']
        if 'preferred_date' in data:
            appointment.preferred_date = data['preferred_date']
        if 'preferred_time_slot' in data:
            appointment.preferred_time_slot = data['preferred_time_slot']

        appointment.counselor_id = session['user_id']
        appointment.updated_at = get_utc_now()
        db.session.commit()

        return jsonify({
            'message': 'Appointment updated successfully.',
            'appointment': appointment.to_dict()
        }), 200

    @app.route('/api/counselor/student/<int:user_id>/timeline', methods=['GET'])
    @counselor_required
    def student_timeline(user_id):
        student = db.session.get(User, user_id)
        if not student:
            return jsonify({'error': 'Student record not found'}), 404
        profile = student.profile
        logs = MoodLog.query.filter_by(user_id=user_id).order_by(MoodLog.logged_at.desc()).all()
        assessments = AssessmentResult.query.filter_by(user_id=user_id).order_by(AssessmentResult.created_at.desc()).all()
        appointments = Appointment.query.filter_by(user_id=user_id).order_by(Appointment.created_at.desc()).all()

        return jsonify({
            'student': student.to_dict(),
            'mood_logs': [l.to_dict() for l in logs],
            'assessments': [a.to_dict() for a in assessments],
            'appointments': [ap.to_dict() for ap in appointments]
        }), 200

    # Emergency helplines endpoint
    @app.route('/api/emergency/helplines', methods=['GET'])
    def emergency_helplines():
        return jsonify({
            'helplines': [
                {'name': 'Campus Crisis Counseling (24/7)', 'contact': '+1 (800) 273-TALK / Ext 911', 'type': 'Campus'},
                {'name': 'National Suicide & Crisis Lifeline', 'contact': 'Dial 988', 'type': 'National'},
                {'name': 'Crisis Text Line', 'contact': 'Text HOME to 741741', 'type': 'Text'},
                {'name': 'The Trevor Project (LGBTQ+ Youth)', 'contact': '1-866-488-7386', 'type': 'Specialized'},
                {'name': 'Campus Health Center Urgent Care', 'contact': 'Bldg 4, Room 102 | (555) 019-4822', 'type': 'Campus Walk-in'}
            ]
        }), 200

    return app

app = create_app()

if __name__ == '__main__':
    # Local development server
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
