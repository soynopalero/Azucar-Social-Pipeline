"""
Build the FB Event Kit — docs/fb_kit.json + flyer copies under docs/media/fb-kit/.

Lists every upcoming Monday event that HAS an Eventbrite URL but has NO
Facebook Event URL yet (the handshake columns), with every field pre-formatted
in the exact order Facebook's "Create event" form asks for them. The kit page
(docs/fb-kit.html) renders these with one-tap copy buttons so creating the
native FB event takes ~1 minute.

Env: MONDAY_API_KEY (same token the website sync uses).
Run:  python code/build_fb_kit.py          then commit docs/ and push.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"
KIT_MEDIA = DOCS / "media" / "fb-kit"
KIT_JSON = DOCS / "fb_kit.json"

MONDAY_API_KEY = os.environ.get("MONDAY_API_KEY", "").strip()
BOARD_ID = "18414182966"

COL_DATE = "date_mm3h56jc"
COL_TIME = "hour_mm3h4nrh"
COL_PHASE = "color_mm3hz990"
COL_LONG_DESC = "long_text_mm4tbk7f"
COL_SHORT_DESC = "long_text_mm4nvacq"
COL_PRICE = "text_mm4nazaw"
COL_AGE = "color_mm4p6jsr"
COL_EVENTBRITE = "link_mm4nmhe3"
COL_FB_EVENT = "link_mm4xv1nv"
COL_FLYER = "file_mm4nnwtq"

HIDDEN_PHASES = {"Cancelled", "Completed"}
VENUE_ADDRESS = "327 W Lewis St, Pasco, WA 99301"
VENUE_LINE = "📍 Azúcar at Out & About — 327 W Lewis St, Pasco WA"

MONDAY_URL = "https://api.monday.com/v2"


def monday_query(query: str, variables: dict | None = None) -> dict:
    if not MONDAY_API_KEY:
        sys.exit("MONDAY_API_KEY env var is empty — refusing to run.")
    payload = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        MONDAY_URL, data=payload, method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": MONDAY_API_KEY, "API-Version": "2024-10"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.loads(r.read().decode())
    if body.get("errors"):
        sys.exit(f"Monday API error: {json.dumps(body['errors'])}")
    return body["data"]


def fetch_items() -> list[dict]:
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
                      ... on StatusValue { label }
                      ... on DateValue { date }
                      ... on HourValue { hour minute }
                      ... on LinkValue { url }
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
            return items


def col(item: dict, col_id: str) -> dict:
    return next((c for c in item["column_values"] if c["id"] == col_id), {})


def long_text(item: dict, col_id: str) -> str | None:
    c = col(item, col_id)
    try:
        v = json.loads(c.get("value") or "null")
        if isinstance(v, dict):
            return (v.get("text") or "").strip() or None
    except (json.JSONDecodeError, TypeError):
        pass
    return (c.get("text") or "").strip() or None


def fmt_date(d: dt.date) -> str:
    return d.strftime("%b %-d, %Y") if os.name != "nt" else d.strftime("%b %d, %Y").replace(" 0", " ")


def fmt_time(hour: int, minute: int) -> str:
    suffix = "AM" if hour < 12 else "PM"
    h12 = 12 if hour % 12 == 0 else hour % 12
    return f"{h12}:{minute:02d} {suffix}"


def download_flyer(item: dict) -> str | None:
    c = col(item, COL_FLYER)
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
    KIT_MEDIA.mkdir(parents=True, exist_ok=True)
    out = KIT_MEDIA / f"{item['id']}{ext}"
    with urllib.request.urlopen(url, timeout=30) as r:
        out.write_bytes(r.read())
    return f"media/fb-kit/{out.name}"


def build_description(item: dict, event_date: dt.date, start_str: str,
                      eventbrite_url: str) -> str:
    body = long_text(item, COL_LONG_DESC) or long_text(item, COL_SHORT_DESC) or ""
    price = (col(item, COL_PRICE).get("text") or "").strip()
    age = (col(item, COL_AGE).get("label") or "").strip()

    spanish_months = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                      "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    spanish_days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    fecha = f"{spanish_days[event_date.weekday()]} {event_date.day} de {spanish_months[event_date.month - 1]}"

    logistics = [f"🗓️ {fecha} — Show {start_str}", VENUE_LINE]
    extras = " · ".join(x for x in [age or None, f"Cover {price}" if price else None] if x)
    if extras:
        logistics.append(f"🔞 {extras}" if age else f"💵 {extras}")

    return f"{body}\n\n" + "\n".join(logistics) + f"\n\n🎟️ Tickets: {eventbrite_url}"


def main() -> int:
    today = dt.date.today().isoformat()
    kit_events = []

    for item in fetch_items():
        phase = col(item, COL_PHASE).get("label")
        date_iso = col(item, COL_DATE).get("date")
        eb = (col(item, COL_EVENTBRITE).get("url") or "").strip()
        fb = (col(item, COL_FB_EVENT).get("url") or "").strip()

        if not date_iso or date_iso < today or phase in HIDDEN_PHASES:
            continue
        if not eb or fb:
            continue  # no Eventbrite yet, or FB event already exists

        hour_c = col(item, COL_TIME)
        hour, minute = hour_c.get("hour"), hour_c.get("minute")
        if hour is None:
            print(f"  skip {item['name']!r}: no event time set")
            continue
        desc_ok = long_text(item, COL_LONG_DESC) or long_text(item, COL_SHORT_DESC)
        if not desc_ok:
            print(f"  skip {item['name']!r}: no description on Monday")
            continue

        flyer = download_flyer(item)
        if not flyer:
            print(f"  skip {item['name']!r}: no flyer on Monday")
            continue

        event_date = dt.date.fromisoformat(date_iso)
        start_str = fmt_time(hour, minute or 0)
        # Default: 4-hour event; past-midnight end lands on the next day.
        end_hour = (hour + 4) % 24
        end_date = event_date + dt.timedelta(days=1) if hour + 4 >= 24 else event_date

        kit_events.append({
            "item_id": item["id"],
            "name": item["name"].strip(),
            "date_display": fmt_date(event_date),
            "start_time": start_str,
            "end_date_display": fmt_date(end_date),
            "end_time": fmt_time(end_hour, minute or 0),
            "location": VENUE_ADDRESS,
            "description": build_description(item, event_date, start_str, eb),
            "eventbrite_url": eb,
            "flyer": flyer,
            "monday_url": f"https://nopaleros-org.monday.com/boards/{BOARD_ID}/pulses/{item['id']}",
        })
        print(f"  ✓ {item['name']!r} on {date_iso}")

    KIT_JSON.write_text(
        json.dumps({"generated_at": dt.datetime.now().isoformat(timespec="seconds"),
                    "events": kit_events}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    print(f"\nWrote {KIT_JSON.relative_to(REPO_ROOT)} with {len(kit_events)} event(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
