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
  * entries new on either side are kept.

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
    return list(merged.values())


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
    print(f"merge_queue: merged {len(merged['posts'])} entries by id")
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
