import httpx
from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

BASE = "https://air-quality-api.open-meteo.com/v1/air-quality"
IST = ZoneInfo("Asia/Kolkata")


def get_forecast(lat: float, lng: float) -> Optional[list]:
    """Hourly forecast for the next 24 hours, starting with the current hour.
    Returns a list of {"time": datetime in IST, "pm2_5": float, "pm10": float}, or None on error.
    """
    params = {
        "latitude": lat,
        "longitude": lng,
        "hourly": "pm2_5,pm10",
        "forecast_days": 2,
        "timezone": "Asia/Kolkata",
    }
    try:
        r = httpx.get(BASE, params=params, timeout=10.0)
        r.raise_for_status()
        hourly = r.json().get("hourly", {})
        times = hourly.get("time") or []
        pm2_5_list = hourly.get("pm2_5") or []
        pm10_list = hourly.get("pm10") or []

        this_hour = datetime.now(IST).replace(minute=0, second=0, microsecond=0)
        forecast = []
        for time_str, pm2_5, pm10 in zip(times, pm2_5_list, pm10_list):
            # times come back in IST without an offset, e.g. "2026-10-27T16:00"
            time = datetime.fromisoformat(time_str).replace(tzinfo=IST)
            if this_hour <= time < this_hour + timedelta(hours=24):
                forecast.append({"time": time, "pm2_5": pm2_5, "pm10": pm10})
        return forecast
    except Exception:
        return None


def get_air_quality(lat: float, lng: float) -> Optional[dict]:
    """Returns dict with keys: us_aqi, pm2_5, pm10, time, pm2_5_24h_avg, pm10_24h_avg
    Returns None on error.
    """
    params = {
        "latitude": lat,
        "longitude": lng,
        "current": "us_aqi,pm2_5,pm10",
        "hourly": "pm2_5,pm10",
        "past_days": 1,
        "timezone": "Asia/Kolkata",
    }
    try:
        r = httpx.get(BASE, params=params, timeout=10.0)
        r.raise_for_status()
        data = r.json()
        # current values
        current = data.get("current", {})
        us_aqi = current.get("us_aqi")
        pm2_5 = current.get("pm2_5")
        pm10 = current.get("pm10")
        time = current.get("time")

        hourly = data.get("hourly", {})
        pm2_5_list = hourly.get("pm2_5") or []
        pm10_list = hourly.get("pm10") or []
        # take last 24 entries if available
        def avg_last_24(lst):
            if not lst:
                return None
            last = lst[-24:]
            nums = [x for x in last if isinstance(x, (int, float))]
            if not nums:
                return None
            return sum(nums) / len(nums)

        pm2_5_24 = avg_last_24(pm2_5_list)
        pm10_24 = avg_last_24(pm10_list)

        return {
            "us_aqi": us_aqi,
            "pm2_5": pm2_5,
            "pm10": pm10,
            "time": time,
            "pm2_5_24h_avg": pm2_5_24,
            "pm10_24h_avg": pm10_24,
        }
    except Exception:
        return None
