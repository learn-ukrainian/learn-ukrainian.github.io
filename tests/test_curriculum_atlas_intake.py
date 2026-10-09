from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.audit.source_inventory_intake import read_source_inventory
from scripts.audit.source_inventory_review_decisions import validate_decision_file
from scripts.lexicon import curriculum_atlas_intake as intake

pytestmark = pytest.mark.reads_content


def write_fixture_curriculum(root: Path) -> Path:
    curriculum = root / "curriculum" / "l2-uk-en"
    module = curriculum / "a1" / "fixture" / "module.md"
    module.parent.mkdir(parents=True)
    module.write_text("# Урок\n\nКіт читає. Мати тут.\n", encoding="utf-8")

    activities = curriculum / "a1" / "activities" / "fixture.yaml"
    activities.parent.mkdir(parents=True)
    activities.write_text(
        "instruction: Виберіть слово\nitems:\n  - answer: Мати\n",
        encoding="utf-8",
    )

    vocabulary = curriculum / "a1" / "vocabulary" / "fixture.yaml"
    vocabulary.parent.mkdir(parents=True)
    vocabulary.write_text(
        "vocabulary:\n"
        "  - word: Авто\n"
        "    translation: car\n"
        "    pos: ім.\n"
        "  - word: Дубль\n"
        "    translation: duplicate\n"
        "    pos: ім.\n",
        encoding="utf-8",
    )
    return curriculum


def fake_vesum(forms: list[str]) -> dict[str, list[dict[str, str]]]:
    rows = {
        "авто": [{"lemma": "авто", "pos": "noun"}],
        "дубль": [{"lemma": "дубль", "pos": "noun"}],
        "кіт": [{"lemma": "кіт", "pos": "noun"}],
        "читає": [{"lemma": "читати", "pos": "verb"}],
        "тут": [{"lemma": "тут", "pos": "adv"}],
        "виберіть": [{"lemma": "вибрати", "pos": "verb"}],
        "слово": [{"lemma": "слово", "pos": "noun"}],
        "мати": [
            {"lemma": "мати", "pos": "noun"},
            {"lemma": "мати", "pos": "verb"},
        ],
    }
    return {form: rows.get(form, []) for form in forms}


def clear_heritage(lemma: str) -> dict[str, object]:
    return {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "vesum_attested": True,
        "sovietization_risk": 0,
    }


def test_discovers_all_sources_and_classifies_fail_closed(tmp_path: Path) -> None:
    curriculum = write_fixture_curriculum(tmp_path)

    result = intake.build_curriculum_intake(
        curriculum_root=curriculum,
        project_root=tmp_path,
        manifest_lemma_keys={"кіт"},
        existing_ledger_keys={"дубль"},
        vesum_lookup=fake_vesum,
        heritage_lookup=clear_heritage,
        inventory_path="fixture-inventory.yaml",
    )

    assert result.source_counts == {"module": 1, "activity": 1, "vocabulary": 1}
    assert [source.relative_path for source in result.sources] == [
        "curriculum/l2-uk-en/a1/activities/fixture.yaml",
        "curriculum/l2-uk-en/a1/fixture/module.md",
        "curriculum/l2-uk-en/a1/vocabulary/fixture.yaml",
    ]
    by_lemma = {candidate.lemma: candidate for candidate in result.candidates}
    assert by_lemma["авто"].classification == "auto_approve"
    assert by_lemma["авто"].reasons == (
        "vesum_unique_lemma_pos",
        "explicit_english_anchor",
        "heritage_clear",
    )
    assert by_lemma["кіт"].classification == "reject"
    assert by_lemma["кіт"].reasons == ("already_in_atlas",)
    assert by_lemma["дубль"].classification == "reject"
    assert by_lemma["дубль"].reasons == ("already_in_existing_ledger",)
    assert by_lemma["мати"].classification == "review_queue"
    assert by_lemma["мати"].reasons == ("vesum_ambiguous_pos",)
    assert by_lemma["читати"].classification == "review_queue"
    assert by_lemma["читати"].reasons == ("missing_english_anchor",)
    assert result.classification_counts == {"auto_approve": 1, "review_queue": 6, "reject": 2}


def test_discovers_module_centric_and_legacy_activity_vocabulary_paths(tmp_path: Path) -> None:
    curriculum = write_fixture_curriculum(tmp_path)
    current = curriculum / "a1" / "current"
    current.mkdir()
    (current / "activities.yaml").write_text("instruction: Читайте.\n", encoding="utf-8")
    (current / "vocabulary.yaml").write_text(
        "- lemma: читати\n  translation: to read\n  pos: verb\n",
        encoding="utf-8",
    )

    sources = intake.discover_curriculum_sources(curriculum, project_root=tmp_path)

    assert {source.relative_path for source in sources} >= {
        "curriculum/l2-uk-en/a1/current/activities.yaml",
        "curriculum/l2-uk-en/a1/current/vocabulary.yaml",
        "curriculum/l2-uk-en/a1/activities/fixture.yaml",
        "curriculum/l2-uk-en/a1/vocabulary/fixture.yaml",
    }


