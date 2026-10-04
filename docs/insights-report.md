# Azúcar — real engagement report

_Generated 2026-10-04 10:18 PDT by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **63** published posts with metrics, of 164 marked posted in the queue
- **1778** Instagram posts and **1692** Facebook posts on file
- **17** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 14 | 314 | 5.2% |
| 5-9 posts | 29 | 187 (-41%) | 3.2% |
| 10-19 posts | 20 | 206 (-34%) | 2.8% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 14 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,039 |
| 19:00 | 1,034 |
| 18:00 | 1,028 |
| 17:00 | 1,015 |
| 16:00 | 1,011 |
| 15:00 | 1,004 |
| 21:00 | 998 |
| 12:00 | 985 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 63 | 203 | 3.3% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 63 | 203 | 3.3% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| evening | 31 | 210 | 3.0% |
| morning | 32 | 195 | 3.9% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Tuesday | 6 | 302 | 3.9% |
| Friday | 11 | 271 | 4.0% |
| Wednesday | 5 | 205 | 3.3% |
| Saturday | 9 | 203 | 4.3% |
| Sunday | 10 | 201 | 3.4% |
| Monday | 10 | 188 | 2.8% |
| Thursday | 12 | 184 | 2.8% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_the_bikini_bottoms | 10 | 272 | 3.2% |
| cadence_scream_queens_drag_show | 7 | 271 | 4.6% |
| cadence_emo_night_drag_show_edition | 13 | 205 | 4.4% |
| cadence_industry_night_drag_show | 17 | 185 | 2.2% |
| cadence_mosh_night | 13 | 165 | 3.0% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 710 | 13.7% | instagram | Sep 08, 19:00 | Dust off the eyeliner and dig out those band tees — Emo Night just got |
| 567 | 3.9% | instagram | Sep 08, 19:00 | Riot mode: ACTIVATED. 🔥🤘 Revolutionary Riot Productions is turning Azu |
| 503 | 4.6% | instagram | Sep 19, 11:00 | Fog rolls across the Main Floor. Glitter catches the black-light like  |
| 475 | 4.0% | instagram | Sep 25, 11:00 | Here's everything you need to know: Scream Queens Drag Show hits Azuca |
| 456 | 8.8% | instagram | Sep 11, 19:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 454 | 3.7% | instagram | Sep 26, 11:00 | The dark is casting. 🖤⚡ |
| 400 | 6.2% | instagram | Sep 22, 19:00 | Come as you are, come in costume, come screaming — Azucar's Main Floor |
| 359 | 8.4% | instagram | Sep 20, 19:00 | Dust off the eyeliner and dig out those band tees — Emo Night just got |
| 343 | 5.2% | instagram | Sep 06, 19:00 | Mark your calendar — Industry Night Drag Show hits Azúcar this Sunday, |
| 342 | 5.6% | instagram | Sep 04, 19:00 | Sunday's your night off — so hand it over to Azúcar. 🍹👑 Industry Night |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 96 | 5.2% | instagram | Sep 07, 11:00 | Sunday's your night off — so hand it over to Azúcar. 🍹👑 Industry Night |
| 101 | 0.0% | instagram | Sep 23, 11:00 | Lights down, lashes on, and the smell of tequila already in the air. 💄 |
| 116 | 2.6% | instagram | Sep 14, 11:00 | Mark it down: Sunday, October 11 — Mosh Night takes over Azucar's Main |
| 125 | 5.6% | instagram | Sep 20, 11:00 | You feel it before you hear it — floor vibrating, chests thumping, swe |
| 134 | 0.7% | instagram | Oct 01, 11:00 | Mark it down: Sunday, October 11 — Mosh Night takes over Azucar's Main |

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

