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

Needs MONDAY_API_KEY and EVENTBRITE_TOKEN in the environment or in code/.env.

Hard-won API facts baked in (see memory/project_eventbrite_integration.md):
- description.html in the CREATE post only; never send summary too
  (SUMMARY_DESCRIPTION_CONFLICT) and never touch structured_content.
- Venue 298365330 must keep its lat/long (a null there breaks EB's editor).
- Pages are only created for items whose "Eventbrite?" column is Yes, with
  ONE paid General Admission ticket at the "Ticket Price" column (never a
  free ticket — Pedro, 2026-11-06). Publishing a paid event needs the
  per-event Washington tax questionnaire answered first (otherwise
  EVENT_TAX_SETTINGS_MISSING); eb_answer_tax() does that through the
  undocumented /events/{id}/tax_settings/ endpoint.
- Portrait flyers get a generated 1920x1005 blurred-wings cover (same
  make_fb_cover used by the FB kit) so EB's wide cover band never crops art.
- Emoji in event names: create/update accept them, but an async sanitizer
  blanks the whole name and publish then 400s with "event.name - MISSING"
  (seen live 2026-07-27, '🌿 JOTERÍA…'). Names are emoji-stripped up front.
- Eventbrite's API throws plain HTTP 500 INTERNAL_ERROR on ordinary writes
  (seen live 2026-09-09 on ticket_classes, right after the event itself was
  created). Every call is retried with backoff, and the create→ticket→publish
  chain is RESUMABLE: a run that dies after "event created" leaves a draft on
  Eventbrite, and the next run adopts that draft (matched by name + start)
  instead of creating a duplicate.

Self-test (offline, fake HTTP): python code/monday_to_eventbrite.py --selftest
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


def load_dotenv() -> None:
    env_file = Path(__file__).resolve().parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


# Must run before importing build_fb_kit, which reads MONDAY_API_KEY at import.
load_dotenv()

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

EB_TOKEN = os.environ.get("EVENTBRITE_TOKEN", "").strip()
EB_ORG = "2861869150261"
EB_VENUE = "298365330"
EB_BASE = "https://www.eventbriteapi.com/v3"
EB_AUTH = {"Authorization": f"Bearer {EB_TOKEN}"}
EB_JSON = {**EB_AUTH, "Content-Type": "application/json"}

# Intake columns added 2026-11-06 (the Telegram bot sets them).
COL_EB_WANT = "color_mm8vzf05"        # status: Yes / No
COL_TICKET_PRICE = "numeric_mm8vmw52"  # USD, one paid ticket

PACIFIC = ZoneInfo("America/Los_Angeles")
VENUE_LINE = "📍 Azúcar at Out &amp; About — 327 W Lewis St, Pasco WA"
EVENT_HOURS = 4  # default duration

SPANISH_DAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
SPANISH_MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def fail(label: str, resp: requests.Response) -> None:
    # Raise (not sys.exit) so one bad item can't abort the whole --all-pending run.
    raise RuntimeError(f"{label} FAILED — HTTP {resp.status_code}\n{resp.text}")


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

# Emoji + pictograph ranges Eventbrite's name sanitizer silently blanks.
EMOJI_RX = re.compile(
    "["
    "\U0001F000-\U0001FAFF"  # emoji, symbols & pictographs
    "\u2600-\u27BF"          # misc symbols + dingbats
    "\u2B00-\u2BFF"          # misc symbols and arrows
    "\uFE0E\uFE0F\u200D"  # variation selectors + zero-width joiner
    "]+"
)


def eb_safe_name(name: str) -> str:
    cleaned = EMOJI_RX.sub("", name)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" \t-\u2013\u2014|\u2022\u00b7~")
    return cleaned or name  # never send an empty name


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

# Eventbrite answers with these when IT is having a bad moment; a bad request
# from us is a 4xx and is never retried (it would not fix itself in 20s).
EB_RETRY_STATUS = {429, 500, 502, 503, 504}
EB_ATTEMPTS = 4
EB_BACKOFF = (5, 10, 20)  # seconds between attempts


def eb_transient(resp: requests.Response | None) -> bool:
    if resp is None:
        return True  # network error / timeout
    if resp.status_code in EB_RETRY_STATUS:
        return True
    # Media store: 4xx whose own text says "Please try again" (seen 2026-07-08).
    return "S3_ERROR" in (resp.text or "")


