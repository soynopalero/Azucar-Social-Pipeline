# azucar-scheduler-cron

A Cloudflare Worker that triggers `post-scheduler.yml` on time.

## Why this exists

GitHub's `schedule:` cron is **best-effort on every plan, including paid ones**.
Scheduled workflows get deprioritised under load and can be dropped outright.
There is no tier that buys punctuality, and this repo is public, so Actions
minutes are already unlimited and free — nothing here is a quota problem.

Measured on this repo, across 146 posts since 2026-08-25:

| | |
|---|---|
| median lateness | **2h 20m** |
| on time (< 20 min) | 14 of 146 |
| over 1h late | 114 of 146 |
| over 3h late | 54 of 146 |
| worst | **7.8 hours** |

A 7 PM Saturday post going out at 11 PM is, for a bar, a post that did not run.

Cloudflare cron triggers do fire on schedule, so this Worker pokes the workflow
through `workflow_dispatch`. **Nothing else changes** — same workflow, same
Python, same queue. This only decides *when* it runs.

Expect **under 5 minutes**, not to-the-second: ~5 min cron granularity plus
~40s of GitHub runner startup.

## Setup

### 1. Create a GitHub token

A **fine-grained** personal access token, scoped as narrowly as this:

- Repository access: **Only select repositories** → `soynopalero/Azucar-Social-Pipeline`
- Permissions: **Actions → Read and write**. Nothing else.
- Expiry: your call, but note that **when it expires, posts silently go back to
  being hours late.** Put the renewal date in a calendar. The Worker logs a 401
  with a pointed message, but nobody reads Worker logs unprompted.

This token can start workflow runs in one repo. It cannot read your code, push
commits, or touch any other repo.

### 2. Deploy

```sh
cd workers/scheduler-cron
npx wrangler deploy
npx wrangler secret put GH_DISPATCH_TOKEN   # paste the token when prompted
```

The secret is stored by Cloudflare, not in this repo. It is not in
`wrangler.toml` and must never be.

### 3. Confirm it works

```sh
curl https://azucar-scheduler-cron.<your-subdomain>.workers.dev
```

Expect `token_configured: true`. This endpoint reports status only — it never
triggers a run, because a public URL that fires posts is a URL anyone can fire.

Then watch a real cron fire:

```sh
npx wrangler tail
```

Within five minutes you should see a `dispatched post-scheduler.yml` line, and
a matching `workflow_dispatch` run in the repo's Actions tab.

## Checking it is still working

The honest failure mode is silence: if this Worker stops, nothing breaks
loudly — posts just drift back to hours late, exactly as before, and it may be
days before anyone notices.

Two ways to check:

- Cloudflare dashboard → Workers → `azucar-scheduler-cron` → the cron trigger's
  success rate.
- The repo's Actions tab: post-scheduler runs should show `workflow_dispatch`
  every ~5 minutes, not `schedule` every few hours.

## Notes

- The repo's own `schedule:` block stays in place as a backstop. A duplicate
  trigger is harmless: the workflow's concurrency group serialises runs, and a
  run with nothing due exits in seconds without committing.
- The Worker dispatches unconditionally rather than checking the queue first.
  Parsing a 0.65 MB queue every five minutes is an awkward fit for the free
  tier's 10ms CPU budget, and `process_queue.py` already no-ops cheaply. Fewer
  moving parts in the thing that makes posts punctual.
- Cron expressions here are **UTC**, like GitHub's.
