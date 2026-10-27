"""Dispatch evaluation prompts verbatim through ``scripts/dispatch.py``.

V2 records attest submitted bytes, not legacy prompt wrappers. Acceptance checks
those stored bytes, task identity and result digest against the frozen paired
frame. Caller arguments remain frozen in the existing evaluation manifest;
v2 records do not attest them. Legacy records retain their wrapper and
argument-attestation checks.
"""

from __future__ import annotations

import json
import subprocess
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from scripts.agent_runtime.attribution import resolve_invocation_attribution
from scripts.common.repo_root import main_checkout_root
from scripts.dispatcher.cli import build_parser
from scripts.guardrails import worktree_containment
from scripts.lib.rules_core import RulesCoreError

from . import legacy_codec
from .common import Seat, sha256_bytes, sha256_text

TERMINAL_STATUSES = frozenset(
    {
        "done",
        "failed",
        "timeout",
        "rate_limited",
        "cancelled",
        "crashed",
        "dry_run",
        "needs_finalize",
        "no_deliverable",
        "blocked",
    }
)
CONTROL_TIMEOUT = 120  # seconds for status calls
SPAWN_TIMEOUT = 900  # seconds for dispatch, which may create a read-only worktree
WAIT_MARGIN = 900  # seconds a wait may outlast the worker's hard timeout
RULES_SEAT = "core"
READ_ONLY = "read-only"
# Delegate always exports and names the supported evidence directory (#11342).
# The block is path-free, so this presence marker reproduces delegate's prompt
# exactly while the real per-task lease path stays out of the paired frame.
EVIDENCE_BLOCK = "evidence"
# Classification is a property of the task kind, not the seat. Judge compares Ukrainian writing, so it is review.
TASK_FAMILIES = {
    "review": "ukrainian-review",
    "writing": "ukrainian-authoring",
    "judge": "ukrainian-review",
}
# Record evidence and explicitly caller-derived fingerprints, besides the seat and prompt.
CONDITION_FIELDS = (
    "schema_version",
    "prompt_sha256",
    "stored_prompt_sha256",
    "research_task_family",
    "effective_prompt_sha256",
    "prompt_blocks",
    "dispatch_args_sha256",
    "cwd",
    "mode",
    "worktree_path",
    "research",
    "effort",
    "cli_version",
    "harness",
    "resolved_model",
    "output_schema_sha256",
)
# The parts of a composition that do not depend on the prompt: equal across a frozen plan's tasks.
FRAME_FIELDS = ("cwd", "worktree_path", "prompt_blocks", "prefix_sha256", "suffix_sha256")
# Of the condition fields, the ones paired arms must share (the rest are per task by construction).
PAIRED_FIELDS = tuple(
    f
    for f in CONDITION_FIELDS
    if f
    not in {
        "effective_prompt_sha256",
        "dispatch_args_sha256",
        "prompt_sha256",
        "stored_prompt_sha256",
    }
)
# Instruction and tool-configuration files a seat reads from its working directory.
WORKSPACE_FILES = (
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".mcp.json",
    ".claude/settings.json",
    ".claude/settings.local.json",
    ".codex/config.toml",
    ".gemini/settings.json",
    ".cursor/mcp.json",
)


@dataclass(frozen=True)
class TaskOutcome:
    task_id: str
    status: str
    agent: str | None
    model: str | None
    substitution: Any
    response_text: str | None
    result_sha256: str | None
    run_nonce: str | None
    prompt_sha256: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)
    conditions: dict[str, Any] = field(default_factory=dict)

    def identity_problem(self, seat: Seat, prompt_sha256: str) -> str | None:
        """Why the answer cannot be attributed to ``seat`` answering exactly this prompt (None when it can)."""
        if self.prompt_sha256 != prompt_sha256:
            return f"task ran prompt {self.prompt_sha256!r}, not the planned {prompt_sha256!r}"
        if self.agent != seat.agent:
            return f"launched agent {self.agent!r} is not {seat.agent!r}"
        if self.model != seat.model:
            return f"launched model {self.model!r} is not {seat.model!r}"
        if self.conditions.get("schema_version") == 2 and self.conditions.get("effort") != seat.effort:
            return "launched effort differs from the planned effort"
        if self.substitution:
            return f"route was substituted: {self.substitution!r}"
        return None


