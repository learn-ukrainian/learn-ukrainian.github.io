"""Unicode boundary regressions through real open_model_data readers (#9556)."""

import pytest
from jsonl_reader_cases import reader_case


@pytest.mark.parametrize(
    "module, function, site",
    [
        ("scripts.projects.open_model_data.adoption_cli", "_read_jsonl", 62),
        ("scripts.projects.open_model_data.correction_factory", "read_jsonl", 128),
        ("scripts.projects.open_model_data.correction_protection_consumer", "_release_bundle", 116),
        ("scripts.projects.open_model_data.correction_protection_consumer", "public_bundle", 203),
        ("scripts.projects.open_model_data.inventory_existing_assets", "_read_jsonl_records", 813),
        ("scripts.projects.open_model_data.inventory_existing_assets", "_jsonl_record_count", 861),
        ("scripts.projects.open_model_data.inventory_existing_assets", "load_fixture_records", 1399),
        ("scripts.projects.open_model_data.reference_build", "read_jsonl", 101),
        ("scripts.projects.open_model_data.train_and_eval_real_model", "_read_jsonl_records", 206),
        ("scripts.projects.open_model_data.train_and_eval_real_model", "_read_jsonl_records", 207),
        ("scripts.projects.open_model_data.train_and_eval_real_model", "_read_jsonl_records", 243),
        ("scripts.projects.open_model_data.v4_differential_soviet_miner", "_jsonl_record_count", 855),
        ("scripts.projects.open_model_data.v4_language_usage_separation", "_update_index_header", 477),
        ("scripts.projects.open_model_data.v4_native_extraction_validation", "_update_index_header", 519),
        ("scripts.projects.open_model_data.v4_production_shards_assembly", "_jsonl_bytes", 172),
        ("scripts.projects.open_model_data.v4_provenance_restoration", "_load_ledger", 169),
        ("scripts.projects.open_model_data.v5_build_dialect_historical_protection_suite", "_load_existing_suite", 156),
        ("scripts.projects.open_model_data.v5_build_dialect_historical_protection_suite", "mine_lemko_from_seeds", 172),
        ("scripts.projects.open_model_data.v5_build_dialect_historical_protection_suite", "mine_oes_from_seeds", 281),
        (
            "scripts.projects.open_model_data.v5_build_dialect_historical_protection_suite",
            "mine_middle_ua_from_seeds",
            594,
        ),
        ("scripts.projects.open_model_data.v5_dialect_protection_evaluator", "_read_jsonl_records", 521),
        ("scripts.projects.open_model_data.v5_dialect_protection_evaluator", "_read_predictions", 530),
        ("scripts.projects.open_model_data.v5_evaluation_harness", "_read_jsonl_records", 1588),
        ("scripts.projects.open_model_data.v5_evaluation_harness", "_read_jsonl_records", 1591),
        ("scripts.projects.open_model_data.v5_mine_dialect_corpus", "build_sft_dialect_dataset", 1099),
        ("scripts.projects.open_model_data.v5_mine_dialect_corpus", "_read_jsonl_records", 1301),
        ("scripts.projects.open_model_data.v5_mine_dialect_corpus", "_read_jsonl_records", 1541),
        ("scripts.projects.open_model_data.v5_mine_dialect_corpus", "_read_jsonl_records", 1546),
        ("scripts.projects.open_model_data.v5_mine_kyivan_rus_epigraphy", "build_sft_dataset", 879),
        ("scripts.projects.open_model_data.v5_pretraining_contradiction_audit", "run_pretraining_audit", 953),
        ("scripts.projects.open_model_data.v5_pretraining_contradiction_audit", "run_pretraining_audit", 1010),
        ("scripts.projects.open_model_data.validate_source_records", "load_records", 81),
        ("scripts.projects.open_model_data.vesum_unattested_sample", "_phase1_rows", 146),
    ],
    ids=lambda value: str(value),
)
@pytest.mark.parametrize("ending", ["\n", "\r\n", ""], ids=["LF", "CRLF", "unterminated"])
def test_reader_preserves_unicode_separators(module, function, site, ending, tmp_path, monkeypatch):
    reader_case(module, function, site, ending, tmp_path, monkeypatch)
