#!/usr/bin/env python3
"""Audit module quality-gate coverage across planned curriculum modules.

This is the cheap, deterministic pass to run before spending reviewer tokens.
It scans built module artifacts for surface-policy failures and reports whether
each built module has a current persisted LLM quality-gate result.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
AUDIT_DIR = Path(__file__).resolve().parent
if str(AUDIT_DIR) not in sys.path:
    sys.path.insert(0, str(AUDIT_DIR))

from content_surface_gates import scan_module_surface
from llm_qg_canaries import evaluate_canaries
from llm_qg_store import (
    current_llm_qg_for_module,
    latest_llm_qg,
    llm_qg_file_is_current_for_module,
)

from scripts.api.config import CURRICULUM_ROOT, LEVELS, SEMINAR_TRACK_IDS

_YAML_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
_CURRENT_LLM_STATUSES = {"current_db", "current_file_only"}


@dataclass(frozen=True, slots=True)
class PlannedModule:
    """One module from the curriculum manifest or plan fallback."""

    num: int
    level: str
    slug: str
    profile: str


@dataclass(frozen=True, slots=True)
class ModuleQualityAudit:
    """Quality-gate coverage for one planned module."""

    num: int
    level: str
    slug: str
    profile: str
    built: bool
    module_dir: str | None
    surface_verdict: str
    surface_counts: dict[str, int]
    surface_findings: list[dict[str, Any]]
    llm_qg_status: str
    llm_qg_source: str | None
    llm_qg_run_id: str | None
    llm_qg_gate_version: str | None
    llm_qg_prompt_hash: str | None
    llm_qg_content_sha: str | None
    llm_qg_reviewer_family: str | None
    llm_qg_reviewer_model: str | None
    needs_llm_qg: bool
    needs_db_persistence: bool
    second_review_recommended: bool
    second_review_reason: str | None


def planned_modules(
    *,
    curriculum_root: Path = CURRICULUM_ROOT,
    level_ids: list[str] | None = None,
) -> list[PlannedModule]:
    """Return planned modules for selected levels/tracks."""
    levels = _selected_level_ids(level_ids)
    manifest = _load_manifest(curriculum_root / "curriculum.yaml")
    modules: list[PlannedModule] = []

    for level in levels:
        slugs = _manifest_slugs(manifest, level)
        if not slugs:
            slugs = _plan_dir_slugs(curriculum_root / "plans" / level)
        profile = profile_for_level(level)
        modules.extend(
            PlannedModule(num=index, level=level, slug=slug, profile=profile)
            for index, slug in enumerate(slugs, 1)
        )
    return modules


def audit_modules(
    *,
    curriculum_root: Path = CURRICULUM_ROOT,
    level_ids: list[str] | None = None,
    db_path: Path | None = None,
    include_findings: bool = True,
    canary_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Audit planned modules and return a JSON-serializable report."""
    rows = [
        audit_one_module(
            module,
            curriculum_root=curriculum_root,
            db_path=db_path,
            include_findings=include_findings,
        )
        for module in planned_modules(curriculum_root=curriculum_root, level_ids=level_ids)
    ]
    row_dicts = [asdict(row) for row in rows]
    return {
        "summary": summarize(row_dicts),
        "canaries": canary_results or {},
        "modules": row_dicts,
    }


