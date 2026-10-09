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
from scripts.curriculum.arc.loader import ArcPosition, ArcStaleError, load_arc
from scripts.curriculum.learner_state.immersion import ImmersionError, compute_lesson_immersion_band
from scripts.curriculum.validate import codes
from scripts.curriculum.validate.cross import LevelPlans
from scripts.curriculum.validate.pack import Pack, WordRecord, WordStore, load_pack
from scripts.curriculum.validate.report import Report
from scripts.curriculum.validate.review_gates import ReviewGates
from scripts.curriculum.validate.validate import _check_cyrillic

ROOT = Path(__file__).resolve().parents[2]


def registered_quote(quote="model"):
    """Existing publication fixture identity; synthetic print, no language assertion."""
    from tests.curriculum.evidence.test_publication import record

    return record(quote=quote)


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


def test_explicit_orientation_vs_normal_zero():
    positions = load_arc("a1")
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
    changed = tmp_path / "changed.md"
    changed.write_bytes(doc.read_bytes() + b"\nChanged source.\n")
    with pytest.raises(ArcStaleError):
        compute_lesson_immersion_band("a1", 1, 1, 0, doc_path=changed)


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
    pack["texts"] = [registered_quote()]
    expanded, _ = assemble_expanded_document(draft, plan, pack, words, "a1", "unit", 1)
    rendered, _ = _render_urok_markdown(draft, expanded, pack, words)
    assert "model" in rendered
    assert "> — *Захарійчук, «Українська мова. Буквар», 1 клас, ч. 1, 2025, с. 39*" in rendered
    pack["texts"] = []
    with pytest.raises(AssemblerError, match="recap_task_print"):
        assemble_expanded_document(draft, plan, pack, words, "a1", "unit", 1)


@pytest.mark.parametrize("section,record,selection,code", [
    ("texts", {**registered_quote("x" * 860), "source": {"kind": "textbook", "file": "unregistered", "page": 39}},
     "T-001", "publication_right"),
    ("texts", registered_quote("x" * 801), {"ref": "T-001", "words": ["x"]}, "publication_limit"),
    ("texts", {**registered_quote(), "source": {**registered_quote()["source"], "page": None}},
     "T-001", "publication_attribution"),
    ("texts", {"id": "T-001", "text": "model"}, "T-001", "learner_text_not_allowed"),
    ("texts", {**registered_quote(), "text": "sibling"}, "T-001", "learner_text_not_allowed"),
    ("examples", {"id": "EX-001", "text": "model", "items_sample": ["sibling"]},
     "EX-001", "learner_text_not_allowed"),
    ("exercises", {"id": "X-001", "items_sample": ["model"]}, "X-001", "learner_text_not_allowed"),
    ("examples", {"id": "T-001", "text": "model"}, "T-001", "learner_text_not_allowed"),
    ("texts", registered_quote(), {"ref": "T-001", "words": ["models"]}, "recap_task_print"),
    ("texts", registered_quote(), {"ref": "T-001", "words": ["Model"]}, "recap_task_print"),
    ("texts", registered_quote(), {"ref": "T-001", "words": []}, "recap_task_print"),
    ("examples", {"id": "EX-001", "text": ""}, "EX-001", "recap_task_print"),
    ("examples", {"id": "EX-001"}, "EX-001", "recap_task_print"),
    ("examples", {"id": "EX-001", "text": None}, "EX-001", "recap_task_print"),
    ("texts", registered_quote(), "T-999", "recap_task_print"),
])
def test_recap_source_refusals_agree_in_assembly_and_validation(tmp_path, section, record, selection, code):
    import yaml

    draft, plan, _pack, words = assembly_world()
    step = plan["lessons"][0]["steps"][0]
    ref = selection if isinstance(selection, str) else selection["ref"]
    step["evidence"] = [ref]
    step["task"]["learner_reads"] = [selection]
    pack = {section: [record]}
    with pytest.raises(AssemblerError) as exc:
        assemble_expanded_document(draft, plan, pack, words, "a1", "unit", 1)
    assert exc.value.code == code
    path = tmp_path / "pack.yaml"
    path.write_text(yaml.safe_dump(pack))
    gates, closure = gate_world()
    gates.pack = load_pack(path)
    # Aggregate print is deliberately present even for absent refs: it cannot grant permission.
    gates.pack.record_texts[ref] = "model"
    closure["evidence"] = [ref]
    closure["task"]["learner_reads"] = [selection]
    gates.check_practical_recaps()
    assert codes.RECAP_TASK_PRINT in gates.report.codes()


