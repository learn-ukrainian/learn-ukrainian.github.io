"""Supported owner writes, using disposable Git trees and canonical readers."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.fleet import ignored_task_output as output
from scripts.orchestration import reap_worktrees as rw
from tests.orchestration.test_worktree_output_chokepoint import boundary_tree as boundary_tree
from tests.test_continuation_worktree_reap import abandon_cohort as abandon_cohort
from tests.test_continuation_worktree_reap import same_branch_pending_cohort as same_branch_pending_cohort
from tests.test_reused_worktree_retention import cohort as cohort
from tests.test_reused_worktree_retention import save


@pytest.mark.parametrize("mode", ["file", "module"])
def test_cli_help_imports(mode, tmp_path):
    root = Path(__file__).resolve().parents[2]
    args = (
        [str(root / "scripts/fleet/terminal_abandon.py")]
        if mode == "file"
        else ["-m", "scripts.fleet.terminal_abandon"]
    )
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, *args, "--help"],
        cwd=tmp_path if mode == "file" else root,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "--preservation-bundle" in result.stdout


@pytest.fixture
def writer_fixture(abandon_cohort, monkeypatch):
    repo, tree, tasks, creator, successor, _ = abandon_cohort
    receipt = creator.pop("worktree_abandon")
    creator["initiator"] = "claude-data"
    save(tasks, creator)
    monkeypatch.setenv("LU_RUNTIME_INITIATOR", "claude-data")
    monkeypatch.setenv("LU_RUNTIME_INITIATOR_SOURCE", "session_env")
    # Hermetic: a launcher-run test session must not lend its own stream lease.
    for key in [key for key in os.environ if key.startswith("SESSION_STREAM_")]:
        monkeypatch.delenv(key)
    monkeypatch.delenv("LU_MONITOR_HOST_ID", raising=False)
    monkeypatch.setattr(rw.worktree_claims, "control_plane_root", lambda _: repo)
    monkeypatch.setattr(rw, "_has_active_ownership_claim", lambda *_: None)
    return repo, tree, tasks, creator, successor, repo / receipt["preservation"]["path"], receipt["head_sha"]


def invoke(fixture, **overrides):
    from scripts.fleet import terminal_abandon

    _, _, _, creator, _, bundle, head = fixture
    values = dict(task_id=creator["task_id"], head_sha=head, reason="superseded implementation", bundle=bundle)
    values.update(overrides)
    return terminal_abandon.main(
        [
            "--task-id",
            values["task_id"],
            "--head",
            values["head_sha"],
            "--reason",
            values["reason"],
            "--preservation-bundle",
            str(values["bundle"]),
        ]
    )


def test_written_record_passes_both_existing_readers(writer_fixture, capsys):
    repo, tree, tasks, creator, _, _, head = writer_fixture
    assert invoke(writer_fixture) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["outcome"] == "recorded" and result["head_sha"] == head
    matches = output.matching_worktree_records(tree, tasks, repo_root=repo, publish_cache=False)
    path, record = output.terminal_abandon_creator(matches, tree, primary=repo, tasks_dir=tasks)
    assert path == tasks / "boundary.json"
    assert record == dict(creator, worktree_abandon=record["worktree_abandon"])
    assert record["worktree_abandon"]["schema"] == "terminal-abandon.v1"
    assert rw._terminal_abandon_matches(repo, tree) == matches
    preservation = record["worktree_abandon"]["preservation"]
    manifest_bytes = (repo / preservation["path"]).read_bytes()
    assert hashlib.sha256(manifest_bytes).hexdigest() == preservation["sha256"]
    assert json.loads(manifest_bytes)["schema"] == "terminal-abandon-preservation.v1"


@pytest.mark.parametrize(
    "failure,code",
    [
        ("bundle_hash", "PRESERVATION_INVALID"),
        ("caller", "NOT_CREATOR"),
        ("unknown_caller", "NOT_CREATOR"),
        ("head", "HEAD_MISMATCH"),
        ("no_creator", "CREATOR_RECOVERY_REQUIRED"),
        ("no_record", "CREATOR_RECOVERY_REQUIRED"),
        ("running", "LIVE_OR_WANTED"),
        ("keep", "LIVE_OR_WANTED"),
        ("pid", "LIVE_OR_WANTED"),
        ("lease", "LIVE_OR_WANTED"),
        ("active", "LIVE_OR_WANTED"),
        ("monitor_unknown", "ACTIVITY_UNKNOWN"),
        ("cwd", "LIVE_OR_WANTED"),
        ("cwd_unknown", "ACTIVITY_UNKNOWN"),
        ("rollover", "LIVE_OR_WANTED"),
        ("patch_changed", "PRESERVATION_INVALID"),
        ("open_pr", "LIVE_OR_WANTED"),
        ("pr_unknown", "ACTIVITY_UNKNOWN"),
        ("blank_reason", "INVALID_INPUT"),
        ("short_head", "INVALID_INPUT"),
        ("path_task_id", "INVALID_INPUT"),
        ("missing_bundle", "INVALID_INPUT"),
        ("symlink_bundle", "INVALID_INPUT"),
        ("fifo_bundle", "INVALID_INPUT"),
        ("task_lock_symlink", "INVALID_INPUT"),
        ("bundle_not_object", "PRESERVATION_INVALID"),
        ("bundle_in_tasks", "INVALID_INPUT"),
        ("unmerged_index", "PRESERVATION_INVALID"),
        ("index_lock", "PRESERVATION_INVALID"),
        ("no_initiator", "NOT_CREATOR"),
        ("no_nonce", "PRESERVATION_INVALID"),
        ("manifest_collision", "PRESERVATION_INVALID"),
    ],
)
def test_refusal_writes_no_record_or_manifest(writer_fixture, monkeypatch, capsys, failure, code):
    repo, tree, tasks, creator, successor, bundle, _ = writer_fixture
    overrides = {}
    if failure == "bundle_hash":
        manifest = json.loads(bundle.read_bytes())
        (repo / manifest["head_patch"]["path"]).write_bytes(b"corrupt patch")
    elif failure == "caller":
        monkeypatch.setenv("LU_RUNTIME_INITIATOR", "claude-harness")
    elif failure == "unknown_caller":
        monkeypatch.setenv("LU_RUNTIME_INITIATOR", "unknown")
    elif failure == "head":
        overrides["head_sha"] = "0" * 40
    elif failure == "no_record":
        (tasks / "boundary.json").unlink()
    elif failure == "no_creator":
        creator.pop("ignored_output_baseline")
        save(tasks, creator)
    elif failure in {"running", "keep", "pid", "lease"}:
        successor.update(
            {
                "running": {"status": "running"},
                "keep": {"keep_worktree": True},
                "pid": {"pid": os.getpid()},
                "lease": {"lease_state": "active"},
            }[failure]
        )
        save(tasks, successor)
    elif failure == "active":
        monkeypatch.setattr(rw, "_active_task_ids", lambda: {successor["task_id"]})
    elif failure == "monitor_unknown":
        monkeypatch.setattr(rw, "_active_task_ids", lambda: None)
    elif failure == "cwd":
        monkeypatch.setattr(rw, "_live_cwd_paths", lambda _: {tree / "ignored"})
    elif failure == "cwd_unknown":
        monkeypatch.setattr(rw, "_live_cwd_paths", lambda _: None)
    elif failure == "rollover":
        monkeypatch.setattr(rw, "_has_active_rollover_lease", lambda *_: "active rollover")
    elif failure == "patch_changed":
        (tree / "README.md").write_bytes(b"new work since preservation")
    elif failure == "open_pr":
        monkeypatch.setattr(rw, "_query_pr_states", lambda *_: ([rw.PullRequestState(1, "OPEN", "0" * 40)], None))
    elif failure == "pr_unknown":
        monkeypatch.setattr(rw, "_query_pr_states", lambda *_: ([], "unavailable"))
    elif failure == "blank_reason":
        overrides["reason"] = " "
    elif failure == "short_head":
        overrides["head_sha"] = "abc"
    elif failure == "path_task_id":
        overrides["task_id"] = "../boundary"
    elif failure == "missing_bundle":
        overrides["bundle"] = bundle.with_name("missing.json")
    elif failure in {"symlink_bundle", "fifo_bundle"}:
        bad = bundle.with_name("bad-bundle")
        if failure == "symlink_bundle":
            bad.symlink_to(bundle)
        else:
            os.mkfifo(bad)
        overrides["bundle"] = bad
    elif failure == "task_lock_symlink":
        (tasks / "boundary.json.lock").symlink_to(bundle)
    elif failure == "bundle_not_object":
        bundle.write_text("[]")
    elif failure == "bundle_in_tasks":
        bad = tasks / "bundle.json"
        bad.write_bytes(bundle.read_bytes())
        overrides["bundle"] = bad
    elif failure == "unmerged_index":
        monkeypatch.setattr(output.artifacts, "_git_paths", lambda *_: ["unmerged"])
    elif failure == "index_lock":
        from tests.orchestration.test_worktree_claims_cli import _git

        index_lock = _git(tree, "rev-parse", "--path-format=absolute", "--git-path", "index.lock")
        from pathlib import Path

        Path(index_lock).write_bytes(b"")
    elif failure == "no_initiator":
        creator.pop("initiator")
        save(tasks, creator)
    elif failure == "no_nonce":
        creator.pop("run_nonce")
        save(tasks, creator)
    elif failure == "manifest_collision":
        manifest = json.loads(bundle.read_bytes())
        encoded = (json.dumps(manifest, sort_keys=True) + "\n").encode()
        digest = hashlib.sha256(encoded).hexdigest()
        bundle.with_name(f"terminal-abandon-boundary-{digest}.json").write_bytes(b"collision")
    before = {p: p.read_bytes() for p in (repo / "batch_state").rglob("*.json")}
    assert invoke(writer_fixture, **overrides) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["outcome"] == "refused" and result["code"] == code
    if failure in {"no_creator", "no_record"}:
        assert "recover authentic dispatch creator" in result["reason"]
    assert {p: p.read_bytes() for p in (repo / "batch_state").rglob("*.json")} == before
    assert tree.exists()


def test_repeat_is_idempotent(writer_fixture, capsys):
    repo, *_ = writer_fixture
    assert invoke(writer_fixture) == 0
    capsys.readouterr()
    before = {p: p.read_bytes() for p in (repo / "batch_state").rglob("*.json")}
    assert invoke(writer_fixture) == 0
    assert json.loads(capsys.readouterr().out)["outcome"] == "already_recorded"
    assert {p: p.read_bytes() for p in (repo / "batch_state").rglob("*.json")} == before


def test_existing_record_cannot_be_overwritten(writer_fixture, capsys):
    repo, *_ = writer_fixture
    assert invoke(writer_fixture) == 0
    capsys.readouterr()
    before = {p: p.read_bytes() for p in (repo / "batch_state").rglob("*.json")}
    assert invoke(writer_fixture, reason="different disposition") == 2
    assert json.loads(capsys.readouterr().out)["code"] == "ALREADY_RECORDED"
    assert {p: p.read_bytes() for p in (repo / "batch_state").rglob("*.json")} == before


def test_patch_mutation_during_final_activity_probe_refuses(writer_fixture, monkeypatch, capsys):
    repo, tree, tasks, *_ = writer_fixture
    calls = 0

    def active():
        nonlocal calls
        calls += 1
        if calls == 2:
            (tree / "README.md").write_bytes(b"arrived during activity probe")
        return set()

    monkeypatch.setattr(rw, "_active_task_ids", active)
    before = {p: p.read_bytes() for p in (repo / "batch_state").rglob("*.json")}
    assert invoke(writer_fixture) == 2
    assert json.loads(capsys.readouterr().out)["code"] == "PRESERVATION_INVALID"
    assert {p: p.read_bytes() for p in (repo / "batch_state").rglob("*.json")} == before
    assert not list((repo / "batch_state/abandon/boundary").glob(".terminal-abandon-*"))
    assert "worktree_abandon" not in json.loads((tasks / "boundary.json").read_bytes())


def test_bundle_can_contain_only_patch_metadata(writer_fixture, capsys):
    *_, bundle, _ = writer_fixture
    manifest = json.loads(bundle.read_bytes())
    bundle.write_text(
        json.dumps({key: manifest[key] for key in ("base_sha", "head_patch", "index_patch", "working_patch")})
    )
    assert invoke(writer_fixture) == 0
    assert json.loads(capsys.readouterr().out)["outcome"] == "recorded"


# --- Lane succession (#10617): current stream custody, never alias membership ---


def _anchor(key):
    """The launcher's canonical stream id: ``epic:`` plus the stream's first registered epic."""
    import yaml

    registry = Path(__file__).resolve().parents[2] / "scripts/config/issue_streams.yaml"
    return f"epic:{yaml.safe_load(registry.read_text())['streams'][key]['epics'][0]}"


MONITOR = _anchor("monitor")
INFRA = _anchor("infra-harness")
OPEN_MODEL_DATA = _anchor("open-model-data")

_LEASE_ENV = {
    "ID": MONITOR,
    "SESSION_ID": "session-current",
    "LEASE_ID": "lease-current",
    "GENERATION": "4",
    "FENCING_TOKEN": "17",
    "AGENT": "muse",
    "HARNESS": "muse-cli",
    "INSTANCE_ID": "muse-monitor-1",
    "HOLDER_KIND": "process",
    "PROCESS_ID": "4242",
}


def _set_lease_env(monkeypatch, **overrides):
    for key, value in dict(_LEASE_ENV, **overrides).items():
        monkeypatch.setenv(f"SESSION_STREAM_{key}", value)


@pytest.fixture
def succession(writer_fixture, monkeypatch):
    """A retired monitor seat's tree; the current Muse monitor driver holds custody."""
    from agents_extensions.shared.session_streams.hooks import lease_from_environment
    from scripts.session_supervisor import remote

    _, tree, tasks, creator, _, _, _ = writer_fixture
    creator["initiator"] = "claude-monitor"
    save(tasks, creator)
    monkeypatch.setenv("LU_RUNTIME_INITIATOR", "muse-monitor")
    _set_lease_env(monkeypatch)
    (tree / "untracked.txt").write_bytes(b"untracked unique bytes")
    current = dict(
        remote.RemoteEpicClient._lease_payload(lease_from_environment()),
        state="active",
        session_state="open",
        expires_at="2999-01-01T00:00:00Z",
    )
    monitor = {"streams": {MONITOR: current}, "calls": 0, "on_call": None, "error": None}

    def stream(self, stream_id, *, digest_limit=20):
        monitor["calls"] += 1
        if monitor["on_call"] is not None:
            monitor["on_call"](monitor["calls"])
        if monitor["error"] is not None:
            raise monitor["error"]
        return {"stream_id": stream_id, "lease": json.loads(json.dumps(monitor["streams"].get(stream_id)))}

    monkeypatch.setattr(remote.RemoteEpicClient, "stream", stream)
    return writer_fixture, monitor


