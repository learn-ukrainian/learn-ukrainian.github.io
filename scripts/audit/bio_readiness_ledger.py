#!/usr/bin/env python3
"""Report fail-closed BIO promotion readiness without generating artifacts.

The source-controlled registry records only reviewed manual evidence. Everything
else is calculated from the current manifest and source tree at report time.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
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
from scripts.audit.llm_qg_store import content_sha_for_module
from scripts.audit.llm_qg_store import db_path as configured_qg_db_path
from scripts.audit.module_quality_audit import PlannedModule, audit_one_module
from scripts.audit.wiki_completeness_gate import check_wiki_completeness
from scripts.build import linear_pipeline
from scripts.orchestration.preparation_evidence import RegistryValidationError, load_manual_evidence
from scripts.validate import check_discovery_integrity, check_wiki_subject, lint_seminar_quality
from scripts.wiki.domains import resolve_write_domain

MILESTONES = (
    "inventory",
    "source-ready",
    "plan-ready",
    "wiki-ready",
    "module-ready",
    "module-built",
    "qg-current",
    "shipped",
)


def _status(status: bool | None) -> str:
    return "pass" if status is True else "fail" if status is False else "unknown"


def _gate(status: bool | None, *, paths: list[str] | None = None, detail: str | None = None) -> dict:
    result = {"status": _status(status), "evidence_paths": paths or []}
    if detail:
        result["detail"] = detail
    return result


def _manual_gate(record: Mapping[str, object] | None, registry_path: Path, slug: str, name: str) -> dict:
    if record is None:
        return _gate(None, paths=[f"{registry_path}#entries.{slug}.{name}"])
    result = _gate(
        record.get("status") == "pass",
        paths=[f"{registry_path}#entries.{slug}.{name}"],
    )
    result["reviewer_family"] = record["reviewer_family"]
    result["date"] = record["date"].isoformat() if isinstance(record["date"], date) else record["date"]
    result["evidence_url"] = record["evidence_url"]
    if "disposition" in record:
        result["disposition"] = record["disposition"]
    if "active" in record:
        result["active"] = record["active"]
    if "reason" in record:
        result["reason"] = record["reason"]
    return result


def manifest_inventory(root: Path, track: str) -> tuple[list[str], Counter[str]]:
    manifest_path = root / "curriculum" / "l2-uk-en" / "curriculum.yaml"
    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    modules = raw.get("levels", {}).get(track, {}).get("modules", [])
    if not isinstance(modules, list) or not all(isinstance(slug, str) and slug for slug in modules):
        raise ValueError(f"manifest levels.{track}.modules must be a list of non-empty slugs")
    counts = Counter(modules)
    duplicates = sorted(slug for slug, count in counts.items() if count != 1)
    if duplicates:
        raise ValueError(f"manifest levels.{track}.modules contains duplicate slugs: {', '.join(duplicates)}")
    return modules, counts


def resolved_wiki_paths(root: Path, track: str, slug: str) -> tuple[Path, Path]:
    """Return the shared resolver's wiki/source pair, not a track-local fork."""
    directory = root / "wiki" / resolve_write_domain(track, slug)
    return directory / f"{slug}.md", directory / f"{slug}.sources.yaml"


def _plan_has_reading_packet(plan: Mapping[str, object]) -> bool:
    readings = plan.get("readings")
    return isinstance(readings, list) and bool(readings)


def _read_current_qg(db_path: Path, track: str, slug: str, module_dir: Path) -> dict:
    """Read persisted QG state without initialising or changing the telemetry DB."""
    if not db_path.exists():
        return {
            "current": None,
            "passed": None,
            "source": str(db_path),
            "store_available": False,
            "query_ok": False,
            "detail": "QG store is unavailable",
        }
    try:
        connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            row = connection.execute(
                """
                SELECT payload_json, run_id, created_at, reviewer_family, reviewer_model, gate_version
                FROM llm_qg_runs
                WHERE level = ? AND slug = ? AND content_sha = ?
                ORDER BY created_at DESC, run_id DESC LIMIT 1
                """,
                (track, slug, content_sha_for_module(module_dir)),
            ).fetchone()
        finally:
            connection.close()
    except sqlite3.Error as exc:
        return {
            "current": None,
            "passed": None,
            "source": str(db_path),
            "store_available": True,
            "query_ok": False,
            "detail": f"read-only QG query failed: {exc}",
        }
    if row is None:
        return {
            "current": False,
            "passed": False,
            "source": str(db_path),
            "store_available": True,
            "query_ok": True,
        }
    try:
        payload = json.loads(row[0])
    except (TypeError, json.JSONDecodeError):
        payload = {}
    aggregate = payload.get("aggregate", {}) if isinstance(payload, Mapping) else {}
    terminal = (
        aggregate.get("terminal_verdict", payload.get("terminal_verdict")) if isinstance(aggregate, Mapping) else None
    )
    return {
        "current": True,
        "passed": str(terminal).upper() == "PASS",
        "source": str(db_path),
        "store_available": True,
        "query_ok": True,
        "run_id": row[1],
        "created_at": row[2],
        "reviewer_family": row[3],
        "reviewer_model": row[4],
        "gate_version": row[5],
        "terminal_verdict": terminal,
    }


