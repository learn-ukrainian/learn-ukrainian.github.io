"""Subset verified artifacts using only their pinned register and record bytes."""

import json
import os
import re
from collections import defaultdict
from pathlib import Path

import yaml

from .build import _jsonl
from .contract import canonical, digest
from .errors import BuildError, require
from .output import OutputGuard

FILTER_KEYS = frozenset({"source_id", "licence_ref", "permission_status"})


def parse_filters(criteria: list[str]) -> dict[str, list[str]]:
    """Values within a key are OR; keys are AND for inclusion."""
    result = defaultdict(set)
    for criterion in criteria:
        key, separator, value = criterion.partition("=")
        require(separator == "=" and key in FILTER_KEYS, "export_filter")
        require(bool(value) and value == value.strip(), "export_filter_value")
        result[key].add(value)
    return {key: sorted(values) for key, values in sorted(result.items())}


def _json(content: bytes):
    try:
        return json.loads(content)
    except (ValueError, UnicodeError):
        raise BuildError("export_input") from None


def _verified_files(source: OutputGuard) -> tuple[dict, dict[str, bytes], str]:
    """Check a successful verify receipt and every manifest-pinned artifact."""
    raw = source.read("manifest.json")
    manifest = _json(raw)
    sha = digest(raw)
    receipt = _json(source.read("verification.json"))
    require(
        isinstance(receipt, dict)
        and set(receipt) == {"schema", "build_sha256", "files"}
        and receipt["schema"] == "omd-review-verification.v1"
        and receipt["build_sha256"] == sha,
        "export_unverified",
    )
    require(isinstance(manifest, dict) and manifest.get("schema") == "omd-review-build.v1", "export_input")
    pins = manifest.get("pins", {})
    require(isinstance(pins, dict), "export_input")
    components = pins.get("components")
    require(
        isinstance(components, list)
        and bool(components)
        and all(isinstance(c, str) and re.fullmatch(r"C(?:[1-79]|6[ab])", c) for c in components)
        and len(set(components)) == len(components),
        "export_input",
    )
    hashes = manifest.get("files")
    required = {"permissions-register.yaml", "licence-notices.jsonl", "accounting.json"}
    required.update(f"{c}/records.jsonl" for c in components)
    require(isinstance(hashes, dict) and required <= hashes.keys(), "export_input")
    verified_hashes = receipt["files"]
    require(
        isinstance(verified_hashes, dict)
        and set(verified_hashes) == set(hashes) | {"manifest.json", "private-manifest.json"}
        and verified_hashes["manifest.json"] == sha
        and all(verified_hashes[name] == expected for name, expected in hashes.items()),
        "export_unverified",
    )
    files = {}
    for name, expected in sorted(verified_hashes.items()):
        require(isinstance(expected, str) and bool(re.fullmatch(r"[0-9a-f]{64}", expected)), "export_input")
        OutputGuard._parts(name)
        # OutputGuard.read normally creates intermediate private directories.
        # A damaged input build must remain untouched rather than be repaired.
        require((source.path / name).is_file(), "artifact_mismatch")
        content = source.read(name)
        require(digest(content) == expected, "artifact_mismatch")
        files[name] = content
    require(digest(files["permissions-register.yaml"]) == pins.get("register"), "artifact_mismatch")
    return manifest, files, sha


def _sources(content: bytes) -> dict[str, dict]:
    try:
        register = yaml.safe_load(content)
    except (yaml.YAMLError, UnicodeError):
        raise BuildError("export_register") from None
    require(isinstance(register, dict) and isinstance(register.get("sources"), list), "export_register")
    sources = {}
    for entry in register["sources"]:
        require(isinstance(entry, dict), "export_register")
        source_id = entry.get("id")
        require(isinstance(source_id, str) and bool(source_id) and source_id not in sources, "export_register")
        sources[source_id] = entry
    return sources


def _fields(provenance: dict, sources: dict[str, dict]) -> dict:
    """Source identity and licence reference must resolve exactly in the snapshot."""
    require(isinstance(provenance, dict), "export_provenance")
    source_id = provenance.get("source_id")
    require(isinstance(source_id, str) and source_id in sources, "export_provenance")
    entry = sources[source_id]
    try:
        licence = entry["terms"]["licence"]["name"]
    except (KeyError, TypeError):
        raise BuildError("export_register") from None
    require(isinstance(licence, str) and bool(licence.strip()), "export_register")
    licence_ref = f"permissions-register.yaml#{source_id}; {licence}"
    require(provenance.get("licence_ref") == licence_ref, "export_provenance")
    require(
        isinstance(provenance.get("attribution"), str) and bool(provenance["attribution"].strip()), "export_provenance"
    )
    return {"source_id": source_id, "licence_ref": licence_ref, "permission_status": entry.get("permission_status")}


