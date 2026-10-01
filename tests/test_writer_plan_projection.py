"""Writer-only plan projection preserves teaching data and unknown keys (#9343)."""

from copy import deepcopy

import pytest
import yaml

from scripts.build import linear_pipeline
from tests.test_writer_prompt_render_size import _pin_a1_letter_prompt_inputs

pytestmark = pytest.mark.reads_content

EDITORIAL_KEYS = {
    "plan_fixes", "changelog", "review_notes", "reviewed_by", "reviewed_at",
    "lifecycle", "version",
}


@pytest.mark.parametrize("references_rendered", [False, True])
def test_projection_omits_only_named_keys_and_preserves_unknown_data(references_rendered):
    plan = {
        "slug": "fixture-module",
        "content_outline": [{"section": "Teaching", "points": ["Keep this whole."]}],
        "new_teaching_key": {"version": 7, "review_notes": "Nested teaching data stays."},
        "references": [{"title": "Fixture source", "notes": "Required grounding."}],
        **{key: f"editorial-{key}" for key in EDITORIAL_KEYS},
    }
    original = deepcopy(plan)
    omitted = EDITORIAL_KEYS | ({"references"} if references_rendered else set())

    rendered = linear_pipeline._writer_plan_content_for_prompt(
        plan, references_rendered=references_rendered,
    )

    assert yaml.safe_load(rendered) == {key: value for key, value in plan.items() if key not in omitted}
    assert plan == original
    assert EDITORIAL_KEYS | {"references"} == linear_pipeline.WRITER_PLAN_OMIT_KEYS


@pytest.mark.parametrize("writer,use_generator", [
    ("claude-tools", False), ("claude-tools", True),
])
def test_projection_is_writer_only_and_references_render_once(monkeypatch, tmp_path, writer, use_generator):
    _pin_a1_letter_prompt_inputs(monkeypatch, tmp_path)
    plan_path = linear_pipeline.plan_path_for("a1", "sounds-letters-and-hello")
    plan = linear_pipeline.plan_check(plan_path)
    original = deepcopy(plan)
    raw = yaml.safe_dump(plan, allow_unicode=True, sort_keys=False)
    packet = linear_pipeline.build_knowledge_packet(plan=plan)
    manifest = {"slug": plan["slug"], "sequence_steps": [], "l2_errors": []}

    prompt = linear_pipeline.render_writer_prompt(
        plan=plan, plan_content=raw, knowledge_packet=packet, wiki_manifest=manifest,
        writer=writer, use_generator=use_generator,
    )
    block = prompt.split("\n## Plan\n", 1)[1].split("```yaml\n", 1)[1].split("\n```", 1)[0]
    projected = yaml.safe_load(block)

    assert not ((EDITORIAL_KEYS | {"references"}) & projected.keys())
    assert prompt.count("\n## Plan References\n") == 1
    reference_block = packet.split("\n## Plan References\n", 1)[1]
    for reference in plan["references"]:
        assert f"**{reference['title']}**" in reference_block
        for key in ("notes", "url"):
            if reference.get(key):
                assert str(reference[key]).strip() in reference_block
    assert packet in prompt
    assert plan == original
    review = linear_pipeline.review_context(plan, raw, "Draft.", "pedagogical", manifest)
    expected_review = linear_pipeline._plan_content_for_prompt(plan, raw)
    assert review["PLAN_CONTENT"] == expected_review
    assert yaml.safe_load(review["PLAN_CONTENT"]).keys() >= EDITORIAL_KEYS


def test_grok_writer_uses_the_same_plan_projection(monkeypatch, tmp_path):
    _pin_a1_letter_prompt_inputs(monkeypatch, tmp_path)
    plan = linear_pipeline.plan_check(linear_pipeline.plan_path_for("a1", "sounds-letters-and-hello"))
    packet = linear_pipeline.build_knowledge_packet(plan=plan)
    prompt = linear_pipeline.render_writer_prompt(
        plan=plan, plan_content=yaml.safe_dump(plan), knowledge_packet=packet,
        wiki_manifest={"slug": plan["slug"], "sequence_steps": [], "l2_errors": []},
        writer="grok-tools",
    )
    block = prompt.split("\n## Plan\n", 1)[1].split("```yaml\n", 1)[1].split("\n```", 1)[0]

    assert yaml.safe_load(block) == yaml.safe_load(
        linear_pipeline._writer_plan_content_for_prompt(plan, references_rendered=True),
    )
    assert packet in prompt


def test_writer_context_keeps_references_without_separate_block(monkeypatch, tmp_path):
    _pin_a1_letter_prompt_inputs(monkeypatch, tmp_path)
    plan = linear_pipeline.plan_check(linear_pipeline.plan_path_for("a1", "sounds-letters-and-hello"))
    context = linear_pipeline.writer_context(
        plan, yaml.safe_dump(plan), "Knowledge packet without a reference block.",
        {"slug": plan["slug"], "sequence_steps": [], "l2_errors": []},
    )

    assert yaml.safe_load(context["PLAN_CONTENT"])["references"] == plan["references"]
