"""Contracts for fleet routing and the Codex subagent default.

The fleet catalog's bounded workers are GPT-6 Luna at high. Codex's native
subagent default is Sol; explicit Luna profiles retain that scouting seat. Neither selection makes Luna a
formal reviewer. Large structural assertions stay in ``test_model_catalog.py``.
"""

from __future__ import annotations

from scripts.review.model_catalog import load_model_catalog


def test_catalog_routes_bounded_codex_workers_to_luna_high() -> None:
    route = load_model_catalog()["execution_routing"]["sol_advised_bounded"]

    preferred = route["preferred_worker"]
    assert preferred["model_id"] == "gpt-6-luna"
    assert preferred["effort"] == "high"

    # Operator decision 2026-09-30 (#9275): Luna is never dispatched directly;
    # every bounded worker needs the advisor's complete envelope.
    assert "direct_worker" not in route
    assert "bounded_fallback_worker" not in route
    assert preferred["requires"] == ["complete_advisory_envelope", "objective_scope_ceiling"]

    fallback = route["autonomous_fallback"]
    assert fallback["model_id"] == "gpt-6.1-sol"
    assert fallback["effort"] == "high"
    assert "missing_objective_scope_ceiling" in fallback["when"]


def test_luna_is_absent_from_formal_review_candidates_and_ladders() -> None:
    catalog = load_model_catalog()

    assert "gpt-5.6-luna" not in catalog["review_candidates"]
    assert "gpt-6-luna" not in catalog["review_candidates"]
    for ladder in catalog["review_ladders"].values():
        rung_candidates = {candidate for rung in ladder for candidate in rung}
        assert "gpt-5.6-luna" not in rung_candidates


def test_review_boundary_rejects_same_family_advisory_output() -> None:
    boundary = load_model_catalog()["execution_routing"]["sol_advised_bounded"]["review_boundary"]

    assert boundary["advisory_family"] == "openai"
    assert boundary["advisory_satisfies_cross_family_review"] is False
    assert boundary["independent_cross_family_review_required"] is True
