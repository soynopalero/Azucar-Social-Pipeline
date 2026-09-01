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
| Hosting | **New dedicated repo**, public, no auth (see Hosting below) |
| Source video | `C:\Users\Pedro.AzureAD\Videos\Aquarium Cleaning` |
| Contractor on a public page | Agreed — gate is open |
| Contractor reachable | Not for ~2 weeks |

Not this repo. An aquarium SOP is unrelated to the social pipeline, and the
clips would weigh on it permanently.

## The deadline is the clean, not the contractor

Two facts landed after the first draft of this file, and they invert its
priorities:

- The contractor **has agreed** to being on a public page. That gate is open.
- He is reachable, but **not for about two weeks**.
- **The tank is being cleaned tomorrow.**

So the ambiguity list is no longer the urgent artifact — he cannot answer it
for a fortnight either way. The urgent artifact is something a person can
follow at the tank tomorrow.

`sop/index.html` is that stopgap, written from general freshwater practice
rather than from his knowledge: the fish-killing rules, a water change, a
filter section branching by filter type, and a field-notes checklist whose
real job is gathering what tomorrow's clean can tell us. Every gap is marked
in the page rather than guessed at.

## Order of work

1. `extract-aquarium-media.ps1` — inventory, audio, contact sheets.
2. Transcribe (below).
3. Look at the contact sheets and name the equipment before writing steps.
4. `flag_deictic.py` — the questions for him, plus a frame-grab script.
5. Rewrite `sop/index.html` from his actual procedure, cut clips, deploy.
6. Hold the flagged list for the two-week conversation, and add whatever
   tomorrow's field notes turn up to it.

Where his procedure and the stopgap disagree, **his wins** — it is this tank
and this filter. Keep the general safety rules, which hold regardless.

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

Two routes. On the Windows machine, faster-whisper below is easier and can
use a GPU. In a cloud container, its weights are unreachable — use
`fetch_models.sh` + `transcribe.py`, which pull Whisper-as-ONNX from GitHub
release assets and run fully offline:

```sh
./fetch_models.sh medium.en          # small.en is 636 MB, medium.en 1.9 GB
pip install sherpa-onnx numpy
python transcribe.py audio.opus --models models --size medium.en --out transcript/
```

It segments with a voice activity detector first, so every line carries a
real start and end — Whisper on its own returns one block of text and caps
at 30 seconds per call. Output is Whisper-shaped JSON plus SRT, and feeds
`flag_deictic.py` directly.

Measured on container CPU: **small.en 3.8x realtime** (18 min of audio in
about five), **medium.en 1.0x** (about eighteen), 636 MB versus 1.9 GB
downloaded and 3.8 GB unpacked. Both produced identical errors on synthetic
test speech, so that test cannot say which is better on real audio — it only
shows the errors were the synthesiser's. Run small.en on the first real file,
and only reach for medium.en if equipment names are coming out wrong.

### The easier route, where the network allows it

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

## Hosting — Cloudflare is already in the stack

The brief weighed Vercel against GitHub Pages. Neither is the obvious pick:
this repo already deploys to **Cloudflare Pages** (project
`azucar-post-manager`, see `manager/README.md`), so the account, the
workflow and the muscle memory are all there. A new repo wires up the same
way in a couple of minutes.

**The trap:** the existing Pages project sits behind **Cloudflare Access**,
an email allow-list. The SOP must be public with no login — someone reads it
standing at the tank, possibly not a Pedro-account holder at all. Create the
new project *without* an Access application in front of it, and open the
deployed URL in a private window to confirm it doesn't bounce to a login.

Per-file limits, worth confirming against current docs before cutting a
long clip: Cloudflare Pages caps a single file around 25 MiB; GitHub Pages
caps at 100 MB and gets unhappy past ~1 GB in a repo. Short 720p clips land
under either, but the Cloudflare ceiling is the tighter one — one more
reason to keep clips to one step each rather than long reused takes.

## Still open — needs Pedro

- Supply sources and a callback number, for the two-week conversation.
- Whoever cleans the tank tomorrow should fill in the field notes in
  `sop/index.html` §11 and photograph the equipment — that is the only
  information-gathering opportunity before he is reachable.
- Which property the tank is at.
- Whether a printable PDF for a binder is wanted alongside the page.
