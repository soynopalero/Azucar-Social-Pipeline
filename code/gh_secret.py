#!/usr/bin/env python3
"""
gh_secret.py
------------
Write a value back into this repo's GitHub Actions secrets.

Why this exists
---------------
Canva refresh tokens are single-use: every refresh spends the stored one and
hands back a replacement. A fixed `CANVA_REFRESH_TOKEN` secret therefore works
exactly once. Either a human pastes a new token in every week, or the job that
spent it puts the replacement back. This is the second option.

The same shape is coming for Instagram — its long-lived token expires every 60
days and is refreshed the same way — so this is a module, not a helper buried
in the Canva client.

What it needs
-------------
`GH_SECRETS_PAT`: a fine-grained PAT scoped to this repository alone, with
**Secrets: Read and write** and nothing else. The built-in GITHUB_TOKEN cannot
do this — there is no `secrets: write` permission to grant it.

That PAT can write any secret in this repo, so it is the most powerful
credential in the pipeline. Scope it to the one repo, and to Secrets only.

How GitHub wants it
-------------------
Secrets are encrypted client-side with libsodium's sealed box against the
repo's public key, so the plaintext never reaches the API. That needs PyNaCl —
`pip install pynacl`. Everything else here is stdlib.

Usage:
    from gh_secret import put_secret
    ok, why = put_secret("owner/repo", "CANVA_REFRESH_TOKEN", tok, pat)

    python code/gh_secret.py --selftest
"""
from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.request

GH_API = "https://api.github.com"


def _api(method: str, path: str, pat: str, payload: dict | None = None) -> dict:
    req = urllib.request.Request(
        f"{GH_API}{path}",
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"authorization": f"Bearer {pat}",
                 "accept": "application/vnd.github+json",
                 "x-github-api-version": "2022-11-28",
                 "content-type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read()
        return json.loads(body) if body else {}


def seal(value: str, public_key_b64: str) -> str:
    """Encrypt with libsodium's sealed box, which is what GitHub accepts.

    Imported here rather than at module scope so the offline selftest — and any
    caller that only wants the fallback path — runs without PyNaCl installed.
    """
    from nacl import encoding, public  # noqa: PLC0415

    box = public.SealedBox(public.PublicKey(public_key_b64.encode(),
                                            encoding.Base64Encoder()))
    return base64.b64encode(box.encrypt(value.encode())).decode()


def put_secret(repo: str, name: str, value: str,
               pat: str | None = None) -> tuple[bool, str]:
    """Set an Actions secret. Returns (ok, reason).

    Never raises and never puts `value` in the reason: callers log the reason
    to a public Actions log, and the values passed here are credentials.
    """
    pat = (pat or os.environ.get("GH_SECRETS_PAT") or "").strip()
    if not pat:
        return False, "no GH_SECRETS_PAT set"
    if not repo or "/" not in repo:
        return False, f"need owner/repo, got {repo!r}"
    try:
        key = _api("GET", f"/repos/{repo}/actions/secrets/public-key", pat)
        encrypted = seal(value, key["key"])
        _api("PUT", f"/repos/{repo}/actions/secrets/{name}", pat,
             {"encrypted_value": encrypted, "key_id": key["key_id"]})
        return True, f"wrote {name}"
    except ImportError:
        return False, "PyNaCl not installed (pip install pynacl)"
    except urllib.error.HTTPError as e:
        # 403 here almost always means the PAT lacks Secrets: write, which is
        # worth saying plainly — it is the one setting people miss.
        detail = e.read().decode("utf-8", "replace")[:200]
        hint = " (PAT needs Secrets: Read and write)" if e.code == 403 else ""
        return False, f"GitHub said {e.code}{hint}: {detail}"
    except Exception as e:                      # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"


def selftest() -> int:
    # The failure path must never leak the value it was handed, because the
    # reason is printed straight into a public Actions log.
    secret = "s3cr3t-token-value"
    for repo in ("owner/repo", "", "not-a-repo"):
        ok, why = put_secret(repo, "X", secret, pat="")
        assert ok is False
        assert secret not in why, why

    ok, why = put_secret("not-a-repo", "X", secret, pat="ghp_fake")
    assert ok is False and "owner/repo" in why, why
    assert secret not in why

    # A bad PAT must come back as a reason, not an exception: the caller's job
    # is to fall back to Telegram, and a traceback would skip that.
    ok, why = put_secret("soynopalero/Azucar-Social-Pipeline", "X", secret,
                         pat="ghp_definitely_not_valid")
    assert ok is False, why
    assert secret not in why

    print("gh_secret selftest: all checks passed")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(selftest())
    print(__doc__)
