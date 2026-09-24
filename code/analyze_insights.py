#!/usr/bin/env python3
"""
analyze_insights.py
-------------------
Turn the pulled numbers into the answers we actually want, by joining
data/insights/* back onto posts_queue.json.

The join is what makes this worth more than Metricool for our purposes.
A generic dashboard can tell you post #47 got 300 reach. It cannot tell you
that post #47 was the fourth Bikini Bottoms flyer that day, went out at 7pm
alongside nineteen others, and did a third of the reach of the same flyer on
a quiet Tuesday. We know all of that, because we scheduled it.

The headline question this is built to answer:
    does stacking 20 posts into one evening cost us reach?
See `crowding_table()`. Everything else is supporting detail.

Usage:
    python code/analyze_insights.py                # writes docs/insights-report.md
    python code/analyze_insights.py --print        # also print to stdout
    python code/analyze_insights.py --selftest     # offline checks
"""

import argparse
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data" / "insights"
QUEUE_PATH = REPO_ROOT / "posts_queue.json"
REPORT_PATH = REPO_ROOT / "docs" / "insights-report.md"
PT = ZoneInfo("America/Los_Angeles")

# How many posts, across every event, went out that local day. Boundaries are
# where the current schedule actually lands (see the cadence engine: one slot
# becomes one IG + one FB entry, so "4" is a single event posting twice).
CROWD_BUCKETS = [(1, 4, "1-4 posts"), (5, 9, "5-9 posts"),
                 (10, 19, "10-19 posts"), (20, 999, "20+ posts")]


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return default


def extract_id(entry: dict) -> str | None:
    """Recover the platform object id for a queue entry.

    Two sources, preferred in this order:
      result:    "Instagram media id: 18125845253503265"
                 "Facebook post id: 1663577895770335"
      permalink: ".../201644454280/posts/1686277153500409"

    The result line is the id the API handed back at publish time, so it is
    exact. The permalink is the fallback for older entries written before the
    result line carried the id.
    """
    result = entry.get("result") or ""
    m = re.search(r"(?:media|post) id:\s*(\d+)", result, re.I)
    if m:
        return m.group(1)

    link = entry.get("permalink") or ""
    m = re.search(r"/posts/(\d+)", link)
    if m:
        return m.group(1)
    return None


def index_api_posts(ig_media: dict, fb_posts: dict) -> dict:
    """Map bare object id -> (platform, record).

    Facebook returns composite ids (`{page_id}_{post_id}`) while the queue
    stored only the trailing half, so the suffix is indexed too. Instagram
    ids match outright.
    """
    idx = {}
    for mid, rec in ig_media.items():
        idx[str(mid)] = ("instagram", rec)
    for pid, rec in fb_posts.items():
        idx[str(pid)] = ("facebook", rec)
        if "_" in str(pid):
            idx[str(pid).split("_", 1)[1]] = ("facebook", rec)
    return idx