def audit_one_module(
    module: PlannedModule,
    *,
    curriculum_root: Path = CURRICULUM_ROOT,
    db_path: Path | None = None,
    include_findings: bool = True,
) -> ModuleQualityAudit:
    """Audit one planned module."""
    module_dir = curriculum_root / module.level / module.slug
    built = (module_dir / "module.md").exists()
    if not built:
        return ModuleQualityAudit(
            num=module.num,
            level=module.level,
            slug=module.slug,
            profile=module.profile,
            built=False,
            module_dir=None,
            surface_verdict="NOT_BUILT",
            surface_counts={"critical": 0, "warning": 0, "total": 0},
            surface_findings=[],
            llm_qg_status="not_built",
            llm_qg_source=None,
            llm_qg_run_id=None,
            llm_qg_gate_version=None,
            llm_qg_prompt_hash=None,
            llm_qg_content_sha=None,
            llm_qg_reviewer_family=None,
            llm_qg_reviewer_model=None,
            needs_llm_qg=False,
            needs_db_persistence=False,
            second_review_recommended=False,
            second_review_reason=None,
        )

    surface = scan_module_surface(module_dir, level=module.level)
    llm_status = llm_qg_status_for_module(
        level=module.level,
        slug=module.slug,
        module_dir=module_dir,
        db_path=db_path,
    )
    second_review_reason = second_review_reason_for_module(
        profile=module.profile,
        surface_verdict=str(surface["verdict"]),
        llm_qg_status=str(llm_status["status"]),
    )
    return ModuleQualityAudit(
        num=module.num,
        level=module.level,
        slug=module.slug,
        profile=module.profile,
        built=True,
        module_dir=str(module_dir),
        surface_verdict=str(surface["verdict"]),
        surface_counts=dict(surface["counts"]),
        surface_findings=list(surface["findings"]) if include_findings else [],
        llm_qg_status=str(llm_status["status"]),
        llm_qg_source=llm_status["source"],
        llm_qg_run_id=llm_status["run_id"],
        llm_qg_gate_version=llm_status["gate_version"],
        llm_qg_prompt_hash=llm_status["prompt_hash"],
        llm_qg_content_sha=llm_status["content_sha"],
        llm_qg_reviewer_family=llm_status["reviewer_family"],
        llm_qg_reviewer_model=llm_status["reviewer_model"],
        needs_llm_qg=llm_status["status"] not in _CURRENT_LLM_STATUSES,
        needs_db_persistence=llm_status["status"] != "current_db",
        second_review_recommended=second_review_reason is not None,
        second_review_reason=second_review_reason,
    )


