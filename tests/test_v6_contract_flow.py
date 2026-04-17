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


def test_apply_contract_word_budget_rewrites_targets_only_budget_blockers(
    tmp_path: Path, monkeypatch
) -> None:
    level = "a1"
    slug = "word-budget-autoheal"
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    content_path = curriculum_root / level / f"{slug}.md"
    content_path.parent.mkdir(parents=True, exist_ok=True)
    content_path.write_text(
        "## Intro\nОдне коротке речення.\n\n"
        "## Practice\nТут уже достатньо слів для перевірки.\n",
        "utf-8",
    )

    calls: list[tuple[str, str]] = []

    def fake_rewrite(*args, **kwargs):
        calls.append((kwargs["section_name"], kwargs["directive"]))
        return True

    monkeypatch.setattr(v6_build, "_rewrite_block_section", fake_rewrite)

    ok, count = v6_build._apply_contract_word_budget_rewrites(
        content_path,
        level=level,
        module_num=1,
        slug=slug,
        writer="gemini",
        contract={
            "section_word_budgets": {
                "Intro": {"target": 100, "min": 90, "max": 110},
                "Practice": {"target": 100, "min": 90, "max": 110},
            }
        },
        contract_violations=[
            {
                "type": "WORD_BUDGET",
                "severity": "ERROR",
                "section": "Intro",
                "message": "Section 'Intro' has 10 words; contract minimum is 90",
            }
        ],
    )

    assert ok is True
    assert count == 1
    assert calls[0][0] == "Intro"
    assert "Issue type: WORD_BUDGET" in calls[0][1]
    assert "Contract minimum: 90" in calls[0][1]
    assert "Contract target: 100" in calls[0][1]
    assert "Add at least" in calls[0][1]


def test_apply_contract_word_budget_rewrites_skips_mixed_violation_sets(
    tmp_path: Path, monkeypatch
) -> None:
    content_path = tmp_path / "module.md"
    content_path.write_text("## Intro\nКороткий текст.\n", "utf-8")

    monkeypatch.setattr(v6_build, "_rewrite_block_section", lambda *args, **kwargs: True)

    ok, count = v6_build._apply_contract_word_budget_rewrites(
        content_path,
        level="a1",
        module_num=1,
        slug="mixed-violations",
        writer="gemini",
        contract={"section_word_budgets": {"Intro": {"target": 100, "min": 90, "max": 110}}},
        contract_violations=[
            {
                "type": "WORD_BUDGET",
                "severity": "ERROR",
                "section": "Intro",
                "message": "Section 'Intro' has 10 words; contract minimum is 90",
            },
            {
                "type": "ACTIVITY_MISSING",
                "severity": "ERROR",
                "section": "Intro",
                "message": "Missing required activity marker.",
            },
        ],
    )

    assert ok is False
    assert count == 0


