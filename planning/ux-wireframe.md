# UX Design: Rocket Logistic Price Calculator
**Document version:** 1.0
**Date:** 2026-03-06
**Author:** ux-designer

---

## 1. User Flow

### Flow A — Instant Price Estimate (no submission)

```
1. User arrives at #calculator section (anchored from hero CTA or nav)
2. Step 1 — Service & Route Selection
   ├─ Select service type: [FTL] [LTL]  (tab-style toggle, FTL default)
   └─ Select route type:   [Domestic BG] [International]  (tab-style toggle)
3. Step 2 — Route Details
   ├─ Origin city: dropdown (known cities) or free text
   └─ Destination: dropdown filtered by route_type
        • Domestic: Sofia / Burgas / Varna / Targovishte
        • International: Romania / Greece / General EU
4. Step 3 — Cargo Details  (fields differ by service type)
   LTL branch:
   ├─ Number of pallets (number, required)
   ├─ Total weight kg   (number, required)
   └─ Pallet type       (select, optional)
   FTL branch:
   ├─ Cargo weight kg   (number, required)
   └─ Truck type        (select, optional)
   Both (optional):
   ├─ Desired load date (date picker)
   └─ Date flexibility  (radio: flexible / fixed)
5. Estimate Panel updates in real time (debounced 300 ms)
   ├─ While incomplete → prompt message
   ├─ Price found      → range in BGN (+EUR secondary)
   ├─ No rate          → "Contact us" message
   └─ API error        → error message
6. User reads estimate — flow complete (no submission required)
```

### Flow B — Formal Quote Request (optional extension)

```
Precondition: estimate is displayed (price found state)
1. User clicks "Request Formal Quote" CTA button
2. Quote extension panel expands inline below estimate (no redirect)
3. Contact fields revealed:
   ├─ Name   (text, required)
   ├─ Email  (email, required)
   ├─ Phone  (tel, optional)
   └─ Notes  (textarea, optional)
4. All calculator fields from Flow A are preserved (read-only summary shown)
5. User clicks "Submit Quote Request"
6. Inline validation runs; errors shown per-field
7. On success: confirmation message replaces quote form (no reload)
8. Company receives email with full shipment + contact details
9. Customer receives confirmation email
```

---

## 2. Multi-step vs Single-page Decision

**Recommendation: Single-page progressive disclosure**

All fields appear on one scrollable page, grouped into logical visual sections. Steps are not separate pages or wizard screens — instead, earlier selections conditionally reveal later fields in the same view.

**Rationale:**

- The total field count is low (6–8 required fields max). A full wizard adds navigation overhead with no benefit at this scale.
- Real-time estimate updates require all inputs to be simultaneously readable by the JS calculation logic. Multi-page wizards complicate this with state management.
- Progressive disclosure (showing cargo fields only after service/route is selected) provides the clarity of a wizard without the navigation cost.
- Single-page layout performs better on mobile (no step transitions, no back button confusion).
- The quote extension panel expands inline — this is only possible in a single-page model.
- Consistent with the existing site pattern: the contact section is a single scrollable form, not a wizard.

---

## 3. Form Structure — Field Order and Grouping

### Group 1 — Service & Route (always visible)

| Order | Field         | Type          | Required | Reveals            |
|-------|---------------|---------------|----------|--------------------|
| 1     | service_type  | Tab toggle    | Yes      | Cargo group below  |
| 2     | route_type    | Tab toggle    | Yes      | Destination options|

### Group 2 — Route Details (revealed after Group 1)

| Order | Field        | Type             | Required | Notes                                      |
|-------|--------------|------------------|----------|--------------------------------------------|
| 3     | origin_city  | Select + fallback| Yes      | Known cities pre-populated                 |
| 4     | destination  | Select           | Yes      | Options filtered by route_type selection   |

### Group 3 — Cargo Details (revealed after Group 2; fields differ by service_type)

**LTL path:**

| Order | Field           | Type   | Required | Constraints        |
|-------|-----------------|--------|----------|--------------------|
| 5a    | num_pallets     | Number | Yes      | Min 1, max 33      |
| 5b    | total_weight_kg | Number | Yes      | Positive integer   |
| 5c    | pallet_type     | Select | No       | EUR / Industrial   |

