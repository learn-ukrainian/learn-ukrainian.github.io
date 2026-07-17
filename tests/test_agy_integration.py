"""Integration test surfaces for Agy in ab discuss / inbox / lint.

The agent runtime registry already exposes ``agy`` via
``scripts/agent_runtime/registry.py`` (AgyAdapter, ``cli_available:
True``). These tests pin the bridge allowlists so future churn cannot
silently strip ``agy`` from ``ab discuss --with``.
"""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_VENV_PYTHON = _REPO_ROOT / ".venv" / "bin" / "python"


def _resolve_test_python() -> str:
    if _VENV_PYTHON.exists():
        return str(_VENV_PYTHON)
    try:
        common_dir = subprocess.check_output(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=_REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if common_dir:
            main_venv = (Path(common_dir) / ".." / ".venv" / "bin" / "python").resolve()
            if main_venv.exists():
                return str(main_venv)
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        pass
    active_venv = os.environ.get("VIRTUAL_ENV")
    if active_venv:
        candidate = Path(active_venv) / "bin" / "python"
        if candidate.exists():
            return str(candidate)
    raise RuntimeError(
        "No project virtualenv Python found. Run tests via `.venv/bin/python -m pytest`."
    )


_TEST_PYTHON = _resolve_test_python()


def _ensure_scripts_path() -> None:
    scripts_dir = str(_REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)


@pytest.fixture(autouse=True)
def _isolate_bridge_db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Per-test isolation for module-global bridge ``DB_PATH`` (#5247).

    ``_db`` binds ``DB_PATH`` via ``from ._config import DB_PATH``, so the
    two names are independent. Tests that only patch ``_db.DB_PATH`` leave
    ``_config.DB_PATH`` pointing at the shared broker file; under xdist a
    sibling worker/test can then make ``create_channel`` / ``get_channel``
    disagree and ``ab discuss`` exits before ``runtime_invoke``.

    Autouse so every test in this module — including future discuss
    siblings — inherits isolation without reintroducing the leak.
    """
    _ensure_scripts_path()
    from ai_agent_bridge import _config, _db

    db_path = tmp_path / "bridge.db"
    monkeypatch.setattr(_config, "DB_PATH", db_path)
    monkeypatch.setattr(_db, "DB_PATH", db_path)
    return db_path


@pytest.fixture
def discuss_bridge(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub channel I/O for discuss tests; relies on ``_isolate_bridge_db_path``."""
    _ensure_scripts_path()
    from ai_agent_bridge import _channels

    monkeypatch.setattr(_channels, "fetch_monitor_state", lambda: None)
    monkeypatch.setattr(_channels, "context_sha256", lambda path: "")
    monkeypatch.setattr(
        _channels,
        "load_channel_context",
        lambda channel: {"body": "", "revs": {}, "missing": []},
    )
    _channels.create_channel("shared", exist_ok=True)
    _channels.create_channel("agy-topic", exist_ok=True)


def test_registry_exposes_agy():
    """The agent_runtime registry is the canonical source of truth."""
    scripts_dir = str(_REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from agent_runtime.registry import AGENTS, available_agents

    assert "agy" in AGENTS, "agy must be in agent_runtime.registry.AGENTS"
    assert AGENTS["agy"]["cli_available"] is True
    assert AGENTS["agy"]["resume_policy"] == "bridge_only"
    assert "agy" in available_agents()


def test_delegate_dispatch_accepts_agy_agent():
    """``delegate.py dispatch --agent agy ...`` must parse without error."""
    result = subprocess.run(
        [
            _TEST_PYTHON,
            str(_REPO_ROOT / "scripts" / "delegate.py"),
            "dispatch",
            "--agent",
            "agy",
            "--task-id",
            "test-agy-argparse-probe",
            "--prompt",
            "noop",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(_REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"delegate dispatch --agent agy failed:\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert "test-agy-argparse-probe" in result.stdout


def test_ab_channels_valid_agents_includes_agy():
    scripts_dir = str(_REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from ai_agent_bridge import _channels

    importlib.reload(_channels)
    assert "agy" in _channels.VALID_AGENTS


def test_ab_channels_cli_marks_agy_cli_available():
    """``ab discuss`` requires the agent to be CLI-spawnable."""
    scripts_dir = str(_REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from ai_agent_bridge import _channels_cli

    assert _channels_cli._cli_available_agent("agy") is True


def test_ab_discuss_accepts_agy_in_with_list(
    discuss_bridge, monkeypatch,
):
    """``ab discuss --with agy`` passes agent validation and invokes runtime."""
    from types import SimpleNamespace

    _ensure_scripts_path()
    from ai_agent_bridge import _channels_cli

    invoked: list[str] = []
    invoke_kwargs: list[dict] = []

    def fake_invoke(agent_name: str, prompt: str, **kwargs):
        invoked.append(agent_name)
        invoke_kwargs.append(kwargs)
        return SimpleNamespace(
            ok=True,
            response="[AGREE] agy first take",
            stderr_excerpt="",
            session_id="agy-session-1",
        )

    monkeypatch.setattr("agent_runtime.runner.invoke", fake_invoke)

    args = SimpleNamespace(
        channel="agy-topic",
        body="Does STRICT grounding measure model discipline fairly?",
        with_agents="agy",
        max_rounds=1,
        review=False,
        models=None,
    )

    assert _channels_cli._handle_discuss(args) == 0
    assert invoked == ["agy"]
    assert invoke_kwargs[0].get("model") is None


def test_ab_discuss_passes_agy_pro_model_override(discuss_bridge, monkeypatch):
    """``--models agy:gemini-3.1-pro-high`` reaches runtime_invoke as model=."""
    from types import SimpleNamespace

    _ensure_scripts_path()
    from ai_agent_bridge import _channels_cli

    invoke_kwargs: list[dict] = []

    def fake_invoke(agent_name: str, prompt: str, **kwargs):
        invoke_kwargs.append(kwargs)
        return SimpleNamespace(
            ok=True,
            response="[AGREE] pro take",
            stderr_excerpt="",
            session_id="agy-session-pro",
        )

    monkeypatch.setattr("agent_runtime.runner.invoke", fake_invoke)

    args = SimpleNamespace(
        channel="agy-topic",
        body="STRICT bakeoff fairness?",
        with_agents="agy",
        max_rounds=1,
        review=False,
        models="agy:gemini-3.1-pro-high",
    )

    assert _channels_cli._handle_discuss(args) == 0
    assert invoke_kwargs[0]["model"] == "gemini-3.1-pro-high"
