#!/usr/bin/env python3
"""Start the Rocket Logistic calculator server."""
import os
import sys
from pathlib import Path

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Ensure backend is importable
sys.path.insert(0, str(Path(__file__).parent))

from app import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() in ("true", "1", "yes")
    print(f"Starting Rocket Logistic Calculator on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
