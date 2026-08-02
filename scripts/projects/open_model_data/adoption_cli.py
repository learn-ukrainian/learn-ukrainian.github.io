#!/usr/bin/env python3
"""Package Foundry outputs for a local trial, Lapa, or lang-uk.

This adapter never downloads a model, runs training, creates a weight adapter,
or contacts an external service. It transforms already verified artifacts and
records exact upstream and input revisions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.projects.open_model_data import foundry_cli
from scripts.projects.ua_open_weight_eval import suite_cli

LOCKS_PATH = ROOT / "data/projects/open_model_data/integrations/upstream-locks.json"
EXAMPLE_PATH = ROOT / "data/projects/open_model_data/examples/portable-corpus-v1.jsonl"
EXAMPLE_COST_PATH = ROOT / "data/projects/open_model_data/examples/portable-cost-v1.json"


class AdoptionError(ValueError):
    """An adoption input violates a pinned integration contract."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AdoptionError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AdoptionError(f"expected JSON object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise AdoptionError(f"cannot read JSONL {path}: {exc}") from exc
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AdoptionError(f"invalid JSONL {path}:{line_number}: {exc}") from exc
        if not isinstance(row, dict):
            raise AdoptionError(f"expected object at {path}:{line_number}")
        rows.append(row)
    if not rows:
        raise AdoptionError(f"empty JSONL: {path}")
    return rows


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.write_text("".join(_canonical_json(dict(row)) + "\n" for row in rows), encoding="utf-8")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AdoptionError(message)


def _atomic_output(output_dir: Path, builder: Any) -> dict[str, Any]:
    _require(not output_dir.exists(), f"refusing to replace output directory: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}-", dir=output_dir.parent))
    try:
        result = builder(staging)
        staging.replace(output_dir)
        return result
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def trial(*, input_path: Path, output_dir: Path, max_records: int) -> dict[str, Any]:
    """Run the small no-model Foundry trial and prepare evaluation requests."""

    def build(staging: Path) -> dict[str, Any]:
        foundry = foundry_cli.prepare(
            input_path=input_path,
            output_dir=staging / "foundry",
            max_records=max_records,
            evaluation_artifacts=(),
            tokenizer_path=None,
            tokenizer_identifier=None,
            tokenizer_revision=None,
            cost_path=EXAMPLE_COST_PATH if input_path.resolve() == EXAMPLE_PATH.resolve() else None,
        )
        verification = foundry_cli.verify(foundry.output_dir)
        request_path = staging / "ua-open-weight-eval-requests.jsonl"
        requests = suite_cli.prepare_requests(request_path)
        receipt = {
            "schema_version": "foundry_adoption_trial_receipt.v1",
            "input_sha256": _sha256_file(input_path),
            "foundry_receipt_sha256": _sha256_file(foundry.output_dir / "run-receipt.json"),
            "evaluation_requests_sha256": requests["sha256"],
            "records": foundry.receipt["input"]["records"],
            "evaluation_requests": requests["requests"],
            "verification": verification["status"],
            "network_or_api_used": False,
            "model_or_training_run": False,
        }
        _write_json(staging / "trial-receipt.json", receipt)
        return receipt

    return _atomic_output(output_dir, build)


def export_lapa(*, foundry_run: Path, output_dir: Path) -> dict[str, Any]:
    """Export only verified, unmasked faithful rows to Lapa's JSONL text shape."""
    verification = foundry_cli.verify(foundry_run)
    rows = _read_jsonl(foundry_run / "faithful-source.jsonl")
    locks = _read_json(LOCKS_PATH)

    def build(staging: Path) -> dict[str, Any]:
        output_rows: list[dict[str, str]] = []
        lineage: list[dict[str, str]] = []
        for row in rows:
            _require(row.get("schema_version") == "foundry_faithful_source_view_v1", "not a faithful Foundry view")
            _require(row.get("character_mask_spans") == [], "masked or rewritten row cannot enter Lapa pretraining export")
            text = row.get("text")
            _require(isinstance(text, str) and text, "empty Lapa text row")
            _require(foundry_cli.sha256_text(text) == row.get("text_sha256"), "Foundry text hash mismatch")
            output_rows.append({"text": text})
            lineage.append(
                {
                    "record_id": str(row["record_id"]),
                    "text_sha256": str(row["text_sha256"]),
                    "source_record_id": str(row["lineage"]["source_record_id"]),
                }
            )
        dataset_path = staging / "foundry-pretraining.jsonl"
        _write_jsonl(dataset_path, output_rows)
        _write_jsonl(staging / "foundry-pretraining.lineage.jsonl", lineage)
        receipt = {
            "schema_version": "foundry_lapa_integration_receipt.v1",
            "upstream": locks["lapa"],
            "target_format": {"media_type": "application/jsonl", "fields": ["text"]},
            "source_foundry_run_receipt_sha256": _sha256_file(foundry_run / "run-receipt.json"),
            "source_verification": verification["status"],
            "rows": len(output_rows),
            "dataset_sha256": _sha256_file(dataset_path),
            "lineage_sha256": _sha256_file(staging / "foundry-pretraining.lineage.jsonl"),
            "masked_rows_exported": 0,
            "evaluation_rows_exported": 0,
            "training_or_weight_adapter_created": False,
        }
        _write_json(staging / "lapa-integration-receipt.json", receipt)
        return receipt

    return _atomic_output(output_dir, build)


