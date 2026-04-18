from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from build.finding_topology import classify_topology


def test_topology_is_deterministic() -> None:
    finding = {
        "error_class": "register_drift",
        "location": "## Привіт! / paragraph 2",
        "issue": "The teacher models the opposite register rule in the same scene.",
        "fix": "Make the teacher-student exchange formal.",
    }

    assert classify_topology(finding) == classify_topology(finding)


def test_local_to_prose_rule() -> None:
    finding = {
        "error_class": "notation_error",
        "location": "## Intro / paragraph 1 / sentence 2",
        "issue": "The sentence mislabels [=] as a dash.",
        "fix": "Change the sentence only.",
    }

    assert classify_topology(finding) == "local_to_prose"


def test_section_local_rule() -> None:
    finding = {
        "error_class": "register_drift",
        "location": "## Привіт!",
        "issue": "The register conflict is confined to one H2 section.",
        "fix": "Rewrite that section.",
    }

    assert classify_topology(finding) == "section_local"


def test_cross_section_rule() -> None:
    finding = {
        "error_class": "activity_order",
        "location": "## Intro and ## Practice",
        "issue": "Activity order and vocabulary pacing drift across multiple sections.",
        "fix": "Resequence the module.",
    }

    assert classify_topology(finding) == "cross_section"


def test_plan_level_rule() -> None:
    finding = {
        "error_class": "plan_contradiction",
        "location": "## Whole module",
        "issue": "The plan contradicts its own register rule.",
        "fix": "Change the plan.",
    }

    assert classify_topology(finding) == "plan_level"
