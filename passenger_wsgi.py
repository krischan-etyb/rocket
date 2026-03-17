"""
Passenger WSGI entry point for JetHost (cPanel + Phusion Passenger).

This file must sit in the application root directory that the hosting
points to.  Passenger looks for ``passenger_wsgi.py`` automatically.
"""

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths — make sure the calculator backend package is importable
# ---------------------------------------------------------------------------
_THIS_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _THIS_DIR / "calculator" / "backend"

# Add the backend directory so Flask app.py and its siblings are importable
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

# Also add the project root (some modules may reference it)
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

# ---------------------------------------------------------------------------
# Load environment variables from the backend .env file
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
    env_path = _BACKEND_DIR / ".env"
    if env_path.is_file():
        load_dotenv(env_path)
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Import the Flask application — Passenger expects it as ``application``
# ---------------------------------------------------------------------------
from app import app as application