def eb_call(method: str, url: str, label: str, **kw) -> requests.Response:
    """One Eventbrite HTTP call, retried on 5xx/429/network errors.

    Safe for every call this script makes: creating an event, a ticket class,
    or publishing twice in a row does not double anything — Eventbrite rejects
    a second ticket class with the same name and publish is idempotent — and a
    failed create returns no id, so a retried create cannot leave two events.
    """
    import time

    kw.setdefault("timeout", 60)
    resp: requests.Response | None = None
    for attempt in range(1, EB_ATTEMPTS + 1):
        try:
            resp = requests.request(method, url, **kw)
        except requests.RequestException as e:
            resp = None
            reason = f"{type(e).__name__}: {e}"
        else:
            if resp.ok:
                return resp
            reason = f"HTTP {resp.status_code} {resp.text[:120]}"
        if not eb_transient(resp) or attempt == EB_ATTEMPTS:
            break
        wait = EB_BACKOFF[min(attempt, len(EB_BACKOFF)) - 1]
        print(f"  … {label}: {reason}; retry {attempt}/{EB_ATTEMPTS - 1} in {wait}s", flush=True)
        time.sleep(wait)
    if resp is None:
        raise RuntimeError(f"{label} FAILED — no response from Eventbrite after {EB_ATTEMPTS} attempts")
    fail(label, resp)
    raise RuntimeError("unreachable")


def eb_upload_image(path: Path) -> str:
    from PIL import Image

    info = eb_call("GET", f"{EB_BASE}/media/upload/?type=image-event-logo",
                   "upload instructions", headers=EB_AUTH).json()
    with open(path, "rb") as f:
        eb_call("POST", info["upload_url"], "S3 upload", data=info["upload_data"],
                files={"file": ("cover.jpg", f, "image/jpeg")}, timeout=120)
    with Image.open(path) as im:
        w, h = im.size
    r3 = eb_call("POST", f"{EB_BASE}/media/upload/", "upload confirm", headers=EB_JSON, json={
        "upload_token": info["upload_token"],
        "crop_mask": {"top_left": {"x": 0, "y": 0}, "width": w, "height": h},
    })
    return r3.json()["id"]


def eb_find_draft(name: str, start_utc: str) -> dict | None:
    """A draft left behind by an earlier run that died between "event created"
    and "published". Matched on the exact (emoji-safe) name AND start time so
    a same-named monthly show on another date is never mistaken for it."""
    url = (f"{EB_BASE}/organizations/{EB_ORG}/events/"
           "?status=draft&order_by=created_desc&page_size=50")
    for _page in range(3):  # 150 most recent drafts is plenty
        body = eb_call("GET", url, "draft lookup", headers=EB_AUTH).json()
        for ev in body.get("events") or []:
            if ((ev.get("name") or {}).get("text") or "").strip() == name \
                    and (ev.get("start") or {}).get("utc") == start_utc:
                return ev
        pg = body.get("pagination") or {}
        if not pg.get("has_more_items") or not pg.get("continuation"):
            return None
        url = (f"{EB_BASE}/organizations/{EB_ORG}/events/"
               f"?status=draft&page_size=50&continuation={pg['continuation']}")
    return None


