"""Installed package resources are verified at each separate operation."""

from __future__ import annotations

import json

import pytest
from learn_ukrainian_v4_runtime import provenance, resources
from learn_ukrainian_v4_runtime import v4_a3_heldout_family_assignment as a3


@pytest.fixture(autouse=True)
def verified_pristine_package():
    provenance.verify_current_identity()


def test_actual_release_and_fixed_manifest_validate():
    identity = provenance.verify_current_identity()
    assert identity["public_commit"] and len(identity["installed_files"]) > 17
    provenance.validate_package_bindings(json.loads(a3.DEFAULT_RECEIPT.read_bytes()))


def _historical_resources():
    spec = json.loads(resources.read_bytes(provenance.SPEC))
    return sorted(
        {
            "provenance/v1/blobs/sha256/" + b["sha256"] + ".blob"
            for r in spec["receipts"]
            for b in r["bindings"].values()
            if b["path"].startswith("scripts/")
        }
    )


@pytest.mark.parametrize(
    "target",
    [
        *_historical_resources(),
        provenance.MANIFEST,
        provenance.SPEC,
        *sorted(name for name in provenance.verify_current_identity()["installed_files"] if name.endswith(".py")),
        "LICENSE-CONTENT.md",
        "data/projects/open_model_data/trust/v4_trust_policy_v1.json",
        "data/projects/open_model_data/trust/v4_review_rubric_v1.txt",
    ],
)
def test_each_historical_blob_and_current_trust_input_tamper_refuses(target, monkeypatch):
    original = resources.read_bytes

    def read(name):
        value = original(name)
        return value + b" " if name == target else value

    monkeypatch.setattr(resources, "read_bytes", read)
    with pytest.raises(provenance.ProvenanceError):
        provenance.validate_package_bindings(json.loads(a3.DEFAULT_RECEIPT.read_bytes()))


@pytest.mark.parametrize(
    "field",
    [
        "relationship",
        "public_commit",
        "package_version",
        "successor_resource",
        "successor_sha256",
        "historical_resource",
        "historical_sha256",
    ],
)
def test_relationship_field_tamper_is_rejected(field, monkeypatch):
    original = resources.read_bytes
    manifest = json.loads(original(provenance.MANIFEST))
    occurrence = next(o for r in manifest["receipts"] for o in r["occurrences"].values() if "successor_resource" in o)
    occurrence[field] = "foreign"

    def read(name):
        return provenance._canonical(manifest) if name == provenance.MANIFEST else original(name)

    monkeypatch.setattr(resources, "read_bytes", read)
    with pytest.raises(provenance.ProvenanceError):
        provenance.validate_package_bindings(json.loads(a3.DEFAULT_RECEIPT.read_bytes()))


@pytest.mark.parametrize("field", ["seal_sha256", "receipt_binding_sha256", "algorithm_descriptor_sha256"])
def test_sealed_context_tamper_is_rejected(field, monkeypatch):
    original = resources.read_bytes
    manifest = json.loads(original(provenance.MANIFEST))
    manifest["a3"][field] = "b" * 64
    monkeypatch.setattr(
        resources,
        "read_bytes",
        lambda name: provenance._canonical(manifest) if name == provenance.MANIFEST else original(name),
    )
    with pytest.raises(provenance.ProvenanceError):
        provenance.validate_package_bindings(json.loads(a3.DEFAULT_RECEIPT.read_bytes()))


@pytest.mark.parametrize("mutation", ["remove", "add", "duplicate"])
def test_missing_extra_or_duplicate_receipt_mapping_refuses(mutation, monkeypatch):
    original = resources.read_bytes
    manifest = json.loads(original(provenance.MANIFEST))
    if mutation == "remove":
        manifest["receipts"].pop()
    elif mutation == "duplicate":
        manifest["receipts"].append(manifest["receipts"][0])
    else:
        manifest["receipts"].append({"resource": "foreign"})
    monkeypatch.setattr(
        resources,
        "read_bytes",
        lambda name: provenance._canonical(manifest) if name == provenance.MANIFEST else original(name),
    )
    with pytest.raises(provenance.ProvenanceError):
        provenance.validate_package_bindings(json.loads(a3.DEFAULT_RECEIPT.read_bytes()))
