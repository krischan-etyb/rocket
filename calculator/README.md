# Rocket Logistic — Transport Price Calculator

A self-hosted transport price estimation tool built with Flask (Python) and vanilla JavaScript. Visitors receive an instant price range for FTL or LTL shipments without submitting any data, and can optionally submit a formal quote request that triggers confirmation emails to both the customer and the company.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack](#2-tech-stack)
3. [Directory Structure](#3-directory-structure)
4. [Setup Instructions](#4-setup-instructions)
5. [Running the Application](#5-running-the-application)
6. [Running Tests](#6-running-tests)
7. [API Endpoints](#7-api-endpoints)
8. [Bilingual Support](#8-bilingual-support)
9. [Pricing Configuration](#9-pricing-configuration)

---

## 1. Project Overview

**Core objective:** Enable website visitors to instantly see a price estimate for their shipment — with zero form submission — and optionally submit a formal quote request.

### What it does

- Displays a real-time price estimate (min–max range in BGN/EUR) as the user fills in route and cargo details, with a 300 ms debounce so no button click is needed.
- Supports two service types: **FTL** (full truck load) and **LTL** (partial load / pallets).
- Covers domestic Bulgaria routes and international routes to Romania, Greece, and general EU.
- When a price cannot be calculated (unknown route), the UI guides the user to request a manual quote.
- Optionally collects contact details (name, email or phone) and persists a quote request to `submissions/quotes.json` and `submissions/quotes.csv`, while sending notification emails.

### Pricing logic

All pricing rules live in `backend/prices.json` and are applied by `backend/pricing_engine.py`. The pricing data is never sent to the client — only the resulting min/max range is returned.

---

## 2. Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | Python 3.10+ / Flask |
| Pricing engine | Pure Python (`pricing_engine.py`) |
| Email | SMTP via Python `smtplib` (configurable host) |
| Data persistence | JSON + CSV flat files |
| Frontend | Vanilla JavaScript (ES2020), no framework |
| Styling | Vanilla CSS (custom properties, no preprocessor) |
| Testing | pytest |
| Environment config | `python-dotenv` (`.env` file) |

No build step, no npm, no bundler. The frontend is a set of plain `.html`, `.js`, and `.css` files served statically or embedded directly in the existing site pages.

---

## 3. Directory Structure

```
calculator/
├── README.md                    # This file
├── pytest.ini                   # Test runner configuration
├── .gitignore                   # Python, submissions, OS exclusions
│
├── backend/
│   ├── app.py                   # Flask application, route handlers
│   ├── config.py                # Config class loaded from environment
│   ├── pricing_engine.py        # Pricing logic (LTL, FTL, surcharges)
│   ├── email_templates.py       # Email body builders (company + customer)
│   ├── prices.json              # Editable pricing data (BGN rates, surcharges)
│   ├── run.py                   # Convenience startup script
│   └── submissions/
│       ├── .gitkeep             # Keeps directory in git; actual data files are git-ignored
│       ├── quotes.json          # Quote requests (git-ignored)
│       ├── quotes.csv           # Quote requests, spreadsheet format (git-ignored)
│       ├── contacts.json        # Contact form submissions (git-ignored)
│       └── contacts.csv         # Contact form submissions, spreadsheet format (git-ignored)
│
├── frontend/
│   ├── calculator.js            # All calculator JS (estimate + quote submission)
│   └── calculator.css           # Calculator-specific CSS (or appended to main style.css)
│
└── tests/
    ├── __init__.py
    ├── test_pricing_engine.py   # Unit tests for PricingEngine
    ├── test_calculate_api.py    # Integration tests for POST /api/calculate
    └── test_quote_api.py        # Integration tests for POST /api/quote
```

> Note: The `frontend/` files may be co-located with the main site's `js/` and `css/` directories rather than inside `calculator/`. The structure above shows logical ownership; check `CLAUDE.md` or the main site layout for the actual placement used during integration.

---

## 4. Setup Instructions

### Prerequisites

- Python 3.10 or higher
- `pip` (bundled with Python)
- An SMTP server or relay for sending emails (Gmail, SendGrid SMTP, a local mailhog instance, etc.)

### Step 1 — Clone / obtain the project

If the repository has not been initialized yet, copy the project files to your working directory. The working root is the `rocket/` folder containing `CLAUDE.md`.

### Step 2 — Create a virtual environment

Run the following commands from the `calculator/backend/` directory:

```bash
cd calculator/backend

# Create the virtual environment
python -m venv venv

# Activate it — Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Activate it — Windows (CMD)
.\venv\Scripts\activate.bat

# Activate it — macOS / Linux
source venv/bin/activate
```

You should see `(venv)` prepended to your shell prompt after activation.

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` does not yet exist, install the direct dependencies manually and then pin them:

```bash
pip install flask python-dotenv
pip freeze > requirements.txt
```

For development and testing, also install pytest:

```bash
pip install pytest
pip freeze > requirements.txt
```

### Step 4 — Create the `.env` file

Copy the example below to `calculator/backend/.env` and fill in your values. **Never commit this file to version control** — it is excluded by `.gitignore`.

```dotenv
# Flask
FLASK_DEBUG=false
PORT=5000
SECRET_KEY=change-me-to-a-long-random-string

# Email — SMTP credentials
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-smtp-user@example.com
SMTP_PASSWORD=your-smtp-password
COMPANY_EMAIL=info@rocketlogistic.bg
EMAIL_FROM=noreply@rocketlogistic.bg

# Paths (optional — defaults shown)
# PRICES_FILE=backend/prices.json
# PRICES_MAX_REQUESTS_PER_HOUR=60
# MAX_SUBMISSIONS_PER_HOUR=5
```

#### Required variables

| Variable | Description |
|---|---|
| `SECRET_KEY` | Flask session signing key. Use a long random string. |
| `SMTP_HOST` | Hostname of your outbound mail server. |
| `SMTP_PORT` | Usually `587` (STARTTLS) or `465` (SSL). |
| `SMTP_USER` | SMTP login username. |
| `SMTP_PASSWORD` | SMTP login password. |
| `COMPANY_EMAIL` | Address that receives quote notification emails. |
| `EMAIL_FROM` | Sender address shown on outbound emails. |

#### Optional variables

| Variable | Default | Description |
|---|---|---|
| `PORT` | `5000` | Port Flask listens on. |
| `FLASK_DEBUG` | `false` | Set to `true` for auto-reload during development. Never use in production. |
| `PRICES_FILE` | `backend/prices.json` | Path to the pricing config file. |
| `PRICES_MAX_REQUESTS_PER_HOUR` | `60` | Rate limit for `/api/calculate` per IP per hour. |
| `MAX_SUBMISSIONS_PER_HOUR` | `5` | Rate limit for `/api/quote` and `/api/contact` per IP per hour. |

### Step 5 — Verify prices.json exists

The file `calculator/backend/prices.json` must be present before the application starts. `Config.validate()` will raise an error at startup if it is missing. See [Section 9 — Pricing Configuration](#9-pricing-configuration) for the full schema and editing guide.

---

## 5. Running the Application

### Using the convenience startup script (recommended)

```bash
# From calculator/backend/ with the virtual environment active
python run.py
```

Expected output:

```
Starting Rocket Logistic Calculator on http://localhost:5000
 * Running on http://0.0.0.0:5000
```

### Using Flask directly

```bash
# From calculator/backend/ with the virtual environment active
python app.py
```

Or with the Flask CLI:

```bash
export FLASK_APP=app.py        # macOS / Linux
set FLASK_APP=app.py           # Windows CMD
$env:FLASK_APP = "app.py"      # Windows PowerShell

flask run --port 5000
```

### Verifying the server is running

Open a browser and navigate to `http://localhost:5000`. You should see the application, or a JSON health response if a health endpoint is configured. To test the calculate endpoint directly:

```bash
curl -X POST http://localhost:5000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{"service_type":"ftl","origin_country":"BG","origin_city":"Targovishte","destination_country":"BG","destination":"Sofia","cargo_weight_kg":10000}'
```

Expected response:

```json
{
  "success": true,
  "min_price": 837,
  "max_price": 1079,
  "currency": "BGN",
  "breakdown": { "base_price": 850, "fuel_surcharge": 127, "express_surcharge": 0, "dangerous_goods_surcharge": 0 },
  "disclaimer": "Indicative estimate only. Final price subject to confirmation.",
  "disclaimer_bg": "Само приблизителна оценка. Крайната цена подлежи на потвърждение."
}
```

---

## 6. Running Tests

All tests live in `calculator/tests/` and are discovered automatically by pytest.

### Run the full test suite

```bash
# From the calculator/ directory with the virtual environment active
pytest
```

pytest is configured via `calculator/pytest.ini` to look in the `tests/` folder, run verbose output, and show short tracebacks.

### Run a specific test file

```bash
pytest tests/test_pricing_engine.py
pytest tests/test_calculate_api.py
pytest tests/test_quote_api.py
```

### Run a specific test function

```bash
pytest tests/test_pricing_engine.py::TestPricingEngine::test_domestic_ltl_pallet_mode
```

### Run with additional verbosity or stop on first failure

```bash
# Extra verbose output
pytest -vv

# Stop after first failure
pytest -x

# Show print() output
pytest -s
```

### Test categories

| File | What it covers |
|---|---|
| `test_pricing_engine.py` | Unit tests for `PricingEngine`: route type derivation, known domestic routes, fallback by km, international routes, surcharge application, edge cases. |
| `test_calculate_api.py` | Integration tests for `POST /api/calculate`: valid inputs return a price range, non-pallet LTL cargo, unknown routes return `no_rate: true`, malformed requests return 400. |
| `test_quote_api.py` | Integration tests for `POST /api/quote`: successful submission saves data and triggers email mocks, missing contact info returns 400, rate limiting returns 429. |

---

## 7. API Endpoints

All endpoints accept and return JSON. The `Content-Type: application/json` header must be set on all POST requests.

### POST /api/calculate

Stateless estimate endpoint. No data is saved. Called by the frontend on every input change (debounced 300 ms).

**Minimum required fields:**

```json
{
  "service_type": "ltl",
  "origin_country": "BG",
  "origin_city": "Targovishte",
  "destination_country": "BG",
  "destination": "Sofia",
  "num_pallets": 4,
  "total_weight_kg": 1200
}
```

**All supported fields:**

| Field | Type | Required when | Notes |
|---|---|---|---|
| `service_type` | string | Always | `"ftl"` or `"ltl"` |
| `origin_country` | string | Always | ISO 3166-1 alpha-2 (e.g. `"BG"`) |
| `origin_city` | string | Always | Free text, max 100 chars |
| `destination_country` | string | Always | ISO 3166-1 alpha-2 |
| `destination` | string | Always | City name, max 100 chars |
| `num_pallets` | integer | LTL (pallet mode) | 1–33 |
| `total_weight_kg` | number | LTL | Must be > 0 |
| `pallet_type` | string | No | `"eur"` (default) or `"industrial"` |
| `non_pallet_cargo` | boolean | No | `false` (default). When `true`, uses dimensions instead of pallet count |
| `cargo_length_cm` | integer | LTL non-pallet | Must be > 0 |
| `cargo_width_cm` | integer | LTL non-pallet | Must be > 0 |
| `cargo_weight_kg` | number | FTL | Must be > 0 |
| `truck_type` | string | No | `"standard"` (default), `"refrigerated"`, `"flatbed"` |
| `load_date` | string | No | ISO date `YYYY-MM-DD` |
| `date_flexibility` | string | No | `"flexible"` (default) or `"fixed"` (triggers express surcharge) |
| `language` | string | No | `"en"` (default) or `"bg"` |

> `route_type` is NOT sent by the client. The server derives it: `domestic` when both countries are `"BG"`, otherwise `international`.

**Success response — price found (HTTP 200):**

```json
{
  "success": true,
  "min_price": 420,
  "max_price": 520,
  "currency": "BGN",
  "breakdown": {
    "base_price": 400,
    "fuel_surcharge": 60,
    "express_surcharge": 0,
    "dangerous_goods_surcharge": 0
  },
  "disclaimer": "Indicative estimate only. Final price subject to confirmation.",
  "disclaimer_bg": "Само приблизителна оценка. Крайната цена подлежи на потвърждение."
}
```

**Success response — no rate available (HTTP 200):**

```json
{
  "success": true,
  "no_rate": true,
  "message": "Contact us for a custom quote",
  "message_bg": "Свържете се с нас за индивидуална оферта"
}
```

**Validation error (HTTP 400):**

```json
{
  "success": false,
  "error": "num_pallets is required for LTL service"
}
```

**Rate limit exceeded (HTTP 429):**

```json
{
  "success": false,
  "error": "Too many requests. Please try again later.",
  "error_bg": "Твърде много запитвания. Моля, опитайте отново по-късно."
}
```

---

### POST /api/quote

Saves the quote request and sends notification emails. Accepts all fields from `/api/calculate` plus the contact fields below.

**Additional fields:**

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | Yes | 2–100 chars |
| `email` | string | Conditional | Required if `phone` not provided; valid email format |
| `phone` | string | Conditional | Required if `email` not provided; max 50 chars |
| `notes` | string | No | Max 500 chars |
| `shown_min_price` | number | No | Estimate the user saw — logged, not re-validated |
| `shown_max_price` | number | No | Estimate the user saw — logged, not re-validated |

At least one of `email` or `phone` must be present.

**Success response (HTTP 200):**

```json
{
  "success": true,
  "message": "Quote request submitted successfully",
  "message_bg": "Заявката за оферта е изпратена успешно"
}
```

**Persistence:** Appends to `backend/submissions/quotes.json` and `backend/submissions/quotes.csv`. Fields saved: `timestamp`, `name`, `email`, `phone`, `service_type`, `route_type`, `origin_country`, `origin_city`, `destination_country`, `destination`, `num_pallets`, `total_weight_kg`, `pallet_type`, `non_pallet_cargo`, `cargo_length_cm`, `cargo_width_cm`, `cargo_weight_kg`, `truck_type`, `load_date`, `date_flexibility`, `shown_min_price`, `shown_max_price`, `notes`, `language`, `ip`.

---

### POST /api/contact

Existing endpoint — unchanged. Handles the general contact form. See the existing backend documentation for its contract.

---

## 8. Bilingual Support

The calculator is fully bilingual in **English** and **Bulgarian**. Language is inherited from the page's `<html lang>` attribute — no separate language selector is required on the calculator itself.

### How it works

- The main site pages (`index.html` for English, `bg/index.html` for Bulgarian) each set `lang="en"` or `lang="bg"` on the `<html>` element.
- The calculator JavaScript reads `document.documentElement.lang` at initialization and selects the appropriate string set.
- All user-facing strings (labels, placeholders, error messages, estimate states, button text, confirmation messages) have both EN and BG variants defined in a single strings object in `calculator.js`.
- API responses from `/api/calculate` and `/api/quote` return bilingual fields (e.g. `disclaimer` and `disclaimer_bg`) so the frontend can display the correct language without a second request.
- The hidden `language` field is auto-populated from `document.documentElement.lang` before each API call.

### Adding or editing strings

All strings are defined in `frontend/calculator.js` in a `STRINGS` constant. Each key maps to an object with `en` and `bg` properties. To update a translation, edit the corresponding value. To add a new string, add a new key with both language variants.

---

## 9. Pricing Configuration

All pricing data lives in `backend/prices.json`. This file is committed to the repository and is safe to edit — it contains no secrets. No code change or server restart is required to update prices; the pricing engine re-reads the file at startup (and can be extended to hot-reload if needed).

### File location

```
calculator/backend/prices.json
```

### Top-level structure

```jsonc
{
  "settings": {
    "currency": "BGN",
    "price_range_pct": 12        // ± spread applied to produce min/max estimate
  },
  "surcharges": {
    "fuel_pct": 15,              // % added to base price on every shipment
    "express_pct": 25,           // % added when date_flexibility == "fixed"
    "dangerous_goods_pct": 30    // reserved for v2
  },
  "truck_type_multipliers": { ... },
  "domestic": { ... },
  "international": { ... }
}
```

### Editing domestic routes

Each known city pair is stored as `"origin|destination"` (lowercase). Both directions must be listed separately if the rate differs.

```jsonc
"domestic": {
  "routes": {
    "targovishte|sofia": {
      "ftl_base_bgn": 850,       // Full truck base price in BGN
      "ltl_per_pallet_bgn": 42,  // LTL rate per pallet
      "ltl_per_100kg_bgn": 14    // LTL rate per 100 kg
    }
  }
}
```

To add a new domestic route, copy an existing entry and adjust the values:

```jsonc
"plovdiv|sofia": { "ftl_base_bgn": 400, "ltl_per_pallet_bgn": 20, "ltl_per_100kg_bgn": 7 },
"sofia|plovdiv": { "ftl_base_bgn": 400, "ltl_per_pallet_bgn": 20, "ltl_per_100kg_bgn": 7 }
```

### Extending the domestic fallback

For city pairs not explicitly listed, the engine estimates the distance using `known_city_coords_km_from_sofia` (a simple lookup table of approximate distance from Sofia in km). Add new cities here to enable fallback pricing:

```jsonc
"known_city_coords_km_from_sofia": {
  "sofia": 0,
  "plovdiv": 150,
  "burgas": 390,
  "varna": 440,
  "sliven": 270           // newly added city
}
```

If either city in a pair is absent from this table, the engine returns `no_rate: true` and the frontend shows "Contact us for a custom quote."

### Editing international rates

Each country is keyed by its ISO 3166-1 alpha-2 code. The `"EU"` key is a catch-all for countries not individually listed.

```jsonc
"international": {
  "countries": {
    "RO": {
      "ftl_base_bgn": 2600,
      "ltl_per_pallet_bgn": 120,
      "ltl_per_100kg_bgn": 38,
      "ltl_min_charge_bgn": 180    // minimum charge for any LTL shipment
    },
    "DE": {                        // newly added country
      "ftl_base_bgn": 5800,
      "ltl_per_pallet_bgn": 260,
      "ltl_per_100kg_bgn": 80,
      "ltl_min_charge_bgn": 400
    }
  }
}
```

### Editing surcharges and multipliers

```jsonc
"surcharges": {
  "fuel_pct": 15,       // Increase to 18 to reflect higher fuel costs
  "express_pct": 25
},
"truck_type_multipliers": {
  "standard": 1.0,
  "refrigerated": 1.35,  // 35% premium for refrigerated trucks
  "flatbed": 1.20
}
```

### How the price range is calculated

The engine calculates a single `base_price`, applies surcharges, then spreads by `price_range_pct` to produce the displayed range:

```
with_surcharges = base_price * (1 + fuel_pct / 100)
# if fixed date: with_surcharges *= (1 + express_pct / 100)

min_price = round(with_surcharges * (1 - price_range_pct / 100))
max_price = round(with_surcharges * (1 + price_range_pct / 100))
```

For LTL, `base_price = max(weight_based_price, pallet_based_price)`. The higher of the two methods is always charged.

### Important: confirm rates before go-live

The rates in the committed `prices.json` are initial estimates. **Review and confirm all rates with the company owner before making the calculator publicly accessible.**

---

*Last updated: 2026-03-10*
