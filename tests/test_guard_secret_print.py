"""Unit tests for the secret-print guard hook (#M-5 / #1908).

Exercises the narrow decision logic in
``agents_extensions/shared/hooks/guard-secret-print.py``:

  * clear secret dump shapes are blocked,
  * key-only/count/presence checks are allowed,
  * quoted command-message bodies do not trigger substring false positives, and
  * the LEARN_UK_SECRETS_OK=1 override is honored.

The hook filename has hyphens, so it is loaded by path via importlib. ``main``
is guarded by ``__name__ == "__main__"``, so import has no side effects.
"""

from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = REPO_ROOT / "agents_extensions/shared" / "hooks" / "guard-secret-print.py"


def _load_hook():
    spec = importlib.util.spec_from_file_location("guard_secret_print", HOOK_PATH)
    assert spec and spec.loader, f"could not load hook at {HOOK_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guard = _load_hook()


def _run(monkeypatch, command: str, *, env_override: bool = False) -> int:
    payload = json.dumps({"tool_input": {"command": command}})
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    if env_override:
        monkeypatch.setenv("LEARN_UK_SECRETS_OK", "1")
    else:
        monkeypatch.delenv("LEARN_UK_SECRETS_OK", raising=False)
    return guard.main()


@pytest.mark.parametrize(
    "cmd",
    [
        "env",
        "cat ~/.aws/credentials",
        "grep KEY .envrc",
        "echo $GH_TOKEN",
    ],
)
def test_secret_dump_shapes_blocked(monkeypatch, capsys, cmd):
    assert _run(monkeypatch, cmd) == 2
    err = capsys.readouterr().err
    assert "BLOCKED by guard-secret-print (#M-5)" in err
    assert "cut -d= -f1" in err
    assert "jq keys" in err
    assert '[ -n "${X:-}" ]' in err
    assert "LEARN_UK_SECRETS_OK=1" in err


@pytest.mark.parametrize(
    "cmd",
    [
        "env | cut -d= -f1",
        '[ -n "${X:-}" ] && echo SET',
        "cat README.md",
        "jq keys",
        'git commit -m "notes: gh pr merge --admin and echo $GH_TOKEN"',
        "LEARN_UK_SECRETS_OK=1 env",
    ],
)
def test_safe_commands_allowed(monkeypatch, cmd):
    assert _run(monkeypatch, cmd) == 0


def test_environment_override_allowed(monkeypatch):
    assert _run(monkeypatch, "env", env_override=True) == 0


def test_single_quoted_secret_var_literal_allowed(monkeypatch):
    assert _run(monkeypatch, "echo '$GH_TOKEN'") == 0
