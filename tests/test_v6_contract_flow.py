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


_HEAL_LOOP_DIMENSIONS = (
    "Plan adherence",
    "Linguistic accuracy",
    "Pedagogical quality",
    "Vocabulary coverage",
    "Exercise quality",
    "Engagement & tone",
    "Structural integrity",
    "Cultural accuracy",
    "Dialogue & conversation quality",
)


def _fake_review_text(per_dim_score: int, verdict: str, fixes_body: str = "") -> str:
    """Build a minimal-but-realistic review markdown body.

    Bug #1316 Bug B confirmation-review validity guard re-parses the text
    with ``_parse_review_result`` and requires ``raw_scores`` to be
    non-empty before accepting the confirmation — which means the text
    must contain a scored dimension table, not just a ``Verdict:`` line.
    This helper produces such a table so the fake review survives the
    guard instead of getting rejected as malformed.

    The outer ``(passed, score, text)`` returned by the step_review mock
    is independently hardcoded by each test; the table here exists only
    so the guard recognizes the text as a real review.
    """
    lines = ["## Scores", "| Dimension | Score | Evidence |", "|-----------|-------|----------|"]
    for i, dim in enumerate(_HEAL_LOOP_DIMENSIONS, 1):
        lines.append(f"| {i}. {dim} | {per_dim_score}/10 | ok |")
    if fixes_body:
        lines.append(f"\n<fixes>{fixes_body}</fixes>")
    lines.append(f"\n## Verdict: {verdict}\n")
    return "\n".join(lines)


def _setup_heal_loop_fixture(tmp_path: Path, monkeypatch, slug: str) -> Path:
    """Shared scaffold for the Bug B (confirmation-review) tests.

    Creates a minimal tmp curriculum tree, stubs the contract/verify/save
    calls that aren't under test, and returns the content path. Each test
    is responsible for installing its own ``step_review`` and fix-applier
    stubs to drive the specific scenario it wants to exercise.
    """
    level = "a1"
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    content_path = curriculum_root / level / f"{slug}.md"
    content_path.parent.mkdir(parents=True, exist_ok=True)
    content_path.write_text("## Intro\nStart.\n", "utf-8")
    packet_path = curriculum_root / level / "research" / f"{slug}-knowledge-packet.md"
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_text("packet", "utf-8")

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(v6_build, "step_verify", lambda *args, **kwargs: "complete")
    monkeypatch.setattr(
        v6_build,
        "_ensure_contract_artifacts",
        lambda *args, **kwargs: ({"section_word_budgets": {}}, {}),
    )
    monkeypatch.setattr(
        "audit.checks.contract_compliance.check_contract_compliance",
        lambda *args, **kwargs: [],
    )
    monkeypatch.setattr(
        v6_build,
        "_apply_contract_word_budget_rewrites",
        lambda *args, **kwargs: (False, 0),
    )
    monkeypatch.setattr(v6_build, "_save_contract_compliance", lambda *args, **kwargs: None)
    return content_path


