"""V7.2 Step 5 — prompt_generator composition + opt-in wiring tests.

Covers:
- per-slot composition (writer = preamble+body+shared; reviewer = rubric+shared)
- topo / slot order preserved from the loader
- ``shared.contract`` rules emitted into BOTH writer and reviewer blocks
- ``#R-*`` markers restored (registry bodies don't carry them)
- ONE Obligation Checklist, single-sourced across writer + reviewer + the
  ``wiki_coverage_gate`` extraction
- the ``--use-generator`` opt-in flag: OFF → byte-identical legacy dicts,
  ON → registry-composed prompts with full ``#R-*`` parity for m20
- level edge: A1-gated rules present in BOTH prompts at a1, absent at b1
"""

from __future__ import annotations

import re

import pytest

from scripts.build import linear_pipeline as lp
from scripts.build import prompt_generator as pg
from scripts.build.phases.implementation_map import seed_implementation_map
from scripts.build.universal_rules_registry import load_applicable_rules

RULE_RE = re.compile(r"#R-[A-Z0-9-]+")
# Emission order is read from the one rule_id comment the generator prepends per
# rule — NOT from a bare #R-* scan, because rule BODIES cross-reference other
# rule ids (e.g. R-RENDERER-CHARTER names #R-VOICE-META in prose).
MARKER_COMMENT_RE = re.compile(r"<!-- rule_id: (#R-[A-Z0-9-]+) -->")
BRACE_TOKEN_RE = re.compile(r"\{([A-Z][A-Z0-9_]*)\}")

# A1-gated rules promoted to shared.contract — present in BOTH prompts at a1,
# dropped at b1 (mirrors test_audience_language_a1_does_not_apply_at_b1).
A1_ONLY_RULES = {
    "#R-AUDIENCE-LANGUAGE-A1",
    "#R-GRAMMAR-TERMS-A1",
    "#R-NO-CHILDREN-PRIMARY-QUOTES",
    "#R-PROSE-FLOOR-A1",
    "#R-SINGLE-VOICE-A1",
}


def _rule_ids(text: str) -> set[str]:
    return set(RULE_RE.findall(text))


def _emission_order(text: str) -> list[str]:
    """Rule ids in emission order, from the generator's rule_id comment markers."""
    return MARKER_COMMENT_RE.findall(text)


def _inserted_obligation_checklist(prompt: str) -> str:
    start = prompt.index("**Coverage rule**:")
    end = prompt.index("\n\n## Implementation Map Contract", start)
    return prompt[start:end].strip()


@pytest.fixture(scope="module")
def m20():
    """Real a1/my-morning plan + manifest + implementation map fixtures."""
    level, slug = "a1", "my-morning"
    plan_path = lp.plan_path_for(level, slug)
    plan = lp.plan_check(plan_path)
    plan_content = plan_path.read_text(encoding="utf-8")
    wiki_manifest = lp.build_wiki_manifest_data(level=level, slug=slug, plan=plan)
    implementation_map = seed_implementation_map(wiki_manifest, plan=plan)
    return {
        "level": level,
        "slug": slug,
        "plan": plan,
        "plan_content": plan_content,
        "wiki_manifest": wiki_manifest,
        "implementation_map": implementation_map,
    }


# --------------------------------------------------------------------------- #
# Composition
# --------------------------------------------------------------------------- #


def test_track_for_level_maps_core_and_seminar():
    assert pg.track_for_level("a1") == "core"
    assert pg.track_for_level("B1") == "core"
    assert pg.track_for_level("hist") == "seminar"


def test_writer_block_is_preamble_then_body_then_shared_in_loader_order():
    block = pg.build_writer_rules_block("a1", "core")
    emitted = _emission_order(block)

    expected: list[str] = []
    for slot in pg.WRITER_SLOT_ORDER:
        for rule in load_applicable_rules("a1", "core", pg.DEFAULT_ACTIVITY_PROFILE, slot=slot):
            expected.append(rule.telemetry_id)

    assert emitted == expected, "generator must preserve slot order + loader topo/tie-break"
    # writer.preamble (R-RENDERER-CHARTER) must precede every shared.contract rule.
    assert emitted[0] == "#R-RENDERER-CHARTER"


def test_reviewer_block_is_rubric_then_shared_in_loader_order():
    block = pg.build_reviewer_rules_block("a1", "core")
    emitted = _emission_order(block)

    expected: list[str] = []
    for slot in pg.REVIEWER_SLOT_ORDER:
        for rule in load_applicable_rules("a1", "core", pg.DEFAULT_ACTIVITY_PROFILE, slot=slot):
            expected.append(rule.telemetry_id)

    assert emitted == expected
    # reviewer.rubric is currently empty → the block is exactly shared.contract.
    assert "#R-RENDERER-CHARTER" not in emitted, "writer.preamble must NOT leak into reviewer block"


