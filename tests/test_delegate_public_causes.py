"""#9878: every reason that can leave the machine goes through one sink and names a registered cause.

The task record's reason fields, the rescue and refusal rows and the lines
that print them accept only a cause from the closed registry
(``delegate.public_causes``) with fixed parameters. Anything else is replaced
at the sink and its text kept in the task's local diagnostic file, which is
opened without following symlinks, created 0600 and bounded.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate

# Autouse fixtures of the delegate unit suite that keep a ``_run_worker`` hermetic.
from tests.test_delegate import (  # noqa: F401
    _agy_dispatch_worktree,
    _bg_mock_result,
    _fixture_runtime_tmp_root,
    _fixture_worktree_lock_dir,
    _keep_delegate_unit_tests_local,
    _review_target_from_fixture_refs,
    _sanitize_git_env_for_test,
    _stub_node_modules_integrity_sweep,
    _stub_primary_integrity_sweep,
    _stub_venv_integrity_sweep,
    _stub_worktree_cleanup_integrity_sweep,
    _worktree_add_via_run,
    tmp_tasks_dir,
)
from tests.test_kimi_coding_only_admission import _FAKE_TOKEN, HOSTILE_GIT_ERRORS, assert_no_host_details

pytestmark = pytest.mark.usefixtures("tmp_tasks_dir")

# A host name, a private path and two address-like tokens, with a credential, in one error.
HOSTILE = (
    "fatal: unable to access 'https://deploy:" + _FAKE_TOKEN + "@git.build-host.example.internal/learn.git/': "
    "cannot read /srv/synthetic-operator/backups/learn.git via 203.0.113.77 and [fe80::1ff:fe23:4567:890a%eth7]"
)
HOSTILE_MARKERS = ("build-host", "example.internal", "/srv/", "synthetic-operator", "203.0.113.77", "fe80", "eth7")
# The public reason fields and row keys this contract names, enumerated here rather than read from the module.
PUBLIC_RECORD_FIELDS = (
    "last_error",
    "finalize_error",
    "incomplete_run_reason",
    "no_deliverable_reason",
    "failure_reason",
    "failure_code",
    "review_verdict_failure",
    "rescue_status",
    "kimi_content_refusal",
)
PUBLIC_NESTED_FIELDS = (("auto_finalize", "error"),)
PUBLIC_ROW_KEYS = ("reason", "failure_code")


def _diagnostics(task_id: str) -> list[dict]:
    path = delegate._diagnostic_path(task_id)
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def _assert_kept_locally(task_id: str, *, field: str | None = None) -> dict:
    """The local diagnostic keeps the injected error, its credential redacted; returns the entry."""
    entries = [entry for entry in _diagnostics(task_id) if field is None or entry["field"] == field]
    kept = [entry for entry in entries if "git.build-host.example.internal" in entry["diagnostic"]]
    assert kept, entries
    for entry in kept:
        assert "/srv/synthetic-operator/backups" in entry["diagnostic"] and "203.0.113.77" in entry["diagnostic"]
        assert _FAKE_TOKEN not in entry["diagnostic"]
    return kept[0]


def _public_values(record: dict) -> list[object]:
    values: list[object] = [record.get(field) for field in (*PUBLIC_RECORD_FIELDS, *PUBLIC_ROW_KEYS)]
    for parent, key in PUBLIC_NESTED_FIELDS:
        nested = record.get(parent)
        values.append(nested.get(key) if isinstance(nested, dict) else None)
    return [value for value in values if value is not None]


def _assert_public(record: dict) -> None:
    """No host detail shows in any public reason of ``record``, and each one is a registered cause."""
    public = json.dumps(_public_values(record), ensure_ascii=False)
    for marker in (*HOSTILE_MARKERS, _FAKE_TOKEN):
        assert marker not in public, marker
    for value in _public_values(record):
        assert delegate.is_public_cause(value), value


# --- the registry and the sink -------------------------------------------------------------------


def test_the_public_fields_are_the_ones_this_contract_names():
    """Removing a field or row key from the sink fails here, not silently in production."""
    assert set(delegate.PUBLIC_RECORD_REASON_FIELDS) == set(PUBLIC_RECORD_FIELDS)
    assert delegate.PUBLIC_RECORD_NESTED_REASON_FIELDS == PUBLIC_NESTED_FIELDS
    assert delegate.PUBLIC_ROW_REASON_KEYS == PUBLIC_ROW_KEYS


def test_every_registered_cause_is_fixed_text():
    for cause in delegate.public_causes():
        assert delegate.is_public_cause(cause), cause
        for marker in ("/", "@", "://", "%", "~", "\\", "\n"):
            assert marker not in cause, (cause, marker)


@pytest.mark.parametrize(
    "value",
    [
        "temp_index_failed, git add, exit 128",
        "file_unreadable, PermissionError EACCES",
        "read_only_checkout_mutation, count 3",
        "background_jobs_alive_at_exit; worker_failed, exit 1",
        "kimi_content_refused; diff_command_failed, git diff-tree, exit 128",
        "task attempt changed after rescue push; recovery ref preserved",
    ],
)
def test_a_registered_cause_with_fixed_parameters_is_public(value):
    assert delegate.is_public_cause(value)
    assert delegate.public_cause(value) == (value, None)


@pytest.mark.parametrize(
    "value",
    [
        HOSTILE,
        "temp_index_failed, git.build-host.example.internal",
        "temp_index_failed, git build-host",
        "temp_index_failed, exit 128 from 203.0.113.77",
        "temp_index_failed, Buildhost",
        "temp_index_failed, OSError EHOSTNAME",
        "made_up_code",
        "made_up_code, exit 1",
        "x" * 600,
    ],
)
def test_anything_else_is_replaced_and_kept_for_the_local_record(value):
    public, cause = delegate.public_cause(value)
    assert public is not None and delegate.is_public_cause(public)
    assert "unclassified_error" in public
    assert cause is not None and cause.diagnostic == value


def test_an_exception_publishes_its_class_only():
    public, cause = delegate.public_cause(OSError(13, HOSTILE))
    assert public == "unclassified_error, PermissionError EACCES"
    assert "git.build-host.example.internal" in cause.diagnostic


def test_a_non_string_value_is_replaced():
    assert delegate.public_cause({"error": HOSTILE})[0] == "unclassified_error"
    assert delegate.public_cause(None) == (None, None)


# --- no record write bypasses the sink -----------------------------------------------------------


def _delegate_tree() -> ast.Module:
    return ast.parse(Path(delegate.__file__).read_text(encoding="utf-8"))


def _functions_referencing(tree: ast.Module, name: str) -> set[str]:
    """Functions whose body names ``name`` (as a name or an attribute), the import excluded."""
    found: set[str] = set()
    for function in ast.walk(tree):
        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for node in ast.walk(function):
            if (isinstance(node, ast.Name) and node.id == name) or (
                isinstance(node, ast.Attribute) and node.attr == name
            ):
                found.add(function.name)
    return found


# The dead-worker markers persist the record themselves unless handed a writer.
_RECORD_MARKERS = (
    "mark_dead_worker_terminal",
    "mark_orphaned_worktree_prep_crashed",
    "mark_orphaned_admission_hold_crashed",
)


def test_only_the_sink_writes_a_task_record():
    """AST regression guard: the raw writer is called from the sink alone, and every record writer goes through it.

    A guard only, not the proof: it sees the writers it names, not a direct
    file write. The runtime tests below write through the persistence point
    and read the record back from disk.
    """
    tree = _delegate_tree()
    assert _functions_referencing(tree, "write_state_unlocked") == {"_write_record_unlocked"}
    assert "_write_state_atomic" in _functions_referencing(tree, "_write_record_unlocked")
    module_level = [
        node
        for node in tree.body
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.ImportFrom, ast.Import))
        and any(isinstance(sub, ast.Name) and sub.id == "write_state_unlocked" for sub in ast.walk(node))
    ]
    assert module_level == []  # no alias of the raw writer escapes the sink
    marker_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _RECORD_MARKERS
    ]
    assert {call.func.id for call in marker_calls} == set(_RECORD_MARKERS)
    for call in marker_calls:  # each marker is handed the sink as its writer
        writers = [keyword.value for keyword in call.keywords if keyword.arg == "write"]
        assert [getattr(writer, "id", None) for writer in writers] == ["_write_record_unlocked"], call.func.id


def test_every_rescue_row_leaves_through_the_sink():
    tree = _delegate_tree()
    assert {"_rescue_task", "cmd_rescue"} <= _functions_referencing(tree, "_public_row")


@pytest.mark.parametrize("field", PUBLIC_RECORD_FIELDS)
def test_a_record_write_replaces_free_text_in_every_public_field(field):
    """Runtime: whatever a producer put in a public field, the record on disk holds a public cause."""
    path = delegate._state_path("sink-field")
    delegate._write_state_atomic(path, {"task_id": "sink-field", field: HOSTILE})

    record = json.loads(path.read_text(encoding="utf-8"))
    _assert_public(record)
    assert record[field] == "unclassified_error"
    assert _assert_kept_locally("sink-field", field=field)["source"] == "record"


def test_a_record_write_replaces_free_text_in_the_auto_finalize_error():
    path = delegate._state_path("sink-nested")
    delegate._write_state_atomic(path, {"task_id": "sink-nested", "auto_finalize": {"ok": False, "error": HOSTILE}})

    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["auto_finalize"] == {"ok": False, "error": "unclassified_error"}
    _assert_kept_locally("sink-nested", field="auto_finalize.error")


def test_a_typed_cause_in_a_record_field_is_rendered_and_its_text_kept():
    path = delegate._state_path("sink-typed")
    cause = delegate._TypedCause("worker_spawn_failed", error="OSError ENOENT", diagnostic=HOSTILE)
    delegate._write_state_atomic(path, {"task_id": "sink-typed", "last_error": cause})

    assert json.loads(path.read_text(encoding="utf-8"))["last_error"] == "worker_spawn_failed, OSError ENOENT"
    _assert_kept_locally("sink-typed", field="last_error")


def test_a_rescue_row_with_free_text_is_replaced_at_the_sink(monkeypatch):
    path = delegate._state_path("sink-row")
    delegate._write_state_atomic(path, {"task_id": "sink-row", "status": "failed"})
    monkeypatch.setattr(
        delegate,
        "_rescue_task_row",
        lambda *_a, **_k: {"task_id": "sink-row", "action": "error", "reason": HOSTILE, "failure_code": HOSTILE},
    )

    row = delegate._rescue_task(path, apply=True)

    assert (row["reason"], row["failure_code"]) == ("unclassified_error", "unclassified_error")
    assert row["diagnostic"].endswith("sink-row.diag")
    _assert_public(row)
    _assert_kept_locally("sink-row", field="reason")


def _status(task_id: str, capsys) -> dict:
    assert delegate.cmd_status(argparse.Namespace(task_id=task_id, run_nonce=None)) == 0
    return json.loads(capsys.readouterr().out)


def test_a_raw_reason_assigned_in_memory_during_status_is_persisted_as_a_typed_cause(monkeypatch, capsys):
    """``cmd_status`` heals an orphaned record; a raw ``last_error`` assigned to it in memory is caught at the write."""
    task_id = "sink-status-memory"
    path = delegate._state_path(task_id)
    record = {
        "task_id": task_id,
        "status": "spawning",
        "pid": None,
        "run_nonce": "nonce-1",
        "started_at": "2026-10-06T00:00:00+00:00",
        "worktree_prep": {"run_nonce": "nonce-1", "owner_pid": 999_999},
    }
    path.write_text(json.dumps(record), encoding="utf-8")

    def orphaned_with_raw_reason(current):
        current["last_error"] = HOSTILE  # any producer, in memory, before the record is persisted
        return True

    monkeypatch.setattr(delegate.worktree_prep, "is_orphaned_prep_record", orphaned_with_raw_reason)

    shown = _status(task_id, capsys)

    on_disk = json.loads(path.read_text(encoding="utf-8"))
    assert (on_disk["status"], on_disk["last_error"]) == ("crashed", "unclassified_error")
    _assert_public(on_disk)
    assert shown["last_error"] == "unclassified_error"
    _assert_public(shown)
    assert _assert_kept_locally(task_id, field="last_error")["source"] == "record"


def test_a_raw_reason_already_on_disk_is_replaced_when_status_persists_the_record(monkeypatch, capsys):
    """A dead worker's record, raw ``last_error`` from an earlier writer: the heal write holds a typed cause."""
    task_id = "sink-status-disk"
    path = delegate._state_path(task_id)
    path.write_text(
        json.dumps({"task_id": task_id, "status": "running", "pid": 999_999, "last_error": HOSTILE}), encoding="utf-8"
    )
    monkeypatch.setattr(delegate, "_pid_alive", lambda _pid: False)

    shown = _status(task_id, capsys)

    on_disk = json.loads(path.read_text(encoding="utf-8"))
    assert (on_disk["status"], on_disk["last_error"]) == ("crashed", "unclassified_error")
    _assert_public(on_disk)
    _assert_public(shown)
    _assert_kept_locally(task_id, field="last_error")


