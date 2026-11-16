# Azúcar — real engagement report

_Generated 2026-11-16 14:49 PST by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **21** published posts with metrics, of 132 marked posted in the queue
- **1900** Instagram posts and **8433** Facebook posts on file
- **60** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 5 | 317 | 3.1% |
| 5-9 posts | 5 | 327 (+3%) | 3.4% |
| 10-19 posts | 11 | 227 (-28%) | 2.3% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 5 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,076 |
| 19:00 | 1,073 |
| 18:00 | 1,068 |
| 17:00 | 1,057 |
| 16:00 | 1,051 |
| 15:00 | 1,044 |
| 14:00 | 1,025 |
| 21:00 | 1,024 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 21 | 262 | 2.7% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 21 | 262 | 2.7% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| morning | 9 | 262 | 1.7% |
| evening | 11 | 230 | 3.4% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Tuesday | 3 | 461 | 3.9% |
| Monday | 6 | 322 | 4.0% |
| Wednesday | 3 | 234 | 1.7% |
| Saturday | 3 | 230 | 1.5% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_bachata_class___social_dance | 5 | 265 | 1.3% |
| cadence_the_sweet_spot | 5 | 213 | 1.5% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 503 | 5.0% | instagram | Nov 07, 19:00 | Board games just got a Latinx glow-up 🎲🔥 Gay's N Gameboards is pulling |
| 490 | 5.1% | instagram | Nov 10, 19:00 | Toons don't play nice on this stage 🎬⚡ Cartoon Chaos is crashing into  |
| 461 | 3.9% | instagram | Nov 10, 19:00 | Lights go low, bass drops, and suddenly you're back in middle school e |
| 407 | 3.4% | instagram | Nov 02, 19:00 | Mark it, underline it, set a reminder 🖤 The Sweet Spot is back and thi |
| 391 | 8.2% | instagram | Nov 12, 11:00 | Whoever had a poster on their wall, a crush on a boy-band member, or a |
| 373 | 4.6% | instagram | Oct 26, 19:00 | Mark your calendars mi gente, because the Main Floor is about to turn  |
| 354 | 3.1% | instagram | Oct 27, 17:39 | El show de drag más longevo de Washington regresa con un twist peligro |
| 327 | 7.0% | instagram | Nov 02, 11:00 | Neon glow, slow bachata beats, sudor en la frente 🌙✨ Picture this: the |
| 317 | 5.0% | instagram | Nov 09, 11:00 | Picture it: dice clacking, dominoes slapping down hard, laughter bounc |
| 265 | 1.1% | instagram | Nov 11, 11:00 | Neon glow, slow bachata beats, dos maestras on the floor ✨🌙 Picture it |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 82 | 0.0% | instagram | Nov 16, 11:00 | Okay let's keep this simple porque you need these details 📝 Bachata cl |
| 166 | 1.8% | instagram | Nov 15, 19:00 | Cabana Bass is back and this time they're not holding ANYTHING back 🔊🐟 |
| 177 | 1.7% | instagram | Nov 13, 11:00 | El show de drag más longevo de Washington regresa con un twist peligro |
| 180 | 0.0% | instagram | Nov 09, 19:00 | Come as you are, ask what you want, stay as long as you like 💛 The Swe |
| 197 | 1.5% | instagram | Nov 14, 19:00 | Mark it, underline it, set a reminder 🖤 The Sweet Spot is back and thi |

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

