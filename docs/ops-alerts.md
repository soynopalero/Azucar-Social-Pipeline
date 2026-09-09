# Pipeline alerts — what each one means and what to do

The pipeline is a chain of third-party services glued together by GitHub
Actions: Monday (event board) → Claude (captions) → Telegram (approval) →
GitHub Pages (flyer hosting) → Meta (Instagram/Facebook), with Eventbrite and a
Google Calendar hanging off the side. Any of them can hiccup for a minute, and
until September 2026 every hiccup failed a whole workflow and paged **both**
owners with the same vague message. This page describes the policy that
replaced that, and how to read the alerts you still get.

## Who gets what

| Message | Who | Why |
|---|---|---|
| ✅ "Eventbrite created for …", 📣 "Captions ready", 📅 "Queued N posts" | Pedro + Jayme | Things to act on or be glad about. |
| ⚠️ / 🚨 / ℹ️ failure alerts with a GitHub log link | **Pedro only** | Only the maintainer can do anything with an Actions log. Configured in one place: `.github/actions/ops-alert/action.yml`. |

## Severity at a glance

| Prefix | Meaning | Response |
|---|---|---|
| 🚨 | A post may have gone out **twice**, or may go out twice on the next run. | Look now. |
| ⚠️ | Something in the chain failed for a specific event; the message names it and says whether it self-heals. | Read the message; usually nothing to do. |
| ℹ️ | A convenience (FB kit, license snapshot) is stale. Posting unaffected. | Ignore unless it repeats for a day. |

## What does NOT alert any more

* **Google Calendar cleanup** (`gcal_sync.py`, part of the cadence engine run).
  Google's Apps Script endpoint intermittently answers a valid URL with a bare
  HTTP 404 for a minute. The step now retries, and if it still fails the run
  stays green and a note appears in the job summary. Four of the six cadence
  alerts in the first week of September 2026 were this.
* **A single Meta rejection** of one post. It stays in the queue and is
  retried on the next scheduler run (up to six cycles); the Post Manager shows
  its status. Only a crash of the scheduler itself alerts.
* **One flaky Monday response.** Every Monday call retries transient errors,
  including Monday's habit of returning HTTP 200 with an `errors` array.
* **One Eventbrite 500.** Every Eventbrite call retries. If it still fails
  after the event was created, the draft is left in place and the next run
  (every two hours, or the next Monday publish) **resumes** it — no duplicate.

## The alerts, one by one

### 🚨 Post scheduler: posts may have been PUBLISHED but the queue could not be pushed
The scheduler posted, then failed to commit `posts_queue.json` four times in a
row (GitHub down, or a conflict the merge driver could not resolve). The next
run, five minutes later, will not know those posts went out.
**Do:** open the run log, find the `✅ Posted!` lines, and mark those entries
posted in the Post Manager before the next run — or pause the Cloudflare
Worker cron for a few minutes while you do.

### ⚠️ Cadence engine: caption drafting/queueing failed for at least one event
The `ERROR` line in the log names the event and the cause (model returned no
parseable captions, Monday write failed, flyer download failed). Other events
in the same run were still processed. The daily run retries tomorrow.
**Do:** nothing, unless the same event fails two days running — then read the
error.

### ⚠️ Cadence engine / Flyer sync: output could not be pushed to main
Everything ran (captions were sent to Telegram, queue entries were created in
memory) but the commit did not land. Approvals still work; queued posts from
this run are missing.
**Do:** re-run the "Cadence engine (live)" workflow from the Actions tab. It is
idempotent — already-drafted events are skipped, approved events are queued.

### ⚠️ Flyer sync: the new flyers did NOT reach Monday
Telegram → Monday shuttle failed before uploading. The event's flyers are
unchanged.
**Do:** once the log makes sense, ask the sender to `/update` again.

### ⚠️ Eventbrite auto-create: N event(s) not published this run
Sent by the script itself, naming the event and the first line of the error.
If the message says "Eventbrite server error — nothing to do", it is exactly
that: the draft stays on Eventbrite and the next run finishes it.
**Do:** nothing for server errors. For anything else (a 400 naming a field),
fix the Monday item — usually a missing time, an emoji-only name, or a flyer
that is not an image.

### ℹ️ FB Event Kit refresh failed
The copy-paste kit page may be up to 30 minutes stale. It runs 48 times a day.
**Do:** nothing.

## Why things are wired the way they are

* **`posts_queue.json` is merged by entry id**, not by text
  (`code/merge_queue.py`, registered through `.gitattributes`). The scheduler
  marks posts posted every five minutes while the cadence engine adds entries;
  before, they shared one GitHub concurrency group so they could never touch
  the file at the same time, and GitHub silently cancelled queued runs in that
  group (the daily cadence pass was dropped four times in Aug–Sep 2026). Now
  each has its own group and a race resolves to "posted marker wins, new
  entries survive, deletions stick".
* **The Cloudflare Worker** (`workers/scheduler-cron`) is what makes posts
  punctual; GitHub's own cron is a backstop that runs hours late. If posts
  start landing hours late again, check the Worker first (its token expires).
* **Every external call retries** with backoff, once, in one place per
  service: `monday_api.monday_query`, `process_queue.graph_post`,
  `monday_to_eventbrite.eb_call`, `gcal_sync._open_with_retry`. A new script
  should use those rather than calling the API directly.