# --- the producers the review named: injected host details never reach a public field ------------


def _kimi_worktree(tmp_path: Path, monkeypatch, task_id: str) -> Path:
    worktree = _agy_dispatch_worktree(tmp_path, f"kimi/{task_id}")
    delegate._write_state_atomic(
        delegate._state_path(task_id),
        {
            "task_id": task_id,
            "worktree_path": str(worktree),
            "worktree_base": "main",
            "owned_paths": ["site/src/components/Label.tsx"],
        },
    )
    return worktree


def test_a_worker_admission_tree_reader_error_never_reaches_the_refusal(tmp_path, monkeypatch, capsys):
    """``_kimi_worker_refusal``: the tree reader's message (``kimi_admission._content_reasons``) stays local."""
    _sanitize_git_env_for_test(monkeypatch)
    task_id = "sink-admission"
    worktree = _kimi_worktree(tmp_path, monkeypatch, task_id)

    def unreadable(_cwd):
        raise RuntimeError(HOSTILE)

    monkeypatch.setattr(delegate, "_kimi_worktree_trees", unreadable)
    before = delegate._state_path(task_id).read_bytes()

    rc = delegate._run_worker(
        task_id=task_id,
        agent="kimi",
        prompt="Implement it.",
        mode="workspace-write",
        cwd_str=str(worktree),
        model=None,
        hard_timeout=60,
    )

    err = capsys.readouterr().err
    assert rc == 1
    assert "ROUTING REFUSED: KIMI CODING-ONLY: kimi_admission_refused, RuntimeError" in err
    assert_no_host_details(err, worktree)
    assert delegate._state_path(task_id).read_bytes() == before
    entry = _assert_kept_locally(task_id)
    assert (entry["source"], entry["code"]) == ("worker", "kimi_admission_refused")


