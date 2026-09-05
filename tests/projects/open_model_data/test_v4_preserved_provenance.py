"""Historical provenance is inert; runtime identity is distinct and fail-closed."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from learn_ukrainian_v4_runtime import provenance, resources, sources_handlers
from learn_ukrainian_v4_runtime import v4_a3_builder_packet as packet
from learn_ukrainian_v4_runtime import v4_a3_heldout_family_assignment as a3
from learn_ukrainian_v4_runtime.operation_auth import OperationRefused

FIXTURE = Path(__file__).parent / "fixtures/v4_pre_migration_synthetic.json"


def test_pre_migration_membership_packet_and_context_are_byte_identical():
    original = json.loads(FIXTURE.read_bytes())
    seal = json.loads(a3.DEFAULT_RECEIPT.read_bytes())
    salt = bytes.fromhex(original["synthetic_salt_hex"])
    ids = sorted(f["family_id"] for f in seal["source_family_registry"]["families"])
    assignment = a3.assign(salt, ids)
    units = packet.builder_eligible_source_unit_ids(seal, assignment["builder_eligible_family_ids"])
    current = packet._private_packet_payload(seal, assignment["builder_eligible_family_ids"], units)
    assert a3.canonical_json(assignment) == a3.canonical_json(original["assignment"])
    assert a3.canonical_json(current) == a3.canonical_json(original["packet"])
    assert a3.public_commitment_summary(salt, assignment) == original["assignment_summary"]
    assert packet.public_commitment_summary(salt, current) == original["packet_summary"]
    assert a3.receipt_binding_sha256(seal) == original["receipt_binding_sha256"]
    assert original["algorithm_descriptor_sha256"] == a3.ALGORITHM_DESCRIPTOR_SHA256


def _bindings():
    spec = json.loads(resources.read_bytes("provenance/v1/bindings.json"))
    return {
        b["path"]: b
        for receipt in spec["receipts"]
        for b in receipt["bindings"].values()
        if b["path"].startswith("scripts/")
    }


@pytest.mark.parametrize("binding", list(_bindings().values()), ids=lambda b: b["path"].rsplit("/", 1)[-1])
def test_all_seventeen_historical_implementations_are_exact_inert_blobs(binding):
    blob = "provenance/v1/blobs/sha256/" + binding["sha256"] + ".blob"
    assert hashlib.sha256(resources.read_bytes(blob)).hexdigest() == binding["sha256"]
    with pytest.raises(ValueError, match="metadata"):
        resources.read_bytes(binding["path"])
    assert len(_bindings()) == 17


def test_original_repository_validator_still_rejects_relocated_current_code(tmp_path):
    seal = json.loads(a3.DEFAULT_RECEIPT.read_bytes())
    for binding in seal["bindings"].values():
        target = tmp_path / binding["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        if binding["path"].startswith("scripts/"):
            target.write_bytes(resources.read_bytes("v4_a3_heldout_family_assignment.py"))
        else:
            target.write_bytes(resources.read_bytes(binding["path"]))
    with pytest.raises(a3.AssignmentError, match="on-disk sha256"):
        a3.validate_bindings_hash_to_disk(seal, tmp_path)


@pytest.mark.parametrize("path", ["/absolute", "../parent", "a/../b", "a//b", "./a", "a\\b"])
def test_resource_traversal_is_refused(path):
    with pytest.raises(ValueError):
        resources.read_bytes(path)


def test_duplicate_and_noncanonical_manifest_keys_refuse():
    for raw in [b'{"a":1,"a":2}\n', b'{ "a": 1 }\n', b"{}{}", b"null"]:
        with pytest.raises(provenance.ProvenanceError):
            provenance._json(raw)


class LexicalResources:
    def source_version(self):
        return "a" * 64

    def verify_word(self, word, pos):
        return [{"word_form": word, "lemma": word, "pos": "noun", "tags": "noun"}]

    def verify_words(self, words, pos):
        return {word: self.verify_word(word, pos) for word in words if word != "absent"}


@pytest.fixture
def lexical_resources(monkeypatch):
    monkeypatch.setattr(sources_handlers, "_backend", LexicalResources())


@pytest.mark.anyio
async def test_modern_form_identifiers_bind_actual_records(lexical_resources):
    _, first = await sources_handlers.handle_check_modern_form({"word": "fixture-one"})
    _, second = await sources_handlers.handle_check_modern_form({"word": "fixture-two"})
    assert first["success"] is second["success"] is True
    assert first["evidence_identifiers"] != second["evidence_identifiers"]


@pytest.mark.anyio
async def test_word_list_partial_does_not_become_supported(lexical_resources):
    _, positive = await sources_handlers.handle_verify_words({"words": ["fixture-one"]})
    _, partial = await sources_handlers.handle_verify_words({"words": ["fixture-one", "absent"]})
    assert positive["success"] is True
    assert partial["success"] is False and partial["disposition"] == "partial"
    assert partial["evidence_identifiers"] == []


@pytest.mark.anyio
async def test_unknown_source_version_refuses_evidence(lexical_resources, monkeypatch):
    monkeypatch.setattr(sources_handlers._backend, "source_version", lambda: None)
    with pytest.raises(OperationRefused, match="version unproved"):
        await sources_handlers.handle_check_modern_form({"word": "fixture-one"})


@pytest.fixture
def anyio_backend():
    return "asyncio"
