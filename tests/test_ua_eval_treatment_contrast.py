from __future__ import annotations

import gzip
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.open_dataset.publish import OpenDatasetPublishError, build_package, publish_open_dataset
from scripts.open_dataset.russification import (
    QuarantineError,
    _fold,
    build_contrastive_subset,
    validate_default_split,
    write_contrastive_subset,
)
from scripts.projects.ua_eval_harness.compare_treatment_runs import (
    ContrastError,
    paired_contrast,
    safety_contrast,
)

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = ROOT / "data/projects/ua_eval_harness/baselines/v1/identity.responses.jsonl"
FIXTURE = ROOT / "data/projects/ua_eval_harness/baselines/v1/fixture-rules.responses.jsonl"


def test_paired_identical_run_has_zero_delta_and_interval() -> None:
    report = paired_contrast(IDENTITY, IDENTITY, samples=25, seed=6170)
    assert report["primary"] == {"delta_f0_5": 0.0, "delta_f0_5_95_ci": [0.0, 0.0]}
    assert report["secondary"]["delta_exact_sentence_accuracy_95_ci"] == [0.0, 0.0]
    assert report["inference"]["statistical_gate_passed"] is False


def test_paired_contrast_is_antisymmetric_under_arm_swap(tmp_path: Path) -> None:
    identity_rows = IDENTITY.read_text(encoding="utf-8").splitlines()
    fixture_rows = FIXTURE.read_text(encoding="utf-8").splitlines()
    aligned_fixture = tmp_path / "aligned-fixture.jsonl"
    aligned_fixture.write_text(identity_rows[0] + "\n" + "\n".join(fixture_rows[1:]) + "\n", encoding="utf-8")
    forward = paired_contrast(IDENTITY, aligned_fixture, samples=25, seed=6170)
    reverse = paired_contrast(aligned_fixture, IDENTITY, samples=25, seed=6170)
    assert forward["primary"]["delta_f0_5"] == pytest.approx(-reverse["primary"]["delta_f0_5"])
    assert forward["primary"]["delta_f0_5_95_ci"] == pytest.approx(
        [-reverse["primary"]["delta_f0_5_95_ci"][1], -reverse["primary"]["delta_f0_5_95_ci"][0]]
    )


def test_paired_contrast_rejects_decoding_drift(tmp_path: Path) -> None:
    rows = IDENTITY.read_text(encoding="utf-8").splitlines()
    header = json.loads(rows[0])
    header["decoding"] = {"deterministic": False}
    drifted = tmp_path / "drifted.jsonl"
    drifted.write_text(json.dumps(header, sort_keys=True) + "\n" + "\n".join(rows[1:]) + "\n", encoding="utf-8")
    with pytest.raises(ContrastError, match="generation constants drift"):
        paired_contrast(IDENTITY, drifted, samples=1)


