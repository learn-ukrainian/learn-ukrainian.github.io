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
    compact_profile = resolve_profile("sol_lead", "gpt-6.1-sol")
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
        model_id="gpt-6.1-sol",
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
        model_id="gpt-6.1-sol",
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
        model_id="gpt-6.1-sol",
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
        model_id="gpt-6.1-sol",
        delegated_model_id="gpt-6.1-sol",
    )
    luna = cold_start.measure(
        "luna",
        profile_id="sol_lead",
        model_id="gpt-6.1-sol",
        delegated_model_id="gpt-6-luna",
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
    assert [(source.name, source.kind, source.provenance, source.bytes, source.tokens) for source in terra.sources] == [
        (source.name, source.kind, source.provenance, source.bytes, source.tokens) for source in luna.sources
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
        model_id="gpt-6.1-sol",
        transcript=transcript,
    )

    assert measurement.observed_first_turn_tokens == 40_000
    assert measurement.gate_input_tokens == 40_000
    assert measurement.within_budget is False
    assert measurement.transcript_observation is not None
    assert measurement.transcript_observation.method == ("transcript:first-assistant-input-cache-usage")


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
        model_id="gpt-6.1-sol",
    )

    assert measurement.complete is False
    assert measurement.within_budget is False
    assert (
        next(source for source in measurement.sources if source.name == "orientation").error
        == "TimeoutError: unavailable"
    )


def test_missing_route_fails_closed_even_when_payload_is_small(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cold_start, "_load_source", _successful_loader(1))

    measurement = cold_start.measure("unknown")

    assert measurement.selected_profile_id == "fallback"
    assert measurement.main_context_window_tokens == 0
    assert measurement.profile_trusted is False
    assert measurement.within_budget is False


# --- #10480: the first-turn observation uses the corrected context size ----------

TOP_LEVEL_SUM = 100 + 20_000 + 3_000


def _write_rows(path: Path, *usages: object) -> Path:
    rows = [{"type": "assistant", "message": {"usage": usage}} for usage in usages]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    return path


def _top_level(**extra: object) -> dict[str, object]:
    return {
        "input_tokens": 100,
        "cache_read_input_tokens": 20_000,
        "cache_creation_input_tokens": 3_000,
        "output_tokens": 777_777,
        **extra,
    }


def _message(input_tokens: int, cache_read: int, cache_creation: int, **extra: object) -> dict[str, object]:
    return {
        "type": "message",
        "input_tokens": input_tokens,
        "cache_read_input_tokens": cache_read,
        "cache_creation_input_tokens": cache_creation,
        "output_tokens": 55_555,
        **extra,
    }


def _advisor(tokens: int) -> dict[str, object]:
    return {"type": "advisor_message", "input_tokens": tokens, "output_tokens": 44_444}


def test_advisor_incident_reports_last_message_iteration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tests.test_context_latest_usage import incident_usage

    monkeypatch.setattr(cold_start, "_load_source", _successful_loader(100))
    transcript = _write_rows(tmp_path / "session.jsonl", incident_usage())

    observation = cold_start.observe_first_turn(transcript)
    measurement = cold_start.measure(
        "incident",
        profile_id="sol_lead",
        model_id="gpt-6.1-sol",
        transcript=transcript,
    )

    # Top level aggregates both executor passes (1,175,950); the real fill is the
    # last main pass, 2 + 586,399 + 3,148, with no output tokens.
    assert observation.tokens == 589_549
    assert observation.method == "transcript:first-assistant-input-cache-usage"
    assert measurement.observed_first_turn_tokens == 589_549
    assert measurement.estimated_input_tokens < 589_549
    assert measurement.gate_input_tokens == 589_549


