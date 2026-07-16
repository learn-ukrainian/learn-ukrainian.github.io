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
    resolve_local_target,
    resolve_review_target,
)


def _load_state(state_file: Path) -> dict:
    if not state_file.exists():
        return {"target": None, "target_args": None, "baseline": None, "cycle_outstanding_counts": [], "findings": []}
    return json.loads(state_file.read_text(encoding="utf-8"))


def _save_state(state_file: Path, state: dict) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def _target_from_dict(data: dict) -> ReviewTarget:
    return ReviewTarget(
        mode=data["mode"],
        base_sha=data["base_sha"],
        head_sha=data["head_sha"],
        changed_paths=tuple(data["changed_paths"]),
        non_test_loc=data["non_test_loc"],
        clean_tree=data["clean_tree"],
        description=data["description"],
    )


def _ledger_from_state(state: dict) -> FindingsLedger:
    return FindingsLedger.from_events(FindingEvent(**raw) for raw in state.get("findings", []))


def _cmd_target(args: argparse.Namespace) -> int:
    state = _load_state(args.state_file)
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
    if not state.get("target"):
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
    data = state["baseline"]
    return ScopeBaseline(
        issue_ref=data["issue_ref"],
        intended_behavior=data["intended_behavior"],
        non_goals=data["non_goals"],
        owner_boundary=data["owner_boundary"],
        target=_target_from_dict(data["target"]),
        review_profile=data["review_profile"],
        risk=data["risk"],
        frozen_files=frozenset(data["frozen_files"]),
        frozen_non_test_loc=data["frozen_non_test_loc"],
    )


def _cmd_check_expansion(args: argparse.Namespace) -> int:
    state = _load_state(args.state_file)
    if not state.get("baseline"):
        print(json.dumps({"error": "no frozen baseline yet — run `freeze` first"}), file=sys.stderr)
        return 1
    baseline = _baseline_from_state(state)
    current = resolve_local_target(Path(args.repo_root).resolve())
    result = check_expansion_breaker(baseline, frozenset(current.changed_paths), current.non_test_loc)
    print(json.dumps({"triggered": result.triggered, "reason": result.reason}, indent=2))
    return 0


def _cmd_record_cycle(args: argparse.Namespace) -> int:
    state = _load_state(args.state_file)
    if not state.get("baseline"):
        print(json.dumps({"error": "no frozen baseline yet — run `freeze` first"}), file=sys.stderr)
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
    )
    resolution = resolve_reviewer(inputs)
    print(
        json.dumps(
            {
                "selected": asdict(resolution.selected) if resolution.selected else None,
                "advisory": [asdict(a) for a in resolution.advisory],
                "trace": [asdict(t) for t in resolution.trace],
                "substitution_note": resolution.substitution_note,
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
    p_expansion.set_defaults(func=_cmd_check_expansion)

    p_cycle = sub.add_parser("record-cycle", help="Record one review/fix cycle's outstanding-finding count")
    p_cycle.add_argument("--outstanding-count", required=True, type=int)
    p_cycle.set_defaults(func=_cmd_record_cycle)

    p_reviewer = sub.add_parser("resolve-reviewer", help="Resolve the cross-family reviewer for this author")
    p_reviewer.add_argument("--author-model", required=True)
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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
