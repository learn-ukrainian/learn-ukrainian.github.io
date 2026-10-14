"""Ambient credential-shaped names are absent inside every test.

``tests/conftest.py`` drops names ending in ``_API_KEY``, ``_TOKEN`` or
``_SECRET`` when it is imported, and does not put them back. A subprocess
pytest, started with those names set and with cwd at the repo root, loads
the real conftest and checks the result. ``LU_TEST_CREDENTIAL_STRIP`` does
not change that strip, whatever value it holds.
Failure text names variables and never prints their values.

AnyIO, pytest-cov, pytest-mock, pytest-rerunfailures, pytest-timeout,
pytest-xdist, and the repo's own dispatch-cap plugin load before this
conftest; none reads credential-suffix names.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path

import pytest

from tests.conftest import _is_credential_shaped_env_name

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
    with Path(os.environ["ZZ_STRIP_ORDER_LOG"]).open("a", encoding="utf-8") as handle:
        handle.write("password_at_import=" + ("yes" if "ZZ_STRIP_PROBE_PASSWORD" in os.environ else "no") + "\\n")
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


# Import probes copy the parent environment and must not look like a nested
# pytest worker. Child pytest sessions do not use this list: they start from
# an explicit environment instead of a filtered copy.
_CHILD_RUNTIME_DROPS = (
    "PYTEST_CURRENT_TEST",
    "PYTEST_XDIST_WORKER",
    "PYTEST_XDIST_WORKER_COUNT",
    "PYTEST_XDIST_TESTRUNUID",
)
# Parent-runner names that a nested interpreter still needs. Everything else,
# including PYTEST_* and the shard allowlist, stays out.
_CHILD_ENV_FROM_PARENT = ("PATH", "LANG", "LC_ALL", "TMPDIR")
_PASSED_SUMMARY = re.compile(r"\b[1-9]\d* passed\b")
_PROBE_ROOT: Path | None = None
_PROBE_SEQ = 0


def _proc_start_token(pid: int) -> str:
    """Clock-tick start time of ``pid``. Failures do not include the token."""
    try:
        raw = Path(f"/proc/{pid}/stat").read_bytes()
    except OSError as exc:
        raise AssertionError(f"start time unavailable for pid {pid}") from exc
    close = raw.rfind(b")")
    fields = raw[close + 2 :].split() if close >= 0 else []
    if len(fields) <= 19:
        raise AssertionError(f"start time unavailable for pid {pid}")
    try:
        token = fields[19].decode("ascii")
    except UnicodeDecodeError as exc:
        raise AssertionError(f"start time unavailable for pid {pid}") from exc
    if not token.isdigit():
        raise AssertionError(f"start time unavailable for pid {pid}")
    return token


def _parent_process_identity() -> str:
    """``<pid>:<starttime>`` of this process, the parent of a child probe."""
    return f"{os.getpid()}:{_proc_start_token(os.getpid())}"


@pytest.fixture(scope="session", autouse=True)
def _managed_probe_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Session scratch for generated child suites. Pytest owns the directory."""
    global _PROBE_ROOT
    _PROBE_ROOT = tmp_path_factory.mktemp("zz-strip-probes")
    return _PROBE_ROOT


def _new_probe_dir(prefix: str) -> Path:
    global _PROBE_SEQ
    if _PROBE_ROOT is None:
        raise AssertionError("managed probe root is not ready")
    _PROBE_SEQ += 1
    probe = _PROBE_ROOT / f"{prefix}{_PROBE_SEQ}"
    probe.mkdir()
    return probe


def _hermetic_child_env(overrides: dict[str, str], *, home: Path) -> dict[str, str]:
    """Minimal environment for one nested pytest process.

    A copied parent environment carries ``LU_PYTEST_SHARD_FILES``. The suite
    conftest then ignores every generated file that was not on the shard list,
    and the child exits 5 with ``no tests ran``. ``PYTEST_*`` and
    ``PYTEST_ADDOPTS`` would also reapply the parent run. The marker naming
    this parent is not read by the strip.
    """
    env = {
        "HOME": str(home),
        "PYTHONPATH": os.pathsep.join((str(REPO_ROOT), str(REPO_ROOT / "scripts"))),
    }
    for name in _CHILD_ENV_FROM_PARENT:
        value = os.environ.get(name)
        if value:
            env[name] = value
    for name, value in overrides.items():
        if name.startswith("PYTEST_"):
            continue
        env[name] = value
    env.setdefault("LU_TEST_CREDENTIAL_STRIP", _parent_process_identity())
    return env