def _dirty_owned_worktree(tmp_path: Path, task_id: str) -> Path:
    worktree = _agy_dispatch_worktree(tmp_path, f"claude/{task_id}")
    (worktree / "scripts").mkdir()
    (worktree / "scripts" / "fix.py").write_text("fixed = True\n", encoding="utf-8")
    delegate._write_state_atomic(
        delegate._state_path(task_id),
        {
            "task_id": task_id,
            "worktree_path": str(worktree),
            "worktree_branch": f"claude/{task_id}",
            "worktree_base": "main",
            "owned_paths": ["scripts/"],
            "keep_worktree": True,
        },
    )
    return worktree


def _failing_git(monkeypatch, subcommand: str, stderr: str = HOSTILE) -> None:
    """``git <subcommand>`` exits 128 with ``stderr``; for add and commit, only auto-finalize's own scoped run."""
    real_run = delegate.subprocess.run

    def run(cmd, *args, **kwargs):
        words = [str(word) for word in cmd] if isinstance(cmd, (list, tuple)) else []
        scoped = subcommand not in ("add", "commit") or "--literal-pathspecs" in words
        if words[:1] == ["git"] and delegate._git_subcommand(words) == subcommand and scoped:
            return subprocess.CompletedProcess(cmd, 128, "", stderr)
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(delegate.subprocess, "run", run)


