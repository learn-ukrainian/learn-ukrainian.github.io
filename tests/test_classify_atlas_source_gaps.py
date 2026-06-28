from __future__ import annotations

import json
import subprocess

from scripts.audit.classify_atlas_source_gaps import classify_manifest, rendered_sections


def _entry(**overrides: object) -> dict:
    entry = {
        "lemma": "слово",
        "url_slug": "слово",
        "gloss": "word",
        "pos": "noun",
        "primary_source": "test",
        "enrichment": {
            "definition_cards": [
                {
                    "id": "vts-main",
                    "source": "ВТС",
                    "definitions": ["Тестове значення."],
                }
            ],
            "morphology": {
                "pos": "noun",
                "form_count": 1,
                "forms": [{"form": "слово", "label": "називний"}],
                "source": "VESUM",
            },
            "translation": {"en": ["word"], "source": "test"},
        },
        "sections": {},
    }
    entry.update(overrides)
    return entry


def test_rendered_sections_excludes_course_usage_from_source_backed_gap_count() -> None:
    entry = _entry(course_usage=[{"track": "a1", "module_num": 1, "slug": "known"}])

    assert rendered_sections(entry) == {"meaning", "morphology", "translation"}


def test_classify_manifest_reports_unclassified_missing_source_sections() -> None:
    thin = _entry(
        lemma="тонкий",
        url_slug="тонкий",
        gloss=None,
        pos="adjective",
        enrichment={
            "definition_cards": [
                {
                    "id": "vts-main",
                    "source": "ВТС",
                    "definitions": ["Без товщини."],
                }
            ],
            "morphology": {
                "pos": "adjective",
                "form_count": 1,
                "forms": [{"form": "тонкий", "label": "прикметник"}],
                "source": "VESUM",
            },
        },
    )

    summary = classify_manifest({"entries": [thin]}, min_rich_sections=5, sample_limit=20)

    assert summary["thin_entries"] == 1
    assert summary["unclassified_source_gap_entries"] == 1
    assert summary["by_status"] == {"unclassified_source_gap": 6}
    assert summary["by_section"]["etymology"] == 1
    assert summary["by_section"]["translation"] == 1
    assert {row["section"] for row in summary["samples"]} == {
        "etymology",
        "synonyms_antonyms",
        "idioms",
        "literary_attestation",
        "translation",
        "wikipedia",
    }


def test_classify_manifest_uses_declared_gap_statuses_and_skips_not_applicable() -> None:
    thin = _entry(
        gloss=None,
        source_gaps=[
            {
                "section": "etymology",
                "status": "lookup_granularity_gap",
                "source": "ЕСУМ",
                "note": "root-indexed entry",
            },
            {"section": "idioms", "status": "not_applicable", "source": "phrasebook"},
            {"section": "translation", "status": "source_absent", "source": "dmklinger"},
        ],
        enrichment={
            "definition_cards": [
                {
                    "id": "vts-main",
                    "source": "ВТС",
                    "definitions": ["Тестове значення."],
                }
            ],
            "morphology": {
                "pos": "noun",
                "form_count": 1,
                "forms": [{"form": "слово", "label": "називний"}],
                "source": "VESUM",
            },
        },
    )

    summary = classify_manifest({"entries": [thin]}, min_rich_sections=5, sample_limit=20)

    rows = {(row["section"], row["status"], row["source"], row["note"]) for row in summary["samples"]}
    assert ("etymology", "lookup_granularity_gap", "ЕСУМ", "root-indexed entry") in rows
    assert ("translation", "source_absent", "dmklinger", None) in rows
    assert not any(row["section"] == "idioms" for row in summary["samples"])
    assert summary["by_status"]["lookup_granularity_gap"] == 1
    assert summary["by_status"]["source_absent"] == 1


def test_classify_manifest_accepts_enrichment_source_gap_mapping() -> None:
    thin = _entry(
        enrichment={
            "definition_cards": [
                {
                    "id": "vts-main",
                    "source": "ВТС",
                    "definitions": ["Тестове значення."],
                }
            ],
            "morphology": {
                "pos": "noun",
                "form_count": 1,
                "forms": [{"form": "слово", "label": "називний"}],
                "source": "VESUM",
            },
            "source_gaps": {
                "wikipedia": {
                    "status": "source_not_integrated",
                    "source": "Вікіпедія",
                }
            },
        },
    )

    summary = classify_manifest({"entries": [thin]}, min_rich_sections=5, sample_limit=20)

    assert any(
        row["section"] == "wikipedia"
        and row["status"] == "source_not_integrated"
        and row["source"] == "Вікіпедія"
        for row in summary["samples"]
    )


def test_classify_manifest_marks_bad_declared_status() -> None:
    thin = _entry(source_gaps=[{"section": "etymology", "status": "maybe_later"}])

    summary = classify_manifest({"entries": [thin]}, min_rich_sections=5, sample_limit=20)

    assert any(
        row["section"] == "etymology"
        and row["status"] == "invalid_source_gap_status"
        and row["note"] == "invalid status: maybe_later"
        for row in summary["samples"]
    )


def test_cli_can_fail_on_unclassified_gaps(tmp_path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps({"entries": [_entry(gloss=None)]}, ensure_ascii=False),
        encoding="utf-8",
    )

    blocked = subprocess.run(
        [
            ".venv/bin/python",
            "scripts/audit/classify_atlas_source_gaps.py",
            "--manifest",
            str(manifest_path),
            "--local",
            "--fail-on-unclassified",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert blocked.returncode == 1
    assert "--fail-on-unclassified matched" in blocked.stdout

    subprocess.run(
        [
            ".venv/bin/python",
            "scripts/audit/classify_atlas_source_gaps.py",
            "--manifest",
            str(manifest_path),
            "--local",
            "--max-unclassified-source-gaps",
            "6",
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def test_cli_emits_machine_readable_formats(tmp_path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps({"entries": [_entry(gloss=None)]}, ensure_ascii=False),
        encoding="utf-8",
    )

    json_result = subprocess.run(
        [
            ".venv/bin/python",
            "scripts/audit/classify_atlas_source_gaps.py",
            "--manifest",
            str(manifest_path),
            "--local",
            "--format",
            "json",
            "--limit",
            "1",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(json_result.stdout)
    assert payload["unclassified_source_gap_rows"] == 5
    assert len(payload["samples"]) == 1

    tsv_result = subprocess.run(
        [
            ".venv/bin/python",
            "scripts/audit/classify_atlas_source_gaps.py",
            "--manifest",
            str(manifest_path),
            "--local",
            "--format",
            "tsv",
            "--limit",
            "1",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    lines = tsv_result.stdout.strip().splitlines()
    assert lines[0] == "lemma\turl_slug\tpos\tcefr\tsection\tstatus\tsource\tnote\tprimary_source"
    assert len(lines) == 2


def test_cli_rejects_negative_unclassified_gap_limit(tmp_path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps({"entries": [_entry(gloss=None)]}, ensure_ascii=False),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            ".venv/bin/python",
            "scripts/audit/classify_atlas_source_gaps.py",
            "--manifest",
            str(manifest_path),
            "--local",
            "--max-unclassified-source-gaps",
            "-1",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "must be non-negative" in result.stdout
