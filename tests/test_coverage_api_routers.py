"""Tests for API routers: comms_router, admin_router, images_router.

Targets ~150+ tests for coverage improvement.
"""

import json
import os
import sqlite3
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

pytestmark = pytest.mark.reads_content

# ---------------------------------------------------------------------------
# Fixtures: create a test app with all three routers mounted
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_project_root(tmp_path):
    """Set up a fake project root with required directory structure."""
    # Create directory structure
    (tmp_path / "data" / "backups").mkdir(parents=True)
    (tmp_path / "data" / "textbook_images").mkdir(parents=True)
    (tmp_path / "data" / "textbooks").mkdir(parents=True)
    (tmp_path / "data" / "textbook_chunks").mkdir(parents=True)
    (tmp_path / "data" / "literary_texts").mkdir(parents=True)
    (tmp_path / "logs").mkdir(parents=True)
    (tmp_path / "logs" / "research-preseed").mkdir(parents=True)
    (tmp_path / ".mcp" / "servers" / "message-broker" / "pids").mkdir(parents=True)
    (tmp_path / "curriculum" / "l2-uk-en").mkdir(parents=True)
    return tmp_path


@pytest.fixture()
def broker_db(mock_project_root):
    """Create a SQLite broker DB with the messages table."""
    db_path = mock_project_root / ".mcp" / "servers" / "message-broker" / "messages.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT,
            from_llm TEXT,
            to_llm TEXT,
            message_type TEXT,
            content TEXT,
            data TEXT,
            timestamp TEXT,
            acknowledged INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()
    return db_path


def _insert_messages(db_path, messages):
    """Helper to insert test messages into broker DB."""
    conn = sqlite3.connect(str(db_path))
    for msg in messages:
        conn.execute(
            "INSERT INTO messages (task_id, from_llm, to_llm, message_type, content, data, timestamp, acknowledged) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                msg.get("task_id", "test-task"),
                msg.get("from_llm", "claude"),
                msg.get("to_llm", "gemini"),
                msg.get("message_type", "message"),
                msg.get("content", "test content"),
                msg.get("data", ""),
                msg.get("timestamp", datetime.now(UTC).isoformat()),
                msg.get("acknowledged", 0),
            ),
        )
    conn.commit()
    conn.close()


@pytest.fixture()
def _patch_config(mock_project_root, broker_db):
    """Patch config module paths to use tmp_path.

    comms_router itself keeps no path globals since #7269 step 5 — it
    resolves everything from the app's MonitorContext — so steering comms
    routes at the fixture root happens via ``app.state.ctx`` (see
    ``comms_client`` and ``_comms_ctx``). admin_router is the same since
    step 8. The config patches below remain for images_router (still
    unmigrated; #7325) and helpers that read ``scripts.api.config``.
    """
    with (
        patch("scripts.api.config.PROJECT_ROOT", mock_project_root),
        patch("scripts.api.config.CURRICULUM_ROOT", mock_project_root / "curriculum" / "l2-uk-en"),
        patch("scripts.api.config.MESSAGE_DB", broker_db),
    ):
        yield


def _comms_ctx(project_root, **root_overrides):
    """Build the comms app context for the fixture root (#7269 step 5).

    Same pattern as ``tests/test_comms_router_expiry_sweep.py``: a fixture
    context whose roots all live under the test's project root.
    ``root_overrides`` replace individual ``MonitorRoots`` fields (e.g.
    ``pid_dir=Path("/nonexistent")``).
    """

    from scripts.api.monitor_context import fixture_context

    ctx = fixture_context(project_root)
    if root_overrides:
        ctx = ctx.with_roots(**root_overrides)
    return ctx


@pytest.fixture()
def comms_client(_patch_config, mock_project_root):
    """TestClient for comms router."""
    from scripts.api.comms_router import router
    app = FastAPI()
    app.state.ctx = _comms_ctx(mock_project_root)
    app.include_router(router, prefix="/api/comms")
    return TestClient(app)


