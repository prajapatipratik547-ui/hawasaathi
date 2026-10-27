# Step 6: Morning alerts, spike alerts and the impact button

Read PLAN.md and all the code first. Then build this step. Keep it simple and readable.
Never print or log the values in .env.

1. **Forecast:** extend air/openmeteo.py with get_forecast(lat, lng) that returns hourly pm2_5 and pm10 for the next 24 hours (forecast_days=2, timezone=Asia/Kolkata).

2. **Advice rules (no LLM):** new file air/advice.py with
   - best_time_outside(forecast): the 2-hour window between 06:00 and 21:00 IST today with the lowest PM2.5, e.g. "4–6 PM".
   - build_advice(category, profile): short, practical tips based on the India AQI category and the user's profile
     (age_group child/adult/senior, condition none/lung/heart/pregnant, outdoor_worker).
     Sensitive users (child, senior, lung, heart, pregnant) get stricter advice one category earlier.
     Examples: avoid morning walks, keep kids' outdoor play short, wear an N95 mask outdoors, keep inhalers handy,
     close windows during peak hours, outdoor workers take breaks in cleaner hours.
   - All advice texts go in bot/texts.py for en, hi and mr.

3. **Morning alert message** (in the user's language), for example:
   "🌅 Good morning! Air in Kothrud today: 🟠 Moderate (India AQI 142)
    For you (asthma): keep your inhaler with you, avoid exercising outdoors before 10 AM.
    ✅ Best time to go out: 4–6 PM
    Not medical advice. If you have trouble breathing, call 108."
   Use an emoji per category: 🟢 Good, 🟡 Satisfactory, 🟠 Moderate, 🔴 Poor, 🟣 Very Poor, 🟤 Severe.

4. **Impact button:** every alert has inline buttons "✅ Yes, it changed my plan" / "❌ No".
   callback_data like "fb:<alert_id>:1" or "fb:<alert_id>:0". On tap: log_feedback (only once per alert),
   answer the callback with "Thanks!", and edit the message to remove the buttons.

5. **Tick endpoint:** POST /api/tick in api/index.py, protected by header "X-Cron-Secret" == CRON_SECRET (403 otherwise). It runs tick():
   - For every user who finished onboarding: if the current IST time is at or after their alert_time,
     less than 3 hours after it, and they have not had a morning alert today, send the morning alert and log_alert(type='morning').
   - Spike alert: if the user's current India AQI is "Very Poor" or worse, or is a higher category than their last alert,
     and their last alert was more than 3 hours ago, send a short spike warning and log_alert(type='spike').
   - One user's error must not stop the others. Return a JSON summary (users checked, alerts sent).
   Add list_ready_users() and last_alert(telegram_id, type=None) to db/store.py.

6. **Local testing:** scripts/tick.py that loads .env and calls tick() directly. Add a --force flag that sends a morning alert to every ready user right now, ignoring times.

7. **Scheduler:** .github/workflows/tick.yml that runs every 30 minutes ("*/30 * * * *") and on workflow_dispatch,
   and POSTs to the URL in secret TICK_URL with header X-Cron-Secret from secret CRON_SECRET. Use curl with --fail.

8. Use zoneinfo "Asia/Kolkata" for times and add tzdata to requirements.txt (Windows needs it).

9. **Small fixes from testing:**
   - Area names are too long ("Kothrud, Karve Nagar, Pune, Pune City Subdistrict, Pune, Maharashtra, 411051, India").
     Store and show a short name instead: the first locality plus the city, e.g. "Kothrud, Pune".
   - If anything fails while handling a user's message, send them the friendly texts.py message
     "Sorry, something went wrong. Please try again in a minute." in their language, instead of staying silent.
   - After a user taps an onboarding answer, edit that question message so the buttons disappear
     and it shows the chosen answer, e.g. "1/3 · Age group: Adult ✅". Right now old buttons stay on screen.
   - Telegram and Supabase calls sometimes fail with a temporary ConnectError. Retry them once after 1 second.

10. Run py_compile on every changed file. Then tell me the exact PowerShell command to test with scripts/tick.py --force.
