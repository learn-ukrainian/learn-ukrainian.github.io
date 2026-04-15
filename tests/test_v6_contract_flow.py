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


def test_apply_style_review_rewrite_blocks_groups_by_section(tmp_path: Path, monkeypatch) -> None:
    level = "a1"
    slug = "style-rewrite-flow"
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    content_path = curriculum_root / level / f"{slug}.md"
    content_path.parent.mkdir(parents=True, exist_ok=True)
    content_path.write_text("## Intro\nOld intro.\n\n## Practice\nOld practice.\n", "utf-8")

    calls: list[tuple[str, str]] = []

    def fake_rewrite(*args, **kwargs):
        calls.append((kwargs["section_name"], kwargs["directive"]))
        return True

    monkeypatch.setattr(v6_build, "_rewrite_block_section", fake_rewrite)

    ok, count = v6_build._apply_style_review_rewrite_blocks(
        """phase: review-style
verdict: REVISE
pass: false
overall_score: 8.4
scores: []
blocking_issues:
  - type: META_PEDAGOGICAL_NARRATION
    location: "Section: Intro, paragraph 1"
    evidence: "In this dialogue..."
    fix: "Teach the point directly."
  - type: REGISTER_MISMATCH
    location: "Practice, dialogue"
    evidence: "Що ви хочете?"
    fix: "Use a more polite service opener."
  - type: META_PEDAGOGICAL_NARRATION
    location: "Section: Intro, closing"
    evidence: "Here ..."
    fix: "Remove local meta-commentary."
""",
        content_path,
        level=level,
        module_num=1,
        slug=slug,
        writer="gemini",
    )

    assert ok is True
    assert count == 2
    assert calls[0][0] == "Intro"
    assert "Teach the point directly." in calls[0][1]
    assert "Remove local meta-commentary." in calls[0][1]
    assert calls[1][0] == "Practice"
    assert "Use a more polite service opener." in calls[1][1]


def test_apply_style_review_rewrite_blocks_maps_dialogue_and_whole_module_locations(
    tmp_path: Path, monkeypatch
) -> None:
    level = "a1"
    slug = "style-location-flow"
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    content_path = curriculum_root / level / f"{slug}.md"
    content_path.parent.mkdir(parents=True, exist_ok=True)
    content_path.write_text(
        "## Діалоги (Dialogues)\nOld dialogue.\n\n"
        "## Хотіти (To Want)\nOld want.\n\n"
        "## Підсумок — Summary\nOld summary.\n",
        "utf-8",
    )

    calls: list[str] = []

    def fake_rewrite(*args, **kwargs):
        calls.append(kwargs["section_name"])
        return True

    monkeypatch.setattr(v6_build, "_rewrite_block_section", fake_rewrite)

    ok, count = v6_build._apply_style_review_rewrite_blocks(
        """phase: review-style
verdict: REVISE
pass: false
overall_score: 5.8
scores: []
blocking_issues:
  - type: META_PEDAGOGICAL_NARRATION
    location: "Діалоги opening prose and commentary, lines 3-5; Підсумок, lines 20-30"
    evidence: "Notice how..."
    fix: "Replace the meta-teaching narration."
  - type: EXPLANATION_TONE_MISMATCH
    location: "Whole module prose outside the example sentences"
    evidence: "Communication often revolves..."
    fix: "Rewrite the explanatory layer in concise Ukrainian educational prose."
  - type: TRANSLATED_DIALOGUE_RHYTHM
    location: "First dialogue, lines 9-11"
    evidence: "Це погано. А завтра?"
    fix: "Use a more idiomatic reaction."
  - type: SERVICE_REGISTER_STIFFNESS
    location: "Café dialogue, line 17"
    evidence: "Що ви хочете?"
    fix: "Use a more natural service opener."
""",
        content_path,
        level=level,
        module_num=1,
        slug=slug,
        writer="gemini",
    )

    assert ok is True
    assert count == 3
    assert calls.count("Діалоги (Dialogues)") == 1
    assert calls.count("Хотіти (To Want)") == 1
    assert calls.count("Підсумок — Summary") == 1


