"""
Email template factory for Rocket Logistic.

All functions return a {"subject": str, "body": str} dictionary where
body is an HTML string safe to pass directly to an SMTP send() call.
"""

from __future__ import annotations

import html as _html
from datetime import datetime


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_BASE_STYLE = """
    body { font-family: Arial, sans-serif; color: #222; background: #f5f5f5; margin: 0; padding: 0; }
    .wrapper { max-width: 620px; margin: 32px auto; background: #fff;
               border-radius: 8px; overflow: hidden;
               box-shadow: 0 2px 8px rgba(0,0,0,.12); }
    .header { background: #1E3A5F; color: #fff; padding: 24px 32px; }
    .header h1 { margin: 0; font-size: 22px; letter-spacing: 1px; }
    .header p  { margin: 4px 0 0; font-size: 13px; opacity: .85; }
    .body   { padding: 28px 32px; }
    .section-title { font-size: 13px; font-weight: bold; text-transform: uppercase;
                     color: #1E3A5F; border-bottom: 1px solid #eee;
                     padding-bottom: 6px; margin: 24px 0 12px; }
    table.info { border-collapse: collapse; width: 100%; font-size: 14px; }
    table.info td { padding: 6px 4px; vertical-align: top; }
    table.info td:first-child { color: #666; width: 42%; }
    .price-box { background: #fafafa; border: 1px solid #e0e0e0;
                 border-radius: 6px; padding: 16px 20px; margin: 20px 0; }
    .price-box .range { font-size: 26px; font-weight: bold; color: #4EA831; }
    .price-box .label { font-size: 12px; color: #888; margin-top: 4px; }
    .footer { background: #f5f5f5; padding: 16px 32px;
              font-size: 12px; color: #999; text-align: center; }
    .disclaimer { font-size: 12px; color: #999; margin-top: 20px;
                  border-top: 1px solid #eee; padding-top: 12px; }
""".strip()


