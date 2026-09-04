"""Permanent glm→cursor retirement alias tests (operator 2026-09-03).

The z.ai GLM subscription backing the ``glm`` lane is retired (key gone).
glm-5.3 work routes to Cursor or OpenRouter instead — do not dispatch
``--agent glm`` unless the operator explicitly asks. `--agent glm` must
resolve to the Cursor adapter unconditionally, before Popen — the same
unconditional pattern as ``gemini``→``agy`` (see
test_gemini_retired_agy_alias.py). Covers:
- ``agent_identity.RETIRED_AGENT_ALIASES`` / ``resolve_retired_agent_alias``
- ``capacity_pick`` never recommends glm as a pick, and drops it from the
  default pick-order (it used to rank #2)
- the substitution is documented in the dispatch_fallbacks yaml
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


def test_resolve_retired_agent_alias_maps_glm_to_cursor():
    from agent_runtime.agent_identity import (
        RETIRED_AGENT_ALIASES,
        resolve_retired_agent_alias,
    )

    assert RETIRED_AGENT_ALIASES["glm"] == "cursor"
    assert resolve_retired_agent_alias("glm") == "cursor"
    assert resolve_retired_agent_alias("GLM") == "cursor"
    assert resolve_retired_agent_alias("  glm  ") == "cursor"


def test_dispatch_fallbacks_yaml_documents_permanent_glm_substitution():
    """The yaml row must exist for other consumers of dispatch_fallbacks,
    but the canonical mapping is agent_identity.RETIRED_AGENT_ALIASES."""
    from agent_runtime.agent_identity import RETIRED_AGENT_ALIASES

    path = _REPO_ROOT / "scripts" / "config" / "agent_fallback_substitutions.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["dispatch_fallbacks"]["glm"] == RETIRED_AGENT_ALIASES["glm"]


def test_capacity_pick_never_recommends_glm_as_pick():
    from scripts.fleet import capacity_pick

    budget = {
        "generated_at": "2026-09-03T00:00:00Z",
        "agents": {
            # A budget snapshot can still read glm as cool/wrong (the exact
            # trap this fix targets) — capacity_pick must AVOID it anyway.
            "glm": {"status": "cool", "burn_pct_7d": 1.0, "remaining_pct": 99.0},
            "cursor": {"status": "cool", "burn_pct_7d": 15.0, "remaining_pct": 85.0},
            "codex": {"status": "cool", "burn_pct_7d": 20.0, "remaining_pct": 80.0},
        },
        "in_flight": {},
        "recommendation": {
            "primary_agent_for_code": "glm",
            "rationale": "stale upstream recommendation off a cool-looking glm reading",
            "warnings": [],
        },
        "diagnostics": {"records_loaded": 4, "stale": False},
    }

    report = capacity_pick.build_report(budget)
    rows = {r["lane"]: r for r in report["rows"]}

    assert rows["glm"]["avoid"] is True
    assert "retired→cursor" in rows["glm"]["notes"]
    picks = report["pick_order"]
    assert next(p for p in picks if p["lane"] == "glm")["pick"] == "AVOID"

    # Upstream still said glm; capacity_pick must rewrite the recommendation.
    assert report["recommendation"]["primary_agent_for_code"] == "cursor"
    assert any("retired CLI" in w for w in report["recommendation"]["warnings"])


def test_glm_dropped_from_default_pick_order_priority():
    """glm's priority used to be #1 (pick-order #2, right after cursor).
    It must no longer sort as a live pick candidate."""
    from scripts.fleet.capacity_pick import _CODE_LANE_PRIORITY

    live_lane_ranks = {
        lane: rank
        for lane, rank in _CODE_LANE_PRIORITY.items()
        if lane not in {"gemini", "glm"}
    }
    assert _CODE_LANE_PRIORITY["glm"] > min(live_lane_ranks.values())
    assert _CODE_LANE_PRIORITY["glm"] != 1
