from __future__ import annotations

import json
import subprocess

from scripts.audit.audit_atlas_poc_richness import (
    audit_manifest,
)
from tests.project_python import project_python


def _entry(**overrides: object) -> dict:
    entry = {
        "lemma": "слово",
        "url_slug": "слово",
        "gloss": "word",
        "pos": "noun",
        "primary_source": "test",
        "course_usage": [],
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


def test_audit_cli_enforces_explicit_max_counts(tmp_path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "entries": [
                    _entry(
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
                ]
            }
        ),
        encoding="utf-8",
    )

    blocked = subprocess.run(
        [
            str(project_python()),
            "scripts/audit/audit_atlas_poc_richness.py",
            "--manifest",
            str(manifest_path),
            "--local",
            "--max-search-no-visible-gloss",
            "0",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert blocked.returncode == 1
    assert "search_no_visible_gloss: 1 exceeds max 0" in blocked.stdout

    subprocess.run(
        [
            str(project_python()),
            "scripts/audit/audit_atlas_poc_richness.py",
            "--manifest",
            str(manifest_path),
            "--local",
            "--max-search-no-visible-gloss",
            "1",
            "--max-old-gate-no-english-anchor",
            "1",
            "--max-poc-thin-pages",
            "1",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_audit_separates_search_gloss_and_poc_thin_failures() -> None:
    ogo_like = _entry(
        lemma="ого",
        url_slug="ого",
        gloss="wow",
        pos="interjection",
        enrichment={
            "cefr": {"level": "A2", "source": "test"},
            "definition_cards": [
                {"id": "vts-main", "source": "ВТС", "definitions": ["Здивування."]}
            ],
            "morphology": {
                "pos": "interjection",
                "form_count": 1,
                "forms": [{"form": "ого", "label": "вигук"}],
                "source": "VESUM",
            },
            "literary_attestation": {"text": "Ого!", "source": "corpus"},
            "translation": {"en": ["wow"], "source": "dmklinger"},
        },
    )
    translation_fallback = _entry(
        lemma="помішувати",
        url_slug="помішувати",
        gloss=None,
        pos="verb",
        enrichment={
            "definition_cards": [
                {"id": "vts-main", "source": "ВТС", "definitions": ["Мішати."]}
            ],
            "morphology": {
                "pos": "verb",
                "form_count": 1,
                "forms": [{"form": "помішувати", "label": "інфінітив"}],
                "source": "VESUM",
            },
            "translation": {"en": ["stir"], "source": "dmklinger"},
        },
    )
    no_english = _entry(
        lemma="тонкий",
        url_slug="тонкий",
        gloss=None,
        pos="adjective",
        enrichment={
            "cefr": {"level": "A1", "source": "test"},
            "definition_cards": [
                {"id": "vts-main", "source": "ВТС", "definitions": ["Без товщини."]}
            ],
            "morphology": {
                "pos": "adjective",
                "form_count": 1,
                "forms": [{"form": "тонкий", "label": "прикметник"}],
                "source": "VESUM",
            },
        },
    )

    summary = audit_manifest(
        {"entries": [ogo_like, translation_fallback, no_english]},
        min_rich_sections=5,
        sample_limit=10,
    )

    assert summary["old_gate_enriched_search_entries"] == 3
    assert summary["search_no_visible_gloss"] == 1
    assert summary["old_gate_no_english_anchor"] == 1
    assert summary["poc_thin_pages"] == 3
    assert summary["priority_poc_thin_pages"] == 2
    assert [row["lemma"] for row in summary["samples"]["search_no_visible_gloss"]] == [
        "тонкий"
    ]


def test_form_stub_excluded_from_poc_thin_pages() -> None:
    target = _entry(
        lemma="брат",
        url_slug="брат",
        enrichment={
            "definition_cards": [
                {"id": "vts-main", "source": "ВТС", "definitions": ["Родич чоловічої статі."]}
            ],
            "etymology": {"text": "Indo-European.", "source": "Kaikki"},
            "morphology": {
                "pos": "noun",
                "form_count": 1,
                "forms": [{"form": "брат", "label": "називний"}],
                "source": "VESUM",
            },
            "literary_attestation": {"text": "Брате мій.", "source": "corpus"},
            "translation": {"en": ["brother"], "source": "test"},
        },
        sections={"synonyms": {"items": ["сиб"], "source": "slovnyk"}},
        wiki_reference={
            "wikipedia": {
                "title": "Брат",
                "summary": "...",
                "url": "https://example.test",
            }
        },
    )
    stub = _entry(
        lemma="брата",
        url_slug="брата",
        gloss="brother (gen.)",
        enrichment={"translation": {"en": ["brother"], "source": "test"}},
        form_of={"lemma": "брат", "url_slug": "брат"},
    )

    summary = audit_manifest({"entries": [target, stub]}, min_rich_sections=5, sample_limit=10)

    assert summary["form_stub_pages"] == 1
    assert summary["form_stub_broken"] == 0
    assert summary["poc_thin_pages"] == 0


def test_form_stub_broken_when_target_missing() -> None:
    stub = _entry(
        lemma="брата",
        url_slug="брата",
        gloss="brother (gen.)",
        enrichment={"translation": {"en": ["brother"], "source": "test"}},
        form_of={"lemma": "брат", "url_slug": "брат"},
    )

    summary = audit_manifest({"entries": [stub]}, min_rich_sections=5, sample_limit=10)

    assert summary["form_stub_pages"] == 1
    assert summary["form_stub_broken"] == 1
    assert summary["samples"]["form_stub_broken"][0]["lemma"] == "брата"


def test_malformed_form_of_counts_as_broken_not_excluded_stub() -> None:
    entry = _entry(
        lemma="брата",
        url_slug="брата",
        gloss="brother (gen.)",
        form_of="брат",
    )

    summary = audit_manifest({"entries": [entry]}, min_rich_sections=5, sample_limit=10)

    assert summary["form_stub_pages"] == 0
    assert summary["form_stub_broken"] == 1
    assert summary["poc_thin_pages"] == 1


def test_multiword_weak_page_stays_thin_without_meaning_bucket() -> None:
    entry = _entry(
        lemma="на вулиці",
        url_slug="на-вулиці",
        gloss="on the street",
        enrichment={
            "meaning": {"definitions": [], "source": "test"},
        },
        wiki_reference={
            "wikipedia": {
                "title": "Вулиця",
                "summary": "...",
                "url": "https://example.test",
            }
        },
    )

    summary = audit_manifest({"entries": [entry]}, min_rich_sections=5, sample_limit=10)

    assert summary["thin_by_class"]["multiword"] == 1
    assert summary["poc_thin_pages"] == 1


def test_multiword_passes_with_meaning_anchor_and_extra_bucket() -> None:
    entry = _entry(
        lemma="на вулиці",
        url_slug="на-вулиці",
        gloss="on the street",
        enrichment={
            "definition_cards": [
                {"id": "vts-main", "source": "ВТС", "definitions": ["На дорозі."]}
            ],
            "translation": {"en": ["on the street"], "source": "test"},
        },
        wiki_reference={
            "wikipedia": {
                "title": "Вулиця",
                "summary": "...",
                "url": "https://example.test",
            }
        },
    )

    summary = audit_manifest({"entries": [entry]}, min_rich_sections=5, sample_limit=10)

    assert summary["thin_by_class"]["multiword"] == 0
    assert summary["poc_thin_pages"] == 0


def test_lemma_article_keeps_five_of_nine_bar() -> None:
    rich = _entry(
        enrichment={
            "definition_cards": [
                {"id": "vts-main", "source": "ВТС", "definitions": ["Абзац."]}
            ],
            "etymology": {"text": "Borrowed.", "source": "Kaikki"},
            "morphology": {
                "pos": "noun",
                "form_count": 1,
                "forms": [{"form": "слово", "label": "називний"}],
                "source": "VESUM",
            },
            "literary_attestation": {"text": "Приклад.", "source": "corpus"},
            "translation": {"en": ["word"], "source": "test"},
        },
        sections={"synonyms": {"items": ["вираз"], "source": "slovnyk"}},
        wiki_reference={
            "wikipedia": {
                "title": "Слово",
                "summary": "...",
                "url": "https://example.test",
            }
        },
    )
    thin = _entry(
        lemma="тонкий",
        url_slug="тонкий",
        gloss="thin",
        enrichment={
            "definition_cards": [
                {"id": "vts-main", "source": "ВТС", "definitions": ["Без товщини."]}
            ],
            "morphology": {
                "pos": "adjective",
                "form_count": 1,
                "forms": [{"form": "тонкий", "label": "прикметник"}],
                "source": "VESUM",
            },
            "translation": {"en": ["thin"], "source": "test"},
        },
    )

    summary = audit_manifest({"entries": [rich, thin]}, min_rich_sections=5, sample_limit=10)

    assert summary["thin_by_class"]["lemma_article"] == 1
    assert summary["poc_thin_pages"] == 1
