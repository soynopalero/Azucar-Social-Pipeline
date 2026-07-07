/* POST /api/upload — host a photo where Meta's API can fetch it.
   Proxies the file to catbox.moe, the same host schedule_post.py uses
   (queue_utils.upload_image_to_catbox), and returns { url }. */

import { json } from "../_lib/queue.js";

const MAX_BYTES = 15 * 1024 * 1024; // catbox comfortably handles this; flyers are ~1-3 MB

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

  const out = new FormData();
  out.set("reqtype", "fileupload");
  out.set("fileToUpload", file, file.name || "photo.jpg");

  const res = await fetch("https://catbox.moe/user/api.php", { method: "POST", body: out });
  const text = (await res.text()).trim();
  if (!res.ok || !text.startsWith("http")) {
    console.log("catbox error:", res.status, text.slice(0, 200));
    return json({ error: "The photo host didn't accept the upload. Try again in a minute." }, 502);
  }
  return json({ url: text });
}