def test_shared_contract_rules_appear_in_both_writer_and_reviewer():
    writer = _rule_ids(pg.build_writer_rules_block("a1", "core"))
    reviewer = _rule_ids(pg.build_reviewer_rules_block("a1", "core"))

    shared = {
        rule.telemetry_id
        for rule in load_applicable_rules("a1", "core", pg.DEFAULT_ACTIVITY_PROFILE, slot="shared.contract")
    }
    assert shared, "expected non-empty shared.contract slot"
    # Single-source point: every shared rule the writer is asked to follow is the
    # same rule the reviewer is asked to verify.
    assert shared <= writer
    assert shared <= reviewer


def test_markers_restored_for_every_emitted_rule():
    """Fragment bodies carry no #R-* marker; the generator must prepend it."""
    block = pg.build_writer_rules_block("a1", "core")
    for rule in load_applicable_rules("a1", "core", pg.DEFAULT_ACTIVITY_PROFILE):
        assert rule.telemetry_id in block, f"{rule.telemetry_id} missing from composed block"
        # The fragment body itself does not contain the marker.
        assert rule.telemetry_id not in rule.body


def test_emit_all_rules_no_further_filtering():
    """Every rule the loader returns for a slot is emitted — no extra filtering."""
    writer = _rule_ids(pg.build_writer_rules_block("a1", "core"))
    loader = {
        rule.telemetry_id
        for rule in load_applicable_rules("a1", "core", pg.DEFAULT_ACTIVITY_PROFILE)
        if rule.slot in pg.WRITER_SLOT_ORDER
    }
    assert writer == loader


# --------------------------------------------------------------------------- #
# Level edge
# --------------------------------------------------------------------------- #


def test_a1_only_rules_present_in_both_prompts_at_a1():
    writer = _rule_ids(pg.build_writer_rules_block("a1", "core"))
    reviewer = _rule_ids(pg.build_reviewer_rules_block("a1", "core"))
    assert writer >= A1_ONLY_RULES
    assert reviewer >= A1_ONLY_RULES


def test_a1_only_rules_absent_at_b1():
    writer = _rule_ids(pg.build_writer_rules_block("b1", "core"))
    reviewer = _rule_ids(pg.build_reviewer_rules_block("b1", "core"))
    assert not (A1_ONLY_RULES & writer)
    assert not (A1_ONLY_RULES & reviewer)


# --------------------------------------------------------------------------- #
# Obligation checklist — single source
# --------------------------------------------------------------------------- #


def test_obligation_checklist_is_single_source(m20):
    checklist_obj = pg.build_obligation_checklist_object(
        m20["wiki_manifest"],
        seeded_map=m20["implementation_map"],
    )
    checklist = pg.build_obligation_checklist(
        m20["wiki_manifest"],
        obligation_checklist=checklist_obj,
    )
    assert checklist, "expected a non-empty checklist for m20"
    # Same renderer object the writer prompt, reviewer prompt, and gate consume.
    assert checklist == lp._render_wiki_coverage_required_items(
        m20["wiki_manifest"],
        obligation_checklist=checklist_obj,
    )


def test_obligation_checklist_derived_from_wiki_coverage_gate_extraction(m20):
    """The checklist's required vocab must be the gate's extracted required items."""
    from scripts.audit.wiki_coverage_gate import _extract_required_items, _normalize_required_claim

    checklist_obj = pg.build_obligation_checklist_object(
        m20["wiki_manifest"],
        seeded_map=m20["implementation_map"],
    )
    checklist = pg.build_obligation_checklist(
        m20["wiki_manifest"],
        obligation_checklist=checklist_obj,
    )
    required_examples: set[str] = set()
    for item in m20["wiki_manifest"].get("sequence_steps", []):
        claim = str(item.get("required_claim") or item.get("heading") or "")
        if not claim:
            continue
        extracted = _extract_required_items(_normalize_required_claim(claim))
        required_examples.update(extracted["examples"])
    # Every required example surfaced by the gate's own extractor appears in the
    # checklist text the writer + reviewer see — no drift between gate and prompt.
    for example in required_examples:
        assert example in checklist, f"gate-required example {example!r} missing from checklist"


