#!/usr/bin/env python3
"""
week_card_review.py
-------------------
The Friday approval gate for the Monday round-up.

Why Friday
----------
The round-up used to queue itself on Monday morning with nobody looking. That
is fine until the board is wrong — a night entered at the wrong time, an event
nobody added — and by then the post is already out. Building it on Friday
leaves the weekend to fix the board, and nothing posts until Pedro says so.

The loop
--------
    Friday 09:00 PT   review  -> Telegram: the week's rows + two buttons
    tap ✅            approve -> queue the round-up for Monday 11:00 PT
    tap ✏️            regen   -> bot asks what to change, re-runs review

The buttons are handled by the Telegram bot in the azucar-events-pipeline
repo, which writes nothing here — it fires this workflow again with
`action=approve` or `action=regen`. That is the same baton the caption
approval already passes, so there is one mechanism to understand, not two.

Nothing posts on its own. A week that is never approved is simply never
queued, which is the correct failure: silence beats a wrong post.

Usage:
    python code/week_card_review.py --action review           # Friday's job
    python code/week_card_review.py --action review --feedback "karaoke is 8pm now"
    python code/week_card_review.py --action approve --week-of 2026-09-28
    python code/week_card_review.py --action review --dry-run # print, send nothing
    python code/week_card_review.py --selftest                # offline
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_week_card import SLOTS, build_card, week_window  # noqa: E402

TG_API = "https://api.telegram.org/bot{}/{}"
POST_DAY, POST_HOUR = "Monday", "11:00 AM"


def envvar(name: str) -> str:
    import os
    return (os.environ.get(name) or "").strip()


def tg_call(method: str, payload: dict) -> dict:
    """Same shape as cadence_engine.tg_call — one Telegram transport per repo."""
    token = envvar("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set")
    req = urllib.request.Request(
        TG_API.format(token, method),
        data=json.dumps(payload).encode(),
        headers={"content-type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def review_text(card: dict, feedback: str | None = None) -> str:
    """The message body. Plain text on purpose: event names carry apostrophes
    and asterisks that Telegram's markdown parser rejects, and a post that
    fails to send is worse than one without bold."""
    f = card["fields"]
    used = card["rows_used"]
    lines = [f"🗞️ This Week at Azúcar — {f['week_label']}", ""]

    if not used:
        lines += ["Nothing on the board for this week.",
                  "",
                  "Approving posts nothing. Add the events and tap ✏️ to rebuild."]
        return "\n".join(lines)

    for i in range(1, SLOTS + 1):
        if not f[f"title_{i}"]:
            continue
        lines.append(f"{f['day_' + str(i)]} · {f['title_' + str(i)]}")
        if f[f"detail_{i}"]:
            lines.append(f"      {f['detail_' + str(i)]}")

    if card["overflow"]:
        lines += ["", "Too many for the card — these go in the caption only:",
                  "  " + ", ".join(card["overflow"])]

    if card["long_titles"]:
        lines += ["", "⚠️ Too long for the big line — set a Card Title on the board:",
                  "  " + ", ".join(card["long_titles"])]

    if feedback:
        lines += ["", f"Rebuilt after: “{feedback}”"]

    lines += ["", f"✅ queues it for {POST_DAY} {POST_HOUR}. ✏️ to change something.",
              "Nothing posts unless you tap ✅."]
    return "\n".join(lines)


def send_review(card: dict, feedback: str | None, chat: str) -> None:
    week = card["week_of"]
    tg_call("sendMessage", {
        "chat_id": chat,
        "text": review_text(card, feedback),
        "disable_web_page_preview": True,
        "reply_markup": {"inline_keyboard": [[
            {"text": "✅ Post it", "callback_data": f"week:approve:{week}"},
            {"text": "✏️ Change something", "callback_data": f"week:regen:{week}"},
        ]]},
    })


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--action", choices=("review", "approve", "regen"), default="review")
    ap.add_argument("--week-of", type=str, help="any date inside the target week")
    ap.add_argument("--feedback", type=str, help="what Pedro asked to change")
    ap.add_argument("--dry-run", action="store_true", help="print, send nothing")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    from build_week_card import collect_week
    from cadence_engine import LOCAL_TZ

    today = dt.datetime.now(LOCAL_TZ).date()
    # Approval must name the week it is approving. The button always carries
    # it; without that guard a bare --action approve would default to the week
    # containing today and quietly queue a week nobody reviewed.
    if args.action == "approve" and not args.week_of:
        print("--action approve needs --week-of (the button carries it)", file=sys.stderr)
        return 2
    week_of = dt.date.fromisoformat(args.week_of) if args.week_of else None
    # "regen" is a review with a note attached; only the wording differs.
    ahead = args.action in ("review", "regen")
    monday, sunday = week_window(week_of, today, ahead=ahead)

    card = build_card(collect_week(monday, sunday), monday, sunday)

    if args.action == "approve":
        # Approval is the only path that queues anything. It re-reads the
        # board rather than trusting what Friday saw, so a weekend fix is
        # picked up without a second round trip.
        import build_week_carousel as wc

        events = wc.collect_week(monday, sunday)
        if not events:
            msg = (f"⚠️ Approved {card['fields']['week_label']}, but the board has "
                   f"nothing for that week now — nothing queued.")
            print(msg)
            if not args.dry_run:
                tg_call("sendMessage", {"chat_id": envvar("TELEGRAM_CHAT_ID"), "text": msg})
            return 0

        print(f"Approved — queueing {len(events)} events for {monday} {POST_HOUR}")
        if args.dry_run:
            print(review_text(card))
            return 0
        sys.argv = ["build_week_carousel.py", "--week-of", monday.isoformat()]
        rc = wc.main()
        if rc == 0:
            tg_call("sendMessage", {
                "chat_id": envvar("TELEGRAM_CHAT_ID"),
                "text": (f"✅ {card['fields']['week_label']} is queued for "
                         f"{POST_DAY} {POST_HOUR}.\n"
                         "https://soynopalero.github.io/Azucar-Social-Pipeline/"),
                "disable_web_page_preview": True,
            })
        return rc

    if args.dry_run:
        print(review_text(card, args.feedback))
        return 0

    send_review(card, args.feedback, envvar("TELEGRAM_CHAT_ID"))
    print(f"Sent {card['fields']['week_label']} for review "
          f"({card['rows_used']} rows).")
    return 0


# ---------- tests ----------
def _card(rows, monday=dt.date(2026, 9, 28)):
    return build_card(rows, monday, monday + dt.timedelta(days=6))


def _ev(name, day, month=9, hour=21, price=None, title=None):
    return {"id": name, "name": name, "date": dt.date(2026, month, day),
            "hour": hour, "minute": 0, "price": price, "age": "21+",
            "entertainer": None, "card_title": title, "card_tagline": None}


def selftest() -> int:
    card = _card([_ev("Candy Shop", 2, month=10, price="$5", title="Candy Shop"),
                  _ev("Karaoke", 30, hour=19, price="Free", title="Karaoke")])
    txt = review_text(card)
    assert "This Week at Azúcar" in txt
    assert "Week Sept 28-Oct 4" in txt, txt
    assert "WED 30 · Karaoke" in txt, txt
    assert "FRI 2 · Candy Shop" in txt, txt
    # The gate has to be stated in the message, or a missed tap looks like a bug.
    assert "Nothing posts unless you tap" in txt
    assert "Monday 11:00 AM" in txt

    # A note from the redraft round is echoed back, so it is obvious which
    # version of the card is being looked at.
    assert "karaoke is 8pm now" in review_text(card, "karaoke is 8pm now")

    # An empty week says so plainly instead of sending a blank list, and says
    # approving does nothing — the one case where tapping ✅ is pointless.
    empty = review_text(_card([]))
    assert "Nothing on the board" in empty
    assert "Approving posts nothing" in empty

    # Overflow and over-long titles are surfaced here, not just in the JSON,
    # because Telegram is the only place anyone actually looks on a Friday.
    mon = dt.date(2026, 9, 28)
    busy_rows = []
    for i, c in enumerate("ABCDEFG"):          # 7 events, one past the 6 slots
        d = mon + dt.timedelta(days=min(i, 6))  # stays inside the Mon-Sun window
        busy_rows.append({"id": c, "name": f"Event {c}", "date": d, "hour": 20,
                          "minute": 0, "price": None, "age": "21+",
                          "entertainer": None, "card_title": f"Event {c}",
                          "card_tagline": None})
    busy = _card(busy_rows)
    assert "caption only" in review_text(busy), review_text(busy)
    longish = _card([_ev("Noche Vaquera Ranchera Extravaganza", 30)])
    assert "Set a Card Title" in review_text(longish) or \
           "set a Card Title" in review_text(longish)

    # The callback payload carries the week, so a tap on last Friday's message
    # can never queue this Friday's week by accident.
    assert card["week_of"] == "2026-09-28"

    # Approving without naming a week is refused rather than defaulting to
    # whichever week contains today.
    import subprocess
    here = str(Path(__file__).resolve())
    r = subprocess.run([sys.executable, here, "--action", "approve"],
                       capture_output=True, text=True)
    assert r.returncode == 2, (r.returncode, r.stdout, r.stderr)
    assert "needs --week-of" in r.stderr, r.stderr

    print("selftest: all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
