"""Tests for delegate.py --check-budget pre-dispatch guard."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import types
import urllib.error
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from agents_extensions.shared.session_streams.db import SessionStreamDatabase
from agents_extensions.shared.session_streams.model import LeaseHolder
from agents_extensions.shared.session_streams.store import SessionStreamStore

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import pytest

import delegate
from scripts.api.subscription_usage import compute_usage_pace, pace_is_deficit
from tests.test_ask_review_admission_floor import ordinary_review_scope as ordinary_review_scope


@pytest.fixture(autouse=True)
def _allow_notebook_dispatch(monkeypatch):
    monkeypatch.setenv("LU_ALLOW_NOTEBOOK_DISPATCH", "1")


def _use_fallbacks(monkeypatch, table: dict[str, str]) -> None:
    """Serve ``table`` as the ``dispatch_fallbacks`` that ``resolve_and_admit`` hands the launch route."""
    monkeypatch.setattr("scripts.common.fallback_substitutions.load_dispatch_fallbacks", lambda _path: dict(table))


def _fallbacks() -> dict[str, str]:
    """The ``dispatch_fallbacks`` table as the launch route receives it (patched by ``_use_fallbacks``)."""
    from scripts.common import fallback_substitutions

    return fallback_substitutions.load_dispatch_fallbacks(delegate._FALLBACK_SUBS_PATH)


class _FakeBudgetResponse:
    """Configurable fake for /routing-budget responses (supports rec, agents status for hard sub, stale, empty)."""

    def __init__(
        self,
        recommended: str = "codex",
        *,
        status_for_agent: str | None = None,
        burn_for_agent: float | None = None,
        records_loaded: int = 5,
        stale: bool = False,
        empty: bool = False,
    ):
        self.recommended = recommended
        self.status_for_agent = status_for_agent
        self.burn_for_agent = burn_for_agent
        self.records_loaded = 0 if empty else records_loaded
        self.stale = stale
        self.empty = empty

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc, _tb):
        return False

    def read(self):
        rec = {
            "primary_agent_for_code": None if self.empty else self.recommended,
            "rationale": "fixture rationale (empty)" if self.empty else "fixture rationale",
            "warnings": ["empty snapshot"] if self.empty else [],
        }
        agents = {}
        # default fixture agents for claude/codex etc
        for a in ("claude", "codex", "gemini"):
            if a == "claude":
                agents[a] = {
                    "interactive": {"status": "cool", "burn_pct_7d": 10.0},
                    "status": "cool",
                    "burn_pct_7d": 10.0,
                    "resets_at": "2026-07-14T00:00:00Z",
                }
            else:
                agents[a] = {"status": "cool", "burn_pct_7d": 20.0, "resets_at": "2026-07-14T00:00:00Z"}
        if self.status_for_agent:
            tgt = self.status_for_agent
            if tgt == "claude":
                agents["claude"]["status"] = "near_cap"
                agents["claude"]["interactive"]["status"] = "near_cap"
                agents["claude"]["interactive"]["burn_pct_7d"] = self.burn_for_agent or 95.0
            elif tgt in agents:
                agents[tgt]["status"] = self.status_for_agent
                agents[tgt]["burn_pct_7d"] = self.burn_for_agent or 95.0
        payload = {
            "recommendation": rec,
            "agents": agents if not self.empty else {},
            "diagnostics": {
                "records_loaded": self.records_loaded,
                "stale": self.stale,
                "data_age_s": 1000 if self.stale else 10,
            },
            "generated_at": "2026-07-07T12:00:00Z",
        }
        return json.dumps(payload).encode("utf-8")


class _FakeHealthResponse:
    """Fake for the /api/health probe cmd_dispatch runs before every dispatch (#5817)."""

    status = 200

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc, _tb):
        return False


def _urlopen_routing(budget_response):
    """Route urlopen by URL: /api/health → healthy probe, anything else → budget fake.

    cmd_dispatch probes /api/health unconditionally (#5817 monitor supervision);
    budget fixtures only model /api/state/routing-budget, so the probe needs its
    own response or it trips on the missing ``status`` attribute.
    """

    def _fake(url, *_args, **_kwargs):
        if "/api/health" in str(url):
            return _FakeHealthResponse()
        return budget_response

    return _fake


class _FakeStdin:
    def write(self, _data):
        pass

    def close(self):
        pass


class _FakeProc:
    pid = 12345
    stdin = _FakeStdin()


def _dispatch_args(*extra: str):
    return delegate.build_parser().parse_args(
        [
            "dispatch",
            "--agent",
            "claude",
            "--task-id",
            "budget-check-fixture",
            "--prompt",
            "no-op",
            "--mode",
            "read-only",
            "--cwd",
            str(delegate._REPO_ROOT),
            *extra,
        ]
    )


def _patch_spawn(monkeypatch, tmp_path):
    from tests.helpers.dispatch_checkout import isolate_dispatch_repo

    isolate_dispatch_repo(monkeypatch, tmp_path, delegate)
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    monkeypatch.setattr(delegate.subprocess, "Popen", lambda *_args, **_kwargs: _FakeProc())
    monkeypatch.setattr(delegate, "_session_stream_store", lambda: _session_stream_store(tmp_path))
    telemetry = type(
        "_Telemetry",
        (),
        {"model": "fixture-model", "effort": "high", "cli_version": "fixture"},
    )()
    monkeypatch.setattr(
        "agent_runtime.telemetry.resolve_dispatch_start_telemetry",
        lambda **_kwargs: telemetry,
    )


def _track_worker_spawns(monkeypatch):
    spawned = []

    def fake_popen(*args, **kwargs):
        command = args[0] if args else ()
        if isinstance(command, (list, tuple)) and "_worker" in command:
            spawned.append((args, kwargs))
        return _FakeProc()

    monkeypatch.setattr(delegate.subprocess, "Popen", fake_popen)
    return spawned


def _session_stream_store(tmp_path: Path) -> SessionStreamStore:
    database = SessionStreamDatabase(tmp_path / "session-streams.sqlite3")
    connection = database.connect()
    connection.close()
    return SessionStreamStore(database)


_CURSOR_DRIVER_STREAM_ID = "epic:4707"


@pytest.fixture
def cursor_driver_stream_id() -> str:
    return _CURSOR_DRIVER_STREAM_ID


def _cursor_driver_store(tmp_path: Path, *, process_id: int = 99999, host_id: str | None = None) -> SessionStreamStore:
    store = _session_stream_store(tmp_path)
    store.open_session(
        stream_id=_CURSOR_DRIVER_STREAM_ID,
        holder=LeaseHolder(
            agent="cursor",
            harness="cursor-agent",
            instance_id="cursor-driver-fixture",
            task_id="cursor-driver-fixture",
            process_id=process_id,
            host_id=host_id,
        ),
        lineage_id="cursor-driver-lineage",
        ttl_seconds=600,
        now=datetime.now(UTC),
    )
    return store


def _self_cursor_driver_store(tmp_path: Path) -> SessionStreamStore:
    """A live Cursor driver lease held by this process (the self-dispatch case)."""
    return _cursor_driver_store(tmp_path, process_id=os.getpid())


def test_check_budget_warns_when_agent_mismatch(monkeypatch, tmp_path, capsys):
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        delegate.urllib.request,
        "urlopen",
        _urlopen_routing(_FakeBudgetResponse("codex")),
    )

    rc = delegate.cmd_dispatch(_dispatch_args("--check-budget"))

    assert rc == 0
    captured = capsys.readouterr()
    assert "⚠ ROUTING WARNING: budget recommends --agent codex, you passed --agent claude." in captured.err
    assert "Rationale: fixture rationale" in captured.err


