"""Exercise AGY's real launch boundary with fixture stores and no provider calls."""

import contextlib
import json
import sqlite3
import subprocess

import pytest

from scripts.dispatcher import agy_sandbox
from scripts.lib.readonly_sqlite import open_readonly
from scripts.storage import generations
from scripts.storage.wal_permissions import hold_database
from tests.dispatcher.test_providers_b import _launch, _linked_worktree


@pytest.mark.parametrize("mode", ["legacy", "no_sidecars", "reader", "lifted_writer"])
def test_real_launch_reads_only_the_selected_store_and_existing_sidecars(tmp_path, mode):
    worktree, _head = _linked_worktree(tmp_path)
    primary = tmp_path / "repo"
    (primary / "AGENTS.md").write_text("primary must remain hidden")
    selector = primary / "data" / "sources.db"
    selected = selector
    hidden = None
    with contextlib.ExitStack() as stack:
        if mode != "legacy":
            directory = primary / "data" / "sources-generations"
            directory.mkdir()
            selected = directory / "sources.20261031T010000Z-0123456789ab.db"
            selector.rename(selected)
            selector.symlink_to(selected.relative_to(selector.parent))
            connection = sqlite3.connect(selected)
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("INSERT INTO proof VALUES ('selected')")
            connection.commit()
            connection.close()
            hidden = directory / "sources.20261031T000000Z-abcdef012345.db"
            hidden.write_bytes(b"hidden history")
            selected.with_name(selected.name + ".receipt.json").write_text("hidden receipt")
            if mode == "reader":
                reader = stack.enter_context(contextlib.closing(open_readonly(selected)))
                assert reader.execute("SELECT value FROM proof").fetchall() == [("selected",)]
            elif mode == "lifted_writer":
                hold_database(selected)
                stack.enter_context(generations.store_writer(selector))
                writer = stack.enter_context(contextlib.closing(sqlite3.connect(selected)))
                writer.execute("INSERT INTO proof VALUES ('host writer')")
                writer.commit()
        before = set(agy_sandbox._store_sidecars(selected))
        argv, env = _launch(tmp_path, worktree, "store-layout", ["/bin/true"])
        run = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=120, cwd=worktree)
        receipt = json.loads((tmp_path / "store-layout.sandbox.json").read_text())
        assert (run.returncode, receipt["status"]) == (0, "ran"), (receipt.get("reason"), run.stderr)
        assert receipt["canary"]["passed"] is True
        probes = receipt["canary"]["probes"]
        source_read = next(probe["outcome"] for probe in probes if probe["op"] == "store_read" and probe["store"] == "sources")
        if mode == "no_sidecars":
            assert source_read in [{"status": "read", "store": "sources", "reason": None},
                                   {"status": "refused", "store": "sources", "reason": "wal_sidecars_unavailable"}]
        else:
            assert source_read == {"status": "read", "store": "sources", "reason": None}
        outcomes = {(p["op"], p["path"]): p["outcome"] for p in probes}
        assert outcomes[("stat", str(primary / "AGENTS.md"))] == "ENOENT"
        if hidden is not None:
            assert outcomes[("stat", str(hidden))] == "ENOENT"
            assert outcomes[("stat", str(selected) + ".receipt.json")] == "ENOENT"
        assert set(agy_sandbox._store_sidecars(selected)) == before
        assert not (worktree / "data" / "sources.db").exists()
        assert not (worktree / "data" / "vesum.db").exists()


@pytest.mark.parametrize("kind", ["symlink", "dangling", "file"])
def test_worktree_data_component_never_follows_branch_content(tmp_path, kind):
    worktree, _head = _linked_worktree(tmp_path)
    data = worktree / "data"
    data.rmdir()
    if kind == "file":
        data.write_text("not a directory")
    else:
        data.symlink_to(tmp_path / ("repo/data" if kind == "symlink" else "absent"))
    with pytest.raises(agy_sandbox.Refused, match="worktree_local_store"):
        agy_sandbox._trusted_database(worktree, tmp_path / "repo", "data/sources.db")


def test_disagreeing_primary_anchors_refuse_before_scratch_or_provider(tmp_path, monkeypatch):
    worktree, _head = _linked_worktree(tmp_path)
    monkeypatch.setattr(agy_sandbox, "main_checkout_root", lambda root: tmp_path)
    argv, _env = _launch(tmp_path, worktree, "anchor", ["/bin/true"])
    assert agy_sandbox.main(argv[argv.index("--task-id"):]) == 125
    receipt = json.loads((tmp_path / "anchor.sandbox.json").read_text())
    assert receipt["reason"] == "store_primary_disagreement"
    assert not (tmp_path / "scratch-anchor").exists()
