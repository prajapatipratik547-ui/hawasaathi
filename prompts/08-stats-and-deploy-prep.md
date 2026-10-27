# Step 8: Public stats page + get ready to deploy on Vercel

Read PLAN.md and all the code first. Keep it simple and readable.
Never print or log the values in .env.

1. **Stats page** (judges will open this): GET /stats returns a clean, mobile-friendly HTML page (inline CSS, no JS framework) showing:
   - total users, users who finished onboarding, users per language (English / हिंदी / मराठी)
   - alerts sent (morning and spike), feedback answers, and **% who said "it changed my plan"**
   - questions answered by the AI agent
   - "Last updated" time in IST
   No personal data at all: no names, IDs, areas or question text. Also GET /api/stats with the same numbers as JSON.
   Use Supabase REST count queries (Prefer: count=exact with a HEAD/limit=0 request) in db/store.py. Cache the numbers for 5 minutes.

2. **Vercel config:** make vercel.json valid for the current Vercel Python runtime (remove the invalid top-level "runtime" key).
   Route /api/telegram, /api/tick, /api/stats and /stats to api/index.py. Give the function maxDuration 60.
   Make sure nothing at import time needs .env (Vercel injects env vars instead).

3. **Webhook script:** scripts/set_webhook.py
   - `python scripts/set_webhook.py https://<vercel-domain>` calls setWebhook with url <domain>/api/telegram and TELEGRAM_WEBHOOK_SECRET
   - `python scripts/set_webhook.py --delete` removes the webhook (needed again for local poll.py testing)
   - `python scripts/set_webhook.py --info` prints getWebhookInfo (without the token)

4. **Secrets:** if CRON_SECRET is missing or empty in .env, generate a random 32-character value and add it. Don't print it.

5. **README.md:** rewrite it for judges and contributors: what HawaSaathi is, the problem (with the numbers from PLAN.md),
   features, how it works (short diagram), tech stack, "Built with AgentFoundry", local setup, deploy steps
   (Vercel env vars list, set_webhook.py, GitHub Actions secrets TICK_URL and CRON_SECRET), data sources
   (Open-Meteo, CPCB national AQI breakpoints, OpenStreetMap Nominatim), privacy (what we store), MIT license.

6. **Bug from testing:** sending /settings shows the welcome text WITHOUT the language buttons and immediately asks
   for the location in English. /settings must show the English / हिंदी / मराठी buttons and wait for a tap, exactly like /start.

7. **First commit:** run git status and check that .env, .venv, .codenow and __pycache__ are NOT included.
   Then stage everything else and commit with the message "HawaSaathi MVP: onboarding, alerts, AI agent, stats".
   Do NOT push. Do NOT create a GitHub repo. I will do that myself.

8. Run py_compile on every changed file, and list the exact env var NAMES I need to add in Vercel.
