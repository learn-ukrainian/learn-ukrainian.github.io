from __future__ import annotations

import shutil
import sys
import textwrap
from pathlib import Path
from types import SimpleNamespace

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import build.dispatch as dispatch
import build.v6_build as v6_build

REVIEW_PASS_RAW = """\
| 1. Plan adherence | 9/10 | grounded |
| 2. Linguistic accuracy | 9/10 | accurate |
| 3. Pedagogical quality | 9/10 | clear |
| 4. Vocabulary coverage | 9/10 | on target |
| 5. Exercise quality | 9/10 | aligned |
| 6. Engagement & tone | 9/10 | engaging |
| 7. Structural integrity | 9/10 | solid |
| 8. Cultural accuracy | 9/10 | appropriate |
| 9. Dialogue & conversation quality | 9/10 | natural |

Verdict: PASS
"""

# Per-dim reviewer (added #1421) — 9 independent calls + per-dim templates.
PER_DIM_REVIEW_IDS = (
    "factual",
    "language",
    "decolonization",
    "completeness",
    "actionable",
    "naturalness",
    "plan_adherence",
    "honesty",
    "dialogue",
)

PER_DIM_REVIEW_RAW = (
    "## Dimension\n"
    "id: {dim_id}\n"
    "name: {dim_id}\n"
    "score: 9.0/10\n"
    "verdict: PASS\n"
    "\n"
    "## Evidence\n"
    "- grounded in cited sources\n"
    "\n"
    "## Findings\n"
    "None.\n"
)


def _write_phase_templates(phases_dir: Path) -> None:
    phases_dir.mkdir(parents=True, exist_ok=True)
    templates = {
        "v6-write.md": "EN-WRITE\n{CONTRACT_YAML}\n{SECTION_WIKI_EXCERPTS}\n{SKELETON_SECTION}\n",
        "v6-write-uk.md": "UK-WRITE\n{CONTRACT_YAML}\n{SECTION_WIKI_EXCERPTS}\n{SKELETON_SECTION}\n",
        "v6-vocab.md": "EN-VOCAB\n{PLAN_VOCABULARY}\n{MODULE_CONTENT}\n",
        "v6-vocab-uk.md": "UK-VOCAB\n{PLAN_VOCULARY}\n{PLAN_VOCABULARY}\n{MODULE_CONTENT}\n",
        "v6-activities.md": "EN-ACTIVITIES\n{LEVEL_CONTEXT}\n{INJECTION_MARKERS}\n{PLAN_ACTIVITY_HINTS}\n{MODULE_CONTENT}\n",
        "v6-activities-uk.md": "UK-ACTIVITIES\n{LEVEL_CONTEXT}\n{INJECTION_MARKERS}\n{PLAN_ACTIVITY_HINTS}\n{MODULE_CONTENT}\n",
        # ``v6-review.md`` / ``v6-review-uk.md`` are legacy: the per-dim
        # refactor (#1421) loads from ``v6-review/v6-review-{dim}.md``
        # instead. Legacy entries are retained so tests exercising the
        # resolver at the monolithic name (e.g. suite-variant lookup) keep
        # working. See ``test_phase_suite_switches_templates_and_writer_default``.
        "v6-review.md": "EN-REVIEW\n{CONTRACT_YAML}\n{SECTION_WIKI_EXCERPTS}\n{GENERATED_CONTENT}\n",
        "v6-review-uk.md": "UK-REVIEW\n{CONTRACT_YAML}\n{SECTION_WIKI_EXCERPTS}\n{GENERATED_CONTENT}\n",
        "v6-review-style.md": "STYLE\n{GENERATED_CONTENT}\n",
    }
    for name, body in templates.items():
        (phases_dir / name).write_text(body, "utf-8")

    review_subdir = phases_dir / "v6-review"
    review_subdir.mkdir(parents=True, exist_ok=True)
    # Only ``{CONTRACT_YAML}`` / ``{SECTION_WIKI_EXCERPTS}`` /
    # ``{GENERATED_CONTENT}`` are substituted by v6_build — the rest are
    # raw text, so we cannot use ``str.format`` here (it would try to
    # resolve the prompt placeholders as keyword args).
    for dim_id in PER_DIM_REVIEW_IDS:
        filename = f"v6-review-{dim_id.replace('_', '-')}.md"
        body = (
            f"PER-DIM-{dim_id.upper()}\n"
            "{CONTRACT_YAML}\n"
            "{SECTION_WIKI_EXCERPTS}\n"
            "{GENERATED_CONTENT}\n"
        )
        (review_subdir / filename).write_text(body, "utf-8")

    (phases_dir / "v6-enrich-uk.md").write_text(
        textwrap.dedent(
            """\
            ---
            lesson_tab_label: Урок
            vocab_tab_label: Словник
            workbook_tab_label: Зошит
            resources_tab_label: Ресурси
            slovnyk_mode: definition
            allow_plan_fallback: false
            flashcards: false
            ---

            # UK enrich profile
            """
        ),
        "utf-8",
    )


