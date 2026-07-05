"""
Monday → Eventbrite: create + publish an Eventbrite event from a Monday item,
then write the Eventbrite URL back to the board.

The write-back is the handshake for the rest of the chain: the website's
"Get tickets" button reads that column, and the FB Event Kit lists any event
that has an Eventbrite URL but no Facebook Event URL yet.

Usage (from repo root):
  python code/monday_to_eventbrite.py --item-id 12424060899
  python code/monday_to_eventbrite.py --item-id 12424060899 --dry-run
  python code/monday_to_eventbrite.py --all-pending            # every ready item
  python code/monday_to_eventbrite.py --all-pending --dry-run  # preview first

Needs MONDAY_API_KEY in the environment or in code/.env.

Hard-won API facts baked in (see memory/project_eventbrite_integration.md):
- description.html in the CREATE post only; never send summary too
  (SUMMARY_DESCRIPTION_CONFLICT) and never touch structured_content.
- Venue 298365330 must keep its lat/long (a null there breaks EB's editor).
- Paid tickets blocked until account tax settings are done (EVENT_TAX_
  SETTINGS_MISSING) -> free RSVP ticket named "...— $X cover at door".
- Portrait flyers get a generated 1920x1005 blurred-wings cover (same
  make_fb_cover used by the FB kit) so EB's wide cover band never crops art.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_fb_kit import (  # noqa: E402
    BOARD_ID, COL_AGE, COL_COVER, COL_DATE, COL_EVENTBRITE, COL_FLYER,
    COL_LONG_DESC, COL_PHASE, COL_PRICE, COL_SHORT_DESC, COL_TIME,
    HIDDEN_PHASES, LANDSCAPE_OK, col, fetch_items, long_text, make_fb_cover,
    monday_query,
)

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
WORK_DIR = REPO_ROOT / ".eb_covers"

EB_TOKEN = "RZFOGQGUYBI24B5J43XC"
EB_ORG = "2861869150261"
EB_VENUE = "298365330"
EB_BASE = "https://www.eventbriteapi.com/v3"
EB_AUTH = {"Authorization": f"Bearer {EB_TOKEN}"}
EB_JSON = {**EB_AUTH, "Content-Type": "application/json"}

PACIFIC = ZoneInfo("America/Los_Angeles")
VENUE_LINE = "📍 Azúcar at Out &amp; About — 327 W Lewis St, Pasco WA"
EVENT_HOURS = 4  # default duration

SPANISH_DAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
SPANISH_MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def load_dotenv() -> None:
    env_file = Path(__file__).resolve().parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def fail(label: str, resp: requests.Response) -> None:
    sys.exit(f"!! {label} FAILED — HTTP {resp.status_code}\n{resp.text}")


# ─── Monday helpers ──────────────────────────────────────────────────────────

def monday_download_asset(item: dict, col_id: str, dest_stem: str) -> Path | None:
    c = col(item, col_id)
    try:
        files = json.loads(c.get("value") or "{}").get("files") or []
    except (json.JSONDecodeError, TypeError):
        files = []
    if not files:
        return None
    asset_id = files[0].get("assetId") or files[0].get("asset_id") or files[0].get("id")
    if not asset_id:
        return None
    data = monday_query(
        "query($ids: [ID!]!) { assets(ids: $ids) { public_url url } }",
        {"ids": [str(asset_id)]},
    )
    a = (data.get("assets") or [None])[0]
    if not a:
        return None
    url = a.get("public_url") or a.get("url")
    ext = Path(urllib.parse.urlparse(url).path).suffix or ".jpg"
    if ext.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
        ext = ".jpg"
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    out = WORK_DIR / f"{dest_stem}{ext}"
    with urllib.request.urlopen(url, timeout=30) as r:
        out.write_bytes(r.read())
    return out


def monday_write_eventbrite_url(item_id: str, eb_url: str, label: str) -> None:
    monday_query(
        """
        mutation($boardId: ID!, $itemId: ID!, $columnId: String!, $value: JSON!) {
          change_column_value(board_id: $boardId, item_id: $itemId,
                              column_id: $columnId, value: $value) { id }
        }
        """,
        {
            "boardId": BOARD_ID,
            "itemId": item_id,
            "columnId": COL_EVENTBRITE,
            "value": json.dumps({"url": eb_url, "text": label}),
        },
    )


# ─── Field builders ──────────────────────────────────────────────────────────

def event_times_utc(date_iso: str, hour: int, minute: int) -> tuple[str, str]:
    start_local = dt.datetime.fromisoformat(date_iso).replace(
        hour=hour, minute=minute, tzinfo=PACIFIC)
    end_local = start_local + dt.timedelta(hours=EVENT_HOURS)
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    return (start_local.astimezone(dt.timezone.utc).strftime(fmt),
            end_local.astimezone(dt.timezone.utc).strftime(fmt))


def build_description_html(item: dict, date_iso: str, hour: int, minute: int) -> str:
    body = long_text(item, COL_LONG_DESC) or long_text(item, COL_SHORT_DESC) or ""
    paragraphs = [
        "<p>" + html.escape(p.strip()).replace("\n", "<br>") + "</p>"
        for p in re.split(r"\n\s*\n", body) if p.strip()
    ]

    d = dt.date.fromisoformat(date_iso)
    fecha = f"{SPANISH_DAYS[d.weekday()]} {d.day} de {SPANISH_MONTHS[d.month - 1]}, {d.year}"
    suffix = "AM" if hour < 12 else "PM"
    h12 = 12 if hour % 12 == 0 else hour % 12
    show = f"{h12}:{minute:02d} {suffix}"

    age = (col(item, COL_AGE).get("label") or "").strip()
    price = (col(item, COL_PRICE).get("text") or "").strip()
    extras = " · ".join(x for x in [age or None, f"Cover {price}" if price else None] if x)

    logistics = f"<p>🗓️ {fecha} — Show {show}<br>{VENUE_LINE}"
    if extras:
        logistics += f"<br>🔞 {html.escape(extras)}"
    logistics += "</p>"

    return "".join(paragraphs) + logistics


def resolve_eb_cover(item: dict) -> Path | None:
    """Wide cover for the Eventbrite logo slot. Same priority as the FB kit."""
    from PIL import Image

    custom = monday_download_asset(item, COL_COVER, f"{item['id']}_custom")
    if custom:
        return custom
    flyer = monday_download_asset(item, COL_FLYER, f"{item['id']}_flyer")
    if not flyer:
        return None
    with Image.open(flyer) as im:
        if im.width / im.height >= LANDSCAPE_OK:
            return flyer
    generated = WORK_DIR / f"{item['id']}_cover.jpg"
    make_fb_cover(flyer, generated)
    return generated


# ─── Eventbrite steps ────────────────────────────────────────────────────────

def eb_upload_image(path: Path) -> str:
    from PIL import Image

    r = requests.get(f"{EB_BASE}/media/upload/?type=image-event-logo", headers=EB_AUTH)
    if not r.ok:
        fail("upload instructions", r)
    info = r.json()
    with open(path, "rb") as f:
        r2 = requests.post(info["upload_url"], data=info["upload_data"],
                           files={"file": ("cover.jpg", f, "image/jpeg")})
    if not r2.ok:
        fail("S3 upload", r2)
    with Image.open(path) as im:
        w, h = im.size
    r3 = requests.post(f"{EB_BASE}/media/upload/", headers=EB_JSON, json={
        "upload_token": info["upload_token"],
        "crop_mask": {"top_left": {"x": 0, "y": 0}, "width": w, "height": h},
    })
    if not r3.ok:
        fail("upload confirm", r3)
    return r3.json()["id"]


def eb_create_event(item: dict, image_id: str, start_utc: str, end_utc: str,
                    desc_html: str) -> dict:
    payload = {"event": {
        "name": {"html": html.escape(item["name"].strip())},
        # description only — adding summary too triggers SUMMARY_DESCRIPTION_CONFLICT
        "description": {"html": desc_html},
        "start": {"timezone": "America/Los_Angeles", "utc": start_utc},
        "end": {"timezone": "America/Los_Angeles", "utc": end_utc},
        "venue_id": EB_VENUE,
        "currency": "USD",
        "online_event": False,
        "listed": True,
        "shareable": True,
        "logo_id": image_id,
    }}
    r = requests.post(f"{EB_BASE}/organizations/{EB_ORG}/events/",
                      headers=EB_JSON, json=payload)
    if not r.ok:
        fail("event create", r)
    return r.json()


def eb_add_ticket(event_id: str, price: str) -> None:
    name = "General Admission"
    if price and price.lower() not in {"free", "gratis"}:
        name = f"General Admission — {price} cover at door"
    r = requests.post(f"{EB_BASE}/events/{event_id}/ticket_classes/",
                      headers=EB_JSON, json={"ticket_class": {
                          "name": name, "free": True, "quantity_total": 200,
                          "minimum_quantity": 1, "maximum_quantity": 10}})
    if not r.ok:
        fail("ticket class", r)


def eb_publish(event_id: str) -> None:
    r = requests.post(f"{EB_BASE}/events/{event_id}/publish/", headers=EB_AUTH)
    if not r.ok:
        fail("publish", r)


def refresh_fb_kit_now() -> None:
    """Rebuild the FB kit and push it immediately so the page updates in ~1 min
    instead of waiting for the 30-min cron (which stays on as the backstop)."""
    import subprocess

    import build_fb_kit
    print("\nRefreshing FB kit...")
    build_fb_kit.main()

    def git(*args, check=True):
        return subprocess.run(["git", *args], cwd=REPO_ROOT, check=check)

    try:
        git("add", "docs/fb_kit.json", "docs/media/fb-kit")
        unchanged = git("diff", "--cached", "--quiet", "-I", '"generated_at"',
                        check=False).returncode == 0
        if unchanged:
            git("reset", "-q", "docs/fb_kit.json", "docs/media/fb-kit")
            print("FB kit unchanged — nothing to push.")
            return
        git("commit", "-m", "FB kit refresh [skip ci]")
        git("pull", "--rebase", "--autostash")
        git("push")
        print("FB kit pushed — the kit page updates in ~1 minute.")
    except subprocess.CalledProcessError as e:
        print(f"FB kit push failed ({e}) — no harm done, the 30-min cron will catch it.")


# ─── Per-item pipeline ───────────────────────────────────────────────────────

def readiness(item: dict) -> tuple[bool, str]:
    date_iso = col(item, COL_DATE).get("date")
    if not date_iso:
        return False, "no event date"
    if date_iso < dt.date.today().isoformat():
        return False, "date is in the past"
    if col(item, COL_PHASE).get("label") in HIDDEN_PHASES:
        return False, f"phase is {col(item, COL_PHASE).get('label')}"
    if (col(item, COL_EVENTBRITE).get("url") or "").strip():
        return False, "already has an Eventbrite URL"
    if col(item, COL_TIME).get("hour") is None:
        return False, "no event time"
    if not (long_text(item, COL_LONG_DESC) or long_text(item, COL_SHORT_DESC)):
        return False, "no description"
    return True, "ready"


def process_item(item: dict, dry_run: bool) -> bool:
    name = item["name"].strip()
    date_iso = col(item, COL_DATE).get("date")
    hour = col(item, COL_TIME).get("hour")
    minute = col(item, COL_TIME).get("minute") or 0
    price = (col(item, COL_PRICE).get("text") or "").strip()

    start_utc, end_utc = event_times_utc(date_iso, hour, minute)
    desc_html = build_description_html(item, date_iso, hour, minute)

    print(f"\n=== {name} ({item['id']}) — {date_iso} {hour:02d}:{minute:02d} PT ===")
    print(f"  start/end UTC : {start_utc} → {end_utc}")
    print(f"  ticket        : free RSVP{f' ({price} cover at door)' if price else ''}")

    cover = resolve_eb_cover(item)
    if not cover:
        print("  SKIP: no flyer on the Monday item")
        return False
    print(f"  cover         : {cover.name}")

    if dry_run:
        print("  DRY RUN — no Eventbrite event created. Description preview:")
        print("  " + desc_html[:220].replace("\n", " ") + "…")
        return False

    image_id = eb_upload_image(cover)
    print(f"  image uploaded: {image_id}")
    event = eb_create_event(item, image_id, start_utc, end_utc, desc_html)
    event_id = event["id"]
    print(f"  event created : {event_id}")
    eb_add_ticket(event_id, price)
    eb_publish(event_id)
    print(f"  published     : {event['url']}")

    monday_write_eventbrite_url(item["id"], event["url"], f"Eventbrite — {name}")
    print("  Monday updated: Eventbrite URL written back")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Create Eventbrite events from Monday items")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--item-id", help="Monday item id to process")
    g.add_argument("--all-pending", action="store_true",
                   help="process every upcoming, complete item with no Eventbrite URL")
    ap.add_argument("--dry-run", action="store_true",
                    help="show what would happen without creating anything")
    args = ap.parse_args()

    load_dotenv()
    items = fetch_items()

    if args.item_id:
        targets = [i for i in items if i["id"] == str(args.item_id)]
        if not targets:
            sys.exit(f"Item {args.item_id} not found on board {BOARD_ID}")
        ok, why = readiness(targets[0])
        if not ok and why != "already has an Eventbrite URL":
            sys.exit(f"Item not ready: {why}")
        if not ok:
            sys.exit(f"Refusing: {why} — remove it from the column first to recreate.")
    else:
        targets = []
        for i in items:
            ok, why = readiness(i)
            (targets.append(i) if ok else print(f"  skip {i['name']!r}: {why}"))
        if not targets:
            print("Nothing pending — every ready event already has an Eventbrite URL.")
            return 0

    created = sum(process_item(item, args.dry_run) for item in targets)
    if created:
        refresh_fb_kit_now()
    return 0


if __name__ == "__main__":
    sys.exit(main())
