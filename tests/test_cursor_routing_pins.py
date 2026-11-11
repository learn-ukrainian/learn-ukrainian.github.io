import pytest

from scripts.review.model_catalog import ModelCatalogError, apply_cursor_model_pins


def test_cursor_routing_pins_refuse_the_retired_grok_pins():
    """Grok 4.7 was Cursor's only pin; every Grok model is retired (GROK-CANCEL-1110)."""
    for model in ("grok-4.7", "grok-4.7-high"):
        with pytest.raises(ModelCatalogError, match=r"CURSOR_MODEL_NOT_APPROVED.*cursor_no_approved_model_pin"):
            apply_cursor_model_pins(model)

def test_cursor_routing_pins_grok_refusal():
    with pytest.raises(ModelCatalogError, match="CURSOR_MODEL_NOT_APPROVED"):
        apply_cursor_model_pins("grok-4.7[fast]")
    with pytest.raises(ModelCatalogError, match="CURSOR_MODEL_NOT_APPROVED"):
        apply_cursor_model_pins("grok-4.7-build")

def test_cursor_routing_pins_claude_refusal(monkeypatch):
    import scripts.agent_runtime.adapters.claude as claude_module
    monkeypatch.setattr(claude_module, "_default_claude_bin", lambda: "/usr/bin/claude")
    with pytest.raises(ModelCatalogError, match="CURSOR_CLAUDE_REFUSED"):
        apply_cursor_model_pins("claude-opus-5-5")


def test_cursor_routing_pins_no_native_cli_does_not_bypass_allowlist(monkeypatch):
    import scripts.agent_runtime.adapters.claude as claude_module
    monkeypatch.setattr(claude_module, "_default_claude_bin", lambda: None)
    with pytest.raises(ModelCatalogError, match="CURSOR_MODEL_NOT_APPROVED"):
        apply_cursor_model_pins("claude-opus-5-5")

def test_cursor_routing_pins_claude_allowed_if_no_cli(monkeypatch):
    import scripts.agent_runtime.adapters.claude as claude_module
    import scripts.review.model_catalog as mc
    monkeypatch.setattr(claude_module, "_default_claude_bin", lambda: None)
    monkeypatch.setattr(mc, "cursor_pinned_models", lambda *args: ("claude-opus-5-5",))
    assert apply_cursor_model_pins("claude-opus-5-5") == "claude-opus-5-5"
