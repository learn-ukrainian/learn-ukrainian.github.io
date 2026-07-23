#!/usr/bin/env python3
"""Prove the Kimi Code OAuth refresh-token chain is healthy.

The canary intentionally performs one real ``refresh_token`` grant and persists
the rotated credential through :mod:`scripts.lib.kimi_coding_oauth`. It does
not print an access token. Run it from the repository root:

    .venv/bin/python -m scripts.canary.kimi_oauth_canary

For unattended use, schedule it no more frequently than every 30 minutes;
forcing a refresh more often creates needless refresh-token churn.

On a failure, the canary returns the OAuth helper's compatible exit code and
posts a redacted, action-required system alert to the ``fleet-comms`` channel.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ai_agent_bridge import _channels
from scripts.lib import kimi_coding_oauth

ALERT_CHANNEL = "fleet-comms"
ALERT_RECIPIENTS = ["kimi", "claude-infra"]


@dataclass(frozen=True, slots=True)
class CanaryResult:
    """Outcome that keeps alert delivery separate from OAuth health."""

    exit_code: int
    alert_posted: bool
    failure_kind: str | None = None


def _failure_kind(exc: BaseException) -> tuple[str, int]:
    if isinstance(exc, kimi_coding_oauth.NoCredentialsError):
        return "credentials", 2
    if isinstance(exc, kimi_coding_oauth.RefreshFailedError):
        return "refresh", 3
    return "local_io", 3


def post_failure_alert(failure_kind: str) -> bool:
    """Post a metadata-only alert; alert errors never mask OAuth failure."""
    body = (
        "ACTION REQUIRED: Kimi OAuth refresh canary failed. "
        f"component=kimi_oauth_refresh; failure_kind={failure_kind}. "
        "Run `.venv/bin/python -m scripts.canary.kimi_oauth_canary`; if credentials are invalid, run `kimi login`."
    )
    try:
        _channels.post(
            ALERT_CHANNEL,
            "kimi",
            body,
            to_agents=ALERT_RECIPIENTS,
            correlation_id="canary:kimi-oauth-refresh",
            kind="system",
            priority=_channels.PRIORITY_ACTION_REQUIRED,
            auto_snapshot=False,
            verify_citations=False,
        )
    except Exception as exc:
        # Do not include the OAuth exception here: an upstream response could
        # echo sensitive request material. The command's non-zero exit remains
        # the durable signal when fleet-comms itself is unavailable.
        print(f"kimi-oauth-canary: fleet-comms alert failed: {type(exc).__name__}", file=sys.stderr)
        return False
    return True


def run_canary(
    *,
    refresh: Callable[[], str] = kimi_coding_oauth.force_refresh_token,
    alert: Callable[[str], bool] = post_failure_alert,
) -> CanaryResult:
    """Force the refresh grant and alert on any credential, remote, or I/O failure."""
    try:
        refresh()
    except (kimi_coding_oauth.NoCredentialsError, kimi_coding_oauth.RefreshFailedError, OSError, ValueError) as exc:
        failure_kind, exit_code = _failure_kind(exc)
        alert_posted = alert(failure_kind)
        print(f"kimi-oauth-canary: FAIL ({failure_kind})", file=sys.stderr)
        return CanaryResult(exit_code=exit_code, alert_posted=alert_posted, failure_kind=failure_kind)
    print("kimi-oauth-canary: PASS (refresh grant succeeded)")
    return CanaryResult(exit_code=0, alert_posted=False)


def main() -> int:
    return run_canary().exit_code


if __name__ == "__main__":
    raise SystemExit(main())
