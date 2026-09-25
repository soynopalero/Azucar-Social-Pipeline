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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from monday_api import MondayError, monday_query  # noqa: E402

# The cadence below is per-event and cannot see the other eleven events on the
# board. Summed, it produced 20-36 posts a day, and our own reach data says a
# post in that range reaches ~148 people against ~288 in the 3-5/day band. The
# cap is the one place that adds every event up; see code/cap_queue.py.
from cap_queue import DEFAULT_CAP as DAILY_SLOT_CAP, apply_cap  # noqa: E402

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
COL_CAMPAIGN_NOTES = "long_text_mm52r831"   # performer stories/context from the bot's /update flow
COL_CAPTION_FEEDBACK = "long_text_mm53rtrx" # one-shot revision notes from the Redraft prompt (cleared after use)

HIDDEN_PHASES = {"Cancelled", "Completed"}
PLATFORMS = ["instagram", "facebook"]

# Pacific time-of-day slots
SLOTS = {"morning": (11, 0), "afternoon": (15, 0), "evening": (19, 0)}

# ---------- Tiers ----------
#
# The board's Cadence column picks one of these. A tier is a TOTAL budget of
# feed posts for the whole run-up, written as the days before the event that
# each post lands on — not a rate per week.
#
# Why a fixed ladder instead of "N posts a week":
#
# A rate compounds. The old model said 3 posts/week at four weeks out, 5 at two
# weeks, then EVERY REMAINING DAY the week of, which for a single event reads
# reasonable and across twelve events produced 20-36 posts a day. A ladder
# cannot do that: eight entries is eight entries however many events are live.
#
# The shape is back-loaded on purpose. Nobody buys a ticket three weeks out for
# a Tuesday bar night; the posts that fill a room are the ones in the last few
# days. The first post exists to plant the date, and the last one exists to
# convert it. Marquee runs a month (Pedro's spec, 2026-09-25): 1 post in each of
# weeks 4 and 3 out, 2 in week 2 out, 3 the week of; the stories (STORY_RUNGS)
# carry the rest of the frequency.
#
# Every-week nights get an empty ladder deliberately. Karaoke was taking 18
# posts for one night and the heels class 32. People do not learn that karaoke
# is Wednesday from the eleventh flyer — they learn it from it being Wednesday
# every week. Those nights live in the Monday "this week" post and in stories.
TIERS = {
    "marquee":    {"days_before": [24, 17, 12, 8, 5, 3, 0]},     # 7 posts
    "one-time":   {"days_before": [7, 3, 0]},                    # 3 posts
    "every week": {"days_before": []},                           # 0 posts
    # A NEW weekly night. "Every week" assumes people already know the night
    # exists; a new one has no habit behind it yet, so for its first
    # LAUNCH_WEEKS weeks it gets three feed posts a week — the lineup three
    # days out, the drink special / deal the day before, "tonight" the
    # morning of — and then falls back to Every week on its own (see
    # apply_launch_window). Explicit slots: a launch night's rhythm is the
    # same every week, so it doesn't alternate like a one-off's ladder.
    "launch":     {"days_before": [3, 1, 0],                     # 3 posts / week
                   "slots": ["evening", "evening", "morning"]},
}

LAUNCH_WEEKS = 6
# Launch captions are drafted fresh each week, late enough that the Monday
# check-in (guest DJ, flavor of the week) has had a chance to come back.
LAUNCH_DRAFT_DAYS = 3

# ---------- Stories ----------
#
# Stories carry no caption and need no approval: the flyer is the story. They
# sit outside the feed's daily cap (a different tray; they don't bury feed
# posts), which is what lets every-week nights show up on their own night
# without undoing the cap. (days_before, slot) rungs per tier. Every tier gets
# an 11 AM story the morning of the event.
STORY_RUNGS = {
    # 2 stories in each of weeks 4, 3 and 2 out, 5 the week of = 11
    "marquee":    [(26, "morning"), (22, "morning"), (19, "morning"), (15, "morning"),
                   (11, "morning"), (9, "morning"),
                   (4, "morning"), (2, "morning"), (1, "morning"),
                   (0, "morning"), (0, "afternoon")],
    "one-time":   [(5, "morning"), (2, "morning"), (1, "morning"), (0, "morning")],
    "every week": [(2, "morning"), (1, "morning"), (0, "morning")],
    "launch":     [(2, "morning"), (1, "morning"), (0, "afternoon"), (0, "evening")],
}
# Far enough to cover the whole marquee month, so every story is visible in
# the Post Manager as soon as the event is on the board.
STORY_LOOKAHEAD_DAYS = 30
STORY_W, STORY_H = 1080, 1920

