#!/usr/bin/env python3
"""
fb_event_reminders.py — nag whoever created an event until its Facebook event exists.

Why
---
Facebook events cannot be created by any API we can use (see
memory/project_eventbrite_integration.md), so each one is made by hand from
the FB Event Kit. They were getting forgotten (Pedro, 2026-11-06), so the
pipeline now asks.

What it does
------------
Runs right after build_fb_kit.py in fb-kit.yml (every 30 min). For every
event on the kit (upcoming, no Facebook Event URL on the board) it DMs the
person who created the event on Telegram — the board's "Created by" chat id,
else the default chat — with two buttons:

    ✅ Yes, it's live   -> the bot asks for the link and writes it to the board
    ⏳ Not yet          -> the bot snoozes the reminder for a day

Rhythm: the first ask as soon as the card appears, a second one an hour
later if nobody tapped, then once a day until the link is on the board, the
event date passes, or MAX_ASKS is reached. State lives in the board's
"FB Event Reminder" text column as JSON {"n": asks so far, "last": iso,
"snooze": iso|null}; the bot clears it when the link is saved.

    python code/fb_event_reminders.py            # send what is due
    python code/fb_event_reminders.py --dry-run  # print what would be sent
    python code/fb_event_reminders.py --selftest # offline schedule rules
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
KIT_JSON = REPO_ROOT / "docs" / "fb_kit.json"
KIT_URL = "https://soynopalero.github.io/Azucar-Social-Pipeline/fb-kit.html"

COL_CREATED_BY = "text_mm4wnp8g"
COL_FB_REMINDER = "text_mm8v85st"

FIRST_FOLLOWUP_MIN = 60     # second ask, one hour after the first
DAILY_HOURS = 24            # then once a day
MAX_ASKS = 8                # a week of daily asks after the first two


def due(state: dict | None, now: dt.datetime, event_date: dt.date) -> bool:
    """Should we ask (again) right now?"""
    if event_date < now.date():
        return False
    state = state or {}
    n = int(state.get("n") or 0)
    if n >= MAX_ASKS:
        return False
    snooze = _parse(state.get("snooze"))
    if snooze and now < snooze:
        return False
    last = _parse(state.get("last"))
    if n == 0 or not last:
        return True
    gap = dt.timedelta(minutes=FIRST_FOLLOWUP_MIN) if n == 1 else dt.timedelta(hours=DAILY_HOURS)
    return now - last >= gap


def _parse(s) -> dt.datetime | None:
    if not s:
        return None
    try:
        d = dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return None


def message_for(ev: dict, n: int) -> str:
    head = "📘 *Facebook event check*" if n == 0 else f"⏰ *Reminder {n + 1} — Facebook event*"
    return (
        f"{head}\n\n"
        f"*{ev['name']}* — {ev['date_display']} at {ev['start_time']}\n\n"
        "Have you created the Facebook event for this one, and is it live?\n\n"
        f"Everything to copy-paste is on the kit:\n{KIT_URL}"
    )


def keyboard(item_id: str) -> dict:
    return {"inline_keyboard": [[
        {"text": "✅ Yes, it's live", "callback_data": f"fbev:yes:{item_id}"},
        {"text": "⏳ Not yet", "callback_data": f"fbev:later:{item_id}"},
    ]]}


def tg_send(chat_id: str, text: str, reply_markup: dict) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set")
    body = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown", "reply_markup": reply_markup}
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=json.dumps(body).encode(), headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        out = json.loads(r.read())
    if not out.get("ok"):
        raise RuntimeError(f"Telegram refused: {out}")


def main() -> int:
    dry = "--dry-run" in sys.argv
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from build_fb_kit import BOARD_ID, COL_DATE, COL_FB_EVENT, col, fetch_items, monday_query  # noqa: E402

    if not KIT_JSON.exists():
        print("no docs/fb_kit.json — run build_fb_kit.py first")
        return 0
    kit = {e["item_id"]: e for e in json.loads(KIT_JSON.read_text(encoding="utf-8")).get("events", [])}
    if not kit:
        print("kit is empty — nothing to ask about")
        return 0

    now = dt.datetime.now(dt.timezone.utc)
    default_chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    items = {i["id"]: i for i in fetch_items()}
    sent = failed = 0
    for item_id, ev in kit.items():
        item = items.get(item_id)
        if not item:
            continue
        if (col(item, COL_FB_EVENT).get("url") or "").strip():
            continue  # filled since the kit was built
        try:
            state = json.loads(col(item, COL_FB_REMINDER).get("text") or "{}") or {}
        except json.JSONDecodeError:
            state = {}
        event_date = dt.date.fromisoformat(col(item, COL_DATE).get("date") or ev["date_iso"])
        if not due(state, now, event_date):
            continue
        n = int(state.get("n") or 0)
        chat = (col(item, COL_CREATED_BY).get("text") or "").strip() or default_chat
        if not chat:
            print(f"  skip {ev['name']!r}: no creator chat and no TELEGRAM_CHAT_ID")
            continue
        print(f"  ask #{n + 1} -> chat {chat}: {ev['name']!r} ({ev['date_iso']})")
        if dry:
            continue
        try:
            tg_send(chat, message_for(ev, n), keyboard(item_id))
            new_state = {"n": n + 1, "last": now.isoformat(timespec="seconds"), "snooze": None}
            monday_query(
                "mutation($b: ID!, $i: ID!, $c: String!, $v: String!) {"
                " change_simple_column_value(board_id: $b, item_id: $i, column_id: $c, value: $v) { id } }",
                {"b": BOARD_ID, "i": item_id, "c": COL_FB_REMINDER, "v": json.dumps(new_state)},
            )
            sent += 1
        except Exception as ex:  # one bad chat id must not stop the others
            failed += 1
            print(f"  !! {ev['name']!r}: {type(ex).__name__}: {ex}")
    print(f"reminders: {sent} sent, {failed} failed")
    return 1 if failed and not sent else 0


def selftest() -> int:
    ok = True

    def check(cond, label):
        nonlocal ok
        ok &= bool(cond)
        print(("  ok   " if cond else "  FAIL ") + label)

    now = dt.datetime(2026, 11, 10, 18, 0, tzinfo=dt.timezone.utc)
    ev = dt.date(2026, 11, 21)
    iso = lambda d: d.isoformat(timespec="seconds")
    check(due(None, now, ev), "never asked -> ask now")
    check(due({}, now, ev), "empty state -> ask now")
    check(not due({"n": 1, "last": iso(now - dt.timedelta(minutes=30))}, now, ev), "asked 30 min ago -> wait")
    check(due({"n": 1, "last": iso(now - dt.timedelta(minutes=61))}, now, ev), "asked once, 61 min ago -> second ask")
    check(not due({"n": 2, "last": iso(now - dt.timedelta(hours=5))}, now, ev), "asked twice, 5h ago -> wait for the daily slot")
    check(due({"n": 2, "last": iso(now - dt.timedelta(hours=25))}, now, ev), "asked twice, 25h ago -> daily ask")
    check(not due({"n": 2, "last": iso(now - dt.timedelta(hours=25)), "snooze": iso(now + dt.timedelta(hours=2))}, now, ev), "snoozed -> wait")
    check(due({"n": 2, "last": iso(now - dt.timedelta(hours=25)), "snooze": iso(now - dt.timedelta(hours=1))}, now, ev), "snooze expired -> ask")
    check(not due({"n": MAX_ASKS, "last": iso(now - dt.timedelta(days=3))}, now, ev), "cap reached -> stop")
    check(not due(None, now, dt.date(2026, 11, 9)), "event already happened -> never ask")
    check(due({"n": 1, "last": "garbage"}, now, ev), "unparseable last date -> asks again rather than crashing")
    m = message_for({"name": "Queersgiving", "date_display": "Sun, Nov 22", "start_time": "8:00 PM"}, 0)
    check("Queersgiving" in m and KIT_URL in m and "Reminder" not in m, "first message has the event and the kit link")
    check("Reminder 3" in message_for({"name": "x", "date_display": "d", "start_time": "t"}, 2), "later messages count the reminders")
    kb = keyboard("123")["inline_keyboard"][0]
    check([b["callback_data"] for b in kb] == ["fbev:yes:123", "fbev:later:123"], "buttons carry the item id")
    print("All reminder cases passed." if ok else "Some reminder cases FAILED.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
