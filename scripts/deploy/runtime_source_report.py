"""Compare Atlas discovery with its replayable, data-only runtime release receipt.

This module is deliberately outside the word-card certification implementation glob.
It neither exports a runtime nor acquires source inputs.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RECEIPT = ROOT / "registry/lexicon/atlas-runtime-release.json"
HOLDS = ROOT / "registry/lexicon/atlas-discovery-exclusions.json"
MANIFEST = ROOT / "site/src/data/lexicon-manifest.json"
POINTER_DIR = ROOT / "site/src/data"
LEVELS = ("A1", "A2", "B1", "B2", "C1")
PARTS = ("index", "lexemes", "cloze")
REASONS = ("manifest_changed", "membership_diverged", "count_diverged", "holds_changed")
UNKNOWN_REASONS = ("receipt_missing", "receipt_invalid", "report_error")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def file_digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def membership(slugs: list[str]) -> dict[str, Any]:
    if any(not isinstance(slug, str) or not slug for slug in slugs) or len(set(slugs)) != len(slugs):
        raise ValueError("invalid article membership")
    # Membership is the UTF-8 JSON array itself, without a receipt's trailing LF.
    data = json.dumps(sorted(slugs), ensure_ascii=False, separators=(",", ":")).encode()
    return {"count": len(slugs), "membership_sha256": hashlib.sha256(data).hexdigest()}


def source_binding(manifest_path: Path, *, pointer_dir: Path = POINTER_DIR, deck_dir: Path | None = None) -> dict[str, Any]:
    """Validate hydrated manifest bytes and every consumed deck's pointer binding.

    Reporting reads the deck bindings without consuming deck payloads. Preparation
    additionally verifies the payloads before copying them into isolated scratch.
    """
    pointer = json.loads((pointer_dir / "lexicon-manifest.pointer.json").read_bytes())
    raw = manifest_path.read_bytes()
    if len(raw) != pointer["json_bytes"] or hashlib.sha256(raw).hexdigest() != pointer["json_sha256"]:
        raise ValueError("manifest pointer bytes mismatch")
    manifest = json.loads(raw)
    embedded = manifest["manifest_fingerprint"]
    if (manifest["version"] != pointer["manifest_version"]
            or embedded["schema_version"] != pointer["fingerprint_schema_version"]
            or embedded["fingerprint"] != pointer["manifest_fingerprint"]):
        raise ValueError("manifest pointer fingerprint mismatch")
    sidecar = json.loads((pointer_dir / "lexicon-manifest.fingerprint.json").read_bytes())
    if sidecar["schema_version"] != pointer["fingerprint_schema_version"]:
        raise ValueError("manifest fingerprint schema mismatch")
    deck_pointer = json.loads((pointer_dir / "lexicon-practice-deck.pointer.json").read_bytes())
    if deck_pointer["package_schema_version"] != 1 or len(deck_pointer["files"]) != deck_pointer["file_count"]:
        raise ValueError("invalid practice deck pointer")
    files = {record["path"]: record for record in deck_pointer["files"]}
    if len(files) != len(deck_pointer["files"]):
        raise ValueError("duplicate deck pointer member")
    decks = {}
    for level in LEVELS:
        for part in PARTS:
            name = f"practice-{part}.{level}.json"
            record = files[name]
            if not isinstance(record["sha256"], str) or not _DIGEST.fullmatch(record["sha256"]):
                raise ValueError("invalid deck digest")
            if type(record["bytes"]) is not int or record["bytes"] < 0:
                raise ValueError("invalid deck size")
            if deck_dir is not None:
                path = deck_dir / name
                if path.stat().st_size != record["bytes"] or file_digest(path) != record["sha256"]:
                    raise ValueError("deck pointer bytes mismatch")
            decks[name] = record["sha256"]
    return {"manifest_json_sha256": pointer["json_sha256"], "deck_sha256": decks}


def validate_receipt(value: Any) -> dict[str, Any]:
    """Reject malformed or internally contradictory evidence before comparison."""
    from scripts.deploy.vendor_atlas_tree import _pointed_version_dir, _validate_data_version

    keys = {"schema", "source", "holds_sha256", "archive_sha256", "runtime", "prior", "raw", "projected"}
    if not isinstance(value, dict) or set(value) != keys or value["schema"] != "atlas-runtime-release.v1":
        raise ValueError("invalid release receipt schema")
    source = value["source"]
    if set(source) != {"manifest_json_sha256", "deck_sha256"}:
        raise ValueError("invalid source binding")
    if set(source["deck_sha256"]) != {f"practice-{part}.{level}.json" for level in LEVELS for part in PARTS}:
        raise ValueError("incomplete deck binding")
    digests = [value["holds_sha256"], value["archive_sha256"], source["manifest_json_sha256"], *source["deck_sha256"].values()]
    for key in ("runtime", "prior"):
        identity = value[key]
        expected = {"dataVersion", "runtimeManifestSha256"}
        if key == "prior":
            expected |= {"archive_sha256", "manifestUrl"}
            digests.append(identity["archive_sha256"])
            _pointed_version_dir(identity["manifestUrl"], identity["dataVersion"])
        if set(identity) != expected or not isinstance(identity["dataVersion"], str) or not identity["dataVersion"]:
            raise ValueError("invalid runtime identity")
        _validate_data_version(identity["dataVersion"])
        digests.append(identity["runtimeManifestSha256"])
    if value["prior"]["dataVersion"] == value["runtime"]["dataVersion"]:
        raise ValueError("prior must be a distinct logical generation")
    for key in ("raw", "projected"):
        summary = value[key]
        if set(summary) != {"count", "membership_sha256"} or type(summary["count"]) is not int or summary["count"] < 0:
            raise ValueError("invalid membership summary")
        digests.append(summary["membership_sha256"])
        if summary["count"] == 0 and summary != membership([]):
            raise ValueError("contradictory empty membership")
    if any(not isinstance(digest, str) or not _DIGEST.fullmatch(digest) for digest in digests):
        raise ValueError("invalid receipt digest")
    raw, projected = value["raw"], value["projected"]
    if projected["count"] > raw["count"] or (projected["count"] == raw["count"] and projected != raw):
        raise ValueError("contradictory projection")
    return value


def read_receipt(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    receipt = validate_receipt(json.loads(raw))
    if raw != canonical_bytes(receipt):
        raise ValueError("noncanonical release receipt")
    return receipt


def unknown(reason: str) -> dict[str, Any]:
    if reason not in UNKNOWN_REASONS:
        raise ValueError("invalid unknown reason")
    return {"status": "unknown", "reasons": [reason]}


def compare_evidence(receipt: dict[str, Any], *, source: dict[str, Any], holds_sha256: str,
                     source_raw: dict[str, Any], source_projected: dict[str, Any],
                     observed_raw: dict[str, Any], observed_projected: dict[str, Any],
                     runtime: dict[str, str] | None) -> dict[str, Any]:
    reasons = set()
    if source != receipt["source"] or (runtime is not None and runtime != receipt["runtime"]):
        reasons.add("manifest_changed")
    for name, expected, observed in (("raw", source_raw, observed_raw), ("projected", source_projected, observed_projected)):
        if len({item["membership_sha256"] for item in (receipt[name], expected, observed)}) != 1:
            reasons.add("membership_diverged")
        if len({item["count"] for item in (receipt[name], expected, observed)}) != 1:
            reasons.add("count_diverged")
    if holds_sha256 != receipt["holds_sha256"]:
        reasons.add("holds_changed")
    return {"status": "stale" if reasons else "current", "reasons": [reason for reason in REASONS if reason in reasons],
            "raw_count": observed_raw["count"], "projected_count": observed_projected["count"],
            "source_raw_count": source_raw["count"], "source_projected_count": source_projected["count"]}


def report_source_freshness(rows: list[dict[str, Any]], parity: dict[str, Any] | None, *,
                            manifest_path: Path = MANIFEST, receipt_path: Path = RECEIPT,
                            pointer_dir: Path = POINTER_DIR) -> dict[str, Any]:
    if not receipt_path.exists():
        return unknown("receipt_missing")
    try:
        receipt = read_receipt(receipt_path)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RuntimeError):
        return unknown("receipt_invalid")
    from scripts.atlas.atlas_db import migrate_manifest, validate_alias_targets
    from scripts.audit.generate_search_index import build_atlas_db_search_artifacts
    from scripts.common.scratch import ensure_scratch_root
    from scripts.deploy.vendor_atlas_tree import _discovery_exclusions

    binding = source_binding(manifest_path, pointer_dir=pointer_dir)
    holds = file_digest(HOLDS)
    with tempfile.TemporaryDirectory(prefix="atlas-source-report-", dir=os.environ.get("TMPDIR", ensure_scratch_root())) as scratch:
        db = Path(scratch) / "atlas.db"
        migrate_manifest(manifest_path, db)
        validate_alias_targets(db)
        fresh_rows, _, _ = build_atlas_db_search_artifacts(db)
    withheld, _ = _discovery_exclusions(fresh_rows)
    source_raw = membership([row["s"] for row in fresh_rows])
    source_projected = membership([row["s"] for row in fresh_rows if row["s"] not in withheld])
    if parity is None:
        observed_raw = membership([row["s"] for row in rows])
        observed_holds, _ = _discovery_exclusions(rows)
        observed_projected = membership([row["s"] for row in rows if row["s"] not in observed_holds])
        runtime = None
    else:
        projected_slugs = [row["s"] for row in rows]
        observed_projected = membership(projected_slugs)
        observed_raw = membership([*projected_slugs, *parity["withheldArticles"]])
        # Keep count evidence independent of the reconstructed complete membership.
        observed_raw["count"] = parity["articles"]
        observed_projected["count"] = parity["projectedArticles"]
        runtime = {key: parity[key] for key in ("dataVersion", "runtimeManifestSha256")}
    if binding != source_binding(manifest_path, pointer_dir=pointer_dir) or holds != file_digest(HOLDS):
        raise ValueError("source inputs changed during reporting")
    return compare_evidence(receipt, source=binding, holds_sha256=holds, source_raw=source_raw,
                            source_projected=source_projected, observed_raw=observed_raw,
                            observed_projected=observed_projected, runtime=runtime)


def emit_report(report: dict[str, Any]) -> None:
    """Workflow commands contain only closed enums and integers, never source text."""
    status = report["status"]
    reasons = report["reasons"]
    if status not in ("current", "stale", "unknown") or any(reason not in (*REASONS, *UNKNOWN_REASONS) for reason in reasons):
        raise ValueError("invalid source report")
    level = "notice" if status == "current" else "warning"
    message = " ".join([status, *reasons])
    for key in ("raw_count", "projected_count", "source_raw_count", "source_projected_count"):
        if key in report:
            if type(report[key]) is not int or report[key] < 0:
                raise ValueError("invalid source count")
            message += f" {key}={report[key]}"
    escaped = message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    print(canonical_bytes(report).decode().rstrip("\n"))
    print(f"::{level} title=Atlas runtime source::{escaped}")