def _seed_module_tree(tmp_path: Path, *, level: str = "a1", slug: str = "uk-phase-suite") -> dict[str, Path]:
    project_root = tmp_path
    curriculum_root = project_root / "curriculum" / "l2-uk-en"
    phases_dir = project_root / "scripts" / "build" / "phases"
    orch_dir = curriculum_root / level / "orchestration" / slug
    review_dir = curriculum_root / level / "review"

    _write_phase_templates(phases_dir)

    (curriculum_root / level).mkdir(parents=True, exist_ok=True)
    (curriculum_root / "plans" / level).mkdir(parents=True, exist_ok=True)
    orch_dir.mkdir(parents=True, exist_ok=True)
    review_dir.mkdir(parents=True, exist_ok=True)
    (project_root / "starlight" / "src" / "content" / "docs" / level).mkdir(parents=True, exist_ok=True)

    plan = {
        "module": 1,
        "slug": slug,
        "level": level,
        "sequence": 1,
        "title": "Український еталон",
        "phase": "A1.1",
        "word_target": 1200,
        "content_outline": [
            {"section": "Вступ", "words": 720, "points": ["вітання", "рід"]},
            {"section": "Підсумок", "words": 480, "points": ["самоперевірка"]},
        ],
        "dialogue_situations": [],
        "vocabulary_hints": {
            "required": ["аспект (aspect)", "форма (form)"],
        },
        "activity_hints": [
            {"id": "quiz-vid", "type": "quiz", "focus": "вид дієслова"},
        ],
    }
    (curriculum_root / "plans" / level / f"{slug}.yaml").write_text(
        yaml.safe_dump(plan, sort_keys=False, allow_unicode=True),
        "utf-8",
    )
    (curriculum_root / "curriculum.yaml").write_text(
        yaml.safe_dump({"levels": {level: {"modules": [slug]}}}, sort_keys=False, allow_unicode=True),
        "utf-8",
    )

    packet_path = curriculum_root / level / "research" / f"{slug}-knowledge-packet.md"
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_text("## Packet\nУкраїнський контекст.\n", "utf-8")

    schema_src = Path(__file__).resolve().parent.parent / "schemas" / "activity-v2.schema.json"
    (project_root / "schemas").mkdir(parents=True, exist_ok=True)
    shutil.copy(schema_src, project_root / "schemas" / "activity-v2.schema.json")

    return {
        "project_root": project_root,
        "curriculum_root": curriculum_root,
        "phases_dir": phases_dir,
        "packet_path": packet_path,
        "orch_dir": orch_dir,
        "slug": Path(slug),
    }


def _contract_artifacts() -> tuple[dict, dict]:
    return (
        {
            "module": {"title": "Український еталон"},
            "teaching_beats": {
                "section_order": ["Вступ", "Підсумок"],
                "sections": [
                    {
                        "order": 1,
                        "name": "Вступ",
                        "word_budget": {"min": 40, "max": 120},
                        "teaching_beats": ["Пояснити рід і форму"],
                        "required_terms": ["аспект", "форма"],
                    },
                    {
                        "order": 2,
                        "name": "Підсумок",
                        "word_budget": {"min": 20, "max": 80},
                        "teaching_beats": ["Коротка самоперевірка"],
                        "required_terms": [],
                    },
                ],
            },
            "dialogue_acts": [],
            "activity_obligations": [{"id": "quiz-vid", "type": "quiz"}],
            "vocab_grammar_targets": {"must_introduce": ["аспект", "форма"]},
        },
        {
            "sections": {
                "Вступ": [{"source": "S1", "excerpt": "Рід і форма подаються через зразок."}],
                "Підсумок": [{"source": "S2", "excerpt": "Підсумок стислий і конкретний."}],
            },
            "factual_anchors": [],
        },
    )