# The live board still carries the original labels. Until they are renamed in
# Monday's UI these keep working, so nothing silently stops posting the day
# this ships. Mapped conservatively: no event gets MORE than it used to.
LEGACY_TIERS = {
    # The board's original labels, kept working so a relabel and a deploy never
    # have to happen in the same minute. Mapped so no event gets MORE than it
    # used to.
    "aggressive": "marquee",
    "standard":   "marquee",
    "light":      "one-time",
    # "Big show" was this tier's working name for about a day before the
    # venue's own word won. Anything still carrying it keeps resolving.
    "big show":   "marquee",
}


def resolve_tier(label):
    """Board label -> tier name, or None if it is not one we schedule.

    Accepts the new tier names and the legacy cadence names alike, so the
    board can be relabelled at leisure rather than in lockstep with a deploy.
    """
    if not label:
        return None
    key = " ".join(str(label).strip().lower().split())
    if key in TIERS:
        return key
    return LEGACY_TIERS.get(key)


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
        "campaign_notes": txt(COL_CAMPAIGN_NOTES),
        "caption_feedback": (txt(COL_CAPTION_FEEDBACK) or "").strip() or None,
        "caption_status": (txt(COL_CAPTION_STATUS) or "").strip().lower(),
        "created_by": (txt(COL_CREATED_BY) or "").strip() or None,
        "flyer_assets": flyer_assets,
        "language": language,
    }


def _night_key(name):
    return " ".join((name or "").lower().split())


def apply_launch_window(events):
    """A Launch night runs its launch schedule for LAUNCH_WEEKS weeks, counted
    from its first Launch-labelled date, then is treated as Every week. The
    board only needs "Launch" set once; nobody has to remember to switch it
    back. Mutates each event's cadence in place."""
    starts = {}
    for e in events:
        if e["cadence"] == "launch" and e["date"]:
            k = _night_key(e["name"])
            starts[k] = min(starts.get(k, e["date"]), e["date"])
    for e in events:
        if e["cadence"] == "launch" and e["date"]:
            start = dt.date.fromisoformat(starts[_night_key(e["name"])])
            if dt.date.fromisoformat(e["date"]) >= start + dt.timedelta(weeks=LAUNCH_WEEKS):
                e["cadence"] = "every week"


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
    tier = resolve_tier(cad)
    if not cad:
        reasons.append("no cadence set")
    elif cad == "off":
        reasons.append("cadence = Off")
    elif not tier:
        reasons.append(f"unknown cadence '{cad}'")
    elif not TIERS[tier]["days_before"]:
        # Not an error: an every-week night is meant to ride the Monday
        # round-up post and stories rather than run its own campaign.
        reasons.append(f"tier '{tier}' — covered by the weekly round-up")
    if not e["has_flyer"]:
        reasons.append("no flyer")
    if not e["price"]:
        reasons.append("no price")
    if not e["description"]:
        reasons.append("no description")
    return reasons


# ---------- Schedule math ----------
def schedule_for(event_date, cadence, today):
    """Return a sorted list of (date, slot_name) for one event's tier.

    Walks the tier's ladder of days-before-the-event and keeps the ones that
    have not already passed, so an event added late simply starts partway down
    its ladder instead of trying to post into last week.

    Slots alternate evening/morning for feed variety, except day-of, which is
    always evening: the post that says "tonight" should land while people are
    deciding what to do with their evening, and 19:00-20:00 is where our
    followers-online curve peaks.
    """
    tier = resolve_tier(cadence)
    if not tier:
        return []

    picks = []
    fixed = TIERS[tier].get("slots")
    for i, offset in enumerate(TIERS[tier]["days_before"]):
        d = event_date - dt.timedelta(days=offset)
        if d < today:
            continue  # ladder rung already in the past
        if fixed:
            slot = fixed[i]
        else:
            slot = "evening" if offset == 0 else ("evening" if i % 2 == 0 else "morning")
        picks.append((d, slot))

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

