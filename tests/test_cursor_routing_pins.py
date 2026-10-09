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

def test_cursor_routing_pins_claude_allowed_if_no_cli(monkeypatch):
    import scripts.agent_runtime.adapters.claude as claude_module
    import scripts.review.model_catalog as mc
    monkeypatch.setattr(claude_module, "_default_claude_bin", lambda: None)
    monkeypatch.setattr(mc, "cursor_pinned_models", lambda *args: ("claude-opus-5-5",))
    assert apply_cursor_model_pins("claude-opus-5-5") == "claude-opus-5-5"

def test_cursor_routing_pins_other_models(monkeypatch):
    import scripts.review.model_catalog as mc
    monkeypatch.setattr(mc, "cursor_pinned_models", lambda *args: ("gpt-6.1-sol",))
    assert apply_cursor_model_pins("composer-2.5") == "composer-2.5"
    assert apply_cursor_model_pins("gpt-6.1-sol") == "gpt-6.1-sol"
def test_cursor_routing_pins_none_returns_none():
    assert apply_cursor_model_pins(None) is None
    assert apply_cursor_model_pins("") is None

def test_model_catalog_import_cycle():
    import subprocess
    import sys
    # Import scripts.review.model_catalog in a fresh interpreter
    result = subprocess.run(
        [sys.executable, "-c", "import scripts.review.model_catalog"],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 0, f"Import cycle or error detected: {result.stderr}"
