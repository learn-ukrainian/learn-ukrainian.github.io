import json

from scripts.build import linear_pipeline
from scripts.build.phases.implementation_map import seed_implementation_map


def _render_a1_my_morning_prompt() -> str:
    level = "a1"
    slug = "my-morning"
    plan_path = linear_pipeline.plan_path_for(level, slug)
    plan = linear_pipeline.plan_check(plan_path)
    manifest = {
        "slug": slug,
        "wiki_path": f"wiki/pedagogy/{level}/{slug}.md",
        "sequence_steps": [],
        "l2_errors": [],
        "phonetic_rules": [],
        "decolonization_bans": [],
        "external_resources": [],
    }
    return linear_pipeline.render_writer_prompt(
        plan=plan,
        plan_content=plan_path.read_text(encoding="utf-8"),
        knowledge_packet="Knowledge packet stub for dialogue prompt smoke.",
        wiki_manifest=json.dumps(manifest, ensure_ascii=False, indent=2),
        implementation_map=seed_implementation_map(manifest, plan=plan),
    )


def test_writer_prompt_does_not_require_inline_english_gloss_within_8_tokens() -> None:
    prompt = _render_a1_my_morning_prompt()

    assert "inline English gloss within 8 tokens" not in prompt


def test_writer_prompt_requires_dialoguebox_side_by_side_translation() -> None:
    prompt = _render_a1_my_morning_prompt()

    # The example MUST be self-closing (`/>`): a bare `<DialogueBox ...>` is
    # invalid MDX and the l2_exposure_floor regex counts it as zero. Codex
    # copied the previously-malformed example verbatim and silently failed the
    # dialogue floor on m20 (2026-05-29). The example now teaches valid MDX.
    assert 'Use `<DialogueBox uk="..." en="..." />`' in prompt
    assert "side-by-side translation" in prompt
    # The directive must explicitly require the self-closing `/>` form.
    assert "MUST be self-closing" in prompt
