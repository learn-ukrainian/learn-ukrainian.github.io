from __future__ import annotations

from scripts.build import linear_pipeline
from scripts.build.phases.implementation_map import seed_implementation_map


def test_per_dim_reviewer_prompt_receives_manifest_and_implementation_map() -> None:
    plan_path = linear_pipeline.plan_path_for("a1", "my-morning")
    plan = linear_pipeline.plan_check(plan_path)
    manifest = linear_pipeline.build_wiki_manifest_data(
        level="a1",
        slug="my-morning",
        plan=plan,
    )
    implementation_map = seed_implementation_map(manifest, plan=plan)

    prompt = linear_pipeline.render_review_prompt(
        plan,
        plan_path.read_text(encoding="utf-8"),
        "## module.md\n\nGenerated content",
        "pedagogical",
        manifest,
        implementation_map,
    )

    assert "## Writer Obligation Context" in prompt
    assert "### Wiki Obligations Manifest" in prompt
    assert '"slug": "my-morning"' in prompt
    assert '"id": "step-5"' in prompt
    assert "### Implementation Map Contract" in prompt
    assert "Manifest obligations:" in prompt
    assert "obligation_id: step-5" in prompt
    assert "treatment_template:" in prompt
    assert "## Module Size Policy" in prompt
    assert "Expansion permission:" in prompt
    assert "Padding diagnostic:" in prompt
