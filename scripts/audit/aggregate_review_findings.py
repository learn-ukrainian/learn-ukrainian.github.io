#!/usr/bin/env python3
"""Aggregate review findings across modules for a given level.

Scans review markdown files and structured YAML findings, groups by
dimension and severity, and outputs frequency counts.

Usage:
    .venv/bin/python scripts/aggregate_review_findings.py a1
    .venv/bin/python scripts/aggregate_review_findings.py a1 --severity minor
    .venv/bin/python scripts/aggregate_review_findings.py a1 --severity all
    .venv/bin/python scripts/aggregate_review_findings.py a1 --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import TypedDict

import yaml

CURRICULUM_ROOT = Path(__file__).resolve().parent.parent.parent / "curriculum" / "l2-uk-en"

# Canonical dimension names — normalize variants to these
DIMENSION_ALIASES: dict[str, str] = {
    "engagement": "ENGAGEMENT & TONE",
    "engagement & tone": "ENGAGEMENT & TONE",
    "dialogue": "DIALOGUE QUALITY",
    "dialogue quality": "DIALOGUE QUALITY",
    "exercise quality": "EXERCISE QUALITY",
    "exercise": "EXERCISE QUALITY",
    "plan adherence": "PLAN ADHERENCE",
    "pedagogical quality": "PEDAGOGICAL QUALITY",
    "pedagogical": "PEDAGOGICAL QUALITY",
    "linguistic accuracy": "LINGUISTIC ACCURACY",
    "linguistic": "LINGUISTIC ACCURACY",
    "vocabulary coverage": "VOCABULARY COVERAGE",
    "vocabulary": "VOCABULARY COVERAGE",
    "structural integrity": "STRUCTURAL INTEGRITY",
    "structural": "STRUCTURAL INTEGRITY",
    "cultural accuracy": "CULTURAL ACCURACY",
    "cultural": "CULTURAL ACCURACY",
    "enrich issues": "ENRICH ISSUES",
}

SEVERITY_ORDER = {"CRITICAL": 0, "MAJOR": 1, "MINOR": 2}


class Finding(TypedDict):
    module: str
    dimension: str
    severity: str
    location: str
    issue: str
    fix: str


def normalize_dimension(raw: str) -> str:
    """Normalize dimension name to canonical form.

    Handles numbered prefixes like "1. Plan adherence", "DIM 2: Linguistic accuracy",
    "DIMENSION 6: ENGAGEMENT", and slash-separated compound names.

    When the raw input is a bare placeholder like ``DIMENSION 2``
    (number only, no human-readable name) — produced by some real
    reviews — preserve the original uppercased form rather than
    returning an empty string. Downstream aggregation and dedup rely
    on a truthy dimension key; empty strings collapse unrelated
    findings into a single bucket.
    """
    original = raw.strip()
    key = original
    # Strip numbered prefixes: "1. ", "DIM 2: ", "DIMENSION 6: "
    key = re.sub(r"^(?:DIM(?:ENSION)?\s*\d+[:\s]*|\d+\.\s*)", "", key, flags=re.IGNORECASE)
    key = key.strip().lower()
    if not key:
        # Nothing left after the prefix strip — the raw was a bare
        # "DIMENSION N" / "1." placeholder. Fall back to the original
        # string (uppercased) so the finding still has a non-empty
        # grouping key.
        return original.upper() or "UNKNOWN"
    if key in DIMENSION_ALIASES:
        return DIMENSION_ALIASES[key]
    # Try matching each part of slash-separated names (e.g. "plan adherence / structural integrity")
    if "/" in key:
        parts = [p.strip() for p in key.split("/")]
        normalized = [DIMENSION_ALIASES.get(p, p.upper()) for p in parts]
        return " / ".join(normalized)
    return key.upper()


def normalize_severity(raw: str) -> str:
    """Normalize severity to uppercase."""
    return raw.strip().upper()


def parse_findings_from_markdown(text: str, module_slug: str) -> list[Finding]:
    """Extract findings from review markdown.

    Supports three formats seen in the codebase:
    1. Fenced code block:  ```\\n[DIM] [SEV]\\nLocation:...\\nIssue:...\\nFix:...\\n```
    2. Bold prefix:        **[DIM] [SEV]**\\nLocation:...\\nIssue:...\\nFix:...
    3. Bare:               [DIM] [SEV]\\nLocation:...\\nIssue:...\\nFix:...

    Also handles [SEVERITY: xxx] variant (e.g., [SEVERITY: minor]).
    """
    findings: list[Finding] = []

    # Extract only the Findings section to avoid false positives from scores table
    findings_section = _extract_findings_section(text)
    if not findings_section:
        return findings

    # Pattern 1: Fenced code blocks
    fenced = re.compile(
        r"```\s*\n"
        r"\[([^\]]+)\]\s*\[(?:SEVERITY:\s*)?(\w+)\]\s*\n"
        r"Location:\s*(.*?)\n"
        r"Issue:\s*(.*?)\n"
        r"Fix:\s*(.*?)\n"
        r"```",
        re.DOTALL,
    )
    for m in fenced.finditer(findings_section):
        findings.append(_make_finding(
            module_slug, m.group(1), m.group(2), m.group(3), m.group(4), m.group(5),
        ))

    # Remove fenced blocks so they don't double-match
    remaining = fenced.sub("", findings_section)

    # Pattern 2: Bold prefix  **[DIM] [SEV]**
    bold = re.compile(
        r"\*\*\[([^\]]+)\]\s*\[(?:SEVERITY:\s*)?(\w+)\]\*\*\s*\n"
        r"Location:\s*(.*?)\n"
        r"Issue:\s*(.*?)\n"
        r"Fix:\s*(.*?)(?:\n\n|\n(?=\*\*\[)|\n(?=##)|\Z)",
        re.DOTALL,
    )
    for m in bold.finditer(remaining):
        findings.append(_make_finding(
            module_slug, m.group(1), m.group(2), m.group(3), m.group(4), m.group(5),
        ))

    remaining = bold.sub("", remaining)

    # Pattern 3: Bare  [DIM] [SEV]  (at start of line)
    bare = re.compile(
        r"^\[([^\]]+)\]\s*\[(?:SEVERITY:\s*)?(\w+)\]\s*\n"
        r"Location:\s*(.*?)\n"
        r"Issue:\s*(.*?)\n"
        r"Fix:\s*(.*?)(?:\n\n|\n(?=\[)|\n(?=##)|\Z)",
        re.DOTALL | re.MULTILINE,
    )
    for m in bare.finditer(remaining):
        findings.append(_make_finding(
            module_slug, m.group(1), m.group(2), m.group(3), m.group(4), m.group(5),
        ))

    return findings


def _extract_findings_section(text: str) -> str | None:
    """Extract the ## Findings section from review markdown."""
    match = re.search(r"^## Findings\s*\n(.*?)(?=^## |\Z)", text, re.DOTALL | re.MULTILINE)
    if match:
        return match.group(1)
    return None


