from __future__ import annotations

import json
from pathlib import Path

from scripts.audit.atlas_intake_census import build_census
from scripts.audit.atlas_intake_gate import (
    CLASSIFICATION_AUTO_APPROVE,
    CLASSIFICATION_REJECT,
    CLASSIFICATION_REVIEW_QUEUE,
    classification_counts,
    classify_candidate,
    classify_candidates,
)
from scripts.audit.atlas_intake_registry import (
    REQUIRED_SOURCE_FAMILIES,
    registry_payload,
    source_family_definition,
)
from scripts.audit.check_atlas_intake_freeze import (
    build_surface_snapshot,
    compare_snapshots,
)
from scripts.audit.source_inventory_intake import (
    SourceInventoryCandidate,
    read_source_inventory,
    source_inventory_candidates,
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _write_minimal_freeze_surface(root: Path) -> None:
    _write_json(
        root / "site/src/data/lexicon-daily-pool.json",
        [{"lemma": "дім", "slug": "дім", "gloss": "house", "k": "vyv", "cefr": "A1"}],
    )
    _write_json(
        root / "site/src/data/lexicon-practice-deck.pointer.json",
        {
            "deck_version": "atlas-practice-v1-fixture",
            "package_sha256": "fixture",
            "file_count": 3,
            "files": [
                {
                    "path": "practice-index.A1.json",
                    "kind": "index",
                    "counts": {"lexemes": 2, "cloze": 1},
                }
            ],
        },
    )
    _write_json(
        root / "site/src/data/lexicon-practice-reviewed-sources.json",
        {"reviewed": [{"status": "reviewed", "path": "fixture"}]},
    )
    _write_json(
        root / "site/src/data/lexicon-practice-cloze-sources.json",
        [{"lemma": "дім", "sentence": "Я у ___."}],
    )


def test_registry_declares_required_source_families() -> None:
    payload = registry_payload()

    assert tuple(payload["required_source_families"]) == REQUIRED_SOURCE_FAMILIES
    assert {family["id"] for family in payload["families"]} == set(REQUIRED_SOURCE_FAMILIES)
    for family in REQUIRED_SOURCE_FAMILIES:
        definition = source_family_definition(family)
        assert definition.default_extraction_modes
        assert "surface_admission" in definition.surface_admission_policy


def test_inventory_candidates_carry_count_and_frequency(tmp_path: Path) -> None:
    inventory = tmp_path / "sources.yaml"
    inventory.write_text(
        """
version: 1
kind: atlas_source_inventory
sources:
  - id: curriculum-fixture-a
    source_family: curriculum
    extraction_mode: vocabulary_yaml_item
    title: Fixture A
    headwords:
      - lemma: авто
        pos: noun
        gloss: car
        locator: vocabulary[0]
        count: 3
  - id: curriculum-fixture-b
    source_family: curriculum
    extraction_mode: vocabulary_yaml_item
    title: Fixture B
    headwords:
      - lemma: авто́
        pos: noun
        gloss: car
        locator: vocabulary[1]
        frequency: 2
""".lstrip(),
        encoding="utf-8",
    )

    records = read_source_inventory(inventory, project_root=tmp_path)
    candidates = source_inventory_candidates(records)

    assert [record.count for record in records] == [3, 2]
    assert len(candidates) == 1
    assert candidates[0].lemma == "авто"
    assert candidates[0].source_count == 2
    assert candidates[0].frequency == 5
    assert [row["count"] for row in candidates[0].source_provenance] == [3, 2]


def test_gate_contract_emits_three_classifications(tmp_path: Path) -> None:
    inventory = tmp_path / "sources.yaml"
    inventory.write_text(
        """
version: 1
kind: atlas_source_inventory
sources:
  - id: curriculum-ok
    source_family: curriculum
    extraction_mode: vocabulary_yaml_item
    title: Fixture
    headwords:
      - lemma: авто
        pos: noun
        gloss: car
        locator: vocabulary[0]
      - lemma: безглос
        pos: noun
        locator: vocabulary[1]
  - id: unknown-family
    source_family: ulp
    extraction_mode: curated_headword
    title: Fixture
    headwords:
      - lemma: ревю
        pos: noun
        gloss: revue
        locator: row 1
""".lstrip(),
        encoding="utf-8",
    )
    candidates = source_inventory_candidates(read_source_inventory(inventory, project_root=tmp_path))

    results = classify_candidates(candidates)
    by_lemma = {result.lemma: result for result in results}

    assert classification_counts(results) == {
        CLASSIFICATION_AUTO_APPROVE: 1,
        CLASSIFICATION_REVIEW_QUEUE: 1,
        CLASSIFICATION_REJECT: 1,
    }
    auto_payload = by_lemma["авто"].candidate_payload()
    assert auto_payload["classification"] == CLASSIFICATION_AUTO_APPROVE
    assert auto_payload["source_family"] == "curriculum"
    assert auto_payload["source_ids"] == ["curriculum-ok"]
    assert auto_payload["locators"] == ["vocabulary[0]"]
    assert auto_payload["count"] == 1
    assert auto_payload["frequency"] == 1
    assert by_lemma["безглос"].classification == CLASSIFICATION_REVIEW_QUEUE
    assert by_lemma["безглос"].gate_evidence["reasons"] == ["missing_english_anchor"]
    assert by_lemma["ревю"].classification == CLASSIFICATION_REJECT
    assert by_lemma["ревю"].gate_evidence["reasons"] == ["unknown_source_family:ulp"]


def test_gate_frequency_fallback_counts_missing_count_as_one() -> None:
    candidate = SourceInventoryCandidate(
        lemma="частота",
        pos="noun",
        gloss="frequency",
        source_provenance=(
            {
                "source_family": "curriculum",
                "source_id": "source-a",
                "source_locator": "row 1",
            },
            {
                "source_family": "curriculum",
                "source_id": "source-b",
                "source_locator": "row 2",
                "count": 3,
            },
        ),
        source_count=2,
        frequency=0,
    )

    result = classify_candidate(candidate)

    assert result.candidate_payload()["frequency"] == 4


def test_census_reports_safe_counts_without_raw_text(tmp_path: Path) -> None:
    inventory = tmp_path / "sources.yaml"
    inventory.write_text(
        """
version: 1
kind: atlas_source_inventory
sources:
  - id: curriculum-fixture
    source_family: curriculum
    extraction_mode: vocabulary_yaml_item
    title: Fixture Curriculum
    locator: vocabulary
    headwords:
      - lemma: секретне-слово
        pos: noun
        gloss: secret fixture gloss
        locator: vocabulary[0]
        context: PRIVATE RAW CONTEXT
  - id: teacher-fixture
    source_family: teacher_lesson
    extraction_mode: curated_headword
    title: Neutral Teacher Fixture
    locator: table 1
    headwords:
      - lemma: учительське
        pos: adjective
        gloss: teacher fixture
        locator: row 1
  - id: textbook-fixture
    source_family: textbook
    extraction_mode: headword_inventory
    title: Textbook Fixture
    locator: page 1
    headwords:
      - lemma: підручник
        pos: noun
        gloss: textbook
        locator: page 1
  - id: ohoiko-fixture
    source_family: ohoiko
    extraction_mode: curated_headword
    title: Ohoiko Fixture
    locator: unit 1
    headwords:
      - lemma: абетка
        pos: noun
        gloss: alphabet
        locator: unit 1
""".lstrip(),
        encoding="utf-8",
    )

    census = build_census([inventory], project_root=tmp_path)
    serialized = json.dumps(census, ensure_ascii=False)

    assert census["counts"]["inventory_files"] == 1
    assert census["counts"]["source_units"] == 4
    assert census["counts"]["source_rows"] == 4
    assert set(census["by_family"]) == set(REQUIRED_SOURCE_FAMILIES)
    assert census["safety"]["raw_text_included"] is False
    assert "секретне-слово" not in serialized
    assert "secret fixture gloss" not in serialized
    assert "PRIVATE RAW CONTEXT" not in serialized


def test_freeze_snapshot_compares_daily_practice_and_cloze_surfaces(tmp_path: Path) -> None:
    _write_minimal_freeze_surface(tmp_path)
    before = build_surface_snapshot(tmp_path)
    after = build_surface_snapshot(tmp_path)

    assert before["surfaces"]["daily"]["count"] == 1
    assert before["surfaces"]["practice"]["lexeme_count"] == 2
    assert before["surfaces"]["cloze"]["source_count"] == 1
    assert compare_snapshots(before, after)["ok"] is True

    _write_json(
        tmp_path / "site/src/data/lexicon-daily-pool.json",
        [
            {"lemma": "дім", "slug": "дім", "gloss": "house", "k": "vyv", "cefr": "A1"},
            {"lemma": "сад", "slug": "сад", "gloss": "garden", "k": "vyv", "cefr": "A1"},
        ],
    )
    changed = compare_snapshots(before, build_surface_snapshot(tmp_path))

    assert changed["ok"] is False
    assert any(diff.startswith("surfaces.daily") for diff in changed["diffs"])
