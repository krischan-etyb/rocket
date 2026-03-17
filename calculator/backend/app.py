"""
Rocket Logistic — Flask backend.

Endpoints
---------
POST /api/calculate   Stateless price estimate (rate-limited to 60/hr per IP).
POST /api/quote       Save quote + send confirmation emails (5/hr per IP).
POST /api/contact     Contact-form submission (5/hr per IP).
GET  /health          Liveness probe.
GET  /                Serves ../frontend/index.html.

Run with::

    python app.py
"""

from __future__ import annotations

import csv
import json
import logging
import os
import re
import smtplib
import sys
from collections import defaultdict
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, send_file, send_from_directory
from flask_cors import CORS

# ---------------------------------------------------------------------------
# Bootstrap — ensure the backend package root is importable
# ---------------------------------------------------------------------------
_BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(_BACKEND_DIR / ".env")
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from config import Config  # noqa: E402
from distance_service import DistanceService  # noqa: E402
from email_templates import (  # noqa: E402
    get_contact_template,
    get_quote_company_notification_template,
    get_quote_customer_confirmation_template,
)
from pricing_engine import PricingEngine  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("rocket_logistic")

# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------
_FRONTEND_DIR = _BACKEND_DIR.parent / "frontend"
_PROJECT_ROOT = _BACKEND_DIR.parent.parent
app = Flask(
    __name__,
    static_folder=str(_PROJECT_ROOT),
    static_url_path="",
)
app.secret_key = Config.SECRET_KEY
_CORS_ORIGINS: list[str] = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "").split(",")
    if o.strip()
] or ["http://localhost:5000", "http://127.0.0.1:5000"]

CORS(app, resources={r"/api/*": {"origins": _CORS_ORIGINS}})

# ---------------------------------------------------------------------------
# Global singletons
# ---------------------------------------------------------------------------
pricing_engine: PricingEngine
distance_service: DistanceService

# ---------------------------------------------------------------------------
# In-memory rate-limit tracker  {ip: [timestamp, ...]}
# ---------------------------------------------------------------------------
rate_limit_tracker: defaultdict[str, list[float]] = defaultdict(list)

# Evict IPs whose entire timestamp window has expired.  Called periodically
# inside check_rate_limit() to prevent unbounded memory growth.
_EVICTION_INTERVAL = 3600.0   # seconds between full eviction sweeps
_last_eviction: float = 0.0


def _maybe_evict_stale_ips(now: float) -> None:
    """Remove entries for IPs that have no request in the last hour."""
    global _last_eviction
    if now - _last_eviction < _EVICTION_INTERVAL:
        return
    _last_eviction = now
    cutoff = now - 3600.0
    stale = [ip for ip, times in rate_limit_tracker.items() if not any(t > cutoff for t in times)]
    for ip in stale:
        del rate_limit_tracker[ip]


# ===========================================================================
# Rate limiting
# ===========================================================================

def check_rate_limit(ip: str, limit: int) -> bool:
    """Return True if the request is within the allowed rate, False otherwise."""
    now = datetime.now(tz=timezone.utc).timestamp()
    one_hour_ago = now - 3600.0

    _maybe_evict_stale_ips(now)

    rate_limit_tracker[ip] = [t for t in rate_limit_tracker[ip] if t > one_hour_ago]

    if len(rate_limit_tracker[ip]) >= limit:
        return False

    rate_limit_tracker[ip].append(now)
    return True


# ===========================================================================
# Persistence helpers
# ===========================================================================

def _ensure_submissions_dir() -> None:
    os.makedirs(Config.SUBMISSIONS_DIR, exist_ok=True)


def save_quote_to_json(data: dict[str, Any]) -> None:
    """Append data as a JSON object to quotes.json."""
    _ensure_submissions_dir()
    path = Path(Config.QUOTES_JSON)
    existing: list[dict] = []

    if path.is_file():
        try:
            with path.open(encoding="utf-8") as fh:
                existing = json.load(fh)
            if not isinstance(existing, list):
                existing = []
        except (json.JSONDecodeError, OSError):
            existing = []

    existing.append(data)

    with path.open("w", encoding="utf-8") as fh:
        json.dump(existing, fh, ensure_ascii=False, indent=2)


_QUOTE_CSV_FIELDS = [
    "timestamp", "name", "email", "phone",
    "service_type", "route_type",
    "origin_country", "origin_city",
    "destination_country", "destination",
    "num_pallets", "total_weight_kg", "pallet_type",
    "non_pallet_cargo", "cargo_length_cm", "cargo_width_cm",
    "cargo_weight_kg", "truck_type",
    "load_date", "date_flexibility",
    "shown_min_price", "shown_max_price",
    "notes", "language", "ip",
]


