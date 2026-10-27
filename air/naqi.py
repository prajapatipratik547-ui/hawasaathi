from typing import Tuple, Optional

# CPCB National AQI bands and breakpoints
AQI_BANDS = [
    (0, 50, "Good"),
    (51, 100, "Satisfactory"),
    (101, 200, "Moderate"),
    (201, 300, "Poor"),
    (301, 400, "Very Poor"),
    (401, 500, "Severe"),
]

# Breakpoints for PM2.5 (µg/m3) per band
PM25_BPS = [
    (0, 30),
    (31, 60),
    (61, 90),
    (91, 120),
    (121, 250),
    (250, 1000),
]

# Breakpoints for PM10 (µg/m3) per band
PM10_BPS = [
    (0, 50),
    (51, 100),
    (101, 250),
    (251, 350),
    (351, 430),
    (430, 10000),
]


def _sub_index(conc: float, bps: list) -> Optional[float]:
    if conc is None:
        return None
    # find band index
    for i, (c_lo, c_hi) in enumerate(bps):
        if conc <= c_hi:
            a_lo, a_hi = AQI_BANDS[i][0], AQI_BANDS[i][1]
            # linear interpolation
            return a_lo + (conc - c_lo) * (a_hi - a_lo) / (c_hi - c_lo)
    # if above highest defined, cap to 500
    return 500.0


def india_aqi(pm25_24h: float, pm10_24h: float) -> Tuple[Optional[int], Optional[str]]:
    """Compute National AQI from 24-hour PM2.5 and PM10 averages. Returns (aqi:int, category:str) or (None, None) if missing."""
    sub_pm25 = _sub_index(pm25_24h, PM25_BPS)
    sub_pm10 = _sub_index(pm10_24h, PM10_BPS)
    if sub_pm25 is None and sub_pm10 is None:
        return (None, None)
    # overall AQI is the higher sub-index
    candidates = [v for v in (sub_pm25, sub_pm10) if v is not None]
    aqi_val = max(candidates)
    aqi = int(round(aqi_val))
    # find category
    for lo, hi, cat in AQI_BANDS:
        if lo <= aqi <= hi:
            return (aqi, cat)
    return (min(aqi, 500), "Severe")
