"""Compare executed coverage identities, rather than aggregate percentages (#11226)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path, PurePosixPath

SOURCES = ("scripts", ".mcp", "agents_extensions", "packages")


def read_report(path: Path) -> dict:
    """Reject incomplete/non-branch reports instead of silently comparing empty sets."""
    manifest_path = path.with_name("manifest.json")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"{manifest_path}: expected a readable manifest with complete: true") from error
    if not isinstance(manifest, dict) or manifest.get("complete") is not True:
        raise ValueError(f"{manifest_path}: expected complete: true before comparing coverage")
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("meta", {}).get("branch_coverage") is not True or not report.get("files"):
        raise ValueError(f"{path}: expected a non-empty branch coverage JSON report")
    for name, data in report["files"].items():
        parts = PurePosixPath(name).parts
        if not parts or parts[0] not in SOURCES or ".." in parts:
            raise ValueError(f"{path}: expected repository-relative production path: {name}")
        lines = data["executed_lines"]
        arcs = data.get("executed_arcs", data["executed_branches"])
        if not isinstance(lines, list) or any(type(line) is not int or line < 1 for line in lines):
            raise ValueError(f"{path}: invalid executed_lines for {name}")
        if not isinstance(arcs, list) or any(
            not isinstance(arc, list) or len(arc) != 2 or any(type(line) is not int for line in arc) for arc in arcs
        ):
            raise ValueError(f"{path}: invalid executed arcs for {name}")
    return report


def lost_coverage(baseline: dict, candidate: dict) -> list[dict]:
    """A disappeared file loses every executed line and arc; gains never offset losses."""
    losses = []
    for name, before in sorted(baseline["files"].items()):
        after = candidate["files"].get(name, {})
        arc_key = "executed_arcs" if "executed_arcs" in before else "executed_branches"
        if after and ("executed_arcs" in before) != ("executed_arcs" in after):
            raise ValueError(f"{name}: cannot compare all arcs with branch-only arcs")
        lines = sorted(set(before["executed_lines"]) - set(after.get("executed_lines", [])))
        arcs = sorted(set(map(tuple, before[arc_key])) - set(map(tuple, after.get(arc_key, []))))
        if lines or arcs:
            losses.append(
                {"file": name, "lost_lines": lines, "lost_arcs": arcs, "line_count": len(lines), "arc_count": len(arcs)}
            )
    return losses


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "List production files with lost executed lines or arcs.\n"
            "Use for paired branch coverage reports from coverage-ref.yml; "
            "do not use percentages or reports from different source layouts."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/ci/coverage_diff.py baseline/coverage.json candidate/coverage.json\n"
            "Outputs: JSON to stdout with every lost identity and per-file counts; no files written.\n"
            "Exit codes: 0 = no loss; 1 = lost coverage; 2 = invalid input.\n"
            "Related: .github/workflows/coverage-ref.yml; #11226. "
            "Requires a sibling manifest.json with complete: true for both reports.\n"
            "Line/arc numbers are literal identities: source edits that move lines require review."
        ),
    )
    parser.add_argument("baseline", type=Path, help="Baseline branch JSON, e.g. main/coverage.json")
    parser.add_argument("candidate", type=Path, help="Candidate branch JSON, e.g. prune/coverage.json")
    args = parser.parse_args(argv)
    try:
        losses = lost_coverage(read_report(args.baseline), read_report(args.candidate))
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        print(f"coverage_diff: {error}", file=sys.stderr)
        return 2
    print(json.dumps({"files_with_losses": losses}, indent=2))
    return int(bool(losses))


if __name__ == "__main__":
    raise SystemExit(main())
