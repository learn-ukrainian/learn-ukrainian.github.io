from __future__ import annotations

import io
import json
import os
import stat
import tarfile
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
    private.mkdir(mode=prav_context.PRIVATE_DIR_MODE)
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


def _patch_fixture_pins(monkeypatch: pytest.MonkeyPatch, paths: dict[str, Path], row_count: int) -> None:
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
    monkeypatch.setattr(prav_context, "validate_receipt", lambda receipt: dict(receipt))


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
    paths["partition"].write_bytes(paths["partition"].read_bytes() + b"\n")
    with pytest.raises(prav_context.PravopysEvaluationContextError, match="partition"):
        prav_context.build_context_rows(
            source_jsonl=paths["source_jsonl"],
            partition_path=paths["partition"],
            evaluation_manifest_path=paths["evaluation_manifest"],
            evaluation_manifest_receipt_path=paths["evaluation_manifest_receipt"],
        )


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