def _make_finding(
    module: str, dim: str, sev: str, loc: str, issue: str, fix: str,
) -> Finding:
    return Finding(
        module=module,
        dimension=normalize_dimension(dim),
        severity=normalize_severity(sev),
        location=loc.strip(),
        issue=issue.strip(),
        fix=fix.strip(),
    )


def parse_findings_from_yaml(path: Path, module_slug: str) -> list[Finding]:
    """Parse structured findings from YAML (produced by _save_structured_findings)."""
    try:
        data = yaml.safe_load(path.read_text("utf-8"))
    except Exception:
        return []

    if not isinstance(data, dict):
        return []

    findings: list[Finding] = []
    for f in data.get("findings", []):
        if not isinstance(f, dict):
            continue
        findings.append(Finding(
            module=module_slug,
            dimension=normalize_dimension(f.get("dimension", "UNKNOWN")),
            severity=normalize_severity(f.get("severity", "UNKNOWN")),
            location=f.get("location", ""),
            issue=f.get("issue", ""),
            fix=f.get("fix", ""),
        ))
    return findings


def collect_findings(level: str) -> list[Finding]:
    """Collect all findings for a level from review markdown and YAML files."""
    level_dir = CURRICULUM_ROOT / level
    findings: list[Finding] = []

    # 1. Review markdown files
    review_dir = level_dir / "review"
    if review_dir.is_dir():
        for path in sorted(review_dir.glob("*-review.md")):
            slug = path.stem.replace("-review", "")
            text = path.read_text("utf-8")
            findings.extend(parse_findings_from_markdown(text, slug))

    # 2. Structured YAML findings from orchestration
    orch_dir = level_dir / "orchestration"
    if orch_dir.is_dir():
        for yaml_path in sorted(orch_dir.glob("*/review-structured-r*.yaml")):
            slug = yaml_path.parent.name
            findings.extend(parse_findings_from_yaml(yaml_path, slug))

    # Deduplicate (same module + dimension + issue text)
    seen: set[tuple[str, str, str]] = set()
    deduped: list[Finding] = []
    for f in findings:
        key = (f["module"], f["dimension"], f["issue"][:80])
        if key not in seen:
            seen.add(key)
            deduped.append(f)

    return deduped


