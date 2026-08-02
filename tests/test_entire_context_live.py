"""Live projection, explicit-use, provider-cache, and Monitor acceptance tests."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from scripts.agent_runtime import acpx_discuss
from scripts.api import entire_context_router
from scripts.api.main import app
from scripts.entire_context import provider, reconcile
from scripts.entire_context.model import (
    ContextLink,
    LinkKind,
    VerificationEvidence,
    VerificationStatus,
    isoformat_z,
)
from scripts.entire_context.paths import projection_path, shared_repository_root
from scripts.entire_context.store import ContextLinkStore


def _run_git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _promoted_store(tmp_path: Path) -> tuple[ContextLinkStore, ContextLink]:
    store = ContextLinkStore(tmp_path / "context-links.sqlite3")
    digest = "sha256:" + "a" * 64
    sha = "1" * 40
    link = ContextLink(
        kind=LinkKind.GIT_COMMIT,
        canonical_namespace="git:example/repo",
        canonical_id=sha,
        canonical_digest=digest,
        git_sha=sha,
        facets={"repository": "example/repo"},
    )
    verification = VerificationEvidence(
        verifier="git",
        canonical_digest=digest,
        status=VerificationStatus.VERIFIED,
        evidence_locator=f"git:commit/{sha}",
        checked_at=isoformat_z(datetime.now(UTC)),
    )
    store.admit(link, verification, actor="test")
    return store, link


def test_projection_path_is_shared_across_linked_worktrees(tmp_path: Path) -> None:
    primary = tmp_path / "primary"
    linked = tmp_path / "linked"
    primary.mkdir()
    _run_git(primary, "init", "-q")
    _run_git(primary, "config", "user.email", "test@example.invalid")
    _run_git(primary, "config", "user.name", "tester")
    (primary / "seed.txt").write_text("seed\n", encoding="utf-8")
    _run_git(primary, "add", "seed.txt")
    _run_git(primary, "commit", "-qm", "seed")
    _run_git(primary, "worktree", "add", "-q", "-b", "linked", str(linked))

    assert shared_repository_root(linked) == primary.resolve()
    assert projection_path(linked) == projection_path(primary)


def test_use_receipt_is_explicit_idempotent_and_separate_from_search(tmp_path: Path) -> None:
    store, link = _promoted_store(tmp_path)
    before = store.status()
    first = store.record_use(
        task_id="task-6183",
        consumer="codex",
        purpose="architecture",
        locator_ids=[link.locator_id],
    )
    second = store.record_use(
        task_id="task-6183",
        consumer="codex",
        purpose="architecture",
        locator_ids=[link.locator_id],
    )
    after = store.status()

    assert before["use_receipts"] == 0
    assert first["created"] is True
    assert second["created"] is False
    assert first["receipt_id"] == second["receipt_id"]
    assert after["use_receipts"] == 1
    assert after["uses_by_consumer"] == {"codex": 1}


def test_acp_wrapper_projects_only_after_complete_and_never_changes_result(
    tmp_path: Path, monkeypatch
) -> None:
    calls: list[dict] = []

    class FakeController:
        def __init__(self, *, root: Path) -> None:
            self.root = root

        def run(self, **_kwargs):
            return {
                "conversation_id": "conversation_" + "1" * 32,
                "state": "COMPLETE",
                "classification": "complete",
            }

        def close(self) -> None:
            return None

    monkeypatch.setattr(acpx_discuss, "AcpxDiscussionController", FakeController)
    monkeypatch.setattr(
        reconcile,
        "project_terminal_acp_receipt",
        lambda **kwargs: calls.append(kwargs) or {"outcome": "promoted"},
    )

    result = acpx_discuss.run_discussion(root=tmp_path / "plane", cwd=tmp_path)

    assert result["state"] == "COMPLETE"
    assert len(calls) == 1
    assert calls[0]["conversation_id"] == result["conversation_id"]


def test_acp_projection_failure_is_fail_open(tmp_path: Path, monkeypatch) -> None:
    class FakeController:
        def __init__(self, *, root: Path) -> None:
            self.root = root

        def run(self, **_kwargs):
            return {
                "conversation_id": "conversation_" + "2" * 32,
                "state": "COMPLETE",
            }

        def close(self) -> None:
            return None

    monkeypatch.setattr(acpx_discuss, "AcpxDiscussionController", FakeController)
    monkeypatch.setattr(
        reconcile,
        "project_terminal_acp_receipt",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("projection failed")),
    )

    assert acpx_discuss.run_discussion(root=tmp_path / "plane", cwd=tmp_path)["state"] == "COMPLETE"


def test_provider_refresh_is_allowlisted_cached_and_version_pinned(
    tmp_path: Path, monkeypatch
) -> None:
    def fake_run(_root: Path, *args: str):
        if args == ("version",):
            return subprocess.CompletedProcess(
                ["entire", "version"], 0, "Entire CLI 0.8.42\nGo version: hidden\n", ""
            )
        raw = {
            "enabled": True,
            "agents": ["Codex", "Claude Code"],
            "active_sessions": [{"agent": "Codex", "status": "ended", "body": "forbidden"}],
            "prompt": "forbidden",
        }
        return subprocess.CompletedProcess(
            ["entire", "status", "--json"], 0, json.dumps(raw), ""
        )

    target = tmp_path / "provider.json"
    monkeypatch.setattr(provider, "_run", fake_run)
    refreshed = provider.refresh_provider_status(tmp_path, output_path=target)
    loaded = provider.load_provider_status(
        tmp_path,
        status_path=target,
        now=datetime.now(UTC) + timedelta(seconds=901),
    )

    assert refreshed["version"] == "0.8.42"
    assert refreshed["installed_agents"] == ["claude-code", "codex"]
    assert "prompt" not in target.read_text(encoding="utf-8")
    assert "forbidden" not in target.read_text(encoding="utf-8")
    assert loaded["stale"] is True


def test_monitor_status_distinguishes_capture_recall_and_use(
    tmp_path: Path, monkeypatch
) -> None:
    store, link = _promoted_store(tmp_path)
    store.record_use(
        task_id="task-6183",
        consumer="codex",
        purpose="implementation",
        locator_ids=[link.locator_id],
    )
    monkeypatch.setenv("ENTIRE_CONTEXT_DB", str(store.db_path))
    monkeypatch.setattr(entire_context_router, "_repo_root", lambda: tmp_path)
    monkeypatch.setattr(
        entire_context_router,
        "load_provider_status",
        lambda _root: {
            "available": True,
            "enabled": True,
            "installed_agents": ["Codex"],
        },
    )

    response = TestClient(app).get("/api/ops/entire-context/status")
    payload = response.json()

    assert response.status_code == 200
    assert payload["capture"]["native_agent_installed"] is True
    assert payload["recall"]["available"] is True
    assert payload["use"]["proven"] is True
    assert payload["use"]["by_consumer"] == {"codex": 1}
    assert "projection_path" not in response.text
