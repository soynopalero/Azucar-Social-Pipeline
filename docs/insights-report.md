# Azúcar — real engagement report

_Generated 2026-11-24 14:59 PST by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **25** published posts with metrics, of 182 marked posted in the queue
- **1915** Instagram posts and **8474** Facebook posts on file
- **67** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 4 | 341 | 3.8% |
| 5-9 posts | 6 | 260 (-24%) | 1.3% |
| 10-19 posts | 15 | 243 (-29%) | 2.1% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 4 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,077 |
| 19:00 | 1,077 |
| 18:00 | 1,072 |
| 17:00 | 1,060 |
| 16:00 | 1,054 |
| 15:00 | 1,047 |
| 14:00 | 1,027 |
| 13:00 | 1,027 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 25 | 267 | 2.1% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 25 | 267 | 2.1% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| morning | 10 | 269 | 1.7% |
| evening | 14 | 260 | 2.2% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Monday | 6 | 348 | 5.0% |
| Tuesday | 5 | 295 | 3.1% |
| Wednesday | 4 | 269 | 1.4% |
| Saturday | 3 | 267 | 1.4% |
| Sunday | 3 | 243 | 1.2% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_cartoon_chaos_drag_show | 4 | 332 | 2.4% |
| cadence_bachata_class___social_dance | 6 | 314 | 1.4% |
| cadence_vida_amore_divas_show__fiesta_semáforo__stoplight_party | 6 | 218 | 2.1% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 683 | 4.7% | instagram | Nov 18, 11:00 | Low light. Slow hands. The quiet creak of rope pulling taut. 🪢✨ Rope J |
| 531 | 4.9% | instagram | Nov 10, 19:00 | Toons don't play nice on this stage 🎬⚡ Cartoon Chaos is crashing into  |
| 460 | 5.4% | instagram | Nov 23, 19:00 | Snow outside, sparkle inside ❄️🎄 Picture this: the bass drops, the lig |
| 373 | 4.6% | instagram | Oct 26, 19:00 | Mark your calendars mi gente, because the Main Floor is about to turn  |
| 368 | 2.7% | instagram | Nov 19, 11:00 | Save this one — everything you need for Cartoon Chaos at Azucar 📝🎬 Doo |
| 361 | 1.4% | instagram | Nov 21, 19:00 | No judgment, no pressure, just rope and community. 🪢💛 Whether you've d |
| 354 | 3.1% | instagram | Oct 27, 17:39 | El show de drag más longevo de Washington regresa con un twist peligro |
| 354 | 12.4% | instagram | Nov 23, 19:00 | Mark it, mija — la tarjeta ya salió. 🔥 Abelle Fantasy is hosting SEX-E |
| 341 | 1.8% | instagram | Nov 16, 11:00 | Okay let's keep this simple porque you need these details 📝 Bachata cl |
| 328 | 7.0% | instagram | Nov 02, 11:00 | Neon glow, slow bachata beats, sudor en la frente 🌙✨ Picture this: the |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 74 | 5.4% | instagram | Nov 24, 11:00 | Save this for Friday 📌 Here's everything you need to know: Reggaeton 2 |
| 176 | 2.3% | instagram | Nov 20, 19:00 | Come stuffed into your best fit or straight off the couch — doesn't ma |
| 180 | 1.1% | instagram | Nov 18, 11:00 | Faltan días para la Fiesta Semáforo y ya sentimos la cuenta regresiva. |
| 192 | 0.5% | instagram | Nov 17, 11:00 | Feel the sub before you even hear the song 🔊💥 That's the Stuff Your Ba |
| 194 | 1.0% | instagram | Nov 22, 19:00 | Mark it down — this one's about to sell out your whole Sunday evening  |

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

