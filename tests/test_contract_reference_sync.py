"""Contract-sync pin tests — GH #1431.

The shared module contract at `scripts/build/contracts/module-contract.md`
is the single source of truth for what a module must satisfy. Both the
writer prompt and every per-dimension reviewer prompt MUST reference
this document by path, and both MUST carry the level-calibration clauses
that keep writer and reviewer calibrated on the same axis.

If a future change breaks any of these assertions, CI fails before a
build runs — catching the drift that caused the #1431 round-1 failures
(writer producing correct English-dominant A1 prose, reviewer scoring
it down for "English-dominance"; writer invented dialogue, reviewer
flagged stilted dialogue; etc.).
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRACT_PATH = REPO_ROOT / "scripts" / "build" / "contracts" / "module-contract.md"
WRITER_PROMPT_PATH = REPO_ROOT / "scripts" / "build" / "phases" / "v6-write.md"
REVIEWER_DIR = REPO_ROOT / "scripts" / "build" / "phases" / "v6-review"
CHUNK_BUILDER_PATH = REPO_ROOT / "scripts" / "build" / "v6_build.py"

CONTRACT_RELATIVE_PATH = "scripts/build/contracts/module-contract.md"

REVIEWER_DIMS = (
    "actionable",
    "completeness",
    "decolonization",
    "dialogue",
    "factual",
    "honesty",
    "language",
    "naturalness",
    "plan-adherence",
)


def _reviewer_template(dim: str) -> Path:
    path = REVIEWER_DIR / f"v6-review-{dim}.md"
    assert path.exists(), f"Reviewer template missing: {path}"
    return path


def test_shared_contract_document_exists() -> None:
    assert CONTRACT_PATH.exists(), (
        f"Shared contract missing at {CONTRACT_PATH}. "
        "GH #1431 requires this document to exist as the single source of truth."
    )
    text = CONTRACT_PATH.read_text("utf-8")
    # Sanity — the document must carry the clauses that both sides reference.
    for clause in ("§1", "§2", "§3", "§4", "§5"):
        assert clause in text, f"Contract missing clause marker {clause}"


@pytest.mark.parametrize("phrase", [
    "You have learned",
    "Now it's time",
    "Let's review",
    "In this module",
    "By the end",
    "Here's how to",
    "Try this now",
    "Notice that",
])
def test_contract_carries_section_4_allow_list(phrase: str) -> None:
    """§4 allow-list must appear in the shared contract — it is the authority
    the Naturalness reviewer points at."""
    text = CONTRACT_PATH.read_text("utf-8")
    assert phrase in text, (
        f"§4 allow-list phrase '{phrase}' missing from shared contract. "
        "Contract is the authority for this allow-list; the Naturalness "
        "reviewer references it by path."
    )


def test_writer_prompt_references_shared_contract() -> None:
    text = WRITER_PROMPT_PATH.read_text("utf-8")
    assert CONTRACT_RELATIVE_PATH in text, (
        "Writer prompt must reference scripts/build/contracts/module-contract.md. "
        "GH #1431 pin — do not silently drop the reference."
    )


def test_writer_prompt_carries_section_overflow_protocol() -> None:
    text = WRITER_PROMPT_PATH.read_text("utf-8")
    assert "<section_overflow>" in text, (
        "Writer prompt must carry the <section_overflow> protocol from "
        "contract §2 — silent deferral of contracted items was the Round-1 "
        "colors Section 2 defect."
    )
    assert "proposed_budget_delta" in text, (
        "Writer prompt <section_overflow> block must specify "
        "proposed_budget_delta — the convergence loop reads that field."
    )


def test_writer_prompt_mandates_dialogue_retrieval() -> None:
    text = WRITER_PROMPT_PATH.read_text("utf-8")
    assert "search_sources" in text, (
        "Writer prompt must mandate mcp__sources__search_sources for "
        "corpus-grounded dialogue (contract §3). Invented A1 dialogue "
        "was the Round-1 Dialogue-dim failure."
    )
    # The mandate must be gated on dialogue presence, not universal.
    assert "dialogue_acts" in text, (
        "Writer prompt dialogue-retrieval mandate must reference "
        "dialogue_acts as the gating condition."
    )


def test_writer_prompt_carries_section_4_allow_list() -> None:
    text = WRITER_PROMPT_PATH.read_text("utf-8")
    # At least a representative sample of the allow-list must be present.
    for phrase in ("You have learned", "Now it's time", "Let's review"):
        assert phrase in text, (
            f"Writer prompt must carry §4 allow-list phrase '{phrase}'. "
            "Writer and reviewer allow-lists must match the contract."
        )


@pytest.mark.parametrize("dim", REVIEWER_DIMS)
def test_reviewer_template_references_shared_contract(dim: str) -> None:
    template = _reviewer_template(dim)
    text = template.read_text("utf-8")
    assert CONTRACT_RELATIVE_PATH in text, (
        f"Reviewer template {template.name} must reference "
        f"{CONTRACT_RELATIVE_PATH}. GH #1431 pin."
    )


@pytest.mark.parametrize("dim", REVIEWER_DIMS)
def test_reviewer_template_carries_immersion_rule_placeholder(dim: str) -> None:
    """Every per-dim reviewer prompt must carry the `{IMMERSION_RULE}`
    placeholder so the level-band policy is injected at build time.

    Before GH #1431 this placeholder only existed in the writer prompt —
    reviewers had no access to the level-immersion contract and
    mis-scored English-dominant A1 prose as a pedagogical defect.
    """
    template = _reviewer_template(dim)
    text = template.read_text("utf-8")
    assert "{IMMERSION_RULE}" in text, (
        f"Reviewer template {template.name} must carry {{IMMERSION_RULE}} "
        "placeholder — level-band calibration is injected at build time."
    )


def test_naturalness_reviewer_carries_allow_list_literal() -> None:
    """The Naturalness reviewer is the one that mis-scored standard
    textbook-teacher phrases as LLM-filler in Round-1 colors. It MUST
    carry the §4 allow-list literal so it knows these phrases are
    acceptable."""
    template = _reviewer_template("naturalness")
    text = template.read_text("utf-8")
    for phrase in ("You have learned", "Now it's time", "Let's review"):
        assert phrase in text, (
            f"Naturalness reviewer must carry §4 allow-list phrase "
            f"'{phrase}'. GH #1431 pin — this prevents the Round-1 "
            "Engagement 3/10 miscalibration."
        )


def test_actionable_reviewer_carries_level_calibration() -> None:
    """Actionable (= Pedagogical axis) mis-scored English-dominant A1 prose
    as a pedagogical defect in Round-1 colors. Its prompt must now explicitly
    calibrate scoring against the level-band scaffolding rule."""
    template = _reviewer_template("actionable")
    text = template.read_text("utf-8")
    # Calibration clause must name the band direction.
    assert "A1" in text, (
        "Actionable reviewer must mention A1 level calibration explicitly."
    )
    # It must tell the reviewer NOT to penalize English-dominant prose at A1.
    lowered = text.lower()
    assert "english-dominant" in lowered or "english explanatory" in lowered, (
        "Actionable reviewer must reference English-dominant scaffolding "
        "as contractually correct at A1 early bands — the Round-1 "
        "Pedagogical 4/10 miscalibration pin."
    )


def test_dialogue_reviewer_references_corpus_grounding() -> None:
    template = _reviewer_template("dialogue")
    text = template.read_text("utf-8")
    assert "corpus" in text.lower(), (
        "Dialogue reviewer must reference corpus grounding (§3) — "
        "scoring corpus-grounded dialogue vs invented dialogue was the "
        "Round-1 Dialogue 5/10 calibration gap."
    )


def test_plan_adherence_reviewer_credits_section_overflow() -> None:
    template = _reviewer_template("plan-adherence")
    text = template.read_text("utf-8")
    assert "section_overflow" in text, (
        "Plan Adherence reviewer must treat <section_overflow> as a "
        "positive honesty signal per contract §2, not as a defect."
    )


def test_chunk_builder_carries_shared_contract_clauses() -> None:
    """The chunked writer path (`_build_chunk_prompt`) generates prompts
    inline, not from the v6-write.md template. It must therefore carry
    the same §2 + §3 clauses directly so chunked builds stay calibrated."""
    text = CHUNK_BUILDER_PATH.read_text("utf-8")
    assert CONTRACT_RELATIVE_PATH in text, (
        "Chunk-prompt builder must reference the shared contract path."
    )
    assert "<section_overflow>" in text, (
        "Chunk-prompt builder must carry the §2 overflow protocol."
    )
    assert "search_sources" in text, (
        "Chunk-prompt builder must carry the §3 dialogue-retrieval mandate."
    )


def test_v6_build_injects_immersion_rule_into_reviewer_replacements() -> None:
    """The reviewer replacements dict in v6_build.py MUST include
    {IMMERSION_RULE} so the placeholder resolves at prompt-build time.
    Before GH #1431 only the writer dict had it."""
    text = CHUNK_BUILDER_PATH.read_text("utf-8")
    # Find the reviewer replacements section (near the per-dim review prompt build).
    assert '"{IMMERSION_RULE}"' in text, (
        "v6_build.py must inject {IMMERSION_RULE} into reviewer replacements "
        "so per-dim prompts get the level-band policy at build time."
    )
    # Both writer and reviewer sides must end up with the placeholder populated.
    occurrences = text.count('"{IMMERSION_RULE}"')
    assert occurrences >= 2, (
        "Expected {IMMERSION_RULE} in both writer and reviewer replacement "
        f"dicts; found {occurrences} occurrence(s)."
    )


