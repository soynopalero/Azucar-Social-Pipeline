# Azúcar — real engagement report

_Generated 2026-11-14 10:45 PST by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **24** published posts with metrics, of 142 marked posted in the queue
- **1894** Instagram posts and **8411** Facebook posts on file
- **58** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 7 | 343 | 3.1% |
| 5-9 posts | 7 | 321 (-6%) | 3.4% |
| 10-19 posts | 10 | 288 (-16%) | 2.8% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 7 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,075 |
| 19:00 | 1,072 |
| 18:00 | 1,066 |
| 17:00 | 1,054 |
| 16:00 | 1,049 |
| 15:00 | 1,042 |
| 21:00 | 1,024 |
| 14:00 | 1,023 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 24 | 322 | 3.0% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 24 | 322 | 3.0% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| evening | 11 | 352 | 3.4% |
| morning | 12 | 260 | 2.5% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Tuesday | 5 | 354 | 3.4% |
| Saturday | 3 | 352 | 2.8% |
| Monday | 5 | 321 | 4.6% |
| Thursday | 4 | 272 | 5.5% |
| Wednesday | 4 | 230 | 2.2% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_lesbians_playing_uno | 6 | 304 | 2.5% |
| cadence_the_sweet_spot | 4 | 221 | 1.9% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 1,526 | 6.0% | instagram | Nov 04, 11:00 | New besties are about to happen and y'all aren't ready 👯‍♀️🔥 Azucar is |
| 693 | 8.4% | instagram | Oct 22, 11:00 | Picture this: cards slapping the table, ice clinking in your glass, la |
| 486 | 5.1% | instagram | Nov 07, 19:00 | Board games just got a Latinx glow-up 🎲🔥 Gay's N Gameboards is pulling |
| 448 | 4.9% | instagram | Nov 10, 19:00 | Toons don't play nice on this stage 🎬⚡ Cartoon Chaos is crashing into  |
| 439 | 4.1% | instagram | Nov 10, 19:00 | Lights go low, bass drops, and suddenly you're back in middle school e |
| 402 | 3.5% | instagram | Nov 02, 19:00 | Mark it, underline it, set a reminder 🖤 The Sweet Spot is back and thi |
| 372 | 4.6% | instagram | Oct 26, 19:00 | Mark your calendars mi gente, because the Main Floor is about to turn  |
| 354 | 3.1% | instagram | Oct 27, 17:39 | El show de drag más longevo de Washington regresa con un twist peligro |
| 352 | 2.8% | instagram | Nov 07, 19:00 | Picture this 🫶 laughter bouncing off the walls, drinks clinking, stran |
| 343 | 2.6% | instagram | Oct 27, 19:00 | Come as you are, cards or no card skills required 🫶🃏 |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 126 | 1.6% | instagram | Nov 13, 11:00 | El show de drag más longevo de Washington regresa con un twist peligro |
| 166 | 0.0% | instagram | Nov 09, 19:00 | Come as you are, ask what you want, stay as long as you like 💛 The Swe |
| 184 | 2.7% | instagram | Nov 12, 19:00 | Come alone, leave with a whole new crew 🙌 Gay's N Gameboards is for ev |
| 191 | 2.6% | instagram | Nov 11, 11:00 | Save this one 📌 Your monthly reminder: The Sweet Spot, hosted by House |
| 217 | 2.3% | instagram | Nov 05, 11:00 | Picture this: cards slapping the table, ice clinking in your glass, la |

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

