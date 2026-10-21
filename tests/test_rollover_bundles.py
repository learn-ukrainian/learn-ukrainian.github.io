"""Cross-host rollover bundle round-trip and ordering contracts."""

from __future__ import annotations

import base64
import gzip
import hashlib
import io
import json
import shutil
import subprocess
import tarfile
import urllib.error
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import pytest

from agents_extensions.shared.session_streams.inventory import stream_anchor_id
from agents_extensions.shared.session_streams.store import ContentRejectedError, validate_entry_body
from scripts.orchestration import thread_handoff as th

HANDOFF_PATH = ".claude/infra-epic/CLAUDE-DRIVER-HANDOFF.md"
AGENT = "claude-infra"
STREAM = "epic:9999"
REPO_ROOT = Path(__file__).resolve().parents[1]
# The registered infra stream, whose claude slot is AGENT; uploads bind the bundle
# agent to it. Resolved from issue_streams.yaml so epic succession needs no edit.
REGISTERED_STREAM = stream_anchor_id("infra-harness", REPO_ROOT)
STREAMS_YAML = Path("scripts/config/issue_streams.yaml")


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
    stream: str = STREAM,
) -> SimpleNamespace:
    return SimpleNamespace(
        repo_root=root,
        agent=agent,
        file=bundle,
        from_api=from_api,
        stream=stream,
        force=force,
        monitor_base_url="http://127.0.0.1:1",
    )


@pytest.fixture
def handoff_candidates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(th, "_bundle_handoff_candidates", lambda _root, _stream: (HANDOFF_PATH,))


def _resign(manifest: dict, members: dict[str, bytes], *, order: list[str] | None = None) -> tuple[dict, bytes]:
    """Rebuild a valid manifest for ``members``; ``order`` keeps that archive member order."""
    manifest = dict(manifest)
    manifest["files"] = [
        {
            "path": name,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "tokenized": th._bundle_text_member(name),
        }
        for name, payload in sorted(members.items())
    ]
    manifest["tokenized_members"] = sorted(name for name in members if th._bundle_text_member(name))
    manifest["bundle_sha256"] = th._bundle_digest(members, manifest)
    if order is None:
        return manifest, th._bundle_archive(members, manifest)
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w") as archive:
        for name, payload in [(th.ROLLOVER_BUNDLE_MANIFEST_NAME, th._bundle_json(manifest))] + [
            (name, members[name]) for name in order
        ]:
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))
    return manifest, gzip.compress(raw.getvalue())


def _tree(root: Path) -> dict[str, bytes | None]:
    """Every path under ``root``: file bytes, or None for a directory."""
    return {
        path.relative_to(root).as_posix(): (path.read_bytes() if path.is_file() else None)
        for path in sorted(root.rglob("*"))
    }


def _with_registry(root: Path) -> None:
    """Give a temporary checkout the real stream registry, so handoff candidates resolve as in the repo."""
    (root / STREAMS_YAML).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(REPO_ROOT / STREAMS_YAML, root / STREAMS_YAML)


def _store(tmp_path: Path, *, stream: str = REGISTERED_STREAM, holder: str = "claude"):
    from agents_extensions.shared.session_streams.db import SessionStreamDatabase
    from agents_extensions.shared.session_streams.model import LeaseHolder
    from agents_extensions.shared.session_streams.store import SessionStreamStore

    store = SessionStreamStore(SessionStreamDatabase(tmp_path / "streams.sqlite3"))
    lease = store.open_session(
        stream_id=stream,
        holder=LeaseHolder(agent=holder, harness=f"{holder}-cli", instance_id="instance", process_id=1234),
        lineage_id="lineage-store",
        ttl_seconds=900,
    )
    return store, lease


def _packet_bundle(agent: str, stream: str, *, extra: dict[str, bytes] | None = None) -> tuple[dict, bytes]:
    name = f".agent/thread-rollovers/{agent}/lineage-store/generation-0001/rollover-store/handoff.md"
    manifest = {
        "schema": "rollover-bundle.v1",
        "agent": agent,
        "stream_id": stream,
        "lineage_id": "lineage-store",
        "rollover_id": "rollover-store",
        "generation": 1,
        "status": "pending_start",
        "prepared_at": "2026-08-24T16:00:00Z",
        "source_root": "{{REPO_ROOT}}",
        "exported_at": "2026-08-24T16:00:00Z",
        "upload_seq": 0,
    }
    return _resign(manifest, {name: b"packet\n", **(extra or {})})


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
    assert [item["sha256"] for item in first_manifest["files"]] == [item["sha256"] for item in second_manifest["files"]]

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


def _exported(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    name: str,
    *,
    agent: str = AGENT,
    generation: int = 3,
    prepared_at: str = "2026-08-24T16:00:00Z",
    handoff: str,
    harness: str = "claude-code",
) -> tuple[dict, dict, bytes]:
    """Export one lineage from its own source checkout; returns (state, manifest, blob)."""
    source = tmp_path / name
    source.mkdir()
    state = _seed_state(
        source, thread_id=f"{name}-thread", agent=agent, generation=generation, prepared_at=prepared_at, harness=harness
    )
    (source / HANDOFF_PATH).write_text(handoff, encoding="utf-8")
    bundle = tmp_path / f"{name}.tgz"
    assert th.cmd_export_bundle(_export_args(source, state, bundle)) == 0
    capsys.readouterr()
    manifest, _ = th._bundle_extract(bundle.read_bytes())
    return state, manifest, bundle.read_bytes()


class _BundleServer:
    """In-memory bundle API behind the real request helpers: newest first, honoring agent and limit."""

    def __init__(
        self,
        rows: dict[int, tuple[dict, bytes]],
        *,
        ignore_agent: bool = False,
        listed_agent: str | None = None,
        seq_manifest: dict | None = None,
        answers: dict[str, tuple[int, dict]] | None = None,
    ) -> None:
        """``ignore_agent`` lists every slot's rows; ``listed_agent`` mislabels them
        consistently (row and listed manifest alike), leaving the fetched bundle intact;
        ``seq_manifest`` replaces the fetched manifest; ``answers`` scripts an error
        status for ``"list"`` or ``"seq"`` requests."""
        self.rows = rows
        self.ignore_agent = ignore_agent
        self.listed_agent = listed_agent
        self.seq_manifest = seq_manifest
        self.answers = answers or {}
        self.paths: list[str] = []

    def get(self, path: str, headers: dict | None = None) -> tuple[int, str, dict]:
        self.paths.append(path)
        parsed = urlsplit(path)
        if parsed.path.endswith("/bundles"):
            if "list" in self.answers:
                status, body = self.answers["list"]
                return status, json.dumps(body), {}
            query = parse_qs(parsed.query)
            agent = None if self.ignore_agent else query.get("agent", [None])[0]
            limit = int(query.get("limit", ["20"])[0])
            listed = [
                {
                    "manifest": {**manifest, "agent": self.listed_agent or manifest["agent"], "upload_seq": seq},
                    "upload_seq": seq,
                    "agent": self.listed_agent or manifest["agent"],
                }
                for seq, (manifest, _blob) in sorted(self.rows.items(), reverse=True)
                if agent is None or manifest["agent"] == agent
            ][:limit]
            return 200, json.dumps({"bundles": listed}), {}
        if "seq" in self.answers:
            status, body = self.answers["seq"]
            return status, json.dumps(body), {}
        seq = int(parsed.path.rsplit("/", 1)[1])
        manifest, blob = self.rows[seq]
        manifest = self.seq_manifest or {**manifest, "upload_seq": seq}
        body = {"manifest": manifest, "blob": base64.b64encode(blob).decode("ascii")}
        return 200, json.dumps(body), {}