def _force_dispatch(monkeypatch, tmp_path, budget):
    """Spawn a forced budget-checked dispatch against ``budget`` and return ``(stderr, state)``."""
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(delegate, "_fetch_routing_budget", lambda: budget)
    monkeypatch.setattr(delegate, "_load_reset_reserve", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(delegate.urllib.request, "urlopen", _urlopen_routing(_FakeHealthResponse()))
    rc = delegate.cmd_dispatch(_dispatch_args("--check-budget", "--force-agent"))
    assert rc == 0
    state = json.loads((tmp_path / "tasks" / "budget-check-fixture.json").read_text(encoding="utf-8"))
    return state


def test_force_agent_on_a_deficit_keeps_diagnostics_and_the_seat(monkeypatch, tmp_path, capsys):
    """#9673: a deficit still prints and is stored; --force-agent does not substitute."""
    claude = _fresh_lane(
        status="near_cap",
        codexbar={"weekly_remaining_pct": 80.0, "primary_remaining_pct": 3.0, "will_last_to_reset": True},
    )
    codex = _fresh_lane(status="cool", codexbar={"weekly_remaining_pct": 90.0, "will_last_to_reset": True})
    budget = {
        "recommendation": {"primary_agent_for_code": "codex", "rationale": "fixture rationale", "warnings": []},
        "agents": {"claude": claude, "codex": codex},
        "diagnostics": {"records_loaded": 10, "stale": False, "codexbar_data_available": True},
    }
    monkeypatch.setattr(delegate, "_fetch_routing_budget", lambda: budget)
    monkeypatch.setattr(delegate, "_load_reset_reserve", lambda *_args, **_kwargs: {})
    assert delegate._resolve_agent_with_budget_guard("claude", fallbacks={"claude": "codex"}) == "codex"
    capsys.readouterr()

    state = _force_dispatch(monkeypatch, tmp_path, budget)
    err = capsys.readouterr().err
    assert "HARD AUTO-SUBSTITUTE" not in err
    assert "⚠ ROUTING CHECK: lane claude:" in err
    assert "3% remaining" in err
    assert state["agent"] == "claude"
    assert state["substitution"] is None
    facts = state["routing_facts"]
    assert facts["health"] == "healthy"
    assert facts["plan_remaining_pct"] == 3.0
    assert facts["capacity"] == "avoid"


def test_force_agent_on_a_healthy_lane_records_quota_and_health(monkeypatch, tmp_path, capsys):
    """A cool lane still prints its quota and stores health, with no substitution."""
    claude = _fresh_lane(status="cool", codexbar={"weekly_remaining_pct": 80.0, "will_last_to_reset": True})
    budget = {
        "recommendation": {"primary_agent_for_code": "claude", "rationale": "fixture rationale", "warnings": []},
        "agents": {"claude": claude},
        "diagnostics": {"records_loaded": 10, "stale": False, "codexbar_data_available": True},
    }
    state = _force_dispatch(monkeypatch, tmp_path, budget)
    err = capsys.readouterr().err
    assert "HARD AUTO-SUBSTITUTE" not in err
    assert "⚠ ROUTING CHECK: lane claude: plan status cool (80% remaining)" in err
    assert state["agent"] == "claude"
    assert state["substitution"] is None
    facts = state["routing_facts"]
    assert facts["health"] == "healthy"
    assert facts["plan_remaining_pct"] == 80.0
    assert facts["capacity"] == "verified"


def test_force_agent_records_explicit_unknown_health(monkeypatch, tmp_path, capsys):
    """Unknown lane health is printed with its basis and stored, next to a known quota."""
    from scripts.api.lane_health import BASIS_SCAN_UNAVAILABLE

    claude = _fresh_lane(
        status="cool",
        health={"healthy": None, "basis": BASIS_SCAN_UNAVAILABLE},
        codexbar={"weekly_remaining_pct": 40.0, "will_last_to_reset": True},
    )
    budget = {
        "recommendation": {"primary_agent_for_code": "claude", "rationale": "fixture rationale", "warnings": []},
        "agents": {"claude": claude},
        "diagnostics": {"records_loaded": 10, "stale": False, "codexbar_data_available": True},
    }
    state = _force_dispatch(monkeypatch, tmp_path, budget)
    err = capsys.readouterr().err
    assert f"⚠ lane claude health unknown ({BASIS_SCAN_UNAVAILABLE}); not counted as healthy" in err
    assert "40% remaining" in err
    facts = state["routing_facts"]
    assert facts["health"] == "unknown"
    assert facts["health_basis"] == BASIS_SCAN_UNAVAILABLE
    assert facts["plan_remaining_pct"] == 40.0
    assert state["agent"] == "claude"
    assert state["substitution"] is None


def test_force_agent_records_unknown_when_telemetry_is_unavailable(monkeypatch, tmp_path, capsys):
    """Monitor API failure stays an explicit unknown in stderr and the task record."""
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _seconds: None)

    def unavailable():
        raise delegate.MonitorApiUnavailable("down")

    monkeypatch.setattr(delegate, "_fetch_routing_budget", unavailable)
    monkeypatch.setattr(delegate.urllib.request, "urlopen", _urlopen_routing(_FakeHealthResponse()))

    rc = delegate.cmd_dispatch(_dispatch_args("--check-budget", "--force-agent"))

    assert rc == 0
    err = capsys.readouterr().err
    assert "⚠ ROUTING CHECK SKIPPED: Monitor API unreachable" in err
    assert "⚠ lane claude health unknown (lane health record missing); not counted as healthy" in err
    assert "HARD AUTO-SUBSTITUTE" not in err
    state = json.loads((tmp_path / "tasks" / "budget-check-fixture.json").read_text(encoding="utf-8"))
    facts = state["routing_facts"]
    assert facts["health"] == "unknown"
    assert facts["plan_remaining_pct"] is None
    assert facts["observation_freshness"] == "unknown"
    assert state["agent"] == "claude"
    assert state["substitution"] is None


def test_force_agent_records_unknown_on_an_empty_budget(monkeypatch, tmp_path, capsys):
    """An empty ledger keeps the existing UNKNOWN line and stores an unknown health and quota."""
    budget = {
        "recommendation": {"primary_agent_for_code": None, "warnings": ["empty snapshot"]},
        "agents": {},
        "diagnostics": {"records_loaded": 0, "codexbar_data_available": False},
    }
    state = _force_dispatch(monkeypatch, tmp_path, budget)
    err = capsys.readouterr().err
    assert "⚠ ROUTING CHECK UNKNOWN: budget UNKNOWN" in err
    assert "health unknown" in err
    assert "HARD AUTO-SUBSTITUTE" not in err
    facts = state["routing_facts"]
    assert facts["health"] == "unknown"
    assert facts["plan_remaining_pct"] is None
    assert facts["observation_freshness"] == "unknown"
    assert state["agent"] == "claude"
    assert state["substitution"] is None


def test_check_budget_skipped_when_api_down(monkeypatch, tmp_path, capsys):
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(
        delegate.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(urllib.error.URLError("timeout")),
    )

    rc = delegate.cmd_dispatch(_dispatch_args("--check-budget"))

    assert rc == 0
    assert "⚠ ROUTING CHECK SKIPPED: Monitor API unreachable" in capsys.readouterr().err


def test_check_budget_off_by_default(monkeypatch, tmp_path, capsys):
    _patch_spawn(monkeypatch, tmp_path)

    def fail_on_budget_fetch(url, *_args, **_kwargs):
        if "/api/health" in str(url):
            return _FakeHealthResponse()
        raise AssertionError("routing-budget urlopen should not be called unless --check-budget is passed")

    monkeypatch.setattr(delegate.urllib.request, "urlopen", fail_on_budget_fetch)

    rc = delegate.cmd_dispatch(_dispatch_args())

    assert rc == 0
    assert "ROUTING" not in capsys.readouterr().err