@pytest.mark.parametrize(
    ("subcommand", "public"),
    [
        ("add", "auto_finalize_add_failed, git add, exit 128"),
        ("commit", "auto_finalize_commit_failed, git commit, exit 128"),
        ("push", "auto_finalize_push_failed, git push, exit 128"),
    ],
)
def test_an_auto_finalize_git_error_never_reaches_its_error(tmp_path, monkeypatch, subcommand, public):
    """``_auto_finalize_dirty_worktree``: git's stderr from add, commit and push stays local."""
    _sanitize_git_env_for_test(monkeypatch)
    task_id = f"sink-af-{subcommand}"
    worktree = _dirty_owned_worktree(tmp_path, task_id)
    _failing_git(monkeypatch, subcommand)

    result = delegate._auto_finalize_dirty_worktree(
        worktree=worktree,
        task_id=task_id,
        agent="claude",
        branch=f"claude/{task_id}",
        base_branch="main",
        owned_paths=["scripts/"],
    )

    assert result.ok is False and result.error == public
    _assert_kept_locally(task_id, field="auto_finalize.error")


def test_an_auto_finalize_exception_and_its_failed_reset_publish_their_classes_only(tmp_path, monkeypatch):
    _sanitize_git_env_for_test(monkeypatch)
    task_id = "sink-af-exception"
    worktree = _dirty_owned_worktree(tmp_path, task_id)

    def crash(*_args, **_kwargs):
        raise RuntimeError(HOSTILE)

    monkeypatch.setattr(delegate, "_push_auto_finalize_branch", crash)
    _failing_git(monkeypatch, "reset")

    result = delegate._auto_finalize_dirty_worktree(
        worktree=worktree,
        task_id=task_id,
        agent="claude",
        branch=f"claude/{task_id}",
        base_branch="main",
        owned_paths=["scripts/"],
    )

    assert result.error == "auto_finalize_failed, RuntimeError; auto_finalize_reset_failed, git reset, exit 128"
    assert len(_diagnostics(task_id)) == 2
    _assert_kept_locally(task_id, field="auto_finalize.error")