**FTL path:**

| Order | Field           | Type   | Required | Constraints        |
|-------|-----------------|--------|----------|--------------------|
| 5a    | cargo_weight_kg | Number | Yes      | Positive integer   |
| 5b    | truck_type      | Select | No       | Curtainsider / Refrigerated / Flatbed |

**Both paths (optional, collapsed by default, expandable):**

| Order | Field            | Type        | Required |
|-------|------------------|-------------|----------|
| 6a    | load_date        | Date picker | No       |
| 6b    | date_flexibility | Radio       | No       |

### Group 4 — Estimate Panel (always visible once Group 1 complete)

Live-updating result area. See Section 6.

### Group 5 — Quote Extension (hidden until CTA click)

| Order | Field    | Type     | Required | Constraints           |
|-------|----------|----------|----------|-----------------------|
| 7     | name     | Text     | Yes      | 2–100 chars           |
| 8     | email    | Email    | Yes      | Valid email format    |
| 9     | phone    | Tel      | No       | —                     |
| 10    | notes    | Textarea | No       | Max 500 chars         |
| —     | language | Hidden   | Yes      | Auto from html[lang]  |

---

## 4. ASCII Wireframe — Calculator Widget

### Desktop (>= 768px)

```
+------------------------------------------------------------------+
|  CALCULATOR SECTION                                               |
|  ---------------------------------------------------------------- |
|                                                                    |
|  Get a Price Estimate / Получете ценова оферта                    |
|                                                                    |
|  ┌─────────────────────────────────────────────────────────────┐  |
|  │  SERVICE TYPE                                               │  |
|  │  ┌──────────────────────┐  ┌──────────────────────┐        │  |
|  │  │  [●] Full Truck (FTL)│  │  [ ] Partial Load    │        │  |
|  │  │      Пълен камион    │  │      (LTL)           │        │  |
|  │  └──────────────────────┘  └──────────────────────┘        │  |
|  │                                                             │  |
|  │  ROUTE TYPE                                                 │  |
|  │  ┌──────────────────────┐  ┌──────────────────────┐        │  |
|  │  │  [●] Domestic BG     │  │  [ ] International   │        │  |
|  │  │      Вътрешен        │  │      Международен    │        │  |
|  │  └──────────────────────┘  └──────────────────────┘        │  |
|  └─────────────────────────────────────────────────────────────┘  |
|                                                                    |
|  ┌──────────────────────────┐  ┌──────────────────────────────┐   |
|  │  FROM / ОТ               │  │  TO / ДО                     │   |
|  │  ┌────────────────────┐  │  │  ┌──────────────────────┐   │   |
|  │  │ Targovishte      v │  │  │  │ Sofia              v │   │   |
|  │  └────────────────────┘  │  │  └──────────────────────┘   │   |
|  └──────────────────────────┘  └──────────────────────────────┘   |
|                                                                    |
|  ┌─────────────────────────────────────────────────────────────┐  |
|  │  CARGO DETAILS  (FTL shown; LTL swaps fields dynamically)  │  |
|  │                                                             │  |
|  │  ┌──────────────────────────┐  ┌────────────────────────┐  │  |
|  │  │  Cargo weight (kg)       │  │  Truck type            │  │  |
|  │  │  Тегло на товара (кг)    │  │  Тип камион            │  │  |
|  │  │  ┌──────────────────┐   │  │  ┌──────────────────┐  │  │  |
|  │  │  │ 0                │   │  │  │ Curtainsider   v │  │  │  |
|  │  │  └──────────────────┘   │  │  └──────────────────┘  │  │  |
|  │  └──────────────────────────┘  └────────────────────────┘  │  |
|  │                                                             │  |
|  │  [+ Optional: Desired load date / Желана дата]              │  |
|  └─────────────────────────────────────────────────────────────┘  |
|                                                                    |
|  ┌─────────────────────────────────────────────────────────────┐  |
|  │  ESTIMATED PRICE / ПРИБЛИЗИТЕЛНА ЦЕНА                       │  |
|  │                                                             │  |
|  │        1,200 – 1,500 BGN  (~615 – 768 EUR)                  │  |
|  │                                                             │  |
|  │  ! Indicative estimate only. Final price subject to         │  |
|  │    confirmation. / Само приблизителна оценка...             │  |
|  │                                                             │  |
|  │  ┌─────────────────────────────────────────────────────┐   │  |
|  │  │         REQUEST FORMAL QUOTE                        │   │  |
|  │  │         ПОИСКАЙТЕ ОФИЦИАЛНА ОФЕРТА                  │   │  |
|  │  └─────────────────────────────────────────────────────┘   │  |
|  └─────────────────────────────────────────────────────────────┘  |
|                                                                    |
|  ┌─────────────────────────────────────────────────────────────┐  |
|  │  QUOTE REQUEST  (expands when CTA is clicked)               │  |
|  │                                                             │  |
|  │  ┌──────────────────────┐  ┌──────────────────────────┐    │  |
|  │  │  Name / Имe          │  │  Email                   │    │  |
|  │  │  ┌────────────────┐  │  │  ┌────────────────────┐  │    │  |
|  │  │  │                │  │  │  │                    │  │    │  |
|  │  │  └────────────────┘  │  │  └────────────────────┘  │    │  |
|  │  └──────────────────────┘  └──────────────────────────┘    │  |
|  │                                                             │  |
|  │  ┌──────────────────────┐                                   │  |
|  │  │  Phone / Телефон     │                                   │  |
|  │  │  ┌────────────────┐  │                                   │  |
|  │  │  │                │  │                                   │  |
|  │  │  └────────────────┘  │                                   │  |
|  │  └──────────────────────┘                                   │  |
|  │                                                             │  |
|  │  Notes / Бележки                                            │  |
|  │  ┌─────────────────────────────────────────────────────┐   │  |
|  │  │                                                     │   │  |
|  │  │  (max 500 chars)                                    │   │  |
|  │  └─────────────────────────────────────────────────────┘   │  |
|  │                                                             │  |
|  │  ┌─────────────────────────────────────────────────────┐   │  |
|  │  │  SUBMIT QUOTE REQUEST / ИЗПРАТЕТЕ ЗАЯВКА            │   │  |
|  │  └─────────────────────────────────────────────────────┘   │  |
|  └─────────────────────────────────────────────────────────────┘  |
+------------------------------------------------------------------+
```

