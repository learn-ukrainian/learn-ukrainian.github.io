"""Five-command interface for the minimal dispatcher."""

import argparse
import json
import re
import subprocess
import sys
import uuid
from pathlib import Path
from typing import get_args

from scripts.common.git_context import validate_plain_branch_name
from scripts.dispatcher import admission, checks, git, providers, store, worker, write_intent
from scripts.dispatcher.environment import child_env
from scripts.dispatcher.types import ReviewAccess, TaskSpec

ALIASES = dict(sol="codex", grok="cursor", gemini="agy", deepseek="opencode", openrouter="hermes")


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
        "Exit codes: 0 success, 1 terminal failure, 2 invalid/refused request, 124 client timeout.\n"
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
        "Outputs: task ID and nonce; task JSON, prompt, result, logs and dispatch worktree.\n"
        "  Muse task JSON records the effective contributor_mode. --dry-run prints a plan and creates nothing.\n"
        "Exit codes: 0 task started or plan printed, 2 invalid/refused request.\n"
        "Related: docs/design/dispatch-v2.md.",
    )
    for flag, default, help_text in (
        ("agent", None, "Provider or alias, e.g. sol (required)"),
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
        ("claude-account", None, "Claude account a or b (default: inherited configuration)"),
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
    dispatch.add_argument("--dry-run", action="store_true", help="Print plan; create nothing (default: off)")
    dispatch.add_argument("--print-advisory-binding", action="store_true",
                          help="Print this request's envelope binding; needs --task-id, creates nothing (default: off)")
    dispatch.add_argument(
        "--full-checkout", action="store_true",
        help="Materialize the full Git working tree instead of excluding heavy trees (default: off)",
    )
    dispatch.add_argument(
        "--sparse-include", action="append", default=[], metavar="DIR",
        help="Keep a default-excluded tree; repeatable (default: none). Example: --sparse-include curriculum. "
        "Excluded: " + ", ".join(sorted(git.SPARSE_EXCLUDE_DEFAULT)),
    )
    dispatch.add_argument(
        "--hard-timeout", type=float, default=7200, help="Deadline seconds; 0 disables (default: 7200)"
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
    git.sparse_excludes(args.sparse_include)
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
    # runs before any check, worktree or task record (delegate.py cmd_dispatch, rules_core.require_core).
    from scripts.lib import rules_core

    try:
        rules_core.require_core()
    except rules_core.RulesCoreMissing as exc:
        raise ValueError(f"dispatch refused: {exc}; the rules core is required.") from None
    if write_intent_error := write_intent._read_only_write_intent_error(mode=args.mode, prompt=prompt.decode()):
        raise ValueError(write_intent_error)
    agent = ALIASES.get(args.agent, args.agent)
    # An unknown Claude account label reaches admission, which refuses it typed (claude_account_unknown).
    if agent not in providers.PROVIDERS:
        raise ValueError("unknown agent or Claude account")
    if args.contributor_mode is not None and agent != "muse":
        raise ValueError("--contributor-mode is only supported with --agent muse")
    if args.output_schema is not None and agent != "codex":
        raise ValueError("--output-schema is supported only with the effective codex agent")
    if args.hard_timeout < 0 or (args.cwd and (args.branch or args.pinned_head or args.worktree is not None)):
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
    advisory_fields = checks.check_bounded_advisory(args, args.model, repo, prompt)
    if args.branch is not None:
        args.branch = validate_plain_branch_name(args.branch, repo_root=repo)
    start = args.pinned_head or args.branch or args.base
    publish_remote = None
    if args.mode == "workspace-write" and args.branch and not args.pinned_head and not args.dry_run:
        start, publish_remote = git.publish_start(repo, info, args.branch, task_id)
    worktree, branch, sha = git.worktree_plan(
        repo, agent, task_id, start, args.cwd, args.worktree
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
    checks.check_review_family(args.review_author_model, args.model)
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
    checks.check_resources((worktree, path.parent))
    if args.dry_run:
        # The real run re-checks child_env after worktree creation in worker.py.
        invocation = providers.load(agent).build(spec, child_env(spec))
        plan = dict(worktree=str(worktree), argv=invocation.argv, record_path=str(path))
        if binding:
            plan.update(review_attempt=binding, review_access=args.review_access or "isolated")
        print(json.dumps(plan, indent=2))
        return 0
    if binding:
        store.check_review_attempt(binding, claim=True)
    if not args.cwd:
        git.create_worktree(repo, worktree, branch, sha, full_checkout=args.full_checkout, sparse_include=args.sparse_include)
    record = store.new_record(spec, info, branch, sha, vars(args), binding=binding)
    if publish_remote is not None:
        record["worktree_remote_url"] = publish_remote
    if args.mode != "read-only" and args.owned_path and record["worktree_remote_url"] is None:
        raise ValueError("write task with owned paths refused: origin must match the registered canonical repository URL")
    record.update(advisory_fields, **account_fields)
    if agent == "muse":
        record["contributor_mode"] = spec.options.get("contributor_mode", "off")
    try:
        worker.start(spec, record, prompt, args.hard_timeout)
    except admission.LaunchRefused as exc:
        # The record is already terminal: exit 1 like the legacy spawn refusal, never relaunch.
        print(f"dispatcher: failed to spawn worker for {task_id!r}: {exc}", file=sys.stderr)
        return 1
    print(task_id, record["run_nonce"], sep="\n")
    return 0


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "dispatch":
            return _dispatch(args)
        code = 0
        if args.command == "list":
            result = store.list_tasks(args.status, args.all)
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
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        message = str(exc).splitlines()[0] if isinstance(exc, ValueError) else type(exc).__name__
        print(f"dispatcher: {message}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
