"""A1 bookmark compatibility must not repopulate the upgraded roster."""

from pathlib import Path

import pytest

from scripts import manifest_utils
from scripts.audit import certify_module, module_size_policy_audit, track_deterministic_audit
from scripts.audit.validate_atlas_conformance import _check_cross_links
from scripts.generate_mdx import core as mdx_core
from scripts.level_config import resolve_content_track, resolve_manifest_module_track
from scripts.pipeline import learner_state


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


@pytest.mark.parametrize("canonical", [[], ["shared"]])
def test_slug_lookup_prefers_canonical_even_when_archive_is_first(monkeypatch, canonical):
    monkeypatch.setattr(manifest_utils, "load_manifest", lambda: {"levels": {
        "a1-v1": {"type": "core", "base_level": "a1", "modules": ["shared"]},
        "a1": {"type": "core", "modules": canonical},
    }})
    monkeypatch.setattr(manifest_utils, "_load_meta_file", lambda *_: {})
    assert manifest_utils.get_module_by_slug("shared").level == ("a1" if canonical else "a1-v1")


def test_archived_certification_uses_archive_commands_and_base_plan():
    target = certify_module.parse_target(["a1/sounds-letters-and-hello"])
    assert target.content_level == "a1-v1"
    assert target.module_dir.name == "sounds-letters-and-hello"
    assert target.mdx_path.is_file()
    checks = {check.name: check.command for check in certify_module.build_checks(
        target, site_build=False, install_site_deps=False,
    )}
    assert checks["generate MDX"][3:5] == ("a1-v1", "1")
    assert checks["validate activities"][3:5] == ("a1-v1", "1")
    assert checks["validate plan config"][-1] == "a1/sounds-letters-and-hello"
    archive = certify_module.parse_target(["a1-v1/sounds-letters-and-hello"])
    assert certify_module.plan_source_file(archive).is_file()
    modules = mdx_core.get_modules_from_manifest(target.content_level)
    assert len(modules) == 55
    assert modules[target.local_num - 1].slug == target.slug
    assert mdx_core.get_modules_from_manifest("a1") == []


def test_pbr_child_audits_select_actual_archive_content():
    slug = "sounds-letters-and-hello"
    modules = track_deterministic_audit.select_modules("a1", None, {slug})
    assert len(modules) == 1
    assert modules[0].module_md.is_file()
    assert modules[0].module_dir.parent.name == "a1-v1"
    assert modules[0].plan.parent.name == "a1"
    assert modules[0].plan.is_file()
    plans = module_size_policy_audit.select_plan_paths(["a1"], {slug}, True)
    assert len(plans) == 1
    assert module_size_policy_audit._module_path("a1", slug) == modules[0].module_md
    assert track_deterministic_audit.select_modules("a1", None, {"missing"}) == []


def test_optional_mdx_audit_invokes_the_resolved_edition(monkeypatch):
    from types import SimpleNamespace

    paths = track_deterministic_audit.select_modules("a1", None, {"sounds-letters-and-hello"})[0]
    commands = []

    def run(argv, **kwargs):
        commands.append(argv)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(track_deterministic_audit.subprocess, "run", run)
    assert track_deterministic_audit.run_mdx_validate(paths) == []
    assert commands[0][3:5] == ["a1-v1", "1"]


def test_archive_generator_writes_real_module_to_isolated_output(tmp_path, monkeypatch):
    import sys

    import yaml

    monkeypatch.setattr(mdx_core, "STARLIGHT_DOCS_DIR", tmp_path)
    monkeypatch.setattr(sys, "argv", ["generate_mdx.py", "l2-uk-en", "a1-v1", "1"])
    mdx_core.main()
    output = tmp_path / "a1-v1/sounds-letters-and-hello.mdx"
    assert output.is_file()
    assert list(tmp_path.rglob("*.mdx")) == [output]
    frontmatter, body = mdx_core.parse_frontmatter(output.read_text())
    plan = yaml.safe_load((mdx_core.CURRICULUM_DIR / "l2-uk-en/plans/a1/sounds-letters-and-hello.yaml").read_text())
    assert frontmatter["title"] == plan["title"]
    assert len(body) > 1000
