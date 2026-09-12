# Runway video — setup and use

Runway (Gen-4) turns a still flyer into a short moving clip for Reels, Stories
and TikTok. This page covers getting the key in place once, then the two ways
to make a video: on your own laptop, or from the GitHub Actions tab.

Short version: **put the key in `.env` locally and in GitHub → Settings →
Secrets as `RUNWAY_API_KEY`.** Details below.

## 1. Get the API key

The Runway **API** is a separate product from the runwayml.com web app — a
Runway subscription does not include API credits, and the key does not come
from the app's account page.

1. Go to **https://dev.runwayml.com** and sign in (the same login is fine).
2. Create an organization if it asks.
3. **Billing → add credits.** The API is prepaid; with zero credits every
   request comes back as an error. A 5-second Gen-4 Turbo clip is a handful of
   credits, so a small top-up covers a lot of flyers.
4. **API keys → New API key.** Name it something like `azucar-pipeline`.
5. Copy it. Runway shows the key **once** — if you lose it, delete that key
   and make a new one.

The key looks like `key_` followed by a long string.

## 2. Put the key where the code looks for it

There are two places, because there are two ways to run it.

### For running on your own computer — `.env`

Open `.env` in the repo folder (the same file that holds the Facebook and
Monday keys) and add one line:

```
RUNWAY_API_KEY=key_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

`.env` is listed in `.gitignore`, so it stays on your machine and never goes
to GitHub. **This repo is public — the key must never be typed into a file
that gets committed.**

### For running from GitHub — a repository secret

1. In the repo on github.com: **Settings → Secrets and variables → Actions**.
2. **New repository secret.**
3. Name: `RUNWAY_API_KEY` — exactly that, capitals and underscore.
4. Secret: paste the key. **Add secret.**

GitHub encrypts it and masks it in the logs. Same pattern as
`FB_PAGE_ACCESS_TOKEN` and the rest.

> **Never paste the key into a chat message, a comment, an issue, or a commit.**
> Anything typed into chat is stored in the conversation. Put it in the two
> places above and just say "it's set" — the code reads it from there.

## 3. Make a video

### From your laptop

```bash
# Animate a flyer you already have (the usual case)
python code/runway_video.py --image "path/to/flyer.jpg" \
    --prompt "slow push in, confetti drifting, neon sign flickering"

# No flyer — Runway makes the first frame from the prompt, then animates it
python code/runway_video.py --prompt "neon cantina at night, warm pink light"
```

It prints progress, then saves the `.mp4` into `code/` with a timestamped
name (those are gitignored, so nothing lands in the repo by accident).

| Flag | What it does | Default |
|---|---|---|
| `--prompt` | The motion and mood: camera move, what moves, lighting. | — |
| `--image` | Flyer to animate — a local file or a public URL. | none (a first frame is generated) |
| `--shape` | `vertical` (Reels/Stories/TikTok), `square` (feed), `wide` (website). | `vertical` |
| `--duration` | `5` or `10` seconds — what Gen-4 supports. | `5` |
| `--out` | Where to save the file. | `code/runway-<timestamp>.mp4` |

Then post it the usual way:

```bash
python code/facebook_post.py --video "code/runway-20260912-143000.mp4" \
    --caption "Viernes. 9pm. 🔥"
```

### From GitHub (no laptop needed)

**Actions → Runway video → Run workflow.** Fill in the prompt, optionally a
public image URL, pick a shape and duration, run it. When it finishes, the
`.mp4` is attached to the run as an artifact — open the run and download it
from the **Artifacts** box at the bottom.

The artifact is kept 14 days, so download anything worth keeping.

## Writing a prompt that works

Gen-4 animates a still; it does not redraw it. Describe **movement**, not the
picture.

* Good: "slow push in, smoke drifting left to right, string lights flickering"
* Good: "handheld sway, crowd cheering, confetti falling"
* Bad: "a flyer for a drag show on Friday" — that describes the image it
  already has, so nothing moves.

Text in a flyer usually warps once it starts moving. Either keep the motion
small (a slow push in), or animate a photo and put the text on afterwards.

## When something goes wrong

| What you see | What it means |
|---|---|
| `Missing credentials` | `RUNWAY_API_KEY` is not in `.env` (or the workflow secret is missing/misnamed). |
| status 401 | The key is wrong, or was deleted on dev.runwayml.com. Make a new one. |
| status 429 | Out of credits, or too many jobs at once. Top up at dev.runwayml.com → Billing. |
| `Could not reach Runway` | No internet, or a firewall between you and `api.dev.runwayml.com`. |
| Task `FAILED` | Runway's content filter or a bad input image. The message says which. |
| A version error | Runway changed its API version. Bump `API_VERSION` in `code/runway_video.py` to the date shown at docs.dev.runwayml.com. |

## Note for Claude sessions

Claude Code sessions running **in the cloud** (claude.ai/code) cannot reach
`api.dev.runwayml.com` — the egress policy blocks it, so the call fails before
the key is ever used. Generating a video has to happen either on your own
machine or through the GitHub Actions workflow above. Claude can write the
prompts, run the workflow, and handle the posting either way.
