"""OO-58 / #11327: Fable 5.1 is parked; every Kimi catalog id is retired.

Defect class: a default, substitution, fallback, or review ladder selects
parked Fable 5.1 or a retired Kimi model, or budget routing counts native
Grok and Cursor as two usage pools. Explicit Fable pins remain available.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from scripts.review.model_catalog import load_model_catalog, retired_model_refusal

# The five ids this issue retires. claude-fable-5 was already retired.
RETIRED_IDS = (
    "kimi-code/k3",
    "kimi-code/k3-256k",
    "kimi-k3-max",
    "kimi-code/kimi-for-coding",
    "kimi-code/kimi-for-coding-highspeed",
)

# Aliases and the old Cursor slug must resolve to a retired id and be refused.

ROUTE_SECTIONS = (
    "execution_routing",
    "review_candidates",
    "review_scheduler",
    "orchestrator_seats",
    "formal_cf_defaults",
    "review_ladders",
    "budget_substitution_models",
)

_REPO = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("model_id", RETIRED_IDS)
def test_five_kimi_ids_are_retired_with_no_executable_transport(model_id: str) -> None:
    """A retired id keeps its historical record and has no transport."""
    model = load_model_catalog()["models"][model_id]
    assert model["lifecycle"] == "retired"
    assert model["transports"] == []
    assert "replaced_by" not in model


def test_predecessor_fable_successor_is_an_active_model() -> None:
    """claude-fable-5 cannot name a retired successor."""
    catalog = load_model_catalog()
    successor = catalog["models"]["claude-fable-5"]["replaced_by"]
    assert successor == "claude-fable-5-1"
    assert catalog["models"][successor]["lifecycle"] == "active"


def test_no_substitution_fallback_or_ladder_resolves_to_fable_or_kimi() -> None:
    """No executable section, fallback row, or ladder candidate names these ids."""
    catalog = load_model_catalog()
    for section in ROUTE_SECTIONS:
        blob = json.dumps(catalog[section])
        for model_id in RETIRED_IDS:
            assert model_id not in blob, section
        assert "claude-fable-5-1-thinking-high" not in blob, section
    fallbacks = yaml.safe_load((_REPO / "scripts/config/agent_fallback_substitutions.yaml").read_text(encoding="utf-8"))
    fallback_blob = json.dumps(fallbacks)
    for model_id in RETIRED_IDS:
        assert model_id not in fallback_blob
    assert fallbacks["dispatch_fallbacks"].get("kimi") is None
    candidates = catalog["review_candidates"]
    for risk, ladder in catalog["review_ladders"].items():
        for rung in ladder:
            for name in rung:
                model_id = candidates[name]["model_id"]
                assert model_id not in RETIRED_IDS, (risk, name, model_id)
                assert "fable" not in model_id and "kimi" not in model_id
    for endpoint in catalog["review_scheduler"]["endpoints"].values():
        for model_id in endpoint.get("models") or []:
            if isinstance(model_id, str):
                assert model_id not in RETIRED_IDS
                refusal = retired_model_refusal(model_id, catalog)
                assert refusal == (
                    None
                    if model_id != "gpt-6-astra"
                    else (
                        "model 'gpt-6-astra' is restricted to red-team code review of "
                        "gpt-6.1-sol-authored PRs through native_codex (#10437)"
                    )
                ), model_id
