"""Tests for the consultation monitoring API router.

Validates queue CRUD, history, metrics, safety guards, and idempotency.
Uses temp directories to isolate queue state from real data.
"""

import json
import shutil
from unittest.mock import patch

import pytest
import yaml
from fastapi.testclient import TestClient

from scripts.api.main import app

client = TestClient(app, raise_server_exceptions=False)

# Sample queue YAML matching the real format
SAMPLE_PROPOSAL = {
    "source_module": "a2/being-and-becoming",
    "consultation_num": 1,
    "confidence": "high",
    "root_cause": "The content template produces insufficient Ukrainian containers for immersion learning",
    "proposed_changes": [
        {
            "find": "Write a 3-word unjumble",
            "replace": "Write a 5-word unjumble with case markers",
            "file": "claude_extensions/phases/gemini/content.md",
            "rationale": "A2 needs more complex sentences",
        },
        {
            "find": "Use simple vocabulary",
            "replace": "Use graded vocabulary with frequency markers",
            "file": "claude_extensions/phases/gemini/content.md",
            "rationale": "Better vocabulary progression",
        },
    ],
    "additional_notes": "Both changes target the content template",
    "queued_at": "2026-03-13T18:49:51.749342+00:00",
}

SAMPLE_STATE_WITH_CONSULTATIONS = {
    "track": "a2",
    "slug": "being-and-becoming",
    "mode": "v5",
    "phases": {},
    "consultations": [
        {
            "num": 1,
            "outcome": "queued",
            "ts": "2026-03-13T18:49:51.749342+00:00",
            "scope": "all_modules",
            "action": "rebuild",
            "confidence": "high",
            "changes_count": 3,
        },
        {
            "num": 2,
            "outcome": "applied",
            "ts": "2026-03-13T19:00:00.000000+00:00",
            "scope": "this_module",
            "action": "fix",
            "confidence": "medium",
            "changes_count": 1,
        },
    ],
}


@pytest.fixture()
def temp_queue_dir(tmp_path):
    """Patch QUEUE_DIR, APPLIED_DIR, REJECTED_DIR to use temp directory."""
    queue_dir = tmp_path / "queue"
    queue_dir.mkdir()
    applied_dir = queue_dir / "applied"
    rejected_dir = queue_dir / "rejected"

    with patch("scripts.api.consultation_router.QUEUE_DIR", queue_dir), \
         patch("scripts.api.consultation_router.APPLIED_DIR", applied_dir), \
         patch("scripts.api.consultation_router.REJECTED_DIR", rejected_dir):
        yield queue_dir, applied_dir, rejected_dir


@pytest.fixture()
def queue_with_proposal(temp_queue_dir):
    """Create a queue dir with one proposal file."""
    queue_dir, applied_dir, rejected_dir = temp_queue_dir
    filename = "20260313T184951744734-being-and-becoming.yaml"
    filepath = queue_dir / filename
    filepath.write_text(
        yaml.dump(SAMPLE_PROPOSAL, allow_unicode=True, default_flow_style=False),
        "utf-8",
    )
    return filename, queue_dir, applied_dir, rejected_dir


# ==================== Queue List ====================


class TestQueueList:
    def test_queue_list_empty(self, temp_queue_dir):
        resp = client.get("/api/consultation/queue")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0
        assert data["pending"] == []

    def test_queue_list_with_proposals(self, queue_with_proposal):
        filename, *_ = queue_with_proposal
        resp = client.get("/api/consultation/queue")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        item = data["pending"][0]
        assert item["filename"] == filename
        assert item["track"] == "a2"
        assert item["slug"] == "being-and-becoming"
        assert item["confidence"] == "high"
        assert item["change_count"] == 2
        assert "content.md" in str(item["target_files"])


# ==================== Queue Detail ====================


