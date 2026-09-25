# Serene Minds - Student Wellness System
**A Comprehensive Student Mental Health and Wellness Monitoring System**

Serene Minds is an empathetic, evidence-based web application designed to track, analyze, and support student holistic well-being across mental, emotional, physical, and academic dimensions. It bridges students with campus mental health professionals through continuous mood tracking, clinical self-assessments, personalized mindfulness interventions, proactive risk detection, and confidential appointment scheduling.

---

## 🌟 Key Modules & Features

### 1. Student Module
- **Secure Authentication:** Self-registration with student ID, institutional email, academic department, and password hashing (PBKDF2).
- **Interactive Daily Mood Tracker:**
  - 5-tier emotional rating (Severe Distress 😫, Down/Anxious 😔, Okay/Neutral 😐, Good/Peaceful 😊, Thriving/Great ✨).
  - Academic stress level slider (1–10) with dynamic reactive badge indicators.
  - Sleep hours tracking and energy rating.
  - Granular state tags (Calm, Focused, Motivated, Anxious, Overwhelmed, Exhausted, etc.).
  - Private journal reflections.
  - Instant database persistence and real-time DOM update without page reload.
  - Interactive 7-day personal wellness trajectory chart (Chart.js).
- **Clinical Self-Assessment Surveys:**
  - Standardized instruments: **GAD-7 Anxiety Scale**, **Perceived Stress Scale (PSS-10)**, and **Academic Burnout Index**.
  - Automatic scoring engine with immediate risk tier classification (Minimal, Mild, Moderate, Severe / High Risk).
  - Instant diagnostic feedback and tailored clinical recommendations.
- **Personalized Wellness Hub:**
  - Adaptive recommendations engine that responds dynamically to low mood, high academic stress, or sleep deficits.
  - **Interactive 4-7-8 Breathing Circle:** Visually guided parasympathetic vagus nerve reset with real-time timer countdown.
  - **Synthesized Ambient Soundscapes:** Built with the HTML5 Web Audio API (Rain & Ocean Waves) for offline-capable, distraction-free studying.
  - Evidence-based student coping rituals (50/10 focus cycle, cognitive defusion, sleep hygiene).
- **Counselor Appointment & Help Requests:**
  - Direct request form with date, time window, concern category, and urgency level (Standard, Priority, Immediate Support).
  - Real-time appointment status tracker (Pending, Confirmed, Completed, Cancelled) with counselor location and notes.

### 2. Counselor / Clinical Administration Module
- **Strict Fixed Authentication:**
  - Secure institutional login credentials:
    - **Email:** `counselor@sereneminds.edu`
    - **Password:** `SecurePassword123!`
  - Absolutely zero mock/bypass buttons. Authenticates securely via PBKDF2 password verification.
- **Early Risk Detection & Automated Alerts:**
  - Automated algorithm flagging students exhibiting:
    1. Persistent low mood score (average &le; 2.2/5 over recent check-ins)
    2. Flagged clinical survey scores (e.g. GAD-7 &ge; 15, severe burnout)
    3. Critical academic stress (&ge; 8/10) combined with acute sleep deprivation (&le; 5 hours)
    4. Unresolved urgent/immediate support requests
  - Real-time alert feed with quick actions: **View Longitudinal Wellness Timeline** and **Initiate Outreach**.
- **Data Visualizations & Campus Analytics (Chart.js):**
  - **Campus Wellness Distribution:** Doughnut chart breaking down student body into Thriving, Stable, Vulnerable, and High Risk.
  - **7-Day Campus Mood Trajectory:** Line chart plotting aggregate cohort emotional fluctuations.
- **Queue Management & Clinical Consultation Notes:**
  - Filter appointments by status (Pending, Confirmed, Completed, Cancelled) and urgency.
  - Modal editor to confirm appointments, assign physical rooms or telehealth meeting links, and record confidential counselor notes in the database.
- **Student Longitudinal Timeline Modal:**
  - Deep-dive view of individual student check-in history, past diagnostic test scores, and appointment logs.

---

## 🛠️ Tech Stack & Architecture