def test_rewrite_block_section_emits_slim_prompt_manifest(tmp_path: Path, monkeypatch) -> None:
    level = "a1"
    slug = "rewrite-prompt-audit"
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    orch_dir = curriculum_root / level / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)
    _write_plan(curriculum_root, level, slug)
    content_path = curriculum_root / level / f"{slug}.md"
    content_path.parent.mkdir(parents=True, exist_ok=True)
    content_path.write_text(
        "## Intro\nOld intro.\n\n## Practice\nOld practice.\n",
        "utf-8",
    )
    packet_path = tmp_path / "packet.md"
    packet_path.write_text(
        "### Вікі: pedagogy/a1/rewrite-prompt-audit.md\n\n## Practice\n\nДобре. Учень читає.\n",
        "utf-8",
    )

    captured: dict[str, str] = {}

    def fake_dispatch(prompt: str, writer: str, phase: str, orch_dir_arg: Path):
        captured["prompt"] = prompt
        return True, "## Practice\nRewritten practice with Учень.\n"

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    v6_build._ensure_contract_artifacts(level, 1, slug, packet_path, log_creation=False)
    monkeypatch.setattr(v6_build, "_dispatch_rewrite_prompt", fake_dispatch)

    ok = v6_build._rewrite_block_section(
        content_path,
        level=level,
        module_num=1,
        slug=slug,
        writer="gemini",
        section_name="Practice",
        directive="Fix the dialogue rhythm.",
    )

    manifest_path = orch_dir / "rewrite-block-02-prompt-manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text("utf-8"))

    assert ok is True
    assert "## Rewrite Guardrails" in captured["prompt"]
    assert "## Section-Mapped Wiki Excerpts" in captured["prompt"]
    assert "## Current Section To Replace" in captured["prompt"]
    assert "## Shared Module Contract" not in captured["prompt"]
    assert "## Previous Sections For Continuity" not in captured["prompt"]
    assert "## Skeleton For This Section" not in captured["prompt"]
    assert manifest["audit"]["passed"] is True
    assert manifest["components"] == [
        "rewrite_directive",
        "rewrite_guardrails",
        "section_mapped_wiki_excerpts",
        "current_section",
    ]
    assert manifest["flags"]["includes_shared_contract"] is False
    assert manifest["flags"]["includes_previous_sections"] is False
    assert manifest["flags"]["includes_skeleton"] is False


def test_rewrite_block_prompt_audit_rejects_forbidden_auxiliary_literals(
    tmp_path: Path, monkeypatch
) -> None:
    level = "a1"
    slug = "rewrite-prompt-poison"
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    orch_dir = curriculum_root / level / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)
    content_path = curriculum_root / level / f"{slug}.md"
    content_path.parent.mkdir(parents=True, exist_ok=True)
    content_path.write_text(
        "## Practice\nOld practice.\n",
        "utf-8",
    )

    dispatch_called = {"value": False}

    def fake_dispatch(*args, **kwargs):
        dispatch_called["value"] = True
        return True, "## Practice\nRewritten practice.\n"

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(v6_build, "_dispatch_rewrite_prompt", fake_dispatch)
    monkeypatch.setattr(
        v6_build,
        "_ensure_contract_artifacts",
        lambda *args, **kwargs: (
            {"activity_obligations": []},
            {
                "sections": {
                    "Practice": [
                        {"source": "plan", "excerpt": "Що ви можете порекомендувати?"},
                    ]
                },
                "factual_anchors": [],
            },
        ),
    )

    ok = v6_build._rewrite_block_section(
        content_path,
        level=level,
        module_num=1,
        slug=slug,
        writer="gemini",
        section_name="Practice",
        directive='- Evidence: "Що ви можете порекомендувати?"\n- Required fix: Use a simpler service question.',
    )

    manifest_path = orch_dir / "rewrite-block-01-prompt-manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text("utf-8"))

    assert ok is False
    assert dispatch_called["value"] is False
    assert manifest["audit"]["passed"] is False
    assert "Що ви можете порекомендувати?" in manifest["audit"]["derived_auxiliary_forbidden_literals"]
    assert "Що ви можете порекомендувати?" in manifest["audit"]["auxiliary_forbidden_literals"]
    assert any("forbidden literal" in failure for failure in manifest["audit"]["failures"])


