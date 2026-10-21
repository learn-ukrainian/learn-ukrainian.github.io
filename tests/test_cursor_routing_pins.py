import pytest

from scripts.review.model_catalog import ModelCatalogError, apply_cursor_model_pins


def test_cursor_routing_pins_grok_rewrite():
    assert apply_cursor_model_pins("grok-4.7") == "grok-4.7-high"
    assert apply_cursor_model_pins("grok-4.7-high") == "grok-4.7-high"

def test_cursor_routing_pins_grok_refusal():
    with pytest.raises(ModelCatalogError, match="CURSOR_UNATTESTED_GROK_VARIANT"):
        apply_cursor_model_pins("grok-4.7[fast]")
    with pytest.raises(ModelCatalogError, match="CURSOR_UNATTESTED_GROK_VARIANT"):
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
