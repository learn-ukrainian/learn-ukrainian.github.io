import json

from scripts.audit.check_writer_prompt_size import (
    WRITER_PROMPT_CEILING_BYTES,
    render_fixture_writer_prompt,
)
from scripts.build import linear_pipeline
from scripts.build.phases.implementation_map import seed_implementation_map


def _stub_manifest(level: str, slug: str) -> dict:
    return {
        "slug": slug,
        "wiki_path": f"wiki/pedagogy/{level}/{slug}.md",
        "sequence_steps": [],
        "l2_errors": [],
        "phonetic_rules": [],
        "decolonization_bans": [],
        "external_resources": [],
    }


def _render_c1_sample_prompt() -> str:
    level = "c1"
    slug = "abstract-writing"
    plan_path = linear_pipeline.plan_path_for(level, slug)
    plan = linear_pipeline.load_plan(plan_path)
    manifest = _stub_manifest(level, slug)
    return linear_pipeline.render_writer_prompt(
        plan=plan,
        plan_content=plan_path.read_text(encoding="utf-8"),
        knowledge_packet="Knowledge packet stub for C1 prompt-size smoke.",
        wiki_manifest=json.dumps(manifest, ensure_ascii=False, indent=2),
        implementation_map=seed_implementation_map(manifest, plan=plan),
    )


def test_a1_letter_module_writer_prompt_stays_under_ceiling() -> None:
    prompt = render_fixture_writer_prompt("a1", "sounds-letters-and-hello")

    assert len(prompt.encode("utf-8")) <= WRITER_PROMPT_CEILING_BYTES


def test_a1_m20_writer_prompt_stays_under_ceiling() -> None:
    prompt = render_fixture_writer_prompt("a1", "my-morning")

    assert len(prompt.encode("utf-8")) <= WRITER_PROMPT_CEILING_BYTES


def test_c1_sample_writer_prompt_stays_under_ceiling() -> None:
    prompt = _render_c1_sample_prompt()

    assert len(prompt.encode("utf-8")) <= WRITER_PROMPT_CEILING_BYTES
