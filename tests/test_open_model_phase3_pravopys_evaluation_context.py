from __future__ import annotations

import copy
import io
import json
import os
import stat
import tarfile
from collections.abc import Callable
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_evaluation_context_manifest as eval_manifest
from scripts.projects.open_model_data import phase3_pravopys_evaluation_context as prav_context

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "data/projects/open_model_data/contracts/phase3_pravopys_evaluation_context_receipt_v1.schema.json"
EVAL_RECEIPT = ROOT / "data/projects/open_model_data/inventory/phase3_evaluation_context_manifest_receipt_v1.json"


def _prav_row(
    family: str,
    section_path: list[str],
    text: str,
    *,
    unit_id: str | None = None,
) -> dict[str, object]:
    frozen_locator = {
        "kind": "pdf_numbered_hierarchy",
        "edition_sha256": (
            prav_context.PINNED_PRAVOPYS_2019_PDF_SHA256
            if family == "pravopys_2019_complete"
            else prav_context.PINNED_PRAVOPYS_2026_PDF_SHA256
        ),
        "page": 1,
        "line": 1,
        "end_page": 1,
        "end_line": 2,
        "section_path": section_path,
    }
    unit_id = unit_id or f"unit.{family}.{prav_context.sha256_bytes(text.encode('utf-8'))[:16]}"
    return {
        "family_id": family,
        "unit_id": unit_id,
        "unit_sha256": prav_context.sha256_bytes(text.encode("utf-8")),
        "frozen_locator": frozen_locator,
        "frozen_locator_sha256": eval_manifest.sha256_value(frozen_locator),
        "document_or_edition_identity": family,
        "source_text": text,
        "source_record": {"text": text},
        "source_text_sha256": prav_context.sha256_bytes(text.encode("utf-8")),
    }


def _partition_row(source_row: dict[str, object]) -> dict[str, object]:
    return {
        "family_id": source_row["family_id"],
        "unit_id": source_row["unit_id"],
        "unit_sha256": source_row["unit_sha256"],
        "reason": "evaluation_only",
        "candidate_lane": "phenomenon_strata",
        "source_text_sha256": source_row["source_text_sha256"],
        "frozen_locator_sha256": source_row["frozen_locator_sha256"],
    }


def _manifest_row(source_row: dict[str, object]) -> dict[str, object]:
    return {
        "unit_id": source_row["unit_id"],
        "unit_sha256": source_row["unit_sha256"],
        "family_id": source_row["family_id"],
        "candidate_lane": "phenomenon_strata",
        "context_kind": "frozen_source_unit_text",
        "complete_sentence_context": False,
        "source_text": source_row["source_text"],
        "source_text_sha256": source_row["source_text_sha256"],
        "frozen_locator_sha256": source_row["frozen_locator_sha256"],
    }


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, prav_context.PRIVATE_DIR_MODE)
    payload = b"".join(prav_context.canonical_bytes(row) for row in rows)
    path.write_bytes(payload)
    os.chmod(path, prav_context.PRIVATE_FILE_MODE)


def _evaluation_manifest_receipt(manifest_path: Path) -> dict[str, object]:
    receipt = {
        "schema_version": eval_manifest.SCHEMA_VERSION,
        "implementation_version": eval_manifest.IMPLEMENTATION_VERSION,
        "text_free": True,
        "provider_calls": False,
        "manifest": {
            "private_jsonl_sha256": prav_context.sha256_file(manifest_path),
            "private_jsonl_bytes": manifest_path.stat().st_size,
            "private_jsonl_rows": sum(1 for _ in manifest_path.open("rb")),
        },
    }
    receipt["receipt_sha256"] = eval_manifest.receipt_sha256(receipt)
    return receipt


def _write_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, prav_context.PRIVATE_DIR_MODE)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(path, prav_context.PRIVATE_FILE_MODE)


def _fixture_bundle(tmp_path: Path) -> dict[str, Path]:
    private = tmp_path / "private"
    private.mkdir(parents=True, mode=prav_context.PRIVATE_DIR_MODE)
    os.chmod(private, prav_context.PRIVATE_DIR_MODE)

    parent_2019 = "      4. Параграф батьківського правила 2019.\n      1) дитяче правило."
    child_2019 = "      1) дитяче правило."
    self_2026 = "      1.2. Самостійне десяткове правило 2026."
    emoji_parent = "      5. Батько з емодзі 😀.\n      а) дитина 😀."
    emoji_child = "      а) дитина 😀."

    rows_2019 = [
        _prav_row("pravopys_2019_complete", ["paragraph:4"], parent_2019),
        _prav_row(
            "pravopys_2019_complete",
            ["paragraph:4", "part:1"],
            child_2019,
        ),
    ]
    rows_2026 = [
        _prav_row("pravopys_2026_complete", ["decimal:1", "decimal:1.2"], self_2026),
        _prav_row("pravopys_2026_complete", ["paragraph:5"], emoji_parent),
        _prav_row(
            "pravopys_2026_complete",
            ["paragraph:5", "part:1"],
            emoji_child,
        ),
    ]
    all_rows = rows_2019 + rows_2026
    source_jsonl = private / "source_units_v1.jsonl"
    _write_jsonl(source_jsonl, all_rows)

    partition_rows = [_partition_row(row) for row in all_rows]
    partition = private / "partition_manifest_v1.jsonl"
    _write_jsonl(partition, partition_rows)

    manifest_rows = [_manifest_row(row) for row in all_rows]
    evaluation_manifest = private / "evaluation_context_manifest_v1.jsonl"
    _write_jsonl(evaluation_manifest, manifest_rows)
    evaluation_manifest_receipt_path = private / "evaluation_context_manifest_receipt_v1.json"
    _write_json(evaluation_manifest_receipt_path, _evaluation_manifest_receipt(evaluation_manifest))

    return {
        "source_jsonl": source_jsonl,
        "partition": partition,
        "evaluation_manifest": evaluation_manifest,
        "evaluation_manifest_receipt": evaluation_manifest_receipt_path,
        "private_output": private / prav_context.PRIVATE_FILENAME,
        "public_receipt": tmp_path / "public-receipt.json",
    }


def _accept_all_schema_validator() -> object:
    class _AcceptAll:
        def iter_errors(self, _value: object) -> list[object]:
            return []

    return _AcceptAll()


def _load_public_receipt() -> dict[str, object]:
    path = ROOT / "data/projects/open_model_data/inventory/phase3_pravopys_evaluation_context_receipt_v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _rehash_prav_receipt(receipt: dict[str, object]) -> dict[str, object]:
    receipt["receipt_sha256"] = prav_context.receipt_sha256(receipt)
    return receipt


