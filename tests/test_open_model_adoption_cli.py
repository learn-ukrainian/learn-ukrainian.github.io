"""End-to-end contract tests for Foundry adoption adapters."""

from __future__ import annotations

import json
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


def test_lang_uk_adapter_validates_saved_results_and_broad_tracks(trial_run: Path, tmp_path: Path) -> None:
    cases = suite_cli.read_jsonl(suite_cli.CASES_PATH)
    responses_path = tmp_path / "responses.jsonl"
    response_rows = [
        {
            "item_id": case["case_id"],
            "action": case["expected"]["action"],
            "output_text": case["expected"]["accepted_texts"][0],
        }
        for case in cases
    ]
    responses_path.write_text(suite_cli.encode_jsonl(response_rows), encoding="utf-8")
    broad_report_path = tmp_path / "broad-report.json"
    suite_cli.score_saved(responses_path, broad_report_path)
    results_path = tmp_path / "results_2026-08-02T00-00-00.json"
    results_path.write_text(
        json.dumps(
            {
                "config_general": {"model_name": "local/open-weight-fixture"},
                "results": {"example_task": {"acc": 0.5, "qg_meta": {"seed": 42}}},
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "lang-uk"
    sidecar = adoption_cli.package_lang_uk(
        results_path=results_path,
        broad_report_path=broad_report_path,
        foundry_run=trial_run / "foundry",
        output_dir=output,
    )
    assert (output / results_path.name).read_bytes() == results_path.read_bytes()
    assert sidecar["model_name"] == "local/open-weight-fixture"
    assert sidecar["broad_evaluation"]["tracks"] == sorted(
        suite_cli.read_json(suite_cli.CONFIG_PATH)["tracks"]
    )
    assert sidecar["broad_evaluation"]["global_score"] is None
    assert sidecar["closed_api_or_judge_used"] is False
    assert sidecar["external_submission_performed"] is False
    assert sidecar["upstream"]["commit"] == "bd3d8431e97b3ff86e4f25381ac6b5ecccadad5f"


def test_lang_uk_adapter_rejects_non_numeric_metrics(tmp_path: Path) -> None:
    with pytest.raises(adoption_cli.AdoptionError, match="numeric"):
        adoption_cli._validate_lang_uk_results(
            {
                "config_general": {"model_name": "fixture"},
                "results": {"task": {"acc": "not-a-number"}},
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
