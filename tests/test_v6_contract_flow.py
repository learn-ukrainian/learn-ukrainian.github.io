"""Tests for contract-first prompt plumbing, block rewrites, and escalation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import build.v6_build as v6_build


def _write_manifest(curriculum_root: Path, level: str, slug: str) -> None:
    curriculum_root.mkdir(parents=True, exist_ok=True)
    (curriculum_root / "curriculum.yaml").write_text(
        yaml.safe_dump({"levels": {level: {"modules": [slug]}}}, sort_keys=False),
        "utf-8",
    )


def _write_plan(curriculum_root: Path, level: str, slug: str) -> None:
    plan_path = curriculum_root / "plans" / level / f"{slug}.yaml"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        yaml.safe_dump(
            {
                "module": 1,
                "slug": slug,
                "level": level,
                "sequence": 1,
                "title": "Contract Flow",
                "phase": f"{level.upper()}.1",
                "word_target": 200,
                "content_outline": [
                    {
                        "section": "Intro",
                        "words": 100,
                        "points": ["звук і літера", "Привіт у classroom"],
                    },
                    {
                        "section": "Practice",
                        "words": 100,
                        "points": ["діалог з Учень"],
                    },
                ],
                "dialogue_situations": [
                    {
                        "setting": "classroom",
                        "speakers": ["Вчитель", "Учень"],
                        "motivation": "basic greeting",
                    }
                ],
                "vocabulary_hints": {"required": ["привіт", "добре"]},
                "activity_hints": [
                    {"id": "quiz-intro", "type": "quiz", "focus": "intro"},
                    {"id": "match-practice", "type": "match-up", "focus": "practice"},
                ],
                "grammar": ["звук і літера"],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        "utf-8",
    )


def test_step_write_emits_contract_and_excerpts(tmp_path: Path, monkeypatch) -> None:
    level = "a1"
    slug = "contract-flow"
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    (curriculum_root / level).mkdir(parents=True, exist_ok=True)
    _write_plan(curriculum_root, level, slug)

    packet_path = tmp_path / "packet.md"
    packet_path.write_text(
        "### Вікі: pedagogy/a1/contract-flow.md\n\n## Overview\n\nзвук і літера в classroom. Привіт і добре.\n",
        "utf-8",
    )

    phases_dir = tmp_path / "phases"
    phases_dir.mkdir(parents=True, exist_ok=True)
    (phases_dir / "v6-write.md").write_text(
        "Contract\n{CONTRACT_YAML}\n\nExcerpts\n{SECTION_WIKI_EXCERPTS}\n\n## Output Format\n",
        "utf-8",
    )

    captured: dict[str, str] = {}

    def fake_dispatch(prompt: str, *args, **kwargs):
        captured["prompt"] = prompt
        return True, "## Intro\nпривіт добре classroom звук літера\n\n## Practice\nУчень і Вчитель.\n"

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(v6_build, "PHASES_DIR", phases_dir)
    monkeypatch.setattr(v6_build, "_resolve_persona", lambda *args, **kwargs: ("", ""))
    monkeypatch.setattr("build.dispatch.dispatch_agent", fake_dispatch)

    output = v6_build.step_write(level, 1, slug, packet_path, writer="gemini")
    assert output is not None
    assert (curriculum_root / level / "orchestration" / slug / "contract.yaml").exists()
    assert (curriculum_root / level / "orchestration" / slug / "wiki-excerpts.yaml").exists()
    assert "[BEGIN MODULE CONTRACT LITERAL" in captured["prompt"]
    assert "[BEGIN SECTION WIKI EXCERPTS LITERAL" in captured["prompt"]


def test_apply_review_rewrite_blocks_rewrites_only_target_section(tmp_path: Path, monkeypatch) -> None:
    level = "a1"
    slug = "rewrite-flow"
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    (curriculum_root / level / "orchestration" / slug).mkdir(parents=True, exist_ok=True)
    _write_plan(curriculum_root, level, slug)
    content_path = curriculum_root / level / f"{slug}.md"
    content_path.parent.mkdir(parents=True, exist_ok=True)
    content_path.write_text(
        "## Intro\nOld intro.\n\n## Practice\nOld practice.\n",
        "utf-8",
    )
    (curriculum_root / level / "orchestration" / slug / "skeleton.md").write_text(
        "## Intro (~100 words)\n- P1 (~100 words): intro\n\n## Practice (~100 words)\n- P1 (~100 words): practice\n",
        "utf-8",
    )
    packet_path = tmp_path / "packet.md"
    packet_path.write_text(
        "### Вікі: pedagogy/a1/rewrite-flow.md\n\n## Overview\n\nзвук і літера classroom Вчитель Учень привіт добре.\n",
        "utf-8",
    )

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    v6_build._ensure_contract_artifacts(level, 1, slug, packet_path, log_creation=False)
    monkeypatch.setattr(
        v6_build,
        "_dispatch_rewrite_prompt",
        lambda *args, **kwargs: (True, "## Practice\nRewritten practice with Вчитель Учень привіт добре.\n"),
    )

    ok, count = v6_build._apply_review_rewrite_blocks(
        '<rewrite-block section="Practice">Fix the dialogue.</rewrite-block>',
        content_path,
        level=level,
        module_num=1,
        slug=slug,
        writer="gemini",
    )

    updated = content_path.read_text("utf-8")
    assert ok is True
    assert count == 1
    assert "Old intro." in updated
    assert "Rewritten practice" in updated
    assert "Old practice." not in updated


def test_main_marks_needs_human_review_after_two_rounds(tmp_path: Path, monkeypatch) -> None:
    level = "a1"
    slug = "needs-human"
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    _write_manifest(curriculum_root, level, slug)
    _write_plan(curriculum_root, level, slug)
    (curriculum_root / level).mkdir(parents=True, exist_ok=True)
    (curriculum_root / level / f"{slug}.md").write_text(
        "## Intro\nпривіт добре classroom\n\n## Practice\nУчень.\n",
        "utf-8",
    )
    orch_dir = curriculum_root / level / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)
    (orch_dir / "contract.yaml").write_text(
        yaml.safe_dump(
            {
                "teaching_beats": {"section_order": ["Intro", "Practice"]},
                "section_word_budgets": {"Intro": {"min": 1, "max": 200}, "Practice": {"min": 1, "max": 200}},
                "vocab_grammar_targets": {"must_introduce": ["привіт", "добре"]},
                "activity_obligations": [],
                "dialogue_acts": [],
                "factual_anchors": [],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        "utf-8",
    )
    (orch_dir / "wiki-excerpts.yaml").write_text("sections: {}\nfactual_anchors: []\n", "utf-8")

    review_calls = {"count": 0}
    reviews = iter(
        [
            (False, 8.4, "## Verdict: REVISE\n<fixes></fixes>\n"),
            (False, 8.5, "## Verdict: REVISE\n<fixes></fixes>\n"),
            (False, 8.6, "## Verdict: REVISE\n<fixes></fixes>\n"),
        ]
    )

    def fake_review(*args, **kwargs):
        review_calls["count"] += 1
        return next(reviews)

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "acquire", lambda self: True)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "release", lambda self: None)
    monkeypatch.setattr(v6_build, "_run_pre_build_gate", lambda *args, **kwargs: True)
    monkeypatch.setattr(v6_build, "step_review", fake_review)
    monkeypatch.setattr(v6_build, "_apply_review_fixes", lambda *args, **kwargs: (False, 0))
    monkeypatch.setattr(v6_build, "_apply_review_rewrite_blocks", lambda *args, **kwargs: (False, 0))
    monkeypatch.setattr(v6_build, "step_verify", lambda *args, **kwargs: "complete")
    monkeypatch.setattr(sys, "argv", ["v6_build.py", level, "1", "--step", "review", "--writer", "gemini"])

    result = v6_build.main()

    state = json.loads((orch_dir / "state.json").read_text("utf-8"))
    needs_human_review = yaml.safe_load((orch_dir / "needs-human-review.yaml").read_text("utf-8"))
    assert result is False
    assert review_calls["count"] == 3
    assert state["needs_human_review"]["status"] is True
    assert needs_human_review["review_rounds"] == 3
    assert (orch_dir / "needs-human-review.yaml").exists()