def test_check_budget_dry_run_does_not_spawn(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    monkeypatch.setattr(delegate.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        delegate.urllib.request,
        "urlopen",
        _urlopen_routing(_FakeBudgetResponse("codex")),
    )

    def fail_if_spawned(*_args, **_kwargs):
        raise AssertionError("dry-run must not spawn a worker")

    monkeypatch.setattr(delegate.subprocess, "Popen", fail_if_spawned)

    args = _dispatch_args("--check-budget", "--dry-run")
    args.cwd = None  # Exercise the new default without allowing any git or worker spawn.
    rc = delegate.cmd_dispatch(args)

    assert rc == 0
    captured = capsys.readouterr()
    lines = captured.out.strip().splitlines()
    assert len(lines) == 2
    assert lines[0] == "budget-check-fixture"
    assert len(lines[1]) == 16
    assert int(lines[1], 16) >= 0
    state = json.loads((tmp_path / "tasks" / "budget-check-fixture.json").read_text(encoding="utf-8"))
    assert state["worktree_path"] is not None
    assert not Path(state["worktree_path"]).exists()
    assert lines[1] == state["run_nonce"]
    assert "ROUTING WARNING" in captured.err


def test_issue_9272_review_dry_run_never_prints_grok_substitution(ordinary_review_scope, monkeypatch, tmp_path, capsys):
    import subprocess

    from tests.test_ask_review_admission_floor import _git

    worktree = ordinary_review_scope / ".worktrees/dispatch/codex/budget-check-fixture"
    _git(ordinary_review_scope, "worktree", "add", "-b", "review-target", str(worktree), "HEAD")
    real_popen = subprocess.Popen
    _patch_spawn(monkeypatch, tmp_path)
    spawned = _track_worker_spawns(monkeypatch)
    worker_popen = subprocess.Popen

    def fixture_popen(command, *args, **kwargs):
        if command[0] == "git":
            return real_popen(command, *args, **kwargs)
        return worker_popen(command, *args, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", fixture_popen)
    monkeypatch.setattr(delegate, "_REPO_ROOT", ordinary_review_scope)
    monkeypatch.chdir(ordinary_review_scope)
    # The fixture already materializes the fetched ref; the dry run never contacts a remote.
    monkeypatch.setattr(delegate, "_fetch_existing_branch", lambda _branch: None)
    monkeypatch.setattr(delegate.urllib.request, "urlopen", _urlopen_routing(_FakeBudgetResponse()))
    monkeypatch.setattr(delegate, "_fetch_routing_budget", lambda: _codex_cursor_budget(codex_status="near_cap"))
    monkeypatch.setattr(delegate, "_load_reset_reserve", lambda *_a, **_k: {})
    args = _dispatch_args(
        "--agent",
        "codex",
        "--model",
        "gpt-6.1-sol",
        "--require-review-verdict",
        "--branch",
        "review-target",
        "--check-budget",
        "--dry-run",
    )
    args.cwd = None
    args.worktree = "auto"
    assert delegate.cmd_dispatch(args) == 0
    assert not spawned
    assert "HARD AUTO-SUBSTITUTE" not in capsys.readouterr().err
    state = json.loads((tmp_path / "tasks" / "budget-check-fixture.json").read_text(encoding="utf-8"))
    assert state["agent"] == "codex" and state["substitution"] is None
    assert state["review_author_model"] is None and state["review_risk"] is None


def _hot_language_budget():
    def lane(status):
        return {
            "status": status,
            "interactive": {"status": status, "burn_pct_7d": 99.0 if status == "hot" else 10.0},
            "burn_pct_7d": 99.0 if status == "hot" else 10.0,
            "resets_at": "2026-07-14T00:00:00Z",
        }

    return {
        "recommendation": {"primary_agent_for_code": "agy", "rationale": "fixture", "warnings": []},
        "agents": {
            "claude": lane("hot"),
            "codex": lane("hot"),
            "agy": lane("cool"),
            "grok": lane("cool"),
            "cursor": lane("cool"),
        },
        "diagnostics": {"records_loaded": 10, "stale": False, "codexbar_data_available": True},
    }


def test_language_lane_refuses_to_shed_onto_cursor(monkeypatch):
    monkeypatch.setattr(delegate, "_fetch_routing_budget", lambda: _hot_language_budget())
    with pytest.raises(delegate.BudgetGuardRefuseError, match="LANGUAGE-LANES RULE"):
        delegate._resolve_agent_with_budget_guard("claude", language_lane=True, fallbacks=_fallbacks())


@pytest.mark.parametrize("marker", ["--language-lane", "--review-profile=ukrainian"])
@pytest.mark.parametrize("force_agent", [False, True])
def test_language_dispatch_refuses_grok_before_spawn(monkeypatch, tmp_path, capsys, marker, force_agent):
    spawned = _track_worker_spawns(monkeypatch)
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    args = _dispatch_args(marker, *(["--force-agent"] if force_agent else []))
    args.agent = "grok"

    assert delegate.cmd_dispatch(args) == 2
    assert spawned == []
    refusal = capsys.readouterr().err
    assert "ROUTING REFUSED: LANGUAGE-LANES RULE (operator 2026-09-27)" in refusal
    assert "--agent grok cannot" in refusal
    assert "allowed lanes are claude, codex (GPT), and agy (Gemini)" in refusal


@pytest.mark.parametrize("agent", ["claude", "codex", "agy"])
def test_language_dispatch_admits_sanctioned_agents(monkeypatch, tmp_path, agent):
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(delegate.urllib.request, "urlopen", _urlopen_routing(_FakeBudgetResponse()))
    # #9275: agy without a Ukrainian authoring/review task family is the bounded fallback.
    args = _dispatch_args("--language-lane", "--research-task-family", "ukrainian-authoring")
    args.agent = agent
    assert delegate.cmd_dispatch(args) == 0


def test_language_fallback_refuses_grok_even_when_cool(monkeypatch):
    monkeypatch.setattr(delegate, "_fetch_routing_budget", lambda: _hot_language_budget())
    _use_fallbacks(monkeypatch, {"claude": "codex", "codex": "grok"})
    with pytest.raises(delegate.BudgetGuardRefuseError, match="cannot move to grok"):
        delegate._resolve_agent_with_budget_guard("claude", language_lane=True, fallbacks=_fallbacks())


def test_language_budget_guard_refuses_direct_grok_even_when_cool(monkeypatch):
    monkeypatch.setattr(delegate, "_fetch_routing_budget", lambda: _hot_language_budget())
    with pytest.raises(delegate.BudgetGuardRefuseError, match="--agent grok is outside"):
        delegate._resolve_agent_with_budget_guard("grok", language_lane=True, fallbacks=_fallbacks())


def _codex_reserve_budget(status: str = "warm"):
    """Codex threatened by a visible pace deficit the live free resets cover, so the owner verifies it (#9740).

    ``status="hot"`` keeps the same record behind a hot label from a non-pace source: owner AVOID.
    """
    now = datetime.now(UTC)
    return {
        "recommendation": {"primary_agent_for_code": "cursor", "rationale": "fixture", "warnings": []},
        "agents": {
            "claude": {"status": "hot", "interactive": {"status": "hot"}},
            "codex": {
                "status": status,
                "eligible": True,
                "health": {"healthy": True},
                "freshness": "fresh",
                "age_s": 10,
                "reset_credits": {
                    "available_count": 2,
                    "expires_at": ["2099-01-01T00:00:00Z", "2099-02-01T00:00:00Z"],
                    "fetched_at": datetime.now(UTC).isoformat(),
                },
                "codexbar": {
                    "will_last_to_reset": False,
                    "weekly_used_pct": 70.0,
                    "weekly_expected_pct": 50.0,
                    "weekly_pace_delta_pct": 20.0,
                    "weekly_resets_at": (now + timedelta(days=3)).isoformat(),
                    "freshness": "fresh",
                    "age_s": 10,
                    "fetched_at": now.isoformat(),
                    "windows": {"primary": {"remaining_pct": 15.0}},
                },
                "runtime": {"headroom_blocked": False, "rate_limited": 0, "last_rate_limited_at": None},
            },
            "cursor": {"status": "cool"},
        },
        "diagnostics": {"records_loaded": 5, "stale": False, "codexbar_data_available": True},
    }


def test_check_budget_uses_reset_reserve_for_codex(monkeypatch, capsys):
    monkeypatch.setattr(delegate, "_fetch_routing_budget", _codex_reserve_budget)
    monkeypatch.setattr(
        delegate,
        "_load_reset_reserve",
        lambda _root, **_kwargs: {
            "available": True,
            "provider": "codex",
            "remaining_resets": 2,
            "confirmed_at": (datetime.now(UTC) - timedelta(days=7)).isoformat(),
            "expires_at": "2099-03-01T00:00:00Z",
        },
    )
    assert delegate._resolve_agent_with_budget_guard("codex", fallbacks=_fallbacks()) == "codex"
    assert "reset reserve active (2 confirmed reset(s) remaining)" in capsys.readouterr().err


@pytest.mark.parametrize("language_lane", [False, True])
def test_reset_reserve_never_overrides_the_owner_avoid(monkeypatch, capsys, language_lane):
    """#9740 P1: an otherwise eligible reserve does not keep Codex the owner AVOIDs (hot label)."""
    budget = _codex_reserve_budget(status="hot")
    info = budget["agents"]["codex"]
    facts = delegate.credit_lane.routing_facts(
        "codex", info, model="gpt-6.1-sol", snapshot_metadata=budget["diagnostics"]
    )
    assert facts.capacity == delegate.credit_lane.CAPACITY_AVOID
    monkeypatch.setattr(delegate, "_fetch_routing_budget", lambda: budget)
    reserve = {
        "available": True,
        "provider": "codex",
        "remaining_resets": 2,
        "confirmed_at": (datetime.now(UTC) - timedelta(days=7)).isoformat(),
        "expires_at": "2099-03-01T00:00:00Z",
    }
    monkeypatch.setattr(delegate, "_load_reset_reserve", lambda _root, **_kwargs: reserve)
    # Every reserve precondition but the owner's verdict holds.
    assert delegate._codex_reset_reserve_eligible(reserve, info, owner_capacity=delegate.credit_lane.CAPACITY_VERIFIED)
    if language_lane:
        _use_fallbacks(monkeypatch, {"codex": "claude"})
        with pytest.raises(delegate.BudgetGuardRefuseError, match="LANGUAGE-LANES RULE"):
            delegate._resolve_agent_with_budget_guard("codex", language_lane=True, fallbacks=_fallbacks())
    else:
        assert delegate._resolve_agent_with_budget_guard("codex", fallbacks=_fallbacks()) != "codex"
    assert "reset reserve active" not in capsys.readouterr().err


@pytest.mark.parametrize("requested", ["codex", "claude"])
@pytest.mark.parametrize("inventory_state", ["available", "applied", "expired", "unknown", "stale"])
def test_budget_guard_bounds_old_assertion_by_snapshot_inventory(
    monkeypatch, tmp_path, capsys, inventory_state, requested
):
    from scripts.fleet import reset_reserve

    now = datetime.now(UTC)
    budget = _codex_reserve_budget()
    info = budget["agents"]["codex"]
    info["reset_credits"]["available_count"] = 1
    if inventory_state == "applied":
        info["reset_credits"]["available_count"] = 0
    elif inventory_state == "expired":
        info["reset_credits"]["expires_at"] = [(now - timedelta(seconds=1)).isoformat()]
    elif inventory_state == "unknown":
        info["reset_credits"] = None
    elif inventory_state == "stale":
        info["reset_credits"]["fetched_at"] = (now - timedelta(minutes=15)).isoformat()
    path = tmp_path / "batch_state" / "routing_budget" / "operator_reset_reserve.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": reset_reserve.SCHEMA_VERSION,
                "provider": "codex",
                "remaining_resets": 2,
                "confirmed_at": (now - timedelta(days=7)).isoformat(),
                "expires_at": "2099-03-01T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(delegate, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(delegate, "_fetch_routing_budget", lambda: budget)
    _use_fallbacks(monkeypatch, {"claude": "codex", "codex": "cursor"})
    monkeypatch.setattr(
        reset_reserve, "get_provider_usage_data", lambda _provider: pytest.fail("snapshot inventory must be used")
    )
    if requested == "claude" and inventory_state != "available":
        with pytest.raises(delegate.BudgetGuardRefuseError, match="LANGUAGE-LANES RULE"):
            delegate._resolve_agent_with_budget_guard(requested, language_lane=True, fallbacks=_fallbacks())
        assert "reset reserve active" not in capsys.readouterr().err
        return
    result = delegate._resolve_agent_with_budget_guard(
        requested, language_lane=requested == "claude", fallbacks=_fallbacks()
    )
    output = capsys.readouterr().err
    if inventory_state == "available":
        assert result == "codex"
        if requested == "codex":
            assert "reset reserve active (1 confirmed reset(s) remaining)" in output
    else:
        assert result == "cursor"
        assert "reset reserve active" not in output


def test_check_budget_stale_snapshot_does_not_activate_reset_reserve(monkeypatch, capsys):
    budget = _codex_reserve_budget()
    budget["diagnostics"]["stale"] = True
    monkeypatch.setattr(delegate, "_fetch_routing_budget", lambda: budget)
    monkeypatch.setattr(
        delegate,
        "_load_reset_reserve",
        lambda _root, **_kwargs: {
            "available": True,
            "provider": "codex",
            "remaining_resets": 2,
            "confirmed_at": (datetime.now(UTC) - timedelta(days=7)).isoformat(),
            "expires_at": "2099-03-01T00:00:00Z",
        },
    )
    assert delegate._resolve_agent_with_budget_guard("codex", fallbacks=_fallbacks()) == "codex"
    assert "reset reserve active" not in capsys.readouterr().err


def test_language_fallback_can_land_on_reserve_eligible_codex(monkeypatch):
    monkeypatch.setattr(delegate, "_fetch_routing_budget", _codex_reserve_budget)
    monkeypatch.setattr(
        delegate,
        "_load_reset_reserve",
        lambda _root, **_kwargs: {
            "available": True,
            "provider": "codex",
            "remaining_resets": 1,
            "confirmed_at": (datetime.now(UTC) - timedelta(days=7)).isoformat(),
            "expires_at": "2099-03-01T00:00:00Z",
        },
    )
    _use_fallbacks(monkeypatch, {"claude": "codex"})
    assert delegate._resolve_agent_with_budget_guard("claude", language_lane=True, fallbacks=_fallbacks()) == "codex"


def test_adapter_rejects_foreign_model_after_substitution(monkeypatch, tmp_path):
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    assert delegate._adapter_rejects_model("codex", "claude-fable-5-1") is True
    assert delegate._adapter_rejects_model("codex", "gpt-6.1-sol") is False
    assert not list(tmp_path.glob("codex-runtime-*.txt"))


def test_adapter_probe_keeps_model_when_invocation_cannot_run(monkeypatch):
    class _Boom:
        def build_invocation(self, **_kwargs):
            raise RuntimeError("grok CLI not found")

    fake = types.ModuleType("probe_adapter_mod")
    fake.Boom = _Boom
    monkeypatch.setitem(sys.modules, "probe_adapter_mod", fake)
    monkeypatch.setattr(
        "agent_runtime.registry.get_agent_entry",
        lambda _agent: {"adapter": "probe_adapter_mod:Boom"},
    )
    assert delegate._adapter_rejects_model("grok", "grok-4.7") is False


def _boom_adapter_for(monkeypatch, seat: str) -> None:
    """Point the real registry row for ``seat`` at an adapter whose invocation cannot be built."""
    from agent_runtime.registry import AGENTS

    class _Boom:
        def build_invocation(self, **_kwargs):
            raise RuntimeError("CLI not found")

    fake = types.ModuleType("probe_boom_mod")
    fake.Boom = _Boom
    monkeypatch.setitem(sys.modules, "probe_boom_mod", fake)
    monkeypatch.setitem(AGENTS[seat], "adapter", "probe_boom_mod:Boom")


def test_inconclusive_probe_warning_names_registry_seat_and_catalog_model(monkeypatch, capsys):
    # #9739: the warning is built from the registry and catalog spellings,
    # never from the caller's strings (CodeQL py/clear-text-logging-sensitive-data).
    _boom_adapter_for(monkeypatch, "grok")
    assert delegate._adapter_model_rejection("grok", "GROK-4.7") is None
    err = capsys.readouterr().err
    assert "⚠ model probe for grok could not verify grok-4.7: RuntimeError" in err
    assert "GROK-4.7" not in err


def test_inconclusive_probe_warning_gives_an_uncatalogued_model_a_fixed_label(monkeypatch, capsys):
    _boom_adapter_for(monkeypatch, "grok")
    assert delegate._adapter_model_rejection("grok", "not-a-catalog-model") is None
    err = capsys.readouterr().err
    assert "⚠ model probe for grok could not verify an uncatalogued model: RuntimeError" in err
    assert "not-a-catalog-model" not in err


def test_probe_log_labels_fall_back_without_registry_row_or_catalog(monkeypatch):
    from scripts.review import model_catalog

    assert delegate._registry_seat({"adapter": "x:Y"}) == "an unregistered seat"

    def unavailable(*_args, **_kwargs):
        raise model_catalog.ModelCatalogError("catalog unreadable")

    monkeypatch.setattr(model_catalog, "canonical_model_id", unavailable)
    assert delegate._catalog_model_label("gpt-6.1-sol") == "a model (catalog unavailable)"


def test_adapter_valueerror_before_spawn_is_failed(monkeypatch, tmp_path):
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))

    def boom(*_args, **_kwargs):
        raise ValueError("CodexAdapter: model='claude-fable-5-1' rejected; only 'gpt-6.1-sol' is approved")

    monkeypatch.setattr("agent_runtime.runner.invoke", boom)
    rc = delegate._run_worker(
        "pre-spawn",
        "codex",
        "prompt",
        "workspace-write",
        str(tmp_path),
        "claude-fable-5-1",
        30,
    )
    state = json.loads((tmp_path / "pre-spawn.json").read_text(encoding="utf-8"))
    assert rc == 1
    assert state["status"] == "failed"
    assert state["needs_finalize"] is False
    assert "rejected" in (state.get("last_error") or "")