def test_phase_suite_switches_templates_and_writer_default(tmp_path: Path, monkeypatch) -> None:
    phases_dir = tmp_path / "phases"
    _write_phase_templates(phases_dir)
    monkeypatch.setattr(v6_build, "PHASES_DIR", phases_dir)

    monkeypatch.delenv("V6_PHASE_SUITE", raising=False)
    monkeypatch.delenv("V6_WRITER_TEMPLATE", raising=False)
    assert v6_build._resolve_writer_template_name("a1") == ("v6-write.md", "default")
    assert v6_build._resolve_phase_template_path("v6-review.md").name == "v6-review.md"

    monkeypatch.setenv("V6_PHASE_SUITE", "uk")
    assert v6_build._resolve_writer_template_name("a1") == ("v6-write-uk.md", "V6_PHASE_SUITE")
    assert v6_build._resolve_phase_template_path("v6-review.md").name == "v6-review-uk.md"

    monkeypatch.setenv("V6_WRITER_TEMPLATE", "v6-write.md")
    assert v6_build._resolve_writer_template_name("a1") == ("v6-write.md", "V6_WRITER_TEMPLATE")


def test_uk_suite_end_to_end_build_uses_uk_templates_and_publishes_ukrainian_only(
    tmp_path: Path,
    monkeypatch,
) -> None:
    seeded = _seed_module_tree(tmp_path)
    level = "a1"
    slug = "uk-phase-suite"
    prompts: dict[str, str] = {}

    def fake_dispatch(prompt: str, *args, **kwargs):
        phase = kwargs.get("phase", "")
        prompts[phase] = prompt
        if phase == "write":
            return True, textwrap.dedent(
                """\
                ## Вступ
                Українська форма показує значення без англійського посередництва.
                Короткий діалог іде від зразка до правила.

                <!-- INJECT_ACTIVITY: quiz-vid -->

                ## Підсумок
                Оберіть правильний вид, відновіть форму й перевірте себе українською.
                """
            )
        if phase == "vocab":
            return True, textwrap.dedent(
                """\
                vocabulary:
                  - word: "аспект"
                    definition: "граматична характеристика дієслова, що показує перебіг або завершеність дії"
                    expression: false
                  - word: "форма"
                    definition: "конкретний граматичний вигляд слова в реченні"
                    expression: false
                """
            )
        if phase == "activities":
            payload = textwrap.dedent(
                """\
                version: "1.0"
                module: uk-phase-suite
                level: a1
                inline:
                  - id: quiz-vid
                    type: quiz
                    instruction: "Оберіть правильний вид дієслова"
                    items:
                      - question: "Я щодня ____ листи."
                        options: ["пишу", "напишу", "написав"]
                        correct: 0
                      - question: "Зараз я ____ вправу до кінця."
                        options: ["роблю", "зроблю", "робив"]
                        correct: 1
                      - question: "Щовечора ми ____ текст уголос."
                        options: ["читаємо", "прочитаємо", "прочитали"]
                        correct: 0
                      - question: "За хвилину вона ____ відповідь."
                        options: ["каже", "скаже", "казала"]
                        correct: 1
                      - question: "Уранці я ____ каву."
                        options: ["п'ю", "вип'ю", "випив"]
                        correct: 0
                      - question: "Після дзвінка ми ____ завдання."
                        options: ["перевіряємо", "перевіримо", "перевірили"]
                        correct: 1
                workbook:
                  - id: fill-form
                    type: fill-in
                    instruction: "Вставте потрібну форму"
                    items:
                      - sentence: "Щодня я ____ українською."
                        answer: "пишу"
                      - sentence: "За хвилину я ____ повідомлення."
                        answer: "напишу"
                      - sentence: "Увечері ми ____ текст."
                        answer: "читаємо"
                      - sentence: "Після обіду ми ____ вправу."
                        answer: "зробимо"
                      - sentence: "Щосуботи вона ____ лист."
                        answer: "пише"
                      - sentence: "Сьогодні ввечері вона ____ лист."
                        answer: "напише"
                """
            )
            return True, ("# padding to clear the activity short-response guard\n" * 12) + payload
        if phase.startswith("review-"):
            dim_id = phase.removeprefix("review-")
            return True, PER_DIM_REVIEW_RAW.format(dim_id=dim_id)
        raise AssertionError(f"Unexpected phase: {phase}")

    monkeypatch.setenv("V6_PHASE_SUITE", "uk")
    monkeypatch.delenv("V6_WRITER_TEMPLATE", raising=False)
    monkeypatch.setattr(v6_build, "PROJECT_ROOT", seeded["project_root"])
    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", seeded["curriculum_root"])
    monkeypatch.setattr(v6_build, "PHASES_DIR", seeded["phases_dir"])
    monkeypatch.setattr(v6_build, "_ensure_contract_artifacts", lambda *args, **kwargs: _contract_artifacts())
    monkeypatch.setattr(v6_build, "_build_vesum_report", lambda *args, **kwargs: "")
    monkeypatch.setattr(v6_build, "_build_monitor_prompt_context", lambda *args, **kwargs: "")
    monkeypatch.setattr(v6_build, "_save_structured_findings_from_parsed", lambda *args, **kwargs: None)
    monkeypatch.setattr(dispatch, "dispatch_agent", fake_dispatch)

    content_path = v6_build.step_write(level, 1, slug, seeded["packet_path"], writer="gemini", no_chunk=True)
    assert content_path is not None
    vocab_path = v6_build.step_vocab(content_path, level, 1, slug, writer="gemini")
    assert vocab_path is not None
    activities_path = v6_build.step_activities(content_path, level, 1, slug, writer="gemini", max_retries=0)
    assert activities_path is not None
    passed, score, _ = v6_build.step_review(content_path, level, 1, slug, writer="gemini", reviewer_override="claude")
    assert passed is True
    assert score == 9.0
    assert v6_build.step_publish(content_path, level, slug) is True

    mdx_path = seeded["project_root"] / "starlight" / "src" / "content" / "docs" / level / f"{slug}.mdx"
    mdx = mdx_path.read_text("utf-8")

    assert "UK-WRITE" in prompts["write"]
    assert "UK-VOCAB" in prompts["vocab"]
    assert "UK-ACTIVITIES" in prompts["activities"]
    # Per-dim reviewer refactor (#1421) replaced the monolithic review
    # template with one per dimension; the suite-UK variant of a monolithic
    # ``v6-review.md`` no longer drives any call. The per-dim base
    # templates are always used regardless of V6_PHASE_SUITE.
    assert "PER-DIM-FACTUAL" in prompts["review-factual"]
    assert "PER-DIM-DIALOGUE" in prompts["review-dialogue"]
    assert "ALL instructions and task stems MUST be in Ukrainian" in prompts["activities"]
    assert "EN-WRITE" not in prompts["write"]
    assert "EN-ACTIVITIES" not in prompts["activities"]

    assert "<TabItem label=\"Урок\">" in mdx
    assert "<TabItem label=\"Словник\">" in mdx
    assert "<TabItem label=\"Зошит\">" in mdx
    assert "граматична характеристика дієслова" in mdx
    assert "Оберіть правильний вид дієслова" in mdx
    assert "Translate into Ukrainian" not in mdx
    assert "aspect)" not in mdx
    assert "form)" not in mdx


