"""
Configuration management for Rocket Logistic contact form backend
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""

    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    PORT = int(os.getenv('PORT', 5000))

    # Email service configuration
    EMAIL_SERVICE = os.getenv('EMAIL_SERVICE', 'sendgrid').lower()

    # SendGrid configuration
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', '')

    # Mailgun configuration
    MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY', '')
    MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN', '')

    # Company information
    COMPANY_EMAIL = os.getenv('COMPANY_EMAIL', 'info@rocketlogistic.bg')
    COMPANY_NAME = os.getenv('COMPANY_NAME', 'Rocket Logistic')

    # CORS configuration
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5500').split(',')

    # Rate limiting
    MAX_SUBMISSIONS_PER_HOUR = int(os.getenv('MAX_SUBMISSIONS_PER_HOUR', 5))

    # File paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SUBMISSIONS_DIR = os.path.join(BASE_DIR, 'submissions')
    JSON_FILE = os.path.join(SUBMISSIONS_DIR, 'contacts.json')
    CSV_FILE = os.path.join(SUBMISSIONS_DIR, 'contacts.csv')

    @classmethod
    def validate(cls):
        """Validate that required configuration is present"""
        errors = []

        if cls.EMAIL_SERVICE == 'sendgrid' and not cls.SENDGRID_API_KEY:
            errors.append("SENDGRID_API_KEY is required when using SendGrid")

        if cls.EMAIL_SERVICE == 'mailgun':
            if not cls.MAILGUN_API_KEY:
                errors.append("MAILGUN_API_KEY is required when using Mailgun")
            if not cls.MAILGUN_DOMAIN:
                errors.append("MAILGUN_DOMAIN is required when using Mailgun")

        if cls.EMAIL_SERVICE not in ['sendgrid', 'mailgun']:
            errors.append(f"Invalid EMAIL_SERVICE: {cls.EMAIL_SERVICE}. Must be 'sendgrid' or 'mailgun'")

        if errors:
            raise ValueError("Configuration errors:\n" + "\n".join(f"- {e}" for e in errors))

        return True
