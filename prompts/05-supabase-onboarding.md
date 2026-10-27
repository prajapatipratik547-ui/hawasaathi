# Step 5: Supabase storage + onboarding questions

Read PLAN.md and all the code first. Then build this step:

1. db/schema.sql: Postgres tables for Supabase:
   - users: telegram_id (bigint primary key), chat_id, language, state, lat, lng, area_name, age_group, condition, outdoor_worker (bool), alert_time (default '07:00'), created_at, updated_at
   - alerts: id, telegram_id, type ('morning'|'spike'), aqi, category, sent_at
   - feedback: id, alert_id, telegram_id, changed_plan (bool), answered_at
   - questions: id, telegram_id, question, answered_at
   Enable Row Level Security on every table with NO policies (only our server key can access).
2. db/store.py: small functions using httpx and the Supabase REST API (no supabase-py): get_user, upsert_user, log_alert, log_feedback, log_question. Read SUPABASE_URL and SUPABASE_SERVICE_KEY from env at call time. Put the key in the "apikey" header, and also in "Authorization: Bearer" only if it starts with "eyJ" (legacy key).
3. Replace the in-memory USERS dict in api/index.py with db/store.py, so data survives restarts (needed on Vercel).
4. After the first AQI reply, ask 3 onboarding questions with inline buttons, one at a time, and save the answers:
   - Age group: Child (under 14) / Adult / 60+
   - Health condition: None / Asthma or lung / Heart / Pregnant
   - Work outdoors most of the day? Yes / No
   Then reply: "All set! I'll send your air update every morning at 7 AM." (send /settings to change; just store the time for now)
5. All bot messages must use the user's chosen language (English, Hindi, Marathi). Put all texts in one file, bot/texts.py, as a dict per language.
6. Run py_compile on every file. Then tell me exactly how to run db/schema.sql in the Supabase SQL Editor.

Keep the code simple and readable. Don't build morning alerts yet; that's the next step.
Never print or log the values in .env.
