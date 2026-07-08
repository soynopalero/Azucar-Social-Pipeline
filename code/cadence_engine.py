#!/usr/bin/env python3
"""
cadence_engine.py
-----------------
Read the Azucar Events Monday board and compute the social-media posting
SCHEDULE for each eligible event, following the agreed cadence.

Default run is a DRY-RUN preview (prints; --write saves docs/cadence_preview.md).

--enqueue adds the LIVE layer, driven by the Caption Status text column on Monday:
    (empty)/regenerate -> draft 4 caption variants (Claude) -> save to Monday ->
                          send to Telegram with Approve/Redraft buttons
    needs_review       -> waiting on the Telegram approval; do nothing
    approved           -> upload flyer to catbox once, write the full cadence
                          schedule into posts_queue.json (captions rotate across
                          slots, one entry per platform) -> mark queued
    queued             -> done; never double-queued (pending entries for an event
                          are replaced if it's ever re-approved)
Nothing is ever posted without a human tapping Approve in Telegram.

Cadence (Standard), anchored to weeks-before-event. If an event is created late,
it simply starts at whichever bucket applies:
    4+ weeks out : 3 posts / week
    3 weeks      : 3 posts
    2 weeks      : 5 posts
    week of      : every remaining day (incl. day-of)
Aggressive : identical to Standard for the lead-up weeks; only the WEEK OF the
             event doubles to 2 posts/day (morning + evening).
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
COL_DATE           = "date_mm3h56jc"
COL_PHASE          = "color_mm3hz990"
COL_DESC           = "long_text_mm4nvacq"
COL_PRICE          = "text_mm4nazaw"
COL_FLYER          = "file_mm4nnwtq"
COL_CADENCE        = "color_mm4nsvqh"
COL_CAPTIONS       = "long_text_mm4wcfk4"   # AI caption variants (JSON array)
COL_CAPTION_STATUS = "text_mm4wk4kr"        # ""/needs_review/approved/queued/regenerate
COL_CREATED_BY     = "text_mm4wnp8g"        # Telegram chat id of the event's creator
COL_LANGUAGE       = "dropdown_mm4z9x97"    # Caption Language: English/Spanish/Bilingual (empty = English)

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

    flyer_assets = [f.get("assetId") or f.get("asset_id") for f in files]
    flyer_assets = [a for a in flyer_assets if a]
    flyer_asset_id = flyer_assets[0] if flyer_assets else None

    lang_c = cv.get(COL_LANGUAGE) or {}
    language = (lang_c.get("text") or "").strip().lower() or "english"

    return {
        "id": item["id"],
        "name": (item.get("name") or "").strip() or None,
        "date": date_c.get("date"),
        "phase": phase_c.get("label"),
        "cadence": (cad_c.get("label") or "").strip().lower() or None,
        "description": txt(COL_DESC),
        "price": txt(COL_PRICE),
        "has_flyer": len(files) > 0,
        "flyer_asset_id": flyer_asset_id,
        "captions_json": txt(COL_CAPTIONS),
        "caption_status": (txt(COL_CAPTION_STATUS) or "").strip().lower(),
        "created_by": (txt(COL_CREATED_BY) or "").strip() or None,
        "flyer_assets": flyer_assets,
        "language": language,
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
            # Aggressive only doubles the WEEK OF the event (w == 1): a morning AND an
            # evening post each day. The lead-up weeks stay identical to Standard.
            if cadence == "aggressive" and w == 1:
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


# ---------- Live layer: Monday writes, caption drafting, Telegram, queueing ----------
def envvar(name):
    return (os.environ.get(name) or "").strip()


def monday_set_text(item_id, column_id, value):
    monday_query(
        "mutation($b: ID!, $i: ID!, $c: String!, $v: String!) {"
        " change_simple_column_value(board_id: $b, item_id: $i, column_id: $c, value: $v) { id } }",
        {"b": BOARD_ID, "i": item_id, "c": column_id, "v": value},
    )


def monday_set_long_text(item_id, column_id, text):
    monday_query(
        "mutation($b: ID!, $i: ID!, $c: String!, $v: JSON!) {"
        " change_column_value(board_id: $b, item_id: $i, column_id: $c, value: $v) { id } }",
        {"b": BOARD_ID, "i": item_id, "c": column_id, "v": json.dumps({"text": text})},
    )


# ---------- Weekday ground truth ----------
# The model never decides the weekday: code computes it, injects it, and
# corrects any slip in the finished captions.
WEEKDAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
WEEKDAYS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def event_weekday(date_iso):
    try:
        i = dt.date.fromisoformat(date_iso).weekday()
        return WEEKDAYS_EN[i], WEEKDAYS_ES[i]
    except (ValueError, TypeError):
        return None, None


def fix_weekdays(text, date_iso):
    en, es = event_weekday(date_iso)
    if not en:
        return text
    import re
    for i, w in enumerate(WEEKDAYS_EN):
        if w != en:
            text = re.sub(r"\b" + w + r"\b", en, text)
    for i, w in enumerate(WEEKDAYS_ES):
        if w != es:
            text = re.sub(w, es, text)
            text = re.sub(w.capitalize(), es.capitalize(), text)
    return text


# ---------- Grounding: caption history + runbooks (local repo files) ----------
def _name_tokens(name):
    import re
    return [t for t in re.split(r"[^a-záéíóúñü]+", (name or "").lower()) if len(t) >= 4]


def caption_history(name, limit=3):
    tokens = _name_tokens(name)
    if not tokens:
        return []
    try:
        posts = json.loads((REPO_ROOT / "posts_queue.json").read_text(encoding="utf-8")).get("posts", [])
    except (OSError, json.JSONDecodeError):
        return []
    out, seen = [], set()
    for p in reversed(posts):
        cap = p.get("caption") or ""
        if not cap or cap in seen:
            continue
        hay = ((p.get("campaign") or "") + " " + cap[:160]).lower()
        if any(t in hay for t in tokens):
            out.append(cap)
            seen.add(cap)
            if len(out) >= limit:
                break
    return out


def find_runbook(name):
    tokens = _name_tokens(name)
    rb_dir = REPO_ROOT / "runbooks"
    if not tokens or not rb_dir.is_dir():
        return None
    for f in sorted(rb_dir.glob("*.md")):
        if any(t in f.name.lower() for t in tokens):
            return f.read_text(encoding="utf-8")[:3000]
    return None


def flyer_images_b64(e, cap=4):
    """Download the event's flyer files from Monday, return base64 strings for vision."""
    import base64
    out = []
    for asset_id in (e.get("flyer_assets") or [])[:cap]:
        try:
            data = monday_query(
                "query($ids: [ID!]!) { assets(ids: $ids) { id public_url url } }",
                {"ids": [str(asset_id)]},
            )
            a = (data.get("assets") or [None])[0]
            url = a and (a.get("public_url") or a.get("url"))
            if not url:
                continue
            with urllib.request.urlopen(url, timeout=60) as r:
                out.append(base64.b64encode(r.read()).decode())
        except Exception as ex:
            print(f"  flyer image fetch failed ({asset_id}): {ex}")
    return out


