# Azúcar — real engagement report

_Generated 2026-11-25 14:12 PST by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **27** published posts with metrics, of 196 marked posted in the queue
- **1917** Instagram posts and **8478** Facebook posts on file
- **68** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 4 | 341 | 3.8% |
| 5-9 posts | 6 | 261 (-23%) | 1.3% |
| 10-19 posts | 17 | 229 (-33%) | 1.9% |

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
| instagram | 27 | 257 | 1.9% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 27 | 257 | 1.9% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| evening | 15 | 257 | 1.9% |
| morning | 11 | 239 | 1.7% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Monday | 6 | 358 | 4.7% |
| Saturday | 3 | 269 | 1.6% |
| Tuesday | 6 | 264 | 2.2% |
| Sunday | 3 | 253 | 1.4% |
| Wednesday | 5 | 239 | 1.7% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_cartoon_chaos_drag_show | 4 | 336 | 2.3% |
| cadence_bachata_class___social_dance | 6 | 316 | 1.4% |
| cadence_vida_amore_divas_show__fiesta_semáforo__stoplight_party | 6 | 221 | 2.0% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 693 | 4.6% | instagram | Nov 18, 11:00 | Low light. Slow hands. The quiet creak of rope pulling taut. 🪢✨ Rope J |
| 533 | 4.9% | instagram | Nov 10, 19:00 | Toons don't play nice on this stage 🎬⚡ Cartoon Chaos is crashing into  |
| 530 | 4.9% | instagram | Nov 23, 19:00 | Snow outside, sparkle inside ❄️🎄 Picture this: the bass drops, the lig |
| 441 | 11.6% | instagram | Nov 23, 19:00 | Mark it, mija — la tarjeta ya salió. 🔥 Abelle Fantasy is hosting SEX-E |
| 380 | 1.6% | instagram | Nov 21, 19:00 | No judgment, no pressure, just rope and community. 🪢💛 Whether you've d |
| 373 | 4.6% | instagram | Oct 26, 19:00 | Mark your calendars mi gente, because the Main Floor is about to turn  |
| 373 | 2.7% | instagram | Nov 19, 11:00 | Save this one — everything you need for Cartoon Chaos at Azucar 📝🎬 Doo |
| 354 | 3.1% | instagram | Oct 27, 17:39 | El show de drag más longevo de Washington regresa con un twist peligro |
| 344 | 1.7% | instagram | Nov 16, 11:00 | Okay let's keep this simple porque you need these details 📝 Bachata cl |
| 328 | 7.0% | instagram | Nov 02, 11:00 | Neon glow, slow bachata beats, sudor en la frente 🌙✨ Picture this: the |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 56 | 17.9% | instagram | Nov 25, 11:00 | Here's everything you need to know so you don't miss it. 🗒️ My Little  |
| 168 | 1.2% | instagram | Nov 24, 19:00 | Come as you are, leave with something only you could've made 🫶 Build Y |
| 184 | 1.1% | instagram | Nov 18, 11:00 | Faltan días para la Fiesta Semáforo y ya sentimos la cuenta regresiva. |
| 184 | 2.2% | instagram | Nov 20, 19:00 | Come stuffed into your best fit or straight off the couch — doesn't ma |
| 195 | 0.5% | instagram | Nov 17, 11:00 | Feel the sub before you even hear the song 🔊💥 That's the Stuff Your Ba |

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

