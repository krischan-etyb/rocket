"""
Unit tests for PricingEngine v2 — distance-based pricing model.

Tests cover:
- FTL pricing with weight multipliers and pickup/drop surcharge
- LTL pricing with chargeable m² logic (pallet and non-pallet)
- Industrial vs euro pallet dimensions
- Express surcharges
- Response format validation
- Edge cases
"""
import pytest


# ---------------------------------------------------------------------------
# Base payloads
# ---------------------------------------------------------------------------

def _ftl(origin_city="Targovishte", destination="Sofia", truck_type="standard",
         cargo_weight_kg=10000, date_flexibility="flexible",
         origin_country="BG", destination_country="BG", **kw):
    d = {
        "service_type": "ftl",
        "origin_country": origin_country,
        "origin_city": origin_city,
        "destination_country": destination_country,
        "destination": destination,
        "cargo_weight_kg": cargo_weight_kg,
        "truck_type": truck_type,
        "date_flexibility": date_flexibility,
    }
    d.update(kw)
    return d


def _ltl(origin_city="Targovishte", destination="Sofia", num_pallets=4,
         total_weight_kg=1200, pallet_type="eur", date_flexibility="flexible",
         origin_country="BG", destination_country="BG", **kw):
    d = {
        "service_type": "ltl",
        "origin_country": origin_country,
        "origin_city": origin_city,
        "destination_country": destination_country,
        "destination": destination,
        "num_pallets": num_pallets,
        "total_weight_kg": total_weight_kg,
        "pallet_type": pallet_type,
        "non_pallet_cargo": False,
        "date_flexibility": date_flexibility,
    }
    d.update(kw)
    return d


# ---------------------------------------------------------------------------
# FTL — weight multipliers & pickup/drop
# ---------------------------------------------------------------------------

class TestFTLPricing:

    def test_ftl_light_weight_multiplier(self, engine):
        """
        3000 kg (light bracket, mult=0.96), 300 km, standard truck:
        base = 300 * 1.43 * 0.96 * 1.0 + 80 = 411.84 + 80 = 491.84
        fuel = 491.84 * 0.15 = 73.776
        with_fuel = 565.616
        min = round(565.616 * 0.88) = 498, max = round(565.616 * 1.12) = 633
        """
        result = engine.calculate(_ftl(cargo_weight_kg=3000), distance_km=300)
        base = 300 * 1.43 * 0.96 * 1.0 + 80
        with_fuel = base * 1.15
        assert result["success"] is True
        assert result["min_price"] == round(with_fuel * 0.88)
        assert result["max_price"] == round(with_fuel * 1.12)

    def test_ftl_medium_weight_multiplier(self, engine):
        """
        10000 kg (medium bracket, mult=0.98), 300 km:
        base = 300 * 1.43 * 0.98 + 80 = 420.42 + 80 = 500.42
        """
        result = engine.calculate(_ftl(cargo_weight_kg=10000), distance_km=300)
        base = 300 * 1.43 * 0.98 * 1.0 + 80
        with_fuel = base * 1.15
        assert result["success"] is True
        assert result["min_price"] == round(with_fuel * 0.88)
        assert result["max_price"] == round(with_fuel * 1.12)

    def test_ftl_heavy_weight_multiplier(self, engine):
        """
        20000 kg (heavy bracket, mult=1.00), 300 km:
        base = 300 * 1.43 * 1.00 + 80 = 429 + 80 = 509
        """
        result = engine.calculate(_ftl(cargo_weight_kg=20000), distance_km=300)
        base = 300 * 1.43 * 1.00 * 1.0 + 80
        with_fuel = base * 1.15
        assert result["success"] is True
        assert result["min_price"] == round(with_fuel * 0.88)
        assert result["max_price"] == round(with_fuel * 1.12)

    def test_ftl_refrigerated_multiplier(self, engine):
        """refrigerated multiplier 1.35 on top of weight multiplier."""
        result = engine.calculate(
            _ftl(cargo_weight_kg=10000, truck_type="refrigerated"),
            distance_km=300,
        )
        base = 300 * 1.43 * 0.98 * 1.35 + 80
        with_fuel = base * 1.15
        assert result["success"] is True
        assert result["min_price"] == round(with_fuel * 0.88)
        assert result["max_price"] == round(with_fuel * 1.12)

    def test_ftl_flatbed_multiplier(self, engine):
        """flatbed multiplier 1.20."""
        result = engine.calculate(
            _ftl(cargo_weight_kg=10000, truck_type="flatbed"),
            distance_km=300,
        )
        base = 300 * 1.43 * 0.98 * 1.20 + 80
        with_fuel = base * 1.15
        assert result["success"] is True
        assert result["min_price"] == round(with_fuel * 0.88)
        assert result["max_price"] == round(with_fuel * 1.12)

    def test_ftl_pickup_drop_surcharge_always_added(self, engine):
        """Pickup/drop 80 EUR should be in base_price."""
        result = engine.calculate(_ftl(cargo_weight_kg=10000), distance_km=300)
        base_without_pickup = 300 * 1.43 * 0.98 * 1.0
        assert result["breakdown"]["base_price"] == pytest.approx(
            base_without_pickup + 80, abs=0.01
        )

    def test_ftl_international_uses_international_rate(self, engine):
        """International uses ftl_eur_per_km=1.60 instead of domestic 1.43."""
        result = engine.calculate(
            _ftl(destination_country="RO", destination="Bucharest",
                 cargo_weight_kg=10000),
            distance_km=390,
        )
        base = 390 * 1.60 * 0.98 * 1.0 + 80
        with_fuel = base * 1.15
        assert result["success"] is True
        assert result["min_price"] == round(with_fuel * 0.88)