def test_module_centric_lemma_vocabulary_is_an_explicit_english_anchor(tmp_path: Path) -> None:
    curriculum = tmp_path / "curriculum" / "l2-uk-en"
    vocabulary = curriculum / "a1" / "current" / "vocabulary.yaml"
    vocabulary.parent.mkdir(parents=True)
    vocabulary.write_text(
        "- lemma: авто\n  translation: car\n  pos: noun\n",
        encoding="utf-8",
    )

    result = intake.build_curriculum_intake(
        curriculum_root=curriculum,
        project_root=tmp_path,
        manifest_lemma_keys=set(),
        existing_ledger_keys=set(),
        vesum_lookup=fake_vesum,
        heritage_lookup=clear_heritage,
    )

    assert result.classification_counts == {"auto_approve": 1, "review_queue": 0, "reject": 0}
    assert result.candidates[0].gloss == "car"


def test_merges_colliding_unresolved_surface_into_review_queue(tmp_path: Path) -> None:
    curriculum = tmp_path / "curriculum" / "l2-uk-en"
    module = curriculum / "a1" / "collision" / "module.md"
    module.parent.mkdir(parents=True)
    module.write_text("Десяток десятка.\n", encoding="utf-8")

    def collision_vesum(forms: list[str]) -> dict[str, list[dict[str, str]]]:
        rows = {
            "десяток": [],
            "десятка": [{"lemma": "десяток", "pos": "noun"}],
        }
        return {form: rows.get(form, []) for form in forms}

    result = intake.build_curriculum_intake(
        curriculum_root=curriculum,
        project_root=tmp_path,
        manifest_lemma_keys=set(),
        existing_ledger_keys=set(),
        vesum_lookup=collision_vesum,
        heritage_lookup=clear_heritage,
    )

    assert len(result.candidates) == 1
    candidate = result.candidates[0]
    assert candidate.lemma == "десяток"
    assert candidate.classification == "review_queue"
    assert candidate.frequency == 2
    assert "vesum_unrecognized" in candidate.reasons
    assert "canonical_headword_collision" in candidate.reasons


def test_merges_same_lemma_records_at_a_shared_locator(tmp_path: Path) -> None:
    curriculum = tmp_path / "curriculum" / "l2-uk-en"
    module = curriculum / "a1" / "records" / "module.md"
    module.parent.mkdir(parents=True)
    module.write_text("Читає читати.\n", encoding="utf-8")

    def shared_lemma_vesum(forms: list[str]) -> dict[str, list[dict[str, str]]]:
        rows = {
            "читає": [{"lemma": "читати", "pos": "verb"}],
            "читати": [{"lemma": "читати", "pos": "verb"}],
        }
        return {form: rows.get(form, []) for form in forms}

    result = intake.build_curriculum_intake(
        curriculum_root=curriculum,
        project_root=tmp_path,
        manifest_lemma_keys=set(),
        existing_ledger_keys=set(),
        vesum_lookup=shared_lemma_vesum,
        heritage_lookup=clear_heritage,
    )

    candidate = result.candidates[0]
    assert candidate.lemma == "читати"
    assert candidate.frequency == 2
    assert len(candidate.records) == 1


def test_exact_ledger_collision_remains_rejected(tmp_path: Path) -> None:
    curriculum = tmp_path / "curriculum" / "l2-uk-en"
    module = curriculum / "a1" / "collision" / "module.md"
    module.parent.mkdir(parents=True)
    module.write_text("Десяток десятка.\n", encoding="utf-8")

    def collision_vesum(forms: list[str]) -> dict[str, list[dict[str, str]]]:
        rows = {
            "десяток": [],
            "десятка": [{"lemma": "десяток", "pos": "noun"}],
        }
        return {form: rows.get(form, []) for form in forms}

    result = intake.build_curriculum_intake(
        curriculum_root=curriculum,
        project_root=tmp_path,
        manifest_lemma_keys=set(),
        existing_ledger_keys={"десяток"},
        vesum_lookup=collision_vesum,
        heritage_lookup=clear_heritage,
    )

    candidate = result.candidates[0]
    assert candidate.classification == "reject"
    assert "already_in_existing_ledger" in candidate.reasons
    assert "vesum_unrecognized" in candidate.reasons


def test_writes_parser_compatible_inventory_and_decision_ledger(tmp_path: Path) -> None:
    curriculum = write_fixture_curriculum(tmp_path)
    inventory_path = "data/lexicon/source-inventory/fixture-inventory.json"
    inventory_out = tmp_path / inventory_path
    ledger_out = tmp_path / "fixture-ledger.yaml"
    result = intake.build_curriculum_intake(
        curriculum_root=curriculum,
        project_root=tmp_path,
        manifest_lemma_keys=set(),
        existing_ledger_keys=set(),
        vesum_lookup=fake_vesum,
        heritage_lookup=clear_heritage,
        inventory_path=inventory_path,
    )

    intake.assert_ledger_inventory_destination(inventory_out, inventory_path, project_root=tmp_path)
    intake.write_flat_source_inventory(result, inventory_out)
    ledger = intake.build_ledger_append_payload(
        result,
        batch_id="curriculum-fixture-intake",
        batch_label="curriculum fixture full-text intake",
        reviewed_at="2026-07-14",
        inventory_path=inventory_path,
    )
    intake.write_yaml_payload(ledger, ledger_out)

    records = read_source_inventory(inventory_out, project_root=tmp_path)
    source_index = {(record.lemma, record.inventory_path, record.source_locator): record for record in records}
    summary = validate_decision_file(ledger_out, source_index=source_index)

    assert summary["rows"] == len(result.candidates)
    assert ledger["production_outputs_updated"] == []
    assert all("surface_admission" not in row for row in ledger["decisions"])
    auto_row = next(row for row in ledger["decisions"] if row["lemma"] == "авто")
    assert auto_row["decision"] == "approve_for_publish"
    assert auto_row["approved_pos"] == "noun"
    assert auto_row["approved_gloss"] == "car"
    review_row = next(row for row in ledger["decisions"] if row["lemma"] == "мати")
    assert review_row["decision"] == "needs_more_evidence"
    assert review_row["review_queue_reasons"] == ["vesum_ambiguous_pos"]


