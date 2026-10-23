from __future__ import annotations

import json
import subprocess
from pathlib import Path

from tests.project_python import project_python


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


def test_cli_emits_json_and_markdown(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "version": "0.1",
                "generated_at": "2026-08-31T12:00:00Z",
                "entries": [
                    _entry(
                        lemma="слово",
                        sections={"synonyms": {"items": ["лексема"]}},
                        enrichment={"definition_cards": [{"id": "vts", "definitions": ["def"]}]},
                    )
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    json_result = subprocess.run(
        [
            str(project_python()),
            "scripts/audit/atlas_hub_coverage_census.py",
            "--manifest",
            str(manifest_path),
            "--format",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    data = json.loads(json_result.stdout)
    assert data["metadata"]["total_entries"] == 1
    assert data["residual_analysis"] is not None

    md_result = subprocess.run(
        [
            str(project_python()),
            "scripts/audit/atlas_hub_coverage_census.py",
            "--manifest",
            str(manifest_path),
            "--format",
            "markdown",
            "--p0-only",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert "## Word Atlas — Slovnyk Hub Layer Coverage Census" in md_result.stdout
    assert "P1 & Structural Hub Layers" not in md_result.stdout
