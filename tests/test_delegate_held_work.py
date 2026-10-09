"""Runtime held patches survive finalize and orphan reaping (#10000 AC-01)."""

from __future__ import annotations

import errno
import json
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


def _retrieve(primary: Path, record: dict) -> tuple[Path, dict]:
    receipt = record["preserved_held_work"]
    location = primary / receipt["location"]
    manifest = json.loads(location.with_suffix(".manifest.json").read_text())
    assert manifest == receipt
    assert output.verify_retrieval(primary, manifest) == receipt["retrieval_proof_sha256"]
    return location, manifest


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
    location, manifest = _retrieve(tmp_path, saved)
    assert manifest["count"] == 2
    assert (location / "readers.patch").read_bytes() == b"held patch\n"
    assert (location / "handoff.md").read_text() == "handoff\n"
    assert not (location / "disposable").exists()
    assert delegate._sweep_runtime_tmp_orphans()["leases_reaped"] == 0
    _retrieve(tmp_path, saved)


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
    location, _ = _retrieve(tmp_path, saved)
    assert (location / "readers.patch").read_text() == "held\n"


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
    location, _ = _retrieve(tmp_path, record)
    assert (location / "sub/held patch.txt").read_bytes() == b""


@pytest.mark.parametrize(
    "response",
    [
        "The worker's patch is `{root}/readers.patch`; it isn't committed.",
        "It isn't committed: {root}/readers.patch. I couldn't finish.",
        "The worker's patch is '{root}/readers.patch'; it couldn't be pushed.",
        '"The worker\'s patch is {root}/readers.patch and isn\'t committed."',
        "'The worker's patch is $TMPDIR/readers.patch and couldn't be pushed.'",
        '`The worker\'s patch is "{root}/readers.patch" and isn\'t committed.`',
        '"Held ${{TMPDIR}}/readers.patch and couldn\'t finish."',
        '"{root}/readers.patch couldn\'t be pushed."',
    ],
)
def test_apostrophe_prose_preserves_cited_patch(lease, tmp_path, response):
    root, namespace, record = lease
    (root / "readers.patch").write_text("held patch")
    result = delegate._reap_runtime_tmp_lease(
        root, namespace, task_record=record, response=response.format(root=root)
    )
    assert result["tmp_reap_error"] is None
    assert not root.exists()
    location, manifest = _retrieve(tmp_path, record)
    assert manifest["count"] == 1
    assert (location / "readers.patch").read_text() == "held patch"


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
def test_long_quoted_prose_preserves_real_citation_and_allows_cleanup(lease, tmp_path, quote, passage):
    root, namespace, record = lease
    assert len(passage.encode("utf-8")) > 300
    (root / "readers.patch").write_text("held patch")
    response = f"Report: {quote}{passage}{quote}. Held `readers.patch`."
    assert held.cited_paths(root, record, response) == ["readers.patch"]
    result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=record, response=response)
    assert result["tmp_reap_error"] is None
    assert not root.exists()
    location, manifest = _retrieve(tmp_path, record)
    assert manifest["count"] == 1
    assert (location / "readers.patch").read_text() == "held patch"


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
def test_candidate_open_errors_only_skip_undeclared_long_names(
    lease, tmp_path, monkeypatch, stage, error_number, declared
):
    root, namespace, record = lease
    (root / "readers.patch").write_text("held patch")
    candidate = "prose/patch" if stage == "parent" else "prose"
    if declared:
        record["held_work"] = [candidate]
    original = held.artifacts._open_parent if stage == "parent" else held.open_leaf_descriptor

    def fail_candidate(fd, name):
        if name == (("prose",) if stage == "parent" else "prose"):
            raise OSError(error_number, "fixture open error")
        return original(fd, name)

    if stage == "parent":
        monkeypatch.setattr(held.artifacts, "_open_parent", fail_candidate)
    else:
        monkeypatch.setattr(held, "open_leaf_descriptor", fail_candidate)
    result = delegate._reap_runtime_tmp_lease(
        root, namespace, task_record=record, response=f"`{candidate}` `readers.patch`"
    )
    if declared or error_number != errno.ENAMETOOLONG:
        assert result["tmp_reap_error"] == held.HeldWorkPreservationError.code
        assert root.exists()
        assert (root / "readers.patch").read_text() == "held patch"
    else:
        assert result["tmp_reap_error"] is None
        assert not root.exists()
        location, manifest = _retrieve(tmp_path, record)
        assert manifest["count"] == 1
        assert (location / "readers.patch").read_text() == "held patch"


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
        location, manifest = _retrieve(tmp_path, record)
        assert manifest["count"] == 1
        assert (location / "readers.patch").read_text() == "held patch"
    else:
        assert not (tmp_path / "batch_state/preserved").exists()


