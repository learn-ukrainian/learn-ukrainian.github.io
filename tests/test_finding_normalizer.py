from __future__ import annotations

import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from build.finding_normalizer import normalize_finding


def test_unclassified_fallback_preserves_original_prose(tmp_path: Path) -> None:
    growth_log = tmp_path / "growth.yaml"
    finding = {
        "dimension": "Pedagogical Quality",
        "severity": "minor",
        "location": "## Intro",
        "issue": "The explanation feels weirdly slanted in a way the rules do not know yet.",
        "fix": "Make it more concrete.",
    }

    normalized = normalize_finding(finding, growth_log_path=growth_log)

    assert normalized["error_class"] == "unclassified"
    assert normalized["original_prose"]["issue"] == finding["issue"]
    logged = yaml.safe_load(growth_log.read_text("utf-8"))
    assert logged[0]["issue"] == finding["issue"]


def test_growth_log_appends(tmp_path: Path) -> None:
    growth_log = tmp_path / "growth.yaml"

    normalize_finding(
        {
            "dimension": "Plan Adherence",
            "severity": "major",
            "location": "## Intro",
            "issue": "Unknown issue one.",
            "fix": "Unknown fix one.",
        },
        growth_log_path=growth_log,
    )
    normalize_finding(
        {
            "dimension": "Plan Adherence",
            "severity": "major",
            "location": "## Practice",
            "issue": "Unknown issue two.",
            "fix": "Unknown fix two.",
        },
        growth_log_path=growth_log,
    )

    logged = yaml.safe_load(growth_log.read_text("utf-8"))
    assert [item["issue"] for item in logged] == ["Unknown issue one.", "Unknown issue two."]