def save_quote_to_csv(data: dict[str, Any]) -> None:
    """Append data as a row to quotes.csv."""
    _ensure_submissions_dir()
    path = Path(Config.QUOTES_CSV)
    write_header = not path.is_file()

    with path.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=_QUOTE_CSV_FIELDS, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerow({k: data.get(k, "") for k in _QUOTE_CSV_FIELDS})


_CALC_CSV_FIELDS = [
    "timestamp", "service_type", "route_type",
    "origin_country", "origin_city",
    "destination_country", "destination",
    "num_pallets", "total_weight_kg", "pallet_type",
    "non_pallet_cargo", "cargo_length_cm", "cargo_width_cm",
    "cargo_weight_kg", "truck_type",
    "load_date", "date_flexibility",
    "distance_km", "min_price", "max_price", "no_rate",
    "language", "ip",
]


def save_calculation_to_json(data: dict[str, Any]) -> None:
    """Append data as a JSON object to calculations.json."""
    _ensure_submissions_dir()
    path = Path(Config.CALCULATIONS_JSON)
    existing: list[dict] = []

    if path.is_file():
        try:
            with path.open(encoding="utf-8") as fh:
                existing = json.load(fh)
            if not isinstance(existing, list):
                existing = []
        except (json.JSONDecodeError, OSError):
            existing = []

    existing.append(data)

    with path.open("w", encoding="utf-8") as fh:
        json.dump(existing, fh, ensure_ascii=False, indent=2)


def save_calculation_to_csv(data: dict[str, Any]) -> None:
    """Append data as a row to calculations.csv."""
    _ensure_submissions_dir()
    path = Path(Config.CALCULATIONS_CSV)
    write_header = not path.is_file()

    with path.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=_CALC_CSV_FIELDS, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerow({k: data.get(k, "") for k in _CALC_CSV_FIELDS})


def save_contact_to_json(data: dict[str, Any]) -> None:
    """Append a contact submission to contacts.json."""
    _ensure_submissions_dir()
    path = Path(Config.CONTACTS_JSON)
    existing: list[dict] = []

    if path.is_file():
        try:
            with path.open(encoding="utf-8") as fh:
                existing = json.load(fh)
            if not isinstance(existing, list):
                existing = []
        except (json.JSONDecodeError, OSError):
            existing = []

    existing.append(data)

    with path.open("w", encoding="utf-8") as fh:
        json.dump(existing, fh, ensure_ascii=False, indent=2)


_CONTACT_CSV_FIELDS = ["timestamp", "name", "email", "phone", "message", "language", "ip"]


def save_contact_to_csv(data: dict[str, Any]) -> None:
    """Append a contact submission to contacts.csv."""
    _ensure_submissions_dir()
    path = Path(Config.CONTACTS_CSV)
    write_header = not path.is_file()

    with path.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=_CONTACT_CSV_FIELDS, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerow({k: data.get(k, "") for k in _CONTACT_CSV_FIELDS})


# ===========================================================================
# Email
# ===========================================================================

def send_email(to: str, subject: str, body: str) -> bool:
    """Send an HTML email via SMTP. Returns True on success, False on failure."""
    if not Config.MAIL_USERNAME or not Config.MAIL_PASSWORD:
        logger.warning("Email credentials not configured — skipping send to %s", to)
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = Config.MAIL_USERNAME
        msg["To"] = to
        msg.attach(MIMEText(body, "html", "utf-8"))

        with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT, timeout=15) as server:
            if Config.MAIL_USE_TLS:
                server.starttls()
            server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            server.sendmail(Config.MAIL_USERNAME, to, msg.as_string())

        logger.info("Email sent to %s — %s", to, subject)
        return True
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to, exc)
        return False


# ===========================================================================
# Validation helpers
# ===========================================================================

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email_format(value: str) -> bool:
    return bool(_EMAIL_RE.match(value.strip()))


def _err(msg_en: str, msg_bg: str, code: int = 400) -> tuple[Response, int]:
    return jsonify({"success": False, "error": msg_en, "error_bg": msg_bg}), code