### Mobile (< 768px)

```
+-------------------------------+
|  Get a Price Estimate         |
|  Получете ценова оферта       |
|                               |
|  SERVICE TYPE                 |
|  ┌──────────────────────────┐ |
|  │ [●] Full Truck Load (FTL)│ |
|  └──────────────────────────┘ |
|  ┌──────────────────────────┐ |
|  │ [ ] Partial Load (LTL)   │ |
|  └──────────────────────────┘ |
|                               |
|  ROUTE TYPE                   |
|  ┌──────────────────────────┐ |
|  │ [●] Domestic Bulgaria    │ |
|  └──────────────────────────┘ |
|  ┌──────────────────────────┐ |
|  │ [ ] International        │ |
|  └──────────────────────────┘ |
|                               |
|  FROM / ОТ                    |
|  ┌──────────────────────────┐ |
|  │ Targovishte            v │ |
|  └──────────────────────────┘ |
|                               |
|  TO / ДО                      |
|  ┌──────────────────────────┐ |
|  │ Sofia                  v │ |
|  └──────────────────────────┘ |
|                               |
|  Cargo weight (kg)            |
|  Тегло на товара (кг)         |
|  ┌──────────────────────────┐ |
|  │ 0                        │ |
|  └──────────────────────────┘ |
|                               |
|  Truck type / Тип камион      |
|  ┌──────────────────────────┐ |
|  │ Curtainsider           v │ |
|  └──────────────────────────┘ |
|                               |
|  [+ Load date / optional]     |
|                               |
| ┌────────────────────────────┐|
| │  ESTIMATED PRICE           ││
| │  1,200 – 1,500 BGN         ││
| │  (~615 – 768 EUR)          ││
| │                            ││
| │  ! Indicative estimate...  ││
| └────────────────────────────┘|
|                               |
|  ┌────────────────────────┐   |
|  │  REQUEST FORMAL QUOTE  │   |
|  └────────────────────────┘   |
|                               |
|  [Quote form expands below]   |
+-------------------------------+
```

