"""Tests for hosted reading cross-linking."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.generate_mdx import converters, core
from scripts.generate_mdx.reading_links import normalize_work_title, reading_href_for


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


@pytest.fixture
def readings_dir(tmp_path):
    _write_reading(
        tmp_path / "koliadka-yak-shche-ne-bulo.mdx",
        title="«Як ще не було початку світа» (космогонічна колядка)",
        title_en='"When the world had no beginning" (cosmogonic carol)',
    )
    _write_reading(
        tmp_path / "shchedrivka-oi-syvaia-ta-i-zozulechka.mdx",
        title="«Ой сивая та і зозулечка» (щедрівка з тріадою світил)",
    )
    return tmp_path


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("«Як ще не було початку світа»", "як ще не було початку світа"),
        ("ЯК ЩЕ НЕ БУЛО ПОЧАТКУ СВІТА", "як ще не було початку світа"),
        ("сві́та", "світа"),
        ("koliadka-yak-shche-ne-bulo", "koliadka yak shche ne bulo"),
        ("  “When the world had no beginning”  ", "when the world had no beginning"),
    ],
)
def test_normalize_work_title(raw, expected):
    assert normalize_work_title(raw) == expected


def test_reading_href_matches_inner_quoted_title(readings_dir):
    assert reading_href_for("Як ще не було початку світа", readings_dir) == "/readings/koliadka-yak-shche-ne-bulo/"


def test_reading_href_matches_english_title(readings_dir):
    assert reading_href_for("When the world had no beginning", readings_dir) == "/readings/koliadka-yak-shche-ne-bulo/"


def test_reading_href_matches_file_slug(readings_dir):
    assert (
        reading_href_for("shchedrivka-oi-syvaia-ta-i-zozulechka", readings_dir)
        == "/readings/shchedrivka-oi-syvaia-ta-i-zozulechka/"
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


def test_reading_href_no_file_returns_none(readings_dir):
    assert reading_href_for("неіснуючий текст", readings_dir) is None


def test_reading_href_missing_directory_returns_none(tmp_path):
    assert reading_href_for("Як ще не було початку світа", tmp_path / "missing") is None


def test_primary_reading_uses_attribution_title(monkeypatch):
    def fake_href(work):
        return "/readings/koliadka-yak-shche-ne-bulo/" if work == "Як ще не було початку світа" else None

    monkeypatch.setattr(converters, "reading_href_for", fake_href)
    out = converters.convert_folk_content_blocks(
        ":::primary-reading\n"
        "> Як ще не було початку світа,\n\n"
        "— Народна творчість, «Як ще не було початку світа» (космогонічна колядка)\n"
        ":::\n"
    )

    assert '<PrimaryReading href="/readings/koliadka-yak-shche-ne-bulo/">' in out


def test_primary_reading_prefers_explicit_reading_attr(monkeypatch):
    calls = []

    def fake_href(work):
        calls.append(work)
        return "/readings/shchedrivka-oi-syvaia-ta-i-zozulechka/"

    monkeypatch.setattr(converters, "reading_href_for", fake_href)
    out = converters.convert_folk_content_blocks(
        ':::primary-reading{reading="shchedrivka-oi-syvaia-ta-i-zozulechka"}\n'
        "> Щедрий вечір, добрий вечір,\n\n"
        "— Народна творчість, «Неповна назва»\n"
        ":::\n"
    )

    assert calls == ["shchedrivka-oi-syvaia-ta-i-zozulechka"]
    assert (
        '<PrimaryReading id="reading-shchedrivka-oi-syvaia-ta-i-zozulechka" '
        'href="/readings/shchedrivka-oi-syvaia-ta-i-zozulechka/">'
    ) in out


def test_primary_reading_omits_missing_link(monkeypatch):
    monkeypatch.setattr(converters, "reading_href_for", lambda _work: None)
    out = converters.convert_folk_content_blocks(
        ":::primary-reading\n"
        "> Missing\n\n"
        "— Народна творчість, «Missing»\n"
        ":::\n"
    )

    assert "<PrimaryReading>" in out
    assert "href=" not in out


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


def test_plan_readings_block_falls_back_to_structured_inline_readings(monkeypatch):
    monkeypatch.setattr(core, "reading_href_for", lambda slug: None)
    monkeypatch.setattr(core, "reading_title_for", lambda slug: None)

    out = core._format_plan_readings_for_mdx(
        [],
        ':::primary-reading{reading="kryvyi-tanets-kintsia-ne-znaidemo-fragment"}\n'
        "> Кривого танця йдемо,\n\n"
        "— Михайло Грушевський, «Кривого танця йдемо»; права: суспільне надбання.\n"
        ":::\n",
        include_inline=True,
    )

    assert "**Тексти для читання**" in out
    assert (
        "- [Кривого танця йдемо](#reading-kryvyi-tanets-kintsia-ne-znaidemo-fragment) "
        "— уривок у цьому модулі"
    ) in out


def test_plan_readings_block_uses_first_quoted_line_when_attribution_has_no_title(monkeypatch):
    monkeypatch.setattr(core, "reading_href_for", lambda slug: None)
    monkeypatch.setattr(core, "reading_title_for", lambda slug: None)

    out = core._format_plan_readings_for_mdx(
        [],
        ':::primary-reading{reading="pysanky-velykodnii-dar-fragment"}\n'
        "> Христос воскрес, о тім\n"
        "> знайте\n\n"
        "— Антологія давньої української літератури; права: суспільне надбання.\n"
        ":::\n",
        include_inline=True,
    )

    assert "[Христос воскрес, о тім](#reading-pysanky-velykodnii-dar-fragment)" in out
    assert "pysanky velykodnii dar fragment" not in out


def test_plan_readings_block_uses_hosted_reading_title(monkeypatch):
    monkeypatch.setattr(
        core,
        "reading_href_for",
        lambda slug: f"/readings/{slug}/" if slug == "hnatiuk-kolomyiky-variantni-pryklady" else None,
    )
    monkeypatch.setattr(
        core,
        "reading_title_for",
        lambda slug: "Приклади коломийкового співу у Володимира Гнатюка"
        if slug == "hnatiuk-kolomyiky-variantni-pryklady"
        else None,
    )

    out = core._format_plan_readings_for_mdx(
        [],
        ':::primary-reading{reading="hnatiuk-kolomyiky-variantni-pryklady"}\n'
        "Скорочений уривок із друкованого джерела відкрито в хрестоматії.\n\n"
        "— Народна творчість; приклади з видання \"Коломийки. Том I\"; права: public domain.\n"
        ":::\n",
        include_inline=True,
    )

    assert (
        "[Приклади коломийкового співу у Володимира Гнатюка]"
        "(/readings/hnatiuk-kolomyiky-variantni-pryklady/)"
    ) in out
    assert "hnatiuk kolomyiky variantni pryklady" not in out


def test_plan_readings_block_accepts_explicit_inline_title(monkeypatch):
    monkeypatch.setattr(core, "reading_href_for", lambda slug: None)
    monkeypatch.setattr(core, "reading_title_for", lambda slug: None)

    out = core._format_plan_readings_for_mdx(
        [],
        ':::primary-reading{reading="hnatiuk-nai-pan-znaie-hryts-uzhyvav" title="Хай пан знає, що Гриць уживав"}\n'
        "> Вкрав Гриць пацюка в дворі і зарізав і тримав го дома.\n\n"
        "— В. Гнатюк, «Етнографічний\\nзбірник»; права: суспільне надбання.\n"
        ":::\n",
        include_inline=True,
    )

    assert (
        "[Хай пан знає, що Гриць уживав](#reading-hnatiuk-nai-pan-znaie-hryts-uzhyvav)"
        in out
    )
    assert "Етнографічний" not in out


def test_plan_readings_block_uses_inline_title_override(monkeypatch):
    monkeypatch.setattr(core, "reading_href_for", lambda slug: None)
    monkeypatch.setattr(core, "reading_title_for", lambda slug: None)

    out = core._format_plan_readings_for_mdx(
        [],
        ':::primary-reading{reading="hnatiuk-nai-pan-znaie-hryts-uzhyvav"}\n'
        "> Вкрав Гриць пацюка в дворі і зарізав і тримав го дома.\n\n"
        "— В. Гнатюк, «Етнографічний\\nзбірник»; права: суспільне надбання.\n"
        ":::\n",
        include_inline=True,
    )

    assert (
        "[Хай пан знає, що Гриць уживав](#reading-hnatiuk-nai-pan-znaie-hryts-uzhyvav)"
        in out
    )
    assert "Етнографічний" not in out


def test_plan_readings_block_uses_plain_text_inline_title_override(monkeypatch):
    monkeypatch.setattr(core, "reading_href_for", lambda slug: None)
    monkeypatch.setattr(core, "reading_title_for", lambda slug: None)

    out = core._format_plan_readings_for_mdx(
        [],
        ':::primary-reading{reading="chumatska-pisnia-idut-voly-iz-za-hory"}\n'
        "Ідуть воли із-за гори та все половії,\n"
        "А ярема попереду, та й поганяє.\n\n"
        "— Народна творчість; права: суспільне надбання.\n"
        ":::\n",
        include_inline=True,
    )

    assert "[Ідуть воли із-за гори](#reading-chumatska-pisnia-idut-voly-iz-za-hory)" in out
    assert "chumatska pisnia" not in out


def test_plan_readings_block_deduplicates_plan_and_inline_readings(monkeypatch):
    monkeypatch.setattr(
        core,
        "reading_href_for",
        lambda slug: f"/readings/{slug}/" if slug == "shared-reading" else None,
    )
    monkeypatch.setattr(core, "reading_title_for", lambda slug: None)

    out = core._format_plan_readings_for_mdx(
        [
            {
                "title": "«Плановий текст»",
                "genre": "Пісня",
                "reading_slug": "shared-reading",
            }
        ],
        ':::primary-reading{reading="shared-reading"}\n'
        "> Рядок.\n\n"
        "— Народна творчість, «Інша назва»; права: суспільне надбання.\n"
        ":::\n",
        include_inline=True,
    )

    assert out.count("shared-reading") == 1
    assert "Інша назва" not in out
