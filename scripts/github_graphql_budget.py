"""Probe the authenticated GitHub GraphQL primary budget.

GitHub's GraphQL rate-limit documentation says an API call has a minimum
point cost of 1, so this read-only probe itself consumes at least one point:
https://docs.github.com/en/graphql/overview/rate-limits-and-node-limits-for-the-graphql-api
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Any

QUERY = "query { rateLimit { limit remaining used resetAt } }"
TIMEOUT_SECONDS = 10.0


def _checked_at() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _payload(
    *,
    checked_at: str,
    limit: int | None = None,
    remaining: int | None = None,
    used: int | None = None,
    reset_at: str | None = None,
    exhausted: bool | None,
    error: str | None,
) -> dict[str, Any]:
    return {
        "source": "graphql.rateLimit",
        "limit": limit,
        "remaining": remaining,
        "used": used,
        "reset_at": reset_at,
        "exhausted": exhausted,
        "error": error,
        "checked_at": checked_at,
    }


def _has_rate_limit_error(value: object) -> bool:
    if isinstance(value, dict):
        if value.get("type") in {"RATE_LIMIT", "RATE_LIMITED"} or value.get("code") == "graphql_rate_limit":
            return True
        return any(_has_rate_limit_error(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_rate_limit_error(item) for item in value)
    return False


def _has_http_rate_limit_error(value: object, *, returncode: int | None, stderr: str) -> bool:
    http_status_in_stderr = re.search(r"\bHTTP\s+(?:403|429)\b", stderr, flags=re.IGNORECASE) is not None

    if isinstance(value, dict):
        status = value.get("status")
        message = value.get("message")
        if (
            str(status) in {"403", "429"}
            or (returncode not in (None, 0) and http_status_in_stderr)
        ) and isinstance(message, str) and "api rate limit exceeded" in message.casefold():
            return True
        return any(
            _has_http_rate_limit_error(item, returncode=returncode, stderr=stderr)
            for item in value.values()
        )
    if isinstance(value, list):
        return any(_has_http_rate_limit_error(item, returncode=returncode, stderr=stderr) for item in value)
    return False


def _has_secondary_rate_limit_error(value: object) -> bool:
    if isinstance(value, dict):
        message = value.get("message")
        if isinstance(message, str) and "you have exceeded a secondary rate limit" in message.casefold():
            return True
        return any(_has_secondary_rate_limit_error(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_secondary_rate_limit_error(item) for item in value)
    return False


def _safe_error(stdout: str, stderr: str, fallback: str) -> str:
    message = (stderr or stdout or fallback).strip()
    # gh diagnostics are not an API surface; cap output and discard control chars.
    message = " ".join(message.split())
    return message[:500] or fallback


def _run(
    runner: Callable[..., Any],
) -> tuple[Any, str, str, int | None, str | None]:
    """Return completed process details or a normalized local failure."""
    try:
        proc = runner(
            ["gh", "api", "graphql", "-f", f"query={QUERY}"],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError:
        return None, "", "", None, "gh CLI not found"
    except subprocess.TimeoutExpired:
        return None, "", "", None, f"gh api graphql timed out after {TIMEOUT_SECONDS:g}s"
    except OSError as exc:
        return None, "", "", None, f"gh api graphql failed: {type(exc).__name__}"
    except Exception as exc:
        return None, "", "", None, f"gh api graphql runner failed: {type(exc).__name__}"
    return (
        proc,
        getattr(proc, "stdout", "") or "",
        getattr(proc, "stderr", "") or "",
        getattr(proc, "returncode", None),
        None,
    )


def probe_graphql_budget(
    runner: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Return one bounded ``rateLimit`` observation; never consult REST.

    ``rateLimit`` is the authoritative GraphQL budget field. GitHub documents
    that every GraphQL API call costs at least one point, including this probe.
    """
    checked_at = _checked_at()
    _proc, stdout, stderr, returncode, local_error = _run(runner or subprocess.run)
    if local_error:
        return _payload(checked_at=checked_at, exhausted=None, error=local_error)

    try:
        decoded = json.loads(stdout)
    except (TypeError, json.JSONDecodeError):
        return _payload(
            checked_at=checked_at,
            exhausted=None,
            error=_safe_error(stdout, stderr, "gh api graphql returned malformed JSON"),
        )

    if not isinstance(decoded, dict):
        return _payload(checked_at=checked_at, exhausted=None, error="GraphQL response was not an object")

    if _has_secondary_rate_limit_error(decoded):
        # Secondary limits are a separate abuse-control mechanism, not proof
        # that the primary GraphQL point budget is exhausted.
        return _payload(
            checked_at=checked_at,
            exhausted=None,
            error=_safe_error(stdout, stderr, "GitHub secondary rate limit; primary budget is unknown"),
        )

    if _has_rate_limit_error(decoded) or _has_http_rate_limit_error(
        decoded, returncode=returncode, stderr=stderr
    ):
        return _payload(
            checked_at=checked_at,
            remaining=0,
            exhausted=True,
            error=_safe_error(stdout, stderr, "GraphQL rate limit exhausted"),
        )

    rate_limit = decoded.get("data", {}).get("rateLimit") if isinstance(decoded.get("data"), dict) else None
    if returncode != 0 or not isinstance(rate_limit, dict):
        return _payload(
            checked_at=checked_at,
            exhausted=None,
            error=_safe_error(stdout, stderr, "GraphQL response omitted data.rateLimit"),
        )

    values = (rate_limit.get("limit"), rate_limit.get("remaining"), rate_limit.get("used"))
    if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in values):
        return _payload(checked_at=checked_at, exhausted=None, error="GraphQL data.rateLimit was malformed")
    reset_at = rate_limit.get("resetAt")
    if not isinstance(reset_at, str) or not reset_at:
        return _payload(checked_at=checked_at, exhausted=None, error="GraphQL data.rateLimit.resetAt was malformed")

    limit, remaining, used = values
    return _payload(
        checked_at=checked_at,
        limit=limit,
        remaining=remaining,
        used=used,
        reset_at=reset_at,
        exhausted=remaining == 0,
        error=None,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read the authenticated GitHub GraphQL primary budget using rateLimit.\n"
            "Use for budget health; do not use REST /rate_limit as a GraphQL signal."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.github_graphql_budget\n"
            "  .venv/bin/python -m scripts.github_graphql_budget --json\n\n"
            "Outputs: one probe object on stdout; no files or database changes.\n"
            "Exit codes: 0 healthy, 2 exhausted, 3 unknown/probe failure.\n"
            "Related: GitHub GraphQL rate limits; issue #8535 item 4."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--json", action="store_true", help="Print compact JSON instead of a human-readable summary (default: false).")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = probe_graphql_budget()
    if args.json:
        print(json.dumps(result, separators=(",", ":")))
    else:
        state = "unknown" if result["exhausted"] is None else "exhausted" if result["exhausted"] else "healthy"
        remaining = result["remaining"]
        suffix = f" ({remaining} points remaining)" if remaining is not None else ""
        detail = f": {result['error']}" if result["error"] else ""
        print(f"GitHub GraphQL budget: {state}{suffix}{detail}")
    return 0 if result["exhausted"] is False else 2 if result["exhausted"] is True else 3


if __name__ == "__main__":
    sys.exit(main())
