"""#7483 (1.12): formal-review resolver reads sealed verdicts via ArtifactStore."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.entire_context.resolvers import resolve_formal_review
from scripts.fleet_comms.artifacts import ArtifactStore


def test_resolve_formal_review_uses_readonly_artifact_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sealed bytes must come from ArtifactStore.open_readonly, not a CAS path."""
    root = tmp_path / "fleet"
    head_sha = "a" * 40
    review_id = "review_" + "b" * 32
    sealed = {
        "review_id": review_id,
        "repository": "learn-ukrainian/learn-ukrainian.github.io",
        "pr_number": 7483,
        "head_sha": head_sha,
        "gate_kind": "cross-family-review",
        "verdict": "APPROVED",
        "model": "gpt-5.6-terra",
        "family": "openai",
        "harness": "codex",
    }
    with ArtifactStore(root=root) as store:
        rec = store.store_bytes(
            json.dumps(sealed).encode("utf-8"),
            producer="test",
            mime_type="application/json",
            logical_filename="sealed.json",
            artifact_id="artifact_sealed_store_path",
        )
        conn = store.connection
        conn.execute(
            """INSERT INTO formal_review_jobs(
                review_id, repository, pr_number, head_sha, gate_kind, state,
                sealed_verdict_artifact_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                review_id,
                "learn-ukrainian/learn-ukrainian.github.io",
                7483,
                head_sha,
                "cross-family-review",
                "complete",
                rec.artifact_id,
                "2026-09-02T00:00:00Z",
            ),
        )
        conn.execute(
            """INSERT INTO formal_review_attempts(
                review_attempt_id, review_id, attempt_number, completion_state,
                raw_capture_artifact_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)""",
            ("attempt_1", review_id, 1, "complete", None, "2026-09-02T00:00:01Z"),
        )
        conn.commit()

    opened: list[Path] = []
    real_open = ArtifactStore.open_readonly.__func__

    @classmethod
    def tracking_open(cls, root=None, *, repo_root=None):
        opened.append(Path(root) if root is not None else Path("."))
        return real_open(cls, root=root, repo_root=repo_root)

    monkeypatch.setattr(ArtifactStore, "open_readonly", tracking_open)
    resolution = resolve_formal_review(review_id, fleet_root=root)
    assert resolution.excerpt["verdict"] == "APPROVED"
    assert opened and opened[0] == root.resolve()
