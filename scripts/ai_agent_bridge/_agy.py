"""Agy (Antigravity CLI) interaction: ask_agy and process_for_agy.

Mirrors the codex bridge shape (one-shot send + runtime invoke + response
write-back via the broker). Agy is the Gemini-3.5-Flash-High Antigravity
CLI; docs at https://antigravity.google/docs/cli-overview. Agy is used
for cheap, fast Q&A and short coordination — NOT long-running task
execution. Long-running V7 writer-phase work goes through
``delegate.py dispatch --agent agy`` instead.
"""

import json
import os
from pathlib import Path

from agent_runtime import runner as agent_runner
from agent_runtime.errors import (
    AgentStalledError,
    AgentTimeoutError,
    AgentUnavailableError,
    RateLimitedError,
)

from scripts.common.scratch import ensure_scratch_root

from ._ask_contract import (
    requested_effort,
    resolve_model_selection,
    response_provenance,
    unsupported_effort_note,
)
from ._ask_lifecycle import launch_background_ask, record_ask_failure, record_ask_reply, register_ask
from ._config import REPO_ROOT
from ._db import get_db, set_session
from ._messaging import acknowledge, send_message
from ._prompts import build_agy_prompt
from ._review_worktree import (
    ReviewWorktreeError,
    append_review_prompt_evidence,
    provision_review_worktree,
    review_target_from_message,
    review_target_payload,
)

_DEFAULT_AGY_BRIDGE_TIMEOUT_SECONDS = 900
_NO_TIMEOUT_AGY_BRIDGE_TIMEOUT_SECONDS = 24 * 60 * 60


def _default_agy_model() -> str:
    """The AGY seat's model, read from the live ACP participant registry.

    Never an independently hardcoded slug: the registry pin is what the route
    resolver enforces, so deriving the default from it makes stale-slug drift
    impossible (#6894).
    """
    from agent_runtime.adapters.acpx import ACPX_SUPPORTED_PARTICIPANTS

    pin = ACPX_SUPPORTED_PARTICIPANTS["agy"]["model"]
    assert pin is not None  # the agy participant is always pinned
    return pin


def _agy_ask_scratch_cwd() -> Path:
    """Out-of-tree scratch cwd for unsandboxed agy bridge asks.

    Must live OUTSIDE the repository tree: the runner's worktree containment
    guard (#4444) refuses write-capable spawns from the protected primary
    checkout, and any in-tree path classifies against it. Out-of-tree cwds
    are isolated by definition and skip the git classify entirely.

    #7164: routed to disk-backed fleet scratch root so asks do not exhaust
    tmpfs /tmp quotas, and scanned by tmp leak sweep.
    """
    scratch = ensure_scratch_root() / "learn-ukrainian-bridge-asks" / "agy"
    scratch.mkdir(parents=True, exist_ok=True)
    return scratch


def _resolve_agy_bridge_timeout(no_timeout: bool = False) -> int:
    """Resolve Agy hard timeout from CLI flag/env with a safe fallback.

    ``agent_runtime.runner.invoke()`` requires an integer hard timeout, so
    "no timeout" mode maps to a 24h ceiling rather than ``None``.
    """
    if no_timeout:
        return _NO_TIMEOUT_AGY_BRIDGE_TIMEOUT_SECONDS

    raw = os.environ.get("AGY_BRIDGE_TIMEOUT")
    if raw is None:
        return _DEFAULT_AGY_BRIDGE_TIMEOUT_SECONDS

    value = raw.strip().lower()
    if value in {"0", "none", "off", "false", "no"}:
        return _NO_TIMEOUT_AGY_BRIDGE_TIMEOUT_SECONDS

    try:
        timeout = int(value)
    except ValueError:
        print(f"⚠️  Invalid AGY_BRIDGE_TIMEOUT={raw!r} — falling back to {_DEFAULT_AGY_BRIDGE_TIMEOUT_SECONDS}s")
        return _DEFAULT_AGY_BRIDGE_TIMEOUT_SECONDS

    if timeout <= 0:
        return _NO_TIMEOUT_AGY_BRIDGE_TIMEOUT_SECONDS
    return timeout