def _html_document(header_title: str, header_sub: str, body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{header_title}</title>
  <style>{_BASE_STYLE}</style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <h1>Rocket Logistic</h1>
      <p>{header_sub}</p>
    </div>
    <div class="body">
      {body_html}
    </div>
    <div class="footer">
      &copy; {datetime.utcnow().year} Rocket Logistic &bull; All rights reserved
    </div>
  </div>
</body>
</html>"""


def _info_row(label: str, value: object) -> str:
    return f"<tr><td>{label}</td><td><strong>{value}</strong></td></tr>"


def _safe(value: object, fallback: str = "—") -> str:
    """Convert value to a string and HTML-escape it to prevent injection in email bodies."""
    s = str(value).strip() if value is not None else ""
    return _html.escape(s) if s else fallback


# ---------------------------------------------------------------------------
# Company notification — new quote
# ---------------------------------------------------------------------------

def get_quote_company_notification_template(
    data: dict, language: str = "en"
) -> dict[str, str]:
    """Build the internal company notification for a new quote request."""
    ts = _safe(data.get("timestamp"), datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))
    service = _safe(data.get("service_type"))
    route_type = _safe(data.get("route_type"))
    origin = f"{_safe(data.get('origin_city'))} ({_safe(data.get('origin_country'))})"
    dest = f"{_safe(data.get('destination'))} ({_safe(data.get('destination_country'))})"
    truck = _safe(data.get("truck_type"))
    load_date = _safe(data.get("load_date"))
    flexibility = _safe(data.get("date_flexibility"))

    if service.upper() == "LTL":
        if data.get("non_pallet_cargo"):
            cargo_detail = (
                f"Non-pallet — {_safe(data.get('cargo_length_cm'))} × "
                f"{_safe(data.get('cargo_width_cm'))} cm, "
                f"{_safe(data.get('total_weight_kg'))} kg"
            )
        else:
            cargo_detail = (
                f"{_safe(data.get('num_pallets'))} pallets, "
                f"{_safe(data.get('total_weight_kg'))} kg"
            )
    else:
        cargo_detail = f"{_safe(data.get('cargo_weight_kg'))} kg (FTL)"

    min_p = data.get("shown_min_price", "")
    max_p = data.get("shown_max_price", "")

    if min_p and max_p:
        price_block = f"""
        <div class="price-box">
          <div class="range">{min_p} – {max_p} EUR</div>
          <div class="label">Indicative estimate shown to customer</div>
        </div>"""
    else:
        price_block = """
        <div class="price-box">
          <div class="range">Custom quote required</div>
          <div class="label">No automated rate available for this route</div>
        </div>"""

    cargo_rows = (
        _info_row("Service type", service)
        + _info_row("Route type", route_type.capitalize())
        + _info_row("Origin", origin)
        + _info_row("Destination", dest)
        + _info_row("Cargo", cargo_detail)
        + _info_row("Truck type", truck.capitalize())
        + _info_row("Load date", load_date)
        + _info_row("Date flexibility", flexibility.capitalize())
    )

    contact_rows = (
        _info_row("Name", _safe(data.get("name")))
        + _info_row("Email", _safe(data.get("email")))
        + _info_row("Phone", _safe(data.get("phone")))
        + _info_row("Language", _safe(data.get("language", "en")).upper())
        + _info_row("Notes", _safe(data.get("notes")))
    )

    body_html = f"""
      <p style="margin-top:0">A new quote request was submitted on <strong>{ts}</strong>.</p>
      <div class="section-title">Shipment Details</div>
      <table class="info">{cargo_rows}</table>
      <div class="section-title">Price Estimate</div>
      {price_block}
      <div class="section-title">Customer Contact</div>
      <table class="info">{contact_rows}</table>
      <p class="disclaimer">This notification was generated automatically by the Rocket Logistic calculator.</p>
    """

    return {
        "subject": "New Quote Request - Rocket Logistic",
        "body": _html_document(
            "New Quote Request - Rocket Logistic",
            f"New request received at {ts}",
            body_html,
        ),
    }


# ---------------------------------------------------------------------------
# Customer confirmation — quote received
# ---------------------------------------------------------------------------

def get_quote_customer_confirmation_template(
    data: dict, language: str = "en"
) -> dict[str, str]:
    """Build the customer-facing confirmation email after a quote request."""
    lang = language.lower() if language else "en"
    is_bg = lang == "bg"

    service = _safe(data.get("service_type"))
    origin = f"{_safe(data.get('origin_city'))} ({_safe(data.get('origin_country'))})"
    dest = f"{_safe(data.get('destination'))} ({_safe(data.get('destination_country'))})"
    name = _safe(data.get("name"))

    min_p = data.get("shown_min_price")
    max_p = data.get("shown_max_price")
    has_price = min_p is not None and max_p is not None and min_p != "" and max_p != ""

    if is_bg:
        subject = "Заявка за оферта получена - Rocket Logistic"
        greeting = f"Здравейте, {name},"
        intro = (
            "Получихме вашата заявка за транспортна оферта. "
            "Нашият екип ще се свърже с вас за потвърждение на крайната цена "
            "в рамките на работния ден."
        )
        summary_title = "Резюме на заявката"
        price_title = "Приблизителна цена"
        price_label = "Само приблизителна оценка. Крайната цена подлежи на потвърждение."
        no_rate_msg = "За тази дестинация ще изготвим индивидуална оферта и ще се свържем с вас."
        next_title = "Следващи стъпки"
        next_steps = [
            "Нашият екип ще прегледа заявката ви.",
            "Ще получите потвърждение с окончателна цена.",
            "При въпроси: <a href='mailto:info@rocketlogistic.bg'>info@rocketlogistic.bg</a>",
        ]
        footer_thanks = "Благодарим ви, че се доверявате на Rocket Logistic!"
        service_label = "Вид услуга"
        origin_label = "Произход"
        dest_label = "Дестинация"
    else:
        subject = "Quote Request Received - Rocket Logistic"
        greeting = f"Hello {name},"
        intro = (
            "We have received your transport quote request. "
            "Our team will review it and contact you with a final price confirmation "
            "within the same business day."
        )
        summary_title = "Request Summary"
        price_title = "Price Estimate"
        price_label = "Indicative estimate only. Final price subject to confirmation."
        no_rate_msg = "For this destination we will prepare a custom quote and get back to you."
        next_title = "Next Steps"
        next_steps = [
            "Our team will review your request.",
            "You will receive a confirmation with the final price.",
            "For questions: <a href='mailto:info@rocketlogistic.bg'>info@rocketlogistic.bg</a>",
        ]
        footer_thanks = "Thank you for choosing Rocket Logistic!"
        service_label = "Service type"
        origin_label = "Origin"
        dest_label = "Destination"

    summary_rows = (
        _info_row(service_label, service)
        + _info_row(origin_label, origin)
        + _info_row(dest_label, dest)
    )

    if has_price:
        price_block = f"""
        <div class="section-title">{price_title}</div>
        <div class="price-box">
          <div class="range">{min_p} – {max_p} EUR</div>
          <div class="label">{price_label}</div>
        </div>"""
    else:
        price_block = f"""
        <div class="section-title">{price_title}</div>
        <div class="price-box">
          <div class="label">{no_rate_msg}</div>
        </div>"""

    steps_html = "".join(f"<li>{s}</li>" for s in next_steps)

    body_html = f"""
      <p style="margin-top:0">{greeting}</p>
      <p>{intro}</p>
      <div class="section-title">{summary_title}</div>
      <table class="info">{summary_rows}</table>
      {price_block}
      <div class="section-title">{next_title}</div>
      <ul style="font-size:14px; padding-left:20px; line-height:1.8">
        {steps_html}
      </ul>
      <p style="margin-top:28px; font-weight:bold">{footer_thanks}</p>
      <p class="disclaimer">{price_label}</p>
    """

    return {
        "subject": subject,
        "body": _html_document(subject, subject, body_html),
    }


# ---------------------------------------------------------------------------
# Company notification — contact form
# ---------------------------------------------------------------------------

def get_contact_template(data: dict, language: str = "en") -> dict[str, str]:
    """Build the company notification email for a contact-form submission."""
    ts = _safe(
        data.get("timestamp"),
        datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    )

    rows = (
        _info_row("Name", _safe(data.get("name")))
        + _info_row("Email", _safe(data.get("email")))
        + _info_row("Phone", _safe(data.get("phone")))
        + _info_row("Submitted", ts)
        + _info_row("IP", _safe(data.get("ip")))
    )

    message_text = _safe(data.get("message"), "(no message)")

    body_html = f"""
      <p style="margin-top:0">A new contact form submission was received on <strong>{ts}</strong>.</p>
      <div class="section-title">Contact Details</div>
      <table class="info">{rows}</table>
      <div class="section-title">Message</div>
      <div style="background:#fafafa; border:1px solid #e0e0e0; border-radius:6px;
                  padding:16px; font-size:14px; white-space:pre-wrap;">{message_text}</div>
      <p class="disclaimer">This notification was generated automatically by the Rocket Logistic website.</p>
    """

    return {
        "subject": "New Contact Form Submission - Rocket Logistic",
        "body": _html_document(
            "New Contact Submission - Rocket Logistic",
            f"Received at {ts}",
            body_html,
        ),
    }
