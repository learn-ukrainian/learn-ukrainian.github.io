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


@pytest.fixture
def upgrade_root(tmp_path, monkeypatch):
    from scripts.generate_mdx import atlas_links

    atlas = tmp_path / "atlas.json"
    atlas.write_text('{"entries": []}')
    monkeypatch.setattr(atlas_links, "_DEFAULT_MANIFEST", atlas)
    extract_upgrade_fixtures(tmp_path, "baseline")
    monkeypatch.setattr(v7_build, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(linear_pipeline, "plan_path_for", lambda level, slug: tmp_path / "curriculum/l2-uk-en/plans/a1" / f"{slug}.yaml")
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
    assert "side-by-side English support" in prompt
    assert "file=activities.yaml" in prompt
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