@pytest.mark.parametrize("section,record,selection", [
    ("texts", registered_quote("model"), "T-001"),
    ("texts", registered_quote("model"), {"ref": "T-001", "words": ["model"]}),
    ("texts", registered_quote("x" * 800), "T-001"),
    ("examples", {"id": "EX-001", "text": "model"}, "EX-001"),
    ("examples", {"id": "EX-001", "text": "model"}, {"ref": "EX-001", "words": ["model"]}),
])
def test_permitted_recap_print_uses_raw_metadata_and_mapped_page(tmp_path, section, record, selection):
    import yaml

    draft, plan, _pack, words = assembly_world()
    step = plan["lessons"][0]["steps"][0]
    step["evidence"] = [record["id"]]
    step["task"]["learner_reads"] = [selection]
    pack = {section: [record]}
    expanded, provenance = assemble_expanded_document(draft, plan, pack, words, "a1", "unit", 1)
    rendered, mapping = _render_urok_markdown(draft, expanded, pack, words)
    assert record.get("quote", record.get("text")) in rendered
    assert ("> — *Захарійчук" in rendered) == (section == "texts")
    assert mapping.verify(rendered) == {i: u["text"] for i, u in enumerate(expanded["units"]) if u["tab"] == "urok"}
    span = next(s for s in provenance["spans"] if s["block"] == "recap_print_0")
    assert span["source"] == "record" and span["ref"] == record["id"]
    if section == "texts":
        attribution = next(s for s in provenance["spans"] if s["block"] == "recap_attribution_0")
        assert attribution["source"] == "record" and attribution["ref"] == record["id"]
        assert attribution["role"] == "vesum_exempt" and attribution["record_kind"] == "quote"
        assert attribution["text"] in rendered
    path = tmp_path / "pack.yaml"
    path.write_text(yaml.safe_dump(pack))
    gates, closure = gate_world()
    gates.pack = load_pack(path)
    assert gates.pack.recap_records[record["id"]] == (section, record)
    gates.pack.record_texts.clear()  # Recaps use admitted raw fields, never this aggregate.
    closure["evidence"] = [record["id"]]
    closure["task"]["learner_reads"] = [selection]
    gates.check_practical_recaps()
    assert gates.report.failures == []


@pytest.mark.parametrize("uncited", [False, True])
def test_recap_missing_record_or_citation_refuses(uncited):
    draft, plan, pack, words = assembly_world()
    step = plan["lessons"][0]["steps"][0]
    step["task"]["learner_reads"] = ["T-001"]
    pack["texts"] = [registered_quote()] if uncited else []
    if uncited:
        step["evidence"] = []
    with pytest.raises(AssemblerError, match="recap_task_print"):
        assemble_expanded_document(draft, plan, pack, words, "a1", "unit", 1)
    gates, closure = gate_world()
    if uncited:
        gates.pack.recap_records["T-001"] = ("texts", registered_quote())
        closure["evidence"] = []
    closure["task"]["learner_reads"] = ["T-001"]
    gates.check_practical_recaps()
    assert codes.RECAP_TASK_PRINT in gates.report.codes()


