from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.audit.wiki_completeness_gate import (
    check_wiki_completeness,
)

pytestmark = pytest.mark.reads_content


def _seminar_wiki(
    tmp_path: Path,
    *,
    citations: str = "[S1] [S2]",
    sources: list[dict[str, Any]] | None = None,
    omit_sections: set[str] | None = None,
) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    omit = omit_sections or set()
    sections = {
        "Короткий зміст": f"Стислий опис теми з джерелами {citations}.",
        "Основний зміст": f"Розгорнутий виклад із контекстом {citations}.",
        "Ключові терміни": f"- Термін — визначення {citations}.",
        "Мовні зразки": f"1. Академічна фраза для аналізу {citations}.",
        "Деколонізаційна перспектива": f"Пояснення без імперської рамки {citations}.",
        "Пов'язані статті": f"- [[Суміжна тема]] {citations}.",
    }
    body = "\n\n".join(
        f"## {heading}\n\n{text}"
        for heading, text in sections.items()
        if heading not in omit
    )
    wiki = tmp_path / "seminar.md"
    wiki.write_text(
        f"""# Seminar

<!-- wiki-meta
slug: seminar
domain: folk/ritual
tracks: [folk]
-->

{body}
""",
        encoding="utf-8",
    )
    wiki.with_suffix(".sources.yaml").write_text(
        yaml.safe_dump(
            {
                "sources": sources
                if sources is not None
                else [
                    {"id": "S1", "file": "chunk-1", "type": "literary", "title": "Source 1"},
                    {"id": "S2", "file": "chunk-2", "type": "textbook", "title": "Source 2"},
                ]
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return wiki


def test_seminar_dangling_citation_fails_resolution(tmp_path: Path) -> None:
    wiki = _seminar_wiki(
        tmp_path,
        citations="[S1] [S3]",
        sources=[{"id": "S1", "file": "chunk-1", "type": "literary", "title": "Source 1"}],
    )

    report = check_wiki_completeness(wiki, level="hist", slug="seminar")

    assert report["verdict"] == "FAIL"
    assert report["checks"]["citation_resolution"]["verdict"] == "FAIL"
    assert report["checks"]["citation_resolution"]["dangling_ids"] == ["S3"]


def test_seminar_source_missing_file_or_url_fails_ref_resolution(tmp_path: Path) -> None:
    wiki = _seminar_wiki(
        tmp_path,
        sources=[
            {"id": "S1", "file": "chunk-1", "type": "literary", "title": "Source 1"},
            {"id": "S2", "type": "literary", "title": "Source 2"},
        ],
    )

    report = check_wiki_completeness(wiki, level="hist", slug="seminar")

    assert report["verdict"] == "FAIL"
    assert report["checks"]["source_ref_resolution"]["verdict"] == "FAIL"
    assert report["checks"]["source_ref_resolution"]["unresolved_ids"] == ["S2"]


def test_seminar_verify_quote_checks_every_cited_source(tmp_path: Path) -> None:
    calls: list[str] = []

    def recorder(source_id: str, quote: str, source: dict[str, Any]) -> dict[str, Any]:
        calls.append(source_id)
        return {"verdict": "PASS", "quote": quote, "source": source}

    wiki = _seminar_wiki(
        tmp_path,
        citations="[S1] [S8] [S10]",
        sources=[
            {"id": "S1", "file": "chunk-1", "type": "literary", "title": "Source 1"},
            {"id": "S8", "file": "chunk-8", "type": "literary", "title": "Source 8"},
            {"id": "S10", "file": "chunk-10", "type": "literary", "title": "Source 10"},
        ],
    )

    report = check_wiki_completeness(wiki, level="folk", slug="seminar", verify_quote_fn=recorder)

    assert report["verdict"] == "PASS"
    assert report["checks"]["all_chunk_verify_quote"]["detail"] == "3/3 verify_quote returned PASS"
    assert calls == ["S1", "S8", "S10"]


def test_seminar_verify_quote_does_not_call_adapter_for_missing_sources(tmp_path: Path) -> None:
    calls: list[str] = []

    def recorder(source_id: str, quote: str, source: dict[str, Any]) -> dict[str, Any]:
        calls.append(source_id)
        assert source
        return {"verdict": "PASS", "quote": quote, "source": source}

    wiki = _seminar_wiki(
        tmp_path,
        citations="[S1] [S3]",
        sources=[{"id": "S1", "file": "chunk-1", "type": "literary", "title": "Source 1"}],
    )

    report = check_wiki_completeness(wiki, level="folk", slug="seminar", verify_quote_fn=recorder)

    assert report["verdict"] == "FAIL"
    assert report["checks"]["all_chunk_verify_quote"]["failures"] == ["S3"]
    assert calls == ["S1"]
