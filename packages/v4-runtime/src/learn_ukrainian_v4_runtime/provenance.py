"""Fixed historical receipt validation and separate installed runtime identity.

No historical logical path is resolved to executable code. The only historical
byte operation is hashing the exact .blob. Private deployment anchors this
self-consistency check by verifying every wheel file against its vendor manifest.
"""

from __future__ import annotations

import hashlib
import json
import re
from importlib.resources import files

from learn_ukrainian_v4_runtime import resources

RELATIONSHIP = "runtime_successor_validating_frozen_receipt"
MANIFEST = "provenance/v1/manifest.json"
SPEC = "provenance/v1/bindings.json"


class ProvenanceError(ValueError):
    """Frozen provenance or installed current identity does not verify."""


def _require(value, reason):
    if not value:
        raise ProvenanceError(reason)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _canonical(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode() + b"\n"
    )


def _json(raw, *, canonical=True):
    def pairs(items):
        result = {}
        for key, value in items:
            _require(key not in result, "duplicate JSON key")
            result[key] = value
        return result

    try:
        value = json.loads(raw, object_pairs_hook=pairs)
        if canonical:
            _require(raw == _canonical(value), "noncanonical manifest")
        return value
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ProvenanceError("invalid canonical JSON") from exc


def _read(relative):
    try:
        return resources.read_bytes(relative)
    except (OSError, ValueError) as exc:
        raise ProvenanceError("missing or invalid package resource") from exc


def _read_build_identity():
    """Read fixed generated identity bytes without importing or executing them."""
    import ast
    from types import SimpleNamespace

    raw = _read("_build_identity.py")
    names = ("PUBLIC_COMMIT", "PACKAGE_VERSION", "RELEASE_MANIFEST_SHA256", "PROVENANCE_MANIFEST_SHA256")
    try:
        nodes = ast.parse(raw).body
        _require(len(nodes) == 5, "build identity fields")
        values = {}
        for name, node in zip(names, nodes[1:], strict=True):
            _require(
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == name,
                "build identity assignment",
            )
            values[name] = ast.literal_eval(node.value)
        canonical = (
            '"""Reproducible build identity; externally anchored by private vendor verification."""\n'
            + "".join(f"{name} = {values[name]!r}\n" for name in names)
        ).encode()
        _require(raw == canonical, "noncanonical build identity")
        return SimpleNamespace(**values)
    except (ValueError, SyntaxError, TypeError) as exc:
        raise ProvenanceError("invalid build identity resource") from exc


def verify_current_identity() -> dict:
    from learn_ukrainian_v4_runtime import __version__

    identity = _read_build_identity()

    _require(
        isinstance(identity.PUBLIC_COMMIT, str) and re.fullmatch("[a-f0-9]{40}", identity.PUBLIC_COMMIT),
        "unverified public commit",
    )
    _require(__version__ == identity.PACKAGE_VERSION, "package version mismatch")
    raw = _read("release_manifest.json")
    _require(_sha(raw) == identity.RELEASE_MANIFEST_SHA256, "release manifest digest mismatch")
    release = _json(raw)
    _require(
        set(release) == {"schema", "public_commit", "package_version", "provenance_sha256", "files"}, "release fields"
    )
    _require(
        release["schema"] == "v4-runtime-release.v1"
        and release["public_commit"] == identity.PUBLIC_COMMIT
        and release["package_version"] == identity.PACKAGE_VERSION,
        "release identity mismatch",
    )
    _require(
        release["provenance_sha256"] == identity.PROVENANCE_MANIFEST_SHA256 == _sha(_read(MANIFEST)),
        "provenance manifest digest mismatch",
    )
    expected = release["files"]
    _require(isinstance(expected, dict) and MANIFEST in expected and SPEC in expected, "incomplete release")
    for relative, digest in expected.items():
        _require(relative not in ("release_manifest.json", "_build_identity.py"), "circular release mapping")
        _require(_sha(_read(relative)) == digest, "installed file digest mismatch: " + relative)

    # Enumeration is of installed product files only, never asset discovery or
    # receipt-controlled traversal. Interpreter caches are not release inputs.
    def enumerate_files(node, prefix=""):
        found = set()
        for child in node.iterdir():
            if child.name == "__pycache__":
                continue
            name = prefix + child.name
            if child.is_dir():
                found.update(enumerate_files(child, name + "/"))
            elif child.is_file():
                found.add(name)
        return found

    actual = enumerate_files(files(resources.NAMESPACE))
    _require(
        actual == set(expected) | {"release_manifest.json", "_build_identity.py"}, "missing or extra installed files"
    )
    return {
        "public_commit": identity.PUBLIC_COMMIT,
        "package_version": identity.PACKAGE_VERSION,
        "release_manifest_sha256": identity.RELEASE_MANIFEST_SHA256,
        "provenance_manifest_sha256": identity.PROVENANCE_MANIFEST_SHA256,
        "installed_files": {
            **expected,
            "release_manifest.json": _sha(raw),
            "_build_identity.py": _sha(_read("_build_identity.py")),
        },
    }