def test_check_budget_hard_sub_on_near_cap_fresh(monkeypatch, tmp_path, capsys):
    """AC1: >90% (near_cap) on fresh → hard auto-sub, note substitution, uses fallback."""
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _s: None)
    # patch urlopen to return payload where passed claude is near_cap
    monkeypatch.setattr(
        delegate.urllib.request,
        "urlopen",
        _urlopen_routing(
            _FakeBudgetResponse("codex", status_for_agent="claude", burn_for_agent=95.0, records_loaded=10, stale=False)
        ),
    )

    rc = delegate.cmd_dispatch(_dispatch_args("--check-budget"))

    assert rc == 0
    out = capsys.readouterr()
    assert "HARD AUTO-SUBSTITUTE" in out.err
    assert "claude" in out.err and "codex" in out.err
    assert "per agent_fallback_substitutions.yaml" in out.err


def test_check_budget_no_hard_sub_on_stale(monkeypatch, tmp_path, capsys):
    """Stale → no hard sub, advisory only."""
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _s: None)
    monkeypatch.setattr(
        delegate.urllib.request,
        "urlopen",
        _urlopen_routing(
            _FakeBudgetResponse("codex", status_for_agent="claude", burn_for_agent=95.0, records_loaded=3, stale=True)
        ),
    )

    rc = delegate.cmd_dispatch(_dispatch_args("--check-budget"))

    assert rc == 0
    err = capsys.readouterr().err
    assert "stale" in err.lower()
    assert "HARD AUTO-SUBSTITUTE" not in err


def test_check_budget_reports_deficit_from_empty_ledger_codexbar(monkeypatch, tmp_path, capsys):
    """Empty ledger plus authoritative CodexBar deficit → hard-sub when fallback exists."""
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _s: None)
    monkeypatch.setattr(
        delegate,
        "_fetch_routing_budget",
        lambda: {
            "recommendation": {
                "primary_agent_for_code": "codex",
                "rationale": "Codex has live headroom.",
                "warnings": ["lane claude is in deficit (27% in deficit)"],
            },
            "agents": {
                "claude": {"status": "hot", "burn_pct_7d": 74.0},
                "codex": {"status": "cool", "burn_pct_7d": 20.0},
                "cursor": {"status": "cool", "burn_pct_7d": 5.0},
            },
            "diagnostics": {
                "records_loaded": 0,
                "stale": False,
                "codexbar_data_available": True,
            },
        },
    )

    rc = delegate.cmd_dispatch(_dispatch_args("--check-budget"))

    assert rc == 0
    err = capsys.readouterr().err
    assert "lane claude is in deficit (27% in deficit)" in err
    assert "budget UNKNOWN" not in err
    assert "HARD AUTO-SUBSTITUTE" in err
    assert "claude" in err and "codex" in err


def test_check_budget_reports_unknown_when_empty_ledger_subscription_snapshots_unavailable(
    monkeypatch, tmp_path, capsys
):
    """A failed guard refresh must be explicit rather than using the old silent empty design."""
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _s: None)
    monkeypatch.setattr(
        delegate,
        "_fetch_routing_budget",
        lambda: {
            "recommendation": {"primary_agent_for_code": None, "warnings": []},
            "agents": {},
            "diagnostics": {
                "records_loaded": 0,
                "stale": False,
                "codexbar_data_available": False,
            },
        },
    )

    rc = delegate.cmd_dispatch(_dispatch_args("--check-budget"))

    assert rc == 0
    err = capsys.readouterr().err
    assert (
        "budget UNKNOWN — could not verify subscription usage snapshots; lanes may be in deficit; no hard sub."
    ) in err
    assert "per design" not in err
    assert "HARD AUTO-SUBSTITUTE" not in err


def test_refuse_without_yaml_map(monkeypatch, tmp_path, capsys):
    """near_cap/hot without yaml mapping → refuse dispatch (exit non-zero)."""
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _s: None)
    _use_fallbacks(monkeypatch, {})
    monkeypatch.setattr(
        delegate.urllib.request,
        "urlopen",
        _urlopen_routing(
            _FakeBudgetResponse("codex", status_for_agent="claude", burn_for_agent=95.0, records_loaded=10, stale=False)
        ),
    )

    rc = delegate.cmd_dispatch(_dispatch_args("--check-budget"))

    assert rc == 2
    err = capsys.readouterr().err
    assert "ROUTING REFUSED" in err
    assert "HARD AUTO-SUBSTITUTE" not in err


def test_check_budget_hard_sub_ignores_unknown_fallback_target(monkeypatch, tmp_path, capsys):
    """A yaml typo must never dispatch a nonexistent adapter: unknown target → refuse."""
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _s: None)
    _use_fallbacks(monkeypatch, {"claude": "gemeni"})
    monkeypatch.setattr(
        delegate.urllib.request,
        "urlopen",
        _urlopen_routing(
            _FakeBudgetResponse("codex", status_for_agent="claude", burn_for_agent=95.0, records_loaded=10, stale=False)
        ),
    )

    rc = delegate.cmd_dispatch(_dispatch_args("--check-budget"))

    assert rc == 2
    err = capsys.readouterr().err
    assert "not a known dispatch agent" in err
    assert "ROUTING REFUSED" in err
    assert "HARD AUTO-SUBSTITUTE" not in err


