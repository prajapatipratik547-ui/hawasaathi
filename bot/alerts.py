"""Morning and spike alerts. tick() is run every 15 minutes by the timers (POST/GET /api/tick)."""
import asyncio
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from air.advice import EMOJI, best_time_outside, build_advice, level
from air.naqi import india_aqi
from air.openmeteo import get_air_quality, get_forecast
from bot.telegram import Telegram
from bot.texts import t, category_name
from db import store

IST = ZoneInfo("Asia/Kolkata")

MORNING_WINDOW = timedelta(hours=3)  # send the morning alert up to 3 hours after alert_time
SPIKE_GAP = timedelta(hours=3)  # at most one spike alert per 3 hours
QUIET_HOURS = (22, 6)  # no spike alerts from 10 PM to 6 AM IST
PARALLEL_USERS = 12  # users checked at the same time: ~10 s for 50 users instead of ~100 s


async def tick(telegram: Telegram, force: bool = False) -> dict:
    """Send due alerts to every ready user. force=True sends a morning alert to everyone right now."""
    now = datetime.now(IST)
    users = store.list_ready_users()
    limit = asyncio.Semaphore(PARALLEL_USERS)

    async def check(user: dict):
        async with limit:
            try:
                return await check_user(telegram, user, now, force)
            except Exception as e:
                # one user's error must not stop the others
                print(f"tick: user failed: {e}")
                return "error"

    results = await asyncio.gather(*(check(user) for user in users))
    return {
        "users_checked": len(users),
        "alerts_sent": results.count("morning") + results.count("spike"),
        "morning": results.count("morning"),
        "spike": results.count("spike"),
        "errors": results.count("error"),
    }


async def check_user(telegram: Telegram, user: dict, now: datetime, force: bool):
    """Send this user a morning or spike alert if one is due. Returns "morning", "spike" or None."""
    # the air-data and database calls are plain (blocking) requests: run them in threads so
    # several users can be checked at once
    aqi_data = await asyncio.to_thread(get_air_quality, user["lat"], user["lng"])
    if not aqi_data:
        return None
    aqi, category = india_aqi(aqi_data.get("pm2_5_24h_avg"), aqi_data.get("pm10_24h_avg"))
    if aqi is None:
        return None

    last_morning = await asyncio.to_thread(store.last_alert, user["telegram_id"], "morning")
    if force or morning_due(user, last_morning, now):
        forecast = await asyncio.to_thread(get_forecast, user["lat"], user["lng"])
        best = best_time_outside(forecast)
        await send_alert(telegram, user, "morning", aqi, category, morning_text(user, aqi, category, best))
        return "morning"

    last = await asyncio.to_thread(store.last_alert, user["telegram_id"])
    if spike_due(category, last, now):
        await send_alert(telegram, user, "spike", aqi, category, spike_text(user, aqi, category))
        return "spike"

    return None


def sent_at(alert: dict) -> datetime:
    return datetime.fromisoformat(alert["sent_at"]).astimezone(IST)


def morning_due(user: dict, last_morning, now: datetime) -> bool:
    """True if now is within 3 hours after the user's alert_time and they haven't had one today."""
    alert_time = time.fromisoformat(user.get("alert_time") or "07:00")
    start = now.replace(hour=alert_time.hour, minute=alert_time.minute, second=0, microsecond=0)
    if not (start <= now < start + MORNING_WINDOW):
        return False
    return last_morning is None or sent_at(last_morning).date() != now.date()


def spike_due(category: str, last, now: datetime) -> bool:
    """True if the air is Very Poor or worse, or worse than at the last alert, and that was 3+ hours ago."""
    quiet_start, quiet_end = QUIET_HOURS
    if now.hour >= quiet_start or now.hour < quiet_end:
        return False
    if last and now - sent_at(last) <= SPIKE_GAP:
        return False
    if level(category) >= level("Very Poor"):
        return True
    return last is not None and last.get("category") in EMOJI and level(category) > level(last["category"])


def for_you_line(user: dict, category: str) -> str:
    lang = user.get("language") or "en"
    who = []
    if user.get("condition") in ("lung", "heart", "pregnant"):
        who.append(t(lang, f"who_{user['condition']}"))
    if user.get("age_group") in ("child", "senior"):
        who.append(t(lang, f"who_{user['age_group']}"))
    if user.get("outdoor_worker"):
        who.append(t(lang, "who_outdoor"))

    advice = build_advice(category, user)
    if who:
        return t(lang, "for_you", who=", ".join(who), advice=advice)
    return t(lang, "for_you_plain", advice=advice)


def headline_args(user: dict, aqi: int, category: str) -> dict:
    lang = user.get("language") or "en"
    area = user.get("area_name") or t(lang, "your_area")
    return {"area": area, "emoji": EMOJI[category], "category": category_name(lang, category), "aqi": aqi}


def morning_text(user: dict, aqi: int, category: str, best) -> str:
    lang = user.get("language") or "en"
    lines = [t(lang, "morning_alert", **headline_args(user, aqi, category)), for_you_line(user, category)]
    if best:
        lines.append(t(lang, "best_time", time=best))
    lines.append(t(lang, "disclaimer"))
    return "\n".join(lines)


def spike_text(user: dict, aqi: int, category: str) -> str:
    lang = user.get("language") or "en"
    return "\n".join([
        t(lang, "spike_alert", **headline_args(user, aqi, category)),
        for_you_line(user, category),
        t(lang, "disclaimer"),
    ])


async def send_alert(telegram: Telegram, user: dict, type: str, aqi: int, category: str, text: str):
    """Log the alert, then send it with the impact buttons (which need the alert id)."""
    lang = user.get("language") or "en"
    alert_id = await asyncio.to_thread(store.log_alert, user["telegram_id"], type, aqi, category)
    buttons = [
        [{"text": t(lang, "fb_yes"), "callback_data": f"fb:{alert_id}:1"}],
        [{"text": t(lang, "fb_no"), "callback_data": f"fb:{alert_id}:0"}],
    ]
    try:
        await telegram.send_message(user["chat_id"], text, inline_keyboard=buttons)
    except Exception:
        # not sent, so don't count it; the next tick will try again
        await asyncio.to_thread(store.delete_alert, alert_id)
        raise
