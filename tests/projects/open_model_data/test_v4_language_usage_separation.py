"""Tests for deterministic language usage separation and masking (Issue #7886)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import pytest

import scripts.projects.open_model_data.v4_language_usage_separation as lang_sep

CONFIG_PATH = Path("data/projects/open_model_data/language/v4_language_usage_config_v1.json")
CONFIG_SCHEMA_PATH = Path("data/projects/open_model_data/contracts/v4_language_usage_config_v1.schema.json")
ITEM_SCHEMA_PATH = Path("data/projects/open_model_data/contracts/v4_language_usage_item_v1.schema.json")
RECEIPT_SCHEMA_PATH = Path("data/projects/open_model_data/contracts/v4_language_usage_receipt_v1.schema.json")


@pytest.fixture
def repo_root() -> Path:
    return Path.cwd().resolve()


def test_schema_contracts_valid() -> None:
    """All 3 language usage schemas are valid Draft 2020-12 schemas."""
    for p in [CONFIG_SCHEMA_PATH, ITEM_SCHEMA_PATH, RECEIPT_SCHEMA_PATH]:
        assert p.is_file(), f"Missing schema file: {p}"
        data = json.loads(p.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(data)


def test_analyze_span_language_usage_modern_standard() -> None:
    """Modern textbook prose is classified as modern_standard and eligible for modern view (LANG-1, LANG-2)."""
    text = "Українська мова має багату систему відмінювання іменників та прикметників."
    extraction_item = {
        "source_file": "9-klas-mystetstvo-masol-2017",
        "fidelity_assessment": {"status": "ACCEPTED_FAITHFUL"},
    }
    provenance_meta = {"period": "modern", "domain": "textbook"}
    rules = {"mask_quoted_in_modern_view": True, "mask_foreign_citations_in_modern_view": True}

    res = lang_sep.analyze_span_language_usage(
        text=text,
        extraction_item=extraction_item,
        provenance_meta=provenance_meta,
        separation_rules=rules,
    )
    assert res["functional_role"]["primary_role"] == "modern_standard"
    assert res["consumer_views"]["faithful_view"]["training_eligible"] is True
    assert res["consumer_views"]["modern_view"]["training_eligible"] is True
    assert res["consumer_views"]["modern_view"]["loss_mask_spans"] == []
    assert res["linguistic_invariants"]["verbatim_preserved"] is True


def test_analyze_span_language_usage_literary_register() -> None:
    """Poetry and literary works receive literary_register role (LANG-1)."""
    text = "Реве та стогне Дніпр широкий, сердитий вітер завива."
    extraction_item = {
        "source_file": "ukrlib-shevchenko",
        "fidelity_assessment": {"status": "ACCEPTED_FAITHFUL"},
    }
    provenance_meta = {"period": "modern", "domain": "poetry"}
    rules = {"mask_quoted_in_modern_view": True, "mask_foreign_citations_in_modern_view": True}

    res = lang_sep.analyze_span_language_usage(
        text=text,
        extraction_item=extraction_item,
        provenance_meta=provenance_meta,
        separation_rules=rules,
    )
    assert res["functional_role"]["primary_role"] == "literary_register"
    assert res["consumer_views"]["faithful_view"]["training_eligible"] is True
    assert res["consumer_views"]["modern_view"]["training_eligible"] is True


def test_analyze_span_language_usage_historical_period_excluded_from_modern() -> None:
    """Historical period passages are excluded from modern target loss (LANG-1, LANG-2)."""
    text = "Въ лѣто 6545 поиде Ярославъ на чюдь."
    extraction_item = {
        "source_file": "chronicles-povist",
        "fidelity_assessment": {"status": "ACCEPTED_FAITHFUL"},
    }
    provenance_meta = {"period": "historical", "domain": "chronicle"}
    rules = {"mask_quoted_in_modern_view": True, "mask_foreign_citations_in_modern_view": True}

    res = lang_sep.analyze_span_language_usage(
        text=text,
        extraction_item=extraction_item,
        provenance_meta=provenance_meta,
        separation_rules=rules,
    )
    assert res["functional_role"]["primary_role"] == "historical_period"
    assert res["consumer_views"]["faithful_view"]["training_eligible"] is True
    # Historical period is excluded from modern learning view to prevent contamination
    assert res["consumer_views"]["modern_view"]["training_eligible"] is False


def test_analyze_span_language_usage_quotation_and_foreign_masking() -> None:
    """Quotations and foreign citations generate explicit loss masks for modern view (LANG-2)."""
    text = "У своїй праці автор зазначає: «мова є найважливішим засобом спілкування» та посилається на Opus 4."
    extraction_item = {
        "source_file": "9-klas-mystetstvo-masol-2017",
        "fidelity_assessment": {"status": "ACCEPTED_FAITHFUL"},
    }
    provenance_meta = {"period": "modern", "domain": "textbook"}
    rules = {"mask_quoted_in_modern_view": True, "mask_foreign_citations_in_modern_view": True}

    res = lang_sep.analyze_span_language_usage(
        text=text,
        extraction_item=extraction_item,
        provenance_meta=provenance_meta,
        separation_rules=rules,
    )
    assert "quoted_metalinguistic" in res["functional_role"]["roles"]
    masks = res["consumer_views"]["modern_view"]["loss_mask_spans"]
    assert len(masks) >= 2  # At least the quoted phrase and the Latin Opus
    assert any(m["reason"] == "quotation_metalinguistic" for m in masks)
    assert any("foreign_citation" in m["reason"] for m in masks)


def test_analyze_span_language_usage_damaged_or_excluded() -> None:
    """Quarantined/damaged spans fail closed to damaged_or_excluded with zero eligibility (LANG-2)."""
    text = "Пошкоджений текст з артефактами..."
    extraction_item = {
        "source_file": "ukrlib-andrukhovych",
        "fidelity_assessment": {"status": "QUARANTINED_ANOMALOUS"},
    }
    provenance_meta = {"period": "modern", "domain": "prose"}
    rules = {"mask_quoted_in_modern_view": True, "mask_foreign_citations_in_modern_view": True}

    res = lang_sep.analyze_span_language_usage(
        text=text,
        extraction_item=extraction_item,
        provenance_meta=provenance_meta,
        separation_rules=rules,
    )
    assert res["functional_role"]["primary_role"] == "damaged_or_excluded"
    assert res["consumer_views"]["faithful_view"]["training_eligible"] is False
    assert res["consumer_views"]["modern_view"]["training_eligible"] is False


def test_verify_detects_tampered_receipt_hashes(tmp_path: Path, repo_root: Path) -> None:
    """verify() fails closed when receipt hashes are tampered."""
    tampered_out = tmp_path / "out"
    tgt_lang = tampered_out / "data/projects/open_model_data/language"
    tgt_lang.mkdir(parents=True)

    (tgt_lang / "v4_language_usage_index_v1.jsonl").write_bytes(
        Path("data/projects/open_model_data/language/v4_language_usage_index_v1.jsonl").read_bytes()
    )

    receipt_data = json.loads(
        Path("data/projects/open_model_data/language/v4_language_usage_receipt_v1.json").read_text(encoding="utf-8")
    )
    receipt_tampered = copy.deepcopy(receipt_data)
    receipt_tampered["index_sha256"] = "0" * 64
    (tgt_lang / "v4_language_usage_receipt_v1.json").write_text(json.dumps(receipt_tampered), encoding="utf-8")

    with pytest.raises(lang_sep.LanguageUsageError, match=r"Receipt index_sha256 mismatch"):
        lang_sep.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)


def test_verify_detects_prohibited_private_host_paths(tmp_path: Path, repo_root: Path) -> None:
    """verify() fails closed if private host paths appear in receipts."""
    tampered_out = tmp_path / "out"
    tgt_lang = tampered_out / "data/projects/open_model_data/language"
    tgt_lang.mkdir(parents=True)

    idx_bytes = Path("data/projects/open_model_data/language/v4_language_usage_index_v1.jsonl").read_bytes()
    idx_path = tgt_lang / "v4_language_usage_index_v1.jsonl"
    idx_path.write_bytes(idx_bytes)

    receipt_data = json.loads(
        Path("data/projects/open_model_data/language/v4_language_usage_receipt_v1.json").read_text(encoding="utf-8")
    )
    receipt_tampered = copy.deepcopy(receipt_data)
    receipt_tampered["notes"] = "failed at /home/ops/secret/corpus"
    receipt_tampered["index_sha256"] = lang_sep.sha256_file(idx_path)
    receipt_tampered["receipt_id"] = lang_sep._make_receipt_id(
        receipt_tampered["config_sha256"],
        receipt_tampered["extraction_receipt_sha256"],
        receipt_tampered["index_sha256"],
    )
    (tgt_lang / "v4_language_usage_receipt_v1.json").write_text(json.dumps(receipt_tampered), encoding="utf-8")

    with pytest.raises(
        lang_sep.LanguageUsageError, match=r"Receipt contains prohibited private or absolute host paths"
    ):
        lang_sep.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)


def test_verify_detects_out_of_bounds_mask_spans(tmp_path: Path, repo_root: Path) -> None:
    """verify() fails closed if a loss mask span extends beyond the span boundary."""
    tampered_out = tmp_path / "out"
    tgt_lang = tampered_out / "data/projects/open_model_data/language"
    tgt_lang.mkdir(parents=True)

    orig_lines = (
        Path("data/projects/open_model_data/language/v4_language_usage_index_v1.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    header = orig_lines[0]
    first_item = json.loads(orig_lines[1])
    # Set an invalid out-of-bounds mask
    first_item["consumer_views"]["modern_view"]["loss_mask_spans"] = [
        {"start_char": 0, "end_char": 9999999, "reason": "out_of_bounds"}
    ]

    idx_path = tgt_lang / "v4_language_usage_index_v1.jsonl"
    idx_path.write_text(f"{header}\n{json.dumps(first_item)}\n", encoding="utf-8")

    receipt_data = json.loads(
        Path("data/projects/open_model_data/language/v4_language_usage_receipt_v1.json").read_text(encoding="utf-8")
    )
    receipt_tampered = copy.deepcopy(receipt_data)
    receipt_tampered["index_sha256"] = lang_sep.sha256_file(idx_path)
    receipt_tampered["summary"]["total_spans_evaluated"] = 1
    receipt_tampered["receipt_id"] = lang_sep._make_receipt_id(
        receipt_tampered["config_sha256"],
        receipt_tampered["extraction_receipt_sha256"],
        receipt_tampered["index_sha256"],
    )
    (tgt_lang / "v4_language_usage_receipt_v1.json").write_text(json.dumps(receipt_tampered), encoding="utf-8")

    with pytest.raises(lang_sep.LanguageUsageError, match=r"invalid mask span"):
        lang_sep.verify(CONFIG_PATH, input_root=repo_root, output_root=tampered_out)


def test_build_and_verify_clean_exit() -> None:
    """Current committed language usage artifacts pass verify() cleanly."""
    lang_sep.verify(CONFIG_PATH)


def test_verify_passes_in_unprovisioned_ci_without_sources_db(tmp_path: Path, repo_root: Path) -> None:
    """verify() succeeds in CI environments where data/sources.db is not provisioned."""
    ci_root = tmp_path / "ci_runner"
    for sub in [
        "data/projects/open_model_data/contracts",
        "data/projects/open_model_data/language",
    ]:
        dest = ci_root / sub
        dest.mkdir(parents=True)
        for f in (repo_root / sub).iterdir():
            if f.is_file():
                (dest / f.name).write_bytes(f.read_bytes())

    assert not (ci_root / "data/sources.db").exists()

    lang_sep.verify(
        ci_root / "data/projects/open_model_data/language/v4_language_usage_config_v1.json",
        input_root=ci_root,
        output_root=ci_root,
    )
