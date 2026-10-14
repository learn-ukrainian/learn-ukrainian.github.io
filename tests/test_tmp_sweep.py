from __future__ import annotations

import hashlib
import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.hygiene import tmp_sweep as sweep
from scripts.hygiene.retention_engine import reap_attributed_temp

# Literal containment expectations: task, process, bidirectional protection.
RELATIONSHIPS = [
    ("equal", True, True, True),
    ("deep_descendant", True, True, True),
    ("immediate_parent", True, False, True),
    ("distant_ancestor", False, False, True),
    ("sibling", False, False, False),
    ("prefix_lookalike", False, False, False),
    ("empty", False, False, False),
    ("mixed", True, True, True),
]


def relationship_references(path, relationship):
    """Construct lexical inputs, independently of the containment predicates."""
    return {
        "equal": [path],
        "deep_descendant": [path.joinpath(*(["nested"] * 32), "held")],
        "immediate_parent": [path.parent],
        "distant_ancestor": [path.parent.parent],
        "sibling": [path.with_name("sibling")],
        "prefix_lookalike": [path.with_name(path.name + "-lookalike") / "held"],
        "empty": [],
        "mixed": [path.with_name("sibling"), path / "nested" / "held"],
    }[relationship]


@pytest.mark.parametrize("relationship,task,process,bidirectional", RELATIONSHIPS)
def test_task_reference_relationships(tmp_path, relationship, task, process, bidirectional):
    path = tmp_path / "root" / "entry"
    assert sweep.task_referenced(path, frozenset(relationship_references(path, relationship))) is task


@pytest.mark.parametrize(
    "path,reference,expected",
    [
        ("root/entry", "root/entry/../sibling", True),
        ("root/entry", "root/./entry/held", True),
        ("root/entry", "root/other/../entry", False),
        ("root/entry", "/root/entry/held", False),
        ("/root/entry", "root/entry/held", False),
        (".", "relative/held", True),
        (".", "/absolute/held", False),
        ("/", "relative/held", False),
        ("/", "/absolute/held", True),
        ("//", "/absolute/held", False),
        ("/", "//absolute/held", False),
    ],
)
def test_task_reference_preserves_lexical_paths(path, reference, expected):
    assert sweep.task_referenced(Path(path), frozenset({Path(reference)})) is expected


@pytest.fixture
def classification_input(tmp_path):
    path = tmp_path / "root" / "impl-8755-probe"
    path.mkdir(parents=True)
    (path / "payload").write_bytes(b"fixture payload")
    for node in (path, path / "payload"):
        os.utime(node, (1_600_000_000, 1_600_000_000))
    info = path.stat()
    now = max(info.st_ctime, (path / "payload").stat().st_ctime) + 3 * 86400
    record = {"status": "done", "finished_at": "2020-01-01T00:00:00Z", "record_sha256": "frozen-record"}
    return path, dict(
        tasks=sweep.TaskInventory({"impl-8755": record}, frozenset(), True),
        references=[],
        process_complete=True,
        worktrees=set(),
        managed=set(),
        now=now,
        min_age_s=86400,
    )


def expected_classification_row(path, inputs, reason, *, early=False, live_pids=()):
    """Expected public fields from fixture stat facts and literal decisions."""
    info = path.stat()
    row = {
        "name": path.name,
        "decision": "would_reap" if reason in {"dead_attributed_task", "unattributed_scratch"} else "preserve",
        "bytes": None,
        "task": None,
        "live_pids": [],
        "identity": [info.st_dev, info.st_ino, info.st_uid],
        "kind": "directory",
    }
    if not early:
        facts = [node.stat() for node in [path, *path.iterdir()]]
        newest = max(info.st_mtime for info in facts)
        row.update(
            bytes=sum(info.st_blocks * 512 for info in facts),
            newest_mtime=newest,
            newest_change=max(max(info.st_ctime, info.st_mtime) for info in facts),
            age_hours=round(max(0, inputs["now"] - newest) / 3600, 2),
            live_pids=list(live_pids),
        )
        if inputs["tasks"].records:
            row.update(task="impl-8755", task_record=inputs["tasks"].records["impl-8755"])
    return row | {"reason": reason}


