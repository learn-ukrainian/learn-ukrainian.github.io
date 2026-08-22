"""Tests for /api/admin/disk-usage endpoint, including OPSEC #7081 checks.

Split out of tests/test_coverage_api_routers.py so the pytest fastlane can
collect this module without dragging in the PDF pool tests (which require
the optional ``pymupdf`` dependency absent from slim fastlane deps).
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture()
def mock_project_root(tmp_path):
    """Set up a fake project root with the directories disk-usage measures."""
    (tmp_path / "data" / "backups").mkdir(parents=True)
    (tmp_path / "data" / "textbook_images").mkdir(parents=True)
    (tmp_path / "data" / "textbooks").mkdir(parents=True)
    (tmp_path / "data" / "textbook_chunks").mkdir(parents=True)
    (tmp_path / "data" / "literary_texts").mkdir(parents=True)
    (tmp_path / "logs").mkdir(parents=True)
    return tmp_path


@pytest.fixture()
def admin_client(mock_project_root):
    """TestClient for admin router with disk-usage paths pointed at tmp_path."""
    with (
        patch("scripts.api.admin_router.PROJECT_ROOT", mock_project_root),
        patch("scripts.api.admin_router.DATA_DIR", mock_project_root / "data"),
        patch("scripts.api.admin_router.BACKUP_DIR", mock_project_root / "data" / "backups"),
        patch("scripts.api.admin_router.LOGS_DIR", mock_project_root / "logs"),
    ):
        from scripts.api.admin_router import router
        app = FastAPI()
        app.include_router(router, prefix="/api/admin")
        yield TestClient(app)


class TestAdminDiskUsage:
    """Tests for /api/admin/disk-usage endpoint."""

    def test_disk_usage(self, admin_client, mock_project_root):
        # Create some files
        (mock_project_root / "data" / "textbook_images" / "test.png").write_bytes(b"x" * 100)
        r = admin_client.get("/api/admin/disk-usage")
        data = r.json()
        assert r.status_code == 200
        assert "breakdown" in data
        assert data["total_bytes"] >= 0
        # Breakdown keys are opaque labels only
        assert set(data["breakdown"]) == {
            "textbook_images", "textbooks", "literary_texts",
            "textbook_chunks", "backups", "logs", "vesum_db",
        }

    def test_disk_usage_leaks_no_absolute_paths(self, admin_client, mock_project_root):
        """OPSEC #7081: serialized JSON must not contain path/home/host strings."""
        r = admin_client.get("/api/admin/disk-usage")
        assert r.status_code == 200
        data = r.json()
        for entry in data["breakdown"].values():
            assert "path" not in entry
            assert set(entry) == {"exists", "size_bytes", "size_human"}
        raw = r.content.decode()
        assert "/home/" not in raw
        assert str(Path.home()) not in raw
        if Path(str(mock_project_root)).is_absolute():
            assert str(mock_project_root) not in raw
