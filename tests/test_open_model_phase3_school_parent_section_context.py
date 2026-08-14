from __future__ import annotations

import inspect
import json
import os
import stat
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_school_parent_section_context as parent_ctx

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "data/projects/open_model_data/contracts/phase3_school_parent_section_context_receipt_v1.schema.json"
PUBLIC_RECEIPT = ROOT / "data/projects/open_model_data/inventory/phase3_school_parent_section_context_receipt_v1.json"
DRIVE_ROOT = (
    Path.home() / "Library/CloudStorage/GoogleDrive-krisztian.koos@gmail.com/My Drive/Projects/learn-ukrainian-data"
)
CUSTODY_TARBALL = DRIVE_ROOT / "backups/phase3-6375/20260811T090325Z/phase3-private-and-durable-artifacts.tar.gz"
DRIVE_BACKUP_DIR = DRIVE_ROOT / "backups/phase3-6375/20260814T024800Z/phase3-school-parent-section-context-v1"


def _school_row(
    *,
    unit_suffix: str,
    source_file: str,
    record_id: int,
    chunk_id: str,
    parent_section_id: int | None,
    text: str,
) -> dict[str, object]:
    unit_id = f"unit.school_textbooks.{unit_suffix}"
    unit_sha = parent_ctx.sha256_bytes(f"{unit_id}:{text}".encode())
    return {
        "family_id": "school_textbooks",
        "unit_id": unit_id,
        "unit_sha256": unit_sha,
        "frozen_locator": {"kind": "sqlite_row", "table": "textbooks", "rowid": record_id},
        "frozen_locator_sha256": parent_ctx.sha256_bytes(str(record_id).encode()),
        "document_or_edition_identity": source_file,
        "source_text": text,
        "source_text_sha256": parent_ctx.sha256_bytes(text.encode()),
        "source_record": {
            "id": record_id,
            "chunk_id": chunk_id,
            "source_file": source_file,
            "parent_section_id": parent_section_id,
            "text": text,
        },
    }


def _partition_row(source_row: dict[str, object]) -> dict[str, object]:
    return {
        "family_id": "school_textbooks",
        "unit_id": source_row["unit_id"],
        "unit_sha256": source_row["unit_sha256"],
        "reason": "evaluation_only",
        "candidate_lane": "phenomenon_strata",
        "source_text_sha256": source_row["source_text_sha256"],
        "frozen_locator_sha256": source_row["frozen_locator_sha256"],
    }


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, parent_ctx.PRIVATE_DIR_MODE)
    path.write_bytes(b"".join(parent_ctx.canonical_bytes(row) for row in rows))
    os.chmod(path, parent_ctx.PRIVATE_FILE_MODE)


def _fixture(tmp_path: Path) -> dict[str, object]:
    # Positive group: two siblings with unicode punctuation / apostrophe / combining mark.
    complete_a = _school_row(
        unit_suffix="complete-a",
        source_file="book-a.jsonl",
        record_id=1,
        chunk_id="c1",
        parent_section_id=10,
        text="Перше речення — з тире.",
    )
    complete_b = _school_row(
        unit_suffix="complete-b",
        source_file="book-a.jsonl",
        record_id=2,
        chunk_id="c2",
        parent_section_id=10,
        text="Друге: м'ята й зе́лень.",
    )
    # Negative null-parent held-outs (excluded from output).
    null_a = _school_row(
        unit_suffix="null-a",
        source_file="book-b.jsonl",
        record_id=3,
        chunk_id="c3",
        parent_section_id=None,
        text="Негативний рядок A.",
    )
    null_b = _school_row(
        unit_suffix="null-b",
        source_file="book-b.jsonl",
        record_id=4,
        chunk_id="c4",
        parent_section_id=None,
        text="Негативний рядок B.",
    )
    # Non-held-out sibling in another complete group (not emitted).
    other = _school_row(
        unit_suffix="other",
        source_file="book-c.jsonl",
        record_id=5,
        chunk_id="c5",
        parent_section_id=20,
        text="Поза вибіркою.",
    )

    source_rows = [complete_a, complete_b, null_a, null_b, other]
    heldout = [complete_a, complete_b, null_a, null_b]

    private = tmp_path / "private"
    private.mkdir(mode=parent_ctx.PRIVATE_DIR_MODE)
    os.chmod(private, parent_ctx.PRIVATE_DIR_MODE)
    source_path = private / "source_units_v1.jsonl"
    partition_path = private / "partition_manifest_v1.jsonl"
    _write_jsonl(source_path, source_rows)
    _write_jsonl(partition_path, [_partition_row(row) for row in heldout])

    return {
        "source_jsonl": source_path,
        "partition": partition_path,
        "private_output": private / parent_ctx.PRIVATE_FILENAME,
        "public_receipt": tmp_path / "public-receipt.json",
        "complete_a": complete_a,
        "complete_b": complete_b,
        "null_a": null_a,
        "null_b": null_b,
        "source_rows": source_rows,
        "heldout": heldout,
    }


