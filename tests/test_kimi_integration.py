"""Closed-registry integration coverage for the native Kimi lane."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))



def test_kimi_background_worker_refuses_before_any_processor(monkeypatch):
    from scripts.ai_agent_bridge import _ask_lifecycle, _messaging

    monkeypatch.setattr(_messaging, "read_message", lambda *_a, **_k: None)
    with pytest.raises(ValueError, match="KIMI CODING-ONLY"):
        _ask_lifecycle._process_target(12, "kimi", {"new_session": True, "no_timeout": True, "review": True})