Output ONLY a JSON array of objects, each {{"flyer": <image number, 1-based>, "caption": "<caption text>"}}. No preamble, no code fences."""


def draft_captions(e, n=4):
    key = envvar("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    weekday_en, weekday_es = event_weekday(e["date"])
    history = caption_history(e["name"])
    runbook = find_runbook(e["name"])
    images = flyer_images_b64(e, cap=8)

    if len(images) > 1:
        n = min(10, max(4, len(images) + 2))
        user = (
            f"This event has {len(images)} flyer images attached, in order (image 1 = first). "
            "CURATE the campaign — study each image and decide what it is: a full-cast/hero flyer, "
            "an individual performer spotlight, or a variant.\n"
            f"Draft ~{n} captions, each PAIRED to the image it belongs with:\n"
            "- For the hero/full-cast flyer: 2-3 campaign captions (hype announcement, vibe/sensory, info-forward).\n"
            "- For each individual performer flyer: ONE spotlight caption about THAT performer "
            "(their name is on the artwork; use the campaign notes for their story — debut, birthday, hosting, etc.).\n"
            "- COVERAGE IS MANDATORY: every distinct performer image MUST appear as some caption's flyer. "
            "Never pair more than 3 captions with the hero image.\n"
            "- Order the array: hero captions first, then spotlights.\n"
            "Every caption must stand alone and still end with the full info block.\n\n"
        )
    elif resolve_tier(e.get("cadence")) == "launch":
        n = 3
        user = (
            "This is a NEW weekly night in its launch weeks. Draft exactly 3 captions for THIS week, "
            "in posting order — they go out 3 days before, the day before, and the morning of:\n"
            "1) The lineup: who's on the decks / stage this week (use the campaign notes).\n"
            "2) The reason to come: the drink special, flavor of the week, door deal.\n"
            "3) Tonight: short and urgent — doors time and the deal.\n"
            "Keep the night's name front and center so it sticks as a weekly habit. "
            "Pair every caption with image 1.\n\n"
        )
    else:
        user = (
            f"Draft {n} distinct captions for this event's multi-week posting campaign. Angles: "
            "1) hype announcement, 2) vibe/sensory, 3) community/come-as-you-are, 4) info-forward. "
            "They rotate across many days, so each must stand alone. Pair every caption with image 1.\n\n"
        )
    user += (
        f"Event: {e['name']}\nDate: {e['date']}" + (f" ({weekday_en})" if weekday_en else "") + "\n"
        f"Description: {e['description']}\nPrice: {e['price']}"
    )
    if e.get("campaign_notes"):
        user += ("\n\nCampaign notes from the venue (REAL facts about the performers/night — "
                 f"feature them in the matching captions):\n{e['campaign_notes'][:1500]}")
    if e.get("caption_feedback"):
        prev = load_captions_file(e["id"]) or []
        if prev:
            user += "\n\nPREVIOUS captions (the venue mostly liked these — revise, don't start over):\n"
            user += "\n\n".join(f"[{i+1}] (flyer {c.get('flyer')}) {c['caption'][:600]}"
                                for i, c in enumerate(prev[:10]))
        user += ("\n\nREVISION REQUEST from the venue — apply this to the set: "
                 f"{e['caption_feedback'][:800]}")
    if history:
        user += "\n\nPast captions for this show (match their voice and their FACTS — hosts and names in them are real):\n"
        user += "\n\n".join(f"[{i+1}] {h[:900]}" for i, h in enumerate(history))
    if runbook:
        user += f"\n\nRunbook for this recurring show (canonical facts — hosts, times, rituals):\n{runbook}"
    if images:
        user += "\n\nThe flyer image(s) are attached in order — read them: lineup names, times, and themes on the artwork are real and usable."

    images_content = [{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b}} for b in images]

    caps, text = [], ""
    for attempt in (1, 2):
        prompt = user if attempt == 1 else (user +
            '\n\nIMPORTANT: Your previous reply was not machine-readable. Respond with '
            'NOTHING except the JSON array of {"flyer": <image number>, "caption": "..."} objects.')
        # Up to 10 long paired captions ≈ well past the old 3500-token budget —
        # a short cap truncates the JSON mid-array and the parse dies.
        body = {"model": "claude-sonnet-5", "max_tokens": 12000,
                "system": caption_system(e.get("language"), weekday_en, weekday_es),
                "messages": [{"role": "user", "content": images_content + [{"type": "text", "text": prompt}]}]}
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
        if data.get("stop_reason") == "max_tokens":
            print("  (model hit max_tokens — the last caption is truncated and gets dropped)")
        caps = parse_caption_array(text, images, e["date"])
        if caps:
            break
        # Log what the model actually said so the run log diagnoses itself.
        print(f"  model output had no caption array (attempt {attempt}); it began: {text[:300]!r}")
    if not caps:
        raise RuntimeError(f"model returned no captions after retry; output began: {text[:200]!r}")
    return caps[:n]


def parse_caption_array(text, images, date_iso):
    """Pull the caption array out of the model's reply. Returns [] when there's
    no array at all (e.g. the model replied in prose) — caller retries."""
    start, end = text.find("["), text.rfind("]")
    if start == -1:
        return []
    # strict=False: captions carry the info block on its own lines, and the model
    # often emits those line breaks raw instead of as \n. Strict JSON rejects a
    # control character inside a string, which used to kill the whole array —
    # and the salvage below with it, since it failed on the very first object.
    try:
        raw = json.loads(text[start:end + 1], strict=False) if end > start else []
    except json.JSONDecodeError:
        raw = []
    if not raw:
        # Truncated/malformed: salvage every complete {...} object after the bracket.
        # Skip past a broken one rather than giving up on the rest of the array.
        raw, dec, i = [], json.JSONDecoder(strict=False), text.find("{", start)
        while i != -1:
            try:
                obj, obj_end = dec.raw_decode(text, i)
            except json.JSONDecodeError:
                i = text.find("{", i + 1)
                continue
            if isinstance(obj, dict):
                raw.append(obj)
            i = text.find("{", obj_end)
        if raw:
            print(f"  (salvaged {len(raw)} caption object(s) from malformed model output)")
    # Normalize to paired dicts: {"flyer": 1-based index or None, "caption": str}.
    caps = []
    for item in raw:
        if isinstance(item, dict) and str(item.get("caption") or "").strip():
            fl = item.get("flyer")
            fl = int(fl) if isinstance(fl, (int, float, str)) and str(fl).isdigit() else None
            if fl is not None and images:
                fl = max(1, min(fl, len(images)))
            caps.append({"flyer": fl, "caption": fix_weekdays(str(item["caption"]).strip(), date_iso)})
        elif isinstance(item, str) and item.strip():
            caps.append({"flyer": None, "caption": fix_weekdays(item.strip(), date_iso)})
    return caps


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
    """Telegram caps messages at 4096 chars — a 10-caption curated set is far
    bigger, so captions go out in batches and the buttons ride the last message."""
    chat = chat_for(e)
    tg_call("sendMessage", {"chat_id": chat, "text":
            f"📣 Captions ready — {e['name']} ({e['date']}, "
            f"{(e['cadence'] or '?').capitalize()} cadence) — {len(captions)} variants incoming:"})
    buf = ""
    for i, c in enumerate(captions, 1):
        short = c if len(c) <= 900 else c[:900] + "…"
        block = f"— Variant {i} —\n{short}\n\n"
        if buf and len(buf) + len(block) > 3500:
            tg_call("sendMessage", {"chat_id": chat, "text": buf.rstrip()})
            buf = ""
        buf += block
    if buf:
        tg_call("sendMessage", {"chat_id": chat, "text": buf.rstrip()})
    tg_call("sendMessage", {
        "chat_id": chat,
        "text": "✅ Approve queues the full posting schedule (each caption posts with its matching flyer). ✏️ Redraft asks for fresh takes.",
        "reply_markup": {"inline_keyboard": [[
            {"text": "✅ Approve", "callback_data": f"cap:approve:{e['id']}"},
            {"text": "✏️ Redraft", "callback_data": f"cap:regen:{e['id']}"},
        ]]},
    })


def ask_week_notes(e):
    """Monday check-in for a launch night: the week's specifics make the
    captions. The bot saves a reply to Campaign Notes; no reply just means the
    draft uses general copy for the night."""
    d = dt.date.fromisoformat(e["date"])
    when = d.strftime("%A, %b ") + str(d.day)
    tg_call("sendMessage", {
        "chat_id": chat_for(e),
        "text": (f"🍬 {e['name']} is this {when}.\n\n"
                 "What's special this week? Guest DJ, flavor of the week, drink special, theme — "
                 "anything real we can post about. Captions get drafted "
                 f"{LAUNCH_DRAFT_DAYS} days before and come here for approval as usual.\n\n"
                 "No answer = general captions for the night."),
        "reply_markup": {"inline_keyboard": [[
            {"text": "📝 Add this week's details", "callback_data": f"notes:{e['id']}"},
        ]]},
    })


def download_flyer_files(e, cap=12):
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


def _caption_text(cap):
    return cap["caption"] if isinstance(cap, dict) else cap


def _paired_image(cap, image_urls, i):
    """Curated pairing: a caption drafted for flyer N posts WITH flyer N.
    Legacy string captions (and unpaired ones) rotate through the set."""
    if isinstance(cap, dict) and cap.get("flyer"):
        return image_urls[(int(cap["flyer"]) - 1) % len(image_urls)]
    return image_urls[i % len(image_urls)]


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
                "image_url": _paired_image(captions[i % len(captions)], image_urls, i),
                "caption": _caption_text(captions[i % len(captions)]),
                "status": "pending",
                "created_at": created,
                "posted_at": None,
                "result": None,
                "campaign": campaign,
                "monday_event_id": e["id"],
                "event_date": e["date"],
                "slot": s,
                # Recorded so the daily cap can prefer a big show over a
                # one-off when both are competing for the same day, and so the
                # insights report can compare tiers later.
                "tier": resolve_tier(e["cadence"]),
            })
    # Enforce the global daily cap across EVERY event before saving. This runs
    # here, on the whole queue, rather than inside schedule_for(), because a
    # per-event function has no way to know what the other events already
    # claimed. Nearest-to-event wins, so a "tonight" post displaces a
    # save-the-date three weeks out rather than the other way round.
    queue["posts"], dropped = apply_cap(queue["posts"], DAILY_SLOT_CAP)
    qu.save_queue(queue)

    if dropped:
        mine = sum(1 for p in dropped if p.get("monday_event_id") == e["id"])
        others = len(dropped) - mine
        print(f"    cap {DAILY_SLOT_CAP}/day: dropped {len(dropped)} entries "
              f"({mine} from this event, {others} from events further out)")

    return sum(1 for p in queue["posts"]
               if p.get("monday_event_id") == e["id"] and p.get("status") == "pending")


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


CAPTIONS_DIR = REPO_ROOT / "docs" / "captions"


def save_captions_file(item_id, caps):
    """Full paired captions live in the repo (committed by the workflow) —
    Monday's long_text 2000-char cap only holds a preview."""
    CAPTIONS_DIR.mkdir(parents=True, exist_ok=True)
    (CAPTIONS_DIR / f"{item_id}.json").write_text(
        json.dumps({"captions": caps}, ensure_ascii=False, indent=1), encoding="utf-8")