def test_review_loop_runs_confirmation_review_when_mutations_happened(
    tmp_path: Path, monkeypatch
) -> None:
    """Bug #1316 Bug B — the stale-score plateau case.

    When the loop reaches max_rounds with a pre-fix REVISE score but the
    round applied fixes/rewrites that actually resolved the reviewer's
    complaints, a confirmation review on the now-current content should
    run and convert the plateau into a pass. This is the A1/M01 case.
    """
    content_path = _setup_heal_loop_fixture(tmp_path, monkeypatch, slug="conf-pass")

    review_calls: list[str] = []
    review_rounds = iter(
        [
            # R1: reviewer sees un-repaired content, says REVISE at 9.2 with a fix.
            (False, 9.2, "## Verdict: REVISE\n<fixes>apply me</fixes>\n"),
            # R2: reviewer still sees stale issue (we simulate a hardcoded REVISE),
            # but a fix was applied, triggering confirmation review.
            (False, 9.2, "## Verdict: REVISE\n<fixes>apply me too</fixes>\n"),
            # Confirmation review on the fixed content: PASS. Must include a
            # scored dimension table so the validity guard accepts it.
            (True, 9.6, _fake_review_text(10, "PASS")),
        ]
    )

    def fake_step_review(*args, **kwargs):
        review_calls.append("review")
        return next(review_rounds)

    monkeypatch.setattr(v6_build, "step_review", fake_step_review)
    # Simulate a fix applier that actually mutates content in both rounds.
    monkeypatch.setattr(v6_build, "_apply_review_fixes", lambda *args, **kwargs: (True, 1))
    monkeypatch.setattr(v6_build, "_apply_review_rewrite_blocks", lambda *args, **kwargs: (False, 0))

    result = v6_build._run_review_heal_loop(
        content_path,
        level="a1",
        module_num=1,
        slug="conf-pass",
        writer="gemini",
        reviewer_override="codex-tools",
        max_rounds=2,
    )

    assert result.outcome == "pass", (
        "confirmation review with PASS should convert plateau to pass"
    )
    # Two rounds + one confirmation review = 3 step_review calls.
    assert len(review_calls) == 3
    # The last round should carry the CONFIRMATION score (9.6), not the
    # stale pre-fix score (9.2).
    assert result.rounds[-1].score == 9.6
    assert result.rounds[-1].passed is True


def test_review_loop_confirmation_review_keeps_plateau_when_still_failing(
    tmp_path: Path, monkeypatch
) -> None:
    """Bug #1316 Bug B — confirmation review cannot false-positive.

    If mutations happened but the post-fix content is still failing review
    (e.g. the reviewer finds a new or persistent issue), the confirmation
    review must still plateau. This prevents silent "pass on plateau" of
    genuinely broken content.
    """
    content_path = _setup_heal_loop_fixture(tmp_path, monkeypatch, slug="conf-still-fail")

    review_rounds = iter(
        [
            (False, 8.5, "## Verdict: REVISE\n<fixes>1</fixes>\n"),
            (False, 8.6, "## Verdict: REVISE\n<fixes>2</fixes>\n"),
            # Confirmation review: still REVISE. Include a scored dimension
            # table so the validity guard accepts it (otherwise it would be
            # rejected as malformed and plateau would still fire for the
            # wrong reason).
            (False, 8.7, _fake_review_text(8, "REVISE", fixes_body="still broken")),
        ]
    )
    monkeypatch.setattr(v6_build, "step_review", lambda *args, **kwargs: next(review_rounds))
    monkeypatch.setattr(v6_build, "_apply_review_fixes", lambda *args, **kwargs: (True, 1))
    monkeypatch.setattr(v6_build, "_apply_review_rewrite_blocks", lambda *args, **kwargs: (False, 0))

    result = v6_build._run_review_heal_loop(
        content_path,
        level="a1",
        module_num=1,
        slug="conf-still-fail",
        writer="gemini",
        reviewer_override="codex-tools",
        max_rounds=2,
    )

    assert result.outcome == "plateau"
    # Confirmation score lands on the last round — not a false pass.
    assert result.rounds[-1].score == 8.7
    assert result.rounds[-1].passed is False


