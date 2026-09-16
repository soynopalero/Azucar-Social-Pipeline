#!/usr/bin/env python3
"""
pull_insights.py
----------------
Pull real engagement numbers for @cluboutandabout (Instagram) and the
Out & About Facebook Page, and keep them as a growing history.

WHY THIS IS A SNAPSHOT AND NOT A REPORT
---------------------------------------
This is the part people pay Metricool for, and it is worth being precise
about what is actually being bought. Metricool reads the same public Meta
Graph API this script does, with the same kind of token. What it sells is
not access — it is *memory*. Meta's account-level insights are a short
rolling window: `online_followers` covers roughly the last 30 days and then
it is gone forever. Nobody can go back for it. A tool that has been
snapshotting your account daily since 2024 can show you a two-year trend
that is genuinely unrecoverable from the API today.

So the one thing that matters here is running this on a schedule, starting
now. Per-post metrics can be backfilled whenever we like — they stay
attached to the post. The daily account rows cannot. Every day this does not
run is a row that does not exist later.

WHAT IS WRITTEN (data/insights/)
--------------------------------
  ig_media.json      per-post Instagram metrics, keyed by media id
  fb_posts.json      per-post Facebook metrics, keyed by post id
  account_daily.json one row per calendar day per platform  <- the perishable one
  _metric_support.json  which metric names this API version still answers to

Each section fails independently: a dead Facebook permission must not cost
us the Instagram numbers.

Usage:
    python code/pull_insights.py                 # everything
    python code/pull_insights.py --skip-media    # daily rows only (cheap, fast)
    python code/pull_insights.py --selftest      # offline, no network
"""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from insights_api import (  # noqa: E402
    DATA_DIR,
    GraphError,
    graph_get,
    insights,
    paginate,
    require_env,
)

IG_MEDIA_PATH = DATA_DIR / "ig_media.json"
FB_POSTS_PATH = DATA_DIR / "fb_posts.json"
ACCOUNT_DAILY_PATH = DATA_DIR / "account_daily.json"

IG_MEDIA_FIELDS = (
    "id,caption,media_type,media_product_type,permalink,timestamp,"
    "like_count,comments_count,thumbnail_url,media_url"
)

# Candidate metric names. Anything Meta has retired is dropped by the probing
# in insights_api.insights() and recorded under `_unsupported`, so leaving a
# retired name here is harmless — and leaving its replacement here is how the
# script survives the next rename without an edit.
IG_METRICS = {
    "REELS": [
        "reach", "saved", "likes", "comments", "shares", "total_interactions",
        "views", "plays", "ig_reels_avg_watch_time",
        "ig_reels_video_view_total_time",
    ],
    "STORY": ["reach", "replies", "views", "impressions", "navigation"],
    "FEED": [
        "reach", "saved", "likes", "comments", "shares", "total_interactions",
        "views", "impressions", "profile_visits", "follows",
    ],
}

FB_POST_METRICS = [
    "post_impressions", "post_impressions_unique", "post_engaged_users",
    "post_clicks", "post_reactions_by_type_total", "post_video_views",
]

IG_ACCOUNT_DAY = [
    "reach", "follower_count", "profile_views", "website_clicks",
    "accounts_engaged", "total_interactions", "likes", "comments",
    "saves", "shares", "views",
]

FB_PAGE_DAY = [
    "page_impressions", "page_impressions_unique", "page_post_engagements",
    "page_fans", "page_fan_adds", "page_fan_removes", "page_views_total",
]


