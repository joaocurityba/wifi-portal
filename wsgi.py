"""
WSGI entry point for production deployment with Gunicorn.

Usage:
    gunicorn -c deploy/gunicorn.conf.py wsgi:app
"""

from app_simple import app

if __name__ == "__main__":
    app.run()
