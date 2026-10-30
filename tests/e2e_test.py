"""End-to-end test against the REAL Supabase, Open-Meteo, OpenAQ, Nominatim and Groq. Only Telegram is faked.

    .\\.venv\\Scripts\\python.exe tests\\e2e_test.py

Needs a filled-in .env. Takes about a minute. Test users have negative Telegram IDs (-900001..-900003),
so they can never be real people, and they are deleted at the end (their alerts, feedback and
questions go with them). Exits with code 1 if any check fails.
"""
import asyncio
import os
import sys
import time
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
sys.stdout.reconfigure(encoding="utf-8")  # Hindi/Marathi and emoji in a Windows terminal

from dotenv import load_dotenv

load_dotenv(os.path.join(ROOT, ".env"))

from fastapi.testclient import TestClient

from air import current, stations
from api import index
from bot import alerts
from db import store

IST = ZoneInfo("Asia/Kolkata")
TEST_USERS = {
    -900001: ("en", "lang_en", "Kothrud, Pune"),
    -900002: ("hi", "lang_hi", "कोथरूड, पुणे"),
    -900003: ("mr", "lang_mr", "Andheri, Mumbai"),
}
QUESTIONS = {
    -900001: "Can I go for a run now?",
    -900002: "क्या आज शाम को बच्चे को पार्क ले जाना ठीक है?",
    -900003: "आज सकाळी फिरायला जाऊ का?",
}
ANSWERS = {-900001: ["adult", "lung", "no"], -900002: ["child", "none", "no"], -900003: ["senior", "heart", "yes"]}

PASS, FAIL = [], []


def check(name, ok, detail=""):
    (PASS if ok else FAIL).append(name)
    print(("  ✅ " if ok else "  ❌ ") + name + (f"  [{detail}]" if detail and not ok else ""))


def devanagari(text):
    return any("ऀ" <= ch <= "ॿ" for ch in text)


class FakeTelegram:
    """Records what the bot would send instead of sending it."""

    def __init__(self):
        self.log = []
        self.next_id = 100

    async def send_message(self, chat_id, text, **kw):
        self.next_id += 1
        self.log.append({"chat": chat_id, "text": text, "id": self.next_id, **{k: v for k, v in kw.items() if v}})
        return {"ok": True, "result": {"message_id": self.next_id}}

    async def answer_callback_query(self, callback_id, text=None):
        self.log.append({"toast": text})

    async def remove_buttons(self, chat_id, message_id):
        self.log.append({"removed_buttons": message_id})

    async def edit_message_text(self, chat_id, message_id, text):
        self.log.append({"edited": message_id, "text": text})

    async def send_chat_action(self, chat_id, action):
        self.log.append({"action": action})

    def sent(self, chat):
        return [e for e in self.log if e.get("chat") == chat]

    def last(self, chat):
        return self.sent(chat)[-1]


tg = FakeTelegram()
index.telegram = tg


def msg(uid, text=None, location=None):
    m = {"message_id": 1, "chat": {"id": uid}, "from": {"id": uid}}
    if text is not None:
        m["text"] = text
    if location:
        m["location"] = location
    return {"message": m}


def tap(uid, data, message_id):
    return {"callback_query": {"id": "cb", "data": data, "from": {"id": uid}, "message": {"chat": {"id": uid}, "message_id": message_id}}}


def run(update):
    asyncio.run(index.handle_update(update))


def cleanup():
    for uid in TEST_USERS:
        store._request("DELETE", "users", params={"telegram_id": f"eq.{uid}"}, prefer="return=minimal")


