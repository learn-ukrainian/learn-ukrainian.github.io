#!/usr/bin/env python3
"""Verify the text-free Phase 3 source-universe freeze as an integrity record.

This verifier deliberately establishes only that the published freeze is intact.
It neither reads source inputs nor certifies any source-coverage outcome.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
DEFAULT_EVIDENCE_DIR = DATA / "evidence/source_universe_v1"
SCHEMA_PATH = DATA / "contracts/phase3_source_universe_freeze_v1.schema.json"
RECEIPT_FILE = "source-universe-freeze-receipt.json"
STRUCTURAL_FILE = "lexical_structural_freeze_v1.json"
GIT_SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")

LEDGER_FAMILIES = frozenset({
    "antonenko_style_guide",
    "antonenko_textbook_representation",
    "calque_inventory",
    "ua_gec",
    "school_textbooks",
    "pravopys_2019_complete",
    "pravopys_2026_complete",
    "other_normative_style_inventory",
})
LEXICAL_FAMILIES = frozenset({
    "lexical_balla_en_uk",
    "lexical_dmklinger_uk_en",
    "lexical_esum_cognate_forms",
    "lexical_esum_etymology",
    "lexical_frazeolohichnyi",
    "lexical_grinchenko",
    "lexical_puls_cefr",
    "lexical_sum11",
    "lexical_ukrajinet",
    "lexical_wiktionary",
    "lexical_ulif",
    "lexical_vesum",
    "lexical_r2u",
})
ALL_FAMILIES = LEDGER_FAMILIES | LEXICAL_FAMILIES
PAYLOAD_FILES = frozenset(
    {f"{family_id}.units.jsonl" for family_id in LEDGER_FAMILIES} | {STRUCTURAL_FILE}
)
EXPECTED_FILES = PAYLOAD_FILES | {RECEIPT_FILE}
BASE_LEDGER_FIELDS = frozenset({
    "family_id", "unit_id", "unit_sha256", "ordinal", "locator",
    "duplicate_group_id", "parse_status", "rights", "provenance",
})
BINDING_FIELDS = ["unit_id", "unit_sha256", "duplicate_group_id", "parse_status", "provenance"]


class IntegrityError(ValueError):
    """The published freeze cannot be verified as an intact text-free record."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise IntegrityError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise IntegrityError(f"cannot read artifact: {path.name}") from exc
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IntegrityError(f"cannot read JSON artifact: {path.name}") from exc
    require(isinstance(value, dict), f"JSON artifact must be an object: {path.name}")
    return value


