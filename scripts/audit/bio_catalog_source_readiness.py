#!/usr/bin/env python3
"""Report deterministic BIO catalog-source structural readiness without writing artifacts.

This audit measures the checked-in catalog surfaces that precede module writing:
research dossiers, plans, reading packets, compiled wikis, and sibling source
registries. It deliberately does not infer manual evidence such as source
grounding, quote verification, image rights, or reading-rights dispositions.
Those remain separate promotion/release concerns.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from collections.abc import Mapping
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
# Direct execution otherwise places scripts/audit ahead of the repository root,
# causing ``scripts.audit`` to mistake its local config.py for scripts/config.py.
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) in sys.path:
    sys.path.remove(str(SCRIPT_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit import lint_bio_dossier_xref
from scripts.audit.wiki_completeness_gate import check_wiki_completeness
from scripts.build import linear_pipeline
from scripts.validate import check_wiki_subject, lint_seminar_quality
from scripts.wiki.domains import resolve_write_domain
from scripts.wiki.quality_gate import check_article
from scripts.wiki.sources_schema import load_sources_registry, validate_sources_registry

GATE_BLOCKERS = {
    "dossier": "DOSSIER_MISSING",
    "dossier_xref": "DOSSIER_XREF_FAIL",
    "plan": "PLAN_MISSING",
    "plan_check": "PLAN_CHECK_FAIL",
    "plan_language": "PLAN_LANGUAGE_HIGH",
    "readings": "READING_PACKET_MISSING",
    "wiki_pair": "WIKI_PAIR_MISSING",
    "wiki_quality": "WIKI_QUALITY_FAIL",
    "wiki_completeness": "WIKI_COMPLETENESS_FAIL",
    "wiki_subject": "WIKI_SUBJECT_FAIL",
    "wiki_language": "WIKI_LANGUAGE_HIGH",
    "source_registry": "SOURCE_REGISTRY_INVALID",
}
CATALOG_GATES = tuple(GATE_BLOCKERS)


class SourceRegistryValidationError(ValueError):
    """Raised when a sibling source registry is not a valid registry document."""


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(loader: yaml.SafeLoader, node: yaml.nodes.MappingNode, deep: bool = False):
    mapping: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise SourceRegistryValidationError(f"duplicate YAML key: {key!r}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _display_path(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _gate(
    passed: bool,
    *,
    root: Path,
    paths: list[Path],
    detail: str | None = None,
) -> dict[str, object]:
    report: dict[str, object] = {
        "status": "pass" if passed else "fail",
        "evidence_paths": [_display_path(root, path) for path in paths],
    }
    if detail:
        report["detail"] = detail
    return report


def manifest_inventory(root: Path, track: str = "bio") -> list[str]:
    """Return the unique manifest order for the requested catalog track."""
    manifest_path = root / "curriculum" / "l2-uk-en" / "curriculum.yaml"
    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    modules = raw.get("levels", {}).get(track, {}).get("modules", [])
    if not isinstance(modules, list) or not all(isinstance(slug, str) and slug for slug in modules):
        raise ValueError(f"manifest levels.{track}.modules must be a list of non-empty slugs")
    duplicates = sorted(slug for slug, count in Counter(modules).items() if count != 1)
    if duplicates:
        raise ValueError(f"manifest levels.{track}.modules contains duplicate slugs: {', '.join(duplicates)}")
    return modules


def resolved_wiki_paths(root: Path, track: str, slug: str) -> tuple[Path, Path]:
    """Resolve the shared wiki and source-registry pair for a manifest slug."""
    directory = root / "wiki" / resolve_write_domain(track, slug)
    wiki_path = directory / f"{slug}.md"
    return wiki_path, wiki_path.with_suffix(".sources.yaml")


def _has_readings(raw_plan: Mapping[str, object] | None) -> bool:
    readings = raw_plan.get("readings") if raw_plan else None
    return isinstance(readings, list) and bool(readings)


def _load_raw_plan(plan_path: Path) -> Mapping[str, object] | None:
    try:
        candidate = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    return candidate if isinstance(candidate, Mapping) else None


def _validate_source_registry(wiki_path: Path, source_path: Path) -> tuple[bool, str]:
    """Run strict parser/schema and citation-registry consistency checks.

    This confirms that the sibling registry is structurally usable and agrees
    with inline citations. It intentionally does not resolve source claims or
    assert that a quoted passage supports an article claim.
    """
    try:
        raw = yaml.load(source_path.read_text(encoding="utf-8"), Loader=_UniqueKeyLoader)
    except (OSError, yaml.YAMLError, SourceRegistryValidationError) as exc:
        return False, f"registry YAML is invalid: {exc}"
    if not isinstance(raw, Mapping):
        return False, "registry root must be a mapping"
    sources = raw.get("sources")
    if not isinstance(sources, list):
        return False, "registry sources must be a list"
    for index, source in enumerate(sources, start=1):
        if not isinstance(source, Mapping):
            return False, f"registry sources[{index}] must be a mapping"
        missing = [name for name in ("id", "file") if name not in source]
        if missing:
            return False, f"registry sources[{index}] missing required field(s): {', '.join(missing)}"

    try:
        registry = load_sources_registry(source_path)
        issues = validate_sources_registry(wiki_path.read_text(encoding="utf-8"), registry)
    except Exception as exc:  # Fail closed when the shared schema API rejects malformed input.
        return False, f"registry schema validation failed: {type(exc).__name__}: {exc}"
    if issues:
        return False, "; ".join(issues)
    return True, "source registry schema and inline citation consistency passed"


def _blocker_codes(gates: Mapping[str, Mapping[str, object]]) -> list[str]:
    return [code for name, code in GATE_BLOCKERS.items() if gates[name]["status"] != "pass"]


def build_catalog_readiness(*, root: Path = PROJECT_ROOT, track: str = "bio") -> dict[str, object]:
    """Build a read-only, deterministic catalog-source structural report."""
    track = track.lower()
    if track != "bio":
        raise ValueError("catalog-source readiness currently supports only the BIO track")

    slugs = manifest_inventory(root, track)
    curriculum = root / "curriculum" / "l2-uk-en"
    rows: list[dict[str, object]] = []

    for slug in slugs:
        dossier_path = root / "docs" / "research" / track / f"{slug}.md"
        plan_path = curriculum / "plans" / track / f"{slug}.yaml"
        wiki_path, source_path = resolved_wiki_paths(root, track, slug)
        gates: dict[str, dict[str, object]] = {
            "dossier": _gate(dossier_path.exists(), root=root, paths=[dossier_path]),
            "plan": _gate(plan_path.exists(), root=root, paths=[plan_path]),
            "wiki_pair": _gate(
                wiki_path.exists() and source_path.exists(),
                root=root,
                paths=[wiki_path, source_path],
            ),
        }

        if dossier_path.exists():
            try:
                findings = lint_bio_dossier_xref.lint_dossier(dossier_path)
                gates["dossier_xref"] = _gate(
                    not findings,
                    root=root,
                    paths=[dossier_path],
                    detail=f"{len(findings)} invalid Existing cross-track plan path(s)",
                )
            except Exception as exc:  # Fail closed rather than dropping a broken dossier gate.
                gates["dossier_xref"] = _gate(
                    False,
                    root=root,
                    paths=[dossier_path],
                    detail=f"dossier cross-reference validation failed: {type(exc).__name__}: {exc}",
                )
        else:
            gates["dossier_xref"] = _gate(False, root=root, paths=[dossier_path])

        raw_plan: Mapping[str, object] | None = None
        checked_plan: Mapping[str, object] | None = None
        if plan_path.exists():
            raw_plan = _load_raw_plan(plan_path)
            try:
                checked_plan = linear_pipeline.plan_check(plan_path)
                gates["plan_check"] = _gate(True, root=root, paths=[plan_path])
            except Exception as exc:  # The writer's plan validator is authoritative here.
                gates["plan_check"] = _gate(
                    False,
                    root=root,
                    paths=[plan_path],
                    detail=f"{type(exc).__name__}: {exc}",
                )
            try:
                high = [finding for finding in lint_seminar_quality.lint_plan(plan_path) if finding.severity == "high"]
                gates["plan_language"] = _gate(
                    not high,
                    root=root,
                    paths=[plan_path],
                    detail=f"{len(high)} high language finding(s)",
                )
            except Exception as exc:  # Fail closed when the shared linter cannot inspect the plan.
                gates["plan_language"] = _gate(
                    False,
                    root=root,
                    paths=[plan_path],
                    detail=f"plan language validation failed: {type(exc).__name__}: {exc}",
                )
            gates["readings"] = _gate(
                _has_readings(raw_plan),
                root=root,
                paths=[plan_path],
                detail="plan contains a non-empty readings list" if _has_readings(raw_plan) else "plan has no readings list",
            )
        else:
            for name in ("plan_check", "plan_language", "readings"):
                gates[name] = _gate(False, root=root, paths=[plan_path])

        if wiki_path.exists() and source_path.exists():
            try:
                quality_issues = check_article(wiki_path, track)
                gates["wiki_quality"] = _gate(
                    not quality_issues,
                    root=root,
                    paths=[wiki_path, source_path],
                    detail="; ".join(quality_issues) if quality_issues else "wiki quality gate passed",
                )
            except Exception as exc:  # Fail closed when the shared quality gate rejects the article.
                gates["wiki_quality"] = _gate(
                    False,
                    root=root,
                    paths=[wiki_path, source_path],
                    detail=f"wiki quality validation failed: {type(exc).__name__}: {exc}",
                )
            try:
                completeness = check_wiki_completeness(wiki_path, level=track, slug=slug)
                gates["wiki_completeness"] = _gate(
                    completeness["verdict"] == "PASS",
                    root=root,
                    paths=[wiki_path, source_path],
                    detail=str(completeness["diagnostic"]),
                )
            except Exception as exc:  # Fail closed when the shared completeness gate rejects the article.
                gates["wiki_completeness"] = _gate(
                    False,
                    root=root,
                    paths=[wiki_path, source_path],
                    detail=f"wiki completeness validation failed: {type(exc).__name__}: {exc}",
                )
            try:
                title = str(checked_plan.get("title", "")) if checked_plan else None
                finding = check_wiki_subject.check_wiki_file(wiki_path, plan_title=title)
                gates["wiki_subject"] = _gate(
                    finding is None,
                    root=root,
                    paths=[wiki_path, plan_path],
                    detail=finding.reason if finding else "wiki subject matches plan title",
                )
            except Exception as exc:  # Fail closed when the subject gate cannot inspect the article.
                gates["wiki_subject"] = _gate(
                    False,
                    root=root,
                    paths=[wiki_path, plan_path],
                    detail=f"wiki subject validation failed: {type(exc).__name__}: {exc}",
                )
            try:
                high = [finding for finding in lint_seminar_quality.lint_text(wiki_path) if finding.severity == "high"]
                gates["wiki_language"] = _gate(
                    not high,
                    root=root,
                    paths=[wiki_path],
                    detail=f"{len(high)} high language finding(s)",
                )
            except Exception as exc:  # Fail closed when the shared linter cannot inspect the article.
                gates["wiki_language"] = _gate(
                    False,
                    root=root,
                    paths=[wiki_path],
                    detail=f"wiki language validation failed: {type(exc).__name__}: {exc}",
                )
            registry_ok, registry_detail = _validate_source_registry(wiki_path, source_path)
            gates["source_registry"] = _gate(
                registry_ok,
                root=root,
                paths=[wiki_path, source_path],
                detail=registry_detail,
            )
        else:
            for name in ("wiki_quality", "wiki_completeness", "wiki_subject", "wiki_language", "source_registry"):
                gates[name] = _gate(False, root=root, paths=[wiki_path, source_path])

        structural_complete = all(gates[name]["status"] == "pass" for name in CATALOG_GATES)
        rows.append(
            {
                "slug": slug,
                "gates": gates,
                "catalog_source_structural_complete": structural_complete,
                "blocker_codes": _blocker_codes(gates),
            }
        )

    blocker_counts = Counter(code for row in rows for code in row["blocker_codes"])
    gate_pass_counts = {
        name: sum(row["gates"][name]["status"] == "pass" for row in rows) for name in CATALOG_GATES
    }
    structural_complete_rows = sum(row["catalog_source_structural_complete"] for row in rows)
    return {
        "summary": {
            "track": track,
            "manifest_rows": len(rows),
            "catalog_source_structural_complete_rows": structural_complete_rows,
            "catalog_source_structural_incomplete_rows": len(rows) - structural_complete_rows,
            "gate_pass_counts": gate_pass_counts,
            "blocker_counts": dict(sorted(blocker_counts.items())),
        },
        "rows": rows,
    }


def _print_summary(report: Mapping[str, object]) -> None:
    summary = report["summary"]
    print(
        f"{summary['track']} catalog-source readiness: "
        f"{summary['catalog_source_structural_complete_rows']}/{summary['manifest_rows']} structurally complete"
    )
    print("gate passes: " + json.dumps(summary["gate_pass_counts"], ensure_ascii=False, sort_keys=True))
    print("blockers: " + json.dumps(summary["blocker_counts"], ensure_ascii=False, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--track", default="bio", help="Catalog track (only bio is supported)")
    parser.add_argument("--format", choices=("summary", "json"), default="summary")
    args = parser.parse_args(argv)
    try:
        report = build_catalog_readiness(root=PROJECT_ROOT, track=args.track)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        parser.error(str(exc))
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        _print_summary(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
