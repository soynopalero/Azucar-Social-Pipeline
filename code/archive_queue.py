"""
archive_queue.py
----------------
Move posted entries for finished events out of posts_queue.json into
archive/posts_archive.json.

Why: the queue is append-only in practice — every post the cadence engine
schedules stays in it forever. It reached 1472 entries / 1.95 MB, which pushed
every Post Manager board load and every save through GitHub's over-1 MB
contents-API path. That path is handled correctly now (PR #30), but it is
slower and more fragile than the normal one, and the file only grows. Keeping
the live queue small keeps that path cold.

What moves: entries with status "posted" whose event finished more than
GRACE_DAYS ago. Nothing else. Pending and failed entries always stay — they are
the operational queue — and an entry whose date cannot be read stays too,
because archiving on a guess is worse than a slightly larger file.

Nothing is deleted. Archived entries keep their exact shape in
archive/posts_archive.json, which uses the same {"posts": [...]} schema as the
queue, so any tool that reads one can read the other.

Re-running is safe: entries already in the archive are matched by id and not
duplicated.

Run:  python code/archive_queue.py --dry-run     # report, write nothing
      python code/archive_queue.py               # do it
      python code/archive_queue.py --selftest    # offline rule check
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import queue_utils as qu  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_PATH = REPO_ROOT / "archive" / "posts_archive.json"

# How long after an event finishes its posted entries stay in the live queue.
# A week keeps the just-finished events on the manager's board while it still
# matters, and holds the live file well under 1 MB.
GRACE_DAYS = 7


def event_day(post: dict) -> dt.date | None:
    """The day this post's event happened, or None if it cannot be read.

    Prefers event_date (the real date off the Monday board) and falls back to
    the day the post was scheduled — an event's last post goes out on or before
    the event itself, so this never archives something early.
    """
    raw = post.get("event_date") or (post.get("scheduled_for_utc") or "")[:10]
    try:
        return dt.date.fromisoformat(raw)
    except (TypeError, ValueError):
        return None


def should_archive(post: dict, cutoff: dt.date) -> bool:
    """Only posted entries, only for events that finished before the cutoff."""
    if post.get("status") != "posted":
        return False
    day = event_day(post)
    return day is not None and day < cutoff


def load_archive() -> dict:
    if not ARCHIVE_PATH.exists():
        return {"posts": []}
    with open(ARCHIVE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_archive(archive: dict) -> None:
    ARCHIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ARCHIVE_PATH, "w", encoding="utf-8") as f:
        json.dump(archive, f, indent=2, ensure_ascii=False)


def split(posts: list, cutoff: dt.date) -> tuple[list, list]:
    keep, move = [], []
    for p in posts:
        (move if should_archive(p, cutoff) else keep).append(p)
    return keep, move


def mb(obj) -> float:
    return len(json.dumps(obj, indent=2, ensure_ascii=False).encode()) / 1024 / 1024


def run(grace_days: int, dry_run: bool) -> int:
    queue = qu.load_queue()
    posts = queue.get("posts")
    if not isinstance(posts, list):
        sys.exit('posts_queue.json is not {"posts": [...]} — refusing to touch it.')

    cutoff = dt.date.today() - dt.timedelta(days=grace_days)
    keep, move = split(posts, cutoff)

    print(f"Queue: {len(posts)} entries, {mb(queue):.2f} MB")
    print(f"Events finished before {cutoff.isoformat()} (grace {grace_days}d) → archive")

    if not move:
        print("Nothing to archive — queue already trimmed.")
        return 0

    archive = load_archive()
    existing = {p.get("id") for p in archive.get("posts", [])}
    fresh = [p for p in move if p.get("id") not in existing]
    dupes = len(move) - len(fresh)

    archive["posts"] = archive.get("posts", []) + fresh
    archive["posts"].sort(key=lambda p: (p.get("scheduled_for_utc") or "", p.get("id") or ""))

    trimmed = dict(queue, posts=keep)
    print(f"  moving  {len(move):5} posted entries"
          + (f" ({dupes} already archived, not duplicated)" if dupes else ""))
    print(f"  keeping {len(keep):5} (pending, failed, and recent events)")
    print(f"  live queue {mb(queue):.2f} MB → {mb(trimmed):.2f} MB")
    print(f"  archive    {len(archive['posts'])} entries, {mb(archive):.2f} MB")

    if dry_run:
        print("\n--dry-run: nothing written.")
        return 0

    # Archive first. If this write succeeds and the next one fails, the entries
    # exist in both files — recoverable. The other order could lose them.
    save_archive(archive)
    qu.save_queue(trimmed)
    print(f"\nWrote {ARCHIVE_PATH.relative_to(REPO_ROOT)} and posts_queue.json (+ docs mirror).")
    return 0


# ---------- self-test ----------

def selftest() -> int:
    cutoff = dt.date(2026, 9, 1)
    old, new = "2026-08-01", "2026-09-15"
    cases = [
        ({"status": "posted", "event_date": old}, True, "posted, event long over"),
        ({"status": "posted", "event_date": new}, False, "posted, event still ahead"),
        ({"status": "posted", "event_date": "2026-09-01"}, False, "posted, event on the cutoff"),
        ({"status": "pending", "event_date": old}, False, "pending is never archived"),
        ({"status": "failed", "event_date": old}, False, "failed is never archived"),
        ({"status": "posted", "scheduled_for_utc": old + "T19:00:00+00:00"}, True,
         "posted, no event_date → falls back to scheduled day"),
        ({"status": "posted"}, False, "posted, no date at all → kept"),
        ({"status": "posted", "event_date": "not-a-date"}, False, "posted, unreadable date → kept"),
        ({"status": "posted", "event_date": None,
          "scheduled_for_utc": None}, False, "posted, null dates → kept"),
        # event_date wins: a post scheduled long before an upcoming event stays.
        ({"status": "posted", "event_date": new,
          "scheduled_for_utc": old + "T19:00:00+00:00"}, False,
         "event_date beats scheduled date"),
    ]

    failures = 0
    for post, expected, label in cases:
        got = should_archive(post, cutoff)
        if got != expected:
            failures += 1
        print(f"  {'ok  ' if got == expected else 'FAIL'} {label}: archive={got} (expected {expected})")

    # Splitting must never lose or duplicate an entry.
    sample = [c[0] | {"id": f"p{i}"} for i, c in enumerate(cases)]
    keep, move = split(sample, cutoff)
    if len(keep) + len(move) != len(sample):
        print(f"  FAIL split lost entries: {len(keep)}+{len(move)} != {len(sample)}")
        failures += 1
    else:
        print(f"  ok   split conserves entries: {len(keep)} kept + {len(move)} moved = {len(sample)}")

    # Re-running must be a no-op on what it already moved.
    keep2, move2 = split(keep, cutoff)
    if move2:
        print(f"  FAIL second pass wanted to move {len(move2)} more")
        failures += 1
    else:
        print("  ok   second pass moves nothing (idempotent)")

    if failures:
        print(f"{failures} case(s) failed.")
        return 1
    print(f"All {len(cases) + 2} checks passed.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[3])
    ap.add_argument("--dry-run", action="store_true", help="report what would move, write nothing")
    ap.add_argument("--grace-days", type=int, default=GRACE_DAYS,
                    help=f"keep posted entries this long after the event (default {GRACE_DAYS})")
    ap.add_argument("--selftest", action="store_true", help="offline rule check, no files touched")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    return run(args.grace_days, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
