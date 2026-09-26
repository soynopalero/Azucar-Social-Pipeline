#!/usr/bin/env python3
"""
canva_api.py
------------
Thin Canva Connect client for the weekly card, plus a `--probe` that answers
the two things we cannot know without asking Canva directly.

The two unknowns
----------------
1. **Does the refresh token survive being used?** Canva returns a new one on
   every refresh and its own reference client saves it each time, which is
   how a provider behaves when the old token is dead. If it is dead, a fixed
   `CANVA_REFRESH_TOKEN` secret works once and the Friday job breaks the
   following week — so this is worth knowing before anything depends on it.

2. **How many autofill uses are left?** Autofill is trial-limited off Canva
   Enterprise. The count only comes back on a real autofill, in the job's
   `trial_information`. A weekly job needs 52 a year; if the trial is 20,
   this approach has an expiry date and we should not build on it.

`--probe` tests (1) for free, then spends exactly one autofill to learn (2).

Rotation, if it is enforced
---------------------------
The new refresh token has to reach the GitHub secret somehow, and printing a
credential into a public repo's Actions log is not that. So the probe sends
it over Telegram, the private channel this pipeline already uses, for Pedro
to paste in. Automating the write-back needs a PAT with secrets:write; the
probe says whether that is worth setting up.

Usage:
    python code/canva_api.py --probe            # answer both questions
    python code/canva_api.py --probe --no-autofill   # token test only, free
    python code/canva_api.py --selftest         # offline
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.canva.com/rest"

# The 6-row weekly card. Autofill copies it; the original is never touched.
WEEK_CARD_DESIGN_ID = "DAHWLCTrgMQ"


class CanvaError(RuntimeError):
    pass


def envvar(name: str) -> str:
    return (os.environ.get(name) or "").strip()


def _request(method: str, url: str, *, headers: dict, data: bytes | None = None,
             timeout: int = 60) -> dict:
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        raise CanvaError(f"{method} {url.split('?')[0]} -> {e.code}: {detail}") from None


def refresh_access_token(client_id: str, client_secret: str,
                         refresh_token: str) -> dict:
    """Swap a refresh token for an access token. Returns the whole payload,
    because the new refresh_token in it matters as much as the access one."""
    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    return _request(
        "POST", f"{API}/v1/oauth/token",
        headers={"content-type": "application/x-www-form-urlencoded",
                 "authorization": f"Basic {auth}"},
        data=urllib.parse.urlencode({"grant_type": "refresh_token",
                                     "refresh_token": refresh_token}).encode(),
    )


def bearer(token: str) -> dict:
    return {"authorization": f"Bearer {token}", "content-type": "application/json"}


def capabilities(token: str) -> list[str]:
    return _request("GET", f"{API}/v1/users/me/capabilities",
                    headers=bearer(token)).get("capabilities") or []


def poll_job(path: str, token: str, *, what: str,
             timeout_s: int = 180, every_s: float = 2.0) -> dict:
    """Canva's async jobs all share this shape: in_progress -> success/failed."""
    deadline = time.time() + timeout_s
    while True:
        job = (_request("GET", f"{API}{path}", headers=bearer(token)) or {}).get("job") or {}
        status = job.get("status")
        if status == "success":
            return job
        if status == "failed":
            raise CanvaError(f"{what} failed: {job.get('error')}")
        if time.time() > deadline:
            raise CanvaError(f"{what} still {status} after {timeout_s}s")
        time.sleep(every_s)


def autofill_from_design(token: str, design_id: str, fields: dict,
                         title: str | None = None) -> dict:
    """Fill a design's named autofill fields into a NEW design.

    `create_from_design` is a Canva preview feature — it can change without
    an API version bump. The alternative is publishing brand templates, which
    the plain text fields do not otherwise need.
    """
    body = {"type": "create_from_design", "design_id": design_id,
            "data": {k: {"type": "text", "text": v} for k, v in fields.items()}}
    if title:
        body["title"] = title
    started = _request("POST", f"{API}/v1/autofills", headers=bearer(token),
                       data=json.dumps(body).encode())
    job_id = ((started or {}).get("job") or {}).get("id")
    if not job_id:
        raise CanvaError(f"no autofill job id in reply: {started}")
    return poll_job(f"/v1/autofills/{job_id}", token, what="autofill")


def export_png(token: str, design_id: str) -> list[str]:
    """Export a design to PNG. Returns download URLs, which expire in hours —
    fetch them in the same run."""
    started = _request("POST", f"{API}/v1/exports", headers=bearer(token),
                       data=json.dumps({"design_id": design_id,
                                        "format": {"type": "png"}}).encode())
    job_id = ((started or {}).get("job") or {}).get("id")
    if not job_id:
        raise CanvaError(f"no export job id in reply: {started}")
    job = poll_job(f"/v1/exports/{job_id}", token, what="export")
    return [u for u in (job.get("urls") or []) if u]


