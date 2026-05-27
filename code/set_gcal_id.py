"""
set_gcal_id.py
--------------
Attach (or remove) a Google Calendar event ID on a queued post entry. Called
by the azucar-post skill after creating/deleting a calendar event via the
MCP Google Calendar tools, since those tools live in Claude's session and
can't be invoked from inside Python.

Usage:
    python set_gcal_id.py --id <post-id> --event-id <gcal-event-id>
    python set_gcal_id.py --id <post-id> --clear              # remove the link
"""

import argparse
import sys
from queue_utils import load_queue, save_queue


def main():
    parser = argparse.ArgumentParser(description="Attach a GCal event id to a queued post")
    parser.add_argument("--id", type=str, required=True, help="Post ID")
    parser.add_argument("--event-id", type=str, help="Google Calendar event ID to attach")
    parser.add_argument("--clear", action="store_true", help="Remove the GCal event id from the entry")
    args = parser.parse_args()

    if not args.event_id and not args.clear:
        print("❌ Provide --event-id, or --clear")
        sys.exit(1)

    queue = load_queue()
    matching = [p for p in queue.get("posts", []) if p["id"] == args.id]
    if not matching:
        print(f"❌ No post with id {args.id}")
        sys.exit(1)

    entry = matching[0]
    if args.clear:
        entry.pop("gcal_event_id", None)
        print(f"✅ Cleared GCal event id from {args.id}")
    else:
        entry["gcal_event_id"] = args.event_id
        print(f"✅ Attached GCal event {args.event_id} to {args.id}")

    save_queue(queue)


if __name__ == "__main__":
    main()