# ═══════════════════════════════════════════════════════════════════
# §7a canonical anchors pin-tests — 2026-04-23
# ═══════════════════════════════════════════════════════════════════


def test_contract_carries_section_7a_canonical_anchors() -> None:
    """The shared contract must name §7a — the canonical-anchors
    contract. This is the layer that forbids decolonization-harmful
    forms (e.g. «блакитно-жовтий» for the Ukrainian flag) and it's
    referenced by writer, Factual, Honesty, and Language reviewers.
    If anyone drops §7a from the contract, all four prompts become
    under-specified."""
    text = CONTRACT_PATH.read_text("utf-8")
    assert "§7a" in text or "7a " in text, (
        "Contract missing §7a canonical-anchors section. This is "
        "load-bearing for decolonization — see data/canonical_anchors.yaml."
    )
    assert "canonical_anchors.yaml" in text, (
        "Contract §7a must reference the shared registry at "
        "data/canonical_anchors.yaml."
    )


def test_writer_prompt_carries_canonical_anchors_placeholder() -> None:
    """Writer prompt must inject the Ukrainian-language anchors block
    before drafting begins. Prevents the «блакитний»-for-flag class of
    hallucination that GH #1431 v2 surfaced on a1/colors."""
    text = WRITER_PROMPT_PATH.read_text("utf-8")
    assert "{CANONICAL_ANCHORS}" in text, (
        "Writer prompt missing {CANONICAL_ANCHORS} placeholder. "
        "Contract §7a requires the anchor block to reach the writer."
    )