def _patch_fixture_pins(
    monkeypatch: pytest.MonkeyPatch,
    paths: dict[str, Path],
    row_count: int,
    *,
    stub_prav_validate: bool = True,
) -> None:
    monkeypatch.setattr(prav_context, "ROW_COUNT", row_count)
    monkeypatch.setattr(prav_context, "FAMILY_COUNTS", {"pravopys_2019_complete": 2, "pravopys_2026_complete": 3})
    monkeypatch.setattr(prav_context, "LANE_COUNTS", {"phenomenon_strata": row_count})
    monkeypatch.setattr(
        prav_context,
        "MAPPING_ACCOUNTING",
        {"self_parent_rule": 3, "child_parent_rule": 2},
    )
    monkeypatch.setattr(
        prav_context,
        "CONTEXT_ACCOUNTING",
        {"pravopys_parent_rule_context": row_count, "pravopys_typed_exclusion": 0},
    )
    monkeypatch.setattr(
        prav_context, "PINNED_SOURCE_UNITS_JSONL_SHA256", prav_context.sha256_file(paths["source_jsonl"])
    )
    monkeypatch.setattr(prav_context, "PINNED_PARTITION_SHA256", prav_context.sha256_file(paths["partition"]))
    monkeypatch.setattr(
        prav_context,
        "PINNED_EVALUATION_CONTEXT_MANIFEST_JSONL_SHA256",
        prav_context.sha256_file(paths["evaluation_manifest"]),
    )
    monkeypatch.setattr(
        prav_context,
        "PINNED_EVALUATION_CONTEXT_MANIFEST_RECEIPT_BODY_SHA256",
        eval_manifest.receipt_sha256(json.loads(paths["evaluation_manifest_receipt"].read_text(encoding="utf-8"))),
    )
    monkeypatch.setattr(
        prav_context,
        "PINNED_EVALUATION_CONTEXT_MANIFEST_RECEIPT_FILE_SHA256",
        prav_context.sha256_file(paths["evaluation_manifest_receipt"]),
    )
    monkeypatch.setattr(eval_manifest, "ROW_COUNT", row_count)
    monkeypatch.setattr(eval_manifest, "V2_SOURCE_UNITS", row_count)
    monkeypatch.setattr(eval_manifest, "validate_receipt", lambda receipt: dict(receipt))
    if stub_prav_validate:
        monkeypatch.setattr(prav_context, "validate_receipt", lambda receipt: dict(receipt))
    else:
        # Fixture pins differ from schema consts; keep real validate_receipt require() guards.
        monkeypatch.setattr(prav_context, "_schema_validator", _accept_all_schema_validator)


