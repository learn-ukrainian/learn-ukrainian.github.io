"""Cross-host rollover bundle round-trip and ordering contracts."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from agents_extensions.shared.session_streams.store import ContentRejectedError, validate_entry_body
from scripts.orchestration import thread_handoff as th

HANDOFF_PATH = ".claude/infra-epic/CLAUDE-DRIVER-HANDOFF.md"
AGENT = "claude-infra"
STREAM = "epic:9999"


def _seed_state(
    root: Path,
    *,
    thread_id: str,
    agent: str = AGENT,
    generation: int = 3,
    rollover_id: str | None = None,
    prepared_at: str = "2026-08-24T16:00:00Z",
    harness: str = "claude-code",
) -> dict:
    lineage_id = th.lineage_id_for(agent, thread_id)
    state = th.prepare_state(
        {
            "schema_version": th.SCHEMA_VERSION,
            "lineage_id": lineage_id,
            "active": {
                "thread_id": thread_id,
                "generation": generation - 1,
                "lineage_id": lineage_id,
                "started_at": prepared_at,
            },
        },
        agent=agent,
        now=datetime(2026, 8, 24, 16, 0, tzinfo=UTC),
        active_thread_id=thread_id,
        active_automation_id="old-auto",
        context_percent=80.0,
        force_new_replacement=False,
        harness=harness,
    )
    replacement = state["replacement"]
    del rollover_id
    assert replacement["generation"] == generation
    replacement["prepared_at"] = prepared_at
    replacement["source_checkout"] = {"full_head": "a" * 40, "clean": True}
    state_path = root / th.default_state_path(agent, state["lineage_id"])
    th.write_rollover_state(state_path, root, state)
    bootstrap = root / replacement["bootstrap_prompt_path"]
    handoff = root / replacement["handoff_path"]
    bootstrap.parent.mkdir(parents=True, exist_ok=True)
    bootstrap.write_text(
        f"source checkout: {root}\nThe credential-assignment rule is prose here.\n",
        encoding="utf-8",
    )
    handoff.write_text(f"handoff source checkout: {root}\n", encoding="utf-8")
    lane_handoff = root / HANDOFF_PATH
    lane_handoff.parent.mkdir(parents=True, exist_ok=True)
    lane_handoff.write_text(f"lane handoff source checkout: {root}\n", encoding="utf-8")
    return state


def _export_args(
    root: Path,
    state: dict,
    output: Path,
    *,
    upload: bool = False,
    stream: str = STREAM,
) -> SimpleNamespace:
    return SimpleNamespace(
        repo_root=root,
        agent=state["agent"],
        lineage_id=state["lineage_id"],
        rollover_id=None,
        stream=stream,
        file=output,
        upload=upload,
        monitor_base_url="http://127.0.0.1:1",
    )


def _mark_confirmed(root: Path, state: dict) -> None:
    replacement = state["replacement"]
    replacement.update(
        {
            "status": "started",
            "thread_id": "confirmed-replacement",
            "resumed_thread_id": "confirmed-replacement",
            "confirmed_at": "2026-08-24T17:00:00Z",
        }
    )
    th.write_json_atomic(root / th.default_state_path(AGENT, state["lineage_id"]), state)


def _import_args(
    root: Path,
    bundle: Path | None,
    *,
    agent: str = AGENT,
    force: bool = False,
    from_api: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        repo_root=root,
        agent=agent,
        file=bundle,
        from_api=from_api,
        stream=STREAM,
        force=force,
        monitor_base_url="http://127.0.0.1:1",
    )


@pytest.fixture
def handoff_candidates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(th, "_bundle_handoff_candidates", lambda _root, _stream: (HANDOFF_PATH,))


def test_round_trip_rewrites_root_and_identical_import_is_noop(
    tmp_path: Path,
    handoff_candidates: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    state = _seed_state(source, thread_id="source-thread")
    bundle = tmp_path / "rollover.tgz"

    assert th.cmd_export_bundle(_export_args(source, state, bundle)) == 0
    export_output = capsys.readouterr()
    assert "secret scan" not in export_output.err
    assert bundle.is_file()
    assert th.cmd_import_bundle(_import_args(target, bundle)) == 0
    first_import = json.loads(capsys.readouterr().out)
    assert first_import["status"] == "installed"

    imported_bootstrap = target / state["replacement"]["bootstrap_prompt_path"]
    imported_text = imported_bootstrap.read_text(encoding="utf-8")
    assert str(target) in imported_text
    assert str(source) not in imported_text
    assert (target / HANDOFF_PATH).is_file()

    assert th.cmd_import_bundle(_import_args(target, bundle)) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "noop"


def test_export_digest_is_stable_across_export_clock_and_changes_with_status(
    tmp_path: Path,
    handoff_candidates: None,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    state = _seed_state(source, thread_id="source-thread")
    first_path = tmp_path / "first.tgz"
    second_path = tmp_path / "second.tgz"

    export_times = iter(
        (
            datetime(2026, 8, 24, 18, 0, tzinfo=UTC),
            datetime(2026, 8, 24, 18, 1, tzinfo=UTC),
        )
    )
    monkeypatch.setattr(th, "utc_now", lambda: next(export_times))
    assert th.cmd_export_bundle(_export_args(source, state, first_path)) == 0
    first_output = json.loads(capsys.readouterr().out)
    assert th.cmd_export_bundle(_export_args(source, state, second_path)) == 0
    second_output = json.loads(capsys.readouterr().out)

    first_manifest, _ = th._bundle_extract(first_path.read_bytes())
    second_manifest, _ = th._bundle_extract(second_path.read_bytes())
    assert first_manifest["exported_at"] != second_manifest["exported_at"]
    assert first_output["bundle_sha256"] == second_output["bundle_sha256"]
    assert first_manifest["bundle_sha256"] == second_manifest["bundle_sha256"]
    assert [item["sha256"] for item in first_manifest["files"]] == [
        item["sha256"] for item in second_manifest["files"]
    ]

    monkeypatch.setattr(th, "utc_now", lambda: datetime(2026, 8, 24, 18, 2, tzinfo=UTC))
    _mark_confirmed(source, state)
    confirmed_path = tmp_path / "confirmed.tgz"
    assert th.cmd_export_bundle(_export_args(source, state, confirmed_path)) == 0
    confirmed_output = json.loads(capsys.readouterr().out)
    assert confirmed_output["bundle_sha256"] != first_output["bundle_sha256"]


def test_confirmed_local_copy_refuses_older_pending_remote_at_rank_level(
    tmp_path: Path,
    handoff_candidates: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    remote = _seed_state(source, thread_id="source-thread", generation=3)
    bundle = tmp_path / "pending.tgz"
    assert th.cmd_export_bundle(_export_args(source, remote, bundle)) == 0
    capsys.readouterr()

    local = _seed_state(target, thread_id="source-thread", generation=3)
    _mark_confirmed(target, local)
    local_lease = target / th.default_state_path(AGENT, local["lineage_id"])
    before = local_lease.read_bytes()

    assert th.cmd_import_bundle(_import_args(target, bundle)) == 2
    refused = json.loads(capsys.readouterr().out)
    assert refused["status"] == "refused"
    assert refused["local"]["status_rank"] > refused["remote"]["status_rank"]
    assert local_lease.read_bytes() == before
    archive_root = target / ".agent" / "thread-rollovers" / AGENT / "_archive"
    assert not archive_root.exists() or not any(archive_root.iterdir())


def test_inconsistent_local_lease_refuses_without_archive_or_lineage_mutation(
    tmp_path: Path,
    handoff_candidates: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    remote = _seed_state(source, thread_id="source-thread", generation=4)
    bundle = tmp_path / "remote.tgz"
    assert th.cmd_export_bundle(_export_args(source, remote, bundle)) == 0
    capsys.readouterr()

    local = _seed_state(target, thread_id="source-thread", generation=3)
    local_path = target / th.default_state_path(AGENT, local["lineage_id"])
    broken = json.loads(local_path.read_bytes())
    broken["rollover_id"] = "rollover-inconsistent"
    th.write_json_atomic(local_path, broken)
    broken_before_import = local_path.read_bytes()

    assert th.cmd_import_bundle(_import_args(target, bundle)) == 2
    output = capsys.readouterr()
    reason = json.loads(output.out)
    assert reason["action"] == "import-bundle"
    assert "local rollover lease is invalid" in reason["error"]
    assert "Traceback" not in output.out
    assert local_path.read_bytes() == broken_before_import
    archive_root = target / ".agent" / "thread-rollovers" / AGENT / "_archive"
    assert not archive_root.exists() or not any(archive_root.iterdir())


def test_newer_remote_archives_stale_local_and_preserves_different_handoff(
    tmp_path: Path,
    handoff_candidates: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    state = _seed_state(source, thread_id="source-thread", generation=4)
    bundle = tmp_path / "remote4.tgz"
    assert th.cmd_export_bundle(_export_args(source, state, bundle)) == 0
    capsys.readouterr()

    _seed_state(target, thread_id="source-thread", generation=2)
    (target / HANDOFF_PATH).write_text("local handoff differs\n", encoding="utf-8")

    assert th.cmd_import_bundle(_import_args(target, bundle)) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "installed"
    assert output["archived"]
    assert output["preserved_handoffs"]
    archive_root = target / output["archived"]
    archived_state = json.loads((archive_root / "lease.json").read_text(encoding="utf-8"))
    assert archived_state["replacement"]["status"] == "superseded"
    assert list((target / HANDOFF_PATH).parent.glob("CLAUDE-DRIVER-HANDOFF.*.superseded.md"))


def test_newer_local_refuses_and_force_archives_then_installs(
    tmp_path: Path,
    handoff_candidates: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    state = _seed_state(source, thread_id="source-thread", generation=3)
    bundle = tmp_path / "remote3.tgz"
    assert th.cmd_export_bundle(_export_args(source, state, bundle)) == 0
    capsys.readouterr()
    assert th.cmd_import_bundle(_import_args(target, bundle)) == 0
    capsys.readouterr()

    _seed_state(target, thread_id="source-thread", generation=4, prepared_at="2026-08-25T00:00:00Z")
    assert th.cmd_import_bundle(_import_args(target, bundle)) == 2
    refused = json.loads(capsys.readouterr().out)
    assert refused["status"] == "refused"
    assert refused["local"]["generation"] == 4
    assert refused["remote"]["generation"] == 3

    assert th.cmd_import_bundle(_import_args(target, bundle, force=True)) == 0
    forced = json.loads(capsys.readouterr().out)
    assert forced["status"] == "installed"
    assert forced["archived"]


def test_import_newer_lineage_supersedes_one_of_two_pending_detect_candidates(
    tmp_path: Path,
    handoff_candidates: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    remote = _seed_state(source, thread_id="lineage-a", generation=3)
    _mark_confirmed(source, remote)
    bundle = tmp_path / "lineage-a.tgz"
    assert th.cmd_export_bundle(_export_args(source, remote, bundle)) == 0
    capsys.readouterr()

    _seed_state(target, thread_id="lineage-a", generation=2)
    _seed_state(target, thread_id="lineage-b")
    assert th.cmd_import_bundle(_import_args(target, bundle)) == 0
    capsys.readouterr()

    args = SimpleNamespace(repo_root=target, agent=AGENT, current_thread_id="", task_family="", format="json")
    assert th.cmd_detect(args) == 0
    detected = json.loads(capsys.readouterr().out)
    assert detected["status"] == "pending_start"
    assert detected["lineage_id"] != remote["lineage_id"]


def test_from_api_cross_agent_import_uses_max_upload_seq_for_handoff(
    tmp_path: Path,
    handoff_candidates: None,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_foreign_old = tmp_path / "source-claude-old"
    source_own = tmp_path / "source-grok"
    source_foreign_new = tmp_path / "source-claude-new"
    target = tmp_path / "target"
    source_foreign_old.mkdir()
    source_own.mkdir()
    source_foreign_new.mkdir()
    target.mkdir()

    foreign_old = _seed_state(
        source_foreign_old,
        thread_id="foreign-old-thread",
        agent="claude-infra",
        generation=3,
    )
    own = _seed_state(
        source_own,
        thread_id="own-thread",
        agent="grok-infra",
        generation=4,
        harness="grok-tui",
        prepared_at="2026-08-24T17:00:00Z",
    )
    foreign_new = _seed_state(
        source_foreign_new,
        thread_id="foreign-new-thread",
        agent="claude-infra",
        generation=3,
        prepared_at="2026-08-24T18:00:00Z",
    )
    (source_foreign_old / HANDOFF_PATH).write_text("stale foreign lane handoff\n", encoding="utf-8")
    (source_own / HANDOFF_PATH).write_text("own lane handoff\n", encoding="utf-8")
    (source_foreign_new / HANDOFF_PATH).write_text("fresh foreign lane handoff\n", encoding="utf-8")

    foreign_old_bundle = tmp_path / "foreign-old.tgz"
    own_bundle = tmp_path / "own.tgz"
    foreign_new_bundle = tmp_path / "foreign-new.tgz"
    assert th.cmd_export_bundle(_export_args(source_foreign_old, foreign_old, foreign_old_bundle)) == 0
    capsys.readouterr()
    assert th.cmd_export_bundle(_export_args(source_own, own, own_bundle)) == 0
    capsys.readouterr()
    assert th.cmd_export_bundle(_export_args(source_foreign_new, foreign_new, foreign_new_bundle)) == 0
    capsys.readouterr()
    foreign_old_manifest, _ = th._bundle_extract(foreign_old_bundle.read_bytes())
    own_manifest, _ = th._bundle_extract(own_bundle.read_bytes())
    foreign_new_manifest, _ = th._bundle_extract(foreign_new_bundle.read_bytes())
    foreign_old_blob = foreign_old_bundle.read_bytes()
    own_blob = own_bundle.read_bytes()
    foreign_new_blob = foreign_new_bundle.read_bytes()
    foreign_old_manifest["upload_seq"] = 1
    own_manifest["upload_seq"] = 2
    foreign_new_manifest["upload_seq"] = 3

    bundles = {
        1: (foreign_old_manifest, foreign_old_blob),
        2: (own_manifest, own_blob),
        3: (foreign_new_manifest, foreign_new_blob),
    }

    def bundle_list(_args: SimpleNamespace, *, stream_id: str, limit: int = 20):
        assert stream_id == STREAM
        assert limit == 20
        return [
            {"manifest": manifest, "upload_seq": sequence}
            for sequence, (manifest, _blob) in sorted(bundles.items(), reverse=True)
        ]

    def bundle_by_seq(_args: SimpleNamespace, *, stream_id: str, upload_seq: int):
        assert stream_id == STREAM
        return bundles[upload_seq]

    monkeypatch.setattr(th, "_bundle_api_list", bundle_list)
    monkeypatch.setattr(th, "_bundle_api_by_seq", bundle_by_seq)
    args = _import_args(target, None, agent="grok-infra", from_api=STREAM)
    assert th.cmd_import_bundle(args) == 0
    result = json.loads(capsys.readouterr().out)
    assert [item["agent"] for item in result["bundles"]] == ["claude-infra", "grok-infra"]
    assert result["handoff_source"] == "claude-infra"
    assert result["handoff_upload_seq"] == 3

    foreign_lineage = target / th.default_state_path("claude-infra", foreign_new["lineage_id"])
    own_lineage = target / th.default_state_path("grok-infra", own["lineage_id"])
    assert foreign_lineage.is_file()
    assert own_lineage.is_file()
    handoff_text = (target / HANDOFF_PATH).read_text(encoding="utf-8")
    assert handoff_text == "fresh foreign lane handoff\n"

    detect_args = SimpleNamespace(
        repo_root=target,
        agent="grok-infra",
        current_thread_id=None,
        format=None,
        stream=None,
        task_family=None,
    )
    assert th.cmd_detect(detect_args) == 0
    grok_detected = json.loads(capsys.readouterr().out)
    assert grok_detected["agent"] == "grok-infra"
    assert grok_detected["status"] == "pending_start"
    assert grok_detected["generation"] == 4
    detect_args.agent = "claude-infra"
    assert th.cmd_detect(detect_args) == 0
    detected = json.loads(capsys.readouterr().out)
    assert detected["agent"] == "claude-infra"
    assert detected["status"] == "pending_start"
    assert detected["generation"] == 3
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print(handoff_text, end="")


def test_from_api_foreign_lineage_is_ignored_by_driver_detect(
    tmp_path: Path,
    handoff_candidates: None,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    foreign = _seed_state(source, thread_id="foreign-only", agent="claude-infra", generation=3)
    (source / HANDOFF_PATH).write_text("foreign lane handoff\n", encoding="utf-8")
    bundle = tmp_path / "foreign-only.tgz"
    assert th.cmd_export_bundle(_export_args(source, foreign, bundle)) == 0
    capsys.readouterr()
    manifest, _ = th._bundle_extract(bundle.read_bytes())
    manifest["upload_seq"] = 3
    blob = bundle.read_bytes()

    def bundle_list(_args: SimpleNamespace, *, stream_id: str, limit: int = 20):
        assert stream_id == STREAM
        assert limit == 20
        return [{"manifest": manifest, "upload_seq": 3}]

    monkeypatch.setattr(th, "_bundle_api_list", bundle_list)
    monkeypatch.setattr(th, "_bundle_api_by_seq", lambda _args, *, stream_id, upload_seq: (manifest, blob))
    assert th.cmd_import_bundle(_import_args(target, None, agent="grok-infra", from_api=STREAM)) == 0
    capsys.readouterr()

    detect_args = SimpleNamespace(
        repo_root=target,
        agent="grok-infra",
        current_thread_id=None,
        format=None,
        stream=None,
        task_family=None,
    )
    assert th.cmd_detect(detect_args) == 0
    assert json.loads(capsys.readouterr().out) == {"agent": "grok-infra", "status": "none"}
    detect_args.agent = "claude-infra"
    assert th.cmd_detect(detect_args) == 0
    detected = json.loads(capsys.readouterr().out)
    assert detected["agent"] == "claude-infra"
    assert detected["status"] == "pending_start"
    assert detected["generation"] == 3


def test_api_down_import_is_fail_open_and_secret_prose_is_not_a_hit(
    tmp_path: Path,
    handoff_candidates: None,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    state = _seed_state(source, thread_id="source-thread")
    assert th.cmd_import_bundle(
        SimpleNamespace(
            repo_root=tmp_path / "empty",
            agent=AGENT,
            file=None,
            from_api=STREAM,
            stream=STREAM,
            force=False,
            monitor_base_url="http://127.0.0.1:1",
        )
    ) == 0
    assert "WARNING: rollover bundle import skipped" in capsys.readouterr().err

    validate_entry_body("The credential-assignment rule is discussed as prose, not a secret assignment.")
    assert th._bundle_secret_hits(
        {".agent/thread-rollovers/claude-infra/source-lineage/semantic-snapshot.json": b"api-key: secret-value\n"}
    ) == [
        (".agent/thread-rollovers/claude-infra/source-lineage/semantic-snapshot.json", "credential-assignment")
    ]
    bundle = tmp_path / "secret.tgz"
    (source / HANDOFF_PATH).write_text("api-key: supersecret-value\n", encoding="utf-8")
    called = False

    def unexpected_upload(*_args: object, **_kwargs: object) -> dict[str, object]:
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(th, "_bundle_api_upload", unexpected_upload)
    assert th.cmd_export_bundle(_export_args(source, state, bundle, upload=True)) == 0
    assert not called
    assert bundle.is_file()
    warning = capsys.readouterr().err
    assert "secret scan hit count=1" in warning
    assert "credential-assignment" not in warning
    assert "supersecret-value" not in warning

    auto_result = th._maybe_auto_upload_bundle(
        _export_args(source, state, bundle),
        repo_root=source,
        state_root=source,
        agent=state["agent"],
        state=state,
    )
    assert auto_result["status"] == "skipped-secret-scan"
    auto_warning = capsys.readouterr().err
    assert "secret scan hit count=1" in auto_warning
    assert "credential-assignment" not in auto_warning
    assert "supersecret-value" not in auto_warning


def test_retention_keeps_latest_five_and_store_false_positive_contract(tmp_path: Path) -> None:
    from agents_extensions.shared.session_streams.db import SessionStreamDatabase
    from agents_extensions.shared.session_streams.model import LeaseHolder
    from agents_extensions.shared.session_streams.store import SessionStreamStore

    store = SessionStreamStore(SessionStreamDatabase(tmp_path / "streams.sqlite3"))
    lease = store.open_session(
        stream_id=STREAM,
        holder=LeaseHolder(agent="claude", harness="claude-code", instance_id="instance", process_id=1234),
        lineage_id="lineage-retention",
        ttl_seconds=900,
    )
    for index in range(6):
        payload = f"packet-{index}".encode()
        name = f".agent/thread-rollovers/claude/lineage-retention/generation-0001/rollover-r{index}/handoff.md"
        members = {name: payload}
        manifest = {
            "schema": "rollover-bundle.v1",
            "agent": "claude",
            "stream_id": STREAM,
            "lineage_id": "lineage-retention",
            "rollover_id": f"rollover-r{index}",
            "generation": index + 1,
            "status": "pending_start",
            "prepared_at": f"2026-08-24T16:0{index}:00Z",
            "source_root": "{{REPO_ROOT}}",
            "exported_at": "2026-08-24T16:00:00Z",
            "files": [
                {
                    "path": name,
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "bytes": len(payload),
                    "tokenized": True,
                }
            ],
            "tokenized_members": [name],
            "upload_seq": 0,
            "bundle_sha256": "",
        }
        manifest["bundle_sha256"] = th._bundle_digest(members, manifest)
        store.upload_rollover_bundle(lease, manifest=manifest, blob=th._bundle_archive(members, manifest))
    rows = store.list_rollover_bundles(STREAM, agent="claude", lineage_id="lineage-retention")
    assert len(rows) == 5
    assert rows[0]["manifest"]["generation"] == 6
    with pytest.raises(ContentRejectedError):
        validate_entry_body("password: definitely-a-secret")
