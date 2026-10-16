# Azúcar — real engagement report

_Generated 2026-10-16 10:13 PDT by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **79** published posts with metrics, of 286 marked posted in the queue
- **1818** Instagram posts and **1731** Facebook posts on file
- **29** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 28 | 244 | 4.5% |
| 5-9 posts | 23 | 220 (-10%) | 2.0% |
| 10-19 posts | 19 | 182 (-25%) | 2.1% |
| 20+ posts | 9 | 200 (-18%) | 4.0% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 28 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,052 |
| 19:00 | 1,047 |
| 18:00 | 1,039 |
| 17:00 | 1,027 |
| 16:00 | 1,025 |
| 15:00 | 1,016 |
| 21:00 | 1,008 |
| 14:00 | 996 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 79 | 224 | 2.9% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 79 | 224 | 2.9% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| evening | 40 | 230 | 2.8% |
| morning | 39 | 198 | 3.0% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Friday | 12 | 264 | 2.1% |
| Saturday | 9 | 242 | 4.3% |
| Wednesday | 7 | 231 | 3.1% |
| Monday | 12 | 212 | 2.7% |
| Sunday | 12 | 204 | 3.3% |
| Tuesday | 11 | 202 | 3.9% |
| Thursday | 16 | 192 | 2.5% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_scream_queens_drag_show | 12 | 268 | 3.7% |
| cadence_emo_night_drag_show_edition | 20 | 235 | 3.6% |
| cadence_the_bikini_bottoms | 17 | 228 | 2.9% |
| cadence_mosh_night | 21 | 172 | 2.0% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 720 | 2.2% | instagram | Oct 15, 11:00 | The fog is rolling in and the screams are already real. 🩸💀 |
| 710 | 13.7% | instagram | Sep 08, 19:00 | Dust off the eyeliner and dig out those band tees — Emo Night just got |
| 571 | 1.9% | instagram | Oct 09, 11:00 | Dust off the eyeliner and dig out those band tees — Emo Night just got |
| 567 | 3.9% | instagram | Sep 08, 19:00 | Riot mode: ACTIVATED. 🔥🤘 Revolutionary Riot Productions is turning Azu |
| 504 | 4.6% | instagram | Sep 19, 11:00 | Fog rolls across the Main Floor. Glitter catches the black-light like  |
| 485 | 3.9% | instagram | Sep 25, 11:00 | Here's everything you need to know: Scream Queens Drag Show hits Azuca |
| 456 | 8.8% | instagram | Sep 11, 19:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 403 | 6.2% | instagram | Sep 22, 19:00 | Come as you are, come in costume, come screaming — Azucar's Main Floor |
| 395 | 4.3% | instagram | Oct 11, 11:00 | The mic is haunted. 🎃🎤 Drag-O-Ween Karaoke crashes the Lounge with Bea |
| 360 | 8.3% | instagram | Sep 20, 19:00 | Dust off the eyeliner and dig out those band tees — Emo Night just got |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 92 | 8.7% | instagram | Oct 15, 11:00 | Smoke in the air, bass in your chest, and a stage full of kings servin |
| 116 | 2.6% | instagram | Sep 14, 11:00 | Mark it down: Sunday, October 11 — Mosh Night takes over Azucar's Main |
| 126 | 5.6% | instagram | Sep 20, 11:00 | You feel it before you hear it — floor vibrating, chests thumping, swe |
| 126 | 2.4% | instagram | Oct 15, 19:00 | Scream therapy, Azúcar style. 😱🔪 |
| 127 | 0.8% | instagram | Oct 06, 11:00 | Mark it down: Sunday, October 11 — Mosh Night takes over Azucar's Main |

## Metrics this API version no longer returns

Listed so a missing number is never mistaken for a zero:

- `comments`
- `follows`
- `impressions`
- `likes`
- `plays`
- `post_clicks`
- `post_engaged_users`
- `post_impressions`
- `post_impressions_unique`
- `post_media_view`
- `post_reactions_by_type_total`
- `post_total_media_view_unique`
- `post_video_views`
- `profile_visits`
- `reach`
- `saved`
- `shares`
- `total_interactions`
- `views`

