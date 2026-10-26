"""Runtime cleanup records residue metadata without archiving bytes (C-2481)."""

from __future__ import annotations

import errno
import hashlib
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from scripts import delegate
from scripts.fleet import ignored_task_output as output
from scripts.fleet import runtime_held_work as held
from tests.test_delegate import (  # noqa: F401 -- shared hermetic worker fixtures
    _isolate_delegate_import_path,
    _stub_node_modules_integrity_sweep,
    _stub_primary_integrity_sweep,
    _stub_venv_integrity_sweep,
    _stub_worktree_cleanup_integrity_sweep,
)


@pytest.fixture
def lease(tmp_path, monkeypatch):
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(tmp_path))
    monkeypatch.setattr(delegate, "scratch_scan_roots", lambda: [tmp_path])
    monkeypatch.setattr(delegate.tempfile, "gettempdir", lambda: str(tmp_path))
    monkeypatch.setattr(delegate, "_main_checkout_root", lambda _root: tmp_path)
    root, namespace = delegate._create_runtime_tmp_lease("held-worker")
    record = {
        "task_id": "held-worker",
        "run_nonce": "attempt-1",
        "status": "done",
        "pid": None,
        "runtime_tmp_root": str(root),
        "runtime_tmp_namespace_root": str(namespace),
    }
    delegate._write_state_atomic(delegate._state_path(record["task_id"]), record)
    return root, namespace, record


def _recorded_entries(primary: Path, record: dict) -> tuple[dict, dict]:
    receipt = record["preserved_held_work"]
    assert receipt["mode"] == "record-only"
    assert receipt["copied_bytes"] == 0
    assert "location" not in receipt
    assert not (primary / "batch_state/preserved").exists()
    return {entry["path"]: entry for entry in receipt["paths"]}, receipt


@pytest.mark.parametrize("failed", [False, True])
def test_worker_finalization_preserves_response_before_runtime_tmp_reap(lease, tmp_path, monkeypatch, failed):
    root, namespace, record = lease
    (root / "readers.patch").write_bytes(b"held patch\n")
    (root / "handoff.md").write_text("handoff\n")
    (root / "disposable").write_bytes(b"scratch")
    response = f"Held [patch]({root}/readers.patch:12) and `{root}/handoff.md`."
    # Isolate runtime preservation from unrelated checkout and live-scope gates.
    monkeypatch.setattr(delegate, "_read_only_checkout_snapshot", lambda _cwd: ({}, None))
    monkeypatch.setattr(delegate, "_read_only_task_record_snapshot", lambda *_args: ({}, None))
    monkeypatch.setattr(delegate, "_emit_terminal_dispatch_event", lambda **_kwargs: None)
    record.update({"cli_version": "fixture", "response_chars": None})
    delegate._write_state_atomic(delegate._state_path(record["task_id"]), record)
    result = SimpleNamespace(
        ok=not failed, response=response, returncode=1 if failed else 0, stderr_excerpt=None, rate_limited=False
    )
    with patch("agent_runtime.runner.invoke", return_value=result):
        rc = delegate._run_worker(
            task_id=record["task_id"],
            agent="codex",
            prompt="report",
            mode="read-only",
            cwd_str=str(tmp_path),
            model="gpt-6.1-sol",
            hard_timeout=60,
            runtime_tmp_root=str(root),
            runtime_tmp_namespace_root=str(namespace),
        )
    assert rc == (1 if failed else 0)
    saved = delegate._read_state(delegate._state_path(record["task_id"]))
    assert saved["tmp_reap_error"] is None
    assert not root.exists()
    assert Path(saved["result_file"]).read_text() == response
    entries, manifest = _recorded_entries(tmp_path, saved)
    assert manifest["count"] == 2
    assert entries["readers.patch"]["sha256"] == hashlib.sha256(b"held patch\n").hexdigest()
    assert entries["handoff.md"]["sha256"] == hashlib.sha256(b"handoff\n").hexdigest()
    assert "disposable" not in entries
    assert delegate._sweep_runtime_tmp_orphans()["leases_reaped"] == 0
    _recorded_entries(tmp_path, saved)


