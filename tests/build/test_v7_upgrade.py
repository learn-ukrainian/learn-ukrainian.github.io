"""Upgrade wiring uses V7 writer/review transports; these tests never call a model."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml

from scripts.build import linear_pipeline, v7_build
from scripts.level_config import base_level
from tests.build.upgrade_fixtures import ORIGINAL, UPGRADED, extract_upgrade_fixtures, fixture_text

pytestmark = pytest.mark.reads_content


@pytest.fixture
def upgrade_root(tmp_path, monkeypatch):
    from scripts.build import cf_preflight
    from scripts.generate_mdx import atlas_links

    atlas = tmp_path / "atlas.json"
    atlas.write_text('{"entries": []}')
    monkeypatch.setattr(atlas_links, "_DEFAULT_MANIFEST", atlas)
    extract_upgrade_fixtures(tmp_path, "baseline")
    monkeypatch.setattr(v7_build, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(linear_pipeline, "plan_path_for", lambda level, slug: tmp_path / "curriculum/l2-uk-en/plans/a1" / f"{slug}.yaml")
    # Isolated fixture roots are not git checkouts; seed exact-head clearance so
    # paid-upgrade tests exercise writer/review contracts past CF preflight.
    head = "a" * 40
    monkeypatch.setattr(cf_preflight, "git_head", lambda _root: head)
    cf_preflight.write_clearance_file(tmp_path / "cf_clearance.json", head=head)
    return tmp_path


@pytest.mark.parametrize("writer", ["gemini-tools", "codex-tools"])
def test_upgrade_dry_run_saves_full_prompt_without_writer(upgrade_root, monkeypatch, writer):
    forbidden = Mock(side_effect=AssertionError("dry-run called a model or wiki retrieval"))
    for name in ("invoke_writer", "build_knowledge_packet", "build_wiki_manifest_data"):
        monkeypatch.setattr(linear_pipeline, name, forbidden)
    args = v7_build.parse_args(["a1", "things-have-gender", "--upgrade", "--dry-run", "--writer", writer])
    assert v7_build._run(args) == 0
    output = upgrade_root / UPGRADED
    prompt = (output / "writer_prompt.md").read_text()
    assert "Mode: upgrade" in prompt
    assert "NO named narrator" in prompt
    assert "Classify the archive" in prompt
    assert "watch-and-repeat" in prompt
    assert "untaught" in prompt.lower() or "cannot read" in prompt.lower()
    assert "file=activities.yaml" in prompt
    # #7994: named sources MCP probes, theory + landing; shell VESUM is no proof.
    assert "mcp__sources__search_text" in prompt
    assert "mcp__sources__verify_words" in prompt
    assert "landing-overview.md" in prompt and "probe the landing" in prompt.lower()
    assert "python3 scripts/verification/vesum.py" not in prompt
    assert linear_pipeline._prompt_module_ref(prompt) == "a1/things-have-gender"
    for name in linear_pipeline.WRITER_ARTIFACTS:
        assert (upgrade_root / ORIGINAL / name).read_text() in prompt
    assert len(yaml.safe_load((output / "lessons.yaml").read_text())["lessons"]) == 3
    forbidden.assert_not_called()


def _gold_response(n: int) -> str:
    blocks = []
    for name in linear_pipeline.WRITER_ARTIFACTS:
        content = fixture_text("gold", f"{UPGRADED}/lesson-{n}/{name}")
        language = "markdown" if name == "module.md" else "json"
        if language == "json":
            content = json.dumps(yaml.safe_load(content), ensure_ascii=False)
        blocks.append(f"````{language} file={name}\n{content}\n````")
    return "\n".join(blocks)


@pytest.mark.parametrize("writer", ["gemini-tools", "codex-tools"])
@pytest.mark.parametrize("quality_passes", [True, False])
def test_upgrade_invokes_existing_writer_per_lesson_then_review_then_annotation(upgrade_root, monkeypatch, writer, quality_passes):
    from scripts.build import lesson_gates
    from scripts.pipeline import stress_annotator

    events = []
    def invoke(prompt, selected_writer, **kwargs):
        n = len([e for e in events if e.startswith("writer")]) + 1
        assert selected_writer == writer
        assert f"Your current published unit: lesson {n}" in prompt
        # #7994: the MCP runtime gate must not depend on prompt regexes.
        assert kwargs["module"] == "a1/things-have-gender"
        assert kwargs["sections"]
        assert kwargs["tool_trace_path"].name == "writer_tool_calls.json"
        events.append(f"writer{n}")
        return _gold_response(n)

    def review(**kwargs):
        events.append("coherence" if kwargs.get("content_override") else "review")
        assert "lesson_split" in kwargs["review_context"]
        return {"passed": True}

    monkeypatch.setattr(linear_pipeline, "invoke_writer", invoke)
    monkeypatch.setattr(v7_build, "_run_llm_qg", review)
    monkeypatch.setattr(v7_build, "_llm_qg_payload_passes", lambda result: result["passed"])
    monkeypatch.setattr(stress_annotator, "annotate_file", lambda path: events.append("stress") or 0)
    monkeypatch.setattr(lesson_gates, "run_lesson_gates", lambda *a, **kw: {"passed": quality_passes})
    monkeypatch.setattr(linear_pipeline, "run_mdx_render_gate", lambda mdx: {"passed": True})
    extra = ["--reviewer", "agy-tools"] if writer == "codex-tools" else []
    args = v7_build.parse_args(["a1", "things-have-gender", "--upgrade", "--writer", writer, *extra])
    assert v7_build._run(args) == (0 if quality_passes else 1)
    assert events[:10] == [
        "writer1", "review", "review",
        "writer2", "review", "review",
        "writer3", "review", "review",
        "coherence",
    ]
    assert events[10:] == ["stress"] * 12
    assert sorted(p.name for p in (upgrade_root / "site/src/content/docs/a1/things-have-gender").glob("*.mdx")) == ["1.mdx", "2.mdx", "3.mdx", "index.mdx"]
    for path in (upgrade_root / "site/src/content/docs/a1/things-have-gender").glob("*.mdx"):
        frontmatter = yaml.safe_load(path.read_text().split("---", 2)[1])
        assert frontmatter["draft"] is not quality_passes


@pytest.mark.parametrize("output", ["curriculum/l2-uk-en/a1-v1", "curriculum/l2-uk-en/a1-v1/things-have-gender", "curriculum/l2-uk-en/plans/a1", "curriculum"])
def test_upgrade_rejects_protected_output(upgrade_root, output):
    args = v7_build.parse_args(["a1", "things-have-gender", "--upgrade", "--dry-run", "--out", output])
    assert v7_build._run(args) == 1


def test_archive_level_resolves_all_pedagogical_configs():
    from scripts import config
    from scripts.audit.config import get_level_config
    from scripts.pipeline.config_tables import get_activity_config, get_track_skill

    assert base_level("a1-v1") == "a1"
    assert get_activity_config("a1-v1", 8) == get_activity_config("a1", 8)
    assert get_activity_config("a1-v1", 15) == get_activity_config("a1", 15)
    assert get_track_skill("a1-v1", 8) == get_track_skill("a1", 8)
    assert get_level_config("A1-V1", "grammar") == get_level_config("A1", "grammar")
    assert config.get_config("a1-v1") == config.get_config("a1")
    assert config.get_immersion_rule("a1-v1", 8) == config.get_immersion_rule("a1", 8)
    from scripts.manifest_utils import get_module_by_slug

    # With no published upgrades, slug-only lookup resolves the archived module.
    original = get_module_by_slug("things-have-gender")
    assert original.level == "a1-v1"
    assert original.local_num == 8


def test_reviewed_map_keeps_gold_declarations_and_rejects_changed_ownership(upgrade_root):
    from scripts.build.lesson_map import derive_lesson_map

    plan = yaml.safe_load((upgrade_root / "curriculum/l2-uk-en/plans/a1/things-have-gender.yaml").read_text())
    derived = derive_lesson_map(plan, (upgrade_root / ORIGINAL / "module.md").read_text(),
                                yaml.safe_load((upgrade_root / ORIGINAL / "activities.yaml").read_text()))
    path = upgrade_root / "reviewed.yaml"
    path.write_text(fixture_text("gold", f"{UPGRADED}/lessons.yaml"))
    declared = v7_build._upgrade_declared_map(derived, str(path))
    assert declared["lessons"][0]["unverified_stress"]
    assert declared["proper_names"]
    declared["provenance"][0]["lesson"] = 2
    path.write_text(yaml.safe_dump(declared, allow_unicode=True))
    with pytest.raises(linear_pipeline.LinearPipelineError, match="provenance"):
        v7_build._upgrade_declared_map(derived, str(path))


def test_same_family_upgrade_review_fails_before_writer(upgrade_root, monkeypatch):
    writer = Mock(side_effect=AssertionError("must not call writer"))
    monkeypatch.setattr(linear_pipeline, "invoke_writer", writer)
    args = v7_build.parse_args(["a1", "things-have-gender", "--upgrade", "--writer", "codex-tools", "--reviewer", "codex-tools"])
    assert v7_build._run(args) == 1
    writer.assert_not_called()


def test_upgrade_without_cf_clearance_blocks_writer(upgrade_root, monkeypatch):
    from scripts.build import cf_preflight

    writer = Mock(side_effect=AssertionError("must not call writer without CF"))
    monkeypatch.setattr(linear_pipeline, "invoke_writer", writer)
    (upgrade_root / "cf_clearance.json").unlink()
    monkeypatch.setattr(cf_preflight, "git_head", lambda _root: "b" * 40)
    args = v7_build.parse_args(["a1", "things-have-gender", "--upgrade", "--writer", "gemini-tools"])
    assert v7_build._run(args) == cf_preflight.CfPreflightError.exit_code
    writer.assert_not_called()


def test_upgrade_stale_cf_clearance_blocks_writer(upgrade_root, monkeypatch):
    from scripts.build import cf_preflight

    writer = Mock(side_effect=AssertionError("must not call writer with stale CF"))
    monkeypatch.setattr(linear_pipeline, "invoke_writer", writer)
    cf_preflight.write_clearance_file(upgrade_root / "cf_clearance.json", head="c" * 40)
    monkeypatch.setattr(cf_preflight, "git_head", lambda _root: "d" * 40)
    args = v7_build.parse_args(["a1", "things-have-gender", "--upgrade", "--writer", "gemini-tools"])
    assert v7_build._run(args) == cf_preflight.CfPreflightError.exit_code
    writer.assert_not_called()


def test_resume_binds_actual_writer_and_reviewer_identity(upgrade_root, monkeypatch):
    import re

    from scripts.build import lesson_gates
    from scripts.pipeline import stress_annotator

    calls, review_prompts = [], []
    def invoke(prompt, writer, **kwargs):
        calls.append(writer)
        return _gold_response(int(re.search(r"Your current published unit: lesson (\d+)", prompt)[1]))

    def review(**kwargs):
        review_prompts.append(kwargs["review_context"])
        return {"aggregate": {"verdict": "PASS"}}

    monkeypatch.setattr(linear_pipeline, "invoke_writer", invoke)
    monkeypatch.setattr(v7_build, "_run_llm_qg", review)
    monkeypatch.setattr(stress_annotator, "annotate_file", lambda path: 0)
    monkeypatch.setattr(lesson_gates, "run_lesson_gates", lambda *a, **kw: {"passed": True})
    monkeypatch.setattr(linear_pipeline, "run_mdx_render_gate", lambda mdx: {"passed": True})
    for writer, reviewer in (("gemini-tools", "codex-tools"), ("codex-tools", "gemini-tools"), ("codex-tools", "gemini-tools")):
        args = v7_build.parse_args(["a1", "things-have-gender", "--upgrade", "--writer", writer, "--reviewer", reviewer])
        assert v7_build._run(args) == 0
    assert calls == ["gemini-tools"] * 3 + ["codex-tools"] * 3
    assert any("self_reviewer" in prompt for prompt in review_prompts)
    assert any("independent_reviewer" in prompt for prompt in review_prompts)


def test_upgrade_cli_real_subprocess(tmp_path):
    import subprocess

    root = Path(__file__).resolve().parents[2]
    # Exercise the real CLI guard in an isolated primary checkout, including on CI.
    env = v7_build.reap_worktrees.sanitized_git_env()
    env.pop(v7_build.run_archive.ENV_KEY, None)
    subprocess.run(
        ["git", "init", str(tmp_path)],
        capture_output=True, text=True, check=True, timeout=30, env=env,
    )
    out = tmp_path / "upgrade-output"
    result = subprocess.run(
        [sys.executable, str(root / "scripts/build/v7_build.py"), "a1", "things-have-gender", "--upgrade", "--dry-run", "--out", str(out)],
        cwd=tmp_path, capture_output=True, text=True, check=False, timeout=60, env=env,
    )
    assert result.returncode == v7_build.PrimaryCheckoutBuildError.exit_code
    assert "Refusing to run v7_build in the primary checkout; pass --worktree" in result.stderr
    assert not out.exists()


def _seed_previous_edition(module_dir: Path) -> None:
    for n in (1, 2):
        lesson_dir = module_dir / f"lesson-{n}"
        lesson_dir.mkdir(parents=True, exist_ok=True)
        for name in linear_pipeline.WRITER_ARTIFACTS:
            (lesson_dir / name).write_text("old edition", encoding="utf-8")
        (lesson_dir / "writer_prompt.md").write_text("old prompt", encoding="utf-8")
        (lesson_dir / "writer_output.raw.md").write_text("bound response", encoding="utf-8")
    (module_dir / "lessons.yaml").write_text("lessons: []\n", encoding="utf-8")


def test_clear_previous_edition_removes_lesson_artifacts_and_keeps_lessons_yaml(tmp_path, monkeypatch):
    import hashlib

    monkeypatch.setattr(v7_build, "PROJECT_ROOT", tmp_path)
    module_dir = tmp_path / "curriculum/l2-uk-en/a1/special-signs"
    archive = tmp_path / "curriculum/l2-uk-en/a1-v1/special-signs"
    archive.mkdir(parents=True)
    (archive / "module.md").write_text("archive", encoding="utf-8")
    _seed_previous_edition(module_dir)
    # Lesson 2 was written by this edition: its prompt is bound to the writer receipt.
    bound = hashlib.sha256(b"old prompt").hexdigest()
    (module_dir / "lesson-2/upgrade_writer.json").write_text(json.dumps({"prompt_sha256": bound}), encoding="utf-8")

    removed = v7_build._clear_previous_edition(module_dir)

    for n in (1, 2):
        for name in linear_pipeline.WRITER_ARTIFACTS:
            assert not (module_dir / f"lesson-{n}" / name).exists()
        assert (module_dir / f"lesson-{n}/writer_output.raw.md").exists()
    assert not (module_dir / "lesson-1/writer_prompt.md").exists()  # stale: no receipt binds it
    assert (module_dir / "lesson-2/writer_prompt.md").exists()  # resumable
    assert (module_dir / "lessons.yaml").read_text(encoding="utf-8") == "lessons: []\n"
    assert (archive / "module.md").exists()
    assert len(removed) == 2 * len(linear_pipeline.WRITER_ARTIFACTS) + 1


def _primary_lesson(tmp_path: Path) -> Path:
    primary = tmp_path / "primary/curriculum/l2-uk-en/a1/special-signs/lesson-1"
    primary.mkdir(parents=True)
    for name in (*linear_pipeline.WRITER_ARTIFACTS, "writer_prompt.md"):
        (primary / name).write_text("primary checkout", encoding="utf-8")
    return primary


def _assert_primary_intact(primary: Path) -> None:
    for name in (*linear_pipeline.WRITER_ARTIFACTS, "writer_prompt.md"):
        assert (primary / name).read_text(encoding="utf-8") == "primary checkout"


def test_clear_previous_edition_refuses_a_symlinked_lesson_directory(tmp_path, monkeypatch):
    worktree = tmp_path / "worktree"
    monkeypatch.setattr(v7_build, "PROJECT_ROOT", worktree)
    primary = _primary_lesson(tmp_path)
    module_dir = worktree / "curriculum/l2-uk-en/a1/special-signs"
    module_dir.mkdir(parents=True)
    (module_dir / "lesson-1").symlink_to(primary, target_is_directory=True)
    # A real lesson sorted after the symlink: the refusal must come before any delete.
    real = module_dir / "lesson-2"
    real.mkdir()
    (real / "module.md").write_text("old edition", encoding="utf-8")

    with pytest.raises(linear_pipeline.LinearPipelineError, match="symlink"):
        v7_build._clear_previous_edition(module_dir)

    _assert_primary_intact(primary)
    assert (module_dir / "lesson-1").is_symlink()


def test_clear_previous_edition_refuses_targets_resolving_outside_the_worktree(tmp_path, monkeypatch):
    worktree = tmp_path / "worktree"
    monkeypatch.setattr(v7_build, "PROJECT_ROOT", worktree)
    primary = _primary_lesson(tmp_path)
    module_dir = worktree / "curriculum/l2-uk-en/a1/special-signs"
    _seed_previous_edition(module_dir)
    (module_dir / "lesson-2/module.md").unlink()
    (module_dir / "lesson-2/module.md").symlink_to(primary / "module.md")

    with pytest.raises(linear_pipeline.LinearPipelineError, match="outside the build worktree"):
        v7_build._clear_previous_edition(module_dir)

    _assert_primary_intact(primary)
    # Checked before the first delete: lesson-1 is untouched too.
    assert (module_dir / "lesson-1/module.md").read_text(encoding="utf-8") == "old edition"


def test_clear_previous_edition_removes_the_previous_landing_overview(tmp_path, monkeypatch):
    monkeypatch.setattr(v7_build, "PROJECT_ROOT", tmp_path)
    module_dir = tmp_path / "curriculum/l2-uk-en/a1/special-signs"
    _seed_previous_edition(module_dir)
    landing = module_dir / "landing-overview.md"
    landing.write_text("This module brings mastery of all 33 letters.\n", encoding="utf-8")

    removed = v7_build._clear_previous_edition(module_dir)

    assert landing in removed
    assert not landing.exists()
    assert (module_dir / "lessons.yaml").exists()


def test_clear_previous_edition_refuses_a_symlinked_landing_overview(tmp_path, monkeypatch):
    worktree = tmp_path / "worktree"
    monkeypatch.setattr(v7_build, "PROJECT_ROOT", worktree)
    primary_landing = tmp_path / "primary/curriculum/l2-uk-en/a1/special-signs/landing-overview.md"
    primary_landing.parent.mkdir(parents=True)
    primary_landing.write_text("primary checkout", encoding="utf-8")
    module_dir = worktree / "curriculum/l2-uk-en/a1/special-signs"
    _seed_previous_edition(module_dir)
    (module_dir / "landing-overview.md").symlink_to(primary_landing)

    with pytest.raises(linear_pipeline.LinearPipelineError, match="symlink"):
        v7_build._clear_previous_edition(module_dir)

    assert primary_landing.read_text(encoding="utf-8") == "primary checkout"
    assert (module_dir / "landing-overview.md").is_symlink()
    # Checked before the first delete: the lesson artifacts are untouched too.
    assert (module_dir / "lesson-1/module.md").read_text(encoding="utf-8") == "old edition"


def test_clear_previous_edition_refuses_a_module_outside_the_worktree(tmp_path, monkeypatch):
    monkeypatch.setattr(v7_build, "PROJECT_ROOT", tmp_path / "worktree")
    primary = _primary_lesson(tmp_path)

    with pytest.raises(linear_pipeline.LinearPipelineError, match="outside the build worktree"):
        v7_build._clear_previous_edition(primary.parent)

    _assert_primary_intact(primary)


def _run_upgrade_with_old_edition(upgrade_root, monkeypatch, *, alphabet: bool, dry_run: bool = False):
    from scripts.build import lesson_gates
    from scripts.pipeline import stress_annotator

    module_dir = upgrade_root / UPGRADED
    _seed_previous_edition(module_dir)
    seen: list[bool] = []

    def invoke(prompt, selected_writer, **kwargs):
        n = len(seen) + 1
        if n == 1:
            seen.append(all(
                (module_dir / f"lesson-{k}" / name).exists()
                for k in (1, 2) for name in linear_pipeline.WRITER_ARTIFACTS
            ))
        else:
            seen.append(False)
        return _gold_response(n)

    monkeypatch.setattr(v7_build, "is_alphabet_slug", lambda slug: alphabet)
    monkeypatch.setattr(linear_pipeline, "invoke_writer", invoke)
    monkeypatch.setattr(v7_build, "_run_llm_qg", lambda **kw: {"passed": True})
    monkeypatch.setattr(v7_build, "_llm_qg_payload_passes", lambda result: result["passed"])
    monkeypatch.setattr(stress_annotator, "annotate_file", lambda path: 0)
    monkeypatch.setattr(lesson_gates, "run_lesson_gates", lambda *a, **kw: {"passed": True})
    monkeypatch.setattr(linear_pipeline, "run_mdx_render_gate", lambda mdx: {"passed": True})
    argv = ["a1", "things-have-gender", "--upgrade", "--writer", "gemini-tools"]
    assert v7_build._run(v7_build.parse_args(argv + (["--dry-run"] if dry_run else []))) == 0
    return module_dir, seen


def test_alphabet_upgrade_starts_from_a_cleared_module(upgrade_root, monkeypatch):
    module_dir, seen = _run_upgrade_with_old_edition(upgrade_root, monkeypatch, alphabet=True)
    assert seen[0] is False  # the first writer call no longer sees the old edition
    assert (module_dir / "lessons.yaml").is_file()
    assert "old edition" not in (module_dir / "lesson-1/module.md").read_text(encoding="utf-8")


def test_other_upgrades_and_dry_runs_do_not_clear(upgrade_root, monkeypatch):
    _, seen = _run_upgrade_with_old_edition(upgrade_root, monkeypatch, alphabet=False)
    assert seen[0] is True


def test_alphabet_dry_run_does_not_clear(upgrade_root, monkeypatch):
    module_dir, seen = _run_upgrade_with_old_edition(upgrade_root, monkeypatch, alphabet=True, dry_run=True)
    assert seen == []
    assert (module_dir / "lesson-1/module.md").read_text(encoding="utf-8") == "old edition"


# ── #7994: lesson 1 lands landing-overview.md at the module root ─────────────

_LANDING_FENCE = (
    "````markdown file=landing-overview.md\n"
    "Nouns have gender: **стіл**, **кни́га**, **вікно́**.\n\nBy the end, you can:\n\n- name the gender of a noun.\n\n"
    "Keep the scope small.\n````"
)


def test_lesson_mode_parser_returns_the_optional_landing_overview():
    parsed = linear_pipeline.parse_writer_output(_gold_response(1) + "\n" + _LANDING_FENCE, lesson_mode=True)
    assert parsed["landing-overview.md"].startswith("Nouns have gender")
    assert "landing-overview.md" not in linear_pipeline.parse_writer_output(_gold_response(1), lesson_mode=True)
    with pytest.raises(linear_pipeline.LinearPipelineError):  # module builds have no landing artifact
        linear_pipeline.parse_writer_output(_gold_response(1) + "\n" + _LANDING_FENCE)


def _no_outcomes_source(tmp_path):
    source = tmp_path / "a1-v1"
    source.mkdir()
    (source / "module.md").write_text("# Title\n\nA short opening paragraph that carries no outcome list at all.\n\n## One\n")
    return source


def test_lesson_one_without_a_landing_fails_before_review(tmp_path):
    module = tmp_path / "a1"
    module.mkdir()
    with pytest.raises(linear_pipeline.LinearPipelineError, match=r"landing-overview\.md missing"):
        v7_build._land_overview_or_fail(module, _no_outcomes_source(tmp_path), {"level": "a1"}, {})


def test_lesson_one_landing_is_written_to_the_module_root(tmp_path):
    module = tmp_path / "a1"
    module.mkdir()
    parsed = linear_pipeline.parse_writer_output(_gold_response(1) + "\n" + _LANDING_FENCE, lesson_mode=True)
    v7_build._land_overview_or_fail(module, _no_outcomes_source(tmp_path), {"level": "a1"}, parsed)
    assert (module / "landing-overview.md").read_text().startswith("Nouns have gender")


_LIFT_MODULE = (
    "# Soft Sign\n\n"
    "You read the soft sign and the apostrophe in real Ukrainian words.\n\n"
    "By the end, you can:\n\n"
    "- recognize **ь** and apostrophe in common A1 words;\n"
    "- read **день** without adding an extra vowel.\n\n"
    "## First section\n\nBody that must not be lifted.\n"
)


def test_land_overview_lifts_outcomes_from_lesson_one_opening(tmp_path):
    from scripts.build.lesson_assembler import lift_landing_overview

    module = tmp_path / "a1"
    module.mkdir()
    module_md = _LIFT_MODULE
    parsed = {"module.md": module_md}
    before = parsed["module.md"]
    v7_build._land_overview_or_fail(module, _no_outcomes_source(tmp_path), {"level": "a1"}, parsed)
    landed = (module / "landing-overview.md").read_text(encoding="utf-8")
    assert landed.startswith("By the end, you can")
    assert "recognize **ь** and apostrophe" in landed
    assert "You read the soft sign" not in landed
    assert not landed.lstrip().startswith("# ")
    assert "First section" not in landed
    assert parsed["module.md"] == before
    assert lift_landing_overview(module_md) is not None
    assert "You read the soft sign" not in (lift_landing_overview(module_md) or "")


def test_land_overview_prefers_writer_file_over_lift(tmp_path):
    module = tmp_path / "a1"
    module.mkdir()
    writer = (
        "Nouns have gender: **стіл**, **кни́га**, **вікно́**.\n\n"
        "By the end, you can:\n\n- name the gender of a noun.\n\nKeep the scope small.\n"
    )
    parsed = {"module.md": _LIFT_MODULE, "landing-overview.md": writer}
    v7_build._land_overview_or_fail(module, _no_outcomes_source(tmp_path), {"level": "a1"}, parsed)
    assert (module / "landing-overview.md").read_text(encoding="utf-8") == writer


def test_land_overview_lift_refuses_line_break_or_banned_opening(tmp_path):
    module = tmp_path / "a1"
    module.mkdir()
    banned = (
        "# Soft Sign\n\n"
        "This module completes your mastery of all 33 letters today.\n\n"
        "By the end, you can:\n\n- read **день** with the soft sign.\n\n## Section\n"
    )
    # Banned phrase is only in the orientation prose; outcomes alone still land.
    v7_build._land_overview_or_fail(
        module, _no_outcomes_source(tmp_path), {"level": "a1"}, {"module.md": banned},
    )
    landed = (module / "landing-overview.md").read_text(encoding="utf-8")
    assert landed.startswith("By the end, you can")
    assert "mastery" not in landed
    assert "день" in landed


def test_land_overview_lift_refuses_banned_phrase_inside_outcomes(tmp_path):
    module = tmp_path / "a1"
    module.mkdir()
    banned = (
        "# Soft Sign\n\n"
        "A clean orientation paragraph about soft signs in Ukrainian words.\n\n"
        "By the end, you can:\n\n"
        "- complete your mastery of all 33 letters with **день**.\n\n## Section\n"
    )
    with pytest.raises(linear_pipeline.LinearPipelineError, match=r"landing-overview\.md missing"):
        v7_build._land_overview_or_fail(
            module, _no_outcomes_source(tmp_path), {"level": "a1"}, {"module.md": banned},
        )
    assert not (module / "landing-overview.md").is_file()


def test_lift_ignores_outcomes_after_first_h2():
    from scripts.build.lesson_assembler import lift_landing_overview

    text = (
        "# Soft Sign\n\n"
        "An opening paragraph without any outcomes list at all for the learner.\n\n"
        "## Later\n\nBy the end, you can:\n\n- do something.\n"
    )
    assert lift_landing_overview(text) is None


def test_lift_handles_real_230730_lesson1_dump():
    from scripts.build.lesson_assembler import lift_landing_overview

    path = Path(
        "/home/ops/learn-ukrainian/.worktrees/builds/a1-special-signs-20260919-230730"
        "/curriculum/l2-uk-en/a1/special-signs/lesson-1/module.md"
    )
    if not path.is_file():
        pytest.skip("230730 worktree absent")
    lifted = lift_landing_overview(path.read_text(encoding="utf-8"))
    assert lifted is not None
    assert lifted.startswith("By the end, you can")
    assert "Teacher Oksana" not in lifted
    assert "The signs are small on the page" not in lifted
    assert not lifted.lstrip().startswith("# ")
    assert "## М'яки́й знак" not in lifted
