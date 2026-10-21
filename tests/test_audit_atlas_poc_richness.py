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