def _read_jsonl_rows(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _call_build(paths: dict[str, Path]) -> tuple[list[dict[str, object]], object, object]:
    return prav_context.build_context_rows(
        source_jsonl=paths["source_jsonl"],
        partition_path=paths["partition"],
        evaluation_manifest_path=paths["evaluation_manifest"],
        evaluation_manifest_receipt_path=paths["evaluation_manifest_receipt"],
    )


def _simulate_group_readable_mode(monkeypatch: pytest.MonkeyPatch, target: Path) -> None:
    original_lstat = Path.lstat
    original_stat = Path.stat

    def _with_group_read(result: os.stat_result, path: Path) -> os.stat_result:
        if path != target:
            return result
        values = list(result)
        values[0] |= stat.S_IRGRP
        return os.stat_result(values)

    def patched_lstat(path: Path, *args: object, **kwargs: object) -> os.stat_result:
        return _with_group_read(original_lstat(path, *args, **kwargs), path)

    def patched_stat(path: Path, *args: object, **kwargs: object) -> os.stat_result:
        return _with_group_read(original_stat(path, *args, **kwargs), path)

    monkeypatch.setattr(Path, "lstat", patched_lstat)
    monkeypatch.setattr(Path, "stat", patched_stat)


def _simulate_world_readable_lstat(monkeypatch: pytest.MonkeyPatch, target: Path) -> None:
    original_lstat = Path.lstat

    def patched_lstat(path: Path, *args: object, **kwargs: object) -> os.stat_result:
        result = original_lstat(path, *args, **kwargs)
        if path != target:
            return result
        values = list(result)
        values[0] |= stat.S_IRGRP | stat.S_IROTH
        return os.stat_result(values)

    monkeypatch.setattr(Path, "lstat", patched_lstat)


def _mutate_jsonl_row(
    path: Path,
    line_index: int,
    mutator: Callable[[dict[str, object]], None],
) -> None:
    rows = _read_jsonl_rows(path)
    row = copy.deepcopy(rows[line_index])
    mutator(row)
    rows[line_index] = row
    _write_jsonl(path, rows)


def _assert_hash_guard_probe(
    monkeypatch: pytest.MonkeyPatch,
    *,
    pin_attr: str,
    drifted_path: Path,
    match: str,
    paths: dict[str, Path],
) -> None:
    with pytest.raises(prav_context.PravopysEvaluationContextError, match=match):
        _call_build(paths)
    monkeypatch.setattr(prav_context, pin_attr, prav_context.sha256_file(drifted_path))
    with pytest.raises(prav_context.PravopysEvaluationContextError) as exc_info:
        _call_build(paths)
    assert match not in str(exc_info.value)


def test_self_and_child_parent_mapping_2019_and_2026(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture_bundle(tmp_path)
    _patch_fixture_pins(monkeypatch, paths, row_count=5)
    rows, _, mapping = prav_context.build_context_rows(
        source_jsonl=paths["source_jsonl"],
        partition_path=paths["partition"],
        evaluation_manifest_path=paths["evaluation_manifest"],
        evaluation_manifest_receipt_path=paths["evaluation_manifest_receipt"],
    )
    assert dict(mapping) == {"self_parent_rule": 3, "child_parent_rule": 2}
    child_2019 = next(
        row
        for row in rows
        if row["family_id"] == "pravopys_2019_complete" and row["parent_rule_mapping_kind"] == "child_parent_rule"
    )
    self_2026 = next(
        row
        for row in rows
        if row["family_id"] == "pravopys_2026_complete" and row["parent_rule_mapping_kind"] == "self_parent_rule"
    )
    assert child_2019["parent_section_path"] == ["paragraph:4"]
    assert self_2026["parent_section_path"] == ["decimal:1", "decimal:1.2"]
    assert child_2019["complete_parent_rule_context"].count(child_2019["unit_text"]) == 1


def test_unicode_code_point_offsets_round_trip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture_bundle(tmp_path)
    _patch_fixture_pins(monkeypatch, paths, row_count=5)
    rows, _, _ = prav_context.build_context_rows(
        source_jsonl=paths["source_jsonl"],
        partition_path=paths["partition"],
        evaluation_manifest_path=paths["evaluation_manifest"],
        evaluation_manifest_receipt_path=paths["evaluation_manifest_receipt"],
    )
    emoji_row = next(row for row in rows if "😀" in row["unit_text"])
    parent = emoji_row["complete_parent_rule_context"]
    start = emoji_row["unit_text_start_offset"]
    end = emoji_row["unit_text_end_offset"]
    assert parent[start:end] == emoji_row["unit_text"]
    assert len("😀") == 1


def test_duplicate_child_text_emits_typed_exclusion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture_bundle(tmp_path)
    duplicate_parent = "      4. Rule with duplicate child.\n      1) dup.\n      1) dup."
    duplicate_child = "      1) dup."
    all_rows = [json.loads(line) for line in paths["source_jsonl"].read_text(encoding="utf-8").splitlines()]
    child_2019_id = next(
        row["unit_id"] for row in all_rows if row["frozen_locator"]["section_path"] == ["paragraph:4", "part:1"]
    )
    all_rows = [
        _prav_row("pravopys_2019_complete", ["paragraph:4"], duplicate_parent, unit_id=str(row["unit_id"]))
        if row["frozen_locator"]["section_path"] == ["paragraph:4"]
        else row
        for row in all_rows
        if row["unit_id"] != child_2019_id
    ]
    dup_row = _prav_row(
        "pravopys_2019_complete",
        ["paragraph:4", "point:1"],
        duplicate_child,
        unit_id="unit.pravopys_2019_complete.duplicate-child",
    )
    all_rows.append(dup_row)
    _write_jsonl(paths["source_jsonl"], all_rows)
    partition_rows = [_partition_row(row) for row in all_rows]
    _write_jsonl(paths["partition"], partition_rows)
    manifest_rows = [_manifest_row(row) for row in all_rows]
    _write_jsonl(paths["evaluation_manifest"], manifest_rows)
    _write_json(paths["evaluation_manifest_receipt"], _evaluation_manifest_receipt(paths["evaluation_manifest"]))
    _patch_fixture_pins(monkeypatch, paths, row_count=5)
    monkeypatch.setattr(prav_context, "FAMILY_COUNTS", {"pravopys_2019_complete": 2, "pravopys_2026_complete": 3})
    monkeypatch.setattr(
        prav_context,
        "MAPPING_ACCOUNTING",
        {"self_parent_rule": 3, "child_parent_rule": 1},
    )
    monkeypatch.setattr(
        prav_context,
        "CONTEXT_ACCOUNTING",
        {"pravopys_parent_rule_context": 4, "pravopys_typed_exclusion": 1},
    )
    rows, accounting, _ = prav_context.build_context_rows(
        source_jsonl=paths["source_jsonl"],
        partition_path=paths["partition"],
        evaluation_manifest_path=paths["evaluation_manifest"],
        evaluation_manifest_receipt_path=paths["evaluation_manifest_receipt"],
    )
    excluded = next(row for row in rows if row.get("exclusion_reason_code") == "unit_text_not_unique_in_parent")
    assert accounting["pravopys_typed_exclusion"] == 1


def test_noncontained_child_emits_typed_exclusion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture_bundle(tmp_path)
    orphan = _prav_row("pravopys_2019_complete", ["paragraph:4", "point:9"], "      9) не входить у батька.")
    all_rows = [json.loads(line) for line in paths["source_jsonl"].read_text(encoding="utf-8").splitlines()]
    all_rows.append(orphan)
    _write_jsonl(paths["source_jsonl"], all_rows)
    partition_rows = [_partition_row(row) for row in all_rows if row["family_id"].startswith("pravopys")]
    _write_jsonl(paths["partition"], partition_rows)
    manifest_rows = [_manifest_row(row) for row in all_rows if row["family_id"].startswith("pravopys")]
    _write_jsonl(paths["evaluation_manifest"], manifest_rows)
    _write_json(paths["evaluation_manifest_receipt"], _evaluation_manifest_receipt(paths["evaluation_manifest"]))
    _patch_fixture_pins(monkeypatch, paths, row_count=6)
    monkeypatch.setattr(prav_context, "FAMILY_COUNTS", {"pravopys_2019_complete": 3, "pravopys_2026_complete": 3})
    monkeypatch.setattr(
        prav_context,
        "MAPPING_ACCOUNTING",
        {"self_parent_rule": 3, "child_parent_rule": 2},
    )
    monkeypatch.setattr(
        prav_context,
        "CONTEXT_ACCOUNTING",
        {"pravopys_parent_rule_context": 5, "pravopys_typed_exclusion": 1},
    )
    rows, _, _ = prav_context.build_context_rows(
        source_jsonl=paths["source_jsonl"],
        partition_path=paths["partition"],
        evaluation_manifest_path=paths["evaluation_manifest"],
        evaluation_manifest_receipt_path=paths["evaluation_manifest_receipt"],
    )
    excluded = next(row for row in rows if row.get("exclusion_reason_code") == "unit_text_not_contained_in_parent")
    assert excluded["context_kind"] == "pravopys_typed_exclusion"


def test_missing_parent_emits_typed_exclusion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture_bundle(tmp_path)
    orphan = _prav_row("pravopys_2019_complete", ["paragraph:99", "part:1"], "      1) без батька.")
    all_rows = [json.loads(line) for line in paths["source_jsonl"].read_text(encoding="utf-8").splitlines()]
    all_rows.append(orphan)
    _write_jsonl(paths["source_jsonl"], all_rows)
    partition_rows = [_partition_row(row) for row in all_rows if row["family_id"].startswith("pravopys")]
    _write_jsonl(paths["partition"], partition_rows)
    manifest_rows = [_manifest_row(row) for row in all_rows if row["family_id"].startswith("pravopys")]
    _write_jsonl(paths["evaluation_manifest"], manifest_rows)
    _write_json(paths["evaluation_manifest_receipt"], _evaluation_manifest_receipt(paths["evaluation_manifest"]))
    _patch_fixture_pins(monkeypatch, paths, row_count=6)
    monkeypatch.setattr(prav_context, "FAMILY_COUNTS", {"pravopys_2019_complete": 3, "pravopys_2026_complete": 3})
    monkeypatch.setattr(
        prav_context,
        "MAPPING_ACCOUNTING",
        {"self_parent_rule": 3, "child_parent_rule": 2},
    )
    monkeypatch.setattr(
        prav_context,
        "CONTEXT_ACCOUNTING",
        {"pravopys_parent_rule_context": 5, "pravopys_typed_exclusion": 1},
    )
    rows, _, _ = prav_context.build_context_rows(
        source_jsonl=paths["source_jsonl"],
        partition_path=paths["partition"],
        evaluation_manifest_path=paths["evaluation_manifest"],
        evaluation_manifest_receipt_path=paths["evaluation_manifest_receipt"],
    )
    excluded = next(row for row in rows if row.get("exclusion_reason_code") == "missing_parent_rule")
    assert excluded["parent_section_path"] == ["paragraph:99"]


def test_invalid_section_path_emits_typed_exclusion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture_bundle(tmp_path)
    bad = _prav_row(
        "pravopys_2019_complete",
        ["paragraph:1", "paragraph:2"],
        "      1. подвійний параграф.",
    )
    all_rows = [json.loads(line) for line in paths["source_jsonl"].read_text(encoding="utf-8").splitlines()]
    all_rows.append(bad)
    _write_jsonl(paths["source_jsonl"], all_rows)
    partition_rows = [_partition_row(row) for row in all_rows if row["family_id"].startswith("pravopys")]
    _write_jsonl(paths["partition"], partition_rows)
    manifest_rows = [_manifest_row(row) for row in all_rows if row["family_id"].startswith("pravopys")]
    _write_jsonl(paths["evaluation_manifest"], manifest_rows)
    _write_json(paths["evaluation_manifest_receipt"], _evaluation_manifest_receipt(paths["evaluation_manifest"]))
    _patch_fixture_pins(monkeypatch, paths, row_count=6)
    monkeypatch.setattr(prav_context, "FAMILY_COUNTS", {"pravopys_2019_complete": 3, "pravopys_2026_complete": 3})
    monkeypatch.setattr(
        prav_context,
        "MAPPING_ACCOUNTING",
        {"self_parent_rule": 3, "child_parent_rule": 2},
    )
    monkeypatch.setattr(
        prav_context,
        "CONTEXT_ACCOUNTING",
        {"pravopys_parent_rule_context": 5, "pravopys_typed_exclusion": 1},
    )
    rows, _, _ = prav_context.build_context_rows(
        source_jsonl=paths["source_jsonl"],
        partition_path=paths["partition"],
        evaluation_manifest_path=paths["evaluation_manifest"],
        evaluation_manifest_receipt_path=paths["evaluation_manifest_receipt"],
    )
    excluded = next(row for row in rows if row.get("exclusion_reason_code") == "invalid_section_path")
    assert excluded["parent_section_path"] == []


def test_tar_duplicate_member_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = b"payload"
    member_name = prav_context.TARBALL_MEMBERS["source_jsonl"]
    tarball = tmp_path / "dup-member.tar.gz"
    with tarfile.open(tarball, "w:gz") as archive:
        for _ in range(2):
            info = tarfile.TarInfo(name=member_name)
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))
        for key, name in prav_context.TARBALL_MEMBERS.items():
            if key == "source_jsonl":
                continue
            info = tarfile.TarInfo(name=name)
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))
    monkeypatch.setattr(prav_context, "PINNED_CUSTODY_TARBALL_SHA256", prav_context.sha256_file(tarball))
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="duplicate tarball member names"):
        prav_context._extract_tarball_members(tarball, tmp_path / "out")


