# Backend Spec — Rocket Logistic Price Calculator

**Document version:** 1.0
**Date:** 2026-03-06
**Author:** backend-architect

---

## 1. Executive Summary

This document specifies the pricing model, data schema, and Flask API design for the Rocket Logistic transport price calculator. Two new endpoints are added alongside the existing `/api/contact`: `POST /api/calculate` for stateless instant estimates, and `POST /api/quote` for formal quote submissions. All pricing data lives in a server-side `prices.json` file — never exposed to the client. The design is intentionally minimal: it reuses the existing rate-limiting, validation, JSON/CSV storage, and email patterns already established in `app.py` and `config.py`.

---

## 2. Architecture Overview

```
Frontend (vanilla JS)
    |
    |-- POST /api/calculate  (instant estimate, stateless, no persistence)
    |-- POST /api/quote      (formal quote: saves to JSON+CSV, sends emails)
    |-- POST /api/contact    (existing, unchanged)
    |
Flask app (app.py)
    |
    |-- PricingEngine        (new module: pricing_engine.py)
    |       |-- loads prices.json at startup (or on demand)
    |       |-- zone matrix lookup for domestic routes
    |       |-- country/zone lookup for international routes
    |       |-- LTL per-pallet / per-100kg calculation
    |       |-- FTL flat rate calculation
    |       |-- surcharge application
    |       |-- fallback estimation when exact rate missing
    |
    |-- prices.json          (human-editable, never served to client)
    |-- submissions/
            |-- quotes.json
            |-- quotes.csv
```

The pricing engine is a standalone module so it can be unit-tested independently of Flask.

---

## 3. Service Definitions

### 3.1 PricingEngine (`backend/pricing_engine.py`)

Responsibilities:
- Load and cache `prices.json` from the path in `Config.PRICES_FILE`
- Expose a single public method: `calculate(params) -> dict`
- Implement zone-matrix lookup for domestic BG fixed routes
- Implement country-level flat rate lookup for international routes
- Apply LTL calculation: `base_rate * num_pallets` with weight-based cap
- Apply FTL calculation: flat route rate adjusted by truck type multiplier
- Apply surcharges (fuel, express, dangerous goods)
- Return `(min_price, max_price)` tuple in BGN, or `no_rate=True` when no applicable rate exists

### 3.2 `/api/calculate` handler

Responsibilities:
- Parse and validate incoming JSON (service type, route, cargo)
- Apply same in-memory rate limiting as `/api/contact`
- Delegate to PricingEngine
- Return price range or no-rate signal — no persistence

### 3.3 `/api/quote` handler

Responsibilities:
- All of the above validation
- Persist to `submissions/quotes.json` and `submissions/quotes.csv`
- Send company notification email (full shipment + contact details)
- Send customer confirmation email
- Reuse existing `send_email()`, `save_to_json()`, `save_to_csv()` helpers

---

## 4. API Contracts

### 4.1 POST /api/calculate

**Request**

```json
{
  "service_type":   "ltl",
  "route_type":     "domestic",
  "origin_city":    "Targovishte",
  "destination":    "Sofia",
  "num_pallets":    4,
  "total_weight_kg": 1200,
  "pallet_type":    "eur",
  "cargo_weight_kg": null,
  "truck_type":     null,
  "load_date":      "2026-03-20",
  "date_flexibility": "flexible",
  "language":       "en"
}
```

Field rules:
- `service_type`: required, enum `["ftl", "ltl"]`
- `route_type`: required, enum `["domestic", "international"]`
- `origin_city`: required, string, max 100 chars
- `destination`: required, string (city name for domestic, country code for international: `"RO"`, `"GR"`, `"EU"`)
- `num_pallets`: required when `service_type == "ltl"`, integer 1–33
- `total_weight_kg`: required when `service_type == "ltl"`, number > 0
- `pallet_type`: optional, enum `["eur", "industrial"]`, default `"eur"`
- `cargo_weight_kg`: required when `service_type == "ftl"`, number > 0
- `truck_type`: optional, enum `["standard", "refrigerated", "flatbed"]`, default `"standard"`
- `load_date`: optional, ISO date string `YYYY-MM-DD`
- `date_flexibility`: optional, enum `["flexible", "fixed"]`
- `language`: optional, enum `["en", "bg"]`, default `"en"`

**Success response — price found (200)**

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

**Success response — no rate available (200)**

```json
{
  "success": true,
  "no_rate": true,
  "message": "Contact us for a custom quote",
  "message_bg": "Свържете се с нас за индивидуална оферта"
}
```

**Error responses**

```json
// 400 — validation failure
{
  "success": false,
  "error": "num_pallets is required for LTL service"
}

// 429 — rate limit exceeded
{
  "success": false,
  "error": "Too many requests. Please try again later.",
  "error_bg": "Твърде много запитвания. Моля, опитайте отново по-късно."
}

// 500 — unexpected error
{
  "success": false,
  "error": "Unable to calculate — please contact us."
}
```

