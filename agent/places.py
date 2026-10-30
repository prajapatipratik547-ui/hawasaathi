"""Understand whatever a user types as a place: typos, Hinglish, Devanagari, landmarks, other countries.
The LLM only cleans up the text; the coordinates always come from the map search (air/geocode.py).
"""
import json
import re
from typing import Optional

from agent.llm import chat

# a small, fast model with its own free-tier limit, so place lookups don't use up the Q&A model's
PLACE_MODEL = "openai/gpt-oss-20b"

PROMPT = """You turn what a user typed into a place name for a map search. The user is most likely in India, but may name any place in the world.
- Fix spelling ("Lohegoan" -> "Lohegaon", "Banglore" -> "Bengaluru", "Chenai" -> "Chennai").
- The text may come from speech recognition, so words can be misheard: use the real place it sounds like ("कोत्रूट पुने" -> "Kothrud, Pune").
- Write Hindi/Marathi script and Hinglish as the usual English name ("लोहगाव, पुणे" -> Lohegaon, Pune).
- Drop filler words ("I live in", "near", "mera ghar ... me hai").
- Keep the most specific place the user means. Never replace an area or landmark with just its city.
- Expand short forms ("PCMC" -> "Pimpri-Chinchwad", "CP Delhi" -> "Connaught Place").
- A landmark is fine as the place ("near Pune station" -> "Pune Railway Station").
- If no city is given for a place in India, add the most likely city.
Reply with JSON only:
{"place": "<area or city, in English>", "city": "<city or district, or empty>", "state": "<state or region, or empty>", "country_code": "<ISO 3166-1 alpha-2, e.g. IN, GB>"}
If the text is not a place at all, reply {"place": ""}."""


def understand_place(text: str) -> Optional[dict]:
    """{"place", "city", "state", "country_code"} for the user's text, or None if it isn't a place
    or the LLM is unavailable (then the caller uses a plain map search instead)."""
    try:
        reply = chat(
            [{"role": "system", "content": PROMPT}, {"role": "user", "content": text[:200]}],
            timeout=8.0,
            model=PLACE_MODEL,
            json_mode=True,
        )
        place = json.loads(reply.get("content") or "{}")
    except Exception as e:
        print(f"places: using plain map search: {e}")
        return None
    if not isinstance(place, dict) or not str(place.get("place") or "").strip():
        return {"place": ""}  # the LLM says it's not a place
    country = str(place.get("country_code") or "IN").upper()
    return {
        "place": str(place["place"]).strip(),
        "city": str(place.get("city") or "").strip(),
        "state": str(place.get("state") or "").strip(),
        "country_code": country if re.fullmatch(r"[A-Z]{2}", country) else "IN",
    }
