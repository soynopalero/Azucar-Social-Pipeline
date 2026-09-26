#!/usr/bin/env python3
"""
canva_authorize.py
------------------
Run this ONCE, on your own computer, to let the pipeline talk to Canva.

It opens Canva in your browser, you click Allow, and it prints a refresh
token. That token is what the weekly job uses; it does not expire on a fixed
schedule, so this is a one-time job unless the app's scopes change.

Before running, in the Canva developer portal (Your apps -> your app ->
Outside Canva -> Canva REST APIs):

  * Scopes:  asset Read+Write, brandtemplate:content Read+Write,
             brandtemplate:meta Read, design:content Read+Write,
             design:meta Read, profile Read
  * Redirect URL:  http://127.0.0.1:3001/oauth/redirect
  * Generate a client secret

Then:

    export CANVA_CLIENT_ID=...          # the App ID
    export CANVA_CLIENT_SECRET=...      # the generated secret
    python3 code/canva_authorize.py

It finishes by printing your account's API capabilities. Watch for
`autofill` in that list — without it the weekly card cannot be filled
automatically, and the answer is not more code.

Nothing is written to disk: the token is printed once, for you to paste into
GitHub Secrets as CANVA_REFRESH_TOKEN. Run it again any time to get a fresh
one; authorizing again silently invalidates the previous refresh token, so
only do that when you intend to replace it.

Standard library only — no pip install.
"""
from __future__ import annotations

import base64
import hashlib
import http.server
import json
import os
import secrets
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request

AUTH_URL = "https://www.canva.com/api/oauth/authorize"
API = "https://api.canva.com/rest"
REDIRECT = "http://127.0.0.1:3001/oauth/redirect"
PORT = 3001

SCOPES = [
    "asset:read", "asset:write",
    "brandtemplate:content:read", "brandtemplate:content:write",
    "brandtemplate:meta:read",
    "design:content:read", "design:content:write",
    "design:meta:read",
    "profile:read",
]

_result: dict = {}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/oauth/redirect":
            self.send_response(404)
            self.end_headers()
            return
        q = urllib.parse.parse_qs(parsed.query)
        _result["code"] = (q.get("code") or [None])[0]
        _result["state"] = (q.get("state") or [None])[0]
        _result["error"] = (q.get("error") or [None])[0]
        body = (b"<h2>Done - you can close this tab and go back to the terminal.</h2>"
                if _result["code"] else
                b"<h2>Canva returned an error. Check the terminal.</h2>")
        self.send_response(200)
        self.send_header("content-type", "text/html; charset=utf-8")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        threading.Thread(target=self.server.shutdown, daemon=True).start()

    def log_message(self, *a):
        pass  # the browser's noise is not the user's problem


def post_form(path: str, form: dict, basic: tuple[str, str]) -> dict:
    data = urllib.parse.urlencode(form).encode()
    auth = base64.b64encode(f"{basic[0]}:{basic[1]}".encode()).decode()
    req = urllib.request.Request(
        f"{API}{path}", data=data,
        headers={"content-type": "application/x-www-form-urlencoded",
                 "authorization": f"Basic {auth}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"\nCanva rejected the token request ({e.code}):\n{e.read().decode()[:600]}")


def get_json(path: str, token: str) -> dict:
    req = urllib.request.Request(f"{API}{path}",
                                 headers={"authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"_error": f"{e.code} {e.read().decode()[:300]}"}


def main() -> int:
    client_id = (os.environ.get("CANVA_CLIENT_ID") or "").strip()
    client_secret = (os.environ.get("CANVA_CLIENT_SECRET") or "").strip()
    if not client_id or not client_secret:
        print("Set CANVA_CLIENT_ID and CANVA_CLIENT_SECRET first:\n"
              "  export CANVA_CLIENT_ID=AAHOGHTimHs\n"
              "  export CANVA_CLIENT_SECRET=...", file=sys.stderr)
        return 2

    # PKCE. Canva requires S256; the verifier never leaves this machine until
    # the token exchange, so an intercepted redirect is useless on its own.
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).decode().rstrip("=")
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    state = secrets.token_urlsafe(16)

    url = AUTH_URL + "?" + urllib.parse.urlencode({
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "scope": " ".join(SCOPES),
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT,
        "state": state,
    })

    print("\nOpen this in your browser and click Allow:\n")
    print(url)
    print(f"\nWaiting on {REDIRECT} ...")
    try:
        import webbrowser
        webbrowser.open(url)
    except Exception:
        pass  # printing it is the real path; opening it is a convenience

    try:
        srv = http.server.HTTPServer(("127.0.0.1", PORT), Handler)
    except OSError as e:
        print(f"Could not listen on port {PORT} ({e}). Close whatever is "
              f"using it and run this again.", file=sys.stderr)
        return 1
    srv.serve_forever()
    srv.server_close()

    if _result.get("error"):
        print(f"Canva said: {_result['error']}", file=sys.stderr)
        return 1
    if not _result.get("code"):
        print("No code came back.", file=sys.stderr)
        return 1
    # A mismatched state means the redirect did not come from the request we
    # started, so the code is not ours to spend.
    if _result.get("state") != state:
        print("State mismatch — aborting.", file=sys.stderr)
        return 1

    tok = post_form("/v1/oauth/token", {
        "grant_type": "authorization_code",
        "code": _result["code"],
        "code_verifier": verifier,
        "redirect_uri": REDIRECT,
    }, (client_id, client_secret))

    refresh = tok.get("refresh_token")
    access = tok.get("access_token")
    if not refresh:
        print(f"No refresh token in the reply:\n{tok}", file=sys.stderr)
        return 1

    caps = get_json("/v1/users/me/capabilities", access)
    cap_list = caps.get("capabilities") if isinstance(caps, dict) else None

    print("\n" + "=" * 62)
    print("CANVA_REFRESH_TOKEN — paste this into GitHub Secrets:\n")
    print(refresh)
    print("=" * 62)
    print("\nWhat this account can do through the API:")
    if cap_list is None:
        print(f"  couldn't read capabilities: {caps}")
    else:
        for c in sorted(cap_list):
            print(f"  - {c}")
        if "autofill" not in cap_list:
            print("\n  *** No `autofill`. The weekly card cannot be filled through")
            print("      the API on this plan. Tell Claude — the answer is a")
            print("      different approach, not more code. ***")
        else:
            print("\n  `autofill` is present. Note it is trial-limited off Canva")
            print("  Enterprise: the first real run reports uses remaining.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
