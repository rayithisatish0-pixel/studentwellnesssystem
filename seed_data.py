from datetime import datetime, timedelta, timezone
import json
from database import db, User, StudentProfile, MoodLog, AssessmentResult, Appointment, WellnessTip

def seed_database():
    """Seeds the database with the fixed counselor account and initial wellness resources."""
    # 1. Ensure Fixed Counselor Account exists
    counselor_email = "counselor@sereneminds.edu"
    counselor = User.query.filter_by(email=counselor_email).first()
    if not counselor:
        counselor = User(
            email=counselor_email,
            role="counselor"
        )
        counselor.set_password("SecurePassword123!")
        db.session.add(counselor)
        db.session.commit()
    else:
        # Guarantee role and password consistency
        counselor.role = "counselor"
        counselor.set_password("SecurePassword123!")
        db.session.commit()

    # 2. Seed Wellness Tips if table is empty
    if WellnessTip.query.count() == 0:
        tips = [
            WellnessTip(
                title="The 4-7-8 Deep Grounding Breath",
                category="Mindfulness",
                content="Inhale through your nose for 4 counts, hold your breath gently for 7 counts, and exhale completely through your mouth for 8 counts. This stimulates the vagus nerve and activates the parasympathetic calming response.",
                duration="3 min",
                icon="wind"
            ),
            WellnessTip(
                title="Combating Exam Burnout & Overwhelm",
                category="Study Habits",
                content="Use the 50/10 Focus Protocol: Study with zero notifications for 50 minutes, followed by 10 minutes of complete sensory rest (walk, drink water, stretch—no phone screens). This prevents cognitive fatigue.",
                duration="4 min",
                icon="book-open"
            ),
            WellnessTip(
                title="Cognitive Defusion for Anxiety Spikes",
                category="Stress Relief",
                content="When caught in catastrophic thinking ('I will fail everything'), step back and rephrase: 'I notice I am having the thought that I will fail.' Separating your identity from transient thoughts reduces acute anxiety.",
                duration="5 min",
                icon="brain"
            ),
            WellnessTip(
                title="Optimizing Sleep Architecture for Memory",
                category="Sleep",
                content="Consolidate learning by keeping your sleep window consistent. Lower your room temperature to around 67°F (19°C) and avoid blue light at least 45 minutes before sleep to stimulate natural melatonin release.",
                duration="3 min",
                icon="moon"
            ),
            WellnessTip(
                title="5-4-3-2-1 Sensory Grounding Technique",
                category="Physical Wellness",
                content="Acknowledge 5 things you can see, 4 things you can physically touch, 3 sounds you can hear, 2 things you can smell, and 1 positive affirmation you can say to yourself. Excellent for acute panic or racing thoughts.",
                duration="2 min",
                icon="activity"
            )
        ]
        db.session.bulk_save_objects(tips)
        db.session.commit()

    # 3. Seed Realistic Sample Students & Data if fewer than 2 students exist
    # This provides immediate value to test counselor risk detection and queue management
    student_count = User.query.filter_by(role='student').count()
    if student_count < 2:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        sample_students = [
            {
                "email": "elena.vance@sereneminds.edu",
                "password": "Password123!",
                "name": "Elena Vance",
                "student_id": "SM-2026-0814",
                "department": "Computer Science & Engineering",
                "year": "Junior (3rd Year)",
                "phone": "+1 (555) 234-8901",
                "emergency": "Parent: (555) 234-8900",
                # Needs high risk alert
                "mood_data": [
                    {"score": 1, "stress": 9, "sleep": 4.5, "energy": 1, "tags": "Exhausted,Overwhelmed,Anxious", "notes": "Midterms coming up and project deadline is looming. Barely slept.", "days_ago": 3},
                    {"score": 2, "stress": 9, "sleep": 4.0, "energy": 2, "tags": "Anxious,Overwhelmed", "notes": "Constant headaches, feeling isolated and unable to focus.", "days_ago": 2},
                    {"score": 1, "stress": 10, "sleep": 3.5, "energy": 1, "tags": "Exhausted,Burnout,Hopeless", "notes": "Fell asleep in lecture. Feeling completely detached.", "days_ago": 0},
                ],
                "assessment": {
                    "type": "GAD-7 Anxiety",
                    "score": 17,
                    "max": 21,
                    "risk": "Severe / High Risk",
                    "details": {"feeling_nervous": 3, "uncontrollable_worry": 3, "worrying_too_much": 3, "trouble_relaxing": 2, "restless": 2, "easily_annoyed": 2, "feeling_afraid": 2},
                    "recommendations": "Priority counseling intervention recommended. Student reports acute anxiety symptoms and sleep disruption."
                },
                "appointment": {
                    "preferred_date": (now + timedelta(days=1)).strftime("%Y-%m-%d"),
                    "preferred_time_slot": "10:00 AM - 11:00 AM",
                    "category": "Academic Stress & Burnout",
                    "urgency": "Immediate Support",
                    "notes": "I feel like I am collapsing under coursework pressure and need urgent guidance on coping.",
                    "status": "Pending"
                }
            },
            {
                "email": "liam.chen@sereneminds.edu",
                "password": "Password123!",
                "name": "Liam Chen",
                "student_id": "SM-2026-1192",
                "department": "Biomedical Sciences",
                "year": "Sophomore (2nd Year)",
                "phone": "+1 (555) 345-6789",
                "emergency": "Guardian: (555) 345-6780",
                "mood_data": [
                    {"score": 3, "stress": 6, "sleep": 6.5, "energy": 3, "tags": "Focused,Tired", "notes": "Long lab day, manageable.", "days_ago": 4},
                    {"score": 2, "stress": 7, "sleep": 5.5, "energy": 2, "tags": "Anxious,Tired", "notes": "Feeling nervous about upcoming clinical exam.", "days_ago": 2},
                    {"score": 3, "stress": 6, "sleep": 6.0, "energy": 3, "tags": "Calm,Focused", "notes": "Spent time at the library with study group.", "days_ago": 0},
                ],
                "assessment": {
                    "type": "PSS Stress Scale",
                    "score": 19,
                    "max": 40,
                    "risk": "Moderate",
                    "details": {"upset_unexpected": 2, "unable_control": 2, "nervous_stressed": 3, "confident_handle": 2, "things_going_way": 2},
                    "recommendations": "Moderate stress detected. Recommend mindfulness exercises and sleep optimization protocol."
                },
                "appointment": {
                    "preferred_date": (now + timedelta(days=3)).strftime("%Y-%m-%d"),
                    "preferred_time_slot": "02:00 PM - 03:00 PM",
                    "category": "Anxiety & Panic",
                    "urgency": "Standard",
                    "notes": "Would like strategies for managing test anxiety before clinicals.",
                    "status": "Confirmed",
                    "counselor_notes": "Confirmed session. Provided test-taking breathing worksheet.",
                    "meeting_details": "Room 204, Student Wellness Pavilion"
                }
            },
            {
                "email": "maya.lin@sereneminds.edu",
                "password": "Password123!",
                "name": "Maya Lin",
                "student_id": "SM-2026-0428",
                "department": "Psychology & Cognitive Science",
                "year": "Senior (4th Year)",
                "phone": "+1 (555) 987-6543",
                "emergency": "Roommate: (555) 987-6540",
                "mood_data": [
                    {"score": 4, "stress": 4, "sleep": 7.5, "energy": 4, "tags": "Grateful,Calm", "notes": "Finished capstone draft, feeling relieved.", "days_ago": 5},
                    {"score": 5, "stress": 3, "sleep": 8.0, "energy": 5, "tags": "Thriving,Motivated", "notes": "Great morning run and supportive conversation with mentor.", "days_ago": 2},
                    {"score": 4, "stress": 4, "sleep": 7.5, "energy": 4, "tags": "Calm,Focused", "notes": "Good progress on seminar presentation.", "days_ago": 0},
                ],
                "assessment": {
                    "type": "Burnout Index",
                    "score": 6,
                    "max": 30,
                    "risk": "Minimal",
                    "details": {"emotional_exhaustion": 1, "cynicism": 1, "inefficacy": 0},
                    "recommendations": "Student demonstrates high resilience, healthy sleep patterns, and balanced academic workload."
                },
                "appointment": None
            }
        ]

        for s_data in sample_students:
            user = User(email=s_data["email"], role="student")
            user.set_password(s_data["password"])
            db.session.add(user)
            db.session.flush()

            profile = StudentProfile(
                user_id=user.id,
                full_name=s_data["name"],
                student_id=s_data["student_id"],
                department=s_data["department"],
                academic_year=s_data["year"],
                phone=s_data["phone"],
                emergency_contact=s_data["emergency"]
            )
            db.session.add(profile)

            for m in s_data["mood_data"]:
                m_log = MoodLog(
                    user_id=user.id,
                    mood_score=m["score"],
                    sleep_hours=m["sleep"],
                    academic_stress=m["stress"],
                    energy_level=m["energy"],
                    emotion_tags=m["tags"],
                    notes=m["notes"],
                    logged_at=now - timedelta(days=m["days_ago"], hours=m["score"])
                )
                db.session.add(m_log)

            if s_data["assessment"]:
                a_data = s_data["assessment"]
                ass = AssessmentResult(
                    user_id=user.id,
                    assessment_type=a_data["type"],
                    total_score=a_data["score"],
                    max_score=a_data["max"],
                    risk_level=a_data["risk"],
                    details_json=json.dumps(a_data["details"]),
                    recommendations=a_data["recommendations"],
                    created_at=now - timedelta(days=1)
                )
                db.session.add(ass)

            if s_data.get("appointment"):
                app_data = s_data["appointment"]
                appointment = Appointment(
                    user_id=user.id,
                    counselor_id=counselor.id if app_data.get("status") == "Confirmed" else None,
                    preferred_date=app_data["preferred_date"],
                    preferred_time_slot=app_data["preferred_time_slot"],
                    category=app_data["category"],
                    urgency=app_data["urgency"],
                    student_notes=app_data["notes"],
                    status=app_data["status"],
                    counselor_notes=app_data.get("counselor_notes"),
                    meeting_details=app_data.get("meeting_details")
                )
                db.session.add(appointment)

        db.session.commit()
