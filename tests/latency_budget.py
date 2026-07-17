"""Wall-clock latency budgets for smoke tests (#5360).

Absolute second thresholds cannot distinguish "endpoint got slow" from
"CI runner is busy". On CI they are advisory (``::warning::`` + recorded
numbers); locally they hard-fail. Quiet-runner / nightly hard-fail is
available via ``ENFORCE_LATENCY_ASSERTIONS=1``.
"""

from __future__ import annotations

import os

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def latency_assertions_enforce() -> bool:
    """Return True when absolute latency budgets must hard-fail.

    Hard-fail when:
    - ``ENFORCE_LATENCY_ASSERTIONS`` is truthy (quiet-runner / nightly), or
    - we are not on CI (local developer machine).

    Soft-fail (advisory) when on CI without the enforce flag.
    """
    flag = os.environ.get("ENFORCE_LATENCY_ASSERTIONS", "").strip().lower()
    if flag in _TRUTHY:
        return True
    return not (os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"))


def assert_under_budget(elapsed: float, budget: float, message: str) -> None:
    """Assert ``elapsed < budget``, or emit a CI advisory warning.

    Under budget: no-op. Over budget + enforce: ``AssertionError``.
    Over budget + CI advisory: print ``::warning::{message}`` and continue.
    """
    if elapsed < budget:
        return
    if latency_assertions_enforce():
        raise AssertionError(message)
    # GitHub Actions picks up workflow commands on stdout.
    print(f"::warning::{message}", flush=True)
