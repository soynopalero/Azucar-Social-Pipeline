# Publishing the SOP

The page must be **public with no login** — someone reads it standing at the
tank, and that person may not be a Pedro or Jamie yet.

## Not the existing Pages project

`azucar-post-manager` cannot host this. Two reasons, both fatal:

- Its **root directory is `manager`**, so nothing under `tools/` is served.
- It sits behind a **Cloudflare Access** application, an email allow-list.
  Anyone not on that list gets a login wall instead of the procedure.

## A second Pages project

Same account, same repo, different settings. Mirrors the manager's setup in
`manager/README.md` minus the login gate.

1. dash.cloudflare.com → Workers & Pages → Create → Pages →
   Connect to Git → pick `Azucar-Social-Pipeline`.
   - Production branch: `main`
   - **Root directory:** `tools/aquarium/sop`
   - Build command: *(leave empty)* · Build output directory: `.`
2. **Do not** add an Access application in front of it. This is the whole
   point — skip step 3 of the manager's instructions, don't adapt it.
3. Open the deployed URL **in a private window**. If it asks you to sign in,
   an Access policy is catching it and the page is useless to the person it
   was written for. An auth bounce is invisible when you are already logged in,
   which is why this check has to be a private window rather than a glance.

If the SOP moves to its own repo, the settings are identical except the root
directory becomes `.`.

## Clips

Once his footage is cut in, `clips/` and `frames/` sit beside `index.html`
and deploy with it — no configuration changes. Cloudflare Pages caps a single
file at roughly 25 MiB, so keep clips short and per-step. Worth confirming
against current Cloudflare docs before cutting a long one.
