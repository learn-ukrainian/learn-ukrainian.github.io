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


def _manifest_resource_override(monkeypatch, manifest_bytes):
    """Make the outer self-hashes coherent so the inner contract must reject.

    This changes resource bytes only. It is not a private vendor attestation.
    """
    original = resources.read_bytes
    identity = provenance._read_build_identity()
    release = json.loads(original("release_manifest.json"))
    sha = provenance._sha(manifest_bytes)
    release["provenance_sha256"] = sha
    release["files"][provenance.MANIFEST] = sha
    release_bytes = provenance._canonical(release)
    identity_bytes = (
        '"""Reproducible build identity; externally anchored by private vendor verification."""\n'
        + f"PUBLIC_COMMIT = {identity.PUBLIC_COMMIT!r}\nPACKAGE_VERSION = {identity.PACKAGE_VERSION!r}\n"
        + f"RELEASE_MANIFEST_SHA256 = {provenance._sha(release_bytes)!r}\nPROVENANCE_MANIFEST_SHA256 = {sha!r}\n"
    ).encode()
    replacements = {provenance.MANIFEST: manifest_bytes, "release_manifest.json": release_bytes, "_build_identity.py": identity_bytes}
    monkeypatch.setattr(resources, "read_bytes", lambda name: replacements.get(name, original(name)))


@pytest.mark.parametrize("mutation", [
    "relationship", "context", "descriptor", "version", "commit", "missing", "extra", "duplicate",
    "binding_missing", "binding_extra", "absolute", "traversal", "unknown_successor", "duplicate_json_key",
])
def test_inner_manifest_contract_rejects_even_with_coherent_self_hashes(mutation, monkeypatch):
    manifest = json.loads(resources.read_bytes(provenance.MANIFEST))
    occurrence = next(o for r in manifest["receipts"] for o in r["occurrences"].values() if "successor_resource" in o)
    if mutation == "relationship":
        occurrence["relationship"] = "same_code"
    elif mutation == "context":
        manifest["a3"]["receipt_binding_sha256"] = "a" * 64
    elif mutation == "descriptor":
        manifest["a3"]["algorithm_descriptor_sha256"] = "a" * 64
    elif mutation in {"version", "commit"}:
        manifest[{"version": "package_version", "commit": "public_commit"}[mutation]] = "foreign"
    elif mutation == "missing":
        manifest["receipts"].pop()
    elif mutation == "extra":
        manifest["receipts"].append({"resource": "foreign", "sha256": "a" * 64, "bindings": {}, "occurrences": {}})
    elif mutation == "duplicate":
        manifest["receipts"].append(manifest["receipts"][0])
    elif mutation == "binding_missing":
        manifest["receipts"][0]["occurrences"].pop(next(iter(manifest["receipts"][0]["occurrences"])))
    elif mutation == "binding_extra":
        manifest["receipts"][0]["occurrences"]["foreign"] = {}
    elif mutation in {"absolute", "traversal", "unknown_successor"}:
        occurrence["successor_resource"] = {"absolute": "/foreign.py", "traversal": "../foreign.py", "unknown_successor": "foreign.py"}[mutation]
    raw = provenance._canonical(manifest)
    if mutation == "duplicate_json_key":
        raw = b'{"schema":"duplicate",' + raw[1:]
    _manifest_resource_override(monkeypatch, raw)
    with pytest.raises(provenance.ProvenanceError):
        provenance.validate_package_bindings(json.loads(a3.DEFAULT_RECEIPT.read_bytes()))
