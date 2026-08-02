"""End-to-end contract tests for Foundry adoption adapters."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from scripts.projects.open_model_data import adoption_cli
from scripts.projects.ua_open_weight_eval import suite_cli


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


@pytest.fixture(scope="module")
def trial_run(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output = tmp_path_factory.mktemp("foundry-adoption") / "trial"
    receipt = adoption_cli.trial(
        input_path=adoption_cli.EXAMPLE_PATH,
        output_dir=output,
        max_records=100,
    )
    assert receipt["verification"] == "passed"
    return output


@pytest.fixture(scope="module")
def broad_report_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output = tmp_path_factory.mktemp("foundry-adoption-report")
    responses_path = output / "responses.jsonl"
    response_rows = [
        {
            "item_id": suite_cli.request_item_id(position),
            "action": case["expected"]["action"],
            "output_text": case["expected"]["accepted_texts"][0],
        }
        for position, case in enumerate(suite_cli.read_jsonl(suite_cli.CASES_PATH), 1)
    ]
    responses_path.write_text(suite_cli.encode_jsonl(response_rows), encoding="utf-8")
    report_path = output / "broad-report.json"
    suite_cli.score_saved(responses_path, report_path)
    return report_path


def _write_lang_uk_results(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "model_name": "local/open-weight-fixture",
                "n-shot": {"example_task": 0},
                "results": {
                    "example_task": {
                        "alias": "example_task",
                        "acc,none": 0.5,
                        "qg_meta": {"seed": 42},
                    }
                },
            }
        ),
        encoding="utf-8",
    )


def _tampered_foundry_run(trial_run: Path, destination: Path, mutation: str) -> Path:
    foundry_run = destination / "foundry"
    shutil.copytree(trial_run / "foundry", foundry_run)
    faithful_path = foundry_run / "faithful-source.jsonl"
    rows = _jsonl(faithful_path)
    if mutation == "wrong_schema":
        rows[0]["schema_version"] = "not_a_faithful_view"
    elif mutation == "masked":
        rows[0]["character_mask_spans"] = [{"start": 0, "end": 1}]
    elif mutation == "text_hash":
        rows[0]["text"] += " tampered"
    else:  # pragma: no cover - protects the test helper itself
        raise AssertionError(f"unknown mutation: {mutation}")
    faithful_path.write_text(suite_cli.encode_jsonl(rows), encoding="utf-8")

    receipt_path = foundry_run / "run-receipt.json"
    receipt = _json(receipt_path)
    artifact = receipt["reproduction"]["artifacts"]["faithful_source"]
    artifact["bytes"] = faithful_path.stat().st_size
    artifact["sha256"] = adoption_cli._sha256_file(faithful_path)
    receipt_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return foundry_run


def test_trial_is_no_api_reproducible_and_small(trial_run: Path) -> None:
    receipt = _json(trial_run / "trial-receipt.json")
    assert receipt["records"] == 8
    assert receipt["evaluation_requests"] == 4000
    assert receipt["network_or_api_used"] is False
    assert receipt["model_or_training_run"] is False
    assert (trial_run / "foundry/run-receipt.json").is_file()
    assert (trial_run / "ua-open-weight-eval-requests.jsonl").is_file()


def test_lapa_adapter_emits_only_unmasked_text_and_lineage(trial_run: Path, tmp_path: Path) -> None:
    output = tmp_path / "lapa"
    receipt = adoption_cli.export_lapa(foundry_run=trial_run / "foundry", output_dir=output)
    rows = _jsonl(output / "foundry-pretraining.jsonl")
    lineage = _jsonl(output / "foundry-pretraining.lineage.jsonl")
    assert receipt["rows"] == 7
    assert len(rows) == len(lineage) == 7
    assert all(set(row) == {"text"} and row["text"] for row in rows)
    assert receipt["masked_rows_exported"] == 0
    assert receipt["evaluation_rows_exported"] == 0
    assert receipt["training_or_weight_adapter_created"] is False
    assert receipt["upstream"]["commit"] == "7e695c2bb9deaa214421a657ae23c85968947305"


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("wrong_schema", "not a faithful Foundry view"),
        ("masked", "masked or rewritten row"),
        ("text_hash", "Foundry text hash mismatch"),
    ],
)
def test_lapa_adapter_rejects_ineligible_rows(
    trial_run: Path,
    tmp_path: Path,
    mutation: str,
    message: str,
) -> None:
    foundry_run = _tampered_foundry_run(trial_run, tmp_path, mutation)
    with pytest.raises(adoption_cli.AdoptionError, match=message):
        adoption_cli.export_lapa(foundry_run=foundry_run, output_dir=tmp_path / "lapa")


def test_lang_uk_adapter_validates_saved_results_and_broad_tracks(
    trial_run: Path,
    broad_report_path: Path,
    tmp_path: Path,
) -> None:
    results_path = tmp_path / "results_2026-08-02T00-00-00.json"
    _write_lang_uk_results(results_path)
    output = tmp_path / "lang-uk"
    sidecar = adoption_cli.package_lang_uk(
        results_path=results_path,
        broad_report_path=broad_report_path,
        foundry_run=trial_run / "foundry",
        output_dir=output,
    )
    assert (output / results_path.name).read_bytes() == results_path.read_bytes()
    assert sidecar["model_name"] == "local/open-weight-fixture"
    assert sidecar["broad_evaluation"]["tracks"] == sorted(suite_cli.read_json(suite_cli.CONFIG_PATH)["tracks"])
    assert sidecar["broad_evaluation"]["global_score"] is None
    assert sidecar["closed_api_or_judge_used"] is False
    assert sidecar["external_submission_performed"] is False
    assert sidecar["upstream"]["commit"] == "bd3d8431e97b3ff86e4f25381ac6b5ecccadad5f"


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("wrong_schema", "wrong broad evaluation report schema"),
        ("global_score", "broad report has a global score"),
        ("closed_judge", "closed model judge report rejected"),
        ("dropped_track", "broad report track set drift"),
        ("cases_hash", "not bound to the current frozen case file"),
    ],
)
def test_lang_uk_adapter_rejects_unbound_broad_reports(
    trial_run: Path,
    broad_report_path: Path,
    tmp_path: Path,
    mutation: str,
    message: str,
) -> None:
    report = _json(broad_report_path)
    if mutation == "wrong_schema":
        report["schema_version"] = "wrong_report_schema"
    elif mutation == "global_score":
        report["scoring"]["global_quality_score"] = 0.5
    elif mutation == "closed_judge":
        report["scoring"]["closed_model_judge_used"] = True
    elif mutation == "dropped_track":
        report["tracks"].pop(next(iter(report["tracks"])))
    elif mutation == "cases_hash":
        report["cases_sha256"] = "0" * 64
    else:  # pragma: no cover - protects the test helper itself
        raise AssertionError(f"unknown mutation: {mutation}")

    tampered_report = tmp_path / "broad-report.json"
    tampered_report.write_text(json.dumps(report), encoding="utf-8")
    results_path = tmp_path / "results_2026-08-02T00-00-00.json"
    _write_lang_uk_results(results_path)
    with pytest.raises(adoption_cli.AdoptionError, match=message):
        adoption_cli.package_lang_uk(
            results_path=results_path,
            broad_report_path=tampered_report,
            foundry_run=trial_run / "foundry",
            output_dir=tmp_path / "lang-uk",
        )


def test_lang_uk_adapter_rejects_non_numeric_metrics(tmp_path: Path) -> None:
    with pytest.raises(adoption_cli.AdoptionError, match="numeric"):
        adoption_cli._validate_lang_uk_results(
            {
                "model_name": "fixture",
                "n-shot": {"task": 0},
                "results": {"task": {"alias": "task", "acc,none": "not-a-number"}},
            }
        )


def test_lang_uk_adapter_requires_authentic_lm_eval_top_level_shape() -> None:
    with pytest.raises(adoption_cli.AdoptionError, match="missing lang-uk model_name"):
        adoption_cli._validate_lang_uk_results(
            {
                "config_general": {"model_name": "legacy-fixture"},
                "results": {"task": {"acc": 0.5}},
            }
        )


def test_lang_uk_adapter_rejects_task_set_drift() -> None:
    with pytest.raises(adoption_cli.AdoptionError, match="n-shot task set drift"):
        adoption_cli._validate_lang_uk_results(
            {
                "model_name": "fixture",
                "n-shot": {"different-task": 0},
                "results": {"task": {"alias": "task", "acc,none": 0.5}},
            }
        )


def test_lang_uk_adapter_requires_upstream_result_filename(tmp_path: Path) -> None:
    with pytest.raises(adoption_cli.AdoptionError, match="results_\\*\\.json"):
        adoption_cli.package_lang_uk(
            results_path=tmp_path / "scores.json",
            broad_report_path=tmp_path / "report.json",
            foundry_run=tmp_path / "foundry",
            output_dir=tmp_path / "output",
        )


def test_public_parser_exposes_all_three_adoption_flows() -> None:
    help_text = adoption_cli.build_parser().format_help()
    assert "trial" in help_text
    assert "lapa" in help_text
    assert "lang-uk" in help_text
