# Azúcar — real engagement report

_Generated 2026-09-26 09:58 PDT by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **130** published posts with metrics, of 266 marked posted in the queue
- **1753** Instagram posts and **1308** Facebook posts on file
- **9** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 10 | 353 | 4.8% |
| 5-9 posts | 33 | 159 (-55%) | 3.3% |
| 10-19 posts | 87 | 148 (-58%) | 2.5% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 10 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,034 |
| 19:00 | 1,026 |
| 18:00 | 1,019 |
| 17:00 | 1,006 |
| 16:00 | 1,000 |
| 15:00 | 994 |
| 21:00 | 994 |
| 14:00 | 977 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 130 | 158 | 2.9% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 130 | 158 | 2.9% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| evening | 64 | 164 | 2.8% |
| morning | 66 | 153 | 2.9% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Friday | 19 | 190 | 3.7% |
| Tuesday | 13 | 180 | 2.2% |
| Saturday | 17 | 176 | 3.9% |
| Sunday | 23 | 163 | 2.5% |
| Wednesday | 13 | 151 | 3.3% |
| Thursday | 26 | 146 | 2.2% |
| Monday | 19 | 126 | 2.8% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_scream_queens_drag_show | 4 | 318 | 6.4% |
| cadence_the_bikini_bottoms | 7 | 237 | 6.7% |
| cadence_emo_night_drag_show_edition | 7 | 224 | 7.1% |
| cadence_furanium_fever | 22 | 220 | 3.7% |
| cadence_american_horror_story_viewing_party_and_drag_show | 13 | 167 | 2.3% |
| cadence_mosh_night | 8 | 164 | 4.1% |
| cadence_industry_night_drag_show | 15 | 155 | 2.5% |
| cadence_heels_dance_class_with_frankie | 14 | 148 | 2.5% |
| cadence_vida_amore_divas_show_fiesta_patrias | 12 | 128 | 2.1% |
| cadence_heels_dance_class_with_kimora | 16 | 127 | 2.1% |
| cadence_an_open_stage_drag_debut | 12 | 116 | 2.6% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 1,238 | 12.8% | instagram | Aug 16, 19:00 | Tri-Cities Furs just took over Azúcar and the whole city is about to f |
| 783 | 2.0% | instagram | Sep 23, 11:00 | American Horror Story is BACK and Azucar's throwing the kickoff party  |
| 710 | 13.7% | instagram | Sep 08, 19:00 | Dust off the eyeliner and dig out those band tees — Emo Night just got |
| 583 | 3.9% | instagram | Sep 05, 11:00 | The stage is EMPTY and that's exactly the point. 🎤✨ Azúcar is throwing |
| 567 | 3.9% | instagram | Sep 08, 19:00 | Riot mode: ACTIVATED. 🔥🤘 Revolutionary Riot Productions is turning Azu |
| 495 | 7.9% | instagram | Aug 23, 11:00 | Mark it down: Furanium Fever hits Azúcar's Main Floor on Saturday, Sep |
| 489 | 4.7% | instagram | Sep 19, 11:00 | Fog rolls across the Main Floor. Glitter catches the black-light like  |
| 475 | 6.9% | instagram | Aug 19, 11:00 | Disco ball spinning, glow paint glowing, bass rattling your ribcage —  |
| 456 | 8.8% | instagram | Sep 11, 19:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |
| 407 | 4.4% | instagram | Aug 30, 19:00 | However you show up — fursuit, glitter, streetwear, or something in be |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 66 | 0.0% | instagram | Sep 10, 11:00 | The stage is EMPTY and that's exactly the point. 🎤✨ Azúcar is throwing |
| 67 | 0.0% | instagram | Sep 18, 11:00 | Heels clicking on the Main Floor. Mirror wall catching every angle. Ki |
| 77 | 0.0% | instagram | Sep 23, 11:00 | Lights down, lashes on, and the smell of tequila already in the air. 💄 |
| 80 | 2.5% | instagram | Sep 19, 11:00 | The stage is EMPTY and that's exactly the point. 🎤✨ Azúcar is throwing |
| 82 | 0.0% | instagram | Sep 21, 19:00 | Heads up, Pasco — Kimora is stepping onto the Main Floor and she's bri |

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

