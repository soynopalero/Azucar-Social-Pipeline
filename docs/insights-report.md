# Azúcar — real engagement report

_Generated 2026-11-11 12:01 PST by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **22** published posts with metrics, of 114 marked posted in the queue
- **1890** Instagram posts and **8404** Facebook posts on file
- **55** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 7 | 341 | 3.1% |
| 5-9 posts | 7 | 309 (-9%) | 3.5% |
| 10-19 posts | 8 | 305 (-11%) | 3.9% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 7 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,073 |
| 19:00 | 1,069 |
| 18:00 | 1,063 |
| 17:00 | 1,051 |
| 16:00 | 1,047 |
| 15:00 | 1,039 |
| 21:00 | 1,023 |
| 13:00 | 1,021 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 22 | 310 | 3.3% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 22 | 310 | 3.3% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| evening | 10 | 325 | 3.3% |
| morning | 10 | 262 | 3.7% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Thursday | 3 | 687 | 4.1% |
| Saturday | 3 | 331 | 3.0% |
| Tuesday | 5 | 319 | 3.5% |
| Monday | 5 | 309 | 4.6% |
| Wednesday | 3 | 214 | 6.1% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_lesbians_playing_uno | 6 | 287 | 2.5% |
| cadence_the_sweet_spot | 4 | 188 | 2.0% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 1,497 | 6.1% | instagram | Nov 04, 11:00 | New besties are about to happen and y'all aren't ready 👯‍♀️🔥 Azucar is |
| 693 | 8.4% | instagram | Oct 22, 11:00 | Picture this: cards slapping the table, ice clinking in your glass, la |
| 687 | 4.1% | instagram | Nov 05, 11:05 | Friday just got a new name to know: FREAKETONAS. 🔥🍑 |
| 463 | 5.4% | instagram | Nov 07, 19:00 | Board games just got a Latinx glow-up 🎲🔥 Gay's N Gameboards is pulling |
| 393 | 2.8% | instagram | Nov 02, 19:00 | Mark it, underline it, set a reminder 🖤 The Sweet Spot is back and thi |
| 371 | 4.6% | instagram | Oct 26, 19:00 | Mark your calendars mi gente, because the Main Floor is about to turn  |
| 350 | 3.1% | instagram | Oct 27, 17:39 | El show de drag más longevo de Washington regresa con un twist peligro |
| 341 | 2.6% | instagram | Oct 27, 19:00 | Come as you are, cards or no card skills required 🫶🃏 |
| 331 | 3.0% | instagram | Nov 07, 19:00 | Picture this 🫶 laughter bouncing off the walls, drinks clinking, stran |
| 319 | 4.7% | instagram | Nov 10, 19:00 | Lights go low, bass drops, and suddenly you're back in middle school e |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 20 | 10.0% | instagram | Nov 11, 11:00 | Save this one 📌 Your monthly reminder: The Sweet Spot, hosted by House |
| 141 | 0.0% | instagram | Nov 09, 19:00 | Come as you are, ask what you want, stay as long as you like 💛 The Swe |
| 208 | 2.4% | instagram | Nov 05, 11:00 | Picture this: cards slapping the table, ice clinking in your glass, la |
| 214 | 1.9% | instagram | Nov 04, 11:00 | Luces rojas, amarillas, verdes — y tú decidiendo cuál te define esta n |
| 234 | 1.3% | instagram | Nov 06, 11:00 | Low light. Soft music. Doors wide open. 🕯️ That's the mood the second  |

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