@pytest.mark.parametrize("legacy", [False, True])
def test_orphan_sweep_preserves_saved_result_and_metadata(lease, tmp_path, legacy):
    root, _, record = lease
    if legacy:
        (root / delegate._RUNTIME_TMP_TASK_ID_MARKER).unlink()
    (root / "readers.patch").write_text("held\n")
    result_path = delegate._result_path(record["task_id"])
    response = f"Held `{root}/readers.patch`."
    result_path.write_text(response)
    record.update(result_file=str(result_path), response_chars=len(response))
    delegate._write_state_atomic(delegate._state_path(record["task_id"]), record)
    result = delegate._sweep_runtime_tmp_orphans()
    assert result["leases_reaped"] == 1
    assert result["errors"] == 0
    assert not root.exists()
    saved = delegate._read_state(delegate._state_path(record["task_id"]))
    entries, _ = _recorded_entries(tmp_path, saved)
    assert entries["readers.patch"]["sha256"] == hashlib.sha256(b"held\n").hexdigest()


def test_unreferenced_files_reaped_without_preservation(lease, tmp_path):
    root, namespace, _ = lease
    (root / "disposable").write_bytes(b"temporary")
    result = delegate._reap_runtime_tmp_lease(root, namespace)
    assert result["tmp_reap_error"] is None
    assert result["tmp_bytes_freed"] > 0
    assert not root.exists()
    assert not (tmp_path / "batch_state/preserved").exists()


@pytest.mark.parametrize(
    "citation",
    [
        "`{root}/sub/held patch.txt:4:2`",
        "[held](<{root}/sub/held patch.txt>)",
        "<file://{root}/sub/held%20patch.txt>",
        "'{root}/sub/held patch.txt'",
        '"{root}/sub/held patch.txt"',
        "`$TMPDIR/sub/held patch.txt`",
        "`$LU_RUNTIME_TMP_ROOT/sub/held patch.txt`",
        "`sub/held patch.txt`",
        "[held](<sub/held patch.txt>)",
    ],
)
def test_citation_formats_and_empty_file(lease, tmp_path, citation):
    root, namespace, record = lease
    (root / "sub").mkdir()
    (root / "sub/held").mkdir()
    (root / "sub/held patch.txt").touch()
    result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=record, response=citation.format(root=root))
    assert result["tmp_reap_error"] is None
    entries, _ = _recorded_entries(tmp_path, record)
    assert entries["sub/held patch.txt"]["sha256"] == hashlib.sha256(b"").hexdigest()


@pytest.mark.parametrize(
    "response",
    [
        "The worker's patch is `{root}/readers.patch`; it isn't committed.",
        "It isn't committed: {root}/readers.patch. I couldn't finish.",
        "The worker's patch is '{root}/readers.patch'; it couldn't be pushed.",
        "\"The worker's patch is {root}/readers.patch and isn't committed.\"",
        "'The worker's patch is $TMPDIR/readers.patch and couldn't be pushed.'",
        "`The worker's patch is \"{root}/readers.patch\" and isn't committed.`",
        '"Held ${{TMPDIR}}/readers.patch and couldn\'t finish."',
        '"{root}/readers.patch couldn\'t be pushed."',
    ],
)
def test_apostrophe_prose_records_cited_patch(lease, tmp_path, response):
    root, namespace, record = lease
    (root / "readers.patch").write_text("held patch")
    result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=record, response=response.format(root=root))
    assert result["tmp_reap_error"] is None
    assert not root.exists()
    entries, manifest = _recorded_entries(tmp_path, record)
    assert manifest["count"] == 1
    assert entries["readers.patch"]["sha256"] == hashlib.sha256(b"held patch").hexdigest()


