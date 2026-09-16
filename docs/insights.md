# Engagement insights — how it works, and why we are not paying for it

## The short version

Metricool, Later, Hootsuite, Buffer and Sprout all read the **same free Meta
Graph API this repo already has a token for**. None of them have special
access. What you pay them for is *memory*, a UI, and the other networks.

We already have the token (`FB_PAGE_ACCESS_TOKEN`, a never-expiring Page
token, already a GitHub Actions secret and already used every day by the post
scheduler). So the access half is free. This is the memory half.

## What they actually sell

When you connect Instagram to Metricool, you do an OAuth handshake that hands
them a Page access token for your account — the same kind of token we hold.
From then on they call:

| What they show you | Where it comes from |
|---|---|
| Post likes / comments / reach / saves | `GET /{ig-media-id}/insights` |
| Your post list | `GET /{ig-user-id}/media` |
| Follower count, profile visits, reach | `GET /{ig-user-id}/insights` |
| **"Best time to post" heatmap** | `GET /{ig-user-id}/insights?metric=online_followers` |
| Audience age / gender / city | `follower_demographics` with a breakdown |
| Facebook page + post numbers | `GET /{page-id}/insights`, `GET /{post-id}/insights` |

That is the whole trick. There is no scraping and no private data feed.

**The one thing they have that we cannot buy back later:** Meta's account-level
insights are a short rolling window. `online_followers` — the hour-by-hour
"when is our audience actually awake" metric, the one that should decide our
posting times — covers roughly the **last 30 days**. Once a day falls out of
that window it is gone permanently, for them and for us. A tool that has been
snapshotting daily since 2024 can draw a two-year trend that is genuinely
unrecoverable from the API today.

So their real product is a database that started early and never missed a day.
**Running `insights-pull.yml` on its cron IS the build.** Everything else here
is a few hundred lines of Python.

## What we get that they cannot

Metricool sees a post. We see *why we sent it*. Because `posts_queue.json`
records the campaign, the slot, the platform and the caption for every entry,
`analyze_insights.py` can join our scheduling decisions onto their numbers and
answer questions no generic dashboard can:

- Does reach drop on days we publish twenty posts instead of four?
  (The question that made us pause. See section 1 of the report.)
- Does the 11am slot or the 7pm slot actually do better *for us*?
- Which event types earn their promo, and which are being over-posted?

## What we give up

Being straight about the trade:

- **Only Meta.** No TikTok, no YouTube, no Google Business Profile. Each is a
  separate API and a separate build.
- **Maintenance.** Meta retires metrics on nearly every version bump
  (`impressions` became `views`; Reels `plays` folded into `views`).
  `insights_api.py` degrades past dead metrics and reports them rather than
  printing zeros, but a major version bump is still a morning's work. This is
  the real cost, and it is paid in attention, not dollars.
- **No app.** The output is a markdown report in the repo, not a phone
  dashboard.
- **No competitor tracking.** Meta exposes a limited `business_discovery`
  edge for public accounts; not built here.

For one venue on two Meta platforms, with the token and pipeline already in
hand, this is worth doing ourselves. If TikTok becomes a real channel, revisit
the maths — that is the point where a paid tool starts earning its fee.

## Files

| File | Job |
|---|---|
| `code/insights_api.py` | Graph API client; survives Meta's metric renames |
| `code/pull_insights.py` | Pulls and stores; `--selftest` runs offline |
| `code/analyze_insights.py` | Joins to `posts_queue.json`, writes the report |
| `.github/workflows/insights-pull.yml` | Daily 6am PT cron + manual run button |
| `data/insights/` | The history. **This is the asset.** Do not delete. |
| `docs/insights-report.md` | Generated report |

## Running it

Daily on its own at 6am Pacific. To run it now: Actions → **Pull engagement
insights** → Run workflow.

```bash
python code/pull_insights.py --selftest     # offline, no token needed
python code/pull_insights.py --skip-media   # daily rows only, fast
python code/analyze_insights.py --print
```

## Public repo warning

This repo is public, and this workflow commits engagement data to it. Likes and
comments are already public on the posts themselves — but **reach, follower
counts and follower demographics are not**, and a competitor could read them.

If that is not wanted, add `data/insights/` to `.gitignore` and deliver the
report to Telegram instead, the way `docs/sales-report.md` handles revenue.
Flagging it rather than deciding it quietly.
