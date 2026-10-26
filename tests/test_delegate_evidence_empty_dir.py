"""C-2481: attributed runtime leases use metadata snapshots for disposal."""

from __future__ import annotations

import os

import pytest

from scripts import delegate
from scripts.fleet import runtime_held_work as held
from tests.test_delegate_held_work import (  # noqa: F401 -- shared hermetic lease fixtures
    _isolate_delegate_import_path,
    _one_shot_inventory_hook,
    _stub_node_modules_integrity_sweep,
    _stub_primary_integrity_sweep,
    _stub_venv_integrity_sweep,
    _stub_worktree_cleanup_integrity_sweep,
)
from tests.test_delegate_held_work import (
    lease as lease,
)


def _cleanup(root, namespace, record, cleanup):
    if cleanup == "direct":
        result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=record)
        return result["tmp_reap_error"], result["tmp_bytes_freed"]
    result = delegate._sweep_runtime_tmp_orphans()
    if result["errors"]:
        assert result["errors"] == 1
        assert result["leases_reaped"] == 0
        return result["error_details"][0][2], result["bytes_freed"]
    assert result["leases_reaped"] == 1
    return None, result["bytes_freed"]


@pytest.mark.parametrize("cleanup", ["direct", "orphan"])
@pytest.mark.parametrize("initial", ["empty", "absent", "nonempty"])
@pytest.mark.parametrize("late_name", ["late.md", ".late.md"])
def test_late_file_after_snapshot_allows_record_only_disposal(
    lease, tmp_path, monkeypatch, cleanup, initial, late_name
):
    """A metadata snapshot does not promise retrieval of later residue bytes."""
    root, namespace, record = lease
    evidence = root / "evidence"
    if initial != "absent":
        evidence.mkdir()
    if initial == "nonempty":
        (evidence / "first.md").write_text("first evidence")
    original = held.preserve_evidence

    def preserve_then_add(*args, **kwargs):
        receipt = original(*args, **kwargs)
        evidence.mkdir(exist_ok=True)
        (evidence / late_name).write_text("late unique evidence")
        return receipt

    monkeypatch.setattr(held, "preserve_evidence", preserve_then_add)
    error, freed = _cleanup(root, namespace, record, cleanup)

    assert error is None
    assert freed > 0
    assert not root.exists()
    saved = delegate._read_state(delegate._state_path(record["task_id"]))
    receipt = saved["preserved_evidence"]
    assert receipt["mode"] == "record-only" and receipt["copied_bytes"] == 0
    assert [entry["path"] for entry in receipt["paths"]] == (["first.md"] if initial == "nonempty" else [])
    assert "location" not in receipt
    assert not (tmp_path / "batch_state/preserved").exists()


@pytest.mark.parametrize("cleanup", ["direct", "orphan"])
def test_same_count_replacement_after_snapshot_allows_disposal(lease, monkeypatch, cleanup):
    """A record-only receipt retains the earlier filename without copying either version."""
    root, namespace, record = lease
    evidence = root / "evidence"
    evidence.mkdir()
    (evidence / "first.md").write_text("identical bytes")
    original = held.preserve_evidence

    def preserve_then_replace(*args, **kwargs):
        receipt = original(*args, **kwargs)
        (evidence / "first.md").rename(evidence / "replacement.md")
        return receipt

    monkeypatch.setattr(held, "preserve_evidence", preserve_then_replace)
    error, freed = _cleanup(root, namespace, record, cleanup)

    assert error is None
    assert freed > 0
    assert not root.exists()
    receipt = delegate._read_state(delegate._state_path(record["task_id"]))["preserved_evidence"]
    assert [entry["path"] for entry in receipt["paths"]] == ["first.md"]
    assert receipt["mode"] == "record-only" and receipt["copied_bytes"] == 0


@pytest.mark.parametrize("cleanup", ["direct", "orphan"])
def test_file_added_during_size_accounting_allows_record_only_disposal(lease, monkeypatch, cleanup):
    """Accounting-time residue does not regrow the preserved byte archive."""
    root, namespace, record = lease
    evidence = root / "evidence"
    evidence.mkdir()
    original = delegate._runtime_tmp_lease_bytes

    def count_then_add(path):
        size = original(path)
        (evidence / "late.md").write_text("created during size accounting")
        return size

    monkeypatch.setattr(delegate, "_runtime_tmp_lease_bytes", count_then_add)
    error, freed = _cleanup(root, namespace, record, cleanup)

    assert error is None
    assert freed > 0
    assert not root.exists()
    receipt = delegate._read_state(delegate._state_path(record["task_id"]))["preserved_evidence"]
    assert receipt["paths"] == []
    assert receipt["mode"] == "record-only" and receipt["copied_bytes"] == 0


