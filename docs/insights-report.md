# Azúcar — real engagement report

_Generated 2026-11-23 16:38 PST by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **22** published posts with metrics, of 170 marked posted in the queue
- **1912** Instagram posts and **8469** Facebook posts on file
- **67** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 4 | 341 | 3.8% |
| 5-9 posts | 5 | 264 (-23%) | 1.2% |
| 10-19 posts | 13 | 220 (-35%) | 1.8% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 4 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,077 |
| 19:00 | 1,076 |
| 18:00 | 1,072 |
| 17:00 | 1,060 |
| 16:00 | 1,054 |
| 15:00 | 1,046 |
| 14:00 | 1,027 |
| 13:00 | 1,027 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 22 | 257 | 1.7% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 22 | 257 | 1.7% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| morning | 9 | 296 | 1.7% |
| evening | 12 | 237 | 1.9% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Monday | 4 | 333 | 3.6% |
| Tuesday | 4 | 322 | 2.2% |
| Wednesday | 4 | 268 | 1.4% |
| Saturday | 3 | 264 | 1.5% |
| Sunday | 3 | 220 | 1.2% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_cartoon_chaos_drag_show | 4 | 326 | 2.5% |
| cadence_bachata_class___social_dance | 6 | 312 | 1.5% |
| cadence_vida_amore_divas_show__fiesta_semáforo__stoplight_party | 6 | 215 | 2.2% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 675 | 4.7% | instagram | Nov 18, 11:00 | Low light. Slow hands. The quiet creak of rope pulling taut. 🪢✨ Rope J |
| 529 | 4.9% | instagram | Nov 10, 19:00 | Toons don't play nice on this stage 🎬⚡ Cartoon Chaos is crashing into  |
| 373 | 4.6% | instagram | Oct 26, 19:00 | Mark your calendars mi gente, because the Main Floor is about to turn  |
| 363 | 2.8% | instagram | Nov 19, 11:00 | Save this one — everything you need for Cartoon Chaos at Azucar 📝🎬 Doo |
| 354 | 3.1% | instagram | Oct 27, 17:39 | El show de drag más longevo de Washington regresa con un twist peligro |
| 341 | 1.5% | instagram | Nov 21, 19:00 | No judgment, no pressure, just rope and community. 🪢💛 Whether you've d |
| 338 | 1.8% | instagram | Nov 16, 11:00 | Okay let's keep this simple porque you need these details 📝 Bachata cl |
| 328 | 7.0% | instagram | Nov 02, 11:00 | Neon glow, slow bachata beats, sudor en la frente 🌙✨ Picture this: the |
| 296 | 1.0% | instagram | Nov 11, 11:00 | Neon glow, slow bachata beats, dos maestras on the floor ✨🌙 Picture it |
| 290 | 1.4% | instagram | Nov 17, 19:00 | Come as your favorite character, come as yourself, come however you wa |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 170 | 2.4% | instagram | Nov 20, 19:00 | Come stuffed into your best fit or straight off the couch — doesn't ma |
| 175 | 1.1% | instagram | Nov 18, 11:00 | Faltan días para la Fiesta Semáforo y ya sentimos la cuenta regresiva. |
| 176 | 1.1% | instagram | Nov 22, 19:00 | Mark it down — this one's about to sell out your whole Sunday evening  |
| 181 | 2.8% | instagram | Nov 21, 19:00 | Puertas 8:30pm. Show 9:30pm. HOY. 🚦🔥 |
| 189 | 0.5% | instagram | Nov 17, 11:00 | Feel the sub before you even hear the song 🔊💥 That's the Stuff Your Ba |

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