# Sealed formal CF isolation is not proven for AGY (project instructions, MCP,
# hooks, nested reviewers cannot yet be suppressed), and the sealed review-pr
# path itself is retired (operator 2026-08-07). Fail closed *before* any send
# on this legacy entrypoint so operators get the working path immediately.
AGY_SEALED_REVIEW_UNSUPPORTED = (
    "agy_isolated_review_unsupported: AGY cannot yet prove native "
    "project-instruction, MCP, hook, and nested-reviewer suppression for "
    "sealed formal CF review, and sealed review-pr is retired. "
    "Use the lightweight direct review on an eligible lane: "
    "`ask-claude|ask-codex|ask-kimi - --task-id review-<N> --type review` "
    "(or `--pr <N>`, which routes to the same direct path). "
    "AGY remains fine for advisory ask-agy *without* --review."
)

# Operator 2026-09-25: Gemini reviews Ukrainian only, never code.
GEMINI_REVIEW_PROFILE_CHOICES = ("code", "ukrainian")
GEMINI_REVIEW_AGENTS = frozenset({"agy", "gemini"})
GEMINI_CODE_REVIEW_FORBIDDEN = (
    "gemini_code_review_forbidden: operator 2026-09-25 — "
    "Gemini reviews Ukrainian only, never code (model-assignment.md)"
)
AGY_REVIEW_PROFILE_REQUIRED = (
    "agy_review_profile_required: a review request to agy/gemini requires "
    "--review-profile {code,ukrainian}. "
    "code is refused (Gemini reviews Ukrainian only, never code — "
    "operator 2026-09-25, model-assignment.md). "
    "Ukrainian content review must pass --review-profile ukrainian."
)


def gemini_review_profile_error(profile: str | None) -> str | None:
    """Refuse a Gemini review unless the profile is explicitly Ukrainian.

    ``None`` means the review may proceed. A missing profile names the flag.
    ``code`` cites the operator rule. Any other value is treated as missing.
    """
    normalized = (profile or "").strip().lower()
    if normalized == "ukrainian":
        return None
    if normalized == "code":
        return GEMINI_CODE_REVIEW_FORBIDDEN
    return AGY_REVIEW_PROFILE_REQUIRED


class GeminiChangedPathListError(RuntimeError):
    """The changed-file list for a Gemini PR or branch review could not be read."""


def gemini_content_paths_error(paths: list[str]) -> str | None:
    """Allow a Gemini PR/branch review only when every path is Ukrainian content.

    The classifier is ``scripts.ci.classify_changes.is_content_class_path``.
    An empty list is a listing failure: there is nothing to prove the diff
    is content. The first non-content path is named in listed order.
    """
    from scripts.ci.classify_changes import is_content_class_path

    if not paths:
        raise GeminiChangedPathListError("changed-file list was empty")
    for path in paths:
        normalized = str(path).strip().replace("\\", "/")
        if not normalized or not is_content_class_path(normalized):
            shown = normalized or "<empty>"
            return f"{GEMINI_CODE_REVIEW_FORBIDDEN}; first non-content path: {shown}"
    return None


def _run_changed_path_command(
    command: list[str],
    *,
    cwd: str,
    env: dict[str, str] | None = None,
) -> str:
    import subprocess

    try:
        proc = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GeminiChangedPathListError(str(exc)) from exc
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip().replace("\n", " ")
        raise GeminiChangedPathListError(detail or f"exit {proc.returncode}")
    return proc.stdout or ""


