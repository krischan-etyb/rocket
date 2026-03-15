"""
Rocket Logistic Contact Form Backend
Flask API for handling contact form submissions
"""
import os
import json
import csv
import threading
from datetime import datetime, timedelta
from collections import defaultdict
from flask import Flask, request, jsonify
from flask_cors import CORS
from email_validator import validate_email, EmailNotValidError
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import requests

from config import Config
from email_templates import get_company_notification_template, get_customer_confirmation_template

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": Config.ALLOWED_ORIGINS,
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Rate limiting storage (in-memory - for production, use Redis)
submission_tracker = defaultdict(list)
rate_limit_lock = threading.Lock()


def check_rate_limit(ip_address):
    """
    Check if IP has exceeded rate limit

    Args:
        ip_address: Client IP address

    Returns:
        tuple: (is_allowed, remaining_submissions)
    """
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)

    with rate_limit_lock:
        # Clean old submissions
        submission_tracker[ip_address] = [
            timestamp for timestamp in submission_tracker[ip_address]
            if timestamp > one_hour_ago
        ]

        # Check if under limit
        count = len(submission_tracker[ip_address])
        if count >= Config.MAX_SUBMISSIONS_PER_HOUR:
            return False, 0

        # Add current submission
        submission_tracker[ip_address].append(now)
        return True, Config.MAX_SUBMISSIONS_PER_HOUR - count - 1


def validate_submission(data):
    """
    Validate form submission data

    Args:
        data: dict with form fields

    Returns:
        tuple: (is_valid, error_message)
    """
    # Name validation
    name = data.get('name', '').strip()
    if not name or len(name) < 2 or len(name) > 100:
        return False, "Name must be between 2 and 100 characters"

    # Email validation
    email = data.get('email', '').strip()
    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        return False, "Invalid email address"

    # Phone validation (optional)
    phone = (data.get('phone') or '').strip()
    if phone and len(phone) > 50:
        return False, "Phone number too long"

    # Message validation
    message = data.get('message', '').strip()
    if not message or len(message) < 10 or len(message) > 2000:
        return False, "Message must be between 10 and 2000 characters"

    # Language validation
    language = data.get('language', 'en')
    if language not in ['en', 'bg']:
        return False, "Invalid language"

    # Load date validation (optional)
    load_date = (data.get('load_date') or '').strip()
    if load_date:
        try:
            # Validate date format (YYYY-MM-DD)
            datetime.fromisoformat(load_date)
        except (ValueError, TypeError):
            return False, "Invalid load date format"

    # Date flexibility validation (optional, but if provided must be valid)
    date_flexibility = (data.get('date_flexibility') or '').strip()
    if date_flexibility and date_flexibility not in ['flexible', 'fixed']:
        return False, "Invalid date flexibility option"

    return True, None


