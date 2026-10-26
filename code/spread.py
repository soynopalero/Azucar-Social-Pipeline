#!/usr/bin/env python3
"""
spread.py — spread the day's posts out instead of firing them all at once.

Why this exists
---------------
Every cadence entry is scheduled on the minute of its slot (11:00, 15:00,
19:00 Pacific), and the scheduler posts everything that is due. With four
events live that meant three, four, five flyers and stories hitting Instagram
inside ninety seconds at 11:00, which reads as a bot and buries the earlier
ones. The schedule (which day, which slot) is right; only the clock-time is
too exact.

What it does
------------
Two rules, both applied by the scheduler at posting time. The queue file is
not changed: `scheduled_for_utc` stays the slot time (it is the dedupe key,
and what the dashboard and Post Manager show), and an entry's actual send time
is derived from it on the fly.

1. Release offset. Each slot-scheduled entry gets a deterministic pseudo-random
   delay inside its slot's window (morning 11:00 -> up to 2h30 later,
   afternoon 15:00 -> up to 2h, evening 19:00 -> up to 2h, which covers the
   8 PM online-followers peak). The delay is a hash of the event + day + slot,
   so it is the same on every scheduler run (no drift, nothing to store), and
   the Facebook mirror of an Instagram post keeps the same delay (one post,
   two platforms, as a human would cross-post). Different events land on
   different minutes.

2. Spacing. Even when delays collide, one run sends at most one feed post and
   one story per platform, and it will not send a feed post within
   MIN_GAP_MINUTES of the previous feed post on that platform (likewise for
   stories, with their own gap). The scheduler runs every five minutes, so a
   pile-up drains one at a time. An entry that is already hours late (cron
   outage) skips the gap rule and catches up.

Entries scheduled by hand (no `slot`, e.g. schedule_post.py / the Post
Manager at an exact minute) are sent at exactly that minute, as before.
`"spread": false` on any entry opts it out too.

Self-test (offline): python code/spread.py --selftest
"""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("America/Los_Angeles")

# Slot -> longest delay, in minutes, after the slot's nominal time.
SLOT_WINDOW_MIN = {"morning": 150, "afternoon": 120, "evening": 120}
# Never release after this local hour (a late evening slot stays an evening post).
LATEST_LOCAL_HOUR = 22

# Spacing between sends of the same kind on the same platform.
MIN_GAP_MINUTES = {"feed": 25, "story": 12}
# One run sends at most this many per (platform, kind).
MAX_PER_RUN = 1
# An entry this far past its release time is a backlog, not a pile-up:
# send it without waiting for the gap.
LATE_CATCHUP_MINUTES = 240


def kind_of(entry: dict) -> str:
    return "story" if entry.get("format") == "story" else "feed"


def _parse(s: str) -> datetime:
    d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def release_offset_minutes(entry: dict) -> int:
    """Deterministic delay for a slot-scheduled entry; 0 for exact-time entries."""
    slot = entry.get("slot")
    if entry.get("spread") is False or slot not in SLOT_WINDOW_MIN:
        return 0
    window = SLOT_WINDOW_MIN[slot]
    key = "|".join(str(x) for x in (
        entry.get("monday_event_id") or entry.get("campaign") or entry.get("id"),
        entry.get("scheduled_for_utc"),
        kind_of(entry),
    ))
    h = hashlib.sha256(key.encode("utf-8")).digest()
    return int.from_bytes(h[:4], "big") % (window + 1)


def release_time(entry: dict) -> datetime:
    nominal = _parse(entry["scheduled_for_utc"])
    rel = nominal + timedelta(minutes=release_offset_minutes(entry))
    local = rel.astimezone(LOCAL_TZ)
    cutoff = local.replace(hour=LATEST_LOCAL_HOUR, minute=0, second=0, microsecond=0)
    if local > cutoff >= nominal.astimezone(LOCAL_TZ):
        rel = cutoff.astimezone(timezone.utc)
    return rel


def last_sent(posts: list[dict]) -> dict[tuple[str, str], datetime]:
    """Most recent posted_at per (platform, kind) among posted entries."""
    out: dict[tuple[str, str], datetime] = {}
    for p in posts:
        if p.get("status") != "posted" or not p.get("posted_at"):
            continue
        k = (p.get("platform"), kind_of(p))
        t = _parse(p["posted_at"])
        if k not in out or t > out[k]:
            out[k] = t
    return out