class DispatchError(Exception):
    """The dispatcher refused or failed to start a task."""


def caller_initiator() -> str:
    """The initiator delegate records when this process dispatches without ``--initiator``.

    ``unknown`` is not a caller: delegate refuses ``--force-new`` for it, and so does preflight.
    """
    return resolve_invocation_attribution().initiator


def task_family(kind: str) -> str:
    """The ``--research-task-family`` for ``kind``. An unknown kind is refused, never dispatched unclassified."""
    try:
        return TASK_FAMILIES[kind]
    except KeyError:
        raise DispatchError(f"task kind {kind!r} has no Ukrainian task family") from None


def frame(composition: dict[str, Any]) -> dict[str, Any]:
    """The prompt-independent part of an expected composition."""
    shared = {key: composition.get(key) for key in FRAME_FIELDS}
    if composition.get("schema_version") == 2:
        shared.update(cwd=None, worktree_path=None)
        shared.update({key: composition[key] for key in ("schema_version", "dispatch_root", "worker_head")})
    return shared


def _same_path(recorded: Any, expected: str | None) -> bool:
    if expected is None or recorded is None:
        return recorded is None and expected is None
    return isinstance(recorded, str) and Path(recorded).resolve() == Path(expected).resolve()


def condition_problems(conditions: dict[str, Any], *, expected: dict[str, Any], args_sha256: str) -> list[str]:
    """Why the recorded conditions are not the expected composition of the rendered prompt (empty when they are)."""
    problems = []
    if conditions.get("schema_version") == 2:
        if expected.get("schema_version") != 2:
            problems.append("v2 task cannot satisfy a legacy composition")
        for key in ("prompt_sha256", "stored_prompt_sha256"):
            if conditions.get(key) != expected["effective_prompt_sha256"]:
                problems.append(f"{key} differs from the exact submitted prompt")
        # V2 has no engine argument attestation. The caller's manifest checks
        # its frozen arguments; the record proves the applied prompt and frame.
        for key in ("cwd", "worktree_path"):
            if not _same_path(conditions.get(key), expected[key]):
                problems.append(f"worker {key} differs from the frozen frame")
        if conditions.get("mode") != READ_ONLY:
            problems.append("mode is not read-only")
        if conditions.get("research") is not None:
            problems.append("research context was injected")
        if conditions.get("prompt_blocks") or conditions.get("effective_prompt_sha256"):
            problems.append("v2 task reports unsupported legacy prompt composition")
        return problems
    if conditions.get("effective_prompt_sha256") != expected["effective_prompt_sha256"]:
        problems.append(
            f"worker received effective prompt {conditions.get('effective_prompt_sha256')!r}, "
            "not delegate's composition of the rendered prompt"
        )
    if conditions.get("prompt_blocks") != list(expected["prompt_blocks"]):
        problems.append(
            f"delegate appended prompt blocks {conditions.get('prompt_blocks')!r}, "
            f"not the expected {list(expected['prompt_blocks'])!r}"
        )
    if conditions.get("research") is not None:
        problems.append("research context was injected")
    if conditions.get("mode") != READ_ONLY:
        problems.append(f"mode {conditions.get('mode')!r} is not {READ_ONLY!r}")
    if not _same_path(conditions.get("worktree_path"), expected["worktree_path"]):
        problems.append(
            f"worker worktree {conditions.get('worktree_path')!r} is not the expected {expected['worktree_path']!r}"
        )
    if not _same_path(conditions.get("cwd"), expected["cwd"]):
        problems.append(f"worker cwd {conditions.get('cwd')!r} is not the expected {expected['cwd']!r}")
    if conditions.get("dispatch_args_sha256") != args_sha256:
        problems.append("dispatch arguments differ from the ones the harness built")
    return problems


