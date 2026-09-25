import unittest
import json
from app import create_app
from database import db, User, MoodLog, AssessmentResult, Appointment

class SereneMindsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
        })
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            from seed_data import seed_database
            seed_database()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_counselor_fixed_authentication(self):
        """Test strict counselor authentication with valid and invalid credentials."""
        # 1. Invalid password must be rejected
        res = self.client.post('/api/auth/counselor-login', json={
            'email': 'counselor@sereneminds.edu',
            'password': 'WrongPassword!'
        })
        self.assertEqual(res.status_code, 401)

        # 2. Valid fixed credentials must succeed
        res = self.client.post('/api/auth/counselor-login', json={
            'email': 'counselor@sereneminds.edu',
            'password': 'SecurePassword123!'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['user']['role'], 'counselor')

    def test_student_registration_and_login(self):
        """Test student self-service registration and session login."""
        reg_payload = {
            'email': 'samuel.green@sereneminds.edu',
            'password': 'StrongPassword123!',
            'full_name': 'Samuel Green',
            'student_id': 'SM-2026-9901',
            'department': 'Biomedical Sciences',
            'academic_year': 'Sophomore (2nd Year)'
        }
        res = self.client.post('/api/auth/register', json=reg_payload)
        self.assertEqual(res.status_code, 201)

        # Attempt to login with newly registered account
        login_res = self.client.post('/api/auth/login', json={
            'email': 'samuel.green@sereneminds.edu',
            'password': 'StrongPassword123!'
        })
        self.assertEqual(login_res.status_code, 200)

    def test_daily_mood_tracking(self):
        """Test submitting daily mood check-in and querying history."""
        # Login pre-seeded student
        self.client.post('/api/auth/login', json={
            'email': 'liam.chen@sereneminds.edu',
            'password': 'Password123!'
        })

        mood_payload = {
            'mood_score': 4,
            'sleep_hours': 8.0,
            'academic_stress': 4,
            'energy_level': 4,
            'emotion_tags': ['Calm', 'Focused'],
            'notes': 'Had a great study session with peer group.'
        }
        res = self.client.post('/api/mood/log', json=mood_payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data['log']['mood_score'], 4)

        # Retrieve history
        hist_res = self.client.get('/api/mood/history')
        self.assertEqual(hist_res.status_code, 200)
        hist_data = hist_res.get_json()
        self.assertGreaterEqual(len(hist_data['logs']), 1)

    def test_clinical_assessment_scoring(self):
        """Test GAD-7 assessment submission, scoring, and risk classification."""
        self.client.post('/api/auth/login', json={
            'email': 'maya.lin@sereneminds.edu',
            'password': 'Password123!'
        })

        # Submit GAD-7 with severe anxiety answers (3 on each question = 21)
        answers = {f'q{i}': 3 for i in range(1, 8)}
        res = self.client.post('/api/assessment/submit', json={
            'assessment_type': 'GAD-7',
            'answers': answers
        })
        self.assertEqual(res.status_code, 201)
        result = res.get_json()['result']
        self.assertEqual(result['total_score'], 21)
        self.assertEqual(result['risk_level'], 'Severe / High Risk')

    def test_appointment_booking_and_counselor_queue(self):
        """Test appointment workflow from student request to counselor confirmation."""
        # 1. Student creates request
        self.client.post('/api/auth/login', json={
            'email': 'liam.chen@sereneminds.edu',
            'password': 'Password123!'
        })
        app_payload = {
            'preferred_date': '2026-09-30',
            'preferred_time_slot': '02:00 PM - 03:00 PM',
            'category': 'Academic Stress & Burnout',
            'urgency': 'Priority',
            'student_notes': 'Experiencing high exam anxiety.'
        }
        res = self.client.post('/api/appointment/create', json=app_payload)
        self.assertEqual(res.status_code, 201)
        appointment_id = res.get_json()['appointment']['id']

        # 2. Counselor logs in and reviews queue
        self.client.post('/api/auth/counselor-login', json={
            'email': 'counselor@sereneminds.edu',
            'password': 'SecurePassword123!'
        })
        queue_res = self.client.get('/api/counselor/appointments')
        self.assertEqual(queue_res.status_code, 200)

        # 3. Counselor confirms appointment with notes and room info
        update_res = self.client.put(f'/api/counselor/appointments/{appointment_id}', json={
            'status': 'Confirmed',
            'meeting_details': 'Room 304, Campus Wellness Pavilion',
            'counselor_notes': 'Session confirmed. Sent intake questionnaire.'
        })
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.get_json()['appointment']['status'], 'Confirmed')

    def test_counselor_early_risk_detection(self):
        """Test counselor risk alerts endpoint flags high-risk students."""
        self.client.post('/api/auth/counselor-login', json={
            'email': 'counselor@sereneminds.edu',
            'password': 'SecurePassword123!'
        })
        res = self.client.get('/api/counselor/risk-alerts')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('alerts', data)
        # Elena Vance was pre-seeded with persistent low mood & severe GAD-7
        flagged_names = [a['full_name'] for a in data['alerts']]
        self.assertIn('Elena Vance', flagged_names)

    def test_vercel_index_entrypoint(self):
        """Verify api/index.py exports valid WSGI app."""
        import api.index
        self.assertIsNotNone(api.index.app)

if __name__ == '__main__':
    unittest.main()
