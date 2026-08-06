/* Shared queue logic for the Post Manager API (Cloudflare Pages Functions).
   JS twin of manager/build_events.py — same grouping rules:
   - IG + FB entries with identical (scheduled_for_utc, caption) merge into one
     "logical post" carrying both platforms.
   - Posts group into events by their `campaign` field; posts without a
     campaign fall into a single "one-offs" bucket.
   Event names/dates/looks come from events_meta.json (editable). */

export const LEAD_MS = 2 * 60 * 60 * 1000; // 2-hour minimum lead time

const STATUS_RANK = { failed: 2, pending: 1, posted: 0 };

export function mergeLogical(posts) {
  const buckets = new Map();
  for (const p of posts) {
    const key = p.scheduled_for_utc + "\u0000" + p.caption;
    if (!buckets.has(key)) {
      buckets.set(key, {
        ids: [],
        platforms: [],
        scheduled_for_utc: p.scheduled_for_utc,
        caption: p.caption,
        images: [],
        status: p.status,
        result: p.result || "",
      });
    }
    const b = buckets.get(key);
    b.ids.push(p.id);
    if (!b.platforms.includes(p.platform)) b.platforms.push(p.platform);
    if (p.image_url && !b.images.includes(p.image_url)) b.images.push(p.image_url);
    if ((STATUS_RANK[p.status] || 0) > (STATUS_RANK[b.status] || 0)) {
      b.status = p.status;
      b.result = p.result || "";
    }
  }
  return [...buckets.values()].sort((a, b) =>
    a.scheduled_for_utc.localeCompare(b.scheduled_for_utc));
}

export function buildEvents(queuePosts, meta) {
  const byCampaign = new Map();
  const standalone = [];
  for (const p of queuePosts) {
    if (p.campaign) {
      if (!byCampaign.has(p.campaign)) byCampaign.set(p.campaign, []);
      byCampaign.get(p.campaign).push(p);
    } else {
      standalone.push(p);
    }
  }

  const events = [];
  for (const [camp, plist] of byCampaign) {
    const m = (meta && meta[camp]) || {};
    events.push({
      id: camp,
      name: m.name || camp.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
      event_date: m.event_date || postEventDate(plist) || maxDate(plist),
      tag: m.tag || "✨ Event",
      flyer_grad: m.flyer_grad || "linear-gradient(135deg,#E5195E,#FF7A2F)",
      source: "real",
      posts: mergeLogical(plist),
    });
  }
  if (standalone.length) {
    const m = (meta && meta.__oneoffs) || {};
    events.push({
      id: "__oneoffs",
      name: m.name || "One-off posts",
      event_date: m.event_date || maxDate(standalone),
      tag: m.tag || "🗂️ One-offs",
      flyer_grad: m.flyer_grad || "linear-gradient(135deg,#2F9E6B,#7B2FF0)",
      source: "real",
      posts: mergeLogical(standalone),
    });
  }
  return events;
}

/* Cadence-engine posts carry the event's real date from the Monday board. */
function postEventDate(posts) {
  for (const p of posts) if (p.event_date) return p.event_date;
  return null;
}

/* Fallback: latest post's date in VENUE-LOCAL time. Slicing the raw UTC string
   shifted evening events to the next day (7 PM PT day-of post = 2 AM UTC), so
   they displayed the wrong date and never archived. */
function maxDate(posts) {
  const latest = posts.map((p) => p.scheduled_for_utc).sort().pop();
  return new Date(latest).toLocaleDateString("en-CA", { timeZone: "America/Los_Angeles" });
}

/* Pipeline-compatible id: YYYYMMDD_HHMMSS_hex6 from the scheduled UTC time */
export function genId(scheduledIso) {
  const d = new Date(scheduledIso);
  const p = (n) => String(n).padStart(2, "0");
  const stamp = `${d.getUTCFullYear()}${p(d.getUTCMonth() + 1)}${p(d.getUTCDate())}` +
    `_${p(d.getUTCHours())}${p(d.getUTCMinutes())}${p(d.getUTCSeconds())}`;
  const bytes = new Uint8Array(3);
  crypto.getRandomValues(bytes);
  const hex = [...bytes].map((b) => b.toString(16).padStart(2, "0")).join("");
  return `${stamp}_${hex}`;
}

