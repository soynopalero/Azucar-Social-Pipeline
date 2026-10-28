# Azúcar — real engagement report

_Generated 2026-10-28 11:43 PDT by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **61** published posts with metrics, of 236 marked posted in the queue
- **1863** Instagram posts and **5712** Facebook posts on file
- **41** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 24 | 266 | 2.9% |
| 5-9 posts | 15 | 263 (-1%) | 2.5% |
| 10-19 posts | 17 | 240 (-10%) | 3.1% |
| 20+ posts | 5 | 269 (+1%) | 3.4% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 24 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,063 |
| 19:00 | 1,056 |
| 18:00 | 1,049 |
| 17:00 | 1,038 |
| 16:00 | 1,035 |
| 15:00 | 1,026 |
| 21:00 | 1,012 |
| 14:00 | 1,007 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 61 | 256 | 2.9% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 61 | 256 | 2.9% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| evening | 31 | 259 | 2.7% |
| morning | 29 | 241 | 3.0% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Thursday | 10 | 286 | 2.6% |
| Saturday | 7 | 280 | 3.4% |
| Friday | 11 | 272 | 2.9% |
| Sunday | 7 | 246 | 1.9% |
| Monday | 11 | 228 | 2.8% |
| Tuesday | 13 | 214 | 3.4% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_scream_queens_drag_show | 14 | 272 | 3.7% |
| cadence_drag_o_weeen | 5 | 268 | 6.0% |
| cadence_the_bikini_bottoms | 24 | 221 | 2.4% |
| cadence_american_horror_story_watch_party | 4 | 179 | 1.3% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 958 | 2.4% | instagram | Oct 15, 11:00 | The fog is rolling in and the screams are already real. 🩸💀 |
| 630 | 8.3% | instagram | Oct 22, 11:00 | Picture this: cards slapping the table, ice clinking in your glass, la |
| 604 | 4.8% | instagram | Oct 20, 19:00 | Picture this: twinkly charms clinking, snacks passed around the table, |
| 587 | 3.4% | instagram | Oct 20, 19:00 | Mark it down mi gente — Frankie is taking over the Main Floor and she' |
| 504 | 4.6% | instagram | Sep 19, 11:00 | Fog rolls across the Main Floor. Glitter catches the black-light like  |
| 485 | 3.9% | instagram | Sep 25, 11:00 | Here's everything you need to know: Scream Queens Drag Show hits Azuca |
| 469 | 3.6% | instagram | Oct 22, 11:00 | Brushes out, pumpkins ready — Sunday's about to get messy and magical. |
| 464 | 3.4% | instagram | Oct 17, 19:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 456 | 8.8% | instagram | Sep 11, 19:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 443 | 6.8% | instagram | Oct 19, 11:00 | Grab your prop bag — the castle is open. 🩸👠 |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 113 | 1.8% | instagram | Oct 26, 11:00 | Dim lights. Cold drinks. A room that gasps in unison. 🕯️🔪 |
| 125 | 0.8% | instagram | Oct 20, 11:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 159 | 1.9% | instagram | Oct 18, 11:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 159 | 3.1% | instagram | Oct 27, 19:00 | Picture this: twinkly charms clinking, snacks passed around the table, |
| 160 | 1.2% | instagram | Oct 22, 11:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |

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

