"""Writer-only plan projection preserves teaching data and unknown keys (#9343)."""

import re
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from scripts.build import linear_pipeline
from tests.test_writer_prompt_render_size import _pin_a1_letter_prompt_inputs

pytestmark = pytest.mark.reads_content

EDITORIAL_KEYS = {
    "plan_fixes",
    "changelog",
    "review_notes",
    "reviewed_by",
    "reviewed_at",
    "lifecycle",
    "version",
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
        plan,
        raw,
    )

    assert yaml.safe_load(rendered) == {key: value for key, value in plan.items() if key not in EDITORIAL_KEYS}
    assert plan == original
    assert EDITORIAL_KEYS == linear_pipeline.WRITER_PLAN_OMIT_KEYS


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
        plan,
        raw,
        packet,
        {"slug": plan["slug"], "sequence_steps": [], "l2_errors": []},
    )

    assert context["PLAN_CONTENT"] == raw


@pytest.mark.parametrize(
    "raw,expected",
    [
        (
            "version: 2\n  # editorial comment\n# writer instruction\nslug: fixture\n",
            "# writer instruction\nslug: fixture\n",
        ),
        ("slug: fixture\nreview_notes: old", "slug: fixture\n"),
        ("# history\nversion: 2\nslug: fixture\n", "slug: fixture\n"),
        (
            "---\r\nslug: fixture\r\n'version': 2\r\n# writer\r\n\"references\": []\r\n...\r\n",
            '---\r\nslug: fixture\r\n# writer\r\n"references": []\r\n...\r\n',
        ),
        (
            "slug: fixture\ncontent: |+\n  version: teaching text\n  # literal comment\n\n"
            "version: |\n  slug: editorial text\n# next key instruction\nreferences: []\n",
            "slug: fixture\ncontent: |+\n  version: teaching text\n  # literal comment\n\n"
            "# next key instruction\nreferences: []\n",
        ),
        (
            'slug: fixture\ncontent: "first\nversion: retained inside a string\nlast"\n'
            "version: 'old\n# part of the omitted string'\n# real writer comment\nreferences: []\n",
            'slug: fixture\ncontent: "first\nversion: retained inside a string\nlast"\n'
            "# real writer comment\nreferences: []\n",
        ),
        (
            "---\nversion: 1\nslug: first\n...\n---\nslug: second\nreview_notes: old\n...\n",
            "---\nslug: first\n...\n---\nslug: second\n...\n",
        ),
        ("slug: fixture\r\nreferences: []", "slug: fixture\r\nreferences: []"),
        ("version: 1\nreview_notes: old\n", ""),
    ],
)
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


def _plan_paths():
    root = Path("curriculum/l2-uk-en/plans")
    paths = sorted(root.rglob("*.yaml"))
    if not paths:
        pytest.skip("Plan tree is absent in this sparse worktree; real-corpus property check unavailable.")
    return paths


def _representative_plan_paths(paths):
    """Cover every alphabet/legacy plan, directory and editorial key by rule.

    Use the first sorted path per directory and top-level editorial key, plus
    every alphabet plan and every plan changed by legacy normalization. A fast
    YAML loader inventories the whole tree; only selected plans run the costly
    projection and independent byte oracle.
    """
    safe_loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
    seen_directories = set()
    seen_keys = set()
    selected = []
    for path in sorted(paths):
        plan = yaml.load(path.read_bytes().decode("utf-8"), Loader=safe_loader)
        editorial_keys = EDITORIAL_KEYS & plan.keys()
        normalized = deepcopy(plan)
        linear_pipeline._normalize_legacy_plan_shape(normalized)
        if (
            path.parent not in seen_directories
            or editorial_keys - seen_keys
            or linear_pipeline.is_alphabet_slug(plan.get("slug"))
            or normalized != plan
        ):
            selected.append(path)
        seen_directories.add(path.parent)
        seen_keys.update(editorial_keys)
    return selected


def _assert_plan_projections_are_exact_raw_block_subtraction(paths):
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


def test_representative_plan_projection_is_exact_raw_block_subtraction():
    paths = _plan_paths()
    selected = _representative_plan_paths(paths)
    _assert_plan_projections_are_exact_raw_block_subtraction(selected)
    print(f"Plan subset checked: {len(selected)} of {len(paths)} plans; exact raw block subtraction.")


@pytest.mark.slow
def test_every_plan_projection_is_exact_raw_block_subtraction():
    paths = _plan_paths()
    _assert_plan_projections_are_exact_raw_block_subtraction(paths)
    print(f"Plan corpus checked: {len(paths)} plans; exact raw block subtraction.")
