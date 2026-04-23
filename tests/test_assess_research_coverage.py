"""Tests for assess_research.py --coverage functionality."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
VENV_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from assess_research import _coverage_for_track


@pytest.fixture
def mock_curriculum(tmp_path):
    """Create a minimal curriculum structure for testing."""
    # Create manifest
    manifest = {
        "levels": {
            "test-track": {
                "modules": ["module-a", "module-b", "module-c"]
            }
        }
    }
    # Create research files (only 2 of 3)
    track_dir = tmp_path / "test-track"
    research_dir = track_dir / "research"
    research_dir.mkdir(parents=True)
    (research_dir / "module-a-research.md").write_text("# Research A\nSome content")
    (research_dir / "module-c-research.md").write_text("# Research C\nSome content")
    return manifest, tmp_path


class TestCoverageForTrack:
    def test_detects_gaps(self, mock_curriculum):
        manifest, root = mock_curriculum
        test_track = {"id": "test-track", "name": "TEST", "path": "test-track"}
        with patch("assess_research.TRACKS", [test_track]), \
             patch("assess_research.CURRICULUM_ROOT", root):
            cov = _coverage_for_track("test-track", manifest)
            assert cov["total"] == 3
            assert cov["researched"] == 2
            assert cov["gaps"] == ["module-b"]

    def test_full_coverage(self, mock_curriculum):
        manifest, root = mock_curriculum
        # Add missing research file
        research_dir = root / "test-track" / "research"
        (research_dir / "module-b-research.md").write_text("# Research B")
        test_track = {"id": "test-track", "name": "TEST", "path": "test-track"}
        with patch("assess_research.TRACKS", [test_track]), \
             patch("assess_research.CURRICULUM_ROOT", root):
            cov = _coverage_for_track("test-track", manifest)
            assert cov["total"] == 3
            assert cov["researched"] == 3
            assert cov["gaps"] == []

    def test_unknown_track(self):
        cov = _coverage_for_track("nonexistent-track", {"levels": {}})
        assert cov["total"] == 0
        assert cov["gaps"] == []

    def test_empty_manifest(self):
        cov = _coverage_for_track("a1", {"levels": {}})
        assert cov["total"] == 0


class TestCoverageCliIntegration:
    """Test that --coverage flag works in the CLI (uses real curriculum data)."""

    def test_coverage_json_is_valid(self):
        """--coverage --json produces valid JSON with expected structure."""
        result = subprocess.run(
            [str(VENV_PYTHON), str(REPO_ROOT / "scripts/assess_research.py"), "a1", "--coverage", "--json"],
            capture_output=True, text=True, timeout=30, cwd=REPO_ROOT,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "total" in data
        assert "researched" in data
        assert "gaps" in data
        assert isinstance(data["gaps"], list)

    def test_strict_exits_zero_for_full_coverage(self):
        """``--strict`` exit code mirrors whether gaps exist.

        Historically this test pinned ``a1`` at full coverage and
        required rc 0 — but research can drift (a new module lands in
        curriculum.yaml before its knowledge packet ships). Test the
        CONTRACT (zero gaps → rc 0, any gaps → rc 1) instead of a
        particular coverage snapshot.
        """
        probe = subprocess.run(
            [str(VENV_PYTHON), str(REPO_ROOT / "scripts/assess_research.py"), "a1", "--coverage", "--json"],
            capture_output=True, text=True, timeout=30, cwd=REPO_ROOT,
        )
        assert probe.returncode == 0
        data = json.loads(probe.stdout)
        expected_rc = 0 if not data.get("gaps") else 1

        strict = subprocess.run(
            [str(VENV_PYTHON), str(REPO_ROOT / "scripts/assess_research.py"), "a1", "--coverage", "--strict"],
            capture_output=True, text=True, timeout=30, cwd=REPO_ROOT,
        )
        assert strict.returncode == expected_rc, (
            f"--strict exited {strict.returncode} with "
            f"{len(data.get('gaps', []))} gap(s); expected {expected_rc}"
        )

    def test_all_coverage_json(self):
        """--all --coverage --json produces valid JSON."""
        result = subprocess.run(
            [str(VENV_PYTHON), str(REPO_ROOT / "scripts/assess_research.py"), "--all", "--coverage", "--json"],
            capture_output=True, text=True, timeout=30, cwd=REPO_ROOT,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, dict)
        # Should have at least some tracks
        assert len(data) > 0
        for _track_id, cov in data.items():
            assert "total" in cov
            assert "researched" in cov
            assert "gaps" in cov
