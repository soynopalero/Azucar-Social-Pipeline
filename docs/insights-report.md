# Azúcar — real engagement report

_Generated 2026-11-04 12:23 PST by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **28** published posts with metrics, of 142 marked posted in the queue
- **1876** Instagram posts and **8377** Facebook posts on file
- **48** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 9 | 310 | 5.2% |
| 5-9 posts | 9 | 218 (-30%) | 3.7% |
| 10-19 posts | 10 | 266 (-14%) | 1.9% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 9 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,069 |
| 19:00 | 1,064 |
| 18:00 | 1,056 |
| 17:00 | 1,045 |
| 16:00 | 1,042 |
| 15:00 | 1,033 |
| 21:00 | 1,019 |
| 13:00 | 1,015 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 28 | 276 | 3.2% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 28 | 276 | 3.2% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| evening | 15 | 283 | 2.7% |
| morning | 12 | 231 | 4.6% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Monday | 6 | 316 | 3.8% |
| Sunday | 3 | 310 | 5.5% |
| Tuesday | 6 | 306 | 3.3% |
| Thursday | 3 | 240 | 1.7% |
| Saturday | 5 | 222 | 1.4% |
| Wednesday | 3 | 190 | 1.2% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_drag_o_weeen | 6 | 289 | 3.9% |
| cadence_link_up | 5 | 283 | 3.2% |
| cadence_lesbians_playing_uno | 4 | 275 | 3.5% |
| cadence_american_horror_story_watch_party | 5 | 211 | 1.2% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 690 | 8.4% | instagram | Oct 22, 11:00 | Picture this: cards slapping the table, ice clinking in your glass, la |
| 620 | 4.7% | instagram | Oct 20, 19:00 | Picture this: twinkly charms clinking, snacks passed around the table, |
| 465 | 6.5% | instagram | Oct 19, 11:00 | Grab your prop bag — the castle is open. 🩸👠 |
| 400 | 5.2% | instagram | Oct 23, 19:00 | Mark it down: Drag-O-Ween Karaoke hits the Main Floor on Wednesday, Oc |
| 385 | 6.0% | instagram | Oct 11, 11:00 | Round two of spooky season just landed. 🎃🎤 Drag-O-Ween Karaoke is back |
| 381 | 3.7% | instagram | Oct 24, 11:00 | Link up, lock in, make something cute 🧿✨ Azúcar's Main Floor is turnin |
| 359 | 4.5% | instagram | Oct 26, 19:00 | Mark your calendars mi gente, because the Main Floor is about to turn  |
| 330 | 3.3% | instagram | Oct 27, 17:39 | El show de drag más longevo de Washington regresa con un twist peligro |
| 328 | 2.7% | instagram | Oct 27, 19:00 | Come as you are, cards or no card skills required 🫶🃏 |
| 320 | 3.1% | instagram | Oct 26, 19:00 | Fishnets. Fog. The whole room shouting back at the screen. 🕯️🔪 |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 27 | 18.5% | instagram | Nov 04, 11:00 | New besties are about to happen and y'all aren't ready 👯‍♀️🔥 Azucar is |
| 160 | 1.2% | instagram | Oct 26, 11:00 | Dim lights. Cold drinks. A room that gasps in unison. 🕯️🔪 |
| 190 | 1.1% | instagram | Oct 21, 11:00 | Dim lights. Cold drinks. A room that gasps in unison. 🕯️🔪 |
| 192 | 4.2% | instagram | Nov 03, 19:00 | Pull up your chair, shuffle the deck, and get ready — Lesbians Playing |
| 201 | 2.0% | instagram | Oct 20, 11:00 | Come as you are — or come as something way scarier. 🎃🖤 Drag-O-Ween Kar |

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

