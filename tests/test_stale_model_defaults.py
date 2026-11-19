"""Admission regressions for frozen defaults and historical fleet guidance."""

from __future__ import annotations

import ast
import asyncio
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
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
_SEAT_FREE_MODULES = ("scripts.curriculum.pedagogy_config",)
_SEAT_CONFIG_MODULES = (
    "batch_gemini_config",
    "batch.batch_gemini_config",
    "scripts.batch_gemini_config",
    "scripts.batch.batch_gemini_config",
)
_SENTINEL_SEATS = {"review": "sentinel-review-seat", "routine": "sentinel-routine-seat"}


_REPO_ROOT = Path(__file__).resolve().parents[1]
# Runs one case in a fresh interpreter, so modules imported under patched seats never reach another
# test: no registry surgery, nothing to restore. It prints one JSON object on its last line.
_CASE_DRIVER = r"""
import copy, json, sys, traceback
root, module, case, paths = sys.argv[1], sys.argv[2], sys.argv[3], json.loads(sys.argv[4])
sys.path[:0] = [root, root + "/scripts"]
import yaml
from lu_machinery.agent_runtime.adapters import acpx
from lu_machinery.lib.readonly_sqlite import import_named_module
from lu_machinery.review import model_catalog

sentinels = {"review": "sentinel-review-seat", "routine": "sentinel-routine-seat"}
raw = yaml.safe_load(model_catalog.CATALOG_PATH.read_text(encoding="utf-8"))
if case == "review":
    acpx.ACPX_SUPPORTED_PARTICIPANTS = {k: v for k, v in acpx.ACPX_SUPPORTED_PARTICIPANTS.items() if k != "agy"}
elif case == "routine":  # a valid catalog without an AGY orchestrator seat
    del raw["orchestrator_seats"]["agy"]
    valid = model_catalog.validate_catalog(raw)
    model_catalog.load_model_catalog = lambda *args, **kwargs: valid
elif case == "invalid_catalog":  # the real validator rejects it, so no role has a seat
    raw["orchestrator_seats"]["agy"]["model_id"] = "no-such-model"
    model_catalog.load_model_catalog = lambda *args, **kwargs: model_catalog.validate_catalog(copy.deepcopy(raw))
else:  # wiring: sentinel seats, set after validation
    swapped = model_catalog.validate_catalog(raw)
    routine_id = swapped["orchestrator_seats"]["agy"]["model_id"]
    swapped["models"][routine_id]["routing_wire_ids"]["agy"] = sentinels["routine"]
    agy = {**acpx.ACPX_SUPPORTED_PARTICIPANTS["agy"], "model": sentinels["review"]}
    acpx.ACPX_SUPPORTED_PARTICIPANTS = {**acpx.ACPX_SUPPORTED_PARTICIPANTS, "agy": agy}
    model_catalog.load_model_catalog = lambda *args, **kwargs: swapped
    model_catalog.require_execution_model = lambda model, **kwargs: model


def effective(imported, path):
    if path.startswith("in "):
        return getattr(imported, path[3:]).split(",")
    if path.endswith(")"):
        import inspect
        target, param = path[:-1].split("(")
        obj = imported
        for part in target.split("."):
            obj = getattr(obj, part)
        return inspect.signature(obj).parameters[param].default
    head, *keys = path.split(".")
    value = getattr(imported, head)
    for key in keys:
        value = value[int(key)] if isinstance(value, tuple) else value[key]
    return value


try:
    imported = import_named_module(module)
except Exception as exc:
    frames = [[f.filename, f.lineno, f.line] for f in traceback.extract_tb(exc.__traceback__)]
    result = {"error": type(exc).__name__, "roles": list(getattr(exc, "roles", ()) or ()), "message": str(exc), "frames": frames}
else:
    result = {"error": None, "values": {path: effective(imported, path) for path in paths}}
print(json.dumps(result))
"""


def _run_case(module, case, paths):
    done = subprocess.run(
        [sys.executable, "-c", _CASE_DRIVER, str(_REPO_ROOT), module, case, json.dumps(paths)],
        cwd=_REPO_ROOT, capture_output=True, text=True, timeout=300, check=False,
    )
    assert done.returncode == 0, f"{module} {case} driver failed: {done.stderr[-2000:]}"
    return json.loads(done.stdout.strip().splitlines()[-1])