class TestQueueDetail:
    def test_queue_detail(self, queue_with_proposal):
        filename, *_ = queue_with_proposal
        resp = client.get(f"/api/consultation/queue/{filename}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "pending"
        assert data["confidence"] == "high"
        assert len(data["proposed_changes"]) == 2

    def test_queue_detail_not_found(self, temp_queue_dir):
        resp = client.get("/api/consultation/queue/nonexistent.yaml")
        assert resp.status_code == 404

    def test_queue_detail_shows_applied(self, queue_with_proposal):
        filename, queue_dir, applied_dir, _ = queue_with_proposal
        # Move to applied
        applied_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(queue_dir / filename), applied_dir / filename)
        resp = client.get(f"/api/consultation/queue/{filename}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "applied"


# ==================== Approve ====================


class TestApprove:
    def test_approve_without_confirm(self, queue_with_proposal):
        filename, *_ = queue_with_proposal
        resp = client.post(f"/api/consultation/queue/{filename}/approve")
        assert resp.status_code == 400
        assert "confirm" in resp.json()["error"].lower()

    def test_approve_not_found(self, temp_queue_dir):
        resp = client.post("/api/consultation/queue/nope.yaml/approve?confirm=true")
        assert resp.status_code == 404

    def test_approve_validates_find_strings(self, queue_with_proposal):
        """FIND strings don't exist in template → 409."""
        filename, *_ = queue_with_proposal
        # The sample FIND strings won't match any real template
        resp = client.post(f"/api/consultation/queue/{filename}/approve?confirm=true")
        assert resp.status_code == 409
        data = resp.json()
        assert "mismatch" in data["error"].lower()
        assert len(data["mismatches"]) > 0

    def test_approve_idempotent(self, queue_with_proposal):
        filename, queue_dir, applied_dir, _ = queue_with_proposal
        # Pre-move to applied (simulate already approved)
        applied_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(queue_dir / filename), applied_dir / filename)
        resp = client.post(f"/api/consultation/queue/{filename}/approve?confirm=true")
        assert resp.status_code == 200
        assert resp.json()["status"] == "already_applied"

    def test_approve_malformed_yaml(self, temp_queue_dir):
        """Malformed YAML file returns 400, not a crash."""
        queue_dir, *_ = temp_queue_dir
        filename = "malformed.yaml"
        (queue_dir / filename).write_text("{{{{not: valid: yaml: [", "utf-8")
        resp = client.post(f"/api/consultation/queue/{filename}/approve?confirm=true")
        assert resp.status_code == 400
        assert "malformed" in resp.json()["error"].lower()

    def test_approve_success_with_matching_template(self, queue_with_proposal, tmp_path):
        """When FIND strings match the template, changes are applied."""
        filename, queue_dir, applied_dir, _ = queue_with_proposal

        # Create a fake template with the FIND strings
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "content.md"
        template_file.write_text(
            "Write a 3-word unjumble\nUse simple vocabulary\n",
            "utf-8",
        )

        with patch("scripts.api.consultation_router.TEMPLATE_DIR", template_dir):
            resp = client.post(f"/api/consultation/queue/{filename}/approve?confirm=true")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "approved"
        assert data["changes_applied"] == 2
        # File moved to applied/
        assert (applied_dir / filename).exists()
        assert not (queue_dir / filename).exists()
        # Template was patched
        patched = template_file.read_text()
        assert "5-word unjumble" in patched
        assert "graded vocabulary" in patched

    def test_approve_patch_failure_returns_errors(self, queue_with_proposal, tmp_path):
        """When apply_template_patch fails, errors are reported in response."""
        filename, _queue_dir, _applied_dir, _ = queue_with_proposal

        # Create a template with matching FIND strings
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "content.md"
        template_file.write_text(
            "Write a 3-word unjumble\nUse simple vocabulary\n",
            "utf-8",
        )

        # Mock apply_template_patch to return failure
        with patch("scripts.api.consultation_router.TEMPLATE_DIR", template_dir), \
             patch("scripts.api.consultation_router.apply_template_patch", return_value=(False, 0)):
            resp = client.post(f"/api/consultation/queue/{filename}/approve?confirm=true")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "approved"
        assert data["errors"] is not None
        assert any("patch failed" in e for e in data["errors"])


# ==================== Reject ====================


