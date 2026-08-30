"""Startup registry seeding and API projection coverage for #7185."""

from __future__ import annotations

import asyncio
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from agents_extensions.shared.session_streams.db import SessionStreamDatabase
from agents_extensions.shared.session_streams.inventory import scan_stream_epic_inventory
from agents_extensions.shared.session_streams.model import isoformat_z
from agents_extensions.shared.session_streams.receipts import register_manifest_inventory
from agents_extensions.shared.session_streams.store import SessionStreamStore
from scripts.api import epics_router
from tests.epics_monitor_stub import epics_app_for_store

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 8, 24, 10, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _reset_registry_state() -> None:
    old_marker = epics_router._REGISTRY_SNAPSHOT_SHA256
    old_health = dict(epics_router._REGISTRY_HEALTH)
    epics_router._REGISTRY_SNAPSHOT_SHA256 = None
    epics_router._REGISTRY_HEALTH.update(
        {
            "status": "unavailable",
            "records": 0,
            "registered": 0,
            "skipped": 0,
            "source_sha256": None,
            "seeded_at": None,
        }
    )
    yield
    epics_router._REGISTRY_SNAPSHOT_SHA256 = old_marker
    epics_router._REGISTRY_HEALTH.clear()
    epics_router._REGISTRY_HEALTH.update(old_health)


def _write_registry(root: Path, streams: object, *, raw: bool = False) -> Path:
    config = root / "scripts" / "config"
    config.mkdir(parents=True, exist_ok=True)
    path = config / "issue_streams.yaml"
    if raw:
        path.write_text(str(streams), encoding="utf-8")
    else:
        path.write_text(
            yaml.safe_dump(
                {"schema_version": 1, "streams": streams},
                sort_keys=False,
            ),
            encoding="utf-8",
        )
    return path


def _store(tmp_path: Path) -> SessionStreamStore:
    return SessionStreamStore(SessionStreamDatabase(tmp_path / "api.sqlite3"))