def _validate_calculate_fields(body: dict[str, Any]) -> tuple[Response, int] | None:
    """Validate common calculate fields. Returns an error response or None."""
    required = [
        "service_type", "origin_country", "origin_city",
        "destination_country", "destination",
    ]
    for field in required:
        if not body.get(field):
            return _err(
                f"Missing required field: {field}",
                f"Липсващо задължително поле: {field}",
            )

    service_type = body.get("service_type", "").upper()
    if service_type not in ("LTL", "FTL"):
        return _err(
            "service_type must be 'ltl' or 'ftl'.",
            "service_type трябва да е 'ltl' или 'ftl'.",
        )

    if service_type == "LTL":
        non_pallet = body.get("non_pallet_cargo", False)
        if non_pallet:
            try:
                l_cm = float(body.get("cargo_length_cm", 0))
                w_cm = float(body.get("cargo_width_cm", 0))
            except (TypeError, ValueError):
                return _err(
                    "cargo_length_cm and cargo_width_cm must be numbers.",
                    "cargo_length_cm и cargo_width_cm трябва да са числа.",
                )
            if l_cm <= 0 or w_cm <= 0:
                return _err(
                    "cargo_length_cm and cargo_width_cm must be greater than 0.",
                    "cargo_length_cm и cargo_width_cm трябва да са по-големи от 0.",
                )
            try:
                weight = float(body.get("total_weight_kg", 0))
            except (TypeError, ValueError):
                return _err(
                    "total_weight_kg must be a number.",
                    "total_weight_kg трябва да е число.",
                )
            if weight <= 0:
                return _err(
                    "total_weight_kg must be greater than 0.",
                    "total_weight_kg трябва да е по-голямо от 0.",
                )
        else:
            try:
                pallets = int(body.get("num_pallets", 0))
            except (TypeError, ValueError):
                return _err(
                    "num_pallets must be an integer.",
                    "num_pallets трябва да е цяло число.",
                )
            if not (1 <= pallets <= 33):
                return _err(
                    "num_pallets must be between 1 and 33.",
                    "num_pallets трябва да е между 1 и 33.",
                )
            try:
                weight = float(body.get("total_weight_kg", 0))
            except (TypeError, ValueError):
                return _err(
                    "total_weight_kg must be a number.",
                    "total_weight_kg трябва да е число.",
                )
            if weight <= 0:
                return _err(
                    "total_weight_kg must be greater than 0.",
                    "total_weight_kg трябва да е по-голямо от 0.",
                )

    elif service_type == "FTL":
        try:
            cargo_weight = float(body.get("cargo_weight_kg", 0))
        except (TypeError, ValueError):
            return _err(
                "cargo_weight_kg must be a number.",
                "cargo_weight_kg трябва да е число.",
            )
        if cargo_weight <= 0:
            return _err(
                "cargo_weight_kg must be greater than 0.",
                "cargo_weight_kg трябва да е по-голямо от 0.",
            )

    return None


def _validate_contact_fields(body: dict[str, Any]) -> tuple[Response, int] | None:
    """Validate name, contact info, and notes. Returns an error or None."""
    name = str(body.get("name", "")).strip()
    if not (2 <= len(name) <= 100):
        return _err(
            "Name must be between 2 and 100 characters.",
            "Името трябва да е между 2 и 100 символа.",
        )

    email = str(body.get("email", "")).strip()
    phone = str(body.get("phone", "")).strip()
    if not email and not phone:
        return _err(
            "At least one of email or phone is required.",
            "Изисква се поне имейл или телефон.",
        )

    if email and not _validate_email_format(email):
        return _err(
            "Invalid email address format.",
            "Невалиден формат на имейл адрес.",
        )

    notes = str(body.get("notes", "")).strip()
    if len(notes) > 500:
        return _err(
            "Notes must not exceed 500 characters.",
            "Бележките не трябва да надвишават 500 символа.",
        )

    return None


_TRUSTED_PROXIES: set[str] = {
    p.strip()
    for p in os.getenv("TRUSTED_PROXIES", "127.0.0.1,::1").split(",")
    if p.strip()
}


def _get_client_ip() -> str:
    """Return the real client IP.

    X-Forwarded-For is only honoured when the direct peer (remote_addr) is a
    trusted proxy, preventing trivial rate-limit bypass via header spoofing.
    """
    remote = request.remote_addr or "unknown"
    if remote in _TRUSTED_PROXIES:
        forwarded_for = request.headers.get("X-Forwarded-For", "")
        if forwarded_for:
            # The left-most address is the original client.
            return forwarded_for.split(",")[0].strip()
    return remote


def _derive_route_type(data: dict[str, Any]) -> str:
    if (
        data.get("origin_country", "").upper() == "BG"
        and data.get("destination_country", "").upper() == "BG"
    ):
        return "domestic"
    return "international"


# ===========================================================================
# Routes
# ===========================================================================

@app.route("/health", methods=["GET"])
def health() -> tuple[Response, int]:
    return jsonify({"status": "ok"}), 200


