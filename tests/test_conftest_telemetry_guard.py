"""Exercise the production-store guard in subprocess pytest sessions (#11075)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


def _run_guard(tmp_path: Path, source: str, *, workers: int = 0) -> subprocess.CompletedProcess[str]:
    (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    (tmp_path / "conftest.py").write_text(
        textwrap.dedent("""\
        from pathlib import Path
        from tests.conftest import _TelemetryIsolation

        def pytest_configure(config):
            production = Path(__file__).parent / "repo/batch_state/telemetry/events"
            config.pluginmanager.register(_TelemetryIsolation(production), "telemetry-isolation")
        """),
        encoding="utf-8",
    )
    (tmp_path / "test_probe.py").write_text(textwrap.dedent(source), encoding="utf-8")
    return subprocess.run(
        [
            sys.executable, "-m", "pytest", "-q", "-p", "xdist.plugin",
            "-c", str(tmp_path / "pytest.ini"), "--confcutdir", str(tmp_path),
            "--basetemp", str(tmp_path / "pytest-tmp"), "-n", str(workers), str(tmp_path / "test_probe.py"),
        ],
        env={**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"},
        capture_output=True,
        text=True,
        timeout=120,
    )


@pytest.mark.parametrize("workers", [0, 2])
def test_session_redirect_covers_collection_fixtures_and_children(tmp_path: Path, workers: int) -> None:
    result = _run_guard(tmp_path, """\
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
        """, workers=workers)

    assert result.returncode == 0, result.stdout + result.stderr
    assert not (tmp_path / "repo/batch_state/telemetry/events").exists()
    event_files = {path.resolve() for path in (tmp_path / "pytest-tmp").rglob("telemetry-events*/*.jsonl")}
    assert len(event_files) == (workers or 1)
    for path in event_files:
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        assert {row["event_type"] for row in rows} == {"collection", "setup", "body", "child", "teardown"}


@pytest.mark.parametrize("mutation", ["create", "append", "delete", "rename"])
def test_guard_fails_a_deliberately_leaking_fixture(tmp_path: Path, mutation: str) -> None:
    production = tmp_path / "repo/batch_state/telemetry/events"
    production.mkdir(parents=True)
    existing = production / "existing.jsonl"
    existing.write_text('{"existing":true}\n', encoding="utf-8")
    result = _run_guard(tmp_path, f"""\
        from pathlib import Path
        import pytest
        from scripts.telemetry import emit

        @pytest.fixture(autouse=True)
        def leak(monkeypatch):
            root = Path(__file__).parent / "repo"
            production = root / "batch_state/telemetry/events"
            existing = production / "existing.jsonl"
            if {mutation!r} == "create":
                monkeypatch.delenv("LU_TELEMETRY_EVENTS_DIR")
                monkeypatch.setattr(emit, "__file__", str(root / "scripts/telemetry/emit.py"))
                emit.emit_event("deliberate-leak", {{}})
            elif {mutation!r} == "append":
                with existing.open("ab") as handle:
                    handle.write(b"leak\\n")
            elif {mutation!r} == "delete":
                existing.unlink()
            else:
                existing.rename(production / "renamed.jsonl")

        def test_leaking_fixture(leak):
            pass
        """)

    assert result.returncode == pytest.ExitCode.TESTS_FAILED, result.stdout + result.stderr
    assert "1 passed" in result.stdout
    assert "telemetry event guard: production event files changed" in result.stdout
    assert "batch_state/telemetry/events/" in result.stdout


def test_guard_accepts_unchanged_existing_events(tmp_path: Path) -> None:
    production = tmp_path / "repo/batch_state/telemetry/events"
    production.mkdir(parents=True)
    (production / "existing.jsonl").write_bytes(b"pre-existing\n")

    result = _run_guard(tmp_path, "def test_no_leak():\n    pass\n")

    assert result.returncode == 0, result.stdout + result.stderr
    assert (production / "existing.jsonl").read_bytes() == b"pre-existing\n"