def test_an_auto_finalize_pr_error_never_reaches_its_error(tmp_path, monkeypatch):
    _sanitize_git_env_for_test(monkeypatch)
    task_id = "sink-af-pr"
    worktree = _dirty_owned_worktree(tmp_path, task_id)
    monkeypatch.setattr(delegate, "_push_auto_finalize_branch", lambda *_a: None)
    monkeypatch.setattr(
        delegate,
        "request_run",
        lambda *_a, **_k: subprocess.CompletedProcess(["gh"], 1, "", HOSTILE),
    )

    result = delegate._auto_finalize_dirty_worktree(
        worktree=worktree,
        task_id=task_id,
        agent="claude",
        branch=f"claude/{task_id}",
        base_branch="main",
        open_pr=True,
        owned_paths=["scripts/"],
    )

    assert result.error == "auto_finalize_pr_failed, exit 1"
    assert result.commit_sha  # pushed already: never reset after a PR error
    _assert_kept_locally(task_id, field="auto_finalize.error")


def _run_owned_worker(task_id: str, worktree: Path) -> dict:
    with patch("agent_runtime.runner.invoke", return_value=_bg_mock_result("")):
        delegate._run_worker(
            task_id=task_id,
            agent="claude",
            prompt="hi",
            mode="danger",
            cwd_str=str(worktree),
            model=None,
            hard_timeout=60,
            effort=None,
        )
    return delegate._read_state(delegate._state_path(task_id))