def test_hard_sub_on_hot(monkeypatch, tmp_path, capsys):
    """hot status with yaml fallback → hard auto-sub (same path as near_cap)."""
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _s: None)
    monkeypatch.setattr(
        delegate,
        "_fetch_routing_budget",
        lambda: {
            "recommendation": {
                "primary_agent_for_code": "cursor",
                "rationale": "Codex hot; Cursor cool.",
                "warnings": [],
            },
            "agents": {
                "codex": {"status": "hot", "burn_pct_7d": 70.0, "resets_at": "2026-08-14T00:00:00Z"},
                "cursor": {"status": "cool", "burn_pct_7d": 10.0},
                "claude": {"status": "cool", "burn_pct_7d": 20.0},
            },
            "diagnostics": {"records_loaded": 5, "stale": False, "codexbar_data_available": True},
        },
    )
    _use_fallbacks(monkeypatch, {"codex": "cursor"})

    rc = delegate.cmd_dispatch(
        delegate.build_parser().parse_args(
            [
                "dispatch",
                "--agent",
                "codex",
                "--task-id",
                "budget-check-hot",
                "--cwd",
                str(delegate._REPO_ROOT),
                "--prompt",
                "no-op",
                "--mode",
                "read-only",
                "--check-budget",
            ]
        )
    )

    assert rc == 0
    err = capsys.readouterr().err
    assert "HARD AUTO-SUBSTITUTE" in err
    assert "codex" in err and "cursor" in err
    assert "status=hot" in err


def test_hard_sub_on_deficit(monkeypatch, tmp_path, capsys):
    """Visible pace deficit (won't last, delta outside the on-pace band) hard-subs even if status is warm."""
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _s: None)
    monkeypatch.setattr(
        delegate,
        "_fetch_routing_budget",
        lambda: {
            "recommendation": {
                "primary_agent_for_code": "cursor",
                "rationale": "Codex deficit.",
                "warnings": [],
            },
            "agents": {
                "codex": {
                    "status": "warm",
                    "burn_pct_7d": 55.0,
                    "codexbar": {
                        "will_last_to_reset": False,
                        "weekly_pace_delta_pct": 12.0,
                        "weekly_expected_pct": 40.0,
                        "pace_summary": "won't last",
                    },
                },
                "cursor": {"status": "cool", "burn_pct_7d": 5.0},
            },
            "diagnostics": {"records_loaded": 3, "stale": False, "codexbar_data_available": True},
        },
    )
    _use_fallbacks(monkeypatch, {"codex": "cursor"})

    rc = delegate.cmd_dispatch(
        delegate.build_parser().parse_args(
            [
                "dispatch",
                "--agent",
                "codex",
                "--task-id",
                "budget-check-deficit",
                "--cwd",
                str(delegate._REPO_ROOT),
                "--prompt",
                "no-op",
                "--mode",
                "read-only",
                "--check-budget",
            ]
        )
    )

    assert rc == 0
    err = capsys.readouterr().err
    assert "HARD AUTO-SUBSTITUTE" in err
    assert "will_last_to_reset=False" in err


def test_issue_9040_claude_snapshot_does_not_hard_substitute(monkeypatch, tmp_path, capsys):
    """Freshly reset Claude (1% used, delta +0.49, will_last false, status hot) stays on Claude.

    The producer labels this hot from weekly pace (``status_source``); only that
    source may be cleared by an on-pace reading (A8, #9740).
    """
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _s: None)
    _use_fallbacks(monkeypatch, {"claude": "codex"})
    monkeypatch.setattr(
        delegate,
        "_fetch_routing_budget",
        lambda: {
            "recommendation": {
                "primary_agent_for_code": "codex",
                "rationale": "claude marked hot by early-window pace",
                "warnings": [],
            },
            "agents": {
                "claude": {
                    "status": "hot",
                    "status_source": "weekly_pace",
                    "interactive": {"status": "hot", "burn_pct_7d": 1.0},
                    "burn_pct_7d": 1.0,
                    "remaining_pct": 99,
                    "resets_at": "2026-10-05T06:59:59Z",
                    # The producer's fresh probe: clearance needs it positively verified (A8).
                    "freshness": "fresh",
                    "age_s": 30.0,
                    "codexbar": {
                        "weekly_used_pct": 1.0,
                        "weekly_pace_delta_pct": 0.49,
                        "will_last_to_reset": False,
                        "pace_summary": "0% in deficit | Expected 1% used",
                        "freshness": "fresh",
                        "age_s": 30.0,
                    },
                },
                "codex": {"status": "hot", "burn_pct_7d": 70.0},
            },
            "diagnostics": {"records_loaded": 5, "stale": False, "codexbar_data_available": True},
        },
    )

    rc = delegate.cmd_dispatch(_dispatch_args("--check-budget"))

    assert rc == 0
    err = capsys.readouterr().err
    assert "HARD AUTO-SUBSTITUTE" not in err
    assert delegate._resolve_agent_with_budget_guard("claude", fallbacks=_fallbacks()) == "claude"


def test_genuine_pace_deficit_still_hard_substitutes(monkeypatch, tmp_path, capsys):
    """25% used and projected to run out 2 days before reset still substitutes."""
    now = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
    resets_at = (now + timedelta(days=5.75)).isoformat().replace("+00:00", "Z")
    pace = compute_usage_pace(25.0, resets_at, now=now)
    assert pace is not None
    assert pace["will_last_to_reset"] is False
    assert pace["delta_pct"] > 2
    assert pace_is_deficit(pace) is True
    runs_out_days_early = ((5.75 * 86400) - pace["eta_seconds"]) / 86400
    assert abs(runs_out_days_early - 2) < 0.05

    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _s: None)
    _use_fallbacks(monkeypatch, {"codex": "cursor"})
    monkeypatch.setattr(
        delegate,
        "_fetch_routing_budget",
        lambda: {
            "recommendation": {"primary_agent_for_code": "cursor", "rationale": "codex deficit", "warnings": []},
            "agents": {
                "codex": {
                    "status": "warm",
                    "burn_pct_7d": 25.0,
                    "remaining_pct": 75.0,
                    "codexbar": {
                        "weekly_used_pct": 25.0,
                        "weekly_pace_delta_pct": pace["delta_pct"],
                        "weekly_expected_pct": pace["expected_pct"],
                        "will_last_to_reset": False,
                        "pace_summary": "runs out 2d before reset",
                    },
                },
                "cursor": {"status": "cool", "burn_pct_7d": 5.0},
            },
            "diagnostics": {"records_loaded": 4, "stale": False, "codexbar_data_available": True},
        },
    )

    rc = delegate.cmd_dispatch(
        delegate.build_parser().parse_args(
            [
                "dispatch",
                "--agent",
                "codex",
                "--task-id",
                "budget-real-deficit",
                "--cwd",
                str(delegate._REPO_ROOT),
                "--prompt",
                "no-op",
                "--mode",
                "read-only",
                "--check-budget",
            ]
        )
    )

    assert rc == 0
    err = capsys.readouterr().err
    assert "HARD AUTO-SUBSTITUTE" in err
    assert "codex" in err and "cursor" in err
    assert "will_last_to_reset=False" in err


def test_refuse_hot_lists_cooler(monkeypatch, tmp_path, capsys):
    """hot lane with no yaml fallback → refuse and list cooler seats."""
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _s: None)
    _use_fallbacks(monkeypatch, {})
    monkeypatch.setattr(
        delegate,
        "_fetch_routing_budget",
        lambda: {
            "recommendation": {"primary_agent_for_code": "cursor", "rationale": "x", "warnings": []},
            "agents": {
                "codex": {"status": "hot", "burn_pct_7d": 80.0},
                "cursor": {"status": "cool", "burn_pct_7d": 5.0},
                "agy": {"status": "cool", "burn_pct_7d": 10.0},
            },
            "diagnostics": {"records_loaded": 4, "stale": False, "codexbar_data_available": True},
        },
    )

    rc = delegate.cmd_dispatch(
        delegate.build_parser().parse_args(
            [
                "dispatch",
                "--agent",
                "codex",
                "--task-id",
                "budget-refuse-hot",
                "--prompt",
                "no-op",
                "--mode",
                "read-only",
                "--check-budget",
            ]
        )
    )

    assert rc == 2
    err = capsys.readouterr().err
    assert "ROUTING REFUSED" in err
    assert "cursor" in err
    assert "agy" in err


def test_env_forces_budget_guard(monkeypatch, tmp_path, capsys):
    """LU_DISPATCH_CHECK_BUDGET=1 enables the guard without --check-budget."""
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _s: None)
    monkeypatch.setenv("LU_DISPATCH_CHECK_BUDGET", "1")
    monkeypatch.setattr(
        delegate.urllib.request,
        "urlopen",
        _urlopen_routing(_FakeBudgetResponse("codex")),
    )

    rc = delegate.cmd_dispatch(_dispatch_args())

    assert rc == 0
    assert "ROUTING WARNING" in capsys.readouterr().err