def _patch_pins(monkeypatch: pytest.MonkeyPatch, paths: dict[str, object]) -> None:
    monkeypatch.setattr(
        parent_ctx,
        "PINNED_SOURCE_UNITS_JSONL_SHA256",
        parent_ctx.sha256_file(paths["source_jsonl"]),  # type: ignore[arg-type]
    )
    monkeypatch.setattr(
        parent_ctx,
        "PINNED_PARTITION_SHA256",
        parent_ctx.sha256_file(paths["partition"]),  # type: ignore[arg-type]
    )
    monkeypatch.setattr(parent_ctx, "SCHOOL_UNIVERSE", 5)
    monkeypatch.setattr(parent_ctx, "SCHOOL_HELDOUT", 4)
    monkeypatch.setattr(parent_ctx, "PARENT_NULL_HELDOUT", 2)
    monkeypatch.setattr(parent_ctx, "PARENT_COMPLETE_HELDOUT", 2)
    monkeypatch.setattr(parent_ctx, "SCHOOL_NULL_PARENT_ROWS", 2)
    monkeypatch.setattr(parent_ctx, "NON_NULL_PARENT_GROUPS", 2)
    monkeypatch.setattr(parent_ctx, "POSITIVE_HELDOUT_PARENT_GROUPS", 1)
    monkeypatch.setattr(parent_ctx, "POSITIVE_HELDOUT_SOURCE_FILES", 1)
    monkeypatch.setattr(parent_ctx, "_validate_public_bindings", lambda: None)

    class _AcceptAll:
        def validate(self, _value: object) -> None:
            return None

    monkeypatch.setattr(parent_ctx, "_schema_validator", lambda: _AcceptAll())


def test_schema_parses() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert schema["properties"]["denominators"]["properties"]["positive_parent_section_heldout"]["const"] == 3526
    assert schema["properties"]["gates"]["properties"]["phase4_blocked"]["const"] is True
    assert schema["properties"]["gates"]["properties"]["school_complete_context_ready"]["const"] is False


def test_assemble_roundtrip_offsets_unicode() -> None:
    texts = ["Апостроф: м'ята.", "Комбінування: зе́лень — так."]
    context, offsets = parent_ctx._assemble_parent_section(texts)
    assert parent_ctx.PARENT_SECTION_SEPARATOR.join(texts) == context
    for (start, end), text in zip(offsets, texts, strict=True):
        assert context[start:end] == text


