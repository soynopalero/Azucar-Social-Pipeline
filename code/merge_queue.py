"""
merge_queue.py — git merge driver for posts_queue.json (and its mirrors).

Why this exists
---------------
Several workflows commit the queue to main: the post scheduler marks entries
posted every few minutes, the cadence engine adds and replaces pending entries,
the archive step moves finished entries out. Until now they avoided clobbering
each other only by sharing ONE GitHub concurrency group and rebasing with
`-X theirs` ("whoever commits last wins the whole file"). That had two costs:

  * a queued run in a shared group is CANCELLED when another run is queued
    behind it (GitHub keeps one running + one pending per group), so the daily
    cadence pass was silently dropped four times in Aug–Sep 2026;
  * `-X theirs` on a JSON file is a whole-file overwrite — if the two sides ever
    did overlap, posted markers would be lost and posts would go out twice.

This driver merges the queue BY ENTRY ID instead, so the workflows can run in
separate groups and both sides' changes survive:

  * an entry changed on only one side takes that side's version;
  * an entry changed on both sides keeps the terminal state (posted/failed)
    over pending — a posted marker is never lost;
  * an entry deleted on one side stays deleted (the cadence engine replaces
    pending entries on re-approval) unless the other side had already posted
    it, in which case the posted record is kept as history;
  * entries new on either side are kept — UNLESS they are the same post under
    two ids. Two cadence-engine runs dispatched seconds apart start from the
    same commit, each queues the same story slots with fresh random ids, and
    an id-merge would keep both (Oct 2026: 10 stories in 90 seconds). So after
    merging by id, pending entries that share a NATURAL KEY — same event
    (monday_event_id, or campaign), same scheduled minute, same platform, same
    format — are collapsed to the earliest-created one. A pending copy of an
    entry that was already posted is dropped too.

git wiring (done by the workflows before `git pull --rebase`):
    git config merge.queue.driver "python code/merge_queue.py %O %A %B"
plus `.gitattributes` mapping the queue files to `merge=queue`. git calls this
with (ancestor, current, other) paths and expects the result written to the
`current` path; exit 0 = merged cleanly.

Self-test (offline): python code/merge_queue.py --selftest
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TERMINAL = {"posted", "failed", "cancelled"}


def _load(path: str) -> dict:
    text = Path(path).read_text(encoding="utf-8") if Path(path).exists() else ""
    if not text.strip():
        return {"posts": []}
    return json.loads(text)


def _index(queue: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in queue.get("posts", []):
        pid = p.get("id")
        if pid is not None:
            out[str(pid)] = p
    return out


def _rank(p: dict | None) -> int:
    """Higher = more final. A posted/failed entry beats a pending one."""
    if not p:
        return -1
    return 1 if p.get("status") in TERMINAL else 0


def natural_key(p: dict) -> tuple:
    """What makes two queue entries the same post, ids aside: one event, one
    minute, one platform, one format (feed entries carry no "format")."""
    return (
        p.get("monday_event_id") or p.get("campaign"),
        p.get("scheduled_for_utc"),
        p.get("platform"),
        p.get("format"),
    )


def dedupe_pending(posts: list[dict]) -> tuple[list[dict], list[dict]]:
    """Collapse pending entries that share a natural key. Returns (kept, removed).

    The earliest created_at wins (file order breaks ties). If the key is
    already covered by a POSTED entry, every pending copy goes — it would be
    the same post going out twice. Failed and cancelled entries are ignored:
    a pending re-queue of a failed post is a retry, not a duplicate. Shared by
    the merge driver, the cadence engine's save step and code/dedupe_queue.py,
    so "duplicate" means one thing everywhere.
    """
    def known(key: tuple) -> bool:
        # An entry with no event and no time cannot be proven a duplicate of
        # anything; silently dropping it would be the wrong kind of mistake.
        return bool(key[0] and key[1])

    posted_keys = {natural_key(p) for p in posts if p.get("status") == "posted"}
    groups: dict[tuple, list[int]] = {}
    for i, p in enumerate(posts):
        if p.get("status") == "pending" and known(natural_key(p)):
            groups.setdefault(natural_key(p), []).append(i)
    drop: set[int] = set()
    for key, idxs in groups.items():
        if key in posted_keys:
            drop.update(idxs)
            continue
        if len(idxs) < 2:
            continue
        winner = min(idxs, key=lambda i: (str(posts[i].get("created_at") or ""), i))
        drop.update(i for i in idxs if i != winner)
    kept = [p for i, p in enumerate(posts) if i not in drop]
    removed = [p for i, p in enumerate(posts) if i in drop]
    return kept, removed


def merge_posts(base: list[dict], a: list[dict], b: list[dict]) -> list[dict]:
    bi, ai, bbi = (_index({"posts": x}) for x in (base, a, b))
    merged: dict[str, dict] = {}

    def pick(pid: str) -> dict | None:
        o, x, y = bi.get(pid), ai.get(pid), bbi.get(pid)
        if x is not None and y is not None:
            if x == y:
                return x
            if _rank(x) != _rank(y):
                return x if _rank(x) > _rank(y) else y  # terminal state wins
            if x == o:
                return y  # only y changed it
            if y == o:
                return x  # only x changed it
            # Both changed a pending entry differently (rare). Keep the later
            # write when timestamps say so, otherwise the "other" side (B is
            # the commit being replayed onto upstream during a rebase — the
            # run that just finished).
            return max((x, y), key=lambda p: str(p.get("updated_at") or p.get("posted_at") or ""))
        present = x if x is not None else y
        if o is None:
            return present  # new on one side
        # Present on one side, deleted on the other.
        if _rank(present) > _rank(o):
            return present  # it was posted meanwhile — keep the record
        return None  # deletion wins

    # Keep A's order, then B's additions, so the file stays stable for diffs.
    for pid in list(ai) + [k for k in bbi if k not in ai]:
        if pid in merged:
            continue
        chosen = pick(pid)
        if chosen is not None:
            merged[pid] = chosen
    kept, _ = dedupe_pending(list(merged.values()))
    return kept


def merge_queue(base: dict, a: dict, b: dict) -> dict:
    out = dict(base)
    out.update(a)
    out.update(b)
    out["posts"] = merge_posts(base.get("posts", []), a.get("posts", []), b.get("posts", []))
    return out


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    if len(argv) != 4:
        sys.exit("usage: merge_queue.py <ancestor> <current> <other>   (git merge driver)")
    _, base_p, cur_p, other_p = argv
    try:
        merged = merge_queue(_load(base_p), _load(cur_p), _load(other_p))
    except (json.JSONDecodeError, TypeError, AttributeError) as e:
        print(f"merge_queue: could not merge ({e}); leaving the conflict for git", file=sys.stderr)
        return 1
    Path(cur_p).write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"merge_queue: merged {len(merged['posts'])} entries by id (natural-key duplicates dropped)")
    return 0


# ---------- self-test ----------

def _p(pid, status="pending", **kw):
    d = {"id": pid, "status": status, "caption": "c", "platform": "instagram"}
    d.update(kw)
    return d


def selftest() -> int:
    cases = []

    def case(name, base, a, b, expect):
        got = merge_posts(base, a, b)
        got_map = {p["id"]: p for p in got}
        ok = got_map == {p["id"]: p for p in expect}
        cases.append(ok)
        print(f"  {'ok  ' if ok else 'FAIL'} {name}")
        if not ok:
            print(f"       got:    {json.dumps(got, sort_keys=True)}")
            print(f"       expect: {json.dumps(expect, sort_keys=True)}")

    # The race this driver exists for: scheduler posts #1 while the engine
    # adds #3. Both survive; nothing is re-posted.
    case("scheduler posted, engine appended",
         base=[_p(1), _p(2)],
         a=[_p(1, "posted", posted_at="t"), _p(2)],
         b=[_p(1), _p(2), _p(3)],
         expect=[_p(1, "posted", posted_at="t"), _p(2), _p(3)])
    case("same race, sides swapped",
         base=[_p(1), _p(2)],
         a=[_p(1), _p(2), _p(3)],
         b=[_p(1, "posted", posted_at="t"), _p(2)],
         expect=[_p(1, "posted", posted_at="t"), _p(2), _p(3)])
    # Engine replaces an event's pending entries (delete 2, add 4) while the
    # scheduler leaves them alone: the deletion sticks.
    case("engine re-queue deletes pending entry",
         base=[_p(1), _p(2)],
         a=[_p(1), _p(2)],
         b=[_p(1), _p(4)],
         expect=[_p(1), _p(4)])
    # ...but if the scheduler had posted #2 in the meantime, the posted record
    # is kept — history is never dropped.
    case("deleted on one side, posted on the other",
         base=[_p(1), _p(2)],
         a=[_p(1), _p(2, "posted")],
         b=[_p(1), _p(4)],
         expect=[_p(1), _p(2, "posted"), _p(4)])
    case("archive removes posted entry, other side untouched",
         base=[_p(1, "posted"), _p(2)],
         a=[_p(2)],
         b=[_p(1, "posted"), _p(2)],
         expect=[_p(2)])
    case("failed beats pending when both changed",
         base=[_p(1)],
         a=[_p(1, "failed", result="x")],
         b=[_p(1, transient_attempts=2)],
         expect=[_p(1, "failed", result="x")])
    case("identical changes on both sides",
         base=[_p(1)],
         a=[_p(1, "posted")],
         b=[_p(1, "posted")],
         expect=[_p(1, "posted")])
    case("only one side edited a pending caption",
         base=[_p(1, caption="old")],
         a=[_p(1, caption="old")],
         b=[_p(1, caption="new")],
         expect=[_p(1, caption="new")])
    case("empty base (first commit of the file)",
         base=[],
         a=[_p(1)],
         b=[_p(2)],
         expect=[_p(1), _p(2)])

    # --- natural-key duplicates (the back-to-back dispatch race) ---
    def _s(pid, created, event="E1", when="2026-10-17T18:00:00+00:00",
           platform="instagram", status="pending", **kw):
        return _p(pid, status, format="story", monday_event_id=event,
                  scheduled_for_utc=when, platform=platform, created_at=created, **kw)

    # Two runs from the same commit each add "the" Oct 17 story under a fresh
    # id: only the earlier-created one survives the merge.
    case("same story queued twice with different ids: earliest wins",
         base=[_s(1, "t0", event="OTHER")],
         a=[_s(1, "t0", event="OTHER"), _s("a1", "2026-10-13T06:24:38")],
         b=[_s(1, "t0", event="OTHER"), _s("b1", "2026-10-13T06:24:04")],
         expect=[_s(1, "t0", event="OTHER"), _s("b1", "2026-10-13T06:24:04")])
    # Same minute, different platform / different event / different format:
    # not duplicates.
    case("ig + fb pair of one story is not a duplicate",
         base=[],
         a=[_s("i", "t1", platform="instagram")],
         b=[_s("f", "t1", platform="facebook")],
         expect=[_s("i", "t1", platform="instagram"), _s("f", "t1", platform="facebook")])
    case("two events at the same minute are not duplicates",
         base=[],
         a=[_s("x", "t1", event="E1")],
         b=[_s("y", "t1", event="E2")],
         expect=[_s("x", "t1", event="E1"), _s("y", "t1", event="E2")])
    feed = _p("fd", monday_event_id="E1", scheduled_for_utc="2026-10-17T18:00:00+00:00",
              created_at="t1")
    case("feed post and story at the same minute are not duplicates",
         base=[],
         a=[_s("st", "t1")],
         b=[feed],
         expect=[_s("st", "t1"), feed])
    # Entries from before monday_event_id existed fall back to the campaign.
    old1 = _p("o1", campaign="cadence_x", scheduled_for_utc="w", created_at="t1")
    old2 = _p("o2", campaign="cadence_x", scheduled_for_utc="w", created_at="t2")
    case("no monday_event_id: campaign stands in",
         base=[], a=[old1], b=[old2], expect=[old1])
    # A pending copy of something already posted would go out twice.
    case("pending copy of a posted entry is dropped",
         base=[],
         a=[_s("p", "t0", status="posted")],
         b=[_s("q", "t1")],
         expect=[_s("p", "t0", status="posted")])
    # ...but a pending retry of a FAILED post is a retry, not a duplicate.
    case("pending retry of a failed entry is kept",
         base=[],
         a=[_s("p", "t0", status="failed")],
         b=[_s("q", "t1")],
         expect=[_s("p", "t0", status="failed"), _s("q", "t1")])
    # dedupe_pending reports what it removed, so callers can log it.
    kept, removed = dedupe_pending([_s("a", "t2"), _s("b", "t1"), _s("c", "t3")])
    ok = [p["id"] for p in kept] == ["b"] and {p["id"] for p in removed} == {"a", "c"}
    cases.append(ok)
    print(f"  {'ok  ' if ok else 'FAIL'} dedupe_pending keeps earliest, reports the rest")

    # Whole-file wiring: top-level keys survive and the driver writes JSON.
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        paths = []
        for name, q in (("O", {"posts": [_p(1)]}),
                        ("A", {"posts": [_p(1, "posted")], "note": "a"}),
                        ("B", {"posts": [_p(1), _p(2)], "note": "b"})):
            p = Path(d) / name
            p.write_text(json.dumps(q), encoding="utf-8")
            paths.append(str(p))
        rc = main(["merge_queue.py", *paths])
        result = json.loads(Path(paths[1]).read_text(encoding="utf-8"))
        ok = rc == 0 and result["note"] == "b" and [p["id"] for p in result["posts"]] == [1, 2] \
            and result["posts"][0]["status"] == "posted"
        cases.append(ok)
        print(f"  {'ok  ' if ok else 'FAIL'} driver entry point writes merged file")

    failed = cases.count(False)
    if failed:
        print(f"{failed} case(s) failed.")
        return 1
    print(f"All {len(cases)} merge cases passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
