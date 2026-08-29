"""Tests for the #6371 textbook leftover residual census."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from scripts.lexicon.build_data_manifest import _lemma_key
from scripts.lexicon.census_atlas_6371_textbook_leftover import (
    CENSUS_ID,
    NAMED_DECISIONS,
    NAMED_INVENTORIES,
    ONESHOT_DECISIONS,
    ONESHOT_INVENTORY,
    admission_allowed_keys,
    build_census,
    is_learner_english,
    iter_manifest_lemmas_from_text,
    iter_yaml_list_maps,
    refuse_invented_lemmas,
    render_report,
)

FIXTURE_INVENTORY = """
version: 1
kind: atlas_source_inventory
sources:
- id: fixture-textbook
  source_family: textbook
  extraction_mode: curated_headword
  title: Fixture textbook leftover list
  path: docs/l2-uk-direct/textbook-map.yaml
  locator: fixture
  headwords:
  - lemma: мама
    pos: noun
    gloss: mother
    locator: family[0]
    context: Fixture named leftover.
  - lemma: крейда
    pos: noun
    locator: school[0]
    context: Fixture named leftover without a gloss.
"""

FIXTURE_NAMED_DECISIONS = {
    "version": 1,
    "kind": "atlas_source_inventory_review_decisions",
    "batch_id": "fixture-named",
    "batch_label": "fixture",
    "reviewer": "test",
    "reviewed_at": "2026-08-29",
    "source_queue": {
        "workflow": "source_inventory_publish_review_queue.v1",
        "total_queue_rows": 2,
        "approved_in_queue": 2,
        "promotion_batch_size": 2,
    },
    "production_outputs_updated": [],
    "decisions": [
        {
            "lemma": "мама",
            "decision": "approve_for_publish",
            "approved_pos": "noun",
            "approved_gloss": "mother",
            "sense_note": "fixture",
            "source_inventory": {
                "key": "fixture-mama",
                "path": "named.yaml",
                "locator": "family[0]",
                "source_id": "fixture-textbook",
                "source_family": "textbook",
            },
            "evidence_refs": ["fixture"],
        },
        {
            "lemma": "крейда",
            "decision": "approve_for_publish",
            "approved_pos": "noun",
            "approved_gloss": "Уживається як шкільне слово.",
            "sense_note": "fixture SUM-11 dump, not teacher P1",
            "source_inventory": {
                "key": "fixture-krejda",
                "path": "named.yaml",
                "locator": "school[0]",
                "source_id": "fixture-textbook",
                "source_family": "textbook",
            },
            "evidence_refs": ["fixture"],
        },
    ],
}

ONESHOT_FIXTURE = """
version: 1
kind: atlas_source_inventory
sources:
- id: textbook-jsonl-curated-fixture
  source_family: textbook
  extraction_mode: curated_bulk
  title: Fixture oneshot
  headwords:
  - lemma: на
    pos: interjection
    gloss: 'Уживається із знах. і місц. відмінками. Сполучення з прийм. на виражають:
      Просторові відношення'
    locator: grade-1::s0001
    context: Curated school-textbook inventory (JSONL/token mine)
"""

ONESHOT_DECISION_FIXTURE = """
version: 1
kind: atlas_source_inventory_review_decisions
decisions:
- lemma: на
  decision: approve_for_publish
  approved_pos: interjection
  approved_gloss: 'Уживається із знах. і місц. відмінками. Сполучення з прийм. на виражають:
    Просторові відношення'
  source_inventory:
    key: fixture-na
    path: oneshot.yaml
    locator: grade-1::s0001
  evidence_refs:
  - curated source family textbook
  - VESUM POS + SUM11 gloss