@pytest.mark.parametrize("dim", ["factual", "honesty", "language"])
def test_reviewer_template_carries_canonical_anchors_placeholder(dim: str) -> None:
    """Factual + Honesty + Language reviewers each need the reviewer-
    flavored canonical anchors block so they emit REJECT on any
    forbidden-pattern match."""
    template = _reviewer_template(dim)
    text = template.read_text("utf-8")
    assert "{CANONICAL_ANCHORS_REVIEWER}" in text, (
        f"Reviewer template for {dim!r} missing "
        "{CANONICAL_ANCHORS_REVIEWER} placeholder. Contract §7a "
        "requires this dim to REJECT on anchor violations."
    )


def test_v6_build_injects_canonical_anchors_replacements() -> None:
    """v6_build.py replacements dicts (writer + reviewer) must invoke
    _build_canonical_anchors_replacements so the two keys resolve at
    prompt-build time. Without this, the placeholder literal leaks
    into the prompt and the discipline rules are silently dropped."""
    text = CHUNK_BUILDER_PATH.read_text("utf-8")
    assert "_build_canonical_anchors_replacements" in text, (
        "v6_build.py must import and call _build_canonical_anchors_replacements."
    )
    # The helper must be called from at least the writer AND reviewer
    # replacements blocks — counting `**_build_canonical_anchors_replacements`
    # occurrences catches the case where someone calls it once but forgets
    # the other side.
    splat_occurrences = text.count("**_build_canonical_anchors_replacements()")
    assert splat_occurrences >= 2, (
        "Expected **_build_canonical_anchors_replacements() call in both "
        f"writer and reviewer replacements dicts; found {splat_occurrences}."
    )


def test_canonical_anchors_registry_exists_and_has_required_keys() -> None:
    """Sanity check: the registry file itself is present and has the
    shape all downstream code assumes. Without this, any test that
    touches the helper will fail for a confusing reason later."""
    import yaml as _yaml

    registry_path = REPO_ROOT / "data" / "canonical_anchors.yaml"
    assert registry_path.exists(), (
        f"Canonical anchors registry missing at {registry_path}"
    )
    data = _yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    assert isinstance(data, dict) and "anchors" in data, (
        "Registry must have top-level 'anchors' key"
    )
    assert isinstance(data["anchors"], list) and data["anchors"], (
        "Registry must have a non-empty anchors list"
    )
    # Every anchor needs id + topic_uk + correct for downstream renderers.
    for anchor in data["anchors"]:
        assert {"id", "topic_uk", "correct"}.issubset(anchor), (
            f"Anchor missing required keys: {anchor}"
        )