def test_rewrite_block_section_allows_shorter_summary_meta_cleanup(
    tmp_path: Path, monkeypatch
) -> None:
    level = "a1"
    slug = "rewrite-summary-meta"
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    orch_dir = curriculum_root / level / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)
    content_path = curriculum_root / level / f"{slug}.md"
    content_path.parent.mkdir(parents=True, exist_ok=True)
    original_summary = " ".join(["пояснення"] * 320)
    content_path.write_text(
        f"## Підсумок — Summary\n{original_summary}\n",
        "utf-8",
    )

    rewritten_summary = " ".join(["речення"] * 134)

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(
        v6_build,
        "_ensure_contract_artifacts",
        lambda *args, **kwargs: (
            {"activity_obligations": []},
            {"sections": {"Підсумок — Summary": []}, "factual_anchors": []},
        ),
    )
    monkeypatch.setattr(
        v6_build,
        "_dispatch_rewrite_prompt",
        lambda *args, **kwargs: (
            True,
            f"## Підсумок — Summary\n{rewritten_summary}\n",
        ),
    )

    ok = v6_build._rewrite_block_section(
        content_path,
        level=level,
        module_num=18,
        slug=slug,
        writer="gemini",
        section_name="Підсумок — Summary",
        directive=(
            "Style review blocking issues to fix in this section:\n"
            "- Issue type: META_PEDAGOGICAL_NARRATION\n"
            "- Required fix: Remove meta-commentary and present the examples directly."
        ),
    )

    assert ok is True
    updated = content_path.read_text("utf-8")
    assert rewritten_summary in updated
    assert original_summary not in updated


def test_rewrite_block_section_allows_shorter_meta_narration_cleanup_outside_summary(
    tmp_path: Path, monkeypatch
) -> None:
    level = "a1"
    slug = "rewrite-meta-shortening"
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    orch_dir = curriculum_root / level / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)
    _write_plan(curriculum_root, level, slug)
    content_path = curriculum_root / level / f"{slug}.md"
    content_path.parent.mkdir(parents=True, exist_ok=True)
    content_path.write_text(
        "## Intro\nOld intro.\n\n"
        "## Practice\n" + ("Речення для пояснення. " * 70) + "\nMeta line.\n",
        "utf-8",
    )
    packet_path = tmp_path / "packet.md"
    packet_path.write_text(
        "### Вікі: pedagogy/a1/rewrite-meta-shortening.md\n\n## Practice\n\nУчень читає.\n",
        "utf-8",
    )

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    v6_build._ensure_contract_artifacts(level, 1, slug, packet_path, log_creation=False)
    monkeypatch.setattr(
        v6_build,
        "_dispatch_rewrite_prompt",
        lambda *args, **kwargs: (
            True,
            "## Practice\n" + ("Коротше, але зміст лишається. " * 28) + "\n",
        ),
    )

    ok = v6_build._rewrite_block_section(
        content_path,
        level=level,
        module_num=1,
        slug=slug,
        writer="gemini",
        section_name="Practice",
        directive="- Issue type: META_PEDAGOGICAL_NARRATION\n- Required fix: Remove the after-dialogue narration.",
    )

    assert ok is True
    updated = content_path.read_text("utf-8")
    assert "Коротше, але зміст лишається." in updated


def test_rewrite_block_section_allows_shorter_summary_register_cleanup(
    tmp_path: Path, monkeypatch
) -> None:
    level = "a1"
    slug = "rewrite-summary-register"
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    orch_dir = curriculum_root / level / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)
    content_path = curriculum_root / level / f"{slug}.md"
    content_path.parent.mkdir(parents=True, exist_ok=True)
    original_summary = " ".join(["запам'ятайте"] * 320)
    content_path.write_text(
        f"## Підсумок — Summary\n{original_summary}\n",
        "utf-8",
    )

    rewritten_summary = " ".join(["сьогодні", "я", "хочу", "каву"] * 28)

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(
        v6_build,
        "_ensure_contract_artifacts",
        lambda *args, **kwargs: (
            {"activity_obligations": []},
            {"sections": {"Підсумок — Summary": []}, "factual_anchors": []},
        ),
    )
    monkeypatch.setattr(
        v6_build,
        "_dispatch_rewrite_prompt",
        lambda *args, **kwargs: (
            True,
            f"## Підсумок — Summary\n{rewritten_summary}\n",
        ),
    )

    ok = v6_build._rewrite_block_section(
        content_path,
        level=level,
        module_num=18,
        slug=slug,
        writer="gemini",
        section_name="Підсумок — Summary",
        directive=(
            "Style review blocking issues to fix in this section:\n"
            "- Issue type: REGISTER_MISMATCH\n"
            "- Issue type: EXPLANATION_TONE_MISMATCH\n"
            "- Required fix: Replace workbook commands and abstract recap with a short plain A1 recap."
        ),
    )

    assert ok is True
    updated = content_path.read_text("utf-8")
    assert rewritten_summary in updated
    assert original_summary not in updated
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