try:
    cleanup()  # in case an earlier run was interrupted
    for uid, (lang, lang_button, area) in TEST_USERS.items():
        print(f"\n=== onboarding: user {uid} ({lang}) ===")
        run(msg(uid, "/start"))
        welcome = tg.last(uid)
        check("/start shows the 3 language buttons", len(sum(welcome.get("inline_keyboard", []), [])) == 3)
        check("state = awaiting_language", store.get_user(uid)["state"] == "awaiting_language")

        run(tap(uid, lang_button, welcome["id"]))
        ask = tg.last(uid)
        check("language tap -> location question in the right language", ask.get("reply_markup_request_location") and store.get_user(uid)["language"] == lang, ask["text"][:40])
        run(tap(uid, lang_button, welcome["id"]))  # duplicate tap
        check("duplicate language tap is ignored", tg.last(uid)["id"] == ask["id"])

        run(msg(uid, area))
        replies = tg.sent(uid)[-2:]
        u = store.get_user(uid)
        check("typed area -> AQI reply", "AQI" in replies[0]["text"], replies[0]["text"][:60])
        check("AQI reply says its source (CPCB station or estimate)", "🏭" in replies[0]["text"] or "🛰️" in replies[0]["text"])
        check(f"short area name saved ({u.get('area_name')})", u.get("area_name") and u["area_name"].count(",") <= 1)
        check("first question (age) asked with buttons", len(replies[1].get("inline_keyboard", [])) == 3)

        run(tap(uid, "condition:lung", replies[1]["id"]))  # out-of-order tap
        check("out-of-order answer is ignored", store.get_user(uid).get("condition") is None)
        q_msg = replies[1]
        for column, answer in zip(["age_group", "condition", "outdoor_worker"], ANSWERS[uid]):
            run(tap(uid, f"{column}:{answer}", q_msg["id"]))
            edited = [e for e in tg.log if e.get("edited") == q_msg["id"]]
            check(f"answer {column}={answer}: question edited to show ✅", edited and "✅" in edited[-1]["text"])
            q_msg = tg.last(uid)
        u = store.get_user(uid)
        check("all set message + state ready", u["state"] == "ready" and "/settings" in tg.last(uid)["text"])
        check("profile saved", [u["age_group"], u["condition"], "yes" if u["outdoor_worker"] else "no"] == ANSWERS[uid])
        check("alert_time defaults to 07:00", str(u.get("alert_time", "")).startswith("07:00"))
        print("   AQI reply:", replies[0]["text"].replace("\n", " | "))

    print("\n=== CPCB stations (real OpenAQ) ===")
    if os.environ.get("OPENAQ_API_KEY"):
        air = current.current_air(18.5913, 73.9197)  # Lohegaon, Pune: CPCB stations within a few km
        check("Pune gets a fresh CPCB station within 10 km", air and air["station"] and air["station"]["distance_km"] <= 10, str(air))
    else:
        print("   (no OPENAQ_API_KEY: skipped)")
    air = current.current_air(51.5, -0.12)  # London: no CPCB stations
    check("no station nearby -> satellite estimate", air and air["station"] is None, str(air))
    real_base, stations.BASE = stations.BASE, "http://10.255.255.1/v3"  # an address that never answers
    stations._reading_cache.clear()
    stations._locations_cache.clear()
    t0 = time.time()
    air = current.current_air(18.5913, 73.9197)
    check(f"OpenAQ down -> estimate after {time.time() - t0:.1f}s (max ~3s)", air and air["station"] is None and time.time() - t0 < 6)
    stations.BASE, stations._down_until = real_base, 0.0

    print("\n=== AI agent (real Groq) ===")
    for uid, question in QUESTIONS.items():
        t0 = time.time()
        run(msg(uid, question))
        reply = tg.last(uid)["text"]
        lang = TEST_USERS[uid][0]
        right_lang = not devanagari(reply) if lang == "en" else devanagari(reply)
        check(f"{lang}: answered in {time.time() - t0:.1f}s, logged, typing shown",
              store.count_questions_today(uid, 20) == 1 and {"action": "typing"} in tg.log)
        check(f"{lang}: reply in user's language + 108 line", right_lang and "108" in reply)
        print("   Q:", question, "\n   A:", reply.replace("\n", "\n      "))
        time.sleep(8)  # stay under Groq's tokens-per-minute limit
    run(msg(-900001, "Write me a poem about cricket"))
    print("   off-topic ->", tg.last(-900001)["text"])
    check("off-topic is declined (no 108 line, short)", "108" not in tg.last(-900001)["text"] and len(tg.last(-900001)["text"]) < 200)

    print("\n=== daily question limit ===")
    for _ in range(19):
        store.log_question(-900001, "test")
    run(msg(-900001, "one more?"))
    check("21st question gets the limit message", "20" in tg.last(-900001)["text"], tg.last(-900001)["text"][:60])

    print("\n=== morning alert + impact button (real DB, fake Telegram) ===")
    now = datetime.now(IST)
    for uid in TEST_USERS:
        user = store.get_user(uid)
        sent = asyncio.run(alerts.check_user(tg, user, now, force=True))
        alert_msg = tg.last(uid)
        last = store.last_alert(uid, "morning")
        check(f"{uid}: morning alert sent + logged", sent == "morning" and last and last["category"])
        check(f"{uid}: alert has Yes/No buttons with its alert id", f"fb:{last['id']}:1" in str(alert_msg.get("inline_keyboard")))
        morning_time = now.replace(hour=7, minute=30)
        check(f"{uid}: no second morning alert the same day", not alerts.morning_due(user, last, morning_time))
        if uid == -900001:
            print("   " + alert_msg["text"].replace("\n", "\n   "))
        run(tap(uid, f"fb:{last['id']}:1", alert_msg["id"]))
        run(tap(uid, f"fb:{last['id']}:0", alert_msg["id"]))  # second tap must not count
        rows = store._request("GET", "feedback", params={"alert_id": f"eq.{last['id']}", "select": "changed_plan"})
        check(f"{uid}: feedback saved once, first answer kept", rows == [{"changed_plan": True}], str(rows))

    print("\n=== /settings, unknown text, errors ===")
    run(msg(-900002, "/settings"))
    check("/settings shows language buttons and waits", len(tg.last(-900002).get("inline_keyboard", [])) == 2 and store.get_user(-900002)["state"] == "awaiting_language")
    run(msg(-900002, "/help"))
    check("unknown command -> friendly fallback in Hindi", "/start" in tg.last(-900002)["text"] and devanagari(tg.last(-900002)["text"]))
    real_geocode = index.geocode_area
    index.geocode_area = lambda q: (_ for _ in ()).throw(RuntimeError("Nominatim down"))
    store.upsert_user(-900003, state="awaiting_location")
    try:
        run(msg(-900003, "Pune"))
    except RuntimeError:
        pass
    index.geocode_area = real_geocode
    check("error -> 'something went wrong' in Marathi", "माफ करा" in tg.last(-900003)["text"])
    run(msg(-900003, "zzqxv nowhere place"))
    check("unknown place -> 'couldn't find' message", "सापडली नाही" in tg.last(-900003)["text"], tg.last(-900003)["text"][:50])

    print("\n=== HTTP endpoints (same app Vercel runs) ===")
    client = TestClient(index.app)
    check("/api/telegram rejects a wrong secret (403)", client.post("/api/telegram", json={}, headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"}).status_code == 403)
    check("/api/telegram accepts the right secret", client.post("/api/telegram", json={"update_id": 1}, headers={"X-Telegram-Bot-Api-Secret-Token": os.getenv("TELEGRAM_WEBHOOK_SECRET")}).json() == {"ok": True})
    check("/api/tick rejects a wrong cron secret (403)", client.post("/api/tick", headers={"X-Cron-Secret": "wrong"}).status_code == 403)
    store._stats_cache["stats"] = None
    s = client.get("/api/stats").json()
    check("/api/stats counts include the test users", s["users"]["total"] >= 3 and s["alerts"]["morning"] >= 3, str(s["users"]))
    page = client.get("/stats")
    check("/stats page renders, no personal data", page.status_code == 200 and "Kothrud" not in page.text and "-90000" not in page.text)

except Exception:
    traceback.print_exc()
    FAIL.append("crashed")
finally:
    cleanup()
    left = [uid for uid in TEST_USERS if store.get_user(uid)]
    print(f"\ncleanup: test users deleted (with their alerts/feedback/questions): {not left}")
    print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed" + (f" -> {FAIL}" if FAIL else ""))

sys.exit(1 if FAIL else 0)
