"""Behavior proof for the reviewed historical full-materialization gate."""

from __future__ import annotations

import csv
import json
import zipfile
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_historical_full_materialization as full
from scripts.projects.open_model_data import phase3_historical_materialization as base
from scripts.projects.open_model_data import phase3_historical_representation as historical

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = (
    ROOT
    / "data/projects/open_model_data/admission/phase3_historical_full_materialization_gate_v1.json"
)
GATE_SCHEMA_PATH = (
    ROOT
    / "data/projects/open_model_data/contracts/phase3_historical_full_materialization_gate_v1.schema.json"
)
RECEIPT_SCHEMA_PATH = (
    ROOT
    / "data/projects/open_model_data/contracts/phase3_historical_full_materialization_receipt_v1.schema.json"
)

UD_FIXTURE = """# newdoc = uk__fixture__1413
# lang = orv-uk
# created = 1413
# title = Fixture charter
# sent_id = uk__fixture__1413-1
# text = Во имя.
1\tВо\tво\tADP\t_\t_\t2\tcase\t_\t_
2\tимя\tимя\tNOUN\t_\tCase=Acc\t0\troot\t_\tSpaceAfter=No
3\t.\t.\tPUNCT\t_\t_\t2\tpunct\t_\t_

# newdoc = unresolved__fixture
# lang = orv
# sent_id = unresolved__fixture-1
# text = Не кандидат.
1\tНе\tне\tPART\t_\t_\t2\tadvmod\t_\t_
2\tкандидат\tкандидат\tNOUN\t_\t_\t0\troot\t_\tSpaceAfter=No
3\t.\t.\tPUNCT\t_\t_\t2\tpunct\t_\t_
"""

PLUG_HEADERS = [
    "path",
    "doc.name",
    "doc.date",
    "doc.publicationYear",
    "doc.tokenCount",
    "doc.sentenceCount",
    "doc.original",
    "doc.style",
    "doc.genre",
    "doc.source",
    "doc.orthography",
    "doc.mediaName",
    "doc.author",
    "doc.authorSex",
    "doc.authorBorn",
    "doc.authorLocCode",
    "doc.translator",
    "doc.translatorSex",
    "doc.translatorBorn",
    "doc.translatorLocCode",
    "doc.publication",
    "doc.publicationCity",
    "doc.publisher",
]


def _source_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    ud_dir = tmp_path / "ud"
    ud_dir.mkdir()
    (ud_dir / "fixture.conllu").write_text(UD_FIXTURE, encoding="utf-8")

    metadata = tmp_path / "PluG2_metadata.psv"
    rows = [
        {
            "path": "A/uk.txt",
            "doc.name": "Ukrainian fixture",
            "doc.date": "1913",
            "doc.tokenCount": "8",
            "doc.sentenceCount": "2",
            "doc.original": "UK",
            "doc.style": "FIC",
            "doc.authorLocCode": "UA-X",
        },
        {
            "path": "B/context.txt",
            "doc.name": "Excluded fixture",
            "doc.date": "1914",
            "doc.tokenCount": "3",
            "doc.sentenceCount": "1",
            "doc.original": "PL",
        },
    ]
    with metadata.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=PLUG_HEADERS,
            delimiter="|",
            quotechar='"',
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()
        writer.writerows(rows)

    archive = tmp_path / "PLuG2_texts.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as handle:
        handle.writestr("PLuG2_texts/A/uk.txt", "Перший рядок.\n\nДругий рядок.")
        handle.writestr("PLuG2_texts/B/context.txt", "Nie kandydat.")
    return ud_dir, archive, metadata


def _fixture_gate(ud_dir: Path, archive: Path, metadata: Path) -> dict[str, object]:
    return full.build_gate(
        ud_file_sha256={"fixture.conllu": base.file_sha256(ud_dir / "fixture.conllu")},
        plug2_archive_sha256=base.file_sha256(archive),
        plug2_metadata_sha256=base.file_sha256(metadata),
        ud_denominator={"documents": 1, "sentences": 1, "token_rows": 3},
        plug2_denominator={
            "documents": 2,
            "token_sum": 11,
            "uk_documents": 1,
            "non_uk_or_unknown_documents": 1,
        },
        plug2_uk_token_sum=8,
    )


def _run(tmp_path: Path, output_name: str) -> tuple[dict[str, object], Path]:
    ud_dir, archive, metadata = _source_inputs(tmp_path)
    output_parent = tmp_path / output_name
    output_parent.mkdir()
    output = output_parent / full.OUTPUT_DIRECTORY_NAME
    receipt = full.materialize_full(
        gate=_fixture_gate(ud_dir, archive, metadata),
        gate_file_sha256="a" * 64,
        ud_dir=ud_dir,
        plug2_archive=archive,
        plug2_metadata=metadata,
        private_output_dir=output,
        receipt_output=output / full.RECEIPT_FILENAME,
    )
    return receipt, output


def test_tracked_gate_is_exact_reproducible_and_fail_closed() -> None:
    gate, gate_sha256 = full.load_gate(GATE_PATH)
    assert gate == full.build_gate()
    assert gate_sha256 == full.EXPECTED_GATE_FILE_SHA256
    assert gate["execution"]["provider_calls_authorized"] is False
    assert gate["phase_boundaries"] == {
        "source_freeze_ready": False,
        "source_coverage_ready": False,
        "phase3_complete": False,
        "phase4_blocked": True,
    }
    assert gate["residuals"]["saint_sophia_current_database_reconciliation_pending"] is True


