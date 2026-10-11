# Azúcar — real engagement report

_Generated 2026-10-11 10:57 PDT by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **64** published posts with metrics, of 186 marked posted in the queue
- **1802** Instagram posts and **1716** Facebook posts on file
- **24** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 28 | 236 | 4.5% |
| 5-9 posts | 23 | 217 (-8%) | 2.1% |
| 10-19 posts | 13 | 167 (-29%) | 2.4% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 28 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,047 |
| 19:00 | 1,042 |
| 18:00 | 1,036 |
| 17:00 | 1,023 |
| 16:00 | 1,021 |
| 15:00 | 1,012 |
| 21:00 | 1,004 |
| 12:00 | 990 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 64 | 218 | 3.0% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 64 | 218 | 3.0% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| evening | 32 | 231 | 3.1% |
| morning | 31 | 197 | 3.0% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Friday | 12 | 264 | 2.4% |
| Monday | 9 | 232 | 3.1% |
| Wednesday | 5 | 231 | 2.1% |
| Tuesday | 8 | 220 | 3.8% |
| Sunday | 8 | 203 | 3.4% |
| Saturday | 9 | 186 | 4.5% |
| Thursday | 13 | 182 | 2.5% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_scream_queens_drag_show | 9 | 267 | 4.5% |
| cadence_the_bikini_bottoms | 13 | 259 | 3.0% |
| cadence_emo_night_drag_show_edition | 20 | 228 | 3.8% |
| cadence_mosh_night | 20 | 168 | 2.2% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 710 | 13.7% | instagram | Sep 08, 19:00 | Dust off the eyeliner and dig out those band tees — Emo Night just got |
| 567 | 3.9% | instagram | Sep 08, 19:00 | Riot mode: ACTIVATED. 🔥🤘 Revolutionary Riot Productions is turning Azu |
| 504 | 4.6% | instagram | Sep 19, 11:00 | Fog rolls across the Main Floor. Glitter catches the black-light like  |
| 484 | 3.9% | instagram | Sep 25, 11:00 | Here's everything you need to know: Scream Queens Drag Show hits Azuca |
| 469 | 2.3% | instagram | Oct 09, 11:00 | Dust off the eyeliner and dig out those band tees — Emo Night just got |
| 456 | 8.8% | instagram | Sep 11, 19:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 402 | 6.2% | instagram | Sep 22, 19:00 | Come as you are, come in costume, come screaming — Azucar's Main Floor |
| 360 | 8.3% | instagram | Sep 20, 19:00 | Dust off the eyeliner and dig out those band tees — Emo Night just got |
| 331 | 3.0% | instagram | Oct 02, 11:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 317 | 2.8% | instagram | Oct 01, 19:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 111 | 0.9% | instagram | Oct 06, 11:00 | Mark it down: Sunday, October 11 — Mosh Night takes over Azucar's Main |
| 116 | 2.6% | instagram | Sep 14, 11:00 | Mark it down: Sunday, October 11 — Mosh Night takes over Azucar's Main |
| 124 | 1.6% | instagram | Oct 10, 11:00 | Mark it down: Sunday, October 11 — Mosh Night takes over Azucar's Main |
| 126 | 5.6% | instagram | Sep 20, 11:00 | You feel it before you hear it — floor vibrating, chests thumping, swe |
| 126 | 2.4% | instagram | Oct 09, 19:00 | No dress code for chaos. 🤘🖤 Doesn't matter if you're scene, punk, meta |

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

