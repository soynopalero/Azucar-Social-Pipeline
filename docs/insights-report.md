# Azúcar — real engagement report

_Generated 2026-11-15 11:20 PST by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **24** published posts with metrics, of 146 marked posted in the queue
- **1897** Instagram posts and **8425** Facebook posts on file
- **59** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 8 | 326 | 2.9% |
| 5-9 posts | 6 | 308 (-6%) | 2.7% |
| 10-19 posts | 10 | 234 (-28%) | 2.6% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 8 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,075 |
| 19:00 | 1,072 |
| 18:00 | 1,067 |
| 17:00 | 1,055 |
| 16:00 | 1,050 |
| 15:00 | 1,043 |
| 21:00 | 1,024 |
| 14:00 | 1,024 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 24 | 300 | 2.7% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 24 | 300 | 2.7% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| evening | 12 | 335 | 3.1% |
| morning | 11 | 260 | 2.3% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Tuesday | 5 | 354 | 3.4% |
| Monday | 5 | 324 | 4.6% |
| Thursday | 4 | 293 | 5.4% |
| Wednesday | 3 | 233 | 1.7% |
| Saturday | 4 | 226 | 1.5% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_lesbians_playing_uno | 6 | 308 | 2.4% |
| cadence_bachata_class___social_dance | 4 | 290 | 2.7% |
| cadence_the_sweet_spot | 5 | 205 | 1.9% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 693 | 8.4% | instagram | Oct 22, 11:00 | Picture this: cards slapping the table, ice clinking in your glass, la |
| 498 | 5.0% | instagram | Nov 07, 19:00 | Board games just got a Latinx glow-up 🎲🔥 Gay's N Gameboards is pulling |
| 460 | 4.8% | instagram | Nov 10, 19:00 | Toons don't play nice on this stage 🎬⚡ Cartoon Chaos is crashing into  |
| 453 | 4.0% | instagram | Nov 10, 19:00 | Lights go low, bass drops, and suddenly you're back in middle school e |
| 407 | 3.4% | instagram | Nov 02, 19:00 | Mark it, underline it, set a reminder 🖤 The Sweet Spot is back and thi |
| 373 | 4.6% | instagram | Oct 26, 19:00 | Mark your calendars mi gente, because the Main Floor is about to turn  |
| 366 | 7.9% | instagram | Nov 12, 11:00 | Whoever had a poster on their wall, a crush on a boy-band member, or a |
| 354 | 3.1% | instagram | Oct 27, 17:39 | El show de drag más longevo de Washington regresa con un twist peligro |
| 344 | 2.6% | instagram | Oct 27, 19:00 | Come as you are, cards or no card skills required 🫶🃏 |
| 326 | 3.4% | instagram | Nov 03, 19:00 | Pull up your chair, shuffle the deck, and get ready — Lesbians Playing |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 156 | 1.9% | instagram | Nov 14, 19:00 | Mark it, underline it, set a reminder 🖤 The Sweet Spot is back and thi |
| 164 | 1.8% | instagram | Nov 13, 11:00 | El show de drag más longevo de Washington regresa con un twist peligro |
| 175 | 0.0% | instagram | Nov 09, 19:00 | Come as you are, ask what you want, stay as long as you like 💛 The Swe |
| 181 | 0.6% | instagram | Nov 14, 19:00 | Zero rhythm? Two left feet? Never danced bachata in your life? Girl, s |
| 205 | 2.4% | instagram | Nov 11, 11:00 | Save this one 📌 Your monthly reminder: The Sweet Spot, hosted by House |

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

