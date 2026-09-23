# Azúcar — real engagement report

_Generated 2026-09-23 10:42 PDT by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **150** published posts with metrics, of 307 marked posted in the queue
- **1733** Instagram posts and **0** Facebook posts on file
- **6** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 10 | 353 | 4.8% |
| 5-9 posts | 4 | 334 (-5%) | 4.6% |
| 10-19 posts | 86 | 154 (-57%) | 3.3% |
| 20+ posts | 50 | 144 (-59%) | 2.6% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 10 posts in the quietest bucket._

## 2. When are our followers actually online?


_No `online_followers` data yet — it needs the daily pull to have run at least once with the metric available. This is the section that replaces guessing at 11am and 7pm._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 150 | 154 | 3.1% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 150 | 154 | 3.1% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| evening | 75 | 168 | 3.2% |
| morning | 75 | 139 | 3.0% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Friday | 21 | 190 | 3.7% |
| Saturday | 23 | 181 | 3.7% |
| Sunday | 30 | 157 | 2.7% |
| Tuesday | 17 | 154 | 3.2% |
| Thursday | 26 | 140 | 2.3% |
| Wednesday | 8 | 140 | 4.4% |
| Monday | 25 | 133 | 3.0% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_the_bikini_bottoms | 5 | 263 | 6.8% |
| cadence_furanium_fever | 19 | 219 | 3.9% |
| cadence_emo_night_drag_show_edition | 6 | 204 | 8.2% |
| cadence_end_of_summer_blackout_party | 12 | 198 | 2.8% |
| cadence_mosh_night | 7 | 159 | 5.0% |
| cadence_dolly_parton__a_drag_tribute_night | 16 | 156 | 2.7% |
| cadence_industry_night_drag_show | 12 | 148 | 3.1% |
| cadence_heels_dance_class_with_frankie | 12 | 144 | 3.3% |
| cadence_american_horror_story_viewing_party_and_drag_show | 11 | 135 | 3.0% |
| cadence_vida_amore_divas_show_fiesta_patrias | 12 | 125 | 2.1% |
| cadence_heels_dance_class_with_kimora | 14 | 122 | 1.9% |
| cadence_drag_king_kareoke | 9 | 121 | 3.8% |
| cadence_an_open_stage_drag_debut | 12 | 115 | 2.6% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 1,238 | 12.8% | instagram | Aug 16, 19:00 | Tri-Cities Furs just took over Azúcar and the whole city is about to f |
| 717 | 3.1% | instagram | Sep 10, 19:00 | Summer's saying goodbye and Azucar's throwing it a Blackout Party it'l |
| 710 | 13.7% | instagram | Sep 08, 19:00 | Dust off the eyeliner and dig out those band tees — Emo Night just got |
| 615 | 8.0% | instagram | Sep 04, 19:00 | Big wigs. Bigger hearts. Backwoods Barbie energy for DAYS. 👑✨ Azúcar a |
| 583 | 3.9% | instagram | Sep 05, 11:00 | The stage is EMPTY and that's exactly the point. 🎤✨ Azúcar is throwing |
| 567 | 3.9% | instagram | Sep 08, 19:00 | Riot mode: ACTIVATED. 🔥🤘 Revolutionary Riot Productions is turning Azu |
| 495 | 7.9% | instagram | Aug 23, 11:00 | Mark it down: Furanium Fever hits Azúcar's Main Floor on Saturday, Sep |
| 478 | 5.4% | instagram | Sep 05, 11:00 | Grab the mic. Grab your best friend. Grab a front row seat because thi |
| 475 | 6.9% | instagram | Aug 19, 11:00 | Disco ball spinning, glow paint glowing, bass rattling your ribcage —  |
| 473 | 4.9% | instagram | Sep 19, 11:00 | Fog rolls across the Main Floor. Glitter catches the black-light like  |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 63 | 3.2% | instagram | Sep 22, 19:00 | Mark it down — Heels Dance Class is back on the Main Floor and Frankie |
| 64 | 0.0% | instagram | Sep 18, 11:00 | Heels clicking on the Main Floor. Mirror wall catching every angle. Ki |
| 66 | 0.0% | instagram | Sep 10, 11:00 | The stage is EMPTY and that's exactly the point. 🎤✨ Azúcar is throwing |
| 67 | 0.0% | instagram | Sep 21, 19:00 | Heads up, Pasco — Kimora is stepping onto the Main Floor and she's bri |
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

