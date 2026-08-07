"""
gcal_sync.py
------------
Cleanup pass for the shared "Azucar Events" Google Calendar.

The pipeline drops an entry onto the calendar when it creates an Eventbrite
event (monday_to_eventbrite.py -> code/gcal_webhook.gs), but until now nothing
removed or moved that entry when the Monday item later changed — on 2026-08-06
three stale entries (a postponed brunch and a cancelled duplicate) had to be
deleted by hand.

This script walks the Azucar Events board and, for each item, asks the Apps
Script webhook to sync the calendar:
  - phase looks Cancelled/Postponed  -> delete the matching calendar entry
  - active item whose date/time moved -> re-date the entry to match Monday
Matching happens inside the webhook, by the Monday pulse URL that the create
path bakes into every entry's description (with an exact title+date fallback
for hand-made entries).

DRY-RUN by default: reports what would change, touches nothing. Pass --live
to apply. Refuses to run against the old (v1) webhook deployment, which
doesn't understand sync payloads.

Usage (from repo root; needs MONDAY_API_KEY and GCAL_WEBHOOK_URL):
  python code/gcal_sync.py                     # dry-run, whole board
  python code/gcal_sync.py --item-id 12345     # dry-run, one item
  python code/gcal_sync.py --live              # actually delete / re-date
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_fb_kit import (  # noqa: E402
    COL_DATE, COL_EVENTBRITE, COL_PHASE, COL_TIME, col, fetch_items,
)

PACIFIC = ZoneInfo("America/Los_Angeles")
EVENT_HOURS = 4  # keep in sync with monday_to_eventbrite.py
SHARED_TOKEN = "azucar-gcal-2026"  # must match code/gcal_webhook.gs
# Cancelled/postponed items older than this were cleaned long ago (or by hand);
# skip them so the daily run doesn't re-probe ancient history forever.
LOOKBACK_DAYS = 14


def sync_status(phase_label: str | None) -> str:
    label = (phase_label or "").lower()
    if "cancel" in label:
        return "cancelled"
    if "postpon" in label:
        return "postponed"
    return "active"


def event_times_utc(date_iso: str, hour: int, minute: int) -> tuple[str, str]:
    """Same math as monday_to_eventbrite.event_times_utc (kept local so this
    script stays stdlib-only and importable without requests/Pillow)."""
    start_local = dt.datetime.fromisoformat(date_iso).replace(
        hour=hour, minute=minute, tzinfo=PACIFIC)
    end_local = start_local + dt.timedelta(hours=EVENT_HOURS)
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    return (start_local.astimezone(dt.timezone.utc).strftime(fmt),
            end_local.astimezone(dt.timezone.utc).strftime(fmt))


def webhook_get(url: str) -> str:
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def webhook_post(url: str, payload: dict) -> str:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    # Apps Script answers POSTs with a 302 to googleusercontent; urllib
    # follows it as a GET, which serves the script's actual output.
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read().decode("utf-8", "replace")


def check_webhook_version(url: str) -> None:
    """The v1 deployment treats EVERY valid-token POST as a create — a sync
    payload with start/end would create a duplicate calendar entry. A GET
    probe is side-effect-free on both versions, so verify v2 before sending
    anything."""
    try:
        body = webhook_get(url)
    except OSError as e:
        sys.exit(f"GCAL_WEBHOOK_URL probe failed ({e}) — aborting, nothing sent.")
    if "azucar-gcal v3" not in body:
        sys.exit(
            "The deployed Apps Script webhook is outdated (v1 can't sync;\n"
            "v2's title+date fallback could delete the wrong entry when a\n"
            "cancelled duplicate shares the real event's name and date).\n"
            "Update it first: open script.google.com, paste the current\n"
            "code/gcal_webhook.gs over the old code, then Deploy → Manage\n"
            "deployments → ✏️ Edit → Version: New version → Deploy.\n"
            "Nothing was sent; the calendar is untouched."
        )


def build_requests(items: list[dict], today: dt.date) -> list[dict]:
    cutoff = (today - dt.timedelta(days=LOOKBACK_DAYS)).isoformat()
    out = []
    for item in items:
        name = (item.get("name") or "").strip()
        date_iso = col(item, COL_DATE).get("date")
        status = sync_status(col(item, COL_PHASE).get("label"))
        base = {"token": SHARED_TOKEN, "action": "sync",
                "item_id": item["id"], "name": name, "status": status}

        if status in ("cancelled", "postponed"):
            # Clean regardless of Eventbrite state — the title+date fallback
            # also catches hand-made calendar entries.
            if date_iso and date_iso < cutoff:
                continue
            out.append({**base, "event_date": date_iso})
            continue

        # Active items: the pipeline only ever created a calendar entry
        # alongside an Eventbrite event, so items without one have nothing
        # on the calendar to re-date.
        if not (col(item, COL_EVENTBRITE).get("url") or "").strip():
            continue
        hour = col(item, COL_TIME).get("hour")
        if not date_iso or hour is None or date_iso < today.isoformat():
            continue
        start_utc, end_utc = event_times_utc(date_iso, hour,
                                             col(item, COL_TIME).get("minute") or 0)
        out.append({**base, "event_date": date_iso,
                    "start_utc": start_utc, "end_utc": end_utc})
    return out


def describe_change(c: dict, dry: bool) -> str:
    when = c.get("start", "?")[:16].replace("T", " ")
    if c.get("change") == "delete":
        return f"{'would delete' if dry else 'deleted'} '{c.get('title')}' @ {when} UTC"
    new = (c.get("new_start") or "?")[:16].replace("T", " ")
    return (f"{'would move' if dry else 'moved'} '{c.get('title')}' "
            f"@ {when} UTC -> {new} UTC")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Delete/re-date Azucar Events calendar entries whose Monday "
                    "item was cancelled, postponed, or moved (dry-run by default).")
    ap.add_argument("--live", action="store_true",
                    help="actually delete / re-date (default is a dry-run report)")
    ap.add_argument("--item-id", help="only sync this Monday item id")
    args = ap.parse_args()
    dry = not args.live

    url = os.environ.get("GCAL_WEBHOOK_URL", "").strip()
    if not url:
        print("GCAL_WEBHOOK_URL not set — nothing to sync.")
        return 0
    check_webhook_version(url)

    items = fetch_items()
    if args.item_id:
        items = [i for i in items if i["id"] == str(args.item_id)]
        if not items:
            sys.exit(f"Item {args.item_id} not found on the board.")

    today = dt.datetime.now(PACIFIC).date()
    payloads = build_requests(items, today)
    mode = "DRY-RUN (nothing will change)" if dry else "LIVE"
    print(f"=== GCal sync — {mode} — {len(payloads)} item(s) to check ===")

    errors = changed = 0
    for p in payloads:
        label = f"{p['name'] or '(unnamed)'} ({p['item_id']}, {p['status']})"
        try:
            raw = webhook_post(url, {**p, "dry_run": dry})
            resp = json.loads(raw)
        except (OSError, json.JSONDecodeError) as e:
            errors += 1
            print(f"• ERROR {label}: {type(e).__name__}: {e}")
            continue
        if not resp.get("ok"):
            errors += 1
            print(f"• ERROR {label}: {raw[:200]}")
            continue
        changes = resp.get("changes") or []
        if changes:
            changed += len(changes)
            for c in changes:
                print(f"• {label} [{resp.get('matched_by')}]: {describe_change(c, dry)}")
        elif resp.get("matched"):
            print(f"• {label}: {resp['matched']} entry(ies) already correct")
        elif p["status"] != "active":
            print(f"• {label}: no calendar entry found (already clean)")

    verb = "would be changed" if dry else "changed"
    print(f"\n{changed} calendar entry(ies) {verb}; {errors} error(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
