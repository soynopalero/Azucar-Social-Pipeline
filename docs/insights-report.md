# Azúcar — real engagement report

_Generated 2026-11-09 14:54 PST by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **18** published posts with metrics, of 92 marked posted in the queue
- **1886** Instagram posts and **8400** Facebook posts on file
- **53** daily account snapshots

> ⚠️ **Thin data.** Under 20 matched posts, treat every table below as a direction to check, not a conclusion. The daily snapshots need a few weeks to become useful.

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 6 | 344 | 3.9% |
| 5-9 posts | 6 | 300 (-13%) | 3.2% |
| 10-19 posts | 6 | 276 (-20%) | 2.3% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 6 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,072 |
| 19:00 | 1,067 |
| 18:00 | 1,061 |
| 17:00 | 1,050 |
| 16:00 | 1,045 |
| 15:00 | 1,037 |
| 21:00 | 1,021 |
| 13:00 | 1,019 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 18 | 300 | 3.0% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 18 | 300 | 3.0% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| evening | 7 | 340 | 2.9% |
| morning | 9 | 256 | 2.5% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Thursday | 3 | 675 | 4.1% |
| Tuesday | 3 | 340 | 3.2% |
| Monday | 4 | 334 | 4.9% |
| Saturday | 3 | 296 | 2.7% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_lesbians_playing_uno | 6 | 282 | 2.6% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 1,470 | 6.1% | instagram | Nov 04, 11:00 | New besties are about to happen and y'all aren't ready 👯‍♀️🔥 Azucar is |
| 693 | 8.4% | instagram | Oct 22, 11:00 | Picture this: cards slapping the table, ice clinking in your glass, la |
| 675 | 4.1% | instagram | Nov 05, 11:05 | Friday just got a new name to know: FREAKETONAS. 🔥🍑 |
| 429 | 5.8% | instagram | Nov 07, 19:00 | Board games just got a Latinx glow-up 🎲🔥 Gay's N Gameboards is pulling |
| 384 | 2.9% | instagram | Nov 02, 19:00 | Mark it, underline it, set a reminder 🖤 The Sweet Spot is back and thi |
| 371 | 4.6% | instagram | Oct 26, 19:00 | Mark your calendars mi gente, because the Main Floor is about to turn  |
| 348 | 3.2% | instagram | Oct 27, 17:39 | El show de drag más longevo de Washington regresa con un twist peligro |
| 340 | 2.6% | instagram | Oct 27, 19:00 | Come as you are, cards or no card skills required 🫶🃏 |
| 305 | 3.6% | instagram | Nov 03, 19:00 | Pull up your chair, shuffle the deck, and get ready — Lesbians Playing |
| 296 | 7.8% | instagram | Nov 02, 11:00 | Neon glow, slow bachata beats, sudor en la frente 🌙✨ Picture this: the |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 77 | 5.2% | instagram | Nov 09, 11:00 | Picture it: dice clacking, dominoes slapping down hard, laughter bounc |
| 199 | 2.5% | instagram | Nov 05, 11:00 | Picture this: cards slapping the table, ice clinking in your glass, la |
| 203 | 2.0% | instagram | Nov 04, 11:00 | Luces rojas, amarillas, verdes — y tú decidiendo cuál te define esta n |
| 228 | 2.2% | instagram | Nov 08, 19:00 | Come as you are, cards or no card skills required 🫶🃏 |
| 228 | 1.3% | instagram | Nov 06, 11:00 | Low light. Soft music. Doors wide open. 🕯️ That's the mood the second  |

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