def test_apply_style_review_rewrite_blocks_adds_a1_guardrails(tmp_path: Path, monkeypatch) -> None:
    level = "a1"
    slug = "style-guardrails"
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    content_path = curriculum_root / level / f"{slug}.md"
    content_path.parent.mkdir(parents=True, exist_ok=True)
    content_path.write_text(
        "## Діалоги (Dialogues)\nOld dialogue.\n\n"
        "## Хотіти (To Want)\nOld want.\n\n"
        "## Підсумок — Summary\nOld summary.\n",
        "utf-8",
    )

    calls: dict[str, str] = {}

    def fake_rewrite(*args, **kwargs):
        calls[kwargs["section_name"]] = kwargs["directive"]
        return True

    monkeypatch.setattr(v6_build, "_rewrite_block_section", fake_rewrite)

    ok, count = v6_build._apply_style_review_rewrite_blocks(
        """phase: review-style
verdict: REVISE
pass: false
overall_score: 7.3
scores: []
blocking_issues:
  - type: META_PEDAGOGICAL_NARRATION
    location: "Підсумок — Summary, opening"
    evidence: "This text demonstrates..."
    fix: "Replace with a direct reading cue."
  - type: TRANSLATIONESE
    location: "Діалоги (Dialogues), explanatory framing"
    evidence: "Наступна розмова відбувається в кафе."
    fix: "Cut the scene-announcing narration."
  - type: PRAGMATIC_MISFRAMING
    location: "Діалоги (Dialogues), note after dialogue"
    evidence: "Шкода is a polite refusal."
    fix: "Explain that шкода expresses regret and can soften a refusal."
  - type: STYLE_REGISTER_MISMATCH
    location: "Хотіти (To Want), opening explanation"
    evidence: "The verb хотіти is essential..."
    fix: "Keep exposition in one coherent Ukrainian pedagogical register."
  - type: REGISTER_MISMATCH
    location: "Діалоги (Dialogues), café exchange closing"
    evidence: "Чудово, давайте борщ."
    fix: "Use a more natural ordering formula."
  - type: MIXED_EXPLANATORY_VOICE
    location: "Хотіти (To Want); Могти і мусити (Can and Must)"
    evidence: "dense inline glosses"
    fix: "Keep one concise Ukrainian pedagogical voice."
  - type: TRANSLATIONESE_EXPLANATION
    location: "Хотіти (To Want); Підсумок — Summary"
    evidence: "у своїй базовій словниковій формі"
    fix: "Rewrite into plainer Ukrainian pedagogical prose."
  - type: FORMULAIC_SECTION_OPENERS
    location: "Підсумок — Summary, opening and cue lines"
    evidence: "Запам'ятайте: / Прочитайте й повторіть:"
    fix: "Replace worksheet-style commands with plain recap prose."
  - type: WORKSHEET_DIALOGUE_RHYTHM
    location: "Діалоги (Dialogues), café exchange"
    evidence: "Велику. І можна ще борщ?"
    fix: "Turn this into a fuller service exchange with a reactive recommendation turn and a natural close."
  - type: REGISTER_DRIFT
    location: "Підсумок — Summary, opening and mid-section"
    evidence: "Порівняйте ці речення... Запам'ятайте..."
    fix: "Turn the summary into a short natural recap."
  - type: ABSTRACT_SUMMARY_REGISTER
    location: "Підсумок — Summary, opening and closing prose"
    evidence: "These verbs express desires, abilities, and obligations"
    fix: "Replace abstract recap with concrete everyday examples."
  - type: UNNATURAL_COLLOCATION
    location: "Хотіти (To Want), examples"
    evidence: "Він хоче великий чай."
    fix: "Use idiomatic everyday collocations."
  - type: UNNATURAL_SERVICE_DIALOGUE
    location: "Діалоги (Dialogues), café dialogue"
    evidence: "Можу порекомендувати український борщ."
    fix: "Use plainer native service speech."
  - type: UNNATURAL_SERVICE_PHRASE
    location: "Діалоги (Dialogues), café dialogue final turn"
    evidence: "Чудово, давайте борщ."
    fix: "Use a more idiomatic final order."
  - type: NON_IDIOMATIC_MODEL_EXAMPLE
    location: "Підсумок — Summary, accusative examples"
    evidence: "Він хоче великий чай."
    fix: "Use a more idiomatic beginner model."
  - type: OVERSTATED_USAGE_EXPLANATION
    location: "Діалоги (Dialogues), explanation after café dialogue"
    evidence: "Я хочу їсти is the standard everyday way to say I am hungry."
    fix: "Present it as one common colloquial option and mention голодний/голодна."
  - type: PRAGMATIC_EQUIVALENCE
    location: "Діалоги (Dialogues), café explanation paragraph"
    evidence: "The phrase я хочу їсти is the standard, everyday way to say I am hungry."
    fix: "State the literal meaning first and mention everyday alternatives."
  - type: UNIDIOMATIC_COLLOCATION
    location: "Підсумок — Summary, evening-plans paragraph"
    evidence: "вона хоче пити смачну каву"
    fix: "Prefer a more idiomatic collocation."
""",
        content_path,
        level=level,
        module_num=18,
        slug=slug,
        writer="gemini",
    )

    assert ok is True
    assert count == 3
    summary_directive = calls["Підсумок — Summary"]
    assert "Lecture-style explanation is allowed" in summary_directive
    assert "Forbidden meta phrasing" in summary_directive
    assert "In summary sections, use direct Ukrainian instructional prose" in summary_directive
    assert "delete meta-teaching lead-ins entirely instead of paraphrasing them" in summary_directive
    assert "Start the summary immediately with Ukrainian recap content" in summary_directive
    assert "short natural recap with everyday examples" in summary_directive
    dialogue_directive = calls["Діалоги (Dialogues)"]
    assert "In dialogue sections, start with the dialogue" in dialogue_directive
    assert "Do not announce the scene beforehand" in dialogue_directive
    assert "one natural communicative goal per turn" in dialogue_directive
    assert "express regret and can soften a refusal" in dialogue_directive
    assert "prefer short request-based ordering and plain staff responses" in dialogue_directive
    assert "do not use blunt `Я хочу [noun]` as the direct order" in dialogue_directive
    assert "state the literal meaning of the target phrase first" in dialogue_directive
    want_directive = calls["Хотіти (To Want)"]
    dialogue_directive = calls["Діалоги (Dialogues)"]
    assert "English may appear only as brief parenthetical glosses" in want_directive
    assert "Rewrite any full English lecture-style explanation paragraph" in want_directive
    assert "let the exchange breathe: request -> clarifying question or recommendation" in dialogue_directive
    assert "Prefer idiomatic everyday collocations" in want_directive
    assert "Prefer the more idiomatic everyday collocation" in summary_directive
    assert "do not write traps like `частка не завжди ...`" in want_directive
    assert "Replace model sentences that are merely grammatical" in summary_directive
    assert "do not use worksheet commands like `Запам'ятайте`" in summary_directive
    assert "avoid abstract lecture lines like `These verbs express...`" in summary_directive
    assert "do not write traps like `частка не завжди ...`" in summary_directive


