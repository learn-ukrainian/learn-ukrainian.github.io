from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

import scripts.audit.wiki_coverage_gate as gate
from scripts.audit.wiki_coverage_gate import (
    check_wiki_coverage,
    check_wiki_coverage_paths,
    validate_obligations,
)
from scripts.build import linear_pipeline
from scripts.build.phases.implementation_map import (
    seed_implementation_map,
    write_implementation_map,
)
from scripts.build.phases.wiki_manifest import extract_manifest

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


def _l2_manifest(
    *,
    treatment: str = "contrast_pair",
    obligation_id: str = "err-1",
    incorrect: str = "Я прокидаєшся.",
    correct: str = "Я прокидаюся.",
    why: str = "The person ending must match я.",
) -> dict[str, Any]:
    return {
        "slug": "fixture",
        "wiki_path": "wiki/pedagogy/a1/fixture.md",
        "sequence_steps": [],
        "l2_errors": [
            {
                "id": obligation_id,
                "incorrect": incorrect,
                "correct": correct,
                "why": why,
                "treatment": treatment,
                "source_lines": "20",
            }
        ],
        "phonetic_rules": [],
        "decolonization_bans": [],
        "external_resources": [],
    }


def _phonetic_manifest() -> dict[str, Any]:
    return {
        "slug": "fixture",
        "wiki_path": "wiki/pedagogy/a1/fixture.md",
        "sequence_steps": [],
        "l2_errors": [],
        "phonetic_rules": [
            {
                "id": "phon-1",
                "written": "-шся",
                "spoken": "[с':а]",
                "treatment": "explicit_explanation",
                "source_lines": "30",
            }
        ],
        "decolonization_bans": [],
        "external_resources": [],
    }


def _ban_manifest() -> dict[str, Any]:
    return {
        "slug": "fixture",
        "wiki_path": "wiki/pedagogy/a1/fixture.md",
        "sequence_steps": [],
        "l2_errors": [],
        "phonetic_rules": [],
        "decolonization_bans": [
            {
                "id": "ban-1",
                "rule": "Do not frame Ukrainian as a dialect.",
                "source_lines": "40",
            }
        ],
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


def _activity_yaml(text: str, *, activity_id: str = "act-1") -> str:
    return yaml.safe_dump(
        [
            {
                "id": activity_id,
                "type": "select",
                "prompt": text,
                "items": [
                    {
                        "prompt": text,
                        "options": [text],
                        "answer": text,
                    }
                ],
            }
        ],
        allow_unicode=True,
        sort_keys=False,
    )


def _single_proposal(report: dict[str, Any]) -> dict[str, Any]:
    proposals = report["fix_proposals"]
    assert len(proposals) == 1
    proposal = proposals[0]
    assert set(proposal) == PROPOSAL_KEYS
    return proposal


def test_pass_short_circuit_omits_fix_proposals() -> None:
    manifest = _sequence_manifest()

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map={"step-1": _claim()},
        module_md="Teach `привіт` and `ранок` together.",
        activities_yaml="[]",
        seeded_map=_seeded(manifest),
    )

    assert report["passed"] is True
    assert "fix_proposals" not in report


def test_back_compat_without_seeded_map_emits_degraded_fix_proposals_on_failure() -> None:
    manifest = _sequence_manifest()

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map={},
        module_md="",
        activities_yaml="[]",
    )

    proposal = _single_proposal(report)
    assert report["passed"] is False
    assert proposal["failure_reason"] == "implementation_map_missing"
    assert proposal["expected_treatment"] == {}
    assert proposal["manifest_payload"] == {}
    assert "no seeded sidecar" in proposal["surgical_diff_hint"]


def test_implementation_map_missing_uses_seeded_artifact_and_location_hint() -> None:
    manifest = _sequence_manifest(heading="Morning proof")

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map={},
        module_md="",
        activities_yaml="[]",
        seeded_map=_seeded(manifest),
    )

    proposal = _single_proposal(report)
    assert proposal["current_artifact_state"] == "MISSING (no <implementation_map> entry from writer)"
    assert "artifact=module.md" in proposal["surgical_diff_hint"]
    assert "location=§Morning proof" in proposal["surgical_diff_hint"]
    assert proposal["expected_treatment"]
    assert proposal["manifest_payload"]["id"] == "step-1"