def caption_system(language, weekday_en, weekday_es):
    lang = {
        "spanish": "Write captions in SPANISH only.",
        "bilingual": "Write captions BILINGUAL — natural Spanglish, lead English, weave Spanish in.",
    }.get(language, "Write captions in ENGLISH, with at most an occasional Spanish word where it lands naturally.")
    weekday = (
        f"\n- The event is on {weekday_en} (Spanish: {weekday_es}). If you mention a weekday, "
        "it MUST be that one — never any other." if weekday_en else ""
    )
    return f"""You are the social media copywriter for Azucar — a Latinx bar, restaurant, and live venue at Out & About in Pasco, WA.

Voice: FOMO-driven, fun, energetic, sensorial. Full campaign captions like the venue's past hits — a hook that stops the scroll, a body that builds the night (who, what sounds, what it feels like, why you can't miss it), then the info block. Emojis welcome. Short punchy lines inside a longer caption (~150-220 words). Never corporate, never "Join us for".

{lang}

GROUNDING — hard rules:
- Use ONLY performer names, hosts, times, and facts that appear in the event details, the flyer image(s), the past captions, or the runbook provided. NEVER invent names, guests, specials, or details. If you don't know who's performing, hype the night without naming anyone.{weekday}
- NEVER use the words "nightclub", "queer", or "gay" (positioning constraints). Say "Latinx" when referencing community.
- Every caption ends with, on separate lines: a date/time line, "📍 Azucar at Out & About — 327 W Lewis St, Pasco WA", a price line, an age line if age is given, then 6-10 hashtags including #AzucarPasco and #OutAndAbout.

Output ONLY a JSON array of exactly 4 caption strings. No preamble, no code fences."""


