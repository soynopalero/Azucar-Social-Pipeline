"""
schedule_post.py
----------------
Add scheduled post(s) to posts_queue.json for one or more platforms.

Usage:
    # Single platform (instagram by default)
    python schedule_post.py --image flyer.jpg --caption-file caption.txt --when "2026-06-13 16:00"

    # Multi-platform: creates one queue entry per platform, same scheduled time
    python schedule_post.py --image flyer.jpg --caption-file caption.txt \
        --when "2026-06-13 16:00" --platforms instagram facebook

Times are interpreted as Pacific time. Image is uploaded to catbox.moe once
and the URL is reused across all platform entries. After updating the queue,
the script commits and pushes to GitHub so the cloud workflow can post it.
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from queue_utils import (
    load_queue, save_queue, new_post_id,
    parse_local_time, to_utc_iso, fmt_local,
    upload_image_to_catbox, git_commit_and_push,
)


def main():
    parser = argparse.ArgumentParser(description="Schedule a post for one or more platforms")
    parser.add_argument("--image", type=str, required=True, help="Path to image file")
    parser.add_argument("--caption", type=str, help="Caption text")
    parser.add_argument("--caption-file", type=str, help="Path to a UTF-8 text file containing the caption")
    parser.add_argument("--when", type=str, required=True, help="Scheduled time (Pacific). Format: YYYY-MM-DD HH:MM")
    parser.add_argument(
        "--platforms",
        nargs="+",
        default=["instagram"],
        choices=["instagram", "facebook"],
        help="Target platforms (one or more, space-separated). Default: instagram",
    )
    parser.add_argument("--no-push", action="store_true", help="Skip git commit/push (queue saved locally only)")
    args = parser.parse_args()

    if not args.caption and not args.caption_file:
        print("❌ Must provide --caption or --caption-file")
        sys.exit(1)
    if args.caption and args.caption_file:
        print("❌ Use either --caption or --caption-file, not both")
        sys.exit(1)

    if args.caption_file:
        caption = Path(args.caption_file).read_text(encoding="utf-8").strip()
    else:
        caption = args.caption

    scheduled_local = parse_local_time(args.when)
    scheduled_utc = scheduled_local.astimezone(timezone.utc)

    if scheduled_utc < datetime.now(timezone.utc):
        print(f"❌ Scheduled time is in the past: {scheduled_local}")
        sys.exit(1)

    image_url = upload_image_to_catbox(args.image)

    now_utc_iso = datetime.now(timezone.utc).isoformat()
    scheduled_iso = to_utc_iso(scheduled_local)

    queue = load_queue()
    created_ids = []
    for platform in args.platforms:
        post_id = new_post_id(scheduled_utc)
        entry = {
            "id": post_id,
            "platform": platform,
            "scheduled_for_utc": scheduled_iso,
            "image_url": image_url,
            "caption": caption,
            "status": "pending",
            "created_at": now_utc_iso,
            "posted_at": None,
            "result": None,
        }
        queue["posts"].append(entry)
        created_ids.append((post_id, platform))

    save_queue(queue)

    print(f"\n✅ Scheduled {len(created_ids)} post(s)")
    for pid, platform in created_ids:
        print(f"   [{platform}] {pid}")
    print(f"   When:    {fmt_local(scheduled_iso)}")
    print(f"   Image:   {image_url}")
    print(f"   Caption: {caption[:80]}{'...' if len(caption) > 80 else ''}")

    if not args.no_push:
        platforms_str = "+".join(args.platforms)
        commit_msg = f"Schedule {platforms_str} post(s) for {fmt_local(scheduled_iso)}"
        git_commit_and_push(commit_msg)


if __name__ == "__main__":
    main()