---

### 4.2 POST /api/quote

**Request** — all `/api/calculate` fields plus contact fields:

```json
{
  "service_type":    "ftl",
  "route_type":      "international",
  "origin_city":     "Sofia",
  "destination":     "RO",
  "cargo_weight_kg": 18000,
  "truck_type":      "standard",
  "load_date":       "2026-03-25",
  "date_flexibility": "fixed",
  "shown_min_price": 2400,
  "shown_max_price": 2900,
  "name":            "Ivan Petrov",
  "email":           "ivan@example.com",
  "phone":           "+359 88 123 4567",
  "notes":           "Fragile machinery parts, no stacking.",
  "language":        "bg"
}
```

Additional field rules beyond `/api/calculate`:
- `name`: required, 2–100 chars
- `email`: required, valid email
- `phone`: optional, max 50 chars
- `notes`: optional, max 500 chars
- `shown_min_price`, `shown_max_price`: optional numbers — the estimate the user saw; logged for company context but not re-validated

**Success response (200)**

```json
{
  "success": true,
  "message": "Quote request submitted successfully",
  "message_bg": "Заявката за оферта е изпратена успешно"
}
```

**Error responses** — same shape as `/api/contact` and `/api/calculate`.

---

## 5. Data Schema

### 5.1 prices.json

Full schema with sample data for 4 domestic routes and 2 international destinations:

```json
{
  "_comment": "Rocket Logistic pricing config. All prices in BGN. Edit rates here — no code change required.",
  "_version": "1.0",

  "settings": {
    "currency": "BGN",
    "price_range_pct": 12,
    "comment_price_range_pct": "Min/max spread around base price as a percentage (e.g. 12 = base-12% to base+12%)"
  },

  "surcharges": {
    "fuel_pct": 15,
    "comment_fuel_pct": "Fuel surcharge as % of base price. Update when fuel costs change.",
    "express_pct": 25,
    "comment_express_pct": "Express / fixed-date surcharge as % of base price.",
    "dangerous_goods_pct": 30,
    "comment_dangerous_goods_pct": "ADR dangerous goods surcharge as % of base price."
  },

  "truck_type_multipliers": {
    "standard":     1.0,
    "refrigerated": 1.35,
    "flatbed":      1.20
  },

  "domestic": {
    "comment": "Fixed domestic BG routes. Key format: 'ORIGIN|DESTINATION' (lowercase, ASCII). Both directions should be listed.",
    "routes": {
      "burgas|sofia": {
        "ftl_base_bgn": 1100,
        "ltl_per_pallet_bgn": 55,
        "ltl_per_100kg_bgn": 18,
        "comment": "Burgas — Sofia, ~400 km"
      },
      "sofia|burgas": {
        "ftl_base_bgn": 1100,
        "ltl_per_pallet_bgn": 55,
        "ltl_per_100kg_bgn": 18
      },
      "varna|sofia": {
        "ftl_base_bgn": 1050,
        "ltl_per_pallet_bgn": 52,
        "ltl_per_100kg_bgn": 17,
        "comment": "Varna — Sofia, ~450 km"
      },
      "sofia|varna": {
        "ftl_base_bgn": 1050,
        "ltl_per_pallet_bgn": 52,
        "ltl_per_100kg_bgn": 17
      },
      "targovishte|sofia": {
        "ftl_base_bgn": 850,
        "ltl_per_pallet_bgn": 42,
        "ltl_per_100kg_bgn": 14,
        "comment": "Targovishte — Sofia, ~300 km"
      },
      "sofia|targovishte": {
        "ftl_base_bgn": 850,
        "ltl_per_pallet_bgn": 42,
        "ltl_per_100kg_bgn": 14
      },
      "targovishte|burgas": {
        "ftl_base_bgn": 600,
        "ltl_per_pallet_bgn": 30,
        "ltl_per_100kg_bgn": 10,
        "comment": "Targovishte — Burgas, ~200 km"
      },
      "burgas|targovishte": {
        "ftl_base_bgn": 600,
        "ltl_per_pallet_bgn": 30,
        "ltl_per_100kg_bgn": 10
      },
      "targovishte|varna": {
        "ftl_base_bgn": 420,
        "ltl_per_pallet_bgn": 22,
        "ltl_per_100kg_bgn": 8,
        "comment": "Targovishte — Varna, ~140 km"
      },
      "varna|targovishte": {
        "ftl_base_bgn": 420,
        "ltl_per_pallet_bgn": 22,
        "ltl_per_100kg_bgn": 8
      }
    },
    "fallback_per_km": {
      "comment": "Used when the exact city pair is not listed above. Owner must supply approximate km between cities.",
      "ftl_bgn_per_km": 2.80,
      "ltl_bgn_per_pallet_per_km": 0.14,
      "ltl_bgn_per_100kg_per_km": 0.045
    },
    "known_city_coords_km_from_sofia": {
      "comment": "Straight-line km from Sofia — used only for rough fallback distance estimation.",
      "sofia": 0,
      "plovdiv": 150,
      "burgas": 390,
      "varna": 440,
      "targovishte": 300,
      "ruse": 300,
      "stara zagora": 220,
      "pleven": 170
    }
  },

  "international": {
    "comment": "Country-level rates. 'destination' in request maps to these keys (uppercase ISO code or 'EU').",
    "countries": {
      "RO": {
        "comment": "Romania — served via Ruse/Giurgiu border",
        "ftl_base_bgn": 2600,
        "ltl_per_pallet_bgn": 120,
        "ltl_per_100kg_bgn": 38,
        "ltl_min_charge_bgn": 180
      },
      "GR": {
        "comment": "Greece — served via Kulata border",
        "ftl_base_bgn": 2200,
        "ltl_per_pallet_bgn": 100,
        "ltl_per_100kg_bgn": 32,
        "ltl_min_charge_bgn": 150
      },
      "EU": {
        "comment": "General EU — placeholder rate. Owner should split into specific countries as data becomes available.",
        "ftl_base_bgn": 4500,
        "ltl_per_pallet_bgn": 200,
        "ltl_per_100kg_bgn": 65,
        "ltl_min_charge_bgn": 300
      }
    }
  }
}
```

