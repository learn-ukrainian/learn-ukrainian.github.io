"""Prove the Cycle 007 evidence JSON schemas are valid and actually match

what the compiler produces — not decorative artifacts sitting unused next
to the Python contract module.
"""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from scripts.projects.open_model_data import phase3_cycle007_evidence_compiler as compiler
from scripts.projects.open_model_data import phase3_cycle007_evidence_contract as contract

CONTRACTS = Path(__file__).resolve().parents[1] / "data/projects/open_model_data/contracts"
EVIDENCE_SCHEMA = CONTRACTS / "phase3_cycle007_evidence_v1.schema.json"
SIDECAR_SCHEMA = CONTRACTS / "phase3_cycle007_evidence_sidecar_v1.schema.json"
MANIFEST_SCHEMA = CONTRACTS / "phase3_cycle007_evidence_manifest_v1.schema.json"


def _validators() -> dict[Path, Draft202012Validator]:
    paths = (EVIDENCE_SCHEMA, SIDECAR_SCHEMA, MANIFEST_SCHEMA)
    schemas = {path: json.loads(path.read_text(encoding="utf-8")) for path in paths}
    registry = Registry()
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)
        registry = registry.with_resource(str(schema["$id"]), Resource.from_contents(schema))
    return {path: Draft202012Validator(schema, registry=registry) for path, schema in schemas.items()}


class SyntheticSourcesClient:
    def server_identity(self):
        return {
            "server_code_sha256": "a" * 64,
            "sources_db_sha256": "b" * 64,
            "sources_db_bytes": 1,
            "vesum_db_sha256": "c" * 64,
            "vesum_db_bytes": 1,
        }

    def verify_words(self, words):
        return {word: [{"lemma": word, "pos": "noun", "tags": ""}] for word in words}

    def check_modern_form(self, word):
        return {"found": True, "is_modern_codified": True, "has_archaic_form": False, "has_only_archaic_form": False}

    def ulif_cached(self, word):
        return {"status": "unavailable", "payload": None}

    def slovnyk_me_cached(self, word):
        return {"status": "unavailable", "payload": None}

    def grac_cached(self, word):
        return {"status": "unavailable", "payload": None}

    def search_style_guide(self, query):
        return {"status": "not_found", "hits": []}

    def search_antonenko_text(self, query):
        return {"status": "not_found", "hits": []}

    def search_ua_gec_errors(self, query):
        return {"status": "not_found", "hits": []}

    def search_heritage_cached(self, query):
        return {"status": "not_found", "hits": []}

    def check_russian_shadow(self, word):
        return {"matches_russian": False, "russian_lemma": None, "confidence": 0.0}


def _row(unit_id: str, text: str) -> dict:
    return {
        "unit_id": unit_id,
        "unit_sha256": contract.sha256_text(text),
        "family_id": "synthetic",
        "source_text": text,
        "source_text_sha256": contract.sha256_text(text),
        "frozen_locator_sha256": contract.sha256_text("locator:" + unit_id),
    }


def test_schemas_are_valid_draft_2020_12():
    for schema_path in (EVIDENCE_SCHEMA, SIDECAR_SCHEMA, MANIFEST_SCHEMA):
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)


def test_compiled_evidence_records_validate_against_evidence_schema():
    validators = _validators()
    row = _row("unit-1", "Привіт світ")
    row_evidence = compiler.compile_row_evidence(row, SyntheticSourcesClient(), source_version="v1")
    for record in row_evidence["evidence"]:
        errors = list(validators[EVIDENCE_SCHEMA].iter_errors(record))
        assert not errors, errors


def test_compiled_sidecar_validates_against_sidecar_schema(tmp_path: Path):
    validators = _validators()
    client = SyntheticSourcesClient()
    sidecar = compiler.compile_packet_sidecar(1, [_row("unit-1", "Привіт"), _row("unit-2", "Дякую")], client)
    errors = list(validators[SIDECAR_SCHEMA].iter_errors(sidecar))
    assert not errors, errors


def test_compiled_manifest_validates_against_manifest_schema(tmp_path: Path):
    validators = _validators()
    client = SyntheticSourcesClient()
    manifest = compiler.compile_sidecar_bundle([[_row("unit-1", "Привіт")]], client, tmp_path / "sidecars")
    errors = list(validators[MANIFEST_SCHEMA].iter_errors(manifest))
    assert not errors, errors


def test_evidence_schema_rejects_closed_claim_boundary_violation():
    validators = _validators()
    row = _row("unit-1", "получити")
    record = contract.build_evidence_record(
        channel="russian_shadow_suspicion",
        source_identity="check_ru_morph",
        source_version="v1",
        locator="repo:scripts/verification/check_ru_morph.py",
        query="получити",
        query_sha256=contract.sha256_text("получити"),
        status="attested",
        supports="suspicion",
        retrieval_sha256=contract.sha256_text("payload"),
        parser_id="russian-shadow-heuristic-v1",
        parser_version="1",
        row=row,
    )
    # Hand-corrupt the record the way a drifted sidecar might, bypassing the
    # contract module's own construction-time guard.
    corrupted = dict(record)
    corrupted["supports"] = "attestation"
    errors = list(validators[EVIDENCE_SCHEMA].iter_errors(corrupted))
    assert errors, "schema must reject russian_shadow_suspicion claiming attestation support"
