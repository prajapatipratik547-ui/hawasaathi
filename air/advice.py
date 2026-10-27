"""Fixed advice rules for alerts (no LLM). The advice texts themselves live in bot/texts.py."""
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from bot.texts import t

IST = ZoneInfo("Asia/Kolkata")

# India AQI categories from best to worst; the position is the "level" (0-5)
CATEGORIES = ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"]

EMOJI = {
    "Good": "🟢",
    "Satisfactory": "🟡",
    "Moderate": "🟠",
    "Poor": "🔴",
    "Very Poor": "🟣",
    "Severe": "🟤",
}


def level(category: str) -> int:
    return CATEGORIES.index(category)


def is_sensitive(profile: dict) -> bool:
    return profile.get("age_group") in ("child", "senior") or profile.get("condition") in ("lung", "heart", "pregnant")


def _hour_label(hour: int) -> tuple:
    # 16 -> ("4", "PM")
    return str(hour % 12 or 12), ("AM" if hour < 12 else "PM")


def best_time_outside(forecast: Optional[list]) -> Optional[str]:
    """The 2-hour window between 06:00 and 21:00 IST today with the lowest PM2.5, e.g. "4–6 PM".
    Returns None if no window is left today (or there's no forecast).
    """
    if not forecast:
        return None
    today = datetime.now(IST).date()
    pm2_5_by_hour = {
        f["time"].hour: f["pm2_5"]
        for f in forecast
        if f["time"].date() == today and f["pm2_5"] is not None
    }

    best_start, best_pm2_5 = None, None
    for start in range(6, 20):  # windows 6–8 AM ... 7–9 PM
        if start in pm2_5_by_hour and start + 1 in pm2_5_by_hour:
            avg = (pm2_5_by_hour[start] + pm2_5_by_hour[start + 1]) / 2
            if best_pm2_5 is None or avg < best_pm2_5:
                best_start, best_pm2_5 = start, avg
    if best_start is None:
        return None

    start_num, start_suffix = _hour_label(best_start)
    end_num, end_suffix = _hour_label(best_start + 2)
    if start_suffix == end_suffix:
        return f"{start_num}–{end_num} {end_suffix}"
    return f"{start_num} {start_suffix}–{end_num} {end_suffix}"


def build_advice(category: str, profile: dict) -> str:
    """Short, practical tips in the user's language for this India AQI category and profile."""
    lang = profile.get("language") or "en"

    # sensitive users get the advice for one category worse
    lvl = level(category)
    if is_sensitive(profile):
        lvl = min(lvl + 1, len(CATEGORIES) - 1)

    tips = [t(lang, f"tip_{lvl}")]

    # extra tips for the user's situation once the air is Moderate or worse (for them)
    if lvl >= 2:
        if profile.get("condition") in ("lung", "heart", "pregnant"):
            tips.append(t(lang, f"tip_{profile['condition']}"))
        if profile.get("age_group") in ("child", "senior"):
            tips.append(t(lang, f"tip_{profile['age_group']}"))
        if profile.get("outdoor_worker"):
            tips.append(t(lang, "tip_outdoor"))

    # keep it short: the general tip plus the two most important extras
    return " ".join(tips[:3])
