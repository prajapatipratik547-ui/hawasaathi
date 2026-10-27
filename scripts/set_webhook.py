"""Point the Telegram bot at the deployed app, or remove the webhook again.

    python scripts/set_webhook.py https://your-app.vercel.app   # set webhook to <domain>/api/telegram
    python scripts/set_webhook.py --delete                      # remove it (needed for scripts/poll.py)
    python scripts/set_webhook.py --info                        # show the current webhook

Needs TELEGRAM_BOT_TOKEN and TELEGRAM_WEBHOOK_SECRET in .env. The token is never printed.
"""
import argparse
import json
import os
import re
import sys

from dotenv import load_dotenv

# add project root to path so `from bot import ...` works when run from project folder
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

load_dotenv(os.path.join(ROOT, ".env"))

from bot.telegram import Telegram


def main():
    parser = argparse.ArgumentParser(description="Set, delete or show the Telegram webhook.")
    parser.add_argument("domain", nargs="?", help="your deployed app, e.g. https://hawasaathi.vercel.app")
    parser.add_argument("--delete", action="store_true", help="remove the webhook (to use scripts/poll.py again)")
    parser.add_argument("--info", action="store_true", help="show the current webhook")
    args = parser.parse_args()
    telegram = Telegram()

    if args.info:
        # getWebhookInfo never contains the token
        print(json.dumps(telegram.get_webhook_info_sync()["result"], indent=2))
        return

    if args.delete:
        telegram.delete_webhook_sync()
        print("Webhook removed. scripts/poll.py works again.")
        return

    if not args.domain:
        parser.error("give your domain, e.g. https://hawasaathi.vercel.app, or use --delete / --info")
    if not args.domain.startswith("https://"):
        parser.error("Telegram needs an https:// URL")

    secret = os.getenv("TELEGRAM_WEBHOOK_SECRET")
    if not secret:
        sys.exit("TELEGRAM_WEBHOOK_SECRET is not set in .env")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,256}", secret):
        sys.exit("TELEGRAM_WEBHOOK_SECRET may only use letters, digits, _ and - (Telegram's rule)")

    url = args.domain.rstrip("/") + "/api/telegram"
    telegram.set_webhook_sync(url, secret_token=secret)
    print(f"Webhook set to {url}")


if __name__ == "__main__":
    main()