def assert_classification_row(path, inputs, reason, *, early=False, live_pids=()):
    expected = expected_classification_row(path, inputs, reason, early=early, live_pids=live_pids)
    row = sweep.classify_path(path, **inputs)
    assert row == expected
    proof = {key: value for key, value in expected.items() if key != "age_hours"}
    expected_digest = hashlib.sha256(json.dumps(proof, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert sweep.proof_digest(row) == expected_digest


@pytest.mark.parametrize("mode", ["attributed", "scratch"])
@pytest.mark.parametrize("source", ["task", "process", "managed", "worktree"])
@pytest.mark.parametrize("relationship,task,process,bidirectional", RELATIONSHIPS)
def test_classification_containment_rows_and_proofs(
    classification_input, mode, source, relationship, task, process, bidirectional
):
    path, inputs = classification_input
    if mode == "scratch":
        inputs.update(tasks=sweep.TaskInventory({}, frozenset(), True), scratch=sweep.ScratchPolicy())
    refs = relationship_references(path, relationship)
    live_pids = []
    protected = {"task": task, "process": process, "managed": bidirectional, "worktree": bidirectional}[source]
    if source == "task":
        inputs["tasks"] = sweep.TaskInventory(inputs["tasks"].records, frozenset(refs), True)
    elif source == "process":
        # Duplicate holders and multiple references must still report sorted unique PIDs.
        inputs["references"] = [(pid, ref) for pid in (9, 3, 9) for ref in refs]
        live_pids = [3, 9] if protected else []
    else:
        inputs["managed" if source == "managed" else "worktrees"] = set(refs)
    reasons = {"task": "task_reference", "process": "live_process", "managed": "managed_scratch",
               "worktree": "registered_worktree"}
    reason = reasons[source] if protected else "dead_attributed_task" if mode == "attributed" else "unattributed_scratch"
    assert_classification_row(path, inputs, reason, early=source == "managed" and protected, live_pids=live_pids)


@pytest.mark.parametrize("mode", ["attributed", "scratch"])
@pytest.mark.parametrize(
    "case,reason",
    [
        ("process_unknown", "liveness_unknown"),
        ("task_unknown", "task_inventory_unknown"),
        ("malformed_task", "task_not_settled"),
        ("completion_unknown", "task_completion_unknown"),
        ("known_holder_unknown_probe", "live_process"),
        ("task_before_unknown_probe", "task_reference"),
        ("managed_before_registration", "managed_scratch"),
        ("registration_before_holder", "git_registration_unknown"),
        ("worktree_before_holder", "registered_worktree"),
        ("foreign_before_holder", "foreign_owner"),
        ("tree_before_holder", "git_metadata"),
        ("holder_before_task", "live_process"),
        ("young_before_task_unknown", "too_young"),
        ("unsettled_before_age", "task_not_settled"),
    ],
)
def test_classification_refusal_precedence(classification_input, monkeypatch, mode, case, reason):
    path, inputs = classification_input
    records = inputs["tasks"].records
    if mode == "scratch":
        records = {}
        inputs.update(tasks=sweep.TaskInventory(records, frozenset(), True), scratch=sweep.ScratchPolicy())
    if case in {"process_unknown", "known_holder_unknown_probe", "task_before_unknown_probe"}:
        inputs["process_complete"] = False
    if case in {"task_unknown", "young_before_task_unknown"}:
        inputs["tasks"] = sweep.TaskInventory(records, frozenset(), False)
    if case in {"malformed_task", "completion_unknown", "unsettled_before_age"}:
        record = {"status": None if case != "completion_unknown" else "done", "finished_at": None,
                  "record_sha256": None}
        inputs["tasks"] = sweep.TaskInventory({"impl-8755": record}, frozenset(), case != "malformed_task")
    if case in {"known_holder_unknown_probe", "registration_before_holder", "worktree_before_holder",
                "foreign_before_holder", "tree_before_holder", "holder_before_task"}:
        inputs["references"] = [(9, path / "payload"), (3, path), (9, path)]
    if case in {"holder_before_task", "task_before_unknown_probe"}:
        inputs["tasks"] = sweep.TaskInventory(records, frozenset({path / "nested" / "held"}), False)
    if case in {"managed_before_registration", "registration_before_holder"}:
        inputs["worktrees"] = None
    if case == "managed_before_registration":
        inputs["managed"] = {path / "managed"}
    if case == "worktree_before_holder":
        inputs["worktrees"] = {path.parent}
    if case == "foreign_before_holder":
        monkeypatch.setattr(sweep.os, "geteuid", lambda: path.stat().st_uid + 1)
    if case == "tree_before_holder":
        (path / ".git").write_text("fixture metadata")
    if case in {"young_before_task_unknown", "unsettled_before_age"}:
        inputs["now"] = path.stat().st_mtime
    assert_classification_row(
        path, inputs, reason, early=case == "managed_before_registration",
        live_pids=[3, 9] if inputs["references"] else [],
    )


@pytest.mark.parametrize("depth", [8, 128])
def test_nested_reference_cost_does_not_construct_parent_sequences(classification_input, monkeypatch, depth):
    path, inputs = classification_input
    refs = frozenset(path.joinpath(*(["nested"] * depth), str(index)) for index in range(32))
    inputs.update(
        tasks=sweep.TaskInventory(inputs["tasks"].records, refs, True),
        references=[(9, ref) for ref in refs],
        managed={path.with_name("sibling").joinpath(*(["nested"] * depth))},
        worktrees={path.with_name("other").joinpath(*(["nested"] * depth))},
    )
    original = Path.parents
    constructions = 0

    def counted_parents(self):
        nonlocal constructions
        constructions += 1
        return original.__get__(self)

    with monkeypatch.context() as counter:
        counter.setattr(Path, "parents", property(counted_parents))
        assert sweep.task_referenced(path, refs) is True
        row = sweep.classify_path(path, **inputs)
    assert (row["decision"], row["reason"], row["live_pids"]) == ("preserve", "live_process", [9])
    assert constructions == 0


@pytest.mark.parametrize("mode", ["attributed", "scratch"])
@pytest.mark.parametrize("source", ["managed", "worktree", "task"])
@pytest.mark.parametrize("relationship", ["immediate_parent", "deep_descendant"])
def test_fresh_apply_reloads_containment_protection(inventory, monkeypatch, mode, source, relationship):
    path = inventory.make()
    kwargs = {}
    if mode == "scratch":
        (inventory.tasks / "impl-8755.json").unlink()
        kwargs["scratch"] = sweep.ScratchPolicy()
        # Fixture ctime is current; move only the sweep clock beyond both age gates.
        monkeypatch.setattr(sweep, "time", SimpleNamespace(time=lambda: path.stat().st_ctime + 3 * 86400))
    [reference] = relationship_references(path, relationship)
    calls = 0

    def changed_roots(*_args):
        nonlocal calls
        calls += 1
        # Managed roots are also read once to validate the synthetic scan root.
        initial_calls = 2 if source == "managed" else 1
        return set() if calls <= initial_calls else {reference}

    if source == "managed":
        monkeypatch.setattr(sweep, "protected_roots", changed_roots)
    elif source == "worktree":
        monkeypatch.setattr(sweep, "registered_worktrees", changed_roots)
    else:
        def changed_tasks():
            nonlocal calls
            calls += 1
            if calls == 2:
                (inventory.tasks / "running.json").write_text(json.dumps({
                    "task_id": "running", "status": "running", "cwd": str(reference),
                }))
            return [], True

        monkeypatch.setattr(sweep, "process_snapshot", changed_tasks)
    row = inventory.run(apply=True, **kwargs)["rows"][0]
    assert (row["decision"], row["reason"]) == ("preserve", "proof_changed")
    assert (path / "payload").read_bytes() == b"x" * 8192
    assert not list(inventory.root.glob(sweep.QUARANTINE_PREFIX + "*"))


@pytest.mark.parametrize("consumer", ["post_rename", "purge"])
@pytest.mark.parametrize("location", ["original", "quarantined"])
@pytest.mark.parametrize("relationship", ["immediate_parent", "deep_descendant"])
def test_shared_task_predicate_at_retention_boundaries(inventory, consumer, location, relationship):
    original = inventory.make()
    row = inventory.run()["rows"][0]
    before = sweep.tree_fingerprint(original)
    quarantined = inventory.root / "holding" / original.name
    quarantined.parent.mkdir()
    original.rename(quarantined)
    [reference] = relationship_references(original if location == "original" else quarantined, relationship)
    (inventory.tasks / "running.json").write_text(json.dumps({
        "task_id": "running", "status": "running", "cwd": str(reference),
    }))
    if consumer == "post_rename":
        reason = sweep.quarantined_problem(quarantined, original, row, before, inventory.tasks)
        assert reason == "quarantine_task_reference"
    else:
        entry = SimpleNamespace(original=original, location=quarantined)
        assert sweep.purge_problem(entry, inventory.tasks) == "purge_task_reference"
    assert (quarantined / "payload").read_bytes() == b"x" * 8192
    assert not original.exists()


@pytest.fixture
def inventory(tmp_path, tmp_path_factory, monkeypatch):
    # The pre-push gate runs pytest with a basetemp outside /tmp. The sweep
    # only accepts a real system temp, so the fixture root cannot be tmp_path.
    root = Path(tempfile.mkdtemp(prefix="impl-8755-temp-", dir="/tmp"))
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    # Never the user's real ledger (#9887).
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path_factory.mktemp("xdg-state")))
    monkeypatch.setattr(sweep, "process_snapshot", lambda: ([], True))
    monkeypatch.setattr(sweep, "registered_worktrees", lambda _: set())
    monkeypatch.setattr(sweep, "protected_roots", lambda: set())

    def make(name="impl-8755-probe", status="done", finished="2020-01-01T00:00:00Z"):
        path = root / name
        path.mkdir()
        (path / "payload").write_bytes(b"x" * 8192)
        for entry in (path / "payload", path):
            os.utime(entry, (time.time() - 86400, time.time() - 86400))
        (tasks / "impl-8755.json").write_text(
            json.dumps({"task_id": "impl-8755", "status": status, "finished_at": finished})
        )
        return path

    def run(**kwargs):
        return sweep.sweep(temp_root=root, task_root=tasks, repo_root=tmp_path, **kwargs)

    try:
        yield SimpleNamespace(root=root, tasks=tasks, make=make, run=run)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dead_task_dry_run_and_common_reap(inventory):
    path = inventory.make()
    before = path.stat()
    report = inventory.run()
    assert path.is_dir()
    assert report["mode"] == "dry-run" and report["bytes_reclaimed"] == 0
    assert report["rows"][0]["decision"] == "would_reap"
    assert report["bytes_reclaimable"] > 0
    assert report["projected_free_bytes"] == report["free_bytes"] + report["bytes_purgeable"]
    assert report["rows"][0]["identity"][:2] == [before.st_dev, before.st_ino]
    applied = inventory.run(apply=True)
    assert applied["errors"] == 0
    # Retained in quarantine (#9887): gone from its path, nothing reclaimed until the purge.
    assert applied["rows"][0]["decision"] == "quarantined" and not path.exists()
    assert applied["bytes_quarantined"] == report["bytes_reclaimable"] and applied["bytes_reclaimed"] == 0
    purged = inventory.run(apply=True, quarantine_s=1e-6)
    assert [row["decision"] for row in purged["rows"]] == ["purged"]
    assert purged["bytes_reclaimed"] == report["bytes_reclaimable"]
    assert not list(inventory.root.glob(sweep.QUARANTINE_PREFIX + "*"))


