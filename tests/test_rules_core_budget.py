"""The always-loaded rules core is complete, bounded against growth, and names only live models.

The byte budget guards against unbounded growth; obligations are never cut to fit it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "agents_extensions/shared/rules/core.md"
CATALOG = ROOT / "scripts/config/model_catalog.yaml"
CORE_BYTE_BUDGET = 34_000
PILLARS = tuple(f"P{n}" for n in range(10))
# A launcher context-window suffix such as `[1m]` is not part of the model id; the base id is checked.
MODEL_ID = re.compile(r"`((?:gpt|claude|gemini|grok|kimi|glm|deepseek|composer|poolside)[^`\s\[]*)(?:\[[^\]`\s]*\])?`")


def _section(text: str, heading_prefix: str) -> str:
    start = re.search(rf"^## {heading_prefix} — .*$", text, re.MULTILINE)
    assert start, heading_prefix
    end = re.search(r"^## ", text[start.end():], re.MULTILINE)
    return text[start.end(): start.end() + end.start()] if end else text[start.end():]


def test_core_fits_the_byte_budget() -> None:
    size = len(CORE.read_bytes())
    assert size <= CORE_BYTE_BUDGET, (
        f"core.md is {size} bytes; budget {CORE_BYTE_BUDGET} guards against growth "
        "(obligations are never cut to fit; raise the budget deliberately if a real obligation needs room)"
    )


@pytest.mark.parametrize("pillar", PILLARS)
def test_core_states_each_pillar_once(pillar: str) -> None:
    headings = re.findall(rf"^## {pillar} — ", CORE.read_text(encoding="utf-8"), re.MULTILINE)
    assert len(headings) == 1, f"expected one '## {pillar} — ' heading, found {len(headings)}"


def test_model_table_names_only_active_catalog_models() -> None:
    table = _section(CORE.read_text(encoding="utf-8"), "P2")
    named = set(MODEL_ID.findall(table))
    assert named, "P2 names no model ids"
    models = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))["models"]
    unknown = sorted(model for model in named if model not in models)
    inactive = sorted(
        model for model in named
        if model in models and models[model].get("lifecycle", "active") != "active"
    )
    assert not unknown, f"P2 names models absent from the catalog: {unknown}"
    assert not inactive, f"P2 names models that are not active: {inactive}"