_RESOLVER_SEATS = {
    "GEMINI_REVIEW_MODEL": "review",
    "GEMINI_ROUTINE_MODEL": "routine",
    "PRO_MODEL": "review",
    "FLASH_MODEL": "review",
    "FLASH_LITE_MODEL": "review",
}
# Every effective model default each caller binds, and the role it must carry. A path is a global,
# then dict keys or tuple indexes; ``name(param)`` is a function's default (``Class.method(param)``
# for a method). ``in`` marks a comma-joined model list that must contain the seat.
_EFFECTIVE_DEFAULTS = {
    "scripts.batch.batch_gemini_config": _RESOLVER_SEATS,
    "batch_gemini_config": _RESOLVER_SEATS,
    "scripts.pipeline.prompt_preflight": {"GEMINI_REVIEW_MODEL": "review"},
    "scripts.build.linear_pipeline": {
        "WRITER_DEFAULTS.gemini-tools.model": "routine",
        "WRITER_DEFAULTS.agy-tools.model": "routine",
        "REVIEWER_DEFAULTS.gemini-tools.model": "review",
        "REVIEWER_DEFAULTS.agy-tools.model": "review",
    },
    "scripts.batch.batch_otaman": {"dispatch_otaman(model)": "review", "BatchOtaman.__init__(model)": "review"},
    "scripts.batch.batch_fix_review": {},
    "scripts.audit.naturalness_check": {"call_agy(model)": "review", "check_naturalness(model)": "review"},
    "scripts.audit.russianism_eval": {"in DEFAULT_MODELS": "review"},
    "scripts.audit.layerb_judge_bridge": {"DEFAULT_MODELS.gemini": "review"},
    "scripts.project_api.hramatka_generator": {
        "PRIMARY_MODEL": "routine",
        "SECONDARY_MODEL": "review",
        "generate_qualified_lesson(primary_model)": "routine",
        "generate_qualified_lesson(secondary_model)": "review",
    },
    "scripts.tools.upgrade_activity_hints": {"call_agy(model)": "review", "upgrade_plan(model)": "review"},
    "scripts.review.integration_check": {"SECOND_SEAT_MODEL.1": "review"},
}
# CLI ``--model`` defaults are checked in the source: each must name this resolver constant.
_PARSER_MODEL_DEFAULT = "GEMINI_REVIEW_MODEL"


def _gemini_identifiers(catalog):
    """Every exact string that names a Gemini catalog model: ids, aliases and wire ids."""
    google = {model_id for model_id, entry in catalog["models"].items() if entry.get("family") == "google"}
    names = set(google)
    names |= {alias for alias, model_id in model_catalog.model_aliases(catalog).items() if model_id in google}
    for model_id in google:
        names |= set((catalog["models"][model_id].get("routing_wire_ids") or {}).values())
    return names


def _source_literals_and_parser_defaults(path):
    """String literals in the source (including ``__main__`` code) and each ``--model`` default node."""
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    literals = [node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)]
    defaults = [
        keyword.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument"
        and node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == "--model"
        for keyword in node.keywords
        if keyword.arg == "default"
    ]
    return literals, defaults


# An invalid catalog breaks machinery's own catalog readers at import too, so that case runs on the
# resolver modules, where the attribution under test happens.
_CASES = [
    (module, case)
    for module in (*_GEMINI_SEAT_CALLERS, *_SEAT_FREE_MODULES)
    for case in ("review", "routine", "invalid_catalog", "wiring")
    if case != "invalid_catalog" or module in _SEAT_CONFIG_MODULES
]


@pytest.mark.parametrize(("module", "case"), _CASES)
def test_every_gemini_caller_binds_the_catalog_seat_at_import(module, case):
    """Defect class: a caller binds a Gemini seat lazily, to a placeholder name or to a literal, so a
    catalog that lacks the seat imports cleanly and fails later or dispatches a refused name.

    Each case imports the caller in a fresh interpreter. Missing-seat cases: the import raises
    GeminiSeatUnavailable naming the roles, and the caller's own failing statement is its seat
    binding, so a transitive import cannot hide a caller that went back to a literal. The wiring case
    swaps in sentinel seats: every effective model default must carry its role's seat, every CLI
    --model default must name the review constant, and no string literal in the caller's source may
    name a Gemini catalog model.
    """
    origin = importlib.util.find_spec(module).origin
    paths = _EFFECTIVE_DEFAULTS.get(module, {})
    result = _run_case(module, case, sorted(paths))

    if case == "wiring":
        assert result["error"] is None, result
        literals, parser_defaults = _source_literals_and_parser_defaults(origin)
        named = sorted(set(literals) & _gemini_identifiers(model_catalog.load_model_catalog()))
        assert named == [], f"{module} names Gemini models in its source: {named}"
        assert all(isinstance(node, ast.Name) and node.id == _PARSER_MODEL_DEFAULT for node in parser_defaults), (
            f"{module} has a --model default that is not {_PARSER_MODEL_DEFAULT}"
        )
        for path, role in paths.items():
            value, seat = result["values"][path], _SENTINEL_SEATS[role]
            assert seat in value if path.startswith("in ") else value == seat, f"{module} {path} is {value!r}, not the {role} seat"
        if module in _GEMINI_SEAT_CALLERS:
            assert paths or parser_defaults, f"{module} has no checked seat binding"
        return
    if module in _SEAT_FREE_MODULES:
        assert result["error"] is None, result  # binds no seat, so a missing seat cannot break it
        return
    expected_roles = {"review": ["review"], "routine": ["routine"], "invalid_catalog": ["review", "routine"]}[case]
    assert result["error"] == "GeminiSeatUnavailable", result
    assert result["roles"] == expected_roles
    assert all(repr(role) in result["message"] for role in expected_roles)
    own_frames = [line for filename, _, line in result["frames"] if filename == origin]
    assert own_frames, f"{module} did not reach a seat binding of its own"
    failing_line = own_frames[0]  # the module-level statement
    assert "batch_gemini_config import" in failing_line or "_gemini_seats()" in failing_line, failing_line
