#!/usr/bin/env python
"""delegate.py — async task dispatch over agent_runtime.

Layer 3 of the #1184 architecture (see watchdog.py::should_kill for the
incident chain that led here). This module is the "fire and wait later"
execution model: callers dispatch a task, get a task-id back
immediately, and poll/wait at their own pace. No heuristic stall
detection, no speculative kills, no 30-minute caller blocks. The user
controls how long to wait.

CLI:

    # Fire a task. Returns immediately with the task-id.
    # Write-capable modes (workspace-write / danger) require a dispatch worktree.
    delegate.py dispatch --agent codex --task-id my-task \
        --prompt "do the thing" [--mode workspace-write --worktree] [--model gpt-6.1-sol]
        [--allow-merge] [--force-new]

    # Check status without blocking.
    delegate.py status my-task
    → {"status": "running", "pid": 12345, "elapsed_s": 42.1, ...}
    → {"status": "done",    "result_file": ".../my-task.result", ...}
    → {"status": "failed",  "stderr_excerpt": "...", ...}
    → {"status": "crashed", "reason": "pid 12345 is dead but state says running"}

    # Guardrail check for stale async-task claims.
    delegate.py status-or-fail my-task
    → exits 0 only when Monitor API says the task is currently running

    # Wait for completion. Polls at 2s intervals.
    delegate.py wait my-task [--timeout 3600]

State files live at ``batch_state/tasks/<task-id>.json``. Format:

    {
        "task_id": str,
        "run_nonce": str,           # unique run identifier for split-brain detection (#7168)
        "repository": str | null,   # authoritative "owner/repo" of the dispatch target (#7083)
        "agent": str,
        "model": str,
        "resolved_model": str,  # Cursor's concrete model, or "unknown"
        "resolved_model_known": bool,
        "resolved_model_source": str,
        "effort": str,
        "cli_version": str,
        "mode": str,
        "pid": int,
        "status": "running" | "done" | "failed" | "timeout" | "rate_limited" | "crashed"
                  | "needs_finalize" | "no_deliverable",
        "started_at": iso-8601 UTC,
        "finished_at": iso-8601 UTC | null,
        "duration_s": float | null,
        "prompt_chars": int,
        "prompt_sha256": str,        # sha256 of the prompt as given (--prompt/--prompt-file), before appended blocks
        "effective_prompt_sha256": str,  # sha256 of the final prompt handed to the worker, after every appended block
        "prompt_blocks": [str],      # kinds of the blocks delegate added, in prompt order: "rules_core", "worktree", "lifecycle", "research"
        "review_attempt": {review_id, attempt_id, manifest_sha256} | absent,  # --review-attempt dispatches only (#9022)
        "review_contract": {render_checkout, server_checkout, server_interpreter, render_server_digest, server_digest, server_components, render_template_digest, template_digest, templates, prompt_sha256} | absent,  # (#9163)
        "review_input_paths": [str] | absent,  # attempt reads outside input_root; claimed until terminal (#9597)
        "dispatch_args_sha256": str,  # sha256 of every parsed `dispatch` arg except DISPATCH_ARGS_HASH_EXCLUDED_FIELDS
        "response_chars": int | null,
        "result_file": str | null,   # path to the full response text
        "held_work": [str] | absent,  # explicit runtime-root relative files to preserve (#10000)
        "preserved_held_work": object | absent,  # verified runtime-held-work.v1 retrieval manifest
        "stderr_excerpt": str | null,   # the worker's raw stderr: local; never quote it in a PR or issue
        "returncode": int | null,
        "returncode_reason": str | null,
        "require_review_verdict": bool,  # opt-in bridge review completion gate
        "pinned_head": str | null,  # exact --branch/--pr head required before dispatch
        "review_author_model": str | null,  # trusted author identity for code review resolution
        "review_risk": str | null,  # code review resolver risk; budget substitution needs author + risk
        "review_profile": str | null,  # code (default) or ukrainian
        "review_language_lane": bool,  # dispatch's Ukrainian content classification
        "sources_mcp_call_count": int | null,  # runtime evidence; null means unknown
        "failure_reason": str | null,  # named cause on failed verdict-required reviews
        "launch_mode": "scope" | "popen-fallback",  # #8645 part C
        "launch_unit": str | null,                  # scope unit when launch_mode is scope
        "launch_fallback_reason": str | null,
        "launch_user_bus": {source: "caller" | "derived" | "unavailable", variables?, reason?},  # #9534
        "peak_rss_mib": float | null,               # terminal records; largest reaped child
        "owned_paths": [str] | absent,              # the --owned-path values: auto-finalize scope (#8991)
        "authoring_review_admission": {check, reviewer_availability, target, head_sha, author_families,
                                       risk, reviewer, ...} | absent,  # write dispatches: review feasibility (#9739)
        "review_subject_seats": [str] | absent,     # --subject-seat values the verdict recorder re-applies (#9739)
        "review_subject_families": [str] | absent,  # --subject-family values, likewise
        "leftovers_scan": "clear" | "live" | "unknown" | absent,  # exit scan of the worker's scope
        "leftovers_scope": {task_id, launch_mode, unit, cgroup, run_nonce, ...} | absent,
        "leftovers_scan_error": str | absent,       # why the scan was unknown
        "leftovers_terminated": [{pid, cmdline, signals, stopped, left_scope}] | absent,  # Cursor worker-server stopped before the scan (#9534)
        "incomplete_run_reason": "background_jobs_alive_at_exit" | "leftovers_scan_unknown" | absent,
        "background_jobs_alive_at_exit": {reason, count, processes: [{pid, cmdline}], scope} | absent,
        "finalize_skipped_paths": [str] | absent,   # changed files auto-finalize left out of its commit
        "kimi_content_refusal": str | absent,       # a Kimi diff held Cyrillic text or content that is not plain text; nothing was committed
        "failure_code": str | absent,               # runtime's typed failure, e.g. provider_policy_refusal; last_error names the class (#9532)
        "advisory_envelope": {requirement, advisory_args, advisory_args_sha256, prompt_sha256,
                              admitted_execution, research_block, repo_root, advisor_task_id, advisor_model,
                              advisor_run_nonce, result_path, result_sha256, envelope_sha256,
                              dispatch_args_sha256, owned_paths, max_changed_files, max_non_test_loc}
                             | absent,  # bounded-worker admission; the worker re-verifies it (#9275)
        "advisory_prompt_sha256": str | absent,  # the bounded worker's prompt as checked and submitted
        "advisory_exemption": {model_id, task_family, review_profile, mode, classified_paths} | absent,
                              # a Gemini Flash launch classified Ukrainian; the worker re-classifies it
        "advisory_ceiling_check": {measured, changed_files, non_test_loc, max_*, exceeded | error} | absent,
        "advisory_exempt_change_check": {measured, changed_paths, ignored_residue, problems | error} | absent,
        "advisory_role": "bounded_advisory_envelope" | absent,  # the advisor run that issues an envelope (#9275)
        "advisory_route": str | absent,
        "advisory_binding_sha256": str | absent,    # the worker dispatch's advisory binding digest
        "advisory_seal": {result_sha256, envelope_sha256, advisor_model, run_nonce} | absent,
                              # advisor runs: a consistency checksum of the result as its worker wrote it
        "routing_facts": object | absent,  # --force-agent with a budget check: the lane's routing_facts summary
                                           # (quota, health, freshness). Missing telemetry is explicit unknown.
    }

    Reason fields (``PUBLIC_RECORD_REASON_FIELDS`` and ``auto_finalize.error``)
    hold only registered public causes (``public_causes``, #9878): the record
    writer replaces anything else, and the raw text goes to the task's local
    ``<task-id>.diag`` file (0600, bounded, rotated once to ``.diag.prev``).

Design notes:

* Zombie detection. ``os.kill(pid, 0)`` is the POSIX way to ask "is this
  PID alive?" without sending a signal. The ``status`` command does this
  whenever it reads a state file that says ``running``. If the PID is
  dead but the file still says running, we mark the state file
  ``crashed`` — this catches OOM kills, machine reboots, and any other
  abrupt termination of the worker process.

* PID recycling is theoretically possible (the OS reuses PIDs), but in
  practice a PID from minutes ago is extremely unlikely to be recycled
  AND owned by a process matching our command line. For the short-lived
  nature of agent tasks this is acceptable. A fully bulletproof version
  would record the process start_time from ``/proc/<pid>/stat`` (Linux)
  or ``kvm_getprocs`` (BSD/macOS) and re-verify — deferred as over-engineering
  for the current scale.

* Atomic writes. Every state-file update goes via write-rename so a
  concurrent reader never sees a half-written JSON. ``os.replace`` is
  atomic on POSIX.

* No lock contention on the state dir. Each task owns its own file;
  there's no shared index, no global lock.

* Quota safety. The detached worker calls ``agent_runtime.runner.invoke``
  which already consults ``has_headroom`` before spawning the CLI — so
  you can't stampede the provider by firing many delegate tasks in a
  row if the last one got rate-limited.

* Dual-host VPS placement. When healthy VPS occupancy hosts are available
  and the local retired marker exists, ``dispatch`` forwards execution
  over BatchMode SSH to the remote host.
  Host environment contract:
  - ``LU_JOB_DISPATCH_HOST`` (or ``ATLAS_RUNNER_HOST``) and ``LU_JOB_REPO``
  - ``LU_TEACHER_DISPATCH_HOST`` (or ``LU_DISPATCH_SSH``) and ``LU_TEACHER_REPO``
  - ``LU_ALLOW_NOTEBOOK_DISPATCH=1`` bypasses VPS forwarding to force local spawn.
  Configuration errors fail closed without fallback to preserve visibility.

Issue: #1184, #7230.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import dataclasses
import errno
import fcntl
import functools
import hashlib
import json
import logging
import os
import re
import resource
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from agent_runtime.routes import RUNTIME_ROUTE_TOOL_CONFIG_KEY

# Resolve repo root from this file's location so we work from any cwd —
# then hop to the primary checkout so worktree copies behave identically.
_local_repo_root = Path(__file__).resolve().parents[1]
if str(_local_repo_root) not in sys.path:
    sys.path.insert(0, str(_local_repo_root))

from scripts.agent_runtime import bounded_advisory
from scripts.common.jsonl import jsonl_lines
from scripts.common.repo_root import main_checkout_root as _main_checkout_root  # compatibility seam
from scripts.common.repo_root import project_interpreter, resolve_repo_root
from scripts.common.scratch import (
    DEFAULT_SCRATCH_ROOT,
    ScratchScanRootError,
    ensure_scratch_root,
    fallback_scratch_root,
    resolve_scratch_root,
    scratch_scan_roots,
)
from scripts.common.task_store_paths import tasks_dir
from scripts.config import (
    DELEGATE_WORKTREE_ADD_MAX_S,
    DELEGATE_WORKTREE_ADD_STALL_S,
    DELEGATE_WORKTREE_ADD_TIMEOUT_S,
)
from scripts.fleet import credit_lane
from scripts.fleet.regenerable_output import is_disposable_auto_finalize_path as _is_disposable_auto_finalize_path
from scripts.fleet.reset_reserve import codex_is_threatened as _codex_is_threatened
from scripts.fleet.reset_reserve import codex_reset_reserve_eligible as _codex_reset_reserve_eligible
from scripts.fleet.reset_reserve import load_reset_reserve as _load_reset_reserve
from scripts.lib import rules_core
from scripts.opsec.prepublish import PublishBlocked, publication_boundary
from scripts.orchestration import (
    dispatch_admission,
    dispatch_isolation,
    reaper_lifecycle,
    task_record_store,
    worker_leftovers,
    worktree_claims,
    worktree_paths,
    worktree_prep,
)
from scripts.orchestration.dead_worker_state import (
    mark_dead_worker_terminal,
    mark_orphaned_admission_hold_crashed,
    mark_orphaned_worktree_prep_crashed,
    task_state_lock,
    write_state_unlocked,
)
from scripts.orchestration.safe_git_context import CANONICAL_ORIGIN, SafeGitContext, SnapshotRefusal
from scripts.publish.github import Request, request_run
from scripts.review.language_lane import is_ukrainian_review
from scripts.review.verdict_parser import recognized_verdicts
from scripts.secret_redactor import redact_text

if TYPE_CHECKING:
    from scripts.agent_runtime.target_admission import AdmittedTarget, Route, RouteRequest

_REPO_ROOT = resolve_repo_root(Path(__file__), 1)
_BASH_SECRETS_PATH = Path.home() / ".bash_secrets"
# The Gemini-family seat is intentionally absent in BOTH spellings: the
# retired ``gemini`` alias resolves to ``agy`` before Popen (#7041), so the
# strip has to attach to the resolved seat id ``agy`` — otherwise every
# ``--agent gemini`` dispatch would slip a parent operator ``GH_TOKEN`` /
# ``GITHUB_TOKEN`` back in through the alias. Intended App or
# ``LU_AGENT_GITHUB_TOKEN`` identity still reaches that CLI via
# ``build_agent_env`` (#7020).
_GH_TOKEN_AGENTS = {
    "bridge",
    "claude",
    "codex",
    "cursor",
    "deepseek",
    "glm",
    "grok",
    "grok-build",
    "grok-hermes",
    "kimi",
}
_RUNTIME_TMP_TERMINAL_STATUSES = frozenset(
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
    }
)
_RUNTIME_TMP_ORPHAN_MAX_AGE_S = 7 * 24 * 60 * 60
_RUNTIME_TMP_SWEEP_ERROR_DETAILS_LIMIT = 10
_RUNTIME_TMP_TASK_ID_MARKER = ".delegate-task-id"
_READ_ONLY_CHECKOUT_SNAPSHOT_SUFFIX = ".snapshots"
# Task records must stay small enough for frequent reads during dispatch sweeps.
# Whole-checkout read-only snapshots live in ``<task>.snapshots/`` sidecars (#7203).
_READ_ONLY_CHECKOUT_RECORD_BYTE_BUDGET = 256 * 1024
_FALLBACK_SUBS_PATH = _REPO_ROOT / "scripts" / "config" / "agent_fallback_substitutions.yaml"
# Single source for dispatchable agents: argparse choices AND the hard-sub
# validation in _resolve_agent_with_budget_guard (a yaml typo must never
# dispatch a nonexistent adapter).
_DISPATCH_AGENT_CHOICES = (
    "codex",
    "gemini",  # permanent retired-CLI alias → agy (RETIRED_AGENT_ALIASES); gemini CLI not installed
    "claude",
    "grok",  # canonical native CLI seat
    "grok-build",  # permanent alias → grok
    "grok-hermes",  # demoted Hermes path
    "kimi",  # managed native kimi-code CLI seat; web, UI and backend coding only; no automatic fallback chain
    "deepseek",
    "agy",
    "cursor",
    "glm",
)
# "native" is accepted for explicit task-state attribution but is
# observability-only: KimiAdapter treats it identically to an omitted flag
# (#5938 F2). Only "kimicc" changes the transport.
_KIMI_HARNESSES = frozenset({"native", "kimicc"})
# Dispatch agent → effort validator. Keep this mapping at the dispatch
# boundary so an effort unsupported by a provider fails before a task state,
# worktree, runtime lease, or worker process is created. The native Grok alias
# deliberately shares the canonical adapter's vocabulary; grok-hermes is a
# different transport and must not inherit the native CLI restriction.
_EFFORT_VALIDATOR_BY_DISPATCH_AGENT = {
    "grok": "native_grok",
    "grok-build": "native_grok",
}
_MONITOR_API_BASE_URL = "http://127.0.0.1:8765"
_logger = logging.getLogger(__name__)

# Fields of the parsed `dispatch` Namespace that legitimately differ between
# otherwise-identical runs and carry no content of the request itself — the
# only fields ``dispatch_args_sha256`` excludes. Every other parsed `dispatch`
# argument (including --output-schema, --cwd, --worktree, --mode, --model,
# --effort, and every research/lifecycle flag) is bound into the hash, so a
# caller cannot smuggle an extra flag past a check that only names a subset
# of fields (#8430 R3-A r8).
DISPATCH_ARGS_HASH_EXCLUDED_FIELDS = {
    "run_nonce": "unique per attempt; only used for stale cross-host split-brain detection (#7168)",
    "force_new": "a retry/idempotency knob for reusing an existing --task-id, not part of what the seat is asked",
    "initiator": "orchestrator attribution metadata, auto-detected when omitted",
}
# argparse plumbing present on every subcommand's Namespace, not a CLI-supplied
# dispatch argument.
_DISPATCH_ARGS_HASH_ARGPARSE_KEYS = frozenset({"command", "func"})


def dispatch_args_sha256(args: argparse.Namespace) -> str:
    """sha256 of the canonical JSON of every parsed ``dispatch`` argument that binds the record.

    Additive to ``prompt_sha256``/``effective_prompt_sha256`` (which prove the prompt): this proves the
    *arguments* that produced the dispatch, so a record cannot pass a check that compares only a named
    subset of fields while carrying an unchecked extra flag (e.g. a caller-supplied --output-schema).
    Canonical means ``sort_keys=True`` and no separator whitespace, so the same arguments always hash the
    same regardless of argv order.
    """
    payload = {
        key: value
        for key, value in vars(args).items()
        if key not in DISPATCH_ARGS_HASH_EXCLUDED_FIELDS and key not in _DISPATCH_ARGS_HASH_ARGPARSE_KEYS
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# Fields excluded from the advisory binding digest on top of the record hash's
# exclusions (#9275): the envelope reference itself, which the advisor cannot
# know when it issues the envelope, and the flag that prints the digest.
ADVISORY_BINDING_EXCLUDED_FIELDS = frozenset({"advisory_task", "print_advisory_binding"})


def advisory_args_payload(args: argparse.Namespace) -> dict[str, Any]:
    """The arguments ``advisory_args_sha256`` hashes: ``dispatch_args_sha256``'s, without the envelope reference."""
    return {
        key: value
        for key, value in vars(args).items()
        if key not in DISPATCH_ARGS_HASH_EXCLUDED_FIELDS
        and key not in _DISPATCH_ARGS_HASH_ARGPARSE_KEYS
        and key not in ADVISORY_BINDING_EXCLUDED_FIELDS
    }


def advisory_args_sha256(args: argparse.Namespace) -> str:
    """``dispatch_args_sha256`` without the envelope reference: the argument half of the advisory binding."""
    return bounded_advisory.canonical_sha256(advisory_args_payload(args))


def advisory_binding(args_sha256: str, prompt_sha256: str | None) -> str:
    """The digest an advisory envelope binds to: the dispatch arguments and the prompt text they carry.

    Every parsed ``dispatch`` argument except the envelope reference — task id,
    prompt, owned paths, mode, model, research flags — and the SHA-256 of the
    prompt text (a ``--prompt-file`` is bound by content, not only by path), so
    an envelope issued for one dispatch admits no other.
    """
    return bounded_advisory.binding_digest(args_sha256, prompt_sha256)


def _binding_prompt_sha256(args: argparse.Namespace, *, read_stdin: bool) -> str | None:
    """SHA-256 of the dispatch's prompt text for the advisory binding; None for an unread stdin prompt.

    Raises ``OSError`` when a ``--prompt-file`` cannot be read.
    """
    if getattr(args, "prompt_file", None):
        text = Path(args.prompt_file).read_text(encoding="utf-8")
    elif getattr(args, "prompt", None) == "-":
        if not read_stdin:
            return None
        text = sys.stdin.read()
    elif getattr(args, "prompt", None) is not None:
        text = str(args.prompt)
    else:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def advisory_binding_sha256(args: argparse.Namespace, *, read_stdin: bool = False) -> str:
    """The advisory binding of a parsed dispatch (what ``--print-advisory-binding`` prints)."""
    return advisory_binding(advisory_args_sha256(args), _binding_prompt_sha256(args, read_stdin=read_stdin))


def _resolve_dispatch_harness(agent: str, harness: str | None) -> str | None:
    """Validate the opt-in Kimi harness selector without changing its seat."""
    if harness is None:
        return None
    if agent != "kimi":
        raise ValueError("--harness is currently supported only with --agent kimi")
    if harness not in _KIMI_HARNESSES:
        raise ValueError(f"unsupported Kimi harness {harness!r}; expected one of {sorted(_KIMI_HARNESSES)}")
    return harness


def _warn_kimicc_oauth_token_life(harness: str | None, hard_timeout: int) -> None:
    """Pre-flight note when a KimiCC dispatch can outlive its OAuth session (#5938 F4)."""
    if harness != "kimicc" or hard_timeout <= _KIMICC_OAUTH_SESSION_LIFE_S:
        return
    print(
        f"⚠️  --harness kimicc with --hard-timeout {hard_timeout}s exceeds the ~15-minute "
        "Kimi OAuth session lifetime; the wrapper refreshes the session only at spawn, "
        "so calls still running past ~15 minutes may fail auth. Prefer shorter dispatches "
        "and relaunch instead of one long call.",
        file=sys.stderr,
    )


def _validate_dispatch_effort(agent: str, effort: str | None) -> None:
    """Fail closed when a dispatch effort cannot reach its selected CLI.

    The top-level ``--effort`` parser accepts the cross-runtime vocabulary.
    Provider-specific limits belong here, before dispatch creates any durable
    task or process state. Revalidate after a budget substitution because that
    can change the effective provider.
    """
    if effort is None:
        return
    validator = _EFFORT_VALIDATOR_BY_DISPATCH_AGENT.get(agent.strip().lower())
    if validator == "native_grok":
        from agent_runtime.adapters.grok_build import validate_grok_effort

        try:
            validate_grok_effort(effort)
        except ValueError as exc:
            raise ValueError(
                f"--agent {agent} cannot use --effort {effort!r}: {exc}. "
                "Refusing before worker spawn; choose low, medium, or high, "
                "or omit --effort for the native Grok default."
            ) from exc


def _resolve_github_token() -> str | None:
    """Resolve the App-first GitHub token used by an agent shell."""
    from agent_runtime.agent_github_identity import resolve_agent_github_identity

    return resolve_agent_github_identity(bash_secrets_path=_BASH_SECRETS_PATH).token


def _inject_gh_token_for_agent(worker_env: dict[str, str], agent: str) -> None:
    """Inject the resolved agent identity for every dispatchable push lane."""
    worker_env.pop("GITHUB_TOKEN", None)
    if agent not in _GH_TOKEN_AGENTS:
        worker_env.pop("GH_TOKEN", None)
        return

    token = _resolve_github_token()
    if token:
        worker_env["GH_TOKEN"] = token
        return

    # Without an agent identity, do not allow a dispatch shell to inherit an
    # operator credential by accident through its parent environment.
    worker_env.pop("GH_TOKEN", None)


def _scrub_unusable_gh_config_dir(worker_env: dict[str, str]) -> None:
    """Drop empty/sandbox GH_CONFIG_DIR so review seats recover host gh (#7472).

    A prior agent-runtime token-mode (or pre-#7166) isolate leaves
    ``GH_CONFIG_DIR`` pointing at an empty dir. Inherited into the next
    read-only review dispatch, that makes ``gh`` report unauthenticated even
    when ``~/.config/gh/hosts.yml`` is valid. Only drop unusable paths; a
    real hosts.yml dir (or unset) is left alone. Never copies token values.
    """
    from agent_runtime.env_sanitize import usable_host_gh_config_dir

    current = worker_env.get("GH_CONFIG_DIR")
    if current and usable_host_gh_config_dir(current) is None:
        worker_env.pop("GH_CONFIG_DIR", None)


DEFAULT_HARD_TIMEOUT_S = 7200
# Silence timeout is a composite hang backstop: stdout/stderr, liveness-file
# updates, and process-tree CPU/disk activity all keep it alive. Do not lower it
# for build/test/enrich jobs merely because wrapper stdout is expected to be
# quiet; that recreates the false-kill shape from #3875.
DEFAULT_SILENCE_TIMEOUT_S = 3600
# Fail fast only when no observable startup activity occurs: stdout/stderr,
# documented liveness-file updates, or process-tree CPU/disk work. This is
# distinct from the long silence window above (#2071).
# 600s: reasoning-heavy models at high/max effort routinely think for minutes
# before their first token; the old 180s killed healthy workers mid-thought
# (observed: deepseek review dispatch reaped at 181s, 1s over the limit).
DEFAULT_INITIAL_RESPONSE_TIMEOUT_S = 600
# KimiCC headless calls authenticate with a Kimi OAuth session whose
# lifetime is roughly 15 minutes (~840s). The wrapper refreshes credentials
# only at spawn, so a worker still running past that point can start failing
# auth.
_KIMICC_OAUTH_SESSION_LIFE_S = 840
# Timeout bounds for synchronous subprocess invocations (#7213).
DEFAULT_GIT_TIMEOUT_S: float = 30.0
DEFAULT_NETWORK_GIT_TIMEOUT_S: float = 180.0
DEFAULT_GH_CLI_TIMEOUT_S: float = 180.0


# ---------------------------------------------------------------------------
# State file helpers
# ---------------------------------------------------------------------------


def _state_path_no_create(task_id: str) -> Path:
    """The task record's path, without creating the task directory (for readers that must not write)."""
    # task-ids with slashes would break paths; sanitize
    safe = task_id.replace("/", "_").replace("\\", "_")
    return tasks_dir() / f"{safe}.json"


def _state_path(task_id: str) -> Path:
    tasks_dir().mkdir(parents=True, exist_ok=True)
    return _state_path_no_create(task_id)


def _result_path(task_id: str) -> Path:
    return _state_path(task_id).with_suffix(".result")


def _archived_state_path(task_id: str) -> Path:
    """Where ``stale_task_records archive`` moved an old terminal record (#8625).

    Only terminal records are archived. By-id readers (status, wait, task-id
    reuse) fall back to this path; the worktree claim scan never needs it.
    """
    return task_record_store.archived_task_record_path(tasks_dir(), task_id)


def _read_state_or_archived(task_id: str) -> tuple[Path, dict[str, Any] | None]:
    """Return ``task_id``'s record path and state: the hot record, else the archived one (#8625).

    An archived state is marked ``archived: true`` and its ``result_file`` names
    the ``.result`` sidecar that moved into the archive with it. Archived
    records are terminal, so no caller ever rewrites one.
    """
    state_path = _state_path(task_id)
    state = _read_state(state_path)
    if state is not None:
        return state_path, state
    archived_path = _archived_state_path(task_id)
    archived = _read_state(archived_path)
    if archived is None:
        return state_path, None
    archived = {**archived, "archived": True}
    if "result_file" in archived:
        archived["result_file"] = task_record_store.relocated_result_file(archived_path, archived["result_file"])
    return archived_path, archived


def _generate_run_nonce() -> str:
    """Generate a unique run identifier to disambiguate dispatches (#7168)."""
    return uuid.uuid4().hex[:16]


def _archive_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")


def _archived_artifact_path(path: Path, stamp: str) -> Path:
    dest = path.with_name(f"{path.stem}.{stamp}.archived{path.suffix}")
    if dest.exists():
        dest = path.with_name(f"{path.stem}.{stamp}.{os.getpid()}.archived{path.suffix}")
    return dest


def _read_only_snapshot_dir_for(task_id: str) -> Path:
    state_path = _state_path(task_id)
    return state_path.parent / f"{state_path.stem}{_READ_ONLY_CHECKOUT_SNAPSHOT_SUFFIX}"


_READ_ONLY_SNAPSHOT_DIGEST_NAME = "digest.json"
_READ_ONLY_SNAPSHOT_RETENTION_DIGEST = "digest"
_READ_ONLY_SNAPSHOT_RETENTION_FULL = "full"


def _read_only_snapshot_sidecar_path(task_id: str, phase: str) -> Path:
    return _read_only_snapshot_dir_for(task_id) / f"read_only_checkout_{phase}.json"


def _read_only_snapshot_digest_path(task_id: str) -> Path:
    return _read_only_snapshot_dir_for(task_id) / _READ_ONLY_SNAPSHOT_DIGEST_NAME


def _write_read_only_snapshot_sidecar(
    task_id: str,
    phase: str,
    snapshot: dict[str, str] | None,
) -> None:
    """Persist a read-only checkout snapshot beside the task record."""
    path = _read_only_snapshot_sidecar_path(task_id, phase)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".json.tmp.{os.getpid()}")
    tmp.write_text(
        json.dumps(snapshot if snapshot is not None else {}, separators=(",", ":")),
        encoding="utf-8",
    )
    os.replace(tmp, path)


def _canonical_snapshot_bytes(snapshot: dict[str, str] | None) -> bytes:
    """Bytes written for a phase sidecar: compact JSON, empty object when missing."""
    payload = snapshot if isinstance(snapshot, dict) else {}
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def _snapshot_digest_phase(snapshot: dict[str, str] | None) -> dict[str, Any]:
    raw = _canonical_snapshot_bytes(snapshot)
    payload = snapshot if isinstance(snapshot, dict) else {}
    return {"sha256": hashlib.sha256(raw).hexdigest(), "entries": len(payload)}


def read_only_snapshot_digest(
    pre: dict[str, str] | None,
    post: dict[str, str] | None,
) -> dict[str, Any]:
    """Content digest of the two canonical checkout snapshots."""
    return {"pre": _snapshot_digest_phase(pre), "post": _snapshot_digest_phase(post)}


def read_only_snapshot_keep_full(
    mutation_paths: list[str] | None,
    snapshot_error: str | None,
) -> bool:
    """Full sidecars stay only for a recorded mutation or a snapshot error."""
    return bool(mutation_paths) or snapshot_error is not None


def _read_only_phase_paths(snapshot_dir: Path) -> list[Path]:
    return [snapshot_dir / f"read_only_checkout_{phase}.json" for phase in ("pre", "post")]


def stage_read_only_snapshot_digest(
    snapshot_dir: Path,
    pre: dict[str, str] | None,
    post: dict[str, str] | None,
) -> int:
    """Write ``digest.json`` and leave the phase files in place.

    Returns the bytes a later discard would reclaim. Writing the digest first
    means a crash before the task record is published still leaves the full
    sidecars on disk.
    """
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    before = 0
    for path in _read_only_phase_paths(snapshot_dir):
        try:
            info = path.lstat()
        except OSError:
            continue
        if stat.S_ISREG(info.st_mode):
            before += info.st_size
    digest = read_only_snapshot_digest(pre, post)
    digest_path = snapshot_dir / _READ_ONLY_SNAPSHOT_DIGEST_NAME
    raw = json.dumps(digest, separators=(",", ":")).encode("utf-8")
    tmp = digest_path.with_suffix(f".json.tmp.{os.getpid()}")
    tmp.write_bytes(raw)
    os.replace(tmp, digest_path)
    return before - len(raw)


def discard_read_only_snapshot_phases(snapshot_dir: Path) -> None:
    """Unlink regular phase files. Symlinks are left in place."""
    for path in _read_only_phase_paths(snapshot_dir):
        try:
            info = path.lstat()
        except OSError:
            continue
        if stat.S_ISREG(info.st_mode):
            path.unlink()


def collapse_read_only_snapshot_dir(
    snapshot_dir: Path,
    pre: dict[str, str] | None,
    post: dict[str, str] | None,
) -> int:
    """Replace phase JSON with ``digest.json``. Return bytes reclaimed.

    The digest hashes the same canonical bytes ``_write_read_only_snapshot_sidecar``
    writes. Callers that still have to publish the task record must
    :func:`stage_read_only_snapshot_digest`, write the record, then
    :func:`discard_read_only_snapshot_phases`. This helper does both file steps
    and is for a caller that has already published the record.
    """
    reclaimed = stage_read_only_snapshot_digest(snapshot_dir, pre, post)
    discard_read_only_snapshot_phases(snapshot_dir)
    return reclaimed


def _load_read_only_snapshot_sidecar(task_id: str, phase: str) -> dict[str, str] | None:
    path = _read_only_snapshot_sidecar_path(task_id, phase)
    if not path.exists():
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return loaded if isinstance(loaded, dict) else None


def _hydrate_read_only_checkout_snapshots(state: dict[str, Any]) -> dict[str, Any]:
    """Load sidecar snapshots into the in-memory state dict when present."""
    task_id = state.get("task_id")
    if not isinstance(task_id, str):
        return state
    for phase in ("pre", "post"):
        key = f"read_only_checkout_{phase}"
        if key in state and isinstance(state[key], dict):
            continue
        sidecar = _load_read_only_snapshot_sidecar(task_id, phase)
        if sidecar is not None:
            state[key] = sidecar
    return state


def _archive_task_artifacts(task_id: str, *, stamp: str | None = None) -> list[Path]:
    """Move the prior record, result and local diagnostics aside. Never overwrite an archive.

    Holds the per-task lock for the whole rename. The retention sweep holds
    that same lock across its digest and record write; without it, this move
    can land after the sweep's hot-name recheck and the sweep then creates a
    new hot record whose sidecar is already gone.
    """
    stamp = stamp or _archive_stamp()
    state_path = _state_path(task_id)
    archived: list[Path] = []
    with task_state_lock(state_path):
        diagnostic = _diagnostic_path(task_id)
        rotated = diagnostic.with_name(diagnostic.name + _DIAG_ROTATED_SUFFIX)
        for path in (state_path, _result_path(task_id), diagnostic, rotated):
            if not path.exists():
                continue
            dest = _archived_artifact_path(path, stamp)
            os.replace(path, dest)
            archived.append(dest)
        snapshot_dir = state_path.parent / f"{state_path.stem}{_READ_ONLY_CHECKOUT_SNAPSHOT_SUFFIX}"
        if snapshot_dir.is_dir():
            dest = snapshot_dir.parent / f"{snapshot_dir.name}.{stamp}.archived"
            if dest.exists():
                dest = snapshot_dir.parent / f"{snapshot_dir.name}.{stamp}.{os.getpid()}.archived"
            os.replace(snapshot_dir, dest)
            archived.append(dest)
    return archived


def _existing_task_status(state_path: Path, existing: dict[str, Any] | None) -> str:
    status = existing.get("status") if existing else None
    if isinstance(status, str) and status.strip():
        return status
    if state_path.exists():
        return "unreadable"
    return "result-only"


def _core_terminal_fields(
    *,
    status: str,
    duration_s: float,
    response: str,
    result_file: str | None,
    stderr_excerpt: str | None,
    returncode: int | None,
    returncode_reason: str | None,
    dirty_on_exit: bool | None,
    commits_ahead: int | None,
    needs_finalize: bool,
    finalize_error: str | None,
    last_error: str | None,
) -> dict[str, Any]:
    """The complete set of fields that define a finished dispatch's outcome.

    Both writers that can be the LAST word on a task — the normal checkpoint and
    the interrupt fallback — build their record here. The fallback used to
    hand-assemble a subset, so an interrupted run persisted a terminal status
    beside stale placeholder ``response_chars``/``exit_code``/``last_error``:
    the same duplication that let the return-code invariant apply on one path
    and not the other. One definition, both paths. (Cross-family review of
    #5807, round ten.)
    """
    return {
        "status": status,
        "finished_at": datetime.now(UTC).isoformat(),
        "duration_s": round(duration_s, 3),
        "response_chars": len(response),
        "result_file": result_file,
        "result_sha256": hashlib.sha256(response.encode("utf-8")).hexdigest() if result_file else None,
        "stderr_excerpt": stderr_excerpt,
        "returncode": returncode,
        "returncode_reason": returncode_reason,
        "last_error": last_error if status != "done" else None,
        "exit_code": returncode,
        "worktree_dirty_on_exit": dirty_on_exit,
        "commits_ahead": commits_ahead,
        "needs_finalize": needs_finalize,
        "finalize_error": finalize_error,
        "peak_rss_mib": _children_peak_rss_mib(),
    }


def _children_peak_rss_mib() -> float | None:
    """Peak RSS of the largest process this worker has reaped, in MiB (#8645).

    The worker is the waiting parent of the agent CLI, so
    ``getrusage(RUSAGE_CHILDREN)`` covers the CLI and every descendant that was
    itself waited for (a shell tool's pytest, xdist workers, git). It is the
    largest single process, not the tree's sum, and misses descendants that
    were never reaped up the chain (daemonized or still running at exit).
    """
    try:
        peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    except (OSError, ValueError):
        return None
    if peak <= 0:
        return None
    # Linux reports KiB; macOS reports bytes.
    peak_bytes = peak if sys.platform == "darwin" else peak * 1024
    return round(peak_bytes / (1024 * 1024), 1)


def _apply_returncode_invariant(status: str, returncode: int | None) -> str:
    """A success without a terminal child return code is not a success (#4837).

    Lives on its own because it is applied twice: once on the normal completion
    path and once in the interrupt fallback. When only the normal path enforced
    it, a cancel landing between classification and the check persisted
    ``done`` with a null return code — the fallback contradicting the invariant
    precisely when it was exercised (cross-family review of #5807).
    """
    if status == "done" and returncode is None:
        return "failed"
    return status


@contextlib.contextmanager
def _sigterm_deferred():
    """Ignore SIGTERM for the duration of a critical write, then restore.

    The worker's SIGTERM handler raises KeyboardInterrupt, and an exception
    raised inside an ``except`` suite is not caught by that same suite. So a
    SECOND cancel arriving while the terminal-status fallback is writing escapes
    before the atomic rename, and the task stays recorded as ``running`` even
    though its worker finished — the very failure the fallback exists to prevent
    (cross-family review of #5807).

    The window is one small file write. Deferring the signal across it cannot
    hang a cancel meaningfully, and the interrupt is re-raised immediately after.
    Degrades to a no-op off the main thread, where ``signal.signal`` is illegal.
    """
    try:
        previous = signal.signal(signal.SIGTERM, signal.SIG_IGN)
    except (ValueError, OSError):  # not the main thread — nothing to defer
        yield
        return
    try:
        yield
    finally:
        with contextlib.suppress(ValueError, OSError):
            signal.signal(signal.SIGTERM, previous)


def _detach_read_only_checkout_snapshots(state: dict[str, Any]) -> dict[str, Any]:
    """Drop hydrated snapshot dicts before persisting; sidecars are canonical."""
    task_id = state.get("task_id")
    if not isinstance(task_id, str):
        return state
    detached = dict(state)
    for phase in ("pre", "post"):
        key = f"read_only_checkout_{phase}"
        if key in detached and _read_only_snapshot_sidecar_path(task_id, phase).exists():
            detached.pop(key, None)
    return detached


def _write_state_atomic(path: Path, state: dict[str, Any]) -> None:
    """Write state JSON atomically via write-rename.

    os.replace() is atomic on POSIX, so concurrent readers never see
    a partially-written file. Ensures the parent directory exists
    before writing — callers that bypass _state_path may not have
    created it yet.

    Concurrency: a per-task lock serializes worker and probe writes. Each
    writer also uses a PID-suffixed tmp filename before ``os.replace``.
    """
    if state.get("require_review_verdict"):
        state = {
            **state,
            "failure_reason": _review_task_failure_reason(state) if state.get("status") == "failed" else None,
        }
    state = _detach_read_only_checkout_snapshots(state)
    with task_state_lock(path):
        _write_record_unlocked(path, state)


def _review_task_failure_reason(state: dict[str, Any]) -> str:
    """Give every failed verdict-required review a stable, queryable cause."""
    if state.get("review_verdict_failure"):
        return state["review_verdict_failure"]
    # A typed cause another gate already set (#9275) is kept, never renamed.
    if isinstance(state.get("failure_reason"), str) and state["failure_reason"]:
        return state["failure_reason"]
    if state.get("read_only_mutation_paths"):
        return "read_only_checkout_mutation"
    if state.get("read_only_checkout_snapshot_error"):
        return "read_only_checkout_snapshot_failed"
    if state.get("returncode") is None:
        if state.get("returncode_reason") in {
            "worktree preparation failed",
            "forward configuration failed",
            "worker process was not started",
            "scoped worker startup was ambiguous; not relaunched",
        }:
            return "review_worker_not_started"
        return "review_worker_returncode_missing"
    if state["returncode"] != 0:
        return "review_worker_nonzero_exit"
    return "review_worker_reported_failure"


def _append_dispatch_event(event: str, **fields: Any) -> None:
    """Append one delegate JSONL event without making telemetry fatal."""
    payload = {
        "ts": datetime.now(UTC).isoformat(),
        "event": event,
        **fields,
    }
    try:
        tasks_dir().mkdir(parents=True, exist_ok=True)
        line = (json.dumps(payload, ensure_ascii=False, default=str) + "\n").encode("utf-8")
        fd = os.open(
            str(tasks_dir() / "dispatch_events.jsonl"),
            os.O_APPEND | os.O_CREAT | os.O_WRONLY,
            0o600,
        )
        try:
            os.write(fd, line)
        finally:
            os.close(fd)
    except OSError as exc:
        print(
            f"[delegate] WARNING: failed to write dispatch event: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )


def _read_state_json(path: Path) -> dict[str, Any] | None:
    """Read a state file without hydrating read-only snapshot sidecars."""
    if not path.exists():
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return loaded if isinstance(loaded, dict) else None


def _read_state(path: Path) -> dict[str, Any] | None:
    """Read a state file; return None if missing or corrupted."""
    state = _read_state_json(path)
    if state is None:
        return None
    return _hydrate_read_only_checkout_snapshots(state)


def _state_file_unparseable(path: Path) -> bool:
    """True when a state file exists on disk but cannot be parsed to a dict."""
    return path.is_file() and _read_state_json(path) is None


def _bound_task_state_unparseable_reason(path: Path) -> str | None:
    """Return a refusal reason when a layout-bound state file is corrupt."""
    for task_id in _task_status_candidates_for_worktree(path):
        state_path = _state_path(task_id)
        if _state_file_unparseable(state_path):
            return f"unparseable task state for task-id={task_id}"
    return None


def _pid_alive(pid: int) -> bool:
    """Check if a PID is currently alive via signal-0 probe.

    os.kill(pid, 0) raises ProcessLookupError if the PID doesn't exist,
    PermissionError if it exists but is owned by another user (which
    still counts as "alive" for our purposes), or returns None on success.
    """
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists, we just can't signal it
    return True


def _normalize_worktree_path(raw_path: str, *, repo_root: Path | None = None) -> Path:
    """Resolve a worktree path relative to the repo root.

    Every task record stores ``worktree_path`` in this resolved absolute form,
    which is what settle's active-claim scan compares against (#8610).
    """
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (repo_root if repo_root is not None else _REPO_ROOT) / path
    return path.resolve()


def _helper_worktree_path(raw_path: str | None, validated_path: Path | None) -> Path:
    """Return the path a worktree helper operates on (#8775).

    ``validated_path`` is the path dispatch resolved once at validation and
    re-checked after taking the worktree lock. It is used exactly as given:
    resolving it again would follow a symlink swapped in after that re-check.
    Only ``raw_path``, from direct callers that have no validated path, is
    resolved here.
    """
    if validated_path is not None:
        return validated_path
    if raw_path is None:
        raise ValueError("a worktree helper needs raw_path or validated_path")
    return _normalize_worktree_path(raw_path)


# Caller-supplied paths reach the worker prompt, task records, and subprocess
# cwd (#8775). Controls (Cc: C0, C1, DEL) and line/paragraph separators (Zl,
# Zp) can start a new line in a prompt; format controls (Cf: bidi overrides
# and isolates such as U+202E and U+2066, zero-width characters) can make the
# displayed text differ from the stored one; lone surrogates (Cs) are bytes
# that are not UTF-8. None belongs in a filesystem path this repo uses.
_CALLER_PATH_FORBIDDEN_CATEGORIES = frozenset({"Cc", "Cf", "Cs", "Zl", "Zp"})


def _caller_path_control_char_error(flag: str, raw: str, *, what: str = "the path") -> str | None:
    """Refuse a ``--worktree``/``--cwd`` value that contains a control or format character.

    The message names the rule and the offending code point, never the raw
    value, so the refusal itself cannot carry injected text.
    """
    for offset, char in enumerate(raw):
        if unicodedata.category(char) in _CALLER_PATH_FORBIDDEN_CATEGORIES:
            return (
                f"❌ {flag} refused: {what} contains control or format character U+{ord(char):04X} "
                f"at offset {offset}; caller-supplied paths may not contain control characters, "
                "format (bidi) characters, or line separators (#8775)."
            )
    return None


def _validate_caller_path(flag: str, raw: str, *, resolve: Callable[[str], Path]) -> tuple[Path | None, str | None]:
    """Check ``raw``, resolve it once, and check the resolved path (#8775).

    A clean name can be a symlink to a path that is not clean, so both the
    caller's string and the path it resolves to are checked. Returns the
    resolved path, which dispatch uses for every later step instead of ``raw``.
    """
    error = _caller_path_control_char_error(flag, raw)
    if error:
        return None, error
    try:
        resolved = resolve(raw)
    except (OSError, RuntimeError) as exc:
        return None, f"❌ {flag} refused: the path cannot be resolved ({type(exc).__name__}) (#8775)."
    error = _caller_path_control_char_error(flag, str(resolved), what="the resolved path")
    if error:
        return None, error
    return resolved, None


def _worktree_containment_anchor(agent: str, *, repo_root: Path) -> tuple[Path | None, str | None]:
    """Return ``<resolved repo>/.worktrees/dispatch/<agent>`` when each level is a real directory.

    Resolving the anchor would let a symlinked ``.worktrees``, ``dispatch`` or
    agent directory move the whole subtree outside the repository, so each
    level is checked with ``lstat`` instead: it must exist and be a directory,
    not a symlink (#8775).
    """
    if agent in {"", ".", ".."} or "/" in agent or "\\" in agent:
        return None, f"❌ --worktree refused: agent {agent!r} is not a single path component (#8775)."
    anchor = repo_root.resolve()
    for part in (".worktrees", "dispatch", agent):
        anchor = anchor / part
        try:
            mode: int | None = os.lstat(anchor).st_mode
        except OSError:
            mode = None
        if mode is None or stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            state = "is missing" if mode is None else "is a symlink" if stat.S_ISLNK(mode) else "is not a directory"
            return None, (
                f"❌ --worktree refused: {str(anchor)!r} {state}; an explicit --worktree PATH needs "
                f".worktrees/dispatch/{agent}/ to be a real directory inside the target repository (#8775). "
                "Pass bare `--worktree` to auto-create one."
            )
    return anchor, None


def _validate_explicit_worktree(raw: str, *, agent: str, repo_root: Path) -> tuple[Path | None, str | None]:
    """Validate an explicit ``--worktree PATH`` and return its resolved path (#8775).

    The path must resolve, symlinks followed, strictly inside the
    real-directory anchor ``<repo>/.worktrees/dispatch/<agent>/``, and neither
    the caller's string nor the resolved path may contain a control or format
    character. The message quotes only resolved paths via ``repr``.
    """
    candidate, error = _validate_caller_path(
        "--worktree", raw, resolve=lambda value: _normalize_worktree_path(value, repo_root=repo_root)
    )
    if candidate is None:
        return None, error
    anchor, error = _worktree_containment_anchor(agent, repo_root=repo_root)
    if anchor is None:
        return None, error
    if candidate != anchor and candidate.is_relative_to(anchor):
        return candidate, None
    return None, (
        f"❌ --worktree refused: {str(candidate)!r} does not resolve under {str(anchor)!r}; "
        f"an explicit --worktree PATH must be a directory inside .worktrees/dispatch/{agent}/ "
        "of the target repository after following symlinks (#8775). "
        "Pass bare `--worktree` to auto-create one."
    )


def _validated_path_changed_error(flag: str, validated: Path) -> str | None:
    """Refuse when a validated path no longer resolves to itself (#8775).

    ``validated`` was fully resolved at validation time, so it keeps resolving
    to itself until one of its components is replaced by a symlink. Dispatch
    calls this after taking the worktree lock and before the worktree helpers
    run, and the helpers use ``validated`` as given without resolving it again
    (:func:`_helper_worktree_path`), so a swap after validation is refused
    instead of redirecting the lock, git operations, or the worker.

    Scope: the prompt-injection vector of #8775 is closed by the character
    check on the raw and resolved paths plus JSON quoting in the worker
    prompt. Path containment is checked on real directories and re-checked
    here, after the lock. A symlink swap in the remaining gap (after this
    check, while git or the filesystem follows the path) needs write access
    to a directory on ``validated``. Under ``.worktrees/dispatch/`` that is a
    process running as the same user, which already holds every capability
    the dispatcher has, so the race grants it nothing new; it is out of
    scope. ``--cwd`` also accepts registered worktrees elsewhere, where write
    access to any parent directory is enough to swap the worktree without
    access to it. The out-of-scope argument holds there only when every
    directory on the path is writable by the dispatching user alone.

    ``--dry-run`` takes no lock: a ``--worktree`` dry run still calls this
    check, and a ``--cwd`` dry run returns before calling it.
    """
    try:
        current: Path | None = validated.resolve()
    except (OSError, RuntimeError):
        current = None
    if current == validated:
        return None
    return (
        f"❌ {flag} refused: {str(validated)!r} changed after validation (a component is now a symlink "
        "or cannot be resolved); refusing to follow it (#8775)."
    )


def _resolve_output_schema(
    raw_path: str | None,
    *,
    agent: str,
) -> tuple[str | None, str | None]:
    """Validate one provider output schema before any worker is spawned.

    The Codex CLI is currently the only native dispatch adapter with a
    file-backed structured-output flag. Returning an absolute path prevents
    the detached worker from resolving a relative schema against a different
    working directory. The SHA is persisted in task state as proof of the
    exact schema bytes admitted at the dispatch boundary.
    """
    if raw_path is None:
        return None, None
    if agent != "codex":
        raise ValueError("--output-schema is supported only with the effective codex agent")

    candidate = Path(raw_path).expanduser()
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise ValueError(f"output schema does not exist: {candidate}") from exc
    if not resolved.is_file():
        raise ValueError(f"output schema is not a regular file: {resolved}")
    try:
        payload = resolved.read_bytes()
        schema = json.loads(payload.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"output schema is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(schema, dict):
        raise ValueError("output schema JSON must be an object")
    return str(resolved), hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------------------
# Worktree lifecycle — create, validate, reuse
# ---------------------------------------------------------------------------
#
# The four failure classes below drove a design change from "silent-reuse
# existing directory" to "validate before reuse, raise a specific error
# otherwise." Silent reuse is how #1473 shipped a stub alignment_manifest.py
# as a real PR: the dispatched worktree already existed on a stale branch
# and delegate.py inherited that state. Each exception carries the exact
# remediation command in its message so operators can unblock without
# digging.


class WorktreeBranchMismatch(RuntimeError):
    """Existing worktree is on a branch other than the expected dispatch branch."""


class WorktreeDirty(RuntimeError):
    """Existing worktree has uncommitted changes; refuse to reuse."""


class WorktreeStaleBase(RuntimeError):
    """Existing worktree is behind origin/<base> and the fast-forward rebase failed."""


class WorktreeBranchDiverged(RuntimeError):
    """A local --branch ref contains commits absent from its fetched origin ref."""


WorktreeLockError = worktree_claims.WorktreeLockError
WorktreeLockTimeout = worktree_claims.WorktreeLockTimeout
WorktreeLockReentry = worktree_claims.WorktreeLockReentry

# Dispatch (create-or-attach, then publish the task record) and every
# dispatch-worktree removal (see _remove_dispatch_worktree) serialize on one
# lock per worktree, so an attachment can never land between a remover's claim
# scan and its removal (#8610). The lock itself lives in
# scripts/orchestration/worktree_claims.py, shared with the scheduled reaper.
_WORKTREE_LOCK_DEFAULT_TIMEOUT_S = worktree_claims.DEFAULT_LOCK_TIMEOUT_S
# Test seam: overrides ``<git common dir>/lu-worktree-locks`` when set.
_WORKTREE_LOCK_DIR: Path | None = None


def _worktree_lock_dir() -> Path:
    """Return the lock home shared by every checkout of this repository."""
    if _WORKTREE_LOCK_DIR is not None:
        return _WORKTREE_LOCK_DIR
    common_dir = _git_common_dir(_REPO_ROOT)
    return (common_dir if common_dir is not None else tasks_dir().parent) / worktree_claims.LOCK_DIR_NAME


def _worktree_lock_path(path: Path | str) -> tuple[str, Path]:
    """Return the canonical absolute worktree path and its lock file."""
    return worktree_claims.lock_path(path, lock_dir=_worktree_lock_dir())


def worktree_lock(path: Path | str, timeout_s: float | None = None) -> contextlib.AbstractContextManager[None]:
    """Hold this repository's exclusive advisory lock for one worktree path.

    See :func:`scripts.orchestration.worktree_claims.worktree_lock`. Every
    failure raises a :class:`WorktreeLockError`; ``timeout_s`` defaults to
    ``_WORKTREE_LOCK_DEFAULT_TIMEOUT_S``.
    """
    return worktree_claims.worktree_lock(
        path,
        lock_dir=_worktree_lock_dir(),
        timeout_s=_WORKTREE_LOCK_DEFAULT_TIMEOUT_S if timeout_s is None else timeout_s,
    )


def _normalize_task_id(agent: str, task_id: str) -> str:
    """Strip a leading ``{agent}-`` or ``{agent}/`` from task_id.

    Shared by :func:`_derive_worktree_branch` and :func:`_auto_worktree_path`
    so the branch name and the dispatch/ subtree path land in sync even
    when the caller accidentally prefixed the agent name (our own tools
    often do — task-ids like ``codex-1472-foo`` are common).
    """
    return worktree_paths.normalize_task_id(agent, task_id)


def _runtime_tmp_lease_name(task_id: str) -> str:
    """Return one safe path component for a task's runtime tmp lease."""
    return re.sub(r"[^A-Za-z0-9._-]+", "-", task_id).strip("./-") or "task"


def _create_runtime_tmp_lease(task_id: str) -> tuple[Path, Path]:
    """Create and return a task lease plus its resolved namespace root.

    The lease is intentionally deterministic per task ID: a task can restart
    after its previous worker has finished and re-create the same root, while
    Stage 2 will eventually handle roots left by crashed processes.

    #7164: the namespace lives under the disk-backed fleet scratch root
    (``scripts/common/scratch.py``), not tmpfs ``/tmp`` — worker TMPDIR
    payloads must not be able to exhaust the small per-user tmpfs quota.
    """
    namespace_root = ensure_scratch_root() / "learn-ukrainian"
    try:
        namespace_root.mkdir(parents=True, exist_ok=True)
        namespace_stat = namespace_root.lstat()
    except OSError as exc:
        raise RuntimeError(
            f"could not create runtime tmp namespace {namespace_root}: {exc}",
        ) from exc
    if stat.S_ISLNK(namespace_stat.st_mode):
        raise RuntimeError(
            f"runtime tmp namespace must not be a symlink: {namespace_root}",
        )

    lease_root = namespace_root / _runtime_tmp_lease_name(task_id)
    try:
        lease_root.mkdir(exist_ok=True)
        lease_stat = lease_root.lstat()
        resolved_namespace = namespace_root.resolve(strict=True)
        resolved_lease = lease_root.resolve(strict=True)
    except OSError as exc:
        raise RuntimeError(
            f"could not create runtime tmp lease {lease_root}: {exc}",
        ) from exc
    if stat.S_ISLNK(lease_stat.st_mode):
        raise RuntimeError(
            f"runtime tmp lease must not be a symlink: {lease_root}",
        )
    if not stat.S_ISDIR(lease_stat.st_mode) or resolved_lease.parent != resolved_namespace:
        raise RuntimeError(
            f"runtime tmp lease is not a direct child of its namespace: {lease_root}",
        )
    _write_runtime_tmp_task_id_marker(resolved_lease, task_id)
    return resolved_lease, resolved_namespace


def _runtime_tmp_task_id_marker_path(lease_root: Path) -> Path:
    return lease_root / _RUNTIME_TMP_TASK_ID_MARKER


def _write_runtime_tmp_task_id_marker(
    lease_root: Path,
    task_id: str,
    *,
    no_clobber: bool = False,
) -> None:
    """Persist the owning task id so orphan sweeps never scan task records."""
    marker = _runtime_tmp_task_id_marker_path(lease_root)
    if no_clobber:
        try:
            fd = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            return
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(task_id)
        return
    tmp = marker.with_suffix(f".tmp.{os.getpid()}")
    tmp.write_text(task_id, encoding="utf-8")
    os.replace(tmp, marker)


def _read_runtime_tmp_task_id_marker(lease_root: Path) -> str | None:
    marker = _runtime_tmp_task_id_marker_path(lease_root)
    try:
        task_id = marker.read_text(encoding="utf-8").strip()
    except (OSError, ValueError):
        return None
    return task_id or None


def _runtime_tmp_lease_bytes(lease_root: Path) -> int:
    """Count lease payload bytes without traversing directory symlinks."""
    total = 0
    seen_regular_files: set[tuple[int, int]] = set()
    for directory, dirnames, filenames in os.walk(lease_root, followlinks=False):
        for name in [*dirnames, *filenames]:
            path = Path(directory) / name
            try:
                entry = path.lstat()
            except FileNotFoundError:
                continue
            if stat.S_ISREG(entry.st_mode):
                inode = (entry.st_dev, entry.st_ino)
                if inode in seen_regular_files:
                    continue
                seen_regular_files.add(inode)
                total += entry.st_size
            elif stat.S_ISLNK(entry.st_mode):
                # Account for the link's own small directory entry, never its
                # target. ``os.walk(..., followlinks=False)`` will not descend.
                total += entry.st_size
    return total


def _grant_owner_rwx_at(path: Path, *, dir_fd: int) -> bool:
    """Give the owner access to a non-symlink path anchored at ``dir_fd``."""
    try:
        entry = os.stat(path, dir_fd=dir_fd, follow_symlinks=False)
    except FileNotFoundError:
        return False
    if stat.S_ISLNK(entry.st_mode):
        return False
    mode = stat.S_IMODE(entry.st_mode)
    repaired_mode = mode | stat.S_IRWXU
    if repaired_mode == mode:
        return False
    os.chmod(
        path,
        repaired_mode,
        dir_fd=dir_fd,
        follow_symlinks=False,
    )
    return True


def _runtime_tmp_reap_onexc(
    lease: Path,
    namespace: Path,
    namespace_fd: int,
    repairs: set[Path],
):
    """Build an ``rmtree`` repair callback confined to one verified lease."""

    def repair(_func: Any, raw_path: str | os.PathLike[str], exc: BaseException) -> None:
        if not isinstance(exc, PermissionError):
            raise exc
        path = Path(raw_path)
        try:
            candidate = path.relative_to(namespace) if path.is_absolute() else path
            candidate.relative_to(lease.name)
        except ValueError:
            raise exc from None
        if _grant_owner_rwx_at(candidate, dir_fd=namespace_fd):
            repairs.add(candidate)
        if _grant_owner_rwx_at(candidate.parent, dir_fd=namespace_fd):
            repairs.add(candidate.parent)

    return repair


def _remove_runtime_tmp_lease(lease: Path, namespace: Path) -> None:
    """Delete one verified lease, repairing restrictive owned entries first."""
    if not getattr(shutil.rmtree, "avoids_symlink_attacks", False):
        raise RuntimeError("platform rmtree lacks symlink-attack protection")
    if not hasattr(os, "O_NOFOLLOW"):
        raise RuntimeError("platform lacks O_NOFOLLOW for runtime tmp cleanup")
    open_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    open_flags |= os.O_NOFOLLOW
    last_error: OSError | None = None
    # ``shutil.rmtree`` calls onexc but cannot resume an ``os.open`` that
    # failed while descending into a mode-000 directory. Re-run the complete,
    # fd-relative walk after every actual permission repair: a tree can have
    # any number of nested restricted directories, so a fixed retry count
    # abandons valid entries below the next barrier.
    while os.path.lexists(lease):
        repairs: set[Path] = set()
        namespace_fd = os.open(namespace, open_flags)
        try:
            shutil.rmtree(
                lease.name,
                dir_fd=namespace_fd,
                onexc=_runtime_tmp_reap_onexc(lease, namespace, namespace_fd, repairs),
            )
        except FileNotFoundError:
            return
        except OSError as exc:
            last_error = exc
        finally:
            os.close(namespace_fd)
        if not os.path.lexists(lease):
            return
        if not repairs:
            break
    # A lease already gone at entry (e.g. a concurrent sweep won the race) is
    # success, not a survived-cleanup failure — the loop guard never ran rmtree,
    # so nothing above could return early on its behalf.
    if not os.path.lexists(lease):
        return
    if last_error is not None:
        raise OSError(
            last_error.errno,
            f"runtime tmp lease survived hardened cleanup: {lease}: {last_error.strerror or last_error}",
            last_error.filename or str(lease),
        )
    raise OSError(f"runtime tmp lease survived hardened cleanup: {lease}")


def _build_runtime_tmp_legacy_stem_index() -> dict[str, str]:
    """Map lease names to task-record stems without opening any JSON."""
    index: dict[str, str] = {}
    try:
        state_files = tuple(tasks_dir().glob("*.json")) if tasks_dir().is_dir() else ()
    except OSError:
        return index
    for state_path in state_files:
        if state_path.name.endswith(".tmp") or ".tmp." in state_path.name:
            continue
        stem = state_path.stem
        index[_runtime_tmp_lease_name(stem)] = stem
    return index


def _read_runtime_tmp_state_for_legacy_lease(
    lease_name: str,
    *,
    legacy_stem_index: dict[str, str],
) -> dict[str, Any] | None:
    """Resolve one marker-less lease, falling back to a bounded record scan."""
    stem = legacy_stem_index.get(lease_name)
    if stem is not None:
        return _read_state_json(tasks_dir() / f"{stem}.json")
    try:
        state_files = tuple(tasks_dir().glob("*.json")) if tasks_dir().is_dir() else ()
    except OSError:
        return None
    for state_path in state_files:
        if state_path.name.endswith(".tmp") or ".tmp." in state_path.name:
            continue
        state = _read_state_json(state_path)
        if not isinstance(state, dict):
            continue
        task_id = state.get("task_id")
        if isinstance(task_id, str) and _runtime_tmp_lease_name(task_id) == lease_name:
            return state
    return None


def _runtime_tmp_state_for_lease(
    lease_name: str,
    lease_root: Path,
    *,
    legacy_stem_index: dict[str, str] | None,
) -> dict[str, Any] | None:
    """Find the task state that owns a runtime-lease directory."""
    task_id = _read_runtime_tmp_task_id_marker(lease_root)
    if task_id is not None:
        return _read_state_json(_state_path(task_id))
    if legacy_stem_index is None:
        return None
    return _read_runtime_tmp_state_for_legacy_lease(
        lease_name,
        legacy_stem_index=legacy_stem_index,
    )


def _runtime_tmp_state_has_live_pid(state: dict[str, Any]) -> bool:
    """Treat a valid live recorded PID as an active lease regardless of status."""
    pid = state.get("pid")
    if isinstance(pid, bool):
        return False
    try:
        return isinstance(pid, (int, str)) and int(pid) > 0 and _pid_alive(int(pid))
    except (TypeError, ValueError):
        return False


def _scratch_scan_roots() -> list[Path]:
    """Return reaper scan roots, or raise ``ScratchScanRootError`` here.

    A misconfigured ``LU_SCRATCH_SCAN_ROOT`` fails at this dispatch boundary.
    The error names the variable and the reason, includes no filesystem path,
    and is not chained to the resolver's traceback.
    """
    try:
        return scratch_scan_roots()
    except ScratchScanRootError as exc:
        raise ScratchScanRootError(exc.reason) from None


def _preserve_runtime_tmp_held_work(
    lease: Path,
    record: dict[str, Any] | None,
    response: str | None = None,
) -> dict[str, Any]:
    """Publish held-work retrieval metadata before any runtime lease deletion."""
    from scripts.fleet import runtime_held_work

    if record is None:
        return {}
    if response is None:
        task_id = record.get("task_id")
        response = saved_task_response(record, _state_path_no_create(task_id) if isinstance(task_id, str) else None)
        if response is None and (record.get("result_file") or record.get("response_chars")):
            raise runtime_held_work.HeldWorkPreservationError()
    try:
        bound_root = record.get("runtime_tmp_root")
        if bound_root and Path(bound_root).absolute() != lease.absolute():
            raise runtime_held_work.HeldWorkPreservationError()
        receipt = runtime_held_work.preserve(
            lease, primary=_main_checkout_root(_REPO_ROOT), record=record, response=response or ""
        )
        if receipt is None:
            return {}
        updates = {"preserved_held_work": receipt}
        path = _state_path_no_create(record["task_id"])
        with task_state_lock(path):
            current = _read_state_json(path)
            if current is None or any(current.get(key) != record.get(key) for key in ("task_id", "run_nonce")):
                raise runtime_held_work.HeldWorkPreservationError()
            current.update(updates)
            _write_record_unlocked(path, current)
        record.update(updates)
        return updates
    except (OSError, ValueError, TypeError):
        raise runtime_held_work.HeldWorkPreservationError() from None


def _sweep_runtime_tmp_orphans(
    *,
    now: float | None = None,
) -> dict[str, Any]:
    """Reap terminal or clearly abandoned task leases before a new dispatch.

    A state-backed lease is removed only once its task is terminal and no
    recorded process is alive. A state-less lease must be older than seven
    days. Symlinks and malformed entries are skipped rather than followed.
    """
    error_details: list[tuple[str, int | None, str]] = []
    result: dict[str, Any] = {
        "leases_reaped": 0,
        "bytes_freed": 0,
        "errors": 0,
        "error_details": error_details,
    }
    # #7164: the lease namespace moved to the disk-backed fleet scratch root;
    # sweep every known scratch base (new root + legacy tmpfs $TMPDIR) so old
    # namespaces still drain.
    namespaces: list[Path] = []
    seen_namespaces: set[Path] = set()
    for scratch_base in _scratch_scan_roots():
        namespace = scratch_base / "learn-ukrainian"
        if namespace in seen_namespaces:
            continue
        seen_namespaces.add(namespace)
        namespaces.append(namespace)
    cutoff = (time.time() if now is None else now) - _RUNTIME_TMP_ORPHAN_MAX_AGE_S
    legacy_stem_index: dict[str, str] | None = None

    for namespace in namespaces:
        try:
            namespace_stat = namespace.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            result["errors"] += 1
            error_details.append((namespace.name, exc.errno, str(exc.filename or namespace)))
            continue
        if stat.S_ISLNK(namespace_stat.st_mode) or not stat.S_ISDIR(namespace_stat.st_mode):
            result["errors"] += 1
            continue

        try:
            candidates = tuple(namespace.iterdir())
        except OSError as exc:
            result["errors"] += 1
            error_details.append((namespace.name, exc.errno, str(exc.filename or namespace)))
            continue
        for lease in candidates:
            try:
                lease_stat = lease.lstat()
            except FileNotFoundError:
                continue
            except OSError as exc:
                result["errors"] += 1
                if len(error_details) < _RUNTIME_TMP_SWEEP_ERROR_DETAILS_LIMIT:
                    error_details.append((lease.name, exc.errno, str(exc.filename or lease)))
                continue
            if stat.S_ISLNK(lease_stat.st_mode) or not stat.S_ISDIR(lease_stat.st_mode):
                continue

            had_marker = _read_runtime_tmp_task_id_marker(lease) is not None
            if not had_marker and legacy_stem_index is None:
                legacy_stem_index = _build_runtime_tmp_legacy_stem_index()
            state = _runtime_tmp_state_for_lease(
                lease.name,
                lease,
                legacy_stem_index=legacy_stem_index,
            )
            if state is not None:
                status = state.get("status")
                if status not in _RUNTIME_TMP_TERMINAL_STATUSES or _runtime_tmp_state_has_live_pid(state):
                    if not had_marker:
                        resolved_task_id = state.get("task_id")
                        if isinstance(resolved_task_id, str):
                            with contextlib.suppress(OSError):
                                _write_runtime_tmp_task_id_marker(
                                    lease,
                                    resolved_task_id,
                                    no_clobber=True,
                                )
                    continue
            elif lease_stat.st_mtime >= cutoff:
                continue

            try:
                _preserve_runtime_tmp_held_work(lease, state)
                bytes_freed = _runtime_tmp_lease_bytes(lease)
                _remove_runtime_tmp_lease(lease, namespace)
            except (OSError, ValueError) as exc:
                result["errors"] += 1
                if len(error_details) < _RUNTIME_TMP_SWEEP_ERROR_DETAILS_LIMIT:
                    error_details.append(
                        (
                            lease.name,
                            getattr(exc, "errno", None),
                            getattr(exc, "code", None) or str(getattr(exc, "filename", None) or lease),
                        )
                    )
                continue
            result["leases_reaped"] += 1
            result["bytes_freed"] += bytes_freed
    return result


def _reap_runtime_tmp_lease(
    lease_root: Path | str | None,
    namespace_root: Path | str | None,
    *,
    task_record: dict[str, Any] | None = None,
    response: str | None = None,
) -> dict[str, Any]:
    """Best-effort, fd-relative deletion of one task-scoped runtime lease.

    This is intentionally stricter than a generic ``rm -rf``. It only removes
    a non-symlink direct child of the dispatcher-created namespace and uses
    ``shutil.rmtree``'s fd-based implementation so a symlink swap cannot turn
    cleanup into a deletion outside the lease. A filesystem or validation
    failure is recorded on ``tmp_reap_error`` and does not fail the worker.
    Cited held work is copied and its retrieval manifest published before
    deletion; preservation failure refuses deletion with a typed reason.
    ``ScratchScanRootError`` propagates: a misconfigured scan root is not
    telemetry, and this function raises it before it deletes the lease.
    """
    result: dict[str, Any] = {
        "tmp_bytes_freed": 0,
        "tmp_reap_error": None,
    }
    worker_base_root: Path | None = None
    resolved_lease: Path | None = None
    try:
        if lease_root is None or namespace_root is None:
            raise ValueError("runtime tmp lease metadata is missing")
        lease = Path(lease_root)
        namespace = Path(namespace_root)
        namespace_stat = namespace.lstat()
        lease_stat = lease.lstat()
        if stat.S_ISLNK(namespace_stat.st_mode):
            raise ValueError("runtime tmp namespace is a symlink")
        if stat.S_ISLNK(lease_stat.st_mode):
            raise ValueError("runtime tmp lease is a symlink")
        if not stat.S_ISDIR(namespace_stat.st_mode):
            raise ValueError("runtime tmp namespace is not a directory")
        if not stat.S_ISDIR(lease_stat.st_mode):
            raise ValueError("runtime tmp lease is not a directory")

        resolved_namespace = namespace.resolve(strict=True)
        resolved_lease = lease.resolve(strict=True)
        resolved_tmp_root = Path(tempfile.gettempdir()).resolve(strict=True)
        if resolved_tmp_root == resolved_lease:
            # The worker deliberately points TMPDIR at its lease. In that one
            # process context, use the pre-override root recorded by the
            # dispatcher; parent cleanup still validates against its live
            # tempfile root, so a stale inherited base cannot bless a child.
            runtime_tmp_base_root = os.environ.get("LU_RUNTIME_TMP_BASE_ROOT")
            if not runtime_tmp_base_root:
                raise ValueError("runtime tmp worker is missing its base root")
            worker_base_root = Path(runtime_tmp_base_root).resolve(strict=True)
            accepted_parents = {worker_base_root}
        else:
            # #7164: leases live under the disk-backed fleet scratch root; the
            # legacy tmpfs $TMPDIR namespace stays accepted so pre-change
            # leases can still be reaped. Fallback scratch root is also accepted.
            accepted_parents = {root.resolve() for root in _scratch_scan_roots()}
            with contextlib.suppress(OSError):
                accepted_parents.add(resolve_scratch_root().resolve())
            with contextlib.suppress(OSError):
                accepted_parents.add(fallback_scratch_root().resolve())
            with contextlib.suppress(OSError):
                accepted_parents.add(DEFAULT_SCRATCH_ROOT.resolve())
            accepted_parents.add(resolved_tmp_root)
        if resolved_namespace.parent not in accepted_parents:
            raise ValueError(
                "resolved runtime tmp namespace is not directly under an approved scratch root",
            )
        if resolved_lease.parent != resolved_namespace:
            raise ValueError(
                "resolved runtime tmp lease is not under $TMPDIR/learn-ukrainian",
            )
        if resolved_namespace.name != "learn-ukrainian":
            raise ValueError("runtime tmp namespace has the wrong name")
        if not getattr(shutil.rmtree, "avoids_symlink_attacks", False):
            raise RuntimeError("platform rmtree lacks symlink-attack protection")

        if task_record is None:
            task_record = _runtime_tmp_state_for_lease(
                lease.name,
                lease,
                legacy_stem_index=_build_runtime_tmp_legacy_stem_index()
                if _read_runtime_tmp_task_id_marker(lease) is None
                else None,
            )
        result.update(_preserve_runtime_tmp_held_work(lease, task_record, response))
        bytes_freed = _runtime_tmp_lease_bytes(lease)
        _remove_runtime_tmp_lease(lease, namespace)
        if os.path.lexists(lease):
            raise OSError(f"runtime tmp lease survived hardened cleanup: {lease}")
        result["tmp_bytes_freed"] = bytes_freed
    except ScratchScanRootError:
        raise
    except Exception as exc:
        result["tmp_reap_error"] = getattr(exc, "code", None) or (f"{type(exc).__name__}: {exc}")[:500]
    if worker_base_root is not None and resolved_lease is not None and not os.path.lexists(resolved_lease):
        _rebind_reaped_process_tmp(resolved_lease, worker_base_root)
    return result


def _rebind_reaped_process_tmp(lease: Path, base_root: Path) -> None:
    """Move this process's temporary-file root off its reaped runtime lease (#9878).

    A worker process runs with ``TMPDIR`` at its lease, and ``tempfile`` caches
    that root per process. The worker reaps the lease as soon as its agent
    exits, yet the finalize steps after the reap still create temporary files:
    the Kimi content check's and auto-finalize's scratch index, and the hooks of
    the commit and push they spawn. Each found its root gone (FileNotFoundError).
    Those steps now use the base root the lease lived under, which outlives
    them; the runtime lease variable naming the removed directory is dropped.
    """

    def _in_lease(value: str | None) -> bool:
        if not value:
            return False
        try:
            return Path(value).resolve().is_relative_to(lease)
        except (OSError, RuntimeError, ValueError):
            return False

    if _in_lease(tempfile.tempdir):
        tempfile.tempdir = str(base_root)
    if _in_lease(os.environ.get("TMPDIR")):
        os.environ["TMPDIR"] = str(base_root)
    if _in_lease(os.environ.get("LU_RUNTIME_TMP_ROOT")):
        os.environ.pop("LU_RUNTIME_TMP_ROOT", None)


def _derive_worktree_branch(agent: str, task_id: str) -> str:
    """Derive a git-safe branch name for a delegated worktree.

    Normalizes task_id first so ``codex-1472-foo`` produces
    ``codex/1472-foo`` rather than ``codex/codex-1472-foo``.
    """
    normalized = _normalize_task_id(agent, task_id)
    safe_task = re.sub(r"[^A-Za-z0-9._/-]+", "-", normalized).strip("./-")
    safe_task = re.sub(r"/{2,}", "/", safe_task)
    if not safe_task:
        safe_task = "task"
    return f"{agent}/{safe_task}"


def _auto_worktree_path(agent: str, task_id: str, *, repo_root: Path | None = None) -> Path:
    """Default worktree path for a fresh dispatch: ``.worktrees/dispatch/{agent}/{task}/``.

    Defaults under :data:`_REPO_ROOT`. With ``--repo`` (#672 P2.1) the path is
    rooted at the allowlisted sibling checkout instead. A bare sibling cwd
    still cannot retarget this path — use ``--repo`` or the manual ``--cwd``
    flow (:func:`_resolve_cross_repo_binding_error`).
    """
    root = Path(repo_root) if repo_root is not None else _REPO_ROOT
    return worktree_paths.automatic_worktree_path(agent, task_id, repo_root=root)


# ``git worktree add`` bounds, configurable in scripts/config.py (#8663). Tests
# shrink them here instead of generating host load.
_WORKTREE_ADD_TIMEOUT_S: float = DELEGATE_WORKTREE_ADD_TIMEOUT_S
_WORKTREE_ADD_STALL_S: float = DELEGATE_WORKTREE_ADD_STALL_S
_WORKTREE_ADD_MAX_S: float = DELEGATE_WORKTREE_ADD_MAX_S
# How often a slow add's checkout is re-counted once the base window has passed.
_WORKTREE_ADD_POLL_S: float = 5.0
# How long a stopped add gets to run git's own cleanup after SIGTERM, and to
# exit after SIGKILL.
_WORKTREE_ADD_STOP_GRACE_S: float = 30.0

_GIT_INITIALIZING_LOCK_REASON = worktree_prep.INITIALIZING_LOCK_REASON


class WorktreeAddFailed(RuntimeError):
    """``git worktree add`` failed or timed out before any worker was spawned (#8663).

    ``cleanup`` records what dispatch found and did after the add; the failed
    task record carries it as ``worktree_prep_cleanup``. ``prep`` is this
    call's path reservation, stored as ``worktree_prep``, or ``None`` when the
    path could not be reserved.
    """

    def __init__(self, message: str, *, cleanup: dict[str, Any], prep: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.cleanup = cleanup
        self.prep = prep


class WorktreeAddTimeout(subprocess.TimeoutExpired):
    """A stopped ``git worktree add``; ``git_exited`` says whether its exit was confirmed."""

    def __init__(self, cmd: list[str], timeout: float, *, git_exited: bool) -> None:
        super().__init__(cmd, timeout)
        self.git_exited = git_exited


def _checkout_entry_count(path: Path) -> int:
    """Count the files and directories under ``path``, skipping ``.git``.

    The progress signal for a slow ``git worktree add``: a checkout that is
    still being written keeps gaining entries. Entries that vanish mid-walk
    are skipped; a missing ``path`` counts as zero.
    """
    count = 0
    pending = [path]
    while pending:
        try:
            with os.scandir(pending.pop()) as entries:
                for entry in entries:
                    if entry.name == ".git":
                        continue
                    count += 1
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            pending.append(Path(entry.path))
                    except OSError:
                        continue
        except OSError:
            continue
    return count


def _stop_worktree_add(proc: subprocess.Popen[str]) -> bool:
    """Stop a slow ``git worktree add`` and its checkout child.

    SIGTERM goes to the whole process group first, and git gets
    :data:`_WORKTREE_ADD_STOP_GRACE_S` to run its own signal cleanup, which
    deletes the worktree directory and admin directory it was building.
    SIGKILL follows only after that grace. Returns whether the add was
    confirmed exited; a process that outlives even SIGKILL (for example one
    stuck in uninterruptible I/O) may still write, so nothing may be touched
    while this is False.
    """
    for sig in (signal.SIGTERM, signal.SIGKILL):
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(proc.pid, sig)
        try:
            proc.communicate(timeout=_WORKTREE_ADD_STOP_GRACE_S)
            return True
        except subprocess.TimeoutExpired:
            continue
    return False


def _run_worktree_add(
    add_command: list[str],
    *,
    cwd: Path,
    worktree_path: Path,
    env: dict[str, str] | None = None,
    on_spawn: Callable[[int], None] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run ``git worktree add`` with a progress-aware bound (#8663).

    The add always gets :data:`_WORKTREE_ADD_TIMEOUT_S`. After that it keeps
    running while the checkout at ``worktree_path`` is still gaining entries,
    is stopped once it gains none for :data:`_WORKTREE_ADD_STALL_S`, and is
    never allowed past :data:`_WORKTREE_ADD_MAX_S`. A stopped add (see
    :func:`_stop_worktree_add`) raises :class:`WorktreeAddTimeout`. The add
    runs in the C locale so the lock reason git holds during it is the
    literal ``initializing``. ``on_spawn`` receives git's pid as soon as it
    is spawned.
    """
    add_env = dict(os.environ if env is None else env)
    add_env["LC_ALL"] = "C"
    add_env.pop("LANGUAGE", None)
    proc = subprocess.Popen(
        add_command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=add_env,
        # Its own process group, so a stop also reaches the checkout child.
        start_new_session=True,
    )
    started = time.monotonic()
    if on_spawn is not None:
        on_spawn(proc.pid)
    poll_s = max(min(_WORKTREE_ADD_POLL_S, _WORKTREE_ADD_STALL_S), 0.01)
    last_count: int | None = None
    last_growth = started
    while True:
        elapsed = time.monotonic() - started
        if elapsed < _WORKTREE_ADD_TIMEOUT_S:
            wait_s = min(_WORKTREE_ADD_TIMEOUT_S, _WORKTREE_ADD_MAX_S) - elapsed
        else:
            wait_s = min(poll_s, _WORKTREE_ADD_MAX_S - elapsed)
        try:
            stdout, stderr = proc.communicate(timeout=max(wait_s, 0.01))
        except subprocess.TimeoutExpired:
            pass
        else:
            return subprocess.CompletedProcess(add_command, proc.returncode, stdout, stderr)
        now = time.monotonic()
        if now - started >= _WORKTREE_ADD_MAX_S:
            break
        if now - started < _WORKTREE_ADD_TIMEOUT_S:
            continue
        count = _checkout_entry_count(worktree_path)
        if last_count is None or count > last_count:
            last_count = count
            last_growth = now
        elif now - last_growth >= _WORKTREE_ADD_STALL_S:
            break
    git_exited = _stop_worktree_add(proc)
    raise WorktreeAddTimeout(add_command, time.monotonic() - started, git_exited=git_exited)


def _worktree_registration(repo_root: Path, worktree_path: Path) -> tuple[bool, str | None] | None:
    """Return whether ``repo_root`` registers ``worktree_path`` and its lock reason.

    The lock reason is ``None`` for an unlocked worktree and ``""`` for a lock
    without a reason. Returns ``None`` when git cannot list its worktrees.
    """
    try:
        proc = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=DEFAULT_GIT_TIMEOUT_S,
            env=_sanitized_git_env(),
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    target = worktree_path.resolve()
    registered = False
    lock_reason: str | None = None
    for line in (proc.stdout or "").splitlines():
        if line.startswith("worktree "):
            if registered:
                break
            registered = Path(line.removeprefix("worktree ")).resolve() == target
            lock_reason = None
        elif registered and (line == "locked" or line.startswith("locked ")):
            lock_reason = line.removeprefix("locked").strip()
    return registered, lock_reason if registered else None


def _is_own_worktree_prep_record(state: dict[str, Any], run_nonce: str) -> bool:
    """True when ``state`` is this run's pre-``git worktree add`` reservation record."""
    prep = state.get("worktree_prep")
    return (
        state.get("run_nonce") == run_nonce
        and state.get("pid", False) is None
        and isinstance(prep, dict)
        and prep.get("run_nonce") == run_nonce
    )


def _is_own_admission_hold(state: dict[str, Any], run_nonce: str) -> bool:
    """True when ``state`` is this run's admission hold (#8717), without a worktree reservation."""
    return (
        state.get("run_nonce") == run_nonce
        and "worktree_prep" not in state
        and dispatch_admission.is_admission_hold_record(state)
    )


def _is_own_provisional_record(state: dict[str, Any], run_nonce: str) -> bool:
    """True for this run's pid-less admission hold or worktree reservation record."""
    return _is_own_worktree_prep_record(state, run_nonce) or _is_own_admission_hold(state, run_nonce)


# Fields an admission hold carries into the worktree reservation record that
# replaces it, so the reservation keeps the admitted slot (#8717).
_ADMISSION_HOLD_FIELDS = ("mode", "admission", dispatch_admission.ADMISSION_HOLD_KEY)


def _publish_admission_hold(task_id: str, run_nonce: str, *, mode: str, admission: dict[str, Any]) -> None:
    """Publish the ``spawning`` record that holds this run's admitted write slot (#8717).

    Dispatch calls this under the admission lock, before any worktree side
    effect, so a refusal leaves nothing behind. The hold names this
    dispatcher, so admission counts it for as long as the dispatcher lives
    (however long its worktree add takes) and heals it once the dispatcher is
    provably gone. The worktree reservation and the full task record replace
    it in place. Raises ``RuntimeError`` rather than overwrite a live record
    of another run.
    """
    state_path = _state_path(task_id)
    with task_state_lock(state_path):
        existing = _read_state_json(state_path)
        if (
            existing is not None
            and existing.get("status") in ("running", "spawning")
            and not _is_own_provisional_record(existing, run_nonce)
        ):
            raise RuntimeError(f"task record for {task_id!r} is {existing.get('status')}; refusing to overwrite it")
        hold = dispatch_admission.new_admission_hold(run_nonce)
        _write_record_unlocked(
            state_path,
            {
                "task_id": task_id,
                "run_nonce": run_nonce,
                "status": "spawning",
                "pid": None,
                "mode": mode,
                "started_at": hold["admitted_at"],
                "finished_at": None,
                "admission": admission,
                dispatch_admission.ADMISSION_HOLD_KEY: hold,
            },
        )


def _release_admission_hold(task_id: str, run_nonce: str) -> None:
    """Drop this run's admission hold when dispatch stops before publishing any other record.

    A no-op once the hold was replaced by the full task record, a failure
    record, or a worktree reservation (kept as the reaper's evidence).
    """
    state_path = _state_path(task_id)
    with contextlib.suppress(OSError), task_state_lock(state_path):
        existing = _read_state_json(state_path)
        if existing is not None and _is_own_admission_hold(existing, run_nonce):
            state_path.unlink(missing_ok=True)


def _publish_worktree_prep(task_id: str, run_nonce: str, prep: dict[str, Any]) -> None:
    """Record this run's path reservation in its task record before git starts (#8663).

    The record says ``spawning`` with ``pid: null`` (dispatch is preparing,
    no worker exists yet), so claim scans treat the path as taken while the
    add runs, and a dispatcher that dies meanwhile is detectable from the
    recorded owner. It replaces this run's admission hold and keeps its
    fields, so the admitted slot stays held while the add runs (#8717). The
    terminal record a failed add later writes keeps ``worktree_prep`` as
    evidence for the reaper's report. Raises ``RuntimeError`` rather than
    overwrite a live record of another run.
    """
    state_path = _state_path(task_id)
    with task_state_lock(state_path):
        existing = _read_state_json(state_path)
        if (
            existing is not None
            and existing.get("status") in ("running", "spawning")
            and not _is_own_provisional_record(existing, run_nonce)
        ):
            raise RuntimeError(f"task record for {task_id!r} is {existing.get('status')}; refusing to overwrite it")
        held = (
            {key: existing[key] for key in _ADMISSION_HOLD_FIELDS if key in existing}
            if existing is not None and _is_own_provisional_record(existing, run_nonce)
            else {}
        )
        _write_record_unlocked(
            state_path,
            {
                "task_id": task_id,
                "run_nonce": run_nonce,
                "status": "spawning",
                "pid": None,
                **held,
                "cwd": prep["path"],
                "worktree_path": prep["path"],
                "started_at": prep["reserved_at"],
                "finished_at": None,
                "worktree_prep": prep,
            },
        )


def _update_worktree_prep(task_id: str, run_nonce: str, prep: dict[str, Any]) -> None:
    """Rewrite ``worktree_prep`` in this run's provisional record; best effort."""
    state_path = _state_path(task_id)
    with contextlib.suppress(OSError), task_state_lock(state_path):
        existing = _read_state_json(state_path)
        if existing is not None and _is_own_worktree_prep_record(existing, run_nonce):
            existing["worktree_prep"] = dict(prep)
            _write_record_unlocked(state_path, existing)


def _retire_worktree_prep(task_id: str, run_nonce: str) -> None:
    """Drop this run's reservation record once its ``git worktree add`` succeeded.

    Dispatch publishes the full task record next; until then no record
    claims the finished worktree, exactly as before reservations existed.
    A reservation that replaced an admission hold reverts to that hold, so
    the admitted slot stays held until the full record replaces it (#8717).
    """
    state_path = _state_path(task_id)
    with contextlib.suppress(OSError), task_state_lock(state_path):
        existing = _read_state_json(state_path)
        if existing is None or not _is_own_worktree_prep_record(existing, run_nonce):
            return
        hold = existing.get(dispatch_admission.ADMISSION_HOLD_KEY)
        if not isinstance(hold, dict):
            state_path.unlink(missing_ok=True)
            return
        _write_record_unlocked(
            state_path,
            {
                "task_id": task_id,
                "run_nonce": run_nonce,
                "status": "spawning",
                "pid": None,
                **{key: existing[key] for key in _ADMISSION_HOLD_FIELDS if key in existing},
                "started_at": hold.get("admitted_at"),
                "finished_at": None,
            },
        )


def _leave_reservation(worktree_path: Path, prep: dict[str, Any]) -> dict[str, Any]:
    """Report the reserved directory a failed add left unregistered; never remove it (#8663).

    Git 2.53 can write another add's admin registration while this path is
    still empty and before its ``.git`` exists, so no ``rmdir`` of the
    reservation is safe. The directory stays as it is, empty or not, and
    ``reserved_dir_left`` is recorded in ``prep`` and the returned report.
    An empty, unregistered one is swept later by the reaper's existing
    dispatch-husk rule (``reap_worktrees._reap_dispatch_husks``).
    """
    left = os.path.lexists(worktree_path)
    prep["reserved_dir_left"] = left
    report: dict[str, Any] = {"error": None, "reserved_dir_left": left}
    if not left:
        return {**report, "action": "none", "reason": "git left no worktree behind"}
    if not worktree_prep.identity_matches(prep, worktree_path):
        reason = "path holds a directory this run did not reserve (device/inode differ); never removed"
    else:
        reason = "git registered no worktree; reserved directory left in place, never removed automatically"
    return {**report, "action": "skipped", "reason": reason}


def _settle_failed_worktree_add(
    worktree_path: Path,
    *,
    repo_root: Path,
    git_exited: bool,
    prep: dict[str, Any],
) -> dict[str, Any]:
    """Record what this run's failed ``git worktree add`` left; remove nothing (#8663).

    A stopped add got SIGTERM first, so git normally deleted its own partial
    worktree and admin directory. Whatever remains stays: a reserved
    directory git left unregistered is reported with ``reserved_dir_left``
    (see :func:`_leave_reservation`). A worktree git left
    registered is never removed, unlocked or pruned here: it is reported, as
    :data:`worktree_prep.LEFTOVER_KIND` when git still holds its
    ``initializing`` lock, with a removal command to run only after
    verification. Returns the record stored as ``worktree_prep_cleanup``;
    never raises.
    """
    prep["reserved_dir_left"] = os.path.lexists(worktree_path)
    base: dict[str, Any] = {
        "path": str(worktree_path),
        "branch_ref_kept": True,
        "reserved_dir_left": prep["reserved_dir_left"],
    }
    if not git_exited:
        return {
            **base,
            "action": "skipped",
            "reason": "git worktree add not confirmed exited after SIGKILL; nothing touched",
            "error": None,
            "git_exited": False,
        }
    registration = _worktree_registration(repo_root, worktree_path)
    if registration is None:
        return {**base, "action": "error", "reason": "could not list git worktrees; nothing touched", "error": None}
    registered, lock_reason = registration
    if not registered:
        return {**base, **_leave_reservation(worktree_path, prep)}
    report = {
        **base,
        "action": "skipped",
        "error": None,
        "lock_reason": lock_reason,
        "command": worktree_prep.verify_first_command(repo_root, worktree_path),
    }
    if lock_reason == _GIT_INITIALIZING_LOCK_REASON:
        return {
            **report,
            "needs_attention": worktree_prep.LEFTOVER_KIND,
            "reason": "git left a registered worktree locked 'initializing'; never removed automatically",
        }
    return {**report, "reason": f"git left a registered worktree (lock={lock_reason!r}); never removed automatically"}


def _resolve_commit(repo_root: Path, ref: str, env: dict[str, str] | None) -> str | None:
    """Resolve ``ref`` to a commit SHA in ``repo_root``, or ``None``."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=DEFAULT_GIT_TIMEOUT_S,
            env=_sanitized_git_env() if env is None else env,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    sha = (proc.stdout or "").strip()
    return sha if proc.returncode == 0 and sha else None


def _add_reserved_worktree(
    add_command: list[str],
    *,
    repo_root: Path,
    worktree_path: Path,
    task_id: str,
    run_nonce: str | None = None,
    env: dict[str, str] | None = None,
    base_sha: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run this dispatch's ``git worktree add`` into a freshly reserved path (#8663).

    The path is first reserved with ``mkdir``, which fails when anything is
    already there (git accepts the empty directory). A path that cannot be
    reserved is never passed to git and never removed. ``base_sha`` is the
    commit the add checks out; without it, the last element of
    ``add_command`` is resolved.

    The reservation (see :mod:`scripts.orchestration.worktree_prep`) records
    the reserved directory's device and inode, the base commit, this
    dispatcher's pid and start time, and git's as soon as it is spawned. With
    ``run_nonce``, it is published as ``worktree_prep`` in the task record
    before git starts.

    Returns the completed process on success. On a timeout or a non-zero
    exit, reports what the add left (see :func:`_settle_failed_worktree_add`),
    removing nothing, and raises :class:`WorktreeAddFailed`.
    """
    try:
        os.mkdir(worktree_path)
    except OSError as exc:
        exists = isinstance(exc, FileExistsError)
        raise WorktreeAddFailed(
            f"could not reserve worktree path {worktree_path}: {type(exc).__name__}: {exc}",
            cleanup={
                "path": str(worktree_path),
                "action": "skipped" if exists else "none",
                "reason": "path existed before this dispatch reserved it; never removed"
                if exists
                else "path could not be reserved; git was not run",
                "error": None,
                "branch_ref_kept": True,
            },
        ) from exc
    identity = worktree_prep.directory_identity(worktree_path)
    owner = worktree_prep.process_identity(os.getpid())
    prep: dict[str, Any] = {
        "path": str(worktree_path),
        "run_nonce": run_nonce,
        "reserved_by_mkdir": True,
        "reserved_at": datetime.now(UTC).isoformat(),
        "dir_dev": identity[0] if identity else None,
        "dir_ino": identity[1] if identity else None,
        "base_sha": base_sha or _resolve_commit(repo_root, add_command[-1], env),
        "git_pid": None,
        "git_start": None,
        "owner_pid": owner["pid"],
        "owner_start": owner["start"],
    }

    def record_git(pid: int) -> None:
        git_identity = worktree_prep.process_identity(pid)
        prep["git_pid"] = git_identity["pid"]
        prep["git_start"] = git_identity["start"]
        if run_nonce is not None:
            _update_worktree_prep(task_id, run_nonce, prep)

    if run_nonce is not None:
        try:
            _publish_worktree_prep(task_id, run_nonce, prep)
        except (OSError, RuntimeError) as exc:
            left = _leave_reservation(worktree_path, prep)
            raise WorktreeAddFailed(
                f"could not record the reservation of {worktree_path}: {exc}",
                cleanup={"path": str(worktree_path), **left, "branch_ref_kept": True},
                prep=dict(prep),
            ) from exc
    git_exited = True
    try:
        proc = _run_worktree_add(add_command, cwd=repo_root, worktree_path=worktree_path, env=env, on_spawn=record_git)
    except subprocess.TimeoutExpired as exc:
        # Only a stop that saw git exit proves it can no longer write.
        git_exited = getattr(exc, "git_exited", False)
        message = f"git worktree add timed out after {exc.timeout:.1f}s"
    except OSError as exc:
        message = f"git worktree add could not start: {type(exc).__name__}: {exc}"
    else:
        if proc.returncode == 0:
            if run_nonce is not None:
                _retire_worktree_prep(task_id, run_nonce)
            return proc
        message = (proc.stderr or proc.stdout or "git worktree add failed").strip()
    cleanup = _settle_failed_worktree_add(worktree_path, repo_root=repo_root, git_exited=git_exited, prep=prep)
    if run_nonce is not None:
        _update_worktree_prep(task_id, run_nonce, prep)
    raise WorktreeAddFailed(message, cleanup=cleanup, prep=dict(prep))


def _ensure_sibling_repo_worktree(
    *,
    repo_root: Path,
    agent: str,
    task_id: str,
    raw_path: str | None = None,
    base: str = "main",
    dry_run: bool = False,
    run_nonce: str | None = None,
    detached: bool = False,
    validated_path: Path | None = None,
) -> tuple[Path, str | None, dict[str, Any]]:
    """Create or reuse a layout-A worktree under an allowlisted sibling checkout.

    Public-primary helpers (sparse checkout, data symlinks, mirror-aware
    ``_fetch_base``) stay on :data:`_REPO_ROOT`. Sibling repos get a narrow
    fetch + ``git worktree add`` path so private product/infra trees are not
    forced through public monorepo provisioning (#672 P2.1). ``validated_path``,
    when given, is used as is and never resolved again (#8775).
    """
    root = Path(repo_root).resolve()
    if validated_path is not None:
        worktree_path = validated_path
    elif raw_path is None:
        raise ValueError("a worktree helper needs raw_path or validated_path")
    else:
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = root / path
        worktree_path = path.resolve()
    try:
        worktree_path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"sibling worktree path {worktree_path} is outside target repo {root}") from exc
    worktree_branch = None if detached else _derive_worktree_branch(agent, task_id)
    telemetry: dict[str, Any] = {
        "base_sha": None,
        "rebased": False,
        "layout": "dispatch",
        "reused": False,
        "sparse": None,
        "local_venv": None,
        "repo_root": str(root),
    }
    if worktree_path.exists():
        if detached:
            raise ValueError(f"detached read-only worktree already exists: {worktree_path}; refuse reuse")
        if not worktree_path.is_dir():
            raise ValueError(f"worktree path exists but is not a directory: {worktree_path}")
        _refuse_review_attempt_worktree_reuse(worktree_path)
        telemetry["reused"] = True
        actual_sha = _resolve_sha(worktree_path)
        if actual_sha is None:
            raise RuntimeError(f"could not resolve HEAD for existing worktree {worktree_path}")
        telemetry["base_sha"] = actual_sha
        return worktree_path, worktree_branch, telemetry
    if dry_run:
        raise ValueError(
            f"sibling --repo dry-run found no worktree at {worktree_path}; rerun without --dry-run to create one"
        )
    branch_name = _base_branch_name(base)
    origin_ref = f"origin/{branch_name}"
    try:
        fetch_proc = subprocess.run(
            [
                "git",
                "fetch",
                "origin",
                f"+refs/heads/{branch_name}:refs/remotes/origin/{branch_name}",
            ],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=DEFAULT_GIT_TIMEOUT_S,
            env=_sanitized_git_env(),
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"git fetch timed out after {DEFAULT_GIT_TIMEOUT_S}s for sibling repo {root}") from exc
    if fetch_proc.returncode != 0:
        detail = (fetch_proc.stderr or fetch_proc.stdout or "git fetch failed").strip()
        raise RuntimeError(f"could not fetch {origin_ref} in sibling repo {root}: {detail}")
    if _resolve_sha(root, origin_ref) is None:
        raise RuntimeError(f"{origin_ref} unresolvable in sibling repo {root} after fetch")
    worktree_path.parent.mkdir(parents=True, exist_ok=True)
    add_command = ["git", "worktree", "add"]
    if detached:
        add_command.extend(["--detach", str(worktree_path), origin_ref])
    else:
        add_command.extend(["-b", worktree_branch, str(worktree_path), origin_ref])
    _add_reserved_worktree(
        add_command,
        repo_root=root,
        worktree_path=worktree_path,
        task_id=task_id,
        run_nonce=run_nonce,
        env=_sanitized_git_env(),
    )
    actual_sha = _resolve_sha(worktree_path)
    if actual_sha is None:
        raise RuntimeError(f"could not resolve HEAD for created worktree {worktree_path}")
    telemetry["base_sha"] = actual_sha
    return worktree_path, worktree_branch, telemetry


def _classify_worktree_layout(path: Path | str | None) -> str | None:
    """Return "dispatch" (new subtree), "flat" (old), "external", or None."""
    if path is None:
        return None
    p = Path(path)
    try:
        rel = p.resolve().relative_to(_REPO_ROOT)
    except ValueError:
        return "external"
    parts = rel.parts
    if parts and parts[0] == ".worktrees":
        if len(parts) >= 4 and parts[1] == "dispatch":
            return "dispatch"
        if len(parts) >= 2:
            return "flat"
    return None


# ---------------------------------------------------------------------------
# Write-capable-mode worktree guard (#4445)
# ---------------------------------------------------------------------------
#
# ``workspace-write`` and ``danger`` let the delegated worker mutate files. Both
# MUST run inside an isolated dispatch worktree so those writes never dirty the
# protected primary checkout — the operator contract must not rely on a model
# *remembering* the worktree rule. ``read-only`` dispatches are exempt from
# this write guard; they get a detached worktree by default or an explicit cwd.

_WRITE_CAPABLE_MODES = frozenset({"workspace-write", "danger"})
# This is deliberately a narrow, directive-only check.  It catches briefs
# whose first-order outcome is a repository mutation without treating an
# ordinary read-only discussion of a proposed change as write intent.
_WRITE_SHAPED_PROMPT_RE = re.compile(
    r"""(?imx)
    ^\s*(?P<prefix>[-*+]\s+|\d+[.)]\s+|\#{1,6}\s+)?(?:please\s+)?
    (?:
        (?:implement|fix|add|update|modify|edit|remove|delete|refactor|rename|create|build)\b
        |
        write\s+(?:(?:new|the)\s+)?(?:code|tests?|scripts?|files?|documentation|docs?)\b
    )
    """,
)
_FENCED_BLOCK_RE = re.compile(r"^(`{3,}|~{3,}).*?^\1", re.DOTALL | re.MULTILINE)
_BLOCKQUOTE_LINE_RE = re.compile(r"^\s*>.*$", re.MULTILINE)
_HEADING_BOUNDARY_RE = re.compile(r"^\s*\#{1,6}\s+")
_LIST_BOUNDARY_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)")
_THEMATIC_BREAK_RE = re.compile(r"^\s*[-*_]{3,}\s*$")
_NO_DELIVERABLE_STATUS = "no_deliverable"
# A clean read-only checkout holds no uncommitted deliverable. Every terminal
# status the worker can persist is enough to drop it (#8536). Write-capable
# modes stay on the danger rule: only a clean successful ``done``.
_READ_ONLY_SETTLE_REAP_STATUSES = frozenset(
    {
        "done",
        "failed",
        _NO_DELIVERABLE_STATUS,
        "timeout",
        "rate_limited",
        "cancelled",
        "crashed",
        "needs_finalize",
    }
)
# Explicit unattested classification for Cursor Auto when no concrete model was
# extracted (#6964 / #6953). Never record a bare ``"unknown"`` here.
_CURSOR_UNKNOWN_MODEL = "unattested-harness"
_NON_CONCRETE_MODEL_VALUES = frozenset({"", "auto", "default", "unknown", "none", "null", "n/a", "unattested-harness"})


def _cursor_model_state(
    *,
    agent: str,
    result: Any | None = None,
    substitution: dict[str, Any] | None = None,
    initial: bool = False,
) -> dict[str, Any]:
    """Return runtime model-attribution companions for Cursor and native Grok.

    ``model`` remains the requested selector unless the runtime supplied a
    concrete runtime model. The separate ``resolved_model`` field makes an
    unresolved Auto run explicit without promoting ``auto`` to family proof.
    """
    if agent not in {"cursor", "grok", "grok-build"}:
        return {}

    if initial:
        return {
            "resolved_model": _CURSOR_UNKNOWN_MODEL,
            "resolved_model_known": False,
            "resolved_model_source": "pending",
        }

    actual_model: object = None
    source = "unattested-harness"
    known_raw: object = None
    if isinstance(substitution, dict):
        actual_model = substitution.get("actual_model")
        known_raw = substitution.get("actual_model_known")
        source_value = substitution.get("source")
        if isinstance(source_value, str) and source_value.strip():
            source = source_value.strip()

    concrete = actual_model.strip() if isinstance(actual_model, str) else ""
    is_concrete = bool(concrete) and concrete.casefold() not in _NON_CONCRETE_MODEL_VALUES
    explicitly_unknown = str(known_raw).strip().casefold() in {"false", "0", "no"}
    resolved_model = concrete if is_concrete and not explicitly_unknown else _CURSOR_UNKNOWN_MODEL
    known = resolved_model != _CURSOR_UNKNOWN_MODEL
    if not known and source.casefold() in {"unknown", "pending", ""}:
        # Receipts must carry the explicit unattested classification, not a
        # bare "unknown" placeholder (#6953 / #6964).
        source = _CURSOR_UNKNOWN_MODEL

    state = {
        "resolved_model": resolved_model,
        "resolved_model_known": known,
        "resolved_model_source": source,
    }
    if result is not None and known:
        # Keep the legacy ``model`` field useful to consumers that only read
        # one field, while leaving it at the requested ``auto`` selector when
        # attribution is unknown.
        state["model"] = resolved_model
        if agent in {"grok", "grok-build"} and isinstance(substitution, dict):
            from scripts.review.model_catalog import runtime_model_matches_requested

            requested_model = substitution.get("requested_model")
            if isinstance(requested_model, str) and runtime_model_matches_requested(requested_model, resolved_model):
                # Keep the requested pin for legacy substitution comparisons;
                # resolved_model retains the exact runtime attestation bytes.
                state["model"] = requested_model
    return state


def _deepseek_model_state(*, agent: str, model: str | None, cache_path: Path | None = None) -> dict[str, Any]:
    """Attest a DeepSeek route from its versioned pin or cached alias name."""
    if agent != "deepseek":
        return {}
    if model == "deepseek-v4-pro":
        return {
            "resolved_model": model,
            "resolved_model_known": True,
            "resolved_model_source": "versioned_first_party_route",
        }
    if model not in {"deepseek-v4.1-flash", "deepseek/deepseek-flash"}:
        return {
            "resolved_model": "unattested-harness",
            "resolved_model_known": False,
            "resolved_model_source": "unrecognized_deepseek_route",
        }
    path = cache_path or Path.home() / ".cache" / "opencode" / "models.json"
    try:
        cache = json.loads(path.read_text(encoding="utf-8"))
        name = cache["deepseek"]["models"]["deepseek-flash"]["name"]
    except (OSError, ValueError, KeyError, TypeError):
        name = None
    if name == "DeepSeek V4.1 Flash":
        return {
            "resolved_model": "deepseek-v4.1-flash",
            "resolved_model_known": True,
            "resolved_model_source": "models_dev_cached_alias",
        }
    return {
        "resolved_model": "unattested-harness",
        "resolved_model_known": False,
        "resolved_model_source": "models_dev_alias_unverified",
    }


_NO_DELIVERABLE_UNKNOWN_COMMIT_COUNT_REASON = "commit_count_unknown"
_NO_DELIVERABLE_NO_COMMITS_REASON = "no_commits_no_changes"
_NO_DELIVERABLE_INVALID_DECLARATION_REASON = "invalid_delivery_declaration"
_NO_DELIVERABLE_JUNK_ONLY_WORKTREE_REASON = "junk_only_worktree_changes"
# Auto-finalize refusals (#8991): every deliverable change is outside the
# owned paths, or the task declared no --owned-path at all.
_AUTO_FINALIZE_NOTHING_OWNED_REASON = "no_changes_under_owned_paths"
_AUTO_FINALIZE_NO_OWNED_PATHS_REASON = "no_owned_paths_declared"
_NO_DELIVERABLE_MISSING_REVIEW_VERDICT_REASON = "review_missing_verdict_line"
_DELIVERY_DECLARATION_PREFIX = "DELIVERABLE:"
# A declaration is an optional positive signal, so tolerate a few closing
# lines after it — but do not scan the whole report, or a quoted example of
# the format would masquerade as the worker's own declaration.
_DELIVERY_DECLARATION_SCAN_LINES = 5
_DELIVERY_OUTCOMES = frozenset({"change", "no_change"})

_WRITE_WORKTREE_HINT = (
    "Write-capable dispatch must run inside a dispatch worktree, never the "
    "primary checkout. Preferred: pass bare `--worktree` to auto-create "
    ".worktrees/dispatch/<agent>/<task>/. Alternatively point `--cwd` at an "
    "existing added worktree there."
)
_CROSS_REPO_BINDING_HINT = (
    "Dispatch binds the Learn Ukrainian primary checkout that owns this "
    "script, not the invocation cwd. Prefer first-class "
    "`dispatch --repo {infra-private|hramatka} --worktree` (#672 P2.1). "
    "Legacy: create a worktree in the sibling manually "
    "(`git worktree add .worktrees/dispatch/<agent>/<task> <base>`), then "
    "run `dispatch --mode workspace-write --cwd <that-worktree>` without "
    "`--worktree` or `--branch`. See docs/runbooks/agent-seat-onboarding.md."
)


def _strip_quoted_content(prompt: str) -> str:
    """Drop fenced blocks and Markdown blockquotes before the write-intent scan.

    A critique dispatch attaches or includes the brief under review, and that
    brief legitimately contains write-shaped lines ("Add a CLI …").  Quoted
    content is data for the worker to critique, not a directive to mutate the
    repository, so it must not trip the read-only gate (#7814 item 6).
    """
    without_fences = _FENCED_BLOCK_RE.sub("", prompt)
    return _BLOCKQUOTE_LINE_RE.sub("", without_fences)


def _is_list_or_heading_boundary(line: str) -> bool:
    """Return True if line is a markdown heading, list item, or thematic break."""
    return bool(_HEADING_BOUNDARY_RE.match(line) or _LIST_BOUNDARY_RE.match(line) or _THEMATIC_BREAK_RE.match(line))


def _is_write_directive(line: str, prev_non_empty: str | None) -> bool:
    """Classify whether a line in a prompt is a write directive (#8703).

    A line is a directive only if:
    1. It matches the write verb action pattern.
    2. It does not end in '?' (which indicates a question to the reviewer).
    3. It starts a sentence:
       - The line itself is a numbered/bulleted item or heading; OR
       - The previous non-empty line is absent (e.g. first line of the prompt); OR
       - The previous non-empty line ends in '.', ':', '!', '?'; OR
       - The previous non-empty line is a list item or heading boundary.
    A line that continues the previous line's sentence is prose, not a directive.
    """
    match = _WRITE_SHAPED_PROMPT_RE.match(line)
    if not match:
        return False

    # A line ending in '?' is a question to the reviewer, not a directive.
    stripped = line.rstrip()
    if stripped.endswith("?") or stripped.rstrip("\"'`").endswith("?"):
        return False

    # A numbered or bulleted item (or heading) starting with a write verb is a directive.
    if match.group("prefix"):
        return True

    # Continuation rule: a line without a list/heading prefix is a directive
    # only if it starts a sentence (the previous non-empty line is absent,
    # ends in '.', ':', '!', '?', or is a list item / heading boundary).
    # A line that continues the previous line's sentence is prose, not a directive.
    if prev_non_empty is None:
        return True

    prev_stripped = prev_non_empty.rstrip()
    if prev_stripped.rstrip("\"')`").endswith((".", ":", "!", "?")):
        return True

    if _HEADING_BOUNDARY_RE.match(prev_stripped) or _THEMATIC_BREAK_RE.match(prev_stripped):
        return True

    if _LIST_BOUNDARY_RE.match(prev_stripped):
        # Indented line under an unpunctuated list item continues that item's sentence
        is_indented_continuation = line.startswith(("  ", "\t")) and not prev_stripped.rstrip("\"')`").endswith(
            (".", ":", "!", "?")
        )
        return not is_indented_continuation

    return False


def _has_write_directive(prompt: str) -> bool:
    """Scan stripped prompt lines for an unquoted write directive (#8703)."""
    stripped_prompt = _strip_quoted_content(prompt)
    prev_non_empty: str | None = None
    for line in stripped_prompt.splitlines():
        if not line.strip():
            prev_non_empty = None
            continue
        if _is_write_directive(line, prev_non_empty):
            return True
        prev_non_empty = line
    return False


def _read_only_write_intent_error(*, mode: str, prompt: str) -> str | None:
    """Reject clearly write-shaped briefs before a read-only worker starts.

    ``read-only`` remains the default for genuine review and investigation
    work.  A directive to change repository content, however, cannot produce
    its requested deliverable in that mode and must fail before it can look
    like a successful no-op.  The conservative expression intentionally
    requires an instruction-shaped line, rather than matching incidental
    words such as "changes" in a review prompt.  Fenced blocks and blockquote
    lines are excluded from the scan: they carry the brief under critique,
    not the worker's own instructions.  Wrapped continuation prose and
    review questions ending in '?' are not classified as directives (#8703).
    """
    if mode != "read-only":
        return None
    if not _has_write_directive(prompt):
        return None
    return (
        "❌ write-shaped prompt cannot run with --mode read-only. "
        "Re-run with --mode workspace-write --worktree for repository edits "
        "(or --mode danger --worktree only when its extra permissions are required)."
    )


def _parse_delivery_declaration(response: str) -> dict[str, Any] | None:
    """Return a structured outcome declaration from a worker response, if any.

    The declaration is an OPTIONAL positive signal: its presence can prove
    delivery, but its absence never implies failure (git evidence decides
    first). A worker may close with one machine-readable line:

    ``DELIVERABLE: {"outcome":"change",...}`` or
    ``DELIVERABLE: {"outcome":"no_change","reason":"..."}``.

    Only the last few non-empty lines are scanned, so a polite closing line
    after the declaration does not void it while a mid-report example of the
    format is not mistaken for the worker's own declaration.
    """
    lines = [line.strip() for line in jsonl_lines(response) if line.strip()]
    line = next(
        (
            candidate
            for candidate in reversed(lines[-_DELIVERY_DECLARATION_SCAN_LINES:])
            if candidate.startswith(_DELIVERY_DECLARATION_PREFIX)
        ),
        None,
    )
    if line is None:
        return None
    try:
        declaration = json.loads(line.removeprefix(_DELIVERY_DECLARATION_PREFIX).strip())
    except json.JSONDecodeError:
        return None
    if not isinstance(declaration, dict):
        return None
    outcome = declaration.get("outcome")
    if outcome not in _DELIVERY_OUTCOMES:
        return None
    if outcome == "no_change":
        reason = declaration.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            return None
        return {"outcome": outcome, "reason": reason.strip()}
    summary = declaration.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        return None
    changed_paths = declaration.get("changed_paths")
    if (
        not isinstance(changed_paths, list)
        or not changed_paths
        or any(
            not isinstance(path, str) or not path or Path(path).is_absolute() or ".." in Path(path).parts
            for path in changed_paths
        )
    ):
        return None
    return {
        "outcome": outcome,
        "summary": summary.strip(),
        "changed_paths": sorted(set(changed_paths)),
    }


def _delivery_failure_reason(
    response: str,
    declaration: dict[str, Any] | None,
    *,
    commits_ahead: int | None,
) -> str | None:
    """Return why a write-capable run lacks delivery evidence, or None.

    Delivery is inferred from observable facts the runner already has —
    own-branch commits and response size — never from a formatting contract
    imposed on every worker's final message:

    - commits on the dispatch branch prove delivery on their own;
    - an unknown commit count proves nothing, so it fails closed;
    - a reasoned ``no_change`` declaration proves a legitimate no-op, while a
      ``change`` claim against a zero-commit branch contradicts the git
      evidence and is flagged;
    - with zero commits and no valid ``no_change`` declaration, there is
      nothing to finalize (#8448). A long "waiting in the background" reply
      is not a deliverable. A reasoned ``no_change`` declaration still is.
    """
    if commits_ahead is None:
        return _NO_DELIVERABLE_UNKNOWN_COMMIT_COUNT_REASON
    if commits_ahead > 0:
        return None
    if declaration is not None:
        if declaration["outcome"] == "no_change":
            return None
        return _NO_DELIVERABLE_INVALID_DECLARATION_REASON
    return _NO_DELIVERABLE_NO_COMMITS_REASON


def parse_review_verdict(response: str) -> str | None:
    """Return the final recognized verdict token, preserving dispatch policy."""
    verdicts = recognized_verdicts(response)
    return verdicts[-1] if verdicts else None


def _review_verdict_failure_reason(response: str) -> str | None:
    """Return the failure reason when a review-typed reply has no verdict line.

    Applies only to dispatches that opt in via ``--require-review-verdict``
    (the ask-* review wrapper); ordinary asks and implement dispatches never
    require a magic marker. A review reply that never states
    ``VERDICT: <APPROVE|APPROVED|CHANGES_REQUESTED|REQUEST_CHANGES|BLOCKED>``
    at the start of a line is not a completed review — on 2026-09-21 several
    review tasks settled ``done`` with a promise to wait for a background
    command as the whole body (#8421).
    """
    if parse_review_verdict(response) is not None:
        return None
    return _NO_DELIVERABLE_MISSING_REVIEW_VERDICT_REASON


def _load_worktree_containment():
    """Import the shared containment predicate (#4444), ensuring repo root on path.

    Mirrors the import guard used for :mod:`scripts.orchestration.reap_worktrees`
    below: running ``scripts/delegate.py`` directly puts ``scripts/`` (not the
    repo root) on ``sys.path``, so the ``scripts.*`` package needs its parent.
    """
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    from scripts.guardrails import worktree_containment

    return worktree_containment


def _load_primary_write_guard():
    """Import the primary write guard logic (#5389), ensuring repo root on path."""
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    from scripts.guardrails import primary_write_guard

    return primary_write_guard


def _resolve_cwd_path(raw: str) -> Path:
    """Resolve a ``--cwd`` argument the way the spawned worker will see it.

    A relative ``--cwd`` is handed to the worker subprocess verbatim and thus
    resolved against the dispatch process cwd, so classify it the same way.
    """
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    return p.resolve()


# Authoritative repository attribution (#7083). Task state carries the
# dispatch target's ``owner/repo`` slug so the public Work projection can
# scope its delegate join without ever inferring identity from paths or task
# ids at read time. Only GitHub remotes yield a slug; anything else stays
# unclassified (the projection fails closed on it).
_GITHUB_REMOTE_PATTERNS = (
    re.compile(r"^https?://(?:[^/@\s]+@)?github\.com/([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", re.IGNORECASE),
    re.compile(r"^ssh://git@github\.com/([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", re.IGNORECASE),
    re.compile(r"^git@github\.com:([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", re.IGNORECASE),
    re.compile(r"^git://github\.com/([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", re.IGNORECASE),
)
# Same authoritative-claim contract as scripts/api/delegate_router.py:
# only these fields attribute a task to a repository.
_REPOSITORY_ATTR_FIELDS = ("repository_id", "repository")
# Canonical GitHub home of this repository (#7522): the remote dispatch must
# pin base SHAs to when a host's ``origin`` is only a lagging mirror.
_CANONICAL_GITHUB_REPO = "learn-ukrainian/learn-ukrainian.github.io"


def _parse_github_owner_repo(remote_url: str | None) -> str | None:
    """Return ``owner/repo`` for a GitHub remote URL, else None (fail closed)."""
    if not remote_url:
        return None
    text = remote_url.strip()
    for pattern in _GITHUB_REMOTE_PATTERNS:
        match = pattern.match(text)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
    return None


_GITCONFIG_REMOTE_SECTION_RE = re.compile(r'^\s*\[\s*remote\s+"([^"]+)"\s*\]')
_GITCONFIG_ANY_SECTION_RE = re.compile(r"^\s*\[")
_GITCONFIG_URL_RE = re.compile(r"^\s*url\s*=\s*(.+?)\s*$")


def _git_common_dir(root: Path) -> Path | None:
    """Return the git common dir for a checkout or linked worktree.

    Pure filesystem — never a git subprocess. The dispatch path stays
    independent of the ``subprocess.Popen`` stubs used by dispatch tests,
    same contract as :func:`_resolve_invocation_git_root`.
    """
    dot_git = root / ".git"
    try:
        if dot_git.is_dir():
            return dot_git
        if not dot_git.is_file():
            return None
        text = dot_git.read_text(encoding="utf-8", errors="replace").strip()
        if not text.startswith("gitdir:"):
            return None
        gitdir = Path(text.split(":", 1)[1].strip())
        if not gitdir.is_absolute():
            gitdir = (root / gitdir).resolve()
        commondir_file = gitdir / "commondir"
        if commondir_file.is_file():
            common = Path(commondir_file.read_text(encoding="utf-8", errors="replace").strip())
            if not common.is_absolute():
                common = (gitdir / common).resolve()
            return common
        return gitdir
    except OSError:
        return None


def _git_remote_urls(root: Path) -> dict[str, str]:
    """Map remote names to URLs from the checkout's common git config.

    Pure filesystem, same contract as :func:`_git_common_dir` — never a git
    subprocess, so dispatch-path logic stays independent of the
    ``subprocess.Popen`` stubs used by dispatch tests and hook environments.
    The first ``url`` entry wins for remotes configured with multiple URLs.
    """
    common = _git_common_dir(root)
    if common is None:
        return {}
    try:
        lines = (common / "config").read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return {}
    urls: dict[str, str] = {}
    current_remote: str | None = None
    for line in lines:
        remote_section = _GITCONFIG_REMOTE_SECTION_RE.match(line)
        if remote_section:
            current_remote = remote_section.group(1)
            continue
        if _GITCONFIG_ANY_SECTION_RE.match(line):
            current_remote = None
            continue
        if current_remote is not None:
            url = _GITCONFIG_URL_RE.match(line)
            if url and current_remote not in urls:
                urls[current_remote] = url.group(1)
    return urls


def _read_origin_url(root: Path) -> str | None:
    """Read ``remote.origin.url`` from the checkout's common git config."""
    return _git_remote_urls(root).get("origin")


def _resolve_canonical_remote_name(remote_urls: dict[str, str]) -> str | None:
    """Return the name of the remote that serves the canonical GitHub repo.

    Prefers a remote literally named ``github`` whose URL is the canonical
    ``owner/repo``; otherwise ``origin`` when origin itself is that GitHub
    URL. Any other layout stays unclassified (None) so the dispatch path
    keeps its origin-only behavior instead of inventing a remote (#7522).
    """
    github_url = remote_urls.get("github")
    if github_url and _parse_github_owner_repo(github_url) == _CANONICAL_GITHUB_REPO:
        return "github"
    origin_url = remote_urls.get("origin")
    if origin_url and _parse_github_owner_repo(origin_url) == _CANONICAL_GITHUB_REPO:
        return "origin"
    return None


def _resolve_dispatch_repository(target: str | Path | None) -> str | None:
    """Resolve the authoritative ``owner/repo`` identity for a dispatch target.

    Reads the target checkout's git config from disk — never a network call,
    never a subprocess. A target inside the primary checkout (including an
    auto worktree, existing or already reaped) binds the primary's origin by
    construction; any other target must exist on disk so its own
    ``remote.origin.url`` can be read. Returns None when no GitHub slug can be
    proven — callers then leave the task unclassified rather than guess.
    """
    if target is None or str(target) == "":
        return None
    try:
        target_path = Path(target).expanduser().resolve()
        primary = _REPO_ROOT.resolve()
    except OSError:
        return None
    if target_path == primary or primary in target_path.parents:
        config_dir = primary
    elif target_path.is_dir():
        config_dir = target_path
    else:
        return None
    return _parse_github_owner_repo(_read_origin_url(config_dir))


def _state_repository_claims(state: dict[str, Any]) -> list[str]:
    """Return the distinct authoritative repository claims on a task state."""
    claims: list[str] = []
    for field_name in _REPOSITORY_ATTR_FIELDS:
        raw = state.get(field_name)
        if raw is None or raw == "":
            continue
        text = str(raw).strip()
        if text and text not in claims:
            claims.append(text)
    return claims


def _resolve_invocation_git_root(start: Path | str | None = None) -> Path | None:
    """Primary checkout that owns ``start`` (default: process cwd), or None.

    Walks ``.git`` on disk instead of calling ``git rev-parse``. The answer we
    need is "same repository or a sibling?", and the filesystem shape already
    distinguishes a primary ``.git`` directory from a linked worktree gitdir.
    Avoiding a git subprocess also keeps this preflight independent of the
    ``subprocess.Popen`` stubs used by dispatch tests and hook environments.
    """
    wc = _load_worktree_containment()
    origin = wc.canonicalize(start if start is not None else Path.cwd())
    probe = origin if origin.is_dir() else origin.parent
    return wc._fs_main_root(probe)


def _resolve_cross_repo_binding_error(
    *,
    worktree_arg: str | None,
    cwd_arg: str | None,
    requested_branch: str | None = None,
    invocation_cwd: Path | str | None = None,
    target_repo_root: Path | str | None = None,
) -> str | None:
    """Refuse silent primary-repo binding when invoked from another git root.

    ``--worktree`` / ``--branch`` without ``--repo`` still create under
    :data:`_REPO_ROOT` (see :func:`_auto_worktree_path`). An invocation cwd
    whose git root is a sibling checkout used to look like "dispatch here"
    while the worktree landed in the primary — issue #6900.

    With allowlisted ``--repo`` (#672 P2.1), worktrees are created under the
    resolved sibling checkout; the guard allows that explicit retarget.
    """
    invocation_root = _resolve_invocation_git_root(invocation_cwd)
    if invocation_root is None:
        return None
    wc = _load_worktree_containment()
    primary = wc.canonicalize(_REPO_ROOT)
    if invocation_root == primary:
        return None
    if target_repo_root is not None:
        target = wc.canonicalize(target_repo_root)
        if invocation_root == target:
            return None
        # Explicit --repo retargets creation even when the shell sits elsewhere.
        if target != primary:
            return None
    # Documented sibling flow: explicit --cwd, never --worktree/--branch.
    # cmd_dispatch promotes a bare --branch to worktree_arg="auto" first.
    if cwd_arg and not worktree_arg and not requested_branch:
        return None
    flags = [flag for flag, present in (("--worktree", worktree_arg), ("--branch", requested_branch)) if present]
    flag_bit = (
        " and ".join(flags) + " would silently create or attach a worktree under the primary"
        if flags
        else "the worker would silently run in the primary checkout"
    )
    return (
        f"❌ dispatch targets the primary checkout ({primary}); "
        f"invocation cwd resolves to a different git root ({invocation_root}). "
        f"{flag_bit}.\n   {_CROSS_REPO_BINDING_HINT}"
    )


# Runtime worktrees the ACP bridge creates, git-locks, and removes on its own
# schedule (scripts/ai_agent_bridge/_acp_execution.py). They are never a
# dispatch attach target (#8610).
_ACP_RUNTIME_SUBTREE = (".worktrees", "dispatch", "acp")


def _is_acp_runtime_path(path: Path) -> bool:
    """True when ``path`` lies in a repository's ``.worktrees/dispatch/acp/`` subtree."""
    parts = path.parts
    width = len(_ACP_RUNTIME_SUBTREE)
    return any(parts[index : index + width] == _ACP_RUNTIME_SUBTREE for index in range(len(parts) - width + 1))


def _resolve_acp_runtime_target_error(
    *,
    worktree_arg: str | None,
    cwd_arg: str | None,
    target_repo_root: Path,
) -> str | None:
    """Refuse a dispatch whose ``--cwd`` or explicit ``--worktree`` is an ACP runtime.

    The ACP bridge removes its runtime worktrees without consulting dispatch
    task records, so a worker attached to one could lose its cwd (#8610).
    Checked for every mode, before any side effect.
    """
    candidates: list[tuple[str, str, Path]] = []
    if cwd_arg:
        candidates.append(("--cwd", cwd_arg, _resolve_cwd_path(cwd_arg)))
    if worktree_arg and worktree_arg != "auto":
        candidates.append(
            ("--worktree", worktree_arg, _normalize_worktree_path(worktree_arg, repo_root=target_repo_root))
        )
    for flag, raw, candidate in candidates:
        if _is_acp_runtime_path(candidate):
            return (
                f"❌ {flag} {raw!r} resolves inside an ACP runtime worktree ({candidate}); "
                ".worktrees/dispatch/acp/ belongs to the ACP bridge and is never a dispatch target.\n"
                "   Pass bare `--worktree` to auto-create .worktrees/dispatch/<agent>/<task>/, "
                "or point `--cwd` at an existing dispatch worktree."
            )
    return None


def _resolve_verified_worktree_path(path: Path) -> Path | None:
    """Return canonical Path of the containing registered worktree if ``path`` resolves
    inside a git-registered worktree that is not the primary checkout, else None.

    "Verified" means the containing worktree appears in ``git worktree list``. A
    bare directory that only *looks* like ``.worktrees/**`` but was never
    ``git worktree add``-ed does NOT qualify — the worker would otherwise run
    outside any real worktree while believing it was isolated. An ACP runtime
    worktree does not qualify either (:func:`_is_acp_runtime_path`).
    """
    wc = _load_worktree_containment()
    target = wc.canonicalize(path)
    if target == wc.canonicalize(_REPO_ROOT):
        # The exact primary root cannot be an added worktree. This common
        # explicit --cwd path needs no git subprocess before worker spawn.
        return None
    start = target if target.exists() else target.parent
    try:
        main_root = wc.resolve_main_root(start)
    except wc.NotAGitRepositoryError:
        return None
    for worktree in wc.registered_worktrees(main_root):
        if worktree == main_root:
            continue
        if target == worktree or target.is_relative_to(worktree):
            return None if _is_acp_runtime_path(worktree) else worktree
    return None


def _is_verified_added_worktree(path: Path) -> bool:
    """True if ``path`` resolves inside a git-registered worktree that is not the
    primary checkout.
    """
    return _resolve_verified_worktree_path(path) is not None


def _apply_worktree_git_ceiling(worker_env: dict[str, str], worktree_path: Path) -> None:
    """Pin GIT_CEILING_DIRECTORIES at the worktree's PARENT (#5803 follow-up).

    Damage reduction, NOT isolation: stops git repo discovery at the dispatch
    parent dir so a broken/missing worktree .git pointer can never bind the
    worker to the PRIMARY checkout via upward traversal. The ceiling must be
    the parent — a ceiling at the worktree root itself excludes the root from
    the discovery walk and breaks git from subdirectories (verified
    2026-07-25). Linked worktrees resolve their own .git file at the root and
    share the git control plane, so normal ops (subdirs, fetch, commit) are
    unaffected.
    """
    ceiling = str(worktree_path.parent)
    existing_ceiling = worker_env.get("GIT_CEILING_DIRECTORIES")
    worker_env["GIT_CEILING_DIRECTORIES"] = f"{existing_ceiling}{os.pathsep}{ceiling}" if existing_ceiling else ceiling


def _resolve_write_cwd_error(
    *,
    mode: str,
    worktree_arg: str | None,
    cwd_arg: str | None,
) -> str | None:
    """Reject a write-capable dispatch that would run outside a verified worktree.

    Returns an operator-facing error string, or None when the dispatch is safe.
    Evaluated before any side effects (log files, ``git worktree add``) so a
    rejection leaves no worktree/branch residue behind.

    Policy (issue #4445):

    * ``--worktree`` (bare/``auto``) is the recommended path and always lands in
      ``.worktrees/dispatch/<agent>/<task>/`` — :func:`_ensure_worktree` creates
      or validates it. An explicit ``--worktree PATH`` is rejected only when it
      *is* the primary checkout.
    * ``--cwd`` is allowed only when it resolves to a verified added worktree,
      never the primary checkout or a bare in-repo directory.
    * With neither flag the worker would default to the primary checkout, so a
      write-capable dispatch is rejected outright.
    """
    if mode not in _WRITE_CAPABLE_MODES:
        return None

    wc = _load_worktree_containment()

    if worktree_arg:
        # Bare ``--worktree`` (the sentinel ``auto``) auto-derives the dispatch
        # subtree — always isolated, nothing to verify up front.
        if worktree_arg == "auto":
            return None
        candidate = _normalize_worktree_path(worktree_arg)
        if wc.is_primary_checkout(candidate):
            return (
                f"❌ --worktree {worktree_arg!r} points at the primary checkout; "
                f"write-capable dispatch may not run there.\n   {_WRITE_WORKTREE_HINT}"
            )
        return None

    if cwd_arg:
        candidate = _resolve_cwd_path(cwd_arg)
        if wc.is_primary_checkout(candidate):
            return (
                f"❌ --cwd {cwd_arg!r} resolves inside the primary checkout; "
                f"write-capable dispatch may not run there.\n   {_WRITE_WORKTREE_HINT}"
            )
        if not _is_verified_added_worktree(candidate):
            return (
                f"❌ --cwd {cwd_arg!r} is not a verified git worktree; "
                f"write-capable dispatch requires an added worktree under "
                f".worktrees/dispatch/<agent>/<task>/.\n   {_WRITE_WORKTREE_HINT}"
            )
        return None

    return (
        f"❌ --mode {mode} requires an isolated worktree; without --worktree/--cwd "
        f"the worker would run in the primary checkout.\n   {_WRITE_WORKTREE_HINT}"
    )


def _format_dirty_entries(entries: list[dict[str, str]], *, limit: int = 10) -> str:
    shown = [f"{entry.get('xy', '').strip() or '??'} {entry.get('path', '')}" for entry in entries[:limit]]
    if len(entries) > limit:
        shown.append(f"... and {len(entries) - limit} more")
    return ", ".join(shown) if shown else "(none)"


# Declared receipt collection points unignored in .gitignore as tracked-by-design (#6967).
# Untracked files under these directories are allowlisted by the clean-tree guard so
# concurrent jobs writing receipts do not block write-capable dispatches.
_CLEAN_TREE_UNTRACKED_RECEIPT_ALLOWLIST: tuple[str, ...] = ("batch_state/atlas-jobs/receipts/",)


def _is_untracked_receipt_allowlisted(entry: dict[str, str]) -> bool:
    """Return True if entry is an untracked file under a declared receipt collection point."""
    if entry.get("kind") != "untracked" and entry.get("xy", "").strip() != "??":
        return False
    raw_path = (entry.get("path") or "").replace("\\", "/")
    if raw_path.startswith("./"):
        raw_path = raw_path[2:]
    raw_path = raw_path.lstrip("/")
    for prefix in _CLEAN_TREE_UNTRACKED_RECEIPT_ALLOWLIST:
        clean_prefix = prefix.strip("/")
        if raw_path == clean_prefix or raw_path.startswith(clean_prefix + "/"):
            return True
    return False


def _resolve_dirty_primary_checkout_error(*, mode: str) -> str | None:
    """Reject write-capable dispatch when the protected primary checkout is dirty.

    This is separate from the #4445 isolation check: even a correctly isolated
    new worktree should not be dispatched while main/master already has tracked
    or untracked non-ignored dirt, because the next worker inherits polluted
    operator state. Read-only dispatches stay allowed for preflight and diagnosis.
    """
    if mode not in _WRITE_CAPABLE_MODES:
        return None

    wc = _load_worktree_containment()
    try:
        status = wc.primary_checkout_dirty_status(_REPO_ROOT)
    except Exception as exc:
        return (
            "❌ could not verify primary checkout cleanliness before "
            f"write-capable dispatch: {type(exc).__name__}: {exc}"
        )

    if not status.get("protected_branch") or not status.get("dirty"):
        return None

    raw_entries = status.get("entries") or []
    entries = [entry for entry in raw_entries if not _is_untracked_receipt_allowlisted(entry)]
    if not entries:
        return None

    extra_diagnostic = ""
    try:
        pwg = _load_primary_write_guard()
        writable = pwg.get_writable_tracked_files(_REPO_ROOT)
        if writable:
            offenders = [str(f.relative_to(_REPO_ROOT)) for f in writable]
            extra_diagnostic = f"   writable tracked files (guard OFF): {', '.join(offenders)}\n"
        else:
            extra_diagnostic = "   writable tracked files (guard ON): (none)\n"
    except Exception as exc:
        extra_diagnostic = f"   could not check write guard status: {exc}\n"

    return (
        "❌ primary checkout is dirty; refusing write-capable dispatch before "
        "creating branch/worktree residue.\n"
        f"   checkout role: {status.get('role')}\n"
        f"   head: {status.get('head_sha')}\n"
        f"   command: {status.get('checked_command')}\n"
        f"   branch: {status.get('branch')}\n"
        f"   dirty files: {_format_dirty_entries(entries)}\n"
        f"{extra_diagnostic}"
        "   Clean/stash the primary checkout, or keep only gitignored local "
        "runtime state, then retry."
    )


def _resolve_primary_integrity_error(*, mode: str) -> str | None:
    """Block NEW write-capable dispatches while the primary checkout is drifted.

    #5803 follow-up: a worker detached the primary (`checkout: moving from main
    to FETCH_HEAD`) and every worktree branched afterwards would inherit a
    wrong base. The watchdog only diagnoses and records drift here; new
    write-capable dispatches stop until an operator explicitly repairs the
    checkout. Read-only dispatches stay allowed for preflight and diagnosis,
    same contract as the dirty-primary guard.
    """
    if mode not in _WRITE_CAPABLE_MODES:
        return None

    try:
        try:
            from scripts.audit.check_primary_integrity import check_primary_integrity
        except ImportError:  # path-flavoured import for test/script contexts
            from audit.check_primary_integrity import check_primary_integrity

        ok, message = check_primary_integrity(_REPO_ROOT, fix=False, tasks_dir=tasks_dir())
    except Exception as exc:
        print(
            f"⚠️  primary-integrity watchdog errored ({type(exc).__name__}: {exc}); "
            "proceeding — the health-poll canary will surface persistent failures",
            file=sys.stderr,
        )
        return None

    if ok:
        return None

    return (
        "❌ primary checkout drift is UNREPAIRED; refusing to start a new "
        "write-capable dispatch (it would branch from a wrong base). Running "
        "dispatches are not touched.\n"
        f"   watchdog: {message}\n"
        "   Inspect the primary checkout and run the explicit doctor only when "
        "appropriate: .venv/bin/python scripts/audit/check_primary_integrity.py "
        "--fix. Evidence is under "
        "data/telemetry/primary-integrity/events.jsonl."
    )


def _warn_venv_integrity() -> None:
    """Advisory-only primary-venv integrity probe (#6830 follow-up).

    A mid-session venv rebuild can leave `.venv` empty (every import fails)
    or with console-script launchers pointing at a deleted worktree venv
    (`pytest`/`py.test`/`cbor2` live finding). This probe DETECTS and RECORDS
    such corruption; it never blocks a dispatch and never repairs here —
    reinstalling packages is a package mutation, gated to an explicit
    operator command (see check_venv_integrity.py). Fails open on any probe
    error, same contract as the sibling integrity watchdogs.
    """
    try:
        try:
            from scripts.audit.check_venv_integrity import check_venv_integrity
        except ImportError:  # path-flavoured import for test/script contexts
            from audit.check_venv_integrity import check_venv_integrity

        ok, message = check_venv_integrity(_REPO_ROOT, tasks_dir=tasks_dir())
    except Exception as exc:
        print(
            f"⚠️  venv-integrity probe errored ({type(exc).__name__}: {exc}); "
            "proceeding — detection only, never blocks dispatch",
            file=sys.stderr,
        )
        return

    if not ok:
        print(f"⚠️  {message}", file=sys.stderr)


def _warn_worktree_cleanup_integrity() -> None:
    """Advisory-only worktree-cleanup launchd probe (#6937 follow-up).

    A venv rebuild can leave launchd unable to start
    ``com.learn-ukrainian.worktree-cleanup`` (LWCR init failure, exit 78)
    with no new receipt for days. This probe DETECTS and RECORDS that
    darkness; it never blocks a dispatch and never reloads launchd here —
    reinstall is an explicit operator action from the merged primary.
    Fails open on any probe error, same contract as the sibling integrity
    watchdogs.
    """
    try:
        try:
            from scripts.audit.check_worktree_cleanup_integrity import (
                check_worktree_cleanup_integrity,
            )
        except ImportError:  # path-flavoured import for test/script contexts
            from audit.check_worktree_cleanup_integrity import (
                check_worktree_cleanup_integrity,
            )

        ok, message = check_worktree_cleanup_integrity(_REPO_ROOT, tasks_dir=tasks_dir())
    except Exception as exc:
        print(
            f"⚠️  worktree-cleanup-integrity probe errored ({type(exc).__name__}: {exc}); "
            "proceeding — detection only, never blocks dispatch",
            file=sys.stderr,
        )
        return

    if not ok:
        print(f"⚠️  {message}", file=sys.stderr)


def _warn_node_modules_integrity() -> None:
    """Advisory-only node_modules symlink-corruption probe (#6818 follow-up).

    `_provision_data_symlinks` symlinks the primary's `node_modules` and
    `site/node_modules` directly into every dispatch worktree — any write a
    worktree makes through that path lands in the primary's real files
    (#6805 incident). This probe DETECTS and RECORDS such corruption; per the
    K3-reviewed design it never blocks a dispatch and never repairs here —
    auto-repair is gated on the Node-version pin landing first and is a
    separate operator decision (see check_node_modules_integrity.py). Fails
    open on any probe error, same contract as the primary-integrity watchdog.
    """
    try:
        try:
            from scripts.audit.check_node_modules_integrity import (
                check_node_modules_integrity,
            )
        except ImportError:  # path-flavoured import for test/script contexts
            from audit.check_node_modules_integrity import check_node_modules_integrity

        ok, message = check_node_modules_integrity(_REPO_ROOT, tasks_dir=tasks_dir())
    except Exception as exc:
        print(
            f"⚠️  node_modules-integrity probe errored ({type(exc).__name__}: {exc}); "
            "proceeding — detection only, never blocks dispatch",
            file=sys.stderr,
        )
        return

    if not ok:
        print(f"⚠️  {message}", file=sys.stderr)


def _warn_if_monitor_api_unreachable() -> None:
    """Make a dead local Monitor API visible without making dispatch depend on it.

    Dispatch remains a recovery path when the dashboard is down. The warning is
    deliberately advisory, unlike primary-integrity drift, because workers can
    still run with their file-based fallbacks and may be needed to repair the
    API itself.
    """
    url = f"{_monitor_api_base_url()}/api/health"
    try:
        with urllib.request.urlopen(url, timeout=1) as response:
            if response.status != 200:
                raise MonitorApiUnavailable(f"HTTP {response.status}")
    except (OSError, TimeoutError, urllib.error.URLError, MonitorApiUnavailable) as exc:
        detail = f"{type(exc).__name__}: {exc}"
        _append_dispatch_event("monitor_api_unreachable_pre_dispatch", url=url, detail=detail)
        print(
            "⚠ MONITOR API UNREACHABLE — dispatch will continue with offline fallbacks.\n"
            f"   probe: GET {url}\n"
            f"   error: {detail}\n"
            "   recovery: ./services.sh status api; inspect .pids/api-last-crash.json; "
            "then ./services.sh restart api",
            file=sys.stderr,
        )


def _origin_tracking_refspec(branch: str) -> str:
    """Explicit fetch mapping that lands ``branch`` under refs/remotes/origin."""
    from scripts.common.git_context import origin_tracking_refspec

    return origin_tracking_refspec(branch)


def _fetch_remote_branch(remote: str, branch: str) -> subprocess.CompletedProcess[str] | None:
    """Fetch ``branch`` from ``remote`` into the origin tracking ref.

    Returns None when the fetch could not run at all (spawn failure or
    timeout); a completed process with a nonzero returncode is returned
    as-is so callers can fail closed carrying git's own diagnostics.
    """
    try:
        return subprocess.run(
            ["git", "fetch", remote, _origin_tracking_refspec(branch)],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_NETWORK_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _ls_remote_branch_sha(remote: str, branch: str, *, strict: bool = False) -> str | None:
    """Probe the SHA ``remote`` serves for ``branch`` without touching refs.

    ``git ls-remote`` answers from the remote directly, so a lagging mirror
    can be detected (#7522) while ``refs/remotes/origin/<branch>`` is written
    only by the canonical fetch. Best-effort: a spawn failure, timeout, or
    unresolved ref yields None. With ``strict``, read failures raise instead
    of being confused with an absent branch; diagnostics omit remote URLs.
    """
    try:
        proc = subprocess.run(
            ["git", "ls-remote", remote, f"refs/heads/{branch}"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_NETWORK_GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        if strict:
            raise _AuthoringObservationUnknown("canonical remote branch lookup (git ls-remote) timed out") from exc
        return None
    except OSError as exc:
        if strict:
            raise _AuthoringObservationUnknown("canonical remote branch lookup (git ls-remote) could not run") from exc
        return None
    if proc.returncode != 0:
        if strict:
            raise _AuthoringObservationUnknown(
                f"canonical remote branch lookup (git ls-remote) failed (exit {proc.returncode}); "
                "check network/authentication and remote access, then retry"
            )
        return None
    for line in (proc.stdout or "").splitlines():
        sha, sep, ref = line.partition("\t")
        if sep and ref.strip() == f"refs/heads/{branch}":
            return sha.strip() or None
    return None


def _verify_origin_tracking_ref(branch: str) -> subprocess.CompletedProcess[str] | None:
    """Verify that ``origin/<branch>`` resolves after a mapped fetch."""
    try:
        return subprocess.run(
            ["git", "rev-parse", "--verify", f"origin/{branch}"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _fetch_origin_branch(branch: str) -> bool:
    """Single-remote fetch contract: fetch origin, report success as bool."""
    proc = _fetch_remote_branch("origin", branch)
    if proc is None or proc.returncode != 0:
        return False
    verify = _verify_origin_tracking_ref(branch)
    return verify is not None and verify.returncode == 0


def _canonical_fetch_failure_error(
    *,
    branch: str,
    canonical_remote: str,
    canonical_url: str,
    mirror_url: str,
    detail: str,
) -> RuntimeError:
    """Build the #7522 fail-closed error for a canonical-remote fetch failure."""
    return RuntimeError(
        f"could not fetch base branch {branch!r} from canonical GitHub remote "
        f"'{canonical_remote}' ({canonical_url}): {detail}. Remote 'origin' is "
        f"{mirror_url!r} (a non-canonical mirror) and was NOT used as a fallback — "
        "a lagging mirror must never pin the worktree base. Recovery: inspect "
        "`git remote -v`, then run "
        f"`git fetch {canonical_remote} {_origin_tracking_refspec(branch)}` and "
        "retry the dispatch."
    )


def _fetch_base(base: str) -> bool:
    """Fetch the dispatch base branch into ``origin/<branch>``.

    ``base`` may be a plain branch name (``main``), an origin-prefixed ref
    (``origin/main`` — the form the dispatch runbooks mandate), or a
    github-prefixed one (``github/main``). The remote refspec is an explicit
    mapping ``+refs/heads/<branch>:refs/remotes/origin/<branch>`` so the
    remote-tracking ref exists regardless of host git fetch refspec config
    (#7168).

    #7522: on hosts where ``origin`` is a lagging mirror and a separate
    remote points at the canonical GitHub repository, the base must be
    fetched from that canonical remote — the mirror is probed read-only
    (``git ls-remote``) only so divergence can be warned about, and a
    canonical fetch failure fails closed instead of silently pinning the
    mirror's stale SHA. The canonical fetch is the only writer of
    ``refs/remotes/origin/<branch>``: a fail-closed dispatch leaves the
    prior tracking ref untouched, never pinned to the lagging mirror.
    """
    branch = _base_branch_name(base)
    remote_urls = _git_remote_urls(_REPO_ROOT)
    canonical_remote = _resolve_canonical_remote_name(remote_urls)
    if canonical_remote is None or canonical_remote == "origin":
        # Single-remote hosts — origin is the canonical GitHub remote, or no
        # GitHub remote is configured at all. Exactly the pre-#7522 origin
        # fetch, including its bool failure contract: callers own the
        # instructive fail-closed message.
        return _fetch_origin_branch(branch)

    canonical_url = remote_urls.get(canonical_remote) or "<unknown url>"
    mirror_url = remote_urls.get("origin") or "<unknown url>"

    # Probe the mirror read-only — never a fetch. A mirror fetch lands its
    # lagging SHA in refs/remotes/origin/<branch>; if the canonical fetch
    # below then fails closed, the tracking ref would stay poisoned at that
    # stale SHA. ls-remote writes no local ref, so the canonical fetch is
    # the only writer of the tracking ref.
    mirror_sha: str | None = None
    if "origin" in remote_urls:
        mirror_sha = _ls_remote_branch_sha("origin", branch)

    canonical_proc = _fetch_remote_branch(canonical_remote, branch)
    if canonical_proc is None:
        raise _canonical_fetch_failure_error(
            branch=branch,
            canonical_remote=canonical_remote,
            canonical_url=canonical_url,
            mirror_url=mirror_url,
            detail=f"fetch timed out or failed to start after {DEFAULT_NETWORK_GIT_TIMEOUT_S}s",
        )
    if canonical_proc.returncode != 0:
        raise _canonical_fetch_failure_error(
            branch=branch,
            canonical_remote=canonical_remote,
            canonical_url=canonical_url,
            mirror_url=mirror_url,
            detail=_format_process_failure(canonical_proc),
        )
    canonical_sha = _resolve_sha(_REPO_ROOT, f"origin/{branch}")
    if canonical_sha is None:
        raise _canonical_fetch_failure_error(
            branch=branch,
            canonical_remote=canonical_remote,
            canonical_url=canonical_url,
            mirror_url=mirror_url,
            detail=f"fetched, but refs/remotes/origin/{branch} did not resolve afterwards",
        )
    if mirror_sha is not None and mirror_sha != canonical_sha:
        print(
            f"⚠️  remote 'origin' ({mirror_url}) lags the canonical GitHub remote "
            f"'{canonical_remote}' ({canonical_url}) for branch {branch!r}: "
            f"origin SHA {mirror_sha} != canonical SHA {canonical_sha}. "
            "Dispatching from the canonical GitHub SHA.",
            file=sys.stderr,
        )
    return True


def _validate_branch_reuse_name(branch: str) -> str:
    """Reject unsafe or ambiguous ``--branch`` values before attaching a worktree."""
    from scripts.common.git_context import UnsafeBranchNameError, validate_plain_branch_name

    try:
        normalized = validate_plain_branch_name(branch, repo_root=_REPO_ROOT)
    except UnsafeBranchNameError as exc:
        raise ValueError(
            "--branch must be a local branch name without origin/, github/, or refs/ "
            f"prefixes, and a valid git branch: got {branch!r} ({exc})"
        ) from exc

    containment = _load_worktree_containment()
    if normalized in containment.PROTECTED_BRANCHES:
        raise ValueError(
            f"refusing --branch {normalized!r}: protected branches may not be attached to a dispatch worktree"
        )
    return normalized


def _fetch_existing_branch(branch: str) -> None:
    """Fetch and verify the remote branch used by ``--branch`` reuse mode.

    The remote refspec is an explicit mapping ``+refs/heads/<branch>:refs/remotes/origin/<branch>``
    so the remote-tracking ref exists regardless of host git fetch refspec config (#7168).
    #7522: when a canonical GitHub remote is configured it is the fetch
    source — a host mirror may lag or not carry the PR branch at all.
    """
    remote_urls = _git_remote_urls(_REPO_ROOT)
    canonical_remote = _resolve_canonical_remote_name(remote_urls)
    remote_name = canonical_remote or "origin"
    refspec = _origin_tracking_refspec(branch)
    try:
        proc = subprocess.run(
            ["git", "fetch", remote_name, refspec],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_NETWORK_GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"could not fetch existing branch {branch!r} from remote {remote_name!r}: "
            f"fetch timed out after {DEFAULT_NETWORK_GIT_TIMEOUT_S}s"
        ) from exc
    if proc.returncode != 0:
        if canonical_remote is not None and canonical_remote != "origin":
            raise RuntimeError(
                f"could not fetch existing branch {branch!r} from canonical GitHub "
                f"remote '{canonical_remote}' ({remote_urls.get(canonical_remote)}): "
                f"{_format_process_failure(proc)}. Remote 'origin' is "
                f"{remote_urls.get('origin')!r} (a non-canonical mirror) and was NOT "
                "used as a fallback — the mirror may lag or not carry the PR branch. "
                "Recovery: inspect `git remote -v`, then run "
                f"`git fetch {canonical_remote} {refspec}` and retry the dispatch."
            )
        raise RuntimeError(f"could not fetch existing branch {branch!r}: {_format_process_failure(proc)}")
    try:
        verify = subprocess.run(
            ["git", "rev-parse", "--verify", f"origin/{branch}"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"origin/{branch} was not found after fetch; rev-parse timed out after {DEFAULT_GIT_TIMEOUT_S}s"
        ) from exc
    if verify.returncode != 0:
        raise RuntimeError(f"origin/{branch} was not found after fetch; --branch requires an existing remote branch")


def _require_local_branch_is_ancestor_of_origin(
    branch: str, *, continuation_head_sha: str | None = None, continuation_remote_sha: str | None = None
) -> str:
    """Return fetched origin SHA, or an admitted same-writer local continuation.

    Only an existing checkout admitted on its local-only commits can supply
    ``continuation_head_sha`` (#9988). Never reset that head to the remote.
    """
    origin_ref = f"origin/{branch}"
    local_ref = f"refs/heads/{branch}"
    origin_sha = _resolve_sha(_REPO_ROOT, origin_ref)
    if origin_sha is None:
        raise RuntimeError(f"{origin_ref} was not found after fetch; --branch requires an existing remote branch")
    local_sha = _resolve_sha(_REPO_ROOT, local_ref)
    if local_sha is None or local_sha == origin_sha:
        return origin_sha

    try:
        ancestry = subprocess.run(
            ["git", "merge-base", "--is-ancestor", local_ref, origin_ref],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"could not compare local {branch!r} against {origin_ref}: merge-base timed out after {DEFAULT_GIT_TIMEOUT_S}s"
        ) from exc
    if ancestry.returncode == 0:
        return origin_sha
    if ancestry.returncode != 1:
        raise RuntimeError(
            f"could not compare local {branch!r} against {origin_ref}: {_format_process_failure(ancestry)}"
        )
    if continuation_head_sha == local_sha and continuation_remote_sha == origin_sha:
        try:
            if _git_is_ancestor(origin_sha, local_sha):
                return local_sha
        except _AuthoringObservationUnknown as exc:
            raise RuntimeError(f"could not verify continuation ancestry: {exc}") from exc
    raise WorktreeBranchDiverged(
        f"refusing --branch {branch!r}: local {local_ref} is not an ancestor of "
        f"{origin_ref}; local_sha={local_sha} origin_sha={origin_sha}. "
        "Reconcile explicitly before dispatching: inspect with "
        f"`git log --left-right --graph --oneline {local_ref}...{origin_ref}`; "
        f"to preserve local commits, run `git switch {branch} && git rebase {origin_ref}` "
        f"then `git push --force-with-lease origin {branch}`; to discard the local-only "
        f"ref, run `git branch -f {branch} {origin_ref}`."
    )


def _branch_worktree_paths(branch: str) -> list[Path]:
    """Return registered worktree roots currently attached to ``branch``."""
    try:
        proc = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"could not list git worktrees: timed out after {DEFAULT_GIT_TIMEOUT_S}s") from exc
    if proc.returncode != 0:
        raise RuntimeError(f"could not list git worktrees: {_format_process_failure(proc)}")

    matches: list[Path] = []
    current_path: Path | None = None
    current_branch: str | None = None
    for line in [*(proc.stdout or "").splitlines(), ""]:
        if not line:
            if current_path is not None and current_branch == branch:
                matches.append(current_path.resolve())
            current_path = None
            current_branch = None
        elif line.startswith("worktree "):
            current_path = Path(line.removeprefix("worktree ").strip())
        elif line.startswith("branch refs/heads/"):
            current_branch = line.removeprefix("branch refs/heads/").strip()
    return matches


def _dispatch_layout_parts(path: Path) -> tuple[str, str] | None:
    """Return ``(agent, path_component)`` for ``.worktrees/dispatch/<agent>/<task>/``."""
    try:
        rel = path.resolve().relative_to((_REPO_ROOT / ".worktrees" / "dispatch").resolve())
    except ValueError:
        return None
    if len(rel.parts) >= 2:
        return rel.parts[0], rel.parts[1]
    return None


def _task_status_candidates_for_worktree(path: Path) -> list[str]:
    """Candidate task IDs that may own a dispatch worktree path.

    Path components are *normalized* (agent prefix stripped, non-alnum flattened)
    while state files keep the original task_id with ``/`` → ``_``. Prefer an
    exact ``worktree_path`` match in batch_state; candidates are a fallback only.
    """
    parts = _dispatch_layout_parts(path)
    if parts is None:
        return []
    agent, component = parts
    candidates = [
        component,
        f"{agent}-{component}",
        f"{agent}/{component}",
        f"{agent}_{component}",
    ]
    # Preserve order, drop duplicates.
    seen: set[str] = set()
    out: list[str] = []
    for cand in candidates:
        if cand not in seen:
            seen.add(cand)
            out.append(cand)
    return out


def _task_state_for_worktree(path: Path) -> tuple[str | None, dict[str, Any] | None]:
    """Load the path-bound task record for a dispatch worktree.

    Resolution order:
    1. Exact ``worktree_path`` match in any task state (authoritative).
    2. Candidate task IDs reconstructed from the dispatch layout.

    ``None`` is meaningful to the branch-holder release path: a legacy holder
    can have no task record, but only a separate known-empty liveness probe may
    authorize its release.  Never infer a task record from a path component
    alone.
    """
    resolved = path.resolve()
    # 1) Authoritative: scan states for worktree_path match.
    try:
        state_files = list(tasks_dir().glob("*.json")) if tasks_dir().is_dir() else []
    except OSError:
        state_files = []
    for state_file in state_files:
        if state_file.name.endswith(".tmp") or ".tmp." in state_file.name:
            continue
        state = _read_state(state_file)
        if not isinstance(state, dict):
            continue
        wt = state.get("worktree_path") or state.get("cwd")
        if not wt:
            continue
        try:
            if Path(str(wt)).resolve() == resolved:
                task_id = state.get("task_id")
                return (str(task_id) if task_id is not None else None), state
        except OSError:
            continue

    # 2) Fallback candidates from path layout — only if state records an
    # exact worktree_path/cwd match. Never accept path-less legacy states
    # (CF F001 #5708): a shared path-component name must not authorize remove.
    for task_id in _task_status_candidates_for_worktree(path):
        state = _read_state(_state_path(task_id))
        if not isinstance(state, dict):
            continue
        wt = state.get("worktree_path") or state.get("cwd")
        if not wt:
            continue
        try:
            if Path(str(wt)).resolve() != resolved:
                continue
        except OSError:
            continue
        return task_id, state
    return None, None


def _task_status_for_worktree(path: Path) -> str | None:
    """Return a path-bound worktree owner's recorded status, when present."""
    _task_id, state = _task_state_for_worktree(path)
    if state is None:
        return None
    status = state.get("status")
    return str(status) if status is not None else None


def _worktree_is_clean(path: Path) -> bool:
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=path,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if proc.returncode != 0:
        return False
    return not bool((proc.stdout or "").strip())


def _worktree_matches_origin_branch(path: Path, branch: str) -> bool:
    """True only when HEAD equals the live, exact origin branch tip."""
    head = _resolve_sha(path, "HEAD")
    try:
        result = _run_git_stdout(
            path, "ls-remote", "--exit-code", "--refs", "origin", f"refs/heads/{branch}",
        )
    except (OSError, subprocess.SubprocessError):
        return False
    if result is None:
        return False
    returncode, stdout = result
    lines = stdout.splitlines()
    return bool(
        head and returncode == 0 and len(lines) == 1
        and lines[0].split("\t") == [head, f"refs/heads/{branch}"]
    )


def _branch_holder_active_task_ids() -> set[str] | None:
    """Strict branch hand-off probe: missing/malformed tasks means unknown."""
    try:
        import urllib.request

        with urllib.request.urlopen(f"{_monitor_api_base_url()}/api/delegate/active", timeout=3) as response:
            data = json.loads(response.read().decode("utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
            return None
        tasks = data["tasks"]
        if any(not isinstance(task, dict) or not isinstance(task.get("task_id"), str) or not task["task_id"] for task in tasks):
            return None
        return {task["task_id"] for task in tasks}
    except (OSError, ValueError, TimeoutError):
        return None


# Terminal statuses that mean a prior dispatch no longer needs the worktree
# mounted. Includes failure modes — a crashed review worktree should not
# permanently pin a PR branch for follow-up dispatches (#5340). The same set
# decides which task records stop claiming a worktree for removal (#8610).
_RELEASED_TASK_STATUSES = worktree_claims.RELEASED_TASK_STATUSES


def _branch_holder_activity_reason(
    path: Path,
    *,
    task_id: str | None,
    task_state: dict[str, Any] | None,
    complete: bool = False,
    open_files: bool = False,
) -> str | None:
    """Return why a branch holder cannot be released while activity is possible.

    Unlike scheduled cleanup, a branch hand-off needs to support legacy
    holders whose task state has already been removed.  That is safe only when
    both of the reaper's independent liveness probes are available and empty:
    the active-dispatch API rules out an attached task and ``lsof`` rules out a
    process still using the checkout.  Probe failure is a refusal, not evidence
    of inactivity.
    """
    candidate_task_ids = [task_id] if task_id is not None else _task_status_candidates_for_worktree(path)
    if not candidate_task_ids:
        return "holder is outside the dispatch layout"

    unparseable = _bound_task_state_unparseable_reason(path)
    if unparseable is not None:
        return unparseable

    try:
        from scripts.orchestration import reap_worktrees

        try:
            active_ids = _branch_holder_active_task_ids() if complete else reap_worktrees._active_task_ids()
        except reap_worktrees._ActiveTaskProbeFailure as exc:
            _record_diagnostic(
                candidate_task_ids[0], _exception_cause("activity probe unavailable", exc), source="branch_hand_off",
            )
            active_ids = None
        live_cwds = reap_worktrees._live_cwd_paths(_REPO_ROOT)
    except Exception as exc:
        return f"activity probes unavailable ({type(exc).__name__})"
    if (complete or task_state is None) and active_ids is None:
        return "active-task probe unavailable"
    if live_cwds is None:
        return "process-CWD activity probe unavailable"
    if active_ids is not None:
        active_task_id = next((candidate for candidate in candidate_task_ids if candidate in active_ids), None)
        if active_task_id is not None:
            return f"active dispatch task-id={active_task_id}"
    if task_state is None:
        for candidate in candidate_task_ids:
            cand_state = _read_state(_state_path(candidate))
            if isinstance(cand_state, dict):
                cand_status = cand_state.get("status")
                if cand_status not in _RELEASED_TASK_STATUSES:
                    return f"active dispatch task-id={candidate}"
                if reap_worktrees._task_pid_alive(cand_state):
                    return f"live task PID for task-id={candidate}"
    elif reap_worktrees._task_pid_alive(task_state):
        return f"live task PID for task-id={candidate_task_ids[0]}"

    worktree = path.resolve()
    for cwd in live_cwds:
        try:
            resolved_cwd = cwd.resolve()
            resolved_cwd.relative_to(worktree)
        except (OSError, ValueError):
            continue
        return f"live process cwd={cwd}"
    if open_files:
        try:
            open_file_reason = reap_worktrees._open_file_activity_reason(path)
        except Exception as exc:
            return f"open-file activity probe unavailable ({type(exc).__name__})"
        if open_file_reason is not None:
            return open_file_reason
    return None


def _stale_branch_holder_releasable(path: Path, branch: str) -> tuple[bool, str]:
    """Return (ok, reason) for auto-releasing a worktree holding ``branch`` (#5340).

    HEAD must equal the live origin branch tip. A bound terminal owner may
    retain only regular allowlisted scratch for verified archival. A clean
    legacy holder needs complete known-empty activity probes too. Reaper
    reservations always win. This proof is read-only; preparation and removal
    run under the shared attachment/removal lock.
    """
    if reaper_lifecycle.is_reap_pending(_REPO_ROOT, path):
        return False, "reaper lifecycle reservation is pending"
    clean = _worktree_is_clean(path)
    if not _worktree_matches_origin_branch(path, branch):
        return False, "live_remote_tip_unknown_or_mismatch"
    unparseable = _bound_task_state_unparseable_reason(path)
    if unparseable is not None:
        return False, unparseable
    task_id, task_state = _task_state_for_worktree(path)
    # The open-file proof gates only scratch: an unavailable /proc proof must
    # not block a clean, pushed, terminal holder.
    activity = _branch_holder_activity_reason(
        path,
        task_id=task_id,
        task_state=task_state,
        complete=True,
        open_files=not clean,
    )
    if activity is not None:
        return False, activity
    status = str(task_state.get("status")) if task_state and task_state.get("status") is not None else None
    if task_state is None:
        if not clean:
            return False, "scratch_owner_unknown"
    elif status not in _RELEASED_TASK_STATUSES:
        return False, f"task still active or invalid status (status={status})"
    try:
        from scripts.fleet.ignored_task_output import resolve_worktree_record
        from scripts.fleet.regenerable_output import branch_holder_scratch_inventory

        branch_holder_scratch_inventory(path, primary=_REPO_ROOT)
        if not clean:
            if worktree_claims.checked_out_branch(path) != branch:
                return False, "holder_branch_unknown_or_changed"
            try:
                record_path, owner = resolve_worktree_record(path, tasks_dir(), repo_root=_REPO_ROOT, publish_cache=False)
            except ValueError:
                return False, "scratch_owner_ambiguous"
            if record_path is None or owner.get("task_id") != task_id or owner.get("status") not in _RELEASED_TASK_STATUSES:
                return False, "scratch_owner_ambiguous"
    except Exception as exc:
        kind = str(exc) if isinstance(exc, ValueError) and re.fullmatch(r"[a-z_]+", str(exc)) else "unknown"
        return False, f"scratch_inventory_refused:{type(exc).__name__}:{kind}"
    if task_state is None:
        return True, "clean+synced; task record absent; activity probes empty"
    return True, f"{'clean' if clean else 'archivable-scratch'}+synced; task status={status}"


def _prepare_branch_holder_release(path: Path, branch: str) -> tuple[bool, str]:
    """Archive/recheck/unlink scratch inside the common remover's held lock."""
    ok, detail = _stale_branch_holder_releasable(path, branch)
    if not ok:
        return ok, detail
    try:
        from scripts.fleet import ignored_task_output
        from scripts.fleet.regenerable_output import branch_holder_scratch_inventory
        from scripts.orchestration import worktree_artifacts

        inventory = branch_holder_scratch_inventory(path, primary=_REPO_ROOT)
        scratch = [entry for entry in inventory["paths"] if entry["kind"] == "scratch"]
        if not scratch:
            return True, detail
        head = _resolve_sha(path, "HEAD")
        record_path, owner = ignored_task_output.resolve_worktree_record(
            path, tasks_dir(), repo_root=_REPO_ROOT, publish_cache=False,
        )
        if record_path is None:
            return False, "scratch_owner_unknown"
        ok, refusal, receipt = ignored_task_output.preserve_worktree_artifacts(
            path, primary=_REPO_ROOT, tasks_dir=tasks_dir(), task_id=owner["task_id"],
            repo_root=_REPO_ROOT, extra_files=[entry["path"] for entry in scratch],
        )
        if not ok or receipt is None:
            return False, refusal or "archive_receipt_missing"
        archive_receipt = {
            key: receipt[key] for key in ("manifest_path", "content_sha256", "retrieval_proof_sha256")
        }
        # Publish the locator even if the final recheck/removal later refuses.
        print("Branch holder archive: " + json.dumps(archive_receipt, sort_keys=True), file=sys.stderr)

        def recheck() -> None:
            claims = worktree_claims.active_worktree_claim_refusal(path, tasks_dir=tasks_dir(), repo_root=_REPO_ROOT)
            if claims is not None:
                raise ValueError(claims)
            valid, reason = _stale_branch_holder_releasable(path, branch)
            current_path, current_owner = ignored_task_output.resolve_worktree_record(
                path, tasks_dir(), repo_root=_REPO_ROOT, publish_cache=False,
            )
            if not valid:
                raise ValueError(reason)
            if (
                current_path != record_path or current_owner.get("task_id") != owner.get("task_id")
                or current_owner.get("run_nonce") != owner.get("run_nonce")
                or _resolve_sha(path, "HEAD") != head
                or branch_holder_scratch_inventory(path, primary=_REPO_ROOT) != inventory
            ):
                raise ValueError("holder_changed_before_delete")
            ignored_task_output.verify_retrieval(_REPO_ROOT, receipt)

        # Retire only receipt-covered entries, including ignored output, so
        # the common boundary does not archive it again. Its regenerable
        # output exemptions remain outside this explicit unlink pass.
        archived_names = {entry["path"] for entry in receipt["paths"]}
        archived = [entry for entry in inventory["paths"] if entry["path"] in archived_names]
        worktree_artifacts.unlink_archived_regular_files(path, archived, recheck=recheck)
        return True, detail + "; archive=" + json.dumps(archive_receipt, sort_keys=True)
    except Exception as exc:
        if isinstance(exc, worktree_artifacts.ArtifactReleaseRefusal):
            recovery = dict(exc.receipt)
            try:
                recovery["receipt_recorded"] = ignored_task_output._update_bound_task_record(
                    record_path, path, {"branch_holder_release_refusal": exc.receipt},
                    repo_root=_REPO_ROOT, expected_record=owner,
                )
            except (OSError, ValueError):
                recovery["receipt_recorded"] = False
            return False, "scratch_release_refused:" + json.dumps(recovery, sort_keys=True)
        kind = str(exc) if isinstance(exc, ValueError) and re.fullmatch(r"[a-z_]+", str(exc)) else "unknown"
        return False, f"scratch_release_refused:{type(exc).__name__}:{kind}"


_REVIEW_SERIES_RE = re.compile(r"^(?P<stem>review-.+)-r(?P<round>[1-9][0-9]*)$")


def _review_series(task_id: str) -> tuple[str, int] | None:
    """Return ``(stem, round)`` for a review task, or None for other tasks.

    ``review-gpt6-routing`` is round 0. ``review-gpt6-routing-r7`` is round 7
    of that same series. A later round replaces every earlier checkout.
    """
    name = task_id.strip().strip("/")
    if not name.startswith("review-"):
        return None
    match = _REVIEW_SERIES_RE.fullmatch(name)
    if match is None:
        return name, 0
    return match.group("stem"), int(match.group("round"))


def _dispatch_worktree_components() -> list[tuple[Path, str]]:
    """Return ``(path, task component)`` for registered dispatch worktrees."""
    try:
        proc = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if proc.returncode != 0:
        return []
    found: list[tuple[Path, str]] = []
    current: Path | None = None
    for line in [*(proc.stdout or "").splitlines(), ""]:
        if not line:
            if current is not None:
                parts = _dispatch_layout_parts(current)
                if parts is not None:
                    found.append((current, parts[1]))
            current = None
        elif line.startswith("worktree "):
            current = Path(line.removeprefix("worktree ").strip())
    return found


def _live_origin_branch_shas(cwd: Path, branches: list[str]) -> dict[str, str] | None:
    """Return live ``refs/heads/<name>`` SHAs from one batched ``ls-remote``.

    ``None`` means the lookup itself failed (git error, unreachable origin,
    timeout) and proves nothing. A branch absent from a successful mapping is
    genuinely gone from the remote; its local tracking ref is a stale cache.
    """
    if not branches:
        return {}
    patterns = sorted({f"refs/heads/{branch}" for branch in branches})
    try:
        proc = subprocess.run(
            ["git", "ls-remote", "origin", *patterns],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    live: dict[str, str] = {}
    for line in (proc.stdout or "").splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        sha, ref = parts
        if ref.startswith("refs/heads/"):
            live[ref.removeprefix("refs/heads/")] = sha
    return live


def _commit_is_durably_contained(cwd: Path, sha: str) -> bool:
    """True when ``sha`` is on ``origin/main`` or a live origin branch.

    A local ``refs/remotes/origin/*`` ref is a cache, not proof: the remote
    branch may already be deleted while the tracking ref still contains the
    tip. Every tracking-ref candidate is re-verified against the live remote;
    containment counts only when the live SHA equals the cached tracking SHA
    or has ``sha`` as an ancestor. Any git error, a missing remote ref, or an
    unreadable live SHA is not containment. A clean worktree is not enough:
    its commits may exist only in that checkout.
    """
    try:
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", sha, "origin/main"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if ancestor.returncode == 0:
        return True
    if ancestor.returncode != 1:
        return False
    try:
        listed = subprocess.run(
            [
                "git",
                "for-each-ref",
                "--contains",
                sha,
                "--format=%(refname)%09%(objectname)",
                "refs/remotes/origin",
            ],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if listed.returncode != 0:
        return False
    candidates: list[tuple[str, str]] = []
    for line in (listed.stdout or "").splitlines():
        parts = line.split("\t")
        if len(parts) != 2:
            continue
        ref, tracking_sha = parts
        if ref.startswith("refs/remotes/origin/"):
            candidates.append((ref.removeprefix("refs/remotes/origin/"), tracking_sha))
    live = _live_origin_branch_shas(cwd, [name for name, _ in candidates])
    if live is None:
        return False
    for name, tracking_sha in candidates:
        live_sha = live.get(name)
        if live_sha is None:
            continue
        if live_sha == tracking_sha:
            return True
        try:
            contains = subprocess.run(
                ["git", "merge-base", "--is-ancestor", sha, live_sha],
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False,
                env=_sanitized_git_env(),
                timeout=DEFAULT_GIT_TIMEOUT_S,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if contains.returncode == 0:
            return True
    return False


def _worktree_head_is_durably_contained(path: Path) -> bool:
    sha = _resolve_sha(path, "HEAD")
    if not sha:
        return False
    return _commit_is_durably_contained(path, sha)


def _superseded_review_releasable(path: Path) -> tuple[bool, str]:
    """A finished review checkout can go once a later round of the same series starts.

    Cleanliness and liveness are required. The checkout does not have to match
    ``origin/<branch>``: a detached earlier round no longer holds the branch,
    which is why the branch-holder release never saw it. Removal still requires
    a separate containment proof of HEAD; this predicate does not provide it.
    """
    if reaper_lifecycle.is_reap_pending(_REPO_ROOT, path):
        return False, "reaper lifecycle reservation is pending"
    if not _worktree_is_clean(path):
        return False, "dirty"
    unparseable = _bound_task_state_unparseable_reason(path)
    if unparseable is not None:
        return False, unparseable
    task_id, task_state = _task_state_for_worktree(path)
    activity = _branch_holder_activity_reason(
        path,
        task_id=task_id,
        task_state=task_state,
    )
    if activity is not None:
        return False, activity
    if task_state is None:
        return True, "clean; task record absent; activity probes empty"
    status = str(task_state.get("status") or "")
    if status in _RELEASED_TASK_STATUSES:
        return True, f"clean; task status={status}"
    return False, f"task still active or invalid status (status={status})"


def _superseded_review_release_proof(path: Path) -> tuple[bool, str]:
    """Return ``(ok, reason)`` for removing an earlier review round's checkout.

    The checkout must be releasable (:func:`_superseded_review_releasable`)
    and its HEAD durably contained in main or a remote ref.
    """
    ok, reason = _superseded_review_releasable(path)
    if not ok:
        return False, reason
    if not _worktree_head_is_durably_contained(path):
        return False, "tip not contained in main or a remote ref"
    return True, reason


def _release_superseded_review_worktrees(
    task_id: str,
    *,
    dry_run: bool,
    review_dependencies: Sequence[tuple[str, Path]] = (),
) -> list[Path]:
    """Remove earlier rounds of this review series before the new checkout is made.

    Each removal goes through :func:`_remove_dispatch_worktree`, which runs the
    release proof while holding the earlier round's worktree lock (#8610).
    Earlier rounds holding attempt dependencies are kept without release (#9417).
    """
    series = _review_series(task_id)
    if series is None:
        return []
    stem, current_round = series
    candidates: list[tuple[Path, str]] = []
    for path, component in _dispatch_worktree_components():
        earlier = _review_series(component)
        if earlier is None:
            continue
        earlier_stem, earlier_round = earlier
        if earlier_stem != stem or earlier_round >= current_round:
            continue
        candidates.append((path, component))
    released: list[Path] = []
    for path, component in candidates:
        dependencies = _review_attempt_dependency_names(path, review_dependencies)
        if dependencies:
            print(
                f"ℹ️  earlier review {path} kept: review dependency ({', '.join(dependencies)})",
                file=sys.stderr,
            )
            continue
        if dry_run:
            ok, reason = _superseded_review_release_proof(path)
            if not ok:
                print(f"ℹ️  earlier review {path} kept ({reason})", file=sys.stderr)
                continue
            print(
                f"🌲 dry-run: would remove superseded review worktree {path} ({reason})",
                file=sys.stderr,
            )
            released.append(path)
            continue
        removal = _remove_dispatch_worktree(
            path,
            reason="superseded by a later review round",
            owner_task_id=None,
            releasable=functools.partial(_superseded_review_release_proof, path),
        )
        if removal["action"] == "skipped":
            print(f"ℹ️  earlier review {path} kept ({removal['reason']})", file=sys.stderr)
            continue
        if removal["action"] != "removed":
            print(
                f"⚠️  failed to remove superseded review worktree {path}: {removal['error']}",
                file=sys.stderr,
            )
            continue
        print(f"🌲 removed superseded review worktree {path} ({removal['reason']})", file=sys.stderr)
        # Delete only the local branch named for this review round.
        scratch_branch = removal["branch"]
        if scratch_branch is not None and scratch_branch.split("/")[-1] == component:
            _delete_local_branch(scratch_branch)
        released.append(path)
    return released


def _delete_local_branch(branch: str) -> None:
    if any(item == branch for item in _checked_out_branch_names()):
        print(f"ℹ️  kept local branch {branch}; another checkout still has it", file=sys.stderr)
        return
    sha = _resolve_sha(_REPO_ROOT, f"refs/heads/{branch}")
    if not sha or not _commit_is_durably_contained(_REPO_ROOT, sha):
        print(
            f"ℹ️  kept local branch {branch}; tip not contained in main or a remote ref",
            file=sys.stderr,
        )
        return
    try:
        proc = subprocess.run(
            ["git", "branch", "-D", branch],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(
            f"⚠️  failed to delete local branch {branch}: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return
    if proc.returncode != 0:
        print(
            f"⚠️  failed to delete local branch {branch}: {_format_process_failure(proc)}",
            file=sys.stderr,
        )
        return
    print(f"🌲 deleted superseded review branch {branch}", file=sys.stderr)


def _checked_out_branch_names() -> list[str]:
    names: list[str] = []
    try:
        proc = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return names
    for line in (proc.stdout or "").splitlines():
        if line.startswith("branch refs/heads/"):
            names.append(line.removeprefix("branch refs/heads/").strip())
    return names


def _review_attempt_worktree_dependencies(args: argparse.Namespace) -> tuple[tuple[str, Path], ...]:
    """Locate attempt dependencies for retention only; prompt admission still validates the record."""
    from scripts.review.render_contract import RENDER_RECORD_KEY, render_record_path

    manifest = getattr(args, "review_attempt", None)
    if not manifest:
        return ()
    paths = [("manifest", Path(manifest))]
    prompt_file = getattr(args, "prompt_file", None)
    if prompt_file:
        try:
            reads = json.loads(render_record_path(Path(prompt_file)).read_bytes())
            record = reads.get(RENDER_RECORD_KEY)
        except (OSError, ValueError, AttributeError):
            record = None  # Existing admission refuses unreadable or malformed render records.
        if isinstance(record, dict):
            for name in ("input_root", "render_checkout"):
                value = record.get(name)
                if isinstance(value, str) and value:
                    paths.append((name, Path(value)))
    # Retain the supplied location as well as its target: removing a checkout
    # containing a symlink would still break subsequent reads via that name.
    return tuple(
        dict.fromkeys((name, location) for name, path in paths for location in (path.absolute(), path.resolve()))
    )


def _review_attempt_dependency_names(path: Path, dependencies: Sequence[tuple[str, Path]]) -> list[str]:
    """Name dependencies whose supplied or resolved locations lie in this checkout."""
    if not dependencies:
        return []
    roots = (path.absolute(), path.resolve())
    return sorted({name for name, location in dependencies if any(location.is_relative_to(root) for root in roots)})


def _refuse_review_attempt_branch_holders(
    branch: str | None,
    holders: Sequence[Path],
    dependencies: Sequence[tuple[str, Path]],
) -> None:
    """Refuse cleanup that can delete this attempt's dependencies (#9388, #9417)."""
    if not dependencies:
        return
    for holder in holders:
        conflicts = _review_attempt_dependency_names(holder, dependencies)
        if conflicts:
            context = f"branch {branch!r} holder" if branch is not None else "superseded review worktree"
            raise ValueError(
                "review_attempt_branch_holder_conflict: "
                f"{context} {holder} contains this attempt's {', '.join(conflicts)}; "
                "refusing to release it; render from a separate retained worktree at the exact commit and retry (#9388)"
            )


def _release_stale_branch_holders(
    *,
    branch: str,
    holders: list[Path],
    dry_run: bool,
    review_dependencies: Sequence[tuple[str, Path]] = (),
) -> list[Path]:
    """Remove releasable holders of ``branch`` so a new worktree can attach.

    Returns paths successfully released (or that would be released in dry-run).
    Non-releasable holders are left in place for the caller to refuse on. Each
    removal goes through :func:`_remove_dispatch_worktree`, which runs
    :func:`_stale_branch_holder_releasable` while holding the holder's
    worktree lock (#8610).
    Attempt dependencies are checked across all holders before any removal (#9388).
    """
    _refuse_review_attempt_branch_holders(branch, holders, review_dependencies)
    released: list[Path] = []
    for path in holders:
        if dry_run:
            ok, reason = _stale_branch_holder_releasable(path, branch)
            if not ok:
                print(
                    f"ℹ️  branch {branch!r} held by {path} not auto-releasable ({reason})",
                    file=sys.stderr,
                )
                continue
            print(
                f"🌲 dry-run: would release stale branch holder {path} ({reason})",
                file=sys.stderr,
            )
            released.append(path)
            continue
        # No force: if the tree went dirty after the cleanliness check
        # (dirty-TOCTOU), or a process adopted the holder as cwd after the
        # live-CWD probe (live-cwd TOCTOU — accepted residual), git refuses
        # removal and we leave the holder mounted (#5708 CF, #7242).
        removal = _remove_dispatch_worktree(
            path,
            reason=f"stale holder of {branch!r}",
            owner_task_id=None,
            releasable=functools.partial(_prepare_branch_holder_release, path, branch),
        )
        if removal["action"] == "skipped":
            print(
                f"ℹ️  branch {branch!r} held by {path} not auto-releasable ({removal['reason']})",
                file=sys.stderr,
            )
            continue
        if removal["action"] != "removed":
            print(
                f"⚠️  failed to release stale branch holder {path}: {removal['error']}",
                file=sys.stderr,
            )
            continue
        print(
            f"🌲 released stale branch holder {path} ({removal['reason']}) so {branch!r} can attach to a new dispatch worktree",
            file=sys.stderr,
        )
        released.append(path)
    return released


def _resolve_sha(path: Path, ref: str = "HEAD") -> str | None:
    """Return the commit SHA at ``ref`` in ``path``, or None if unresolvable."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", ref],
            cwd=path,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    sha = (proc.stdout or "").strip()
    return sha or None


def _record_final_branch_head(state: dict[str, Any]) -> None:
    """Capture the current HEAD when a terminal task still owns a worktree."""
    raw_path = state.get("worktree_path")
    if isinstance(raw_path, str) and Path(raw_path).is_dir():
        state["final_branch_head_commit"] = _resolve_sha(Path(raw_path))


def _mark_crashed_task(state_path: Path, state: dict[str, Any], *, source: str) -> None:
    """Persist a zombie correction with the worktree's final branch head."""
    current, _changed = mark_dead_worker_terminal(
        state_path,
        state,
        source=source,
        terminal_status="crashed",
        allowed_statuses=("running", "spawning"),
        pid_alive=_pid_alive,
        resolve_head=_resolve_sha,
        write=_write_record_unlocked,
    )
    state.clear()
    state.update(_hydrate_read_only_checkout_snapshots(_public_record(current)[0]))


def _heal_dead_task(state_path: Path, state: dict[str, Any], *, source: str) -> None:
    """Mark an active record ``crashed`` when the process that owns it is gone.

    A worker record's owner is its pid. A worktree-prep record (``pid: null``
    while dispatch runs ``git worktree add``) is owned by the dispatcher
    recorded in ``worktree_prep``; if the dispatcher died, no pid will ever be
    written, so it is marked ``crashed`` with reason
    ``dispatch_died_during_worktree_prep`` (#8663). An admission hold is
    owned by the dispatcher recorded in ``admission_hold`` and is marked
    ``crashed`` with reason ``dispatch_died_after_admission`` (#8717).
    """
    if state.get("status") not in ("running", "spawning"):
        return
    pid = state.get("pid")
    if pid and not _pid_alive(int(pid)):
        _mark_crashed_task(state_path, state, source=source)
    elif worktree_prep.is_orphaned_prep_record(state):
        current, _changed = mark_orphaned_worktree_prep_crashed(
            state_path,
            state,
            source=source,
            is_orphaned=worktree_prep.is_orphaned_prep_record,
            write=_write_record_unlocked,
        )
        state.clear()
        state.update(_public_record(current)[0])
    elif dispatch_admission.is_orphaned_admission_hold(state):
        current, _changed = mark_orphaned_admission_hold_crashed(
            state_path,
            state,
            source=source,
            is_orphaned=dispatch_admission.is_orphaned_admission_hold,
            reason=dispatch_admission.ORPHANED_HOLD_REASON,
            write=_write_record_unlocked,
        )
        state.clear()
        state.update(_public_record(current)[0])


# Exit code for a dispatch refused by host admission: retryable once a worker
# finishes or the host recovers, unlike exit 2 (invalid request).
_ADMISSION_REFUSED_EXIT = 3


def _evaluate_dispatch_admission(
    mode: str,
    *,
    sweep: bool,
    thresholds: dispatch_admission.Thresholds | None = None,
) -> dispatch_admission.AdmissionDecision:
    """Host admission for a ``mode`` dispatch (#8645 part A).

    With ``sweep`` every running/spawning record whose owner is gone (a dead
    worker pid, or a pid-less worktree reservation or admission hold whose
    dispatcher died) is marked ``crashed`` first by the healer ``status``,
    ``wait``, ``list`` and reconcile use, so it never holds a slot and never
    sits active until someone probes it (#8717).
    """
    return dispatch_admission.evaluate(
        mode,
        tasks_dir(),
        pid_alive=_pid_alive,
        on_dead=(lambda path, state: _heal_dead_task(path, state, source="admission")) if sweep else None,
        thresholds=thresholds,
    )


def _report_dispatch_admission(
    decision: dispatch_admission.AdmissionDecision, *, force_reason: str | None
) -> int | None:
    """Print the admission outcome; return the exit code when dispatch must stop."""
    if decision.exempt:
        return None
    if decision.admitted:
        print(f"🚦 dispatch admission: admitted — {decision.summary()}", file=sys.stderr)
        return None
    if force_reason is not None:
        print(
            f"⚠️  dispatch admission overridden by --force-admission ({force_reason!r}): {'; '.join(decision.failures)}",
            file=sys.stderr,
        )
        return None
    print(f"❌ {decision.refusal_line()}", file=sys.stderr)
    return _ADMISSION_REFUSED_EXIT


def _tracking_remote_for_current_branch(worktree: Path) -> str | None:
    """Return the configured upstream remote for the checked-out branch.

    A reused ``--cwd`` worktree can belong to a private repository whose
    canonical remote is not named ``origin``.  Its checked-out dispatch branch
    is the narrowest local source for that repository identity: unlike scanning
    every configured remote, it cannot accidentally select an unrelated mirror.
    """
    try:
        branch = _current_branch(worktree)
    except OSError:
        return None
    if not branch or branch == "HEAD":
        return None
    try:
        proc = subprocess.run(
            ["git", "config", "--get", f"branch.{branch}.remote"],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    remote = (proc.stdout or "").strip()
    return remote or None


def _commit_count_refs(worktree: Path, base_ref: str) -> tuple[str, ...]:
    """Return ordered, local-only base-ref candidates for finalization.

    ``origin/<base>`` remains the canonical candidate for ordinary dispatches.
    If it is unavailable, count against the base branch on the checked-out
    branch's upstream remote before falling back to the local base.  The remote
    candidate must win because a reused checkout can have a stale local branch.
    The remote fallback is required for private/secondary remotes, where a
    pushed dispatch branch may track ``private/<task>`` and the shared checkout
    intentionally has neither ``origin/<base>`` nor a current local ``<base>``
    branch.
    """
    candidates = [base_ref]
    _remote, separator, branch = base_ref.partition("/")
    if not separator:
        branch = base_ref

    tracking_remote = _tracking_remote_for_current_branch(worktree)
    if tracking_remote and branch:
        candidates.append(f"{tracking_remote}/{branch}")
    if separator:
        candidates.append(branch)
    return tuple(dict.fromkeys(candidate for candidate in candidates if candidate))


def _recorded_base_sha(record: Mapping[str, Any]) -> str | None:
    """The commit the task's worktree was branched from, as its record stored it, or None."""
    sha = record.get("worktree_base_sha")
    return sha.strip() if isinstance(sha, str) and sha.strip() else None


def _run_count_ahead(worktree: Path, base: str) -> tuple[int | None, bool]:
    """``(count, base_missing)`` for ``git rev-list --count <base>..HEAD``.

    ``base_missing`` is True only when git ran and rejected ``base`` (the ref
    does not resolve): the one case where trying another base is sound. A git
    that cannot run, or output that is not a number, is unknown outright.
    """
    try:
        proc = subprocess.run(
            ["git", "rev-list", "--count", f"{base}..HEAD"],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None, False
    if proc.returncode != 0:
        # Permit fallback only on confirmed absence (exit 1 from rev-parse).
        # Unavailable verification (None), operational error (!= 1), or ref present (0) fails closed.
        ref_check = _run_git_stdout(worktree, "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}")
        if ref_check is not None and ref_check[0] == 1:
            return None, True
        return None, False
    try:
        return int((proc.stdout or "").strip()), False
    except ValueError:
        return None, False


def _is_ancestor_of_head(worktree: Path, sha: str) -> bool:
    """Whether ``sha`` names a commit in the repository that is an ancestor of ``HEAD``."""
    try:
        proc = subprocess.run(
            ["git", "merge-base", "--is-ancestor", f"{sha}^{{commit}}", "HEAD"],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0


def _run_git_stdout(worktree: Path, *args: str) -> tuple[int, str] | None:
    """``(returncode, stdout)`` of a git command, or None when git could not run."""
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return proc.returncode, proc.stdout or ""


def _count_real_changes_ahead(worktree: Path, base: str) -> tuple[int | None, bool]:
    """``(count, base_missing)`` of ``<base>..HEAD``, or 0 when merging ``HEAD`` into ``base`` changes nothing.

    ``<default>..HEAD`` overcounts as delivery proof: an empty commit, a merge of
    the default branch, a cherry-pick of a change it already has, or a squash of
    work it already holds is ahead of a stale or squash-merged base yet adds
    nothing (#9451). Rather than approximate that per commit shape, ask git the
    exact question: ``git merge-tree --write-tree <base> HEAD`` is the tree a
    merge would produce, so when it equals ``base``'s own tree nothing new is
    delivered. A different tree, or a conflict (exit status 1, which a real
    change colliding with ``base`` produces), is a delivery. Any other failure,
    including a git without ``--write-tree`` or history too shallow to merge, is
    ``(None, False)`` so the caller fails closed.
    """
    ahead, base_missing = _run_count_ahead(worktree, base)
    if ahead is None or ahead == 0:
        return ahead, base_missing
    base_tree = _run_git_stdout(worktree, "rev-parse", "--verify", "--quiet", f"{base}^{{tree}}")
    if base_tree is None or base_tree[0] != 0 or not base_tree[1].strip():
        return None, False
    merged = _run_git_stdout(worktree, "merge-tree", "--write-tree", "--no-messages", base, "HEAD")
    if merged is None or merged[0] not in (0, 1):
        return None, False
    if merged[0] == 1:
        return ahead, False
    merged_tree = merged[1].strip().splitlines()[0] if merged[1].strip() else ""
    if not merged_tree:
        return None, False
    return (0 if merged_tree == base_tree[1].strip() else ahead), False


def _count_commits_ahead_without_named_base(worktree: Path, base_ref: str, base_sha: str | None) -> int | None:
    """Count the branch's commits when the named base ref is gone everywhere (#9451).

    A base branch deleted after it merged leaves nothing to count against, which
    recorded a pushed fix as ``commit_count_unknown``. Fall back, in order, to:

    1. the commit the worktree was branched from (``base_sha``, as the dispatch
       recorded it), when it is an ancestor of ``HEAD``;
    2. the merge base of ``HEAD`` with the default branch (``origin/main``, then
       the upstream remote's ``main``), which is what ``<default>..HEAD`` counts.

    A SHA that does not resolve, or is not an ancestor of ``HEAD`` (the branch
    was rebased off it), is skipped rather than trusted. None when no base
    resolves, so the caller still fails closed.

    The recorded commit is the exact point the worktree started from, so its
    plain ``<sha>..HEAD`` count is exact. The default branch is only a proxy
    for the lost base and may already hold the work, so its commits count only
    when merging ``HEAD`` into it would change it (``_count_real_changes_ahead``).
    """
    for candidate, exact in _fallback_base_candidates(worktree, base_sha):
        count_ahead = _run_count_ahead if exact else _count_real_changes_ahead
        count, base_missing = count_ahead(worktree, candidate)
        if count is not None:
            print(
                f"⚠️  base {base_ref!r} is gone; counted commits ahead against {candidate!r} instead",
                file=sys.stderr,
            )
            return count
        if not base_missing:
            return None
    return None


def _fallback_base_candidates(worktree: Path, base_sha: str | None) -> list[tuple[str, bool]]:
    """Return ordered ``(ref_or_sha, is_exact_recorded_commit)`` candidates when the named base is gone (#9451, #9489).

    1. The recorded commit the worktree was branched from (``base_sha``), when
       it is reachable and an ancestor of ``HEAD``;
    2. The default branch (``origin/main``, then the upstream remote's ``main``).

    The recorded commit is exact. The default branch is only a proxy for the lost
    base: when the base was squash-merged, the default branch's merge-base
    predates the base branch, so diffs and commit counts can include the base
    branch's own commits (an overcount). Testing the recorded commit first avoids
    this whenever ``worktree_base_sha`` was preserved.
    """
    candidates: list[tuple[str, bool]] = []
    if base_sha and _is_ancestor_of_head(worktree, base_sha):
        candidates.append((base_sha, True))
    default_refs = ["origin/main"]
    tracking_remote = _tracking_remote_for_current_branch(worktree)
    if tracking_remote:
        default_refs.append(f"{tracking_remote}/main")
    candidates.extend((ref, False) for ref in dict.fromkeys(default_refs))
    return candidates


def _run_merge_base(worktree: Path, base: str) -> tuple[str | None, bool]:
    """``(merge_base_sha, base_missing)`` for ``git merge-base <base> HEAD`` (#9489).

    ``base_missing`` is True only when git ran and rejected ``base`` (the ref or
    SHA does not resolve): the one case where trying another base candidate is
    sound. A present base that has no common ancestor with HEAD or whose
    computation failed fails closed ((None, False)).
    """
    sha, base_missing, _why = _run_merge_base_detail(worktree, base)
    return sha, base_missing


def _run_merge_base_detail(worktree: Path, base: str) -> tuple[str | None, bool, _TypedCause | None]:
    """:func:`_run_merge_base` plus why it failed, typed, with git's own error from this run (#9878)."""
    command = ["git", "merge-base", base, "HEAD"]
    try:
        proc = subprocess.run(
            command,
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, False, _exception_cause("merge_base_unresolved", exc, command=command)
    if proc.returncode == 0:
        sha = (proc.stdout or "").strip()
        if sha:
            return sha, False, None
        return (
            None,
            False,
            _TypedCause("merge_base_unresolved", "merge-base", 0, diagnostic=f"{' '.join(command)} printed no commit"),
        )
    why = _git_cause("merge_base_unresolved", proc)
    if proc.returncode == 1 and not (proc.stderr or proc.stdout or "").strip():
        why = dataclasses.replace(why, diagnostic=f"{' '.join(command)} failed (exit 1): no common ancestor")
    ref_check = _run_git_stdout(worktree, "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}")
    if ref_check is not None and ref_check[0] == 1:
        # Confirmed absence: git rev-parse ran and confirmed the ref does not exist (exit 1).
        return None, True, why
    # Either ref exists (0), verification was unavailable (None), or failed operationally (!= 1).
    # Fail closed in all these cases: do NOT treat as missing and do NOT fall back.
    return None, False, why


def _resolve_merge_base(worktree: Path, base_ref: str, base_sha: str | None = None) -> str | None:
    """Return the merge-base SHA between base_ref and HEAD, or a fallback if base_ref was deleted (#9489).

    First tries eligible candidates for base_ref (_commit_count_refs).
    When all candidates for base_ref are missing (the base branch was deleted
    after merging), falls back to:
    1. the recorded base commit (base_sha) when reachable and an ancestor of HEAD;
    2. the default-branch merge-base (origin/main).

    When the base was squash-merged, the default branch fallback can overcount
    changes because the merge base with main is older than the task's starting
    point; the recorded base commit avoids this whenever available.

    Returns None if no merge base can be resolved (failing closed).
    """
    return _resolve_merge_base_detail(worktree, base_ref, base_sha)[0]


def _resolve_merge_base_detail(
    worktree: Path, base_ref: str, base_sha: str | None = None
) -> tuple[str | None, _TypedCause | None]:
    """``(merge_base, None)`` as :func:`_resolve_merge_base` resolves it, or ``(None, why)`` (#9878).

    ``why`` is ``merge_base_unresolved`` with the last attempt's exit status;
    its diagnostic carries each failed attempt's own command and git error,
    from the attempt that failed: nothing is run again to explain a failure.
    """
    failures: list[str] = []
    last: _TypedCause | None = None

    def unresolved() -> tuple[None, _TypedCause]:
        detail = "; ".join(failures) or f"no base candidate for {base_ref!r}"
        if last is None:
            return None, _TypedCause("merge_base_unresolved", "merge-base", diagnostic=detail)
        return None, dataclasses.replace(last, diagnostic=f"no merge base with {base_ref!r}: {detail}")

    for candidate in _commit_count_refs(worktree, base_ref):
        sha, base_missing, why = _run_merge_base_detail(worktree, candidate)
        if sha is not None:
            return sha, None
        last = why or last
        failures.append(why.diagnostic if why else candidate)
        if not base_missing:
            return unresolved()

    fallbacks = _fallback_base_candidates(worktree, base_sha)
    if base_sha and all(candidate != base_sha for candidate, _exact in fallbacks):
        failures.append(f"the recorded base commit {base_sha} is not an ancestor of HEAD")
    for candidate, _exact in fallbacks:
        sha, base_missing, why = _run_merge_base_detail(worktree, candidate)
        if sha is not None:
            print(
                f"⚠️  base {base_ref!r} is gone; resolved merge-base against {candidate!r} instead",
                file=sys.stderr,
            )
            return sha, None
        last = why or last
        failures.append(why.diagnostic if why else candidate)
        if not base_missing:
            return unresolved()

    return unresolved()


def _count_commits_ahead(worktree: Path, base_ref: str, base_sha: str | None = None) -> int | None:
    """Return commits on HEAD not reachable from an eligible base ref, or None.

    ``None`` means "cannot count", and a vanished worktree is exactly that: on
    2026-07-25 a dispatch whose worktree disappeared mid-run raised
    FileNotFoundError out of here, which killed the finalize path before it
    could write a terminal status and left the task reading ``running`` with a
    dead pid — invisible to every settle-loop watching it. The sibling
    ``_worktree_is_dirty`` already treated OSError as unknown; this is the same
    contract, and callers already fail closed on ``None``.

    When every named candidate is gone (the base branch was deleted after it
    merged, #9451), the count falls back to the recorded ``base_sha`` and then
    the default-branch merge base; a present base is always measured first,
    unchanged.
    """
    for candidate in _commit_count_refs(worktree, base_ref):
        count, base_missing = _run_count_ahead(worktree, candidate)
        if count is not None:
            return count
        if not base_missing:
            return None
    return _count_commits_ahead_without_named_base(worktree, base_ref, base_sha)


def _unpushed_commit_refs(worktree: Path, branch: str) -> tuple[str, ...]:
    """Return ordered remote-tracking ref candidates for unpushed-commit checks."""
    clean_branch = branch.removeprefix("refs/heads/").removeprefix("refs/remotes/")
    if clean_branch.startswith("origin/"):
        clean_branch = clean_branch.removeprefix("origin/")
    if not clean_branch:
        return ()

    candidates: list[str] = [f"{clean_branch}@{{upstream}}", "@{upstream}"]
    tracking_remote = _tracking_remote_for_current_branch(worktree)
    if tracking_remote:
        candidates.append(f"{tracking_remote}/{clean_branch}")
    candidates.append(f"origin/{clean_branch}")
    return tuple(dict.fromkeys(candidate for candidate in candidates if candidate))


def _count_unpushed_commits(worktree: Path, branch: str) -> int | None:
    """Return commits on HEAD not reachable from the branch's remote, or None.

    ``None`` means cannot count or no remote tracking ref exists. Fail closed
    on unknown or unpushed commits (#7311).
    """
    for candidate in _unpushed_commit_refs(worktree, branch):
        try:
            proc = subprocess.run(
                ["git", "rev-list", "--count", f"{candidate}..HEAD"],
                cwd=worktree,
                capture_output=True,
                text=True,
                check=False,
                env=_sanitized_git_env(),
                timeout=DEFAULT_GIT_TIMEOUT_S,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if proc.returncode != 0:
            continue
        try:
            return int((proc.stdout or "").strip())
        except ValueError:
            return None
    return None


def _commit_count_base_ref(worktree: Path, base_branch: str) -> str:
    """Keep an explicit available non-origin remote base for finalization."""
    explicit_ref = base_branch.removeprefix("refs/remotes/")
    if "/" in explicit_ref and _resolve_sha(worktree, explicit_ref) is not None:
        return explicit_ref
    return _origin_base_ref(base_branch)


def _origin_base_ref(base_branch: str) -> str:
    """Return the remote ref used for ahead-count checks."""
    if base_branch.startswith("origin/"):
        return base_branch
    return f"origin/{_base_branch_name(base_branch)}"


def _base_branch_name(base_branch: str) -> str:
    """Return a PR base branch name without the remote prefix.

    ``origin/main`` and ``github/main`` both name the canonical ``main`` —
    the dispatch fetch lands every base into ``refs/remotes/origin/<name>``
    regardless of which remote served it (#7522).
    """
    stripped = base_branch.removeprefix("origin/")
    return stripped.removeprefix("github/")


_GIT_ENV_DENYLIST = {
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_NAMESPACE",
    "GIT_CEILING_DIRECTORIES",
    "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    "GIT_COMMON_DIR",
}


def _sanitized_git_env() -> dict[str, str]:
    """Select the explicit repository and refuse interactive credential prompts."""
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in _GIT_ENV_DENYLIST and not key.startswith("PRE_COMMIT")
    }
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def _is_virtualenv_bin_path(entry: str) -> bool:
    """Return whether a PATH entry is a conventional Python virtualenv bin."""
    path = Path(entry)
    return path.name == "bin" and path.parent.name in {".venv", "venv"}


def _pinned_worker_venv_env(source: dict[str, str]) -> dict[str, str]:
    """Pin a detached worker to this repository's venv, never an inherited one.

    A dispatch worker can run arbitrary project commands.  If its parent was
    launched from a different checkout's activated virtualenv, retaining that
    ``VIRTUAL_ENV`` or its ``bin`` directory in ``PATH`` lets ``pip`` rewrite
    that other environment's console scripts.  The worker always receives the
    canonical project venv path; its explicit ``.venv/bin/python`` spawn
    command has no fallback if that interpreter is unavailable.
    """
    venv_root = _REPO_ROOT / ".venv"
    venv_bin = venv_root / "bin"
    pinned = dict(source)
    inherited_path = source.get("PATH", "")
    inherited_venv = source.get("VIRTUAL_ENV")
    inherited_venv_bin = os.path.normpath(str(Path(inherited_venv) / "bin")) if inherited_venv else None
    path_entries = [
        entry
        for entry in inherited_path.split(os.pathsep)
        if entry and not _is_virtualenv_bin_path(entry) and os.path.normpath(entry) != inherited_venv_bin
    ]
    from scripts.opsec.prepublish import publish_environment

    pinned["PATH"] = os.pathsep.join((str(venv_bin), *path_entries))
    pinned = publish_environment(pinned, root=_REPO_ROOT)
    pinned["VIRTUAL_ENV"] = str(venv_root)
    # PYTHONHOME can override the interpreter's calculated prefix and make a
    # correctly pinned venv behave like an unrelated Python installation.
    pinned.pop("PYTHONHOME", None)
    return pinned


@dataclass(frozen=True)
class AutoFinalizeResult:
    ok: bool
    commit_sha: str | None = None
    pr_url: str | None = None
    error: str | None = None
    changed_files: tuple[str, ...] = ()
    # The task's declared --owned-path values, or None when it declared none (#8991).
    owned_paths: tuple[str, ...] | None = None
    # Changed files outside the owned paths: never staged, left in the tree.
    skipped_paths: tuple[str, ...] = ()
    # Additions and deletions that could be one move across the owned-path
    # boundary (an owned side plus an opposite outside side): all skipped.
    cross_boundary_moves: tuple[str, ...] = ()


def _format_process_failure(proc: subprocess.CompletedProcess[str]) -> str:
    detail = (proc.stderr or proc.stdout or "").strip()
    if detail:
        return detail.splitlines()[-1]
    return f"exit {proc.returncode}"


def _worktree_is_dirty(worktree: Path) -> bool | None:
    from scripts.orchestration.execution_safe_git import run_git as safe_git

    try:
        status_proc = safe_git(
            ["status", "--porcelain"],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if status_proc.returncode != 0:
        return None
    return bool((status_proc.stdout or "").strip())


# Top-level checkout dirs the read-only snapshot never records. Other lanes'
# dispatch worktrees live under ``.worktrees/`` (layout A): concurrent activity
# there — including writes inside a sandbox that already existed at pre-snapshot
# time — is never this task's mutation, and it false-failed cleanly-successful
# read-only dispatches (#7124). The guard diffs only what the task could own.
_READ_ONLY_SNAPSHOT_EXCLUDED_TOP_LEVEL_DIRS = frozenset({".worktrees"})


def _is_read_only_snapshot_excluded_path(path: str) -> bool:
    """Return whether a checkout-relative path is outside the snapshot scope."""
    normalized = _normalize_read_only_relpath(path)
    top_level = normalized.split("/", 1)[0]
    return top_level in _READ_ONLY_SNAPSHOT_EXCLUDED_TOP_LEVEL_DIRS


def _read_only_checkout_snapshot(cwd: Path) -> tuple[dict[str, str] | None, str | None]:
    """Capture Git state and linked database contents for a read-only worker.

    The snapshot includes ignored files because a writeful legacy audit can
    create ignored cache entries that ordinary ``git status`` deliberately
    hides.  It is diagnostic only: this guard reports leaked paths and never
    removes them, since a pre-existing user file cannot be attributed safely.

    Paths under ``.worktrees/`` are excluded entirely (#7124): they belong to
    concurrent dispatch lanes, not to the task being guarded.
    Provisioned DB links retain their Git status when the primary target is
    written (#9421). Fingerprint their link text, resolved path, and contents,
    including SQLite's persistent journal/WAL at the resolved target, so a
    write followed by retargeting to an older copy cannot settle ``done``.
    """
    commands = (
        (
            "status",
            ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        ),
        (
            "ignored",
            ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignored"],
        ),
    )
    outputs: dict[str, str] = {}
    for label, command in commands:
        try:
            proc = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False,
                env=_sanitized_git_env(),
                timeout=DEFAULT_GIT_TIMEOUT_S,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return None, f"{label} snapshot could not start: {type(exc).__name__}: {exc}"
        if proc.returncode != 0:
            return None, f"{label} snapshot failed: {_format_process_failure(proc)}"
        outputs[label] = proc.stdout or ""

    entries: dict[str, str] = {}
    status_records = outputs["status"].split("\0")
    index = 0
    while index < len(status_records):
        record = status_records[index]
        index += 1
        if not record:
            continue
        if len(record) < 4 or record[2] != " ":
            return None, "status snapshot returned an unparseable porcelain record"
        state, path = record[:2], record[3:]
        # Porcelain v1 emits the pre-rename/pre-copy path as a second NUL item.
        # Consume it even for excluded paths so the record stream stays aligned.
        rename_source: str | None = None
        if "R" in state or "C" in state:
            if index >= len(status_records) or not status_records[index]:
                return None, "status snapshot returned an incomplete rename/copy record"
            rename_source = status_records[index]
            index += 1
        # Filter the rename/copy source and destination independently
        # (#7147): ``git mv tracked.txt .worktrees/lane/tracked.txt`` must still
        # surface the tracked source deletion even though the destination is
        # out of snapshot scope.
        if not _is_read_only_snapshot_excluded_path(path):
            entries[path] = state
        if rename_source is not None and not _is_read_only_snapshot_excluded_path(rename_source):
            entries[rename_source] = f"{state}:source"
    # ``git status`` without ``--ignored`` omits ignored paths entirely. The
    # second status invocation makes those paths observable as ``!!`` while
    # retaining porcelain's tracked/untracked classification for the first
    # invocation. Do not let the second invocation overwrite real statuses.
    for record in outputs["ignored"].split("\0"):
        if len(record) < 4 or record[:2] != "!!" or record[2] != " ":
            continue
        path = record[3:]
        if not _is_read_only_snapshot_excluded_path(path):
            entries[path] = "!!"
    # Discover database links directly so every provisioned link is covered
    # without duplicating the provisioning paths in another scope.
    try:
        with os.scandir(cwd / "data") as data_entries:
            database_paths = sorted(Path(entry.path) for entry in data_entries if entry.name.endswith(".db"))
    except FileNotFoundError:
        database_paths = []
    except OSError as exc:
        return None, f"linked database snapshot failed: data: {type(exc).__name__}"
    for link in database_paths:
        if not link.is_symlink():
            continue
        relative_path = link.relative_to(cwd).as_posix()
        try:
            link_text = os.readlink(link)
            target = link.resolve(strict=True)
            fingerprints = []
            for suffix in ("", "-journal", "-wal"):
                database_file = Path(f"{target}{suffix}")
                try:
                    with database_file.open("rb") as handle:
                        digest = hashlib.file_digest(handle, "sha256").hexdigest()
                except FileNotFoundError:
                    if not suffix:
                        raise
                    digest = None
                fingerprints.append(digest)
        except (OSError, RuntimeError) as exc:
            return None, f"linked database snapshot failed: {relative_path}: {type(exc).__name__}"
        entries[relative_path] = entries.get(relative_path, "!!") + ":" + json.dumps(
            {"link_text": link_text, "resolved_path": str(target), "contents": fingerprints}
        )
    return entries, None


def _read_only_task_record_snapshot(
    task_id: str,
    baseline: dict[str, tuple[str, str | None]] | None = None,
) -> tuple[dict[str, tuple[str, str | None]] | None, str | None]:
    """Fingerprint results of tasks already terminal when the review starts.

    A sibling task owns its live record and may finish during a review. Only
    changes to a pre-existing terminal result are attributable here. A new
    run_nonce means ``--force-new`` replaced the hot record, not that the old
    result was edited.
    """
    own_stem = _state_path(task_id).stem
    snapshot: dict[str, tuple[str, str | None]] = {}
    try:
        paths = (
            list(tasks_dir().glob("*.result"))
            if baseline is None
            else [tasks_dir() / Path(name).name for name in baseline]
        )
    except OSError as exc:
        return None, f"task record snapshot failed: {type(exc).__name__}: {exc}"
    for path in paths:
        if path.stem == own_stem:
            continue
        state = _read_state_json(path.with_suffix(".json"))
        if baseline is None and (state is None or state.get("status") not in _TERMINAL_STATUSES):
            continue
        name = f"batch_state/tasks/{path.name}"
        nonce = state.get("run_nonce") if state else None
        if baseline is not None and nonce != baseline[name][1]:
            continue
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            # The task may have been archived or reaped during the scan.
            continue
        snapshot[name] = (digest, nonce)
    return snapshot, None


# Harness-owned Entire residue under the checkout (ADR-018 capture). These paths
# are gitignored and appear in the read-only snapshot because the guard includes
# ignored files (#4840). Treating them as task mutations false-fails healthy
# read-only dispatches at repo root and inside dispatch worktrees (#6803).
# Keep this list precise: committed ``.entire/`` config (settings, allowlist,
# private-recall) must still fail the guard when a worker edits it.
# Force-added tracked files under these prefixes are NOT exempt: exemption
# requires an ignored/untracked porcelain status at snapshot time (#6803 r2).
_READ_ONLY_RUNTIME_TELEMETRY_PREFIXES = (
    ".entire/metadata",
    ".entire/logs",
    ".entire/tmp",
    ".entire/redactors/local",
)
_READ_ONLY_RUNTIME_TELEMETRY_FILES = frozenset({".entire/settings.local.json"})
# Gitignored-by-default dirs a worker's own tooling writes (#6860). Observed
# false-fails: ``.agent/sessions/*.json``, fleet-comms sqlite ``-shm/-wal``,
# ``.pytest_cache/``, ``.pytest_breadcrumbs/``. Siblings are the same class
# (harness/session/cache residue). Membership is load-bearing (#8516 AC-02):
# an ignored ``!!`` path escapes the mutation guard ONLY through this
# classification, so task-authored leak targets like ``.cache/`` (#4840),
# root-level ``/*.py`` scratch, and ``/scratch/`` deliberately stay OUT and
# now fail the task. Deploy-target dirs (``.claude``, ``.codex``, ``.gemini``,
# ``.cursor``, ``.agents``) are not in this set: they hold tracked,
# harness-executed content, so an untracked new file there (e.g.
# ``.claude/hooks/``) must still fail a read-only task in its own worktree.
# Tracked files under these names still fail via porcelain status.
_READ_ONLY_RUNTIME_STATE_DIR_NAMES = frozenset(
    {
        ".agent",
        ".antigravitycli",
        ".deploy-state",
        ".pytest_breadcrumbs",
        ".pytest_cache",
        ".runtime",
        ".ruff_cache",
        "__pycache__",
        "batch_state",
    }
)
_READ_ONLY_RUNTIME_STATE_SUFFIXES = (
    ".db-journal",
    ".db-shm",
    ".db-wal",
    ".sqlite-journal",
    ".sqlite-shm",
    ".sqlite-wal",
    ".sqlite3-journal",
    ".sqlite3-shm",
    ".sqlite3-wal",
)
_READ_ONLY_PACKAGE_BUILD_PREFIXES = (
    "packages/v4-runtime/build",
    "packages/v4-runtime/src/learn_ukrainian_v4_runtime.egg-info",
)
_READ_ONLY_UNTRACKED_OR_IGNORED_STATUSES = frozenset({"??", "!!"})
# Dispatch sandboxes live at ``.worktrees/dispatch/<agent>/<task>/`` (layout A).
# Concurrent ``git worktree add`` under that prefix must not false-fail a
# read-only task that is scanning the shared primary checkout (#6938).
_READ_ONLY_DISPATCH_SANDBOX_PREFIX = (".worktrees", "dispatch")
_READ_ONLY_DISPATCH_SANDBOX_ROOT_PARTS = 4  # .worktrees / dispatch / agent / task


def _normalize_read_only_relpath(path: str) -> str:
    """Normalize a checkout-relative path for read-only guard matching."""
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.rstrip("/")


def _is_read_only_runtime_telemetry_path(path: str) -> bool:
    """Return whether a path is harness Entire telemetry, not a task mutation."""
    normalized = _normalize_read_only_relpath(path)
    if normalized in _READ_ONLY_RUNTIME_TELEMETRY_FILES:
        return True
    return any(
        normalized == prefix or normalized.startswith(f"{prefix}/") for prefix in _READ_ONLY_RUNTIME_TELEMETRY_PREFIXES
    )


def _is_read_only_delegate_snapshot_sidecar_path(path: str) -> bool:
    """Return whether *path* is a delegate-owned read-only snapshot sidecar."""
    normalized = _normalize_read_only_relpath(path)
    if not normalized.endswith(".json"):
        return False
    parts = normalized.split("/")
    if len(parts) < 2:
        return False
    if not parts[-2].endswith(f"{_READ_ONLY_CHECKOUT_SNAPSHOT_SUFFIX}"):
        return False
    name = parts[-1]
    if name == _READ_ONLY_SNAPSHOT_DIGEST_NAME:
        return True
    return name.startswith("read_only_checkout_") and name.endswith(".json")


def _is_read_only_runtime_state_path(path: str) -> bool:
    """Return whether a path is harness/tooling runtime state, not repo content.

    Covers Entire telemetry (#6803) plus the gitignored runtime dirs and sqlite
    sidecars that false-failed successful read-only tasks (#6860). Since #8516
    AC-02 this classification is ALSO the only way an ignored ``!!`` path
    escapes the mutation guard: task-authored ignored leaks outside it (the
    review-a3-api-ui ``/*.py`` + ``/scratch/`` scratch class; ``.cache/``
    residue from #4840/#7253) now fail the task like any other mutation.
    """
    if _is_read_only_delegate_snapshot_sidecar_path(path):
        return True
    if _is_read_only_runtime_telemetry_path(path):
        return True
    normalized = _normalize_read_only_relpath(path)
    # The shared broker watcher can append while a review runs (#10025).
    # Exempt its log only; other ignored MCP files remain mutation targets.
    if normalized == ".mcp/servers/message-broker/watcher.log":
        return True
    # `pip`/setuptools can regenerate these Git-ignored package outputs while
    # a reviewer runs tests. They are build residue, not review edits (#9213).
    if _is_read_only_package_build_path(normalized):
        return True
    parts = tuple(part for part in normalized.split("/") if part and part != ".")
    if any(part in _READ_ONLY_RUNTIME_STATE_DIR_NAMES for part in parts):
        return True
    return any(normalized.endswith(suffix) for suffix in _READ_ONLY_RUNTIME_STATE_SUFFIXES)


def _is_read_only_package_build_path(path: str) -> bool:
    normalized = _normalize_read_only_relpath(path)
    return any(
        normalized == prefix or normalized.startswith(f"{prefix}/") for prefix in _READ_ONLY_PACKAGE_BUILD_PREFIXES
    )


def _read_only_dispatch_sandbox_root(path: str) -> str | None:
    """Return ``.worktrees/dispatch/<agent>/<task>`` when *path* is under one.

    Paths outside the dispatch sandbox layout (including other ``.worktrees/``
    entries) return ``None`` so the guard still sees them as ordinary mutations.
    """
    normalized = _normalize_read_only_relpath(path)
    parts = tuple(part for part in normalized.split("/") if part and part != ".")
    if len(parts) < _READ_ONLY_DISPATCH_SANDBOX_ROOT_PARTS:
        return None
    if parts[:2] != _READ_ONLY_DISPATCH_SANDBOX_PREFIX:
        return None
    return "/".join(parts[:_READ_ONLY_DISPATCH_SANDBOX_ROOT_PARTS])


def _read_only_dispatch_sandbox_roots(snapshot: dict[str, str]) -> frozenset[str]:
    """Collect dispatch sandbox roots visible in a read-only checkout snapshot."""
    return frozenset(root for path in snapshot if (root := _read_only_dispatch_sandbox_root(path)) is not None)


def _is_read_only_new_sibling_dispatch_sandbox_path(path: str, *, before_roots: frozenset[str]) -> bool:
    """Return whether *path* belongs to a sibling sandbox absent from *before*.

    Only newly appeared ``.worktrees/dispatch/<agent>/<task>/`` trees are
    exempt (#6938). A write under a sandbox root that already appeared in the
    pre-snapshot still counts as a mutation when the root checkout can see it.
    """
    root = _read_only_dispatch_sandbox_root(path)
    if root is None:
        return False
    return root not in before_roots


def _is_read_only_untracked_or_ignored_status(state: str | None) -> bool:
    """Return whether a porcelain status is ignored/untracked (not git-tracked).

    Absent entries are treated as non-tracked for the exemption gate: a clean
    tracked file is invisible in the snapshot until it mutates, and the
    post-mutation status then fails this check.
    """
    if state is None:
        return True
    return state[:2] in _READ_ONLY_UNTRACKED_OR_IGNORED_STATUSES


def _is_read_only_runtime_state_exemption(
    path: str,
    *,
    before_state: str | None,
    after_state: str | None,
) -> bool:
    """Exempt harness runtime state only when it is not tracked at snapshot time."""
    if not _is_read_only_runtime_state_path(path):
        return False
    if _is_read_only_package_build_path(path):
        # The package exemption is for Git-ignored build products only. An
        # ordinary untracked scratch file under this tree is still a leak.
        return (
            before_state in (None, "!!")
            and after_state in (None, "!!")
            and (before_state == "!!" or after_state == "!!")
        )
    return _is_read_only_untracked_or_ignored_status(before_state) and _is_read_only_untracked_or_ignored_status(
        after_state
    )


def _is_read_only_ignored_status(state: str | None) -> bool:
    """Return whether a snapshot status is Git's ignored ``!!`` marker."""
    return state is not None and state[:2] == "!!"


def _is_read_only_ignored_mutation(*, before_state: str | None, after_state: str | None) -> bool:
    """Return whether a changed path is ignored in its observable final state.

    A deleted ignored file disappears from both porcelain snapshots, so its
    pre-snapshot ``!!`` marker is also sufficient to classify that delta as an
    ignored mutation. A path that becomes ordinary untracked ``??`` remains a
    real mutation and is intentionally not classified as ignored.
    """
    if after_state is not None:
        return _is_read_only_ignored_status(after_state)
    return _is_read_only_ignored_status(before_state)


def _read_only_ignored_mutation_paths(before: dict[str, str], after: dict[str, str]) -> list[str]:
    """Return changed ignored paths the guard deliberately tolerates as noise.

    Diagnostic companion to :func:`_read_only_mutation_paths` (#8516): an
    ignored ``!!`` status alone no longer exempts a path, so this list holds
    exactly the ignored deltas that were ALSO recognized as harness/runtime
    state — the build-noise class a read-only dispatch legitimately cannot
    own (``.pytest_cache/``, ``batch_state/``, ``.entire/`` telemetry, …).
    """
    before_roots = _read_only_dispatch_sandbox_roots(before)
    return sorted(
        path
        for path in set(before) | set(after)
        if before.get(path) != after.get(path)
        and _is_read_only_ignored_mutation(
            before_state=before.get(path),
            after_state=after.get(path),
        )
        and _is_read_only_runtime_state_exemption(
            path,
            before_state=before.get(path),
            after_state=after.get(path),
        )
        and not _is_read_only_new_sibling_dispatch_sandbox_path(path, before_roots=before_roots)
    )


def _read_only_mutation_paths(before: dict[str, str], after: dict[str, str]) -> list[str]:
    """Return exact paths whose observable Git state changed during a review.

    A changed path is exempt only when it is recognized harness/runtime noise
    (:func:`_is_read_only_runtime_state_exemption`: gitignored tooling residue
    such as ``.pytest_cache/`` or ``batch_state/``) or a newly appeared
    sibling dispatch sandbox under ``.worktrees/dispatch/<agent>/<task>/``
    (#6938 defense in depth; since #7124 the snapshot itself already drops
    every ``.worktrees/`` path). Tracked paths under runtime prefixes
    (including force-added files) still trip the guard.

    #8516 AC-02: an ignored ``!!`` status BY ITSELF no longer exempts a path.
    The review-a3-api-ui leak showed why: the agy worker wrote its scratch
    files at the checkout root and under ``scratch/``, where ``.gitignore``
    (``/*.py``, ``/scratch/``) marked them ``!!``, and the guard filed them
    as diagnostic-only "ignored mutations" while the task settled ``done``.
    Now any other new, modified, or deleted path — tracked, untracked, or
    ignored — fails the task and is named.
    """
    before_roots = _read_only_dispatch_sandbox_roots(before)
    return sorted(
        path
        for path in set(before) | set(after)
        if before.get(path) != after.get(path)
        and not _is_read_only_runtime_state_exemption(
            path,
            before_state=before.get(path),
            after_state=after.get(path),
        )
        and not _is_read_only_new_sibling_dispatch_sandbox_path(path, before_roots=before_roots)
    )


def _auto_finalize_changed_files(worktree: Path) -> tuple[str, ...]:
    try:
        # --no-renames lists both sides of a rename, so an owned-path filter
        # never commits the new path while leaving the old one's deletion out.
        tracked = subprocess.run(
            ["git", "diff", "--no-renames", "--name-only", "-z", "HEAD", "--"],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
        untracked = subprocess.run(
            ["git", "ls-files", "-z", "--others", "--exclude-standard"],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ()
    if tracked.returncode != 0 or untracked.returncode != 0:
        return ()
    changed = {path for path in (*tracked.stdout.split("\0"), *untracked.stdout.split("\0")) if path}
    return tuple(sorted(changed))


def _auto_finalize_is_junk_only(changed_files: tuple[str, ...]) -> bool:
    """Return whether auto-finalization would publish only disposable residue."""
    return bool(changed_files) and all(_is_disposable_auto_finalize_path(path) for path in changed_files)


def _declared_owned_paths(raw: object) -> tuple[str, ...] | None:
    """The task record's ``owned_paths`` (its ``--owned-path`` values), or None."""
    if not isinstance(raw, (list, tuple)):
        return None
    paths = tuple(str(item) for item in raw if isinstance(item, str) and item.strip())
    return paths or None


def _owned_path_errors(values: Sequence[str] | None) -> list[str]:
    """``--owned-path`` values that could never own a file; dispatch refuses them."""
    try:
        from scripts.guardrails.delegate_ownership import owned_path_matcher
    except ImportError:  # pragma: no cover - flat script path
        from guardrails.delegate_ownership import owned_path_matcher  # type: ignore

    return [value for value in values or () if owned_path_matcher(value) is None]


def _path_is_owned(path: str, owned_paths: Sequence[str]) -> bool:
    """Whether a repo-relative changed ``path`` falls under a declared owned path (:func:`path_is_owned`)."""
    try:
        from scripts.guardrails.delegate_ownership import path_is_owned
    except ImportError:  # pragma: no cover - flat script path
        from guardrails.delegate_ownership import path_is_owned  # type: ignore

    return path_is_owned(path, owned_paths)


def _worktree_diff_output(worktree: Path, diff_args: Sequence[str], *, git_options: Sequence[str] = ()) -> str | None:
    """``git diff <diff_args>`` as if every change, untracked files included, were committed; None when unknown."""
    return _worktree_diff_read(worktree, diff_args, git_options=git_options)[0]


# #9878: the closed registry of public causes. A reason that can leave the
# machine (a task record's reason fields, a refusal or rescue row, the lines
# that print them, and through them a PR, issue, inbox or the Monitor) is one
# of these causes, with fixed parameters only: a known git subcommand, an exit
# status, a count, an exception class and its errno name. Raw stderr, exception
# messages, paths and URLs never are: :func:`public_cause` replaces them with
# :data:`UNCLASSIFIED_CAUSE` and they go only to the task's local diagnostic
# file (:func:`_append_diagnostics`).
TYPED_CAUSE_CODES = frozenset(
    {
        # Reading a Kimi worker's changes for the content check.
        "merge_base_unresolved",
        "temp_index_failed",
        "diff_command_failed",
        "changes_parse_failed",
        "file_unreadable",
        "changes_unreadable",
        "kimi_content_refused",
        # The worker-side Kimi admission and worktree boundary.
        "kimi_admission_refused",
        "kimi_worktree_mismatch",
        "review_admission_refused",
        "mechanical_admission_refused",
        "boundary_remove_failed",
        "boundary_install_failed",
        # The worker's own outcome.
        "worker_failed",
        "worker_cancelled",
        "worker_timed_out",
        "worker_rate_limited",
        "worker_runtime_error",
        "worker_unexpected_error",
        "adapter_rejected",
        "runtime_returncode_missing",
        "read_only_checkout_mutation",
        "task_records_snapshot_failed",
        # Dispatch before the worker ran.
        "worktree_preparation_failed",
        "forward_configuration_failed",
        "dispatch_not_started",
        "worker_spawn_failed",
        "dispatch_isolation_failed",
        "dispatch_fallback_refused",
        # Finalize and auto-finalize.
        "finalize_failed",
        "interrupted_during_finalize",
        "finalize_skipped_paths",
        "auto_finalize_unsafe_branch",
        "auto_finalize_add_failed",
        "auto_finalize_commit_failed",
        "auto_finalize_push_failed",
        "auto_finalize_reset_failed",
        "auto_finalize_pr_failed",
        "auto_finalize_publish_blocked",
        "auto_finalize_failed",
        # Rescue.
        "rescue_worktree_unregistered",
        "rescue_tree_unavailable",
        "rescue_identity_unavailable",
        "rescue_commit_failed",
        "rescue_filtered_path",
        "rescue_embedded_repository",
        "rescue_new_gitlink",
        "rescue_input_unreadable",
        "rescue_input_changed",
        "rescue_push_url_unavailable",
        "rescue_push_failed",
        "rescue_remote_unverified",
        "rescue_step_failed",
        "remote_unreachable",
        # Review task records (``_review_task_failure_reason``) and the dead-worker settle.
        "read_only_checkout_snapshot_failed",
        "review_worker_not_started",
        "review_worker_returncode_missing",
        "review_worker_nonzero_exit",
        "review_worker_reported_failure",
        "worker_process_dead",
        "worktree_missing_at_settle",
    }
)
UNCLASSIFIED_CAUSE = "unclassified_error"
# Fixed reason phrases already published verbatim (rescue rows, finalize and
# auto-finalize states): closed literals, never built from data.
_PUBLIC_REASON_PHRASES = frozenset(
    {
        "activity probe unavailable",
        "ahead count unavailable",
        "already rescued at HEAD",
        "changed files unavailable",
        "clean disposable residue",
        "could not clean disposable residue",
        "disposable residue removed",
        "files exceed 5 MB",
        "HEAD unavailable",
        "invalid finished_at",
        "no finished_at",
        "no provable unpushed work",
        "no recorded worktree",
        "not a registered dispatch worktree",
        "rescue remote branch already exists at another head",
        "task attempt changed after rescue push; recovery ref preserved",
        "task is not terminal non-success",
        "task lease active",
        "task process alive",
        "task state changed",
        "unreadable task state",
        "worktree active",
        "worktree already removed",
        "worktree branch differs from task record",
        "worktree ownership unknown or reused",
        "unpushed work - needs rescue",
        "unpushed state unknown - needs rescue",
        "rescued",
        "clean-tree",
        "not a git worktree",
        "move detection failed; nothing committed",
        "interrupted before the completion gates ran",
    }
)
# Task-record fields whose value is a reason; ``auto_finalize.error`` is the nested one.
PUBLIC_RECORD_REASON_FIELDS = (
    "last_error",
    "finalize_error",
    "incomplete_run_reason",
    "no_deliverable_reason",
    "failure_reason",
    "failure_code",
    "review_verdict_failure",
    "rescue_status",
    "kimi_content_refusal",
)
PUBLIC_RECORD_NESTED_REASON_FIELDS = (("auto_finalize", "error"),)
# Rescue and refusal rows: the keys whose value is a reason.
PUBLIC_ROW_REASON_KEYS = ("reason", "failure_code")
_PUBLIC_CAUSE_MAX_CHARS = 512
# git's own command names: a closed vocabulary.
_PUBLIC_GIT_SUBCOMMANDS = frozenset(
    {
        "add", "am", "apply", "archive", "branch", "cat-file", "check-attr", "check-ignore", "check-ref-format",
        "checkout", "cherry-pick", "clean", "clone", "commit", "commit-tree", "config", "count-objects",
        "describe", "diff", "diff-files", "diff-index", "diff-tree", "fetch", "for-each-ref", "fsck", "gc",
        "hash-object", "init", "log", "ls-files", "ls-remote", "ls-tree", "merge", "merge-base", "mktree", "mv",
        "notes", "pack-refs", "prune", "pull", "push", "read-tree", "rebase", "reflog", "remote", "repack",
        "reset", "restore", "rev-list", "rev-parse", "rm", "show", "show-ref", "sparse-checkout", "stash",
        "status", "submodule", "switch", "symbolic-ref", "tag", "update-index", "update-ref", "var",
        "verify-commit", "worktree", "write-tree",
    }
)  # fmt: skip
# An exception class: a CamelCase identifier with one of Python's exception-name endings.
_PUBLIC_ERROR_CLASS_RE = re.compile(
    r"[A-Z][A-Za-z0-9]{0,63}(?:Error|Exception|Exit|Interrupt|Expired|Refused|Unreadable|Blocked|Iteration|Warning)"
)
_PUBLIC_ERRNO_NAMES = frozenset(errno.errorcode.values())
_PUBLIC_INT_PARAM_RE = re.compile(r"(?:exit -?|count )\d{1,9}")
_GIT_SUBCOMMAND_RE = re.compile(r"[a-z][a-z-]{0,39}")
# git's own words for a remote it never reached (DNS, routing, refused connection).
_REMOTE_UNREACHABLE_STDERR = (
    "could not resolve host",
    "could not resolve hostname",
    "temporary failure in name resolution",
    "name or service not known",
    "connection refused",
    "connection timed out",
    "network is unreachable",
    "no route to host",
)


@functools.cache
def public_causes() -> frozenset[str]:
    """Every cause a public reason may name: the one closed registry (#9878).

    Delegate's own codes and phrases, the agent runtime's failure codes, AGY's
    incomplete-run reasons, the bounded-advisory refusal and gate codes, the
    exit-scan reasons, and the completion-gate and delivery causes.
    """
    from scripts.agent_runtime.adapters.agy import AGY_INCOMPLETE_RUN_REASONS
    from scripts.agent_runtime.failure_codes import RUNTIME_FAILURE_CODES

    advisory = {
        getattr(bounded_advisory, name)
        for name in (
            "ENVELOPE_REQUIRED", "FLAG_CONFLICT", "TASK_NOT_FOUND", "TASK_NOT_DONE", "TASK_WRONG_MODEL",
            "TASK_WRONG_ROLE", "RESULT_UNREADABLE", "ENVELOPE_MISSING", "ENVELOPE_INCOMPLETE",
            "OWNED_PATHS_INVALID", "BINDING_MISMATCH", "OWNED_PATHS_MISMATCH", "ENVELOPE_CHANGED", "SEAL_MISSING",
            "SEAL_MISMATCH", "ADMISSION_MISSING", "ADMISSION_INVALID", "ADVISOR_ROUTE_REFUSED",
            "EXECUTION_MISMATCH", "CEILING_EXCEEDED", "CEILING_UNMEASURED", "EXEMPT_CODE_CHANGE",
            "EXEMPT_CHANGES_UNMEASURED",
        )
        if isinstance(getattr(bounded_advisory, name, None), str)
    }  # fmt: skip
    delegate_causes = {
        _NO_DELIVERABLE_UNKNOWN_COMMIT_COUNT_REASON,
        _NO_DELIVERABLE_NO_COMMITS_REASON,
        _NO_DELIVERABLE_INVALID_DECLARATION_REASON,
        _NO_DELIVERABLE_JUNK_ONLY_WORKTREE_REASON,
        _NO_DELIVERABLE_MISSING_REVIEW_VERDICT_REASON,
        _AUTO_FINALIZE_NOTHING_OWNED_REASON,
        _AUTO_FINALIZE_NO_OWNED_PATHS_REASON,
        COMPLETION_GATE_RESPONSE_UNAVAILABLE,
        RECOVERY_REQUIRES_RERUN,
        _INTERRUPTED_BEFORE_COMPLETION_GATES,
        worker_leftovers.BACKGROUND_JOBS_REASON,
        worker_leftovers.SCAN_UNKNOWN_REASON,
        UNCLASSIFIED_CAUSE,
    }
    return frozenset(
        TYPED_CAUSE_CODES
        | _PUBLIC_REASON_PHRASES
        | RUNTIME_FAILURE_CODES
        | frozenset(AGY_INCOMPLETE_RUN_REASONS)
        | advisory
        | delegate_causes
    )


def _is_public_error(text: str) -> bool:
    """An exception class, optionally with its errno name: ``OSError EACCES``."""
    error_class, _, errno_name = text.partition(" ")
    return bool(_PUBLIC_ERROR_CLASS_RE.fullmatch(error_class)) and (not errno_name or errno_name in _PUBLIC_ERRNO_NAMES)


def _is_public_param(text: str) -> bool:
    """One fixed parameter: ``git <known subcommand>``, ``exit <n>``, ``count <n>``, or ``<ErrorClass>[ <ERRNO>]``."""
    if text.startswith("git "):
        return text[4:] in _PUBLIC_GIT_SUBCOMMANDS
    return bool(_PUBLIC_INT_PARAM_RE.fullmatch(text)) or _is_public_error(text)


def _is_public_item(text: str) -> bool:
    """A registered cause, alone or followed by fixed parameters (``cause, git push, exit 1``)."""
    if text in public_causes():
        return True
    cause, *params = text.split(", ")
    return cause in public_causes() and bool(params) and all(_is_public_param(param) for param in params)


def is_public_cause(value: object) -> bool:
    """Whether ``value`` may be published as it is: registered causes with fixed parameters, joined by ``; ``."""
    if not isinstance(value, str) or not value or len(value) > _PUBLIC_CAUSE_MAX_CHARS:
        return False
    return value in public_causes() or all(_is_public_item(item) for item in value.split("; "))


@dataclass(frozen=True)
class _TypedCause:
    """Why a refusal, rescue step or worker failed, in a form that may leave the machine (#9878).

    :meth:`public` renders only registered parts: the code (one of
    :func:`public_causes`), a known git subcommand, the exit status, a count
    and the exception class. ``path`` and ``diagnostic`` (the raw stderr or
    exception text) go only to the task's local diagnostic file.
    """

    code: str
    command: str | None = None
    exit_status: int | None = None
    error: str | None = None
    path: str | None = None
    count: int | None = None
    diagnostic: str = dataclasses.field(default="", compare=False, repr=False)

    def public(self) -> str:
        parts = [self.code if self.code in public_causes() else UNCLASSIFIED_CAUSE]
        if self.command in _PUBLIC_GIT_SUBCOMMANDS:
            parts.append(f"git {self.command}")
        for label, number in (("exit", self.exit_status), ("count", self.count)):
            if isinstance(number, int) and not isinstance(number, bool) and abs(number) < 10**9:
                parts.append(f"{label} {number}")
        if self.error and _is_public_error(self.error):
            parts.append(self.error)
        return ", ".join(parts)


def public_cause(value: object) -> tuple[str | None, _TypedCause | None]:
    """The sink every public reason is written through: ``(public text, cause to record locally)`` (#9878).

    A :class:`_TypedCause` renders its public form. A string that is already
    a public cause (:func:`is_public_cause`) passes unchanged with nothing to
    record. Anything else (free text, an exception, another type) is replaced
    item by item with :data:`UNCLASSIFIED_CAUSE` (an exception keeps its class)
    and returned as the cause whose raw text the caller records in the task's
    local diagnostic file. Pure: it writes nothing.
    """
    if value is None:
        return None, None
    if isinstance(value, _TypedCause):
        return value.public(), value
    if isinstance(value, BaseException):
        cause = _exception_cause(UNCLASSIFIED_CAUSE, value)
        return cause.public(), cause
    if isinstance(value, str):
        if not value or is_public_cause(value):
            return value, None
        kept: list[str] = []
        for item in value.split("; "):
            public = item if _is_public_item(item) else UNCLASSIFIED_CAUSE
            if public not in kept:
                kept.append(public)
        text = "; ".join(kept)
        return (text if len(text) <= _PUBLIC_CAUSE_MAX_CHARS else UNCLASSIFIED_CAUSE), _TypedCause(
            UNCLASSIFIED_CAUSE, diagnostic=value
        )
    return UNCLASSIFIED_CAUSE, _TypedCause(UNCLASSIFIED_CAUSE, diagnostic=f"{type(value).__name__}: {value!r}")


def _public_record(state: Mapping[str, Any]) -> tuple[dict[str, Any], list[tuple[str, _TypedCause]]]:
    """``state`` with every public reason field through :func:`public_cause`, and the ``(field, cause)`` to record."""
    public = dict(state)
    recorded: list[tuple[str, _TypedCause]] = []
    for field in PUBLIC_RECORD_REASON_FIELDS:
        if field in public:
            public[field], cause = public_cause(public[field])
            if cause is not None:
                recorded.append((field, cause))
    for parent, key in PUBLIC_RECORD_NESTED_REASON_FIELDS:
        nested = public.get(parent)
        if isinstance(nested, Mapping) and key in nested:
            text, cause = public_cause(nested[key])
            public[parent] = {**nested, key: text}
            if cause is not None:
                recorded.append((f"{parent}.{key}", cause))
    return public, recorded


def _public_row(row: Mapping[str, Any], record_path: Path | None, *, source: str) -> dict[str, Any]:
    """A rescue or refusal row with its reason keys through :func:`public_cause`; raw text goes beside ``record_path``."""
    public = dict(row)
    recorded: list[tuple[str, _TypedCause]] = []
    for key in PUBLIC_ROW_REASON_KEYS:
        if key in public:
            public[key], cause = public_cause(public[key])
            if cause is not None:
                recorded.append((key, cause))
    if recorded and record_path is not None:
        pointer = _append_diagnostics(record_path, recorded, source=source)
        if pointer:
            public["diagnostic"] = pointer
    return public


def _write_record_unlocked(path: Path, state: dict[str, Any]) -> None:
    """Write a task record through the public-reason sink; the caller holds its lock (#9878).

    The only writer of a task record in this module, and the one it hands the
    dead-worker markers (``write=``): at this persistence point every reason
    field is checked against the cause registry and replaced by its public
    form, whoever assigned it, and the raw text it replaced is recorded in the
    task's local diagnostic file after the write.
    """
    public, recorded = _public_record(state)
    write_state_unlocked(path, public)
    if recorded:
        _append_diagnostics(path, recorded, source="record")


def _is_repo_relative(path: str) -> bool:
    """Whether ``path`` reads as a repository-relative path: no root, home, parent step or control character."""
    if not path or path.startswith(("/", "~", "\\")) or re.match(r"[A-Za-z]:", path):
        return False
    if any(unicodedata.category(char).startswith("C") for char in path):
        return False
    return ".." not in re.split(r"[/\\]", path) and "://" not in path


def _git_subcommand(args: Sequence[str] | str | None) -> str | None:
    """The subcommand of a ``git [options] <subcommand> ...`` argv, skipping global options and their values."""
    if not isinstance(args, (list, tuple)):
        return None
    words = [str(arg) for arg in args]
    index = 1 if words and Path(words[0]).name == "git" else 0
    while index < len(words):
        word = words[index]
        if word in ("-c", "-C"):
            index += 2
            continue
        if word.startswith("-"):
            index += 1
            continue
        return word if _GIT_SUBCOMMAND_RE.fullmatch(word) else None
    return None


def _git_cause(code: str, proc: subprocess.CompletedProcess[str], *, path: str | None = None) -> _TypedCause:
    """A failed git run as a :class:`_TypedCause`; its argv and stderr stay in the local diagnostic."""
    args = proc.args if isinstance(proc.args, (list, tuple)) else [str(proc.args)]
    return _TypedCause(
        code,
        command=_git_subcommand(args),
        exit_status=proc.returncode,
        path=path,
        diagnostic=f"{' '.join(str(arg) for arg in args)} failed (exit {proc.returncode}): "
        f"{(proc.stderr or proc.stdout or '').strip() or 'no output'}",
    )


def _remote_git_cause(code: str, proc: subprocess.CompletedProcess[str]) -> _TypedCause:
    """:func:`_git_cause` for a git run that talks to a remote: ``remote_unreachable`` when it never reached it."""
    stderr = (proc.stderr or "").lower()
    unreachable = any(marker in stderr for marker in _REMOTE_UNREACHABLE_STDERR)
    return _git_cause("remote_unreachable" if unreachable else code, proc)


def _exception_cause(
    code: str, exc: BaseException, *, command: Sequence[str] | None = None, path: str | None = None
) -> _TypedCause:
    """An exception as a :class:`_TypedCause`: its class (and errno name) public, its message local."""
    if isinstance(exc, _TypedFailure):
        return exc.cause
    errno_name = errno.errorcode.get(exc.errno, "") if isinstance(exc, OSError) and isinstance(exc.errno, int) else ""
    step = f"{' '.join(command)} " if command else ""
    return _TypedCause(
        code,
        command=_git_subcommand(list(command)) if command else None,
        error=f"{type(exc).__name__}{f' {errno_name}' if errno_name else ''}",
        path=path,
        diagnostic=f"{step}raised {type(exc).__name__}: {exc}",
    )


class _TypedFailure(RuntimeError):
    """A step failed with a :class:`_TypedCause`: ``str()`` is its public form, never the raw error (#9878).

    ``message`` is a literal for the local diagnostic; nothing read from git,
    the remote or the host enters the public form.
    """

    def __init__(self, message: str, cause: _TypedCause) -> None:
        super().__init__(cause.public())
        self.message = message
        self.cause = dataclasses.replace(
            cause, diagnostic=f"{message}: {cause.diagnostic}" if cause.diagnostic else message
        )

    @property
    def code(self) -> str:
        return self.cause.code


# The task's local diagnostic file: ``<id>.diag`` beside the record, rotated once
# to ``<id>.diag.prev``. Never served or published. Each entry is one JSON line
# of at most _DIAG_MAX_ENTRY_BYTES; each of the two files stays within
# _DIAG_MAX_FILE_BYTES and mode 0600, whatever was on disk before the append.
_DIAG_MAX_ENTRY_BYTES = 4096
_DIAG_MAX_FILE_BYTES = 256 * 1024
_DIAG_ROTATED_SUFFIX = ".prev"
_DIAG_TRUNCATED = "…[truncated]"


def _diagnostic_path(task_id: str) -> Path:
    """The task's local diagnostic file, ``batch_state/tasks/<id>.diag``: never served or published."""
    return _state_path_no_create(task_id).with_suffix(".diag")


def _diagnostic_line(source: str, field: str, cause: _TypedCause) -> bytes:
    """One JSON line of at most :data:`_DIAG_MAX_ENTRY_BYTES`: the raw text secret-redacted, cut to fit."""
    diagnostic = redact_text(cause.diagnostic) or ""
    path = (redact_text(cause.path) or "")[:512] if cause.path else None

    def encode(text: str) -> bytes:
        entry = {
            "at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": source[:64],
            "field": field[:64],
            "code": cause.code[:64],
            "public": cause.public(),
            **({"path": path} if path else {}),
            "diagnostic": text,
        }
        return (json.dumps(entry, ensure_ascii=False) + "\n").encode("utf-8")

    line = encode(diagnostic)
    if len(line) <= _DIAG_MAX_ENTRY_BYTES:
        return line
    # The longest prefix that fits, in encoded bytes (escapes and multi-byte characters included).
    low, high = 0, min(len(diagnostic), _DIAG_MAX_ENTRY_BYTES)
    while low < high:
        middle = (low + high + 1) // 2
        if len(encode(diagnostic[:middle] + _DIAG_TRUNCATED)) <= _DIAG_MAX_ENTRY_BYTES:
            low = middle
        else:
            high = middle - 1
    return encode(diagnostic[:low] + _DIAG_TRUNCATED)


def _open_diagnostic(directory_fd: int, name: str, flags: int = os.O_RDWR | os.O_APPEND | os.O_CREAT) -> int:
    """Open ``name`` in the trusted task directory: no symlink, a private regular file of ours, made 0600."""
    fd = os.open(name, flags | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, 0o600, dir_fd=directory_fd)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or info.st_nlink != 1:
            raise OSError(errno.EPERM, "diagnostic file is not a private regular file")
        if stat.S_IMODE(info.st_mode) != 0o600:
            os.fchmod(fd, 0o600)
        return fd
    except BaseException:
        os.close(fd)
        raise


def _newest_lines(data: bytes, limit: int) -> bytes:
    """The newest whole lines of ``data`` that fit in ``limit`` bytes."""
    if len(data) <= limit:
        return data
    tail = data[len(data) - limit :]
    return tail if data[len(data) - limit - 1 : len(data) - limit] == b"\n" else tail.partition(b"\n")[2]


def _bound_diagnostic_fd(fd: int) -> None:
    """Cut the locked diagnostic file ``fd`` to its newest lines within :data:`_DIAG_MAX_FILE_BYTES`."""
    size = os.fstat(fd).st_size
    if size <= _DIAG_MAX_FILE_BYTES:
        return
    kept = _newest_lines(os.pread(fd, _DIAG_MAX_FILE_BYTES + 1, size - _DIAG_MAX_FILE_BYTES - 1), _DIAG_MAX_FILE_BYTES)
    os.ftruncate(fd, 0)
    os.lseek(fd, 0, os.SEEK_SET)
    view = memoryview(kept)
    while view:
        view = view[os.write(fd, view) :]


def _bound_rotated_diagnostic(directory_fd: int, name: str) -> None:
    """Bring the rotated generation ``name`` within :data:`_DIAG_MAX_FILE_BYTES` and 0600, keeping its newest lines.

    A name that is not a private regular file of ours (a symlink, a hard
    link, another owner's file) is unlinked: the name alone goes, never what
    it points at. The caller holds the lock on the current diagnostic file;
    this one is locked too, against the writer that rotated it.
    """
    try:
        fd = _open_diagnostic(directory_fd, name, os.O_RDWR)
    except FileNotFoundError:
        return
    except OSError:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(name, dir_fd=directory_fd)
        return
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        _bound_diagnostic_fd(fd)
    finally:
        os.close(fd)


def _append_diagnostics(record_path: Path, causes: Sequence[tuple[str, _TypedCause]], *, source: str) -> str | None:
    """Append each ``(field, cause)`` with its raw text to the record's local ``.diag`` file (#9878).

    Writes only beside an existing task record, so a refused worker still
    leaves no task file behind. The task directory is opened without following
    a symlink and each file through it, never following one either, created
    0600 and refused unless it is a private regular file with one link.
    Entries are bounded (:data:`_DIAG_MAX_ENTRY_BYTES`). Each file is
    unconditionally bounded (:data:`_DIAG_MAX_FILE_BYTES`) and 0600: an
    oversized ``.diag`` rotates, and before every append the rotated
    ``.diag.prev`` is cut to its newest lines and made private, so neither a
    pre-existing oversized file nor a rotation leaves one over the limit.
    Returns the file's repository-relative path for a row to point at, or
    None when nothing was written; a write error never hides the failure
    being recorded.
    """
    if not causes:
        return None
    data = _newest_lines(
        b"".join(_diagnostic_line(source, field, cause) for field, cause in causes), _DIAG_MAX_FILE_BYTES
    )
    name = record_path.with_suffix(".diag").name
    try:
        directory_fd = os.open(record_path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    except OSError:
        return None
    fd: int | None = None
    try:
        if not stat.S_ISREG(os.stat(record_path.name, dir_fd=directory_fd, follow_symlinks=False).st_mode):
            return None
        for _attempt in range(3):
            fd = _open_diagnostic(directory_fd, name)
            fcntl.flock(fd, fcntl.LOCK_EX)
            # Another writer may have rotated the file between our open and lock.
            if os.stat(name, dir_fd=directory_fd, follow_symlinks=False).st_ino != os.fstat(fd).st_ino:
                os.close(fd)
                fd = None
                continue
            if os.fstat(fd).st_size + len(data) > _DIAG_MAX_FILE_BYTES:
                os.replace(name, name + _DIAG_ROTATED_SUFFIX, src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
                _bound_diagnostic_fd(fd)  # the rotated copy, still locked: never left over the limit
                os.close(fd)
                fd = None
                continue
            _bound_rotated_diagnostic(directory_fd, name + _DIAG_ROTATED_SUFFIX)
            view = memoryview(data)
            while view:
                view = view[os.write(fd, view) :]
            break
        else:
            return None
    except OSError:
        return None
    finally:
        if fd is not None:
            os.close(fd)
        os.close(directory_fd)
    path = record_path.with_suffix(".diag")
    try:
        return path.resolve().relative_to(_REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return f"{path.parent.name}/{path.name}"


def _record_diagnostic(task_id: object, cause: _TypedCause | None, *, source: str, field: str = "") -> str | None:
    """Record ``cause``'s raw text beside ``task_id``'s record (:func:`_append_diagnostics`); its pointer or None."""
    if cause is None or not isinstance(task_id, str) or not task_id:
        return None
    return _append_diagnostics(_state_path_no_create(task_id), [(field or source, cause)], source=source)


def _publish_cause(task_id: object, cause: _TypedCause, *, source: str, field: str = "") -> str:
    """Record ``cause`` locally and return its public form: the producer side of :func:`public_cause`."""
    _record_diagnostic(task_id, cause, source=source, field=field)
    return cause.public()


def _worktree_diff_read(
    worktree: Path, diff_args: Sequence[str], *, git_options: Sequence[str] = ()
) -> tuple[str | None, _TypedCause | None]:
    """``(git diff <diff_args>, None)`` as if every change, untracked files included, were committed; ``(None, why)``.

    Untracked files are marked intent-to-add in a throwaway copy of the index
    (no file content is written to the object store) so they show up as
    additions; the real index is never touched. ``why`` is
    ``temp_index_failed`` while the scratch index is being made and
    ``diff_command_failed`` for the diff itself (#9878).
    """
    env = _sanitized_git_env()
    index_command = ["git", "rev-parse", "--path-format=absolute", "--git-path", "index"]
    step, code = index_command, "temp_index_failed"
    try:
        index_proc = subprocess.run(
            index_command,
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=env,
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
        if index_proc.returncode != 0:
            return None, _git_cause("temp_index_failed", index_proc)
        step = []  # creating the scratch index: no git command runs
        with tempfile.TemporaryDirectory(prefix="lu-finalize-index-") as scratch:
            scratch_index = Path(scratch) / "index"
            real_index = Path(index_proc.stdout.strip())
            if real_index.is_file():
                shutil.copyfile(real_index, scratch_index)
            scratch_env = {**env, "GIT_INDEX_FILE": str(scratch_index)}
            add_command = ["git", "add", "-A", "--intent-to-add"]
            step = add_command
            add_proc = subprocess.run(
                add_command,
                cwd=worktree,
                capture_output=True,
                text=True,
                check=False,
                env=scratch_env,
                timeout=DEFAULT_GIT_TIMEOUT_S,
            )
            if add_proc.returncode != 0:
                return None, _git_cause("temp_index_failed", add_proc)
            diff_command = ["git", *git_options, "diff", *diff_args]
            step, code = diff_command, "diff_command_failed"
            diff_proc = subprocess.run(
                diff_command,
                cwd=worktree,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                env=scratch_env,
                timeout=DEFAULT_GIT_TIMEOUT_S,
            )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, _exception_cause(code, exc, command=step or None)
    if diff_proc.returncode != 0:
        return None, _git_cause("diff_command_failed", diff_proc)
    return diff_proc.stdout, None


def _auto_finalize_additions_deletions(worktree: Path) -> tuple[tuple[str, ...], tuple[str, ...]] | None:
    """Files added and deleted relative to ``HEAD`` if every change were committed; None when unknown.

    Renames are not detected: git pairs a move only above a similarity
    threshold, so a caller that must not split a move treats every deletion
    as a possible source of every addition.
    """
    output = _worktree_diff_output(worktree, ["--no-renames", "--name-status", "-z", "HEAD", "--"])
    if output is None:
        return None
    fields = output.split("\0")
    added: list[str] = []
    deleted: list[str] = []
    for index in range(0, len(fields) - 1, 2):
        status, path = fields[index], fields[index + 1]
        if not status or not path:
            break
        if status == "A":
            added.append(path)
        elif status == "D":
            deleted.append(path)
    return tuple(added), tuple(deleted)


def _kimi_worker_refusal(
    task_id: str,
    *,
    agent: str,
    model: str | None,
    mode: str,
    cwd: Path,
    review: bool,
    prompt: str = "",
) -> tuple[str | None, Any]:
    """The worker-side gate: ``(refusal, admitted target)``; installs the Kimi worktree boundary when it admits.

    The worker's seat and model are resolved and admitted in one step
    (``resolve_and_admit``); the worker invokes the admitted target.

    The refusal is a public cause only (#9878). Non-Kimi admission refusals
    settle an existing task record as failed with the typed cause and local
    reason. A refused Kimi worker preserves its zero-write policy boundary;
    tree reader and boundary errors go to the task's local diagnostic file.

    A Kimi seat is refused unless its mode and review flags are admitted (read
    first, from the argv alone), the task's owned paths pass admission read in
    ``cwd`` — the tree the worker runs in — and in the commit checked out
    there, and ``cwd`` is the task's worktree, where the boundary (hooks and
    push block, ``kimi_boundary``) must install. For any other seat a boundary
    left in ``cwd`` by an earlier Kimi run is taken down. Writes nothing but
    that worktree's git config and hooks directory.
    """
    from scripts.agent_runtime import kimi_boundary
    from scripts.agent_runtime.kimi_admission import (
        ADMITTED_MODE,
        KimiAdmissionRefused,
        is_kimi_seat,
    )
    from scripts.agent_runtime.mechanical_admission import MechanicalAdmissionRefused
    from scripts.agent_runtime.target_admission import (
        ReviewAdmissionRefused,
        mechanical_worker_scope,
        resolve_and_admit,
    )

    boundary_errors = (kimi_boundary.BoundaryError, OSError, subprocess.SubprocessError)
    if not is_kimi_seat(agent, model=model):
        if mode in _WRITE_CAPABLE_MODES and kimi_boundary.is_installed(cwd):
            try:
                kimi_boundary.remove(cwd, env=_sanitized_git_env())
            except boundary_errors as exc:
                return _publish_cause(task_id, _exception_cause("boundary_remove_failed", exc), source="worker"), None
        try:
            launch = _read_state_json(_state_path_no_create(task_id)) or {}
            scope = mechanical_worker_scope(launch, mode=mode, model=model, prompt=prompt)
            scope["review"] = review or bool(launch.get("review")) or bool(scope.get("review"))
            (target,) = resolve_and_admit(
                (agent,), model=model, mode=mode, repo_root=_REPO_ROOT,
                trees=lambda: _kimi_worktree_trees(cwd), **scope,
            )
        except (MechanicalAdmissionRefused, ReviewAdmissionRefused, KimiAdmissionRefused) as exc:
            code = (
                "mechanical_admission_refused" if isinstance(exc, MechanicalAdmissionRefused)
                else "review_admission_refused" if isinstance(exc, ReviewAdmissionRefused)
                else "kimi_admission_refused"
            )
            cause = _publish_cause(task_id, _TypedCause(code, diagnostic=str(exc)), source="worker")
            if launch:
                launch.update({
                    "status": "failed", "finished_at": datetime.now(UTC).isoformat(),
                    "failure_reason": cause, "last_error": cause,
                    "returncode_reason": cause, "returncode": None, "exit_code": 1,
                    "stderr_excerpt": str(exc),
                })
                _write_state_atomic(_state_path_no_create(task_id), launch)
            return cause, None
        return None, target
    try:
        if mode != ADMITTED_MODE or review:
            # Refused by mode or review alone: no need to read the task record (or create its directory).
            resolve_and_admit((agent,), model=model, mode=mode, review=review)
        # Read-only: a refused worker must leave no task directory or file behind.
        launch = _read_state_json(_state_path_no_create(task_id)) or {}
        owned = _declared_owned_paths(launch.get("owned_paths")) or ()
        (target,) = resolve_and_admit(
            (agent,),
            model=model,
            mode=mode,
            review=review,
            paths=owned,
            repo_root=_REPO_ROOT,
            trees=lambda: _kimi_worktree_trees(cwd),
        )
    except KimiAdmissionRefused as exc:
        if not exc.read_errors:
            # A policy refusal: its text is fixed policy that the dispatch-time gate prints in full,
            # and a refused Kimi worker writes nothing.
            return _TypedCause("kimi_admission_refused").public(), None
        # A tree reader failed: the refusal names its class; the reader's message stays local.
        cause = _exception_cause("kimi_admission_refused", exc.read_errors[0])
        detail = "\n".join(f"{type(error).__name__}: {error}" for error in exc.read_errors)
        return _publish_cause(task_id, dataclasses.replace(cause, diagnostic=f"{exc}\n{detail}"), source="worker"), None
    worktree = launch.get("worktree_path")
    if not worktree or Path(worktree).resolve() != cwd.resolve():
        return _TypedCause("kimi_worktree_mismatch").public(), None
    base_ref = _commit_count_base_ref(cwd, str(launch.get("worktree_base") or "main"))
    try:
        kimi_boundary.install(cwd, agent=agent, base_ref=base_ref, owned_paths=owned, env=_sanitized_git_env())
    except boundary_errors as exc:
        return _publish_cause(task_id, _exception_cause("boundary_install_failed", exc), source="worker"), None
    return None, target


def _kimi_diff_refusal(worktree: Path, base_ref: str, agent: str, *, base_sha: str | None = None) -> str | None:
    """The refusal when a Kimi worker's changed files are not plain UTF-8 text or hold Cyrillic text; None otherwise.

    The changes run from the merge base with ``base_ref`` to the working tree,
    so they cover the worker's own commits and its uncommitted and untracked
    files. Each changed path's post-image is read in full, so git's binary
    classification cannot hide text. When ``base_ref`` was deleted after
    merging, falls back to the recorded ``base_sha`` and then the default-branch
    merge base (#9489). Fails closed: changes that cannot be read are a refusal
    that names only its typed cause (#9878); see :func:`_kimi_diff_refusal_detail`.
    """
    return _kimi_diff_refusal_detail(worktree, base_ref, agent, base_sha=base_sha)[0]


def _kimi_diff_refusal_detail(
    worktree: Path, base_ref: str, agent: str, *, base_sha: str | None = None
) -> tuple[str | None, _TypedCause | None]:
    """``(refusal, cause)`` for :func:`_kimi_diff_refusal`; ``cause`` is set when the changes could not be read.

    The caller records ``cause`` with :func:`_record_diagnostic`: its raw
    diagnostic never enters the refusal.
    """
    from scripts.agent_runtime import kimi_boundary

    merge_base, why = _resolve_merge_base_detail(worktree, base_ref, base_sha=base_sha)
    if merge_base is None:
        why = why or _TypedCause("merge_base_unresolved", "merge-base")
        return _kimi_unreadable(agent, why), why
    name_status, why = _worktree_diff_read(worktree, ["--name-status", "-z", "--no-renames", merge_base, "--"])
    if name_status is None:
        why = why or _TypedCause("diff_command_failed", "diff")
        return _kimi_unreadable(agent, why), why
    return _kimi_changes_refusal(
        agent,
        lambda: kimi_boundary.changes(
            worktree, kimi_boundary.parse_name_status(name_status), after=None, env=_sanitized_git_env()
        ),
    )


def _kimi_unreadable(agent: str, cause: _TypedCause) -> str:
    """The typed refusal for Kimi changes that could not be read: only ``cause``'s public form (#9878)."""
    from scripts.agent_runtime.kimi_admission import format_refusal

    return format_refusal(agent, [f"the finalized changes could not be read for Ukrainian content [{cause.public()}]"])


def _kimi_changes_refusal(agent: str, read: Callable[[], Any]) -> tuple[str | None, _TypedCause | None]:
    """Run the Kimi content check on the changes ``read()`` returns: ``(refusal, cause)``, ``(None, None)`` on a pass.

    Each way the changes can fail to be read is a typed refusal (#9878): a
    changed file that cannot be read (``file_unreadable``), git output that
    cannot be parsed (``changes_parse_failed``), and git or the filesystem
    failing (``changes_unreadable``).
    """
    from scripts.agent_runtime import kimi_boundary
    from scripts.agent_runtime.kimi_admission import KimiAdmissionRefused, refuse_kimi_changes

    try:
        refuse_kimi_changes(agent, read())
    except KimiAdmissionRefused as exc:
        return str(exc), None
    except kimi_boundary.ChangeUnreadable as exc:
        cause = _TypedCause(
            "file_unreadable", error=exc.cause, path=exc.path, diagnostic=f"{exc}: {exc.__cause__ or ''}"
        )
    except ValueError as exc:
        cause = _exception_cause("changes_parse_failed", exc)
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        cause = _exception_cause("changes_unreadable", exc)
    else:
        return None, None
    return _kimi_unreadable(agent, cause), cause


def _advisory_ceiling_check(
    worktree: Path | None, base_branch: str, envelope: Mapping[str, Any], *, base_sha: str | None = None, round_start_head: str | None = None
) -> dict[str, Any]:
    """Measure a bounded worker's changes against its envelope ceilings (#9275); unmeasurable is reported as such.

    Changes run from the round-start head when supplied, otherwise from the
    merge base with the base branch, to the working tree:
    the worker's commits plus its uncommitted and untracked files. When the base
    branch was deleted after merging, falls back to the recorded ``base_sha``
    and then the default branch (#9489).
    """
    try:
        max_files = int(envelope["max_changed_files"])
        max_loc = int(envelope["max_non_test_loc"])
    except (KeyError, TypeError, ValueError):
        return {"measured": False, "error": "the task record's envelope has no ceilings"}
    numstat, error = _advisory_worker_diff(
        worktree, base_branch, ["--numstat", "-z", "--no-renames"], base_sha=base_sha, round_start_head=round_start_head
    )
    if numstat is None:
        return {"measured": False, "error": error}
    try:
        entries = bounded_advisory.parse_numstat_z(numstat)
    except ValueError as exc:
        return {"measured": False, "error": str(exc)}
    return bounded_advisory.ceiling_verdict(entries, max_changed_files=max_files, max_non_test_loc=max_loc)


def _advisory_worker_diff(
    worktree: Path | None,
    base_branch: str,
    diff_args: Sequence[str],
    *,
    committed_only: bool = False,
    base_sha: str | None = None,
    round_start_head: str | None = None,
) -> tuple[str | None, str | None]:
    """``(git diff <diff_args> <merge-base>, None)`` over the worker's changes, or ``(None, why)`` when unreadable.

    Changes run from the round-start head when supplied, otherwise from the
    merge base with the base branch, to the working tree:
    the worker's commits plus its uncommitted and untracked files; with
    ``committed_only``, to ``HEAD``: its commits alone. When the base branch was
    deleted after merging, falls back to the recorded ``base_sha`` and then the
    default branch (#9489).
    """
    if worktree is None or not worktree.is_dir():
        return None, "no worktree to measure"
    if round_start_head:
        try:
            subprocess.run(
                ["git", "rev-parse", "--verify", f"{round_start_head}^{{commit}}"],
                cwd=worktree,
                capture_output=True,
                check=True,
                text=True,
                env=_sanitized_git_env(),
                timeout=DEFAULT_GIT_TIMEOUT_S,
            )
        except subprocess.CalledProcessError:
            return None, f"round-start head {round_start_head} is missing"
        except (OSError, subprocess.TimeoutExpired) as exc:
            # Class only: exception messages can contain private host paths (#9878).
            return None, f"round-start head could not be read ({type(exc).__name__})"
        merge_base = round_start_head
    else:
        base_ref = _commit_count_base_ref(worktree, base_branch)
        merge_base = _resolve_merge_base(worktree, base_ref, base_sha=base_sha)
        if not merge_base:
            return None, "merge-base with the base branch is unknown"

    error_detail = "the worker's diff could not be read"
    for _attempt in range(2):
        if committed_only:
            try:
                proc = subprocess.run(
                    ["git", "diff", *diff_args, merge_base, "HEAD", "--"],
                    cwd=worktree,
                    capture_output=True,
                    text=True,
                    check=False,
                    env=_sanitized_git_env(),
                    timeout=DEFAULT_GIT_TIMEOUT_S,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                # The class only: the measurement is recorded and shown; the message can hold host paths (#9878).
                error_detail = f"the worker's committed diff could not be read ({type(exc).__name__})"
            else:
                if proc.returncode == 0:
                    return proc.stdout, None
                error_detail = f"the worker's committed diff could not be read (return code {proc.returncode})"
        else:
            output, why = _worktree_diff_read(worktree, [*diff_args, merge_base, "--"])
            if output is not None:
                return output, None
            error_detail = f"the worker's diff could not be read ({why.public()})" if why else "the worker's diff could not be read"
    return None, error_detail


# #9275: the record keys the completion gates write their measurement to.
_ADVISORY_GATE_KEYS = ("advisory_ceiling_check", "advisory_exempt_change_check")
_INTERRUPTED_BEFORE_COMPLETION_GATES = "interrupted before the completion gates ran"


def _advisory_completion_gate(
    record: Mapping[str, Any], worktree: Path | None
) -> tuple[str, dict[str, Any], str | None, str] | None:
    """The #9275 completion gate a write task's record calls for, run on its changes; None when neither applies.

    ``(record key, check, failure code or None, detail)``: the envelope
    ceilings of a bounded worker, or the changed-path classification of a
    Ukrainian content exemption. Unmeasurable changes fail.
    """
    base_branch = str(record.get("worktree_base") or "main")
    base_sha = _recorded_base_sha(record)
    round_start_head = record.get("pinned_head")
    round_start_head = str(round_start_head).strip() if isinstance(round_start_head, str) else None
    admission = record.get(AUTHORING_REVIEW_STATE_KEY)
    if not round_start_head and (
        record.get("worktree_reused")
        or (isinstance(admission, dict) and admission.get("target") == "existing-branch")
    ):
        # A plain --branch attach has no pin; its recorded base is the round's
        # starting head. A fresh branch keeps the merge-base measurement.
        round_start_head = base_sha

    envelope = record.get("advisory_envelope")
    if isinstance(envelope, dict):
        ceiling = _advisory_ceiling_check(
            worktree, base_branch, envelope, base_sha=base_sha, round_start_head=round_start_head
        )
        failure = (
            bounded_advisory.CEILING_UNMEASURED
            if not ceiling.get("measured")
            else (bounded_advisory.CEILING_EXCEEDED if ceiling.get("exceeded") else None)
        )
        detail = "; ".join(ceiling.get("exceeded") or []) or str(ceiling.get("error") or "unmeasured")
        return "advisory_ceiling_check", ceiling, failure, detail
    if isinstance(record.get("advisory_exemption"), dict):
        check = _exempt_change_check(
            worktree, base_branch, base_sha=base_sha, round_start_head=round_start_head
        )
        failure = (
            bounded_advisory.EXEMPT_CHANGES_UNMEASURED
            if not check.get("measured")
            else (bounded_advisory.EXEMPT_CODE_CHANGE if check.get("problems") else None)
        )
        detail = "; ".join(check.get("problems") or []) or str(check.get("error") or "unmeasured")
        return "advisory_exempt_change_check", check, failure, detail
    return None


# #9275: the single definition of the completion gates a task record calls for.
# The worker's terminal settle runs them, and so does the ask-* review wrapper;
# success needs every applicable gate to pass. Recovery paths (stale-record
# settlement, rate-limit reclassification) apply :func:`recovery_requires_rerun`.
COMPLETION_GATE_BACKGROUND_LEFTOVERS = "background_leftovers"
COMPLETION_GATE_DELIVERY = "delivery"
COMPLETION_GATE_REVIEW_VERDICT = "review_verdict"
COMPLETION_GATE_ADVISORY_CEILING = "advisory_ceiling"
COMPLETION_GATE_ADVISORY_EXEMPT_CHANGE = "advisory_exempt_change"
# Recovery's pseudo-gate: a failure the record already carries is never overwritten.
COMPLETION_GATE_RECORDED_FAILURE = "recorded_failure"
# The delivery gate reads a zero-commit run's response; it cannot run when the saved response is gone or replaced.
COMPLETION_GATE_RESPONSE_UNAVAILABLE = "completion_gate_response_unavailable"
# Operator decision 2026-09-30 (option A): recovery never settles a record with a
# completion gate beyond delivery ``done``; it settles it ``failed`` with this cause.
RECOVERY_REQUIRES_RERUN = "recovery_requires_rerun"
# Record fields that hold a failure the worker already found.
_RECORDED_FAILURE_FIELDS = (
    "failure_reason",
    "review_verdict_failure",
    "no_deliverable_reason",
    "kimi_content_refusal",
    "agy_oauth_link_error",
    "read_only_mutation_paths",
)


@dataclass(frozen=True)
class CompletionGateResult:
    """One completion gate's verdict on a task record.

    ``failure`` is the typed cause (None when the gate passed), ``status`` the
    terminal status a failure settles, and ``record_key``/``check`` the
    measurement the gate writes to the record, when it has one.
    """

    gate: str
    failure: str | None
    detail: str = ""
    status: str = "failed"
    record_key: str | None = None
    check: dict[str, Any] | None = None


def applicable_completion_gates(record: Mapping[str, Any]) -> tuple[str, ...]:
    """Every completion gate the record calls for, in the order the worker runs them.

    An exit scan that did not rule out live background jobs (``leftovers_scan``
    other than clear) leaves the run unconfirmed; delivery binds every
    write-capable dispatch; the review verdict binds an opted-in review
    (``require_review_verdict``); a write-capable bounded worker has its envelope
    ceilings checked, else a content exemption its changed paths.
    """
    write = record.get("mode") in _WRITE_CAPABLE_MODES
    gates: list[str] = []
    if record.get("leftovers_scan") not in (None, worker_leftovers.SCAN_CLEAR) or record.get("incomplete_run_reason"):
        gates.append(COMPLETION_GATE_BACKGROUND_LEFTOVERS)
    if write:
        gates.append(COMPLETION_GATE_DELIVERY)
    if record.get("require_review_verdict"):
        gates.append(COMPLETION_GATE_REVIEW_VERDICT)
    if write and isinstance(record.get("advisory_envelope"), dict):
        gates.append(COMPLETION_GATE_ADVISORY_CEILING)
    elif write and isinstance(record.get("advisory_exemption"), dict):
        gates.append(COMPLETION_GATE_ADVISORY_EXEMPT_CHANGE)
    return tuple(gates)


def run_completion_gate(
    gate: str,
    record: Mapping[str, Any],
    *,
    response: str | None,
    commits_ahead: int | None,
    worktree: Path | None,
) -> CompletionGateResult:
    """Run one completion gate on the worker's response, commit count and tree.

    ``response`` None means the saved response is unavailable and ``worktree``
    None that the worker's tree is gone: a gate that needs either fails typed,
    never passes.
    """
    if gate == COMPLETION_GATE_BACKGROUND_LEFTOVERS:
        reason = record.get("incomplete_run_reason") or worker_leftovers.SCAN_UNKNOWN_REASON
        return CompletionGateResult(gate, str(reason), str(reason), status="needs_finalize")
    if gate == COMPLETION_GATE_DELIVERY:
        if response is None and commits_ahead == 0:
            # Only a zero-commit run reads the response (its no_change declaration).
            return CompletionGateResult(gate, COMPLETION_GATE_RESPONSE_UNAVAILABLE, "saved response unavailable")
        reason = _delivery_failure_reason(
            response or "", _parse_delivery_declaration(response or ""), commits_ahead=commits_ahead
        )
        return CompletionGateResult(gate, reason, reason or "", status=_NO_DELIVERABLE_STATUS)
    if gate == COMPLETION_GATE_REVIEW_VERDICT:
        reason = _review_verdict_failure_reason(response or "")
        return CompletionGateResult(gate, reason, reason or "")
    if gate in (COMPLETION_GATE_ADVISORY_CEILING, COMPLETION_GATE_ADVISORY_EXEMPT_CHANGE):
        advisory = _advisory_completion_gate(record, worktree)
        if advisory is None:
            raise ValueError(f"record does not call for completion gate {gate!r}")
        record_key, check, failure, detail = advisory
        return CompletionGateResult(gate, failure, detail if failure else "", record_key=record_key, check=check)
    raise ValueError(f"unknown completion gate {gate!r}")


def recorded_completion_failure(record: Mapping[str, Any]) -> CompletionGateResult | None:
    """A failure the record already carries, as a result with its typed cause; None when it carries none."""
    for field in _RECORDED_FAILURE_FIELDS:
        value = record.get(field)
        if not value:
            continue
        cause = value if isinstance(value, str) else field
        status = _NO_DELIVERABLE_STATUS if field == "no_deliverable_reason" else "failed"
        return CompletionGateResult(COMPLETION_GATE_RECORDED_FAILURE, cause, f"{field}: {cause}", status=status)
    return None


def saved_task_response(record: Mapping[str, Any], record_path: Path | None = None) -> str | None:
    """The worker's response as the record saved it, or None when it is gone or was replaced.

    Recovery's delivery gate reads it for a zero-commit run. The ``.result`` sidecar next to the record is read first (it moves with the
    record into the archive), then ``result_file``. A text whose length is not
    the recorded ``response_chars`` was replaced after the worker finished. A
    record with an empty response wrote no result file: that response is ``""``.
    """
    chars = record.get("response_chars")
    known_chars = isinstance(chars, int) and not isinstance(chars, bool)
    candidates: list[Path] = []
    if record_path is not None:
        candidates.append(record_path.with_suffix(".result"))
    result_file = record.get("result_file")
    if isinstance(result_file, str) and result_file:
        candidates.append(Path(result_file))
    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        return text if not known_chars or len(text) == chars else None
    if known_chars and chars == 0 and not result_file:
        return ""
    return None


def recovery_requires_rerun(record: Mapping[str, Any]) -> CompletionGateResult | None:
    """Recovery's refusal for a record with any completion gate beyond delivery; None for a delivery-only record.

    Operator decision 2026-09-30 (option A): recovery runs after the worker is
    gone, so it never re-measures a tree or reconstructs a response to settle
    such a record ``done``. It settles it ``failed`` with :data:`RECOVERY_REQUIRES_RERUN`,
    or with the failure the record already carries, for the driver to re-run
    or finalize by hand.
    """
    gated = [gate for gate in applicable_completion_gates(record) if gate != COMPLETION_GATE_DELIVERY]
    if not gated:
        return None
    recorded = recorded_completion_failure(record)
    cause = recorded.failure if recorded is not None else RECOVERY_REQUIRES_RERUN
    detail = f"completion gates {', '.join(gated)} run only in the worker; re-run the task or finalize it by hand"
    return CompletionGateResult(gated[0], cause, detail)


def completion_gate_recovery_failure(
    record: Mapping[str, Any], *, response: str | None, commits_ahead: int | None
) -> CompletionGateResult | None:
    """The reason recovery may not report this record ``done``; None when it may.

    A gated record is refused by :func:`recovery_requires_rerun`; a delivery-only
    record keeps a failure it already carries, else its delivery gate runs on the
    saved ``response`` and the ``commits_ahead`` evidence the caller holds now.
    """
    refusal = recovery_requires_rerun(record)
    if refusal is not None:
        return refusal
    recorded = recorded_completion_failure(record)
    if recorded is not None:
        return recorded
    return first_completion_gate_failure(record, response=response, commits_ahead=commits_ahead, worktree=None)


def first_completion_gate_failure(
    record: Mapping[str, Any], *, response: str | None, commits_ahead: int | None, worktree: Path | None
) -> CompletionGateResult | None:
    """Run every gate in :func:`applicable_completion_gates` in order; the first failure, or None when all pass."""
    for gate in applicable_completion_gates(record):
        result = run_completion_gate(gate, record, response=response, commits_ahead=commits_ahead, worktree=worktree)
        if result.failure is not None:
            return result
    return None


def _advisory_completion_gate_fails(record: Mapping[str, Any], worktree: Path) -> bool:
    """True when the record's #9275 completion gate already fails, so auto-finalize must not commit or open a PR."""
    gate = _advisory_completion_gate(record, worktree)
    return gate is not None and gate[2] is not None


def _exempt_change_check(
    worktree: Path | None, base_branch: str, *, base_sha: str | None = None, round_start_head: str | None = None
) -> dict[str, Any]:
    """Classify every path a content-exempt worker changed (#9275); unmeasurable is reported as such.

    Every committed path is classified, and every uncommitted one except the
    scratch residue auto-finalize never publishes (``_is_disposable_auto_finalize_path``),
    which is listed as ``ignored_residue``. When the base branch was deleted
    after merging, falls back to the recorded ``base_sha`` and then the default
    branch (#9489).
    """
    name_args = ["--name-only", "-z", "--no-renames"]
    names, error = _advisory_worker_diff(
        worktree, base_branch, name_args, base_sha=base_sha, round_start_head=round_start_head
    )
    committed, committed_error = _advisory_worker_diff(
        worktree, base_branch, name_args, committed_only=True, base_sha=base_sha, round_start_head=round_start_head
    )
    if names is None or committed is None:
        return {"measured": False, "error": error or committed_error}
    assert worktree is not None
    committed_paths = {name for name in committed.split("\0") if name}
    all_paths = {name for name in names.split("\0") if name} | committed_paths
    residue = sorted(
        path for path in all_paths if path not in committed_paths and _is_disposable_auto_finalize_path(path)
    )
    changed = sorted(all_paths - set(residue))
    try:
        problems = bounded_advisory.exempt_change_problems(changed, worktree)
    except RuntimeError as exc:
        return {"measured": False, "error": str(exc)}
    return {"measured": True, "changed_paths": changed, "ignored_residue": residue, "problems": problems}


def _cross_boundary_moves(added: Sequence[str], deleted: Sequence[str], owned: Sequence[str]) -> set[str]:
    """Additions and deletions that could be one move across the owned-path boundary.

    Every deletion is a possible source of every addition, so an owned
    addition is paired with any outside deletion and an owned deletion with
    any outside addition; both sides of each pairing are returned.
    """
    moves: set[str] = set()
    for sources, targets in ((deleted, added), (added, deleted)):
        outside = [path for path in sources if not _path_is_owned(path, owned)]
        inside = [path for path in targets if _path_is_owned(path, owned)]
        if outside and inside:
            moves.update(outside, inside)
    return moves


def _current_branch(worktree: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    branch = (proc.stdout or "").strip()
    return branch or None


def _x_agent_task_id(agent: str, task_id: str) -> str:
    normalized = _normalize_task_id(agent, task_id)
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", normalized).strip(".-")
    return safe or "task"


def _x_agent_trailer(agent: str, task_id: str) -> str:
    return f"X-Agent: {agent}/{_x_agent_task_id(agent, task_id)}"


def _build_worker_env(
    *,
    task_id: str,
    dispatch_agent: str,
    attribution: Any | None = None,
    run_nonce: str = "",
    runtime_tmp_root: Path | str | None = None,
    runtime_tmp_namespace_root: Path | str | None = None,
    worktree_path: Path | None = None,
    allow_merge: bool = False,
    base_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Construct the execution environment for a dispatched worker process."""
    source = dict(os.environ if base_env is None else base_env)
    worker_env = _pinned_worker_venv_env(source)
    if attribution is not None:
        worker_env["LU_RUNTIME_INITIATOR"] = getattr(attribution, "initiator", str(attribution))
        worker_env["LU_RUNTIME_INITIATOR_SOURCE"] = getattr(attribution, "source", "")
    if run_nonce:
        worker_env["LU_RUNTIME_RUN_NONCE"] = run_nonce
    # Explicit dispatch-worker identity (#7827): the SessionStart gate uses
    # this marker to skip the per-agent thread lease, which belongs to the
    # orchestrator of the agent family, never to a headless worker. Both
    # names are allowlisted in agent_runtime/env_sanitize.py (name and
    # value lists — a task id containing "sk-" must survive the secret
    # redactor), so the marker reaches the harness CLI's SessionStart hook.
    # The marker is the primary signal: a read-only dispatch without
    # --worktree runs from the primary checkout, so the
    # .worktrees/dispatch/<agent>/<task>/ path is only the fallback.
    worker_env["LEARN_UKRAINIAN_DISPATCH_TASK_ID"] = task_id
    worker_env["LEARN_UKRAINIAN_DISPATCH_AGENT"] = dispatch_agent
    worker_env["LU_X_AGENT_TRAILER"] = _x_agent_trailer(dispatch_agent, task_id)
    # #8645 part B: CI's `--override-ini addopts=-v` drops the pyproject
    # `-p ci.pytest_dispatch_cap`. Load it from the environment instead.
    _dispatch_cap_plugin = "ci.pytest_dispatch_cap"
    _pytest_plugins = [part.strip() for part in worker_env.get("PYTEST_PLUGINS", "").split(",") if part.strip()]
    if _dispatch_cap_plugin not in _pytest_plugins:
        _pytest_plugins.append(_dispatch_cap_plugin)
    worker_env["PYTEST_PLUGINS"] = ",".join(_pytest_plugins)
    # #8795: "ci.pytest_dispatch_cap" only resolves via pyproject.toml's
    # `pythonpath = ["scripts"]`, which is rootdir-relative and inactive for a
    # pytest process started elsewhere (e.g. a test's own `pytester` subprocess
    # in a temp dir). PYTHONPATH is an interpreter-level env var, so it makes
    # the import resolve regardless of that nested pytest's rootdir.
    _worker_scripts_dir = str((worktree_path if worktree_path is not None else _REPO_ROOT) / "scripts")
    _worker_pythonpath = [part for part in worker_env.get("PYTHONPATH", "").split(os.pathsep) if part]
    if _worker_scripts_dir not in _worker_pythonpath:
        worker_env["PYTHONPATH"] = os.pathsep.join([_worker_scripts_dir, *_worker_pythonpath])
    _inject_gh_token_for_agent(worker_env, dispatch_agent)
    _scrub_unusable_gh_config_dir(worker_env)
    worker_env["AGENT_NO_TELEMETRY_FOOTER"] = "1"
    if runtime_tmp_root is not None:
        worker_env["TMPDIR"] = str(runtime_tmp_root)
        worker_env["LU_RUNTIME_TMP_ROOT"] = str(runtime_tmp_root)
    if runtime_tmp_namespace_root is not None:
        worker_env["LU_RUNTIME_TMP_BASE_ROOT"] = str(Path(runtime_tmp_namespace_root).parent)
    if worktree_path is not None:
        _apply_worktree_git_ceiling(worker_env, worktree_path)
    if allow_merge:
        worker_env.pop("AGENT_NO_MERGE", None)
        worker_env["AGENT_ALLOW_MERGE"] = "1"
    else:
        worker_env["AGENT_NO_MERGE"] = "1"
        worker_env.pop("AGENT_ALLOW_MERGE", None)
    return worker_env


def _push_auto_finalize_branch(worktree: Path, branch: str) -> None:
    try:
        proc = subprocess.run(
            ["git", "push", "-u", "origin", branch],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_NETWORK_GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        raise _TypedFailure(
            f"git push timed out after {DEFAULT_NETWORK_GIT_TIMEOUT_S}s",
            _exception_cause("auto_finalize_push_failed", exc, command=["git", "push"]),
        ) from exc
    if proc.returncode != 0:
        raise _TypedFailure("git push failed", _remote_git_cause("auto_finalize_push_failed", proc))


@publication_boundary(RuntimeError)
def _create_auto_finalize_pr(
    worktree: Path,
    *,
    branch: str,
    base_branch: str,
    title: str,
    body: str,
) -> str | None:
    try:
        proc = request_run(
            Request("pr-create", draft=True, base=base_branch, head=branch, title=title, body=body),
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GH_CLI_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        raise _TypedFailure(
            f"gh pr create timed out after {DEFAULT_GH_CLI_TIMEOUT_S}s",
            _exception_cause("auto_finalize_pr_failed", exc),
        ) from exc
    except PublishBlocked as exc:
        # The OPSEC gate refused the publication: typed, its reason kept for the local diagnostic (#9878).
        raise _TypedFailure(
            "publish blocked", _TypedCause("auto_finalize_publish_blocked", diagnostic=str(exc))
        ) from None
    if proc.returncode != 0:
        raise _TypedFailure(
            "gh pr create failed",
            _TypedCause(
                "auto_finalize_pr_failed", exit_status=proc.returncode, diagnostic=_format_process_failure(proc)
            ),
        )
    lines = [line.strip() for line in (proc.stdout or "").splitlines() if line.strip()]
    return lines[-1] if lines else None


def _auto_finalize_dirty_worktree(
    *,
    worktree: Path,
    task_id: str,
    agent: str,
    model: str | None = None,
    branch: str | None,
    base_branch: str,
    open_pr: bool = False,
    owned_paths: object = None,
) -> AutoFinalizeResult:
    """Stage, commit, and push the owned part of a cleanly exited dirty dispatch.

    ``owned_paths`` is the task record's ``owned_paths`` list, written at
    dispatch from the task's explicit ``--owned-path`` values (#8991). Only
    changed files under them are staged and committed; the rest stay
    uncommitted in the tree and come back as ``skipped_paths``. A move across
    the owned-path boundary is never split, whatever git's rename similarity
    says: when any file outside the owned paths was deleted, no owned
    addition is committed, and when any outside file was added, no owned
    deletion is. Those paths are listed in ``cross_boundary_moves``.
    A task that declared no owned paths gets no commit at all
    (``no_owned_paths_declared``). ``error`` is a public cause (#9878): git's
    stderr and an exception's message go only to the task's ``.diag`` file.
    """
    owned = _declared_owned_paths(owned_paths)
    all_changed = _auto_finalize_changed_files(worktree)
    changed_files: tuple[str, ...] = ()
    skipped: tuple[str, ...] = ()
    moves: tuple[str, ...] = ()

    def _result(**fields: Any) -> AutoFinalizeResult:
        return AutoFinalizeResult(owned_paths=owned, skipped_paths=skipped, cross_boundary_moves=moves, **fields)

    try:
        worktree_proc = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return _result(
            ok=False,
            error="not a git worktree",
            changed_files=changed_files,
        )
    if worktree_proc.returncode != 0 or (worktree_proc.stdout or "").strip() != "true":
        return _result(
            ok=False,
            error="not a git worktree",
            changed_files=changed_files,
        )

    if not all_changed:
        return _result(ok=False, error="clean-tree")
    if _auto_finalize_is_junk_only(all_changed):
        return _result(
            ok=False,
            error=_NO_DELIVERABLE_JUNK_ONLY_WORKTREE_REASON,
            changed_files=all_changed,
        )
    if owned is None:
        skipped = all_changed
        return _result(ok=False, error=_AUTO_FINALIZE_NO_OWNED_PATHS_REASON)
    added_deleted = _auto_finalize_additions_deletions(worktree)
    if added_deleted is None:
        return _result(ok=False, error="move detection failed; nothing committed")
    moves = tuple(sorted(_cross_boundary_moves(*added_deleted, owned)))
    changed_files = tuple(path for path in all_changed if path not in moves and _path_is_owned(path, owned))
    skipped = tuple(path for path in all_changed if path not in changed_files)
    if not changed_files or _auto_finalize_is_junk_only(changed_files):
        # Real work exists only outside the declared scope: a human decides.
        return _result(ok=False, error=_AUTO_FINALIZE_NOTHING_OWNED_REASON, changed_files=changed_files)

    def _failed(cause: _TypedCause, **fields: Any) -> AutoFinalizeResult:
        error = _publish_cause(task_id, cause, source="auto_finalize", field="auto_finalize.error")
        return _result(ok=False, error=error, changed_files=changed_files, **fields)

    resolved_branch = branch or _current_branch(worktree)
    if not resolved_branch or resolved_branch in {"HEAD", "main", "master"}:
        return _failed(
            _TypedCause("auto_finalize_unsafe_branch", diagnostic=f"unsafe or unresolved branch {resolved_branch!r}")
        )

    safe_task = _x_agent_task_id(agent, task_id)
    subject = f"chore(dispatch): finalize {agent} task {safe_task}"
    body = (
        "Auto-finalized a dirty delegate worktree after the agent exited "
        "with returncode 0 but made no commits.\n\n"
        f"Delegate task: {task_id}\n"
        f"Agent: {agent}"
    )

    # git reads the exact file list from stdin as literal pathspecs; ``commit
    # --only`` then leaves anything the worker had already staged outside that
    # list out of the commit.
    scoped_input = "\0".join(changed_files)
    scoped_args = ["--pathspec-from-file=-", "--pathspec-file-nul"]
    git_prefix = ["git", "--literal-pathspecs"]
    commit_sha: str | None = None
    # This commit is made by the supervisor, outside build_agent_env. Use the
    # worker lane's identity instead of the launcher's inherited driver identity.
    from scripts.lib.git_identity import git_identity_env

    commit_env = {**_sanitized_git_env(), **git_identity_env(agent, model)}
    try:
        add_proc = subprocess.run(
            [*git_prefix, "add", "-A", *scoped_args],
            cwd=worktree,
            input=scoped_input,
            capture_output=True,
            text=True,
            check=False,
            env=commit_env,
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
        if add_proc.returncode != 0:
            return _failed(_git_cause("auto_finalize_add_failed", add_proc))

        commit_proc = subprocess.run(
            [
                *git_prefix,
                "commit",
                "--only",
                *scoped_args,
                "-m",
                subject,
                "-m",
                body,
                "--trailer",
                _x_agent_trailer(agent, task_id),
            ],
            cwd=worktree,
            input=scoped_input,
            capture_output=True,
            text=True,
            check=False,
            env=commit_env,
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
        if commit_proc.returncode != 0:
            with contextlib.suppress(OSError, subprocess.TimeoutExpired):
                subprocess.run(
                    [*git_prefix, "restore", "--staged", *scoped_args],
                    cwd=worktree,
                    input=scoped_input,
                    capture_output=True,
                    text=True,
                    check=False,
                    env=_sanitized_git_env(),
                    timeout=DEFAULT_GIT_TIMEOUT_S,
                )
            return _failed(_git_cause("auto_finalize_commit_failed", commit_proc))

        commit_sha = _resolve_sha(worktree)
        _push_auto_finalize_branch(worktree, resolved_branch)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        step = exc.cmd if isinstance(exc, subprocess.TimeoutExpired) and isinstance(exc.cmd, (list, tuple)) else None
        causes = [_exception_cause("auto_finalize_failed", exc, command=step)]
        if commit_sha is not None:
            try:
                reset_proc = subprocess.run(
                    ["git", "reset", "--soft", "HEAD~1"],
                    cwd=worktree,
                    capture_output=True,
                    text=True,
                    check=False,
                    env=_sanitized_git_env(),
                    timeout=DEFAULT_GIT_TIMEOUT_S,
                )
            except (OSError, subprocess.TimeoutExpired) as reset_exc:
                causes.append(_exception_cause("auto_finalize_reset_failed", reset_exc, command=["git", "reset"]))
            else:
                if reset_proc.returncode != 0:
                    causes.append(_git_cause("auto_finalize_reset_failed", reset_proc))
                else:
                    commit_sha = None
        error = "; ".join(
            _publish_cause(task_id, cause, source="auto_finalize", field="auto_finalize.error") for cause in causes
        )
        return _result(ok=False, commit_sha=commit_sha, error=error, changed_files=changed_files)

    pr_url = None
    if open_pr:
        try:
            pr_url = _create_auto_finalize_pr(
                worktree,
                branch=resolved_branch,
                base_branch=_base_branch_name(base_branch),
                title=subject,
                body=(
                    f"Auto-finalized delegate task `{task_id}` for `{agent}`.\n\n"
                    "The agent exited with `returncode=0`, left a dirty worktree, "
                    "and had made zero commits, so delegate.py staged and pushed the work."
                ),
            )
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
            # The commit is already pushed. Never soft-reset it after a PR error.
            return _failed(_exception_cause("auto_finalize_pr_failed", exc), commit_sha=commit_sha)

    return _result(
        ok=True,
        commit_sha=commit_sha,
        pr_url=pr_url,
        changed_files=changed_files,
    )


_RESCUE_TERMINAL_STATUSES = frozenset(
    {"crashed", "timeout", "failed", "no_deliverable", "needs_finalize", "cancelled", "rate_limited"}
)
_RESCUE_MAX_FILE_BYTES = 5 * 1024 * 1024


class _RescueFailure(_TypedFailure):
    """A rescue step failed: its row shows only the :class:`_TypedCause`; the raw error goes to the ``.diag`` file."""

def _rescue_git(context: SafeGitContext, *args: str, **kwargs) -> subprocess.CompletedProcess[str]:
    """All rescue execution uses the fresh context, including checking and network proof."""
    return context.run(*args, **kwargs)


@dataclass(frozen=True)
class _RescueRepo:
    """Validated source registration, used only for ref reads and borrowed objects."""

    worktree: Path
    git_dir: Path
    admin_dir: Path

    @property
    def head_ref(self) -> str:
        return f"worktrees/{self.admin_dir.name}/HEAD"


def _rescue_canonical_push_url() -> str:
    """Driver-side destination; source repository configuration is not authority."""
    return CANONICAL_ORIGIN


def _rescue_execution_context(repo: _RescueRepo) -> SafeGitContext:
    from scripts.agent_runtime.agent_github_identity import resolve_agent_github_identity

    identity = resolve_agent_github_identity(
        bash_secrets_path=_BASH_SECRETS_PATH,
        repository="learn-ukrainian/learn-ukrainian.github.io",
    )
    if not identity.token:
        raise _RescueFailure("driver identity unavailable", _TypedCause("rescue_identity_unavailable"))
    return SafeGitContext(
        objects=repo.git_dir / "objects", origin=_rescue_canonical_push_url(),
        token=identity.token, temp_root=Path(tempfile.gettempdir()),
    )


def _rescue_repo(worktree: Path) -> _RescueRepo:
    """``worktree`` as a :class:`_RescueRepo`, read from the files git keeps, without running git in it."""
    from scripts.agent_runtime import kimi_boundary

    admin = kimi_boundary.worktree_git_dir(worktree)
    try:
        if admin is None:
            raise FileNotFoundError(".git")
        admin = admin.resolve(strict=True)
        git_dir = (admin / (admin / "commondir").read_text(encoding="utf-8").strip()).resolve(strict=True)
        registered = Path((admin / "gitdir").read_text(encoding="utf-8").strip()).resolve()
    except (OSError, ValueError) as exc:
        raise _RescueFailure(
            "the worktree's git directory cannot be read", _exception_cause("rescue_worktree_unregistered", exc)
        ) from exc
    if (
        git_dir != (_REPO_ROOT / ".git").resolve()
        or admin.parent != git_dir / "worktrees"
        or registered != (worktree / ".git").resolve()
    ):
        raise _RescueFailure(
            "the worktree is not a linked worktree of the main repository",
            _TypedCause("rescue_worktree_unregistered"),
        )
    return _RescueRepo(worktree, git_dir, admin)


def _rescue_head(repo: _RescueRepo, context: SafeGitContext) -> tuple[str, str] | None:
    """Resolve the worker HEAD by plumbing, then use only that exact object ID."""
    commit = context.read_source_ref(repo.git_dir, repo.head_ref)
    name = context.read_source_ref(repo.git_dir, repo.head_ref, symbolic=True)
    if commit.returncode or name.returncode or not commit.stdout.strip():
        return None
    full_name = name.stdout.strip()
    return commit.stdout.strip(), full_name.removeprefix("refs/heads/") if full_name.startswith("refs/heads/") else "HEAD"


def _rescue_base(repo: _RescueRepo, context: SafeGitContext, state: Mapping[str, Any]) -> str:
    base = str(state.get("worktree_base") or "main")
    for ref in (base, _origin_base_ref(base), _recorded_base_sha(state), "refs/remotes/origin/main", "refs/heads/main"):
        if ref:
            proc = context.read_source_ref(repo.git_dir, ref)
            if proc.returncode == 0:
                return proc.stdout.strip()
    raise _RescueFailure("base unavailable", _TypedCause("merge_base_unresolved", "rev-parse"))


def _rescue_commit_matches(context: SafeGitContext, commit: str, tree: str, parent: str) -> bool:
    proc = _rescue_git(context, "show", "-s", "--format=%T %P", commit)
    return proc.returncode == 0 and proc.stdout.split() == [tree, parent]


def _rescue_commit(context: SafeGitContext, tree: str, parent: str, *, agent: str, task_id: str) -> str:
    """Fixed driver commit identity, never the source repository's user config."""
    message = f"chore(dispatch): rescue {task_id}\n\nX-Agent: {agent}/{task_id}"
    proc = _rescue_git(
        context, "commit-tree", tree, "-p", parent, "-m", message,
    )
    if proc.returncode or not proc.stdout.strip():
        raise _RescueFailure("cannot commit rescue work", _git_cause("rescue_commit_failed", proc))
    return proc.stdout.strip()


def _rescue_remote_head(context: SafeGitContext, branch: str) -> str | None:
    proc = _rescue_git(context, "ls-remote", "--heads", "origin", f"refs/heads/{branch}", network=True)
    if proc.returncode:
        raise _RescueFailure("rescue remote proof unavailable", _remote_git_cause("rescue_remote_unverified", proc))
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        return None
    if len(lines) != 1 or lines[0].split("\t")[-1] != f"refs/heads/{branch}":
        raise _RescueFailure("rescue remote proof ambiguous", _TypedCause("rescue_remote_unverified", "ls-remote"))
    return lines[0].split("\t", 1)[0]


def _is_kimi_task_record(state: Mapping[str, Any]) -> bool:
    """Whether a task record names a Kimi seat or an effective Kimi model."""
    from scripts.agent_runtime.kimi_admission import is_kimi_seat

    model = state.get("model")
    return is_kimi_seat(str(state.get("agent") or ""), model=model if isinstance(model, str) else None)


def _kimi_tree_refusal(
    context: SafeGitContext, base: str, agent: str, *, tree: str
) -> tuple[str | None, _TypedCause | None]:
    """Existing Kimi checker on the exact captured tree, read only inside the context."""
    from scripts.agent_runtime import kimi_boundary
    from scripts.agent_runtime.kimi_admission import FileChange

    proc = _rescue_git(context, "diff-tree", "-r", "-z", "--name-status", "--no-renames", base, tree)
    if proc.returncode:
        why = _git_cause("diff_command_failed", proc)
        return _kimi_unreadable(agent, why), why

    def changes():
        result = []
        for status, path in kimi_boundary.parse_name_status(proc.stdout):
            if status == "D":
                result.append(FileChange(path, None, deleted=True))
                continue
            blob = _rescue_git(context, "cat-file", "blob", f"{tree}:{path}", binary=True)
            content = blob.stdout if blob.returncode == 0 else None
            result.append(FileChange(path, content))
        return result

    return _kimi_changes_refusal(agent, changes)


def _clean_rescue_junk(repo: _RescueRepo, context: SafeGitContext, head: str, changed: tuple[str, ...]) -> bool:
    """Restore classified disposable files using the same driver-owned context."""
    present = _rescue_git(context, "ls-tree", "-r", "-z", "--name-only", head, "--", *changed)
    if present.returncode:
        return False
    tracked = {path for path in present.stdout.split("\0") if path}
    for name in changed:
        path = repo.worktree / name
        if name in tracked:
            proc = _rescue_git(context, "restore", f"--source={head}", "--worktree", "--", name, work_tree=repo.worktree)
            if proc.returncode:
                return False
        elif path.is_file() or path.is_symlink():
            path.unlink()
        else:
            return False
    # The source index may still stage classified residue after its files
    # are restored/deleted. Reset only those paths through the fresh context.
    staged = _rescue_git(
        context, "--literal-pathspecs", "reset", head, "--", *changed,
        work_tree=repo.worktree, index=repo.admin_dir / "index",
    )
    if staged.returncode:
        return False
    return context.capture(repo.worktree, head, worker_index=repo.admin_dir / "index", exclude_file=repo.git_dir / "info/exclude") == context.checked("rev-parse", f"{head}^{{tree}}")


def _rescue_task(state_path: Path, *, apply: bool) -> dict[str, Any]:
    """:func:`_rescue_task_row` through the public-reason sink: a row's reason is a public cause only (#9878)."""
    return _public_row(_rescue_task_row(state_path, apply=apply), state_path, source="rescue")


def _rescue_task_row(state_path: Path, *, apply: bool) -> dict[str, Any]:
    """Preserve one terminal task on origin; never remove its worktree here.

    Rescue captures, checks, commits and pushes in a fresh bare Git context.
    The source contributes only resolved refs and objects; its checkout is
    retained, apart from classified disposable residue (#9878).
    """
    state = _read_state(state_path)
    task_id = state.get("task_id") if state else None
    row: dict[str, Any] = {"task_id": task_id, "action": "skipped"}
    if not state or state.get("status") not in _RESCUE_TERMINAL_STATUSES:
        row["reason"] = "task is not terminal non-success"
        return row
    raw_worktree = state.get("worktree_path")
    if not isinstance(raw_worktree, str):
        row["reason"] = "no recorded worktree"
        return row
    worktree = Path(raw_worktree).resolve()
    dispatch_root = (_REPO_ROOT / ".worktrees" / "dispatch").resolve()
    if not worktree.is_relative_to(dispatch_root):
        row["reason"] = "not a registered dispatch worktree"
        return row
    # A reaped or hand-removed worktree has nothing left to preserve. Before
    # #9878 the registration check skipped it; reading its git files now would
    # raise FileNotFoundError and fail every scheduled rescue run.
    if not worktree.is_dir():
        row["reason"] = "worktree already removed"
        return row
    if not (worktree / ".git").exists():
        row["reason"] = "not a registered dispatch worktree"
        return row
    if state.get("worktree_reused") is not False:
        row["reason"] = "worktree ownership unknown or reused"
        return row
    lease = state.get("lease")
    if (isinstance(lease, dict) and lease.get("state") == "active") or state.get("lease_state") == "active":
        row["reason"] = "task lease active"
        return row
    try:
        from scripts.orchestration import reap_worktrees

        with worktree_lock(worktree) if apply else contextlib.nullcontext():
            current = _read_state(state_path)
            if current != state:
                row["reason"] = "task state changed"
                return row
            if reap_worktrees._task_pid_alive(state):
                row["reason"] = "task process alive"
                return row
            try:
                active_ids = reap_worktrees._active_task_ids()
            except reap_worktrees._ActiveTaskProbeFailure as exc:
                diagnostic = _record_diagnostic(
                    task_id, _exception_cause("activity probe unavailable", exc), source="rescue", field="reason",
                )
                if diagnostic:
                    row["diagnostic"] = diagnostic
                active_ids = None
            live_cwds = reap_worktrees._live_cwd_paths(_REPO_ROOT)
            if active_ids is None or live_cwds is None:
                row["reason"] = "activity probe unavailable"
                return row
            if task_id in active_ids or any(cwd == worktree or cwd.is_relative_to(worktree) for cwd in live_cwds):
                row["reason"] = "worktree active"
                return row
            repo = _rescue_repo(worktree)
            with _rescue_execution_context(repo) as context:
                return _rescue_in_context(repo, context, state, state_path, row, apply=apply)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        cause = _TypedCause(exc.code) if isinstance(exc, SnapshotRefusal) else _exception_cause("rescue_step_failed", exc)
        reason = cause.public()
        row.update(action="error", reason=reason, failure_code=reason.split(", ")[0])
        diagnostic = _record_diagnostic(task_id, cause, source="rescue", field="reason")
        if diagnostic:
            row["diagnostic"] = diagnostic
        return row


def _rescue_in_context(
    repo: _RescueRepo, context: SafeGitContext, state: Mapping[str, Any],
    state_path: Path, row: dict[str, Any], *, apply: bool,
) -> dict[str, Any]:
    from scripts.agent_runtime import kimi_boundary

    worktree = repo.worktree
    task_id = state["task_id"]
    worker_head = _rescue_head(repo, context)
    if worker_head is None:
        row["reason"] = "HEAD unavailable"
        return row
    head, current_branch = worker_head
    recorded_branch = state.get("worktree_branch")
    agent = str(state.get("agent") or "agent")
    branch = f"rescue/{agent}/{_x_agent_task_id(agent, str(task_id))}"
    if current_branch not in {recorded_branch, branch}:
        row["reason"] = "worktree branch differs from task record"
        return row
    tree = context.capture(worktree, head, worker_index=repo.admin_dir / "index", exclude_file=repo.git_dir / "info/exclude")
    changed = tuple(path for path in context.checked("diff-tree", "-r", "-z", "--name-only", head, tree).split("\0") if path)
    large = []
    for name in changed:
        try:
            info = (worktree / name).lstat()
        except FileNotFoundError:  # tracked deletion
            continue
        if stat.S_ISREG(info.st_mode) and info.st_size > _RESCUE_MAX_FILE_BYTES:
            large.append(name)
    if large:
        row.update(reason="files exceed 5 MB", large_files=large)
        return row
    cleaned_junk = False
    if _auto_finalize_is_junk_only(changed):
        if not apply:
            row.update(action="candidate", reason="clean disposable residue")
            return row
        if not _clean_rescue_junk(repo, context, head, changed):
            row.update(action="error", reason="could not clean disposable residue")
            return row
        cleaned_junk = True
        changed = ()
        tree = context.checked("rev-parse", f"{head}^{{tree}}")
    base = _rescue_base(repo, context, state)
    merge = _rescue_git(context, "merge-base", base, head)
    if merge.returncode:
        raise _RescueFailure("merge base unavailable", _git_cause("merge_base_unresolved", merge))
    merge_base = merge.stdout.strip()
    context.refuse_tree(merge_base, tree)
    rescued = state.get("rescue_head_commit") if state.get("rescue_status") == "rescued" else None
    if isinstance(rescued, str) and changed:
        _rescue_git(context, "fetch", "--no-tags", "origin", f"refs/heads/{branch}", network=True)
    if isinstance(rescued, str) and (rescued == head if not changed else _rescue_commit_matches(context, rescued, tree, head)):
        row["reason"] = "already rescued at HEAD"
        return row
    if not changed:
        count = _rescue_git(context, "rev-list", "--count", f"{base}..{head}")
        if count.returncode:
            row["reason"] = "ahead count unavailable"
            return row
        tracking = context.read_source_ref(repo.git_dir, f"refs/remotes/origin/{recorded_branch}")
        unpushed = _rescue_git(context, "rev-list", "--count", f"{tracking.stdout.strip()}..{head}") if tracking.returncode == 0 else None
        if count.stdout.strip() == "0" or (unpushed is not None and unpushed.returncode == 0 and unpushed.stdout.strip() == "0"):
            row.update(action="cleaned" if cleaned_junk else "skipped", reason="disposable residue removed" if cleaned_junk else "no provable unpushed work")
            return row
    if kimi_boundary.is_installed(worktree) or _is_kimi_task_record(state):
        refusal, unreadable = _kimi_tree_refusal(context, merge_base, agent, tree=tree)
        if refusal is not None:
            reason, cause = _kimi_refusal_cause(refusal, unreadable)
            row.update(action="error", reason=reason, failure_code="kimi_content_refused")
            diagnostic = _record_diagnostic(task_id, cause, source="rescue", field="reason")
            if diagnostic:
                row["diagnostic"] = diagnostic
            return row
    existing_remote = _rescue_remote_head(context, branch)
    commit = head if not changed else None
    if changed and existing_remote:
        # A previous process may have pushed before recording its success.
        fetched = _rescue_git(context, "fetch", "--no-tags", "origin", f"refs/heads/{branch}", network=True)
        if fetched.returncode == 0 and _rescue_commit_matches(context, existing_remote, tree, head):
            commit = existing_remote
    if existing_remote is not None and existing_remote != commit:
        row["reason"] = "rescue remote branch already exists at another head"
        return row
    row.update(action="candidate", rescue_ref=branch, head=commit or head)
    if not apply:
        return row
    if commit is None:
        commit = _rescue_commit(context, tree, head, agent=agent, task_id=str(task_id))
    context.verify_inputs()
    if _rescue_head(repo, context) != worker_head:
        raise SnapshotRefusal("rescue_input_changed")
    proc = _rescue_git(context, "push", "--no-verify", "origin", f"{commit}:refs/heads/{branch}", network=True)
    if proc.returncode:
        raise _RescueFailure("cannot push rescue branch", _remote_git_cause("rescue_push_failed", proc))
    if _rescue_remote_head(context, branch) != commit:
        raise _RescueFailure("rescue remote verification failed", _TypedCause("rescue_remote_unverified", "ls-remote"))
    with task_state_lock(state_path):
        current = _read_state(state_path)
        if not current or current.get("run_nonce") != state.get("run_nonce"):
            row.update(
                action="skipped",
                reason="task attempt changed after rescue push; recovery ref preserved",
                owner=task_id,
                next_condition="rescue the current attempt from its own task record",
                head=commit,
            )
            return row
        current.update({"rescue_ref": branch, "rescue_head_commit": commit, "rescue_status": "rescued"})
        _write_record_unlocked(state_path, current)
    row.update({"action": "rescued", "head": commit})
    return row


def cmd_rescue(args: argparse.Namespace) -> int:
    """Show or preserve terminal dispatch work before the P0 reaper runs."""
    if args.all_stale:
        try:
            amount = str(args.older_than).removesuffix("h")
            min_age_hours = float(amount)
            if min_age_hours < 0:
                raise ValueError
        except (TypeError, ValueError):
            print("--older-than must be a non-negative hour duration, such as 6h", file=sys.stderr)
            return 2
        paths = sorted(tasks_dir().glob("*.json")) if tasks_dir().is_dir() else []
    elif args.task_id:
        paths = [_state_path(args.task_id)]
        min_age_hours = 0
    else:
        print("provide a task ID or --all-stale", file=sys.stderr)
        return 2

    rows: list[dict[str, Any]] = []
    now = datetime.now(UTC)
    for path in paths:
        state = _read_state(path)
        if args.all_stale:
            if state is None:
                rows.append({"task_id": path.stem, "action": "skipped", "reason": "unreadable task state"})
                continue
            if state.get("status") not in _RESCUE_TERMINAL_STATUSES:
                continue
            try:
                finished = datetime.fromisoformat(str(state["finished_at"]).replace("Z", "+00:00"))
                age_hours = (now - finished).total_seconds() / 3600
            except (KeyError, TypeError, ValueError, OverflowError):
                rows.append(
                    {
                        "task_id": state.get("task_id"),
                        "action": "skipped",
                        "reason": "no finished_at" if not state.get("finished_at") else "invalid finished_at",
                    }
                )
                continue
            if age_hours < min_age_hours:
                continue
        rows.append(_rescue_task(path, apply=bool(args.apply or not args.all_stale)))
    # Every row leaves through the public-reason sink (#9878).
    rows = [_public_row(row, None, source="rescue") for row in rows]
    summary = {
        action: sum(row["action"] == action for row in rows)
        for action in ("candidate", "rescued", "cleaned", "skipped", "error")
    }
    print(
        json.dumps(
            {"mode": "apply" if args.apply or not args.all_stale else "dry_run", "summary": summary, "tasks": rows}
        )
    )
    return 1 if summary["error"] else 0


def _branch_ref_exists(repo_root: Path, branch: str) -> bool:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0


def _should_reap_settled_worktree(
    *,
    mode: str,
    keep_worktree: bool,
    final_status: str,
    returncode: int | None,
    dirty_on_exit: bool | None,
) -> bool:
    """Return whether settle may remove this dispatch checkout.

    ``ask-* --review`` reaches this path through ``delegate.py dispatch
    --mode read-only --worktree``. The sealed snapshot helper tears its own
    temp root down and is not a second worktree owner.

    Dirty or unknown trees stay mounted. ``--keep-worktree`` stays mounted.
    Read-only reaps on any terminal status. ``workspace-write`` uses the same
    rule as ``danger``: status ``done`` and return code 0.
    """
    if keep_worktree or dirty_on_exit is not False:
        return False
    if mode == "read-only":
        return final_status in _READ_ONLY_SETTLE_REAP_STATUSES
    if mode in _WRITE_CAPABLE_MODES:
        return final_status == "done" and returncode == 0
    return False


def _settled_worktree_ownership(worktree: Path, *, created_by_this_dispatch: bool | None) -> tuple[bool, str]:
    """Return settle's ``(ok, reason)`` ownership proof for removing ``worktree``.

    Settle removes only a checkout this dispatch created. An attached or
    reused checkout belongs to another task, and that owner reaps it (#8610).
    Ownership that cannot be established fails closed; the default reaper
    does not collect that legacy case, so the refusal names the explicit
    operator cleanup.
    """
    if created_by_this_dispatch is None:
        return False, (
            "worktree ownership unknown; refusing worktree removal; operator cleanup: "
            "scripts/orchestration/reap_worktrees.py --terminal-dispatches "
            f"--worktree {worktree} --apply"
        )
    if not created_by_this_dispatch:
        return False, "reused worktree; owner reaps"
    return True, ""


# The claim scan's byte pre-filter; see scripts/orchestration/worktree_claims.py.
_worktree_claim_needles = worktree_claims.worktree_claim_needles
_record_may_claim_worktree = worktree_claims.record_may_claim_worktree


def _remove_dispatch_worktree(
    worktree: Path,
    *,
    reason: str,
    owner_task_id: str | None,
    releasable: Callable[[], tuple[bool, str]],
    force: bool = False,
    lock_timeout_s: float | None = None,
    task_record: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Remove one dispatch worktree. Every removal in this module comes here (#8610).

    An adapter over
    :func:`scripts.orchestration.worktree_claims.remove_unclaimed_worktree`,
    the chokepoint every remover in the repository shares, bound to this
    repository's task records and lock home. Holding :func:`worktree_lock`,
    it runs ``releasable``, the caller's ownership proof returning
    ``(ok, detail)``; for ``force``, a clean-tree proof; the active-claim
    scan, which exempts only ``owner_task_id``'s own record; and only then
    the removal. ``reason`` is the caller's purpose, recorded on success.
    Returns a ``worktree_reap`` record whose ``action`` is ``removed``,
    ``skipped``, or ``error``; this never raises.
    """
    removal = worktree_claims.remove_unclaimed_worktree(
        worktree,
        # A ``--repo`` sibling worktree is git-operated in its own repository,
        # while its records and locks stay on this control plane (#8624).
        repo_root=worktree_claims.owning_repo_root(worktree, default=_REPO_ROOT),
        control_root=_REPO_ROOT,
        reason=reason,
        owner_task_id=owner_task_id,
        releasable=releasable,
        task_record=task_record,
        force=force,
        tasks_dir=tasks_dir(),
        lock_dir=_worktree_lock_dir(),
        lock_timeout_s=_WORKTREE_LOCK_DEFAULT_TIMEOUT_S if lock_timeout_s is None else lock_timeout_s,
    )
    record = {**removal.as_record(), "pr": None}
    return record


def _stop_worker_background_jobs(task_record: Mapping[str, Any], *, task_id: str) -> tuple[bool, str]:
    """Stop a worker's possibly live background jobs; ``(ok, refusal detail)``.

    The scope comes from the task record only when it matches the task's
    launch identity (:func:`worker_leftovers.scope_from_record`).
    """
    scope, refusal = worker_leftovers.scope_from_record(task_record, task_id=task_id)
    if refusal is not None:
        return (
            False,
            f"background jobs may be alive but the recorded scope is refused ({refusal}); refusing worktree removal",
        )
    if scope is None:
        return True, ""
    try:
        stopped = worker_leftovers.stop_leftovers(scope, reader=_worker_process_reader())
    except Exception as exc:
        return False, f"background jobs could not be stopped ({type(exc).__name__}: {exc}); refusing worktree removal"
    if stopped.ok:
        return True, ""
    survivors = ", ".join(str(proc.pid) for proc in stopped.survivors) or "unknown"
    return False, f"background jobs could not be stopped ({stopped.error}; pids {survivors}); refusing worktree removal"


def _settle_worktree_reap(
    worktree: Path,
    *,
    created_by_this_dispatch: bool | None,
    settling_task_id: str,
    lock_timeout_s: float | None = None,
    task_record: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Remove a settled checkout this dispatch created and keep its branch ref.

    The scheduled reaper's PR, rollover, and GraphQL gates skip the clean
    read-only review checkouts this path exists to drop. Removal goes through
    :func:`_remove_dispatch_worktree` with settle's ownership proof and is
    worktree-only: ``git branch`` is never invoked, and a missing branch ref
    after removal is an error. ``task_record`` is the settling task's record:
    when its exit scan says jobs may be alive, once ownership is proven those
    processes are stopped inside the worker's own scope before removal, and
    removal is refused if any survive or the scope is refused (#8991). This
    never raises.
    """

    def releasable() -> tuple[bool, str]:
        ok, detail = _settled_worktree_ownership(worktree, created_by_this_dispatch=created_by_this_dispatch)
        if not ok or task_record is None:
            return ok, detail
        if task_record.get("mode") == "read-only":
            from scripts.orchestration.reap_worktrees import _is_head_reachable_from_remote

            current = _read_state(_state_path(settling_task_id))
            if current is None or (current.get("run_nonce"), current.get("pid")) != (
                task_record.get("run_nonce"),
                task_record.get("pid"),
            ):
                return False, (
                    f"read-only settle attempt changed; retained for owner {settling_task_id}; "
                    "next condition: settle the current attempt"
                )
            head = _resolve_sha(worktree)
            if head is None or (
                head != _recorded_base_sha(task_record) and not _is_head_reachable_from_remote(worktree, head)
            ):
                return False, (
                    f"read-only HEAD moved or unknown; retained for owner {settling_task_id}; "
                    "next condition: HEAD equals recorded base or is reachable from a remote ref"
                )
        stopped, refusal = _stop_worker_background_jobs(task_record, task_id=settling_task_id)
        return (True, detail) if stopped else (False, refusal)

    # Resolved before removal: the checkout's ``.git`` pointer is gone after it.
    owning_repo = worktree_claims.owning_repo_root(worktree, default=_REPO_ROOT)
    removal = _remove_dispatch_worktree(
        worktree,
        reason="settled clean worktree; branch ref kept",
        owner_task_id=settling_task_id,
        releasable=releasable,
        force=True,
        lock_timeout_s=lock_timeout_s,
        task_record=task_record,
    )
    branch = removal["branch"]
    if removal["action"] == "removed" and branch is not None and not _branch_ref_exists(owning_repo, branch):
        return {
            **removal,
            "action": "error",
            "reason": "branch ref missing after worktree removal",
            "error": f"refs/heads/{branch} was deleted",
        }
    return removal


def _validate_existing_worktree(
    *,
    path: Path,
    expected_branch: str,
    base: str,
    allow_rebase: bool = True,
    onto: str | None = None,
) -> bool:
    """Validate a reused worktree. Returns True if a rebase occurred.

    Raises :class:`WorktreeBranchMismatch`, :class:`WorktreeDirty`, or
    :class:`WorktreeStaleBase` on the respective failure mode. The
    checks skip silently when the path isn't a real git worktree (e.g.
    a tmp_path fixture) — those cases either fail at the first real git
    operation later or were never on the dispatch path to begin with.
    ``onto``, when given, is the commit of ``origin/{base}`` admission
    checked (#9739 A7): staleness and the rebase use it as is, never the
    ref fetched again.
    """
    # 1. Branch check.
    try:
        branch_proc = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=path,
            capture_output=True,
            text=True,
            check=False,
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if branch_proc.returncode != 0:
        # Not a git worktree (e.g. test tmp dir). Don't treat as an error —
        # the caller may be a test fixture, and real dispatch paths will
        # surface the issue on the next git op.
        return False
    actual_branch = (branch_proc.stdout or "").strip()
    if actual_branch and actual_branch != expected_branch:
        raise WorktreeBranchMismatch(
            f"worktree at {path} is on branch {actual_branch!r}, expected "
            f"{expected_branch!r}. Remove it and retry:\n"
            f"    git worktree remove {path}"
        )

    # 2. Dirty check.
    try:
        status_proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=path,
            capture_output=True,
            text=True,
            check=False,
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"git status timed out after {DEFAULT_GIT_TIMEOUT_S}s checking {path}") from exc
    dirty_output = (status_proc.stdout or "").strip()
    if dirty_output:
        first_files = [line[3:] for line in dirty_output.splitlines()[:3]]
        raise WorktreeDirty(
            f"worktree at {path} has uncommitted changes "
            f"(first {len(first_files)}): {first_files}. "
            f"Commit, stash, or remove the worktree before reuse."
        )

    # 3. Stale-base check. Refresh origin/{base} first. Single-remote hosts
    # keep the lenient bool contract — an offline fetch falls back to
    # whatever ref is locally available below. Two-remote hosts fail
    # closed inside _fetch_base when the canonical GitHub remote is
    # unreachable: a lagging mirror must never pin the base (#7522).
    # Normalize so an origin-prefixed ``base`` (the form the dispatch
    # runbooks mandate) never yields ``origin/origin/main`` — that
    # unresolvable ref made this whole check a silent no-op.
    origin_ref = _origin_base_ref(base)
    target = onto or origin_ref
    if onto is None:
        _fetch_base(base)
    shown = f"{origin_ref} at {onto[:12]}" if onto else origin_ref
    try:
        count_proc = subprocess.run(
            ["git", "rev-list", "--count", f"HEAD..{target}"],
            cwd=path,
            capture_output=True,
            text=True,
            check=False,
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if count_proc.returncode != 0:
        # origin/{base} unresolvable (offline / no remote). Nothing to do.
        return False
    try:
        behind = int((count_proc.stdout or "0").strip())
    except ValueError:
        behind = 0
    if behind == 0:
        return False

    if not allow_rebase:
        raise WorktreeStaleBase(
            f"worktree at {path} is {behind} commit(s) behind {shown}; "
            "automatic rebasing is disabled. Synchronize it explicitly (for "
            "example, `git merge --ff-only "
            f"{target}`) before attaching a worker."
        )

    print(
        f"⚠️  worktree {path} is {behind} commit(s) behind {shown}; attempting fast-forward rebase",
        file=sys.stderr,
    )
    try:
        rebase_proc = subprocess.run(
            ["git", "rebase", target],
            cwd=path,
            capture_output=True,
            text=True,
            check=False,
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        with contextlib.suppress(OSError, subprocess.TimeoutExpired):
            subprocess.run(
                ["git", "rebase", "--abort"],
                cwd=path,
                capture_output=True,
                text=True,
                check=False,
                timeout=DEFAULT_GIT_TIMEOUT_S,
            )
        raise WorktreeStaleBase(
            f"worktree at {path} is {behind} commit(s) behind {shown} "
            f"and rebase timed out after {DEFAULT_GIT_TIMEOUT_S}s."
        ) from exc
    if rebase_proc.returncode != 0:
        # Clean up so the worktree isn't left mid-rebase.
        with contextlib.suppress(OSError, subprocess.TimeoutExpired):
            subprocess.run(
                ["git", "rebase", "--abort"],
                cwd=path,
                capture_output=True,
                text=True,
                check=False,
                timeout=DEFAULT_GIT_TIMEOUT_S,
            )
        raise WorktreeStaleBase(
            f"worktree at {path} is {behind} commit(s) behind {shown} "
            f"and rebase failed. Resolve manually or remove:\n"
            f"    git worktree remove {path}"
        )
    return True


def _withdraw_primary_database_links(
    worktree_path: Path, main_repo_root: Path, relative_paths: Sequence[str]
) -> None:
    """Remove a reused worktree's database links that resolve to the primary databases (#9421).

    A read-only dispatch must carry no such link: a symlink cannot be made
    read-only, so a write through it lands in the primary database. Links to
    anything else stay. Never touches the main checkout itself, whose own
    database entries are the primary.

    The parent containment is checked for every database path, whatever the
    entry type. An aliased parent (for example a worktree ``data`` directory
    that points into the primary checkout) makes a relative write reach the
    primary database even when the entry is an ordinary file or absent, so
    such a dispatch fails closed instead of only when the entry is a link.
    """
    if worktree_path.resolve() == main_repo_root.resolve():
        return
    worktree = worktree_path.resolve()
    for relative_path in relative_paths:
        target = worktree_path / relative_path
        if not target.parent.resolve().is_relative_to(worktree):
            raise RuntimeError(
                f"refusing read-only dispatch: database path {target} has a parent that resolves outside the worktree"
            )
        # Non-strict resolution also matches a dangling link, whose write
        # would create the primary database.
        if target.is_symlink() and target.resolve() == (main_repo_root / relative_path).resolve():
            # The primary checkout contains worktrees, so containment in this
            # worktree (not absence from the primary) is the boundary.
            target.unlink()
            print(f"ℹ️  withdrew database link {target} for a read-only dispatch", file=sys.stderr)


def _provision_data_symlinks(worktree_path: Path, main_repo_root: Path, *, read_only: bool = False) -> None:
    """Symlink heavy local-only files into a delegated worktree.

    Worktrees omit gitignored DBs and Node dependency directories, but quality
    gates open them relative to the running checkout. Use symlinks so each
    delegated worktree sees the same local files without copying multi-GB
    directories. The primary Python environment is deliberately excluded:
    workers invoke its absolute interpreter and must not receive a local
    ``.venv`` symlink.

    A read-only dispatch gets no database link (#9421). A symlink cannot be
    made read-only, so a write through it lands in the primary database.
    ``read_only`` withdraws a database link an earlier write-capable dispatch
    provisioned into a reused worktree; a link to anything else is left alone.
    A relative open then creates a worktree-local file that the read-only
    guard flags, and the primary stays untouched. Workers read the primary
    databases by absolute path with ``mode=ro`` or through the ``sources`` MCP.

    Self-link guard: if ``worktree_path`` *is* the main checkout, provisioning
    would create ``node_modules -> node_modules`` (a self-referential loop) that
    makes every later ``npm`` invocation die with ``spawn ELOOP``. Refuse. The
    per-link guards below also skip a ``source`` that already loops, so a bad
    root link is never propagated into worktrees. See the autopsy
    ``docs/bug-autopsies/node-modules-eloop-symlink.md``.
    """
    if worktree_path.resolve() == main_repo_root.resolve():
        print(
            "⚠️  refusing to provision symlinks into the main checkout "
            f"({worktree_path}) — would create self-referential loops",
            file=sys.stderr,
        )
        return

    database_links = ("data/vesum.db", "data/sources.db")
    if read_only:
        _withdraw_primary_database_links(worktree_path, main_repo_root, database_links)
    for relative_path in (
        *(() if read_only else database_links),
        "node_modules",
        "site/node_modules",
    ):
        source = main_repo_root / relative_path
        target = worktree_path / relative_path
        # ``source.exists()`` follows symlinks and returns False for a looping
        # source, so a self-referential root ``node_modules`` is skipped here
        # rather than copied into the worktree.
        if not source.exists():
            print(
                f"⚠️  skipping worktree link for missing/looping {source}",
                file=sys.stderr,
            )
            continue

        if target.exists() or target.is_symlink():
            continue

        resolved_source = source.resolve()
        if resolved_source == target.resolve():
            print(
                f"⚠️  skipping worktree link {target} — would be self-referential",
                file=sys.stderr,
            )
            continue

        if target.parent.exists() and not target.parent.is_dir():
            print(
                f"⚠️  skipping worktree link because {target.parent} is not a directory",
                file=sys.stderr,
            )
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(resolved_source)


# Default cone sparse-checkout exclusions for dispatch worktrees.
# Measured 2026-09-23 on a full working tree (du -sh, .git excluded): 1.6GB,
# of which curriculum/ is 289MB, wiki/ 66MB, data/projects/ 633MB, and
# data/lexicon/ 277MB. The migrated open-model registry payload tree is also
# excluded independently from registry/ so registry/lexicon remains available.
# Dropping these trees leaves a default dispatch under
# 450MB (re-measured 2026-09-25: 287MB). Opt back in with --sparse-include
# or --full-checkout. wiki/ is still a top-level tree
# (`git ls-tree -d HEAD wiki`), so it stays excluded.
#
# curriculum/ stays in the exclusion set, with one cone anchor so
# ``pytest -m repo_wide`` can read the manifest. Measured 2026-09-25 in a
# default sparse worktree (no curriculum/): that command failed 15 tests,
# and each one read only ``curriculum/l2-uk-en/curriculum.yaml``
# (FileNotFoundError, or ORCH_TRACK_NOT_ACTIVE because a missing manifest
# yields no active levels). Cone mode also checks out files that sit
# directly in every ancestor of an included directory. The anchor is
# ``curriculum/l2-uk-en/lesson-plans`` (192K), not a smaller sibling:
# once ``curriculum/`` exists, collection of
# tests/curriculum/test_plan_validate_cross.py loads
# ``lesson-plans/a1/_arc.yaml`` (tree_absent is false). An evidence-only
# anchor (3.4M, yaml present, arc absent) died at collection with exit 2.
# Including lesson-plans materialises the arc, curriculum.yaml, and the
# other loose files beside the manifest (vocabulary.db,
# module-mapping.json, callout-claims-review.md). ``du -sh`` of that
# tree: 3.6M, not 289M. The anchor is added only when that directory
# exists at HEAD.
_DISPATCH_SPARSE_EXCLUDE_DEFAULT = frozenset(
    {
        "curriculum",
        "wiki",
        "data/projects",
        "data/lexicon",
        "registry/projects",
    }
)
_DISPATCH_SPARSE_CURRICULUM_MANIFEST_CONE = "curriculum/l2-uk-en/lesson-plans"
# Owned-path prefixes that re-include a default-excluded tree even when the
# path itself is not under that tree (tests and scripts that read it).
# Filename stems end with "_" and match tests/test_open_model_*.py. Exact
# files are listed only when grep shows that file reads the tree. ``site/``
# consumes site/src/data/lexicon-*.json, not raw data/lexicon/.
# ``tests/test_open_model_`` is content-gated: most of those modules never
# read data/projects, and a blanket stem would check out ~633MB.
_SPARSE_OWNED_PATH_REINCLUDE: dict[str, tuple[str, ...]] = {
    "data/projects": (
        "data/projects",
        "tests/projects/open_model_data",
        "scripts/projects/open_model_data",
        "tests/test_open_model_",
    ),
    "data/lexicon": (
        "data/lexicon",
        "scripts/lexicon",
        "tests/lexicon",
        "tests/test_source_inventory_",
        "scripts/audit/source_inventory_review_decisions.py",
        "scripts/audit/generate_source_inventory_review_candidates.py",
        "scripts/practice/author_densified_pairs.py",
        "scripts/practice/creation_review.py",
        "scripts/practice/thin_mode_source_inventory.py",
    ),
}
# Stem prefixes whose match still has to mention the tree in that file.
_SPARSE_REINCLUDE_CONTENT_MARKERS: dict[str, tuple[str, ...]] = {
    "tests/test_open_model_": ("data/projects",),
}


def _sparse_path_has_prefix(path: str, prefix: str) -> bool:
    prefix = prefix.strip("/")
    return path == prefix or path.startswith(prefix + "/")


def _sparse_reinclude_prefix_matches(path: str, prefix: str) -> bool:
    """Match a directory prefix, an exact file, or a filename stem.

    Stems end with ``_`` so ``tests/test_open_model_`` matches
    ``tests/test_open_model_foundry_cli.py`` without also matching a
    sibling directory.
    """
    if _sparse_path_has_prefix(path, prefix):
        return True
    return prefix.endswith("_") and path.startswith(prefix)


def _assignment_mentions_marker(module_path: Path, name: str, markers: tuple[str, ...]) -> bool:
    """True when ``name = ...`` in ``module_path`` embeds a marker string."""
    try:
        source = module_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError, UnicodeError):
        return False
    for stmt in tree.body:
        targets: list[ast.expr] = []
        value: ast.expr | None = None
        if isinstance(stmt, ast.Assign):
            targets = list(stmt.targets)
            value = stmt.value
        elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
            targets = [stmt.target]
            value = stmt.value
        if value is None:
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in targets):
            rendered = ast.unparse(value)
            if any(marker in rendered for marker in markers):
                return True
    return False


def _imported_binding_mentions_marker(text: str, markers: tuple[str, ...]) -> bool:
    """True when the file uses an imported name whose value embeds a marker.

    Content-gated sparse stems used to require the literal ``data/projects``
    in the owned file. Readers that reach the tree through an imported path
    constant (``foundry.DEFAULT_V011_MANIFEST``) still need that tree.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False
    imported: dict[str, tuple[str, str]] = {}
    for stmt in tree.body:
        if isinstance(stmt, ast.ImportFrom) and stmt.module and stmt.level == 0:
            for alias in stmt.names:
                if alias.name == "*":
                    continue
                imported[alias.asname or alias.name] = (stmt.module, alias.name)
    needed: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and isinstance(node.ctx, ast.Load):
            binding = imported.get(node.value.id)
            if binding is None:
                continue
            module, imported_name = binding
            needed.add((f"{module}.{imported_name}", node.attr))
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            binding = imported.get(node.id)
            if binding is not None:
                needed.add(binding)
    for dotted, attr in needed:
        module_path = _REPO_ROOT / Path(*dotted.split(".")).with_suffix(".py")
        if module_path.is_file() and _assignment_mentions_marker(module_path, attr, markers):
            return True
    return False


def _reinclude_file_confirms(path: str, prefix: str) -> bool:
    """Content-gated stems must read the tree, directly or via an import."""
    markers = _SPARSE_REINCLUDE_CONTENT_MARKERS.get(prefix)
    if not markers:
        return True
    file_path = _REPO_ROOT / path
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError:
        return False
    if any(marker in text for marker in markers):
        return True
    return _imported_binding_mentions_marker(text, markers)


def _normalize_sparse_include(raw: Sequence[str] | None) -> tuple[str, ...]:
    """Normalize --sparse-include values to unique default-excluded trees.

    Fail closed: explicit values must be names in the default exclusion set
    (``curriculum``, ``wiki``, ``data/projects``, ``data/lexicon``,
    ``registry/projects``). Other nested paths and unknown names raise
    :class:`ValueError`.
    """
    if not raw:
        return ()
    seen: set[str] = set()
    ordered: list[str] = []
    allowed = ", ".join(sorted(_DISPATCH_SPARSE_EXCLUDE_DEFAULT))
    for item in raw:
        name = str(item).strip().strip("/")
        if not name or name in {".", ".."} or name.startswith("../") or "/../" in f"/{name}/":
            raise ValueError(
                f"--sparse-include {item!r} is empty or invalid; "
                "pass a default-excluded tree such as 'curriculum', 'wiki', 'data/projects', "
                "or 'registry/projects'"
            )
        if name not in _DISPATCH_SPARSE_EXCLUDE_DEFAULT:
            if "/" in name:
                raise ValueError(
                    f"--sparse-include {item!r} must name a default-excluded tree "
                    "(nested exclusions: data/projects, data/lexicon, registry/projects). "
                    f"Allowed: {allowed}"
                )
            raise ValueError(f"--sparse-include {name!r} is not a default-excluded tree; allowed: {allowed}")
        if name in seen:
            continue
        seen.add(name)
        ordered.append(name)
    return tuple(ordered)


def _infer_sparse_include_from_text(text: str | None) -> tuple[str, ...]:
    """Detect default-excluded path prefixes referenced in a prompt."""
    if not text:
        return ()
    found: list[str] = []
    for name in sorted(_DISPATCH_SPARSE_EXCLUDE_DEFAULT, key=len, reverse=True):
        # Path-like reference: curriculum/…, data/projects/… — not bare words.
        if re.search(rf"(?<![\w.-]){re.escape(name)}/", text):
            found.append(name)
    return tuple(found)


def _sparse_tree_for_owned_path(raw: str) -> str | None:
    """Return the excluded tree a research-owned path requires, if any."""
    path = str(raw).strip().strip("/")
    if not path:
        return None
    for name in sorted(_DISPATCH_SPARSE_EXCLUDE_DEFAULT, key=len, reverse=True):
        if _sparse_path_has_prefix(path, name):
            return name
    for tree, prefixes in _SPARSE_OWNED_PATH_REINCLUDE.items():
        if any(
            _sparse_reinclude_prefix_matches(path, prefix) and _reinclude_file_confirms(path, prefix)
            for prefix in prefixes
        ):
            return tree
    return None


def _infer_sparse_include(
    explicit: Sequence[str] | None,
    *,
    owned_paths: Sequence[str] | None = None,
    prompt_text: str | None = None,
) -> tuple[str, ...]:
    """Merge explicit includes with owned-path prefixes and prompt path references.

    A dispatch that already declares ``--research-owned-path curriculum/...``,
    ``scripts/projects/open_model_data/...``, or a lexicon reader such as
    ``scripts/lexicon/...`` materializes the matching excluded tree without a
    second flag. ``site/...`` does not: the frontend reads runtime JSON under
    ``site/src/data/``, not raw ``data/lexicon/``.
    """
    merged: list[str] = list(_normalize_sparse_include(explicit))
    seen = set(merged)
    for raw in owned_paths or ():
        name = _sparse_tree_for_owned_path(str(raw))
        if name and name not in seen:
            seen.add(name)
            merged.append(name)
    for name in _infer_sparse_include_from_text(prompt_text):
        if name not in seen:
            seen.add(name)
            merged.append(name)
    return tuple(merged)


def _list_worktree_dirs(worktree_path: Path, *tree_path: str, at_ref: str = "HEAD") -> list[str]:
    """Return directory names from ``git ls-tree -d`` at ``at_ref``.

    With no ``tree_path``, lists top-level directories. ``data/`` lists the
    children (``data/projects``, …) so new ``data/*`` dirs are included
    automatically and only the named exclusions drop out.
    """
    label = "/".join(tree_path) if tree_path else "top-level"
    try:
        proc = subprocess.run(
            ["git", "ls-tree", "-d", "--name-only", at_ref, *tree_path],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"could not list {label} dirs in {worktree_path}: timed out after {DEFAULT_GIT_TIMEOUT_S}s"
        ) from exc
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "git ls-tree failed").strip()
        raise RuntimeError(f"could not list {label} dirs in {worktree_path}: {detail}")
    return [line.strip() for line in (proc.stdout or "").splitlines() if line.strip()]


def _list_worktree_top_dirs(worktree_path: Path, *, at_ref: str = "HEAD") -> list[str]:
    """Return top-level directory names at ``at_ref`` inside a worktree."""
    return _list_worktree_dirs(worktree_path, at_ref=at_ref)


def _dispatch_sparse_cone_dirs(
    top_dirs: Sequence[str],
    data_children: Sequence[str],
    exclude: Collection[str],
    registry_children: Sequence[str] = (),
) -> tuple[list[str], list[str]]:
    """Build a cone include list that drops excluded dirs at directory level.

    Nested exclusions (``data/projects``, ``data/lexicon``, and
    ``registry/projects``) are expressed by listing the sibling directories
    instead of their parent. Cone mode then keeps files directly in each
    parent and preserves the other sibling trees.
    """
    exclude_set = set(exclude)
    nested_children = {"data": data_children, "registry": registry_children}
    cone: list[str] = []
    excluded: list[str] = []
    for name in top_dirs:
        if name not in nested_children:
            if name in exclude_set:
                excluded.append(name)
            else:
                cone.append(name)
            continue
        if name in exclude_set:
            excluded.append(name)
            continue
        children = list(nested_children[name])
        dropped = [child for child in children if child in exclude_set]
        if not dropped:
            cone.append(name)
            continue
        for child in children:
            if child in exclude_set:
                excluded.append(child)
            else:
                cone.append(child)
    return cone, sorted(excluded)


def _apply_dispatch_sparse_checkout(
    worktree_path: Path,
    *,
    full_checkout: bool = False,
    sparse_include: Sequence[str] = (),
) -> dict[str, Any]:
    """Apply (or disable) cone sparse-checkout on a dispatch worktree.

    Default profile excludes ``curriculum/``, ``wiki/``, ``data/projects/``
    (~633MB), ``data/lexicon/`` (~277MB), and ``registry/projects/``. The
    latter is excluded as a nested tree so ``registry/lexicon/`` stays
    available. When ``curriculum`` stays
    excluded and ``curriculum/l2-uk-en/lesson-plans`` exists at HEAD, that
    directory is still cone-included so ``curriculum/l2-uk-en/curriculum.yaml``
    and ``lesson-plans/a1/_arc.yaml`` are present (~3.6MB) without the rest
    of ``curriculum/``.
    ``--full-checkout`` disables sparse mode. ``--sparse-include`` keeps a
    named excluded tree.
    """
    includes = _normalize_sparse_include(sparse_include)
    telemetry: dict[str, Any] = {
        "full_checkout": bool(full_checkout),
        "sparse_include": list(includes),
        "excluded": [],
        "included_dirs": [],
        "applied": False,
        "error": None,
    }

    def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
        # Must sanitize GIT_* so sparse-checkout applies to *this* worktree
        # when a parent harness injects GIT_DIR/GIT_WORK_TREE (pre-commit, etc.).
        try:
            return subprocess.run(
                args,
                cwd=worktree_path,
                capture_output=True,
                text=True,
                check=False,
                env=_sanitized_git_env(),
                timeout=DEFAULT_GIT_TIMEOUT_S,
            )
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(
                args=args,
                returncode=124,
                stdout="",
                stderr=f"sparse-checkout command timed out after {DEFAULT_GIT_TIMEOUT_S}s",
            )

    if full_checkout:
        proc = _run_git(["git", "sparse-checkout", "disable"])
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "sparse-checkout disable failed").strip()
            telemetry["error"] = detail
            raise RuntimeError(f"failed to disable sparse-checkout in {worktree_path}: {detail}")
        telemetry["applied"] = True
        return telemetry

    exclude = set(_DISPATCH_SPARSE_EXCLUDE_DEFAULT) - set(includes)
    all_dirs = _list_worktree_top_dirs(worktree_path)
    data_children = _list_worktree_dirs(worktree_path, "data/") if "data" in all_dirs else []
    registry_children = _list_worktree_dirs(worktree_path, "registry/") if "registry" in all_dirs else []
    included, excluded = _dispatch_sparse_cone_dirs(all_dirs, data_children, exclude, registry_children)
    manifest_cone = _DISPATCH_SPARSE_CURRICULUM_MANIFEST_CONE
    if "curriculum" in excluded and manifest_cone in _list_worktree_dirs(worktree_path, manifest_cone):
        included.append(manifest_cone)
    telemetry["excluded"] = excluded
    telemetry["included_dirs"] = included

    if not excluded:
        # Nothing to drop at this ref (or everything was re-included). Prefer a
        # full tree rather than an empty cone set.
        proc = _run_git(["git", "sparse-checkout", "disable"])
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "sparse-checkout disable failed").strip()
            telemetry["error"] = detail
            raise RuntimeError(f"failed to disable sparse-checkout in {worktree_path}: {detail}")
        telemetry["applied"] = True
        return telemetry

    proc = _run_git(["git", "sparse-checkout", "init", "--cone"])
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "sparse-checkout init failed").strip()
        telemetry["error"] = detail
        raise RuntimeError(f"failed to init sparse-checkout in {worktree_path}: {detail}")

    set_args = ["git", "sparse-checkout", "set", "--cone"]
    if included:
        set_args.extend(["--", *included])
    proc = _run_git(set_args)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "sparse-checkout set failed").strip()
        telemetry["error"] = detail
        raise RuntimeError(
            f"failed to set sparse-checkout in {worktree_path}: {detail}. "
            "Commit/stash local changes under excluded paths, or pass "
            "--full-checkout / --sparse-include."
        )

    telemetry["applied"] = True
    print(
        f"🌲 dispatch sparse-checkout: excluded {', '.join(excluded)} "
        f"in {worktree_path} "
        "(git sparse-checkout add <dir>, or --sparse-include / --full-checkout)",
        file=sys.stderr,
    )
    return telemetry


def _inspect_worktree_local_venv(worktree_path: Path) -> dict[str, str | bool | None]:
    """Describe a prohibited worktree-local environment without modifying it.

    Dispatch worktrees share the primary checkout's project interpreter. Git
    does not copy ignored files into a new worktree, but an adapter or worker
    can still create a local ``.venv`` after creation. Record an early warning
    in dispatch state instead of deleting a possibly active environment; the
    P0 reaper remains the sole automatic deletion hand after merge.
    """
    candidate = worktree_path / ".venv"
    try:
        candidate.lstat()
    except FileNotFoundError:
        return {"present": False, "kind": None, "path": None}
    except OSError as exc:
        return {
            "present": False,
            "kind": "unreadable",
            "path": str(candidate),
            "error": type(exc).__name__,
        }

    if candidate.is_symlink():
        kind = "symlink"
    elif candidate.is_dir():
        kind = "directory"
    else:
        kind = "file"
    return {"present": True, "kind": kind, "path": str(candidate)}


def _record_worktree_local_venv_warning(
    worktree_path: Path,
    telemetry: dict[str, Any],
) -> None:
    """Attach local-venv state to telemetry and warn when it is present."""
    local_venv = _inspect_worktree_local_venv(worktree_path)
    telemetry["local_venv"] = local_venv
    if local_venv.get("present"):
        print(
            "⚠️  dispatch worktree contains a local .venv; do not use, copy, or "
            f"replace it. Use the primary interpreter {project_interpreter()} "
            f"instead: {worktree_path / '.venv'} ({local_venv.get('kind')}).",
            file=sys.stderr,
        )


def _refuse_if_gate_head_moved(origin_sha: str, pinned_head_sha: str | None) -> None:
    """Refuse when a fetched or reused head differs from the required pinned SHA."""
    if pinned_head_sha is not None and origin_sha != pinned_head_sha:
        raise RuntimeError(
            f"refusing dispatch: fetched branch head {origin_sha} differs from the pinned head SHA {pinned_head_sha}"
        )


def _resolve_worktree_base_sha(
    *,
    agent: str,
    task_id: str,
    raw_path: str | None = None,
    base: str,
    branch: str | None,
    allow_rebase: bool = True,
    rebase_onto: str | None = None,
    pinned_head_sha: str | None = None,
    detached: bool = False,
    validated_path: Path | None = None,
    review_dependencies: Sequence[tuple[str, Path]] = (),
    continuation_head_sha: str | None = None,
    continuation_remote_sha: str | None = None,
) -> str:
    """Resolve one immutable base SHA before worktree creation.

    A dispatch receipt and its worker must bind the same checkout state. This
    helper performs moving-ref validation first, then returns the SHA passed to
    :func:`_ensure_worktree`. The latter must not fetch, rebase, or dereference
    a branch again when the SHA is supplied. ``validated_path``, when given, is
    used as is and never resolved again (#8775, :func:`_helper_worktree_path`).
    ``rebase_onto`` pins a reused worktree's auto-rebase to the commit
    authoring-review admission checked (#9739 A7).
    """
    worktree_path = _helper_worktree_path(raw_path, validated_path)
    requested_branch = _validate_branch_reuse_name(branch) if branch else None
    if detached and worktree_path.exists():
        raise ValueError(f"detached read-only worktree already exists: {worktree_path}; refuse reuse")

    if worktree_path.exists():
        if not worktree_path.is_dir():
            raise ValueError(f"worktree path exists but is not a directory: {worktree_path}")
        _validate_existing_worktree(
            path=worktree_path,
            expected_branch=requested_branch or _derive_worktree_branch(agent, task_id),
            base=requested_branch or base,
            # Receipt-bound dispatches must leave a reused worktree untouched
            # until admission succeeds. Ordinary follow-ups retain the
            # established auto-rebase behavior.
            # An explicit branch is an attach request, not permission to
            # rewrite the PR's history. In particular, rebasing an attached
            # branch can flatten or replay merge commits. A stale attachment
            # must be synchronized deliberately by its owner.
            # Review admission already read these dependencies. A stale target
            # must refuse rather than advance to different admitted bytes.
            allow_rebase=allow_rebase and requested_branch is None and not review_dependencies,
            onto=rebase_onto,
        )
        if requested_branch:
            # Existing paths used to return before this check, allowing local
            # commits not present on the PR branch to slip into a new worker.
            # Validate only after the dirty check above, so a dirty checkout
            # always receives the most actionable refusal.
            _fetch_existing_branch(requested_branch)
            _refuse_if_gate_head_moved(
                _require_local_branch_is_ancestor_of_origin(
                    requested_branch,
                    continuation_head_sha=continuation_head_sha,
                    continuation_remote_sha=continuation_remote_sha,
                ),
                pinned_head_sha,
            )
        resolved = _resolve_sha(worktree_path)
        if resolved is None:
            raise RuntimeError(f"could not resolve HEAD for existing worktree {worktree_path}")
        _refuse_if_gate_head_moved(resolved, pinned_head_sha)
        return resolved

    if requested_branch:
        _fetch_existing_branch(requested_branch)
        origin_sha = _require_local_branch_is_ancestor_of_origin(requested_branch)
        _refuse_if_gate_head_moved(origin_sha, pinned_head_sha)
        return pinned_head_sha or origin_sha

    origin_ref = _origin_base_ref(base)
    if _fetch_base(base):
        resolved = _resolve_sha(_REPO_ROOT, origin_ref)
        if resolved is not None:
            return resolved

    branch_name = _base_branch_name(base)
    raise RuntimeError(
        f"could not fetch origin/{branch_name} and {origin_ref} is "
        f"unresolvable — refusing to branch from possibly-stale local "
        f"{branch_name}. Check connectivity and that "
        "`git remote get-url origin` points at the canonical remote "
        "(github.com:learn-ukrainian/learn-ukrainian.github.io), then "
        f"run `git fetch origin +refs/heads/{branch_name}:refs/remotes/origin/{branch_name}` and retry the dispatch. "
        "Do NOT use the primary checkout as a freshness source."
    )


_REVIEW_ATTEMPT_NO_REUSE_MARKER = "lu-review-attempt-no-reuse"


def _review_attempt_marker_path(worktree_path: Path) -> Path:
    try:
        proc = subprocess.run(
            ["git", "-C", str(worktree_path), "rev-parse", "--absolute-git-dir"],
            capture_output=True,
            text=True,
            check=False,
            timeout=DEFAULT_GIT_TIMEOUT_S,
            env=_sanitized_git_env(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"could not resolve git admin directory for {worktree_path}: {exc}") from exc
    git_dir = Path(proc.stdout.strip())
    if proc.returncode != 0 or not git_dir.is_absolute():
        raise RuntimeError(f"could not resolve git admin directory for {worktree_path}")
    return git_dir / _REVIEW_ATTEMPT_NO_REUSE_MARKER


def _refuse_review_attempt_worktree_reuse(worktree_path: Path) -> None:
    # A real linked worktree has a .git pointer. Test stubs may model only the
    # directory; the existing validation still handles those paths.
    if not (worktree_path / ".git").exists():
        return
    marker = _review_attempt_marker_path(worktree_path)
    if marker.is_file():
        try:
            task_id = marker.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise RuntimeError(f"could not read review attempt marker in {worktree_path}: {exc}") from exc
        raise ValueError(f"worktree {worktree_path} belongs to review attempt task {task_id!r}; reuse refused (#8517)")


def _mark_review_attempt_worktree(worktree_path: Path, task_id: str) -> None:
    marker = _review_attempt_marker_path(worktree_path)
    marker.write_text(f"{task_id}\n", encoding="utf-8")


def _ensure_worktree(
    *,
    agent: str,
    task_id: str,
    raw_path: str | None = None,
    base: str = "main",
    branch: str | None = None,
    resolved_base_sha: str | None = None,
    dry_run: bool = False,
    full_checkout: bool = False,
    sparse_include: Sequence[str] = (),
    run_nonce: str | None = None,
    detached: bool = False,
    validated_path: Path | None = None,
    review_dependencies: Sequence[tuple[str, Path]] = (),
    read_only: bool = False,
) -> tuple[Path, str | None, dict[str, Any]]:
    """Return a ready worktree path, creating or validating as needed.

    ``read_only`` (implied by ``detached``) provisions no database link and
    withdraws one a reused worktree still carries (#9421).

    ``run_nonce`` names the dispatch run a fresh worktree's path reservation
    is recorded under (see :func:`_add_reserved_worktree`). ``validated_path``,
    when given, is used as is and never resolved again (#8775,
    :func:`_helper_worktree_path`).
    ``review_dependencies`` retains attempt inputs before superseded-review or
    stale-holder cleanup can run, including detached earlier review rounds (#9388, #9417).

    The telemetry dict (third tuple element) carries:
    - ``base_sha``: the SHA the worktree was branched from (or is currently
      sitting on, if reused).
    - ``rebased``: whether :func:`_validate_existing_worktree` advanced the
      reused worktree.
    - ``layout``: ``"dispatch"`` or ``"flat"``.
    - ``reused``: whether the path already existed and was validated rather
      than created.
    - ``sparse``: sparse-checkout profile telemetry (when applied).
    """
    worktree_path = _helper_worktree_path(raw_path, validated_path)
    requested_branch = _validate_branch_reuse_name(branch) if branch else None
    if detached and requested_branch:
        raise ValueError("detached worktree cannot attach a branch")
    worktree_branch = None if detached else requested_branch or _derive_worktree_branch(agent, task_id)
    layout = _classify_worktree_layout(worktree_path)
    telemetry: dict[str, Any] = {
        "base_sha": None,
        "rebased": False,
        "layout": layout,
        "reused": False,
        "sparse": None,
        "local_venv": None,
    }
    if requested_branch and review_dependencies:
        _refuse_review_attempt_branch_holders(
            requested_branch,
            [path for path in _branch_worktree_paths(requested_branch) if path != worktree_path],
            review_dependencies,
        )
    _release_superseded_review_worktrees(task_id, dry_run=dry_run, review_dependencies=review_dependencies)

    if requested_branch:
        if resolved_base_sha is None:
            _fetch_existing_branch(requested_branch)
            _require_local_branch_is_ancestor_of_origin(requested_branch)
        occupied_paths = _branch_worktree_paths(requested_branch)
        elsewhere = [path for path in occupied_paths if path != worktree_path]
        if elsewhere:
            # #5340: clean+synced+terminal holders are pure friction — release
            # them instead of bouncing the dispatch. Live/dirty holders still refuse.
            _release_stale_branch_holders(
                branch=requested_branch,
                holders=elsewhere,
                dry_run=dry_run,
                review_dependencies=review_dependencies,
            )
            occupied_paths = _branch_worktree_paths(requested_branch)
            elsewhere = [path for path in occupied_paths if path != worktree_path]
            # dry-run treats releasable holders as free without mutating
            if dry_run:
                still_blocking = [
                    path for path in elsewhere if not _stale_branch_holder_releasable(path, requested_branch)[0]
                ]
            else:
                still_blocking = elsewhere
            if still_blocking:
                locations = ", ".join(str(path) for path in still_blocking)
                raise WorktreeBranchMismatch(
                    f"branch {requested_branch!r} is already checked out in {locations}; "
                    "refusing to attach it to another worktree"
                )

    if worktree_path.exists():
        if detached:
            raise ValueError(f"detached read-only worktree already exists: {worktree_path}; refuse reuse")
        if not worktree_path.is_dir():
            raise ValueError(f"worktree path exists but is not a directory: {worktree_path}")
        _refuse_review_attempt_worktree_reuse(worktree_path)
        telemetry["reused"] = True
        if resolved_base_sha is None:
            telemetry["rebased"] = _validate_existing_worktree(
                path=worktree_path,
                expected_branch=worktree_branch,
                # For --branch reuse the staleness/fast-forward reference is the
                # requested branch ITSELF (origin/<branch>), never origin/main: a
                # follow-up worktree for an existing PR is almost always behind
                # main (main moved since the PR branched), and validating against
                # main would spuriously fail the dry-run or rebase a PR branch
                # onto main as a validation side effect. (review-4905-grok)
                base=requested_branch or base,
                # `--branch` is an explicit attach request. Never rewrite its
                # history during provisioning; a stale worktree must be
                # synchronized deliberately by its owner.
                allow_rebase=not dry_run and requested_branch is None and not review_dependencies,
            )
        actual_sha = _resolve_sha(worktree_path)
        if actual_sha is None:
            raise RuntimeError(f"could not resolve HEAD for existing worktree {worktree_path}")
        if resolved_base_sha is not None and actual_sha != resolved_base_sha:
            raise WorktreeStaleBase(
                "existing worktree HEAD changed after immutable-base resolution; "
                f"expected {resolved_base_sha}, found {actual_sha}. Refusing worker spawn."
            )
        telemetry["base_sha"] = actual_sha
        if dry_run:
            return worktree_path, worktree_branch, telemetry
        # Reused worktrees may predate this provisioning hook; the helper is
        # idempotent and never clobbers existing files. For a read-only
        # dispatch it withdraws the restored database links instead (#9421).
        _provision_data_symlinks(worktree_path, _REPO_ROOT, read_only=read_only or detached)
        # Admission has already read these inputs. Preserve the current checkout
        # when it holds any dependency; reapplying sparse mode can hide those bytes.
        dependencies = _review_attempt_dependency_names(worktree_path, review_dependencies)
        if dependencies:
            print(
                f"ℹ️  reused worktree {worktree_path} kept current checkout: review dependency "
                f"({', '.join(dependencies)})",
                file=sys.stderr,
            )
        else:
            telemetry["sparse"] = _apply_dispatch_sparse_checkout(
                worktree_path,
                full_checkout=full_checkout,
                sparse_include=sparse_include,
            )
        _record_worktree_local_venv_warning(worktree_path, telemetry)
        return worktree_path, worktree_branch, telemetry

    if dry_run:
        raise ValueError(
            f"branch reuse dry-run found no existing worktree at {worktree_path}; rerun without --dry-run to create one"
        )

    # Fix 1 (#1476): fetch origin/{base} and branch from the remote ref,
    # not the local one. Local `main` drifts the moment a PR merges while
    # a dispatch is queued — this is the stale-base footgun Codex
    # diagnosed in bridge msg #431 (2026-04-23). Normalize so an
    # origin-prefixed ``base`` (``--base origin/main``, the mandated form)
    # fetches ``main`` and branches from ``origin/main`` — not the
    # unresolvable ``origin/origin/main``.
    if resolved_base_sha is not None:
        worktree_base_ref = resolved_base_sha
    elif requested_branch:
        # Attach directly to the fetched PR/follow-up branch.  Never branch
        # from origin/main here: that was the follow-up-dispatch footgun.
        worktree_base_ref = requested_branch
    else:
        origin_ref = _origin_base_ref(base)
        if _fetch_base(base):
            worktree_base_ref = origin_ref
        else:
            # #5803 follow-up: NO silent fallback to the local base. That
            # fallback is exactly why a worker concluded "origin/main may be
            # stale" and went to the PRIMARY checkout for a fresh copy,
            # leaving it detached. Fail with an actionable error instead.
            branch_name = _base_branch_name(base)
            raise RuntimeError(
                f"could not fetch origin/{branch_name} and {origin_ref} is "
                f"unresolvable — refusing to branch from possibly-stale local "
                f"{branch_name}. Check connectivity and that "
                "`git remote get-url origin` points at the canonical remote "
                "(github.com:learn-ukrainian/learn-ukrainian.github.io), then "
                f"run `git fetch origin +refs/heads/{branch_name}:refs/remotes/origin/{branch_name}` and retry the dispatch. "
                "Do NOT use the primary checkout as a freshness source."
            )

    # Ensure parent dirs exist for the dispatch/ subtree layout.
    worktree_path.parent.mkdir(parents=True, exist_ok=True)

    add_command = ["git", "worktree", "add"]
    if requested_branch and resolved_base_sha is None:
        # ``-B`` intentionally resets a behind local tracking ref to the SHA
        # fetched from origin. _require_local_branch_is_ancestor_of_origin()
        # already refused any local-only commits, and branch holders were
        # released/refused above, so this cannot silently overwrite work.
        add_command.extend(
            [
                "--track",
                "-B",
                requested_branch,
                str(worktree_path),
                f"origin/{requested_branch}",
            ]
        )
    elif requested_branch:
        # The branch was resolved before creation. Reset only to that immutable
        # commit, never a ref that might move before creation.
        add_command.extend(["-B", requested_branch, str(worktree_path), worktree_base_ref])
    elif detached:
        add_command.extend(["--detach", str(worktree_path), worktree_base_ref])
    else:
        add_command.extend(["-b", worktree_branch, str(worktree_path), worktree_base_ref])
    _add_reserved_worktree(
        add_command,
        repo_root=_REPO_ROOT,
        worktree_path=worktree_path,
        task_id=task_id,
        run_nonce=run_nonce,
        base_sha=resolved_base_sha,
    )
    actual_sha = _resolve_sha(worktree_path)
    if actual_sha is None:
        raise RuntimeError(f"could not resolve HEAD for created worktree {worktree_path}")
    if resolved_base_sha is not None and actual_sha != resolved_base_sha:
        raise WorktreeStaleBase(
            "created worktree HEAD differs from immutable base; "
            f"expected {resolved_base_sha}, found {actual_sha}. Refusing worker spawn."
        )
    telemetry["base_sha"] = actual_sha
    if requested_branch and resolved_base_sha is not None:
        # `git worktree add -B <branch> <path> <sha>` does not configure an
        # upstream. Restore the tracking contract the non-SHA branch path
        # gets from `--track`, after verifying the immutable checkout and
        # before any provisioning or worker side effect.
        try:
            upstream_proc = subprocess.run(
                ["git", "branch", "--set-upstream-to", f"origin/{requested_branch}", requested_branch],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=DEFAULT_GIT_TIMEOUT_S,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"could not configure upstream origin/{requested_branch} for {worktree_path}: timed out after {DEFAULT_GIT_TIMEOUT_S}s"
            ) from exc
        if upstream_proc.returncode != 0:
            detail = (upstream_proc.stderr or upstream_proc.stdout or "git branch failed").strip()
            raise RuntimeError(f"could not configure upstream origin/{requested_branch} for {worktree_path}: {detail}")
    _provision_data_symlinks(worktree_path, _REPO_ROOT, read_only=read_only or detached)
    telemetry["sparse"] = _apply_dispatch_sparse_checkout(
        worktree_path,
        full_checkout=full_checkout,
        sparse_include=sparse_include,
    )
    _record_worktree_local_venv_warning(worktree_path, telemetry)
    return worktree_path, worktree_branch, telemetry


def _resolve_primary_root_for_worktree(cwd_or_worktree: Path) -> Path:
    """Resolve the primary checkout root for a worktree or arbitrary cwd."""
    primary_root = _main_checkout_root(cwd_or_worktree)
    if primary_root == cwd_or_worktree and cwd_or_worktree != _REPO_ROOT:
        primary_root = _main_checkout_root(_REPO_ROOT)
    return primary_root


def _primary_database_path(primary_root: Path, name: str) -> Path:
    """Resolve the canonical primary path for data/sources.db or data/vesum.db (#9122)."""
    if name == "sources.db":
        override = os.environ.get("LU_SOURCES_DB")
        if override:
            p = Path(override).expanduser()
            return p.resolve() if p.is_absolute() else (primary_root / p).resolve()
        return (primary_root / "data" / "sources.db").resolve()
    return (primary_root / "data" / "vesum.db").resolve()


def _primary_database_connect_code(target: Path) -> str:
    """Return Python connect code opening target read-only via RFC file URI (#9122)."""
    uri = f"{target.resolve().as_uri()}?mode=ro"
    return f"sqlite3.connect({uri!r}, uri=True)"


def _augment_prompt_with_worktree(
    prompt: str,
    worktree_path: Path | None,
    *,
    mode: str = "read-only",
    sparse_telemetry: dict[str, Any] | None = None,
    delegate_commits: bool = False,
) -> str:
    """Inject worktree context into the delegated prompt when relevant.

    ``delegate_commits`` (Kimi seats) replaces the commit-and-push closeout:
    the worker leaves its changes in the tree and delegate commits the owned
    paths after checking that the diff adds no Cyrillic text.
    """
    if worktree_path is None:
        return prompt
    sparse_note = ""
    if sparse_telemetry and not sparse_telemetry.get("full_checkout"):
        excluded = sparse_telemetry.get("excluded") or []
        if excluded:
            add_commands = " ".join(f"`git sparse-checkout add {name}`" for name in excluded)
            sparse_note = (
                "Sparse-checkout is active: these trees are NOT present: "
                + ", ".join(str(p) for p in excluded)
                + ". To materialize one inside this worktree, run "
                + add_commands
                + " (for example `git sparse-checkout add data/projects`). "
                + "Do not invent content for missing paths.\n"
            )
    delivery_note = ""
    if mode in _WRITE_CAPABLE_MODES and delegate_commits:
        delivery_note = (
            "\n[write-mode closeout]\n"
            "Do not commit or push. Leave your changes in this worktree, inside the owned paths.\n"
            "After you exit, delegate checks the diff and commits and pushes the owned paths; "
            "a diff that adds any Cyrillic character, or content that is not text, is refused and "
            "nothing is committed. This worktree's git hooks refuse the same commits, and it has no push access.\n"
            "Delete scratch files before you finish.\n"
        )
    elif mode in _WRITE_CAPABLE_MODES:
        delivery_note = (
            "\n[write-mode closeout]\n"
            "Commit your work (use the literal trailer in `$LU_X_AGENT_TRAILER`).\n"
            "`git push -u origin HEAD`\n"
            "Leave `git status --porcelain` empty (commit or delete scratch files).\n"
            "Keep scratch git repositories and probes outside `batch_state/reports/` "
            "(use `$TMPDIR`, the managed lease, never a literal system temp path); "
            "`batch_state/` is reserved for report files and logs.\n"
            "Do not open or merge PRs unless the brief says so; "
            "report the pushed head SHA and clean status.\n"
            "\n[optional delivery signal]\n"
            "If you finish with zero commits (a verified no-op), you MAY end your final response "
            "with one machine-readable line as positive proof: "
            '`DELIVERABLE: {"outcome":"no_change","reason":"why no changes are required"}`. '
            "This line is optional — its absence never fails the dispatch.\n"
        )
    # #9057: every worktree dispatch carries one test-scope rule. Write modes
    # run only the tests for files they changed, including importers of a
    # changed shared helper; review modes cite CI. The PR's own CI, and the
    # merge queue on the merged tree, are the full-suite proof — a dispatch
    # `gh workflow run` does not satisfy the PR's required check.
    if mode in _WRITE_CAPABLE_MODES:
        test_scope = (
            "\n[test scope]\n"
            "Run only the tests that cover the files you changed, including tests of "
            "code that imports a changed shared helper, and name those test files explicitly.\n"
            "Never collect the whole `tests/` tree (`pytest tests`, `pytest tests -k …`); "
            "never `-n auto` or `-n` above 2.\n"
            "Run tests in the foreground and wait for them "
            "(never end the turn while a test runs in the background).\n"
            "The full suite runs in the PR's CI (and again in the merge queue on the merged "
            "tree) — that is the proof; do not trigger extra full runs. "
            "Use `gh workflow run ci.yml --ref <branch>` only when the brief explicitly asks "
            "for it (a branch with no PR yet, a baseline capture, or diagnosis).\n"
        )
    else:
        test_scope = (
            "\n[test scope]\n"
            "Do not re-run test suites that the PR's CI runs. Review the diff.\n"
            "Run at most the specific tests that reproduce a finding you are checking.\n"
            "Cite CI run ids for suite results.\n"
        )
    db_note = ""
    if worktree_path is not None:
        primary_root = _resolve_primary_root_for_worktree(worktree_path)
        primary_sources = _primary_database_path(primary_root, "sources.db")
        primary_vesum = _primary_database_path(primary_root, "vesum.db")
        sources_code = _primary_database_connect_code(primary_sources)
        vesum_code = _primary_database_connect_code(primary_vesum)
        db_note = (
            "\n[database access in worktrees]\n"
            "Primary databases (data/sources.db, data/vesum.db) reside in the primary checkout, "
            "not in this worktree. Prefer MCP tools (`sources` server: `verify_words`, `search_text`, etc.) "
            "which resolve databases automatically. If running ad-hoc Python/SQLite queries, NEVER use a relative "
            "path like `data/sources.db` or `data/vesum.db` (which creates an empty file in the worktree and triggers "
            "read-only checkout mutation failure); connect to the primary database using its absolute path read-only: "
            f"`{sources_code}` or `{vesum_code}`.\n"
        )
    # #8775: the path is data. ASCII JSON quoting keeps it one quoted line even
    # if an unvalidated path ever reaches this block.
    return (
        "[delegate worktree]\n"
        "Run all file edits, tests, and git commands inside this worktree "
        f"(JSON-quoted path): {json.dumps(str(worktree_path))}\n"
        "Do not switch branches in the main checkout.\n"
        # #5803 follow-up: remove the workflow reason to visit the primary.
        # A linked worktree shares the canonical `origin` remote, so fresh
        # main is always one fetch away from INSIDE the worktree.
        "If you need a fresh base, run `git fetch origin main` INSIDE this worktree — "
        "`origin` here points at the canonical GitHub remote and fetch works from any "
        "linked worktree. NEVER use the primary checkout as a source of freshness "
        "(no `git -C <primary> pull/fetch/checkout`); it is the human's interactive home.\n"
        "\n[shared project interpreter]\n"
        "Never create, copy, symlink, activate, or use a `.venv` inside this worktree. "
        f"Run every project Python command with `{project_interpreter()}` "
        "(the absolute primary interpreter), never `python`, `.venv/bin/python`, or "
        "`python -m venv .venv`. Do not change `PYTHONPATH` merely because the worker "
        "cwd is a worktree.\n"
        f"{sparse_note}{test_scope}{delivery_note}{db_note}\n"
        "[held work]\n"
        "Keep patches, handoffs and diagnostics needed after exit in this worktree's "
        "`batch_state/reports/`, and cite each file in your final response. "
        "Runtime scratch is deleted at exit; if held work remains there, cite its absolute "
        "file path or `$TMPDIR/<file>` in the final response so it is preserved. "
        "Cite regular files, not directories or symlinks; automatic preservation has a 256 MiB cap.\n\n"
        f"{prompt}"
    )


def _load_task_lifecycle_carrier(raw_path: str | None) -> tuple[dict[str, Any] | None, str]:
    """Validate one canonical lifecycle ledger before dispatch side effects."""
    if not raw_path:
        return None, ""
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    from scripts.orchestration import task_lifecycle

    path = Path(raw_path).expanduser().resolve()
    ledger = task_lifecycle.load_lifecycle(path)
    carrier = task_lifecycle.carrier_projection(ledger, state_file=str(path))
    return carrier, task_lifecycle.render_carrier_prompt(carrier)


class ResearchContextError(ValueError):
    """A --research-* flag violated a request-side bound (mirrors the API 422s)."""


def _build_research_context(args: argparse.Namespace):
    """Return a normalized research ``Context`` from the explicit --research-* flags.

    Returns ``None`` when no flag was given (the no-flags path stays byte-identical
    to a pre-P3 dispatch). Never infers a value from the prompt, agent, provider, or
    branch — ADR-011 P3 requires explicit dimensions and fails closed on the rest.
    Validates the same request-side caps the FastAPI query layer enforces so a
    direct CLI caller cannot smuggle an oversize/over-count context past the API.
    """
    role = getattr(args, "research_role", None)
    family = getattr(args, "research_task_family", None)
    track = getattr(args, "research_track", None)
    owned = getattr(args, "research_owned_path", None) or []
    if not (role or family or track or owned):
        return None

    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    from scripts.research import registry as reg

    for label, value in (
        ("--research-role", role),
        ("--research-task-family", family),
        ("--research-track", track),
    ):
        if value is not None and len(value) > reg.MAX_QUERY_VALUE_LEN:
            raise ResearchContextError(f"{label} value too long (max {reg.MAX_QUERY_VALUE_LEN} chars)")
    if len(owned) > reg.MAX_OWNED_PATHS:
        raise ResearchContextError(f"too many --research-owned-path values ({len(owned)} > {reg.MAX_OWNED_PATHS})")
    for path in owned:
        if len(path) > reg.MAX_OWNED_PATH_LEN:
            raise ResearchContextError(f"--research-owned-path value too long (max {reg.MAX_OWNED_PATH_LEN} chars)")
    return reg.normalize_context(role, family, track, owned)


def _render_research_prompt_block(pointers: list[dict[str, Any]]) -> str:
    """Render the bounded, POINTER-ONLY research block appended to a delegated prompt.

    Never contains a digest body/summary/source — only ids, states, and content
    hashes plus the on-demand fetch instruction. The pointer set is already capped
    (top-5 / ≤1.5 KB) by the selector.
    """
    lines = [
        "",
        "[project research pointers — ADR-011 P3]",
        "These research-registry records match this task's context. Bodies are NOT",
        "included; fetch one on demand only if you need it:",
        "  GET /api/knowledge/record/{id}?task={your-task-id}",
    ]
    for ptr in pointers:
        lines.append(f"- {ptr['id']} [{ptr['state']}] content_hash={ptr['content_hash']}")
    lines.append("")
    return "\n".join(lines)


_RESEARCH_POINTER_LINE = re.compile(r"- ([a-z0-9]+(?:-[a-z0-9]+)*) \[([a-z_-]+)\] content_hash=([A-Za-z0-9:]+)")


def _recorded_research_block(block: object) -> str:
    """A recorded research block, when it is exactly a rendering of research pointers (#9275).

    The bounded worker rebuilds its expected prompt with the research block the
    dispatcher recorded; only a block that re-renders from its own pointer
    lines is a permitted dispatcher block. Raises ``AdvisoryRefused`` otherwise.
    """
    if block in (None, ""):
        return ""
    text = str(block)
    pointers = [
        {"id": match.group(1), "state": match.group(2), "content_hash": match.group(3)}
        for line in text.splitlines()
        if (match := _RESEARCH_POINTER_LINE.fullmatch(line))
    ]
    if not pointers or _render_research_prompt_block(pointers) != text:
        raise bounded_advisory.AdvisoryRefused(
            bounded_advisory.ADMISSION_INVALID, "the recorded research block is not a rendering of research pointers"
        )
    return text


def _compose_dispatch_prompt(
    base: str,
    *,
    worktree_path: Path | None,
    mode: str,
    sparse_telemetry: dict[str, Any] | None,
    delegate_commits: bool,
    research_block: str,
    advisory_block: str,
    advisory_block_kind: str | None,
    rules_seat: str | None,
    blocks: list[str] | None = None,
    agent: str | None = None,
    review_route: bool = False,
) -> str:
    """The prompt a worker receives: ``base`` (the brief and any lifecycle block) inside the dispatcher blocks.

    In prompt order: the rules core, the worktree block, ``base``, the research
    pointers and the advisory block. ``blocks``, when given, gets the kinds
    added, in prompt order. The bounded worker rebuilds its expected prompt
    with this function (#9275), so the two cannot drift apart.
    """
    prompt = _augment_prompt_with_worktree(
        base,
        worktree_path,
        mode=mode,
        sparse_telemetry=sparse_telemetry,
        delegate_commits=delegate_commits,
    )
    if worktree_path is not None and blocks is not None:
        blocks.insert(0, "worktree")
    if research_block and blocks is not None:
        blocks.append("research")
    prompt = prompt + research_block
    if advisory_block_kind is not None:
        if blocks is not None:
            blocks.append(advisory_block_kind)
        prompt = prompt + advisory_block
    # Every worker and review seat starts with the rules core, read from this checkout.
    cored_prompt = rules_core.with_core(prompt, rules_seat)
    if cored_prompt != prompt:
        if blocks is not None:
            blocks.insert(0, "rules_core")
        prompt = cored_prompt
    if agent == "agy" and mode in ("workspace-write", "danger") and not review_route:
        from scripts.agent_runtime.adapters.agy import _WRITE_MODE_PROMPT_CONTRACT
        prompt += _WRITE_MODE_PROMPT_CONTRACT
        if blocks is not None:
            blocks.append("agy_write_contract")
    return prompt


def _with_optional_research_state(state: dict[str, Any], research_state: dict[str, Any] | None) -> dict[str, Any]:
    """Add ``"research"`` to ``state`` only when ``research_state`` is non-``None``.

    ADR-011 P3 default-compatibility: a no-flags dispatch, a disabled registry, or
    a degraded/failed injection must persist byte-identical pre-P3 state — the key
    is OMITTED, never present as ``"research": null``. Pointer ids / filtered ETag
    / dropped ids / context fingerprint only when present — never raw owned paths,
    digest/source/prompt text, role, or task family.
    """
    if research_state is not None:
        state["research"] = research_state
    return state


def _resolve_research_injection(ctx, task_id: str) -> tuple[str, dict[str, Any] | None]:
    """Fail-open pointer resolution for a dispatch context.

    Returns ``(prompt_block, persist_state)``. ``persist_state`` records ONLY the
    pointer ids, filtered projection ETag, dropped ids, and a context fingerprint —
    never raw owned paths, digest/source/prompt text, role, or task family. Any
    disabled/malformed/unexpected registry condition degrades to ``("", None)`` so a
    dispatch is never blocked by the research surface. Emits one surface (not
    consumption) telemetry event per injected pointer, attributed to ``task_id``.
    """
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    from scripts.research import consumption
    from scripts.research import registry as reg

    try:
        if not reg.is_enabled(root=_REPO_ROOT):
            return "", None
        runtime = reg.load_runtime_safe(root=_REPO_ROOT)
        if runtime is None:
            return "", None
        pointers, dropped = reg.select_pointers(runtime, ctx)
        etag = reg.filtered_manifest(runtime, ctx).etag_hex
        persist_state = {
            "pointer_ids": [ptr["id"] for ptr in pointers],
            "filtered_etag": etag,
            "dropped_ids": list(dropped),
            "context_fingerprint": reg.context_fingerprint(ctx),
        }
        if not pointers:
            return "", persist_state
        for ptr in pointers:
            consumption.emit_surface(
                research_id=ptr["id"],
                surface=consumption.SURFACE_DISPATCH,
                task_id=task_id,
            )
        return _render_research_prompt_block(pointers), persist_state
    except Exception as exc:  # fail-open: research never blocks a dispatch
        print(
            f"[delegate] WARNING: research pointer injection skipped: {type(exc).__name__}",
            file=sys.stderr,
        )
        return "", None


# ---------------------------------------------------------------------------
# Worker entrypoint — runs inside the detached subprocess
# ---------------------------------------------------------------------------


def _worker_sigterm_handler(_signum, _frame):
    """SIGTERM handler for the worker process.

    Default Python SIGTERM behavior is to terminate abruptly WITHOUT
    running any finally blocks — meaning a cancel via
    ``delegate.py cancel`` would leave the child CLI subprocess
    (codex exec, gemini, claude) orphaned. That's a real leak,
    especially for workspace-write / danger modes.

    Fix: install this handler in _run_worker. When the parent sends
    SIGTERM, this raises KeyboardInterrupt, which propagates up
    through runner.invoke()'s try/finally block, which kills the
    subprocess and stops the watchdog cleanly. The worker's own
    try/except in _run_worker catches the KeyboardInterrupt, writes
    a final state file with status=failed + a "cancelled via SIGTERM"
    stderr excerpt, and exits 1.

    Added after Gemini review 2026-04-10.
    """
    raise KeyboardInterrupt("SIGTERM received; unwinding for cleanup")


def _classify_final_status(
    *,
    cancelled: bool,
    rate_limited: bool,
    ok_outcome: bool,
    timed_out: bool = False,
) -> str:
    """Map worker outcome flags to the persisted delegate task status."""
    if cancelled:
        return "cancelled"
    if timed_out:
        return "timeout"
    if rate_limited:
        return "rate_limited"
    if ok_outcome:
        return "done"
    return "failed"


def _worker_run_incomplete(stderr_excerpt: str | None) -> bool:
    """True when the adapter could not prove the worker's run finished its work.

    AGY print mode can exit 0 while the agent's backgrounded commands are still
    running or were killed (#8502/#8503); the adapter then leads
    ``stderr_excerpt`` with a reason code — including when no transcript bound
    to this run exists to prove completion. Whatever that worker left in its
    worktree is unconfirmed, so it must never be auto-finalized as ``done``.
    """
    from agent_runtime.adapters.agy import AGY_INCOMPLETE_RUN_REASONS

    return _first_error_line(stderr_excerpt) in AGY_INCOMPLETE_RUN_REASONS


# Children that exit on their own right after the CLI (a stdio MCP server
# reading EOF) get this long before they count as background jobs.
_BACKGROUND_JOBS_SETTLE_S = 5.0


def _worker_process_reader() -> worker_leftovers.ProcessReader:
    """Seam for tests: the live ``/proc`` and cgroup reader."""
    return worker_leftovers.ProcFsReader()


def _worker_pidfd_ops() -> worker_leftovers.PidfdOps:
    """Seam for tests: the live pidfd calls the exit scan signals through."""
    return worker_leftovers.live_pidfd_ops()


def _background_jobs_at_exit(state: Mapping[str, Any], *, task_id: str) -> worker_leftovers.ExitScan | None:
    """Whether processes of this worker outlived its CLI (#8991); None when not checked.

    Runs inside the detached worker, so only records carrying the
    ``launch_mode`` that spawn wrote are checked: a foreground or test run has
    no scope or session of its own to inspect. The scope's ``cgroup.procs``
    (or, on the Popen fallback, the task's environment marker and the worker's
    session) bound the scan. A headless session cannot be woken by a
    background-task notification, so whatever is still running is unfinished
    work, and a scan that could not read everything it needed is ``unknown``,
    never ``clear``. A scope launch first stops the Cursor CLI's own
    ``worker-server`` in its cgroup (#9534); anything that survives is still
    reported. Never raises.
    """
    launch_mode = state.get("launch_mode")
    if launch_mode not in {dispatch_isolation.LAUNCH_SCOPE, dispatch_isolation.LAUNCH_FALLBACK}:
        return None

    def recorded(key: str) -> str | None:
        value = state.get(key)
        return value if isinstance(value, str) and value else None

    scope = worker_leftovers.WorkerScope(
        task_id=task_id,
        launch_mode=str(launch_mode),
        unit=recorded("launch_unit") if launch_mode == dispatch_isolation.LAUNCH_SCOPE else None,
        run_nonce=recorded("run_nonce"),
    )
    try:
        reader = _worker_process_reader()
        scope = worker_leftovers.worker_scope_at_exit(
            task_id=task_id,
            launch_mode=str(launch_mode),
            launch_unit=recorded("launch_unit"),
            run_nonce=recorded("run_nonce"),
            reader=reader,
        )
        scan = worker_leftovers.exit_scan(
            scope, reader=reader, settle_s=_BACKGROUND_JOBS_SETTLE_S, pidfd=_worker_pidfd_ops()
        )
    except Exception as exc:
        scan = worker_leftovers.ExitScan(
            status=worker_leftovers.SCAN_UNKNOWN, scope=scope, error=f"{type(exc).__name__}: {exc}"[:300]
        )
    if scan.status == worker_leftovers.SCAN_UNKNOWN:
        print(
            f"[delegate] WARNING: background-job check could not read the worker scope: {scan.error}", file=sys.stderr
        )
    return scan


def _first_error_line(stderr_excerpt: str | None) -> str | None:
    """Return the first non-blank captured stderr line for task summaries."""
    if not stderr_excerpt:
        return None
    return next(
        (line.strip() for line in stderr_excerpt.splitlines() if line.strip()),
        None,
    )


def _worker_last_error(
    task_id: str | None,
    *,
    stderr_excerpt: str | None,
    failure_cause: str | None,
    final_status: str,
    returncode: int | None,
    runtime_failure_code: str | None,
    worker_exception: _TypedCause | None,
) -> str | None:
    """The public cause a failed run's ``last_error`` names; None when no error line was captured (#9878).

    A gate's or refusal's cause comes first, then an error line that is itself
    a registered cause (an adapter's typed reason), the runtime's typed failure
    code, the terminal status, the exception class that ended the run, and
    else ``worker_failed`` with its exit status. The captured error line it
    summarizes stays in ``stderr_excerpt`` and goes to the task's ``.diag``.
    """
    line = _first_error_line(stderr_excerpt)
    if line is None:
        return None
    if failure_cause:
        public = public_cause(failure_cause)[0] or UNCLASSIFIED_CAUSE
    elif is_public_cause(line):
        return line
    elif runtime_failure_code in public_causes():
        public = str(runtime_failure_code)
    elif final_status in _STATUS_FAILURE_CAUSES:
        public = _STATUS_FAILURE_CAUSES[final_status]
    elif worker_exception is not None:
        public = worker_exception.public()
    else:
        public = _TypedCause("worker_failed", exit_status=returncode).public()
    if task_id:
        _record_diagnostic(
            task_id,
            _TypedCause(public.split("; ")[0].split(", ")[0], diagnostic=line),
            source="worker",
            field="last_error",
        )
    return public


_STATUS_FAILURE_CAUSES = {
    "cancelled": "worker_cancelled",
    "timeout": "worker_timed_out",
    "rate_limited": "worker_rate_limited",
}


def _kimi_refusal_cause(refusal: str, unreadable: _TypedCause | None) -> tuple[str, _TypedCause]:
    """``(public form, cause to record)`` for a Kimi content refusal (#9878).

    The public form is ``kimi_content_refused``, followed by the typed cause
    when the changes could not be read; the refusal text (paths and the lines
    that held Cyrillic text) and git's error go only to the task's ``.diag``.
    """
    cause = unreadable or _TypedCause("kimi_content_refused")
    detail = f"{refusal}\n{cause.diagnostic}" if cause.diagnostic else refusal
    public = "kimi_content_refused" if unreadable is None else f"kimi_content_refused; {unreadable.public()}"
    return public, dataclasses.replace(cause, diagnostic=detail)


def _sources_mcp_call_count(result: Any) -> int | None:
    """Count Sources invocations from runtime telemetry without retaining arguments."""
    total = getattr(result, "tool_calls_total", None)
    calls = getattr(result, "tool_calls", None)
    if type(total) is not int or total < 0 or not isinstance(calls, list) or len(calls) != total:
        return None
    names = []
    for call in calls:
        if not isinstance(call, dict) or not isinstance(call.get("name"), str) or not call["name"].strip():
            return None
        names.append(call["name"])
    return sum(
        bool(re.fullmatch(r"(?:mcp__sources__|mcp_sources_)[A-Za-z][A-Za-z0-9_]*", name))
        for name in names
    )


def _emit_terminal_dispatch_event(
    *,
    task_id: str,
    agent: str,
    final_state: dict[str, Any],
    result: Any,
    fallback_prompt_chars: int,
) -> None:
    """Emit the central terminal dispatch event without affecting worker exit."""
    try:
        try:
            from telemetry.emit import emit_event
            from telemetry.pricing import compute_cost
        except ImportError:  # pragma: no cover - package import path
            from scripts.telemetry.emit import emit_event
            from scripts.telemetry.pricing import compute_cost

        usage_record = getattr(result, "usage_record", None)
        tokens = usage_record.get("tokens") if isinstance(usage_record, dict) else None
        substitution = final_state.get("substitution")
        if substitution is None and isinstance(usage_record, dict):
            substitution = usage_record.get("substitution")
        model = final_state.get("model")
        cost = compute_cost(
            str(model).strip() if model else None,
            tokens,
            agent=agent,
        )
        emit_event(
            "dispatch",
            {
                "task_id": task_id,
                "agent": agent,
                "model": model,
                "resolved_model": final_state.get("resolved_model"),
                "resolved_model_known": final_state.get("resolved_model_known"),
                "resolved_model_source": final_state.get("resolved_model_source"),
                "effort": final_state.get("effort"),
                "branch": final_state.get("worktree_branch"),
                "worktree": final_state.get("worktree_path"),
                "status": final_state.get("status"),
                "duration_s": final_state.get("duration_s"),
                "result_file": final_state.get("result_file"),
                "prompt_chars": final_state.get("prompt_chars", fallback_prompt_chars),
                "response_chars": final_state.get("response_chars"),
                "tokens": tokens,
                "substitution": substitution,
                "cost_usd": cost.cost_usd,
                "billing_model": cost.billing_model,
                "cost_provenance": cost.provenance,
                "tmp_bytes_freed": final_state.get("tmp_bytes_freed"),
                "tmp_reap_error": final_state.get("tmp_reap_error"),
            },
        )
    except Exception as exc:  # pragma: no cover - degraded mode only
        _logger.debug(
            "failed to emit terminal dispatch telemetry: %s: %s",
            type(exc).__name__,
            exc,
        )


def _dispatch_worker_identity_flags(args: argparse.Namespace, requested_harness: str | None) -> list[str]:
    """Flags ``cmd_dispatch`` copies onto the ``_worker`` argv.

    ``--harness`` selects the Kimi transport and ``--require-review-verdict``
    carries the review completion gate. Review-attempt MCP flags stay on the
    ``review_plan`` branch and are not part of this list.
    """
    flags: list[str] = []
    if requested_harness is not None:
        flags.extend(["--harness", requested_harness])
    if bool(getattr(args, "require_review_verdict", False)):
        flags.append("--require-review-verdict")
    return flags


def _run_worker(
    task_id: str,
    agent: str,
    prompt: str,
    mode: str,
    cwd_str: str,
    model: str | None,
    hard_timeout: int,
    silence_timeout: int = DEFAULT_SILENCE_TIMEOUT_S,
    effort: str | None = None,
    max_budget_usd: float | None = None,
    initial_response_timeout: int = DEFAULT_INITIAL_RESPONSE_TIMEOUT_S,
    keep_worktree: bool = False,
    provider: str | None = None,
    output_schema_path: str | None = None,
    output_schema_sha256: str | None = None,
    harness: str | None = None,
    runtime_tmp_root: str | None = None,
    runtime_tmp_namespace_root: str | None = None,
    run_nonce: str | None = None,
    require_review_verdict: bool = False,
    review_id: str | None = None,
    attempt_id: str | None = None,
    mcp_config_path: str | None = None,
    strict_mcp_config: bool = False,
    review_manifest: str | None = None,
    review_input_root: str | None = None,
    review_access: str = "isolated",
    finalize_open_pr: bool = False,
) -> int:
    """Worker main loop. Invokes the runtime, updates the state file.

    Returns the process exit code to use: 0 on ok, 1 on any failure.
    The parent never sees this return code directly — it reads the
    state file instead — but returning it cleanly allows the process
    to show up correctly in ``ps`` and systemd-style supervisors if
    we ever wrap this in one.
    """
    # The worker is a second entry point: a worker argv built by hand or a
    # stale parent must not invoke a Kimi seat outside web, UI and backend
    # coding. It reads the task's owned paths in the tree it is about to run
    # in, then installs the worktree boundary (hooks and push block), before
    # any state write or invocation. A refusal goes to the caller only.
    kimi_refusal, worker_target = _kimi_worker_refusal(
        task_id,
        agent=agent,
        model=model,
        mode=mode,
        cwd=Path(cwd_str),
        review=require_review_verdict or review_id is not None,
        prompt=prompt,
    )
    if kimi_refusal:
        from scripts.agent_runtime import kimi_admission

        record = _read_state_json(_state_path_no_create(task_id))
        if record and record.get("status") == "failed" and record.get("failure_reason") == kimi_refusal:
            record.update(_reap_runtime_tmp_lease(runtime_tmp_root, runtime_tmp_namespace_root))
            _write_state_atomic(_state_path_no_create(task_id), record)
        # A fixed prefix and the typed cause only (#9878).
        policy = f"{kimi_admission.POLICY_NAME}: " if kimi_admission.is_kimi_seat(agent, model=model) else ""
        print(f"❌ ROUTING REFUSED: {policy}{kimi_refusal}", file=sys.stderr)
        return 1
    # The worker runs the admitted seat and model; nothing resolves them again.
    agent, model = worker_target.recipient, worker_target.model
    # #9275: a bounded model runs only with the parent's advisory admission in
    # the task record, re-verified here on the launch values it runs; nothing
    # reaches the provider without it.
    advisory_execution = {
        "effort": effort,
        "hard_timeout": hard_timeout,
        "silence_timeout": silence_timeout,
        "initial_response_timeout": initial_response_timeout,
        "max_budget_usd": max_budget_usd,
        "provider": provider,
        "harness": harness,
        "finalize_open_pr": finalize_open_pr,
    }
    advisory_refusal = _advisory_worker_refusal(
        task_id,
        agent=agent,
        model=model,
        mode=mode,
        cwd=Path(cwd_str),
        execution=advisory_execution,
        prompt=prompt,
        runtime_tmp_root=runtime_tmp_root,
        runtime_tmp_namespace_root=runtime_tmp_namespace_root,
    )
    if advisory_refusal:
        print(f"❌ {advisory_refusal}", file=sys.stderr)
        return 1
    from scripts.agent_runtime.adapters.cursor import CURSOR_AUTO_ADMITTED_KEY
    from scripts.agent_runtime.kimi_admission import OWNED_PATHS_KEY, is_kimi_seat

    # Install SIGTERM handler so `delegate.py cancel` unwinds cleanly
    # through the runtime's finally block (see handler docstring).
    signal.signal(signal.SIGTERM, _worker_sigterm_handler)

    # Imports inside the function so the CLI startup path stays fast
    # and doesn't pay the cost of loading the runtime on 'status' calls.
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))
    from agent_runtime.errors import (
        AgentRuntimeError,
        AgentStalledError,
        AgentTimeoutError,
        RateLimitedError,
    )
    from agent_runtime.runner import invoke as runtime_invoke
    from agent_runtime.telemetry import resolve_dispatch_start_telemetry

    state_path = _state_path(task_id)

    # Update state to include our actual PID. The parent wrote an
    # initial state before forking; we overwrite with the real one
    # (in case the parent's guess was off, or we were re-exec'd).
    state = _read_state(state_path) or {}
    state["pid"] = os.getpid()
    state["status"] = "running"
    state["max_budget_usd"] = max_budget_usd
    effective_nonce = run_nonce or os.environ.get("LU_RUNTIME_RUN_NONCE")
    if effective_nonce:
        state["run_nonce"] = effective_nonce
    if "cli_version" not in state:
        start_telemetry = resolve_dispatch_start_telemetry(
            agent_name=agent,
            requested_model=model,
            requested_effort=effort,
            harness=harness,
            probe_cli_version=not (review_manifest and review_access == "full"),
        )
        state.setdefault("model", start_telemetry.model)
        state.setdefault("effort", start_telemetry.effort)
        state.setdefault("cli_version", start_telemetry.cli_version)
    _write_state_atomic(state_path, state)

    cwd = Path(cwd_str)
    read_only_checkout_pre: dict[str, str] | None = None
    read_only_checkout_post: dict[str, str] | None = None
    task_records_pre: dict[str, str] | None = None
    read_only_snapshot_error: str | None = None
    task_records_snapshot_error: str | None = None
    read_only_mutation_paths: list[str] = []
    read_only_ignored_mutation_paths: list[str] = []
    # Set only after digest.json is on disk. Phase files stay until the
    # terminal record that names retention=digest has been written.
    clean_snapshots_to_discard: Path | None = None
    if mode == "read-only":
        read_only_checkout_pre, read_only_snapshot_error = _read_only_checkout_snapshot(cwd)
        task_records_pre, task_records_error = _read_only_task_record_snapshot(task_id)
        task_records_snapshot_error = task_records_error
        if read_only_snapshot_error is None:
            read_only_snapshot_error = task_records_error
        _write_read_only_snapshot_sidecar(task_id, "pre", read_only_checkout_pre)
        state["read_only_checkout_snapshot_error"] = read_only_snapshot_error
        _write_state_atomic(state_path, state)
    start = time.monotonic()
    ok_outcome = False
    stderr_excerpt = None
    response = ""
    returncode: int | None = None
    returncode_reason: str | None = None
    rate_limited = False
    runtime_failure_code: str | None = None
    # The typed cause of an exception that ended the run (#9878); its message stays in stderr_excerpt.
    worker_exception: _TypedCause | None = None
    # A gate's or refusal's public cause, which names the failure ahead of the worker's own outcome.
    failure_cause: str | None = None
    timed_out = False
    result = None
    substitution: dict[str, Any] | None = None
    runtime_tmp_reap: dict[str, Any] | None = None

    cancelled = False
    # ONE recovery region, spanning the runtime call itself through the moment
    # the outcome is on disk.
    #
    # Seven review rounds each found a different instruction-level gap — the
    # reaper, the checkpoint, a second signal, lease cleanup, the boundary right
    # after lease cleanup — and each fix guarded that gap and created the next
    # one, because the interval kept being cut into guarded and unguarded
    # halves. The gaps were not the bug; splitting the interval was. This region
    # is the whole interval, so there is no boundary left to land between.
    #
    # A cancellation during the runtime call records ``cancelled`` — accurate,
    # the worker really was stopped. A cancellation after it records the
    # outcome the worker reached. Either way the state file stops saying
    # "running" about a process that is gone, and the signal still propagates.
    # What remains uncoverable in-process is SIGKILL, which the dead-pid probe
    # in cmd_status/cmd_wait already reports.
    #
    # Nothing the fallback reads may be bound only inside this region: a handler
    # that raises UnboundLocalError fails exactly when it is needed. Every name
    # it touches is initialized above, including the runtime-outcome flags.
    # Read the persisted record BEFORE the region, not inside it. Starting the
    # fallback from {} meant an early interrupt atomically REPLACED the task
    # file — recording a terminal status while destroying task_id, pid, mode,
    # cwd and worktree metadata that status/wait/cleanup and the operator all
    # read. A terminal status with no context is not an improvement over a stale
    # running one. (Cross-family review of #5807, round nine.)
    final_state: dict[str, Any] = _read_state(state_path) or {}
    worktree_path = final_state.get("worktree_path")
    final_status = ""
    duration_s = time.monotonic() - start
    result_file: str | None = None
    dirty_on_exit: bool | None = None
    commits_ahead: int | None = None
    needs_finalize = False
    finalize_error: str | None = None
    no_deliverable = False
    no_deliverable_reason: str | None = None
    pre_spawn_failure = False
    # #9275: the digest of the prompt checked and submitted at the provider
    # handoff, or the typed code that refused it there.
    advisory_prompt_sha256: str | None = None
    advisory_handoff_refusal: str | None = None
    delivery_declaration: dict[str, Any] | None = None
    auto_finalize: AutoFinalizeResult | None = None
    leftovers_scan: worker_leftovers.ExitScan | None = None
    leftovers_unconfirmed = False
    telemetry_settled = False
    # #9275: set only once every applicable completion gate (delivery, review
    # verdict, advisory ceiling or exemption) has run on the current tree and
    # the outcome is final. Before that the interrupt fallback never persists
    # ``done``: an interrupted gate is not a passed gate.
    completion_gates_settled = False
    rescue_status: str | None = None
    kimi_worker = is_kimi_seat(agent, model=model)
    kimi_content_refusal: str | None = None
    kimi_refusal_text: str | None = None
    cursor_mcp_path: Path | None = None
    cursor_mcp_backup: bytes | None = None
    cursor_mcp_existed = False
    from scripts.agent_runtime.result import AgyTelemetry

    agy_telemetry = AgyTelemetry(parent_task_id=task_id) if agent == "agy" else None

    try:
        try:
            stdout_silence_timeout = silence_timeout if silence_timeout > 0 else None
            initial_probe = initial_response_timeout if initial_response_timeout > 0 else None
            tool_config: dict[str, Any] = {}
            if state.get("mechanical_task"):
                tool_config["mechanical_task"] = state["mechanical_task"]
            if (
                agent in {"agy", "gemini"}
                and (
                    _dispatch_is_review_typed(argparse.Namespace(**state))
                    or require_review_verdict
                    or review_id is not None
                )
            ):
                tool_config["review_profile"] = state.get("review_profile") or "code"
                if (
                    mode == "read-only"
                    and tool_config["review_profile"] in {"ukrainian", "code"}
                    and mcp_config_path is None
                    and review_id is None
                    and attempt_id is None
                ):
                    # Formal attempts provision their home at the runtime boundary;
                    # missing attempt inputs must reach its typed refusal first.
                    from scripts.agent_runtime.review_mcp import prepare_agy_permission_home

                    if runtime_tmp_root is None:
                        raise ValueError("agy_review_permissions_require_scoped_home")
                    tool_config["agy_home_override"] = str(
                        prepare_agy_permission_home(Path(runtime_tmp_root), checkout_root=Path(cwd_str))
                    )
            if agent in {"agy", "gemini"} and mcp_config_path is not None and attempt_id is not None:
                from scripts.agent_runtime.review_mcp import review_ledger_path

                tool_config["review_ledger_path"] = str(review_ledger_path(mcp_config_path))
            if max_budget_usd is not None:
                tool_config["max_budget_usd"] = max_budget_usd
            if provider is not None:
                tool_config[RUNTIME_ROUTE_TOOL_CONFIG_KEY] = {"provider": provider}
            if output_schema_path is not None:
                tool_config["output_schema_path"] = output_schema_path
                tool_config["output_schema_sha256"] = output_schema_sha256
            if harness is not None:
                tool_config["harness"] = harness
            if mode == "read-only" and runtime_tmp_root is not None:
                tool_config["read_only_tmp_root"] = runtime_tmp_root
            if mcp_config_path is not None:
                tool_config["mcp_config_path"] = mcp_config_path
            if strict_mcp_config:
                tool_config["strict_mcp_config"] = True
                tool_config["mcp_server_names"] = ["sources"]
            if review_id is not None:
                tool_config["review_id"] = review_id
            if attempt_id is not None:
                tool_config["attempt_id"] = attempt_id
            if review_manifest is not None:
                tool_config["review_manifest"] = review_manifest
                tool_config["review_input_root"] = review_input_root
            if review_manifest is not None:
                tool_config["review_access"] = review_access
                tool_config["review_cwd"] = str(cwd)
            if (
                strict_mcp_config
                and review_id is not None
                and attempt_id is not None
                and agent == "claude"
                and review_access == "isolated"
            ):
                from scripts.agent_runtime.review_mcp import review_tools_allowed_csv

                tool_config["allowed_tools"] = review_tools_allowed_csv(agent)
            elif agent in {"claude", "grok", "grok-build"} and mode == "read-only":
                tool_config["reviewer_tools"] = True
            if (
                strict_mcp_config
                and review_id is not None
                and attempt_id is not None
                and mcp_config_path is not None
                and agent == "codex"
                and review_access != "full"
            ):
                # Codex has no --mcp-config: -c mcp_servers.* MERGES with global config, so
                # the attempt runs under its scoped CODEX_HOME (sibling of the .mcp.json)
                # with no daemon URL override, and is gated on the effective MCP set (#8517).
                from scripts.agent_runtime.review_mcp import (
                    codex_review_home_path,
                    verify_codex_review_launch,
                )

                tool_config["codex_home_override"] = str(codex_review_home_path(mcp_config_path))
                verify_codex_review_launch(
                    config_path=mcp_config_path,
                    cwd=cwd,
                    mode=mode,
                    model=model,
                    effort=effort,
                    task_id=task_id,
                    tool_config=tool_config,
                )
            if (
                strict_mcp_config
                and review_id is not None
                and attempt_id is not None
                and mcp_config_path is not None
                and agent == "agy"
                and review_access != "full"
            ):
                # agy has no per-invocation MCP flag and reads its servers from
                # $HOME/.gemini/config, so the attempt runs under its scoped home (sibling
                # of the .mcp.json) and is gated on the effective MCP set (#8617).
                from scripts.agent_runtime.review_mcp import (
                    agy_review_home_path,
                    verify_agy_review_launch,
                )

                tool_config["agy_home_override"] = str(agy_review_home_path(mcp_config_path))
                verify_agy_review_launch(
                    config_path=mcp_config_path,
                    cwd=cwd,
                    mode=mode,
                    model=model,
                    effort=effort,
                    task_id=task_id,
                    tool_config=tool_config,
                )
            if strict_mcp_config and agent == "cursor":
                cursor_mcp_path = cwd / ".cursor" / "mcp.json"
                if cursor_mcp_path.is_file():
                    cursor_mcp_existed = True
                    try:
                        cursor_mcp_backup = cursor_mcp_path.read_bytes()
                    except OSError as exc:
                        raise RuntimeError(f"failed to back up {cursor_mcp_path}: {exc}") from exc

            if strict_mcp_config and review_id is not None and attempt_id is not None and mcp_config_path is not None:
                # Last check before the path strings reach the launcher: re-walk the attempt
                # directory no-follow and owner-checked (#8652). It narrows, not closes, the window.
                from scripts.agent_runtime.review_mcp import verify_review_attempt_paths

                verify_review_attempt_paths(mcp_config_path)

            if isinstance(state.get(CURSOR_AUTO_ADMISSION_STATE_KEY), dict) and state[
                CURSOR_AUTO_ADMISSION_STATE_KEY
            ].get("admitted"):
                tool_config[CURSOR_AUTO_ADMITTED_KEY] = True
            if is_kimi_seat(agent, model=model):
                # The runner and the adapters run the same gate on these paths and this tree.
                tool_config[OWNED_PATHS_KEY] = list(_declared_owned_paths(state.get("owned_paths")) or ())
            # #9275: the provider handoff. The admission is re-verified on the
            # exact prompt object submitted below, after every transformation.
            advisory_prompt_sha256 = _verify_bounded_worker(
                task_id, agent=agent, model=model, mode=mode, cwd=cwd, execution=advisory_execution, prompt=prompt
            )
            result = runtime_invoke(
                agent,
                prompt,
                mode=mode,
                cwd=cwd,
                model=model,
                task_id=task_id,
                session_id=None,  # Layer 3 is always fresh-session
                tool_config=tool_config,
                entrypoint="delegate",
                hard_timeout=hard_timeout,
                stdout_silence_timeout=stdout_silence_timeout,
                initial_response_timeout=initial_probe,
                effort=effort,
            )
            ok_outcome = result.ok
            response = result.response
            stderr_excerpt = result.stderr_excerpt
            returncode = result.returncode
            rate_limited = result.rate_limited
            runtime_failure_code = getattr(result, "failure_code", None)
            if not isinstance(runtime_failure_code, str):
                runtime_failure_code = None
            substitution = getattr(result, "substitution", None)
            agy_telemetry = getattr(result, "agy_telemetry", agy_telemetry)
        except KeyboardInterrupt as exc:
            # Raised by our SIGTERM handler (or by Ctrl+C in manual runs).
            # The runtime's finally block has already killed the CLI
            # subprocess and stopped the watchdog by the time we catch
            # this, so no extra cleanup is needed here. Mark as cancelled.
            cancelled = True
            stderr_excerpt = f"cancelled via SIGTERM or Ctrl+C: {exc}"[:500]
            returncode_reason = "worker interrupted before a terminal subprocess returncode was available"
        except RateLimitedError as exc:
            agy_telemetry = getattr(exc, "agy_telemetry", None) or agy_telemetry
            rate_limited = True
            stderr_excerpt = str(exc)[:500]
            returncode_reason = "runtime rejected the dispatch before a terminal subprocess returncode was available"
        except AgentStalledError as exc:
            agy_telemetry = getattr(exc, "agy_telemetry", None) or agy_telemetry
            timed_out = True
            substitution = getattr(exc, "substitution", None)
            if getattr(exc, "kind", "stall") == "initial_response_timeout":
                stderr_excerpt = (
                    f"initial_response_timeout fired after {exc.stall_timeout}s "
                    f"with no first observable startup activity "
                    f"(stdout, stderr, liveness file, or process-tree work): {exc} "
                    f"— raise it with --initial-response-timeout "
                    f"(current default {DEFAULT_INITIAL_RESPONSE_TIMEOUT_S}s)"
                )[:500]
            else:
                stderr_excerpt = (
                    f"stdout_silence_timeout fired after {exc.stall_timeout}s "
                    f"without watchdog activity: {exc} "
                    f"— raise it with --silence-timeout "
                    f"(current default {DEFAULT_SILENCE_TIMEOUT_S}s)"
                )[:500]
            returncode_reason = "runtime timeout raised before a terminal subprocess returncode was available"
        except AgentTimeoutError as exc:
            agy_telemetry = getattr(exc, "agy_telemetry", None) or agy_telemetry
            substitution = getattr(exc, "substitution", None)
            stderr_excerpt = (
                f"hard_timeout fired after {exc.hard_timeout}s: {exc} "
                f"— raise it with --hard-timeout "
                f"(current default {DEFAULT_HARD_TIMEOUT_S}s)"
            )[:500]
            returncode_reason = "runtime timeout raised before a terminal subprocess returncode was available"
        except AgentRuntimeError as exc:
            agy_telemetry = getattr(exc, "agy_telemetry", None) or agy_telemetry
            worker_exception = _exception_cause("worker_runtime_error", exc)
            stderr_excerpt = f"runtime error: {type(exc).__name__}: {exc}"[:500]
            returncode_reason = "runtime exception did not expose a terminal subprocess returncode"
        except bounded_advisory.AdvisoryRefused as exc:
            pre_spawn_failure = True
            advisory_handoff_refusal = exc.code
            failure_cause = exc.code
            stderr_excerpt = f"worker refused at the provider handoff: {exc}"[:500]
            returncode_reason = (
                "bounded model failed its advisory admission at the provider handoff; provider not started"
            )
        except ValueError as exc:
            agy_telemetry = getattr(exc, "agy_telemetry", None) or agy_telemetry
            pre_spawn_failure = True
            worker_exception = _exception_cause("adapter_rejected", exc)
            stderr_excerpt = f"adapter rejected before spawn: {exc}"[:500]
            returncode_reason = "adapter rejected the dispatch before a process was spawned"
        except Exception as exc:
            # Last-ditch: don't crash the worker on an unexpected bug — we
            # need to update the state file or the parent will see us as
            # "crashed" forever.
            worker_exception = _exception_cause("worker_unexpected_error", exc)
            stderr_excerpt = f"worker unexpected: {type(exc).__name__}: {exc}"[:500]
            returncode_reason = "unexpected worker exception before a terminal subprocess returncode was available"
        finally:
            if cursor_mcp_path is not None:
                try:
                    if cursor_mcp_existed and cursor_mcp_backup is not None:
                        cursor_mcp_path.write_bytes(cursor_mcp_backup)
                    elif not cursor_mcp_existed and cursor_mcp_path.is_file():
                        cursor_mcp_path.unlink()
                except OSError as exc:
                    print(f"⚠️  failed to restore {cursor_mcp_path}: {exc}", file=sys.stderr)
            if runtime_tmp_root is not None or runtime_tmp_namespace_root is not None:
                # This cleanup runs AFTER the worker has finished but BEFORE the
                # guarded span below, and it catches Exception rather than the
                # KeyboardInterrupt a SIGTERM raises — so a cancel landing here used
                # to unwind out of _run_worker with no terminal status written.
                # Deferring the signal across the cleanup drops a cancel that has
                # nothing left to cancel (the work is already done) in exchange for
                # never losing the record that it was done. (Cross-family review of
                # #5807.) Cleanup stays in `finally` so an interrupt during the
                # runtime call itself still frees the lease.
                with _sigterm_deferred():
                    runtime_tmp_reap = _reap_runtime_tmp_lease(
                        runtime_tmp_root,
                        runtime_tmp_namespace_root,
                        task_record=final_state,
                        response=response,
                    )
                    final_state.update(runtime_tmp_reap)

        duration_s = time.monotonic() - start
        final_status = _classify_final_status(
            cancelled=cancelled,
            rate_limited=rate_limited,
            ok_outcome=ok_outcome,
            timed_out=timed_out,
        )

        # A successful runtime result must carry the completed child process's
        # return code.  Refuse to persist a misleading ``done``/null combination
        # if a future runner regression drops it; failures without a child code
        # retain a precise reason instead of inventing a number (#4837).
        if _apply_returncode_invariant(final_status, returncode) != final_status:
            final_status = _apply_returncode_invariant(final_status, returncode)
            ok_outcome = False
            returncode_reason = "runtime reported success without a terminal subprocess returncode"
            stderr_excerpt = "runtime reported success without a terminal subprocess returncode"
            failure_cause = "runtime_returncode_missing"
        elif returncode is None and returncode_reason is None:
            returncode_reason = "no terminal subprocess returncode was available"
        if returncode is not None and returncode < 0 and returncode_reason is None:
            # Python reports signal deaths as negative returncodes. Decode the
            # signal so a SIGKILLed worker persists as SIGKILL, not an opaque
            # -9 (#7124).
            signum = -returncode
            try:
                signal_name = signal.Signals(signum).name
            except ValueError:
                signal_name = f"signal {signum}"
            returncode_reason = f"worker subprocess terminated by {signal_name} (returncode {returncode})"

        final_state = _read_state(state_path) or {}
        # #9275: gate evidence is this run's measurement, never an earlier record's.
        for gate_key in _ADVISORY_GATE_KEYS:
            final_state.pop(gate_key, None)
        final_state["require_review_verdict"] = require_review_verdict
        final_state["review_verdict_failure"] = None
        # The runtime's typed failure class, e.g. a provider policy refusal (#9532).
        final_state.pop("failure_code", None)
        if runtime_failure_code and not ok_outcome:
            final_state["failure_code"] = runtime_failure_code
        if advisory_prompt_sha256 is not None:
            final_state["advisory_prompt_sha256"] = advisory_prompt_sha256
        if advisory_handoff_refusal is not None:
            final_state["failure_reason"] = advisory_handoff_refusal
        if strict_mcp_config:
            final_state["worktree_disallow_reuse"] = True

        # A headless worker that ended its turn while its own background jobs
        # still run has not finished (#8991): record them before anything
        # reads the worktree, so no finalize step treats it as settled. A scan
        # that could not prove nothing is left counts the same way.
        if not pre_spawn_failure:
            leftovers_scan = _background_jobs_at_exit(final_state, task_id=task_id)
        if leftovers_scan is not None:
            final_state.update(leftovers_scan.record_fields())
            leftovers_unconfirmed = leftovers_scan.unconfirmed

        if (
            strict_mcp_config
            and review_id is not None
            and attempt_id is not None
            and mcp_config_path is not None
            and agent == "agy"
        ):
            from scripts.agent_runtime.review_mcp import agy_oauth_link_problem

            link_problem = agy_oauth_link_problem(mcp_config_path)
            if link_problem is not None:
                # Never copy credentials back automatically: both files stay as they
                # are for the operator, and the attempt cannot settle as done (#8617).
                final_state["agy_oauth_link_error"] = "agy_oauth_link_replaced"
                stderr_excerpt = f"agy_oauth_link_replaced: {link_problem}\n{stderr_excerpt or ''}".strip()[:500]
                final_status = "failed"
                ok_outcome = False

        if mode == "read-only":
            read_only_checkout_post, post_snapshot_error = _read_only_checkout_snapshot(cwd)
            task_records_post, task_records_error = _read_only_task_record_snapshot(task_id, task_records_pre)
            if task_records_snapshot_error is None:
                task_records_snapshot_error = task_records_error
            if post_snapshot_error is None:
                post_snapshot_error = task_records_error
            _write_read_only_snapshot_sidecar(task_id, "post", read_only_checkout_post)
            if read_only_snapshot_error is None and post_snapshot_error is not None:
                read_only_snapshot_error = post_snapshot_error
            final_state["read_only_checkout_snapshot_error"] = read_only_snapshot_error
            if read_only_checkout_pre is not None and read_only_checkout_post is not None:
                read_only_ignored_mutation_paths = _read_only_ignored_mutation_paths(
                    read_only_checkout_pre,
                    read_only_checkout_post,
                )
                read_only_mutation_paths = _read_only_mutation_paths(
                    read_only_checkout_pre,
                    read_only_checkout_post,
                )
            if task_records_pre is not None and task_records_post is not None:
                read_only_mutation_paths = sorted(
                    set(read_only_mutation_paths)
                    | {
                        path
                        for path, fingerprint in task_records_post.items()
                        if fingerprint[0] != task_records_pre[path][0]
                    }
                )
            final_state["read_only_ignored_mutation_paths"] = read_only_ignored_mutation_paths
            final_state["read_only_mutation_paths"] = read_only_mutation_paths
            if read_only_snapshot_keep_full(read_only_mutation_paths, read_only_snapshot_error):
                final_state["read_only_snapshot_retention"] = _READ_ONLY_SNAPSHOT_RETENTION_FULL
            else:
                snapshot_dir = _read_only_snapshot_dir_for(task_id)
                stage_read_only_snapshot_digest(
                    snapshot_dir,
                    read_only_checkout_pre,
                    read_only_checkout_post,
                )
                final_state["read_only_snapshot_retention"] = _READ_ONLY_SNAPSHOT_RETENTION_DIGEST
                # Drop hydrated copies so the terminal record stays small even
                # while the phase files are still on disk.
                final_state.pop("read_only_checkout_pre", None)
                final_state.pop("read_only_checkout_post", None)
                clean_snapshots_to_discard = snapshot_dir
            if (
                read_only_mutation_paths
                or task_records_snapshot_error
                or (read_only_snapshot_error or "").startswith("linked database snapshot failed:")
            ):
                final_status = "failed"
                ok_outcome = False

        # Write the full response to a result file (may be large).
        if response:
            result_path = state_path.with_suffix(".result")
            try:
                result_path.write_text(response, encoding="utf-8")
                result_file = str(result_path)
            except OSError:
                result_file = None
            # #9275: an advisor's result is sealed as written, with the model this
            # worker ran, so admission refuses a result replaced after finish.
            if result_file is not None and final_state.get("advisory_role") is not None:
                final_state[bounded_advisory.SEAL_FIELD] = bounded_advisory.seal_advisor_result(
                    response, model=model, run_nonce=final_state.get("run_nonce")
                )

        # Fix 5 (#1476 AC 5): dispatch-finish telemetry — record whether the
        # worktree exited dirty so follow-up reviewers can see at a glance
        # that the dispatched agent left uncommitted changes behind.
        # Ownership is fixed at launch: only a worktree_path recorded with an
        # explicit ``worktree_reused: false`` was created by this dispatch. A
        # path derived from cwd below, or a legacy record without the flag,
        # has unknown ownership and settle will not remove it (#8610).
        reused_flag = final_state.get("worktree_reused")
        worktree_created_by_dispatch = (
            (reused_flag is False) if worktree_path and isinstance(reused_flag, bool) else None
        )
        if not worktree_path and final_state.get("cwd"):
            candidate_cwd = Path(final_state.get("cwd"))
            resolved_wt = _resolve_verified_worktree_path(candidate_cwd)
            if resolved_wt:
                worktree_path = str(resolved_wt)
                final_state["worktree_path"] = worktree_path

        if worktree_path:
            dirty_on_exit = _worktree_is_dirty(Path(worktree_path))

        # EVERYTHING from here to the state write is telemetry ABOUT a worker that
        # has already finished. None of it may prevent the terminal status from
        # being recorded: a task stuck at ``running`` with a dead pid is worse than
        # a task with unknown telemetry, because no settle-loop can ever wake on it
        # and the operator sees a job that appears to still be working. See the
        # 2026-07-25 incident where a vanished worktree crashed the count and hid a
        # dead dispatch for 52 minutes.
        try:
            # The dirty-worktree safety net must cover EVERY write-capable mode, not just
            # ``danger``. It was gated on ``danger`` alone, so a ``workspace-write``
            # dispatch that left finished work uncommitted settled as ``done`` — a real
            # failure reported as success. On 2026-07-25 three lanes did exactly that
            # (``timeouts-B3``, ``timeouts-B6``, ``timeouts-B4-orig``: dirty worktrees,
            # zero commits, ``status: done``) and 31 files of finished work were one agent
            # restart away from being lost. Detection now runs for the whole write-capable
            # set; the riskier auto-finalize action stays scoped to ``danger``, except for
            # Kimi, whose work delegate always commits after the content check below.
            if worktree_path and mode in _WRITE_CAPABLE_MODES:
                base_branch = str(final_state.get("worktree_base") or "main")
                base_ref = _commit_count_base_ref(Path(worktree_path), base_branch)
                commits_ahead = _count_commits_ahead(
                    Path(worktree_path),
                    base_ref,
                    base_sha=_recorded_base_sha(final_state),
                )
                # Kimi takes only plain text without Ukrainian content: a diff that breaks
                # that is refused before auto-finalize can stage or commit anything.
                if kimi_worker:
                    kimi_refusal_text, kimi_unreadable_cause = _kimi_diff_refusal_detail(
                        Path(worktree_path),
                        base_ref,
                        agent,
                        base_sha=_recorded_base_sha(final_state),
                    )
                    if kimi_refusal_text is not None:
                        # The record names the typed cause; the refusal and git's own error stay local (#9878).
                        kimi_content_refusal, kimi_cause = _kimi_refusal_cause(kimi_refusal_text, kimi_unreadable_cause)
                        _record_diagnostic(task_id, kimi_cause, source="finalize", field="kimi_content_refusal")
                # Fail CLOSED on BOTH unknowns — they are the same bug in two variables.
                #
                # ``_count_commits_ahead`` returns None when it cannot count, and
                # ``commits_ahead == 0`` silently skipped that case, which is how the B4
                # dispatch (commits_ahead=None, dirty_on_exit=True) still reported ``done``.
                #
                # ``_worktree_is_dirty`` can ALSO return None (OSError, or a non-zero
                # ``git status --porcelain``). A bare ``if dirty_on_exit`` treats that unknown
                # as falsy and skips the check entirely — failing OPEN in precisely the way
                # this fix exists to prevent. Caught in cross-family review of #5754, which
                # noted the asymmetry after the count half had been fixed.
                #
                # Neither unknown can prove the work was committed, so either one surfaces
                # the task for finalization rather than letting it settle as ``done``.
                # Earlier pushed commits do not account for dirty continuation
                # work (#10077): every dirty or unknown tree needs finalization.
                # A worker cut off mid-work (#8502) leaves unfinished edits even
                # when it had pushed earlier commits: surface them, never ``done``.
                # Exit 0 does not override the adapter's provider-neutral verdict
                # (#9771): rejected work stays unconfirmed, even after an earlier push.
                run_incomplete = not ok_outcome or _worker_run_incomplete(stderr_excerpt) or leftovers_unconfirmed
                if dirty_on_exit in (True, None):
                    needs_finalize = True

                # Catch committed-but-unpushed write dispatches (#7311):
                # A clean tree with local commits on the dispatch branch has commits_ahead >= 1
                # relative to base_ref (e.g. origin/main), but if those commits were never
                # pushed to the branch's remote tracking ref, the work has not left the machine.
                worktree_branch = final_state.get("worktree_branch")
                if isinstance(worktree_branch, str) and worktree_branch.strip():
                    normalized_branch = worktree_branch.strip()
                    if normalized_branch.startswith("refs/heads/"):
                        normalized_branch = normalized_branch.removeprefix("refs/heads/")
                    if normalized_branch.startswith("origin/"):
                        normalized_branch = normalized_branch.removeprefix("origin/")
                    containment = _load_worktree_containment()
                    if normalized_branch not in containment.PROTECTED_BRANCHES and not (
                        commits_ahead == 0 and dirty_on_exit is False
                    ):
                        unpushed_commits = _count_unpushed_commits(
                            Path(worktree_path),
                            normalized_branch,
                        )
                        if unpushed_commits is None or unpushed_commits > 0:
                            needs_finalize = True
                            if unpushed_commits is not None and unpushed_commits > 0:
                                rescue_status = "unpushed work - needs rescue"
                            elif commits_ahead != 0:
                                rescue_status = "unpushed state unknown - needs rescue"
                            if rescue_status:
                                finalize_error = rescue_status

                if (
                    needs_finalize
                    and rescue_status is None
                    and returncode == 0
                    and (mode == "danger" or kimi_worker)
                    and kimi_content_refusal is None
                    and not run_incomplete
                    and not _advisory_completion_gate_fails(final_state, Path(worktree_path))
                ):
                    if kimi_worker:
                        # The content check passed and the worker has exited: take the
                        # boundary down so delegate's own commit and push go through.
                        from scripts.agent_runtime import kimi_boundary

                        kimi_boundary.remove(Path(worktree_path), env=_sanitized_git_env())
                    from learn_ukrainian_v4_runtime.model_families import is_cursor_auto_selector

                    auto_finalize = _auto_finalize_dirty_worktree(
                        worktree=Path(worktree_path),
                        task_id=task_id,
                        agent=agent,
                        model=(
                            model
                            if agent == "cursor" and is_cursor_auto_selector(model)
                            else getattr(result, "model", None) or model or _lane_default_model(agent)
                        ),
                        branch=final_state.get("worktree_branch"),
                        base_branch=base_branch,
                        open_pr=finalize_open_pr,
                        owned_paths=final_state.get("owned_paths"),
                    )
                    dirty_on_exit = _worktree_is_dirty(Path(worktree_path))
                    commits_ahead = _count_commits_ahead(
                        Path(worktree_path), base_ref, base_sha=_recorded_base_sha(final_state)
                    )
                    if auto_finalize.ok and not auto_finalize.skipped_paths:
                        needs_finalize = False
                        ok_outcome = True
                        final_status = "done"
                    elif auto_finalize.ok:
                        # Owned work is committed and pushed, but changes outside
                        # the owned paths are still in the tree (finalize_skipped_paths): a human decides.
                        finalize_error = _TypedCause(
                            "finalize_skipped_paths", count=len(auto_finalize.skipped_paths)
                        ).public()
                    elif auto_finalize.error == _NO_DELIVERABLE_JUNK_ONLY_WORKTREE_REASON:
                        # A dirty tree with only known scratch residue has no
                        # user-visible deliverable. Refuse before staging so it
                        # cannot create a branch, push, or public PR.
                        needs_finalize = False
                        no_deliverable = True
                        no_deliverable_reason = _NO_DELIVERABLE_JUNK_ONLY_WORKTREE_REASON
        # Deliberately broad: this is measurement about a worker that has already
        # finished, and no measurement failure may cost the task its terminal status.
        except Exception as finalize_exc:
            # The record names the exception class; its message stays local (#9878).
            finalize_error = _publish_cause(
                task_id, _exception_cause("finalize_failed", finalize_exc), source="finalize", field="finalize_error"
            )
            # Unknown telemetry cannot prove the work was committed, so surface
            # the task for a human instead of settling it as done.
            needs_finalize = True
        # Live background jobs, or a scan that could not rule them out, make any
        # run unconfirmed (#8991), read-only included, even when its tree is
        # clean and pushed: the jobs may still be producing the result.
        if leftovers_unconfirmed:
            needs_finalize = True
        # Either way the verdict is now measured rather than assumed, so an
        # interrupt below must persist it as-is instead of forcing attention
        # onto a dispatch already shown to be clean and committed.
        telemetry_settled = True

        # A write-capable dispatch that settled ``done`` must have SOME
        # verifiable deliverable. The signal is inferred from observable
        # facts — own-branch commits, worktree state, response size — never
        # from a formatting contract on the worker's final message, so a
        # worker needs no magic phrase to count as successful. A structured
        # ``DELIVERABLE:`` line is honoured as an optional positive signal.
        # Read-only tasks are excluded: their deliverable may be analysis or
        # an external side effect such as a posted review comment.
        #
        # A review-typed dispatch (#8421) that settled ``done`` must actually
        # state a verdict. A reviewer that backgrounds its work and replies
        # with a promise to keep waiting exits 0 with an intent-only body; the
        # observable-facts rule above does not cover read-only review tasks, so
        # without this gate the false ``done`` reported success to ask-* review
        # drivers. Opt-in via ``--require-review-verdict`` (the ask-* review
        # wrapper only) — ordinary asks and implement dispatches are unchanged.
        #
        # #9275: a bounded worker's envelope ceilings, and a Ukrainian content
        # exemption's changed paths, are checked on what it changed; a breach, or
        # changes that cannot be measured, is a typed failure, never done.
        #
        # Which gates apply is one definition (``applicable_completion_gates``),
        # shared with every recovery path that can report ``done``.
        gate_record = {**final_state, "mode": mode, "require_review_verdict": require_review_verdict}
        for gate in applicable_completion_gates(gate_record):
            if final_status != "done":
                break
            if gate == COMPLETION_GATE_BACKGROUND_LEFTOVERS:
                continue  # the exit scan above already left this run needs_finalize
            if gate in (COMPLETION_GATE_DELIVERY, COMPLETION_GATE_REVIEW_VERDICT) and (
                returncode != 0 or needs_finalize or no_deliverable_reason is not None
            ):
                continue
            gate_result = run_completion_gate(
                gate,
                gate_record,
                response=response,
                commits_ahead=commits_ahead,
                worktree=Path(worktree_path) if worktree_path else None,
            )
            if gate_result.record_key is not None:
                final_state[gate_result.record_key] = gate_result.check
            if gate == COMPLETION_GATE_DELIVERY:
                delivery_declaration = _parse_delivery_declaration(response)
                no_deliverable_reason = gate_result.failure
                no_deliverable = no_deliverable_reason is not None
            elif gate_result.failure is None:
                continue
            elif gate == COMPLETION_GATE_REVIEW_VERDICT:
                final_state["review_verdict_failure"] = gate_result.failure
                final_status = "failed"
                ok_outcome = False
                stderr_excerpt = gate_result.failure
                failure_cause = gate_result.failure
            else:
                final_state["failure_reason"] = gate_result.failure
                final_status = "failed"
                ok_outcome = False
                needs_finalize = False
                failure_cause = gate_result.failure
                message = f"{gate_result.failure}: {gate_result.detail}"
                stderr_excerpt = f"{message}\n{stderr_excerpt}" if stderr_excerpt else message

        if pre_spawn_failure:
            needs_finalize = False
            final_status = "failed"
            ok_outcome = False
        elif kimi_content_refusal:
            # Nothing was committed for the worker; its changes stay in the tree.
            needs_finalize = False
            final_status = "failed"
            ok_outcome = False
            final_state["kimi_content_refusal"] = kimi_content_refusal
            failure_cause = kimi_content_refusal
            stderr_excerpt = f"{kimi_refusal_text}\n{stderr_excerpt}" if stderr_excerpt else kimi_refusal_text
        elif needs_finalize:
            final_status = "needs_finalize"
        elif no_deliverable:
            final_status = _NO_DELIVERABLE_STATUS
            ok_outcome = False
        # Every completion gate has run and the outcome is final: from here an
        # interrupt persists it with its gate evidence, as the checkpoint would.
        completion_gates_settled = True

        # last_error is a public cause (#9878): the stderr line it summarizes stays in stderr_excerpt and the .diag.
        last_error = _worker_last_error(
            task_id,
            stderr_excerpt=stderr_excerpt if final_status != "done" else None,
            failure_cause=failure_cause,
            final_status=final_status,
            returncode=returncode,
            runtime_failure_code=runtime_failure_code,
            worker_exception=worker_exception,
        )
        if leftovers_scan is not None and leftovers_scan.reason and final_status == "needs_finalize":
            reason = leftovers_scan.reason
            last_error = f"{reason}; {last_error}" if last_error else reason
        if read_only_mutation_paths:
            mutation_diagnostic = "read-only checkout mutation detected: " + ", ".join(read_only_mutation_paths)
            db_mutations = [p for p in read_only_mutation_paths if p in ("data/sources.db", "data/vesum.db")]
            if db_mutations:
                primary_root = _resolve_primary_root_for_worktree(Path(cwd))
                remedies = []
                for p in db_mutations:
                    name = "sources.db" if p == "data/sources.db" else "vesum.db"
                    target = _primary_database_path(primary_root, name)
                    remedies.append(_primary_database_connect_code(target))
                mutation_diagnostic += (
                    f" (databases do not reside in sparse worktrees; ad-hoc queries must open the "
                    f"primary database read-only by absolute path: {'; '.join(remedies)})"
                )
            # Never REPLACE a real failure with the guard diagnostic (#7124):
            # overwriting it hid the actual cause (e.g. a SIGKILLed worker's
            # stderr) behind the mutation list. The paths stay independently
            # queryable via ``read_only_mutation_paths`` either way.
            mutation = _publish_cause(
                task_id,
                _TypedCause(
                    "read_only_checkout_mutation", count=len(read_only_mutation_paths), diagnostic=mutation_diagnostic
                ),
                source="worker",
                field="last_error",
            )
            last_error = f"{last_error}; {mutation}" if last_error else mutation
        if task_records_snapshot_error:
            snapshot = _publish_cause(
                task_id,
                _TypedCause("task_records_snapshot_failed", diagnostic=task_records_snapshot_error),
                source="worker",
                field="last_error",
            )
            last_error = f"{last_error}; {snapshot}" if last_error else snapshot
        elif (read_only_snapshot_error or "").startswith("linked database snapshot failed:"):
            snapshot = _publish_cause(
                task_id,
                _TypedCause("read_only_checkout_snapshot_failed", diagnostic=read_only_snapshot_error),
                source="worker",
                field="last_error",
            )
            last_error = f"{last_error}; {snapshot}" if last_error else snapshot
        if no_deliverable_reason is not None:
            last_error = no_deliverable_reason

        # CHECKPOINT: persist the COMPLETE core outcome before any best-effort work.
        #
        # Everything below — worktree reaping, usage extraction, the enriched state
        # assembly — is enrichment, and any of it can raise: worktree reaping once
        # performed its import outside its own handler, so an unimportable reaper
        # module skipped the write entirely and stood the task back up as ``running``
        # with a dead pid. Ordering fixes that by construction, where wrapping each
        # statement would only hold until someone adds the next one.
        #
        # The checkpoint carries every field that defines the outcome, not just the
        # status: a watcher that sees ``done`` must not find null ``finished_at`` /
        # ``duration_s`` / ``result_file`` / ``returncode`` next to it, and if this
        # process dies mid-enrichment the surviving record must still be complete
        # and true. Only genuinely optional metadata (reap telemetry, usage record,
        # runtime model/effort/cli labels) is left to the second write.
        # (Both points from cross-family review of this PR.)
        core_terminal_state = _core_terminal_fields(
            status=final_status,
            duration_s=duration_s,
            response=response,
            result_file=result_file,
            stderr_excerpt=stderr_excerpt,
            returncode=returncode,
            returncode_reason=returncode_reason,
            dirty_on_exit=dirty_on_exit,
            commits_ahead=commits_ahead,
            needs_finalize=needs_finalize,
            finalize_error=finalize_error,
            last_error=last_error,
        )
        if isinstance(agy_telemetry, AgyTelemetry):
            core_terminal_state.update(agy_telemetry.task_fields())
        final_state["final_branch_head_commit"] = _resolve_sha(Path(worktree_path)) if worktree_path else None
        final_state["rescue_status"] = rescue_status
        _write_state_atomic(state_path, {**final_state, **core_terminal_state})
        if clean_snapshots_to_discard is not None:
            discard_read_only_snapshot_phases(clean_snapshots_to_discard)
            clean_snapshots_to_discard = None
    except BaseException as interrupt_exc:
        # Defer SIGTERM across the ENTIRE handler, not just its write. A second
        # cancel arriving while the fallback was still computing raised from
        # inside this `except` suite, which the same suite cannot catch — the
        # same boundary-between-guarded-spans mistake as the region itself, one
        # level down. (Cross-family review of #5807, round nine.)
        with _sigterm_deferred():
            # Honour a verdict the telemetry already reached; fail closed only
            # when the interrupt beat the measurement to it — and only for modes
            # that can leave work behind, so an interrupted read-only review is
            # not dressed up as a dispatch needing manual finalization — unless
            # its own background jobs may still be running (#8991).
            interrupted_needs_finalize = (
                needs_finalize if telemetry_settled else (mode in _WRITE_CAPABLE_MODES or leftovers_unconfirmed)
            )
            # The interrupt may have landed before classification ran, so derive
            # the outcome from the runtime flags rather than persisting an empty
            # status, and apply the same return-code invariant the normal path
            # enforces.
            interrupted_status = _apply_returncode_invariant(
                final_status
                or _classify_final_status(
                    cancelled=cancelled,
                    rate_limited=rate_limited,
                    ok_outcome=ok_outcome,
                    timed_out=timed_out,
                ),
                returncode,
            )
            interrupted_gate_error: str | None = None
            if interrupted_status == "done" and not completion_gates_settled:
                # #9275: success needs every applicable completion gate run on the
                # current tree. A write dispatch interrupted before that boundary is
                # left for finalization; a read-only one is a typed failure.
                interrupted_gate_error = _INTERRUPTED_BEFORE_COMPLETION_GATES
                if mode in _WRITE_CAPABLE_MODES:
                    interrupted_needs_finalize = True
                else:
                    interrupted_status = "failed"
            if interrupted_needs_finalize:
                interrupted_status = "needs_finalize"
            _write_state_atomic(
                state_path,
                {
                    # final_state was read before the region, so this MERGES onto
                    # the real task record instead of replacing it...
                    **final_state,
                    "final_branch_head_commit": _resolve_sha(Path(worktree_path)) if worktree_path else None,
                    "rescue_status": rescue_status,
                    # ...and the outcome fields come from the same builder the
                    # checkpoint uses, so an interrupted run never persists a
                    # terminal status beside stale placeholder values.
                    **_core_terminal_fields(
                        status=interrupted_status,
                        duration_s=duration_s,
                        response=response,
                        result_file=result_file,
                        stderr_excerpt=stderr_excerpt,
                        returncode=returncode,
                        returncode_reason=returncode_reason,
                        dirty_on_exit=dirty_on_exit,
                        commits_ahead=commits_ahead,
                        needs_finalize=interrupted_needs_finalize,
                        finalize_error=_exception_cause("interrupted_during_finalize", interrupt_exc).public(),
                        last_error=(
                            no_deliverable_reason
                            or interrupted_gate_error
                            or _worker_last_error(
                                None,
                                stderr_excerpt=stderr_excerpt if interrupted_status != "done" else None,
                                failure_cause=failure_cause,
                                final_status=interrupted_status,
                                returncode=returncode,
                                runtime_failure_code=runtime_failure_code,
                                worker_exception=worker_exception,
                            )
                        ),
                    ),
                },
            )
            if clean_snapshots_to_discard is not None:
                discard_read_only_snapshot_phases(clean_snapshots_to_discard)
                clean_snapshots_to_discard = None
        raise

    last_error = _first_error_line(stderr_excerpt) if final_status != "done" else None
    if no_deliverable_reason is not None:
        last_error = no_deliverable_reason
    if last_error:
        # Task logs capture this worker's stderr, while agent_runtime captures
        # the CLI child's stderr internally. Re-emit the excerpt so an
        # instant CLI failure is visible in both task state and its stderr log.
        print(stderr_excerpt, file=sys.stderr, flush=True)

    # Read-only checkout snapshots (read_only_checkout_pre/post) already ran
    # above. Reap only after that comparison.
    worktree_reap: dict[str, Any] | None = None
    if worktree_path and _should_reap_settled_worktree(
        mode=mode,
        keep_worktree=keep_worktree,
        final_status=final_status,
        returncode=returncode,
        dirty_on_exit=dirty_on_exit,
    ):
        worktree_reap = _settle_worktree_reap(
            Path(worktree_path),
            created_by_this_dispatch=worktree_created_by_dispatch,
            settling_task_id=task_id,
            task_record=final_state,
        )

    usage_record = getattr(result, "usage_record", None)
    result_substitution = getattr(result, "substitution", None)
    if result_substitution is not None:
        substitution = result_substitution
    if substitution is None and isinstance(usage_record, dict):
        substitution = usage_record.get("substitution")
    runtime_substitution = substitution
    substitution = _merge_agent_substitution(final_state.get("substitution"), runtime_substitution)
    cursor_model_state = _cursor_model_state(
        agent=agent,
        result=result,
        substitution=runtime_substitution if isinstance(runtime_substitution, dict) else None,
    )

    final_state.update(
        {
            # The core outcome was already checkpointed above; re-stating it here
            # keeps this write self-contained and idempotent — same values, so a
            # reader between the two writes never sees the status change.
            **core_terminal_state,
            "model": getattr(result, "model", final_state.get("model")),
            **cursor_model_state,
            **_deepseek_model_state(
                agent=agent,
                model=getattr(result, "model", final_state.get("model")),
            ),
            "effort": getattr(result, "effort", final_state.get("effort")),
            "cli_version": getattr(result, "cli_version", final_state.get("cli_version")),
            "substitution": substitution,
            "no_deliverable_reason": no_deliverable_reason,
            "sources_mcp_call_count": _sources_mcp_call_count(result),
            "delivery_declaration": delivery_declaration,
            "keep_worktree": keep_worktree,
            "worktree_reap": worktree_reap,
            "tmp_bytes_freed": (
                runtime_tmp_reap["tmp_bytes_freed"]
                if runtime_tmp_reap is not None
                else final_state.get("tmp_bytes_freed")
            ),
            "tmp_reap_error": (
                runtime_tmp_reap["tmp_reap_error"]
                if runtime_tmp_reap is not None
                else final_state.get("tmp_reap_error")
            ),
            "auto_finalize": (
                {
                    "ok": auto_finalize.ok,
                    "commit_sha": auto_finalize.commit_sha,
                    "pr_url": auto_finalize.pr_url,
                    "error": auto_finalize.error,
                    "changed_files": list(auto_finalize.changed_files),
                    "owned_paths": (list(auto_finalize.owned_paths) if auto_finalize.owned_paths is not None else None),
                    "owned_paths_declared": auto_finalize.owned_paths is not None,
                    "cross_boundary_moves": list(auto_finalize.cross_boundary_moves),
                }
                if auto_finalize is not None
                else None
            ),
        }
    )
    if auto_finalize is not None:
        final_state["finalize_skipped_paths"] = list(auto_finalize.skipped_paths)
    _write_state_atomic(state_path, final_state)
    if worktree_path:
        print(
            f"[delegate] final branch={final_state.get('worktree_branch')} "
            f"head={final_state.get('final_branch_head_commit') or 'unknown'} "
            f"rescue_status={final_state.get('rescue_status') or 'none'}",
            file=sys.stderr,
        )
    _emit_terminal_dispatch_event(
        task_id=task_id,
        agent=agent,
        final_state=final_state,
        result=result,
        fallback_prompt_chars=len(prompt),
    )

    # Post-worker primary-integrity sweep (#5803 follow-up): if THIS worker
    # touched the primary checkout, the drift is caught here while its
    # task_id/agent/pid are still known, so the drift event names the likely
    # actor. Diagnostic only: never switches the human's checkout. Runs after
    # final_state is persisted.
    try:
        try:
            from scripts.audit.check_primary_integrity import check_primary_integrity
        except ImportError:  # path-flavoured import for test/script contexts
            from audit.check_primary_integrity import check_primary_integrity

        pi_ok, pi_message = check_primary_integrity(_REPO_ROOT, fix=False, tasks_dir=tasks_dir())
        if not pi_ok:
            _append_dispatch_event(
                "primary_integrity_post_worker",
                task_id=task_id,
                agent=agent,
                ok=pi_ok,
                detail=pi_message,
            )
    except Exception as pi_exc:
        print(
            f"[delegate] WARNING: primary-integrity post-worker sweep failed: {type(pi_exc).__name__}: {pi_exc}",
            file=sys.stderr,
        )

    # Post-worker node_modules-integrity sweep (#6818 follow-up): same shape
    # as the primary-integrity sweep above, but for the symlink conduit
    # `_provision_data_symlinks` opens into every worktree's node_modules.
    # ALERT-only — never blocks, never repairs; attributes this worker's
    # task_id/agent/pid while they're still known.
    try:
        try:
            from scripts.audit.check_node_modules_integrity import (
                check_node_modules_integrity,
            )
        except ImportError:  # path-flavoured import for test/script contexts
            from audit.check_node_modules_integrity import check_node_modules_integrity

        nmi_ok, nmi_message = check_node_modules_integrity(_REPO_ROOT, tasks_dir=tasks_dir())
        if not nmi_ok:
            _append_dispatch_event(
                "node_modules_integrity_post_worker",
                task_id=task_id,
                agent=agent,
                ok=nmi_ok,
                detail=nmi_message,
            )
    except Exception as nmi_exc:
        print(
            f"[delegate] WARNING: node_modules-integrity post-worker sweep failed: {type(nmi_exc).__name__}: {nmi_exc}",
            file=sys.stderr,
        )

    # Post-worker venv-integrity sweep (#6830 follow-up): same shape as the
    # node_modules-integrity sweep above, but for an empty/broken primary
    # venv. ALERT-only — never blocks, never repairs; attributes this
    # worker's task_id/agent/pid while they're still known.
    try:
        try:
            from scripts.audit.check_venv_integrity import check_venv_integrity
        except ImportError:  # path-flavoured import for test/script contexts
            from audit.check_venv_integrity import check_venv_integrity

        vi_ok, vi_message = check_venv_integrity(_REPO_ROOT, tasks_dir=tasks_dir())
        if not vi_ok:
            _append_dispatch_event(
                "venv_integrity_post_worker",
                task_id=task_id,
                agent=agent,
                ok=vi_ok,
                detail=vi_message,
            )
    except Exception as vi_exc:
        print(
            f"[delegate] WARNING: venv-integrity post-worker sweep failed: {type(vi_exc).__name__}: {vi_exc}",
            file=sys.stderr,
        )

    # Post-worker worktree-cleanup-integrity sweep (#6937 follow-up): same
    # shape as the venv-integrity sweep above, but for a dark/red scheduled
    # LaunchAgent. ALERT-only — never blocks, never reloads launchd.
    try:
        try:
            from scripts.audit.check_worktree_cleanup_integrity import (
                check_worktree_cleanup_integrity,
            )
        except ImportError:  # path-flavoured import for test/script contexts
            from audit.check_worktree_cleanup_integrity import (
                check_worktree_cleanup_integrity,
            )

        wci_ok, wci_message = check_worktree_cleanup_integrity(_REPO_ROOT, tasks_dir=tasks_dir())
        if not wci_ok:
            _append_dispatch_event(
                "worktree_cleanup_integrity_post_worker",
                task_id=task_id,
                agent=agent,
                ok=wci_ok,
                detail=wci_message,
            )
    except Exception as wci_exc:
        print(
            f"[delegate] WARNING: worktree-cleanup-integrity post-worker sweep failed: "
            f"{type(wci_exc).__name__}: {wci_exc}",
            file=sys.stderr,
        )

    if timed_out:
        _append_dispatch_event(
            "dispatch_silence_timeout",
            task_id=task_id,
            agent=agent,
            model=final_state.get("model"),
            effort=final_state.get("effort"),
            cwd=str(cwd),
            pid=final_state.get("pid"),
            status=final_status,
            silence_timeout_s=silence_timeout,
            hard_timeout_s=hard_timeout,
            max_budget_usd=max_budget_usd,
            duration_s=round(duration_s, 3),
            stderr_excerpt=stderr_excerpt,
        )

    return 0 if ok_outcome and not needs_finalize and not no_deliverable else 1


def _record_worktree_prep_failure(
    *,
    task_id: str,
    run_nonce: str,
    attribution: Any,
    agent: str,
    mode: str,
    prompt: str,
    error: Exception | str,
    requested_model: str | None = None,
    requested_effort: str | None = None,
    requested_harness: str | None = None,
    lifecycle_carrier: Any = None,
    worktree_path: str | Path | None = None,
    worktree_branch: str | None = None,
    worktree_base_sha: str | None = None,
    worktree_base: str | None = None,
    agent_alias_note: str | None = None,
    output_schema_path: str | None = None,
    output_schema_sha256: str | None = None,
    keep_worktree: bool = False,
    hard_timeout: float | None = None,
    silence_timeout: float | None = None,
    initial_response_timeout: float | None = None,
    max_budget_usd: float | None = None,
    require_review_verdict: bool = False,
    returncode_reason: str = "worktree preparation failed",
    worktree_prep_cleanup: dict[str, Any] | None = None,
    worktree_prep: dict[str, Any] | None = None,
    substitution: dict[str, Any] | None = None,
) -> bool:
    """Persist a terminal failed task record when worktree provisioning is refused.

    Returns True when a record was written. Refuses to overwrite an existing
    running/spawning record (pre-write re-check closes the guard→write race),
    except this run's own admission hold or path-reservation record, whose
    admission snapshot it keeps. ``worktree_prep`` is that
    reservation and ``worktree_prep_cleanup`` what dispatch found and did
    after a failed ``git worktree add`` (#8663); each is recorded when given.
    """
    if str(_REPO_ROOT / "scripts") not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT / "scripts"))
    from agent_runtime.telemetry import resolve_dispatch_start_telemetry

    start_telemetry = resolve_dispatch_start_telemetry(
        agent_name=agent,
        requested_model=requested_model,
        requested_effort=requested_effort,
        harness=requested_harness,
    )
    now_iso = datetime.now(UTC).isoformat()
    error_str = str(error)
    wt_path_str = str(worktree_path) if worktree_path else None
    wt_layout = _classify_worktree_layout(Path(worktree_path)) if worktree_path else None
    failed_state: dict[str, Any] = {
        "task_id": task_id,
        "run_nonce": run_nonce,
        "repository": _resolve_dispatch_repository(_REPO_ROOT),
        "initiator": attribution.initiator,
        "attribution_source": attribution.source,
        "agent": agent,
        "model": start_telemetry.model,
        **_cursor_model_state(agent=agent, initial=True),
        **_deepseek_model_state(agent=agent, model=start_telemetry.model),
        "effort": start_telemetry.effort,
        "cli_version": start_telemetry.cli_version,
        "allow_merge": False,
        "require_review_verdict": require_review_verdict,
        "mode": mode,
        "cwd": wt_path_str or str(_REPO_ROOT),
        "worktree_path": wt_path_str,
        "worktree_branch": worktree_branch,
        "final_branch_head_commit": _resolve_sha(Path(worktree_path)) if worktree_path else None,
        "worktree_base_sha": worktree_base_sha,
        "worktree_base": worktree_base,
        "worktree_rebased": False,
        "worktree_reused": False,
        "worktree_layout": wt_layout,
        "worktree_sparse": None,
        "worktree_local_venv": None,
        "runtime_tmp_root": None,
        "tmp_bytes_freed": None,
        "tmp_reap_error": None,
        "keep_worktree": keep_worktree,
        "hard_timeout": hard_timeout,
        "silence_timeout": silence_timeout,
        "initial_response_timeout": initial_response_timeout,
        "max_budget_usd": max_budget_usd,
        "output_schema_path": output_schema_path,
        "output_schema_sha256": output_schema_sha256,
        "pid": None,
        "status": "failed",
        "started_at": now_iso,
        "finished_at": now_iso,
        "duration_s": 0.0,
        "prompt_chars": len(prompt) if prompt else 0,
        "response_chars": None,
        "result_file": None,
        "stderr_excerpt": f"{returncode_reason}: {error_str}"[:500],
        "returncode": None,
        "returncode_reason": returncode_reason,
        # A typed cause: the record writer renders it public and keeps the error text in the .diag (#9878).
        "last_error": _TypedCause(
            _DISPATCH_FAILURE_CAUSES.get(returncode_reason, "dispatch_not_started"),
            error=_exception_cause(UNCLASSIFIED_CAUSE, error).error if isinstance(error, BaseException) else None,
            diagnostic=error_str,
        ),
        "exit_code": None,
        "substitution": substitution,
        "agent_alias_note": agent_alias_note,
    }
    if requested_harness is not None:
        failed_state["harness"] = requested_harness
    if lifecycle_carrier is not None:
        failed_state["task_lifecycle"] = lifecycle_carrier
    if worktree_prep is not None:
        failed_state["worktree_prep"] = worktree_prep
    if worktree_prep_cleanup is not None:
        failed_state["worktree_prep_cleanup"] = worktree_prep_cleanup
    state_path = _state_path(task_id)
    existing = _read_state(state_path)
    if existing is not None and existing.get("status") in ("running", "spawning"):
        if not _is_own_provisional_record(existing, run_nonce):
            return False
        if isinstance(existing.get("admission"), dict):
            failed_state["admission"] = existing["admission"]
    _write_state_atomic(state_path, failed_state)
    return True


_DISPATCH_FAILURE_CAUSES = {
    "worktree preparation failed": "worktree_preparation_failed",
    "forward configuration failed": "forward_configuration_failed",
}


def _record_forward_failure(
    *,
    task_id: str,
    run_nonce: str,
    attribution: Any,
    agent: str,
    mode: str,
    prompt: str,
    error: Exception | str,
    requested_model: str | None = None,
    requested_effort: str | None = None,
    requested_harness: str | None = None,
    lifecycle_carrier: Any = None,
    worktree_path: str | Path | None = None,
    worktree_branch: str | None = None,
    worktree_base_sha: str | None = None,
    worktree_base: str | None = None,
    agent_alias_note: str | None = None,
    output_schema_path: str | None = None,
    output_schema_sha256: str | None = None,
    keep_worktree: bool = False,
    hard_timeout: float | None = None,
    silence_timeout: float | None = None,
    initial_response_timeout: float | None = None,
    max_budget_usd: float | None = None,
    require_review_verdict: bool = False,
    substitution: dict[str, Any] | None = None,
) -> bool:
    """Persist a terminal failed task record when VPS forward dispatch is refused."""
    return _record_worktree_prep_failure(
        task_id=task_id,
        run_nonce=run_nonce,
        attribution=attribution,
        agent=agent,
        mode=mode,
        prompt=prompt,
        error=error,
        requested_model=requested_model,
        requested_effort=requested_effort,
        requested_harness=requested_harness,
        lifecycle_carrier=lifecycle_carrier,
        worktree_path=worktree_path,
        worktree_branch=worktree_branch,
        worktree_base_sha=worktree_base_sha,
        worktree_base=worktree_base,
        agent_alias_note=agent_alias_note,
        output_schema_path=output_schema_path,
        output_schema_sha256=output_schema_sha256,
        keep_worktree=keep_worktree,
        hard_timeout=hard_timeout,
        silence_timeout=silence_timeout,
        initial_response_timeout=initial_response_timeout,
        max_budget_usd=max_budget_usd,
        require_review_verdict=require_review_verdict,
        returncode_reason="forward configuration failed",
        substitution=substitution,
    )


# ---------------------------------------------------------------------------
# Dispatch command — spawn detached worker
# ---------------------------------------------------------------------------


def _run_preflight_triage(args: argparse.Namespace, *, worktree_arg: str | None) -> int | None:
    """#8183: TypeSafe readiness triage before any worker is spawned.

    Returns the fast-fail exit code, or ``None`` to let dispatch proceed
    (pass, missing key, API/git failure — advisory, never blocks).
    """
    from scripts.typesafe import preflight_triage as pt

    if args.cwd:
        cwd = Path(args.cwd)
    elif worktree_arg and worktree_arg != "auto" and Path(worktree_arg).is_dir():
        cwd = Path(worktree_arg)
    else:
        cwd = Path.cwd()
    try:
        paths, diff = pt.collect_candidate(getattr(args, "preflight_base", None) or "origin/main", cwd)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"preflight-triage: could not resolve git diff ({type(exc).__name__}) — skipping.", file=sys.stderr)
        return None
    log_arg = getattr(args, "preflight_test_log", None)
    log_path = Path(log_arg) if log_arg else cwd / ".preflight-test.log"
    result = pt.run_preflight(paths, diff, pt.read_test_log(log_path), pt.load_api_key())
    print(result.message, file=sys.stderr)
    if not result.fast_fail:
        return None
    pt.record_fast_fail(args.task_id, result, tasks_dir().parent / "preflight_fast_fail.jsonl")
    return pt.FAST_FAIL_EXIT_CODE


# The short form rejects common file suffixes so source locations do not become issue repositories.
_DOR_ISSUE_RE = re.compile(
    r"(?<![\w/=])(?:"
    r"https://github\.com/(?P<url_repo>[\w.-]+/[\w.-]+)/issues/(?P<url_number>\d+)\b"
    r"|(?P<short_repo>[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})/"
    r"(?!(?:[A-Za-z0-9._-]+\.(?i:md|markdown|py|pyi|rst|txt))#)"
    r"(?=[A-Za-z0-9._-]*[A-Za-z0-9_-]#)[A-Za-z0-9._-]+)"
    r"#(?P<short_number>\d+)\b(?![/\\])"
    r"|#(?P<number>\d+)\b)"
)


def _registered_stream_epics() -> frozenset[int]:
    """Epic numbers registered for this repository in the stream registry (#9276).

    Uses the registry ``issue_stream_audit`` audits from, including closed and retired epics: an epic
    is never a task card. An unreadable registry yields no exemption, so the check only gets stricter.
    """
    import yaml

    from scripts.orchestration import issue_stream_audit

    try:
        registry = issue_stream_audit.load_registry()
    except (OSError, ValueError, AttributeError, TypeError, yaml.YAMLError):
        return frozenset()
    return frozenset(epic for epics in registry.values() for epic in epics)


def _run_dor_preflight(
    prompt: str, allow_reason: str | None, *, dispatch_repo: str
) -> tuple[str | None, dict[str, Any] | None]:
    """Check each issue named by an implementation brief before dispatch side effects.

    A registered stream epic of this repository is linked context, not a task card (#9276): it is recorded
    as ``stream_epic`` and skipped when the brief also names a task issue, but a brief naming only an epic
    (or an epic and pull requests) is refused as ``dor_epic_only_no_task_issue``, whatever the epic's card
    says and even under ``--allow-dor-warn``. Only ``(this repository, epic number)`` is exempt; a same-numbered issue elsewhere is not.
    """
    distinct: dict[tuple[str, int], tuple[str, int]] = {}
    for match in _DOR_ISSUE_RE.finditer(_strip_quoted_content(prompt)):
        repo = match.group("url_repo") or match.group("short_repo") or dispatch_repo
        if repo.casefold() == _CANONICAL_GITHUB_REPO.casefold():
            repo = _CANONICAL_GITHUB_REPO
        number = int(match.group("url_number") or match.group("short_number") or match.group("number"))
        distinct.setdefault((repo.casefold(), number), (repo, number))
    candidates = sorted(distinct.values(), key=lambda issue: (issue[1], issue[0].casefold()))
    if not candidates:
        return None, None
    epic_numbers = _registered_stream_epics()
    epics = [c for c in candidates if c[0] == _CANONICAL_GITHUB_REPO and c[1] in epic_numbers]
    tasks = [c for c in candidates if c not in epics]
    warnings: dict[str, str] = {}
    issue_numbers: list[int] = []
    checker = _REPO_ROOT / "scripts" / "ci" / "check_issue_task_quality.py"
    issue_repositories: list[dict[str, Any]] = []

    def check(batch: list[tuple[str, int]]) -> None:
        for repo, number in batch:
            label = str(number) if repo.casefold() == _CANONICAL_GITHUB_REPO.casefold() else f"{repo}#{number}"
            recorded = False
            try:
                issue = subprocess.run(
                    ["gh", "api", f"repos/{repo}/issues/{number}"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    check=False,
                )
                if issue.returncode:
                    raise ValueError("issue lookup failed")
                issue_payload = json.loads(issue.stdout)
                if not isinstance(issue_payload, dict) or issue_payload.get("number") != number:
                    raise ValueError("issue lookup must identify the requested number")
                if "pull_request" in issue_payload:
                    continue
                issue_numbers.append(number)
                recorded = True
                if repo.casefold() != _CANONICAL_GITHUB_REPO.casefold():
                    issue_repositories.append({"issue": number, "repo": repo})
                result = subprocess.run(
                    [sys.executable, str(checker), "--issue", str(number), "--repo", repo, "--strict", "--json"],
                    capture_output=True,
                    text=True,
                    timeout=75,
                    check=False,
                )
                payload = json.loads(result.stdout)
                if not isinstance(payload, dict):
                    raise ValueError("checker result must be an object")
                if result.returncode or payload.get("verdict") != "PASS":
                    warnings[label] = ",".join(payload.get("missing") or ["checker_error"])
            except (OSError, subprocess.SubprocessError, json.JSONDecodeError, TypeError, ValueError):
                if not recorded:
                    issue_numbers.append(number)
                    if repo.casefold() != _CANONICAL_GITHUB_REPO.casefold():
                        issue_repositories.append({"issue": number, "repo": repo})
                warnings[label] = "checker_error"

    check(tasks)
    stream_epics: list[int] = []
    if epics:
        if not issue_numbers:
            # No task issue was checked (none named, or all were pull requests): the epic is all the
            # brief names. An epic is not a task card, so its own card verdict cannot admit the brief,
            # and no override applies.
            names = ", ".join(f"#{number}" for _repo, number in epics)
            return (
                f"❌ DoR refused: dor_epic_only_no_task_issue: the brief names only the stream epic {names}; "
                "name the task issue it implements (#9276)"
            ), None
        stream_epics = [number for _repo, number in epics]
    if not issue_numbers:
        return None, None
    record: dict[str, Any] = {"issues": issue_numbers, "warnings": warnings}
    if stream_epics:
        record["stream_epic"] = stream_epics
    if issue_repositories:
        record["issue_repositories"] = issue_repositories
    if allow_reason is not None:
        record["allow_warn_reason"] = allow_reason
    if warnings and allow_reason is None:
        details = "; ".join(
            f"{('#' + label) if label.isdigit() else label}: {missing}" for label, missing in warnings.items()
        )
        return f"❌ DoR issue card WARN ({details}); fix the issue or pass --allow-dor-warn REASON", record
    return None, record


def _review_attempt_prompt_admission(
    args: argparse.Namespace, early_prompt: str | None, review_id: str, attempt_id: str
) -> tuple[str | None, dict[str, Any] | None]:
    """Admit a ``--review-attempt`` prompt, or say why not: ``(refusal, None)`` or ``(None, review_contract)``.

    Runs before any side effect. The prompt's own attempt block (#8996) must name this dispatch's ids, and the
    prompt must come from a ``--prompt-file`` whose render record matches the code the seat would run (#9163).
    """
    import yaml

    from scripts.agent_runtime.review_mcp import check_review_contract
    from scripts.review.prompts.check import AttemptIdsUnreadableError, check_prompt, parse_attempt_ids
    from scripts.review.render_contract import ReviewContractError

    prompt_file = Path(args.prompt_file) if getattr(args, "prompt_file", None) else None
    prompt = early_prompt or ""
    try:
        manifest = yaml.safe_load(Path(args.review_attempt).read_bytes())
        if isinstance(manifest, dict) and any(key in manifest for key in ("manifest_schema", "kind", "inputs")):
            contract = check_review_contract(prompt_file, prompt, review_id=review_id, attempt_id=attempt_id)
            try:
                input_root = worktree_claims.required_review_input_root(contract)
            except ValueError as err:
                return f"❌ review attempt refused: {err}", None
            checked = check_prompt(
                prompt,
                Path(args.review_attempt),
                repo_root=Path(input_root),
                prompts_dir=Path(contract["server_checkout"]) / "scripts/review/prompts",
                recorded_prompts_dir=Path(contract["render_checkout"]) / "scripts/review/prompts",
                files_read=contract["recorded_files_read"],
                template_sha256=contract["recorded_template_sha256"],
                recorded_templates=contract["recorded_templates"],
                review_id=review_id,
                attempt_id=attempt_id,
                review_access=getattr(args, "review_access", "full"),
            )
            if not checked.passed:
                return "❌ review attempt refused: prompt_render_invalid: " + "; ".join(checked.errors), None
            return None, contract
        if prompt_file is None and getattr(args, "prompt", None) == "-":
            # stdin is read only later, and a stdin prompt has no render record: refused as review_render_record_missing
            return None, check_review_contract(None, "")
        prompt_review_id, prompt_attempt_id = parse_attempt_ids(prompt, custom=True)
    except AttemptIdsUnreadableError as err:
        return f"❌ review attempt refused: prompt_attempt_ids_unreadable: {err} (#8996)", None
    except ReviewContractError as err:
        return f"❌ {err}", None
    except (OSError, ValueError, yaml.YAMLError) as err:
        return f"❌ review attempt refused: prompt_render_invalid: {type(err).__name__}", None
    if prompt_review_id is None or prompt_attempt_id is None:
        # A seat whose prompt names no ids can only guess them, and a guessed id never matches the
        # ledger this dispatch prepares — the failure #8996 was filed for.
        return (
            "❌ review attempt refused: prompt_attempt_ids_missing: a --review-attempt prompt must print "
            "the review_id and attempt_id its seat echoes (render it with --review-id/--attempt-id) (#8996)"
        ), None
    id_mismatches = [
        f"{name} prompt={found!r} dispatch={expected!r}"
        for name, found, expected in (
            ("review_id", prompt_review_id, review_id),
            ("attempt_id", prompt_attempt_id, attempt_id),
        )
        if found != expected
    ]
    if id_mismatches:
        return (
            "❌ review attempt refused: prompt_attempt_ids_mismatch: the prompt's attempt block ids differ "
            f"from --review-id/--attempt-id ({'; '.join(id_mismatches)}) (#8996)"
        ), None
    # The seat's sources server launches from the primary checkout; the prompt may have been rendered anywhere.
    try:
        return None, check_review_contract(prompt_file, prompt, review_id=review_id, attempt_id=attempt_id)
    except ReviewContractError as err:
        return f"❌ {err}", None
    except (OSError, ValueError) as err:
        return f"❌ review attempt refused: prompt_render_invalid: {type(err).__name__}", None


def _lock_review_input_root(
    contract: dict[str, Any],
    locks: contextlib.ExitStack,
    *,
    locked_worktree: Path | None = None,
    inputs: Sequence[Path] = (),
) -> None:
    """Protect input preparation until the task's persisted record takes over (#9485, #9597).

    Lock the containing registered checkout of the input root and of every other
    attempt input (``_review_attempt_input_paths``), rather than an input
    subdirectory's lock. The dispatch stack releases them on every early return
    or exception, and the kernel releases them on process exit; no git lock leaks.
    """
    input_root = Path(worktree_claims.required_review_input_root(contract)).resolve()
    if not input_root.is_dir():
        raise ValueError("review input root disappeared before preparation")
    paths = [input_root]
    for path in inputs:
        resolved = path.resolve()
        if not resolved.exists():
            raise ValueError("review attempt input disappeared before preparation")
        paths.append(resolved)
    # Reuse eligibility excludes ACP runtime checkouts. Reading one still
    # requires its removal lock, so consult registration directly here: the
    # primary's, exactly as the removal guard does, never a repository
    # discovered from an input path.
    wc = _load_worktree_containment()
    try:
        main_root, registered = worktree_claims.repository_registration(_REPO_ROOT)
    except ValueError as exc:
        raise ValueError(f"review input {exc}") from exc
    selected = {
        tree
        for path in paths
        if (tree := worktree_claims.review_input_worktree(path, main_root=main_root, registered=registered)) is not None
    }
    for tree in sorted(selected):
        if locked_worktree is None or tree != locked_worktree.resolve():
            locks.enter_context(worktree_lock(tree))
    current = wc.registered_worktrees(main_root)
    if any(not path.exists() for path in paths) or any(tree not in current for tree in selected):
        raise ValueError("review input worktree disappeared while dispatch waited for its lock")


def _review_attempt_input_paths(manifest: str) -> list[Path]:
    """Paths a formal attempt reads after its id is reserved, besides its input root (#9597).

    The worker re-reads the manifest (``attempt_boundary``) at the canonical path
    dispatch froze at admission, and runs this checkout's code and its lazy
    imports for the whole attempt. A formal attempt takes no output schema
    (``attempt_output_schema_unsupported``). The receipts, the sources server and
    its interpreter live in the primary checkout or this one; the runtime tmp root
    is refused inside a removable checkout (``_refuse_review_scratch_in_worktree``).
    """
    return list(dict.fromkeys([Path(manifest).resolve(), _local_repo_root]))


def _refuse_review_scratch_in_worktree() -> None:
    """Refuse an attempt whose runtime scratch would sit in a removable checkout (#9597).

    The worker's tmp lease lives under the fleet scratch root for the whole
    attempt and no task record claims it, so a scratch root whose real path is
    inside a registered linked checkout is refused before the attempt id is
    reserved. The registration is the primary's, the removal guard's source;
    discovering a repository from the scratch path would let a nested one mask
    the checkout around it.
    """
    scratch = resolve_scratch_root().resolve()
    try:
        main_root, registered = worktree_claims.repository_registration(_REPO_ROOT)
    except ValueError as exc:
        raise ValueError(f"review_scratch_root_unverifiable: {exc}") from exc
    tree = worktree_claims.review_input_worktree(scratch, main_root=main_root, registered=registered)
    if tree is not None:
        raise ValueError(
            f"review_scratch_root_in_worktree: the fleet scratch root {scratch} lies in removable "
            f"checkout {tree}; set LU_SCRATCH_ROOT outside every linked checkout"
        )


def cmd_dispatch(args: argparse.Namespace) -> int:
    """Spawn a detached worker and return immediately (stdout: `<task_id>\n<run_nonce>`)."""
    # The stack owns the worktree lock taken before create-or-attach. Dispatch
    # releases it once the task record is published; every earlier return or
    # exception releases it here (#8610). ``admission_holds`` drops an
    # admission hold that no later record replaced (#8717).
    with contextlib.ExitStack() as worktree_locks, contextlib.ExitStack() as admission_holds:
        return _dispatch(args, worktree_locks=worktree_locks, admission_holds=admission_holds)


def _dispatch(
    args: argparse.Namespace,
    *,
    worktree_locks: contextlib.ExitStack,
    admission_holds: contextlib.ExitStack,
) -> int:
    """Body of :func:`cmd_dispatch`; ``worktree_locks`` holds the worktree lock.

    ``admission_holds`` releases this run's admission hold on any return or
    exception before the task record replaces it.
    """
    if (
        str(getattr(args, "agent", "") or "").strip().casefold() in {"agy", "gemini"}
        and (_dispatch_is_review_typed(args) or getattr(args, "pr", None) is not None)
        and args.mode != "read-only"
    ):
        print("❌ agy_review_permissions_require_read_only: use --mode read-only", file=sys.stderr)
        return 2

    if getattr(args, "pinned_head", None) and not (getattr(args, "branch", None) or getattr(args, "pr", None)):
        print("❌ PINNED_HEAD_TARGET_REQUIRED: --pinned-head requires --branch or --pr", file=sys.stderr)
        return 2

    # Diagnose the required profile before route admission defaults to code
    # review and checks its explicit risk.
    if (
        str(getattr(args, "agent", "") or "").strip().casefold() in {"agy", "gemini"}
        and getattr(args, "require_review_verdict", False)
        and not getattr(args, "review_profile", None)
    ):
        from scripts.ai_agent_bridge._agy import gemini_review_profile_error

        print(f"❌ {gemini_review_profile_error(None)}", file=sys.stderr)
        return 2

    from scripts.agent_runtime.attribution import resolve_invocation_attribution
    from scripts.orchestration.job_host_exec import (
        SshTransportError,
        decide_dispatch_placement,
        format_forward_config_refusal,
        forward_dispatch,
        notebook_fallback_after_forward,
    )

    # Captured before any later mutation of ``args`` (e.g. --pr resolving into
    # args.branch, a rejected --model cleared to None): the hash binds what was
    # literally parsed, not what dispatch later resolved it to (#8430 R3-A r8).
    dispatch_args_hash = dispatch_args_sha256(args)
    # The advisory binding's argument half, as parsed: dispatch mutates ``args`` below (#9275).
    advisory_args = json.loads(json.dumps(advisory_args_payload(args)))
    advisory_args_hash = bounded_advisory.canonical_sha256(advisory_args)
    if getattr(args, "print_advisory_binding", False):
        try:
            print(advisory_binding(advisory_args_hash, _binding_prompt_sha256(args, read_stdin=True)))
        except OSError as exc:
            print(f"❌ cannot read --prompt-file for the advisory binding: {exc}", file=sys.stderr)
            return 2
        return 0
    advisory_flag_refusal = _advisory_flag_refusal(args)
    if advisory_flag_refusal:
        print(f"❌ dispatch refused: {advisory_flag_refusal}", file=sys.stderr)
        return 2

    task_id = args.task_id
    run_nonce = getattr(args, "run_nonce", None) or os.environ.get("LU_RUNTIME_RUN_NONCE") or _generate_run_nonce()

    caller_task_id = os.environ.get("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "").strip()
    if caller_task_id:
        # Read-only: this runs before the Kimi gate, so it must not create the task directory.
        caller_state = _read_state_json(_state_path_no_create(caller_task_id))
        if caller_state is None or caller_state.get("mode") not in _WRITE_CAPABLE_MODES:
            print(
                f"❌ dispatch refused from task {caller_task_id!r}: "
                "read-only or unavailable parent task record cannot start a dispatch.",
                file=sys.stderr,
            )
            return 2

    try:
        attribution = resolve_invocation_attribution(
            explicit=getattr(args, "initiator", None),
            task_id=task_id,
        )
    except ValueError as exc:
        print(f"❌ invalid --initiator: {exc}", file=sys.stderr)
        return 2

    # Resolve before DoR: the first check runs before worktree setup (#9133).
    fleet_repo_key = getattr(args, "repo", None)
    try:
        from scripts.orchestration.fleet_repos import (
            FleetRepoError,
            fleet_repo_as_dict,
            resolve_fleet_repo,
        )
    except ImportError:  # pragma: no cover - flat script path
        from orchestration.fleet_repos import (  # type: ignore
            FleetRepoError,
            fleet_repo_as_dict,
            resolve_fleet_repo,
        )

    from scripts.agent_runtime.kimi_admission import is_kimi_seat

    try:
        fleet_repo, target_repo_root = resolve_fleet_repo(
            fleet_repo_key, primary_root=_REPO_ROOT, require_checkout=False
        )
    except FleetRepoError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2
    # Kimi admission turns on the repository's catalog role, not on which sibling
    # checkouts this host has: a Kimi request reports a missing checkout only after
    # the Kimi gate. Every other request is refused for it here, as before.
    try:
        resolve_fleet_repo(fleet_repo_key, primary_root=_REPO_ROOT)
        checkout_error = None
    except FleetRepoError as exc:
        checkout_error = f"❌ {exc}"
    if checkout_error and not is_kimi_seat(args.agent, model=getattr(args, "model", None)):
        print(checkout_error, file=sys.stderr)
        return 2
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", fleet_repo.github):
        print(f"❌ --repo {fleet_repo.key!r} has no valid owner/name in fleet_repos", file=sys.stderr)
        return 2
    fleet_repo_meta = fleet_repo_as_dict(fleet_repo, target_repo_root)

    sys.path.insert(0, str(_REPO_ROOT / "scripts"))
    from agent_runtime.telemetry import resolve_dispatch_start_telemetry
    from scripts.review.model_catalog import is_cursor_auto_selector, retired_model_refusal

    # A catalog-retired model is refused before any check can run a command.
    retired_refusal = retired_model_refusal(getattr(args, "model", None))
    if retired_refusal:
        print(f"❌ dispatch refused: {retired_refusal}", file=sys.stderr)
        return 2

    # Every worker and review seat starts with the rules core: without it nothing
    # is dispatched, and this runs before any check, worktree or task record.
    try:
        rules_core.require_core(getattr(args, "rules_seat", None))
    except rules_core.RulesCoreMissing as exc:
        print(f"❌ dispatch refused: {exc}; the rules core is required.", file=sys.stderr)
        return 2

    # The launch route (the retired-CLI alias and any budget substitution; #8517: a review
    # attempt never takes a substitute) is resolved inside ``resolve_and_admit``, which gates
    # the original request before the route probes anything and the resolved route after it.
    review_attempt = getattr(args, "review_attempt", None)
    if review_attempt and getattr(args, "output_schema", None):
        print(
            "❌ review attempt refused: attempt_output_schema_unsupported: "
            "--review-attempt cannot be combined with --output-schema (#9251)",
            file=sys.stderr,
        )
        return 2
    from scripts.agent_runtime.target_admission import launch_seat

    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    from scripts.ai_agent_bridge.routing_guard import (
        RoutingGuardError,
        assert_agent_routing_allowed,
        assert_model_routing_allowed,
    )

    try:
        assert_agent_routing_allowed(args.agent, context="delegate dispatch")
        assert_model_routing_allowed(getattr(args, "model", None), context="delegate dispatch --model")
    except RoutingGuardError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2

    original_agent = args.agent
    original_model = getattr(args, "model", None)
    language_lane = _dispatch_is_language_lane(args)
    if language_lane and launch_seat(original_agent) not in _LANGUAGE_LANES:
        print(
            "❌ ROUTING REFUSED: LANGUAGE-LANES RULE (operator 2026-09-27): "
            f"--agent {launch_seat(original_agent)} cannot author, review, critique, settle, or judge "
            "Ukrainian language, culture, or heritage content; "
            "allowed lanes are claude, codex (GPT), and agy (Gemini).",
            file=sys.stderr,
        )
        return 2

    # #8775: validate caller-supplied paths once, before the DoR check, PR
    # resolution, or anything else that can run an external command, and
    # before any use reaches a check, a subprocess cwd, a task record, or the
    # worker prompt. Every later step uses the resolved paths returned here,
    # never the caller's strings. An explicit --worktree PATH must stay inside
    # the dispatching agent's own dispatch subtree; --cwd keeps its documented
    # isolated read-only and sibling-repo flows. Read-only git lookups between
    # here and the worktree lock (the write-mode worktree check, the cursor
    # review check, --preflight-triage) may run git in the validated path; the
    # path is re-checked after the lock, before any step that changes it.
    worktree_arg = getattr(args, "worktree", None)
    validated_worktree: Path | None = None
    validated_cwd: Path | None = None
    if worktree_arg and worktree_arg != "auto":
        validated_worktree, path_error = _validate_explicit_worktree(
            worktree_arg,
            agent=launch_seat(args.agent),
            repo_root=target_repo_root,
        )
        if path_error:
            print(path_error, file=sys.stderr)
            return 2
        worktree_arg = str(validated_worktree)
    if args.cwd:
        validated_cwd, path_error = _validate_caller_path("--cwd", args.cwd, resolve=_resolve_cwd_path)
        if path_error:
            print(path_error, file=sys.stderr)
            return 2
        args.cwd = str(validated_cwd)

    # Explicit-target retention precedes route/prompt admission and all cleanup.
    # Auto targets depend on the admitted route and are checked just after routing.
    # The sidecar's paths grant no authority; they only prevent destructive release.
    try:
        review_dependencies = _review_attempt_worktree_dependencies(args)
        if review_dependencies and getattr(args, "branch", None) and worktree_arg != "auto":
            # A validated target already registered on this branch is reused,
            # never released. Later worktree validation still checks reuse safety.
            _refuse_review_attempt_branch_holders(
                args.branch,
                [path for path in _branch_worktree_paths(args.branch) if path != validated_worktree],
                review_dependencies,
            )
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"❌ review attempt refused: {exc}", file=sys.stderr)
        return 2

    # #9874: --branch only continues a remote branch. Observe it before any
    # content scan or launch routing, using the same canonical read as authoring
    # admission. Reuse the observation at initial admission, never at a recheck.
    observed_branch_head: str | None = None
    if args.mode in _WRITE_CAPABLE_MODES and getattr(args, "branch", None) and fleet_repo.default:
        cross_repo_error = _resolve_cross_repo_binding_error(
            worktree_arg=worktree_arg or "auto",
            cwd_arg=args.cwd,
            requested_branch=args.branch,
            target_repo_root=target_repo_root,
        )
        if cross_repo_error:
            print(cross_repo_error, file=sys.stderr)
            return 2
        try:
            args.branch = _validate_branch_reuse_name(args.branch)
            observed_branch_head = _ls_remote_branch_sha(_authoring_canonical_remote(), args.branch, strict=True)
        except ValueError as exc:
            print(f"❌ {exc}", file=sys.stderr)
            return 2
        except _AuthoringObservationUnknown as exc:
            print(f"❌ DISPATCH_BRANCH_REMOTE_READ_FAILED: {exc}", file=sys.stderr)
            return 2
        if observed_branch_head is None:
            print(
                f"❌ DISPATCH_BRANCH_NOT_FOUND: --branch {args.branch!r} does not exist on the canonical remote. "
                "--branch continues an existing remote branch; for a new branch omit --branch "
                "(default: <agent>/<task-id>), optionally with --base.",
                file=sys.stderr,
            )
            return 2

    # The single Kimi gate runs on the original request (--agent, --model and their aliases)
    # before the launch route probes the budget or a model, and on the route it resolves —
    # the retired-CLI alias and any budget substitution — on the validated paths, before any
    # later preflight that can run an external command, write a record, sweep runtime tmp,
    # archive a task or create a worktree. Owned paths are read in the tree the worker
    # starts from: a reused worktree on disk and at its commit, a new one at its creation
    # base commit (fetched and read with git plumbing). The worktree must start from
    # ``kimi_start_commit``; two checks below refuse one that does not.
    routing = _DispatchRouting()
    kimi_refusal, kimi_start_commit, launch_target = _kimi_dispatch_gate(
        args,
        agent=original_agent,
        route=_dispatch_route(args, routing, language_lane=language_lane, review_attempt=review_attempt),
        repo_role=fleet_repo.role,
        target_repo_root=target_repo_root,
        validated_worktree=validated_worktree,
        validated_cwd=validated_cwd,
    )
    if kimi_refusal:
        print(f"❌ {kimi_refusal}", file=sys.stderr)
        return 2
    if checkout_error:
        print(checkout_error, file=sys.stderr)
        return 2
    # Everything below launches the admitted route; nothing resolves it again.
    dispatch_agent, args.model = launch_target.recipient, launch_target.model
    # Reviewer resolution and budget substitution can change the seat after
    # the original-request guard. Enforce the same boundary on the final route.
    if (
        dispatch_agent in {"agy", "gemini"}
        and (_dispatch_is_review_typed(args) or getattr(args, "pr", None) is not None)
        and args.mode != "read-only"
    ):
        print("❌ agy_review_permissions_require_read_only: use --mode read-only", file=sys.stderr)
        return 2
    requested_agent = routing.requested_agent or original_agent
    agent_alias_note = routing.alias_note
    agent_substitution = routing.substitution

    if review_dependencies and getattr(args, "branch", None) and worktree_arg == "auto":
        try:
            reuse_target = _normalize_worktree_path(
                str(_auto_worktree_path(dispatch_agent, args.task_id, repo_root=target_repo_root)),
                repo_root=target_repo_root,
            )
            _refuse_review_attempt_branch_holders(
                args.branch,
                [path for path in _branch_worktree_paths(args.branch) if path != reuse_target],
                review_dependencies,
            )
        except (OSError, ValueError, RuntimeError) as exc:
            print(f"❌ review attempt refused: {exc}", file=sys.stderr)
            return 2

    # #9518: while a lane is past its plan cap with a fresh positive credit balance
    # (router state irrelevant), only its credit-period models are admitted. Checked on the admitted route (aliases,
    # substitution and review selection applied; no --model means the lane default)
    # before any side effect.
    credit_refusal = _credit_period_refusal(dispatch_agent, launch_target.model)
    if credit_refusal:
        print(f"❌ dispatch refused: {credit_refusal}", file=sys.stderr)
        return 2

    # #9275 (operator decision 2026-09-30): a bounded worker is admitted only with a
    # complete advisory envelope bound to this dispatch. Checked on the admitted
    # route — after aliases, --force-agent and any substitution — before any task
    # record, worktree or other side effect.
    try:
        advisory_admission = _admit_advisory(
            args,
            dispatch_agent=dispatch_agent,
            launch_model=launch_target.model,
            bound_args=advisory_args,
            repo_root=target_repo_root,
        )
    except bounded_advisory.AdvisoryRefused as exc:
        print(f"❌ dispatch refused: {exc}", file=sys.stderr)
        return 2

    # Formal attempts and permission-only AGY Ukrainian reviews share the
    # effective sources grant. Refuse before archival, provisioning or spawn.
    sources_review_access = None
    if review_attempt:
        sources_review_access = getattr(args, "review_access", "full")
    elif (
        dispatch_agent in {"agy", "gemini"}
        and args.mode == "read-only"
        and getattr(args, "review_profile", None) == "ukrainian"
        and (
            getattr(args, "review", False)
            or getattr(args, "require_review_verdict", False)
            or str(getattr(args, "type", "") or "").strip().casefold() == "review"
        )
    ):
        sources_review_access = "isolated"

    # Match the launch prompt's precedence. Ordinary review stdin is consumed
    # before side effects; formal attempts require a render-recorded file and
    # must refuse stdin without consuming it.
    early_prompt: str | None = None
    if getattr(args, "prompt_file", None):
        try:
            early_prompt = Path(args.prompt_file).read_text(encoding="utf-8")
        except OSError:
            early_prompt = None
    elif getattr(args, "prompt", None):
        early_prompt = (
            sys.stdin.read()
            if args.prompt == "-" and sources_review_access is not None and not review_attempt
            else str(args.prompt)
        )

    if sources_review_access is not None:
        from scripts.agent_runtime.review_mcp import ReviewToolRequirementsRefused, check_review_tool_requirements

        if early_prompt is not None:
            try:
                check_review_tool_requirements(early_prompt, sources_review_access)
            except ReviewToolRequirementsRefused as exc:
                print(f"❌ dispatch refused: {exc}", file=sys.stderr)
                return 2

    dor_reason = getattr(args, "allow_dor_warn", None)
    if dor_reason is not None:
        dor_reason = str(dor_reason).strip()
        if not dor_reason:
            print("❌ --allow-dor-warn requires a non-empty reason", file=sys.stderr)
            return 2
    dor_record: dict[str, Any] | None = None
    if early_prompt is not None and args.mode in {"workspace-write", "danger"}:
        dor_error, dor_record = _run_dor_preflight(early_prompt, dor_reason, dispatch_repo=fleet_repo.github)
        if dor_error:
            print(dor_error, file=sys.stderr)
            return 2
    cursor_auto_error = _cursor_auto_refusal(args, agent=dispatch_agent, model=args.model, dor_record=dor_record)
    if cursor_auto_error:
        print(cursor_auto_error, file=sys.stderr)
        return 2
    cursor_auto_admission = (
        {"admitted": True, "model": args.model, "issues": list(dor_record["issues"])}
        if dispatch_agent == "cursor" and dor_record and is_cursor_auto_selector(args.model)
        else None
    )

    task_id = args.task_id
    try:
        _validate_dispatch_effort(args.agent, getattr(args, "effort", None))
    except ValueError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2
    from scripts.ai_agent_bridge._agy import (
        GeminiChangedPathListError,
        gemini_review_verdict_dispatch_error,
        resolve_same_repo_pr_head,
    )

    pr_number = getattr(args, "pr", None)
    pinned_head = getattr(args, "pinned_head", None)
    if pr_number is not None:
        try:
            pr_branch, resolved_head = resolve_same_repo_pr_head(int(pr_number), repo_root=str(_REPO_ROOT))
        except GeminiChangedPathListError as exc:
            print(f"❌ could not resolve PR head: {exc}", file=sys.stderr)
            return 2
        admitted_head = getattr(args, "_review_admission_head", None)
        if admitted_head and admitted_head != resolved_head:
            print("❌ REVIEW_TARGET_UNRESOLVED: PR head changed after review admission", file=sys.stderr)
            return 2
        supplied_head = str(pinned_head).strip().lower() if pinned_head else ""
        if supplied_head and supplied_head != resolved_head:
            print(
                f"❌ --pinned-head {pinned_head} is not PR #{pr_number} head {resolved_head}",
                file=sys.stderr,
            )
            return 2
        named_branch = getattr(args, "branch", None)
        if named_branch and named_branch != pr_branch:
            print(
                f"❌ --branch {named_branch!r} is not PR #{pr_number} head {pr_branch!r}",
                file=sys.stderr,
            )
            return 2
        if supplied_head and not named_branch:
            print(
                f"❌ --pr {pr_number} with --pinned-head requires --branch {pr_branch!r}",
                file=sys.stderr,
            )
            return 2
        pinned_head = resolved_head
        args.branch = pr_branch
        args.pinned_head = pinned_head

    gemini_checked_heads: list[str] = []
    gemini_review_error = gemini_review_verdict_dispatch_error(
        agent=str(args.agent),
        require_review_verdict=bool(getattr(args, "require_review_verdict", False)),
        profile=getattr(args, "review_profile", None),
        pr_number=pr_number,
        branch=getattr(args, "branch", None),
        repo_root=str(_REPO_ROOT),
        model=original_model,
        review=bool(getattr(args, "review", False))
        or str(getattr(args, "type", "") or "").strip().casefold() == "review",
        head_out=gemini_checked_heads,
        head_sha=pinned_head,
    )
    if gemini_review_error is not None:
        print(f"❌ {gemini_review_error}", file=sys.stderr)
        return 2
    try:
        requested_harness = _resolve_dispatch_harness(args.agent, getattr(args, "harness", None))
    except ValueError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2
    force_admission_reason = getattr(args, "force_admission", None)
    if force_admission_reason is not None:
        force_admission_reason = str(force_admission_reason).strip()
        if not force_admission_reason:
            print("❌ --force-admission requires a non-empty reason", file=sys.stderr)
            return 2

    review_id = getattr(args, "review_id", None)
    attempt_id = getattr(args, "attempt_id", None)
    review_plan = None
    review_access = getattr(args, "review_access", "full")
    review_contract: dict[str, Any] | None = None
    review_input_root: str | None = None
    review_input_paths: list[Path] = []
    if review_attempt or review_id or attempt_id:
        if not (review_attempt and review_id and attempt_id):
            print(
                "❌ --review-attempt, --review-id, and --attempt-id must be used together",
                file=sys.stderr,
            )
            return 2
        if review_access == "full" and not getattr(args, "full_checkout", False):
            print("❌ full_review_requires_full_checkout: use --full-checkout", file=sys.stderr)
            return 2
        if review_access == "full" and args.mode != "read-only":
            print("❌ attempt_requires_fresh_read_only_sources: use --mode read-only", file=sys.stderr)
            return 2
        manifest_path = Path(review_attempt)
        if not manifest_path.is_file():
            print(f"❌ review manifest file not found: {manifest_path}", file=sys.stderr)
            return 2
        # Admission, preparation and the worker read one canonical manifest path (#9597):
        # only the target's checkout is claimed, so a supplied symlink's checkout may go.
        review_attempt = args.review_attempt = str(manifest_path.resolve())

        effective_harness = requested_harness or args.agent
        from scripts.agent_runtime.review_mcp import (
            SUPPORTED_HARNESSES,
            UNSUPPORTED_HARNESS_REASONS,
        )

        if effective_harness in UNSUPPORTED_HARNESS_REASONS:
            print(
                f"❌ review attempt refused for {args.agent}: {UNSUPPORTED_HARNESS_REASONS[effective_harness]} (#8517)",
                file=sys.stderr,
            )
            return 2
        if effective_harness not in SUPPORTED_HARNESSES:
            print(
                f"❌ review attempt refused for {args.agent}: unsupported harness {effective_harness!r} (#8517)",
                file=sys.stderr,
            )
            return 2
        # Before any archival, worktree, task record or worker (#9163 finding 3).
        review_refusal, review_contract = _review_attempt_prompt_admission(args, early_prompt, review_id, attempt_id)
        if review_refusal:
            print(review_refusal, file=sys.stderr)
            return 2
        try:
            # A rootless contract is refused here, before the attempt id is reserved (#9597).
            review_input_root = worktree_claims.required_review_input_root(review_contract)
        except ValueError as exc:
            print(f"❌ review attempt refused: {exc}", file=sys.stderr)
            return 2

    invalid_owned_paths = _owned_path_errors(getattr(args, "owned_path", None))
    if invalid_owned_paths:
        print(
            "❌ --owned-path must be a repo-relative path or narrow glob (not empty, '.', absolute, "
            "a '..' segment, or a glob starting with a wildcard): "
            + ", ".join(repr(value) for value in invalid_owned_paths),
            file=sys.stderr,
        )
        return 2

    requested_branch = getattr(args, "branch", None)
    full_checkout = bool(getattr(args, "full_checkout", False))
    try:
        sparse_include = _infer_sparse_include(
            getattr(args, "sparse_include", None),
            owned_paths=getattr(args, "research_owned_path", None),
            prompt_text=early_prompt,
        )
    except ValueError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 1
    if early_prompt is not None:
        write_intent_error = _read_only_write_intent_error(
            mode=args.mode,
            prompt=early_prompt,
        )
        if write_intent_error:
            print(write_intent_error, file=sys.stderr)
            return 2
    silence_timeout = getattr(args, "silence_timeout", DEFAULT_SILENCE_TIMEOUT_S)
    initial_response_timeout = getattr(
        args,
        "initial_response_timeout",
        DEFAULT_INITIAL_RESPONSE_TIMEOUT_S,
    )
    max_budget_usd = getattr(args, "max_budget_usd", None)
    keep_worktree = bool(getattr(args, "keep_worktree", False))

    # Branch reuse always needs an isolated worktree.  A bare --branch uses
    # the normal dispatch subtree automatically; --cwd would otherwise make
    # it unclear which checkout must be validated.
    if requested_branch and not worktree_arg:
        worktree_arg = "auto"

    if args.cwd and worktree_arg:
        print(
            "❌ --cwd cannot be combined with --worktree or --branch. Use --worktree for delegated write isolation.",
            file=sys.stderr,
        )
        return 2

    # #672 P2.1: allowlisted --repo retargets worktree creation to a sibling
    # checkout. Control-plane task state stays on the public primary.
    if not fleet_repo.default and requested_branch:
        print(
            "❌ --branch attach on sibling --repo is not supported in P2.1; "
            "use --repo with bare --worktree for a fresh branch, or the manual --cwd flow.",
            file=sys.stderr,
        )
        return 2
    # Explicit primary-root callers need the same isolation as the default
    # read-only flow (#10025). Keep their dispatch working without snapshotting
    # other drivers' local edits in that shared checkout.
    primary_read_only_cwd = (
        args.mode == "read-only" and not worktree_arg and validated_cwd == target_repo_root
    )
    if primary_read_only_cwd:
        args.cwd = None
        validated_cwd = None
    detached_read_only = args.mode == "read-only" and not worktree_arg and not args.cwd
    if detached_read_only:
        worktree_arg = "auto"

    if not fleet_repo.default and not worktree_arg and not args.cwd:
        print(
            "❌ sibling --repo requires --worktree (auto) or --cwd at an existing sibling worktree.",
            file=sys.stderr,
        )
        return 2

    # #6900: --worktree/--branch (and the default worker cwd) bind the target
    # checkout (public primary, or --repo sibling). Invoking from another git
    # root without --repo used to create the worktree in the primary while the
    # shell cwd said otherwise.
    cross_repo_error = _resolve_cross_repo_binding_error(
        worktree_arg=None if primary_read_only_cwd else worktree_arg,
        cwd_arg=str(target_repo_root) if primary_read_only_cwd else args.cwd,
        requested_branch=requested_branch,
        target_repo_root=target_repo_root,
    )
    if cross_repo_error:
        print(cross_repo_error, file=sys.stderr)
        return 2

    acp_runtime_error = _resolve_acp_runtime_target_error(
        worktree_arg=worktree_arg,
        cwd_arg=args.cwd,
        target_repo_root=target_repo_root,
    )
    if acp_runtime_error:
        print(acp_runtime_error, file=sys.stderr)
        return 2

    # An explicit read-only cwd must also be isolated (#10025): snapshotting
    # the primary checkout attributes concurrent driver edits to this task.
    if (
        args.mode == "read-only"
        and validated_cwd is not None
        and _resolve_verified_worktree_path(validated_cwd) is None
    ):
        print(
            "❌ read-only --cwd requires a verified added worktree; "
            "omit --cwd for an automatic detached dispatch worktree, or use --worktree.",
            file=sys.stderr,
        )
        return 2

    # Write-capable modes must resolve to a verified added worktree (#4445).
    # Evaluated before side effects.
    write_cwd_error = _resolve_write_cwd_error(
        mode=args.mode,
        worktree_arg=worktree_arg,
        cwd_arg=args.cwd,
    )
    if write_cwd_error:
        print(write_cwd_error, file=sys.stderr)
        return 2

    dirty_primary_error = _resolve_dirty_primary_checkout_error(mode=args.mode)
    if dirty_primary_error:
        print(dirty_primary_error, file=sys.stderr)
        return 2

    primary_integrity_error = _resolve_primary_integrity_error(mode=args.mode)
    if primary_integrity_error:
        print(primary_integrity_error, file=sys.stderr)
        return 2

    # #9739: after the argument and checkout checks above, so a malformed dispatch
    # gets its own refusal; before preflight triage, the task directory, archival,
    # runtime cleanup, forwarding, any rebase, worktree or provider. A forwarded
    # dispatch runs this again on its host; a checkout reaped while dispatch
    # waits for its lock is admitted again under that lock (#8610).
    def admit_authoring(branch_head: str | None = None) -> _AuthoringAdmission | None:
        return _authoring_review_admission(
            args,
            dispatch_agent=dispatch_agent,
            requested_harness=requested_harness,
            requested_branch=requested_branch,
            worktree_arg=worktree_arg,
            validated_worktree=validated_worktree,
            validated_cwd=validated_cwd,
            target_repo_root=target_repo_root,
            repository=fleet_repo.github,
            default_repo=bool(fleet_repo.default),
            observed_branch_head=branch_head,
        )

    try:
        authoring_admission = admit_authoring(observed_branch_head)
    except _AuthoringReviewRefused as exc:
        print(exc.render(), file=sys.stderr)
        return 2
    # A worktree's base defaults to the repository's actual default branch where
    # admission discovered it (M4); "main" only where admission does not apply.
    worktree_base = getattr(args, "base", None) or (
        authoring_admission.default_branch if authoring_admission is not None else "main"
    )
    # The task directory is created only once the writer is admitted (#9739).
    state_path = _state_path(task_id)

    if getattr(args, "preflight_triage", False):
        preflight_rc = _run_preflight_triage(args, worktree_arg=worktree_arg)
        if preflight_rc is not None:
            return preflight_rc

    _warn_node_modules_integrity()
    _warn_venv_integrity()
    _warn_worktree_cleanup_integrity()

    _warn_if_monitor_api_unreachable()
    if bool(getattr(args, "dry_run", False)):
        print("🧹 runtime tmp orphan sweep: skipped=dry-run", file=sys.stderr)
    else:
        runtime_tmp_sweep = _sweep_runtime_tmp_orphans()
        print(
            "🧹 runtime tmp orphan sweep: "
            f"leases_reaped={runtime_tmp_sweep['leases_reaped']} "
            f"bytes_freed={runtime_tmp_sweep['bytes_freed']} "
            f"errors={runtime_tmp_sweep['errors']} "
            f"error_details={runtime_tmp_sweep['error_details']}",
            file=sys.stderr,
        )

    # #6980: fail closed when the task record (or its .result) already
    # exists in ANY state. The previous guard only refused live
    # running/spawning PIDs, so a dispatch with a completed task-id
    # silently overwrote batch_state/tasks/<id>.json + .result and
    # destroyed receipt evidence. Must run BEFORE ownership admission
    # so a rejected duplicate cannot DELETE/replace live write claims
    # (#5643 CF F001). --force-new archives only the caller's terminal
    # record; a dead pid does not make a nonterminal record safe to replace.
    existing = _read_state(state_path)
    record_exists = state_path.exists()
    result_exists = _result_path(task_id).exists()
    # An archived record still owns its task id (#8625): reuse needs --force-new,
    # which leaves the archived record where it is.
    archived_path = _archived_state_path(task_id)
    archived_exists = archived_path.is_file()
    if record_exists or result_exists or archived_exists:
        if not bool(getattr(args, "force_new", False)):
            if record_exists or result_exists:
                status = _existing_task_status(state_path, existing)
            else:
                existing = _read_state(archived_path)
                status = f"{_existing_task_status(archived_path, existing)} (archived)"
            pid = existing.get("pid") if existing else None
            pid_part = f" (pid={pid})" if pid not in (None, "") else ""
            print(
                f"❌ task_id {task_id!r} is already {status}{pid_part}. "
                "Dispatch refuses to reuse a task-id in any state. "
                "Use a unique --task-id; --force-new can archive only "
                "the caller's own terminal record+result.",
                file=sys.stderr,
            )
            return 2
        # Only the hot record establishes ownership. Archived siblings are
        # history and may belong to earlier runs by another initiator.
        prior_status = existing.get("status") if existing else None
        prior_initiator = existing.get("initiator") if existing else None
        if (record_exists or result_exists) and (
            prior_status not in _RUNTIME_TMP_TERMINAL_STATUSES
            or prior_initiator in (None, "unknown")
            or prior_initiator != attribution.initiator
        ):
            print(
                f"❌ task_id {task_id!r} cannot be reused with --force-new: "
                f"prior status {prior_status!r} must be terminal and prior initiator "
                f"{prior_initiator!r} must match a known caller {attribution.initiator!r}. "
                "The prior record and result were not archived.",
                file=sys.stderr,
            )
            return 2
        try:
            archived = _archive_task_artifacts(task_id)
        except OSError as exc:
            print(
                f"❌ failed to archive prior task artifacts for {task_id!r}: {exc}",
                file=sys.stderr,
            )
            return 1
        for dest in archived:
            print(f"📦 archived prior task artifact: {dest.name}", file=sys.stderr)

    # Resolve prompt: literal --prompt, or - for stdin, or --prompt-file.
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text()
    elif args.prompt == "-":
        prompt = early_prompt if sources_review_access is not None and not review_attempt else sys.stdin.read()
    elif args.prompt is not None:
        prompt = args.prompt
    else:
        print("❌ --prompt or --prompt-file is required", file=sys.stderr)
        return 2
    # What the caller handed in, before the lifecycle, worktree and research blocks are appended: a caller that
    # rendered the prompt to a file (the R3 adjudication) checks the task ran exactly that file.
    source_prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    if sources_review_access is not None:
        # Recheck the launch text, including a file changed since the early read.
        try:
            check_review_tool_requirements(prompt, sources_review_access)
        except ReviewToolRequirementsRefused as exc:
            print(f"❌ dispatch refused: {exc}", file=sys.stderr)
            return 2

    if review_attempt and review_contract is not None and source_prompt_sha256 != review_contract["prompt_sha256"]:
        # Admission checked the prompt file before any side effect; the file must still be that prompt (#9163).
        print(
            "❌ review attempt refused: review_prompt_changed: the prompt file changed after its admission "
            f"(admitted {review_contract['prompt_sha256']}, now {source_prompt_sha256}) (#9163)",
            file=sys.stderr,
        )
        return 2

    if advisory_admission.prompt_sha256 is not None and source_prompt_sha256 != advisory_admission.prompt_sha256:
        # The envelope was admitted for the prompt read at admission; the prompt run must be that text (#9275).
        print(
            f"❌ dispatch refused: {bounded_advisory.BINDING_MISMATCH}: the prompt changed after advisory admission "
            f"(admitted {advisory_admission.prompt_sha256}, now {source_prompt_sha256})",
            file=sys.stderr,
        )
        return 2

    if args.mode in {"workspace-write", "danger"} and prompt != early_prompt:
        dor_error, dor_record = _run_dor_preflight(prompt, dor_reason, dispatch_repo=fleet_repo.github)
        if dor_error:
            print(dor_error, file=sys.stderr)
            return 2

    # stdin prompts were unavailable to the earlier side-effect-free check.
    write_intent_error = _read_only_write_intent_error(mode=args.mode, prompt=prompt)
    if write_intent_error:
        print(write_intent_error, file=sys.stderr)
        return 2

    try:
        lifecycle_carrier, lifecycle_prompt = _load_task_lifecycle_carrier(getattr(args, "lifecycle_file", None))
    except (OSError, ValueError) as exc:
        print(f"❌ invalid --lifecycle-file: {exc}", file=sys.stderr)
        return 2
    # Kinds of the blocks delegate adds around the caller's prompt, in the order they appear in the final prompt (the
    # worktree block leads it, the lifecycle and research blocks follow it); recorded so a consumer can tell which
    # instructions the worker saw beyond the source prompt.
    prompt_blocks: list[str] = []
    if lifecycle_prompt:
        prompt += lifecycle_prompt
        prompt_blocks.append("lifecycle")

    # ADR-011 P3 research context — explicit --research-* flags only. Validate the
    # request-side caps up front (fail fast, before any worktree side effect) so a
    # direct CLI caller is bounded exactly like the API query layer.
    try:
        research_ctx = _build_research_context(args)
    except ResearchContextError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2

    if dispatch_agent == "agy" and getattr(args, "model", None):
        from agent_runtime.adapters.agy import AgyAdapter

        try:
            AgyAdapter()._resolve_model_flag(str(args.model))
        except ValueError as exc:
            print(f"❌ {exc}", file=sys.stderr)
            return 2

    if review_attempt and dispatch_agent != requested_agent:
        print(
            f"❌ review attempt refused: agent substitution from {requested_agent} to {dispatch_agent} (budget guard) is not allowed (#8517)",
            file=sys.stderr,
        )
        return 2

    if review_attempt:
        from scripts.agent_runtime.review_mcp import (
            SUPPORTED_HARNESSES,
            UNSUPPORTED_HARNESS_REASONS,
        )

        final_harness = requested_harness or dispatch_agent
        if final_harness in UNSUPPORTED_HARNESS_REASONS:
            print(
                f"❌ review attempt refused for {dispatch_agent}: {UNSUPPORTED_HARNESS_REASONS[final_harness]} (#8517)",
                file=sys.stderr,
            )
            return 2
        if final_harness not in SUPPORTED_HARNESSES:
            print(
                f"❌ review attempt refused for {dispatch_agent}: unsupported harness {final_harness!r} (#8517)",
                file=sys.stderr,
            )
            return 2

        if dispatch_agent == "cursor" or requested_harness == "cursor":
            has_worktree = False
            if worktree_arg:
                has_worktree = True
            elif validated_cwd is not None:
                candidate_cwd = validated_cwd
                if _resolve_verified_worktree_path(candidate_cwd):
                    has_worktree = True
            if not has_worktree:
                print(
                    "❌ review attempt for cursor requires a dispatch worktree; refusing primary checkout (#8517)",
                    file=sys.stderr,
                )
                return 2

    from agent_runtime.telemetry import _resolve_model_from_defaults

    resolved_model = _resolve_model_from_defaults(
        dispatch_agent,
        getattr(args, "model", None),
        harness=requested_harness,
    )
    gemini_review_error = gemini_review_verdict_dispatch_error(
        agent=str(dispatch_agent),
        require_review_verdict=bool(getattr(args, "require_review_verdict", False)),
        profile=getattr(args, "review_profile", None),
        pr_number=pr_number,
        branch=getattr(args, "branch", None),
        repo_root=str(_REPO_ROOT),
        model=getattr(args, "model", None),
        resolved_model=resolved_model,
        review=bool(getattr(args, "review", False))
        or str(getattr(args, "type", "") or "").strip().casefold() == "review",
        head_out=gemini_checked_heads,
        head_sha=getattr(args, "pinned_head", None) or pinned_head,
    )
    if gemini_review_error is not None:
        print(f"❌ {gemini_review_error}", file=sys.stderr)
        return 2

    try:
        _validate_dispatch_effort(dispatch_agent, getattr(args, "effort", None))
    except ValueError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2

    if requested_harness is not None and dispatch_agent != "kimi":
        print(
            "❌ --harness kimicc requires the effective dispatch agent to remain kimi; use --force-agent.",
            file=sys.stderr,
        )
        return 2

    _warn_kimicc_oauth_token_life(requested_harness, args.hard_timeout)

    try:
        _check_capacity_hint(dispatch_agent, args=args)
    except CapacityGuardRefuseError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2

    # Admission must precede placement forwarding: a VPS forward is itself a
    # spawn path, so a refused Cursor dispatch must never leave this process.
    if not bool(getattr(args, "dry_run", False)):
        placement, reason, host_id = decide_dispatch_placement(repo_root=_REPO_ROOT)
        if placement == "vps" and host_id:
            if review_attempt:
                print(
                    f"❌ review attempt refused: cannot forward to {host_id}; "
                    "the attempt ledger must stay on this host (#8517)",
                    file=sys.stderr,
                )
                return 2
            print(f"→ forwarding dispatch to {host_id} (run_nonce={run_nonce})", file=sys.stderr)
            forward_error: BaseException | None = None
            forward_rc: int | None = None
            try:
                forward_rc = forward_dispatch(
                    host_id=host_id,
                    argv=sys.argv,
                    initiator=attribution.initiator,
                    initiator_source=attribution.source,
                    run_nonce=run_nonce,
                )
            except SshTransportError as exc:
                forward_error = exc
            except (ValueError, FileNotFoundError, OSError) as exc:
                forward_error = exc
            if not notebook_fallback_after_forward(forward_rc, error=forward_error):
                if forward_error is not None:
                    _record_forward_failure(
                        task_id=task_id,
                        run_nonce=run_nonce,
                        attribution=attribution,
                        agent=getattr(args, "agent", "unknown"),
                        mode=getattr(args, "mode", "read-only"),
                        prompt=early_prompt or "",
                        error=forward_error,
                        requested_model=getattr(args, "model", None),
                        requested_effort=getattr(args, "effort", None),
                        requested_harness=getattr(args, "harness", None),
                        worktree_path=getattr(args, "worktree", None),
                        worktree_branch=getattr(args, "branch", None),
                        worktree_base=worktree_base,
                        keep_worktree=bool(getattr(args, "keep_worktree", False)),
                        hard_timeout=getattr(args, "hard_timeout", DEFAULT_HARD_TIMEOUT_S),
                        silence_timeout=getattr(args, "silence_timeout", DEFAULT_SILENCE_TIMEOUT_S),
                        initial_response_timeout=getattr(
                            args, "initial_response_timeout", DEFAULT_INITIAL_RESPONSE_TIMEOUT_S
                        ),
                        max_budget_usd=getattr(args, "max_budget_usd", None),
                        require_review_verdict=bool(getattr(args, "require_review_verdict", False)),
                        output_schema_path=getattr(args, "output_schema", None),
                        substitution=agent_substitution,
                    )
                    refusal_msg = format_forward_config_refusal(forward_error, host_id=host_id)
                    print(refusal_msg, file=sys.stderr)
                    return 2
                return int(forward_rc or 0)
            why = str(forward_error) if forward_error is not None else f"ssh rc {forward_rc}"
            print(
                f"⚠️  VPS forward failed ({why}); spawning on notebook",
                file=sys.stderr,
            )
        elif reason in {"unavailable", "full"}:
            print(f"⚠️  every VPS worker host is {reason}; spawning on notebook", file=sys.stderr)

    # Host admission (#8645 part A) for the host that spawns the worker, so it
    # follows VPS forwarding. This check fails fast before the base fetch; the
    # authoritative one runs under the admission lock just before the first
    # worktree or task-record side effect. Dry-run reports dead-pid records
    # without marking them.
    try:
        admission = _evaluate_dispatch_admission(args.mode, sweep=not bool(getattr(args, "dry_run", False)))
    except ValueError as exc:
        print(f"❌ invalid dispatch admission threshold: {exc}", file=sys.stderr)
        return 2
    admission_rc = _report_dispatch_admission(admission, force_reason=force_admission_reason)
    if admission_rc is not None:
        return admission_rc

    try:
        output_schema_path, output_schema_sha256 = _resolve_output_schema(
            getattr(args, "output_schema", None),
            agent=dispatch_agent,
        )
    except ValueError as exc:
        print(f"❌ invalid --output-schema: {exc}", file=sys.stderr)
        return 2

    # Resolve the immutable worktree base once before ownership admission.
    resolved_worktree_base_sha: str | None = None
    resolved_worktree_raw: str | None = None
    rebase_onto: str | None = None
    if worktree_arg and not (detached_read_only and bool(getattr(args, "dry_run", False))):
        resolved_worktree_raw = (
            str(_auto_worktree_path(dispatch_agent, task_id, repo_root=target_repo_root))
            if worktree_arg == "auto"
            else worktree_arg
        )
        try:
            if not bool(getattr(args, "dry_run", False)):
                # Attach is lock -> verify the checkout -> mutate -> publish the
                # task record. The lock is taken before _resolve_worktree_base_sha
                # can rebase an existing checkout and held until the record naming
                # the worktree is published, so no removal can land in between.
                # A removal that finished first leaves a missing path, which the
                # checks below treat as a fresh worktree (#8610).
                worktree_locks.enter_context(
                    worktree_lock(
                        validated_worktree
                        or _normalize_worktree_path(resolved_worktree_raw, repo_root=target_repo_root)
                    )
                )
            # #8775: an explicit path is locked as validated, then re-checked
            # before the base-SHA and worktree helpers run; they use it as is.
            changed_error = validated_worktree and _validated_path_changed_error("--worktree", validated_worktree)
            if changed_error:
                raise ValueError(changed_error.removeprefix("❌ "))
            # A3 (#9739): under the lock and before any rebase, the admitted
            # branch head must still be the head the authors were read from;
            # a checkout reaped meanwhile becomes a fresh worktree, admitted again.
            try:
                authoring_admission, moved = _authoring_recheck_under_lock(authoring_admission, readmit=admit_authoring)
            except _AuthoringReviewRefused as exc:
                print(exc.render(), file=sys.stderr)
                return 2
            if moved:
                print(moved.render(), file=sys.stderr)
                return 2
            # A Kimi worktree is never rebased: it must stay at the commit the gate read.
            allow_rebase = not bool(getattr(args, "dry_run", False)) and kimi_start_commit is None
            if (
                allow_rebase
                and authoring_admission is not None
                and authoring_admission.kind == "existing-worktree"
                and not requested_branch
                and not review_dependencies
            ):
                # A7: the auto-rebase of a reused worktree is admitted before it
                # runs, and runs onto exactly the commit admitted.
                try:
                    rebase_onto = _authoring_rebase_plan(authoring_admission, base=worktree_base)
                except _AuthoringReviewRefused as exc:
                    print(exc.render(), file=sys.stderr)
                    return 2
            if authoring_admission is not None and authoring_admission.creation_sha is not None:
                # A7: a new worktree starts at the commit admission enumerated from,
                # never at a base dereferenced again.
                resolved_worktree_base_sha = authoring_admission.creation_sha
            elif fleet_repo.default:
                resolved_worktree_base_sha = _resolve_worktree_base_sha(
                    agent=dispatch_agent,
                    task_id=task_id,
                    raw_path=resolved_worktree_raw,
                    validated_path=validated_worktree,
                    base=worktree_base,
                    branch=requested_branch,
                    detached=detached_read_only,
                    allow_rebase=allow_rebase,
                    rebase_onto=rebase_onto,
                    review_dependencies=review_dependencies,
                    continuation_head_sha=(
                        authoring_admission.head_sha
                        if authoring_admission is not None and authoring_admission.record.get("local_continuation")
                        else None
                    ),
                    continuation_remote_sha=(
                        (authoring_admission.record.get("local_continuation") or {}).get("remote_head_sha")
                        if authoring_admission is not None
                        else None
                    ),
                    pinned_head_sha=(
                        getattr(args, "pinned_head", None)
                        or (gemini_checked_heads[-1] if gemini_checked_heads else None)
                    ),
                )
            else:
                # Sibling repos resolve the base SHA at create time inside
                # _ensure_sibling_repo_worktree (simple origin fetch).
                resolved_worktree_base_sha = None
        except (ValueError, RuntimeError) as exc:
            if not bool(getattr(args, "dry_run", False)):
                _record_worktree_prep_failure(
                    task_id=task_id,
                    run_nonce=run_nonce,
                    attribution=attribution,
                    agent=dispatch_agent,
                    mode=args.mode,
                    prompt=prompt,
                    error=exc,
                    requested_model=args.model,
                    requested_effort=getattr(args, "effort", None),
                    requested_harness=requested_harness,
                    lifecycle_carrier=lifecycle_carrier,
                    worktree_path=resolved_worktree_raw,
                    worktree_branch=requested_branch,
                    worktree_base=worktree_base,
                    agent_alias_note=agent_alias_note,
                    output_schema_path=output_schema_path,
                    output_schema_sha256=output_schema_sha256,
                    keep_worktree=keep_worktree,
                    hard_timeout=args.hard_timeout,
                    silence_timeout=silence_timeout,
                    initial_response_timeout=initial_response_timeout,
                    max_budget_usd=max_budget_usd,
                    require_review_verdict=bool(getattr(args, "require_review_verdict", False)),
                    substitution=agent_substitution,
                )
            failed_step = "lock worktree" if isinstance(exc, WorktreeLockError) else "resolve immutable worktree base"
            print(f"❌ failed to {failed_step} for {task_id!r}: {exc}", file=sys.stderr)
            return 1

    # A3, A7 (#9739): the head the worker gets is the admitted one: commits pushed
    # to an attached --branch since admission were never checked, and a reused
    # worktree's auto-rebase must have produced the planned head.
    if resolved_worktree_base_sha is not None:
        moved = _authoring_target_moved(
            authoring_admission, resolved=resolved_worktree_base_sha, rebase_onto=rebase_onto
        )
        if moved:
            print(moved.render(), file=sys.stderr)
            return 2

    # The base resolved under the worktree lock must be the commit the Kimi gate read.
    if kimi_start_commit is not None and worktree_arg and resolved_worktree_base_sha != kimi_start_commit:
        from scripts.agent_runtime.kimi_admission import format_refusal

        drift = f"the worktree base {resolved_worktree_base_sha} is not the commit {kimi_start_commit} its owned paths were read at"
        print(f"❌ {format_refusal(dispatch_agent, [drift + '; retry the dispatch'])}", file=sys.stderr)
        return 2

    # Writable-path admission guard (#5643 Δ2-A WARN; #5645 REFUSE later).
    # Claims use the enforced commit scope (--owned-path), not research
    # classification paths, which neither grant nor restrict writes (#10015).
    # Runs before task-state write / worktree / branch side effects so a refuse
    # leaves no residue. Read-only modes are exempt inside the helper.
    # Dry-run must leave zero residue (same contract as tmp-lease reap) — skip
    # the shared ownership ledger entirely (Claude CF #5649 r11).
    if not bool(getattr(args, "dry_run", False)):
        try:
            from scripts.guardrails.delegate_ownership import (
                GuardMode,
                admit_write_paths,
                env_guard_mode,
            )
        except ImportError:  # pragma: no cover - flat script path
            from guardrails.delegate_ownership import (  # type: ignore
                GuardMode,
                admit_write_paths,
                env_guard_mode,
            )

        guard_mode = env_guard_mode()
        try:
            ownership = admit_write_paths(
                task_id=task_id,
                mode=str(args.mode),
                owned_paths=_declared_owned_paths(getattr(args, "owned_path", None)),
                allow_path_overlap=getattr(args, "allow_path_overlap", None),
                pid=os.getpid(),
                guard_mode=guard_mode,
            )
        except Exception as own_exc:
            # WARN (opt-in via DELEGATE_OWNERSHIP_MODE=warn): never crash on ledger I/O.
            # REFUSE (default after #5645): fail closed so conflicts cannot proceed.
            print(
                f"⚠️  write-path ownership: ledger error: {own_exc}",
                file=sys.stderr,
            )
            if guard_mode == GuardMode.REFUSE:
                print(
                    f"❌ write-path ownership refused (ledger error) for task_id={task_id!r}",
                    file=sys.stderr,
                )
                return 2
        else:
            if ownership.would_refuse or ownership.override_reason:
                # Only report a conflict count when there ARE conflicts: an
                # unprovable-disjointness refusal has none, and printing
                # "conflicts=0" next to it reads as a guard bug (#5340-adjacent).
                suffix = f" (conflicts={len(ownership.conflicts)})" if ownership.conflicts else ""
                print(
                    f"⚠️  write-path ownership: {ownership.reason}{suffix}",
                    file=sys.stderr,
                )
            if not ownership.admitted:
                print(
                    f"❌ write-path ownership refused for task_id={task_id!r}: {ownership.reason}",
                    file=sys.stderr,
                )
                return 2

    if getattr(args, "dry_run", False):
        dry_run_worktree: Path | None = None
        dry_run_branch: str | None = None
        dry_run_worktree_telemetry: dict[str, Any] = {}
        if detached_read_only:
            # A dry-run describes the eventual checkout without fetching the
            # base or creating a worktree. Both can spawn git subprocesses.
            dry_run_worktree = _auto_worktree_path(dispatch_agent, task_id, repo_root=target_repo_root)
        elif requested_branch:
            resolved_raw = str(_auto_worktree_path(dispatch_agent, task_id)) if worktree_arg == "auto" else worktree_arg
            assert resolved_raw is not None  # --branch above supplies the auto sentinel.
            try:
                (
                    dry_run_worktree,
                    dry_run_branch,
                    dry_run_worktree_telemetry,
                ) = _ensure_worktree(
                    agent=dispatch_agent,
                    task_id=task_id,
                    raw_path=resolved_raw,
                    validated_path=validated_worktree,
                    base=worktree_base,
                    branch=requested_branch,
                    detached=detached_read_only,
                    resolved_base_sha=resolved_worktree_base_sha,
                    dry_run=True,
                    full_checkout=full_checkout,
                    sparse_include=sparse_include,
                    review_dependencies=review_dependencies,
                )
            except (ValueError, RuntimeError) as exc:
                print(f"❌ failed to validate branch reuse for {task_id!r}: {exc}", file=sys.stderr)
                return 1
        elif validated_cwd is not None:
            candidate_cwd = validated_cwd
            resolved_wt = _resolve_verified_worktree_path(candidate_cwd)
            if resolved_wt:
                dry_run_worktree = resolved_wt
                dry_run_branch = _current_branch(resolved_wt)
                dry_run_worktree_telemetry["base_sha"] = _resolve_sha(resolved_wt)

        try:
            runtime_tmp_root, runtime_tmp_namespace_root = _create_runtime_tmp_lease(task_id)
        except RuntimeError as exc:
            print(f"❌ failed to create runtime tmp lease for {task_id!r}: {exc}", file=sys.stderr)
            return 1

        try:
            start_telemetry = resolve_dispatch_start_telemetry(
                agent_name=dispatch_agent,
                requested_model=args.model,
                requested_effort=getattr(args, "effort", None),
                harness=requested_harness,
                probe_cli_version=not (review_attempt and review_access == "full"),
            )
            dry_run_state = {
                "pinned_head": pinned_head,
                "review_author_model": getattr(args, "review_author_model", None),
                "review_risk": getattr(args, "review_risk", None),
                "review_profile": getattr(args, "review_profile", None),
                "review_language_lane": _dispatch_is_language_lane(args)
                or is_ukrainian_review(vars(args)),
                "task_id": task_id,
                "run_nonce": run_nonce,
                "repository": _resolve_dispatch_repository(
                    dry_run_worktree or (Path(args.cwd) if args.cwd else _REPO_ROOT)
                ),
                "initiator": attribution.initiator,
                "attribution_source": attribution.source,
                "agent": dispatch_agent,
                "model": start_telemetry.model,
                **_cursor_model_state(agent=dispatch_agent, initial=True),
                **_deepseek_model_state(agent=dispatch_agent, model=start_telemetry.model),
                "effort": start_telemetry.effort,
                "cli_version": start_telemetry.cli_version,
                "mode": args.mode,
                "cwd": str(dry_run_worktree or (Path(args.cwd) if args.cwd else _REPO_ROOT)),
                "worktree_path": str(dry_run_worktree) if dry_run_worktree else None,
                "worktree_branch": dry_run_branch,
                "worktree_base_sha": dry_run_worktree_telemetry.get("base_sha"),
                "runtime_tmp_root": str(runtime_tmp_root),
                "output_schema_path": output_schema_path,
                "output_schema_sha256": output_schema_sha256,
                "tmp_bytes_freed": None,
                "tmp_reap_error": None,
                "pid": None,
                "status": "dry_run",
                "started_at": datetime.now(UTC).isoformat(),
                "finished_at": None,
                "duration_s": None,
                "prompt_chars": len(prompt),
                "response_chars": None,
                "result_file": None,
                "stderr_excerpt": None,
                "returncode": None,
                "returncode_reason": None,
                "last_error": None,
                "exit_code": None,
                "substitution": agent_substitution,
                "agent_alias_note": agent_alias_note,
            }
            if mechanical_task := _mechanical_task_scope(args, admitted=True):
                dry_run_state["mechanical_task"] = mechanical_task
            if routing.budget_diagnostics:
                dry_run_state["routing_facts"] = routing.budget_diagnostics
            if requested_harness is not None:
                dry_run_state["harness"] = requested_harness
            if not admission.exempt:
                dry_run_state["admission"] = admission.to_record(force_reason=force_admission_reason)
            if lifecycle_carrier is not None:
                dry_run_state["task_lifecycle"] = lifecycle_carrier
            dry_run_state.update(_authoring_review_state_fields(args, authoring_admission))
            dry_run_state.update(advisory_admission.state_fields())
            if primary_read_only_cwd:
                dry_run_state["read_only_primary_cwd"] = True
            dry_run_reap = _reap_runtime_tmp_lease(
                runtime_tmp_root,
                runtime_tmp_namespace_root,
            )
            dry_run_state.update(
                {
                    "finished_at": datetime.now(UTC).isoformat(),
                    "duration_s": 0.0,
                    "tmp_bytes_freed": dry_run_reap["tmp_bytes_freed"],
                    "tmp_reap_error": dry_run_reap["tmp_reap_error"],
                }
            )
            _write_state_atomic(state_path, dry_run_state)
        except BaseException:
            _reap_runtime_tmp_lease(runtime_tmp_root, runtime_tmp_namespace_root)
            raise
        if requested_branch:
            print(
                f"🌲 branch reuse validated: branch={dry_run_branch} "
                f"path={dry_run_worktree} "
                f"base_sha={dry_run_worktree_telemetry.get('base_sha') or '?'} [reused]",
                file=sys.stderr,
            )
        print(task_id)
        print(run_nonce)
        return 0

    # Authoritative admission (#8645 part A, #8717): count → check → publish
    # the admission hold under one host-wide lock, so concurrent dispatches
    # cannot all pass the check above and then exceed the cap together. It
    # runs before the review attempt, log files, worktree and task record, so
    # a refusal leaves none of them. The hold names this dispatcher and keeps
    # the slot until the full task record replaces it before the spawn.
    admission_record: dict[str, Any] | None = None
    if not admission.exempt:
        admission_refusal: str | None = None
        try:
            with dispatch_admission.admission_lock(tasks_dir()):
                admission = _evaluate_dispatch_admission(args.mode, sweep=True, thresholds=admission.thresholds)
                if admission.admitted or force_admission_reason is not None:
                    admission_record = admission.to_record(force_reason=force_admission_reason)
                    _publish_admission_hold(task_id, run_nonce, mode=args.mode, admission=admission_record)
                    admission_holds.callback(_release_admission_hold, task_id, run_nonce)
                else:
                    admission_refusal = admission.refusal_line()
        except dispatch_admission.AdmissionLockTimeout as exc:
            admission_refusal = f"dispatch admission lock unavailable: {exc}; retry the dispatch"
        except (OSError, RuntimeError) as exc:
            print(f"❌ could not publish the admission hold for {task_id!r}: {exc}", file=sys.stderr)
            return 1
        if admission_refusal is not None:
            print(f"❌ {admission_refusal}", file=sys.stderr)
            return _ADMISSION_REFUSED_EXIT

    # Set up log files before provisioning a worktree. If this cheap
    # filesystem setup fails, dispatch exits before leaving worktree/branch
    # side effects behind.
    log_dir = tasks_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    stdout_log = log_dir / f"{task_id}.stdout.log"
    stderr_log = log_dir / f"{task_id}.stderr.log"
    # task_id may contain "/" (for example "codex/1885-foo"), which makes
    # the log path live under a per-agent subdir that log_dir.mkdir above
    # does not cover.
    stdout_log.parent.mkdir(parents=True, exist_ok=True)
    stderr_log.parent.mkdir(parents=True, exist_ok=True)
    # These file descriptors MUST outlive this function — Popen keeps
    # them open for the child process. A context manager would close
    # them the instant Popen returns, breaking the worker's output.
    # SIM115 doesn't understand this case.
    stdout_fd = open(stdout_log, "ab", buffering=0)  # noqa: SIM115
    stderr_fd = open(stderr_log, "ab", buffering=0)  # noqa: SIM115

    def discard_logs() -> None:
        """A refusal before any worker exists: close the logs and remove the ones still empty."""
        stdout_fd.close()
        stderr_fd.close()
        for log in (stdout_log, stderr_log):
            with contextlib.suppress(OSError):
                if log.stat().st_size == 0:
                    log.unlink()

    worktree_path: Path | None = None
    worktree_branch: str | None = None
    worktree_telemetry: dict[str, Any] = {}
    if worktree_arg:
        # Fix 4 (#1476): the sentinel ``auto`` (from bare ``--worktree``)
        # resolves to ``.worktrees/dispatch/{agent}/{task}/``. An explicit
        # path is the one resolved at validation (#8775).
        # #672 P2.1: sibling --repo roots the auto path under that checkout.
        resolved_raw = (
            str(_auto_worktree_path(dispatch_agent, task_id, repo_root=target_repo_root))
            if worktree_arg == "auto"
            else worktree_arg
        )
        try:
            # The worktree lock taken before base resolution is still held (#8610).
            changed_error = validated_worktree and _validated_path_changed_error("--worktree", validated_worktree)
            if changed_error:
                raise ValueError(changed_error.removeprefix("❌ "))
            if fleet_repo.default:
                worktree_path, worktree_branch, worktree_telemetry = _ensure_worktree(
                    agent=dispatch_agent,
                    task_id=task_id,
                    raw_path=resolved_raw,
                    validated_path=validated_worktree,
                    base=worktree_base,
                    branch=requested_branch,
                    detached=detached_read_only,
                    resolved_base_sha=resolved_worktree_base_sha,
                    full_checkout=full_checkout,
                    sparse_include=sparse_include,
                    run_nonce=run_nonce,
                    review_dependencies=review_dependencies,
                    read_only=args.mode == "read-only",
                )
            else:
                worktree_path, worktree_branch, worktree_telemetry = _ensure_sibling_repo_worktree(
                    repo_root=target_repo_root,
                    agent=dispatch_agent,
                    task_id=task_id,
                    raw_path=resolved_raw,
                    validated_path=validated_worktree,
                    base=worktree_base,
                    run_nonce=run_nonce,
                    detached=detached_read_only,
                )
                if fleet_repo_meta is not None:
                    worktree_telemetry["fleet_repo"] = fleet_repo_meta
            if not worktree_telemetry.get("reused"):
                from scripts.fleet.ignored_task_output import creation_inventory

                worktree_telemetry["ignored_output_baseline"] = creation_inventory(
                    worktree_path,
                    primary=_REPO_ROOT,
                    task_id=task_id,
                    run_nonce=run_nonce,
                )
        except (ValueError, RuntimeError) as exc:
            stdout_fd.close()
            stderr_fd.close()
            # Record the resolved absolute path like every other writer (#8610);
            # a path that cannot even be resolved is kept verbatim. A validated
            # explicit path is recorded as validated, not resolved again (#8775).
            try:
                failed_worktree_path = str(
                    validated_worktree or _normalize_worktree_path(resolved_raw, repo_root=target_repo_root)
                )
            except (OSError, RuntimeError, ValueError):
                failed_worktree_path = resolved_raw
            _record_worktree_prep_failure(
                task_id=task_id,
                run_nonce=run_nonce,
                attribution=attribution,
                agent=dispatch_agent,
                mode=args.mode,
                prompt=prompt,
                error=exc,
                requested_model=args.model,
                requested_effort=getattr(args, "effort", None),
                requested_harness=requested_harness,
                lifecycle_carrier=lifecycle_carrier,
                worktree_path=failed_worktree_path,
                worktree_branch=(
                    None if detached_read_only else requested_branch or _derive_worktree_branch(dispatch_agent, task_id)
                ),
                worktree_base_sha=resolved_worktree_base_sha,
                worktree_base=worktree_base,
                agent_alias_note=agent_alias_note,
                output_schema_path=output_schema_path,
                output_schema_sha256=output_schema_sha256,
                keep_worktree=keep_worktree,
                hard_timeout=args.hard_timeout,
                silence_timeout=silence_timeout,
                initial_response_timeout=initial_response_timeout,
                max_budget_usd=max_budget_usd,
                require_review_verdict=bool(getattr(args, "require_review_verdict", False)),
                substitution=agent_substitution,
                worktree_prep_cleanup=exc.cleanup if isinstance(exc, WorktreeAddFailed) else None,
                worktree_prep=exc.prep if isinstance(exc, WorktreeAddFailed) else None,
            )
            print(f"❌ failed to prepare worktree for {task_id!r}: {exc}", file=sys.stderr)
            if isinstance(exc, WorktreeAddFailed):
                print(
                    f"   worktree cleanup: {exc.cleanup.get('action')} — {exc.cleanup.get('reason')}",
                    file=sys.stderr,
                )
                if exc.cleanup.get("reserved_dir_left"):
                    print(
                        f"   reserved_dir_left: {exc.cleanup.get('path')} — left in place, never removed automatically",
                        file=sys.stderr,
                    )
                if exc.cleanup.get("needs_attention"):
                    print(
                        f"   needs_attention: {exc.cleanup['needs_attention']} — {exc.cleanup.get('command')}",
                        file=sys.stderr,
                    )
            return 1
    elif validated_cwd is not None:
        candidate_cwd = validated_cwd
        # #8775: the validated cwd is re-checked before the registered-worktree
        # lookup below and again under the lock. In write-capable modes (and
        # for a cursor review attempt) an earlier read-only lookup already ran
        # git in this path, before either re-check.
        changed_error = _validated_path_changed_error("--cwd", candidate_cwd)
        if changed_error:
            discard_logs()
            print(changed_error, file=sys.stderr)
            return 1
        resolved_wt = _resolve_verified_worktree_path(candidate_cwd)
        if args.mode == "read-only" and resolved_wt is None:
            discard_logs()
            print(f"❌ read-only cwd {candidate_cwd} is no longer a registered worktree", file=sys.stderr)
            return 1
        if resolved_wt:
            try:
                worktree_locks.enter_context(worktree_lock(resolved_wt))
            except WorktreeLockError as exc:
                discard_logs()
                print(f"❌ failed to lock worktree for {task_id!r}: {exc}", file=sys.stderr)
                return 1
            # A removal that held the lock may have taken the checkout while
            # this dispatch waited. Never fall back to the stale cwd: fail
            # before any task record is published or any worker spawned (#8610).
            # A symlink swapped in since validation is refused too (#8775).
            changed_error = _validated_path_changed_error("--cwd", candidate_cwd)
            if changed_error:
                discard_logs()
                print(changed_error, file=sys.stderr)
                return 1
            if _resolve_verified_worktree_path(candidate_cwd) != resolved_wt:
                discard_logs()
                print(
                    f"❌ worktree {resolved_wt} for {task_id!r} was removed while dispatch waited for its lock; "
                    f"refusing to spawn in {candidate_cwd}",
                    file=sys.stderr,
                )
                return 1
            try:
                _refuse_review_attempt_worktree_reuse(resolved_wt)
            except (OSError, ValueError, RuntimeError) as exc:
                discard_logs()
                print(f"❌ failed to reuse worktree for {task_id!r}: {exc}", file=sys.stderr)
                return 1
            moved = _authoring_bindings_moved(authoring_admission)
            if moved:
                discard_logs()
                print(moved.render(), file=sys.stderr)
                return 2
            worktree_path = resolved_wt
            worktree_branch = _current_branch(resolved_wt)
            worktree_telemetry["reused"] = True
            worktree_telemetry["layout"] = _classify_worktree_layout(resolved_wt)
            worktree_telemetry["base_sha"] = _resolve_sha(resolved_wt)
            worktree_telemetry["sparse"] = _apply_dispatch_sparse_checkout(
                resolved_wt,
                full_checkout=full_checkout,
                sparse_include=sparse_include,
            )
            _record_worktree_local_venv_warning(resolved_wt, worktree_telemetry)
            if args.mode == "read-only":
                # Still under the worktree lock: a link an earlier write-capable
                # dispatch provisioned must not reach the worker (#9421).
                try:
                    _provision_data_symlinks(resolved_wt, _REPO_ROOT, read_only=True)
                except RuntimeError as exc:
                    discard_logs()
                    print(f"❌ failed to reuse worktree for {task_id!r}: {exc}", file=sys.stderr)
                    return 1

    # A Kimi worker needs its own worktree, checked out at the commit the gate read. The
    # gate and the check above already hold this; this re-check under the worktree lock
    # catches a worktree changed meanwhile, before any task record, tmp lease or worker exists.
    if is_kimi_seat(dispatch_agent, model=getattr(args, "model", None)):
        from scripts.agent_runtime.kimi_admission import format_refusal

        kimi_head = _resolve_sha(worktree_path) if worktree_path is not None else None
        if kimi_head is None or (kimi_start_commit is not None and kimi_head != kimi_start_commit):
            discard_logs()
            where = f"is at {kimi_head}, not {kimi_start_commit}" if kimi_head else "is missing"
            print(f"❌ {format_refusal(dispatch_agent, [f'the worker worktree {where}'])}", file=sys.stderr)
            return 2

    if review_attempt:
        from scripts.agent_runtime.attempt_boundary import verify_full_review_tree
        from scripts.agent_runtime.review_mcp import prepare_review_attempt
        from scripts.review.isolation import ReviewIsolationError

        try:
            _refuse_review_scratch_in_worktree()
            review_input_paths = _review_attempt_input_paths(review_attempt)
            _lock_review_input_root(
                review_contract, worktree_locks, locked_worktree=worktree_path, inputs=review_input_paths
            )
            # A refused tree must not reserve the attempt id or create its ledger.
            if review_access == "full":
                verify_full_review_tree(Path(review_attempt), worktree_path or Path(args.cwd or _REPO_ROOT))
            review_plan = prepare_review_attempt(
                review_id=review_id,
                attempt_id=attempt_id,
                manifest_path=Path(review_attempt),
                harness=requested_harness or dispatch_agent,
                review_access=review_access,
                review_contract=review_contract,
                checkout_root=worktree_path or Path(args.cwd or _REPO_ROOT),
            )
        except (ReviewIsolationError, ValueError, FileExistsError, WorktreeLockError) as exc:
            stdout_fd.close()
            stderr_fd.close()
            # The remover takes the same lock; release dispatch's hold before
            # asking the guarded cleanup path to remove an unpublished tree.
            worktree_locks.close()
            if worktree_path is not None and worktree_telemetry.get("reused") is False:
                cleanup = _settle_worktree_reap(worktree_path, created_by_this_dispatch=True, settling_task_id=task_id)
                print(f"   review refusal cleanup: {cleanup}", file=sys.stderr)
            print(f"❌ {exc}", file=sys.stderr)
            return 2

    if review_plan is not None and worktree_path is not None:
        try:
            _mark_review_attempt_worktree(worktree_path, task_id)
        except (OSError, RuntimeError) as exc:
            stdout_fd.close()
            stderr_fd.close()
            print(f"❌ failed to mark review worktree for {task_id!r}: {exc}", file=sys.stderr)
            return 1

    try:
        runtime_tmp_root, runtime_tmp_namespace_root = _create_runtime_tmp_lease(task_id)
    except RuntimeError as exc:
        stdout_fd.close()
        stderr_fd.close()
        _record_worktree_prep_failure(
            task_id=task_id,
            run_nonce=run_nonce,
            attribution=attribution,
            agent=dispatch_agent,
            mode=args.mode,
            prompt=prompt,
            error=exc,
            requested_model=args.model,
            requested_effort=getattr(args, "effort", None),
            requested_harness=requested_harness,
            lifecycle_carrier=lifecycle_carrier,
            worktree_path=worktree_path,
            worktree_branch=worktree_branch,
            worktree_base_sha=worktree_telemetry.get("base_sha") or resolved_worktree_base_sha,
            worktree_base=worktree_base,
            agent_alias_note=agent_alias_note,
            output_schema_path=output_schema_path,
            output_schema_sha256=output_schema_sha256,
            keep_worktree=keep_worktree,
            hard_timeout=args.hard_timeout,
            silence_timeout=silence_timeout,
            initial_response_timeout=initial_response_timeout,
            max_budget_usd=max_budget_usd,
            require_review_verdict=bool(getattr(args, "require_review_verdict", False)),
            substitution=agent_substitution,
        )
        print(f"❌ failed to create runtime tmp lease for {task_id!r}: {exc}", file=sys.stderr)
        return 1

    spawned = False
    try:
        cwd = str(worktree_path or (Path(args.cwd) if args.cwd else _REPO_ROOT))
        # POINTERS ONLY: inject bounded research pointers + an on-demand fetch
        # instruction (never digest bodies) when an explicit context was supplied and
        # the registry is enabled. Fail-open — a disabled/malformed registry leaves the
        # prompt and state untouched.
        research_state: dict[str, Any] | None = None
        research_block = ""
        if research_ctx is not None:
            research_block, research_state = _resolve_research_injection(research_ctx, task_id)

        # #9275: the bounded worker reads its envelope (ceilings included); the
        # advisor reads the envelope output contract bound to the worker dispatch.
        advisory_block, advisory_block_kind = advisory_admission.prompt_block()
        # The rules core's presence was required at the top of the dispatch.
        prompt = _compose_dispatch_prompt(
            prompt,
            worktree_path=worktree_path,
            mode=args.mode,
            sparse_telemetry=worktree_telemetry.get("sparse")
            if isinstance(worktree_telemetry.get("sparse"), dict)
            else None,
            delegate_commits=is_kimi_seat(dispatch_agent, model=getattr(args, "model", None)),
            research_block=research_block,
            advisory_block=advisory_block,
            advisory_block_kind=advisory_block_kind,
            rules_seat=getattr(args, "rules_seat", None),
            blocks=prompt_blocks,
            agent=dispatch_agent,
            review_route=(review_attempt is not None),
        )
        effective_prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()

        start_telemetry = resolve_dispatch_start_telemetry(
            agent_name=dispatch_agent,
            requested_model=args.model,
            requested_effort=getattr(args, "effort", None),
            harness=requested_harness,
            probe_cli_version=not (review_attempt and review_access == "full"),
        )

        # Write initial state BEFORE forking so a fast caller can see it.
        # pid is filled in by the worker once it starts; for now we record
        # the parent PID as a placeholder (overwritten by worker).
        worktree_layout = worktree_telemetry.get("layout") if worktree_path else None
        initial_state = {
            "pinned_head": pinned_head,
            "review_author_model": getattr(args, "review_author_model", None),
            "review_risk": getattr(args, "review_risk", None),
            "review_profile": getattr(args, "review_profile", None),
            "review_language_lane": _dispatch_is_language_lane(args)
            or is_ukrainian_review(vars(args)),
            "task_id": task_id,
            "review": bool(getattr(args, "review", False))
            or str(getattr(args, "type", "") or "").strip().casefold() == "review",
            "run_nonce": run_nonce,
            # Authoritative repository identity for the Work projection's scoped
            # delegate join (#7083); None stays unclassified and fails closed.
            "repository": _resolve_dispatch_repository(cwd),
            "initiator": attribution.initiator,
            "attribution_source": attribution.source,
            "agent": dispatch_agent,
            "model": start_telemetry.model,
            **_cursor_model_state(agent=dispatch_agent, initial=True),
            **_deepseek_model_state(agent=dispatch_agent, model=start_telemetry.model),
            "effort": start_telemetry.effort,
            "cli_version": start_telemetry.cli_version,
            "allow_merge": bool(getattr(args, "allow_merge", False)),
            "require_review_verdict": bool(getattr(args, "require_review_verdict", False)),
            "mode": args.mode,
            "cwd": cwd,
            "worktree_path": str(worktree_path) if worktree_path else None,
            "worktree_branch": worktree_branch,
            "worktree_base_sha": worktree_telemetry.get("base_sha"),
            "worktree_base": worktree_base if worktree_path else None,
            "worktree_rebased": bool(worktree_telemetry.get("rebased")),
            "worktree_reused": bool(worktree_telemetry.get("reused")),
            "worktree_layout": worktree_layout,
            "worktree_sparse": worktree_telemetry.get("sparse"),
            "worktree_local_venv": worktree_telemetry.get("local_venv"),
            "ignored_output_baseline": worktree_telemetry.get("ignored_output_baseline"),
            "runtime_tmp_root": str(runtime_tmp_root),
            "tmp_bytes_freed": None,
            "tmp_reap_error": None,
            "keep_worktree": keep_worktree,
            "hard_timeout": args.hard_timeout,
            "silence_timeout": silence_timeout,
            "initial_response_timeout": initial_response_timeout,
            "max_budget_usd": max_budget_usd,
            "output_schema_path": output_schema_path,
            "output_schema_sha256": output_schema_sha256,
            "prompt_sha256": source_prompt_sha256,
            "effective_prompt_sha256": effective_prompt_sha256,
            "prompt_blocks": prompt_blocks,
            "dispatch_args_sha256": dispatch_args_hash,
            "pid": None,  # worker fills this
            "status": "spawning",
            "started_at": datetime.now(UTC).isoformat(),
            "finished_at": None,
            "duration_s": None,
            "prompt_chars": len(prompt),
            "response_chars": None,
            "result_file": None,
            "stderr_excerpt": None,
            "returncode": None,
            "returncode_reason": None,
            "last_error": None,
            "exit_code": None,
            "substitution": agent_substitution,
            "agent_alias_note": agent_alias_note,
            "dor_preflight": dor_record,
        }
        if routing.budget_diagnostics:
            initial_state["routing_facts"] = routing.budget_diagnostics
        if cursor_auto_admission is not None:
            # The Cursor adapter runs Auto only with this admission (#9274).
            initial_state[CURSOR_AUTO_ADMISSION_STATE_KEY] = cursor_auto_admission
        initial_state.update(_authoring_review_state_fields(args, authoring_admission))
        if requested_harness is not None:
            initial_state["harness"] = requested_harness
        if lifecycle_carrier is not None:
            initial_state["task_lifecycle"] = lifecycle_carrier
        if review_plan is not None:
            initial_state["worktree_disallow_reuse"] = True
            # Binds this task to its review attempt (#9022): the recorder attests a return's prompt hash only
            # from the task whose record names the same review, attempt and manifest.
            initial_state["review_attempt"] = {
                "review_id": review_id,
                "attempt_id": attempt_id,
                "manifest_sha256": review_plan.manifest_sha256,
            }
            # The render-time and dispatch-time digests compared (#9163): what the review of record ran against.
            initial_state["review_contract"] = review_contract
            initial_state["review_input_paths"] = [str(path) for path in review_input_paths]
            initial_state["review_access"] = review_access
        if mechanical_task := _mechanical_task_scope(args, admitted=True):
            initial_state["mechanical_task"] = mechanical_task
        initial_state = _with_optional_research_state(initial_state, research_state)
        # Auto-finalize's commit scope (#8991): the explicit --owned-path values,
        # verbatim. Never derived from --research-owned-path, which classifies
        # research context and is not commit authority. Omitted, not null, when
        # none were given: auto-finalize then commits nothing.
        declared_owned_paths = _declared_owned_paths(getattr(args, "owned_path", None))
        if declared_owned_paths is not None:
            initial_state["owned_paths"] = list(declared_owned_paths)
        if worktree_path is not None and not worktree_path.is_dir():
            _reap_runtime_tmp_lease(runtime_tmp_root, runtime_tmp_namespace_root)
            print(
                f"❌ worktree {worktree_path} for {task_id!r} disappeared before its task record was published",
                file=sys.stderr,
            )
            return 1
        # The admission hold published under the lock is replaced in place, so
        # the admitted slot stays held until the worker writes its pid (#8717).
        if admission_record is not None:
            initial_state["admission"] = admission_record
        # #9275: the launch handed to the worker below, recorded for its admission check.
        worker_execution = _worker_execution(
            args,
            cwd=cwd,
            silence_timeout=silence_timeout,
            initial_response_timeout=initial_response_timeout,
            max_budget_usd=max_budget_usd,
            harness=requested_harness,
        )
        initial_state.update(advisory_admission.state_fields(research_block=research_block, execution=worker_execution))
        if primary_read_only_cwd:
            initial_state["read_only_primary_cwd"] = True
        # #9275: the envelope admitted at route resolution must still be the
        # advisor's canonical result now, just before the worker is spawned.
        try:
            _recheck_advisory(advisory_admission, repo_root=target_repo_root)
        except bounded_advisory.AdvisoryRefused as exc:
            refusal = f"dispatch refused before spawn: {exc}"
            initial_state.update(
                {
                    "status": "failed",
                    "finished_at": datetime.now(UTC).isoformat(),
                    "stderr_excerpt": refusal[:500],
                    "returncode": None,
                    "returncode_reason": "advisory envelope changed before spawn; worker not started",
                    "last_error": exc.code,
                    "failure_reason": exc.code,
                    "exit_code": None,
                }
            )
            initial_state.update(_reap_runtime_tmp_lease(runtime_tmp_root, runtime_tmp_namespace_root))
            _record_final_branch_head(initial_state)
            _write_state_atomic(state_path, initial_state)
            worktree_locks.close()
            print(f"❌ {refusal}", file=sys.stderr)
            return 2
        _write_state_atomic(state_path, initial_state)
        # The published record now claims the worktree for settle's scan, so
        # the lock is released before the worker, whose own settle takes it
        # again, is spawned. The two acquisitions never nest (#8610).
        worktree_locks.close()

        # Fix 5 (#1476 AC 5) — dispatch-start telemetry.
        if worktree_path:
            sparse_meta = worktree_telemetry.get("sparse") or {}
            sparse_tag = ""
            if sparse_meta.get("full_checkout"):
                sparse_tag = " [full-checkout]"
            elif sparse_meta.get("excluded"):
                sparse_tag = f" [sparse-exclude={','.join(sparse_meta['excluded'])}]"
            print(
                f"🌲 dispatch {task_id}: run_nonce={run_nonce} branch={worktree_branch} "
                f"base_sha={worktree_telemetry.get('base_sha') or '?'} "
                f"path={worktree_path} layout={worktree_layout}"
                + (" [rebased]" if worktree_telemetry.get("rebased") else "")
                + (" [reused]" if worktree_telemetry.get("reused") else "")
                + sparse_tag,
                file=sys.stderr,
            )
            if worktree_layout == "flat":
                print(
                    f"⚠️  task {task_id!r} is using the DEPRECATED flat worktree "
                    f"layout ({worktree_path}). New dispatches should use "
                    f"`--worktree` (bare) to land in "
                    f".worktrees/dispatch/{{agent}}/{{task}}/.",
                    file=sys.stderr,
                )
        else:
            print(
                f"🌲 dispatch {task_id}: run_nonce={run_nonce}",
                file=sys.stderr,
            )

        # Fork a detached subprocess that runs this same script with
        # --worker. We use Popen rather than os.fork for portability.
        #
        # Python interpreter: the project rule (non-negotiable-rules.md)
        # is to always use .venv/bin/python. delegate.py follows that rule
        # strictly.
        venv_python = project_interpreter()
        python_bin = str(venv_python)
        cmd = [
            python_bin,
            str(Path(__file__).resolve()),
            "_worker",
            "--task-id",
            task_id,
            *_worker_route_argv(launch_target),
            "--mode",
            worker_execution["mode"],
            "--cwd",
            worker_execution["cwd"],
            "--hard-timeout",
            str(worker_execution["hard_timeout"]),
            "--silence-timeout",
            str(worker_execution["silence_timeout"]),
            "--initial-response-timeout",
            str(worker_execution["initial_response_timeout"]),
            "--runtime-tmp-root",
            str(runtime_tmp_root),
            "--runtime-tmp-namespace-root",
            str(runtime_tmp_namespace_root),
        ]
        cmd.extend(_dispatch_worker_identity_flags(args, worker_execution["harness"]))
        if keep_worktree:
            cmd.append("--keep-worktree")
        if worker_execution["finalize_open_pr"]:
            cmd.append("--finalize-open-pr")
        if worker_execution["max_budget_usd"] is not None:
            cmd.extend(["--max-budget-usd", str(worker_execution["max_budget_usd"])])
        if output_schema_path is not None:
            cmd.extend(
                [
                    "--output-schema",
                    output_schema_path,
                    "--output-schema-sha256",
                    str(output_schema_sha256),
                ]
            )
        if worker_execution["provider"]:
            cmd.extend(["--provider", worker_execution["provider"]])
        if worker_execution["effort"]:
            cmd.extend(["--effort", worker_execution["effort"]])
        if run_nonce:
            cmd.extend(["--run-nonce", run_nonce])
        if review_plan is not None:
            cmd.extend(
                [
                    "--review-access",
                    review_access,
                    "--review-id",
                    str(review_id),
                    "--attempt-id",
                    str(attempt_id),
                    "--mcp-config-path",
                    str(review_plan.config_path),
                    "--strict-mcp-config",
                    "--review-manifest",
                    review_attempt,
                    "--review-input-root",
                    str(review_input_root),
                ]
            )

        # Pipe the prompt via stdin so it doesn't hit argv length limits.
        # start_new_session=True detaches from our process group — the
        # worker survives our exit, which is what we want.
        worker_env = _build_worker_env(
            task_id=task_id,
            dispatch_agent=dispatch_agent,
            attribution=attribution,
            run_nonce=run_nonce,
            runtime_tmp_root=runtime_tmp_root,
            runtime_tmp_namespace_root=runtime_tmp_namespace_root,
            worktree_path=worktree_path,
            allow_merge=bool(getattr(args, "allow_merge", False)),
        )
        try:
            # Scoped when lu-dispatch.slice is really in force; plain Popen
            # otherwise. The recorded pid is the worker in both cases (#8645).
            proc, launch = dispatch_isolation.spawn_detached_worker(
                cmd,
                task_id=task_id,
                run_nonce=run_nonce,
                popen=subprocess.Popen,
                env=worker_env,
                stdin=subprocess.PIPE,
                stdout=stdout_fd,
                stderr=stderr_fd,
                stderr_log=stderr_log,
            )
            spawned = True
        except (OSError, FileNotFoundError, ValueError, dispatch_isolation.DispatchIsolationError) as exc:
            # Popen itself failed — typically because the Python
            # interpreter isn't where we expected, or the file
            # descriptors are somehow invalid. Without this handler
            # the state file would stay at "spawning" forever with
            # pid=None and no zombie detection could rescue it
            # (because zombie detection is gated on `pid and not alive`).
            # Codex 2026-04-10 audit finding.
            # A fallback refusal starts no worker. Other isolation errors can
            # mean a late marker or an unprovable exec; never relaunch those.
            fallback_refused = isinstance(exc, dispatch_isolation.DispatchIsolationError) and str(exc).startswith(
                "fallback-refused:"
            )
            if isinstance(exc, dispatch_isolation.DispatchIsolationError):
                spawn_error = f"dispatch isolation: {exc}"[:500]
                returncode_reason = (
                    "worker process was not started"
                    if fallback_refused
                    else "scoped worker startup was ambiguous; not relaunched"
                )
            else:
                spawn_error = f"Popen failed: {type(exc).__name__}: {exc}"[:500]
                returncode_reason = "worker process was not started"
            failed_state = _read_state(state_path) or initial_state
            if fallback_refused:
                failed_state["failure_reason"] = "dispatch_fallback_refused"
            spawn_code = (
                "dispatch_fallback_refused"
                if fallback_refused
                else "dispatch_isolation_failed"
                if isinstance(exc, dispatch_isolation.DispatchIsolationError)
                else "worker_spawn_failed"
            )
            failed_state.update(
                {
                    "status": "failed",
                    "finished_at": datetime.now(UTC).isoformat(),
                    "stderr_excerpt": spawn_error,
                    "returncode": None,
                    "returncode_reason": returncode_reason,
                    # The record writer renders the typed cause; the error text goes to the .diag (#9878).
                    "last_error": dataclasses.replace(_exception_cause(spawn_code, exc), diagnostic=spawn_error),
                    "exit_code": None,
                }
            )
            failed_state.update(
                _reap_runtime_tmp_lease(
                    runtime_tmp_root,
                    runtime_tmp_namespace_root,
                )
            )
            _record_final_branch_head(failed_state)
            _write_state_atomic(state_path, failed_state)
            print(
                f"❌ failed to spawn worker for {task_id!r}: {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            return 1

        # CRITICAL: write the Popen child's PID into the state file
        # RIGHT NOW, from the parent, before the worker has a chance
        # to run. Without this, if the worker crashes before reaching
        # _run_worker (e.g. top-level import error in delegate.py,
        # syntax error on a future edit, env var issue), the state
        # file stays at {"status": "spawning", "pid": null} forever
        # and no subsequent status/wait call can detect the crash
        # because zombie detection is gated on `pid and not _pid_alive(pid)`.
        # Fixed after Gemini review 2026-04-10.
        state_with_pid = _read_state(state_path) or initial_state
        state_with_pid["pid"] = proc.pid
        state_with_pid.update(launch.as_state())
        _write_state_atomic(state_path, state_with_pid)
        # Bind ownership ledger rows to the long-lived worker PID (not the
        # short-lived dispatch CLI). Best-effort: WARN path must not fail spawn.
        if str(args.mode) in _WRITE_CAPABLE_MODES:
            try:
                from scripts.guardrails.delegate_ownership import update_write_claim_pid
            except ImportError:  # pragma: no cover
                from guardrails.delegate_ownership import update_write_claim_pid  # type: ignore

            try:
                update_write_claim_pid(task_id, int(proc.pid))
            except Exception as own_exc:
                print(
                    f"⚠️  write-path ownership: failed to bind worker pid: {own_exc}",
                    file=sys.stderr,
                )

        assert proc.stdin is not None  # we passed stdin=PIPE
        try:
            proc.stdin.write(prompt.encode("utf-8"))
            proc.stdin.close()
        except BrokenPipeError:
            pass  # worker crashed before reading; zombie detector will catch it
    except BaseException:
        if not spawned:
            _reap_runtime_tmp_lease(runtime_tmp_root, runtime_tmp_namespace_root)
        raise
    finally:
        # The Popen child inherited these FDs via dup; our copies can
        # be closed immediately without affecting the child.
        stdout_fd.close()
        stderr_fd.close()

    # Return task-id and run_nonce on stdout so shell callers can capture them (#7168).
    print(task_id)
    print(run_nonce)
    return 0


# ---------------------------------------------------------------------------
# Status command — read state + detect zombies
# ---------------------------------------------------------------------------


def cmd_status(args: argparse.Namespace) -> int:
    state_path, state = _read_state_or_archived(args.task_id)
    if state is None:
        print(
            json.dumps({"error": f"no state file for task {args.task_id!r}"}),
        )
        return 1

    expected_nonce = getattr(args, "run_nonce", None)
    if expected_nonce is not None and state.get("run_nonce") != expected_nonce:
        print(
            json.dumps(
                {
                    "error": "stale_run_nonce",
                    "task_id": args.task_id,
                    "expected_run_nonce": expected_nonce,
                    "record_run_nonce": state.get("run_nonce"),
                    "status": "stale",
                }
            ),
            file=sys.stderr,
        )
        return 1

    # Detect zombies: if status is "running" but PID is dead, the worker
    # crashed (OOM, SIGKILL, reboot, etc.) and never got to update the
    # state file. Mark as "crashed" and persist the correction so
    # subsequent status calls get the right answer without redoing the check.
    _heal_dead_task(state_path, state, source="status")

    # Elapsed time for still-running tasks
    if state.get("status") == "running" and state.get("started_at"):
        try:
            started = datetime.fromisoformat(str(state["started_at"]).replace("Z", "+00:00"))
            state["elapsed_s"] = round(
                (datetime.now(UTC) - started).total_seconds(),
                1,
            )
        except (ValueError, TypeError):
            pass

    # Fix 4 (#1476): backfill worktree_layout for tasks persisted before
    # the field existed, and warn about flat-layout worktrees.
    if state.get("worktree_path") and not state.get("worktree_layout"):
        state["worktree_layout"] = _classify_worktree_layout(
            state.get("worktree_path"),
        )
    if state.get("worktree_layout") == "flat":
        print(
            f"⚠️  task {args.task_id!r} uses the DEPRECATED flat worktree "
            f"layout ({state.get('worktree_path')}). New dispatches should "
            f"use the `.worktrees/dispatch/{{agent}}/{{task}}/` subtree.",
            file=sys.stderr,
        )

    print(json.dumps(state, indent=2, default=str))
    return 0


class MonitorApiUnavailable(RuntimeError):
    """Raised when the local Monitor API cannot answer a task status query."""


class BudgetGuardRefuseError(RuntimeError):
    """Raised when --check-budget must refuse dispatch (hot/deficit/near_cap, no fallback)."""


class CapacityGuardRefuseError(RuntimeError):
    """Raised when Cursor driver lease admission must refuse a worker spawn."""


def _monitor_api_base_url() -> str:
    return os.environ.get("DELEGATE_MONITOR_API", _MONITOR_API_BASE_URL).rstrip("/")


def _dispatch_check_budget_enabled(args: argparse.Namespace) -> bool:
    """True when --check-budget is set or LU_DISPATCH_CHECK_BUDGET=1."""
    if getattr(args, "check_budget", False):
        return True
    return os.environ.get("LU_DISPATCH_CHECK_BUDGET", "").strip() in {"1", "true", "yes", "on"}


def _age_seconds_from_started_at(started_at: Any) -> int:
    try:
        started = datetime.fromisoformat(str(started_at).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return 0
    if started.tzinfo is None:
        started = started.replace(tzinfo=UTC)
    return max(0, round((datetime.now(UTC) - started.astimezone(UTC)).total_seconds()))


def _fetch_monitor_task(task_id: str, *, run_nonce: str | None = None) -> dict[str, Any] | None:
    quoted = urllib.parse.quote(task_id, safe="")
    url = f"{_monitor_api_base_url()}/api/delegate/tasks/{quoted}"
    if run_nonce:
        url += f"?run_nonce={urllib.parse.quote(run_nonce, safe='')}"
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        if exc.code == 409:
            return {"task": {"status": "stale_run_nonce", "task_id": task_id}, "alive": False, "stale_run_nonce": True}
        raise MonitorApiUnavailable(str(exc)) from exc
    except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise MonitorApiUnavailable(str(exc)) from exc
    return payload if isinstance(payload, dict) else {}


def _fetch_routing_budget() -> dict[str, Any]:
    url = f"{_monitor_api_base_url()}/api/state/routing-budget?fresh_codexbar=true"
    try:
        with urllib.request.urlopen(url, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise MonitorApiUnavailable(str(exc)) from exc
    return payload if isinstance(payload, dict) else {}


def _budget_lane_status(agent: str, agent_info: dict[str, Any]) -> str | None:
    if agent == "claude":
        return (agent_info.get("interactive") or {}).get("status") or agent_info.get("status")
    return agent_info.get("status")


def _budget_will_last_to_reset(agent_info: dict[str, Any]) -> bool | None:
    cb = agent_info.get("codexbar")
    if not isinstance(cb, dict) or "will_last_to_reset" not in cb:
        return None
    val = cb.get("will_last_to_reset")
    if val is None:
        return None
    return bool(val)


def _budget_cooler_lanes(agents: dict[str, Any], *, exclude: str) -> list[str]:
    cool: list[str] = []
    for lane, info in agents.items():
        if not isinstance(info, dict):
            continue
        lane_l = str(lane).strip().lower()
        if lane_l == exclude:
            continue
        deficit = credit_lane.pace_deficit_state(lane_l, info)
        status = deficit["status"] or _budget_lane_status(lane_l, info)
        if status in {"hot", "near_cap"} or deficit["uncovered"] is True:
            continue
        if status in {"cool", "warm"}:
            cool.append(lane_l)
    return sorted(cool)


def _budget_pace(agent_info: dict[str, Any]) -> dict[str, Any] | None:
    cb = agent_info.get("codexbar")
    return cb if isinstance(cb, dict) else None


def _budget_headroom_blocked(agent_info: dict[str, Any]) -> bool:
    runtime = agent_info.get("runtime")
    return isinstance(runtime, dict) and bool(runtime.get("headroom_blocked"))


def _budget_owner_facts(
    lane: str,
    info: dict[str, Any] | None,
    *,
    model: str | None,
    is_stale: bool,
    snapshot_metadata: Mapping[str, Any] | None = None,
) -> credit_lane.RoutingFacts:
    """The owner's reading (:func:`credit_lane.routing_facts`, #9740) of one lane for this dispatch.

    No model resolves to the lane default; none at all is never on a
    credit-period allowlist. ``snapshot_metadata`` is the snapshot's
    ``diagnostics`` (absent: the stale flag alone).
    """
    return credit_lane.routing_facts(
        lane,
        info,
        model=model or _lane_default_model(lane) or "",
        snapshot_metadata=snapshot_metadata if snapshot_metadata is not None else {"stale": is_stale},
    )


def _budget_needs_hard_capacity_action(
    *,
    status: str | None,
    will_last: bool | None,
    is_stale: bool,
    snapshot_metadata: Mapping[str, Any] | None = None,
    pace: dict[str, Any] | None = None,
    headroom_blocked: bool = False,
    lane: str = "",
    info: dict[str, Any] | None = None,
    model: str | None = None,
) -> tuple[bool, str]:
    """Return (needs_action, reason) for near_cap / hot / a real pace deficit.

    A stale snapshot is advisory (A2): never a hard action. Otherwise the
    decision is the owner's (:func:`credit_lane.routing_facts`, #9740) over the
    same lane record and snapshot ``diagnostics`` (``snapshot_metadata``):

    * near cap (the ``near_cap`` status, the owner's effective status or
      :func:`credit_lane.plan_window_exhausted`) hard-acts unless the owner
      grants credit relief for ``model``, whether or not the USD cost ledger
      has records;
    * a hot label hard-acts unless the owner cleared it: a weekly-pace label
      whose deficit is covered, whose pace is hidden below the visibility
      floor, or whose fresh pace reading finds no deficit (#9040: the
      early-window/on-pace false positive; A8). A hot label from any other
      source (Cursor Auto, ledger burn, a source-less record), or one set by
      runtime headroom, stays;
    * an uncovered pace deficit hard-acts.

    A bare ``will_last`` False still counts only when no pace dict was supplied.
    No model (none requested, no lane default) is never on a credit-period
    allowlist, so it gets no credit relief or coverage.
    """
    if is_stale:
        return False, ""
    if status == "hot" and headroom_blocked:
        return True, "status=hot"
    facts = _budget_owner_facts(lane, info, model=model, is_stale=is_stale, snapshot_metadata=snapshot_metadata)
    if "near_cap" in {status, facts.status} or credit_lane.plan_window_exhausted(lane, info):
        if facts.credit_relief:
            return False, ""
        remaining = facts.plan_remaining_pct
        where = f"{remaining:g}% remaining" if remaining is not None else ">90% used"
        return True, f"near_cap ({where} on FRESH snapshot)"
    if facts.covered_by:
        print(f"⚠ lane {lane}: {facts.pace_reason}", file=sys.stderr)
    if facts.uncovered is True:
        return True, "codexbar will_last_to_reset=False (deficit)"
    # The owner clears a qualifying weekly-pace hot label (#9040, A8); whatever it keeps hot hard-acts.
    if facts.status == "hot":
        return True, "status=hot"
    if pace is None and will_last is False:
        return True, "codexbar will_last_to_reset=False (deficit)"
    return False, ""


_LANGUAGE_LANES = frozenset({"claude", "codex", "agy"})
_SHA256_HEX_RE = re.compile(r"[0-9a-f]{64}")


def _advisory_flag_refusal(args: argparse.Namespace) -> str | None:
    """A typed refusal when the #9275 advisory flags are combined inconsistently; None otherwise."""
    advisory_task = getattr(args, "advisory_task", None)
    role = getattr(args, "advisory_role", None)
    binding = getattr(args, "advisory_binding", None)
    conflict = bounded_advisory.FLAG_CONFLICT
    if advisory_task is not None and not str(advisory_task).strip():
        return f"{conflict}: --advisory-task must name a task"
    if advisory_task is not None and role is not None:
        return f"{conflict}: --advisory-task (bounded worker) and --advisory-role (advisor) are exclusive"
    if advisory_task is not None and str(advisory_task).strip() == str(args.task_id):
        return f"{conflict}: --advisory-task must name another task, not this one"
    if (role is None) != (binding is None):
        return f"{conflict}: --advisory-role and --advisory-binding are required together"
    if binding is not None and not _SHA256_HEX_RE.fullmatch(str(binding)):
        return f"{conflict}: --advisory-binding must be a lowercase sha256 hex digest"
    if role is not None and getattr(args, "mode", "read-only") != "read-only":
        return f"{bounded_advisory.ADVISOR_ROUTE_REFUSED}: the advisor runs read-only, not {args.mode}"
    return None


@dataclass(frozen=True)
class _AdvisoryAdmission:
    """What #9275 admission decided for a dispatch: an advisor run, a bounded worker with its envelope, or neither."""

    requirement: str | None = None
    envelope: bounded_advisory.ValidatedEnvelope | None = None
    advisor_binding: str | None = None
    prompt_sha256: str | None = None  # the bounded worker's prompt text as bound at admission
    args: dict[str, Any] | None = None  # the argument half of the bounded worker's binding
    repo_root: Path | None = None  # where the envelope's owned paths were validated
    agent: str | None = None  # the admitted launch the bounded worker must run
    model_id: str | None = None
    exemption: dict[str, Any] | None = None  # a Gemini Flash launch classified Ukrainian

    def state_fields(self, *, research_block: str = "", execution: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Task-record fields; ``research_block`` is the research pointer block added to the worker prompt.

        ``execution`` is the launch handed to the worker (``_worker_execution``),
        recorded with the admitted agent and model as ``admitted_execution``;
        None for a dry run, which starts no worker.
        """
        if self.envelope is not None and self.requirement is not None:
            assert self.args is not None and self.prompt_sha256 is not None and self.repo_root is not None
            assert self.agent is not None and self.model_id is not None
            return {
                "advisory_envelope": self.envelope.state_record(
                    self.requirement,
                    args=self.args,
                    prompt_sha256=self.prompt_sha256,
                    repo_root=self.repo_root,
                    execution=(
                        None if execution is None else {"agent": self.agent, "model_id": self.model_id, **execution}
                    ),
                    research_block=research_block,
                )
            }
        if self.exemption is not None:
            return {"advisory_exemption": dict(self.exemption)}
        if self.advisor_binding is not None:
            return {
                "advisory_role": bounded_advisory.bounded_execution_policy().advisor_role,
                "advisory_route": bounded_advisory.ADVISOR_ROUTE,
                "advisory_binding_sha256": self.advisor_binding,
            }
        return {}

    def prompt_block(self) -> tuple[str, str | None]:
        """``(text, block kind)`` appended to the worker prompt; empty when neither role applies."""
        if self.envelope is not None:
            return bounded_advisory.worker_prompt_block(self.envelope), "advisory_envelope"
        if self.advisor_binding is not None:
            return bounded_advisory.advisor_prompt_block(self.advisor_binding), "advisory_contract"
        return "", None


def _worker_execution(
    args: argparse.Namespace,
    *,
    cwd: str,
    silence_timeout: int,
    initial_response_timeout: int,
    max_budget_usd: float | None,
    harness: str | None,
) -> dict[str, Any]:
    """The launch values ``cmd_dispatch`` hands the ``_worker`` argv, beside the admitted agent and model (#9275).

    A bounded worker compares each with what it runs (``EXECUTION_FIELDS``).
    """
    return {
        "mode": args.mode,
        "cwd": cwd,
        "effort": getattr(args, "effort", None) or None,
        "hard_timeout": args.hard_timeout,
        "silence_timeout": silence_timeout,
        "initial_response_timeout": initial_response_timeout,
        "max_budget_usd": max_budget_usd,
        "provider": getattr(args, "provider", None) or None,
        "harness": harness,
        "finalize_open_pr": bool(getattr(args, "finalize_open_pr", False)),
    }


def _admit_advisory(
    args: argparse.Namespace,
    *,
    dispatch_agent: str,
    launch_model: str | None,
    bound_args: dict[str, Any],
    repo_root: Path,
) -> _AdvisoryAdmission:
    """Admit the admitted route under #9275 or raise ``AdvisoryRefused``.

    ``dispatch_agent`` and ``launch_model`` are the admitted launch target, so
    aliases, ``--force-agent`` and budget substitution are already applied: a
    substitution into a bounded worker needs an envelope like a direct request.
    ``bound_args`` is the argument half of the binding, captured as parsed.
    """
    from scripts.agent_runtime.telemetry import _default_model_for
    from scripts.review.model_catalog import canonical_model_id

    policy = bounded_advisory.bounded_execution_policy()
    model_id = canonical_model_id(launch_model or _default_model_for(dispatch_agent))
    if getattr(args, "advisory_role", None) is not None:
        if model_id != policy.advisor_model_id:
            raise bounded_advisory.AdvisoryRefused(
                bounded_advisory.ADVISOR_ROUTE_REFUSED,
                f"--advisory-role runs on the advisor {policy.advisor_model_id}; the admitted route launches "
                f"{dispatch_agent} {launch_model or model_id!r}",
            )
        return _AdvisoryAdmission(advisor_binding=str(args.advisory_binding))
    declared = _declared_owned_paths(getattr(args, "owned_path", None)) or []
    research_paths = getattr(args, "research_owned_path", None) or []
    classified_paths = [*declared, *research_paths]
    mode = str(getattr(args, "mode", "") or "")
    task_family = getattr(args, "research_task_family", None)
    review_profile = getattr(args, "review_profile", None)
    requirement = bounded_advisory.bounded_requirement(
        model_id,
        mode=mode,
        task_family=task_family,
        review_profile=review_profile,
        owned_paths=classified_paths,
        repo_root=repo_root,
        policy=policy,
    )
    advisory_task = getattr(args, "advisory_task", None)
    if requirement is None:
        if advisory_task is not None:
            raise bounded_advisory.AdvisoryRefused(
                bounded_advisory.FLAG_CONFLICT,
                f"--advisory-task applies only to a bounded-worker dispatch; the admitted route launches "
                f"{dispatch_agent} {launch_model or model_id!r}",
            )
        if model_id == policy.bounded_fallback_model_id:
            # The worker re-classifies from this record before it starts the model.
            return _AdvisoryAdmission(
                exemption={
                    "model_id": model_id,
                    "task_family": task_family,
                    "review_profile": review_profile,
                    "mode": mode,
                    "classified_paths": [str(path) for path in classified_paths],
                }
            )
        return _AdvisoryAdmission()
    if advisory_task is None:
        raise bounded_advisory.AdvisoryRefused(
            bounded_advisory.ENVELOPE_REQUIRED,
            f"{requirement}; dispatch it with --advisory-task <task-id> naming a finished "
            f"{policy.advisor_model_id} advisory task (operator decision 2026-09-30, #9275)",
        )
    advisory_task = str(advisory_task).strip()
    try:
        prompt_sha256 = _binding_prompt_sha256(args, read_stdin=False)
    except OSError as exc:
        raise bounded_advisory.AdvisoryRefused(
            bounded_advisory.BINDING_MISMATCH, f"--prompt-file cannot be read for the advisory binding: {exc}"
        ) from None
    if prompt_sha256 is None:
        raise bounded_advisory.AdvisoryRefused(
            bounded_advisory.FLAG_CONFLICT,
            "a bounded dispatch binds its prompt text; pass --prompt or --prompt-file, not stdin",
        )
    envelope = bounded_advisory.load_envelope(
        advisory_task,
        state_path=_state_path_no_create(advisory_task),
        binding_sha256=advisory_binding(bounded_advisory.canonical_sha256(bound_args), prompt_sha256),
        repo_root=repo_root,
        policy=policy,
    )
    bounded_advisory.require_owned_paths_match(envelope.owned_paths, declared)
    return _AdvisoryAdmission(
        requirement=requirement,
        envelope=envelope,
        prompt_sha256=prompt_sha256,
        args=bound_args,
        repo_root=repo_root,
        agent=dispatch_agent,
        model_id=model_id,
    )


def _bounded_prompt_composer(
    record: Mapping[str, Any], *, agent: str, model: str | None, mode: str
) -> bounded_advisory.PromptComposer:
    """How ``_dispatch`` built this worker's prompt around a brief, rebuilt from the task record (#9275).

    The permitted dispatcher blocks are re-derived, never copied from the
    prompt: the rules core from this checkout and the bound ``--rules-seat``,
    the worktree block from the recorded worktree, the lifecycle block from
    the recorded carrier, the research block only when it re-renders from its
    own pointers, and the advisory block from the advisor's sealed envelope.
    """
    from scripts.agent_runtime.kimi_admission import is_kimi_seat

    def compose(brief: str, validated: bounded_advisory.ValidatedEnvelope, args: Mapping[str, Any]) -> str:
        carrier = record.get("task_lifecycle")
        lifecycle = ""
        if isinstance(carrier, dict):
            from scripts.orchestration import task_lifecycle

            lifecycle = task_lifecycle.render_carrier_prompt(carrier)
        worktree = record.get("worktree_path")
        sparse = record.get("worktree_sparse")
        admitted = record.get("advisory_envelope") or {}
        return _compose_dispatch_prompt(
            brief + lifecycle,
            worktree_path=Path(str(worktree)) if worktree else None,
            mode=mode,
            sparse_telemetry=sparse if isinstance(sparse, dict) else None,
            delegate_commits=is_kimi_seat(agent, model=model),
            research_block=_recorded_research_block(admitted.get("research_block")),
            advisory_block=bounded_advisory.worker_prompt_block(validated),
            advisory_block_kind="advisory_envelope",
            rules_seat=args.get("rules_seat"),
            agent=agent,
            review_route=(record.get("review_attempt") is not None),
        )

    return compose


def _verify_bounded_worker(
    task_id: str,
    *,
    agent: str,
    model: str | None,
    mode: str,
    cwd: Path,
    execution: Mapping[str, Any],
    prompt: str,
) -> str | None:
    """Re-verify this worker's #9275 admission against ``prompt``, the exact text it hands the provider.

    ``execution`` holds the other launch values the worker runs (effort,
    timeouts, budget, provider, harness, PR opening); each must be the admitted
    one. Reads the worker's own task record (never creating it). Returns the
    SHA-256 of the checked prompt for an envelope admission, None when the
    model is not bounded or runs under a Ukrainian exemption; raises
    ``AdvisoryRefused`` otherwise.
    """
    from scripts.agent_runtime.telemetry import _default_model_for
    from scripts.review.model_catalog import canonical_model_id

    record = _read_state_json(_state_path_no_create(task_id))
    return bounded_advisory.verify_worker_admission(
        record,
        agent=agent,
        model_id=canonical_model_id(model or _default_model_for(agent)),
        mode=mode,
        cwd=cwd,
        execution=execution,
        prompt=prompt,
        compose_prompt=_bounded_prompt_composer(record or {}, agent=agent, model=model, mode=mode),
        state_path_for=_state_path_no_create,
        default_repo_root=_REPO_ROOT,
    )


def _advisory_worker_refusal(
    task_id: str,
    *,
    agent: str,
    model: str | None,
    mode: str,
    cwd: Path,
    execution: Mapping[str, Any],
    prompt: str,
    runtime_tmp_root: str | None,
    runtime_tmp_namespace_root: str | None,
) -> str | None:
    """The worker-side #9275 backstop at start: a refusal when a bounded model lacks a valid parent admission.

    Runs ``_verify_bounded_worker`` before the worker marks itself running;
    the provider handoff runs it again on the exact prompt submitted. A
    refused worker with a task record marks it failed with the typed code; a
    hand-built worker argv with no record gets the refusal only.
    """
    try:
        _verify_bounded_worker(
            task_id, agent=agent, model=model, mode=mode, cwd=cwd, execution=execution, prompt=prompt
        )
    except bounded_advisory.AdvisoryRefused as exc:
        refusal = f"worker refused before start: {exc}"
        state_path = _state_path_no_create(task_id)
        record = _read_state_json(state_path)
        if record:
            record.update(
                {
                    "status": "failed",
                    "finished_at": datetime.now(UTC).isoformat(),
                    "stderr_excerpt": refusal[:500],
                    "returncode": None,
                    "returncode_reason": "bounded model without a valid advisory admission; provider not started",
                    "last_error": exc.code,
                    "failure_reason": exc.code,
                    "exit_code": None,
                }
            )
            record.update(_reap_runtime_tmp_lease(runtime_tmp_root, runtime_tmp_namespace_root))
            _write_state_atomic(state_path, record)
        return refusal
    return None


def _recheck_advisory(admission: _AdvisoryAdmission, *, repo_root: Path) -> None:
    """Refuse when the admitted envelope's advisor record or result changed before spawn (#9275)."""
    validated = admission.envelope
    if validated is None:
        return
    current = bounded_advisory.load_envelope(
        validated.advisor_task_id,
        state_path=_state_path_no_create(validated.advisor_task_id),
        binding_sha256=validated.binding_sha256,
        repo_root=repo_root,
    )
    bounded_advisory.require_unchanged(validated, current)


def _dispatch_is_language_lane(args: argparse.Namespace) -> bool:
    """True when the dispatch is Ukrainian language work.

    Signals: ``--language-lane``, ``--review-profile ukrainian``, a ``l2-uk*``
    research track, or an owned path under ``curriculum/``. Other lanes must
    not receive that work directly or through budget substitution (#8449).
    """
    if bool(getattr(args, "language_lane", False)):
        return True
    if getattr(args, "review_profile", None) == "ukrainian":
        return True
    track = str(getattr(args, "research_track", "") or "").strip().lower()
    if track.startswith("l2-uk"):
        return True
    owned = getattr(args, "research_owned_path", None) or []
    if isinstance(owned, str):
        owned = [owned]
    for path in owned:
        text = str(path).replace("\\", "/").lstrip("./")
        if text.startswith("curriculum/") or text.startswith("scripts/curriculum/"):
            return True
    return False


# Operator decision 2026-09-30 (#9274): Cursor Auto runs only a well-defined coding task,
# typed by the dispatch's declared functional role (``--research-role``). Any other role,
# or none, pins a concrete model.
CURSOR_AUTO_IMPLEMENTATION_ROLE = "implementation"
CURSOR_AUTO_ADMISSION_STATE_KEY = "cursor_auto_admission"


def _dispatch_is_review_typed(args: argparse.Namespace) -> bool:
    """True when a PR target or any review flag types this dispatch as a review.

    ``--review-author-model`` and ``--review-risk`` exist only for reviewer
    resolution, so either one types the dispatch as a (code-profile) review.
    """
    return (
        bool(getattr(args, "review", False))
        or getattr(args, "pr", None) is not None
        or bool(getattr(args, "review_attempt", None))
        or bool(getattr(args, "require_review_verdict", False))
        or bool(getattr(args, "review_profile", None))
        or bool(getattr(args, "review_author_model", None))
        or bool(getattr(args, "review_risk", None))
        or str(getattr(args, "type", "") or "").strip().casefold() == "review"
    )


def _cursor_auto_refusal(
    args: argparse.Namespace, *, agent: str, model: str | None, dor_record: dict[str, Any] | None
) -> str | None:
    """Refusal when the admitted launch asks Cursor for Auto outside a well-defined coding task.

    Auto needs positive evidence of that task: ``--research-role implementation``
    (the declared functional role; a missing or any other role is unclassified for
    Auto), a write-capable mode, at least one ``--owned-path``, a DoR preflight that
    checked an issue card and found it PASS (``--allow-dor-warn`` is not PASS), and no
    review typing. No ``--model`` is not Auto: the Cursor adapter pins its default.
    """
    from scripts.review.model_catalog import (
        CURSOR_AUTO_OUTSIDE_CODING_TASK_CODE,
        cursor_pinned_models,
        is_cursor_auto_selector,
    )

    if agent != "cursor" or not is_cursor_auto_selector(model):
        return None
    reasons: list[str] = []
    role = str(getattr(args, "research_role", None) or "").strip()
    if not role:
        reasons.append(f"the task is unclassified (no --research-role {CURSOR_AUTO_IMPLEMENTATION_ROLE})")
    elif role != CURSOR_AUTO_IMPLEMENTATION_ROLE:
        reasons.append(f"--research-role {role[:64]!r} is not {CURSOR_AUTO_IMPLEMENTATION_ROLE}")
    if args.mode not in _WRITE_CAPABLE_MODES:
        reasons.append(f"mode {args.mode} is not write-capable")
    if _dispatch_is_review_typed(args):
        reasons.append("the dispatch is review-typed")
    if not _declared_owned_paths(getattr(args, "owned_path", None)):
        reasons.append("no --owned-path")
    if not dor_record or not dor_record.get("issues"):
        reasons.append("no DoR issue card was checked")
    elif dor_record.get("warnings") or dor_record.get("allow_warn_reason") is not None:
        reasons.append("the DoR issue card is not PASS")
    if not reasons:
        return None
    pins = " or ".join(f"--model {pin}" for pin in cursor_pinned_models())
    return (
        f"❌ dispatch refused: {CURSOR_AUTO_OUTSIDE_CODING_TASK_CODE}: --agent cursor --model {model} runs only a "
        f"--research-role {CURSOR_AUTO_IMPLEMENTATION_ROLE} write dispatch with owned paths and a PASS DoR issue card ({'; '.join(reasons)}); "
        f"pin a concrete model: {pins} (operator decision 2026-09-30, #9274)"
    )


# #9739: a writer is admitted only while a qualified reviewer outside every
# author family (the incoming writer's included) remains under the live catalog
# floors. Typed reasons for the refusal; none can be overridden.
AUTHORING_REVIEW_NO_ROUTE = "AUTHORING_REVIEW_NO_ROUTE"
AUTHORING_REVIEW_AUTHORSHIP_UNKNOWN = "AUTHORING_REVIEW_AUTHORSHIP_UNKNOWN"
AUTHORING_REVIEW_SCOPE_UNKNOWN = "AUTHORING_REVIEW_SCOPE_UNKNOWN"
AUTHORING_REVIEW_TARGET_MOVED = "AUTHORING_REVIEW_TARGET_MOVED"
AUTHORING_REVIEW_CATALOG_UNKNOWN = "AUTHORING_REVIEW_CATALOG_UNKNOWN"
AUTHORING_REVIEW_REPOSITORY_MISMATCH = "AUTHORING_REVIEW_REPOSITORY_MISMATCH"
AUTHORING_REVIEW_STATE_KEY = "authoring_review_admission"
# A write dispatch that names no planned review risk is checked at the strictest
# risk; path inference may raise a declared risk, never lower it.
AUTHORING_REVIEW_DEFAULT_RISK = "critical"
# A7 (#9739): an open-PR lookup that returns this many rows may be truncated, so
# it is incomplete (M3).
AUTHORING_REVIEW_PR_LOOKUP_LIMIT = 100
_AUTHORING_COMMIT_SHA_RE = re.compile(r"[0-9a-f]{40}")


class _AuthoringReviewRefused(Exception):
    """Dispatch refused before a task record or a worker.

    The branch is untouched, except a refusal whose record binding is
    ``rebase``: that rebase has already run, and :meth:`render` says so.
    """

    def __init__(self, code: str, detail: str, record: dict[str, Any]) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.record = record

    def render(self) -> str:
        """The stderr refusal: one actionable line, then one JSON line for tools.

        A post-rebase refusal (``binding`` ``rebase``) has already moved the
        worktree. It names the pre-rebase head and the refs that still point
        at it. Every earlier refusal leaves the branch untouched.
        """
        payload = json.dumps({AUTHORING_REVIEW_STATE_KEY: {**self.record, "refusal": self.code}}, sort_keys=True)
        if self.record.get("binding") == "rebase":
            pre = self.record.get("pre_rebase_head") or self.record.get("admitted_sha") or ""
            refs = self.record.get("recovery_refs") or ("ORIG_HEAD", "HEAD@{1}")
            tail = (
                f"Worktree was rebased; pre-rebase head {pre}. "
                f"Recover it with {' or '.join(str(ref) for ref in refs)}. provider_calls=0."
            )
        else:
            tail = "Branch preserved; provider_calls=0."
        return f"❌ {self.code}: {self.detail} {tail}\n{payload}"


class _AuthoringObservationUnknown(Exception):
    """A review-target observation did not complete; the message names no private detail."""


@dataclass(frozen=True)
class _ReviewBase:
    """The commit the verdict recorder enumerates authors from, and what bound it (A7).

    ``source`` is ``pr`` (``--pr``), ``open-pr`` (the one open PR of the head
    branch) or ``default-branch`` (no open PR: the repository's actual default).
    """

    sha: str
    branch: str
    pr: int | None
    source: str

    def binding(self) -> tuple[str, str, int | None]:
        return (self.sha, self.branch, self.pr)

    def receipt(self, repository: str) -> dict[str, Any]:
        return {"repository": repository, "branch": self.branch, "pr": self.pr, "source": self.source}


@dataclass(frozen=True)
class _AuthoringAdmission:
    """The endpoints authoring-review admission froze, for the re-check under the worktree lock (A3, A7).

    ``head_sha`` is the commit authors were enumerated to: an existing target's
    head, or ``creation_sha`` for a new branch, which worktree creation then
    uses as is. ``review_base`` is the enumeration's lower end.
    """

    kind: str  # existing-worktree | existing-branch | new-branch
    head_sha: str
    checkout: Path | None
    branch: str | None
    pinned_head: str | None
    record: dict[str, Any]
    repository: str
    remote: str
    head_branch: str
    pr: int | None
    review_base: _ReviewBase
    default_branch: str
    creation_ref: str | None = None
    creation_sha: str | None = None
    # This writer's facts over ``base..head`` (raises ``_AuthoringReviewRefused``),
    # and the planned risk, for the rebase plan and its result (A7).
    collect: Callable[..., Any] | None = dataclasses.field(default=None, compare=False, repr=False)
    planned_risk: str | None = None


def _authoring_canonical_remote() -> str:
    """The remote serving the canonical GitHub repository, chosen as the fetch helpers choose it (#7522, M2)."""
    return _resolve_canonical_remote_name(_git_remote_urls(_REPO_ROOT)) or "origin"


def _authoring_default_branch(remote: str) -> tuple[str, str]:
    """The remote's actual default branch and its commit, from ``git ls-remote --symref`` (M4)."""
    try:
        proc = subprocess.run(
            ["git", "ls-remote", "--symref", remote, "HEAD"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_NETWORK_GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        raise _AuthoringObservationUnknown("the default-branch lookup timed out") from exc
    except OSError as exc:
        raise _AuthoringObservationUnknown("the default-branch lookup is unavailable") from exc
    name = sha = None
    for line in (proc.stdout or "").splitlines() if proc.returncode == 0 else ():
        value, _, ref = line.partition("\t")
        if ref.strip() != "HEAD":
            continue
        if value.startswith("ref: refs/heads/"):
            name = value.removeprefix("ref: refs/heads/").strip()
        elif _AUTHORING_COMMIT_SHA_RE.fullmatch(value.strip()):
            sha = value.strip()
    if not name or not sha:
        raise _AuthoringObservationUnknown("the canonical remote's default branch is unavailable")
    return name, sha


def _authoring_gh_json(command: list[str], *, what: str) -> Any:
    """One GitHub read; a failure is typed (timeout, quota, unavailable, malformed), never echoed."""
    try:
        proc = subprocess.run(command, capture_output=True, text=True, check=False, timeout=DEFAULT_GH_CLI_TIMEOUT_S)
    except subprocess.TimeoutExpired as exc:
        raise _AuthoringObservationUnknown(f"{what} timed out") from exc
    except OSError as exc:
        raise _AuthoringObservationUnknown(f"{what} is unavailable") from exc
    if proc.returncode != 0:
        detail = f"{proc.stderr or ''} {proc.stdout or ''}".casefold()
        if "rate limit" in detail or "http 429" in detail:
            raise _AuthoringObservationUnknown(f"{what} hit the GitHub API quota")
        raise _AuthoringObservationUnknown(f"{what} is unavailable")
    try:
        return json.loads(proc.stdout)
    except ValueError as exc:
        raise _AuthoringObservationUnknown(f"{what} returned a malformed answer") from exc


def _authoring_pr_base(row: Any, *, source: str, what: str) -> tuple[_ReviewBase, str]:
    """A PR row's review base and head branch; a row missing either is malformed."""
    if not isinstance(row, dict):
        raise _AuthoringObservationUnknown(f"{what} returned a malformed answer")
    number, base, base_sha, head = (row.get(key) for key in ("number", "baseRefName", "baseRefOid", "headRefName"))
    if (
        type(number) is not int
        or not isinstance(base, str)
        or not base.strip()
        or not isinstance(base_sha, str)
        or not _AUTHORING_COMMIT_SHA_RE.fullmatch(base_sha)
        or not isinstance(head, str)
    ):
        raise _AuthoringObservationUnknown(f"{what} returned a malformed answer")
    return _ReviewBase(base_sha, base.strip(), number, source), head


def _authoring_open_pr_bases(repository: str, head_branch: str) -> list[_ReviewBase]:
    """The review base of every open PR whose head is ``head_branch`` in ``repository`` itself (M3).

    A fork's branch of the same name belongs to another repository and is left
    out, so no outside fork can block a dispatch. A list at the lookup limit
    may be truncated and is refused as incomplete.
    """
    what = "the open-PR lookup"
    rows = _authoring_gh_json(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            repository,
            "--state",
            "open",
            "--head",
            head_branch,
            "--limit",
            str(AUTHORING_REVIEW_PR_LOOKUP_LIMIT),
            "--json",
            "number,headRefName,isCrossRepository,baseRefName,baseRefOid",
        ],
        what=what,
    )
    if not isinstance(rows, list):
        raise _AuthoringObservationUnknown(f"{what} returned a malformed answer")
    if len(rows) >= AUTHORING_REVIEW_PR_LOOKUP_LIMIT:
        raise _AuthoringObservationUnknown(f"{what} reached its limit, so it is incomplete")
    bases: list[_ReviewBase] = []
    for row in rows:
        cross = row.get("isCrossRepository") if isinstance(row, dict) else None
        if not isinstance(cross, bool):
            raise _AuthoringObservationUnknown(f"{what} returned a malformed answer")
        if cross:
            continue
        base, head = _authoring_pr_base(row, source="open-pr", what=what)
        if head != head_branch:
            raise _AuthoringObservationUnknown(f"{what} returned a malformed answer")
        bases.append(base)
    return bases


def _authoring_review_base(
    repository: str, *, pr: int | None, head_branch: str, default_branch: Callable[[], tuple[str, str]]
) -> _ReviewBase:
    """The base the verdict recorder will enumerate this branch's authors from (A7 §2).

    ``--pr``: that PR's ``baseRefOid``, once the PR is shown open, in this
    repository and headed by ``head_branch``. Otherwise the one open PR of
    ``head_branch``, or, when the lookup establishes there is none, the
    repository's actual default branch commit. A caller's ``--base`` never
    enters. Raises ``_AuthoringObservationUnknown`` when the binding cannot be
    established: unavailable, malformed, incomplete or ambiguous.
    """
    if pr is not None:
        what = f"the lookup of PR #{int(pr)}"
        row = _authoring_gh_json(
            [
                "gh",
                "pr",
                "view",
                str(int(pr)),
                "--repo",
                repository,
                "--json",
                "number,state,headRefName,isCrossRepository,baseRefName,baseRefOid",
            ],
            what=what,
        )
        base, head = _authoring_pr_base(row, source="pr", what=what)
        if row.get("state") != "OPEN" or row.get("isCrossRepository") is not False:
            raise _AuthoringObservationUnknown(f"PR #{int(pr)} is not an open PR headed in {repository}")
        if head != head_branch:
            raise _AuthoringObservationUnknown(f"PR #{int(pr)} is headed by another branch than {head_branch}")
        return base
    bases = _authoring_open_pr_bases(repository, head_branch)
    if len(bases) > 1:
        raise _AuthoringObservationUnknown(
            f"{len(bases)} open PRs are headed by {head_branch}, so the review base is ambiguous"
        )
    if bases:
        return bases[0]
    name, sha = default_branch()
    return _ReviewBase(sha, name, None, "default-branch")


def _authoring_start_commit(remote: str, ref: str, default: tuple[str, str]) -> str:
    """The commit a new branch would start at: ``ref`` on the canonical remote, or the observed default tip."""
    name, sha = default
    start = sha if ref == name else _ls_remote_branch_sha(remote, ref)
    if not start:
        raise _AuthoringObservationUnknown(f"start branch {ref} is not readable on the canonical remote")
    return start


def _authoring_commit_available(sha: str) -> bool:
    try:
        proc = subprocess.run(
            ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
            cwd=_REPO_ROOT,
            capture_output=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0


def _authoring_require_commit(sha: str, *, fetch: Callable[[], object], what: str, refresh: bool = False) -> None:
    """M1: make an observed commit local, fetching from the canonical remote at most once.

    The fetch only mirrors remote state into ``origin/<branch>``; the SHA stays
    the one observed and is never resolved from a ref again. ``refresh``
    fetches even when the commit is already local, keeping the tracking ref as
    current as the base fetch at worktree creation used to (the Kimi gate reads
    it, #9275).
    """
    if not refresh and _authoring_commit_available(sha):
        return
    # A failed fetch is judged by its outcome: the commit is still missing.
    with contextlib.suppress(RuntimeError, ValueError):
        fetch()
    if not _authoring_commit_available(sha):
        raise _AuthoringObservationUnknown(f"{what} {sha[:12]} is not available locally after fetching")


def _authoring_attach_head(
    *,
    kind: str,
    checkout: Path | None,
    branch: str | None,
    pinned_head: str | None,
    remote: str,
    observed_branch_head: str | None = None,
) -> str:
    """The head an attaching writer continues: the checkout's commit, or the branch on the canonical remote.

    A branch head is observed on the remote, never read from a possibly stale
    tracking ref (M2); a pinned head is the commit the dispatch was pinned to.
    Initial admission may reuse the early branch observation; rechecks omit it.
    """
    if kind == "existing-worktree":
        head = _resolve_sha(checkout) if checkout is not None and checkout.is_dir() else None
        if not head:
            raise _AuthoringObservationUnknown("the checkout's HEAD is unreadable")
        return head
    head = pinned_head or observed_branch_head or (_ls_remote_branch_sha(remote, branch) if branch else None)
    if not head:
        raise _AuthoringObservationUnknown(f"branch {branch} is not readable on the canonical remote")
    return head


def _git_common_dir_identity(path: Path) -> Path | None:
    """The repository ``path`` belongs to: git's absolute common directory, canonical; None outside git."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=path,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    common = (proc.stdout or "").strip() if proc.returncode == 0 else ""
    return Path(common).resolve() if common else None


def _is_other_repository(checkout: Path, repo_root: Path) -> bool:
    """True only when git proves ``checkout`` belongs to a repository other than ``repo_root``'s.

    Repository identity is the shared git common directory, never a path name:
    a sibling worktree laid out like one of the primary's still has its own
    common directory. Unresolvable identity is not proof of a sibling.
    """
    checkout_repo = _git_common_dir_identity(checkout)
    target_repo = _git_common_dir_identity(repo_root)
    return checkout_repo is not None and target_repo is not None and checkout_repo != target_repo


def _authoring_review_admission(
    args: argparse.Namespace,
    *,
    dispatch_agent: str,
    requested_harness: str | None,
    requested_branch: str | None,
    worktree_arg: str | None,
    validated_worktree: Path | None,
    validated_cwd: Path | None,
    target_repo_root: Path,
    repository: str,
    default_repo: bool,
    observed_branch_head: str | None = None,
) -> _AuthoringAdmission | None:
    """Admit a writer only if a qualified independent reviewer remains (#9739).

    Applies to every write-capable dispatch: an attach to an existing branch or
    worktree, and a new branch whose proposed scope is protected. Complete
    authorship (every branch-owned commit plus this
    writer, after substitution, aliases and ``--force-agent``) and protected
    scope come from ``record_cf_verdict.collect_branch_review_facts``, the
    calculation the verdict recorder uses. The check is structural (A2):
    catalog qualification, families, protected seats and the risk floor; it
    records reviewer availability as unknown. Authors are enumerated over
    ``review_base_sha..creation_sha`` for a new branch and
    ``review_base_sha..head_sha`` for an attach (A7): the review base is the
    one the recorder will read (:func:`_authoring_review_base`), never
    ``--base``; main-side commits are excluded from authorship while retaining
    the stale-base diff's protected scope (#9988). Every endpoint is observed on the canonical remote, frozen in
    the receipt and never resolved from a ref again. Fetches only to mirror
    remote state (M1); runs before any task record, archival, forwarding,
    rebase, worktree or provider. Returns None for read-only dispatches and
    for checkouts of a sibling repository (``--repo``, or a ``--cwd`` checkout
    whose git common directory is another repository's); a ``--repo`` whose
    ``--cwd`` belongs to a different repository is refused. Raises
    ``_AuthoringReviewRefused``, which no override flag bypasses.
    """
    if args.mode not in _WRITE_CAPABLE_MODES:
        return None
    from agent_runtime.telemetry import _resolve_model_from_defaults
    from scripts.review.model_catalog import ModelCatalogError

    planned_risk = getattr(args, "authoring_review_risk", None)
    writer_model = _resolve_model_from_defaults(dispatch_agent, getattr(args, "model", None), harness=requested_harness)
    record: dict[str, Any] = {
        "checked_at": datetime.now(UTC).isoformat(),
        "check": "structural",
        "reviewer_availability": "unknown",
        "planned_risk": planned_risk,
        "incoming_agent": dispatch_agent,
        "incoming_model": writer_model,
    }
    declared = _declared_owned_paths(getattr(args, "owned_path", None))
    if not declared:
        raise _AuthoringReviewRefused(
            AUTHORING_REVIEW_SCOPE_UNKNOWN,
            "write dispatch declares no --owned-path, so its review scope cannot be checked; "
            "pass every path this writer owns.",
            record,
        )
    cwd_only = (
        validated_cwd is not None and validated_worktree is None and worktree_arg != "auto" and not requested_branch
    )
    # Applicability follows the repository the writer's checkout belongs to,
    # never the --repo label alone: protected seats and risk floors describe the
    # default repository's own paths.
    if not default_repo and cwd_only:
        checkout_repo = _git_common_dir_identity(validated_cwd)
        if checkout_repo is None or checkout_repo != _git_common_dir_identity(target_repo_root):
            raise _AuthoringReviewRefused(
                AUTHORING_REVIEW_REPOSITORY_MISMATCH,
                f"--cwd is not a checkout of --repo {repository} (git common directory differs or is unknown); "
                "pass a --cwd worktree of that repository, or drop --repo for a checkout of this one.",
                record,
            )
    if not default_repo or (cwd_only and _is_other_repository(validated_cwd, target_repo_root)):
        record.update({"applicable": False, "reason": "sibling repository"})
        return None
    try:
        from scripts.review.record_cf_verdict import (
            FACTS_SCOPE_UNKNOWN,
            BranchFactsError,
            collect_branch_review_facts,
        )
        from scripts.review.security_paths import is_security_sensitive_change
    except (ImportError, ModelCatalogError) as exc:
        raise _AuthoringReviewRefused(
            AUTHORING_REVIEW_CATALOG_UNKNOWN, f"model catalog or reviewer resolver unavailable ({exc}).", record
        ) from exc

    checkout: Path | None = None
    if validated_worktree is not None:
        checkout = validated_worktree
    elif worktree_arg == "auto" or requested_branch:
        checkout = _auto_worktree_path(dispatch_agent, args.task_id, repo_root=target_repo_root)
    elif validated_cwd is not None:
        checkout = validated_cwd
    pinned_head = getattr(args, "pinned_head", None)
    if checkout is not None and checkout.exists():
        kind = "existing-worktree"
    elif requested_branch:
        kind, checkout = "existing-branch", None
    else:
        kind, checkout = "new-branch", None
    record.update({"target": kind, "branch": requested_branch})
    remote = _authoring_canonical_remote()
    pr = getattr(args, "pr", None)
    creation_ref: str | None = None
    creation_sha: str | None = None
    try:
        default_name, default_sha = _authoring_default_branch(remote)
        if kind == "existing-worktree":
            head_branch = _current_branch(checkout)
            if head_branch in (None, "HEAD"):
                raise _AuthoringObservationUnknown("the checkout has a detached HEAD, which names no PR")
        else:
            head_branch = requested_branch or _derive_worktree_branch(dispatch_agent, args.task_id)
        record["head_branch"] = head_branch
        # Authorship is enumerated from the base the verdict recorder will use,
        # never from --base, which only names where a new branch starts (A2, A7).
        review_base = _authoring_review_base(
            repository, pr=pr, head_branch=head_branch, default_branch=lambda: (default_name, default_sha)
        )
        record.update({"review_base": review_base.receipt(repository), "review_base_sha": review_base.sha})
        _authoring_require_commit(
            review_base.sha, fetch=lambda: _fetch_base(review_base.branch), what="the review base commit"
        )
        if kind == "new-branch":
            # The commit a new worktree starts at, frozen here and used as is by creation.
            base_arg = getattr(args, "base", None)
            creation_ref = _base_branch_name(base_arg) if base_arg else default_name
            creation_sha = _authoring_start_commit(remote, creation_ref, (default_name, default_sha))
            record.update({"creation_base": creation_ref, "creation_sha": creation_sha})
            _authoring_require_commit(
                creation_sha, fetch=lambda: _fetch_base(creation_ref), what="the creation commit", refresh=True
            )
            head = creation_sha
        else:
            head = _authoring_attach_head(
                kind=kind,
                checkout=checkout,
                branch=requested_branch,
                pinned_head=pinned_head,
                remote=remote,
                observed_branch_head=observed_branch_head,
            )
            _authoring_require_commit(
                head, fetch=lambda: _fetch_existing_branch(head_branch), what="the branch head commit"
            )
    except _AuthoringObservationUnknown as exc:
        raise _AuthoringReviewRefused(
            AUTHORING_REVIEW_AUTHORSHIP_UNKNOWN, f"{exc}, so the branch's authors are unknown; retry.", record
        ) from exc

    # A stale main PR base still determines scope, but main's newer commits
    # are not branch authors (#9988). Non-main target branches keep their
    # existing enumeration. The rebase plan and result use this same exclusion,
    # never the caller's --base or the rebase target.
    authorship_exclude = default_sha if review_base.branch == default_name else None
    record["authorship_exclude_sha"] = authorship_exclude
    if authorship_exclude is not None:
        try:
            _authoring_require_commit(
                authorship_exclude, fetch=lambda: _fetch_base(default_name), what="the authorship exclusion commit"
            )
        except _AuthoringObservationUnknown as exc:
            raise _AuthoringReviewRefused(AUTHORING_REVIEW_AUTHORSHIP_UNKNOWN, str(exc), record) from exc

    def collect(base_sha: str, head_sha: str, *, authorship_exclude_sha: str | None = authorship_exclude) -> Any:
        """This writer's branch facts over ``base_sha..head_sha``; a fact that cannot be established refuses."""
        try:
            return collect_branch_review_facts(
                repository=repository,
                repo_root=target_repo_root,
                base_tip_sha=base_sha,
                head_sha=head_sha,
                task_root=tasks_dir(),
                incoming_agent=dispatch_agent,
                incoming_model=writer_model,
                owned_paths=declared,
                subject_seats=tuple(getattr(args, "subject_seat", None) or ()),
                subject_families=tuple(getattr(args, "subject_family", None) or ()),
                authorship_exclude_sha=authorship_exclude_sha,
            )
        except BranchFactsError as exc:
            code = (
                AUTHORING_REVIEW_SCOPE_UNKNOWN
                if exc.code == FACTS_SCOPE_UNKNOWN
                else AUTHORING_REVIEW_AUTHORSHIP_UNKNOWN
            )
            raise _AuthoringReviewRefused(code, f"{exc} (head {head_sha[:12]}).", record) from exc

    facts = collect(review_base.sha, head)
    record.update(facts.receipt())
    if kind == "existing-worktree" and requested_branch:
        try:
            remote_head = observed_branch_head or _ls_remote_branch_sha(remote, requested_branch, strict=True)
            if not remote_head:
                raise _AuthoringObservationUnknown("the continuation's remote head is unavailable")
            _authoring_require_commit(
                remote_head, fetch=lambda: _fetch_existing_branch(requested_branch), what="the remote branch head"
            )
            if remote_head != head and _git_is_ancestor(remote_head, head):
                local = collect(remote_head, head, authorship_exclude_sha=remote_head)
                if local.existing_families != {facts.incoming_family}:
                    raise _AuthoringReviewRefused(
                        AUTHORING_REVIEW_AUTHORSHIP_UNKNOWN,
                        "local-only commits are not all by the incoming writer family; "
                        "reconcile the branch before continuation.",
                        record,
                    )
                record["local_continuation"] = {"remote_head_sha": remote_head, "head_sha": head}
        except _AuthoringObservationUnknown as exc:
            raise _AuthoringReviewRefused(AUTHORING_REVIEW_AUTHORSHIP_UNKNOWN, str(exc), record) from exc
    protected = bool(
        facts.subject_seats
        or facts.subject_families
        or is_security_sensitive_change(facts.changed_paths, facts.scope_paths)
    )
    record["protected_scope"] = protected
    admission = _AuthoringAdmission(
        kind=kind,
        head_sha=head,
        checkout=checkout,
        branch=requested_branch,
        pinned_head=pinned_head,
        record=record,
        repository=repository,
        remote=remote,
        head_branch=head_branch,
        pr=pr,
        review_base=review_base,
        default_branch=default_name,
        creation_ref=creation_ref,
        creation_sha=creation_sha,
        collect=collect,
        planned_risk=planned_risk,
    )
    if kind == "new-branch" and not protected:
        record["applicable"] = False
        return admission
    _authoring_require_route(facts, planned_risk=planned_risk, record=record, at=head)
    return admission


def _authoring_require_route(facts: Any, *, planned_risk: str | None, record: dict[str, Any], at: str) -> None:
    """Record the structural reviewer for ``facts``; refuse when none remains outside all authors (A2)."""
    from scripts.review.model_catalog import ModelCatalogError
    from scripts.review.record_cf_verdict import structural_review_route
    from scripts.review.security_paths import effective_review_risk

    risk = str(planned_risk or AUTHORING_REVIEW_DEFAULT_RISK).strip().casefold()
    try:
        resolution = structural_review_route(facts, risk=risk)
    except ModelCatalogError as exc:
        raise _AuthoringReviewRefused(
            AUTHORING_REVIEW_CATALOG_UNKNOWN, f"model catalog unavailable ({exc}).", record
        ) from exc
    record.update(
        {
            "applicable": True,
            "risk": effective_review_risk(risk, facts.changed_paths, facts.scope_paths),
            "reviewer": (
                {
                    "name": resolution.selected.name,
                    "model": resolution.selected.concrete_model,
                    "family": resolution.selected.family,
                    "route": resolution.selected.route,
                }
                if resolution.selected
                else None
            ),
        }
    )
    if resolution.selected is None:
        reason = resolution.fail_closed_reason or "no eligible formal reviewer in the catalog ladder"
        raise _AuthoringReviewRefused(
            AUTHORING_REVIEW_NO_ROUTE,
            f"write dispatch refused at {at[:12]}; authors={','.join(sorted(facts.existing_families)) or '(none)'}; "
            f"incoming={facts.incoming_family}; risk={record['risk']}; no qualified reviewer remains outside all "
            f"authors and protected seats ({reason}).",
            record,
        )


def _authoring_review_state_fields(args: argparse.Namespace, admission: _AuthoringAdmission | None) -> dict[str, Any]:
    """Task-record fields: the admission receipt, and explicit subjects the verdict recorder re-applies."""
    fields: dict[str, Any] = {}
    if admission is not None:
        fields[AUTHORING_REVIEW_STATE_KEY] = admission.record
    for flag, key in (("subject_seat", "review_subject_seats"), ("subject_family", "review_subject_families")):
        values = getattr(args, flag, None)
        if values:
            fields[key] = [values] if isinstance(values, str) else list(values)
    return fields


def _authoring_recheck_under_lock(
    admission: _AuthoringAdmission | None,
    *,
    readmit: Callable[[], _AuthoringAdmission | None],
) -> tuple[_AuthoringAdmission | None, _AuthoringReviewRefused | None]:
    """A3 and A7 under the worktree lock: the admission that now applies, and the refusal if a binding moved.

    A removal holding the lock may take the admitted checkout while dispatch
    waits (#8610); dispatch then creates a fresh worktree, so the observation
    is discarded and admission runs again in full for that target, freezing
    its own creation and review-base commits (becoming a new branch exempts
    nothing). Otherwise every frozen binding is observed again
    (:func:`_authoring_bindings_moved`). Raises ``_AuthoringReviewRefused``
    when the re-run refuses.
    """
    if (
        admission is not None
        and admission.kind == "existing-worktree"
        and admission.checkout is not None
        and not os.path.lexists(admission.checkout)
    ):
        return readmit(), None
    return admission, _authoring_bindings_moved(admission)


def _authoring_bindings_moved(admission: _AuthoringAdmission | None) -> _AuthoringReviewRefused | None:
    """A7: the refusal when an admitted endpoint differs before use; None when every binding is unchanged.

    Observed as at admission: an attached head (the checkout's commit, or the
    branch on the canonical remote), a new branch's start commit, and the
    review base with its branch and PR identity. An observation that cannot
    complete refuses as unknown authorship, never as a proven move. The base
    auto-rebase of a reused worktree runs after this and is not a move (A3).
    """
    if admission is None:
        return None
    default_branch = functools.cache(lambda: _authoring_default_branch(admission.remote))
    try:
        if admission.kind == "new-branch":
            assert admission.creation_ref is not None  # set for every new-branch admission
            current = _authoring_start_commit(admission.remote, admission.creation_ref, default_branch())
            moved = _authoring_drift(admission, "creation", current)
        else:
            current = _authoring_attach_head(
                kind=admission.kind,
                checkout=admission.checkout,
                branch=admission.branch,
                pinned_head=admission.pinned_head,
                remote=admission.remote,
            )
            moved = _authoring_drift(admission, "head", current)
            if not moved and admission.kind == "existing-worktree":
                # The checkout's branch names its PR and so its review base: a switch at
                # the same commit changes both (``HEAD`` when detached).
                assert admission.checkout is not None  # set for every existing-worktree admission
                moved = _authoring_branch_moved(admission, _current_branch(admission.checkout))
        if moved:
            return moved
        base = _authoring_review_base(
            admission.repository, pr=admission.pr, head_branch=admission.head_branch, default_branch=default_branch
        )
    except _AuthoringObservationUnknown as exc:
        return _AuthoringReviewRefused(
            AUTHORING_REVIEW_AUTHORSHIP_UNKNOWN,
            f"{exc} on re-checking the admitted target, so the branch's authors are unknown; retry.",
            admission.record,
        )
    if base.binding() == admission.review_base.binding():
        return None
    return _authoring_drift(admission, "review_base", base.sha, current_base=base)


def _authoring_branch_moved(admission: _AuthoringAdmission, current: str | None) -> _AuthoringReviewRefused | None:
    """The ``TARGET_MOVED`` refusal when the checkout no longer has the branch admission read; None when it does."""
    if current == admission.head_branch:
        return None
    now = "a detached HEAD" if current == "HEAD" else (current or "an unreadable branch")
    record = {
        **admission.record,
        "binding": "head_branch",
        "admitted_branch": admission.head_branch,
        "current_branch": current,
    }
    return _AuthoringReviewRefused(
        AUTHORING_REVIEW_TARGET_MOVED,
        f"the checkout's branch moved after authoring-review admission (admitted {admission.head_branch}, now {now}), "
        "so its PR and review base are no longer the admitted ones; retry the dispatch so its authors are checked again.",
        record,
    )


def _authoring_target_moved(
    admission: _AuthoringAdmission | None, *, resolved: str, rebase_onto: str | None = None
) -> _AuthoringReviewRefused | None:
    """A3, A7: the refusal when the head the worktree helpers settled on is not the admitted one.

    A planned auto-rebase (``rebase_onto``, from :func:`_authoring_rebase_plan`)
    legitimately moves a reused worktree's head; its result is checked by
    :func:`_authoring_rebase_result_refusal` instead.
    """
    if admission is None or admission.kind == "new-branch" or resolved == admission.head_sha:
        return None
    if rebase_onto is not None and admission.record.get("rebase_planned"):
        return _authoring_rebase_result_refusal(admission, onto=rebase_onto, rebased=resolved)
    return _authoring_drift(admission, "head", resolved)


def _authoring_merge_facts(lower: Any, upper: Any) -> Any:
    """Branch facts for the union of two enumerations (A7 rebase plan): every commit, family, path and subject."""
    return dataclasses.replace(
        upper,
        base_tip_sha=lower.base_tip_sha,
        commits=(*lower.commits, *upper.commits),
        existing_families=lower.existing_families | upper.existing_families,
        changed_paths=tuple(dict.fromkeys((*lower.changed_paths, *upper.changed_paths))),
        subject_seats=lower.subject_seats | upper.subject_seats,
        subject_families=lower.subject_families | upper.subject_families,
        subject_evidence=tuple(dict.fromkeys((*lower.subject_evidence, *upper.subject_evidence))),
    )


def _authoring_rebase_plan(admission: _AuthoringAdmission, *, base: str) -> str:
    """A7: the commit a reused worktree may be rebased onto, its result admitted before the branch is touched.

    The auto-rebase replays the branch's own commits (``onto..head``) onto
    ``onto``. Rebasing keeps each commit's message and attribution.
    Enumerate ``review_base..onto`` plus those replays, retaining the stale-base
    diff's protected scope. Use admission's frozen main-side authorship
    exclusion only for PRs targeting main (#9988); other targets keep every
    imported author. The caller's ``base`` never changes that exclusion.
    Both are checked under the admitted risk. ``onto`` is
    observed on the canonical remote and returned for the rebase to use as is,
    so the rebase can never move onto a later, unchecked tip. Read-only: it
    only fetches to make the observed commit local (M1). Raises
    ``_AuthoringReviewRefused``: ``AUTHORSHIP_UNKNOWN`` when ``onto`` or the
    planned authors cannot be determined, ``NO_ROUTE`` when no reviewer
    remains for the rebased branch.
    """
    assert admission.collect is not None  # set by every admission
    record = admission.record
    ref = _base_branch_name(base)
    try:
        # Observed as a new branch's start commit is (A7 §3).
        onto = _authoring_start_commit(admission.remote, ref, _authoring_default_branch(admission.remote))
        _authoring_require_commit(onto, fetch=lambda: _fetch_base(base), what="the rebase target commit")
        behind = _git_rev_count(f"{admission.head_sha}..{onto}")
    except _AuthoringObservationUnknown as exc:
        raise _AuthoringReviewRefused(
            AUTHORING_REVIEW_AUTHORSHIP_UNKNOWN,
            f"{exc}, so the authors of the rebased branch are unknown; retry. Branch not rebased.",
            record,
        ) from exc
    record.update({"rebase_onto": onto, "rebase_planned": behind > 0})
    if behind == 0:
        return onto
    planned = _authoring_merge_facts(
        admission.collect(admission.review_base.sha, onto),
        admission.collect(onto, admission.head_sha),
    )
    record["rebase_existing_families"] = sorted(planned.existing_families)
    _authoring_require_route(planned, planned_risk=admission.planned_risk, record=record, at=onto)
    return onto


def _git_rev_parse_at(cwd: Path, ref: str) -> str | None:
    """The commit ``ref`` names in ``cwd``, or None when it cannot be read. Stderr is discarded."""
    # Same helper as the other worktree reads, so this probe adds no git spawn.
    parsed = _run_git_stdout(cwd, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    if parsed is None or parsed[0] != 0:
        return None
    sha = parsed[1].strip()
    return sha if _AUTHORING_COMMIT_SHA_RE.fullmatch(sha) else None


def _authoring_post_rebase_recovery(admission: _AuthoringAdmission) -> dict[str, Any]:
    """Refs that still name the pre-rebase head. Names no host path.

    ``ORIG_HEAD`` is the immediate pre-rebase head. ``<branch>@{1}`` is that
    head on the branch reflog (git-rebase(1)). The admitted head stays
    ``head_sha`` when a later commit landed before the rebase.
    """
    branch = admission.head_branch if admission.head_branch not in (None, "", "HEAD") else None
    reflog = f"{branch}@{{1}}" if branch else "HEAD@{1}"
    pre = _git_rev_parse_at(admission.checkout, "ORIG_HEAD") if admission.checkout is not None else None
    return {"pre_rebase_head": pre or admission.head_sha, "recovery_refs": ["ORIG_HEAD", reflog]}


def _authoring_rebase_result_refusal(
    admission: _AuthoringAdmission, *, onto: str, rebased: str
) -> _AuthoringReviewRefused | None:
    """A7: the refusal when the rebased head is not the planned one; None when it is.

    The planned head is the admitted commits replayed onto ``onto``: ``onto``
    must be an ancestor, and the authors the recorder now enumerates must be
    among the planned ones, with a reviewer still remaining. Runs before any
    task record or worker; the rebase itself has already happened.

    On success ``rebased_existing_families`` is those enumerated families. The
    planned superset stays on ``rebase_existing_families`` (#9782): a commit
    git drops as patch-equivalent was planned and is not an author of the
    rebased branch. A refusal names the pre-rebase head and its recovery refs.
    """
    assert admission.collect is not None  # set by every admission
    record = {
        **admission.record,
        "binding": "rebase",
        "admitted_sha": admission.head_sha,
        "current_sha": rebased,
        **_authoring_post_rebase_recovery(admission),
    }
    planned = set(record.get("rebase_existing_families") or ())
    try:
        on_plan = _git_is_ancestor(onto, rebased)
    except _AuthoringObservationUnknown as exc:
        return _AuthoringReviewRefused(
            AUTHORING_REVIEW_AUTHORSHIP_UNKNOWN, f"{exc} after the rebase, so its authors are unknown; retry.", record
        )
    try:
        actual = admission.collect(admission.review_base.sha, rebased) if on_plan else None
        if actual is not None and actual.existing_families <= planned:
            _authoring_require_route(actual, planned_risk=admission.planned_risk, record=record, at=rebased)
            # Enforcement already decided from ``actual``. The receipt records that
            # set, not the planned superset a dropped patch-equivalent commit inflated.
            admission.record.update(
                {"rebased_head_sha": rebased, "rebased_existing_families": sorted(actual.existing_families)}
            )
            return None
    except _AuthoringReviewRefused as exc:
        return _AuthoringReviewRefused(exc.code, exc.detail, {**exc.record, **record})
    record["current_existing_families"] = sorted(actual.existing_families) if actual is not None else None
    return _AuthoringReviewRefused(
        AUTHORING_REVIEW_TARGET_MOVED,
        f"the rebased branch head {rebased[:12]} is not the planned rebase of {admission.head_sha[:12]} onto "
        f"{onto[:12]}; retry the dispatch so its authors are checked again.",
        record,
    )


def _git_rev_count(revisions: str) -> int:
    """``git rev-list --count`` in the repository; raises ``_AuthoringObservationUnknown`` when it cannot complete."""
    try:
        proc = subprocess.run(
            ["git", "rev-list", "--count", revisions],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise _AuthoringObservationUnknown("the commit count is unavailable") from exc
    count = (proc.stdout or "").strip() if proc.returncode == 0 else ""
    if not count.isdigit():
        raise _AuthoringObservationUnknown("the commit count is unavailable")
    return int(count)


def _git_is_ancestor(ancestor: str, descendant: str) -> bool:
    """Whether ``ancestor`` is an ancestor of ``descendant``; raises ``_AuthoringObservationUnknown`` on failure."""
    try:
        proc = subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise _AuthoringObservationUnknown("the ancestry check is unavailable") from exc
    if proc.returncode not in (0, 1):
        raise _AuthoringObservationUnknown("the ancestry check is unavailable")
    return proc.returncode == 0


def _authoring_drift(
    admission: _AuthoringAdmission, binding: str, current: str, *, current_base: _ReviewBase | None = None
) -> _AuthoringReviewRefused | None:
    """The structured ``TARGET_MOVED`` refusal (A6, M5) for one binding; None when it still holds."""
    if binding == "review_base":
        assert current_base is not None
        admitted = admission.review_base.sha
        what = f"the review base (admitted branch {admission.review_base.branch}, now {current_base.branch})"
    else:
        admitted = admission.creation_sha if binding == "creation" else admission.head_sha
        what = "the start commit of the new branch" if binding == "creation" else "the branch head"
        if current == admitted:
            return None
    assert admitted is not None
    record = {**admission.record, "binding": binding, "admitted_sha": admitted, "current_sha": current}
    if binding == "head":
        record["current_head_sha"] = current
    if current_base is not None:
        record["current_review_base"] = current_base.receipt(admission.repository)
    return _AuthoringReviewRefused(
        AUTHORING_REVIEW_TARGET_MOVED,
        f"{what} moved after authoring-review admission (admitted {admitted[:12]}, now {current[:12]}); "
        "retry the dispatch so its authors are checked again.",
        record,
    )


def _kimi_worktree_trees(worktree: Path) -> list[Any]:
    """An existing worktree as a Kimi worker sees it: its files on disk and the commit checked out there."""
    from scripts.agent_runtime.kimi_admission import worktree_trees

    return worktree_trees(worktree, env=_sanitized_git_env())


def _resolve_local_base_sha(*, base: str, branch: str | None, pinned_head_sha: str | None) -> str:
    """The commit a new Kimi worktree would start from, from local objects only.

    The Kimi content scan runs before any effect, so this never fetches: it
    verifies the pinned head, the existing remote-tracking ref of ``branch``,
    or the base's remote-tracking ref, as a commit already in the repository.
    Worktree creation later fetches as it does for any seat and refuses when
    the fetched commit is not the one scanned. Raises ``RuntimeError`` when the
    commit is not available locally.
    """
    if pinned_head_sha:
        ref = pinned_head_sha
    elif branch:
        ref = f"origin/{branch}"
    else:
        ref = _origin_base_ref(base)
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=_sanitized_git_env(),
            timeout=DEFAULT_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        proc = None
    sha = (proc.stdout or "").strip() if proc is not None and proc.returncode == 0 else ""
    if not sha:
        from scripts.agent_runtime.kimi_admission import TreeUnavailable

        raise TreeUnavailable(f"base not available locally ({ref}); refresh origin and retry")
    return sha


def _kimi_start_trees(
    args: argparse.Namespace,
    *,
    agent: str,
    target_repo_root: Path,
    validated_worktree: Path | None,
    validated_cwd: Path | None,
) -> tuple[list[Any], str]:
    """The trees a Kimi worker will start from, and the commit they are read at.

    A reused worktree (``--worktree``, ``--branch`` or ``--cwd``) is read as it
    is on disk and at the commit checked out there. A new worktree is read at
    its creation base commit, resolved from objects already present locally
    (no fetch, no checkout) and read with git plumbing. Dispatch then refuses
    a worktree that is not created from, or no longer checked out at, that
    commit. Raises ``ValueError`` or ``RuntimeError`` when there is no such tree.
    """
    from scripts.agent_runtime.kimi_admission import CommitTree

    worktree = getattr(args, "worktree", None) or ("auto" if getattr(args, "branch", None) else None)
    if worktree == "auto":
        path: Path | None = _auto_worktree_path(agent, str(args.task_id), repo_root=target_repo_root)
    elif worktree:
        path = validated_worktree
    elif validated_cwd is not None:
        path = _resolve_verified_worktree_path(validated_cwd)
        if path is None:
            raise ValueError(f"--cwd {str(validated_cwd)!r} is not a dispatch worktree")
    else:
        path = None
    if path is None:
        raise ValueError("workspace-write without a dispatch worktree")
    if path.exists():
        trees = _kimi_worktree_trees(path)
        return trees, trees[-1].commit
    if getattr(args, "pr", None) and not getattr(args, "branch", None):
        raise ValueError("--pr without --branch: name the PR branch so its head is read before dispatch")
    branch, pinned_head = getattr(args, "branch", None), getattr(args, "pinned_head", None)
    base = getattr(args, "base", None)
    if not (base or branch or pinned_head):
        # The new worktree starts at the repository's actual default branch, as
        # authoring-review admission discovers it (#9739 M4), never an assumed main.
        try:
            base = _authoring_default_branch(_authoring_canonical_remote())[0]
        except _AuthoringObservationUnknown as exc:
            raise RuntimeError(f"{exc}; retry") from exc
    base_sha = _resolve_local_base_sha(base=base or "", branch=branch, pinned_head_sha=pinned_head)
    return [CommitTree(_REPO_ROOT, base_sha, env=_sanitized_git_env())], base_sha


def _worker_route_argv(target: AdmittedTarget) -> list[str]:
    """The worker's ``--agent``/``--model`` arguments, taken from the admitted launch target only."""
    from scripts.agent_runtime.target_admission import require_admitted

    target = require_admitted(target)
    argv = ["--agent", target.recipient]
    model = target.model
    if target.recipient == "cursor":
        from scripts.review.model_catalog import apply_cursor_model_pins

        model = apply_cursor_model_pins(model)
    if model:
        argv.extend(["--model", model])
    return argv


@dataclass
class _DispatchRouting:
    """What a dispatch's launch route decided; filled in by :func:`_dispatch_route` inside ``resolve_and_admit``."""

    requested_agent: str | None = None  # after the retired-CLI alias, before budget substitution
    alias_note: str | None = None
    substitution: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        # Forced-lane routing_facts (#9673). Kept off the dataclass fields so the
        # frozen dispatch surface stays the route decision; copied to the task record when set.
        self.budget_diagnostics: dict[str, Any] | None = None


class _DispatchRouteRefused(Exception):
    """The launch route refused the dispatch; the message says why."""


def _dispatch_route(
    args: argparse.Namespace,
    routing: _DispatchRouting,
    *,
    language_lane: bool,
    review_attempt: Any,
) -> Route:
    """The launch route ``resolve_and_admit`` runs for a dispatch, after the original request is gated.

    A retired CLI resolves to its successor (a review attempt refuses that,
    #8517); with ``--check-budget`` the budget guard may substitute a coding
    seat from ``dispatch_fallbacks`` unless ``--force-agent`` is set, which
    keeps the requested seat and still records quota and health; its model is
    mapped or defaulted (``_resolve_substitution_model``). Review routes use
    ``request.review_select`` instead, retaining the resolver's exact model.
    Refusals raise
    ``_DispatchRouteRefused`` or ``BudgetGuardRefuseError``. Records what it
    decided in ``routing``.
    """

    def route(request: RouteRequest) -> tuple[str, str | None, str]:
        original_agent, original_model = request.seat, request.model
        model_resolution: dict[str, Any] = {}
        requested_agent = original_agent
        retired_target = request.retired_successor
        # Permanent CLI retirement (e.g. gemini→agy, operator 2026-08-18): resolve
        # BEFORE the budget guard and unconditionally — a hot/cool budget reading
        # for a retired lane is not proof its binary still exists. --force-agent
        # disables budget substitution, not this — there is no CLI left to force.
        if retired_target:
            if review_attempt:
                raise _DispatchRouteRefused(
                    f"review attempt refused: agent substitution from {original_agent} to {retired_target} "
                    "(retired CLI) is not allowed (#8517)"
                )
            retired_model, retired_how = request.retired_model_resolution or _resolve_substitution_model(
                retired_target, original_model
            )
            _remember_agent_substitution(
                model_resolution,
                source="retired-cli",
                requested_agent=original_agent,
                requested_model=original_model,
                actual_agent=retired_target,
                actual_model=retired_model,
                how=retired_how,
            )
            routing.alias_note = f"NOTE: {original_agent}→{retired_target} retired CLI"
            print(
                f"🔄 RETIRED CLI ALIAS: --agent {original_agent} → {retired_target} "
                f"{_substitution_model_phrase(retired_model, retired_how, original_model)} "
                f"({routing.alias_note}; the {original_agent} CLI is not installed/supported).",
                file=sys.stderr,
            )
            requested_agent = retired_target
            if request.review_select is not None:
                original_model = retired_model
        routing.requested_agent = requested_agent

        if request.review_select is not None:
            selected_agent, selected_model = request.review_select(None, requested_agent)
            if (selected_agent, selected_model) != (requested_agent, original_model):
                print(
                    f"REVIEW_IDENTITY_SUBSTITUTED: --agent {requested_agent} --model {original_model} "
                    f"→ --agent {selected_agent} --model {selected_model} (reviewer resolver admission).",
                    file=sys.stderr,
                )
                _remember_agent_substitution(
                    model_resolution,
                    source="reviewer-resolver",
                    requested_agent=original_agent,
                    requested_model=original_model,
                    actual_agent=selected_agent,
                    actual_model=selected_model,
                    how="reviewer-resolver",
                )
            requested_agent = selected_agent
            original_model = selected_model

        if request.review_select is not None or _dispatch_check_budget_enabled(args):
            force_agent = bool(getattr(args, "force_agent", False))
            diagnostic_sink: dict[str, Any] = {}
            dispatch_agent = _resolve_agent_with_budget_guard(
                requested_agent,
                provider="openrouter" if getattr(args, "provider", None) == "openrouter" else None,
                language_lane=language_lane,
                requested_model=original_model,
                model_resolution=model_resolution,
                origin_agent=original_agent,
                fallbacks=request.fallbacks,
                review_select=request.review_select,
                review_trusted_inputs=bool(
                    getattr(args, "review_author_model", None) and getattr(args, "review_risk", None)
                ),
                force_agent=force_agent,
                diagnostic_sink=diagnostic_sink if force_agent else None,
            )
            if diagnostic_sink:
                routing.budget_diagnostics = diagnostic_sink
        else:
            dispatch_agent = requested_agent

        substitution = _applied_agent_substitution(model_resolution, dispatch_agent)
        if dispatch_agent != original_agent and substitution is None:
            chosen_model, chosen_how = _resolve_substitution_model(dispatch_agent, original_model)
            _remember_agent_substitution(
                model_resolution,
                source="budget-guard",
                requested_agent=original_agent,
                requested_model=original_model,
                actual_agent=dispatch_agent,
                actual_model=chosen_model,
                how=chosen_how,
            )
            substitution = model_resolution["record"]
        if language_lane and dispatch_agent not in _LANGUAGE_LANES:
            raise _DispatchRouteRefused(
                "ROUTING REFUSED: LANGUAGE-LANES RULE (operator 2026-09-27): "
                f"effective --agent {dispatch_agent} is outside claude, codex (GPT), and agy (Gemini)."
            )
        routing.substitution = substitution
        if substitution is not None:
            substitution["requested_model"] = request.model
        if substitution is None:
            return dispatch_agent, original_model, "explicit"
        return dispatch_agent, substitution["actual_model"], f"route:{substitution['source']}"

    return route


def _kimi_dispatch_gate(
    args: argparse.Namespace,
    *,
    agent: str,
    route: Route,
    repo_role: str | None,
    target_repo_root: Path,
    validated_worktree: Path | None,
    validated_cwd: Path | None,
) -> tuple[str | None, str | None, Any]:
    """The dispatch-side gate: ``(refusal, start commit, admitted target)``.

    ``agent`` and ``--model`` are the original request; ``route`` (see
    :func:`_dispatch_route`) resolves the launch route inside
    ``resolve_and_admit``, which gates the request before it and the route
    after it. The admitted target is the seat and model the worker is
    launched with; None when refused. The start commit is the commit the
    owned paths were last read at — in the worktree of the seat resolved so
    far — which the worker's worktree must be created from or checked out at;
    None when the call is refused, is not Kimi, or owns no paths. The tree is
    resolved only after every policy check admits.
    """
    from scripts.agent_runtime.target_admission import launch_seat

    start: list[str] = []
    seat = [launch_seat(agent)]

    def routed(request: RouteRequest) -> tuple[str, str | None, str]:
        result = route(request)
        seat[0] = result[0]
        return result

    def trees() -> list[Any]:
        if args.mode == "read-only" and not (getattr(args, "worktree", None) or getattr(args, "branch", None)):
            # Mechanical classification/recon can read an ordinary checkout.
            # Kimi writes still use the dispatch-worktree resolver below.
            return _kimi_worktree_trees(validated_cwd or target_repo_root)
        resolved, commit = _kimi_start_trees(
            args,
            agent=seat[0],
            target_repo_root=target_repo_root,
            validated_worktree=validated_worktree,
            validated_cwd=validated_cwd,
        )
        start.append(commit)
        return resolved

    refusal, target = _admit_dispatch_target(args, agent=agent, repo_role=repo_role, trees=trees, route=routed)
    return refusal, (start[-1] if start and refusal is None else None), target


def _kimi_admission_refusal(
    args: argparse.Namespace,
    *,
    agent: str,
    trees: Any,
    repo_role: str | None = None,
) -> str | None:
    """Refusal message when ``agent`` or ``--model`` is a Kimi seat and the dispatch is not admitted."""
    return _admit_dispatch_target(args, agent=agent, trees=trees, repo_role=repo_role)[0]


def _dispatch_review_changed_paths(args: argparse.Namespace) -> tuple[str, ...]:
    """Resolve a review's exact scope before route selection, pinning branch heads.

    Branch refs use the existing remote-tracking objects; a missing object
    refuses and must be refreshed before retrying. PR resolution uses its
    actual base. Attempt records supply their frozen target.changed_paths.
    """
    from scripts.review.security_paths import git_changed_paths
    from scripts.review.target_resolution import TargetResolutionError, resolve_branch_target, resolve_pr_target

    attempt = getattr(args, "review_attempt", None)
    paths: tuple[str, ...] | None = None
    if attempt:
        import yaml

        try:
            record = yaml.safe_load(Path(attempt).read_bytes())
        except (OSError, ValueError, yaml.YAMLError) as exc:
            raise TargetResolutionError("review attempt target unreadable") from exc
        target_record = record.get("target") if isinstance(record, dict) else None
        changed = target_record.get("changed_paths") if isinstance(target_record, dict) else None
        if not isinstance(changed, list) or not all(isinstance(path, str) and path for path in changed):
            raise TargetResolutionError("review attempt target.changed_paths missing or invalid")
        paths = tuple(changed)

    branch = getattr(args, "branch", None)
    pr = getattr(args, "pr", None)
    pinned = getattr(args, "pinned_head", None)
    if pinned and not (branch or pr):
        raise TargetResolutionError("--pinned-head requires --branch or --pr")
    if pr is not None:
        target = resolve_pr_target(_local_repo_root, int(pr))
        if pinned and pinned.lower() != target.head_sha:
            raise TargetResolutionError("pinned head differs from PR head")
        args._review_admission_head = target.head_sha
    elif branch:
        if pinned and not re.fullmatch(r"[0-9a-fA-F]{40}", pinned):
            raise TargetResolutionError("pinned head must be a full commit SHA")
        target = resolve_branch_target(
            _local_repo_root,
            pinned or _origin_base_ref(branch),
            _origin_base_ref(getattr(args, "base", None) or "main"),
        )
        args.pinned_head = target.head_sha
    elif paths is not None:
        return paths
    else:
        raise TargetResolutionError("review target required: supply --branch, --pr or a resolved --review-attempt")
    literal = git_changed_paths(_local_repo_root, target.base_sha, target.head_sha)
    # The frozen endpoints the complete-authorship facts are read from (#9739).
    args._review_target = target
    return tuple(dict.fromkeys((*literal, *(paths or ()))))


def _dispatch_review_facts(args: argparse.Namespace, owned_paths: Sequence[str]) -> Any:
    """Complete authorship and scope of the review target for a trusted code review (#9739).

    Only a review that names its author and risk attests cross-family
    independence, so only it reads the facts; legacy reviews keep intrinsic
    eligibility. Runs after :func:`_dispatch_review_changed_paths` pinned the
    target. Returns None without a branch or PR target.
    """
    from scripts.review.record_cf_verdict import collect_branch_review_facts

    target = getattr(args, "_review_target", None)
    if target is None or not (getattr(args, "review_author_model", None) and getattr(args, "review_risk", None)):
        return None
    return collect_branch_review_facts(
        repository=_resolve_dispatch_repository(_local_repo_root) or "",
        repo_root=_local_repo_root,
        base_tip_sha=target.base_sha,
        head_sha=target.head_sha,
        task_root=tasks_dir(),
        owned_paths=owned_paths,
        subject_seats=tuple(getattr(args, "subject_seat", None) or ()),
        subject_families=tuple(getattr(args, "subject_family", None) or ()),
    )


def _admit_dispatch_target(
    args: argparse.Namespace,
    *,
    agent: str,
    trees: Any,
    repo_role: str | None = None,
    route: Route | None = None,
) -> tuple[str | None, Any]:
    """``(refusal, admitted target)`` for launching ``agent`` with ``--model``; exactly one is None.

    The original request (``agent``, ``--model``) and the launch ``route``
    it resolves to (retired-CLI alias, budget substitution) are resolved and
    admitted in one step (``resolve_and_admit``); a route refusal is returned
    like a Kimi refusal. ``--owned-path`` and ``--research-owned-path`` both
    declare task ownership, so every path from either flag must be on the
    Kimi allowlist and is read for Ukrainian content in ``trees`` (see
    ``refuse_kimi_if_disallowed``).
    """
    from scripts.agent_runtime.kimi_admission import KimiAdmissionRefused
    from scripts.agent_runtime.mechanical_admission import MechanicalAdmissionRefused
    from scripts.agent_runtime.target_admission import ReviewAdmissionRefused, resolve_and_admit
    from scripts.review.model_catalog import ModelCatalogError, apply_cursor_model_pins
    from scripts.review.target_resolution import TargetResolutionError

    def flag_paths(attr: str) -> list[str]:
        value = getattr(args, attr, None) or []
        return [value] if isinstance(value, str) else list(value)

    # Only ``--owned-path`` is ownership (the worker's boundary and scan use it); a
    # ``--research-owned-path`` is checked like one but never stands in for it.
    declared = flag_paths("owned_path")
    owned = declared + flag_paths("research_owned_path")
    review_dispatch = _dispatch_is_review_typed(args)
    subjects = flag_paths("subject_seat")
    subject_families = flag_paths("subject_family")
    if subjects or subject_families:
        from scripts.review.subject_seat import prepare_subject_exclusion

        subject = prepare_subject_exclusion(
            subject_seats=frozenset(subjects), subject_families=frozenset(subject_families)
        )
        if subject.fail_closed_reason:
            return f"REVIEW_ROUTE_REFUSED: {subject.fail_closed_reason}", None
        if not review_dispatch and getattr(args, "mode", None) not in {"workspace-write", "danger"}:
            return "REVIEW_ROUTE_REFUSED: subject flags require a review or write-dispatch review admission", None

    def collect_review_paths() -> tuple[str, ...]:
        try:
            return _dispatch_review_changed_paths(args)
        except (TargetResolutionError, OSError, subprocess.TimeoutExpired) as exc:
            raise ReviewAdmissionRefused(f"REVIEW_TARGET_UNRESOLVED: {exc}") from exc

    def collect_review_facts() -> Any:
        from scripts.review.record_cf_verdict import BranchFactsError

        try:
            return _dispatch_review_facts(args, tuple(declared))
        except BranchFactsError as exc:
            raise ReviewAdmissionRefused(f"REVIEW_TARGET_UNRESOLVED: {exc}") from exc

    try:
        mechanical_task = _mechanical_task_scope(args)
        (target,) = resolve_and_admit(
            (agent,),
            model=getattr(args, "model", None),
            mode=str(getattr(args, "mode", "") or ""),
            route=route,
            fallbacks_path=_FALLBACK_SUBS_PATH,
            # Every review-typed dispatch passes reviewer admission, not only verdict-gated ones (#9538).
            review_dispatch=review_dispatch,
            review_author_model=getattr(args, "review_author_model", None),
            review_risk=getattr(args, "review_risk", None),
            review_profile=getattr(args, "review_profile", None),
            review_attempt=bool(getattr(args, "review_attempt", None)),
            review_alias_model_resolver=_resolve_substitution_model,
            review_owned_paths=tuple(declared),
            review_changed_paths=(
                collect_review_paths
                if review_dispatch and (getattr(args, "review_profile", None) or "code") in {"code", "infra"}
                else ()
            ),
            review_subject_seats=frozenset(subjects),
            review_subject_families=frozenset(subject_families),
            review_facts=(
                collect_review_facts
                if review_dispatch and (getattr(args, "review_profile", None) or "code") in {"code", "infra"}
                else None
            ),
            paths=owned,
            declared_paths=declared,
            repo=repo_role,
            review=review_dispatch,
            language_lane=_dispatch_is_language_lane(args),
            research_track=getattr(args, "research_track", None),
            prompt_file=getattr(args, "prompt_file", None),
            repo_root=_REPO_ROOT,
            trees=trees,
            task_family=getattr(args, "research_task_family", None),
            task_role=getattr(args, "research_role", None),
            task_prompt=getattr(args, "prompt", None),
        )
        if mechanical_task != _mechanical_task_scope(args):
            raise MechanicalAdmissionRefused("MECHANICAL_TASK_REFUSED: admission inputs changed during dispatch (#10079)")
        args._mechanical_admitted_scope = mechanical_task
        if target.recipient == "cursor":
            apply_cursor_model_pins(target.model)
    except (KimiAdmissionRefused, MechanicalAdmissionRefused, ReviewAdmissionRefused, _DispatchRouteRefused, BudgetGuardRefuseError, ModelCatalogError) as exc:
        return str(exc), None
    return None, target


def _mechanical_task_scope(args: argparse.Namespace, *, admitted: bool = False) -> dict[str, Any]:
    """Persist the admission inputs the execution adapter must recheck (#9996)."""
    from scripts.agent_runtime.mechanical_admission import MECHANICAL_FAMILIES, MechanicalAdmissionRefused
    from scripts.agent_runtime.target_admission import mechanical_scope_digest

    if admitted:
        # Persist the inputs captured at admission, even if argv or the prompt file changed since then.
        return dict(getattr(args, "_mechanical_admitted_scope", {}))
    family = getattr(args, "research_task_family", None)
    if family not in MECHANICAL_FAMILIES:
        return {}
    prompt_file = getattr(args, "prompt_file", None)
    try:
        prompt_file_sha256 = hashlib.sha256(Path(prompt_file).read_bytes()).hexdigest() if prompt_file else None
    except OSError as exc:
        raise MechanicalAdmissionRefused("MECHANICAL_TASK_REFUSED: task input unavailable at prompt file (#10079)") from exc
    paths = []
    for value in (getattr(args, "owned_path", None), getattr(args, "research_owned_path", None)):
        paths.extend([value] if isinstance(value, str) else value or [])
    scope = {
        "family": family,
        "role": getattr(args, "research_role", None),
        "track": getattr(args, "research_track", None),
        "language_lane": _dispatch_is_language_lane(args),
        "review": _dispatch_is_review_typed(args),
        "paths": paths,
        "mode": getattr(args, "mode", None),
        "task_prompt": getattr(args, "prompt", None),
        "prompt_file": str(Path(prompt_file).resolve()) if prompt_file else None,
        "prompt_file_sha256": prompt_file_sha256,
    }
    scope["sha256"] = mechanical_scope_digest(scope)
    return scope


def _discard_model_probe_output(plan: object) -> None:
    """Remove a temp file a successful model probe created. Leave repo paths alone."""
    output = getattr(plan, "output_file", None)
    if not isinstance(output, Path):
        return
    try:
        resolved = output.resolve()
        temp_root = Path(tempfile.gettempdir()).resolve()
    except OSError:
        return
    if resolved != temp_root and temp_root not in resolved.parents:
        return
    try:
        resolved.unlink(missing_ok=True)
    except OSError:
        return


def _adapter_model_rejection(agent: str, model: str) -> str | None:
    """Return the adapter's refusal text, or None when this model is not refused.

    A successful probe is not a rejection. Any error other than the adapter's
    model ValueError is inconclusive: keep the explicit model instead of
    crashing dispatch. The probe must not leave the temp file ``build_invocation``
    creates on the accepted path.
    """
    from agent_runtime.registry import get_agent_entry

    entry = get_agent_entry(agent)
    spec = str(entry.get("adapter") or "")
    if ":" not in spec:
        return None
    module_name, class_name = spec.split(":", 1)
    module = __import__(module_name, fromlist=[class_name])
    adapter = getattr(module, class_name)()
    try:
        plan = adapter.build_invocation(
            prompt="model-probe",
            mode="read-only",
            cwd=Path("."),
            model=model,
            task_id=None,
            session_id=None,
            tool_config=None,
        )
    except ValueError as exc:
        text = str(exc)
        if model in text and ("rejected" in text or "unsupported" in text.lower()):
            return text
        return None
    except Exception as exc:
        print(
            f"⚠ model probe for {_registry_seat(entry)} could not verify {_catalog_model_label(model)}: "
            f"{type(exc).__name__}",
            file=sys.stderr,
        )
        return None
    _discard_model_probe_output(plan)
    return None


def _registry_seat(entry: object) -> str:
    """The registry's name for ``entry`` (an alias's canonical seat), for log text (#9739).

    Log text names seats and models as the registry and catalog spell them,
    never as the caller passed them, which CodeQL's
    ``py/clear-text-logging-sensitive-data`` flagged as secret data.
    """
    from agent_runtime.registry import AGENTS

    return next((name for name, row in AGENTS.items() if row is entry), "an unregistered seat")


def _catalog_model_label(model: str) -> str:
    """The catalog id ``model`` names, for log text; an unknown model gets a fixed label (#9739)."""
    from scripts.review.model_catalog import ModelCatalogError, canonical_model_id

    try:
        return canonical_model_id(model) or "an uncatalogued model"
    except ModelCatalogError:
        return "a model (catalog unavailable)"


def _adapter_rejects_model(agent: str, model: str) -> bool:
    """True when the target adapter refuses this explicit model before spawn."""
    return _adapter_model_rejection(agent, model) is not None


def _lane_default_model(agent: str) -> str | None:
    """Role-backed dispatch default, with registry-only lanes retained until PR 3c."""
    from agent_runtime.telemetry import _default_model_for
    from scripts.review.model_catalog import substitution_default_model

    return substitution_default_model(agent) or _default_model_for(agent)


def _credit_period_refusal(dispatch_agent: str, launch_model: str | None) -> str | None:
    """Typed refusal when the credit-period allowlist applies to ``dispatch_agent`` and the launch model is off it (#9518).

    The allowlist applies whenever the plan window is at or below the threshold
    and a fresh positive credit balance exists, whether or not the router
    currently recommends the lane. A dispatch without ``--model`` is judged by the lane's default model. The
    policy (``scripts/config/credit_lanes.yaml``) and the lane state come from
    ``scripts.fleet.credit_lane``, the same reader ``capacity_pick`` uses; an
    unreadable policy restricts only the built-in credit lanes and warns on
    stderr. Reads snapshots only: never consumes credits or resets.
    """
    from scripts.fleet import credit_lane

    return credit_lane.dispatch_refusal(dispatch_agent, launch_model or _lane_default_model(dispatch_agent))


def _load_budget_substitution_table() -> dict[str, dict[str, str]]:
    from scripts.review.model_catalog import ModelCatalogError, budget_substitution_table, load_model_catalog

    try:
        return budget_substitution_table(load_model_catalog())
    except ModelCatalogError as exc:
        raise BudgetGuardRefuseError(
            f"ROUTING REFUSED: model catalog cannot resolve a substitution model: {exc}"
        ) from exc


def _substitution_model_admitted(agent: str, model: str) -> bool:
    """True when ``model`` is a catalog-or-invocation model for ``agent`` and the adapter does not reject it."""
    from scripts.review.model_catalog import ModelCatalogError, load_model_catalog, substitution_model_admitted

    try:
        admitted = substitution_model_admitted(load_model_catalog(), agent, model)
    except ModelCatalogError as exc:
        raise BudgetGuardRefuseError(
            f"ROUTING REFUSED: model catalog cannot resolve a substitution model: {exc}"
        ) from exc
    if not admitted:
        return False
    return not _adapter_rejects_model(agent, model)


def _resolve_substitution_model(target_agent: str, explicit_model: str | None) -> tuple[str, str]:
    """Map ``explicit_model`` onto ``target_agent``, or use that lane's registry default.

    A mapping row wins when the substitute admits the mapped model. With no
    explicit model, or an explicit model the substitute adapter does not
    reject, dispatch uses that lane's registry default. An explicit model
    with no mapping row that the adapter rejects is refused before spawn:
    the default must not hide that refusal (retired alias and budget guard).

    Returns ``(model, "mapped"|"catalog-default")``. Raises BudgetGuardRefuseError
    when the explicit model is rejected, or neither a mapped model nor the
    default is valid for the substitute.
    """
    table = _load_budget_substitution_table().get(target_agent, {})
    mapped = table.get(explicit_model) if explicit_model else None
    default = _lane_default_model(target_agent)
    if mapped and _substitution_model_admitted(target_agent, mapped):
        return mapped, "mapped"
    if explicit_model and mapped is None:
        rejection = _adapter_model_rejection(target_agent, explicit_model)
        if rejection:
            raise BudgetGuardRefuseError(
                "ROUTING REFUSED: substitute "
                f"--agent {target_agent} rejects explicit --model {explicit_model} "
                f"({rejection}). Refusing before spawn."
            )
    if default and _substitution_model_admitted(target_agent, default):
        return default, "catalog-default"
    raise BudgetGuardRefuseError(
        "ROUTING REFUSED: no valid model for substitute "
        f"--agent {target_agent} "
        f"(requested --model {explicit_model or '(none)'}; "
        f"mapped {mapped or '(none)'}; "
        f"catalog default {default or '(none)'}). "
        "Refusing before spawn."
    )


def _substitution_model_phrase(chosen: str, how: str, explicit_model: str | None) -> str:
    if how == "mapped":
        return f"--model {chosen} (mapped from {explicit_model})"
    if explicit_model:
        return f"--model {chosen} (catalog default; {explicit_model} has no mapping)"
    return f"--model {chosen} (catalog default)"


def _remember_agent_substitution(
    sink: dict[str, Any] | None,
    *,
    source: str,
    requested_agent: str,
    requested_model: str | None,
    actual_agent: str,
    actual_model: str,
    how: str,
) -> None:
    if sink is None:
        return
    sink["applied"] = True
    sink["model"] = actual_model
    sink["record"] = {
        "kind": "agent-substitution",
        "substituted": True,
        "source": source,
        "requested_agent": requested_agent,
        "actual_agent": actual_agent,
        "requested_model": requested_model,
        "actual_model": actual_model,
        "actual_model_known": True,
        "model_resolution": how,
    }


def _applied_agent_substitution(resolution: dict[str, Any], dispatch_agent: str) -> dict[str, Any] | None:
    if not resolution.get("applied"):
        return None
    record = resolution.get("record")
    if not isinstance(record, dict) or record.get("actual_agent") != dispatch_agent:
        return None
    return record


def _merge_agent_substitution(prior: Any, runtime: Any) -> Any:
    """Keep a dispatch agent-substitution when later runtime attribution arrives."""
    if not isinstance(prior, dict) or prior.get("kind") != "agent-substitution":
        return runtime
    if not isinstance(runtime, dict):
        return prior
    if runtime.get("kind") == "agent-substitution":
        return runtime
    merged = dict(prior)
    merged["runtime_attribution"] = runtime
    return merged


def _ranked_reports_lane_health(ranked: Any, lane: str) -> bool:
    """True when the snapshot's ranked rows already carry a health record for ``lane``."""
    if not isinstance(ranked, list):
        return False
    return any(isinstance(item, dict) and item.get("lane") == lane and item.get("health") for item in ranked)


def _publish_forced_lane_diagnostics(
    lane: str,
    record: Mapping[str, Any] | None,
    snapshot_metadata: Mapping[str, Any] | None,
    *,
    model: str | None,
    sink: dict[str, Any] | None,
    ranked: Any = None,
) -> None:
    """Print and retain one forced lane's quota and health (#9673).

    The text reuses the guard's existing lines: the health-unknown sentence,
    and ``⚠ ROUTING CHECK:`` around the owner's ``capacity_reason``. A known
    remaining percent is added with the owner's ``% remaining`` phrase when
    that reason does not already include it. ``sink`` receives
    :meth:`credit_lane.RoutingFacts.summary`, whose missing quota, health and
    freshness are explicit unknowns.
    """
    facts = credit_lane.routing_facts(
        lane,
        record if isinstance(record, Mapping) else None,
        model=model or _lane_default_model(lane) or "",
        snapshot_metadata=snapshot_metadata,
    )
    if facts.health == credit_lane.UNKNOWN and not _ranked_reports_lane_health(ranked, lane):
        print(
            f"⚠ lane {lane} health unknown ({facts.health_basis}); not counted as healthy",
            file=sys.stderr,
        )
    quota = facts.capacity_reason
    remaining = facts.plan_remaining_pct
    if (
        isinstance(remaining, (int, float))
        and not isinstance(remaining, bool)
        and f"{remaining:g}% remaining" not in quota
    ):
        quota = f"{quota} ({remaining:g}% remaining)"
    print(f"⚠ ROUTING CHECK: lane {lane}: {quota}", file=sys.stderr)
    if sink is not None:
        sink.clear()
        sink.update(facts.summary())


def _resolve_agent_with_budget_guard(
    agent: str,
    *,
    provider: str | None = None,
    language_lane: bool = False,
    requested_model: str | None = None,
    model_resolution: dict[str, Any] | None = None,
    origin_agent: str | None = None,
    fallbacks: Mapping[str, str],
    review_select: Callable[[Mapping[str, Any] | None, str], tuple[str, str | None]] | None = None,
    review_trusted_inputs: bool = False,
    force_agent: bool = False,
    diagnostic_sink: dict[str, Any] | None = None,
) -> str:
    """Return possibly-substituted agent.

    Writer routes hard-auto-sub on fresh snapshot when the lane is near_cap, hot, or in
    CodexBar deficit (will_last_to_reset is False), if yaml dispatch_fallbacks
    (``fallbacks``, which ``resolve_and_admit`` reads and hands to the launch
    route) has a known target. Without a usable fallback: refuse (raise
    BudgetGuardRefuseError). ``force_agent`` disables that writer substitution and
    the capacity refusal, and still prints and stores the lane's quota and
    health (explicit unknowns when telemetry is missing).
    Subscription stale/empty: advisory only. Prepaid requires fresh verified
    funding independently of the subscription ledger and never auto-substitutes.
    Review routes use ``review_select`` before either coding fallback path;
    pace only orders equal fits and ``force_agent`` never bypasses review hard gates.
    A lane with a credit balance present (``scripts.fleet.credit_lane``) is not substituted.
    """
    requested = (agent or "").strip().lower()
    if language_lane and requested not in _LANGUAGE_LANES:
        raise BudgetGuardRefuseError(
            "ROUTING REFUSED: LANGUAGE-LANES RULE (operator 2026-09-27): "
            f"--agent {requested} is outside claude, codex (GPT), and agy (Gemini)."
        )
    try:
        payload = _fetch_routing_budget()
    except MonitorApiUnavailable:
        if (requested == "deepseek" or provider == "openrouter") and not force_agent:
            raise BudgetGuardRefuseError(
                "NOTE: ROUTING REFUSED: prepaid capacity NEED_PROBE; Monitor API unreachable."
            ) from None
        print("⚠ ROUTING CHECK SKIPPED: Monitor API unreachable", file=sys.stderr)
        if force_agent:
            _publish_forced_lane_diagnostics(
                requested,
                None,
                None,
                model=requested_model,
                sink=diagnostic_sink,
            )
        return requested

    prepaid = "openrouter" if provider == "openrouter" else requested if requested == "deepseek" else None
    if prepaid:
        from scripts.api.state_router import _api_lane_status_from_account

        accounts = payload.get("api_accounts") or {}
        account = accounts.get(prepaid) or {}
        status = _api_lane_status_from_account(prepaid, account)
        blocked = (
            status not in {"cool", "warm"}
            or account.get("is_available") is False
            or account.get("status") == "near_cap"
        )
        if blocked and not force_agent:
            raise BudgetGuardRefuseError(
                f"NOTE: ROUTING REFUSED: prepaid {prepaid} status={status}; "
                f"probe_state={account.get('probe_state', 'NEED_PROBE')}; "
                f"freshness={account.get('freshness', 'unavailable')}. "
                "Verify funding with `python -m scripts.fleet.usage refresh` or pass --force-agent."
            )
        if force_agent:
            if blocked:
                print(
                    f"⚠ ROUTING CHECK: prepaid {prepaid} status={status}; "
                    f"probe_state={account.get('probe_state', 'NEED_PROBE')}; "
                    f"freshness={account.get('freshness', 'unavailable')}.",
                    file=sys.stderr,
                )
            _publish_forced_lane_diagnostics(
                requested,
                account if isinstance(account, dict) else None,
                payload.get("diagnostics") if isinstance(payload.get("diagnostics"), dict) else None,
                model=requested_model,
                sink=diagnostic_sink,
            )
        return requested

    diags = payload.get("diagnostics") or {}
    rec = payload.get("recommendation") or {}
    agents = payload.get("agents") or {}
    records_loaded = int(diags.get("records_loaded", 0) or 0)
    is_stale = bool(diags.get("stale", False))
    codexbar_data_available = bool(diags.get("codexbar_data_available", False))
    subscription_data_available = codexbar_data_available or bool(agents)
    initial_review_substitution = (
        review_select is not None
        and (model_resolution or {}).get("record", {}).get("source") == "reviewer-resolver"
    )
    if initial_review_substitution and not (isinstance(agents.get(requested), Mapping) and agents[requested]):
        raise BudgetGuardRefuseError(
            f"REVIEW_ROUTE_REFUSED: substitute --agent {requested} has no usable budget snapshot; refusing before spawn"
        )

    # An empty ledger is only unknown when the explicit subscription refresh also
    # yielded no authoritative weekly data. Never quietly fail open here.
    if not agents or (records_loaded == 0 and not subscription_data_available):
        print(
            "⚠ ROUTING CHECK UNKNOWN: budget UNKNOWN — could not verify subscription "
            "usage snapshots; lanes may be in deficit; no hard sub.",
            file=sys.stderr,
        )
        if force_agent:
            _publish_forced_lane_diagnostics(
                requested,
                None,
                diags if isinstance(diags, dict) else None,
                model=requested_model,
                sink=diagnostic_sink,
            )
        return requested

    # Warn about demoted lanes and lanes whose health is unknown (#9740 F4: the owner's reading).
    for item in payload.get("ranked_by_headroom") or []:
        if not isinstance(item, dict) or not item.get("health"):
            continue
        lane = item.get("lane")
        health, basis = credit_lane.health_fact(item)
        if health == credit_lane.UNHEALTHY:
            h = item["health"]
            print(
                f"⚠ lane {lane} demoted: {h.get('consecutive_failures')} spawn failures in {h.get('span_minutes')}m",
                file=sys.stderr,
            )
        elif health == credit_lane.UNKNOWN:
            print(f"⚠ lane {lane} health unknown ({basis}); not counted as healthy", file=sys.stderr)

    if records_loaded == 0:
        for warning in rec.get("warnings") or []:
            if "is in deficit" in str(warning):
                print(f"⚠ ROUTING CHECK: {warning}", file=sys.stderr)

    if is_stale:
        print(
            "⚠ ROUTING CHECK ADVISORY (stale snapshot, generatedAt/data age >15min) — verify manually; no hard sub",
            file=sys.stderr,
        )
        # Rec warning deliberately suppressed on stale: a recommendation from
        # stale numbers is worse than none (same rationale as the empty case).
    else:
        # advisory rec mismatch still emitted (for info)
        recommended = rec.get("primary_agent_for_code")
        if recommended and recommended != requested and recommended not in (None, "inline_orchestrator"):
            print(
                f"⚠ ROUTING WARNING: budget recommends --agent {recommended}, you passed --agent {requested}.",
                file=sys.stderr,
            )
            if rec.get("rationale"):
                print(f"Rationale: {rec['rationale']}", file=sys.stderr)

    agent_info = agents.get(requested, {}) or {}
    agent_dict = agent_info if isinstance(agent_info, dict) else {}
    status = _budget_lane_status(requested, agent_dict)
    will_last = _budget_will_last_to_reset(agent_dict)
    reserve = _load_reset_reserve(_REPO_ROOT, codex_info=agents.get("codex", {}))
    # The reserve never overrides the owner (#9740): it needs the owner's verified capacity.
    reserve_relaxes = (
        requested == "codex"
        and _codex_is_threatened(agent_dict)
        and _codex_reset_reserve_eligible(
            reserve,
            agent_dict,
            owner_capacity=_budget_owner_facts(
                requested, agent_dict, model=requested_model, is_stale=is_stale, snapshot_metadata=diags
            ).capacity,
            snapshot_stale=is_stale,
        )
    )
    if reserve_relaxes:
        print(
            f"⚠ Codex reset reserve active ({reserve.get('remaining_resets')} confirmed reset(s) remaining); "
            "provider and runtime headroom checks passed.",
            file=sys.stderr,
        )
    credit_relaxes = False
    if not reserve_relaxes:
        # #9518: a lane with a credit balance present and no recent rate limit stays
        # usable (the credit-period model check runs on the admitted route); unknown,
        # stale or contradicted credit data, or an unreadable policy, keeps today's guard.
        try:
            credit = credit_lane.lane_credit_state(
                requested, agent_dict, credit_lane.load_policy(), snapshot_stale=is_stale
            )
        except ValueError:
            credit = {"state": None}
        credit_relaxes = credit["state"] == credit_lane.CREDIT_BALANCE_PRESENT
        if credit_relaxes:
            print(
                f"⚠ lane {requested} has a {credit_lane.DRAW_NOT_VERIFIED} ({credit['reason']}); "
                f"credit-period models only: {', '.join(credit['allowed_models'])}.",
                file=sys.stderr,
            )
    burn = (
        agent_info.get("burn_pct_7d")
        if requested != "claude"
        else (agent_info.get("interactive") or {}).get("burn_pct_7d") or agent_info.get("burn_pct_7d")
    )

    needs_action, reason = (
        (False, "")
        if reserve_relaxes or credit_relaxes
        else _budget_needs_hard_capacity_action(
            status=status,
            will_last=will_last,
            is_stale=is_stale,
            snapshot_metadata=diags,
            pace=_budget_pace(agent_dict),
            headroom_blocked=_budget_headroom_blocked(agent_dict),
            lane=requested,
            info=agent_dict,
            model=requested_model,
        )
    )
    if review_select is not None:
        from scripts.review.capacity import review_capacity_action

        review_blocked, review_reason = review_capacity_action(requested, agent_dict, diags, requested_model)
        if review_blocked:
            needs_action, reason = True, review_reason
    if force_agent:
        _publish_forced_lane_diagnostics(
            requested,
            agent_dict,
            diags if isinstance(diags, dict) else None,
            model=requested_model,
            sink=diagnostic_sink,
            ranked=payload.get("ranked_by_headroom"),
        )
        if review_select is None:
            return requested
    if review_select is not None:
        # #9959: capacity is an exclusion before the resolver ranks candidates,
        # not a veto on its first pick. Keep coding fallbacks out of review
        # selection, and evaluate exact candidate models with this guard's
        # existing thresholds/credit rules. The snapshot is caller-owned data.
        from scripts.review.capacity import review_capacity_action
        from scripts.review.reviewer_resolver import REVIEW_CANDIDATES

        capacity_exclusions: dict[str, str] = {}
        for candidate in REVIEW_CANDIDATES.values():
            info = agents.get(candidate.route)
            if candidate.route != requested and not (isinstance(info, Mapping) and info):
                capacity_exclusions[candidate.name] = "substitute has no usable budget snapshot"
                continue
            info = info if isinstance(info, Mapping) else {}
            blocked, cause = review_capacity_action(candidate.route, info, diags, candidate.concrete_model)
            if blocked:
                capacity_exclusions[candidate.name] = cause
        review_snapshot = {
            **payload,
            "agents": {lane: info if isinstance(info, Mapping) else {} for lane, info in agents.items()},
            "review_capacity_exclusions": capacity_exclusions,
        }
        sub, chosen = review_select(review_snapshot, requested if needs_action else "")
        if sub == requested and chosen == requested_model:
            if not needs_action:
                return requested
            if status in {"cool", "warm"} and "deficit" in reason:
                note = (
                    "NOTE: REVIEW_BUDGET_RETAINED: retaining resolver-selected reviewer "
                    "on pace-only deficit."
                )
            else:
                note = "REVIEW_SUBSTITUTION_DISABLED: retaining eligible requested reviewer" + (
                    ";" if not review_trusted_inputs else "."
                )
            if not review_trusted_inputs:
                note += (
                    " Legacy calls without trusted author/risk inputs prove only intrinsic eligibility. "
                    "budget substitution requires --review-author-model and --review-risk (code profile only)"
                )
            print(note, file=sys.stderr)
            return requested
        sub_info = agents.get(sub)
        if not (isinstance(sub_info, Mapping) and sub_info):
            raise BudgetGuardRefuseError(
                f"REVIEW_ROUTE_REFUSED: substitute --agent {sub} has no usable budget snapshot; refusing before spawn"
            )
        sub_dict = dict(sub_info)
        # #10016: the primary and substitute both use this allowance rule;
        # pace/reset-reserve writer routing cannot override review hard gates.
        sub_blocked, sub_reason = review_capacity_action(sub, sub_dict, diags, chosen)
        if sub_blocked:
            raise BudgetGuardRefuseError(
                f"REVIEW_ROUTE_REFUSED: resolver-selected substitute --agent {sub} is {sub_reason}; refusing before spawn"
            )
        print(
            f"🔄 HARD AUTO-SUBSTITUTE: REVIEW_IDENTITY_SUBSTITUTED: --agent {requested} → {sub} --model {chosen} "
            f"({reason}; reviewer resolver).",
            file=sys.stderr,
        )
        _remember_agent_substitution(
            model_resolution,
            source="reviewer-resolver",
            requested_agent=origin_agent or requested,
            requested_model=requested_model,
            actual_agent=sub,
            actual_model=chosen,
            how="reviewer-resolver",
        )
        return sub

    if not needs_action:
        return requested

    sub = fallbacks.get(requested)
    # The yaml `dispatch_fallbacks` map is the ONLY source for hard subs —
    # no inferred/hardcoded mappings (a deleted config entry must mean
    # refuse or advisory, not silently resurrect an old route).
    if sub and sub not in _DISPATCH_AGENT_CHOICES:
        print(
            f"⚠ ROUTING: dispatch_fallbacks maps {requested} → {sub}, not a known dispatch agent — ignoring hard sub.",
            file=sys.stderr,
        )
        sub = None
    if sub and sub != requested:
        if language_lane:
            return _language_lane_substitute(
                requested,
                fallbacks,
                agents if isinstance(agents, dict) else {},
                is_stale=is_stale,
                snapshot_metadata=diags,
                reset_reserve=reserve,
                requested_model=requested_model,
                model_resolution=model_resolution,
                origin_agent=origin_agent or requested,
            )
        chosen, how = _resolve_substitution_model(sub, requested_model)
        note = (
            f"🔄 HARD AUTO-SUBSTITUTE: --agent {requested} → {sub} "
            f"{_substitution_model_phrase(chosen, how, requested_model)} "
            f"({reason}; "
            f"sub per agent_fallback_substitutions.yaml dispatch_fallbacks). "
            "Substitution noted for operator contract / review independence."
        )
        print(note, file=sys.stderr)
        _remember_agent_substitution(
            model_resolution,
            source="budget-guard",
            requested_agent=origin_agent or requested,
            requested_model=requested_model,
            actual_agent=sub,
            actual_model=chosen,
            how=how,
        )
        if burn is not None:
            print(f"  (burn_pct_7d was ~{burn}%; resets_at={agent_info.get('resets_at')})", file=sys.stderr)
        return sub

    cooler = _budget_cooler_lanes(agents if isinstance(agents, dict) else {}, exclude=requested)
    cooler_txt = ", ".join(cooler) if cooler else "(none marked cool/warm in snapshot)"
    raise BudgetGuardRefuseError(
        f"ROUTING REFUSED: --agent {requested} is {reason} and "
        f"dispatch_fallbacks has no usable substitute. "
        f"Cooler seats from budget snapshot: {cooler_txt}. "
        "Re-route (see `python -m scripts.fleet.capacity_pick`) or pass --force-agent."
    )


def _language_lane_substitute(
    requested: str,
    fallbacks: Mapping[str, str],
    agents: dict[str, Any],
    *,
    is_stale: bool,
    snapshot_metadata: Mapping[str, Any] | None = None,
    reset_reserve: dict[str, Any] | None = None,
    requested_model: str | None = None,
    model_resolution: dict[str, Any] | None = None,
    origin_agent: str | None = None,
) -> str:
    """Walk fallbacks, staying inside claude/codex/agy (#8449)."""
    seat = requested
    seen = {seat}
    current_model = requested_model
    origin = origin_agent or requested
    while True:
        info = agents.get(seat, {}) or {}
        info_dict = info if isinstance(info, dict) else {}
        status = _budget_lane_status(seat, info_dict)
        will_last = _budget_will_last_to_reset(info_dict)
        reserve_relaxes = (
            seat == "codex"
            and _codex_is_threatened(info_dict)
            and _codex_reset_reserve_eligible(
                reset_reserve or {},
                info_dict,
                owner_capacity=_budget_owner_facts(
                    seat, info_dict, model=current_model, is_stale=is_stale, snapshot_metadata=snapshot_metadata
                ).capacity,
                snapshot_stale=is_stale,
            )
        )
        needs, why = (
            (False, "")
            if reserve_relaxes
            else _budget_needs_hard_capacity_action(
                status=status,
                will_last=will_last,
                is_stale=is_stale,
                snapshot_metadata=snapshot_metadata,
                pace=_budget_pace(info_dict),
                headroom_blocked=_budget_headroom_blocked(info_dict),
                lane=seat,
                info=info_dict,
                model=current_model,
            )
        )
        if not needs:
            return seat
        nxt = fallbacks.get(seat)
        if not nxt or nxt in seen or nxt not in _LANGUAGE_LANES:
            raise BudgetGuardRefuseError(
                "ROUTING REFUSED: LANGUAGE-LANES RULE (operator 2026-09-27). "
                f"Language work on --agent {requested} cannot move to "
                f"{nxt or 'no fallback'}; allowed lanes are claude, codex (GPT), and agy (Gemini)."
            )
        chosen, how = _resolve_substitution_model(nxt, current_model)
        print(
            f"🔄 HARD AUTO-SUBSTITUTE: --agent {seat} → {nxt} "
            f"{_substitution_model_phrase(chosen, how, current_model)} "
            f"({why}; language-lane fallback stays inside claude, codex, agy).",
            file=sys.stderr,
        )
        _remember_agent_substitution(
            model_resolution,
            source="budget-guard",
            requested_agent=origin,
            requested_model=requested_model,
            actual_agent=nxt,
            actual_model=chosen,
            how=how,
        )
        current_model = chosen
        seen.add(nxt)
        seat = nxt
        if len(seen) > len(_LANGUAGE_LANES):
            raise BudgetGuardRefuseError("ROUTING REFUSED: language-lane fallback chain did not reach a cool seat.")


def _session_stream_store() -> Any:
    """Build the canonical read-only session-stream store used by fleet code."""
    from agents_extensions.shared.session_streams.db import DEFAULT_RELATIVE_DATABASE, SessionStreamDatabase
    from agents_extensions.shared.session_streams.store import SessionStreamStore

    return SessionStreamStore(SessionStreamDatabase(_REPO_ROOT / DEFAULT_RELATIVE_DATABASE))


def _find_live_cursor_driver_lease() -> dict[str, Any] | None:
    """Return one live Cursor process-driver lease, or ``None`` when absent.

    The session-stream database is the sole source of truth here. A missing
    store file means absence (no live lease), not refusal. An unreadable or
    malformed existing store still refuses admission rather than allowing an
    unverifiable Cursor spawn.
    """
    try:
        from agents_extensions.shared.session_streams.model import parse_timestamp

        store = _session_stream_store()
        database = getattr(store, "database", None)
        database_path = getattr(database, "path", None)
        if database_path is not None and not Path(database_path).is_file():
            return None

        projections = store.list_remote_projections()
        now = datetime.now(UTC)
        for projection in projections:
            if not isinstance(projection, dict):
                raise ValueError("session-stream projection is not an object")

            nested_lease = projection.get("lease")
            lease = nested_lease if isinstance(nested_lease, dict) else projection
            holder_agent = str(lease.get("holder_agent") or "").strip().lower()
            if holder_agent != "cursor":
                continue
            if str(lease.get("holder_harness") or "").strip().lower() != "cursor-agent":
                continue
            if str(lease.get("holder_kind") or "process").strip().lower() != "process":
                continue
            if str(lease.get("state") or "").strip().lower() != "active":
                continue
            session_state = str(lease.get("session_state") or projection.get("session_state") or "").strip().lower()
            if session_state not in {"open", "rolling"}:
                continue
            if lease.get("session_expired_at") or projection.get("session_expired_at"):
                continue

            expires_at = lease.get("expires_at")
            if not isinstance(expires_at, str) or not expires_at.strip():
                raise ValueError("Cursor lease has no expiry")
            if parse_timestamp(expires_at) > now:
                return lease
        return None
    except CapacityGuardRefuseError:
        raise
    except Exception as exc:
        raise CapacityGuardRefuseError(
            "CAPACITY REFUSED: unable to verify the session-stream store for a live Cursor driver lease; "
            "use --force-agent to override."
        ) from exc


def _proc_parent_pid(pid: int) -> int:
    """Return the parent pid of ``pid`` from Linux ``/proc``."""
    stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8", errors="replace")
    # comm is parenthesized and may contain spaces or ')'; the fields after the
    # final ')' are state, ppid, ...
    return int(stat.rsplit(")", 1)[1].split()[1])


def _process_is_self_or_ancestor(holder_pid: int) -> bool:
    """True when ``holder_pid`` is this process or one of its ancestors."""
    pid = os.getpid()
    seen: set[int] = set()
    while pid > 0 and pid not in seen:
        if pid == holder_pid:
            return True
        seen.add(pid)
        pid = _proc_parent_pid(pid)
    return False


def _cursor_driver_lease_is_self_dispatch(lease: dict[str, Any]) -> bool:
    """True only when the live Cursor driver lease belongs to this process tree.

    The documented rule refuses ``--agent cursor`` only from within the Cursor
    driver session itself (the self-dispatch deadlock case). A lease held on
    another host, or by an unrelated local process, is another lane's driver:
    concurrent Cursor workers are allowed. An ancestry lookup failure (no
    /proc, permission error) is treated as "not self" so dispatch never
    crashes on the probe.
    """
    holder_host_id = str(lease.get("holder_host_id") or "").strip().lower()
    if holder_host_id:
        try:
            try:
                from scripts.api.occupancy_local import resolve_launcher_host_id
            except ImportError:
                from api.occupancy_local import resolve_launcher_host_id

            local_host_id = resolve_launcher_host_id()
        except Exception:
            local_host_id = ""
        if local_host_id and holder_host_id != str(local_host_id).strip().lower():
            return False
    holder_pid = lease.get("holder_process_id")
    if not isinstance(holder_pid, int) or isinstance(holder_pid, bool) or holder_pid <= 0:
        return False
    try:
        return _process_is_self_or_ancestor(holder_pid)
    except Exception:
        print(
            "NOTE: unable to verify the Cursor driver lease holder ancestry; "
            "treating the live lease as another session and spawning --agent cursor.",
            file=sys.stderr,
        )
        return False


def _check_capacity_hint(dispatch_agent: str, args: argparse.Namespace | None = None) -> None:
    """Refuse Cursor driver-lease self-dispatch; otherwise retain the busy-lane hint."""
    target_norm = str(dispatch_agent or "").strip().lower()
    force_agent = bool(getattr(args, "force_agent", False)) if args is not None else False

    if target_norm == "cursor":
        try:
            cursor_driver_lease = _find_live_cursor_driver_lease()
        except CapacityGuardRefuseError:
            if not force_agent:
                raise
            print(
                "NOTE: --force-agent overrides Cursor driver-lease admission after the live lease check failed; "
                "spawning --agent cursor.",
                file=sys.stderr,
            )
        else:
            if cursor_driver_lease is not None:
                if _cursor_driver_lease_is_self_dispatch(cursor_driver_lease):
                    if not force_agent:
                        raise CapacityGuardRefuseError(
                            "CAPACITY REFUSED: --agent cursor dispatch from inside the live Cursor "
                            "driver session (the stream lease is held by this process tree); refusing "
                            "worker spawn. Dispatch from outside the Cursor driver session, or pass "
                            "--force-agent to override."
                        )
                    print(
                        "NOTE: --force-agent overrides the live Cursor driver stream lease; spawning --agent cursor.",
                        file=sys.stderr,
                    )
                else:
                    stream_id = str(cursor_driver_lease.get("stream_id") or "").strip() or "unknown stream"
                    print(
                        f"NOTE: Cursor driver live on {stream_id} (other session); spawning a separate Cursor worker.",
                        file=sys.stderr,
                    )

    if args is not None and (getattr(args, "json", False) or getattr(args, "quiet", False)):
        return

    with contextlib.suppress(Exception):
        try:
            from scripts.api.lane_health import compute_lane_health, normalize_agent_name
        except ImportError:
            from api.lane_health import compute_lane_health, normalize_agent_name

        from agent_runtime.agent_identity import RETIRED_AGENT_ALIASES
        from scripts.agent_runtime.kimi_admission import DirectoryTree

        # "gemini" excluded: it is a permanent retired-CLI alias (→ agy), so
        # it must never appear as a "idle capacity available in: gemini"
        # suggestion — that would just point drivers back at the dead CLI.
        # "kimi" is suggested only when this dispatch is web, UI or backend coding that a
        # Kimi seat would admit (default public repo, no refusal reason).
        target_norm = normalize_agent_name(dispatch_agent) or target_norm
        # A suggestion only: the owned paths are read in this checkout, not in a worker's tree.
        kimi_admissible = target_norm == "kimi" or (
            args is not None
            and getattr(args, "repo", None) is None
            and _kimi_admission_refusal(args, agent="kimi", trees=(DirectoryTree(_REPO_ROOT),)) is None
        )
        subscription_lanes = tuple(
            lane
            for lane in ("claude", "codex", "gemini", "grok", "cursor", "kimi")
            if lane not in RETIRED_AGENT_ALIASES and (lane != "kimi" or kimi_admissible)
        )

        in_flight: dict[str, int] = {lane: 0 for lane in subscription_lanes}
        if tasks_dir().is_dir():
            for state_file in tasks_dir().glob("*.json"):
                state = _read_state(state_file)
                if not state or state.get("status") not in ("running", "spawning"):
                    continue
                pid = state.get("pid")
                if pid and not _pid_alive(int(pid)):
                    continue
                agent_norm = normalize_agent_name(state.get("agent"))
                if agent_norm in in_flight:
                    in_flight[agent_norm] += 1

        busy_count = in_flight.get(target_norm, 0)
        if busy_count <= 0:
            return

        health: dict[str, Any] = {}
        with contextlib.suppress(Exception):
            health = compute_lane_health(tasks_dir())

        idle_lanes = [
            lane
            for lane in subscription_lanes
            if lane != target_norm and in_flight.get(lane, 0) == 0 and health.get(lane, {}).get("healthy", True)
        ]

        if idle_lanes:
            idle_str = ", ".join(idle_lanes)
            print(
                f"💡 Note: lane '{target_norm}' has {busy_count} task(s) in flight while idle capacity is available in: {idle_str}",
                file=sys.stderr,
            )


def _status_or_fail_payload(task_id: str, *, run_nonce: str | None = None) -> dict[str, Any]:
    payload = _fetch_monitor_task(task_id, run_nonce=run_nonce)
    if payload is None:
        return {"task_id": task_id, "status": "task not found", "age_s": 0}

    task = payload.get("task") if isinstance(payload.get("task"), dict) else {}
    status = str(task.get("status") or "unknown")
    if status == "running" and payload.get("alive") is False:
        status = "stale"
    result = {
        "task_id": task.get("task_id") or task_id,
        "status": status,
        "age_s": _age_seconds_from_started_at(task.get("started_at")),
        "alive": payload.get("alive"),
    }
    if run_nonce is not None:
        result["run_nonce"] = task.get("run_nonce")
    return result


def cmd_status_or_fail(args: argparse.Namespace) -> int:
    """Exit 0 only when Monitor API confirms a task is currently running."""
    run_nonce = getattr(args, "run_nonce", None)
    try:
        status = _status_or_fail_payload(args.task_id, run_nonce=run_nonce)
    except MonitorApiUnavailable as exc:
        print(f"Monitor API unreachable: {exc}", file=sys.stderr)
        return 2

    if getattr(args, "verbose", False):
        print(json.dumps(status, indent=2, default=str))

    if status["status"] == "running":
        return 0

    print(
        f"task {args.task_id} is not running (status={status['status']}, age={status['age_s']}s)",
        file=sys.stderr,
    )
    return 1


# ---------------------------------------------------------------------------
# Wait command — poll until terminal state or timeout
# ---------------------------------------------------------------------------

_TERMINAL_STATUSES = frozenset(
    {
        "done",
        "failed",
        "timeout",
        "rate_limited",
        "crashed",
        "cancelled",
        "dry_run",
        # A worker that settles as ``needs_finalize`` HAS finished — the status
        # flags leftover work for a human, it does not mean "still running".
        # Omitting it made ``delegate.py wait`` poll a finished task until its
        # own timeout, and made ``cancel`` willing to signal a stored PID the OS
        # may already have recycled. Worktree claims differ on purpose: a
        # ``needs_finalize`` record still claims its checkout for the leftover
        # work (see _RELEASED_TASK_STATUSES).
        "needs_finalize",
        _NO_DELIVERABLE_STATUS,
    },
)


def cmd_wait(args: argparse.Namespace) -> int:
    poll_interval = max(0.5, float(args.poll_interval))
    deadline = time.monotonic() + float(args.timeout) if args.timeout else None
    expected_nonce = getattr(args, "run_nonce", None)

    while True:
        state_path, state = _read_state_or_archived(args.task_id)
        if state is None:
            if expected_nonce is not None and (deadline is None or time.monotonic() < deadline):
                time.sleep(poll_interval)
                continue
            print(
                json.dumps({"error": f"no state file for task {args.task_id!r}"}),
            )
            return 1

        record_nonce = state.get("run_nonce")
        if expected_nonce is not None and record_nonce != expected_nonce:
            if deadline and time.monotonic() >= deadline:
                print(
                    json.dumps(
                        {
                            "error": "stale_run_nonce",
                            "task_id": args.task_id,
                            "expected_run_nonce": expected_nonce,
                            "record_run_nonce": record_nonce,
                            "last_known_status": state.get("status"),
                            "waited_s": args.timeout,
                        }
                    ),
                    file=sys.stderr,
                )
                return 1
            time.sleep(poll_interval)
            continue

        # Zombie probe (same logic as cmd_status)
        _heal_dead_task(state_path, state, source="wait")

        status = state.get("status")
        if status in _TERMINAL_STATUSES:
            print(json.dumps(state, indent=2, default=str))
            # Exit code: 0 if done, 1 otherwise (failed/crashed/rate_limited)
            if status == "timeout":
                return 124
            return 0 if status == "done" else 1

        if deadline and time.monotonic() >= deadline:
            print(
                json.dumps(
                    {
                        "error": "timeout",
                        "task_id": args.task_id,
                        "last_known_status": status,
                        "waited_s": args.timeout,
                    }
                ),
                file=sys.stderr,
            )
            return 124  # conventional timeout exit code

        time.sleep(poll_interval)


# ---------------------------------------------------------------------------
# Cancel command — signal the worker
# ---------------------------------------------------------------------------


def cmd_cancel(args: argparse.Namespace) -> int:
    """Send SIGTERM to the worker's PID. Lets the runtime unwind cleanly.

    Refuses to signal a task whose status is already terminal (done,
    failed, crashed, cancelled, rate_limited). Otherwise we'd be
    signalling a PID that the OS may have recycled to some unrelated
    process. Codex 2026-04-10 audit finding.
    """
    state_path = _state_path(args.task_id)
    state = _read_state(state_path)
    if state is None:
        print(f"❌ no state file for task {args.task_id!r}", file=sys.stderr)
        return 1

    expected_nonce = getattr(args, "run_nonce", None)
    if expected_nonce is not None and state.get("run_nonce") != expected_nonce:
        print(
            f"❌ task {args.task_id!r} run_nonce mismatch (expected {expected_nonce!r}, "
            f"got {state.get('run_nonce')!r}); refusing to cancel unrelated worker",
            file=sys.stderr,
        )
        return 1

    status = state.get("status")
    if status in _TERMINAL_STATUSES:
        print(
            f"⚠️  task {args.task_id!r} is already in terminal state "
            f"{status!r}; refusing to signal the stored PID "
            f"(could be recycled by the OS).",
            file=sys.stderr,
        )
        return 1

    if status not in ("running", "spawning"):
        print(
            f"❌ task {args.task_id!r} has unexpected status {status!r}; refusing to cancel.",
            file=sys.stderr,
        )
        return 1

    pid = state.get("pid")
    if not pid:
        print(f"❌ state has no pid for {args.task_id!r}", file=sys.stderr)
        return 1

    pid = int(pid)
    if not _pid_alive(pid):
        print(f"⚠️  pid {pid} is already dead; nothing to cancel")
        return 0

    try:
        os.kill(pid, signal.SIGTERM)
        print(f"✅ SIGTERM sent to pid {pid}")
        return 0
    except PermissionError:
        print(f"❌ permission denied signalling pid {pid}", file=sys.stderr)
        return 1
    except ProcessLookupError:
        print(f"⚠️  pid {pid} vanished before we could signal it")
        return 0


# ---------------------------------------------------------------------------
# List command — show all tasks (for operators)
# ---------------------------------------------------------------------------


def cmd_list(args: argparse.Namespace) -> int:
    """Print task summaries as a JSON list.

    History is bounded to the hot directory unless ``--all`` is given: records
    ``stale_task_records archive`` moved to ``archive/`` (#8625) are then listed
    too, marked ``"archived": true``. Without ``--all`` a stderr note counts the
    archived records left out.
    """
    tasks_dir().mkdir(parents=True, exist_ok=True)
    include_archive = bool(getattr(args, "all", False))
    tasks: list[dict[str, Any]] = []
    flat_tasks: list[str] = []
    for state_file in task_record_store.iter_task_records(tasks_dir(), include_archive=include_archive):
        state = _read_state(state_file)
        if state is None:
            continue
        # Zombie probe inline for running tasks
        _heal_dead_task(state_file, state, source="list")
        if args.status and state.get("status") != args.status:
            continue
        # Fix 4 (#1476): classify worktree layout so operators can see at
        # a glance which tasks are on the deprecated flat path.
        layout = state.get("worktree_layout") or _classify_worktree_layout(
            state.get("worktree_path"),
        )
        if layout == "flat":
            flat_tasks.append(str(state.get("task_id")))
        tasks.append(
            {
                "task_id": state.get("task_id"),
                "agent": state.get("agent"),
                "model": state.get("model"),
                "effort": state.get("effort"),
                "cli_version": state.get("cli_version"),
                "status": state.get("status"),
                "started_at": state.get("started_at"),
                "duration_s": state.get("duration_s"),
                "worktree_path": state.get("worktree_path"),
                "worktree_layout": layout,
                **({"archived": True} if state_file.parent.name == task_record_store.ARCHIVE_DIR_NAME else {}),
            }
        )
    print(json.dumps(tasks, indent=2, default=str))
    if not include_archive:
        archive_dir = tasks_dir() / task_record_store.ARCHIVE_DIR_NAME
        archived = sum(1 for _ in task_record_store.iter_task_records(archive_dir, include_archive=False))
        if archived:
            print(
                f"ℹ️  history is the hot directory only: {archived} archived record(s) not listed; pass --all.",
                file=sys.stderr,
            )
    if flat_tasks:
        print(
            f"⚠️  {len(flat_tasks)} task(s) use the DEPRECATED flat worktree "
            f"layout: {flat_tasks[:5]}" + (" …" if len(flat_tasks) > 5 else "") + ". New dispatches should use "
            "`.worktrees/dispatch/{agent}/{task}/`.",
            file=sys.stderr,
        )
    return 0


def cmd_backfill_repository(args: argparse.Namespace) -> int:
    """Stamp authoritative ``repository`` identity on legacy task states (#7083).

    Task states written before dispatch-time attribution have no
    ``repository`` / ``repository_id`` claim, so the public Work projection's
    repository-scoped delegate join (correctly) drops them and reports
    ``delegate_tasks.count=0``. This rewrites history the same way new
    dispatches stamp it: the target's git ``remote.origin.url`` is read by the
    owner of the state directory — never inferred by projection readers from
    paths, branches, or task ids.

    Dry-run by default; ``--apply`` performs the atomic write-rename updates.
    Existing claims are authoritative: consistent claims are kept, conflicting
    claims are reported and never overwritten. Targets whose repository cannot
    be proven stay unclassified.
    """
    apply_changes = bool(getattr(args, "apply", False))
    if not tasks_dir().is_dir():
        print(f"❌ tasks dir not found: {tasks_dir()}", file=sys.stderr)
        return 1
    scanned = stamped = already = unresolved = conflicts = errors = 0
    # Archived records (#8625) are history too; they are stamped where they lie.
    for state_file in task_record_store.iter_task_records(tasks_dir(), include_archive=True):
        state = _read_state(state_file)
        if state is None:
            continue
        scanned += 1
        task_id = str(state.get("task_id") or state_file.stem)
        claims = _state_repository_claims(state)
        if len(claims) == 1:
            already += 1
            continue
        if len(claims) > 1:
            conflicts += 1
            print(
                f"⚠️  {task_id}: conflicting repository claims {claims}; left untouched",
                file=sys.stderr,
            )
            continue
        target = state.get("worktree_path") or state.get("cwd")
        slug = _resolve_dispatch_repository(target)
        if slug is None:
            unresolved += 1
            print(
                f"⚠️  {task_id}: cannot prove repository from recorded target; left unclassified",
                file=sys.stderr,
            )
            continue
        if apply_changes:
            state["repository"] = slug
            try:
                _write_state_atomic(state_file, state)
            except OSError as exc:
                errors += 1
                print(f"❌ {task_id}: failed to write stamp: {exc}", file=sys.stderr)
                continue
        stamped += 1
        print(f"{'✅' if apply_changes else '🔎'} {task_id}: repository={slug}")
    mode = "apply" if apply_changes else "dry-run"
    print(
        f"repository backfill ({mode}): scanned={scanned} stamped={stamped} "
        f"already_attributed={already} unresolved={unresolved} "
        f"conflicts={conflicts} errors={errors}"
    )
    if not apply_changes and stamped:
        print("dry-run only — re-run with --apply to write these stamps")
    return 1 if errors else 0


# ---------------------------------------------------------------------------
# _worker command — internal, called by cmd_dispatch's spawned process
# ---------------------------------------------------------------------------


def cmd_worker(args: argparse.Namespace) -> int:
    """Internal entrypoint for the detached worker subprocess."""
    prompt = sys.stdin.read()
    return _run_worker(
        task_id=args.task_id,
        agent=args.agent,
        prompt=prompt,
        mode=args.mode,
        cwd_str=args.cwd,
        model=args.model,
        hard_timeout=args.hard_timeout,
        provider=getattr(args, "provider", None),
        output_schema_path=getattr(args, "output_schema", None),
        output_schema_sha256=getattr(args, "output_schema_sha256", None),
        harness=getattr(args, "harness", None),
        silence_timeout=args.silence_timeout,
        max_budget_usd=getattr(args, "max_budget_usd", None),
        effort=args.effort,
        initial_response_timeout=getattr(
            args,
            "initial_response_timeout",
            DEFAULT_INITIAL_RESPONSE_TIMEOUT_S,
        ),
        keep_worktree=bool(getattr(args, "keep_worktree", False)),
        require_review_verdict=bool(getattr(args, "require_review_verdict", False)),
        runtime_tmp_root=getattr(args, "runtime_tmp_root", None),
        runtime_tmp_namespace_root=getattr(args, "runtime_tmp_namespace_root", None),
        run_nonce=getattr(args, "run_nonce", None) or os.environ.get("LU_RUNTIME_RUN_NONCE"),
        review_id=getattr(args, "review_id", None),
        attempt_id=getattr(args, "attempt_id", None),
        mcp_config_path=getattr(args, "mcp_config_path", None),
        strict_mcp_config=bool(getattr(args, "strict_mcp_config", False)),
        review_manifest=getattr(args, "review_manifest", None),
        review_input_root=getattr(args, "review_input_root", None),
        review_access=getattr(args, "review_access", "isolated"),
        finalize_open_pr=bool(getattr(args, "finalize_open_pr", False)),
    )


# ---------------------------------------------------------------------------
# CLI glue
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="delegate.py",
        description=(
            "Dispatch async agent_runtime tasks and monitor their lifecycle.\n"
            "Use it for long-running background agent work; do not use it for one-shot local invocations."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/delegate.py dispatch --agent codex --task-id review-123 --prompt-file prompt.md --mode read-only\n"
            "  .venv/bin/python scripts/delegate.py dispatch --agent codex --task-id fix-123 --prompt-file brief.md --mode workspace-write --worktree\n"
            "  .venv/bin/python scripts/delegate.py dispatch --agent codex --task-id pr-123 --prompt-file brief.md --mode danger --worktree\n"
            "  .venv/bin/python scripts/delegate.py dispatch --agent claude --task-id review-456 --prompt-file brief.md --max-budget-usd 0.50\n"
            "  .venv/bin/python scripts/delegate.py status-or-fail review-123\n"
            "  .venv/bin/python scripts/delegate.py wait review-123 --timeout 600\n"
            "  .venv/bin/python scripts/delegate.py list --status running\n\n"
            "Outputs:\n"
            "  Persists task state under batch_state/tasks/ and streams worker output to task-owned logs.\n\n"
            "Timeouts:\n"
            "  --hard-timeout is the absolute wall-clock fallback for the worker.\n"
            "  --silence-timeout kills the agent CLI earlier when no watchdog activity arrives within the window.\n"
            f"    Default is {DEFAULT_SILENCE_TIMEOUT_S}s to tolerate quiet build/test phases; 0 disables it.\n\n"
            "  --max-budget-usd caps Claude Code API spend for this dispatch when set; omitted means no dollar cap.\n\n"
            "Placement & VPS Forwarding:\n"
            "  Dual-host occupancy routes dispatches to healthy VPS worker hosts when available.\n"
            "  Forwarding requires host environment variables in the launcher environment:\n"
            "    LU_JOB_DISPATCH_HOST (or ATLAS_RUNNER_HOST) and LU_JOB_REPO for host-job\n"
            "    LU_TEACHER_DISPATCH_HOST (or LU_DISPATCH_SSH) and LU_TEACHER_REPO for host-teacher\n"
            "  To bypass VPS forwarding and force local spawn: export LU_ALLOW_NOTEBOOK_DISPATCH=1\n"
            "  Configuration errors fail closed without fallback to prevent silent local drift.\n\n"
            "Exit codes:\n"
            "  0 on successful command completion; non-zero on CLI misuse or worker/task failures;\n"
            "  dispatch exits 3 when host admission refuses a write worker (see `dispatch --help`).\n\n"
            "Related:\n"
            "  Runtime: scripts/agent_runtime/\n"
            "  Rule: agents_extensions/shared/rules/delegate-must-use-worktree.md\n"
            "  Issue: #1379, #7230\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="command", required=True)

    rescue = sub.add_parser(
        "rescue",
        help="Inspect or preserve terminal dispatch work on rescue/<agent>/<task>.",
        description=(
            "Preserve terminal non-success dispatch work on a verified rescue branch.\n"
            "Use after a worker exits; --all-stale previews candidates unless --apply is set."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/delegate.py rescue impl-8508\n"
            "  .venv/bin/python scripts/delegate.py rescue --all-stale --older-than 6h\n"
            "  .venv/bin/python scripts/delegate.py rescue --all-stale --older-than 6h --apply\n\n"
            "Outputs: JSON summary and task dispositions; apply may clean residue, commit, and push rescue refs.\n"
            "Exit codes: 0 inspection or rescue completed; 1 rescue error; 2 invalid arguments.\n"
            "Related: docs/runbooks/worktree-cleanup.md; issue #8508."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    rescue.add_argument("task_id", nargs="?", help="One terminal task ID, e.g. impl-8508; applies immediately.")
    rescue.add_argument("--all-stale", action="store_true", help="Inspect all terminal tasks older than --older-than.")
    rescue.add_argument("--older-than", default="6h", metavar="HOURS", help="Minimum terminal age (default: 6h).")
    rescue.add_argument(
        "--apply", action="store_true", help="Apply rescue to --all-stale candidates (default: dry-run)."
    )
    rescue.set_defaults(func=cmd_rescue)

    # dispatch
    def _dispatch_help_formatter(prog: str) -> argparse.HelpFormatter:
        return argparse.RawDescriptionHelpFormatter(prog, max_help_position=36, width=120)

    admission_defaults = dispatch_admission.config_defaults()
    d = sub.add_parser(
        "dispatch",
        help="Fire a task, return immediately (stdout: `<task_id>\\n<run_nonce>`)",
        description=(
            "Fire an async agent task and return immediately with the task ID and run nonce.\n"
            "Routes to available VPS worker hosts unless LU_ALLOW_NOTEBOOK_DISPATCH=1 is set.\n"
            "Forward configuration requires LU_JOB_DISPATCH_HOST (or ATLAS_RUNNER_HOST) and LU_JOB_REPO."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/delegate.py dispatch --agent codex --task-id fix-123 --prompt-file brief.md "
            "--mode workspace-write --worktree\n"
            "  DISPATCH_MAX_LIVE_WRITE_WORKERS=0 .venv/bin/python scripts/delegate.py dispatch --agent codex "
            "--task-id probe-1 --prompt x --mode workspace-write --worktree --dry-run\n"
            '  .venv/bin/python scripts/delegate.py dispatch ... --force-admission "hotfix for #1234; one worker is draining"\n\n'
            "Host admission (#8645; workspace-write and danger only, read-only is exempt):\n"
            "  Refuses a new worker when live write workers (running/spawning, pid alive) reach "
            f"DISPATCH_MAX_LIVE_WRITE_WORKERS (default {admission_defaults.max_live_write_workers}),\n"
            f"  /proc/meminfo MemAvailable is below DISPATCH_MIN_MEM_AVAILABLE_GIB (default "
            f"{admission_defaults.min_mem_available_gib:g} GiB), or the 1-minute load per CPU\n"
            f"  exceeds DISPATCH_MAX_LOAD_PER_CPU (default {admission_defaults.max_load_per_cpu:g}). "
            "Environment variables override the scripts/config.py defaults.\n"
            "  Without /proc (macOS) memory and CPU are unknown and only the worker cap applies. Records whose pid\n"
            "  is dead are marked crashed first. The final check holds a host-wide lock until the spawning record\n"
            "  is published. Preview the decision with: .venv/bin/python -m scripts.fleet.capacity_pick\n\n"
            "Outputs:\n"
            "  stdout `<task_id>\\n<run_nonce>`; batch_state/tasks/<task_id>.json (write modes carry an `admission`\n"
            "  snapshot; `launch_mode` is `scope` or `popen-fallback`; terminal records carry `peak_rss_mib`);\n"
            "  worker logs under batch_state/tasks/logs/. Workers run in the user slice lu-dispatch.slice when\n"
            "  that slice is installed with its memory limits; otherwise dispatch warns and uses plain Popen.\n"
            "  A scoped start that does not prove the worker never started is marked failed and is not relaunched.\n"
            "  LU_DISPATCH_ISOLATION=fallback forces the plain Popen path. See packaging/systemd/README.md.\n\n"
            "Exit codes:\n"
            "  0 dispatched, or --dry-run validated; 1 worktree, lease, or spawn failure;\n"
            "  2 invalid request or another guard refused; 3 host admission refused (retry later or --force-admission).\n\n"
            "Related:\n"
            "  scripts/orchestration/dispatch_admission.py; docs/bug-autopsies/2026-09-24-dispatch-fanout-oom.md; #8645\n"
        ),
        formatter_class=_dispatch_help_formatter,
    )
    d.add_argument(
        "--agent",
        required=True,
        choices=list(_DISPATCH_AGENT_CHOICES),
        # "qwen" removed from choices (banned agent): advertising it in --help
        # while the routing guard rejects it at dispatch is a UX trap. The
        # guard still catches programmatic Namespace bypass.
        help="Agent to run for the task: codex, gemini (retired CLI — permanent "
        "alias to agy, do not install gemini), claude, grok "
        "(native CLI; grok-build=alias), grok-hermes, deepseek, agy, cursor, or kimi "
        "(web, UI and backend coding only: workspace-write in site UI, scripts/ and tests/; "
        "Ukrainian-language content, reviews, consults, design and rules are refused).",
    )
    d.add_argument(
        "--harness",
        choices=sorted(_KIMI_HARNESSES),
        default=None,
        help=(
            "Opt-in Kimi transport. Only valid with --agent kimi; use kimicc "
            "for Kimi through headless Claude Code. Omit to keep native Kimi Code. "
            "'native' is observability-only: it records harness=native in task "
            "state and is functionally identical to omitting the flag (#5938)."
        ),
    )
    d.add_argument("--task-id", required=True, help="Stable task identifier used for state/log files, e.g. review-123.")
    d.add_argument(
        "--force-new",
        action="store_true",
        help=(
            "Reuse an existing --task-id by first archiving the prior record "
            "and result alongside (never clobber). Required when the task "
            "record is terminal and has the caller's initiator (#9075). "
            "Refuses nonterminal or foreign records even when their pid is dead."
        ),
    )
    d.add_argument(
        "--force-admission",
        metavar="REASON",
        default=None,
        help=(
            "Start a write-capable worker even when host admission refuses it (live write-worker cap, "
            "MemAvailable floor, or load per CPU; #8645). REASON is required and is recorded in the "
            "task record under admission.force_reason."
        ),
    )
    d.add_argument(
        "--initiator",
        default=None,
        help=(
            "Initiating orchestrator identity for runtime attribution. Launcher "
            "and Codex Desktop identity are detected automatically when omitted."
        ),
    )
    d.add_argument(
        "--run-nonce",
        default=None,
        help="Unique run identifier for detecting stale cross-host task records (#7168).",
    )
    d.add_argument("--prompt", help="Prompt text, or '-' to read the prompt from stdin.")
    d.add_argument("--prompt-file", help="Read the prompt body from this file path.")
    d.add_argument(
        "--allow-dor-warn",
        metavar="REASON",
        help="Allow an implementation dispatch with a WARN issue card; record the required reason in task JSON.",
    )
    d.add_argument(
        "--lifecycle-file",
        help=(
            "Canonical task-lifecycle.v1 ledger to validate and carry in the worker prompt/state. "
            "Invalid ledgers fail before worktree or worker side effects."
        ),
    )
    d.add_argument(
        "--mode",
        default="read-only",
        choices=["read-only", "workspace-write", "danger"],
        help="Runtime mode (default: read-only). Read-only rejects write-shaped "
        "prompts; workspace-write and danger "
        "require a verified dispatch worktree (bare --worktree, or --cwd "
        "pointing at an existing added worktree); read-only defaults to an isolated detached worktree.",
    )
    d.add_argument("--model", default=None, help="Optional model override, e.g. gpt-6.1-sol or gemini-3.1-pro-preview.")
    d.add_argument(
        "--provider",
        default=None,
        choices=["openrouter"],
        help="Opt-in provider for Hermes-routed agents (e.g. deepseek). "
        "Default for DeepSeek is first-party (local-only). "
        "Use --provider openrouter for US-residency pinned path.",
    )
    d.add_argument(
        "--effort",
        default=None,
        choices=["low", "medium", "high", "xhigh", "max"],
        help=(
            "Optional reasoning / effort level. Accepted: low, medium, "
            "high, xhigh, max. Omit to use the agent's own default: "
            "Codex falls through to ~/.codex/config.toml (currently high); "
            "Claude falls through to its CLI default (currently high for "
            "Opus/Sonnet 4.6+ per CC 1.117); Gemini effort is not yet "
            "wired (gemini-cli does not expose the flag) and is a no-op. "
            "See #1396."
        ),
    )
    d.add_argument(
        "--repo",
        default=None,
        metavar="KEY",
        help=(
            "Allowlisted fleet repository for worktree creation and GitHub "
            "targeting (#672 P2.1). Keys come from scripts/config/fleet_repos.yaml "
            "(public, infra-private, hramatka). Default: public primary. Sibling "
            "write modes require --worktree (auto) or --cwd; task state stays on the "
            "public primary control plane. Legacy manual sibling --cwd flow remains valid."
        ),
    )
    d.add_argument(
        "--cwd",
        default=None,
        help="Working directory for the worker (read-only defaults to a detached dispatch worktree; "
        "an explicit primary root also gets a detached worktree). "
        "Other --cwd targets must be verified added worktrees. "
        "Workspace-write/danger may never use the primary checkout — prefer --worktree. "
        "Sibling-repo flow: prefer `--repo KEY --worktree`, or manual "
        "`git worktree add` then `--cwd <that-worktree>` without `--worktree`.",
    )
    d.add_argument(
        "--worktree",
        nargs="?",
        const="auto",
        default=None,
        help=(
            "Run inside this git worktree (created on demand). Required for "
            "write-capable modes (workspace-write, danger). Pass `--worktree` "
            "alone (recommended) to auto-derive `.worktrees/dispatch/{agent}/"
            "{task}/` under the primary checkout that owns this script, or "
            "`--worktree PATH` to reuse a specific added worktree inside "
            "`.worktrees/dispatch/{agent}/` (validated against the expected "
            "dispatch branch before reuse; paths elsewhere, under a symlinked "
            "anchor, or with control or format characters are refused, #8775). "
            "Refuses when the invocation cwd is a different git root (#6900)."
        ),
    )
    d.add_argument(
        "--pr",
        type=int,
        default=None,
        help=(
            "Review this same-repo PR. The head SHA is resolved once and pinned; "
            "a later fetch of a different tip refuses the dispatch."
        ),
    )
    d.add_argument(
        "--pinned-head",
        default=None,
        metavar="SHA",
        help=(
            "Exact commit the worktree must check out. A fetched branch tip that "
            "differs from this SHA refuses the dispatch. Requires --branch or --pr; "
            "without either, refuses before probes or task/worktree creation. Default: None."
        ),
    )
    d.add_argument(
        "--branch",
        default=None,
        metavar="EXISTING",
        help=(
            "Continue an existing remote branch, e.g. codex/fix-123. "
            "For a new branch omit --branch (default: <agent>/<task-id>), optionally with --base. "
            "Fetches and validates the branch from the primary "
            "checkout, then creates/reuses an isolated worktree on it (--branch "
            "implies --worktree). Refuses protected branches (main/master), "
            "branches checked out in another worktree, and invocation from a "
            "different git root (#6900). --branch must omit origin/ and refs/ prefixes."
        ),
    )
    d.add_argument(
        "--keep-worktree",
        action="store_true",
        help=(
            "Keep a successful clean dispatch worktree instead of reaping it "
            "after the branch is recoverable from origin or PR state."
        ),
    )
    d.add_argument(
        "--finalize-open-pr",
        action="store_true",
        help="Explicitly open a draft PR after a successful dirty-worktree auto-finalize push.",
    )
    d.add_argument(
        "--require-review-verdict",
        action="store_true",
        help=(
            "Review-typed dispatch: a run that settles done without a "
            "`VERDICT: APPROVE|APPROVED|CHANGES_REQUESTED|REQUEST_CHANGES|BLOCKED` line of its own in the "
            "reply terminalizes as no_deliverable instead (#8421). Used by the "
            "ask-* review wrapper; ordinary dispatches are unaffected. "
            "On agy/gemini this also requires --review-profile code or ukrainian. "
            "Native AGY code review requires low or medium risk and resolver admission; "
            "Ukrainian review targets must be Ukrainian-content diffs."
        ),
    )
    d.add_argument(
        "--review-profile",
        default=None,
        choices=("code", "infra", "ukrainian"),
        help=(
            "Required with --require-review-verdict when --agent is agy or gemini. "
            "Native AGY admits code at low or medium risk through the reviewer resolver, "
            "excluding security-sensitive paths; infra is refused. "
            "Ukrainian content review must pass ukrainian."
        ),
    )
    d.add_argument(
        "--review-author-model",
        default=None,
        metavar="MODEL",
        help=(
            "Author's concrete model for cross-family reviewer resolution (e.g. gpt-6.1-sol). "
            "Code profile only. "
            "Review budget substitution requires this and --review-risk; the reviewer's model "
            "is never the author identity. Default: None (keep eligible requested reviewer)."
        ),
    )
    d.add_argument(
        "--review-risk",
        default=None,
        choices=("low", "medium", "high", "critical"),
        help=(
            "Risk passed to the canonical reviewer resolver with --review-author-model. "
            "Code profile only (--review-profile code, the default). Default: None (no review budget substitution). "
            "Mandatory for requested or substituted AGY code reviews, including seat defaults and aliases, "
            "even without author metadata; explicitly choose low, medium, high or critical. "
            "Example: critical for admission or launcher changes."
        ),
    )
    d.add_argument(
        "--authoring-review-risk",
        default=None,
        choices=("low", "medium", "high", "critical"),
        help=(
            "#9739: the planned review risk of the branch this write dispatch authors. Admission refuses "
            "a writer when no qualified reviewer outside every author family would remain at this risk; "
            "protected paths only raise it. Does not type the dispatch as a review. "
            "Default: None, checked as critical. Example: medium for a routine mixed-family branch."
        ),
    )
    d.add_argument(
        "--subject-seat",
        action="append",
        default=None,
        metavar="SEAT",
        help=(
            "Seat governed by the change (repeatable); excluded by the reviewer resolver, and by "
            "write-dispatch review admission (#9739). Requires a review or write-capable mode; "
            "unknown seats fail closed. Default: none. "
            "Example: --subject-seat codex for a shared adapter change."
        ),
    )
    d.add_argument(
        "--subject-family",
        action="append",
        default=None,
        metavar="FAMILY",
        help=(
            "Family governed by the reviewed change (repeatable); excluded by the reviewer resolver. "
            "Also used by write-dispatch review admission. Requires a review or write-capable mode; "
            "unknown families fail closed. Default: none. Example: --subject-family openai."
        ),
    )
    d.add_argument(
        "--review-attempt",
        default=None,
        metavar="MANIFEST",
        help=(
            "Path to manifest YAML file for formal review attempt recording (#8517). "
            "Code/infra review admission requires the record's frozen target.changed_paths list; "
            "Ukrainian content attempts do not require that target for the security floor. "
            "Used together with --review-id and --attempt-id to launch a per-attempt "
            "stdio sources MCP server with ledger receipts. Default: None. "
            "Example: --review-attempt batch_state/manifests/rev-1.yaml"
        ),
    )
    d.add_argument(
        "--review-access",
        choices=("full", "isolated"),
        default="full",
        help="Review access mode: full checkout (requires --full-checkout), or manifest isolation. Default: full.",
    )
    d.add_argument(
        "--review-id",
        default=None,
        metavar="REVIEW_ID",
        help=(
            "Formal review identifier for receipt recording (#8517). Required when "
            "--review-attempt is set; must match the review id in receipt paths. "
            "Default: None. Example: --review-id rev-20260922-001"
        ),
    )
    d.add_argument(
        "--attempt-id",
        default=None,
        metavar="ATTEMPT_ID",
        help=(
            "Unique attempt identifier for receipt recording (#8517). Required when "
            "--review-attempt is set; names the attempt ledger <attempt_id>.jsonl. "
            "Default: None. Example: --attempt-id att-01"
        ),
    )
    d.add_argument(
        "--full-checkout",
        action="store_true",
        help=(
            "Materialize the full git working tree in the dispatch worktree. "
            "Default cone sparse-checkout excludes curriculum/ (289MB), wiki/ (66MB), "
            "data/projects/ (633MB), data/lexicon/ (277MB), and registry/projects/ "
            "while retaining registry/lexicon/, leaving a default "
            "worktree under 450MB. Use this when the task needs the entire tree."
        ),
    )
    d.add_argument(
        "--sparse-include",
        action="append",
        default=None,
        metavar="DIR",
        help=(
            "Keep a tree that default sparse-checkout would exclude "
            "(curriculum, wiki, data/projects, data/lexicon, registry/projects). Repeatable. "
            "Example: --sparse-include data/projects, or --sparse-include registry/projects "
            "for module content. Owned paths under those trees are included automatically."
        ),
    )
    d.add_argument(
        "--base",
        default=None,
        help=(
            "Base branch to fetch and branch the worktree from "
            "(default: the repository's default branch, read from the canonical "
            "remote for a write dispatch; main otherwise). The worktree is branched "
            "from origin/{base}, not local {base}. Where a writer starts, never "
            "the base its authors are reviewed against (#9739)."
        ),
    )
    d.add_argument(
        "--allow-merge",
        action="store_true",
        help=(
            "Opt in to allow PR approval/merge and pushes to main inside the "
            "delegated subprocess. Default is off: AGENT_NO_MERGE=1 is set."
        ),
    )
    d.add_argument(
        "--language-lane",
        action="store_true",
        help=(
            "This dispatch authors, reviews, critiques, settles, or judges Ukrainian language, "
            "culture, or heritage content. Only claude, codex (GPT), and agy (Gemini) are admitted."
        ),
    )
    d.add_argument(
        "--check-budget",
        action="store_true",
        help=(
            "Query /api/state/routing-budget before spawning; hard-sub or refuse "
            "when the requested writer lane is near_cap/hot/deficit. Reviews always read "
            "fresh capacity, even without this flag; pace alone orders equal fits. Code review admits a sole "
            "eligible cross-family lane with a NOTE on pace-only deficit; hard capacity "
            "and health gates still bind. Review substitutes follow the resolver's eligible "
            "order; no-capacity refusals name every candidate and exclusion. Prepaid DeepSeek/OpenRouter "
            "also refuse unknown, stale or empty funding. Also enabled when "
            "LU_DISPATCH_CHECK_BUDGET=1 (launchers can force without flag churn)."
        ),
    )
    d.add_argument(
        "--force-agent",
        action="store_true",
        help=(
            "Dispatch the requested agent with no budget substitution. "
            "--check-budget / LU_DISPATCH_CHECK_BUDGET still prints and records that lane's "
            "quota and health, using explicit unknowns when telemetry is missing. "
            "Also overrides a live Cursor driver-lease refusal with a NOTE."
        ),
    )
    d.add_argument(
        "--dry-run",
        action="store_true",
        help="Run dispatch pre-flight checks and print task-id without spawning a worker.",
    )
    d.add_argument(
        "--hard-timeout",
        type=int,
        default=DEFAULT_HARD_TIMEOUT_S,
        help=(
            "Absolute wall-clock seconds for the worker before the runtime "
            f"hard-kills it (default: {DEFAULT_HARD_TIMEOUT_S}). "
            f"--silence-timeout defaults to {DEFAULT_SILENCE_TIMEOUT_S}s and catches "
            "stdout-silent hangs sooner."
        ),
    )
    d.add_argument(
        "--silence-timeout",
        type=int,
        metavar="SECS",
        default=DEFAULT_SILENCE_TIMEOUT_S,
        help=(
            "Seconds without subprocess watchdog activity before killing the agent "
            "CLI and marking the task status='timeout' "
            f"(default: {DEFAULT_SILENCE_TIMEOUT_S}s; 0 disables). "
            "Watchdog activity includes stdout/stderr, liveness-file updates, "
            "and process-tree CPU/disk activity. --hard-timeout still applies as the "
            "absolute wall-clock fallback."
        ),
    )
    d.add_argument(
        "--initial-response-timeout",
        type=int,
        metavar="SECS",
        default=DEFAULT_INITIAL_RESPONSE_TIMEOUT_S,
        help=(
            "Startup probe: kill the agent CLI if it produces no "
            "observable startup activity (stdout, stderr, liveness file, or "
            "process-tree CPU/disk work) within this many seconds "
            f"(default: {DEFAULT_INITIAL_RESPONSE_TIMEOUT_S}; 0 disables). "
            "Distinct from --silence-timeout, which watches composite "
            "activity after startup (#2071, #3875)."
        ),
    )
    d.add_argument(
        "--max-budget-usd",
        type=float,
        default=None,
        help=(
            "Optional Claude Code dollar cap for this dispatch. Only Claude "
            "translates this to a CLI flag; non-Claude adapters warn and "
            "ignore it. Omit to run uncapped."
        ),
    )
    d.add_argument(
        "--output-schema",
        default=None,
        metavar="FILE",
        help=(
            "Bind a JSON Schema to the final response of an effective Codex "
            "dispatch. The file is parsed before spawn, resolved to an "
            "absolute path, hashed into task state, and revalidated by the "
            "Codex adapter before it emits --output-schema. "
            "Cannot be combined with --review-attempt; default: omitted."
        ),
    )
    d.add_argument(
        "--research-role",
        default=None,
        metavar="ROLE",
        help=(
            "ADR-011 P3 research context: the task's single role (e.g. quality). "
            "Explicit only — never inferred from the prompt, agent, provider, or "
            "branch. Combined with the other --research-* flags, injects bounded, "
            "pointer-only research pointers (bodies fetched on demand). "
            "`implementation` types a coding dispatch; --agent cursor --model auto requires it (#9274)."
        ),
    )
    d.add_argument(
        "--research-task-family",
        default=None,
        metavar="FAMILY",
        help=("ADR-011 P3 research context: the task's single task family (e.g. difficulty-gate). "
              "Mechanical-only models require routine_mechanical, mechanical_classification or readonly_recon; "
              "declare narrow safe owned paths. Classification and recon use read-only mode."),
    )
    d.add_argument(
        "--research-track",
        default=None,
        metavar="TRACK",
        help="ADR-011 P3 research context: the task's single track (e.g. core).",
    )
    d.add_argument(
        "--research-owned-path",
        action="append",
        default=None,
        metavar="GLOB",
        help=(
            "ADR-011 P3 research context: an owned/changed path for the task. "
            "Repeatable. Matched against each record's owned_paths globs. "
            "Also feeds the writable-path admission guard (#5643)."
        ),
    )
    d.add_argument(
        "--rules-seat",
        choices=rules_core.SEATS,
        default=None,
        help=(
            "Rules core the worker starts with: core, or content (core plus the curriculum "
            f"addendum) for curriculum seats. Default: ${rules_core.SEAT_ENV}, else core."
        ),
    )
    d.add_argument(
        "--owned-path",
        action="append",
        default=None,
        metavar="PATH",
        help=(
            "#8991: a repo-relative path (dir/, dir/**, file, or glob) this task may "
            "commit. Repeatable; recorded as the task's owned_paths. Auto-finalize of a "
            "dirty danger-mode worktree commits only changes under these paths; without "
            "any it commits nothing and the task ends needs_finalize. Required for a "
            "write-capable --mode: review admission checks the branch's scope from it (#9739). "
            "Independent of --research-owned-path."
        ),
    )
    d.add_argument(
        "--advisory-task",
        default=None,
        metavar="TASK_ID",
        help=(
            "#9275: the finished advisor task whose envelope admits this bounded-worker dispatch. "
            "Required whenever the admitted route launches the bounded worker (gpt-6-luna) or the "
            "Gemini Flash bounded fallback without a Ukrainian authoring/review classification; "
            "refused on any other dispatch. Its owned_paths must equal --owned-path. Default: None."
        ),
    )
    d.add_argument(
        "--advisory-role",
        default=None,
        choices=("bounded_advisory_envelope",),
        help=(
            "#9275: run this read-only dispatch as the catalog advisor that issues a bounded-worker "
            "envelope; the admitted model must be the advisor model. Requires --advisory-binding. Default: None."
        ),
    )
    d.add_argument(
        "--advisory-binding",
        default=None,
        metavar="SHA256",
        help=(
            "#9275: with --advisory-role, the worker dispatch's binding digest, printed by the worker "
            "dispatch command with --print-advisory-binding. Default: None."
        ),
    )
    d.add_argument(
        "--print-advisory-binding",
        action="store_true",
        help=(
            "#9275: print this dispatch's advisory binding digest (every parsed argument except "
            "--advisory-task and this flag) and exit without any other effect."
        ),
    )
    d.add_argument(
        "--allow-path-overlap",
        default=None,
        metavar="REASON",
        help=(
            "Explicitly admit a write-capable dispatch that intersects another "
            "active claim. Records task, conflicts, reason, and caller in the "
            "ownership ledger. Required text reason; empty string is ignored."
        ),
    )
    d.add_argument(
        "--preflight-triage",
        action="store_true",
        help=(
            "#8183: before spawning, run cheap TypeSafe/Jev readiness triage on the candidate "
            "diff (+ local test log). A confident broken_or_failing verdict exits 3 without "
            "starting a worker. Missing key or API failure skips (dispatch proceeds)."
        ),
    )
    d.add_argument(
        "--preflight-base",
        default=None,
        metavar="REF",
        help="Base ref for the --preflight-triage diff (default: origin/main).",
    )
    d.add_argument(
        "--preflight-test-log",
        default=None,
        metavar="PATH",
        help="Local test log for --preflight-triage (default: <cwd>/.preflight-test.log if present).",
    )
    d.set_defaults(func=cmd_dispatch)

    # status
    s = sub.add_parser(
        "status",
        help="Check task status from local state (fast, no block)",
        description=(
            "Check task status from local batch_state. For guardrails that "
            "must fail when a task is no longer running, use status-or-fail."
        ),
    )
    s.add_argument("task_id", help="Task ID to inspect, e.g. review-123.")
    s.add_argument(
        "--run-nonce",
        default=None,
        help="Expected run nonce to detect stale records from prior rounds (#7168).",
    )
    s.set_defaults(func=cmd_status)

    # status-or-fail
    sof = sub.add_parser(
        "status-or-fail",
        help="Exit 0 only if Monitor API says task is running",
        description=(
            "Verify a delegated task through the Monitor API and exit 0 only when it is running.\n"
            "Use it in guardrails before trusting stale async-task claims; do not use it when the API may be offline."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/delegate.py status-or-fail review-123\n"
            "  .venv/bin/python scripts/delegate.py status-or-fail review-123 --verbose\n\n"
            "Exit codes:\n"
            "  0 Monitor API confirms the task is running.\n"
            "  1 Task is not running, done, missing, or stale.\n"
            "  2 Monitor API is unreachable.\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sof.add_argument("task_id", help="Task ID to verify, e.g. review-123.")
    sof.add_argument(
        "--run-nonce",
        default=None,
        help="Expected run nonce to verify against the running task (#7168).",
    )
    sof.add_argument(
        "--verbose",
        action="store_true",
        help="Print structured status JSON before exiting.",
    )
    sof.set_defaults(func=cmd_status_or_fail)

    # wait
    w = sub.add_parser("wait", help="Block until task reaches terminal state")
    w.add_argument("task_id", help="Task ID to wait for, e.g. review-123.")
    w.add_argument("--timeout", type=float, default=0, help="Max wait seconds (0 = forever)")
    w.add_argument("--poll-interval", type=float, default=2.0, help="Poll interval seconds (default: 2.0)")
    w.add_argument(
        "--run-nonce",
        default=None,
        help="Expected run nonce to verify before accepting terminal status (#7168).",
    )
    w.set_defaults(func=cmd_wait)

    # cancel
    c = sub.add_parser("cancel", help="SIGTERM the worker")
    c.add_argument("task_id", help="Task ID to cancel, e.g. review-123.")
    c.add_argument(
        "--run-nonce",
        default=None,
        help="Expected run nonce to verify before cancelling worker (#7168).",
    )
    c.set_defaults(func=cmd_cancel)

    # list
    l = sub.add_parser("list", help="List tasks (with optional status filter)")
    l.add_argument(
        "--all",
        action="store_true",
        help="Also list records archived into batch_state/tasks/archive/ (#8625); default is the hot directory only.",
    )
    l.add_argument(
        "--status",
        default=None,
        choices=[
            "spawning",
            "running",
            "done",
            "failed",
            "timeout",
            "rate_limited",
            "crashed",
            "cancelled",
            "needs_finalize",
            _NO_DELIVERABLE_STATUS,
            "dry_run",
        ],
        help="Optional status filter, e.g. running or failed.",
    )
    l.set_defaults(func=cmd_list)

    # backfill-repository
    bf = sub.add_parser(
        "backfill-repository",
        help="Stamp authoritative repository identity on legacy task states (#7083); dry-run unless --apply",
    )
    bf.add_argument(
        "--apply",
        action="store_true",
        help="Write the stamps (default is a dry-run report).",
    )
    bf.set_defaults(func=cmd_backfill_repository)

    # _worker (hidden — internal)
    wk = sub.add_parser("_worker", help=argparse.SUPPRESS)
    wk.add_argument("--task-id", required=True)
    wk.add_argument("--agent", required=True)
    wk.add_argument("--harness", choices=sorted(_KIMI_HARNESSES), default=None)
    wk.add_argument("--mode", required=True)
    wk.add_argument("--cwd", required=True)
    wk.add_argument("--model", default=None)
    wk.add_argument("--provider", default=None)
    wk.add_argument(
        "--effort",
        default=None,
        choices=["low", "medium", "high", "xhigh", "max"],
    )
    wk.add_argument("--hard-timeout", type=int, default=DEFAULT_HARD_TIMEOUT_S)
    wk.add_argument("--silence-timeout", type=int, default=DEFAULT_SILENCE_TIMEOUT_S)
    wk.add_argument(
        "--initial-response-timeout",
        type=int,
        default=DEFAULT_INITIAL_RESPONSE_TIMEOUT_S,
    )
    wk.add_argument("--keep-worktree", action="store_true")
    wk.add_argument("--finalize-open-pr", action="store_true")
    wk.add_argument("--require-review-verdict", action="store_true")
    wk.add_argument("--max-budget-usd", type=float, default=None)
    wk.add_argument("--output-schema", default=None)
    wk.add_argument("--output-schema-sha256", default=None)
    wk.add_argument("--runtime-tmp-root", default=None)
    wk.add_argument("--runtime-tmp-namespace-root", default=None)
    wk.add_argument("--run-nonce", default=None)
    wk.add_argument("--review-access", choices=("full", "isolated"), default="isolated")
    wk.add_argument("--review-id", default=None)
    wk.add_argument("--attempt-id", default=None)
    wk.add_argument("--mcp-config-path", default=None)
    wk.add_argument("--strict-mcp-config", action="store_true")
    wk.add_argument("--review-manifest", default=None, help="Formal attempt manifest path (default: none)")
    wk.add_argument(
        "--review-input-root", default=None, help="Manifest render checkout for input projection (default: none)"
    )
    wk.set_defaults(func=cmd_worker)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
