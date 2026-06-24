from __future__ import annotations

import re
from typing import Any

from scripts.build import linear_pipeline

PLAN_SECTION_TITLES = [
    "Розминка",
    "Конфліктна карта: як читати походження веснянок",
    "Читання: Як веснянка кличе весну",
    "Аналіз: Хоровод, гаївка і великодній простір",
    "Дискусія: Від обряду до естетики",
    "Підсумок",
]


def _plan() -> dict[str, Any]:
    return {
        "level": "folk",
        "sequence": 1,
        "module": 1,
        "slug": "vesnianky-hayivky",
        "title": "Веснянки і гаївки",
        "content_outline": [
            {"section": title, "words": 1, "points": ["Cover the section."]}
            for title in PLAN_SECTION_TITLES
        ],
    }


def _artifact(section_id: str, markdown: str) -> linear_pipeline.SectionArtifact:
    return linear_pipeline.SectionArtifact(
        section_id=section_id,
        markdown=markdown,
        citations_used=[],
        primary_readings_used=[],
        vocab_candidates=[],
        activity_refs=[],
        self_check={},
    )


def test_assemble_iterative_emits_plan_h2_headings_once() -> None:
    artifacts = [
        _artifact(
            "s1",
            "### Warmup invented heading\n\nBody for warmup.\n\n### Kept subheading\n\nMore.",
        ),
        _artifact("s2", "Conflict map body without any section heading."),
        _artifact(
            "s3",
            "# Invented module title\n\n## Invented reading title\n\nReading body.",
        ),
        _artifact("s4", "## 4. Spatial analysis\n\nAnalysis body."),
        _artifact("s5", "### Discussion as theme\n\nDiscussion body."),
        _artifact("s6", "Summary body.\n\n### Kept closing subheading\n\nFinal note."),
    ]

    result = linear_pipeline.assemble_iterative(artifacts, _plan())
    module_md = result["module_md"]
    gate = linear_pipeline._section_gate(module_md, _plan())

    assert gate["passed"] is True
    assert gate["missing_headings"] == []
    assert gate["duplicate_headings"] == []
    for title in PLAN_SECTION_TITLES:
        assert len(re.findall(rf"^## {re.escape(title)}$", module_md, re.MULTILINE)) == 1
    assert "## 4. Spatial analysis" not in module_md
    assert "### Kept subheading" in module_md
    assert "### Kept closing subheading" in module_md


def test_assemble_iterative_sidecar_ranges_follow_rewritten_headings() -> None:
    result = linear_pipeline.assemble_iterative(
        [
            _artifact("s1", "### Wrong opening\n\nFirst body."),
            _artifact("s2", "Second body."),
            _artifact("s3", "Third body."),
            _artifact("s4", "Fourth body."),
            _artifact("s5", "Fifth body."),
            _artifact("s6", "Sixth body."),
        ],
        _plan(),
    )

    lines = result["module_md"].splitlines()
    sidecar = result["sidecar"]

    for index, title in enumerate(PLAN_SECTION_TITLES, start=1):
        entry = sidecar[f"s{index}"]
        assert lines[entry["line_start"] - 1] == f"## {title}"
        assert entry["line_start"] <= entry["line_end"]