@pytest.fixture()
def admin_app(_patch_config, mock_project_root):
    """Bare FastAPI app mounting admin_router against a fixture context."""
    from scripts.api.admin_router import router

    app = FastAPI()
    app.state.ctx = _comms_ctx(mock_project_root)
    app.include_router(router, prefix="/api/admin")
    return app


@pytest.fixture()
def admin_client(admin_app):
    """TestClient for admin router."""
    return TestClient(admin_app)


@pytest.fixture()
def images_client(_patch_config, mock_project_root):
    """TestClient for images router."""
    from scripts.api import images_router
    from scripts.api.monitor_context import fixture_context

    app = FastAPI()
    app.state.ctx = fixture_context(mock_project_root)
    app.include_router(images_router.router, prefix="/api/images")
    return TestClient(app)


@pytest.fixture()
def rag_client(mock_project_root):
    """TestClient for sources router."""
    from scripts.api.monitor_context import fixture_context
    from scripts.api.sources_router import router

    app = FastAPI()
    app.state.ctx = fixture_context(mock_project_root)
    app.include_router(router, prefix="/api/sources")
    yield TestClient(app)


# ===========================================================================
# COMMS ROUTER TESTS
# ===========================================================================


class TestCommsMessages:
    """Tests for /api/comms/messages endpoint."""

    def test_messages_no_db(self, comms_client, mock_project_root):
        """When DB doesn't exist, return empty with error."""
        db_path = mock_project_root / ".mcp" / "servers" / "message-broker" / "messages.db"
        db_path.unlink()
        r = comms_client.get("/api/comms/messages")
        assert r.status_code == 200
        assert r.json()["error"] == "Broker DB not found"


class TestCommsActiveProcesses:
    """Tests for /api/comms/active-processes endpoint."""

    def test_with_pid_files(self, comms_client, mock_project_root):
        pid_dir = mock_project_root / ".mcp" / "servers" / "message-broker" / "pids"
        pid_data = {
            "pid": os.getpid(),  # current process, should be alive
            "agent": "claude",
            "task_id": "t1",
            "model": "gpt-4",
            "mode": "review",
            "started": datetime.now(UTC).isoformat(),
        }
        (pid_dir / "proc1.json").write_text(json.dumps(pid_data))
        r = comms_client.get("/api/comms/active-processes")
        data = r.json()
        assert data["count"] == 1
        assert data["alive"] == 1
        assert data["processes"][0]["alive"] is True

    def test_with_dead_pid(self, comms_client, mock_project_root):
        pid_dir = mock_project_root / ".mcp" / "servers" / "message-broker" / "pids"
        (pid_dir / "dead.json").write_text(json.dumps({
            "pid": 99999999,  # almost certainly not running
            "started": datetime.now(UTC).isoformat(),
        }))
        r = comms_client.get("/api/comms/active-processes")
        data = r.json()
        assert data["count"] == 1
        assert data["alive"] == 0

    def test_corrupt_pid_file(self, comms_client, mock_project_root):
        pid_dir = mock_project_root / ".mcp" / "servers" / "message-broker" / "pids"
        (pid_dir / "corrupt.json").write_text("not json!")
        r = comms_client.get("/api/comms/active-processes")
        data = r.json()
        assert data["count"] == 1
        assert data["processes"][0]["error"] == "corrupt"


