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

3. Stories take the whole day (Pedro, 2026-10-28). A day's stories on a
   platform are spread evenly from ~8:30 AM to ~7 PM local in a fixed
   pseudo-random order with a little jitter, whatever slot the cadence engine
   put on them -- so five stories read as one every couple of hours from
   breakfast to the evening, not a burst at 11. A story can therefore go out
   BEFORE its nominal slot time. Same determinism: the day's set decides the
   minutes, nothing is stored, and the Facebook mirror lands with its
   Instagram twin.

Entries scheduled by hand (no `slot`, e.g. schedule_post.py / the Post
Manager at an exact minute) are sent at exactly that minute, as before.
`"spread": false` on any entry opts it out too.

The scheduler stamps each pending entry's computed time into `release_at_utc`
so the dashboard can show when it will really go out; the field is advisory
and recomputed every run.

Self-test (offline): python code/spread.py --selftest
"""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime, time, timedelta, timezone
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

# Stories: the day's set is spread from first to last across this window
# (minutes after local midnight), each nudged by up to +/- STORY_JITTER_MIN
# and clamped to STORY_DAY_CLAMP. A lone story goes out around STORY_SOLO_MIN.
STORY_DAY_START_MIN = 8 * 60 + 30     # ~8:30 AM
STORY_DAY_END_MIN = 19 * 60           # ~7:00 PM
STORY_JITTER_MIN = 20
STORY_DAY_CLAMP = (8 * 60, 19 * 60 + 30)
STORY_SOLO_MIN = 12 * 60


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


def _story_key(entry: dict) -> str:
    """Platform-independent identity of a story on its day: the IG and FB
    copies share it, so they share an order position and a minute."""
    return "|".join(str(x) for x in (
        entry.get("monday_event_id") or entry.get("campaign") or entry.get("id"),
        entry.get("scheduled_for_utc"),
    ))


def _story_order(entry: dict) -> str:
    return hashlib.sha256(_story_key(entry).encode("utf-8")).hexdigest()


def _story_jitter(entry: dict) -> int:
    h = hashlib.sha256((_story_key(entry) + "|jitter").encode("utf-8")).digest()
    return int.from_bytes(h[:4], "big") % (2 * STORY_JITTER_MIN + 1) - STORY_JITTER_MIN


def story_day_plan(posts: list[dict]) -> dict[str, datetime]:
    """Release time per story entry id, spreading each day's stories (per
    platform) evenly across the day. Every story of the day counts, whatever
    its status, so adding one later shifts the others only as much as it must."""
    groups: dict[tuple, list[dict]] = {}
    for p in posts:
        if kind_of(p) != "story" or p.get("spread") is False or not p.get("slot") or not p.get("id"):
            continue
        d = _parse(p["scheduled_for_utc"]).astimezone(LOCAL_TZ).date()
        groups.setdefault((p.get("platform"), d), []).append(p)
    plan: dict[str, datetime] = {}
    span = STORY_DAY_END_MIN - STORY_DAY_START_MIN
    for (_platform, d), ps in groups.items():
        ps.sort(key=_story_order)
        n = len(ps)
        for i, p in enumerate(ps):
            base = STORY_SOLO_MIN if n == 1 else STORY_DAY_START_MIN + i * span / (n - 1)
            m = int(round(base + _story_jitter(p)))
            m = max(STORY_DAY_CLAMP[0], min(STORY_DAY_CLAMP[1], m))
            local = datetime.combine(d, time(0), tzinfo=LOCAL_TZ) + timedelta(minutes=m)
            plan[p["id"]] = local.astimezone(timezone.utc)
    return plan


def release_time(entry: dict, plan: dict | None = None) -> datetime:
    if plan is not None and entry.get("id") in plan:
        return plan[entry["id"]]
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


def stamp_release_times(posts: list[dict], plan: dict | None = None) -> int:
    """Write each pending slot entry's computed release time into
    `release_at_utc` (for the dashboard). Returns how many entries changed."""
    plan = story_day_plan(posts) if plan is None else plan
    changed = 0
    for p in posts:
        if p.get("status") != "pending" or not p.get("slot") or p.get("spread") is False:
            continue
        rel = release_time(p, plan).isoformat()
        if p.get("release_at_utc") != rel:
            p["release_at_utc"] = rel
            changed += 1
    return changed


def select_due(posts: list[dict], now: datetime, plan: dict | None = None) -> tuple[list[dict], list[tuple[dict, str]]]:
    """Which pending entries this run should send, in order, and why the rest wait.

    Returns (send, held) where held is [(entry, reason)] for pending entries
    whose time has come but which are not sent this run. A planned story is
    due at its planned minute (which may precede its slot); everything else
    is due once its scheduled minute has passed.
    """
    plan = story_day_plan(posts) if plan is None else plan

    def gate(p):
        return plan.get(p.get("id")) or _parse(p["scheduled_for_utc"])

    due = [p for p in posts if p.get("status") == "pending" and gate(p) <= now]
    due.sort(key=lambda p: (release_time(p, plan), p.get("id") or ""))
    recent = last_sent(posts)
    sent_this_run: dict[tuple[str, str], int] = {}
    send, held = [], []
    for p in due:
        k = (p.get("platform"), kind_of(p))
        rel = release_time(p, plan)
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

    # Stories spread across the day, not the slot window.
    day = [_e("st" + str(i), nov5_11, event="S" + str(i), fmt="story") for i in range(5)]
    day += [dict(p, id=p["id"] + "fb", platform="facebook") for p in day]
    plan = story_day_plan(day)
    ig_times = sorted(plan["st" + str(i)].astimezone(LOCAL_TZ) for i in range(5))
    mins = [t.hour * 60 + t.minute for t in ig_times]
    check(mins[0] <= 9 * 60 and mins[-1] >= 18 * 60 + 30,
          "5 stories run from ~8:30 (%02d:%02d) to ~7 PM (%02d:%02d)" % (ig_times[0].hour, ig_times[0].minute, ig_times[-1].hour, ig_times[-1].minute))
    gaps = [b - a for a, b in zip(mins, mins[1:])]
    check(min(gaps) >= 90, "stories are at least 90 min apart (min gap %d min)" % min(gaps))
    check(all(plan["st" + str(i)] == plan["st" + str(i) + "fb"] for i in range(5)), "Facebook story lands with its Instagram twin")
    check(plan == story_day_plan(list(reversed(day))), "plan does not depend on queue order")
    solo = story_day_plan([day[0]])["st0"].astimezone(LOCAL_TZ)
    check(11 * 60 + 40 <= solo.hour * 60 + solo.minute <= 12 * 60 + 20, "a lone story goes out around noon (%02d:%02d)" % (solo.hour, solo.minute))
    early_story = min(day[:5], key=lambda p: plan[p["id"]])
    at_9 = datetime(2026, 11, 5, 17, 0, tzinfo=timezone.utc)  # 09:00 Pacific, before the 11:00 slot
    send_e, _ = select_due(day, at_9)
    check([p["id"] for p in send_e] == [early_story["id"], early_story["id"] + "fb"] if plan[early_story["id"]] <= at_9 else not send_e,
          "the first story of the day goes out before its 11:00 slot")
    feed_only = _e("fx", nov5_11, event="FX")
    check("fx" not in story_day_plan([feed_only]), "feed posts keep the slot-window rule")
    n_st = stamp_release_times(day + [feed_only])
    check(n_st == 11 and day[0]["release_at_utc"] == plan["st0"].isoformat() and "release_at_utc" in feed_only,
          "release_at_utc stamped on every pending slot entry (%d)" % n_st)
    check(stamp_release_times(day + [feed_only]) == 0, "re-stamping an unchanged set changes nothing")

    # Pile-up: three feed posts + two stories all due at 11:00; a run at 20:00, past every window.
    now = datetime(2026, 11, 6, 4, 0, tzinfo=timezone.utc)  # 20:00 Pacific
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
    mid = datetime(2026, 11, 5, 21, 40, tzinfo=timezone.utc)  # 13:40 Pacific: late, but not backlog-late
    posts2 = [_e("done", nov5_11, event="E0", status="posted", posted_at=(mid - timedelta(minutes=10)).isoformat()),
              _e("f4", nov5_11, event="E4"), _e("s4", nov5_11, event="E4", fmt="story")]
    send2, held2 = select_due(posts2, mid)
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