def test_an_auto_finalize_push_error_never_reaches_the_task_record(tmp_path, monkeypatch):
    """End to end: git's push stderr is not in ``auto_finalize.error`` or any other public field."""
    _sanitize_git_env_for_test(monkeypatch)
    task_id = "sink-af-record"
    worktree = _dirty_owned_worktree(tmp_path, task_id)
    _failing_git(monkeypatch, "push")

    record = _run_owned_worker(task_id, worktree)

    assert record["status"] == "needs_finalize"
    assert record["auto_finalize"]["error"] == "auto_finalize_push_failed, git push, exit 128"
    _assert_public(record)
    _assert_kept_locally(task_id, field="auto_finalize.error")


def test_the_outer_finalize_handler_publishes_the_exception_class_only(tmp_path, monkeypatch):
    """The broad finalize handler: the exception's message stays local; the task still needs a human."""
    _sanitize_git_env_for_test(monkeypatch)
    task_id = "sink-finalize"
    worktree = _dirty_owned_worktree(tmp_path, task_id)

    def crash(*_args, **_kwargs):
        raise RuntimeError(HOSTILE)

    monkeypatch.setattr(delegate, "_count_commits_ahead", crash)

    record = _run_owned_worker(task_id, worktree)

    assert record["status"] == "needs_finalize"
    assert record["finalize_error"] == "finalize_failed, RuntimeError"
    _assert_public(record)
    _assert_kept_locally(task_id, field="finalize_error")


@pytest.mark.parametrize("kind", sorted(HOSTILE_GIT_ERRORS))
def test_a_failed_worker_s_stderr_never_reaches_last_error(tmp_path, monkeypatch, kind):
    """The worker CLI's own error line is summarized by its typed outcome; the line stays local."""
    task_id = f"sink-worker-{kind.replace('_', '-')}"
    path = delegate._state_path(task_id)
    delegate._write_state_atomic(path, {"task_id": task_id})
    result = type(
        "_Result",
        (),
        {"ok": False, "response": "", "stderr_excerpt": HOSTILE_GIT_ERRORS[kind], "returncode": 2,
         "rate_limited": False, "model": "m", "effort": "high", "cli_version": "1"},
    )()  # fmt: skip

    with patch("agent_runtime.runner.invoke", return_value=result):
        delegate._run_worker(
            task_id=task_id, agent="claude", prompt="hi", mode="read-only", cwd_str=str(tmp_path),
            model=None, hard_timeout=60, effort=None,
        )  # fmt: skip

    record = delegate._read_state(path)
    assert record["last_error"] == "worker_failed, exit 2"
    _assert_public(record)
    assert_no_host_details(json.dumps(_public_values(record)))


# --- the local diagnostic file -------------------------------------------------------------------


def _cause(text: str = HOSTILE) -> delegate._TypedCause:
    return delegate._TypedCause("rescue_push_failed", "push", 128, diagnostic=text)


def test_the_diagnostic_is_created_private():
    record = delegate._state_path("diag-mode")
    delegate._write_state_atomic(record, {"task_id": "diag-mode"})
    old_umask = os.umask(0)
    try:
        assert delegate._append_diagnostics(record, [("reason", _cause())], source="test")
    finally:
        os.umask(old_umask)

    assert stat.S_IMODE(record.with_suffix(".diag").stat().st_mode) == 0o600


def test_a_diagnostic_left_readable_is_made_private_again():
    record = delegate._state_path("diag-chmod")
    delegate._write_state_atomic(record, {"task_id": "diag-chmod"})
    diag = record.with_suffix(".diag")
    diag.write_text("", encoding="utf-8")
    diag.chmod(0o644)

    assert delegate._append_diagnostics(record, [("reason", _cause())], source="test")
    assert stat.S_IMODE(diag.stat().st_mode) == 0o600