"""


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _census_fixture(tmp_path: Path, *, atlas_lemmas: list[str] | None = None) -> tuple[Path, object]:
    named_inv = _write(tmp_path / "named.yaml", FIXTURE_INVENTORY)
    named_dec = tmp_path / "named-decisions.yaml"
    named_dec.write_text(yaml.safe_dump(FIXTURE_NAMED_DECISIONS, allow_unicode=True), encoding="utf-8")
    oneshot_inv = _write(tmp_path / "oneshot.yaml", ONESHOT_FIXTURE)
    oneshot_dec = _write(tmp_path / "oneshot-decisions.yaml", ONESHOT_DECISION_FIXTURE)
    manifest = None
    if atlas_lemmas is not None:
        manifest = tmp_path / "manifest.json"
        manifest.write_text(
            json.dumps({"entries": [{"lemma": lemma} for lemma in atlas_lemmas]}, ensure_ascii=False),
            encoding="utf-8",
        )
    census = build_census(
        project_root=tmp_path,
        oneshot_inventory=oneshot_inv,
        oneshot_decisions=oneshot_dec,
        named_inventories=[named_inv],
        named_decisions=[named_dec],
        manifest_path=manifest,
        pointer_path=tmp_path / "missing-pointer.json",
        vesum_path=tmp_path / "vesum.db",
        sources_path=tmp_path / "sources.db",
        allow_download=False,
    )
    return tmp_path, census


def test_learner_english_matches_teacher_p1_bar() -> None:
    assert is_learner_english("mother")
    assert is_learner_english("father; dad")
    assert is_learner_english("Ukraine")
    assert not is_learner_english("Уживається перед присудком")
    assert not is_learner_english("mother мама")
    assert not is_learner_english("gloss pending")
    assert not is_learner_english("")
    assert not is_learner_english(None)


def test_iter_yaml_list_maps_joins_folded_gloss(tmp_path: Path) -> None:
    path = _write(tmp_path / "oneshot.yaml", ONESHOT_FIXTURE)
    rows = list(iter_yaml_list_maps(path, item_indent=2))
    assert [row["lemma"] for row in rows] == ["на"]
    assert "Уживається" in rows[0]["gloss"]
    assert "Просторові" in rows[0]["gloss"]


def test_iter_yaml_list_maps_skips_nested_evidence_refs(tmp_path: Path) -> None:
    path = _write(tmp_path / "decisions.yaml", ONESHOT_DECISION_FIXTURE)
    rows = list(iter_yaml_list_maps(path, item_indent=0))
    assert [row["lemma"] for row in rows] == ["на"]
    assert rows[0]["decision"] == "approve_for_publish"
    assert "curated source family textbook" not in rows[0].get("lemma", "")


def test_iter_manifest_lemmas_from_text_unescapes() -> None:
    lemmas = list(iter_manifest_lemmas_from_text('{"entries":[{"lemma":"кам\'яниця"},{"lemma":"ліс"}]}'))
    assert lemmas == ["кам'яниця", "ліс"]


def test_iter_manifest_lemmas_ignores_nested_pretty_printed_lemmas() -> None:
    text = """{
  "stats": {
    "lemmas_total": 2,
    "entries": 2
  },
  "samples": [
    {
      "lemmas": [
        "всьо",
        "діюча"
      ]
    }
  ],
  "entries": [
    {
      "lemma": "мама",
      "enrichment": {
        "related": [
          {"lemma": "тато"}
        ]
      }
    },
    {
      "lemma": "ліс"
    }
  ]
}
"""
    assert list(iter_manifest_lemmas_from_text(text)) == ["мама", "ліс"]


def test_census_marks_missing_dbs_as_blockers(tmp_path: Path) -> None:
    _, census = _census_fixture(tmp_path, atlas_lemmas=["мама"])
    assert census.census_id == CENSUS_ID
    assert "data/vesum.db" in census.blockers
    assert "data/sources.db" in census.blockers
    assert census.admission["refused"] is True
    assert "data/vesum.db" in census.admission["refuse_reason"]
    assert "data/sources.db" in census.admission["refuse_reason"]
    assert "no named teacher-P1 leftovers" in census.admission["refuse_reason"]
    assert census.admission["admitted_this_run"] == []


def test_oneshot_sum11_gloss_is_not_teacher_p1_eligible(tmp_path: Path) -> None:
    _, census = _census_fixture(tmp_path, atlas_lemmas=[])
    assert census.oneshot["approved_decisions"] == 1
    assert census.oneshot["approved_english_gloss_rows"] == 0
    assert census.oneshot["teacher_p1_eligible_count"] == 0
    assert census.oneshot["missing_from_atlas"] == 1
    assert census.oneshot["missing_lemmas"] == ["на"]


def test_named_english_leftover_is_teacher_p1_and_sum11_is_not(tmp_path: Path) -> None:
    _, census = _census_fixture(tmp_path, atlas_lemmas=[])
    assert census.named["approved_decisions"] == 2
    assert census.named["approved_english_gloss_rows"] == 1
    assert census.named["teacher_p1_missing_from_atlas"] == ["мама"]
    assert "крейда" not in census.named["teacher_p1_missing_from_atlas"]
    assert census.admission["named_teacher_p1_missing"] == ["мама"]


def test_named_leftover_already_in_atlas_is_not_admitted(tmp_path: Path) -> None:
    _, census = _census_fixture(tmp_path, atlas_lemmas=["мама", "крейда", "на"])
    assert census.named["missing_from_atlas"] == 0
    assert census.named["teacher_p1_missing_from_atlas"] == []
    assert census.admission["named_teacher_p1_missing"] == []
    assert census.admission["admitted_this_run"] == []


def test_refuse_invented_lemmas() -> None:
    allowed = {_lemma_key("мама")}
    refuse_invented_lemmas(["мама"], allowed)
    try:
        refuse_invented_lemmas(["вигаданеслово"], allowed)
    except ValueError as exc:
        assert "вигаданеслово" in str(exc)
    else:
        raise AssertionError("invented lemma must be refused")


def test_admission_allowed_keys_are_only_named_teacher_p1(tmp_path: Path) -> None:
    _, census = _census_fixture(tmp_path, atlas_lemmas=[])
    allowed = admission_allowed_keys(census)
    assert allowed == {_lemma_key("мама")}
    refuse_invented_lemmas(["мама"], allowed)
    try:
        refuse_invented_lemmas(["на"], allowed)
    except ValueError as exc:
        assert "на" in str(exc)
    else:
        raise AssertionError("oneshot SUM-11 leftover must not be admission-eligible")


def test_render_report_names_exact_missing_dbs(tmp_path: Path) -> None:
    _, census = _census_fixture(tmp_path, atlas_lemmas=["мама"])
    rendered = render_report(census)
    assert "data/vesum.db" in rendered
    assert "data/sources.db" in rendered
    assert "BLOCKED" in rendered
    assert "Issue #6371 stays open" in rendered


def test_committed_oneshot_and_named_leftover_paths_exist() -> None:
    assert ONESHOT_INVENTORY.is_file()
    assert ONESHOT_DECISIONS.is_file()
    for path in NAMED_INVENTORIES:
        assert path.is_file(), path
    for path in NAMED_DECISIONS:
        assert path.is_file(), path


def test_committed_oneshot_stream_matches_published_denominator() -> None:
    """Lock the honest #6371 oneshot denominator without a full YAML object graph."""
    from scripts.lexicon.census_atlas_6371_textbook_leftover import (
        load_oneshot_decisions,
        load_oneshot_inventory_rows,
        load_named_decisions,
        load_named_inventory_rows,
    )

    inventory = load_oneshot_inventory_rows()
    decisions = load_oneshot_decisions()
    assert len(inventory) == 24682
    assert len(decisions) == 24682
    assert {row.decision for row in decisions} == {"approve_for_publish"}
    assert sum(1 for row in decisions if is_learner_english(row.approved_gloss)) == 0

    named_inventory = load_named_inventory_rows()
    named_decisions = load_named_decisions()
    assert len(named_inventory) == 114
    assert len(named_decisions) == 91
    assert {row.decision for row in named_decisions} == {"approve_for_publish"}
    assert sum(1 for row in named_decisions if is_learner_english(row.approved_gloss)) == 91