def _build_gate(track: str, slug: str, module_dir: Path, plan_path: Path) -> dict:
    """Use the current read-only deterministic module-quality surface gate.

    ``verify_shippable`` performs external resource liveness checks, which are
    deliberately not a deterministic readiness predicate. The ledger reports
    the required checked-in MDX separately and leaves full ship verification to
    its dedicated release workflow.
    """
    del plan_path  # The active writer plan check already runs independently.
    audit = audit_one_module(
        PlannedModule(num=0, level=track, slug=slug, profile="seminar"),
        curriculum_root=module_dir.parents[1],
        include_findings=False,
    )
    passed = audit.built and audit.surface_verdict == "PASS"
    return _gate(passed, paths=[str(module_dir)], detail=f"surface verdict: {audit.surface_verdict}")


def calculate_milestones(gates: Mapping[str, Mapping[str, object]]) -> dict[str, bool]:
    """Apply the promotion contract in its declared order.

    ``bundle`` and ``qg_result`` remain visible independently, but promotion
    milestones are cumulative: a legacy built module cannot skip manual source
    and cohort approval merely because its files happen to exist.
    """

    def passed(name: str) -> bool:
        return gates[name]["status"] == "pass"

    inventory = passed("inventory")
    source = inventory and all(passed(name) for name in ("dossier", "dossier_xref", "dossier_grounding"))
    plan = source and all(passed(name) for name in ("plan", "plan_check", "plan_language", "reading_or_rights"))
    wiki = plan and all(
        passed(name)
        for name in (
            "wiki_pair",
            "wiki_completeness",
            "wiki_subject",
            "wiki_language",
            "wiki_grounding",
            "wiki_quote_verification",
            "image_rights",
        )
    )
    module_ready = wiki and all(
        passed(name) for name in ("discovery", "discovery_integrity", "no_active_hold", "cohort_promotion")
    )
    module_built = module_ready and all(passed(name) for name in ("module_bundle", "mdx", "deterministic_build"))
    qg_current = module_built and passed("qg_result")
    shipped = qg_current and all(
        passed(name) for name in ("qg_pass", "corpus_hammer", "independent_content_review", "merged_publication")
    )
    return {
        "inventory": inventory,
        "source-ready": source,
        "plan-ready": plan,
        "wiki-ready": wiki,
        "module-ready": module_ready,
        "module-built": module_built,
        "qg-current": qg_current,
        "shipped": shipped,
    }


def release_state(milestones: Mapping[str, bool], gates: Mapping[str, Mapping[str, object]]) -> str:
    """Name release state from observed build/QG gates plus promotion policy.

    A legacy pilot can be physically built before the promotion registry exists.
    That does not promote it, but missing QG must still be visible as
    ``qg-pending`` instead of being hidden behind ``promotion-blocked``.
    """
    if milestones["shipped"]:
        return "shipped"
    built = all(gates[name]["status"] == "pass" for name in ("module_bundle", "mdx", "deterministic_build"))
    if built and gates["qg_result"]["status"] != "pass":
        return "qg-pending"
    if built and gates["qg_result"]["status"] == "pass" and gates["qg_pass"]["status"] != "pass":
        return "qg-failed"
    if milestones["qg-current"]:
        return "release-review-pending"
    return "promotion-blocked"


def artifact_state(gates: Mapping[str, Mapping[str, object]]) -> str:
    """Report observed build progress separately from fail-closed promotion."""
    built = all(gates[name]["status"] == "pass" for name in ("module_bundle", "mdx", "deterministic_build"))
    if not built:
        return "not-built"
    if gates["qg_result"]["status"] == "pass":
        return "qg-current"
    return "module-built"


