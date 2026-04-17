"""Tests for P2 content-delivery-to-production endpoints (GH #1309).

Covered:
    /api/artifacts/{track}/{slug}   per-module gate snapshot
    /api/artifacts/ship-ready       aggregate ship-ready list
    /api/site/health                public-site reachability + freshness
    /api/site/deployments           recent GH Pages deploys
"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

import scripts.api.artifacts_router as artifacts_router
import scripts.api.main as api_main
import scripts.api.site_router as site_router

client = TestClient(api_main.app, raise_server_exceptions=False)


# ---------------------------------------------------------------------
# /api/artifacts/{track}/{slug}
# ---------------------------------------------------------------------


def _valid_mdx(path: Path, body: str = "Learners greet each other.") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        "title: Hello\n"
        "description: Greetings\n"
        "---\n\n"
        "# Hello\n\n"
        + (body + " ") * 200,
        encoding="utf-8",
    )


def _set_env(tmp_path: Path, monkeypatch):
    """Redirect the artifact router at a synthetic checkout."""
    curr = tmp_path / "curriculum" / "l2-uk-en"
    plans = tmp_path / "plans" / "a1"
    curr.mkdir(parents=True)
    plans.mkdir(parents=True)

    fake_levels = [{"id": "a1", "path": "l2-uk-en/a1"}]
    monkeypatch.setattr(artifacts_router, "LEVELS", fake_levels)
    monkeypatch.setattr(artifacts_router, "CURRICULUM_ROOT", tmp_path / "curriculum")
    monkeypatch.setattr(artifacts_router, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(artifacts_router, "PLANS_ROOT", tmp_path / "plans")
    return curr / "a1", plans


def _stub_gates(monkeypatch, *, audit_status="pass", word_count=1200, word_target=1200,
                review_score=9.2, final_verdict: str | None = "PASS"):
    monkeypatch.setattr(
        artifacts_router, "get_audit_status",
        lambda *_a, **_kw: {
            "status": audit_status,
            "word_count": word_count,
            "word_target": word_target,
            "blocking_issues": [],
        },
    )
    monkeypatch.setattr(
        artifacts_router, "_get_review_score",
        lambda *_a, **_kw: {"exists": True, "score": review_score, "verdict": "PASS"},
    )
    monkeypatch.setattr(
        artifacts_router, "get_final_review_info",
        lambda *_a, **_kw: (
            {"exists": True, "verdict": final_verdict, "score": review_score}
            if final_verdict else None
        ),
    )
    monkeypatch.setattr(
        artifacts_router, "get_word_target_from_plan",
        lambda *_a, **_kw: word_target,
    )


def test_module_artifact_all_gates_green(tmp_path, monkeypatch):
    track_dir, plans = _set_env(tmp_path, monkeypatch)
    content_path = track_dir / "hello.md"
    _valid_mdx(content_path)
    plan_path = plans / "hello.yaml"
    plan_path.write_text("slug: hello\n", encoding="utf-8")

    # Make the plan OLDER than the content so plan_fresh is True.
    import os
    older = content_path.stat().st_mtime - 60
    os.utime(plan_path, (older, older))

    _stub_gates(monkeypatch)
    monkeypatch.setattr(
        artifacts_router, "find_content_file",
        lambda _track_dir, slug: content_path if slug == "hello" else None,
    )

    resp = client.get("/api/artifacts/a1/hello")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ship_ready"] is True
    assert all(body["gates"].values()), body["gates"]


def test_module_artifact_flags_stale_plan(tmp_path, monkeypatch):
    track_dir, plans = _set_env(tmp_path, monkeypatch)
    content_path = track_dir / "hello.md"
    _valid_mdx(content_path)
    plan_path = plans / "hello.yaml"
    plan_path.write_text("slug: hello\n", encoding="utf-8")

    # Plan is NEWER than content — rebuild required before shipping.
    import os
    newer = content_path.stat().st_mtime + 60
    os.utime(plan_path, (newer, newer))

    _stub_gates(monkeypatch)
    monkeypatch.setattr(
        artifacts_router, "find_content_file",
        lambda _track_dir, slug: content_path if slug == "hello" else None,
    )

    body = client.get("/api/artifacts/a1/hello").json()
    assert body["gates"]["plan_fresh"] is False
    assert body["ship_ready"] is False


def test_module_artifact_flags_missing_frontmatter(tmp_path, monkeypatch):
    track_dir, plans = _set_env(tmp_path, monkeypatch)
    content_path = track_dir / "hello.md"
    content_path.parent.mkdir(parents=True, exist_ok=True)
    content_path.write_text("No frontmatter here.\n", encoding="utf-8")
    plan_path = plans / "hello.yaml"
    plan_path.write_text("slug: hello\n", encoding="utf-8")

    _stub_gates(monkeypatch)
    monkeypatch.setattr(
        artifacts_router, "find_content_file",
        lambda _track_dir, slug: content_path if slug == "hello" else None,
    )

    body = client.get("/api/artifacts/a1/hello").json()
    assert body["gates"]["frontmatter_valid"] is False
    assert body["ship_ready"] is False


def test_module_artifact_404_on_unknown_track(tmp_path, monkeypatch):
    _set_env(tmp_path, monkeypatch)
    resp = client.get("/api/artifacts/does-not-exist/foo")
    assert resp.status_code == 404


def test_module_artifact_fails_when_final_review_missing(tmp_path, monkeypatch):
    track_dir, plans = _set_env(tmp_path, monkeypatch)
    content_path = track_dir / "hello.md"
    _valid_mdx(content_path)
    plan_path = plans / "hello.yaml"
    plan_path.write_text("slug: hello\n", encoding="utf-8")

    _stub_gates(monkeypatch, final_verdict=None)
    monkeypatch.setattr(
        artifacts_router, "find_content_file",
        lambda _track_dir, slug: content_path if slug == "hello" else None,
    )

    body = client.get("/api/artifacts/a1/hello").json()
    assert body["gates"]["final_review_pass"] is False
    assert body["ship_ready"] is False


# ---------------------------------------------------------------------
# /api/artifacts/ship-ready
# ---------------------------------------------------------------------


def test_ship_ready_aggregates(monkeypatch):
    """ship-ready walks all plans and filters on ALL gates green."""
    fake_levels = [{"id": "a1", "path": "l2-uk-en/a1"}]
    monkeypatch.setattr(artifacts_router, "LEVELS", fake_levels)

    monkeypatch.setattr(
        artifacts_router, "get_plan_slugs",
        lambda _track: [(1, "ready"), (2, "stale-plan")],
    )

    def fake_snapshot(track, slug):
        if slug == "ready":
            return {
                "ship_ready": True,
                "track": track,
                "slug": slug,
                "review": {"score": 9.5},
                "audit": {"word_count": 1300, "word_target": 1200},
            }
        return {"ship_ready": False, "track": track, "slug": slug,
                "review": {"score": 9.0}, "audit": {}}

    monkeypatch.setattr(artifacts_router, "_compute_artifact_snapshot", fake_snapshot)

    resp = client.get("/api/artifacts/ship-ready?track=a1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["modules_inspected"] == 2
    assert body["ship_ready_count"] == 1
    assert body["ship_ready"][0]["slug"] == "ready"
    assert body["ship_ready"][0]["review_score"] == 9.5


# ---------------------------------------------------------------------
# /api/site/health
# ---------------------------------------------------------------------


def test_site_health_graceful_when_offline(monkeypatch):
    """Network-free site health check. Every field degrades gracefully."""
    monkeypatch.setattr(
        site_router, "_canary_probes",
        lambda _url: [{"url": "https://example/", "status": None, "error": "URLError: offline"}],
    )
    monkeypatch.setattr(site_router, "_last_astro_build", lambda: {"built": False})
    monkeypatch.setattr(site_router, "_last_deploy_commit", lambda: {"error": "no gh-pages ref"})
    monkeypatch.setattr(site_router, "_sitemap_freshness", lambda: {"exists": False})

    resp = client.get("/api/site/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["reachable"] is False
    assert body["canaries"][0]["error"].startswith("URLError")
    assert body["last_astro_build"]["built"] is False
    assert body["last_deploy_commit"]["error"]


def test_site_health_reachable_when_canary_200(monkeypatch):
    monkeypatch.setattr(
        site_router, "_canary_probes",
        lambda _url: [{"url": "https://example/", "status": 200, "elapsed_ms": 42}],
    )
    monkeypatch.setattr(site_router, "_last_astro_build", lambda: {"built": True})
    monkeypatch.setattr(site_router, "_last_deploy_commit", lambda: {"sha": "abc123"})
    monkeypatch.setattr(site_router, "_sitemap_freshness", lambda: {"exists": True})

    body = client.get("/api/site/health").json()
    assert body["reachable"] is True


# ---------------------------------------------------------------------
# /api/site/deployments
# ---------------------------------------------------------------------


def test_deployments_surfaces_gh_error_gracefully(monkeypatch):
    """gh not authed / not installed → error field, not 500."""

    class FakeProc:
        returncode = 1
        stdout = ""
        stderr = "gh: command not found"

    monkeypatch.setattr(site_router, "_run", lambda *_a, **_kw: FakeProc())

    resp = client.get("/api/site/deployments")
    assert resp.status_code == 200
    body = resp.json()
    assert body["runs"] == []
    assert "gh: command not found" in body["error"]


def test_deployments_returns_parsed_runs(monkeypatch):
    class FakeProc:
        returncode = 0
        stdout = '[{"databaseId":1,"conclusion":"success","headSha":"abc","displayTitle":"deploy"}]'
        stderr = ""

    monkeypatch.setattr(site_router, "_run", lambda *_a, **_kw: FakeProc())

    body = client.get("/api/site/deployments?limit=1").json()
    assert body["runs"][0]["conclusion"] == "success"


# ---------------------------------------------------------------------
# Post-review regression tests (GH #1309 final review pass)
# ---------------------------------------------------------------------


def test_site_run_swallows_timeout_expired(monkeypatch):
    """site_router._run must catch subprocess.TimeoutExpired.

    Regression for the #1309 final-review BLOCKER: both reviewers
    flagged that a hung `git ls-remote` or `gh run list` would leak
    ``TimeoutExpired`` into FastAPI and return HTTP 500, violating
    the file's "every field degrades to an error string" contract.
    """
    import subprocess

    def raises_timeout(*_a, **_kw):
        raise subprocess.TimeoutExpired(cmd=["gh"], timeout=3.0)

    monkeypatch.setattr(site_router.subprocess, "run", raises_timeout)

    proc = site_router._run(["gh", "run", "list"], timeout_s=3.0)
    assert proc.returncode == 124
    assert "TimeoutExpired" in proc.stderr


def test_site_run_swallows_missing_binary(monkeypatch):
    """site_router._run must catch FileNotFoundError when gh / git isn't on PATH.

    Regression for #1309 final review: a fresh machine without the
    gh CLI installed would 500 on /api/site/deployments.
    """
    def raises_not_found(*_a, **_kw):
        raise FileNotFoundError("gh not in PATH")

    monkeypatch.setattr(site_router.subprocess, "run", raises_not_found)

    proc = site_router._run(["gh", "run", "list"], timeout_s=3.0)
    assert proc.returncode == 127
    assert "FileNotFoundError" in proc.stderr


def test_site_deployments_200_when_gh_times_out(monkeypatch):
    """End-to-end: /api/site/deployments must stay 200 on timeout."""
    import subprocess

    def raises_timeout(*_a, **_kw):
        raise subprocess.TimeoutExpired(cmd=["gh"], timeout=5.0)

    monkeypatch.setattr(site_router.subprocess, "run", raises_timeout)

    resp = client.get("/api/site/deployments")
    assert resp.status_code == 200
    body = resp.json()
    assert body["runs"] == []
    assert "TimeoutExpired" in body["error"]


def test_module_artifact_404_on_unknown_slug(tmp_path, monkeypatch):
    """Unknown slug on a valid track must 404, not 200-with-all-gates-false.

    Reviewer CONCERN Codex-1 / #1309: typo detection was impossible
    because an unknown module looked identical to a known-but-
    unshippable one.
    """
    _set_env(tmp_path, monkeypatch)
    monkeypatch.setattr(
        artifacts_router, "find_content_file", lambda *_a, **_kw: None,
    )
    resp = client.get("/api/artifacts/a1/does-not-exist")
    assert resp.status_code == 404
    assert "unknown module" in resp.json()["error"]


def test_ship_ready_404_on_unknown_track(monkeypatch):
    """Unknown track on ship-ready must 404, mirroring /{track}/{slug}.

    Reviewer CONCERN Codex-2 / #1309: previously silently returned
    an empty scan.
    """
    fake_levels = [{"id": "a1", "path": "l2-uk-en/a1"}]
    monkeypatch.setattr(artifacts_router, "LEVELS", fake_levels)
    resp = client.get("/api/artifacts/ship-ready?track=does-not-exist")
    assert resp.status_code == 404
