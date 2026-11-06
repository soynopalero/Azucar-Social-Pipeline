# Azúcar — real engagement report

_Generated 2026-11-06 11:55 PST by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **18** published posts with metrics, of 92 marked posted in the queue
- **1879** Instagram posts and **8383** Facebook posts on file
- **50** daily account snapshots

> ⚠️ **Thin data.** Under 20 matched posts, treat every table below as a direction to check, not a conclusion. The daily snapshots need a few weeks to become useful.

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 5 | 384 | 4.4% |
| 5-9 posts | 9 | 287 (-25%) | 3.1% |
| 10-19 posts | 4 | 264 (-31%) | 2.1% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 5 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,071 |
| 19:00 | 1,066 |
| 18:00 | 1,059 |
| 17:00 | 1,048 |
| 16:00 | 1,043 |
| 15:00 | 1,035 |
| 21:00 | 1,020 |
| 13:00 | 1,017 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 18 | 310 | 3.2% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 18 | 310 | 3.2% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| evening | 8 | 310 | 3.1% |
| morning | 8 | 258 | 3.3% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Thursday | 4 | 367 | 3.6% |
| Monday | 3 | 360 | 4.4% |
| Tuesday | 5 | 330 | 3.3% |
| Saturday | 3 | 291 | 1.7% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_link_up | 5 | 287 | 3.1% |
| cadence_lesbians_playing_uno | 5 | 260 | 3.0% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 1,136 | 6.1% | instagram | Nov 04, 11:00 | New besties are about to happen and y'all aren't ready 👯‍♀️🔥 Azucar is |
| 692 | 8.4% | instagram | Oct 22, 11:00 | Picture this: cards slapping the table, ice clinking in your glass, la |
| 620 | 4.7% | instagram | Oct 20, 19:00 | Picture this: twinkly charms clinking, snacks passed around the table, |
| 485 | 4.1% | instagram | Nov 05, 11:05 | Friday just got a new name to know: FREAKETONAS. 🔥🍑 |
| 384 | 3.6% | instagram | Oct 24, 11:00 | Link up, lock in, make something cute 🧿✨ Azúcar's Main Floor is turnin |
| 366 | 4.4% | instagram | Oct 26, 19:00 | Mark your calendars mi gente, because the Main Floor is about to turn  |
| 360 | 3.1% | instagram | Nov 02, 19:00 | Mark it, underline it, set a reminder 🖤 The Sweet Spot is back and thi |
| 335 | 3.3% | instagram | Oct 27, 17:39 | El show de drag más longevo de Washington regresa con un twist peligro |
| 330 | 2.7% | instagram | Oct 27, 19:00 | Come as you are, cards or no card skills required 🫶🃏 |
| 291 | 1.7% | instagram | Oct 31, 19:00 | Halloween just got a Latinx glow-up. 💀🔥 Noche Latina: Día de los Muert |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 132 | 3.0% | instagram | Nov 05, 11:00 | Picture this: cards slapping the table, ice clinking in your glass, la |
| 165 | 2.4% | instagram | Nov 04, 11:00 | Luces rojas, amarillas, verdes — y tú decidiendo cuál te define esta n |
| 238 | 0.8% | instagram | Oct 31, 11:00 | Mark it down — Lesbians Playing Uno returns to Azucar this Sunday 🃏 |
| 240 | 2.1% | instagram | Nov 01, 19:00 | Picture this: twinkly charms clinking, snacks passed around the table, |
| 249 | 1.6% | instagram | Oct 29, 11:00 | Link up, lock in, make something cute 🧿✨ Azúcar's Main Floor is turnin |

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

