# Aquarium cleaning SOP — handoff to the local session

Written from a Claude Code **web** session, which cannot reach the footage.
The work continues in a **local** session on `gokic-00101`. Read this first.

## Decisions locked

| Question | Answer |
|---|---|
| Where the processing runs | Local session on `gokic-00101` |
| Recording language | English |
| SOP language | English only |
| Output | Single `index.html`, clips inline, mobile-first |
| Hosting | **New dedicated repo**, GitHub Pages, public, no auth |
| Source video | `C:\Users\Pedro.AzureAD\Videos\Aquarium Cleaning` |

Not this repo. An aquarium SOP is unrelated to the social pipeline, and the
clips would weigh on it permanently.

## Do the ambiguity list before the pretty page

The brief has the "ask the fish guy" list falling out of step 3, as a
byproduct of writing the SOP. Invert that. The page can be built any week.
He cannot. Transcribe, run `flag_deictic.py`, and get the list to Pedro on
day one — everything else is recoverable, that window is not.

## Order of work

1. `extract-aquarium-media.ps1` — inventory, audio, contact sheets.
2. Transcribe (below).
3. `flag_deictic.py` — the questions for him, plus a frame-grab script.
4. **Send Pedro the list.** Stop here until it goes out.
5. Look at the contact sheets and name the equipment before writing steps.
6. Write the SOP, cut clips, build the page, deploy.

## Verified commands

These ran against test footage in the web container. `ffmpeg`/`ffprobe`
behaviour is identical on Windows.

**Probing.** Read rotation from the video stream's `side_data_list`:

```bash
ffprobe -v error -print_format json -show_format -show_streams -- INPUT.mp4
```

Do **not** ask for it as `-show_entries side_data=rotation`. That makes
ffprobe dump every packet and frame in the file — hundreds of KB of noise
per clip. Confirmed the hard way. Rotation appears as a Display Matrix
entry with a `rotation` key; older files instead carry `tags.rotate`.
Check both, and check before cutting anything, or the clips come out
sideways on a phone.

**Audio for transcription** — ~5 MB for 18 minutes:

```bash
ffmpeg -v error -y -i INPUT.mp4 -vn -ac 1 -ar 16000 -c:a libopus -b:a 32k -- audio.opus
```

**Contact sheet** — a 5x5 tile of 320px frames, one per 15 s:

```bash
ffmpeg -v error -y -i INPUT.mp4 -vf "fps=1/15,scale=320:-2,tile=5x5" -q:v 4 -- sheet-%02d.jpg
```

Look at these. They are how "the blue one" becomes a named part.

## Transcription

Expect poor audio — phone mic, running filter and pumps, hard surfaces.
Budget for correction passes.

```python
from faster_whisper import WhisperModel

model = WhisperModel("large-v3", device="cuda", compute_type="float16")  # or device="cpu"
segments, _ = model.transcribe(
    "audio.opus",
    language="en",
    word_timestamps=True,          # required -- clip cuts key off these
    vad_filter=True,               # helps against constant pump noise
    initial_prompt=(
        "Aquarium maintenance. Canister filter, impeller, media basket, bio-media, "
        "ceramic rings, filter floss, sponge pre-filter, powerhead, substrate, "
        "gravel vacuum, siphon, dechlorinator, Prime, water conditioner, ammonia, "
        "nitrite, nitrate, pH, KH, GH, API master test kit, algae scraper, magnet "
        "cleaner, heater, airstone, return line, intake, spray bar, O-ring, priming."
    ),
)
```

The `initial_prompt` is doing real work — it is what keeps "bio-media" from
landing as "bio meeting". Treat every equipment name as suspect anyway and
check it against the contact sheets.

## Flagging what the words can't carry

```bash
python flag_deictic.py transcript.json --video "clip-01.mp4" --out review/
```

Writes `review.md` (moments needing a visual, and unclear audio to confirm),
`flags.json`, and `grab_frames.sh` which pulls a frame for each. The rule
from the brief holds: **no SOP step may cite a flagged moment without a
frame or clip beside it.**

## Page requirements

Mobile-first, read one-handed with wet hands. Large tap targets, generous
type, high contrast. Per step: number, plain instruction, clip inline as
`<video controls preload="metadata" playsinline poster="...">`, warning
callout where he gives one. `preload="metadata"`, never `auto`. Sticky
jump-to nav. Prints cleanly with clips falling back to poster frames. No
CDN, no fonts, no frameworks — it has to work on bad phone data in a back room.

Clips: 720p, `-movflags +faststart`, one step each, none reused across steps.

```bash
ffmpeg -ss START -i INPUT.mp4 -t DURATION \
  -vf "scale=-2:720" -c:v libx264 -crf 26 -preset medium \
  -c:a aac -b:a 96k -movflags +faststart clips/step-03.mp4
```

GitHub Pages caps a single file at 100 MB and gets unhappy past ~1 GB in a
repo. Short 720p clips land far under that, but keep an eye on the total.

## Still open — needs Pedro

- **How long is the fish guy reachable, and will he do one follow-up call?**
  Drives everything above. If he's gone this week, skip polish and race to
  the gap list.
- He has not agreed to being on a public, no-login page. He is on camera and
  audible throughout. Settle before deploy.
- Supply sources and a callback number, captured in the same conversation.
- Which property the tank is at.
- Whether a printable PDF for a binder is wanted alongside the page.
