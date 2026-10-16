#!/usr/bin/env python3
"""
dedupe_queue.py
---------------
Remove duplicate PENDING entries from posts_queue.json.

Two entries are duplicates when they share the natural key

    (monday_event_id or campaign, scheduled_for_utc, platform, format)

i.e. the same event, going out at the same minute, on the same platform, in
the same format (feed or story). Random entry ids do not count: the duplicates
this removes were created by back-to-back cadence-engine runs that each
generated the same slots with fresh ids (see audit-social-posting-2026-10-15.md).

The oldest entry (by created_at, then file order) is kept; later copies go,
as does a pending copy of an entry that was already posted. Failed and
cancelled entries are history and are never touched.

The rule itself lives in code/merge_queue.py (dedupe_pending), which the git
merge driver and the cadence engine's save step also apply — this script is
the one-off cleanup for a queue that predates that rule.

Usage:
    python code/dedupe_queue.py --dry-run    # list what would be removed
    python code/dedupe_queue.py              # remove, save (+ docs/ mirror)
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import queue_utils as qu  # noqa: E402
from merge_queue import dedupe_pending  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="print what would be removed, write nothing")
    args = ap.parse_args()

    queue = qu.load_queue()
    posts = queue.get("posts", [])
    pending_before = sum(1 for p in posts if p.get("status") == "pending")
    kept, removed = dedupe_pending(posts)

    if not removed:
        print(f"No duplicate pending entries ({pending_before} pending).")
        return 0

    by_campaign: dict[str, list[dict]] = defaultdict(list)
    for p in removed:
        by_campaign[p.get("campaign") or "?"].append(p)
    print(f"Duplicate pending entries to remove: {len(removed)}\n")
    for camp in sorted(by_campaign):
        rows = sorted(by_campaign[camp], key=lambda p: (p.get("scheduled_for_utc") or "", p.get("platform") or ""))
        print(f"  {camp}  ({len(rows)})")
        for p in rows:
            print(f"      - {qu.fmt_local(p['scheduled_for_utc'])}  {p.get('platform'):<9} "
                  f"{p.get('format') or 'feed':<5} id={p.get('id')}  created {str(p.get('created_at'))[:19]}")
    print(f"\nPending entries: {pending_before} -> {pending_before - len(removed)}")

    if args.dry_run:
        print("\n(dry run — nothing written)")
        return 0

    queue["posts"] = kept
    qu.save_queue(queue)
    print(f"\nWrote {qu.QUEUE_PATH.name} (+ docs/ mirror).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