def draft_captions(e, n=4):
    key = envvar("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    weekday_en, weekday_es = event_weekday(e["date"])
    history = caption_history(e["name"])
    runbook = find_runbook(e["name"])
    images = flyer_images_b64(e)

    user = (
        f"Draft {n} distinct captions for this event's multi-week posting campaign. Angles: "
        "1) hype announcement, 2) vibe/sensory, 3) community/come-as-you-are, 4) info-forward. "
        "They rotate across many days, so each must stand alone.\n\n"
        f"Event: {e['name']}\nDate: {e['date']}" + (f" ({weekday_en})" if weekday_en else "") + "\n"
        f"Description: {e['description']}\nPrice: {e['price']}"
    )
    if history:
        user += "\n\nPast captions for this show (match their voice and their FACTS — hosts and names in them are real):\n"
        user += "\n\n".join(f"[{i+1}] {h[:900]}" for i, h in enumerate(history))
    if runbook:
        user += f"\n\nRunbook for this recurring show (canonical facts — hosts, times, rituals):\n{runbook}"
    if images:
        user += "\n\nThe flyer image(s) are attached — read them: lineup names, times, and themes on the artwork are real and usable."

    content = [{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b}} for b in images]
    content.append({"type": "text", "text": user})

    body = {"model": "claude-sonnet-5", "max_tokens": 3500,
            "system": caption_system(e.get("language"), weekday_en, weekday_es),
            "messages": [{"role": "user", "content": content}]}
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.loads(r.read())
    # The model may emit a thinking block before the text block — join text blocks only.
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text").strip()
    if not text:
        raise RuntimeError(f"no text block in model response: {json.dumps(data)[:300]}")
    start, end = text.find("["), text.rfind("]")
    caps = json.loads(text[start:end + 1])
    caps = [fix_weekdays(c.strip(), e["date"]) for c in caps if isinstance(c, str) and c.strip()]
    if not caps:
        raise RuntimeError("model returned no captions")
    return caps[:n]


