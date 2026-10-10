"""Ambient credential-shaped names are absent inside every test.

``tests/conftest.py`` drops names ending in ``_API_KEY``, ``_TOKEN`` or
``_SECRET`` before each test. A subprocess pytest, started with those names
set and with cwd at the repo root, loads the real conftest and checks the
result. Failure text names variables and never prints their values.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SENTINEL = "sentinel-not-a-real-value"
SET_INSIDE = "set-inside-the-test"
_STRIPPED = (
    "ZZ_STRIP_PROBE_API_KEY",
    "ZZ_STRIP_PROBE_TOKEN",
    "ZZ_STRIP_PROBE_SECRET",
    "zz_strip_probe_api_key",
)
_PLAIN = "ZZ_STRIP_PROBE_PLAIN"
_PLURAL = "ZZ_STRIP_PROBE_TOKENS"

_PROBE = textwrap.dedent(
    """\
    import os

    _ABSENT = (
        "ZZ_STRIP_PROBE_API_KEY",
        "ZZ_STRIP_PROBE_TOKEN",
        "ZZ_STRIP_PROBE_SECRET",
        "zz_strip_probe_api_key",
    )
    _PLAIN = "ZZ_STRIP_PROBE_PLAIN"
    _PLURAL = "ZZ_STRIP_PROBE_TOKENS"
    _SENTINEL = "sentinel-not-a-real-value"
    _SET_INSIDE = "set-inside-the-test"


    def test_suffixes_absent_and_unrelated_names_survive(monkeypatch):
        visible = [name for name in _ABSENT if name in os.environ]
        if visible:
            raise AssertionError("credential-shaped names still set: " + ", ".join(visible))
        if os.environ.get(_PLAIN) != _SENTINEL:
            raise AssertionError("unrelated name was stripped or changed")
        if os.environ.get(_PLURAL) != _SENTINEL:
            raise AssertionError("plural TOKENS name was stripped or changed")
        monkeypatch.setenv("ZZ_STRIP_PROBE_API_KEY", _SET_INSIDE)
        if os.environ.get("ZZ_STRIP_PROBE_API_KEY") != _SET_INSIDE:
            raise AssertionError("monkeypatch.setenv value was not visible")


    def test_setenv_value_is_gone_afterwards():
        if "ZZ_STRIP_PROBE_API_KEY" in os.environ:
            raise AssertionError("value set inside the previous test is still set")
        if os.environ.get(_PLAIN) != _SENTINEL or os.environ.get(_PLURAL) != _SENTINEL:
            raise AssertionError("unrelated names did not survive the next test")
    """
)

_PROBE_CONFTEST = textwrap.dedent(
    """\
    def pytest_sessionfinish(session, exitstatus):
        import os
        from pathlib import Path

        value = os.environ.get("ZZ_STRIP_PROBE_API_KEY")
        state = "sentinel" if value == "sentinel-not-a-real-value" else "other" if value else "absent"
        Path(os.environ["ZZ_STRIP_PROBE_AFTER"]).write_text(state, encoding="utf-8")
    """
)


def test_ambient_credential_env_is_stripped_for_every_test() -> None:
    """A real conftest session hides credential suffixes and restores them after."""
    tests_dir = REPO_ROOT / "tests"
    descriptor, after_name = tempfile.mkstemp(prefix="zz-strip-after-")
    os.close(descriptor)
    after_path = Path(after_name)
    try:
        with tempfile.TemporaryDirectory(prefix="_zz_strip_probe_", dir=tests_dir) as raw:
            probe_dir = Path(raw)
            probe = probe_dir / "test_probe.py"
            probe.write_text(_PROBE, encoding="utf-8")
            (probe_dir / "conftest.py").write_text(_PROBE_CONFTEST, encoding="utf-8")
            env = os.environ.copy()
            env.pop("PYTEST_CURRENT_TEST", None)
            env["ZZ_STRIP_PROBE_AFTER"] = str(after_path)
            for name in (*_STRIPPED, _PLAIN, _PLURAL):
                env[name] = SENTINEL
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(probe.relative_to(REPO_ROOT)),
                    "-q",
                    "--tb=short",
                    "-p",
                    "no:cacheprovider",
                    "-o",
                    "addopts=",
                    "--rootdir",
                    str(REPO_ROOT),
                ],
                cwd=REPO_ROOT,
                env=env,
                capture_output=True,
                text=True,
                timeout=90,
                check=False,
            )
            assert result.returncode == 0, result.stdout + "\n" + result.stderr
            assert after_path.read_text(encoding="utf-8") == "sentinel"
    finally:
        after_path.unlink(missing_ok=True)


def test_suffix_match_ignores_case_and_plural_tokens() -> None:
    """Suffix matching is case-insensitive and does not treat ``_TOKENS`` as ``_TOKEN``."""
    from tests.conftest import _is_credential_shaped_env_name

    assert _is_credential_shaped_env_name("ZZ_STRIP_PROBE_API_KEY")
    assert _is_credential_shaped_env_name("zz_strip_probe_api_key")
    assert _is_credential_shaped_env_name("Zz_Strip_Probe_Secret")
    assert _is_credential_shaped_env_name("ZZ_STRIP_PROBE_TOKEN")
    assert not _is_credential_shaped_env_name("ZZ_STRIP_PROBE_TOKENS")
    assert not _is_credential_shaped_env_name("ZZ_STRIP_PROBE_PLAIN")
    assert not _is_credential_shaped_env_name("TOKEN")
    assert not _is_credential_shaped_env_name("API_KEY")


def test_suite_owned_tokens_are_published_values_not_inherited_names() -> None:
    """The cursor guard's minted token is what the strip puts back."""
    import sys

    from tests.conftest import _suite_owned_credential_env
    from tests.cursor_exec_tripwire import SESSION_TOKEN_ENV, session_token

    restores = dict(_suite_owned_credential_env())
    assert session_token
    assert restores[SESSION_TOKEN_ENV] == session_token
    assert ("AGENT_MONITOR_TOKEN" in restores) is ("tests.test_agent_monitor_router" in sys.modules)
