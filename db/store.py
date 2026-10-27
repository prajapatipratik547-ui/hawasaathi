"""Tiny Supabase store using the REST API (PostgREST) directly with httpx."""
import os
import time
from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

import httpx


def _base() -> str:
    url = os.getenv("SUPABASE_URL")
    if not url:
        raise RuntimeError("SUPABASE_URL is not set")
    return url.rstrip("/") + "/rest/v1"


def _headers(prefer: Optional[str] = None) -> dict:
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not key:
        raise RuntimeError("SUPABASE_SERVICE_KEY is not set")
    headers = {"apikey": key, "Content-Type": "application/json"}
    # legacy service_role keys are JWTs (start with "eyJ") and also go in Authorization;
    # new secret keys (sb_secret_...) only go in "apikey"
    if key.startswith("eyJ"):
        headers["Authorization"] = f"Bearer {key}"
    if prefer:
        headers["Prefer"] = prefer
    return headers


def _request(method: str, table: str, params: Optional[dict] = None, json=None, prefer: Optional[str] = None):
    """Make a request and return the JSON body (or None if empty)."""
    r = _send(method, table, params=params, json=json, prefer=prefer)
    return r.json() if r.content else None


def _send(method: str, table: str, params: Optional[dict] = None, json=None, prefer: Optional[str] = None) -> httpx.Response:
    # errors never include the URL or key, so they are safe to print
    for attempt in (1, 2):
        try:
            r = httpx.request(method, f"{_base()}/{table}", params=params, json=json, headers=_headers(prefer), timeout=10.0)
            break
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            # the request never reached Supabase, so it's safe to retry once
            if attempt == 2:
                raise RuntimeError(f"Supabase {method} {table} failed: {type(e).__name__}") from None
            time.sleep(1)
        except httpx.HTTPError as e:
            raise RuntimeError(f"Supabase {method} {table} failed: {type(e).__name__}") from None
    if r.status_code >= 400:
        raise RuntimeError(f"Supabase {method} {table} failed: HTTP {r.status_code} {r.text[:200]}")
    return r


def get_user(telegram_id: int) -> Optional[dict]:
    rows = _request("GET", "users", params={"telegram_id": f"eq.{telegram_id}", "select": "*"})
    return rows[0] if rows else None


def upsert_user(telegram_id: int, **fields) -> None:
    """Create the user, or update only the given fields if they already exist."""
    row = {"telegram_id": telegram_id, **fields, "updated_at": datetime.now(timezone.utc).isoformat()}
    _request(
        "POST",
        "users",
        params={"on_conflict": "telegram_id"},
        json=row,
        prefer="resolution=merge-duplicates,return=minimal",
    )


def list_ready_users() -> list:
    """Users who finished onboarding (all 3 questions answered and a location saved)."""
    return _request(
        "GET",
        "users",
        params={
            "state": "eq.ready",
            "outdoor_worker": "not.is.null",
            "lat": "not.is.null",
            "chat_id": "not.is.null",
            "select": "*",
        },
    )


def last_alert(telegram_id: int, type: Optional[str] = None) -> Optional[dict]:
    """The user's most recent alert (of this type, if given), or None."""
    params = {"telegram_id": f"eq.{telegram_id}", "order": "sent_at.desc", "limit": 1, "select": "*"}
    if type:
        params["type"] = f"eq.{type}"
    rows = _request("GET", "alerts", params=params)
    return rows[0] if rows else None


def log_alert(telegram_id: int, type: str, aqi: Optional[int], category: Optional[str]) -> int:
    """Save a sent alert ('morning' or 'spike') and return its id."""
    rows = _request(
        "POST",
        "alerts",
        json={"telegram_id": telegram_id, "type": type, "aqi": aqi, "category": category},
        prefer="return=representation",
    )
    return rows[0]["id"]


def delete_alert(alert_id: int) -> None:
    """Used when an alert was logged but couldn't be sent, so the next tick tries again."""
    _request("DELETE", "alerts", params={"id": f"eq.{alert_id}"}, prefer="return=minimal")


def has_feedback(alert_id: int) -> bool:
    rows = _request("GET", "feedback", params={"alert_id": f"eq.{alert_id}", "select": "id", "limit": 1})
    return bool(rows)


def log_feedback(alert_id: int, telegram_id: int, changed_plan: bool) -> None:
    _request(
        "POST",
        "feedback",
        json={"alert_id": alert_id, "telegram_id": telegram_id, "changed_plan": changed_plan},
        prefer="return=minimal",
    )


def count_questions_today(telegram_id: int, limit: int) -> int:
    """How many questions the user asked since midnight IST (counts up to `limit`, which is all we need)."""
    midnight = datetime.now(ZoneInfo("Asia/Kolkata")).replace(hour=0, minute=0, second=0, microsecond=0)
    rows = _request(
        "GET",
        "questions",
        params={"telegram_id": f"eq.{telegram_id}", "answered_at": f"gte.{midnight.isoformat()}", "select": "id", "limit": limit},
    )
    return len(rows or [])


def log_question(telegram_id: int, question: str) -> None:
    _request(
        "POST",
        "questions",
        json={"telegram_id": telegram_id, "question": question},
        prefer="return=minimal",
    )


# --- public stats (counts only, no personal data) ---

STATS_CACHE_SECONDS = 300
_stats_cache = {"at": 0.0, "stats": None}


def count_rows(table: str, **filters) -> int:
    """Count matching rows without downloading them: HEAD request with Prefer: count=exact.
    Filters use PostgREST syntax, e.g. count_rows("users", language="eq.hi").
    """
    r = _send("HEAD", table, params={"select": "*", **filters}, prefer="count=exact")
    # Content-Range looks like "*/42" (or "0-24/42")
    return int(r.headers.get("content-range", "*/0").split("/")[-1])


def get_stats() -> dict:
    """Numbers for the /stats page, cached for 5 minutes."""
    if _stats_cache["stats"] and time.monotonic() - _stats_cache["at"] < STATS_CACHE_SECONDS:
        return _stats_cache["stats"]

    morning = count_rows("alerts", type="eq.morning")
    spike = count_rows("alerts", type="eq.spike")
    answers = count_rows("feedback")
    changed = count_rows("feedback", changed_plan="eq.true")
    stats = {
        "users": {
            "total": count_rows("users"),
            "onboarded": count_rows("users", outdoor_worker="not.is.null"),
            "by_language": {lang: count_rows("users", language=f"eq.{lang}") for lang in ("en", "hi", "mr")},
        },
        "alerts": {"total": morning + spike, "morning": morning, "spike": spike},
        "feedback": {
            "answers": answers,
            "changed_plan": changed,
            "changed_plan_percent": round(100 * changed / answers) if answers else None,
        },
        "questions_answered": count_rows("questions"),
        "updated_at": datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(timespec="seconds"),
    }

    _stats_cache.update(at=time.monotonic(), stats=stats)
    return stats
