"""CLI for the local-code-review closeout workflow.

Ties together target resolution, scope-baseline freezing/breakers, findings
adjudication, and reviewer resolution behind one state file so an agent
driving the skill in ``agents_extensions/shared/skills/local-code-review/``
can call a subcommand per step instead of re-deriving the logic by hand.

State lives in a single JSON file (``--state-file``, an ``.agent/`` scratch
path by convention) for the duration of one closeout review. Every
subcommand is read-mostly against the repo — nothing here runs ``ruff --fix``,
formatters, generators, or any other mutating command.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

from scripts.common.git_context import sanitized_git_env
from scripts.fleet import credit_lane
from scripts.review.evidence import compute_target_input_fingerprint
from scripts.review.findings import FindingEvent, FindingsLedger, FindingsLedgerError
from scripts.review.model_catalog import VALID_REVIEW_PROFILES, VALID_RISKS
from scripts.review.record_cf_verdict import (
    BranchFactsError,
    authorship_exclude_sha,
    collect_branch_review_facts,
    refuse_excluded_only_range,
)
from scripts.review.reviewer_resolver import ResolverInputs, resolve_reviewer
from scripts.review.scope_baseline import (
    ScopeBaseline,
    check_cycle_convergence_breaker,
    check_expansion_breaker,
)
from scripts.review.security_paths import git_changed_paths
from scripts.review.target_resolution import (
    ReviewTarget,
    TargetResolutionError,
    diff_against_base,
    resolve_local_target,
    resolve_review_target,
    rev_parse,
)

BEHAVIOR_PROOF_SCHEMA_VERSION = "behavior-proof.v1"


class CloseoutStateError(RuntimeError):
    """The canonical closeout state is malformed or cannot be read."""


def _load_state(state_file: Path) -> dict:
    if not state_file.exists():
        return {
            "target": None,
            "target_args": None,
            "baseline": None,
            "behavior_proof": {},
            "cycle_outstanding_counts": [],
            "findings": [],
        }
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        raise CloseoutStateError(f"state_unreadable:{exc}") from exc
    except json.JSONDecodeError as exc:
        raise CloseoutStateError(f"state_invalid_json:{exc.msg}") from exc
    if not isinstance(state, dict):
        raise CloseoutStateError("state_must_be_object")
    return state


def _save_state(state_file: Path, state: dict) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def _target_from_dict(data: object) -> ReviewTarget:
    if not isinstance(data, dict):
        raise CloseoutStateError("target_must_be_object")
    mode = data.get("mode")
    base_sha = data.get("base_sha")
    head_sha = data.get("head_sha")
    changed_paths = data.get("changed_paths")
    non_test_loc = data.get("non_test_loc")
    clean_tree = data.get("clean_tree")
    description = data.get("description")
    base_ref_name = data.get("base_ref_name")
    if mode not in {"local", "commit", "branch", "pr"}:
        raise CloseoutStateError("target_mode_invalid")
    if not all(
        value is None or (isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{40}", value))
        for value in (base_sha, head_sha)
    ):
        raise CloseoutStateError("target_sha_invalid")
    if not isinstance(changed_paths, list) or not all(isinstance(path, str) and path for path in changed_paths):
        raise CloseoutStateError("target_changed_paths_invalid")
    if not isinstance(non_test_loc, int) or isinstance(non_test_loc, bool) or non_test_loc < 0:
        raise CloseoutStateError("target_non_test_loc_invalid")
    if not isinstance(clean_tree, bool):
        raise CloseoutStateError("target_clean_tree_invalid")
    if not isinstance(description, str) or not description.strip():
        raise CloseoutStateError("target_description_invalid")
    if base_ref_name is not None and (not isinstance(base_ref_name, str) or not base_ref_name.strip()):
        raise CloseoutStateError("target_base_ref_invalid")
    return ReviewTarget(
        mode=mode,
        base_sha=base_sha,
        head_sha=head_sha,
        changed_paths=tuple(changed_paths),
        non_test_loc=non_test_loc,
        clean_tree=clean_tree,
        description=description,
        base_ref_name=base_ref_name,
    )


def _target_args_from_state(state: dict) -> dict:
    target_args = state.get("target_args")
    if target_args is None:
        return {}
    if not isinstance(target_args, dict):
        raise CloseoutStateError("target_args_must_be_object")
    return target_args


def _ledger_from_state(state: dict) -> FindingsLedger:
    return FindingsLedger.from_events(FindingEvent(**raw) for raw in state.get("findings", []))


def _cmd_target(args: argparse.Namespace) -> int:
    state = _load_state(args.state_file)
    if state.get("baseline"):
        print(
            json.dumps(
                {
                    "error": (
                        "baseline already frozen for this state file — the target is immutable "
                        "once frozen; start a new review with a new --state-file"
                    )
                }
            ),
            file=sys.stderr,
        )
        return 1
    try:
        target = resolve_review_target(
            args.mode,
            Path(args.repo_root).resolve(),
            commit=args.commit,
            branch=args.branch,
            base=args.base,
            pr_number=args.pr,
        )
    except TargetResolutionError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1

    state["target"] = asdict(target)
    # PR mode has no --base. Keep the ref GitHub named, or a frozen target
    # that later merges the default branch cannot exclude those authors.
    stored_base = target.base_ref_name if args.mode == "pr" else args.base
    state["target_args"] = {
        "repo_root": str(Path(args.repo_root).resolve()),
        "mode": args.mode,
        "commit": args.commit,
        "branch": args.branch,
        "base": stored_base,
        "pr": args.pr,
    }
    _save_state(args.state_file, state)
    print(json.dumps(asdict(target), indent=2))
    return 0


def _cmd_freeze(args: argparse.Namespace) -> int:
    if args.review_profile.strip().casefold() not in VALID_REVIEW_PROFILES:
        print(
            json.dumps(
                {
                    "error": (
                        f"unsupported local-code-review profile {args.review_profile!r}; "
                        "learner-content semantic review belongs to track-completion via "
                        "post-build-review"
                    )
                }
            ),
            file=sys.stderr,
        )
        return 1
    state = _load_state(args.state_file)
    if state.get("baseline"):
        print(
            json.dumps(
                {
                    "error": (
                        "baseline already frozen for this state file — freeze may only be called "
                        "once; start a new review with a new --state-file"
                    )
                }
            ),
            file=sys.stderr,
        )
        return 1
    if state.get("target") is None:
        print(json.dumps({"error": "no target resolved yet — run the `target` subcommand first"}), file=sys.stderr)
        return 1

    target = _target_from_dict(state["target"])
    baseline = ScopeBaseline.freeze(
        issue_ref=args.issue,
        intended_behavior=args.intended_behavior,
        non_goals=args.non_goals,
        owner_boundary=args.owner_boundary,
        target=target,
        review_profile=args.review_profile,
        risk=args.risk,
    )
    state["baseline"] = {
        "issue_ref": baseline.issue_ref,
        "intended_behavior": baseline.intended_behavior,
        "non_goals": baseline.non_goals,
        "owner_boundary": baseline.owner_boundary,
        "target": asdict(baseline.target),
        "review_profile": baseline.review_profile,
        "risk": baseline.risk,
        "frozen_files": sorted(baseline.frozen_files),
        "frozen_non_test_loc": baseline.frozen_non_test_loc,
    }
    state["cycle_outstanding_counts"] = []
    _save_state(args.state_file, state)
    print(baseline.render())
    return 0


def _baseline_from_state(state: dict) -> ScopeBaseline:
    data = state.get("baseline")
    if not isinstance(data, dict):
        raise CloseoutStateError("baseline_must_be_object")
    required_strings = (
        "issue_ref",
        "intended_behavior",
        "non_goals",
        "owner_boundary",
        "review_profile",
        "risk",
    )
    for key in required_strings:
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            raise CloseoutStateError(f"baseline_{key}_invalid")
    frozen_files = data.get("frozen_files")
    frozen_non_test_loc = data.get("frozen_non_test_loc")
    if not isinstance(frozen_files, list) or not all(isinstance(path, str) and path for path in frozen_files):
        raise CloseoutStateError("baseline_frozen_files_invalid")
    if not isinstance(frozen_non_test_loc, int) or isinstance(frozen_non_test_loc, bool) or frozen_non_test_loc < 0:
        raise CloseoutStateError("baseline_frozen_non_test_loc_invalid")
    target = data.get("target")
    if not isinstance(target, dict):
        raise CloseoutStateError("baseline_target_invalid")
    return ScopeBaseline(
        issue_ref=data["issue_ref"],
        intended_behavior=data["intended_behavior"],
        non_goals=data["non_goals"],
        owner_boundary=data["owner_boundary"],
        target=_target_from_dict(target),
        review_profile=data["review_profile"],
        risk=data["risk"],
        frozen_files=frozenset(frozen_files),
        frozen_non_test_loc=frozen_non_test_loc,
    )


def _cmd_check_expansion(args: argparse.Namespace) -> int:
    """Re-measure the frozen target's mode against its current state.

    ``local`` mode is re-resolved from the working tree, same as before — it
    has no committed endpoint by definition. Every other mode (commit/branch/
    pr) is frozen against a committed base/head, so a clean working tree
    tells us nothing: review-triggered fixes land as *commits*, not
    uncommitted changes. Re-resolving those modes means re-diffing the
    frozen ``base_sha`` against an explicit ``--current-head`` (the reviewed
    head after fixes) — never re-querying ``gh pr view`` or re-deriving the
    mode from ``git status``, since either could silently drift from the
    mode the baseline was actually frozen under.
    """
    state = _load_state(args.state_file)
    if state.get("baseline") is None:
        print(json.dumps({"error": "no frozen baseline yet — run `freeze` first"}), file=sys.stderr)
        return 1
    baseline = _baseline_from_state(state)
    repo_root = Path(args.repo_root).resolve()
    target_args = _target_args_from_state(state)
    mode = target_args.get("mode") or baseline.target.mode

    try:
        if mode == "local":
            current = resolve_local_target(repo_root)
            current_files = frozenset(current.changed_paths)
            current_non_test_loc = current.non_test_loc
        else:
            if not args.current_head:
                print(
                    json.dumps(
                        {
                            "error": (
                                f"check-expansion for mode={mode!r} requires --current-head "
                                "(the explicit reviewed head after any committed fixes) — "
                                "a clean local working tree is not evidence that committed "
                                "fixes were re-measured against the frozen baseline"
                            )
                        }
                    ),
                    file=sys.stderr,
                )
                return 1
            if not baseline.target.base_sha:
                print(
                    json.dumps({"error": f"frozen baseline for mode={mode!r} has no base_sha to re-diff against"}),
                    file=sys.stderr,
                )
                return 1
            current_head_sha = rev_parse(repo_root, args.current_head)
            changed_paths, non_test_loc = diff_against_base(repo_root, baseline.target.base_sha, current_head_sha)
            current_files = frozenset(changed_paths)
            current_non_test_loc = non_test_loc
    except TargetResolutionError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1

    result = check_expansion_breaker(baseline, current_files, current_non_test_loc)
    print(json.dumps({"triggered": result.triggered, "reason": result.reason}, indent=2))
    return 0


def _cmd_record_cycle(args: argparse.Namespace) -> int:
    state = _load_state(args.state_file)
    if state.get("baseline") is None:
        print(json.dumps({"error": "no frozen baseline yet — run `freeze` first"}), file=sys.stderr)
        return 1
    if args.outstanding_count < 0:
        print(
            json.dumps({"error": f"--outstanding-count must be >= 0, got {args.outstanding_count}"}),
            file=sys.stderr,
        )
        return 1
    state.setdefault("cycle_outstanding_counts", []).append(args.outstanding_count)
    result = check_cycle_convergence_breaker(state["cycle_outstanding_counts"])
    _save_state(args.state_file, state)
    print(
        json.dumps(
            {"triggered": result.triggered, "reason": result.reason, "history": state["cycle_outstanding_counts"]},
            indent=2,
        )
    )
    return 0


def _checkout_git(repo_root: Path, *args: str) -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
            env=sanitized_git_env(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CloseoutStateError(f"git {args[0]} unavailable") from exc
    if proc.returncode:
        raise CloseoutStateError(f"git {args[0]} failed")
    return proc.stdout.strip()


def _checkout_repository(repo_root: Path) -> str:
    """``owner/name`` of the checkout's GitHub origin, which task records must name."""
    url = _checkout_git(repo_root, "config", "--get", "remote.origin.url")
    match = re.search(r"github\.com[:/]([\w.-]+/[\w.-]+?)(?:\.git)?/?$", url)
    if not match:
        raise CloseoutStateError("repository unknown: pass --repository owner/name")
    return match.group(1)


