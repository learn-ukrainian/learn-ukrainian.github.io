"""Named residual lists for the post-#6062 teacher local-practice smoke (#6064).

#6062 admits every ``sentenceStatus=has_candidates`` private teacher row to
local Practice regardless of whether its lemma has a public Atlas route or a
pipeline-derived CEFR level — those two gates are only evaluated later, by
``scripts.lexicon.curated_seed_atlas_admission.prepare_practice_seed``, when
building the actual Practice seed. This module reuses that same classifier
(it never re-derives route/CEFR membership itself) and splits its
``atlas_failures`` / ``practice_skipped_no_cefr`` output into two named,
deterministic residual lists so a teacher/operator can see what is left:

- rows whose lemma has no public Atlas route at all (``missing_route.jsonl``)
- rows whose lemma has a route but no pipeline CEFR (``no_cefr.jsonl``)

Inputs are the private curated-seed package (gitignored; see
``.claude/atlas-epic/plans/curated-seed/`` — ``curated-seed.jsonl`` +
``practice-admission.jsonl``, produced by
``scripts/atlas/rebuild_teacher_curated_seed.py``) and the hydrated public
Atlas manifest (``site/src/data/lexicon-manifest.json``). Outputs are
gitignored JSONL/JSON reports under ``batch_state/atlas/residual/`` — never
the public learner site.

This script never invents a lemma, a CEFR level, or a redistribution right;
it only reports what the existing pipeline already decided.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lexicon.curated_seed_atlas_admission import normalize_rows, prepare_practice_seed
from scripts.lexicon.manifest_io import DEFAULT_MANIFEST, load_manifest

DEFAULT_PACKAGE_ROOT = ROOT / ".claude" / "atlas-epic" / "plans" / "curated-seed"
DEFAULT_OUTPUT_DIR = ROOT / "batch_state" / "atlas" / "residual"
MISSING_ROUTE_REASON = "missing_public_route"
SUMMARY_SCHEMA = "atlas-residual-teacher-lists-v1"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"JSONL rows must be objects: {path}")
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify_admission_consistency(seed_rows: list[dict[str, Any]], admission_rows: list[dict[str, Any]]) -> None:
    """Cross-check the two private package files agree before trusting either.

    Both files are dual-written from the same refresh (see
    ``rebuild_teacher_curated_seed.refresh_rights_ledger``); a mismatch means
    the package drifted between writes and residual counts would be unsafe.
    """
    by_row = {row.get("seedRow"): row for row in admission_rows}
    if len(by_row) != len(admission_rows):
        raise ValueError("practice-admission.jsonl contains duplicate seedRow values")
    for row in seed_rows:
        seed_row = row.get("seedRow")
        ledger = by_row.get(seed_row)
        if ledger is None:
            raise ValueError(f"seed row {seed_row} missing from practice-admission.jsonl")
        raw_admission = row.get("admission")
        admission: dict[str, Any] = raw_admission if isinstance(raw_admission, dict) else {}
        if bool(ledger.get("practice")) != (admission.get("practice") is True):
            raise ValueError(f"seed row {seed_row}: practice flag disagrees between the two package files")
        if str(ledger.get("mode") or "") != str(admission.get("mode") or ""):
            raise ValueError(f"seed row {seed_row}: admission mode disagrees between the two package files")


def load_package_rows(package_root: Path) -> list[dict[str, Any]]:
    """Read + cross-validate the private curated-seed package (gitignored)."""
    seed_path = package_root / "curated-seed.jsonl"
    admission_path = package_root / "practice-admission.jsonl"
    if not seed_path.is_file():
        raise FileNotFoundError(
            f"curated-seed.jsonl not found under {package_root}. This is the gitignored private "
            "teacher package (.claude/atlas-epic/plans/curated-seed/); rebuild it with "
            "scripts/atlas/rebuild_teacher_curated_seed.py before running residual reporting."
        )
    if not admission_path.is_file():
        raise FileNotFoundError(
            f"practice-admission.jsonl not found under {package_root}. This is the gitignored private "
            "teacher rights ledger (.claude/atlas-epic/plans/curated-seed/), dual-written alongside "
            "curated-seed.jsonl; rebuild it with scripts/atlas/rebuild_teacher_curated_seed.py before "
            "running residual reporting."
        )
    seed_rows = _read_jsonl(seed_path)
    verify_admission_consistency(seed_rows, _read_jsonl(admission_path))
    return seed_rows


def classify_residuals(rows: list[dict[str, Any]], manifest_path: Path) -> dict[str, Any]:
    """Split the existing admission classifier's failures into named residuals.

    Reuses ``curated_seed_atlas_admission.prepare_practice_seed`` verbatim —
    this function never re-derives route or CEFR membership itself.
    """
    normalized = normalize_rows(rows)
    _seed, report = prepare_practice_seed(normalized, manifest_path)
    admission_by_seed_row = {row.get("seedRow"): row.get("admission") or {} for row in normalized}

    missing_route: list[dict[str, Any]] = []
    other_atlas_failures: list[dict[str, Any]] = []
    for failure in report["atlas_failures"]:
        if failure.get("reason") == MISSING_ROUTE_REASON:
            seed_row = failure.get("seedRow")
            mode = str(admission_by_seed_row.get(seed_row, {}).get("mode") or "")
            missing_route.append({"seedRow": seed_row, "lemma": failure.get("lemma"), "mode": mode})
        else:
            other_atlas_failures.append(failure)

    no_cefr: list[dict[str, Any]] = [
        {
            "seedRow": entry.get("seedRow"),
            "lemma": entry.get("lemma"),
            "url_slug": str(entry.get("url_slug") or ""),
        }
        for entry in report["practice_skipped_no_cefr"]
    ]

    summary: dict[str, Any] = {
        "schema": SUMMARY_SCHEMA,
        "issue": 6064,
        "counts": {
            "input_rows": len(rows),
            **report["counts"],
            "missing_route": len(missing_route),
            "no_cefr": len(no_cefr),
            "other_atlas_failures": len(other_atlas_failures),
        },
    }
    if other_atlas_failures:
        summary["other_atlas_failures"] = other_atlas_failures
    return {"missing_route": missing_route, "no_cefr": no_cefr, "summary": summary}


def write_residual_reports(result: dict[str, Any], output_dir: Path) -> None:
    _write_jsonl(output_dir / "missing_route.jsonl", result["missing_route"])
    _write_jsonl(output_dir / "no_cefr.jsonl", result["no_cefr"])
    _write_json(output_dir / "summary.json", result["summary"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--package-root",
        type=Path,
        default=DEFAULT_PACKAGE_ROOT,
        help="Private curated-seed package root (gitignored .claude/atlas-epic/plans/curated-seed/).",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Atlas manifest path (default: hydrate site/src/data/lexicon-manifest.json).",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)

    rows = load_package_rows(args.package_root)
    manifest_path = args.manifest
    if manifest_path is None:
        load_manifest()
        manifest_path = DEFAULT_MANIFEST

    result = classify_residuals(rows, manifest_path)
    write_residual_reports(result, args.output_dir)

    counts = result["summary"]["counts"]
    print(
        f"input_rows={counts['input_rows']} practice_admitted_rows={counts['practice_admitted_rows']} "
        f"missing_route={counts['missing_route']} no_cefr={counts['no_cefr']} -> {args.output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