def test_a_symlinked_diagnostic_is_refused_and_its_target_untouched(tmp_path):
    record = delegate._state_path("diag-link")
    delegate._write_state_atomic(record, {"task_id": "diag-link"})
    target = tmp_path / "other-artifact.json"
    target.write_text('{"keep": true}\n', encoding="utf-8")
    record.with_suffix(".diag").symlink_to(target)

    assert delegate._append_diagnostics(record, [("reason", _cause())], source="test") is None
    assert target.read_text(encoding="utf-8") == '{"keep": true}\n'


def test_a_symlinked_task_directory_is_refused(tmp_path):
    real = tmp_path / "real-tasks"
    real.mkdir()
    (real / "diag-dir.json").write_text('{"task_id": "diag-dir"}', encoding="utf-8")
    linked = tmp_path / "linked-tasks"
    linked.symlink_to(real, target_is_directory=True)

    assert delegate._append_diagnostics(linked / "diag-dir.json", [("reason", _cause())], source="test") is None
    assert not (real / "diag-dir.diag").exists()


def test_a_hard_linked_diagnostic_is_refused(tmp_path):
    record = delegate._state_path("diag-hardlink")
    delegate._write_state_atomic(record, {"task_id": "diag-hardlink"})
    target = tmp_path / "other-artifact.txt"
    target.write_text("keep\n", encoding="utf-8")
    os.link(target, record.with_suffix(".diag"))

    assert delegate._append_diagnostics(record, [("reason", _cause())], source="test") is None
    assert target.read_text(encoding="utf-8") == "keep\n"


def test_a_diagnostic_needs_an_existing_task_record():
    record = delegate._state_path("diag-none")
    assert delegate._append_diagnostics(record, [("reason", _cause())], source="test") is None
    assert not record.with_suffix(".diag").exists()


def test_an_oversized_entry_is_cut_to_the_entry_bound():
    record = delegate._state_path("diag-big")
    delegate._write_state_atomic(record, {"task_id": "diag-big"})

    assert delegate._append_diagnostics(record, [("reason", _cause("ж" * 200_000))], source="test")

    (line,) = record.with_suffix(".diag").read_bytes().splitlines(keepends=True)
    assert len(line) <= delegate._DIAG_MAX_ENTRY_BYTES
    entry = json.loads(line)
    assert entry["diagnostic"].endswith(delegate._DIAG_TRUNCATED)
    assert entry["diagnostic"].startswith("ж" * 100)


def test_the_diagnostic_file_rotates_once_and_stays_bounded():
    record = delegate._state_path("diag-rotate")
    delegate._write_state_atomic(record, {"task_id": "diag-rotate"})
    diag = record.with_suffix(".diag")
    rotated = diag.with_name(diag.name + delegate._DIAG_ROTATED_SUFFIX)
    entry_bytes = len(delegate._diagnostic_line("test", "reason", _cause("x" * 3000)))
    writes = 3 * delegate._DIAG_MAX_FILE_BYTES // entry_bytes

    for _ in range(writes):
        assert delegate._append_diagnostics(record, [("reason", _cause("x" * 3000))], source="test")

    assert rotated.is_file()
    assert diag.stat().st_size <= delegate._DIAG_MAX_FILE_BYTES
    assert rotated.stat().st_size <= delegate._DIAG_MAX_FILE_BYTES
    assert stat.S_IMODE(rotated.stat().st_mode) == 0o600
    for path in (diag, rotated):
        for line in path.read_text(encoding="utf-8").splitlines():
            assert json.loads(line)["public"] == "rescue_push_failed, git push, exit 128"


