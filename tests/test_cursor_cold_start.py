"""Cursor cold-start must fetch /api/rules (#7016)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO / "scripts" / "cursor_cold_start.py"
COLD_START_DOCS = (
    REPO / "agents_extensions/cursor/rules/cold-start.md",
    REPO / ".cursor/rules/cold-start.mdc",
)

spec = importlib.util.spec_from_file_location("cursor_cold_start_under_test", MODULE_PATH)
assert spec and spec.loader
cursor_cold_start = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cursor_cold_start)


class _FakeResp:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> _FakeResp:
        return self

    def __exit__(self, *args: object) -> bool:
        return False

    def read(self) -> bytes:
        return self._payload


def test_cursor_cold_start_fetches_api_rules(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    seen: list[str] = []

    def fake_urlopen(url: str, timeout: float | None = None) -> _FakeResp:
        seen.append(url)
        if url.endswith("/api/state/manifest"):
            return _FakeResp({"rules": {"hash": "abc123def4567890"}})
        if "/api/rules" in url:
            assert "format=json" in url
            return _FakeResp(
                {
                    "hash": "abc123def4567890",
                    "bytes": 12,
                    "sources": ["agents_extensions/shared/rules/operator-expectations.md"],
                    "markdown": "# contract\n",
                }
            )
        if url.endswith("/api/orient"):
            return _FakeResp({"git": {"branch": "main", "head": "deadbeef00"}})
        raise AssertionError(url)

    monkeypatch.setattr(cursor_cold_start.urllib.request, "urlopen", fake_urlopen)
    assert cursor_cold_start.main() == 0
    out = capsys.readouterr().out
    assert any("/api/rules?format=json" in url for url in seen)
    assert "fetched /api/rules" in out
    assert "rules skipped" not in out
    assert "# contract" not in out


def test_cursor_cold_start_docs_require_rules_fetch() -> None:
    for path in COLD_START_DOCS:
        body = path.read_text(encoding="utf-8")
        assert "/api/rules" in body
        assert "Do **not** refetch `/api/rules`" not in body
        assert "/api/rules` — duplicates workspace rules" not in body
        assert "/api/rules` — `AGENTS.md` + `CLAUDE.md` already in workspace" not in body
        assert "`memory/MEMORY.md`" not in body


def test_cursor_cold_start_script_does_not_skip_rules() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert "Skips /api/rules" not in source
    assert "RULES_PATH" in source
    assert "/api/rules?format=json" in source
