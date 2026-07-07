/* GET /api/events — live view of the pipeline queue, grouped into events.
   Reads posts_queue.json straight from the GitHub repo (main branch), merges
   IG+FB twins, groups by campaign, and decorates with events_meta.json. */

import { buildEvents, loadQueue, json } from "../_lib/queue.js";

export async function onRequestGet(context) {
  const { env, request } = context;
  try {
    const [{ queue }, meta] = await Promise.all([
      loadQueue(env),
      loadMeta(context),
    ]);
    return json({
      mode: "live",
      generated_at: new Date().toISOString(),
      events: buildEvents(queue.posts, meta),
    });
  } catch (e) {
    console.log("events error:", e.message);
    return json({ error: "Couldn't load the queue from GitHub. " + e.message }, 502);
  }
}

async function loadMeta(context) {
  try {
    const url = new URL("/events_meta.json", context.request.url);
    const res = await context.env.ASSETS.fetch(new Request(url));
    if (res.ok) return await res.json();
  } catch (e) { /* fall through */ }
  return {};
}
