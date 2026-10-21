"""Admission regressions for frozen defaults and historical fleet guidance."""

from __future__ import annotations

import pytest

from scripts.audit import (
    code_review_benchmark,
    judge_calibration_matrix,
    llm_reviewer_dispatch,
)
from scripts.audit.checks import content_quality
from scripts.batch import batch_gemini_config
from scripts.build import linear_pipeline
from scripts.review.model_catalog import require_execution_model


def forbidden(*args, **kwargs):
    raise AssertionError("refused defaults must not reach provider or filesystem side effects")


def test_supported_pipeline_and_spot_audit_defaults_are_admitted():
    for defaults in (linear_pipeline.WRITER_DEFAULTS, linear_pipeline.REVIEWER_DEFAULTS):
        for lane, transport in (
            ("claude-tools", "native_claude"), ("codex-tools", "native_codex"),
            ("gemini-tools", "agy"), ("agy-tools", "agy"),
        ):
            require_execution_model(defaults[lane]["model"], transport=transport)
    for lane, transport in (("grok-tools", "native_grok"), ("cursor-tools", "cursor")):
        require_execution_model(linear_pipeline.WRITER_DEFAULTS[lane]["model"], transport=transport)
    require_execution_model(llm_reviewer_dispatch.CLAUDE_SPOT_AUDIT_MODEL_ID, transport="native_claude")
    for model in (batch_gemini_config.PRO_MODEL, batch_gemini_config.FLASH_MODEL, batch_gemini_config.FLASH_LITE_MODEL):
        require_execution_model(model, transport="agy")
    # Flash-Lite resolves to Flash: only two configured tiers, no extra capacity.
    assert batch_gemini_config.FLASH_LITE_MODEL == batch_gemini_config.FLASH_MODEL
    assert len({batch_gemini_config.PRO_MODEL, batch_gemini_config.FLASH_MODEL}) == 2


@pytest.mark.parametrize("module", [code_review_benchmark, judge_calibration_matrix])
def test_frozen_benchmark_smoke_defaults_refused_before_side_effects(module, monkeypatch):
    monkeypatch.setattr(module, "run_subprocess", forbidden)
    monkeypatch.setattr(module, "hermes_effort_swap", forbidden)
    for args in module.SMOKE_CELLS:
        cell = module.Cell(*args)
        with pytest.raises(ValueError):
            module.run_harness(cell, "prompt")


@pytest.mark.parametrize("module", [code_review_benchmark, judge_calibration_matrix])
def test_benchmark_native_active_successor_reaches_subprocess(module, monkeypatch):
    calls = []
    monkeypatch.setattr(module, "run_subprocess", lambda cmd, **kwargs: calls.append(cmd) or "result")
    cell = module.Cell("anthropic", "claude-opus-5-5", "native_cli", "high", "with_mcp")
    assert module.run_native_cli(cell, "prompt") == "result"
    assert calls[0][calls[0].index("--model") + 1] == "claude-opus-5-5"


def test_enabled_content_quality_records_model_refusal_and_preserves_deterministic_findings(monkeypatch):
    monkeypatch.setattr(content_quality, "CONTENT_QUALITY_ENABLED", True)
    deterministic_finding = {"type": "INVALID_CHARACTER", "severity": "error", "issue": "fixture"}
    monkeypatch.setattr(content_quality, "validate_characters_in_content", lambda *args: [deterministic_finding])
    # Refusal must precede credential access and must not escape into the audit.
    monkeypatch.setattr(content_quality.os, "getenv", forbidden)
    violations = content_quality.check_content_quality("Mechanical fixture. " * 40, "A1", 1)
    assert violations[0] == deterministic_finding
    assert violations[1]["type"] == "CONTENT_QUALITY"
    assert violations[1]["severity"] == "info"
    assert "LLM evaluation refused:" in violations[1]["issue"]
    assert "not in the model catalog" in violations[1]["issue"]
    assert "AGY" in violations[1]["fix"]
    assert len(violations) == 2