---

## 5. Bilingual Labels — Complete Reference

| Key                  | EN Label                          | BG Label                                          |
|----------------------|-----------------------------------|---------------------------------------------------|
| calc_title           | Get a Price Estimate              | Получете ценова оферта                            |
| service_type_label   | Service Type                      | Вид услуга                                        |
| service_ftl          | Full Truck Load (FTL)             | Пълен камион (FTL)                                |
| service_ltl          | Partial Load (LTL)                | Частичен товар (LTL)                              |
| route_type_label     | Route Type                        | Вид маршрут                                       |
| route_domestic       | Domestic Bulgaria                 | Вътрешен транспорт                                |
| route_international  | International                     | Международен                                      |
| label_origin         | From                              | От                                                |
| label_destination    | To                                | До                                                |
| placeholder_origin   | Select origin city                | Изберете град на тръгване                         |
| placeholder_dest     | Select destination                | Изберете дестинация                               |
| label_pallets        | Number of pallets                 | Брой палети                                       |
| placeholder_pallets  | e.g. 5                            | напр. 5                                           |
| label_weight_ltl     | Total weight (kg)                 | Общо тегло (кг)                                   |
| label_pallet_type    | Pallet type                       | Вид палет                                         |
| opt_eur_pallet       | EUR pallet (120×80 cm)            | ЕУР палет (120×80 см)                             |
| opt_ind_pallet       | Industrial (120×100 cm)           | Индустриален (120×100 см)                         |
| label_weight_ftl     | Cargo weight (kg)                 | Тегло на товара (кг)                              |
| label_truck_type     | Truck type                        | Тип камион                                        |
| opt_curtainsider     | Standard curtainsider             | Стандартна тентова                                |
| opt_refrigerated     | Refrigerated                      | Хладилна                                          |
| opt_flatbed          | Flatbed                           | Платформа                                         |
| label_load_date      | Desired load date                 | Желана дата на товарене                           |
| label_flexibility    | Date flexibility                  | Гъвкавост на датата                               |
| opt_flexible         | Flexible                          | Гъвкава                                           |
| opt_fixed            | Fixed date                        | Фиксирана дата                                    |
| toggle_optional      | + Optional details                | + Допълнителни подробности                        |
| estimate_label       | Estimated price                   | Приблизителна цена                                |
| estimate_secondary   | approx.                           | прибл.                                            |
| fill_fields          | Fill in details above to see estimate | Попълнете данните по-горе, за да видите оценката |
| no_rate              | Contact us for a custom quote     | Свържете се с нас за индивидуална оферта          |
| api_error            | Unable to calculate — please contact us | Не може да се изчисли — моля свържете се с нас |
| disclaimer           | Indicative estimate only. Final price subject to confirmation. | Само приблизителна оценка. Крайната цена подлежи на потвърждение. |
| btn_get_quote        | Request Formal Quote              | Поискайте официална оферта                        |
| quote_section_title  | Request a Quote                   | Заявете оферта                                    |
| label_name           | Name                              | Имe                                               |
| placeholder_name     | Your full name                    | Вашето пълно име                                  |
| label_email          | Email                             | Имейл                                             |
| placeholder_email    | your@email.com                    | вашия@имейл.com                                   |
| label_phone          | Phone (optional)                  | Телефон (незадължително)                          |
| placeholder_phone    | +359 …                            | +359 …                                            |
| label_notes          | Additional notes                  | Допълнителни бележки                              |
| placeholder_notes    | Cargo specifics, special requirements… | Специфики на товара, специални изисквания…   |
| btn_submit           | Submit Quote Request              | Изпратете заявка за оферта                        |
| submit_success       | Thank you! We will contact you shortly. | Благодарим! Ще се свържем с вас скоро.     |
| submit_error         | Something went wrong. Please try again or contact us directly. | Нещо се обърка. Моля опитайте отново или се свържете с нас директно. |

---

