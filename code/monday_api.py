"""
Shared Monday.com GraphQL client.

Every scheduled workflow in this repo reads the Events board, so the retry
policy for a flaky Monday API lives in one place instead of being reinvented
(differently, and wrongly) in each script.

Monday reports a server-side failure in one of two shapes:

  * a real HTTP error status (500, 502, 503, ...), or
  * **HTTP 200** with the failure described in the GraphQL ``errors`` array,
    e.g. ``{"extensions": {"code": "INTERNAL_SERVER_ERROR"}}``.

The second shape is by far the common one, and it is what took the whole
pipeline down at 08:12-08:44 UTC on 2026-09-05: the retry wrapper we had only
inspected HTTP status, so it never saw the 200-with-errors response and a
~30-minute Monday outage became a hard workflow failure. Both shapes are
retried here.

Env: MONDAY_API_KEY.
Self-test: python code/monday_api.py --selftest   (offline; no Monday call)
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

MONDAY_URL = "https://api.monday.com/v2"
API_VERSION = "2024-10"

MAX_ATTEMPTS = 4
BASE_BACKOFF = 2.0  # seconds; waits ~2s, 4s, 8s between attempts
RETRY_HTTP_CODES = {429, 500, 502, 503, 504}

# GraphQL extensions.code / extensions.error_code values that mean "Monday is
# having a bad moment", as opposed to a bad query or a bad token. Anything not
# listed here fails immediately — a malformed query won't fix itself in 8s.
TRANSIENT_ERROR_CODES = {
    "INTERNAL_SERVER_ERROR",
    "DOWNSTREAM_SERVICE_ERROR",
    "SERVICE_UNAVAILABLE",
    "GATEWAY_TIMEOUT",
    "TIMEOUT",
    "RATE_LIMIT_EXCEEDED",
}


class MondayError(RuntimeError):
    """A Monday GraphQL response came back carrying an `errors` array."""

    def __init__(self, errors):
        self.errors = errors
        super().__init__(json.dumps(errors))


def is_transient_errors(errors) -> bool:
    """True if a GraphQL `errors` array describes a failure worth retrying.

    Any transient entry makes the whole response retryable: a response mixing a
    permanent error with a transient one is retried and then surfaces the real
    error, which is the safer way round.
    """
    if not isinstance(errors, list):
        errors = [errors]
    for err in errors:
        if not isinstance(err, dict):
            continue
        ext = err.get("extensions")
        if not isinstance(ext, dict):
            continue
        status = ext.get("status_code")
        if isinstance(status, int) and status in RETRY_HTTP_CODES:
            return True
        for key in ("code", "error_code"):
            value = ext.get(key)
            if isinstance(value, str) and value.strip().upper() in TRANSIENT_ERROR_CODES:
                return True
    return False


def _backoff(attempt: int, what: str, reason) -> None:
    wait = BASE_BACKOFF * (2 ** (attempt - 1))
    print(f"  … {what} failed ({reason}); retry {attempt}/{MAX_ATTEMPTS - 1} in {wait:.0f}s",
          flush=True)
    time.sleep(wait)


def api_key() -> str:
    key = (os.environ.get("MONDAY_API_KEY") or "").strip()
    if not key:
        sys.exit("MONDAY_API_KEY env var is empty — export it locally, or add it "
                 "as a repo secret for the workflow.")
    return key


def urlopen_retry(target, *, timeout: int, what: str) -> bytes:
    """urlopen() that retries transient network errors, returning the body.

    Used for Monday's asset CDN as well as the API — signed flyer URLs stall
    often enough that one bad fetch shouldn't sink a run.
    """
    last_err: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(target, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code not in RETRY_HTTP_CODES:
                raise  # 4xx (other than 429) won't fix itself — fail fast
            last_err = e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_err = e
        if attempt < MAX_ATTEMPTS:
            _backoff(attempt, what, last_err)
    raise last_err  # type: ignore[misc]


def monday_query(query: str, variables: dict | None = None, *,
                 timeout: int = 45, what: str = "Monday API") -> dict:
    """Run a GraphQL query and return its `data`, retrying transient failures.

    Raises MondayError for a permanent GraphQL error, or once the retries for a
    transient one are spent.
    """
    key = api_key()
    payload = json.dumps({"query": query, "variables": variables or {}}).encode()
    headers = {"Content-Type": "application/json",
               "Authorization": key, "API-Version": API_VERSION}

    last_reason: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        req = urllib.request.Request(MONDAY_URL, data=payload, method="POST", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code not in RETRY_HTTP_CODES:
                raise
            last_reason = e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_reason = e
        else:
            errors = body.get("errors")
            if not errors:
                return body["data"]
            if not is_transient_errors(errors):
                raise MondayError(errors)  # a bad query/token — don't burn retries on it
            last_reason = MondayError(errors)
        if attempt < MAX_ATTEMPTS:
            _backoff(attempt, what, last_reason)

    raise last_reason  # type: ignore[misc]


# ---------- self-test ----------

def selftest() -> int:
    """Offline check of the transient/permanent classifier."""
    # The exact payload Monday returned during the 2026-09-05 outage.
    outage = [
        {"message": "Internal Server Error", "extensions": {"code": "INTERNAL_SERVER_ERROR"}},
        {"message": "Internal server error",
         "extensions": {"status_code": 500, "error_code": "INTERNAL_SERVER_ERROR",
                        "code": "DOWNSTREAM_SERVICE_ERROR"}},
    ]
    cases = [
        (outage, True, "2026-09-05 outage payload"),
        ([{"message": "x", "extensions": {"code": "SERVICE_UNAVAILABLE"}}], True, "503 body"),
        ([{"message": "x", "extensions": {"status_code": 502}}], True, "status_code only"),
        ([{"message": "x", "extensions": {"code": "RATE_LIMIT_EXCEEDED"}}], True, "rate limit"),
        ([{"message": "x", "extensions": {"code": "internal_server_error"}}], True, "lowercase"),
        # Permanent — retrying these just delays a failure we can't fix.
        ([{"message": "Invalid query", "extensions": {"code": "GRAPHQL_VALIDATION_FAILED"}}],
         False, "bad query"),
        ([{"message": "Unauthorized", "extensions": {"code": "UNAUTHENTICATED",
                                                     "status_code": 401}}], False, "bad token"),
        ([{"message": "Not found", "extensions": {"status_code": 404}}], False, "404"),
        ([{"message": "no extensions at all"}], False, "bare message"),
        (["a plain string error"], False, "non-dict entry"),
        ([], False, "empty list"),
    ]

    failures = 0
    for errors, expected, label in cases:
        got = is_transient_errors(errors)
        mark = "ok  " if got == expected else "FAIL"
        if got != expected:
            failures += 1
        print(f"  {mark} {label}: transient={got} (expected {expected})")

    waits = [BASE_BACKOFF * (2 ** (a - 1)) for a in range(1, MAX_ATTEMPTS)]
    print(f"  ok   backoff schedule: {waits} (total {sum(waits):.0f}s over {MAX_ATTEMPTS} attempts)")

    if failures:
        print(f"{failures} case(s) failed.")
        return 1
    print(f"All {len(cases)} classifier cases passed.")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit("Nothing to run — this is a library. Try: python code/monday_api.py --selftest")
