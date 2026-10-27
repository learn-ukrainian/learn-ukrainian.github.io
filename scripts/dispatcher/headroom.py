"""Plan-headroom admission and the runtime pre-call stop from the legacy launcher.

The plan check mirrors target_admission._refuse_paused, called by
delegate._admit_dispatch_target and _kimi_worker_refusal. Runtime headroom
mirrors runner.invoke's pre-call has_headroom check. Neither selects a route.
"""

import logging

from scripts.agent_runtime import model_pause, usage
from scripts.agent_runtime.errors import RateLimitedError
from scripts.fleet import claude_account_lane


def check_plan(agent: str, model: str, record: dict, *, review: bool = False) -> None:
    """Read the named account again; pins and host overrides do not bypass policy.

    Unknown/stale usage and missing/invalid policy retain the shared reader's
    fail-open contract. Reviews protect Claude headroom only; model pauses
    still apply to every selected model (target_admission.py:553-565).
    """
    account = claude_account_lane.account_from_record(record, agent=agent)
    if agent == "claude" and account.refusal is not None:
        raise ValueError(f"CLAUDE_ACCOUNT_REFUSED: {account.refusal}")
    used_pct = model_pause.account_used_pct(account)
    model_pause.refuse_paused_models(
        [model], used_pct=lambda lane: used_pct(lane) if not review or lane == "claude" else None,
    )


def check_runtime(agent: str, model: str) -> None:
    """Stop before provider construction on the shared recent rate-limit reading.

    has_headroom owns the event window, threshold and LU_BYPASS_RATE_LIMIT
    override. Its key is (agent, model), not an account; a lane summary's
    unattributed headroom_blocked flag is never an account's plan meter.
    """
    unreadable = {"files": 0, "lines": 0, "records": 0}
    ok, reason = usage.has_headroom(agent, model, unreadable=unreadable)
    if any(unreadable.values()):
        logging.getLogger(__name__).warning("Headroom check for %s/%s: unreadable usage records %s",
                                           agent, model, unreadable)
    if not ok:
        raise RateLimitedError(agent, model, reason)