def test_hermetic_materialize_roundtrip_and_negative_exclusion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path)
    _patch_pins(monkeypatch, paths)
    receipt = parent_ctx.materialize(
        source_jsonl=paths["source_jsonl"],  # type: ignore[arg-type]
        partition_path=paths["partition"],  # type: ignore[arg-type]
        private_output=paths["private_output"],  # type: ignore[arg-type]
        public_receipt_path=paths["public_receipt"],  # type: ignore[arg-type]
        started_at="2026-08-14T02:48:00Z",
        completed_at="2026-08-14T02:48:30Z",
    )
    assert receipt["denominators"]["positive_parent_section_heldout"] == 2
    assert receipt["denominators"]["negative_null_parent_heldout_excluded"] == 2
    assert receipt["provider_calls"] is False
    assert receipt["labels_present"] is False
    assert receipt["semantic_gold"] is False
    assert receipt["gates"]["school_complete_context_ready"] is False
    assert receipt["gates"]["phase4_blocked"] is True
    assert receipt["gates"]["phase3_complete"] is False
    assert receipt["gates"]["source_coverage_ready"] is False

    private_path = paths["private_output"]
    assert isinstance(private_path, Path)
    assert stat.S_IMODE(private_path.stat().st_mode) == 0o600
    rows = [json.loads(line) for line in private_path.read_text(encoding="utf-8").splitlines() if line]
    assert len(rows) == 2
    unit_ids = {row["unit_id"] for row in rows}
    assert paths["complete_a"]["unit_id"] in unit_ids  # type: ignore[index]
    assert paths["complete_b"]["unit_id"] in unit_ids  # type: ignore[index]
    assert paths["null_a"]["unit_id"] not in unit_ids  # type: ignore[index]
    assert paths["null_b"]["unit_id"] not in unit_ids  # type: ignore[index]

    for row in rows:
        context = row["complete_parent_section_context"]
        start = row["unit_text_start_offset"]
        end = row["unit_text_end_offset"]
        assert context[start:end] == row["unit_text"]
        assert row["sibling_count"] == 2
        assert row["separator"] == parent_ctx.PARENT_SECTION_SEPARATOR
        assert row["context_kind"] == parent_ctx.CONTEXT_KIND
        assert row["complete_sentence_context"] is False

    public = paths["public_receipt"]
    assert isinstance(public, Path)
    assert stat.S_IMODE(public.stat().st_mode) == 0o600
    public_text = public.read_text(encoding="utf-8")
    assert "unit.school_textbooks." not in public_text
    assert "Перше" not in public_text
    assert "Негативний" not in public_text
    assert not any("\u0400" <= ch <= "\u04ff" for ch in public_text)

    # Idempotent identical rerun
    again = parent_ctx.materialize(
        source_jsonl=paths["source_jsonl"],  # type: ignore[arg-type]
        partition_path=paths["partition"],  # type: ignore[arg-type]
        private_output=paths["private_output"],  # type: ignore[arg-type]
        public_receipt_path=paths["public_receipt"],  # type: ignore[arg-type]
        started_at="2026-08-14T02:48:00Z",
        completed_at="2026-08-14T02:48:30Z",
    )
    assert again["receipt_sha256"] == receipt["receipt_sha256"]
    assert again["context"]["private_jsonl_sha256"] == receipt["context"]["private_jsonl_sha256"]
    assert stat.S_IMODE(public.stat().st_mode) == 0o600


def test_verify_existing_rejects_implementation_binding_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _fixture(tmp_path)
    _patch_pins(monkeypatch, paths)
    parent_ctx.materialize(
        source_jsonl=paths["source_jsonl"],  # type: ignore[arg-type]
        partition_path=paths["partition"],  # type: ignore[arg-type]
        private_output=paths["private_output"],  # type: ignore[arg-type]
        public_receipt_path=paths["public_receipt"],  # type: ignore[arg-type]
        started_at="2026-08-14T02:48:00Z",
        completed_at="2026-08-14T02:48:30Z",
    )
    public = paths["public_receipt"]
    assert isinstance(public, Path)
    receipt = json.loads(public.read_text(encoding="utf-8"))
    receipt["bindings"] = dict(receipt["bindings"])
    receipt["bindings"]["implementation_sha256"] = "0" * 64
    receipt["receipt_sha256"] = parent_ctx.receipt_sha256(receipt)
    # Mutate bytes in place; leave mode alone (no chmod 0644).
    public.write_bytes(parent_ctx.canonical_bytes(receipt))
    os.chmod(public, parent_ctx.PRIVATE_FILE_MODE)
    with pytest.raises(parent_ctx.SchoolParentSectionContextError, match="implementation binding drift"):
        parent_ctx.verify_existing(
            source_jsonl=paths["source_jsonl"],  # type: ignore[arg-type]
            partition_path=paths["partition"],  # type: ignore[arg-type]
            private_output=paths["private_output"],  # type: ignore[arg-type]
            public_receipt_path=public,
        )


