"""Tests for P1 follow-up endpoints (#1313 / Codex 1, 2, 3, 8).

Covers:
    /api/state/module/{track}/slug/{slug}            slug-keyed compact view
    /api/artifacts/{track}/{slug}/files              classified file manifest
    /api/artifacts/{track}/{slug}/review-snapshot    main + style + empty flag
    /api/artifacts/{track}/{slug}/drift              state cross-check
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

import scripts.api.artifacts_router as artifacts_router
import scripts.api.main as api_main
import scripts.api.state_router as state_router

client = TestClient(api_main.app, raise_server_exceptions=False)


# ---------------------------------------------------------------------
# /api/state/module/{track}/slug/{slug}
# ---------------------------------------------------------------------


def test_module_by_slug_compact_default(monkeypatch):
    fake_levels = [{"id": "a1", "path": "l2-uk-en/a1"}]
    monkeypatch.setattr(state_router, "LEVELS", fake_levels)
    monkeypatch.setattr(
        state_router, "get_plan_slugs",
        lambda _t: [(3, "target-slug")],
    )

    def fake_detail(track, num, cfg):
        return {
            "track": track, "num": num, "slug": "target-slug",
            "pipeline_version": "v6", "needs_rebuild": False,
            "phases": {
                "write": {"status": "complete", "executor": {"agent": "gemini"}},
                "review": {"status": "in_progress", "executor": {"agent": "claude"}, "retries": 2},
            },
            "audit": {"status": "pass", "word_count": 1300, "word_target": 1200,
                      "blocking_issues": []},
            "review": {"score": 9.4, "verdict": "PASS"},
            "final_review": {"exists": True, "verdict": "PASS"},
            "shippable": True,
        }

    monkeypatch.setattr(state_router, "compute_module_detail", fake_detail)

    resp = client.get("/api/state/module/a1/slug/target-slug")
    assert resp.status_code == 200
    body = resp.json()
    assert body["num"] == 3
    assert body["slug"] == "target-slug"
    assert body["phase"] == "review"  # current in-progress
    assert body["last_successful"] == "write"
    assert body["retry_count"] == 2
    assert body["worker"] == "claude"
    assert body["review"]["score"] == 9.4
    assert body["shippable"] is True
    # Compact projection must NOT leak the full phases payload.
    assert "phases" not in body


def test_module_by_slug_verbose_returns_full_payload(monkeypatch):
    fake_levels = [{"id": "a1", "path": "l2-uk-en/a1"}]
    monkeypatch.setattr(state_router, "LEVELS", fake_levels)
    monkeypatch.setattr(state_router, "get_plan_slugs", lambda _t: [(1, "x")])
    monkeypatch.setattr(
        state_router, "compute_module_detail",
        lambda *_a, **_kw: {"num": 1, "slug": "x", "phases": {"write": {"status": "complete"}}},
    )

    body = client.get("/api/state/module/a1/slug/x?verbose=true").json()
    assert "phases" in body


def test_module_by_slug_404_on_unknown_slug(monkeypatch):
    fake_levels = [{"id": "a1", "path": "l2-uk-en/a1"}]
    monkeypatch.setattr(state_router, "LEVELS", fake_levels)
    monkeypatch.setattr(state_router, "get_plan_slugs", lambda _t: [(1, "one")])

    resp = client.get("/api/state/module/a1/slug/nope")
    assert resp.status_code == 404
    assert "not found" in resp.json()["error"]


# ---------------------------------------------------------------------
# /api/artifacts/{track}/{slug}/files
# ---------------------------------------------------------------------


def _classification_fixture(tmp_path: Path, monkeypatch):
    proj = tmp_path
    base = proj / "curriculum" / "l2-uk-en" / "a1"
    (base / "audit").mkdir(parents=True, exist_ok=True)
    (base / "status").mkdir(exist_ok=True)
    (base / "activities").mkdir(exist_ok=True)
    (base / "vocabulary").mkdir(exist_ok=True)
    (base / "review").mkdir(exist_ok=True)
    (base / "research").mkdir(exist_ok=True)
    orch = base / "orchestration" / "hello"
    orch.mkdir(parents=True, exist_ok=True)

    # Source of truth
    plan_dir = proj / "plans" / "a1"
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan = plan_dir / "hello.yaml"
    plan.write_text("slug: hello", encoding="utf-8")
    (orch / "index.md").write_text("notes", encoding="utf-8")
    (orch / "friction.yaml").write_text("frictions", encoding="utf-8")

    # Generated (all NEWER than plan — not stale).
    (base / "hello.md").write_text("content", encoding="utf-8")
    (base / "activities" / "hello.yaml").write_text("a", encoding="utf-8")
    (base / "audit" / "hello-audit.md").write_text("a", encoding="utf-8")
    (orch / "state.json").write_text("{}", encoding="utf-8")

    # Bump plan back to OLDER than generated so the stale check is off.
    import os
    base_mtime = plan.stat().st_mtime
    for p in (base / "hello.md", base / "audit" / "hello-audit.md"):
        os.utime(p, (base_mtime + 100, base_mtime + 100))

    # Published
    mdx_dir = proj / "starlight" / "src" / "content" / "docs" / "a1"
    mdx_dir.mkdir(parents=True, exist_ok=True)
    (mdx_dir / "hello.mdx").write_text("<p>", encoding="utf-8")

    monkeypatch.setattr(
        artifacts_router, "LEVELS", [{"id": "a1", "path": "l2-uk-en/a1"}],
    )
    monkeypatch.setattr(artifacts_router, "CURRICULUM_ROOT", proj / "curriculum")
    monkeypatch.setattr(artifacts_router, "PROJECT_ROOT", proj)
    monkeypatch.setattr(artifacts_router, "PLANS_ROOT", proj / "plans")
    return proj, plan


def test_files_classifies_source_generated_published(tmp_path, monkeypatch):
    _classification_fixture(tmp_path, monkeypatch)

    body = client.get("/api/artifacts/a1/hello/files").json()
    assert set(body["counts"]) == {"source_of_truth", "generated", "published", "stale"}
    assert body["counts"]["published"] == 1
    assert body["counts"]["source_of_truth"] >= 3  # plan + index.md + friction.yaml
    assert body["counts"]["generated"] >= 2

    # Plan must land in source_of_truth bucket, not generated.
    sot_paths = {f["path"] for f in body["buckets"]["source_of_truth"]}
    assert any(p.endswith("plans/a1/hello.yaml") for p in sot_paths)


def test_files_detects_stale_generated_artifact(tmp_path, monkeypatch):
    """An artifact older than plan.yaml lands in the stale bucket."""
    _proj, plan = _classification_fixture(tmp_path, monkeypatch)

    # Push the plan's mtime FAR into the future so generated output is stale.
    import os
    future = plan.stat().st_mtime + 10_000
    os.utime(plan, (future, future))

    body = client.get("/api/artifacts/a1/hello/files").json()
    stale_paths = {f["path"] for f in body["buckets"]["stale"]}
    assert any(p.endswith("hello.md") for p in stale_paths)


def test_files_404_on_unknown_track(monkeypatch):
    monkeypatch.setattr(
        artifacts_router, "LEVELS", [{"id": "a1", "path": "l2-uk-en/a1"}],
    )
    resp = client.get("/api/artifacts/does-not-exist/foo/files")
    assert resp.status_code == 404


# ---------------------------------------------------------------------
# /api/artifacts/{track}/{slug}/review-snapshot
# ---------------------------------------------------------------------


def test_review_snapshot_flags_empty_findings_with_high_score(tmp_path, monkeypatch):
    proj = tmp_path
    base = proj / "curriculum" / "l2-uk-en" / "a1"
    (base / "review").mkdir(parents=True, exist_ok=True)
    # High score + zero findings == reviewer-gaming pattern.
    (base / "review" / "hello-review.md").write_text(
        "# Review\n**Overall Score:** 9.5/10\n**Status:** PASS\n"
        "Looks great overall, ensuring a high score.\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        artifacts_router, "LEVELS", [{"id": "a1", "path": "l2-uk-en/a1"}],
    )
    monkeypatch.setattr(artifacts_router, "CURRICULUM_ROOT", proj / "curriculum")
    monkeypatch.setattr(artifacts_router, "PROJECT_ROOT", proj)

    body = client.get("/api/artifacts/a1/hello/review-snapshot").json()
    assert body["main_review"]["score"] == 9.5
    assert body["main_review"]["findings_count"] == 0
    assert body["main_review"]["empty_findings_flag"] is True
    assert body["any_empty_findings_flag"] is True


def test_review_snapshot_no_flag_when_low_score_or_findings(tmp_path, monkeypatch):
    proj = tmp_path
    base = proj / "curriculum" / "l2-uk-en" / "a1"
    (base / "review").mkdir(parents=True, exist_ok=True)
    (base / "review" / "hi-review.md").write_text(
        "# Issue #1\nCorrect this.\n**Overall Score:** 9.1/10\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        artifacts_router, "LEVELS", [{"id": "a1", "path": "l2-uk-en/a1"}],
    )
    monkeypatch.setattr(artifacts_router, "CURRICULUM_ROOT", proj / "curriculum")
    monkeypatch.setattr(artifacts_router, "PROJECT_ROOT", proj)

    body = client.get("/api/artifacts/a1/hi/review-snapshot").json()
    assert body["main_review"]["findings_count"] == 1
    assert body["main_review"]["empty_findings_flag"] is False


def test_review_snapshot_handles_missing_files(tmp_path, monkeypatch):
    proj = tmp_path
    (proj / "curriculum" / "l2-uk-en" / "a1").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        artifacts_router, "LEVELS", [{"id": "a1", "path": "l2-uk-en/a1"}],
    )
    monkeypatch.setattr(artifacts_router, "CURRICULUM_ROOT", proj / "curriculum")
    monkeypatch.setattr(artifacts_router, "PROJECT_ROOT", proj)

    body = client.get("/api/artifacts/a1/absent/review-snapshot").json()
    assert body["main_review"] is None
    assert body["style_review"] is None
    assert body["any_empty_findings_flag"] is False


# ---------------------------------------------------------------------
# /api/artifacts/{track}/{slug}/drift
# ---------------------------------------------------------------------


def _drift_fixture(tmp_path: Path, monkeypatch):
    proj = tmp_path
    base = proj / "curriculum" / "l2-uk-en" / "a1"
    (base / "orchestration" / "hello").mkdir(parents=True, exist_ok=True)
    (base / "status").mkdir(exist_ok=True)
    mdx_dir = proj / "starlight" / "src" / "content" / "docs" / "a1"
    mdx_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(
        artifacts_router, "LEVELS", [{"id": "a1", "path": "l2-uk-en/a1"}],
    )
    monkeypatch.setattr(artifacts_router, "CURRICULUM_ROOT", proj / "curriculum")
    monkeypatch.setattr(artifacts_router, "PROJECT_ROOT", proj)
    return proj, base, mdx_dir


def test_drift_flags_publish_complete_without_mdx(tmp_path, monkeypatch):
    _proj, base, _mdx = _drift_fixture(tmp_path, monkeypatch)
    # state says publish=complete
    (base / "orchestration" / "hello" / "state.json").write_text(
        json.dumps({"phases": {"publish": {"status": "complete"}}}),
        encoding="utf-8",
    )
    # Stub downstream helpers
    monkeypatch.setattr(
        artifacts_router, "get_audit_status",
        lambda *_a, **_kw: {"status": "pass"},
    )
    monkeypatch.setattr(
        artifacts_router, "get_final_review_info",
        lambda *_a, **_kw: None,
    )
    monkeypatch.setattr(
        artifacts_router, "find_content_file",
        lambda *_a, **_kw: base / "hello.md",
    )
    # content file exists so audit_passes_without_content doesn't fire
    (base / "hello.md").write_text("c", encoding="utf-8")

    body = client.get("/api/artifacts/a1/hello/drift").json()
    kinds = {d["kind"] for d in body["drift"]}
    assert "publish_mdx_missing" in kinds
    assert body["in_sync"] is False


def test_drift_flags_mdx_without_state(tmp_path, monkeypatch):
    _proj, _base, mdx = _drift_fixture(tmp_path, monkeypatch)
    # MDX present but no state.json
    (mdx / "hello.mdx").write_text("<p>", encoding="utf-8")
    monkeypatch.setattr(
        artifacts_router, "get_audit_status",
        lambda *_a, **_kw: {"status": "not_run"},
    )
    monkeypatch.setattr(
        artifacts_router, "get_final_review_info",
        lambda *_a, **_kw: None,
    )
    monkeypatch.setattr(
        artifacts_router, "find_content_file", lambda *_a, **_kw: None,
    )

    body = client.get("/api/artifacts/a1/hello/drift").json()
    kinds = {d["kind"] for d in body["drift"]}
    assert "mdx_without_state" in kinds


def test_drift_in_sync_when_everything_agrees(tmp_path, monkeypatch):
    _proj, base, mdx = _drift_fixture(tmp_path, monkeypatch)
    (base / "orchestration" / "hello" / "state.json").write_text(
        json.dumps({"phases": {"publish": {"status": "complete"}}}),
        encoding="utf-8",
    )
    (mdx / "hello.mdx").write_text("<p>", encoding="utf-8")
    content = base / "hello.md"
    content.write_text("c", encoding="utf-8")

    monkeypatch.setattr(
        artifacts_router, "get_audit_status",
        lambda *_a, **_kw: {"status": "pass"},
    )
    monkeypatch.setattr(
        artifacts_router, "get_final_review_info",
        lambda *_a, **_kw: {"exists": True, "verdict": "PASS"},
    )
    monkeypatch.setattr(
        artifacts_router, "find_content_file", lambda *_a, **_kw: content,
    )

    body = client.get("/api/artifacts/a1/hello/drift").json()
    assert body["in_sync"] is True
    assert body["drift"] == []
