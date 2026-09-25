-- ===============================================================
-- Serene Minds - Student Wellness System
-- Complete Database Initialization Schema (schema.sql)
-- Compatible with SQLite, PostgreSQL, and standard SQL engines
-- ===============================================================

-- 1. Users Table (Core Auth for Students & Counselors)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'student', -- 'student' or 'counselor'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 2. Student Profiles Table (Academic & Demographic info)
CREATE TABLE IF NOT EXISTS student_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    full_name VARCHAR(120) NOT NULL,
    student_id VARCHAR(50) NOT NULL UNIQUE,
    department VARCHAR(100) NOT NULL,
    academic_year VARCHAR(20) NOT NULL,
    phone VARCHAR(30),
    emergency_contact VARCHAR(120),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_student_profiles_student_id ON student_profiles(student_id);

-- 3. Daily Mood Logs Table (Interactive Mood Tracking)
CREATE TABLE IF NOT EXISTS mood_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    mood_score INTEGER NOT NULL, -- 1: Severe Distress, 2: Down/Anxious, 3: Neutral, 4: Good, 5: Thriving
    sleep_hours REAL DEFAULT 7.0,
    academic_stress INTEGER DEFAULT 5, -- Scale 1 to 10
    energy_level INTEGER DEFAULT 3,     -- Scale 1 to 5
    emotion_tags VARCHAR(255) DEFAULT '',
    notes TEXT,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_mood_logs_user_date ON mood_logs(user_id, logged_at);

-- 4. Assessment Results Table (GAD-7, PSS Stress, Burnout Inventory)
CREATE TABLE IF NOT EXISTS assessment_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    assessment_type VARCHAR(50) NOT NULL, -- 'GAD-7 Anxiety', 'PSS Stress Scale', 'Burnout Index'
    total_score INTEGER NOT NULL,
    max_score INTEGER NOT NULL,
    risk_level VARCHAR(30) NOT NULL,      -- 'Minimal', 'Mild', 'Moderate', 'Severe / High Risk'
    details_json TEXT,
    recommendations TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_assessment_user_date ON assessment_results(user_id, created_at);

-- 5. Appointments & Help Requests Table (Counselor-Student Queue)
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    counselor_id INTEGER,
    preferred_date VARCHAR(50) NOT NULL,
    preferred_time_slot VARCHAR(50) NOT NULL,
    category VARCHAR(60) NOT NULL,
    urgency VARCHAR(30) DEFAULT 'Standard', -- 'Standard', 'Priority', 'Immediate Support'
    student_notes TEXT,
    status VARCHAR(30) DEFAULT 'Pending',   -- 'Pending', 'Confirmed', 'Completed', 'Cancelled'
    counselor_notes TEXT,
    meeting_details VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (counselor_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);
CREATE INDEX IF NOT EXISTS idx_appointments_user ON appointments(user_id);

-- 6. Wellness Tips & Resources Table
CREATE TABLE IF NOT EXISTS wellness_tips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(150) NOT NULL,
    category VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    duration VARCHAR(30) DEFAULT '3 min',
    icon VARCHAR(50) DEFAULT 'heart'
);