def test_invalid_yaml_fails_closed(tmp_path: Path) -> None:
    curriculum = tmp_path / "curriculum" / "l2-uk-en"
    broken = curriculum / "a1" / "activities" / "broken.yaml"
    broken.parent.mkdir(parents=True)
    broken.write_text("instruction: [not closed\n", encoding="utf-8")

    with pytest.raises(intake.CurriculumIntakeError, match="invalid curriculum YAML"):
        intake.build_curriculum_intake(
            curriculum_root=curriculum,
            project_root=tmp_path,
            manifest_lemma_keys=set(),
            existing_ledger_keys=set(),
            vesum_lookup=fake_vesum,
            heritage_lookup=clear_heritage,
        )


def test_empty_yaml_is_skipped_without_blocking_other_curriculum_sources(tmp_path: Path) -> None:
    curriculum = tmp_path / "curriculum" / "l2-uk-en"
    vocabulary = curriculum / "a1" / "current" / "vocabulary.yaml"
    vocabulary.parent.mkdir(parents=True)
    vocabulary.write_text("# intentionally empty\n", encoding="utf-8")
    module = curriculum / "a1" / "current" / "module.md"
    module.write_text("Кіт.\n", encoding="utf-8")

    result = intake.build_curriculum_intake(
        curriculum_root=curriculum,
        project_root=tmp_path,
        manifest_lemma_keys=set(),
        existing_ledger_keys=set(),
        vesum_lookup=fake_vesum,
        heritage_lookup=clear_heritage,
    )

    assert [candidate.lemma for candidate in result.candidates] == ["кіт"]


def test_yaml_occurrences_keep_their_structural_safe_locators(tmp_path: Path) -> None:
    curriculum = tmp_path / "curriculum" / "l2-uk-en"
    activities = curriculum / "a1" / "activities" / "locators.yaml"
    activities.parent.mkdir(parents=True)
    activities.write_text("instruction: Читайте\nitems:\n  - answer: Слухайте\n", encoding="utf-8")

    def locator_vesum(forms: list[str]) -> dict[str, list[dict[str, str]]]:
        rows = {
            "читайте": [{"lemma": "читати", "pos": "verb"}],
            "слухайте": [{"lemma": "слухати", "pos": "verb"}],
        }
        return {form: rows.get(form, []) for form in forms}

    result = intake.build_curriculum_intake(
        curriculum_root=curriculum,
        project_root=tmp_path,
        manifest_lemma_keys=set(),
        existing_ledger_keys=set(),
        vesum_lookup=locator_vesum,
        heritage_lookup=clear_heritage,
    )

    locators = {record.source_locator for candidate in result.candidates for record in candidate.records}
    assert locators == {
        "curriculum/l2-uk-en/a1/activities/locators.yaml::instruction",
        "curriculum/l2-uk-en/a1/activities/locators.yaml::items[0].answer",
    }


def test_ukrainian_type_text_is_not_skipped_from_full_text_intake(tmp_path: Path) -> None:
    curriculum = tmp_path / "curriculum" / "l2-uk-en"
    activities = curriculum / "a1" / "activities" / "type.yaml"
    activities.parent.mkdir(parents=True)
    activities.write_text("type: етнографічний запис\n", encoding="utf-8")

    def type_vesum(forms: list[str]) -> dict[str, list[dict[str, str]]]:
        rows = {
            "етнографічний": [{"lemma": "етнографічний", "pos": "adjective"}],
            "запис": [{"lemma": "запис", "pos": "noun"}],
        }
        return {form: rows.get(form, []) for form in forms}

    result = intake.build_curriculum_intake(
        curriculum_root=curriculum,
        project_root=tmp_path,
        manifest_lemma_keys=set(),
        existing_ledger_keys=set(),
        vesum_lookup=type_vesum,
        heritage_lookup=clear_heritage,
    )

    assert {candidate.lemma for candidate in result.candidates} == {"етнографічний", "запис"}


def test_explicit_manifest_uses_the_canonical_atlas_key_normalizer(tmp_path: Path) -> None:
    manifest = tmp_path / "atlas.json"
    manifest.write_text('{"entries": [{"lemma": "Кіт,"}]}\n', encoding="utf-8")

    assert intake.load_atlas_lemma_keys(manifest) == {"кіт"}


