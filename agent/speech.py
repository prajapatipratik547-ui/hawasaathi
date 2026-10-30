"""Voice messages -> text, with Groq's Whisper (OpenAI-compatible speech-to-text, free tier).
Like chat() in agent/llm.py, everything goes through one function so the provider can be swapped.
"""
import os

import httpx

GROQ_STT_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
STT_MODEL = "whisper-large-v3"  # the most accurate Whisper for Hindi and Marathi


def transcribe(audio: bytes, lang: str = "en", filename: str = "voice.ogg") -> str:
    """Text of a voice message ("" if nothing was said). Raises RuntimeError on failure; errors never include the key."""
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is not set")

    data = {"model": STT_MODEL, "response_format": "json", "temperature": "0"}
    if lang in ("hi", "mr"):
        # without a hint, Whisper sometimes writes Hindi in Urdu script; the hint keeps it in Devanagari
        data["language"] = lang

    try:
        r = httpx.post(
            GROQ_STT_URL,
            headers={"Authorization": f"Bearer {key}"},
            data=data,
            files={"file": (filename, audio)},
            timeout=20.0,
        )
    except httpx.HTTPError as e:
        raise RuntimeError(f"Groq transcription failed: {type(e).__name__}") from None
    if r.status_code >= 400:
        try:
            detail = r.json().get("error", {}).get("message", "")
        except ValueError:
            detail = ""
        raise RuntimeError(f"Groq transcription failed: HTTP {r.status_code} {detail[:200]}".strip())
    return (r.json().get("text") or "").strip()
