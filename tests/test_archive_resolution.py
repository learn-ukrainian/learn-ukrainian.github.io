"""A1 bookmark compatibility must not repopulate the upgraded roster."""

from pathlib import Path

import pytest

from scripts.audit.validate_atlas_conformance import _check_cross_links
from scripts.level_config import resolve_content_track, resolve_manifest_module_track
from scripts.pipeline import learner_state

pytestmark = pytest.mark.reads_content


@pytest.mark.parametrize("canonical", [[], ["shared"]])
def test_manifest_resolution_preserves_rosters_and_canonical_precedence(canonical):
    levels = {"a1": {"modules": canonical}, "a1-v1": {"modules": ["shared", "old"]}}
    assert resolve_manifest_module_track("a1", "shared", levels) == ("a1" if canonical else "a1-v1")
    assert resolve_manifest_module_track("a1", "old", levels) == "a1-v1"
    assert resolve_manifest_module_track("a1", "missing", levels) == "a1"
    assert resolve_manifest_module_track("a2", "old", levels) == "a2"
    assert levels["a1"]["modules"] == canonical


@pytest.mark.parametrize("body", ["module.md", "lesson-1/module.md", "../shared.md"])
def test_content_resolution_uses_one_edition_and_prefers_canonical(tmp_path: Path, body: str):
    old = tmp_path / "a1-v1/shared"
    old.mkdir(parents=True)
    (old / "module.md").write_text("archived content")
    canonical = tmp_path / "a1/shared"
    canonical.mkdir(parents=True)
    (canonical / "lessons.yaml").write_text("lessons: []")
    assert resolve_content_track("a1", "shared", tmp_path) == "a1-v1"
    assert resolve_content_track("a1", "missing", tmp_path) == "a1"
    assert resolve_content_track("a2", "shared", tmp_path) == "a2"
    published = canonical / body
    published.parent.mkdir(parents=True, exist_ok=True)
    published.write_text("upgraded content")
    assert resolve_content_track("a1", "shared", tmp_path) == "a1"


def test_atlas_archive_links_resolve_but_unknown_slugs_still_fail():
    violations = []
    _check_cross_links(
        {"course_usage": [
            {"track": "a1", "slug": "old"},
            {"track": "a1-v1", "slug": "old"},
            {"track": "a1", "slug": "missing"},
            {"track": "a2", "slug": "old"},
        ]},
        "fixture", {("a1-v1", "old")}, violations,
    )
    assert len(violations) == 2
    assert all(item.gate == "cross_link_integrity" for item in violations)
    assert "missing" in violations[0].detail
    assert "a2" in violations[1].detail


def test_vocabulary_fallback_and_canonical_precedence(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(learner_state, "CURRICULUM_ROOT", tmp_path)
    archive = tmp_path / "a1-v1/shared"
    archive.mkdir(parents=True)
    (archive / "module.md").write_text("archive")
    (archive / "vocabulary.yaml").write_text("items: [{lemma: archive}]")
    assert learner_state._load_vocab("a1", "shared") == ["archive"]
    canonical = tmp_path / "a1/shared"
    canonical.mkdir(parents=True)
    (canonical / "module.md").write_text("canonical")
    # Missing canonical vocabulary must not be silently supplied by the archive.
    assert learner_state._load_vocab("a1", "shared") == []
    (canonical / "vocabulary.yaml").write_text("items: [{lemma: canonical}]")
    assert learner_state._load_vocab("a1", "shared") == ["canonical"]


def test_empty_canonical_learner_roster_does_not_inherit_archive(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(learner_state, "CURRICULUM_ROOT", tmp_path)
    (tmp_path / "curriculum.yaml").write_text(
        "levels:\n  a1:\n    modules: []\n  a1-v1:\n    modules: [old]\n"
    )
    state = learner_state.build_learner_state("a1", 20)
    assert state["module_count"] == 0
    assert state["cumulative_vocabulary"] == []