def _files(repo):
    return {p: p.read_bytes() for p in (repo / "batch_state").rglob("*") if p.is_file() and p.suffix != ".lock"}


def _preserved_files(repo):
    return [p for p in (repo / "batch_state/preserved").rglob("*") if p.is_file()]


def _recorded(fixture):
    repo, tree, tasks, *_ = fixture
    matches = output.matching_worktree_records(tree, tasks, repo_root=repo, publish_cache=False)
    _, record = output.terminal_abandon_creator(matches, tree, primary=repo, tasks_dir=tasks)
    receipt = record["worktree_abandon"]
    manifest = json.loads((repo / receipt["preservation"]["path"]).read_bytes())
    return record, receipt, manifest


def test_same_stream_successor_records_bound_succession_receipt(succession, capsys):
    fixture, monitor = succession
    repo, tree, _, _, _, _, head = fixture
    assert invoke(fixture) == 0
    assert json.loads(capsys.readouterr().out)["outcome"] == "recorded"
    assert monitor["calls"] == 2  # admission, then again immediately before publication
    record, receipt, manifest = _recorded(fixture)
    # The creator's identity and nonce are kept; succession is appended, not substituted.
    assert record["initiator"] == "claude-monitor"
    assert receipt["owner"] == "boundary" and receipt["run_nonce"] == "creation-nonce"
    assert manifest["owner"] == "boundary" and manifest["run_nonce"] == "creation-nonce"
    assert receipt["succession"] == {
        "schema": "terminal-abandon-succession.v1",
        "task_id": "boundary",
        "creator_initiator": "claude-monitor",
        "caller_initiator": "muse-monitor",
        "stream_id": MONITOR,
        "mapping_sha256": hashlib.sha256(output.SUCCESSION_MAP.read_bytes()).hexdigest(),
        "authority": {
            "stream_id": MONITOR,
            "session_id": "session-current",
            "lease_id": "lease-current",
            "generation": 4,
            "fencing_token": 17,
            "holder": {"agent": "muse", "harness": "muse-cli", "instance_id": "muse-monitor-1"},
        },
        "tree": tree.relative_to(repo).as_posix(),
        "branch": "codex/boundary",
        "head_sha": head,
        "preservation_sha256": receipt["preservation"]["sha256"],
    }
    located = manifest["output"]
    assert output.verify_retrieval(repo, located) == located["content_sha256"]
    copy = repo / located["location"]
    assert (copy / "ignored/output.txt").read_bytes() == b"current output"
    assert (copy / "untracked.txt").read_bytes() == b"untracked unique bytes"


