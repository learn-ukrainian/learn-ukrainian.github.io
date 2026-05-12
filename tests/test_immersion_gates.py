from __future__ import annotations

from scripts.build import linear_pipeline
from scripts.build.linear_pipeline import (
    _advisory_immersion_pct,
    _component_density_gate,
    _l2_exposure_floor_gate,
    _long_uk_ceiling_gate,
)
from scripts.config import IMMERSION_POLICIES

A1_PLAN = {"level": "a1", "sequence": 20}
A1_EARLY_PLAN = {"level": "a1", "sequence": 1}
A2_RAMP_PLAN = {"level": "a2", "sequence": 4}


def _happy_path_text() -> str:
    return "\n".join(
        [
            "English setup explains the pattern before learners practice.",
            "",
            "<RuleBox>Use the reflexive ending after the verb. Keep the form short.</RuleBox>",
            "",
            "<DialogueBox",
            "  lines={[",
            '    { speaker: "Ліна", text: "Я прокидаюся рано." },',
            '    { speaker: "Марко", text: "Я снідаю вдома." },',
            "  ]}",
            "/>",
            "",
            "| Українською | English |",
            "|---|---|",
            "| прокидаюся | I wake up |",
            "| вмиваюся | I wash up |",
            "| одягаюся | I get dressed |",
            "| снідаю | I eat breakfast |",
            "| вдома | at home |",
            "",
            "- **Я прокидаюся рано.** — I wake up early.",
            "- **Я вмиваюся швидко.** — I wash up quickly.",
            "- **Я одягаюся вдома.** — I get dressed at home.",
            "- **Я снідаю вдома.** — I eat breakfast at home.",
            "",
            "<!-- INJECT_ACTIVITY: act-1 -->",
        ]
    )


def test_advisory_pct_always_passes() -> None:
    result = _advisory_immersion_pct("Only English scaffolding appears here.", A1_EARLY_PLAN)

    assert result["passed"] is True
    assert result["pct"] == 0.0
    assert result["min_pct"] == 5
    assert result["max_pct"] == 25
    assert result["policy"] == "a1-m01-03"


def test_structural_gates_pass_happy_path_fixture() -> None:
    text = _happy_path_text()

    assert _l2_exposure_floor_gate(text, A1_PLAN)["passed"] is True
    assert _long_uk_ceiling_gate(text, A1_PLAN)["passed"] is True
    assert _component_density_gate(text, A1_PLAN)["passed"] is True


def test_l2_exposure_floor_pass() -> None:
    result = _l2_exposure_floor_gate(_happy_path_text(), A1_PLAN)

    assert result["passed"] is True
    assert result["observed"]["vocab_entries"] >= result["required"]["vocab_entries"]


def test_l2_exposure_floor_fail_dialogue_lines() -> None:
    text = "\n".join(
        [
            "| Українською | English |",
            "|---|---|",
            "| слово | word |",
            "| фраза | phrase |",
            "| ранок | morning |",
            "| дім | home |",
            "| кава | coffee |",
            "| вода | water |",
            "- **Я читаю.** — I read.",
            "- **Я пишу.** — I write.",
            "- **Я слухаю.** — I listen.",
            "- **Я говорю.** — I speak.",
            "- **Я повторюю.** — I repeat.",
            "<!-- INJECT_ACTIVITY: act-1 -->",
        ]
    )

    result = _l2_exposure_floor_gate(text, A2_RAMP_PLAN)

    assert result["passed"] is False
    assert "too_few_uk_dialogue_lines" in result["reason"]


def test_l2_exposure_floor_fail_vocab_entries() -> None:
    text = "\n".join(
        [
            "> **Ліна:** Я читаю. (I read.)",
            "> **Марко:** Я пишу. (I write.)",
            "> **Оля:** Я слухаю. (I listen.)",
            "- **Я читаю.** — I read.",
            "- **Я пишу.** — I write.",
            "- **Я слухаю.** — I listen.",
            "- **Я говорю.** — I speak.",
            "- **Я повторюю.** — I repeat.",
            "<!-- INJECT_ACTIVITY: act-1 -->",
        ]
    )

    result = _l2_exposure_floor_gate(text, A2_RAMP_PLAN)

    assert result["passed"] is False
    assert "too_few_vocab_entries" in result["reason"]


def test_long_uk_ceiling_pass() -> None:
    text = "Слово ранок (morning) коротке. Фраза вдома (at home) теж коротка."

    result = _long_uk_ceiling_gate(text, A1_EARLY_PLAN)

    assert result["passed"] is True


def test_long_uk_ceiling_fail() -> None:
    text = " ".join(
        [
            "Український",
            "студент",
            "повільно",
            "прокидається",
            "вмивається",
            "одягається",
            "снідає",
            "планує",
            "повторює",
            "записує",
            "читає",
            "слухає",
            "практикує",
            "розповідає",
            "запитує",
            "відповідає",
        ]
    )

    result = _long_uk_ceiling_gate(text, A1_EARLY_PLAN)

    assert result["passed"] is False
    assert result["reason"] == "long_uk_without_gloss"
    assert result["offending_runs"][0].startswith("Український студент")


def test_component_density_dialoguebox_pass() -> None:
    result = _component_density_gate('<DialogueBox text="Привіт!" />', A1_EARLY_PLAN)

    assert result["passed"] is True


def test_component_density_rulebox_fail_at_a1_early() -> None:
    text = (
        "<RuleBox>Український студент читає пише слухає повторює "
        "говорить відповідає сьогодні.</RuleBox>"
    )

    result = _component_density_gate(text, A1_EARLY_PLAN)

    assert result["passed"] is False
    assert result["reason"] == "component_density_mismatch"
    assert result["mismatches"][0]["component_tag"] == "RuleBox"


def test_immersion_policies_schema() -> None:
    required_keys = {
        "advisory_pct_min",
        "advisory_pct_max",
        "min_uk_dialogue_lines",
        "min_vocab_entries",
        "min_uk_example_sentences",
        "min_uk_tab3_activities",
        "max_unsupported_uk_words",
        "support_proximity",
        "required_components",
    }
    min_fields = {
        "min_uk_dialogue_lines",
        "min_vocab_entries",
        "min_uk_example_sentences",
        "min_uk_tab3_activities",
    }

    for bands in IMMERSION_POLICIES.values():
        for band in bands:
            assert required_keys <= set(band)
            assert "min_pct" not in band
            assert "max_pct" not in band
            assert isinstance(band["advisory_pct_min"], int)
            assert isinstance(band["advisory_pct_max"], int)
            for field in min_fields:
                assert isinstance(band[field], int)
            assert isinstance(band["required_components"], dict)


def test_old_immersion_gate_removed() -> None:
    assert not hasattr(linear_pipeline, "_immersion_gate")
    assert hasattr(linear_pipeline, "_advisory_immersion_pct")
