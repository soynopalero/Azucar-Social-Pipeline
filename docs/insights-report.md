# Azúcar — real engagement report

_Generated 2026-10-10 10:39 PDT by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **61** published posts with metrics, of 168 marked posted in the queue
- **1799** Instagram posts and **1713** Facebook posts on file
- **23** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 28 | 234 | 4.5% |
| 5-9 posts | 23 | 216 (-8%) | 2.2% |
| 10-19 posts | 10 | 148 (-37%) | 2.1% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 28 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,046 |
| 19:00 | 1,042 |
| 18:00 | 1,035 |
| 17:00 | 1,022 |
| 16:00 | 1,019 |
| 15:00 | 1,010 |
| 21:00 | 1,003 |
| 12:00 | 988 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 61 | 217 | 3.1% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 61 | 217 | 3.1% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| evening | 30 | 232 | 3.1% |
| morning | 30 | 194 | 3.3% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Saturday | 6 | 246 | 4.6% |
| Friday | 12 | 242 | 3.1% |
| Monday | 9 | 232 | 3.1% |
| Wednesday | 5 | 230 | 2.2% |
| Tuesday | 8 | 214 | 3.8% |
| Sunday | 8 | 202 | 3.4% |
| Thursday | 13 | 182 | 2.2% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_scream_queens_drag_show | 8 | 266 | 4.6% |
| cadence_the_bikini_bottoms | 13 | 258 | 3.0% |
| cadence_emo_night_drag_show_edition | 19 | 224 | 3.9% |
| cadence_mosh_night | 19 | 172 | 2.6% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 710 | 13.7% | instagram | Sep 08, 19:00 | Dust off the eyeliner and dig out those band tees — Emo Night just got |
| 567 | 3.9% | instagram | Sep 08, 19:00 | Riot mode: ACTIVATED. 🔥🤘 Revolutionary Riot Productions is turning Azu |
| 504 | 4.6% | instagram | Sep 19, 11:00 | Fog rolls across the Main Floor. Glitter catches the black-light like  |
| 484 | 3.9% | instagram | Sep 25, 11:00 | Here's everything you need to know: Scream Queens Drag Show hits Azuca |
| 456 | 8.8% | instagram | Sep 11, 19:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 402 | 6.2% | instagram | Sep 22, 19:00 | Come as you are, come in costume, come screaming — Azucar's Main Floor |
| 360 | 8.3% | instagram | Sep 20, 19:00 | Dust off the eyeliner and dig out those band tees — Emo Night just got |
| 328 | 3.0% | instagram | Oct 02, 11:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 313 | 2.9% | instagram | Oct 01, 19:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 303 | 3.3% | instagram | Sep 26, 19:00 | Dust off the eyeliner and dig out those band tees — Emo Night just got |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 98 | 3.1% | instagram | Oct 09, 19:00 | No dress code for chaos. 🤘🖤 Doesn't matter if you're scene, punk, meta |
| 100 | 1.0% | instagram | Oct 09, 11:00 | ¡POR FIN! 💋🔥 Lo que todos estaban pidiendo ya tiene fecha. |
| 104 | 1.0% | instagram | Oct 06, 11:00 | Mark it down: Sunday, October 11 — Mosh Night takes over Azucar's Main |
| 115 | 0.9% | instagram | Oct 08, 11:00 | You feel it before you hear it — floor vibrating, chests thumping, swe |
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

