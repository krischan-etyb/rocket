"""
Integration tests for Flask pricing calculator API endpoints.

Tests cover:
- /health endpoint
- /api/calculate validation and success cases
- /api/quote validation and success cases
- Error handling
"""
import pytest
import json
import os


# ---------------------------------------------------------------------------
# Payload helpers
# ---------------------------------------------------------------------------

def ftl_payload(**overrides):
    base = {
        "service_type": "ftl",
        "origin_country": "BG",
        "origin_city": "Targovishte",
        "destination_country": "BG",
        "destination": "Sofia",
        "cargo_weight_kg": 10000,
        "truck_type": "standard",
        "date_flexibility": "flexible",
    }
    base.update(overrides)
    return base


def ltl_payload(**overrides):
    base = {
        "service_type": "ltl",
        "origin_country": "BG",
        "origin_city": "Targovishte",
        "destination_country": "BG",
        "destination": "Sofia",
        "num_pallets": 4,
        "total_weight_kg": 1200,
        "pallet_type": "eur",
        "non_pallet_cargo": False,
        "date_flexibility": "flexible",
    }
    base.update(overrides)
    return base


def quote_payload(**overrides):
    base = {**ftl_payload(), "name": "Ivan Petrov", "email": "ivan@example.com"}
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

class TestHealthEndpoint:

    def test_health_returns_ok(self, app_client):
        response = app_client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"


# ---------------------------------------------------------------------------
# /api/calculate — validation
# ---------------------------------------------------------------------------

class TestCalculateValidation:

    def test_calculate_missing_service_type(self, app_client):
        payload = ftl_payload()
        del payload["service_type"]
        r = app_client.post("/api/calculate", json=payload)
        assert r.status_code == 400

    def test_calculate_missing_origin_country(self, app_client):
        payload = ftl_payload()
        del payload["origin_country"]
        r = app_client.post("/api/calculate", json=payload)
        assert r.status_code == 400

    def test_calculate_missing_origin_city(self, app_client):
        payload = ftl_payload()
        del payload["origin_city"]
        r = app_client.post("/api/calculate", json=payload)
        assert r.status_code == 400

    def test_calculate_missing_destination_country(self, app_client):
        payload = ftl_payload()
        del payload["destination_country"]
        r = app_client.post("/api/calculate", json=payload)
        assert r.status_code == 400

    def test_calculate_missing_destination(self, app_client):
        payload = ftl_payload()
        del payload["destination"]
        r = app_client.post("/api/calculate", json=payload)
        assert r.status_code == 400

    def test_calculate_ltl_missing_num_pallets(self, app_client):
        payload = ltl_payload()
        del payload["num_pallets"]
        r = app_client.post("/api/calculate", json=payload)
        assert r.status_code == 400

    def test_calculate_ltl_num_pallets_zero(self, app_client):
        r = app_client.post("/api/calculate", json=ltl_payload(num_pallets=0))
        assert r.status_code == 400

    def test_calculate_ltl_num_pallets_34(self, app_client):
        r = app_client.post("/api/calculate", json=ltl_payload(num_pallets=34))
        assert r.status_code == 400

    def test_calculate_ltl_missing_weight(self, app_client):
        payload = ltl_payload()
        del payload["total_weight_kg"]
        r = app_client.post("/api/calculate", json=payload)
        assert r.status_code == 400

    def test_calculate_ltl_nonpallet_missing_cargo_length(self, app_client):
        payload = ltl_payload(
            non_pallet_cargo=True,
            total_weight_kg=500,
            cargo_width_cm=80,
        )
        del payload["num_pallets"]
        r = app_client.post("/api/calculate", json=payload)
        assert r.status_code == 400

    def test_calculate_ftl_missing_weight(self, app_client):
        payload = ftl_payload()
        del payload["cargo_weight_kg"]
        r = app_client.post("/api/calculate", json=payload)
        assert r.status_code == 400

    def test_calculate_invalid_service_type(self, app_client):
        r = app_client.post("/api/calculate", json=ftl_payload(service_type="xyz"))
        assert r.status_code == 400

    def test_calculate_invalid_json_body(self, app_client):
        r = app_client.post(
            "/api/calculate",
            data="{bad json}",
            content_type="application/json",
        )
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# /api/calculate — success
# ---------------------------------------------------------------------------