def _checkout_task_root(repo_root: Path) -> Path:
    """The primary checkout's dispatch task records, shared by every linked worktree."""
    common = Path(_checkout_git(repo_root, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    return common.parent / "batch_state" / "tasks"


def _cmd_resolve_reviewer(args: argparse.Namespace) -> int:
    if args.domain.strip().casefold() not in VALID_REVIEW_PROFILES:
        print(
            json.dumps(
                {
                    "selected": None,
                    "fail_closed_reason": (
                        f"unsupported local-code-review domain {args.domain!r}; learner-content "
                        "semantic review belongs to track-completion via post-build-review"
                    ),
                },
                indent=2,
            )
        )
        return 1
    if args.routing_snapshot_file:
        routing_snapshot = json.loads(Path(args.routing_snapshot_file).read_text(encoding="utf-8"))
        snapshot_source = "file"
    else:
        routing_snapshot = credit_lane.read_routing_budget(timeout=8.0)
        snapshot_source = "live"
    diagnostics = routing_snapshot.get("diagnostics") if isinstance(routing_snapshot, dict) else None
    freshness, fallback_reason = credit_lane.snapshot_freshness(diagnostics)
    if routing_snapshot is None:
        fallback_reason = "live routing snapshot unavailable"
    snapshot_receipt = {
        "source": snapshot_source,
        "freshness": freshness,
        "fallback_reason": fallback_reason or None,
    }
    state = _load_state(args.state_file)
    target = _target_from_dict(state["target"]) if state.get("target") is not None else None
    if args.review_profile == "code" and target is None and not args.owned_path:
        raise CloseoutStateError("review_target_required: resolve the target first or supply --owned-path")
    changed_paths = target.changed_paths if target else ()
    facts = None
    if target:
        # numstat display paths compact renames (a/{old => new}/file). Read
        # literal filenames from the frozen endpoints instead of parsing that
        # presentation; --no-renames exposes both names, including deletions.
        target_args = _target_args_from_state(state)
        repo_root_value = target_args.get("repo_root")
        if not isinstance(repo_root_value, str) or not repo_root_value:
            raise CloseoutStateError("target_repo_root_missing")
        repo_root = Path(repo_root_value)
        try:
            base_sha = rev_parse(repo_root, "HEAD") if target.mode == "local" else target.base_sha
            literal_paths = git_changed_paths(repo_root, base_sha, target.head_sha)
        except TargetResolutionError as exc:
            raise CloseoutStateError(str(exc)) from exc
        changed_paths = tuple(dict.fromkeys((*changed_paths, *literal_paths)))
        if target.mode != "local":
            # A committed target has complete Git authorship: select from the
            # same facts the verdict recorder accepts (#9739). --author-model is
            # added to them, never substituted for them.
            try:
                raw_base = target_args.get("base")
                exclude = authorship_exclude_sha(repo_root, base_branch=raw_base if isinstance(raw_base, str) else None)
                facts = collect_branch_review_facts(
                    repository=args.repository or _checkout_repository(repo_root),
                    repo_root=repo_root,
                    base_tip_sha=target.base_sha,
                    head_sha=target.head_sha,
                    task_root=Path(args.task_root) if args.task_root else _checkout_task_root(repo_root),
                    owned_paths=tuple(args.owned_path or []),
                    subject_seats=tuple(args.subject_seat or []),
                    subject_families=tuple(args.subject_family or []),
                    authorship_exclude_sha=exclude,
                )
                refuse_excluded_only_range(facts, repo_root=repo_root, exclude_sha=exclude)
            except (BranchFactsError, CloseoutStateError) as exc:
                payload = {"selected": None, "fail_closed_reason": f"branch review facts unavailable: {exc}"}
                state["resolved_reviewer"] = payload
                _save_state(args.state_file, state)
                print(json.dumps(payload, indent=2))
                return 1
    common = {
        "author_model": args.author_model,
        "domain": args.domain,
        "language_lane": args.language_lane,
        "required_capabilities": frozenset(args.required_capability or []),
        "data_egress_policy": args.data_egress_policy,
        "isolation_required": args.isolation_required,
        "routing_snapshot": routing_snapshot,
        "author_family": args.author_family,
        "contested": bool(getattr(args, "contested", False)),
    }
    if facts is not None:
        inputs = facts.resolver_inputs(risk=args.risk, review_profile=args.review_profile, **common)
    else:
        inputs = ResolverInputs(
            review_profile=args.review_profile,
            risk=args.risk,
            changed_paths=changed_paths,
            subject_seats=frozenset(args.subject_seat or []),
            subject_families=frozenset(args.subject_family or []),
            owned_paths=tuple(args.owned_path or []),
            **common,
        )
    resolution = resolve_reviewer(inputs)
    payload = {
        "selected": asdict(resolution.selected) if resolution.selected else None,
        "routing_snapshot": snapshot_receipt,
        "branch_facts": facts.receipt() if facts is not None else None,
        "quorum": [asdict(q) for q in resolution.quorum],
        "quorum_rule": resolution.quorum_rule,
        "advisory": [asdict(a) for a in resolution.advisory],
        "trace": [asdict(t) for t in resolution.trace],
        "substitution_note": resolution.substitution_note,
        "policy_version": resolution.policy_version,
        "catalog_reviewed_on": resolution.catalog_reviewed_on,
        "resolved_risk": resolution.resolved_risk,
        "fail_closed_reason": resolution.fail_closed_reason,
    }
    # Persist the durable receipt: drivers downstream expect the resolution on
    # disk, not just on stdout. Merge with any prior state; without a target,
    # code-profile resolution needs explicit owned paths.
    state["resolved_reviewer"] = payload
    _save_state(args.state_file, state)
    print(json.dumps(payload, indent=2))
    if resolution.fail_closed_reason:
        return 1
    # A dual-family quorum plan (unattested-harness author) is a successful
    # resolution: no single reviewer of record, both seats must PASS.
    if len(resolution.quorum) >= 2:
        return 0
    return 1 if resolution.selected is None else 0


def _cmd_finding(args: argparse.Namespace) -> int:
    state = _load_state(args.state_file)
    ledger = _ledger_from_state(state)
    try:
        if args.finding_action == "raise":
            ledger.raise_finding(args.id, summary=args.summary, source=args.source)
        elif args.finding_action == "adjudicate":
            ledger.adjudicate(args.id, disposition=args.disposition, rationale=args.rationale)
        elif args.finding_action == "apply":
            ledger.apply(args.id)
        elif args.finding_action == "skip":
            ledger.skip(args.id, rationale=args.rationale)
        elif args.finding_action == "report":
            print(ledger.render_report())
            return 0
    except FindingsLedgerError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1

    state["findings"] = [asdict(e) for e in ledger.events()]
    _save_state(args.state_file, state)
    print(json.dumps({"ok": True, "finding_id": args.id}))
    return 0


def _cmd_behavior_proof(args: argparse.Namespace) -> int:
    """Record target-bound behavior proof from the frozen closeout state."""
    state = _load_state(args.state_file)
    if state.get("baseline") is None:
        print(json.dumps({"error": "no frozen baseline yet — run `freeze` first"}), file=sys.stderr)
        return 1
    baseline = _baseline_from_state(state)
    target_args = _target_args_from_state(state)
    repo_root_raw = target_args.get("repo_root")
    if not isinstance(repo_root_raw, str) or not repo_root_raw:
        print(json.dumps({"error": "frozen target has no repository root"}), file=sys.stderr)
        return 1
    try:
        target_input_sha256 = compute_target_input_fingerprint(Path(repo_root_raw), baseline.target)
    except Exception as exc:
        print(json.dumps({"error": f"target_fingerprint_unavailable:{exc}"}), file=sys.stderr)
        return 1

    proof = state.get("behavior_proof", {})
    if not isinstance(proof, dict):
        raise CloseoutStateError("behavior_proof_must_be_object")
    if proof and proof.get("schema_version") != BEHAVIOR_PROOF_SCHEMA_VERSION:
        raise CloseoutStateError("behavior_proof_schema_version_invalid")
    if args.behavior_action == "emit":
        if not any(key in proof for key in ("source_aware", "source_blind")):
            print(json.dumps({"error": "no behavior proof recorded yet"}), file=sys.stderr)
            return 1
        print(json.dumps(proof, indent=2, sort_keys=True))
        return 0

    if args.status == "pass":
        command = args.command.strip() if isinstance(args.command, str) else None
        step = args.step.strip() if isinstance(args.step, str) else None
        has_command = bool(command)
        has_step = bool(step)
        if has_command == has_step:
            print(json.dumps({"error": "passing proof requires --command or --step"}), file=sys.stderr)
            return 1
        if has_command and (not isinstance(args.cwd, str) or not args.cwd.strip()):
            print(json.dumps({"error": "command proof requires --cwd"}), file=sys.stderr)
            return 1
        if args.exit_code is None and (not isinstance(args.result, str) or not args.result.strip()):
            print(json.dumps({"error": "passing proof requires --exit-code or --result"}), file=sys.stderr)
            return 1
        if not isinstance(args.observation, str) or not args.observation.strip():
            print(json.dumps({"error": "passing proof requires --observation"}), file=sys.stderr)
            return 1
        if not isinstance(args.evidence_ref, str) or not args.evidence_ref.strip():
            print(json.dumps({"error": "passing proof requires --evidence-ref"}), file=sys.stderr)
            return 1
        clause: dict[str, object] = {
            # The claim is derived from the frozen baseline; callers cannot
            # provide a competing behavior-surface string.
            "claim": baseline.intended_behavior,
            "target_input_sha256": target_input_sha256,
            "observation": args.observation,
            "evidence_ref": args.evidence_ref,
        }
        if has_command:
            clause["command"] = command
            clause["cwd"] = args.cwd
        else:
            clause["step"] = step
        if args.exit_code is not None:
            clause["exit_code"] = args.exit_code
        else:
            clause["result"] = args.result
        surface: dict[str, object] = {"status": "pass", "clauses": [clause]}
    else:
        if args.status == "n/a" and (not isinstance(args.reason, str) or not args.reason.strip()):
            print(json.dumps({"error": "n/a proof requires --reason"}), file=sys.stderr)
            return 1
        surface = {"status": args.status, "reason": args.reason}

    proof["schema_version"] = BEHAVIOR_PROOF_SCHEMA_VERSION
    if args.surface == "source_blind" and (args.status == "pass" or args.blind_enforced):
        surface["blind_enforced"] = args.blind_enforced
    proof[args.surface] = surface
    state["behavior_proof"] = proof
    _save_state(args.state_file, state)
    print(json.dumps(proof, indent=2, sort_keys=True))
    return 0


_CLOSEOUT_EPILOG = """\
Examples:
  .venv/bin/python -m scripts.review.closeout_cli --state-file .agent/review.json \\
    target --mode pr --pr 8946 --repo-root .
  .venv/bin/python -m scripts.review.closeout_cli --state-file .agent/review.json \\
    resolve-reviewer --author-model codex:gpt-6.1-sol --risk high --domain infra \\
    --owned-path scripts/agent_runtime/adapters/grok_build.py
  .venv/bin/python -m scripts.review.closeout_cli --state-file .agent/review.json \\
    resolve-reviewer --author-model claude --subject-seat grok

NOTE: --state-file is a global argument and must precede the subcommand.

Outputs:
  stdout JSON for the subcommand, and the same closeout state JSON file
  (--state-file). resolve-reviewer merges a resolved_reviewer receipt into
  that file. Nothing here mutates the git tree.

Exit codes:
  0  the subcommand completed (resolve-reviewer: a reviewer was selected, or
     a dual-family quorum was planned)
  1  the subcommand failed closed (bad target, unsupported profile, no
     eligible reviewer, ambiguous subject-seat path, ledger error)

Related:
  agents_extensions/shared/skills/local-code-review/local-code-review-checklist.md
  scripts/review/reviewer_resolver.py
  scripts/config/model_catalog.yaml
  issue #8946 (subject-seat exclusion) under epic #8875
"""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=".venv/bin/python -m scripts.review.closeout_cli",
        description=(
            "Drive one local code-review closeout from a single state file.\n"
            "Use it for target, scope freeze, findings, and cross-family reviewer "
            "resolution. Do not use it for learner-content semantic review "
            "(track-completion / post-build-review) or to apply fixes."
        ),
        epilog=_CLOSEOUT_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--state-file",
        required=True,
        type=Path,
        help=(
            "Path to the closeout state JSON file (global argument — must precede the "
            "subcommand). Created on first write; subcommands merge into any existing state. "
            "Example: .agent/review-closeout/impl-8946.json"
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_target = sub.add_parser("target", help="Resolve the review target (local/commit/branch/pr)")
    p_target.add_argument(
        "--mode",
        required=True,
        choices=["local", "commit", "branch", "pr"],
        help=(
            "How to resolve the diff. local = staged+unstaged+untracked vs HEAD; "
            "commit = one SHA vs its parent; branch = --branch vs --base; "
            "pr = the PR's merge-base. Example: pr"
        ),
    )
    p_target.add_argument(
        "--repo-root",
        default=".",
        help="Repository root to diff. Default: . Example: .",
    )
    p_target.add_argument("--commit", help="Commit SHA for --mode commit. Example: HEAD")
    p_target.add_argument("--branch", help="Branch name for --mode branch. Example: grok/impl-8946")
    p_target.add_argument("--base", help="Base ref for --mode branch. Example: origin/main")
    p_target.add_argument("--pr", type=int, help="Pull request number for --mode pr. Example: 8946")
    p_target.set_defaults(func=_cmd_target)

    p_freeze = sub.add_parser("freeze", help="Freeze the scope baseline from the resolved target")
    p_freeze.add_argument(
        "--issue", required=True, help="Issue or request reference stored on the baseline. Example: #8946"
    )
    p_freeze.add_argument(
        "--intended-behavior",
        required=True,
        help="What the change is supposed to do. Example: exclude the seat the change governs",
    )
    p_freeze.add_argument(
        "--non-goals",
        required=True,
        help="What the change explicitly does not do. Example: no quality-ladder changes",
    )
    p_freeze.add_argument(
        "--owner-boundary",
        required=True,
        help="Paths or surfaces this change owns. Example: scripts/review",
    )
    p_freeze.add_argument(
        "--review-profile",
        default="code",
        help="Closeout profile. Default: code. Example: code or infra",
    )
    p_freeze.add_argument(
        "--risk",
        default="medium",
        help="Review risk recorded on the baseline. Default: medium. Example: high",
    )
    p_freeze.set_defaults(func=_cmd_freeze)

    p_expansion = sub.add_parser("check-expansion", help="Check the 2x files/LOC scope-expansion breaker")
    p_expansion.add_argument("--repo-root", default=".", help="Repository root to re-diff. Default: . Example: .")
    p_expansion.add_argument(
        "--current-head",
        default=None,
        help=(
            "Required for commit/branch/pr-mode targets: the explicit reviewed head "
            "(e.g. HEAD, or a specific SHA) to re-diff against the frozen base_sha "
            "after committed fixes. Ignored for mode=local, which re-resolves from "
            "the working tree instead. Default: unset."
        ),
    )
    p_expansion.set_defaults(func=_cmd_check_expansion)

    p_cycle = sub.add_parser("record-cycle", help="Record one review/fix cycle's outstanding-finding count")
    p_cycle.add_argument(
        "--outstanding-count",
        required=True,
        type=int,
        help="Outstanding finding count after this cycle. Example: 0",
    )
    p_cycle.set_defaults(func=_cmd_record_cycle)

    p_reviewer = sub.add_parser(
        "resolve-reviewer",
        help="Resolve the cross-family reviewer for this author",
        description=(
            "Pick the formal cross-family reviewer for one author.\n"
            "Resolve the target first in the same state file, or supply --owned-path. "
            "For a committed target (commit, branch, pr), every author named by the "
            "target's X-Agent trailers and task records is excluded too, as the verdict "
            "recorder requires (#9739); --author-model adds to them. "
            "Use it after the author model is known. Pass --subject-seat, "
            "--subject-family, or --owned-path when the change governs a seat's "
            "adapter or reviewer hooks. Do not use it to hand-pick a lane, and do "
            "not use it for learner-content semantic review."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.review.closeout_cli --state-file .agent/review.json \\\n"
            "    resolve-reviewer --author-model claude --risk high\n"
            "  .venv/bin/python -m scripts.review.closeout_cli --state-file .agent/review.json \\\n"
            "    resolve-reviewer --author-model codex:gpt-6.1-sol --domain infra --risk high \\\n"
            "    --owned-path scripts/agent_runtime/adapters/grok_build.py\n"
            "  .venv/bin/python -m scripts.review.closeout_cli --state-file .agent/review.json \\\n"
            "    resolve-reviewer --author-model claude --subject-seat grok --subject-family xai\n"
            "\n"
            "Outputs:\n"
            "  stdout JSON (selected, quorum, advisory, trace, fail_closed_reason) and the\n"
            "  same object stored at resolved_reviewer in --state-file. Code-profile\n"
            "  resolution requires a target or owned path; security paths raise risk to critical.\n"
            "  A governed seat is excluded and the trace records why.\n"
            "\n"
            "Exit codes:\n"
            "  0  a reviewer was selected, or a dual-family quorum was planned\n"
            "  1  fail-closed (unknown author, ambiguous owned path, unknown subject\n"
            "     seat/family, or no eligible reviewer)\n"
            "\n"
            "Related:\n"
            "  scripts/review/reviewer_resolver.py\n"
            "  scripts/review/subject_seat.py\n"
            "  scripts/config/model_catalog.yaml\n"
            "  agents_extensions/shared/skills/local-code-review/local-code-review-checklist.md\n"
            "  issue #8946\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_reviewer.add_argument(
        "--author-model",
        required=True,
        help=(
            "Concrete seat/model id, or '<ambiguous-harness>:<concrete-model>' "
            "(e.g. 'cursor:claude-opus-5-5') to disambiguate a multi-model harness session."
        ),
    )
    p_reviewer.add_argument(
        "--author-family",
        default=None,
        help=(
            "Explicit, caller-asserted author model family (e.g. from session logs). "
            "Default: unset. Required to disambiguate a bare ambiguous-harness "
            "--author-model; optional corroboration otherwise — a mismatch is a "
            "fail-closed conflict. Example: anthropic"
        ),
    )
    p_reviewer.add_argument(
        "--review-profile",
        default="code",
        help="Review profile. Default: code. Example: code or infra. Content profiles fail closed.",
    )
    p_reviewer.add_argument(
        "--risk",
        default="medium",
        choices=sorted(VALID_RISKS),
        help="Risk ladder to walk. Default: medium. Example: high. One of low, medium, high, critical.",
    )
    p_reviewer.add_argument(
        "--domain",
        default="code",
        help="Domain carve-out checked against candidate exclusions. Default: code. Example: infra",
    )
    p_reviewer.add_argument(
        "--required-capability",
        action="append",
        help=(
            "Capability the reviewer must advertise (repeatable). Default: none. "
            "Example: --required-capability isolation"
        ),
    )
    p_reviewer.add_argument(
        "--data-egress-policy",
        help=(
            "Egress policy for fail-closed candidate gates. Default: unset, which excludes "
            "any candidate that requires a specific policy. Example: local_interactive"
        ),
    )
    p_reviewer.add_argument(
        "--isolation-required",
        action="store_true",
        help="Require a candidate that supports process isolation. Default: false.",
    )
    p_reviewer.add_argument(
        "--routing-snapshot-file",
        help=(
            "JSON file of route health (flat map or /api/state/routing-budget). "
            "Default: one bounded live snapshot; a file overrides it. Example: routing-snapshot.json"
        ),
    )
    p_reviewer.add_argument(
        "--subject-seat",
        action="append",
        default=None,
        help=(
            "Seat whose boundary this change governs (repeatable). Default: none. "
            "Matching reviewer candidates are excluded and the trace records why. "
            "Example: --subject-seat grok. Aliases such as grok-build and grok-4.7 "
            "normalize to the seat. Does not change the quality ladder."
        ),
    )
    p_reviewer.add_argument(
        "--subject-family",
        action="append",
        default=None,
        help=(
            "Model family whose seats this change governs (repeatable). Default: none. "
            "Every candidate of that family is excluded. Example: --subject-family xai. "
            "Unknown families fail closed."
        ),
    )
    p_reviewer.add_argument(
        "--owned-path",
        action="append",
        default=None,
        help=(
            "Repo path owned by the change (repeatable). Default: none, so nothing "
            "is inferred and selection is unchanged. Example: "
            "--owned-path scripts/agent_runtime/adapters/grok_build.py. "
            "An unambiguous per-seat adapter or reviewer hook infers that seat. "
            "An ambiguous path (shared acpx.py, base.py, guard-reviewer-publish.py) "
            "fails closed unless --subject-seat or --subject-family is also set."
        ),
    )
    p_reviewer.add_argument(
        "--repository",
        default=None,
        help=(
            "GitHub owner/name that author task records must name, for a committed target's "
            "complete authorship. Default: the target checkout's origin. Example: owner/repo"
        ),
    )
    p_reviewer.add_argument(
        "--task-root",
        default=None,
        help=(
            "Dispatch task-record directory (hot and archive/) that X-Agent task trailers resolve "
            "against. Default: batch_state/tasks of the target's primary checkout. Example: batch_state/tasks"
        ),
    )
    p_reviewer.add_argument(
        "--language-lane",
        action="store_true",
        help=(
            "Mark Ukrainian language, culture, or heritage work outside known paths. "
            "Default: false. Example: use for an off-tree Ukrainian culture change."
        ),
    )
    p_reviewer.add_argument(
        "--contested",
        action="store_true",
        help=(
            "Mark review as contested, admitting authority models for non-critical code/infra. "
            "Default: false."
        ),
    )
    p_reviewer.set_defaults(func=_cmd_resolve_reviewer)

    p_finding = sub.add_parser("finding", help="Record/adjudicate/apply/skip/report findings")
    finding_sub = p_finding.add_subparsers(dest="finding_action", required=True)
    fr = finding_sub.add_parser("raise")
    fr.add_argument("--id", required=True, help="Finding id. Example: F1")
    fr.add_argument("--summary", required=True, help="One-line finding summary. Example: governed seat can self-review")
    fr.add_argument("--source", required=True, help="Who raised it. Example: reviewer:gpt-6.1-sol")
    fa = finding_sub.add_parser("adjudicate")
    fa.add_argument("--id", required=True, help="Finding id to adjudicate. Example: F1")
    fa.add_argument(
        "--disposition",
        required=True,
        choices=["in_scope_blocker", "follow_up", "stop_and_escalate"],
        help="Disposition. Example: in_scope_blocker",
    )
    fa.add_argument("--rationale", required=True, help="Why this disposition. Example: real bug inside the frozen diff")
    fap = finding_sub.add_parser("apply")
    fap.add_argument("--id", required=True, help="Finding id already adjudicated in_scope_blocker. Example: F1")
    fs = finding_sub.add_parser("skip")
    fs.add_argument("--id", required=True, help="Finding id to skip. Example: F1")
    fs.add_argument("--rationale", required=True, help="Why it is skipped. Example: out of frozen scope")
    frep = finding_sub.add_parser("report")
    frep.add_argument("--id", required=False, default=None, help="unused, present for CLI symmetry")
    p_finding.set_defaults(func=_cmd_finding)

    p_behavior = sub.add_parser(
        "behavior-proof",
        help="Record or emit behavior proof bound to the frozen target",
    )
    behavior_sub = p_behavior.add_subparsers(dest="behavior_action", required=True)
    behavior_record = behavior_sub.add_parser("record", help="Record one source-aware or source-blind proof surface")
    behavior_record.add_argument(
        "--surface",
        required=True,
        choices=["source_aware", "source_blind"],
        help="Which proof surface to record. Example: source_blind",
    )
    behavior_record.add_argument(
        "--status",
        required=True,
        choices=["pass", "fail", "n/a"],
        help="Proof status. Example: pass. n/a requires --reason.",
    )
    command_or_step = behavior_record.add_mutually_exclusive_group()
    command_or_step.add_argument(
        "--command", help="Command that was run. Example: .venv/bin/python -m scripts.review.closeout_cli --help"
    )
    command_or_step.add_argument(
        "--step", help="Non-command step that was exercised. Example: clicked the submit control"
    )
    behavior_record.add_argument("--cwd", help="Working directory for --command. Example: .")
    result = behavior_record.add_mutually_exclusive_group()
    result.add_argument("--exit-code", type=int, help="Exit code of --command. Example: 0")
    result.add_argument("--result", help="Non-exit result when there is no exit code. Example: rendered")
    behavior_record.add_argument("--observation", help="What was observed. Example: help text listed --subject-seat")
    behavior_record.add_argument(
        "--evidence-ref", help="Durable pointer to the evidence. Example: test:closeout-cli-help"
    )
    behavior_record.add_argument("--reason", help="Why status is n/a or fail. Example: no runtime surface")
    behavior_record.add_argument(
        "--blind-enforced",
        action="store_true",
        help="Record that source-blind proof was isolation-enforced. Default: false.",
    )
    behavior_record.set_defaults(func=_cmd_behavior_proof)
    behavior_emit = behavior_sub.add_parser("emit", help="Print recorded proof JSON for verify_review")
    behavior_emit.set_defaults(func=_cmd_behavior_proof)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except CloseoutStateError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
