#!/usr/bin/env python3
"""
build_week_card.py
------------------
Turn the Monday board into the six rows of the "This Week at Azúcar" card.

What this is
------------
The weekly round-up carousel (build_week_carousel.py) posts the week's
flyers. Its first slide should be a card with the week written out, because a
stack of flyers does not tell anyone what is on Thursday. That card is a
punk-zine Canva design with six fixed event rows; this script decides what
goes in them.

It emits data, not pixels. The output is JSON that maps one-to-one onto the
Canva template's autofill fields:

    week_label                  "Week Sept 21-27"
    day_1 .. day_6              "THU 24"
    title_1 .. title_6          "Heels Class"
    detail_1 .. detail_6        "with Frankie 6 PM • with Kimora 7 PM • $10"

Rows past the last event come back empty; whoever fills the template deletes
those strips so a quiet week does not show blank paper.

The merging rule
----------------
Two events on the same day that are really one thing — the 6pm and 7pm heels
classes — take one row, not two. Six rows is a hard ceiling, and spending two
of them on the same class is how a genuinely busy week loses an event.

Merging is decided in this order:

1. Same day + same Card Title on the board. Explicit, and the way to force
   it: set both heels classes to "Heels Class" and they combine.
2. Same day + names that share a long common prefix ("Heels dance class with
   Frankie" / "...with Kimora"). This is the fallback for events nobody has
   given a Card Title yet, which is most of them.

A merged row's detail line carries each part with its own time, so the
information survives the merge:  `with Frankie 6 PM • with Kimora 7 PM • $10`

Overflow past six rows is reported, never silently dropped — the caller puts
it in the caption. That is the same contract build_week_carousel.py already
uses for flyers past Meta's 10-slide limit.

Usage:
    python code/build_week_card.py                    # this week, as JSON
    python code/build_week_card.py --week-of 2026-10-05
    python code/build_week_card.py --pretty           # human-readable
    python code/build_week_card.py --selftest         # offline, no network
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

SLOTS = 6                 # event rows on the card; matches the Canva template
TITLE_MAX = 22            # characters that still fit the bold line at 46px

COL_CARD_TITLE = "text_mm7hrgth"
COL_CARD_TAGLINE = "text_mm7hnx63"
COL_ENTERTAINER = "text_mm3h4q4q"

DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "June", "July",
          "Aug", "Sept", "Oct", "Nov", "Dec"]

# Words that pad out a board name but say nothing on a card that is already
# headed "This Week at Azúcar". Stripped only from the end, and only while
# something is left over.
TAIL_NOISE = ("drag show", "viewing party", "watch party", "party",
              "night", "class", "show")

# Merge rule 2: how much of the shorter name two events must share before
# they are treated as the same thing. 12 characters stops "Drag Bingo" and
# "Drag Show" merging on a common "Drag "; 0.55 stops a long name swallowing
# a short one that merely starts the same way.
PREFIX_MIN_CHARS = 12
PREFIX_MIN_RATIO = 0.55


# ---------- formatting ----------
def day_label(d: dt.date) -> str:
    """`THU 24` — the black tag at the top of a row."""
    return f"{DAYS[d.weekday()]} {d.day}"


def week_label(monday: dt.date, sunday: dt.date) -> str:
    """`Week Sept 21-27`, or `Week Sept 28-Oct 4` across a month boundary."""
    a = MONTHS[monday.month - 1]
    if monday.month == sunday.month:
        return f"Week {a} {monday.day}-{sunday.day}"
    b = MONTHS[sunday.month - 1]
    return f"Week {a} {monday.day}-{b} {sunday.day}"


def fmt_time(hour, minute) -> str | None:
    """`9 PM` / `6:30 PM` — card style, uppercase and spaced."""
    if hour is None:
        return None
    suffix = "AM" if hour < 12 else "PM"
    h12 = hour % 12 or 12
    return f"{h12}:{minute:02d} {suffix}" if minute else f"{h12} {suffix}"


def fmt_price(price: str | None) -> str | None:
    """Board prices are hand-typed: "$15", "10$", "20", "Free", "$20-$40".

    Normalise to a leading sign so the same price written two ways compares
    equal. The two heels classes really are typed "10$" and "$10" on the live
    board; without this the merged row reads "$10 / 10$" as though they cost
    different amounts. Flipping a trailing sign also avoids the "$10$" that
    blindly prefixing produced. "Free" is shouted — free is the selling point.
    """
    if not price:
        return None
    p = " ".join(price.split())
    if not p:
        return None
    if p.lower() == "free":
        return "FREE"
    m = re.fullmatch(r"(\d[\d.,]*)\s*\$", p)      # "10$" -> "$10"
    if m:
        return f"${m.group(1)}"
    return p if "$" in p or not p[:1].isdigit() else f"${p}"


def shorten_title(name: str) -> str:
    """Board names are written for the board ("Heels dance class with
    Frankie"). The card has room for about 22 characters.

    Cut at "with"/"and"/"—" first, since that is where board names hang their
    detail, then drop trailing filler words. Never returns empty: a name that
    is nothing but filler is kept whole rather than erased.
    """
    s = " ".join((name or "").split())
    if not s:
        return ""

    for sep in (" with ", " w/ ", " — ", " - ", " feat. ", " ft. ", ": "):
        i = s.lower().find(sep)
        if i > 0:
            s = s[:i].strip()
            break

    changed = True
    while changed and len(s) > TITLE_MAX:
        changed = False
        for tail in TAIL_NOISE:
            if s.lower().endswith(" " + tail):
                trimmed = s[: -(len(tail) + 1)].strip()
                if trimmed:
                    s, changed = trimmed, True
                    break
    return s


def common_prefix_len(a: str, b: str) -> int:
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def same_thing(a: dict, b: dict) -> bool:
    """Are these two board items one event on the card?"""
    if a["date"] != b["date"]:
        return False

    ta, tb = (a.get("card_title") or ""), (b.get("card_title") or "")
    if ta and tb:                       # rule 1: explicit, and authoritative
        return ta.casefold() == tb.casefold()
    if ta or tb:                        # one set, one not — not a match
        return False

    na, nb = a["name"].casefold(), b["name"].casefold()
    shared = common_prefix_len(na, nb)  # rule 2: near-identical names
    shortest = min(len(na), len(nb))
    return (shared >= PREFIX_MIN_CHARS
            and shortest > 0
            and shared / shortest >= PREFIX_MIN_RATIO)


def merged_title(group: list[dict]) -> str:
    """The bold line for a row, merged or not."""
    explicit = next((e["card_title"] for e in group if e.get("card_title")), None)
    if explicit:
        return explicit
    if len(group) == 1:
        return shorten_title(group[0]["name"])

    # Merged with no Card Title: the shared prefix of the names is the
    # thing they have in common, which is exactly the title we want.
    prefix = group[0]["name"]
    for e in group[1:]:
        prefix = prefix[: common_prefix_len(prefix.casefold(), e["name"].casefold())]
    prefix = prefix.strip().rstrip("-—:,")
    for tail in (" with", " w/", " and", " feat.", " ft."):
        if prefix.lower().endswith(tail):
            prefix = prefix[: -len(tail)].strip()
    return shorten_title(prefix) or shorten_title(group[0]["name"])


def part_label(e: dict, title: str) -> str | None:
    """What distinguishes one half of a merged row: usually the instructor."""
    who = (e.get("entertainer") or "").strip()
    if who and who.casefold() != title.casefold():
        return who
    name = e["name"]
    for sep in (" with ", " w/ "):
        i = name.lower().find(sep)
        if i > 0:
            return name[i + len(sep):].strip()
    return None


def detail_line(group: list[dict], title: str) -> str:
    """The small line under the title.

    Single event:  `Rohla Blunt & Abele Fantasy • 21+ • 9 PM • $15`
    Merged:        `with Frankie 6 PM • with Kimora 7 PM • $10`

    A merged row keeps each part's own time, because "Heels Class • 6 PM"
    would quietly lose the 7pm session.
    """
    bits: list[str] = []

    if len(group) > 1:
        for e in group:
            who = part_label(e, title)
            when = fmt_time(e["hour"], e["minute"])
            if who and when:
                bits.append(f"with {who} {when}")
            elif who:
                bits.append(f"with {who}")
            elif when:
                bits.append(when)
    else:
        e = group[0]
        lead = (e.get("card_tagline") or "").strip() or part_label(e, title)
        if lead:
            bits.append(lead)

    ages = {e.get("age") for e in group if e.get("age")}
    if len(ages) == 1:
        bits.append(ages.pop())

    if len(group) == 1:
        when = fmt_time(group[0]["hour"], group[0]["minute"])
        if when:
            bits.append(when)

    prices = {fmt_price(e.get("price")) for e in group}
    prices.discard(None)
    if len(prices) == 1:
        bits.append(prices.pop())
    elif prices:
        bits.append(" / ".join(sorted(prices)))

    return " • ".join(bits)


# ---------- assembly ----------
def group_events(events: list[dict]) -> list[list[dict]]:
    """Chronological rows, with same-day duplicates folded together."""
    rows: list[list[dict]] = []
    for e in sorted(events, key=lambda x: (x["date"], x["hour"] if x["hour"] is not None else 99, x["name"])):
        for row in rows:
            if same_thing(row[0], e):
                row.append(e)
                break
        else:
            rows.append([e])
    return rows


def build_card(events: list[dict], monday: dt.date, sunday: dt.date) -> dict:
    """Board events in, autofill fields out."""
    rows = group_events(events)
    shown, overflow = rows[:SLOTS], rows[SLOTS:]

    fields = {"week_label": week_label(monday, sunday)}
    for i in range(1, SLOTS + 1):
        fields[f"day_{i}"] = ""
        fields[f"title_{i}"] = ""
        fields[f"detail_{i}"] = ""

    for i, group in enumerate(shown, start=1):
        title = merged_title(group)
        fields[f"day_{i}"] = day_label(group[0]["date"])
        fields[f"title_{i}"] = title
        fields[f"detail_{i}"] = detail_line(group, title)

    return {
        "week_of": monday.isoformat(),
        "rows_used": len(shown),
        "fields": fields,
        # Named, not counted: the caller puts these in the caption so a
        # seventh event is never simply lost.
        "overflow": [merged_title(g) for g in overflow],
        "long_titles": [fields[f"title_{i}"] for i in range(1, len(shown) + 1)
                        if len(fields[f"title_{i}"]) > TITLE_MAX],
    }


# ---------- live layer ----------
def collect_week(monday: dt.date, sunday: dt.date) -> list[dict]:
    """Events in the window. Needs the Monday board."""
    from build_fb_kit import (COL_AGE, COL_DATE, COL_PHASE, COL_PRICE,
                              COL_TIME, HIDDEN_PHASES, col, fetch_items)

    out = []
    for item in fetch_items():
        date_iso = (col(item, COL_DATE) or {}).get("date")
        if not date_iso:
            continue
        try:
            d = dt.date.fromisoformat(date_iso)
        except ValueError:
            continue
        if not (monday <= d <= sunday):
            continue
        if (col(item, COL_PHASE) or {}).get("label") in HIDDEN_PHASES:
            continue

        hour_c = col(item, COL_TIME) or {}
        out.append({
            "id": item["id"],
            "name": (item.get("name") or "").strip() or "Untitled",
            "date": d,
            "hour": hour_c.get("hour"),
            "minute": hour_c.get("minute") or 0,
            "price": (col(item, COL_PRICE) or {}).get("text"),
            "age": (col(item, COL_AGE) or {}).get("label"),
            "entertainer": (col(item, COL_ENTERTAINER) or {}).get("text"),
            "card_title": (col(item, COL_CARD_TITLE) or {}).get("text"),
            "card_tagline": (col(item, COL_CARD_TAGLINE) or {}).get("text"),
        })
    return out


def week_window(week_of: dt.date | None, today: dt.date,
                ahead: bool = False) -> tuple[dt.date, dt.date]:
    """Monday..Sunday of the week CONTAINING the given day.

    Same rule as build_week_carousel: the card goes out on Monday morning
    about the days that follow it, so on Monday the answer is this week.

    `ahead` targets the NEXT week instead, which is what the Friday review
    run wants: it is built on Friday for the week that starts on Monday, so
    there is a weekend to fix the board before anything posts. An explicit
    --week-of always wins, so a rerun can name any week directly.
    """
    base = week_of or today
    monday = base - dt.timedelta(days=base.weekday())
    if ahead and week_of is None:
        monday += dt.timedelta(days=7)
    return monday, monday + dt.timedelta(days=6)


def render(card: dict) -> str:
    f = card["fields"]
    out = [f["week_label"], ""]
    for i in range(1, SLOTS + 1):
        if not f[f"title_{i}"]:
            out.append(f"  {i}. (empty — strip deleted)")
            continue
        out.append(f"  {i}. {f['day_' + str(i)]:<7} {f['title_' + str(i)]}")
        if f[f"detail_{i}"]:
            out.append(f"     {' ' * 7} {f['detail_' + str(i)]}")
    if card["overflow"]:
        out += ["", "  overflow (caption only): " + ", ".join(card["overflow"])]
    if card["long_titles"]:
        out += ["", "  WARNING: too long for the bold line, set a Card Title: "
                + ", ".join(card["long_titles"])]
    return "\n".join(out)


# ---------- tests ----------
def _ev(name, day, hour=None, minute=0, price=None, age=None,
        entertainer=None, card_title=None, card_tagline=None):
    return {"id": name, "name": name, "date": dt.date(2026, 9, day),
            "hour": hour, "minute": minute, "price": price, "age": age,
            "entertainer": entertainer, "card_title": card_title,
            "card_tagline": card_tagline}


def selftest() -> int:
    assert day_label(dt.date(2026, 9, 24)) == "THU 24"
    assert day_label(dt.date(2026, 9, 27)) == "SUN 27"

    assert week_label(dt.date(2026, 9, 21), dt.date(2026, 9, 27)) == "Week Sept 21-27"
    # A week that straddles two months names both.
    assert week_label(dt.date(2026, 9, 28), dt.date(2026, 10, 4)) == "Week Sept 28-Oct 4"

    assert fmt_time(21, 0) == "9 PM"
    assert fmt_time(18, 30) == "6:30 PM"
    assert fmt_time(11, 0) == "11 AM"
    assert fmt_time(0, 0) == "12 AM"
    assert fmt_time(None, 0) is None

    # Prices carrying their own sign are never double-signed, wherever the
    # sign sits. Both "$10" and "10$" are real values on the live board.
    assert fmt_price("$10") == "$10"
    # The same price typed two ways must normalise to one, or a merged row
    # claims the two heels classes cost different amounts.
    assert fmt_price("10$") == "$10"
    assert fmt_price("10 $") == "$10"
    assert fmt_price("20") == "$20"
    assert fmt_price("$20-$40") == "$20-$40"
    assert fmt_price("Free") == "FREE"
    assert fmt_price(None) is None and fmt_price("  ") is None

    assert shorten_title("Heels dance class with Frankie") == "Heels dance class"
    assert shorten_title("Industry Night Drag Show") == "Industry Night"
    assert shorten_title("Candy Shop") == "Candy Shop"
    # Stripping filler must never empty a title out.
    assert shorten_title("Drag Show") == "Drag Show"
    assert shorten_title("") == ""

    # --- merging ---
    frankie = _ev("Heels dance class with Frankie", 24, 18, price="10$",
                  age="21+", entertainer="Frankie")
    kimora = _ev("Heels dance class with Kimora", 24, 19, price="$10",
                 age="21+", entertainer="Kimora")
    assert same_thing(frankie, kimora)

    # Same names, different days: never merged.
    assert not same_thing(frankie, _ev("Heels dance class with Frankie", 25, 18))
    # A shared first word is not enough.
    assert not same_thing(_ev("Drag Bingo", 24), _ev("Drag Show", 24))
    # An explicit Card Title decides it, both ways.
    assert same_thing(_ev("Totally Different", 24, card_title="Heels Class"),
                      _ev("Nothing Alike", 24, card_title="heels class"))
    assert not same_thing(_ev("Heels dance class with A", 24, card_title="Heels"),
                          _ev("Heels dance class with B", 24, card_title="Other"))

    rows = group_events([kimora, frankie])
    assert len(rows) == 1 and len(rows[0]) == 2
    # Merged rows keep both times, so neither session is lost.
    line = detail_line(rows[0], merged_title(rows[0]))
    assert line == "with Frankie 6 PM • with Kimora 7 PM • 21+ • $10", line
    # The shared prefix becomes the title, with the dangling "with" removed.
    assert merged_title(rows[0]) == "Heels dance class", merged_title(rows[0])

    # A single event leads with its tagline when one is set, else the act.
    solo = _ev("Industry Night Drag Show", 27, 21, price="$15", age="21+",
               entertainer="Rohla Blunt & Abele Fantasy")
    assert (detail_line([solo], "Industry Night")
            == "Rohla Blunt & Abele Fantasy • 21+ • 9 PM • $15")
    tagged = _ev("Candy Shop", 25, 21, price="$5", age="18+",
                 entertainer="DJ Ralphy Ray", card_tagline="girls free before 11")
    assert (detail_line([tagged], "Candy Shop")
            == "girls free before 11 • 18+ • 9 PM • $5")
    # An act named the same as the row adds nothing and is left out.
    assert detail_line([_ev("Furanium Fever", 26, 18, price="$15", age="21+",
                            entertainer="Furanium Fever")], "Furanium Fever") \
        == "21+ • 6 PM • $15"

    # --- the real week, end to end ---
    week = [frankie, kimora,
            _ev("American Horror Story viewing party and Drag show", 24, 19,
                price="Free", age="21+", entertainer="Drag show",
                card_title="AHS Drag Show"),
            tagged,
            _ev("Furanium Fever", 26, 18, price="$15", age="21+",
                entertainer="Furanium Fever", card_tagline="Tri-Cities Furs takeover"),
            solo]
    card = build_card(week, dt.date(2026, 9, 21), dt.date(2026, 9, 27))
    f = card["fields"]
    assert card["rows_used"] == 5, card["rows_used"]
    assert f["week_label"] == "Week Sept 21-27"
    assert (f["day_1"], f["title_1"]) == ("THU 24", "Heels dance class")
    assert (f["day_2"], f["title_2"]) == ("THU 24", "AHS Drag Show")
    assert (f["day_3"], f["title_3"]) == ("FRI 25", "Candy Shop")
    assert (f["day_4"], f["title_4"]) == ("SAT 26", "Furanium Fever")
    assert (f["day_5"], f["title_5"]) == ("SUN 27", "Industry Night")
    # The unused sixth row comes back empty so the filler deletes the strip.
    assert f["day_6"] == "" and f["title_6"] == "" and f["detail_6"] == ""
    assert card["overflow"] == [] and card["long_titles"] == []

    # --- overflow is named, never silently dropped ---
    busy = [_ev(f"Event {c}", 21 + i, 20) for i, c in enumerate("ABCDEFG")]
    big = build_card(busy, dt.date(2026, 9, 21), dt.date(2026, 9, 27))
    assert big["rows_used"] == SLOTS
    assert big["overflow"] == ["Event G"], big["overflow"]

    # --- an empty week is a valid card, not a crash ---
    blank = build_card([], dt.date(2026, 9, 28), dt.date(2026, 10, 4))
    assert blank["rows_used"] == 0
    assert blank["fields"]["week_label"] == "Week Sept 28-Oct 4"
    assert all(blank["fields"][f"title_{i}"] == "" for i in range(1, SLOTS + 1))

    # --- a title too long to fit is flagged, not silently clipped ---
    longish = build_card([_ev("Noche Vaquera Ranchera Extravaganza", 26, 20)],
                         dt.date(2026, 9, 21), dt.date(2026, 9, 27))
    assert longish["long_titles"], longish

    # --- week_window matches the carousel's rule ---
    assert week_window(None, dt.date(2026, 9, 23))[0] == dt.date(2026, 9, 21)
    assert week_window(None, dt.date(2026, 9, 21))[0] == dt.date(2026, 9, 21)
    assert week_window(dt.date(2026, 10, 8), dt.date(2026, 9, 1))[0] == dt.date(2026, 10, 5)

    # --- the Friday review run targets the week that starts on Monday ---
    # Friday Sept 25 reviews Sept 28 - Oct 4, so the weekend is left to fix
    # the board in before anything is queued.
    assert week_window(None, dt.date(2026, 9, 25), ahead=True) == (
        dt.date(2026, 9, 28), dt.date(2026, 10, 4))
    # Every weekday lands on the same following Monday, so a manual rerun on
    # Saturday reviews the same week the Friday job did.
    for day in range(21, 28):
        assert week_window(None, dt.date(2026, 9, day), ahead=True)[0] == dt.date(2026, 9, 28)
    # An explicit --week-of always wins over --next-week; otherwise a rerun
    # naming a week would silently review the one after it.
    assert week_window(dt.date(2026, 9, 23), dt.date(2026, 9, 25), ahead=True)[0] \
        == dt.date(2026, 9, 21)

    print("selftest: all checks passed")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--week-of", type=str, help="any date inside the target week")
    ap.add_argument("--next-week", action="store_true",
                    help="target the week after this one (the Friday review run)")
    ap.add_argument("--pretty", action="store_true", help="human-readable, not JSON")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    from cadence_engine import LOCAL_TZ

    today = dt.datetime.now(LOCAL_TZ).date()
    week_of = dt.date.fromisoformat(args.week_of) if args.week_of else None
    monday, sunday = week_window(week_of, today, ahead=args.next_week)

    card = build_card(collect_week(monday, sunday), monday, sunday)
    print(render(card) if args.pretty else json.dumps(card, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
