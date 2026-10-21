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

from scripts import delegate
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
RETIRED_PINS = (
    *RETIRED_IDS,
    "k3",
    "k3-256k",
    "k3-max",
    "kimi-for-coding",
    "k2.7-highspeed",
)

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


def _clear_message(model: str) -> str:
    refusal = retired_model_refusal(model)
    assert refusal, model
    assert refusal.startswith(f"model {model!r} is retired in the model catalog")
    return refusal


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


@pytest.mark.parametrize("model", RETIRED_PINS)
def test_dispatch_refuses_each_retired_pin_before_later_work(capsys, monkeypatch, model: str) -> None:
    """Dispatch prints the catalog refusal and does not continue into host checks."""

    def _later_work_must_not_run(*_args, **_kwargs):
        raise AssertionError(f"retired pin {model!r} must be refused before later dispatch work")

    monkeypatch.setattr(delegate, "_early_host_refusal", _later_work_must_not_run)
    args = delegate.build_parser().parse_args(
        ["dispatch", "--agent", "cursor", "--model", model, "--task-id", "retired-11327", "--prompt", "review"]
    )
    assert delegate.cmd_dispatch(args) == 2
    assert delegate._read_state(delegate._state_path("retired-11327")) is None
    assert f"dispatch refused: {_clear_message(model)}" in capsys.readouterr().err


def test_dispatch_refuses_omitted_kimi_default_before_later_work(capsys, monkeypatch) -> None:
    """An omitted --model on kimi is the registry default, which is retired."""

    def _later_work_must_not_run(*_args, **_kwargs):
        raise AssertionError("omitted kimi model must be refused before later dispatch work")

    monkeypatch.setattr(delegate, "_early_host_refusal", _later_work_must_not_run)
    args = delegate.build_parser().parse_args(
        ["dispatch", "--agent", "kimi", "--task-id", "retired-kimi-default", "--prompt", "review"]
    )
    assert delegate.cmd_dispatch(args) == 2
    assert delegate._read_state(delegate._state_path("retired-kimi-default")) is None
    err = capsys.readouterr().err
    assert "dispatch refused: model 'k3-256k' is retired in the model catalog (kimi-code/k3-256k)" in err
    assert "use an active catalog model" in err


def test_dispatch_does_not_treat_omitted_grok_as_retired(capsys, monkeypatch) -> None:
    """The omitted-model check refuses only a retired seat default."""
    reached = {}

    def _stop_after_the_retirement_gate(*_args, **_kwargs):
        reached["yes"] = True
        return 2

    monkeypatch.setattr(delegate, "_early_host_refusal", _stop_after_the_retirement_gate)
    args = delegate.build_parser().parse_args(
        ["dispatch", "--agent", "grok", "--task-id", "grok-default-live", "--prompt", "review"]
    )
    assert delegate.cmd_dispatch(args) == 2
    assert reached == {"yes": True}
    assert "is retired" not in capsys.readouterr().err


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
                assert refusal is None, model_id


def test_budget_routing_reads_one_grok_cursor_usage_pool() -> None:
    """Native Grok and Cursor are one usage meter, read by the cooler-lane hint."""
    from scripts.review.model_catalog import usage_pool_for_seat

    catalog = load_model_catalog()
    assert catalog["usage_pools"]["grok_cursor"]["seats"] == ["grok", "cursor"]
    assert usage_pool_for_seat("grok", catalog) == usage_pool_for_seat("cursor", catalog) == "grok_cursor"
    assert usage_pool_for_seat("codex", catalog) == "codex"
    assert usage_pool_for_seat("kimi", catalog) == "kimi"

    paired = delegate._budget_cooler_lanes(
        {
            "grok": {"status": "near_cap"},
            "cursor": {"status": "cool"},
            "codex": {"status": "cool"},
            "claude": {"status": "hot"},
        },
        exclude="grok",
    )
    assert "cursor" not in paired
    assert "codex" in paired

    both_cool = delegate._budget_cooler_lanes(
        {"grok": {"status": "cool"}, "cursor": {"status": "cool"}, "codex": {"status": "near_cap"}},
        exclude="codex",
    )
    assert ("grok" in both_cool) != ("cursor" in both_cool)
    assert "codex" not in both_cool
