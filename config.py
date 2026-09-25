import os

def is_directory_writable(path):
    """Checks whether the specified directory allows file creation and writing."""
    try:
        test_file = os.path.join(path, '.perm_test')
        with open(test_file, 'w') as f:
            f.write('ok')
        os.remove(test_file)
        return True
    except Exception:
        return False

class Config:
    """Application configuration supporting Local, Render, Vercel Drop, and Serverless environments."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'serene-minds-production-secret-key-2026')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database resolution:
    # 1. DATABASE_URL environment variable (Render PostgreSQL, Supabase, Neon)
    # 2. Vercel / AWS Lambda Serverless environment (/tmp directory is the only writable directory)
    # 3. Read-only filesystem auto-detection (fallback to /tmp for Vercel Drop)
    # 4. Local environment (sereneminds.db in project folder)
    db_url = os.environ.get('DATABASE_URL')
    base_dir = os.path.abspath(os.path.dirname(__file__))

    if db_url:
        # SQLAlchemy 1.4+ requires postgresql:// instead of postgres://
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = db_url
    elif os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME') or not is_directory_writable(base_dir):
        # Running inside Vercel serverless / Vercel Drop / Lambda environment
        SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/sereneminds.db'
    else:
        # Running locally with standard write access
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(base_dir, 'sereneminds.db')}"

    # Session settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
