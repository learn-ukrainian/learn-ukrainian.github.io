"""Structural assertions for the V7 writer + reviewer prompts.

Locks three coordinated prompt-discipline features:
  - #1673 #1696 visible ``<plan_reasoning>`` mandate for the writer (5 keys)
  - #1673 reviewer CoT reasoning checklist (4 numbered steps)
  - #1661 #1696 Tier-1 verification discipline / audit (5 numbered/lettered
    items, with #1696 heritage-defense extensions)

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
    "## Mandatory visible verification block (emit BEFORE drafting — #1673/#1661)"
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

# The visible <plan_reasoning> block requires these five keys (#1696 Q4).
WRITER_COT_KEYS = (
    "word_budget",
    "plan_vocab",
    "register",
    "teaching_sequence",
    "verification",
)

WRITER_TIER1_BULLETS = (
    "Verify every example word in VESUM",
    "Modern Ukrainian + heritage-defense discipline",
    "Source-citation discipline",
    "Quote attribution discipline",
    "End-of-output gate",
)

REVIEWER_TIER1_BULLETS = (
    "Source-attribution audit (all dims)",
    "Quote verification (all dims)",
    "Sovietization flag (decolonization, naturalness)",
    "Modern Ukrainian + heritage-defense audit (naturalness, decolonization)",
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
    # The mandatory visible-CoT block (#1696 Q4) requires the writer to emit
    # <plan_reasoning> blocks containing five named keys. Each key MUST appear
    # at least once in the rendered prompt's instructions.
    for key in WRITER_COT_KEYS:
        assert f"`{key}`" in rendered, (
            f"Writer visible-CoT key `{key}` missing for {level}/{slug}"
        )
    # The mandate must explicitly forbid hidden-only thinking: telemetry
    # detects writer CoT via the visible <plan_reasoning> tag.
    assert "<plan_reasoning" in rendered, (
        f"Writer <plan_reasoning> tag mandate missing for {level}/{slug}"
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
        # #1696 Q7 — heritage-defense routing through canonical MCP tools
        # (shipped via #1717).
        "mcp__sources__search_heritage",
        "mcp__sources__search_slovnyk_me",
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
        # #1696 Q6 — old "archaic form as modern" flag was replaced by the
        # heritage-defense flag pair (untagged vs misclassified).
        "untagged heritage form",
        "heritage form misclassified",
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


@pytest.mark.parametrize(("level", "slug"), REFERENCE_PLANS)
@pytest.mark.parametrize("dim", QG_DIMS)
def test_reviewer_prompt_requires_evidence_quotes_array(
    level: str, slug: str, dim: str
) -> None:
    """#1696 Q5 — reviewer per-dim schema must demand 3 verbatim quotes plus
    a rubric mapping, not a single paraphrasable evidence string."""
    rendered = _reviewer_prompt(level, slug, dim)
    assert "evidence_quotes" in rendered, (
        f"Reviewer evidence_quotes array requirement missing for "
        f"{level}/{slug} dim={dim}"
    )
    assert "rubric_mapping" in rendered, (
        f"Reviewer rubric_mapping requirement missing for "
        f"{level}/{slug} dim={dim}"
    )
    assert "3 verbatim quotes" in rendered, (
        f"Reviewer 3-quote mandate missing for {level}/{slug} dim={dim}"
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
