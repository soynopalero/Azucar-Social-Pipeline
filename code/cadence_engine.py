#!/usr/bin/env python3
"""
cadence_engine.py
-----------------
Read the Azucar Events Monday board and compute the social-media posting
SCHEDULE for each eligible event, following the agreed cadence.

DRY-RUN ONLY (for now): it prints and (with --write) saves a preview of what it
WOULD queue. It does NOT post anything and does NOT touch posts_queue.json.
Wiring it to actually enqueue + the Telegram caption approval come next.

Cadence (Standard), anchored to weeks-before-event. If an event is created late,
it simply starts at whichever bucket applies:
    4+ weeks out : 3 posts / week
    3 weeks      : 3 posts
    2 weeks      : 5 posts
    week of      : every remaining day (incl. day-of)
Aggressive : same days, doubled (a morning AND an evening post each day).
Light      : 1/wk far out, 2 the week before, every-other-day the week of.
Off / no flyer / no price / no description / past / cancelled / completed: skipped.

Times are Pacific. Each scheduled slot becomes one Instagram + one Facebook
queue entry (matching the existing pipeline).

Usage:
    MONDAY_API_KEY=xxx  python code/cadence_engine.py            # print preview
    MONDAY_API_KEY=xxx  python code/cadence_engine.py --write    # + save to docs/
    python code/cadence_engine.py --selftest                     # offline math test
"""

import argparse
import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

MONDAY_API = "https://api.monday.com/v2"
BOARD_ID = "18414182966"
LOCAL_TZ = ZoneInfo("America/Los_Angeles")
REPO_ROOT = Path(__file__).resolve().parent.parent
PREVIEW_PATH = REPO_ROOT / "docs" / "cadence_preview.md"

# Live board column ids
COL_DATE    = "date_mm3h56jc"
COL_PHASE   = "color_mm3hz990"
COL_DESC    = "long_text_mm4nvacq"
COL_PRICE   = "text_mm4nazaw"
COL_FLYER   = "file_mm4nnwtq"
COL_CADENCE = "color_mm4nsvqh"

HIDDEN_PHASES = {"Cancelled", "Completed"}
PLATFORMS = ["instagram", "facebook"]

# Pacific time-of-day slots
SLOTS = {"morning": (11, 0), "afternoon": (15, 0), "evening": (19, 0)}

# Posts per week-bucket by cadence (week-of handled specially below)
COUNTS = {
    "standard":   {"w4plus": 3, "w3": 3, "w2": 5},
    "aggressive": {"w4plus": 3, "w3": 3, "w2": 5},   # doubled via 2 slots/day
    "light":      {"w4plus": 1, "w3": 1, "w2": 2},
}
HORIZON_WEEKS = 6  # don't start posting earlier than this many weeks out


