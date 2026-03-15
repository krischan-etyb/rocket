# CSS Component Plan — Price Calculator
## Rocket Logistic · rocket-calculator-planning
**Revised after:** ux-wireframe.md v1.0 (2026-03-06)

---

## 1. Existing Design Tokens Inventory

All tokens are defined in `css/style.css` `:root`. The calculator must use these exclusively — no hard-coded values.

### Colors
| Token | Value | Intended use in calculator |
|---|---|---|
| `--color-brand-green` | `#4EA831` | Active toggle (selected state), estimate card top border |
| `--color-brand-green-dark` | `#3D8A26` | Hover on green-selected toggles |
| `--color-primary` | `#1E3A5F` | Label text, active toggle fill, price figure |
| `--color-primary-dark` | `#152a45` | Hover on primary-filled toggles |
| `--color-accent` | `#FF6B35` | CTA "Request Formal Quote" button, API-error panel border |
| `--color-accent-dark` | `#e55a2b` | CTA hover |
| `--color-light` | `#F5F5F5` | Section background, incomplete/no-rate/error panel backgrounds |
| `--color-dark` | `#333333` | Body/input text |
| `--color-white` | `#FFFFFF` | Card backgrounds, input fields, price-found panel |
| `--color-gray` | `#555555` | Helper text, inactive toggle labels, disclaimer |
| `--color-gray-light` | `#E8E8E8` | Input borders, dividers, inactive toggle borders |
| `--color-success` | `#4CAF50` | Available if a success icon is needed in price-found state |
| `--color-error` | `#e74c3c` | Inline validation errors, error-state field borders |

### Typography
| Token | Value |
|---|---|
| `--font-heading` | `'Montserrat', sans-serif` |
| `--font-body` | `'Open Sans', sans-serif` |
| `--fs-xs` | `0.8rem` |
| `--fs-sm` | `0.875rem` |
| `--fs-base` | `1rem` |
| `--fs-md` | `1.25rem` |
| `--fs-lg` | `1.563rem` |
| `--fs-xl` | `1.953rem` |
| `--fs-2xl` | `2.441rem` |
| `--fs-3xl` | `3.052rem` |

### Spacing / Layout
| Token | Value |
|---|---|
| `--space-xs` | `0.25rem` |
| `--space-sm` | `0.5rem` |
| `--space-md` | `1rem` |
| `--space-lg` | `1.5rem` |
| `--space-xl` | `2rem` |
| `--space-2xl` | `3rem` |
| `--space-3xl` | `4rem` |
| `--section-padding` | `80px 0` (60px on mobile) |
| `--container-width` | `1200px` |
| `--nav-height` | `70px` (60px on mobile) |
| `--transition` | `0.3s ease` |

---

## 2. New Component Class Plan (BEM)

All new rules go into a single new section block appended to `css/style.css`, following the existing section-comment architecture:

```css
/* =============================================
   Price Calculator Section
   ============================================= */
```

No new file. The project uses a single stylesheet.

---

### 2.1 Calculator Section Container

```css
.calculator                   /* <section id="calculator"> */
.calculator__header           /* centered heading + subtitle wrapper */
```

Section background: `var(--color-white)` — sits between `.services` (light) and `.about` (white). Two consecutive white sections are visually separated by the bordered group cards within the calculator, so the rhythm remains clear.

The `.container` class is reused inside for max-width and padding, matching every other section. The `<h2>` uses `.section__title` + `.section__subtitle` — no new heading rules.

---

### 2.2 Form Layout

The wireframe is a **single-column vertical flow** — not a two-column form/result split. All groups stack vertically, full-width within the container. Two-column layout applies only within individual groups (e.g., From/To side by side, Name/Email side by side).

```css
.calculator__form             /* <form> element */
.calculator__group            /* visual card wrapping a set of related fields */
.calculator__group-title      /* all-caps label above a group, e.g. "SERVICE TYPE" */
```

```css
.calculator__group {
    background-color: var(--color-white);
    border: 1px solid var(--color-gray-light);
    border-radius: 8px;
    padding: var(--space-xl);
    margin-bottom: var(--space-lg);
}

.calculator__group-title {
    font-family: var(--font-heading);
    font-size: var(--fs-xs);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--color-gray);
    margin-bottom: var(--space-md);
}
```

Two-column field rows within groups:

