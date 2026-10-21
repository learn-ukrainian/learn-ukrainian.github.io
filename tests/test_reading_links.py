"""Tests for hosted reading cross-linking."""

from __future__ import annotations

from pathlib import Path

from scripts.generate_mdx import core
from scripts.generate_mdx.reading_links import reading_href_for


def _write_reading(
    path: Path,
    *,
    title: str,
    title_en: str = "",
    published: bool | None = None,
    canonical: bool | None = None,
) -> None:
    def quote(value: str) -> str:
        return "'" + value.replace("'", "''") + "'"

    title_en_line = f"title_en: {quote(title_en)}\n" if title_en else ""
    published_line = f"published: {str(published).lower()}\n" if published is not None else ""
    canonical_line = f"canonical: {str(canonical).lower()}\n" if canonical is not None else ""
    path.write_text(
        "---\n"
        f"title: {quote(title)}\n"
        f"{title_en_line}"
        'genre: "Колядка"\n'
        'tracks: ["folk"]\n'
        'excerpt: "excerpt"\n'
        'source: "source"\n'
        "public_domain: true\n"
        f"{published_line}"
        f"{canonical_line}"
        "---\n",
        encoding="utf-8",
    )


def test_reading_href_ignores_unpublished_or_noncanonical_readings(tmp_path):
    _write_reading(
        tmp_path / "hidden-unpublished.mdx",
        title="«Прихований неопублікований текст»",
        published=False,
    )
    _write_reading(
        tmp_path / "hidden-noncanonical.mdx",
        title="«Прихований неканонічний текст»",
        canonical=False,
    )
    _write_reading(
        tmp_path / "visible-reading.mdx",
        title="«Видимий текст»",
    )

    assert reading_href_for("Прихований неопублікований текст", tmp_path) is None
    assert reading_href_for("Прихований неканонічний текст", tmp_path) is None
    assert reading_href_for("Видимий текст", tmp_path) == "/readings/visible-reading/"


def test_plan_readings_block_is_integrity_gated(monkeypatch):
    monkeypatch.setattr(
        core,
        "reading_href_for",
        lambda slug: f"/readings/{slug}/" if slug == "koliadka-yak-shche-ne-bulo" else None,
    )

    out = core._format_plan_readings_for_mdx(
        [
            {
                "title": "«Як ще не було початку світа»",
                "title_en": "When the world had no beginning",
                "genre": "Колядка",
                "reading_slug": "koliadka-yak-shche-ne-bulo",
            },
            {
                "title": "Broken",
                "genre": "Колядка",
                "reading_slug": "missing",
            },
        ]
    )

    assert "**Тексти для читання**" in out
    assert "/readings/koliadka-yak-shche-ne-bulo/" in out
    assert "Колядка" in out
    assert "When world had no beginning" not in out
    assert "Broken" not in out