@pytest.mark.parametrize("citation", ["'readers.patch\"", '"readers.patch`', "`readers.patch'"])
def test_quote_delimiters_must_match(lease, citation):
    root, _, _ = lease
    assert held.cited_paths(root, {}, citation) == []


@pytest.mark.parametrize("quote", ["'", '"', "`"])
@pytest.mark.parametrize(
    "passage",
    [
        "This long sentence describes the worker report and its remaining work. " * 6,
        "У цьому звіті наведено довге цитоване речення. " * 8,
    ],
    ids=["english", "ukrainian"],
)
def test_long_quoted_prose_records_real_citation_and_allows_cleanup(lease, tmp_path, quote, passage):
    root, namespace, record = lease
    assert len(passage.encode("utf-8")) > 300
    (root / "readers.patch").write_text("held patch")
    response = f"Report: {quote}{passage}{quote}. Held `readers.patch`."
    assert held.cited_paths(root, record, response) == ["readers.patch"]
    result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=record, response=response)
    assert result["tmp_reap_error"] is None
    assert not root.exists()
    entries, manifest = _recorded_entries(tmp_path, record)
    assert manifest["count"] == 1
    assert entries["readers.patch"]["sha256"] == hashlib.sha256(b"held patch").hexdigest()


@pytest.mark.parametrize(
    "segment",
    ["a" * 255, "a" * 256, "я" * 127 + "a", "я" * 128],
    ids=["ascii-255", "ascii-256", "utf8-255", "utf8-256"],
)
@pytest.mark.parametrize("parent", [False, True])
def test_citation_component_limit_uses_utf8_bytes(lease, segment, parent):
    root, _, record = lease
    name = f"{segment}/patch" if parent else segment
    expected = [] if len(segment.encode("utf-8")) > 255 else [name]
    assert held.cited_paths(root, record, f"`{name}`") == expected


@pytest.mark.parametrize("stage", ["parent", "leaf"])
@pytest.mark.parametrize("error_number", [errno.ENAMETOOLONG, errno.EACCES])
@pytest.mark.parametrize("declared", [False, True])
def test_candidate_open_errors_are_receipted_without_blocking_disposal(
    lease, tmp_path, monkeypatch, stage, error_number, declared
):
    root, namespace, record = lease
    (root / "readers.patch").write_text("held patch")
    candidate = "prose/patch" if stage == "parent" else "prose"
    if declared:
        record["held_work"] = [candidate]
    original = output.os.open

    def fail_candidate(name, *args, **kwargs):
        if name == "prose":
            raise OSError(error_number, "fixture open error")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(output.os, "open", fail_candidate)
    result = delegate._reap_runtime_tmp_lease(
        root, namespace, task_record=record, response=f"`{candidate}` `readers.patch`"
    )
    assert result["tmp_reap_error"] is None
    assert not root.exists()
    entries, receipt = _recorded_entries(tmp_path, record)
    assert receipt["inventory_error"] == "inventory_incomplete"
    assert receipt["count"] == 1
    assert entries["readers.patch"]["sha256"] == hashlib.sha256(b"held patch").hexdigest()