def test_obligation_checklist_identical_in_writer_and_reviewer_prompts(m20):
    checklist_obj = pg.build_obligation_checklist_object(
        m20["wiki_manifest"],
        seeded_map=m20["implementation_map"],
    )
    checklist = pg.build_obligation_checklist(
        m20["wiki_manifest"],
        obligation_checklist=checklist_obj,
    )
    writer_prompt = lp.render_writer_prompt(
        plan=m20["plan"],
        plan_content=m20["plan_content"],
        knowledge_packet="KP",
        wiki_manifest=m20["wiki_manifest"],
        implementation_map=m20["implementation_map"],
        writer="claude-tools",
        use_generator=True,
        obligation_checklist=checklist_obj,
    )
    reviewer_prompt = lp.render_review_prompt(
        m20["plan"],
        m20["plan_content"],
        "GENERATED CONTENT",
        "pedagogical",
        m20["wiki_manifest"],
        m20["implementation_map"],
        use_generator=True,
        obligation_checklist=checklist_obj,
    )
    assert _inserted_obligation_checklist(writer_prompt) == checklist
    assert _inserted_obligation_checklist(reviewer_prompt) == checklist


# --------------------------------------------------------------------------- #
# Opt-in flag — OFF byte-identical, ON parity
# --------------------------------------------------------------------------- #


def test_writer_context_off_is_unchanged_by_flag(m20):
    """Flag OFF must not perturb the legacy writer_context dict."""
    default = lp.writer_context(
        m20["plan"],
        m20["plan_content"],
        "KP",
        m20["wiki_manifest"],
        implementation_map=m20["implementation_map"],
        writer="claude-tools",
    )
    explicit_off = lp.writer_context(
        m20["plan"],
        m20["plan_content"],
        "KP",
        m20["wiki_manifest"],
        implementation_map=m20["implementation_map"],
        writer="claude-tools",
        use_generator=False,
    )
    assert default == explicit_off
    # The exact legacy key set — guards against a generator key leaking into OFF.
    assert set(default) == {
        "LEVEL", "MODULE_NUM", "MODULE_SLUG", "TOPIC_TITLE", "PHASE", "WORD_TARGET",
        "WRITER_SPECIFIC_DIRECTIVES", "PLAN_CONTENT", "KNOWLEDGE_PACKET", "WIKI_MANIFEST",
        "WIKI_COVERAGE_REQUIRED_ITEMS", "IMPLEMENTATION_MAP_CONTRACT", "LEARNER_STATE",
        "IMMERSION_RULE", "CONTRACT_YAML", "ALLOWED_ACTIVITY_TYPES", "FORBIDDEN_ACTIVITY_TYPES",
        "INLINE_ALLOWED_TYPES", "WORKBOOK_ALLOWED_TYPES", "ACTIVITY_COUNT_TARGET",
        "VOCAB_COUNT_TARGET", "COMPONENT_PROPS_SCHEMA",
    }
    assert "GENERATED_WRITER_RULES" not in default
    assert "OBLIGATION_CHECKLIST" not in default


def test_review_context_off_is_unchanged_by_flag(m20):
    default = lp.review_context(
        m20["plan"], m20["plan_content"], "X", "pedagogical",
        m20["wiki_manifest"], m20["implementation_map"],
    )
    explicit_off = lp.review_context(
        m20["plan"], m20["plan_content"], "X", "pedagogical",
        m20["wiki_manifest"], m20["implementation_map"], use_generator=False,
    )
    assert default == explicit_off
    assert "GENERATED_REVIEWER_RULES" not in default
    assert "OBLIGATION_CHECKLIST" not in default


def test_writer_prompt_off_byte_identical_to_legacy_template(m20):
    """Flag OFF renders the legacy template verbatim."""
    off = lp.render_writer_prompt(
        plan=m20["plan"], plan_content=m20["plan_content"], knowledge_packet="KP",
        wiki_manifest=m20["wiki_manifest"], implementation_map=m20["implementation_map"],
        writer="claude-tools", use_generator=False,
    )
    expected = lp.render_phase_prompt(
        lp.writer_prompt_path("claude-tools"),
        lp.writer_context(
            m20["plan"], m20["plan_content"], "KP", m20["wiki_manifest"],
            implementation_map=m20["implementation_map"], writer="claude-tools",
        ),
    )
    assert off == expected


def test_writer_context_on_adds_generator_keys(m20):
    checklist_obj = pg.build_obligation_checklist_object(
        m20["wiki_manifest"],
        seeded_map=m20["implementation_map"],
    )
    ctx = lp.writer_context(
        m20["plan"], m20["plan_content"], "KP", m20["wiki_manifest"],
        implementation_map=m20["implementation_map"], writer="claude-tools",
        use_generator=True, obligation_checklist=checklist_obj,
    )
    assert "#R-VESUM-ALL-WORDS" in ctx["GENERATED_WRITER_RULES"]
    assert ctx["OBLIGATION_CHECKLIST"] == pg.build_obligation_checklist(
        m20["wiki_manifest"],
        obligation_checklist=checklist_obj,
    )
    # Build-time tokens inside rule bodies are resolved before injection.
    assert "{ACTIVITY_COUNT_TARGET}" not in ctx["GENERATED_WRITER_RULES"]