def tg(text: str) -> None:
    """Telegram is where a rotated refresh token can go without ending up in
    a public repo's Actions log."""
    token, chat = envvar("TELEGRAM_BOT_TOKEN"), envvar("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("(no Telegram creds — skipping the DM)")
        return
    try:
        _request("POST", f"https://api.telegram.org/bot{token}/sendMessage",
                 headers={"content-type": "application/json"},
                 data=json.dumps({"chat_id": chat, "text": text,
                                  "disable_web_page_preview": True}).encode())
    except CanvaError as e:
        print(f"(Telegram send failed: {e})")


def fingerprint(s: str) -> str:
    """Enough to tell two tokens apart in a log, not enough to use one."""
    return f"{s[:6]}…{s[-4:]} (len {len(s)})" if len(s) > 12 else "(short)"


def probe(do_autofill: bool) -> int:
    cid, sec = envvar("CANVA_CLIENT_ID"), envvar("CANVA_CLIENT_SECRET")
    original = envvar("CANVA_REFRESH_TOKEN")
    missing = [n for n, v in (("CANVA_CLIENT_ID", cid),
                              ("CANVA_CLIENT_SECRET", sec),
                              ("CANVA_REFRESH_TOKEN", original)) if not v]
    if missing:
        print(f"Missing secrets: {', '.join(missing)}", file=sys.stderr)
        return 2

    print("1. Refreshing with the stored token…")
    first = refresh_access_token(cid, sec, original)
    access = first.get("access_token")
    rotated = first.get("refresh_token")
    if not access:
        print(f"No access token came back: {first}", file=sys.stderr)
        return 1
    print(f"   access token ok, expires_in={first.get('expires_in')}s")
    print(f"   stored refresh:  {fingerprint(original)}")
    print(f"   returned refresh:{fingerprint(rotated or '')}")
    print(f"   same token?      {rotated == original}")

    print("\n2. Re-using the ORIGINAL refresh token (the real question)…")
    reusable = False
    try:
        refresh_access_token(cid, sec, original)
        reusable = True
        print("   WORKS — the stored token survives use.")
        print("   => a fixed CANVA_REFRESH_TOKEN secret is enough. No write-back needed.")
    except CanvaError as e:
        print(f"   REJECTED — {str(e)[:200]}")
        print("   => Canva rotates and invalidates. The secret must be replaced")
        print("      after every run, or the job breaks next week.")

    print("\n3. Capabilities:")
    caps = capabilities(access)
    for c in sorted(caps):
        print(f"   - {c}")

    uses = None
    if do_autofill:
        if "autofill" not in caps:
            print("\n4. Skipping the autofill test — no autofill capability.")
        else:
            print("\n4. Spending ONE autofill to read the trial counter…")
            job = autofill_from_design(
                access, WEEK_CARD_DESIGN_ID,
                {"week_label": "PROBE — delete me"},
                title="Azúcar — API probe (safe to delete)")
            res = job.get("result") or {}
            design = res.get("design") or {}
            trial = res.get("trial_information") or {}
            uses = trial.get("uses_remaining")
            print(f"   autofill OK -> design {design.get('id')} {design.get('url','')}")
            if uses is None:
                print("   no trial_information returned — usually means the account")
                print("   is not trial-limited. Good news, but unconfirmed.")
            else:
                print(f"   *** autofill uses remaining: {uses} ***")
                print(f"   at 52 posts a year that is ~{uses // 52} year(s) "
                      f"and {uses % 52} week(s).")

    print("\n" + "=" * 60)
    print(f"refresh token reusable : {reusable}")
    print(f"autofill capability    : {'autofill' in caps}")
    print(f"autofill uses remaining: {uses if uses is not None else 'not reported'}")
    print("=" * 60)

    if not reusable and rotated:
        # The stored secret is now dead; the only live token is this one, and
        # it must not be printed here.
        tg("🔑 Canva refresh token rotated.\n\n"
           "The token in GitHub Secrets no longer works — Canva invalidates it "
           "on use. Replace CANVA_REFRESH_TOKEN with the value below:\n\n"
           f"{rotated}\n\n"
           "https://github.com/soynopalero/Azucar-Social-Pipeline/settings/secrets/actions")
        print("\nRotation detected: the replacement token was sent to Telegram,")
        print("not printed here — this log is public.")
    return 0


def selftest() -> int:
    assert fingerprint("abcdefghijklmnop") == "abcdef…mnop (len 16)"
    assert fingerprint("short") == "(short)"
    # A fingerprint must never be enough to reconstruct the token.
    tok = "x" * 200
    assert len(fingerprint(tok)) < 30

    body = {"type": "create_from_design", "design_id": "D1",
            "data": {k: {"type": "text", "text": v}
                     for k, v in {"day_1": "THU 24", "title_1": "Karaoke"}.items()}}
    assert body["data"]["day_1"] == {"type": "text", "text": "THU 24"}
    assert json.loads(json.dumps(body))["design_id"] == "D1"
    print("selftest: all checks passed")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--no-autofill", action="store_true",
                    help="skip the autofill test so no trial use is spent")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if args.probe:
        return probe(do_autofill=not args.no_autofill)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
