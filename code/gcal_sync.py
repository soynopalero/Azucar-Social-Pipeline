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
  - upcoming active item with NO entry -> add one (since 2026-11-10)

Why the last one: until 2026-11-06 every event got an Eventbrite page, and the
calendar entry rode along with it. Eventbrite is now on request only (the
bot's "Eventbrite?" question), so events answered "No" never reached the
calendar. Adding missing entries here decouples the calendar from Eventbrite.
"Idea" items stay off the calendar: they aren't committed yet.
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
import time
import urllib.error
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_fb_kit import (  # noqa: E402
    BOARD_ID, COL_DATE, COL_EVENTBRITE, COL_PHASE, COL_TIME, col, fetch_items,
)

PACIFIC = ZoneInfo("America/Los_Angeles")
EVENT_HOURS = 4  # keep in sync with monday_to_eventbrite.py
SHARED_TOKEN = "azucar-gcal-2026"  # must match code/gcal_webhook.gs
# Cancelled/postponed items older than this were cleaned long ago (or by hand);
# skip them so the daily run doesn't re-probe ancient history forever.
LOOKBACK_DAYS = 14
# Active phases that never get a calendar entry. Idea = not committed yet;
# Completed = already happened.
NO_CALENDAR_PHASES = {"idea", "completed"}
LOCATION = "Azúcar at Out & About — 327 W Lewis St, Pasco, WA 99301"  # same as monday_to_eventbrite


def monday_url(item_id: str) -> str:
    # The webhook matches entries to Monday items by this "/pulses/<id>" link.
    return f"https://nopaleros-org.monday.com/boards/{BOARD_ID}/pulses/{item_id}"


def entry_description(item_id: str, eventbrite_url: str = "") -> str:
    lines = [f"🎟️ {eventbrite_url}"] if eventbrite_url else []
    lines.append(f"📋 {monday_url(item_id)}")
    return "\n".join(lines)


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


# Apps Script web apps intermittently answer a perfectly good deployment URL
# with a bare HTTP 404 for a minute or two. Seen live 2026-09-02 and three
# times on 2026-09-08 (the probe 404'd at 19:11 and 19:15 UTC, having passed
# at 19:09) — each one failed the whole cadence workflow and paged both owners
# over a calendar clean-up. Retry those, and the usual 5xx/network blips.
RETRY_CODES = {404, 429, 500, 502, 503, 504}
ATTEMPTS = 3
BACKOFF = (5, 15)  # seconds between attempts


def _open_with_retry(req, timeout: int, what: str) -> str:
    last: Exception | None = None
    for attempt in range(1, ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code not in RETRY_CODES:
                raise
            last = e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last = e
        if attempt < ATTEMPTS:
            wait = BACKOFF[min(attempt, len(BACKOFF)) - 1]
            print(f"  … {what} failed ({last}); retry {attempt}/{ATTEMPTS - 1} in {wait}s", flush=True)
            time.sleep(wait)
    raise last  # type: ignore[misc]


def webhook_get(url: str) -> str:
    return _open_with_retry(url, 60, "webhook probe")


def webhook_post(url: str, payload: dict) -> str:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    # Apps Script answers POSTs with a 302 to googleusercontent; urllib
    # follows it as a GET, which serves the script's actual output.
    return _open_with_retry(req, 90, f"webhook sync for {payload.get('name') or payload.get('item_id')}")


def check_webhook_version(url: str) -> None:
    """The v1 deployment treats EVERY valid-token POST as a create — a sync
    payload with start/end would create a duplicate calendar entry. A GET
    probe is side-effect-free on both versions, so verify v2 before sending
    anything."""
    try:
        body = webhook_get(url)
    except OSError as e:
        # Calendar clean-up is a convenience, not part of the posting chain.
        # The workflow runs this step with continue-on-error, so this exit
        # only marks the step, never the run.
        sys.exit(f"GCAL_WEBHOOK_URL probe failed after {ATTEMPTS} attempts ({e}) — "
                 "calendar clean-up skipped this run; nothing sent, posts unaffected.")
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

        # Active items: re-date an existing entry, or add one if missing
        # (with or without an Eventbrite page).
        phase = (col(item, COL_PHASE).get("label") or "").strip().lower()
        if phase in NO_CALENDAR_PHASES:
            continue
        hour = col(item, COL_TIME).get("hour")
        if not date_iso or hour is None or date_iso < today.isoformat():
            continue
        start_utc, end_utc = event_times_utc(date_iso, hour,
                                             col(item, COL_TIME).get("minute") or 0)
        out.append({**base, "event_date": date_iso,
                    "start_utc": start_utc, "end_utc": end_utc,
                    "eventbrite_url": (col(item, COL_EVENTBRITE).get("url") or "").strip()})
    return out


def has_any_entry(url: str, item_id: str, name: str, event_date: str) -> bool:
    """Is there already an entry for this event — tagged with its Monday link,
    OR a hand-made one with the exact same title on the same day?

    The v3 webhook only applies the title+date fallback when asked to remove,
    so this asks for a removal with dry_run:true. dry_run never touches the
    calendar (the webhook skips deleteEvent); it just reports the matches.
    Read-only by construction, and it needs no Apps Script redeploy."""
    raw = webhook_post(url, {"token": SHARED_TOKEN, "action": "sync", "item_id": item_id,
                             "name": name, "status": "postponed",
                             "event_date": event_date, "dry_run": True})
    resp = json.loads(raw)
    if not resp.get("ok") or not resp.get("dry_run"):
        raise RuntimeError(f"unexpected probe answer: {raw[:200]}")
    return bool(resp.get("matched"))


def create_entry(url: str, item_id: str, name: str, start_utc: str, end_utc: str,
                 eventbrite_url: str = "") -> str:
    """Add the event to the calendar (the webhook's original create action)."""
    raw = webhook_post(url, {"token": SHARED_TOKEN, "action": "create", "name": name,
                             "start_utc": start_utc, "end_utc": end_utc,
                             "location": LOCATION,
                             "description": entry_description(item_id, eventbrite_url)})
    if raw.strip() != "ok":
        raise RuntimeError(f"webhook create answered {raw[:200]!r}")
    return raw


def ensure_entry(url: str, item_id: str, name: str, event_date: str, start_utc: str,
                 end_utc: str, eventbrite_url: str = "") -> bool:
    """Create the calendar entry unless one already exists. True if created."""
    if has_any_entry(url, item_id, name, event_date):
        return False
    create_entry(url, item_id, name, start_utc, end_utc, eventbrite_url)
    return True


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

    errors = changed = added = 0
    for p in payloads:
        label = f"{p['name'] or '(unnamed)'} ({p['item_id']}, {p['status']})"
        eb_url = p.pop("eventbrite_url", "")
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
        else:
            # Active, upcoming, and nothing tagged with its Monday link: add it
            # (unless someone already put it on the calendar by hand).
            try:
                if has_any_entry(url, p["item_id"], p["name"], p["event_date"]):
                    print(f"• {label}: already on the calendar (hand-made entry), left as is")
                elif dry:
                    added += 1
                    print(f"• {label}: would add to the calendar on {p['event_date']}")
                else:
                    create_entry(url, p["item_id"], p["name"], p["start_utc"], p["end_utc"], eb_url)
                    added += 1
                    print(f"• {label}: added to the calendar on {p['event_date']}")
            except (OSError, json.JSONDecodeError, RuntimeError) as e:
                errors += 1
                print(f"• ERROR adding {label}: {type(e).__name__}: {e}")

    verb = "would be changed" if dry else "changed"
    print(f"\n{changed} calendar entry(ies) {verb}; "
          f"{added} {'would be added' if dry else 'added'}; {errors} error(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
