#!/usr/bin/env python3
"""
build_week_carousel.py
----------------------
Queue the Monday "Esta semana en Azúcar" carousel: one post that carries the
whole week's flyers, so the every-week nights stop needing campaigns of their
own.

Why this post exists
--------------------
It is the piece that makes the rest of the cadence affordable. Karaoke was
taking 18 posts for one night and the heels class 32, because the engine knew
only one way to tell anyone about anything. Those nights are habits, not news:
people do not learn karaoke is Wednesday from the eleventh flyer. Put them in
one weekly round-up and their tier can drop to zero posts, which is where the
budget for the marquee shows comes from.

The format earns it too. A carousel takes roughly nine times the saves of a
single image, and Instagram weights saves heavily — a what's-on post is a
reference object people come back to, which is exactly the behaviour that
keeps it alive in the feed all week.

What it builds
--------------
One queue entry per platform, scheduled for Monday morning, carrying
`image_urls` (a list) rather than `image_url`. process_queue turns that into
an Instagram carousel and a Facebook multi-photo post.

Slides are the events' own flyers, chronological, capped at Meta's limit of
10. Anything past the cap still appears in the caption, so a busy week loses
its picture but never its listing.

NOTE: the summary slide Pedro asked for — a card with the week written out —
is not generated here. That needs a rendered image, which this script has no
way to make; the caption carries the same information for now. Worth
revisiting with Canva, which the account already has.

Usage:
    python code/build_week_carousel.py --dry-run     # print, queue nothing
    python code/build_week_carousel.py               # queue it
    python code/build_week_carousel.py --week-of 2026-10-05
    python code/build_week_carousel.py --selftest    # offline, no network
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

MAX_SLIDES = 10          # Meta's carousel limit for API publishing
POST_HOUR, POST_MINUTE = 11, 0   # Monday 11:00 PT, inside the online plateau

SPANISH_DAYS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
HIDDEN_PHASES = {"Cancelled", "Completed"}
VENUE_LINE = "📍 Azúcar at Out & About — 327 W Lewis St, Pasco WA"
SITE_LINE = "🎟️ cluboutandabout.com"


def week_window(week_of: dt.date | None, today: dt.date) -> tuple[dt.date, dt.date]:
    """Monday..Sunday of the week being promoted.

    Given no date, use the week that CONTAINS today rather than the next one:
    the post goes out on Monday morning about the days that follow it, so on
    Monday itself the right answer is this week, not next.
    """
    base = week_of or today
    monday = base - dt.timedelta(days=base.weekday())
    return monday, monday + dt.timedelta(days=6)


def fmt_time(hour, minute) -> str | None:
    if hour is None:
        return None
    suffix = "am" if hour < 12 else "pm"
    h12 = hour % 12 or 12
    return f"{h12}:{minute:02d}{suffix}" if minute else f"{h12}{suffix}"


def event_line(name: str, date: dt.date, time_str: str | None, price: str | None) -> str:
    """One line of the caption: `Vie 26 · Candy Shop · 9pm · $15`."""
    bits = [f"{SPANISH_DAYS[date.weekday()]} {date.day}", name]
    if time_str:
        bits.append(time_str)
    if price:
        p = price.strip()
        bits.append(p if p.startswith("$") or not p[:1].isdigit() else f"${p}")
    return " · ".join(bits)


def build_caption(lines: list[str], monday: dt.date, extra: list[str]) -> str:
    out = ["ESTA SEMANA EN AZÚCAR 🌹", ""]
    out += lines
    if extra:
        out += [""] + extra
    out += ["", VENUE_LINE, SITE_LINE, "",
            "#AzucarPasco #TriCitiesWA #DragShow #NocheLatina"]
    return "\n".join(out)


# ---------- live layer ----------
def collect_week(monday: dt.date, sunday: dt.date):
    """Events in the window, chronological. Needs the Monday board."""
    from build_fb_kit import COL_AGE, COL_DATE, COL_FLYER, COL_PRICE, COL_TIME, col, fetch_items

    found = []
    for item in fetch_items():
        date_iso = (col(item, COL_DATE) or {}).get("date")
        if not date_iso:
            continue
        try:
            d = dt.date.fromisoformat(date_iso)
        except ValueError:
            continue
        if not (monday <= d <= sunday):
            continue

        phase = (col(item, "color_mm3hz990") or {}).get("label")
        if phase in HIDDEN_PHASES:
            continue

        flyer_raw = (col(item, COL_FLYER) or {}).get("value")
        assets = []
        if flyer_raw:
            try:
                v = json.loads(flyer_raw)
                assets = [f.get("assetId") or f.get("asset_id")
                          for f in (v.get("files") or [])]
                assets = [a for a in assets if a]
            except (ValueError, TypeError):
                assets = []

        hour_c = col(item, COL_TIME) or {}
        found.append({
            "id": item["id"],
            "name": (item.get("name") or "").strip() or "Untitled",
            "date": d,
            "time": fmt_time(hour_c.get("hour"), hour_c.get("minute") or 0),
            "price": (col(item, COL_PRICE) or {}).get("text"),
            "age": (col(item, COL_AGE) or {}).get("label"),
            "flyer_assets": assets,
        })
    found.sort(key=lambda e: (e["date"], e["name"]))
    return found


def queue_carousel(events, monday: dt.date, caption: str, image_urls: list) -> int:
    import queue_utils as qu
    from cadence_engine import LOCAL_TZ
    from cap_queue import DEFAULT_CAP, apply_cap

    when_local = dt.datetime(monday.year, monday.month, monday.day,
                             POST_HOUR, POST_MINUTE, tzinfo=LOCAL_TZ)
    utc = when_local.astimezone(dt.timezone.utc)
    campaign = f"week_of_{monday.isoformat()}"

    queue = qu.load_queue()
    # Re-running for the same week replaces its own pending entries rather
    # than stacking a second carousel on top of the first.
    queue["posts"] = [p for p in queue["posts"]
                      if not (p.get("campaign") == campaign and p.get("status") == "pending")]

    for platform in ("instagram", "facebook"):
        queue["posts"].append({
            "id": qu.new_post_id(utc),
            "platform": platform,
            "scheduled_for_utc": utc.isoformat(),
            "image_url": image_urls[0],     # fallback for any older reader
            "image_urls": image_urls,
            "caption": caption,
            "status": "pending",
            "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "posted_at": None,
            "result": None,
            "campaign": campaign,
            "monday_event_id": None,
            "event_date": monday.isoformat(),
            "slot": "morning",
            "tier": "round-up",
        })

    queue["posts"], dropped = apply_cap(queue["posts"], DEFAULT_CAP)
    qu.save_queue(queue)
    if dropped:
        print(f"  cap: {len(dropped)} entries dropped to stay under "
              f"{DEFAULT_CAP} slots/day")
    return sum(1 for p in queue["posts"] if p.get("campaign") == campaign)


def selftest() -> int:
    mon, sun = week_window(None, dt.date(2026, 9, 23))   # a Wednesday
    assert (mon, sun) == (dt.date(2026, 9, 21), dt.date(2026, 9, 27)), (mon, sun)
    # On Monday itself the answer is this week, not next.
    mon2, _ = week_window(None, dt.date(2026, 9, 21))
    assert mon2 == dt.date(2026, 9, 21), mon2
    # An explicit mid-week date still resolves to that week's Monday.
    mon3, sun3 = week_window(dt.date(2026, 10, 8), dt.date(2026, 9, 1))
    assert (mon3, sun3) == (dt.date(2026, 10, 5), dt.date(2026, 10, 11))

    assert fmt_time(21, 0) == "9pm"
    assert fmt_time(21, 30) == "9:30pm"
    assert fmt_time(9, 0) == "9am"
    assert fmt_time(12, 0) == "12pm"
    assert fmt_time(0, 0) == "12am"
    assert fmt_time(None, 0) is None

    line = event_line("Candy Shop", dt.date(2026, 9, 25), "9pm", "15")
    assert line == "Vie 25 · Candy Shop · 9pm · $15", line
    # A price already carrying its own sign is not double-signed.
    assert "$$" not in event_line("X", dt.date(2026, 9, 25), None, "$10")
    # A non-numeric price ("Free") is passed through as written.
    assert event_line("X", dt.date(2026, 9, 26), None, "Free").endswith("Free")
    # No time and no price still gives a usable line.
    assert event_line("X", dt.date(2026, 9, 27), None, None) == "Dom 27 · X"

    cap = build_caption(["Vie 25 · A", "Sáb 26 · B"], dt.date(2026, 9, 21), [])
    assert cap.startswith("ESTA SEMANA EN AZÚCAR")
    assert "Vie 25 · A" in cap and VENUE_LINE in cap
    # Overflow events appear in the caption even without a slide.
    cap2 = build_caption(["a"], dt.date(2026, 9, 21), ["También: Karaoke, Heels"])
    assert "También" in cap2

    print("selftest: all checks passed")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--week-of", type=str, help="any date inside the target week")
    ap.add_argument("--dry-run", action="store_true", help="print, queue nothing")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    from cadence_engine import LOCAL_TZ, download_flyer_files, host_image_on_pages

    today = dt.datetime.now(LOCAL_TZ).date()
    week_of = dt.date.fromisoformat(args.week_of) if args.week_of else None
    monday, sunday = week_window(week_of, today)
    print(f"Week of {monday} – {sunday}\n")

    events = collect_week(monday, sunday)
    if not events:
        print("No events on the board this week — nothing to post.")
        return 0

    lines, extra_names, image_urls = [], [], []
    for e in events:
        lines.append(event_line(e["name"], e["date"], e["time"], e["price"]))
        if len(image_urls) >= MAX_SLIDES or not e["flyer_assets"]:
            if not e["flyer_assets"]:
                print(f"  {e['name']}: no flyer — caption only")
            else:
                extra_names.append(e["name"])
            continue
        paths = download_flyer_files(e, cap=1)
        if not paths:
            print(f"  {e['name']}: flyer download failed — caption only")
            continue
        image_urls.append(host_image_on_pages(paths[0], f"week_{monday.isoformat()}",
                                              len(image_urls)))

    if not image_urls:
        print("No usable flyers this week — nothing to post.")
        return 0

    extra = [f"También: {', '.join(extra_names)}"] if extra_names else []
    caption = build_caption(lines, monday, extra)

    print(f"{len(image_urls)} slide(s), {len(events)} event(s)\n")
    print(caption)
    print()

    if args.dry_run:
        print("(dry run — nothing queued)")
        return 0

    n = queue_carousel(events, monday, caption, image_urls)
    print(f"Queued {n} entries for Monday {monday} {POST_HOUR}:{POST_MINUTE:02d} PT.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