def test_explicit_directory_declaration_refuses_cleanup(lease):
    root, namespace, record = lease
    (root / "sub").mkdir()
    record["held_work"] = ["sub"]
    result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=record, response="")
    assert result["tmp_reap_error"] == held.HeldWorkPreservationError.code
    assert root.exists()


@pytest.mark.parametrize("declaration", ["readers.patch", "absolute"])
def test_explicit_held_work_declarations(lease, tmp_path, declaration):
    root, namespace, record = lease
    (root / "readers.patch").write_text("held")
    record["held_work"] = [str(root / "readers.patch") if declaration == "absolute" else declaration]
    result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=record, response="")
    assert result["tmp_reap_error"] is None
    location, _ = _retrieve(tmp_path, record)
    assert (location / "readers.patch").read_text() == "held"


@pytest.mark.parametrize("attack", ["leaf", "parent", "traversal", "prefix"])
def test_held_work_refuses_symlinks_and_boundary_attacks(lease, tmp_path, attack):
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
    assert result["tmp_reap_error"] == held.HeldWorkPreservationError.code
    assert result["tmp_bytes_freed"] == 0
    assert root.exists()
    assert (outside / "private.patch").read_text() == "must not copy"
    assert not (tmp_path / "batch_state/preserved").exists()


@pytest.mark.parametrize("failure", ["copy", "manifest", "metadata", "cap", "unreadable_result"])
def test_preservation_failure_refuses_cleanup_and_orphan_retry(lease, tmp_path, monkeypatch, failure):
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
        monkeypatch.setattr(held.artifacts, "_copy_verified", fail)
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
    assert result["tmp_reap_error"] == held.HeldWorkPreservationError.code
    assert result["tmp_bytes_freed"] == 0
    assert (root / "readers.patch").read_text() == "held"
    swept = delegate._sweep_runtime_tmp_orphans()
    assert swept["leases_reaped"] == 0
    assert swept["errors"] == 1
    assert swept["error_details"][0][2] == held.HeldWorkPreservationError.code


def test_worker_preamble_guides_held_work_to_reports(tmp_path, monkeypatch):
    monkeypatch.setattr(delegate, "_resolve_primary_root_for_worktree", lambda _root: tmp_path)
    prompt = delegate._augment_prompt_with_worktree("task", tmp_path, mode="workspace-write")
    assert "[held work]" in prompt
    assert "`batch_state/reports/`" in prompt
    assert "cite its absolute file path" in prompt


def test_structured_report_and_deliverable_citations(lease, tmp_path):
    root, namespace, record = lease
    (root / "report.txt").write_text("held report")
    (root / "patch.txt").write_text("held patch")
    record["report"] = {"files": [f"`{root}/report.txt`", 42]}
    record["deliverable"] = [f"{root}/patch.txt"]
    result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=record, response="")
    assert result["tmp_reap_error"] is None
    _, manifest = _retrieve(tmp_path, record)
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
def test_invalid_or_missing_declaration_refuses_cleanup(lease, declaration):
    root, namespace, record = lease
    record["held_work"] = declaration
    result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=record, response="")
    assert result["tmp_reap_error"] == held.HeldWorkPreservationError.code
    assert root.exists()


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


def test_destination_symlink_refuses_cleanup_without_writing_outside(lease, tmp_path):
    root, namespace, record = lease
    (root / "patch").write_text("held")
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "batch_state").symlink_to(outside, target_is_directory=True)
    result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=record, response=f"`{root}/patch`")
    assert result["tmp_reap_error"] == held.HeldWorkPreservationError.code
    assert root.exists()
    assert list(outside.iterdir()) == []


def test_changed_task_attempt_refuses_receipt_publication_and_cleanup(lease):
    root, namespace, record = lease
    (root / "patch").write_text("held")
    path = delegate._state_path(record["task_id"])
    replacement = {**record, "run_nonce": "replacement"}
    delegate._write_state_atomic(path, replacement)
    result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=record, response=f"`{root}/patch`")
    assert result["tmp_reap_error"] == held.HeldWorkPreservationError.code
    assert root.exists()
    assert "preserved_held_work" not in delegate._read_state(path)


def test_copy_mutation_refuses_cleanup(lease, monkeypatch):
    root, namespace, record = lease
    (root / "patch").write_text("held")
    original_copy = held.artifacts._copy_verified

    def mutate_after_copy(*args, **kwargs):
        original_copy(*args, **kwargs)
        (root / "patch").write_text("new content")

    monkeypatch.setattr(held.artifacts, "_copy_verified", mutate_after_copy)
    result = delegate._reap_runtime_tmp_lease(root, namespace, task_record=record, response=f"`{root}/patch`")
    assert result["tmp_reap_error"] == held.HeldWorkPreservationError.code
    assert root.exists()