def test_writer_context_on_without_manifest_builds_checklist(m20):
    ctx = lp.writer_context(
        m20["plan"],
        m20["plan_content"],
        "KP",
        wiki_manifest=None,
        implementation_map=m20["implementation_map"],
        writer="claude-tools",
        use_generator=True,
    )

    assert "OBLIGATION_CHECKLIST" in ctx
    assert "### step-" in ctx["OBLIGATION_CHECKLIST"]


def test_generated_writer_prompt_parity_with_legacy(m20):
    """ON writer prompt contains every #R-* the legacy writer template carries."""
    legacy = lp.render_writer_prompt(
        plan=m20["plan"], plan_content=m20["plan_content"], knowledge_packet="KP",
        wiki_manifest=m20["wiki_manifest"], implementation_map=m20["implementation_map"],
        writer="claude-tools", use_generator=False,
    )
    generated = lp.render_writer_prompt(
        plan=m20["plan"], plan_content=m20["plan_content"], knowledge_packet="KP",
        wiki_manifest=m20["wiki_manifest"], implementation_map=m20["implementation_map"],
        writer="claude-tools", use_generator=True,
    )
    assert _rule_ids(legacy) <= _rule_ids(generated)
    assert not BRACE_TOKEN_RE.findall(generated), "no unresolved downstream tokens"


def test_generated_reviewer_prompt_parity_with_legacy(m20):
    """ON reviewer prompt contains every #R-* the legacy reviewer template carries.

    The legacy reviewer template mirrors only 6 rules by hand; the generator
    emits all shared.contract rules (the single-source fix), so the generated
    prompt is a superset.
    """
    legacy = lp.render_review_prompt(
        m20["plan"], m20["plan_content"], "GC", "pedagogical",
        m20["wiki_manifest"], m20["implementation_map"], use_generator=False,
    )
    generated = lp.render_review_prompt(
        m20["plan"], m20["plan_content"], "GC", "pedagogical",
        m20["wiki_manifest"], m20["implementation_map"], use_generator=True,
    )
    assert _rule_ids(legacy) <= _rule_ids(generated)
    assert not BRACE_TOKEN_RE.findall(generated), "no unresolved downstream tokens"


def test_obligation_checklist_single_source_across_three_consumers(m20):
    """writer prompt == reviewer prompt == build_obligation_checklist text."""
    checklist_obj = pg.build_obligation_checklist_object(
        m20["wiki_manifest"],
        seeded_map=m20["implementation_map"],
    )
    checklist = pg.build_obligation_checklist(
        m20["wiki_manifest"],
        obligation_checklist=checklist_obj,
    )
    writer_ctx = lp.writer_context(
        m20["plan"], m20["plan_content"], "KP", m20["wiki_manifest"],
        implementation_map=m20["implementation_map"], writer="claude-tools", use_generator=True,
        obligation_checklist=checklist_obj,
    )
    review_ctx = lp.review_context(
        m20["plan"], m20["plan_content"], "X", "pedagogical",
        m20["wiki_manifest"], m20["implementation_map"], use_generator=True,
        obligation_checklist=checklist_obj,
    )
    assert checklist == writer_ctx["OBLIGATION_CHECKLIST"]
    assert checklist == review_ctx["OBLIGATION_CHECKLIST"]


def test_gate_consumes_obligation_checklist_one_to_one(m20):
    """wiki_coverage_gate sees the same obligations the renderer emitted."""
    from scripts.audit.wiki_coverage_gate import obligations_from_checklist

    checklist_obj = pg.build_obligation_checklist_object(
        m20["wiki_manifest"],
        seeded_map=m20["implementation_map"],
    )
    rendered = pg.build_obligation_checklist(
        m20["wiki_manifest"],
        obligation_checklist=checklist_obj,
    )
    gate_obligations = obligations_from_checklist(checklist_obj)
    gate_ids = [str(item["id"]) for item in gate_obligations]
    rendered_ids = [
        match
        for match in re.findall(r"^### (\S+) \(", rendered, flags=re.MULTILINE)
        if match != "wiki_vocabulary_minimum"
    ]

    assert len(gate_obligations) == len(m20["implementation_map"]["entries"])
    assert rendered_ids == gate_ids
    assert len(rendered_ids) == len(set(rendered_ids)), "no orphan/duplicate rendered obligations"
    for item in gate_obligations:
        if item["type"] == "sequence_step":
            assert item["normalized_claim"] in rendered
