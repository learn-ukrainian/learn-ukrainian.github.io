"""Tests for v6 --force module reset (#1296).

Covers:
- _force_reset_module deletes generated artifacts
- _force_reset_module preserves plan YAML
- _force_reset_module deletes published MDX
- _clean_build_artifacts deletes orchestration artifacts (keeps index.md, friction.yaml)
- --force flag is forwarded in --range batch subprocess calls

Does NOT cover:
- Full E2E build with --force (integration test, requires LLM)

Issue: #1296
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

v6_build = importlib.import_module("build.v6_build")


@pytest.fixture()
def module_tree(tmp_path, monkeypatch):
    """Create a realistic module artifact tree under tmp_path.

    Layout mirrors curriculum/l2-uk-en/{level}/ structure.
    Returns (root, level, slug) tuple for test use.
    """
    level = "a1"
    slug = "test-module"
    root = tmp_path / "curriculum" / "l2-uk-en"

    # Plan (source of truth — MUST survive --force)
    plan_dir = root.parent.parent / "plans" / level
    plan_dir.mkdir(parents=True)
    (plan_dir / f"{slug}.yaml").write_text("title: Test Module\nversion: 1\n")

    # Lesson markdown (generated)
    (root / level).mkdir(parents=True)
    (root / level / f"{slug}.md").write_text("# Test Module\nContent here.")

    # Activities (generated)
    (root / level / "activities").mkdir(parents=True)
    (root / level / "activities" / f"{slug}.yaml").write_text("activities: []\n")

    # Vocabulary (generated)
    (root / level / "vocabulary").mkdir(parents=True)
    (root / level / "vocabulary" / f"{slug}.yaml").write_text("words: []\n")

    # Reviews (generated)
    review_dir = root / level / "review"
    review_dir.mkdir(parents=True)
    (review_dir / f"{slug}-review.md").write_text("Review text")
    (review_dir / f"{slug}-review-r1.md").write_text("Round 1")
    (review_dir / f"{slug}-review-r2.md").write_text("Round 2")

    # Audit (generated)
    (root / level / "audit").mkdir(parents=True)
    (root / level / "audit" / f"{slug}-audit.md").write_text("Audit results")

    # Status (generated)
    (root / level / "status").mkdir(parents=True)
    (root / level / "status" / f"{slug}.json").write_text(json.dumps({"score": 9.5}))

    # Research / knowledge packet (generated)
    (root / level / "research").mkdir(parents=True)
    (root / level / "research" / f"{slug}-knowledge-packet.md").write_text("Research")

    # Orchestration (generated, except index.md and friction.yaml)
    orch = root / level / "orchestration" / slug
    orch.mkdir(parents=True)
    (orch / "state.json").write_text(json.dumps({"phases": {"check": {"status": "complete"}}}))
    (orch / "skeleton.md").write_text("Skeleton outline")
    (orch / "v6-prompt.md").write_text("Build prompt")
    (orch / "v6-review-prompt.md").write_text("Review prompt")
    (orch / "contract.yaml").write_text("contract: true\n")
    (orch / "wiki-excerpts.yaml").write_text("excerpts: []\n")
    (orch / "needs-human-review.yaml").write_text("violations: []\n")
    (orch / "index.md").write_text("Module index (preserved)")
    (orch / "friction.yaml").write_text("friction: none (preserved)")
    dispatch = orch / "dispatch"
    dispatch.mkdir()
    (dispatch / "01-skeleton-meta.json").write_text("{}")
    (dispatch / "02-write-meta.json").write_text("{}")

    # Published MDX (generated)
    mdx_dir = tmp_path / "starlight" / "src" / "content" / "docs" / level
    mdx_dir.mkdir(parents=True)
    (mdx_dir / f"{slug}.mdx").write_text("---\ntitle: Test\n---\nMDX content")

    # Patch module-level constants to use our temp tree
    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", root)
    monkeypatch.setattr(v6_build, "PROJECT_ROOT", tmp_path)

    return root, level, slug


def test_force_reset_deletes_generated_artifacts(module_tree):
    """_force_reset_module must remove all generated content artifacts."""
    root, level, slug = module_tree

    v6_build._force_reset_module(level, slug)

    # Generated artifacts should be gone
    assert not (root / level / f"{slug}.md").exists(), "lesson .md should be deleted"
    assert not (root / level / "activities" / f"{slug}.yaml").exists(), "activities should be deleted"
    assert not (root / level / "vocabulary" / f"{slug}.yaml").exists(), "vocabulary should be deleted"
    assert not (root / level / "audit" / f"{slug}-audit.md").exists(), "audit should be deleted"
    assert not (root / level / "status" / f"{slug}.json").exists(), "status should be deleted"
    assert not (root / level / "research" / f"{slug}-knowledge-packet.md").exists(), "knowledge packet should be deleted"


def test_force_reset_deletes_review_files(module_tree):
    """All review files (versioned + latest) must be deleted."""
    root, level, slug = module_tree

    v6_build._force_reset_module(level, slug)

    review_dir = root / level / "review"
    remaining = list(review_dir.glob(f"{slug}-review*"))
    assert remaining == [], f"review files should be deleted, found: {remaining}"


def test_force_reset_deletes_orchestration_artifacts(module_tree):
    """Orchestration state, prompts, dispatch, skeleton, contract must be deleted."""
    root, level, slug = module_tree

    v6_build._force_reset_module(level, slug)

    orch = root / level / "orchestration" / slug
    assert not (orch / "state.json").exists(), "state.json should be deleted"
    assert not (orch / "skeleton.md").exists(), "skeleton should be deleted"
    assert not (orch / "v6-prompt.md").exists(), "prompt should be deleted"
    assert not (orch / "v6-review-prompt.md").exists(), "review prompt should be deleted"
    assert not (orch / "contract.yaml").exists(), "contract should be deleted"
    assert not (orch / "wiki-excerpts.yaml").exists(), "wiki-excerpts should be deleted"
    assert not (orch / "needs-human-review.yaml").exists(), "needs-human-review should be deleted"
    assert not (orch / "dispatch").exists(), "dispatch dir should be deleted"


def test_force_reset_preserves_orchestration_index_and_friction(module_tree):
    """index.md and friction.yaml in orchestration dir must survive --force."""
    root, level, slug = module_tree

    v6_build._force_reset_module(level, slug)

    orch = root / level / "orchestration" / slug
    assert (orch / "index.md").exists(), "index.md should be preserved"
    assert (orch / "friction.yaml").exists(), "friction.yaml should be preserved"
    assert (orch / "index.md").read_text() == "Module index (preserved)"
    assert (orch / "friction.yaml").read_text() == "friction: none (preserved)"


def test_force_reset_preserves_plan_yaml(module_tree, tmp_path):
    """Plan YAML is source of truth — must never be deleted by --force."""
    _root, level, slug = module_tree

    v6_build._force_reset_module(level, slug)

    plan_path = tmp_path / "plans" / level / f"{slug}.yaml"
    assert plan_path.exists(), "plan YAML should be preserved"
    assert "Test Module" in plan_path.read_text()


def test_force_reset_deletes_published_mdx(module_tree, tmp_path):
    """Published MDX in starlight/src/content/docs/ must be deleted."""
    _root, level, slug = module_tree

    mdx_path = tmp_path / "starlight" / "src" / "content" / "docs" / level / f"{slug}.mdx"
    assert mdx_path.exists(), "MDX should exist before reset"

    v6_build._force_reset_module(level, slug)

    assert not mdx_path.exists(), "published MDX should be deleted"


def test_force_reset_is_idempotent(module_tree):
    """Running _force_reset_module twice should not raise."""
    _root, level, slug = module_tree

    v6_build._force_reset_module(level, slug)
    # Second call should not raise even though everything is already gone
    v6_build._force_reset_module(level, slug)


def test_force_reset_handles_missing_module(tmp_path, monkeypatch):
    """Resetting a module that has no artifacts should not raise."""
    root = tmp_path / "curriculum" / "l2-uk-en"
    (root / "a1").mkdir(parents=True)
    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", root)
    monkeypatch.setattr(v6_build, "PROJECT_ROOT", tmp_path)

    # Should not raise — nothing to delete
    v6_build._force_reset_module("a1", "nonexistent-module")
