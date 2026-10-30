"""The question-answering agent: system prompt + question, the model calls tools, we return its answer.
If the LLM is unavailable, a rule-based answer is used instead, so the user always gets a reply.
"""
import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from agent.llm import LLMError, chat
from agent.tools import TOOLS, current_air, run_tool
from bot.alerts import for_you_line, headline_args
from bot.texts import t

IST = ZoneInfo("Asia/Kolkata")

MAX_TOOL_ROUNDS = 4
TIME_LIMIT = 15  # seconds for the whole answer, then we use the rule-based fallback
MAX_QUESTION_CHARS = 500
MAX_REPLY_CHARS = 4000  # Telegram's limit is 4096

LANGUAGE_NAMES = {"en": "English", "hi": "Hindi", "mr": "Marathi"}

SYSTEM_PROMPT = """You are HawaSaathi, a friendly air-quality assistant for India on Telegram.

Rules:
- Always reply in {language}. Max 5 short lines. Simple words. Plain text only, no markdown.
- The question may be a voice message turned into text, with a few misheard words: answer what the user most likely meant.
- Use the tools for every number. Never guess AQI or pollution values. If a tool has no data, say so.
- Give practical advice that fits the user's profile. Call get_user_profile before giving personal advice.
- Advice must match the air: suggest a mask only when the category is Poor or worse, or Moderate for sensitive people (child, 60+, lung or heart condition, pregnant). Never for Good or Satisfactory air.
- Keep to air-related advice. Skip generic tips like drinking water, sunscreen or snacks.
- AQI means India's National AQI (Good, Satisfactory, Moderate, Poor, Very Poor, Severe). The data is an Open-Meteo satellite/model estimate.
- This is not medical advice. If the user mentions symptoms, say "please see a doctor".
- Trouble breathing or chest pain is an emergency: whenever you mention it, even as a warning, say "call 108 now", never just "see a doctor".
- A line saying "Not medical advice. If you have trouble breathing, call 108." is added after air-quality answers automatically, so don't add your own general warning.
- Only answer questions about air quality, pollution, weather-related health and this bot. Politely decline anything else in one line.
- About this bot: it sends an air update every morning at the user's alert time (7 AM by default), warns when pollution spikes, and /settings changes language, location and profile.

Current date and time in India: {now}."""


def answer(user: dict, question: str) -> str:
    """Answer a user's question in their language. Never raises."""
    try:
        return ask_llm(user, question)[:MAX_REPLY_CHARS]
    except Exception as e:
        print(f"agent: using rule-based answer: {e}")
        return fallback_answer(user)


def ask_llm(user: dict, question: str) -> str:
    lang = user.get("language") or "en"
    system = SYSTEM_PROMPT.format(
        language=LANGUAGE_NAMES.get(lang, "English"),
        now=datetime.now(IST).strftime("%A %d %B %Y, %I:%M %p"),
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": question[:MAX_QUESTION_CHARS]},
    ]
    deadline = time.monotonic() + TIME_LIMIT
    used_tools = False

    for round_number in range(MAX_TOOL_ROUNDS + 1):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise LLMError("timed out")

        # after the last tool round, ask for a final answer with no more tool calls
        tool_choice = "none" if round_number == MAX_TOOL_ROUNDS else None
        reply = chat(messages, TOOLS, timeout=remaining, tool_choice=tool_choice)

        tool_calls = reply.get("tool_calls")
        if not tool_calls:
            # Telegram shows plain text, so drop any **bold** the model adds anyway
            text = (reply.get("content") or "").replace("**", "").strip()
            if not text:
                raise LLMError("empty answer")
            # safety net: air-quality answers always end with the same 108 line as the alerts
            if used_tools:
                text += "\n" + t(lang, "disclaimer")
            return text

        used_tools = True
        messages.append({"role": "assistant", "content": reply.get("content") or "", "tool_calls": tool_calls})
        for call in tool_calls:
            try:
                args = json.loads(call["function"].get("arguments") or "{}")
            except ValueError:
                args = {}
            result = run_tool(call["function"]["name"], args if isinstance(args, dict) else {}, user)
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": json.dumps(result, ensure_ascii=False)})

    raise LLMError("no answer after the tool rounds")


def fallback_answer(user: dict) -> str:
    """Rule-based reply: the current India AQI, category and advice from air/advice.py."""
    lang = user.get("language") or "en"
    air = current_air(user["lat"], user["lng"]) if user.get("lat") is not None else {"error": "no location"}
    if "error" in air:
        return t(lang, "agent_unavailable")
    return "\n".join([
        t(lang, "fallback_answer", **headline_args(user, air["india_aqi"], air["category"])),
        for_you_line(user, air["category"]),
        t(lang, "disclaimer"),
    ])
