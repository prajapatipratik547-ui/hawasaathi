"""LLM client. Everything goes through chat(), so we can switch providers later.

Groq's API is OpenAI-compatible. On 27 Oct 2026 llama-3.3-70b-versatile was no longer listed,
so the default is openai/gpt-oss-120b (supports tool calling). Override with GROQ_MODEL.
"""
import os
from typing import Optional

import httpx

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-120b"


class LLMError(Exception):
    pass


def chat(messages: list, tools: Optional[list] = None, timeout: float = 15.0, tool_choice: Optional[str] = None) -> dict:
    """Send the conversation and return the assistant's message: {"content": ..., "tool_calls": [...]}."""
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise LLMError("GROQ_API_KEY is not set")

    model = os.getenv("GROQ_MODEL") or DEFAULT_MODEL
    payload = {"model": model, "messages": messages, "temperature": 0.3}
    if model.startswith("openai/gpt-oss"):
        # gpt-oss "thinks" before answering; low keeps it fast and inside the free tier's tokens-per-minute limit
        payload["reasoning_effort"] = "low"
    if tools:
        payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice

    # errors never include the key, so they are safe to print
    try:
        r = httpx.post(GROQ_URL, json=payload, headers={"Authorization": f"Bearer {key}"}, timeout=timeout)
    except httpx.HTTPError as e:
        raise LLMError(f"Groq request failed: {type(e).__name__}") from None
    if r.status_code >= 400:
        try:
            detail = r.json().get("error", {}).get("message", "")
        except ValueError:
            detail = ""
        raise LLMError(f"Groq request failed: HTTP {r.status_code} {detail[:200]}".strip())

    return r.json()["choices"][0]["message"]
