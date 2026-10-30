<p align="center"><img src="assets/logo-256.png" width="128" height="128" alt="HawaSaathi logo"></p>

# HawaSaathi 🌬️

**A free Telegram assistant that tells you how clean the air is where you live, and what to do about it, in English, हिंदी or मराठी.**

Every morning it sends a local air-quality update with advice made for *you* (your age, health and work), warns you when pollution spikes, and answers questions like *"Can I go for a run now?"* or *"क्या आज बच्चे को पार्क ले जाना ठीक है?"*

- **Try it:** [t.me/HawaSaathiBot](https://t.me/HawaSaathiBot)
- **Live impact numbers:** `/stats` on the deployed app (e.g. `https://<your-app>.vercel.app/stats`)
- Built for **Code for a Billion (Code for India)** · Impact area: **Clean Air**

---

## The problem

Almost every Indian breathes polluted air, but people don't know **when** it's worst where they live or **what to do about it**. Children, elderly people, and people with asthma or heart problems are hit hardest.

- **All of India's 1.4 billion people** live where annual particulate pollution is above the WHO guideline. In 2023 the national average PM2.5 was 41 µg/m³, against a WHO guideline of 5 µg/m³. ([AQLI India Fact Sheet 2025](https://aqli.epic.uchicago.edu/files/India%20FactSheet_2025_IndiaWV.pdf), EPIC, University of Chicago)
- Meeting the WHO guideline would add **3.5 years** to the life expectancy of an average Indian. ([AQLI 2025](https://aqli.epic.uchicago.edu/files/India%20FactSheet_2025_IndiaWV.pdf))
- India had **more than 2 million deaths attributable to air pollution in 2023**, out of 7.9 million worldwide. ([State of Global Air 2025](https://www.stateofglobalair.org/sites/default/files/documents/2025-10/soga-2025-annual-report-executive-summary-infographic.pdf), Health Effects Institute)

Air-quality data exists, but it sits in apps and dashboards people don't check, in English, with numbers that don't say what *you* should do today.

## What HawaSaathi does

1. **Onboarding** (`/start`): pick a language, share your location (or type your area), answer 3 quick questions: age group, health condition, and whether you work outdoors.
   **Type any place, any way:** an area, city, landmark or PIN code, in English, हिंदी or मराठी, with typos or as a sentence. *"Lohegoan, Pune"*, *"mera ghar kothrud me hai"*, *"near Pune station"*, *"PCMC"*, *"411014"* and *"London"* all work. An AI model cleans up the text, and OpenStreetMap finds the coordinates.
2. **Morning alert** (7 AM IST): today's India AQI near you, advice for *your* profile, and the cleanest 2-hour window to go outside.
3. **Spike alert**: a short warning when the air turns *Very Poor* or gets worse than at your last alert (at most one every 3 hours, none at night).
4. **Ask anything**: free-text questions are answered by an AI agent that looks up live data and your profile. It never guesses numbers.
5. **Impact button** under every alert: *"Did this change your plan? ✅ Yes / ❌ No"*.
6. **Public `/stats` page**: users, alerts sent and the % who said an alert changed their plan. Counts only, no personal data.

`/settings` lets you change your language, location and answers at any time.

**Safety:** advice is general, not medical. Every alert and air-quality answer ends with *"Not medical advice. If you have trouble breathing, call 108."*. Questions about symptoms are pointed to a doctor, and emergencies to 108.

## How it works

```
 User on Telegram
     │  message / location / button tap
     ▼
 Telegram webhook ──► Vercel (Python, FastAPI)  api/index.py
                          │
                          ├─ Onboarding + texts in en / hi / mr      bot/
                          ├─ AI agent (Groq, tool calling)            agent/
                          │     ├─ get_current_air / get_air_forecast ──► Open-Meteo
                          │     ├─ get_air_for_place                  ──► Nominatim (OpenStreetMap)
                          │     └─ get_user_profile                   ──► Supabase
                          ├─ Advice rules, no LLM (alerts)            air/advice.py
                          └─ Supabase Postgres (users, alerts, feedback, questions)

 GitHub Actions cron (every 30 min) ──► POST /api/tick ──► morning + spike alerts
 Anyone ──► GET /stats ──► counts from Supabase (cached 5 min)
```

- **Alerts use fixed rules and pre-written templates in 3 languages**, so they're fast, free and never wrong about the numbers.
- **The LLM is only used for free-text questions.** If it's unavailable, slow (over 15 s) or over its rate limit, the bot replies with a rule-based answer instead, so users always get a reply.

## Tech stack

| Part | Choice |
|---|---|
| Language | Python 3 + FastAPI |
| Bot | Telegram Bot API (webhook) |
| Air data | Open-Meteo Air Quality API, converted to India's National AQI (CPCB breakpoints) |
| Places | OpenStreetMap Nominatim |
| AI | Groq (`openai/gpt-oss-120b`, OpenAI-compatible API), behind one `chat()` function so it can be swapped |
| Database | Supabase (Postgres via its REST API, Row Level Security on) |
| Hosting | Vercel (Python function) |
| Scheduler | GitHub Actions cron |

## Built with AgentFoundry

HawaSaathi was built for Code for a Billion using **AgentFoundry**, the AI-assisted IDE required by the hackathon. The build was done step by step as prompt-driven sessions. Each step's prompt is in [`prompts/`](prompts/).

## Project layout

```
api/index.py        FastAPI app: Telegram webhook, /api/tick, /stats, /api/stats
bot/                Telegram client, alerts (tick), all texts in en/hi/mr
agent/              LLM client (Groq), agent tools, agent loop + rule-based fallback
air/                Open-Meteo, India AQI calculation, advice rules, geocoding
db/                 schema.sql (Supabase) and store.py (REST calls)
web/                The /stats HTML page
scripts/            poll.py (local testing), tick.py, set_webhook.py, setup_bot_profile.py
assets/             logo (SVG), bot profile photo
.github/workflows/  tick.yml (cron every 30 minutes)
```

## Local setup

You need Python 3.11+, a Telegram bot token from [@BotFather](https://t.me/BotFather), a free [Supabase](https://supabase.com) project and a free [Groq](https://console.groq.com/keys) API key.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env     # then fill in your own values
```

1. **Database:** in Supabase, open **SQL Editor → New query**, paste `db/schema.sql` and click **Run**. It's safe to run again.
2. **Chat with the bot locally** (long polling, no webhook needed):
   ```powershell
   .\.venv\Scripts\python.exe scripts\set_webhook.py --delete   # only if a webhook is set
   .\.venv\Scripts\python.exe scripts\poll.py
   ```
3. **Send alerts now** to test them: `.\.venv\Scripts\python.exe scripts\tick.py --force`

## Deploy (Vercel + Telegram + GitHub Actions)

1. **Import the repo in Vercel** (or run `vercel` from the project folder) with Framework Preset **Other**. Vercel detects the FastAPI app in `api/index.py` and sends every path to it (`/stats`, `/api/stats`, `/api/telegram`, `/api/tick`). `vercel.json` only sets the 60-second time limit.
2. **Add these environment variables** in Vercel → Project → Settings → Environment Variables:

   | Name | What |
   |---|---|
   | `TELEGRAM_BOT_TOKEN` | from @BotFather |
   | `TELEGRAM_WEBHOOK_SECRET` | random string (letters, digits, `_`, `-`); Telegram sends it back on every webhook call |
   | `SUPABASE_URL` | Supabase → Project Settings → API |
   | `SUPABASE_SERVICE_KEY` | the service_role key or a secret key (`sb_secret_…`), **not** the anon key |
   | `GROQ_API_KEY` | from console.groq.com |
   | `GROQ_MODEL` | optional, defaults to `openai/gpt-oss-120b` |
   | `CRON_SECRET` | random string; GitHub Actions sends it to `/api/tick` |

   Then redeploy so the variables take effect.
3. **Point Telegram at your app:**
   ```powershell
   .\.venv\Scripts\python.exe scripts\set_webhook.py https://<your-app>.vercel.app
   .\.venv\Scripts\python.exe scripts\set_webhook.py --info    # check: url set, no last_error_message
   ```
4. **Turn on the timers.** `/api/tick` sends whatever alerts are due. Calling it extra times is safe (one morning alert per day, at most one spike alert per 3 hours), so three timers run side by side:
   - **[cron-job.org](https://cron-job.org) (main timer, every 15 minutes):** a free job that sends `POST https://<your-app>.vercel.app/api/tick` with the header `X-Cron-Secret: <CRON_SECRET>`.
   - **Vercel Cron (daily safety net):** set in `vercel.json` (`0 2 * * *` = 7:30 AM IST). Vercel's free plan runs it once a day, somewhere in that hour, so morning alerts still go out if the other timers fail. Vercel signs in with `Authorization: Bearer <CRON_SECRET>` automatically.
   - **GitHub Actions (backup):** `.github/workflows/tick.yml`. In GitHub → Settings → Secrets and variables → Actions, add `TICK_URL` = `https://<your-app>.vercel.app/api/tick` and `CRON_SECRET` = the same value as in Vercel. GitHub runs free scheduled workflows irregularly (we saw gaps of 4–7 hours), so it isn't the main timer.
5. Open `https://<your-app>.vercel.app/stats`.

## Data sources

- **[Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api):** hourly PM2.5 and PM10 for any location, from the Copernicus Atmosphere Monitoring Service (CAMS) models. These are satellite/model estimates, not station readings, and the bot labels them that way. Licensed CC BY 4.0.
- **CPCB National Air Quality Index:** India's official AQI categories and breakpoints (Good, Satisfactory, Moderate, Poor, Very Poor, Severe). HawaSaathi computes the India AQI from 24-hour average PM2.5 and PM10.
- **[OpenStreetMap Nominatim](https://nominatim.org/)** and **[Photon](https://photon.komoot.io/)** (typo-tolerant search): turn typed place names into coordinates and back into short area names. Map data © OpenStreetMap contributors, ODbL.

## Privacy

HawaSaathi stores only what it needs to send useful alerts:

- **Users:** Telegram user ID and chat ID, chosen language, onboarding step, location (latitude/longitude and a short area name such as "Kothrud, Pune"), age group, health condition, whether you work outdoors, and alert time.
- **Alerts:** when an alert was sent, its type and the AQI at that time.
- **Feedback:** your Yes/No answer to "Did this change your plan?".
- **Questions:** the text of questions you ask, and when you asked them.

It does **not** store names, usernames or phone numbers. Your question text and profile are sent to Groq to generate an answer. Your location is sent to Open-Meteo, and typed place names to Groq (to clean them up) and to Nominatim/Photon. The database is locked with Row Level Security, so only the server's key can read it. The `/stats` page shows totals only. To have your data deleted, open an issue or contact the maintainer.

## License

[MIT](LICENSE) © 2026 Pratik Prajapati
