# Rocket Logistic Contact Form Backend

Flask API backend for handling contact form submissions with email notifications and data storage.

## Features

- RESTful API endpoint for contact form submissions
- Email notifications to company and customer confirmations
- Bilingual support (English/Bulgarian)
- Data storage in JSON and CSV formats
- Rate limiting (5 submissions per hour per IP)
- Input validation and sanitization
- CORS support for cross-origin requests
- SendGrid or Mailgun email integration

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SendGrid or Mailgun account (for email sending)

## Installation

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` and set your values:

```env
# Choose email service (sendgrid or mailgun)
EMAIL_SERVICE=sendgrid

# For SendGrid:
SENDGRID_API_KEY=your-sendgrid-api-key-here

# For Mailgun (alternative):
# MAILGUN_API_KEY=your-mailgun-api-key-here
# MAILGUN_DOMAIN=your-domain.mailgun.org

# Company email
COMPANY_EMAIL=office@r-logistic.com

# CORS origins (comma-separated)
ALLOWED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
```

### 3. Get Email Service API Key

#### Option A: SendGrid (Recommended)

1. Sign up at [SendGrid](https://sendgrid.com/)
2. Go to Settings > API Keys
3. Create a new API key with "Mail Send" permissions
4. Copy the key to your `.env` file as `SENDGRID_API_KEY`

#### Option B: Mailgun

1. Sign up at [Mailgun](https://www.mailgun.com/)
2. Go to Sending > Domains
3. Copy your domain and API key
4. Add them to your `.env` file as `MAILGUN_DOMAIN` and `MAILGUN_API_KEY`

## Running the Server

### Development Mode

```bash
python app.py
```

The server will start on `http://localhost:5000`

### Test the API

#### Health Check

```bash
curl http://localhost:5000/api/health
```

#### Submit Contact Form

```bash
curl -X POST http://localhost:5000/api/contact \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+359 123 456 789",
    "message": "Hello, I would like to request a quote for freight services.",
    "language": "en"
  }'
```

## API Endpoints

### POST /api/contact

Submit a contact form.

**Request Body:**

```json
{
  "name": "string (required, 2-100 chars)",
  "email": "string (required, valid email)",
  "phone": "string (optional, max 50 chars)",
  "message": "string (required, 10-2000 chars)",
  "language": "string (optional, 'en' or 'bg', default: 'en')"
}
```

**Success Response (200):**

```json
{
  "success": true,
  "message": "Form submitted successfully",
  "remaining_submissions": 4
}
```

**Error Responses:**

- `400 Bad Request` - Invalid data
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### GET /api/health

Health check endpoint.

**Response (200):**

```json
{
  "status": "ok",
  "service": "Rocket Logistic Contact Form API",
  "timestamp": "2026-01-25T14:30:00.000000"
}
```

## File Structure

```
backend/
├── app.py                  # Main Flask application
├── config.py               # Configuration management
├── email_templates.py      # Email HTML templates
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not in git)
├── .env.example            # Environment template
├── README.md               # This file
└── submissions/            # Data storage directory
    ├── contacts.json       # JSON format submissions
    └── contacts.csv        # CSV format submissions
```

## Data Storage

Submissions are automatically saved in two formats:

### JSON Format (`submissions/contacts.json`)

```json
[
  {
    "timestamp": "2026-01-25T14:30:00.123456",
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+359 123 456 789",
    "message": "Hello...",
    "language": "en",
    "ip": "127.0.0.1"
  }
]
```

### CSV Format (`submissions/contacts.csv`)

| timestamp | name | email | phone | message | language | ip |
|-----------|------|-------|-------|---------|----------|----|
| 2026-01-25T14:30:00 | John Doe | john@example.com | +359... | Hello... | en | 127.0.0.1 |

## Security Features

- **Rate Limiting**: 5 submissions per hour per IP address
- **Input Validation**: All fields are validated and sanitized
- **CORS Protection**: Only allowed origins can access the API
- **Email Validation**: Email addresses are validated before processing
- **Environment Variables**: Sensitive data stored in `.env` file
- **No SQL Injection**: File-based storage, no database queries

## Production Deployment

### Environment Setup

1. Set `FLASK_ENV=production` in `.env`
2. Set `DEBUG=False`
3. Use a strong `SECRET_KEY`
4. Update `ALLOWED_ORIGINS` to your production domain

### Deployment Options

#### Heroku

```bash
# Install Heroku CLI
heroku login
heroku create your-app-name

# Set environment variables
heroku config:set SENDGRID_API_KEY=your-key
heroku config:set COMPANY_EMAIL=office@r-logistic.com
heroku config:set ALLOWED_ORIGINS=https://rocketlogistic.bg

# Deploy
git push heroku main
```

#### PythonAnywhere

1. Upload files to PythonAnywhere
2. Create a new web app (Flask)
3. Set environment variables in web app settings
4. Configure WSGI file to point to `app.py`

#### DigitalOcean/AWS

Use a service like Gunicorn with Nginx:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Troubleshooting

### Configuration Errors

If you see configuration errors on startup:

```
✗ Configuration error: SENDGRID_API_KEY is required when using SendGrid
```

Make sure your `.env` file exists and has all required variables set.

### Email Not Sending

1. Check API key is correct
2. Verify email service account is active
3. Check server logs for error messages
4. Test with SendGrid/Mailgun dashboard

### CORS Errors

If the frontend can't connect:

1. Check `ALLOWED_ORIGINS` includes your frontend URL
2. Make sure frontend is using correct API URL
3. Check browser console for specific CORS errors

### Rate Limiting

If you're testing and hit rate limits:

1. Wait 1 hour for limit to reset
2. Or increase `MAX_SUBMISSIONS_PER_HOUR` in `.env` for development

## Logs

Check console output for:
- Request logs
- Email sending status
- Error messages
- Configuration validation

## Future Enhancements

- Database storage (PostgreSQL/MySQL)
- Admin dashboard for viewing submissions
- Webhook integrations (Slack, Discord, etc.)
- Email templates with attachments
- Spam detection (reCAPTCHA)
- Export submissions to Excel

## Support

For issues or questions:
- Check logs for error messages
- Verify `.env` configuration
- Test email service separately
- Contact: office@r-logistic.com