def test_main_clears_stale_needs_human_review_after_review_pass(
    tmp_path: Path, monkeypatch
) -> None:
    level = "a1"
    slug = "review-clears-needs-human"
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
    (orch_dir / "needs-human-review.yaml").write_text("stale: true\n", "utf-8")
    state_path = orch_dir / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "mode": "v6",
                "track": level,
                "slug": slug,
                "phases": {},
                "needs_human_review": {"status": True, "reason": "stale"},
            }
        ),
        "utf-8",
    )

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "acquire", lambda self: True)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "release", lambda self: None)
    monkeypatch.setattr(v6_build, "_run_pre_build_gate", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        v6_build,
        "step_review",
        lambda *args, **kwargs: (
            True,
            9.2,
            "## Verdict: PASS\n| 1. Plan adherence | 9/10 | ok |\n",
        ),
    )
    monkeypatch.setattr(
        v6_build,
        "_run_style_review_heal_loop",
        lambda *args, **kwargs: v6_build.StyleReviewLoopRunResult(
            outcome="pass",
            rounds=(
                v6_build.StyleReviewRoundState(
                    round_num=1,
                    passed=True,
                    score=9.3,
                    review_text="phase: review-style\nverdict: PASS\n",
                    blocking_issues=(),
                ),
            ),
        ),
    )
    monkeypatch.setattr(sys, "argv", ["v6_build.py", level, "1", "--step", "review", "--writer", "gemini"])

    result = v6_build.main()

    state = json.loads(state_path.read_text("utf-8"))
    assert result is True
    assert "needs_human_review" not in state
    assert (orch_dir / "needs-human-review.yaml").exists() is False


def test_run_review_heal_loop_triggers_word_budget_autoheal(tmp_path: Path, monkeypatch) -> None:
    level = "a1"
    slug = "review-word-budget"
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    content_path = curriculum_root / level / f"{slug}.md"
    content_path.parent.mkdir(parents=True, exist_ok=True)
    content_path.write_text(
        "## Intro\nКороткий текст.\n\n## Practice\nДостатньо слів для другої секції.\n",
        "utf-8",
    )
    packet_path = curriculum_root / level / "research" / f"{slug}-knowledge-packet.md"
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_text("packet", "utf-8")

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    review_rounds = iter(
        [
            (False, 9.1, "## Verdict: REVISE\n<fixes></fixes>\n"),
            (True, 9.3, "## Verdict: PASS\n"),
        ]
    )

    monkeypatch.setattr(v6_build, "step_review", lambda *args, **kwargs: next(review_rounds))
    monkeypatch.setattr(v6_build, "_apply_review_fixes", lambda *args, **kwargs: (False, 0))
    monkeypatch.setattr(v6_build, "_apply_review_rewrite_blocks", lambda *args, **kwargs: (False, 0))

    verify_calls = {"count": 0}

    def fake_verify(*args, **kwargs):
        verify_calls["count"] += 1
        return "complete"

    monkeypatch.setattr(v6_build, "step_verify", fake_verify)
    monkeypatch.setattr(
        v6_build,
        "_ensure_contract_artifacts",
        lambda *args, **kwargs: (
            {
                "section_word_budgets": {
                    "Intro": {"target": 100, "min": 90, "max": 110},
                    "Practice": {"target": 100, "min": 90, "max": 110},
                }
            },
            {},
        ),
    )

    review_passes = iter(
        [
            [
                {
                    "type": "WORD_BUDGET",
                    "severity": "ERROR",
                    "section": "Intro",
                    "message": "Section 'Intro' has 10 words; contract minimum is 90",
                }
            ],
            [],
            [],
        ]
    )

    monkeypatch.setattr(
        "audit.checks.contract_compliance.check_contract_compliance",
        lambda *args, **kwargs: next(review_passes),
    )

    autoheal_calls: list[dict] = []

    def fake_word_budget_autoheal(*args, **kwargs):
        autoheal_calls.append(kwargs)
        return (len(autoheal_calls) == 1), (1 if len(autoheal_calls) == 1 else 0)

    monkeypatch.setattr(v6_build, "_apply_contract_word_budget_rewrites", fake_word_budget_autoheal)
    monkeypatch.setattr(v6_build, "_save_contract_compliance", lambda *args, **kwargs: None)

    result = v6_build._run_review_heal_loop(
        content_path,
        level=level,
        module_num=1,
        slug=slug,
        writer="gemini",
        reviewer_override="codex-tools",
        max_rounds=2,
    )

    assert result.outcome == "pass"
    assert len(autoheal_calls) >= 1
    assert autoheal_calls[0]["writer"] == "gemini"
    assert autoheal_calls[0]["contract_violations"][0]["type"] == "WORD_BUDGET"
    assert verify_calls["count"] == 1


