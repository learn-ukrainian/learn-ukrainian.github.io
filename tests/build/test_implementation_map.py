from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.audit.wiki_coverage_gate import validate_obligations
from scripts.build.phases.implementation_map import (
    read_implementation_map,
    seed_implementation_map,
    validate_implementation_map,
    write_implementation_map,
)
from scripts.build.phases.wiki_manifest import extract_manifest

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _fixture_manifest() -> dict[str, Any]:
    return {
        "slug": "fixture-module",
        "wiki_path": "wiki/pedagogy/a1/fixture-module.md",
        "sequence_steps": [
            {
                "id": "step-1",
                "heading": "Привітання",
                "step_num": 1,
                "required_claim": "Start with a morning greeting.",
                "source_lines": "10-11",
            },
            {
                "id": "step-2",
                "heading": "Дії вранці",
                "step_num": 2,
                "required_claim": "Introduce routine verbs.",
                "source_lines": "12-13",
            },
            {
                "id": "step-3",
                "heading": "Зворотні дієслова",
                "step_num": 3,
                "required_claim": "Contrast actions done to oneself.",
                "source_lines": "14-15",
            },
            {
                "id": "step-4",
                "heading": "Мінідіалог",
                "step_num": 4,
                "required_claim": "End with a short dialogue.",
                "source_lines": "16-17",
            },
        ],
        "l2_errors": [
            {
                "id": "l2-1",
                "incorrect": "я вмиваю",
                "correct": "я вмиваюся",
                "why": "Reflexive morning routines need -ся.",
                "treatment": "contrast_pair",
                "source_lines": "20",
            },
            {
                "id": "l2-2",
                "incorrect": "він миєся",
                "correct": "він миється",
                "why": "The third-person reflexive ending is -ться.",
                "treatment": "contrast_pair",
                "source_lines": "21",
            },
            {
                "id": "l2-3",
                "incorrect": "я прокидаю",
                "correct": "я прокидаюся",
                "why": "The verb прокидатися is reflexive in this meaning.",
                "treatment": "prose_explanation",
                "source_lines": "22",
            },
        ],
        "phonetic_rules": [
            {
                "id": "phon-1",
                "written": "-ться",
                "spoken": "[ц':а]",
                "treatment": "explicit_explanation",
                "source_lines": "30",
            },
            {
                "id": "phon-2",
                "written": "-шся",
                "spoken": "[с':а]",
                "treatment": "explicit_explanation",
                "source_lines": "31",
            },
        ],
        "decolonization_bans": [
            {"id": "ban-1", "rule": "Do not frame Ukrainian as a dialect.", "source_lines": "40"},
            {"id": "ban-2", "rule": "Avoid imperial place-name defaults.", "source_lines": "41"},
            {"id": "ban-3", "rule": "Do not normalize Russian calques.", "source_lines": "42"},
            {"id": "ban-4", "rule": "Avoid Soviet nostalgia framing.", "source_lines": "43"},
            {"id": "ban-5", "rule": "Do not omit Ukrainian agency.", "source_lines": "44"},
        ],
        "external_resources": [],
    }