def test_cli_rejects_ledger_output_outside_the_source_inventory_directory(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TMPDIR", raising=False)
    result = intake.main(
        [
            "--ledger-out",
            str(tmp_path / "ledger.yaml"),
            "--batch-id",
            "fixture",
            "--batch-label",
            "fixture",
            "--reviewed-at",
            "2026-07-14",
            "--inventory-out",
            str(intake.PROJECT_ROOT / "batch_state" / "cli-fixture-inventory.json"),
            "--report-out",
            str(tmp_path / "report.json"),
            "--inventory-path",
            "batch_state/cli-fixture-inventory.json",
        ]
    )

    assert result == 2
    assert "data/lexicon/source-inventory" in capsys.readouterr().err
    assert not (tmp_path / "report.json").exists()
    assert not (tmp_path / "ledger.yaml").exists()


def test_existing_ledger_keys_ignores_unreviewed_inventory(tmp_path: Path) -> None:
    inventory_dir = tmp_path / "data" / "lexicon" / "source-inventory"
    inventory_dir.mkdir(parents=True)
    (inventory_dir / "prior-intake.json").write_text("[]\n", encoding="utf-8")
    decisions_dir = tmp_path / "registry" / "lexicon" / "source-inventory-review-decisions"
    decisions_dir.mkdir(parents=True)
    (decisions_dir / "prior-decisions.yaml").write_text(
        "version: 1\n"
        "kind: atlas_source_inventory_review_decisions\n"
        "decisions:\n"
        "  - lemma: кіт\n"
        "    decision: needs_more_evidence\n",
        encoding="utf-8",
    )

    assert intake.load_existing_ledger_keys(project_root=tmp_path) == {"кіт"}


def test_ledger_inventory_destination_must_match_metadata_path(tmp_path: Path) -> None:
    inventory_out = tmp_path / "data" / "lexicon" / "source-inventory" / "fixture.json"

    with pytest.raises(intake.CurriculumIntakeError, match="--inventory-path"):
        intake.assert_ledger_inventory_destination(
            inventory_out,
            "data/lexicon/source-inventory/different.json",
            project_root=tmp_path,
        )

    with pytest.raises(intake.CurriculumIntakeError, match="data/lexicon/source-inventory"):
        intake.assert_ledger_inventory_destination(
            tmp_path / "batch_state" / "fixture.json",
            "batch_state/fixture.json",
            project_root=tmp_path,
        )


def test_word_and_lemma_share_translation_only_with_canonical_lemma(tmp_path: Path) -> None:
    curriculum = tmp_path / "curriculum" / "l2-uk-en"
    vocabulary = curriculum / "a1" / "current" / "vocabulary.yaml"
    vocabulary.parent.mkdir(parents=True)
    vocabulary.write_text(
        "- word: привіт\n  lemma: вітати\n  translation: to greet\n",
        encoding="utf-8",
    )

    def word_and_lemma_vesum(forms: list[str]) -> dict[str, list[dict[str, str]]]:
        rows = {
            "привіт": [{"lemma": "привіт", "pos": "noun"}],
            "вітати": [{"lemma": "вітати", "pos": "verb"}],
        }
        return {form: rows.get(form, []) for form in forms}

    result = intake.build_curriculum_intake(
        curriculum_root=curriculum,
        project_root=tmp_path,
        manifest_lemma_keys=set(),
        existing_ledger_keys=set(),
        vesum_lookup=word_and_lemma_vesum,
        heritage_lookup=clear_heritage,
    )

    by_lemma = {candidate.lemma: candidate for candidate in result.candidates}
    assert by_lemma["вітати"].classification == "auto_approve"
    assert by_lemma["привіт"].classification == "review_queue"
    assert by_lemma["привіт"].reasons == ("missing_english_anchor",)


def test_multiword_headword_does_not_auto_approve_its_component_words(tmp_path: Path) -> None:
    curriculum = tmp_path / "curriculum" / "l2-uk-en"
    vocabulary = curriculum / "a1" / "current" / "vocabulary.yaml"
    vocabulary.parent.mkdir(parents=True)
    vocabulary.write_text("- word: будь ласка\n  translation: please\n", encoding="utf-8")

    def phrase_vesum(forms: list[str]) -> dict[str, list[dict[str, str]]]:
        rows = {
            "будь": [{"lemma": "бути", "pos": "verb"}],
            "ласка": [{"lemma": "ласка", "pos": "noun"}],
        }
        return {form: rows.get(form, []) for form in forms}

    result = intake.build_curriculum_intake(
        curriculum_root=curriculum,
        project_root=tmp_path,
        manifest_lemma_keys=set(),
        existing_ledger_keys=set(),
        vesum_lookup=phrase_vesum,
        heritage_lookup=clear_heritage,
    )

    assert result.classification_counts == {"auto_approve": 0, "review_queue": 2, "reject": 0}
    assert all(candidate.reasons == ("missing_english_anchor",) for candidate in result.candidates)


def test_translation_metadata_is_not_reingested_as_curriculum_text(tmp_path: Path) -> None:
    curriculum = tmp_path / "curriculum" / "l2-uk-en"
    vocabulary = curriculum / "a1" / "current" / "vocabulary.yaml"
    vocabulary.parent.mkdir(parents=True)
    vocabulary.write_text("- word: авто\n  translation: car (автівка)\n", encoding="utf-8")

    def metadata_vesum(forms: list[str]) -> dict[str, list[dict[str, str]]]:
        rows = {
            "авто": [{"lemma": "авто", "pos": "noun"}],
            "автівка": [{"lemma": "автівка", "pos": "noun"}],
        }
        return {form: rows.get(form, []) for form in forms}

    result = intake.build_curriculum_intake(
        curriculum_root=curriculum,
        project_root=tmp_path,
        manifest_lemma_keys=set(),
        existing_ledger_keys=set(),
        vesum_lookup=metadata_vesum,
        heritage_lookup=clear_heritage,
    )

    assert [candidate.lemma for candidate in result.candidates] == ["авто"]


def test_case_variant_collision_keeps_valid_distinct_ledger_rows(tmp_path: Path) -> None:
    curriculum = tmp_path / "curriculum" / "l2-uk-en"
    module = curriculum / "a1" / "kyiv" / "module.md"
    module.parent.mkdir(parents=True)
    module.write_text("Київ Києва.\n", encoding="utf-8")
    inventory_path = "data/lexicon/source-inventory/kyiv-fixture.json"
    inventory_out = tmp_path / inventory_path
    ledger_out = tmp_path / "kyiv-ledger.yaml"

    def case_variant_vesum(forms: list[str]) -> dict[str, list[dict[str, str]]]:
        rows = {
            "київ": [],
            "києва": [{"lemma": "Київ", "pos": "noun"}],
        }
        return {form: rows.get(form, []) for form in forms}

    result = intake.build_curriculum_intake(
        curriculum_root=curriculum,
        project_root=tmp_path,
        manifest_lemma_keys=set(),
        existing_ledger_keys=set(),
        vesum_lookup=case_variant_vesum,
        heritage_lookup=clear_heritage,
        inventory_path=inventory_path,
    )

    assert {candidate.lemma for candidate in result.candidates} == {"Київ", "київ"}
    intake.write_flat_source_inventory(result, inventory_out)
    intake.write_yaml_payload(
        intake.build_ledger_append_payload(
            result,
            batch_id="kyiv-fixture-intake",
            batch_label="Kyiv collision fixture",
            reviewed_at="2026-07-14",
            inventory_path=inventory_path,
        ),
        ledger_out,
    )
    records = read_source_inventory(inventory_out, project_root=tmp_path)
    source_index = {(record.lemma, record.inventory_path, record.source_locator): record for record in records}

    assert validate_decision_file(ledger_out, source_index=source_index)["rows"] == 2


def test_heritage_rejection_and_uncertainty_are_fail_closed() -> None:
    common = {
        "lemma": "тест",
        "pos": "noun",
        "gloss": "test",
        "metadata_reasons": (),
        "atlas_keys": set(),
        "ledger_keys": set(),
    }

    reject, reject_reasons, _ = intake.classify_resolved_candidate(
        **common,
        heritage_lookup=lambda _: {"classification": "russianism", "is_russianism": True},
    )
    shadow, shadow_reasons, _ = intake.classify_resolved_candidate(
        **common,
        heritage_lookup=lambda _: {"classification": "standard", "russian_shadow": True},
    )
    failed, failed_reasons, _ = intake.classify_resolved_candidate(
        **common,
        heritage_lookup=lambda _: (_ for _ in ()).throw(RuntimeError("lookup failure")),
    )
    sovietized, sovietized_reasons, _ = intake.classify_resolved_candidate(
        **common,
        heritage_lookup=lambda _: {"classification": "standard", "sovietization_risk": 2},
    )
    borrowing, borrowing_reasons, _ = intake.classify_resolved_candidate(
        **common,
        heritage_lookup=lambda _: {"classification": "borrowing", "sovietization_risk": 0},
    )
    surzhyk, surzhyk_reasons, _ = intake.classify_resolved_candidate(
        **common,
        heritage_lookup=lambda _: {"classification": "surzhyk", "sovietization_risk": 0},
    )

    assert (reject, reject_reasons) == ("reject", ("heritage_russianism",))
    assert (shadow, shadow_reasons) == ("review_queue", ("heritage_russian_shadow",))
    assert (failed, failed_reasons) == ("review_queue", ("heritage_lookup_failed",))
    assert (sovietized, sovietized_reasons) == ("review_queue", ("heritage_sovietization_risk",))
    assert (borrowing, borrowing_reasons) == ("review_queue", ("heritage_nonstandard_classification",))
    assert (surzhyk, surzhyk_reasons) == ("reject", ("heritage_surzhyk",))


def test_default_atlas_loader_is_used_for_deduplication(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    curriculum = tmp_path / "curriculum" / "l2-uk-en"
    vocabulary = curriculum / "a1" / "current" / "vocabulary.yaml"
    vocabulary.parent.mkdir(parents=True)
    vocabulary.write_text("- lemma: авто\n  translation: car\n", encoding="utf-8")
    monkeypatch.setattr(intake, "load_atlas_lemma_keys", lambda: {"авто"})

    result = intake.build_curriculum_intake(
        curriculum_root=curriculum,
        project_root=tmp_path,
        vesum_lookup=fake_vesum,
        heritage_lookup=clear_heritage,
    )

    assert result.candidates[0].classification == "reject"
    assert result.candidates[0].reasons == ("already_in_atlas",)


def test_capitalized_proper_nouns_resolve_to_canonical_lemma() -> None:
    def fake_cap_vesum(forms: list[str]) -> dict[str, list[dict[str, str]]]:
        data = {
            "Олена": [{"lemma": "Олена", "pos": "noun"}],
            "Львів": [{"lemma": "Львів", "pos": "noun"}],
            "Івано-Франківськ": [{"lemma": "Івано-Франківськ", "pos": "noun"}],
        }
        return {form: data.get(form, []) for form in forms}

    resolutions = intake.resolve_forms(["олена", "львів", "івано-франківськ", "невідоме"], vesum_lookup=fake_cap_vesum)
    assert resolutions["олена"].lemma == "Олена"
    assert resolutions["олена"].pos == "noun"
    assert resolutions["олена"].reason is None
    assert resolutions["львів"].lemma == "Львів"
    assert resolutions["львів"].pos == "noun"
    assert resolutions["львів"].reason is None
    assert resolutions["івано-франківськ"].lemma == "Івано-Франківськ"
    assert resolutions["івано-франківськ"].pos == "noun"
    assert resolutions["івано-франківськ"].reason is None
    assert resolutions["невідоме"].lemma is None
    assert resolutions["невідоме"].reason == "vesum_unrecognized"


def test_translated_english_anchor_resolves_missing_gloss(tmp_path: Path) -> None:
    curriculum = tmp_path / "curriculum" / "l2-uk-en"
    module = curriculum / "a1" / "fixture" / "module.md"
    module.parent.mkdir(parents=True)
    module.write_text("# Урок\n\nчитає тут\n", encoding="utf-8")

    def mock_english_lookup(lemma: str) -> str | None:
        return "read" if lemma == "читати" else None

    result = intake.build_curriculum_intake(
        curriculum_root=curriculum,
        project_root=tmp_path,
        manifest_lemma_keys=set(),
        existing_ledger_keys=set(),
        vesum_lookup=fake_vesum,
        heritage_lookup=clear_heritage,
        english_lookup=mock_english_lookup,
    )

    by_lemma = {candidate.lemma: candidate for candidate in result.candidates}
    assert by_lemma["читати"].classification == "auto_approve"
    assert by_lemma["читати"].gloss == "read"
    assert "translated_english_anchor" in by_lemma["читати"].reasons
    assert "vesum_unique_lemma_pos" in by_lemma["читати"].reasons
    assert "heritage_clear" in by_lemma["читати"].reasons


def test_unresolved_form_checks_heritage_lookup(tmp_path: Path) -> None:
    curriculum = tmp_path / "curriculum" / "l2-uk-en"
    module = curriculum / "a1" / "heritage" / "module.md"
    module.parent.mkdir(parents=True)
    module.write_text("# Урок\n\nяти тут\n", encoding="utf-8")

    def vesum_empty(forms: list[str]) -> dict[str, list[dict[str, str]]]:
        return {f: [] for f in forms}

    def mock_heritage(lemma: str) -> dict[str, object]:
        if lemma == "яти":
            return {
                "classification": "standard",
                "attestation": {"source": "grinchenko", "ref": "яти", "detail": "яти - братися"},
                "is_russianism": False,
                "sovietization_risk": 0,
            }
        return {"classification": "unknown"}

    result = intake.build_curriculum_intake(
        curriculum_root=curriculum,
        project_root=tmp_path,
        manifest_lemma_keys=set(),
        existing_ledger_keys=set(),
        vesum_lookup=vesum_empty,
        heritage_lookup=mock_heritage,
        english_lookup=lambda _: "to take / begin",
    )

    by_lemma = {candidate.lemma: candidate for candidate in result.candidates}
    assert "яти" in by_lemma
    assert by_lemma["яти"].classification == "review_queue"
    assert "heritage_attested_non_vesum" in by_lemma["яти"].reasons
    assert by_lemma["яти"].heritage_status is not None
    assert by_lemma["яти"].gloss == "to take / begin"


def test_unresolved_hyphenated_form_checks_capitalized_heritage_lookup(tmp_path: Path) -> None:
    curriculum = tmp_path / "curriculum" / "l2-uk-en"
    module = curriculum / "a1" / "heritage" / "module.md"
    module.parent.mkdir(parents=True)
    module.write_text("# Урок\n\nдівка-бранка тут\n", encoding="utf-8")

    def vesum_empty(forms: list[str]) -> dict[str, list[dict[str, str]]]:
        return {f: [] for f in forms}

    def mock_heritage(lemma: str) -> dict[str, object]:
        if lemma == "Дівка-Бранка":
            return {
                "classification": "authentic-archaism",
                "attestation": {"source": "literary", "ref": "Дівка-Бранка", "detail": "фольклорний епос"},
                "is_russianism": False,
                "sovietization_risk": 0,
            }
        return {"classification": "unknown"}

    result = intake.build_curriculum_intake(
        curriculum_root=curriculum,
        project_root=tmp_path,
        manifest_lemma_keys=set(),
        existing_ledger_keys=set(),
        vesum_lookup=vesum_empty,
        heritage_lookup=mock_heritage,
        english_lookup=lambda _: "captive maiden",
    )

    by_lemma = {candidate.lemma: candidate for candidate in result.candidates}
    assert "дівка-бранка" in by_lemma
    assert by_lemma["дівка-бранка"].classification == "review_queue"
    assert "heritage_attested_non_vesum" in by_lemma["дівка-бранка"].reasons
    assert by_lemma["дівка-бранка"].heritage_status is not None
    assert by_lemma["дівка-бранка"].heritage_status["classification"] == "authentic-archaism"
    assert by_lemma["дівка-бранка"].gloss == "captive maiden"


def empty_intake_cli_args(tmp_path: Path) -> list[str]:
    """Use synthetic empty inputs; never inspect a corpus or a live database."""
    source = tmp_path / "empty-curriculum"
    source.mkdir()
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"entries": []}\n', encoding="utf-8")
    return ["--curriculum-root", str(source), "--manifest", str(manifest)]


@pytest.mark.parametrize(
    "inventory_override,report_override", [(False, False), (True, False), (False, True), (True, True)]
)
def test_caller_scratch_defaults_and_override_readback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys,
    inventory_override: bool,
    report_override: bool,
) -> None:
    monkeypatch.setattr(intake, "load_existing_ledger_keys", lambda **kwargs: set())
    argv = empty_intake_cli_args(tmp_path)
    baseline_inventory, baseline_report = tmp_path / "baseline.json", tmp_path / "baseline-report.json"
    monkeypatch.delenv("TMPDIR", raising=False)
    assert intake.main([*argv, "--inventory-out", str(baseline_inventory), "--report-out", str(baseline_report)]) == 0
    expected_inventory, expected_report = baseline_inventory.read_bytes(), baseline_report.read_bytes()
    capsys.readouterr()
    # Reuse the imported API after the caller changes roots; prior outputs survive.
    for root_name in ("producer-consumer", "distinct-held-out-root"):
        root = tmp_path / root_name
        root.mkdir()
        monkeypatch.setenv("TMPDIR", str(root))
        inventory = tmp_path / f"{root_name}-inventory.json" if inventory_override else root / intake.INVENTORY_FILENAME
        report = tmp_path / f"{root_name}-report.json" if report_override else root / intake.REPORT_FILENAME
        overrides = ({"inventory_out": inventory} if inventory_override else {}) | (
            {"report_out": report} if report_override else {}
        )
        assert intake.resolve_output_paths(**overrides) == (inventory, report)
        call_args = argv.copy()
        for key, path in overrides.items():
            call_args.extend(["--" + key.replace("_", "-"), str(path)])
        assert intake.main(call_args) == 0
        output = capsys.readouterr().out
        assert f"inventory_out: {inventory}" in output and f"report_out: {report}" in output
        assert inventory.read_bytes() == expected_inventory == b"[\n\n]\n"
        assert report.read_bytes() == expected_report
        assert read_source_inventory(inventory) == []
        payload = json.loads(report.read_bytes())
        assert payload["production_outputs_updated"] == []
        assert set(payload["surface_admission"].values()) == {"unchanged"}
        assert payload["counts"]["deduped_candidates"] == 0
        assert str(tmp_path) not in report.read_text()
        assert intake.build_parser().parse_args(call_args).inventory_path == intake.DEFAULT_INVENTORY_PATH
        assert set(root.iterdir()) == ({inventory} if not inventory_override else set()) | (
            {report} if not report_override else set()
        )
    if not inventory_override:
        assert (tmp_path / "producer-consumer" / intake.INVENTORY_FILENAME).read_bytes() == expected_inventory
    if not report_override:
        assert (tmp_path / "producer-consumer" / intake.REPORT_FILENAME).read_bytes() == expected_report