@pytest.mark.parametrize("with_patch", [False, True])
@pytest.mark.parametrize("structured", [False, True])
def test_harmless_report_paths_allow_cleanup(lease, tmp_path, with_patch, structured):
    root, namespace, record = lease
    outside = tmp_path / "outside.patch"
    outside.write_text("must not copy")
    (root / "sub").mkdir()
    (root / "disposable").write_text("scratch")
    report = (
        "Paths: `.`, `..`, [runbook](../docs/runbook.md), `{root}`, `$TMPDIR/`, "
        "`${TMPDIR}/`, `$LU_RUNTIME_TMP_ROOT/`, `${LU_RUNTIME_TMP_ROOT}/`, "
        f"`{root}`, `{root}/`, `{root}/../../outside.patch`, "
        "`sub/../readers.patch`, `../outside.patch`, `bad\x00name`, "
        "`sub`, `disposable/child`, `disposable/../child`."
    )
    if with_patch:
        (root / "readers.patch").write_text("held patch")
        report += f" Held [patch](<{root}/readers.patch>)."
    if structured:
        record["report"] = {"text": report}
        report = ""
    result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=record, response=report)
    assert result["tmp_reap_error"] is None
    assert not root.exists()
    assert outside.read_text() == "must not copy"
    if with_patch:
        entries, manifest = _recorded_entries(tmp_path, record)
        assert manifest["count"] == 1
        assert entries["readers.patch"]["sha256"] == hashlib.sha256(b"held patch").hexdigest()
    else:
        assert not (tmp_path / "batch_state/preserved").exists()


def test_explicit_directory_declaration_records_incomplete_inventory(lease):
    root, namespace, record = lease
    (root / "sub").mkdir()
    record["held_work"] = ["sub"]
    result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=record, response="")
    assert result["tmp_reap_error"] is None
    assert not root.exists()
    assert record["preserved_held_work"]["inventory_error"] == "inventory_incomplete"
    assert record["preserved_held_work"]["copied_bytes"] == 0


@pytest.mark.parametrize("declaration", ["readers.patch", "absolute"])
def test_explicit_held_work_declarations(lease, tmp_path, declaration):
    root, namespace, record = lease
    (root / "readers.patch").write_text("held")
    record["held_work"] = [str(root / "readers.patch") if declaration == "absolute" else declaration]
    result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=record, response="")
    assert result["tmp_reap_error"] is None
    entries, _ = _recorded_entries(tmp_path, record)
    assert entries["readers.patch"]["sha256"] == hashlib.sha256(b"held").hexdigest()


@pytest.mark.parametrize("attack", ["leaf", "parent", "traversal", "prefix"])
def test_held_work_records_boundary_attacks_without_reading_outside(lease, tmp_path, attack):
    root, namespace, record = lease
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "private.patch").write_text("must not copy")
    if attack == "leaf":
        (root / "attack").symlink_to(outside / "private.patch")
        response = f"`{root}/attack`"
    elif attack == "parent":
        (root / "attack").symlink_to(outside, target_is_directory=True)
        response = f"`{root}/attack/private.patch`"
    elif attack == "traversal":
        record["held_work"] = [str(root / "../../outside/private.patch")]
        response = ""
    else:
        record["held_work"] = [str(root) + "-other/private.patch"]
        response = ""
    result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=record, response=response)
    assert result["tmp_reap_error"] is None
    assert not root.exists()
    assert record["preserved_held_work"]["inventory_error"] == (
        "inventory_incomplete" if attack in {"leaf", "parent"} else "inventory_failed"
    )
    assert record["preserved_held_work"]["count"] == 0
    assert (outside / "private.patch").read_text() == "must not copy"
    assert not (tmp_path / "batch_state/preserved").exists()


