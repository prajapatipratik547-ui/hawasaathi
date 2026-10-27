import httpx
from typing import Optional, Tuple

BASE = "https://nominatim.openstreetmap.org"
HEADERS = {"User-Agent": "HawaSaathi/0.1"}


def short_name(item: dict) -> Optional[str]:
    """First locality plus the city, e.g. "Kothrud, Pune" instead of the full address."""
    display = item.get("display_name") or ""
    locality = display.split(",")[0].strip()
    address = item.get("address") or {}
    # reverse lookups often have no "city", so fall back to the district
    city = (
        address.get("city")
        or address.get("state_district")
        or address.get("town")
        or address.get("village")
        or address.get("county")
    )
    if locality and city and city != locality:
        return f"{locality}, {city}"
    return locality or city or None


def geocode_area(text: str) -> Optional[Tuple[float, float, str]]:
    params = {"q": text, "format": "json", "limit": 1, "countrycodes": "in", "addressdetails": 1}
    try:
        r = httpx.get(f"{BASE}/search", params=params, headers=HEADERS, timeout=10.0)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        item = data[0]
        lat = float(item.get("lat"))
        lon = float(item.get("lon"))
        return (lat, lon, short_name(item))
    except Exception:
        return None


def reverse_geocode(lat: float, lng: float) -> Optional[str]:
    params = {"lat": lat, "lon": lng, "format": "json", "zoom": 14, "addressdetails": 1}
    try:
        r = httpx.get(f"{BASE}/reverse", params=params, headers=HEADERS, timeout=10.0)
        r.raise_for_status()
        data = r.json()
        if not data or "error" in data:
            return None
        return short_name(data)
    except Exception:
        return None
