"""Contract for the Luna @ max bounded-worker routing policy.

Focused on the machine-readable invariants of the 2026-08-01 routing change:
Luna @ max is the default bounded worker, Terra @ high is the autonomous
fallback, and neither promotion weakens the independent cross-family review
gate. Large structural assertions stay in ``test_model_catalog.py`` and
``test_codex_hooks_contract.py``; this file guards only the routing contract.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from scripts.review.model_catalog import load_model_catalog

REPO_ROOT = Path(__file__).resolve().parents[1]
CODEX_PROJECT_CONFIG = REPO_ROOT / "agents_extensions" / "codex" / "config.toml"
SHARED_DOCTRINE = REPO_ROOT / "docs" / "best-practices" / "fleet-shared-doctrine.md"
ROLE_SCORECARD = REPO_ROOT / "docs" / "best-practices" / "fleet-role-scorecard.md"


def test_codex_source_config_defaults_subagents_to_luna_max() -> None:
    config = tomllib.loads(CODEX_PROJECT_CONFIG.read_text(encoding="utf-8"))

    agents = config["agents"]
    assert agents["default_subagent_model"] == "gpt-5.6-luna"
    assert agents["default_subagent_reasoning_effort"] == "max"


def test_catalog_routes_bounded_workers_to_luna_max_terra_high_fallback() -> None:
    route = load_model_catalog()["execution_routing"]["sol_advised_bounded"]

    preferred = route["preferred_worker"]
    assert preferred["model_id"] == "gpt-5.6-luna"
    assert preferred["effort"] == "max"

    direct = route["direct_worker"]
    assert direct["model_id"] == "gpt-5.6-luna"
    assert direct["effort"] == "max"
    assert "objective_scope_ceiling" in direct["constraints"]
    assert "no_final_disposition" in direct["constraints"]

    fallback = route["autonomous_fallback"]
    assert fallback["model_id"] == "gpt-5.6-terra"
    assert fallback["effort"] == "high"
    assert "missing_objective_scope_ceiling" in fallback["when"]


def test_luna_is_absent_from_formal_review_candidates_and_ladders() -> None:
    catalog = load_model_catalog()

    assert "gpt-5.6-luna" not in catalog["review_candidates"]
    for ladder in catalog["review_ladders"].values():
        rung_candidates = {candidate for rung in ladder for candidate in rung}
        assert "gpt-5.6-luna" not in rung_candidates


def test_kimi_k3_and_glm_5_2_remain_on_every_code_review_ladder() -> None:
    ladders = load_model_catalog()["review_ladders"]
    assert set(ladders) == {"critical", "high", "medium", "low"}

    for ladder in ladders.values():
        rung_candidates = {candidate for rung in ladder for candidate in rung}
        assert {"kimi-k3", "glm-5.2"} <= rung_candidates


def test_review_boundary_rejects_same_family_advisory_output() -> None:
    boundary = load_model_catalog()["execution_routing"]["sol_advised_bounded"]["review_boundary"]

    assert boundary["advisory_family"] == "openai"
    assert boundary["advisory_satisfies_cross_family_review"] is False
    assert boundary["independent_cross_family_review_required"] is True


def test_served_doctrine_uses_luna_max_without_overriding_other_recon_seats() -> None:
    doctrine = SHARED_DOCTRINE.read_text(encoding="utf-8")
    scorecard = ROLE_SCORECARD.read_text(encoding="utf-8")

    assert "| Luna bounded work / recon | **`max`**" in doctrine
    assert "| Claude Haiku recon | **`medium`** default" in doctrine
    assert "Luna `max` with exact owned paths + objective scope ceiling" in scorecard
