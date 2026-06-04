#!/usr/bin/env python3
"""Audit A2 readiness inputs before content generation.

Use this when preparing A2 for build fanout. It checks the source-of-truth
inputs, not generated lesson artifacts.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
A2_TRACK = "a2"
CURRICULUM_PATH = Path("curriculum/l2-uk-en/curriculum.yaml")
PLANS_DIR = Path("curriculum/l2-uk-en/plans/a2")
WIKI_DIR = Path("wiki/grammar/a2")
REVIEWS_DIR = Path("wiki/.reviews/grammar/a2")

REQUIRED_REVIEW_DIMENSIONS = (
    "Factual accuracy",
    "Ukrainian language quality",
    "Decolonization",
    "Completeness",
    "Actionable",
)

READINESS_FIELDS = ("grammar", "register", "persona")


@dataclass(frozen=True)
class Finding:
    check: str
    severity: str
    path: str
    message: str


@dataclass(frozen=True)
class AuditResult:
    root: str
    summary: dict[str, Any]
    findings: list[Finding]

    @property
    def failed(self) -> bool:
        return any(f.severity == "ERROR" for f in self.findings)


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _load_a2_slugs(root: Path) -> list[str]:
    data = _load_yaml(root / CURRICULUM_PATH)
    modules = data.get("levels", {}).get(A2_TRACK, {}).get("modules", [])
    return [m for m in modules if isinstance(m, str)]


def _plan_paths(root: Path) -> list[Path]:
    return sorted((root / PLANS_DIR).glob("*.yaml"))


def _wiki_paths(root: Path) -> list[Path]:
    return sorted((root / WIKI_DIR).glob("*.md"))


def _source_paths(root: Path) -> list[Path]:
    return sorted((root / WIKI_DIR).glob("*.sources.yaml"))


def _review_paths(root: Path) -> list[Path]:
    review_dir = root / REVIEWS_DIR
    if not review_dir.exists():
        return []
    return sorted(review_dir.glob("*.md"))


def _review_path(root: Path, slug: str) -> Path:
    return root / REVIEWS_DIR / f"{slug}-review-LOCKED.md"


def _expected_module_id(seq: int) -> str:
    return f"a2-{seq:03d}"


def _is_checkpoint_like(slug: str) -> bool:
    return any(token in slug for token in ("checkpoint", "review", "finale", "practice", "exam"))


def _activity_min_items(slug: str) -> int:
    return 10 if _is_checkpoint_like(slug) else 8


def _activity_type(hint: dict[str, Any]) -> str:
    raw = hint.get("type") or hint.get("kind") or hint.get("activity_type") or "<missing>"
    return str(raw)


def _verify_markers(text: str) -> list[tuple[int, str]]:
    pattern = re.compile(r"<!--\s*VERIFY\b.*?-->|(?<![A-Za-z])VERIFY\s*:", re.IGNORECASE | re.DOTALL)
    findings: list[tuple[int, str]] = []
    for match in pattern.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        marker = " ".join(match.group(0).split())[:160]
        findings.append((line, marker))
    return findings


def _check_inventory(root: Path, slugs: list[str], findings: list[Finding]) -> dict[str, int]:
    plan_files = _plan_paths(root)
    wiki_files = _wiki_paths(root)
    source_files = _source_paths(root)
    review_files = _review_paths(root)

    counts = {
        "manifest_modules": len(slugs),
        "plan_files": len(plan_files),
        "wiki_markdown_files": len(wiki_files),
        "wiki_source_sidecars": len(source_files),
        "review_files": len(review_files),
    }

    if len(plan_files) != len(slugs):
        findings.append(
            Finding(
                "inventory",
                "ERROR",
                _relative(root / PLANS_DIR, root),
                f"expected {len(slugs)} plan files, found {len(plan_files)}",
            )
        )
    if len(wiki_files) != len(slugs):
        findings.append(
            Finding(
                "inventory",
                "ERROR",
                _relative(root / WIKI_DIR, root),
                f"expected {len(slugs)} wiki markdown files, found {len(wiki_files)}",
            )
        )
    if len(source_files) != len(slugs):
        findings.append(
            Finding(
                "inventory",
                "ERROR",
                _relative(root / WIKI_DIR, root),
                f"expected {len(slugs)} wiki source sidecars, found {len(source_files)}",
            )
        )

    return counts


def _check_plan_ordering(root: Path, slugs: list[str], findings: list[Finding]) -> None:
    slug_to_seq = {slug: i for i, slug in enumerate(slugs, 1)}
    seen: set[str] = set()

    for path in _plan_paths(root):
        slug = path.stem
        seen.add(slug)
        rel = _relative(path, root)
        data = _load_yaml(path)
        if not isinstance(data, dict):
            findings.append(Finding("plan_ordering", "ERROR", rel, "plan root is not a mapping"))
            continue
        if slug not in slug_to_seq:
            findings.append(Finding("plan_ordering", "ERROR", rel, "plan is not listed in curriculum.yaml"))
            continue

        expected_seq = slug_to_seq[slug]
        expected_module = _expected_module_id(expected_seq)
        if data.get("slug") not in (None, slug):
            findings.append(Finding("plan_ordering", "ERROR", rel, f"slug={data.get('slug')!r}, expected {slug!r}"))
        if int(data.get("sequence", expected_seq)) != expected_seq:
            findings.append(
                Finding("plan_ordering", "ERROR", rel, f"sequence={data.get('sequence')!r}, expected {expected_seq}")
            )
        if str(data.get("module", expected_module)) != expected_module:
            findings.append(
                Finding("plan_ordering", "ERROR", rel, f"module={data.get('module')!r}, expected {expected_module!r}")
            )
        if data.get("level") not in (None, "A2", "a2"):
            findings.append(Finding("plan_ordering", "ERROR", rel, f"level={data.get('level')!r}, expected A2"))

    for slug in slugs:
        if slug not in seen:
            path = root / PLANS_DIR / f"{slug}.yaml"
            findings.append(Finding("plan_ordering", "ERROR", _relative(path, root), "missing plan file"))


def _check_plan_config(root: Path, findings: list[Finding]) -> None:
    for path in _plan_paths(root):
        rel = _relative(path, root)
        data = _load_yaml(path)
        if not isinstance(data, dict):
            continue

        slug = str(data.get("slug") or path.stem)
        expected_target = 1500 if _is_checkpoint_like(slug) else 2000
        target = data.get("word_target")
        if not isinstance(target, int):
            findings.append(Finding("plan_config", "ERROR", rel, "missing integer word_target"))
        elif target < expected_target:
            findings.append(
                Finding("plan_config", "ERROR", rel, f"word_target={target}, expected at least {expected_target}")
            )

        outline = data.get("content_outline")
        if not isinstance(outline, list) or not outline:
            findings.append(Finding("plan_config", "ERROR", rel, "missing content_outline"))
            continue
        outline_sum = sum(item.get("words", 0) for item in outline if isinstance(item, dict))
        if isinstance(target, int) and outline_sum < target * 0.95:
            findings.append(
                Finding("plan_config", "ERROR", rel, f"content_outline words={outline_sum}, under word_target={target}")
            )


def _check_activity_density(root: Path, findings: list[Finding]) -> int:
    count = 0
    for path in _plan_paths(root):
        rel = _relative(path, root)
        data = _load_yaml(path)
        if not isinstance(data, dict):
            continue
        slug = str(data.get("slug") or path.stem)
        min_items = _activity_min_items(slug)
        hints = data.get("activity_hints") or []
        if not isinstance(hints, list):
            findings.append(Finding("activity_density", "ERROR", rel, "activity_hints is not a list"))
            continue
        for index, hint in enumerate(hints, 1):
            if not isinstance(hint, dict):
                findings.append(Finding("activity_density", "ERROR", rel, f"activity_hints[{index}] is not a mapping"))
                count += 1
                continue
            items = hint.get("items")
            if not isinstance(items, int):
                findings.append(
                    Finding("activity_density", "ERROR", rel, f"activity_hints[{index}] missing integer items")
                )
                count += 1
            elif items < min_items:
                findings.append(
                    Finding(
                        "activity_density",
                        "ERROR",
                        rel,
                        f"activity_hints[{index}] {_activity_type(hint)} items={items}, expected at least {min_items}",
                    )
                )
                count += 1
    return count


def _check_readiness_fields(root: Path, findings: list[Finding]) -> dict[str, int]:
    missing_counts = {field: 0 for field in READINESS_FIELDS}
    for path in _plan_paths(root):
        rel = _relative(path, root)
        data = _load_yaml(path)
        if not isinstance(data, dict):
            continue
        for field in READINESS_FIELDS:
            if data.get(field) in (None, "", []):
                missing_counts[field] += 1
                findings.append(Finding("readiness_fields", "ERROR", rel, f"missing {field}"))
    return missing_counts


def _check_verify_markers(root: Path, findings: list[Finding]) -> int:
    count = 0
    for path in _wiki_paths(root):
        rel = _relative(path, root)
        for line, marker in _verify_markers(path.read_text(encoding="utf-8")):
            findings.append(Finding("wiki_verify", "ERROR", rel, f"line {line}: {marker}"))
            count += 1
    return count


def _check_reviews(root: Path, slugs: list[str], findings: list[Finding]) -> int:
    locked_count = 0
    for slug in slugs:
        path = _review_path(root, slug)
        rel = _relative(path, root)
        if not path.exists():
            findings.append(Finding("wiki_reviews", "ERROR", rel, "missing LOCKED review file"))
            continue
        text = path.read_text(encoding="utf-8")
        missing = [dimension for dimension in REQUIRED_REVIEW_DIMENSIONS if dimension not in text]
        if missing:
            findings.append(
                Finding("wiki_reviews", "ERROR", rel, "review missing dimensions: " + ", ".join(missing))
            )
            continue
        if "LOCKED" not in text:
            findings.append(Finding("wiki_reviews", "ERROR", rel, "review does not mark the slug LOCKED"))
            continue
        locked_count += 1
    return locked_count


def _check_plan_backups(root: Path, findings: list[Finding]) -> int:
    backup_paths = sorted((root / PLANS_DIR).glob("*.yaml.bak"))
    for path in backup_paths:
        findings.append(Finding("plan_backups", "ERROR", _relative(path, root), "tracked/source-tree plan backup file"))
    return len(backup_paths)


def audit(root: Path = PROJECT_ROOT) -> AuditResult:
    root = root.resolve()
    findings: list[Finding] = []
    slugs = _load_a2_slugs(root)

    summary: dict[str, Any] = {}
    summary.update(_check_inventory(root, slugs, findings))
    _check_plan_ordering(root, slugs, findings)
    _check_plan_config(root, findings)
    summary["activity_density_below_floor"] = _check_activity_density(root, findings)
    summary["missing_readiness_fields"] = _check_readiness_fields(root, findings)
    summary["verify_markers"] = _check_verify_markers(root, findings)
    summary["locked_reviews"] = _check_reviews(root, slugs, findings)
    summary["plan_backup_files"] = _check_plan_backups(root, findings)
    summary["errors"] = sum(1 for f in findings if f.severity == "ERROR")
    summary["warnings"] = sum(1 for f in findings if f.severity == "WARNING")

    return AuditResult(root=str(root), summary=summary, findings=findings)


def _print_text(result: AuditResult) -> None:
    summary = result.summary
    print("A2 readiness audit")
    print(f"Root: {result.root}")
    print(
        "Inventory: "
        f"{summary['manifest_modules']} manifest modules, "
        f"{summary['plan_files']} plans, "
        f"{summary['wiki_markdown_files']} wiki pages, "
        f"{summary['wiki_source_sidecars']} source sidecars, "
        f"{summary['review_files']} review files"
    )
    print(f"Activity hints below floor: {summary['activity_density_below_floor']}")
    print(f"VERIFY markers: {summary['verify_markers']}")
    print(f"LOCKED reviews: {summary['locked_reviews']}/{summary['manifest_modules']}")
    print(f"Plan backup files: {summary['plan_backup_files']}")
    missing = summary["missing_readiness_fields"]
    print(
        "Missing readiness fields: "
        + ", ".join(f"{field}={missing[field]}" for field in READINESS_FIELDS)
    )
    print(f"Findings: {summary['errors']} error(s), {summary['warnings']} warning(s)")

    for finding in result.findings:
        print(f"{finding.severity}: {finding.check}: {finding.path}: {finding.message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Audit A2 source inputs before content generation.\n"
            "Use this for A2 readiness tickets; do not use it for built lesson artifacts."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/validate/a2_readiness_audit.py\n"
            "  .venv/bin/python scripts/validate/a2_readiness_audit.py --json\n"
            "  .venv/bin/python scripts/validate/a2_readiness_audit.py --root /path/to/worktree\n\n"
            "Outputs: text or JSON summary of A2 plan/wiki/review readiness findings.\n"
            "Exit codes: 0 when A2 inputs are audit-clean; 1 when blockers remain.\n"
            "Related: issues #2551, #2554, #2555, #2556, #2557, #2558, #2559."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=PROJECT_ROOT,
        help="Repository root to audit. Default: current script's repository root.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text. Default: false.",
    )
    args = parser.parse_args(argv)

    result = audit(args.root)
    if args.json:
        print(
            json.dumps(
                {
                    "root": result.root,
                    "summary": result.summary,
                    "findings": [asdict(finding) for finding in result.findings],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        _print_text(result)
    return 1 if result.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
