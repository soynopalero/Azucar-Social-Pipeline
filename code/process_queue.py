"""
process_queue.py
----------------
Cloud worker — invoked by the GitHub Actions cron every 15 minutes.
Reads posts_queue.json, posts anything that's due (status=pending and
scheduled_for_utc <= now), updates the queue, and exits.

The GitHub Actions workflow handles committing the updated queue back.

Credentials are read from environment variables (set as GitHub repo secrets):
    FB_PAGE_ACCESS_TOKEN, IG_USER_ID, FB_PAGE_ID
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

from queue_utils import load_queue, save_queue, from_utc_iso

# Load .env when running locally (no-op in GitHub Actions where env is set natively)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")
IG_USER_ID = os.environ.get("IG_USER_ID")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
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


def post_to_facebook(image_url: str, caption: str) -> dict:
    """Post a photo to the FB Page via Graph API using a remote image URL.

    Returns {'ok': True, 'id': ...} or {'ok': False, 'error': ...}.
    """
    response = requests.post(
        f"{BASE_URL}/{FB_PAGE_ID}/photos",
        data={
            "url": image_url,
            "message": caption,
            "access_token": PAGE_ACCESS_TOKEN,
        },
        timeout=120,
    ).json()
    if "id" in response:
        return {"ok": True, "id": response["id"], "post_id": response.get("post_id")}
    return {"ok": False, "error": f"FB post failed: {response}"}


def main():
    missing = [k for k, v in {
        "FB_PAGE_ACCESS_TOKEN": PAGE_ACCESS_TOKEN,
        "IG_USER_ID": IG_USER_ID,
        "FB_PAGE_ID": FB_PAGE_ID,
    }.items() if not v]
    if missing:
        # IG_USER_ID and FB_PAGE_ID are only required for their respective platforms,
        # but we error early if FB_PAGE_ACCESS_TOKEN is missing (used by both).
        if "FB_PAGE_ACCESS_TOKEN" in missing:
            print(f"❌ Missing required env var(s): {', '.join(missing)}")
            sys.exit(1)
        print(f"⚠️  Missing env var(s): {', '.join(missing)} — will skip posts that need them.")

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

        platform = entry["platform"]
        if platform == "instagram":
            if not IG_USER_ID:
                print(f"    ⚠️  IG_USER_ID not set — skipping")
                continue
            result = post_to_instagram(entry["image_url"], entry["caption"])
            result_label = "Instagram media id"
        elif platform == "facebook":
            if not FB_PAGE_ID:
                print(f"    ⚠️  FB_PAGE_ID not set — skipping")
                continue
            result = post_to_facebook(entry["image_url"], entry["caption"])
            result_label = "Facebook post id"
        else:
            print(f"    ⚠️  Unsupported platform '{platform}' — skipping")
            continue

        entry["posted_at"] = datetime.now(timezone.utc).isoformat()
        if result["ok"]:
            entry["status"] = "posted"
            entry["result"] = f"{result_label}: {result['id']}"
            print(f"    ✅ Posted! {result_label}: {result['id']}")
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