/* ---------- GitHub contents API ---------- */

const GH_API = "https://api.github.com";

function ghHeaders(env) {
  const h = {
    "User-Agent": "azucar-post-manager",
    Accept: "application/vnd.github+json",
  };
  if (env.GITHUB_TOKEN) h.Authorization = `Bearer ${env.GITHUB_TOKEN}`;
  return h;
}

// An expired/revoked GITHUB_TOKEN makes GitHub answer 401 even for files
// anyone can read. The repo is public, so retry the read without
// credentials instead of going dark — only writes truly need the token.
async function ghFetch(env, url, extraHeaders = {}) {
  let res = await fetch(url, { headers: { ...ghHeaders(env), ...extraHeaders }, cf: { cacheTtl: 0 } });
  if ((res.status === 401 || res.status === 403) && env.GITHUB_TOKEN) {
    res = await fetch(url, { headers: { ...ghHeaders({}), ...extraHeaders }, cf: { cacheTtl: 0 } });
  }
  return res;
}

export async function ghGetFile(env, path) {
  const repo = env.GITHUB_REPO || "soynopalero/Azucar-Social-Pipeline";
  const url = `${GH_API}/repos/${repo}/contents/${path}?ref=main`;
  const res = await ghFetch(env, url);
  if (!res.ok) {
    const err = new Error(`GitHub read ${path} failed: ${res.status}`);
    err.status = res.status;
    throw err;
  }
  const data = await res.json();
  let text;
  if (data.content) {
    text = new TextDecoder().decode(
      Uint8Array.from(atob(data.content.replace(/\n/g, "")), (c) => c.charCodeAt(0)));
  } else if (data.size > 0) {
    // Files over 1 MB come back with empty inline content — the queue crossed
    // that line in Aug 2026 and froze the whole manager. Re-fetch the raw
    // bytes, which the same endpoint serves for files up to 100 MB.
    const raw = await ghFetch(env, url, { Accept: "application/vnd.github.raw+json" });
    if (!raw.ok) {
      const err = new Error(`GitHub raw read ${path} failed: ${raw.status}`);
      err.status = raw.status;
      throw err;
    }
    text = await raw.text();
  } else {
    text = "";
  }
  return { text, sha: data.sha };
}

export async function ghPutFile(env, path, text, sha, message) {
  const repo = env.GITHUB_REPO || "soynopalero/Azucar-Social-Pipeline";
  const bytes = new TextEncoder().encode(text);
  let bin = "";
  for (let i = 0; i < bytes.length; i += 0x8000) {
    bin += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  }
  const res = await fetch(`${GH_API}/repos/${repo}/contents/${path}`, {
    method: "PUT",
    headers: { ...ghHeaders(env), "Content-Type": "application/json" },
    body: JSON.stringify({ message, content: btoa(bin), sha, branch: "main" }),
  });
  if (!res.ok) {
    const body = await res.text();
    const err = new Error(`GitHub write ${path} failed: ${res.status} ${body.slice(0, 200)}`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export async function loadQueue(env) {
  const { text, sha } = await ghGetFile(env, "posts_queue.json");
  return { queue: JSON.parse(text), sha };
}

export async function saveQueue(env, queue, sha, message) {
  const text = JSON.stringify(queue, null, 2) + "\n";
  await ghPutFile(env, "posts_queue.json", text, sha, message);
  // mirror for the GitHub Pages dashboard (best-effort; root file is the truth)
  try {
    const mirror = await ghGetFile(env, "docs/posts_queue.json");
    await ghPutFile(env, "docs/posts_queue.json", text, mirror.sha, message + " (mirror)");
  } catch (e) {
    console.log("mirror update skipped:", e.message);
  }
}

export function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}
