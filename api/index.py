import os
import sys

# Add project root directory to path for Vercel Serverless environment
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import the initialized Flask application
from app import app

# Vercel WSGI entry point
# On Vercel, the `app` instance is invoked directly for serverless routing
