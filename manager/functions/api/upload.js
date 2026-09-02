/* POST /api/upload — host a photo where Meta's API can fetch it, returns { url }.

   Writes to the R2 bucket bound as PHOTOS and serves it from R2_PUBLIC_BASE.
   That base has to be a hostname Access does not sit in front of (the bucket's
   r2.dev URL, or a custom domain on the bucket) — Meta fetches the image
   unauthenticated at posting time, so anything behind the email gate is
   useless to it.

   Falls back to catbox.moe when the bucket isn't configured, which is what
   this used to do exclusively. Worth knowing that catbox refuses uploads from
   datacenter IPs — cadence_engine.py hit exactly that from GitHub Actions
   (412 "Invalid uploader") and moved to GitHub Pages over it. Cloudflare's
   egress is datacenter IP space too, so the fallback may simply not work from
   here; it stays only so the endpoint keeps working before the bucket exists. */

import { json } from "../_lib/queue.js";

const ALLOWED = new Set(["image/jpeg", "image/png", "image/webp", "image/gif"]);

function objectKey(file) {
  const now = new Date();
  const ext = ({ "image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif" })[file.type]
    || (file.name?.match(/\.([a-z0-9]{2,4})$/i)?.[1] ?? "jpg").toLowerCase();
  const rand = crypto.randomUUID().slice(0, 8);
  return `flyers/${now.getUTCFullYear()}/${String(now.getUTCMonth() + 1).padStart(2, "0")}/${rand}.${ext}`;
}

async function uploadToR2(env, file) {
  const key = objectKey(file);
  await env.PHOTOS.put(key, file.stream(), {
    httpMetadata: {
      contentType: file.type || "image/jpeg",
      // Flyers never change once written -- the key is unique per upload.
      cacheControl: "public, max-age=31536000, immutable",
    },
  });
  return `${env.R2_PUBLIC_BASE.replace(/\/$/, "")}/${key}`;
}

const MAX_BYTES = 15 * 1024 * 1024; // catbox comfortably handles this; flyers are ~1-3 MB
const ATTEMPTS = 3;                 // catbox drops requests when busy; a retry usually lands
const TIMEOUT_MS = 60_000;          // don't let one hung request eat the whole invocation
// requests(1) sends its own agent from the Python path, so identify ourselves here too --
// several free hosts reject uploads they cannot attribute.
const USER_AGENT = "azucar-post-manager (+https://github.com/soynopalero/Azucar-Social-Pipeline)";

async function uploadToCatbox(file) {
  // Rebuilt per attempt: FormData is single-use once fetch has consumed it.
  const body = new FormData();
  body.set("reqtype", "fileupload");
  body.set("fileToUpload", file, file.name || "photo.jpg");

  const res = await fetch("https://catbox.moe/user/api.php", {
    method: "POST",
    body,
    headers: { "User-Agent": USER_AGENT },
    signal: AbortSignal.timeout(TIMEOUT_MS),
  });
  const text = (await res.text()).trim();
  // catbox answers 200 with a bare URL on success, and 200 with an error
  // sentence on failure -- so the status alone does not tell you anything.
  return { ok: res.ok && text.startsWith("http"), status: res.status, text };
}

export async function onRequestPost(context) {
  const { request, env } = context;
  let form;
  try {
    form = await request.formData();
  } catch {
    return json({ error: "Send the photo as multipart form data." }, 400);
  }
  const file = form.get("file");
  if (!file || typeof file === "string") return json({ error: "No photo attached." }, 400);
  if (file.size > MAX_BYTES) return json({ error: "That photo is over 15 MB — export a smaller version and try again." }, 400);
  if (file.type && !ALLOWED.has(file.type)) {
    return json({ error: `That file is ${file.type}. Meta only fetches JPEG, PNG, WebP or GIF.` }, 400);
  }

  if (env.PHOTOS && env.R2_PUBLIC_BASE) {
    try {
      return json({ url: await uploadToR2(env, file) });
    } catch (err) {
      // A bucket failure is ours to fix, not something a retry against catbox
      // should paper over -- say so plainly instead of falling through.
      console.log("r2 put failed:", err?.message || err);
      return json({ error: `Couldn't save the photo to storage — ${err?.message || err}.` }, 502);
    }
  }

  let last = "no response";
  for (let attempt = 1; attempt <= ATTEMPTS; attempt++) {
    try {
      const { ok, status, text } = await uploadToCatbox(file);
      if (ok) return json({ url: text });
      // catbox's own sentences end in a period; strip it so the message below reads cleanly.
      last = `HTTP ${status}: ${text.slice(0, 120).replace(/\.$/, "") || "(empty response)"}`;
    } catch (err) {
      // Timeout or a connection that never opened -- worth retrying.
      last = err?.name === "TimeoutError" ? `timed out after ${TIMEOUT_MS / 1000}s` : String(err?.message || err);
    }
    console.log(`catbox upload attempt ${attempt}/${ATTEMPTS} failed:`, last);
    if (attempt < ATTEMPTS) await new Promise((r) => setTimeout(r, attempt * 1000));
  }

  // Say what actually went wrong. The old generic message sent everyone to the
  // Cloudflare logs to find out whether catbox was down or rejecting us.
  return json({
    error: `No photo storage is configured, and the catbox.moe fallback refused the upload ` +
           `after ${ATTEMPTS} tries — ${last}. Set up the R2 bucket (see manager/README.md), ` +
           `or post this one manually.`,
  }, 502);
}