def tg_call(method, payload):
    token = envvar("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set")
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=json.dumps(payload).encode(), headers={"content-type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def chat_for(e):
    """DM the event's creator; hand-made Monday events fall back to the default chat."""
    return e.get("created_by") or envvar("TELEGRAM_CHAT_ID")


def notify_captions_review(e, captions):
    parts = [f"📣 Captions ready — {e['name']} ({e['date']}, {(e['cadence'] or '?').capitalize()} cadence)", ""]
    for i, c in enumerate(captions, 1):
        short = c if len(c) <= 700 else c[:700] + "…"
        parts.append(f"— Variant {i} —\n{short}\n")
    parts.append("✅ Approve queues the full posting schedule (posts rotate through the variants). ✏️ Redraft asks for fresh takes.")
    tg_call("sendMessage", {
        "chat_id": chat_for(e),
        "text": "\n".join(parts),
        "reply_markup": {"inline_keyboard": [[
            {"text": "✅ Approve", "callback_data": f"cap:approve:{e['id']}"},
            {"text": "✏️ Redraft", "callback_data": f"cap:regen:{e['id']}"},
        ]]},
    })


def download_flyer_files(e, cap=6):
    """Download all of the event's flyer files from Monday; returns local paths."""
    import tempfile
    paths = []
    for idx, asset_id in enumerate((e.get("flyer_assets") or [])[:cap]):
        data = monday_query(
            "query($ids: [ID!]!) { assets(ids: $ids) { id public_url url } }",
            {"ids": [str(asset_id)]},
        )
        a = (data.get("assets") or [None])[0]
        url = a and (a.get("public_url") or a.get("url"))
        if not url:
            continue
        path = Path(tempfile.gettempdir()) / f"cadence_flyer_{e['id']}_{idx}.jpg"
        with urllib.request.urlopen(url, timeout=60) as r, open(path, "wb") as f:
            f.write(r.read())
        paths.append(str(path))
    if not paths:
        raise RuntimeError(f"no downloadable flyer files for event {e['id']}")
    return paths


def enqueue_event(e, captions, now):
    import queue_utils as qu  # sibling module; hosts to catbox + saves the queue

    today = now.astimezone(LOCAL_TZ).date()
    ed = dt.date.fromisoformat(e["date"])
    slots = [(d, s) for (d, s) in schedule_for(ed, e["cadence"], today) if to_local_dt(d, s) >= now]
    if not slots:
        return 0

    # Host every flyer once; posts rotate through them for feed variety.
    # Hosted on our own GitHub Pages (committed by the workflow) — catbox.moe
    # blocks uploads from GitHub's datacenter IPs (412 "Invalid uploader").
    image_urls = [host_image_on_pages(p, e["id"], i)
                  for i, p in enumerate(download_flyer_files(e))]
    queue = qu.load_queue()
    # Replace any pending entries for this event (re-approval refreshes cleanly;
    # already-posted entries are never touched).
    queue["posts"] = [p for p in queue["posts"]
                      if not (p.get("monday_event_id") == e["id"] and p.get("status") == "pending")]

    created = now.isoformat()
    campaign = "cadence_" + "".join(ch if ch.isalnum() else "_" for ch in (e["name"] or "").lower()).strip("_")
    for i, (d, s) in enumerate(slots):
        utc = to_local_dt(d, s).astimezone(dt.timezone.utc)
        for platform in PLATFORMS:
            queue["posts"].append({
                "id": qu.new_post_id(utc),
                "platform": platform,
                "scheduled_for_utc": utc.isoformat(),
                "image_url": image_urls[i % len(image_urls)],
                "caption": captions[i % len(captions)],
                "status": "pending",
                "created_at": created,
                "posted_at": None,
                "result": None,
                "campaign": campaign,
                "monday_event_id": e["id"],
                "slot": s,
            })
    qu.save_queue(queue)
    return len(slots) * len(PLATFORMS)


PAGES_BASE = "https://soynopalero.github.io/Azucar-Social-Pipeline"
CADENCE_MEDIA = REPO_ROOT / "docs" / "media" / "cadence"


def host_image_on_pages(local_path, event_id, idx):
    """Copy a flyer into docs/media/cadence/ — the workflow commits it and
    GitHub Pages serves it. Meta fetches post images at posting time, by which
    the Pages deploy (~1 min after commit) is long live."""
    import shutil

    CADENCE_MEDIA.mkdir(parents=True, exist_ok=True)
    ext = Path(local_path).suffix or ".jpg"
    dest = CADENCE_MEDIA / f"{event_id}_{idx}{ext}"
    shutil.copyfile(local_path, dest)
    return f"{PAGES_BASE}/media/cadence/{dest.name}"


def fit_captions_for_monday(caps, budget=1900):
    """Monday's long_text API writes silently truncate around 2,000 chars —
    storing fewer whole captions beats storing corrupted JSON. (Root cause of
    the Jul 5–8 enqueue failures.)"""
    caps = list(caps)
    while len(caps) > 1 and len(json.dumps(caps, ensure_ascii=False)) > budget:
        caps.pop()
    if caps and len(json.dumps(caps, ensure_ascii=False)) > budget:
        c = caps[0][: budget - 60]
        caps = [c[: max(c.rfind(" "), 1)] + " …"]
    return caps


def parse_captions(raw):
    """Parse the captions column; salvage complete strings from truncated JSON
    (events approved through the bot before the truncation fix)."""
    raw = (raw or "").strip()
    if not raw:
        return []
    try:
        caps = json.loads(raw)
        return [c.strip() for c in caps if isinstance(c, str) and c.strip()]
    except json.JSONDecodeError:
        pass
    dec, caps, i = json.JSONDecoder(), [], raw.find('"')
    while i != -1:
        try:
            s, end = dec.raw_decode(raw, i)
        except json.JSONDecodeError:
            break
        if isinstance(s, str) and s.strip():
            caps.append(s.strip())
        i = raw.find('"', end)
    if caps:
        print(f"  (salvaged {len(caps)} caption(s) from truncated JSON)")
    return caps


def run_enqueue(events, today, now):
    print("=== LIVE enqueue pass ===")
    failures = 0
    for e in events:
        if eligibility(e, today):
            continue  # preview already explains skips
        st = e.get("caption_status") or ""
        try:
            if st in ("", "regenerate"):
                caps = fit_captions_for_monday(draft_captions(e))
                monday_set_long_text(e["id"], COL_CAPTIONS, json.dumps(caps, ensure_ascii=False))
                monday_set_text(e["id"], COL_CAPTION_STATUS, "needs_review")
                notify_captions_review(e, caps)
                print(f"• drafted {len(caps)} captions, sent for review: {e['name']}")
            elif st == "needs_review":
                print(f"• awaiting Telegram approval: {e['name']}")
            elif st == "approved":
                caps = parse_captions(e.get("captions_json"))
                if not caps:
                    raise RuntimeError("approved but no captions stored on Monday")
                n = enqueue_event(e, caps, now)
                monday_set_text(e["id"], COL_CAPTION_STATUS, "queued")
                tg_call("sendMessage", {
                    "chat_id": chat_for(e),
                    "text": f"📅 Queued {n} posts for {e['name']} through {e['date']}. They'll go out automatically on schedule.",
                })
                print(f"• queued {n} entries: {e['name']}")
            elif st == "queued":
                print(f"• already queued: {e['name']}")
            else:
                print(f"• unknown caption status '{st}': {e['name']} (fix the Caption Status column)")
        except Exception as ex:
            failures += 1
            print(f"• ERROR {e['name']}: {type(ex).__name__}: {ex}")
    return failures


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
    ap = argparse.ArgumentParser(description="Compute the social cadence schedule (dry-run by default).")
    ap.add_argument("--write", action="store_true", help="save preview to docs/cadence_preview.md")
    ap.add_argument("--enqueue", action="store_true",
                    help="LIVE: draft captions -> Telegram approval -> write approved schedules into posts_queue.json")
    ap.add_argument("--selftest", action="store_true", help="offline schedule-math test (no Monday call)")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    now = dt.datetime.now(dt.timezone.utc)
    today = now.astimezone(LOCAL_TZ).date()
    events = fetch_events()

    failures = 0
    if args.enqueue:
        failures = run_enqueue(events, today, now)
        print()

    md = build_preview(events, today, now)
    print(md)
    if args.write:
        PREVIEW_PATH.parent.mkdir(exist_ok=True)
        PREVIEW_PATH.write_text(md, encoding="utf-8")
        print(f"\nWrote {PREVIEW_PATH}")

    if failures:
        # Fail the workflow loudly — a silent green run hides broken captioning.
        sys.exit(f"{failures} event(s) failed during the enqueue pass — see ERROR lines above.")


if __name__ == "__main__":
    main()