@app.route("/calculate", methods=["POST"])
def api_calculate() -> tuple[Response, int]:
    """Return a stateless price estimate."""
    ip = _get_client_ip()
    if not check_rate_limit(ip, Config.PRICES_MAX_REQUESTS_PER_HOUR):
        return _err(
            "Too many requests. Please try again later.",
            "Твърде много заявки. Моля, опитайте по-късно.",
            429,
        )

    body = request.get_json(silent=True) or {}

    validation_error = _validate_calculate_fields(body)
    if validation_error is not None:
        return validation_error

    dist = distance_service.get_distance(
        body.get("origin_city", ""),
        body.get("origin_country", ""),
        body.get("destination", ""),
        body.get("destination_country", ""),
    )

    route_type = _derive_route_type(body)
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    if dist is None:
        calc_record: dict[str, Any] = {
            **body,
            "route_type": route_type,
            "distance_km": "",
            "min_price": "",
            "max_price": "",
            "no_rate": True,
            "timestamp": ts,
            "ip": ip,
        }
        try:
            save_calculation_to_json(calc_record)
            save_calculation_to_csv(calc_record)
        except OSError as exc:
            logger.error("Failed to persist calculation: %s", exc)

        return jsonify({
            "success": True,
            "no_rate": True,
            "message": "Contact us for a custom quote",
            "message_bg": "Свържете се с нас за индивидуална оферта",
        }), 200

    try:
        result = pricing_engine.calculate(body, dist)
    except Exception as exc:
        logger.error("Pricing engine error: %s", exc, exc_info=True)
        return _err(
            "An error occurred while calculating the price.",
            "Възникна грешка при изчисляването на цената.",
            500,
        )

    calc_record = {
        **body,
        "route_type": route_type,
        "distance_km": dist,
        "min_price": result.get("min_price", ""),
        "max_price": result.get("max_price", ""),
        "no_rate": False,
        "timestamp": ts,
        "ip": ip,
    }
    try:
        save_calculation_to_json(calc_record)
        save_calculation_to_csv(calc_record)
    except OSError as exc:
        logger.error("Failed to persist calculation: %s", exc)

    return jsonify(result), 200


@app.route("/quote", methods=["POST"])
def api_quote() -> tuple[Response, int]:
    """Save a quote request and send confirmation emails."""
    ip = _get_client_ip()
    if not check_rate_limit(ip, Config.MAX_SUBMISSIONS_PER_HOUR):
        return _err(
            "Too many submissions. Please try again later.",
            "Твърде много изпращания. Моля, опитайте по-късно.",
            429,
        )

    body = request.get_json(silent=True) or {}

    calc_error = _validate_calculate_fields(body)
    if calc_error is not None:
        return calc_error

    contact_error = _validate_contact_fields(body)
    if contact_error is not None:
        return contact_error

    dist = distance_service.get_distance(
        body.get("origin_city", ""),
        body.get("origin_country", ""),
        body.get("destination", ""),
        body.get("destination_country", ""),
    )

    try:
        if dist is not None:
            price_result = pricing_engine.calculate(body, dist)
        else:
            price_result = {
                "success": True,
                "no_rate": True,
                "message": "Contact us for a custom quote",
                "message_bg": "Свържете се с нас за индивидуална оферта",
            }
    except Exception as exc:
        logger.error("Pricing engine error during quote: %s", exc, exc_info=True)
        return _err(
            "An error occurred while calculating the price.",
            "Възникна грешка при изчисляването на цената.",
            500,
        )

    route_type = _derive_route_type(body)
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    if price_result.get("no_rate"):
        shown_min: Any = ""
        shown_max: Any = ""
    else:
        shown_min = price_result.get("min_price", "")
        shown_max = price_result.get("max_price", "")

    record: dict[str, Any] = {
        **body,
        "route_type": route_type,
        "shown_min_price": shown_min,
        "shown_max_price": shown_max,
        "timestamp": ts,
        "ip": ip,
    }

    try:
        save_quote_to_json(record)
        save_quote_to_csv(record)
    except OSError as exc:
        logger.error("Failed to persist quote: %s", exc)
        return _err(
            "Failed to save your request. Please try again.",
            "Неуспешно запазване на заявката. Моля, опитайте отново.",
            500,
        )

    language: str = str(body.get("language", "en")).lower()
    customer_email = str(body.get("email", "")).strip()

    company_tpl = get_quote_company_notification_template(record, language)
    send_email(Config.COMPANY_EMAIL, company_tpl["subject"], company_tpl["body"])

    if customer_email:
        customer_tpl = get_quote_customer_confirmation_template(record, language)
        send_email(customer_email, customer_tpl["subject"], customer_tpl["body"])

    response_payload: dict[str, Any] = {
        "success": True,
        "message": "Your quote request has been received. We will contact you shortly.",
        "message_bg": "Заявката ви за оферта е получена. Ще се свържем с вас скоро.",
    }

    if not price_result.get("no_rate"):
        response_payload["min_price"] = shown_min
        response_payload["max_price"] = shown_max
        response_payload["currency"] = price_result.get("currency", "EUR")
        response_payload["breakdown"] = price_result.get("breakdown")
        response_payload["disclaimer"] = price_result.get("disclaimer")
        response_payload["disclaimer_bg"] = price_result.get("disclaimer_bg")

    return jsonify(response_payload), 200