class TestCommsZombies:
    """Tests for /api/comms/zombies endpoint."""

    def test_stale_messages(self, comms_client, broker_db):
        old_ts = "2020-01-01T00:00:00+00:00"
        _insert_messages(broker_db, [
            {"timestamp": old_ts, "acknowledged": 0, "task_id": "stale-task"},
        ])
        r = comms_client.get("/api/comms/zombies", params={"stale_hours": 0.001})
        zombies = r.json()["zombies"]
        stale = [z for z in zombies if z["type"] == "stale_message"]
        assert len(stale) >= 1

    def test_stale_message_severity_critical(self, comms_client, broker_db):
        old_ts = "2020-01-01T00:00:00+00:00"
        _insert_messages(broker_db, [
            {"timestamp": old_ts, "acknowledged": 0},
        ])
        r = comms_client.get("/api/comms/zombies", params={"stale_hours": 0.001})
        stale = [z for z in r.json()["zombies"] if z["type"] == "stale_message"]
        # Old enough to be critical (> 2x stale_hours)
        assert stale[0]["severity"] == "critical"

    def test_error_loops(self, comms_client, broker_db):
        _insert_messages(broker_db, [
            {"task_id": "err-task", "message_type": "error"},
            {"task_id": "err-task", "message_type": "error"},
            {"task_id": "err-task", "message_type": "error"},
        ])
        r = comms_client.get("/api/comms/zombies")
        error_loops = [z for z in r.json()["zombies"] if z["type"] == "error_loop"]
        assert len(error_loops) == 1
        assert error_loops[0]["error_count"] == 3

    def test_orphan_pid(self, comms_client, mock_project_root):
        pid_dir = mock_project_root / ".mcp" / "servers" / "message-broker" / "pids"
        (pid_dir / "orphan.json").write_text(json.dumps({"pid": 99999999, "task_id": "orphan-task"}))
        r = comms_client.get("/api/comms/zombies")
        orphans = [z for z in r.json()["zombies"] if z["type"] == "orphan_pid"]
        assert len(orphans) == 1


class TestCommsLiveActivity:
    """Tests for /api/comms/live-activity endpoint."""

    def test_live_activity_with_state_file(self, comms_client, mock_project_root):
        # Create a recently-modified state-v3.json
        orch_dir = mock_project_root / "curriculum" / "l2-uk-en" / "hist" / "orchestration" / "test-module"
        orch_dir.mkdir(parents=True)
        state = {
            "slug": "test-module",
            "phases": {
                "v3-content": {
                    "status": "running",
                    "ts": datetime.now(UTC).isoformat(),
                    "task_id": "task-1",
                    "mode": "build",
                },
            },
        }
        (orch_dir / "state-v3.json").write_text(json.dumps(state))
        r = comms_client.get("/api/comms/live-activity", params={"minutes": 120})
        data = r.json()
        assert len(data["in_progress"]) >= 1

    def test_live_activity_with_v6_state_file(self, comms_client, mock_project_root):
        orch_dir = mock_project_root / "curriculum" / "l2-uk-en" / "hist" / "orchestration" / "v6-module"
        orch_dir.mkdir(parents=True)
        state = {
            "mode": "v6",
            "slug": "v6-module",
            "phases": {
                "write": {
                    "status": "running",
                    "ts": datetime.now(UTC).isoformat(),
                    "task_id": "task-v6",
                    "mode": "build",
                },
            },
        }
        (orch_dir / "state.json").write_text(json.dumps(state))
        r = comms_client.get("/api/comms/live-activity", params={"minutes": 120})
        data = r.json()
        assert any(item["slug"] == "v6-module" and item["phase"] == "write" for item in data["in_progress"])


# ===========================================================================
# ADMIN ROUTER TESTS
# ===========================================================================


class TestAdminHelpers:
    """Tests for admin helper functions."""

    def test_safe_join_valid(self, tmp_path):
        # _safe_within was replaced by path_safety.safe_join in commit
        # 9fe99a00a7. Same guarantee, raises ValueError instead of bool.
        from scripts.path_safety import safe_join
        result = safe_join(tmp_path, "child", "file.txt")
        assert result.name == "file.txt"

    def test_safe_join_traversal(self, tmp_path):
        from scripts.path_safety import safe_join
        with pytest.raises(ValueError):
            safe_join(tmp_path, "..", "etc", "passwd")


