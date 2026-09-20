# Azúcar — real engagement report

_Generated 2026-09-20 09:43 PDT by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **165** published posts with metrics, of 337 marked posted in the queue
- **1711** Instagram posts and **0** Facebook posts on file
- **3** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 8 | 441 | 5.5% |
| 5-9 posts | 5 | 194 (-56%) | 2.5% |
| 10-19 posts | 69 | 149 (-66%) | 3.2% |
| 20+ posts | 83 | 129 (-71%) | 2.5% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 8 posts in the quietest bucket._

## 2. When are our followers actually online?


_No `online_followers` data yet — it needs the daily pull to have run at least once with the metric available. This is the section that replaces guessing at 11am and 7pm._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 165 | 142 | 2.8% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 165 | 142 | 2.8% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| evening | 81 | 152 | 3.1% |
| morning | 84 | 130 | 2.6% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Friday | 26 | 166 | 3.1% |
| Saturday | 29 | 155 | 3.3% |
| Sunday | 28 | 152 | 2.9% |
| Tuesday | 16 | 146 | 3.0% |
| Monday | 22 | 132 | 2.8% |
| Wednesday | 13 | 128 | 3.3% |
| Thursday | 31 | 124 | 2.2% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_the_bikini_bottoms | 4 | 252 | 7.5% |
| cadence_furanium_fever | 16 | 233 | 4.2% |
| cadence_end_of_summer_blackout_party | 12 | 184 | 2.9% |
| cadence_emo_night_drag_show_edition | 5 | 183 | 7.1% |
| cadence_industry_night_drag_show | 9 | 155 | 3.8% |
| cadence_mosh_night | 5 | 155 | 3.9% |
| cadence_dolly_parton__a_drag_tribute_night | 16 | 152 | 2.8% |
| cadence_heels_dance_class_with_frankie | 9 | 146 | 3.4% |
| cadence_american_horror_story_viewing_party_and_drag_show | 8 | 140 | 2.7% |
| cadence_night_of_kings__an_all_king_drag_show | 20 | 130 | 2.3% |
| cadence_heels_dance_class_with_kimora | 11 | 121 | 1.7% |
| cadence_vida_amore_divas_show_fiesta_patrias | 12 | 113 | 2.2% |
| cadence_sip_and_paint_with_artwithaubrey | 16 | 112 | 1.1% |
| cadence_an_open_stage_drag_debut | 11 | 112 | 2.8% |
| cadence_drag_king_kareoke | 9 | 112 | 3.8% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 1,238 | 12.8% | instagram | Aug 16, 19:00 | Tri-Cities Furs just took over Azúcar and the whole city is about to f |
| 714 | 3.1% | instagram | Sep 10, 19:00 | Summer's saying goodbye and Azucar's throwing it a Blackout Party it'l |
| 710 | 13.7% | instagram | Sep 08, 19:00 | Dust off the eyeliner and dig out those band tees — Emo Night just got |
| 615 | 8.0% | instagram | Sep 04, 19:00 | Big wigs. Bigger hearts. Backwoods Barbie energy for DAYS. 👑✨ Azúcar a |
| 571 | 4.0% | instagram | Sep 05, 11:00 | The stage is EMPTY and that's exactly the point. 🎤✨ Azúcar is throwing |
| 567 | 3.9% | instagram | Sep 08, 19:00 | Riot mode: ACTIVATED. 🔥🤘 Revolutionary Riot Productions is turning Azu |
| 518 | 5.4% | instagram | Sep 01, 19:00 | Kings take the crown tonight. 👑🔥 Night of Kings drops into the Lounge  |
| 495 | 7.9% | instagram | Aug 23, 11:00 | Mark it down: Furanium Fever hits Azúcar's Main Floor on Saturday, Sep |
| 478 | 5.4% | instagram | Sep 05, 11:00 | Grab the mic. Grab your best friend. Grab a front row seat because thi |
| 475 | 6.9% | instagram | Aug 19, 11:00 | Disco ball spinning, glow paint glowing, bass rattling your ribcage —  |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 51 | 0.0% | instagram | Sep 18, 11:00 | Heels clicking on the Main Floor. Mirror wall catching every angle. Ki |
| 66 | 0.0% | instagram | Sep 10, 11:00 | The stage is EMPTY and that's exactly the point. 🎤✨ Azúcar is throwing |
| 67 | 0.0% | instagram | Sep 09, 11:00 | Come as you are — paint-stained hands optional, good energy required.  |
| 69 | 0.0% | instagram | Sep 10, 19:00 | Dim lights, midnight-blue canvas, a moon glowing right where Aubrey te |
| 69 | 0.0% | instagram | Sep 11, 11:00 | Come as you are — paint-stained hands optional, good energy required.  |

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

