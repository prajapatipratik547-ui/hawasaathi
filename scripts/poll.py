"""Local long-polling tester for Telegram updates. Run this locally to fetch getUpdates and pass them to the same handler used by the webhook.

Create a .env with TELEGRAM_BOT_TOKEN and optionally TELEGRAM_WEBHOOK_SECRET.
"""
import os
import sys
import time
from dotenv import load_dotenv
# add project root to path so `from api import index` works when run from project folder
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

load_dotenv()

import httpx
import asyncio
from api import index

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Set TELEGRAM_BOT_TOKEN in .env")
BASE = f"https://api.telegram.org/bot{TOKEN}"


def get_updates(offset=None, timeout=30):
    params = {"timeout": timeout}
    if offset:
        params["offset"] = offset
    # BASE contains the bot token, so don't let httpx errors (which include the URL) escape
    try:
        r = httpx.get(f"{BASE}/getUpdates", params=params, timeout=timeout + 10)
    except httpx.HTTPError as e:
        raise RuntimeError(f"Telegram getUpdates failed: {type(e).__name__}") from None
    if r.status_code >= 400:
        raise RuntimeError(f"Telegram getUpdates failed: HTTP {r.status_code}")
    return r.json().get("result", [])


def skip_old_updates():
    """Telegram re-sends updates the last run didn't confirm (e.g. after Ctrl+C), which replays
    old button taps. offset=-1 returns only the newest update and forgets the rest; we skip that one too."""
    latest = get_updates(offset=-1, timeout=0)
    return latest[-1]["update_id"] + 1 if latest else None


def main():
    print("Starting local poller. Press Ctrl+C to stop.")
    offset = skip_old_updates()
    if offset:
        print("Skipped messages sent while the poller was off.")
    while True:
        try:
            updates = get_updates(offset=offset)
            for u in updates:
                offset = u["update_id"] + 1
                # call the webhook handler synchronously via event loop
                asyncio.run(index.handle_update(u))
            time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping")
            break
        except Exception as e:
            print("Error in poller:", e)
            time.sleep(5)


if __name__ == "__main__":
    main()