def test_unknown_artifact_points_back_to_seeded_artifact() -> None:
    manifest = _sequence_manifest()

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map={"step-1": _claim("readme.md", "whole file")},
        module_md="Teach `привіт` and `ранок` together.",
        activities_yaml="[]",
        seeded_map=_seeded(manifest),
    )

    proposal = _single_proposal(report)
    assert proposal["failure_reason"] == "unknown_artifact"
    assert "artifact=readme.md" in proposal["surgical_diff_hint"]
    assert "requires artifact=module.md" in proposal["surgical_diff_hint"]
    assert "writer_claim={'artifact': 'readme.md'" in proposal["current_artifact_state"]


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


def test_unresolved_location_surfaces_substance_failure_with_proposal() -> None:
    """When the writer's `location` doesn't anchor AND the obligation's
    substance is genuinely absent from the artifact, the gate must still
    FAIL — but with the substance-level reason (`sequence_claim_missing`,
    `phonetic_rule_missing`, etc.) instead of the location-level reason
    (`claimed_location_missing`). A fix_proposal must be emitted so the
    correction loop can target the missing substance markers.

    PR #2207 made `_location_text` permissive on location resolution but
    did NOT loosen the substance check — that's still the canonical
    correctness gate. This test pins the FAIL path: bogus location +
    absent substance → FAIL + actionable proposal.
    """
    # Use a required_claim with markers that are deliberately ABSENT from
    # the module. The default required_claim ("Teach `привіт` and `ранок`
    # together.") would match the fallback module — supply an explicit one.
    manifest = _sequence_manifest(
        heading="Diaspora deep-dive",
        required_claim="Diaspora deep-dive — discuss `діаспора` and `еміграція`.",
    )

    report = check_wiki_coverage(
        manifest=manifest,
        # location doesn't anchor + substance markers absent from module.
        implementation_map={"step-1": _claim("module.md", "§Diaspora")},
        module_md="## Routine\nA brief morning narrative without diaspora content.\n",
        activities_yaml="[]",
        seeded_map=_seeded(manifest),
    )

    proposal = _single_proposal(report)
    # New failure mode is the substance-level reason.
    assert proposal["failure_reason"] == "sequence_claim_missing"
    # current_artifact_state now reflects the substance-check evidence
    # (the actual module text scanned by the fallback), giving the
    # correction loop the real context for proposing fixes — not a
    # placeholder "resolved_artifact_text=''" sentinel.
    assert "A brief morning narrative" in proposal["current_artifact_state"]
    # Surgical diff hint must surface the missing markers / claim shape
    # so the correction loop can target them.
    assert "Diaspora deep-dive" in proposal["surgical_diff_hint"]


def test_missing_incorrect_quotes_payload_incorrect() -> None:
    manifest = _l2_manifest()

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map={"err-1": _claim("activities.yaml", "act-1")},
        module_md="",
        activities_yaml=_activity_yaml("Я прокидаюся."),
        seeded_map=_seeded(manifest),
    )

    proposal = _single_proposal(report)
    assert proposal["failure_reason"] == "missing_incorrect"
    assert "manifest_payload.incorrect ('Я прокидаєшся.')" in proposal["surgical_diff_hint"]
    assert "act-1" in proposal["surgical_diff_hint"]


def test_missing_correct_quotes_payload_correct() -> None:
    manifest = _l2_manifest()

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map={"err-1": _claim("activities.yaml", "act-1")},
        module_md="",
        activities_yaml=_activity_yaml("Я прокидаєшся."),
        seeded_map=_seeded(manifest),
    )

    proposal = _single_proposal(report)
    assert proposal["failure_reason"] == "missing_correct"
    assert "manifest_payload.correct ('Я прокидаюся.')" in proposal["surgical_diff_hint"]


