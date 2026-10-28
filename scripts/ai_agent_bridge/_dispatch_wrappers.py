"""Bridge wrapper commands for recurring agent dispatches."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Bootstrap import path for scripts.* from any cwd
_local_repo_root = Path(__file__).resolve().parents[2]
if str(_local_repo_root) not in sys.path:
    sys.path.insert(0, str(_local_repo_root))

from scripts.common import github_client
from scripts.common.repo_root import resolve_repo_root
from scripts.review.verdict_parser import ACCEPTED_VERDICT_TOKENS, recognized_verdicts, unsupported_verdict_tokens
from scripts.secret_redactor import redact_text

if TYPE_CHECKING:
    from agent_runtime.target_admission import AdmittedTarget

REPO_ROOT = resolve_repo_root(Path(__file__), 2)
PYTHON = ".venv/bin/python"

REVIEW_DEEP_INSTRUCTIONS = (
    "Adversarial review. Find logical bugs, security issues, contradictions, "
    "missing tests, dead code, performance footguns. Cite file:line. Be terse "
    "but complete. Do NOT propose stylistic preferences. Output: structured "
    "`## Findings` markdown. Report one finding per input class with a "
    "reproducer, not one spelling at a time. Give each finding a disposition "
    "from the local-code-review checklist Step 5: in_scope_blocker (violates "
    "the change's stated contract, or an existing invariant on a path it "
    "introduces, modifies or newly exposes, or regresses main), follow_up "
    "(pre-existing off-path defect, wording, P2/P3, unless material) or "
    "stop_and_escalate (material contract ambiguity). Each blocker states the "
    "reproducible failure, its impact and the required corrected behaviour. "
    "APPROVED may carry tracked follow-ups; a missing required capability is "
    "BLOCKED, naming that capability (#10665)."
)


def _safe_path_component(raw: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", raw).strip(".-")
    return safe or "task"


def _is_pr_number(target: str) -> bool:
    return target.lstrip("#").isdigit()


def _task_state_path(task_id: str) -> Path:
    tasks_dir = REPO_ROOT / "batch_state" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    safe = task_id.replace("/", "_").replace("\\", "_")
    return tasks_dir / f"{safe}.json"


DEFAULT_JSON_COMMAND_TIMEOUT_SECONDS: float = 60.0
DEFAULT_TEXT_COMMAND_TIMEOUT_SECONDS: float = 60.0
DISPATCH_COMMAND_TIMEOUT_SECONDS: float = 180.0
ASK_REVIEW_WAIT_GRACE_SECONDS: float = 60.0


def _run_json_command(
    cmd: list[str],
    *,
    timeout: float = DEFAULT_JSON_COMMAND_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    proc = github_client.run(
        cmd,
        fresh=True,
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return json.loads(proc.stdout or "{}")


def _run_text_command(
    cmd: list[str],
    *,
    timeout: float = DEFAULT_TEXT_COMMAND_TIMEOUT_SECONDS,
) -> str:
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return proc.stdout


@contextmanager
def _prompt_directory() -> Iterator[Path]:
    """Yield a task lease or a self-cleaning directory for prompt files."""
    runtime_tmp_root = os.environ.get("LU_RUNTIME_TMP_ROOT")
    if runtime_tmp_root:
        lease_root = Path(runtime_tmp_root)
        if not lease_root.is_dir():
            raise RuntimeError(f"runtime tmp lease is not a directory: {lease_root}")
        yield lease_root
        return

    from scripts.common.scratch import ensure_scratch_root

    with tempfile.TemporaryDirectory(prefix="learn-ukrainian-bridge-", dir=ensure_scratch_root()) as directory:
        yield Path(directory)


def _serialize_files(files: Any) -> str:
    if not files:
        return "(none)"
    if not isinstance(files, list):
        return json.dumps(files, indent=2, sort_keys=True)
    lines = []
    for item in files:
        if isinstance(item, dict):
            path = item.get("path") or item.get("filename") or item.get("name") or str(item)
            additions = item.get("additions")
            deletions = item.get("deletions")
            if additions is not None and deletions is not None:
                lines.append(f"- {path} (+{additions}/-{deletions})")
            else:
                lines.append(f"- {path}")
        else:
            lines.append(f"- {item}")
    return "\n".join(lines)


def _write_review_deep_pr_prompt(pr_number: str, prompt_directory: Path, *, pr: dict | None = None) -> Path:
    """Pointer-only PR review prompt (Sol fleet-comms Phase 2).

    Never embed full PR body or diff — the reviewer pulls evidence under
    read-only mode. Exact-head cross-family review through ``ask-<lane> --type review``
    (headless dispatch) replaced the removed ``review-pr``.
    """
    from ._review_safety import (
        MAX_REVIEW_REQUEST_BYTES,
        assert_content_size,
        prepend_read_only_contract,
    )

    if pr is None:
        pr = _run_json_command(["gh", "pr", "view", pr_number, "--json", "title,files,url,headRefOid"])
    title = str(pr.get("title") or "").strip()
    url = str(pr.get("url") or f"https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/{pr_number}")
    head = str(pr.get("headRefOid") or "").strip()
    files = _serialize_files(pr.get("files"))
    prompt = prepend_read_only_contract(
        f"{REVIEW_DEEP_INSTRUCTIONS}\n\n"
        f"## PR #{pr_number}: {title}\n\n"
        f"**URL:** {url}\n"
        f"**Expected head SHA:** `{head}`\n\n"
        f"### Changed files (names only — pull the diff yourself)\n\n{files}\n\n"
        "Do **not** ask the operator to paste the diff. Use `gh pr diff` / sealed "
        "snapshot in the read-only dispatch worktree.\n\n"
        "End with exactly one line: `VERDICT: APPROVED` or "
        "`VERDICT: CHANGES_REQUESTED` or `VERDICT: BLOCKED`.\n"
    )
    assert_content_size(prompt, limit=MAX_REVIEW_REQUEST_BYTES, label="review_deep_prompt")
    prompt_path = prompt_directory / f"review-deep-pr-{_safe_path_component(pr_number)}.md"
    prompt_path.write_text(prompt, encoding="utf-8")
    return prompt_path


def _review_task_id(target: str) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    digest = hashlib.sha256(target.encode("utf-8")).hexdigest()[:8]
    return f"review-{_safe_path_component(target)[:80]}-{digest}-{timestamp}"


def build_review_deep_command(target: str, prompt_file: Path, effort: str, *, pr: dict | None = None) -> list[str]:
    if not _is_pr_number(target):
        raise ValueError("review-deep requires a PR number; local-path review is retired")
    from scripts.common.git_context import validate_plain_branch_name

    if pr is None:
        pr = _run_json_command(["gh", "pr", "view", target.lstrip("#"), "--json", "headRefName,headRefOid"])
    if not isinstance(pr, dict):
        raise ValueError("review-deep could not load PR metadata")
    branch, head = pr.get("headRefName"), pr.get("headRefOid")
    if not isinstance(branch, str) or not isinstance(head, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", head):
        raise ValueError("review-deep requires the PR head ref and full head SHA")
    branch = validate_plain_branch_name(branch, repo_root=REPO_ROOT)
    command = [
        PYTHON,
        "scripts/dispatch.py",
        "dispatch",
        "--agent",
        "claude",
        "--mode",
        "read-only",
        "--model",
        "claude-opus-5-5",
        "--effort",
        effort,
        "--task-id",
        _review_task_id(target),
        "--prompt-file",
        str(prompt_file),
    ]
    command.extend(["--full-checkout", "--branch", branch, "--pinned-head", head])
    return command


def _write_dry_run_state(task_id: str, command: list[str], prompt_file: Path) -> None:
    prompt = prompt_file.read_text(encoding="utf-8")
    state = {
        "task_id": task_id,
        "agent": command[command.index("--agent") + 1],
        "model": command[command.index("--model") + 1] if "--model" in command else None,
        "effort": command[command.index("--effort") + 1] if "--effort" in command else None,
        "mode": command[command.index("--mode") + 1],
        "status": "dry-run",
        "prompt_file": str(prompt_file),
        "prompt_chars": len(prompt),
        "command": command,
        "started_at": datetime.now(UTC).isoformat(),
        "finished_at": datetime.now(UTC).isoformat(),
        "returncode": 0,
    }
    _task_state_path(task_id).write_text(json.dumps(state, indent=2), encoding="utf-8")


def _run_dispatch(
    command: list[str],
    dry_run: bool,
    prompt_file: Path,
    *,
    timeout: float = DISPATCH_COMMAND_TIMEOUT_SECONDS,
) -> int:
    task_id = command[command.index("--task-id") + 1]
    if dry_run:
        _write_dry_run_state(task_id, command, prompt_file)
        print("DRY RUN: " + " ".join(command))
        print(f"Prompt file: {prompt_file}")
        print(f"State file: {_task_state_path(task_id)}")
        return 0
    try:
        proc = github_client.run(command, cwd=REPO_ROOT, timeout=timeout)
        return int(proc.returncode)
    except subprocess.TimeoutExpired:
        print(
            f"❌ dispatch command timed out after {timeout}s: {' '.join(command)}",
            file=sys.stderr,
        )
        return 1


def handle_review_deep(args: Any) -> int:
    if not _is_pr_number(args.target):
        print(
            "review-deep local-path review is retired. Use scripts/dispatch.py dispatch "
            "--agent <agent> --model <model> --mode read-only --cwd <dispatch-worktree> "
            "--prompt-file <brief> for a live checkout, then scripts/dispatch.py wait <task-id>. "
            "Publish formal verdicts with scripts.review.record_cf_verdict.",
            file=sys.stderr,
        )
        return 2
    with _prompt_directory() as prompt_directory:
        try:
            pr = _run_json_command([
                "gh", "pr", "view", args.target.lstrip("#"), "--json", "title,files,url,headRefName,headRefOid",
            ])
            if not isinstance(pr, dict):
                raise ValueError("review-deep could not load PR metadata")
            prompt_file = _write_review_deep_pr_prompt(args.target.lstrip("#"), prompt_directory, pr=pr)
            command = build_review_deep_command(args.target, prompt_file, args.effort, pr=pr)
        except (OSError, ValueError, subprocess.SubprocessError):
            print("review-deep: could not load a valid PR head ref and SHA; review not dispatched.", file=sys.stderr)
            return 2
        return _run_dispatch(command, args.dry_run, prompt_file)


# ---------------------------------------------------------------------------
# ask-* review-intent dispatch (#7155) — headless native CLI, never ACP.
#
# A reviewer must be able to use tools (gh, fs, pytest). ACP's
# `--deny-all --no-fs --no-terminal` chat transport cannot do that (Terra
# ABSTAIN on #7155: `gh auth` unavailable in ACP). `ask-<lane> --review` /
# `--type review` / `--pr` / `--branch` route here instead of run_compat_ask.
# ---------------------------------------------------------------------------


def build_ask_review_dispatch_command(
    target: AdmittedTarget,
    task_id: str,
    prompt_file: Path,
    *,
    effort: str | None,
    repo: str | None = None,
    branch: str | None = None,
    review_profile: str | None = None,
    pinned_head: str | None = None,
    subject_seats: list[str] | None = None,
    subject_families: list[str] | None = None,
) -> list[str]:
    """Headless dispatch command for one review-intent ask-*.

    ``--mode read-only`` still grants `gh pr view` / `gh pr diff` / repo read
    inside an isolated `--worktree` — read-only is exactly what `review-deep`
    already uses for the same class of work, it is not a tool restriction.

    ``--branch`` attaches that worktree to the author branch. A read-only
    reviewer cannot ``git checkout``, so a worktree born on ``main`` never
    reaches the SHA under review.

    ``target`` is the ``AdmittedTarget`` ``resolve_and_admit`` produced for
    the review seat; the command carries its seat and model.
    """
    from agent_runtime.target_admission import require_admitted, seat_default_model

    target = require_admitted(target)
    model = target.model or seat_default_model(target.recipient)
    if not model:
        raise ValueError(f"no default dispatch model for {target.recipient!r}")
    cmd = [
        PYTHON,
        "scripts/dispatch.py",
        "dispatch",
        "--agent",
        target.recipient,
    ]
    cmd += [
        "--mode",
        "read-only",
        "--worktree",
        "--task-id",
        task_id,
        "--prompt-file",
        str(prompt_file),
        "--require-review-verdict",
    ]
    if repo is not None:
        cmd.extend(["--repo", repo])
    if branch:
        cmd.extend(["--branch", branch])
    if pinned_head:
        cmd.extend(["--pinned-head", pinned_head])
    if review_profile:
        cmd.extend(["--review-profile", review_profile])
    for seat in subject_seats or ():
        cmd.extend(["--subject-seat", seat])
    for family in subject_families or ():
        cmd.extend(["--subject-family", family])
    if model:
        cmd += ["--model", model]
    if effort:
        cmd += ["--effort", effort]
    return cmd


def build_ask_review_wait_command(task_id: str, *, timeout: int) -> list[str]:
    return [PYTHON, "scripts/dispatch.py", "wait", task_id, "--timeout", str(timeout)]


_ASK_REVIEW_DEFAULT_TIMEOUT_S = 1800

_REVIEW_VERDICT_OUTPUT = (
    "Review completion requires your own plain, unfenced verdict line: "
    "the label VERDICT, a colon, then one accepted token. "
    f"Accepted tokens: {', '.join(ACCEPTED_VERDICT_TOKENS)}. "
    # #10665: proportional verdicts; INCONCLUSIVE maps onto the existing BLOCKED token.
    "An approval may carry tracked non-blocking follow-ups. A review that lacks a capability "
    "its brief requires (shell, diff access, hashing, sources tools) is inconclusive: give the "
    "BLOCKED token and name the missing capability."
)

_NATIVE_CODE_REVIEW_OUTPUT = """## Existing code-review output and exact-target evidence contract