def eb_create_event(item: dict, image_id: str, start_utc: str, end_utc: str,
                    desc_html: str) -> dict:
    payload = {"event": {
        "name": {"html": html.escape(eb_safe_name(item["name"].strip()))},
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
    return eb_call("POST", f"{EB_BASE}/organizations/{EB_ORG}/events/", "event create",
                   headers=EB_JSON, json=payload).json()


def ticket_cents(item: dict) -> int | None:
    """The board's Ticket Price as whole cents, or None when missing / not > 0."""
    raw = (col(item, COL_TICKET_PRICE).get("text") or "").strip().replace("$", "").replace(",", "")
    try:
        dollars = float(raw)
    except ValueError:
        return None
    return int(round(dollars * 100)) if dollars > 0 else None


def eb_ensure_ticket(event_id: str, cents: int) -> None:
    """One paid General Admission ticket at the board's price. A paid class
    already on an adopted draft is kept; a FREE class left by the old code is
    removed first — free tickets are never offered (Pedro, 2026-11-06)."""
    existing = eb_call("GET", f"{EB_BASE}/events/{event_id}/ticket_classes/",
                       "ticket class lookup", headers=EB_AUTH).json().get("ticket_classes") or []
    paid = [t for t in existing if not t.get("free")]
    if paid:
        print(f"  ticket class  : already present ({(paid[0].get('cost') or {}).get('display', 'paid')})")
        return
    for t in existing:
        eb_call("DELETE", f"{EB_BASE}/events/{event_id}/ticket_classes/{t['id']}/",
                "free ticket removal", headers=EB_AUTH)
        print("  ticket class  : removed a leftover free ticket")
    eb_call("POST", f"{EB_BASE}/events/{event_id}/ticket_classes/", "ticket class",
            headers=EB_JSON, json={"ticket_class": {
                "name": "General Admission", "cost": f"USD,{cents}", "quantity_total": 200,
                "minimum_quantity": 1, "maximum_quantity": 10, "include_fee": False}})
    print(f"  ticket class  : created (${cents / 100:.2f} General Admission)")


def _answer_text(ans: dict) -> str:
    for t in ans.get("texts") or []:
        if t.get("translated_text"):
            return t["translated_text"]
    for t in ans.get("texts") or []:
        if t.get("text"):
            return t["text"]
    return ""


def _no_answer(question: dict) -> dict | None:
    """The plain "No" answer of a tax question ("No", "No (Not an enumerated
    activity)" — never "Not sure")."""
    for a in question.get("answers") or []:
        t = _answer_text(a).strip().lower()
        if t == "no" or t.startswith("no (") or t.startswith("no,"):
            return a
    return None


def tax_responses(form: dict) -> tuple[int | None, list[dict]]:
    """Walk the questionnaire answering No at every step (a bar night is not
    a lecture, course, or amusement activity). Returns (template_id, responses)."""
    root = (form or {}).get("questions") or {}
    if not root.get("question_id"):
        return None, []
    responses, q = [], root
    for _ in range(8):
        ans = _no_answer(q)
        if not ans:
            break
        responses.append({"question_id": q["question_id"], "answer_id": ans["answer_id"],
                          "answer_text": _answer_text(ans)})
        q = ans.get("next_question") or {}
        if not q.get("question_id"):
            break
    return root["question_id"], responses


def eb_answer_tax(event_id: str) -> None:
    """Answer Eventbrite's per-event Washington tax questionnaire so a paid
    event can publish; without it publish 400s with EVENT_TAX_SETTINGS_MISSING.
    Undocumented endpoint, verified live 2026-11-06 (GET returns the question
    tree, POST takes template_id = root question id + the chosen answers)."""
    form = eb_call("GET", f"{EB_BASE}/events/{event_id}/tax_settings/", "tax form",
                   headers=EB_AUTH).json()
    template_id, responses = tax_responses(form)
    if template_id is None:
        print("  tax form      : none offered for this event")
        return
    if not responses:
        raise RuntimeError("tax form: no 'No' answer path found — Eventbrite changed the questionnaire")
    r = eb_call("POST", f"{EB_BASE}/events/{event_id}/tax_settings/", "tax answers",
                headers=EB_JSON, json={"template_id": template_id, "responses": responses})
    print(f"  tax form      : answered ({len(responses)} steps) -> {r.json().get('tax_status')}")


def eb_publish(event_id: str) -> None:
    eb_call("POST", f"{EB_BASE}/events/{event_id}/publish/", "publish", headers=EB_AUTH)


def notify_telegram(created: list[tuple[str, str, str]]) -> None:
    """Send Pedro + Jayme the 'it's done' message on Telegram: Eventbrite link(s),
    the FB kit link, and the Monday item. No-op unless TELEGRAM_BOT_TOKEN is set."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_ids = [c.strip() for c in
                os.environ.get("TELEGRAM_NOTIFY_CHAT_IDS", "").split(",") if c.strip()]
    if not token or not chat_ids or not created:
        return
    blocks = [
        f"🎟️ {name}\nEventbrite: {eb_url}\nMonday: {monday_url}"
        for name, eb_url, monday_url, _start, _end in created
    ]
    msg = ("✅ Eventbrite created for "
           f"{len(created)} event{'s' if len(created) > 1 else ''}:\n\n"
           + "\n\n".join(blocks)
           + "\n\n📘 FB Event Kit is ready to copy-paste (new Eventbrite link included):"
             "\nhttps://soynopalero.github.io/Azucar-Social-Pipeline/fb-kit.html")
    for cid in chat_ids:
        try:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={"chat_id": cid, "text": msg,
                                "disable_web_page_preview": True}, timeout=15)
        except requests.RequestException as e:
            print(f"Telegram notify to {cid} failed: {e}")


def notify_ops_failure(failed: list[tuple[str, str]]) -> None:
    """Tell the maintainer WHAT failed and whether anything needs doing.
    Goes only to OPS_ALERT_CHAT_ID (Pedro) — a GitHub log link is not something
    Jayme can act on, and the 'done' message above already tells both of them
    when things work."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat = os.environ.get("OPS_ALERT_CHAT_ID", "").strip()
    if not token or not chat or not failed:
        return
    run_url = ""
    if os.environ.get("GITHUB_RUN_ID"):
        run_url = (f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/"
                   f"{os.environ.get('GITHUB_REPOSITORY', '')}/actions/runs/{os.environ['GITHUB_RUN_ID']}")
    lines = [f"⚠️ Eventbrite auto-create: {len(failed)} event(s) not published this run."]
    for name, err in failed:
        first = err.strip().splitlines()[0][:160] if err.strip() else "unknown error"
        lines.append(f"• {name}: {first}")
    if any("HTTP 5" in err or "no response" in err for _, err in failed):
        lines.append("Eventbrite server error — nothing to do. The next run (every 2 h, or the "
                     "next Monday publish) resumes the draft; no duplicate is created.")
    else:
        lines.append("This one needs a look — see the log.")
    if run_url:
        lines.append(run_url)
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat, "text": "\n".join(lines),
                            "disable_web_page_preview": True}, timeout=15)
    except requests.RequestException as e:
        print(f"ops alert to {chat} failed: {e}")


