from __future__ import annotations

from scripts.build.linear_pipeline import _render_wiki_coverage_required_items


def test_render_wiki_coverage_required_items_contains_hint() -> None:
    manifest = {
        "sequence_steps": [
            {
                "id": "step-1",
                "required_claim": "How to say water in Ukrainian: «вода»",
            }
        ]
    }
    rendered = _render_wiki_coverage_required_items(manifest)

    assert "**Coverage rule**" in rendered
    assert "MUST appear at least once in `module.md` PROSE" in rendered
    assert "A vocab table entry alone is NOT coverage" in rendered
    assert "### step-1 (sequence step)" in rendered
    assert "Vocabulary to introduce: вода" in rendered