In your first completed reply, include a plain, unfenced verdict line using
the label VERDICT, a colon, then APPROVE, REQUEST_CHANGES, or BLOCKED, as warranted
by your independent judgment. Also include one native JSON object, unfenced, conforming to
schemas/code-review-findings.v1.schema.json (schema_version: code-review-findings.v1).
Read that schema: overall requires correctness, explanation, confidence; each
finding requires id, title, body, priority, confidence, category, location,
verbatim, why_wrong, smallest_fix, sources. Do not add fields or wrap the object
in another object. Retain every material and nonblocking finding, including
nonblocking findings with an approving verdict; choose judgment and confidence
independently.

For each finding, use a repository-relative location.path and complete literal
source lines from the exact reviewed target in verbatim, including all leading
indentation, tabs, trailing spaces and intervening blank lines. Use JSON escapes
for newlines and tabs; do not strip whitespace, quote only a substring, add line
numbers, diff prefixes, backticks or ellipses. Only line endings are normalized.
The 1-based start_line/end_line are inclusive and must exactly cover those lines:
end_line = start_line + number of quoted source lines - 1.

The primary location must be in a changed file. For claim_type "present", the
quoted span must intersect an actual changed new-side line. Put unchanged
consumers and supporting references in body/sources, anchoring the finding to
the relevant changed source. For claim_type "missing", quote real contextual
evidence in a changed file (which may be an unchanged line); explain the absence
in body/why_wrong, never invent a line for absent code.

