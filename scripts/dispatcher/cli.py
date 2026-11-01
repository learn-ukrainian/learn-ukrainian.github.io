"""Command interface for the minimal dispatcher."""

import argparse
import contextlib
import json
import os
import re
import subprocess
import sys
import time
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
    ownership,
    pool_selector,
    providers,
    review_attempt,
    runtime_context,
    scope,
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
        "  .venv/bin/python scripts/dispatch.py grant-paths TASK --run-nonce NONCE --owned-path tests/fix.py "
        "--reason 'Approved fixture change' --approval-ref message-id\n"
        "  .venv/bin/python scripts/dispatch.py retain-worktree TASK --set\n"
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
        ("codex-account", None, "Codex account: sub or api (default: sub; api requires a private codex_accounts.json binding)"),
        ("claude-account", None, "Claude account: subscription a or b, or API key kk or szb (default: inherited configuration)"),
        ("max-budget-usd", None, "Spend cap in USD for a Claude API-key account, at most its configured amount "
         "(default: that amount)"),
        ("provider", None, "Explicit upstream, e.g. openrouter (default: native)"),
        ("output-schema", None, "Codex, AGY, or Claude JSON object schema: repo-relative or absolute readable file "
         "(default: the review findings schema for a code or infra --require-review-verdict on those agents, otherwise none)"),
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
        ("trial-role", None, "Shadow trial role, e.g. review; read-only, with --trial-qualified-task and --pinned-head (default: none)"),
        ("trial-qualified-task", None, "Successful qualified non-trial task on the same input, head and role, e.g. qualified-42 (default: none)"),
    ):
        dispatch.add_argument(f"--{flag}", default=default, required=flag in {"agent", "model"}, help=help_text)
    dispatch.add_argument(
        "--contributor-mode",
        choices=("on", "off"),
        help="Muse contributor mode, on or off; Muse only (default: omitted, provider default off)",
    )
    dispatch.add_argument(
        "--advisor",
        choices=("opus",),
        help="Ask for the Opus 5.5 advisor on a workspace-write Claude Haiku 5.5 run; a Sonnet 5.5 "
        "workspace-write run always has it, any other run never does (default: omitted)",
    )
    dispatch.add_argument(
        "--mode",
        choices=("read-only", "workspace-write"),
        default="read-only",
        help="Mode (default: read-only). Review mode permits shell, the project interpreter, named tests "
             "and probes, Sources MCP and internet access; publishing and shared-state mutations stay denied.",
    )
    dispatch.add_argument(
        "--input", action="append", default=[], metavar="PATH",
        help="Regular file, e.g. notes.txt, mounted read-only at /agy-inputs/<n>; "
             "requires --agent agy and --mode read-only "
             "(repeatable, at most 8, each at most 8 MiB; default: none). "
             "Refuses excess inputs, oversized files, symlinks, hard links, unreadable or "
             "non-regular files, paths under credential directories or inside the primary "
             "checkout, paths changed before read, invalid input records, and missing "
             "digests or digests changed before start.",
    )
    dispatch.add_argument("--worktree", nargs="?", const="", help="Dispatch path (default: automatic)")
    dispatch.add_argument("--pr", type=int, help="Reviewed PR number, e.g. 42 (default: none; use --branch for identity)")
    for flag in ("subject-seat", "subject-family"):
        dispatch.add_argument(f"--{flag}", action="append", default=[],
                              help="Excluded review subject, e.g. grok or xai (repeatable; default: none)")
    dispatch.add_argument("--require-review-verdict", action="store_true", default=None,
                          help="Require an unambiguous review verdict; Codex, AGY, and Claude bind the existing "
                          "structured findings schema (read-only; default: off)")
    for flag in ("review-id", "attempt-id", "review-attempt"):
        dispatch.add_argument(f"--{flag}", help="Bound review: id or manifest file for --review-attempt; all three "
                              "required, with a rendered --prompt-file; use --pinned-head, not --branch or --pr; "
                              "runs inside the attempt boundary (default: none)")
    dispatch.add_argument("--review-access", choices=get_args(ReviewAccess),
                          help="Bound review access; full needs --full-checkout (default: isolated for bound attempts)")
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
    grant = subs.add_parser(
        "grant-paths", help="Grant exact additional owned paths to a running task",
        description="Append an attributable owned-path grant to a running write task.\n"
        "Coordinator use only; refuses self/descendants, sealed envelopes and settling tasks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python scripts/dispatch.py grant-paths TASK --run-nonce NONCE "
        "--owned-path tests/fix.py --reason 'Approved fixture change' --approval-ref message-id\n"
        "Outputs: JSON receipt with task, nonce, grant id, paths and effective scope.\n"
        "Side effects: appends a grant to the canonical task record; never changes sparse checkout.\n"
        "Exit codes: 0 durable grant or identical retry, 1 operational failure, 2 invalid/refused request.\n"
        "Related: agents_extensions/shared/skills/full-send/SKILL.md (owned-path exchange).",
    )
    grant.add_argument("task_id", help="Exact dispatch task ID, e.g. worker-42")
    grant.add_argument("--run-nonce", required=True, help="Exact run nonce returned by dispatch")
    grant.add_argument("--owned-path", action="append", required=True,
                       help="Literal repository-relative path, e.g. tests/fix.py (repeatable; no wildcards)")
    grant.add_argument("--reason", required=True, help="Nonempty reason for the approved scope addition")
    grant.add_argument("--approval-ref", required=True,
                       help="Fleet Comms message ID or comment URL; stored as given, never fetched")
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
    trees = subs.add_parser(
        "worktrees",
        help="List linked worktrees with their owning task",
        description="List every linked worktree of a repository with its owning task record.\n"
        "Read-only: changes no record and removes nothing.",
        epilog="Examples:\n  .venv/bin/python scripts/dispatch.py worktrees\n"
        "  .venv/bin/python scripts/dispatch.py worktrees --repo public --all\n"
        "Outputs: JSON list; per tree: path, task_id, borrowers, status, worktree_disposition,\n"
        "  worktree_disposition_reason, age_s, size_bytes and no_task_record (no record names it).\n"
        "Exit codes: 0 listed, 2 repository or records unavailable.\n"
        "Related: docs/design/dispatch-v2.md.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    trees.add_argument("--repo", help="fleet_repos.yaml key (default: public primary)")
    trees.add_argument("--all", action="store_true", help="Also match archived records (default: hot only)")
    retain = subs.add_parser(
        "retain-worktree",
        help="Set or clear one task's worktree retention hold",
        description="Set or clear the retention hold on one task's worktree.\n"
        "Use when an owner must keep that worktree. Settlement, salvage and scheduled cleanup then "
        "leave it untouched. Do not use this command to publish, delete, or inspect the worktree.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
        "  .venv/bin/python scripts/dispatch.py retain-worktree TASK --set\n"
        "  .venv/bin/python scripts/dispatch.py retain-worktree TASK --clear\n"
        "Outputs: JSON with task_id and worktree_retention_hold. Writes the task record only.\n"
        "Side effects: --set stores the hold and a non-retry retained disposition; --clear removes the "
        "hold and any retention_hold or retention_hold_invalid disposition. Neither pushes "
        "nor removes the worktree.\n"
        "Exit codes: 0 hold updated, 2 missing record or invalid request.\n"
        "Related: docs/runbooks/worktree-cleanup.md.",
    )
    retain.add_argument("task_id", help="Task ID whose worktree to hold, e.g. worker-42")
    mode = retain.add_mutually_exclusive_group(required=True)
    mode.add_argument("--set", action="store_true", help="Set the hold (required unless --clear)")
    mode.add_argument("--clear", action="store_true", help="Clear the hold; does not push or remove (required unless --set)")
    return parser


def _tree_size(tree: str) -> int | None:
    try:
        output = subprocess.run(["du", "-s", "-B1", "-x", "--", tree], capture_output=True, text=True,
                                timeout=60, check=True).stdout
        return int(output.split()[0])
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        return None


def _worktrees(repo_key: str | None, include_archive: bool) -> list[dict]:
    """Join the repository's registered linked worktrees with the task records that name them."""
    from scripts.orchestration.worktree_claims import repository_registration

    main_root, registered = repository_registration(git.resolve_repo(repo_key)[0])
    named: dict[str, list[dict]] = {}
    for record in store.list_tasks(include_archive=include_archive):
        if isinstance(path := record.get("worktree_path"), str) and path:
            named.setdefault(os.path.realpath(path), []).append(record)
    rows = []
    for tree in sorted(str(tree) for tree in registered if tree != main_root):
        # The owner created the tree; a task dispatched into it with --cwd only borrows it.
        records = sorted(named.get(os.path.realpath(tree), []),
                         key=lambda r: (not (r.get("options") or {}).get("cwd"), str(r.get("started_at") or "")))
        owner = records[-1] if records else {}
        try:
            age = round(time.time() - os.lstat(os.path.join(tree, ".git")).st_mtime)
        except OSError:
            age = None
        rows.append(dict(
            path=tree, task_id=owner.get("task_id"),
            borrowers=[r.get("task_id") for r in records if r is not owner],
            status=owner.get("status"), worktree_disposition=owner.get("worktree_disposition"),
            worktree_disposition_reason=owner.get("worktree_disposition_reason"),
            age_s=age, size_bytes=_tree_size(tree), no_task_record=not records,
        ))
    return rows


def _dispatch(args) -> int:
    if binding := store.review_binding(vars(args)):
        # Bound attempts have their own accounting; PR selectors would also charge their records to a PR budget.
        if args.branch is not None or args.pr is not None:
            raise ValueError(
                "review_attempt_pr_selector_unsupported: --review-attempt cannot be combined with --branch or --pr; "
                "use --pinned-head as in docs/runbooks/formal-review-attempt-isolation.md#running-a-bound-attempt"
            )
        store.check_review_attempt(binding)
        # The supervisor re-reads the manifest from another working directory.
        args.review_attempt = str(Path(args.review_attempt).resolve())
    if args.require_review_verdict and args.mode != "read-only":
        raise ValueError("--require-review-verdict requires --mode read-only")
    # Resolved once, before anything reads the owned paths: the advisory binding, bounded admission, the
    # sparse checkout and the task record all see this set, and hooks and settlement read it from the record.
    args.owned_path, generated = scope.with_generated_outputs(args.owned_path)
    for output in generated:
        print(f"dispatcher: owned paths include {output}; a commit gate regenerates it from the owned paths",
              file=sys.stderr)
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
    if agent == "agy":
        # The requested Claude id is the catalog's AGY wire id, not the bare catalog id.
        from scripts.dispatcher.providers.agy import transport_model

        args.model = transport_model(args.model)
    # An unknown Claude account label reaches admission, which refuses it typed (claude_account_unknown).
    if agent not in providers.PROVIDERS:
        aliases = ", ".join(f"{name}={target}" for name, target in ALIASES.items())
        raise ValueError(f"unknown agent {args.agent!r}; supported agents: {', '.join(providers.PROVIDERS)} "
                         f"(aliases: {aliases}); dispatch Grok as --agent cursor --model grok-4.7-high")
    if agent in {"claude", "codex", "agy", "cursor", "muse", "opencode"}:
        from scripts.dispatcher.review_tools import sources_config

        sources_config()  # A missing trusted Sources runtime refuses before any task or worktree is created.
    if args.contributor_mode is not None and agent != "muse":
        raise ValueError("--contributor-mode is only supported with --agent muse")
    if args.advisor is not None and not (
        agent == "claude" and args.mode == "workspace-write" and providers.load("claude").model_id(args.model) == "claude-haiku-5-5"
    ):
        raise ValueError("--advisor is supported only for a workspace-write Claude Haiku 5.5 run")
    if args.output_schema is not None and agent not in {"codex", "agy", "claude"}:
        raise ValueError("--output-schema is supported only with the effective codex, agy, or claude agent")
    # Checked before admission and before any worker starts. A path that cannot be mounted is not dropped.
    bound_inputs = []
    if args.input:
        if agent != "agy" or args.mode != "read-only":
            raise ValueError("agy_input_refused: --input requires --agent agy and --mode read-only")
        from scripts.dispatcher.agy_sandbox import bind_inputs

        bound_inputs = bind_inputs(args.input, repo_root=git.resolve_repo(args.repo)[0])
    if args.mode == "read-only" and (refusal := providers.read_only_refusal(agent)):
        raise ValueError(refusal)
    deadlines(vars(args))
    if args.cwd and (args.branch or args.pinned_head or args.worktree is not None):
        raise ValueError("invalid process deadline or conflicting existing-worktree options")
    account_fields = admission.claude_account(agent, args.claude_account)
    args.claude_account = account_fields.get("claude_account", args.claude_account)
    if admission.claude_budget(args.claude_account, args.max_budget_usd) is None and args.max_budget_usd is not None:
        raise ValueError("--max-budget-usd applies only to a Claude API-key account")
    account_fields.update(admission.codex_account(agent, args.codex_account))
    args.codex_account = account_fields.get("codex_account")
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
    host_admission.precheck(args.mode, force_reason=args.force_admission)
    role_record = {**vars(args), **account_fields, "prompt_sha256": store.digest(prompt),
                   "repository_id": info.get("github")}
    trial_fields = checks.check_trial_shadow(agent, args.model, role_record)
    role_record.update(trial_fields)
    try:
        headroom.check_plan(agent, args.model, role_record,
                            review=admission.review_typed(vars(args)) or bool(args.risk))
    except headroom.model_pause.ModelPausedRefused as exc:
        raise host_admission.Refused(f"❌ {exc}", 2) from None
    host_admission.check_credit(agent, args.model)
    checks.check_model_admission(agent, args.model, args.mode, vars(args), prompt)
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
    options = {key: str(value) for key, value in vars(args).items()
               if value is not None and key not in {"prompt", "input"}}
    if bound_inputs:
        options["inputs"] = json.dumps(bound_inputs, separators=(",", ":"), sort_keys=True)
    output_schema = args.output_schema
    if agent in {"codex", "agy", "claude"} and args.require_review_verdict and output_schema is None:
        from scripts.review.review_contract import schema_path

        selected = schema_path(profile=args.review_profile, task=vars(args))
        if selected is not None:
            output_schema = str(selected)
    if output_schema is not None:
        from scripts.dispatcher.output_schema import bind

        options.update(bind(output_schema, repo))
        if agent == "agy":
            from scripts.dispatcher.providers.agy import schema_argument

            schema_argument(options)
        elif agent == "claude":
            from scripts.dispatcher.providers.claude import schema_argument

            schema_argument(options)
    fields = {name: getattr(args, name) for name in ("model", "effort", "mode", "claude_account", "provider", "codex_account")}
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
    # A bound attempt is admitted before anything exists: its prompt is the exact render of its manifest
    # with these ids, its tools are granted and its pins are the commit's bytes (#12114).
    review_contract = review_attempt.admit(args, prompt, binding, repo, sha) if binding and not args.dry_run else None
    if args.review_mode == "red_team":
        checks.check_review_family(args.review_author_model, args.model, review_mode=args.review_mode)
    else:
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
    review = any((args.review_profile, args.language_lane, args.review_author_model, args.risk,
                  args.review_mode, args.pr, args.require_review_verdict, args.subject_seat,
                  args.subject_family))
    # A read-only review resolves its subjects from owned paths, and a bounded or advisory task has them sealed
    # by its envelope; any other read-only task cannot write them, so owned paths there mean the mode was
    # forgotten (#12141).
    if args.mode == "read-only" and args.owned_path and not (review or binding or advisory_fields):
        raise ValueError("--owned-path on a read-only task that is not a review: a task that writes needs "
                         "--mode workspace-write; owned paths on a read-only task only name a review's subjects")
    if args.subject_seat or args.subject_family or (args.mode == "read-only" and args.owned_path):
        exclusion = checks.check_review_subjects(agent, args.model, args.subject_seat, args.subject_family,
                                                args.owned_path, review=review)
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
    # A review round is spent at dispatch, so the budget is checked here and not only when a verdict is recorded.
    if args.mode == "read-only" and (args.pr or args.branch) and not args.advisory_role and (
        admission.review_typed(vars(args)) or args.risk or args.review_mode
    ):
        checks.check_review_budget(args, info, sha)
    with host_admission.reserve(
        task_id, args.mode, decision, agent=agent, force_reason=force_reason,
        disk_guard=lambda: not (args.worktree is not None and (worktree / ".git").exists()),
    ) as hold:
        if binding:
            store.check_review_attempt(binding)  # the supervisor claims it (review_attempt.run)
        if not args.cwd:
            git.create_worktree(repo, worktree, branch, sha, full_checkout=args.full_checkout,
                                sparse_include=git.SPARSE_EXCLUDE_DEFAULT - set(excluded), **exact_start)
        record = store.new_record(spec, info, branch, sha, vars(args), binding=binding, admission_hold=hold)
        # A task dispatched from inside another task's run names that run, whose settlement then names it while
        # it still runs (worker._running_children, #12156).
        if (parent := os.environ.get(ownership.TASK_ID_ENV)) and parent != task_id:
            record["parent_task_id"] = parent
        if review_contract is not None:
            record["review_contract"] = review_contract
        if publish_remote is not None:
            record["worktree_remote_url"] = publish_remote
        if args.mode != "read-only" and args.owned_path and record["worktree_remote_url"] is None:
            raise ValueError("write task with owned paths refused: origin must match the registered canonical repository URL")
        record.update(advisory_fields, **account_fields, **trial_fields)
        record["pool_shadow"] = pool_selector.shadow_decision(record)
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


def _retain_worktree(task_id: str, *, hold: bool) -> dict:
    """Set or clear ``worktree_retention_hold`` under the task lock. Never pushes or removes."""
    path = store.record_path(task_id)
    with store.task_state_lock(path):
        record = store.read(task_id)
        if record.get("schema_version") != 2:
            raise ValueError("retention hold requires a dispatch v2 task")
        if hold:
            record["worktree_retention_hold"] = True
            record["worktree_disposition"] = "retained"
            record["worktree_disposition_reason"] = "retention_hold"
            record.pop("worktree_disposition_detail", None)
        else:
            # False, not absence: a stale copy must not put the hold back.
            record["worktree_retention_hold"] = False
            if record.get("worktree_disposition_reason") in {"retention_hold", "retention_hold_invalid"}:
                record.pop("worktree_disposition", None)
                record.pop("worktree_disposition_reason", None)
                record.pop("worktree_disposition_detail", None)
        store.replace(record, path)
    return {"task_id": task_id, "worktree_retention_hold": hold}


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
        if args.command == "retain-worktree":
            print(json.dumps(_retain_worktree(args.task_id, hold=args.set), indent=2))
            return 0
        if args.command == "grant-paths":
            try:
                result = store.grant_paths(args.task_id, args.run_nonce, args.owned_path, args.reason, args.approval_ref)
            except (OSError, subprocess.SubprocessError) as exc:
                print(f"dispatcher: grant failed ({type(exc).__name__})", file=sys.stderr)
                return 1
            print(json.dumps(result, indent=2))
            return 0
        code = 0
        if args.command == "worktrees":
            result = _worktrees(args.repo, args.all)
        elif args.command == "list":
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