def test_review_loop_ignores_malformed_confirmation_review(
    tmp_path: Path, monkeypatch
) -> None:
    """Bug #1316 Bug B — Codex re-review defect: a rate-limit error blob or
    truncated text must NOT overwrite the stale round state. If the
    confirmation review text has no scored dimension table and no explicit
    PASS/REVISE/REJECT verdict, preserve the original round state and
    accept the original plateau decision.
    """
    content_path = _setup_heal_loop_fixture(tmp_path, monkeypatch, slug="conf-malformed")

    review_rounds = iter(
        [
            (False, 9.0, "## Verdict: REVISE\n<fixes>1</fixes>\n"),
            (False, 9.1, "## Verdict: REVISE\n<fixes>2</fixes>\n"),
            # Confirmation review: malformed — no scores table, no verdict.
            # Looks like a rate-limit error blob or truncated output.
            (False, 0.0, "Error: rate limit exceeded. Please try again later."),
        ]
    )
    monkeypatch.setattr(v6_build, "step_review", lambda *args, **kwargs: next(review_rounds))
    monkeypatch.setattr(v6_build, "_apply_review_fixes", lambda *args, **kwargs: (True, 1))
    monkeypatch.setattr(v6_build, "_apply_review_rewrite_blocks", lambda *args, **kwargs: (False, 0))

    result = v6_build._run_review_heal_loop(
        content_path,
        level="a1",
        module_num=1,
        slug="conf-malformed",
        writer="gemini",
        reviewer_override="codex-tools",
        max_rounds=2,
    )

    # Plateau preserved; stale-but-real R2 score kept, not overwritten by 0.0.
    assert result.outcome == "plateau"
    assert result.rounds[-1].score == 9.1, (
        "malformed confirmation must not replace real R2 score"
    )


def test_review_loop_rejects_verdict_only_confirmation(
    tmp_path: Path, monkeypatch
) -> None:
    """Bug #1316 Bug B — Codex re-review-2 defect: a truncated reviewer
    output that contains only ``## Verdict: PASS`` but no scored
    dimension table must NOT be accepted by the confirmation-review
    validity guard. Such text could come from a rate-limit error blob
    that happens to include the word 'Verdict:', and accepting it would
    overwrite the stale round state with score=0.0 junk.

    The guard requires ``raw_scores`` to be non-empty.
    """
    content_path = _setup_heal_loop_fixture(tmp_path, monkeypatch, slug="conf-verdict-only")

    review_rounds = iter(
        [
            (False, 9.1, "## Verdict: REVISE\n<fixes>1</fixes>\n"),
            (False, 9.2, "## Verdict: REVISE\n<fixes>2</fixes>\n"),
            # Confirmation review: bare verdict, no score table.
            # Could be a truncated output or a rate-limit error blob that
            # happens to include 'Verdict: PASS' in its body.
            (False, 0.0, "## Verdict: PASS\n"),
        ]
    )
    monkeypatch.setattr(v6_build, "step_review", lambda *args, **kwargs: next(review_rounds))
    monkeypatch.setattr(v6_build, "_apply_review_fixes", lambda *args, **kwargs: (True, 1))
    monkeypatch.setattr(v6_build, "_apply_review_rewrite_blocks", lambda *args, **kwargs: (False, 0))

    result = v6_build._run_review_heal_loop(
        content_path,
        level="a1",
        module_num=1,
        slug="conf-verdict-only",
        writer="gemini",
        reviewer_override="codex-tools",
        max_rounds=2,
    )

    # Verdict-only confirmation rejected → original plateau decision stands.
    assert result.outcome == "plateau"
    assert result.rounds[-1].score == 9.2, (
        "verdict-only confirmation must not overwrite real R2 score with 0.0"
    )