@pytest.mark.parametrize("failure", ["copy", "manifest", "metadata", "cap", "unreadable_result"])
def test_only_task_state_failures_refuse_cleanup_and_orphan_retry(lease, tmp_path, monkeypatch, failure):
    root, namespace, record = lease
    (root / "readers.patch").write_text("held")
    response = f"`{root}/readers.patch`"
    result_file = delegate._result_path(record["task_id"])
    result_file.write_text(response)
    record.update(result_file=str(result_file), response_chars=len(response))
    delegate._write_state_atomic(delegate._state_path(record["task_id"]), record)

    def fail(*_args, **_kwargs):
        raise OSError("fixture failure")

    if failure == "copy":
        monkeypatch.setattr(output.artifacts, "_copy_verified", fail)
    elif failure == "manifest":
        real_open = Path.open

        def open_manifest(path, *args, **kwargs):
            return fail() if path.name.endswith(".manifest.json") else real_open(path, *args, **kwargs)

        monkeypatch.setattr(Path, "open", open_manifest)
    elif failure == "metadata":
        monkeypatch.setattr(delegate, "_write_record_unlocked", fail)
    elif failure == "cap":
        monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", 3)
    else:
        result_file.unlink()
    result = delegate._reap_runtime_tmp_lease(root, namespace)
    if failure in {"metadata", "unreadable_result"}:
        assert result["tmp_reap_error"] == held.HeldWorkPreservationError.code
        assert result["tmp_bytes_freed"] == 0
        assert (root / "readers.patch").read_text() == "held"
        swept = delegate._sweep_runtime_tmp_orphans()
        assert swept["leases_reaped"] == 0
        assert swept["errors"] == 1
        assert swept["error_details"][0][2] == held.HeldWorkPreservationError.code
    else:
        assert result["tmp_reap_error"] is None
        assert not root.exists()
        saved = delegate._read_state(delegate._state_path(record["task_id"]))
        entries, receipt = _recorded_entries(tmp_path, saved)
        assert receipt["count"] == 1 and receipt["bytes"] == 4
        if failure == "cap":
            assert receipt["paths_truncated"] and entries == {}
        else:
            assert entries["readers.patch"]["sha256"] == hashlib.sha256(b"held").hexdigest()
        assert delegate._sweep_runtime_tmp_orphans()["errors"] == 0


def test_worker_preamble_guides_held_work_to_reports(tmp_path, monkeypatch):
    monkeypatch.setattr(delegate, "_resolve_primary_root_for_worktree", lambda _root: tmp_path)
    prompt = delegate._augment_prompt_with_worktree("task", tmp_path, mode="workspace-write")
    assert "[held work]" in prompt
    assert "`$LU_TASK_EVIDENCE_DIR`" in prompt
    assert "`batch_state/reports/`" not in prompt
    assert "cite each file in your final response" in prompt
    assert "Task cleanup preserves that directory with a retrieval receipt before removing the runtime lease." in prompt


def test_structured_report_and_deliverable_citations(lease, tmp_path):
    root, namespace, record = lease
    (root / "report.txt").write_text("held report")
    (root / "patch.txt").write_text("held patch")
    record["report"] = {"files": [f"`{root}/report.txt`", 42]}
    record["deliverable"] = [f"{root}/patch.txt"]
    result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=record, response="")
    assert result["tmp_reap_error"] is None
    _, manifest = _recorded_entries(tmp_path, record)
    assert [entry["path"] for entry in manifest["paths"]] == ["patch.txt", "report.txt"]


@pytest.mark.parametrize(
    "declaration",
    [
        ["missing.patch"],
        ["sub/missing.patch"],
        ["./missing.patch"],
        ["$TMPDIR/missing.patch"],
        "patch",
        [None],
        ["../outside"],
        ["."],
        [".."],
        [""],
        ["$TMPDIR/"],
        ["${TMPDIR}/"],
        ["bad\x00name"],
        ["a" * 256],
        ["я" * 128],
        ["a" * 256 + "/patch"],
    ],
)
def test_invalid_or_missing_declaration_records_inventory_error(lease, declaration):
    root, namespace, record = lease
    record["held_work"] = declaration
    result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=record, response="")
    assert result["tmp_reap_error"] is None
    assert not root.exists()
    receipt = record["preserved_held_work"]
    assert receipt["mode"] == "record-only" and receipt["copied_bytes"] == 0
    assert receipt["count"] == 0
    assert receipt["inventory_error"] in {"inventory_incomplete", "inventory_failed"}


