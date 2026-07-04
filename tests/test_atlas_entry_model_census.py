from __future__ import annotations

import json
import subprocess
from pathlib import Path

from scripts.audit.atlas_entry_model_census import build_entry_model_census, classify_entry


def _entry(**overrides: object) -> dict:
    entry = {
        "lemma": "слово",
        "url_slug": "слово",
        "gloss": "word",
        "pos": "noun",
        "primary_source": "test",
        "course_usage": [],
    }
    entry.update(overrides)
    return entry


def test_explicit_entry_type_counts_reviewed_article() -> None:
    classification = classify_entry(_entry(entry_type="phraseologism", lemma="бити байдики", url_slug="бити-байдики"))

    assert classification.bucket == "phraseologism"
    assert classification.counts_as_entry is True
    assert classification.source == "entry_type"


def test_form_of_records_are_not_reviewed_entries() -> None:
    payload = build_entry_model_census(
        {
            "entries": [
                _entry(lemma="слово", url_slug="слово", entry_type="lemma"),
                _entry(
                    lemma="слова",
                    url_slug="слова",
                    form_of={"lemma": "слово", "url_slug": "слово"},
                ),
            ]
        }
    )

    assert payload["reviewed_entries_by_type"]["lemma"] == 1
    assert payload["total_reviewed_entries"] == 1
    assert payload["non_entry_records"]["form_alias"] == 1


def test_legacy_records_use_conservative_buckets() -> None:
    payload = build_entry_model_census(
        {
            "entries": [
                _entry(lemma="Ілля", url_slug="ілля", pos="proper noun:sg"),
                _entry(lemma="доконаний вид", url_slug="доконаний-вид", pos="noun phrase"),
                _entry(lemma="pluralia tantum", url_slug="pluralia-tantum", pos="grammar term"),
            ]
        }
    )

    assert payload["reviewed_entries_by_type"]["proper_name"] == 1
    assert payload["reviewed_entries_by_type"]["multiword_term"] == 1
    assert payload["non_entry_records"]["grammar_term"] == 1
    assert payload["warnings"]["legacy_multiword_defaulted_to_multiword_term"] == 1


def test_missing_required_fields_are_invalid_non_entries() -> None:
    for entry in (
        _entry(lemma="", url_slug="слово"),
        _entry(lemma="слово", url_slug=""),
    ):
        classification = classify_entry(entry)
        assert classification.bucket == "invalid"
        assert classification.counts_as_entry is False
        assert classification.warning == "missing_lemma_or_url_slug"


def test_explicit_rejected_types_are_non_entry_records() -> None:
    payload = build_entry_model_census(
        {
            "entries": [
                _entry(entry_type="noise"),
                _entry(entry_type="rejected", lemma="неприйняте", url_slug="неприйняте"),
            ]
        }
    )

    assert payload["non_entry_records"]["noise_rejected"] == 2
    assert payload["total_reviewed_entries"] == 0


def test_public_payload_is_aggregate_only() -> None:
    payload = build_entry_model_census(
        {
            "entries": [
                _entry(entry_type="phraseologism", lemma="бити байдики", url_slug="бити-байдики"),
                _entry(entry_type="proverb", lemma="Без труда нема плода", url_slug="без-труда-нема-плода"),
            ]
        }
    )

    public_json = json.dumps(payload, ensure_ascii=False)
    assert "бити байдики" not in public_json
    assert "Без труда" not in public_json
    assert payload["reviewed_entries_by_type"]["phraseologism"] == 1
    assert payload["reviewed_entries_by_type"]["proverb"] == 1


def test_cli_emits_json_and_markdown(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "entries": [
                    _entry(entry_type="lemma"),
                    _entry(entry_type="expression", lemma="будь ласка", url_slug="будь-ласка"),
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    json_result = subprocess.run(
        [
            ".venv/bin/python",
            "scripts/audit/atlas_entry_model_census.py",
            "--manifest",
            str(manifest_path),
            "--format",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(json_result.stdout)["reviewed_entries_by_type"]["expression"] == 1

    md_result = subprocess.run(
        [
            ".venv/bin/python",
            "scripts/audit/atlas_entry_model_census.py",
            "--manifest",
            str(manifest_path),
            "--format",
            "markdown",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "# Word Atlas Entry Model Census" in md_result.stdout


def test_cli_can_fail_on_legacy_heuristic(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({"entries": [_entry()]}), encoding="utf-8")

    result = subprocess.run(
        [
            ".venv/bin/python",
            "scripts/audit/atlas_entry_model_census.py",
            "--manifest",
            str(manifest_path),
            "--fail-on-legacy-heuristic",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "--fail-on-legacy-heuristic matched 1 records" in result.stdout