def _manifest_items(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for group in ("sequence_steps", "l2_errors", "phonetic_rules", "decolonization_bans"):
        items.extend(manifest[group])
    return items


def test_seed_emits_one_entry_per_obligation_in_manifest_order() -> None:
    manifest = _fixture_manifest()
    payload = seed_implementation_map(manifest)

    assert len(payload["entries"]) == 14
    assert payload["manifest_obligation_count"] == 14
    assert [entry["obligation_id"] for entry in payload["entries"]] == [
        item["id"] for item in _manifest_items(manifest)
    ]
    assert [entry["obligation_type"] for entry in payload["entries"]] == [
        "sequence_step",
        "sequence_step",
        "sequence_step",
        "sequence_step",
        "l2_error",
        "l2_error",
        "l2_error",
        "phonetic_rule",
        "phonetic_rule",
        "decolonization_ban",
        "decolonization_ban",
        "decolonization_ban",
        "decolonization_ban",
        "decolonization_ban",
    ]


def test_artifact_mapping_matches_obligation_type_and_treatment() -> None:
    payload = seed_implementation_map(_fixture_manifest())
    artifacts = {entry["obligation_id"]: entry["artifact"] for entry in payload["entries"]}

    assert artifacts == {
        "step-1": "module.md",
        "step-2": "module.md",
        "step-3": "module.md",
        "step-4": "module.md",
        "l2-1": "activities.yaml",
        "l2-2": "activities.yaml",
        "l2-3": "module.md",
        "phon-1": "module.md",
        "phon-2": "module.md",
        "ban-1": "module.md",
        "ban-2": "module.md",
        "ban-3": "module.md",
        "ban-4": "module.md",
        "ban-5": "module.md",
    }


def test_manifest_payload_round_trips_verbatim() -> None:
    manifest = _fixture_manifest()
    payload = seed_implementation_map(manifest)
    manifest_by_id = {item["id"]: item for item in _manifest_items(manifest)}

    for entry in payload["entries"]:
        assert entry["manifest_payload"] == manifest_by_id[entry["obligation_id"]]


def test_json_schema_validates_seeded_output() -> None:
    validate_implementation_map(seed_implementation_map(_fixture_manifest()))


def test_write_read_round_trip_identity(tmp_path: Path) -> None:
    payload = seed_implementation_map(_fixture_manifest())
    path = tmp_path / "implementation_map.json"

    write_implementation_map(payload, path)

    assert read_implementation_map(path) == payload


def test_empty_manifest_writes_empty_entries(tmp_path: Path) -> None:
    manifest = {
        "slug": "empty-module",
        "wiki_path": "wiki/pedagogy/a1/empty-module.md",
        "sequence_steps": [],
        "l2_errors": [],
        "phonetic_rules": [],
        "decolonization_bans": [],
        "external_resources": [],
    }

    payload = seed_implementation_map(manifest)
    path = tmp_path / "empty-implementation-map.json"
    write_implementation_map(payload, path)

    assert payload["entries"] == []
    assert read_implementation_map(path) == payload


def test_location_hint_fallback_without_plan() -> None:
    payload = seed_implementation_map(_fixture_manifest(), plan=None)
    hints = {entry["obligation_id"]: entry["location_hint"] for entry in payload["entries"]}

    assert hints["step-1"] == "§Привітання"
    assert hints["step-2"] == "§Дії вранці"
    assert hints["step-3"] == "§Зворотні дієслова"
    assert hints["step-4"] == "§Мінідіалог"
    assert hints["l2-1"] == "activities.yaml"
    assert hints["l2-2"] == "activities.yaml"
    assert hints["l2-3"] == "(any prose section)"
    assert hints["phon-1"] == "(any prose section)"
    assert hints["phon-2"] == "(any prose section)"
    assert hints["ban-1"] == "(any prose section)"


def test_location_hint_uses_simple_plan_section_match() -> None:
    plan = {
        "sections": [
            {"heading": "Розминка"},
            {"heading": "Вимова -ться"},
            {"heading": "Пояснення: я прокидаю"},
            {"heading": "Деколонізація: dialect"},
        ]
    }

    payload = seed_implementation_map(_fixture_manifest(), plan=plan)
    hints = {entry["obligation_id"]: entry["location_hint"] for entry in payload["entries"]}

    assert hints["phon-1"] == "§Вимова -ться"
    assert hints["l2-3"] == "§Пояснення: я прокидаю"
    assert hints["ban-1"] == "§Деколонізація: dialect"


def test_seeder_is_byte_deterministic() -> None:
    manifest = _fixture_manifest()

    first = json.dumps(seed_implementation_map(manifest), ensure_ascii=False, indent=2, sort_keys=True)
    second = json.dumps(seed_implementation_map(manifest), ensure_ascii=False, indent=2, sort_keys=True)

    assert first == second


def test_m20_real_world_manifest_seeds_gate_obligation_count() -> None:
    manifest = extract_manifest(PROJECT_ROOT / "wiki/pedagogy/a1/my-morning.md")
    payload = seed_implementation_map(manifest)
    gate_obligations = validate_obligations(manifest)

    assert len(payload["entries"]) == len(gate_obligations)
    assert len(payload["entries"]) >= 10
