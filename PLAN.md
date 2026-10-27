# HawaSaathi — Locked Plan

**Hackathon:** Code for a Billion (Code for India) · Impact area: **Clean Air** · Solo build
**Submit by:** 14 Nov 2026 (official deadline 15 Nov) · Winners: 5 Dec 2026

---

## 1. Problem (in one line)
Almost every Indian breathes polluted air, but people don't know **when** it's worst where they live or **what to do about it**. Kids, elderly people, and people with asthma or heart problems are hit hardest.

## 2. Solution (in one line)
**HawaSaathi** is a free Telegram assistant that sends each person a daily, local air-quality alert with advice made for *them* (in Hindi, Marathi or English), warns them when pollution spikes, and answers questions like "Can I go for a run now?"

## 3. Who it's for (pilot)
- First 30–50 real users: family, college friends, housing-society groups, people with asthma or elderly parents.
- Pilot city: **Pune**, though it works anywhere in India that has a monitoring station nearby.

## 4. What the bot does (MVP — must ship)
1. **Onboarding** (`/start`): pick language → share location or type area → 3 quick questions:
   age group (child / adult / 60+), health condition (none / asthma-lung / heart / pregnant), works outdoors (yes/no).
2. **Morning alert** (default 7:00 AM IST): today's AQI near you, what it means for *you*, the safest time to go outside.
3. **Spike alert**: when air near you jumps a category or crosses "Very Poor", send a short warning (max 1 per 3 hours).
4. **Ask anything**: free-text questions are answered by the AI agent, using live data plus the user's profile.
5. **Impact button** under every alert: *"Did this change your plan? ✅ Yes / ❌ No"*.
6. **/stats page** (public web page): users, alerts sent, % who changed plans. Judges can open it.

**Later, only if time allows:** forecast-based "tomorrow" alerts, school/parent mode, WhatsApp.

## 5. How it works

```
 User (Telegram)
      │  message / location / button tap
      ▼
 Telegram webhook ──► Vercel (Python, FastAPI)
                          │
                          ├─ Agent (LLM + tools) ─► get_air_quality(lat,lng)  → WAQI API
                          │                       ├► get_forecast(lat,lng)     → WAQI API
                          │                       └► get_user_profile(id)      → Supabase
                          ├─ Advice rules (no LLM) for morning/spike alerts
                          └─ Supabase (users, alerts, feedback, questions)

 GitHub Actions cron (every 30 min) ──► /api/tick ──► sends morning + spike alerts
```

- **Alerts use fixed rules + pre-written templates in 3 languages** (fast, free, never wrong about numbers).
- **The LLM is only used for free-text questions** (keeps costs at ₹0 and avoids hitting rate limits).
- **Safety:** advice is general, not medical. Any symptom question → "please see a doctor"; emergency signs → "call 108".

## 6. Tech stack (locked)
| Part | Choice | Why |
|---|---|---|
| IDE | **AgentFoundry** (required) | Hackathon rule — do real build sessions in it |
| Language | Python 3.11 + FastAPI | Simple, you know it |
| Bot | Telegram Bot API (webhook) | Free, instant setup, no business verification |
| Air data | Open-Meteo air-quality API (no key) now; CPCB via data.gov.in (own free key) next | WAQI returned Delhi for every Indian location on 27 Oct, so it was dropped. Open-Meteo works everywhere and has hourly forecasts; CPCB adds real measured station data |
| AI | Groq free tier (openai/gpt-oss-120b), behind a swappable interface | Free and fast; can switch to Gemini/Claude later. Llama 3.3 70B was no longer on Groq on 27 Oct, so gpt-oss-120b replaced it (tool calling + good Hindi/Marathi) |
| Database | Supabase (free Postgres) | Stores users + impact data; easy to export |
| Hosting | Vercel (Python functions) | Free, you already use it |
| Scheduler | GitHub Actions cron | Free on public repos; Vercel Hobby cron is once/day only |
| License | MIT | Hackathon requires Apache-2.0 or MIT |

## 7. Data we store (Supabase tables)
- `users` — telegram_id, language, lat, lng, area_name, age_group, condition, outdoor_worker, alert_time, created_at
- `alerts` — id, user_id, type (morning/spike), aqi, sent_at
- `feedback` — alert_id, changed_plan (yes/no), answered_at
- `questions` — user_id, question, answered_at (no extra personal data)

## 8. Impact data (this is 25% of the score, and it breaks ties)
- **Baseline survey (before):** a short Google Form for beta users: "Do you check air quality? Did pollution change your plans last week?"
- **In-app:** number of users, alerts sent, questions answered, **% "changed my plan"**.
- **After survey (13 Nov):** same questions plus "Did HawaSaathi help? What did you do differently?"
- Before/after numbers and 2–3 real user quotes go into the submission.

## 9. Timeline
| Dates | Work | Done when |
|---|---|---|
| **27 Oct – 4 Nov** (light, ~30 min/day; Meta + PromptWars come first) | Accounts + keys, beta-user list, baseline survey sent | All keys in `.env`; 30+ people agreed to try it |
| **5 – 6 Nov** | Onboarding + live AQI lookup + Supabase | Bot replies with *your* AQI after `/start` |
| **7 Nov** | Morning alert rules + templates (EN/HI/MR) + cron + **first deploy** | You get a 7 AM alert on your phone |
| **8 – 9 Nov** | Agent Q&A with tools, spike alerts, feedback button, /stats page | Friends can ask questions in Hindi and get correct answers |
| **10 – 13 Nov** | **Launch to beta users**, fix bugs, collect data, after-survey on 13 Nov | 30+ active users, real numbers on /stats |
| **14 Nov** | README, 2–3 min demo video, submit GitHub issue | Submission issue is live |
| 15 Nov | Buffer only | — |

## 10. Submission checklist
- [ ] Built in AgentFoundry (keep screenshots of AF sessions for the "how you used AF" answer)
- [ ] Public GitHub repo, MIT license, README with setup steps
- [ ] Deployed and running (Vercel URL + Telegram bot link)
- [ ] 2–3 min demo video (YouTube unlisted)
- [ ] Scale & severity numbers with sources (State of Global Air, WHO, CPCB)
- [ ] Impact data: users, alerts, % changed plans, before/after survey, quotes
- [ ] GitHub submission form: track **Climate** (no "Clean Air" option in the dropdown; say Clean Air in the text)

## 11. Risks and fixes
| Risk | Fix |
|---|---|
| Not enough real users | Start collecting names **now**, not on 10 Nov |
| WAQI uses the US AQI scale, not India's | Label it clearly, or compute India's AQI from CPCB data if time allows |
| LLM free-tier limits | Alerts don't use the LLM; questions fall back to a rule-based answer |
| Overlap with Meta (to 4 Nov) and PromptWars (1 Nov) | Before 5 Nov only do setup and user-gathering |
| Health-advice liability | General advice only, doctor/108 disclaimer, no diagnosis |