def _oversized_diagnostic(path: Path, *, mode: int = 0o644) -> list[str]:
    """Fill ``path`` with about 2 MiB of numbered entries, left ``mode``; returns the lines written."""
    lines = [
        json.dumps(
            {"code": "rescue_push_failed", "public": "rescue_push_failed", "diagnostic": f"{n:06d} " + "y" * 1000}
        )
        for n in range(2 * 1024 * 1024 // 1050)
    ]
    path.write_text("".join(line + "\n" for line in lines), encoding="utf-8")
    path.chmod(mode)
    assert path.stat().st_size > 2 * 1024 * 1024 - 4096
    return lines


def _assert_bounded_and_private(*paths: Path) -> None:
    for path in paths:
        assert path.stat().st_size <= delegate._DIAG_MAX_FILE_BYTES, path
        assert stat.S_IMODE(path.stat().st_mode) == 0o600, path
        for line in path.read_text(encoding="utf-8").splitlines():
            json.loads(line)  # only whole entries are kept


def test_an_append_beside_an_oversized_diagnostic_leaves_every_file_bounded_and_private():
    """An existing 2 MiB, 0644 ``.diag`` rotates, and the rotated copy keeps only its newest entries."""
    record = delegate._state_path("diag-oversized")
    delegate._write_state_atomic(record, {"task_id": "diag-oversized"})
    diag = record.with_suffix(".diag")
    rotated = diag.with_name(diag.name + delegate._DIAG_ROTATED_SUFFIX)
    lines = _oversized_diagnostic(diag)

    assert delegate._append_diagnostics(record, [("reason", _cause())], source="test")

    _assert_bounded_and_private(diag, rotated)
    kept = rotated.read_text(encoding="utf-8").splitlines()
    assert kept and kept == lines[-len(kept) :]
    assert [json.loads(line)["source"] for line in diag.read_text(encoding="utf-8").splitlines()] == ["test"]


def test_an_existing_oversized_readable_rotated_diagnostic_is_bounded_and_made_private():
    """An existing 2 MiB, 0644 ``.diag.prev`` is cut to its newest entries and made 0600 before the append."""
    record = delegate._state_path("diag-prev")
    delegate._write_state_atomic(record, {"task_id": "diag-prev"})
    diag = record.with_suffix(".diag")
    rotated = diag.with_name(diag.name + delegate._DIAG_ROTATED_SUFFIX)
    lines = _oversized_diagnostic(rotated)

    assert delegate._append_diagnostics(record, [("reason", _cause())], source="test")

    _assert_bounded_and_private(diag, rotated)
    kept = rotated.read_text(encoding="utf-8").splitlines()
    assert kept and kept == lines[-len(kept) :]


def test_a_symlinked_rotated_diagnostic_is_dropped_and_its_target_untouched(tmp_path):
    record = delegate._state_path("diag-prev-link")
    delegate._write_state_atomic(record, {"task_id": "diag-prev-link"})
    diag = record.with_suffix(".diag")
    rotated = diag.with_name(diag.name + delegate._DIAG_ROTATED_SUFFIX)
    target = tmp_path / "other-artifact.txt"
    target.write_text("keep\n" * 100_000, encoding="utf-8")
    rotated.symlink_to(target)

    assert delegate._append_diagnostics(record, [("reason", _cause())], source="test")

    assert not rotated.is_symlink() and not rotated.exists()
    assert target.read_text(encoding="utf-8") == "keep\n" * 100_000
    _assert_bounded_and_private(diag)


def test_the_advisory_committed_diff_error_names_the_exception_class_only(tmp_path, monkeypatch):
    """``_advisory_worker_diff``: its error is recorded in the ceiling check, so the message stays out."""
    _sanitize_git_env_for_test(monkeypatch)
    worktree = _agy_dispatch_worktree(tmp_path, "claude/advisory")
    real_run = delegate.subprocess.run

    def run(cmd, *args, **kwargs):
        if isinstance(cmd, (list, tuple)) and list(cmd[:2]) == ["git", "diff"]:
            raise OSError(HOSTILE)
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(delegate.subprocess, "run", run)

    output, error = delegate._advisory_worker_diff(worktree, "main", ["--numstat"], committed_only=True)

    assert output is None
    assert error == "the worker's committed diff could not be read (OSError)"