def test_review_loop_rejects_truncated_score_table(
    tmp_path: Path, monkeypatch
) -> None:
    """Bug #1316 Bug B — Codex re-review-3 defect: a truncated reviewer
    output with only part of the 9-dimension score table must be
    rejected. Could come from a mid-stream timeout where the reviewer
    had emitted e.g. 5 of 9 rows before the connection dropped. Partial
    tables carry no meaningful weighted score and must not overwrite
    the stale round state.

    The guard requires ``len(raw_scores) == 9`` AND a recognized
    verdict.
    """
    content_path = _setup_heal_loop_fixture(tmp_path, monkeypatch, slug="conf-truncated")

    # Build a review body with only the first 5 dimensions scored plus
    # a Verdict line — mimics a mid-stream truncation.
    partial_dims = list(_HEAL_LOOP_DIMENSIONS[:5])
    partial_body_lines = [
        "## Scores",
        "| Dimension | Score | Evidence |",
        "|-----------|-------|----------|",
    ]
    for i, dim in enumerate(partial_dims, 1):
        partial_body_lines.append(f"| {i}. {dim} | 10/10 | ok |")
    partial_body_lines.append("\n## Verdict: PASS\n")
    partial_body = "\n".join(partial_body_lines)

    review_rounds = iter(
        [
            (False, 9.0, "## Verdict: REVISE\n<fixes>1</fixes>\n"),
            (False, 9.1, "## Verdict: REVISE\n<fixes>2</fixes>\n"),
            # Confirmation: partial (5/9) score table plus PASS verdict.
            # Must be REJECTED by the validity guard.
            (True, 5.5, partial_body),
        ]
    )
    monkeypatch.setattr(v6_build, "step_review", lambda *args, **kwargs: next(review_rounds))
    monkeypatch.setattr(v6_build, "_apply_review_fixes", lambda *args, **kwargs: (True, 1))
    monkeypatch.setattr(v6_build, "_apply_review_rewrite_blocks", lambda *args, **kwargs: (False, 0))

    result = v6_build._run_review_heal_loop(
        content_path,
        level="a1",
        module_num=1,
        slug="conf-truncated",
        writer="gemini",
        reviewer_override="codex-tools",
        max_rounds=2,
    )

    # Partial table rejected → plateau preserved, stale score kept.
    assert result.outcome == "plateau"
    assert result.rounds[-1].score == 9.1, (
        "truncated confirmation table must not overwrite real R2 score"
    )


def test_review_loop_rejects_duplicated_dimension_table(
    tmp_path: Path, monkeypatch
) -> None:
    """Bug #1316 Bug B — Codex re-review-4: a confirmation review with 9
    score rows that share duplicate dimension numbers (e.g. reviewer
    emitted dim 1 nine times) must be rejected. The guard must require
    all 9 unique dimension IDs, not just 9 regex matches.

    Gemini is known to occasionally emit the score table twice or with
    broken numbering — the existing score-pattern comment at
    scripts/build/v6_build.py:1493 acknowledges this. Without the
    unique-dim check, a malformed 9-match-but-same-dim table would
    slip through and overwrite the stale round state.
    """
    content_path = _setup_heal_loop_fixture(tmp_path, monkeypatch, slug="conf-dup-dim")

    # Build a review body with 9 rows all numbered "1. Plan adherence".
    # This parses to raw_scores of length 9 (first 9 regex matches) but
    # parsed_scores dedupes by dim number, giving a unique-dim set of {1}.
    dup_lines = [
        "## Scores",
        "| Dimension | Score | Evidence |",
        "|-----------|-------|----------|",
    ]
    for _ in range(9):
        dup_lines.append("| 1. Plan adherence | 10/10 | ok |")
    dup_lines.append("\n## Verdict: PASS\n")
    dup_body = "\n".join(dup_lines)

    review_rounds = iter(
        [
            (False, 9.0, "## Verdict: REVISE\n<fixes>1</fixes>\n"),
            (False, 9.1, "## Verdict: REVISE\n<fixes>2</fixes>\n"),
            # Confirmation: 9 rows of dim 1, verdict PASS. Must be REJECTED.
            (True, 10.0, dup_body),
        ]
    )
    monkeypatch.setattr(v6_build, "step_review", lambda *args, **kwargs: next(review_rounds))
    monkeypatch.setattr(v6_build, "_apply_review_fixes", lambda *args, **kwargs: (True, 1))
    monkeypatch.setattr(v6_build, "_apply_review_rewrite_blocks", lambda *args, **kwargs: (False, 0))

    result = v6_build._run_review_heal_loop(
        content_path,
        level="a1",
        module_num=1,
        slug="conf-dup-dim",
        writer="gemini",
        reviewer_override="codex-tools",
        max_rounds=2,
    )

    # Duplicate-dim confirmation rejected → plateau preserved.
    assert result.outcome == "plateau"
    assert result.rounds[-1].score == 9.1, (
        "confirmation with duplicate dim numbers must not overwrite R2"
    )


