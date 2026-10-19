# Azúcar — real engagement report

_Generated 2026-10-19 11:59 PDT by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **47** published posts with metrics, of 210 marked posted in the queue
- **1832** Instagram posts and **1743** Facebook posts on file
- **32** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 21 | 272 | 3.0% |
| 5-9 posts | 5 | 280 (+3%) | 4.3% |
| 10-19 posts | 12 | 165 (-39%) | 2.3% |
| 20+ posts | 9 | 258 (-5%) | 3.6% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 21 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,054 |
| 19:00 | 1,049 |
| 18:00 | 1,041 |
| 17:00 | 1,029 |
| 16:00 | 1,027 |
| 15:00 | 1,017 |
| 21:00 | 1,009 |
| 14:00 | 998 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 47 | 239 | 2.9% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 47 | 239 | 2.9% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| evening | 25 | 252 | 2.6% |
| morning | 22 | 210 | 3.2% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Tuesday | 6 | 272 | 4.2% |
| Friday | 11 | 256 | 2.9% |
| Saturday | 6 | 246 | 2.7% |
| Thursday | 8 | 208 | 2.6% |
| Monday | 8 | 206 | 2.9% |
| Sunday | 6 | 166 | 2.6% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_drag_o_weeen | 4 | 318 | 4.6% |
| cadence_scream_queens_drag_show | 13 | 272 | 3.5% |
| cadence_the_bikini_bottoms | 20 | 234 | 2.8% |
| cadence_mentivads_allstars___after_party | 4 | 167 | 1.0% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 934 | 2.5% | instagram | Oct 15, 11:00 | The fog is rolling in and the screams are already real. 🩸💀 |
| 504 | 4.6% | instagram | Sep 19, 11:00 | Fog rolls across the Main Floor. Glitter catches the black-light like  |
| 485 | 3.9% | instagram | Sep 25, 11:00 | Here's everything you need to know: Scream Queens Drag Show hits Azuca |
| 456 | 8.8% | instagram | Sep 11, 19:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 403 | 6.2% | instagram | Sep 22, 19:00 | Come as you are, come in costume, come screaming — Azucar's Main Floor |
| 400 | 4.2% | instagram | Oct 11, 11:00 | The mic is haunted. 🎃🎤 Drag-O-Ween Karaoke crashes the Lounge with Bea |
| 377 | 6.1% | instagram | Oct 11, 11:00 | Round two of spooky season just landed. 🎃🎤 Drag-O-Ween Karaoke is back |
| 341 | 2.9% | instagram | Oct 02, 11:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 330 | 2.7% | instagram | Oct 01, 19:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 326 | 5.2% | instagram | Oct 15, 19:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 34 | 14.7% | instagram | Oct 19, 11:00 | Grab your prop bag — the castle is open. 🩸👠 |
| 110 | 2.7% | instagram | Oct 18, 11:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 121 | 1.7% | instagram | Oct 18, 19:00 | The crowns are coming out and the Lounge is about to belong to the KIN |
| 137 | 1.5% | instagram | Oct 17, 19:00 | Anota esto antes de que se te olvide 📝🔥 |
| 156 | 0.6% | instagram | Oct 16, 11:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |

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

