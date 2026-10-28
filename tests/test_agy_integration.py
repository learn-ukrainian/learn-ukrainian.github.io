"""Integration test surfaces for Agy in ab discuss / inbox / lint.

The agent runtime registry already exposes ``agy`` via
``scripts/agent_runtime/registry.py`` (AgyAdapter, ``cli_available:
True``). These tests pin the bridge allowlists so future churn cannot
silently strip ``agy`` from ``ab discuss --with``.
"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]


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
    from scripts.ai_agent_bridge import _config, _db

    db_path = tmp_path / "bridge.db"
    monkeypatch.setattr(_config, "DB_PATH", db_path)
    monkeypatch.setattr(_db, "DB_PATH", db_path)
    monkeypatch.setattr(
        "scripts.fleet_comms.artifacts.default_plane_root",
        lambda **_kwargs: tmp_path / "authority-plane",
    )
    return db_path


@pytest.fixture
def discuss_bridge(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub channel I/O for discuss tests; relies on ``_isolate_bridge_db_path``."""
    _ensure_scripts_path()
    from scripts.ai_agent_bridge import _channels

    monkeypatch.setattr(_channels, "fetch_monitor_state", lambda: None)
    monkeypatch.setattr(_channels, "context_sha256", lambda path: "")
    monkeypatch.setattr(
        _channels,
        "load_channel_context",
        lambda channel: {"body": "", "revs": {}, "missing": []},
    )
    _channels.create_channel("shared", exist_ok=True)
    _channels.create_channel("agy-topic", exist_ok=True)


def test_delegate_dispatch_accepts_agy_agent(tmp_path, monkeypatch, capsys):
    """The v2 parser and dry-run accept AGY regardless of checkout refs."""
    from scripts.dispatcher import cli, git

    task_id = f"test-agy-argparse-probe-{uuid.uuid4().hex}"
    monkeypatch.setattr(
        git, "worktree_plan", lambda *args, **kwargs: (tmp_path / task_id, f"agy/{task_id}", "a" * 40),
    )
    result = cli.main(
        [
            "dispatch",
            "--agent",
            "agy",
            "--model",
            "gemini-3.8-flash-high",
            "--task-id",
            task_id,
            "--prompt",
            "noop",
            # #9275: agy without a Ukrainian classification is the bounded fallback.
            "--research-task-family",
            "ukrainian-authoring",
            # This checks the write-mode argv; read-only AGY runs inside the bubblewrap boundary (C-3027).
            "--mode",
            "workspace-write",
            "--dry-run",
        ],
    )
    captured = capsys.readouterr()
    assert result == 0, f"dispatch --agent agy failed:\n{captured.out}\n{captured.err}"
    assert task_id in captured.out
    plan = json.loads(captured.out)
    assert Path(plan["record_path"]).name == f"{task_id}.json"
    assert plan["argv"][0] == "agy"
    assert plan["argv"][plan["argv"].index("--model") + 1] == "gemini-3.8-flash-high"


def test_ab_discuss_accepts_agy_in_multi_participant_list(discuss_bridge, monkeypatch):
    """ACP discussion accepts Agy as one member of a bounded participant set."""
    _ensure_scripts_path()
    from scripts.ai_agent_bridge import _channels_cli

    observed: dict[str, object] = {}

    def fake_discussion(**kwargs):
        observed.update(kwargs)
        return {
            "conversation_id": "conversation_" + ("a" * 32),
            "state": "COMPLETE",
            "rounds_completed": 1,
            "synthesis": "ACP synthesis",
        }

    monkeypatch.setattr("agent_runtime.acpx_discuss.run_discussion", fake_discussion)

    args = SimpleNamespace(
        channel="agy-topic",
        body="Does STRICT grounding measure model discipline fairly?",
        with_agents="agy,pool",
        max_rounds=1,
        review=False,
        review_profile="ukrainian",
        models=None,
    )

    assert _channels_cli._handle_discuss(args) == 0
    assert observed["participants"] == ("agy", "pool")
    assert observed["models"] is None


def test_ab_discuss_passes_registered_agy_model_pin(discuss_bridge, monkeypatch):
    """The registered Agy ACP model pin reaches the durable controller."""
    _ensure_scripts_path()
    from scripts.ai_agent_bridge import _channels_cli

    observed: dict[str, object] = {}

    def fake_discussion(**kwargs):
        observed.update(kwargs)
        return {
            "conversation_id": "conversation_" + ("b" * 32),
            "state": "COMPLETE",
            "rounds_completed": 1,
            "synthesis": "ACP synthesis",
        }

    monkeypatch.setattr("agent_runtime.acpx_discuss.run_discussion", fake_discussion)

    args = SimpleNamespace(
        channel="agy-topic",
        body="STRICT bakeoff fairness?",
        with_agents="agy,pool",
        max_rounds=1,
        review=False,
        review_profile="ukrainian",
        models="agy:gemini-3.8-flash-high",
    )

    assert _channels_cli._handle_discuss(args) == 0
    assert observed["models"] == {"agy": "gemini-3.8-flash-high"}
