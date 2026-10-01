"""Writer-only plan projection preserves teaching data and unknown keys (#9343)."""

import re
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from scripts.build import linear_pipeline
from tests.test_writer_prompt_render_size import _checkout_text, _pin_a1_letter_prompt_inputs

pytestmark = pytest.mark.reads_content

EDITORIAL_KEYS = {
    "plan_fixes", "changelog", "review_notes", "reviewed_by", "reviewed_at",
    "lifecycle", "version",
}


def test_projection_omits_only_named_keys_and_preserves_unknown_data():
    plan = {
        "slug": "fixture-module",
        "content_outline": [{"section": "Teaching", "points": ["Keep this whole."]}],
        "new_teaching_key": {"version": 7, "review_notes": "Nested teaching data stays."},
        "references": [{"title": "Fixture source", "notes": "Required grounding."}],
        **{key: f"editorial-{key}" for key in EDITORIAL_KEYS},
    }
    original = deepcopy(plan)
    raw = yaml.safe_dump(plan, sort_keys=False)

    rendered = linear_pipeline._writer_plan_content_for_prompt(
        plan, raw,
    )

    assert yaml.safe_load(rendered) == {key: value for key, value in plan.items() if key not in EDITORIAL_KEYS}
    assert plan == original
    assert EDITORIAL_KEYS == linear_pipeline.WRITER_PLAN_OMIT_KEYS


@pytest.mark.parametrize("writer,use_generator", [
    ("claude-tools", False), ("claude-tools", True),
])
def test_projection_is_writer_only_and_keeps_both_reference_renderings(monkeypatch, tmp_path, writer, use_generator):
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

    assert not (EDITORIAL_KEYS & projected.keys())
    assert projected["references"] == plan["references"]
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
        linear_pipeline._writer_plan_content_for_prompt(plan, yaml.safe_dump(plan)),
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


@pytest.mark.parametrize("packet", ["Packet without references.", "\n## Plan References\n- **Shared title**\n"])
def test_writer_context_keeps_raw_comments_and_all_reference_fields(monkeypatch, tmp_path, packet):
    """Both review blockers must fail on the original implementation's behavior."""
    _pin_a1_letter_prompt_inputs(monkeypatch, tmp_path)
    raw = (
        "slug: fixture-module\nlevel: A1\nsequence: 1\ntitle: Fixture\nword_target: 300\n"
        "# The writer MUST preserve the instruction in this comment.\n"
        "content_outline:\n- section: Teaching\n  words: 300\n  points: [Keep this.]\n"
        "references:\n- title: Shared title\n  note: Instruction\n  type: primary\n"
        "  author: Source author\n  path: wiki/source.md\n  pages: 10-12\n  topic: First\n"
        "- title: Shared title\n  pages: 13-15\n  topic: Second\n"
    )
    plan = yaml.safe_load(raw)
    plan["references"][0]["corpus_missing"] = True
    context = linear_pipeline.writer_context(
        plan, raw, packet,
        {"slug": plan["slug"], "sequence_steps": [], "l2_errors": []},
    )

    assert context["PLAN_CONTENT"] == raw


@pytest.mark.parametrize("raw,expected", [
    (
        "version: 2\n  # editorial comment\n# writer instruction\nslug: fixture\n",
        "# writer instruction\nslug: fixture\n",
    ),
    ("slug: fixture\nreview_notes: old", "slug: fixture\n"),
    ("# history\nversion: 2\nslug: fixture\n", "slug: fixture\n"),
    (
        "---\r\nslug: fixture\r\n'version': 2\r\n# writer\r\n\"references\": []\r\n...\r\n",
        "---\r\nslug: fixture\r\n# writer\r\n\"references\": []\r\n...\r\n",
    ),
    (
        "slug: fixture\ncontent: |+\n  version: teaching text\n  # literal comment\n\n"
        "version: |\n  slug: editorial text\n# next key instruction\nreferences: []\n",
        "slug: fixture\ncontent: |+\n  version: teaching text\n  # literal comment\n\n"
        "# next key instruction\nreferences: []\n",
    ),
    (
        "slug: fixture\ncontent: \"first\nversion: retained inside a string\nlast\"\n"
        "version: 'old\n# part of the omitted string'\n# real writer comment\nreferences: []\n",
        "slug: fixture\ncontent: \"first\nversion: retained inside a string\nlast\"\n"
        "# real writer comment\nreferences: []\n",
    ),
    (
        "---\nversion: 1\nslug: first\n...\n---\nslug: second\nreview_notes: old\n...\n",
        "---\nslug: first\n...\n---\nslug: second\n...\n",
    ),
    ("slug: fixture\r\nreferences: []", "slug: fixture\r\nreferences: []"),
    ("version: 1\nreview_notes: old\n", ""),
])
def test_raw_projection_preserves_every_retained_byte(raw, expected):
    assert linear_pipeline._omit_writer_plan_blocks(raw) == expected


