"""Ungoverned local pytest refuses an xdist fan-out above the existing cap (#11179).

Subprocess cases use a private slot pool and at most four workers. A refusal must
leave no worker-start line and no test-body sentinel. Admitted runs record the
worker ids xdist actually configured.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.ci import pytest_dispatch_cap
from scripts.ci.pytest_dispatch_cap import DISPATCH_TASK_ENV, GOVERNED_PYTEST
from scripts.common import test_slots

_REPO = Path(__file__).resolve().parents[2]
_PY = sys.executable

_CONFTEST = """\
import os


def pytest_configure(config):
    path = os.environ.get("FANOUT_WORKERS")
    if not path or not hasattr(config, "workerinput"):
        return
    with open(path, "a", encoding="utf-8") as stream:
        stream.write(config.workerinput["workerid"] + "\\n")
"""

_TESTS = """\
import os


def _mark():
    with open(os.environ["FANOUT_BODY"], "a", encoding="utf-8") as stream:
        stream.write((os.environ.get("PYTEST_XDIST_WORKER") or "controller") + "\\n")


def test_first():
    _mark()


def test_second():
    _mark()
"""

_OBSERVE = """\
def pytest_configure(config):
    if hasattr(config, "workerinput"):
        return
    from ci.pytest_dispatch_cap import tx_spec_worker_count

    tx = list(getattr(config.option, "tx", None) or [])
    print(f"OBSERVED_WORKERS={tx_spec_worker_count(tx)}", flush=True)
    config.option.tx = []
    config.option.numprocesses = 0
    config.option.dist = "no"