## 6. Instant Estimate Display

### Position
The estimate panel is a sticky-ish block positioned directly below the cargo details group, within the same section. It is always visible on desktop as a distinct card. On mobile it flows naturally below the last input group.

### States and Visual Treatment

**State 1 — Incomplete inputs**
```
┌─────────────────────────────────────────────────────────┐
│  Estimated price / Приблизителна цена                   │
│                                                         │
│  Fill in details above to see estimate.                 │
│  Попълнете данните по-горе, за да видите оценката.      │
└─────────────────────────────────────────────────────────┘
```
Visual: muted grey panel, no price visible.

**State 2 — Price found**
```
┌─────────────────────────────────────────────────────────┐
│  Estimated price / Приблизителна цена                   │
│                                                         │
│       1,200 – 1,500 BGN                                 │
│       (approx. 615 – 768 EUR)                           │
│                                                         │
│  ! Indicative estimate only. Final price subject to     │
│    confirmation.                                        │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │  REQUEST FORMAL QUOTE / ПОИСКАЙТЕ ОФИЦИАЛНА       │  │
│  │  ОФЕРТА                                           │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```
Visual: accent-colored card (matching site brand), large bold price, disclaimer in small text, CTA button prominent.

**State 3 — No rate available**
```
┌─────────────────────────────────────────────────────────┐
│  Estimated price / Приблизителна цена                   │
│                                                         │
│  Contact us for a custom quote.                         │
│  Свържете се с нас за индивидуална оферта.              │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │  REQUEST FORMAL QUOTE                             │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```
Visual: neutral panel, direct link/button to quote form or contact section.

**State 4 — API error**
```
┌─────────────────────────────────────────────────────────┐
│  Unable to calculate — please contact us.               │
│  Не може да се изчисли — моля свържете се с нас.        │
└─────────────────────────────────────────────────────────┘
```
Visual: subtle warning style (amber/orange border), no CTA shown.

### Update Behavior
- Estimate panel transitions between states smoothly (CSS opacity transition, ~150ms).
- Debounce: 300ms after last input change before sending to `/api/calculate`.
- A loading spinner or subtle shimmer replaces the price number during the API call.

---

## 7. Quote Submission Flow

### Transition from Estimate to Quote

1. User sees estimate in State 2 (price found) or State 3 (no rate).
2. User clicks "Request Formal Quote" CTA.
3. The quote extension panel slides open inline immediately below the estimate card (CSS `max-height` transition from 0 to auto, ~250ms).
4. All cargo/route fields from the calculator remain visible above as a read-only summary (condensed single-line display):
   ```
   FTL  |  Targovishte → Sofia  |  12,000 kg  |  Curtainsider
   ```
5. Contact fields (name, email, phone, notes) are now focused and editable.
6. The estimate value (e.g. "1,200 – 1,500 BGN") is included as a hidden field in the POST to `/api/quote` so the company email shows what the customer was quoted.
7. User submits the quote form.
8. On success: the quote extension panel is replaced by the confirmation message inline (no scroll jump, no reload).
9. The CTA button label changes to "Quote submitted" / "Заявката е изпратена" and becomes disabled.

### Re-use of Filled Fields
- No data re-entry is needed — all calculator inputs carry through automatically.
- The hidden `language` field is populated from `document.documentElement.lang`.
- The estimate values (min_price, max_price, currency) are passed to the API as hidden fields.

---

## 8. Validation UX

### Required Fields Summary

| Field           | Required | Condition                  |
|-----------------|----------|----------------------------|
| service_type    | Yes      | Always                     |
| route_type      | Yes      | Always                     |
| origin_city     | Yes      | Always                     |
| destination     | Yes      | Always                     |
| num_pallets     | Yes      | LTL service only           |
| total_weight_kg | Yes      | LTL service only           |
| cargo_weight_kg | Yes      | FTL service only           |
| name            | Yes      | Quote form only            |
| email           | Yes      | Quote form only            |

### Validation Rules

