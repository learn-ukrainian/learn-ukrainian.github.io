import json

from scripts.build import linear_pipeline
from scripts.build.phases.implementation_map import seed_implementation_map


def _render_prompt(level: str, slug: str, *, validate: bool = True) -> str:
    plan_path = linear_pipeline.plan_path_for(level, slug)
    plan = linear_pipeline.plan_check(plan_path) if validate else linear_pipeline.load_plan(plan_path)
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
        knowledge_packet="Knowledge packet stub for resource-search prompt smoke.",
        wiki_manifest=json.dumps(manifest, ensure_ascii=False, indent=2),
        implementation_map=seed_implementation_map(manifest, plan=plan),
    )


def test_a1_writer_prompt_requires_resource_search_attempt_telemetry() -> None:
    prompt = _render_prompt("a1", "my-morning")

    assert "resources_search_attempted" in prompt
    assert "MUST still record the search attempt in writer telemetry" in prompt


def test_c1_writer_prompt_requires_resource_search_attempt_telemetry() -> None:
    prompt = _render_prompt("c1", "abstract-writing", validate=False)

    assert "resources_search_attempted" in prompt
    assert "MUST still record the search attempt in writer telemetry" in prompt
