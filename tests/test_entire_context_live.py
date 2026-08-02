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
from scripts.entire_context.resolvers import (
    default_fleet_root,
    default_issue_cache,
    default_monitor_root,
    resolve_github_issue,
)
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


def test_monitor_status_allowlists_reconciliation_health_and_malformed_aggregates(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(entire_context_router, "_repo_root", lambda: tmp_path)
    monkeypatch.setattr(
        entire_context_router,
        "_projection_status",
        lambda _root: {
            "available": True,
            "schema_version": 1,
            "counts": {"promoted": "4", "pending": True, "tombstoned": None},
            "events": "8",
            "last_event_at": "2026-08-02T12:00:00Z",
            "use_receipts": "2",
            "last_use_at": "2026-08-02T12:01:00Z",
            "uses_by_consumer": {"codex": "2", "broken": object()},
            "projection_path": "/private/worktree/context.sqlite3",
            "prompt": "must never cross the API boundary",
            "projection_health": {
                "pending": 1,
                "tombstoned": 2,
                "dangling": 3,
                "tombstones_by_reason": {"source_missing": 2},
                "acp": {
                    "attempts": 5,
                    "failures": 1,
                    "retries": 2,
                    "last_attempt_at": "2026-08-02T12:00:00Z",
                    "last_success_at": "2026-08-02T11:59:00Z",
                    "last_failure_at": "2026-08-02T11:58:00Z",
                    "last_failure_reason": "source_missing",
                    "last_reconciliation_at": "2026-08-02T12:00:00Z",
                    "source_latest_at": "2026-08-02T11:59:55Z",
                    "lag_seconds": 5,
                    "last_reconciliation": {
                        "examined": 7,
                        "changed": 1,
                        "skipped": 6,
                        "truncated": False,
                        "limit": 500,
                        "local_path": "/forbidden",
                    },
                },
            },
        },
    )
    monkeypatch.setattr(
        entire_context_router,
        "load_provider_status",
        lambda _root: {
            "available": True,
            "enabled": True,
            "installed_agents": "malformed",
            "prompt": "forbidden",
        },
    )

    response = TestClient(app).get("/api/ops/entire-context/status")
    payload = response.json()
    projection = payload["recall"]["projection"]

    assert response.status_code == 200
    assert payload["capture"]["installed_agents"] == []
    assert payload["recall"]["promoted_links"] == 4
    assert payload["use"]["by_consumer"] == {"codex": 2}
    assert projection["counts"] == {"pending": 0, "promoted": 4, "tombstoned": 0}
    assert projection["projection_health"] == {
        "pending": 1,
        "tombstoned": 2,
        "dangling": 3,
        "tombstones_by_reason": {"source_missing": 2},
        "acp": {
            "attempts": 5,
            "failures": 1,
            "lag_seconds": 5,
            "retries": 2,
            "last_attempt_at": "2026-08-02T12:00:00Z",
            "last_failure_at": "2026-08-02T11:58:00Z",
            "last_failure_reason": "source_missing",
            "last_reconciliation_at": "2026-08-02T12:00:00Z",
            "last_success_at": "2026-08-02T11:59:00Z",
            "source_latest_at": "2026-08-02T11:59:55Z",
            "last_reconciliation": {
                "examined": 7,
                "changed": 1,
                "skipped": 6,
                "truncated": False,
                "limit": 500,
            },
        },
    }
    assert "/private/" not in response.text
    assert "prompt" not in response.text


def test_monitor_search_reverifies_typed_issue_from_shared_local_cache(
    tmp_path: Path, monkeypatch
) -> None:
    """Monitor search supplies shared typed roots and omits stale issue evidence."""
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

    issue_cache = default_issue_cache(linked)
    issue_cache.parent.mkdir(parents=True)
    report = {
        "generated_at": datetime.now(UTC).timestamp(),
        "open_issue_numbers": [6183],
        "effective_membership": {
            "6183": {"epics": [4707], "streams": ["infra"], "via": "native", "unique_stream": True}
        },
    }
    issue_cache.write_text(json.dumps(report), encoding="utf-8")
    store = ContextLinkStore(projection_path(linked))
    resolution = resolve_github_issue(
        6183,
        cache_path=issue_cache,
        repo=linked,
        namespace="github:learn-ukrainian/learn-ukrainian.github.io",
    )
    admitted = store.admit(resolution.link, resolution.verification, actor="test")

    observed: dict[str, Path] = {}
    real_search = entire_context_router.search_past_work

    def observe_search(*args, **kwargs):
        observed["fleet_root"] = kwargs["fleet_root"]
        observed["monitor_root"] = kwargs["monitor_root"]
        observed["issue_cache_path"] = kwargs["issue_cache_path"]
        observed["rollover_root"] = kwargs["rollover_root"]
        return real_search(*args, **kwargs)

    monkeypatch.setattr(entire_context_router, "_repo_root", lambda: linked)
    monkeypatch.setattr(entire_context_router, "search_past_work", observe_search)
    response = TestClient(app).get("/api/ops/entire-context/search", params={"q": "6183"})

    assert response.status_code == 200
    payload = response.json()
    assert [card["kind"] for card in payload["results"]] == ["github_issue"]
    assert observed == {
        "fleet_root": default_fleet_root(primary),
        "monitor_root": default_monitor_root(primary),
        "issue_cache_path": default_issue_cache(primary),
        "rollover_root": primary.resolve(),
    }
    override = tmp_path / "rollover-override"
    monkeypatch.setenv("ENTIRE_CONTEXT_ROLLOVER_ROOT", str(override))
    assert entire_context_router._rollover_root(linked) == override
    monkeypatch.delenv("ENTIRE_CONTEXT_ROLLOVER_ROOT")

    report["generated_at"] = 0
    issue_cache.write_text(json.dumps(report), encoding="utf-8")
    stale = TestClient(app).get("/api/ops/entire-context/search", params={"q": "6183"}).json()
    assert stale["results"] == []
    assert stale["omitted"] == [{"locator_id": admitted.locator_id, "reason": "partial_terminal"}]
