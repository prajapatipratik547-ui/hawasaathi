"""Official CPCB monitoring stations, via the OpenAQ v3 API (needs a free OPENAQ_API_KEY).

nearest_station() returns the 24-hour PM2.5/PM10 averages at the closest CPCB station, or None
when there's no fresh station nearby, no key, or OpenAQ is slow or down. Callers then use the
Open-Meteo estimate, so this never blocks a reply for long.
"""
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

import httpx

BASE = "https://api.openaq.org/v3"
IST = ZoneInfo("Asia/Kolkata")

MAX_DISTANCE_M = 10_000  # further than this, a station says little about the user's own area
MAX_AGE = timedelta(hours=4)  # CPCB data reaches OpenAQ 1-3 hours late
MIN_HOURS = 16  # CPCB needs at least 16 hourly values for a 24-hour average
TIMEOUT = 3.0  # per request
LOCATIONS_TTL = 6 * 3600  # stations near a point rarely change
READING_TTL = 20 * 60  # stations report hourly
DOWN_PAUSE = 5 * 60  # after a failure, skip OpenAQ for a while instead of waiting on it each time

_locations_cache = {}  # (lat, lng) rounded -> (saved_at, [locations])
_reading_cache = {}  # location id -> (saved_at, reading or None)
_down_until = 0.0


class OpenAQError(Exception):
    pass


def _get(path: str, params: dict) -> dict:
    # the key goes in a header, so it never appears in URLs or error messages
    try:
        r = httpx.get(f"{BASE}{path}", params=params, headers={"X-API-Key": os.environ["OPENAQ_API_KEY"]}, timeout=TIMEOUT)
    except httpx.HTTPError as e:
        raise OpenAQError(type(e).__name__) from None
    if r.status_code != 200:
        raise OpenAQError(f"HTTP {r.status_code}")
    return r.json()


def nearest_station(lat: float, lng: float) -> Optional[dict]:
    """{"name", "distance_km", "pm2_5_24h_avg", "pm10_24h_avg", "updated" (IST datetime)} or None. Never raises."""
    global _down_until
    if not os.environ.get("OPENAQ_API_KEY") or time.monotonic() < _down_until:
        return None
    try:
        # the closest station first; if it has no usable PM data, try the next one
        for location in nearby_stations(lat, lng)[:2]:
            reading = station_reading(location)
            if reading:
                return {**reading, "distance_km": round(location["distance"] / 1000, 1)}
        return None
    except Exception as e:
        print(f"stations: using the estimate instead: {e}")
        _down_until = time.monotonic() + DOWN_PAUSE
        return None


def nearby_stations(lat: float, lng: float) -> list:
    """CPCB stations within 10 km that reported recently, nearest first."""
    key = (round(lat, 3), round(lng, 3))
    cached = _locations_cache.get(key)
    if cached and time.monotonic() - cached[0] < LOCATIONS_TTL:
        locations = cached[1]
    else:
        data = _get("/locations", {"coordinates": f"{lat},{lng}", "radius": MAX_DISTANCE_M, "limit": 100})
        # only official monitors: OpenAQ also lists low-cost sensors and other providers
        locations = [
            loc for loc in data.get("results", [])
            if (loc.get("provider") or {}).get("name") == "CPCB" and loc.get("isMonitor")
        ]
        _locations_cache[key] = (time.monotonic(), locations)
    return sorted((loc for loc in locations if is_fresh(last_reported(loc))), key=lambda loc: loc["distance"])


def last_reported(location: dict) -> Optional[datetime]:
    utc = (location.get("datetimeLast") or {}).get("utc")
    return datetime.fromisoformat(utc.replace("Z", "+00:00")) if utc else None


def is_fresh(when: Optional[datetime]) -> bool:
    return when is not None and datetime.now(timezone.utc) - when <= MAX_AGE


def station_reading(location: dict) -> Optional[dict]:
    cached = _reading_cache.get(location["id"])
    if cached and time.monotonic() - cached[0] < READING_TTL:
        return cached[1]

    # some stations still list old, dead sensors next to the working ones: ask for every PM sensor
    # and keep the one with recent hourly data
    sensors = [(s["parameter"]["name"], s["id"]) for s in location.get("sensors", []) if s["parameter"]["name"] in ("pm25", "pm10")]
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    with ThreadPoolExecutor(max_workers=4) as pool:
        hours = list(pool.map(lambda s: _get(f"/sensors/{s[1]}/hours", {"datetime_from": since, "limit": 48}), sensors))

    averages, newest = {}, None
    for (parameter, _), data in zip(sensors, hours):
        values = [h["value"] for h in data.get("results", []) if isinstance(h.get("value"), (int, float)) and h["value"] >= 0]
        if len(values) < MIN_HOURS:
            continue
        ended = max(datetime.fromisoformat(h["period"]["datetimeTo"]["utc"].replace("Z", "+00:00")) for h in data["results"])
        if not is_fresh(ended):
            continue
        averages[parameter] = sum(values) / len(values)
        newest = max(newest, ended) if newest else ended

    reading = None
    if averages:
        reading = {
            # "Revenue Colony-Shivajinagar, Pune - IITM": drop the agency that runs the station
            "name": location["name"].rsplit(" - ", 1)[0],
            "pm2_5_24h_avg": averages.get("pm25"),
            "pm10_24h_avg": averages.get("pm10"),
            "updated": newest.astimezone(IST),
        }
    _reading_cache[location["id"]] = (time.monotonic(), reading)
    return reading
