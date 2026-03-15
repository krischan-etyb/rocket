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
    # OpenRouteService API helpers
    # ------------------------------------------------------------------

    def _fetch_from_api(
        self,
        origin_city: str,
        origin_country: str,
        dest_city: str,
        dest_country: str,
    ) -> float | None:
        """Geocode both cities and fetch driving distance via ORS."""
        if requests is None:
            logger.warning("requests library not installed, cannot call ORS API.")
            return None

        if not self._api_key:
            logger.warning("ORS_API_KEY not set, cannot call ORS API.")
            return None

        origin_coords = self._geocode(origin_city, origin_country)
        if origin_coords is None:
            return None

        dest_coords = self._geocode(dest_city, dest_country)
        if dest_coords is None:
            return None

        return self._get_route_distance(origin_coords, dest_coords)

    def _geocode(
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

    def _get_route_distance(
        self,
        origin: tuple[float, float],
        dest: tuple[float, float],
    ) -> float | None:
        """Return driving distance in km between two coordinate pairs."""
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
