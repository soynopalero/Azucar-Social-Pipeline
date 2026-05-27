---
name: post-flyers-on-social-media
description: Post or schedule event flyers (photos and videos) to the Out And About Facebook Page and @cluboutandabout Instagram account using the Meta Graph API. Use whenever the user asks to "post to Facebook", "post to Instagram", "schedule a post", "post a flyer", "post this picture", "promote this event", or shares an event image/video and wants it published or scheduled. Handles single posts, scheduled posts, multi-post campaigns, photo recycling, and Spanish-language caption generation in the Azúcar brand voice (fun, gay, Latino).
---

# Post Flyers on Social Media

This skill posts and schedules event content for **Azúcar at Out & About** (a 21+ Latino/queer nightclub in Pasco, WA) to Facebook and Instagram via the Meta Graph API.

## When to use this skill

Use whenever the user:
- Shares a flyer/image/video and asks to "post it"
- Says "post on Facebook" or "post on Instagram"
- Says "schedule a post for [date]"
- Asks to "create a campaign" or "promote this event"
- Provides caption text and a picture name
- Asks you to "write a caption" or "make a description" for an event flyer

## Project location

All scripts and assets live under:
```
C:\Users\Pedro.AzureAD\Documents\Azucar-Projects\07-API & MCP Connections\07 — API & MCP Connections\
```

Key files:
- `code/facebook_post.py` — handles photos, videos, and scheduled posts to Facebook
- `code/instagram_post.py` — posts photos to Instagram (via Imgur intermediate upload)
- `code/.env` — contains `FB_PAGE_ID`, `IG_USER_ID`, and `FB_PAGE_ACCESS_TOKEN` (permanent token)

## Required credentials (in `code/.env`)

```
FB_PAGE_ID=201644454280
IG_USER_ID=17841406112085472
FB_PAGE_ACCESS_TOKEN=<permanent page access token>
```

The token in `.env` is a **never-expiring Page Access Token** (already exchanged from a long-lived user token). Do NOT replace it with short-lived user tokens.

## Python environment

Python is installed at:
```
C:\Users\Pedro.AzureAD\AppData\Local\Programs\Python\Python314\python.exe
```

In Bash, invoke as:
```
/c/Users/Pedro.AzureAD/AppData/Local/Programs/Python/Python314/python.exe
```

**IMPORTANT:** Always set `PYTHONIOENCODING=utf-8` before running — captions contain emojis and Spanish accents that crash on Windows' default cp1252 encoding.

## How to post to Facebook

### Post a photo immediately

```bash
cd "C:\Users\Pedro.AzureAD\Documents\Azucar-Projects\07-API & MCP Connections\07 — API & MCP Connections" && \
PYTHONIOENCODING=utf-8 \
/c/Users/Pedro.AzureAD/AppData/Local/Programs/Python/Python314/python.exe \
code/facebook_post.py \
--image "path/to/image.jpg" \
--caption "Your caption with 🎉 emojis and ñ"
```

### Post a video immediately

```bash
... code/facebook_post.py --video "path/to/video.mp4" --caption "..."
```

### Schedule a post for the future

Add `--schedule <unix_timestamp>`. Facebook requires the time to be at least **10 minutes in the future** and within **30 days**.

```bash
... code/facebook_post.py --image "flyer.jpg" --schedule 1778950800 --caption "..."
```

### Computing Unix timestamps

The site timezone is **America/Los_Angeles (PDT/PST)**. Convert PDT → UTC by adding 7 hours (PST → UTC by adding 8 hours), then:

```bash
date -d "2026-05-16 17:00:00 UTC" +%s
# 1778950800
```

That command in Bash gives the timestamp for **10:00 AM PDT on May 16, 2026** (10:00 PDT = 17:00 UTC).

Suggested posting times:
- Weekday hype posts → **6:00 PM PDT** (after work, peak scroll)
- Sunday / show-day morning → **10:00 AM PDT**

## How to post to Instagram

```bash
... code/instagram_post.py --image "path/to/image.jpg" --caption "..."
```

The Instagram script uploads the image to Imgur first (anonymous, no account needed) to get a public URL, then asks Instagram to fetch it via the Graph API. Two-step process: create media container → publish container.

Note: Instagram requires `instagram_basic` and `instagram_content_publish` permissions on the access token.

## Captions: brand voice rules

When writing captions for Azúcar / Out & About:

1. **Always Spanish** (unless the user explicitly asks for English).
2. **Fun, gay, Latino energy** — drag queens, joteria, chusma, comadres, brillo, picante.
3. **Emoji-rich** — 🌈🔥💃👑✨🎤💋🌶️🏳️‍🌈 are core. Use generously but not randomly.
4. **Bilingual flair** when natural — "te queremos ver", "tu mesa gratis", "última llamada".
5. **Include event essentials at the bottom**:
   - 🗓️ Date and time
   - 📍 Azúcar at Out & About — 327 W Lewis St, Pasco WA
   - 🔞 21+ | 💵 $20 cover (or whatever the cover is)
   - 🎟️ Mesa gratis: @VidaAmore / @AlyanaAmore / @VidaAmoreDivasShow
