"""Admission regressions for frozen defaults and historical fleet guidance."""

from __future__ import annotations

import ast
import asyncio
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.audit import (
    code_review_benchmark,
    grok_judge_calibration,
    grok_stage_runner,
    judge_calibration_matrix,
    llm_reviewer_dispatch,
)
from scripts.audit.checks import content_quality
from scripts.batch import batch_gemini_config
from scripts.build import linear_pipeline
from scripts.etymology import bulk_ocr_gemini
from scripts.review.model_catalog import ModelCatalogError, load_model_catalog, require_execution_model
from scripts.tools import convert_plans_v4

ROOT = Path(__file__).resolve().parents[1]


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


def test_grok_standalone_defaults_refused_before_config_or_provider_access(monkeypatch, tmp_path):
    monkeypatch.setattr(grok_stage_runner.subprocess, "run", forbidden)
    monkeypatch.setattr(grok_stage_runner.shutil, "copy2", forbidden)
    monkeypatch.setattr(grok_judge_calibration, "load_hermes_oauth_token", forbidden)
    monkeypatch.setattr(grok_judge_calibration, "pull_calibration_cases", forbidden)
    with pytest.raises(ModelCatalogError, match="is retired"):
        grok_stage_runner.run_hermes("prompt", grok_stage_runner.GROK_MODEL)
    with pytest.raises(ModelCatalogError, match="is retired"):
        grok_judge_calibration.call_grok("prompt", "grok-4.5")
    monkeypatch.setattr("sys.argv", ["grok-stage", "--stage", "2", "--effort", "high", "--out-dir", str(tmp_path / "out")])
    with pytest.raises(ModelCatalogError, match="is retired"):
        grok_stage_runner.main()
    monkeypatch.setattr("sys.argv", ["grok-judge"])
    with pytest.raises(ModelCatalogError, match="is retired"):
        grok_judge_calibration.main()
    assert not (tmp_path / "out").exists()


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


def test_shell_defaults_and_retired_plan_enrichment():
    paths = [ROOT / "scripts" / rel for rel in (
        "enrich_a2_plans_gemini.sh", "run_otaman_serial_12_15.sh", "agent_runtime/_smoke_pty_agents.sh",
    )]
    for path in paths:
        subprocess.run(["bash", "-n", str(path)], check=True, timeout=30)
    result = subprocess.run(["bash", str(paths[0])], capture_output=True, text=True, cwd=ROOT, timeout=30)
    assert result.returncode == 2
    assert "Refused: legacy Gemini CLI" in result.stderr
    smoke = paths[2].read_text().split("<<'PYDRIVER'\n", 1)[1].split("\nPYDRIVER", 1)[0]
    tree = ast.parse(smoke)
    models = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign) and
                  any(isinstance(target, ast.Name) and target.id == "MODEL_BY_AGENT" for target in node.targets))
    require_execution_model(models["gemini"], transport="agy")
    require_execution_model(models["claude"], transport="native_claude")
    assert "--model gemini-3.8-flash-high" in paths[1].read_text()


def test_historical_content_review_rows_cannot_read_as_live_routes():
    text = (ROOT / "docs/best-practices/agent-activity-matrix.md").read_text()
    section = text.split("### 4.8 ", 1)[1].split("### 4.9 ", 1)[0]
    rows = [row for row in section.splitlines() if "DeepSeek" in row]
    assert len(rows) == 2
    for row in rows:
        assert row.startswith("| Historical result |")
        assert "DeepSeek is excluded from dispatch, implementation and review." in row


def test_scorecard_example_and_phase3_rebind_contract():
    text = (ROOT / "docs/best-practices/fleet-role-scorecard.md").read_text()
    model_row = next(line for line in text.splitlines() if line.startswith("| model |"))
    model = model_row.split("`")[1]
    require_execution_model(model, transport="native_codex")
    catalog = load_model_catalog()
    note = next(note for note in catalog["policy"]["notes"] if "#6870 item 3" in note)
    for model in ("gemini-3.6/3.7", "claude-fable-5", "grok-4.6"):
        assert model in note
