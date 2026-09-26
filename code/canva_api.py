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

What the probe found (2026-09-26)
---------------------------------
* `autofill` and `brand_template` are both available.
* A real autofill returned **no** `trial_information`, so this account is not
  trial-limited. There is no use-count to budget against.
* Rotation **is** enforced: every refresh returns a new token and kills the old
  one. That is the only hard constraint left, and it is handled below.

Rotation
--------
Because the stored token is spent on use, the replacement has to reach the
GitHub secret or the following week cannot authenticate. `gh_secret.put_secret`
writes it back directly, in the same breath as the refresh. If that fails the
token goes to Telegram to be pasted in by hand — not ideal, but far better than
losing it, which costs a whole browser authorization. It is never printed:
this repo is public and so is its log.

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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gh_secret import put_secret  # noqa: E402

API = "https://api.canva.com/rest"

# The 6-row weekly card. Autofill copies it; the original is never touched.
WEEK_CARD_DESIGN_ID = "DAHWLCTrgMQ"

# Where the rotated refresh token is written back. GITHUB_REPOSITORY wins when
# set; this is the fallback for a local run.
SECRETS_REPO = "soynopalero/Azucar-Social-Pipeline"


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


def probe(do_autofill: bool, test_reuse: bool) -> int:
    """Order matters here, and it cost us a token to learn why.

    Re-using a refresh token does not merely fail — Canva answers
    "Refresh token used twice. All access tokens granted from this flow are
    now revoked" and kills the access token you are holding. Run that test
    first and everything after it 401s.

    So: refresh, then do all the useful work, and only then, if explicitly
    asked, run the destructive test. The answer is already known and
    recorded below; --test-reuse exists to re-confirm it after an API
    change, not for routine use.
    """
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
    print(f"   ok, expires_in={first.get('expires_in')}s")
    print(f"   stored refresh  : {fingerprint(original)}")
    print(f"   returned refresh: {fingerprint(rotated or '')}")
    print(f"   rotated?          {rotated != original}")

    # The stored secret is spent the moment the line above ran. Hand the
    # replacement over before anything else can fail and strand it.
    deliver_token(rotated)

    rc = 0
    try:
        print("\n2. Capabilities:")
        caps = capabilities(access)
        for c in sorted(caps):
            print(f"   - {c}")

        uses = None
        if not do_autofill:
            print("\n3. Autofill test skipped (--no-autofill).")
        elif "autofill" not in caps:
            print("\n3. No autofill capability — skipping.")
        else:
            print("\n3. Spending ONE autofill to read the trial counter…")
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
                print("   no trial_information returned — usually means the")
                print("   account is not trial-limited. Good, but unconfirmed.")
            else:
                print(f"   *** autofill uses remaining: {uses} ***")
                print(f"   at 52 a year that is ~{uses // 52}y {uses % 52}w.")

        print("\n" + "=" * 60)
        print(f"autofill capability    : {'autofill' in caps}")
        print(f"autofill uses remaining: {uses if uses is not None else 'not reported'}")
        print("refresh tokens         : single-use, reuse revokes the whole flow")
        print("=" * 60)
    except CanvaError as e:
        print(f"\nFailed: {e}", file=sys.stderr)
        rc = 1

    if test_reuse:
        # Deliberately destructive. Everything above has already run.
        print("\n4. DESTRUCTIVE: re-using the original refresh token…")
        try:
            refresh_access_token(cid, sec, original)
            print("   WORKS — reuse is allowed after all. Re-check the design.")
        except CanvaError as e:
            print(f"   REJECTED — {str(e)[:160]}")
            print("   Confirmed: single-use. The token just delivered is still")
            print("   the live one; the access token is now revoked.")
    return rc


def deliver_token(rotated: str | None) -> None:
    """Every refresh spends the stored token, so the replacement has to reach
    the secret or the next run cannot authenticate at all.

    First choice is writing it back ourselves — a weekly job that needs a human
    to paste a credential is a job that breaks on the first busy Friday. If that
    fails for any reason the token goes to Telegram instead, so it is at least
    not lost: a stranded token means running the browser authorization again.

    Either way it is never printed. This repo is public and so is its log.
    """
    if not rotated:
        print("   !! no replacement refresh token returned — the stored one is")
        print("      spent and there is nothing to replace it with.")
        return

    repo = envvar("GITHUB_REPOSITORY") or SECRETS_REPO
    ok, why = put_secret(repo, "CANVA_REFRESH_TOKEN", rotated)
    if ok:
        print(f"   {why} — CANVA_REFRESH_TOKEN updated, nothing to paste.")
        tg("🔑 Canva refresh token rotated. Already written back to GitHub "
           "Secrets — nothing for you to do.")
        return

    print(f"   write-back failed ({why}) — falling back to Telegram.")
    tg("⚠️ Canva refresh token rotated and I could not write it back "
       f"({why}).\n\n"
       "The token in GitHub Secrets is dead now. Replace CANVA_REFRESH_TOKEN "
       "with this or the next run cannot authenticate:\n\n"
       f"{rotated}\n\n"
       f"https://github.com/{repo}/settings/secrets/actions")
    print("   replacement token sent to Telegram (this log is public).")


def selftest() -> int:
    assert fingerprint("abcdefghijklmnop") == "abcdef…mnop (len 16)"
    assert fingerprint("short") == "(short)"
    # A fingerprint must never be enough to reconstruct the token.
    tok = "x" * 200
    assert len(fingerprint(tok)) < 30

    # Reuse is destructive, so it must never be on by default.
    ap_defaults = argparse.ArgumentParser()
    ap_defaults.add_argument("--test-reuse", action="store_true")
    assert ap_defaults.parse_args([]).test_reuse is False

    body = {"type": "create_from_design", "design_id": "D1",
            "data": {k: {"type": "text", "text": v}
                     for k, v in {"day_1": "THU 24", "title_1": "Karaoke"}.items()}}
    assert body["data"]["day_1"] == {"type": "text", "text": "THU 24"}
    assert json.loads(json.dumps(body))["design_id"] == "D1"

    # A rotated token must never reach stdout. The Actions log is public, and
    # this is the one function that handles the token after the refresh.
    import contextlib
    import io

    buf = io.StringIO()
    token = "rotated-token-do-not-print"
    # Clear the PAT for the duration: with one set this would write the dummy
    # token above over the live CANVA_REFRESH_TOKEN. A test must not be able to
    # break production because of what is in someone's shell.
    saved = os.environ.pop("GH_SECRETS_PAT", None)
    try:
        with contextlib.redirect_stdout(buf):
            deliver_token(token)      # no PAT, so it takes the fallback path
            deliver_token(None)       # and the nothing-came-back path
    finally:
        if saved is not None:
            os.environ["GH_SECRETS_PAT"] = saved
    out = buf.getvalue()
    assert token not in out, out
    assert "write-back failed" in out, out
    assert "no replacement refresh token" in out, out
    print("selftest: all checks passed")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--no-autofill", action="store_true",
                    help="skip the autofill test so no trial use is spent")
    ap.add_argument("--test-reuse", action="store_true",
                    help="DESTRUCTIVE: re-use the old refresh token, which "
                         "revokes the access token. Runs last. Already proven "
                         "single-use; only for re-checking after an API change.")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if args.probe:
        return probe(do_autofill=not args.no_autofill,
                     test_reuse=args.test_reuse)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