def _schema_validate(receipt: Mapping[str, Any], schema_path: Path) -> None:
    schema = read_json(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(receipt)
    except SchemaError as exc:
        raise IntegrityError(f"invalid freeze schema: {exc.message}") from exc
    except ValidationError as exc:
        location = ".".join(str(part) for part in exc.path) or "<root>"
        raise IntegrityError(f"receipt schema violation at {location}: {exc.message}") from exc


def _directory_files(evidence_dir: Path) -> dict[str, Path]:
    require(evidence_dir.is_dir() and not evidence_dir.is_symlink(), "evidence directory is not a real directory")
    files: dict[str, Path] = {}
    try:
        children = list(evidence_dir.iterdir())
    except OSError as exc:
        raise IntegrityError("cannot enumerate evidence directory") from exc
    for path in children:
        require(not path.is_symlink(), f"symlinked evidence artifact: {path.name}")
        require(path.is_file(), f"non-file evidence artifact: {path.name}")
        files[path.name] = path
    require(set(files) == EXPECTED_FILES, "evidence directory file set differs from the frozen 10 artifacts")
    return files


def _validate_manifest(receipt: Mapping[str, Any], files: Mapping[str, Path]) -> None:
    manifest = receipt["artifact_manifest"]
    require(isinstance(manifest, Mapping), "receipt manifest is not an object")
    payloads = manifest["payloads"]
    require(isinstance(payloads, list), "receipt payload manifest is not a list")
    paths = [item.get("path") for item in payloads if isinstance(item, Mapping)]
    require(len(paths) == len(payloads) and len(set(paths)) == len(paths), "receipt payload paths are duplicated or invalid")
    require(set(paths) == PAYLOAD_FILES, "receipt payload paths differ from the frozen payload set")
    require(payloads == sorted(payloads, key=lambda item: item["path"]), "receipt payload manifest is not canonical")
    require(
        manifest["payload_manifest_sha256"] == sha256_bytes(canonical_json(payloads).encode("utf-8")),
        "receipt payload manifest hash mismatch",
    )
    for item in payloads:
        path = files[item["path"]]
        require(path.stat().st_size == item["byte_count"], f"payload byte count mismatch: {path.name}")
        require(sha256_file(path) == item["sha256"], f"payload hash mismatch: {path.name}")


def _require_sha(value: object, label: str) -> str:
    require(isinstance(value, str) and SHA256.fullmatch(value) is not None, f"invalid SHA-256: {label}")
    return value


def _validate_record(record: object, family_id: str, ordinal: int, ledger_name: str) -> None:
    require(isinstance(record, Mapping), f"ledger record is not an object: {ledger_name}:{ordinal}")
    expected_fields = BASE_LEDGER_FIELDS | ({"normalized_text_sha256"} if family_id.startswith("pravopys_") else set())
    require(set(record) == expected_fields, f"unexpected record shape: {ledger_name}:{ordinal}")
    require(record["family_id"] == family_id, f"ledger family mismatch: {ledger_name}:{ordinal}")
    require(record["ordinal"] == ordinal, f"ledger ordinal mismatch: {ledger_name}:{ordinal}")
    for key in ("unit_sha256", "duplicate_group_id"):
        value = record[key]
        if key == "duplicate_group_id":
            require(isinstance(value, str) and value.startswith(f"duplicate.{family_id}.") and SHA256.fullmatch(value.rsplit(".", 1)[-1]) is not None, f"invalid duplicate group: {ledger_name}:{ordinal}")
        else:
            _require_sha(value, f"{ledger_name}:{ordinal}:{key}")
    require(isinstance(record["unit_id"], str) and record["unit_id"].startswith(f"unit.{family_id}.") and SHA256.fullmatch(record["unit_id"].rsplit(".", 1)[-1]) is not None, f"invalid unit identifier: {ledger_name}:{ordinal}")
    if "normalized_text_sha256" in record:
        _require_sha(record["normalized_text_sha256"], f"{ledger_name}:{ordinal}:normalized_text_sha256")
    _validate_rights(record["rights"], ledger_name, ordinal)
    _validate_provenance(record["provenance"], ledger_name, ordinal)
    _validate_locator(record["locator"], family_id, ledger_name, ordinal)
    require(isinstance(record["parse_status"], str) and record["parse_status"], f"invalid parse status: {ledger_name}:{ordinal}")


def _validate_rights(value: object, ledger_name: str, ordinal: int) -> None:
    expected = {
        "source_text_committed": False,
        "locator_only_allowed": True,
        "rights_limited_disposition": "rights_limited_locator_only",
    }
    require(value == expected, f"rights record is not text-free: {ledger_name}:{ordinal}")


def _validate_provenance(value: object, ledger_name: str, ordinal: int) -> None:
    require(isinstance(value, Mapping) and set(value) == {"input_sha256", "unit_grain"}, f"unexpected provenance shape: {ledger_name}:{ordinal}")
    _require_sha(value["input_sha256"], f"{ledger_name}:{ordinal}:provenance")
    require(isinstance(value["unit_grain"], str) and value["unit_grain"], f"invalid unit grain: {ledger_name}:{ordinal}")


def _validate_locator(value: object, family_id: str, ledger_name: str, ordinal: int) -> None:
    require(isinstance(value, Mapping) and isinstance(value.get("kind"), str), f"invalid locator: {ledger_name}:{ordinal}")
    kind = value["kind"]
    if kind == "sqlite_row":
        require(set(value) == {"kind", "table", "primary_key_fields", "primary_key_sha256"}, f"unexpected SQLite locator shape: {ledger_name}:{ordinal}")
        require(isinstance(value["table"], str) and value["table"], f"invalid SQLite table: {ledger_name}:{ordinal}")
        require(isinstance(value["primary_key_fields"], list) and value["primary_key_fields"] and all(isinstance(item, str) and item for item in value["primary_key_fields"]), f"invalid SQLite primary key fields: {ledger_name}:{ordinal}")
        _require_sha(value["primary_key_sha256"], f"{ledger_name}:{ordinal}:primary key")
    elif kind == "python_mapping_entry":
        require(family_id == "calque_inventory" and set(value) == {"kind", "collection", "entry_id_sha256"}, f"unexpected mapping locator shape: {ledger_name}:{ordinal}")
        require(isinstance(value["collection"], str) and value["collection"], f"invalid mapping collection: {ledger_name}:{ordinal}")
        _require_sha(value["entry_id_sha256"], f"{ledger_name}:{ordinal}:entry id")
    elif kind == "pdf_numbered_hierarchy":
        require(family_id.startswith("pravopys_") and set(value) == {"kind", "edition_sha256", "page", "line", "end_page", "end_line", "section_path"}, f"unexpected PDF locator shape: {ledger_name}:{ordinal}")
        _require_sha(value["edition_sha256"], f"{ledger_name}:{ordinal}:edition")
        require(all(isinstance(value[name], int) and value[name] >= 1 for name in ("page", "line", "end_page", "end_line")), f"invalid PDF locator bounds: {ledger_name}:{ordinal}")
        require(
            (value["end_page"], value["end_line"]) >= (value["page"], value["line"]),
            f"inverted PDF locator bounds: {ledger_name}:{ordinal}",
        )
        require(isinstance(value["section_path"], list) and value["section_path"] and all(isinstance(item, str) and item for item in value["section_path"]), f"invalid PDF section path: {ledger_name}:{ordinal}")
    else:
        raise IntegrityError(f"unexpected locator kind: {ledger_name}:{ordinal}")


def _validate_ledgers(receipt_families: Mapping[str, Mapping[str, Any]], files: Mapping[str, Path]) -> None:
    for family_id in LEDGER_FAMILIES:
        family = receipt_families[family_id]
        ledger_name = f"{family_id}.units.jsonl"
        require(family["ledger_file"] == ledger_name, f"ledger filename mismatch: {family_id}")
        path = files[ledger_name]
        count = 0
        try:
            with path.open(encoding="utf-8") as handle:
                for count, line in enumerate(handle, start=1):
                    require(line.endswith("\n"), f"ledger line lacks newline: {ledger_name}:{count}")
                    try:
                        _validate_record(json.loads(line), family_id, count, ledger_name)
                    except json.JSONDecodeError as exc:
                        raise IntegrityError(f"invalid JSONL record: {ledger_name}:{count}") from exc
        except OSError as exc:
            raise IntegrityError(f"cannot read ledger: {ledger_name}") from exc
        require(count == family["unit_count"], f"ledger line count mismatch: {family_id}")
        require(sha256_file(path) == family["ledger_sha256"], f"ledger receipt hash mismatch: {family_id}")


def _validate_structural(receipt_families: Mapping[str, Mapping[str, Any]], files: Mapping[str, Path]) -> None:
    path = files[STRUCTURAL_FILE]
    structural = read_json(path)
    require(set(structural) == {"schema_version", "text_free", "families"}, "unexpected lexical structural receipt shape")
    require(structural["schema_version"] == "lexical_structural_freeze_v1" and structural["text_free"] is True, "lexical structural receipt is not text-free")
    families = structural["families"]
    require(isinstance(families, list), "lexical structural families is not a list")
    summaries: dict[str, Mapping[str, Any]] = {}
    for summary in families:
        require(isinstance(summary, Mapping), "lexical structural family is not an object")
        require(set(summary) == {"family_id", "unit_count", "ordered_rolling_sha256", "parse_status_counts", "binding_fields", "provenance"}, "unexpected lexical structural family shape")
        family_id = summary["family_id"]
        require(isinstance(family_id, str) and family_id not in summaries, "duplicate lexical structural family")
        summaries[family_id] = summary
        require(summary["binding_fields"] == BINDING_FIELDS, f"lexical binding fields mismatch: {family_id}")
        require(isinstance(summary["unit_count"], int) and summary["unit_count"] > 0, f"invalid lexical count: {family_id}")
        _require_sha(summary["ordered_rolling_sha256"], f"lexical universe: {family_id}")
        parse_counts = summary["parse_status_counts"]
        require(isinstance(parse_counts, Mapping) and parse_counts and all(isinstance(key, str) and key and isinstance(value, int) and value >= 0 for key, value in parse_counts.items()), f"invalid lexical parse counts: {family_id}")
        require(sum(parse_counts.values()) == summary["unit_count"], f"lexical parse count mismatch: {family_id}")
        provenance = summary["provenance"]
        require(isinstance(provenance, Mapping) and set(provenance) in ({"input_sha256", "unit_grain"}, {"input_sha256", "unit_grain", "cache_id_sha256"}), f"unexpected lexical provenance shape: {family_id}")
        _require_sha(provenance["input_sha256"], f"lexical provenance: {family_id}")
        require(isinstance(provenance["unit_grain"], str) and provenance["unit_grain"], f"invalid lexical unit grain: {family_id}")
        if "cache_id_sha256" in provenance:
            _require_sha(provenance["cache_id_sha256"], f"lexical cache identifier: {family_id}")
    require(set(summaries) == LEXICAL_FAMILIES, "lexical structural family set mismatch")
    structural_hash = sha256_file(path)
    for family_id in LEXICAL_FAMILIES:
        family = receipt_families[family_id]
        summary = summaries[family_id]
        require(family["structural_receipt_file"] == STRUCTURAL_FILE, f"structural filename mismatch: {family_id}")
        require(family["structural_receipt_sha256"] == structural_hash, f"structural receipt hash mismatch: {family_id}")
        require(family["unit_count"] == summary["unit_count"], f"structural unit count mismatch: {family_id}")
        require(family["structural_universe_sha256"] == summary["ordered_rolling_sha256"], f"structural universe hash mismatch: {family_id}")


def _validate_families(receipt: Mapping[str, Any], files: Mapping[str, Path]) -> None:
    raw_families = receipt["families"]
    require(isinstance(raw_families, list), "receipt families is not a list")
    families: dict[str, Mapping[str, Any]] = {}
    for family in raw_families:
        require(isinstance(family, Mapping) and isinstance(family.get("family_id"), str), "invalid receipt family")
        family_id = family["family_id"]
        require(family_id not in families, f"duplicate receipt family: {family_id}")
        families[family_id] = family
    require(set(families) == ALL_FAMILIES, "receipt family set must be exactly 8 ledger and 13 lexical families")
    for family_id in LEDGER_FAMILIES:
        family = families[family_id]
        require(set(family) == {"family_id", "unit_count", "ledger_sha256", "ledger_file"}, f"ledger receipt shape mismatch: {family_id}")
    for family_id in LEXICAL_FAMILIES:
        family = families[family_id]
        require(set(family) == {"family_id", "unit_count", "structural_receipt_file", "structural_receipt_sha256", "structural_universe_sha256"}, f"lexical receipt shape mismatch: {family_id}")
    _validate_ledgers(families, files)
    _validate_structural(families, files)


def _git_bytes(repo_root: Path, arguments: Sequence[str], label: str) -> bytes:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), *arguments],
            check=False,
            capture_output=True,
        )
    except OSError as exc:
        raise IntegrityError(f"unable to run git for {label}") from exc
    require(result.returncode == 0, f"git verification failed: {label}")
    return result.stdout


