# Price Calculator Requirements
# Rocket Logistic — Transport Price Calculator

**Document version:** 1.0
**Date:** 2026-03-06
**Author:** product-manager

---

## 1. Core Objective

Enable website visitors to instantly see a price estimate for their shipment and optionally submit a formal quote request — without any page reload or form submission required for the estimate.

---

## 2. User Stories

### Instant Estimate (no submission)

- **US-01** — As a visitor, I want to select my service type (FTL or LTL) so the calculator shows relevant input fields.
- **US-02** — As a visitor, I want to select origin and destination (domestic BG routes or international: RO, GR, EU) so the estimate reflects the correct route.
- **US-03** — As a visitor doing LTL, I want to enter number of pallets and total weight so I get a per-pallet or per-kg rate estimate.
- **US-04** — As a visitor doing FTL, I want to select truck type and enter cargo weight so I get a full-truck price estimate.
- **US-05** — As a visitor, I want to see the price estimate instantly update as I change inputs, without clicking a submit button.
- **US-06** — As a Bulgarian-speaking visitor, I want all labels, placeholders, and messages to appear in Bulgarian.
- **US-07** — As an English-speaking visitor, I want all labels, placeholders, and messages to appear in English.

### Formal Quote Request (with submission)

- **US-08** — As a visitor, after seeing the estimate, I want to submit a formal quote request with my contact details so the company can follow up.
- **US-09** — As a visitor, I want to receive a confirmation email acknowledging my quote request.
- **US-10** — As the company, I want to receive an email with the full shipment details and contact info when a quote is submitted.

---

## 3. Services Covered

| Service | Scope |
|---|---|
| FTL — Full Truck Load | Domestic BG + International (RO, GR, EU) |
| LTL — Partial Load / Pallets | Domestic BG + International (RO, GR, EU) |

**Domestic BG routes** (known fixed routes):
- Burgas — Sofia
- Varna — Sofia
- Targovishte — Sofia
- Targovishte — Burgas
- Targovishte — Varna
- (General BG domestic, km-based fallback)

**International destinations:**
- Romania (RO)
- Greece (GR)
- General EU (rest of Europe, rate-per-km or zone pricing)

---

## 4. Required Input Fields

### Step 1 — Service Selection
| Field | Type | Required | Values |
|---|---|---|---|
| service_type | radio / tab | Yes | `ftl`, `ltl` |
| route_type | radio / tab | Yes | `domestic`, `international` |

### Step 2 — Route Details
| Field | Type | Required | Values |
|---|---|---|---|
| origin_city | select / text | Yes | Dropdown for known cities or free text |
| destination | select | Yes | For domestic: city list; for international: country (RO, GR, EU) |

### Step 3 — Cargo Details (LTL)
| Field | Type | Required | Notes |
|---|---|---|---|
| num_pallets | number input | Yes | Min 1, max 33 |
| total_weight_kg | number input | Yes | Gross weight in kg |
| pallet_type | select | No | EUR pallet (120x80), Industrial (120x100) |

### Step 3 — Cargo Details (FTL)
| Field | Type | Required | Notes |
|---|---|---|---|
| cargo_weight_kg | number input | Yes | Total cargo weight in kg |
| truck_type | select | No | Standard curtainsider, Refrigerated, Flatbed |

### Optional for both
| Field | Type | Required | Notes |
|---|---|---|---|
| load_date | date picker | No | Desired pickup date |
| date_flexibility | radio | No | `flexible`, `fixed` |

### Quote Request Extension (shown on CTA click)
| Field | Type | Required | Notes |
|---|---|---|---|
| name | text | Yes | 2–100 chars |
| email | email | Yes | Valid email |
| phone | tel | No | Optional |
| notes | textarea | No | Max 500 chars, additional cargo details |
| language | hidden | Yes | Auto-detected from page language |

---

## 5. Output Specification

### Instant Estimate Panel
- Displays a **price range** (e.g., "1,200 – 1,500 BGN") or a **base price** with a disclaimer.
- Updates in real time on any input change (debounced ~300ms).
- Shows price in **BGN** (Bulgarian Lev) as primary currency; optionally EUR as secondary.
- Includes a short disclaimer: "This is an indicative estimate. Final price depends on exact route conditions and cargo specifics."
- Bilingual disclaimer (EN / BG).

