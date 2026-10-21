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
    # google (gemma + gemini + agy + antigravity)
    "google": "google",
    "gemma": "google",
    "gemma-4-31b-it": "google",
    "gemini": "google",
    "gemini-3.1-pro": "google",
    "agy": "google",
    "antigravity": "google",
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
    "cursor": "cursor",
    "auto": "cursor",
    "default": "cursor",
    "grok-4": "xai",
    "xai": "xai",
    # formal code-review families
    "composer-2.5": "moonshot",
    "kimi-code/k3": "moonshot",
    "glm-5.3": "zhipu",
    "poolside/laguna-s-2.1": "poolside",
    "poolside/laguna-m.1": "poolside",
    # qwen — restored in Layer-B (was orphaned/None)
    "qwen": "qwen",
    "qwen-2.5": "qwen",
    # fixture sentinel
    "fixture": "fixture",
    "adversarial-fixture": "fixture",
}

# Unmapped models remain UNKNOWN; concrete Composer 2.5 keeps its family.
_UNKNOWN_TOKENS = (
    "composer",
    "cursor-fast",
    "mystery-model",
    "composer-2.4",
    "mystery-reviewer",
    "gravity",
    "anti",
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
    # "gemmate" must NOT be read as gemma; "openrouter" has no openai marker;
    # "gravity" and "anti" alone stay unknown.
    assert model_families.normalize_family("gemmate-thing") is model_families.Family.UNKNOWN
    assert model_families.normalize_family("openrouter") is model_families.Family.UNKNOWN
    assert model_families.normalize_family("gravity") is model_families.Family.UNKNOWN
    assert model_families.normalize_family("anti") is model_families.Family.UNKNOWN


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
    # Cursor Auto has its own family without a concrete pin.
    assert model_families.normalize_lineage_family({"family": "cursor"}) is model_families.Family.CURSOR


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


def test_unknown_writer_refuses_in_layer_b_with_explicit_failure_class() -> None:
    # An UNKNOWN writer cannot satisfy the third-family constraint: route
    # selection returns None, which the runner turns into the explicit
    # LINEAGE_OR_ROUTE failure_class (relation=AUDIT), never acceptance.
    from scripts.audit.layerb_shadow import JudgeRoute, _select_route

    gemini = JudgeRoute("gemini", "gemini-3.1-pro")
    claude = JudgeRoute("claude", "claude-opus-4-6")

    # Cursor Auto can be reviewed by a distinct family.
    assert _select_route((gemini, claude), writer_family="cursor", reviewer_family="deepseek") == gemini
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


# Cursor's runtime reports display names, not slugs (a recorded dispatch carries
# ``resolved_model: "Composer 2.5"``); only that exact display name maps to its slug.
@pytest.mark.parametrize("display", ["Composer 2.5", "composer 2.5", "COMPOSER 2.5", "  Composer   2.5  "])
def test_cursor_display_name_resolves_to_the_concrete_composer_slug(display: str) -> None:
    assert model_families.canonical_cursor_model(display) == "composer-2.5"
    assert model_families.normalize_family(display) is model_families.Family.MOONSHOT
    assert model_families.normalize_lineage_family({"family": "cursor", "resolved_model": display}) is (
        model_families.Family.MOONSHOT
    )


@pytest.mark.parametrize(
    "value",
    [
        "unknown",
        "",
        "   ",
        "Composer",
        "Composer 2",
        "Composer 2.4",
        "Composer 2.50",
        "Composer 2.5 Fast",
        "Composer 3",
    ],
)
def test_cursor_display_name_normaliser_rejects_everything_else(value: str) -> None:
    assert model_families.canonical_cursor_model(value) == value
    assert model_families.normalize_family(value) is model_families.Family.UNKNOWN


@pytest.mark.parametrize(
    "selector",
    [
        "auto",
        "AUTO",
        "Auto",
        " auto ",
        "default",
        "DEFAULT",
        "Default",
        " default ",
        "cursor:auto",
        "CURSOR:AUTO",
        "Cursor:Auto",
        " cursor:auto ",
        "cursor/auto",
        "CURSOR/AUTO",
        "Cursor/Auto",
        " cursor/auto ",
        "cursor:default",
        "CURSOR:DEFAULT",
        "Cursor:Default",
        " cursor:default ",
        "cursor/default",
        "CURSOR/DEFAULT",
        "Cursor/Default",
        " cursor/default ",
    ],
)
def test_cursor_auto_selectors_share_canonical_family(selector):
    from scripts.review.model_catalog import is_cursor_auto_selector

    assert is_cursor_auto_selector(selector)
    assert model_families.normalize_family(selector) is model_families.Family.CURSOR
    assert (
        model_families.normalize_lineage_family({"family": "cursor", "model": selector}) is model_families.Family.CURSOR
    )


@pytest.mark.parametrize("field", ["pin", "pin_slug", "model", "model_id", "writer_model_id"])
@pytest.mark.parametrize("selector", ["auto", "DEFAULT", "cursor:auto", "cursor/default"])
@pytest.mark.parametrize("reported", ["Grok 4.7 256K High", "claude-opus-5-5", None])
def test_explicit_auto_selector_keeps_cursor_despite_runtime_telemetry(field, selector, reported):
    metadata = {"family": "cursor", field: selector, "resolved_model": reported}
    assert model_families.normalize_lineage_family(metadata) is model_families.Family.CURSOR


@pytest.mark.parametrize(
    "selector,expected",
    [
        ("claude-opus-5-5-agy", "anthropic"),
        ("agy:claude-opus-5-5", "anthropic"),
        ("antigravity:claude-opus-5-5", "anthropic"),
        ("agy:gpt-6.1-sol", "openai"),
        ("AGY/CLAUDE-OPUS-5-5[1m]", "anthropic"),
        ("ANTIGRAVITY:GPT-6.1-SOL", "openai"),
        ("gpt-6.1-sol-antigravity", "openai"),
        ("[antigravity]claude-opus-5-5", "anthropic"),
        ("gpt-6.1-sol[agy]", "openai"),
    ],
)
def test_agy_decoration_preserves_concrete_family_in_all_shared_consumers(selector, expected):
    from scripts.review.reviewer_resolver import resolve_author_family, resolve_family

    assert model_families.normalize_family(selector).value == expected
    assert model_families.normalize_lineage_family({"model": selector}).value == expected
    assert llm_reviewer_dispatch.normalize_family(selector) == expected
    assert layerb_shadow.normalize_lineage_family({"pin": selector}) == expected
    assert resolve_family(selector) == expected
    assert resolve_author_family(selector) == expected


@pytest.mark.parametrize(
    "token,expected",
    [
        ("agy", "google"),
        ("ANTIGRAVITY", "google"),
        ("agy:mystery-model", "google"),
        ("antigravity:gemini-3.1-pro-high", "google"),
        ("gemma-agy", "google"),
        ("agy:deepseek-v4.1-flash", "deepseek"),
        ("agy:grok-4.7", "xai"),
        ("agy:composer-2.5", "moonshot"),
        ("agy:glm-5.3", "zhipu"),
        ("agy:laguna-s-2.1", "poolside"),
        ("agy:qwen", "qwen"),
        ("cursor:agy:gpt-6.1-sol", "unknown"),
        ("cursor:auto", "cursor"),
        ("fixture", "fixture"),
        ("adversarial-fixture", "fixture"),
        ("agyx:mystery", "unknown"),
        ("xantigravity:mystery", "unknown"),
        ("mystery:antigravityx", "unknown"),
    ],
)
def test_agy_route_fallback_and_other_family_controls(token, expected):
    assert model_families.normalize_family(token).value == expected


@pytest.mark.parametrize(
    "mixed,expected",
    [
        ("claude-opus-5-5:gpt-6.1-sol", "openai"),
        ("gpt-6.1-sol:claude-opus-5-5", "openai"),
        ("claude-opus-5-5:gemini-3.1-pro-high", "google"),
        ("gemini-3.1-pro-high:gpt-6.1-sol", "google"),
        ("deepseek-v4.1-flash:gemini-3.1-pro-high", "deepseek"),
        ("grok-4.7:claude-opus-5-5", "anthropic"),
    ],
)
def test_agy_does_not_change_existing_mixed_concrete_token_precedence(mixed, expected):
    for selector in (mixed, f"agy:{mixed}", f"{mixed}-antigravity"):
        assert model_families.normalize_family(selector).value == expected


@pytest.mark.parametrize("model,family", [("claude-opus-5-5", "anthropic"), ("gpt-6.1-sol", "openai")])
def test_agy_decoration_does_not_override_conflicting_lineage_or_author_family(model, family):
    from scripts.review.reviewer_resolver import resolve_author_family

    decorated = f"agy:{model}"
    assert model_families.normalize_lineage_family({"family": "google", "pin": decorated}).value == "unknown"
    assert model_families.normalize_lineage_family({"family": family, "pin": decorated}).value == family
    assert resolve_author_family(decorated, "google") == "conflict"
    assert resolve_author_family(decorated, family) == family