def _blockers(gates: Mapping[str, Mapping[str, object]]) -> list[str]:
    codes = {
        "dossier": "DOSSIER_MISSING",
        "dossier_xref": "DOSSIER_XREF_FAIL",
        "dossier_grounding": "DOSSIER_GROUNDING_UNKNOWN",
        "plan": "PLAN_MISSING",
        "plan_check": "PLAN_CHECK_FAIL",
        "plan_language": "PLAN_LANGUAGE_HIGH",
        "reading_or_rights": "READING_OR_RIGHTS_UNKNOWN",
        "wiki_pair": "WIKI_PAIR_MISSING",
        "wiki_completeness": "WIKI_COMPLETENESS_FAIL",
        "wiki_subject": "WIKI_SUBJECT_FAIL",
        "wiki_language": "WIKI_LANGUAGE_HIGH",
        "wiki_grounding": "WIKI_GROUNDING_UNKNOWN",
        "wiki_quote_verification": "WIKI_QUOTE_UNKNOWN",
        "image_rights": "IMAGE_RIGHTS_UNKNOWN",
        "discovery": "DISCOVERY_MISSING",
        "discovery_integrity": "DISCOVERY_INTEGRITY_FAIL",
        "no_active_hold": "ACTIVE_HOLD",
        "cohort_promotion": "COHORT_PROMOTION_UNKNOWN",
        "module_bundle": "MODULE_BUNDLE_MISSING",
        "mdx": "MDX_MISSING",
        "deterministic_build": "BUILD_GATE_FAIL",
        "qg_result": "QG_CURRENT_MISSING",
        "qg_pass": "QG_NOT_PASS",
        "corpus_hammer": "CORPUS_HAMMER_UNKNOWN",
        "independent_content_review": "INDEPENDENT_REVIEW_UNKNOWN",
        "merged_publication": "MERGED_PUBLICATION_UNKNOWN",
    }
    blockers: list[str] = []
    for name, code in codes.items():
        status = gates[name]["status"]
        if status == "pass":
            continue
        if name == "qg_result" and status == "unknown":
            code = "QG_STORE_UNAVAILABLE"
        elif name == "qg_pass" and status == "unknown":
            code = "QG_PASS_UNKNOWN"
        blockers.append(code)
    return blockers


def _off_manifest_artifacts(root: Path, track: str, manifest: set[str]) -> dict[str, list[str]]:
    curriculum = root / "curriculum" / "l2-uk-en"
    wiki_dir = root / "wiki" / resolve_write_domain(track, "")
    categories = {
        "dossiers": root / "docs" / "research" / track,
        "plans": curriculum / "plans" / track,
        "discovery": curriculum / track / "discovery",
        "wiki": wiki_dir,
        "wiki_sources": wiki_dir,
        "modules": curriculum / track,
    }
    result: dict[str, list[str]] = {}
    for category, directory in categories.items():
        if not directory.exists():
            result[category] = []
            continue
        if category == "modules":
            paths = [item for item in directory.iterdir() if item.is_dir() and item.name != "discovery"]
        elif category in {"wiki", "dossiers"}:
            paths = list(directory.glob("*.md"))
        elif category == "wiki_sources":
            paths = list(directory.glob("*.sources.yaml"))
        else:
            paths = list(directory.glob("*.yaml"))
        names = [path.name.removesuffix(".sources.yaml") if category == "wiki_sources" else path.stem for path in paths]
        result[category] = sorted(name for name in names if name not in manifest)
    return result


