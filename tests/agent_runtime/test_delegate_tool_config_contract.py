"""Every dispatch adapter must accept the tool_config keys delegate.py adds.

The key list is parsed from ``_run_worker`` so a new read-only or review
assignment fails this contract until the adapters accept it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.agent_runtime.adapters.agy import AgyAdapter, _agy_version
from tests.agent_runtime.agy_hook_helpers import register_agy_hooks

# Placeholder per key delegate.py assigns. An unmapped key still gets a
# value so a new read-only or review assignment is sent, not dropped.

# Failures that are fixture preconditions, not key rejection. Any other
# exception fails the contract, including ones that omit "unsupported tool_config".


# Dispatch adapters that resolve a CLI via PATH. Stubs keep the contract
# independent of whichever binaries the host happens to have installed.
_CLI_STUBS = (
    "agy",
    "agent",
    "claude",
    "codex",
    "cursor-agent",
    "gemini",
    "grok",
    "kimi",
    "muse",
    "npx",
    "opencode",
)


# Stub bodies for CLIs whose adapter probes the binary before building a plan.
# agy must report a version at or above the background-wait floor (#8502).
_CLI_STUB_BODIES: dict[str, str] = {
    "agy": 'if [ "$1" = "--version" ]; then echo "agy 1.2.9"; fi\nexit 0\n',
    "muse": 'if [ "$1" = "--version" ]; then echo "muse fixture"; fi\nexit 0\n',
}


def _install_cli_stubs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    bin_dir = tmp_path / "cli-stubs"
    bin_dir.mkdir()
    for name in _CLI_STUBS:
        stub = bin_dir / name
        stub.write_text("#!/bin/sh\n" + _CLI_STUB_BODIES.get(name, "exit 0\n"), encoding="utf-8")
        stub.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))
    # The probe is cached per path, and pytest reuses tmp dir names.
    _agy_version.cache_clear()
    return bin_dir


@pytest.mark.parametrize(
    ("stub_body", "code"),
    [("exit 0\n", "agy_version_unverified"), ('echo "agy 1.2.8"\n', "agy_version_unsupported")],
)
def test_agy_stub_without_supported_version_is_still_refused(stub_body, code, tmp_path, monkeypatch) -> None:
    """The version-reporting stub above must not mask the agy >= 1.2.9 gate."""
    bin_dir = _install_cli_stubs(tmp_path, monkeypatch)
    (bin_dir / "agy").write_text("#!/bin/sh\n" + stub_body, encoding="utf-8")
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    home = tmp_path / "ordinary-home"
    monkeypatch.setenv("HOME", str(home))
    register_agy_hooks(checkout, home=home)

    with pytest.raises(ValueError, match=code):
        AgyAdapter().build_invocation(
            prompt="read-only contract",
            mode="read-only",
            cwd=checkout,
            model=None,
            task_id="tool-config-contract",
            session_id=None,
            tool_config={},
        )