def test_successor_retry_is_idempotent(succession, capsys):
    fixture, _ = succession
    repo, *_ = fixture
    assert invoke(fixture) == 0
    capsys.readouterr()
    before = _files(repo)
    assert invoke(fixture) == 0
    assert json.loads(capsys.readouterr().out)["outcome"] == "already_recorded"
    assert _files(repo) == before


def test_successor_preservation_restores_and_reaper_removes(succession, tmp_path, capsys):
    fixture, _ = succession
    repo, tree, _, _, _, _, head = fixture
    assert invoke(fixture) == 0
    capsys.readouterr()
    _, receipt, manifest = _recorded(fixture)
    environment = dict(os.environ, GIT_INDEX_FILE=str(tmp_path / "restore.index"))
    subprocess.run(["git", "read-tree", manifest["base_sha"]], cwd=repo, env=environment, check=True, timeout=30)
    subprocess.run(
        ["git", "apply", "--cached", str(repo / manifest["head_patch"]["path"])],
        cwd=repo,
        env=environment,
        check=True,
        timeout=30,
    )
    restored = subprocess.run(
        ["git", "write-tree"], cwd=repo, env=environment, check=True, capture_output=True, text=True, timeout=30
    ).stdout.strip()
    tree_of_head = subprocess.run(
        ["git", "rev-parse", f"{head}^{{tree}}"], cwd=repo, check=True, capture_output=True, text=True, timeout=30
    ).stdout.strip()
    assert restored == tree_of_head
    row = next(
        r
        for r in rw.reap_worktrees(
            repo_root=repo, apply=True, live_cwds=set(), preserve_then_reap=True, merged_pr_only=False
        )
        if r.path == str(tree)
    )
    assert row.action == "preserved_then_removed", row
    assert not tree.exists()
    # The removal gate reused the successor's verified copy, which outlives the tree.
    assert row.preserved_artifacts["location"] == manifest["output"]["location"]
    assert row.preserved_artifacts["abandon_proof"]["succession"] == receipt["succession"]
    copy = repo / manifest["output"]["location"]
    assert output.verify_retrieval(repo, manifest["output"]) == manifest["output"]["content_sha256"]
    assert (copy / "ignored/output.txt").read_bytes() == b"current output"
    assert (copy / "untracked.txt").read_bytes() == b"untracked unique bytes"


