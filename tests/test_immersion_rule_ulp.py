from __future__ import annotations

from pathlib import Path

from scripts import config
from scripts.audit.ulp_fidelity_gate import _UK_WORD_RE, check_ulp_fidelity
from scripts.build import linear_pipeline, v7_build
from scripts.pipeline.stress_annotator import STRESS_MARK

ULP_KEYWORDS = (
    "em-dash",
    "DialogueBox",
    "stress marks",
    "Ukrainian-first",
    "named first-person teacher persona",
)


def _keyword_hits(rule: str) -> int:
    lowered = rule.lower()
    return sum(1 for keyword in ULP_KEYWORDS if keyword.lower() in lowered)


def test_a1_letter_module_gets_ulp_practices() -> None:
    rule = config.get_immersion_rule("a1", 4)

    assert "ULP Presentation Pattern" in rule
    assert _keyword_hits(rule) >= 2


def test_a1_m20_gets_ulp_practices() -> None:
    rule = config.get_immersion_rule("a1", 20)

    assert "ULP Presentation Pattern" in rule
    assert _keyword_hits(rule) >= 2


def test_a1_late_module_gets_s1_ulp_practices() -> None:
    rule = config.get_immersion_rule("a1", 50)

    assert "ULP Presentation Pattern" in rule
    assert _keyword_hits(rule) >= 2


def test_c1_module_does_not_get_a1_ulp_practices() -> None:
    rule = config.get_immersion_rule("c1", 50)

    assert "ULP Presentation Pattern" not in rule
    assert _keyword_hits(rule) == 0


def test_ulp_word_regex_does_not_absorb_quoting_marks() -> None:
    assert [match.group(1) for match in _UK_WORD_RE.finditer("'слово' сім'я")] == [
        "слово",
        "сім'я",
    ]


def test_ulp_fidelity_gate_passes_ukrainian_first_fixture() -> None:
    module = """# Мій ра́нок

## Ра́нок

Я прокида́юся — I wake up. Мене́ зва́ти Оле́на. Я кажу́: до́брий ра́нок. English support.

<DialogueBox uk="До́брий ра́нок, Оле́но." en="Good morning, Olena." />
<DialogueBox uk="Я прокида́юся і пи́шу пові́льно." en="I wake up and write slowly." />

## Ді́я

Прокида́юся — I wake up. Пи́шу — I write. Чита́ю — I read. Це мій ма́лий ритм. Short support.
"""

    report = check_ulp_fidelity(
        module,
        {"level": "a1", "sequence": 20, "slug": "fixture"},
        profile="core",
    )

    assert report["passed"] is True
    assert report["verdict"] == "PASS"
    assert report["failed_checks"] == []


def test_ulp_fidelity_gate_revises_grammar_translation_fixture() -> None:
    module = """# Morning verbs

## Morning verbs

Your morning story needs a few verbs before it can move.
The word прокидаюся means I wake up. A reflexive verb is a verb that points back to the subject.

<DialogueBox uk="Я прокидаюся and I wake up." en="I wake up." />
"""

    report = check_ulp_fidelity(
        module,
        {"level": "a1", "sequence": 20, "slug": "fixture"},
        profile="core",
    )

    assert report["passed"] is False
    assert report["verdict"] == "REVISE"
    assert set(report["failed_checks"]) >= {
        "stress_coverage",
        "em_dash_gloss",
        "dialoguebox_uk_en",
        "section_openers",
    }


def test_linear_pipeline_stress_annotation_marks_module_and_vocabulary(
    tmp_path: Path,
) -> None:
    (tmp_path / "module.md").write_text(
        'Моя мама читає.\n<DialogueBox uk="Моя мама пише." en="My mother writes." />\n',
        encoding="utf-8",
    )
    (tmp_path / "vocabulary.yaml").write_text(
        "- word: мама\n  translation: mother\n  example_uk: Моя мама читає.\n",
        encoding="utf-8",
    )

    first = linear_pipeline.run_stress_annotation(tmp_path)
    second = linear_pipeline.run_stress_annotation(tmp_path)

    assert first["passed"] is True
    assert first["total_added"] > 0
    assert second["total_added"] == 0
    assert STRESS_MARK in (tmp_path / "module.md").read_text(encoding="utf-8")
    assert STRESS_MARK in (tmp_path / "vocabulary.yaml").read_text(encoding="utf-8")


def test_v7_resume_artifact_passes_for_stress_and_ulp_gate(tmp_path: Path) -> None:
    (tmp_path / "module.md").write_text("Моя мама читає.\n", encoding="utf-8")
    (tmp_path / "vocabulary.yaml").write_text("[]\n", encoding="utf-8")
    linear_pipeline.write_json(
        tmp_path / "stress_annotation.json",
        {"passed": True, "phase": "stress_annotation"},
    )
    linear_pipeline.write_json(
        tmp_path / "ulp_fidelity_gate.json",
        {"passed": True, "verdict": "PASS"},
    )

    assert v7_build._phase_artifact_passes(tmp_path, "stress_annotation") is True
    assert v7_build._phase_artifact_passes(tmp_path, "ulp_fidelity_gate") is True

    linear_pipeline.write_json(
        tmp_path / "ulp_fidelity_gate.json",
        {"passed": False, "verdict": "REVISE"},
    )
    assert v7_build._phase_artifact_passes(tmp_path, "ulp_fidelity_gate") is False