# ---------------------------------------------------------------------------
# LTL — chargeable m² logic (palletised)
# ---------------------------------------------------------------------------

class TestLTLPalletised:

    def test_user_example_1_pallet_700kg(self, engine):
        """
        User example: 1 euro pallet, 700 kg
        actual_m2 = 1 * 0.96 = 0.96
        weight_equiv = 700 / 500 = 1.4
        chargeable = max(0.96, 1.4) = 1.4 (weight wins)
        base = 1.4 * 0.075 * 300 + 60 = 31.5 + 60 = 91.5
        """
        result = engine.calculate(
            _ltl(num_pallets=1, total_weight_kg=700),
            distance_km=300,
        )
        base = 1.4 * 0.075 * 300 + 60
        with_fuel = base * 1.15
        assert result["success"] is True
        assert result["min_price"] == round(with_fuel * 0.88)
        assert result["max_price"] == round(with_fuel * 1.12)

    def test_user_example_1_pallet_400kg(self, engine):
        """
        User example: 1 euro pallet, 400 kg
        actual_m2 = 0.96
        weight_equiv = 400 / 500 = 0.8
        chargeable = max(0.96, 0.8) = 0.96 (area wins)
        base = 0.96 * 0.075 * 300 + 60 = 21.6 + 60 = 81.6
        """
        result = engine.calculate(
            _ltl(num_pallets=1, total_weight_kg=400),
            distance_km=300,
        )
        base = 0.96 * 0.075 * 300 + 60
        with_fuel = base * 1.15
        assert result["success"] is True
        assert result["min_price"] == round(with_fuel * 0.88)
        assert result["max_price"] == round(with_fuel * 1.12)

    def test_user_example_5_pallets_3000kg(self, engine):
        """
        User example: 5 euro pallets, 3000 kg
        actual_m2 = 5 * 0.96 = 4.8
        weight_equiv = 3000 / 500 = 6.0
        chargeable = max(4.8, 6.0) = 6.0 (weight wins)
        base = 6.0 * 0.075 * 300 + 60 = 135 + 60 = 195
        """
        result = engine.calculate(
            _ltl(num_pallets=5, total_weight_kg=3000),
            distance_km=300,
        )
        base = 6.0 * 0.075 * 300 + 60
        with_fuel = base * 1.15
        assert result["success"] is True
        assert result["min_price"] == round(with_fuel * 0.88)
        assert result["max_price"] == round(with_fuel * 1.12)

    def test_area_wins_over_weight(self, engine):
        """Many pallets, low weight -> area-based m² wins."""
        result = engine.calculate(
            _ltl(num_pallets=10, total_weight_kg=500),
            distance_km=300,
        )
        actual_m2 = 10 * 0.96  # 9.6
        weight_m2 = 500 / 500  # 1.0
        chargeable = max(actual_m2, weight_m2)  # 9.6
        base = chargeable * 0.075 * 300 + 60
        with_fuel = base * 1.15
        assert result["success"] is True
        assert result["min_price"] == round(with_fuel * 0.88)

    def test_industrial_pallet_uses_larger_area(self, engine):
        """Industrial pallets: 1.20 m² instead of 0.96 m²."""
        result = engine.calculate(
            _ltl(num_pallets=5, total_weight_kg=1000, pallet_type="industrial"),
            distance_km=300,
        )
        actual_m2 = 5 * 1.20  # 6.0
        weight_m2 = 1000 / 500  # 2.0
        chargeable = max(actual_m2, weight_m2)  # 6.0
        base = chargeable * 0.075 * 300 + 60
        with_fuel = base * 1.15
        assert result["success"] is True
        assert result["min_price"] == round(with_fuel * 0.88)

    def test_ltl_pickup_drop_surcharge(self, engine):
        """Pickup/drop 60 EUR should be in base_price."""
        result = engine.calculate(
            _ltl(num_pallets=1, total_weight_kg=400),
            distance_km=300,
        )
        base_without_pickup = 0.96 * 0.075 * 300
        assert result["breakdown"]["base_price"] == pytest.approx(
            base_without_pickup + 60, abs=0.01
        )