def _child_env(after_path: Path, order_log: Path) -> dict[str, str]:
    env = {
        "ZZ_STRIP_PROBE_AFTER": str(after_path),
        "ZZ_STRIP_ORDER_LOG": str(order_log),
    }
    for name in (*_STRIPPED, _PLAIN, _PLURAL, *_OUTSIDE_CONTRACT, _CURSOR_TOKEN):
        env[name] = SENTINEL
    return env


def _assert_child_collected(stdout: str, stderr: str) -> None:
    """A child that collected nothing must not look like a passing session."""
    text = stdout + "\n" + stderr
    assert "no tests ran" not in text, text
    assert _PASSED_SUMMARY.search(stdout), text


def _run_child_pytest(
    probe_dir: Path,
    overrides: dict[str, str],
    *,
    workers: int = 0,
) -> subprocess.CompletedProcess[str]:
    """Run the generated files in a private root, loading the real suite conftest.

    ``--rootdir`` is the probe directory, so discovery does not walk up to
    ``tests/conftest.py``. ``-p tests.conftest`` loads that module anyway: the
    import strip and the worker publish/restore hooks live there. ``-c
    /dev/null`` keeps the repo's ``addopts`` marker expression out.
    """
    test_files = sorted(str(path) for path in probe_dir.glob("test_*.py"))
    if not test_files:
        raise AssertionError(f"child probe has no test files: {probe_dir.name}")
    home = probe_dir / "home"
    home.mkdir()
    command = [
        sys.executable,
        "-m",
        "pytest",
        *test_files,
        "-q",
        "--tb=short",
        "-p",
        "no:cacheprovider",
        "-p",
        "tests.conftest",
        "-c",
        "/dev/null",
        "--rootdir",
        str(probe_dir),
        "-o",
        "addopts=",
    ]
    if workers:
        command.extend(["-p", "xdist", "-n", str(workers)])
    else:
        command.extend(["-p", "no:xdist"])
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=_hermetic_child_env(overrides, home=home),
        capture_output=True,
        text=True,
        timeout=180 if workers else 120,
        check=False,
    )


def _run_recorded_probe(files: dict[str, str]) -> _ChildPytest:
    """Run a child pytest after this test's own strip, so the copy has no host secret."""
    probe_dir = _new_probe_dir("zz-strip-probe-")
    after_path = probe_dir / "after.txt"
    order_path = probe_dir / "order.txt"
    after_path.touch()
    order_path.touch()
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
    _assert_child_collected(child.stdout, child.stderr)
    assert child.returncode == 0, child.stdout + "\n" + child.stderr


def test_ambient_credential_env_is_stripped_for_every_test() -> None:
    """A real conftest session hides credential suffixes and leaves them hidden."""
    probe_dir = _new_probe_dir("zz-strip-probe-")
    after_path = probe_dir / "after.txt"
    after_path.touch()
    probe = probe_dir / "test_probe.py"
    probe.write_text(_PROBE, encoding="utf-8")
    (probe_dir / "conftest.py").write_text(_PROBE_CONFTEST, encoding="utf-8")
    overrides = {"ZZ_STRIP_PROBE_AFTER": str(after_path)}
    for name in (*_STRIPPED, _PLAIN, _PLURAL):
        overrides[name] = SENTINEL
    result = _run_child_pytest(probe_dir, overrides)
    _assert_child_collected(result.stdout, result.stderr)
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    assert after_path.read_text(encoding="utf-8") == "absent"


