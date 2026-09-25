# Azúcar — real engagement report

_Generated 2026-09-25 10:51 PDT by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **138** published posts with metrics, of 283 marked posted in the queue
- **1746** Instagram posts and **1302** Facebook posts on file
- **8** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 10 | 353 | 4.8% |
| 5-9 posts | 22 | 170 (-52%) | 3.5% |
| 10-19 posts | 75 | 151 (-57%) | 2.6% |
| 20+ posts | 31 | 147 (-58%) | 2.6% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 10 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,032 |
| 19:00 | 1,025 |
| 18:00 | 1,020 |
| 17:00 | 1,006 |
| 16:00 | 1,000 |
| 15:00 | 995 |
| 21:00 | 994 |
| 14:00 | 976 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 138 | 154 | 2.9% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 138 | 154 | 2.9% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| evening | 68 | 166 | 2.8% |
| morning | 70 | 150 | 2.9% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Friday | 17 | 193 | 3.7% |
| Tuesday | 14 | 190 | 2.4% |
| Saturday | 19 | 185 | 3.8% |
| Sunday | 25 | 163 | 2.5% |
| Wednesday | 13 | 150 | 3.3% |
| Thursday | 29 | 135 | 2.5% |
| Monday | 21 | 128 | 2.9% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_the_bikini_bottoms | 6 | 246 | 6.9% |
| cadence_emo_night_drag_show_edition | 7 | 224 | 7.1% |
| cadence_furanium_fever | 21 | 212 | 3.9% |
| cadence_end_of_summer_blackout_party | 12 | 202 | 2.8% |
| cadence_american_horror_story_viewing_party_and_drag_show | 13 | 166 | 2.3% |
| cadence_mosh_night | 8 | 163 | 4.2% |
| cadence_industry_night_drag_show | 14 | 152 | 2.7% |
| cadence_heels_dance_class_with_frankie | 14 | 144 | 2.6% |
| cadence_vida_amore_divas_show_fiesta_patrias | 12 | 126 | 2.1% |
| cadence_heels_dance_class_with_kimora | 16 | 124 | 2.2% |
| cadence_an_open_stage_drag_debut | 12 | 115 | 2.6% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 1,238 | 12.8% | instagram | Aug 16, 19:00 | Tri-Cities Furs just took over Azúcar and the whole city is about to f |
| 728 | 2.2% | instagram | Sep 23, 11:00 | American Horror Story is BACK and Azucar's throwing the kickoff party  |
| 717 | 3.1% | instagram | Sep 10, 19:00 | Summer's saying goodbye and Azucar's throwing it a Blackout Party it'l |
| 710 | 13.7% | instagram | Sep 08, 19:00 | Dust off the eyeliner and dig out those band tees — Emo Night just got |
| 583 | 3.9% | instagram | Sep 05, 11:00 | The stage is EMPTY and that's exactly the point. 🎤✨ Azúcar is throwing |
| 567 | 3.9% | instagram | Sep 08, 19:00 | Riot mode: ACTIVATED. 🔥🤘 Revolutionary Riot Productions is turning Azu |
| 495 | 7.9% | instagram | Aug 23, 11:00 | Mark it down: Furanium Fever hits Azúcar's Main Floor on Saturday, Sep |
| 485 | 4.7% | instagram | Sep 19, 11:00 | Fog rolls across the Main Floor. Glitter catches the black-light like  |
| 475 | 6.9% | instagram | Aug 19, 11:00 | Disco ball spinning, glow paint glowing, bass rattling your ribcage —  |
| 456 | 8.8% | instagram | Sep 11, 19:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 65 | 0.0% | instagram | Sep 18, 11:00 | Heels clicking on the Main Floor. Mirror wall catching every angle. Ki |
| 66 | 0.0% | instagram | Sep 10, 11:00 | The stage is EMPTY and that's exactly the point. 🎤✨ Azúcar is throwing |
| 70 | 0.0% | instagram | Sep 23, 11:00 | Lights down, lashes on, and the smell of tequila already in the air. 💄 |
| 78 | 0.0% | instagram | Sep 21, 19:00 | Heads up, Pasco — Kimora is stepping onto the Main Floor and she's bri |
| 80 | 2.5% | instagram | Sep 19, 11:00 | The stage is EMPTY and that's exactly the point. 🎤✨ Azúcar is throwing |

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

