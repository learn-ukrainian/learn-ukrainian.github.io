from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ai_agent_bridge import measure_cold_start as cold_start
from scripts.lib.context_profiles import resolve_profile


def _successful_loader(size: int):
    def load(spec: cold_start.SourceSpec):
        return b"x" * size, 200, 1.0, None

    return load


def test_profile_selects_compact_or_full_source_contract() -> None:
    compact_profile = resolve_profile("sol_lead", "gpt-5.6-sol")
    full_profile = resolve_profile("native_claude", "claude-sonnet-5")

    compact = cold_start.build_source_specs(
        compact_profile,
        session_id="session-one",
        agent="claude-infra",
    )
    full = cold_start.build_source_specs(
        full_profile,
        session_id="session-one",
        agent="claude-infra",
    )

    assert {source.name for source in compact} == cold_start.REQUIRED_STARTUP_SOURCE_NAMES
    assert {source.name for source in full} == cold_start.REQUIRED_STARTUP_SOURCE_NAMES
    compact_orient = next(source for source in compact if source.name == "orientation")
    full_orient = next(source for source in full if source.name == "orientation")
    assert "lean=true" in compact_orient.locator
    assert compact_orient.provenance == "monitor-api:lean-orient"
    assert "lean=true" not in full_orient.locator
    assert full_orient.provenance == "monitor-api:full-orient"
    assert all("/api/rules" not in source.locator for source in compact)
    assert all("/api/session/current" not in source.locator for source in compact)


def test_conservative_counter_is_explicit_and_rounds_up() -> None:
    tokens, method = cold_start.count_payload_tokens(
        b"1234",
        model_id="gpt-5.6-sol",
        token_count_url=None,
    )

    assert tokens == 34
    assert method == "conservative-bytes/3+32:endpoint-unavailable"


def test_gateway_token_counter_wins_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cold_start, "_gateway_token_count", lambda *args, **kwargs: 17)

    token_count_url = "{scheme}{separator}{authority}{path}?{query}".format(
        scheme="https",
        separator="://",
        authority="".join(("user", ":", "private", "@", "tokenizer.invalid")),
        path="/count",
        query="".join(("token", "=", "private")),
    )
    tokens, method = cold_start.count_payload_tokens(
        "українська".encode(),
        model_id="gpt-5.6-sol",
        token_count_url=token_count_url,
    )

    assert tokens == 17
    assert method == "gateway-token-count"
    assert "tokenizer.invalid" not in method


def test_compact_and_full_budgets_are_enforced(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cold_start, "_load_source", _successful_loader(20_000))

    compact = cold_start.measure(
        "compact",
        profile_id="sol_lead",
        model_id="gpt-5.6-sol",
    )
    full = cold_start.measure(
        "full",
        profile_id="native_claude",
        model_id="claude-sonnet-5",
    )

    assert compact.estimated_input_tokens > compact.cold_start_budget_tokens
    assert compact.within_budget is False
    assert full.estimated_input_tokens < full.cold_start_budget_tokens
    assert full.within_budget is True
    assert compact.main_context_window_tokens == 272_000
    assert full.main_context_window_tokens == 1_000_000


def test_delegated_model_cannot_change_lead_startup_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cold_start, "_load_source", _successful_loader(1_000))

    terra = cold_start.measure(
        "terra",
        profile_id="sol_lead",
        model_id="gpt-5.6-sol",
        delegated_model_id="gpt-5.6-terra",
    )
    luna = cold_start.measure(
        "luna",
        profile_id="sol_lead",
        model_id="gpt-5.6-sol",
        delegated_model_id="gpt-5.6-luna",
    )

    assert terra.delegated_model_id != luna.delegated_model_id
    assert (
        terra.main_model_id,
        terra.main_context_window_tokens,
        terra.cold_start_profile,
        terra.cold_start_budget_tokens,
        terra.rollover_warning_percentages,
        terra.estimated_input_tokens,
    ) == (
        luna.main_model_id,
        luna.main_context_window_tokens,
        luna.cold_start_profile,
        luna.cold_start_budget_tokens,
        luna.rollover_warning_percentages,
        luna.estimated_input_tokens,
    )
    assert [
        (source.name, source.kind, source.provenance, source.bytes, source.tokens)
        for source in terra.sources
    ] == [
        (source.name, source.kind, source.provenance, source.bytes, source.tokens)
        for source in luna.sources
    ]


def test_observed_first_turn_is_gate_when_larger_and_excludes_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cold_start, "_load_source", _successful_loader(100))
    transcript = tmp_path / "session.jsonl"
    transcript.write_text(
        json.dumps(
            {
                "type": "assistant",
                "message": {
                    "usage": {
                        "input_tokens": 30_000,
                        "cache_read_input_tokens": 8_000,
                        "cache_creation_input_tokens": 2_000,
                        "output_tokens": 999_999,
                    }
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    measurement = cold_start.measure(
        "observed",
        profile_id="sol_lead",
        model_id="gpt-5.6-sol",
        transcript=transcript,
    )

    assert measurement.observed_first_turn_tokens == 40_000
    assert measurement.gate_input_tokens == 40_000
    assert measurement.within_budget is False
    assert measurement.transcript_observation is not None
    assert measurement.transcript_observation.method == (
        "transcript:first-assistant-input-cache-usage"
    )


def test_failed_source_makes_measurement_incomplete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def load(spec: cold_start.SourceSpec):
        if spec.name == "orientation":
            return b"", None, 1.0, "TimeoutError: unavailable"
        return b"x", 200, 1.0, None

    monkeypatch.setattr(cold_start, "_load_source", load)

    measurement = cold_start.measure(
        "incomplete",
        profile_id="sol_lead",
        model_id="gpt-5.6-sol",
    )

    assert measurement.complete is False
    assert measurement.within_budget is False
    assert next(
        source for source in measurement.sources if source.name == "orientation"
    ).error == "TimeoutError: unavailable"


def test_missing_route_fails_closed_even_when_payload_is_small(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cold_start, "_load_source", _successful_loader(1))

    measurement = cold_start.measure("unknown")

    assert measurement.selected_profile_id == "fallback"
    assert measurement.main_context_window_tokens == 0
    assert measurement.profile_trusted is False
    assert measurement.within_budget is False