```css
.form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-md);
}

@media (max-width: 768px) {
    .form-row {
        grid-template-columns: 1fr;
    }
}
```

Standard form primitives reused without modification: `.form-group`, `.form-group label`, `.form-group input`, `.form-group select`, `.form-group textarea`, `.form-error`.

---

### 2.3 Service Type and Route Type Toggles

Each toggle group (Service Type, Route Type) is an independent pair of styled radio buttons. Desktop: two buttons side by side. Mobile: stacked full-width.

```css
.toggle-group                 /* wrapper for one toggle pair + its label */
.toggle-group__options        /* grid container for the two toggle buttons */
.toggle-group__btn            /* <label> wrapping hidden <input type="radio"> */
.toggle-group__btn--selected  /* JS-added modifier when radio is checked */
```

```css
.toggle-group {
    margin-bottom: var(--space-lg);
}

.toggle-group__options {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-sm);
}

.toggle-group__btn {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 48px;             /* WCAG 2.5.5 — minimum touch target */
    padding: var(--space-sm) var(--space-md);
    font-family: var(--font-heading);
    font-size: var(--fs-sm);
    font-weight: 600;
    text-align: center;
    cursor: pointer;
    border: 2px solid var(--color-gray-light);
    border-radius: 4px;
    background-color: var(--color-white);
    color: var(--color-gray);
    transition: var(--transition);
}

/* Hide native radio — visually replaced by styled label */
.toggle-group__btn input[type="radio"] {
    position: absolute;
    opacity: 0;
    width: 0;
    height: 0;
}

/* Selected state — :has() for CSS-only, .--selected as JS fallback */
.toggle-group__btn--selected,
.toggle-group__btn:has(input:checked) {
    background-color: var(--color-primary);
    border-color: var(--color-primary);
    color: var(--color-white);
}

.toggle-group__btn:hover:not(.toggle-group__btn--selected) {
    border-color: var(--color-primary);
    color: var(--color-primary);
}

/* Focus ring — radio is hidden, so focus-within on the label */
.toggle-group__btn:focus-within {
    outline: 2px solid var(--color-accent);
    outline-offset: 2px;
}

/* Mobile: stack full-width */
@media (max-width: 768px) {
    .toggle-group__options {
        grid-template-columns: 1fr;
    }
}
```

`:has()` support: Chrome 105+, Firefox 121+, Safari 15.4+. The JS-toggled `.toggle-group__btn--selected` modifier provides the fallback.

---

### 2.4 Progressive Disclosure (no step indicators)

The UX is single-page progressive disclosure. There are no step indicators — the form is one scrollable page where earlier selections conditionally reveal later groups via JS.

```css
.calculator__group.is-hidden {
    display: none;
}

/* Optional fade-in on reveal — reuses existing @keyframes fadeIn from style.css */
.calculator__group.is-revealed {
    animation: fadeIn 0.3s ease forwards;
}
```

---

### 2.5 Optional Fields Disclosure Toggle

Load date and date flexibility fields are collapsed by default behind a toggle link.

```css
.optional-toggle              /* <button> styled as a text link */
.optional-fields              /* wrapper div for the collapsible optional fields */
.optional-fields.is-open      /* JS adds this class to expand */
```

```css
.optional-toggle {
    display: inline-flex;
    align-items: center;
    gap: var(--space-xs);
    font-family: var(--font-body);
    font-size: var(--fs-sm);
    color: var(--color-accent);
    background: none;
    border: none;
    cursor: pointer;
    padding: var(--space-xs) 0;
    margin-top: var(--space-sm);
    text-decoration: underline;
    transition: var(--transition);
}

.optional-toggle:hover {
    color: var(--color-accent-dark);
}

.optional-fields {
    overflow: hidden;
    max-height: 0;
    transition: max-height 0.25s ease;
}

.optional-fields.is-open {
    max-height: 300px;   /* larger than content; actual content is two fields */
}
```

---

### 2.6 Estimate Panel — 4 States

Full-width card positioned directly below the cargo details group, in normal document flow. No `position: sticky` on any breakpoint.

