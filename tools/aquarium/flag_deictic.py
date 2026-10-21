#!/usr/bin/env python3
"""Flag transcript moments where the words alone cannot carry the instruction.

The speaker is standing in front of the tank pointing at things. "You twist
that one" is complete to someone watching and useless to someone reading, so
every such moment needs a still frame or a clip pinned to it before it can
become an SOP step.

Reads Whisper JSON (segments with start/end/text) or SRT, and writes a review
list plus the ffmpeg commands that pull a frame for each flagged moment.

    python flag_deictic.py transcript.json --video "clip-01.mp4" --out review/
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

# Words that point at something outside the transcript. Split by kind so the
# report can say *why* a line was flagged rather than just that it was.
DEICTIC = {
    "demonstrative": r"\b(this|that|these|those)\b",
    "place": r"\b(here|there|over here|over there|right here|down here|back here)\b",
    "vague-noun": r"\b(thing|things|stuff|piece|part|bit|guy|one|ones|deal|doohickey|thingy)\b",
    "manner": r"\b(like this|like that|like so|this way|that way|this much|about that)\b",
    "bare-color": r"\b(the (?:blue|red|green|black|white|grey|gray|clear|silver|yellow|orange) one)\b",
}

# Transcription is expected to be poor -- phone mic, running filter, hard
# surfaces. These mark spots to re-listen to rather than trust.
UNCERTAIN = {
    "inaudible": r"\[(?:inaudible|unintelligible|indistinct|noise)\]|\(\?\)|\.\.\.",
    "hedge": r"\b(um|uh|whatchamacallit|what do you call it|i forget|something like)\b",
}

# Idioms that use a deictic word without pointing at anything. Over-flagging is
# cheaper than under-flagging here -- a spare frame costs nothing, a missing one
# costs a step -- but "first thing every week" is noise, and noise gets ignored.
NON_DEICTIC = re.compile(
    r"\b(?:first thing|one thing|another thing|same thing|the thing is|sure thing"
    r"|one of|no one|any one|every one|each one|one day|one time|for one"
    r"|at one point|there (?:is|are|was|were)|there you go|and that's (?:it|that))\b",
    re.IGNORECASE,
)

SRT_TIME = re.compile(
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})"
)


@dataclass
class Flag:
    start: float
    end: float
    text: str
    kinds: list[str]
    terms: list[str]
    needs_visual: bool

    @property
    def timestamp(self) -> str:
        m, s = divmod(int(self.start), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    @property
    def slug(self) -> str:
        return f"{int(self.start // 3600):02d}{int(self.start // 60) % 60:02d}{int(self.start) % 60:02d}"


def parse_srt(text: str) -> list[dict]:
    segments, pending, start, end = [], [], None, None
    for line in text.splitlines():
        match = SRT_TIME.search(line)
        if match:
            if pending and start is not None:
                segments.append({"start": start, "end": end, "text": " ".join(pending)})
            g = [int(x) for x in match.groups()]
            start = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
            end = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
            pending = []
        elif line.strip() and not line.strip().isdigit():
            pending.append(line.strip())
    if pending and start is not None:
        segments.append({"start": start, "end": end, "text": " ".join(pending)})
    return segments


def load_segments(path: Path) -> list[dict]:
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".srt", ".vtt"}:
        return parse_srt(raw)
    data = json.loads(raw)
    segments = data["segments"] if isinstance(data, dict) else data
    return [
        {"start": float(s["start"]), "end": float(s["end"]), "text": str(s["text"]).strip()}
        for s in segments
    ]


def scan(segments: list[dict]) -> list[Flag]:
    flags = []
    for seg in segments:
        text = seg["text"]
        # Match against the idiom-stripped text, but report what he actually said.
        probe = NON_DEICTIC.sub(" ", text)
        kinds, terms = [], []
        for kind, pattern in {**DEICTIC, **UNCERTAIN}.items():
            found = re.findall(pattern, probe, flags=re.IGNORECASE)
            if found:
                kinds.append(kind)
                # findall yields tuples when a pattern has groups.
                terms += [f if isinstance(f, str) else next(x for x in f if x) for f in found]
        if kinds:
            flags.append(
                Flag(
                    start=seg["start"],
                    end=seg["end"],
                    text=text,
                    kinds=sorted(set(kinds)),
                    terms=sorted({t.lower() for t in terms if t}),
                    needs_visual=any(k in DEICTIC for k in kinds),
                )
            )
    return flags


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("transcript", type=Path)
    ap.add_argument("--video", default="INPUT.mp4", help="source file the timestamps refer to")
    ap.add_argument("--out", type=Path, default=Path("review"))
    args = ap.parse_args()

    if not args.transcript.exists():
        print(f"transcript not found: {args.transcript}", file=sys.stderr)
        return 1

    segments = load_segments(args.transcript)
    flags = scan(segments)
    args.out.mkdir(parents=True, exist_ok=True)

    visual = [f for f in flags if f.needs_visual]
    unclear = [f for f in flags if not f.needs_visual]

    lines = [
        "# Transcript review",
        "",
        f"- segments: {len(segments)}",
        f"- need a frame or clip: **{len(visual)}**",
        f"- unclear audio, re-listen: **{len(unclear)}**",
        "",
        "## Needs a visual",
        "",
        "Each line points at something the words don't name. No SOP step may cite",
        "one of these without a frame or clip beside it.",
        "",
        "| time | what he says | pointing via |",
        "|---|---|---|",
    ]
    for f in visual:
        say = f.text.replace("|", "\\|")
        lines.append(f"| `{f.timestamp}` | {say} | {', '.join(f.kinds)} |")

    if unclear:
        lines += [
            "",
            "## Unclear audio",
            "",
            "Confirm these with him while he is still reachable.",
            "",
            "| time | heard as |",
            "|---|---|",
        ]
        lines += [f"| `{f.timestamp}` | {f.text.replace('|', chr(92) + '|')} |" for f in unclear]

    (args.out / "review.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (args.out / "flags.json").write_text(
        json.dumps([asdict(f) for f in flags], indent=2), encoding="utf-8"
    )

    # One frame per flagged moment, grabbed a beat after he starts pointing.
    script = ["#!/bin/sh", "# Frames for every moment the words alone are not enough.", "set -e", "mkdir -p frames"]
    for f in visual:
        at = f.start + min(1.0, max(0.0, (f.end - f.start) / 2))
        script.append(
            f'ffmpeg -v error -y -ss {at:.2f} -i "{args.video}" '
            f'-frames:v 1 -q:v 3 "frames/at-{f.slug}.jpg"'
        )
    (args.out / "grab_frames.sh").write_text("\n".join(script) + "\n", encoding="utf-8")

    print(f"{len(visual)} moments need a visual, {len(unclear)} need confirming")
    print(f"wrote {args.out}/review.md, flags.json, grab_frames.sh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
