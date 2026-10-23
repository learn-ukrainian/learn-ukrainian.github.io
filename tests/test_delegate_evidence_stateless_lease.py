"""#11342: stateless dispatch evidence must neither disappear nor wedge cleanup."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from scripts import delegate
from scripts.fleet import ignored_task_output as output
from scripts.fleet import runtime_held_work as held
from tests.test_delegate_evidence_empty_dir import _cleanup
from tests.test_delegate_held_work import (  # noqa: F401 -- shared hermetic lease fixtures
    _isolate_delegate_import_path,
    _stub_node_modules_integrity_sweep,
    _stub_primary_integrity_sweep,
    _stub_venv_integrity_sweep,
    _stub_worktree_cleanup_integrity_sweep,
)
from tests.test_delegate_held_work import lease as lease


def _lose_record(record, failure):
    path = delegate._state_path(record["task_id"])
    if failure == "missing":
        path.unlink()
    elif failure == "corrupt":
        path.write_text("{not-json")
    else:
        path.rename(path.with_suffix(".unlinked"))


@pytest.mark.parametrize("cleanup", ["direct", "orphan"])
@pytest.mark.parametrize("failure", ["missing", "corrupt", "unlinked"])
@pytest.mark.parametrize("initial", ["absent", "empty", "file", "directory"])
def test_stateless_dispatch_removes_only_empty_evidence(lease, cleanup, failure, initial):
    """Lost records must not wedge empty dispatch leases or authorize evidence loss."""
    root, namespace, record = lease
    _lose_record(record, failure)
    evidence = root / "evidence"
    if initial != "absent":
        evidence.mkdir()
    if initial == "file":
        (evidence / "report.md").write_text("irreplaceable report")
    elif initial == "directory":
        (evidence / ".held").mkdir()
    os.utime(root, (0, 0))

    error, freed = _cleanup(root, namespace, None, cleanup)

    if initial in {"absent", "empty"}:
        assert error is None
        assert not root.exists()
    else:
        assert error == held.EvidencePreservationError.code
        assert freed == 0
        if initial == "file":
            assert (evidence / "report.md").read_text() == "irreplaceable report"
        else:
            assert (evidence / ".held").is_dir()


@pytest.mark.parametrize("cleanup", ["direct", "orphan"])
@pytest.mark.parametrize("initial", ["absent", "empty"])
@pytest.mark.parametrize("arrival", ["file", "directory", "symlink"])
def test_stateless_final_recheck_keeps_late_entries(lease, monkeypatch, cleanup, initial, arrival):
    """An entry added during accounting invalidates an earlier empty inventory."""
    root, namespace, record = lease
    _lose_record(record, "missing")
    evidence = root / "evidence"
    if initial == "empty":
        evidence.mkdir()
    os.utime(root, (0, 0))
    original = delegate._runtime_tmp_lease_bytes
    called = []

    def count_then_add(path):
        size = original(path)
        called.append(path)
        evidence.mkdir(exist_ok=True)
        late = evidence / ".late"
        if arrival == "file":
            late.write_text("late report")
        elif arrival == "directory":
            late.mkdir()
        else:
            late.symlink_to("missing-target")
        # Removing attribution after the first check cannot bypass the second.
        (root / delegate._RUNTIME_TMP_TASK_ID_MARKER).unlink()
        return size

    monkeypatch.setattr(delegate, "_runtime_tmp_lease_bytes", count_then_add)
    error, freed = _cleanup(root, namespace, None, cleanup)

    assert called == [root]
    assert error == held.EvidencePreservationError.code
    assert freed == 0
    late = evidence / ".late"
    if arrival == "file":
        assert late.read_text() == "late report"
    elif arrival == "directory":
        assert late.is_dir()
    else:
        assert late.is_symlink()


@pytest.mark.parametrize("cleanup", ["direct", "orphan"])
def test_non_dispatch_evidence_keeps_existing_age_retention(lease, cleanup):
    """A tool's populated evidence directory cannot become a permanent refusal."""
    root, namespace, record = lease
    _lose_record(record, "missing")
    (root / delegate._RUNTIME_TMP_TASK_ID_MARKER).unlink()
    tool = root.rename(namespace / "coverage-tool")
    evidence = tool / "evidence"
    evidence.mkdir()
    for index in range(12):
        (evidence / f"coverage-{index}.txt").write_text("disposable coverage")
    now = delegate._RUNTIME_TMP_ORPHAN_MAX_AGE_S + 100
    os.utime(tool, (now, now))
    young = delegate._sweep_runtime_tmp_orphans(now=now)
    assert young["errors"] == 0
    assert young["leases_reaped"] == 0
    assert len(list(evidence.iterdir())) == 12
    os.utime(tool, (0, 0))

    error, freed = _cleanup(tool, namespace, None, cleanup)

    assert error is None
    assert freed > 0
    assert not tool.exists()


@pytest.mark.parametrize("cleanup", ["direct", "orphan"])
def test_recovered_original_record_allows_receipted_cleanup(lease, tmp_path, cleanup):
    """Recovering the original record resolves refusal without discarding evidence."""
    root, namespace, record = lease
    _lose_record(record, "missing")
    evidence = root / "evidence"
    evidence.mkdir()
    (evidence / "report.md").write_text("retrievable report")
    os.utime(root, (0, 0))
    error, freed = _cleanup(root, namespace, None, cleanup)
    assert error == held.EvidencePreservationError.code
    assert freed == 0
    retrieved = held.preserve_evidence(root, primary=tmp_path, record=record)
    assert output.verify_retrieval(tmp_path, retrieved) == retrieved["retrieval_proof_sha256"]
    assert (evidence / "report.md").read_text() == "retrievable report"
    delegate._write_state_atomic(delegate._state_path(record["task_id"]), record)

    error, _freed = _cleanup(root, namespace, None, cleanup)

    assert error is None
    assert not root.exists()
    receipt = delegate._read_state(delegate._state_path(record["task_id"]))["preserved_evidence"]
    assert output.verify_retrieval(tmp_path, receipt) == receipt["retrieval_proof_sha256"]
    assert (tmp_path / receipt["location"] / "report.md").read_text() == "retrievable report"


@pytest.mark.parametrize("cleanup", ["direct", "orphan"])
def test_absent_evidence_does_not_require_legacy_id_to_name_a_receipt(lease, cleanup):
    """An absent evidence directory cannot wedge cleanup on receipt-id validation."""
    root, namespace, record = lease
    delegate._state_path(record["task_id"]).unlink()
    record["task_id"] = "legacy/worker"
    delegate._write_state_atomic(delegate._state_path(record["task_id"]), record)
    delegate._write_runtime_tmp_task_id_marker(root, record["task_id"])

    error, _freed = _cleanup(root, namespace, None, cleanup)

    assert error is None
    assert not root.exists()


def test_refusal_runbook_has_a_non_destructive_receipt_recovery_path():
    """A refusal without retrieval and a retry path leaves evidence retained forever."""
    runbook = Path("docs/runbooks/worktree-cleanup.md").read_text()
    section = runbook.split("### Reusing a worktree with evidence (#11342)", 1)[1].split("\n## ", 1)[0]
    assert "Retrieve the evidence" in section
    assert "original task record" in section
    assert "Retry the same cleanup path" in section
    assert "verified retrieval receipt" in section
    assert "never delete" in section