def test_tar_symlink_member_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = b"payload"
    tarball = tmp_path / "symlink.tar.gz"
    with tarfile.open(tarball, "w:gz") as archive:
        info = tarfile.TarInfo(name=prav_context.TARBALL_MEMBERS["source_jsonl"])
        info.type = tarfile.SYMTYPE
        info.linkname = "/etc/passwd"
        archive.addfile(info)
    monkeypatch.setattr(prav_context, "PINNED_CUSTODY_TARBALL_SHA256", prav_context.sha256_file(tarball))
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="regular file"):
        prav_context._extract_tarball_members(tarball, tmp_path / "out")


def test_tar_traversal_member_rejected() -> None:
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="traversal"):
        prav_context._safe_tar_member_name("../escape")


def test_hash_drift_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture_bundle(tmp_path)
    _patch_fixture_pins(monkeypatch, paths, row_count=5)
    _mutate_jsonl_row(
        paths["partition"],
        0,
        lambda row: row.update({"reason": "evaluation_only "}),
    )
    _assert_hash_guard_probe(
        monkeypatch,
        pin_attr="PINNED_PARTITION_SHA256",
        drifted_path=paths["partition"],
        match="partition manifest hash drift",
        paths=paths,
    )


def test_source_materialization_hash_drift_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture_bundle(tmp_path)
    _patch_fixture_pins(monkeypatch, paths, row_count=5)
    _mutate_jsonl_row(
        paths["source_jsonl"],
        0,
        lambda row: row.update({"document_or_edition_identity": "drifted"}),
    )
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="source materialization stream drift"):
        _call_build(paths)
    monkeypatch.setattr(
        prav_context,
        "PINNED_SOURCE_UNITS_JSONL_SHA256",
        prav_context.sha256_file(paths["source_jsonl"]),
    )
    try:
        _call_build(paths)
    except prav_context.PravopysEvaluationContextError as exc:
        assert "source materialization stream drift" not in str(exc)


def test_evaluation_context_manifest_hash_drift_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _fixture_bundle(tmp_path)
    _patch_fixture_pins(monkeypatch, paths, row_count=5)
    _mutate_jsonl_row(
        paths["evaluation_manifest"],
        0,
        lambda row: row.update({"context_kind": "frozen_source_unit_text "}),
    )
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="evaluation context manifest drift"):
        _call_build(paths)
    monkeypatch.setattr(
        prav_context,
        "PINNED_EVALUATION_CONTEXT_MANIFEST_JSONL_SHA256",
        prav_context.sha256_file(paths["evaluation_manifest"]),
    )
    with pytest.raises(prav_context.PravopysEvaluationContextError) as exc_info:
        _call_build(paths)
    assert "evaluation context manifest drift" not in str(exc_info.value)


def test_evaluation_context_manifest_receipt_binding_hash_drift_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _fixture_bundle(tmp_path)
    _patch_fixture_pins(monkeypatch, paths, row_count=5)
    _mutate_jsonl_row(
        paths["evaluation_manifest"],
        0,
        lambda row: row.update({"context_kind": "frozen_source_unit_text "}),
    )
    monkeypatch.setattr(
        prav_context,
        "PINNED_EVALUATION_CONTEXT_MANIFEST_JSONL_SHA256",
        prav_context.sha256_file(paths["evaluation_manifest"]),
    )
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="evaluation context manifest hash drift"):
        _call_build(paths)