def _validate_freezer_binding(receipt: Mapping[str, Any], repo_root: Path) -> None:
    merged_main_sha = receipt["merged_main_sha"]
    require(isinstance(merged_main_sha, str) and GIT_SHA40.fullmatch(merged_main_sha) is not None, "merged main SHA must be 40 lowercase hex characters")
    _git_bytes(repo_root, ["merge-base", "--is-ancestor", merged_main_sha, "origin/main"], "merged-main ancestry")
    freezer = receipt["freezer"]
    require(isinstance(freezer, Mapping), "freezer binding is not an object")
    script_path = freezer["script_path"]
    require(isinstance(script_path, str) and script_path and not Path(script_path).is_absolute() and ".." not in Path(script_path).parts, "unsafe freezer script path")
    script = _git_bytes(repo_root, ["show", f"{merged_main_sha}:{script_path}"], "freezer script")
    require(sha256_bytes(script) == freezer["script_sha256"], "freezer script hash mismatch")


def validate(evidence_dir: Path = DEFAULT_EVIDENCE_DIR, *, schema_path: Path = SCHEMA_PATH, repo_root: Path = ROOT) -> dict[str, Any]:
    """Validate a published freeze directory without assigning a coverage verdict."""
    files = _directory_files(evidence_dir)
    receipt = read_json(files[RECEIPT_FILE])
    _schema_validate(receipt, schema_path)
    require(receipt["text_free"] is True, "receipt is not text-free")
    _validate_manifest(receipt, files)
    _validate_families(receipt, files)
    _validate_freezer_binding(receipt, repo_root)
    return {
        "ok": True,
        "integrity_verified": True,
        "artifact_count": len(files),
        "family_count": len(ALL_FAMILIES),
        "merged_main_sha": receipt["merged_main_sha"],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify Phase 3 source-universe freeze integrity only.")
    parser.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE_DIR)
    parser.add_argument("--schema", type=Path, default=SCHEMA_PATH)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = validate(args.evidence_dir, schema_path=args.schema, repo_root=args.repo_root)
    except IntegrityError as exc:
        print(canonical_json({"ok": False, "error": str(exc)}))
        return 2
    print(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