def test_review_loop_confirmation_triggers_on_two_small_deltas_plateau(
    tmp_path: Path, monkeypatch
) -> None:
    """Bug #1316 Bug B — confirmation must also trigger on the
    ``two_small_deltas`` plateau path, not only on ``max_rounds``.

    When two consecutive rounds improve by less than 0.2, the loop
    declares plateau with reason ``two_small_deltas``. If mutations
    happened in that last round, a confirmation review must still run.
    """
    content_path = _setup_heal_loop_fixture(tmp_path, monkeypatch, slug="conf-two-small")

    # Three rounds with small deltas: 9.0 -> 9.1 -> 9.2 (both deltas < 0.2)
    # trigger the two_small_deltas plateau at round 3. Mutations happened,
    # so confirmation must run and see the post-fix content score of 9.7.
    review_rounds = iter(
        [
            (False, 9.0, "## Verdict: REVISE\n<fixes>1</fixes>\n"),
            (False, 9.1, "## Verdict: REVISE\n<fixes>2</fixes>\n"),
            (False, 9.2, "## Verdict: REVISE\n<fixes>3</fixes>\n"),
            (True, 9.7, _fake_review_text(10, "PASS")),  # confirmation
        ]
    )
    monkeypatch.setattr(v6_build, "step_review", lambda *args, **kwargs: next(review_rounds))
    monkeypatch.setattr(v6_build, "_apply_review_fixes", lambda *args, **kwargs: (True, 1))
    monkeypatch.setattr(v6_build, "_apply_review_rewrite_blocks", lambda *args, **kwargs: (False, 0))

    result = v6_build._run_review_heal_loop(
        content_path,
        level="a1",
        module_num=1,
        slug="conf-two-small",
        writer="gemini",
        reviewer_override="codex-tools",
        max_rounds=6,  # well above 3 — plateau must come from small deltas.
    )

    assert result.outcome == "pass"
    assert result.rounds[-1].score == 9.7


def test_review_loop_confirmation_triggers_on_word_budget_rewrite_only(
    tmp_path: Path, monkeypatch
) -> None:
    """Bug #1316 Bug B — word_budget_rewrite alone must trigger confirmation.

    The three mutation paths are independent: main fixes, rewrite blocks,
    and word-budget rewrites. A round where ONLY the word-budget rewrite
    applied still changes content and still invalidates the pre-fix
    review score, so confirmation must run.
    """
    content_path = _setup_heal_loop_fixture(tmp_path, monkeypatch, slug="conf-word-budget")

    review_rounds = iter(
        [
            (False, 9.0, "## Verdict: REVISE\n"),
            (False, 9.1, "## Verdict: REVISE\n"),
            (True, 9.5, _fake_review_text(10, "PASS")),  # confirmation
        ]
    )
    monkeypatch.setattr(v6_build, "step_review", lambda *args, **kwargs: next(review_rounds))
    monkeypatch.setattr(v6_build, "_apply_review_fixes", lambda *args, **kwargs: (False, 0))
    monkeypatch.setattr(v6_build, "_apply_review_rewrite_blocks", lambda *args, **kwargs: (False, 0))
    # Only word-budget rewrite applies a mutation.
    monkeypatch.setattr(
        v6_build,
        "_apply_contract_word_budget_rewrites",
        lambda *args, **kwargs: (True, 1),
    )

    result = v6_build._run_review_heal_loop(
        content_path,
        level="a1",
        module_num=1,
        slug="conf-word-budget",
        writer="gemini",
        reviewer_override="codex-tools",
        max_rounds=2,
    )

    assert result.outcome == "pass"
    assert result.rounds[-1].score == 9.5