def test_private_input_modes_and_symlinks_are_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture_bundle(tmp_path)
    _patch_fixture_pins(monkeypatch, paths, row_count=5)
    _simulate_group_readable_mode(monkeypatch, paths["source_jsonl"])
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="source materialization permissions must be 0600"):
        _call_build(paths)

    paths = _fixture_bundle(tmp_path / "partition-mode")
    _patch_fixture_pins(monkeypatch, paths, row_count=5)
    _simulate_group_readable_mode(monkeypatch, paths["partition"])
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="partition manifest permissions must be 0600"):
        _call_build(paths)

    paths = _fixture_bundle(tmp_path / "manifest-mode")
    _patch_fixture_pins(monkeypatch, paths, row_count=5)
    _simulate_group_readable_mode(monkeypatch, paths["evaluation_manifest"])
    with pytest.raises(
        prav_context.PravopysEvaluationContextError,
        match="evaluation context manifest permissions must be 0600",
    ):
        _call_build(paths)

    paths = _fixture_bundle(tmp_path / "source-symlink")
    _patch_fixture_pins(monkeypatch, paths, row_count=5)
    source_link = tmp_path / "source-link.jsonl"
    source_link.symlink_to(paths["source_jsonl"])
    paths["source_jsonl"] = source_link
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="symlink forbidden for source materialization"):
        _call_build(paths)

    paths = _fixture_bundle(tmp_path / "partition-symlink")
    _patch_fixture_pins(monkeypatch, paths, row_count=5)
    partition_link = tmp_path / "partition-link.jsonl"
    partition_link.symlink_to(paths["partition"])
    paths["partition"] = partition_link
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="symlink forbidden for partition manifest"):
        _call_build(paths)

    paths = _fixture_bundle(tmp_path / "manifest-symlink")
    _patch_fixture_pins(monkeypatch, paths, row_count=5)
    manifest_link = tmp_path / "manifest-link.jsonl"
    manifest_link.symlink_to(paths["evaluation_manifest"])
    paths["evaluation_manifest"] = manifest_link
    with pytest.raises(
        prav_context.PravopysEvaluationContextError,
        match="symlink forbidden for evaluation context manifest",
    ):
        _call_build(paths)

    secure_paths = _fixture_bundle(tmp_path / "secure-perms")
    assert stat.S_IMODE(secure_paths["source_jsonl"].stat().st_mode) == prav_context.PRIVATE_FILE_MODE
    assert stat.S_IMODE(secure_paths["source_jsonl"].parent.stat().st_mode) == prav_context.PRIVATE_DIR_MODE


def test_private_output_rejects_wrong_mode_and_ancestor_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _fixture_bundle(tmp_path)
    _patch_fixture_pins(monkeypatch, paths, row_count=5)

    _simulate_group_readable_mode(monkeypatch, paths["private_output"].parent)
    with pytest.raises(
        prav_context.PravopysEvaluationContextError,
        match="private output directory must be mode 0700",
    ):
        prav_context.materialize(
            source_jsonl=paths["source_jsonl"],
            partition_path=paths["partition"],
            evaluation_manifest_path=paths["evaluation_manifest"],
            evaluation_manifest_receipt_path=paths["evaluation_manifest_receipt"],
            private_output=paths["private_output"],
            public_receipt_path=paths["public_receipt"],
            started_at="2026-08-13T23:00:00Z",
            completed_at="2026-08-13T23:00:01Z",
        )

    paths = _fixture_bundle(tmp_path / "output-symlink")
    _patch_fixture_pins(monkeypatch, paths, row_count=5)
    root = tmp_path / "roots"
    real = root / "real"
    real.mkdir(parents=True, mode=prav_context.PRIVATE_DIR_MODE)
    link = root / "link"
    link.symlink_to(real)
    nested = link / "nested"
    nested.mkdir(mode=prav_context.PRIVATE_DIR_MODE)
    os.chmod(nested, prav_context.PRIVATE_DIR_MODE)
    private_output = nested / prav_context.PRIVATE_FILENAME
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="symlink forbidden for private output"):
        prav_context.materialize(
            source_jsonl=paths["source_jsonl"],
            partition_path=paths["partition"],
            evaluation_manifest_path=paths["evaluation_manifest"],
            evaluation_manifest_receipt_path=paths["evaluation_manifest_receipt"],
            private_output=private_output,
            public_receipt_path=tmp_path / "public-receipt-symlink.json",
            started_at="2026-08-13T23:00:00Z",
            completed_at="2026-08-13T23:00:01Z",
        )

    assert stat.S_IMODE(real.stat().st_mode) == prav_context.PRIVATE_DIR_MODE


def test_text_free_receipt_rejects_world_readable_permissions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_bytes(b"{}\n")
    os.chmod(receipt_path, prav_context.PRIVATE_FILE_MODE)
    _simulate_world_readable_lstat(monkeypatch, receipt_path)
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="text-free receipt permissions must be 0600"):
        prav_context._regular_text_free_receipt(receipt_path, "text-free receipt")
    assert stat.S_IMODE(receipt_path.stat().st_mode) == prav_context.PRIVATE_FILE_MODE


def test_duplicate_source_identity_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture_bundle(tmp_path)
    rows = _read_jsonl_rows(paths["source_jsonl"])
    rows.append(copy.deepcopy(rows[0]))
    _write_jsonl(paths["source_jsonl"], rows)
    _patch_fixture_pins(monkeypatch, paths, row_count=5)
    monkeypatch.setattr(eval_manifest, "V2_SOURCE_UNITS", 6)
    monkeypatch.setattr(
        prav_context,
        "PINNED_SOURCE_UNITS_JSONL_SHA256",
        prav_context.sha256_file(paths["source_jsonl"]),
    )
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="duplicate source identity: 6"):
        _call_build(paths)


def test_duplicate_partition_identity_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture_bundle(tmp_path)
    rows = _read_jsonl_rows(paths["partition"])
    rows.append(copy.deepcopy(rows[0]))
    _write_jsonl(paths["partition"], rows)
    _patch_fixture_pins(monkeypatch, paths, row_count=5)
    monkeypatch.setattr(eval_manifest, "ROW_COUNT", 6)
    monkeypatch.setattr(prav_context, "PINNED_PARTITION_SHA256", prav_context.sha256_file(paths["partition"]))
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="duplicate partition identity: 6"):
        _call_build(paths)


def test_missing_partition_identity_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture_bundle(tmp_path)
    manifest_rows = _read_jsonl_rows(paths["evaluation_manifest"])
    missing_id = str(manifest_rows[0]["unit_id"])
    _mutate_jsonl_row(
        paths["partition"],
        0,
        lambda row: row.update({"unit_id": f"{row['unit_id']}.mutated"}),
    )
    _patch_fixture_pins(monkeypatch, paths, row_count=5)
    with pytest.raises(
        prav_context.PravopysEvaluationContextError,
        match=f"partition identity missing: {missing_id}",
    ):
        _call_build(paths)


def test_missing_source_identity_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture_bundle(tmp_path)
    manifest_rows = _read_jsonl_rows(paths["evaluation_manifest"])
    missing_id = str(manifest_rows[0]["unit_id"])
    _mutate_jsonl_row(
        paths["source_jsonl"],
        0,
        lambda row: row.update({"unit_id": f"{row['unit_id']}.mutated"}),
    )
    _patch_fixture_pins(monkeypatch, paths, row_count=5)
    monkeypatch.setattr(
        prav_context,
        "PINNED_SOURCE_UNITS_JSONL_SHA256",
        prav_context.sha256_file(paths["source_jsonl"]),
    )
    with pytest.raises(
        prav_context.PravopysEvaluationContextError,
        match=f"source identity missing: {missing_id}",
    ):
        _call_build(paths)