class TestReject:
    def test_reject_without_confirm(self, queue_with_proposal):
        filename, *_ = queue_with_proposal
        resp = client.post(f"/api/consultation/queue/{filename}/reject")
        assert resp.status_code == 400

    def test_reject_success(self, queue_with_proposal):
        filename, queue_dir, _, rejected_dir = queue_with_proposal
        resp = client.post(
            f"/api/consultation/queue/{filename}/reject?confirm=true&reason=Not+useful",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "rejected"
        assert (rejected_dir / filename).exists()
        assert not (queue_dir / filename).exists()
        # Check reason was written to file
        saved = yaml.safe_load((rejected_dir / filename).read_text())
        assert saved["rejected_reason"] == "Not useful"

    def test_reject_idempotent(self, queue_with_proposal):
        filename, queue_dir, _, rejected_dir = queue_with_proposal
        rejected_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(queue_dir / filename), rejected_dir / filename)
        resp = client.post(
            f"/api/consultation/queue/{filename}/reject?confirm=true",
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "already_rejected"


# ==================== History ====================


class TestHistory:
    def _mock_collect(self, track=None, outcome=None):
        """Return sample consultation entries, applying filters."""
        entries = [
            {"track": "a2", "slug": "being-and-becoming", "num": 1, "outcome": "queued",
             "ts": "2026-03-13T18:49:51", "scope": "all_modules", "confidence": "high"},
            {"track": "a2", "slug": "being-and-becoming", "num": 2, "outcome": "applied",
             "ts": "2026-03-13T19:00:00", "scope": "this_module", "confidence": "medium"},
            {"track": "b1", "slug": "some-module", "num": 1, "outcome": "queued",
             "ts": "2026-03-13T20:00:00", "scope": "all_modules", "confidence": "low"},
        ]
        if track:
            entries = [e for e in entries if e["track"] == track]
        if outcome:
            entries = [e for e in entries if e["outcome"] == outcome]
        return entries

    def test_history_all(self):
        with patch("scripts.api.consultation_router._collect_all_consultations", self._mock_collect):
            resp = client.get("/api/consultation/history")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3

    def test_history_filtered_by_track(self):
        with patch("scripts.api.consultation_router._collect_all_consultations", self._mock_collect):
            resp = client.get("/api/consultation/history?track=a2")
        data = resp.json()
        assert data["total"] == 2
        assert all(c["track"] == "a2" for c in data["consultations"])

    def test_history_filtered_by_outcome(self):
        with patch("scripts.api.consultation_router._collect_all_consultations", self._mock_collect):
            resp = client.get("/api/consultation/history?outcome=queued")
        data = resp.json()
        assert data["total"] == 2

    def test_history_module(self, tmp_path):
        # Create a fake orchestration dir with state.json
        orch_dir = tmp_path / "a2" / "orchestration" / "being-and-becoming"
        orch_dir.mkdir(parents=True)
        state_file = orch_dir / "state.json"
        state_file.write_text(json.dumps(SAMPLE_STATE_WITH_CONSULTATIONS))

        with patch("scripts.api.consultation_router.CURRICULUM_ROOT", tmp_path):
            resp = client.get("/api/consultation/history/a2/being-and-becoming")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        assert data["consultations"][0]["outcome"] == "queued"

    def test_history_module_not_found(self, tmp_path):
        with patch("scripts.api.consultation_router.CURRICULUM_ROOT", tmp_path):
            resp = client.get("/api/consultation/history/a2/nonexistent")
        assert resp.status_code == 404


# ==================== Metrics ====================


class TestMetrics:
    def test_metrics(self, temp_queue_dir):
        queue_dir, _applied_dir, _rejected_dir = temp_queue_dir

        # Add a proposal to queue for root cause keyword extraction
        filepath = queue_dir / "test-proposal.yaml"
        filepath.write_text(
            yaml.dump(SAMPLE_PROPOSAL, allow_unicode=True, default_flow_style=False),
        )

        with patch(
            "scripts.api.consultation_router._collect_all_consultations",
            lambda *a, **kw: [
                {"track": "a2", "outcome": "queued", "confidence": "high", "scope": "all_modules"},
                {"track": "a2", "outcome": "applied", "confidence": "medium", "scope": "this_module"},
                {"track": "b1", "outcome": "queued", "confidence": "low", "scope": "all_modules"},
            ],
        ):
            resp = client.get("/api/consultation/metrics")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert data["pending_queue"] == 1
        assert data["by_outcome"]["queued"] == 2
        assert data["by_outcome"]["applied"] == 1
        assert data["by_confidence"]["high"] == 1
        assert data["by_scope"]["all_modules"] == 2
        assert data["by_track"]["a2"] == 2
        # Root cause keywords extracted from queue file
        assert len(data["top_root_causes"]) > 0