def test_dispatch_rewrite_prompt_uses_shorter_gemini_budget(tmp_path: Path, monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_dispatch(prompt: str, **kwargs):
        captured["prompt"] = prompt
        captured.update(kwargs)
        return True, "## Intro\nRewritten.\n"

    monkeypatch.setattr("build.dispatch.dispatch_agent", fake_dispatch)

    ok, raw = v6_build._dispatch_rewrite_prompt(
        "rewrite prompt",
        "gemini-tools",
        "rewrite-block-01",
        tmp_path,
    )

    assert ok is True
    assert raw.startswith("## Intro")
    assert captured["agent"] == "gemini"
    assert captured["timeout"] == v6_build.REWRITE_BLOCK_TIMEOUT_S
    assert captured["cascade_per_call_max_s"] == v6_build.REWRITE_BLOCK_GEMINI_CALL_CAP_S
    assert "mcp_tools" not in captured


def test_dispatch_rewrite_prompt_falls_back_to_codex_after_gemini_failure(
    tmp_path: Path, monkeypatch
) -> None:
    calls: list[dict[str, object]] = []

    def fake_dispatch(prompt: str, **kwargs):
        calls.append({"prompt": prompt, **kwargs})
        if kwargs["agent"] == "gemini":
            return False, ""
        return True, "## Intro\nRewritten by codex.\n"

    monkeypatch.setattr("build.dispatch.dispatch_agent", fake_dispatch)

    ok, raw = v6_build._dispatch_rewrite_prompt(
        "rewrite prompt",
        "gemini-tools",
        "rewrite-block-01",
        tmp_path,
    )

    assert ok is True
    assert raw.startswith("## Intro")
    assert [call["agent"] for call in calls] == ["gemini", "codex"]
    assert calls[0]["cascade_per_call_max_s"] == v6_build.REWRITE_BLOCK_GEMINI_CALL_CAP_S
    assert "cascade_per_call_max_s" not in calls[1]


def test_main_continues_after_style_advisory_pass(tmp_path: Path, monkeypatch) -> None:
    level = "a1"
    slug = "style-advisory"
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

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "acquire", lambda self: True)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "release", lambda self: None)
    monkeypatch.setattr(v6_build, "_run_pre_build_gate", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        v6_build,
        "_run_style_review_heal_loop",
        lambda *args, **kwargs: v6_build.StyleReviewLoopRunResult(
            outcome="pass",
            rounds=(
                v6_build.StyleReviewRoundState(
                    round_num=1,
                    passed=False,
                    score=8.4,
                    review_text="phase: review-style\nverdict: REVISE\n",
                    blocking_issues=({"type": "META_PEDAGOGICAL_NARRATION"},),
                ),
            ),
        ),
    )
    monkeypatch.setattr(sys, "argv", ["v6_build.py", level, "1", "--step", "review-style", "--writer", "gemini"])

    result = v6_build.main()

    state = json.loads((orch_dir / "state.json").read_text("utf-8"))
    assert result is True
    # Should NOT have needs_human_review because it's advisory pass
    assert "needs_human_review" not in state