def llm_qg_status_for_module(
    *,
    level: str,
    slug: str,
    module_dir: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    """Return LLM-QG persistence status and reviewer metadata."""
    current = current_llm_qg_for_module(level, slug, module_dir, path=db_path)
    if current is not None:
        return _record_status("current_db", current)

    latest = latest_llm_qg(level, slug, path=db_path)
    file_path = module_dir / "llm_qg.json"
    file_exists = file_path.exists()
    if file_exists and llm_qg_file_is_current_for_module(module_dir, file_path):
        return _empty_status("current_file_only", source="llm_qg.json")
    if latest is not None:
        return _record_status("stale_db", latest)
    if file_exists:
        return _empty_status("stale_file", source="llm_qg.json")
    return _empty_status("missing")


def _record_status(status: str, record: Any) -> dict[str, Any]:
    return {
        "status": status,
        "source": record.source,
        "run_id": record.run_id,
        "gate_version": record.gate_version,
        "prompt_hash": record.prompt_hash,
        "content_sha": record.content_sha,
        "reviewer_family": record.reviewer_family,
        "reviewer_model": record.reviewer_model,
    }


def _empty_status(status: str, *, source: str | None = None) -> dict[str, Any]:
    return {
        "status": status,
        "source": source,
        "run_id": None,
        "gate_version": None,
        "prompt_hash": None,
        "content_sha": None,
        "reviewer_family": None,
        "reviewer_model": None,
    }


def second_review_reason_for_module(
    *,
    profile: str,
    surface_verdict: str,
    llm_qg_status: str,
) -> str | None:
    """Return why a module should receive a second cross-family review."""
    if profile == "seminar":
        return "seminar_high_risk"
    if surface_verdict in {"FAIL", "WARN"}:
        return f"surface_{surface_verdict.lower()}"
    if llm_qg_status not in _CURRENT_LLM_STATUSES:
        return "missing_or_stale_llm_qg"
    return None


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize per-module audit rows."""
    planned = len(rows)
    built_rows = [row for row in rows if row["built"]]
    built = len(built_rows)
    surface_fail = [row for row in built_rows if row["surface_verdict"] == "FAIL"]
    surface_warn = [row for row in built_rows if row["surface_verdict"] == "WARN"]
    current_db = [row for row in built_rows if row["llm_qg_status"] == "current_db"]
    current_file = [row for row in built_rows if row["llm_qg_status"] == "current_file_only"]
    stale = [row for row in built_rows if row["llm_qg_status"] in {"stale_db", "stale_file"}]
    missing = [row for row in built_rows if row["llm_qg_status"] == "missing"]
    return {
        "planned_modules": planned,
        "built_modules": built,
        "unbuilt_modules": planned - built,
        "surface_fail_modules": len(surface_fail),
        "surface_warn_modules": len(surface_warn),
        "current_db_llm_qg_modules": len(current_db),
        "current_file_only_llm_qg_modules": len(current_file),
        "stale_llm_qg_modules": len(stale),
        "missing_llm_qg_modules": len(missing),
        "modules_without_current_db_llm_qg": built - len(current_db),
        "modules_without_current_any_llm_qg": built - len(current_db) - len(current_file),
        "modules_needing_llm_review": sum(1 for row in built_rows if row["needs_llm_qg"]),
        "modules_needing_db_persistence": sum(1 for row in built_rows if row["needs_db_persistence"]),
        "modules_recommended_for_second_review": sum(
            1 for row in built_rows if row["second_review_recommended"]
        ),
        "by_level": _summary_by(rows, "level"),
        "by_profile": _summary_by(rows, "profile"),
    }


def profile_for_level(level: str) -> str:
    """Return reviewer calibration profile for a level or seminar track."""
    clean = level.strip().lower()
    if clean in SEMINAR_TRACK_IDS:
        return "seminar"
    if clean.startswith("a1"):
        return "a1"
    if clean.startswith("a2"):
        return "a2"
    return "b1_plus"


def _selected_level_ids(level_ids: list[str] | None) -> list[str]:
    known = [str(item["id"]) for item in LEVELS]
    if level_ids is None:
        return known
    requested = [level.strip().lower() for level in level_ids if level.strip()]
    unknown = sorted(set(requested) - set(known))
    if unknown:
        raise ValueError(f"unknown level/track: {', '.join(unknown)}")
    return requested


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.load(path.read_text(encoding="utf-8"), Loader=_YAML_LOADER) or {}


def _manifest_slugs(manifest: dict[str, Any], level: str) -> list[str]:
    raw = manifest.get("levels", {}).get(level, {}).get("modules", [])
    if not isinstance(raw, list):
        return []
    slugs = []
    for entry in raw:
        slug = str(entry).split("#", 1)[0].strip()
        if slug:
            slugs.append(_to_bare_slug(slug))
    return slugs


def _plan_dir_slugs(plan_dir: Path) -> list[str]:
    if not plan_dir.is_dir():
        return []
    return [
        path.stem
        for path in sorted(plan_dir.glob("*.yaml"))
        if path.name != ".gitkeep"
    ]


def _to_bare_slug(entry: str) -> str:
    head, sep, tail = entry.partition("-")
    if sep and head.isdigit():
        return tail
    return entry


def _summary_by(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    out: dict[str, dict[str, int]] = {}
    for row in rows:
        label = str(row[key])
        bucket = out.setdefault(
            label,
            {
                "planned": 0,
                "built": 0,
                "surface_fail": 0,
                "surface_warn": 0,
                "current_db_llm_qg": 0,
                "current_file_only_llm_qg": 0,
                "missing_or_stale_llm_qg": 0,
                "needs_db_persistence": 0,
                "second_review_recommended": 0,
            },
        )
        bucket["planned"] += 1
        if row["built"]:
            bucket["built"] += 1
        if row["surface_verdict"] == "FAIL":
            bucket["surface_fail"] += 1
        if row["surface_verdict"] == "WARN":
            bucket["surface_warn"] += 1
        if row["llm_qg_status"] == "current_db":
            bucket["current_db_llm_qg"] += 1
        if row["llm_qg_status"] == "current_file_only":
            bucket["current_file_only_llm_qg"] += 1
        if row["llm_qg_status"] in {"missing", "stale_db", "stale_file"}:
            bucket["missing_or_stale_llm_qg"] += 1
        if row["needs_db_persistence"]:
            bucket["needs_db_persistence"] += 1
        if row["second_review_recommended"]:
            bucket["second_review_recommended"] += 1
    return out


def load_canary_results(specs: list[str] | None) -> dict[str, Any]:
    """Load LEVEL=PATH specs and evaluate reviewer canary outputs."""
    if not specs:
        return {}
    out: dict[str, Any] = {}
    for spec in specs:
        level, sep, raw_path = spec.partition("=")
        if not sep or not level.strip() or not raw_path.strip():
            raise ValueError("--canary-result must use LEVEL=/path/to/result.json")
        path = Path(raw_path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        out[level.strip().lower()] = {
            "path": str(path),
            **evaluate_canaries(payload, level),
        }
    return out


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--level",
        action="append",
        dest="levels",
        help="Level/track id to audit. Repeat for multiple levels. Defaults to all configured levels.",
    )
    parser.add_argument(
        "--curriculum-root",
        type=Path,
        default=CURRICULUM_ROOT,
        help="Curriculum root containing curriculum.yaml and level directories.",
    )
    parser.add_argument(
        "--llm-qg-db",
        type=Path,
        default=None,
        help="Optional LLM-QG SQLite path. Defaults to LEARN_UKRAINIAN_LLM_QG_DB or data/telemetry/llm_qg.db.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "summary"),
        default="summary",
        help="Output format. JSON includes per-module rows.",
    )
    parser.add_argument(
        "--include-findings",
        action="store_true",
        help="Include full surface finding rows in JSON output.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output file. Defaults to stdout.",
    )
    parser.add_argument(
        "--canary-result",
        action="append",
        dest="canary_results",
        help="Evaluate a saved LLM canary result as LEVEL=/path/result.json and include it in the report.",
    )
    parser.add_argument(
        "--fail-on-canary-failure",
        action="store_true",
        help="Return exit code 1 if any supplied canary result fails.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        canary_results = load_canary_results(args.canary_results)
        report = audit_modules(
            curriculum_root=args.curriculum_root,
            level_ids=args.levels,
            db_path=args.llm_qg_db,
            include_findings=args.include_findings,
            canary_results=canary_results,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        output = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    else:
        output = _format_summary(report["summary"])

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    if args.fail_on_canary_failure and any(
        not result.get("passed") for result in report.get("canaries", {}).values()
    ):
        return 1
    return 0


def _format_summary(summary: dict[str, Any]) -> str:
    lines = [
        "Module Quality Gate Audit",
        f"Planned modules: {summary['planned_modules']}",
        f"Built modules: {summary['built_modules']}",
        f"Unbuilt modules: {summary['unbuilt_modules']}",
        f"Surface FAIL/WARN: {summary['surface_fail_modules']}/{summary['surface_warn_modules']}",
        f"Current DB LLM-QG: {summary['current_db_llm_qg_modules']}",
        f"Current file-only LLM-QG: {summary['current_file_only_llm_qg_modules']}",
        f"Stale LLM-QG: {summary['stale_llm_qg_modules']}",
        f"Missing LLM-QG: {summary['missing_llm_qg_modules']}",
        f"Built modules without current DB LLM-QG: {summary['modules_without_current_db_llm_qg']}",
        f"Built modules without current DB/file LLM-QG: {summary['modules_without_current_any_llm_qg']}",
        f"Modules needing LLM review: {summary['modules_needing_llm_review']}",
        f"Modules needing DB persistence: {summary['modules_needing_db_persistence']}",
        f"Modules recommended for second review: {summary['modules_recommended_for_second_review']}",
        "",
        "By profile:",
    ]
    for profile, bucket in sorted(summary["by_profile"].items()):
        lines.append(
            "  "
            f"{profile}: planned={bucket['planned']} built={bucket['built']} "
            f"surface_fail={bucket['surface_fail']} surface_warn={bucket['surface_warn']} "
            f"current_db={bucket['current_db_llm_qg']} "
            f"missing_or_stale={bucket['missing_or_stale_llm_qg']}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