def test_duplicate_parent_path_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture_bundle(tmp_path)
    rows = _read_jsonl_rows(paths["source_jsonl"])
    template = rows[0]
    section_path = template["frozen_locator"]["section_path"]
    duplicate_parent = _prav_row(
        str(template["family_id"]),
        list(section_path),
        "      99. інший батько з тим самим шляхом.",
        unit_id="unit.pravopys.duplicate-parent-path",
    )
    rows.append(duplicate_parent)
    _write_jsonl(paths["source_jsonl"], rows)
    partition_rows = [_partition_row(row) for row in rows]
    _write_jsonl(paths["partition"], partition_rows)
    manifest_rows = [_manifest_row(row) for row in rows]
    _write_jsonl(paths["evaluation_manifest"], manifest_rows)
    _write_json(paths["evaluation_manifest_receipt"], _evaluation_manifest_receipt(paths["evaluation_manifest"]))
    _patch_fixture_pins(monkeypatch, paths, row_count=6)
    monkeypatch.setattr(eval_manifest, "V2_SOURCE_UNITS", 6)
    monkeypatch.setattr(eval_manifest, "ROW_COUNT", 6)
    monkeypatch.setattr(prav_context, "ROW_COUNT", 6)
    monkeypatch.setattr(prav_context, "FAMILY_COUNTS", {"pravopys_2019_complete": 3, "pravopys_2026_complete": 3})
    monkeypatch.setattr(prav_context, "LANE_COUNTS", {"phenomenon_strata": 6})
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="duplicate parent path in materialization"):
        _call_build(paths)


def _swap_pravopys_family_on_row(rows: list[dict[str, object]], index: int) -> None:
    current = str(rows[index]["family_id"])
    swapped = "pravopys_2026_complete" if current == "pravopys_2019_complete" else "pravopys_2019_complete"
    rows[index] = dict(rows[index], family_id=swapped)


def _misbind_partition_family_preserving_counts(rows: list[dict[str, object]]) -> None:
    for index, row in enumerate(rows):
        if index == 0 or row["family_id"] != "pravopys_2026_complete":
            continue
        rows[0] = dict(rows[0], family_id="pravopys_2026_complete")
        rows[index] = dict(row, family_id="pravopys_2019_complete")
        return
    raise AssertionError("fixture partition rows missing a pravopys_2026_complete swap target")


@pytest.mark.parametrize(
    ("target", "mutator", "match"),
    [
        (
            "partition",
            _misbind_partition_family_preserving_counts,
            "partition/manifest family drift",
        ),
        (
            "source",
            lambda rows: _swap_pravopys_family_on_row(rows, 0),
            "source/manifest family drift",
        ),
        (
            "partition",
            lambda rows: rows.__setitem__(0, dict(rows[0], candidate_lane="clean_modern")),
            "lane drift",
        ),
        (
            "partition",
            lambda rows: rows.__setitem__(0, dict(rows[0], source_text_sha256="0" * 64)),
            "manifest source hash drift",
        ),
        (
            "partition",
            lambda rows: rows.__setitem__(0, dict(rows[0], frozen_locator_sha256="0" * 64)),
            "manifest locator hash drift",
        ),
        (
            "manifest",
            lambda rows: rows.__setitem__(0, dict(rows[0], source_text=str(rows[0]["source_text"]) + " ")),
            "source/manifest text drift",
        ),
        (
            "manifest",
            lambda rows: rows.__setitem__(0, dict(rows[0], source_text_sha256="0" * 64)),
            "manifest source hash drift",
        ),
        (
            "manifest",
            lambda rows: rows.__setitem__(0, dict(rows[0], frozen_locator_sha256="0" * 64)),
            "manifest locator hash drift",
        ),
    ],
)
def test_manifest_binding_mismatches_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    target: str,
    mutator: Callable[[list[dict[str, object]]], None],
    match: str,
) -> None:
    paths = _fixture_bundle(tmp_path)
    if target == "partition":
        rows = _read_jsonl_rows(paths["partition"])
        mutator(rows)
        _write_jsonl(paths["partition"], rows)
        pin_path = paths["partition"]
        pin_attr = "PINNED_PARTITION_SHA256"
    elif target == "source":
        rows = _read_jsonl_rows(paths["source_jsonl"])
        mutator(rows)
        _write_jsonl(paths["source_jsonl"], rows)
        pin_path = paths["source_jsonl"]
        pin_attr = "PINNED_SOURCE_UNITS_JSONL_SHA256"
    else:
        rows = _read_jsonl_rows(paths["evaluation_manifest"])
        mutator(rows)
        _write_jsonl(paths["evaluation_manifest"], rows)
        _write_json(paths["evaluation_manifest_receipt"], _evaluation_manifest_receipt(paths["evaluation_manifest"]))
        pin_path = paths["evaluation_manifest"]
        pin_attr = "PINNED_EVALUATION_CONTEXT_MANIFEST_JSONL_SHA256"
    _patch_fixture_pins(monkeypatch, paths, row_count=5)
    if target != "manifest":
        monkeypatch.setattr(prav_context, pin_attr, prav_context.sha256_file(pin_path))
    with pytest.raises(prav_context.PravopysEvaluationContextError, match=match):
        _call_build(paths)


def test_source_manifest_hash_drift_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture_bundle(tmp_path)
    wrong_hash = "0" * 64
    _mutate_jsonl_row(paths["partition"], 0, lambda row: row.update({"source_text_sha256": wrong_hash}))
    _mutate_jsonl_row(paths["evaluation_manifest"], 0, lambda row: row.update({"source_text_sha256": wrong_hash}))
    _write_json(paths["evaluation_manifest_receipt"], _evaluation_manifest_receipt(paths["evaluation_manifest"]))
    _patch_fixture_pins(monkeypatch, paths, row_count=5)
    monkeypatch.setattr(prav_context, "PINNED_PARTITION_SHA256", prav_context.sha256_file(paths["partition"]))
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="source/manifest hash drift"):
        _call_build(paths)


def test_source_manifest_locator_drift_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture_bundle(tmp_path)
    wrong_hash = "0" * 64
    _mutate_jsonl_row(paths["partition"], 0, lambda row: row.update({"frozen_locator_sha256": wrong_hash}))
    _mutate_jsonl_row(paths["evaluation_manifest"], 0, lambda row: row.update({"frozen_locator_sha256": wrong_hash}))
    _write_json(paths["evaluation_manifest_receipt"], _evaluation_manifest_receipt(paths["evaluation_manifest"]))
    _patch_fixture_pins(monkeypatch, paths, row_count=5)
    monkeypatch.setattr(prav_context, "PINNED_PARTITION_SHA256", prav_context.sha256_file(paths["partition"]))
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="source/manifest locator drift"):
        _call_build(paths)


