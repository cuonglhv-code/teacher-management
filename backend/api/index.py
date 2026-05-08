"""Vercel serverless entry point for FastAPI."""

import sys
import os

# Add parent directory to path so 'app' module can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

# Vercel expects the app to be named 'app'
# It's already exported from app.main, but we re-export here for clarity
if __name__ != "__main__":
    # Running on Vercel
    pass