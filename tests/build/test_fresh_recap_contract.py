"""Public synthetic contract tests for #10105; independent held-out cases stay unseen."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts import config
from scripts.build.fresh.assemble import AssemblerError, _render_urok_markdown, assemble_expanded_document
from scripts.build.fresh.immersion import compute_immersion_payload
from scripts.curriculum.arc.generate_arc import render_arc_yaml
from scripts.curriculum.arc.loader import ArcPosition, ArcStaleError, load_arc
from scripts.curriculum.learner_state.immersion import ImmersionError, compute_lesson_immersion_band
from scripts.curriculum.validate import codes
from scripts.curriculum.validate.cross import LevelPlans
from scripts.curriculum.validate.pack import Pack, WordRecord, WordStore
from scripts.curriculum.validate.report import Report
from scripts.curriculum.validate.review_gates import ReviewGates
from scripts.curriculum.validate.validate import _check_cyrillic

ROOT = Path(__file__).resolve().parents[2]


def task(task_id: str = "practical-closure") -> dict:
    return {
        "id": task_id,
        "action": "select_for_context",
        "context_en": "A new familiar situation.",
        "instruction_en": "Select and use a taught model that fits the situation.",
        "response_mode": "selection",
        "success_criteria_en": ["Select a model suited to the context."],
        "learner_reads": [],
    }


def generated_a1_arc(tmp_path: Path) -> list[ArcPosition]:
    """Generate a current isolated arc; never refresh tracked migration inputs."""
    doc = ROOT / "docs/epics/fresh-build-a1-arc.md"
    arc = tmp_path / "_arc.yaml"
    arc.write_text(render_arc_yaml(doc.read_bytes(), "docs/epics/fresh-build-a1-arc.md"), encoding="utf-8")
    return load_arc("a1", arc_path=arc, doc_path=doc)


@pytest.mark.parametrize(
    "count,key,share",
    [
        (0, "a1-m01-03", (0, 15)),
        (24, "a1-m01-03", (0, 15)),
        (25, "a1-m04-06", (10, 20)),
        (59, "a1-m04-06", (10, 20)),
        (60, "a1-m07-14", (15, 30)),
        (139, "a1-m07-14", (15, 30)),
        (140, "a1-m15-24", (25, 40)),
        (241, "a1-m15-24", (25, 40)),
        (242, "a1-m25-34", (35, 50)),
        (399, "a1-m25-34", (35, 50)),
        (400, "a1-m35-54", (45, 60)),
        (599, "a1-m35-54", (45, 60)),
        (600, "a1-m55+", (55, 70)),
    ],
)
def test_boundaries_renumber_and_split_invariance(count, key, share):
    for position, lesson in [(1, 1), (40, 1), (2, 8)]:
        payload = compute_immersion_payload("a1", position, lesson, count, arc_loader=lambda _: [])
        assert payload.band_key == key and payload.advisory_uk_share == share
        assert payload.structural_targets == {}
        assert payload.not_checked == ["lesson_structural_minimums_not_calibrated"]


@pytest.mark.parametrize("count", [None, True, False, -1, 1.5, "0", [], {}])
def test_invalid_counts_fail_closed(count):
    with pytest.raises(ImmersionError) as exc:
        compute_lesson_immersion_band("a1", 1, 1, count, arc_loader=lambda _: [])
    assert exc.value.code == ("cumulative_core_count_missing" if count is None else "cumulative_core_count_invalid")


def test_explicit_orientation_vs_normal_zero(tmp_path):
    positions = generated_a1_arc(tmp_path)
    original = positions[0]
    from dataclasses import replace

    declared = replace(original, position=17, band_key="a1-orientation")
    payload = compute_immersion_payload("a1", 17, 1, 0, arc_loader=lambda _: [declared])
    assert payload.band_key == "a1-orientation" and payload.to_dict()["advisory_uk_share"] is None
    assert payload.permitted_languages["narration"] == ("en",)
    assert payload.structural_targets == {}
    band = compute_lesson_immersion_band("a1", 17, 1, 0, arc_loader=lambda _: [declared])
    assert band.to_dict()["advisory_uk_share"] is None and "No advisory share" in band.render_text()
    assert compute_immersion_payload("a1", 1, 1, 0, arc_loader=lambda _: [declared]).band_key == "a1-m01-03"
    # Cumulative prior vocabulary is not a declaration of new words; the plan gate checks additions.
    assert compute_immersion_payload("a1", 17, 1, 1, arc_loader=lambda _: [declared]).advisory_uk_share is None
    for pos in [-5, 0, 1, 17, 10001]:
        assert config.compute_immersion_band("a1", pos)["key"] != "a1-orientation"


def test_stale_arc_is_rejected(tmp_path):
    doc = ROOT / "docs/epics/fresh-build-a1-arc.md"
    generated_a1_arc(tmp_path)
    changed = tmp_path / "changed.md"
    changed.write_bytes(doc.read_bytes() + b"\nChanged source.\n")
    with pytest.raises(ArcStaleError):
        compute_lesson_immersion_band("a1", 1, 1, 0, arc_path=tmp_path / "_arc.yaml", doc_path=changed)


def gate_world(*, embedded=False, early_count=0, orientation=False):
    intro = {
        "id": "s1",
        "kind": "teach",
        "introduces": {"letters": [], "vocabulary": ["W-001"], "grammar": ["G-a1-001"]},
    }
    closure = {
        "id": "s2",
        "kind": "recap",
        "task": task(),
        "uses": {"vocabulary": ["W-001"], "grammar": ["G-a1-001"]},
        "evidence": ["T-001"],
        "practice": [],
    }
    inv = {"grammar": [], "vocabulary": {"core": [], "incidental": [], "recycled": []}}
    lesson = {
        "n": 1,
        "kind": "teach" if embedded else "recap",
        "inventory": copy.deepcopy(inv),
        "steps": [intro, closure] if embedded else [closure],
        "activities": [],
    }
    if embedded:
        lesson["closes_with_recap"] = True
        lesson["inventory"]["vocabulary"]["core"] = [{"evidence": "W-001"}]
    plan = {"level": "a1", "slug": "unit", "arc_ref": {"position": 1}, "lessons": [lesson]}
    records = {"W-001": WordRecord("W-001", "model", frozenset())}
    prior = {
        "lessons": [
            {
                "inventory": {"vocabulary": {"core": [{"evidence": f"W-{i + 100:03d}"} for i in range(early_count)]}},
                "steps": [],
            }
        ]
    }
    gates = ReviewGates(
        Report("a1", "unit"),
        plan,
        "a1",
        WordStore(Path("words"), records),
        [],
        LevelPlans(),
        Path("words"),
        pack=Pack(Path("pack"), ids=frozenset({"T-001"})),
    )
    gates.__dict__["_base_layer"] = (frozenset(), "")
    gates.__dict__["_earlier_introduced"] = ({"W-001"} if not embedded else set(), "")
    if not embedded:
        # Genuine earlier teaching supplies the grammar; normal synthetic position is 2.
        plan["arc_ref"]["position"] = 2
        prior["lessons"][0]["steps"] = [{"introduces": {"grammar": ["G-a1-001"], "vocabulary": ["W-001"]}}]
        gates.level_plans.by_position[1] = ("prior", prior, Path("prior"))
    if orientation:
        gates.arc = [
            ArcPosition(
                plan["arc_ref"]["position"], "unit", 1, "job", None, "phase", "skill", [], [], band_key="a1-orientation"
            )
        ]
    return gates, closure


@pytest.mark.parametrize("embedded", [False, True])
def test_practical_and_embedded_availability(embedded):
    gates, closure = gate_world(embedded=embedded)
    gates.check_practical_recaps()
    assert gates.report.failures == []
    closure["uses"]["vocabulary"] = ["W-999"]
    gates.check_practical_recaps()
    assert codes.RECAP_TASK_INVENTORY in gates.report.codes()


@pytest.mark.parametrize(
    "mutation,code",
    [
        (lambda g, s: s.pop("task"), codes.A1_RECAP_MIGRATION_REQUIRED),
        (lambda g, s: s["task"].update(instruction_en=" "), codes.RECAP_TASK_INVALID),
        (lambda g, s: s.update(introduces={"vocabulary": ["W-009"]}), codes.RECAP_TASK_INVENTORY),
        (lambda g, s: s["uses"].update(grammar=["G-a1-999"]), codes.RECAP_TASK_INVENTORY),
        (lambda g, s: s.update(evidence=[]), codes.RECAP_TASK_INVENTORY),
        (lambda g, s: g.plan["lessons"][0]["steps"].append({"id": "s3", "kind": "practice"}), codes.RECAP_TASK_ORDER),
        (lambda g, s: s["task"].update(learner_reads=["T-999"]), codes.RECAP_TASK_PRINT),
    ],
)
def test_structural_failures(mutation, code):
    gates, step = gate_world()
    mutation(gates, step)
    gates.check_practical_recaps()
    assert code in gates.report.codes()


def test_embedded_later_teaching_cannot_supply_recap():
    gates, _step = gate_world(embedded=True)
    gates.plan["lessons"][0]["steps"].reverse()
    gates.check_practical_recaps()
    assert {codes.RECAP_TASK_ORDER, codes.RECAP_TASK_INVENTORY} <= gates.report.codes()


def test_early_definition_and_later_scoping():
    for count, rejected in [(0, True), (400, False)]:
        gates, step = gate_world(early_count=count)
        step["practice"] = ["a1"]
        gates.plan["lessons"][0]["activities"] = [{"id": "a1", "focus": "kind: comprehension; host: {kind: dialogue}"}]
        gates.check_practical_recaps()
        assert (codes.RECAP_TASK_INVALID in gates.report.codes()) is rejected


def test_orientation_introductions_rejected():
    gates, _ = gate_world(embedded=True, orientation=True)
    gates.check_practical_recaps()
    assert codes.ORIENTATION_CORE_WORDS in gates.report.codes()


def test_task_schema_and_english_fields():
    schema = json.loads((ROOT / "schemas/module-plan-v2.schema.json").read_text())
    validator = Draft202012Validator({"$ref": "#/$defs/recapTask", "$defs": schema["$defs"]})
    assert not list(validator.iter_errors(task()))
    for mutation in [
        dict(action="copy"),
        dict(action="question_only"),
        dict(decision="pretend"),
        dict(success_criteria_en=[]),
        dict(instruction_en=""),
    ]:
        assert list(validator.iter_errors(task() | mutation))
    g, _step = gate_world()
    _check_cyrillic(g.report, g.plan)
    assert g.report.failures == []


def assembly_world():
    g, _step = gate_world()
    plan = g.plan
    plan["lessons"][0]["steps"] = [_step]
    draft = {
        "status": "ok",
        "steps": [{"id": "s2", "blocks": [{"kind": "prose", "text": "Support first."}]}],
        "activities": [],
    }
    return draft, plan, {"texts": [{"id": "T-001", "quote": "model"}]}, {"words": []}


def test_assembler_prints_plan_without_draft_echo():
    draft, plan, pack, words = assembly_world()
    expanded, prov = assemble_expanded_document(draft, plan, pack, words, "a1", "unit", 1)
    rendered, mapping = _render_urok_markdown(draft, expanded, pack, words)
    assert rendered.index("Support first.") < rendered.index(task()["instruction_en"])
    assert all(t in rendered for t in [task()["context_en"], *task()["success_criteria_en"], "Response: selection"])
    assert mapping.verify(rendered) == {
        i: unit["text"] for i, unit in enumerate(expanded["units"]) if unit["tab"] == "urok"
    }
    from scripts.build.fresh.assemble import get_provenance_validator

    get_provenance_validator().validate(prov)
    draft["steps"] = []
    with pytest.raises(AssemblerError, match="recap_task_order"):
        assemble_expanded_document(draft, plan, pack, words, "a1", "unit", 1)


def test_assembler_permitted_source_print():
    draft, plan, pack, words = assembly_world()
    plan["lessons"][0]["steps"][0]["task"]["learner_reads"] = [{"ref": "T-001", "words": ["model"]}]
    pack["texts"] = [{"id": "T-001", "quote": "model"}]
    expanded, _ = assemble_expanded_document(draft, plan, pack, words, "a1", "unit", 1)
    rendered, _ = _render_urok_markdown(draft, expanded, pack, words)
    assert "model" in rendered
    pack["texts"] = []
    with pytest.raises(AssemblerError, match="recap_task_print"):
        assemble_expanded_document(draft, plan, pack, words, "a1", "unit", 1)


def produced_recap_codes() -> set[str]:
    """Actual outcomes from public fixture mutations, for the validator registry check."""
    produced = set()
    for change in [
        lambda g, s: s.pop("task"),
        lambda g, s: s["task"].update(instruction_en=" "),
        lambda g, s: s["uses"].update(vocabulary=["W-999"]),
        lambda g, s: g.plan["lessons"][0]["steps"].append({"id": "s3", "kind": "practice"}),
        lambda g, s: s["task"].update(learner_reads=["T-999"]),
    ]:
        g, s = gate_world()
        change(g, s)
        g.check_practical_recaps()
        produced |= g.report.codes()
    g, _ = gate_world(embedded=True, orientation=True)
    g.check_practical_recaps()
    return produced | g.report.codes()


def test_a2plus_and_legacy_structural_pins():
    # Base 23ecf8c4620f06cec6f3bc402a8934f4c30be6f3, which includes merged #10104.
    pins = {
        "a2": "a52b41d69e6774682d98165118ac7454e6b51256b6952d3cfa426499acb95cce",
        "b1": "acd993e20acdc7e921ebd624ef45a76496ed46fd5a457f407c71c9bb1f2f0b88",
        "default": "db56f20e861768d7062b25e19e2a783cd845a8cb59cc11e6f7b7ab25c0a22b42",
    }
    for family, pin in pins.items():
        assert hashlib.sha256(repr(config.IMMERSION_POLICIES[family]).encode()).hexdigest() == pin
    assert (
        hashlib.sha256((ROOT / "schemas/lesson-draft-v1.schema.json").read_bytes()).hexdigest()
        == "d4dfd713254a0361736de036f65fe9227e63268651514c5fcfe9bd3b00f46ccc"
    )


def test_recap_print_decodability_and_before_step_inventory():
    g, s = gate_world(embedded=True)
    # Synthetic glyph fixture, no claim about Ukrainian words.
    glyph = chr(0x0430)
    g.pack.record_texts["T-001"] = glyph
    s["task"]["learner_reads"] = [{"ref": "T-001", "words": [glyph]}]
    g.__dict__["taught_before"] = {1: set()}
    g.check_practical_recaps()
    assert codes.RECAP_TASK_PRINT in g.report.codes()
    g.report.failures.clear()
    g.plan["lessons"][0]["steps"][0]["introduces"]["letters"] = [glyph]
    g.check_practical_recaps()
    assert g.report.failures == []
    g.report.failures.clear()
    s["task"]["learner_reads"][0]["words"] = [chr(0x0431)]
    g.check_practical_recaps()
    assert codes.RECAP_TASK_PRINT in g.report.codes()


def test_duplicate_task_and_a2_gate_exclusion():
    g, _step = gate_world()
    second = copy.deepcopy(g.plan["lessons"][0])
    second["n"] = 2
    g.plan["lessons"].append(second)
    g.check_practical_recaps()
    assert codes.RECAP_TASK_ORDER in g.report.codes()
    g.report.failures.clear()
    g.level = "a2"
    g.check_practical_recaps()
    assert g.report.failures == []


@pytest.mark.parametrize("count", [True, False, -1, 1.5, "0", {}])
def test_config_a1_invalid_counts_and_non_a1_invariance(count):
    with pytest.raises(ValueError, match="cumulative_core_count_invalid"):
        config.compute_immersion_band("a1", 1, {"cumulative_vocabulary": count})
    for level in ["a2", "b1", "c1"]:
        assert config.compute_immersion_band(
            level, 1, {"cumulative_vocabulary": count}
        ) == config.compute_immersion_band(level, 1, {"cumulative_vocabulary": 0})


def test_task_print_is_the_only_cyrillic_task_field():
    from scripts.curriculum.validate.validate import _cyrillic_allowed

    assert _cyrillic_allowed(("lessons", 0, "steps", 0, "task", "learner_reads", 0, "words", 0))
    assert not _cyrillic_allowed(("lessons", 0, "steps", 0, "task", "instruction_en"))