6. **Hashtags**: pick 4–7 from `#VADS #AzucarPasco #DragShow #TriCities #LatinoLGBTQ #Pasco` plus performer-specific tags like `#VidaAmore`, `#VictoriaAmore`, `#LaBebotaAmore`, `#AlyanaAmore`.
7. **Each performer has a different "angle"** when writing spotlight posts:
   - **Vida Amore** → fundadora, la mamá del show, leyenda viva, 25 años
   - **Victoria Amore** → elegancia, reina, glamour, respeto
   - **Alyana Amore** → energía pura, peace signs, "vamos a romper la pista"
   - **LaBebota Amore** → sassy, atrevida, "no pide permiso"
   - **Frívola** / **Kendra Amore** / guest performers → match their flyer vibe
8. **Escape `$` as `\$`** in shell commands (bash will try to expand variables otherwise).

## Multi-post campaigns

When the user asks for a campaign (e.g., "promote this event over the next 2 weeks"):

1. **Inventory available flyers** — list every unique image in the event folder.
2. **Propose a calendar table** (date, time, image, theme, recycled?). Get approval before scheduling.
3. **Recycle wisely** — for countdown days (mañana, este sábado, ES HOY), reuse the strongest images (full cast and crew shots are best for "hype" posts).
4. **Build narrative momentum**: Save-the-date → cast announce → spotlights → countdown → mañana → ES HOY.
5. **Default cadence**: kickoff today, then 2–3 posts the week before, then daily countdown the week of.

## App configuration (one-time setup, already done)

- App name: **Azucar Posters** (App ID: `1282707894009655`)
- App secret: stored separately, used only for token exchange
- App is **published / Live** (not in development mode) — public can see all posts
- Required for Live mode: privacy policy URL, app icon (1024x1024), category
- Privacy policy URL: `https://www.cluboutandabout.com/privacy-policy`

If the access token ever expires (it shouldn't, but if Meta invalidates it), regenerate:

1. Get a fresh **User Access Token** from the [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Run this Python snippet to exchange it for a permanent Page token:

```python
import requests
app_id = "1282707894009655"
app_secret = "<APP_SECRET>"
short_token = "<FRESH_USER_TOKEN>"

# Exchange for long-lived user token
r = requests.get(
    f"https://graph.facebook.com/v19.0/oauth/access_token"
    f"?grant_type=fb_exchange_token&client_id={app_id}"
    f"&client_secret={app_secret}&fb_exchange_token={short_token}"
)
long_user_token = r.json()["access_token"]

# Get permanent Page Access Token
r2 = requests.get(
    f"https://graph.facebook.com/v19.0/me/accounts?access_token={long_user_token}"
)
for page in r2.json()["data"]:
    if page["id"] == "201644454280":
        print(page["access_token"])  # This token never expires
```

Update `code/.env` with the new permanent token.

## Common errors and fixes

| Error | Fix |
|-------|-----|
| `'charmap' codec can't encode character` | Add `PYTHONIOENCODING=utf-8` to the command |
| `Session has expired` | Refresh the token (see above) |
| `Unpublished posts must be posted to a page as the page itself` | You're using a User token, not a Page token. Exchange it. |
| `(#200) Application does not have permission` | Token missing required permissions — regenerate with `pages_manage_posts`, `pages_read_engagement`, `instagram_basic`, `instagram_content_publish` |
| `Please reduce the amount of data you're asking for` | Transient rate-limit. Wait a few seconds and retry. |
| Post visible to admin but not public | App is in Development Mode — publish the Meta app |
| `scheduled_publish_time` rejected | Must be 10 min – 30 days in future; verify timestamp is correct |

## Workflow with the user

When the user shares an image + caption and asks to post:

1. **Confirm**: which platform (Facebook, Instagram, or both)? Post now or schedule?
2. **Locate the image**: use `Glob` to find it if they gave a partial name. If pasted in chat with no file saved, ask them to save it to the project root with a clear filename.
3. **Run the script** with proper `PYTHONIOENCODING=utf-8` prefix.
4. **Report back** with the post URL so they can verify.
5. **For schedules**, compute the UTC timestamp from PDT correctly (add 7 hours).

When the user asks you to **write captions** for performer flyers:
1. Use the `Read` tool to view each image directly — describe what the performer is wearing/doing.
2. Draft a caption matching that performer's "angle" (see brand voice list above).
3. Present all caption drafts in a single response for approval, then schedule once approved.

## Quick reference: full Facebook post command template

```bash
cd "C:\Users\Pedro.AzureAD\Documents\Azucar-Projects\07-API & MCP Connections\07 — API & MCP Connections" && \
PYTHONIOENCODING=utf-8 \
FB_PAGE_ACCESS_TOKEN=<TOKEN_IF_OVERRIDING> \
FB_PAGE_ID=201644454280 \
/c/Users/Pedro.AzureAD/AppData/Local/Programs/Python/Python314/python.exe \
code/facebook_post.py \
--image "FOLDER/file.jpg" \
[--schedule UNIX_TIMESTAMP] \
--caption "Caption with emojis 🌈 and \$escaped dollar signs"
```
