"""#11342: late evidence must survive both runtime-lease deletion paths."""

from __future__ import annotations

import os

import pytest

from scripts import delegate
from scripts.fleet import ignored_task_output as output
from scripts.fleet import runtime_held_work as held
from tests.test_delegate_held_work import (  # noqa: F401 -- shared hermetic lease fixtures
    _isolate_delegate_import_path,
    _one_shot_copy_hook,
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
def test_late_file_refuses_deletion_and_retry_preserves_it(lease, tmp_path, monkeypatch, cleanup, initial, late_name):
    """A cached empty/absent inventory or a new dotfile cannot authorize deletion."""
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

    assert error == held.EvidencePreservationError.code
    assert freed == 0
    assert (evidence / late_name).read_text() == "late unique evidence"
    monkeypatch.setattr(held, "preserve_evidence", original)
    error, _freed = _cleanup(root, namespace, record, cleanup)
    assert error is None
    assert not root.exists()
    saved = delegate._read_state(delegate._state_path(record["task_id"]))
    receipt = saved["preserved_evidence"]
    assert output.verify_retrieval(tmp_path, receipt) == receipt["retrieval_proof_sha256"]
    assert (tmp_path / receipt["location"] / late_name).read_text() == "late unique evidence"


@pytest.mark.parametrize("cleanup", ["direct", "orphan"])
def test_same_count_replacement_after_receipt_refuses_deletion(lease, monkeypatch, cleanup):
    """Matching file counts cannot hide replacement by a different filename."""
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

    assert error == held.EvidencePreservationError.code
    assert freed == 0
    assert (evidence / "replacement.md").read_text() == "identical bytes"


@pytest.mark.parametrize("cleanup", ["direct", "orphan"])
def test_file_added_during_size_accounting_refuses_deletion(lease, monkeypatch, cleanup):
    """The final recheck must follow size accounting, which also traverses the lease."""
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

    assert error == held.EvidencePreservationError.code
    assert freed == 0
    assert (evidence / "late.md").read_text() == "created during size accounting"


@pytest.mark.parametrize("cleanup", ["direct", "orphan"])
def test_unchanged_empty_directory_gets_verified_receipt_and_reaps(lease, tmp_path, cleanup):
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
    assert output.verify_retrieval(tmp_path, receipt) == receipt["retrieval_proof_sha256"]


@pytest.mark.parametrize("cleanup", ["direct", "orphan"])
def test_empty_subdirectory_added_after_receipt_refuses_deletion(lease, monkeypatch, cleanup):
    """Even a new directory entry invalidates the initial empty inventory."""
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

    assert error == held.EvidencePreservationError.code
    assert freed == 0
    assert (evidence / ".late").is_dir()


@pytest.mark.parametrize("cleanup", ["direct", "orphan"])
def test_new_file_during_nonempty_copy_is_retrieved(lease, tmp_path, monkeypatch, cleanup):
    """A late copy-time file must reach the receipt on both cleanup paths."""
    root, namespace, record = lease
    evidence = root / "evidence"
    (evidence / "nested").mkdir(parents=True)
    (evidence / "first.md").write_text("first evidence")
    hook = _one_shot_copy_hook(monkeypatch, lambda: (evidence / ".late.md").write_text("late evidence"))

    error, _freed = _cleanup(root, namespace, record, cleanup)

    assert hook["fired"]
    assert error is None
    assert not root.exists()
    receipt = delegate._read_state(delegate._state_path(record["task_id"]))["preserved_evidence"]
    assert [entry["path"] for entry in receipt["paths"]] == [".late.md", "first.md"]
    assert receipt["directories"] == ["nested"]
    assert output.verify_retrieval(tmp_path, receipt) == receipt["retrieval_proof_sha256"]
    location = tmp_path / receipt["location"]
    assert (location / ".late.md").read_text() == "late evidence"
    assert (location / "first.md").read_text() == "first evidence"
    assert (location / "nested").is_dir()


@pytest.mark.parametrize("cleanup", ["direct", "orphan"])
def test_stateless_late_evidence_refuses_deletion(lease, monkeypatch, cleanup):
    """An unattributed orphan cannot lose evidence created after its first look."""
    root, namespace, record = lease
    delegate._state_path(record["task_id"]).unlink()
    (root / delegate._RUNTIME_TMP_TASK_ID_MARKER).unlink()
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
