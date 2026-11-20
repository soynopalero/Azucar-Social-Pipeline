# Azúcar — real engagement report

_Generated 2026-11-20 12:59 PST by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **25** published posts with metrics, of 170 marked posted in the queue
- **1907** Instagram posts and **8454** Facebook posts on file
- **64** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 4 | 294 | 2.4% |
| 5-9 posts | 4 | 366 (+24%) | 5.2% |
| 10-19 posts | 17 | 236 (-20%) | 1.5% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 4 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,076 |
| 19:00 | 1,075 |
| 18:00 | 1,070 |
| 17:00 | 1,059 |
| 16:00 | 1,053 |
| 15:00 | 1,045 |
| 14:00 | 1,025 |
| 13:00 | 1,025 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 25 | 256 | 1.9% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 25 | 256 | 1.9% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| morning | 12 | 275 | 1.8% |
| evening | 12 | 242 | 2.1% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Tuesday | 5 | 354 | 3.1% |
| Monday | 6 | 322 | 3.2% |
| Thursday | 3 | 294 | 3.1% |
| Wednesday | 5 | 236 | 1.7% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_bachata_class___social_dance | 6 | 302 | 1.5% |
| cadence_the_sweet_spot | 5 | 236 | 1.3% |
| cadence_vida_amore_divas_show__fiesta_semáforo__stoplight_party | 5 | 207 | 1.7% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 576 | 4.9% | instagram | Nov 18, 11:00 | Low light. Slow hands. The quiet creak of rope pulling taut. 🪢✨ Rope J |
| 517 | 4.8% | instagram | Nov 10, 19:00 | Toons don't play nice on this stage 🎬⚡ Cartoon Chaos is crashing into  |
| 461 | 3.9% | instagram | Nov 10, 19:00 | Lights go low, bass drops, and suddenly you're back in middle school e |
| 409 | 3.4% | instagram | Nov 02, 19:00 | Mark it, underline it, set a reminder 🖤 The Sweet Spot is back and thi |
| 404 | 7.9% | instagram | Nov 12, 11:00 | Whoever had a poster on their wall, a crush on a boy-band member, or a |
| 373 | 4.6% | instagram | Oct 26, 19:00 | Mark your calendars mi gente, because the Main Floor is about to turn  |
| 354 | 3.1% | instagram | Oct 27, 17:39 | El show de drag más longevo de Washington regresa con un twist peligro |
| 328 | 7.0% | instagram | Nov 02, 11:00 | Neon glow, slow bachata beats, sudor en la frente 🌙✨ Picture this: the |
| 316 | 1.9% | instagram | Nov 16, 11:00 | Okay let's keep this simple porque you need these details 📝 Bachata cl |
| 294 | 3.1% | instagram | Nov 19, 11:00 | Save this one — everything you need for Cartoon Chaos at Azucar 📝🎬 Doo |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 130 | 1.5% | instagram | Nov 18, 11:00 | Faltan días para la Fiesta Semáforo y ya sentimos la cuenta regresiva. |
| 140 | 0.0% | instagram | Nov 19, 19:00 | Mark your calendars mi gente, Alicia is pulling up ALL the way from Se |
| 156 | 0.6% | instagram | Nov 17, 11:00 | Feel the sub before you even hear the song 🔊💥 That's the Stuff Your Ba |
| 195 | 1.5% | instagram | Nov 13, 11:00 | El show de drag más longevo de Washington regresa con un twist peligro |
| 195 | 0.0% | instagram | Nov 09, 19:00 | Come as you are, ask what you want, stay as long as you like 💛 The Swe |

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