- **Backend:** Python (Flask), Flask-SQLAlchemy, Werkzeug Security, Gunicorn WSGI.
- **Database:** SQLite (default for zero-config local development and serverless) and PostgreSQL-ready via `DATABASE_URL` (psycopg2-binary). Complete SQL schema provided in `schema.sql`.
- **Frontend:** HTML5, CSS3 (Custom Calming Theme: soft blues, sage greens, warm neutrals), Vanilla JavaScript, Chart.js, HTML5 Web Audio API.
- **Deployments:**
  - **Vercel:** Serverless WSGI adapter configured via `api/index.py` and `vercel.json`.
  - **Render:** Production web service configured via `render.yaml` and Gunicorn.

---

## 🚀 Local Setup & Running Instructions

### 1. Clone or Navigate to the Project
```bash
cd serene-minds
```

### 2. Create and Activate a Virtual Environment
**On Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```
**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Development Server
```bash
python app.py
```
The application will automatically initialize the database, apply `schema.sql` definitions, and seed the default counselor account and sample student wellness data.

Open your browser and navigate to:
```
http://localhost:5000
```

---

## 🔑 Login Credentials

| Role | Email | Password | Access Portal |
| :--- | :--- | :--- | :--- |
| **Counselor / Staff** | `counselor@sereneminds.edu` | `SecurePassword123!` | `/counselor-login` |
| **Pre-Seeded Student (Flagged)** | `elena.vance@sereneminds.edu` | `Password123!` | `/login` |
| **Pre-Seeded Student (Moderate)** | `liam.chen@sereneminds.edu` | `Password123!` | `/login` |
| **Pre-Seeded Student (Thriving)** | `maya.lin@sereneminds.edu` | `Password123!` | `/login` |
| **New Students** | *Self-register via portal* | *Custom* | `/login` (Register tab) |

---

## ☁️ Deployment Guide

### Deploying to Vercel (Full-Stack / Serverless)
The project is pre-configured for seamless Vercel deployment:
1. **Configured Files:**
   - `vercel.json`: Directs all incoming traffic to `api/index.py` using `@vercel/python`.
   - `api/index.py`: Serverless WSGI entry point that cleanly initializes the Flask application.
2. **Steps to Deploy:**
   - Push this repository to GitHub or GitLab.
   - Go to [vercel.com](https://vercel.com) and click **"Add New Project"** &rarr; Import your repository.
   - In **Environment Variables**, add:
     - `SECRET_KEY`: A random secure string.
     - *(Recommended for permanent production data)* `DATABASE_URL`: A hosted PostgreSQL database URL (from Supabase, Neon, or Render PostgreSQL).
       *Note: If `DATABASE_URL` is omitted, the app automatically runs using `/tmp/sereneminds.db` on Vercel's writable serverless filesystem.*
   - Click **Deploy**. Vercel will build and launch your application without server errors.

### Deploying to Render (Persistent Web Service)
1. **Configured Files:**
   - `render.yaml`: Blueprint specifying Python 3.10 environment, build command `pip install -r requirements.txt`, and start command `gunicorn app:app`.
2. **Steps to Deploy:**
   - Push repository to GitHub.
   - In Render, click **"New +"** &rarr; **"Web Service"** &rarr; Connect repository.
   - Set:
     - **Environment:** `Python 3`
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `gunicorn app:app`
   - Under **Environment Variables**, add:
     - `SECRET_KEY`: A secure random string.
     - *(Optional)* `DATABASE_URL`: If using Render PostgreSQL.
   - Click **Create Web Service**.

---

## 🗄️ Database Architecture (`schema.sql`)

- `users`: Core account authentication for both students and counselors.
- `student_profiles`: Academic department, student ID, emergency contacts.
- `mood_logs`: Daily emotional rating, sleep hours, stress score, energy level, emotion tags, private reflections.
- `assessment_results`: Completed GAD-7, PSS, and Burnout survey scores, risk classification, and clinical recommendations.
- `appointments`: Counselor session requests, urgency tiers, statuses, room info, and confidential counselor notes.
- `wellness_tips`: Curated evidence-based stress-relief and mindfulness resources.

---

## 📄 License & Confidentiality
Developed for educational institutions to provide student mental health support. Built with privacy-first standards.
#   s t u d e n t w e l l n e s s s y s t e m  
 