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
    generation: int = 3,
    rollover_id: str | None = None,
    prepared_at: str = "2026-08-24T16:00:00Z",
) -> dict:
    lineage_id = th.lineage_id_for(AGENT, thread_id)
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
        agent=AGENT,
        now=datetime(2026, 8, 24, 16, 0, tzinfo=UTC),
        active_thread_id=thread_id,
        active_automation_id="old-auto",
        context_percent=80.0,
        force_new_replacement=False,
        harness="claude-code",
    )
    replacement = state["replacement"]
    del rollover_id
    assert replacement["generation"] == generation
    replacement["prepared_at"] = prepared_at
    replacement["source_checkout"] = {"full_head": "a" * 40, "clean": True}
    state_path = root / th.default_state_path(AGENT, state["lineage_id"])
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


def _export_args(root: Path, state: dict, output: Path, *, upload: bool = False) -> SimpleNamespace:
    return SimpleNamespace(
        repo_root=root,
        agent=AGENT,
        lineage_id=state["lineage_id"],
        rollover_id=None,
        stream=STREAM,
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


def _import_args(root: Path, bundle: Path, *, force: bool = False) -> SimpleNamespace:
    return SimpleNamespace(
        repo_root=root,
        agent=AGENT,
        file=bundle,
        from_api=None,
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
    assert "member=" in capsys.readouterr().err


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
