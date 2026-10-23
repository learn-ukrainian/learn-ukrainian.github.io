"""Contract tests for the advisory Phase 1 text-difficulty report."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.audit import text_difficulty

pytestmark = pytest.mark.reads_content


def _write_module(root: Path, track: str, slug: str, content: str) -> Path:
    module_path = root / track / slug / "module.md"
    module_path.parent.mkdir(parents=True)
    module_path.write_text(content, encoding="utf-8")
    return module_path


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
