# Azúcar — real engagement report

_Generated 2026-09-22 10:35 PDT by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **144** published posts with metrics, of 295 marked posted in the queue
- **1727** Instagram posts and **0** Facebook posts on file
- **5** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 10 | 353 | 4.8% |
| 5-9 posts | 4 | 334 (-5%) | 4.6% |
| 10-19 posts | 80 | 147 (-58%) | 3.3% |
| 20+ posts | 50 | 142 (-60%) | 2.6% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 10 posts in the quietest bucket._

## 2. When are our followers actually online?


_No `online_followers` data yet — it needs the daily pull to have run at least once with the metric available. This is the section that replaces guessing at 11am and 7pm._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 144 | 150 | 3.2% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 144 | 150 | 3.2% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| evening | 71 | 158 | 3.3% |
| morning | 73 | 135 | 3.1% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Friday | 21 | 190 | 3.7% |
| Saturday | 23 | 179 | 3.7% |
| Sunday | 30 | 154 | 2.8% |
| Tuesday | 11 | 153 | 2.7% |
| Wednesday | 8 | 140 | 4.4% |
| Thursday | 26 | 139 | 2.3% |
| Monday | 25 | 124 | 3.4% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_the_bikini_bottoms | 5 | 259 | 6.2% |
| cadence_furanium_fever | 18 | 227 | 3.8% |
| cadence_emo_night_drag_show_edition | 6 | 204 | 8.5% |
| cadence_end_of_summer_blackout_party | 12 | 194 | 2.8% |
| cadence_mosh_night | 7 | 157 | 5.1% |
| cadence_dolly_parton__a_drag_tribute_night | 16 | 155 | 2.7% |
| cadence_heels_dance_class_with_frankie | 11 | 149 | 3.4% |
| cadence_industry_night_drag_show | 11 | 149 | 3.0% |
| cadence_american_horror_story_viewing_party_and_drag_show | 10 | 146 | 3.3% |
| cadence_vida_amore_divas_show_fiesta_patrias | 12 | 122 | 2.1% |
| cadence_heels_dance_class_with_kimora | 13 | 122 | 1.6% |
| cadence_drag_king_kareoke | 9 | 120 | 3.8% |
| cadence_an_open_stage_drag_debut | 12 | 115 | 2.6% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 1,238 | 12.8% | instagram | Aug 16, 19:00 | Tri-Cities Furs just took over Azúcar and the whole city is about to f |
| 717 | 3.1% | instagram | Sep 10, 19:00 | Summer's saying goodbye and Azucar's throwing it a Blackout Party it'l |
| 710 | 13.7% | instagram | Sep 08, 19:00 | Dust off the eyeliner and dig out those band tees — Emo Night just got |
| 615 | 8.0% | instagram | Sep 04, 19:00 | Big wigs. Bigger hearts. Backwoods Barbie energy for DAYS. 👑✨ Azúcar a |
| 580 | 4.0% | instagram | Sep 05, 11:00 | The stage is EMPTY and that's exactly the point. 🎤✨ Azúcar is throwing |
| 567 | 3.9% | instagram | Sep 08, 19:00 | Riot mode: ACTIVATED. 🔥🤘 Revolutionary Riot Productions is turning Azu |
| 495 | 7.9% | instagram | Aug 23, 11:00 | Mark it down: Furanium Fever hits Azúcar's Main Floor on Saturday, Sep |
| 478 | 5.4% | instagram | Sep 05, 11:00 | Grab the mic. Grab your best friend. Grab a front row seat because thi |
| 475 | 6.9% | instagram | Aug 19, 11:00 | Disco ball spinning, glow paint glowing, bass rattling your ribcage —  |
| 455 | 8.8% | instagram | Sep 11, 19:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 53 | 0.0% | instagram | Sep 21, 19:00 | Heads up, Pasco — Kimora is stepping onto the Main Floor and she's bri |
| 61 | 0.0% | instagram | Sep 18, 11:00 | Heels clicking on the Main Floor. Mirror wall catching every angle. Ki |
| 66 | 0.0% | instagram | Sep 10, 11:00 | The stage is EMPTY and that's exactly the point. 🎤✨ Azúcar is throwing |
| 74 | 2.7% | instagram | Sep 20, 11:00 | Mark it down. 📌 Kimora is teaching an intermediate-advanced heels chor |
| 80 | 2.5% | instagram | Sep 19, 11:00 | The stage is EMPTY and that's exactly the point. 🎤✨ Azúcar is throwing |

## Metrics this API version no longer returns

Listed so a missing number is never mistaken for a zero:

- `comments`
- `follows`
- `impressions`
- `likes`
- `plays`
- `profile_visits`
- `reach`
- `saved`
- `shares`
- `total_interactions`
- `views`