class TestAdminBackup:
    """Tests for backup endpoints."""

    def test_delete_backup_traversal(self, admin_client, mock_project_root, tmp_path):
        # Path traversal in the filename component is rejected by the
        # path_safety.safe_join guard inside admin_router (replacement
        # for the old _safe_within bool-returning helper). Filenames
        # containing path separators or .. fail with ValueError →
        # router returns 400 "Invalid filename".
        r = admin_client.delete("/api/admin/backup/..%2Fevil.tar")
        assert r.status_code in (400, 404)


class TestAdminDiskUsage:
    """Tests for /api/admin/disk-usage endpoint."""


class TestAdminMaintenance:
    """Tests for maintenance endpoints."""

    def test_annotation_stats_dict_format(self, admin_client, mock_project_root):
        img_dir = mock_project_root / "data" / "textbook_images"
        grade_dir = img_dir / "grade-3"
        grade_dir.mkdir()
        annotations = {
            "img1": {"image_id": "img1", "description_uk": "test", "teaching_value": "high"},
        }
        (grade_dir / "annotations.json").write_text(json.dumps(annotations))
        r = admin_client.get("/api/admin/maintenance/annotation-stats")
        assert r.json()["total_images"] == 1


class TestAdminCollections:
    """Tests for collection management endpoints."""









# ===========================================================================
# IMAGES ROUTER TESTS
# ===========================================================================


class TestImageIndex:
    """Tests for the _ImageIndex singleton."""

    def test_index_load_with_data(self, images_client, mock_project_root):
        """Index loads structural JSONLs and annotations."""
        img_dir = mock_project_root / "data" / "textbook_images"
        grade_dir = img_dir / "grade-1"
        grade_dir.mkdir(exist_ok=True)
        # Structural JSONL
        records = [
            {"image_id": "img1", "pdf_stem": "book1", "page": 1, "grade": 1},
            {"image_id": "img2", "pdf_stem": "book1", "page": 2, "grade": 1},
        ]
        with open(grade_dir / "book1-images.jsonl", "w") as f:
            for rec in records:
                f.write(json.dumps(rec) + "\n")
        # Annotations
        annotations = [
            {"image_id": "img1", "description_uk": "test description", "teaching_value": "high"},
        ]
        ann_file = img_dir / "image_text_pairs.jsonl"
        with open(ann_file, "w") as f:
            for ann in annotations:
                f.write(json.dumps(ann) + "\n")

        # Reset and reload
        store = images_client.app.state.ctx.stores.image_store
        store.index.reload()

        r = images_client.get("/api/images/stats")
        data = r.json()
        assert data["total"] == 2
        assert data["annotated"] == 1


class TestImagesCleanup:
    """Tests for POST /api/images/cleanup."""

    def test_cleanup(self, images_client, mock_project_root):
        store = images_client.app.state.ctx.stores.image_store
        img_path = mock_project_root / "data" / "textbook_images" / "test.png"
        img_path.write_bytes(b"PNG")
        store.index._records = {
            "img1": {"image_id": "img1", "image_path": "data/textbook_images/test.png", "pdf_stem": "book", "page": 1},
        }
        store.index._by_pdf_page = {
            "book": {1: [store.index._records["img1"]]},
        }
        store.index._loaded = True

        with (
            patch("scripts.api.images_router._remove_from_book_jsonls"),
            patch("scripts.api.images_router._rewrite_annotations_jsonl", new_callable=AsyncMock),
        ):
            r = images_client.post("/api/images/cleanup", json={"image_ids": ["img1"]})
        data = r.json()
        assert data["deleted_count"] == 1
        assert not img_path.exists()

    def test_cleanup_rejects_path_traversal(self, images_client, mock_project_root):
        store = images_client.app.state.ctx.stores.image_store

        outside_file = mock_project_root.parent / "outside.png"
        outside_file.write_bytes(b"PNG")
        store.index._records = {
            "img1": {"image_id": "img1", "image_path": "../outside.png", "pdf_stem": "", "page": None},
        }
        store.index._loaded = True

        r = images_client.post("/api/images/cleanup", json={"image_ids": ["img1"]})

        assert r.json()["deleted_count"] == 0
        assert r.json()["not_found"] == ["img1"]
        assert outside_file.exists()
        assert "img1" in store.index.records


