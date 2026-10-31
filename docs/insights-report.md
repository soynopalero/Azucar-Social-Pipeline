# Azúcar — real engagement report

_Generated 2026-10-31 10:44 PDT by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **26** published posts with metrics, of 140 marked posted in the queue
- **1868** Instagram posts and **6187** Facebook posts on file
- **44** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 5 | 267 | 2.6% |
| 5-9 posts | 7 | 323 (+21%) | 3.6% |
| 10-19 posts | 14 | 259 (-3%) | 2.6% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 5 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,066 |
| 19:00 | 1,060 |
| 18:00 | 1,053 |
| 17:00 | 1,041 |
| 16:00 | 1,037 |
| 15:00 | 1,029 |
| 21:00 | 1,015 |
| 13:00 | 1,010 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 26 | 280 | 3.0% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 26 | 280 | 3.0% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| morning | 11 | 286 | 3.4% |
| evening | 14 | 276 | 2.7% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Monday | 4 | 308 | 4.2% |
| Sunday | 4 | 286 | 3.7% |
| Tuesday | 6 | 282 | 3.5% |
| Thursday | 5 | 261 | 2.4% |
| Saturday | 3 | 210 | 1.4% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_link_up | 4 | 296 | 3.6% |
| cadence_drag_o_weeen | 6 | 276 | 4.0% |
| cadence_american_horror_story_watch_party | 5 | 176 | 1.4% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 676 | 8.6% | instagram | Oct 22, 11:00 | Picture this: cards slapping the table, ice clinking in your glass, la |
| 611 | 4.7% | instagram | Oct 20, 19:00 | Picture this: twinkly charms clinking, snacks passed around the table, |
| 608 | 3.3% | instagram | Oct 20, 19:00 | Mark it down mi gente — Frankie is taking over the Main Floor and she' |
| 476 | 3.6% | instagram | Oct 22, 11:00 | Brushes out, pumpkins ready — Sunday's about to get messy and magical. |
| 453 | 6.6% | instagram | Oct 19, 11:00 | Grab your prop bag — the castle is open. 🩸👠 |
| 385 | 6.0% | instagram | Oct 11, 11:00 | Round two of spooky season just landed. 🎃🎤 Drag-O-Ween Karaoke is back |
| 385 | 5.5% | instagram | Oct 23, 19:00 | Mark it down: Drag-O-Ween Karaoke hits the Main Floor on Wednesday, Oc |
| 350 | 3.4% | instagram | Oct 24, 11:00 | Link up, lock in, make something cute 🧿✨ Azúcar's Main Floor is turnin |
| 323 | 5.0% | instagram | Oct 26, 19:00 | Mark your calendars mi gente, because the Main Floor is about to turn  |
| 293 | 3.4% | instagram | Oct 26, 19:00 | Fishnets. Fog. The whole room shouting back at the screen. 🕯️🔪 |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 136 | 1.5% | instagram | Oct 26, 11:00 | Dim lights. Cold drinks. A room that gasps in unison. 🕯️🔪 |
| 165 | 2.4% | instagram | Oct 29, 11:00 | Link up, lock in, make something cute 🧿✨ Azúcar's Main Floor is turnin |
| 168 | 1.8% | instagram | Oct 29, 19:00 | The screams come back one last time. 😱🔪 |
| 176 | 1.1% | instagram | Oct 21, 11:00 | Dim lights. Cold drinks. A room that gasps in unison. 🕯️🔪 |
| 194 | 2.1% | instagram | Oct 20, 11:00 | Come as you are — or come as something way scarier. 🎃🖤 Drag-O-Ween Kar |

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