def load_captions_file(item_id):
    p = CAPTIONS_DIR / f"{item_id}.json"
    if not p.exists():
        return None
    try:
        caps = json.loads(p.read_text(encoding="utf-8")).get("captions")
        return caps or None
    except (OSError, json.JSONDecodeError):
        return None


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
            if resolve_tier(e["cadence"]) == "launch" and st in ("", "asked_notes"):
                days_out = (dt.date.fromisoformat(e["date"]) - today).days
                if st == "" and today.weekday() == 0 and days_out <= 6:
                    ask_week_notes(e)
                    monday_set_text(e["id"], COL_CAPTION_STATUS, "asked_notes")
                    print(f"• asked for this week's details: {e['name']} ({e['date']})")
                    continue
                if days_out > LAUNCH_DRAFT_DAYS:
                    print(f"• launch week not open yet (drafts {LAUNCH_DRAFT_DAYS} days out): "
                          f"{e['name']} ({e['date']})")
                    continue
                st = ""
            if st in ("", "regenerate"):
                caps = draft_captions(e)  # paired dicts {flyer, caption}
                save_captions_file(e["id"], caps)  # full set, no truncation
                texts = [c["caption"] for c in caps]
                monday_set_long_text(e["id"], COL_CAPTIONS,
                                     json.dumps(fit_captions_for_monday(texts), ensure_ascii=False))
                monday_set_text(e["id"], COL_CAPTION_STATUS, "needs_review")
                if e.get("caption_feedback"):
                    # One-shot notes: applied to this draft, cleared for the next.
                    monday_set_long_text(e["id"], COL_CAPTION_FEEDBACK, "")
                notify_captions_review(e, texts)
                print(f"• drafted {len(caps)} captions, sent for review: {e['name']}")
            elif st == "needs_review":
                print(f"• awaiting Telegram approval: {e['name']}")
            elif st == "approved":
                # Prefer the repo file (full paired set); fall back to the
                # Monday column (bot-approved intake captions, plain strings).
                caps = load_captions_file(e["id"]) or parse_captions(e.get("captions_json"))
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