def select_due(posts: list[dict], now: datetime) -> tuple[list[dict], list[tuple[dict, str]]]:
    """Which pending entries this run should send, in order, and why the rest wait.

    Returns (send, held) where held is [(entry, reason)] for pending entries
    whose slot time has passed but which are not sent this run.
    """
    due = [p for p in posts if p.get("status") == "pending" and _parse(p["scheduled_for_utc"]) <= now]
    due.sort(key=lambda p: (release_time(p), p.get("id") or ""))
    recent = last_sent(posts)
    sent_this_run: dict[tuple[str, str], int] = {}
    send, held = [], []
    for p in due:
        k = (p.get("platform"), kind_of(p))
        rel = release_time(p)
        if rel > now:
            held.append((p, "releases at " + rel.astimezone(LOCAL_TZ).strftime("%H:%M") + " local"))
            continue
        if sent_this_run.get(k, 0) >= MAX_PER_RUN:
            held.append((p, "another " + k[1] + " already sent to " + str(k[0]) + " this run"))
            continue
        late = (now - rel) >= timedelta(minutes=LATE_CATCHUP_MINUTES)
        gap = timedelta(minutes=MIN_GAP_MINUTES[k[1]])
        if not late and k in recent and now - recent[k] < gap:
            mins = int((now - recent[k]).total_seconds() // 60)
            held.append((p, "last " + k[1] + " on " + str(k[0]) + " was " + str(mins) + " min ago"))
            continue
        send.append(p)
        sent_this_run[k] = sent_this_run.get(k, 0) + 1
        recent[k] = now  # the next candidate of this kind must wait for the gap
    return send, held


# ---------- self-test ----------

def _e(pid, when_utc, platform="instagram", slot="morning", fmt=None, status="pending", **kw):
    d = {"id": pid, "platform": platform, "scheduled_for_utc": when_utc, "status": status,
         "slot": slot, "monday_event_id": kw.pop("event", pid)}
    if fmt:
        d["format"] = fmt
    d.update(kw)
    return d


def selftest() -> int:
    ok_all = True

    def check(cond, label):
        nonlocal ok_all
        ok_all &= bool(cond)
        print(("  ok   " if cond else "  FAIL ") + label)

    nov5_11 = "2026-11-05T19:00:00+00:00"   # 11:00 Pacific (PST)
    nov5_19 = "2026-11-06T03:00:00+00:00"   # 19:00 Pacific

    a = _e("a", nov5_11, event="E1")
    check(release_offset_minutes(a) == release_offset_minutes(dict(a, id="zzz")),
          "offset depends on event+slot, not on the random entry id")
    check(release_offset_minutes(a) == release_offset_minutes(dict(a, platform="facebook")),
          "Facebook mirror keeps the Instagram post's delay")
    check(release_offset_minutes(a) != release_offset_minutes(dict(a, format="story")),
          "a story and a feed post of the same event get different delays")
    offs = {release_offset_minutes(_e(str(i), nov5_11, event="E" + str(i))) for i in range(40)}
    check(len(offs) > 25 and max(offs) <= 150,
          "40 events spread over the morning window (%d distinct minutes, max %d)" % (len(offs), max(offs)))
    check(release_offset_minutes(_e("m", nov5_11, slot=None)) == 0, "hand-scheduled entry (no slot) keeps its exact minute")
    check(release_offset_minutes(dict(a, spread=False)) == 0, "spread:false opts out")
    ev = _e("v", nov5_19, slot="evening", event="E9")
    check(release_time(ev).astimezone(LOCAL_TZ).hour <= LATEST_LOCAL_HOUR, "evening release never passes 10 PM local")

    # Pile-up: three feed posts + two stories all due at 11:00; a run at 13:40.
    now = datetime(2026, 11, 5, 21, 40, tzinfo=timezone.utc)  # 13:40 Pacific, past every window
    feeds = [_e("f1", nov5_11, event="E1"), _e("f2", nov5_11, event="E2"), _e("f3", nov5_11, event="E3")]
    posts = feeds + [_e("s1", nov5_11, event="E1", fmt="story"), _e("s2", nov5_11, event="E2", fmt="story"),
                     _e("fb1", nov5_11, platform="facebook", event="E1")]
    send, held = select_due(posts, now)
    kinds = [(p["platform"], kind_of(p)) for p in send]
    check(len(send) == 3 and len(set(kinds)) == 3,
          "one feed + one story per platform per run (%d sent, %d held)" % (len(send), len(held)))
    first_feed = min(feeds, key=release_time)["id"]
    check(send[0]["id"] == first_feed or any(p["id"] == first_feed for p in send), "earliest-releasing feed post is the one sent")

    # Gap: a feed post went out 10 minutes ago -> the next waits; a story is unaffected.
    posts2 = [_e("done", nov5_11, event="E0", status="posted", posted_at=(now - timedelta(minutes=10)).isoformat()),
              _e("f4", nov5_11, event="E4"), _e("s4", nov5_11, event="E4", fmt="story")]
    send2, held2 = select_due(posts2, now)
    check([p["id"] for p in send2] == ["s4"] and held2 and held2[0][0]["id"] == "f4",
          "feed post waits out the 25-minute gap, story still goes")

    # Backlog: 5 hours late skips the gap rule.
    late_now = now + timedelta(hours=5)
    posts3 = [_e("done", nov5_11, event="E0", status="posted", posted_at=(late_now - timedelta(minutes=5)).isoformat()),
              _e("f5", nov5_11, event="E5")]
    send3, _ = select_due(posts3, late_now)
    check([p["id"] for p in send3] == ["f5"], "hours-late entry catches up without waiting for the gap")

    # Not yet released: run at 11:02, entry's delay is >5 min -> held with a time.
    early = datetime(2026, 11, 5, 19, 2, tzinfo=timezone.utc)
    big = next(e for e in (_e("x" + str(i), nov5_11, event="X" + str(i)) for i in range(100))
               if release_offset_minutes(e) > 5)
    send4, held4 = select_due([big], early)
    check(not send4 and held4 and "releases at" in held4[0][1], "entry inside its window is held until its minute")

    print("All spread cases passed." if ok_all else "Some spread cases FAILED.")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else 0)