def test_missing_incorrect_and_correct_joins_both_hint_lines() -> None:
    manifest = _l2_manifest()

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map={"err-1": _claim("activities.yaml", "act-1")},
        module_md="",
        activities_yaml=_activity_yaml("Choose the morning form."),
        seeded_map=_seeded(manifest),
    )

    proposal = _single_proposal(report)
    assert proposal["failure_reason"] == "missing_incorrect_and_correct"
    assert "manifest_payload.incorrect ('Я прокидаєшся.')" in proposal["surgical_diff_hint"]
    assert "; Insert manifest_payload.correct ('Я прокидаюся.')" in proposal["surgical_diff_hint"]


def test_contrast_pair_not_in_activity_quotes_claimed_artifact() -> None:
    manifest = _l2_manifest()

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map={"err-1": _claim("module.md", "whole file")},
        module_md="Я прокидаєшся. -> Я прокидаюся.",
        activities_yaml="[]",
        seeded_map=_seeded(manifest),
    )

    proposal = _single_proposal(report)
    assert proposal["failure_reason"] == "contrast_pair_not_in_activity"
    assert proposal["surgical_diff_hint"] == (
        "Move contrast_pair to activities.yaml entry - currently claimed in module.md"
    )


def test_prose_substance_missing_quotes_payload_correct_and_why() -> None:
    manifest = _l2_manifest(treatment="prose_explanation")

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map={"err-1": _claim("module.md", "whole file")},
        module_md="This paragraph is unrelated but present.",
        activities_yaml="[]",
        seeded_map=_seeded(manifest),
    )

    proposal = _single_proposal(report)
    assert proposal["failure_reason"] == "prose_substance_missing"
    assert "manifest_payload.correct ('Я прокидаюся.')" in proposal["surgical_diff_hint"]
    assert "manifest_payload.why ('The person ending must match я.')" in proposal["surgical_diff_hint"]


def test_phonetic_rule_missing_quotes_written_spoken_and_example_pair_instruction() -> None:
    manifest = _phonetic_manifest()

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map={"phon-1": _claim("module.md", "whole file")},
        module_md="The written ending -шся is introduced without IPA.",
        activities_yaml="[]",
        seeded_map=_seeded(manifest),
    )

    proposal = _single_proposal(report)
    assert proposal["failure_reason"] == "phonetic_rule_missing"
    assert "written='-шся'" in proposal["surgical_diff_hint"]
    assert "spoken=\"[с':а]\"" in proposal["surgical_diff_hint"]
    assert "example pair" in proposal["surgical_diff_hint"]


def test_sequence_claim_missing_quotes_heading_and_required_claim() -> None:
    manifest = _sequence_manifest(heading="Morning proof")

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map={"step-1": _claim("module.md", "whole file")},
        module_md="A present but unrelated section.",
        activities_yaml="[]",
        seeded_map=_seeded(manifest),
    )

    proposal = _single_proposal(report)
    assert proposal["failure_reason"] == "sequence_claim_missing"
    assert "manifest_payload.heading ('Morning proof')" in proposal["surgical_diff_hint"]
    assert "required_claim: 'Teach `привіт` and `ранок` together.'" in proposal["surgical_diff_hint"]


def test_ban_substance_missing_quotes_seeded_rule() -> None:
    manifest = _ban_manifest()
    manifest["decolonization_bans"][0]["rule"] = "Use «рушник» (не «полотенце»)."

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map={"ban-1": _claim("module.md", "whole file")},
        module_md="This paragraph is present but avoids the banned framing.",
        activities_yaml="[]",
        seeded_map=_seeded(manifest),
    )

    proposal = _single_proposal(report)
    assert proposal["failure_reason"] == "ban_substance_missing"
    assert "manifest_payload.rule ('Use «рушник» (не «полотенце»).')" in proposal["surgical_diff_hint"]
    assert "lexical substitution substance" in proposal["surgical_diff_hint"]


