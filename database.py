from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json

def get_utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # 'student' or 'counselor'
    created_at = db.Column(db.DateTime, default=get_utc_now)
    
    # Relationships
    profile = db.relationship('StudentProfile', backref='user', uselist=False, cascade="all, delete-orphan")
    mood_logs = db.relationship('MoodLog', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    assessments = db.relationship('AssessmentResult', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    appointments = db.relationship('Appointment', backref='student', foreign_keys='Appointment.user_id', lazy='dynamic', cascade="all, delete-orphan")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def to_dict(self):
        data = {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
        if self.profile:
            data.update(self.profile.to_dict())
        return data


class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    full_name = db.Column(db.String(120), nullable=False)
    student_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    department = db.Column(db.String(100), nullable=False)
    academic_year = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    emergency_contact = db.Column(db.String(120), nullable=True)
    
    def to_dict(self):
        return {
            'full_name': self.full_name,
            'student_id': self.student_id,
            'department': self.department,
            'academic_year': self.academic_year,
            'phone': self.phone,
            'emergency_contact': self.emergency_contact
        }


class MoodLog(db.Model):
    __tablename__ = 'mood_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    mood_score = db.Column(db.Integer, nullable=False)  # 1 to 5
    sleep_hours = db.Column(db.Float, default=7.0)
    academic_stress = db.Column(db.Integer, default=5)  # 1 to 10
    energy_level = db.Column(db.Integer, default=3)     # 1 to 5
    emotion_tags = db.Column(db.String(255), default='')
    notes = db.Column(db.Text, nullable=True)
    logged_at = db.Column(db.DateTime, default=get_utc_now, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'mood_score': self.mood_score,
            'sleep_hours': self.sleep_hours,
            'academic_stress': self.academic_stress,
            'energy_level': self.energy_level,
            'emotion_tags': self.emotion_tags.split(',') if self.emotion_tags else [],
            'notes': self.notes or '',
            'logged_at': self.logged_at.strftime('%Y-%m-%d %H:%M') if self.logged_at else None,
            'date_formatted': self.logged_at.strftime('%b %d, %Y') if self.logged_at else ''
        }


class AssessmentResult(db.Model):
    __tablename__ = 'assessment_results'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    assessment_type = db.Column(db.String(50), nullable=False) # 'GAD-7', 'PSS Stress Scale', 'Burnout Index'
    total_score = db.Column(db.Integer, nullable=False)
    max_score = db.Column(db.Integer, nullable=False)
    risk_level = db.Column(db.String(30), nullable=False) # 'Minimal', 'Mild', 'Moderate', 'Severe / High Risk'
    details_json = db.Column(db.Text, nullable=True)
    recommendations = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=get_utc_now, index=True)
    
    def to_dict(self):
        details = {}
        if self.details_json:
            try:
                details = json.loads(self.details_json)
            except Exception:
                details = {}
        return {
            'id': self.id,
            'user_id': self.user_id,
            'assessment_type': self.assessment_type,
            'total_score': self.total_score,
            'max_score': self.max_score,
            'risk_level': self.risk_level,
            'details': details,
            'recommendations': self.recommendations or '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
            'date_formatted': self.created_at.strftime('%b %d, %Y') if self.created_at else ''
        }


class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    counselor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    preferred_date = db.Column(db.String(50), nullable=False)
    preferred_time_slot = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(60), nullable=False)
    urgency = db.Column(db.String(30), default='Standard') # 'Standard', 'Priority', 'Immediate Support'
    student_notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default='Pending') # 'Pending', 'Confirmed', 'Completed', 'Cancelled'
    counselor_notes = db.Column(db.Text, nullable=True)
    meeting_details = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=get_utc_now)
    updated_at = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    def to_dict(self):
        student_name = "Unknown Student"
        student_dept = "General"
        student_id_code = "N/A"
        if self.student and self.student.profile:
            student_name = self.student.profile.full_name
            student_dept = self.student.profile.department
            student_id_code = self.student.profile.student_id
        elif self.student:
            student_name = self.student.email.split('@')[0]
            
        return {
            'id': self.id,
            'user_id': self.user_id,
            'student_name': student_name,
            'student_email': self.student.email if self.student else '',
            'student_id': student_id_code,
            'student_department': student_dept,
            'counselor_id': self.counselor_id,
            'preferred_date': self.preferred_date,
            'preferred_time_slot': self.preferred_time_slot,
            'category': self.category,
            'urgency': self.urgency,
            'student_notes': self.student_notes or '',
            'status': self.status,
            'counselor_notes': self.counselor_notes or '',
            'meeting_details': self.meeting_details or '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else None
        }


class WellnessTip(db.Model):
    __tablename__ = 'wellness_tips'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    duration = db.Column(db.String(30), default='3 min')
    icon = db.Column(db.String(50), default='feather')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'category': self.category,
            'content': self.content,
            'duration': self.duration,
            'icon': self.icon
        }