def _defect(failure, fixture, monitor, monkeypatch, tmp_path):
    """Apply one defect and return its exact repair; the repaired run must succeed."""
    _, _, tasks, creator, successor, _, _ = fixture
    lease = monitor["streams"][MONITOR]
    if failure == "alias_only":
        # Listed in the map for the same stream, but holds no launcher custody.
        for key in _LEASE_ENV:
            monkeypatch.delenv(f"SESSION_STREAM_{key}")
        return lambda: _set_lease_env(monkeypatch)
    if failure == "unknown_caller":
        monkeypatch.setenv("LU_RUNTIME_INITIATOR", "unknown")
        return lambda: monkeypatch.setenv("LU_RUNTIME_INITIATOR", "muse-monitor")
    if failure == "cross_stream":
        _set_lease_env(monkeypatch, ID=INFRA)
        monitor["streams"][INFRA] = dict(lease, stream_id=INFRA)
        return lambda: _set_lease_env(monkeypatch)
    if failure in {"stale_fence", "stale_generation", "other_session", "released", "expired", "closed_session"}:
        field, value = {
            "stale_fence": ("fencing_token", 18),
            "stale_generation": ("generation", 5),
            "other_session": ("session_id", "session-newer"),
            "released": ("state", "released"),
            "expired": ("expires_at", "2000-01-01T00:00:00Z"),
            "closed_session": ("session_state", "closed"),
        }[failure]
        original = lease[field]
        lease[field] = value
        return lambda: lease.__setitem__(field, original)
    if failure == "unleased":
        monitor["streams"][MONITOR] = None
        return lambda: monitor["streams"].__setitem__(MONITOR, lease)
    if failure == "authority_unknown":
        from scripts.session_supervisor.remote import RemoteUnreachableError

        monitor["error"] = RemoteUnreachableError("unreachable")
        return lambda: monitor.__setitem__("error", None)
    if failure == "unmapped_suffix":
        # Same "-monitor" suffix, never listed: no suffix inference.
        creator["initiator"] = "kimi-monitor"
        save(tasks, creator)

        def repair():
            creator["initiator"] = "claude-monitor"
            save(tasks, creator)

        return repair
    if failure == "invalid_map":
        bad = tmp_path / "map.yaml"
        bad.write_bytes(output.SUCCESSION_MAP.read_bytes() + b'  "epic:9999":\n    initiators: [claude-monitor]\n')
        monkeypatch.setattr(output, "SUCCESSION_MAP", bad)
        real = Path(output.__file__).resolve().parents[2] / "scripts/config/terminal_abandon_succession.yaml"
        return lambda: monkeypatch.setattr(output, "SUCCESSION_MAP", real)
    if failure == "ambiguous_creator":
        successor["worktree_reused"] = False
        save(tasks, successor)

        def repair():
            successor["worktree_reused"] = True
            save(tasks, successor)

        return repair
    if failure == "activity_unknown":
        monkeypatch.setattr(rw, "_active_task_ids", lambda: None)
        return lambda: monkeypatch.setattr(rw, "_active_task_ids", set)
    if failure == "pid_alive":
        successor["pid"] = os.getpid()
        save(tasks, successor)

        def repair():
            successor["pid"] = 999_999_999
            save(tasks, successor)

        return repair
    raise AssertionError(failure)