def test_dispatch_capacity_hint_printed_when_target_lane_busy(monkeypatch, tmp_path, capsys):
    """Task 2: non-blocking note printed when dispatching to busy lane while other lanes idle."""
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks_dir))
    monkeypatch.setattr(delegate, "_pid_alive", lambda _pid: True)

    # Create a running task for codex
    state_file = tasks_dir / "busy-task.json"
    state_file.write_text(
        json.dumps(
            {
                "task_id": "busy-task",
                "agent": "codex",
                "status": "running",
                "pid": 99999,
            }
        )
    )

    delegate._check_capacity_hint("codex")
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "💡 Note: lane 'codex' has 1 task(s) in flight while idle capacity is available in:" in captured.err
    assert "claude" in captured.err

    # Machine/JSON mode suppresses hints entirely
    mock_args = types.SimpleNamespace(json=True)
    delegate._check_capacity_hint("codex", args=mock_args)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def _refusing_cursor_dispatch_setup(monkeypatch, tmp_path, store):
    """Common mocks for Cursor dispatches that must be refused before Popen."""
    from scripts.orchestration import job_host_exec

    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(delegate.urllib.request, "urlopen", _urlopen_routing(_FakeBudgetResponse()))
    monkeypatch.setattr(delegate, "_session_stream_store", lambda: store)
    monkeypatch.setattr(job_host_exec, "decide_dispatch_placement", lambda **_kwargs: ("vps", "available", "host-job"))
    monkeypatch.setattr(
        job_host_exec,
        "forward_dispatch",
        lambda **_kwargs: pytest.fail("a refused Cursor dispatch must not forward to a worker host"),
    )
    return _track_worker_spawns(monkeypatch)


def test_dispatch_cursor_allows_worker_when_driver_lease_is_other_session(
    monkeypatch, tmp_path, capsys, cursor_driver_stream_id
):
    """A live Cursor driver lease from another lane/session is a NOTE, not a refusal."""
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(delegate.urllib.request, "urlopen", _urlopen_routing(_FakeBudgetResponse()))
    monkeypatch.setattr(delegate, "_session_stream_store", lambda: _cursor_driver_store(tmp_path))
    spawned = _track_worker_spawns(monkeypatch)

    rc = delegate.cmd_dispatch(_dispatch_args("--agent", "cursor"))

    assert rc == 0
    assert len(spawned) == 1
    err = capsys.readouterr().err
    assert (
        f"NOTE: Cursor driver live on {cursor_driver_stream_id} (other session); spawning a separate Cursor worker."
    ) in err
    assert "CAPACITY REFUSED" not in err


def test_dispatch_cursor_refuses_when_lease_holder_is_an_ancestor(monkeypatch, tmp_path, capsys):
    """Self-dispatch: the lease holder is an ancestor of the dispatching process."""
    store = _cursor_driver_store(tmp_path, process_id=os.getppid())
    spawned = _refusing_cursor_dispatch_setup(monkeypatch, tmp_path, store)

    rc = delegate.cmd_dispatch(_dispatch_args("--agent", "cursor"))

    assert rc == 2
    assert spawned == []
    err = capsys.readouterr().err
    assert "CAPACITY REFUSED" in err
    assert "inside the live Cursor driver session" in err


def test_dispatch_cursor_refuses_when_lease_holder_is_current_process(monkeypatch, tmp_path, capsys):
    """Self-dispatch: the lease holder is the dispatching process itself."""
    store = _cursor_driver_store(tmp_path, process_id=os.getpid())
    spawned = _refusing_cursor_dispatch_setup(monkeypatch, tmp_path, store)

    rc = delegate.cmd_dispatch(_dispatch_args("--agent", "cursor"))

    assert rc == 2
    assert spawned == []
    assert "CAPACITY REFUSED" in capsys.readouterr().err


def test_dispatch_cursor_allows_worker_when_lease_is_on_another_host(
    monkeypatch, tmp_path, capsys, cursor_driver_stream_id
):
    """A lease with a different holder_host_id belongs to another host's driver."""
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(delegate.urllib.request, "urlopen", _urlopen_routing(_FakeBudgetResponse()))
    monkeypatch.setattr(
        delegate,
        "_session_stream_store",
        lambda: _cursor_driver_store(tmp_path, process_id=os.getpid(), host_id="host-other"),
    )
    monkeypatch.setattr("scripts.api.occupancy_local.resolve_launcher_host_id", lambda: "host-self")
    spawned = _track_worker_spawns(monkeypatch)

    rc = delegate.cmd_dispatch(_dispatch_args("--agent", "cursor"))

    assert rc == 0
    assert len(spawned) == 1
    err = capsys.readouterr().err
    assert (
        f"NOTE: Cursor driver live on {cursor_driver_stream_id} (other session); spawning a separate Cursor worker."
    ) in err
    assert "CAPACITY REFUSED" not in err


def test_dispatch_cursor_ancestry_lookup_failure_allows_with_note(monkeypatch, tmp_path, capsys):
    """A /proc ancestry lookup failure is 'not self': spawn with a NOTE, never crash."""
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(delegate.urllib.request, "urlopen", _urlopen_routing(_FakeBudgetResponse()))
    monkeypatch.setattr(delegate, "_session_stream_store", lambda: _cursor_driver_store(tmp_path))

    def fail_parent_pid(_pid):
        raise PermissionError("no /proc access")

    monkeypatch.setattr(delegate, "_proc_parent_pid", fail_parent_pid)
    spawned = _track_worker_spawns(monkeypatch)

    rc = delegate.cmd_dispatch(_dispatch_args("--agent", "cursor"))

    assert rc == 0
    assert len(spawned) == 1
    err = capsys.readouterr().err
    assert "NOTE: unable to verify the Cursor driver lease holder ancestry" in err
    assert "CAPACITY REFUSED" not in err


def test_dispatch_cursor_malformed_session_stream_store_still_refuses(monkeypatch, tmp_path, capsys):
    """An unreadable/malformed existing store stays fail-closed."""
    _session_stream_store(tmp_path)  # create the database file, then corrupt it
    (tmp_path / "session-streams.sqlite3").write_bytes(b"not a sqlite database")
    store = SessionStreamStore(SessionStreamDatabase(tmp_path / "session-streams.sqlite3"))
    spawned = _refusing_cursor_dispatch_setup(monkeypatch, tmp_path, store)

    rc = delegate.cmd_dispatch(_dispatch_args("--agent", "cursor"))

    assert rc == 2
    assert spawned == []
    err = capsys.readouterr().err
    assert "CAPACITY REFUSED" in err
    assert "unable to verify the session-stream store" in err


@pytest.mark.parametrize("suppression", ("json", "quiet"))
def test_dispatch_cursor_lease_refusal_is_not_suppressed_by_json_or_quiet(monkeypatch, tmp_path, capsys, suppression):
    """Machine-output modes hide hints, not the hard Cursor self-dispatch refusal."""
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(delegate.urllib.request, "urlopen", _urlopen_routing(_FakeBudgetResponse()))
    monkeypatch.setattr(delegate, "_session_stream_store", lambda: _self_cursor_driver_store(tmp_path))
    spawned = _track_worker_spawns(monkeypatch)
    args = _dispatch_args("--agent", "cursor")
    setattr(args, suppression, True)

    rc = delegate.cmd_dispatch(args)

    assert rc == 2
    assert spawned == []
    err = capsys.readouterr().err
    assert "CAPACITY REFUSED" in err
    assert "💡" not in err


def test_dispatch_cursor_force_agent_overrides_live_driver_lease(monkeypatch, tmp_path, capsys):
    """--force-agent permits the explicit self-dispatch collision and records a NOTE."""
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(delegate.urllib.request, "urlopen", _urlopen_routing(_FakeBudgetResponse()))
    monkeypatch.setattr(delegate, "_session_stream_store", lambda: _self_cursor_driver_store(tmp_path))
    spawned = _track_worker_spawns(monkeypatch)

    rc = delegate.cmd_dispatch(_dispatch_args("--agent", "cursor", "--force-agent"))

    assert rc == 0
    assert len(spawned) == 1
    err = capsys.readouterr().err
    assert "NOTE: --force-agent overrides the live Cursor driver stream lease" in err


def test_dispatch_cursor_worker_only_in_flight_keeps_hint_and_spawns(monkeypatch, tmp_path, capsys):
    """A Cursor worker task is not the Cursor driver's session-stream lease."""
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(delegate.urllib.request, "urlopen", _urlopen_routing(_FakeBudgetResponse()))
    monkeypatch.setattr(delegate, "_session_stream_store", lambda: _session_stream_store(tmp_path))
    monkeypatch.setattr(delegate, "_pid_alive", lambda _pid: True)
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    (tasks_dir / "cursor-worker.json").write_text(
        json.dumps(
            {
                "task_id": "cursor-worker",
                "agent": "cursor",
                "status": "running",
                "pid": 99999,
            }
        ),
        encoding="utf-8",
    )
    spawned = _track_worker_spawns(monkeypatch)

    rc = delegate.cmd_dispatch(_dispatch_args("--agent", "cursor"))

    assert rc == 0
    assert len(spawned) == 1
    err = capsys.readouterr().err
    assert "💡 Note: lane 'cursor' has 1 task(s) in flight" in err


def test_dispatch_cursor_missing_session_stream_db_is_absence_not_refusal(monkeypatch, tmp_path, capsys):
    """A missing session-stream database file means no live lease, not refusal."""
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(delegate.urllib.request, "urlopen", _urlopen_routing(_FakeBudgetResponse()))
    monkeypatch.setattr(
        delegate,
        "_session_stream_store",
        lambda: SessionStreamStore(SessionStreamDatabase(tmp_path / "missing.sqlite3")),
    )
    spawned = _track_worker_spawns(monkeypatch)

    rc = delegate.cmd_dispatch(_dispatch_args("--agent", "cursor"))

    assert rc == 0
    assert len(spawned) == 1
    assert "CAPACITY REFUSED" not in capsys.readouterr().err


