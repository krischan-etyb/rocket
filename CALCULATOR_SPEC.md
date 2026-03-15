# CALCULATOR_SPEC.md
# Rocket Logistic — Transport Price Calculator

**Version:** 1.0
**Date:** 2026-03-06
**Status:** Ready for implementation

---

## Table of Contents

1. [Core Objective](#1-core-objective)
2. [User Stories](#2-user-stories)
3. [Services Covered](#3-services-covered)
4. [Input Fields](#4-input-fields)
5. [UX Flow & Form Structure](#5-ux-flow--form-structure)
6. [Estimate Display](#6-estimate-display)
7. [Quote Submission Flow](#7-quote-submission-flow)
8. [Validation Rules](#8-validation-rules)
9. [Bilingual Requirements](#9-bilingual-requirements)
10. [Backend API Contracts](#10-backend-api-contracts)
11. [Pricing Model](#11-pricing-model)
12. [Data Schema — prices.json](#12-data-schema--pricesjson)
13. [Data Persistence — quotes.json / quotes.csv](#13-data-persistence--quotesjson--quotescsv)
14. [Config Extensions](#14-config-extensions)
15. [CSS Components & Page Integration](#15-css-components--page-integration)
16. [Responsive Layout](#16-responsive-layout)
17. [Accessibility](#17-accessibility)
18. [Implementation Checklist](#18-implementation-checklist)

---

## 1. Core Objective

Enable website visitors to instantly see a price estimate for their shipment — with zero form submission — and optionally submit a formal quote request that sends an email to Rocket Logistic and a confirmation to the customer.

---

## 2. User Stories

### Instant Estimate (no submission required)

| ID | Story |
|---|---|
| US-01 | As a visitor, I want to select FTL or LTL so the form shows relevant cargo fields. |
| US-02 | As a visitor, I want to select origin and destination countries so the route type (domestic / international) is determined automatically and destination options update accordingly. |
| US-03 | As a visitor doing LTL, I want to enter number of pallets and total weight so I get a rate estimate. |
| US-03b | As a visitor doing LTL with non-standard cargo, I want to check a box and enter cargo dimensions so the price accounts for floor space used. |
| US-04 | As a visitor doing FTL, I want to select truck type and enter cargo weight so I get a full-truck price estimate. |
| US-05 | As a visitor, I want the price estimate to update instantly as I change inputs, without clicking a submit button. |
| US-06 | As a Bulgarian-speaking visitor, I want all labels and messages to appear in Bulgarian. |
| US-07 | As an English-speaking visitor, I want all labels and messages to appear in English. |

### Formal Quote Request (optional)

| ID | Story |
|---|---|
| US-08 | As a visitor who has seen the estimate, I want to submit my contact details to request a formal quote. |
| US-09 | As a visitor, I want to receive a confirmation email acknowledging my quote request. |
| US-10 | As the company, I want to receive an email with the full shipment details and contact information. |

---

## 3. Services Covered

| Service | Domestic BG | RO | GR | General EU |
|---|---|---|---|---|
| FTL — Full Truck Load | Yes | Yes | Yes | Yes |
| LTL — Partial Load / Pallets | Yes | Yes | Yes | Yes |

**Known domestic routes with fixed pricing:**

| Route | Approx. km |
|---|---|
| Targovishte — Sofia | ~300 km |
| Targovishte — Burgas | ~200 km |
| Targovishte — Varna | ~140 km |
| Burgas — Sofia | ~400 km |
| Varna — Sofia | ~450 km |

Unlisted city pairs fall back to a per-km rate (see Section 11.3).

---

## 4. Input Fields

### Group 1 — Service Type (always visible)

| Field | Type | Required | Values |
|---|---|---|---|
| `service_type` | Tab toggle (radio) | Yes | `ftl`, `ltl` |

### Group 2 — Route Details

Route type (domestic vs international) is **derived**: if `origin_country == destination_country == "BG"` → domestic; otherwise → international.

| Field | Type | Required | Notes |
|---|---|---|---|
| `origin_country` | Select | Yes | Two-letter ISO code (e.g. `BG`, `RO`, `GR`, `DE`, …) |
| `origin_city` | Select + free-text fallback | Yes | Known cities pre-populated based on origin country |
| `destination_country` | Select | Yes | Two-letter ISO code (e.g. `BG`, `RO`, `GR`, `DE`, …) |
| `destination` | Select + free-text fallback | Yes | Cities/regions filtered by destination country; for BG: Sofia / Burgas / Varna / Targovishte |

### Group 3 — Cargo Details (LTL path)

| Field | Type | Required | Constraints |
|---|---|---|---|
| `num_pallets` | Number | Yes | Integer 1–33 |
| `total_weight_kg` | Number | Yes | Positive integer |
| `pallet_type` | Select | No | `eur` (120×80 cm), `industrial` (120×100 cm) |
| `non_pallet_cargo` | Checkbox | No | When checked: hides `pallet_type`, unlocks `cargo_length_cm` and `cargo_width_cm` |
| `cargo_length_cm` | Number | Conditional | Positive integer (cm); enabled only when `non_pallet_cargo` is checked |
| `cargo_width_cm` | Number | Conditional | Positive integer (cm); enabled only when `non_pallet_cargo` is checked |

### Group 3 — Cargo Details (FTL path)

| Field | Type | Required | Constraints |
|---|---|---|---|
| `cargo_weight_kg` | Number | Yes | Positive integer |
| `truck_type` | Select | No | `standard` (curtainsider), `refrigerated`, `flatbed` |

### Group 3 — Optional (both paths, collapsed by default)

| Field | Type | Required | Notes |
|---|---|---|---|
| `load_date` | Date picker | No | ISO date YYYY-MM-DD |
| `date_flexibility` | Radio | No | `flexible`, `fixed` (fixed triggers express surcharge) |

### Group 5 — Quote Contact Extension (revealed on CTA click)

| Field | Type | Required | Constraints |
|---|---|---|---|
| `name` | Text | Yes | 2–100 chars |
| `email` | Email | Conditional | Required if `phone` not provided; valid email format |
| `phone` | Tel | Conditional | Required if `email` not provided; max 50 chars |
| `notes` | Textarea | No | Max 500 chars |
| `language` | Hidden | Yes | Auto-populated from `document.documentElement.lang` |
| `shown_min_price` | Hidden | No | Estimate min shown to user — logged but not trusted server-side |
| `shown_max_price` | Hidden | No | Estimate max shown to user — logged but not trusted server-side |

---

## 5. UX Flow & Form Structure

### Design Decision: Single-page progressive disclosure

All fields appear on one scrollable page grouped into logical visual sections. Fields in later groups are revealed as earlier groups are completed. A full wizard/multi-step screen is not used — the low field count (7–10 required fields) does not justify the navigation overhead, and real-time estimate updates require all inputs to be simultaneously accessible by the JS calculation logic.

### Flow A — Instant Estimate

```
1. User arrives at #calculate section (nav link or hero CTA)
2. Group 1 — Select service type (FTL / LTL)
3. Group 2 — Select origin country + city, destination country + city
   (route type domestic/international is derived automatically from country selection;
    destination city options filter based on destination country)
4. Group 3 — Enter cargo details (fields differ by service type)
   LTL: if non-standard cargo, check box and enter length + width
   Optional: expand load date / date flexibility
5. Estimate panel updates in real time (debounced 300ms after last input change)
6. User reads estimate — flow complete, no submission required
```

### Flow B — Formal Quote (optional extension)

```
Precondition: estimate is displayed (price-found or no-rate state)
1. User clicks "Request Formal Quote" CTA
2. Quote extension panel (Group 5) expands inline below the estimate card
3. Cargo summary shown read-only above contact fields:
   e.g. "FTL  |  BG Targovishte → BG Sofia  |  12,000 kg  |  Curtainsider"
   or   "LTL  |  BG Targovishte → RO Bucharest  |  4 pallets  |  1,200 kg"
   or   "LTL  |  BG Sofia → GR Athens  |  non-pallet 150×90 cm  |  800 kg"
4. User fills in name, email and/or phone, notes (optional)
5. User clicks "Submit Quote Request"
6. Per-field inline validation runs
7. On success: quote form is replaced by confirmation message inline (no reload)
8. Company receives email; customer receives confirmation email
9. CTA button changes to "Quote submitted" and becomes disabled
```

### Form Layout (desktop)

The calculator uses a two-column grid:
- **Left column**: the form (Groups 1–3 + optional fields + quote extension)
- **Right column**: the estimate card (sticky, always visible while scrolling the form)

On mobile (≤768px): single column, estimate card flows naturally below the last input group (not sticky on mobile).

---

## 6. Estimate Display

The estimate panel is always visible once Group 1 is complete. It transitions between four states:

### State 1 — Incomplete inputs
```
┌────────────────────────────────────────────────┐
│  Estimated price / Приблизителна цена          │
│                                                │
│  Fill in details above to see estimate.        │
│  Попълнете данните, за да видите оценката.     │
└────────────────────────────────────────────────┘
```
Visual: muted grey card.

### State 2 — Price found
```
┌────────────────────────────────────────────────┐
│  Estimated price / Приблизителна цена          │
│                                                │
│       1,200 – 1,500 BGN                        │
│       (approx. 615 – 768 EUR)                  │
│                                                │
│  ! Indicative estimate only. Final price       │
│    subject to confirmation.                    │
│                                                │
│  [ REQUEST FORMAL QUOTE ]                      │
└────────────────────────────────────────────────┘
```
Visual: accent-colored top border (`--color-brand-green`), large bold price, disclaimer in small italic text, prominent CTA button.

Price in BGN primary; EUR secondary calculated at a fixed exchange rate (configurable in `prices.json`).

### State 3 — No rate available
```
┌────────────────────────────────────────────────┐
│  Estimated price / Приблизителна цена          │
│                                                │
│  Contact us for a custom quote.                │
│  Свържете се с нас за индивидуална оферта.     │
│                                                │
│  [ REQUEST FORMAL QUOTE ]                      │
└────────────────────────────────────────────────┘
```

### State 4 — API error
```
┌────────────────────────────────────────────────┐
│  Unable to calculate — please contact us.      │
│  Не може да се изчисли — моля свържете се.     │
└────────────────────────────────────────────────┘
```
Visual: amber/orange border. No CTA shown.

### Loading behavior
- A CSS spinner (`.calc-spinner__ring`) replaces the price number during the API call.
- State transitions use CSS opacity transition (~150ms).
- API call is debounced 300ms after the last input change.
- The estimate panel uses `aria-live="polite"` so screen readers announce updates.

---

## 7. Quote Submission Flow

1. Hidden fields are auto-populated on CTA click:
   - `language` from `document.documentElement.lang`
   - `shown_min_price` / `shown_max_price` from last successful estimate response
2. All calculator inputs carry through to the POST — no re-entry required.
3. On `POST /api/quote` success:
   - Quote panel replaced by inline confirmation message
   - CTA button text changes to "Quote submitted" / "Заявката е изпратена" and is disabled
4. On failure: inline error message appears, form remains editable.

---

## 8. Validation Rules

### Calculator fields (client-side, prevents API call)

| Field | Rule | EN Error | BG Error |
|---|---|---|---|
| `service_type` | Must be selected | Please select a service type. | Моля изберете вид услуга. |
| `origin_country` | Must be selected | Please select an origin country. | Моля изберете държава на тръгване. |
| `origin_city` | Must be selected or entered | Please enter an origin city. | Моля въведете град на тръгване. |
| `destination_country` | Must be selected | Please select a destination country. | Моля изберете държава на дестинация. |
| `destination` | Must be selected or entered | Please select a destination. | Моля изберете дестинация. |
| `num_pallets` | Integer 1–33 (LTL, pallet mode only) | Enter a number of pallets between 1 and 33. | Въведете брой палети между 1 и 33. |
| `total_weight_kg` | Positive integer (LTL only) | Enter a valid total weight in kg. | Въведете валидно общо тегло в кг. |
| `cargo_length_cm` | Positive integer (LTL, non-pallet only) | Enter a valid cargo length in cm. | Въведете валидна дължина на товара в см. |
| `cargo_width_cm` | Positive integer (LTL, non-pallet only) | Enter a valid cargo width in cm. | Въведете валидна ширина на товара в см. |
| `cargo_weight_kg` | Positive integer (FTL only) | Enter a valid cargo weight in kg. | Въведете валидно тегло на товара в кг. |

### Quote contact fields (on form submit)

| Field | Rule | EN Error | BG Error |
|---|---|---|---|
| `name` | 2–100 chars | Name must be between 2 and 100 characters. | Името трябва да е между 2 и 100 знака. |
| `email` / `phone` | At least one must be provided | Please enter an email address or phone number. | Моля въведете имейл адрес или телефонен номер. |
| `email` | Valid email format (if provided) | Please enter a valid email address. | Моля въведете валиден имейл адрес. |
| `notes` | Max 500 chars if provided | Notes must not exceed 500 characters. | Бележките не трябва да надвишават 500 знака. |

### Error display pattern
- Errors appear inline, directly below the offending field (not in a top summary block).
- Each error uses `<span role="alert">` styled in `--color-error`.
- The field receives `aria-invalid="true"` and a visible red border.
- Errors clear on the `input` event (not only on re-submit).
- Submit button is not disabled in advance — shows all errors on first attempt.
- Estimate panel does not show validation errors; it simply stays in the "incomplete" state.

---

## 9. Bilingual Requirements

Language is inherited from the page `<html lang>` attribute (`en` or `bg`). All user-facing strings have both EN and BG versions.

### Complete String Table

| Key | EN | BG |
|---|---|---|
| `calc_title` | Get a Price Estimate | Получете ценова оферта |
| `service_type_label` | Service Type | Вид услуга |
| `service_ftl` | Full Truck Load (FTL) | Пълен камион (FTL) |
| `service_ltl` | Partial Load (LTL) | Частичен товар (LTL) |
| `label_origin_country` | From (country) | Държава на тръгване |
| `placeholder_origin_country` | Select country | Изберете държава |
| `label_origin` | From (city) | Град на тръгване |
| `placeholder_origin` | Select origin city | Изберете град на тръгване |
| `label_destination_country` | To (country) | Държава на дестинация |
| `placeholder_dest_country` | Select country | Изберете държава |
| `label_destination` | To (city) | Град на дестинация |
| `placeholder_dest` | Select destination | Изберете дестинация |
| `label_pallets` | Number of pallets | Брой палети |
| `placeholder_pallets` | e.g. 5 | напр. 5 |
| `label_weight_ltl` | Total weight (kg) | Общо тегло (кг) |
| `label_pallet_type` | Pallet type | Вид палет |
| `opt_eur_pallet` | EUR pallet (120×80 cm) | ЕУР палет (120×80 см) |
| `opt_ind_pallet` | Industrial (120×100 cm) | Индустриален (120×100 см) |
| `label_non_pallet` | Cargo is not on pallets | Товарът не е на палети |
| `label_cargo_length` | Cargo length (cm) | Дължина на товара (см) |
| `label_cargo_width` | Cargo width (cm) | Ширина на товара (см) |
| `placeholder_dimension` | e.g. 120 | напр. 120 |
| `label_weight_ftl` | Cargo weight (kg) | Тегло на товара (кг) |
| `label_truck_type` | Truck type | Тип камион |
| `opt_curtainsider` | Standard curtainsider | Стандартна тентова |
| `opt_refrigerated` | Refrigerated | Хладилна |
| `opt_flatbed` | Flatbed | Платформа |
| `label_load_date` | Desired load date | Желана дата на товарене |
| `label_flexibility` | Date flexibility | Гъвкавост на датата |
| `opt_flexible` | Flexible | Гъвкава |
| `opt_fixed` | Fixed date | Фиксирана дата |
| `toggle_optional` | + Optional details | + Допълнителни подробности |
| `estimate_label` | Estimated price | Приблизителна цена |
| `estimate_secondary` | approx. | прибл. |
| `fill_fields` | Fill in details above to see estimate | Попълнете данните по-горе, за да видите оценката |
| `no_rate` | Contact us for a custom quote | Свържете се с нас за индивидуална оферта |
| `api_error` | Unable to calculate — please contact us | Не може да се изчисли — моля свържете се с нас |
| `disclaimer` | Indicative estimate only. Final price subject to confirmation. | Само приблизителна оценка. Крайната цена подлежи на потвърждение. |
| `btn_get_quote` | Request Formal Quote | Поискайте официална оферта |
| `quote_section_title` | Request a Quote | Заявете оферта |
| `label_name` | Name | Имe |
| `placeholder_name` | Your full name | Вашето пълно име |
| `label_email` | Email | Имейл |
| `placeholder_email` | your@email.com | вашия@имейл.com |
| `label_phone` | Phone | Телефон |
| `contact_hint` | Please provide at least an email or phone number. | Моля въведете поне имейл или телефон. |
| `placeholder_phone` | +359 … | +359 … |
| `label_notes` | Additional notes | Допълнителни бележки |
| `placeholder_notes` | Cargo specifics, special requirements… | Специфики на товара, специални изисквания… |
| `btn_submit` | Submit Quote Request | Изпратете заявка за оферта |
| `submit_success` | Thank you! We will contact you shortly. | Благодарим! Ще се свържем с вас скоро. |
| `submit_error` | Something went wrong. Please try again or contact us directly. | Нещо се обърка. Моля опитайте отново или се свържете с нас директно. |
| `nav_calculator` | Get Quote | Цена |

---

## 10. Backend API Contracts

Two new endpoints added to `backend/app.py` alongside the existing `/api/contact`.

### Architecture

```
Frontend (vanilla JS)
    |
    |-- POST /api/calculate  — stateless instant estimate, no persistence
    |-- POST /api/quote      — saves to JSON+CSV, sends emails
    |-- POST /api/contact    — existing, unchanged
    |
Flask app (app.py)
    |
    |-- PricingEngine (new: backend/pricing_engine.py)
    |       |-- loads prices.json at startup
    |       |-- derives route_type from origin_country / destination_country
    |       |-- domestic zone-matrix lookup
    |       |-- international country-level lookup
    |       |-- LTL calculation (pallet mode and non-pallet area mode)
    |       |-- FTL calculation
    |       |-- surcharge application
    |       |-- km-based fallback for unknown domestic routes
    |
    |-- prices.json       (server-side only, never served to client)
    |-- submissions/
            |-- quotes.json
            |-- quotes.csv
```

---

### 10.1 POST /api/calculate

**Request**

```json
{
  "service_type":      "ltl",
  "origin_country":    "BG",
  "origin_city":       "Targovishte",
  "destination_country": "BG",
  "destination":       "Sofia",
  "num_pallets":       4,
  "total_weight_kg":   1200,
  "pallet_type":       "eur",
  "non_pallet_cargo":  false,
  "cargo_length_cm":   null,
  "cargo_width_cm":    null,
  "cargo_weight_kg":   null,
  "truck_type":        null,
  "load_date":         "2026-03-20",
  "date_flexibility":  "flexible",
  "language":          "en"
}
```

`route_type` is **not sent by the client** — the server derives it: `domestic` when `origin_country == destination_country == "BG"`, otherwise `international`.

**Field rules**

| Field | Required | Type / Enum |
|---|---|---|
| `service_type` | Yes | `"ftl"` or `"ltl"` |
| `origin_country` | Yes | ISO 3166-1 alpha-2 string, e.g. `"BG"`, `"RO"`, `"GR"` |
| `origin_city` | Yes | string, max 100 chars |
| `destination_country` | Yes | ISO 3166-1 alpha-2 string |
| `destination` | Yes | city name string, max 100 chars |
| `num_pallets` | Yes if LTL and `non_pallet_cargo` is false | integer 1–33 |
| `total_weight_kg` | Yes if LTL | number > 0 |
| `pallet_type` | No | `"eur"` (default) or `"industrial"` |
| `non_pallet_cargo` | No | boolean, default `false` |
| `cargo_length_cm` | Yes if `non_pallet_cargo` is true | integer > 0 |
| `cargo_width_cm` | Yes if `non_pallet_cargo` is true | integer > 0 |
| `cargo_weight_kg` | Yes if FTL | number > 0 |
| `truck_type` | No | `"standard"` (default), `"refrigerated"`, `"flatbed"` |
| `load_date` | No | ISO date `YYYY-MM-DD` |
| `date_flexibility` | No | `"flexible"`, `"fixed"` |
| `language` | No | `"en"` (default), `"bg"` |

**Responses**

Price found (200):
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

No rate available (200):
```json
{
  "success": true,
  "no_rate": true,
  "message": "Contact us for a custom quote",
  "message_bg": "Свържете се с нас за индивидуална оферта"
}
```

Validation error (400):
```json
{
  "success": false,
  "error": "num_pallets is required for LTL service"
}
```

Rate limit exceeded (429):
```json
{
  "success": false,
  "error": "Too many requests. Please try again later.",
  "error_bg": "Твърде много запитвания. Моля, опитайте отново по-късно."
}
```

---

### 10.2 POST /api/quote

All fields from `/api/calculate` plus:

```json
{
  "name":            "Ivan Petrov",
  "email":           "ivan@example.com",
  "phone":           "+359 88 123 4567",
  "notes":           "Fragile machinery parts, no stacking.",
  "shown_min_price": 420,
  "shown_max_price": 520,
  "language":        "bg"
}
```

Additional field rules:
- `name`: required, 2–100 chars
- `email`: conditional — required if `phone` not provided; valid email format
- `phone`: conditional — required if `email` not provided; max 50 chars
- At least one of `email` or `phone` must be present
- `notes`: optional, max 500 chars
- `shown_min_price` / `shown_max_price`: optional numbers — logged for context, not re-validated

Success response (200):
```json
{
  "success": true,
  "message": "Quote request submitted successfully",
  "message_bg": "Заявката за оферта е изпратена успешно"
}
```

Error responses follow the same shape as `/api/contact` and `/api/calculate`.

**Rate limiting:** Same in-memory pattern as `/api/contact` (`check_rate_limit()`), shared tracker.

**Persistence:** Saves to `submissions/quotes.json` and `submissions/quotes.csv` using the same helper pattern as `save_to_json()` and `save_to_csv()` in `app.py`.

**Emails:** Two new templates in `email_templates.py`:
- `get_quote_company_notification_template(data, language)` — includes full cargo details + estimate shown
- `get_quote_customer_confirmation_template(data, language)` — acknowledges the quote request

The company email body must include a formatted cargo summary so the team can act without opening the CSV.

---

## 11. Pricing Model

All pricing logic lives in `backend/pricing_engine.py`. Prices are loaded from `backend/prices.json` at startup. Pricing data is never included in any API response.

### 11.1 LTL Calculation

**Pallet mode** (`non_pallet_cargo == false`):

```
weight_based  = (total_weight_kg / 100) * ltl_per_100kg_bgn
pallet_based  = num_pallets * ltl_per_pallet_bgn
base_price    = max(weight_based, pallet_based)          # charge the higher
base_price    = max(base_price, ltl_min_charge_bgn)      # minimum charge (international only)
```

**Non-pallet mode** (`non_pallet_cargo == true`):

```
EUR_PALLET_AREA_CM2 = 9600                               # 120 × 80 cm, fixed constant
cargo_area          = cargo_length_cm * cargo_width_cm
equiv_pallets       = ceil(cargo_area / EUR_PALLET_AREA_CM2)

weight_based  = (total_weight_kg / 100) * ltl_per_100kg_bgn
pallet_based  = equiv_pallets * ltl_per_pallet_bgn
base_price    = max(weight_based, pallet_based)          # charge the higher
base_price    = max(base_price, ltl_min_charge_bgn)      # minimum charge (international only)
```

**Surcharges and range (both modes):**

```
with_surcharges = base_price * (1 + fuel_pct / 100)
# if date_flexibility == "fixed": multiply by (1 + express_pct / 100)

min_price = round(with_surcharges * (1 - price_range_pct / 100))
max_price = round(with_surcharges * (1 + price_range_pct / 100))
```

### 11.2 FTL Calculation

```
base_price    = ftl_base_bgn * truck_type_multipliers[truck_type]

with_surcharges = base_price * (1 + fuel_pct / 100)
# if date_flexibility == "fixed": multiply by (1 + express_pct / 100)

min_price = round(with_surcharges * (1 - price_range_pct / 100))
max_price = round(with_surcharges * (1 + price_range_pct / 100))
```

### 11.3 Domestic Fallback (unknown city pair)

When `origin_city|destination` key is absent from `domestic.routes`:
1. Look up both cities in `known_city_coords_km_from_sofia`.
2. Estimate distance: `abs(origin_km - destination_km)`.
3. Apply `fallback_per_km` rates.
4. If either city is not in the lookup table: return `no_rate: true`.

### 11.4 Truck Type Multipliers

| Type | Multiplier |
|---|---|
| `standard` | 1.00 |
| `refrigerated` | 1.35 |
| `flatbed` | 1.20 |

### 11.5 Default Surcharges (configurable in prices.json)

| Surcharge | Default | Trigger |
|---|---|---|
| Fuel | 15% | Always applied |
| Express | 25% | `date_flexibility == "fixed"` |
| Dangerous goods | 30% | v2 — not in v1 inputs |
| Price range spread | ±12% | Applied to produce min/max |

---

## 12. Data Schema — prices.json

Location: `backend/prices.json`. Committed to the repository (no secrets). Owner edits rates here — no code change required.

```json
{
  "_comment": "Rocket Logistic pricing config. All prices in BGN.",
  "_version": "1.0",

  "settings": {
    "currency": "BGN",
    "price_range_pct": 12
  },

  "surcharges": {
    "fuel_pct": 15,
    "express_pct": 25,
    "dangerous_goods_pct": 30
  },

  "truck_type_multipliers": {
    "standard":     1.0,
    "refrigerated": 1.35,
    "flatbed":      1.20
  },

  "domestic": {
    "routes": {
      "targovishte|sofia":  { "ftl_base_bgn": 850,  "ltl_per_pallet_bgn": 42, "ltl_per_100kg_bgn": 14 },
      "sofia|targovishte":  { "ftl_base_bgn": 850,  "ltl_per_pallet_bgn": 42, "ltl_per_100kg_bgn": 14 },
      "targovishte|burgas": { "ftl_base_bgn": 600,  "ltl_per_pallet_bgn": 30, "ltl_per_100kg_bgn": 10 },
      "burgas|targovishte": { "ftl_base_bgn": 600,  "ltl_per_pallet_bgn": 30, "ltl_per_100kg_bgn": 10 },
      "targovishte|varna":  { "ftl_base_bgn": 420,  "ltl_per_pallet_bgn": 22, "ltl_per_100kg_bgn": 8  },
      "varna|targovishte":  { "ftl_base_bgn": 420,  "ltl_per_pallet_bgn": 22, "ltl_per_100kg_bgn": 8  },
      "burgas|sofia":       { "ftl_base_bgn": 1100, "ltl_per_pallet_bgn": 55, "ltl_per_100kg_bgn": 18 },
      "sofia|burgas":       { "ftl_base_bgn": 1100, "ltl_per_pallet_bgn": 55, "ltl_per_100kg_bgn": 18 },
      "varna|sofia":        { "ftl_base_bgn": 1050, "ltl_per_pallet_bgn": 52, "ltl_per_100kg_bgn": 17 },
      "sofia|varna":        { "ftl_base_bgn": 1050, "ltl_per_pallet_bgn": 52, "ltl_per_100kg_bgn": 17 }
    },
    "fallback_per_km": {
      "ftl_bgn_per_km":              2.80,
      "ltl_bgn_per_pallet_per_km":   0.14,
      "ltl_bgn_per_100kg_per_km":    0.045
    },
    "known_city_coords_km_from_sofia": {
      "sofia": 0, "plovdiv": 150, "burgas": 390, "varna": 440,
      "targovishte": 300, "ruse": 300, "stara zagora": 220, "pleven": 170
    }
  },

  "international": {
    "countries": {
      "RO": {
        "ftl_base_bgn": 2600, "ltl_per_pallet_bgn": 120,
        "ltl_per_100kg_bgn": 38, "ltl_min_charge_bgn": 180
      },
      "GR": {
        "ftl_base_bgn": 2200, "ltl_per_pallet_bgn": 100,
        "ltl_per_100kg_bgn": 32, "ltl_min_charge_bgn": 150
      },
      "EU": {
        "ftl_base_bgn": 4500, "ltl_per_pallet_bgn": 200,
        "ltl_per_100kg_bgn": 65, "ltl_min_charge_bgn": 300
      }
    }
  }
}
```

**How the owner adds partial data:**
- Known routes: add a `"origin|destination"` key with rates.
- Unknown city distances: add the city to `known_city_coords_km_from_sofia` and the fallback rates apply automatically.
- New international countries: copy an existing entry under `international.countries` and update the rates.
- If a route/city is absent and no fallback distance is known: the engine returns `no_rate: true` — the frontend shows "contact us".

---

## 13. Data Persistence — quotes.json / quotes.csv

Fields saved per quote submission (follows existing `contacts.json`/`contacts.csv` pattern):

```
timestamp, name, email, phone, service_type, route_type,
origin_country, origin_city, destination_country, destination,
num_pallets, total_weight_kg, pallet_type,
non_pallet_cargo, cargo_length_cm, cargo_width_cm,
cargo_weight_kg, truck_type, load_date, date_flexibility,
shown_min_price, shown_max_price, notes, language, ip
```

`route_type` is the server-derived value (`"domestic"` or `"international"`) saved for reference.

Files: `submissions/quotes.json` and `submissions/quotes.csv` (same directory as contact form submissions).

---

## 14. Config Extensions

Add to `Config` class in `backend/config.py`, following existing `BASE_DIR` pattern:

```python
# Pricing
PRICES_FILE = os.getenv('PRICES_FILE', os.path.join(BASE_DIR, 'prices.json'))
PRICES_MAX_REQUESTS_PER_HOUR = int(os.getenv('PRICES_MAX_REQUESTS_PER_HOUR', 60))

# Quote submissions
QUOTES_JSON = os.path.join(SUBMISSIONS_DIR, 'quotes.json')
QUOTES_CSV  = os.path.join(SUBMISSIONS_DIR, 'quotes.csv')
```

`Config.validate()` must be extended to verify `PRICES_FILE` exists at startup:

```python
if not os.path.exists(cls.PRICES_FILE):
    errors.append(f"PRICES_FILE not found: {cls.PRICES_FILE}")
```

`PRICES_MAX_REQUESTS_PER_HOUR` is intentionally higher than `MAX_SUBMISSIONS_PER_HOUR` (5) because `/api/calculate` is a read-only endpoint called on every input change.

---

## 15. CSS Components & Page Integration

### Page placement

Insert between `.about` and `.contact` in both `index.html` and `bg/index.html`:

```
hero       (#hero)
services   (#services)
about      (#about)
           ← INSERT .price-calculator here (#calculate)
contact    (#contact)
footer
```

### Navigation link

Add between "About" and "Contact" in `.nav__list` in both pages:

```html
<li class="nav__item">
    <a href="#calculate" class="nav__link" data-en="Get Quote" data-bg="Цена">Get Quote</a>
</li>
```

Nav order: Services | About | **Get Quote** | Contact

### Section HTML structure

```html
<section class="price-calculator" id="calculate">
    <div class="container">
        <h2 class="section__title" data-en="Get a Price Estimate" data-bg="Получете ценова оферта">
            Get a Price Estimate
        </h2>
        <div class="price-calculator__body">
            <form class="price-calculator__form" id="calc-form" novalidate>
                <!-- Groups 1–3 + optional + quote extension -->
            </form>
            <div class="price-calculator__result">
                <!-- .estimate-card -->
            </div>
        </div>
    </div>
</section>
```

### New CSS classes (append to css/style.css under "/* Price Calculator Section */")

All new CSS is appended to the existing `css/style.css` under a new section comment. No new stylesheet file.

| Class | Purpose |
|---|---|
| `.price-calculator` | Section wrapper (matches `.services`, `.about` pattern) |
| `.price-calculator__body` | Two-column grid (form + result) |
| `.price-calculator__form` | The `<form>` element |
| `.price-calculator__result` | Estimate card column |
| `.service-tabs` | Wrapper for FTL/LTL tab toggles |
| `.service-tabs__options` | Flex container, border-grouped |
| `.service-tabs__option` | `<label>` wrapping hidden radio + text |
| `.service-tabs__option--active` | JS-toggled selected state |
| `.form-row` | Two-column field grid within the form |
| `.estimate-card` | White card, `border-top: 4px solid var(--color-brand-green)`, sticky on desktop |
| `.estimate-card__price` | Large bold price figure |
| `.estimate-card__currency` | Currency label |
| `.estimate-card__breakdown` | Surcharge line-item list |
| `.estimate-card__note` | Disclaimer text |
| `.estimate-card--loading` | State modifier: shows spinner, hides price |
| `.estimate-card--empty` | Initial state modifier |
| `.calc-spinner` | Spinner wrapper inside estimate card |
| `.calc-spinner__ring` | CSS-only animated ring (no external dependency) |

**Reuse without changes:**
- `.form-group`, `.form-group label`, `.form-group input`, `.form-group select`, `.form-error` — identical to contact form
- `.btn.btn--primary.btn--full` — the sole CTA button style
- `.section__title`, `.section__subtitle` — heading pattern
- `.container` — max-width and padding

### Design token usage

All new classes use only existing CSS custom properties from `:root`. Key mappings:
- Active tab / selected state: `--color-primary` (#1E3A5F) background, white text
- Estimate card top border accent: `--color-brand-green` (#4EA831)
- CTA button: `.btn--primary` uses `--color-accent` (#FF6B35) — no change
- Error states: `--color-error` (#e74c3c)
- Card shadow: `box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08)` — matches `.service-card`
- Border radius: `4px` for inputs/buttons, `8px` for cards
- Transitions: always `var(--transition)` (0.3s ease)

---

## 16. Responsive Layout

| Breakpoint | Layout |
|---|---|
| > 1024px (desktop) | Two-column grid: form left, estimate card right (sticky) |
| ≤ 1024px (tablet) | Two-column still, gap reduced from `var(--space-2xl)` to `var(--space-lg)` |
| ≤ 768px (mobile) | Single column; estimate card loses sticky, moves below form |
| ≤ 480px (small mobile) | All `.form-row` become single column; estimate card padding reduced |

Service type tabs remain side-by-side at all sizes (short labels, no wrapping required).

Optional fields (load date, date flexibility) are collapsed by default at all sizes behind a toggle link to reduce initial form length.

---

## 17. Accessibility

- All inputs have associated `<label>` elements (not just placeholders).
- All inputs have `aria-label` or `aria-labelledby` in both EN and BG.
- Estimate panel uses `aria-live="polite"` for screen reader announcements.
- Quote CTA button uses `aria-expanded` to signal open/closed state of the quote panel.
- `aria-invalid="true"` is set on fields with validation errors.
- Color is never the sole error indicator (text + border + icon together).
- Tab order follows visual reading order (top to bottom, left to right).
- All interactive elements: minimum 44×44px touch target (WCAG 2.5.5).
- Service tab `<label>` elements use `.service-tabs__option:focus-within { outline: 2px solid var(--color-accent); }`.
- `.calc-spinner__ring` animation wrapped in `@media (prefers-reduced-motion: reduce)`.
- Font weights: 400, 600, 700 only (matching existing site).
- WCAG AA contrast confirmed for all new text/background combinations using existing design tokens.

---

## 18. Implementation Checklist

### Backend

- [ ] Create `backend/prices.json` using schema in Section 12 (fill real rates with owner)
- [ ] Create `backend/pricing_engine.py` implementing logic in Section 11
- [ ] Add `PRICES_FILE`, `PRICES_MAX_REQUESTS_PER_HOUR`, `QUOTES_JSON`, `QUOTES_CSV` to `backend/config.py`
- [ ] Extend `Config.validate()` to check `PRICES_FILE` exists
- [ ] Add `POST /api/calculate` handler to `backend/app.py`
- [ ] Add `POST /api/quote` handler to `backend/app.py`
- [ ] Add `save_quote_to_json()` and `save_quote_to_csv()` helpers (or generalize existing helpers)
- [ ] Add `get_quote_company_notification_template()` and `get_quote_customer_confirmation_template()` to `backend/email_templates.py`

### Backend tests

- [ ] Unit test `PricingEngine`: derives `domestic` when both countries are `BG`
- [ ] Unit test `PricingEngine`: derives `international` when countries differ
- [ ] Unit test `PricingEngine`: known domestic route LTL (pallet mode)
- [ ] Unit test `PricingEngine`: known domestic route LTL (non-pallet mode — equiv pallets from dimensions)
- [ ] Unit test `PricingEngine`: known domestic route FTL
- [ ] Unit test `PricingEngine`: domestic fallback (unlisted city pair with known km)
- [ ] Unit test `PricingEngine`: domestic no-rate (unknown city)
- [ ] Unit test `PricingEngine`: international LTL (RO, GR, EU)
- [ ] Unit test `PricingEngine`: international FTL
- [ ] Unit test `PricingEngine`: express surcharge applied when `date_flexibility == "fixed"`
- [ ] Integration test: `POST /api/calculate` returns 200 + price range for valid input
- [ ] Integration test: `POST /api/calculate` returns 200 + price range for non-pallet LTL input
- [ ] Integration test: `POST /api/calculate` returns `no_rate: true` for unknown route
- [ ] Integration test: `POST /api/quote` returns 200, saves record, triggers email
- [ ] Integration test: `POST /api/quote` rejects submission with neither email nor phone

### Frontend

- [ ] Add `#calculate` section HTML to `index.html` (between `#about` and `#contact`)
- [ ] Add `#calculate` section HTML to `bg/index.html` (same position)
- [ ] Add nav link "Get Quote" / "Цена" to both pages
- [ ] Implement vanilla JS calculator logic (debounced `POST /api/calculate` on input change)
- [ ] Implement country dropdowns: filter city options based on selected country; derive route type client-side for UI hints
- [ ] Implement `non_pallet_cargo` checkbox: hide `pallet_type`, show `cargo_length_cm` / `cargo_width_cm` on check
- [ ] Implement estimate panel state transitions (incomplete → loading → result/no-rate/error)
- [ ] Implement inline quote form expansion on CTA click
- [ ] Implement quote form submission (`POST /api/quote`) with inline success/error handling
- [ ] Implement bilingual string switching (inherit from `html[lang]`)
- [ ] Implement per-field inline validation with EN/BG error messages
- [ ] Implement email-or-phone cross-field validation on quote submit

### CSS

- [ ] Append new "Price Calculator Section" block to `css/style.css`
- [ ] Implement all classes listed in Section 15
- [ ] Verify responsive breakpoints at 1024px, 768px, 480px
- [ ] Verify `prefers-reduced-motion` wraps spinner animation
- [ ] Cross-check `.calc-steps` classes against final UX decision (single-page = omit step indicators)

### Content / Data

- [ ] Confirm all rates in `prices.json` with company owner before go-live
- [ ] Confirm EUR exchange rate display (fixed rate or remove secondary currency)
- [ ] Review and finalize BG translations with native speaker

---

*Source documents:*
- `planning/requirements.md` — product requirements and user stories
- `planning/ux-wireframe.md` — UX flow, wireframes, bilingual labels, validation UX
- `planning/backend-spec.md` — pricing model, API contracts, data schema, config
- `planning/style-plan.md` — CSS components, design tokens, page integration, responsive breakpoints