def _validate_filters(filters: dict[str, dict[str, list[str]]], sources: dict[str, dict]) -> None:
    """Every requested value must be recorded in the pinned register."""
    allowed = {}
    for key in sorted({key for group in filters.values() for key in group}):
        values = set()
        for source_id, entry in sources.items():
            if key == "source_id":
                value = source_id
            elif key == "licence_ref":
                try:
                    licence = entry["terms"]["licence"]["name"]
                except (KeyError, TypeError):
                    raise BuildError("export_register") from None
                require(isinstance(licence, str) and bool(licence.strip()), "export_register")
                value = f"permissions-register.yaml#{source_id}; {licence}"
            else:
                value = entry.get("permission_status")
            require(isinstance(value, str) and bool(value.strip()), "export_register")
            values.add(value)
        allowed[key] = values
    for group in filters.values():
        for key, values in group.items():
            require(set(values) <= allowed[key], "export_filter_unknown")


def export_build(
    build: Path, out: OutputGuard, *, include: list[str] | None = None, exclude: list[str] | None = None
) -> dict:
    """Export whole records; overlapping or nonempty destinations fail closed."""
    filters = {"include": parse_filters(include or []), "exclude": parse_filters(exclude or [])}
    build = build.absolute()
    require(build.is_dir(), "export_input")
    resolved = build.resolve()
    require(
        resolved != out.path and resolved not in out.path.parents and out.path not in resolved.parents,
        "export_overlap",
    )
    require(not os.listdir(out.fd), "export_output_not_empty")
    with OutputGuard(build) as source:
        manifest, files, sha = _verified_files(source)
    sources = _sources(files["permissions-register.yaml"])
    _validate_filters(filters, sources)
    accounting = {"components": {}, "sources": {}}
    notices = set()
    exported = {}
    for component in sorted(manifest["pins"]["components"]):
        name = f"{component}/records.jsonl"
        kept = []
        counts = {"kept": 0, "dropped": 0, "counted": 0}
        # Split only physical LF, preserving CRLF, Unicode separators and a
        # possible final unterminated line. Never serialize records again.
        lines = files[name].split(b"\n")
        for index, line in enumerate(lines):
            if index == len(lines) - 1 and not line:
                continue
            record = _json(line)
            require(isinstance(record, dict) and record.get("component") == component, "export_input")
            provenance = record.get("provenance")
            require(isinstance(provenance, dict) and bool(provenance), "export_provenance")
            entries = list(provenance.values())
            fields = [_fields(entry, sources) for entry in entries]
            for group in filters.values():
                require(
                    all(isinstance(f[key], str) and bool(f[key]) for f in fields for key in group), "export_register"
                )
            passes = all(
                all(f[key] in values for key, values in filters["include"].items())
                and not any(f[key] in values for key, values in filters["exclude"].items())
                for f in fields
            )
            outcome = "kept" if passes else "dropped"
            counts[outcome] += 1
            counts["counted"] += 1
            for source_id in sorted({f["source_id"] for f in fields}):
                source_counts = accounting["sources"].setdefault(source_id, {"kept": 0, "dropped": 0, "counted": 0})
                source_counts[outcome] += 1
                source_counts["counted"] += 1
            if passes:
                kept.append(line + (b"\n" if index < len(lines) - 1 else b""))
                notices.update((p["source_id"], p["licence_ref"], p["attribution"]) for p in entries)
        require(counts["counted"] == manifest["accounting"][component]["accepted"], "export_accounting")
        accounting["components"][component] = counts
        exported[name] = b"".join(kept)
    exported["licence-notices.jsonl"] = _jsonl(
        [dict(zip(("source_id", "licence_ref", "attribution"), notice, strict=True)) for notice in sorted(notices)]
    )
    exported["permissions-register.yaml"] = files["permissions-register.yaml"]
    exported["accounting.json"] = canonical(accounting) + b"\n"
    exported["README.md"] = (
        b"# Private review export\n\nStatus: review_only; no training-readiness claim.\n"
        b"Records retain their input bytes. Source counts count records once per cited source;\n"
        b"mixed-source records contribute to multiple source totals. Licence notices cover kept records only.\n"
    )
    export_manifest = {
        "schema": "omd-review-export.v1",
        "status": "review_only",
        "input_build_sha256": sha,
        "register_sha256": manifest["pins"]["register"],
        "filter": filters,
        "accounting": accounting,
        "files": {name: digest(content) for name, content in sorted(exported.items())},
    }
    exported["manifest.json"] = canonical(export_manifest) + b"\n"
    for name, content in sorted(exported.items()):
        out.write(name, content)
    return {
        "status": "exported",
        "export_sha256": digest(exported["manifest.json"]),
        "input_build_sha256": sha,
        "kept": sum(c["kept"] for c in accounting["components"].values()),
        "dropped": sum(c["dropped"] for c in accounting["components"].values()),
    }
