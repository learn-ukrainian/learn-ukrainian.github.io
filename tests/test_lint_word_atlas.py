from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from audit import lint_word_atlas


def _manifest(*senses: dict) -> dict:
    return {"entries": [{"slug": "test-entry", "senses": list(senses)}]}


def test_default_fixture_flags_exactly_the_known_cases(capsys) -> None:
    """The committed small fixture has one honest LINT-001 dodge, one dishonest
    hit, one flagged bare-EN, and one disambiguated bare-EN that must not fire."""
    assert lint_word_atlas.main([]) == 0
    output = capsys.readouterr().out

    assert "LINT-001" in output
    assert "LINT-002" in output
    assert "tsytata_quote" in output
    assert "tsytata_honest_truncation" not in output
    assert "sekunda_time_unit" in output
    assert "sekunda_disambiguated" not in output
    assert "2 finding(s)" in output


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