def test_source_text_hash_drift_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture_bundle(tmp_path)
    _mutate_jsonl_row(
        paths["source_jsonl"],
        0,
        lambda row: row.update({"source_text_sha256": "0" * 64}),
    )
    _patch_fixture_pins(monkeypatch, paths, row_count=5)
    monkeypatch.setattr(
        prav_context,
        "PINNED_SOURCE_UNITS_JSONL_SHA256",
        prav_context.sha256_file(paths["source_jsonl"]),
    )
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="source text hash drift: 1"):
        _call_build(paths)


def test_pravopys_family_count_drift_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture_bundle(tmp_path)
    _mutate_jsonl_row(
        paths["evaluation_manifest"],
        0,
        lambda row: row.update({"family_id": "pravopys_2026_complete"}),
    )
    _write_json(paths["evaluation_manifest_receipt"], _evaluation_manifest_receipt(paths["evaluation_manifest"]))
    _patch_fixture_pins(monkeypatch, paths, row_count=5)
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="pravopys family count drift"):
        _call_build(paths)


def test_pravopys_lane_count_drift_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture_bundle(tmp_path)
    _mutate_jsonl_row(
        paths["evaluation_manifest"],
        0,
        lambda row: row.update({"candidate_lane": "clean_modern"}),
    )
    _write_json(paths["evaluation_manifest_receipt"], _evaluation_manifest_receipt(paths["evaluation_manifest"]))
    _patch_fixture_pins(monkeypatch, paths, row_count=5)
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="pravopys lane count drift"):
        _call_build(paths)


def test_partition_family_count_drift_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture_bundle(tmp_path)
    _mutate_jsonl_row(
        paths["partition"],
        0,
        lambda row: row.update({"family_id": "pravopys_2026_complete"}),
    )
    _patch_fixture_pins(monkeypatch, paths, row_count=5)
    monkeypatch.setattr(prav_context, "PINNED_PARTITION_SHA256", prav_context.sha256_file(paths["partition"]))
    with pytest.raises(
        prav_context.PravopysEvaluationContextError,
        match="partition family count drift: pravopys_2019_complete",
    ):
        _call_build(paths)


def test_unicode_offset_round_trip_drift_fails_closed() -> None:
    parent_text = "      4. Батько.\n      1) дитяче правило."
    unit_text = "      1) дитяче правило."
    start = parent_text.find(unit_text)
    end = start + len(unit_text)

    class _SliceDriftParent(str):
        def __getitem__(self, key: object) -> str:
            if key == slice(start, end):
                return "x" * len(unit_text)
            return super().__getitem__(key)

    with pytest.raises(prav_context.PravopysEvaluationContextError, match="unicode offset round-trip drift"):
        prav_context._unique_codepoint_offsets(_SliceDriftParent(parent_text), unit_text)


def test_materialize_writes_restricted_private_output_and_text_free_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _fixture_bundle(tmp_path)
    _patch_fixture_pins(monkeypatch, paths, row_count=5)
    receipt = prav_context.materialize(
        source_jsonl=paths["source_jsonl"],
        partition_path=paths["partition"],
        evaluation_manifest_path=paths["evaluation_manifest"],
        evaluation_manifest_receipt_path=paths["evaluation_manifest_receipt"],
        private_output=paths["private_output"],
        public_receipt_path=paths["public_receipt"],
        started_at="2026-08-13T23:00:00Z",
        completed_at="2026-08-13T23:00:01Z",
    )
    assert paths["private_output"].exists()
    assert stat.S_IMODE(paths["private_output"].stat().st_mode) == prav_context.PRIVATE_FILE_MODE
    assert stat.S_IMODE(paths["private_output"].parent.stat().st_mode) == prav_context.PRIVATE_DIR_MODE
    assert stat.S_IMODE(paths["public_receipt"].stat().st_mode) == prav_context.PRIVATE_FILE_MODE
    serialized = json.dumps(receipt, ensure_ascii=False)
    assert "complete_parent_rule_context" not in serialized
    assert "unit_id" not in serialized
    assert receipt["provider_calls"] is False
    assert receipt["gates"]["phase4_blocked"] is True


def test_public_schema_is_closed_and_text_free() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    serialized = json.dumps(schema, ensure_ascii=False)
    assert "complete_parent_rule_context" not in serialized
    assert "unit_id" not in serialized
    assert schema["additionalProperties"] is False


def test_deterministic_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture_bundle(tmp_path)
    _patch_fixture_pins(monkeypatch, paths, row_count=5)
    first = prav_context.materialize(
        source_jsonl=paths["source_jsonl"],
        partition_path=paths["partition"],
        evaluation_manifest_path=paths["evaluation_manifest"],
        evaluation_manifest_receipt_path=paths["evaluation_manifest_receipt"],
        private_output=paths["private_output"],
        public_receipt_path=tmp_path / "receipt-a.json",
        started_at="2026-08-13T23:00:00Z",
        completed_at="2026-08-13T23:00:01Z",
    )
    second = prav_context.materialize(
        source_jsonl=paths["source_jsonl"],
        partition_path=paths["partition"],
        evaluation_manifest_path=paths["evaluation_manifest"],
        evaluation_manifest_receipt_path=paths["evaluation_manifest_receipt"],
        private_output=tmp_path / "private-b.jsonl",
        public_receipt_path=tmp_path / "receipt-b.json",
        started_at="2026-08-13T23:00:00Z",
        completed_at="2026-08-13T23:00:01Z",
    )
    assert first["context"]["private_jsonl_sha256"] == second["context"]["private_jsonl_sha256"]


def test_live_database_path_is_rejected(tmp_path: Path) -> None:
    database = tmp_path / "sources.db"
    database.write_bytes(b"sqlite")
    exit_code = prav_context.main(
        [
            "build",
            "--source-jsonl",
            str(tmp_path / "source.jsonl"),
            "--partition",
            str(tmp_path / "partition.jsonl"),
            "--evaluation-manifest",
            str(tmp_path / "manifest.jsonl"),
            "--evaluation-manifest-receipt",
            str(EVAL_RECEIPT),
            "--private-output",
            str(tmp_path / "out.jsonl"),
            "--public-receipt",
            str(tmp_path / "public.json"),
            "--database",
            str(database),
        ]
    )
    assert exit_code == 2