def test_from_api_installs_only_the_callers_bundle_when_another_agent_uploaded_later(
    tmp_path: Path,
    handoff_candidates: None,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    own, own_manifest, own_blob = _exported(
        tmp_path, capsys, "own", agent="grok-infra", generation=4, harness="grok-tui", handoff="own lane handoff\n"
    )
    foreign, foreign_manifest, foreign_blob = _exported(
        tmp_path, capsys, "foreign", prepared_at="2026-08-24T18:00:00Z", handoff="foreign lane handoff\n"
    )
    target = tmp_path / "target"
    target.mkdir()
    server = _BundleServer({1: (own_manifest, own_blob), 2: (foreign_manifest, foreign_blob)})
    monkeypatch.setattr(th, "_bundle_client", lambda *_a, **_kw: server)

    assert th.cmd_import_bundle(_import_args(target, None, agent="grok-infra", from_api=STREAM)) == 0
    result = json.loads(capsys.readouterr().out)

    assert result["status"] == "installed"
    assert result["agent"] == "grok-infra"
    assert result["upload_seq"] == 1
    assert (target / th.default_state_path("grok-infra", own["lineage_id"])).is_file()
    assert not (target / ".agent" / "thread-rollovers" / "claude-infra").exists()
    assert not (target / th.default_state_path("claude-infra", foreign["lineage_id"])).exists()
    assert (target / HANDOFF_PATH).read_text(encoding="utf-8") == "own lane handoff\n"
    assert all("agent=grok-infra" in path for path in server.paths if urlsplit(path).path.endswith("/bundles"))


def test_from_api_selects_the_highest_upload_seq_among_the_callers_rows(
    tmp_path: Path,
    handoff_candidates: None,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    older, older_manifest, older_blob = _exported(tmp_path, capsys, "older", handoff="older own handoff\n")
    newer, newer_manifest, newer_blob = _exported(
        tmp_path, capsys, "newer", generation=4, prepared_at="2026-08-24T17:00:00Z", handoff="newer own handoff\n"
    )
    target = tmp_path / "target"
    target.mkdir()
    server = _BundleServer({3: (older_manifest, older_blob), 5: (newer_manifest, newer_blob)})
    monkeypatch.setattr(th, "_bundle_client", lambda *_a, **_kw: server)

    assert th.cmd_import_bundle(_import_args(target, None, from_api=STREAM)) == 0
    result = json.loads(capsys.readouterr().out)

    assert result["status"] == "installed"
    assert result["upload_seq"] == 5
    assert result["lineage_id"] == newer["lineage_id"]
    assert not (target / th.default_state_path(AGENT, older["lineage_id"])).exists()
    assert (target / HANDOFF_PATH).read_text(encoding="utf-8") == "newer own handoff\n"


def test_from_api_twenty_newer_foreign_rows_do_not_hide_the_callers_bundle(
    tmp_path: Path,
    handoff_candidates: None,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    own, own_manifest, own_blob = _exported(tmp_path, capsys, "own", handoff="own lane handoff\n")
    _foreign, foreign_manifest, foreign_blob = _exported(
        tmp_path, capsys, "foreign", agent="grok-infra", harness="grok-tui", handoff="foreign lane handoff\n"
    )
    rows = {1: (own_manifest, own_blob)}
    rows.update({seq: (foreign_manifest, foreign_blob) for seq in range(2, 22)})
    server = _BundleServer(rows)
    monkeypatch.setattr(th, "_bundle_client", lambda *_a, **_kw: server)
    target = tmp_path / "target"
    target.mkdir()

    assert th.cmd_import_bundle(_import_args(target, None, from_api=STREAM)) == 0
    result = json.loads(capsys.readouterr().out)

    list_queries = [parse_qs(urlsplit(path).query) for path in server.paths if urlsplit(path).path.endswith("/bundles")]
    assert list_queries == [{"agent": [AGENT], "limit": ["20"]}]
    assert result["status"] == "installed"
    assert result["upload_seq"] == 1
    assert (target / th.default_state_path(AGENT, own["lineage_id"])).is_file()
    assert not (target / ".agent" / "thread-rollovers" / "grok-infra").exists()
    assert (target / HANDOFF_PATH).read_text(encoding="utf-8") == "own lane handoff\n"


TYPED_NONE = '{"status":"none","action":"import-bundle"}\n'


def test_from_api_slot_without_a_bundle_is_a_typed_none(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = _BundleServer({})
    monkeypatch.setattr(th, "_bundle_client", lambda *_a, **_kw: server)
    target = tmp_path / "target"
    target.mkdir()

    assert th.cmd_import_bundle(_import_args(target, None, from_api=STREAM)) == 0
    captured = capsys.readouterr()

    assert captured.out == TYPED_NONE
    assert captured.err == ""
    assert _tree(target) == {}
    assert [urlsplit(path).path for path in server.paths] == [f"/api/epics/v1/{STREAM}/bundles"]


@pytest.mark.parametrize("ignore_agent", [False, True], ids=["api-filters-slot", "api-lists-every-slot"])
def test_from_api_with_only_another_agents_bundle_is_none_and_installs_nothing(
    tmp_path: Path,
    handoff_candidates: None,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    ignore_agent: bool,
) -> None:
    _foreign, manifest, blob = _exported(tmp_path, capsys, "foreign", handoff="foreign lane handoff\n")
    server = _BundleServer({3: (manifest, blob)}, ignore_agent=ignore_agent)
    monkeypatch.setattr(th, "_bundle_client", lambda *_a, **_kw: server)
    target = tmp_path / "target"
    target.mkdir()

    assert th.cmd_import_bundle(_import_args(target, None, agent="grok-infra", from_api=STREAM)) == 0
    assert capsys.readouterr().out == TYPED_NONE
    assert _tree(target) == {}
    # The foreign blob is never even fetched.
    assert all(urlsplit(path).path.endswith("/bundles") for path in server.paths)


def _refusal(capsys: pytest.CaptureFixture[str]) -> dict:
    out = capsys.readouterr().out
    assert "invalid_rollover_bundle" in out
    return json.loads(out)


@pytest.mark.parametrize(
    ("request_kind", "status", "detail"),
    [
        ("list", 409, "stale generation"),
        ("seq", 409, "stale generation"),
        ("list", 403, "fenced lease"),
        ("seq", 403, "fenced lease"),
        # A row the list just named vanished: an inconsistency, not an empty slot.
        ("seq", 404, "rollover bundle not found"),
        # The stream itself is unknown to the API.
        ("list", 404, "epic stream not found"),
    ],
)
def test_from_api_semantic_refusal_still_exits_invalid_rollover_bundle(
    tmp_path: Path,
    handoff_candidates: None,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    request_kind: str,
    status: int,
    detail: str,
) -> None:
    _own, manifest, blob = _exported(tmp_path, capsys, "own", handoff="own lane handoff\n")
    server = _BundleServer({4: (manifest, blob)}, answers={request_kind: (status, {"detail": detail})})
    monkeypatch.setattr(th, "_bundle_client", lambda *_a, **_kw: server)
    target = tmp_path / "target"
    target.mkdir()

    assert th.cmd_import_bundle(_import_args(target, None, from_api=STREAM)) == 2
    refusal = _refusal(capsys)

    assert refusal == {"code": "invalid_rollover_bundle", "error": refusal["error"], "action": "import-bundle"}
    assert detail in refusal["error"]
    assert _tree(target) == {}


def test_from_api_hash_mismatch_still_exits_invalid_rollover_bundle(
    tmp_path: Path,
    handoff_candidates: None,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _own, manifest, blob = _exported(tmp_path, capsys, "own", handoff="own lane handoff\n")
    forged = {**manifest, "upload_seq": 4, "bundle_sha256": "0" * 64}
    server = _BundleServer({4: (manifest, blob)}, seq_manifest=forged)
    monkeypatch.setattr(th, "_bundle_client", lambda *_a, **_kw: server)
    target = tmp_path / "target"
    target.mkdir()

    assert th.cmd_import_bundle(_import_args(target, None, from_api=STREAM)) == 2
    assert "does not match the embedded manifest" in _refusal(capsys)["error"]
    assert _tree(target) == {}


def test_from_api_agent_mismatch_still_exits_invalid_rollover_bundle(
    tmp_path: Path,
    handoff_candidates: None,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The list row claims the caller's slot, but the fetched bundle belongs to another.
    _foreign, manifest, blob = _exported(tmp_path, capsys, "foreign", handoff="foreign lane handoff\n")
    server = _BundleServer({4: (manifest, blob)}, ignore_agent=True, listed_agent="grok-infra")
    monkeypatch.setattr(th, "_bundle_client", lambda *_a, **_kw: server)
    target = tmp_path / "target"
    target.mkdir()

    assert th.cmd_import_bundle(_import_args(target, None, agent="grok-infra", from_api=STREAM)) == 2
    assert _refusal(capsys)["error"] == "bundle agent does not match --agent"
    assert _tree(target) == {}


FOREIGN_ROW = {"manifest": {"agent": "claude-devops", "stream_id": STREAM, "upload_seq": 7}, "upload_seq": 7}
# The same slot identity carried at both levels, consistently.
FOREIGN_ROW_WITH_COPIES = {
    "agent": "gpt-infra",
    "stream_id": STREAM,
    "manifest": {"agent": "gpt-infra", "stream_id": STREAM, "upload_seq": 8},
    "upload_seq": 8,
}

# Listings whose slot identity is missing or malformed. None of them proves the
# slot empty, so each must refuse rather than read as the typed none (#11257).
MALFORMED_LISTINGS = {
    "manifest-without-agent": {"bundles": [{"manifest": {}}]},
    "manifest-missing": {"bundles": [{"upload_seq": 3}]},
    "manifest-not-a-mapping": {"bundles": [{"manifest": ["claude-devops"]}]},
    "manifest-agent-null": {"bundles": [{"manifest": {"agent": None}}]},
    "manifest-agent-empty": {"bundles": [{"manifest": {"agent": ""}}]},
    "manifest-agent-int": {"bundles": [{"manifest": {"agent": 7}}]},
    "manifest-agent-list": {"bundles": [{"manifest": {"agent": ["claude-devops"]}}]},
    "manifest-agent-not-a-slot-name": {"bundles": [{"manifest": {"agent": "Claude Devops"}}]},
    "row-agent-null": {"bundles": [{"agent": None, "manifest": {}}]},
    # A present but null row identity is malformed even beside a manifest agent.
    "row-agent-null-over-manifest-agent": {"bundles": [{"agent": None, "manifest": {"agent": "claude-devops"}}]},
    "row-agent-empty": {"bundles": [{"agent": "", "manifest": {"agent": "claude-devops"}}]},
    "row-agent-int": {"bundles": [{"agent": 7, "manifest": {"agent": "claude-devops"}}]},
    "row-agent-list": {"bundles": [{"agent": ["claude-devops"], "manifest": {"agent": "claude-devops"}}]},
    "row-not-an-object": {"bundles": ["claude-devops"]},
    "bundles-not-a-list": {"bundles": {"agent": "claude-devops"}},
    "bundles-null": {"bundles": None},
    "bundles-missing": {},
    "foreign-then-malformed": {"bundles": [FOREIGN_ROW, {"manifest": {}}]},
    "malformed-then-foreign": {"bundles": [{"manifest": {"agent": 7}}, FOREIGN_ROW]},
}


@pytest.mark.parametrize("listing", list(MALFORMED_LISTINGS.values()), ids=list(MALFORMED_LISTINGS))
def test_from_api_listing_without_a_valid_slot_identity_refuses(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    listing: dict,
) -> None:
    server = _BundleServer({}, answers={"list": (200, listing)})
    monkeypatch.setattr(th, "_bundle_client", lambda *_a, **_kw: server)
    target = tmp_path / "target"
    target.mkdir()

    assert th.cmd_import_bundle(_import_args(target, None, from_api=STREAM)) == 2
    captured = capsys.readouterr()

    assert captured.out != TYPED_NONE
    refusal = json.loads(captured.out)
    assert refusal == {"code": "invalid_rollover_bundle", "error": refusal["error"], "action": "import-bundle"}
    assert _tree(target) == {}
    # Nothing past the listing is fetched.
    assert [urlsplit(path).path for path in server.paths] == [f"/api/epics/v1/{STREAM}/bundles"]


def test_from_api_well_formed_foreign_row_alone_is_still_none(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    listing = {"bundles": [FOREIGN_ROW, FOREIGN_ROW_WITH_COPIES]}
    server = _BundleServer({}, answers={"list": (200, listing)})
    monkeypatch.setattr(th, "_bundle_client", lambda *_a, **_kw: server)
    target = tmp_path / "target"
    target.mkdir()

    assert th.cmd_import_bundle(_import_args(target, None, from_api=STREAM)) == 0
    assert capsys.readouterr().out == TYPED_NONE
    assert _tree(target) == {}


def _contradictory(field: str, row_value: object, manifest_value: object, *, agent: str = "claude-devops") -> dict:
    """A well-formed row whose top-level ``field`` disagrees with its manifest's."""
    manifest = {"agent": agent, "stream_id": STREAM, "upload_seq": 7}
    return {"manifest": {**manifest, field: manifest_value}, **{field: row_value}}


# Rows whose top-level identity contradicts their own manifest. Every value is
# well-formed on its own; only their disagreement makes the row unclassifiable,
# so it can prove neither a foreign slot nor this one (#11257).
CONTRADICTORY_LISTINGS = {
    # The exact probe from the review of 2aa5a0d8: caller AGENT is claude-infra.
    "foreign-row-own-manifest": {
        "bundles": [{"agent": "claude-devops", "manifest": {"agent": AGENT, "upload_seq": 7}, "upload_seq": 7}]
    },
    "foreign-row-own-manifest-full": {"bundles": [_contradictory("agent", "claude-devops", AGENT)]},
    "own-row-foreign-manifest": {"bundles": [_contradictory("agent", AGENT, "claude-devops")]},
    "two-foreign-agents": {"bundles": [_contradictory("agent", "claude-devops", "gpt-infra")]},
    "stream-mismatch": {"bundles": [_contradictory("stream_id", "epic:1", STREAM)]},
    "stream-mismatch-own-slot": {"bundles": [_contradictory("stream_id", STREAM, "epic:1", agent=AGENT)]},
    "upload-seq-mismatch": {"bundles": [_contradictory("upload_seq", 7, 8)]},
    "upload-seq-mismatch-own-slot": {"bundles": [_contradictory("upload_seq", 7, 8, agent=AGENT)]},
    "consistent-foreign-then-contradictory": {
        "bundles": [FOREIGN_ROW_WITH_COPIES, _contradictory("agent", "claude-devops", AGENT)]
    },
    "contradictory-then-consistent-foreign": {
        "bundles": [_contradictory("agent", "claude-devops", AGENT), FOREIGN_ROW]
    },
}


@pytest.mark.parametrize("listing", list(CONTRADICTORY_LISTINGS.values()), ids=list(CONTRADICTORY_LISTINGS))
def test_from_api_listing_row_contradicting_its_manifest_refuses(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    listing: dict,
) -> None:
    server = _BundleServer({}, answers={"list": (200, listing)})
    monkeypatch.setattr(th, "_bundle_client", lambda *_a, **_kw: server)
    target = tmp_path / "target"
    target.mkdir()

    assert th.cmd_import_bundle(_import_args(target, None, from_api=STREAM)) == 2
    refusal = _refusal(capsys)

    assert refusal == {"code": "invalid_rollover_bundle", "error": refusal["error"], "action": "import-bundle"}
    assert "contradicts its manifest" in refusal["error"]
    assert _tree(target) == {}
    # The refusal comes from the listing itself; no bundle is fetched.
    assert [urlsplit(path).path for path in server.paths] == [f"/api/epics/v1/{STREAM}/bundles"]


class _DownBundleClient:
    def get(self, path: str, headers: dict | None = None) -> tuple[int, str, dict]:
        raise urllib.error.URLError("connection refused")


@pytest.mark.parametrize(
    "client",
    [_DownBundleClient(), _BundleServer({}, answers={"list": (503, {"detail": "store offline"})})],
    ids=["transport", "http-503"],
)
def test_from_api_unavailable_still_fails_open_with_the_warning(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    client: object,
) -> None:
    monkeypatch.setattr(th, "_bundle_client", lambda *_a, **_kw: client)
    target = tmp_path / "target"
    target.mkdir()

    assert th.cmd_import_bundle(_import_args(target, None, from_api=STREAM)) == 0
    captured = capsys.readouterr()

    assert captured.err.startswith("WARNING: rollover bundle import skipped (fail-open): bundle API unavailable")
    assert json.loads(captured.out)["status"] == "warning"
    assert _tree(target) == {}


def _gate_import(monkeypatch: pytest.MonkeyPatch, target: Path, client: object, *, agent: str = AGENT) -> dict:
    from scripts.hooks import session_start_gate as gate

    monkeypatch.setattr(gate, "_import_thread_handoff", lambda: th)
    monkeypatch.setattr(th, "_bundle_client", lambda *_a, **_kw: client)
    return gate.phase_rollover_import(
        SimpleNamespace(import_bundle=True, repo_root=str(target), agent=agent, stream=STREAM)
    )


@pytest.mark.parametrize("foreign_row", [False, True], ids=["empty-slot", "another-slot-only"])
def test_session_start_reports_a_slot_without_a_bundle_as_ok(
    tmp_path: Path,
    handoff_candidates: None,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    foreign_row: bool,
) -> None:
    rows = {}
    if foreign_row:
        _foreign, manifest, blob = _exported(tmp_path, capsys, "foreign", handoff="foreign lane handoff\n")
        rows = {3: (manifest, blob)}
    target = tmp_path / "target"
    target.mkdir()

    result = _gate_import(monkeypatch, target, _BundleServer(rows, ignore_agent=True), agent="grok-infra")

    assert result["status"] == "ok"
    assert "warning" not in result
    assert "invalid_rollover_bundle" not in json.dumps(result)
    assert _tree(target) == {}


def test_session_start_still_warns_on_a_refusal_and_on_unavailability(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "target"
    target.mkdir()

    refused = _gate_import(monkeypatch, target, _BundleServer({}, answers={"list": (409, {"detail": "stale"})}))
    assert refused["status"] == "issue"
    assert refused["warning"].startswith("WARNING: rollover bundle import skipped (fail-open):")
    assert "invalid_rollover_bundle" in refused["warning"]

    down = _gate_import(monkeypatch, target, _DownBundleClient())
    assert down["status"] == "issue"
    assert down["warning"].startswith("WARNING: rollover bundle import skipped (fail-open):")
    assert "bundle API unavailable" in down["warning"]
    assert _tree(target) == {}


@pytest.mark.parametrize(
    "listing",
    [
        MALFORMED_LISTINGS["manifest-without-agent"],
        MALFORMED_LISTINGS["foreign-then-malformed"],
        CONTRADICTORY_LISTINGS["foreign-row-own-manifest"],
        CONTRADICTORY_LISTINGS["consistent-foreign-then-contradictory"],
    ],
    ids=[
        "identity-missing",
        "mixed-foreign-and-malformed",
        "identity-contradictory",
        "mixed-foreign-and-contradictory",
    ],
)
def test_session_start_warns_when_a_listed_row_has_no_valid_slot_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    listing: dict,
) -> None:
    target = tmp_path / "target"
    target.mkdir()

    result = _gate_import(monkeypatch, target, _BundleServer({}, answers={"list": (200, listing)}))

    assert result["status"] == "issue"
    assert result["warning"].startswith("WARNING: rollover bundle import skipped (fail-open):")
    assert "invalid_rollover_bundle" in result["warning"]
    assert _tree(target) == {}


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
@pytest.mark.parametrize(
    ("payload", "rc", "warns"),
    [
        (TYPED_NONE.strip(), 0, False),
        ('{"code":"invalid_rollover_bundle","error":"stale","action":"import-bundle"}', 2, True),
    ],
    ids=["typed-none", "refusal"],
)
def test_launcher_import_is_silent_for_the_typed_none_only(tmp_path: Path, payload: str, rc: int, warns: bool) -> None:
    helper = tmp_path / "helper"
    script = helper / "scripts" / "orchestration" / "thread_handoff.py"
    script.parent.mkdir(parents=True)
    script.write_text("# placeholder: the stub interpreter answers for it\n", encoding="utf-8")
    python = helper / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text(f"#!/usr/bin/env bash\nprintf '%s\\n' '{payload}'\nexit {rc}\n", encoding="utf-8")
    python.chmod(0o755)
    harness = (
        'source "$1/scripts/lib/launcher_core.sh"\n'
        f"launcher_selector_stream() {{ printf '%s\\n' '{STREAM}'; }}\n"
        'LC_EPIC=infra LC_DURABLE_HELPER_ROOT="$2" launcher_import_rollover_bundle\n'
    )
    result = subprocess.run(
        ["bash", "-c", harness, "bash", str(REPO_ROOT), str(helper)],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert ("WARNING:" in result.stderr) is warns


def test_api_down_import_is_fail_open_and_secret_prose_is_not_a_hit(
    tmp_path: Path,
    handoff_candidates: None,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    state = _seed_state(source, thread_id="source-thread")
    assert (
        th.cmd_import_bundle(
            SimpleNamespace(
                repo_root=tmp_path / "empty",
                agent=AGENT,
                file=None,
                from_api=STREAM,
                stream=STREAM,
                force=False,
                monitor_base_url="http://127.0.0.1:1",
            )
        )
        == 0
    )
    assert "WARNING: rollover bundle import skipped" in capsys.readouterr().err

    validate_entry_body("The credential-assignment rule is discussed as prose, not a secret assignment.")
    assert th._bundle_secret_hits(
        {".agent/thread-rollovers/claude-infra/source-lineage/semantic-snapshot.json": b"api-key: secret-value\n"}
    ) == [(".agent/thread-rollovers/claude-infra/source-lineage/semantic-snapshot.json", "credential-assignment")]
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
    store, lease = _store(tmp_path)
    for index in range(6):
        payload = f"packet-{index}".encode()
        name = f".agent/thread-rollovers/{AGENT}/lineage-retention/generation-0001/rollover-r{index}/handoff.md"
        manifest = {
            "schema": "rollover-bundle.v1",
            "agent": AGENT,
            "stream_id": REGISTERED_STREAM,
            "lineage_id": "lineage-retention",
            "rollover_id": f"rollover-r{index}",
            "generation": index + 1,
            "status": "pending_start",
            "prepared_at": f"2026-08-24T16:0{index}:00Z",
            "source_root": "{{REPO_ROOT}}",
            "exported_at": "2026-08-24T16:00:00Z",
            "upload_seq": 0,
        }
        manifest, blob = _resign(manifest, {name: payload})
        store.upload_rollover_bundle(lease, manifest=manifest, blob=blob)
    rows = store.list_rollover_bundles(REGISTERED_STREAM, agent=AGENT, lineage_id="lineage-retention")
    assert len(rows) == 5
    assert rows[0]["manifest"]["generation"] == 6
    with pytest.raises(ContentRejectedError):
        validate_entry_body("password: definitely-a-secret")


DISALLOWED_MEMBERS = [
    "README.md",
    "scripts/start-example-launcher.sh",
    ".claude/infra-epic/notes.sh",
    ".git/config",
    ".claude/other-epic/CLAUDE-DRIVER-HANDOFF.md",
    "docs/session-state/current.md",
    ".claude/infra-epic/CLAUDE-DRIVER-HANDOFF.md.bak",
    "{lineage}-extra/lease.json",
]


def _bundle_with_extra(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], extra: str
) -> tuple[Path, dict, dict[str, bytes], str]:
    """A valid export plus one extra member written right after a valid lineage member."""
    source = tmp_path / "source"
    source.mkdir()
    state = _seed_state(source, thread_id="source-thread")
    bundle = tmp_path / "export.tgz"
    assert th.cmd_export_bundle(_export_args(source, state, bundle)) == 0
    capsys.readouterr()
    manifest, members = th._bundle_extract(bundle.read_bytes())
    name = extra.format(lineage=f".agent/thread-rollovers/{AGENT}/{state['lineage_id']}")
    lineage_names = sorted(member for member in members if member.startswith(".agent/"))
    order = [lineage_names[0], name, *[member for member in sorted(members) if member != lineage_names[0]]]
    members[name] = b"extra member\n"
    manifest, blob = _resign(manifest, members, order=order)
    bundle.write_bytes(blob)
    return bundle, manifest, members, name


@pytest.mark.parametrize("extra", DISALLOWED_MEMBERS)
def test_import_refuses_whole_bundle_with_member_outside_lineage_and_own_handoffs(
    tmp_path: Path,
    handoff_candidates: None,
    capsys: pytest.CaptureFixture[str],
    extra: str,
) -> None:
    bundle, _manifest, _members, name = _bundle_with_extra(tmp_path, capsys, extra)
    target = tmp_path / "target"
    target.mkdir()
    (target / "kept.txt").write_text("unchanged\n", encoding="utf-8")
    before = _tree(target)

    assert th.cmd_import_bundle(_import_args(target, bundle)) == 2
    refusal = json.loads(capsys.readouterr().out)

    assert "outside its lineage and handoff paths" in refusal["error"]
    assert name not in refusal["error"]
    assert _tree(target) == before


@pytest.mark.parametrize("extra", DISALLOWED_MEMBERS)
def test_stage_install_refuses_member_outside_allowlist_before_any_write(
    tmp_path: Path,
    handoff_candidates: None,
    capsys: pytest.CaptureFixture[str],
    extra: str,
) -> None:
    _bundle, manifest, members, _name = _bundle_with_extra(tmp_path, capsys, extra)
    target = tmp_path / "target"
    target.mkdir()

    with pytest.raises(ValueError, match="outside its lineage and handoff paths"):
        th._bundle_stage_install(target, target, manifest=manifest, members=members)
    assert _tree(target) == {}


@pytest.mark.parametrize("extra", DISALLOWED_MEMBERS)
def test_store_refuses_member_outside_lineage_and_handoffs_leaving_no_row(tmp_path: Path, extra: str) -> None:
    store, lease = _store(tmp_path)
    name = extra.format(lineage=f".agent/thread-rollovers/{AGENT}/lineage-store")
    manifest, blob = _packet_bundle(AGENT, REGISTERED_STREAM, extra={name: b"extra member\n"})

    with pytest.raises(ValueError, match="outside its lineage and handoff paths"):
        store.upload_rollover_bundle(lease, manifest=manifest, blob=blob)
    assert store.list_rollover_bundles(REGISTERED_STREAM) == []


def test_same_agent_bundle_with_every_handoff_candidate_imports_and_uploads(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    _with_registry(source)
    _with_registry(target)
    candidates = th._bundle_handoff_candidates_for_agent(target, REGISTERED_STREAM, AGENT)
    assert candidates == th._bundle_handoff_candidates_for_agent(REPO_ROOT, REGISTERED_STREAM, AGENT)
    assert len(candidates) >= 3
    state = _seed_state(source, thread_id="source-thread")
    bundle = tmp_path / "export.tgz"
    assert th.cmd_export_bundle(_export_args(source, state, bundle, stream=REGISTERED_STREAM)) == 0
    capsys.readouterr()
    manifest, members = th._bundle_extract(bundle.read_bytes())
    for candidate in candidates:
        members[candidate] = f"handoff {candidate} at {th.ROLLOVER_BUNDLE_REPO_TOKEN}\n".encode()
    manifest, blob = _resign(manifest, members)
    bundle.write_bytes(blob)

    assert th.cmd_import_bundle(_import_args(target, bundle, stream=REGISTERED_STREAM)) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "installed"
    for candidate in candidates:
        assert (target / candidate).read_text(encoding="utf-8") == f"handoff {candidate} at {target.resolve()}\n"
    assert (target / th.default_state_path(AGENT, state["lineage_id"])).is_file()

    store, lease = _store(tmp_path)
    stored = store.upload_rollover_bundle(lease, manifest=manifest, blob=blob)
    assert stored["upload_seq"] == 1
    assert len(store.list_rollover_bundles(REGISTERED_STREAM, agent=AGENT)) == 1


@pytest.mark.parametrize(
    ("stream_key", "holder", "agent", "accepted"),
    [
        ("infra-harness", "claude", "claude-infra", True),
        ("infra-harness", "claude", "claude-devops", False),
        ("infra-harness", "claude", "grok-infra", False),
        ("devops", "claude", "claude-devops", True),
        ("devops", "claude", "claude-infra", False),
        ("curriculum-upgrade", "claude", "claude-core", True),
        ("curriculum-upgrade", "claude", "claude-curriculum-upgrade", False),
    ],
)
def test_store_binds_bundle_agent_to_holder_slot_for_the_stream(
    tmp_path: Path, stream_key: str, holder: str, agent: str, accepted: bool
) -> None:
    stream = stream_anchor_id(stream_key, REPO_ROOT)
    store, lease = _store(tmp_path, stream=stream, holder=holder)
    manifest, blob = _packet_bundle(agent, stream)

    if accepted:
        assert store.upload_rollover_bundle(lease, manifest=manifest, blob=blob)["upload_seq"] == 1
        assert len(store.list_rollover_bundles(stream)) == 1
    else:
        with pytest.raises(ValueError, match="handoff slot"):
            store.upload_rollover_bundle(lease, manifest=manifest, blob=blob)
        assert store.list_rollover_bundles(stream) == []


def test_store_refuses_a_stream_with_no_registered_slot(tmp_path: Path) -> None:
    store, lease = _store(tmp_path, stream=STREAM)
    manifest, blob = _packet_bundle(AGENT, STREAM)

    with pytest.raises(ValueError, match="handoff slot"):
        store.upload_rollover_bundle(lease, manifest=manifest, blob=blob)
    assert store.list_rollover_bundles(STREAM) == []


def _special_member_blob(manifest: dict, members: dict[str, bytes], special: tarfile.TarInfo) -> bytes:
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w") as archive:
        for name, payload in [(th.ROLLOVER_BUNDLE_MANIFEST_NAME, th._bundle_json(manifest)), *members.items()]:
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))
        archive.addfile(special)
    return gzip.compress(raw.getvalue())


@pytest.mark.parametrize(
    ("kind", "linkname"),
    [
        (tarfile.SYMTYPE, "../../../../outside"),
        (
            tarfile.LNKTYPE,
            ".agent/thread-rollovers/claude-infra/lineage-store/generation-0001/rollover-store/handoff.md",
        ),
        (tarfile.FIFOTYPE, ""),
        (tarfile.CHRTYPE, ""),
        (tarfile.BLKTYPE, ""),
    ],
)
def test_non_regular_tar_members_are_refused_by_importer_and_store(tmp_path: Path, kind: bytes, linkname: str) -> None:
    manifest, blob = _packet_bundle(AGENT, REGISTERED_STREAM)
    members = th._bundle_extract(blob)[1]
    special = tarfile.TarInfo(".agent/thread-rollovers/claude-infra/lineage-store/special")
    special.type = kind
    special.linkname = linkname
    special_blob = _special_member_blob(manifest, members, special)

    with pytest.raises(ValueError, match="non-regular"):
        th._bundle_extract(special_blob)
    store, lease = _store(tmp_path)
    with pytest.raises(ValueError, match="non-regular"):
        store.upload_rollover_bundle(lease, manifest=manifest, blob=special_blob)
    assert store.list_rollover_bundles(REGISTERED_STREAM) == []


@pytest.mark.parametrize(
    "name",
    [
        "/etc/example",
        ".agent/thread-rollovers/claude-infra/lineage-store/../../../../escape.md",
        "..\\escape.md",
    ],
)
def test_absolute_and_parent_member_paths_are_refused_by_importer_and_store(tmp_path: Path, name: str) -> None:
    from agents_extensions.shared.session_streams.store import validate_rollover_bundle_members

    with pytest.raises(ValueError):
        th._bundle_member_path(name)
    with pytest.raises(ValueError, match="member path"):
        validate_rollover_bundle_members(
            [name], agent=AGENT, lineage_id="lineage-store", handoff_candidates=(HANDOFF_PATH,)
        )


def test_duplicate_tar_member_is_refused(tmp_path: Path) -> None:
    manifest, blob = _packet_bundle(AGENT, REGISTERED_STREAM)
    members = th._bundle_extract(blob)[1]
    name, payload = next(iter(members.items()))
    duplicate = tarfile.TarInfo(name)
    duplicate.size = len(payload)
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w") as archive:
        manifest_bytes = th._bundle_json(manifest)
        info = tarfile.TarInfo(th.ROLLOVER_BUNDLE_MANIFEST_NAME)
        info.size = len(manifest_bytes)
        archive.addfile(info, io.BytesIO(manifest_bytes))
        for _ in range(2):
            archive.addfile(duplicate, io.BytesIO(payload))

    with pytest.raises(ValueError, match="duplicate"):
        th._bundle_extract(gzip.compress(raw.getvalue()))


def _raw_bundle(entries: list[tuple[str, bytes]]) -> bytes:
    """A gzip tar holding exactly ``entries`` in order, with no validation."""
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w") as archive:
        for name, payload in entries:
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))
    return gzip.compress(raw.getvalue())


def _parity_case(case: str) -> tuple[dict, bytes]:
    """The supplied manifest and archive for one bundle the store and the HTTP route must both refuse."""
    manifest, blob = _packet_bundle(AGENT, REGISTERED_STREAM)
    (name, payload), *_ = th._bundle_extract(blob)[1].items()
    manifest_bytes = th._bundle_json(manifest)
    twice = {**manifest, "files": manifest["files"] * 2}
    if case == "foreign-embedded-agent":
        embedded, foreign_blob = _resign({**manifest, "agent": "claude-devops"}, {name: payload})
        return {**embedded, "agent": AGENT}, foreign_blob
    if case == "duplicate-member":
        return twice, _raw_bundle([("manifest.json", manifest_bytes), (name, payload), (name, payload)])
    if case == "normalized-duplicate-member":
        return twice, _raw_bundle([("manifest.json", manifest_bytes), (name, payload), (f"./{name}", payload)])
    if case == "checksum-mismatch":
        return manifest, _raw_bundle([("manifest.json", manifest_bytes), (name, b"not the declared bytes\n")])
    if case == "missing-embedded-manifest":
        return manifest, _raw_bundle([(name, payload)])
    if case == "duplicate-embedded-manifest":
        return manifest, _raw_bundle(
            [("manifest.json", manifest_bytes), ("manifest.json", manifest_bytes), (name, payload)]
        )
    if case == "truncated-archive":
        return manifest, blob[: len(blob) // 2]
    raise AssertionError(case)


@pytest.mark.parametrize(
    ("case", "reason"),
    [
        ("foreign-embedded-agent", "differs from the embedded manifest at agent"),
        ("duplicate-member", "duplicate or non-regular member"),
        ("normalized-duplicate-member", "duplicate or non-regular member"),
        ("checksum-mismatch", "member fingerprint mismatch"),
        ("missing-embedded-manifest", "has no embedded manifest"),
        ("duplicate-embedded-manifest", "duplicate embedded manifest"),
        ("truncated-archive", "not a valid tar.gz"),
    ],
)
def test_direct_store_upload_and_http_route_refuse_the_same_bundle_for_the_same_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str, reason: str
) -> None:
    from fastapi.testclient import TestClient

    from agents_extensions.shared.session_streams.db import SessionStreamDatabase
    from agents_extensions.shared.session_streams.store import SessionStreamStore
    from tests.epics_monitor_stub import epics_app_for_store

    manifest, blob = _parity_case(case)
    direct_root = tmp_path / "direct"
    direct_root.mkdir()
    store, lease = _store(direct_root)
    for _attempt in range(2):
        with pytest.raises(ValueError, match=reason) as direct:
            store.upload_rollover_bundle(lease, manifest=manifest, blob=blob)
    assert store.list_rollover_bundles(REGISTERED_STREAM) == []

    api_root = tmp_path / "api"
    api_root.mkdir()
    api_store = SessionStreamStore(SessionStreamDatabase(api_root / "streams.sqlite3"))
    refused: list[BaseException] = []
    upload = api_store.upload_rollover_bundle

    def recording_upload(*args: object, **kwargs: object) -> dict:
        try:
            return upload(*args, **kwargs)
        except BaseException as exc:
            refused.append(exc)
            raise

    monkeypatch.setattr(api_store, "upload_rollover_bundle", recording_upload)
    client = TestClient(
        epics_app_for_store(api_store, api_root), base_url="http://127.0.0.1", client=("127.0.0.1", 8765)
    )
    claim = client.post(
        f"/api/epics/v1/{REGISTERED_STREAM}/claim",
        json={
            "session_id": "parity-session",
            "lease_id": "parity-lease",
            "lineage_id": "parity-lineage",
            "agent": "claude",
            "harness": "claude-cli",
            "instance_id": "parity-instance",
            "process_id": 1234,
            "host_id": "parity-host",
            "ttl_seconds": 900,
        },
    )
    assert claim.status_code == 200, claim.text
    response = client.post(
        f"/api/epics/v1/{REGISTERED_STREAM}/bundles",
        json={**claim.json()["lease"], "manifest": manifest, "blob": base64.b64encode(blob).decode("ascii")},
    )

    assert response.status_code == 400, response.text
    assert [(type(exc), str(exc)) for exc in refused] == [(type(direct.value), str(direct.value))]
    assert api_store.list_rollover_bundles(REGISTERED_STREAM) == []


def test_direct_store_upload_refuses_a_secret_bearing_member_leaving_no_row(tmp_path: Path) -> None:
    store, lease = _store(tmp_path)
    manifest, blob = _packet_bundle(AGENT, REGISTERED_STREAM, extra={HANDOFF_PATH: b"api-key: supersecret-value\n"})

    with pytest.raises(ContentRejectedError, match="credential-assignment"):
        store.upload_rollover_bundle(lease, manifest=manifest, blob=blob)
    assert store.list_rollover_bundles(REGISTERED_STREAM) == []


class _AppTransport:
    """MonitorClient-shaped adapter that sends bundle traffic to the in-process API."""

    def __init__(self, client) -> None:
        self.client = client

    def get(self, path: str, *, headers: dict | None = None) -> tuple[int, str, dict]:
        response = self.client.get(path, headers=headers or {})
        return response.status_code, response.text, dict(response.headers)

    def post(self, path: str, *, json_body=None, headers: dict | None = None, **_kwargs) -> tuple[int, str, dict]:
        response = self.client.post(path, json=json_body, headers=headers or {})
        return response.status_code, response.text, dict(response.headers)


def test_export_upload_import_round_trip_creates_only_lineage_handoff_and_receipt(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from fastapi.testclient import TestClient

    from agents_extensions.shared.session_streams.db import SessionStreamDatabase
    from agents_extensions.shared.session_streams.store import SessionStreamStore
    from tests.epics_monitor_stub import epics_app_for_store

    api_root = tmp_path / "api"
    api_root.mkdir()
    store = SessionStreamStore(SessionStreamDatabase(api_root / "streams.sqlite3"))
    client = TestClient(epics_app_for_store(store, api_root), base_url="http://127.0.0.1", client=("127.0.0.1", 8765))
    claim = client.post(
        f"/api/epics/v1/{REGISTERED_STREAM}/claim",
        json={
            "session_id": "round-trip-session",
            "lease_id": "round-trip-lease",
            "lineage_id": "round-trip-lineage",
            "agent": "claude",
            "harness": "claude-code",
            "instance_id": "round-trip-instance",
            "process_id": 1234,
            "host_id": "round-trip-host",
            "ttl_seconds": 900,
        },
    )
    assert claim.status_code == 200, claim.text
    lease = claim.json()["lease"]
    for name, value in {
        "SESSION_STREAM_SESSION_ID": lease["session_id"],
        "SESSION_STREAM_LEASE_ID": lease["lease_id"],
        "SESSION_STREAM_GENERATION": str(lease["generation"]),
        "SESSION_STREAM_FENCING_TOKEN": str(lease["fencing_token"]),
        "SESSION_STREAM_PROCESS_ID": "1234",
        "SESSION_STREAM_AGENT": "claude",
        "SESSION_STREAM_HARNESS": "claude-code",
        "SESSION_STREAM_INSTANCE_ID": "round-trip-instance",
        "LU_MONITOR_HOST_ID": "round-trip-host",
    }.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(th, "_bundle_client", lambda *_a, **_kw: _AppTransport(client))

    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    _with_registry(source)
    _with_registry(target)
    state = _seed_state(source, thread_id="round-trip-thread")
    bundle = tmp_path / "round-trip.tgz"
    assert th.cmd_export_bundle(_export_args(source, state, bundle, upload=True, stream=REGISTERED_STREAM)) == 0
    exported = json.loads(capsys.readouterr().out)
    assert exported["upload"] == "uploaded", exported
    _manifest, members = th._bundle_extract(bundle.read_bytes())
    before = _tree(target)

    assert th.cmd_import_bundle(_import_args(target, None, from_api=REGISTERED_STREAM, stream=REGISTERED_STREAM)) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "installed"

    after = _tree(target)
    assert {name: after[name] for name in before} == before
    lineage = f".agent/thread-rollovers/{AGENT}/{state['lineage_id']}/"
    handoffs = [name for name in members if not name.startswith(lineage)]
    assert handoffs == [HANDOFF_PATH]
    receipt = f".agent/thread-rollovers/{AGENT}/_bundle-receipts/{state['lineage_id']}.json"
    allowed_files = {*members, receipt}
    allowed_dirs = {parent.as_posix() for name in allowed_files for parent in Path(name).parents if parent.parts}
    for name in after.keys() - before.keys():
        assert name in (allowed_files if after[name] is not None else allowed_dirs), name
    for name in members:
        assert (target / name).is_file(), name
    assert (target / receipt).is_file()
    assert (target / HANDOFF_PATH).read_text(encoding="utf-8") == f"lane handoff source checkout: {target.resolve()}\n"


# Names and values below are deliberately recognizable in diagnostics.
BOUND_SENTINEL = "bundle-supplied-sentinel"
BOUND_MEMBER = f".agent/thread-rollovers/{AGENT}/lineage-store/{BOUND_SENTINEL}.md"

HOSTILE_TIMESTAMPS = (
    "9999-12-31T23:59:59-23:59",
    "0001-01-01T00:00:00+23:59",
    "2026-08-24T16:00:00+24:00",
    "0000-01-01T00:00:00Z",
    "10000-01-01T00:00:00Z",
    "2026-08-24T16:00:60Z",
    "2026-08-24\ud80016:00:00Z",
    "2026-08-24\x0016:00:00Z",
)
TIMESTAMP_FIELDS = (
    ("manifest", "prepared_at"),
    ("manifest", "exported_at"),
    ("lease", "created_at"),
    ("lease", "updated_at"),
    ("lease", "expires_at"),
    ("lease", "acquired_at"),
    ("lease", "heartbeat_at"),
    ("lease", "active.started_at"),
    ("lease", "active.last_seen_at"),
    ("lease", "replacement.prepared_at"),
    ("lease", "replacement.updated_at"),
    ("lease", "replacement.confirmed_at"),
)


@pytest.mark.parametrize("entry_point", ["importer", "store", "http"])
@pytest.mark.parametrize("member,field", TIMESTAMP_FIELDS)
def test_bundle_timestamp_conversion_refusal(tmp_path, capsys, entry_point, member, field):
    # Exercise every malformed shape in each field so each test also reproduces
    # the UTC range escape, rather than only rechecking previously refused syntax.
    for index, timestamp in enumerate(HOSTILE_TIMESTAMPS):
        case = tmp_path / str(index)
        case.mkdir()
        source = case / "source"
        source.mkdir()
        state = _seed_state(source, thread_id="source-thread")
        manifest, blob, _hits = th._build_rollover_bundle(
            source, source, agent=AGENT, state=state, stream_id=REGISTERED_STREAM
        )
        members = th._bundle_extract(blob)[1]
        if member == "manifest":
            manifest[field] = timestamp
        else:
            name = th.default_state_path(AGENT, state["lineage_id"]).as_posix()
            value = json.loads(members[name])
            parent = value
            parts = field.split(".")
            for part in parts[:-1]:
                parent = parent[part]
            parent[parts[-1]] = timestamp
            members[name] = json.dumps(value, ensure_ascii=True).encode()
        if member != "manifest" or "\ud800" not in timestamp:
            manifest, _ = _resign(manifest, members)
        # Serialize with escaped Unicode independently of production converters.
        # An invalid timestamp must be refused before its digest is consulted.
        blob = _raw_bundle(
            [
                (th.ROLLOVER_BUNDLE_MANIFEST_NAME, json.dumps(manifest, ensure_ascii=True).encode()),
                *members.items(),
            ]
        )
        _assert_bundle_refused_at_entry_point(case, capsys, entry_point, manifest, blob)
        with pytest.raises(ValueError, match=r"^bundle conversion is invalid$"):
            th._bundle_load_json(json.dumps({"prepared_at": timestamp}).encode())


@pytest.mark.parametrize("entry_point", ["importer", "store", "http"])
@pytest.mark.parametrize("member", ["manifest", "lease", "handoff_state"])
def test_bundle_unicode_conversion_refusal(tmp_path, capsys, entry_point, member):
    source = tmp_path / "source"
    source.mkdir()
    state = _seed_state(source, thread_id="source-thread")
    manifest, blob, _hits = th._build_rollover_bundle(
        source, source, agent=AGENT, state=state, stream_id=REGISTERED_STREAM
    )
    members = th._bundle_extract(blob)[1]
    if member == "manifest":
        manifest["unused"] = "\ud800"
    else:
        name = (
            th.default_state_path(AGENT, state["lineage_id"]).as_posix()
            if member == "lease"
            else state["replacement"]["semantic_snapshot_path"]
        )
        value = json.loads(members.get(name, b"{}"))
        value["unused"] = "\ud800"
        members[name] = json.dumps(value).encode()
        manifest, _ = _resign(manifest, members)
    blob = _raw_bundle([(th.ROLLOVER_BUNDLE_MANIFEST_NAME, json.dumps(manifest).encode()), *members.items()])
    _assert_bundle_refused_at_entry_point(tmp_path, capsys, entry_point, manifest, blob)
    with pytest.raises(ValueError, match=r"^bundle conversion is invalid$"):
        th._bundle_load_json(b'{"unused": "\\ud800"}')


@pytest.mark.parametrize(
    "member,field",
    [
        ("manifest", "generation"),
        ("manifest", "upload_seq"),
        ("manifest", "files.0.bytes"),
        ("manifest", "prepared_at"),
        ("manifest", "exported_at"),
        ("lease", "schema_version"),
        ("lease", "active.generation"),
        ("lease", "replacement.generation"),
        ("lease", "bundle_upload_seq"),
        ("lease", "owner_pid"),
        ("lease", "owner_pid_started_at"),
        ("lease", "last_handoff.context_percent"),
        ("lease", "created_at"),
        ("lease", "updated_at"),
        ("lease", "expires_at"),
        ("lease", "active.started_at"),
        ("lease", "active.last_seen_at"),
        ("lease", "replacement.prepared_at"),
    ],
)
def test_bundle_converted_field_sweep(member, field):
    # Every converted field goes through the JSON boundary, including optional
    # lease data used by later consumers. A lone surrogate is not UTF-8 data.
    value = "\ud800"
    for part in reversed(field.split(".")):
        value = [value] if part == "0" else {part: value}
    with pytest.raises(ValueError, match=r"^bundle conversion is invalid$"):
        th._bundle_load_json(json.dumps({member: value}).encode())


@pytest.mark.parametrize(
    "error_type", [ValueError, OverflowError, RecursionError, UnicodeError, ArithmeticError, TypeError]
)
def test_bundle_conversion_errors_are_one_sanitized_refusal(error_type):
    with pytest.raises(ValueError, match=r"^bundle conversion is invalid$") as refusal:
        with th._bundle_conversion():
            raise error_type(BOUND_SENTINEL)
    assert refusal.value.__suppress_context__


@pytest.mark.parametrize("error_type", [MemoryError, RuntimeError, OSError])
def test_bundle_conversion_server_errors_propagate(error_type):
    with pytest.raises(error_type, match=BOUND_SENTINEL):
        with th._bundle_conversion():
            raise error_type(BOUND_SENTINEL)


@pytest.mark.parametrize("conversion", [
    lambda: int(float("inf")),
    lambda: float("invalid"),
    lambda: Decimal("invalid"),
    lambda: base64.b64decode(b"!", validate=True),
    lambda: bytes.fromhex("invalid"),
    lambda: json.loads("1" * 5000),
    lambda: "\ud800".encode("utf-8"),
    lambda: datetime.fromisoformat("9999-12-31T23:59:59-23:59").astimezone(UTC),
], ids=["int", "float", "decimal", "base64", "hex", "json-number", "unicode", "utc"])
def test_bundle_actual_stdlib_conversion_refusal(conversion):
    with pytest.raises(ValueError, match=r"^bundle conversion is invalid$"):
        with th._bundle_conversion():
            conversion()


@pytest.mark.parametrize("entry_point", ["importer", "store", "http"])
def test_bundle_collection_conversion_refusal(tmp_path, capsys, entry_point):
    for index, (field, value) in enumerate([
        ("status", []), ("status", {}), ("tokenized_members", [{}]),
    ]):
        case = tmp_path / str(index)
        case.mkdir()
        manifest, blob = _packet_bundle(AGENT, REGISTERED_STREAM)
        members = th._bundle_extract(blob)[1]
        manifest[field] = value
        blob = th._bundle_archive(members, manifest)
        _assert_bundle_refused_at_entry_point(case, capsys, entry_point, manifest, blob)
        with pytest.raises(ValueError):
            th.verify_rollover_bundle(blob, repo_root=REPO_ROOT)


def _assert_bundle_refused_at_entry_point(tmp_path, capsys, entry_point, manifest, blob, *, raw_manifest=None):
    if entry_point == "importer":
        target = tmp_path / "target"
        target.mkdir()
        (target / "kept.txt").write_text("unchanged\n", encoding="utf-8")
        before = _tree(target)
        bundle = tmp_path / "refused.tgz"
        bundle.write_bytes(blob)
        assert th.cmd_import_bundle(_import_args(target, bundle, stream=REGISTERED_STREAM)) == 2
        refusal = json.loads(capsys.readouterr().out)
        assert refusal["code"] == "invalid_rollover_bundle"
        assert refusal["action"] == "import-bundle"
        assert BOUND_SENTINEL not in refusal["error"]
        assert _tree(target) == before
        return

    store, lease = _store(tmp_path)
    if entry_point == "store":
        with pytest.raises(ValueError) as refusal:
            store.upload_rollover_bundle(lease, manifest=manifest, blob=blob)
        assert BOUND_SENTINEL not in str(refusal.value)
    else:
        from dataclasses import asdict

        from fastapi.testclient import TestClient

        from tests.epics_monitor_stub import epics_app_for_store

        client = TestClient(
            epics_app_for_store(store, tmp_path), base_url="http://127.0.0.1", client=("127.0.0.1", 8765)
        )
        request_body = client.app.openapi()["paths"]["/api/epics/v1/{stream_id}/bundles"]["post"]["requestBody"]
        assert request_body["required"] is True
        assert request_body["content"]["application/json"]["schema"]["type"] == "object"
        body = {**asdict(lease), **asdict(lease.holder), "blob": base64.b64encode(blob).decode("ascii")}
        raw_body = json.dumps(body)[:-1] + ', "manifest": ' + (raw_manifest or json.dumps(manifest)) + "}"
        response = client.post(
            f"/api/epics/v1/{REGISTERED_STREAM}/bundles",
            content=raw_body,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400, response.text
        assert response.json()["error"] == "request_refused"
        assert response.json()["detail"] == "invalid rollover bundle upload request"
    assert store.list_rollover_bundles(REGISTERED_STREAM) == []


@pytest.mark.parametrize("entry_point", ["importer", "store", "http"])
@pytest.mark.parametrize("member", ["manifest", "lease", "handoff_state"])
@pytest.mark.parametrize(
    "invalid", ["nested", "syntax", "encoding", "integer", "NaN", "Infinity", "-Infinity", "overflow"]
)
def test_bundle_json_refusal_parity(tmp_path, capsys, entry_point, member, invalid):
    source = tmp_path / "source"
    source.mkdir()
    state = _seed_state(source, thread_id="source-thread")
    manifest, blob, _hits = th._build_rollover_bundle(
        source, source, agent=AGENT, state=state, stream_id=REGISTERED_STREAM
    )
    members = th._bundle_extract(blob)[1]
    nonfinite = invalid in {"NaN", "Infinity", "-Infinity", "overflow"}
    payload = {
        "nested": b"[" * 30000 + b"]" * 30000,
        "syntax": b"{",
        "encoding": b"\xff",
        "integer": b"1" * 5000,
    }.get(invalid, b'{"unused": ' + ("1e999" if invalid == "overflow" else invalid).encode() + b"}")
    if member == "manifest":
        if nonfinite:
            payload = th._bundle_json(manifest)[:-1] + b', "unused": ' + payload[len(b'{"unused": '):]
        blob = _raw_bundle([(th.ROLLOVER_BUNDLE_MANIFEST_NAME, payload), *members.items()])
    else:
        name = (
            th.default_state_path(AGENT, state["lineage_id"]).as_posix()
            if member == "lease"
            else state["replacement"]["semantic_snapshot_path"]
        )
        if nonfinite and member == "lease":
            payload = members[name].rstrip()[:-1] + b', "unused": ' + payload[len(b'{"unused": '):]
        members[name] = payload
        manifest, blob = _resign(manifest, members)
    _assert_bundle_refused_at_entry_point(tmp_path, capsys, entry_point, manifest, blob)


@pytest.mark.parametrize("entry_point", ["store", "http"])
@pytest.mark.parametrize("invalid", ["nested", "NaN", "Infinity", "-Infinity", "overflow"])
def test_supplied_manifest_json_refusal(tmp_path, capsys, entry_point, invalid):
    manifest, blob = _packet_bundle(AGENT, REGISTERED_STREAM)
    raw_value = "[" * 30000 + "]" * 30000 if invalid == "nested" else ("1e999" if invalid == "overflow" else invalid)
    raw_manifest = json.dumps(manifest)[:-1] + ', "unused": ' + raw_value + "}"
    if invalid == "nested":
        value = []
        for _ in range(30000):
            value = [value]
    else:
        value = json.loads(raw_value)
    manifest["unused"] = value
    _assert_bundle_refused_at_entry_point(tmp_path, capsys, entry_point, manifest, blob, raw_manifest=raw_manifest)


@pytest.mark.parametrize("entry_point", ["importer", "store", "http"])
@pytest.mark.parametrize("field", ["generation", "upload_seq"])
@pytest.mark.parametrize(
    "raw_value",
    ["Infinity", "-Infinity", "1e999", "NaN", "1.5", "9223372036854775808", "1" * 5000],
    ids=["positive-infinity", "negative-infinity", "exponent-overflow", "nan", "fraction", "integer-range", "integer-digits"],
)
def test_manifest_numeric_field_refusal(tmp_path, capsys, entry_point, field, raw_value):
    source = tmp_path / "source"
    source.mkdir()
    state = _seed_state(source, thread_id="source-thread", generation=1)
    manifest, blob, _hits = th._build_rollover_bundle(
        source, source, agent=AGENT, state=state, stream_id=REGISTERED_STREAM
    )
    members = th._bundle_extract(blob)[1]
    # Construct the large Python integer without relaxing the parser's digit cap.
    manifest[field] = (10**5000 - 1) // 9 if len(raw_value) == 5000 else json.loads(raw_value)
    if entry_point == "importer" and len(raw_value) != 5000:
        manifest["bundle_sha256"] = th._bundle_digest(members, manifest)
    remaining = {key: value for key, value in manifest.items() if key != field}
    raw_manifest = json.dumps(remaining)[:-1] + f', "{field}": ' + raw_value + "}"
    if entry_point == "importer":
        blob = _raw_bundle([(th.ROLLOVER_BUNDLE_MANIFEST_NAME, raw_manifest.encode()), *members.items()])
    _assert_bundle_refused_at_entry_point(tmp_path, capsys, entry_point, manifest, blob, raw_manifest=raw_manifest)


@pytest.mark.parametrize("entry_point", ["importer", "store", "http"])
def test_embedded_manifest_duplicate_key_refusal(tmp_path, capsys, entry_point):
    source = tmp_path / "source"
    source.mkdir()
    state = _seed_state(source, thread_id="source-thread")
    manifest, blob, _hits = th._build_rollover_bundle(
        source, source, agent=AGENT, state=state, stream_id=REGISTERED_STREAM
    )
    members = th._bundle_extract(blob)[1]
    raw_manifest = b'{"agent":"' + BOUND_SENTINEL.encode() + b'",' + th._bundle_json(manifest)[1:]
    blob = _raw_bundle([(th.ROLLOVER_BUNDLE_MANIFEST_NAME, raw_manifest), *members.items()])
    _assert_bundle_refused_at_entry_point(tmp_path, capsys, entry_point, manifest, blob)


@pytest.mark.parametrize("generation", [1, 2**63 - 1])
@pytest.mark.parametrize("upload_seq", [0, 2**63 - 1])
def test_manifest_numeric_boundaries_remain_orderable(generation, upload_seq):
    manifest, _blob = _packet_bundle(AGENT, REGISTERED_STREAM)
    manifest.update(generation=generation, upload_seq=upload_seq)
    order = th._bundle_order(manifest)
    assert order[0] == generation
    assert order[-1] == upload_seq


@pytest.mark.parametrize("entry_point", ["importer", "store", "http"])
@pytest.mark.parametrize(
    "runtime_name",
    [
        ".native-intent.lock",
        "nested/.native-intent.lock",
        "remote.bundle.tgz",
        "nested/remote.bundle.tgz",
        "_bundle-reconcile",
        "nested/_bundle-reconcile/receipt.json",
        ".NATIVE-INTENT.LOCK",
        "REMOTE.BUNDLE.TGZ",
        "nested/_BUNDLE-RECONCILE/receipt.json",
    ],
)
def test_export_excluded_member_refusal_parity(tmp_path, capsys, entry_point, runtime_name):
    source = tmp_path / "source"
    source.mkdir()
    state = _seed_state(source, thread_id="source-thread")
    manifest, blob, _hits = th._build_rollover_bundle(
        source, source, agent=AGENT, state=state, stream_id=REGISTERED_STREAM
    )
    members = th._bundle_extract(blob)[1]
    name = f".agent/thread-rollovers/{AGENT}/{state['lineage_id']}/{runtime_name}"
    members[name] = b"{}\n"
    manifest, blob = _resign(manifest, members)
    _assert_bundle_refused_at_entry_point(tmp_path, capsys, entry_point, manifest, blob)


def _assert_bundle_refused_everywhere(tmp_path, monkeypatch, capsys, manifest, blob, reason):
    from fastapi.testclient import TestClient

    from tests.epics_monitor_stub import epics_app_for_store

    target = tmp_path / "target"
    target.mkdir()
    (target / "kept.txt").write_text("unchanged\n", encoding="utf-8")
    before = _tree(target)
    bundle = tmp_path / "refused.tgz"
    bundle.write_bytes(blob)
    assert th.cmd_import_bundle(_import_args(target, bundle, stream=REGISTERED_STREAM)) == 2
    refusal = json.loads(capsys.readouterr().out)
    assert reason in refusal["error"]
    assert BOUND_SENTINEL not in refusal["error"]
    assert _tree(target) == before

    direct_root = tmp_path / "direct"
    direct_root.mkdir()
    store, lease = _store(direct_root)
    with pytest.raises((ValueError, ContentRejectedError)) as direct:
        store.upload_rollover_bundle(lease, manifest=manifest, blob=blob)
    assert ("status is invalid" if reason == "not bundle-orderable" else reason) in str(direct.value)
    assert BOUND_SENTINEL not in str(direct.value)
    assert store.list_rollover_bundles(REGISTERED_STREAM) == []

    api_root = tmp_path / "api"
    api_root.mkdir()
    api_store, api_lease = _store(api_root)
    client = TestClient(
        epics_app_for_store(api_store, api_root), base_url="http://127.0.0.1", client=("127.0.0.1", 8765)
    )
    from dataclasses import asdict

    errors = []
    upload = api_store.upload_rollover_bundle

    def record_upload(*args, **kwargs):
        try:
            return upload(*args, **kwargs)
        except (ValueError, ContentRejectedError) as exc:
            errors.append(str(exc))
            raise

    monkeypatch.setattr(api_store, "upload_rollover_bundle", record_upload)
    response = client.post(
        f"/api/epics/v1/{REGISTERED_STREAM}/bundles",
        json={
            **asdict(api_lease),
            **asdict(api_lease.holder),
            "manifest": manifest,
            "blob": base64.b64encode(blob).decode("ascii"),
        },
    )
    assert response.status_code == 400, response.text
    assert BOUND_SENTINEL not in response.text
    assert errors == [str(direct.value)]
    assert api_store.list_rollover_bundles(REGISTERED_STREAM) == []


@pytest.mark.parametrize("case", ["member", "aggregate", "stream", "count", "manifest", "casefold"])
def test_expanded_bounds_refuse_without_rows_or_installation(tmp_path, monkeypatch, capsys, case):
    extra = {BOUND_MEMBER: b"safe\n"}
    reason = "expanded"
    if case == "member":
        extra[BOUND_MEMBER] = b"x" * (8 * 1024 * 1024)
    elif case == "aggregate":
        monkeypatch.setattr(th, "ROLLOVER_BUNDLE_MAX_EXPANDED_BYTES", 4096, raising=False)
        extra = {f"{BOUND_MEMBER}.{i}": b"x" * 1024 for i in range(8)}
        reason = "aggregate expanded limit"
    elif case == "count":
        monkeypatch.setattr(th, "ROLLOVER_BUNDLE_MAX_MEMBERS", 4, raising=False)
        extra = {f"{BOUND_MEMBER}.{i}": b"safe\n" for i in range(4)}
        reason = "member count limit"
    elif case == "manifest":
        monkeypatch.setattr(th, "ROLLOVER_BUNDLE_MAX_MANIFEST_BYTES", 512, raising=False)
        reason = "manifest size limit"
    elif case == "casefold":
        extra[BOUND_MEMBER.replace(BOUND_SENTINEL, BOUND_SENTINEL.upper())] = b"other\n"
        reason = "duplicate or non-regular member"
    manifest, blob = _packet_bundle(AGENT, REGISTERED_STREAM, extra=extra)
    if case == "stream":
        # All tar headers declare small payloads. The gzip stream expands far
        # beyond them, even after tar's end marker; tarfile alone ignores it.
        blob = gzip.compress(gzip.decompress(blob) + b"\0" * (8 * 1024 * 1024))
        reason = "expanded archive limit"
    _assert_bundle_refused_everywhere(tmp_path, monkeypatch, capsys, manifest, blob, reason)


@pytest.mark.parametrize("case", ["allowlist", "path", "fingerprint", "tokenization", "status", "parser", "timestamp"])
def test_refusal_diagnostics_never_echo_bundle_strings(tmp_path, monkeypatch, capsys, case):
    manifest, blob = _packet_bundle(AGENT, REGISTERED_STREAM, extra={BOUND_MEMBER: b"safe\n"})
    members = th._bundle_extract(blob)[1]
    reason = {
        "allowlist": "outside its lineage",
        "path": "path is unsafe",
        "fingerprint": "fingerprint mismatch",
        "tokenization": "tokenization declaration",
        "status": "not bundle-orderable",
        "parser": "not a valid tar.gz",
        "timestamp": "bundle conversion is invalid",
    }[case]
    if case == "allowlist":
        manifest, blob = _resign(manifest, {f"{BOUND_SENTINEL}.md": b"safe\n"})
    elif case == "path":
        blob = _raw_bundle([("manifest.json", th._bundle_json(manifest)), (f"../{BOUND_SENTINEL}.md", b"safe\n")])
    elif case == "fingerprint":
        members[BOUND_MEMBER] = b"different\n"
        blob = th._bundle_archive(members, manifest)
    elif case == "tokenization":
        next(item for item in manifest["files"] if item["path"] == BOUND_MEMBER)["tokenized"] = False
        blob = th._bundle_archive(members, manifest)
    elif case == "status":
        manifest["status"] = BOUND_SENTINEL
        blob = th._bundle_archive(members, manifest)
    elif case == "timestamp":
        manifest["prepared_at"] = BOUND_SENTINEL
        blob = th._bundle_archive(members, manifest)
    else:

        def failed_parser(*_args, **_kwargs):
            raise tarfile.ReadError(BOUND_SENTINEL)

        monkeypatch.setattr(th.tarfile, "open", failed_parser)
    _assert_bundle_refused_everywhere(tmp_path, monkeypatch, capsys, manifest, blob, reason)


@pytest.mark.parametrize(
    ("payload", "rule"), [(b"api-key: supersecret-value\n", "credential-assignment"), (b"\xff", "invalid-utf8-text")]
)
def test_secret_scan_refusal_never_echoes_member_name(tmp_path, monkeypatch, payload, rule):
    store, lease = _store(tmp_path)
    manifest, blob = _packet_bundle(AGENT, REGISTERED_STREAM, extra={BOUND_MEMBER: payload})
    with pytest.raises(ContentRejectedError, match=rule) as refusal:
        store.upload_rollover_bundle(lease, manifest=manifest, blob=blob)
    assert BOUND_SENTINEL not in str(refusal.value)
    assert "supersecret-value" not in str(refusal.value)
    assert store.list_rollover_bundles(REGISTERED_STREAM) == []

    from dataclasses import asdict

    from fastapi.testclient import TestClient

    from tests.epics_monitor_stub import epics_app_for_store

    errors = []
    upload = store.upload_rollover_bundle

    def record_upload(*args, **kwargs):
        try:
            return upload(*args, **kwargs)
        except ContentRejectedError as exc:
            errors.append(str(exc))
            raise

    monkeypatch.setattr(store, "upload_rollover_bundle", record_upload)
    client = TestClient(epics_app_for_store(store, tmp_path), base_url="http://127.0.0.1", client=("127.0.0.1", 8765))
    response = client.post(
        f"/api/epics/v1/{REGISTERED_STREAM}/bundles",
        json={
            **asdict(lease),
            **asdict(lease.holder),
            "manifest": manifest,
            "blob": base64.b64encode(blob).decode("ascii"),
        },
    )
    assert response.status_code == 400
    assert BOUND_SENTINEL not in response.text
    assert errors == [str(refusal.value)]
    assert store.list_rollover_bundles(REGISTERED_STREAM) == []


def test_maximum_member_round_trips_and_next_byte_is_refused(tmp_path, monkeypatch, capsys):
    source = tmp_path / "source"
    source.mkdir()
    target = tmp_path / "target"
    target.mkdir()
    state = _seed_state(source, thread_id="source-thread")
    extra = source / ".agent/thread-rollovers" / AGENT / state["lineage_id"] / f"{BOUND_SENTINEL}.md"
    limit = getattr(th, "ROLLOVER_BUNDLE_MAX_MEMBER_BYTES", 1024 * 1024)
    extra.write_bytes(b"x" * limit)
    bundle = tmp_path / "maximum.tgz"
    assert th.cmd_export_bundle(_export_args(source, state, bundle, stream=REGISTERED_STREAM)) == 0
    capsys.readouterr()
    manifest, members = th.verify_rollover_bundle(bundle.read_bytes(), repo_root=source)
    store, lease = _store(tmp_path)
    stored = store.upload_rollover_bundle(lease, manifest=manifest, blob=bundle.read_bytes())
    assert stored["blob"] == bundle.read_bytes()
    assert th.cmd_import_bundle(_import_args(target, bundle, stream=REGISTERED_STREAM)) == 0
    capsys.readouterr()
    assert (target / extra.relative_to(source)).read_bytes() == b"x" * limit
    members[extra.relative_to(source).as_posix()] += b"x"
    _, over_limit = _resign(manifest, members)
    with pytest.raises(ValueError, match="expanded member limit"):
        th.verify_rollover_bundle(over_limit, repo_root=source)


def test_member_reader_enforces_cap_when_size_header_understates_output(tmp_path, monkeypatch, capsys):
    manifest, blob = _packet_bundle(AGENT, REGISTERED_STREAM, extra={BOUND_MEMBER: b"small"})
    monkeypatch.setattr(th, "ROLLOVER_BUNDLE_MAX_MEMBER_BYTES", 16, raising=False)
    extract = tarfile.TarFile.extractfile

    def understated_member(archive, member):
        if member.name == BOUND_MEMBER:
            return io.BytesIO(b"x" * 17)
        return extract(archive, member)

    monkeypatch.setattr(tarfile.TarFile, "extractfile", understated_member)
    _assert_bundle_refused_everywhere(tmp_path, monkeypatch, capsys, manifest, blob, "expanded member limit")


@pytest.mark.parametrize("dimension", ["aggregate", "manifest", "count"])
def test_exact_expanded_boundary_accepts_and_next_unit_refuses(monkeypatch, dimension):
    manifest, blob = _packet_bundle(AGENT, REGISTERED_STREAM, extra={BOUND_MEMBER: b"safe\n"})
    members = th._bundle_extract(blob)[1]
    manifest_bytes = len(th._bundle_json(manifest))
    constant, limit = {
        "aggregate": ("ROLLOVER_BUNDLE_MAX_EXPANDED_BYTES", manifest_bytes + sum(map(len, members.values()))),
        "manifest": ("ROLLOVER_BUNDLE_MAX_MANIFEST_BYTES", manifest_bytes),
        "count": ("ROLLOVER_BUNDLE_MAX_MEMBERS", len(members) + 1),
    }[dimension]
    monkeypatch.setattr(th, constant, limit, raising=False)
    assert th.verify_rollover_bundle(blob, repo_root=REPO_ROOT) == (manifest, members)
    monkeypatch.setattr(th, constant, limit - 1, raising=False)
    with pytest.raises(
        ValueError,
        match={
            "aggregate": "aggregate expanded limit",
            "manifest": "manifest size limit",
            "count": "member count limit",
        }[dimension],
    ):
        th.verify_rollover_bundle(blob, repo_root=REPO_ROOT)


def test_imported_lease_refusal_never_echoes_bundle_strings(tmp_path):
    state = _seed_state(tmp_path, thread_id="source-thread")
    state["agent"] = BOUND_SENTINEL
    lease_name = th.default_state_path(AGENT, state["lineage_id"]).as_posix()
    with pytest.raises(ValueError, match="bundle lease is invalid") as refusal:
        th._bundle_validate_lease_member(
            tmp_path,
            agent=AGENT,
            lineage_id=state["lineage_id"],
            manifest={},
            members={lease_name: th._bundle_json(state)},
        )
    assert BOUND_SENTINEL not in str(refusal.value)


@pytest.mark.parametrize("name", [f"../{BOUND_SENTINEL}.md", f"{BOUND_SENTINEL}.md"])
def test_member_allowlist_refusal_never_echoes_bundle_strings(name):
    from agents_extensions.shared.session_streams.store import validate_rollover_bundle_members

    with pytest.raises(ValueError) as refusal:
        validate_rollover_bundle_members([name], agent=AGENT, lineage_id="lineage-store", handoff_candidates=())
    assert BOUND_SENTINEL not in str(refusal.value)
