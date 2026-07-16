#!/usr/bin/env python3
"""Strict structured code-review verifier and receipt runner (issue #5284).

Canonical reviewer output is versioned JSON (``code-review-findings.v1``).
Legacy ``FINDING:`` text is rejected. Verification binds to an exact
local/commit/branch/PR target from ``scripts.review.target_resolution``.

Exit codes (stable):
  0 clean valid review
  1 valid review with actionable findings / incorrect overall
  2 invalid (schema, non-JSON, legacy text, malformed)
  3 incomplete
  4 stale (head / input hash)
  5 unverifiable (quote/line/scope evidence failure)

GitHub posting is opt-in (``--post-comment``). Receipts go to stdout and/or
``--receipt-path`` — never to status/, audit/*-review.md, review/*-review.md,
or telemetry paths.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Allow ``.venv/bin/python scripts/verify_review.py`` as well as ``-m``.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.review.review_contract import (
    EXIT_INVALID,
    AgentIdentity,
    VerifyContext,
    sha256_text,
    verify_review,
)
from scripts.review.target_resolution import (
    TargetResolutionError,
    resolve_review_target,
)

FORBIDDEN_RECEIPT_MARKERS = (
    "/status/",
    "/audit/",
    "-review.md",
    "/telemetry/",
    "data/telemetry",
)


def _run(cmd: list[str], input_text: str | None = None) -> str:
    return subprocess.run(
        cmd, check=True, capture_output=True, text=True, input=input_text
    ).stdout


def _read_review(issue: int | None, from_stdin: bool, review_file: Path | None) -> str:
    if from_stdin:
        return sys.stdin.read()
    if review_file is not None:
        return review_file.read_text(encoding="utf-8")
    if issue is None:
        raise SystemExit("one of --from-stdin, --review-file, or --issue is required")
    data = json.loads(_run(["gh", "issue", "view", str(issue), "--json", "comments"]))
    comments = data.get("comments") or []
    return comments[-1]["body"] if comments else ""


def _load_json_arg(raw: str | None, *, label: str) -> dict:
    if not raw:
        return {}
    path = Path(raw)
    text = path.read_text(encoding="utf-8") if path.is_file() else raw
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON for {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"{label} must be a JSON object")
    return value


def _receipt_path_allowed(path: Path) -> bool:
    posix = path.as_posix()
    lowered = posix.lower()
    if any(marker in lowered for marker in FORBIDDEN_RECEIPT_MARKERS):
        return False
    # Explicit denylist for repo artifact layouts.
    parts = path.parts
    if "status" in parts and path.suffix == ".json":
        return False
    if "audit" in parts and path.name.endswith("-review.md"):
        return False
    if "review" in parts and path.name.endswith("-review.md"):
        return False
    return "telemetry" not in parts


def _post_summary(issue: int, receipt: dict) -> None:
    counts: dict[str, int] = {}
    for item in receipt.get("findings") or []:
        outcome = str(item.get("outcome") or "unknown")
        counts[outcome] = counts.get(outcome, 0) + 1
    lines = [
        f"verify_review receipt for #{issue}:",
        f"- disposition: {receipt.get('final_disposition')}",
        f"- exit_code: {receipt.get('exit_code')}",
        f"- input_sha256: {(receipt.get('target') or {}).get('input_sha256')}",
    ]
    for name in (
        "verified",
        "line_mismatch",
        "quote_missing",
        "malformed",
        "out_of_scope",
    ):
        lines.append(f"- {name}: {counts.get(name, 0)}")
    _run(["gh", "issue", "comment", str(issue), "--body", "\n".join(lines)])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify structured code-review JSON against an exact target."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--issue", type=int, help="Read latest issue comment as review JSON")
    source.add_argument("--from-stdin", action="store_true", help="Read review JSON from stdin")
    source.add_argument(
        "--review-file",
        type=Path,
        help="Read review JSON from a local file",
    )

    parser.add_argument(
        "--mode",
        choices=["local", "commit", "branch", "pr"],
        default="local",
        help="Exact review target mode (default: local)",
    )
    parser.add_argument("--repo-root", default=".", help="Repository root for the target")
    parser.add_argument("--commit", help="Commit SHA/ref for mode=commit")
    parser.add_argument("--branch", help="Branch ref for mode=branch")
    parser.add_argument("--base", help="Base ref for mode=branch")
    parser.add_argument("--pr", type=int, dest="pr_number", help="PR number for mode=pr")

    parser.add_argument(
        "--expected-head",
        help="Fail EXIT_STALE if target head SHA differs from this value",
    )
    parser.add_argument(
        "--expected-input-sha256",
        help="Fail EXIT_STALE if review input SHA-256 differs",
    )

    parser.add_argument("--issue-ref", default="", help="Originating issue/request id for receipt")
    parser.add_argument(
        "--scope-json",
        default="",
        help="Frozen scope JSON object or path (runner-supplied)",
    )

    parser.add_argument("--author-model", default="unknown")
    parser.add_argument("--author-family", default="unknown")
    parser.add_argument("--author-harness", default="unknown")
    parser.add_argument("--author-selection-reason", default="not_provided")
    parser.add_argument("--reviewer-model", default="unknown")
    parser.add_argument("--reviewer-family", default="unknown")
    parser.add_argument("--reviewer-harness", default="unknown")
    parser.add_argument("--reviewer-selection-reason", default="not_provided")

    parser.add_argument(
        "--tests-json",
        default="",
        help="JSON object describing tests run (runner-supplied)",
    )
    parser.add_argument(
        "--behavior-proof-json",
        default="",
        help="JSON object with source_aware / source_blind proof fields",
    )
    parser.add_argument(
        "--dispositions-json",
        default="",
        help='JSON object mapping finding id → {"disposition","rationale"}',
    )
    parser.add_argument(
        "--routing-lineage-json",
        default="",
        help="JSON object recording implementation/routing provenance",
    )

    parser.add_argument(
        "--receipt-path",
        type=Path,
        help="Write full receipt JSON to this local path (must not be a forbidden artifact path)",
    )
    parser.add_argument(
        "--print-findings",
        action="store_true",
        help="Also print per-finding validation JSONL before the receipt",
    )
    parser.add_argument(
        "--post-comment",
        action="store_true",
        help="Opt-in: post a short summary comment on --issue (not the only durable path)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.post_comment and args.issue is None:
        parser.error("--post-comment requires --issue")

    repo_root = Path(args.repo_root).resolve()
    try:
        target = resolve_review_target(
            args.mode,
            repo_root,
            commit=args.commit,
            branch=args.branch,
            base=args.base,
            pr_number=args.pr_number,
        )
    except TargetResolutionError as exc:
        err = {"error": str(exc), "final_disposition": "invalid", "exit_code": EXIT_INVALID}
        print(json.dumps(err, ensure_ascii=False), file=sys.stderr)
        return EXIT_INVALID

    try:
        raw = _read_review(args.issue, args.from_stdin, args.review_file)
    except Exception as exc:
        print(json.dumps({"error": f"read_review_failed:{exc}"}, ensure_ascii=False), file=sys.stderr)
        return EXIT_INVALID

    issue_ref = args.issue_ref or (f"#{args.issue}" if args.issue else "unspecified")
    scope = _load_json_arg(args.scope_json or None, label="--scope-json")
    tests = _load_json_arg(args.tests_json or None, label="--tests-json")
    behavior_proof = _load_json_arg(
        args.behavior_proof_json or None, label="--behavior-proof-json"
    )
    dispositions = _load_json_arg(
        args.dispositions_json or None, label="--dispositions-json"
    )
    routing_lineage = _load_json_arg(
        args.routing_lineage_json or None, label="--routing-lineage-json"
    )

    ctx = VerifyContext(
        issue_ref=issue_ref,
        scope=scope,
        author=AgentIdentity(
            model=args.author_model,
            family=args.author_family,
            harness=args.author_harness,
            selection_reason=args.author_selection_reason,
        ),
        reviewer=AgentIdentity(
            model=args.reviewer_model,
            family=args.reviewer_family,
            harness=args.reviewer_harness,
            selection_reason=args.reviewer_selection_reason,
        ),
        target=target,
        repo_root=repo_root,
        input_sha256=sha256_text(raw),
        expected_head=args.expected_head,
        expected_input_sha256=args.expected_input_sha256,
        tests=tests,
        behavior_proof=behavior_proof,
        dispositions={
            str(k): v if isinstance(v, dict) else {"disposition": str(v)}
            for k, v in dispositions.items()
        },
        routing_lineage={str(k): str(v) for k, v in routing_lineage.items()},
    )

    result = verify_review(raw, ctx)

    if args.print_findings:
        for item in result.validations:
            print(json.dumps(item.to_dict(), ensure_ascii=False))

    receipt_json = json.dumps(result.receipt, ensure_ascii=False, indent=2, sort_keys=True)
    print(receipt_json)

    if args.receipt_path is not None:
        if not _receipt_path_allowed(args.receipt_path):
            print(
                json.dumps(
                    {
                        "error": (
                            "receipt_path_forbidden: do not write receipts under "
                            "status/, audit/*-review.md, review/*-review.md, or telemetry/"
                        )
                    },
                    ensure_ascii=False,
                ),
                file=sys.stderr,
            )
            return EXIT_INVALID
        args.receipt_path.parent.mkdir(parents=True, exist_ok=True)
        args.receipt_path.write_text(receipt_json + "\n", encoding="utf-8")

    if args.post_comment:
        _post_summary(args.issue, result.receipt)

    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
