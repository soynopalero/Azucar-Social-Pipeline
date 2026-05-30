"""
list_scheduled.py
-----------------
Unified view of scheduled posts across platforms:
  - Instagram pending posts in posts_queue.json (queued in our pipeline)
  - Facebook posts scheduled via the Graph API (page-level scheduled_posts)

Note: posts scheduled directly in Meta Business Suite's GUI calendar are NOT
visible — Meta doesn't expose those via the public API.

Usage:
    python list_scheduled.py
    python list_scheduled.py --json    # machine-readable output
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv

# load .env from code/ so this works regardless of CWD
load_dotenv(Path(__file__).resolve().parent / ".env")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from queue_utils import load_queue, fmt_local, from_utc_iso

LOCAL_TZ = ZoneInfo("America/Los_Angeles")
PAGE_ID = os.getenv("FB_PAGE_ID")
PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
GRAPH_API = "https://graph.facebook.com/v19.0"


def get_pending_by_platform(platform: str) -> list:
    """Return pending posts for a specific platform from our queue, sorted by scheduled time."""
    queue = load_queue()
    pending = [
        p for p in queue.get("posts", [])
        if p["status"] == "pending" and p.get("platform") == platform
    ]
    pending.sort(key=lambda p: p["scheduled_for_utc"])
    return pending


def get_scheduled_fb() -> list:
    """Return scheduled FB posts via Graph API, sorted by scheduled time."""
    if not PAGE_ID or not PAGE_ACCESS_TOKEN:
        return []
    try:
        r = requests.get(
            f"{GRAPH_API}/{PAGE_ID}/scheduled_posts",
            params={
                "access_token": PAGE_ACCESS_TOKEN,
                "fields": "id,message,scheduled_publish_time,created_time,permalink_url",
                "limit": 100,
            },
            timeout=30,
        )
        data = r.json()
    except requests.RequestException as e:
        print(f"⚠️  FB query failed: {e}", file=sys.stderr)
        return []
    if "error" in data:
        print(f"⚠️  FB API error: {data['error'].get('message')}", file=sys.stderr)
        return []
    posts = data.get("data", [])
    posts.sort(key=lambda p: int(p.get("scheduled_publish_time") or 0))
    return posts


def fmt_fb_time(ts) -> str:
    if ts is None:
        return "(no time)"
    dt = datetime.fromtimestamp(int(ts), tz=timezone.utc).astimezone(LOCAL_TZ)
    return dt.strftime("%Y-%m-%d %I:%M %p %Z").replace(" 0", " ")


def _print_pipeline_entries(entries: list):
    if not entries:
        print("  (none)\n")
        return
    for p in entries:
        caption_preview = p["caption"].split("\n")[0][:60]
        print(f"  • {fmt_local(p['scheduled_for_utc'])}")
        print(f"    {caption_preview}")
        print(f"    id: {p['id']}  |  image: {p['image_url']}")
        print()


def render_text(ig_pending: list, fb_pending: list, fb_native: list):
    total = len(ig_pending) + len(fb_pending) + len(fb_native)
    print(f"📅 Scheduled posts (Pacific time) — {total} total\n")

    print("─" * 70)
    print(f"📷 INSTAGRAM — pipeline queue ({len(ig_pending)} pending)")
    print("─" * 70)
    _print_pipeline_entries(ig_pending)

    print("─" * 70)
    print(f"📘 FACEBOOK — pipeline queue ({len(fb_pending)} pending)")
    print("─" * 70)
    _print_pipeline_entries(fb_pending)

    print("─" * 70)
    print(f"📘 FACEBOOK — Graph API native scheduled_posts ({len(fb_native)} scheduled)")
    print("    (posts scheduled directly on Facebook, not through our pipeline)")
    print("─" * 70)
    if not fb_native:
        print("  (none)\n")
    else:
        for p in fb_native:
            msg_preview = (p.get("message") or "").split("\n")[0][:60]
            print(f"  • {fmt_fb_time(p.get('scheduled_publish_time'))}")
            print(f"    {msg_preview}")
            print(f"    id: {p['id']}")
            print()

    print("ℹ️  Note: posts scheduled via Meta Business Suite GUI are NOT shown")
    print("    (no public API). Check business.facebook.com directly for those.")


def render_json(ig_pending: list, fb_pending: list, fb_native: list):
    def serialize_pipeline(p):
        return {
            "id": p["id"],
            "platform": p.get("platform"),
            "scheduled_for_local": fmt_local(p["scheduled_for_utc"]),
            "scheduled_for_utc": p["scheduled_for_utc"],
            "caption_first_line": p["caption"].split("\n")[0],
            "image_url": p["image_url"],
        }
    out = {
        "instagram_pipeline_pending": [serialize_pipeline(p) for p in ig_pending],
        "facebook_pipeline_pending": [serialize_pipeline(p) for p in fb_pending],
        "facebook_graph_native_scheduled": [
            {
                "id": p["id"],
                "scheduled_for_local": fmt_fb_time(p.get("scheduled_publish_time")),
                "scheduled_publish_time_epoch": p.get("scheduled_publish_time"),
                "message_first_line": (p.get("message") or "").split("\n")[0],
            }
            for p in fb_native
        ],
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="Show scheduled posts across IG queue + FB queue + FB native Graph API")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    args = parser.parse_args()

    ig_pending = get_pending_by_platform("instagram")
    fb_pending = get_pending_by_platform("facebook")
    fb_native = get_scheduled_fb()

    if args.json:
        render_json(ig_pending, fb_pending, fb_native)
    else:
        render_text(ig_pending, fb_pending, fb_native)


if __name__ == "__main__":
    main()