def test_main_accepts_writer_and_reviewer_flags_under_uk_suite(
    tmp_path: Path,
    monkeypatch,
) -> None:
    seeded = _seed_module_tree(tmp_path, slug="cli-uk-suite")
    level = "a1"
    slug = "cli-uk-suite"
    content_path = seeded["curriculum_root"] / level / f"{slug}.md"
    content_path.write_text("## Вступ\nУкраїнський текст.\n\n## Підсумок\nКороткий підсумок.\n", "utf-8")

    recorded: dict[str, str | None] = {}

    def fake_convergence(*args, **kwargs):
        recorded["writer"] = kwargs["writer"]
        recorded["reviewer_override"] = kwargs["reviewer_override"]
        review_dir = seeded["curriculum_root"] / level / "review"
        review_dir.mkdir(parents=True, exist_ok=True)
        (review_dir / f"{slug}-review.md").write_text(REVIEW_PASS_RAW, "utf-8")
        return SimpleNamespace(
            terminal="pass",
            rounds=[{"score_overall": 9.0}],
            artifact_path="",
        )

    monkeypatch.setenv("V6_PHASE_SUITE", "uk")
    monkeypatch.setattr(v6_build, "PROJECT_ROOT", seeded["project_root"])
    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", seeded["curriculum_root"])
    monkeypatch.setattr(v6_build, "PHASES_DIR", seeded["phases_dir"])
    monkeypatch.setattr(v6_build, "_ensure_contract_artifacts", lambda *args, **kwargs: _contract_artifacts())
    monkeypatch.setattr(v6_build, "_run_convergence_loop", fake_convergence)
    monkeypatch.setattr(v6_build, "step_review_style", lambda *args, **kwargs: (True, 9.1, "phase: review-style"))
    monkeypatch.setattr(v6_build, "_build_monitor_prompt_context", lambda *args, **kwargs: "")
    monkeypatch.setattr(v6_build, "_clear_terminal_marker", lambda *args, **kwargs: None)
    monkeypatch.setattr(v6_build, "_set_terminal_state", lambda *args, **kwargs: None)
    monkeypatch.setattr(v6_build, "_save_v6_state", lambda *args, **kwargs: None)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "acquire", lambda self: True)
    monkeypatch.setattr(v6_build.ModuleBuildLock, "release", lambda self: None)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "v6_build.py",
            level,
            "1",
            "--step",
            "review",
            "--writer",
            "gemini",
            "--reviewer",
            "claude",
        ],
    )

    assert v6_build.main() is True
    assert recorded == {"writer": "gemini", "reviewer_override": "claude"}