def test_suffix_match_ignores_case_and_plural_tokens() -> None:
    """Suffix matching is case-insensitive and does not treat ``_TOKENS`` as ``_TOKEN``."""
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
    """A value the suite writes after the strip stays through the test and at session end."""
    child = _early_probe()
    _require_child_ok(child)
    assert child.notes["suite_before_undo"] == "yes"
    assert child.notes["suite_after_undo"] == "yes"
    assert child.notes["import_published"] == "yes"
    assert child.notes["cursor_token"] == "suite"
    observed = _note_map(child.after)
    assert observed["ambient"] == "absent"
    assert observed["suite"] == "present"
    assert observed["import_published"] == "present"
    assert observed["plain"] == "sentinel"


def test_names_outside_the_suffix_contract_stay_visible() -> None:
    """Keep unrelated names while passwords are absent before collection."""
    child = _early_probe()
    _require_child_ok(child)
    assert child.notes["plain"] == "yes"
    assert child.notes["plural"] == "yes"
    assert child.notes["password_at_import"] == "no"
    assert child.notes["password"] == "no"
    assert child.notes["bare_key"] == "yes"
    assert child.notes["aws_secret_access_key"] == "yes"


def test_failing_test_does_not_restore_ambient_credentials() -> None:
    """A failed test does not put the ambient names back, and the next test stays hidden."""
    child = _run_recorded_probe(
        {
            "conftest.py": _PROBE_CONFTEST,
            "test_failure.py": _FAILURE_PROBE,
        }
    )
    _assert_child_collected(child.stdout, child.stderr)
    assert child.returncode != 0, child.stdout + "\n" + child.stderr
    assert "intentional failure" in child.stdout
    assert child.notes["failing_test"] == "absent"
    assert child.notes["later_test"] == "absent"
    assert child.after == "absent"


def _credential_snapshot() -> dict[str, str]:
    """Credential-shaped names, without the cursor session token.

    The cursor process guard mints a new token at every session start, including
    a nested ``pytest.main``. That publication is not a restore of an ambient value.
    """
    snapshot = {name: value for name, value in os.environ.items() if _is_credential_shaped_env_name(name)}
    snapshot.pop(_CURSOR_TOKEN, None)
    return snapshot


def test_nested_pytest_main_leaves_the_outer_environment_unchanged() -> None:
    """``pytest.main(["--collect-only", ...])`` must not restore or delete names.

    The nested call does not import ``tests.conftest`` again, so it neither
    strips nor restores.
    """
    published = "ZZ_NESTED_OUTER_API_KEY"
    assert published not in os.environ
    assert "ZZ_STRIP_PROBE_API_KEY" not in os.environ
    os.environ[published] = "published-by-outer-session"
    try:
        inner = _new_probe_dir("zz-nested-main-") / "test_inner.py"
        inner.write_text("def test_inner():\n    pass\n", encoding="utf-8")
        before = _credential_snapshot()
        code = pytest.main(
            [
                "--collect-only",
                "-q",
                "-p",
                "no:cacheprovider",
                "-o",
                "addopts=",
                "--rootdir",
                str(REPO_ROOT),
                str(inner),
            ]
        )
        after = _credential_snapshot()
    finally:
        os.environ.pop(published, None)
    assert code == 0
    assert before == after
    assert before[published] == "published-by-outer-session"
    assert "ZZ_STRIP_PROBE_API_KEY" not in before


_IMPORT_REPORT = textwrap.dedent(
    """\
    import os
    import sys

    def _start_token(pid):
        raw = open("/proc/%s/stat" % pid, "rb").read()
        close = raw.rfind(b")")
        fields = raw[close + 2 :].split() if close >= 0 else []
        if len(fields) <= 19:
            raise SystemExit("start time unavailable")
        return fields[19].decode("ascii")

    mode = os.environ.get("ZZ_MARKER_MODE", "preset")
    if mode == "own-bare":
        os.environ["LU_TEST_CREDENTIAL_STRIP"] = str(os.getpid())
    elif mode == "own-wellformed":
        pid = os.getpid()
        os.environ["LU_TEST_CREDENTIAL_STRIP"] = "%s:%s" % (pid, _start_token(pid))
    elif mode == "pid1-wellformed":
        os.environ["LU_TEST_CREDENTIAL_STRIP"] = "1:" + _start_token(1)

    before = os.environ.get("LU_TEST_CREDENTIAL_STRIP")
    sys.path.insert(0, os.getcwd())
    import tests.conftest

    after = os.environ.get("LU_TEST_CREDENTIAL_STRIP")
    watched = (
        "ZZ_STRIP_PROBE_API_KEY",
        "ZZ_STRIP_PROBE_TOKEN",
        "ZZ_STRIP_PROBE_SECRET",
        "ZZ_STRIP_PROBE_PLAIN",
    )
    present = [name for name in watched if name in os.environ]
    print("present=" + ",".join(present))
    print("marker_unchanged=" + ("yes" if before == after else "no"))
    print("marker_present=" + ("yes" if "LU_TEST_CREDENTIAL_STRIP" in os.environ else "no"))
    """
)