"""


def _project(tmp_path: Path, *, conftest: str = _CONFTEST) -> Path:
    root = tmp_path / "project"
    (root / "tests").mkdir(parents=True)
    scripts = (_REPO / "scripts").as_posix()
    (root / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\n"
        "testpaths = ['tests']\n"
        f"pythonpath = ['{scripts}']\n"
        "addopts = '-p ci.pytest_dispatch_cap'\n",
        encoding="utf-8",
    )
    (root / "conftest.py").write_text(conftest, encoding="utf-8")
    (root / "tests" / "test_sample.py").write_text(_TESTS, encoding="utf-8")
    return root


def _env(tmp_path: Path, **extra: str | None) -> dict[str, str]:
    """A local child: no dispatch marker, no inherited holder, slots explicitly on, CI cleared."""
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {test_slots.HOLDER_ENV, "CI", "PYTEST_ADDOPTS", DISPATCH_TASK_ENV}
        and not key.startswith("PYTEST_XDIST_")
    }
    env.update(
        {
            test_slots.ENABLE_ENV: "on",
            test_slots.DIR_ENV: str(tmp_path / "pool"),
            test_slots.COUNT_ENV: "4",
            test_slots.WAIT_ENV: "5",
            "PYTHONPATH": os.pathsep.join((str(_REPO), str(_REPO / "scripts"), env.get("PYTHONPATH", ""))),
            "FANOUT_BODY": str(tmp_path / "body"),
            "FANOUT_WORKERS": str(tmp_path / "workers"),
        }
    )
    for key, value in extra.items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value
    return env


def _run(root: Path, args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [_PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_sample.py", *args],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def _workers(tmp_path: Path) -> set[str]:
    path = tmp_path / "workers"
    if not path.is_file():
        return set()
    return {line for line in path.read_text(encoding="utf-8").splitlines() if line}


def _body(tmp_path: Path) -> list[str]:
    path = tmp_path / "body"
    if not path.is_file():
        return []
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line]


def _assert_refused(completed: subprocess.CompletedProcess[str], tmp_path: Path, *, slots_off: bool = False) -> None:
    combined = completed.stdout + completed.stderr
    assert completed.returncode == pytest.ExitCode.USAGE_ERROR, combined
    assert GOVERNED_PYTEST in combined
    assert "pytest worker cap:" in combined
    if slots_off:
        assert "does not authorize a larger fan-out" in combined
    assert _workers(tmp_path) == set()
    assert _body(tmp_path) == []


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv(test_slots.ENABLE_ENV, "on")
    monkeypatch.setenv(test_slots.DIR_ENV, str(tmp_path / "pool"))
    monkeypatch.setenv(test_slots.COUNT_ENV, "4")
    monkeypatch.delenv(test_slots.HOLDER_ENV, raising=False)
    return _project(tmp_path)


def test_unleased_n4_is_refused_before_workers_or_the_body(project: Path, tmp_path: Path) -> None:
    completed = _run(project, ["-n", "4"], _env(tmp_path))
    _assert_refused(completed, tmp_path)


@pytest.mark.parametrize(
    "args",
    [
        ["-n4"],
        ["--numprocesses=4"],
        ["--numprocesses", "4"],
        ["-n", "1", "-n", "4"],
        ["--dist=load", "--tx", "3*popen"],
        ["--dist=load", "--tx", "popen", "--tx", "popen", "--tx", "popen"],
        ["--fixtures", "-n", "4"],
        ["--fixtures-per-test", "-n", "4"],
    ],
)
def test_over_cap_option_forms_are_refused(project: Path, tmp_path: Path, args: list[str]) -> None:
    completed = _run(project, args, _env(tmp_path))
    _assert_refused(completed, tmp_path)


@pytest.mark.parametrize("flag", ["auto", "logical"])
def test_auto_above_the_cap_is_refused(project: Path, tmp_path: Path, flag: str) -> None:
    env = _env(tmp_path)
    env[test_slots.XDIST_AUTO_ENV] = "4"
    completed = _run(project, ["-n", flag], env)
    _assert_refused(completed, tmp_path)


def test_fixtures_with_auto_above_the_cap_is_refused(project: Path, tmp_path: Path) -> None:
    env = _env(tmp_path)
    env[test_slots.XDIST_AUTO_ENV] = "4"
    completed = _run(project, ["--fixtures", "-n", "auto"], env)
    _assert_refused(completed, tmp_path)


def test_within_cap_serial_and_zero_still_run(project: Path, tmp_path: Path) -> None:
    within = _run(project, ["-n", "2"], _env(tmp_path))
    assert within.returncode == 0, within.stdout + within.stderr
    assert _workers(tmp_path) == {"gw0", "gw1"}
    assert set(_body(tmp_path)) <= {"gw0", "gw1"}
    assert _body(tmp_path)
    for path in (tmp_path / "workers", tmp_path / "body"):
        path.unlink()
    serial = _run(project, [], _env(tmp_path))
    assert serial.returncode == 0, serial.stdout + serial.stderr
    assert _workers(tmp_path) == set()
    assert _body(tmp_path) == ["controller", "controller"]
    for path in (tmp_path / "body",):
        path.unlink()
    zero = _run(project, ["-n", "0", "--dist=load", "--tx", "3*popen"], _env(tmp_path))
    assert zero.returncode == 0, zero.stdout + zero.stderr
    assert _workers(tmp_path) == set()
    assert _body(tmp_path) == ["controller", "controller"]


def test_last_n_under_the_cap_is_admitted(project: Path, tmp_path: Path) -> None:
    completed = _run(project, ["-n", "4", "-n", "1"], _env(tmp_path))
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert _workers(tmp_path) == {"gw0"}
    assert _body(tmp_path)


def test_maxprocesses_can_keep_an_explicit_n_inside_the_cap(project: Path, tmp_path: Path) -> None:
    completed = _run(project, ["-n", "4", "--maxprocesses=1"], _env(tmp_path))
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert _workers(tmp_path) == {"gw0"}


def test_informational_over_cap_is_not_refused(project: Path, tmp_path: Path) -> None:
    for args in (["--collect-only", "-n", "4"], ["--markers", "-n", "4"], ["--fixtures"], ["-n", "0", "--fixtures"]):
        completed = _run(project, args, _env(tmp_path))
        combined = completed.stdout + completed.stderr
        assert completed.returncode == 0, combined
        assert "pytest worker cap:" not in combined
        assert "TEST SLOTS:" not in combined
        assert _workers(tmp_path) == set()
        assert _body(tmp_path) == []


def test_ci_over_cap_is_not_refused(tmp_path: Path) -> None:
    """CI keeps today's unlimited local count. The probe records it and starts no worker."""
    root = _project(tmp_path, conftest=_OBSERVE)
    env = _env(tmp_path, CI="true")
    completed = _run(root, ["-n", "4"], env)
    combined = completed.stdout + completed.stderr
    assert completed.returncode == 0, combined
    assert "OBSERVED_WORKERS=4" in completed.stdout
    assert "pytest worker cap:" not in combined
    assert _workers(tmp_path) == set()