def test_verify_existing_rejects_schema_binding_mutation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path)
    _patch_pins(monkeypatch, paths)
    parent_ctx.materialize(
        source_jsonl=paths["source_jsonl"],  # type: ignore[arg-type]
        partition_path=paths["partition"],  # type: ignore[arg-type]
        private_output=paths["private_output"],  # type: ignore[arg-type]
        public_receipt_path=paths["public_receipt"],  # type: ignore[arg-type]
        started_at="2026-08-14T02:48:00Z",
        completed_at="2026-08-14T02:48:30Z",
    )
    public = paths["public_receipt"]
    assert isinstance(public, Path)
    receipt = json.loads(public.read_text(encoding="utf-8"))
    receipt["bindings"] = dict(receipt["bindings"])
    receipt["bindings"]["receipt_schema_sha256"] = "0" * 64
    receipt["receipt_sha256"] = parent_ctx.receipt_sha256(receipt)
    public.write_bytes(parent_ctx.canonical_bytes(receipt))
    os.chmod(public, parent_ctx.PRIVATE_FILE_MODE)
    with pytest.raises(parent_ctx.SchoolParentSectionContextError, match="schema binding drift"):
        parent_ctx.verify_existing(
            source_jsonl=paths["source_jsonl"],  # type: ignore[arg-type]
            partition_path=paths["partition"],  # type: ignore[arg-type]
            private_output=paths["private_output"],  # type: ignore[arg-type]
            public_receipt_path=public,
        )


def test_verify_existing_rejects_stale_pinned_binding_mutation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path)
    _patch_pins(monkeypatch, paths)
    parent_ctx.materialize(
        source_jsonl=paths["source_jsonl"],  # type: ignore[arg-type]
        partition_path=paths["partition"],  # type: ignore[arg-type]
        private_output=paths["private_output"],  # type: ignore[arg-type]
        public_receipt_path=paths["public_receipt"],  # type: ignore[arg-type]
        started_at="2026-08-14T02:48:00Z",
        completed_at="2026-08-14T02:48:30Z",
    )
    public = paths["public_receipt"]
    assert isinstance(public, Path)
    receipt = json.loads(public.read_text(encoding="utf-8"))
    receipt["bindings"] = dict(receipt["bindings"])
    receipt["bindings"]["source_universe_receipt_sha256"] = "0" * 64
    receipt["receipt_sha256"] = parent_ctx.receipt_sha256(receipt)
    public.write_bytes(parent_ctx.canonical_bytes(receipt))
    os.chmod(public, parent_ctx.PRIVATE_FILE_MODE)
    with pytest.raises(parent_ctx.SchoolParentSectionContextError, match="source universe binding drift"):
        parent_ctx.verify_existing(
            source_jsonl=paths["source_jsonl"],  # type: ignore[arg-type]
            partition_path=paths["partition"],  # type: ignore[arg-type]
            private_output=paths["private_output"],  # type: ignore[arg-type]
            public_receipt_path=public,
        )