_CREDENTIAL_STRIP_MARKER = "LU_TEST_CREDENTIAL_STRIP"
_IMPORT_CREDENTIALS = (
    "ZZ_STRIP_PROBE_API_KEY",
    "ZZ_STRIP_PROBE_TOKEN",
    "ZZ_STRIP_PROBE_SECRET",
)


def _probe_base_env() -> dict[str, str]:
    env = os.environ.copy()
    for name in (*_CHILD_RUNTIME_DROPS, "PYTHONPATH", "PYTEST_ADDOPTS", _CREDENTIAL_STRIP_MARKER):
        env.pop(name, None)
    return env


def _import_probe_env(mode: str) -> dict[str, str]:
    """Environment whose credential-shaped names must be stripped at import."""
    env = _probe_base_env()
    env["ZZ_MARKER_MODE"] = mode
    env["ZZ_STRIP_PROBE_PLAIN"] = SENTINEL
    for name in _IMPORT_CREDENTIALS:
        env[name] = SENTINEL
    if mode == "literal-1":
        env[_CREDENTIAL_STRIP_MARKER] = "1"
    elif mode == "empty":
        env[_CREDENTIAL_STRIP_MARKER] = ""
    elif mode == "garbage":
        env[_CREDENTIAL_STRIP_MARKER] = "garbage"
    elif mode == "parent-wellformed":
        env[_CREDENTIAL_STRIP_MARKER] = _parent_process_identity()
    else:
        env[_CREDENTIAL_STRIP_MARKER] = "placeholder"
    return env


