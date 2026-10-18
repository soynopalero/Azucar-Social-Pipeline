# Azúcar — real engagement report

_Generated 2026-10-18 09:26 PDT by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **64** published posts with metrics, of 250 marked posted in the queue
- **1826** Instagram posts and **1737** Facebook posts on file
- **31** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 29 | 228 | 3.5% |
| 5-9 posts | 12 | 188 (-18%) | 1.4% |
| 10-19 posts | 14 | 179 (-21%) | 2.0% |
| 20+ posts | 9 | 253 (+11%) | 3.6% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 29 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,054 |
| 19:00 | 1,049 |
| 18:00 | 1,040 |
| 17:00 | 1,029 |
| 16:00 | 1,026 |
| 15:00 | 1,017 |
| 21:00 | 1,009 |
| 14:00 | 998 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 64 | 198 | 2.7% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 64 | 198 | 2.7% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| evening | 34 | 228 | 2.7% |
| morning | 30 | 186 | 2.7% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Tuesday | 8 | 268 | 3.8% |
| Friday | 13 | 244 | 2.3% |
| Wednesday | 4 | 206 | 2.5% |
| Monday | 11 | 199 | 2.8% |
| Saturday | 7 | 191 | 2.4% |
| Thursday | 13 | 182 | 2.5% |
| Sunday | 8 | 174 | 2.4% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_drag_o_weeen | 4 | 310 | 4.7% |
| cadence_scream_queens_drag_show | 12 | 270 | 3.7% |
| cadence_the_bikini_bottoms | 19 | 228 | 2.9% |
| cadence_mosh_night | 21 | 178 | 2.0% |
| cadence_mentivads_allstars___after_party | 4 | 163 | 1.2% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 931 | 2.4% | instagram | Oct 15, 11:00 | The fog is rolling in and the screams are already real. 🩸💀 |
| 567 | 3.9% | instagram | Sep 08, 19:00 | Riot mode: ACTIVATED. 🔥🤘 Revolutionary Riot Productions is turning Azu |
| 504 | 4.6% | instagram | Sep 19, 11:00 | Fog rolls across the Main Floor. Glitter catches the black-light like  |
| 485 | 3.9% | instagram | Sep 25, 11:00 | Here's everything you need to know: Scream Queens Drag Show hits Azuca |
| 456 | 8.8% | instagram | Sep 11, 19:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 403 | 6.2% | instagram | Sep 22, 19:00 | Come as you are, come in costume, come screaming — Azucar's Main Floor |
| 398 | 4.3% | instagram | Oct 11, 11:00 | The mic is haunted. 🎃🎤 Drag-O-Ween Karaoke crashes the Lounge with Bea |
| 366 | 6.0% | instagram | Oct 11, 11:00 | Round two of spooky season just landed. 🎃🎤 Drag-O-Ween Karaoke is back |
| 341 | 2.9% | instagram | Oct 02, 11:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 330 | 2.7% | instagram | Oct 01, 19:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 116 | 2.6% | instagram | Sep 14, 11:00 | Mark it down: Sunday, October 11 — Mosh Night takes over Azucar's Main |
| 119 | 1.7% | instagram | Oct 17, 19:00 | Anota esto antes de que se te olvide 📝🔥 |
| 126 | 5.6% | instagram | Sep 20, 11:00 | You feel it before you hear it — floor vibrating, chests thumping, swe |
| 128 | 0.8% | instagram | Oct 17, 19:00 | The screams come back one last time. 😱🔪 |
| 131 | 0.8% | instagram | Oct 06, 11:00 | Mark it down: Sunday, October 11 — Mosh Night takes over Azucar's Main |

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

