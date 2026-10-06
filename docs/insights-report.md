# Azúcar — real engagement report

_Generated 2026-10-06 11:47 PDT by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **52** published posts with metrics, of 146 marked posted in the queue
- **1784** Instagram posts and **1698** Facebook posts on file
- **19** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 27 | 232 | 4.6% |
| 5-9 posts | 11 | 201 (-13%) | 3.8% |
| 10-19 posts | 14 | 216 (-7%) | 2.7% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 27 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,042 |
| 19:00 | 1,035 |
| 18:00 | 1,029 |
| 17:00 | 1,017 |
| 16:00 | 1,013 |
| 15:00 | 1,006 |
| 21:00 | 999 |
| 12:00 | 986 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 52 | 215 | 3.8% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 52 | 215 | 3.8% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| evening | 25 | 232 | 3.9% |
| morning | 27 | 210 | 3.8% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Tuesday | 6 | 294 | 3.8% |
| Friday | 8 | 274 | 3.6% |
| Wednesday | 4 | 254 | 3.7% |
| Saturday | 7 | 250 | 4.4% |
| Monday | 10 | 206 | 3.5% |
| Sunday | 8 | 199 | 3.4% |
| Thursday | 9 | 193 | 3.0% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_the_bikini_bottoms | 11 | 272 | 3.3% |
| cadence_scream_queens_drag_show | 7 | 272 | 4.4% |
| cadence_emo_night_drag_show_edition | 15 | 216 | 4.3% |
| cadence_mosh_night | 16 | 166 | 2.8% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 710 | 13.7% | instagram | Sep 08, 19:00 | Dust off the eyeliner and dig out those band tees — Emo Night just got |
| 567 | 3.9% | instagram | Sep 08, 19:00 | Riot mode: ACTIVATED. 🔥🤘 Revolutionary Riot Productions is turning Azu |
| 504 | 4.6% | instagram | Sep 19, 11:00 | Fog rolls across the Main Floor. Glitter catches the black-light like  |
| 479 | 4.0% | instagram | Sep 25, 11:00 | Here's everything you need to know: Scream Queens Drag Show hits Azuca |
| 471 | 3.8% | instagram | Sep 26, 11:00 | The dark is casting. 🖤⚡ |
| 456 | 8.8% | instagram | Sep 11, 19:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 402 | 6.2% | instagram | Sep 22, 19:00 | Come as you are, come in costume, come screaming — Azucar's Main Floor |
| 360 | 8.3% | instagram | Sep 20, 19:00 | Dust off the eyeliner and dig out those band tees — Emo Night just got |
| 314 | 3.2% | instagram | Sep 30, 11:00 | The dark is casting. 🖤⚡ |
| 305 | 3.3% | instagram | Oct 02, 11:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 16 | 0.0% | instagram | Oct 06, 11:00 | Mark it down: Sunday, October 11 — Mosh Night takes over Azucar's Main |
| 116 | 2.6% | instagram | Sep 14, 11:00 | Mark it down: Sunday, October 11 — Mosh Night takes over Azucar's Main |
| 119 | 6.7% | instagram | Oct 05, 19:00 | No dress code for chaos. 🤘🖤 Doesn't matter if you're scene, punk, meta |
| 124 | 1.6% | instagram | Oct 04, 11:00 | You feel it before you hear it — floor vibrating, chests thumping, swe |
| 126 | 5.6% | instagram | Sep 20, 11:00 | You feel it before you hear it — floor vibrating, chests thumping, swe |

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

