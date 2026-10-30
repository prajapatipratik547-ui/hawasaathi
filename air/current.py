"""The India AQI right now at a location: from the nearest official CPCB station when there's a
fresh one within 10 km, otherwise from the Open-Meteo satellite/model estimate.
Replies, alerts and the agent all use this, so they always agree on the number.
"""
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from air.naqi import india_aqi
from air.openmeteo import get_air_quality
from air.stations import nearest_station


def current_air(lat: float, lng: float) -> Optional[dict]:
    """{"india_aqi", "category", "pm2_5", "pm10" (24-hour averages), "station"} or None if there's no data.
    "station" is {"name", "distance_km", "updated"} when the numbers come from a CPCB station, else None.
    """
    # ask both sources at once, so the station lookup adds no waiting when OpenAQ is quick
    with ThreadPoolExecutor(max_workers=2) as pool:
        station_job = pool.submit(nearest_station, lat, lng)
        estimate_job = pool.submit(get_air_quality, lat, lng)
        station, estimate = station_job.result(), estimate_job.result()

    if station:
        aqi, category = india_aqi(station["pm2_5_24h_avg"], station["pm10_24h_avg"])
        if aqi is not None:
            return {
                "india_aqi": aqi,
                "category": category,
                "pm2_5": station["pm2_5_24h_avg"],
                "pm10": station["pm10_24h_avg"],
                "station": {k: station[k] for k in ("name", "distance_km", "updated")},
            }

    if not estimate:
        return None
    aqi, category = india_aqi(estimate.get("pm2_5_24h_avg"), estimate.get("pm10_24h_avg"))
    if aqi is None:
        return None
    return {
        "india_aqi": aqi,
        "category": category,
        "pm2_5": estimate.get("pm2_5_24h_avg"),
        "pm10": estimate.get("pm10_24h_avg"),
        "station": None,
    }
