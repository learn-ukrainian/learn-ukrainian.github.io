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


def test_cursor_display_name_normaliser_handles_none() -> None:
    assert model_families.canonical_cursor_model(None) == ""
    assert model_families.normalize_family(None) is model_families.Family.UNKNOWN


@pytest.mark.parametrize("display", ["Grok 4.7 256K High", "grok 4.7 256k high", " Grok\t4.7  256K   High "])
def test_cursor_grok_high_display_name_maps_to_the_concrete_model(display: str) -> None:
    """#9488: the Cursor review seat's runtime report names the catalog model."""
    assert model_families.canonical_cursor_model(display) == "grok-4.7"
    assert model_families.normalize_family(display) is model_families.Family.XAI


@pytest.mark.parametrize(
    "display",
    [
        "Grok 4.7 256K High Fast",
        "Grok 4.7 256K Medium",
        "Grok 4.7 256K Extra High",
        "Grok 4.7 High",
        "Grok 4.6 256K High",
        "Gro\u212a 4.7 256K High",  # KELVIN SIGN folds to "k" under Unicode IGNORECASE
        "Grok 4.7\u00a0256K High",  # no-break space
        "Grok 4.7 256K High\n",
    ],
)
def test_other_grok_display_names_are_not_rewritten(display: str) -> None:
    assert model_families.canonical_cursor_model(display) == display


@pytest.mark.parametrize(
    "display,expected",
    [
        ("Grok 4.7 256K High Fast", model_families.Family.XAI),
        ("Claude Fable 5 300K High", model_families.Family.ANTHROPIC),
        ("composer-2.5", model_families.Family.MOONSHOT),
        ("composer-2.5-fast", model_families.Family.MOONSHOT),
    ],
)
def test_other_cursor_display_names_resolve_as_before(display: str, expected: model_families.Family) -> None:
    assert model_families.canonical_cursor_model(display) == display
    assert model_families.normalize_family(display) is expected


@pytest.mark.parametrize(
    "value",
    [
        "Compo\u017fer 2.5",  # LATIN SMALL LETTER LONG S folds to "s" under Unicode IGNORECASE
        "Composer 2.5".replace("o", "\u043e", 1),  # Cyrillic o
        "Composer 2.5".replace("o", "\u03bf", 1),  # Greek omicron
        "Composer 2.5".replace("C", "\u0421", 1),  # Cyrillic Es
        "\uff23omposer 2.5",  # full-width C
        "Composer \uff12.\uff15",  # full-width digits
        "\uff43\uff4f\uff4d\uff50\uff4f\uff53\uff45\uff52 2.5",  # full-width word
        "Composer\u00a02.5",  # no-break space
        "Composer\u20032.5",  # em space
        "Composer\u200b 2.5",  # zero-width space
        "Composer \u200b2.5",
        "Composer\n2.5",
        "Composer 2.5\n",
        "\nComposer 2.5",
        "Composer 2.5\x00",
        "Composer\x002.5",
        "Composer 2.5\u212a",  # KELVIN SIGN
        "Composer\r2.5",
    ],
)
def test_cursor_display_name_match_is_ascii_only(value: str) -> None:
    assert model_families.canonical_cursor_model(value) == value
    assert model_families.normalize_family(value) is model_families.Family.UNKNOWN


@pytest.mark.parametrize("display", ["Composer\t2.5", "composer \t 2.5", "\tComposer 2.5 ", "cOmPoSeR     2.5"])
def test_cursor_display_name_accepts_ascii_space_and_tab_runs(display: str) -> None:
    assert model_families.canonical_cursor_model(display) == "composer-2.5"


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
