from __future__ import annotations

from pathlib import Path

import pytest

from scripts.audit.source_inventory_intake import read_source_inventory
from scripts.audit.source_inventory_review_decisions import validate_decision_file
from scripts.lexicon import curriculum_atlas_intake as intake


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
) -> None:
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
            "--inventory-path",
            "batch_state/cli-fixture-inventory.json",
        ]
    )

    assert result == 2
    assert "data/lexicon/source-inventory" in capsys.readouterr().err


def test_existing_ledger_keys_ignores_unreviewed_inventory(tmp_path: Path) -> None:
    inventory_dir = tmp_path / "data" / "lexicon" / "source-inventory"
    inventory_dir.mkdir(parents=True)
    (inventory_dir / "prior-intake.json").write_text("[]\n", encoding="utf-8")
    decisions_dir = tmp_path / "data" / "lexicon" / "source-inventory-review-decisions"
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
