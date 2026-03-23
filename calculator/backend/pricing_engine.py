"""
Pricing engine for Rocket Logistic transport calculator.

Loads a prices.json configuration at instantiation and exposes a single
``calculate(data, distance_km)`` method that returns a price estimate or a
``no_rate`` sentinel when the requested route has no configured rate.

Pricing model (v2 – distance-based):

FTL:
    base = distance_km × ftl_rate_per_km × weight_multiplier × truck_multiplier
    total = base + pickup_drop_surcharge (80 EUR)

LTL (palletised):
    chargeable_m2 = max(num_pallets × pallet_area, weight / density_factor)
    base = chargeable_m2 × ltl_rate_per_m2_per_km × distance_km
    total = base + pickup_drop_surcharge (60 EUR)

LTL (non-palletised):
    chargeable_m2 = max(length_m × width_m, weight / density_factor)
    base = chargeable_m2 × ltl_rate_per_m2_per_km × distance_km × non_pallet_multiplier
    total = base + pickup_drop_surcharge (60 EUR)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PricingEngine:
    """Calculate transport price estimates from a prices.json configuration."""

    def __init__(self, prices_path: str | Path) -> None:
        self._path = Path(prices_path)
        if not self._path.is_file():
            raise FileNotFoundError(f"Prices file not found: {prices_path}")
        self._last_mtime: float = 0.0
        self._load_prices()

    def _load_prices(self) -> None:
        """Load or reload prices from disk."""
        with self._path.open(encoding="utf-8") as fh:
            self._prices: dict[str, Any] = json.load(fh)

        self._settings: dict[str, Any] = self._prices["settings"]
        self._surcharges: dict[str, Any] = self._prices["surcharges"]
        self._truck_multipliers: dict[str, float] = self._prices["truck_type_multipliers"]
        self._pickup_drop: dict[str, float] = self._prices["pickup_drop_surcharge"]
        self._weight_brackets: list[dict[str, Any]] = self._prices["ftl_weight_multipliers"]
        self._ltl_config: dict[str, Any] = self._prices["ltl_config"]
        self._rates: dict[str, Any] = self._prices["rates"]
        self._country_multipliers: dict[str, Any] = self._prices.get("country_multipliers", {})
        self._city_multipliers: dict[str, float] = self._prices.get("city_multipliers", {})
        self._last_mtime = self._path.stat().st_mtime
        logger.info("Prices loaded from %s", self._path)

    def _reload_if_changed(self) -> None:
        """Reload prices.json if the file has been modified."""
        try:
            current_mtime = self._path.stat().st_mtime
            if current_mtime != self._last_mtime:
                self._load_prices()
        except OSError:
            pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def calculate(self, data: dict[str, Any], distance_km: float) -> dict[str, Any]:
        """Return a price estimate for the supplied shipment data.

        Parameters
        ----------
        data:
            Shipment parameters (service_type, weights, pallets, etc.)
        distance_km:
            Road distance between origin and destination in kilometres.
        """
        self._reload_if_changed()
        service_type: str = data.get("service_type", "LTL").upper()
        route_type = self._derive_route_type(data)

        if service_type == "LTL":
            result = self._calculate_ltl(data, distance_km, route_type)
        else:
            result = self._calculate_ftl(data, distance_km, route_type)

        if result.get("no_rate"):
            return {
                "success": True,
                "no_rate": True,
                "message": "Contact us for a custom quote",
                "message_bg": "Свържете се с нас за индивидуална оферта",
            }

        base_price: float = result["base_price"]
        country_mult = 1.0
        if route_type == "international":
            country_mult = self._get_country_multiplier(
                data.get("origin_country", ""),
                data.get("destination_country", ""),
            )
            base_price *= country_mult

        city_mult = self._get_city_multiplier(
            data.get("origin_city", ""),
            data.get("destination", ""),
        )
        base_price *= city_mult

        date_flexibility: str = data.get("date_flexibility", "flexible")

        # --- surcharges ---
        fuel_pct: float = self._surcharges["fuel_pct"]
        express_pct: float = self._surcharges["express_pct"]
        price_range_pct: float = self._settings["price_range_pct"]

        fuel_surcharge = base_price * (fuel_pct / 100)
        with_fuel = base_price + fuel_surcharge

        express_surcharge = 0.0
        if date_flexibility == "fixed":
            express_surcharge = with_fuel * (express_pct / 100)

        with_surcharges = with_fuel + express_surcharge

        min_price = round(with_surcharges * (1 - price_range_pct / 100))
        max_price = round(with_surcharges * (1 + price_range_pct / 100))

        return {
            "success": True,
            "min_price": min_price,
            "max_price": max_price,
            "currency": self._settings["currency"],
            "breakdown": {
                "base_price": round(base_price, 2),
                "fuel_surcharge": round(fuel_surcharge, 2),
                "express_surcharge": round(express_surcharge, 2),
                "dangerous_goods_surcharge": 0,
                "country_multiplier": round(country_mult, 4),
                "city_multiplier": round(city_mult, 4),
                "distance_km": round(distance_km, 1),
            },
            "disclaimer": "Indicative estimate only. Final price subject to confirmation.",
            "disclaimer_bg": "Само приблизителна оценка. Крайната цена подлежи на потвърждение.",
        }

    # ------------------------------------------------------------------
    # Route derivation
    # ------------------------------------------------------------------

    @staticmethod
    def _derive_route_type(data: dict[str, Any]) -> str:
        if (
            data.get("origin_country", "").upper() == "BG"
            and data.get("destination_country", "").upper() == "BG"
        ):
            return "domestic"
        return "international"

    def _get_country_multiplier(self, origin: str, destination: str) -> float:
        """Return import or export multiplier based on BG's route direction.

        BG → foreign country (export): use destination's export multiplier.
        Foreign country → BG (import): use origin's import multiplier.
        """
        origin = origin.upper()
        destination = destination.upper()
        if origin == "BG":
            return float(self._country_multipliers.get(destination, {}).get("export", 1.0))
        return float(self._country_multipliers.get(origin, {}).get("import", 1.0))

    def _get_city_multiplier(self, origin_city: str, destination_city: str) -> float:
        """Return combined multiplier for origin and destination cities.

        Both multipliers are applied multiplicatively — if both cities carry
        a surcharge, both are included.
        """
        origin_mult = 1.0
        dest_mult = 1.0
        for city, mult in self._city_multipliers.items():
            if city.startswith("_"):
                continue
            if origin_city and city.lower() == origin_city.lower():
                origin_mult = float(mult)
            if destination_city and city.lower() == destination_city.lower():
                dest_mult = float(mult)
        return origin_mult * dest_mult

    # ------------------------------------------------------------------
    # FTL
    # ------------------------------------------------------------------

    def _calculate_ftl(
        self,
        data: dict[str, Any],
        distance_km: float,
        route_type: str,
    ) -> dict[str, Any]:
        rate_per_km: float = self._rates[route_type]["ftl_eur_per_km"]
        truck_type: str = data.get("truck_type", "standard")
        truck_mult: float = self._truck_multipliers.get(truck_type, 1.0)
        weight_kg: float = float(data.get("cargo_weight_kg", 0))
        weight_mult: float = self._get_weight_multiplier(weight_kg)

        pickup_drop: float = self._pickup_drop["ftl_eur"]

        base_price = distance_km * rate_per_km * weight_mult * truck_mult + pickup_drop
        return {"base_price": base_price}

    def _get_weight_multiplier(self, weight_kg: float) -> float:
        """Look up the FTL weight multiplier for the given weight."""
        for bracket in self._weight_brackets:
            min_kg = bracket["min_kg"]
            max_kg = bracket["max_kg"]  # None means unlimited
            if weight_kg >= min_kg and (max_kg is None or weight_kg < max_kg):
                return float(bracket["multiplier"])
        # Default to 1.0 if no bracket matches
        return 1.0

    # ------------------------------------------------------------------
    # LTL
    # ------------------------------------------------------------------

    def _calculate_ltl(
        self,
        data: dict[str, Any],
        distance_km: float,
        route_type: str,
    ) -> dict[str, Any]:
        rate_per_m2_km: float = self._rates[route_type]["ltl_eur_per_m2_per_km"]
        density_factor: float = self._ltl_config["density_factor_kg_per_m2"]
        total_weight_kg: float = float(data.get("total_weight_kg", 0))
        non_pallet: bool = bool(data.get("non_pallet_cargo", False))

        if non_pallet:
            # Non-palletised: dimensions in cm from frontend, convert to m
            cargo_length_cm: float = float(data.get("cargo_length_cm", 0))
            cargo_width_cm: float = float(data.get("cargo_width_cm", 0))
            actual_m2 = (cargo_length_cm / 100) * (cargo_width_cm / 100)
            non_pallet_mult: float = self._ltl_config["non_pallet_multiplier"]
        else:
            # Palletised: use pallet area based on type
            pallet_type: str = data.get("pallet_type", "eur")
            pallet_areas = self._ltl_config["pallet_dimensions_m2"]
            pallet_area: float = pallet_areas.get(pallet_type, pallet_areas["eur"])
            num_pallets: int = int(data.get("num_pallets", 1))
            actual_m2 = num_pallets * pallet_area
            non_pallet_mult = 1.0

        # Chargeable m²: the greater of actual area or weight-equivalent area
        weight_equiv_m2 = total_weight_kg / density_factor
        chargeable_m2 = max(actual_m2, weight_equiv_m2)

        pickup_drop: float = self._pickup_drop["ltl_eur"]

        base_price = (
            chargeable_m2 * rate_per_m2_km * distance_km * non_pallet_mult
            + pickup_drop
        )
        return {"base_price": base_price}
