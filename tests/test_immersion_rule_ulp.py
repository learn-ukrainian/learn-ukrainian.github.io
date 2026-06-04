from __future__ import annotations

import json
from pathlib import Path

import pytest

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
        "em_dash_gloss",
        "dialoguebox_uk_en",
        "section_openers",
    }
    assert "stress_coverage" in report["warnings"]


def test_uk_en_ratio_is_advisory_not_terminal(monkeypatch) -> None:
    """uk_en_ratio must never drive the REVISE verdict.

    A continuous immersion-ratio band is context-dependent; hard-gating on it is
    the mechanics-over-teaching trap the ULP harness fix removes. When every
    structural ULP check passes but the ratio is out of band, the module must
    still PASS, with the ratio surfaced as an advisory warning.
    """
    from scripts.audit import ulp_fidelity_gate as gate

    structural_pass = {"passed": True}
    monkeypatch.setattr(gate, "_stress_coverage_check", lambda _t: dict(structural_pass))
    monkeypatch.setattr(gate, "_em_dash_gloss_check", lambda _t: dict(structural_pass))
    monkeypatch.setattr(gate, "_dialoguebox_check", lambda _t: dict(structural_pass))
    monkeypatch.setattr(gate, "_section_opener_check", lambda _t: dict(structural_pass))
    monkeypatch.setattr(gate, "_ratio_check", lambda _t, _p: {"passed": False, "pct": 99.0})

    report = gate.check_ulp_fidelity(
        "irrelevant",
        {"level": "a1", "sequence": 20, "slug": "fixture"},
        profile="core",
    )

    assert report["verdict"] == "PASS"
    assert report["passed"] is True
    assert report["failed_checks"] == []
    assert "uk_en_ratio" in report["warnings"]


def test_stress_coverage_is_advisory_not_terminal(monkeypatch) -> None:
    from scripts.audit import ulp_fidelity_gate as gate

    structural_pass = {"passed": True}
    monkeypatch.setattr(gate, "_stress_coverage_check", lambda _t: {"passed": False, "coverage": 0.9})
    monkeypatch.setattr(gate, "_em_dash_gloss_check", lambda _t: dict(structural_pass))
    monkeypatch.setattr(gate, "_dialoguebox_check", lambda _t: dict(structural_pass))
    monkeypatch.setattr(gate, "_section_opener_check", lambda _t: dict(structural_pass))
    monkeypatch.setattr(gate, "_ratio_check", lambda _t, _p: dict(structural_pass))

    report = gate.check_ulp_fidelity(
        "irrelevant",
        {"level": "a1", "sequence": 20, "slug": "fixture"},
        profile="core",
    )

    assert report["verdict"] == "PASS"
    assert report["passed"] is True
    assert report["failed_checks"] == []
    assert "stress_coverage" in report["warnings"]


def test_em_dash_gate_is_line_level_for_real_scaffold() -> None:
    module = """# Мій ра́нок

## Мій ра́нок

**Вода́ — water** can stand after **по́тім**: **По́тім вода́**. **Ру́ханка — light exercise** is a short morning item.
Written **-шся** is spoken **[с':а]**: **прокида́єшся** -> **[прокидайес':а]**.

<DialogueBox uk="Я прокида́юся." en="I wake up." />
"""

    report = check_ulp_fidelity(
        module,
        {"level": "a1", "sequence": 20, "slug": "fixture"},
        profile="core",
    )

    assert "em_dash_gloss" not in report["failed_checks"]


def test_em_dash_gate_rejects_distant_punctuation_dash() -> None:
    module = """# Мій ра́нок

## Мій ра́нок

The word **вода́** is useful in the morning because you see it in routines, and this sentence uses a normal aside after many words — not a glossary pair.

<DialogueBox uk="Я п'ю воду́." en="I drink water." />
"""

    report = check_ulp_fidelity(
        module,
        {"level": "a1", "sequence": 20, "slug": "fixture"},
        profile="core",
    )

    assert "em_dash_gloss" in report["failed_checks"]


# Loads the live Stanza Ukrainian model (run_ulp_fidelity_with_correction →
# run_stress_annotation). Non-hermetic: the model download flakes the md5 check
# in parallel CI. Marked `slow` so the required pytest selection
# (`-k "not slow"`) excludes it; it still runs in the slow/nightly path.
@pytest.mark.slow
def test_ulp_fidelity_correction_reruns_stress_and_gate(tmp_path: Path) -> None:
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text(
        "\n".join(
            [
                "level: a1",
                "sequence: 20",
                "slug: fixture",
                "module: 20",
                "title: Fixture",
                "subtitle: ULP fixture",
                "word_target: 300",
                "content_outline:",
                "  - section: opener",
                "    words: 300",
                "    points:",
                "      - fixture",
                "references:",
                "  - title: Fixture",
                "    notes: synthetic test plan",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (module_dir / "module.md").write_text(
        """# Мій ра́нок

## Підсумок

Your clean morning sentence uses **я прокида́юся** before breakfast.

<DialogueBox uk="Я прокида́юся." en="I wake up." />
""",
        encoding="utf-8",
    )
    (module_dir / "vocabulary.yaml").write_text("[]\n", encoding="utf-8")

    corrected = """```module.md
# Мій ра́нок

## Підсумок

**Я прокида́юся ра́но** — I wake up early. This is the clean morning model.

<DialogueBox uk="Я прокида́юся ра́но." en="I wake up early." />
```"""

    def corrector(_context: linear_pipeline.CorrectionContext) -> str:
        return corrected

    report = linear_pipeline.run_ulp_fidelity_with_correction(
        module_dir,
        plan_path,
        profile="core",
        writer="codex-tools",
        writer_corrector=corrector,
    )

    assert report["passed"] is True
    assert (module_dir / "stress_annotation.json").exists()
    correction = json.loads((module_dir / "ulp_fidelity_correction_r1.json").read_text(encoding="utf-8"))
    assert correction["correction"]["applied"] == "module_patch"
    assert correction["after"]["passed"] is True


# Loads the live Stanza Ukrainian model (run_stress_annotation). See note above.
@pytest.mark.slow
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