# ---------------------------------------------------------------------------
# LTL — non-pallet mode
# ---------------------------------------------------------------------------

class TestLTLNonPallet:

    def test_nonpallet_area_wins(self, engine):
        """
        240x160 cm = 2.4m * 1.6m = 3.84 m²
        weight_equiv = 500 / 500 = 1.0
        chargeable = 3.84 (area wins)
        base = 3.84 * 0.075 * 300 * 1.15 + 60 = 99.36 + 60 = 159.36
        """
        result = engine.calculate(
            _ltl(
                total_weight_kg=500,
                non_pallet_cargo=True,
                cargo_length_cm=240,
                cargo_width_cm=160,
            ),
            distance_km=300,
        )
        actual_m2 = 2.4 * 1.6  # 3.84
        chargeable = max(actual_m2, 500 / 500)
        base = chargeable * 0.075 * 300 * 1.15 + 60
        with_fuel = base * 1.15
        assert result["success"] is True
        assert result["min_price"] == round(with_fuel * 0.88)

    def test_nonpallet_weight_wins(self, engine):
        """
        100x80 cm = 1.0m * 0.8m = 0.80 m²
        weight_equiv = 2000 / 500 = 4.0
        chargeable = 4.0 (weight wins)
        base = 4.0 * 0.075 * 300 * 1.15 + 60
        """
        result = engine.calculate(
            _ltl(
                total_weight_kg=2000,
                non_pallet_cargo=True,
                cargo_length_cm=100,
                cargo_width_cm=80,
            ),
            distance_km=300,
        )
        chargeable = max(0.80, 4.0)  # 4.0
        base = chargeable * 0.075 * 300 * 1.15 + 60
        with_fuel = base * 1.15
        assert result["success"] is True
        assert result["min_price"] == round(with_fuel * 0.88)

    def test_nonpallet_multiplier_applied(self, engine):
        """Non-pallet base should be 1.15× higher than equivalent pallet."""
        # Same area and weight, compare pallet vs non-pallet
        pallet_result = engine.calculate(
            _ltl(num_pallets=1, total_weight_kg=400),
            distance_km=300,
        )
        nonpallet_result = engine.calculate(
            _ltl(
                total_weight_kg=400,
                non_pallet_cargo=True,
                cargo_length_cm=120,
                cargo_width_cm=80,
            ),
            distance_km=300,
        )
        # Both have same chargeable_m2 = 0.96 (area from 1.2x0.8)
        # Non-pallet should have higher price due to 1.15x multiplier
        assert nonpallet_result["min_price"] > pallet_result["min_price"]


# ---------------------------------------------------------------------------
# Express surcharge
# ---------------------------------------------------------------------------