@pytest.mark.parametrize("root_kind", ["unset", "empty", "relative", "missing", "file"])
@pytest.mark.parametrize("inventory_override,report_override", [(False, False), (True, False), (False, True)])
def test_invalid_caller_root_refuses_before_intake(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys,
    root_kind: str,
    inventory_override: bool,
    report_override: bool,
) -> None:
    if root_kind == "unset":
        monkeypatch.delenv("TMPDIR", raising=False)
    else:
        file = tmp_path / "file"
        file.write_text("sentinel", encoding="utf-8")
        value = {"empty": "", "relative": "relative", "missing": str(tmp_path / "missing"), "file": str(file)}[
            root_kind
        ]
        monkeypatch.setenv("TMPDIR", value)
    monkeypatch.setattr(intake, "build_curriculum_intake", lambda **kwargs: pytest.fail("must refuse before intake"))
    overrides = ({"inventory_out": tmp_path / "override-inventory.json"} if inventory_override else {}) | (
        {"report_out": tmp_path / "override-report.json"} if report_override else {}
    )
    with pytest.raises(ValueError, match="TMPDIR"):
        intake.resolve_output_paths(**overrides)
    argv = []
    for key, path in overrides.items():
        argv.extend(["--" + key.replace("_", "-"), str(path)])
    assert intake.main(argv) == 2
    assert "TMPDIR" in capsys.readouterr().err
    assert not (tmp_path / "missing").exists()
    assert not any(path.exists() for path in overrides.values())


