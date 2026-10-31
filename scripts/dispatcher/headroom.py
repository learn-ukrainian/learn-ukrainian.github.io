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

    Applicable caps refuse unknown/stale usage. Reviews protect native Claude
    headroom only; model pauses still apply to every selected model.
    """
    account = claude_account_lane.account_from_record(record, agent=agent)
    if agent == "claude" and account.refusal is not None:
        raise ValueError(f"CLAUDE_ACCOUNT_REFUSED: {account.refusal}")
    model_pause.refuse_paused_models(
        [model], policy=model_pause.policy_for_seat(agent, review=review),
        used_pct=model_pause.account_used_pct(account),
    )
    from scripts.dispatcher import checks

    trial = checks.check_trial_shadow(agent, model, record)
    roles = model_pause.dispatch_roles(record, review=review)
    model_pause.refuse_model_roles(model, roles, shadow=bool(trial))


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