def _raw_plan_without_editorial_blocks(raw):
    """Independent line oracle for the real plan tree's column-zero key shape."""
    lines = raw.splitlines(keepends=True)
    boundaries = []
    for index, line in enumerate(lines):
        match = re.match(r"^([a-zA-Z_][\w-]*):(?:\s|$)", line)
        if not match:
            continue
        start = index
        while start and lines[start - 1].startswith("#"):
            start -= 1
        boundaries.append((start, match[1]))
    boundaries.append((len(lines), None))
    omitted_lines = set()
    for index, (start, key) in enumerate(boundaries[:-1]):
        end = boundaries[index + 1][0]
        if key in EDITORIAL_KEYS:
            omitted_lines.update(range(start, end))
    return "".join(line for index, line in enumerate(lines) if index not in omitted_lines)


@pytest.mark.parametrize("relative_path", [
    "a1/colors.yaml", "a1/this-and-that.yaml", "a1/things-have-gender.yaml", "a1/my-morning.yaml",
    "a2/nature-and-traditions.yaml", "b1/participle-phrases.yaml",
    "b2/passive-voice-system.yaml", "folk/bylyny-kyivskoho-tsyklu.yaml",
])
def test_real_plan_projection_preserves_comments_and_reference_shapes(relative_path):
    raw = _checkout_text(f"curriculum/l2-uk-en/plans/{relative_path}")
    plan = yaml.safe_load(raw)
    linear_pipeline._normalize_legacy_plan_shape(plan)
    original = deepcopy(plan)
    if plan.get("references"):
        plan["references"][0]["corpus_missing"] = True
    rendered = linear_pipeline._writer_plan_content_for_prompt(plan, raw)

    assert rendered == _raw_plan_without_editorial_blocks(raw)
    assert yaml.safe_load(rendered)["references"] == yaml.safe_load(raw)["references"]
    assert "corpus_missing" not in rendered
    # Projection does not mutate the caller's already-normalized mapping either.
    if original.get("references"):
        original["references"][0]["corpus_missing"] = True
    assert plan == original


def test_alphabet_projection_keeps_existing_filter_and_dump_path(monkeypatch, tmp_path):
    _pin_a1_letter_prompt_inputs(monkeypatch, tmp_path)
    plan_path = linear_pipeline.plan_path_for("a1", "sounds-letters-and-hello")
    plan = linear_pipeline.plan_check(plan_path)
    raw = plan_path.read_text(encoding="utf-8")
    projected = {key: value for key, value in plan.items() if key not in EDITORIAL_KEYS}

    assert linear_pipeline._writer_plan_content_for_prompt(plan, raw) == (
        linear_pipeline._plan_content_for_prompt(projected, raw)
    )
    assert yaml.safe_load(linear_pipeline._plan_content_for_prompt(plan, raw)) == {
        **yaml.safe_load(linear_pipeline._writer_plan_content_for_prompt(plan, raw)),
        **{key: value for key, value in plan.items() if key in EDITORIAL_KEYS},
    }


def test_every_plan_projection_is_exact_raw_block_subtraction():
    root = Path("curriculum/l2-uk-en/plans")
    paths = sorted(root.rglob("*.yaml"))
    if not paths:
        pytest.skip("Plan tree is absent in this sparse worktree; real-corpus property check unavailable.")
    safe_loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
    for path in paths:
        raw = path.read_bytes().decode("utf-8")
        raw_plan = yaml.load(raw, Loader=safe_loader)
        plan = deepcopy(raw_plan)
        if linear_pipeline.is_alphabet_slug(plan.get("slug")):
            # Alphabet writer rendering is checked separately; exercise raw
            # subtraction on these files too without replacing its dump path.
            projected = linear_pipeline._omit_writer_plan_blocks(raw)
        else:
            linear_pipeline._normalize_legacy_plan_shape(plan)
            projected = linear_pipeline._writer_plan_content_for_prompt(plan, raw)
        assert projected == _raw_plan_without_editorial_blocks(raw), path
        assert yaml.load(projected, Loader=safe_loader) == {
            key: value for key, value in raw_plan.items() if key not in EDITORIAL_KEYS
        }, path
    print(f"Plan corpus checked: {len(paths)} plans; exact raw block subtraction.")
