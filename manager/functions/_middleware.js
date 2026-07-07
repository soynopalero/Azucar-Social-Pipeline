/* Auth middleware for all /api/* routes.

   Cloudflare Access sits in front of the whole site (the email allow-list).
   Access stamps every authenticated request with a signed JWT in the
   Cf-Access-Jwt-Assertion header. We verify that signature here as
   defense-in-depth, so the write endpoints stay locked even if someone
   reaches the *.pages.dev URL directly.

   Env vars (Pages project settings):
     ACCESS_TEAM_DOMAIN  e.g. "azucar.cloudflareaccess.com"
     ACCESS_AUD          the Access application's Audience (AUD) tag
     DEV_MODE=1          local dev only — skips auth entirely

   Fail-safe default: if Access isn't configured yet, reads still work
   (the queue file is public on GitHub anyway) but writes are refused. */

let certCache = { keys: null, fetched: 0 };

export async function onRequest(context) {
  const { request, env, next } = context;
  const url = new URL(request.url);
  if (!url.pathname.startsWith("/api/")) return next();
  if (env.DEV_MODE === "1") return next();

  const isWrite = request.method !== "GET";

  if (!env.ACCESS_TEAM_DOMAIN || !env.ACCESS_AUD) {
    if (isWrite) {
      return refuse("Editing is locked until the login gate (Cloudflare Access) is configured.", 503);
    }
    return next(); // reads only
  }

  const token = request.headers.get("Cf-Access-Jwt-Assertion");
  if (!token) return refuse("You need to sign in to use this.", 401);

  try {
    const payload = await verifyAccessJwt(token, env);
    // hand the verified identity to the endpoints
    context.data = { email: payload.email || "" };
    return next();
  } catch (e) {
    console.log("access jwt rejected:", e.message);
    return refuse("Your sign-in couldn't be verified. Reload the page and sign in again.", 401);
  }
}

function refuse(message, status) {
  return new Response(JSON.stringify({ error: message }), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

async function verifyAccessJwt(token, env) {
  const [h, p, s] = token.split(".");
  if (!h || !p || !s) throw new Error("malformed token");
  const header = JSON.parse(b64uToText(h));
  const payload = JSON.parse(b64uToText(p));

  const now = Math.floor(Date.now() / 1000);
  if (payload.exp && payload.exp < now) throw new Error("token expired");
  const auds = Array.isArray(payload.aud) ? payload.aud : [payload.aud];
  if (!auds.includes(env.ACCESS_AUD)) throw new Error("wrong audience");
  const expectedIss = `https://${env.ACCESS_TEAM_DOMAIN}`;
  if (payload.iss !== expectedIss) throw new Error("wrong issuer");

  const jwk = await findKey(env, header.kid);
  const key = await crypto.subtle.importKey(
    "jwk", jwk, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]);
  const ok = await crypto.subtle.verify(
    "RSASSA-PKCS1-v1_5", key,
    b64uToBytes(s), new TextEncoder().encode(`${h}.${p}`));
  if (!ok) throw new Error("bad signature");
  return payload;
}

async function findKey(env, kid) {
  const fresh = Date.now() - certCache.fetched < 60 * 60 * 1000;
  if (!certCache.keys || !fresh || !certCache.keys.find((k) => k.kid === kid)) {
    const res = await fetch(`https://${env.ACCESS_TEAM_DOMAIN}/cdn-cgi/access/certs`);
    if (!res.ok) throw new Error("couldn't fetch Access certs");
    certCache = { keys: (await res.json()).keys || [], fetched: Date.now() };
  }
  const jwk = certCache.keys.find((k) => k.kid === kid);
  if (!jwk) throw new Error("unknown signing key");
  return jwk;
}

function b64uToText(s) {
  return new TextDecoder().decode(b64uToBytes(s));
}
function b64uToBytes(s) {
  const b64 = s.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((s.length + 3) % 4);
  return Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
}