| Field           | Rule                                            | EN Error                                      | BG Error                                              |
|-----------------|-------------------------------------------------|-----------------------------------------------|-------------------------------------------------------|
| service_type    | Must be selected                                | Please select a service type.                 | Моля изберете вид услуга.                             |
| route_type      | Must be selected                                | Please select a route type.                   | Моля изберете вид маршрут.                            |
| origin_city     | Must be selected or entered                     | Please enter an origin city.                  | Моля въведете град на тръгване.                       |
| destination     | Must be selected                                | Please select a destination.                  | Моля изберете дестинация.                             |
| num_pallets     | Integer, min 1, max 33                          | Enter a number of pallets between 1 and 33.   | Въведете брой палети между 1 и 33.                    |
| total_weight_kg | Positive integer                                | Enter a valid total weight in kg.             | Въведете валидно общо тегло в кг.                     |
| cargo_weight_kg | Positive integer                                | Enter a valid cargo weight in kg.             | Въведете валидно тегло на товара в кг.                |
| name            | 2–100 characters                                | Name must be between 2 and 100 characters.    | Името трябва да е между 2 и 100 знака.                |
| email           | Valid email format                              | Please enter a valid email address.           | Моля въведете валиден имейл адрес.                    |
| notes           | Max 500 characters if provided                  | Notes must not exceed 500 characters.         | Бележките не трябва да надвишават 500 знака.          |

### Error Display Pattern

- Errors appear **inline**, directly below the offending field — not in a summary block at the top.
- Error text uses a small `<span role="alert">` element styled in the site's error color.
- The field receives an `aria-invalid="true"` attribute and a visible red/amber border.
- Errors clear as soon as the user corrects the field (on `input` event, not only on re-submit).
- The submit button is not disabled in advance (allows the user to attempt submission and see all errors at once on first try).

### Estimate Panel Validation
- The estimate panel does not show validation errors — it simply remains in the "incomplete" state until all required calculator fields are valid.
- This avoids premature red states before the user has had a chance to fill in the form.

---

## 9. Mobile Considerations

### Layout Adaptation

| Element                | Desktop (>= 768px)                       | Mobile (< 768px)                          |
|------------------------|------------------------------------------|-------------------------------------------|
| Service/Route toggles  | Side-by-side two-column grid             | Full-width stacked buttons                |
| Route fields (From/To) | Two columns                              | Full-width stacked                        |
| Cargo fields           | Two columns                              | Full-width stacked                        |
| Estimate panel         | Inline card below inputs                 | Full-width card below inputs              |
| Quote form (name/email)| Two columns                              | Full-width stacked                        |
| CTA button             | Full-width within card                   | Full-width                                |

### Touch Targets
- All interactive elements (toggle buttons, selects, inputs, CTA) must have a minimum touch target of 44×44px per WCAG 2.1 guideline 2.5.5.
- Tab-style toggles for service/route type use large pill buttons (min height: 48px) rather than small radio buttons.

### Sticky Estimate Panel (mobile)
- On mobile, the estimate panel does NOT use position:sticky — it stays in natural document flow to avoid covering input fields.
- After entering cargo details, the user scrolls naturally down to see the estimate.

### Optional Fields Disclosure
- The optional "load date / date flexibility" group is collapsed behind a toggle link on all screen sizes to reduce initial form length. On mobile this is especially important to prevent excessive scrolling before the user reaches the estimate.

### Keyboard and Accessibility
- All inputs have associated `<label>` elements (not just placeholders).
- All inputs have descriptive `aria-label` or `aria-labelledby` attributes in both EN and BG.
- Tab order follows visual reading order (top to bottom, left to right).
- The estimate panel uses `aria-live="polite"` so screen readers announce price updates without interrupting the user.
- The quote extension panel uses `aria-expanded` on the CTA button to convey open/closed state.
- Color is never the sole indicator of error state (text + icon + border color together).

---

## 10. Section Integration

The calculator is inserted as a new `<section id="calculator">` between the Services section and the About section in both `index.html` and `bg/index.html`. A "Calculator" / "Калкулатор" link is added to the nav.

```
Nav order:  Services | Calculator | About | Contact
            Услуги   | Калкулатор | За нас | Контакти
```

The section heading level is `<h2>` consistent with other section titles. The widget container uses the existing `.container` class for consistent max-width and padding.
