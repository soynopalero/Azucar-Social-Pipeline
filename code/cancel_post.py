"""
cancel_post.py
--------------
Remove a pending post from the queue.

Usage:
    python cancel_post.py --id 20260613_230000_abc123
"""

import argparse
import sys
from queue_utils import load_queue, save_queue, fmt_local, git_commit_and_push


def main():
    parser = argparse.ArgumentParser(description="Cancel a scheduled post")
    parser.add_argument("--id", type=str, required=True, help="Post ID (from list_posts.py)")
    parser.add_argument("--no-push", action="store_true", help="Skip git commit/push")
    args = parser.parse_args()

    queue = load_queue()
    posts = queue.get("posts", [])

    matching = [p for p in posts if p["id"] == args.id]
    if not matching:
        print(f"❌ No post found with id {args.id}")
        sys.exit(1)

    entry = matching[0]
    if entry["status"] != "pending":
        print(f"❌ Post {args.id} is '{entry['status']}', not pending. Cannot cancel.")
        sys.exit(1)

    queue["posts"] = [p for p in posts if p["id"] != args.id]
    save_queue(queue)

    print(f"✅ Cancelled post {args.id}")
    print(f"   Was scheduled for: {fmt_local(entry['scheduled_for_utc'])}")
    print(f"   Caption preview:   {entry['caption'][:80]}")

    if not args.no_push:
        git_commit_and_push(f"Cancel post {args.id}")


if __name__ == "__main__":
    main()
