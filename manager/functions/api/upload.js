/* POST /api/upload — host a photo where Meta's API can fetch it.
   Proxies the file to catbox.moe, the same host schedule_post.py uses
   (queue_utils.upload_image_to_catbox), and returns { url }. */

import { json } from "../_lib/queue.js";

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
  const { request } = context;
  let form;
  try {
    form = await request.formData();
  } catch {
    return json({ error: "Send the photo as multipart form data." }, 400);
  }
  const file = form.get("file");
  if (!file || typeof file === "string") return json({ error: "No photo attached." }, 400);
  if (file.size > MAX_BYTES) return json({ error: "That photo is over 15 MB — export a smaller version and try again." }, 400);

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
    error: `The photo host (catbox.moe) refused the upload after ${ATTEMPTS} tries — ${last}. ` +
           `Wait a few minutes and retry, or post this one manually.`,
  }, 502);
}
