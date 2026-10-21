"""Claude invocation tests never depend on the installed CLI version (#9903).

A fake ``claude`` that reports an old version sits first on ``PATH``. Tests
that build an invocation must still pass through the shared probe stub in
``tests/conftest.py`` on both Claude module aliases. The gate's own tests,
marked ``real_claude_cli_gate``, keep the real probe and still fail closed.

``kimicc`` copies the gate at first import. That copy calls
``_probe_claude_cli_version`` through the Claude module's globals, so the
order tests import kimicc while the probe is stubbed and while it is real.
A late import must not keep the stub after teardown.
"""

import importlib
import inspect
import os
import sys
from pathlib import Path

import pytest

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
        pytest.fail(f"kimicc was not imported: {missing}")
    return [sys.modules[alias] for alias in KIMICC_ALIASES]


def _clear_claude_probe_caches() -> None:
    for alias in ALIASES:
        module = sys.modules.get(alias)
        probe = getattr(module, "_probe_claude_cli_version", None) if module is not None else None
        cache_clear = getattr(probe, "cache_clear", None)
        if cache_clear is not None:
            cache_clear()


def _import_kimicc() -> None:
    for alias in KIMICC_ALIASES:
        importlib.import_module(alias)


def _assert_kimicc_stubbed(prefix: tuple[str, ...]) -> None:
    from tests.conftest import _STUBBED_CLAUDE_CLI_VERSION

    for module in _kimicc_modules():
        gate = module._ensure_supported_claude_cli_version
        assert gate.__name__ == "_ensure_supported_claude_cli_version"
        assert gate(prefix) == _STUBBED_CLAUDE_CLI_VERSION


def _assert_kimicc_shares_claude_gate() -> None:
    """kimicc holds the Claude function, not a stub captured at import."""
    for kimicc_alias, claude_alias in zip(KIMICC_ALIASES, ALIASES, strict=True):
        shared = sys.modules[claude_alias]._ensure_supported_claude_cli_version
        assert sys.modules[kimicc_alias]._ensure_supported_claude_cli_version is shared


def _assert_every_binding_rejects(prefix: tuple[str, ...]) -> None:
    _clear_claude_probe_caches()
    _assert_kimicc_shares_claude_gate()
    for alias in (*ALIASES, *KIMICC_ALIASES):
        module = sys.modules.get(alias)
        if module is None:
            pytest.fail(f"expected {alias} to be imported")
        with pytest.raises(RuntimeError, match=r"Claude CLI < 2\.1\.116"):
            module._ensure_supported_claude_cli_version(prefix)


def _install_gate(patch: pytest.MonkeyPatch, *, marked: bool) -> None:
    # Pytest refuses a direct fixture call. Drive the same function the autouse
    # fixture wraps, so this process repeats its probe patch.
    import tests.conftest as root_conftest

    install = inspect.unwrap(root_conftest._stub_claude_cli_version_gate)
    install(_GateRequest(marked), patch)


@pytest.mark.real_claude_cli_gate
def test_kimicc_bindings_survive_unmarked_then_marked_and_the_reverse(monkeypatch, old_claude_on_path):
    """Both kimicc aliases follow the shared probe across fixture order (#9903).

    Unmarked then marked imports kimicc while the probe stub is active.
    Marked then unmarked imports kimicc while the real probe is still in place.
    After each teardown, every Claude and kimicc binding rejects 2.1.50.
    """
    prefix = (str(old_claude_on_path),)
    for alias in ALIASES:
        gate = importlib.import_module(alias)._ensure_supported_claude_cli_version
        assert gate.__name__ == "_ensure_supported_claude_cli_version"

    snapshot = _snapshot_kimicc()
    try:
        _unload_kimicc()
        with monkeypatch.context() as patch:
            _install_gate(patch, marked=False)
            _import_kimicc()
            _assert_kimicc_stubbed(prefix)
        _assert_every_binding_rejects(prefix)

        _unload_kimicc()
        with monkeypatch.context() as patch:
            _install_gate(patch, marked=True)
            _import_kimicc()
            _assert_every_binding_rejects(prefix)
        with monkeypatch.context() as patch:
            _install_gate(patch, marked=False)
            _assert_kimicc_stubbed(prefix)
        _assert_every_binding_rejects(prefix)
    finally:
        _restore_kimicc(snapshot)
        _clear_claude_probe_caches()