def _write_safety_run(path: Path, *, arm: str, probe_hash: str, responses: dict[str, str]) -> None:
    header = {
        "arm": arm,
        "decoding": {"do_sample": False, "temperature": 0},
        "model_revision": "842da3794eaa0b77d5f08bae87a17459d91ff475",
        "probe_artifact_sha256": probe_hash,
        "schema_version": "ua_eval_treatment_safety_responses.v1",
        "type": "safety_run",
    }
    rows = [header, *({"probe_id": probe_id, "raw_response": response} for probe_id, response in responses.items())]
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def test_safety_contrast_enforces_protected_and_no_change_gate(tmp_path: Path) -> None:
    probes = [
        {
            "gold_status": "deterministic_non_human_proxy_not_linguistic_gold",
            "kind": "clean_no_change",
            "probe_id": "probe:clean",
            "source": "Це коректне речення.",
            "source_payload_id": "source-clean",
            "source_sha256": "0" * 64,
            "type": "safety_probe",
        },
        {
            "gold_status": "deterministic_non_human_proxy_not_linguistic_gold",
            "kind": "protected_span",
            "probe_id": "probe:protected",
            "protected": {"end_char": 14, "reason": "quote", "sha256": "1" * 64, "start_char": 8, "text": "цитата"},
            "source": "Тут є цитата у контексті.",
            "source_payload_id": "source-protected",
            "source_sha256": "2" * 64,
            "type": "safety_probe",
        },
    ]
    probes_path = tmp_path / "probes.jsonl"
    probes_path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in probes), encoding="utf-8")
    probe_hash = hashlib.sha256(probes_path.read_bytes()).hexdigest()
    faithful = tmp_path / "faithful.jsonl"
    modern = tmp_path / "modern.jsonl"
    responses = {"probe:clean": "Це коректне речення.", "probe:protected": "Тут є цитата у контексті."}
    _write_safety_run(faithful, arm="faithful_cpt", probe_hash=probe_hash, responses=responses)
    _write_safety_run(modern, arm="modern_mask_cpt", probe_hash=probe_hash, responses=responses)
    report = safety_contrast(probes_path, faithful, modern)
    assert report["gate"]["passed"] is True
    failing = {"probe:clean": "Це змінене речення.", "probe:protected": "Тут немає слова у контексті."}
    _write_safety_run(modern, arm="modern_mask_cpt", probe_hash=probe_hash, responses=failing)
    report = safety_contrast(probes_path, faithful, modern)
    assert report["gate"]["passed"] is False
    assert report["modern"]["protected_span"]["failures"] == 1


@pytest.fixture
def contrast_pair() -> dict:
    """Synthetic mechanics fixture, never a Ukrainian linguistic judgment."""
    return {
        "pair_id": "pair:synthetic",
        "sense_id": "sense:synthetic",
        "distortion_type": "synthetic_distortion",
        "imposed": {
            "text": "Synthetic Soviet distortion quotation.",
            "citation": {
                "source_id": "sum11", "snapshot_id": "sum11:fixture",
                "locator": "fixture row 1", "attribution": "Synthetic Soviet source",
            },
            "sovietization_risk": 1,
            "sovietization_keywords": ["synthetic"],
        },
        "norm": {
            "text": "Synthetic authentic correction.",
            "assertion_id": "assertion:synthetic",
            "citation": {
                "source_id": "ulif", "snapshot_id": "ulif:fixture",
                "locator": "fixture row 2", "attribution": "Synthetic modern source",
            },
        },
    }


def test_russification_subset_requires_explicit_opt_in(contrast_pair) -> None:
    for value in (False, None, 1, "true"):
        with pytest.raises(QuarantineError, match="explicit_opt_in_required"):
            build_contrastive_subset([contrast_pair], opt_in=value)


def test_russification_subset_preserves_complete_pairs_without_mutating_input(contrast_pair) -> None:
    before = deepcopy(contrast_pair)
    other = deepcopy(contrast_pair)
    other["pair_id"] = "pair:another"
    rows = build_contrastive_subset([contrast_pair, other], opt_in=True)
    assert rows == [
        {"schema": "russification-contrast.v1", "opt_in": True, "for_pretraining": False,
         "soviet_colonization_context": other},
        {"schema": "russification-contrast.v1", "opt_in": True, "for_pretraining": False,
         "soviet_colonization_context": before},
    ]
    rows[1]["soviet_colonization_context"]["norm"]["text"] = "Changed copy"
    assert contrast_pair == before


@pytest.mark.parametrize("field", ["pair_id", "sense_id", "distortion_type", "imposed", "norm"])
def test_russification_subset_refuses_missing_pair_fields(contrast_pair, field) -> None:
    contrast_pair.pop(field)
    with pytest.raises(QuarantineError, match="contrast_pair_required"):
        build_contrastive_subset([contrast_pair], opt_in=True)


@pytest.mark.parametrize("side", ["imposed", "norm"])
@pytest.mark.parametrize("field", ["source_id", "snapshot_id", "locator", "attribution"])
def test_russification_subset_refuses_incomplete_citations(contrast_pair, side, field) -> None:
    contrast_pair[side]["citation"][field] = " "
    with pytest.raises(QuarantineError, match="both_citations_required"):
        build_contrastive_subset([contrast_pair], opt_in=True)