def test_custody_receipt_preserves_prior_via_versioned_successors(tmp_path: Path) -> None:
    drive = tmp_path / "drive"
    drive.mkdir(mode=0o700)
    os.chmod(drive, 0o700)
    first = {
        "schema_version": "phase3_school_parent_section_context_custody_receipt_v1",
        "artifacts": {"public_receipt_sha256": "a" * 64},
    }
    second = {
        "schema_version": "phase3_school_parent_section_context_custody_receipt_v1",
        "artifacts": {"public_receipt_sha256": "b" * 64},
    }
    third = {
        "schema_version": "phase3_school_parent_section_context_custody_receipt_v1",
        "artifacts": {"public_receipt_sha256": "c" * 64},
    }
    primary = parent_ctx._write_custody_receipt(drive, first)
    assert primary.name == parent_ctx.CUSTODY_RECEIPT_FILENAME
    assert stat.S_IMODE(primary.stat().st_mode) == 0o600
    successor = parent_ctx._write_custody_receipt(drive, second)
    assert successor.name == parent_ctx.CUSTODY_RECEIPT_SUCCESSOR_FILENAME
    assert primary.read_bytes() == parent_ctx.canonical_bytes(first)
    assert successor.read_bytes() == parent_ctx.canonical_bytes(second)
    assert parent_ctx._write_custody_receipt(drive, second) == successor
    second_successor = parent_ctx._write_custody_receipt(drive, third)
    assert second_successor.name == f"{parent_ctx.CUSTODY_RECEIPT_SUCCESSOR_STEM}.2.json"
    assert second_successor.read_bytes() == parent_ctx.canonical_bytes(third)
    assert parent_ctx._write_custody_receipt(drive, third) == second_successor
    assert primary.read_bytes() == parent_ctx.canonical_bytes(first)
    assert successor.read_bytes() == parent_ctx.canonical_bytes(second)


def test_idempotent_rerun_refuses_changed_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path)
    _patch_pins(monkeypatch, paths)
    parent_ctx.materialize(
        source_jsonl=paths["source_jsonl"],  # type: ignore[arg-type]
        partition_path=paths["partition"],  # type: ignore[arg-type]
        private_output=paths["private_output"],  # type: ignore[arg-type]
        public_receipt_path=paths["public_receipt"],  # type: ignore[arg-type]
        started_at="2026-08-14T02:48:00Z",
        completed_at="2026-08-14T02:48:30Z",
    )
    private_path = paths["private_output"]
    assert isinstance(private_path, Path)
    private_path.write_bytes(private_path.read_bytes() + b" ")
    os.chmod(private_path, 0o600)
    with pytest.raises(parent_ctx.SchoolParentSectionContextError, match="refusing to overwrite"):
        parent_ctx.materialize(
            source_jsonl=paths["source_jsonl"],  # type: ignore[arg-type]
            partition_path=paths["partition"],  # type: ignore[arg-type]
            private_output=paths["private_output"],  # type: ignore[arg-type]
            public_receipt_path=paths["public_receipt"],  # type: ignore[arg-type]
            started_at="2026-08-14T02:48:00Z",
            completed_at="2026-08-14T02:48:30Z",
        )


def test_missing_duplicate_extra_heldouts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path)
    _patch_pins(monkeypatch, paths)

    # Extra held-out in partition only.
    partition = paths["partition"]
    assert isinstance(partition, Path)
    extra = _partition_row(
        _school_row(
            unit_suffix="extra",
            source_file="book-x.jsonl",
            record_id=99,
            chunk_id="cx",
            parent_section_id=10,
            text="extra",
        )
    )
    with partition.open("ab") as handle:
        handle.write(parent_ctx.canonical_bytes(extra))
    monkeypatch.setattr(parent_ctx, "PINNED_PARTITION_SHA256", parent_ctx.sha256_file(partition))
    with pytest.raises(parent_ctx.SchoolParentSectionContextError, match="held-out school count drift"):
        parent_ctx.build_context_rows(
            source_jsonl=paths["source_jsonl"],  # type: ignore[arg-type]
            partition_path=partition,
        )


def test_null_parent_rejected_for_positive_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path)
    _patch_pins(monkeypatch, paths)
    # Force constants to expect zero null held-outs while fixture still has them.
    monkeypatch.setattr(parent_ctx, "PARENT_NULL_HELDOUT", 0)
    monkeypatch.setattr(parent_ctx, "PARENT_COMPLETE_HELDOUT", 4)
    with pytest.raises(parent_ctx.SchoolParentSectionContextError, match="held-out null parent_section_id drift"):
        parent_ctx.build_context_rows(
            source_jsonl=paths["source_jsonl"],  # type: ignore[arg-type]
            partition_path=paths["partition"],  # type: ignore[arg-type]
        )


