# Azúcar — real engagement report

_Generated 2026-11-07 10:00 PST by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **20** published posts with metrics, of 100 marked posted in the queue
- **1881** Instagram posts and **8390** Facebook posts on file
- **51** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 6 | 376 | 4.0% |
| 5-9 posts | 8 | 311 (-17%) | 3.2% |
| 10-19 posts | 6 | 230 (-39%) | 1.5% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 6 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,071 |
| 19:00 | 1,067 |
| 18:00 | 1,060 |
| 17:00 | 1,049 |
| 16:00 | 1,044 |
| 15:00 | 1,036 |
| 21:00 | 1,020 |
| 13:00 | 1,018 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 20 | 293 | 3.0% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 20 | 293 | 3.0% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| evening | 8 | 313 | 3.0% |
| morning | 10 | 248 | 2.3% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Thursday | 4 | 422 | 3.2% |
| Monday | 3 | 366 | 4.3% |
| Tuesday | 5 | 331 | 3.2% |
| Saturday | 3 | 295 | 1.7% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_link_up | 5 | 291 | 3.1% |
| cadence_lesbians_playing_uno | 5 | 273 | 2.7% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 1,231 | 6.1% | instagram | Nov 04, 11:00 | New besties are about to happen and y'all aren't ready 👯‍♀️🔥 Azucar is |
| 693 | 8.4% | instagram | Oct 22, 11:00 | Picture this: cards slapping the table, ice clinking in your glass, la |
| 620 | 4.7% | instagram | Oct 20, 19:00 | Picture this: twinkly charms clinking, snacks passed around the table, |
| 593 | 4.0% | instagram | Nov 05, 11:05 | Friday just got a new name to know: FREAKETONAS. 🔥🍑 |
| 385 | 3.6% | instagram | Oct 24, 11:00 | Link up, lock in, make something cute 🧿✨ Azúcar's Main Floor is turnin |
| 368 | 4.3% | instagram | Oct 26, 19:00 | Mark your calendars mi gente, because the Main Floor is about to turn  |
| 366 | 3.0% | instagram | Nov 02, 19:00 | Mark it, underline it, set a reminder 🖤 The Sweet Spot is back and thi |
| 342 | 3.2% | instagram | Oct 27, 17:39 | El show de drag más longevo de Washington regresa con un twist peligro |
| 331 | 2.7% | instagram | Oct 27, 19:00 | Come as you are, cards or no card skills required 🫶🃏 |
| 295 | 1.7% | instagram | Oct 31, 19:00 | Halloween just got a Latinx glow-up. 💀🔥 Noche Latina: Día de los Muert |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 164 | 1.2% | instagram | Nov 06, 11:00 | Low light. Soft music. Doors wide open. 🕯️ That's the mood the second  |
| 165 | 2.4% | instagram | Nov 05, 11:00 | Picture this: cards slapping the table, ice clinking in your glass, la |
| 177 | 2.3% | instagram | Nov 04, 11:00 | Luces rojas, amarillas, verdes — y tú decidiendo cuál te define esta n |
| 212 | 0.9% | instagram | Nov 06, 11:00 | TONIGHT. 🚨 Freaketonas is here. |
| 247 | 0.8% | instagram | Oct 31, 11:00 | Mark it down — Lesbians Playing Uno returns to Azucar this Sunday 🃏 |

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