def test_main_clears_stale_needs_human_review_after_style_pass(
    tmp_path: Path, monkeypatch
) -> None:
    level = "a1"
    slug = "style-clears-needs-human"
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
    (orch_dir / "needs-human-review.yaml").write_text("stale: true\n", "utf-8")
    state_path = orch_dir / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "mode": "v6",
                "track": level,
                "slug": slug,
                "phases": {},
                "needs_human_review": {"status": True, "reason": "stale"},
            }
        ),
        "utf-8",
    )

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "acquire", lambda self: True)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "release", lambda self: None)
    monkeypatch.setattr(v6_build, "_run_pre_build_gate", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        v6_build,
        "_run_style_review_heal_loop",
        lambda *args, **kwargs: v6_build.StyleReviewLoopRunResult(
            outcome="pass",
            rounds=(
                v6_build.StyleReviewRoundState(
                    round_num=1,
                    passed=True,
                    score=9.2,
                    review_text="phase: review-style\nverdict: PASS\n",
                    blocking_issues=(),
                ),
            ),
        ),
    )
    monkeypatch.setattr(sys, "argv", ["v6_build.py", level, "1", "--step", "review-style", "--writer", "gemini"])

    result = v6_build.main()

    state = json.loads(state_path.read_text("utf-8"))
    assert result is True
    assert "needs_human_review" not in state
    assert (orch_dir / "needs-human-review.yaml").exists() is False


def test_run_style_review_heal_loop_treats_malformed_yaml_as_error(
    tmp_path: Path, monkeypatch
) -> None:
    level = "a1"
    slug = "style-malformed"
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    _write_manifest(curriculum_root, level, slug)
    _write_plan(curriculum_root, level, slug)
    content_path = curriculum_root / level / f"{slug}.md"
    content_path.parent.mkdir(parents=True, exist_ok=True)
    content_path.write_text(
        "## Intro\nпривіт добре classroom\n\n## Practice\nУчень.\n",
        "utf-8",
    )

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(
        v6_build,
        "step_review_style",
        lambda *args, **kwargs: (False, -1.0, "scores: ["),
    )

    result = v6_build._run_style_review_heal_loop(
        content_path,
        level=level,
        module_num=1,
        slug=slug,
        writer="gemini",
        reviewer_override=None,
    )

    assert result.outcome == "error"
    assert result.rounds == ()


def test_normalize_activity_markers_to_contract_reorders_type_only_slots() -> None:
    content = """## Intro
<!-- INJECT_ACTIVITY: fill-in-khotity-conjugation -->
<!-- INJECT_ACTIVITY: quiz-regular-irregular -->
<!-- INJECT_ACTIVITY: quiz-choose-modal -->
<!-- INJECT_ACTIVITY: fill-in-modal-story -->
"""
    contract = {
        "activity_obligations": [
            {"type": "fill-in"},
            {"type": "quiz"},
            {"type": "fill-in"},
            {"type": "quiz"},
        ]
    }
    normalized = v6_build._normalize_activity_markers_to_contract(content, contract)
    assert "<!-- INJECT_ACTIVITY: fill-in-khotity-conjugation -->" in normalized
    assert "<!-- INJECT_ACTIVITY: quiz-regular-irregular -->" in normalized
    assert "<!-- INJECT_ACTIVITY: fill-in-modal-story -->" in normalized
    assert "<!-- INJECT_ACTIVITY: quiz-choose-modal -->" in normalized
    assert normalized.index("fill-in-modal-story") < normalized.index("quiz-choose-modal")