@pytest.mark.parametrize("status", ["running", "spawning", "needs_finalize", "blocked", "dry_run", None])
def test_unsettled_tasks_preserved(inventory, status):
    path = inventory.make(status=status)
    report = inventory.run(apply=True)
    assert path.exists() and report["rows"][0]["reason"] == "task_not_settled"


@pytest.mark.parametrize("finished", [None, "bad", "2039-01-01T00:00:00Z", "2020-01-01T00:00:00"])
def test_unknown_completion_preserved(inventory, finished):
    path = inventory.make(finished=finished)
    assert inventory.run(apply=True)["rows"][0]["reason"] == "task_completion_unknown"
    assert path.exists()


def test_prefix_or_issue_number_is_not_attribution(inventory):
    path = inventory.make(name="impl8755-probe")
    assert inventory.run(apply=True)["rows"][0]["reason"] == "unattributed"
    assert path.exists()
    assert sweep.task_attribution("impl-87550", {"impl-8755": {}}) == []
    assert sweep.task_attribution("impl-8755-r2-probe", {"impl-8755": {}, "impl-8755-r2": {}}) == ["impl-8755-r2"]


def test_latest_descendant_write_is_age_gate(inventory):
    path = inventory.make()
    os.utime(path / "payload", None)
    assert inventory.run(apply=True)["rows"][0]["reason"] == "too_young"
    assert path.exists()