@app.route("/contact", methods=["POST"])
def api_contact() -> tuple[Response, int]:
    """Handle a contact-form submission."""
    ip = _get_client_ip()
    if not check_rate_limit(ip, Config.MAX_SUBMISSIONS_PER_HOUR):
        return _err(
            "Too many submissions. Please try again later.",
            "Твърде много изпращания. Моля, опитайте по-късно.",
            429,
        )

    body = request.get_json(silent=True) or {}

    name = str(body.get("name", "")).strip()
    if not (2 <= len(name) <= 100):
        return _err(
            "Name must be between 2 and 100 characters.",
            "Името трябва да е между 2 и 100 символа.",
        )

    email = str(body.get("email", "")).strip()
    phone = str(body.get("phone", "")).strip()
    if not email and not phone:
        return _err(
            "At least one of email or phone is required.",
            "Изисква се поне имейл или телефон.",
        )
    if email and not _validate_email_format(email):
        return _err(
            "Invalid email address format.",
            "Невалиден формат на имейл адрес.",
        )

    message = str(body.get("message", "")).strip()
    if not message:
        return _err("Message is required.", "Съобщението е задължително.")
    if len(message) > 2000:
        return _err(
            "Message must not exceed 2000 characters.",
            "Съобщението не трябва да надвишава 2000 символа.",
        )

    language: str = str(body.get("language", "en")).lower()
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    record: dict[str, Any] = {
        "name": name, "email": email, "phone": phone,
        "message": message, "language": language,
        "timestamp": ts, "ip": ip,
    }

    try:
        save_contact_to_json(record)
        save_contact_to_csv(record)
    except OSError as exc:
        logger.error("Failed to persist contact: %s", exc)
        return _err(
            "Failed to save your message. Please try again.",
            "Неуспешно запазване на съобщението. Моля, опитайте отново.",
            500,
        )

    tpl = get_contact_template(record, language)
    send_email(Config.COMPANY_EMAIL, tpl["subject"], tpl["body"])

    return jsonify({
        "success": True,
        "message": "Your message has been sent. We will get back to you shortly.",
        "message_bg": "Вашето съобщение беше изпратено. Ще се свържем с вас скоро.",
    }), 200


# ===========================================================================
# Error handlers
# ===========================================================================

@app.errorhandler(404)
def not_found(exc: Exception) -> tuple[Response, int]:
    return jsonify({"success": False, "error": "Endpoint not found.", "error_bg": "Крайната точка не е намерена."}), 404


@app.errorhandler(405)
def method_not_allowed(exc: Exception) -> tuple[Response, int]:
    return jsonify({"success": False, "error": "Method not allowed.", "error_bg": "Методът не е разрешен."}), 405


@app.errorhandler(500)
def internal_error(exc: Exception) -> tuple[Response, int]:
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return jsonify({"success": False, "error": "Internal server error.", "error_bg": "Вътрешна сървърна грешка."}), 500


# ===========================================================================
# Application startup
# ===========================================================================

def _bootstrap() -> None:
    global pricing_engine, distance_service

    for warning in Config.validate():
        logger.warning(warning)

    _ensure_submissions_dir()
    logger.info("Submissions directory: %s", Config.SUBMISSIONS_DIR)

    try:
        pricing_engine = PricingEngine(Config.PRICES_FILE)
        logger.info("PricingEngine loaded from: %s", Config.PRICES_FILE)
    except FileNotFoundError as exc:
        logger.critical("Cannot load prices file: %s", exc)
        sys.exit(1)

    cache_path = _BACKEND_DIR / "distances_cache.json"
    distance_service = DistanceService(
        predefined_distances={},
        cache_path=cache_path,
    )
    logger.info("DistanceService initialised (cache: %s)", cache_path)


_bootstrap()

# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == "__main__":
    _debug = os.getenv("FLASK_DEBUG", "false").lower() in ("true", "1", "yes")
    app.run(debug=_debug, port=5000)
