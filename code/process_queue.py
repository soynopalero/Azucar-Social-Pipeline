"""
process_queue.py
----------------
Cloud worker — invoked by the GitHub Actions cron every 15 minutes.
Reads posts_queue.json, posts anything that's due (status=pending and
scheduled_for_utc <= now), updates the queue, and exits.

The GitHub Actions workflow handles committing the updated queue back.

Credentials are read from environment variables (set as GitHub repo secrets):
    FB_PAGE_ACCESS_TOKEN, IG_USER_ID
"""

import os
import sys
from datetime import datetime, timezone

import requests

from queue_utils import load_queue, save_queue, from_utc_iso

PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")
IG_USER_ID = os.environ.get("IG_USER_ID")
API_VERSION = "v19.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"


def post_to_instagram(image_url: str, caption: str) -> dict:
    """Post via Meta Graph API. Returns {'ok': True, 'id': ...} or {'ok': False, 'error': ...}."""
    container = requests.post(
        f"{BASE_URL}/{IG_USER_ID}/media",
        data={"image_url": image_url, "caption": caption, "access_token": PAGE_ACCESS_TOKEN},
        timeout=60,
    ).json()
    if "id" not in container:
        return {"ok": False, "error": f"container creation failed: {container}"}
    publish = requests.post(
        f"{BASE_URL}/{IG_USER_ID}/media_publish",
        data={"creation_id": container["id"], "access_token": PAGE_ACCESS_TOKEN},
        timeout=60,
    ).json()
    if "id" in publish:
        return {"ok": True, "id": publish["id"], "container_id": container["id"]}
    return {"ok": False, "error": f"publish failed: {publish}"}


def main():
    if not PAGE_ACCESS_TOKEN or not IG_USER_ID:
        print("❌ Missing FB_PAGE_ACCESS_TOKEN or IG_USER_ID in env")
        sys.exit(1)

    queue = load_queue()
    posts = queue.get("posts", [])
    now_utc = datetime.now(timezone.utc)
    print(f"⏰ Now (UTC): {now_utc.isoformat()}")

    due = [
        p for p in posts
        if p["status"] == "pending" and from_utc_iso(p["scheduled_for_utc"]) <= now_utc
    ]

    if not due:
        print(f"ℹ️  No posts due. Queue has {len(posts)} entry(ies).")
        return

    print(f"📋 {len(due)} post(s) due — processing...\n")
    any_changes = False

    for entry in due:
        print(f"--- Processing {entry['id']} ---")
        print(f"    Scheduled: {entry['scheduled_for_utc']}")
        print(f"    Platform:  {entry['platform']}")

        if entry["platform"] != "instagram":
            print(f"    ⚠️  Unsupported platform '{entry['platform']}' — skipping")
            continue

        result = post_to_instagram(entry["image_url"], entry["caption"])
        entry["posted_at"] = datetime.now(timezone.utc).isoformat()
        if result["ok"]:
            entry["status"] = "posted"
            entry["result"] = f"Instagram media id: {result['id']}"
            print(f"    ✅ Posted! IG media id: {result['id']}")
        else:
            entry["status"] = "failed"
            entry["result"] = result["error"]
            print(f"    ❌ Failed: {result['error']}")
        any_changes = True

    if any_changes:
        save_queue(queue)
        print(f"\n💾 Queue updated.")


if __name__ == "__main__":
    main()
