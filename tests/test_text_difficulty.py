"""Contract tests for the advisory Phase 1 text-difficulty report."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.audit import text_difficulty


def _write_module(root: Path, track: str, slug: str, content: str) -> Path:
    module_path = root / track / slug / "module.md"
    module_path.parent.mkdir(parents=True)
    module_path.write_text(content, encoding="utf-8")
    return module_path


def _module_report(root: Path, track: str = "a1", slug: str = "sample") -> dict:
    return text_difficulty.build_report(root, modules=[(track, slug)])


def test_extracts_reader_visible_markdown_regions_and_excludes_noise(tmp_path: Path) -> None:
    content = """---
title: Прихований заголовок
summary: Hidden English front matter
---
<!-- Коментар не входить. INJECT_ACTIVITY: act-1 -->
# Заголовок уроку

Проза українською. English scaffold.
- Список українською.
| Українська клітинка | English cell |
| --- | --- |
> Цитата українською.

```text
Фраза у блоці.
```

Вбудований `приклад` лишається.
[Докладніше](https://example.test/українська) і https://example.test/bare
import Widget from './english-import';
export const metadata = { english: 'noise' };
<Widget label="English JSX noise" />
"""

    regions = text_difficulty.extract_markdown_regions(content)
    extracted = text_difficulty.extract_markdown_text(content)

    assert "Прихований" not in extracted
    assert "Коментар" not in extracted
    assert "INJECT_ACTIVITY" not in extracted
    assert "example.test" not in extracted
    assert "english-import" not in extracted
    assert "English JSX noise" not in extracted
    assert "Заголовок уроку" in extracted
    assert "Список українською" in extracted
    assert "Українська клітинка" in extracted
    assert "Цитата українською" in extracted
    assert "Фраза у блоці" in extracted
    assert "приклад" in extracted
    assert "Докладніше" in extracted
    assert {fragment.region for fragment in regions} >= {
        "headings",
        "prose",
        "lists",
        "tables",
        "block_quotes",
        "fenced_examples",
        "inline_examples",
    }


def test_preserves_literal_comparators_and_import_export_prose() -> None:
    extracted = text_difficulty.extract_markdown_text(
        "< 5 відсотків населення це знає.\n"
        "Це наступний український рядок.\n"
        "import — англійське слово в поясненні.\n"
        "export — ще одне слово в поясненні."
    )

    assert "5 відсотків населення це знає" in extracted
    assert "Це наступний український рядок" in extracted
    assert "import — англійське слово в поясненні" in extracted
    assert "export — ще одне слово в поясненні" in extracted


def test_mixed_language_features_use_only_ukrainian_tokens_and_report_coverage(tmp_path: Path) -> None:
    _write_module(tmp_path, "a1", "sample", "Кіт кіт мама. Пес. English support only.")

    result = _module_report(tmp_path)["results"][0]
    features = result["features"]
    coverage = result["coverage"]

    assert result["status"] == "analyzed"
    assert result["source"]["declared_target_level"] == "A1"
    assert features["ukrainian_token_count"] == 4
    assert features["ukrainian_sentence_count"] == 2
    assert features["average_ukrainian_token_length"] == 3.25
    assert features["average_ukrainian_sentence_length"] == 2.0
    assert features["unique_ukrainian_form_count"] == 3
    assert features["unique_ukrainian_form_rate"] == 0.75
    assert features["hapax_ukrainian_form_count"] == 2
    assert features["hapax_ukrainian_form_rate"] == 0.5
    assert features["mattr"]["status"] == "unavailable"
    assert features["mattr"]["reason"] == "insufficient_ukrainian_tokens"
    assert coverage["language"]["ukrainian_token_count"] == 4
    assert coverage["language"]["english_token_count"] == 3
    assert coverage["language"]["ukrainian_token_rate"] == pytest.approx(4 / 7)
    assert coverage["regions"]["prose"]["english_token_count"] == 3


def test_english_only_and_empty_sources_have_structured_no_ukrainian_results(tmp_path: Path) -> None:
    _write_module(tmp_path, "a1", "english", "English-only scaffolding. No Ukrainian words here.")
    _write_module(tmp_path, "a1", "empty", "<!-- Only a comment -->\n<!-- INJECT_ACTIVITY: demo -->")

    english = _module_report(tmp_path, slug="english")["results"][0]
    empty = _module_report(tmp_path, slug="empty")["results"][0]

    for result in (english, empty):
        assert result["status"] == "no_ukrainian_text"
        assert result["features"]["ukrainian_token_count"] == 0
        assert result["features"]["ukrainian_sentence_count"] == 0
        assert result["features"]["average_ukrainian_token_length"] is None
        assert result["features"]["average_ukrainian_sentence_length"] is None
        assert result["features"]["mattr"] == {
            "status": "unavailable",
            "reason": "insufficient_ukrainian_tokens",
            "window_size": 50,
            "minimum_token_count": 50,
            "observed_token_count": 0,
        }
    assert english["coverage"]["language"]["english_token_count"] == 6
    assert empty["coverage"]["language"]["word_token_count"] == 0


def test_mattr_uses_a_fixed_overlapping_window(tmp_path: Path) -> None:
    _write_module(tmp_path, "b1", "mattr", " ".join(["слово"] * 51) + ".")

    result = _module_report(tmp_path, track="b1", slug="mattr")["results"][0]
    mattr = result["features"]["mattr"]

    assert mattr == {
        "status": "available",
        "window_size": 50,
        "window_count": 2,
        "value": 0.02,
    }


def test_missing_and_non_regular_sources_are_structured(tmp_path: Path) -> None:
    missing = _module_report(tmp_path, track="a2", slug="absent")["results"][0]
    directory_source = tmp_path / "a2" / "directory" / "module.md"
    directory_source.mkdir(parents=True)
    skipped = text_difficulty.analyze_source(
        text_difficulty.SourceRef(track="a2", slug="directory", path=directory_source)
    )

    assert missing["status"] == "missing_source"
    assert missing["reason"] == "module_md_not_found"
    assert missing["source"]["module_path"] == "a2/absent/module.md"
    assert skipped["status"] == "skipped"
    assert skipped["reason"] == "module_md_not_regular_file"


def test_parser_capabilities_are_explicitly_unavailable_and_report_is_advisory(tmp_path: Path) -> None:
    _write_module(tmp_path, "bio", "person", "Текст має одне речення.")

    report = _module_report(tmp_path, track="bio", slug="person")
    result = report["results"][0]

    assert report["schema_version"] == "text_difficulty.v1"
    assert report["analysis"]["advisory"] is True
    assert report["analysis"]["calibration"]["status"] == "uncalibrated"
    assert report["analysis"]["does_not_estimate_cefr"] is True
    assert result["source"]["declared_target_level"] == "C1"
    for capability in (report["analysis"]["parser_capabilities"], result["capabilities"]):
        assert set(capability) == {"clauses_per_sentence", "dependency_tree_depth"}
        assert all(value["status"] == "unavailable" for value in capability.values())
        assert all("ukrainian_ud_parser" in value["reason"] for value in capability.values())

    serialized = text_difficulty.serialize_report(report)
    assert '"estimated_level"' not in serialized
    assert '"threshold"' not in serialized
    assert '"verdict"' not in serialized
    assert '"blocking"' not in serialized


def test_discovery_and_json_are_deterministic_and_output_is_stable(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_module(tmp_path, "b2", "zeta", "Один.")
    _write_module(tmp_path, "a1", "beta", "Два.")
    _write_module(tmp_path, "a1", "alpha", "Три.")

    first = text_difficulty.build_report(tmp_path)
    second = text_difficulty.build_report(tmp_path)
    first_json = text_difficulty.serialize_report(first)

    assert first_json == text_difficulty.serialize_report(second)
    assert [result["source"]["module_path"] for result in first["results"]] == [
        "a1/alpha/module.md",
        "a1/beta/module.md",
        "b2/zeta/module.md",
    ]
    assert first_json == json.dumps(first, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    output = tmp_path / "report.json"
    assert (
        text_difficulty.main(
            [
                "--curriculum-root",
                str(tmp_path),
                "--track",
                "a1",
                "--slug",
                "alpha",
                "--output",
                str(output),
            ]
        )
        == 0
    )
    assert capsys.readouterr().out == ""
    assert output.read_text(encoding="utf-8") == text_difficulty.serialize_report(
        text_difficulty.build_report(tmp_path, tracks=["a1"], slugs=["alpha"])
    )


def test_real_source_smoke_is_analyzed_without_fixed_corpus_counts() -> None:
    curriculum_root = Path(__file__).resolve().parents[1] / "curriculum" / "l2-uk-en"

    report = text_difficulty.build_report(curriculum_root, modules=[("a2", "checkpoint-dative")])
    result = report["results"][0]

    assert result["status"] == "analyzed"
    assert result["source"]["module_path"] == "a2/checkpoint-dative/module.md"
    assert result["features"]["ukrainian_token_count"] > 0
