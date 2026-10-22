"""V7.2 Step 5 — prompt_generator composition + opt-in wiring tests.

Covers:
- per-slot composition (writer = preamble+body+shared; reviewer = rubric+shared)
- topo / slot order preserved from the loader
- ``shared.contract`` rules emitted into BOTH writer and reviewer blocks
- ``#R-*`` markers restored (registry bodies don't carry them)
- ONE Obligation Checklist, single-sourced across writer + reviewer + the
  ``wiki_coverage_gate`` extraction
- the ``--use-generator`` opt-in flag: OFF → byte-identical legacy dicts,
  ON → registry-composed prompts with full ``#R-*`` parity for m20
- level edge: A1-gated rules present in BOTH prompts at a1, absent at b1
"""

from __future__ import annotations

import re

import pytest

from scripts.build import linear_pipeline as lp
from scripts.build import prompt_generator as pg
from scripts.build.phases.implementation_map import seed_implementation_map


@pytest.fixture(scope="module")
def m20():
    """Real a1/my-morning plan + manifest + implementation map fixtures."""
    level, slug = "a1", "my-morning"
    plan_path = lp.plan_path_for(level, slug)
    plan = lp.plan_check(plan_path)
    plan_content = plan_path.read_text(encoding="utf-8")
    wiki_manifest = lp.build_wiki_manifest_data(level=level, slug=slug, plan=plan)
    implementation_map = seed_implementation_map(wiki_manifest, plan=plan)
    return {
        "level": level,
        "slug": slug,
        "plan": plan,
        "plan_content": plan_content,
        "wiki_manifest": wiki_manifest,
        "implementation_map": implementation_map,
    }


# --------------------------------------------------------------------------- #
# Composition
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# Level edge
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# Obligation checklist — single source
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# Opt-in flag — OFF byte-identical, ON parity
# --------------------------------------------------------------------------- #


def test_gate_consumes_obligation_checklist_one_to_one(m20):
    """wiki_coverage_gate sees the same obligations the renderer emitted."""
    from scripts.audit.wiki_coverage_gate import obligations_from_checklist

    checklist_obj = pg.build_obligation_checklist_object(
        m20["wiki_manifest"],
        seeded_map=m20["implementation_map"],
    )
    rendered = pg.build_obligation_checklist(
        m20["wiki_manifest"],
        obligation_checklist=checklist_obj,
    )
    gate_obligations = obligations_from_checklist(checklist_obj)
    gate_ids = [str(item["id"]) for item in gate_obligations]
    rendered_ids = [
        match
        for match in re.findall(r"^### (\S+) \(", rendered, flags=re.MULTILINE)
        if match != "wiki_vocabulary_minimum"
    ]

    assert len(gate_obligations) == len(m20["implementation_map"]["entries"])
    assert rendered_ids == gate_ids
    assert len(rendered_ids) == len(set(rendered_ids)), "no orphan/duplicate rendered obligations"
    for item in gate_obligations:
        if item["type"] == "sequence_step":
            assert item["normalized_claim"] in rendered