def test_help_and_argument_errors_need_no_caller_root(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    monkeypatch.delenv("TMPDIR", raising=False)
    args = intake.build_parser().parse_args([])
    assert args.inventory_out is None and args.report_out is None
    assert args.inventory_path == intake.DEFAULT_INVENTORY_PATH
    with pytest.raises(SystemExit) as exc:
        intake.main(["--help"])
    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    for required in ("$TMPDIR", "caller", "Outputs:", "Exit codes:", "Related:"):
        assert required in help_text
    with pytest.raises(SystemExit) as exc:
        intake.main(["--ledger-out", "ledger.yaml"])
    assert exc.value.code == 2
    assert "--batch-id" in capsys.readouterr().err


def test_real_no_source_cli_retains_artifacts_for_consumer(tmp_path: Path) -> None:
    argv = empty_intake_cli_args(tmp_path)
    root = tmp_path / "subprocess-caller"
    root.mkdir()
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from scripts.lexicon import curriculum_atlas_intake as intake; "
            "intake.load_existing_ledger_keys = lambda **kwargs: set(); "
            "raise SystemExit(intake.main())",
            *argv,
        ],
        cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, "TMPDIR": str(root)},
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    inventory, report = root / intake.INVENTORY_FILENAME, root / intake.REPORT_FILENAME
    assert f"inventory_out: {inventory}" in result.stdout
    assert f"report_out: {report}" in result.stdout
    assert inventory.read_bytes() == b"[\n\n]\n"
    assert read_source_inventory(inventory) == []
    assert json.loads(report.read_bytes())["counts"]["deduped_candidates"] == 0
    assert set(root.iterdir()) == {inventory, report}