def save_to_json(data):
    """
    Save submission to JSON file

    Args:
        data: dict with submission data
    """
    # Ensure submissions directory exists
    os.makedirs(Config.SUBMISSIONS_DIR, exist_ok=True)

    # Load existing data or create new list
    if os.path.exists(Config.JSON_FILE):
        with open(Config.JSON_FILE, 'r', encoding='utf-8') as f:
            try:
                submissions = json.load(f)
            except json.JSONDecodeError:
                submissions = []
    else:
        submissions = []

    # Add new submission
    submissions.append(data)

    # Save back to file
    with open(Config.JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(submissions, f, ensure_ascii=False, indent=2)


def sanitize_csv_value(value):
    """
    Prevent CSV injection by prefixing dangerous leading characters with a single quote.

    Args:
        value: string value to sanitize

    Returns:
        sanitized string
    """
    if isinstance(value, str) and value and value[0] in ('=', '+', '-', '@', '\t', '\r'):
        return "'" + value
    return value


def save_to_csv(data):
    """
    Save submission to CSV file

    Args:
        data: dict with submission data
    """
    # Ensure submissions directory exists
    os.makedirs(Config.SUBMISSIONS_DIR, exist_ok=True)

    # Check if file exists to determine if we need headers
    file_exists = os.path.exists(Config.CSV_FILE)

    # Define fieldnames
    fieldnames = ['timestamp', 'name', 'email', 'phone', 'message', 'load_date', 'date_flexibility', 'language', 'ip']

    # Append to CSV
    with open(Config.CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        sanitized = dict(data)
        for field in ('name', 'email', 'phone', 'message', 'load_date', 'date_flexibility'):
            sanitized[field] = sanitize_csv_value(sanitized[field])
        writer.writerow(sanitized)


def send_email_sendgrid(to_email, subject, html_content, from_name="Rocket Logistic"):
    """
    Send email using SendGrid

    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: Email HTML body
        from_name: Sender name

    Returns:
        bool: True if sent successfully
    """
    try:
        message = Mail(
            from_email=Email(Config.COMPANY_EMAIL, from_name),
            to_emails=To(to_email),
            subject=subject,
            html_content=Content("text/html", html_content)
        )

        sg = SendGridAPIClient(Config.SENDGRID_API_KEY)
        response = sg.send(message)

        return response.status_code in [200, 201, 202]

    except Exception as e:
        app.logger.error(f"SendGrid error: {str(e)}")
        return False


def send_email_mailgun(to_email, subject, html_content, from_name="Rocket Logistic"):
    """
    Send email using Mailgun

    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: Email HTML body
        from_name: Sender name

    Returns:
        bool: True if sent successfully
    """
    try:
        response = requests.post(
            f"https://api.mailgun.net/v3/{Config.MAILGUN_DOMAIN}/messages",
            auth=("api", Config.MAILGUN_API_KEY),
            data={
                "from": f"{from_name} <{Config.COMPANY_EMAIL}>",
                "to": to_email,
                "subject": subject,
                "html": html_content
            }
        )

        return response.status_code == 200

    except Exception as e:
        app.logger.error(f"Mailgun error: {str(e)}")
        return False


def send_email(to_email, subject, html_content, from_name="Rocket Logistic"):
    """
    Send email using configured service

    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: Email HTML body
        from_name: Sender name

    Returns:
        bool: True if sent successfully
    """
    if Config.EMAIL_SERVICE == 'sendgrid':
        return send_email_sendgrid(to_email, subject, html_content, from_name)
    elif Config.EMAIL_SERVICE == 'mailgun':
        return send_email_mailgun(to_email, subject, html_content, from_name)
    else:
        app.logger.error(f"Unknown email service: {Config.EMAIL_SERVICE}")
        return False


@app.route('/api/contact', methods=['POST', 'OPTIONS'])
def handle_contact():
    """
    Handle contact form submission

    Expects JSON payload:
    {
        "name": "string",
        "email": "string",
        "phone": "string" (optional),
        "message": "string",
        "language": "en" or "bg"
    }
    """
    # Handle preflight CORS request
    if request.method == 'OPTIONS':
        return '', 204

    try:
        # Get JSON data
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Get client IP
        client_ip = request.remote_addr

        # Check rate limit
        is_allowed, remaining = check_rate_limit(client_ip)
        if not is_allowed:
            return jsonify({
                'success': False,
                'error': 'Too many submissions. Please try again later.',
                'error_bg': 'Твърде много запитвания. Моля, опитайте отново по-късно.'
            }), 429

        # Validate data
        is_valid, error_message = validate_submission(data)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_message
            }), 400

        # Prepare submission data
        submission_data = {
            'timestamp': datetime.now().isoformat(),
            'name': data['name'].strip(),
            'email': data['email'].strip().lower(),
            'phone': (data.get('phone') or '').strip(),
            'message': data['message'].strip(),
            'load_date': (data.get('load_date') or '').strip(),
            'date_flexibility': (data.get('date_flexibility') or '').strip(),
            'language': data.get('language', 'en'),
            'ip': client_ip
        }

        # Save to files
        try:
            save_to_json(submission_data)
            save_to_csv(submission_data)
        except Exception as e:
            app.logger.error(f"Error saving submission: {str(e)}")
            # Continue even if saving fails - emails are more important

        # Send emails
        language = submission_data['language']
        email_errors = []

        # 1. Send notification to company
        try:
            company_subject, company_html = get_company_notification_template(
                submission_data, language
            )
            company_sent = send_email(
                Config.COMPANY_EMAIL,
                company_subject,
                company_html,
                "Rocket Logistic Website"
            )
            if not company_sent:
                email_errors.append("Failed to send company notification")
        except Exception as e:
            app.logger.error(f"Error sending company email: {str(e)}")
            email_errors.append("Failed to send company notification")

        # 2. Send confirmation to customer
        try:
            customer_subject, customer_html = get_customer_confirmation_template(
                submission_data, language
            )
            customer_sent = send_email(
                submission_data['email'],
                customer_subject,
                customer_html,
                Config.COMPANY_NAME
            )
            if not customer_sent:
                email_errors.append("Failed to send customer confirmation")
        except Exception as e:
            app.logger.error(f"Error sending customer email: {str(e)}")
            email_errors.append("Failed to send customer confirmation")

        # Determine response
        if email_errors:
            app.logger.warning(f"Email errors: {email_errors}")
            # Still return success if data was saved
            return jsonify({
                'success': True,
                'message': 'Form submitted but some emails failed to send',
                'warnings': email_errors
            }), 200
        else:
            return jsonify({
                'success': True,
                'message': 'Form submitted successfully',
                'remaining_submissions': remaining
            }), 200

    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred. Please try again later.'
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'Rocket Logistic Contact Form API',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'message': 'Rocket Logistic Contact Form API',
        'version': '1.0.0',
        'endpoints': {
            'POST /api/contact': 'Submit contact form',
            'GET /api/health': 'Health check'
        }
    })


if __name__ == '__main__':
    # Validate configuration
    try:
        Config.validate()
        print("✓ Configuration validated successfully")
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        print("\nPlease check your .env file and ensure all required variables are set.")
        print("See .env.example for reference.")
        exit(1)

    # Create submissions directory if it doesn't exist
    os.makedirs(Config.SUBMISSIONS_DIR, exist_ok=True)

    # Run the app
    print(f"\nStarting Rocket Logistic Contact Form API...")
    print(f"Server running on http://localhost:{Config.PORT}")
    print(f"Email service: {Config.EMAIL_SERVICE}")
    print(f"Allowed origins: {', '.join(Config.ALLOWED_ORIGINS)}")
    print(f"\nPress CTRL+C to stop the server\n")

    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=Config.DEBUG
    )