def load_store(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            print(f"  ! {path.name} unreadable — starting a fresh store")
    return {}


def save_store(path: Path, data: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def metric_family(node: dict) -> str:
    """Pick the metric list for one Instagram object.

    `media_product_type` is the reliable signal (REELS / FEED / STORY);
    `media_type` only says IMAGE / VIDEO / CAROUSEL_ALBUM and reports VIDEO
    for a Reel, which would ask for Reels metrics on a plain feed video and
    fail the whole batch.
    """
    product = (node.get("media_product_type") or "").upper()
    if product in IG_METRICS:
        return product
    return "REELS" if node.get("media_type") == "VIDEO" else "FEED"


def pull_ig_media(token: str, ig_user_id: str, refresh_days: int) -> int:
    """Per-post Instagram metrics.

    Posts older than `refresh_days` are only fetched once. Engagement on a
    feed post is effectively settled after a couple of weeks, and re-pulling
    two years of back catalogue every night would burn the rate limit for no
    new information.
    """
    store = load_store(IG_MEDIA_PATH)
    cutoff = datetime.now(timezone.utc) - timedelta(days=refresh_days)
    fetched = 0

    for node in paginate(f"{ig_user_id}/media", token, fields=IG_MEDIA_FIELDS):
        mid = node.get("id")
        if not mid:
            continue

        existing = store.get(mid, {})
        ts = node.get("timestamp")
        settled = False
        if ts and existing.get("metrics"):
            try:
                settled = datetime.fromisoformat(ts.replace("Z", "+00:00")) < cutoff
            except ValueError:
                settled = False

        record = {
            **{k: node.get(k) for k in
               ("caption", "media_type", "media_product_type", "permalink",
                "timestamp", "like_count", "comments_count", "media_url",
                "thumbnail_url")},
            "first_seen": existing.get("first_seen", now_iso()),
            "last_pulled": existing.get("last_pulled"),
            "metrics": existing.get("metrics", {}),
        }

        if not settled:
            family = metric_family(node)
            record["metrics"] = insights(
                mid, token, IG_METRICS[family], support_key=f"ig_media:{family}"
            )
            record["last_pulled"] = now_iso()
            fetched += 1
            if fetched % 25 == 0:
                print(f"  ... {fetched} Instagram posts")

        store[mid] = record

    save_store(IG_MEDIA_PATH, store)
    print(f"  Instagram: {len(store)} posts on file, {fetched} refreshed this run")
    return len(store)


def pull_fb_posts(token: str, page_id: str, refresh_days: int) -> int:
    """Per-post Facebook metrics. Same settle-and-stop rule as Instagram."""
    store = load_store(FB_POSTS_PATH)
    cutoff = datetime.now(timezone.utc) - timedelta(days=refresh_days)
    fetched = 0

    fields = (
        "id,created_time,message,permalink_url,full_picture,"
        "shares,attachments{media_type},"
        "reactions.summary(total_count).limit(0),"
        "comments.summary(total_count).limit(0)"
    )

    for node in paginate(f"{page_id}/posts", token, fields=fields):
        pid = node.get("id")
        if not pid:
            continue

        existing = store.get(pid, {})
        ts = node.get("created_time")
        settled = False
        if ts and existing.get("metrics"):
            try:
                settled = datetime.fromisoformat(ts.replace("Z", "+00:00")) < cutoff
            except ValueError:
                settled = False

        attachments = (node.get("attachments") or {}).get("data") or [{}]
        record = {
            "created_time": ts,
            "message": node.get("message"),
            "permalink_url": node.get("permalink_url"),
            "full_picture": node.get("full_picture"),
            "media_type": attachments[0].get("media_type"),
            "shares": (node.get("shares") or {}).get("count", 0),
            "reactions": (node.get("reactions") or {}).get("summary", {}).get("total_count", 0),
            "comments": (node.get("comments") or {}).get("summary", {}).get("total_count", 0),
            "first_seen": existing.get("first_seen", now_iso()),
            "last_pulled": existing.get("last_pulled"),
            "metrics": existing.get("metrics", {}),
        }

        if not settled:
            record["metrics"] = insights(
                pid, token, FB_POST_METRICS, support_key="fb_post"
            )
            record["last_pulled"] = now_iso()
            fetched += 1
            if fetched % 25 == 0:
                print(f"  ... {fetched} Facebook posts")

        store[pid] = record

    save_store(FB_POSTS_PATH, store)
    print(f"  Facebook: {len(store)} posts on file, {fetched} refreshed this run")
    return len(store)


def pull_account_daily(token: str, ig_user_id: str, page_id: str):
    """The perishable rows. Everything here is why the cron matters.

    Written keyed by date so a re-run overwrites rather than duplicates, and
    so a missed day stays visibly missing instead of being quietly averaged
    away by the next run.
    """
    store = load_store(ACCOUNT_DAILY_PATH)
    today = datetime.now(timezone.utc).date().isoformat()
    row = store.get(today, {})
    row["pulled_at"] = now_iso()

    since = int((datetime.now(timezone.utc) - timedelta(days=2)).timestamp())
    until = int(datetime.now(timezone.utc).timestamp())

    try:
        row["instagram"] = insights(
            ig_user_id, token, IG_ACCOUNT_DAY,
            support_key="ig_account_day", period="day", since=since, until=until,
        )
    except GraphError as exc:
        row["instagram"] = {"_error": str(exc)}
        print(f"  ! Instagram account metrics: {exc}")

    # The single most useful row we collect, and the one with the shortest
    # shelf life: hour-by-hour, when are our followers actually on Instagram.
    # This is what replaces guessing at 11am and 7pm.
    try:
        row["instagram_online_followers"] = insights(
            ig_user_id, token, ["online_followers"],
            support_key="ig_online_followers", period="lifetime",
        )
    except GraphError as exc:
        row["instagram_online_followers"] = {"_error": str(exc)}
        print(f"  ! online_followers: {exc}")

    try:
        demo = {}
        for breakdown in ("city", "age", "gender", "country"):
            try:
                got = insights(
                    ig_user_id, token, ["follower_demographics"],
                    support_key=f"ig_demo:{breakdown}", period="lifetime",
                    metric_type="total_value", breakdown=breakdown,
                )
                demo[breakdown] = got.get("follower_demographics__breakdown")
            except GraphError:
                continue
        row["instagram_demographics"] = demo
    except GraphError as exc:
        print(f"  ! demographics: {exc}")

    try:
        row["facebook"] = insights(
            page_id, token, FB_PAGE_DAY,
            support_key="fb_page_day", period="day", since=since, until=until,
        )
    except GraphError as exc:
        row["facebook"] = {"_error": str(exc)}
        print(f"  ! Facebook page metrics: {exc}")

    try:
        row["facebook_fans_online"] = insights(
            page_id, token, ["page_fans_online_per_day", "page_fans_online"],
            support_key="fb_fans_online", period="day", since=since, until=until,
        )
    except GraphError as exc:
        row["facebook_fans_online"] = {"_error": str(exc)}

    store[today] = row
    save_store(ACCOUNT_DAILY_PATH, store)
    print(f"  Account snapshot written for {today} ({len(store)} days on file)")


def selftest() -> int:
    """Offline checks on the logic that does not need a token."""
    from insights_api import _flatten

    assert metric_family({"media_product_type": "REELS"}) == "REELS"
    assert metric_family({"media_product_type": "FEED"}) == "FEED"
    assert metric_family({"media_product_type": "STORY"}) == "STORY"
    # A Reel reports media_type VIDEO; without media_product_type we must not
    # ask for Reels-only metrics on what might be a plain feed video.
    assert metric_family({"media_type": "VIDEO"}) == "REELS"
    assert metric_family({"media_type": "IMAGE"}) == "FEED"
    assert metric_family({}) == "FEED"

    single = {"data": [{"name": "reach", "values": [{"value": 412}]}]}
    assert _flatten(single) == {"reach": 412}

    total = {"data": [{"name": "views", "total_value": {"value": 900}}]}
    assert _flatten(total) == {"views": 900}

    series = {"data": [{"name": "reach", "values": [
        {"value": 1, "end_time": "2026-09-01T07:00:00+0000"},
        {"value": 2, "end_time": "2026-09-02T07:00:00+0000"},
    ]}]}
    assert _flatten(series)["reach"]["2026-09-02T07:00:00+0000"] == 2

    brk = {"data": [{"name": "follower_demographics",
                     "total_value": {"breakdowns": [{"results": []}]}}]}
    assert "follower_demographics__breakdown" in _flatten(brk)

    assert _flatten({"data": [{"values": []}]}) == {}

    print("selftest: all checks passed")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skip-media", action="store_true",
                    help="only the daily account rows (fast; safe to run often)")
    ap.add_argument("--refresh-days", type=int, default=21,
                    help="re-pull per-post metrics for posts newer than this "
                         "many days; older posts are fetched once (default 21)")
    ap.add_argument("--selftest", action="store_true", help="offline checks, no network")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    env = require_env("FB_PAGE_ACCESS_TOKEN", "IG_USER_ID", "FB_PAGE_ID")
    token = env["FB_PAGE_ACCESS_TOKEN"]

    print("Pulling engagement from the Meta Graph API")
    print("  (per-post numbers backfill any time; the daily rows do not — "
          "they are why this runs on a cron)\n")

    failures = []

    print("Daily account snapshot:")
    try:
        pull_account_daily(token, env["IG_USER_ID"], env["FB_PAGE_ID"])
    except Exception as exc:  # noqa: BLE001 - one section must not sink the rest
        failures.append(f"account snapshot: {exc}")
        print(f"  ! failed: {exc}")

    if not args.skip_media:
        print("\nInstagram posts:")
        try:
            pull_ig_media(token, env["IG_USER_ID"], args.refresh_days)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"instagram media: {exc}")
            print(f"  ! failed: {exc}")

        print("\nFacebook posts:")
        try:
            pull_fb_posts(token, env["FB_PAGE_ID"], args.refresh_days)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"facebook posts: {exc}")
            print(f"  ! failed: {exc}")

    if failures:
        print("\nFinished with problems:")
        for f in failures:
            print(f"  - {f}")
        # Partial data is still worth committing, but the run must go red so
        # a quietly-expired token cannot masquerade as a flat month.
        return 1

    print("\nDone. Data in data/insights/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
