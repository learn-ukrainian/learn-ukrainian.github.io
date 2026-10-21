from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from scripts.audit.wiki_coverage_gate import (
    check_wiki_coverage,
    check_wiki_coverage_paths,
)
from scripts.build import linear_pipeline
from scripts.build.phases.implementation_map import (
    seed_implementation_map,
    write_implementation_map,
)

pytestmark = pytest.mark.reads_content

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROPOSAL_KEYS = {
    "obligation_id",
    "obligation_type",
    "failure_reason",
    "current_artifact_state",
    "expected_treatment",
    "surgical_diff_hint",
    "manifest_payload",
}


def _sequence_manifest(
    *,
    obligation_id: str = "step-1",
    heading: str = "Morning routine",
    required_claim: str = "Teach `привіт` and `ранок` together.",
) -> dict[str, Any]:
    return {
        "slug": "fixture",
        "wiki_path": "wiki/pedagogy/a1/fixture.md",
        "sequence_steps": [
            {
                "id": obligation_id,
                "heading": heading,
                "step_num": 1,
                "required_claim": required_claim,
                "source_lines": "10",
            }
        ],
        "l2_errors": [],
        "phonetic_rules": [],
        "decolonization_bans": [],
        "external_resources": [],
    }


def _claim(
    artifact: str = "module.md",
    location: str = "whole file",
    treatment: str = "fixture treatment",
) -> dict[str, str]:
    return {"artifact": artifact, "location": location, "treatment": treatment}


def _seeded(manifest: dict[str, Any]) -> dict[str, Any]:
    return seed_implementation_map(manifest)


def _single_proposal(report: dict[str, Any]) -> dict[str, Any]:
    proposals = report["fix_proposals"]
    assert len(proposals) == 1
    proposal = proposals[0]
    assert set(proposal) == PROPOSAL_KEYS
    return proposal


def test_unresolved_location_passes_when_substance_present_anywhere() -> None:
    """PR #2207: `_location_text` now falls back to whole-artifact matching
    when the writer's `location` field doesn't anchor to a heading and
    isn't a literal substring of the artifact. If the obligation's
    substance markers (backticked terms, italicized markers, or fallback
    substance words) are present anywhere in the artifact, the obligation
    PASSES — writer drift on the descriptive `location` field is a soft
    signal, not a hard contract.

    Pre-PR-#2207 behavior: location='§Diaspora' returned "" target_text
    → FAIL with `claimed_location_missing` + fix_proposal generated.
    New behavior: falls back to whole module.md → substance check finds
    the backticked markers `привіт` and `ранок` from the required_claim
    → PASS, no fix_proposal.

    This converts a noisy false-positive class (writer used descriptive
    location prose) into clean passes, while still failing when content
    is genuinely absent (see
    `test_unresolved_location_surfaces_substance_failure_with_proposal`).
    """
    manifest = _sequence_manifest(heading="Morning proof")

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map={"step-1": _claim("module.md", "§Diaspora")},
        module_md="## Інший розділ\nTeach `привіт` and `ранок` together.",
        activities_yaml="[]",
        seeded_map=_seeded(manifest),
    )

    # New behavior: substance IS in the module (just at a section that
    # doesn't match the descriptive location), so the obligation passes
    # via the whole-artifact fallback.
    assert report["passed"] is True
    assert "fix_proposals" not in report, (
        "When the gate passes via location fallback, no fix proposals "
        "should be emitted"
    )
    step_result = next(
        item for item in report["obligations"] if item["obligation_id"] == "step-1"
    )
    assert step_result["status"] == "PASS"
    assert step_result["reason"] == "sequence_claim_present"


def test_paths_auto_loads_seeded_sidecar(tmp_path: Path) -> None:
    manifest = _sequence_manifest(heading="Morning proof")
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "module.md").write_text("", encoding="utf-8")
    (module_dir / "activities.yaml").write_text("[]", encoding="utf-8")
    (module_dir / "vocabulary.yaml").write_text("[]", encoding="utf-8")
    (module_dir / "resources.yaml").write_text("[]", encoding="utf-8")
    write_implementation_map(_seeded(manifest), module_dir / "implementation_map.json")

    report = check_wiki_coverage_paths(
        manifest=manifest,
        implementation_map={},
        module_dir=module_dir,
    )

    proposal = _single_proposal(report)
    assert "Location '§Morning proof' returns empty text in module.md" in proposal[
        "surgical_diff_hint"
    ]
    assert "no seeded sidecar" not in proposal["surgical_diff_hint"]


def test_pipeline_emits_wiki_coverage_fix_proposals_event(tmp_path: Path) -> None:
    manifest = _sequence_manifest()
    module_dir = tmp_path / "module"
    telemetry = tmp_path / "events.jsonl"
    module_dir.mkdir()
    (module_dir / "module.md").write_text("", encoding="utf-8")
    (module_dir / "activities.yaml").write_text("[]", encoding="utf-8")
    (module_dir / "vocabulary.yaml").write_text("[]", encoding="utf-8")
    (module_dir / "resources.yaml").write_text("[]", encoding="utf-8")
    write_implementation_map(_seeded(manifest), module_dir / "implementation_map.json")

    with linear_pipeline.telemetry_event_sink(telemetry):
        result = linear_pipeline.run_wiki_coverage_gate(
            manifest=manifest,
            writer_output="",
            module_dir=module_dir,
            level="a1",
        )

    events = [json.loads(line) for line in telemetry.read_text(encoding="utf-8").splitlines()]
    event = next(item for item in events if item["event"] == "wiki_coverage_fix_proposals")
    assert result["passed"] is False
    assert event["slug"] == "fixture"
    assert event["fail_count"] == 1
    assert event["proposals"] == result["fix_proposals"]


def test_paths_accepts_wiki_markdown_manifest_path(tmp_path: Path) -> None:
    module_dir = tmp_path / "m20-my-morning"
    module_dir.mkdir()

    report = check_wiki_coverage_paths(
        manifest=PROJECT_ROOT / "wiki/pedagogy/a1/my-morning.md",
        implementation_map="",
        module_dir=module_dir,
    )

    assert report["passed"] is False
    assert len(report["fix_proposals"]) == 18