@pytest.mark.parametrize(
    "failure,code,reason",
    [
        ("alias_only", "NOT_CREATOR", "stream custody"),
        ("unknown_caller", "NOT_CREATOR", "creator-of-record"),
        ("cross_stream", "CROSS_STREAM", "canonical stream"),
        ("stale_fence", "STALE_AUTHORITY", "current active custody"),
        ("stale_generation", "STALE_AUTHORITY", "current active custody"),
        ("other_session", "STALE_AUTHORITY", "current active custody"),
        ("released", "STALE_AUTHORITY", "current active custody"),
        ("closed_session", "STALE_AUTHORITY", "current active custody"),
        ("unleased", "STALE_AUTHORITY", "current active custody"),
        ("expired", "STALE_AUTHORITY", "expired"),
        ("authority_unknown", "AUTHORITY_UNKNOWN", "probe unavailable"),
        ("unmapped_suffix", "STREAM_UNMAPPED", "no reviewed stream mapping"),
        ("invalid_map", "STREAM_UNMAPPED", "map unavailable or invalid"),
        ("ambiguous_creator", "CREATOR_RECOVERY_REQUIRED", "recover authentic dispatch creator"),
        ("activity_unknown", "ACTIVITY_UNKNOWN", "probe unavailable"),
        ("pid_alive", "LIVE_OR_WANTED", "PID"),
    ],
)
def test_successor_rejection_is_caused_by_the_defect_alone(
    succession, monkeypatch, tmp_path, capsys, failure, code, reason
):
    fixture, monitor = succession
    repo, tree, *_ = fixture
    repair = _defect(failure, fixture, monitor, monkeypatch, tmp_path)
    before = _files(repo)
    assert invoke(fixture) == 2
    result = json.loads(capsys.readouterr().out)
    assert (result["outcome"], result["code"]) == ("refused", code), result
    assert reason in result["reason"]
    assert _files(repo) == before and not _preserved_files(repo) and tree.exists()
    # Paired control: repairing only this defect lets the same successor record.
    repair()
    assert invoke(fixture) == 0
    assert json.loads(capsys.readouterr().out)["outcome"] == "recorded"


