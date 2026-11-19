"""Admission regressions for frozen defaults and historical fleet guidance."""

from __future__ import annotations

import asyncio
import importlib.util
import linecache
import sys
import traceback
from types import SimpleNamespace

import pytest
from lu_machinery.agent_runtime.adapters import acpx
from lu_machinery.lib.readonly_sqlite import import_named_module
from lu_machinery.review import model_catalog
from lu_machinery.review.model_catalog import (
    ModelCatalogError,  # the refusing subjects run the installed release
    require_execution_model,
)

from scripts.audit import (
    code_review_benchmark,
    judge_calibration_matrix,
    llm_reviewer_dispatch,
)
from scripts.audit.checks import content_quality
from scripts.batch import batch_gemini_config
from scripts.build import linear_pipeline
from scripts.etymology import bulk_ocr_gemini
from scripts.tools import convert_plans_v4


def forbidden(*args, **kwargs):
    raise AssertionError("refused defaults must not reach provider or filesystem side effects")


def test_supported_pipeline_and_spot_audit_defaults_are_admitted():
    for defaults in (linear_pipeline.WRITER_DEFAULTS, linear_pipeline.REVIEWER_DEFAULTS):
        for lane, transport in (
            ("claude-tools", "native_claude"),
            ("codex-tools", "native_codex"),
            ("gemini-tools", "agy"),
            ("agy-tools", "agy"),
        ):
            require_execution_model(defaults[lane]["model"], transport=transport)
    # C-5307 restores grok-4.7 on its native and exact Cursor transports.
    for lane, transport in (("grok-tools", "native_grok"), ("cursor-tools", "cursor")):
        require_execution_model(linear_pipeline.WRITER_DEFAULTS[lane]["model"], transport=transport)
    require_execution_model(llm_reviewer_dispatch.CLAUDE_SPOT_AUDIT_MODEL_ID, transport="native_claude")
    for model in (batch_gemini_config.GEMINI_REVIEW_MODEL, batch_gemini_config.GEMINI_ROUTINE_MODEL):
        require_execution_model(model, transport="agy")
    # Tier names are aliases of the review seat: their callers dispatch over the AGY ACP bridge.
    tiers = {batch_gemini_config.PRO_MODEL, batch_gemini_config.FLASH_MODEL, batch_gemini_config.FLASH_LITE_MODEL}
    assert tiers == {batch_gemini_config.GEMINI_REVIEW_MODEL}


@pytest.mark.parametrize("module", [code_review_benchmark, judge_calibration_matrix])
def test_frozen_benchmark_smoke_defaults_refused_before_side_effects(module, monkeypatch):
    monkeypatch.setattr(module, "run_subprocess", forbidden)
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


def test_standalone_gemini_defaults_refused_before_corpus_or_credentials(monkeypatch):
    monkeypatch.setattr(convert_plans_v4.subprocess, "Popen", forbidden)
    monkeypatch.setattr(convert_plans_v4, "load_templates", forbidden)
    monkeypatch.setattr(bulk_ocr_gemini, "discover_volumes", forbidden)
    monkeypatch.setattr(content_quality.os, "getenv", forbidden)
    with pytest.raises(ModelCatalogError, match="not in the model catalog"):
        convert_plans_v4.call_gemini("prompt")
    monkeypatch.setattr("sys.argv", ["convert-plans", "hist", "--all"])
    with pytest.raises(ModelCatalogError, match="not in the model catalog"):
        convert_plans_v4.main()
    with pytest.raises(ModelCatalogError, match="not in the model catalog"):
        asyncio.run(bulk_ocr_gemini.run(SimpleNamespace(dry_run=False, model=bulk_ocr_gemini.DEFAULT_MODEL)))
    with pytest.raises(ModelCatalogError, match="not in the model catalog"):
        content_quality.call_gemini_api("content", {})


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


# Every module that binds a Gemini seat, and pedagogy_config, which must bind none.
_GEMINI_SEAT_CALLERS = (
    "scripts.batch.batch_gemini_config",
    "batch_gemini_config",
    "scripts.pipeline.prompt_preflight",
    "scripts.build.linear_pipeline",
    "scripts.batch.batch_otaman",
    "scripts.batch.batch_fix_review",
    "scripts.audit.naturalness_check",
    "scripts.audit.russianism_eval",
    "scripts.audit.layerb_judge_bridge",
    "scripts.project_api.hramatka_generator",
    "scripts.tools.upgrade_activity_hints",
    "scripts.review.integration_check",
)
_SEAT_CONFIG_MODULES = (
    "batch_gemini_config",
    "batch.batch_gemini_config",
    "scripts.batch_gemini_config",
    "scripts.batch.batch_gemini_config",
)


def _catalog_without_routine_seat():
    catalog = dict(model_catalog.load_model_catalog())
    catalog["orchestrator_seats"] = {k: v for k, v in catalog["orchestrator_seats"].items() if k != "agy"}
    return catalog


@pytest.mark.parametrize("role", ["review", "routine"])
@pytest.mark.parametrize("module", [*_GEMINI_SEAT_CALLERS, "scripts.curriculum.pedagogy_config"])
def test_missing_catalog_gemini_seat_fails_every_caller_at_import(module, role, monkeypatch):
    """Defect class: a caller binds a Gemini seat lazily, to a placeholder name or to a literal,
    so a catalog that lacks the seat imports cleanly and fails later or dispatches a refused name.

    The caller's own failing statement must be its seat binding, so a transitive import that
    happens to load the resolver first cannot hide a caller that went back to a literal.
    """
    origin = importlib.util.find_spec(module).origin
    if role == "review":
        participants = {k: v for k, v in acpx.ACPX_SUPPORTED_PARTICIPANTS.items() if k != "agy"}
        monkeypatch.setattr(acpx, "ACPX_SUPPORTED_PARTICIPANTS", participants)
    else:
        missing = _catalog_without_routine_seat()
        monkeypatch.setattr(model_catalog, "load_model_catalog", lambda *args, **kwargs: missing)
    for name in (*_SEAT_CONFIG_MODULES, module):
        monkeypatch.delitem(sys.modules, name, raising=False)

    if module not in _GEMINI_SEAT_CALLERS:
        import_named_module(module)  # binds no seat, so a missing seat cannot break it
        return
    with pytest.raises(RuntimeError) as raised:
        import_named_module(module)
    assert type(raised.value).__name__ == "GeminiSeatUnavailable"
    assert raised.value.role == role
    assert repr(role) in str(raised.value)
    own_frames = [frame for frame in traceback.extract_tb(raised.tb) if frame.filename == origin]
    assert own_frames, f"{module} did not reach a seat binding of its own"
    failing_line = linecache.getline(origin, own_frames[0].lineno)  # the module-level statement
    assert "batch_gemini_config import" in failing_line or "_gemini_seat(" in failing_line, failing_line
