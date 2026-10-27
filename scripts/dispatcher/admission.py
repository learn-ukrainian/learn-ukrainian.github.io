"""Launch protections the legacy launcher applied: Claude account, review test slots, systemd placement.

Ported from ``scripts/delegate.py`` (C-2188 unit D). Each helper names the legacy function whose
refusal conditions, error text and recorded fields it keeps.
"""

import functools
import subprocess
import sys
from pathlib import Path

from scripts.common import test_slots
from scripts.orchestration import dispatch_isolation

# Slots a Codex read-only review holds for its reviewer: the review bound of two test workers (cto-10744).
REVIEW_TEST_SLOTS = 2


def review_typed(record: dict) -> bool:
    """True when a PR target or any review flag types this task as a review (``delegate._dispatch_is_review_typed``).

    v2 has no ``--review``/``--type`` flags; ``--risk`` is stored as ``review_risk`` and a bound
    review id as ``review_attempt``.
    """
    return any(
        record.get(name) not in (None, False, "", [])
        for name in (
            "pr", "review_attempt", "require_review_verdict", "review_profile", "review_author_model", "review_risk",
        )
    )


def claude_account(agent: str, explicit: str | None) -> dict:
    """The resolved account fields a dispatch records (``delegate._resolve_dispatch_claude_account`` and
    ``_claude_account_state``).

    A claude request resolves its label from ``--claude-account``, the default-account file, then
    the built-in default, and verifies a non-default label's binding and credential sources before
    any worktree exists; a refusal raises ``ValueError`` with the legacy ``ClaudeAccountRefused``
    code. Another seat may not name a non-default account (``claude_account_seat_unsupported``) and
    records none. The verified login directory must be the one ``environment.child_env`` selects, so
    a worker never authenticates in a directory the binding did not verify.
    """
    from scripts.agent_runtime.attempt_boundary import (
        CLAUDE_ACCOUNT_KEY,
        CLAUDE_ACCOUNT_SOURCE_KEY,
        DEFAULT_CLAUDE_ACCOUNT,
        ClaudeAccountRefused,
        resolve_claude_account_label,
        verify_claude_account,
    )

    try:
        if agent != "claude":
            if resolve_claude_account_label(explicit) != DEFAULT_CLAUDE_ACCOUNT:
                raise ClaudeAccountRefused("claude_account_seat_unsupported")
            # v2 never reselects a claude reviewer for another seat, so no other seat reads the account file.
            return {}
        from scripts.fleet import claude_account_lane

        account = claude_account_lane.resolve_route_account(explicit, strict=True)
        if account.label is None:
            raise ClaudeAccountRefused(account.refusal or "claude_account_unknown")
        binding = verify_claude_account(account.label)
    except ClaudeAccountRefused as exc:
        raise ValueError(f"CLAUDE_ACCOUNT_REFUSED: {exc.code}") from None
    if binding is not None:
        from scripts.dispatcher.environment import claude_config_dir

        if Path(binding.config_dir).resolve() != Path(claude_config_dir(account.label)).resolve():
            raise ValueError("CLAUDE_ACCOUNT_REFUSED: bound login directory is not the dispatcher's account directory")
    return {CLAUDE_ACCOUNT_KEY: account.label, CLAUDE_ACCOUNT_SOURCE_KEY: account.source}


def hold_review_test_slots(
    *, agent: str, mode: str, review_typed: bool, sealed_attempt: bool, task_id: str
) -> tuple[test_slots.Hold | None, dict | None]:
    """Take a Codex read-only review's test slots in the supervisor, before its sandbox starts (#11230, #10744).

    Mechanical copy of ``delegate._hold_review_test_slots``. Codex's read-only sandbox cannot prepare
    the pool, so the supervisor queues in the host pool and holds ``review`` slots until the provider
    returns; the CLI's governed runs check the holder marker read-only. Other routes, and sealed
    attempts whose inputs carry no pool, take their own slots or none. A refusal is recorded and the
    review runs on; its governed runs are then refused, typed. Returns the hold (or ``None``) and the
    record for the task's ``review_test_slots`` field. The hold's locks end with the supervisor
    process, so a crash or kill releases the slots too.
    """
    if agent != "codex" or mode != "read-only" or not review_typed or sealed_attempt:
        return None, None
    try:
        if not test_slots.enabled():
            return None, {"outcome": "disabled"}
        hold = test_slots.acquire(REVIEW_TEST_SLOTS, kind="review", task_id=task_id)
    except test_slots.SlotError as error:
        print(f"[dispatcher] WARNING: review test slots refused: {error}", file=sys.stderr)
        return None, {"outcome": "refused", "reason": error.reason}
    return hold, {"outcome": "held", "slots": hold.count, "waited_s": round(hold.waited, 1)}


class LaunchRefused(ValueError):
    """No supervisor was started, or its start was ambiguous and must not be retried."""

    def __init__(self, message: str, fields: dict):
        super().__init__(message)
        self.fields = fields


def spawn_supervisor(cmd: list[str], *, task_id: str, run_nonce: str, cwd: Path, stderr, stderr_log: Path):
    """Start the supervisor in ``lu-dispatch.slice`` or, when isolation is unavailable, with plain ``Popen``.

    Mirrors the legacy spawn (``delegate.py`` ``dispatch_isolation.spawn_detached_worker`` call): the
    returned pid is the supervisor in both cases, and the launch fields (``launch_mode``,
    ``launch_unit``, ``launch_fallback_reason``, ``launch_user_bus``) go into the record. A refused
    fallback (a caller inside a driver scope) or an ambiguous scoped start raises
    :class:`LaunchRefused` with the legacy failure code; it is never relaunched.
    """
    try:
        process, launch = dispatch_isolation.spawn_detached_worker(
            cmd,
            task_id=task_id,
            run_nonce=run_nonce,
            popen=functools.partial(subprocess.Popen, cwd=cwd),
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=stderr,
            stderr_log=stderr_log,
        )
    except dispatch_isolation.DispatchIsolationError as exc:
        refused = str(exc).startswith("fallback-refused:")
        code = "dispatch_fallback_refused" if refused else "dispatch_isolation_failed"
        message = f"dispatch isolation: {exc}"[:500]
        raise LaunchRefused(message, {"status": "failed", "error": f"{code}: {message}"}) from None
    return process, launch.as_state()
