# How posting works now

Three moving parts. In order of how much they matter:

## 1. The daily cap — `code/cap_queue.py`

**No more than 4 posting slots a day**, across every event on the board. One
slot is one Instagram post plus its Facebook mirror.

This is the backstop, and it is the one rule that cannot be argued with by a
single event. It exists because the scheduler is per-event and per-event rules
multiply: twelve events each behaving reasonably produced 20–36 posts a day.

What it cost us, from `data/insights/ig_media.json` (105 days of real reach):

| Posts that day | Reach per post | Total reach that day |
|---|---:|---:|
| 1–2 | 335 | 572 |
| **3–5** | **288** | **1,268** |
| 6–9 | 179 | 1,996 |
| 10–14 | 148 | 2,071 |
| 15+ | 106 | 2,511 |

1–2 a day is too few — it more than halves the people reached. Past 5 the
total stops moving while every post keeps losing reach. 3–5 is the band.

When a day is over cap, **nearest-to-event wins**, with a marquee getting
three days' head start. Not a strict tier sort: a marquee three weeks out must
never bump tonight's show off the calendar.

Run it by hand any time: `python code/cap_queue.py --dry-run`

## 2. Tiers — the board's Cadence column

Each event's Cadence column picks a **total budget**, written as the days
before the event that each post lands on:

| Tier | Ladder | Posts |
|---|---|---:|
| Marquee | 14, 10, 7, 5, 3, 2, 1, 0 | 8 |
| One-time | 7, 4, 2, 0 | 4 |
| Every week | — | 0 |
| Launch | 3, 1, 0 — every week, for 6 weeks | 3 / week |

Back-loaded on purpose: nobody commits to a Tuesday bar night three weeks out.
The first rung plants the date, the last one converts it. Day-of always posts
in the evening, where the followers-online curve peaks.

**Every-week nights get zero posts of their own** — karaoke, heels class,
industry night. They ride the Monday round-up and stories. That is where the
budget for the marquee shows comes from: karaoke alone had been taking 18 posts
for one night, the heels class 32.

**Launch is for a new weekly night** (Candy Shop was the first). Every week
assumes people already know the night exists; a new one has no habit yet. For
its first 6 weeks, counted from the first date labelled Launch, each night gets
three feed posts — the lineup at 7 PM three days out, the special / deal at
7 PM the day before, "tonight" at 11 AM — then the engine treats it as Every
week on its own. Set Launch on the dates once; nothing has to be switched back.

Launch captions are drafted fresh each week, 3 days out. On the Monday before,
the bot asks in Telegram what's special that week (guest DJ, flavor of the
week); a reply lands in Campaign Notes and feeds the draft. No reply means
general copy for the night.

The old labels still work — Standard and Aggressive map to Marquee, Light to
One-time — so the board can be relabelled whenever, not in lockstep with a
deploy.

### Stories

Every event that isn't Off gets stories, queued by the same daily engine run
for the coming 8 days. The flyer is the story (blurred-fill 1080×1920, made
once per event into `docs/media/stories/`), so there is no caption and nothing
to approve. They post to Instagram and Facebook, and sit **outside the daily
cap** — a different tray, so they don't bury feed posts.

| Tier | Stories |
|---|---|
| Marquee | day before + day of, 11 AM |
| One-time | day of, 11 AM |
| Every week | day of, 11 AM |
| Launch | 2 days before + day before at 11 AM, day of at 3 PM and 7 PM |

Cancelled, Completed or Off events have their pending stories withdrawn on the
next run.

## 3. The Monday round-up — `code/build_week_carousel.py`

One carousel every Monday morning carrying the whole week's flyers, with the
week written out in the caption. Queued by `.github/workflows/week-carousel.yml`
on Mondays at 9am PT for an 11am post.

This is what makes tier 3 possible. It is also the best-performing shape
available: a carousel takes roughly nine times the saves of a single image,
and a what's-on post is exactly the kind of thing people save.

Capped at 10 slides (Meta's limit). Events past the cap, or with no flyer,
still get their line in the caption — a busy week loses a picture, never a
listing.

Preview before it posts: `python code/build_week_carousel.py --dry-run`

**Not built yet:** the summary card Pedro asked for as slide 1 — the week
written out as an image. That needs something to render it; Canva is the
obvious candidate since the account already has it.

## Formats

`process_queue.py` posts whichever the entry carries:

| Entry field | Becomes |
|---|---|
| `image_url` | a photo (both platforms) |
| `image_urls` (list) | IG carousel · FB multi-photo |
| `video_url` | IG Reel · FB Page video |

**Reels are worth three flyers.** Median reach in 2026: Reels 505, photos 175.
Reel output fell to zero in August, which tracks the reach decline about as
closely as the volume increase does. Every event should get one, in its final
week.

⚠️ **Music:** Meta's publishing API has no access to Instagram's licensed
music library — that only exists inside the app. Audio must be baked into the
file, and baked-in commercial music on a business account is what Rights
Manager mutes. Original or licensed audio only, or post that one by hand.
