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
import sys
from dataclasses import asdict
from pathlib import Path

from scripts.review.evidence import compute_target_input_fingerprint
from scripts.review.findings import FindingEvent, FindingsLedger, FindingsLedgerError
from scripts.review.reviewer_resolver import ResolverInputs, resolve_reviewer
from scripts.review.scope_baseline import (
    ScopeBaseline,
    check_cycle_convergence_breaker,
    check_expansion_breaker,
)
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
    if mode not in {"local", "commit", "branch", "pr"}:
        raise CloseoutStateError("target_mode_invalid")
    if not all(value is None or isinstance(value, str) for value in (base_sha, head_sha)):
        raise CloseoutStateError("target_sha_invalid")
    if not isinstance(changed_paths, list) or not all(
        isinstance(path, str) and path for path in changed_paths
    ):
        raise CloseoutStateError("target_changed_paths_invalid")
    if not isinstance(non_test_loc, int) or isinstance(non_test_loc, bool) or non_test_loc < 0:
        raise CloseoutStateError("target_non_test_loc_invalid")
    if not isinstance(clean_tree, bool):
        raise CloseoutStateError("target_clean_tree_invalid")
    if not isinstance(description, str) or not description.strip():
        raise CloseoutStateError("target_description_invalid")
    return ReviewTarget(
        mode=mode,
        base_sha=base_sha,
        head_sha=head_sha,
        changed_paths=tuple(changed_paths),
        non_test_loc=non_test_loc,
        clean_tree=clean_tree,
        description=description,
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
    state["target_args"] = {
        "repo_root": str(Path(args.repo_root).resolve()),
        "mode": args.mode,
        "commit": args.commit,
        "branch": args.branch,
        "base": args.base,
        "pr": args.pr,
    }
    _save_state(args.state_file, state)
    print(json.dumps(asdict(target), indent=2))
    return 0


def _cmd_freeze(args: argparse.Namespace) -> int:
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
    if not isinstance(frozen_files, list) or not all(
        isinstance(path, str) and path for path in frozen_files
    ):
        raise CloseoutStateError("baseline_frozen_files_invalid")
    if (
        not isinstance(frozen_non_test_loc, int)
        or isinstance(frozen_non_test_loc, bool)
        or frozen_non_test_loc < 0
    ):
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
    print(json.dumps({"triggered": result.triggered, "reason": result.reason, "history": state["cycle_outstanding_counts"]}, indent=2))
    return 0


def _cmd_resolve_reviewer(args: argparse.Namespace) -> int:
    routing_snapshot = None
    if args.routing_snapshot_file:
        routing_snapshot = json.loads(Path(args.routing_snapshot_file).read_text(encoding="utf-8"))
    inputs = ResolverInputs(
        author_model=args.author_model,
        review_profile=args.review_profile,
        risk=args.risk,
        domain=args.domain,
        required_capabilities=frozenset(args.required_capability or []),
        data_egress_policy=args.data_egress_policy,
        isolation_required=args.isolation_required,
        routing_snapshot=routing_snapshot,
        author_family=args.author_family,
    )
    resolution = resolve_reviewer(inputs)
    print(
        json.dumps(
            {
                "selected": asdict(resolution.selected) if resolution.selected else None,
                "advisory": [asdict(a) for a in resolution.advisory],
                "trace": [asdict(t) for t in resolution.trace],
                "substitution_note": resolution.substitution_note,
                "fail_closed_reason": resolution.fail_closed_reason,
            },
            indent=2,
        )
    )
    return 0


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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-file", required=True, type=Path)
    sub = parser.add_subparsers(dest="command", required=True)

    p_target = sub.add_parser("target", help="Resolve the review target (local/commit/branch/pr)")
    p_target.add_argument("--mode", required=True, choices=["local", "commit", "branch", "pr"])
    p_target.add_argument("--repo-root", default=".")
    p_target.add_argument("--commit")
    p_target.add_argument("--branch")
    p_target.add_argument("--base")
    p_target.add_argument("--pr", type=int)
    p_target.set_defaults(func=_cmd_target)

    p_freeze = sub.add_parser("freeze", help="Freeze the scope baseline from the resolved target")
    p_freeze.add_argument("--issue", required=True)
    p_freeze.add_argument("--intended-behavior", required=True)
    p_freeze.add_argument("--non-goals", required=True)
    p_freeze.add_argument("--owner-boundary", required=True)
    p_freeze.add_argument("--review-profile", default="code")
    p_freeze.add_argument("--risk", default="medium")
    p_freeze.set_defaults(func=_cmd_freeze)

    p_expansion = sub.add_parser("check-expansion", help="Check the 2x files/LOC scope-expansion breaker")
    p_expansion.add_argument("--repo-root", default=".")
    p_expansion.add_argument(
        "--current-head",
        default=None,
        help=(
            "Required for commit/branch/pr-mode targets: the explicit reviewed head "
            "(e.g. HEAD, or a specific SHA) to re-diff against the frozen base_sha "
            "after committed fixes. Ignored for mode=local, which re-resolves from "
            "the working tree instead."
        ),
    )
    p_expansion.set_defaults(func=_cmd_check_expansion)

    p_cycle = sub.add_parser("record-cycle", help="Record one review/fix cycle's outstanding-finding count")
    p_cycle.add_argument("--outstanding-count", required=True, type=int)
    p_cycle.set_defaults(func=_cmd_record_cycle)

    p_reviewer = sub.add_parser("resolve-reviewer", help="Resolve the cross-family reviewer for this author")
    p_reviewer.add_argument(
        "--author-model",
        required=True,
        help=(
            "Concrete seat/model id, or '<ambiguous-harness>:<concrete-model>' "
            "(e.g. 'cursor:gpt-5.6-sol') to disambiguate a multi-model harness session."
        ),
    )
    p_reviewer.add_argument(
        "--author-family",
        default=None,
        help=(
            "Explicit, caller-asserted author model family (e.g. from session logs). "
            "Required to disambiguate a bare ambiguous-harness --author-model; optional "
            "corroboration otherwise — a mismatch is a fail-closed conflict."
        ),
    )
    p_reviewer.add_argument("--review-profile", default="code")
    p_reviewer.add_argument("--risk", default="medium")
    p_reviewer.add_argument("--domain", default="code")
    p_reviewer.add_argument("--required-capability", action="append")
    p_reviewer.add_argument("--data-egress-policy")
    p_reviewer.add_argument("--isolation-required", action="store_true")
    p_reviewer.add_argument("--routing-snapshot-file")
    p_reviewer.set_defaults(func=_cmd_resolve_reviewer)

    p_finding = sub.add_parser("finding", help="Record/adjudicate/apply/skip/report findings")
    finding_sub = p_finding.add_subparsers(dest="finding_action", required=True)
    fr = finding_sub.add_parser("raise")
    fr.add_argument("--id", required=True)
    fr.add_argument("--summary", required=True)
    fr.add_argument("--source", required=True)
    fa = finding_sub.add_parser("adjudicate")
    fa.add_argument("--id", required=True)
    fa.add_argument("--disposition", required=True, choices=["in_scope_blocker", "follow_up", "stop_and_escalate"])
    fa.add_argument("--rationale", required=True)
    fap = finding_sub.add_parser("apply")
    fap.add_argument("--id", required=True)
    fs = finding_sub.add_parser("skip")
    fs.add_argument("--id", required=True)
    fs.add_argument("--rationale", required=True)
    frep = finding_sub.add_parser("report")
    frep.add_argument("--id", required=False, default=None, help="unused, present for CLI symmetry")
    p_finding.set_defaults(func=_cmd_finding)

    p_behavior = sub.add_parser(
        "behavior-proof",
        help="Record or emit behavior proof bound to the frozen target",
    )
    behavior_sub = p_behavior.add_subparsers(dest="behavior_action", required=True)
    behavior_record = behavior_sub.add_parser("record", help="Record one source-aware or source-blind proof surface")
    behavior_record.add_argument("--surface", required=True, choices=["source_aware", "source_blind"])
    behavior_record.add_argument("--status", required=True, choices=["pass", "fail", "n/a"])
    command_or_step = behavior_record.add_mutually_exclusive_group()
    command_or_step.add_argument("--command")
    command_or_step.add_argument("--step")
    behavior_record.add_argument("--cwd")
    result = behavior_record.add_mutually_exclusive_group()
    result.add_argument("--exit-code", type=int)
    result.add_argument("--result")
    behavior_record.add_argument("--observation")
    behavior_record.add_argument("--evidence-ref")
    behavior_record.add_argument("--reason")
    behavior_record.add_argument("--blind-enforced", action="store_true")
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