@pytest.mark.parametrize("lane,provider", [("deepseek", None), ("codex", "openrouter")])
@pytest.mark.parametrize(
    "change",
    [
        {"total_balance": 0, "limit_remaining_usd": 0},
        {"is_available": False},
        {"total_balance": 4.99, "limit_remaining_usd": 4.99},
        {"probe_state": "NEED_PROBE"},
        {"probe_state": "NEED_KEY"},
        {"freshness": "stale_last_good"},
        {"freshness": "unavailable"},
        {"age_s": 601},
    ],
)
def test_prepaid_guard_refuses_without_cost_ledger(monkeypatch, lane, provider, change):
    account = {
        "probe_state": "ok",
        "freshness": "fresh",
        "age_s": 1,
        "currency": "USD",
        "total_balance": 30,
        "limit_remaining_usd": 30,
        "is_available": True,
        **change,
    }
    prepaid = provider or lane
    monkeypatch.setattr(
        delegate,
        "_fetch_routing_budget",
        lambda: {
            "agents": {},
            "api_accounts": {prepaid: account},
            "diagnostics": {"records_loaded": 0, "stale": True},
        },
    )
    with pytest.raises(delegate.BudgetGuardRefuseError, match=f"NOTE: ROUTING REFUSED: prepaid {prepaid}"):
        delegate._resolve_agent_with_budget_guard(lane, provider=provider, fallbacks=_fallbacks())


@pytest.mark.parametrize("lane,provider", [("deepseek", None), ("codex", "openrouter")])
def test_fresh_funded_prepaid_does_not_require_cost_ledger(monkeypatch, lane, provider):
    account = {
        "probe_state": "ok",
        "freshness": "fresh",
        "age_s": 1,
        "currency": "USD",
        "total_balance": 30,
        "limit_remaining_usd": 30,
        "is_available": True,
    }
    monkeypatch.setattr(
        delegate,
        "_fetch_routing_budget",
        lambda: {
            "agents": {},
            "api_accounts": {provider or lane: account},
            "diagnostics": {"records_loaded": 0, "stale": True},
        },
    )
    assert delegate._resolve_agent_with_budget_guard(lane, provider=provider, fallbacks=_fallbacks()) == lane


@pytest.mark.parametrize("lane,provider", [("deepseek", None), ("codex", "openrouter")])
def test_prepaid_monitor_failure_refuses(monkeypatch, lane, provider):
    def unavailable():
        raise delegate.MonitorApiUnavailable("offline")

    monkeypatch.setattr(delegate, "_fetch_routing_budget", unavailable)
    with pytest.raises(delegate.BudgetGuardRefuseError, match="NEED_PROBE"):
        delegate._resolve_agent_with_budget_guard(lane, provider=provider, fallbacks=_fallbacks())


@pytest.mark.parametrize(
    "args,prepaid",
    [
        (("--agent", "deepseek"), "deepseek"),
        (("--provider", "openrouter"), "openrouter"),
    ],
)
def test_check_budget_empty_prepaid_refuses_before_spawn(monkeypatch, tmp_path, capsys, args, prepaid):
    _patch_spawn(monkeypatch, tmp_path)
    spawned = _track_worker_spawns(monkeypatch)
    monkeypatch.setattr(delegate.urllib.request, "urlopen", _urlopen_routing(_FakeBudgetResponse()))
    monkeypatch.setattr(
        delegate,
        "_fetch_routing_budget",
        lambda: {
            "agents": {},
            "diagnostics": {"records_loaded": 0},
            "api_accounts": {
                prepaid: {
                    "probe_state": "ok",
                    "freshness": "fresh",
                    "age_s": 0,
                    "currency": "USD",
                    "total_balance": 0,
                    "limit_remaining_usd": 0,
                }
            },
        },
    )
    result = delegate.cmd_dispatch(_dispatch_args("--check-budget", *args))
    assert result == 2
    assert not spawned
    message = capsys.readouterr().err
    assert f"ROUTING REFUSED: prepaid {prepaid} status=near_cap" in message
    print(f"check-budget fixture {prepaid}: exit={result}, worker_spawns={len(spawned)}")
    print(message.strip())


def _codex_cursor_budget(*, codex_status: str) -> dict:
    hot = codex_status == "hot"
    return {
        "recommendation": {
            "primary_agent_for_code": "cursor" if hot else "codex",
            "rationale": "fixture",
            "warnings": [],
        },
        "agents": {
            "codex": {"status": codex_status, "burn_pct_7d": 95.0 if hot else 10.0},
            "cursor": {"status": "cool", "burn_pct_7d": 5.0},
            "claude": {"status": "cool", "burn_pct_7d": 10.0},
        },
        "diagnostics": {"records_loaded": 5, "stale": False, "codexbar_data_available": True},
    }