def composition_of(
    composed: str, prompt: str, *, cwd: str | None, worktree_path: str | None, blocks: list[str]
) -> dict:
    """An expected composition: the record fields delegate would write and the frame around ``prompt``."""
    at = composed.find(prompt)
    if at < 0:
        raise DispatchError("delegate's composition does not contain the rendered prompt")
    return {
        "cwd": cwd,
        "worktree_path": worktree_path,
        "prompt_blocks": list(blocks),
        "prefix_sha256": sha256_text(composed[:at]),
        "suffix_sha256": sha256_text(composed[at + len(prompt) :]),
        "effective_prompt_sha256": sha256_text(composed),
    }


class DelegateComposer:
    """Delegate's composition of a read-only ``--cwd`` dispatch, computed in-process without spawning anything.

    Mirrors ``cmd_dispatch`` for this harness's flags: the cwd is validated and
    resolved as delegate does; it must be inside a registered worktree and gets the
    worktree block, with the sparse-checkout exclusions delegate would apply
    there (computed from ``git ls-tree`` without changing the checkout); then
    ``_compose_dispatch_prompt`` builds the final prompt. A record that departs
    from this is refused, so any drift fails closed.
    """

    def __init__(self, delegate: Any, cwd: Path, rules_seat: str = RULES_SEAT) -> None:
        validated = _legacy_cwd(cwd)
        try:
            main = worktree_containment.resolve_main_root(validated if validated.exists() else validated.parent)
        except worktree_containment.NotAGitRepositoryError:
            main = None
        if validated == main:
            raise DispatchError(
                "primary --worker-cwd would redirect each read-only task to a different automatic worktree; "
                "pass an existing isolated Git worktree with --worker-cwd to preserve the paired frame"
            )
        self.delegate = delegate
        self.rules_seat = rules_seat
        self.worktree = (
            next(
                (
                    path
                    for path in worktree_containment.registered_worktrees(main)
                    if path != main and validated.is_relative_to(path)
                ),
                None,
            )
            if main is not None
            else None
        )
        if self.worktree is not None and any(
            self.worktree.parts[i : i + 3] == (".worktrees", "dispatch", "acp")
            for i in range(len(self.worktree.parts) - 2)
        ):
            self.worktree = None
        if self.worktree is None:
            raise DispatchError(
                "--worker-cwd must resolve inside a registered added Git worktree; "
                "pass an existing isolated Git worktree with --worker-cwd"
            )
        self.cwd = str(self.worktree)

    def _sparse(self, prompt: str) -> dict[str, Any]:
        """The sparse-checkout telemetry delegate's worktree block reads (exclusions only; nothing applied)."""
        d, worktree = self.delegate, self.worktree
        includes = d._infer_sparse_include(None, owned_paths=None, prompt_text=prompt)
        _, excluded = d._dispatch_sparse_profile(d._worktree_dir_lister(worktree), includes)
        return {"full_checkout": False, "excluded": excluded}

    def compose(self, prompt: str) -> dict[str, Any]:
        d = self.delegate
        blocks: list[str] = []
        try:
            composed = d._compose_dispatch_prompt(
                prompt,
                worktree_path=self.worktree,
                mode=READ_ONLY,
                sparse_telemetry=self._sparse(prompt) if self.worktree is not None else None,
                delegate_commits=False,  # only read by write modes
                research_block="",
                advisory_block="",
                advisory_block_kind=None,
                rules_seat=self.rules_seat,
                blocks=blocks,
                evidence_dir=EVIDENCE_BLOCK,
            )
        except (OSError, RuntimeError, ValueError, RulesCoreError) as exc:
            raise DispatchError(f"cannot compute delegate's composition: {exc}") from exc
        worktree = str(self.worktree) if self.worktree is not None else None
        return composition_of(composed, prompt, cwd=self.cwd, worktree_path=worktree, blocks=blocks)


