"""Structural assertions for the V7 writer + reviewer prompts.

Locks two coordinated prompt-discipline features:
  - #1673 chain-of-thought reasoning checklist (4 numbered steps)
  - #1661 Tier-1 verification discipline / audit (5 numbered/lettered items)

Renders ``linear-write.md`` and ``linear-review-dim.md`` against three
already-validated reference plans (a1/my-morning, b1/aspect-future-tense,
a2/a2-bridge) and asserts the structural markers + verbatim discipline
text are present and that no ``{TOKEN}`` placeholders survived rendering.
"""

from __future__ import annotations

import re

import pytest

from scripts.build import linear_pipeline
from scripts.common.thresholds import QG_DIMS

REFERENCE_PLANS: tuple[tuple[str, str], ...] = (
    ("a1", "my-morning"),
    ("a2", "a2-bridge"),
    ("b1", "adjectives-comparative"),
)

WRITER_TEMPLATE = (
    linear_pipeline.PROJECT_ROOT / "scripts/build/phases/linear-write.md"
)
REVIEWER_TEMPLATE = (
    linear_pipeline.PROJECT_ROOT / "scripts/build/phases/linear-review-dim.md"
)

WRITER_COT_HEADER = (
    "## Reasoning checklist (do this BEFORE drafting — #1673)"
)
WRITER_TIER1_HEADER = (
    "## Tier-1 verification discipline (do this WHILE drafting — #1661)"
)
REVIEWER_COT_HEADER = (
    "## Reasoning checklist (do this BEFORE scoring — #1673)"
)
REVIEWER_TIER1_HEADER = (
    "## Tier-1 verification audit (do this DURING evidence search — #1661)"
)

WRITER_TIER1_BULLETS = (
    "Verify every example word in VESUM",
    "Modern Ukrainian only",
    "Source-citation discipline",
    "Quote attribution discipline",
    "End-of-output gate",
)

REVIEWER_TIER1_BULLETS = (
    "Source-attribution audit (all dims)",
    "Quote verification (all dims)",
    "Sovietization flag (decolonization, naturalness)",
    "Modern Ukrainian guard (naturalness, decolonization)",
    "Reinforce rule #6",
)

# Plain ``{NAME}`` placeholders the renderer is supposed to substitute.
# Anything matching this pattern after rendering is unresolved.
PLACEHOLDER_RE = re.compile(r"\{([A-Z][A-Z0-9_]+)\}")


def _writer_prompt(level: str, slug: str) -> str:
    plan_path = linear_pipeline.plan_path_for(level, slug)
    plan = linear_pipeline.plan_check(plan_path)
    plan_content = plan_path.read_text(encoding="utf-8")
    context = linear_pipeline.writer_context(
        plan, plan_content, "Knowledge packet stub for prompt-rendering ablation."
    )
    return linear_pipeline.render_phase_prompt(WRITER_TEMPLATE, context)


def _reviewer_prompt(level: str, slug: str, dim: str) -> str:
    plan_path = linear_pipeline.plan_path_for(level, slug)
    plan = linear_pipeline.plan_check(plan_path)
    plan_content = plan_path.read_text(encoding="utf-8")
    return linear_pipeline.render_review_prompt(
        plan,
        plan_content,
        "Generated content stub for prompt-rendering ablation.",
        dim,
    )


@pytest.mark.parametrize(("level", "slug"), REFERENCE_PLANS)
def test_writer_prompt_has_cot_block(level: str, slug: str) -> None:
    rendered = _writer_prompt(level, slug)
    assert rendered.count(WRITER_COT_HEADER) == 1, (
        f"Writer CoT header missing or duplicated for {level}/{slug}"
    )
    for n in (1, 2, 3, 4):
        assert f"\n{n}. **" in rendered, (
            f"Writer CoT step {n} marker missing for {level}/{slug}"
        )


