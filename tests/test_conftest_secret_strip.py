"""Ambient credential-shaped names are absent inside every test.

``tests/conftest.py`` drops names ending in ``_API_KEY``, ``_TOKEN`` or
``_SECRET`` before collection. A subprocess pytest, started with those names
set and with cwd at the repo root, loads the real conftest and checks the
result. Failure text names variables and never prints their values.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass
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
_OUTSIDE_CONTRACT = (
    "ZZ_STRIP_PROBE_PASSWORD",
    "ZZ_STRIP_PROBE_KEY",
    "AWS_SECRET_ACCESS_KEY",
)
_CURSOR_TOKEN = "LU_TEST_CURSOR_SESSION_TOKEN"

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
    def pytest_unconfigure(config):
        import os
        from pathlib import Path

        value = os.environ.get("ZZ_STRIP_PROBE_API_KEY")
        state = "sentinel" if value == "sentinel-not-a-real-value" else "other" if value else "absent"
        Path(os.environ["ZZ_STRIP_PROBE_AFTER"]).write_text(state, encoding="utf-8")
    """
)

_ORDER_CONFTEST = textwrap.dedent(
    """\
    def pytest_unconfigure(config):
        import os
        from pathlib import Path

        value = os.environ.get("ZZ_STRIP_PROBE_API_KEY")
        ambient = "sentinel" if value == "sentinel-not-a-real-value" else "other" if value else "absent"
        suite = "present" if "ZZ_SUITE_PUBLISHED_API_KEY" in os.environ else "absent"
        published = "present" if "ZZ_IMPORT_PUBLISHED_API_KEY" in os.environ else "absent"
        plain = os.environ.get("ZZ_STRIP_PROBE_PLAIN")
        plain_state = "sentinel" if plain == "sentinel-not-a-real-value" else "other" if plain else "absent"
        text = (
            "ambient=" + ambient + "\\n"
            "suite=" + suite + "\\n"
            "import_published=" + published + "\\n"
            "plain=" + plain_state + "\\n"
        )
        Path(os.environ["ZZ_STRIP_PROBE_AFTER"]).write_text(text, encoding="utf-8")
    """
)

_ORDER_PROBE = textwrap.dedent(
    """\
    import os
    from pathlib import Path

    def _note(phase):
        flag = "visible" if "ZZ_STRIP_PROBE_API_KEY" in os.environ else "absent"
        with Path(os.environ["ZZ_STRIP_ORDER_LOG"]).open("a", encoding="utf-8") as handle:
            handle.write(phase + "=" + flag + "\\n")

    _note("import")
    os.environ["ZZ_IMPORT_PUBLISHED_API_KEY"] = "published-at-import"

    import pytest

    @pytest.fixture(scope="session", autouse=True)
    def _session_seen():
        _note("session")
        yield

    @pytest.fixture(scope="module", autouse=True)
    def _module_seen():
        _note("module")
        os.environ["ZZ_SUITE_PUBLISHED_API_KEY"] = "published-by-module-fixture"
        yield

    @pytest.fixture(scope="class", autouse=True)
    def _class_seen():
        _note("class")
        yield

    class TestRecord:
        def test_record(self, monkeypatch):
            def add(name, ok):
                with Path(os.environ["ZZ_STRIP_ORDER_LOG"]).open("a", encoding="utf-8") as handle:
                    handle.write(name + "=" + ("yes" if ok else "no") + "\\n")

            add("ambient_in_test", "ZZ_STRIP_PROBE_API_KEY" not in os.environ)
            add(
                "suite_before_undo",
                os.environ.get("ZZ_SUITE_PUBLISHED_API_KEY") == "published-by-module-fixture",
            )
            add(
                "import_published",
                os.environ.get("ZZ_IMPORT_PUBLISHED_API_KEY") == "published-at-import",
            )
            add("plain", os.environ.get("ZZ_STRIP_PROBE_PLAIN") == "sentinel-not-a-real-value")
            add("plural", os.environ.get("ZZ_STRIP_PROBE_TOKENS") == "sentinel-not-a-real-value")
            add("password", os.environ.get("ZZ_STRIP_PROBE_PASSWORD") == "sentinel-not-a-real-value")
            add("bare_key", os.environ.get("ZZ_STRIP_PROBE_KEY") == "sentinel-not-a-real-value")
            add(
                "aws_secret_access_key",
                os.environ.get("AWS_SECRET_ACCESS_KEY") == "sentinel-not-a-real-value",
            )
            import subprocess
            import sys

            completed = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import os; raise SystemExit(0 if 'ZZ_STRIP_PROBE_API_KEY' not in os.environ else 1)",
                ],
                check=False,
            )
            add("subprocess_hidden", completed.returncode == 0)
            token = os.environ.get("LU_TEST_CURSOR_SESSION_TOKEN")
            if token and token != "sentinel-not-a-real-value":
                cursor_state = "suite"
            elif token:
                cursor_state = "ambient"
            else:
                cursor_state = "absent"
            with Path(os.environ["ZZ_STRIP_ORDER_LOG"]).open("a", encoding="utf-8") as handle:
                handle.write("cursor_token=" + cursor_state + "\\n")
            monkeypatch.undo()
            add("ambient_after_undo", "ZZ_STRIP_PROBE_API_KEY" not in os.environ)
            add(
                "suite_after_undo",
                os.environ.get("ZZ_SUITE_PUBLISHED_API_KEY") == "published-by-module-fixture",
            )
    """
)

