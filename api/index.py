from fastapi import FastAPI, Header, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from dotenv import load_dotenv
import hmac
import os
from agent.agent import answer
from bot import alerts
from bot.telegram import Telegram
from bot.texts import WELCOME, t, category_name
from air.openmeteo import get_air_quality as om_get_air_quality
from air.naqi import india_aqi
from air.geocode import geocode_area, reverse_geocode
from db import store
from web.stats_page import render_stats_page, render_unavailable_page

# local runs read .env; on Vercel there's no .env and env vars are injected instead.
# Nothing below needs an env var at import time: they are all read when a request comes in.
load_dotenv()

# Vercel sends every path straight to this app, so vercel.json needs no rewrites.
# No auto-generated /docs pages: this is a bot backend, not a public API.
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

telegram = Telegram()

# let browsers and Vercel's edge cache the stats for a bit; the numbers are cached for 5 minutes anyway
STATS_CACHE_HEADERS = {"Cache-Control": "public, max-age=60, s-maxage=300"}

LANGUAGES = {"lang_en": "en", "lang_hi": "hi", "lang_mr": "mr"}
LANGUAGE_LABELS = {"en": "English", "hi": "हिंदी", "mr": "मराठी"}

# onboarding questions, asked in this order after the first AQI reply:
# (user state while waiting for the answer, users column, answer options)
QUESTIONS = [
    ("awaiting_age", "age_group", ["child", "adult", "senior"]),
    ("awaiting_condition", "condition", ["none", "lung", "heart", "pregnant"]),
    ("awaiting_outdoor", "outdoor_worker", ["yes", "no"]),
]

DAILY_QUESTION_LIMIT = 20


@app.post("/api/telegram")
async def telegram_webhook(request: Request, x_telegram_bot_api_secret_token: str = Header(None)):
    webhook_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET")
    if webhook_secret and not hmac.compare_digest(x_telegram_bot_api_secret_token or "", webhook_secret):
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    update = await request.json()
    # minimal update handling: message (text or location) and callback_query
    try:
        await handle_update(update)
    except Exception as e:
        # don't crash on handler errors
        return JSONResponse({"ok": False, "error": str(e)})

    return JSONResponse({"ok": True})


@app.post("/api/tick")
async def tick_endpoint(x_cron_secret: str = Header(None)):
    # called every 30 minutes by .github/workflows/tick.yml
    cron_secret = os.getenv("CRON_SECRET")
    if not cron_secret or not x_cron_secret or not hmac.compare_digest(x_cron_secret, cron_secret):
        raise HTTPException(status_code=403, detail="Invalid cron secret")
    return JSONResponse(await alerts.tick(telegram))


@app.get("/")
async def home():
    # people (and judges) opening the bare domain land on the impact page
    return RedirectResponse("/stats")


@app.get("/stats", response_class=HTMLResponse)
async def stats_page():
    # public page for judges: counts only, no personal data
    try:
        stats = store.get_stats()
    except Exception as e:
        print(f"stats failed: {e}")
        return HTMLResponse(render_unavailable_page(), status_code=503)
    return HTMLResponse(render_stats_page(stats), headers=STATS_CACHE_HEADERS)


@app.get("/api/stats")
async def stats_json():
    try:
        stats = store.get_stats()
    except Exception as e:
        print(f"stats failed: {e}")
        return JSONResponse({"error": "stats unavailable"}, status_code=503)
    return JSONResponse(stats, headers=STATS_CACHE_HEADERS)


async def handle_update(update: dict):
    try:
        await route_update(update)
    except Exception:
        # tell the user instead of staying silent, then let the caller log the error
        await send_error_message(update)
        raise


async def send_error_message(update: dict):
    source = update.get("message") or update.get("callback_query") or {}
    chat = source.get("chat") or (source.get("message") or {}).get("chat") or {}
    uid = (source.get("from") or {}).get("id")
    if not chat.get("id"):
        return
    try:
        lang = (store.get_user(uid) or {}).get("language") or "en"
    except Exception:
        lang = "en"
    try:
        await telegram.send_message(chat["id"], t(lang, "error"))
    except Exception:
        pass