def test_review_loop_confirmation_pass_blocked_by_contract_errors(
    tmp_path: Path, monkeypatch
) -> None:
    """Bug #1316 Bug B — confirmation PASS must not override blocking
    contract ERROR violations.

    The plateau decision uses ``latest.passed and not latest.contract_blocking``
    to detect a pass. Even if the confirmation review says PASS, an
    ERROR-severity contract violation on the same content must keep the
    outcome as plateau.
    """
    content_path = _setup_heal_loop_fixture(tmp_path, monkeypatch, slug="conf-contract-err")

    # Contract check returns a blocking ERROR violation (overrides the
    # default no-op setup fixture).
    monkeypatch.setattr(
        "audit.checks.contract_compliance.check_contract_compliance",
        lambda *args, **kwargs: [
            {
                "type": "MISSING_SECTION",
                "severity": "ERROR",
                "section": "(whole module)",
                "message": "Missing required H2 section",
            }
        ],
    )

    review_rounds = iter(
        [
            (False, 9.0, "## Verdict: REVISE\n<fixes>1</fixes>\n"),
            (False, 9.1, "## Verdict: REVISE\n<fixes>2</fixes>\n"),
            # Confirmation says PASS but contract still has ERROR —
            # plateau must stand.
            (True, 9.7, _fake_review_text(10, "PASS")),
        ]
    )
    monkeypatch.setattr(v6_build, "step_review", lambda *args, **kwargs: next(review_rounds))
    monkeypatch.setattr(v6_build, "_apply_review_fixes", lambda *args, **kwargs: (True, 1))
    monkeypatch.setattr(v6_build, "_apply_review_rewrite_blocks", lambda *args, **kwargs: (False, 0))

    result = v6_build._run_review_heal_loop(
        content_path,
        level="a1",
        module_num=1,
        slug="conf-contract-err",
        writer="gemini",
        reviewer_override="codex-tools",
        max_rounds=2,
    )

    assert result.outcome == "plateau", (
        "confirmation PASS must not bypass blocking contract ERROR violations"
    )
    # Confirmation score still lands on the round (for observability),
    # but the contract_blocking flag keeps _review_loop_decision from
    # choosing the pass branch.
    assert result.rounds[-1].score == 9.7
    assert result.rounds[-1].contract_blocking is True


def test_review_loop_skips_confirmation_when_no_mutations(
    tmp_path: Path, monkeypatch
) -> None:
    """Bug #1316 Bug B — efficiency check.

    If the final round did not apply any fixes/rewrites/word-budget
    rewrites, the pre-fix score is NOT stale and no confirmation review
    is needed. This avoids a spurious extra LLM call on genuinely stuck
    modules where the reviewer keeps complaining without the pipeline
    making any changes.
    """
    content_path = _setup_heal_loop_fixture(tmp_path, monkeypatch, slug="no-mutation")

    review_rounds = iter(
        [
            (False, 7.0, "## Verdict: REVISE\n"),
            (False, 7.0, "## Verdict: REVISE\n"),
        ]
    )
    call_count = {"n": 0}

    def counting_step_review(*args, **kwargs):
        call_count["n"] += 1
        return next(review_rounds)

    monkeypatch.setattr(v6_build, "step_review", counting_step_review)
    # No mutations in any round.
    monkeypatch.setattr(v6_build, "_apply_review_fixes", lambda *args, **kwargs: (False, 0))
    monkeypatch.setattr(v6_build, "_apply_review_rewrite_blocks", lambda *args, **kwargs: (False, 0))

    result = v6_build._run_review_heal_loop(
        content_path,
        level="a1",
        module_num=1,
        slug="no-mutation",
        writer="gemini",
        reviewer_override="codex-tools",
        max_rounds=2,
    )

    assert result.outcome == "plateau"
    # Exactly 2 reviews — no confirmation call because nothing was mutated.
    assert call_count["n"] == 2


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