Before replying, locally reread each quote at the exact target (git show at the
pinned head for committed reviews), compare every character and inclusive span,
and check the target diff for present anchors. Return the findings JSON yourself;
the existing strict verifier remains authoritative.
"""


def run_ask_review_dispatch(
    agent: str,
    content: str,
    *,
    task_id: str,
    data: str | None = None,
    model: str | None = None,
    effort: str | None = None,
    hard_timeout: int | None = None,
    repo: str | None = None,
    branch: str | None = None,
    review_profile: str | None = None,
    pinned_head: str | None = None,
    subject_seats: list[str] | None = None,
    subject_families: list[str] | None = None,
) -> dict[str, Any]:
    """Dispatch one review-intent ask-* to the headless native CLI and block for it.

    Fires `dispatch.py dispatch --agent <agent> --worktree --mode read-only`
    (a real TUI agent with tools in an isolated worktree), then
    `dispatch.py wait` to block for the terminal state. Returns the terminal
    state dict plus the read-back ``response`` text and a normalized ``ok``.
    Raises ``RuntimeError`` if dispatch itself could not be started or the
    wait output could not be parsed — callers turn that into a hard failure,
    never a silent fallback to ACP. Raises ``KimiAdmissionRefused`` for a
    Kimi seat before anything is written.

    ``content`` is caller instruction text; ``data`` stays a separate inert
    attachment and cannot opt into the code-review contract. Compose active
    guidance before the attachment without interpreting or rewriting either.
    """
    # Kimi seats never review: the seat is admitted before the temporary prompt is written.
    from agent_runtime.kimi_admission import REVIEW_MODE
    from agent_runtime.target_admission import resolve_and_admit

    (target,) = resolve_and_admit((agent,), mode=REVIEW_MODE, model=model, review=True)
    timeout = hard_timeout or _ASK_REVIEW_DEFAULT_TIMEOUT_S
    with _prompt_directory() as prompt_directory:
        prompt_path = prompt_directory / f"ask-review-{_safe_path_component(task_id)}.md"
        prompt = _REVIEW_VERDICT_OUTPUT + "\n\n" + content
        if review_profile in {"code", "infra"} or re.search(r"\bcode-review-findings\.v1\b", content):
            prompt += "\n\n" + _NATIVE_CODE_REVIEW_OUTPUT
        if data:
            prompt += "\n\n--- attached inert text ---\n" + data
        prompt_path.write_text(prompt, encoding="utf-8")
        dispatch_command = build_ask_review_dispatch_command(
            target,
            task_id,
            prompt_path,
            effort=effort,
            repo=repo,
            branch=branch,
            review_profile=review_profile,
            pinned_head=pinned_head,
            subject_seats=subject_seats,
            subject_families=subject_families,
        )
        try:
            dispatch_proc = subprocess.run(
                dispatch_command,
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=DISPATCH_COMMAND_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"dispatch.py dispatch timed out after {DISPATCH_COMMAND_TIMEOUT_SECONDS}s: "
                f"Command: {' '.join(dispatch_command)}"
            ) from exc
        if dispatch_proc.returncode != 0:
            raise RuntimeError(
                f"dispatch.py dispatch failed rc={dispatch_proc.returncode}: "
                f"{(dispatch_proc.stderr or dispatch_proc.stdout).strip()}\n"
                f"Command: {' '.join(dispatch_command)}"
            )

        wait_command = build_ask_review_wait_command(task_id, timeout=timeout)
        try:
            wait_proc = subprocess.run(
                wait_command,
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=timeout + ASK_REVIEW_WAIT_GRACE_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"dispatch.py wait timed out at process level after {timeout + ASK_REVIEW_WAIT_GRACE_SECONDS}s: "
                f"Command: {' '.join(wait_command)}"
            ) from exc
        try:
            state = json.loads(wait_proc.stdout or "{}")
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"dispatch.py wait produced non-JSON output (rc={wait_proc.returncode}): "
                f"stdout={wait_proc.stdout!r} stderr={wait_proc.stderr!r}"
            ) from exc

        result_file = state.get("result_file")
        response = ""
        if result_file:
            try:
                response = Path(result_file).read_text(encoding="utf-8")
            except OSError:
                response = ""
        state["response"] = response
        # Only a successful v2 wait can complete the review.
        completed = state.get("status") == "done" and wait_proc.returncode == 0
        verdicts = set(recognized_verdicts(response))
        unsupported = unsupported_verdict_tokens(response) if not verdicts else []
        failure = None
        if not verdicts:
            failure = "review_unsupported_verdict_token" if unsupported else "review_missing_verdict_line"
        elif len(verdicts) > 1:
            failure = "review_ambiguous_verdict"
        state["ok"] = completed and failure is None
        if completed and failure:
            state.update(status="failed", failure_reason=failure)
        if unsupported and (
            completed or state.get("error") == "review_missing_verdict_line" or state.get("failure_reason") == failure
        ):
            detail = (
                f"{failure}: unsupported verdict identifier {unsupported[-1]!r}; "
                f"accepted tokens: {', '.join(ACCEPTED_VERDICT_TOKENS)}"
            )
            state["stderr_excerpt"] = redact_text(detail) or ""
        if not state["ok"] and not state.get("stderr_excerpt"):
            state["stderr_excerpt"] = f"ask-{agent} review dispatch did not complete: status={state.get('status')!r}"
        return state
