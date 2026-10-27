# Step 7: AI agent that answers questions

Read PLAN.md and all the code first. Then build this step. Keep it simple and readable.
Never print or log the values in .env.

Goal: when a user who finished onboarding sends free text (not a command, not an onboarding answer),
an AI agent answers it, e.g. "Can I go for a run now?", "Is it safe to take my baby to the park this evening?",
"क्या आज बाहर व्यायाम करना ठीक है?".

1. **LLM client:** new file agent/llm.py that calls Groq's OpenAI-compatible API
   (https://api.groq.com/openai/v1/chat/completions) with httpx, using GROQ_API_KEY and GROQ_MODEL
   (default "llama-3.3-70b-versatile"). First check the current model list at
   https://api.groq.com/openai/v1/models to confirm the default exists and supports tool calling; pick the
   closest current replacement if it doesn't. Keep it behind one function chat(messages, tools) so we can
   switch providers later.

2. **Tools the agent can call** (agent/tools.py), each returning small JSON:
   - get_current_air(): current India AQI, category, PM2.5, PM10 for the user's saved location
   - get_air_forecast(hours=12): hourly PM2.5 and India AQI category for the next hours, plus the best 2-hour window
   - get_user_profile(): language, area, age group, condition, outdoor worker
   - get_air_for_place(place): geocode a place name and return its current India AQI (for "how is the air in Mumbai?")

3. **Agent loop** (agent/agent.py): answer(user, question) → system prompt + question, let the model call tools,
   max 4 tool rounds, then return the final text. System prompt rules:
   - You are HawaSaathi, a friendly air-quality assistant for India.
   - Always reply in the user's language (en/hi/mr). Max 5 short lines. Simple words.
   - Use the tools for every number. Never guess AQI or pollution values.
   - Give practical advice that fits the user's profile.
   - Not medical advice. For symptoms say "please see a doctor". For trouble breathing or chest pain say "call 108 now".
   - Only answer questions about air quality, pollution, weather-related health and this bot. Politely decline anything else.

4. **Wire it in** api/index.py: free text from a ready user → send a "typing" chat action, call answer(), reply, and log_question().
   Limit each user to 20 questions per day (count today's rows in questions); after that, reply politely in their language.

5. **Fallback:** if GROQ_API_KEY is missing, the API fails or it times out (15 s), reply with a rule-based answer
   instead: the current India AQI, category and advice from air/advice.py. The user must always get a reply.

6. Add GROQ_API_KEY and GROQ_MODEL to .env.example. Add any new texts to bot/texts.py for en, hi and mr.

7. Run py_compile on every changed file. Then give me 5 test questions (2 English, 2 Hindi, 1 Marathi),
   including one off-topic question and one about another city.
