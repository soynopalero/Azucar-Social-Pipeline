# Azúcar — real engagement report

_Generated 2026-10-24 09:34 PDT by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **57** published posts with metrics, of 226 marked posted in the queue
- **1849** Instagram posts and **5696** Facebook posts on file
- **37** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 21 | 272 | 3.0% |
| 5-9 posts | 11 | 192 (-29%) | 2.3% |
| 10-19 posts | 20 | 206 (-24%) | 2.7% |
| 20+ posts | 5 | 248 (-9%) | 3.8% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 21 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,060 |
| 19:00 | 1,054 |
| 18:00 | 1,045 |
| 17:00 | 1,035 |
| 16:00 | 1,032 |
| 15:00 | 1,022 |
| 21:00 | 1,011 |
| 14:00 | 1,002 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 57 | 244 | 2.8% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 57 | 244 | 2.8% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| evening | 28 | 258 | 2.8% |
| morning | 29 | 209 | 2.9% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Tuesday | 11 | 272 | 3.8% |
| Saturday | 6 | 270 | 2.9% |
| Friday | 12 | 251 | 2.9% |
| Thursday | 11 | 233 | 2.7% |
| Monday | 9 | 228 | 2.8% |
| Wednesday | 3 | 182 | 1.5% |
| Sunday | 5 | 180 | 2.0% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_scream_queens_drag_show | 14 | 272 | 3.7% |
| cadence_drag_o_weeen | 4 | 207 | 4.4% |
| cadence_the_bikini_bottoms | 24 | 206 | 2.4% |
| cadence_mentivads_allstars___after_party | 4 | 176 | 0.9% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 948 | 2.4% | instagram | Oct 15, 11:00 | The fog is rolling in and the screams are already real. 🩸💀 |
| 553 | 4.3% | instagram | Oct 20, 19:00 | Picture this: twinkly charms clinking, snacks passed around the table, |
| 527 | 3.8% | instagram | Oct 20, 19:00 | Mark it down mi gente — Frankie is taking over the Main Floor and she' |
| 504 | 4.6% | instagram | Sep 19, 11:00 | Fog rolls across the Main Floor. Glitter catches the black-light like  |
| 485 | 3.9% | instagram | Sep 25, 11:00 | Here's everything you need to know: Scream Queens Drag Show hits Azuca |
| 484 | 6.2% | instagram | Oct 22, 11:00 | Picture this: cards slapping the table, ice clinking in your glass, la |
| 456 | 8.8% | instagram | Sep 11, 19:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 453 | 3.5% | instagram | Oct 17, 19:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 441 | 3.6% | instagram | Oct 22, 11:00 | Brushes out, pumpkins ready — Sunday's about to get messy and magical. |
| 403 | 6.2% | instagram | Sep 22, 19:00 | Come as you are, come in costume, come screaming — Azucar's Main Floor |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 114 | 0.9% | instagram | Oct 20, 11:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 128 | 1.6% | instagram | Oct 22, 11:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 144 | 0.7% | instagram | Oct 21, 11:00 | Dim lights. Cold drinks. A room that gasps in unison. 🕯️🔪 |
| 152 | 2.0% | instagram | Oct 18, 11:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 153 | 7.8% | instagram | Oct 23, 19:00 | Mark it down: Drag-O-Ween Karaoke hits the Main Floor on Wednesday, Oc |

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