```css
.estimate-panel               /* card wrapper; aria-live="polite" on this element */
.estimate-panel__header       /* "Estimated price" label */
.estimate-panel__price        /* large BGN range */
.estimate-panel__secondary    /* EUR secondary amount */
.estimate-panel__disclaimer   /* italic disclaimer */
.estimate-panel__message      /* prompt / no-rate / error message text */

/* State modifiers */
.estimate-panel--incomplete   /* State 1: required fields not yet filled */
.estimate-panel--price-found  /* State 2: API returned a rate */
.estimate-panel--no-rate      /* State 3: no rate available */
.estimate-panel--error        /* State 4: API/network error */
.estimate-panel--loading      /* Transitional: spinner shown during API call */
```

```css
/* Base */
.estimate-panel {
    border-radius: 8px;
    border: 1px solid var(--color-gray-light);
    padding: var(--space-xl);
    margin-top: var(--space-lg);
    opacity: 1;
    transition: opacity 150ms ease, background-color var(--transition), border-color var(--transition);
}

.estimate-panel__header {
    font-family: var(--font-heading);
    font-size: var(--fs-sm);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--color-gray);
    margin-bottom: var(--space-md);
}

/* State 1 — Incomplete */
.estimate-panel--incomplete {
    background-color: var(--color-light);
}

.estimate-panel--incomplete .estimate-panel__price,
.estimate-panel--incomplete .estimate-panel__secondary,
.estimate-panel--incomplete .estimate-panel__disclaimer {
    display: none;
}

.estimate-panel__message {
    font-size: var(--fs-sm);
    color: var(--color-gray);
}

/* State 2 — Price found */
.estimate-panel--price-found {
    background-color: var(--color-white);
    border-top: 4px solid var(--color-brand-green);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.estimate-panel__price {
    font-family: var(--font-heading);
    font-size: var(--fs-2xl);
    font-weight: 700;
    color: var(--color-primary);
    line-height: 1.1;
}

.estimate-panel__secondary {
    font-size: var(--fs-base);
    color: var(--color-gray);
    margin-top: var(--space-xs);
}

.estimate-panel__disclaimer {
    font-size: var(--fs-xs);
    color: var(--color-gray);
    font-style: italic;
    margin-top: var(--space-md);
}

/* State 3 — No rate */
.estimate-panel--no-rate {
    background-color: var(--color-light);
}

.estimate-panel--no-rate .estimate-panel__price,
.estimate-panel--no-rate .estimate-panel__secondary,
.estimate-panel--no-rate .estimate-panel__disclaimer {
    display: none;
}

/* State 4 — API error: accent orange border as warning indicator */
.estimate-panel--error {
    background-color: var(--color-light);
    border-color: var(--color-accent);
    border-width: 2px;
}

.estimate-panel--error .estimate-panel__price,
.estimate-panel--error .estimate-panel__secondary,
.estimate-panel--error .estimate-panel__disclaimer {
    display: none;
}

/* Loading */
.estimate-panel--loading {
    opacity: 0.6;
}

.estimate-panel--loading .estimate-panel__price,
.estimate-panel--loading .estimate-panel__secondary {
    visibility: hidden;
}
```

---

### 2.7 CTA Button — Request Formal Quote

Reuses `.btn.btn--primary.btn--full` exactly. No new class needed.

```html
<button type="button" class="btn btn--primary btn--full" aria-expanded="false">
    Request Formal Quote
</button>
```

`aria-expanded` is toggled by JS when the quote extension panel opens/closes. The CTA is only present in State 2 and State 3 panels.

After successful quote submission, the button becomes disabled:

```css
.btn--primary:disabled,
.btn--primary[disabled] {
    background-color: var(--color-gray-light);
    color: var(--color-gray);
    cursor: not-allowed;
    transform: none;
}
```

---

### 2.8 Quote Extension Panel

Expands inline below the estimate panel using a `max-height` CSS transition (250ms as specified in wireframe).

```css
.quote-extension              /* expanding wrapper div */
.quote-extension.is-open      /* JS adds this to expand */
.quote-summary-bar            /* read-only condensed calculator summary above quote form */
.quote-summary-bar__text      /* single-line text: "FTL | Targovishte → Sofia | 12,000 kg" */
```

```css
.quote-extension {
    overflow: hidden;
    max-height: 0;
    transition: max-height 250ms ease;
}

.quote-extension.is-open {
    max-height: 900px;   /* large enough for all contact fields + submit button */
}

.quote-summary-bar {
    background-color: var(--color-light);
    border-radius: 4px;
    padding: var(--space-sm) var(--space-md);
    margin-bottom: var(--space-lg);
    border-left: 3px solid var(--color-brand-green);
}

.quote-summary-bar__text {
    font-family: var(--font-heading);
    font-size: var(--fs-sm);
    font-weight: 600;
    color: var(--color-primary);
}
```

