"""The public /stats page: plain HTML with inline CSS, no JavaScript. Only counts, never personal data."""
from datetime import datetime
from html import escape

STYLE = """
:root {
  --bg: #f6f7f4; --card: #ffffff; --text: #1d2420; --muted: #5d6862; --line: #e3e7e2;
  --accent: #1f7a4d; --accent-soft: #e3f2ea; --bar: #2f9e63;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #111613; --card: #1a211d; --text: #e8ede9; --muted: #9aa69f; --line: #2a332e;
    --accent: #5fd39a; --accent-soft: #1d3328; --bar: #4cc287;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--text);
  font: 16px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans", "Noto Sans Devanagari", sans-serif;
}
main { max-width: 680px; margin: 0 auto; padding: 32px 16px 48px; }
h1 { font-size: 28px; line-height: 1.2; margin: 0 0 6px; }
h2 { font-size: 15px; font-weight: 600; color: var(--muted); margin: 28px 0 10px; }
.sub { color: var(--muted); margin: 0 0 24px; }
.hero {
  background: var(--accent-soft); border-radius: 16px; padding: 22px 20px; margin-bottom: 12px;
}
.hero .num { font-size: 52px; font-weight: 700; color: var(--accent); line-height: 1; font-variant-numeric: tabular-nums; }
.hero .label { font-weight: 600; margin-top: 8px; }
.hero .note { color: var(--muted); font-size: 14px; margin-top: 2px; }
.grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 16px; }
.card .num { font-size: 30px; font-weight: 700; line-height: 1.1; font-variant-numeric: tabular-nums; }
.card .label { color: var(--muted); font-size: 14px; margin-top: 4px; }
.lang { background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 6px 16px; }
.row { display: grid; grid-template-columns: 76px 1fr 44px; align-items: center; gap: 12px; padding: 10px 0; }
.row + .row { border-top: 1px solid var(--line); }
.track { height: 8px; background: var(--line); border-radius: 4px; overflow: hidden; }
.fill { height: 100%; background: var(--bar); border-radius: 4px; }
.count { text-align: right; font-variant-numeric: tabular-nums; font-weight: 600; }
footer { color: var(--muted); font-size: 14px; margin-top: 28px; }
footer a { color: var(--accent); }
"""

LANGUAGE_LABELS = [("en", "English"), ("hi", "हिंदी"), ("mr", "मराठी")]


def _page(body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HawaSaathi Impact</title>
<meta name="description" content="Live impact numbers for HawaSaathi, a free air-quality assistant on Telegram.">
<style>{STYLE}</style>
</head>
<body><main>{body}</main></body>
</html>"""


def _card(number, label: str) -> str:
    return f'<div class="card"><div class="num">{number}</div><div class="label">{escape(label)}</div></div>'


def render_stats_page(stats: dict) -> str:
    users, alerts, feedback = stats["users"], stats["alerts"], stats["feedback"]

    percent = feedback["changed_plan_percent"]
    hero_number = f"{percent}%" if percent is not None else "–"
    hero_note = (
        f'{feedback["changed_plan"]} of {feedback["answers"]} answers to "Did this change your plan?"'
        if feedback["answers"]
        else "No answers yet to \"Did this change your plan?\""
    )

    total_lang = sum(users["by_language"].values()) or 1
    language_rows = "".join(
        f'<div class="row"><div>{label}</div>'
        f'<div class="track"><div class="fill" style="width:{round(100 * users["by_language"][code] / total_lang)}%"></div></div>'
        f'<div class="count">{users["by_language"][code]}</div></div>'
        for code, label in LANGUAGE_LABELS
    )

    at = datetime.fromisoformat(stats["updated_at"])
    updated = f"{at.day} {at:%b %Y}, {at.hour % 12 or 12}:{at:%M %p} IST"  # e.g. "27 Oct 2026, 7:45 PM IST"

    body = f"""
<h1>HawaSaathi impact</h1>
<p class="sub">A free Telegram assistant that sends daily local air-quality alerts and advice in English, Hindi and Marathi.</p>

<div class="hero">
  <div class="num">{hero_number}</div>
  <div class="label">said an alert changed their plan</div>
  <div class="note">{escape(hero_note)}</div>
</div>

<div class="grid">
  {_card(users["total"], "users")}
  {_card(users["onboarded"], "finished onboarding")}
  {_card(alerts["total"], f'alerts sent ({alerts["morning"]} morning, {alerts["spike"]} spike)')}
  {_card(stats["questions_answered"], "questions answered by the AI agent")}
</div>

<h2>Users by language</h2>
<div class="lang">{language_rows}</div>

<footer>
  Last updated {escape(updated)} · refreshes every 5 minutes.<br>
  Counts only: no names, IDs, locations or questions are shown. Same numbers as <a href="/api/stats">JSON</a>.
</footer>
"""
    return _page(body)


def render_unavailable_page() -> str:
    return _page('<h1>HawaSaathi impact</h1><p class="sub">The numbers are unavailable right now. Please try again in a minute.</p>')
