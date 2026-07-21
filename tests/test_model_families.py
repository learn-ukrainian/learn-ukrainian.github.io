"""Tests for the canonical model-family vocabulary (issues #5385, #5293).

The route-refusal chain used to carry TWO divergent family vocabularies
(live dispatcher vs Layer-B). They now both consume the single
``scripts.audit.model_families`` module. These tests pin:

* the canonical token→family mapping and the explicit UNKNOWN/FIXTURE members;
* that both former call sites AGREE on every previously-recognized token;
* that an UNKNOWN writer propagates to an explicit refusal, never acceptance
  or a crash, on BOTH layers.
* that formal code-review resolver families consume the same vocabulary.
"""

from __future__ import annotations

import pytest

from scripts.audit import layerb_shadow, llm_reviewer_dispatch, model_families

# Every previously-recognized token, mapped to the unified family it must
# normalize to in BOTH layers. "previously-recognized" = the union of tokens
# the two old normalizers ever returned a non-raw answer for.
_TOKEN_TO_FAMILY = {
    # deepseek
    "deepseek": "deepseek",
    "deepseek-v4-pro": "deepseek",
    "openrouter/deepseek/deepseek-v4-flash": "deepseek",
    # google (gemma + gemini + agy)
    "google": "google",
    "gemma": "google",
    "gemma-4-31b-it": "google",
    "gemini": "google",
    "gemini-3.1-pro": "google",
    "agy": "google",
    # openai (codex + gpt + openai)
    "openai": "openai",
    "gpt-5.6-terra": "openai",
    "codex": "openai",
    "gpt": "openai",
    # anthropic (claude + opus + sonnet)
    "anthropic": "anthropic",
    "claude": "anthropic",
    "claude-opus-4-6": "anthropic",
    "opus": "anthropic",
    "sonnet": "anthropic",
    # xai (grok) — SEPARATE from cursor
    "grok": "xai",
    "grok-4": "xai",
    "xai": "xai",
    # formal code-review families
    "composer-2.5": "moonshot",
    "kimi-code/k3": "moonshot",
    "glm-5.2": "zhipu",
    "poolside/laguna-s-2.1": "poolside",
    "poolside/laguna-m.1": "poolside",
    # qwen — restored in Layer-B (was orphaned/None)
    "qwen": "qwen",
    "qwen-2.5": "qwen",
    # fixture sentinel
    "fixture": "fixture",
    "adversarial-fixture": "fixture",
}

# Tokens that are UNKNOWN under the unified vocabulary. cursor-Auto is the
# routing decision (2026-07-17); unpinned Cursor/Composer remains UNKNOWN even
# though the concrete Composer 2.5 model is recognized for formal review.
_UNKNOWN_TOKENS = (
    "cursor",
    "composer",
    "auto",
    "cursor-fast",
    "mystery-model",
    "composer-2.4",
    "mystery-reviewer",
)


def test_canonical_normalize_family_maps_every_recognized_token() -> None:
    for token, expected in _TOKEN_TO_FAMILY.items():
        assert model_families.normalize_family(token).value == expected, token


def test_canonical_normalize_family_unknown_is_first_class() -> None:
    for token in _UNKNOWN_TOKENS:
        assert model_families.normalize_family(token) is model_families.Family.UNKNOWN, token
    assert model_families.normalize_family("") is model_families.Family.UNKNOWN
    assert model_families.normalize_family(None) is model_families.Family.UNKNOWN


def test_canonical_word_boundary_prevents_false_matches() -> None:
    # "gemmate" must NOT be read as gemma; "openrouter" has no openai marker.
    assert model_families.normalize_family("gemmate-thing") is model_families.Family.UNKNOWN
    assert model_families.normalize_family("openrouter") is model_families.Family.UNKNOWN


def test_canonical_lineage_prefers_pin_over_cursor_seat() -> None:
    # cursor seat + pinned model -> the pin's family.
    assert model_families.normalize_lineage_family({"family": "cursor", "pin": "grok-4"}) is model_families.Family.XAI
    assert (
        model_families.normalize_lineage_family({"family": "cursor", "pin": "claude-opus-4-6"})
        is model_families.Family.ANTHROPIC
    )
    assert (
        model_families.normalize_lineage_family({"family": "cursor", "pin": "composer-2.5"})
        is model_families.Family.MOONSHOT
    )
    # cursor-Auto (no pin) is UNKNOWN.
    assert model_families.normalize_lineage_family({"family": "cursor"}) is model_families.Family.UNKNOWN


def test_canonical_lineage_ambiguous_concrete_signals_fail_closed() -> None:
    assert (
        model_families.normalize_lineage_family({"family": "google", "pin": "openrouter/deepseek/deepseek-v4-pro"})
        is model_families.Family.UNKNOWN
    )


@pytest.mark.parametrize("token", sorted(_TOKEN_TO_FAMILY))
def test_both_consumption_layers_agree_on_every_recognized_token(token: str) -> None:
    expected = _TOKEN_TO_FAMILY[token]
    live = llm_reviewer_dispatch.normalize_family(token)
    layer_b = layerb_shadow.normalize_lineage_family(token)
    assert live == expected, (token, "live", live)
    assert layer_b == expected, (token, "layer-b", layer_b)


@pytest.mark.parametrize("token", _UNKNOWN_TOKENS)
def test_both_consumption_layers_agree_on_unknown(token: str) -> None:
    # UNKNOWN collapses to None at the compatibility seam in BOTH layers.
    assert llm_reviewer_dispatch.normalize_family(token) is None, token
    assert layerb_shadow.normalize_lineage_family(token) is None, token


def test_unknown_writer_refuses_in_layer_b_with_explicit_failure_class() -> None:
    # An UNKNOWN writer cannot satisfy the third-family constraint: route
    # selection returns None, which the runner turns into the explicit
    # LINEAGE_OR_ROUTE failure_class (relation=AUDIT), never acceptance.
    from scripts.audit.layerb_shadow import JudgeRoute, _select_route

    gemini = JudgeRoute("gemini", "gemini-3.1-pro")
    claude = JudgeRoute("claude", "claude-opus-4-6")

    # cursor-Auto writer -> UNKNOWN -> no satisfiable route.
    assert _select_route((gemini, claude), writer_family="cursor", reviewer_family="deepseek") is None
    # arbitrary unrecognized writer -> UNKNOWN -> no satisfiable route.
    assert _select_route((gemini, claude), writer_family="mystery-reviewer", reviewer_family="deepseek") is None


def test_unknown_writer_refuses_on_live_path_with_lineage_error() -> None:
    # On the live path an UNKNOWN family resolves to lineage.family=None, which
    # validate_cross_family turns into an explicit ReviewerLineageError refusal
    # (never acceptance, never a silent pass).
    lineage = llm_reviewer_dispatch.AuthorLineage(family=None, source="test")
    with pytest.raises(llm_reviewer_dispatch.ReviewerLineageError):
        llm_reviewer_dispatch.validate_cross_family(llm_reviewer_dispatch.GEMMA_SURFACE_ROUTE, lineage)


def test_self_review_still_blocks_when_families_match() -> None:
    # Behavior preservation: equal families still raise ReviewerSelfReviewError.
    lineage = llm_reviewer_dispatch.AuthorLineage(family="google", source="test")
    with pytest.raises(llm_reviewer_dispatch.ReviewerSelfReviewError):
        llm_reviewer_dispatch.validate_cross_family(llm_reviewer_dispatch.GEMMA_SURFACE_ROUTE, lineage)