def test_runtime_bindings_are_exact_and_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    full.verify_runtime_bindings()
    monkeypatch.setattr(full, "CANARY_MATERIALIZER_SHA256", "0" * 64)
    with pytest.raises(full.HistoricalFullMaterializationError, match="runtime file drift"):
        full.verify_runtime_bindings()


def test_full_run_materializes_every_eligible_unit_and_excludes_other_languages(
    tmp_path: Path,
) -> None:
    receipt, output = _run(tmp_path, "full")
    assert receipt["mode"] == "full"
    assert receipt["selection"]["ud_selected_sentences"] == 1
    assert receipt["selection"]["plug2_selected_documents"] == 1
    assert receipt["outputs"]["ud"]["records"] == 1
    assert receipt["outputs"]["plug2"]["records"] == 2
    assert receipt["coverage"] == {
        "full_materialization_complete": True,
        "ud_eligible_set_equal": True,
        "plug2_eligible_set_equal": True,
        "non_eligible_inputs_excluded": True,
        "periodization_assignment_state": "unresolved_pending_qualified_historical_review",
    }
    assert receipt["safeguards"]["historical_forms_protected"] is True
    assert receipt["safeguards"]["modern_correction_eligible"] is False
    assert (output / full.RECEIPT_FILENAME).is_file()


def test_full_run_is_byte_deterministic(tmp_path: Path) -> None:
    ud_dir, archive, metadata = _source_inputs(tmp_path)
    gate = _fixture_gate(ud_dir, archive, metadata)
    receipts = []
    hashes = []
    for ordinal in (1, 2):
        output_parent = tmp_path / f"full-{ordinal}"
        output_parent.mkdir()
        output = output_parent / full.OUTPUT_DIRECTORY_NAME
        receipts.append(
            full.materialize_full(
                gate=gate,
                gate_file_sha256="b" * 64,
                ud_dir=ud_dir,
                plug2_archive=archive,
                plug2_metadata=metadata,
                private_output_dir=output,
                receipt_output=output / full.RECEIPT_FILENAME,
            )
        )
        hashes.append(
            {
                path.name: base.file_sha256(path)
                for path in output.iterdir()
                if path.is_file()
            }
        )
    assert receipts[0] == receipts[1]
    assert hashes[0] == hashes[1]


def test_full_run_rejects_denominator_drift_before_output(tmp_path: Path) -> None:
    ud_dir, archive, metadata = _source_inputs(tmp_path)
    gate = _fixture_gate(ud_dir, archive, metadata)
    gate["source_denominators"]["plug2"]["uk_documents"] = 2
    body = {key: value for key, value in gate.items() if key != "receipt_sha256"}
    gate["receipt_sha256"] = base.sha256_value(body)
    output = tmp_path / full.OUTPUT_DIRECTORY_NAME
    with pytest.raises(full.HistoricalFullMaterializationError, match="denominator drift"):
        full.materialize_full(
            gate=gate,
            gate_file_sha256="c" * 64,
            ud_dir=ud_dir,
            plug2_archive=archive,
            plug2_metadata=metadata,
            private_output_dir=output,
            receipt_output=output / full.RECEIPT_FILENAME,
        )
    assert not output.exists()


def test_full_run_rejects_output_inside_git_checkout(tmp_path: Path) -> None:
    ud_dir, archive, metadata = _source_inputs(tmp_path)
    checkout = tmp_path / "checkout"
    (checkout / ".git").mkdir(parents=True)
    output = checkout / full.OUTPUT_DIRECTORY_NAME
    with pytest.raises(full.HistoricalFullMaterializationError, match="inside a Git checkout"):
        full.materialize_full(
            gate=_fixture_gate(ud_dir, archive, metadata),
            gate_file_sha256="d" * 64,
            ud_dir=ud_dir,
            plug2_archive=archive,
            plug2_metadata=metadata,
            private_output_dir=output,
            receipt_output=output / full.RECEIPT_FILENAME,
        )


def test_full_run_rejects_receipt_collision(tmp_path: Path) -> None:
    ud_dir, archive, metadata = _source_inputs(tmp_path)
    output = tmp_path / full.OUTPUT_DIRECTORY_NAME
    with pytest.raises(full.HistoricalFullMaterializationError, match="receipt filename"):
        full.materialize_full(
            gate=_fixture_gate(ud_dir, archive, metadata),
            gate_file_sha256="e" * 64,
            ud_dir=ud_dir,
            plug2_archive=archive,
            plug2_metadata=metadata,
            private_output_dir=output,
            receipt_output=output / "ud-orv-uk-full.jsonl.gz",
        )
    assert not output.exists()


def test_historical_schema_validator_is_cached() -> None:
    historical._schema_validator.cache_clear()
    assert historical._schema_validator() is historical._schema_validator()


def test_new_schemas_are_closed_and_text_free() -> None:
    for path in (GATE_SCHEMA_PATH, RECEIPT_SCHEMA_PATH):
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        assert schema["additionalProperties"] is False
        serialized = json.dumps(schema, ensure_ascii=False)
        assert "source_text" not in serialized
        assert "evidence_text" not in serialized