def _validate_lang_uk_results(results: Mapping[str, Any]) -> str:
    general = results.get("config_general")
    metrics = results.get("results")
    _require(isinstance(general, dict) and isinstance(general.get("model_name"), str), "missing lang-uk model_name")
    _require(isinstance(metrics, dict) and metrics, "missing lang-uk results")
    for task_name, task_metrics in metrics.items():
        _require(isinstance(task_name, str) and isinstance(task_metrics, dict), "invalid lang-uk task")
        for metric_name, value in task_metrics.items():
            if metric_name == "qg_meta":
                _require(isinstance(value, dict), "qg_meta must be an object")
                continue
            _require(isinstance(value, int | float) and not isinstance(value, bool), "lang-uk metric must be numeric")
    return general["model_name"]


def package_lang_uk(
    *,
    results_path: Path,
    broad_report_path: Path,
    foundry_run: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Copy validated lang-uk results and add reproducibility evidence."""
    _require(
        results_path.name.startswith("results_") and results_path.suffix == ".json",
        "lang-uk result filename must match results_*.json",
    )
    results = _read_json(results_path)
    model_name = _validate_lang_uk_results(results)
    broad_report = _read_json(broad_report_path)
    _require(broad_report.get("schema_version") == suite_cli.REPORT_SCHEMA, "wrong broad evaluation report schema")
    scoring = broad_report.get("scoring")
    _require(isinstance(scoring, dict) and scoring.get("global_quality_score") is None, "broad report has a global score")
    _require(scoring.get("closed_model_judge_used") is False, "closed model judge report rejected")
    _require(set(broad_report.get("tracks", {})) == set(suite_cli.read_json(suite_cli.CONFIG_PATH)["tracks"]), "broad report track set drift")
    _require(
        broad_report.get("cases_sha256") == suite_cli.sha256_file(suite_cli.CASES_PATH),
        "broad report is not bound to the current frozen case file",
    )
    verification = foundry_cli.verify(foundry_run)
    locks = _read_json(LOCKS_PATH)

    def build(staging: Path) -> dict[str, Any]:
        copied_results = staging / results_path.name
        shutil.copyfile(results_path, copied_results)
        sidecar = {
            "schema_version": "foundry_lang_uk_evidence_sidecar.v1",
            "model_name": model_name,
            "upstream": locks["lang_uk_leaderboard"],
            "lang_uk_results": {
                "file": copied_results.name,
                "sha256": _sha256_file(copied_results),
            },
            "foundry": {
                "run_receipt_sha256": _sha256_file(foundry_run / "run-receipt.json"),
                "verification": verification["status"],
            },
            "broad_evaluation": {
                "release_id": broad_report["release_id"],
                "report_sha256": _sha256_file(broad_report_path),
                "cases_sha256": broad_report["cases_sha256"],
                "tracks": sorted(broad_report["tracks"]),
                "global_score": None,
            },
            "closed_api_or_judge_used": False,
            "external_submission_performed": False,
        }
        _write_json(staging / f"{results_path.stem}.foundry.json", sidecar)
        return sidecar

    return _atomic_output(output_dir, build)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, prog="ukrainian-data-foundry-adoption")
    commands = parser.add_subparsers(dest="command", required=True)
    trial_parser = commands.add_parser("trial", help="run the ten-minute, no-model trial")
    trial_parser.add_argument("--input", type=Path, default=EXAMPLE_PATH)
    trial_parser.add_argument("--output", type=Path, required=True)
    trial_parser.add_argument("--max-records", type=int, default=100)
    lapa = commands.add_parser("lapa", help="export faithful unmasked JSONL for pinned Lapa")
    lapa.add_argument("--foundry-run", type=Path, required=True)
    lapa.add_argument("--output", type=Path, required=True)
    lang_uk = commands.add_parser("lang-uk", help="package saved lang-uk and broad-eval results")
    lang_uk.add_argument("--results", type=Path, required=True)
    lang_uk.add_argument("--broad-report", type=Path, required=True)
    lang_uk.add_argument("--foundry-run", type=Path, required=True)
    lang_uk.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "trial":
            result = trial(input_path=args.input, output_dir=args.output, max_records=args.max_records)
        elif args.command == "lapa":
            result = export_lapa(foundry_run=args.foundry_run, output_dir=args.output)
        else:
            result = package_lang_uk(
                results_path=args.results,
                broad_report_path=args.broad_report,
                foundry_run=args.foundry_run,
                output_dir=args.output,
            )
    except (AdoptionError, OSError, foundry_cli.FoundryError, suite_cli.SuiteError) as exc:
        print(f"foundry-adoption: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