def test_slots_off_refuses_over_cap_even_with_a_live_marker(
    project: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(test_slots.COUNT_ENV, "4")
    hold = test_slots.acquire(2, kind="pytest")
    try:
        refused = _run(
            project,
            ["-n", "4"],
            _env(tmp_path, **{test_slots.ENABLE_ENV: "off", test_slots.HOLDER_ENV: hold.marker()}),
        )
        _assert_refused(refused, tmp_path, slots_off=True)
        for path in (tmp_path / "workers", tmp_path / "body"):
            path.unlink(missing_ok=True)
        admitted = _run(project, ["-n", "2"], _env(tmp_path, **{test_slots.ENABLE_ENV: "off"}))
    finally:
        hold.release()
    assert admitted.returncode == 0, admitted.stdout + admitted.stderr
    assert "pytest worker cap:" not in admitted.stdout + admitted.stderr
    assert _workers(tmp_path) == {"gw0", "gw1"}


@pytest.mark.parametrize("kind", ["stale", "malformed", "overclaimed"])
def test_a_bad_marker_does_not_authorize_extra_workers(
    project: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    monkeypatch.setenv(test_slots.COUNT_ENV, "4")
    hold = test_slots.acquire(2, kind="pytest")
    try:
        if kind == "stale":
            marker = hold.marker()
            hold.release()
        elif kind == "malformed":
            marker = "not-a-marker"
        else:
            count, _nonce, record = hold.marker().split(":", 2)
            assert count == "2"
            marker = f"8:{hold.marker().split(':', 2)[1]}:{record}"
        completed = _run(project, ["-n", "4"], _env(tmp_path, **{test_slots.HOLDER_ENV: marker}))
    finally:
        if kind != "stale":
            hold.release()
    _assert_refused(completed, tmp_path)


def test_a_live_hold_clamps_instead_of_refusing(project: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(test_slots.COUNT_ENV, "4")
    hold = test_slots.acquire(2, kind="pytest")
    try:
        completed = _run(project, ["-n", "4"], _env(tmp_path, **{test_slots.HOLDER_ENV: hold.marker()}))
    finally:
        hold.release()
    combined = completed.stdout + completed.stderr
    assert completed.returncode == 0, combined
    assert "pytest worker cap:" not in combined
    assert _workers(tmp_path) == {"gw0", "gw1"}
    assert set(_body(tmp_path)) <= {"gw0", "gw1"}
    assert _body(tmp_path)


def test_an_inherited_worker_env_is_not_a_worker(project: Path, tmp_path: Path) -> None:
    """``PYTEST_XDIST_WORKER`` on a new controller is not ``workerinput`` and does not skip the refusal."""
    completed = _run(project, ["-n", "4"], _env(tmp_path, PYTEST_XDIST_WORKER="gw0"))
    _assert_refused(completed, tmp_path)


def test_dispatch_still_clamps_instead_of_refusing(project: Path, tmp_path: Path) -> None:
    env = _env(tmp_path, **{DISPATCH_TASK_ENV: "impl-11179"})
    completed = _run(project, ["-n", "4"], env)
    combined = completed.stdout + completed.stderr
    assert completed.returncode == 0, combined
    assert "pytest worker cap:" not in combined
    assert _workers(tmp_path) == {"gw0", "gw1"}


def _config(*, numprocesses: object = None, dist: str = "no", distload: bool = False,
            tx: list[str] | None = None, maxprocesses: int | None = None, pdb: bool = False,
            hook: int | None = None) -> SimpleNamespace:
    def getoption(name: str, default: object = None) -> object:
        if name == "usepdb":
            return pdb
        return default

    def auto(config: object) -> int:
        assert hook is not None
        return hook

    return SimpleNamespace(
        option=SimpleNamespace(
            numprocesses=numprocesses, dist=dist, distload=distload, tx=tx, maxprocesses=maxprocesses
        ),
        getoption=getoption,
        hook=SimpleNamespace(pytest_xdist_auto_num_workers=auto),
    )


def test_effective_count_matches_xdist_precedence() -> None:
    count = pytest_dispatch_cap.effective_xdist_workers
    assert count(_config(numprocesses=0, tx=["3*popen"], dist="load")) == 0
    assert count(_config(numprocesses=4, tx=["3*popen"], dist="load")) == 4
    assert count(_config(numprocesses=8, maxprocesses=1)) == 1
    assert count(_config(numprocesses=8, maxprocesses=0)) == 8
    assert count(_config(numprocesses=8, maxprocesses=-1)) == -1
    assert count(_config(dist="load", tx=["3*popen"], maxprocesses=1)) == 3
    assert count(_config(dist="no", tx=["3*popen"])) == 0
    assert count(_config(distload=True, tx=["2*popen"])) == 2
    assert count(_config(numprocesses="auto", pdb=True, hook=8)) == 0
    assert count(_config(numprocesses="logical", hook=6)) == 6
    assert count(_config(numprocesses="auto", maxprocesses=2, hook=6)) == 2


def test_fixture_listing_without_workers_does_not_read_slot_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom() -> None:
        raise AssertionError("slot settings were read")

    monkeypatch.setattr(pytest_dispatch_cap, "_test_slots", _boom)
    option = SimpleNamespace(
        showfixtures=True, numprocesses="auto", maxprocesses=None, tx=None,
        collectonly=False, dist="no", distload=False,
    )
    config = _config(numprocesses="auto", pdb=True, hook=8)
    config.option = option
    pytest_dispatch_cap._acquire_test_slots(config, acquire=False)  # type: ignore[arg-type]


def test_raw_options_request_workers_only_when_xdist_would_start_them(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pytest_dispatch_cap, "xdist_available", lambda: False)
    assert pytest_dispatch_cap._option_requests_workers(SimpleNamespace()) is False  # type: ignore[arg-type]
    monkeypatch.setattr(pytest_dispatch_cap, "xdist_available", lambda: True)
    asks = pytest_dispatch_cap._option_requests_workers
    assert asks(_config(numprocesses="auto", hook=4)) is True  # type: ignore[arg-type]
    assert asks(_config(numprocesses="auto", pdb=True, hook=4)) is False  # type: ignore[arg-type]
    assert asks(_config(numprocesses=0, dist="load", tx=["3*popen"])) is False  # type: ignore[arg-type]
    assert asks(_config(dist="load", tx=["2*popen"])) is True  # type: ignore[arg-type]


def test_absent_xdist_counts_as_no_workers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pytest_dispatch_cap, "xdist_available", lambda: False)
    assert pytest_dispatch_cap.effective_xdist_workers(SimpleNamespace()) == 0


def test_within_cap_does_not_read_whether_slots_are_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Slots:
        HOLDER_ENV = test_slots.HOLDER_ENV
        ENABLE_ENV = test_slots.ENABLE_ENV
        _TRUE = test_slots._TRUE
        _FALSE = test_slots._FALSE

        @staticmethod
        def enabled() -> bool:
            raise AssertionError("slot settings were read under the cap")

    monkeypatch.setattr(pytest_dispatch_cap, "_test_slots", lambda: _Slots)
    monkeypatch.delenv(test_slots.HOLDER_ENV, raising=False)
    option = SimpleNamespace(numprocesses=1, maxprocesses=None, tx=None, collectonly=False, dist="no", distload=False)
    config = SimpleNamespace(option=option, getoption=lambda *_a, **_k: False)
    pytest_dispatch_cap._acquire_test_slots(config, acquire=False)  # type: ignore[arg-type]


def test_over_cap_invalid_slot_setting_is_the_typed_refusal(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Slots:
        HOLDER_ENV = test_slots.HOLDER_ENV
        ENABLE_ENV = test_slots.ENABLE_ENV
        _TRUE = test_slots._TRUE
        _FALSE = test_slots._FALSE
        SlotError = test_slots.SlotError

        @staticmethod
        def enabled() -> bool:
            raise test_slots.SlotError("invalid_configuration", f"{test_slots.ENABLE_ENV} must be on or off")

    monkeypatch.setattr(pytest_dispatch_cap, "_test_slots", lambda: _Slots)
    monkeypatch.delenv(test_slots.HOLDER_ENV, raising=False)
    monkeypatch.delenv("CI", raising=False)
    option = SimpleNamespace(numprocesses=4, maxprocesses=None, tx=None, collectonly=False, dist="no", distload=False)
    config = SimpleNamespace(option=option, getoption=lambda *_a, **_k: False)
    with pytest.raises(pytest.UsageError, match="test_slots_invalid_configuration"):
        pytest_dispatch_cap._acquire_test_slots(config, acquire=False)  # type: ignore[arg-type]