def test_missing_prose_citations_and_outside_paths_are_not_copied(lease, tmp_path):
    root, namespace, record = lease
    (tmp_path / "outside.patch").write_text("outside")
    result = delegate._reap_runtime_tmp_lease(
        root,
        namespace,
        task_record=record,
        response=f"`{root}/missing.patch` `{root}/sub/missing.patch` `{tmp_path}/outside.patch`",
    )
    assert result["tmp_reap_error"] is None
    assert not root.exists()
    assert not (tmp_path / "batch_state/preserved").exists()
    assert (tmp_path / "outside.patch").read_text() == "outside"


def test_record_only_cleanup_does_not_write_through_destination_symlink(lease, tmp_path):
    root, namespace, record = lease
    (root / "patch").write_text("held")
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "batch_state").symlink_to(outside, target_is_directory=True)
    result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=record, response=f"`{root}/patch`")
    assert result["tmp_reap_error"] is None
    assert not root.exists()
    assert record["preserved_held_work"]["mode"] == "record-only"
    assert list(outside.iterdir()) == []


def test_changed_task_attempt_refuses_receipt_publication_and_cleanup(lease):
    root, namespace, record = lease
    (root / "patch").write_text("held")
    path = delegate._state_path(record["task_id"])
    wrong_root = {**record, "runtime_tmp_root": str(root / "different-lease")}
    result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=wrong_root, response=f"`{root}/patch`")
    assert result["tmp_reap_error"] == held.HeldWorkPreservationError.code
    assert (root / "patch").read_text() == "held"
    assert "preserved_held_work" not in delegate._read_state(path)
    replacement = {**record, "run_nonce": "replacement"}
    delegate._write_state_atomic(path, replacement)
    result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=record, response=f"`{root}/patch`")
    assert result["tmp_reap_error"] == held.HeldWorkPreservationError.code
    assert root.exists()
    assert "preserved_held_work" not in delegate._read_state(path)


def test_source_mutation_after_inventory_allows_record_only_disposal(lease, monkeypatch):
    root, namespace, record = lease
    (root / "patch").write_text("held")
    original = output.record_only_receipt

    def mutate_after_inventory(*args, **kwargs):
        receipt = original(*args, **kwargs)
        (root / "patch").write_text("new content")
        return receipt

    monkeypatch.setattr(output, "record_only_receipt", mutate_after_inventory)
    result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=record, response=f"`{root}/patch`")
    assert result["tmp_reap_error"] is None
    assert not root.exists()
    assert record["preserved_held_work"]["mode"] == "record-only"
    assert record["preserved_held_work"]["copied_bytes"] == 0


def test_supported_evidence_directory_is_recorded_before_lease_reap(lease, tmp_path):
    root, namespace, record = lease
    (root / "evidence" / "screenshots").mkdir(parents=True)
    (root / "evidence" / "publish-review.md").write_text("report\n")
    (root / "evidence" / "screenshots" / "card.png").write_bytes(b"png")
    result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=record)
    assert result["tmp_reap_error"] is None
    assert not root.exists()
    saved = delegate._read_state(delegate._state_path(record["task_id"]))
    receipt = saved["preserved_evidence"]
    assert receipt["mode"] == "record-only" and receipt["copied_bytes"] == 0
    assert receipt["task_id"] == record["task_id"]
    assert receipt["run_nonce"] == record["run_nonce"]
    assert receipt["count"] == 2
    assert "location" not in receipt
    assert not (tmp_path / "batch_state/preserved").exists()
    entries = {entry["path"]: entry for entry in receipt["paths"]}
    assert entries["publish-review.md"]["sha256"] == hashlib.sha256(b"report\n").hexdigest()
    assert entries["screenshots/card.png"]["sha256"] == hashlib.sha256(b"png").hexdigest()