_SECOND_MODULE_PROBE = textwrap.dedent(
    """\
    import os
    from pathlib import Path

    import pytest

    @pytest.fixture(scope="module", autouse=True)
    def _second_module_seen():
        flag = "visible" if "ZZ_STRIP_PROBE_API_KEY" in os.environ else "absent"
        with Path(os.environ["ZZ_STRIP_ORDER_LOG"]).open("a", encoding="utf-8") as handle:
            handle.write("second_module=" + flag + "\\n")

    def test_second_module_body():
        flag = "visible" if "ZZ_STRIP_PROBE_API_KEY" in os.environ else "absent"
        with Path(os.environ["ZZ_STRIP_ORDER_LOG"]).open("a", encoding="utf-8") as handle:
            handle.write("second_test=" + flag + "\\n")
    """
)

_FAILURE_PROBE = textwrap.dedent(
    """\
    import os
    from pathlib import Path

    def _note(phase):
        flag = "visible" if "ZZ_STRIP_PROBE_API_KEY" in os.environ else "absent"
        with Path(os.environ["ZZ_STRIP_ORDER_LOG"]).open("a", encoding="utf-8") as handle:
            handle.write(phase + "=" + flag + "\\n")

    def test_intentional_failure():
        _note("failing_test")
        raise AssertionError("intentional failure")

    def test_later_test_still_hides_ambient():
        _note("later_test")
    """
)


@dataclass(frozen=True)
class _ChildPytest:
    """One child pytest session. Notes never contain environment values."""

    returncode: int
    stdout: str
    stderr: str
    notes: dict[str, str]
    after: str


def _note_map(text: str) -> dict[str, str]:
    notes: dict[str, str] = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        notes[key] = value
    return notes


