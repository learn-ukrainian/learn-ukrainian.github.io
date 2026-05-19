from __future__ import annotations

import re
from typing import Any

from scripts.build import linear_pipeline
from scripts.build.phases.implementation_map import (
    render_for_writer_prompt,
    seed_implementation_map,
)
from tests.build.test_implementation_map import _fixture_manifest

SENTINEL = "(no implementation_map provided to render_writer_prompt — gate will fail)"


def _minimal_plan() -> dict[str, Any]:
    return {
        "module": "A1-20",
        "level": "A1",
        "sequence": 20,
        "slug": "fixture-module",
        "title": "Fixture Module",
        "subtitle": "Fixture module",
        "phase": "writer",
        "word_target": 1200,
        "content_outline": [
            {
                "section": "Привітання",
                "words": 300,
                "points": ["Start with a morning greeting."],
            }
        ],
        "activity_hints": [],
        "vocabulary_hints": {"required": []},
        "references": [],
    }


def _seeded_payload() -> dict[str, Any]:
    return seed_implementation_map(_fixture_manifest(), plan=None)


def _rendered_writer_prompt(writer: str = "claude-tools") -> tuple[str, dict[str, Any]]:
    manifest = _fixture_manifest()
    payload = seed_implementation_map(manifest, plan=None)
    prompt = linear_pipeline.render_writer_prompt(
        plan=_minimal_plan(),
        plan_content="Plan content stub.",
        knowledge_packet="Knowledge packet stub.",
        wiki_manifest=manifest,
        implementation_map=payload,
        writer=writer,
    )
    return prompt, payload


def _row_ids(rendered: str) -> list[str]:
    return re.findall(r"^- obligation_id: (\S+)", rendered, flags=re.MULTILINE)


def test_render_contains_one_row_per_entry() -> None:
    payload = _seeded_payload()
    rendered = render_for_writer_prompt(payload)

    assert rendered.count("- obligation_id: ") == len(payload["entries"])
    for entry in payload["entries"]:
        assert f"obligation_id: {entry['obligation_id']}" in rendered


def test_render_is_deterministic() -> None:
    payload = _seeded_payload()

    assert render_for_writer_prompt(payload) == render_for_writer_prompt(payload)


def test_render_sorted_by_obligation_id() -> None:
    payload = _seeded_payload()
    rendered = render_for_writer_prompt(payload)

    assert _row_ids(rendered) == sorted(entry["obligation_id"] for entry in payload["entries"])


def test_placeholder_is_fully_replaced() -> None:
    prompt, payload = _rendered_writer_prompt()

    assert "{IMPLEMENTATION_MAP_CONTRACT}" not in prompt
    assert f"obligation_id: {payload['entries'][0]['obligation_id']}" in prompt


def test_every_seeded_row_appears_in_prompt() -> None:
    prompt, payload = _rendered_writer_prompt()

    for entry in payload["entries"]:
        assert f"obligation_id: {entry['obligation_id']}" in prompt


def test_grok_variant_also_renders_contract() -> None:
    prompt, payload = _rendered_writer_prompt(writer="grok-tools")

    assert "{IMPLEMENTATION_MAP_CONTRACT}" not in prompt
    assert f"obligation_id: {payload['entries'][0]['obligation_id']}" in prompt


def test_writer_context_without_map_emits_sentinel() -> None:
    context = linear_pipeline.writer_context(
        _minimal_plan(),
        "Plan content stub.",
        "Knowledge packet stub.",
        wiki_manifest=_fixture_manifest(),
        implementation_map=None,
    )

    assert context["IMPLEMENTATION_MAP_CONTRACT"] == SENTINEL