def produced_recap_codes() -> set[str]:
    """Actual outcomes from public fixture mutations, for the validator registry check."""
    produced = set()
    for change in [
        lambda g, s: s.pop("task"),
        lambda g, s: s["task"].update(instruction_en=" "),
        lambda g, s: s["task"].update(instruction_en="Choose 'село'."),
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
    g.pack.recap_records["T-001"] = ("texts", registered_quote(glyph))
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


def test_task_cyrillic_is_allowed_in_print_and_english_scaffolding():
    from scripts.curriculum.validate.validate import _cyrillic_allowed

    assert _cyrillic_allowed(("lessons", 0, "steps", 0, "task", "learner_reads", 0, "words", 0))
    for field in ("context_en", "instruction_en"):
        assert _cyrillic_allowed(("lessons", 0, "steps", 0, "task", field))
    assert _cyrillic_allowed(("lessons", 0, "steps", 0, "task", "success_criteria_en", 0))
    assert not _cyrillic_allowed(("lessons", 0, "steps", 0, "task", "id"))


def test_tracked_a1_selector_and_payload():
    band = compute_lesson_immersion_band("a1", 1, 1, 0)
    payload = compute_immersion_payload("a1", 1, 1, 0)
    assert band.band_key == payload.band_key == "a1-m01-03"
    assert band.advisory_uk_share == payload.advisory_uk_share == (0, 15)
    assert payload.structural_targets == {}


@pytest.mark.parametrize("field", ["context_en", "instruction_en", "success_criteria_en"])
def test_quoted_scaffolding_is_note_only_and_not_inventory_credit(field):
    g, step = gate_world()
    value = "Choose 'село' in this context."
    step["task"][field] = [value] if field == "success_criteria_en" else value
    _check_cyrillic(g.report, g.plan)
    g.check_practical_recaps()
    assert g.report.failures == []
    notes = [n for n in g.report.notes if n.code == codes.RECAP_TASK_QUOTED_UKRAINIAN]
    assert len(notes) == 1 and "село" in notes[0].message
    assert (notes[0].lesson, notes[0].step) == (1, "s2")
    assert "not learner print or inventory evidence" in notes[0].message
    step["uses"]["vocabulary"] = ["W-999"]
    g.check_practical_recaps()
    assert codes.RECAP_TASK_INVENTORY in g.report.codes()


@pytest.mark.parametrize("field", ["id", "context_en", "instruction_en", "success_criteria_en"])
@pytest.mark.parametrize("value", [" ", "123 !", "село"])
def test_scaffolding_requires_latin_letters_and_id_requires_nonempty(field, value):
    g, step = gate_world()
    step["task"][field] = [value] if field == "success_criteria_en" else value
    g.check_practical_recaps()
    if field == "id" and value.strip():
        assert codes.RECAP_TASK_INVALID not in g.report.codes()
        if value == "село":
            _check_cyrillic(g.report, g.plan)
            assert codes.CYRILLIC_IN_DISALLOWED_FIELD in g.report.codes()
    else:
        assert codes.RECAP_TASK_INVALID in g.report.codes()


def test_all_quoted_fields_emit_one_note_with_unique_tokens():
    g, step = gate_world()
    for field in ("context_en", "instruction_en"):
        step["task"][field] = "Say 'село'."
    step["task"]["success_criteria_en"] = ["Say 'село'.", "Choose 'замок'."]
    g.check_practical_recaps()
    notes = [n for n in g.report.notes if n.code == codes.RECAP_TASK_QUOTED_UKRAINIAN]
    assert len(notes) == 1
    assert "['замок', 'село']" in notes[0].message
    assert g.report.failures == []


def test_task_only_practice_counts_as_printed_content():
    g, step = gate_world()
    step["kind"] = "practice"
    g.check_practice_steps_have_content()
    assert g.report.failures == []
    step.pop("task")
    g.check_practice_steps_have_content()
    assert codes.PRACTICE_STEP_EMPTY in g.report.codes()


def quoted_task_world(tmp_path, quote="село", *, slug="sample-slug"):
    """Controlled locked disk fixture from existing captured source facts."""
    import sqlite3

    from scripts.curriculum.evidence import lesson_lock, lock
    from tests.build.test_fresh_assemble import (
        make_draft,
        make_pack,
        make_plan,
        make_plan_lesson,
        make_text_record,
        make_word_record,
        make_words_store,
    )

    capture = json.loads((ROOT / "tests/fixtures/stress-ci.json").read_text())
    captured = next(row for row in capture["forms"] if row["form_unstressed"] == "село")
    analysis = capture["vesum"]["село"][0]
    word = make_word_record(1, "село", forms=[{
        "form": "село", "tags": analysis["tags"], "stress_source": "ulif", "markers": [],
        "learner": True, "stressed": captured["pedagogical_stressed_form"],
    }])
    base_analysis = capture["vesum"]["апостроф"][0]
    base_form = next(row for row in capture["forms"] if row["form_unstressed"] == "апостроф")
    base_word = make_word_record(2, "апостроф", forms=[{
        "form": "апостроф", "tags": base_analysis["tags"], "stress_source": "ulif", "markers": [],
        "learner": True, "stressed": base_form["pedagogical_stressed_form"],
    }])
    untaught_analysis = capture["vesum"]["замок"][0]
    untaught_form = next(row for row in capture["forms"] if row["form_unstressed"] == "замок")
    untaught_word = make_word_record(3, "замок", forms=[{
        "form": "замок", "tags": untaught_analysis["tags"], "stress_source": "ulif", "markers": [],
        "learner": True, "stressed": untaught_form["pedagogical_stressed_form"],
    }])
    words = make_words_store(words=[word, base_word, untaught_word])
    introduction = {
        "id": "s1", "kind": "teach", "teach": "Teach the recorded model.",
        "evidence": ["T-1"], "introduces": {"vocabulary": ["W-1"], "grammar": [], "letters": list("село")},
        "uses": {"vocabulary": [], "grammar": []}, "practice": [],
    }
    closing = {
        "id": "s2", "kind": "recap", "task": task(), "evidence": ["T-1"],
        "uses": {"vocabulary": ["W-1"], "grammar": []}, "practice": [],
    }
    closing["task"]["learner_reads"] = [{"ref": "T-1", "words": ["село"]}]
    closing["task"].update(
        context_en=f"The familiar label is '{quote}'.", instruction_en=f"Choose '{quote}' for this context.",
        success_criteria_en=[f"Say '{quote}' for the appropriate context."],
    )
    lesson = make_plan_lesson(1, [introduction, closing], core_words=[word])
    lesson["closes_with_recap"] = True
    lesson["inventory"]["phonetics"] = {"letters": list("село"), "sounds": []}
    plan = make_plan(lessons=[lesson], module=slug)
    pack = make_pack(texts=[make_text_record(1, "село")])
    plans_dir, evidence_dir = tmp_path / "curriculum/l2-uk-en/lesson-plans/a1", tmp_path / "curriculum/l2-uk-en/evidence/a1"
    plans_dir.mkdir(parents=True)
    evidence_dir.mkdir(parents=True)
    for path, data in [
        (plans_dir / f"{slug}.yaml", plan), (evidence_dir / f"{slug}.yaml", pack),
        (evidence_dir / "_words.yaml", words),
        (evidence_dir / "_base.request.yaml", {"words": [{"lemma": "апостроф", "pos": "noun"}]}),
    ]:
        path.write_bytes(lock.yaml_bytes(data))
        lock.write(path)
    locked = lesson_lock.compute_lesson_lock(
        "a1", slug, plans_dir=plans_dir, evidence_dir=evidence_dir, repo_root=tmp_path,
    )
    lock_path = evidence_dir / f"_state/{slug}/lessons.lock.yaml"
    lock_path.parent.mkdir(parents=True)
    lock.write(lock_path, lock.yaml_bytes(locked))
    draft = make_draft(
        module=f"a1/{slug}",
        steps=[{"id": "s1", "blocks": [{"kind": "prose", "text": "Teach the familiar label.", "explains": ["T-1"]}]},
               {"id": "s2", "blocks": [{"kind": "prose", "text": "Use it in context.", "explains": ["T-1"]}]}],
        lesson_lock_entry_sha256=locked["lessons"][0]["entry_sha256"],
    )
    # A small database of captured VESUM analyses supports outside-state diagnostics.
    vesum_db = tmp_path / "captured-vesum.db"
    with sqlite3.connect(vesum_db) as conn:
        conn.executescript("""
            CREATE TABLE forms_all (id INTEGER PRIMARY KEY, entry_id INTEGER,
                word_form TEXT, lemma TEXT, pos TEXT, tags TEXT, source_comment TEXT, source_location TEXT);
            CREATE TABLE form_markers (form_id INTEGER, marker TEXT, origin TEXT, marker_class TEXT);
            CREATE TABLE vesum_build_metadata (key TEXT, value TEXT);
            CREATE VIEW forms AS SELECT word_form, lemma, pos, tags FROM forms_all;
        """)
        conn.execute("INSERT INTO vesum_build_metadata VALUES (?,?)", (
            "canonical_jsonl_sha256", hashlib.sha256(json.dumps(capture["vesum"]).encode()).hexdigest(),
        ))
        row_id = 0
        for spelling in ("село", "замок"):
            for row in capture["vesum"][spelling]:
                row_id += 1
                conn.execute("INSERT INTO forms_all VALUES (?,?,?,?,?,?,?,?)", (
                    row_id, row_id, spelling, row["lemma"], row["pos"], row["tags"], "", f"capture:{row_id}",
                ))
    (lock_path.parent / "lesson-1.draft.yaml").write_bytes(lock.yaml_bytes(draft))
    return {
        "plan": plan, "pack": pack, "words": words, "draft": draft,
        "plans_dir": plans_dir, "evidence_dir": evidence_dir, "vesum_db": vesum_db,
        "captured": captured,
    }


@pytest.mark.parametrize("quote,taught", [("село", True), ("замок", False)])
def test_quoted_tasks_real_resolution_stress_and_check9(tmp_path, monkeypatch, quote, taught):
    """Real assembly, allowlist, resolver, locks, stress, render and check11 on both cases."""
    import yaml

    from scripts.build.fresh.assemble import check_5_assembly, check_9_stress_and_render
    from scripts.curriculum.evidence.sources import Sources
    from scripts.curriculum.resolver import codes as resolver_codes
    from scripts.curriculum.resolver.inputs import ExpandedDocument
    from scripts.curriculum.resolver.stream import load_allowlist, resolve

    world = quoted_task_world(tmp_path, quote)
    plan, pack, words, draft = (world[key] for key in ("plan", "pack", "words", "draft"))
    plans_dir, evidence_dir, vesum_db, captured = (world[key] for key in (
        "plans_dir", "evidence_dir", "vesum_db", "captured",
    ))
    assembled = check_5_assembly(draft, plan, pack, words, "a1", "sample-slug", 1)
    assert assembled.passed, assembled.to_dict()
    expanded = assembled.artifacts["expanded_doc"]
    instructions = [u for u in expanded["units"] if str(u["block"]).startswith("recap_")
                    and not str(u["block"]).startswith(("recap_print", "recap_attribution"))]
    assert len([u for u in instructions if quote in u["text"]]) == 3
    assert all(u["role"] == "instruction" for u in instructions)
    printed = [u for u in expanded["units"] if str(u["block"]).startswith("recap_print")]
    assert len(printed) == 1 and printed[0]["text"] == "село"
    assert printed[0]["role"] == "record_print"

    with Sources(vesum_db=vesum_db, sources_db=tmp_path / "unused-sources.db") as sources:
        allowlist = load_allowlist(
            "a1", "sample-slug", 1, plans_dir=plans_dir, evidence_dir=evidence_dir,
        )
        assert set(allowlist.records) == {"W-1", "W-2"}
        stream = resolve(ExpandedDocument.from_data(expanded), allowlist, sources)
    quoted_tokens = [t for t in stream.tokens if t["token"] == quote and t["role"] == "instruction"]
    assert len(quoted_tokens) == 3
    from scripts.build.fresh.assemble import assemble_lesson

    closed_sources = []

    class CapturedSources(Sources):
        def close(self):
            super().close()
            closed_sources.append(self)

    monkeypatch.setattr("scripts.build.fresh.assemble.Sources", lambda: CapturedSources(
        vesum_db=vesum_db, sources_db=tmp_path / "unused-sources.db",
    ))
    full = assemble_lesson(
        "a1", "sample-slug", 1, repo_root=tmp_path, draft_dict=draft,
        plan_dict=plan, pack_dict=pack, words_dict=words, plans_dir=plans_dir,
        evidence_dir=evidence_dir, output_dir=tmp_path / "full-state", site_dir=tmp_path / "full-site",
    )
    assert len(closed_sources) == 1
    assert closed_sources[0]._conn is None and closed_sources[0]._receipt_words == {}
    if not taught:
        assert {t["class"] for t in quoted_tokens} == {resolver_codes.LEMMA_OUTSIDE_STATE}
        assert len(stream.failures) == 3
        assert not (tmp_path / "site/1.mdx").exists()
        print("quoted_tasks: assembly=PASS resolver=lemma_outside_state (3) render=not_attempted")
        print("production_assembly_untaught:", json.dumps(full, ensure_ascii=False, default=str))
        assert not full.get("check_9", {}).get("passed"), full
        assert full["failure"]["layer"] == "stream", full
        assert full["failure"]["check"] == 9
        assert full["blocking_tokens"] == [quote] * 3, full
        assert full["blocking_token_classes"] == [resolver_codes.LEMMA_OUTSIDE_STATE] * 3, full
        assert not (tmp_path / "full-site/1.mdx").exists()
        return
    assert full["ok"], full
    assert full["check_5"]["passed"] and full["check_9"]["passed"] and full["check_11"]["passed"], full
    full_mdx = (tmp_path / "full-site/1.mdx").read_text()
    assert full_mdx.count(captured["pedagogical_stressed_form"]) >= 4
    assert "recap_print" in (tmp_path / "full-state/lesson-1.expanded.yaml").read_text()
    print("production_assembly_taught: check5=PASS resolver=resolved check9=PASS check11=PASS MDX=written")
    assert stream.failures == [] and stream.open_tokens() == []
    assert all(t["selected"]["stressed"] == captured["pedagogical_stressed_form"] for t in quoted_tokens)
    rendered = check_9_stress_and_render(
        expanded, draft, plan, pack, words, stream, "a1", "sample-slug", 1,
        provenance_doc=assembled.artifacts["provenance"], repo_root=tmp_path,
        plans_dir=plans_dir, evidence_dir=evidence_dir, output_dir=tmp_path / "state", site_dir=tmp_path / "site",
    )
    assert rendered.passed, rendered.to_dict()
    mdx = (tmp_path / "site/1.mdx").read_text()
    assert mdx.count(captured["pedagogical_stressed_form"]) >= 3
    stressed = yaml.safe_load((tmp_path / "state/lesson-1.stressed.yaml").read_text())
    assert all(captured["pedagogical_stressed_form"] in u["text"] for u in stressed["units"]
               if str(u["block"]).startswith("recap_") and quote in u["text"])
    print("quoted_tasks: assembly=PASS resolver=resolved (3) check9=PASS MDX=written")


def test_quoted_task_scaffolding_through_validate_plan(tmp_path):
    from scripts.curriculum.validate.validate import validate_plan
    from tests.curriculum.test_plan_validate import (
        LEMMA_MAMA,
        LEVEL,
        SLUG,
        build_cyrillic_lemma,
        write_world,
    )

    plan, pack, words = build_cyrillic_lemma()
    closure = plan["lessons"][-1]["steps"][-1]
    for field in ("context_en", "instruction_en"):
        closure["task"][field] = f"Choose '{LEMMA_MAMA}' in this context."
    closure["task"]["success_criteria_en"] = [f"Say '{LEMMA_MAMA}' for this context."]
    # A task-only practice step prints content without a redundant linked activity.
    closure["practice"] = []
    world = write_world(tmp_path, plan, pack, words)
    report = validate_plan(LEVEL, SLUG, plan_path=world.plan_path)
    assert report.ok, report.render_text()
    notes = [n for n in report.notes if n.code == codes.RECAP_TASK_QUOTED_UKRAINIAN]
    assert len(notes) == 1 and LEMMA_MAMA in notes[0].message


@pytest.mark.parametrize("path", [
    ("title",), ("subtitle",), ("focus",), ("objectives", 0),
    ("lessons", 0, "dialogue", "situation"),
    ("lessons", 0, "dialogue", "setting"),
    ("lessons", 0, "dialogue", "target_grammar"),
    ("lessons", 0, "dialogue", "speakers", 0, "name"),
    ("lessons", 0, "dialogue", "places", 0, "name"),
])
def test_cyrillic_prose_permissions_remain_available(path):
    from scripts.curriculum.validate.validate import _cyrillic_allowed

    assert _cyrillic_allowed(path)


@pytest.mark.parametrize("path", [
    ("lessons", 0, "dialogue", "speakers", 0, "id"),
    ("lessons", 0, "dialogue", "places", 0, "id"),
    ("lessons", 0, "steps", 0, "task", "action"),
    ("lessons", 0, "steps", 0, "task", "response_mode"),
])
def test_cyrillic_identifiers_remain_disallowed(path):
    from scripts.curriculum.validate.validate import _cyrillic_allowed

    assert not _cyrillic_allowed(path)


def test_precomputed_band_preserves_a2_structural_payload_and_display():
    band = compute_lesson_immersion_band("a2", 1, 1, 0, waiver="controlled waiver")
    payload = compute_immersion_payload("a2", 1, 1, lesson_band=band)
    assert payload.structural_targets == band.module_structural
    assert "Module structural minimums" in band.render_text()
    assert "Waiver: controlled waiver" in band.render_text()
    from dataclasses import replace

    assert "Not checked:" not in replace(band, not_checked=[]).render_text()


def test_legacy_a2_letter_contract_remains_available_outside_ulp_band():
    rule = config.get_immersion_rule("a2", 25, letter_module=True)
    assert config._ulp_letter_module_contract("a2") in rule


def test_legacy_immersion_hook_text_is_preserved(monkeypatch):
    monkeypatch.setattr(config, "_ulp_practices_rule", lambda *_args: "Controlled compatibility hook.")
    assert config.get_immersion_rule("a2", 25).endswith("\n\nControlled compatibility hook.")