def test_extract_structured_findings_handles_bare_plain_markdown() -> None:
    """Bug #1316 Bug A regression.

    Real reviewer output (A1/M01 review r9) uses bare plain-markdown finding
    blocks under ``## Findings`` — not fenced code blocks. The previous
    extractor only matched fenced blocks, so real findings were silently
    dropped and ``review-structured-r*.yaml`` reported ``findings: []``,
    which in turn tricked the plateau/heal loop into giving up on modules
    that actually had actionable fixes.
    """
    review = (
        "## Findings\n"
        "[PLAN ADHERENCE] [SEVERITY: major]\n"
        "Location: `## Звуки і літери` — the alphabet section.\n"
        "Issue: The draft never shows the 33 letters in order.\n"
        "Fix: List all 33 letters in contracted order.\n"
        "\n"
        "## Verdict: REVISE\n"
    )
    findings = v6_build._extract_structured_findings(review)
    assert len(findings) == 1
    assert findings[0]["dimension"] == "PLAN ADHERENCE"
    assert findings[0]["severity"] == "major"
    assert "33 letters" in findings[0]["issue"]


def test_extract_structured_findings_handles_bold_prefix() -> None:
    """Bold-prefix shape used by some reviewers: ``**[DIM] [SEV]**``."""
    review = (
        "## Findings\n"
        "**[LINGUISTIC ACCURACY] [minor]**\n"
        "Location: Section 2\n"
        "Issue: Small wording issue.\n"
        "Fix: Adjust the phrase.\n"
        "\n"
        "**[PLAN ADHERENCE] [major]**\n"
        "Location: Section 3\n"
        "Issue: Missing beat.\n"
        "Fix: Add the beat.\n"
        "\n"
        "## Verdict: REVISE\n"
    )
    findings = v6_build._extract_structured_findings(review)
    assert len(findings) == 2
    severities = [f["severity"] for f in findings]
    assert severities == ["minor", "major"]


def test_extract_structured_findings_mixed_fenced_and_bare() -> None:
    """Bug #1316 Bug A — adversarial case from Codex review.

    A review may contain both a fenced finding AND bare findings. The
    previous fallback-only design returned after the first parser matched,
    silently dropping the rest. Both must be collected.
    """
    review = (
        "## Findings\n"
        "```\n"
        "[LINGUISTIC] [critical]\n"
        "Location: Section A\n"
        "Issue: Fenced issue.\n"
        "Fix: Fenced fix.\n"
        "```\n"
        "\n"
        "[PEDAGOGICAL] [minor]\n"
        "Location: Section B\n"
        "Issue: Bare issue.\n"
        "Fix: Bare fix.\n"
        "\n"
        "## Verdict: REVISE\n"
    )
    findings = v6_build._extract_structured_findings(review)
    assert len(findings) == 2
    dims = {f["dimension"] for f in findings}
    assert dims == {"LINGUISTIC", "PEDAGOGICAL"}


def test_extract_structured_findings_back_to_back_no_blank_line() -> None:
    """Two findings separated by only a newline (no blank line) must both parse."""
    review = (
        "## Findings\n"
        "[A] [minor]\n"
        "Location: L1\n"
        "Issue: I1\n"
        "Fix: F1\n"
        "[B] [major]\n"
        "Location: L2\n"
        "Issue: I2\n"
        "Fix: F2\n"
        "\n"
        "## Verdict: REVISE\n"
    )
    findings = v6_build._extract_structured_findings(review)
    assert len(findings) == 2
    assert [f["dimension"] for f in findings] == ["A", "B"]


def test_extract_structured_findings_malformed_fails_closed() -> None:
    """A Findings section that is prose or missing the Fix: field must not
    return a partial finding. Fail closed rather than producing garbage."""
    prose_only = (
        "## Findings\n"
        "This is prose, not structured.\n"
        "No bracket markers at all.\n"
        "\n"
        "## Verdict: REVISE\n"
    )
    assert v6_build._extract_structured_findings(prose_only) == []

    missing_fix = (
        "## Findings\n"
        "[SOMETHING] [minor]\n"
        "Location: here\n"
        "Issue: wrong\n"
        "\n"
        "## Verdict: REVISE\n"
    )
    assert v6_build._extract_structured_findings(missing_fix) == []