def resolve_same_repo_pr_head(pr_number: int, *, repo_root: str) -> tuple[str, str]:
    """Return ``(head branch, full head SHA)`` from one ``gh pr view``.

    The SHA is the only commit the path gate and the later dispatch may use.
    A second lookup is a different moment: callers keep this pair and pass the
    SHA through instead of asking GitHub again.
    """
    number = int(pr_number)
    if number < 1:
        raise GeminiChangedPathListError(f"refusing to list files for PR {pr_number!r}")
    raw = _run_changed_path_command(
        [
            "gh",
            "pr",
            "view",
            str(number),
            "--json",
            "headRefName,headRefOid,isCrossRepository",
        ],
        cwd=repo_root,
    )
    import json

    try:
        payload = json.loads(raw or "")
    except json.JSONDecodeError as exc:
        raise GeminiChangedPathListError("gh pr view returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise GeminiChangedPathListError("gh pr view returned a non-object payload")
    if payload.get("isCrossRepository") is not False:
        raise GeminiChangedPathListError("cross-repository PR")
    branch = payload.get("headRefName")
    sha = _full_git_sha(str(payload.get("headRefOid") or ""))
    if not isinstance(branch, str) or not branch.strip() or sha is None:
        raise GeminiChangedPathListError("PR payload has no head branch and full head SHA")
    from scripts.common.git_context import UnsafeBranchNameError, validate_plain_branch_name

    try:
        branch = validate_plain_branch_name(branch, repo_root=repo_root)
    except UnsafeBranchNameError as exc:
        raise GeminiChangedPathListError(f"PR head branch {branch!r} is not a local branch name: {exc}") from exc
    return branch, sha


def list_commit_changed_paths(sha: str, *, repo_root: str) -> list[str]:
    """Changed paths of one fetched commit against ``origin/main``.

    ``git fetch origin <sha>`` downloads that commit and does not move a branch
    ref. ``--no-renames`` keeps the pre-rename path, so a rename of
    ``scripts/x.py`` onto a content path still reports the old name.
    """
    pinned = _full_git_sha(sha)
    if pinned is None:
        raise GeminiChangedPathListError(f"refusing to diff non-SHA {sha!r}")
    from scripts.common.git_context import sanitized_git_env

    git_env = sanitized_git_env()
    _run_changed_path_command(
        ["git", "fetch", "origin", pinned],
        cwd=repo_root,
        env=git_env,
    )
    raw = _run_changed_path_command(
        ["git", "diff", "--name-only", "--no-renames", f"origin/main...{pinned}"],
        cwd=repo_root,
        env=git_env,
    )
    return [line.strip() for line in raw.splitlines() if line.strip()]


def _full_git_sha(value: str) -> str | None:
    sha = value.strip().lower()
    if len(sha) == 40 and all(char in "0123456789abcdef" for char in sha):
        return sha
    return None


def list_branch_changed_paths(
    branch: str,
    *,
    repo_root: str,
    head_out: list[str] | None = None,
) -> list[str]:
    """Changed paths on the remote branch Gemini actually reads.

    ``ask-agy --branch`` and ``delegate --branch`` mean the remote head.
    Fetch with an explicit refspec so a narrow clone updates
    ``refs/remotes/origin/<name>`` instead of only FETCH_HEAD, then diff the
    SHA that fetch resolved. A stale tracking ref is never the diff base.
    """
    from scripts.common.git_context import (
        UnsafeBranchNameError,
        origin_tracking_refspec,
        sanitized_git_env,
        validate_plain_branch_name,
    )

    try:
        name = validate_plain_branch_name(branch, repo_root=repo_root)
    except UnsafeBranchNameError as exc:
        raise GeminiChangedPathListError(f"refusing to diff branch {branch!r}: {exc}") from exc
    git_env = sanitized_git_env()
    _run_changed_path_command(
        ["git", "fetch", "origin", origin_tracking_refspec(name)],
        cwd=repo_root,
        env=git_env,
    )
    sha = _full_git_sha(
        _run_changed_path_command(
            ["git", "rev-parse", "--verify", f"refs/remotes/origin/{name}"],
            cwd=repo_root,
            env=git_env,
        )
    )
    if sha is None:
        raise GeminiChangedPathListError(f"fetch of {name!r} did not resolve an exact SHA")
    if head_out is not None:
        head_out.append(sha)
    # ``--no-renames`` keeps the pre-rename path. Without it, a rename of
    # ``scripts/x.py`` onto a content path reports only the new name.
    raw = _run_changed_path_command(
        ["git", "diff", "--name-only", "--no-renames", f"origin/main...{sha}"],
        cwd=repo_root,
        env=git_env,
    )
    return [line.strip() for line in raw.splitlines() if line.strip()]


def gemini_pr_or_branch_content_error(
    *,
    pr_number: int | None,
    branch: str | None,
    repo_root: str,
    head_out: list[str] | None = None,
    head_sha: str | None = None,
) -> str | None:
    """Refuse a Gemini PR/branch target unless every changed path is content.

    A PR head is resolved once. The changed paths are ``git diff`` of that
    exact SHA (``origin/main...<sha>``), never a file list that can move
    between the request and the checkout. ``head_sha`` is that already
    resolved commit; when it is omitted and a PR number is set, this resolves
    it once. A branch with no PR fetches that remote head by explicit refspec
    and diffs the SHA the fetch resolved. ``head_out`` receives the SHA the
    diff used. Any failure to list files refuses. ``None`` means the target
    may proceed.
    """
    if head_sha is None and pr_number is None and not (branch and str(branch).strip()):
        return None
    try:
        if pr_number is not None and int(pr_number) < 1:
            raise GeminiChangedPathListError(f"refusing to list files for PR {pr_number!r}")
        if head_sha is not None or pr_number is not None:
            pinned = _full_git_sha(head_sha or "")
            if pinned is None:
                if pr_number is None:
                    raise GeminiChangedPathListError(f"refusing to diff non-SHA {head_sha!r}")
                _branch, pinned = resolve_same_repo_pr_head(int(pr_number), repo_root=repo_root)
            if head_out is not None:
                head_out.append(pinned)
            paths = list_commit_changed_paths(pinned, repo_root=repo_root)
        else:
            paths = list_branch_changed_paths(str(branch), repo_root=repo_root, head_out=head_out)
        return gemini_content_paths_error(paths)
    except GeminiChangedPathListError as exc:
        return f"{GEMINI_CODE_REVIEW_FORBIDDEN}; could not list changed files: {exc}"


def gemini_review_targets_model(
    *,
    agent: str,
    model: str | None = None,
    resolved_model: str | None = None,
) -> bool:
    """True when this review would run a Gemini-family model on any harness."""
    from ._review_pr import is_gemini_family_model

    if (agent or "").strip().lower() in GEMINI_REVIEW_AGENTS:
        return True
    return is_gemini_family_model(model) or is_gemini_family_model(resolved_model)


def gemini_review_verdict_dispatch_error(
    *,
    agent: str,
    require_review_verdict: bool,
    profile: str | None,
    pr_number: int | None,
    branch: str | None,
    repo_root: str,
    model: str | None = None,
    resolved_model: str | None = None,
    review: bool = False,
    head_out: list[str] | None = None,
    head_sha: str | None = None,
) -> str | None:
    """Gate a review-typed dispatch whose agent or model is Gemini-family.

    Review-typed means ``--require-review-verdict``, ``--review`` / ``--type review``,
    or ``--pr``. The requested model and the model after fallback substitution
    are both checked, on every agent. A matching dispatch needs
    ``--review-profile ukrainian``. When it also names a PR or branch, every
    changed path must be Ukrainian content. ``head_sha``, when set, is the
    commit that diff covers; otherwise a PR number is resolved once.
    ``head_out`` receives that SHA. Implementation dispatches pass.
    """
    review_typed = require_review_verdict or review or pr_number is not None
    if not review_typed:
        return None
    if not gemini_review_targets_model(agent=agent, model=model, resolved_model=resolved_model):
        return None
    profile_error = gemini_review_profile_error(profile)
    if profile_error is not None:
        return profile_error
    return gemini_pr_or_branch_content_error(
        pr_number=pr_number,
        branch=branch,
        repo_root=repo_root,
        head_out=head_out,
        head_sha=head_sha,
    )


def ask_agy(
    content: str,
    task_id: str | None = None,
    msg_type: str = "query",
    data: str | None = None,
    new_session: bool = False,
    from_llm: str = "claude",
    from_model: str | None = None,
    to_model: str | None = None,
    no_timeout: bool = False,
    effort: str | None = None,
    review: bool = False,
    stdout_only: bool = False,
    output_path: str | None = None,
    background: bool = False,
    review_branch: str | None = None,
    review_pr_number: int | None = None,
):
    """Send message to Agy AND invoke Agy to process it (one-shot)."""
    if background and (stdout_only or output_path):
        raise ValueError("ask-agy --background cannot be combined with --stdout-only or --output-path")
    if review or review_branch is not None or review_pr_number is not None:
        # Refuse formal/exact-target review on AGY before any worktree or send.
        raise ValueError(AGY_SEALED_REVIEW_UNSUPPORTED)
    effective_model = resolve_model_selection(
        lane="ask-agy", to_model=to_model, model=None, default=_default_agy_model()
    )
    msg_id = send_message(
        content,
        task_id,
        msg_type,
        data,
        from_llm=from_llm,
        to_llm="agy",
        from_model=from_model,
        to_model=effective_model,
        effort=effort,
        review_target=review_target_payload(review_branch, review_pr_number),
    )
    register_ask(msg_id)
    if background:
        launch_background_ask(
            msg_id,
            "agy",
            {
                "new_session": new_session,
                "no_timeout": no_timeout,
                "review": review,
                "timeout_seconds": 1800,
            },
        )
        return msg_id
    if not stdout_only:
        print(f"\n🚀 Invoking Agy to process message #{msg_id}...")
    response = process_for_agy(
        msg_id,
        new_session,
        no_timeout,
        review=review,
        stdout_only=stdout_only,
        output_path=output_path,
    )
    if stdout_only and response:
        print(response)
    return msg_id


def process_for_agy(
    message_id: int,
    new_session: bool = False,
    no_timeout: bool = False,
    review: bool = False,
    stdout_only: bool = False,
    output_path: str | None = None,
) -> str | None:
    """Read message addressed to Agy, invoke via agent_runtime, send response.

    ``new_session`` is accepted for API parity with the codex bridge but
    is currently a no-op for Agy — the runtime starts a fresh ``agy -p``
    process per invocation. A future revision could pass
    ``--conversation=<session_id>`` to resume a prior turn; today the
    bridge is single-shot.
    """
    msg = _fetch_agy_message(message_id)
    if not msg:
        return

    _ = new_session  # No-op for now; Agy bridge calls are always fresh.
    timeout_val = _resolve_agy_bridge_timeout(no_timeout)
    model = _extract_target_model(msg) or _default_agy_model()
    effort = requested_effort(msg)
    effort_applied, effort_reason = unsupported_effort_note(
        lane="agy",
        effort=effort,
        reason="the Antigravity CLI has no per-invocation effort control",
    )

    review_target = review_target_from_message(msg) if review else None
    if review or review_target is not None:
        # Defense in depth: process-ask may re-enter with review=true.
        raise ValueError(AGY_SEALED_REVIEW_UNSUPPORTED)

    if not stdout_only:
        print(f"📨 Message #{msg['id']}")
        print(f"   From: {msg['from']} → To: {msg['to']}")
        print(f"   Type: {msg['type']}")
        print(f"   Task: {msg['task_id'] or 'N/A'}")
        print(f"   Model: {model}")
        if timeout_val == _NO_TIMEOUT_AGY_BRIDGE_TIMEOUT_SECONDS:
            print("   Hard timeout: no-timeout requested (24h ceiling)")
        else:
            print(f"   Hard timeout: {timeout_val}s")

    try:
        with provision_review_worktree(
            review_target,
            repo_root=REPO_ROOT,
            allow_local_fallback=bool(review),
        ) as checkout:
            prompt = build_agy_prompt(
                msg,
                review,
                review_branch=checkout.branch if checkout else None,
                review_pr_number=checkout.pr_number if checkout else None,
                review_worktree_provisioned=checkout is not None,
            )
            # Reviews grant evidence-only snapshot access via --add-dir and
            # isolation tool_config; never the primary checkout as surface.
            # #5285: never --dangerously-skip-permissions on the review path;
            # runner enforces OS sandbox when review_isolation is set.
            if review:
                if checkout is None:
                    raise ReviewWorktreeError(
                        "exact-target-required: review requires a sealed neutral "
                        "snapshot; refusing primary checkout fallback"
                    )
                tool_config = checkout.isolation_tool_config("agy")
                review_cwd = checkout.path
            else:
                tool_config = {
                    "bridge_repo_read": True,
                    "repo_read_root": str(REPO_ROOT),
                }
                review_cwd = _agy_ask_scratch_cwd()
            prompt = append_review_prompt_evidence(
                prompt,
                review=review,
                checkout=checkout,
                engine="agy",
            )
            result = agent_runner.invoke(
                "agy",
                prompt,
                # Reviews use read-only accounting; non-review keeps danger for
                # headless tool prompts (skip-permissions path).
                mode="read-only" if review else "danger",
                # Reviews run with cwd=sealed snapshot; non-review keeps
                # out-of-tree scratch cwd for write-mode containment.
                cwd=review_cwd,
                model=model,
                effort=effort,
                task_id=msg["task_id"],
                session_id=None,
                tool_config=tool_config,
                entrypoint="bridge",
                hard_timeout=timeout_val,
                stall_timeout=min(600, timeout_val),
            )
            if review and checkout is not None:
                checkout.bind_review_result(result, engine="agy")
    except ReviewWorktreeError as exc:
        _handle_agy_error(msg, message_id, f"Agy review checkout failed: {exc}")
        return None
    except RateLimitedError as exc:
        _handle_agy_error(msg, message_id, f"Agy rate limited: {exc}")
        return None
    except AgentStalledError as exc:
        _handle_agy_error(msg, message_id, f"Agy stalled: {exc}")
        return None
    except AgentTimeoutError as exc:
        _handle_agy_error(msg, message_id, f"Agy hard timeout: {exc}")
        return None
    except AgentUnavailableError as exc:
        _handle_agy_error(msg, message_id, f"Agy unavailable: {exc}")
        return None

    if not result.ok:
        _handle_agy_error(
            msg,
            message_id,
            result.stderr_excerpt or "Agy returned no final message",
        )
        return None

    if result.session_id and msg["task_id"]:
        set_session(msg["task_id"], "agy", result.session_id)

    response = result.response
    if not response:
        _handle_agy_error(msg, message_id, "Agy returned no final message")
        return None

    if output_path:
        from pathlib import Path

        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(response, encoding="utf-8")

    if not stdout_only:
        print(f"\n✅ Agy finished ({len(response)} chars)")
    provenance_data, actual_model = response_provenance(
        msg,
        actual_model=getattr(result, "model", None) or model,
        harness="agy",
        effort_applied=effort_applied,
        effort_reason=effort_reason,
    )
    reply_id = send_message(
        content=response,
        task_id=msg["task_id"],
        msg_type="response",
        from_llm="agy",
        to_llm=msg["from"],
        data=provenance_data,
        from_model=actual_model,
    )
    acknowledge(message_id)
    record_ask_reply(message_id, reply_id)
    return response


def _fetch_agy_message(message_id: int) -> dict | None:
    """Fetch a message addressed to Agy from the database."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, task_id, from_llm, to_llm, message_type, content, data, timestamp
        FROM messages
        WHERE id = ? AND to_llm = 'agy'
        """,
        (message_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        print(f"❌ Message {message_id} not found or not addressed to Agy")
        return None

    return {
        "id": row[0],
        "task_id": row[1],
        "from": row[2],
        "to": row[3],
        "type": row[4],
        "content": row[5],
        "data": row[6],
        "timestamp": row[7],
    }


def _extract_target_model(msg: dict) -> str | None:
    """Read optional ``to_model`` from the message's ``data`` JSON blob.

    ``send_message`` serializes ``--to-model`` into the ``data`` JSON column
    (NOT a dedicated ``to_model`` column — that column never existed in the
    ``messages`` schema, which is why the old PRAGMA-based lookup always
    returned None and every invocation silently fell back to flash). The
    adapter's ``_resolve_model_flag`` maps the returned slug
    (e.g. ``gemini-3.1-pro-high``) or display label to agy's ``--model``.
    Ported from kubedojo's fixed bridge. Returns None when absent.
    """
    data = msg.get("data")
    if not data:
        return None
    try:
        payload = json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(payload, dict):
        return None
    model = payload.get("to_model")
    return str(model) if model else None


def _handle_agy_error(msg: dict, message_id: int, reason: str) -> None:
    """Record an Agy failure as a response message; no ack (#6915).

    The inbound message stays unacknowledged so the failure is retryable;
    acknowledgement happens only after a successful routed reply.
    """
    print(f"\n❌ Agy error for message #{message_id}: {reason}")
    from ._ask_contract import failed_response_provenance

    data, from_model = failed_response_provenance(msg, bridge_model="agy-bridge-error", harness="agy")
    send_message(
        content=f"[Agy error] {reason}",
        task_id=msg["task_id"],
        msg_type="error",
        from_llm="agy",
        to_llm=msg["from"],
        data=data,
        from_model=from_model,
    )
    record_ask_failure(
        message_id,
        reason,
        timed_out="timeout" in reason.lower() or "stalled" in reason.lower(),
    )