### Estimate States
| State | Display |
|---|---|
| Incomplete inputs | "Fill in details above to see estimate" |
| Valid inputs, price found | Price range in BGN (+ EUR) |
| Valid inputs, no rate available | "Contact us for a custom quote" |
| Error (API failure) | "Unable to calculate — please contact us" |

### Quote Submission Response
- Success: Confirmation message inline (no page reload), same pattern as existing contact form.
- Error: Inline error message, bilingual.

---

## 6. Bilingual Requirements

The calculator must support EN and BG languages matching the existing site pattern.

**Language detection:** Inherit from page language (`<html lang="en">` vs `<html lang="bg">`).

**All user-facing strings must have both EN and BG versions:**

| Key | EN | BG |
|---|---|---|
| calc_title | "Get a Price Estimate" | "Получете ценова оферта" |
| service_ftl | "Full Truck Load (FTL)" | "Пълен камион (FTL)" |
| service_ltl | "Partial Load (LTL)" | "Частичен товар (LTL)" |
| route_domestic | "Domestic Bulgaria" | "Вътрешен транспорт" |
| route_international | "International" | "Международен" |
| label_origin | "From" | "От" |
| label_destination | "To" | "До" |
| label_pallets | "Number of pallets" | "Брой палети" |
| label_weight | "Total weight (kg)" | "Общо тегло (кг)" |
| label_truck_type | "Truck type" | "Тип камион" |
| label_load_date | "Desired load date" | "Желана дата на товарене" |
| btn_get_quote | "Request Formal Quote" | "Поискайте официална оферта" |
| btn_calculate | "Calculate" | "Изчисли" |
| estimate_label | "Estimated price" | "Приблизителна цена" |
| disclaimer | "Indicative estimate only. Final price subject to confirmation." | "Само приблизителна оценка. Крайната цена подлежи на потвърждение." |
| no_rate | "Contact us for a custom quote" | "Свържете се с нас за индивидуална оферта" |
| fill_fields | "Fill in details above to see estimate" | "Попълнете данните по-горе, за да видите оценката" |

---

## 7. Backend API Requirement

A new endpoint is needed alongside the existing `/api/contact`:

### `POST /api/calculate`
- Accepts: service type, route, cargo details
- Returns: `{ "min_price": number, "max_price": number, "currency": "BGN", "disclaimer": string }` or `{ "no_rate": true }`
- Must be stateless; pricing logic stored server-side in config (not exposed to client)
- No auth required (public endpoint)
- Rate limiting: apply same pattern as existing contact form

### `POST /api/quote`
- Extends existing `/api/contact` pattern
- Accepts all contact fields PLUS calculator fields (service_type, route, cargo details, estimate shown to user)
- Sends email to company with full shipment + contact details
- Sends confirmation email to customer
- Saves to JSON + CSV (same pattern as existing contact form)

---

## 8. Integration Constraints

- Must fit within existing CSS design system (`css/style.css`) — Montserrat / Open Sans fonts, existing color palette and BEM naming conventions
- Calculator section to be added as a new `<section>` in both `index.html` and `bg/index.html`
- No external JS framework dependencies (site is vanilla JS)
- Must be mobile-responsive, consistent with existing responsive breakpoints
- Should be accessible: ARIA labels on all inputs, keyboard-navigable

---

## 9. Non-Goals (out of scope for v1)

- Real-time GPS route distance calculation
- User accounts or saved quotes
- PDF quote generation
- Payment processing
- Live carrier rate integration

---

## 10. Success Criteria

1. Visitor can get a price estimate with zero form submission
2. Estimate updates within 300ms of changing any input
3. Quote request sends email to company and confirmation to visitor
4. All UI is fully bilingual (EN/BG)
5. Calculator matches visual design of existing site
6. Backend `/api/calculate` returns correct price range for all supported routes and service types
7. No pricing data is exposed in frontend source code