@pytest.mark.parametrize(
    "kind",
    ["live", "unknown", "registered", "registration_unknown", "managed", "harness", "git", "mount_unknown", "mount"],
)
def test_protected_paths_never_reaped(inventory, monkeypatch, kind):
    path = inventory.make(name="claude-123" if kind == "harness" else "impl-8755-probe")
    if kind == "live":
        monkeypatch.setattr(sweep, "process_snapshot", lambda: ([(99, path / "payload")], True))
    elif kind == "unknown":
        monkeypatch.setattr(sweep, "process_snapshot", lambda: ([], False))
    elif kind.startswith("registration") or kind == "registered":
        monkeypatch.setattr(
            sweep, "registered_worktrees", lambda _: {path / "nested"} if kind == "registered" else None
        )
    elif kind == "managed":
        monkeypatch.setattr(sweep, "protected_roots", lambda: {path / "task-scratch"})
    elif kind == "git":
        (path / ".git").write_text("gitdir: elsewhere")
    elif kind == "mount_unknown":
        monkeypatch.setattr(sweep, "mount_points", lambda: None)
    elif kind == "mount":
        monkeypatch.setattr(sweep, "mount_points", lambda: frozenset({str(path)}))
    report = inventory.run(apply=True)
    assert report["rows"][0]["decision"] == "preserve" and path.exists()
    assert report["bytes_reclaimed"] == 0
    if kind == "live":
        assert report["rows"][0]["live_pids"] == [99]


