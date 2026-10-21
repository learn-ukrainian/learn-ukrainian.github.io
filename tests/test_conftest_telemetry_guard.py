"""Exercise the production-store guard in subprocess pytest sessions (#11075)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.common.repo_root import main_checkout_root
from tests.conftest import _TelemetryIsolation


def test_live_guard_covers_repo_and_primary_events(pytestconfig: pytest.Config) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    primary_root = main_checkout_root(repo_root).resolve()
    guard = pytestconfig.pluginmanager.get_plugin("telemetry-isolation")

    assert guard is not None
    assert guard.production_dirs
    assert guard.production_dirs == {
        (root / "batch_state" / "telemetry" / "events").resolve()
        for root in {repo_root, primary_root}
    }
    if primary_root != repo_root:
        assert (primary_root / "batch_state" / "telemetry" / "events").resolve() in guard.production_dirs


def _run_guard(
    tmp_path: Path, source: str, *, workers: int = 0, collect_only: bool = False
) -> subprocess.CompletedProcess[str]:
    (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    (tmp_path / "conftest.py").write_text(
        textwrap.dedent("""\
        from pathlib import Path
        from tests.conftest import _TelemetryIsolation

        def pytest_configure(config):
            production = Path(__file__).parent / "repo/batch_state/telemetry/events"
            primary = Path(__file__).parent / "primary/batch_state/telemetry/events"
            config.pluginmanager.register(_TelemetryIsolation((production, primary)), "telemetry-isolation")
        """),
        encoding="utf-8",
    )
    (tmp_path / "test_probe.py").write_text(textwrap.dedent(source), encoding="utf-8")
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "xdist.plugin",
            "-c",
            str(tmp_path / "pytest.ini"),
            "--confcutdir",
            str(tmp_path),
            "--basetemp",
            str(tmp_path / "pytest-tmp"),
            "-n",
            str(workers),
            *(["--collect-only"] if collect_only else []),
            str(tmp_path / "test_probe.py"),
        ],
        env={
            **os.environ,
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            # Reaped tmp_path names can be reused within the same second.
            # Keep rewritten probes out of the launcher's shared bytecode
            # cache, where equal-size source changes can hit stale .pyc files.
            "PYTHONPYCACHEPREFIX": str(tmp_path / "pycache"),
        },
        capture_output=True,
        text=True,
        timeout=120,
    )


@pytest.mark.parametrize("workers", [0, 2])
def test_session_redirect_covers_collection_fixtures_and_children(tmp_path: Path, workers: int) -> None:
    result = _run_guard(
        tmp_path,
        """\
        import json
        import os
        import subprocess
        import sys
        from pathlib import Path
        import pytest
        from scripts.telemetry.emit import emit_event

        emit_event("collection", {})

        @pytest.fixture(scope="session", autouse=True)
        def events():
            emit_event("setup", {})
            yield
            emit_event("teardown", {})

        @pytest.mark.parametrize("item", range(4))
        def test_emit(item):
            event_dir = Path(os.environ["LU_TELEMETRY_EVENTS_DIR"])
            assert "telemetry-events" in event_dir.name
            emit_event("body", {})
            subprocess.run(
                [sys.executable, "-c", "from scripts.telemetry.emit import emit_event; emit_event('child', {})"],
                check=True, timeout=30,
            )
        """,
        workers=workers,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert not (tmp_path / "repo/batch_state/telemetry/events").exists()
    assert not (tmp_path / "primary/batch_state/telemetry/events").exists()
    event_files = {path.resolve() for path in (tmp_path / "pytest-tmp").rglob("telemetry-events*/*.jsonl")}
    assert len(event_files) == (workers or 1)
    for path in event_files:
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        assert {row["event_type"] for row in rows} == {"collection", "setup", "body", "child", "teardown"}


@pytest.mark.parametrize("workers", [0, 2])
@pytest.mark.parametrize("route", ["default", "override", "file"])
@pytest.mark.parametrize("store", ["repo", "primary"])
def test_guard_fails_a_deliberately_leaking_fixture(tmp_path: Path, route: str, store: str, workers: int) -> None:
    production = tmp_path / store / "batch_state/telemetry/events"
    production.mkdir(parents=True)
    existing = production / "existing.jsonl"
    existing.write_text('{"existing":true}\n', encoding="utf-8")
    result = _run_guard(
        tmp_path,
        f"""\
        import sys
        from pathlib import Path
        import pytest
        from scripts.telemetry import emit as package_emit

        sys.path.insert(0, str(Path(package_emit.__file__).parents[1]))
        from telemetry import emit as top_level_emit
        emit = package_emit if {route!r} == "default" else top_level_emit

        @pytest.fixture(autouse=True)
        def leak(monkeypatch):
            root = Path(__file__).parent / {store!r}
            production = root / "batch_state/telemetry/events"
            existing = production / "existing.jsonl"
            if {route!r} == "default":
                monkeypatch.delenv("LU_TELEMETRY_EVENTS_DIR")
                monkeypatch.setattr(emit, "__file__", str(root / "scripts/telemetry/emit.py"))
            elif {route!r} == "override":
                monkeypatch.setenv("LU_TELEMETRY_EVENTS_DIR", str(production))
            else:
                monkeypatch.setattr(emit, "_event_file", lambda: existing)
            emit.emit_event("deliberate-leak", {{}})

        def test_leaking_fixture(leak):
            pass
        """,
        workers=workers,
    )

    assert result.returncode == pytest.ExitCode.TESTS_FAILED, result.stdout + result.stderr
    assert "1 passed" in result.stdout
    assert "telemetry event guard: test emitter attempted production writes" in result.stdout
    assert "batch_state/telemetry/events/" in result.stdout
    assert existing.read_bytes() == b'{"existing":true}\n'
    assert list(production.iterdir()) == [existing]


@pytest.mark.parametrize("collect_only", [False, True])
@pytest.mark.parametrize("mutation", ["create", "append", "delete", "rename"])
def test_guard_ignores_unrelated_writer(tmp_path: Path, mutation: str, collect_only: bool) -> None:
    production = tmp_path / "repo/batch_state/telemetry/events"
    production.mkdir(parents=True)
    existing = production / "existing.jsonl"
    existing.write_bytes(b"existing\n")
    result = _run_guard(
        tmp_path,
        f"""\
        import threading
        from pathlib import Path

        production = Path(__file__).parent / "repo/batch_state/telemetry/events"
        existing = production / "existing.jsonl"

        def unrelated_writer():
            if {mutation!r} == "create":
                (production / "external.jsonl").write_bytes(b"external\\n")
            elif {mutation!r} == "append":
                with existing.open("ab") as handle:
                    handle.write(b"external\\n")
            elif {mutation!r} == "delete":
                existing.unlink()
            else:
                existing.rename(production / "renamed.jsonl")

        writer = threading.Thread(target=unrelated_writer)
        writer.start()
        writer.join()

        def test_no_leak():
            pass
        """,
        collect_only=collect_only,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "telemetry event guard:" not in result.stdout + result.stderr
    if mutation == "create":
        assert (production / "external.jsonl").read_bytes() == b"external\n"
    elif mutation == "append":
        assert existing.read_bytes() == b"existing\nexternal\n"
    elif mutation == "delete":
        assert not existing.exists()
    else:
        assert (production / "renamed.jsonl").read_bytes() == b"existing\n"


def test_guard_accepts_unchanged_existing_events(tmp_path: Path) -> None:
    production = tmp_path / "repo/batch_state/telemetry/events"
    production.mkdir(parents=True)
    (production / "existing.jsonl").write_bytes(b"pre-existing\n")

    result = _run_guard(tmp_path, "def test_no_leak():\n    pass\n")

    assert result.returncode == 0, result.stdout + result.stderr
    assert (production / "existing.jsonl").read_bytes() == b"pre-existing\n"


def test_guard_is_disabled_after_session_cleanup(tmp_path: Path, tmp_path_factory, monkeypatch) -> None:
    from scripts.telemetry import emit

    production = tmp_path / "batch_state/telemetry/events"
    guard = _TelemetryIsolation((production,))
    cleanups = []
    config = SimpleNamespace(_tmp_path_factory=tmp_path_factory, add_cleanup=cleanups.append)
    previous = os.environ.get("LU_TELEMETRY_EVENTS_DIR")
    try:
        guard.pytest_sessionstart(SimpleNamespace(config=config))
        assert os.environ["LU_TELEMETRY_EVENTS_DIR"] != previous
    finally:
        for cleanup in reversed(cleanups):
            cleanup()
    assert os.environ.get("LU_TELEMETRY_EVENTS_DIR") == previous

    monkeypatch.setenv("LU_TELEMETRY_EVENTS_DIR", str(production))
    emit.emit_event("later-session", {})

    assert not guard.leaks
    assert [json.loads(path.read_text())["event_type"] for path in production.glob("*.jsonl")] == ["later-session"]


def test_guard_handles_a_crashed_worker_without_output() -> None:
    guard = _TelemetryIsolation(())

    guard.pytest_testnodedown(SimpleNamespace(), RuntimeError("worker crashed"))

    assert not guard.leaks