@pytest.mark.parametrize("change", ["custody", "map", "output", "head_patch"])
def test_successor_inputs_changed_between_check_and_publish_refuse(succession, monkeypatch, tmp_path, capsys, change):
    fixture, monitor = succession
    repo, tree, *_ = fixture
    lease = monitor["streams"][MONITOR]
    if change == "custody":
        # Another launch took the stream after admission.
        monitor["on_call"] = lambda calls: calls == 2 and lease.update(fencing_token=18, session_id="session-newer")
        expected = "STALE_AUTHORITY"
    elif change == "map":
        copy = tmp_path / "map.yaml"
        copy.write_bytes(output.SUCCESSION_MAP.read_bytes())
        monkeypatch.setattr(output, "SUCCESSION_MAP", copy)
        monitor["on_call"] = lambda calls: calls == 2 and copy.write_bytes(copy.read_bytes() + b"# edited\n")
        expected = "STATE_CHANGED"
    else:
        calls = 0

        def active():
            nonlocal calls
            calls += 1
            if calls == 2:
                if change == "output":
                    (tree / "ignored/output.txt").write_bytes(b"output arrived during activity probe")
                else:
                    (tree / "README.md").write_bytes(b"tracked change during activity probe")
            return set()

        monkeypatch.setattr(rw, "_active_task_ids", active)
        expected = "PRESERVATION_INVALID"
    before = _files(repo)
    assert invoke(fixture) == 2
    assert json.loads(capsys.readouterr().out)["code"] == expected
    assert _files(repo) == before and not _preserved_files(repo)
    assert not list((repo / "batch_state/abandon/boundary").glob(".terminal-abandon-*"))
    assert "worktree_abandon" not in json.loads((fixture[2] / "boundary.json").read_bytes())


