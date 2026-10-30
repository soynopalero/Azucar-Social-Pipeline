# Azúcar — real engagement report

_Generated 2026-10-30 11:31 PDT by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **40** published posts with metrics, of 188 marked posted in the queue
- **1868** Instagram posts and **5787** Facebook posts on file
- **43** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 15 | 272 | 3.5% |
| 5-9 posts | 5 | 263 (-3%) | 3.8% |
| 10-19 posts | 20 | 268 (-2%) | 3.2% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 15 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,066 |
| 19:00 | 1,059 |
| 18:00 | 1,052 |
| 17:00 | 1,040 |
| 16:00 | 1,037 |
| 15:00 | 1,028 |
| 21:00 | 1,014 |
| 13:00 | 1,009 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 40 | 268 | 3.4% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 40 | 268 | 3.4% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| morning | 18 | 280 | 3.6% |
| evening | 21 | 263 | 2.7% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Thursday | 6 | 365 | 2.9% |
| Friday | 5 | 272 | 3.9% |
| Tuesday | 11 | 272 | 3.5% |
| Saturday | 6 | 272 | 2.9% |
| Sunday | 5 | 270 | 3.2% |
| Monday | 5 | 263 | 3.8% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_link_up | 4 | 274 | 3.9% |
| cadence_scream_queens_drag_show | 14 | 274 | 3.7% |
| cadence_drag_o_weeen | 6 | 271 | 4.1% |
| cadence_american_horror_story_watch_party | 5 | 175 | 1.5% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 959 | 2.4% | instagram | Oct 15, 11:00 | The fog is rolling in and the screams are already real. 🩸💀 |
| 664 | 8.7% | instagram | Oct 22, 11:00 | Picture this: cards slapping the table, ice clinking in your glass, la |
| 609 | 4.8% | instagram | Oct 20, 19:00 | Picture this: twinkly charms clinking, snacks passed around the table, |
| 599 | 3.3% | instagram | Oct 20, 19:00 | Mark it down mi gente — Frankie is taking over the Main Floor and she' |
| 504 | 4.6% | instagram | Sep 19, 11:00 | Fog rolls across the Main Floor. Glitter catches the black-light like  |
| 485 | 3.9% | instagram | Sep 25, 11:00 | Here's everything you need to know: Scream Queens Drag Show hits Azuca |
| 474 | 3.6% | instagram | Oct 22, 11:00 | Brushes out, pumpkins ready — Sunday's about to get messy and magical. |
| 449 | 6.7% | instagram | Oct 19, 11:00 | Grab your prop bag — the castle is open. 🩸👠 |
| 403 | 6.2% | instagram | Sep 22, 19:00 | Come as you are, come in costume, come screaming — Azucar's Main Floor |
| 385 | 6.0% | instagram | Oct 11, 11:00 | Round two of spooky season just landed. 🎃🎤 Drag-O-Ween Karaoke is back |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 116 | 2.6% | instagram | Oct 29, 19:00 | The screams come back one last time. 😱🔪 |
| 127 | 3.1% | instagram | Oct 29, 11:00 | Link up, lock in, make something cute 🧿✨ Azúcar's Main Floor is turnin |
| 131 | 1.5% | instagram | Oct 26, 11:00 | Dim lights. Cold drinks. A room that gasps in unison. 🕯️🔪 |
| 173 | 1.7% | instagram | Oct 28, 19:00 | Fog curling across the floor. Face paint glowing under the lights. A m |
| 175 | 1.1% | instagram | Oct 21, 11:00 | Dim lights. Cold drinks. A room that gasps in unison. 🕯️🔪 |

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