def test_stale_source_hash_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path)
    _patch_pins(monkeypatch, paths)
    monkeypatch.setattr(parent_ctx, "PINNED_SOURCE_UNITS_JSONL_SHA256", "0" * 64)
    with pytest.raises(parent_ctx.SchoolParentSectionContextError, match="source units hash drift"):
        parent_ctx.build_context_rows(
            source_jsonl=paths["source_jsonl"],  # type: ignore[arg-type]
            partition_path=paths["partition"],  # type: ignore[arg-type]
        )


def test_symlink_and_output_collision_rejected(tmp_path: Path) -> None:
    target = tmp_path / "real.jsonl"
    target.write_bytes(b"{}\n")
    os.chmod(target, 0o600)
    link = tmp_path / "link.jsonl"
    link.symlink_to(target)
    with pytest.raises(parent_ctx.SchoolParentSectionContextError, match="symlink forbidden"):
        parent_ctx._regular_file(link, "artifact")

    out = tmp_path / "out.jsonl"
    parent_ctx._atomic_write(out, b"aaa\n")
    with pytest.raises(parent_ctx.SchoolParentSectionContextError, match="refusing to overwrite"):
        parent_ctx._write_immutable(out, b"bbb\n", label="private context artifact")


def test_atomic_write_api_and_mode(tmp_path: Path) -> None:
    params = inspect.signature(parent_ctx._atomic_write).parameters
    assert list(params) == ["path", "payload"]
    target = tmp_path / "secret.bin"
    parent_ctx._atomic_write(target, b"secret")
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    public = tmp_path / "public.json"
    parent_ctx._atomic_write(public, b"{}\n")
    assert stat.S_IMODE(public.stat().st_mode) == 0o600


def test_public_receipt_creates_private_and_accepts_tracked_mode(tmp_path: Path) -> None:
    path = tmp_path / "receipt.json"
    payload = b'{"ok":true}\n'
    parent_ctx._write_public_receipt(path, payload)
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    parent_ctx._write_public_receipt(path, payload)
    assert path.read_bytes() == payload
    with pytest.raises(
        parent_ctx.SchoolParentSectionContextError, match="refusing to overwrite changed public receipt"
    ):
        parent_ctx._write_public_receipt(path, b'{"ok":false}\n')

    # Existing committed inventory receipt is the real git-tracked 0644 case.
    if PUBLIC_RECEIPT.is_file():
        assert stat.S_IMODE(PUBLIC_RECEIPT.stat().st_mode) in parent_ctx.ACCEPTED_PUBLIC_RECEIPT_MODES
        parent_ctx._regular_public(PUBLIC_RECEIPT, "public receipt")

    unsafe = tmp_path / "unsafe.json"
    unsafe.write_bytes(payload)
    os.chmod(unsafe, 0o700)
    with pytest.raises(parent_ctx.SchoolParentSectionContextError, match="permissions must be 0600 or tracked 0644"):
        parent_ctx._regular_public(unsafe, "public receipt")