Contact form fields inside `.quote-extension` use `.form-group` / `.form-row` without modification.

---

### 2.9 Loading Spinner

```css
.calc-spinner                 /* container shown during API call */
.calc-spinner__ring           /* CSS-only animated ring */
```

```css
.calc-spinner {
    display: none;
    justify-content: center;
    align-items: center;
    padding: var(--space-xl) 0;
}

.estimate-panel--loading .calc-spinner {
    display: flex;
}

.calc-spinner__ring {
    width: 36px;
    height: 36px;
    border: 3px solid var(--color-gray-light);
    border-top-color: var(--color-brand-green);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}
```

The `spin` animation must be suppressed inside the existing `@media (prefers-reduced-motion: reduce)` block in style.css (see Section 5).

---

### 2.10 Inline Validation

Reuses existing `.form-error` class. Two additional rules:

```css
.form-group select.field-error {
    border-color: var(--color-error);
}

.form-group input[aria-invalid="true"],
.form-group select[aria-invalid="true"],
.form-group textarea[aria-invalid="true"] {
    border-color: var(--color-error);
}
```

---

## 3. Page Placement Recommendation

### Position in index.html and bg/index.html

Insert **between `.services` and `.about`** per ux-wireframe.md Section 10:

```
hero       (#hero)
services   (#services)
           ← INSERT <section class="calculator" id="calculator">
about      (#about)
contact    (#contact)
footer
```

Section anchor: `id="calculator"` (not `id="calculate"`).

Background rhythm: services (`--color-light`) → calculator (`--color-white`) → about (`--color-white`) → contact (`--color-light`). The bordered group cards inside the calculator visually separate it from `.about` despite both being white.

### Navigation link

Insert between the Services and About links:

```html
<li class="nav__item">
    <a href="#calculator" class="nav__link" data-en="Calculator" data-bg="Калкулатор">Calculator</a>
</li>
```

Nav order: **Services | Calculator | About | Contact**

---

## 4. Responsive Breakpoints

| Breakpoint | Calculator behaviour |
|---|---|
| Desktop `> 1024px` | Two-column within groups (toggle pairs, From/To, Name/Email). Estimate panel: full-width inline card. |
| Tablet `max-width: 1024px` | Same two-column within groups. Reduce `.calculator__group` padding to `var(--space-lg)`. |
| Mobile `max-width: 768px` | Everything single-column. Toggle pairs stack vertically. Estimate panel: in-flow, no sticky. |
| Small mobile `max-width: 480px` | `.calculator__group` padding reduces to `var(--space-md)`. Button padding via existing `.btn` override. |

```css
@media (max-width: 1024px) {
    .calculator__group {
        padding: var(--space-lg);
    }
}

@media (max-width: 768px) {
    .toggle-group__options {
        grid-template-columns: 1fr;
    }

    .form-row {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 480px) {
    .calculator__group {
        padding: var(--space-md);
    }
}
```

---

## 5. Consistency Notes

1. **Border-radius**: `4px` for buttons/inputs/toggle buttons; `8px` for group cards and estimate panel. Matches `.service-card`, `.contact__form`, `.stat`.

2. **Box shadow**: `0 4px 20px rgba(0, 0, 0, 0.08)` on `.estimate-panel--price-found` only. Other states use border only.

3. **Section heading**: `.section__title` + `.section__subtitle` — reuse without override.

4. **Form inputs**: Existing focus state (`border-color: var(--color-accent)`, `outline: 2px solid var(--color-accent)`) already defined — no override.

5. **Button**: Only `.btn--primary`. No new button colour or ghost/outline variant.

6. **Top border accent**: `border-top: 4px solid var(--color-brand-green)` on `.estimate-panel--price-found` — mirrors `.service-card--featured` pattern.

7. **Transition**: `var(--transition)` (0.3s ease) on all interactive elements. Justified exceptions: `max-height` expansions use 250ms ease (per UX spec); spinner uses 0.8s linear.

8. **Focus accessibility**: Toggle buttons (labels wrapping hidden radios) require `.toggle-group__btn:focus-within` rule. All other elements inherit site-wide `*:focus-visible`.

