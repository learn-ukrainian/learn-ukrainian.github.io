"""Enforce writer prompt size ceiling.

Per architectural reset 2026-05-23
(`docs/session-state/2026-05-23-architectural-reset-strip-v7-llm-demote.md`,
decision row C), strip cycle PR-C 2026-05-23): rendered writer prompt must
stay under WRITER_PROMPT_CEILING_BYTES for all level/module fixtures.

Empirical baseline (post-PR-C):
- a1/my-morning rendered: ~120KB target, 130KB ceiling (10KB headroom for
  manifest variance across modules)
- Below 120KB requires per-module data restructure (PR-D scope: knowledge-packet
  diet, manifest compression)

If a fixture's rendered prompt exceeds the ceiling, fail the build so the strip
cycle does not regress silently.
"""

from __future__ import annotations

import json

import pytest

from scripts.build import linear_pipeline
from scripts.build.phases.implementation_map import seed_implementation_map

WRITER_PROMPT_CEILING_BYTES = 130 * 1024  # 130KB

# Fixture modules to enforce against. Add more as the strip proves out on each
# level. Start with the A1 anchor.
FIXTURE_MODULES = [
    ("a1", "my-morning"),
]


def render_fixture_writer_prompt(level: str, slug: str) -> str:
    """Render the writer prompt without invoking a writer."""
    plan_path = linear_pipeline.plan_path_for(level, slug)
    plan = linear_pipeline.plan_check(plan_path)
    plan_content = plan_path.read_text(encoding="utf-8")
    knowledge_packet = linear_pipeline.build_knowledge_packet(
        level=level,
        slug=slug,
        plan=plan,
    )
    wiki_manifest_data = linear_pipeline.build_wiki_manifest_data(
        level=level,
        slug=slug,
        plan=plan,
    )
    implementation_map = seed_implementation_map(wiki_manifest_data, plan=plan)
    return linear_pipeline.render_writer_prompt(
        plan=plan,
        plan_content=plan_content,
        knowledge_packet=knowledge_packet,
        wiki_manifest=json.dumps(wiki_manifest_data, ensure_ascii=False, indent=2),
        implementation_map=implementation_map,
    )


@pytest.mark.parametrize("level,slug", FIXTURE_MODULES)
def test_writer_prompt_rendered_size_under_ceiling(level: str, slug: str) -> None:
    rendered = render_fixture_writer_prompt(level, slug)
    size = len(rendered.encode("utf-8"))
    assert size <= WRITER_PROMPT_CEILING_BYTES, (
        f"{level}/{slug} writer prompt is {size} bytes, over the "
        f"{WRITER_PROMPT_CEILING_BYTES}-byte ceiling. Strip more or escalate "
        f"to per-module data restructure (PR-D scope)."
    )