def build_ledger(
    *,
    root: Path = PROJECT_ROOT,
    track: str = "bio",
    registry_path: Path | None = None,
    qg_db_path: Path | None = None,
) -> dict:
    """Return a live, JSON-serializable promotion ledger without writing files."""
    track = track.lower()
    qg_db_path = configured_qg_db_path(qg_db_path)
    slugs, _ = manifest_inventory(root, track)
    manifest_set = set(slugs)
    registry_path = registry_path or root / "curriculum" / "l2-uk-en" / track / "promotion-evidence.yaml"
    evidence = load_manual_evidence(registry_path, manifest_set)
    curriculum = root / "curriculum" / "l2-uk-en"
    rows: list[dict] = []

    for slug in slugs:
        manual = evidence.get(slug, {})
        dossier = root / "docs" / "research" / track / f"{slug}.md"
        plan_path = curriculum / "plans" / track / f"{slug}.yaml"
        discovery = curriculum / track / "discovery" / f"{slug}.yaml"
        wiki_path, source_path = resolved_wiki_paths(root, track, slug)
        module_dir = curriculum / track / slug
        mdx_path = root / "site" / "src" / "content" / "docs" / track / f"{slug}.mdx"
        gates: dict[str, dict] = {
            # manifest_inventory rejects duplicates before row construction.
            "inventory": _gate(True, paths=["curriculum/l2-uk-en/curriculum.yaml"]),
            "dossier": _gate(dossier.exists(), paths=[str(dossier)]),
            "dossier_grounding": _manual_gate(
                manual.get("dossier_grounding"), registry_path, slug, "dossier_grounding"
            ),
            "plan": _gate(plan_path.exists(), paths=[str(plan_path)]),
            "reading_rights": _manual_gate(manual.get("reading_rights"), registry_path, slug, "reading_rights"),
            "wiki_grounding": _manual_gate(manual.get("wiki_grounding"), registry_path, slug, "wiki_grounding"),
            "wiki_quote_verification": _manual_gate(
                manual.get("wiki_quote_verification"), registry_path, slug, "wiki_quote_verification"
            ),
            "image_rights": _manual_gate(manual.get("image_rights"), registry_path, slug, "image_rights"),
            "cohort_promotion": _manual_gate(manual.get("cohort_promotion"), registry_path, slug, "cohort_promotion"),
            "hold": _manual_gate(manual.get("hold"), registry_path, slug, "hold"),
            "corpus_hammer": _manual_gate(manual.get("corpus_hammer"), registry_path, slug, "corpus_hammer"),
            "independent_content_review": _manual_gate(
                manual.get("independent_content_review"), registry_path, slug, "independent_content_review"
            ),
            "merged_publication": _manual_gate(
                manual.get("merged_publication"), registry_path, slug, "merged_publication"
            ),
        }
        hold = manual.get("hold")
        gates["no_active_hold"] = _gate(
            not (hold and hold.get("active") is True),
            paths=[f"{registry_path}#entries.{slug}.hold"],
        )

        if dossier.exists():
            gates["dossier_xref"] = _gate(not lint_bio_dossier_xref.lint_dossier(dossier), paths=[str(dossier)])
        else:
            gates["dossier_xref"] = _gate(False, paths=[str(dossier)])

        plan: Mapping[str, object] | None = None
        raw_plan: Mapping[str, object] | None = None
        if plan_path.exists():
            try:
                candidate = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
                raw_plan = candidate if isinstance(candidate, Mapping) else None
            except yaml.YAMLError:
                raw_plan = None
            try:
                plan = linear_pipeline.plan_check(plan_path)
                gates["plan_check"] = _gate(True, paths=[str(plan_path)])
            except Exception as exc:  # plan_check is the authoritative writer validator
                gates["plan_check"] = _gate(False, paths=[str(plan_path)], detail=f"{type(exc).__name__}: {exc}")
            high = [finding for finding in lint_seminar_quality.lint_plan(plan_path) if finding.severity == "high"]
            gates["plan_language"] = _gate(not high, paths=[str(plan_path)], detail=f"{len(high)} high finding(s)")
            gates["reading_packet"] = _gate(
                raw_plan is not None and _plan_has_reading_packet(raw_plan),
                paths=[str(plan_path)],
                detail="plan contains a reading packet"
                if raw_plan is not None and _plan_has_reading_packet(raw_plan)
                else "plan has no reading packet",
            )
        else:
            gates["plan_check"] = _gate(False, paths=[str(plan_path)])
            gates["plan_language"] = _gate(False, paths=[str(plan_path)])
            gates["reading_packet"] = _gate(False, paths=[str(plan_path)])
        gates["reading_or_rights"] = _gate(
            gates["reading_packet"]["status"] == "pass" or gates["reading_rights"]["status"] == "pass",
            paths=[*gates["reading_packet"]["evidence_paths"], *gates["reading_rights"]["evidence_paths"]],
            detail="valid-plan reading packet or approved manual exception with rights/hosting disposition",
        )

        gates["wiki_pair"] = _gate(
            wiki_path.exists() and source_path.exists(), paths=[str(wiki_path), str(source_path)]
        )
        if wiki_path.exists() and source_path.exists():
            report = check_wiki_completeness(wiki_path, level=track, slug=slug)
            gates["wiki_completeness"] = _gate(
                report["verdict"] == "PASS", paths=[str(wiki_path), str(source_path)], detail=report["diagnostic"]
            )
            title = str(plan.get("title", "")) if plan else None
            subject_finding = check_wiki_subject.check_wiki_file(wiki_path, plan_title=title)
            gates["wiki_subject"] = _gate(subject_finding is None, paths=[str(wiki_path)])
            high = [finding for finding in lint_seminar_quality.lint_text(wiki_path) if finding.severity == "high"]
            gates["wiki_language"] = _gate(not high, paths=[str(wiki_path)], detail=f"{len(high)} high finding(s)")
        else:
            for name in ("wiki_completeness", "wiki_subject", "wiki_language"):
                gates[name] = _gate(False, paths=[str(wiki_path), str(source_path)])

        gates["discovery"] = _gate(discovery.exists(), paths=[str(discovery)])
        if discovery.exists() and plan is not None:
            finding = check_discovery_integrity.check_discovery_file(discovery, plan_title=str(plan.get("title", "")))
            gates["discovery_integrity"] = _gate(finding is None, paths=[str(discovery)])
        else:
            gates["discovery_integrity"] = _gate(False, paths=[str(discovery)])

        bundle_files = [
            module_dir / name for name in ("module.md", "activities.yaml", "vocabulary.yaml", "resources.yaml")
        ]
        gates["module_bundle"] = _gate(
            all(path.exists() for path in bundle_files), paths=[str(path) for path in bundle_files]
        )
        gates["mdx"] = _gate(mdx_path.exists(), paths=[str(mdx_path)])
        if gates["module_bundle"]["status"] == "pass" and gates["mdx"]["status"] == "pass" and plan_path.exists():
            gates["deterministic_build"] = _build_gate(track, slug, module_dir, plan_path)
            qg = _read_current_qg(qg_db_path, track, slug, module_dir)
        else:
            gates["deterministic_build"] = _gate(False, paths=[str(module_dir)])
            qg = {
                "current": False,
                "passed": False,
                "source": str(qg_db_path),
                "store_available": qg_db_path.exists(),
                "query_ok": None,
                "detail": "QG is not applicable until the module bundle and MDX pass",
            }
        qg_detail = qg.get("terminal_verdict") or qg.get("detail")
        gates["qg_result"] = _gate(qg["current"], paths=[qg["source"]], detail=qg_detail)
        gates["qg_pass"] = _gate(qg["passed"], paths=[qg["source"]], detail=qg_detail)

        milestones = calculate_milestones(gates)
        highest = max((name for name, reached in milestones.items() if reached), key=MILESTONES.index, default="none")
        state = release_state(milestones, gates)
        rows.append(
            {
                "slug": slug,
                "gates": gates,
                "milestones": milestones,
                "highest_milestone": highest,
                "artifact_state": artifact_state(gates),
                "release_state": state,
                "blocker_codes": _blockers(gates),
                "qg": qg,
            }
        )

    summary = {
        "track": track,
        "manifest_rows": len(slugs),
        "highest_milestones": dict(Counter(row["highest_milestone"] for row in rows)),
        "release_states": dict(Counter(row["release_state"] for row in rows)),
        "artifact_states": dict(Counter(row["artifact_state"] for row in rows)),
        "qg_store": {"path": str(qg_db_path), "available": qg_db_path.exists()},
        "qg_current_rows": sum(row["gates"]["qg_result"]["status"] == "pass" for row in rows),
    }
    return {
        "summary": summary,
        "rows": rows,
        "off_manifest_artifacts": _off_manifest_artifacts(root, track, manifest_set),
    }