def test_evidence_over_cap_records_totals_and_allows_disposal(lease, monkeypatch):
    root, namespace, record = lease
    (root / "evidence").mkdir()
    (root / "evidence" / "archive.tar.gz").write_bytes(b"x" * 64)
    monkeypatch.setattr(held.output, "MAX_PRESERVED_BYTES", 8)
    result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=record)
    assert result["tmp_reap_error"] is None
    assert not root.exists()
    receipt = delegate._read_state(delegate._state_path(record["task_id"]))["preserved_evidence"]
    assert receipt["count"] == 1 and receipt["bytes"] == 64
    assert receipt["paths"] == [] and receipt["paths_truncated"]
    assert receipt["mode"] == "record-only" and receipt["copied_bytes"] == 0


def test_linked_evidence_records_error_without_following_the_link(lease, tmp_path):
    root, namespace, record = lease
    (root / "evidence").mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret")
    (root / "evidence" / "link.txt").symlink_to(outside)
    result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=record)
    assert result["tmp_reap_error"] is None
    assert not root.exists()
    assert record["preserved_evidence"]["inventory_error"] == "inventory_failed"
    assert outside.read_text() == "secret"


def test_orphan_sweep_keeps_an_unattributed_evidence_lease(lease):
    root, _namespace, record = lease
    delegate._state_path(record["task_id"]).unlink()
    # Dispatch attribution survives loss of the task record.
    assert (root / delegate._RUNTIME_TMP_TASK_ID_MARKER).is_file()
    (root / "evidence").mkdir()
    (root / "evidence" / "report.md").write_text("report\n")
    old = 0.0
    os.utime(root, (old, old))
    result = delegate._sweep_runtime_tmp_orphans(now=8 * 24 * 60 * 60.0)
    assert result["leases_reaped"] == 0
    assert result["errors"] == 1
    assert (root / "evidence" / "report.md").read_text() == "report\n"


def test_worker_env_exposes_the_supported_evidence_directory(tmp_path):
    lease_root = tmp_path / "lease"
    env = delegate._build_worker_env(
        task_id="evidence-worker",
        dispatch_agent="codex",
        runtime_tmp_root=lease_root,
        runtime_tmp_namespace_root=tmp_path / "namespace",
    )
    assert env["LU_TASK_EVIDENCE_DIR"] == str(lease_root / "evidence")


def test_worker_prompt_names_the_supported_evidence_directory(tmp_path):
    blocks: list[str] = []
    evidence = tmp_path / "lease" / "evidence"
    prompt = delegate._compose_dispatch_prompt(
        "brief",
        worktree_path=tmp_path / "wt",
        mode="read-only",
        sparse_telemetry=None,
        delegate_commits=False,
        research_block="",
        advisory_block="",
        advisory_block_kind=None,
        rules_seat=None,
        blocks=blocks,
        evidence_dir=evidence,
    )
    assert "LU_TASK_EVIDENCE_DIR" in prompt
    assert "batch_state/preserved/<task>/" in prompt
    # The concrete per-task lease path is deliberately absent: the prompt (and
    # its hash, and the evaluation's paired frame) must not depend on it.
    assert str(evidence) not in prompt
    assert "evidence" in blocks


def test_evidence_prompt_block_is_identical_for_different_lease_paths(tmp_path):
    def compose(evidence_dir: Path) -> str:
        return delegate._compose_dispatch_prompt(
            "brief",
            worktree_path=None,
            mode="read-only",
            sparse_telemetry=None,
            delegate_commits=False,
            research_block="",
            advisory_block="",
            advisory_block_kind=None,
            rules_seat=None,
            evidence_dir=evidence_dir,
        )

    first = compose(tmp_path / "lease-one" / "evidence")
    second = compose(tmp_path / "a-different-task-lease" / "evidence")
    assert first == second
    assert delegate._evidence_prompt_block() in first


def _one_shot_inventory_hook(monkeypatch, action):
    """Run ``action`` once immediately before the record-only inventory is read."""
    original = output.record_only_receipt
    state = {"fired": False}

    def inventory_then_action(*args, **kwargs):
        if not state["fired"]:
            state["fired"] = True
            action()
        return original(*args, **kwargs)

    monkeypatch.setattr(output, "record_only_receipt", inventory_then_action)
    return state


