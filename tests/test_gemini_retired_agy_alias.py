"""Permanent gemini→agy retirement alias tests (operator 2026-08-18).

The gemini CLI is not supported and will not be installed. `--agent gemini`
must resolve to the AGY adapter unconditionally, before Popen — not only
when the gemini budget lane happens to read hot/near_cap/deficit. Covers:
- ``agent_identity.RETIRED_AGENT_ALIASES`` / ``resolve_retired_agent_alias``
- ``capacity_pick`` never recommends gemini as a pick
- the substitution is documented in the dispatch_fallbacks yaml

The dispatch-level proof (worker command line never carries `--agent gemini`,
task state records the substitution) lives in
tests/test_delegate.py::test_dispatch_gemini_resolves_to_agy_before_popen_and_never_execs_gemini.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"


@pytest.fixture(autouse=True)
def _scripts_on_path():
    if str(_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS))


def test_resolve_retired_agent_alias_maps_gemini_to_agy():
    from agent_runtime.agent_identity import (
        RETIRED_AGENT_ALIASES,
        resolve_retired_agent_alias,
    )

    assert RETIRED_AGENT_ALIASES["gemini"] == "agy"
    assert resolve_retired_agent_alias("gemini") == "agy"
    assert resolve_retired_agent_alias("GEMINI") == "agy"
    assert resolve_retired_agent_alias("  gemini  ") == "agy"


def test_resolve_retired_agent_alias_passthrough_for_live_agents():
    from agent_runtime.agent_identity import resolve_retired_agent_alias

    assert resolve_retired_agent_alias("agy") is None
    assert resolve_retired_agent_alias("codex") is None
    assert resolve_retired_agent_alias("claude") is None
    assert resolve_retired_agent_alias(None) is None
    assert resolve_retired_agent_alias("") is None


def test_dispatch_fallbacks_yaml_documents_permanent_gemini_substitution():
    """The yaml row must exist for other consumers of dispatch_fallbacks,
    but the canonical mapping is agent_identity.RETIRED_AGENT_ALIASES."""
    from agent_runtime.agent_identity import RETIRED_AGENT_ALIASES

    path = _REPO_ROOT / "scripts" / "config" / "agent_fallback_substitutions.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["dispatch_fallbacks"]["gemini"] == RETIRED_AGENT_ALIASES["gemini"]


def test_capacity_pick_never_recommends_gemini_as_pick():
    from scripts.fleet import capacity_pick

    budget = {
        "generated_at": "2026-08-18T00:00:00Z",
        "agents": {
            # CodexBar reads gemini as ~99% remaining / cool — the exact
            # trap the operator flagged: a healthy quota reading is not
            # proof the CLI binary still exists.
            "gemini": {"status": "cool", "burn_pct_7d": 1.0, "remaining_pct": 99.0},
            "agy": {"status": "cool", "burn_pct_7d": 15.0, "remaining_pct": 85.0},
            "codex": {"status": "cool", "burn_pct_7d": 20.0, "remaining_pct": 80.0},
        },
        "in_flight": {},
        "recommendation": {
            "primary_agent_for_code": "gemini",
            "rationale": "stale upstream recommendation off a cool CodexBar reading",
            "warnings": [],
        },
        "diagnostics": {"records_loaded": 4, "stale": False},
    }

    report = capacity_pick.build_report(budget)
    rows = {r["lane"]: r for r in report["rows"]}

    assert rows["gemini"]["avoid"] is True
    assert "retired→agy" in rows["gemini"]["notes"]
    picks = report["pick_order"]
    assert next(p for p in picks if p["lane"] == "gemini")["pick"] == "AVOID"

    # Upstream still said gemini; capacity_pick must rewrite the recommendation.
    assert report["recommendation"]["primary_agent_for_code"] == "agy"
    assert any("retired CLI" in w for w in report["recommendation"]["warnings"])