def _run_import_probe(env: dict[str, str]) -> dict[str, str]:
    result = subprocess.run(
        [sys.executable, "-c", _IMPORT_REPORT],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    return _note_map(result.stdout)


def _present_names(report: dict[str, str]) -> set[str]:
    return set(report.get("present", "").split(",")) - {""}


def _assert_import_stripped(report: dict[str, str]) -> None:
    present = _present_names(report)
    still_there = sorted(set(_IMPORT_CREDENTIALS) & present)
    assert not still_there, "credential-shaped names still set: " + ", ".join(still_there)
    assert "ZZ_STRIP_PROBE_PLAIN" in present
    assert report.get("marker_unchanged") == "yes"
    assert report.get("marker_present") == "yes"


@pytest.mark.parametrize(
    "mode",
    [
        "literal-1",
        "empty",
        "garbage",
        "own-bare",
        "own-wellformed",
        "parent-wellformed",
        "pid1-wellformed",
    ],
)
def test_credential_strip_marker_has_no_effect(mode: str) -> None:
    """``LU_TEST_CREDENTIAL_STRIP`` does not keep credential-shaped names.

    The value may be ``1``, empty, garbage, this process's own pid, or a
    ``<pid>:<starttime>`` for this process, its parent, or pid 1. None of
    those values is read. The variable is left as it was.
    """
    report = _run_import_probe(_import_probe_env(mode))
    _assert_import_stripped(report)


# A child pytest process loads this conftest and strips again. A test that
# needs a credential in a child session passes it through that child's own
# conftest or monkeypatch.
_CHILD_STRIPS_PUBLISHED = textwrap.dedent(
    """\
    import os

    def test_child_strips_inherited_credentials():
        inherited = (
            "ZZ_PUBLISHED_AFTER_STRIP_API_KEY",
            "ZZ_STRIP_PROBE_API_KEY",
            "ZZ_STRIP_PROBE_TOKEN",
            "ZZ_STRIP_PROBE_SECRET",
        )
        visible = [name for name in inherited if name in os.environ]
        if visible:
            raise AssertionError("credential-shaped names still set: " + ", ".join(visible))
        if os.environ.get("ZZ_STRIP_PROBE_PLAIN") != "sentinel-not-a-real-value":
            raise AssertionError("unrelated name was stripped or changed")
    """
)


def test_child_pytest_process_strips_published_credentials() -> None:
    """A child pytest that loads this conftest strips names the parent published."""
    probe_dir = _new_probe_dir("zz-strip-child-")
    (probe_dir / "test_child_strips.py").write_text(_CHILD_STRIPS_PUBLISHED, encoding="utf-8")
    overrides = {
        _CREDENTIAL_STRIP_MARKER: _parent_process_identity(),
        "ZZ_PUBLISHED_AFTER_STRIP_API_KEY": "published-after-strip",
        "ZZ_STRIP_PROBE_PLAIN": SENTINEL,
    }
    for name in _IMPORT_CREDENTIALS:
        overrides[name] = SENTINEL
    result = _run_child_pytest(probe_dir, overrides)
    _assert_child_collected(result.stdout, result.stderr)
    assert result.returncode == 0, result.stdout + "\n" + result.stderr


_XDIST_CONFTEST = textwrap.dedent(
    """\
    import os

    def pytest_configure(config):
        # Publish on the controller only. The worker stripped at import and
        # receives the name through workerinput.
        if not hasattr(config, "workerinput"):
            os.environ["ZZ_PUBLISHED_AFTER_STRIP_API_KEY"] = "published-after-strip"
    """
)

_XDIST_PROBE = textwrap.dedent(
    """\
    import os
    from pathlib import Path

    def test_worker_receives_controller_publication():
        if os.environ.get("ZZ_PUBLISHED_AFTER_STRIP_API_KEY") != "published-after-strip":
            raise AssertionError("suite-published name was not restored on the worker")
        ambient = (
            "ZZ_STRIP_PROBE_API_KEY",
            "ZZ_STRIP_PROBE_TOKEN",
            "ZZ_STRIP_PROBE_SECRET",
        )
        visible = [name for name in ambient if name in os.environ]
        if visible:
            raise AssertionError("ambient credential-shaped names still set: " + ", ".join(visible))
        if os.environ.get("ZZ_STRIP_PROBE_PLAIN") != "sentinel-not-a-real-value":
            raise AssertionError("unrelated name was stripped or changed")
        Path(os.environ["ZZ_XDIST_RESULT"]).write_text("kept", encoding="utf-8")
    """
)


def test_xdist_worker_receives_names_published_on_the_controller() -> None:
    """A ``-n 1`` worker receives names the controller published after its strip.

    The controller conftest sets the name during ``pytest_configure``, which is
    before ``pytest_configure_node``. Ambient names in the child environment
    are stripped at the controller import and are not copied. The outer run
    does not pass ``-n``.
    """
    probe_dir = _new_probe_dir("zz-strip-xdist-")
    result_path = probe_dir / "result.txt"
    (probe_dir / "conftest.py").write_text(_XDIST_CONFTEST, encoding="utf-8")
    (probe_dir / "test_xdist_worker.py").write_text(_XDIST_PROBE, encoding="utf-8")
    overrides = {
        _CREDENTIAL_STRIP_MARKER: _parent_process_identity(),
        "ZZ_STRIP_PROBE_PLAIN": SENTINEL,
        "ZZ_XDIST_RESULT": str(result_path),
    }
    for name in _IMPORT_CREDENTIALS:
        overrides[name] = SENTINEL
    result = _run_child_pytest(probe_dir, overrides, workers=1)
    _assert_child_collected(result.stdout, result.stderr)
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    assert "published-after-strip" not in result.stdout
    assert "published-after-strip" not in result.stderr
    assert result_path.read_text(encoding="utf-8") == "kept"
