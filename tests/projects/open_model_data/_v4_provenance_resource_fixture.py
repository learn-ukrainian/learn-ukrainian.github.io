"""Coherent, isolated synthetic trust resources for private-algorithm unit tests.

Only resource bytes change. Production code, validators, canonical observations,
authentication and historical blobs are never replaced. This is not evidence
that a synthetic resource set is the deployed/public release. Release-wheel
proofs separately verify the unmodified, committed product resources.
"""

from __future__ import annotations

import copy
import json
from contextlib import contextmanager
from contextvars import ContextVar
from unittest.mock import patch

from learn_ukrainian_v4_runtime import provenance, resources
from learn_ukrainian_v4_runtime import v4_a3_heldout_family_assignment as a3

ACTIVE = ContextVar("synthetic_provenance_resources", default=None)
SEAL = "data/projects/open_model_data/admission/dataset_v4_a3_heldout_source_family_seal_receipt_v1.json"


class SyntheticResources:
    def __init__(self, read):
        self.original = read
        self.overrides = {}

    def read(self, name):
        return self.overrides[name] if name in self.overrides else self.original(name)

    def install_seal(self, receipt, fixture_root):
        release = json.loads(self.original("release_manifest.json"))
        identity = provenance._read_build_identity()
        raw = {name: self.original(name) for name in release["files"]}
        for name in raw:
            candidate = fixture_root / name
            if name.startswith("data/projects/open_model_data/") and candidate.is_file():
                raw[name] = candidate.read_bytes()
        raw[SEAL] = provenance._canonical(receipt)
        spec = json.loads(self.original(provenance.SPEC))
        # The fixed receipt list supplies this finite DAG. Strings in arbitrary
        # objects never discover a path, and historical implementations stay exact.
        for _ in range(len(spec["receipts"]) + 1):
            changed = False
            for item in spec["receipts"]:
                if item["resource"] == SEAL:
                    continue
                obj = json.loads(raw[item["resource"]])
                for binding in obj["bindings"].values():
                    path = binding["path"]
                    if path in raw:
                        expected = provenance._sha(raw[path])
                        if binding["sha256"] != expected:
                            binding["sha256"] = expected
                            changed = True
                if changed:
                    raw[item["resource"]] = provenance._canonical(obj)
            if not changed:
                break
        else:
            raise AssertionError("synthetic binding DAG did not converge")
        for item in spec["receipts"]:
            obj = json.loads(raw[item["resource"]])
            item["sha256"] = provenance._sha(raw[item["resource"]])
            item["bindings"] = obj["bindings"]
        raw[provenance.SPEC] = provenance._canonical(spec)
        manifest = json.loads(self.original(provenance.MANIFEST))
        manifest["receipts"] = []
        for item in spec["receipts"]:
            entry = copy.deepcopy(item)
            entry["occurrences"] = {}
            for name, binding in item["bindings"].items():
                common = {
                    "binding": binding,
                    "package_version": identity.PACKAGE_VERSION,
                    "public_commit": identity.PUBLIC_COMMIT,
                }
                if binding["path"].startswith("scripts/"):
                    successor = binding["path"].rsplit("/", 1)[1]
                    occurrence = {
                        **common,
                        "historical_resource": "provenance/v1/blobs/sha256/" + binding["sha256"] + ".blob",
                        "historical_sha256": binding["sha256"],
                        "successor_resource": successor,
                        "successor_sha256": provenance._sha(raw[successor]),
                        "relationship": provenance.RELATIONSHIP,
                    }
                else:
                    occurrence = {
                        **common,
                        "resource": binding["path"],
                        "sha256": binding["sha256"],
                        "relationship": "frozen_data_resource",
                    }
                entry["occurrences"][name] = occurrence
            manifest["receipts"].append(entry)
        sealed = json.loads(raw[SEAL])
        manifest["a3"] = {
            "seal_sha256": provenance._sha(raw[SEAL]),
            "receipt_binding_sha256": a3.receipt_binding_sha256(sealed),
            "algorithm_descriptor_sha256": a3.ALGORITHM_DESCRIPTOR_SHA256,
        }
        raw[provenance.MANIFEST] = provenance._canonical(manifest)
        release["provenance_sha256"] = provenance._sha(raw[provenance.MANIFEST])
        release["files"] = {name: provenance._sha(value) for name, value in raw.items()}
        raw["release_manifest.json"] = provenance._canonical(release)
        raw["_build_identity.py"] = (
            '"""Reproducible build identity; externally anchored by private vendor verification."""\n'
            + f"PUBLIC_COMMIT = {identity.PUBLIC_COMMIT!r}\nPACKAGE_VERSION = {identity.PACKAGE_VERSION!r}\n"
            + f"RELEASE_MANIFEST_SHA256 = {provenance._sha(raw['release_manifest.json'])!r}\nPROVENANCE_MANIFEST_SHA256 = {release['provenance_sha256']!r}\n"
        ).encode()
        self.overrides = raw
        for name, value in raw.items():
            candidate = fixture_root / name
            if name.startswith("data/projects/open_model_data/") and candidate.is_file():
                candidate.write_bytes(value)
        return sealed


@contextmanager
def synthetic_resources():
    if ACTIVE.get() is not None:
        yield ACTIVE.get()
        return
    bundle = SyntheticResources(resources.read_bytes)
    token = ACTIVE.set(bundle)
    try:
        with patch.object(resources, "read_bytes", bundle.read):
            yield bundle
    finally:
        ACTIVE.reset(token)


def synthetic_wheel(base_wheel, destination):
    """Materialize test resource bytes before execution, with an exact RECORD.

    The base wheel is independently built from committed code. This owned
    derivative is visibly marked as a fixture and never used for release proof.
    """
    import base64
    import csv
    import hashlib
    import io
    import zipfile

    bundle = ACTIVE.get()
    assert bundle is not None and bundle.overrides
    with zipfile.ZipFile(base_wheel) as archive:
        entries = {item.filename: archive.read(item) for item in archive.infolist() if not item.is_dir()}
    prefix = "learn_ukrainian_v4_runtime/"
    for name, value in bundle.overrides.items():
        assert prefix + name in entries
        entries[prefix + name] = value
    metadata = next(name for name in entries if name.endswith(".dist-info/METADATA"))
    lines = entries[metadata].decode().splitlines()
    entries[metadata] = (
        "\n".join(
            "Summary: Synthetic resource fixture; not a deployment release" if line.startswith("Summary:") else line
            for line in lines
        )
        + "\n"
    ).encode()
    record = next(name for name in entries if name.endswith(".dist-info/RECORD"))
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    for name, raw in sorted(entries.items()):
        if name != record:
            writer.writerow(
                [
                    name,
                    "sha256=" + base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).decode().rstrip("="),
                    len(raw),
                ]
            )
    writer.writerow([record, "", ""])
    entries[record] = stream.getvalue().encode()
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw)
    return destination
