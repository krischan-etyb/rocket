"""
Pytest configuration and shared fixtures for Rocket Logistic pricing calculator tests.
"""
import pytest
import json
import os
import sys

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

SAMPLE_PRICES = {
    "_version": "2.0",
    "settings": {"currency": "EUR", "price_range_pct": 12},
    "surcharges": {"fuel_pct": 15, "express_pct": 25, "dangerous_goods_pct": 30},
    "pickup_drop_surcharge": {"ftl_eur": 80, "ltl_eur": 60},
    "truck_type_multipliers": {"standard": 1.0, "refrigerated": 1.35, "flatbed": 1.20},
    "ftl_weight_multipliers": [
        {"min_kg": 0,     "max_kg": 5000,  "multiplier": 0.96},
        {"min_kg": 5000,  "max_kg": 15000, "multiplier": 0.98},
        {"min_kg": 15000, "max_kg": None,  "multiplier": 1.00},
    ],
    "ltl_config": {
        "density_factor_kg_per_m2": 500,
        "non_pallet_multiplier": 1.15,
        "pallet_dimensions_m2": {
            "eur": 0.96,
            "industrial": 1.20,
        },
    },
    "rates": {
        "domestic": {
            "ftl_eur_per_km": 1.43,
            "ltl_eur_per_m2_per_km": 0.075,
        },
        "international": {
            "ftl_eur_per_km": 1.60,
            "ltl_eur_per_m2_per_km": 0.090,
        },
    },
    "distances_km": {
        "targovishte|sofia|bg|bg": 300,
        "sofia|targovishte|bg|bg": 300,
        "targovishte|burgas|bg|bg": 200,
        "burgas|targovishte|bg|bg": 200,
        "targovishte|varna|bg|bg": 150,
        "varna|targovishte|bg|bg": 150,
        "sofia|burgas|bg|bg": 390,
        "burgas|sofia|bg|bg": 390,
        "sofia|varna|bg|bg": 440,
        "varna|sofia|bg|bg": 440,
        "sofia|plovdiv|bg|bg": 150,
        "plovdiv|sofia|bg|bg": 150,
        "plovdiv|ruse|bg|bg": 300,
        "ruse|plovdiv|bg|bg": 300,
        "sofia|bucharest|bg|ro": 390,
        "bucharest|sofia|ro|bg": 390,
        "sofia|thessaloniki|bg|gr": 300,
        "thessaloniki|sofia|gr|bg": 300,
    },
}


@pytest.fixture
def prices_file(tmp_path):
    """Create a temporary prices.json file."""
    prices_path = tmp_path / "prices.json"
    prices_path.write_text(json.dumps(SAMPLE_PRICES))
    return str(prices_path)


@pytest.fixture
def engine(prices_file):
    """Create a PricingEngine with sample data."""
    from pricing_engine import PricingEngine
    return PricingEngine(prices_file)


@pytest.fixture
def app_client(prices_file, tmp_path):
    """Create a test Flask app client with isolated environment."""
    submissions_dir = tmp_path / "submissions"
    submissions_dir.mkdir()

    os.environ['PRICES_FILE'] = prices_file
    os.environ['SECRET_KEY'] = 'test-secret-key'
    os.environ['SUBMISSIONS_DIR'] = str(submissions_dir)

    # Reload app and config modules so they pick up env changes
    for mod in ('app', 'config', 'pricing_engine', 'distance_service'):
        if mod in sys.modules:
            del sys.modules[mod]

    import app as flask_app
    flask_app.app.config['TESTING'] = True

    with flask_app.app.test_client() as client:
        yield client