def validate_package_bindings(receipt: dict) -> None:
    """Validate one exact built-in receipt AND the entire fixed binding closure."""
    scope = _validation_scope.get()
    fingerprint = _sha(_canonical(receipt))
    if scope is not None and fingerprint in scope:
        return
    identity = verify_current_identity()
    manifest = _json(_read(MANIFEST))
    spec = _json(_read(SPEC))
    _require(
        set(manifest) == {"schema", "package_version", "public_commit", "historical_source_commit", "receipts", "a3"},
        "provenance fields",
    )
    _require(
        manifest["schema"] == "v4-sealed-provenance.v1"
        and manifest["public_commit"] == identity["public_commit"]
        and manifest["package_version"] == identity["package_version"],
        "provenance identity",
    )
    _require(
        spec["schema"] == "v4-frozen-bindings.v1"
        and manifest["historical_source_commit"] == spec["source_commit"] == "8a96f439f4ce11d08d4c154af860eee3eded3d7c",
        "historical source identity",
    )
    expected = {item["resource"]: item for item in spec["receipts"]}
    _require(len(expected) == len(spec["receipts"]), "duplicate frozen receipt")
    observed = set()
    matched = False
    historical = set()
    direct = set()
    for item in manifest["receipts"]:
        _require(set(item) == {"resource", "sha256", "bindings", "occurrences"}, "receipt manifest fields")
        name = item["resource"]
        _require(name in expected and name not in observed, "unknown or duplicate receipt")
        observed.add(name)
        frozen = expected[name]
        _require({k: item[k] for k in ("resource", "sha256", "bindings")} == frozen, "frozen receipt mapping mismatch")
        raw = _read(name)
        _require(_sha(raw) == item["sha256"], "raw receipt digest mismatch")
        actual = _json(raw, canonical=False)
        _require(actual["bindings"] == item["bindings"], "complete receipt binding set mismatch")
        if actual == receipt:
            matched = True
        _require(set(item["occurrences"]) == set(actual["bindings"]), "missing or extra binding occurrence")
        for key, binding in actual["bindings"].items():
            resources.safe_relative(binding["path"])
            occurrence = item["occurrences"][key]
            common = {
                "binding": binding,
                "package_version": identity["package_version"],
                "public_commit": identity["public_commit"],
            }
            if binding["path"].startswith("scripts/"):
                _require(
                    binding["path"].startswith("scripts/projects/open_model_data/"), "unknown historical namespace"
                )
                module = binding["path"].rsplit("/", 1)[-1]
                blob = "provenance/v1/blobs/sha256/" + binding["sha256"] + ".blob"
                current = {
                    **common,
                    "historical_resource": blob,
                    "historical_sha256": binding["sha256"],
                    "successor_resource": module,
                    "successor_sha256": _sha(_read(module)),
                    "relationship": RELATIONSHIP,
                }
                _require(occurrence == current, "historical successor relationship mismatch")
                _require(_sha(_read(blob)) == binding["sha256"], "historical blob digest mismatch")
                historical.add(blob)
            else:
                _require(binding["path"].startswith("data/projects/open_model_data/"), "unknown data binding")
                _require(
                    occurrence
                    == {
                        **common,
                        "resource": binding["path"],
                        "sha256": binding["sha256"],
                        "relationship": "frozen_data_resource",
                    },
                    "direct binding mismatch",
                )
                _require(_sha(_read(binding["path"])) == binding["sha256"], "direct resource digest mismatch")
                direct.add(binding["path"])
    _require(observed == set(expected) and matched, "unknown receipt or incomplete manifest")
    _require(len(historical) == 17 and len(direct) == 16, "incomplete provenance closure")
    from learn_ukrainian_v4_runtime import v4_a3_heldout_family_assignment as a3

    seal_raw = _read("data/projects/open_model_data/admission/dataset_v4_a3_heldout_source_family_seal_receipt_v1.json")
    descriptor = _sha(a3.canonical_json(a3.ALGORITHM_DESCRIPTOR).encode())
    _require(
        manifest["a3"]
        == {
            "seal_sha256": _sha(seal_raw),
            "receipt_binding_sha256": a3.receipt_binding_sha256(_json(seal_raw, canonical=False)),
            "algorithm_descriptor_sha256": descriptor,
        },
        "A3 sealed context or descriptor mismatch",
    )
    _require(
        descriptor
        == a3.ALGORITHM_DESCRIPTOR_SHA256
        == "b2abbb8e45f60abb098b8976dec7e7f2b4668137f55bfab8eee3999bd65a1928",
        "A3 frozen descriptor changed",
    )

    if scope is not None:
        # All built-in receipts and their complete bindings were verified above.
        scope.update(
            {_sha(_canonical(_json(_read(item["resource"]), canonical=False))): True for item in manifest["receipts"]}
        )


def validate_receipt_bindings(receipt, root, repository_validator, require):
    """Dispatch by explicit resource type; repository validation stays strict."""
    if type(root) is resources.PackageResource and not root.relative:
        try:
            validate_package_bindings(receipt)
        except ProvenanceError as exc:
            require(False, str(exc))
    else:
        repository_validator(receipt, root)


# One immutable installed release is verified once per nested validation call
# tree. The context ends before the next operation; policy is never cached.
# This avoids re-hashing the entire release for every node of A13's upstream DAG.
from contextvars import ContextVar
from functools import wraps

_validation_scope = ContextVar("v4_package_validation_scope", default=None)


def validation_session(function):
    @wraps(function)
    def validate(*args, **kwargs):
        if _validation_scope.get() is not None:
            return function(*args, **kwargs)
        token = _validation_scope.set({})
        try:
            return function(*args, **kwargs)
        finally:
            _validation_scope.reset(token)

    return validate