# ---------- Stories pass ----------
STORY_MEDIA = REPO_ROOT / "docs" / "media" / "stories"


def story_eligible(e, today):
    """Stories need only a live date and a flyer — no price, description or
    caption approval, since nothing but the artwork goes out."""
    if not e["date"] or e["phase"] in HIDDEN_PHASES or not e["has_flyer"]:
        return False
    try:
        ed = dt.date.fromisoformat(e["date"])
    except ValueError:
        return False
    return ed >= today and resolve_tier(e["cadence"]) in STORY_RUNGS


def story_slots(e, today, now):
    ed = dt.date.fromisoformat(e["date"])
    out = []
    for offset, slot in STORY_RUNGS[resolve_tier(e["cadence"])]:
        d = ed - dt.timedelta(days=offset)
        if d < today or (d - today).days > STORY_LOOKAHEAD_DAYS:
            continue
        if to_local_dt(d, slot) < now:
            continue
        out.append((d, slot))
    return out


def make_story_image(src, out):
    """1080x1920 story frame: the whole flyer centred, a blurred, darkened copy
    of itself filling the rest — so nothing on the artwork is ever cropped."""
    from PIL import Image, ImageEnhance, ImageFilter

    img = Image.open(src).convert("RGB")
    scale = max(STORY_W / img.width, STORY_H / img.height)
    bw, bh = round(img.width * scale), round(img.height * scale)
    left, top = (bw - STORY_W) // 2, (bh - STORY_H) // 2
    bg = img.resize((bw, bh)).crop((left, top, left + STORY_W, top + STORY_H))
    bg = ImageEnhance.Brightness(bg.filter(ImageFilter.GaussianBlur(40))).enhance(0.5)
    fit = min(STORY_W / img.width, STORY_H / img.height)
    fw, fh = round(img.width * fit), round(img.height * fit)
    bg.paste(img.resize((fw, fh)), ((STORY_W - fw) // 2, (STORY_H - fh) // 2))
    out.parent.mkdir(parents=True, exist_ok=True)
    bg.save(out, "JPEG", quality=88)


def story_image_url(e):
    out = STORY_MEDIA / f"{e['id']}.jpg"
    if not out.exists():
        make_story_image(download_flyer_files(e, cap=1)[0], out)
    return f"{PAGES_BASE}/media/stories/{out.name}"


def run_stories(events, today, now):
    """Queue the coming week's stories. Idempotent: a story already queued for
    an event at a given time is left alone, and pending stories for events that
    were cancelled or switched Off are withdrawn."""
    import queue_utils as qu

    print("=== Stories pass ===")
    queue = qu.load_queue()
    live = {e["id"] for e in events if story_eligible(e, today)}
    before = len(queue["posts"])
    queue["posts"] = [p for p in queue["posts"] if not (
        p.get("format") == "story" and p.get("status") == "pending"
        and p.get("monday_event_id") not in live)]
    withdrawn = before - len(queue["posts"])
    have = {(p.get("monday_event_id"), p.get("scheduled_for_utc"), p.get("platform"))
            for p in queue["posts"] if p.get("format") == "story"}

    added, failures = 0, 0
    created = now.isoformat()
    for e in events:
        if e["id"] not in live:
            continue
        todo = []
        for d, s in story_slots(e, today, now):
            utc = to_local_dt(d, s).astimezone(dt.timezone.utc)
            for platform in PLATFORMS:
                if (e["id"], utc.isoformat(), platform) not in have:
                    todo.append((utc, s, platform))
        if not todo:
            continue
        try:
            url = story_image_url(e)
        except Exception as ex:
            failures += 1
            print(f"• ERROR story image {e['name']}: {type(ex).__name__}: {ex}")
            continue
        campaign = "story_" + "".join(ch if ch.isalnum() else "_" for ch in (e["name"] or "").lower()).strip("_")
        for utc, s, platform in todo:
            queue["posts"].append({
                "id": qu.new_post_id(utc),
                "platform": platform,
                "format": "story",
                "scheduled_for_utc": utc.isoformat(),
                "image_url": url,
                "caption": "",
                "status": "pending",
                "created_at": created,
                "posted_at": None,
                "result": None,
                "campaign": campaign,
                "monday_event_id": e["id"],
                "event_date": e["date"],
                "slot": s,
                "tier": resolve_tier(e["cadence"]),
            })
            added += 1
        print(f"• {len(todo)} story entries: {e['name']} ({e['date']})")
    if added or withdrawn:
        qu.save_queue(queue)
    print(f"stories: {added} added, {withdrawn} withdrawn")
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
def parser_selftest():
    """Guard the caption parser against the shapes the model actually emits."""
    cases = [
        ("clean array",
         '[{"flyer": 1, "caption": "One"}, {"flyer": 2, "caption": "Two"}]', 2),
        # The 2026-08-31 failure: real line breaks inside the caption string.
        ("raw newlines in caption",
         '[\n  {"flyer": 1, "caption": "Hype line.\n\n📍 327 W Lewis St\n🎟️ $10"},\n'
         '  {"flyer": 2, "caption": "Spotlight.\n\nDoors 8pm"}\n]', 2),
        ("code fence around it",
         '```json\n[{"flyer": 1, "caption": "One"}]\n```', 1),
        # Truncated at max_tokens: keep the complete objects, drop the partial one.
        ("truncated mid-array",
         '[{"flyer": 1, "caption": "One"}, {"flyer": 2, "caption": "Two"}, {"flyer": 3, "capt', 2),
        ("prose, no array", "Sure! Here are some captions for the show.", 0),
    ]
    failures = 0
    for name, text, want in cases:
        got = len(parse_caption_array(text, ["img1", "img2"], "2026-09-05"))
        ok = got == want
        failures += 0 if ok else 1
        print(f"  [{'ok ' if ok else 'FAIL'}] {name}: {got} caption(s), expected {want}")
    return failures


def selftest():
    print("Caption-parser self-test\n")
    failures = parser_selftest()
    print()

    today = dt.date(2026, 7, 1)
    event = dt.date(2026, 8, 8)  # ~5.4 weeks out (a Saturday)
    print(f"Self-test - event {event}, today {today} ({(event - today).days} days out)\n")
    for cad in ("marquee", "one-time", "every week"):
        sched = schedule_for(event, cad, today)
        print(f"=== {cad.upper()}: {len(sched)} posts ({len(sched) * len(PLATFORMS)} queue entries) ===")
        for d, s in sched:
            print(f"  {d.strftime('%a %Y-%m-%d')}  {s}  (T-{(event - d).days})")
        print()

    # --- tier rules ---
    assert resolve_tier("Marquee") == "marquee"
    assert resolve_tier("  ONE-TIME ") == "one-time"
    assert resolve_tier("Standard") == "marquee", "legacy labels must keep working"
    assert resolve_tier("Aggressive") == "marquee"
    assert resolve_tier("Big Show") == "marquee", "the one-day-old name must still resolve"
    assert resolve_tier("Light") == "one-time"
    assert resolve_tier("Off") is None
    assert resolve_tier("") is None and resolve_tier(None) is None

    # A ladder is a fixed budget, whatever else is on the board. This is the
    # property the old rate model could not hold.
    assert len(schedule_for(event, "marquee", today)) == 7
    assert len(schedule_for(event, "one-time", today)) == 3
    assert schedule_for(event, "every week", today) == []

    # Day-of is always the evening slot.
    day_of = [(d, s) for d, s in schedule_for(event, "marquee", today) if d == event]
    assert day_of and day_of[0][1] == "evening", day_of

    # Pedro's marquee month, per week counted back from the event
    # (week 4 out, 3 out, 2 out, week of): posts 1/1/2/3, stories 2/2/2/5.
    def per_week(offsets):
        return [sum(1 for o in offsets if lo <= o <= lo + 6) for lo in (21, 14, 7, 0)]
    assert per_week(TIERS["marquee"]["days_before"]) == [1, 1, 2, 3]
    assert per_week([o for o, _ in STORY_RUNGS["marquee"]]) == [2, 2, 2, 5]
    assert len(STORY_RUNGS["one-time"]) == 4 and len(STORY_RUNGS["every week"]) == 3

    # An event added late starts partway down its ladder rather than trying to
    # post into the past — and still keeps its day-of post.
    late = schedule_for(event, "marquee", event - dt.timedelta(days=3))
    assert len(late) == 2, late          # the 3 and 0 rungs
    assert all(d >= event - dt.timedelta(days=3) for d, _ in late)
    assert late[-1][0] == event

    # An event today still gets its one post rather than nothing.
    assert len(schedule_for(event, "one-time", event)) == 1

    # Launch: three feed posts a week on fixed slots, "tonight" in the morning.
    fri = dt.date(2026, 10, 2)
    launch = schedule_for(fri, "launch", fri - dt.timedelta(days=7))
    assert [(fri - d).days for d, _ in launch] == [3, 1, 0], launch
    assert [s for _, s in launch] == ["evening", "evening", "morning"], launch
    assert resolve_tier("Launch") == "launch"

    # The launch window closes by itself after LAUNCH_WEEKS weeks.
    evs = [{"name": "Candy Shop", "date": (fri + dt.timedelta(weeks=w)).isoformat(),
            "cadence": "launch"} for w in range(8)]
    evs.append({"name": "Karaoke", "date": fri.isoformat(), "cadence": "every week"})
    apply_launch_window(evs)
    assert [e["cadence"] for e in evs[:8]] == ["launch"] * 6 + ["every week"] * 2, evs
    assert evs[8]["cadence"] == "every week"

    # Stories: every tier that posts gets a day-of story; Off gets none.
    for tier in ("marquee", "one-time", "every week", "launch"):
        assert any(o == 0 for o, _ in STORY_RUNGS[tier]), tier
    ev = {"id": "1", "name": "X", "date": fri.isoformat(), "phase": None,
          "has_flyer": True, "cadence": "every week"}
    wed = fri - dt.timedelta(days=2)
    wed_now = dt.datetime(wed.year, wed.month, wed.day, 8, tzinfo=LOCAL_TZ)
    assert story_eligible(ev, wed)
    assert story_slots(ev, wed, wed_now) == [(wed, "morning"), (fri - dt.timedelta(days=1), "morning"),
                                             (fri, "morning")]
    ev["cadence"] = "launch"
    assert len(story_slots(ev, wed, wed_now)) == 4
    ev["cadence"] = "off"
    assert not story_eligible(ev, wed)

    print("tier rules: all checks passed\n")

    if failures:
        sys.exit(f"{failures} caption-parser self-test case(s) failed.")


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
    apply_launch_window(events)

    failures = 0
    if args.enqueue:
        failures = run_enqueue(events, today, now)
        failures += run_stories(events, today, now)
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
    try:
        main()
    except MondayError as e:
        sys.exit(f"Monday API error: {e}")