def _client(store: SessionStreamStore, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    del monkeypatch
    app = epics_app_for_store(store, store.database.path.parent)
    return TestClient(app)


def _add_store_only(store: SessionStreamStore, stream_id: str) -> None:
    with store._transaction(now=NOW) as connection:
        store._ensure_stream(connection, stream_id=stream_id, created_at=isoformat_z(NOW))


def _migration_state(store: SessionStreamStore) -> list[tuple[str, int, str]]:
    with store._read_snapshot() as connection:
        rows = connection.execute(
            "SELECT stream_id, version, updated_at FROM stream_migration_state ORDER BY stream_id"
        ).fetchall()
        return [(str(row["stream_id"]), int(row["version"]), str(row["updated_at"])) for row in rows]


def test_startup_seed_registers_all_canonical_release_epics(tmp_path: Path) -> None:
    store = _store(tmp_path)
    health = epics_router.seed_manifest_inventory(
        ROOT,
        store=store,
        handoff_root=tmp_path / "live",
        now=NOW,
    )

    # Derive the expectation from the live registry: one record per distinct
    # epic across streams. A literal here broke the merge queue when a new
    # epic was registered (#7470 MQ ejection, 2026-08-30).
    registry = yaml.safe_load(
        (ROOT / "scripts" / "config" / "issue_streams.yaml").read_text(encoding="utf-8")
    )
    expected = len(
        {epic for stream in registry["streams"].values() for epic in stream["epics"]}
    )
    # Ratchet: growth is routine (new epic registered), shrink is exceptional
    # and must be a deliberate test update alongside the registry change.
    assert expected >= 19
    assert health["status"] == "ok"
    assert health["records"] == expected
    assert health["registered"] == expected
    assert health["skipped"] == 0
    assert len(store.list_remote_projections()) == expected


def test_second_startup_on_same_snapshot_is_a_true_noop(tmp_path: Path) -> None:
    release = tmp_path / "release"
    _write_registry(
        release,
        {"alpha": {"title": "Alpha stream", "epics": [1001, 1002]}},
    )
    store = _store(tmp_path)
    epics_router.seed_manifest_inventory(release, store=store, handoff_root=tmp_path / "live", now=NOW)
    before = _migration_state(store)

    class WriteGuardStore(SessionStreamStore):
        def _transaction(self, **kwargs):  # type: ignore[no-untyped-def]
            raise AssertionError("unchanged startup must not open a write transaction")

    guarded = WriteGuardStore(store.database)
    health = epics_router.seed_manifest_inventory(
        release,
        store=guarded,
        handoff_root=tmp_path / "live",
        now=NOW.replace(hour=11),
    )
    direct = register_manifest_inventory(
        guarded,
        release,
        handoff_root=tmp_path / "live",
        read_handoff_files=False,
        now=NOW.replace(hour=12),
    )

    assert health["status"] == "ok"
    assert health["registered"] == 2
    assert direct.no_op is True
    assert _migration_state(store) == before


def test_missing_registry_is_fail_open_and_existing_rows_are_served(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = _store(tmp_path)
    _add_store_only(store, "epic:9999")
    health = epics_router.seed_manifest_inventory(tmp_path / "missing", store=store, now=NOW)
    client = _client(store, monkeypatch)

    listing = client.get("/api/epics/v1")
    detail = client.get("/api/epics/v1/epic:9999")
    api_health = client.get("/api/epics/v1/health")

    assert health["status"] == "unavailable"
    assert listing.status_code == 200
    assert listing.json()["registry_status"] == "unavailable"
    assert detail.status_code == 200
    assert detail.json()["registry_status"] == "unavailable"
    assert detail.json()["registered"] is False
    assert detail.json()["stream_name"] is None
    assert detail.json()["title"] is None
    assert api_health.status_code == 200
    assert api_health.json()["registry"]["status"] == "unavailable"


def test_unreadable_registry_is_fail_open(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    release = tmp_path / "release"
    _write_registry(release, {"alpha": {"title": "Alpha", "epics": [1001]}})
    store = _store(tmp_path)

    def unreadable(*args: object, **kwargs: object) -> str:
        raise OSError("registry read failed")

    monkeypatch.setattr(epics_router, "streams_yaml_sha256", unreadable)
    health = epics_router.seed_manifest_inventory(release, store=store, now=NOW)

    assert health["status"] == "unavailable"
    assert health["registered"] == 0


def test_malformed_registry_entry_is_counted_and_rows_remain_served(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    release = tmp_path / "release"
    _write_registry(
        release,
        {
            "good": {"title": "Good stream", "epics": [1001, "not-an-epic"]},
            "bad name": {"title": "Bad name", "epics": [1002]},
            "bad body": "not a mapping",
        },
    )
    store = _store(tmp_path)
    health = epics_router.seed_manifest_inventory(release, store=store, now=NOW)
    client = _client(store, monkeypatch)

    listing = client.get("/api/epics/v1")
    detail = client.get("/api/epics/v1/epic:1001")
    api_health = client.get("/api/epics/v1/health")

    assert health["status"] == "invalid"
    assert health["records"] == 1
    assert health["registered"] == 1
    assert health["skipped"] == 3
    assert listing.status_code == 200
    assert listing.json()["registry_status"] == "invalid"
    assert detail.status_code == 200
    assert detail.json()["registered"] is True
    assert api_health.status_code == 200
    assert api_health.json()["registry"]["skipped"] == 3


def test_malformed_yaml_is_invalid_but_does_not_block_seed_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    release = tmp_path / "release"
    _write_registry(release, "streams: [", raw=True)
    store = _store(tmp_path)
    _add_store_only(store, "epic:9999")

    health = epics_router.seed_manifest_inventory(release, store=store, now=NOW)
    client = _client(store, monkeypatch)

    assert health["status"] == "invalid"
    assert health["skipped"] == 1
    assert client.get("/api/epics/v1").status_code == 200
    assert client.get("/api/epics/v1/epic:9999").status_code == 200


def test_list_and_detail_distinguish_registered_and_store_only_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    release = tmp_path / "release"
    _write_registry(release, {"alpha": {"title": "Alpha stream", "epics": [1001]}})
    store = _store(tmp_path)
    epics_router.seed_manifest_inventory(release, store=store, handoff_root=tmp_path / "live", now=NOW)
    _add_store_only(store, "epic:999999")
    client = _client(store, monkeypatch)

    listing = client.get("/api/epics/v1")
    rows = {row["stream_id"]: row for row in listing.json()["streams"]}
    registered = rows["epic:1001"]
    store_only = rows["epic:999999"]

    assert listing.status_code == 200
    assert listing.json()["registry_status"] == "ok"
    assert registered["registered"] is True
    assert registered["stream_name"] == "alpha"
    assert registered["title"] == "Alpha stream"
    assert registered["lease"] is None
    assert store_only["registered"] is False
    assert store_only["stream_name"] is None
    assert store_only["title"] is None
    assert client.get("/api/epics/v1/epic:1001").json()["registered"] is True
    assert client.get("/api/epics/v1/epic:999999").json()["registered"] is False


def test_removed_epic_keeps_row_as_stale_metadata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    release = tmp_path / "release"
    _write_registry(
        release,
        {"alpha": {"title": "Alpha stream", "epics": [1001, 1002]}},
    )
    store = _store(tmp_path)
    epics_router.seed_manifest_inventory(release, store=store, now=NOW)
    _write_registry(release, {"alpha": {"title": "Alpha stream", "epics": [1001]}})
    epics_router.seed_manifest_inventory(release, store=store, now=NOW.replace(hour=11))
    client = _client(store, monkeypatch)

    row = {item["stream_id"]: item for item in client.get("/api/epics/v1").json()["streams"]}["epic:1002"]

    assert row["registered"] is False
    assert row["stream_name"] == "alpha"
    assert row["title"] == "Alpha stream"
    assert row["lease"] is None


@pytest.mark.parametrize(
    "value",
    [
        "/" + "private" + "/marker",
        "~" + "/marker",
        ".".join(("10", "0", "0", "7")),
        "2001" + ":" + "db8" + "::1",
        "worker" + "." + "internal",
        "ssh " + "ops-box",
        "token" + "=" + "opaque-secret-value",
        "x" * 161,
    ],
)
def test_registry_text_sanitizer_redacts_forbidden_classes(value: str) -> None:
    assert epics_router._response_registry_text(value) == "[redacted]"


def test_registry_text_sanitizer_preserves_legitimate_title() -> None:
    assert epics_router._response_registry_text("Atlas practice hub") == "Atlas practice hub"


def test_handoff_files_are_read_before_the_lease_transaction(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    release = tmp_path / "release"
    live = tmp_path / "live"
    _write_registry(release, {"alpha": {"title": "Alpha", "epics": [1001]}})
    record = scan_stream_epic_inventory(release, handoff_root=live).records[0]
    candidate = live / record.handoff_candidates[0]
    candidate.parent.mkdir(parents=True)
    candidate.write_text("bounded handoff", encoding="utf-8")

    class TransactionProbeStore(SessionStreamStore):
        def __init__(self, database):  # type: ignore[no-untyped-def]
            super().__init__(database)
            self.in_transaction = False

        @contextmanager
        def _transaction(self, **kwargs):  # type: ignore[no-untyped-def]
            self.in_transaction = True
            try:
                with super()._transaction(**kwargs) as connection:
                    yield connection
            finally:
                self.in_transaction = False

    store = TransactionProbeStore(SessionStreamDatabase(tmp_path / "api.sqlite3"))
    original_read_bytes = Path.read_bytes

    def tracked_read_bytes(path: Path) -> bytes:
        if store.in_transaction and path.resolve() == candidate.resolve():
            raise AssertionError("handoff content was read while BEGIN IMMEDIATE was held")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", tracked_read_bytes)
    result = register_manifest_inventory(store, release, handoff_root=live)

    assert result.import_receipts_written >= 1


def test_startup_seed_does_not_read_handoff_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    release = tmp_path / "release"
    live = tmp_path / "live"
    _write_registry(release, {"alpha": {"title": "Alpha", "epics": [1001]}})
    record = scan_stream_epic_inventory(release, handoff_root=live).records[0]
    candidate = live / record.handoff_candidates[0]
    candidate.parent.mkdir(parents=True)
    candidate.write_text("handoff must not be read by startup", encoding="utf-8")
    store = _store(tmp_path)
    original_read_bytes = Path.read_bytes

    def reject_handoff_read(path: Path) -> bytes:
        if path.resolve() == candidate.resolve():
            raise AssertionError("startup seed must not read handoff content")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", reject_handoff_read)
    health = epics_router.seed_manifest_inventory(
        release,
        store=store,
        handoff_root=live,
        now=NOW,
    )

    assert health["status"] == "ok"
    assert health["registered"] == 1


def test_api_lifespan_invokes_registry_seed_with_two_roots(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.api import main as api_main

    calls: dict[str, object] = {}
    monkeypatch.setattr(api_main, "preload_all", lambda: None)
    monkeypatch.setattr(api_main, "install_signal_logging", lambda: None)
    monkeypatch.setattr(api_main, "ensure_broker_db_ready", lambda: None)
    monkeypatch.setattr(api_main.isa, "schedule_refresh", lambda force=False: None)
    monkeypatch.setattr(api_main, "warm_projection_cache", lambda **_kwargs: None)
    monkeypatch.setattr(api_main, "start_periodic_refresh", lambda: None)
    monkeypatch.setattr(api_main, "stop_periodic_refresh", lambda: None)

    def fake_seed(root: Path, **kwargs: object) -> dict[str, object]:
        calls["root"] = root
        calls["kwargs"] = kwargs
        return {}

    monkeypatch.setattr(api_main, "seed_manifest_inventory", fake_seed)

    async def run_lifespan() -> None:
        async with api_main._lifespan(api_main.app):
            pass

    asyncio.run(run_lifespan())

    ctx = api_main.app.state.ctx
    assert calls["root"] == ctx.roots.project_root
    assert calls["kwargs"] == {
        "store": ctx.stores.epics_store,
        "handoff_root": ctx.roots.live_repo_root,
        "ctx": ctx,
    }