def format_report(
    level: str,
    findings: list[Finding],
    severity_filter: str | None = None,
) -> str:
    """Format findings into a human-readable report."""
    if severity_filter and severity_filter != "all":
        filtered = [f for f in findings if f["severity"] == severity_filter.upper()]
    else:
        filtered = findings

    # Count unique modules that have reviews (including those with zero findings)
    review_dir = CURRICULUM_ROOT / level / "review"
    module_count = len(list(review_dir.glob("*-review.md"))) if review_dir.is_dir() else 0

    lines: list[str] = []
    sev_label = f" ({severity_filter.upper()})" if severity_filter and severity_filter != "all" else ""
    lines.append(f"=== {level.upper()} Review Findings Aggregation{sev_label} ===")
    lines.append(f"{module_count} modules reviewed, {len(filtered)} findings total")
    lines.append("")

    if not filtered:
        lines.append("No findings match the filter.")
        return "\n".join(lines)

    # Group by dimension -> severity -> issue text
    by_dimension: dict[str, list[Finding]] = defaultdict(list)
    for f in filtered:
        by_dimension[f["dimension"]].append(f)

    # Sort dimensions by total count descending
    for dim in sorted(by_dimension, key=lambda d: -len(by_dimension[d])):
        dim_findings = by_dimension[dim]
        lines.append(f"{dim} ({len(dim_findings)} findings):")

        # Group by severity within dimension
        by_sev: dict[str, list[Finding]] = defaultdict(list)
        for f in dim_findings:
            by_sev[f["severity"]].append(f)

        for sev in sorted(by_sev, key=lambda s: SEVERITY_ORDER.get(s, 99)):
            sev_findings = by_sev[sev]
            lines.append(f"  {sev} ({len(sev_findings)}):")

            # Count issue patterns (first 80 chars as key)
            issue_counter: Counter[str] = Counter()
            for f in sev_findings:
                # Use first sentence or first 80 chars as grouping key
                issue_key = _normalize_issue_text(f["issue"])
                issue_counter[issue_key] += 1

            for issue_text, count in issue_counter.most_common():
                marker = f" x{count}" if count > 1 else ""
                lines.append(f'    - "{issue_text}"{marker}')

        lines.append("")

    return "\n".join(lines)


def _normalize_issue_text(text: str) -> str:
    """Shorten issue text for grouping — first sentence, max 100 chars."""
    # Take first sentence
    first = text.split(". ")[0].split(".\n")[0]
    if len(first) > 100:
        return first[:97] + "..."
    return first


def format_json(findings: list[Finding], severity_filter: str | None = None) -> str:
    """Format findings as JSON for programmatic consumption."""
    if severity_filter and severity_filter != "all":
        filtered = [f for f in findings if f["severity"] == severity_filter.upper()]
    else:
        filtered = findings
    return json.dumps(filtered, indent=2, ensure_ascii=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Aggregate review findings across modules for a level",
    )
    parser.add_argument("level", help="Level to scan (e.g., a1, a2, b1)")
    parser.add_argument(
        "--severity",
        default="all",
        help="Filter by severity: minor, major, critical, or all (default: all)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output as JSON instead of human-readable report",
    )
    args = parser.parse_args(argv)

    level = args.level.lower()
    level_dir = CURRICULUM_ROOT / level
    if not level_dir.is_dir():
        print(f"Error: level directory not found: {level_dir}", file=sys.stderr)
        return 1

    findings = collect_findings(level)

    if args.json_output:
        print(format_json(findings, args.severity))
    else:
        print(format_report(level, findings, args.severity))

    return 0


if __name__ == "__main__":
    sys.exit(main())