def num(value) -> float:
    """Coerce one metric to a number; time-series dicts sum, junk becomes 0."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        return float(sum(v for v in value.values() if isinstance(v, (int, float))))
    return 0.0


def post_stats(platform: str, rec: dict) -> dict:
    """Normalise the two platforms onto one vocabulary: reach / interactions.

    Instagram and Facebook name nearly everything differently and Meta has
    renamed several of these mid-flight, so each falls back through its known
    aliases. `reach` is deliberately unique-people, never impressions —
    impressions inflate exactly where we are trying to measure fatigue.
    """
    m = rec.get("metrics") or {}

    if platform == "instagram":
        reach = num(m.get("reach"))
        interactions = num(m.get("total_interactions"))
        if not interactions:
            interactions = (
                num(m.get("likes") or rec.get("like_count"))
                + num(m.get("comments") or rec.get("comments_count"))
                + num(m.get("saved")) + num(m.get("shares"))
            )
        views = num(m.get("views")) or num(m.get("plays")) or num(m.get("impressions"))
    else:
        reach = num(m.get("post_total_media_view_unique")) or num(m.get("post_impressions_unique"))
        interactions = num(m.get("post_engaged_users"))
        if not interactions:
            interactions = (
                num(rec.get("reactions")) + num(rec.get("comments"))
                + num(rec.get("shares"))
            )
        views = num(m.get("post_media_view")) or num(m.get("post_impressions"))

    return {
        "reach": reach,
        "interactions": interactions,
        "views": views,
        # Engagement rate on *reach*, not followers: it answers "of the people
        # who saw this, how many cared", which is the question that survives
        # a changing follower count.
        "eng_rate": (interactions / reach * 100) if reach else None,
    }


def build_rows(queue: dict, idx: dict) -> list[dict]:
    """One row per published post that we have numbers for."""
    posts = queue.get("posts", [])

    posts_per_day = Counter()
    for p in posts:
        s = p.get("scheduled_for_utc")
        if s and p.get("status") == "posted":
            try:
                posts_per_day[datetime.fromisoformat(s).astimezone(PT).date()] += 1
            except ValueError:
                pass

    rows = []
    for p in posts:
        if p.get("status") != "posted":
            continue
        oid = extract_id(p)
        if not oid or oid not in idx:
            continue

        platform, rec = idx[oid]
        stats = post_stats(platform, rec)
        if not stats["reach"]:
            continue  # no reach means Meta gave us nothing; a zero would be a lie

        when = None
        s = p.get("scheduled_for_utc")
        if s:
            try:
                when = datetime.fromisoformat(s).astimezone(PT)
            except ValueError:
                pass

        caption = p.get("caption") or ""
        rows.append({
            **stats,
            "id": oid,
            "platform": platform,
            "campaign": p.get("campaign"),
            "slot": p.get("slot"),
            "when": when,
            "hour": when.hour if when else None,
            "weekday": when.strftime("%A") if when else None,
            "day_volume": posts_per_day.get(when.date(), 0) if when else 0,
            "media_type": rec.get("media_product_type") or rec.get("media_type"),
            "hashtags": caption.count("#"),
            "caption_len": len(caption),
            "permalink": p.get("permalink"),
            "caption_head": caption.split("\n")[0][:70],
        })
    return rows


def med(values) -> float | None:
    vals = [v for v in values if v is not None]
    return round(statistics.median(vals), 1) if vals else None


def group_table(rows, key, label, min_n=3) -> str:
    """Median reach / engagement grouped by one field.

    Median, not mean: one viral post would otherwise drag a whole bucket up
    and hide the pattern. Groups thinner than `min_n` are dropped — with this
    little data a two-post average is noise dressed as a finding.
    """
    groups = defaultdict(list)
    for r in rows:
        k = r.get(key)
        if k is not None:
            groups[k].append(r)

    keep = {k: v for k, v in groups.items() if len(v) >= min_n}
    if not keep:
        return f"\n### {label}\n\n_Not enough data yet._\n"

    out = [f"\n### {label}\n", f"| {label} | Posts | Median reach | Median eng. rate |",
           "|---|---:|---:|---:|"]
    for k, items in sorted(keep.items(), key=lambda kv: -(med([r["reach"] for r in kv[1]]) or 0)):
        rate = med([r["eng_rate"] for r in items])
        out.append(
            f"| {k} | {len(items)} | {med([r['reach'] for r in items]):,.0f} | "
            f"{rate if rate is not None else '—'}% |"
        )
    return "\n".join(out) + "\n"


def crowding_table(rows) -> str:
    """THE question: does a crowded day cost us reach?

    Each post is labelled with how many posts went out that same local day,
    then bucketed. If the bar's own feed is competing with itself, median
    reach falls as the buckets get busier — and that is the number that
    justifies cutting the cadence, rather than my opinion about it.
    """
    buckets = defaultdict(list)
    for r in rows:
        for lo, hi, name in CROWD_BUCKETS:
            if lo <= r["day_volume"] <= hi:
                buckets[name].append(r)
                break

    present = [(n, buckets[n]) for _, _, n in
               [(b[0], b[1], b[2]) for b in CROWD_BUCKETS] if buckets.get(n)]
    if not present:
        return "\n_Not enough published posts to test this yet._\n"

    out = ["\n| Posts that day (all events) | Posts measured | Median reach | "
           "Median eng. rate |", "|---|---:|---:|---:|"]
    baseline = None
    for name, items in present:
        reach = med([r["reach"] for r in items])
        rate = med([r["eng_rate"] for r in items])
        if baseline is None and reach:
            baseline = reach
        delta = ""
        if baseline and reach:
            pct = (reach - baseline) / baseline * 100
            delta = f" ({pct:+.0f}%)" if name != present[0][0] else ""
        out.append(f"| {name} | {len(items)} | {reach:,.0f}{delta} | "
                   f"{rate if rate is not None else '—'}% |")

    n_thin = len(buckets.get(present[0][0], []))
    out.append(
        f"\n_Read the first row as the baseline: what a post does on a quiet day. "
        f"If the busy rows sit well below it, the flyers are eating each other. "
        f"Based on {n_thin} posts in the quietest bucket._"
    )
    return "\n".join(out) + "\n"


def best_hours(daily: dict) -> str:
    """When followers are actually online, averaged over every snapshot we hold.

    This is the metric with a ~30-day shelf life, so early on this section is
    thin by definition and fills in as the cron accumulates days.
    """
    hourly = defaultdict(list)
    for row in daily.values():
        block = (row.get("instagram_online_followers") or {}).get("online_followers")
        if isinstance(block, dict):
            for k, v in block.items():
                if isinstance(v, (int, float)):
                    m = re.search(r"(\d{1,2})", str(k))
                    if m:
                        hourly[int(m.group(1)) % 24].append(v)
    if not hourly:
        return ("\n_No `online_followers` data yet — it needs the daily pull to have "
                "run at least once with the metric available. This is the section "
                "that replaces guessing at 11am and 7pm._\n")

    ranked = sorted(((h, statistics.mean(v)) for h, v in hourly.items()),
                    key=lambda x: -x[1])
    out = ["\n| Hour (Pacific) | Followers online (avg) |", "|---|---:|"]
    for h, v in ranked[:8]:
        out.append(f"| {h:02d}:00 | {v:,.0f} |")
    out.append(f"\n_Peak: **{ranked[0][0]:02d}:00**. Current slots are 11:00 and 19:00._")
    return "\n".join(out) + "\n"


def build_report(rows, daily, ig_media, fb_posts, queue) -> str:
    posted = sum(1 for p in queue.get("posts", []) if p.get("status") == "posted")
    matched = len(rows)

    L = [
        "# Azúcar — real engagement report",
        "",
        f"_Generated {datetime.now(PT).strftime('%Y-%m-%d %H:%M %Z')} by "
        "`code/analyze_insights.py`. Numbers come from the Meta Graph API, "
        "joined to `posts_queue.json`._",
        "",
        "## What this is built on",
        "",
        f"- **{matched}** published posts with metrics, of {posted} marked posted in the queue",
        f"- **{len(ig_media)}** Instagram posts and **{len(fb_posts)}** Facebook posts on file",
        f"- **{len(daily)}** daily account snapshots",
        "",
    ]

    if matched < 20:
        L += ["> ⚠️ **Thin data.** Under 20 matched posts, treat every table below as "
              "a direction to check, not a conclusion. The daily snapshots need "
              "a few weeks to become useful.", ""]

    L += ["## 1. Does posting more cost us reach?", "",
          "The reason we paused. Every published post, labelled with how many posts "
          "went out that same day across all events:", crowding_table(rows)]

    L += ["## 2. When are our followers actually online?", "", best_hours(daily)]

    L += ["## 3. What performs", "",
          group_table(rows, "platform", "Platform"),
          group_table(rows, "media_type", "Media type"),
          group_table(rows, "slot", "Time slot"),
          group_table(rows, "weekday", "Day of week"),
          group_table(rows, "campaign", "Campaign", min_n=4)]

    top = sorted([r for r in rows if r["reach"]], key=lambda r: -r["reach"])[:10]
    if top:
        L += ["\n## 4. Ten best posts we have ever published", "",
              "| Reach | Eng. rate | Platform | When | Opening line |",
              "|---:|---:|---|---|---|"]
        for r in top:
            when = r["when"].strftime("%b %d, %H:%M") if r["when"] else "—"
            rate = f"{r['eng_rate']:.1f}%" if r["eng_rate"] is not None else "—"
            head = r["caption_head"].replace("|", "/")
            L.append(f"| {r['reach']:,.0f} | {rate} | {r['platform']} | {when} | {head} |")

        worst = sorted([r for r in rows if r["reach"]], key=lambda r: r["reach"])[:5]
        L += ["", "### And the five worst", "",
              "| Reach | Eng. rate | Platform | When | Opening line |",
              "|---:|---:|---|---|---|"]
        for r in worst:
            when = r["when"].strftime("%b %d, %H:%M") if r["when"] else "—"
            rate = f"{r['eng_rate']:.1f}%" if r["eng_rate"] is not None else "—"
            head = r["caption_head"].replace("|", "/")
            L.append(f"| {r['reach']:,.0f} | {rate} | {r['platform']} | {when} | {head} |")

    unsupported = set()
    for rec in list(ig_media.values()) + list(fb_posts.values()):
        unsupported.update((rec.get("metrics") or {}).get("_unsupported") or [])
    if unsupported:
        L += ["", "## Metrics this API version no longer returns", "",
              "Listed so a missing number is never mistaken for a zero:", "",
              "".join(f"- `{m}`\n" for m in sorted(unsupported))]

    return "\n".join(L) + "\n"


def selftest() -> int:
    assert extract_id({"result": "Instagram media id: 18125845253503265"}) == "18125845253503265"
    assert extract_id({"result": "Facebook post id: 1663577895770335"}) == "1663577895770335"
    assert extract_id({"permalink": "https://www.facebook.com/201644454280/posts/1686277153500409"}) == "1686277153500409"
    assert extract_id({"result": "publish failed: whatever"}) is None
    assert extract_id({}) is None

    # A composite Facebook id must match the bare id the queue recorded.
    idx = index_api_posts({"111": {}}, {"201644454280_999": {}})
    assert idx["999"][0] == "facebook"
    assert idx["111"][0] == "instagram"

    assert num(5) == 5.0
    assert num({"a": 2, "b": 3}) == 5.0
    assert num(None) == 0.0

    s = post_stats("instagram", {"metrics": {"reach": 100, "total_interactions": 10}})
    assert s["eng_rate"] == 10.0
    # Falls back to summing components when total_interactions is absent.
    s2 = post_stats("instagram", {"metrics": {"reach": 100, "likes": 4, "saved": 1},
                                  "comments_count": 0})
    assert s2["interactions"] == 5.0
    # Zero reach must not divide.
    assert post_stats("instagram", {"metrics": {}})["eng_rate"] is None

    s3 = post_stats("facebook", {"metrics": {"post_impressions_unique": 50},
                                 "reactions": 3, "comments": 1, "shares": 1})
    assert s3["reach"] == 50.0 and s3["interactions"] == 5.0

    rows = [{"day_volume": 2, "reach": 500, "eng_rate": 5.0},
            {"day_volume": 3, "reach": 480, "eng_rate": 4.0},
            {"day_volume": 24, "reach": 120, "eng_rate": 1.0},
            {"day_volume": 22, "reach": 140, "eng_rate": 1.5}]
    table = crowding_table(rows)
    assert "1-4 posts" in table and "20+ posts" in table and "%" in table

    assert "Not enough data yet" in group_table([], "platform", "Platform")

    print("selftest: all checks passed")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--print", action="store_true", dest="do_print")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    ig_media = load_json(DATA_DIR / "ig_media.json", {})
    fb_posts = load_json(DATA_DIR / "fb_posts.json", {})
    daily = load_json(DATA_DIR / "account_daily.json", {})
    queue = load_json(QUEUE_PATH, {"posts": []})

    if not ig_media and not fb_posts:
        print("No insights data found. Run code/pull_insights.py first "
              "(it needs the Meta token — see .github/workflows/insights-pull.yml).")
        return 1

    rows = build_rows(queue, index_api_posts(ig_media, fb_posts))
    report = build_report(rows, daily, ig_media, fb_posts, queue)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Wrote {REPORT_PATH.relative_to(REPO_ROOT)} ({len(rows)} posts matched)")

    if args.do_print:
        print("\n" + report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