def test_unknown_obligation_type_proposal_names_seeder_bug() -> None:
    proposal = gate._build_fix_proposal(
        {
            "obligation_id": "weird-1",
            "type": "external_resource",
            "reason": "unknown_obligation_type",
            "status": "FAIL",
            "claim": {},
            "_evidence_text": "evidence",
        },
        {
            "obligation_id": "weird-1",
            "obligation_type": "external_resource",
            "artifact": "module.md",
            "location_hint": "whole file",
            "treatment_template": {"shape": "unknown"},
            "manifest_payload": {"id": "weird-1", "url": "https://example.invalid"},
        },
        {"module.md": "evidence"},
    )

    assert proposal["manifest_payload"] == {}
    assert "seeder bug" in proposal["surgical_diff_hint"]
    assert set(proposal) == PROPOSAL_KEYS


def test_current_artifact_state_truncates_long_evidence_text() -> None:
    manifest = _l2_manifest(treatment="prose_explanation")
    long_text = "x" * 2000

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map={"err-1": _claim("module.md", "whole file")},
        module_md=long_text,
        activities_yaml="[]",
        seeded_map=_seeded(manifest),
    )

    proposal = _single_proposal(report)
    assert proposal["current_artifact_state"] == ("x" * 400) + "..."


def test_fix_proposals_list_with_eighteen_entries_is_json_serializable() -> None:
    manifest = {
        "slug": "fixture",
        "wiki_path": "wiki/pedagogy/a1/fixture.md",
        "sequence_steps": [
            {
                "id": f"step-{index}",
                "heading": f"Heading {index}",
                "step_num": index,
                "required_claim": f"Teach `term-{index}` and `ранок`.",
                "source_lines": str(index),
            }
            for index in range(1, 19)
        ],
        "l2_errors": [],
        "phonetic_rules": [],
        "decolonization_bans": [],
        "external_resources": [],
    }

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map={},
        module_md="",
        activities_yaml="[]",
        seeded_map=_seeded(manifest),
    )

    assert len(report["fix_proposals"]) == 18
    json.dumps(report, sort_keys=True)


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
    assert "location=§Morning proof" in proposal["surgical_diff_hint"]
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


def test_m20_real_world_manifest_synthesizes_ten_fix_proposals() -> None:
    manifest = extract_manifest(PROJECT_ROOT / "wiki/pedagogy/a1/my-morning.md")
    seeded_map = seed_implementation_map(manifest)
    obligations = validate_obligations(manifest)
    implemented_ids = {
        "step-1",
        "step-2",
        "step-3",
        "step-4",
        "step-5",
        "err-1",
        "err-4",
        "err-6",
    }
    implemented = [obligation for obligation in obligations if obligation["id"] in implemented_ids]
    implementation_map: dict[str, dict[str, str]] = {}
    module_parts: list[str] = []
    activities: list[dict[str, Any]] = []

    for obligation in implemented:
        obligation_id = str(obligation["id"])
        if obligation["type"] == "l2_error":
            activity_id = f"act-{obligation_id}"
            implementation_map[obligation_id] = _claim("activities.yaml", activity_id)
            activities.append(
                {
                    "id": activity_id,
                    "type": "select",
                    "prompt": f"{obligation['incorrect']} -> {obligation['correct']}",
                    "items": [
                        {
                            "prompt": f"{obligation['incorrect']} -> {obligation['correct']}",
                            "options": [obligation["incorrect"], obligation["correct"]],
                            "answer": obligation["correct"],
                        }
                    ],
                }
            )
            continue
        implementation_map[obligation_id] = _claim("module.md", "whole file")
        module_parts.append(str(obligation["required_claim"]))

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map=implementation_map,
        module_md="\n\n".join(module_parts),
        activities_yaml=yaml.safe_dump(activities, allow_unicode=True, sort_keys=False),
        seeded_map=seeded_map,
    )

    assert len(report["fix_proposals"]) == 10
    for proposal in report["fix_proposals"]:
        assert set(proposal) == PROPOSAL_KEYS
        for key in PROPOSAL_KEYS - {"manifest_payload"}:
            assert proposal[key]