def test_evaluation_context_manifest_receipt_file_drift_fails_closed(tmp_path: Path) -> None:
    drifted = tmp_path / "evaluation_context_manifest_receipt_v1.json"
    receipt = json.loads(EVAL_RECEIPT.read_text(encoding="utf-8"))
    drifted.write_bytes((json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    assert json.loads(drifted.read_text(encoding="utf-8")) == receipt
    assert prav_context.sha256_file(drifted) != prav_context.PINNED_EVALUATION_CONTEXT_MANIFEST_RECEIPT_FILE_SHA256
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="manifest receipt file drift"):
        prav_context._validate_evaluation_context_manifest_receipt(drifted)


def test_evaluation_context_manifest_receipt_body_drift_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    drifted = tmp_path / "evaluation_context_manifest_receipt_v1.json"
    receipt = json.loads(EVAL_RECEIPT.read_text(encoding="utf-8"))
    original_body = str(receipt["receipt_sha256"])
    receipt["receipt_sha256"] = "0" * 64
    drifted.write_bytes(EVAL_RECEIPT.read_bytes().replace(original_body.encode("ascii"), b"0" * 64))
    assert json.loads(drifted.read_bytes().decode("utf-8"))["receipt_sha256"] == "0" * 64
    monkeypatch.setattr(
        prav_context,
        "PINNED_EVALUATION_CONTEXT_MANIFEST_RECEIPT_FILE_SHA256",
        prav_context.sha256_file(drifted),
    )
    monkeypatch.setattr(eval_manifest, "validate_receipt", lambda value: dict(value))
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="manifest receipt body drift"):
        prav_context._validate_evaluation_context_manifest_receipt(drifted)


def test_validate_receipt_rejects_binding_drift() -> None:
    receipt = _rehash_prav_receipt(_load_public_receipt())
    receipt["bindings"] = dict(receipt["bindings"])
    receipt["bindings"]["implementation_sha256"] = "0" * 64
    _rehash_prav_receipt(receipt)
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="implementation binding drift"):
        prav_context.validate_receipt(receipt)


def test_validate_receipt_rejects_gate_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(prav_context, "_schema_validator", _accept_all_schema_validator)
    receipt = _rehash_prav_receipt(_load_public_receipt())
    receipt["gates"] = dict(receipt["gates"])
    receipt["gates"]["phase4_blocked"] = False
    _rehash_prav_receipt(receipt)
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="phase 4 opened"):
        prav_context.validate_receipt(receipt)


def test_validate_receipt_rejects_row_count_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(prav_context, "_schema_validator", _accept_all_schema_validator)
    receipt = _rehash_prav_receipt(_load_public_receipt())
    receipt["row_count"] = int(receipt["row_count"]) + 1
    _rehash_prav_receipt(receipt)
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="row count drift"):
        prav_context.validate_receipt(receipt)


def test_validate_receipt_rejects_receipt_self_hash_drift() -> None:
    receipt = _load_public_receipt()
    receipt["receipt_sha256"] = "0" * 64
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="receipt body hash drift"):
        prav_context.validate_receipt(receipt)


def test_verify_existing_rejects_tampered_private_jsonl(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _fixture_bundle(tmp_path)
    _patch_fixture_pins(monkeypatch, paths, row_count=5, stub_prav_validate=False)
    prav_context.materialize(
        source_jsonl=paths["source_jsonl"],
        partition_path=paths["partition"],
        evaluation_manifest_path=paths["evaluation_manifest"],
        evaluation_manifest_receipt_path=paths["evaluation_manifest_receipt"],
        private_output=paths["private_output"],
        public_receipt_path=paths["public_receipt"],
        started_at="2026-08-13T23:00:00Z",
        completed_at="2026-08-13T23:00:01Z",
    )
    original = paths["private_output"].read_bytes()
    paths["private_output"].write_bytes(original + b" ")
    os.chmod(paths["private_output"], prav_context.PRIVATE_FILE_MODE)
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="private context artifact drift"):
        prav_context.verify_existing(
            source_jsonl=paths["source_jsonl"],
            partition_path=paths["partition"],
            evaluation_manifest_path=paths["evaluation_manifest"],
            evaluation_manifest_receipt_path=paths["evaluation_manifest_receipt"],
            private_output=paths["private_output"],
            public_receipt_path=paths["public_receipt"],
        )


def test_verify_existing_rejects_tampered_public_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _fixture_bundle(tmp_path)
    _patch_fixture_pins(monkeypatch, paths, row_count=5, stub_prav_validate=False)
    prav_context.materialize(
        source_jsonl=paths["source_jsonl"],
        partition_path=paths["partition"],
        evaluation_manifest_path=paths["evaluation_manifest"],
        evaluation_manifest_receipt_path=paths["evaluation_manifest_receipt"],
        private_output=paths["private_output"],
        public_receipt_path=paths["public_receipt"],
        started_at="2026-08-13T23:00:00Z",
        completed_at="2026-08-13T23:00:01Z",
    )
    receipt = json.loads(paths["public_receipt"].read_text(encoding="utf-8"))
    receipt["receipt_sha256"] = "0" * 64
    paths["public_receipt"].write_bytes(prav_context.canonical_bytes(receipt))
    os.chmod(paths["public_receipt"], prav_context.PRIVATE_FILE_MODE)
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="receipt body hash drift"):
        prav_context.verify_existing(
            source_jsonl=paths["source_jsonl"],
            partition_path=paths["partition"],
            evaluation_manifest_path=paths["evaluation_manifest"],
            evaluation_manifest_receipt_path=paths["evaluation_manifest_receipt"],
            private_output=paths["private_output"],
            public_receipt_path=paths["public_receipt"],
        )


def test_production_replay_against_drive_custody() -> None:
    drive = (
        Path.home() / "Library/CloudStorage/GoogleDrive-krisztian.koos@gmail.com/My Drive/Projects/learn-ukrainian-data"
    )
    tarball = drive / "backups/phase3-6375/20260811T090325Z/phase3-private-and-durable-artifacts.tar.gz"
    manifest = (
        drive
        / "backups/phase3-6375/20260813T220000Z/phase3-evaluation-context-manifest-v1/evaluation_context_manifest_v1.jsonl"
    )
    backup_dir = drive / "backups/phase3-6375/20260813T231656Z"
    public_receipt = ROOT / "data/projects/open_model_data/inventory/phase3_pravopys_evaluation_context_receipt_v1.json"
    if not tarball.exists() or not manifest.exists():
        pytest.skip("Drive custody artifacts unavailable")
    if backup_dir.exists() and (backup_dir / prav_context.PRIVATE_FILENAME).exists():
        receipt = json.loads(public_receipt.read_text(encoding="utf-8"))
        prav_context.validate_receipt(receipt)
        assert receipt["context_accounting"] == prav_context.CONTEXT_ACCOUNTING
        assert receipt["mapping_accounting"] == prav_context.MAPPING_ACCOUNTING
        return
    receipt = prav_context.production_run(
        custody_tarball=tarball,
        evaluation_manifest_path=manifest,
        evaluation_manifest_receipt_path=EVAL_RECEIPT,
        drive_backup_dir=backup_dir,
        public_receipt_path=public_receipt,
        started_at="2026-08-13T23:00:00Z",
        completed_at="2026-08-13T23:00:30Z",
    )
    prav_context.validate_receipt(receipt)
    assert receipt["row_count"] == 413