def test_validate_receipt_rebinds_current_public_inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Standalone validate_receipt must re-open current NEGREC/eval/source-universe files."""
    if not PUBLIC_RECEIPT.is_file():
        pytest.skip("public receipt not materialized yet")
    if not parent_ctx.NEGREC_RECEIPT.is_file():
        pytest.skip("negative-recovery receipt unavailable")
    receipt = json.loads(PUBLIC_RECEIPT.read_text(encoding="utf-8"))
    # Keep receipt bindings current with this script so only input rebind is under test.
    receipt["bindings"] = dict(receipt["bindings"])
    receipt["bindings"]["implementation_sha256"] = parent_ctx.sha256_file(parent_ctx.SCRIPT_PATH)
    receipt["bindings"]["receipt_schema_sha256"] = parent_ctx.sha256_file(parent_ctx.SCHEMA_PATH)
    receipt["receipt_sha256"] = parent_ctx.receipt_sha256(receipt)
    parent_ctx.validate_receipt(receipt)

    tampered_neg = tmp_path / "negrec.json"
    tampered_neg.write_bytes(b'{"tampered":true}\n')
    os.chmod(tampered_neg, 0o600)
    monkeypatch.setattr(parent_ctx, "NEGREC_RECEIPT", tampered_neg)
    with pytest.raises(parent_ctx.SchoolParentSectionContextError, match="negative-recovery receipt"):
        parent_ctx.validate_receipt(receipt)

    monkeypatch.setattr(
        parent_ctx,
        "NEGREC_RECEIPT",
        parent_ctx.DATA / "inventory/phase3_school_context_negative_recovery_receipt_v1.json",
    )
    tampered_eval = tmp_path / "eval.json"
    tampered_eval.write_bytes(b'{"tampered":true}\n')
    os.chmod(tampered_eval, 0o600)
    monkeypatch.setattr(parent_ctx, "EVAL_CONTEXT_RECEIPT", tampered_eval)
    with pytest.raises(parent_ctx.SchoolParentSectionContextError, match="evaluation context receipt"):
        parent_ctx.validate_receipt(receipt)

    monkeypatch.setattr(
        parent_ctx,
        "EVAL_CONTEXT_RECEIPT",
        parent_ctx.DATA / "inventory/phase3_evaluation_context_manifest_receipt_v1.json",
    )
    tampered_universe = tmp_path / "universe.json"
    tampered_universe.write_bytes(b'{"tampered":true}\n')
    os.chmod(tampered_universe, 0o600)
    monkeypatch.setattr(parent_ctx, "SOURCE_UNIVERSE_RECEIPT", tampered_universe)
    with pytest.raises(parent_ctx.SchoolParentSectionContextError, match="source universe receipt"):
        parent_ctx.validate_receipt(receipt)


def test_canonical_temp_root_resolves_var_symlink(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Reproduce macOS /var -> /private/var TMPDIR alias without weakening the guard.
    alias = tmp_path / "var"
    real = tmp_path / "private" / "var"
    real.mkdir(parents=True)
    alias.symlink_to(real)
    monkeypatch.setenv("TMPDIR", str(alias))
    # tempfile may already have cached the tempdir; clear it.
    monkeypatch.setattr(parent_ctx.tempfile, "tempdir", None)
    root = parent_ctx._canonical_temp_root("phase3-school-parent-ctx-")
    try:
        parent_ctx._reject_symlink_components(root, "temp root")
        assert stat.S_IMODE(root.stat().st_mode) == 0o700
        # Lexical path must not walk through the /var-style alias symlink.
        assert not any(Path(*root.parts[: i + 1]).is_symlink() for i in range(1, len(root.parts)))
        assert root.resolve() == root or not root.is_symlink()
    finally:
        import shutil

        shutil.rmtree(root, ignore_errors=True)


def test_source_text_mismatch_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture(tmp_path)
    _patch_pins(monkeypatch, paths)
    source = paths["source_jsonl"]
    assert isinstance(source, Path)
    rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line]
    rows[0]["source_text_sha256"] = "0" * 64
    _write_jsonl(source, rows)
    monkeypatch.setattr(parent_ctx, "PINNED_SOURCE_UNITS_JSONL_SHA256", parent_ctx.sha256_file(source))
    with pytest.raises(parent_ctx.SchoolParentSectionContextError, match="source_text hash drift"):
        parent_ctx.build_context_rows(
            source_jsonl=source,
            partition_path=paths["partition"],  # type: ignore[arg-type]
        )


def test_committed_receipt_validates_when_present() -> None:
    if not PUBLIC_RECEIPT.is_file():
        pytest.skip("public receipt not materialized yet")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    receipt = json.loads(PUBLIC_RECEIPT.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(receipt)
    assert parent_ctx.receipt_sha256(receipt) == receipt["receipt_sha256"]
    assert stat.S_IMODE(PUBLIC_RECEIPT.stat().st_mode) in parent_ctx.ACCEPTED_PUBLIC_RECEIPT_MODES
    validated = parent_ctx.validate_receipt(receipt)
    assert validated["denominators"]["positive_parent_section_heldout"] == 3526
    assert validated["denominators"]["negative_null_parent_heldout_excluded"] == 4479
    assert validated["provider_calls"] is False
    assert validated["labels_present"] is False
    assert validated["semantic_gold"] is False
    assert validated["gates"]["school_complete_context_ready"] is False
    assert validated["gates"]["phase3_complete"] is False
    assert validated["gates"]["phase4_blocked"] is True
    dumped = json.dumps(validated, ensure_ascii=False)
    assert "unit.school_textbooks." not in dumped
    assert not any("\u0400" <= ch <= "\u04ff" for ch in dumped)


def test_production_verify_against_drive_custody() -> None:
    if not CUSTODY_TARBALL.is_file():
        pytest.skip("Drive custody artifacts unavailable")
    assert parent_ctx.sha256_file(CUSTODY_TARBALL) == parent_ctx.PINNED_CUSTODY_TARBALL_SHA256
    if not PUBLIC_RECEIPT.is_file():
        pytest.skip("public receipt not materialized yet")
    private = DRIVE_BACKUP_DIR / parent_ctx.PRIVATE_FILENAME
    if not private.is_file():
        pytest.skip("private Drive artifact not materialized yet")
    committed = json.loads(PUBLIC_RECEIPT.read_text(encoding="utf-8"))
    assert committed["context"]["private_jsonl_sha256"] == parent_ctx.sha256_file(private)
    assert committed["context"]["private_jsonl_rows"] == 3526
    assert stat.S_IMODE(private.stat().st_mode) == 0o600
    assert stat.S_IMODE(DRIVE_BACKUP_DIR.stat().st_mode) == 0o700
    assert stat.S_IMODE(PUBLIC_RECEIPT.stat().st_mode) in parent_ctx.ACCEPTED_PUBLIC_RECEIPT_MODES
    # Re-run production: identical bytes must verify; no text printed.
    reproduced = parent_ctx.production_run(
        custody_tarball=CUSTODY_TARBALL,
        drive_backup_dir=DRIVE_BACKUP_DIR,
        public_receipt_path=PUBLIC_RECEIPT,
        started_at=committed["started_at"],
        completed_at=committed["completed_at"],
    )
    assert reproduced["receipt_sha256"] == committed["receipt_sha256"]
    assert reproduced["context"]["private_jsonl_sha256"] == committed["context"]["private_jsonl_sha256"]
    assert reproduced["gates"]["school_complete_context_ready"] is False
    assert reproduced["gates"]["phase4_blocked"] is True
    # Prior custody evidence preserved; versioned successors may pin regenerated public hashes.
    primary = DRIVE_BACKUP_DIR / parent_ctx.CUSTODY_RECEIPT_FILENAME
    assert primary.is_file()
    assert stat.S_IMODE(primary.stat().st_mode) == 0o600
    matching = None
    matched_body: dict[str, object] | None = None
    for candidate in parent_ctx._iter_custody_receipt_paths(DRIVE_BACKUP_DIR):
        if not candidate.is_file():
            continue
        body = json.loads(candidate.read_text(encoding="utf-8"))
        if body.get("artifacts", {}).get("public_receipt_sha256") == committed["receipt_sha256"]:
            matching = candidate
            matched_body = body
            break
    assert matching is not None
    assert matched_body is not None
    artifacts = matched_body["artifacts"]
    assert isinstance(artifacts, dict)
    assert artifacts["private_context_sha256"] == committed["context"]["private_jsonl_sha256"]
    gates = matched_body["gates"]
    assert isinstance(gates, dict)
    assert gates["phase3_complete"] is False
    assert gates["phase4_blocked"] is True
    matched_text = matching.read_text(encoding="utf-8")
    assert "unit.school_textbooks." not in matched_text
    assert not any("\u0400" <= ch <= "\u04ff" for ch in matched_text)