def _child_env(after_path: Path, order_log: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.pop("PYTEST_CURRENT_TEST", None)
    env["ZZ_STRIP_PROBE_AFTER"] = str(after_path)
    env["ZZ_STRIP_ORDER_LOG"] = str(order_log)
    for name in (*_STRIPPED, _PLAIN, _PLURAL, *_OUTSIDE_CONTRACT, _CURSOR_TOKEN):
        env[name] = SENTINEL
    return env


def _run_child_pytest(probe_dir: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(probe_dir.relative_to(REPO_ROOT)),
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
        timeout=120,
        check=False,
    )


def _run_recorded_probe(files: dict[str, str]) -> _ChildPytest:
    """Run a child pytest after this test's own strip, so the copy has no host secret."""
    tests_dir = REPO_ROOT / "tests"
    after_descriptor, after_name = tempfile.mkstemp(prefix="zz-strip-after-")
    os.close(after_descriptor)
    order_descriptor, order_name = tempfile.mkstemp(prefix="zz-strip-order-")
    os.close(order_descriptor)
    after_path = Path(after_name)
    order_path = Path(order_name)
    try:
        with tempfile.TemporaryDirectory(prefix="_zz_strip_probe_", dir=tests_dir) as raw:
            probe_dir = Path(raw)
            for name, source in files.items():
                (probe_dir / name).write_text(source, encoding="utf-8")
            result = _run_child_pytest(probe_dir, _child_env(after_path, order_path))
        return _ChildPytest(
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            notes=_note_map(order_path.read_text(encoding="utf-8")),
            after=after_path.read_text(encoding="utf-8"),
        )
    finally:
        after_path.unlink(missing_ok=True)
        order_path.unlink(missing_ok=True)


_EARLY_PROBE: _ChildPytest | None = None


def _early_probe() -> _ChildPytest:
    global _EARLY_PROBE
    if _EARLY_PROBE is None:
        _EARLY_PROBE = _run_recorded_probe(
            {
                "conftest.py": _ORDER_CONFTEST,
                "test_aaa_record.py": _ORDER_PROBE,
                "test_bbb_second.py": _SECOND_MODULE_PROBE,
            }
        )
    return _EARLY_PROBE


def _require_child_ok(child: _ChildPytest) -> None:
    assert child.returncode == 0, child.stdout + "\n" + child.stderr


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


def test_import_time_read_does_not_see_ambient_credentials() -> None:
    """Collection imports the module only after inherited credentials are hidden."""
    child = _early_probe()
    _require_child_ok(child)
    assert child.notes["import"] == "absent"


def test_session_module_and_class_fixtures_do_not_see_ambient_credentials() -> None:
    """Higher-scoped fixtures, including the next module, never see inherited values."""
    child = _early_probe()
    _require_child_ok(child)
    assert child.notes["session"] == "absent"
    assert child.notes["module"] == "absent"
    assert child.notes["class"] == "absent"
    assert child.notes["second_module"] == "absent"
    assert child.notes["second_test"] == "absent"


def test_monkeypatch_undo_does_not_restore_ambient_credentials() -> None:
    """``monkeypatch.undo()`` must not put the inherited value back mid-test."""
    child = _early_probe()
    _require_child_ok(child)
    assert child.notes["ambient_in_test"] == "yes"
    assert child.notes["ambient_after_undo"] == "yes"
    assert child.notes["subprocess_hidden"] == "yes"


def test_module_fixture_published_credential_remains_visible() -> None:
    """A value the suite writes after the snapshot stays, before and after undo."""
    child = _early_probe()
    _require_child_ok(child)
    assert child.notes["suite_before_undo"] == "yes"
    assert child.notes["suite_after_undo"] == "yes"
    assert child.notes["import_published"] == "yes"
    assert child.notes["cursor_token"] == "suite"
    restored = _note_map(child.after)
    assert restored["ambient"] == "sentinel"
    assert restored["suite"] == "absent"
    assert restored["import_published"] == "absent"
    assert restored["plain"] == "sentinel"


def test_names_outside_the_suffix_contract_stay_visible() -> None:
    """``_PASSWORD``, a bare ``_KEY``, and ``AWS_SECRET_ACCESS_KEY`` are not stripped."""
    child = _early_probe()
    _require_child_ok(child)
    assert child.notes["plain"] == "yes"
    assert child.notes["plural"] == "yes"
    assert child.notes["password"] == "yes"
    assert child.notes["bare_key"] == "yes"
    assert child.notes["aws_secret_access_key"] == "yes"


def test_ambient_environment_is_restored_after_a_failing_test() -> None:
    """A failed test still ends with the inherited environment, and the next test stays hidden."""
    child = _run_recorded_probe(
        {
            "conftest.py": _PROBE_CONFTEST,
            "test_failure.py": _FAILURE_PROBE,
        }
    )
    assert child.returncode != 0, child.stdout + "\n" + child.stderr
    assert "intentional failure" in child.stdout
    assert child.notes["failing_test"] == "absent"
    assert child.notes["later_test"] == "absent"
    assert child.after == "sentinel"