class TestExpressSurcharge:

    def test_express_surcharge_applied_for_fixed_date(self, engine):
        """Fixed date adds 25% express surcharge on top of fuel."""
        flex = engine.calculate(_ftl(date_flexibility="flexible"), distance_km=300)
        fixed = engine.calculate(_ftl(date_flexibility="fixed"), distance_km=300)

        assert flex["success"] is True
        assert fixed["success"] is True

        flex_mid = (flex["min_price"] + flex["max_price"]) / 2
        fixed_mid = (fixed["min_price"] + fixed["max_price"]) / 2
        assert fixed_mid == pytest.approx(flex_mid * 1.25, rel=0.01)

    def test_no_express_surcharge_when_flexible(self, engine):
        result = engine.calculate(_ftl(date_flexibility="flexible"), distance_km=300)
        assert result["breakdown"]["express_surcharge"] == 0


# ---------------------------------------------------------------------------
# Response format
# ---------------------------------------------------------------------------

class TestResponseFormat:

    def test_success_response_required_fields(self, engine):
        result = engine.calculate(_ftl(), distance_km=300)
        assert result["success"] is True
        for key in ("min_price", "max_price", "currency", "breakdown",
                    "disclaimer", "disclaimer_bg"):
            assert key in result, f"Missing key: {key}"
        assert result["currency"] == "EUR"

    def test_breakdown_includes_distance(self, engine):
        result = engine.calculate(_ftl(), distance_km=300)
        assert result["breakdown"]["distance_km"] == 300

    def test_breakdown_fields(self, engine):
        result = engine.calculate(_ftl(), distance_km=300)
        bd = result["breakdown"]
        for key in ("base_price", "fuel_surcharge", "express_surcharge",
                    "dangerous_goods_surcharge", "distance_km"):
            assert key in bd, f"Missing breakdown key: {key}"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:

    def test_weight_at_bracket_boundary_5000(self, engine):
        """5000 kg is in medium bracket (5000 <= w < 15000), mult=0.98."""
        result = engine.calculate(_ftl(cargo_weight_kg=5000), distance_km=300)
        base = 300 * 1.43 * 0.98 + 80
        with_fuel = base * 1.15
        assert result["min_price"] == round(with_fuel * 0.88)

    def test_weight_at_bracket_boundary_15000(self, engine):
        """15000 kg is in heavy bracket (>=15000), mult=1.00."""
        result = engine.calculate(_ftl(cargo_weight_kg=15000), distance_km=300)
        base = 300 * 1.43 * 1.00 + 80
        with_fuel = base * 1.15
        assert result["min_price"] == round(with_fuel * 0.88)

    def test_single_pallet_boundary(self, engine):
        result = engine.calculate(
            _ltl(num_pallets=1, total_weight_kg=100),
            distance_km=300,
        )
        assert result["success"] is True
        assert result["min_price"] > 0

    def test_33_pallets_boundary(self, engine):
        result = engine.calculate(
            _ltl(num_pallets=33, total_weight_kg=5000),
            distance_km=300,
        )
        assert result["success"] is True

    def test_no_pallet_type_defaults_to_eur(self, engine):
        data = _ltl()
        data.pop("pallet_type", None)
        result = engine.calculate(data, distance_km=300)
        assert result["success"] is True

    def test_no_truck_type_defaults_to_standard(self, engine):
        data = _ftl()
        data.pop("truck_type", None)
        result = engine.calculate(data, distance_km=300)
        expected = engine.calculate(_ftl(truck_type="standard"), distance_km=300)
        assert result["min_price"] == expected["min_price"]

    def test_short_distance(self, engine):
        """Very short distance still produces a valid price (pickup/drop dominates)."""
        result = engine.calculate(_ftl(cargo_weight_kg=10000), distance_km=10)
        assert result["success"] is True
        # Base ≈ 10*1.43*0.98+80 ≈ 94, still positive
        assert result["min_price"] > 0

    def test_ltl_international_rate(self, engine):
        """International LTL uses 0.090 rate instead of 0.075."""
        result = engine.calculate(
            _ltl(destination_country="RO", destination="Bucharest",
                 num_pallets=5, total_weight_kg=3000),
            distance_km=390,
        )
        chargeable = max(5 * 0.96, 3000 / 500)  # max(4.8, 6.0) = 6.0
        base = 6.0 * 0.090 * 390 + 60
        with_fuel = base * 1.15
        assert result["success"] is True
        assert result["min_price"] == round(with_fuel * 0.88)