def notify_gcal(created: list) -> None:
    """Drop each newly-created event onto the shared Azucar Events Google
    Calendar via the Apps Script webhook (code/gcal_webhook.gs). Silent no-op
    until the GCAL_WEBHOOK_URL secret is configured."""
    url = os.environ.get("GCAL_WEBHOOK_URL", "").strip()
    if not url or not created:
        return
    import gcal_sync  # same folder; stdlib-only
    for name, eb_url, monday_url, start_utc, end_utc in created:
        item_id = monday_url.rstrip("/").rsplit("/", 1)[-1]
        event_date = dt.datetime.fromisoformat(start_utc.replace("Z", "+00:00")) \
            .astimezone(ZoneInfo("America/Los_Angeles")).date().isoformat()
        try:
            # Since 2026-11-10 gcal_sync.py also adds events with no Eventbrite
            # page, so the event may already be on the calendar: don't add a twin.
            made = gcal_sync.ensure_entry(url, item_id, name, event_date,
                                          start_utc, end_utc, eb_url)
            print(f"  Google Calendar: {name} -> {'added' if made else 'already on the calendar'}")
        except Exception as e:  # the calendar is a convenience; never fail the run
            print(f"  Google Calendar notify failed for {name}: {e}")


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
    if (col(item, COL_EB_WANT).get("label") or "").strip().lower() != "yes":
        return False, "Eventbrite not requested (Eventbrite? column is not Yes)"
    if ticket_cents(item) is None:
        return False, "no Ticket Price above $0"
    if col(item, COL_TIME).get("hour") is None:
        return False, "no event time"
    if not (long_text(item, COL_LONG_DESC) or long_text(item, COL_SHORT_DESC)):
        return False, "no description"
    return True, "ready"


def process_item(item: dict, dry_run: bool) -> tuple[str, str, str] | None:
    name = item["name"].strip()
    date_iso = col(item, COL_DATE).get("date")
    hour = col(item, COL_TIME).get("hour")
    minute = col(item, COL_TIME).get("minute") or 0
    cents = ticket_cents(item) or 0

    start_utc, end_utc = event_times_utc(date_iso, hour, minute)
    desc_html = build_description_html(item, date_iso, hour, minute)

    print(f"\n=== {name} ({item['id']}) — {date_iso} {hour:02d}:{minute:02d} PT ===")
    print(f"  start/end UTC : {start_utc} → {end_utc}")
    print(f"  ticket        : ${cents / 100:.2f} General Admission (paid, no free tier)")

    cover = resolve_eb_cover(item)
    if not cover:
        print("  SKIP: no flyer on the Monday item")
        return None
    print(f"  cover         : {cover.name}")

    if dry_run:
        print("  DRY RUN — no Eventbrite event created. Description preview:")
        print("  " + desc_html[:220].replace("\n", " ") + "…")
        return None

    event = eb_find_draft(eb_safe_name(name), start_utc)
    if event:
        # A previous run died between create and publish (Eventbrite 500,
        # runner lost, ...). Finish that draft instead of making a twin.
        print(f"  resuming draft: {event['id']} (left by an earlier run)")
    else:
        image_id = eb_upload_image(cover)
        print(f"  image uploaded: {image_id}")
        event = eb_create_event(item, image_id, start_utc, end_utc, desc_html)
        print(f"  event created : {event['id']}")
    event_id = event["id"]
    try:
        eb_ensure_ticket(event_id, cents)
        eb_answer_tax(event_id)
        eb_publish(event_id)
    except Exception as e:
        raise RuntimeError(
            f"{e}\n  -> draft event {event_id} stays on Eventbrite; the next run "
            "resumes it (no duplicate will be created)") from e
    print(f"  published     : {event['url']}")

    monday_write_eventbrite_url(item["id"], event["url"], f"Eventbrite — {name}")
    print("  Monday updated: Eventbrite URL written back")
    monday_url = f"https://nopaleros-org.monday.com/boards/{BOARD_ID}/pulses/{item['id']}"
    return (name, event["url"], monday_url, start_utc, end_utc)


