# Azúcar — real engagement report

_Generated 2026-11-27 13:53 PST by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **23** published posts with metrics, of 186 marked posted in the queue
- **1919** Instagram posts and **8482** Facebook posts on file
- **70** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 3 | 263 | 1.7% |
| 5-9 posts | 4 | 273 (+4%) | 4.2% |
| 10-19 posts | 16 | 297 (+13%) | 2.1% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 3 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,077 |
| 19:00 | 1,077 |
| 18:00 | 1,072 |
| 17:00 | 1,061 |
| 16:00 | 1,055 |
| 15:00 | 1,047 |
| 14:00 | 1,028 |
| 13:00 | 1,027 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 23 | 281 | 2.2% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 23 | 281 | 2.2% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| morning | 10 | 278 | 3.0% |
| evening | 12 | 272 | 1.9% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Monday | 3 | 492 | 4.9% |
| Wednesday | 4 | 320 | 3.1% |
| Tuesday | 6 | 315 | 2.2% |
| Sunday | 3 | 263 | 1.3% |
| Friday | 3 | 196 | 2.0% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_cartoon_chaos_drag_show | 4 | 352 | 2.2% |
| cadence_vida_amore_divas_show__fiesta_semáforo__stoplight_party | 6 | 230 | 1.9% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 711 | 4.5% | instagram | Nov 18, 11:00 | Low light. Slow hands. The quiet creak of rope pulling taut. 🪢✨ Rope J |
| 576 | 4.9% | instagram | Nov 23, 19:00 | Snow outside, sparkle inside ❄️🎄 Picture this: the bass drops, the lig |
| 534 | 4.9% | instagram | Nov 10, 19:00 | Toons don't play nice on this stage 🎬⚡ Cartoon Chaos is crashing into  |
| 492 | 10.6% | instagram | Nov 23, 19:00 | Mark it, mija — la tarjeta ya salió. 🔥 Abelle Fantasy is hosting SEX-E |
| 411 | 1.7% | instagram | Nov 21, 19:00 | No judgment, no pressure, just rope and community. 🪢💛 Whether you've d |
| 402 | 13.2% | instagram | Nov 25, 11:00 | Here's everything you need to know so you don't miss it. 🗒️ My Little  |
| 390 | 2.6% | instagram | Nov 19, 11:00 | Save this one — everything you need for Cartoon Chaos at Azucar 📝🎬 Doo |
| 354 | 3.1% | instagram | Oct 27, 17:39 | El show de drag más longevo de Washington regresa con un twist peligro |
| 326 | 5.5% | instagram | Nov 26, 11:00 | Come matching. Come cute. Come sexy. Come exactly as you are — the Ran |
| 317 | 6.6% | instagram | Nov 24, 11:00 | Save this for Friday 📌 Here's everything you need to know: Reggaeton 2 |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 86 | 3.5% | instagram | Nov 27, 11:00 | Mark it down now 📌 Drag Me to Christmas hits Azucar Saturday, December |
| 193 | 1.0% | instagram | Nov 18, 11:00 | Faltan días para la Fiesta Semáforo y ya sentimos la cuenta regresiva. |
| 196 | 2.0% | instagram | Nov 20, 19:00 | Come stuffed into your best fit or straight off the couch — doesn't ma |
| 206 | 0.5% | instagram | Nov 17, 11:00 | Feel the sub before you even hear the song 🔊💥 That's the Stuff Your Ba |
| 214 | 0.9% | instagram | Nov 24, 19:00 | Come as you are, leave with something only you could've made 🫶 Build Y |

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