def test_symlink_is_not_followed(inventory):
    target = inventory.make()
    link = inventory.root / "impl-8755-link"
    link.symlink_to(target, target_is_directory=True)
    report = inventory.run()
    row = next(row for row in report["rows"] if row["name"] == link.name)
    assert row["reason"] == "symlink_or_not_directory" and row["bytes"] is None


def test_apply_rechecks_live_process_and_task_record(inventory, monkeypatch):
    path = inventory.make()
    probes = iter([([], True), ([(10, path)], True)])
    monkeypatch.setattr(sweep, "process_snapshot", lambda: next(probes))
    assert inventory.run(apply=True)["rows"][0]["reason"] == "proof_changed"
    assert path.exists()
    calls = 0

    def change_task():
        nonlocal calls
        calls += 1
        if calls == 2:
            (inventory.tasks / "impl-8755.json").write_text(json.dumps({"task_id": "impl-8755", "status": "running"}))
        return [], True

    monkeypatch.setattr(sweep, "process_snapshot", change_task)
    assert inventory.run(apply=True)["rows"][0]["reason"] == "proof_changed"
    assert path.exists()


def test_identity_swap_rejected_by_common_reaper(inventory):
    path = inventory.make()
    old = path.stat()
    path.rename(inventory.root / "retained")
    path.mkdir()
    (path / "sentinel").write_text("keep")
    with pytest.raises(Exception, match="device/inode"):
        reap_attributed_temp(
            path,
            temp_root=inventory.root,
            repo_root=inventory.root.parent,
            expected_dev=old.st_dev,
            expected_ino=old.st_ino,
        )
    assert (path / "sentinel").exists()


def test_reaper_refuses_symlink_or_nonchild(inventory):
    path = inventory.make()
    link = inventory.root / "link"
    link.symlink_to(path)
    info = path.stat()
    for target in (link, path / "payload"):
        with pytest.raises(ValueError, match="direct child"):
            reap_attributed_temp(
                target,
                temp_root=inventory.root,
                repo_root=inventory.root.parent,
                expected_dev=info.st_dev,
                expected_ino=info.st_ino,
            )


def test_scan_error_and_reap_error_are_reported(inventory, monkeypatch):
    path = inventory.make()

    def broken(*args, **kwargs):
        raise OSError("fixture error")

    monkeypatch.setattr(sweep, "reap_attributed_temp", broken)
    assert inventory.run(apply=True)["errors"] == 0 and not path.exists()
    # The common reaper runs at purge; its failure keeps the entry and is ledgered.
    report = inventory.run(apply=True, quarantine_s=1e-6)
    assert report["errors"] == 1 and [row["reason"] for row in report["rows"]] == ["purge_refused"]
    [quarantine] = inventory.root.glob(sweep.QUARANTINE_PREFIX + "*")
    assert (quarantine / path.name / "payload").exists()
    inventory.make(name="impl-8755-again")
    monkeypatch.setattr(sweep, "tree_facts", lambda _: (0, 0, 0, "tree_unknown"))
    assert inventory.run()["rows"][0]["reason"] == "tree_unknown"


