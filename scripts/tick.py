"""Run the alert tick locally, the same thing the cron does via POST /api/tick.

    python scripts/tick.py           # send only the alerts that are due right now
    python scripts/tick.py --force   # send a morning alert to every ready user now, ignoring times

Needs TELEGRAM_BOT_TOKEN, SUPABASE_URL and SUPABASE_SERVICE_KEY in .env.
"""
import argparse
import asyncio
import json
import os
import sys

from dotenv import load_dotenv

# add project root to path so `from bot import ...` works when run from project folder
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

load_dotenv(os.path.join(ROOT, ".env"))

from bot.alerts import tick
from bot.telegram import Telegram


def main():
    parser = argparse.ArgumentParser(description="Send HawaSaathi morning/spike alerts that are due.")
    parser.add_argument("--force", action="store_true", help="send a morning alert to every ready user right now")
    args = parser.parse_args()

    summary = asyncio.run(tick(Telegram(), force=args.force))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