@pytest.mark.parametrize("side,source", [("imposed", "ulif"), ("norm", "sum11"), ("norm", "unregistered")])
def test_russification_subset_refuses_swapped_or_unknown_source_roles(contrast_pair, side, source) -> None:
    contrast_pair[side]["citation"]["source_id"] = source
    with pytest.raises(QuarantineError, match="contrast_source_role_mismatch"):
        build_contrastive_subset([contrast_pair], opt_in=True)


@pytest.mark.parametrize("mutation,error", [
    ("blank_identity", "contrast_identity_required"),
    ("extra_text", "contrast_pair_required"),
    ("blank_quote", "both_quoted_sides_required"),
    ("missing_citation", "both_citations_required"),
    ("risk_boolean", "contrast_evidence_required"),
    ("missing_assertion", "contrast_evidence_required"),
    ("identical_sides", "distinct_correction_required"),
    ("nested_sum11_norm", "sum11_in_default_split"),
])
def test_russification_subset_refuses_invalid_evidence(contrast_pair, mutation, error) -> None:
    if mutation == "blank_identity":
        contrast_pair["sense_id"] = " "
    elif mutation == "extra_text":
        contrast_pair["unpaired_text"] = "Unpaired Soviet quotation"
    elif mutation == "blank_quote":
        contrast_pair["imposed"]["text"] = " "
    elif mutation == "missing_citation":
        contrast_pair["norm"]["citation"] = None
    elif mutation == "risk_boolean":
        contrast_pair["imposed"]["sovietization_risk"] = True
    elif mutation == "missing_assertion":
        contrast_pair["norm"]["assertion_id"] = ""
    elif mutation == "identical_sides":
        contrast_pair["norm"]["text"] = contrast_pair["imposed"]["text"].upper()
    else:
        contrast_pair["norm"]["citation"]["attribution"] = "СУМ-11"
    with pytest.raises(QuarantineError, match=error):
        build_contrastive_subset([contrast_pair], opt_in=True)


def test_russification_subset_refuses_duplicate_identity(contrast_pair) -> None:
    with pytest.raises(QuarantineError, match="duplicate_contrast_pair"):
        build_contrastive_subset([contrast_pair, contrast_pair], opt_in=True)


@pytest.mark.parametrize("record", [
    {"source_id": "sum11"},
    {"source": "https://sum.in.ua/s/example"},
    {"source": "https://slovnyk.me/dict/sum/example"},
    {"nested": [{"source": "СУМ–11 (1970–1980)"}]},
    {"nested": {"russification_exposed": None}},
    {"soviet_colonization_context": {}},
    {"sovietization_risk": 0},
    {"schema": "russification-contrast.v1"},
    {"text": "Prefix SYNTHETIC  SOVIET\nDISTORTION QUOTATION. suffix"},
])
def test_default_split_rejects_quarantined_provenance_and_unlabelled_quotes(record) -> None:
    # Inventory frozen independently of the candidate's source tags and pair builder.
    with pytest.raises(QuarantineError, match="sum11_in_default_split"):
        validate_default_split([record], sum11_texts=["Synthetic Soviet distortion quotation."])


def test_default_split_preserves_modern_sources_and_checks_all_records() -> None:
    rows = [{"source": "СУМ-20", "text": "Authentic correction"}, {"source_id": "ulif"}]
    before = deepcopy(rows)
    assert validate_default_split(iter(rows), sum11_texts=["Synthetic Soviet distortion quotation."]) == 2
    assert rows == before
    with pytest.raises(QuarantineError, match="invalid_sum11_inventory"):
        validate_default_split(rows, sum11_texts=[""])


QUOTATION_VARIANTS = [
    "м'яка пам'ять",
    "м’яка пам’ять",
    "мʼяка памʼять",
    "м`яка пам`ять",
    "м‘яка пам‘ять",
    "м´яка пам´ять",
    "мʹяка памʹять",
    "м′яка пам′ять",
    "м'я\u0301ка па\u0301м'ять",
    "м’я\u0301ка па\u0301м’ять",
    "мʼя\u0301ка па\u0301мʼять",
    "м`я\u0301ка па\u0301м`ять",
    "м‘я\u0301ка па\u0301м‘ять",
    "м´я\u0301ка па\u0301м´ять",
    "мʹя\u0301ка па\u0301мʹять",
    "м′я\u0301ка па\u0301м′ять",
]


