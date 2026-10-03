# Azúcar — real engagement report

_Generated 2026-10-03 10:02 PDT by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **84** published posts with metrics, of 202 marked posted in the queue
- **1776** Instagram posts and **1690** Facebook posts on file
- **16** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 21 | 338 | 5.2% |
| 5-9 posts | 44 | 188 (-44%) | 3.2% |
| 10-19 posts | 19 | 205 (-39%) | 2.8% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 21 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,039 |
| 19:00 | 1,034 |
| 18:00 | 1,026 |
| 17:00 | 1,014 |
| 16:00 | 1,010 |
| 15:00 | 1,002 |
| 21:00 | 998 |
| 12:00 | 984 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 84 | 202 | 3.5% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 84 | 202 | 3.5% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| evening | 42 | 224 | 3.4% |
| morning | 42 | 196 | 3.7% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Saturday | 13 | 272 | 3.8% |
| Friday | 12 | 252 | 3.7% |
| Tuesday | 8 | 222 | 4.0% |
| Sunday | 16 | 196 | 3.5% |
| Wednesday | 10 | 192 | 4.0% |
| Thursday | 14 | 184 | 3.1% |
| Monday | 11 | 171 | 2.6% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_scream_queens_drag_show | 6 | 333 | 4.3% |
| cadence_the_bikini_bottoms | 10 | 243 | 3.5% |
| cadence_furanium_fever | 23 | 220 | 3.6% |
| cadence_emo_night_drag_show_edition | 12 | 202 | 4.4% |
| cadence_industry_night_drag_show | 17 | 185 | 2.2% |
| cadence_mosh_night | 13 | 164 | 3.0% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 1,238 | 12.8% | instagram | Aug 16, 19:00 | Tri-Cities Furs just took over Azúcar and the whole city is about to f |
| 710 | 13.7% | instagram | Sep 08, 19:00 | Dust off the eyeliner and dig out those band tees — Emo Night just got |
| 567 | 3.9% | instagram | Sep 08, 19:00 | Riot mode: ACTIVATED. 🔥🤘 Revolutionary Riot Productions is turning Azu |
| 508 | 2.0% | instagram | Sep 25, 19:00 | However you show up — fursuit, glitter, streetwear, or something in be |
| 502 | 4.6% | instagram | Sep 19, 11:00 | Fog rolls across the Main Floor. Glitter catches the black-light like  |
| 495 | 7.9% | instagram | Aug 23, 11:00 | Mark it down: Furanium Fever hits Azúcar's Main Floor on Saturday, Sep |
| 475 | 6.9% | instagram | Aug 19, 11:00 | Disco ball spinning, glow paint glowing, bass rattling your ribcage —  |
| 473 | 4.0% | instagram | Sep 25, 11:00 | Here's everything you need to know: Scream Queens Drag Show hits Azuca |
| 456 | 8.8% | instagram | Sep 11, 19:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 443 | 3.8% | instagram | Sep 26, 11:00 | The dark is casting. 🖤⚡ |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 96 | 5.2% | instagram | Sep 07, 11:00 | Sunday's your night off — so hand it over to Azúcar. 🍹👑 Industry Night |
| 100 | 0.0% | instagram | Sep 23, 11:00 | Lights down, lashes on, and the smell of tequila already in the air. 💄 |
| 109 | 2.8% | instagram | Oct 02, 19:00 | Riot mode: ACTIVATED. 🔥🤘 Revolutionary Riot Productions is turning Azu |
| 115 | 2.6% | instagram | Sep 14, 11:00 | Mark it down: Sunday, October 11 — Mosh Night takes over Azucar's Main |
| 118 | 1.7% | instagram | Sep 20, 11:00 | Disco ball spinning, glow paint glowing, bass rattling your ribcage —  |

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

