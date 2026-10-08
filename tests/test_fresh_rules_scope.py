"""Sizing scope at the real rule injection surfaces, without changing lesson policy.

These checks exercise the offline selector and rules API, then inspect the
context each digest/agent supplies. They prove rule routing and retained duties;
they do not claim that an LLM follows those instructions or that a lesson passes.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from scripts.lib import rules_core

ROOT = Path(__file__).resolve().parents[1]
SHARED = "agents_extensions/shared"
RULES = f"{SHARED}/rules"

pytestmark = pytest.mark.usefixtures("hermetic_monitor")


def _section(text: str, number: int) -> str:
    match = re.search(rf"^## {number}\. .*?(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    assert match, f"missing rule {number}"
    return match.group()


@pytest.fixture
def api_client():
    from fastapi.testclient import TestClient

    from scripts.api.main import app

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.mark.parametrize("surface", ["offline", "api-full", "api-curriculum"])
def test_curriculum_injection_routes_sizing_and_keeps_legacy_gates(api_client, surface):
    if surface == "offline":
        text = rules_core.assemble(rules_core.scope_sources("task:curriculum"), ROOT)
    else:
        query = "&scope=task:curriculum" if surface == "api-curriculum" else ""
        response = api_client.get(f"/api/rules?format=markdown{query}")
        assert response.status_code == 200
        text = response.text

    scope = _section(text, 1).split("**Scope.**", 1)[1].split("\n\n", 1)[0]
    # Both word/section targets and count gates are scoped; naturalness is not.
    for term in ("Rule 1, rule 3", "Words, Activities, Unique_types and Vocab", "legacy module workflows"):
        assert term in scope
    for workflow in ("V7", "linear pipeline", "track-completion"):
        assert workflow in scope
    assert "every module workflow outside the fresh-build engine" in scope
    assert "Core fresh-build lessons (rule 4)" in scope
    assert "sized by their own contracts" in scope
    assert "Naturalness row of rule 2 and all other rules bind both" in scope

    gates = _section(text, 2)
    for obligation in (
        "| Words | ≥ target from config.py |",
        "| Activities | ≥ minimum count for level |",
        "| Unique_types | Sufficient variety |",
        "| Vocab | ≥ minimum vocabulary for level |",
        "| Naturalness | ≥ 8/10 |",
        "ALL gates must be GREEN",
    ):
        assert obligation in gates
    assert "±10% tolerance" in _section(text, 3)
    assert "A1=1200" in _section(text, 1)
    assert "C2=5000" in _section(text, 1)
    assert "The two word-target rows below follow rule 1's scope" in text
    ownership = _section(text, 4)
    assert "scripts/build/fresh/" in ownership
    assert "docs/epics/fresh-build-build-program.md" in ownership
    assert "V7 module completion follows" in ownership


@pytest.mark.parametrize("surface", ["offline", "api"])
def test_content_seat_keeps_universal_duties_beyond_sizing(api_client, surface):
    text = rules_core.core_text("content", root=ROOT)
    if surface == "api":
        response = api_client.get("/api/rules?scope=content&format=markdown")
        assert response.status_code == 200
        assert response.text == text
        text = response.text
    targets = next(line for line in text.splitlines() if "<!-- ca-targets:" in line)
    assert "Legacy module workflows" in targets
    assert "non-negotiable-rules.md` rule 1 scope" in targets
    assert "Core fresh-build lessons are sized by their own contracts (rule 4)" in targets
    assert "only sizing is scoped" in targets
    for duty in ("plan-file", "source-backed pedagogy", "naturalness", "still bind every workflow"):
        assert duty in targets
    for duty in ("Never silently modify plan files", "Content outlines, objectives and word targets remain immutable"):
        assert duty in targets
    proof = next(line for line in text.splitlines() if "<!-- ca-proof:" in line)
    assert "Use textbook-grounded dialogues; in legacy module workflows" in proof
    assert "1.5× word-target overshoot" in proof
    assert "fresh-build lessons follow their own sizing contract" in proof
    assert "Every bug fix includes a regression test" in proof
    review = next(line for line in text.splitlines() if "<!-- ca-review:" in line)
    assert "PASS ≥ 8, REVISE < 8, REJECT < 6; target 9" in review
    assert "source-backed" in targets
    assert "verify every vocabulary word through VESUM" in text
    assert "<!-- ca-targets:" not in rules_core.core_text("core", root=ROOT)


def test_fresh_task_selector_leads_to_its_own_contracts(api_client):
    sources = rules_core.scope_sources("task:fresh-build")
    assert sources == ("docs/epics/fresh-build-build-program.md",)
    response = api_client.get("/api/rules?scope=task:fresh-build&format=json")
    assert response.status_code == 200
    payload = response.json()
    assert payload["sources"] == list(sources)
    assert payload["markdown"] == rules_core.assemble(sources, ROOT)
    for contract in ("fresh-build-requirements.md", "fresh-build-plan-schema.md"):
        assert contract in payload["markdown"]
        assert (ROOT / "docs/epics" / contract).is_file()
    assert "writer contract (#8431" in payload["markdown"]
    assert "review contract (#8430" in payload["markdown"]


@pytest.mark.parametrize(
    ("path", "directive"),
    [
        (f"{RULES}/critical-rules.md", "Scope: legacy module workflows"),
        (f"{SHARED}/memory/MEMORY.md", "WORD TARGETS (legacy module workflows)"),
        (f"{SHARED}/agents/curriculum-orchestrator.md", "Legacy module word targets are minimums"),
        ("CLAUDE.md", "legacy word count targets are MINIMUMS"),
        ("GEMINI.md", "Legacy module word targets from"),
    ],
)
def test_standalone_injection_directives_point_to_fresh_contracts(path, directive):
    text = (ROOT / path).read_text(encoding="utf-8")
    paragraph = next(part for part in text.split("\n\n") if directive in part)
    assert "fresh-build lessons" in paragraph.lower()
    assert "rule 4" in paragraph or "rules 1 and 4" in paragraph
    if path.endswith("MEMORY.md"):
        assert "1.5× overshoot (4000 → 5500-6000)" in paragraph
    if path.endswith("curriculum-orchestrator.md") or path == "CLAUDE.md":
        # A second conciseness clause must not reintroduce an unscoped minimum.
        assert "where word targets are MINIMUMS" not in text
        assert "content is exempt: word targets" not in text


def test_universal_source_naturalness_and_plan_rules_remain_in_api(api_client):
    response = api_client.get("/api/rules?scope=task:curriculum&format=markdown")
    assert response.status_code == 200
    text = response.text
    assert "Rewrite any text that fails naturalness" in _section(text, 5)
    assert "All words VESUM-verified" in _section(text, 5)
    assert "Every review must: read content first" in _section(text, 6)
    plans = _section(text, 7)
    assert "immutable without approval" in plans
    assert "Content outline, objectives, and word targets remain immutable" in plans
    assert "vocabulary_hints" in plans