def test_extract_structured_findings_bold_then_bare_no_blank_line() -> None:
    """Bug #1316 Bug A — Codex re-review: bold finding immediately followed
    by a bare finding with no blank line separator.

    The bold terminator must include ``\\n(?=\\[)`` so the bare finding's
    header does not get absorbed into the bold finding's Fix field. The
    canonical parser in ``aggregate_review_findings.py`` has the same bug;
    fixing it there is out of scope for this issue.
    """
    review = (
        "## Findings\n"
        "**[LINGUISTIC ACCURACY] [minor]**\n"
        "Location: Section 2\n"
        "Issue: Bold issue.\n"
        "Fix: Bold fix.\n"
        "[PLAN ADHERENCE] [major]\n"
        "Location: Section 3\n"
        "Issue: Bare issue.\n"
        "Fix: Bare fix.\n"
        "\n"
        "## Verdict: REVISE\n"
    )
    findings = v6_build._extract_structured_findings(review)
    assert len(findings) == 2, f"expected 2, got {len(findings)}: {findings}"
    assert [f["dimension"] for f in findings] == ["LINGUISTIC ACCURACY", "PLAN ADHERENCE"]
    # Verify the bold finding's Fix field did NOT absorb the bare header:
    assert "PLAN ADHERENCE" not in findings[0]["fix"]


def test_extract_structured_findings_all_three_shapes_in_one_section() -> None:
    """A single ``## Findings`` section containing fenced + bold + bare
    findings must return all three, regardless of ordering."""
    review = (
        "## Findings\n"
        "```\n"
        "[LINGUISTIC] [critical]\n"
        "Location: Section A\n"
        "Issue: Fenced issue.\n"
        "Fix: Fenced fix.\n"
        "```\n"
        "\n"
        "**[PEDAGOGICAL] [major]**\n"
        "Location: Section B\n"
        "Issue: Bold issue.\n"
        "Fix: Bold fix.\n"
        "\n"
        "[PLAN ADHERENCE] [minor]\n"
        "Location: Section C\n"
        "Issue: Bare issue.\n"
        "Fix: Bare fix.\n"
        "\n"
        "## Verdict: REVISE\n"
    )
    findings = v6_build._extract_structured_findings(review)
    assert len(findings) == 3
    dims = {f["dimension"] for f in findings}
    assert dims == {"LINGUISTIC", "PEDAGOGICAL", "PLAN ADHERENCE"}


def test_extract_structured_findings_warns_on_unparseable_section(caplog, capsys) -> None:
    """Bug #1316 Bug A — Codex re-review #4.

    When ``## Findings`` exists with prose content but nothing parses, the
    extractor must emit a visible warning so grammar drift cannot silently
    masquerade as ``findings: []`` again.
    """
    prose_only = (
        "## Findings\n"
        "This reviewer wrote prose instead of structured findings.\n"
        "\n"
        "## Verdict: REVISE\n"
    )
    result = v6_build._extract_structured_findings(prose_only)
    captured = capsys.readouterr()
    combined_output = captured.out + captured.err
    assert result == []
    assert "Bug #1316" in combined_output or "grammar may have drifted" in combined_output, (
        f"expected grammar-drift warning, got stdout={captured.out!r} stderr={captured.err!r}"
    )


def test_extract_structured_findings_no_findings_section_returns_empty() -> None:
    """A review with a PASS verdict and no Findings section must return []
    with no warning logged."""
    clean = (
        "## Scores\n"
        "| 1. X | 10/10 | all good |\n"
        "\n"
        "## Verdict: PASS\n"
    )
    assert v6_build._extract_structured_findings(clean) == []
    assert v6_build._extract_structured_findings("") == []


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
