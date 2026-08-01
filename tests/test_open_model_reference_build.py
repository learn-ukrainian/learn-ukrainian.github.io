"""End-to-end safety and determinism tests for the Foundry reference build."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from scripts.projects.open_model_data import reference_build

ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


@pytest.fixture(scope="module")
def reference_runs(tmp_path_factory: pytest.TempPathFactory) -> tuple[dict[str, Any], Path, Path]:
    first = tmp_path_factory.mktemp("foundry-reference-first")
    second = tmp_path_factory.mktemp("foundry-reference-second")
    manifest_a, state_a = reference_build.build_reference(
        config_path=reference_build.DEFAULT_CONFIG,
        output_dir=first,
        profile_evidence="committed",
        input_root=None,
    )
    manifest_b, state_b = reference_build.build_reference(
        config_path=reference_build.DEFAULT_CONFIG,
        output_dir=second,
        profile_evidence="committed",
        input_root=None,
    )
    assert state_a == state_b == "not_generated_committed_receipt_mode"
    assert manifest_a == manifest_b
    return manifest_a, first, second


def test_reference_manifest_is_deterministic_and_strict(
    reference_runs: tuple[dict[str, Any], Path, Path],
) -> None:
    manifest, first, second = reference_runs
    first_path = first / "manifest.json"
    second_path = second / "manifest.json"
    reference_build.write_json(first_path, manifest)
    reference_build.write_json(second_path, manifest)
    assert first_path.read_bytes() == second_path.read_bytes()
    reference_build.validate_schema(
        manifest,
        reference_build.MANIFEST_SCHEMA,
        label="test reference manifest",
    )
    assert manifest["schema_version"] == "reference_build_manifest_v1"
    assert len(manifest["interfaces"]["schema_hashes"]) >= 10
    assert manifest["determinism"]["timestamps_omitted"] is True


def test_fixture_preserves_russian_interference_lineage(
    reference_runs: tuple[dict[str, Any], Path, Path],
) -> None:
    manifest, output_dir, _ = reference_runs
    config = reference_build.load_config(reference_build.DEFAULT_CONFIG)
    source_text = config["fixture"]["source_text"]
    incorrect = config["fixture"]["incorrect_span"]
    correction = config["fixture"]["accepted_correction"]
    candidate = read_jsonl(output_dir / "fixture/correction_candidates.jsonl")[0]
    corrected = read_jsonl(output_dir / "views/correction_instruction.jsonl")[0]
    pretraining = read_jsonl(output_dir / "views/continued_pretraining.jsonl")[0]

    assert candidate["span"]["text"] == incorrect == "звучит"
    assert candidate["span"]["language_identity"] == "russian"
    assert candidate["candidate_layers"] == ["grammar", "russian_interference"]
    assert {item["source"] for item in candidate["evidence"]} == {
        "vesum",
        "russian_morphology",
        "r2u",
        "ulif_dictua",
        "slovnyk_me",
        "heritage_dictionary",
        "ukrainian_corpus",
    }
    assert corrected["payload"]["accepted_correction"] == correction == "звучить"
    assert corrected["payload"]["target_text"] == source_text.replace(incorrect, correction)
    assert pretraining["payload"]["text"] == source_text
    assert pretraining["payload"]["character_mask_spans"] == [
        {
            "end_char": source_text.index(incorrect) + len(incorrect),
            "reason": "russian_or_mixed_language",
            "start_char": source_text.index(incorrect),
        }
    ]
    assert manifest["source_to_view_lineage"]["source_contract_admitted_records"] == 1


def test_five_views_are_disjoint_and_never_train_fixture_rows(
    reference_runs: tuple[dict[str, Any], Path, Path],
) -> None:
    manifest, output_dir, _ = reference_runs
    view_rows = {view: read_jsonl(output_dir / f"views/{view}.jsonl") for view in reference_build.VIEW_ORDER}
    all_ids: set[str] = set()
    for view, rows in view_rows.items():
        ids = {row["record_id"] for row in rows}
        assert not (all_ids & ids)
        all_ids.update(ids)
        assert {row["permitted_destination"] for row in rows} == {reference_build.VIEW_DESTINATIONS[view]}
        if view != "heldout_evaluation":
            assert all(row["eligibility"]["test_fixture"] is True for row in rows)
            assert all(row["eligibility"]["model_training_eligible"] is False for row in rows)
    assert len(view_rows["heldout_evaluation"]) == 691
    assert manifest["separation"] == {
        "evaluation_contamination_matches": 0,
        "evaluation_gold_in_non_evaluation_views": False,
        "exact_and_near_evaluation_checks_applied": True,
        "non_evaluation_text_fields_checked": 9,
        "record_id_overlap_count": 0,
        "record_ids_pairwise_disjoint": True,
        "schema_homogeneous_views": 5,
        "view_artifact_hashes_pairwise_distinct": True,
    }


def test_full_profile_denominators_and_unknowns_remain_explicit(
    reference_runs: tuple[dict[str, Any], Path, Path],
) -> None:
    manifest, _, _ = reference_runs
    profile = manifest["profile"]
    assert profile["coverage"] == {
        "complete": True,
        "expected_lexical_words": 50_298_925,
        "expected_rows": 189_150,
        "inaccessible_sources": [],
        "processed_lexical_words": 50_298_925,
        "processed_rows": 189_150,
    }
    assert profile["admission"]["training_eligible_rows"] == 0
    assert profile["admission"]["training_eligible_lexical_words"] == 0
    assert profile["morphology"]["tokens_attested"] == 41_006_903
    assert profile["morphology"]["tokens_unknown"] == 9_292_022
    assert profile["morphology"]["unknown_distinct_normalized_forms"] == 1_091_066
    assert profile["tokenizer_diagnostics"].startswith("not_run;")


def test_saved_baseline_reproduces_without_gold_or_model_generation(
    reference_runs: tuple[dict[str, Any], Path, Path],
) -> None:
    manifest, output_dir, _ = reference_runs
    baseline = manifest["baseline"]
    request_header = read_jsonl(output_dir / "baseline/generation_requests.jsonl")[0]
    assert request_header["request_count"] == 677
    assert request_header["gold_fields_supplied"] == []
    assert request_header["input_fields"] == [
        "item_id",
        "source",
        "source_sha256",
        "prompt_sha256",
    ]
    assert baseline["identity"]["edit_f0_5"] == 0.0
    assert baseline["model"]["edit_f0_5"] == pytest.approx(0.19335142469470828)
    assert baseline["model"]["headline_calque_recall"] == pytest.approx(0.09523809523809523)
    assert baseline["model"]["exact_sentence_accuracy"] == pytest.approx(0.10782865583456426)
    assert baseline["decision"] == "measurement_interface_validated"
    assert baseline["reproduction"]["identity_frozen_header_provenance_preserved"] is True
    assert baseline["gold_firewall"]["model_generation_performed"] is False


def test_observation_binds_manifest_and_denies_external_actions(
    reference_runs: tuple[dict[str, Any], Path, Path],
) -> None:
    manifest, output_dir, _ = reference_runs
    manifest_path = output_dir / "manifest-for-observation.json"
    reference_build.write_json(manifest_path, manifest)
    receipt = reference_build.observation(
        manifest_path=manifest_path,
        manifest=manifest,
        profile_evidence="committed",
        temporary_candidate_state="not_generated_committed_receipt_mode",
        wall_seconds=1.0,
    )
    assert receipt["manifest"]["sha256"] == reference_build.sha256_file(manifest_path)
    assert receipt["execution"]["completed"] is True
    assert not any(receipt["safety"].values())


def test_fresh_profile_branch_verifies_and_deletes_temporary_candidate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config = reference_build.load_config(reference_build.DEFAULT_CONFIG)
    committed_path = reference_build.resolve_path(config["full_corpus_profile"]["committed_receipt_path"])
    committed = reference_build.read_json(committed_path)
    captured: dict[str, Path] = {}

    def fake_profile_corpus(
        *,
        config_path: Path,
        input_root: Path,
        summary_output: Path,
        candidates_output: Path,
    ) -> reference_build.profile_corpus.ProfileRunResult:
        assert config_path.is_file()
        assert input_root == tmp_path
        summary_output.parent.mkdir(parents=True, exist_ok=True)
        summary_output.write_bytes(committed_path.read_bytes())
        candidates_output.write_text("{}\n", encoding="utf-8")
        captured["candidate"] = candidates_output
        return reference_build.profile_corpus.ProfileRunResult(
            summary=committed,
            summary_path=summary_output,
            candidates_path=candidates_output,
        )

    real_sha256_file = reference_build.sha256_file

    def candidate_hash(path: Path) -> str:
        if path == captured.get("candidate"):
            return committed["outputs"]["review_candidates"]["sha256"]
        return real_sha256_file(path)

    monkeypatch.setattr(reference_build.profile_corpus, "profile_corpus", fake_profile_corpus)
    monkeypatch.setattr(reference_build, "sha256_file", candidate_hash)
    output_dir = tmp_path / "reference-output"
    output_dir.mkdir()
    reproduced, state = reference_build.reproduce_profile(
        output_dir,
        config,
        profile_evidence="fresh",
        input_root=tmp_path,
    )
    assert reproduced == committed
    assert state == "deleted_after_verification"
    assert "candidate" in captured
    assert not captured["candidate"].exists()
    assert (output_dir / "profile/full_corpus_profile_v1.json").read_bytes() == committed_path.read_bytes()


def test_fresh_cli_requires_explicit_source_database_root(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as error:
        reference_build.main(
            [
                "--profile-evidence",
                "fresh",
                "--output-dir",
                str(tmp_path / "output"),
                "--manifest-output",
                str(tmp_path / "manifest.json"),
            ]
        )
    assert error.value.code == 2