def test_run_style_review_heal_loop_rewrites_then_passes(tmp_path: Path, monkeypatch) -> None:
    level = "a1"
    slug = "style-heal-flow"
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    content_path = curriculum_root / level / f"{slug}.md"
    content_path.parent.mkdir(parents=True, exist_ok=True)
    content_path.write_text("## Intro\nOld intro.\n\n## Practice\nOld practice.\n", "utf-8")

    reviews = iter(
        [
            (
                False,
                8.4,
                """phase: review-style
verdict: REVISE
pass: false
overall_score: 8.4
scores:
  - key: pragmatic_authenticity
    score: 9.0
  - key: stylistic_consistency
    score: 8.2
  - key: culture_and_register
    score: 9.0
  - key: naturalness
    score: 8.4
blocking_issues:
  - type: META_PEDAGOGICAL_NARRATION
    location: "Section: Intro, paragraph 1"
    evidence: "In this dialogue..."
    fix: "Teach the point directly."
""",
            ),
            (
                True,
                9.2,
                """phase: review-style
verdict: PASS
pass: true
overall_score: 9.2
scores:
  - key: pragmatic_authenticity
    score: 9.2
  - key: stylistic_consistency
    score: 9.0
  - key: culture_and_register
    score: 9.3
  - key: naturalness
    score: 9.1
blocking_issues: []
""",
            ),
        ]
    )

    monkeypatch.setattr(v6_build, "step_review_style", lambda *args, **kwargs: next(reviews))
    monkeypatch.setattr(v6_build, "_apply_style_review_rewrite_blocks", lambda *args, **kwargs: (True, 1))
    monkeypatch.setattr(v6_build, "step_verify", lambda *args, **kwargs: "complete")

    result = v6_build._run_style_review_heal_loop(
        content_path,
        level=level,
        module_num=1,
        slug=slug,
        writer="gemini",
        reviewer_override=None,
    )

    assert result.outcome == "pass"
    assert [round_state.score for round_state in result.rounds] == [8.4, 9.2]


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


def test_main_marks_needs_human_review_after_style_plateau(tmp_path: Path, monkeypatch) -> None:
    level = "a1"
    slug = "style-needs-human"
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
            outcome="plateau",
            rounds=(
                v6_build.StyleReviewRoundState(
                    round_num=1,
                    passed=False,
                    score=8.4,
                    review_text="phase: review-style\nverdict: REVISE\n",
                    blocking_issues=({"type": "META_PEDAGOGICAL_NARRATION"},),
                ),
                v6_build.StyleReviewRoundState(
                    round_num=2,
                    passed=False,
                    score=8.5,
                    review_text="phase: review-style\nverdict: REVISE\n",
                    blocking_issues=({"type": "META_PEDAGOGICAL_NARRATION"},),
                ),
            ),
        ),
    )
    monkeypatch.setattr(sys, "argv", ["v6_build.py", level, "1", "--step", "review-style", "--writer", "gemini"])

    result = v6_build.main()

    state = json.loads((orch_dir / "state.json").read_text("utf-8"))
    needs_human_review = yaml.safe_load((orch_dir / "needs-human-review.yaml").read_text("utf-8"))
    assert result is False
    assert state["needs_human_review"]["status"] is True
    assert needs_human_review["style_review_rounds"] == 2
    assert needs_human_review["style_score_history"] == [8.4, 8.5]


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