@pytest.mark.parametrize("text", QUOTATION_VARIANTS)
def test_quotation_fold_normalizes_apostrophes_and_stress(text) -> None:
    assert _fold(text) == "м'яка пам'ять"


def test_quotation_fold_preserves_other_diacritics_and_existing_normalization() -> None:
    assert _fold("  И\u0306  І\u0308\u0301\n") == "й ї"


@pytest.mark.parametrize("inventory", QUOTATION_VARIANTS)
@pytest.mark.parametrize("candidate", QUOTATION_VARIANTS)
def test_default_split_blocks_quotation_variants_on_both_sides(inventory, candidate) -> None:
    with pytest.raises(QuarantineError, match="sum11_in_default_split"):
        validate_default_split([{"text": f"Prefix {candidate} suffix"}], sum11_texts=[inventory])


def test_russification_writer_emits_only_separate_subset_and_card(contrast_pair, tmp_path) -> None:
    output = tmp_path / "private-subset"
    with pytest.raises(QuarantineError, match="explicit_opt_in_required"):
        write_contrastive_subset([contrast_pair], output)
    assert not output.exists()
    assert write_contrastive_subset([contrast_pair], output, opt_in=True) == 1
    assert {path.name for path in output.iterdir()} == {"russification-contrast.jsonl", "README.md"}
    rows = [json.loads(line) for line in (output / "russification-contrast.jsonl").read_text().splitlines()]
    assert rows[0]["soviet_colonization_context"] == contrast_pair
    card = (output / "README.md").read_text()
    assert "not for language-model pretraining" in card
    assert "law_art22_quotation" in card and "permissions-register.yaml" in card
    with pytest.raises(QuarantineError, match="sum11_in_default_split"):
        validate_default_split(rows)


def test_russification_writer_rejects_checkout_output_before_consuming_input(contrast_pair) -> None:
    from scripts.projects.open_model_data.review_build.errors import BuildError

    def inputs():
        pytest.fail("must refuse repository output before reading source text")
        yield contrast_pair

    with pytest.raises(BuildError, match="repository_output"):
        write_contrastive_subset(inputs(), ROOT, opt_in=True)


def test_russification_writer_leaves_existing_subset_intact_on_invalid_input(contrast_pair, tmp_path) -> None:
    output = tmp_path / "subset"
    write_contrastive_subset([contrast_pair], output, opt_in=True)
    before = (output / "russification-contrast.jsonl").read_bytes()
    contrast_pair.pop("norm")
    with pytest.raises(QuarantineError):
        write_contrastive_subset([contrast_pair], output, opt_in=True)
    assert (output / "russification-contrast.jsonl").read_bytes() == before


@pytest.mark.parametrize("path", ["dataset/default.jsonl", "extra.json", "unlabelled.txt"])
def test_default_package_rejects_copied_quotation_in_any_file(path) -> None:
    text = "Synthetic Soviet distortion quotation."
    content = text if path.endswith(".txt") else json.dumps({"text": text})
    with pytest.raises(OpenDatasetPublishError, match="quarantine gate failed"):
        build_package({}, [{"path": path, "content": content}], sum11_texts=[text])


def test_default_package_rejects_co_located_opt_in_subset(contrast_pair) -> None:
    row = build_contrastive_subset([contrast_pair], opt_in=True)[0]
    with pytest.raises(OpenDatasetPublishError, match="quarantine gate failed"):
        build_package({}, [{"path": "opt-in/contrast.jsonl", "content": json.dumps(row)}])


def test_default_package_round_trip_and_invalid_json() -> None:
    files = [{"path": "dataset/default.jsonl", "content": '{"text":"Authentic correction"}\n'}]
    package = json.loads(build_package({"version": "synthetic"}, files, sum11_texts=["Forbidden quotation"]))
    assert package["files"] == files
    assert package["manifest_version"] == "synthetic"
    with pytest.raises(OpenDatasetPublishError, match="quarantine gate failed"):
        build_package({}, [{"path": "dataset/broken.jsonl", "content": "{"}])