@pytest.mark.parametrize("drift", ["map_entry", "output_copy", "branch", "tree", "preservation_digest"])
def test_successor_record_is_revalidated_at_removal(succession, monkeypatch, tmp_path, capsys, drift):
    fixture, _ = succession
    repo, tree, tasks, *_ = fixture
    assert invoke(fixture) == 0
    capsys.readouterr()
    record, receipt, manifest = _recorded(fixture)
    if drift == "map_entry":
        changed = tmp_path / "map.yaml"
        changed.write_text(output.SUCCESSION_MAP.read_text().replace("      - claude-monitor   # retired\n", ""))
        monkeypatch.setattr(output, "SUCCESSION_MAP", changed)
    elif drift == "output_copy":
        (repo / manifest["output"]["location"] / "untracked.txt").write_bytes(b"tampered copy")
    else:
        field, value = {
            "branch": ("branch", "codex/other"),
            "tree": ("tree", ".worktrees/dispatch/codex/other"),
            "preservation_digest": ("preservation_sha256", "0" * 64),
        }[drift]
        receipt["succession"][field] = value
        save(tasks, record)
    matches = output.matching_worktree_records(tree, tasks, repo_root=repo, publish_cache=False)
    with pytest.raises(ValueError, match="succession"):
        output.terminal_abandon_creator(matches, tree, primary=repo, tasks_dir=tasks)
    row = next(
        r
        for r in rw.reap_worktrees(
            repo_root=repo, apply=True, live_cwds=set(), preserve_then_reap=True, merged_pr_only=False
        )
        if r.path == str(tree)
    )
    assert row.action not in {"removed", "preserved_then_removed"}, row
    assert tree.exists()


