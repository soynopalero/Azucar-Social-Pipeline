# Azúcar — real engagement report

_Generated 2026-09-28 13:03 PDT by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **115** published posts with metrics, of 250 marked posted in the queue
- **1762** Instagram posts and **1317** Facebook posts on file
- **11** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 21 | 220 | 3.9% |
| 5-9 posts | 16 | 204 (-7%) | 3.8% |
| 10-19 posts | 78 | 171 (-22%) | 2.5% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 21 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,032 |
| 19:00 | 1,024 |
| 18:00 | 1,019 |
| 17:00 | 1,006 |
| 16:00 | 1,003 |
| 15:00 | 995 |
| 21:00 | 992 |
| 12:00 | 979 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 115 | 178 | 3.0% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 115 | 178 | 3.0% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| evening | 56 | 182 | 2.8% |
| morning | 59 | 164 | 3.1% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Saturday | 16 | 218 | 3.8% |
| Tuesday | 10 | 215 | 2.4% |
| Friday | 17 | 208 | 3.7% |
| Wednesday | 11 | 176 | 2.3% |
| Sunday | 22 | 176 | 2.6% |
| Thursday | 21 | 170 | 2.2% |
| Monday | 18 | 138 | 2.9% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_scream_queens_drag_show | 4 | 387 | 5.6% |
| cadence_the_bikini_bottoms | 8 | 228 | 5.2% |
| cadence_emo_night_drag_show_edition | 9 | 224 | 5.6% |
| cadence_furanium_fever | 23 | 220 | 3.6% |
| cadence_american_horror_story_viewing_party_and_drag_show | 13 | 179 | 2.2% |
| cadence_industry_night_drag_show | 17 | 170 | 2.4% |
| cadence_mosh_night | 10 | 163 | 4.0% |
| cadence_heels_dance_class_with_frankie | 14 | 156 | 2.3% |
| cadence_heels_dance_class_with_kimora | 16 | 132 | 2.0% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 1,238 | 12.8% | instagram | Aug 16, 19:00 | Tri-Cities Furs just took over Azúcar and the whole city is about to f |
| 804 | 2.0% | instagram | Sep 23, 11:00 | American Horror Story is BACK and Azucar's throwing the kickoff party  |
| 710 | 13.7% | instagram | Sep 08, 19:00 | Dust off the eyeliner and dig out those band tees — Emo Night just got |
| 567 | 3.9% | instagram | Sep 08, 19:00 | Riot mode: ACTIVATED. 🔥🤘 Revolutionary Riot Productions is turning Azu |
| 498 | 4.6% | instagram | Sep 19, 11:00 | Fog rolls across the Main Floor. Glitter catches the black-light like  |
| 495 | 7.9% | instagram | Aug 23, 11:00 | Mark it down: Furanium Fever hits Azúcar's Main Floor on Saturday, Sep |
| 475 | 6.9% | instagram | Aug 19, 11:00 | Disco ball spinning, glow paint glowing, bass rattling your ribcage —  |
| 456 | 8.8% | instagram | Sep 11, 19:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 426 | 2.3% | instagram | Sep 25, 19:00 | However you show up — fursuit, glitter, streetwear, or something in be |
| 407 | 4.4% | instagram | Aug 30, 19:00 | However you show up — fursuit, glitter, streetwear, or something in be |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 46 | 8.7% | instagram | Sep 28, 11:00 | You feel it before you hear it — floor vibrating, chests thumping, swe |
| 63 | 1.6% | instagram | Sep 28, 11:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 72 | 0.0% | instagram | Sep 18, 11:00 | Heels clicking on the Main Floor. Mirror wall catching every angle. Ki |
| 87 | 0.0% | instagram | Sep 21, 19:00 | Heads up, Pasco — Kimora is stepping onto the Main Floor and she's bri |
| 89 | 0.0% | instagram | Sep 23, 11:00 | Lights down, lashes on, and the smell of tequila already in the air. 💄 |

## Metrics this API version no longer returns

Listed so a missing number is never mistaken for a zero:

- `comments`
- `follows`
- `impressions`
- `likes`
- `plays`
- `post_engaged_users`
- `post_impressions`
- `post_impressions_unique`
- `profile_visits`
- `reach`
- `saved`
- `shares`
- `total_interactions`
- `views`