def test_task_loader_rejects_malformed_or_mismatched_records(tmp_path):
    (tmp_path / "bad.json").write_text("not json")
    (tmp_path / "wrong.json").write_text(json.dumps({"task_id": "someone-else"}))
    (tmp_path / "list.json").write_text("[]")
    inventory = sweep.load_tasks(tmp_path)
    assert set(inventory.records) == {"bad", "wrong", "list"}
    assert all(record["status"] is None for record in inventory.records.values())
    assert inventory.complete is False
    assert sweep.load_tasks(tmp_path / "absent").complete is False


def test_process_snapshot_cwd_fd_zombie_and_unknown(tmp_path):
    proc = tmp_path / "proc"
    proc.mkdir()
    live = proc / "11"
    live.mkdir()
    (live / "stat").write_text("11 (fixture) S 0")
    (live / "cwd").symlink_to(tmp_path)
    (live / "fd").mkdir()
    (live / "fd" / "4").symlink_to(tmp_path / "held")
    (live / "maps").write_text(
        f"7f00-7f01 r--s 00000000 08:01 42                     {tmp_path / 'mapped file'}\n"
        f"7f02-7f03 r--p 00000000 08:01 43                     {tmp_path / 'unlinked'} (deleted)\n"
        "7f04-7f05 rw-p 00000000 00:00 0                      [heap]\n"
        "7f06-7f07 rw-p 00000000 00:00 0\n"
    )
    zombie = proc / "12"
    zombie.mkdir()
    (zombie / "stat").write_text("12 (fixture) Z 0")
    refs, complete = sweep.process_snapshot(proc)
    assert complete and (11, tmp_path) in refs and (11, tmp_path / "held") in refs
    assert (11, tmp_path / "mapped file") in refs and (11, tmp_path / "unlinked") in refs
    assert all(ref.is_absolute() for _, ref in refs)
    unknown = proc / "13"
    unknown.mkdir()
    assert sweep.process_snapshot(proc)[1] is False
    assert sweep.process_snapshot(tmp_path / "absent") == ([], False)


def test_real_process_fd_and_cwd_are_seen(tmp_path):
    # Held by this test process: the sweep must include its own caller too.
    with (tmp_path / "held").open("w"):
        refs, _ = sweep.process_snapshot()
        assert (os.getpid(), tmp_path / "held") in refs
        assert (os.getpid(), Path.cwd()) in refs


def test_registration_probe_preserves_on_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **kw: SimpleNamespace(returncode=0, stdout=b"worktree /generic/fixture\0HEAD abc\0\0"),
    )
    assert sweep.registered_worktrees(tmp_path) == {Path("/generic/fixture")}
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=1))
    assert sweep.registered_worktrees(tmp_path) is None


def test_protected_root_includes_dispatch_and_managed_overrides(monkeypatch, tmp_path):
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(tmp_path / "managed"))
    monkeypatch.setenv("LU_RUNTIME_TMP_BASE_ROOT", str(tmp_path / "base"))
    monkeypatch.setenv("TMPDIR", str(tmp_path / "lease"))
    roots = sweep.protected_roots()
    assert {tmp_path / "managed", tmp_path / "base", tmp_path / "lease"} <= roots


@pytest.mark.parametrize("age", [0, -1, float("nan"), float("inf")])
def test_invalid_age_refused(inventory, age):
    with pytest.raises(ValueError):
        inventory.run(min_age_s=age)