def synthetic_intake_result(tmp_path: Path):
    curriculum = write_fixture_curriculum(tmp_path)
    return intake.build_curriculum_intake(
        curriculum_root=curriculum,
        project_root=tmp_path,
        manifest_lemma_keys=set(),
        existing_ledger_keys=set(),
        vesum_lookup=fake_vesum,
        heritage_lookup=clear_heritage,
        english_lookup=lambda lemma: None,
    )


def test_direct_api_defaults_keep_bytes_and_portable_identity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    result = synthetic_intake_result(tmp_path)
    assert result.records
    before = [(record.inventory_path, record.inventory_locator) for record in result.records]
    expected = None
    for root_name in ("api-producer", "api-distinct-consumer"):
        root = tmp_path / root_name
        root.mkdir()
        monkeypatch.setenv("TMPDIR", str(root))
        inventory, report = intake.resolve_output_paths()
        intake.write_flat_source_inventory(result, inventory)
        intake.write_json_payload(result.report_payload(), report)
        actual = (inventory.read_bytes(), report.read_bytes())
        if expected is None:
            expected = actual
        assert actual == expected
        consumed = read_source_inventory(inventory)
        assert {record.lemma for record in consumed} == {record.lemma for record in result.records}
        assert json.loads(report.read_bytes())["production_outputs_updated"] == []
    assert [(record.inventory_path, record.inventory_locator) for record in result.records] == before
    assert {path for path, locator in before} == {intake.DEFAULT_INVENTORY_PATH}
    assert (tmp_path / "api-producer" / intake.INVENTORY_FILENAME).read_bytes() == expected[0]


