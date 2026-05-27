"""
list_posts.py
-------------
Show what's in the post pipeline — pending, posted, failed.

Usage:
    python list_posts.py            # show everything
    python list_posts.py --pending  # only pending
    python list_posts.py --posted   # only posted
    python list_posts.py --failed   # only failed
"""

import argparse
from queue_utils import load_queue, fmt_local


STATUS_ICON = {
    "pending": "⏳",
    "posted": "✅",
    "failed": "❌",
}


def show_post(entry: dict):
    icon = STATUS_ICON.get(entry["status"], "•")
    print(f"\n{icon}  {entry['id']}  [{entry['status'].upper()}]")
    print(f"   When:    {fmt_local(entry['scheduled_for_utc'])}")
    print(f"   Platform: {entry['platform']}")
    print(f"   Image:   {entry['image_url']}")
    caption_preview = entry["caption"].replace("\n", " ")[:100]
    print(f"   Caption: {caption_preview}{'...' if len(entry['caption']) > 100 else ''}")
    if entry.get("posted_at"):
        print(f"   Posted:  {fmt_local(entry['posted_at'])}")
    if entry.get("result"):
        print(f"   Result:  {entry['result']}")


def main():
    parser = argparse.ArgumentParser(description="List scheduled posts")
    parser.add_argument("--pending", action="store_true", help="Show only pending")
    parser.add_argument("--posted", action="store_true", help="Show only posted")
    parser.add_argument("--failed", action="store_true", help="Show only failed")
    args = parser.parse_args()

    statuses = []
    if args.pending:
        statuses.append("pending")
    if args.posted:
        statuses.append("posted")
    if args.failed:
        statuses.append("failed")
    if not statuses:
        statuses = ["pending", "posted", "failed"]

    queue = load_queue()
    posts = queue.get("posts", [])

    if not posts:
        print("Queue is empty. Schedule one with:")
        print('   python schedule_post.py --image "flyer.jpg" --caption "..." --when "2026-06-13 16:00"')
        return

    posts_sorted = sorted(posts, key=lambda p: p["scheduled_for_utc"])
    shown = 0
    for entry in posts_sorted:
        if entry["status"] not in statuses:
            continue
        show_post(entry)
        shown += 1

    print(f"\n--- {shown} post(s) shown ---")


if __name__ == "__main__":
    main()