def test_cli_dry_run_json_table_and_errors(inventory, capsys):
    inventory.make()
    argv = ["--temp-root", str(inventory.root), "--task-root", str(inventory.tasks)]
    assert sweep.main([*argv, "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["bytes_reclaimed"] == 0
    assert sweep.main(argv) == 0
    assert "| Entry |" in capsys.readouterr().out
    with pytest.raises(SystemExit) as exc:
        sweep.main([*argv, "--min-age-hours", "0"])
    assert exc.value.code == 2


def test_hardlinks_are_preserved_without_overstating_reclaim(inventory):
    path = inventory.make()
    os.link(path / "payload", path / "second-link")
    report = inventory.run(apply=True)
    assert path.exists() and report["rows"][0]["reason"] == "hardlinked_content"
    assert report["bytes_reclaimed"] == 0


def test_foreign_ownership_is_preserved(inventory, monkeypatch):
    path = inventory.make()
    real_uid = os.geteuid()
    monkeypatch.setattr(sweep.os, "geteuid", lambda: real_uid + 1)
    report = inventory.run(apply=True)
    assert path.exists() and report["rows"][0]["reason"] == "foreign_owner"


def test_tree_read_error_is_unknown(inventory, monkeypatch):
    path = inventory.make()
    original = Path.iterdir

    def unreadable(self):
        if self == path:
            raise PermissionError("fixture")
        return original(self)

    monkeypatch.setattr(Path, "iterdir", unreadable)
    assert sweep.tree_facts(path)[3] == "tree_unknown"


def test_common_reaper_refuses_unknown_mounts(inventory, monkeypatch):
    from scripts.common import task_scratch

    path = inventory.make()
    info = path.stat()
    monkeypatch.setattr(task_scratch, "mount_points", lambda: None)
    with pytest.raises(task_scratch.ContainmentError, match="mount information unavailable"):
        reap_attributed_temp(
            path,
            temp_root=inventory.root,
            repo_root=inventory.root.parent,
            expected_dev=info.st_dev,
            expected_ino=info.st_ino,
        )
    assert path.exists()


def test_apply_recheck_blocks_directory_replacement(inventory, monkeypatch):
    path = inventory.make()
    calls = 0

    def swap():
        nonlocal calls
        calls += 1
        if calls == 2:
            path.rename(inventory.root / "preserved-original")
            path.mkdir()
            (path / "sentinel").write_text("unrelated data")
        return [], True

    monkeypatch.setattr(sweep, "process_snapshot", swap)
    assert inventory.run(apply=True)["rows"][0]["reason"] == "proof_changed"
    assert (path / "sentinel").exists()


def test_process_snapshot_keeps_known_cwd_when_fds_unknown(tmp_path):
    entry = tmp_path / "14"
    entry.mkdir()
    (entry / "stat").write_text("14 (fixture) S 0")
    (entry / "cwd").symlink_to(tmp_path / "held")
    refs, complete = sweep.process_snapshot(tmp_path)
    assert (14, tmp_path / "held") in refs and not complete


def test_post_rename_process_probe_blocks_reap_and_restores(inventory, monkeypatch):
    path = inventory.make()
    probes = iter([([], True), ([], True)])

    def probe():
        # Third probe: after the rename, a holder shows the quarantined path.
        for result in probes:
            return result
        [quarantine] = inventory.root.glob(sweep.QUARANTINE_PREFIX + "*")
        return [(16, quarantine / path.name / "payload")], True

    monkeypatch.setattr(sweep, "process_snapshot", probe)
    report = inventory.run(apply=True)
    assert report["rows"][0]["reason"] == "quarantine_live_process" and report["rows"][0]["decision"] == "preserve"
    assert (path / "payload").exists() and not list(inventory.root.glob(sweep.QUARANTINE_PREFIX + "*"))


def test_malformed_specific_run_never_falls_back_to_finished_parent(inventory):
    path = inventory.make(name="impl-8755-r2-probe")
    (inventory.tasks / "impl-8755-r2.json").write_text("incomplete state")
    row = inventory.run(apply=True)["rows"][0]
    assert row["task"] == "impl-8755-r2" and row["reason"] == "task_not_settled"
    assert path.exists()


def test_socket_endpoint_is_preserved_even_without_fd_path_reference(inventory, monkeypatch):
    path = inventory.make()
    monkeypatch.chdir(path)
    try:
        endpoint = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    except PermissionError as error:
        pytest.skip(f"this sandbox forbids AF_UNIX socket creation: {error}")
    with endpoint:
        endpoint.bind("endpoint")
        report = inventory.run(apply=True)
        assert path.exists() and report["rows"][0]["reason"] == "special_file"
        assert report["bytes_reclaimed"] == 0
