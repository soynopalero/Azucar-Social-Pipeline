#!/usr/bin/env python3
"""
cap_queue.py
------------
Enforce a GLOBAL daily posting cap across every event in posts_queue.json.

Why this exists as a separate pass
----------------------------------
cadence_engine.py schedules each event in isolation: 3 posts a week at four
weeks out, 5 at two weeks, then every remaining day the week of. That rule is
fine for one event and catastrophic for twelve, because nothing anywhere adds
them up. With a dozen events overlapping it stacked 20-36 posts a day, all at
11:00 and 19:00.

The measured cost of that, from data/insights/ig_media.json (Jun 1 - Sep 20,
105 days of Instagram posts with real reach):

    posts that day   reach per post   total reach that day
    1-2                        335                     572
    3-5                        288                   1,268
    6-9                        179                   1,996
    10-14                      148                   2,071
    15+                        106                   2,511

Going from 1-2 up to 3-5 more than doubles the people reached while each post
loses only 14%. Going from 6-9 to 10-14 moves the total 4% while every post
loses another 17% — that is the range we were living in, paying real audience
fatigue for nothing. Hence a default cap of 4 slots per day, inside the band
where posts still carry their own weight.

A cap cannot live inside the per-event scheduler, because a per-event function
cannot see the other eleven events. So it runs here, over the whole queue, and
is the single place that decides how busy a day is allowed to get.

What it keeps when a day is over cap
------------------------------------
Nearest-to-event first. A "tonight" post is the one that fills a room; a
save-the-date three weeks out is the one nobody needed. Ties break toward the
evening slot, which out-reaches morning in our own numbers (139 vs 121 median).

One SLOT is one Instagram entry plus one Facebook entry, and they are kept or
dropped together — Facebook mirrors Instagram, so splitting a pair would leave
a post on one platform and a hole on the other.

Only `pending` entries are ever touched. Posted and failed entries are history.
Dropped entries are written to archive/posts_dropped.json, not deleted.

Usage:
    python code/cap_queue.py --dry-run      # report only, write nothing
    python code/cap_queue.py                # apply, cap of 4
    python code/cap_queue.py --cap 6        # a looser cap
    python code/cap_queue.py --selftest     # offline rule check
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parent.parent
QUEUE_PATH = REPO_ROOT / "posts_queue.json"
DROPPED_PATH = REPO_ROOT / "archive" / "posts_dropped.json"
LOCAL_TZ = ZoneInfo("America/Los_Angeles")

DEFAULT_CAP = 4

# Evening beats morning on reach in our own data (median 139 vs 121), so when
# two slots are equally close to their event, the morning one yields first.
SLOT_RANK = {"evening": 0, "afternoon": 1, "morning": 2}


def local_day(iso: str) -> dt.date | None:
    try:
        return dt.datetime.fromisoformat(iso).astimezone(LOCAL_TZ).date()
    except (ValueError, TypeError):
        return None


# A marquee show's build-up is worth more than a one-off's at the same distance,
# but not infinitely more — a one-off happening TONIGHT still has to beat a big
# show that is a week and a half away. Expressing the tier as a few days of
# head start keeps both true, where a strict tier-then-distance sort would let
# a marquee post three weeks out bump tonight's show off the calendar.
TIER_HEAD_START = {"marquee": 3, "big show": 3}


def days_until_event(entry: dict) -> int:
    """Effective distance from its event, in days. Lower wins.

    An entry with no readable event date sorts last rather than being dropped
    outright: we cannot prove it is low value, and silently discarding a post
    we failed to parse is the wrong kind of mistake.
    """
    sched = local_day(entry.get("scheduled_for_utc") or "")
    raw = entry.get("event_date")
    if not sched or not raw:
        return 10_000
    try:
        gap = (dt.date.fromisoformat(str(raw)[:10]) - sched).days
    except ValueError:
        return 10_000
    # Entries written before tiers existed carry no tier and simply get no
    # head start, which leaves the old nearest-first behaviour intact.
    return gap - TIER_HEAD_START.get(entry.get("tier"), 0)


def slot_key(entry: dict) -> tuple:
    """One posting moment for one event — the unit kept or dropped together."""
    return (entry.get("campaign"), entry.get("scheduled_for_utc"))


def plan(posts: list[dict], cap: int) -> tuple[set, dict]:
    """Decide which slot keys survive. Returns (keep_keys, per_day_report).

    Pure: takes the queue, returns a decision. Nothing is written here, so the
    dry run and the real run cannot drift apart — they call this same function.
    """
    slots: dict[tuple, list] = defaultdict(list)
    for p in posts:
        # Stories live in their own tray and never crowd the feed, so they
        # are outside the cap entirely.
        if p.get("status") == "pending" and p.get("format") != "story":
            slots[slot_key(p)].append(p)

    by_day: dict[dt.date, list] = defaultdict(list)
    undated = []
    for key, entries in slots.items():
        day = local_day(key[1] or "")
        (by_day[day] if day else undated).append((key, entries))

    keep: set = {k for k, _ in undated}  # unschedulable: leave alone
    report: dict = {}

    for day, items in sorted(by_day.items()):
        items.sort(key=lambda ke: (
            days_until_event(ke[1][0]),
            SLOT_RANK.get(ke[1][0].get("slot"), 9),
            ke[0][1] or "",
        ))
        kept = items[:cap]
        dropped = items[cap:]
        keep.update(k for k, _ in kept)
        if dropped:
            report[day] = {
                "before": len(items),
                "after": len(kept),
                "dropped": [
                    {
                        "campaign": k[0],
                        "when": k[1],
                        "slot": e[0].get("slot"),
                        "days_out": days_until_event(e[0]),
                    }
                    for k, e in dropped
                ],
            }
    return keep, report


def apply_cap(posts: list[dict], cap: int = DEFAULT_CAP) -> tuple[list, list]:
    """Split a queue into (kept, dropped) under the daily cap.

    The shared entry point: both the CLI below and cadence_engine.py call this,
    so the cap can never mean one thing when a human runs it and another when
    the engine does.
    """
    keep, _ = plan(posts, cap)
    kept, dropped = [], []
    for p in posts:
        if p.get("status") != "pending" or p.get("format") == "story" or slot_key(p) in keep:
            kept.append(p)
        else:
            dropped.append(p)
    return kept, dropped


def load(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return default


def selftest() -> int:
    def entry(camp, when, slot, event, status="pending", platform="instagram", tier=None):
        e = {
            "campaign": camp, "scheduled_for_utc": when, "slot": slot,
            "event_date": event, "status": status, "platform": platform,
            "id": f"{camp}_{when}_{platform}",
        }
        if tier:
            e["tier"] = tier
        return e

    # Five slots on one day, cap 2: the two nearest their events survive.
    day = "2026-10-01T18:00:00+00:00"
    posts = []
    for camp, ev in [("a", "2026-10-01"), ("b", "2026-10-02"), ("c", "2026-10-20"),
                     ("d", "2026-10-25"), ("e", "2026-11-01")]:
        when = f"2026-10-01T{18 + len(posts) // 2:02d}:00:00+00:00"
        posts += [entry(camp, when, "evening", ev),
                  entry(camp, when, "evening", ev, platform="facebook")]
    keep, report = plan(posts, cap=2)
    assert len(keep) == 2, keep
    assert {k[0] for k in keep} == {"a", "b"}, keep
    assert report[dt.date(2026, 10, 1)]["before"] == 5

    # Both platforms of a surviving slot survive together.
    survivors = [p for p in posts if slot_key(p) in keep]
    assert len(survivors) == 4
    assert {p["platform"] for p in survivors} == {"instagram", "facebook"}

    # Posted and failed entries are invisible to the cap.
    hist = [entry("z", "2026-10-01T18:00:00+00:00", "evening", "2026-10-01", status="posted"),
            entry("y", "2026-10-01T18:00:00+00:00", "evening", "2026-10-01", status="failed")]
    keep2, _ = plan(hist, cap=1)
    assert keep2 == set(), keep2

    # A day already under cap is untouched and unreported.
    one = [entry("a", "2026-10-05T18:00:00+00:00", "evening", "2026-10-05")]
    keep3, rep3 = plan(one, cap=4)
    assert len(keep3) == 1 and rep3 == {}

    # Ties on distance break toward evening. Both of these land on Pacific
    # Oct 7 — 18:00 UTC is 11:00 PT that morning, and Oct 8 02:00 UTC is
    # 19:00 PT the same evening. Getting that wrong is how a "same day" test
    # quietly becomes a two-day test that passes for the wrong reason.
    tie = [entry("m", "2026-10-07T18:00:00+00:00", "morning", "2026-10-10"),
           entry("n", "2026-10-08T02:00:00+00:00", "evening", "2026-10-10")]
    assert local_day(tie[0]["scheduled_for_utc"]) == local_day(tie[1]["scheduled_for_utc"])
    keep4, _ = plan(tie, cap=1)
    assert [k[0] for k in keep4] == ["n"], keep4

    # An unparseable event date is kept, not silently discarded.
    odd = [entry("q", "2026-10-09T18:00:00+00:00", "evening", "not-a-date")]
    keep5, _ = plan(odd, cap=4)
    assert len(keep5) == 1

    # A big show gets a few days' head start, so at 10 days out it beats a
    # one-off at 8 (10 - 3 = 7).
    when = "2026-10-11T18:00:00+00:00"   # Oct 11, 11:00 PT
    race = [entry("big", when, "morning", "2026-10-21", tier="marquee"),
            entry("small", when, "morning", "2026-10-19")]
    keep6, _ = plan(race, cap=1)
    assert [k[0] for k in keep6] == ["big"], keep6

    # But the head start is finite: a one-off happening in 5 days still wins,
    # because tonight's show beats a marquee that is a week and a half out.
    race2 = [entry("big", when, "morning", "2026-10-21", tier="marquee"),
             entry("small", when, "morning", "2026-10-16")]
    keep7, _ = plan(race2, cap=1)
    assert [k[0] for k in keep7] == ["small"], keep7

    # Entries predating tiers carry none and get no head start — the original
    # nearest-first behaviour, unchanged.
    assert days_until_event(entry("x", when, "morning", "2026-10-21")) == 10
    assert days_until_event(entry("x", when, "morning", "2026-10-21", tier="marquee")) == 7

    # apply_cap splits the same way plan() decides, and loses nothing:
    # every entry comes back in exactly one of the two lists.
    kept, dropped = apply_cap(posts, cap=2)
    assert len(kept) + len(dropped) == len(posts)
    assert all(p.get("status") == "pending" for p in dropped)
    assert {p["id"] for p in kept} | {p["id"] for p in dropped} == {p["id"] for p in posts}
    # Posted history survives any cap.
    kept2, dropped2 = apply_cap(hist, cap=0)
    assert kept2 == hist and dropped2 == []

    print("selftest: all checks passed")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cap", type=int, default=DEFAULT_CAP,
                    help=f"max posting slots per day across all events (default {DEFAULT_CAP})")
    ap.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    ap.add_argument("--selftest", action="store_true", help="offline rule check")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    queue = load(QUEUE_PATH, {"posts": []})
    posts = queue.get("posts", [])
    pending_before = sum(1 for p in posts if p.get("status") == "pending")

    _, report = plan(posts, args.cap)
    kept, dropped = apply_cap(posts, args.cap)

    print(f"Global cap: {args.cap} slots/day ({args.cap} posts per platform per day)\n")
    if not report:
        print("Every day is already at or under the cap — nothing to drop.")
        return 0

    for day in sorted(report):
        r = report[day]
        print(f"  {day}  {r['before']:>2} slots -> {r['after']:>2}   "
              f"(dropping {len(r['dropped'])})")
        for d in r["dropped"]:
            print(f"        - {d['campaign']} · {d['slot']} · {d['days_out']}d before its event")

    print(f"\nPending entries: {pending_before} -> {pending_before - len(dropped)} "
          f"({len(dropped)} dropped, {len(dropped)//2} slots)")

    if args.dry_run:
        print("\n(dry run — nothing written)")
        return 0

    DROPPED_PATH.parent.mkdir(parents=True, exist_ok=True)
    archive = load(DROPPED_PATH, {"posts": []})
    known = {p.get("id") for p in archive.get("posts", [])}
    archive["posts"] = archive.get("posts", []) + [p for p in dropped if p.get("id") not in known]
    DROPPED_PATH.write_text(json.dumps(archive, indent=2, ensure_ascii=False), encoding="utf-8")

    queue["posts"] = kept
    QUEUE_PATH.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")
    docs_copy = REPO_ROOT / "docs" / "posts_queue.json"
    if docs_copy.parent.exists():
        docs_copy.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nWrote {QUEUE_PATH.name}; dropped entries kept in "
          f"{DROPPED_PATH.relative_to(REPO_ROOT)} (nothing deleted).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
