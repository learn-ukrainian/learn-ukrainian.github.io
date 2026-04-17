"""Tests for P0 follow-up endpoints from #1313 feedback batch.

Covers:
    /api/state/range/{track}            Codex-4 — compact range table
    /api/worktrees                       Codex-5 — worktree registry
    /api/artifacts/{track}/{slug}/force-preview   Codex-9 — force dry-run
"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

import scripts.api.artifacts_router as artifacts_router
import scripts.api.main as api_main
import scripts.api.state_router as state_router
import scripts.api.worktrees_router as worktrees_router

client = TestClient(api_main.app, raise_server_exceptions=False)


# ---------------------------------------------------------------------
# /api/state/range/{track}
# ---------------------------------------------------------------------


def test_range_status_slices_and_flattens(monkeypatch):
    """Range endpoint returns compact per-module rows with phase + score."""
    fake_levels = [{"id": "a1", "path": "l2-uk-en/a1"}]
    monkeypatch.setattr(state_router, "LEVELS", fake_levels)

    def fake_pipeline(track_id, level_cfg):
        return {
            "track": track_id,
            "modules": [
                {
                    "num": 1, "slug": "one",
                    "phases": {
                        "write": {"status": "complete", "executor": {"agent": "gemini"}},
                        "review": {"status": "in_progress", "executor": {"agent": "claude"}},
                    },
                    "audit": "pass", "review": {"score": 9.4},
                    "words": 1300, "word_target": 1200, "blocker": None,
                    "pipeline_version": "v6", "needs_rebuild": False,
                },
                {
                    "num": 2, "slug": "two",
                    "phases": {
                        "write": {"status": "complete", "executor": {"agent": "gemini"}},
                    },
                    "audit": "fail", "review": {"score": None},
                    "words": 800, "word_target": 1200,
                    "blocker": "word_budget", "pipeline_version": "v6", "needs_rebuild": False,
                },
                {
                    "num": 3, "slug": "three",
                    "phases": {},
                    "audit": None, "review": {},
                    "blocker": None, "pipeline_version": "unbuilt", "needs_rebuild": True,
                },
            ],
        }

    monkeypatch.setattr(state_router, "compute_pipeline_track", fake_pipeline)

    resp = client.get("/api/state/range/a1?start=1&end=2")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 2
    rows = body["modules"]
    # Module 1: current phase = in_progress review
    assert rows[0]["slug"] == "one"
    assert rows[0]["phase"] == "review"
    assert rows[0]["worker"] == "claude"
    assert rows[0]["review_score"] == 9.4
    # Module 2: current phase = last complete (write), audit fail, blocker set
    assert rows[1]["slug"] == "two"
    assert rows[1]["phase"] == "write"
    assert rows[1]["blocker"] == "word_budget"


def test_range_status_404_on_unknown_track(monkeypatch):
    monkeypatch.setattr(state_router, "LEVELS", [{"id": "a1", "path": "l2-uk-en/a1"}])
    resp = client.get("/api/state/range/does-not-exist")
    assert resp.status_code == 404


def test_range_status_open_ended(monkeypatch):
    fake_levels = [{"id": "a1", "path": "l2-uk-en/a1"}]
    monkeypatch.setattr(state_router, "LEVELS", fake_levels)

    modules = [
        {"num": n, "slug": f"m{n}", "phases": {}, "review": {}, "audit": None}
        for n in range(1, 6)
    ]
    monkeypatch.setattr(
        state_router, "compute_pipeline_track",
        lambda *_a, **_kw: {"modules": modules},
    )

    # Omit end → walk to the last module.
    body = client.get("/api/state/range/a1?start=3").json()
    assert [r["num"] for r in body["modules"]] == [3, 4, 5]


# ---------------------------------------------------------------------
# /api/worktrees
# ---------------------------------------------------------------------


def test_worktrees_parses_porcelain_output(monkeypatch, tmp_path):
    """list_worktrees returns structured records with per-wt status."""
    # Build a fake porcelain block representing one primary + one sibling.
    primary = tmp_path / "main"
    sibling = tmp_path / "sibling"
    primary.mkdir()
    sibling.mkdir()

    porcelain = (
        f"worktree {primary}\n"
        "HEAD abc1234567890\n"
        "branch refs/heads/main\n"
        "\n"
        f"worktree {sibling}\n"
        "HEAD def9876543210\n"
        "branch refs/heads/feature-branch\n"
    )

    monkeypatch.setattr(worktrees_router, "PROJECT_ROOT", primary)

    calls: list[list[str]] = []

    def fake_run(cmd, cwd, timeout_s=2.0):
        calls.append(cmd)
        if cmd[:2] == ["git", "worktree"]:
            return 0, porcelain, ""
        if cmd[:2] == ["git", "status"]:
            # First worktree: clean. Second: modified one file + untracked.
            if Path(cwd) == sibling:
                return 0, " M scripts/foo.py\n?? scratch.txt\n", ""
            return 0, "", ""
        if cmd[:3] == ["git", "log", "-1"]:
            if Path(cwd) == sibling:
                return 0, "def9876 2026-04-17T12:00:00+00:00 wip: feature work\n", ""
            return 0, "abc1234 2026-04-17T10:00:00+00:00 feat: initial\n", ""
        return 127, "", "unexpected command"

    monkeypatch.setattr(worktrees_router, "_run", fake_run)

    resp = client.get("/api/worktrees")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 2

    by_branch = {wt["branch"]: wt for wt in body["worktrees"]}
    main_wt = by_branch["main"]
    feature_wt = by_branch["feature-branch"]

    assert main_wt["is_primary"] is True
    assert main_wt["dirty"] is False
    assert main_wt["last_commit"]["sha"] == "abc1234"

    assert feature_wt["is_primary"] is False
    assert feature_wt["dirty"] is True
    assert "M" in feature_wt["change_types"]
    assert "??" in feature_wt["change_types"]
    assert feature_wt["last_commit"]["subject"] == "wip: feature work"


def test_worktrees_swallows_timeout(monkeypatch):
    """A timeout on git worktree list becomes an error string, not a 500."""
    import subprocess

    def raises_timeout(*_a, **_kw):
        raise subprocess.TimeoutExpired(cmd=["git"], timeout=2.0)

    monkeypatch.setattr(worktrees_router.subprocess, "run", raises_timeout)

    resp = client.get("/api/worktrees")
    assert resp.status_code == 200
    body = resp.json()
    assert body["worktrees"] == []
    assert "TimeoutExpired" in body["error"]


def test_worktrees_missing_git_binary_degrades(monkeypatch):
    def raises_not_found(*_a, **_kw):
        raise FileNotFoundError("git not found")

    monkeypatch.setattr(worktrees_router.subprocess, "run", raises_not_found)

    body = client.get("/api/worktrees").json()
    assert body["worktrees"] == []
    assert "FileNotFoundError" in body["error"]


# ---------------------------------------------------------------------
# /api/artifacts/{track}/{slug}/force-preview
# ---------------------------------------------------------------------


def _lay_out_module(tmp_path: Path):
    """Create a synthetic checkout with every file --force would delete."""
    proj = tmp_path
    track_dir = proj / "curriculum" / "l2-uk-en" / "a1"
    orch_dir = track_dir / "orchestration" / "hello"
    for d in ("audit", "status", "research", "review", "activities", "vocabulary"):
        (track_dir / d).mkdir(parents=True, exist_ok=True)
    orch_dir.mkdir(parents=True, exist_ok=True)

    (track_dir / "hello.md").write_text("content", encoding="utf-8")
    (track_dir / "activities" / "hello.yaml").write_text("a", encoding="utf-8")
    (track_dir / "vocabulary" / "hello.yaml").write_text("v", encoding="utf-8")
    (track_dir / "review" / "hello-review-r1.md").write_text("r", encoding="utf-8")
    (track_dir / "review" / "hello-review-r2.md").write_text("r", encoding="utf-8")
    (track_dir / "audit" / "hello-audit.md").write_text("a", encoding="utf-8")
    (track_dir / "status" / "hello.json").write_text("{}", encoding="utf-8")
    (track_dir / "research" / "hello-knowledge-packet.md").write_text("k", encoding="utf-8")

    # Orchestration: keep + delete files/dirs.
    (orch_dir / "index.md").write_text("keep", encoding="utf-8")
    (orch_dir / "friction.yaml").write_text("keep", encoding="utf-8")
    (orch_dir / "state.json").write_text("{}", encoding="utf-8")
    (orch_dir / "dispatch").mkdir()
    (orch_dir / "dispatch" / "write.md").write_text("x", encoding="utf-8")

    # Published MDX.
    mdx_dir = proj / "starlight" / "src" / "content" / "docs" / "a1"
    mdx_dir.mkdir(parents=True)
    (mdx_dir / "hello.mdx").write_text("<p>", encoding="utf-8")

    # Plan (must be PRESERVED).
    plan = proj / "plans" / "a1" / "hello.yaml"
    plan.parent.mkdir(parents=True)
    plan.write_text("slug: hello", encoding="utf-8")

    return proj


def test_force_preview_enumerates_every_deletion_target(tmp_path, monkeypatch):
    """force-preview must list exactly what v6_build --force would delete.

    Pins the set of paths so an accidental change to
    ``v6_build._clean_build_artifacts`` that drops a category will
    make this test red.
    """
    proj = _lay_out_module(tmp_path)
    fake_levels = [{"id": "a1", "path": "l2-uk-en/a1"}]
    monkeypatch.setattr(artifacts_router, "LEVELS", fake_levels)
    monkeypatch.setattr(artifacts_router, "CURRICULUM_ROOT", proj / "curriculum")
    monkeypatch.setattr(artifacts_router, "PROJECT_ROOT", proj)
    monkeypatch.setattr(artifacts_router, "PLANS_ROOT", proj / "plans")

    resp = client.get("/api/artifacts/a1/hello/force-preview")
    assert resp.status_code == 200
    body = resp.json()

    categories = {t["category"] for t in body["would_remove"]}
    # Every category represented exactly once (or more where applicable).
    assert {"content", "activities", "vocabulary", "review", "audit",
            "status", "research", "orchestration", "published"} <= categories

    # Plan + kept orchestration files show up in `preserved`.
    assert any(p.endswith("plans/a1/hello.yaml") for p in body["preserved"])
    assert any(p.endswith("index.md") for p in body["preserved"])
    assert any(p.endswith("friction.yaml") for p in body["preserved"])

    # Kept files must NEVER appear in would_remove.
    removed_paths = {t["path"] for t in body["would_remove"]}
    for keep_basename in ("hello.yaml", "index.md", "friction.yaml"):
        # kept plan file
        assert not any(
            p.endswith(f"plans/a1/{keep_basename}") for p in removed_paths
        )


def test_force_preview_404_on_unknown_track(monkeypatch):
    monkeypatch.setattr(artifacts_router, "LEVELS", [{"id": "a1", "path": "l2-uk-en/a1"}])
    resp = client.get("/api/artifacts/does-not-exist/foo/force-preview")
    assert resp.status_code == 404


def test_force_preview_empty_for_nonexistent_slug(tmp_path, monkeypatch):
    """Unknown slug on valid track returns zero targets — never 500s."""
    proj = tmp_path
    (proj / "curriculum" / "l2-uk-en" / "a1").mkdir(parents=True)
    monkeypatch.setattr(
        artifacts_router, "LEVELS", [{"id": "a1", "path": "l2-uk-en/a1"}],
    )
    monkeypatch.setattr(artifacts_router, "CURRICULUM_ROOT", proj / "curriculum")
    monkeypatch.setattr(artifacts_router, "PROJECT_ROOT", proj)
    monkeypatch.setattr(artifacts_router, "PLANS_ROOT", proj / "plans")

    body = client.get("/api/artifacts/a1/never-existed/force-preview").json()
    assert body["count"] == 0
    assert body["would_remove"] == []
    assert body["total_bytes"] == 0
