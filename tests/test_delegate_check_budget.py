"""Tests for delegate.py --check-budget pre-dispatch guard."""

from __future__ import annotations

import json
import sys
import types
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate


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
            *extra,
        ]
    )


def _patch_spawn(monkeypatch, tmp_path):
    monkeypatch.setattr(delegate, "_TASKS_DIR", tmp_path / "tasks")
    monkeypatch.setattr(delegate.subprocess, "Popen", lambda *_args, **_kwargs: _FakeProc())
    telemetry = type(
        "_Telemetry",
        (),
        {"model": "fixture-model", "effort": "high", "cli_version": "fixture"},
    )()
    monkeypatch.setattr(
        "agent_runtime.telemetry.resolve_dispatch_start_telemetry",
        lambda **_kwargs: telemetry,
    )


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


def test_check_budget_skipped_when_force_agent(monkeypatch, tmp_path, capsys):
    _patch_spawn(monkeypatch, tmp_path)

    def fail_on_budget_fetch(url, *_args, **_kwargs):
        if "/api/health" in str(url):
            return _FakeHealthResponse()
        raise AssertionError("routing-budget urlopen should not be called with --force-agent")

    monkeypatch.setattr(delegate.urllib.request, "urlopen", fail_on_budget_fetch)

    rc = delegate.cmd_dispatch(_dispatch_args("--check-budget", "--force-agent"))

    assert rc == 0
    assert "ROUTING WARNING" not in capsys.readouterr().err


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
    monkeypatch.setattr(delegate, "_TASKS_DIR", tmp_path / "tasks")
    monkeypatch.setattr(delegate.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        delegate.urllib.request,
        "urlopen",
        _urlopen_routing(_FakeBudgetResponse("codex")),
    )

    def fail_if_spawned(*_args, **_kwargs):
        raise AssertionError("dry-run must not spawn a worker")

    monkeypatch.setattr(delegate.subprocess, "Popen", fail_if_spawned)

    rc = delegate.cmd_dispatch(_dispatch_args("--check-budget", "--dry-run"))

    assert rc == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "budget-check-fixture"
    assert "ROUTING WARNING" in captured.err


def test_check_budget_hard_sub_on_near_cap_fresh(monkeypatch, tmp_path, capsys):
    """AC1: >90% (near_cap) on fresh → hard auto-sub, note substitution, uses fallback."""
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _s: None)
    # patch urlopen to return payload where passed claude is near_cap
    monkeypatch.setattr(
        delegate.urllib.request,
        "urlopen",
        _urlopen_routing(
            _FakeBudgetResponse(
                "codex", status_for_agent="claude", burn_for_agent=95.0, records_loaded=10, stale=False
            )
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
            _FakeBudgetResponse(
                "codex", status_for_agent="claude", burn_for_agent=95.0, records_loaded=3, stale=True
            )
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


def test_check_budget_reports_unknown_when_empty_ledger_codexbar_unavailable(monkeypatch, tmp_path, capsys):
    """A failed guard refresh must be explicit rather than using the old silent empty design."""
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _s: None)
    monkeypatch.setattr(
        delegate,
        "_fetch_routing_budget",
        lambda: {
            "recommendation": {"primary_agent_for_code": None, "warnings": []},
            "agents": {"claude": {"status": "unknown", "burn_pct_7d": None}},
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
    assert "budget UNKNOWN — could not verify CodexBar data; lanes may be in deficit" in err
    assert "per design" not in err
    assert "HARD AUTO-SUBSTITUTE" not in err


def test_check_budget_refuse_without_yaml_mapping(monkeypatch, tmp_path, capsys):
    """near_cap/hot without yaml mapping → refuse dispatch (exit non-zero)."""
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _s: None)
    monkeypatch.setattr(delegate, "_load_dispatch_fallbacks", lambda: {})
    monkeypatch.setattr(
        delegate.urllib.request,
        "urlopen",
        _urlopen_routing(
            _FakeBudgetResponse(
                "codex", status_for_agent="claude", burn_for_agent=95.0, records_loaded=10, stale=False
            )
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
    monkeypatch.setattr(delegate, "_load_dispatch_fallbacks", lambda: {"claude": "gemeni"})
    monkeypatch.setattr(
        delegate.urllib.request,
        "urlopen",
        _urlopen_routing(
            _FakeBudgetResponse(
                "codex", status_for_agent="claude", burn_for_agent=95.0, records_loaded=10, stale=False
            )
        ),
    )

    rc = delegate.cmd_dispatch(_dispatch_args("--check-budget"))

    assert rc == 2
    err = capsys.readouterr().err
    assert "not a known dispatch agent" in err
    assert "ROUTING REFUSED" in err
    assert "HARD AUTO-SUBSTITUTE" not in err


def test_check_budget_hard_sub_on_hot_status(monkeypatch, tmp_path, capsys):
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
    monkeypatch.setattr(delegate, "_load_dispatch_fallbacks", lambda: {"codex": "cursor"})

    rc = delegate.cmd_dispatch(
        delegate.build_parser().parse_args(
            [
                "dispatch",
                "--agent",
                "codex",
                "--task-id",
                "budget-check-hot",
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


def test_check_budget_hard_sub_on_deficit_will_last(monkeypatch, tmp_path, capsys):
    """will_last_to_reset=False (deficit) → hard auto-sub even if status is warm."""
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
                    "codexbar": {"will_last_to_reset": False, "pace_summary": "won't last"},
                },
                "cursor": {"status": "cool", "burn_pct_7d": 5.0},
            },
            "diagnostics": {"records_loaded": 3, "stale": False, "codexbar_data_available": True},
        },
    )
    monkeypatch.setattr(delegate, "_load_dispatch_fallbacks", lambda: {"codex": "cursor"})

    rc = delegate.cmd_dispatch(
        delegate.build_parser().parse_args(
            [
                "dispatch",
                "--agent",
                "codex",
                "--task-id",
                "budget-check-deficit",
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


def test_check_budget_refuse_hot_without_fallback_lists_cooler(monkeypatch, tmp_path, capsys):
    """hot lane with no yaml fallback → refuse and list cooler seats."""
    _patch_spawn(monkeypatch, tmp_path)
    monkeypatch.setattr(delegate.time, "sleep", lambda _s: None)
    monkeypatch.setattr(delegate, "_load_dispatch_fallbacks", lambda: {})
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


def test_check_budget_env_lu_dispatch_forces_guard(monkeypatch, tmp_path, capsys):
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
    monkeypatch.setattr(delegate, "_TASKS_DIR", tasks_dir)
    monkeypatch.setattr(delegate, "_pid_alive", lambda _pid: True)

    # Create a running task for codex
    state_file = tasks_dir / "busy-task.json"
    state_file.write_text(json.dumps({
        "task_id": "busy-task",
        "agent": "codex",
        "status": "running",
        "pid": 99999,
    }))

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