@pytest.mark.parametrize(("level", "slug"), REFERENCE_PLANS)
def test_writer_prompt_has_tier1_discipline(level: str, slug: str) -> None:
    rendered = _writer_prompt(level, slug)
    assert rendered.count(WRITER_TIER1_HEADER) == 1, (
        f"Writer Tier-1 header missing or duplicated for {level}/{slug}"
    )
    for bullet in WRITER_TIER1_BULLETS:
        assert bullet in rendered, (
            f"Writer Tier-1 bullet missing: {bullet!r} for {level}/{slug}"
        )
    # MCP tool callouts must survive into the rendered prompt verbatim
    # so the writer routes verification through MCP, not pre-training.
    for tool in (
        "mcp__sources__verify_words",
        "mcp__sources__check_modern_form",
        "mcp__sources__search_literary",
        "search_definitions",
        "search_style_guide",
        "search_grinchenko_1907",
        "query_pravopys",
        "search_esum",
    ):
        assert tool in rendered, (
            f"Writer Tier-1 MCP-tool reference missing: {tool!r} for {level}/{slug}"
        )


@pytest.mark.parametrize(("level", "slug"), REFERENCE_PLANS)
def test_writer_prompt_has_no_unresolved_placeholders(level: str, slug: str) -> None:
    rendered = _writer_prompt(level, slug)
    leftover = sorted(set(PLACEHOLDER_RE.findall(rendered)))
    assert not leftover, f"Unresolved placeholders for {level}/{slug}: {leftover}"


@pytest.mark.parametrize(("level", "slug"), REFERENCE_PLANS)
@pytest.mark.parametrize("dim", QG_DIMS)
def test_reviewer_prompt_has_cot_block(level: str, slug: str, dim: str) -> None:
    rendered = _reviewer_prompt(level, slug, dim)
    assert rendered.count(REVIEWER_COT_HEADER) == 1, (
        f"Reviewer CoT header missing or duplicated for {level}/{slug} dim={dim}"
    )
    for n in (1, 2, 3, 4):
        assert f"\n{n}. **" in rendered, (
            f"Reviewer CoT step {n} marker missing for {level}/{slug} dim={dim}"
        )
    assert f"Assigned dimension: {dim}" in rendered, (
        f"Assigned-dimension token did not interpolate for {level}/{slug} dim={dim}"
    )


@pytest.mark.parametrize(("level", "slug"), REFERENCE_PLANS)
@pytest.mark.parametrize("dim", QG_DIMS)
def test_reviewer_prompt_has_tier1_audit(level: str, slug: str, dim: str) -> None:
    rendered = _reviewer_prompt(level, slug, dim)
    assert rendered.count(REVIEWER_TIER1_HEADER) == 1, (
        f"Reviewer Tier-1 header missing or duplicated for {level}/{slug} dim={dim}"
    )
    for bullet in REVIEWER_TIER1_BULLETS:
        assert bullet in rendered, (
            f"Reviewer Tier-1 bullet missing: {bullet!r} for {level}/{slug} dim={dim}"
        )
    for flag in (
        "unverified citation",
        "fabricated quote",
        "soviet-framed definition unsupervised",
        "archaic form as modern",
    ):
        assert flag in rendered, (
            f"Reviewer Tier-1 FLAG name missing: {flag!r} for {level}/{slug} dim={dim}"
        )


@pytest.mark.parametrize(("level", "slug"), REFERENCE_PLANS)
@pytest.mark.parametrize("dim", QG_DIMS)
def test_reviewer_prompt_has_no_unresolved_placeholders(
    level: str, slug: str, dim: str
) -> None:
    rendered = _reviewer_prompt(level, slug, dim)
    leftover = sorted(set(PLACEHOLDER_RE.findall(rendered)))
    assert not leftover, (
        f"Unresolved placeholders for {level}/{slug} dim={dim}: {leftover}"
    )


def test_writer_and_reviewer_share_sibir_provenance() -> None:
    writer = WRITER_TEMPLATE.read_text(encoding="utf-8")
    reviewer = REVIEWER_TEMPLATE.read_text(encoding="utf-8")
    # Both prompts cite the same case study so the discipline traces back to a
    # named, reproducible failure rather than a vague "be careful" instruction.
    assert "Сибір case study" in writer
    assert "Сибір case study" in reviewer
    assert "#1661" in writer
    assert "#1661" in reviewer
    assert "#1673" in writer
    assert "#1673" in reviewer