def test_synthetic_cli_ledger_preserves_committed_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    import yaml

    result = synthetic_intake_result(tmp_path)
    inventory = tmp_path / intake.DEFAULT_INVENTORY_PATH
    ledger = tmp_path / "ledger.yaml"
    root = tmp_path / "caller"
    root.mkdir()
    monkeypatch.setenv("TMPDIR", str(root))
    builder = intake.build_curriculum_intake

    def synthetic_builder(**kwargs):
        assert kwargs["inventory_path"] == intake.DEFAULT_INVENTORY_PATH
        return result

    monkeypatch.setattr(intake, builder.__name__, synthetic_builder)
    if hasattr(intake, "load_atlas_lemma_keys"):
        monkeypatch.setattr(intake, "load_atlas_lemma_keys", lambda path: set())
    assert_destination = intake.assert_ledger_inventory_destination
    monkeypatch.setattr(
        intake,
        "assert_ledger_inventory_destination",
        lambda out, identity: assert_destination(out, identity, project_root=tmp_path),
    )
    assert (
        intake.main(
            [
                "--inventory-out",
                str(inventory),
                "--ledger-out",
                str(ledger),
                "--batch-id",
                "synthetic",
                "--batch-label",
                "Synthetic intake",
                "--reviewed-at",
                "2026-10-09",
            ]
        )
        == 0
    )
    payload = yaml.safe_load(ledger.read_text())
    assert payload["decisions"]
    assert all(row["source_inventory"]["path"] == intake.DEFAULT_INVENTORY_PATH for row in payload["decisions"])
    assert payload["production_outputs_updated"] == []
    assert {record.lemma for record in read_source_inventory(inventory)} == {record.lemma for record in result.records}
    assert f"ledger_out: {ledger}" in capsys.readouterr().out
    assert json.loads((root / intake.REPORT_FILENAME).read_bytes())["production_outputs_updated"] == []
