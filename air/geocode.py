import re
import httpx
from typing import Optional, Tuple

from agent.places import understand_place

BASE = "https://nominatim.openstreetmap.org"
HEADERS = {"User-Agent": "HawaSaathi/0.1"}

# Photon searches the same OpenStreetMap data but forgives typos ("Lohegoan" -> Lohegaon)
PHOTON = "https://photon.komoot.io/api/"
INDIA_BBOX = "68.1,6.5,97.4,35.7"  # lon/lat box around India


def short_name(item: dict, locality: Optional[str] = None) -> Optional[str]:
    """First locality plus the city, e.g. "Kothrud, Pune" instead of the full address."""
    display = item.get("display_name") or ""
    locality = locality or display.split(",")[0].strip()
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
    """Whatever the user typed -> (lat, lng, short name), or None if it isn't a place we can find.

    1. An Indian PIN code goes straight to the map search.
    2. Otherwise the LLM cleans up the text (typos, Hinglish, Devanagari, landmarks, other countries),
       and the map search finds that place in that country.
    3. If the LLM is unavailable, a plain map search in India: exact first, then typo-tolerant.
    """
    text = text.strip()
    if re.fullmatch(r"\d{6}", text):
        found = _nominatim_search(text, "in")
        return (found["lat"], found["lng"], found["name"]) if found else None

    place = understand_place(text)
    if place is None:
        found = _nominatim_search(text, "in") or _photon_search(text, "IN")
        return (found["lat"], found["lng"], found["name"]) if found else None
    if not place["place"]:
        return None
    return _search_understood(place, text)


def _search_understood(place: dict, text: str) -> Optional[Tuple[float, float, str]]:
    country = place["country_code"]
    query = ", ".join(p for p in (place["place"], place["city"], place["state"]) if p)
    # the cleaned-up name reads better than the map's ("Lohegaon, Pune", not "Lohgaon - Wagholi Road")
    name_parts = [place["place"]]
    if place["city"] and place["city"].lower() not in place["place"].lower():
        name_parts.append(place["city"])

    found = _nominatim_search(query, country.lower())
    if not found:
        # typo-tolerant search: it may land somewhere a little different, so use that spot's real name
        found = _photon_search(query, country)
        if found:
            name_parts = [found["name"]]
    if not found:
        # the user's own words, in that country only ("PCMC" -> Pimpri-Chinchwad)
        found = _nominatim_search(text, country.lower())
        if found:
            name_parts = [found["name"]]
    if not found and place["city"]:
        # a small area the map doesn't know: use its city, and say so in the name
        found = _nominatim_search(", ".join(p for p in (place["city"], place["state"]) if p), country.lower())
        name_parts = [place["city"]]
    if not found:
        return None

    if country != "IN" and found["country"]:
        name_parts.append(found["country"])
    return (found["lat"], found["lng"], ", ".join(name_parts))


def _nominatim_search(text: str, country: str = "in") -> Optional[dict]:
    """{"lat", "lng", "name", "country"} or None. Names come back in English."""
    # exact names, and the only one that understands Devanagari ("कोथरूड, पुणे")
    params = {"q": text, "format": "json", "limit": 1, "countrycodes": country, "addressdetails": 1, "accept-language": "en"}
    try:
        r = httpx.get(f"{BASE}/search", params=params, headers=HEADERS, timeout=10.0)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        item = data[0]
        lat = float(item.get("lat"))
        lon = float(item.get("lon"))
        # the best match is sometimes a landmark in that area ("Pune International Airport" for
        # "Lohegaon, Pune"); then keep the user's own word for the place
        typed = text.split(",")[0].strip()
        matched = (item.get("display_name") or "").split(",")[0].strip().lower()
        own_word = typed.isascii() and typed.lower() not in matched and matched not in typed.lower()
        name = short_name(item, typed.title()[:40] if own_word else None)
        return {"lat": lat, "lng": lon, "name": name, "country": (item.get("address") or {}).get("country")}
    except Exception:
        return None


def _photon_search(text: str, country: str = "IN") -> Optional[dict]:
    """Typo-tolerant search: {"lat", "lng", "name", "country"} or None."""
    params = {"q": text, "limit": 5, "lang": "en"}
    if country == "IN":
        params["bbox"] = INDIA_BBOX
    try:
        r = httpx.get(PHOTON, params=params, headers=HEADERS, timeout=10.0)
        r.raise_for_status()
        features = [f for f in r.json().get("features", []) if f["properties"].get("countrycode") == country]
        if not features:
            return None
        lon, lat = features[0]["geometry"]["coordinates"]
        props = features[0]["properties"]
        # Photon often matches a landmark ("Pune International Airport"), so name the area around it instead
        name = reverse_geocode(lat, lon) or props.get("name")
        return {"lat": lat, "lng": lon, "name": name, "country": props.get("country")}
    except Exception:
        return None


def reverse_geocode(lat: float, lng: float) -> Optional[str]:
    params = {"lat": lat, "lon": lng, "format": "json", "zoom": 14, "addressdetails": 1, "accept-language": "en"}
    try:
        r = httpx.get(f"{BASE}/reverse", params=params, headers=HEADERS, timeout=10.0)
        r.raise_for_status()
        data = r.json()
        if not data or "error" in data:
            return None
        return short_name(data)
    except Exception:
        return None
