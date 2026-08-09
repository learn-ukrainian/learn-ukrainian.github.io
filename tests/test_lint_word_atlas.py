from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from audit import lint_word_atlas


def _manifest(*senses: dict, practice_items: list[dict] | None = None) -> dict:
    payload: dict = {"entries": [{"slug": "test-entry", "senses": list(senses)}]}
    if practice_items is not None:
        payload["practice_items"] = practice_items
    return payload


def test_default_fixture_flags_exactly_the_known_cases(capsys) -> None:
    """Fixture covers LINT-001/002 sense cases plus two LINT-003 practice misses."""
    assert lint_word_atlas.main([]) == 0
    output = capsys.readouterr().out

    assert "LINT-001" in output
    assert "LINT-002" in output
    assert "LINT-003" in output
    assert "tsytata_quote" in output
    assert "tsytata_honest_truncation" not in output
    assert "sekunda_time_unit" in output
    assert "sekunda_disambiguated" not in output
    assert "брак" in output
    assert "4 finding(s)" in output


def test_truncated_text_cutoff_fires_without_honest_tag() -> None:
    manifest = _manifest(
        {
            "id": "sense-1",
            "uk_source_def": "довге визначення без кінця...",
            "learner_en": ["example"],
            "completeness": "complete",
        }
    )
    findings = lint_word_atlas.lint_manifest(manifest)
    assert len(findings) == 1
    assert findings[0].rule_id == "LINT-001"
    assert findings[0].field == "uk_source_def"


def test_truncated_text_cutoff_suppressed_by_honest_tag() -> None:
    manifest = _manifest(
        {
            "id": "sense-1",
            "uk_source_def": "довге визначення без кінця...",
            "learner_en": ["example"],
            "completeness": "truncated",
        }
    )
    assert lint_word_atlas.lint_manifest(manifest) == []


def test_truncated_text_cutoff_checks_learner_en_list_items() -> None:
    manifest = _manifest(
        {
            "id": "sense-1",
            "learner_en": ["defect", "flaw…"],
            "completeness": "draft",
        }
    )
    findings = lint_word_atlas.lint_manifest(manifest)
    assert len(findings) == 1
    assert findings[0].rule_id == "LINT-001"
    assert findings[0].field == "learner_en[1]"


def test_ambiguous_bare_en_fires_for_denylisted_single_word() -> None:
    manifest = _manifest(
        {
            "id": "sense-1",
            "learner_en": ["second"],
            "en_disambiguation": "",
        }
    )
    findings = lint_word_atlas.lint_manifest(manifest)
    assert len(findings) == 1
    assert findings[0].rule_id == "LINT-002"
    assert findings[0].sense_id == "sense-1"


def test_ambiguous_bare_en_suppressed_with_disambiguation() -> None:
    manifest = _manifest(
        {
            "id": "sense-1",
            "learner_en": ["second"],
            "en_disambiguation": "unit of time (not ordinal position)",
        }
    )
    assert lint_word_atlas.lint_manifest(manifest) == []


def test_ambiguous_bare_en_ignores_multi_word_lists() -> None:
    manifest = _manifest(
        {
            "id": "sense-1",
            "learner_en": ["second", "moment"],
            "en_disambiguation": "",
        }
    )
    assert lint_word_atlas.lint_manifest(manifest) == []


def test_ambiguous_bare_en_ignores_non_denylisted_words() -> None:
    manifest = _manifest(
        {
            "id": "sense-1",
            "learner_en": ["example"],
            "en_disambiguation": "",
        }
    )
    assert lint_word_atlas.lint_manifest(manifest) == []


def test_entries_without_senses_are_skipped() -> None:
    manifest = {"entries": [{"slug": "legacy-entry", "lemma": "легасі"}]}
    assert lint_word_atlas.lint_manifest(manifest) == []


def test_drill_sense_id_missing_flags_practice_item_without_sense_id() -> None:
    manifest = _manifest(
        practice_items=[{"lemmaId": "брак", "mode": "classify"}],
    )
    findings = lint_word_atlas.lint_manifest(manifest)
    assert len(findings) == 1
    assert findings[0].rule_id == "LINT-003"
    assert findings[0].entry_slug == "брак"
    assert findings[0].field == "senseId"


def test_drill_sense_id_missing_suppressed_when_sense_id_present() -> None:
    manifest = _manifest(
        practice_items=[{"lemmaId": "брак", "senseId": "brak_defect", "mode": "classify"}],
    )
    assert lint_word_atlas.lint_manifest(manifest) == []


def test_drill_sense_id_missing_reads_per_entry_practice_bindings() -> None:
    manifest = {
        "entries": [
            {
                "slug": "брак",
                "practice_bindings": [{"mode": "flashcard"}],
            }
        ]
    }
    findings = lint_word_atlas.lint_manifest(manifest)
    assert len(findings) == 1
    assert findings[0].rule_id == "LINT-003"
    assert findings[0].entry_slug == "брак"


def test_practice_deck_mode_flags_cards_without_sense_id(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({"entries": []}), encoding="utf-8")
    deck_path = tmp_path / "practice-cloze.A1.json"
    deck_path.write_text(
        json.dumps(
            {
                "cloze": [
                    {"lemmaId": "автобус", "clozeId": "автобус:1"},
                    {"lemmaId": "мова", "senseId": "mova_language", "clozeId": "мова:1"},
                ]
            }
        ),
        encoding="utf-8",
    )

    exit_code = lint_word_atlas.main(
        ["--manifest", str(manifest_path), "--practice-deck", str(deck_path)]
    )
    assert exit_code == 0
    findings = lint_word_atlas.lint_practice_items(
        [{"lemmaId": "автобус"}, {"lemmaId": "мова", "senseId": "mova_language"}]
    )
    assert len(findings) == 1
    assert findings[0].entry_slug == "автобус"


def test_report_mode_writes_json_and_stays_advisory(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(_manifest({"id": "sense-1", "learner_en": ["second"], "en_disambiguation": ""})),
        encoding="utf-8",
    )
    report_path = tmp_path / "residual.json"

    exit_code = lint_word_atlas.main(
        ["--manifest", str(manifest_path), "--report", str(report_path)]
    )

    assert exit_code == 0  # advisory: findings exist but --strict was not passed
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["finding_count"] == 1
    assert payload["findings"][0]["rule_id"] == "LINT-002"
    assert "LINT-003" in payload["rule_ids"]


def test_strict_mode_fails_on_findings(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(_manifest({"id": "sense-1", "learner_en": ["second"], "en_disambiguation": ""})),
        encoding="utf-8",
    )

    assert lint_word_atlas.main(["--manifest", str(manifest_path), "--strict"]) == 1


def test_strict_mode_passes_when_clean(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_manifest()), encoding="utf-8")

    assert lint_word_atlas.main(["--manifest", str(manifest_path), "--strict"]) == 0


def test_missing_manifest_errors(capsys) -> None:
    try:
        lint_word_atlas.main(["--manifest", "does/not/exist.json"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("expected SystemExit for missing manifest")
