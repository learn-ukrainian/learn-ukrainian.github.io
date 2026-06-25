from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.build import linear_pipeline


def _plan(
    *,
    readings: list[dict[str, Any]] | None = None,
    level: str = "folk",
) -> dict[str, Any]:
    return {
        "level": level,
        "sequence": 1,
        "module": 1,
        "slug": "reading-structure-test",
        "title": "Reading structure test",
        "content_outline": [
            {
                "section": "Корпус і контекст",
                "words": 20,
                "points": ["Read a hosted primary text."],
            }
        ],
        "readings": readings or [],
    }


def _artifact(markdown: str) -> linear_pipeline.SectionArtifact:
    return linear_pipeline.SectionArtifact(
        section_id="s1",
        markdown=markdown,
        citations_used=[],
        primary_readings_used=[],
        vocab_candidates=[],
        activity_refs=[],
        self_check={},
    )


def _write_hosted_reading(
    readings_dir: Path,
    slug: str,
    *,
    title: str,
    lines: list[str],
    aliases: list[str] | None = None,
) -> None:
    readings_dir.mkdir(parents=True, exist_ok=True)
    alias_block = ""
    if aliases:
        alias_block = "aliases:\n" + "".join(f"  - {alias!r}\n" for alias in aliases)
    quoted_lines = "\n".join(f"> {line}" for line in lines)
    (readings_dir / f"{slug}.mdx").write_text(
        "\n".join(
            [
                "---",
                f"title: {title!r}",
                'title_en: "Test reading"',
                alias_block.rstrip(),
                "---",
                "import PrimaryReading from '@site/src/components/PrimaryReading';",
                "",
                "<PrimaryReading>",
                "",
                quoted_lines,
                "",
                "</PrimaryReading>",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _assemble(
    monkeypatch: Any,
    tmp_path: Path,
    markdown: str,
    readings: list[dict[str, Any]],
    *,
    level: str = "folk",
) -> dict[str, Any]:
    readings_dir = tmp_path / "readings"
    monkeypatch.setattr(linear_pipeline, "_HOSTED_READINGS_DIR", readings_dir)
    return linear_pipeline.assemble_iterative(
        [_artifact(markdown)],
        _plan(readings=readings, level=level),
        activities=[],
    )


def _diagnostics(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in str(result["reading_structure_diagnostics_jsonl"]).splitlines()
        if line.strip()
    ]


def test_unique_match_injects_reading_attr_attribution_and_strips_source_tag(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    _write_hosted_reading(
        tmp_path / "readings",
        "vesna",
        title="«Ой весна, весна, ти красна» (веснянка)",
        lines=["Ой весна, весна, ти красна,", "Що ж ти нам, весна, принесла?"],
    )
    result = _assemble(
        monkeypatch,
        tmp_path,
        "\n".join(
            [
                ":::primary-reading",
                "> Ой весна, весна, ти красна, [S1]",
                "> Що ж ти нам, весна, принесла?",
                ":::",
            ]
        ),
        [
            {
                "title": "«Ой весна, весна, ти красна»",
                "source": "Народна творчість; корпус тестовий",
                "hosting": "host",
                "reading_slug": "vesna",
            }
        ],
    )

    module_md = str(result["module_md"])
    assert ':::primary-reading{reading="vesna"}' in module_md
    assert "— Народна творчість; корпус тестовий, «Ой весна, весна, ти красна»" in module_md
    assert "[S1]" not in module_md
    assert "> Ой весна, весна, ти красна," in module_md
    assert _diagnostics(result) == []


def test_existing_reading_attr_is_preserved_without_double_injection(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    _write_hosted_reading(
        tmp_path / "readings",
        "vesna",
        title="«Ой весна»",
        lines=["Ой весна"],
    )
    result = _assemble(
        monkeypatch,
        tmp_path,
        "\n".join(
            [
                ':::primary-reading{reading="already-linked"}',
                "> Ой весна [S2]",
                "— Старе джерело, «Ой весна»",
                ":::",
            ]
        ),
        [
            {
                "title": "«Ой весна»",
                "source": "Нове джерело",
                "hosting": "hosted",
                "reading_slug": "vesna",
            }
        ],
    )

    module_md = str(result["module_md"])
    assert module_md.count('reading="already-linked"') == 1
    assert 'reading="vesna"' not in module_md
    assert module_md.count("— Старе джерело, «Ой весна»") == 1
    assert "Нове джерело" not in module_md
    assert "[S2]" not in module_md


def test_missing_hosted_file_leaves_block_bare_and_emits_diagnostic(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    result = _assemble(
        monkeypatch,
        tmp_path,
        ":::primary-reading\n> Ой весна\n:::",
        [
            {
                "title": "«Ой весна»",
                "source": "Народна творчість",
                "hosting": "host",
                "reading_slug": "missing-file",
            }
        ],
    )

    module_md = str(result["module_md"])
    assert ":::primary-reading\n> Ой весна\n:::" in module_md
    assert "{reading=" not in module_md
    diagnostics = _diagnostics(result)
    assert diagnostics == [
        {
            "candidate_count": 0,
            "event": "reading_structure_unmatched",
            "incipit": "Ой весна",
            "reason": "no_unique_match",
        }
    ]


def test_ambiguous_duplicate_incipit_leaves_block_bare_and_emits_diagnostic(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    _write_hosted_reading(
        tmp_path / "readings",
        "first",
        title="«Перший текст»",
        lines=["Спільний перший рядок", "Перший другий рядок"],
    )
    _write_hosted_reading(
        tmp_path / "readings",
        "second",
        title="«Другий текст»",
        lines=["Спільний перший рядок", "Другий другий рядок"],
    )
    result = _assemble(
        monkeypatch,
        tmp_path,
        ":::primary-reading\n> Спільний перший рядок\n:::",
        [
            {
                "title": "«Перший текст»",
                "source": "Перше джерело",
                "hosting": "host",
                "reading_slug": "first",
            },
            {
                "title": "«Другий текст»",
                "source": "Друге джерело",
                "hosting": "host",
                "reading_slug": "second",
            },
        ],
    )

    module_md = str(result["module_md"])
    assert "{reading=" not in module_md
    assert _diagnostics(result) == [
        {
            "candidate_count": 2,
            "event": "reading_structure_unmatched",
            "incipit": "Спільний перший рядок",
            "matched_by": "incipit",
            "reason": "ambiguous_match",
        }
    ]


def test_incipit_not_in_hosted_file_leaves_block_bare_and_emits_diagnostic(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    _write_hosted_reading(
        tmp_path / "readings",
        "vesna",
        title="«Ой весна, весна, ти красна»",
        lines=["Ой весна, весна, ти красна,"],
    )
    result = _assemble(
        monkeypatch,
        tmp_path,
        "\n".join(
            [
                ":::primary-reading",
                "> Неправильний перший рядок",
                "Назва: «Ой весна, весна, ти красна»",
                ":::",
            ]
        ),
        [
            {
                "title": "«Ой весна, весна, ти красна»",
                "source": "Народна творчість",
                "hosting": "host",
                "reading_slug": "vesna",
            }
        ],
    )

    module_md = str(result["module_md"])
    assert "{reading=" not in module_md
    assert _diagnostics(result) == [
        {
            "candidate_count": 1,
            "event": "reading_structure_unmatched",
            "incipit": "Неправильний перший рядок",
            "matched_by": "hosted_file_title",
            "reason": "incipit_not_in_hosted_file",
        }
    ]


def test_source_tag_strip_variants_inside_primary_reading_preserve_verse_text(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    result = _assemble(
        monkeypatch,
        tmp_path,
        "\n".join(
            [
                ":::primary-reading",
                "> [S1]",
                "> Ой весна [S2] весна",
                "[S3]",
                "Текст [S4] текст",
                "> Дужки [не джерело]",
                ":::",
            ]
        ),
        [],
    )

    module_md = str(result["module_md"])
    assert "[S1]" not in module_md
    assert "[S2]" not in module_md
    assert "[S3]" not in module_md
    assert "[S4]" not in module_md
    assert "> [S1]" not in module_md
    assert "\n[S3]\n" not in module_md
    assert "> Ой весна весна" in module_md
    assert "Текст текст" in module_md
    assert "> Дужки [не джерело]" in module_md


def test_single_shot_writer_artifact_parse_path_does_not_inject_reading_structure() -> None:
    module_md = ":::primary-reading\n> Ой весна [S1]\n:::\n"
    output = linear_pipeline.render_writer_artifacts_output(
        {
            "module.md": module_md,
            "activities.yaml": "[]\n",
            "vocabulary.yaml": "[]\n",
            "resources.yaml": "[]\n",
        }
    )

    parsed = linear_pipeline.parse_writer_output(output)

    assert parsed["module.md"] == module_md
    assert "{reading=" not in parsed["module.md"]
    assert "[S1]" in parsed["module.md"]
