"""
Distance lookup service for Rocket Logistic transport calculator.

Uses a hybrid approach:
1. Check pre-defined distances in prices.json
2. Check cached distances in distances_cache.json
3. Call OpenRouteService API as fallback (geocode + directions)
4. Cache successful API results for future use
"""

from __future__ import annotations

import json
import logging
import math
import os
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

# ISO-3166-1 alpha-2 → full country name for geocoding context
_COUNTRY_NAMES: dict[str, str] = {
    "BG": "Bulgaria",
    "RO": "Romania",
    "GR": "Greece",
    "DE": "Germany",
    "FR": "France",
    "IT": "Italy",
    "ES": "Spain",
    "NL": "Netherlands",
    "BE": "Belgium",
    "AT": "Austria",
    "PL": "Poland",
    "CZ": "Czech Republic",
    "HU": "Hungary",
    "RS": "Serbia",
    "MK": "North Macedonia",
    "TR": "Turkey",
    "HR": "Croatia",
    "SI": "Slovenia",
    "SK": "Slovakia",
}

_ORS_GEOCODE_URL = "https://api.openrouteservice.org/geocode/search"
_ORS_DIRECTIONS_URL = "https://api.openrouteservice.org/v2/directions/driving-hgv"

_GH_GEOCODE_URL = "https://graphhopper.com/api/1/geocode"
_GH_ROUTE_URL = "https://graphhopper.com/api/1/route"

# Typical road-to-straight-line ratio for European highways
_IDEAL_ROAD_RATIO = 1.3