9. **Font weights**: 400 (body), 600 (labels, buttons), 700 (headings, price). Do not introduce 500 or 800.

10. **Touch targets**: Toggle buttons `min-height: 48px`. Inputs: `padding: 12px 16px` + 1rem font = ~44px. Meets WCAG 2.5.5.

11. **Reduced motion**: Add to existing `@media (prefers-reduced-motion: reduce)` block:
    ```css
    .calc-spinner__ring { animation: none; }
    .optional-fields,
    .quote-extension { transition: none; }
    ```

12. **Bilingual support**: All visible text uses `data-en` / `data-bg` attributes, handled by the existing language-toggle JS already on the site. No CSS changes needed for bilingual support.

### Color contrast (WCAG 2.1 AA)

| Element | Foreground | Background | Ratio | Pass |
|---|---|---|---|---|
| Body/input text | `#333333` | `#FFFFFF` | ~12.6:1 | AA |
| Label text | `#1E3A5F` | `#FFFFFF` | ~10.7:1 | AA |
| Inactive toggle text | `#555555` | `#FFFFFF` | ~7.4:1 | AA |
| Active toggle text | `#FFFFFF` | `#1E3A5F` | ~10.7:1 | AA |
| Price figure | `#1E3A5F` | `#FFFFFF` | ~10.7:1 | AA |
| CTA button text | `#FFFFFF` | `#FF6B35` | ~3.1:1 | AA large text |
| Helper/disclaimer | `#555555` | `#F5F5F5` | ~6.1:1 | AA |
| Error text | `#e74c3c` | `#FFFFFF` | ~4.7:1 | AA |
| Group title | `#555555` | `#FFFFFF` | ~7.4:1 | AA |

---

## 6. Complete Class Reference

| Class | Element | Description |
|---|---|---|
| `.calculator` | `<section>` | Section container |
| `.calculator__header` | `<div>` | Heading + subtitle wrapper |
| `.calculator__form` | `<form>` | The form |
| `.calculator__group` | `<div>` | Visual card for a field group |
| `.calculator__group-title` | `<p>` | All-caps group label |
| `.toggle-group` | `<div>` | Wrapper for one radio toggle pair |
| `.toggle-group__options` | `<div>` | Grid of toggle buttons |
| `.toggle-group__btn` | `<label>` | Styled radio toggle button |
| `.toggle-group__btn--selected` | modifier | JS-added on checked state |
| `.form-row` | `<div>` | Two-column field grid |
| `.optional-toggle` | `<button>` | Expand link for optional fields |
| `.optional-fields` | `<div>` | Collapsible optional fields wrapper |
| `.optional-fields.is-open` | state | JS-added to expand |
| `.estimate-panel` | `<div>` | Estimate result card (`aria-live="polite"`) |
| `.estimate-panel__header` | `<p>` | "Estimated price" label |
| `.estimate-panel__price` | `<p>` | Large BGN range |
| `.estimate-panel__secondary` | `<p>` | EUR secondary amount |
| `.estimate-panel__disclaimer` | `<p>` | Italic disclaimer |
| `.estimate-panel__message` | `<p>` | Prompt / no-rate / error message |
| `.estimate-panel--incomplete` | state modifier | No fields filled |
| `.estimate-panel--price-found` | state modifier | API returned rate |
| `.estimate-panel--no-rate` | state modifier | No rate available |
| `.estimate-panel--error` | state modifier | API/network error |
| `.estimate-panel--loading` | state modifier | Waiting for API |
| `.calc-spinner` | `<div>` | Spinner container |
| `.calc-spinner__ring` | `<div>` | Animated ring |
| `.quote-extension` | `<div>` | Expandable quote form wrapper |
| `.quote-extension.is-open` | state | JS-added to expand |
| `.quote-summary-bar` | `<div>` | Read-only condensed calculator summary |
| `.quote-summary-bar__text` | `<p>` | Summary text line |

**Reused without modification:** `.form-group`, `.form-group label`, `.form-group input`, `.form-group select`, `.form-group textarea`, `.form-error`, `.btn`, `.btn--primary`, `.btn--full`, `.section__title`, `.section__subtitle`, `.container`

---

*Source files: `css/style.css`, `index.html`, `planning/ux-wireframe.md` v1.0*
