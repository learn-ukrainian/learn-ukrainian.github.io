"""Command interface for the minimal dispatcher."""

import argparse
import contextlib
import json
import re
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import get_args

from scripts.common.git_context import validate_plain_branch_name
from scripts.dispatcher import (
    admission,
    checks,
    git,
    headroom,
    host_admission,
    providers,
    runtime_context,
    store,
    worker,
)
from scripts.dispatcher.environment import child_env
from scripts.dispatcher.types import ReviewAccess, TaskSpec
from scripts.dispatcher.watchdog import DEFAULT_INITIAL_RESPONSE_TIMEOUT_S, DEFAULT_SILENCE_TIMEOUT_S, deadlines

# Grok runs through Cursor's TUI: --agent cursor --model grok-4.7-high (grok-build is the separate Grok TUI).
ALIASES = dict(sol="codex", gemini="agy", deepseek="opencode", openrouter="hermes")


class _PromptPath(type(Path())):
    """Let builders read submitted bytes while dry-run leaves the filesystem untouched."""

    def read_bytes(self):
        return self.content

    def read_text(self, encoding=None, errors=None):
        return self.content.decode(encoding or "utf-8", errors or "strict")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run provider CLIs in detached dispatch worktrees.\nUse for new tasks; legacy tasks retain their supervisor.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python -m scripts.dispatcher.cli dispatch --agent sol --model gpt-6.1-sol --prompt 'Explain X'\n"
        "  .venv/bin/python scripts/dispatch.py wait TASK --run-nonce NONCE --timeout 60\n"
        "Outputs: task JSON, prompt, result and logs; new branch/worktree on dispatch.\n"
        "Exit codes: 0 success, 1 terminal failure, 2 invalid/refused request,\n"
        "  3 host admission refused (retryable), 4 worktree disk full, 124 client timeout.\n"
        "Related: docs/design/dispatch-v2.md (C-2188).",
    )
    subs = parser.add_subparsers(dest="command", required=True)
    dispatch = subs.add_parser(
        "dispatch",
        help="Start a detached task; print task ID and nonce",
        description="Start a detached provider task.\nUse --dry-run to inspect its command without creating task files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
        "  .venv/bin/python scripts/dispatch.py dispatch --agent muse --model muse-wonder-full-1.0 "
        "--prompt 'Explain X' --contributor-mode on --dry-run\n"
        "  .venv/bin/python scripts/dispatch.py dispatch --agent cursor --model grok-4.7-high --prompt 'Explain X'\n"
        "Outputs: task ID and nonce; task JSON, prompt, result, logs and dispatch worktree.\n"
        "  Muse task JSON records the effective contributor_mode. --dry-run prints a plan and creates nothing.\n"
        "Exit codes: 0 task started or plan printed, 1 hold publication failed, 2 invalid/refused request,\n"
        "  3 host admission refused (retryable), 4 worktree disk full.\n"
        "Related: docs/design/dispatch-v2.md.",
    )
    for flag, default, help_text in (
        ("agent", None, "Provider or alias, e.g. sol; Grok is cursor with --model grok-4.7-high (required)"),
        ("model", None, "Exact provider model, e.g. gpt-6.1-sol (required)"),
        ("task-id", None, "Unique safe task ID (default: random UUID)"),
        ("prompt-file", None, "UTF-8 prompt path; '-' reads stdin (one source required)"),
        ("prompt", None, "Literal prompt; '-' reads stdin (one source required)"),
        ("effort", None, "Provider effort, e.g. high (default: provider default)"),
        ("repo", None, "fleet_repos.yaml key (default: public primary)"),
        ("base", "origin/main", "Starting Git ref (default: origin/main)"),
        ("branch", None, "Review source or publish branch; unpinned writes require a remote tip, e.g. codex/fix (default: base)"),
        ("pinned-head", None, "Exact review commit (default: branch or base)"),
        ("cwd", None, "Existing dispatch worktree root (default: create one)"),
        ("review-author-model", None, "Author model for family check (default: no review check)"),
        ("claude-account", None, "Claude account: subscription a or b, or API key kk or szb (default: inherited configuration)"),
        ("provider", None, "Explicit upstream, e.g. openrouter (default: native)"),
        ("output-schema", None, "Codex-only JSON object schema: repo-relative or absolute readable file (default: none)"),
        ("research-role", None, "Research role metadata (default: none)"),
        ("research-task-family", None, "Research task family metadata (default: none)"),
        ("research-track", None, "Research track metadata (default: none)"),
        ("initiator", None, "Caller label (default: none)"),
        ("language-lane", None, "Language context label (default: none)"),
        ("review-profile", None, "Review context label (default: none)"),
        ("risk", None, "Review risk label (default: none)"),
        ("review-mode", None, "Review mode label (default: none)"),
        ("advisory-task", None, "Finished advisor task admitting this bounded worker, e.g. advice-42 (default: none)"),
        ("advisory-role", None, "Catalog advisory_roles decision this read-only task records, e.g. "
         "review_budget_elevation; needs --advisory-binding (default: none)"),
        ("advisory-binding", None, "SHA-256 the advisory decision binds, e.g. a budget grant ruling digest "
         "(default: none)"),
        ("verify-command", None, "Acceptance command for a bounded driver brief, e.g. 'ruff check scripts' (default: none)"),
    ):
        dispatch.add_argument(f"--{flag}", default=default, required=flag in {"agent", "model"}, help=help_text)
    dispatch.add_argument(
        "--contributor-mode",
        choices=("on", "off"),
        help="Muse contributor mode, on or off; Muse only (default: omitted, provider default off)",
    )
    dispatch.add_argument(
        "--mode",
        choices=("read-only", "workspace-write"),
        default="read-only",
        help="Mode (default: read-only)",
    )
    dispatch.add_argument("--worktree", nargs="?", const="", help="Dispatch path (default: automatic)")
    dispatch.add_argument("--pr", type=int, help="Reviewed PR number, e.g. 42 (default: none; use --branch for identity)")
    for flag in ("subject-seat", "subject-family"):
        dispatch.add_argument(f"--{flag}", action="append", default=[],
                              help="Excluded review subject, e.g. grok or xai (repeatable; default: none)")
    dispatch.add_argument("--require-review-verdict", action="store_true", default=None,
                          help="Mark a review as requiring a verdict; read-only, metadata only (default: off)")
    for flag in ("review-id", "attempt-id", "review-attempt"):
        dispatch.add_argument(f"--{flag}", help="Bound review: id or manifest file for --review-attempt; "
                              "all three required; dry-run only until runtime isolation is wired (default: none)")
    dispatch.add_argument("--review-access", choices=get_args(ReviewAccess),
                          help="Bound review access; dry-run only (default: isolated for bound attempts)")
    dispatch.add_argument(
        "--force-admission", metavar="REASON",
        help="Override host admission with a recorded non-empty reason; never overrides a full worktree disk (default: off)",
    )
    dispatch.add_argument("--dry-run", action="store_true", help="Print plan; create nothing (default: off)")
    dispatch.add_argument("--print-advisory-binding", action="store_true",
                          help="Print this request's envelope binding; needs --task-id, creates nothing (default: off)")
    dispatch.add_argument(
        "--full-checkout", action="store_true",
        help="Materialize the full Git working tree instead of excluding heavy trees (default: off)",
    )
    dispatch.add_argument(
        "--sparse-include", action="append", default=[], metavar="DIR",
        help="Keep a default-excluded tree; repeatable (default: inferred from owned paths). Example: --sparse-include curriculum. "
        "Excluded: " + ", ".join(sorted(git.SPARSE_EXCLUDE_DEFAULT)),
    )
    dispatch.add_argument(
        "--hard-timeout", type=float, default=7200, help="Deadline seconds; 0 disables (default: 7200)"
    )
    dispatch.add_argument(
        "--silence-timeout", type=int, default=DEFAULT_SILENCE_TIMEOUT_S, metavar="SECS",
        help="Kill with status timeout after no stdout/stderr, liveness-file or process-tree work "
             "for SECS; 0 disables, --hard-timeout still applies (default: 3600)",
    )
    dispatch.add_argument(
        "--initial-response-timeout", type=int, default=DEFAULT_INITIAL_RESPONSE_TIMEOUT_S, metavar="SECS",
        help="Kill with status timeout after no first stdout/stderr, liveness-file or process-tree work "
             "within SECS; 0 disables (default: 600)",
    )
    for flag in ("owned-path", "research-owned-path"):
        dispatch.add_argument(f"--{flag}", action="append", default=[], help="Path label (repeatable; default: empty)")
    for name in ("wait", "status", "cancel", "list"):
        sub = subs.add_parser(name, help=f"{name.capitalize()} task records")
        if name == "list":
            sub.add_argument("--status", help="Filter exact state, e.g. running (default: all states)")
            sub.add_argument("--all", action="store_true", help="Include archived records (default: hot only)")
        else:
            sub.add_argument("task_id", help="Task ID returned by dispatch")
            sub.add_argument("--run-nonce", help="Expected run identity (default: omit check)")
        if name == "wait":
            sub.add_argument("--timeout", type=float, default=0, help="Wait seconds; 0 is unlimited (default: 0)")
            sub.add_argument("--poll-interval", type=float, default=1, help="Read interval in seconds (default: 1)")
    sof = subs.add_parser(
        "status-or-fail",
        help="Exit 0 only for a confirmed running task",
        description="Verify task state and supervisor process identity.\n"
        "Use for liveness guardrails; use status to inspect terminal records.",
        epilog="Examples:\n  .venv/bin/python scripts/dispatch.py status-or-fail TASK\n"
        "  .venv/bin/python scripts/dispatch.py status-or-fail TASK --run-nonce NONCE --verbose\n"
        "Outputs: quiet by default; --verbose prints legacy-shaped status JSON. No records changed.\n"
        "Exit codes: 0 confirmed running; 1 not running, missing, stale or nonce mismatch; "
        "2 unavailable or invalid state.\n"
        "Related: status; docs/design/dispatch-v2.md (C-2188).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sof.add_argument("task_id", help="Task ID to verify, e.g. review-123")
    sof.add_argument("--run-nonce", help="Expected run identity (default: omit nonce check)")
    sof.add_argument("--verbose", action="store_true", help="Print structured status JSON (default: quiet)")
    return parser


def _dispatch(args) -> int:
    if binding := store.review_binding(vars(args)):
        store.check_review_attempt(binding)
        # STAGE 1: dry-run-only binding; bound launches exit 2 until the port adds
        # the manifest-only runtime boundary, scoped home, Sources receipts,
        # review_contract/review_input_paths and the no-reuse marker.
        if not args.dry_run:
            raise ValueError("review_attempt_runtime_unavailable: v2 review isolation is not wired")
    if args.require_review_verdict and args.mode != "read-only":
        raise ValueError("--require-review-verdict requires --mode read-only")
    excluded = git.sparse_excludes(args.sparse_include, [*args.owned_path, *args.research_owned_path])
    if (args.prompt is None) == (args.prompt_file is None):
        raise ValueError("provide exactly one of --prompt or --prompt-file")
    source = args.prompt if args.prompt is not None else args.prompt_file
    prompt = (
        sys.stdin.buffer.read()
        if source == "-"
        else (args.prompt.encode() if args.prompt is not None else Path(source).read_bytes())
    )
    prompt.decode("utf-8")
    # Every worker and review seat needs the rules core: without it nothing is dispatched, and this
    # runs before any check, worktree or task record.
    from scripts.lib import rules_core

    try:
        rules_core.require_core()
    except rules_core.RulesCoreMissing as exc:
        raise ValueError(f"dispatch refused: {exc}; the rules core is required.") from None
    agent = ALIASES.get(args.agent, args.agent)
    # An unknown Claude account label reaches admission, which refuses it typed (claude_account_unknown).
    if agent not in providers.PROVIDERS:
        aliases = ", ".join(f"{name}={target}" for name, target in ALIASES.items())
        raise ValueError(f"unknown agent {args.agent!r}; supported agents: {', '.join(providers.PROVIDERS)} "
                         f"(aliases: {aliases}); dispatch Grok as --agent cursor --model grok-4.7-high")
    if args.contributor_mode is not None and agent != "muse":
        raise ValueError("--contributor-mode is only supported with --agent muse")
    if args.output_schema is not None and agent != "codex":
        raise ValueError("--output-schema is supported only with the effective codex agent")
    if args.mode == "read-only" and (refusal := providers.read_only_refusal(agent)):
        raise ValueError(refusal)
    deadlines(vars(args))
    if args.cwd and (args.branch or args.pinned_head or args.worktree is not None):
        raise ValueError("invalid process deadline or conflicting existing-worktree options")
    account_fields = admission.claude_account(agent, args.claude_account)
    args.claude_account = account_fields.get("claude_account", args.claude_account)
    if args.print_advisory_binding:
        if not args.task_id or source == "-":
            raise ValueError("--print-advisory-binding requires --task-id and a non-stdin prompt")
        print(checks.advisory_binding(args, prompt)[2])
        return 0
    task_id = args.task_id or uuid.uuid4().hex
    path = store.record_path(task_id)
    if store.read(task_id, missing_ok=True) is not None:
        raise ValueError("task id already exists; choose a new task id")
    repo, info = git.resolve_repo(args.repo)
    if not args.dry_run:
        # Crash recovery: finish settling this dispatcher's earlier tasks before creating a worktree.
        worker.settle_left_worktrees()
    host_admission.precheck(args.mode, force_reason=args.force_admission)
    try:
        headroom.check_plan(agent, args.model, account_fields,
                            review=admission.review_typed(vars(args)) or bool(args.risk))
    except headroom.model_pause.ModelPausedRefused as exc:
        raise host_admission.Refused(f"❌ {exc}", 2) from None
    host_admission.check_credit(agent, args.model)
    advisory_fields = checks.check_bounded_advisory(args, args.model, repo, prompt)
    advisory_fields.update(checks.check_advisory_role(args, agent, args.model))
    force_reason = args.force_admission
    if force_reason is not None:
        force_reason = str(force_reason).strip()
        if not force_reason:
            raise host_admission.Refused("❌ --force-admission requires a non-empty reason", 2)
    if args.branch is not None:
        args.branch = validate_plain_branch_name(args.branch, repo_root=repo)
    start = args.pinned_head or args.branch or args.base
    publish_remote = None
    if args.mode == "workspace-write" and args.branch and not args.pinned_head and not args.dry_run:
        start, publish_remote = git.publish_start(repo, info, args.branch, task_id)
    # A published start is created and recorded verbatim, never re-resolved in the shared repository.
    exact_start = {"exact": True} if publish_remote is not None else {}
    worktree, branch, sha = git.worktree_plan(
        repo, agent, task_id, start, args.cwd, args.worktree, **exact_start
    )
    if args.pinned_head and not re.fullmatch(r"[0-9a-fA-F]{40}", args.pinned_head):
        raise ValueError("pinned head must be a full commit SHA")
    prompt_path = _PromptPath(path.with_suffix(".prompt"))
    prompt_path.content = prompt
    options = {key: str(value) for key, value in vars(args).items() if value is not None and key != "prompt"}
    if args.output_schema is not None:
        from scripts.dispatcher.output_schema import bind

        options.update(bind(args.output_schema, repo))
    fields = {name: getattr(args, name) for name in ("model", "effort", "mode", "claude_account", "provider")}
    spec = TaskSpec(
        task_id,
        agent,
        worktree=worktree,
        prompt_file=prompt_path,
        final_file=path.with_suffix(".result"),
        options=options,
        **fields,
    )
    checks.check_private_input(spec, info["key"])
    if args.mode == "read-only" and (refusal := providers.read_only_refusal(agent, child_env(spec))):
        raise ValueError(refusal)
    checks.check_review_family(args.review_author_model, args.model)
    # Every read-only review of a change, dry runs included, whichever review flag types it (F10). A change is
    # named by --branch (stored as review_branch, the only identity the verdict recorder publishes for), a PR, or a
    # bound review attempt. A typed dispatch with none of them (the uk-preamble eval's --language-lane run at a
    # pinned head) reviews no branch: the recorder refuses it ("review was not branch-pinned"), so there is no
    # authorship range to check.
    if args.mode == "read-only" and (args.branch or args.pr or binding) and (
        admission.review_typed(vars(args))
        or any((args.risk, args.review_mode, args.language_lane, args.subject_seat, args.subject_family, args.branch))
    ):
        checks.check_branch_author_families(args, repo, info, sha, args.model)
    if args.subject_seat or args.subject_family or (args.mode == "read-only" and args.owned_path):
        exclusion = checks.check_review_subjects(agent, args.model, args.subject_seat, args.subject_family,
                                                args.owned_path, review=any((args.review_profile, args.language_lane,
                                                args.review_author_model, args.risk, args.review_mode, args.pr,
                                                args.require_review_verdict, args.subject_seat, args.subject_family)))
        args.subject_seat, args.subject_family = sorted(exclusion.seats), sorted(exclusion.families)
        if (exclusion.seats or exclusion.families) and (
            (args.review_profile or "").strip().casefold() == "ukrainian" or args.language_lane
        ):
            raise ValueError("protected subject scope needs a code-profile review without --language-lane")
    decision = host_admission.check(
        args.mode, dry_run=args.dry_run, disk_guard=not (args.worktree is not None and (worktree / ".git").exists()),
        force_reason=force_reason,
    )
    if args.dry_run:
        # The real run re-checks child_env after worktree creation in worker.py.
        invocation = runtime_context.build(spec, child_env(spec))
        plan = dict(worktree=str(worktree), argv=invocation.argv, record_path=str(path))
        if binding:
            plan.update(review_attempt=binding, review_access=args.review_access or "isolated")
        print(json.dumps(plan, indent=2))
        return 0
    with host_admission.reserve(
        task_id, args.mode, decision, agent=agent, force_reason=force_reason,
        disk_guard=lambda: not (args.worktree is not None and (worktree / ".git").exists()),
    ) as hold:
        if binding:
            store.check_review_attempt(binding, claim=True)
        if not args.cwd:
            git.create_worktree(repo, worktree, branch, sha, full_checkout=args.full_checkout,
                                sparse_include=git.SPARSE_EXCLUDE_DEFAULT - set(excluded), **exact_start)
        record = store.new_record(spec, info, branch, sha, vars(args), binding=binding, admission_hold=hold)
        if publish_remote is not None:
            record["worktree_remote_url"] = publish_remote
        if args.mode != "read-only" and args.owned_path and record["worktree_remote_url"] is None:
            raise ValueError("write task with owned paths refused: origin must match the registered canonical repository URL")
        record.update(advisory_fields, **account_fields)
        if agent == "muse":
            record["contributor_mode"] = spec.options.get("contributor_mode", "off")
        try:
            # Attach to a borrowed worktree under the lock its settlement removes it under, so an
            # active record names it before any removal can start.
            with git.worktree_lock(repo) if args.cwd else contextlib.nullcontext():
                if args.cwd and not worktree.is_dir():
                    raise ValueError("cwd worktree was removed before the task started")
                worker.start(spec, record, prompt, args.hard_timeout)
        except admission.LaunchRefused as exc:
            # The record is terminal: preserve the account/placement port's no-relaunch refusal.
            print(f"dispatcher: failed to spawn worker for {task_id!r}: {exc}", file=sys.stderr)
            return 1
    print(task_id, record["run_nonce"], sep="\n")
    return 0


def _status_or_fail_payload(task_id: str, *, run_nonce: str | None = None) -> dict:
    try:
        record = store.read(task_id, run_nonce or None)
    except ValueError as exc:
        if str(exc) == "task not found":
            return dict(task_id=task_id, status="task not found", age_s=0)
        if str(exc) != "run nonce mismatch":
            raise
        # The legacy Monitor's 409 response exposes no conflicting run identity.
        record = dict(task_id=task_id, status="stale_run_nonce")
    if not isinstance(record, dict):
        raise ValueError("invalid task record")
    status = str(record.get("status") or "unknown")
    identity = worker._identity(record.get("pid"))
    alive = identity is not None and identity == record.get("process_start")
    if status == "running" and not alive:
        status = "stale"
    try:
        started = datetime.fromisoformat(str(record.get("started_at")).replace("Z", "+00:00"))
        if started.tzinfo is None:
            started = started.replace(tzinfo=UTC)
        age = max(0, round((datetime.now(UTC) - started.astimezone(UTC)).total_seconds()))
    except (TypeError, ValueError):
        age = 0
    result = dict(task_id=record.get("task_id") or task_id, status=status, age_s=age, alive=alive)
    if run_nonce is not None:
        result["run_nonce"] = record.get("run_nonce")
    return result


def _status_or_fail(args: argparse.Namespace) -> int:
    try:
        status = _status_or_fail_payload(args.task_id, run_nonce=args.run_nonce)
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        print(f"Dispatcher state unavailable: {type(exc).__name__}", file=sys.stderr)
        return 2
    if args.verbose:
        print(json.dumps(status, indent=2))
    if status["status"] == "running":
        return 0
    print(
        f"task {args.task_id} is not running (status={status['status']}, age={status['age_s']}s)",
        file=sys.stderr,
    )
    return 1


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "status-or-fail":
            return _status_or_fail(args)
        if args.command == "dispatch":
            return _dispatch(args)
        code = 0
        if args.command == "list":
            result = [worker._observe(record) for record in store.list_tasks(include_archive=args.all)]
            if args.status is not None:
                result = [record for record in result if record.get("status") == args.status]
        elif args.command == "wait":
            if args.timeout < 0 or args.poll_interval <= 0:
                raise ValueError("timeout must be nonnegative and poll interval positive")
            result, code = worker.wait(args.task_id, args.run_nonce, args.timeout, args.poll_interval)
        elif args.command == "cancel":
            result = worker.cancel(args.task_id, args.run_nonce)
        else:
            result = worker._observe(store.read(args.task_id, args.run_nonce))
        print(json.dumps(result, indent=2))
        return code
    except host_admission.Refused as exc:
        print(str(exc), file=sys.stderr)
        return exc.code
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        message = str(exc).splitlines()[0] if isinstance(exc, ValueError) else type(exc).__name__
        print(f"dispatcher: {message}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    from scripts.dispatcher.primary import exec_primary

    exec_primary(sys.argv[1:])
    raise SystemExit(main())
