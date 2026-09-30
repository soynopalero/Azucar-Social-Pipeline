# Azúcar — real engagement report

_Generated 2026-09-30 11:19 PDT by `code/analyze_insights.py`. Numbers come from the Meta Graph API, joined to `posts_queue.json`._

## What this is built on

- **118** published posts with metrics, of 268 marked posted in the queue
- **1767** Instagram posts and **1322** Facebook posts on file
- **13** daily account snapshots

## 1. Does posting more cost us reach?

The reason we paused. Every published post, labelled with how many posts went out that same day across all events:

| Posts that day (all events) | Posts measured | Median reach | Median eng. rate |
|---|---:|---:|---:|
| 1-4 posts | 21 | 220 | 3.9% |
| 5-9 posts | 16 | 211 (-4%) | 3.8% |
| 10-19 posts | 81 | 178 (-19%) | 2.4% |

_Read the first row as the baseline: what a post does on a quiet day. If the busy rows sit well below it, the flyers are eating each other. Based on 21 posts in the quietest bucket._

## 2. When are our followers actually online?


| Hour (Pacific) | Followers online (avg) |
|---|---:|
| 20:00 | 1,034 |
| 19:00 | 1,029 |
| 18:00 | 1,022 |
| 17:00 | 1,010 |
| 16:00 | 1,004 |
| 15:00 | 996 |
| 21:00 | 995 |
| 12:00 | 982 |

_Peak: **20:00**. Current slots are 11:00 and 19:00._

## 3. What performs


### Platform

| Platform | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| instagram | 118 | 184 | 3.0% |


### Media type

| Media type | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| FEED | 118 | 184 | 3.0% |


### Time slot

| Time slot | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| evening | 58 | 188 | 2.6% |
| morning | 60 | 169 | 3.1% |


### Day of week

| Day of week | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| Saturday | 16 | 220 | 3.9% |
| Friday | 17 | 220 | 3.7% |
| Tuesday | 12 | 198 | 2.4% |
| Wednesday | 11 | 184 | 2.2% |
| Sunday | 22 | 181 | 2.5% |
| Thursday | 21 | 173 | 2.2% |
| Monday | 19 | 149 | 2.6% |


### Campaign

| Campaign | Posts | Median reach | Median eng. rate |
|---|---:|---:|---:|
| cadence_scream_queens_drag_show | 5 | 391 | 4.6% |
| cadence_the_bikini_bottoms | 8 | 242 | 4.9% |
| cadence_furanium_fever | 23 | 220 | 3.6% |
| cadence_emo_night_drag_show_edition | 10 | 206 | 4.9% |
| cadence_american_horror_story_viewing_party_and_drag_show | 13 | 181 | 2.2% |
| cadence_industry_night_drag_show | 17 | 176 | 2.4% |
| cadence_mosh_night | 10 | 172 | 3.8% |
| cadence_heels_dance_class_with_frankie | 14 | 162 | 2.3% |
| cadence_heels_dance_class_with_kimora | 16 | 132 | 1.9% |


## 4. Ten best posts we have ever published

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 1,238 | 12.8% | instagram | Aug 16, 19:00 | Tri-Cities Furs just took over Azúcar and the whole city is about to f |
| 811 | 2.0% | instagram | Sep 23, 11:00 | American Horror Story is BACK and Azucar's throwing the kickoff party  |
| 710 | 13.7% | instagram | Sep 08, 19:00 | Dust off the eyeliner and dig out those band tees — Emo Night just got |
| 567 | 3.9% | instagram | Sep 08, 19:00 | Riot mode: ACTIVATED. 🔥🤘 Revolutionary Riot Productions is turning Azu |
| 499 | 4.6% | instagram | Sep 19, 11:00 | Fog rolls across the Main Floor. Glitter catches the black-light like  |
| 495 | 7.9% | instagram | Aug 23, 11:00 | Mark it down: Furanium Fever hits Azúcar's Main Floor on Saturday, Sep |
| 479 | 2.1% | instagram | Sep 25, 19:00 | However you show up — fursuit, glitter, streetwear, or something in be |
| 475 | 6.9% | instagram | Aug 19, 11:00 | Disco ball spinning, glow paint glowing, bass rattling your ribcage —  |
| 461 | 4.1% | instagram | Sep 25, 11:00 | Here's everything you need to know: Scream Queens Drag Show hits Azuca |
| 456 | 8.8% | instagram | Sep 11, 19:00 | Grab your pineapple, we're diving deep tonight 🍍🌊 Azucar's Main Floor  |

### And the five worst

| Reach | Eng. rate | Platform | When | Opening line |
|---:|---:|---|---|---|
| 73 | 0.0% | instagram | Sep 18, 11:00 | Heels clicking on the Main Floor. Mirror wall catching every angle. Ki |
| 92 | 1.1% | instagram | Sep 10, 11:00 | Mark it down. 📌 Kimora is teaching an intermediate-advanced heels chor |
| 95 | 0.0% | instagram | Sep 23, 11:00 | Lights down, lashes on, and the smell of tequila already in the air. 💄 |
| 96 | 5.2% | instagram | Sep 07, 11:00 | Sunday's your night off — so hand it over to Azúcar. 🍹👑 Industry Night |
| 97 | 0.0% | instagram | Sep 21, 19:00 | Heads up, Pasco — Kimora is stepping onto the Main Floor and she's bri |

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

