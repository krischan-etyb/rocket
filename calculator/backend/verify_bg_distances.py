"""
Verify and fix BG-to-BG distances in distances_cache.json using ORS API.

Rate limits: 35 requests/minute, 1600 requests/24 hours.
Saves progress so it can be re-run to continue where it left off.

Usage:
    python verify_bg_distances.py [--dry-run] [--threshold 10]

Options:
    --dry-run       Report mismatches without updating the cache file
    --threshold N   Only flag distances differing by more than N km (default: 10)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: 'requests' library required. Install with: pip install requests")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent
CACHE_FILE = SCRIPT_DIR / "distances_cache.json"
GEOCODE_CACHE_FILE = SCRIPT_DIR / "bg_geocode_cache.json"
PROGRESS_FILE = SCRIPT_DIR / "bg_verify_progress.json"
REPORT_FILE = SCRIPT_DIR / "bg_verify_report.json"

ORS_GEOCODE_URL = "https://api.openrouteservice.org/geocode/search"
ORS_DIRECTIONS_URL = "https://api.openrouteservice.org/v2/directions/driving-hgv"

REQUESTS_PER_MINUTE = 35
REQUESTS_PER_DAY = 1600
MISMATCH_THRESHOLD_KM = 10  # default; overridable via --threshold

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("verify_bg")

# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------

class RateLimiter:
    """Simple token-bucket style limiter for per-minute and per-day caps."""

    def __init__(self, per_minute: int, per_day: int) -> None:
        self.per_minute = per_minute
        self.per_day = per_day
        self._minute_timestamps: list[float] = []
        self._day_count = 0

    def set_day_count(self, count: int) -> None:
        self._day_count = count

    @property
    def day_count(self) -> int:
        return self._day_count

    def wait_if_needed(self) -> bool:
        """Block until a request slot is available. Returns False if daily cap hit."""
        if self._day_count >= self.per_day:
            return False

        now = time.time()
        # Purge timestamps older than 60s
        self._minute_timestamps = [t for t in self._minute_timestamps if now - t < 60]

        if len(self._minute_timestamps) >= self.per_minute:
            wait = 60 - (now - self._minute_timestamps[0]) + 0.1
            log.info("Rate limit: waiting %.1fs for next minute window...", wait)
            time.sleep(wait)
            now = time.time()
            self._minute_timestamps = [t for t in self._minute_timestamps if now - t < 60]

        self._minute_timestamps.append(now)
        self._day_count += 1
        return True


# ---------------------------------------------------------------------------
# ORS API helpers
# ---------------------------------------------------------------------------

def geocode_city(city: str, api_key: str, limiter: RateLimiter) -> tuple[float, float] | None:
    """Return (longitude, latitude) for a Bulgarian city via ORS geocode."""
    if not limiter.wait_if_needed():
        log.warning("Daily request limit reached during geocoding.")
        return None

    params = {
        "api_key": api_key,
        "text": f"{city}, Bulgaria",
        "size": 1,
        "layers": "locality,county",
    }
    try:
        resp = requests.get(ORS_GEOCODE_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        features = data.get("features", [])
        if not features:
            log.warning("No geocode result for: %s", city)
            return None
        coords = features[0]["geometry"]["coordinates"]
        log.info("Geocoded %-25s -> [%.4f, %.4f]", city, coords[0], coords[1])
        return (coords[0], coords[1])
    except Exception as exc:
        log.error("Geocode failed for %s: %s", city, exc)
        return None


def get_driving_distance(
    origin: tuple[float, float],
    dest: tuple[float, float],
    api_key: str,
    limiter: RateLimiter,
) -> float | None:
    """Return driving distance in km between two coordinate pairs via ORS."""
    if not limiter.wait_if_needed():
        log.warning("Daily request limit reached during directions query.")
        return None

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
    }
    body = {
        "coordinates": [list(origin), list(dest)],
        "units": "km",
    }
    try:
        resp = requests.post(ORS_DIRECTIONS_URL, json=body, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        distance_km = data["routes"][0]["summary"]["distance"]
        return round(distance_km, 1)
    except Exception as exc:
        log.error("Directions failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Progress management
# ---------------------------------------------------------------------------

def load_json(path: Path) -> dict:
    if path.is_file():
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_json(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Verify BG distances against ORS API")
    parser.add_argument("--dry-run", action="store_true", help="Don't update cache file")
    parser.add_argument("--threshold", type=float, default=MISMATCH_THRESHOLD_KM,
                        help=f"Mismatch threshold in km (default: {MISMATCH_THRESHOLD_KM})")
    args = parser.parse_args()

    # Load API key
    from dotenv import load_dotenv
    env_path = SCRIPT_DIR / ".env"
    if env_path.is_file():
        load_dotenv(env_path)
    api_key = os.getenv("ORS_API_KEY", "")
    if not api_key:
        log.error("ORS_API_KEY not found in .env or environment. Aborting.")
        sys.exit(1)

    # Load distances cache
    cache = load_json(CACHE_FILE)
    bg_entries = {k: v for k, v in cache.items() if k.endswith("|bg|bg")}
    log.info("Loaded %d bg|bg entries from cache.", len(bg_entries))

    # Build unique pairs (sorted city names to deduplicate a->b and b->a)
    seen: set[tuple[str, str]] = set()
    unique_pairs: list[tuple[str, str]] = []
    for key in bg_entries:
        parts = key.split("|")
        pair = tuple(sorted([parts[0], parts[1]]))
        if pair not in seen:
            seen.add(pair)
            unique_pairs.append(pair)
    unique_pairs.sort()
    log.info("Found %d unique BG city pairs to verify.", len(unique_pairs))

    # Collect unique cities
    cities = sorted({c for pair in unique_pairs for c in pair})
    log.info("Found %d unique BG cities.", len(cities))

    # Load geocode cache
    geocode_cache: dict[str, list[float]] = load_json(GEOCODE_CACHE_FILE)

    # Load progress
    progress = load_json(PROGRESS_FILE)
    verified_pairs: set[str] = set(progress.get("verified", []))
    day_requests = progress.get("day_requests", 0)
    day_date = progress.get("day_date", "")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Reset daily counter if it's a new day
    if day_date != today:
        day_requests = 0
        day_date = today
        log.info("New day detected, resetting daily request counter.")

    limiter = RateLimiter(REQUESTS_PER_MINUTE, REQUESTS_PER_DAY)
    limiter.set_day_count(day_requests)

    # Load or create report
    report: dict = load_json(REPORT_FILE)
    if "mismatches" not in report:
        report["mismatches"] = []
    if "verified_ok" not in report:
        report["verified_ok"] = 0
    if "errors" not in report:
        report["errors"] = []

    def save_progress_now() -> None:
        progress_data = {
            "verified": sorted(verified_pairs),
            "day_requests": limiter.day_count,
            "day_date": day_date,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        save_json(PROGRESS_FILE, progress_data)
        save_json(GEOCODE_CACHE_FILE, geocode_cache)
        save_json(REPORT_FILE, report)

    # Phase 1: Geocode all cities
    log.info("=== Phase 1: Geocoding %d cities ===", len(cities))
    cities_to_geocode = [c for c in cities if c not in geocode_cache]
    if cities_to_geocode:
        log.info("%d cities need geocoding.", len(cities_to_geocode))
    else:
        log.info("All cities already geocoded.")

    for city in cities_to_geocode:
        if limiter.day_count >= REQUESTS_PER_DAY:
            log.warning("Daily limit reached during geocoding. Re-run tomorrow.")
            save_progress_now()
            sys.exit(0)

        coords = geocode_city(city, api_key, limiter)
        if coords is not None:
            geocode_cache[city] = list(coords)
        else:
            log.warning("Could not geocode '%s', pairs with this city will be skipped.", city)

        # Save progress periodically
        if limiter.day_count % 10 == 0:
            save_progress_now()

    save_progress_now()

    # Phase 2: Verify distances
    pairs_remaining = [p for p in unique_pairs if f"{p[0]}|{p[1]}" not in verified_pairs]
    log.info("=== Phase 2: Verifying %d remaining pairs (of %d total) ===",
             len(pairs_remaining), len(unique_pairs))

    mismatches_this_run = 0
    verified_this_run = 0

    for i, (city_a, city_b) in enumerate(pairs_remaining):
        if limiter.day_count >= REQUESTS_PER_DAY:
            log.warning("Daily limit reached after %d verifications this run. Re-run tomorrow.",
                        verified_this_run)
            break

        pair_key = f"{city_a}|{city_b}"

        # Check we have geocodes for both
        if city_a not in geocode_cache or city_b not in geocode_cache:
            log.warning("Skipping %s -> %s (missing geocode)", city_a, city_b)
            report["errors"].append({
                "pair": pair_key,
                "reason": "missing geocode",
            })
            verified_pairs.add(pair_key)
            continue

        coords_a = tuple(geocode_cache[city_a])
        coords_b = tuple(geocode_cache[city_b])

        # Get ORS distance
        ors_distance = get_driving_distance(coords_a, coords_b, api_key, limiter)
        if ors_distance is None:
            if limiter.day_count >= REQUESTS_PER_DAY:
                log.warning("Daily limit hit. Re-run tomorrow.")
                break
            report["errors"].append({
                "pair": pair_key,
                "reason": "API error",
            })
            verified_pairs.add(pair_key)
            continue

        # Compare with cached values (both directions)
        key_ab = f"{city_a}|{city_b}|bg|bg"
        key_ba = f"{city_b}|{city_a}|bg|bg"
        cached_ab = cache.get(key_ab)
        cached_ba = cache.get(key_ba)

        # Use whichever exists for comparison
        cached_val = cached_ab if cached_ab is not None else cached_ba
        if cached_val is None:
            log.warning("No cached value for %s (unexpected)", pair_key)
            verified_pairs.add(pair_key)
            continue

        diff = abs(ors_distance - cached_val)
        if diff > args.threshold:
            mismatches_this_run += 1
            log.warning(
                "MISMATCH: %-25s -> %-25s  cached=%.1f  ORS=%.1f  diff=%.1f km",
                city_a, city_b, cached_val, ors_distance, diff,
            )
            report["mismatches"].append({
                "city_a": city_a,
                "city_b": city_b,
                "cached_km": cached_val,
                "ors_km": ors_distance,
                "diff_km": round(diff, 1),
            })

            if not args.dry_run:
                # Update both directions in cache
                cache[key_ab] = ors_distance
                cache[key_ba] = ors_distance
                log.info("  -> Updated cache: %s and %s = %.1f km", key_ab, key_ba, ors_distance)
        else:
            log.info(
                "OK: %-25s -> %-25s  cached=%.1f  ORS=%.1f  diff=%.1f",
                city_a, city_b, cached_val, ors_distance, diff,
            )
            report["verified_ok"] += 1

        verified_pairs.add(pair_key)
        verified_this_run += 1

        # Save progress every 10 pairs
        if verified_this_run % 10 == 0:
            save_progress_now()
            if not args.dry_run:
                save_json(CACHE_FILE, cache)
            log.info("Progress: %d/%d pairs verified this run. %d total. %d API calls today.",
                     verified_this_run, len(pairs_remaining), len(verified_pairs), limiter.day_count)

    # Final save
    save_progress_now()
    if not args.dry_run and mismatches_this_run > 0:
        save_json(CACHE_FILE, cache)

    # Summary
    total_verified = len(verified_pairs)
    total_remaining = len(unique_pairs) - total_verified
    log.info("=" * 60)
    log.info("RUN SUMMARY")
    log.info("  Verified this run:   %d", verified_this_run)
    log.info("  Mismatches found:    %d", mismatches_this_run)
    log.info("  Total verified:      %d / %d", total_verified, len(unique_pairs))
    log.info("  Remaining:           %d", total_remaining)
    log.info("  API calls today:     %d / %d", limiter.day_count, REQUESTS_PER_DAY)
    log.info("  Report saved to:     %s", REPORT_FILE)
    if total_remaining > 0:
        log.info("  -> Re-run this script tomorrow to continue.")
    else:
        log.info("  -> All pairs verified!")
    if args.dry_run:
        log.info("  (DRY RUN - no changes written to cache)")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