class TestRagBrowseImages:
    """Tests for /api/sources/browse_images and /api/sources/stats."""

    def test_browse_images_rejects_invalid_grade(self, rag_client):
        r = rag_client.get("/api/sources/browse_images", params={"grade": "../etc"})
        assert r.status_code == 400
        assert r.json()["error"] == "Invalid grade format: ../etc"

    def test_stats_missing_corpus_keeps_documented_envelope(self, rag_client):
        r = rag_client.get("/api/sources/stats")
        assert r.status_code == 200
        assert r.json() == {"sources_db": {"error": "data/sources.db not found"}}


class TestImagesHelpers:
    """Tests for helper functions in images_router."""

    def test_remove_from_book_jsonls(self, mock_project_root, _patch_config):
        from scripts.api.images_router import _remove_from_book_jsonls
        img_dir = mock_project_root / "data" / "textbook_images"
        grade_dir = img_dir / "grade-1"
        grade_dir.mkdir(exist_ok=True)
        records = [
            {"image_id": "keep", "data": "a"},
            {"image_id": "delete", "data": "b"},
        ]
        jsonl_path = grade_dir / "book1-images.jsonl"
        with open(jsonl_path, "w") as f:
            for rec in records:
                f.write(json.dumps(rec) + "\n")

        _remove_from_book_jsonls({"delete"}, images_dir=img_dir)

        with open(jsonl_path) as f:
            remaining = [json.loads(line) for line in f if line.strip()]
        assert len(remaining) == 1
        assert remaining[0]["image_id"] == "keep"

    def test_rewrite_annotations_jsonl_sync(self, mock_project_root, _patch_config):
        from scripts.api.monitor_context import fixture_context
        ctx = fixture_context(mock_project_root)
        store = ctx.stores.image_store
        ann_file = mock_project_root / "data" / "textbook_images" / "image_text_pairs.jsonl"
        ann_file.parent.mkdir(parents=True, exist_ok=True)
        ann_file.write_text('{"image_id": "old"}\n')

        store.index._records = {
            "img1": {"image_id": "img1", "description_uk": "test", "teaching_value": "high"},
            "img2": {"image_id": "img2"},  # no annotation data, should be skipped
        }
        store.index._loaded = True

        from scripts.api import images_router
        images_router._rewrite_annotations_jsonl_sync(store=store)

        with open(ann_file) as f:
            lines = [line.strip() for line in f if line.strip()]
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["image_id"] == "img1"


# ===========================================================================
# ADDITIONAL TESTS TO REACH 150+
# ===========================================================================


class TestAdminVerifyCollectionsStatuses:
    """Test various verify status outcomes."""


class TestCommsPreseedLogParsing:
    """Test preseed log parsing with various formats."""

    def test_scan_preseed_logs_with_last_line(self, _patch_config, mock_project_root):
        from scripts.api.comms_router import _scan_preseed_logs
        log_dir = mock_project_root / "logs" / "research-preseed"
        log_content = (
            "Starting batch...\n"
            "VERDICT: PASS\n"
            "VERDICT: FAIL\n"
            "ERROR: something went wrong\n"
            "=====\n"
            "Last meaningful line here\n"
        )
        (log_dir / "hist-20260301-0100.log").write_text(log_content)
        result = _scan_preseed_logs(_comms_ctx(mock_project_root))
        assert len(result) == 1
        assert result[0]["passed"] == 1
        assert result[0]["failed"] == 2  # FAIL + ERROR
        assert "Last meaningful line" in result[0]["last_line"]
        assert result[0]["complete"] is False