def _legacy_cwd(cwd: Path) -> Path:
    """Preserve legacy raw/resolved path validation without loading the CLI runtime."""

    def check(value: str) -> None:
        if any(unicodedata.category(char) in {"Cc", "Cf", "Cs", "Zl", "Zp"} for char in value):
            raise DispatchError("--cwd refused: path contains control or format characters")

    check(str(cwd))
    try:
        resolved = cwd.expanduser().resolve()
    except (OSError, RuntimeError) as exc:
        raise DispatchError("--cwd refused: path cannot be resolved") from exc
    check(str(resolved))
    return resolved


def _git(cwd: Path, *args: str) -> str | None:
    try:
        proc = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=False, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return proc.stdout if proc.returncode == 0 else None


def workspace_fingerprint(cwd: Path) -> dict[str, Any]:
    """The worker checkout's commit, tracked changes and instruction/tool-configuration files."""
    head = _git(cwd, "rev-parse", "HEAD")
    status = _git(cwd, "status", "--porcelain=v1", "--untracked-files=no")
    files = {}
    for rel in WORKSPACE_FILES:
        path = cwd / rel
        files[rel] = sha256_bytes(path.read_bytes()) if path.is_file() else None
    return {
        "head": head.strip() if head is not None else None,
        "tracked_changes_sha256": sha256_text(status) if status is not None else None,
        "files": files,
    }


def workspace_probe(cwd: Path) -> Callable[[], dict[str, Any]]:
    return lambda: workspace_fingerprint(cwd)


class Dispatcher(Protocol):
    def known(self, task_id: str) -> bool:
        """True when a task record with this id already exists."""

    def dispatch(self, task_id: str, seat: Seat, kind: str, prompt_path: Path, *, force_new: bool) -> str | None:
        """Start the task; returns the run nonce."""

    def expected_args_sha256(self, task_id: str, seat: Seat, kind: str, prompt_path: Path) -> str:
        """Fingerprint of the caller invocation frozen by the evaluation manifest."""

    def compose(self, prompt: str) -> dict[str, Any]:
        """The expected composition of ``prompt`` (see ``composition_of``); raises ``DispatchError``."""

    def preflight(self, task_id: str, seat: Seat, kind: str, prompt_path: Path) -> None:
        """Validate a dispatch without spawning a worker."""

    def wait(self, task_id: str, run_nonce: str | None) -> TaskOutcome:
        """Block until the task is terminal and return its attributed outcome."""