class TestCalculateSuccess:

    def test_ftl_domestic_returns_price(self, app_client):
        r = app_client.post("/api/calculate", json=ftl_payload())
        assert r.status_code == 200
        data = r.get_json()
        assert data["success"] is True
        assert data["min_price"] > 0
        assert data["max_price"] > data["min_price"]
        assert data["currency"] == "EUR"

    def test_ltl_domestic_returns_price(self, app_client):
        r = app_client.post("/api/calculate", json=ltl_payload())
        assert r.status_code == 200
        data = r.get_json()
        assert data["success"] is True
        assert data["min_price"] > 0

    def test_ltl_nonpallet_returns_price(self, app_client):
        payload = ltl_payload(
            non_pallet_cargo=True,
            total_weight_kg=500,
            cargo_length_cm=240,
            cargo_width_cm=160,
        )
        del payload["num_pallets"]
        r = app_client.post("/api/calculate", json=payload)
        assert r.status_code == 200
        data = r.get_json()
        assert data["success"] is True
        assert data["min_price"] > 0

    def test_calculate_unknown_route_returns_no_rate(self, app_client):
        payload = ftl_payload(origin_city="UnknownCityXYZ", destination="AnotherUnknown")
        r = app_client.post("/api/calculate", json=payload)
        assert r.status_code == 200
        data = r.get_json()
        assert data.get("no_rate") is True

    def test_calculate_international_ro(self, app_client):
        payload = ftl_payload(destination_country="RO", destination="Bucharest")
        r = app_client.post("/api/calculate", json=payload)
        assert r.status_code == 200
        data = r.get_json()
        assert data["success"] is True

    def test_calculate_response_has_breakdown(self, app_client):
        r = app_client.post("/api/calculate", json=ftl_payload())
        data = r.get_json()
        assert "breakdown" in data
        bd = data["breakdown"]
        assert "base_price" in bd
        assert "fuel_surcharge" in bd
        assert "distance_km" in bd

    def test_express_surcharge_fixed_higher_than_flexible(self, app_client):
        flex = app_client.post("/api/calculate", json=ftl_payload(date_flexibility="flexible")).get_json()
        fixed = app_client.post("/api/calculate", json=ftl_payload(date_flexibility="fixed")).get_json()
        assert flex["success"] is True
        assert fixed["success"] is True
        assert fixed["min_price"] > flex["min_price"]
        assert fixed["max_price"] > flex["max_price"]

    def test_calculate_response_includes_disclaimer(self, app_client):
        r = app_client.post("/api/calculate", json=ftl_payload())
        data = r.get_json()
        assert "disclaimer" in data
        assert "disclaimer_bg" in data

    def test_calculate_ltl_1_pallet_boundary(self, app_client):
        r = app_client.post("/api/calculate", json=ltl_payload(num_pallets=1))
        assert r.status_code == 200
        data = r.get_json()
        assert data["success"] is True

    def test_calculate_ltl_33_pallets_boundary(self, app_client):
        r = app_client.post("/api/calculate", json=ltl_payload(num_pallets=33))
        assert r.status_code == 200
        data = r.get_json()
        assert data["success"] is True


# ---------------------------------------------------------------------------
# /api/quote — validation
# ---------------------------------------------------------------------------

class TestQuoteValidation:

    def test_quote_missing_name(self, app_client):
        payload = quote_payload()
        del payload["name"]
        r = app_client.post("/api/quote", json=payload)
        assert r.status_code == 400

    def test_quote_name_too_short(self, app_client):
        r = app_client.post("/api/quote", json=quote_payload(name="A"))
        assert r.status_code == 400

    def test_quote_name_too_long(self, app_client):
        r = app_client.post("/api/quote", json=quote_payload(name="A" * 101))
        assert r.status_code == 400

    def test_quote_no_email_or_phone(self, app_client):
        payload = quote_payload()
        del payload["email"]
        r = app_client.post("/api/quote", json=payload)
        assert r.status_code == 400

    def test_quote_invalid_email_format(self, app_client):
        r = app_client.post("/api/quote", json=quote_payload(email="not-valid"))
        assert r.status_code == 400

    def test_quote_notes_too_long(self, app_client):
        r = app_client.post("/api/quote", json=quote_payload(notes="x" * 501))
        assert r.status_code == 400

    def test_quote_phone_only_accepted(self, app_client):
        payload = quote_payload(phone="+359 88 123 4567")
        del payload["email"]
        r = app_client.post("/api/quote", json=payload)
        assert r.status_code == 200

    def test_quote_email_only_accepted(self, app_client):
        payload = quote_payload()
        payload.pop("phone", None)
        r = app_client.post("/api/quote", json=payload)
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# /api/quote — success
# ---------------------------------------------------------------------------

class TestQuoteSuccess:

    def test_quote_success_response(self, app_client):
        r = app_client.post("/api/quote", json=quote_payload())
        assert r.status_code == 200
        data = r.get_json()
        assert data["success"] is True
        assert "message" in data

    def test_quote_saves_to_json(self, app_client, tmp_path):
        r = app_client.post("/api/quote", json=quote_payload())
        assert r.status_code == 200
        submissions_dir = os.environ.get("SUBMISSIONS_DIR", "")
        quotes_json = os.path.join(submissions_dir, "quotes.json")
        assert os.path.isfile(quotes_json)
        with open(quotes_json, encoding="utf-8") as f:
            records = json.load(f)
        assert len(records) >= 1
        assert records[-1]["name"] == "Ivan Petrov"

    def test_quote_saves_to_csv(self, app_client):
        r = app_client.post("/api/quote", json=quote_payload())
        assert r.status_code == 200
        submissions_dir = os.environ.get("SUBMISSIONS_DIR", "")
        quotes_csv = os.path.join(submissions_dir, "quotes.csv")
        assert os.path.isfile(quotes_csv)

    def test_quote_shown_prices_logged_not_affecting_calculation(self, app_client):
        payload = quote_payload(shown_min_price=1, shown_max_price=2)
        r = app_client.post("/api/quote", json=payload)
        assert r.status_code == 200
        data = r.get_json()
        assert data["success"] is True
        if "min_price" in data:
            assert data["min_price"] > 2

    def test_quote_with_notes(self, app_client):
        r = app_client.post("/api/quote", json=quote_payload(
            notes="Fragile machinery parts, no stacking."
        ))
        assert r.status_code == 200
        data = r.get_json()
        assert data["success"] is True

    def test_quote_bulgarian_language(self, app_client):
        r = app_client.post("/api/quote", json=quote_payload(language="bg"))
        assert r.status_code == 200
        data = r.get_json()
        assert data["success"] is True

    def test_quote_no_rate_route_still_succeeds(self, app_client):
        payload = quote_payload(origin_city="UnknownXYZ", destination="AnotherXYZ")
        r = app_client.post("/api/quote", json=payload)
        assert r.status_code == 200
        data = r.get_json()
        assert data["success"] is True