def main() -> int:
    ap = argparse.ArgumentParser(description="Create Eventbrite events from Monday items")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--item-id", help="Monday item id to process")
    g.add_argument("--all-pending", action="store_true",
                   help="process every upcoming item with Eventbrite? = Yes, a Ticket Price and no Eventbrite URL")
    ap.add_argument("--dry-run", action="store_true",
                    help="show what would happen without creating anything")
    args = ap.parse_args()

    if not EB_TOKEN and not args.dry_run:
        sys.exit("EVENTBRITE_TOKEN env var is empty — refusing to run. "
                 "Set it in code/.env locally or as a GitHub Actions secret.")
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

    created, failed = [], []
    for item in targets:
        try:
            r = process_item(item, args.dry_run)
            if r:
                created.append(r)
        except Exception as e:
            import traceback
            print(f"\n!! {item['name']!r} failed — continuing with the rest:")
            traceback.print_exc()
            failed.append((item["name"], str(e)))
    if created:
        refresh_fb_kit_now()
        notify_gcal(created)
        notify_telegram(created)
    if failed:
        print(f"\n{len(failed)} item(s) failed: {[n for n, _ in failed]}")
        notify_ops_failure(failed)
        return 1
    return 0


# ─── Offline self-test ───────────────────────────────────────────────────────