async def route_update(update: dict):
    # callback_query for inline buttons
    if "callback_query" in update:
        await handle_button(update["callback_query"])
        return

    if "message" not in update:
        return

    msg = update["message"]
    chat_id = msg["chat"]["id"]
    uid = msg["from"]["id"]
    text = (msg.get("text") or "").strip()
    # "/settings@HawaSaathiBot" and "/Settings" count as /settings
    command = text.split()[0].split("@")[0].lower() if text.startswith("/") else None

    user = store.get_user(uid) or {}
    lang = user.get("language") or "en"

    # /start and /settings both (re)start onboarding with the language buttons
    if command in ("/start", "/settings"):
        store.upsert_user(uid, chat_id=chat_id, state="awaiting_language")
        await telegram.send_message(
            chat_id,
            WELCOME,
            inline_keyboard=[
                [{"text": "English", "callback_data": "lang_en"}, {"text": "हिंदी", "callback_data": "lang_hi"}],
                [{"text": "मराठी", "callback_data": "lang_mr"}],
            ],
        )
        return

    # location shared with the button
    if "location" in msg:
        loc = msg["location"]
        await save_location_and_reply(uid, chat_id, user, loc.get("latitude"), loc.get("longitude"))
        return

    # if we're awaiting location and user typed an area name, geocode it
    if text and user.get("state") == "awaiting_location":
        geocoded = geocode_area(text)
        if not geocoded:
            await telegram.send_message(chat_id, t(lang, "place_not_found"))
            return
        lat, lng, display = geocoded
        await save_location_and_reply(uid, chat_id, user, lat, lng, display)
        return

    # free text from a user who finished onboarding goes to the AI agent
    if text and not text.startswith("/") and user.get("state") == "ready":
        await handle_question(uid, chat_id, user, text)
        return

    # fallback reply
    if text:
        await telegram.send_message(chat_id, t(lang, "fallback"))


async def handle_question(uid: int, chat_id: int, user: dict, question: str):
    lang = user.get("language") or "en"
    if store.count_questions_today(uid, DAILY_QUESTION_LIMIT) >= DAILY_QUESTION_LIMIT:
        await telegram.send_message(chat_id, t(lang, "question_limit", limit=DAILY_QUESTION_LIMIT))
        return

    try:
        await telegram.send_chat_action(chat_id, "typing")
    except Exception:
        pass  # only cosmetic

    reply = answer(user, question)  # never fails: falls back to a rule-based answer
    await telegram.send_message(chat_id, reply)
    store.log_question(uid, question)


async def save_location_and_reply(uid: int, chat_id: int, user: dict, lat: float, lng: float, area_name: str = None):
    """Save the user's location, reply with the AQI there, and start the questions if onboarding."""
    lang = user.get("language") or "en"
    onboarding = user.get("state") == "awaiting_location"
    area_name = area_name or reverse_geocode(lat, lng) or t(lang, "your_area")

    store.upsert_user(
        uid,
        chat_id=chat_id,
        lat=lat,
        lng=lng,
        area_name=area_name,
        state=QUESTIONS[0][0] if onboarding else user.get("state"),
    )

    await telegram.send_message(chat_id, aqi_text(lang, lat, lng, area_name), remove_keyboard=True)

    if onboarding:
        await ask_question(chat_id, lang, 0)


def aqi_text(lang: str, lat: float, lng: float, area_name: str) -> str:
    # fetch AQI from Open-Meteo and convert to India AQI
    aqi_data = om_get_air_quality(lat, lng)
    if not aqi_data:
        return t(lang, "no_data")

    aqi_val, category = india_aqi(aqi_data.get("pm2_5_24h_avg"), aqi_data.get("pm10_24h_avg"))
    if aqi_val is None:
        return t(lang, "not_enough_data")

    return t(
        lang,
        "aqi_reply",
        area=area_name,
        aqi=aqi_val,
        category=category_name(lang, category),
        pm25=aqi_data.get("pm2_5"),
        pm10=aqi_data.get("pm10"),
    )


