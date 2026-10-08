# Azúcar — real engagement report

_Generated 2026-10-08 12:10 PDT by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **55** published posts with metrics, of 156 marked posted in the queue
- **1792** Instagram posts and **1706** Facebook posts on file
- **21** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 26 | 242 | 4.9% |
| 5-9 posts | 19 | 186 (-23%) | 2.7% |
| 10-19 posts | 10 | 212 (-12%) | 2.4% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 26 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,044 |
| 19:00 | 1,038 |
| 18:00 | 1,033 |
| 17:00 | 1,020 |
| 16:00 | 1,016 |
| 15:00 | 1,009 |
| 21:00 | 1,001 |
| 12:00 | 988 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 55 | 218 | 3.8% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 55 | 218 | 3.8% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| evening | 27 | 226 | 3.3% |
| morning | 28 | 202 | 3.8% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Friday | 8 | 274 | 3.6% |
| Saturday | 6 | 239 | 4.4% |
| Monday | 9 | 222 | 3.3% |
| Wednesday | 5 | 220 | 2.6% |
| Sunday | 8 | 200 | 3.4% |
| Tuesday | 8 | 182 | 3.8% |
| Thursday | 11 | 182 | 2.9% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_scream_queens_drag_show | 8 | 263 | 4.1% |
| cadence_the_bikini_bottoms | 12 | 262 | 3.2% |
| cadence_emo_night_drag_show_edition | 17 | 220 | 4.1% |
| cadence_mosh_night | 18 | 167 | 2.6% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 710 | 13.7% | instagram | Sep 08, 19:00 | Dust off the eyeliner and dig out those band tees — Emo Night just got |
| 567 | 3.9% | instagram | Sep 08, 19:00 | Riot mode: ACTIVATED. 🔥🤘 Revolutionary Riot Productions is turning Azu |
| 504 | 4.6% | instagram | Sep 19, 11:00 | Fog rolls across the Main Floor. Glitter catches the black-light like  |
| 481 | 4.0% | instagram | Sep 25, 11:00 | Here's everything you need to know: Scream Queens Drag Show hits Azuca |
| 456 | 8.8% | instagram | Sep 11, 19:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 402 | 6.2% | instagram | Sep 22, 19:00 | Come as you are, come in costume, come screaming — Azucar's Main Floor |
| 360 | 8.3% | instagram | Sep 20, 19:00 | Dust off the eyeliner and dig out those band tees — Emo Night just got |
| 317 | 3.2% | instagram | Oct 02, 11:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 306 | 2.9% | instagram | Oct 01, 19:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 299 | 3.3% | instagram | Sep 26, 19:00 | Dust off the eyeliner and dig out those band tees — Emo Night just got |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 14 | 0.0% | instagram | Oct 08, 11:00 | You feel it before you hear it — floor vibrating, chests thumping, swe |
| 24 | 4.2% | instagram | Oct 08, 11:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 87 | 1.1% | instagram | Oct 06, 11:00 | Mark it down: Sunday, October 11 — Mosh Night takes over Azucar's Main |
| 115 | 2.6% | instagram | Oct 07, 19:00 | Riot mode: ACTIVATED. 🔥🤘 Revolutionary Riot Productions is turning Azu |
| 116 | 2.6% | instagram | Sep 14, 11:00 | Mark it down: Sunday, October 11 — Mosh Night takes over Azucar's Main |

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