@pytest.mark.parametrize(
    ("label", "usage", "expected"),
    [
        ("iterations-absent", _top_level(), TOP_LEVEL_SUM),
        ("iterations-empty", _top_level(iterations=[]), TOP_LEVEL_SUM),
        ("iterations-null", _top_level(iterations=None), TOP_LEVEL_SUM),
        ("iterations-string", _top_level(iterations="message"), TOP_LEVEL_SUM),
        ("iterations-object", _top_level(iterations={"type": "message", "input_tokens": 9}), TOP_LEVEL_SUM),
        (
            "advisor-only",
            _top_level(iterations=[_advisor(555_000), _advisor(666_000)]),
            TOP_LEVEL_SUM,
        ),
        (
            "main-advisor-main-unequal",
            _top_level(
                input_tokens=7,
                cache_read_input_tokens=900_000,
                cache_creation_input_tokens=100,
                iterations=[
                    _message(1, 400_000, 50),
                    _advisor(450_000),
                    _message(3, 420_000, 700),
                ],
            ),
            3 + 420_000 + 700,
        ),
        (
            "advisor-last",
            _top_level(
                input_tokens=7,
                cache_read_input_tokens=900_000,
                cache_creation_input_tokens=100,
                iterations=[_message(1, 400_000, 50), _advisor(450_000)],
            ),
            1 + 400_000 + 50,
        ),
        (
            "non-object-entries-ignored",
            _top_level(
                iterations=[
                    _message(1, 400, 50),
                    7,
                    "message",
                    None,
                    ["message"],
                    _message(2, 500, 60),
                    9,
                ],
            ),
            2 + 500 + 60,
        ),
    ],
)
def test_first_turn_shapes_equal_usage_input_tokens(
    tmp_path: Path,
    label: str,
    usage: dict[str, object],
    expected: int,
) -> None:
    from scripts.api.telemetry.transcript_tokens import usage_input_tokens

    transcript = _write_rows(tmp_path / f"{label}.jsonl", usage)

    observation = cold_start.observe_first_turn(transcript)

    assert usage_input_tokens(usage) == expected
    assert observation.tokens == expected
    assert observation.error is None


def test_message_iteration_without_input_fields_is_zero_and_skipped(
    tmp_path: Path,
) -> None:
    from scripts.api.telemetry.transcript_tokens import usage_input_tokens

    empty_message = _top_level(
        iterations=[
            {"type": "message", "input_tokens": None, "output_tokens": 5},
            {"type": "message", "cache_read_input_tokens": None},
        ]
    )
    assert usage_input_tokens(empty_message) == 0

    # Zero is not an observation: it is skipped like the unmodified scan skipped
    # it, not replaced by the (positive) top-level aggregate.
    only = cold_start.observe_first_turn(_write_rows(tmp_path / "only.jsonl", empty_message))
    assert only.tokens is None
    assert only.method == "unavailable"
    assert only.error == "no assistant usage record found"

    later = _top_level(input_tokens=1, cache_read_input_tokens=2, cache_creation_input_tokens=3)
    followed = cold_start.observe_first_turn(_write_rows(tmp_path / "later.jsonl", empty_message, later))
    assert followed.tokens == 6


def test_later_row_never_replaces_positive_first_row(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tests.test_context_latest_usage import incident_usage

    monkeypatch.setattr(cold_start, "_load_source", _successful_loader(100))
    larger_later = _top_level(cache_read_input_tokens=9_000_000)
    transcript = _write_rows(tmp_path / "session.jsonl", incident_usage(), larger_later)

    assert cold_start.observe_first_turn(transcript).tokens == 589_549
    measurement = cold_start.measure(
        "first-wins",
        profile_id="sol_lead",
        model_id="gpt-6.1-sol",
        transcript=transcript,
    )
    assert measurement.observed_first_turn_tokens == 589_549
    assert measurement.gate_input_tokens == 589_549


def test_later_row_is_corrected_when_first_row_total_is_zero(tmp_path: Path) -> None:
    from scripts.api.telemetry.transcript_tokens import usage_input_tokens

    empty_first = {"input_tokens": 0, "output_tokens": 10, "iterations": [_message(0, 0, 0)]}
    later = _top_level(
        input_tokens=7,
        cache_read_input_tokens=900_000,
        cache_creation_input_tokens=100,
        iterations=[_message(1, 400_000, 50), _advisor(450_000), _message(3, 420_000, 700)],
    )
    transcript = _write_rows(tmp_path / "session.jsonl", empty_first, later)

    observation = cold_start.observe_first_turn(transcript)

    assert usage_input_tokens(later) == 420_703
    assert observation.tokens == 420_703


def test_estimate_stays_the_gate_when_larger_than_corrected_observation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tests.test_context_latest_usage import incident_usage

    monkeypatch.setattr(cold_start, "_load_source", _successful_loader(3_000_000))
    transcript = _write_rows(tmp_path / "session.jsonl", incident_usage())

    measurement = cold_start.measure(
        "estimate-wins",
        profile_id="sol_lead",
        model_id="gpt-6.1-sol",
        transcript=transcript,
    )

    assert measurement.observed_first_turn_tokens == 589_549
    assert measurement.estimated_input_tokens > 589_549
    assert measurement.gate_input_tokens == measurement.estimated_input_tokens