@pytest.mark.parametrize("cleanup", ["direct", "orphan"])
def test_unchanged_empty_directory_gets_record_only_receipt_and_reaps(lease, tmp_path, cleanup):
    """Empty evidence must not permanently retain an otherwise removable lease."""
    root, namespace, record = lease
    (root / "evidence").mkdir()

    error, _freed = _cleanup(root, namespace, record, cleanup)

    assert error is None
    assert not root.exists()
    receipt = delegate._read_state(delegate._state_path(record["task_id"]))["preserved_evidence"]
    assert receipt["paths"] == []
    assert receipt["count"] == 0
    assert receipt["bytes"] == 0
    assert receipt["mode"] == "record-only" and receipt["copied_bytes"] == 0
    assert not (tmp_path / "batch_state/preserved").exists()


@pytest.mark.parametrize("cleanup", ["direct", "orphan"])
def test_empty_subdirectory_after_snapshot_allows_disposal(lease, monkeypatch, cleanup):
    """An attributed empty directory needs no retrievable byte copy."""
    root, namespace, record = lease
    evidence = root / "evidence"
    evidence.mkdir()
    original = held.preserve_evidence

    def preserve_then_add_directory(*args, **kwargs):
        receipt = original(*args, **kwargs)
        (evidence / ".late").mkdir()
        return receipt

    monkeypatch.setattr(held, "preserve_evidence", preserve_then_add_directory)
    error, freed = _cleanup(root, namespace, record, cleanup)

    assert error is None
    assert freed > 0
    assert not root.exists()
    receipt = delegate._read_state(delegate._state_path(record["task_id"]))["preserved_evidence"]
    assert receipt["paths"] == [] and receipt["copied_bytes"] == 0


@pytest.mark.parametrize("cleanup", ["direct", "orphan"])
def test_new_file_after_enumeration_does_not_regrow_an_archive(lease, tmp_path, monkeypatch, cleanup):
    """Both cleanup paths retain the inventory snapshot and copy no residue."""
    root, namespace, record = lease
    evidence = root / "evidence"
    (evidence / "nested").mkdir(parents=True)
    (evidence / "first.md").write_text("first evidence")
    hook = _one_shot_inventory_hook(monkeypatch, lambda: (evidence / ".late.md").write_text("late evidence"))

    error, _freed = _cleanup(root, namespace, record, cleanup)

    assert hook["fired"]
    assert error is None
    assert not root.exists()
    receipt = delegate._read_state(delegate._state_path(record["task_id"]))["preserved_evidence"]
    assert [entry["path"] for entry in receipt["paths"]] == ["first.md"]
    assert receipt["mode"] == "record-only" and receipt["copied_bytes"] == 0
    assert not (tmp_path / "batch_state/preserved").exists()
    assert receipt["paths"][0]["size"] == len(b"first evidence")
    assert "location" not in receipt


@pytest.mark.parametrize("cleanup", ["direct", "orphan"])
def test_stateless_late_evidence_refuses_deletion(lease, monkeypatch, cleanup):
    """An unattributed orphan cannot lose evidence created after its first look."""
    root, namespace, record = lease
    delegate._state_path(record["task_id"]).unlink()
    assert (root / delegate._RUNTIME_TMP_TASK_ID_MARKER).is_file()
    os.utime(root, (0, 0))
    original = delegate._preserve_runtime_tmp_held_work

    def preserve_then_add(*args, **kwargs):
        updates = original(*args, **kwargs)
        (root / "evidence").mkdir()
        (root / "evidence" / "late.md").write_text("unattributed late evidence")
        return updates

    monkeypatch.setattr(delegate, "_preserve_runtime_tmp_held_work", preserve_then_add)
    error, freed = _cleanup(root, namespace, None, cleanup)

    assert error == held.EvidencePreservationError.code
    assert freed == 0
    assert (root / "evidence" / "late.md").read_text() == "unattributed late evidence"
