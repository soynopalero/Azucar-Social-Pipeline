# Azúcar — real engagement report

_Generated 2026-10-23 10:52 PDT by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **56** published posts with metrics, of 218 marked posted in the queue
- **1847** Instagram posts and **5694** Facebook posts on file
- **36** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 21 | 272 | 3.0% |
| 5-9 posts | 9 | 190 (-30%) | 2.4% |
| 10-19 posts | 21 | 207 (-24%) | 2.8% |
| 20+ posts | 5 | 235 (-14%) | 3.6% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 21 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,058 |
| 19:00 | 1,053 |
| 18:00 | 1,044 |
| 17:00 | 1,034 |
| 16:00 | 1,030 |
| 15:00 | 1,022 |
| 21:00 | 1,010 |
| 14:00 | 1,002 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 56 | 237 | 2.9% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 56 | 237 | 2.9% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| evening | 27 | 258 | 2.8% |
| morning | 29 | 207 | 3.0% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Tuesday | 11 | 272 | 3.6% |
| Saturday | 6 | 269 | 3.1% |
| Friday | 11 | 256 | 2.9% |
| Thursday | 11 | 233 | 3.0% |
| Monday | 9 | 228 | 2.8% |
| Sunday | 5 | 180 | 2.0% |
| Wednesday | 3 | 179 | 1.7% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_scream_queens_drag_show | 14 | 272 | 3.7% |
| cadence_the_bikini_bottoms | 24 | 204 | 2.4% |
| cadence_mentivads_allstars___after_party | 4 | 174 | 0.9% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 948 | 2.4% | instagram | Oct 15, 11:00 | The fog is rolling in and the screams are already real. 🩸💀 |
| 538 | 4.3% | instagram | Oct 20, 19:00 | Picture this: twinkly charms clinking, snacks passed around the table, |
| 504 | 4.6% | instagram | Sep 19, 11:00 | Fog rolls across the Main Floor. Glitter catches the black-light like  |
| 503 | 3.6% | instagram | Oct 20, 19:00 | Mark it down mi gente — Frankie is taking over the Main Floor and she' |
| 485 | 3.9% | instagram | Sep 25, 11:00 | Here's everything you need to know: Scream Queens Drag Show hits Azuca |
| 456 | 8.8% | instagram | Sep 11, 19:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 422 | 3.8% | instagram | Oct 17, 19:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 403 | 6.2% | instagram | Sep 22, 19:00 | Come as you are, come in costume, come screaming — Azucar's Main Floor |
| 380 | 6.1% | instagram | Oct 11, 11:00 | Round two of spooky season just landed. 🎃🎤 Drag-O-Ween Karaoke is back |
| 380 | 6.3% | instagram | Oct 22, 11:00 | Picture this: cards slapping the table, ice clinking in your glass, la |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 100 | 2.0% | instagram | Oct 22, 11:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 108 | 0.9% | instagram | Oct 20, 11:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 132 | 0.8% | instagram | Oct 21, 11:00 | Dim lights. Cold drinks. A room that gasps in unison. 🕯️🔪 |
| 134 | 3.0% | instagram | Oct 22, 11:00 | Lights low, music sultry, and every single body in the room moving wit |
| 151 | 2.0% | instagram | Oct 18, 11:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |

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