#### How the owner fills in partial data

Fields marked with `_base_bgn` or `_per_pallet_bgn` are the primary inputs. When a route is unknown:
- If the owner knows an approximate distance in km, they add the city to `known_city_coords_km_from_sofia` and the engine falls back to `fallback_per_km` rates.
- If no distance is known, the engine returns `no_rate: true` and the frontend shows the "contact us" message.
- New countries can be added to `international.countries` by copy-pasting an existing entry and changing the rates.

---

### 5.2 quotes.json / quotes.csv

Quote submissions follow the same append pattern as `contacts.json`/`contacts.csv`. Fields saved:

```
timestamp, name, email, phone, service_type, route_type, origin_city,
destination, num_pallets, total_weight_kg, pallet_type, cargo_weight_kg,
truck_type, load_date, date_flexibility, shown_min_price, shown_max_price,
notes, language, ip
```

CSV fieldnames list must be defined in `save_quote_to_csv()` in the same order, matching the pattern in `save_to_csv()`.

---

## 6. Pricing Calculation Logic

### LTL price

```
weight_based  = (total_weight_kg / 100) * ltl_per_100kg_bgn
pallet_based  = num_pallets * ltl_per_pallet_bgn
base_price    = max(weight_based, pallet_based)         # charge the higher
base_price    = max(base_price, ltl_min_charge_bgn)     # apply minimum (international only)

with_surcharges = base_price * (1 + fuel_pct/100)
# + express_pct if date_flexibility == "fixed"
# + dangerous_goods_pct if flagged (v2 — not in v1 inputs)

min_price = round(with_surcharges * (1 - price_range_pct/100))
max_price = round(with_surcharges * (1 + price_range_pct/100))
```

### FTL price

```
base_price    = ftl_base_bgn * truck_type_multiplier

with_surcharges = base_price * (1 + fuel_pct/100)
# + express_pct if date_flexibility == "fixed"

min_price = round(with_surcharges * (1 - price_range_pct/100))
max_price = round(with_surcharges * (1 + price_range_pct/100))
```

### Domestic fallback (route not in matrix)

When `origin_city|destination` key is absent from `domestic.routes`:
1. Look up both cities in `known_city_coords_km_from_sofia`.
2. Estimate distance as `abs(origin_km - destination_km)` (rough but sufficient for fallback).
3. Apply `fallback_per_km` rates.
4. If either city is unknown, return `no_rate: true`.

---

## 7. Config Extension

Add the following to `config.py` inside the `Config` class, following the existing file-path pattern:

```python
# Pricing configuration
PRICES_FILE = os.path.join(BASE_DIR, 'prices.json')
PRICES_MAX_REQUESTS_PER_HOUR = int(os.getenv('PRICES_MAX_REQUESTS_PER_HOUR', 60))
```

`PRICES_MAX_REQUESTS_PER_HOUR` is intentionally higher than `MAX_SUBMISSIONS_PER_HOUR` (5) because calculate is a read-only, no-email endpoint called on every input change.

No `.env` variable is required for `PRICES_FILE` — the path relative to `BASE_DIR` is sufficient. If the owner ever wants to override it, they add `PRICES_FILE=/path/to/prices.json` to `.env` and the class attribute becomes:

