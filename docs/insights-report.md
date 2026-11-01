# Azúcar — real engagement report

_Generated 2026-11-01 10:24 PST by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **28** published posts with metrics, of 148 marked posted in the queue
- **1871** Instagram posts and **6287** Facebook posts on file
- **45** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 5 | 267 | 2.6% |
| 5-9 posts | 7 | 333 (+25%) | 3.5% |
| 10-19 posts | 16 | 255 (-4%) | 2.1% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 5 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,066 |
| 19:00 | 1,061 |
| 18:00 | 1,053 |
| 17:00 | 1,042 |
| 16:00 | 1,039 |
| 15:00 | 1,030 |
| 21:00 | 1,016 |
| 13:00 | 1,011 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 28 | 283 | 2.6% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 28 | 283 | 2.6% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| morning | 12 | 282 | 2.9% |
| evening | 15 | 267 | 2.6% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Monday | 4 | 320 | 4.0% |
| Sunday | 4 | 308 | 3.5% |
| Tuesday | 6 | 306 | 3.3% |
| Thursday | 5 | 265 | 2.3% |
| Saturday | 5 | 210 | 1.4% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_link_up | 4 | 312 | 3.6% |
| cadence_drag_o_weeen | 6 | 283 | 4.0% |
| cadence_american_horror_story_watch_party | 5 | 196 | 1.4% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 685 | 8.5% | instagram | Oct 22, 11:00 | Picture this: cards slapping the table, ice clinking in your glass, la |
| 617 | 3.2% | instagram | Oct 20, 19:00 | Mark it down mi gente — Frankie is taking over the Main Floor and she' |
| 615 | 4.7% | instagram | Oct 20, 19:00 | Picture this: twinkly charms clinking, snacks passed around the table, |
| 480 | 3.5% | instagram | Oct 22, 11:00 | Brushes out, pumpkins ready — Sunday's about to get messy and magical. |
| 459 | 6.5% | instagram | Oct 19, 11:00 | Grab your prop bag — the castle is open. 🩸👠 |
| 390 | 5.4% | instagram | Oct 23, 19:00 | Mark it down: Drag-O-Ween Karaoke hits the Main Floor on Wednesday, Oc |
| 385 | 6.0% | instagram | Oct 11, 11:00 | Round two of spooky season just landed. 🎃🎤 Drag-O-Ween Karaoke is back |
| 363 | 3.9% | instagram | Oct 24, 11:00 | Link up, lock in, make something cute 🧿✨ Azúcar's Main Floor is turnin |
| 333 | 4.8% | instagram | Oct 26, 19:00 | Mark your calendars mi gente, because the Main Floor is about to turn  |
| 317 | 1.3% | instagram | Oct 25, 19:00 | Every body welcome, every body beautiful, every body about to learn so |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 146 | 1.4% | instagram | Oct 26, 11:00 | Dim lights. Cold drinks. A room that gasps in unison. 🕯️🔪 |
| 166 | 0.6% | instagram | Oct 31, 11:00 | Mark it down — Lesbians Playing Uno returns to Azucar this Sunday 🃏 |
| 179 | 1.1% | instagram | Oct 21, 11:00 | Dim lights. Cold drinks. A room that gasps in unison. 🕯️🔪 |
| 196 | 2.0% | instagram | Oct 20, 11:00 | Come as you are — or come as something way scarier. 🎃🖤 Drag-O-Ween Kar |
| 196 | 2.0% | instagram | Oct 29, 11:00 | Link up, lock in, make something cute 🧿✨ Azúcar's Main Floor is turnin |

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