def selftest() -> int:
    """Exercise the retry + resume logic against a scripted fake Eventbrite.
    No network, no token, no Monday."""
    import time as _time

    class FakeResp:
        def __init__(self, status, body):
            self.status_code, self._body = status, body
            self.text = json.dumps(body)
            self.ok = status < 400

        def json(self):
            return self._body

    calls: list[tuple[str, str]] = []
    script: dict[str, list] = {}

    def fake_request(method, url, **kw):
        calls.append((method, url))
        key = f"{method} {url.split('?')[0].replace(EB_BASE, '')}"
        queue = script.get(key)
        if not queue:
            raise AssertionError(f"unexpected call {key}")
        nxt = queue.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return FakeResp(*nxt)

    real_request, real_sleep = requests.request, _time.sleep
    requests.request, _time.sleep = fake_request, lambda s: None
    results = []

    def check(label, cond):
        results.append(bool(cond))
        print(f"  {'ok  ' if cond else 'FAIL'} {label}")

    try:
        # 1. The 2026-09-09 failure: ticket class 500s once, then succeeds.
        calls.clear()
        script.clear()
        script["GET /events/E1/ticket_classes/"] = [(200, {"ticket_classes": []})]
        script["POST /events/E1/ticket_classes/"] = [
            (500, {"status_code": 500, "error": "INTERNAL_ERROR"}), (200, {"id": "T1"})]
        eb_ensure_ticket("E1", 1000)
        check("ticket class retried after HTTP 500",
              sum(1 for m, u in calls if m == "POST") == 2)

        # 2. A 4xx is a real rejection: fail fast, no retry.
        calls.clear()
        script["POST /events/E2/publish/"] = [(400, {"error": "ARGUMENTS_ERROR"})]
        try:
            eb_publish("E2")
            check("400 raises", False)
        except RuntimeError as e:
            check("400 raises without retry", "HTTP 400" in str(e) and len(calls) == 1)

        # 3. Network errors count as transient; give up after EB_ATTEMPTS.
        calls.clear()
        script["POST /events/E3/publish/"] = [requests.ConnectionError("boom")] * EB_ATTEMPTS
        try:
            eb_publish("E3")
            check("network failure raises", False)
        except RuntimeError as e:
            check("network failure retried then raised",
                  "no response" in str(e) and len(calls) == EB_ATTEMPTS)

        # 4. Resume: the leftover draft is found by name + start, not by name alone.
        calls.clear()
        drafts = {"events": [
            {"id": "OLD", "name": {"text": "Noche Vaquera"}, "start": {"utc": "2026-08-01T02:00:00Z"}},
            {"id": "NEW", "name": {"text": "Noche Vaquera"}, "start": {"utc": "2026-09-25T02:00:00Z"}},
        ], "pagination": {"has_more_items": False}}
        script["GET /organizations/%s/events/" % EB_ORG] = [(200, drafts)]
        found = eb_find_draft("Noche Vaquera", "2026-09-25T02:00:00Z")
        check("draft matched on name AND start", found and found["id"] == "NEW")
        script["GET /organizations/%s/events/" % EB_ORG] = [(200, drafts)]
        check("no match when start differs",
              eb_find_draft("Noche Vaquera", "2026-10-25T02:00:00Z") is None)

        # 5. Adopted draft that already has a PAID ticket: don't add a second one.
        calls.clear()
        script["GET /events/E4/ticket_classes/"] = [(200, {"ticket_classes": [{"id": "T", "free": False, "cost": {"display": "$20.00"}}]})]
        eb_ensure_ticket("E4", 2000)
        check("existing paid ticket class is kept", not any(m == "POST" for m, _ in calls))

        # 6. A leftover FREE ticket (old behaviour) is removed and replaced by the paid one.
        calls.clear()
        script["GET /events/E5/ticket_classes/"] = [(200, {"ticket_classes": [{"id": "F", "free": True}]})]
        script["DELETE /events/E5/ticket_classes/F/"] = [(200, {"deleted": True})]
        script["POST /events/E5/ticket_classes/"] = [(200, {"id": "P"})]
        eb_ensure_ticket("E5", 2500)
        check("free ticket deleted, paid one created",
              [m for m, _ in calls] == ["GET", "DELETE", "POST"])

        # 7. Tax questionnaire: walk the No path, never "Not sure".
        form = {"questions": {"question_id": 81840, "answers": [
            {"answer_id": 81841, "texts": [{"translated_text": "Yes"}], "next_question": {"question_id": 1}},
            {"answer_id": 81842, "texts": [{"translated_text": "No"}], "next_question": {
                "question_id": 82507, "answers": [
                    {"answer_id": 82508, "texts": [{"translated_text": "Yes (Enumerated activity)"}]},
                    {"answer_id": 82510, "texts": [{"translated_text": "Not sure — show me the list"}]},
                    {"answer_id": 82509, "texts": [{"translated_text": "No (Not an enumerated activity)"}]},
                ]}},
        ]}}
        tid, resp = tax_responses(form)
        check("tax form: template id + two No answers",
              tid == 81840 and [r["answer_id"] for r in resp] == [81842, 82509]
              and resp[1]["answer_text"].startswith("No ("))
        check("tax form: no questionnaire -> nothing to answer", tax_responses({}) == (None, []))
        calls.clear()
        script["GET /events/E6/tax_settings/"] = [(200, form)]
        script["POST /events/E6/tax_settings/"] = [(200, {"tax_status": {"eb_tax": 0, "org_tax": 1}})]
        eb_answer_tax("E6")
        check("tax answers posted before publish", [m for m, _ in calls] == ["GET", "POST"])

        # 8. Ticket Price column -> cents; empty, zero or junk means not ready.
        mk = lambda txt: {"column_values": [{"id": COL_TICKET_PRICE, "text": txt}]}
        check("ticket price parsing",
              ticket_cents(mk("20")) == 2000 and ticket_cents(mk("$15.50")) == 1550
              and ticket_cents(mk("0")) is None and ticket_cents(mk("")) is None)

        check("emoji-safe name still used for matching",
              eb_safe_name("🌿 JOTERÍA: La Plant House Edition 🌿") == "JOTERÍA: La Plant House Edition")
    finally:
        requests.request, _time.sleep = real_request, real_sleep

    if not all(results):
        print(f"{results.count(False)} case(s) failed.")
        return 1
    print(f"All {len(results)} Eventbrite cases passed.")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main())