```python
PRICES_FILE = os.getenv('PRICES_FILE', os.path.join(BASE_DIR, 'prices.json'))
```

`Config.validate()` should be extended to check that `PRICES_FILE` exists on startup and raise a clear error if it does not:

```python
if not os.path.exists(cls.PRICES_FILE):
    errors.append(f"PRICES_FILE not found: {cls.PRICES_FILE}")
```

---

## 8. Quote Request Integration (POST /api/quote)

The `/api/quote` endpoint is a superset of `/api/contact`. It does NOT replace `/api/contact` — the existing contact form keeps using `/api/contact` unchanged.

Shared infrastructure reused without modification:
- `check_rate_limit(ip)` — same function, same in-memory tracker
- `send_email()` / `send_email_sendgrid()` / `send_email_mailgun()` — called identically
- `save_to_json()` / `save_to_csv()` — called with a different file path (`Config.QUOTES_JSON_FILE`, `Config.QUOTES_CSV_FILE`) and a wider field set

Two new email templates are needed (in `email_templates.py`):
- `get_quote_company_notification_template(data, language)` — includes full cargo details
- `get_quote_customer_confirmation_template(data, language)` — acknowledges the quote request

The message body sent to the company email should include a formatted summary of all cargo fields, so the team can act on it without opening the CSV. Sample fields to include: service type, route, cargo description, shown estimate, desired date.

Add to `Config`:
```python
QUOTES_DIR    = os.path.join(BASE_DIR, 'submissions')   # reuse same dir
QUOTES_JSON   = os.path.join(SUBMISSIONS_DIR, 'quotes.json')
QUOTES_CSV    = os.path.join(SUBMISSIONS_DIR, 'quotes.csv')
```

---

## 9. Key Considerations

### Scalability

At the current scale (small Bulgarian logistics company), in-memory rate limiting and file-based storage are appropriate. When traffic grows:
- Replace `submission_tracker` dict with Redis for rate limiting across multiple workers.
- Replace JSON/CSV file storage with a simple SQLite or PostgreSQL table.
- The `PricingEngine` can be instantiated once at module load and cached — pricing data rarely changes, so there is no need to reload `prices.json` on every request. A simple module-level singleton is sufficient.

### Security

- Pricing data (`prices.json`) is never returned in any API response — not even partially. The response only contains computed `min_price`/`max_price`.
- `shown_min_price` / `shown_max_price` sent by the client in a quote request are logged for context but never trusted for pricing — the server always recomputes from its own data.
- Input validation rejects unexpected fields; numeric fields are clamped to reasonable bounds (max pallets 33, max weight 50,000 kg) to prevent abuse of the calculation loop.
- CORS is already locked to `Config.ALLOWED_ORIGINS`; `/api/calculate` and `/api/quote` fall under the same `r"/api/*"` rule.

### Observability

- `app.logger.error()` is used in all exception handlers, consistent with existing code.
- Log lines should include: endpoint name, client IP, route key attempted, and whether a rate was found — sufficient to debug pricing gaps without logging PII.
- A future health-check extension of `/api/health` could report `prices_file_loaded: true/false` and `prices_version`.

### Deployment & CI/CD

- `prices.json` should be committed to the repository (it contains no secrets) so it is deployed alongside the code. The owner edits rates via a git commit or directly on the server.
- No new pip dependencies are required — the pricing engine uses only the Python standard library (`json`, `os`, `math`).
- The existing Gunicorn / Flask startup sequence (`Config.validate()` → `app.run()`) naturally validates `PRICES_FILE` presence before the server accepts traffic.

---

## 10. Implementation Checklist

For the developer implementing this spec:

- [ ] Add `PRICES_FILE`, `PRICES_MAX_REQUESTS_PER_HOUR`, `QUOTES_JSON`, `QUOTES_CSV` to `config.py`
- [ ] Extend `Config.validate()` to check `PRICES_FILE` exists
- [ ] Create `backend/prices.json` using the schema in section 5.1 (fill real rates with owner)
- [ ] Create `backend/pricing_engine.py` implementing the logic in section 6
- [ ] Add `POST /api/calculate` handler to `app.py`
- [ ] Add `POST /api/quote` handler to `app.py`
- [ ] Add `save_quote_to_json()` and `save_quote_to_csv()` helpers (or generalize existing helpers)
- [ ] Add `get_quote_company_notification_template()` and `get_quote_customer_confirmation_template()` to `email_templates.py`
- [ ] Unit test `PricingEngine` for: known domestic route LTL, known domestic route FTL, domestic fallback, international LTL, international FTL, no-rate case
- [ ] Integration test: POST /api/calculate returns 200 with price range for valid input
- [ ] Integration test: POST /api/quote returns 200, saves record, triggers email