def _capture_worker_commands(monkeypatch, tmp_path) -> list[list[str]]:
    commands: list[list[str]] = []

    def fake_popen(cmd, *_args, **_kwargs):
        commands.append([str(part) for part in cmd])
        return _FakeProc()

    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setenv("LU_DISPATCH_ISOLATION", "fallback")
    monkeypatch.setattr(delegate.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(delegate.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(delegate, "_fetch_routing_budget", lambda: _codex_cursor_budget(codex_status="hot"))
    return commands


def _codex_dispatch(*extra: str):
    return delegate.build_parser().parse_args(
        [
            "dispatch",
            "--agent",
            "codex",
            "--task-id",
            "probe-8855",
            "--prompt",
            "noop",
            "--mode",
            "read-only",
            "--cwd",
            str(delegate._REPO_ROOT),
            "--check-budget",
            *extra,
        ]
    )


def _worker_argv(commands: list[list[str]]) -> list[str]:
    worker = [command for command in commands if "_worker" in command]
    assert worker, commands
    return worker[-1]


def test_budget_sub_codex_gpt6_sol_spawns_cursor_default(monkeypatch, tmp_path, capsys):
    """AC-01: codex → cursor with gpt-6.1-sol uses the cursor dispatch pin, on the line and in the task JSON."""
    commands = _capture_worker_commands(monkeypatch, tmp_path)

    rc = delegate.cmd_dispatch(_codex_dispatch("--model", "gpt-6.1-sol"))

    assert rc == 0
    err = capsys.readouterr().err
    assert "HARD AUTO-SUBSTITUTE: --agent codex → cursor" in err
    assert "--model grok-4.7 (catalog default; gpt-6.1-sol has no mapping)" in err
    argv = _worker_argv(commands)
    assert "--agent" in argv and argv[argv.index("--agent") + 1] == "cursor"
    assert "--model" in argv and argv[argv.index("--model") + 1] == "grok-4.7"
    assert "gpt-6.1-sol" not in argv
    state = json.loads((tmp_path / "tasks" / "probe-8855.json").read_text(encoding="utf-8"))
    assert state["agent"] == "cursor"
    assert state["substitution"] == {
        "kind": "agent-substitution",
        "substituted": True,
        "source": "budget-guard",
        "requested_agent": "codex",
        "actual_agent": "cursor",
        "requested_model": "gpt-6.1-sol",
        "actual_model": "grok-4.7",
        "actual_model_known": True,
        "model_resolution": "catalog-default",
    }


def test_budget_sub_without_explicit_model_uses_catalog_default(monkeypatch, tmp_path, capsys):
    commands = _capture_worker_commands(monkeypatch, tmp_path)

    rc = delegate.cmd_dispatch(_codex_dispatch())

    assert rc == 0
    err = capsys.readouterr().err
    assert "--model grok-4.7 (catalog default)" in err
    assert "has no mapping" not in err
    argv = _worker_argv(commands)
    assert argv[argv.index("--model") + 1] == "grok-4.7"
    state = json.loads((tmp_path / "tasks" / "probe-8855.json").read_text(encoding="utf-8"))
    assert state["substitution"]["requested_model"] is None
    assert state["substitution"]["actual_model"] == "grok-4.7"
    assert state["substitution"]["model_resolution"] == "catalog-default"


def test_budget_sub_unmapped_model_falls_back_to_catalog_default(monkeypatch, tmp_path, capsys):
    commands = _capture_worker_commands(monkeypatch, tmp_path)

    rc = delegate.cmd_dispatch(_codex_dispatch("--model", "not-a-fleet-model"))

    assert rc == 0
    err = capsys.readouterr().err
    assert "--model grok-4.7 (catalog default; not-a-fleet-model has no mapping)" in err
    argv = _worker_argv(commands)
    assert argv[argv.index("--model") + 1] == "grok-4.7"
    state = json.loads((tmp_path / "tasks" / "probe-8855.json").read_text(encoding="utf-8"))
    assert state["substitution"]["requested_model"] == "not-a-fleet-model"
    assert state["substitution"]["actual_model"] == "grok-4.7"
    assert state["substitution"]["model_resolution"] == "catalog-default"


def test_budget_sub_maps_opus_to_cursor_invocation_slug(monkeypatch, tmp_path, capsys):
    commands = _capture_worker_commands(monkeypatch, tmp_path)

    rc = delegate.cmd_dispatch(_codex_dispatch("--model", "claude-opus-5-5"))

    assert rc == 0
    err = capsys.readouterr().err
    assert "--model claude-opus-5-5-high (mapped from claude-opus-5-5)" in err
    argv = _worker_argv(commands)
    assert argv[argv.index("--model") + 1] == "claude-opus-5-5-high"
    state = json.loads((tmp_path / "tasks" / "probe-8855.json").read_text(encoding="utf-8"))
    assert state["substitution"]["model_resolution"] == "mapped"
    assert state["substitution"]["actual_model"] == "claude-opus-5-5-high"


def test_budget_sub_refuses_unmapped_model_the_substitute_rejects(monkeypatch, tmp_path, capsys):
    """Hot claude → codex: an explicit model Codex rejects, with no mapping row, never spawns."""
    commands: list[list[str]] = []

    def fake_popen(cmd, *_args, **_kwargs):
        commands.append([str(part) for part in cmd])
        return _FakeProc()

    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setenv("LU_DISPATCH_ISOLATION", "fallback")
    monkeypatch.setattr(delegate.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(delegate.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        delegate,
        "_fetch_routing_budget",
        lambda: {
            "recommendation": {"primary_agent_for_code": "codex", "rationale": "fixture", "warnings": []},
            "agents": {
                "claude": {
                    "status": "hot",
                    "burn_pct_7d": 95.0,
                    "interactive": {"status": "hot", "burn_pct_7d": 95.0},
                },
                "codex": {"status": "cool", "burn_pct_7d": 10.0},
                "cursor": {"status": "cool", "burn_pct_7d": 5.0},
            },
            "diagnostics": {"records_loaded": 5, "stale": False, "codexbar_data_available": True},
        },
    )

    rc = delegate.cmd_dispatch(
        delegate.build_parser().parse_args(
            [
                "dispatch",
                "--agent",
                "claude",
                "--task-id",
                "probe-8855-reject",
                "--prompt",
                "noop",
                "--mode",
                "read-only",
                "--check-budget",
                "--model",
                "claude-fable-5-1",
            ]
        )
    )

    assert rc == 2
    err = capsys.readouterr().err
    assert "rejects explicit --model claude-fable-5-1" in err
    assert "CodexAdapter: model='claude-fable-5-1' rejected" in err
    assert "Refusing before spawn." in err
    assert "catalog default" not in err
    assert "HARD AUTO-SUBSTITUTE" not in err
    assert not any("_worker" in command for command in commands)
    assert not (tmp_path / "tasks" / "probe-8855-reject.json").exists()


def test_budget_sub_refuses_before_spawn_when_no_model_is_valid(monkeypatch, tmp_path, capsys):
    """AC-02: neither the mapped model nor the catalog default is valid → no task, no worker."""
    commands = _capture_worker_commands(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate, "_lane_default_model", lambda _agent: "not-a-fleet-model")

    rc = delegate.cmd_dispatch(_codex_dispatch("--model", "gpt-6.1-sol"))

    assert rc == 2
    err = capsys.readouterr().err
    assert "ROUTING REFUSED: no valid model for substitute --agent cursor" in err
    assert "Refusing before spawn." in err
    assert "HARD AUTO-SUBSTITUTE" not in err
    assert not any("_worker" in command for command in commands)
    assert not (tmp_path / "tasks" / "probe-8855.json").exists()


def test_dispatch_without_substitution_keeps_explicit_model(monkeypatch, tmp_path, capsys):
    """AC-03: a cool lane keeps the caller's --model and writes no substitution."""
    commands = _capture_worker_commands(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate, "_fetch_routing_budget", lambda: _codex_cursor_budget(codex_status="cool"))

    rc = delegate.cmd_dispatch(_codex_dispatch("--model", "gpt-6.1-sol"))

    assert rc == 0
    err = capsys.readouterr().err
    assert "HARD AUTO-SUBSTITUTE" not in err
    argv = _worker_argv(commands)
    assert argv[argv.index("--agent") + 1] == "codex"
    assert argv[argv.index("--model") + 1] == "gpt-6.1-sol"
    state = json.loads((tmp_path / "tasks" / "probe-8855.json").read_text(encoding="utf-8"))
    assert state["agent"] == "codex"
    assert state["substitution"] is None


def test_worker_keeps_budget_substitution_beside_runtime_attribution(monkeypatch, tmp_path):
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))
    task_id = "budget-sub-survives"
    state_path = delegate._state_path(task_id)
    delegate._write_state_atomic(
        state_path,
        {
            "task_id": task_id,
            "agent": "cursor",
            "model": "grok-4.7",
            "substitution": {
                "kind": "agent-substitution",
                "substituted": True,
                "source": "budget-guard",
                "requested_agent": "codex",
                "actual_agent": "cursor",
                "requested_model": "gpt-6.1-sol",
                "actual_model": "grok-4.7",
                "actual_model_known": True,
                "model_resolution": "catalog-default",
            },
        },
    )
    mock_result = type(
        "_Result",
        (),
        {
            "ok": True,
            "response": "done",
            "stderr_excerpt": None,
            "returncode": 0,
            "rate_limited": False,
            "model": "grok-4.7",
            "effort": "unknown",
            "cli_version": "test",
            "substitution": {
                "requested_model": "grok-4.7",
                "actual_model": "grok-4.7",
                "actual_model_known": True,
                "source": "cursor-stream-json",
                "substituted": False,
            },
        },
    )()
    with patch("agent_runtime.runner.invoke", return_value=mock_result):
        rc = delegate._run_worker(
            task_id=task_id,
            agent="cursor",
            prompt="hi",
            mode="read-only",
            cwd_str=str(tmp_path),
            model="grok-4.7",
            hard_timeout=60,
        )

    assert rc == 0
    state = delegate._read_state(state_path)
    assert state is not None
    assert state["substitution"]["kind"] == "agent-substitution"
    assert state["substitution"]["requested_model"] == "gpt-6.1-sol"
    assert state["substitution"]["actual_model"] == "grok-4.7"
    assert state["substitution"]["runtime_attribution"]["source"] == "cursor-stream-json"
    assert state["resolved_model"] == "grok-4.7"
    assert state["resolved_model_source"] == "cursor-stream-json"


# --- #9740 round 2: the budget guard acts on the owner's routing facts -----------------


def _fresh_lane(**overrides) -> dict:
    """A healthy lane record with a fresh probe, as the routing-budget producer publishes it."""
    record = {"health": {"healthy": True}, "freshness": "fresh", "age_s": 30.0, **overrides}
    record["codexbar"] = {"freshness": "fresh", "age_s": 30.0, **record.get("codexbar", {})}
    return record


def _owner_guard(monkeypatch, lane: str, record: dict, *, model: str | None = None, **budget) -> str:
    snapshot = {
        "recommendation": {"primary_agent_for_code": None, "warnings": []},
        "agents": {lane: record, "claude": _fresh_lane(status="cool", codexbar={"weekly_remaining_pct": 90.0})},
        "diagnostics": {"records_loaded": 0, "stale": False, "codexbar_data_available": True},
        **budget,
    }
    monkeypatch.setattr(delegate, "_fetch_routing_budget", lambda: snapshot)
    monkeypatch.setattr(delegate, "_load_reset_reserve", lambda *_a, **_k: {})
    return delegate._resolve_agent_with_budget_guard(lane, requested_model=model, fallbacks={lane: "claude"})


def test_near_cap_hard_acts_without_cost_ledger_records(monkeypatch, capsys):
    """F1/F6: a CodexBar near_cap lane is substituted even when the USD ledger is empty."""
    codex = _fresh_lane(
        status="near_cap",
        codexbar={"weekly_remaining_pct": 80.0, "primary_remaining_pct": 3.0, "will_last_to_reset": True},
    )
    assert _owner_guard(monkeypatch, "codex", codex, model="gpt-6.1-sol") == "claude"
    err = capsys.readouterr().err
    assert "HARD AUTO-SUBSTITUTE" in err and "near_cap (3% remaining on FRESH snapshot)" in err


def test_near_cap_on_a_stale_snapshot_stays_advisory(monkeypatch):
    """A2: the stale-snapshot advisory is unchanged."""
    codex = _fresh_lane(status="near_cap", codexbar={"primary_remaining_pct": 3.0})
    stale = {"diagnostics": {"records_loaded": 0, "stale": True, "codexbar_data_available": True}}
    assert _owner_guard(monkeypatch, "codex", codex, model="gpt-6.1-sol", **stale) == "codex"


@pytest.mark.parametrize(
    ("source", "expected"), [("weekly_pace", "cursor"), ("cursor_auto", "claude"), (None, "claude")]
)
def test_hidden_pace_clears_only_a_weekly_pace_hot_label(monkeypatch, source, expected):
    """F3/A3: hidden pace clears a hot label only when the owner says it came from weekly pace."""
    cursor = _fresh_lane(
        status="hot",
        status_source=source,
        codexbar={
            "weekly_used_pct": 30.0,
            "weekly_remaining_pct": 70.0,
            "weekly_expected_pct": 0.1,
            "weekly_pace_delta_pct": 20.0,
            "will_last_to_reset": False,
        },
    )
    assert _owner_guard(monkeypatch, "cursor", cursor) == expected


def test_demoted_message_prints_unknown_health_as_unknown(monkeypatch, capsys):
    from scripts.api.lane_health import BASIS_SCAN_UNAVAILABLE

    ranked = [
        {
            "lane": "kimi",
            "health": {
                "healthy": None,
                "consecutive_failures": None,
                "span_minutes": None,
                "basis": BASIS_SCAN_UNAVAILABLE,
            },
        },
        {"lane": "grok", "health": {"healthy": False, "consecutive_failures": 3, "span_minutes": 12}},
        {"lane": "agy", "health": {"healthy": True, "consecutive_failures": 0, "span_minutes": 0}},
    ]
    codex = _fresh_lane(status="cool", codexbar={"weekly_remaining_pct": 80.0, "will_last_to_reset": True})
    assert _owner_guard(monkeypatch, "codex", codex, model="gpt-6.1-sol", ranked_by_headroom=ranked) == "codex"
    err = capsys.readouterr().err
    assert f"⚠ lane kimi health unknown ({BASIS_SCAN_UNAVAILABLE}); not counted as healthy" in err
    assert "⚠ lane grok demoted: 3 spawn failures in 12m" in err
    assert "None spawn failures" not in err
    assert "lane agy" not in err
