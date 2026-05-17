from __future__ import annotations

from pathlib import Path

from scripts.build import linear_pipeline
from scripts.common.thresholds import QG_DIMS

ROOT = Path(__file__).resolve().parents[1]
WRITER_TEMPLATE = ROOT / "scripts/build/phases/linear-write.md"


def test_qg_dims_remain_five_standard_dimensions() -> None:
    assert QG_DIMS == (
        "pedagogical",
        "naturalness",
        "decolonization",
        "engagement",
        "tone",
    )


def test_writer_prompt_places_manifest_before_module_context() -> None:
    plan_path = linear_pipeline.plan_path_for("a1", "my-morning")
    plan = linear_pipeline.plan_check(plan_path)
    context = linear_pipeline.writer_context(
        plan,
        plan_path.read_text(encoding="utf-8"),
        "Knowledge packet stub.",
        {
            "slug": "my-morning",
            "sequence_steps": [],
            "l2_errors": [],
            "phonetic_rules": [],
            "decolonization_bans": [],
            "external_resources": [],
        },
    )
    rendered = linear_pipeline.render_phase_prompt(WRITER_TEMPLATE, context)

    assert rendered.index("## LESSON SOURCE") < rendered.index("## Module Context")
    assert rendered.index("## Wiki Obligations Manifest") < rendered.index("## Module Context")
    assert "External Resources — multimedia search obligation" in rendered
    assert "resources_search_attempted" in rendered
    assert "mcp__sources__search_external" in rendered
    assert "<implementation_map>" in rendered
    assert "Full Wiki Context (source of truth for citations)" in rendered


def test_build_wiki_manifest_renders_my_morning_json() -> None:
    manifest = linear_pipeline.build_wiki_manifest(level="a1", slug="my-morning")

    assert '"slug": "my-morning"' in manifest
    assert '"id": "err-1"' in manifest
    assert '"id": "step-5"' in manifest
    assert '"external_resources": []' in manifest


def test_wiki_coverage_review_prompt_receives_manifest_and_gate() -> None:
    plan_path = linear_pipeline.plan_path_for("a1", "my-morning")
    plan = linear_pipeline.plan_check(plan_path)
    prompt = linear_pipeline.render_wiki_coverage_review_prompt(
        plan,
        plan_path.read_text(encoding="utf-8"),
        "## module.md\n\nGenerated content",
        {"slug": "my-morning", "l2_errors": [{"id": "err-1"}]},
        {"passed": True, "coverage_pct": 1.0},
    )

    assert "Wiki Obligations Manifest" in prompt
    assert "Deterministic Wiki Coverage Gate" in prompt
    assert '"err-1"' in prompt
    assert "QG_DIMS" in prompt


def test_v7_build_orders_wiki_gate_before_aggregate_qg() -> None:
    source = (ROOT / "scripts/build/v7_build.py").read_text(encoding="utf-8")
    run_body = source[source.index("def _run(") :]

    # PR #2108 (Path 3 PR1) split build_wiki_manifest into a dict-returning
    # build_wiki_manifest_data + a json-stringifying wrapper so the deterministic
    # implementation_map seeder can consume the dict before the writer phase.
    # The structural assertion (manifest built before writer prompt) is unchanged.
    assert run_body.index("build_wiki_manifest_data(") < run_body.index("_writer_prompt(")
    assert run_body.index("run_wiki_coverage_gate(") < run_body.index("_run_wiki_coverage_review(")
    assert run_body.index("_run_wiki_coverage_review(") < run_body.index("_run_llm_qg(")