async def ask_question(chat_id: int, lang: str, index: int):
    _, column, options = QUESTIONS[index]
    buttons = [[{"text": t(lang, f"{column}_{option}"), "callback_data": f"{column}:{option}"}] for option in options]
    await telegram.send_message(chat_id, t(lang, f"q_{column}"), inline_keyboard=buttons)


async def answer_button(cq: dict, text: str = None):
    # acknowledge the callback so the client unblocks
    try:
        await telegram.answer_callback_query(cq.get("id"), text=text)
    except Exception:
        pass


async def tidy_message(chat_id: int, message_id: int, text: str = None):
    """Remove a message's buttons (and replace its text, if given). Only cosmetic, so errors are ignored."""
    try:
        if text:
            await telegram.edit_message_text(chat_id, message_id, text)
        else:
            await telegram.remove_buttons(chat_id, message_id)
    except Exception:
        pass


async def handle_button(cq: dict):
    data = cq.get("data") or ""
    uid = cq["from"]["id"]
    chat_id = cq["message"]["chat"]["id"]
    message_id = cq["message"]["message_id"]

    if data.startswith("fb:"):
        await handle_feedback(cq, uid, chat_id, message_id, data)
        return

    await answer_button(cq)
    user = store.get_user(uid) or {}

    if data in LANGUAGES:
        # only a tap on the welcome we're waiting on counts. An old or re-sent tap (e.g. replayed
        # by Telegram after poll.py restarts) used to skip straight to the English location question.
        if user.get("state") != "awaiting_language":
            await tidy_message(chat_id, message_id)
            return
        lang = LANGUAGES[data]
        store.upsert_user(uid, chat_id=chat_id, language=lang, state="awaiting_location")
        # show the choice instead of the buttons, like the onboarding answers ("✅ English")
        await tidy_message(chat_id, message_id, f"{WELCOME}\n\n✅ {LANGUAGE_LABELS[lang]}")
        await telegram.send_message(
            chat_id,
            t(lang, "ask_location"),
            reply_markup_request_location=True,
            location_button_text=t(lang, "share_location"),
        )
        return

    # onboarding answers look like "age_group:adult"
    lang = user.get("language") or "en"
    column, _, answer = data.partition(":")

    for index, (state, question_column, options) in enumerate(QUESTIONS):
        # ignore taps on old buttons for a question we're not waiting on
        if column != question_column or answer not in options or user.get("state") != state:
            continue

        value = (answer == "yes") if column == "outdoor_worker" else answer
        is_last = index == len(QUESTIONS) - 1
        next_state = "ready" if is_last else QUESTIONS[index + 1][0]
        store.upsert_user(uid, **{column: value, "state": next_state})

        # replace the question with the chosen answer, e.g. "1/3 · Age group: Adult ✅"
        await tidy_message(chat_id, message_id, t(lang, f"answered_{column}", answer=t(lang, f"{column}_{answer}")))

        if is_last:
            # alert_time defaults to 07:00 in the database
            await telegram.send_message(chat_id, t(lang, "all_set"))
        else:
            await ask_question(chat_id, lang, index + 1)
        return


async def handle_feedback(cq: dict, uid: int, chat_id: int, message_id: int, data: str):
    """Impact button under an alert: "fb:<alert_id>:1" (changed plan) or "fb:<alert_id>:0"."""
    try:
        _, alert_id, changed = data.split(":")
        alert_id = int(alert_id)
    except ValueError:
        await answer_button(cq)
        return

    # only the first answer per alert counts
    if not store.has_feedback(alert_id):
        store.log_feedback(alert_id, uid, changed == "1")

    lang = (store.get_user(uid) or {}).get("language") or "en"
    await answer_button(cq, t(lang, "thanks"))
    await tidy_message(chat_id, message_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
