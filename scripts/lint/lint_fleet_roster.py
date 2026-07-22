#!/usr/bin/env python3
"""Fail when marked fleet-roster Markdown tables drift from machine authorities.

Authorities (read-only):
  - scripts/config/model_catalog.yaml → orchestrator_seats
  - scripts/config/fleet_communications.yaml → endpoints[*].formal_review_eligible

Marked blocks are exact projections. This lint never rewrites prose or config.
Missing/malformed markers fail closed. See #5642 / Sol strengthen Δ1.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = PROJECT_ROOT / "scripts/config/model_catalog.yaml"
COMMS_PATH = PROJECT_ROOT / "scripts/config/fleet_communications.yaml"

# Source rules only (not deploy copies under .claude/.agent/.gemini).
DEFAULT_PROJECTION_PATHS = (
    PROJECT_ROOT / "agents_extensions/shared/rules/model-assignment.md",
    PROJECT_ROOT / "docs/runbooks/fleet-comms-open-gaps.md",
    PROJECT_ROOT / "docs/runbooks/epic-orchestrator-roster.md",
)

BEGIN_RE = re.compile(
    r"<!--\s*fleet-roster-projection:begin\s+(?P<kind>orchestrator_seats|formal_review_eligible)\s*-->"
)
END_RE = re.compile(
    r"<!--\s*fleet-roster-projection:end\s+(?P<kind>orchestrator_seats|formal_review_eligible)\s*-->"
)
# Any HTML comment that mentions the projection namespace must be an exact supported form.
ANY_PROJECTION_COMMENT_RE = re.compile(
    r"<!--\s*fleet-roster-projection:[^>]*-->",
    re.IGNORECASE,
)
SUPPORTED_MARKER_RE = re.compile(
    r"<!--\s*fleet-roster-projection:(?:begin|end)\s+"
    r"(?:orchestrator_seats|formal_review_eligible)\s*-->"
)

SEAT_FIELDS = ("model_id", "effort", "escalate_model_id", "escalate_effort")
SEAT_HEADER = ("seat", *SEAT_FIELDS)
ELIG_HEADER = ("endpoint", "formal_review_eligible")


@dataclass(frozen=True)
class LintIssue:
    path: str
    kind: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"path": self.path, "kind": self.kind, "message": self.message}


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be a mapping")
    return data


def load_orchestrator_seats(catalog_path: Path = CATALOG_PATH) -> dict[str, dict[str, str]]:
    catalog = _load_yaml(catalog_path)
    raw = catalog.get("orchestrator_seats")
    if not isinstance(raw, dict) or not raw:
        raise ValueError(f"{catalog_path}: orchestrator_seats missing or empty")
    seats: dict[str, dict[str, str]] = {}
    for seat, body in raw.items():
        if not isinstance(seat, str) or not isinstance(body, dict):
            raise ValueError(f"{catalog_path}: invalid orchestrator_seats entry {seat!r}")
        key = seat.strip()
        if not key:
            raise ValueError(f"{catalog_path}: empty orchestrator_seats key {seat!r}")
        if key in seats:
            raise ValueError(
                f"{catalog_path}: duplicate orchestrator_seats name after normalize: {key!r}"
            )
        row: dict[str, str] = {}
        for field in SEAT_FIELDS:
            value = body.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"{catalog_path}: orchestrator_seats.{seat}.{field} must be a non-empty string"
                )
            row[field] = value.strip()
        seats[key] = row
    return seats


def load_formal_review_eligible(comms_path: Path = COMMS_PATH) -> dict[str, bool]:
    comms = _load_yaml(comms_path)
    endpoints = comms.get("endpoints")
    if not isinstance(endpoints, list) or not endpoints:
        raise ValueError(f"{comms_path}: endpoints missing or empty")
    eligible: dict[str, bool] = {}
    for item in endpoints:
        if not isinstance(item, dict):
            raise ValueError(f"{comms_path}: endpoint entry must be a mapping")
        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"{comms_path}: endpoint name must be a non-empty string")
        if "formal_review_eligible" not in item:
            raise ValueError(f"{comms_path}: endpoint {name!r} missing formal_review_eligible")
        flag = item["formal_review_eligible"]
        if not isinstance(flag, bool):
            raise ValueError(
                f"{comms_path}: endpoint {name!r} formal_review_eligible must be a bool"
            )
        key = name.strip()
        if key in eligible:
            raise ValueError(f"{comms_path}: duplicate endpoint name {key!r}")
        eligible[key] = flag
    return eligible


def _split_row(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    cells = [c.strip() for c in stripped.strip("|").split("|")]
    return cells


def _is_separator_row(cells: list[str]) -> bool:
    if not cells:
        return False
    return all(re.fullmatch(r":?-{3,}:?", c.replace(" ", "")) is not None for c in cells)


def parse_markdown_table(block: str) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    """Parse a single GFM table from a projection block body."""
    lines = [ln for ln in block.splitlines() if ln.strip()]
    if len(lines) < 2:
        raise ValueError("table needs a header and separator row")
    header = _split_row(lines[0])
    if not header:
        raise ValueError("invalid table header")
    sep = _split_row(lines[1])
    if not sep or not _is_separator_row(sep) or len(sep) != len(header):
        raise ValueError(
            f"invalid table separator (need {len(header)} columns of ---, got {len(sep) if sep else 0})"
        )
    rows: list[dict[str, str]] = []
    for line in lines[2:]:
        cells = _split_row(line)
        if not cells:
            raise ValueError(f"invalid table row: {line!r}")
        if len(cells) != len(header):
            raise ValueError(
                f"column count mismatch: header={len(header)} row={len(cells)} ({line!r})"
            )
        if _is_separator_row(cells):
            continue
        rows.append({header[i]: cells[i] for i in range(len(header))})
    return tuple(header), rows


def assert_no_malformed_projection_markers(text: str) -> None:
    """Fail closed if any fleet-roster-projection HTML comment is not a supported marker."""
    for match in ANY_PROJECTION_COMMENT_RE.finditer(text):
        token = match.group(0)
        if SUPPORTED_MARKER_RE.fullmatch(token) is None:
            raise ValueError(f"malformed fleet-roster-projection marker: {token!r}")


def extract_projection_blocks(text: str, kind: str) -> list[str]:
    """Return body text of every matching begin/end marker pair for *kind*.

    Fail-closed on unmatched ends, unclosed begins, nesting, and kind mismatches.
    Markers for *other* kinds are ignored for this extraction (each kind is scanned
    independently by the caller). Callers must run
    ``assert_no_malformed_projection_markers`` first so typoed markers cannot hide.
    """
    # Collect only markers for this kind, in document order.
    events: list[tuple[int, str, re.Match[str]]] = []
    for m in BEGIN_RE.finditer(text):
        if m.group("kind") == kind:
            events.append((m.start(), "begin", m))
    for m in END_RE.finditer(text):
        if m.group("kind") == kind:
            events.append((m.start(), "end", m))
    events.sort(key=lambda item: item[0])

    bodies: list[str] = []
    open_begin: re.Match[str] | None = None
    for _pos, etype, match in events:
        if etype == "begin":
            if open_begin is not None:
                raise ValueError(f"nested fleet-roster-projection for {kind}")
            open_begin = match
            continue
        # end
        if open_begin is None:
            raise ValueError(f"unmatched fleet-roster-projection:end {kind}")
        bodies.append(text[open_begin.end() : match.start()])
        open_begin = None
    if open_begin is not None:
        raise ValueError(f"unclosed fleet-roster-projection:begin {kind}")
    return bodies


def parse_seat_projection(block: str) -> dict[str, dict[str, str]]:
    header, rows = parse_markdown_table(block)
    if header != SEAT_HEADER:
        raise ValueError(
            f"orchestrator_seats header must be {list(SEAT_HEADER)}, got {list(header)}"
        )
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        seat = row["seat"].strip().strip("*")
        if not seat:
            raise ValueError("empty seat name in orchestrator_seats projection")
        if seat in out:
            raise ValueError(f"duplicate seat {seat!r} in projection")
        out[seat] = {field: row[field].strip().strip("`") for field in SEAT_FIELDS}
    return out


def parse_eligible_projection(block: str) -> dict[str, bool]:
    header, rows = parse_markdown_table(block)
    if header != ELIG_HEADER:
        raise ValueError(
            f"formal_review_eligible header must be {list(ELIG_HEADER)}, got {list(header)}"
        )
    out: dict[str, bool] = {}
    for row in rows:
        name = row["endpoint"].strip().strip("*")
        if not name:
            raise ValueError("empty endpoint name in formal_review_eligible projection")
        if name in out:
            raise ValueError(f"duplicate endpoint {name!r} in projection")
        raw = row["formal_review_eligible"].strip().lower()
        if raw not in {"true", "false"}:
            raise ValueError(
                f"endpoint {name!r}: formal_review_eligible must be true|false, got {raw!r}"
            )
        out[name] = raw == "true"
    return out


def _diff_maps(
    expected: dict[str, Any], actual: dict[str, Any], *, key_label: str
) -> list[str]:
    messages: list[str] = []
    exp_keys = set(expected)
    act_keys = set(actual)
    missing = sorted(exp_keys - act_keys)
    extra = sorted(act_keys - exp_keys)
    if missing:
        messages.append(f"missing {key_label}(s): {', '.join(missing)}")
    if extra:
        messages.append(f"extra {key_label}(s): {', '.join(extra)}")
    for key in sorted(exp_keys & act_keys):
        if expected[key] != actual[key]:
            messages.append(
                f"{key_label} {key!r}: expected {expected[key]!r}, got {actual[key]!r}"
            )
    return messages


def check_file_projections(
    path: Path,
    *,
    seats: dict[str, dict[str, str]],
    eligible: dict[str, bool],
    rel: str | None = None,
) -> list[LintIssue]:
    label = rel or str(path)
    issues: list[LintIssue] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [LintIssue(label, "io", f"cannot read file: {exc}")]

    try:
        assert_no_malformed_projection_markers(text)
    except ValueError as exc:
        issues.append(LintIssue(label, "markers", f"malformed markers: {exc}"))
        return issues

    for kind, expected, parser in (
        ("orchestrator_seats", seats, parse_seat_projection),
        ("formal_review_eligible", eligible, parse_eligible_projection),
    ):
        try:
            bodies = extract_projection_blocks(text, kind)
        except ValueError as exc:
            issues.append(LintIssue(label, kind, f"malformed markers: {exc}"))
            continue
        if not bodies:
            issues.append(
                LintIssue(
                    label,
                    kind,
                    f"missing <!-- fleet-roster-projection:begin {kind} --> block",
                )
            )
            continue
        if len(bodies) > 1:
            issues.append(
                LintIssue(
                    label,
                    kind,
                    f"expected exactly one {kind} projection block, found {len(bodies)}",
                )
            )
            continue
        try:
            actual = parser(bodies[0])
        except ValueError as exc:
            issues.append(LintIssue(label, kind, f"malformed projection table: {exc}"))
            continue
        key_label = "seat" if kind == "orchestrator_seats" else "endpoint"
        for msg in _diff_maps(expected, actual, key_label=key_label):
            issues.append(LintIssue(label, kind, msg))
    return issues


def lint_fleet_roster(
    *,
    catalog_path: Path = CATALOG_PATH,
    comms_path: Path = COMMS_PATH,
    projection_paths: tuple[Path, ...] | list[Path] = DEFAULT_PROJECTION_PATHS,
    project_root: Path = PROJECT_ROOT,
) -> list[LintIssue]:
    issues: list[LintIssue] = []
    try:
        seats = load_orchestrator_seats(catalog_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return [LintIssue(str(catalog_path), "authority", f"orchestrator_seats: {exc}")]
    try:
        eligible = load_formal_review_eligible(comms_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return [LintIssue(str(comms_path), "authority", f"formal_review_eligible: {exc}")]

    # Hard acceptance pin from Sol/Fable: Codex is not a driver; remains CF-eligible.
    if "codex" in seats:
        issues.append(
            LintIssue(
                str(catalog_path),
                "orchestrator_seats",
                "codex must not be an orchestrator_seats driver (coding + formal CF only)",
            )
        )
    if eligible.get("codex") is not True:
        issues.append(
            LintIssue(
                str(comms_path),
                "formal_review_eligible",
                "codex must remain formal_review_eligible: true",
            )
        )

    for path in projection_paths:
        try:
            rel = str(path.resolve().relative_to(project_root.resolve()))
        except ValueError:
            rel = str(path)
        if not path.is_file():
            issues.append(LintIssue(rel, "io", "projection file missing"))
            continue
        issues.extend(
            check_file_projections(path, seats=seats, eligible=eligible, rel=rel)
        )
    return issues


def format_seat_table(seats: dict[str, dict[str, str]]) -> str:
    lines = [
        "| seat | model_id | effort | escalate_model_id | escalate_effort |",
        "| --- | --- | --- | --- | --- |",
    ]
    for seat in sorted(seats):
        row = seats[seat]
        lines.append(
            "| {seat} | {model_id} | {effort} | {escalate_model_id} | {escalate_effort} |".format(
                seat=seat, **row
            )
        )
    return "\n".join(lines)


def format_eligible_table(eligible: dict[str, bool]) -> str:
    lines = [
        "| endpoint | formal_review_eligible |",
        "| --- | --- |",
    ]
    for name in sorted(eligible):
        lines.append(f"| {name} | {str(eligible[name]).lower()} |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--catalog",
        type=Path,
        default=CATALOG_PATH,
        help="path to model_catalog.yaml",
    )
    parser.add_argument(
        "--comms",
        type=Path,
        default=COMMS_PATH,
        help="path to fleet_communications.yaml",
    )
    parser.add_argument(
        "--projection",
        type=Path,
        action="append",
        default=None,
        help="projection markdown path (repeatable; default: three SSOT docs)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON summary on stdout",
    )
    args = parser.parse_args(argv)

    projection_paths = (
        tuple(p.resolve() for p in args.projection)
        if args.projection
        else DEFAULT_PROJECTION_PATHS
    )
    issues = lint_fleet_roster(
        catalog_path=args.catalog.resolve(),
        comms_path=args.comms.resolve(),
        projection_paths=projection_paths,
    )
    payload = {
        "ok": not issues,
        "issue_count": len(issues),
        "issues": [i.as_dict() for i in issues],
    }
    if args.json:
        print(json.dumps(payload, sort_keys=True, indent=2))
    elif issues:
        print("Fleet roster lint failed:", file=sys.stderr)
        for issue in issues:
            print(f"  - [{issue.kind}] {issue.path}: {issue.message}", file=sys.stderr)
    else:
        print(
            f"Fleet roster OK ({len(projection_paths)} projection file(s); "
            "orchestrator_seats + formal_review_eligible exact match)"
        )
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
