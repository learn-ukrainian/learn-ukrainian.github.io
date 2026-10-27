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
    any worktree exists; a refusal, an unknown label included (``claude_account_unknown``), raises
    ``ValueError`` with the legacy ``ClaudeAccountRefused`` code. Another seat may not name a
    non-default account (``claude_account_seat_unsupported``) and records none. A non-default label
    loads none of its login directory's user settings (:func:`claude_launch`), recorded as
    ``claude_account_user_scope_omitted`` (#10619).
    """
    from scripts.agent_runtime.attempt_boundary import (
        CLAUDE_ACCOUNT_KEY,
        CLAUDE_ACCOUNT_SOURCE_KEY,
        DEFAULT_CLAUDE_ACCOUNT,
        ClaudeAccountRefused,
        resolve_claude_account_label,
        resolve_dispatch_claude_account,
        verify_claude_account,
    )

    try:
        if agent != "claude":
            if resolve_claude_account_label(explicit) != DEFAULT_CLAUDE_ACCOUNT:
                raise ClaudeAccountRefused("claude_account_seat_unsupported")
            # v2 never reselects a claude reviewer for another seat, so no other seat reads the account file.
            return {}
        # ``claude_account_lane.resolve_route_account(explicit, strict=True)`` without a recorded
        # label (v2 has no --force-new re-run): flag, default-account file, built-in default.
        label, source = resolve_dispatch_claude_account(explicit)
        binding = verify_claude_account(label)
    except ClaudeAccountRefused as exc:
        raise ValueError(f"CLAUDE_ACCOUNT_REFUSED: {exc.code}") from None
    fields = {CLAUDE_ACCOUNT_KEY: label, CLAUDE_ACCOUNT_SOURCE_KEY: source}
    if binding is not None:  # v2 launches no sealed review attempt, so every labelled run omits the user scope
        fields["claude_account_user_scope_omitted"] = True
    return fields


def claude_launch(spec, invocation):
    """Bind a labelled Claude run to its verified login, at the launch boundary (#10619).

    Composes the legacy worker-side checks (``adapters/claude.py`` ``_claude_account_binding`` and
    ``_verified_labelled_launch``) over the v2 environment: the binding is verified again in the
    supervisor and its login directory becomes ``CLAUDE_CONFIG_DIR``; ``claude auth status``, run
    with the launch's own ``--settings``, ``--setting-sources project,local``, working directory and
    environment, must report the bound subscription login and nothing else, so a checkout setting
    such as ``apiKeyHelper`` refuses (``claude_account_auth_method_conflict``); the inputs must not
    change while verified and no machine policy may exist. The returned argv runs the CLI behind
    the legacy launch guard, which recomputes the inputs digest in the spawned process. The default
    label and other seats are returned unchanged. A refusal raises ``ValueError`` with the code.
    """
    from scripts.agent_runtime.adapters import claude as adapter
    from scripts.agent_runtime.attempt_boundary import (
        CLAUDE_AUTH_SUBSCRIPTION_LOGIN,
        DEFAULT_CLAUDE_ACCOUNT,
        ClaudeAccountRefused,
        note_claude_account_verified,
        refuse_claude_machine_policy,
        resolve_claude_account_label,
        verify_claude_account,
    )
    from scripts.agent_runtime.env_sanitize import (
        claude_fingerprints_match,
        claude_labelled_inputs_digest,
        claude_login_credential_fingerprint,
    )
    from scripts.common.repo_root import project_interpreter
    from scripts.dispatcher.types import Invocation

    if spec.agent != "claude":
        return invocation
    try:
        label = resolve_claude_account_label(spec.claude_account)
        if label == DEFAULT_CLAUDE_ACCOUNT:
            return invocation
        binding = verify_claude_account(label)
        if binding is None:  # only the default label verifies without a binding
            raise ClaudeAccountRefused("claude_account_default_has_no_binding")
        login_dir = str(binding.config_dir)
        env = {**invocation.env, "CLAUDE_CONFIG_DIR": login_dir}
        argv = invocation.argv
        settings = argv[argv.index("--settings") + 1]
        sources = argv[argv.index("--setting-sources") + 1]
        if sources != adapter.LABELLED_ACCOUNT_SETTING_SOURCES:
            raise ClaudeAccountRefused("claude_account_settings_changed")

        def digest() -> str:
            return claude_labelled_inputs_digest(
                login_dir=login_dir, cwd=spec.worktree, settings=settings, setting_sources=sources, environ=env
            )

        verified = digest()
        adapter._verify_labelled_auth_method((argv[0],), settings, cwd=spec.worktree, env=env, login_dir=login_dir)
        if not claude_fingerprints_match(digest(), verified) or not claude_fingerprints_match(
            claude_login_credential_fingerprint(login_dir), binding.credential
        ):
            raise ClaudeAccountRefused("claude_account_settings_changed")
        refuse_claude_machine_policy()
        note_claude_account_verified(label, CLAUDE_AUTH_SUBSCRIPTION_LOGIN)
    except ClaudeAccountRefused as exc:
        raise ValueError(f"CLAUDE_ACCOUNT_REFUSED: {exc.code}") from None
    guarded = [str(project_interpreter()), "-I", "-c", adapter._LAUNCH_GUARD_CODE, str(adapter._CODE_ROOT), verified]
    return Invocation([*guarded, "--", *argv], invocation.stdin, env, invocation.final_file)


def hold_review_test_slots(
    *, agent: str, mode: str, review_typed: bool, sealed_attempt: bool, task_id: str
) -> tuple[test_slots.Hold | None, dict | None]:
    """Take a Codex read-only review's test slots in the supervisor, before its sandbox starts (#11230, #10744).

    Mechanical copy of ``delegate._hold_review_test_slots``. Codex's read-only sandbox cannot prepare
    the pool, so the supervisor queues in the host pool and holds ``review`` slots until the provider
    returns; the CLI's governed runs check the holder marker read-only. Other routes, and sealed
    attempts whose inputs carry no pool, take their own slots or none. A refusal is recorded and the
    review runs on; its governed runs are then refused, typed. Returns the hold (or ``None``) and the
    record for the task's ``review_test_slots`` field. As in legacy, the hold ends with the supervisor
    process, so a crash or kill releases it; governed runs in flight keep their slots through their own
    shared locks until they exit.
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


def spawn_supervisor(
    cmd: list[str], *, task_id: str, run_nonce: str, cwd: Path, stderr, stderr_log: Path, env: dict[str, str],
):
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
            env=env,
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
    except (OSError, ValueError) as exc:
        # No supervisor process exists: fail like the legacy spawn instead of reporting a crash.
        message = f"Popen failed: {type(exc).__name__}: {exc}"[:500]
        raise LaunchRefused(message, {"status": "failed", "error": f"worker_spawn_failed: {message}"}) from None
    return process, launch.as_state()