@pytest.mark.parametrize("separator", ["\u0085", "\u2028", "\u2029"])
def test_default_package_keeps_unicode_separators_inside_jsonl_records(separator) -> None:
    text = f"Authentic{separator}quotation"
    files = [{"path": "dataset/default.jsonl", "content": json.dumps({"text": text}, ensure_ascii=False) + "\n"}]
    assert json.loads(build_package({}, files))["files"] == files
    with pytest.raises(OpenDatasetPublishError, match="quarantine gate failed"):
        build_package({}, files, sum11_texts=["Authentic quotation"])


@pytest.mark.parametrize("extension", [".json", ".jsonl", ".JSON", ".JSONL"])
def test_default_package_decodes_escaped_provenance_before_quarantine_check(extension) -> None:
    files = [{"path": "dataset/default" + extension, "content": json.dumps({"source": "СУМ-11"})}]
    with pytest.raises(OpenDatasetPublishError, match="quarantine gate failed"):
        build_package({}, files)


def test_default_publish_refuses_missing_inventory_before_any_write(tmp_path) -> None:
    gzip_path = tmp_path / "package.gz"
    with pytest.raises(OpenDatasetPublishError, match="quotation inventory is required"):
        publish_open_dataset(dataset_root=tmp_path, gzip_path=gzip_path)
    assert not gzip_path.exists()


def test_default_publish_audits_exact_package_before_upload(tmp_path, monkeypatch) -> None:
    from scripts.open_dataset import publish

    root = tmp_path / "default"
    (root / "dataset").mkdir(parents=True)
    for name in ("README.md", "ATTRIBUTION.md", "NOTICE.md"):
        (root / name).write_text("Synthetic documentation\n")
    (root / "dataset/_metadata.json").write_text('{"version":"synthetic"}')
    shard = root / "dataset/default.jsonl"
    shard.write_text('{"text":"Unlabelled Soviet quotation"}\n')
    uploads = []
    monkeypatch.setattr(publish, "upload_release_asset", lambda path, **kw: uploads.append(path.read_bytes()))
    output = tmp_path / "default.gz"
    pointer = tmp_path / "pointer.json"
    kwargs = {"dataset_root": root, "gzip_path": output, "pointer_path": pointer,
              "sum11_texts": ["Unlabelled Soviet quotation"]}
    with pytest.raises(OpenDatasetPublishError, match="quarantine gate failed"):
        publish_open_dataset(**kwargs)
    assert uploads == [] and not output.exists() and not pointer.exists()
    shard.write_text('{"text":"Authentic correction"}\n')
    result = publish_open_dataset(**kwargs)
    assert len(uploads) == 1
    package = json.loads(gzip.decompress(uploads[0]))
    packaged_shard = next(file for file in package["files"] if file["path"] == "dataset/default.jsonl")
    assert packaged_shard["content"] == '{"text":"Authentic correction"}\n'
    assert result == json.loads(pointer.read_text())


def test_publish_cli_passes_inventory_and_rejects_wrong_inventory_shape(tmp_path, monkeypatch, capsys) -> None:
    import sys

    from scripts.open_dataset import publish

    inventory = tmp_path / "inventory.json"
    inventory.write_text('["Frozen Soviet quotation"]')
    calls = []

    def capture(**kwargs):
        calls.append(kwargs)
        return {"manifest_version": "synthetic", "generated_at": None, "file_count": 0}

    monkeypatch.setattr(publish, "publish_open_dataset", capture)
    monkeypatch.setattr(sys, "argv", ["publish", "--dry-run", "--sum11-inventory", str(inventory)])
    assert publish.main() == 0
    assert calls[0]["sum11_texts"] == ["Frozen Soviet quotation"]
    assert calls[0]["dry_run"] is True
    inventory.write_text('{}')
    assert publish.main() == 2
    assert "JSON array" in capsys.readouterr().err
    assert len(calls) == 1
