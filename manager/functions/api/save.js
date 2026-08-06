/* POST /api/save — apply an edit to the pipeline queue and commit it to GitHub.

   Ops (one per request):
   { op:"upsert",  campaign, ids:[..], platforms:["instagram","facebook"],
     scheduled_for_utc, caption, image_url }
       - ids = the queue entries this logical post already owns (empty = new post)
       - platform toggled ON with no existing entry  -> new entry created
       - platform toggled OFF with an existing entry -> that entry is removed
   { op:"delete", ids:[..] }            — remove those entries (pending/failed only)
   { op:"delete_campaign", campaign }   — remove ALL pending+failed entries of an event

   Rules enforced here (server-side, cannot be bypassed by the UI):
   - 2-hour minimum lead time on any created/updated post
   - posts that already went out (status "posted") are never modified or deleted
*/

import { LEAD_MS, genId, loadQueue, saveQueue, json } from "../_lib/queue.js";

export async function onRequestPost(context) {
  const { env, request } = context;
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "Bad request body." }, 400);
  }

  // one retry if the cron worker commits between our read and write
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      const { queue, sha } = await loadQueue(env);
      const result = applyOp(queue, body);
      if (result.error) return json({ error: result.error }, 400);
      await saveQueue(env, queue, sha, result.message);
      return json({ ok: true, message: result.message });
    } catch (e) {
      if (e.status === 409 && attempt === 0) continue; // stale sha -> refetch once
      console.log("save error:", e.message);
      const hint = e.status === 401
        ? " The GitHub token has expired or been revoked — generate a new fine-grained token and update GITHUB_TOKEN in the Cloudflare Pages project settings."
        : "";
      return json({ error: "Couldn't save to GitHub. " + e.message + hint }, 502);
    }
  }
}

function applyOp(queue, body) {
  const posts = queue.posts;

  if (body.op === "delete") {
    const ids = new Set(body.ids || []);
    const victims = posts.filter((p) => ids.has(p.id));
    if (!victims.length) return { error: "Those posts weren't found — maybe already deleted. Refresh and try again." };
    if (victims.some((p) => p.status === "posted")) {
      return { error: "One of those posts already went out — posted posts can't be deleted." };
    }
    queue.posts = posts.filter((p) => !ids.has(p.id));
    return { message: `Post Manager: delete ${victims.length} post(s)` };
  }

  if (body.op === "delete_campaign") {
    if (!body.campaign) return { error: "Missing campaign." };
    const before = posts.length;
    queue.posts = posts.filter(
      (p) => !(p.campaign === body.campaign && p.status !== "posted"));
    const n = before - queue.posts.length;
    if (!n) return { error: "No pending posts found for that event." };
    return { message: `Post Manager: delete all ${n} pending post(s) for ${body.campaign}` };
  }

  if (body.op === "upsert") {
    const err = validateUpsert(body);
    if (err) return { error: err };

    const ids = new Set(body.ids || []);
    const existing = posts.filter((p) => ids.has(p.id));
    if (existing.some((p) => p.status === "posted")) {
      return { error: "This post already went out — it can't be edited." };
    }

    const keep = [];
    for (const plat of body.platforms) {
      const entry = existing.find((p) => p.platform === plat);
      if (entry) {
        entry.scheduled_for_utc = body.scheduled_for_utc;
        entry.caption = body.caption;
        if (body.image_url) entry.image_url = body.image_url;
        entry.status = "pending";
        entry.result = "";
        keep.push(entry.id);
      } else {
        const fresh = {
          id: genId(body.scheduled_for_utc),
          platform: plat,
          scheduled_for_utc: body.scheduled_for_utc,
          image_url: body.image_url || "",
          caption: body.caption,
          status: "pending",
          created_at: new Date().toISOString(),
          posted_at: null,
          result: "",
        };
        if (body.campaign && body.campaign !== "__oneoffs") fresh.campaign = body.campaign;
        posts.push(fresh);
        keep.push(fresh.id);
      }
    }
    // platforms toggled off -> drop their entries
    queue.posts = posts.filter(
      (p) => !ids.has(p.id) || keep.includes(p.id));

    const verb = (body.ids || []).length ? "edit" : "add";
    return { message: `Post Manager: ${verb} post (${body.platforms.join("+")}) for ${body.campaign || "one-off"}` };
  }

  return { error: "Unknown operation." };
}

function validateUpsert(body) {
  if (!Array.isArray(body.platforms) || !body.platforms.length) {
    return "Pick at least one place to post — Instagram, Facebook, or both.";
  }
  if (body.platforms.some((p) => p !== "instagram" && p !== "facebook")) {
    return "Unknown platform.";
  }
  if (!body.caption || !body.caption.trim()) return "The caption is empty.";
  const when = new Date(body.scheduled_for_utc);
  if (isNaN(when)) return "Pick a date and time for this post.";
  if (when.getTime() < Date.now() + LEAD_MS) {
    return "That time is too soon — posts must be at least 2 hours out. Pick a later time, or post it manually on Facebook if you need it now.";
  }
  return null;
}