def test_evidence_added_after_enumeration_is_disposed_without_copying(lease, tmp_path, monkeypatch):
    """Late residue is disposed without promising a retrievable archive."""
    root, namespace, record = lease
    (root / "evidence").mkdir()
    (root / "evidence" / "report.md").write_text("first report")
    _one_shot_inventory_hook(
        monkeypatch, lambda: (root / "evidence" / "late-report.md").write_text("late unique evidence")
    )

    result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=record)

    assert result["tmp_reap_error"] is None
    assert not root.exists()
    saved = delegate._read_state(delegate._state_path(record["task_id"]))
    receipt = saved["preserved_evidence"]
    assert [entry["path"] for entry in receipt["paths"]] == ["report.md"]
    assert "location" not in receipt
    assert not (tmp_path / "batch_state/preserved").exists()
    entries = {entry["path"]: entry for entry in receipt["paths"]}
    assert entries["report.md"]["sha256"] == hashlib.sha256(b"first report").hexdigest()
    assert "late-report.md" not in entries


def test_evidence_changed_before_hashing_records_current_digest(lease, tmp_path, monkeypatch):
    """The inventory hashes the file after enumeration without copying it."""
    root, namespace, record = lease
    (root / "evidence").mkdir()
    evidence = root / "evidence" / "report.md"
    evidence.write_text("first copy")
    _one_shot_inventory_hook(monkeypatch, lambda: evidence.write_text("rewritten during copy"))

    result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=record)

    assert result["tmp_reap_error"] is None
    assert not root.exists()
    saved = delegate._read_state(delegate._state_path(record["task_id"]))
    receipt = saved["preserved_evidence"]
    assert receipt["mode"] == "record-only" and receipt["copied_bytes"] == 0
    assert receipt["paths"][0]["sha256"] == hashlib.sha256(b"rewritten during copy").hexdigest()
    assert not (tmp_path / "batch_state/preserved").exists()


def test_evidence_written_after_snapshot_allows_record_only_disposal(lease, monkeypatch):
    """Record-only receipts authorize disposal of late task residue."""
    root, namespace, record = lease
    (root / "evidence").mkdir()
    (root / "evidence" / "report.md").write_text("report\n")
    original = held.preserve_evidence

    def preserve_then_write_again(*args, **kwargs):
        receipt = original(*args, **kwargs)
        (root / "evidence" / "after-receipt.md").write_text("written after the final enumeration")
        return receipt

    monkeypatch.setattr(held, "preserve_evidence", preserve_then_write_again)
    result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=record)

    assert result["tmp_reap_error"] is None
    assert not root.exists()
    assert [entry["path"] for entry in record["preserved_evidence"]["paths"]] == ["report.md"]
    assert record["preserved_evidence"]["copied_bytes"] == 0


def test_repeated_evidence_changes_do_not_require_archive_retries(lease, tmp_path, monkeypatch):
    root, namespace, record = lease
    (root / "evidence").mkdir()
    evidence = root / "evidence" / "report.md"
    evidence.write_text("0")
    original = output.record_only_receipt
    counter = {"n": 0}

    def flip_after_inventory(*args, **kwargs):
        receipt = original(*args, **kwargs)
        counter["n"] += 1
        evidence.write_text(f"attempt-{counter['n']}")
        return receipt

    monkeypatch.setattr(output, "record_only_receipt", flip_after_inventory)
    result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=record)

    assert result["tmp_reap_error"] is None
    assert not root.exists()
    receipt = record["preserved_evidence"]
    assert receipt["paths"][0]["sha256"] == hashlib.sha256(b"0").hexdigest()
    assert receipt["mode"] == "record-only" and receipt["copied_bytes"] == 0
    assert counter["n"] == 2
    assert not (tmp_path / "batch_state/preserved").exists()
