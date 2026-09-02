# Azúcar Post Manager

A friendly website for Pedro & Jamie to see, edit, add, and delete the scheduled
social posts that live in this repo's `posts_queue.json` — without touching GitHub.

The site never posts to Instagram/Facebook itself. It only edits the queue file;
the existing `post-scheduler.yml` cron (every 15 min) does the actual posting,
exactly as before.

## How it works

```
Browser (index.html + app.js)
   │  behind Cloudflare Access (email allow-list: Google or one-time code)
   ▼
Cloudflare Pages Functions (manager/functions/)
   ├─ GET  /api/events   read posts_queue.json from GitHub → group into events
   ├─ POST /api/save     apply an edit and commit it back (root + docs mirror)
   └─ POST /api/upload   host a photo on catbox.moe (same host the pipeline uses)
   ▼
posts_queue.json on main  ←— read every 15 min by process_queue.py (unchanged)
```

Product rules (enforced in the UI **and** server-side in `api/save.js`):

- **2-hour lead time** — nothing can be scheduled sooner than now + 2h.
  Need something out immediately? Post it manually on Facebook.
- **Auto-archive** — events whose date has passed move to the read-only
  History view. Posts that already went out can never be edited or deleted.
- **Logical posts** — an IG entry and an FB entry with the same time+caption
  show as ONE post with two platform chips; the editor's IG/FB toggles
  create/remove the underlying queue entries.

Event names/dates/card colors for known campaigns live in `events_meta.json`
(key = the `campaign` value used in the queue).

## Local demo (no backend)

```
python manager/build_events.py     # regenerate events.json from the real queue
python -m http.server 8787 --directory manager
```

Without `/api/events` the app runs in DEMO mode: static `events.json`,
edits stay in memory, sample upcoming events are labeled as such.

## Deploying (one-time setup)

1. **GitHub token** (lets the Save button commit):
   github.com → Settings → Developer settings → Personal access tokens →
   Fine-grained tokens → Generate new. Repository access: *Only select
   repositories* → `Azucar-Social-Pipeline`. Permissions: *Contents:
   Read and write*. Copy the token.

2. **Cloudflare Pages project**:
   dash.cloudflare.com → Workers & Pages → Create → Pages →
   Connect to Git → pick `Azucar-Social-Pipeline`.
   - Production branch: `main`
   - Root directory: `manager`
   - Build command: *(leave empty)* · Build output directory: `.`
   Then Settings → Environment variables:
   - `GITHUB_TOKEN` = the token from step 1 (encrypt)
   - `GITHUB_REPO` = `soynopalero/Azucar-Social-Pipeline`

3. **R2 bucket** (where photos live):
   dash.cloudflare.com → R2 → Create bucket → name it `azucar-flyers`.
   - Settings → Public access: either enable the **r2.dev** subdomain, or
     (better) attach a **custom domain** such as `img.yourdomain`.
     Meta fetches the image unauthenticated at posting time, so this URL
     must NOT be behind Cloudflare Access.
   - Back in the Pages project → Settings → Bindings → add an **R2 bucket**
     binding named `PHOTOS` pointing at `azucar-flyers`.
   - Settings → Environment variables: `R2_PUBLIC_BASE` = the public base URL
     from above, e.g. `https://img.yourdomain` (no trailing path).

   Until both `PHOTOS` and `R2_PUBLIC_BASE` exist the uploader falls back to
   catbox.moe, which is what it used to do. Expect that fallback to fail:
   catbox refuses uploads from datacenter IPs (`412 Invalid uploader`), which
   is why `cadence_engine.py` hosts its flyers on GitHub Pages instead.

4. **Cloudflare Access** (the login gate):
   dash.cloudflare.com → Zero Trust → Access → Applications → Add an
   application → Self-hosted. Application domain = the Pages URL (and the
   custom domain if added). Policy: *Allow* → Include → Emails →
   Pedro's + Jamie's emails. Login methods: enable **Google** and
   **One-time PIN**.
   Copy the application's **Audience (AUD) tag**, then back in the Pages
   project add env vars:
   - `ACCESS_TEAM_DOMAIN` = `<team>.cloudflareaccess.com`
   - `ACCESS_AUD` = the AUD tag

Until step 3 is done, `_middleware.js` fails safe: reads work, writes are
refused with a clear message.

## Files

| File | What |
|---|---|
| `index.html` / `styles.css` / `app.js` | the app |
| `functions/_middleware.js` | verifies the Cloudflare Access JWT on every /api call |
| `functions/api/events.js` | live read of the queue, grouped into events |
| `functions/api/save.js` | edits → GitHub commit (2h rule enforced here too) |
| `functions/api/upload.js` | photo → R2 bucket, returns its public URL |
| `functions/lib/queue.js` | shared grouping + GitHub helpers |
| `events_meta.json` | names/dates/colors per campaign |
| `build_events.py` + `events.json` | local demo data (JS twin lives in queue.js) |
