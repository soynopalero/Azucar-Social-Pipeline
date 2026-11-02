# Azúcar — real engagement report

_Generated 2026-11-02 14:25 PST by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **25** published posts with metrics, of 128 marked posted in the queue
- **1873** Instagram posts and **8372** Facebook posts on file
- **46** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 10 | 284 | 4.0% |
| 5-9 posts | 5 | 309 (+9%) | 3.2% |
| 10-19 posts | 10 | 249 (-12%) | 2.0% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 10 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,066 |
| 19:00 | 1,061 |
| 18:00 | 1,053 |
| 17:00 | 1,042 |
| 16:00 | 1,040 |
| 15:00 | 1,031 |
| 21:00 | 1,016 |
| 13:00 | 1,013 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 25 | 267 | 2.5% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 25 | 267 | 2.5% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| evening | 13 | 267 | 2.5% |
| morning | 11 | 216 | 2.0% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Tuesday | 5 | 314 | 3.4% |
| Monday | 5 | 309 | 3.2% |
| Sunday | 3 | 301 | 5.6% |
| Thursday | 3 | 216 | 1.9% |
| Saturday | 5 | 211 | 1.4% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_drag_o_weeen | 6 | 284 | 4.0% |
| cadence_link_up | 5 | 267 | 3.4% |
| cadence_american_horror_story_watch_party | 5 | 210 | 1.3% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 690 | 8.4% | instagram | Oct 22, 11:00 | Picture this: cards slapping the table, ice clinking in your glass, la |
| 617 | 4.7% | instagram | Oct 20, 19:00 | Picture this: twinkly charms clinking, snacks passed around the table, |
| 464 | 6.5% | instagram | Oct 19, 11:00 | Grab your prop bag — the castle is open. 🩸👠 |
| 392 | 5.4% | instagram | Oct 23, 19:00 | Mark it down: Drag-O-Ween Karaoke hits the Main Floor on Wednesday, Oc |
| 385 | 6.0% | instagram | Oct 11, 11:00 | Round two of spooky season just landed. 🎃🎤 Drag-O-Ween Karaoke is back |
| 369 | 3.8% | instagram | Oct 24, 11:00 | Link up, lock in, make something cute 🧿✨ Azúcar's Main Floor is turnin |
| 337 | 4.7% | instagram | Oct 26, 19:00 | Mark your calendars mi gente, because the Main Floor is about to turn  |
| 316 | 2.5% | instagram | Oct 27, 19:00 | Come as you are, cards or no card skills required 🫶🃏 |
| 314 | 3.5% | instagram | Oct 27, 17:39 | El show de drag más longevo de Washington regresa con un twist peligro |
| 309 | 3.2% | instagram | Oct 26, 19:00 | Fishnets. Fog. The whole room shouting back at the screen. 🕯️🔪 |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 55 | 1.8% | instagram | Nov 02, 11:00 | Neon glow, slow bachata beats, sudor en la frente 🌙✨ Picture this: the |
| 151 | 1.3% | instagram | Oct 26, 11:00 | Dim lights. Cold drinks. A room that gasps in unison. 🕯️🔪 |
| 162 | 2.5% | instagram | Nov 01, 19:00 | Picture this: twinkly charms clinking, snacks passed around the table, |
| 185 | 1.1% | instagram | Oct 21, 11:00 | Dim lights. Cold drinks. A room that gasps in unison. 🕯️🔪 |
| 198 | 2.0% | instagram | Oct 20, 11:00 | Come as you are — or come as something way scarier. 🎃🖤 Drag-O-Ween Kar |

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