def test_creator_path_never_consults_custody_or_copies_output(writer_fixture, monkeypatch, capsys):
    from scripts.session_supervisor import remote

    def forbidden(*_args, **_kwargs):
        raise AssertionError("creator path must not use succession machinery")

    monkeypatch.setattr(remote.RemoteEpicClient, "stream", forbidden)
    monkeypatch.setattr(output, "capture_abandon_output", forbidden)
    _set_lease_env(monkeypatch)  # A creator that also holds custody still takes the creator path.
    assert invoke(writer_fixture) == 0
    assert json.loads(capsys.readouterr().out)["outcome"] == "recorded"
    _, receipt, manifest = _recorded(writer_fixture)
    assert "succession" not in receipt and "output" not in manifest


def test_reviewed_map_is_exact_and_launcher_canonical():
    import yaml

    mapping, digest = output.succession_streams()
    assert digest == hashlib.sha256(output.SUCCESSION_MAP.read_bytes()).hexdigest()
    assert mapping["claude-monitor"] == mapping["muse-monitor"] == MONITOR
    assert mapping["gemini-open-model-data"] == OPEN_MODEL_DATA
    assert mapping["claude-infra"] == INFRA
    for omitted in ("claude-corpus", "claude-core", "claude", "monitor", "kimi-monitor"):
        assert omitted not in mapping
    root = Path(output.__file__).resolve().parents[2]
    streams = yaml.safe_load((root / "scripts/config/issue_streams.yaml").read_text())["streams"]
    anchors = {f"epic:{entry['epics'][0]}" for entry in streams.values()}
    assert set(mapping.values()) <= anchors


@pytest.mark.parametrize(
    "text",
    [
        'schema: terminal-abandon-succession-map.v1\nstreams:\n  "epic:1":\n    initiators: [a-x]\n'
        '  "epic:2":\n    initiators: [a-x]\n',
        'schema: terminal-abandon-succession-map.v1\nstreams:\n  "epic:1":\n    initiators: [a-x]\n'
        '  "epic:1":\n    initiators: [b-x]\n',
        'schema: terminal-abandon-succession-map.v1\nstreams:\n  "monitor":\n    initiators: [a-x]\n',
        'schema: terminal-abandon-succession-map.v1\nstreams:\n  "epic:1":\n    initiators: ["*-x"]\n',
        "schema: other.v1\nstreams: {}\n",
        "streams: {}\n",
        "- not a mapping\n",
    ],
    ids=[
        "initiator-in-two-streams",
        "duplicate-stream",
        "non-canonical-stream",
        "pattern",
        "schema",
        "no-schema",
        "list",
    ],
)
def test_invalid_map_refuses_whole_map(tmp_path, text):
    path = tmp_path / "map.yaml"
    path.write_text(text)
    with pytest.raises(ValueError):
        output.succession_streams(path)