class DelegateDispatcher:
    """Evaluation dispatcher used by the CLI and injected fakes."""

    def __init__(
        self,
        *,
        python: str,
        dispatch_script: Path,
        cwd: Path,
        hard_timeout: int = 3600,
        review_profile: str | None = None,
    ) -> None:
        self.python = python
        self.dispatch_script = dispatch_script
        self.cwd = cwd
        self.hard_timeout = hard_timeout
        self.review_profile = review_profile
        self.wait_timeout = hard_timeout + WAIT_MARGIN
        self.legacy_resume = False

    def _run(self, *args: str, timeout: int = CONTROL_TIMEOUT) -> subprocess.CompletedProcess[str]:
        """Run one dispatch subcommand; a timeout preserves pending markers for resume."""
        try:
            return subprocess.run(
                [self.python, str(self.dispatch_script), *args],
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise DispatchError(
                f"dispatch {args[0]} {args[1] if len(args) > 1 else ''} timed out after {timeout}s"
            ) from exc

    def _dispatch_args(
        self, task_id: str, seat: Seat, kind: str, prompt_path: Path, *, legacy: bool = False
    ) -> list[str]:
        args = ["dispatch", "--agent", seat.agent, "--model", seat.model, "--task-id", task_id]
        args += ["--prompt-file", str(prompt_path), "--mode", READ_ONLY, "--language-lane"]
        if legacy:
            args += ["--cwd", str(self.cwd), "--rules-seat", RULES_SEAT]
        else:
            head = _git(self.cwd, "rev-parse", "HEAD")
            if not head:
                raise DispatchError("cannot pin the worker commit")
            args += ["ukrainian", "--pinned-head", head.strip()]
        args += ["--hard-timeout", str(self.hard_timeout)]
        args += ["--research-task-family", task_family(kind)]
        if seat.effort:
            args += ["--effort", seat.effort]
        if self.review_profile and kind == "review":
            args += ["--review-profile", self.review_profile]
            if legacy:
                args += ["--require-review-verdict"]
        return args

    def expected_args_sha256(
        self, task_id: str, seat: Seat, kind: str, prompt_path: Path, *, legacy: bool = False
    ) -> str:
        """Schema-specific argument fingerprint for the frozen evaluation."""
        if legacy or self.legacy_resume:
            args = legacy_codec.build_parser().parse_args(
                self._dispatch_args(task_id, seat, kind, prompt_path, legacy=True)
            )
            return legacy_codec.dispatch_args_sha256(args)
        argv = self._dispatch_args(task_id, seat, kind, prompt_path)
        # Keep the caller fingerprint byte-for-byte: manifests persist the argv JSON,
        # not the parser Namespace. Parsing only verifies the replacement CLI contract.
        try:
            build_parser().parse_args(argv)
        except SystemExit as exc:
            raise DispatchError("evaluation arguments are not supported by scripts/dispatch.py") from exc
        return sha256_text(json.dumps(argv, ensure_ascii=False))

    def legacy_inputs(self, task_id: str, seat: Seat, kind: str, path: Path, prompt: str) -> tuple[dict, str]:
        return (
            DelegateComposer(legacy_codec, self.cwd).compose(prompt),
            self.expected_args_sha256(task_id, seat, kind, path, legacy=True),
        )

    def compose(self, prompt: str) -> dict[str, Any]:
        if self.legacy_resume:
            return DelegateComposer(legacy_codec, self.cwd).compose(prompt)
        cwd = self.cwd.resolve()
        if not (cwd / ".git").is_file() or _git(cwd, "rev-parse", "--show-toplevel") != f"{cwd}\n":
            raise DispatchError("pass an existing isolated Git worktree root with --worker-cwd")
        return {
            "schema_version": 2,
            "dispatch_root": str(main_checkout_root(cwd) / ".worktrees" / "dispatch"),
            "worker_head": (_git(cwd, "rev-parse", "HEAD") or "").strip(),
            **composition_of(prompt, prompt, cwd=None, worktree_path=None, blocks=[]),
        }

    def known(self, task_id: str) -> bool:
        return self._run("status", task_id).returncode == 0

    def dispatch(self, task_id: str, seat: Seat, kind: str, prompt_path: Path, *, force_new: bool) -> str | None:
        if self.legacy_resume:
            raise DispatchError("legacy evaluations support resume only; use a new run tag for new tasks")
        args = self._dispatch_args(task_id, seat, kind, prompt_path)
        if force_new:
            raise DispatchError("v2 refuses task-id replacement; start a new evaluation run tag")
        proc = self._run(*args, timeout=SPAWN_TIMEOUT)
        if proc.returncode != 0:
            raise DispatchError(f"dispatch {task_id} exited {proc.returncode}: {proc.stderr.strip()[-800:]}")
        lines = proc.stdout.splitlines()
        if len(lines) != 2 or lines[0] != task_id or not lines[1].strip():
            raise DispatchError("dispatch did not return the task id and run nonce")
        nonce = lines[1].strip()
        return nonce

    def _existing_record(self, task_id: str) -> dict[str, Any] | None:
        """The task record, or None when dispatch reports that none exists.

        Unreadable status output refuses the caller. A missing record is not an error.
        """
        try:
            proc = self._run("status", task_id)
        except DispatchError as exc:
            raise DispatchError(f"preflight {task_id} refused: {exc} Nothing was archived.") from exc
        if proc.returncode != 0 and proc.stderr.strip() == "dispatcher: task not found":
            return None
        try:
            state = json.loads(proc.stdout)
        except ValueError as exc:
            raise DispatchError("preflight refused: status output is unreadable. Nothing was archived.") from exc
        if not isinstance(state, dict) or proc.returncode != 0:
            raise DispatchError("preflight refused: status output is unreadable. Nothing was archived.")
        return state

    def preflight(self, task_id: str, seat: Seat, kind: str, prompt_path: Path) -> None:
        """V2 dry-run creates nothing and never archives an existing record."""
        record = self._existing_record(task_id)
        if record is not None:
            raise DispatchError(
                f"preflight {task_id} refused: record status {record.get('status')!r} "
                f"initiator {record.get('initiator')!r} already exists. Nothing was archived."
            )
        proc = self._run(*self._dispatch_args(task_id, seat, kind, prompt_path), "--dry-run", timeout=SPAWN_TIMEOUT)
        if proc.returncode != 0:
            raise DispatchError(f"dispatcher dry-run {task_id} exited {proc.returncode}: {proc.stderr.strip()[-800:]}")

    def _status(self, task_id: str, run_nonce: str | None = None) -> dict[str, Any]:
        args = ["status", task_id]
        if run_nonce:
            args += ["--run-nonce", run_nonce]
        proc = self._run(*args)
        try:
            state = json.loads(proc.stdout)
        except ValueError as exc:
            raise DispatchError(f"dispatch status {task_id}: unreadable output ({exc})") from exc
        failed_v2 = (
            isinstance(state, dict)
            and state.get("schema_version") == 2
            and state.get("status") in {"failed", "timeout", "crashed", "cancelled"}
        )
        if proc.returncode != 0 or not isinstance(state, dict) or (state.get("error") and not failed_v2):
            raise DispatchError(f"dispatch status {task_id}: {proc.stdout.strip()[-400:]}")
        return state

    def wait(self, task_id: str, run_nonce: str | None) -> TaskOutcome:
        args = ["wait", task_id, "--timeout", str(self.wait_timeout)]
        if run_nonce:
            args += ["--run-nonce", run_nonce]
        # The exit code reflects the task status; the record read below is authoritative.
        self._run(*args, timeout=self.wait_timeout + CONTROL_TIMEOUT)
        state = self._status(task_id, run_nonce)
        if run_nonce and state.get("run_nonce") != run_nonce:
            raise DispatchError("task returned a stale run nonce")
        if state.get("schema_version") == 2 and (not run_nonce or state.get("task_id") != task_id):
            raise DispatchError("v2 task is missing expected task identity or nonce")
        status = str(state.get("status") or "unknown")
        if status not in TERMINAL_STATUSES:
            raise DispatchError(f"task {task_id} is still {status!r} after wait")
        response, digest = None, state.get("result_sha256")
        result_file = state.get("result_file")
        if result_file and Path(result_file).is_file():
            result_bytes = Path(result_file).read_bytes()
            response = result_bytes.decode("utf-8")
            if digest and sha256_bytes(result_bytes) != digest:
                raise DispatchError(f"task {task_id}: result file does not match its recorded digest")
        conditions = {key: state.get(key) for key in CONDITION_FIELDS}
        if status == "done" and (not response or not response.strip()):
            raise DispatchError("task has no nonempty result")
        if state.get("schema_version") == 2:
            if status == "done" and not digest:
                raise DispatchError("v2 task has no digest-bound result")
            if state.get("prompt_file"):
                try:
                    conditions["stored_prompt_sha256"] = sha256_bytes(Path(state["prompt_file"]).read_bytes())
                except OSError as exc:
                    raise DispatchError("cannot read stored v2 prompt bytes") from exc
        detail = {key: state.get(key) for key in ("duration_s", "returncode", "last_error")}
        if state.get("schema_version") == 2:
            detail["error"] = state.get("error")
        return TaskOutcome(
            task_id=task_id,
            status=status,
            agent=state.get("agent"),
            model=state.get("model"),
            substitution=state.get("substitution"),
            response_text=response,
            result_sha256=digest,
            run_nonce=state.get("run_nonce"),
            prompt_sha256=state.get("prompt_sha256"),
            detail=detail,
            conditions=conditions,
        )