def _haversine_km(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """Return straight-line distance in km between two (lat, lon) pairs."""
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _make_key(
    origin_city: str,
    dest_city: str,
    origin_country: str,
    dest_country: str,
) -> str:
    """Build a normalised cache key: ``city1|city2|cc1|cc2``."""
    return (
        f"{origin_city.lower().strip()}"
        f"|{dest_city.lower().strip()}"
        f"|{origin_country.lower().strip()}"
        f"|{dest_country.lower().strip()}"
    )


class DistanceService:
    """Resolve road distances (km) between two cities."""

    def __init__(
        self,
        predefined_distances: dict[str, float],
        cache_path: str | Path | None = None,
        api_key: str | None = None,
    ) -> None:
        self._predefined = predefined_distances
        self._cache_path = Path(cache_path) if cache_path else None
        self._api_key = api_key or os.getenv("ORS_API_KEY", "")
        self._gh_api_key = os.getenv("GRAPHHOPPER_API_KEY", "")
        self._cache: dict[str, float] = {}

        if self._cache_path and self._cache_path.is_file():
            try:
                with self._cache_path.open(encoding="utf-8") as fh:
                    self._cache = json.load(fh)
            except (json.JSONDecodeError, OSError):
                logger.warning("Could not load distance cache, starting fresh.")
                self._cache = {}

    def get_distance(
        self,
        origin_city: str,
        origin_country: str,
        dest_city: str,
        dest_country: str,
    ) -> float | None:
        """Return road distance in km, or ``None`` if unknown."""
        key = _make_key(origin_city, dest_city, origin_country, dest_country)

        # 1. Check predefined distances
        if key in self._predefined:
            return float(self._predefined[key])

        # 2. Check runtime cache
        if key in self._cache:
            return float(self._cache[key])

        # 3. Try API
        distance = self._fetch_from_api(
            origin_city, origin_country, dest_city, dest_country
        )
        if distance is not None:
            self._cache[key] = distance
            # Also cache the reverse direction
            reverse_key = _make_key(
                dest_city, origin_city, dest_country, origin_country
            )
            self._cache[reverse_key] = distance
            self._save_cache()
            return distance

        return None

    # ------------------------------------------------------------------
    # Cross-validated distance fetch (ORS + GraphHopper)
    # ------------------------------------------------------------------

    def _fetch_from_api(
        self,
        origin_city: str,
        origin_country: str,
        dest_city: str,
        dest_country: str,
    ) -> float | None:
        """Fetch distance from ORS and GraphHopper, cross-validate results."""
        if requests is None:
            logger.warning("requests library not installed, cannot call APIs.")
            return None

        ors_distance = self._fetch_ors(
            origin_city, origin_country, dest_city, dest_country
        )
        gh_distance = self._fetch_graphhopper(
            origin_city, origin_country, dest_city, dest_country
        )

        # If only one API returned a result, use it
        if ors_distance is not None and gh_distance is None:
            return ors_distance
        if gh_distance is not None and ors_distance is None:
            return gh_distance
        if ors_distance is None and gh_distance is None:
            return None

        # Both returned results — check agreement
        avg = (ors_distance + gh_distance) / 2
        diff_pct = abs(ors_distance - gh_distance) / avg * 100

        if diff_pct <= 10:
            # APIs agree within 10% — use ORS as primary
            return ors_distance

        # Disagreement > 10% — use haversine tiebreaker
        origin_coords = self._geocode_ors(origin_city, origin_country)
        dest_coords = self._geocode_ors(dest_city, dest_country)

        if origin_coords and dest_coords:
            straight_km = _haversine_km(
                origin_coords[1], origin_coords[0],
                dest_coords[1], dest_coords[0],
            )
        else:
            # Can't compute haversine — fall back to average
            logger.warning(
                "Cannot compute haversine for %s-%s, using average of ORS=%.1f / GH=%.1f",
                origin_city, dest_city, ors_distance, gh_distance,
            )
            return round((ors_distance + gh_distance) / 2, 1)

        if straight_km < 1:
            # Same city or too close — use ORS
            return ors_distance

        ors_ratio = ors_distance / straight_km
        gh_ratio = gh_distance / straight_km

        # Pick the distance whose ratio is closest to the ideal (1.3)
        ors_diff = abs(ors_ratio - _IDEAL_ROAD_RATIO)
        gh_diff = abs(gh_ratio - _IDEAL_ROAD_RATIO)

        if ors_diff <= gh_diff:
            chosen, chosen_name = ors_distance, "ORS"
        else:
            chosen, chosen_name = gh_distance, "GraphHopper"

        logger.warning(
            "Distance discrepancy >10%%: %s (%s) -> %s (%s) | "
            "ORS=%.1f km (ratio %.2f) | GH=%.1f km (ratio %.2f) | "
            "Haversine=%.1f km | Chose %s=%.1f km",
            origin_city, origin_country, dest_city, dest_country,
            ors_distance, ors_ratio, gh_distance, gh_ratio,
            straight_km, chosen_name, chosen,
        )

        return round(chosen, 1)

    # ------------------------------------------------------------------
    # ORS API helpers
    # ------------------------------------------------------------------

    def _fetch_ors(
        self,
        origin_city: str,
        origin_country: str,
        dest_city: str,
        dest_country: str,
    ) -> float | None:
        """Geocode + route via ORS. Returns distance in km or None."""
        if not self._api_key:
            logger.warning("ORS_API_KEY not set.")
            return None

        origin_coords = self._geocode_ors(origin_city, origin_country)
        if origin_coords is None:
            return None

        dest_coords = self._geocode_ors(dest_city, dest_country)
        if dest_coords is None:
            return None

        return self._route_ors(origin_coords, dest_coords)

    def _geocode_ors(
        self, city: str, country_code: str
    ) -> tuple[float, float] | None:
        """Return (longitude, latitude) for a city via ORS geocode."""
        country_name = _COUNTRY_NAMES.get(country_code.upper(), country_code)
        params: dict[str, Any] = {
            "api_key": self._api_key,
            "text": f"{city}, {country_name}",
            "size": 1,
            "layers": "locality,county",
        }

        try:
            resp = requests.get(
                _ORS_GEOCODE_URL, params=params, timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            features = data.get("features", [])
            if not features:
                logger.warning("ORS geocode: no results for %s, %s", city, country_name)
                return None
            coords = features[0]["geometry"]["coordinates"]
            return (coords[0], coords[1])  # (lon, lat)
        except Exception:
            logger.exception("ORS geocode failed for %s, %s", city, country_name)
            return None

    def _route_ors(
        self,
        origin: tuple[float, float],
        dest: tuple[float, float],
    ) -> float | None:
        """Return driving distance in km via ORS directions."""
        headers = {
            "Authorization": self._api_key,
            "Content-Type": "application/json",
        }
        body = {
            "coordinates": [list(origin), list(dest)],
            "units": "km",
        }

        try:
            resp = requests.post(
                _ORS_DIRECTIONS_URL,
                json=body,
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            distance_km = data["routes"][0]["summary"]["distance"]
            return round(distance_km, 1)
        except Exception:
            logger.exception("ORS directions failed")
            return None

    # ------------------------------------------------------------------
    # GraphHopper API helpers
    # ------------------------------------------------------------------

    def _fetch_graphhopper(
        self,
        origin_city: str,
        origin_country: str,
        dest_city: str,
        dest_country: str,
    ) -> float | None:
        """Geocode + route via GraphHopper. Returns distance in km or None."""
        if not self._gh_api_key:
            return None

        origin_coords = self._geocode_graphhopper(origin_city, origin_country)
        if origin_coords is None:
            return None

        dest_coords = self._geocode_graphhopper(dest_city, dest_country)
        if dest_coords is None:
            return None

        return self._route_graphhopper(origin_coords, dest_coords)

    def _geocode_graphhopper(
        self, city: str, country_code: str
    ) -> tuple[float, float] | None:
        """Return (longitude, latitude) for a city via GraphHopper geocode."""
        country_name = _COUNTRY_NAMES.get(country_code.upper(), country_code)
        params: dict[str, Any] = {
            "key": self._gh_api_key,
            "q": f"{city}, {country_name}",
            "limit": 1,
        }

        try:
            resp = requests.get(
                _GH_GEOCODE_URL, params=params, timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            hits = data.get("hits", [])
            if not hits:
                logger.warning("GH geocode: no results for %s, %s", city, country_name)
                return None
            point = hits[0]["point"]
            return (point["lng"], point["lat"])  # (lon, lat)
        except Exception:
            logger.exception("GH geocode failed for %s, %s", city, country_name)
            return None

    def _route_graphhopper(
        self,
        origin: tuple[float, float],
        dest: tuple[float, float],
    ) -> float | None:
        """Return driving distance in km via GraphHopper routing."""
        params: dict[str, Any] = {
            "key": self._gh_api_key,
            "point": [
                f"{origin[1]},{origin[0]}",  # lat,lon
                f"{dest[1]},{dest[0]}",
            ],
            "vehicle": "truck",
            "calc_points": "false",
        }

        try:
            resp = requests.get(
                _GH_ROUTE_URL, params=params, timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            distance_m = data["paths"][0]["distance"]
            return round(distance_m / 1000, 1)
        except Exception:
            logger.exception("GH routing failed")
            return None

    def _save_cache(self) -> None:
        """Persist the runtime cache to disk."""
        if not self._cache_path:
            return
        try:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            with self._cache_path.open("w", encoding="utf-8") as fh:
                json.dump(self._cache, fh, indent=2, ensure_ascii=False)
        except OSError:
            logger.exception("Failed to save distance cache")