# ---------- Monday ----------
def monday_query(query, variables):
    key = (os.environ.get("MONDAY_API_KEY") or "").strip()
    if not key:
        print("MONDAY_API_KEY not set. Export it locally, or add it as a repo secret for the workflow.")
        sys.exit(1)
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        MONDAY_API, data=body,
        headers={"Content-Type": "application/json", "Authorization": key, "API-Version": "2024-10"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    if "errors" in data:
        raise RuntimeError(json.dumps(data["errors"]))
    return data["data"]


def fetch_events():
    cursor, items = None, []
    while True:
        data = monday_query(
            """
            query($boardId: ID!, $cursor: String) {
              boards(ids: [$boardId]) {
                items_page(limit: 100, cursor: $cursor) {
                  cursor
                  items {
                    id name
                    column_values {
                      id type text value
                      ... on StatusValue { label index }
                      ... on DateValue { date time }
                      ... on LongTextValue { text }
                    }
                  }
                }
              }
            }
            """,
            {"boardId": BOARD_ID, "cursor": cursor},
        )
        page = data["boards"][0]["items_page"]
        items.extend(page["items"])
        cursor = page.get("cursor")
        if not cursor:
            break
    return [parse_item(it) for it in items]


def parse_item(item):
    cv = {c["id"]: c for c in item.get("column_values", [])}

    def txt(cid):
        c = cv.get(cid)
        if not c:
            return None
        if c.get("type") == "long_text":
            try:
                v = json.loads(c.get("value") or "null")
                if isinstance(v, dict):
                    return (v.get("text") or "").strip() or None
            except (json.JSONDecodeError, TypeError):
                pass
        return (c.get("text") or "").strip() or None

    date_c  = cv.get(COL_DATE) or {}
    flyer_c = cv.get(COL_FLYER) or {}
    phase_c = cv.get(COL_PHASE) or {}
    cad_c   = cv.get(COL_CADENCE) or {}

    files = []
    raw = flyer_c.get("value")
    if raw:
        try:
            v = json.loads(raw)
            if isinstance(v, dict) and isinstance(v.get("files"), list):
                files = v["files"]
        except (json.JSONDecodeError, TypeError):
            pass

    return {
        "id": item["id"],
        "name": (item.get("name") or "").strip() or None,
        "date": date_c.get("date"),
        "phase": phase_c.get("label"),
        "cadence": (cad_c.get("label") or "").strip().lower() or None,
        "description": txt(COL_DESC),
        "price": txt(COL_PRICE),
        "has_flyer": len(files) > 0,
    }


# ---------- Eligibility ----------
def eligibility(e, today):
    reasons = []
    if not e["date"]:
        reasons.append("no date")
    else:
        try:
            if dt.date.fromisoformat(e["date"]) < today:
                reasons.append("date in the past")
        except ValueError:
            reasons.append("bad date")
    if e["phase"] in HIDDEN_PHASES:
        reasons.append(f"phase = {e['phase']}")
    cad = e["cadence"]
    if not cad:
        reasons.append("no cadence set")
    elif cad == "off":
        reasons.append("cadence = Off")
    elif cad not in COUNTS:
        reasons.append(f"unknown cadence '{cad}'")
    if not e["has_flyer"]:
        reasons.append("no flyer")
    if not e["price"]:
        reasons.append("no price")
    if not e["description"]:
        reasons.append("no description")
    return reasons


# ---------- Schedule math ----------
def _spread(days, n):
    """Pick n days roughly evenly spread across the sorted list `days`."""
    if n <= 0 or not days:
        return []
    if n >= len(days):
        return list(days)
    if n == 1:
        return [days[len(days) // 2]]
    step = (len(days) - 1) / (n - 1)
    idx = sorted({round(i * step) for i in range(n)})
    return [days[i] for i in idx]


def schedule_for(event_date, cadence, today, horizon_weeks=HORIZON_WEEKS):
    """Return a sorted list of (date, slot_name) for the given cadence."""
    picks = []
    toggle = 0
    for w in range(horizon_weeks, 0, -1):
        win_start = event_date - dt.timedelta(days=w * 7 - 1)
        win_end   = event_date - dt.timedelta(days=(w - 1) * 7)
        lo = max(win_start, today)
        hi = min(win_end, event_date)
        if lo > hi:
            continue
        days = [lo + dt.timedelta(days=i) for i in range((hi - lo).days + 1)]
        if w == 1:  # week of
            if cadence == "light":
                chosen = days[::2]
                if days and days[-1] not in chosen:
                    chosen.append(days[-1])  # always include day-of
            else:
                chosen = days  # every remaining day
        else:
            bucket = "w2" if w == 2 else ("w3" if w == 3 else "w4plus")
            chosen = _spread(days, COUNTS[cadence][bucket])
        for d in chosen:
            slot = "evening" if toggle % 2 == 0 else "morning"
            toggle += 1
            picks.append((d, slot))
            if cadence == "aggressive":
                picks.append((d, "morning" if slot == "evening" else "evening"))
    seen, out = set(), []
    for d, s in sorted(picks, key=lambda x: (x[0], SLOTS[x[1]])):
        if (d, s) in seen:
            continue
        seen.add((d, s))
        out.append((d, s))
    return out


def to_local_dt(d, slot):
    h, m = SLOTS[slot]
    return dt.datetime(d.year, d.month, d.day, h, m, tzinfo=LOCAL_TZ)


def fmt_dt(x):
    # Portable (no platform-specific %-d / %-I): "Sat Jul 18, 7:00 PM"
    return x.strftime("%a %b ") + str(x.day) + ", " + x.strftime("%I:%M %p").lstrip("0")


# ---------- Preview ----------
def build_preview(events, today, now):
    eligible, skipped = [], []
    for e in events:
        r = eligibility(e, today)
        (skipped if r else eligible).append((e, r))

    stamp = now.astimezone(LOCAL_TZ).strftime("%Y-%m-%d %H:%M %Z")
    lines = [
        "# Social cadence - dry-run preview",
        "",
        f"Generated {stamp} - **nothing posted, queue untouched**",
        "",
        f"Eligible events: **{len(eligible)}** - Skipped: **{len(skipped)}**",
        "",
    ]

    total = 0
    for e, _ in sorted(eligible, key=lambda x: x[0]["date"]):
        ed = dt.date.fromisoformat(e["date"])
        sched = schedule_for(ed, e["cadence"], today)
        future = [(d, s) for (d, s) in sched if to_local_dt(d, s) >= now]
        entries = len(future) * len(PLATFORMS)
        total += entries
        lines += [
            f"## {e['name']} - {e['date']}  ({e['cadence'].capitalize()})",
            f"{len(future)} posts x {len(PLATFORMS)} platforms = **{entries}** queue entries",
            "",
            "| When (Pacific) | Slot |",
            "|---|---|",
        ]
        lines += [f"| {fmt_dt(to_local_dt(d, s))} | {s} |" for d, s in future]
        lines.append("")

    if skipped:
        lines += ["---", "", "### Skipped (not eligible yet)", ""]
        for e, r in sorted(skipped, key=lambda x: (x[0]["name"] or "")):
            lines.append(f"- **{e['name'] or '(unnamed)'}** - {', '.join(r)}")
        lines.append("")

    lines += [f"**Total queue entries that would be created: {total}**", ""]
    return "\n".join(lines)


# ---------- Offline self-test ----------
def selftest():
    today = dt.date(2026, 7, 1)
    event = dt.date(2026, 8, 8)  # ~5.4 weeks out (a Saturday)
    print(f"Self-test - event {event}, today {today} ({(event - today).days} days out)\n")
    for cad in ("standard", "aggressive", "light"):
        sched = schedule_for(event, cad, today)
        print(f"=== {cad.upper()}: {len(sched)} posts ({len(sched) * len(PLATFORMS)} queue entries) ===")
        for d, s in sched:
            print(f"  {d.strftime('%a %Y-%m-%d')}  {s}")
        print()


def main():
    ap = argparse.ArgumentParser(description="Compute the social cadence schedule (dry-run).")
    ap.add_argument("--write", action="store_true", help="save preview to docs/cadence_preview.md")
    ap.add_argument("--selftest", action="store_true", help="offline schedule-math test (no Monday call)")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    now = dt.datetime.now(dt.timezone.utc)
    today = now.astimezone(LOCAL_TZ).date()
    md = build_preview(fetch_events(), today, now)
    print(md)
    if args.write:
        PREVIEW_PATH.parent.mkdir(exist_ok=True)
        PREVIEW_PATH.write_text(md, encoding="utf-8")
        print(f"\nWrote {PREVIEW_PATH}")


if __name__ == "__main__":
    main()
