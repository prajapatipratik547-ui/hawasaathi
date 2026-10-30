"""Tools the agent can call. Each returns a small dict that is sent back to the model as JSON."""
from typing import Optional

from air.advice import best_time_outside
from air.geocode import geocode_area
from air.naqi import india_aqi
from air.openmeteo import get_air_quality, get_forecast
from bot.texts import category_name

SOURCE = "Open-Meteo satellite/model estimate"

# tool definitions in the OpenAI/Groq format
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_air",
            "description": "Current India AQI, category, PM2.5 and PM10 at the user's saved location.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_air_forecast",
            "description": (
                "Hourly PM2.5 and India AQI category for the next hours at the user's saved location, "
                "plus the best 2-hour window to go outside today (06:00-21:00)."
            ),
            "parameters": {
                "type": "object",
                "properties": {"hours": {"type": "integer", "description": "How many hours ahead, 1-24. Default 12."}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_profile",
            "description": "The user's language, area, age group, health condition and whether they work outdoors.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_air_for_place",
            "description": "Current India AQI for any place by name: Indian areas and cities, or anywhere in the world.",
            "parameters": {
                "type": "object",
                "properties": {"place": {"type": "string", "description": "Place name, e.g. 'Andheri, Mumbai' or 'London'"}},
                "required": ["place"],
            },
        },
    },
]


def current_air(lat: float, lng: float, area: Optional[str] = None) -> dict:
    """Current India AQI at a location, or {"error": ...}."""
    data = get_air_quality(lat, lng)
    if not data:
        return {"error": "no air-quality data right now"}
    aqi, category = india_aqi(data.get("pm2_5_24h_avg"), data.get("pm10_24h_avg"))
    if aqi is None:
        return {"error": "not enough data to compute the AQI"}
    return {
        "area": area,
        "india_aqi": aqi,
        "category": category,
        "pm2_5": data.get("pm2_5"),
        "pm10": data.get("pm10"),
        "source": SOURCE,
    }


def in_user_language(result: dict, user: dict) -> dict:
    # give the model the category in the user's language, with the same words the alerts use
    if "category" in result:
        result["category"] = category_name(user.get("language") or "en", result["category"])
    return result


def get_current_air(user: dict) -> dict:
    return in_user_language(current_air(user["lat"], user["lng"], user.get("area_name")), user)


def get_air_forecast(user: dict, hours: int = 12) -> dict:
    hours = max(1, min(int(hours or 12), 24))
    forecast = get_forecast(user["lat"], user["lng"])
    if not forecast:
        return {"error": "no forecast right now"}
    hourly = []
    for f in forecast[:hours]:
        # category from hourly values, so it's a rough guide (official AQI uses 24-hour averages)
        _, category = india_aqi(f["pm2_5"], f["pm10"])
        if category:
            category = category_name(user.get("language") or "en", category)
        hourly.append({"time": f["time"].strftime("%a %H:%M"), "pm2_5": f["pm2_5"], "category": category})
    return {
        "area": user.get("area_name"),
        "hourly": hourly,
        "best_2_hour_window_today": best_time_outside(forecast),
        "note": "hourly categories are approximate",
        "source": SOURCE,
    }


def get_user_profile(user: dict) -> dict:
    return {
        "language": user.get("language"),
        "area": user.get("area_name"),
        "age_group": user.get("age_group"),
        "condition": user.get("condition"),
        "outdoor_worker": user.get("outdoor_worker"),
    }


def get_air_for_place(user: dict, place: str = "") -> dict:
    geocoded = geocode_area(place) if place else None
    if not geocoded:
        return {"error": f"couldn't find a place called '{place}'"}
    lat, lng, name = geocoded
    return in_user_language(current_air(lat, lng, name), user)


TOOL_FUNCTIONS = {
    "get_current_air": get_current_air,
    "get_air_forecast": get_air_forecast,
    "get_user_profile": get_user_profile,
    "get_air_for_place": get_air_for_place,
}


def run_tool(name: str, args: dict, user: dict) -> dict:
    func = TOOL_FUNCTIONS.get(name)
    if not func:
        return {"error": f"unknown tool {name}"}
    try:
        return func(user, **args)
    except Exception as e:
        return {"error": f"tool failed: {type(e).__name__}"}
