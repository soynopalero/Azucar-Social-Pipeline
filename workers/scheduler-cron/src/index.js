/* Punctual trigger for the post scheduler.
 *
 * GitHub's `schedule:` cron is best-effort on every plan. On this repo it has
 * been running every 2-4 hours against a 15-minute schedule, so posts land a
 * median of 2h20m after their slot — a 7 PM Saturday post going out at 11 PM. That is
 * not a quota you can pay to raise; scheduled workflows are simply
 * deprioritised under load and can be dropped outright.
 *
 * Cloudflare cron triggers do fire on time, so this Worker just pokes the
 * workflow through workflow_dispatch. The workflow, the Python, and the queue
 * are all unchanged — this only decides *when* they run.
 *
 * It dispatches unconditionally rather than checking whether a post is due:
 *   - parsing the queue would cost CPU this Worker does not need to spend, and
 *     the free tier's 10ms budget is not a comfortable fit for a 0.65 MB JSON
 *     parse every five minutes;
 *   - process_queue.py already exits in seconds when nothing is due, and the
 *     workflow only commits when something changed;
 *   - fewer moving parts here means fewer ways for the thing that makes posts
 *     punctual to itself become the broken part.
 *
 * The repo's own `schedule:` block stays as a backstop. A duplicate trigger is
 * harmless: the workflow's concurrency group serialises runs, and a run with
 * nothing due is a no-op.
 */

const GITHUB_API = "https://api.github.com";

const DEFAULTS = {
  repo: "soynopalero/Azucar-Social-Pipeline",
  workflow: "post-scheduler.yml",
  ref: "main",
};

export function dispatchUrl(repo, workflow) {
  return `${GITHUB_API}/repos/${repo}/actions/workflows/${workflow}/dispatches`;
}

export function config(env = {}) {
  return {
    repo: env.GITHUB_REPO || DEFAULTS.repo,
    workflow: env.WORKFLOW_FILE || DEFAULTS.workflow,
    ref: env.WORKFLOW_REF || DEFAULTS.ref,
  };
}

async function dispatch(env) {
  if (!env.GH_DISPATCH_TOKEN) {
    // Fail loudly. A Worker that silently does nothing looks identical to the
    // problem it was deployed to fix.
    throw new Error("GH_DISPATCH_TOKEN is not set — run: wrangler secret put GH_DISPATCH_TOKEN");
  }
  const { repo, workflow, ref } = config(env);

  const res = await fetch(dispatchUrl(repo, workflow), {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.GH_DISPATCH_TOKEN}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "azucar-scheduler-cron",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ ref }),
  });

  // GitHub answers 204 No Content on success.
  if (res.status === 204) return { ok: true, status: 204 };

  const body = await res.text().catch(() => "");
  throw new Error(
    `workflow_dispatch failed: ${res.status} ${body.slice(0, 300)}` +
    (res.status === 401 || res.status === 403
      ? " — check GH_DISPATCH_TOKEN has Actions: write on this repo and has not expired"
      : "")
  );
}

export default {
  async scheduled(event, env, ctx) {
    // Throwing marks the invocation failed, which is what surfaces in the
    // Cloudflare dashboard and in `wrangler tail`. Swallowing it would hide
    // exactly the outage this Worker exists to prevent.
    ctx.waitUntil(
      dispatch(env).then(
        () => console.log(`dispatched ${config(env).workflow} @ ${new Date().toISOString()}`),
        (err) => {
          console.error(String(err));
          throw err;
        }
      )
    );
  },

  // Deliberately does NOT dispatch: this URL is public, and a trigger anyone
  // can pull is a trigger anyone can pull. It only reports what is configured,
  // so you can confirm a deploy without opening the dashboard.
  async fetch(request, env) {
    const { repo, workflow, ref } = config(env);
    return new Response(
      JSON.stringify(
        {
          ok: true,
          worker: "azucar-scheduler-cron",
          dispatches: { repo, workflow, ref },
          token_configured: Boolean(env.GH_DISPATCH_TOKEN),
          note: "Cron-driven. This endpoint reports status only and never triggers a run.",
        },
        null,
        2
      ),
      { headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } }
    );
  },
};
