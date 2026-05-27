"""
schedule_post.py
----------------
Add a scheduled Instagram post to posts_queue.json.

Usage:
    python schedule_post.py --image "flyer.jpg" --caption "..." --when "2026-06-13 16:00"
    python schedule_post.py --image "flyer.jpg" --caption-file "caption.txt" --when "2026-06-13 16:00"

Times are interpreted as Pacific time. Image is uploaded to catbox.moe and
only the URL is stored in the queue. After updating the queue, the script
commits the change and pushes to GitHub so the cloud workflow can post it.
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
    parser = argparse.ArgumentParser(description="Schedule an Instagram post")
    parser.add_argument("--image", type=str, required=True, help="Path to image file")
    parser.add_argument("--caption", type=str, help="Caption text")
    parser.add_argument("--caption-file", type=str, help="Path to a UTF-8 text file containing the caption")
    parser.add_argument("--when", type=str, required=True, help="Scheduled time (Pacific). Format: YYYY-MM-DD HH:MM")
    parser.add_argument("--platform", type=str, default="instagram", choices=["instagram"], help="Target platform")
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

    post_id = new_post_id(scheduled_utc)
    now_utc_iso = datetime.now(timezone.utc).isoformat()

    entry = {
        "id": post_id,
        "platform": args.platform,
        "scheduled_for_utc": to_utc_iso(scheduled_local),
        "image_url": image_url,
        "caption": caption,
        "status": "pending",
        "created_at": now_utc_iso,
        "posted_at": None,
        "result": None,
    }

    queue = load_queue()
    queue["posts"].append(entry)
    save_queue(queue)

    print(f"\n✅ Scheduled post {post_id}")
    print(f"   Platform:   {args.platform}")
    print(f"   When:       {fmt_local(entry['scheduled_for_utc'])}")
    print(f"   Image:      {image_url}")
    print(f"   Caption:    {caption[:80]}{'...' if len(caption) > 80 else ''}")

    if not args.no_push:
        git_commit_and_push(f"Schedule post {post_id} for {fmt_local(entry['scheduled_for_utc'])}")


if __name__ == "__main__":
    main()
