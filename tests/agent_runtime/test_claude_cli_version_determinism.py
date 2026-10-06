"""Claude invocation tests never depend on the installed CLI version (#9903).

A fake ``claude`` that reports an old version sits first on ``PATH``. Tests
that build an invocation must still pass through the shared gate stub in
``tests/conftest.py`` on both module aliases; the gate's own tests, marked
``real_claude_cli_gate``, keep the real gate and still fail closed.

``kimicc`` copies the gate at first import. The order test drops both kimicc
aliases and drives that fixture through an unmarked run followed by a marked
one, then the reverse, in this process.
"""

import importlib
import inspect
import os
import sys
from pathlib import Path

import pytest

from scripts.agent_runtime.adapters.claude import ClaudeAdapter

# The bare ``agent_runtime`` alias needs ``scripts/`` on the path (as test_agent_runtime.py does).
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

OLD_VERSION = "2.1.50"
ALIASES = ("scripts.agent_runtime.adapters.claude", "agent_runtime.adapters.claude")
KIMICC_ALIASES = ("scripts.agent_runtime.adapters.kimicc", "agent_runtime.adapters.kimicc")
_MISSING = object()


@pytest.fixture
def old_claude_on_path(tmp_path, monkeypatch):
    """Put a fake ``claude`` reporting an old version first on ``PATH``."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "claude"
    fake.write_text(f'#!/bin/sh\necho "{OLD_VERSION} (Claude Code)"\n', encoding="utf-8")
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")
    return fake


def _build(adapter, cwd, fake):
    return adapter.build_invocation(
        prompt="hello",
        mode="read-only",
        cwd=cwd,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"cmd_prefix": [str(fake)]},
    )


def test_invocation_builds_with_old_cli_on_path(tmp_path, old_claude_on_path):
    plan = _build(ClaudeAdapter(), tmp_path, old_claude_on_path)
    assert plan.cmd[0] == str(old_claude_on_path)


@pytest.mark.parametrize("alias", ALIASES)
def test_gate_is_stubbed_on_every_alias(alias, old_claude_on_path):
    module = importlib.import_module(alias)
    assert module._ensure_supported_claude_cli_version((str(old_claude_on_path),)) is not None
    assert module._ensure_supported_claude_cli_version((str(old_claude_on_path),)) >= (2, 1, 116)


@pytest.mark.real_claude_cli_gate
@pytest.mark.parametrize("alias", ALIASES)
def test_real_gate_still_rejects_old_cli_on_every_alias(alias, old_claude_on_path):
    module = importlib.import_module(alias)
    with pytest.raises(RuntimeError, match=r"Claude CLI < 2\.1\.116"):
        module._ensure_supported_claude_cli_version((str(old_claude_on_path),))


class _GateNode:
    """Stand-in for ``request.node`` so the shared fixture can run twice here."""

    def __init__(self, marked: bool) -> None:
        self._marked = marked

    def get_closest_marker(self, name: str):
        if self._marked and name == "real_claude_cli_gate":
            return object()
        return None


class _GateRequest:
    def __init__(self, marked: bool) -> None:
        self.node = _GateNode(marked)

    def addfinalizer(self, _func) -> None:
        return None


def _snapshot_kimicc() -> list[tuple]:
    snapshot = []
    for alias in KIMICC_ALIASES:
        parent_name, child = alias.rsplit(".", 1)
        parent = sys.modules.get(parent_name)
        attr = getattr(parent, child, _MISSING) if parent is not None else _MISSING
        snapshot.append((alias, sys.modules.get(alias), parent, child, attr))
    return snapshot


def _unload_kimicc() -> None:
    """Drop both kimicc modules so the next import binds the gate again."""
    for alias in KIMICC_ALIASES:
        sys.modules.pop(alias, None)
        parent_name, child = alias.rsplit(".", 1)
        parent = sys.modules.get(parent_name)
        if parent is not None and hasattr(parent, child):
            delattr(parent, child)


def _restore_kimicc(snapshot: list[tuple]) -> None:
    _unload_kimicc()
    for alias, module, parent, child, attr in snapshot:
        if module is not None:
            sys.modules[alias] = module
        if parent is None:
            continue
        if attr is _MISSING:
            if hasattr(parent, child):
                delattr(parent, child)
        else:
            setattr(parent, child, attr)


def _kimicc_modules() -> list:
    missing = [alias for alias in KIMICC_ALIASES if alias not in sys.modules]
    if missing:
        pytest.fail(f"gate fixture did not import {missing}")
    return [sys.modules[alias] for alias in KIMICC_ALIASES]


def _clear_claude_probe_caches() -> None:
    for alias in ALIASES:
        module = sys.modules.get(alias)
        probe = getattr(module, "_probe_claude_cli_version", None) if module is not None else None
        if probe is not None:
            probe.cache_clear()


def _assert_kimicc_stubbed(prefix: tuple[str, ...]) -> None:
    from tests.conftest import _STUBBED_CLAUDE_CLI_VERSION

    for module in _kimicc_modules():
        assert module._ensure_supported_claude_cli_version(prefix) == _STUBBED_CLAUDE_CLI_VERSION


def _assert_kimicc_rejects_old_cli(prefix: tuple[str, ...]) -> None:
    _clear_claude_probe_caches()
    for module in _kimicc_modules():
        with pytest.raises(RuntimeError, match=r"Claude CLI < 2\.1\.116"):
            module._ensure_supported_claude_cli_version(prefix)


def _install_gate(patch: pytest.MonkeyPatch, *, marked: bool) -> None:
    # Pytest refuses a direct fixture call. Drive the same function the autouse
    # fixture wraps, so this process repeats its import-then-patch order.
    import tests.conftest as root_conftest

    install = inspect.unwrap(root_conftest._stub_claude_cli_version_gate)
    install(_GateRequest(marked), patch)


@pytest.mark.real_claude_cli_gate
def test_kimicc_bindings_survive_unmarked_then_marked_and_the_reverse(monkeypatch, old_claude_on_path):
    """Both kimicc aliases follow the shared gate across fixture order (#9903).

    Unmarked then marked is the order that kept the stub: a first import copied
    the patched Claude gate, and teardown restored that copy. Marked then
    unmarked imports kimicc while the real gate is still in place.
    """
    prefix = (str(old_claude_on_path),)
    for alias in ALIASES:
        gate = importlib.import_module(alias)._ensure_supported_claude_cli_version
        assert gate.__name__ == "_ensure_supported_claude_cli_version"

    snapshot = _snapshot_kimicc()
    saved_gates = {}
    for alias in ALIASES:
        module = importlib.import_module(alias)
        saved_gates[module] = module._ensure_supported_claude_cli_version
    try:
        _unload_kimicc()
        with monkeypatch.context() as patch:
            _install_gate(patch, marked=False)
            _assert_kimicc_stubbed(prefix)
        _assert_kimicc_rejects_old_cli(prefix)

        _unload_kimicc()
        with monkeypatch.context() as patch:
            _install_gate(patch, marked=True)
            _assert_kimicc_rejects_old_cli(prefix)
        with monkeypatch.context() as patch:
            _install_gate(patch, marked=False)
            _assert_kimicc_stubbed(prefix)
        _assert_kimicc_rejects_old_cli(prefix)
    finally:
        for module, gate in saved_gates.items():
            module._ensure_supported_claude_cli_version = gate
        _restore_kimicc(snapshot)
        _clear_claude_probe_caches()