def _print_summary(report: Mapping[str, object]) -> None:
    summary = report["summary"]
    print(f"{summary['track']} readiness ledger: {summary['manifest_rows']} manifest rows")
    print("highest milestones: " + json.dumps(summary["highest_milestones"], sort_keys=True))
    print("release states: " + json.dumps(summary["release_states"], sort_keys=True))
    print("artifact states: " + json.dumps(summary["artifact_states"], sort_keys=True))
    print("QG store: " + json.dumps(summary["qg_store"], sort_keys=True))
    off_manifest = report["off_manifest_artifacts"]
    print("off-manifest artifacts: " + json.dumps(off_manifest, ensure_ascii=False, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--track", default="bio", help="Seminar track (default: bio)")
    parser.add_argument("--format", choices=("summary", "json"), default="summary")
    parser.add_argument("--output", type=Path, help="Optional explicit report path; default is stdout")
    parser.add_argument("--registry", type=Path, help="Manual evidence registry path")
    parser.add_argument(
        "--llm-qg-db",
        type=Path,
        help="Read-only LLM-QG SQLite path (default: LEARN_UKRAINIAN_LLM_QG_DB or this checkout's store)",
    )
    args = parser.parse_args(argv)
    try:
        report = build_ledger(
            root=PROJECT_ROOT, track=args.track, registry_path=args.registry, qg_db_path=args.llm_qg_db
        )
    except (RegistryValidationError, ValueError, OSError) as exc:
        parser.error(str(exc))
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    if args.format == "json":
        print(rendered)
    elif not args.output:
        _print_summary(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
