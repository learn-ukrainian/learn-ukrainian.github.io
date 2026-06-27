from __future__ import annotations

import sqlite3
from pathlib import Path

from scripts.readings.generate_readings import (
    GENERATED_MARKER,
    PrimaryReadingCandidate,
    generate_from_demand,
    reading_slug,
)

ZAPOVIT_TEXT = """ЗАПОВІТ
Як умру, то поховайте
Мене на могилі,
Серед степу широкого,
На Вкраїні милій."""

MODERN_TEXT = """НІЧНИЙ ВІРШ
Сучасний вірш, рядок за рядком."""


def test_generate_from_demand_writes_hostable_public_domain_reading(tmp_path: Path) -> None:
    plans_dir = _write_plans(
        tmp_path,
        [
            {
                "track": "lit",
                "slug": "zapovit-module",
                "title": "Модуль про Заповіт",
                "references": [{"title": "Заповіт (1845)", "author": "Тарас Шевченко"}],
            }
        ],
    )
    db_path = _write_sources_db(
        tmp_path,
        [
            _row(
                chunk_id=1,
                work="Заповіт",
                author="Шевченко Т.",
                year=1845,
                source_file="ukrlib-shevchenko",
                text=ZAPOVIT_TEXT,
            )
        ],
    )
    output_dir = tmp_path / "readings"

    summary = generate_from_demand(plans_dir=plans_dir, output_dir=output_dir, sources_db=db_path)

    assert [item.slug for item in summary.written] == ["zapovit"]
    assert summary.skipped == ()
    generated = output_dir / "zapovit.mdx"
    content = generated.read_text(encoding="utf-8")
    assert 'tracks: ["lit"]' in content
    assert 'taught_in: ["zapovit-module"]' in content
    assert 'source_chunk_ids: ["1"]' in content
    assert "<PrimaryReading" in content
    assert "text={`" in content
    assert "Як умру, то поховайте" in content
    assert "**Джерело:** Шевченко Т.; корпус ukrlib-shevchenko." in content
    assert "**Де вивчають:** [LIT · «Модуль про Заповіт»](/lit/zapovit-module/)" in content
    assert GENERATED_MARKER in content


def test_generate_from_demand_skips_in_copyright_without_rendering_unverified_link(tmp_path: Path) -> None:
    plans_dir = _write_plans(
        tmp_path,
        [
            {
                "track": "lit",
                "slug": "modern-poem",
                "title": "Модуль про сучасний вірш",
                "references": [{"title": "Нічний вірш", "author": "Сучасна Авторка"}],
            }
        ],
    )
    db_path = _write_sources_db(
        tmp_path,
        [
            _row(
                chunk_id=10,
                work="Нічний вірш",
                author="Сучасна Авторка",
                year=2020,
                source_file="private-source",
                source_url="https://example.test/modern-poem",
                text=MODERN_TEXT,
            )
        ],
    )
    output_dir = tmp_path / "readings"

    summary = generate_from_demand(plans_dir=plans_dir, output_dir=output_dir, sources_db=db_path)

    assert summary.written == ()
    assert len(summary.skipped) == 1
    assert summary.skipped[0].reason == "in-copyright — needs browser-verified free-full-text link"
    assert not list(output_dir.glob("*.mdx"))


def test_generate_from_demand_skips_missing_corpus_work(tmp_path: Path) -> None:
    plans_dir = _write_plans(
        tmp_path,
        [
            {
                "track": "lit",
                "slug": "missing-work",
                "title": "Модуль про відсутній твір",
                "references": [{"title": "Твір поза корпусом", "author": "Ніхто"}],
            }
        ],
    )
    db_path = _write_sources_db(tmp_path, [])

    summary = generate_from_demand(plans_dir=plans_dir, output_dir=tmp_path / "readings", sources_db=db_path)

    assert summary.written == ()
    assert len(summary.skipped) == 1
    assert summary.skipped[0].reason == "not in corpus"


def test_generate_from_demand_does_not_overwrite_hand_authored_reading(tmp_path: Path) -> None:
    plans_dir = _write_plans(
        tmp_path,
        [
            {
                "track": "lit",
                "slug": "zapovit-module",
                "title": "Модуль про Заповіт",
                "references": [{"title": "Заповіт", "author": "Шевченко Т."}],
            }
        ],
    )
    db_path = _write_sources_db(
        tmp_path,
        [
            _row(
                chunk_id=1,
                work="Заповіт",
                author="Шевченко Т.",
                year=1845,
                source_file="ukrlib-shevchenko",
                text=ZAPOVIT_TEXT,
            )
        ],
    )
    output_dir = tmp_path / "readings"
    output_dir.mkdir()
    slug = _slug("Заповіт", "Шевченко Т.")
    hand_authored = output_dir / f"{slug}.mdx"
    hand_authored.write_text("hand-authored\n", encoding="utf-8")

    summary = generate_from_demand(plans_dir=plans_dir, output_dir=output_dir, sources_db=db_path)

    assert hand_authored.read_text(encoding="utf-8") == "hand-authored\n"
    assert summary.written == ()
    assert [item.action for item in summary.existing] == ["existing-hand-authored"]


def _write_plans(tmp_path: Path, modules: list[dict[str, object]]) -> Path:
    plans_dir = tmp_path / "plans"
    for module in modules:
        track = str(module["track"])
        slug = str(module["slug"])
        title = str(module["title"])
        references = module["references"]
        assert isinstance(references, list)
        track_dir = plans_dir / track
        track_dir.mkdir(parents=True, exist_ok=True)
        lines = [
            f"title: {title}",
            f"grade: {track.upper()}",
            "references:",
        ]
        for reference in references:
            assert isinstance(reference, dict)
            lines.extend(
                [
                    "  - type: primary",
                    f"    title: {reference['title']}",
                    f"    author: {reference['author']}",
                ]
            )
        (track_dir / f"{slug}.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return plans_dir


def _write_sources_db(tmp_path: Path, rows: list[dict[str, object]]) -> Path:
    db_path = tmp_path / "sources.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE literary_texts (
                id INTEGER,
                chunk_id INTEGER,
                title TEXT,
                text TEXT,
                source_file TEXT,
                author TEXT,
                work TEXT,
                work_id TEXT,
                year INTEGER,
                genre TEXT,
                language_period TEXT,
                char_count INTEGER,
                source_url TEXT
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO literary_texts (
                id, chunk_id, title, text, source_file, author, work, work_id, year,
                genre, language_period, char_count, source_url
            )
            VALUES (
                :id, :chunk_id, :title, :text, :source_file, :author, :work, :work_id,
                :year, :genre, :language_period, :char_count, :source_url
            )
            """,
            rows,
        )
    return db_path


def _row(
    *,
    chunk_id: int,
    work: str,
    author: str,
    year: int,
    source_file: str,
    text: str,
    source_url: str | None = None,
) -> dict[str, object]:
    return {
        "id": chunk_id,
        "chunk_id": chunk_id,
        "title": work,
        "text": text,
        "source_file": source_file,
        "author": author,
        "work": work,
        "work_id": f"work-{chunk_id}",
        "year": year,
        "genre": "poem",
        "language_period": "modern",
        "char_count": len(text),
        "source_url": source_url,
    }


def _slug(work: str, author: str) -> str:
    return reading_slug(
        PrimaryReadingCandidate(
            module_dir=Path("."),
            track="lit",
            slug="module",
            author=author,
            title=work,
            note="",
            quote_lines=(),
        )
    )
