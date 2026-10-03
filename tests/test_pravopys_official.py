"""Official Правопис 2019: PDF decoding, structure, storage and offline lookup (#9610).

The book's text is never committed: unit tests use synthetic rows, and the check
against the real PDF runs only when ``LU_PRAVOPYS_2019_PDF`` points at a pinned
official copy (it compares counts and SHA-256 digests, plus the short reviewed list
of words that keep both scripts).
"""

from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
import os
import sqlite3
import sys
import unicodedata
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from ingest import pravopys_2019_ingest
from rag import source_query
from wiki import pravopys_official as po
from wiki import sources_db

SOURCES_SERVER_PATH = Path(__file__).resolve().parents[1] / ".mcp" / "servers" / "sources" / "server.py"
ULIF = po.OFFICIAL_FILES["0d2fd75a2e9b2a412d4c8e072f6a8cac06d075a297a770fd037312054b0e501a"]
A = po.ACUTE


# ── Decoding ─────────────────────────────────────────────────────


def test_cp1251_fonts_are_reread_as_windows_1251() -> None:
    assert po.decode_span_text("BINFBB+1251TimesCondBold", "ÁÓÊÂÅÍ² ÏÎÇÍÀ×ÅÍÍß") == "БУКВЕНІ ПОЗНАЧЕННЯ"
    assert po.decode_span_text("BDFNKJ+1251Times", "¥") == "Ґ"


def test_stressed_vowel_fonts_restore_the_acute_after_each_vowel() -> None:
    font = "BLADJN+1251TimesNewItalic"
    assert po.decode_span_text(font, "è") == "и" + A
    assert po.decode_span_text(font, "ÿ") == "я" + A
    assert po.decode_span_text(font, "þ") == "ю" + A
    assert po.decode_span_text(font, "º") == "є" + A
    assert po.decode_span_text(font, "¿") == "ї" + A
    assert po.decode_span_text(font, "²") == "І" + A
    assert po.decode_span_text(font, "Ó") == "У" + A
    # ASCII (punctuation, digits) in such a span stays as it is.
    assert po.decode_span_text(font, ", 1") == ", 1"


def test_unicode_fonts_are_left_for_the_word_level_pass() -> None:
    assert po.decode_span_text("BDFOCI+TimesNewRoman", "далéко") == "далéко"


def test_latin_stressed_vowels_inside_cyrillic_words_become_cyrillic() -> None:
    assert po.restore_scripts("далéко, вèсоко") == f"дале{A}ко, вèсоко"
    assert po.restore_scripts("Íгор") == f"І{A}гор"
    assert po.restore_scripts("однúм однá") == f"одни{A}м одна{A}"
    assert po.restore_scripts("Сýми") == f"Су{A}ми"
    assert po.restore_scripts("осá") == f"оса{A}"


@pytest.mark.parametrize(
    ("printed", "expected"),
    [
        # Endings set off by hyphens (§ 68, § 115, § 97).
        ("душ-á, душ-í, ім-ен-á", f"душ-а{A}, душ-і{A}, ім-ен-а{A}"),
        ("Дністр-у́ (-о́ві, -í)", f"Дністр-у{A} (-о{A}ві, -і{A})"),
        ("(-ю, -і) (-у́, -í)", f"(-ю, -і) (-у{A}, -і{A})"),
        # A hyphenated word broken after a hyphen (§ 41).
        ("пліч-\nó-пліч, хоч-не-хо́ч", f"пліч-\nо{A}-пліч, хоч-не-хо{A}ч"),
        # Lookalike letters of the other script inside a word (§§ 54, 121, 158, 161, 66).
        ("«Мicrosóft»", "«Microsóft»"),
        ("Cкладені", "Складені"),
        ("[lе]", "[le]"),
        ("ХVІ—ХVІІІ ст.", "XVI—XVIII ст."),
        ("IІІ відміна; ІV відміна", "III відміна; IV відміна"),
    ],
)
def test_every_word_is_restored_to_one_script(printed: str, expected: str) -> None:
    assert po.restore_scripts(printed) == expected


@pytest.mark.parametrize(
    "printed",
    [
        "Gómez і café",
        "PIN-код, веб-API, флеш-BIOS",
        "Польське ó, наявне в суфіксі -ów",  # a cited Latin letter keeps its script
        "-sk-(-i), -ck-(-у́)",
        "-Ø (нульове закінчення)",
        "І відміна",  # one-script words are never touched
    ],
)
def test_printed_latin_and_one_script_words_stay_as_printed(printed: str) -> None:
    assert po.restore_scripts(printed) == unicodedata.normalize("NFC", printed)


def test_endings_on_the_next_row_take_the_script_of_their_word() -> None:
    page = po.PageLayout(page=50, rows=[_row("душ-", page=50, y0=10), _row("á, пліч-", page=50, y0=23),
                                        _row("ó-пліч", page=50, y0=36)],
                         margin_labels=[po.MarginLabel(50, 10, "Cкладені")])
    (restored,) = po.restore_page_scripts([page])
    assert [row.text for row in restored.rows] == ["душ-", f"а{A}, пліч-", f"о{A}-пліч"]
    assert [label.text for label in restored.margin_labels] == ["Складені"]


def test_script_anomalies_report_mixed_words_and_bare_latin_stress() -> None:
    assert po.script_anomalies("душ-á і PIN-код, Польське ó; Gómez, café, душ-а́") == ["душ-á", "PIN-код", "ó"]
    assert po.script_anomalies(f"пліч-\nо{A}-пліч, Microsóft, XVI") == []


# ── Layout ───────────────────────────────────────────────────────


def _line(page: int, x0: float, y0: float, x1: float, size: float, text: str) -> po.PdfLine:
    return po.PdfLine(page=page, x0=x0, y0=y0, x1=x1, size=size, text=text)


def test_layout_drops_running_heads_and_keeps_margin_labels_apart() -> None:
    pages = po.layout_pages([
        _line(12, 231, 31, 363, 8.5, "І. Правопис частин основи слова"),
        _line(12, 188, 63, 192, 8.5, "Ї"),
        _line(12, 237, 56, 445, 11.0, "§ 3. Перший рядок"),
        _line(12, 150, 69, 445, 11.0, "другий рядок"),
        _line(12, 433, 526, 445, 12.0, "12"),
    ])
    (page,) = pages
    assert [row.text for row in page.rows] == ["§ 3. Перший рядок", "другий рядок"]
    assert [label.text for label in page.margin_labels] == ["Ї"]
    assert page.printed_number == "12"


def test_note_size_margin_labels_need_a_body_line_beside_them() -> None:
    pages = po.layout_pages([
        _line(177, 237, 433, 445, 11.0, "9. Перший рядок пункту"),
        _line(177, 181, 439, 199, 9.5, "Ą, Ę"),
        _line(177, 167, 470, 227, 9.5, "останній рядок примітки."),
    ])
    (page,) = pages
    assert [label.text for label in page.margin_labels] == ["Ą, Ę"]
    assert [row.text for row in page.rows] == ["9. Перший рядок пункту", "останній рядок примітки."]


def test_table_cells_on_one_baseline_are_tab_joined() -> None:
    pages = po.layout_pages([
        _line(101, 152, 70.7, 163, 11.0, "Н."),
        _line(101, 200, 70.7, 243, 11.0, "машин-и"),
        _line(101, 296, 71.2, 350, 11.0, "відмінниц-і"),
    ])
    assert pages[0].rows[0].text == "Н.\tмашин-и\tвідмінниц-і"


# ── Contents ─────────────────────────────────────────────────────


def _row(text: str, page: int = 383, x0: float = 150.0, size: float = 11.0, y0: float = 0.0) -> po.Row:
    return po.Row(page=page, x0=x0, y0=y0, size=size, text=text)


def test_contents_parse_paragraphs_headings_parts_and_untitled_entries() -> None:
    toc = po.parse_toc([
        _row("ЗМІСТ"),
        _row("ПЕРЕДМОВА ............................  5"),
        _row("І. ПРАВОПИС ЧАСТИН ОСНОВИ СЛОВА"),
        _row("БУКВЕНІ ПОЗНАЧЕННЯ ДЕЯКИХ ГОЛОСНИХ ЗВУКІВ ........ 11"),
        _row("§ 1. Е, И ..................................... 11"),
        _row("§ 13. Зміни приголосних"),
        _row("(буква Щ) ............................... 22"),
        _row("§ 140 .......................................... 164"),
    ])
    assert [(e.kind, e.number, e.title, e.page) for e in toc] == [
        ("heading", None, "ПЕРЕДМОВА", 5),
        ("part", None, "І. ПРАВОПИС ЧАСТИН ОСНОВИ СЛОВА", None),
        ("heading", None, "БУКВЕНІ ПОЗНАЧЕННЯ ДЕЯКИХ ГОЛОСНИХ ЗВУКІВ", 11),
        ("paragraph", 1, "Е, И", 11),
        ("paragraph", 13, "Зміни приголосних (буква Щ)", 22),
        ("paragraph", 140, "", 164),
    ]


# ── Segmentation ─────────────────────────────────────────────────


def _page(page: int, *rows: po.Row, labels: tuple[po.MarginLabel, ...] = ()) -> po.PageLayout:
    layout = po.PageLayout(page=page)
    layout.rows.extend(rows)
    layout.margin_labels.extend(labels)
    return layout


def test_segmentation_follows_paragraph_numbers_and_headings() -> None:
    toc = [po.TocEntry("heading", None, "А. Однина", 20), po.TocEntry("heading", None, "ЧЕРГУВАННЯ", 20)]
    pages = [
        _page(
            20,
            _row("І. ЧАСТИНА", page=20, size=15.0, y0=30),
            _row("ЧЕРГУВАННЯ", page=20, size=12.5, y0=60),
            _row("Вступ до групи.", page=20, y0=80),
            _row("А. Однина", page=20, x0=271, y0=100),
            _row("§ 1. Перше правило з по-", page=20, x0=237, y0=120),
            _row("силанням на", page=20, y0=133),
            _row("§ 3. Це посилання, не новий параграф.", page=20, y0=146),
            _row("Підзаголовок у параграфі", page=20, size=12.0, y0=170),
            _row("Текст після підзаголовка.", page=20, y0=190),
            _row("§ 2. Друге правило.", page=20, x0=237, y0=210),
            labels=(po.MarginLabel(20, 125, "Е, И"),),
        )
    ]
    sections, paragraphs = po.segment_body(pages, toc, expected_count=2)
    assert [(s.level, s.title, s.parent_ordinal) for s in sections] == [
        (1, "І. ЧАСТИНА", None),
        (2, "ЧЕРГУВАННЯ", 1),
        (4, "А. Однина", 2),
    ]
    assert [row.text for row in sections[1].rows] == ["Вступ до групи."]
    first, second = paragraphs
    assert first.number == 1 and first.section_ordinal == 3
    assert [row.text for row in first.rows][-2:] == ["Підзаголовок у параграфі", "Текст після підзаголовка."]
    assert "§ 3. Це посилання, не новий параграф." in [row.text for row in first.rows]
    assert [label.text for label in first.margin_labels] == ["Е, И"]
    assert second.number == 2


def test_segmentation_refuses_a_count_that_differs_from_the_contents() -> None:
    pages = [_page(11, _row("ГРУПА", page=11, size=12.5), _row("§ 1. Правило.", page=11, x0=237))]
    with pytest.raises(po.PravopysParseError, match="expected 2"):
        po.segment_body(pages, expected_count=2)


def test_longest_listed_heading_wins() -> None:
    toc = [
        po.TocEntry("heading", None, "ЧЕРГУВАННЯ ГОЛОСНИХ", 14),
        po.TocEntry("heading", None, "Чергування голосних у дієслівних коренях", 19),
    ]
    pages = [
        _page(
            19,
            _row("ГРУПА", page=19, size=12.5, y0=10),
            _row("§ 1. Правило.", page=19, x0=237, y0=20),
            _row("ЧЕРГУВАННЯ ГОЛОСНИХ", page=19, x0=224, size=10.5, y0=40),
            _row("У ДІЄСЛІВНИХ КОРЕНЯХ", page=19, x0=230, size=10.5, y0=54),
            _row("§ 2. Наступне правило.", page=19, x0=237, y0=70),
        )
    ]
    sections, paragraphs = po.segment_body(pages, toc, expected_count=2)
    assert sections[-1].title == "ЧЕРГУВАННЯ ГОЛОСНИХ У ДІЄСЛІВНИХ КОРЕНЯХ"
    assert [row.text for row in paragraphs[0].rows] == ["§ 1. Правило."]


# ── Line-end hyphens ─────────────────────────────────────────────

LEXICON = {"виразні", "по-сусідському", "година", "дві", "шліфувальний", "ходив"}


def _is_word(form: str) -> bool:
    return form in LEXICON


@pytest.mark.parametrize(
    ("rows", "expected", "alternatives"),
    [
        (["голосні ви-", "разні."], "голосні виразні.", []),
        (["жити по-", "сусідському"], "жити по-сусідському", []),
        (["у Нью-", "Йорку"], "у Нью-Йорку", ["НьюЙорку"]),
        (["суфікс -шк-", "змінюємо"], "суфікс -шк- змінюємо", ["шкзмінюємо"]),
        (["година-", "дві"], "година-дві", ["годинадві"]),
        (["свердлильно-", "шліфувальний"], "свердлильно-шліфувальний", ["свердлильношліфувальний"]),
        (["місто Хар-", "ків"], "місто Харків", ["Хар-ків"]),
        ([f"Бе{A}рклі-", "сквер"], f"Бе{A}рклісквер", [f"Бе{A}рклі-сквер"]),
    ],
)
def test_line_end_hyphens(rows: list[str], expected: str, alternatives: list[str]) -> None:
    """Every hyphen the lexicon does not decide keeps the reading the rules did not choose."""
    built = [_row(text, x0=150, y0=13.0 * index) for index, text in enumerate(rows)]
    assert po.normalized_text(built, _is_word) == (expected, alternatives)


def test_indented_rows_notes_and_points_start_new_lines() -> None:
    rows = [
        _row("§ 7. Початок", x0=237),
        _row("продовження.", x0=150),
        _row("1. Пункт", x0=167),
        _row("далі.", x0=150),
        _row("Примітка. Текст", x0=167),
        _row("Примітка 2. Ще", x0=167),
    ]
    text, _ = po.normalized_text(rows, _is_word)
    assert text == "§ 7. Початок продовження.\n1. Пункт далі.\nПримітка. Текст\nПримітка 2. Ще"


# ── Storage and offline lookup ───────────────────────────────────

SAMPLE_TITLES = {
    7: "Апостроф",
    23: "Уживання прийменників У, В і початкових У-, В-",
    26: "Пишемо Ь",
    74: "Кличний відмінок",
    139: "М’який знак (ь)",
    140: "",
    158: "Кома (,)",
}


def _synthetic_edition() -> po.ParsedEdition:
    sections = [
        po.Section(1, 1, "І. ЧАСТИНА", 11, None),
        po.Section(2, 2, "УЖИВАННЯ М’ЯКОГО ЗНАКА (Ь)", 31, 1),
        po.Section(3, 1, "V. УЖИВАННЯ РОЗДІЛОВИХ ЗНАКІВ", 197, None, rows=[_row("Вступ.", page=197)]),
    ]
    paragraphs = []
    toc: list[po.TocEntry] = []
    for number in range(1, po.TOC_PARAGRAPH_COUNT + 1):
        page = 10 + number
        section = 2 if 26 <= number <= 30 else (3 if number >= 155 else 1)
        rows = [
            _row(f"§ {number}. Синтетичний текст параграфа {number} з пере-", page=page, x0=237, y0=50),
            _row("носом.", page=page, y0=63),
            _row("Кінець.", page=page + 1, y0=50),
        ]
        paragraphs.append(po.Paragraph(number, page, section, rows=rows))
        toc.append(po.TocEntry("paragraph", number, SAMPLE_TITLES.get(number, f"Тема {number}"), page))
    return po.ParsedEdition(sections, paragraphs, toc, [])


@pytest.fixture
def stored_db(tmp_path: Path) -> Path:
    db = tmp_path / "sources.db"
    conn = sqlite3.connect(db)
    counts = po.store_edition(
        conn, _synthetic_edition(), ULIF, retrieved_at="2026-10-03T15:05:00Z", is_word=lambda f: f == "переносом."
    )
    conn.close()
    assert counts == po.IngestCounts(paragraphs=168, sections=3, toc_paragraphs=168, unresolved_hyphenations=168)
    return db


def test_every_paragraph_is_stored_with_locator_and_hash(stored_db: Path) -> None:
    conn = sqlite3.connect(stored_db)
    rows = conn.execute(
        "SELECT number, locator, text, text_sha256, page_start, page_end FROM pravopys_paragraphs ORDER BY number"
    ).fetchall()
    assert [row[0] for row in rows] == list(range(1, 169))
    _number, locator, text, digest, start, end = rows[6]
    assert locator == "Український правопис. Київ: Наукова думка, 2019, § 7, с. 17–18"
    assert digest == hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert (start, end) == (17, 18)
    source = conn.execute("SELECT file_sha256, retrieved_at, toc_paragraph_count FROM pravopys_sources").fetchone()
    assert source == (ULIF.sha256, "2026-10-03T15:05:00Z", 168)
    conn.close()


def test_storing_again_replaces_the_edition(stored_db: Path) -> None:
    conn = sqlite3.connect(stored_db)
    po.store_edition(conn, _synthetic_edition(), ULIF, retrieved_at="2026-10-04T00:00:00Z")
    assert conn.execute("SELECT COUNT(*) FROM pravopys_paragraphs").fetchone()[0] == 168
    assert conn.execute("SELECT retrieved_at FROM pravopys_sources").fetchone()[0] == "2026-10-04T00:00:00Z"
    conn.close()


def test_store_refuses_an_edition_that_disagrees_with_the_contents(tmp_path: Path) -> None:
    parsed = _synthetic_edition()
    parsed.toc[6] = po.TocEntry("paragraph", 7, "Апостроф", 99)
    conn = sqlite3.connect(tmp_path / "sources.db")
    with pytest.raises(po.PravopysParseError, match=r"§ 7: contents p\. 99"):
        po.store_edition(conn, parsed, ULIF, retrieved_at="2026-10-03T15:05:00Z")
    assert conn.execute("SELECT name FROM sqlite_master WHERE name = 'pravopys_paragraphs'").fetchone() is None
    conn.close()


@pytest.mark.parametrize(
    ("topic", "number"),
    [
        ("апостроф", 7),
        ("м-який-знак", 26),
        ("м’який знак", 26),
        ("у-в", 23),
        ("кличний відмінок", 74),
        ("кома", 158),
        ("140", 140),
        ("§ 158", 158),
    ],
)
def test_offline_lookup_answers_topics_and_numbers(stored_db: Path, topic: str, number: int) -> None:
    result = source_query.pravopys_offline(topic, db_path=str(stored_db))
    assert result["status"] == "ok" and result["source"] == "offline"
    assert result["section"] == number
    assert result["url"] == po.ULIF_PDF_URL
    assert result["text"].startswith(f"§ {number}. Синтетичний текст")
    assert "\n" in result["text"]  # the printed lines, not the joined reading text
    assert f"§ {number}," in result["locator"]


def test_search_finds_both_readings_of_an_unresolved_line_end_hyphen(tmp_path: Path) -> None:
    parsed = _synthetic_edition()
    parsed.paragraphs[49].rows[1:2] = [_row(f"Бе{A}рклі-", page=60, y0=63), _row("сквер.", page=60, y0=76)]
    conn = sqlite3.connect(tmp_path / "sources.db")
    po.store_edition(conn, parsed, ULIF, retrieved_at="2026-10-03T15:05:00Z")
    stored = conn.execute("SELECT text, text_normalized, hyphen_alternatives FROM pravopys_paragraphs "
                          "WHERE number = 50").fetchone()
    assert f"Бе{A}рклі-\nсквер." in stored[0]  # the printed text is unchanged
    assert f"Бе{A}рклісквер." in stored[1]
    assert f"Бе{A}рклі-сквер" in json.loads(stored[2])
    assert [hit["section"] for hit in po.search_paragraphs(conn, "сквер")] == [50]
    assert [hit["section"] for hit in po.search_paragraphs(conn, "берклісквер")] == [50]
    conn.close()


def test_storing_over_parser_v1_tables_adds_the_alternatives_column(tmp_path: Path) -> None:
    conn = sqlite3.connect(tmp_path / "sources.db")
    conn.executescript(po.PRAVOPYS_SCHEMA_SQL.replace("    hyphen_alternatives TEXT NOT NULL DEFAULT '[]',\n", ""))
    assert "hyphen_alternatives" not in {row[1] for row in conn.execute("PRAGMA table_info(pravopys_paragraphs)")}
    po.store_edition(conn, _synthetic_edition(), ULIF, retrieved_at="2026-10-03T15:05:00Z")
    assert conn.execute("SELECT COUNT(*) FROM pravopys_paragraphs WHERE hyphen_alternatives != '[]'").fetchone()[0]
    assert conn.execute("SELECT parser_version FROM pravopys_sources").fetchone()[0] == po.PARSER_VERSION
    conn.close()


def test_offline_lookup_misses_and_unavailable_store(stored_db: Path, tmp_path: Path) -> None:
    assert source_query.pravopys_offline("169", db_path=str(stored_db)) is None
    assert source_query.pravopys_offline("ґрунтовщина", db_path=str(stored_db)) is None
    missing = source_query.pravopys_offline("апостроф", db_path=str(tmp_path / "absent.db"))
    assert missing == {"status": "store_unavailable", "reason": "no sources.db"}
    empty = tmp_path / "other.db"
    sqlite3.connect(empty).execute("CREATE TABLE t (x)").connection.close()
    assert source_query.pravopys_offline("апостроф", db_path=str(empty))["reason"] == "missing_table"


def test_a_partial_edition_is_not_served(stored_db: Path) -> None:
    conn = sqlite3.connect(stored_db)
    with conn:
        conn.execute("DELETE FROM pravopys_paragraphs WHERE number = 168")
    conn.close()
    result = source_query.pravopys_offline("7", db_path=str(stored_db))
    assert result == {"status": "store_unavailable", "reason": "incomplete"}


# ── MCP tool ─────────────────────────────────────────────────────


@pytest.fixture
def server_module():
    spec = importlib.util.spec_from_file_location("sources_server_pravopys", SOURCES_SERVER_PATH)
    srv = importlib.util.module_from_spec(spec)
    sys.modules["sources_server_pravopys"] = srv
    spec.loader.exec_module(srv)
    return srv


def _no_live(*_args, **_kwargs):
    raise AssertionError("the live site must not be called when the official text is stored")


@pytest.mark.parametrize(
    ("topic", "number"),
    [("апостроф", 7), ("м’який знак", 26), ("у-в", 23), ("кличний відмінок", 74), ("кома", 158)],
)
def test_query_pravopys_answers_five_topics_from_local_data(
    server_module, stored_db: Path, monkeypatch: pytest.MonkeyPatch, topic: str, number: int
) -> None:
    monkeypatch.setattr(sources_db, "SOURCES_DB_PATH", stored_db)
    with (
        patch("rag.source_query.pravopys_section", side_effect=_no_live),
        patch("rag.source_query.pravopys_lookup", side_effect=_no_live),
    ):
        content, envelope = asyncio.run(server_module.handle_query_pravopys({"topic": topic}))
    prose = content[0].text
    assert prose.startswith(f"**Український правопис (2019), § {number}")
    assert "official authorized edition" in prose
    assert f"Наукова думка, 2019, § {number}, с." in prose
    assert envelope["hits"][0]["section"] == number
    assert envelope["hits"][0]["source"] == "offline"


def test_query_pravopys_real_miss_does_not_go_live(server_module, stored_db: Path, monkeypatch) -> None:
    monkeypatch.setattr(sources_db, "SOURCES_DB_PATH", stored_db)
    with patch("rag.source_query.pravopys_section", side_effect=_no_live):
        content, envelope = asyncio.run(server_module.handle_query_pravopys({"topic": "169"}))
    assert content[0].text == "No pravopys section found for: '169'"
    assert envelope["hits"] == []


def test_query_pravopys_falls_back_to_the_live_site_without_a_stored_edition(
    server_module, tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(sources_db, "SOURCES_DB_PATH", tmp_path / "absent.db")
    live = {"section": 7, "url": "https://2019.pravopys.net/sections/7/", "text": "live text"}
    with patch("rag.source_query.pravopys_section", return_value=live) as fetch:
        content, _envelope = asyncio.run(server_module.handle_query_pravopys({"topic": "7"}))
    fetch.assert_called_once_with(7, report_unavailable=True)
    assert "unofficial copy, live fallback" in content[0].text
    assert "no sources.db" in content[0].text


# ── Ingest CLI ───────────────────────────────────────────────────


def test_ingest_refuses_a_file_that_is_not_pinned(tmp_path: Path, capsys) -> None:
    pdf = tmp_path / "other.pdf"
    pdf.write_bytes(b"%PDF-1.4 not the official file")
    code = pravopys_2019_ingest.main(["--pdf", str(pdf), "--retrieved-at", "2026-10-03T00:00:00Z", "--dry-run"])
    assert code == 1
    assert "is not a pinned official file" in capsys.readouterr().err


def test_ingest_requires_retrieval_time_and_db(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        pravopys_2019_ingest.main(["--pdf", str(tmp_path / "x.pdf"), "--dry-run"])
    with pytest.raises(SystemExit):
        pravopys_2019_ingest.main(["--pdf", str(tmp_path / "x.pdf"), "--retrieved-at", "2026-10-03T00:00:00Z"])


def test_fetch_discards_a_download_with_the_wrong_hash(tmp_path: Path) -> None:
    class Response:
        content = b"changed file"

        def raise_for_status(self) -> None:
            return None

    with (
        patch.object(pravopys_2019_ingest.requests, "get", return_value=Response()),
        pytest.raises(pravopys_2019_ingest.PravopysParseError, match="not the pinned official file"),
    ):
        pravopys_2019_ingest.fetch_official_pdf(tmp_path)
    assert list(tmp_path.iterdir()) == []


# ── The real official PDF (local only) ───────────────────────────

REAL_PDF = os.environ.get("LU_PRAVOPYS_2019_PDF")
# SHA-256 of each §'s printed text as parsed from the pinned PDF (hashes only, no text).
LAYOUT_MANIFEST = Path(__file__).parent / "fixtures" / "pravopys_2019_layout_sha256.json"
# The reviewed words that keep both scripts (or a bare Latin stressed vowel), per §.
SCRIPT_ALLOWLIST = Path(__file__).parent / "fixtures" / "pravopys_2019_script_allowlist.json"


@pytest.mark.skipif(not REAL_PDF, reason="set LU_PRAVOPYS_2019_PDF to a pinned official copy")
def test_real_pdf_yields_every_paragraph_of_the_contents() -> None:
    pdf = Path(REAL_PDF)
    official = pravopys_2019_ingest.official_file_for(pdf)
    parsed = po.parse_edition(pdf, official)
    assert po.validate_against_toc(parsed) == []
    assert [p.number for p in parsed.paragraphs] == list(range(1, 169))
    receipt = {p.number: hashlib.sha256(po.layout_text(p.rows).encode()).hexdigest() for p in parsed.paragraphs}
    manifest = json.loads(LAYOUT_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["parser_version"] == po.PARSER_VERSION
    assert receipt == {int(k): v for k, v in manifest["paragraphs"].items()}


@pytest.mark.skipif(not REAL_PDF, reason="set LU_PRAVOPYS_2019_PDF to a pinned official copy")
def test_real_pdf_words_are_in_one_script_except_reviewed_printed_latin() -> None:
    pdf = Path(REAL_PDF)
    parsed = po.parse_edition(pdf, pravopys_2019_ingest.official_file_for(pdf))
    allowlist = json.loads(SCRIPT_ALLOWLIST.read_text(encoding="utf-8"))
    assert allowlist["parser_version"] == po.PARSER_VERSION

    def found(texts_by_key: dict[str, list[str]]) -> dict[str, list[str]]:
        hits = {key: sorted(w for text in texts for w in po.script_anomalies(text)) for key, texts in texts_by_key.items()}
        return {key: words for key, words in hits.items() if words}

    paragraphs = found({str(p.number): [po.layout_text(p.rows)] for p in parsed.paragraphs})
    labels = found({str(p.number): [label.text for label in p.margin_labels] for p in parsed.paragraphs})
    sections = found({str(s.ordinal): [s.title, po.layout_text(s.rows)] for s in parsed.sections})
    assert paragraphs == {key: sorted(words) for key, words in allowlist["paragraphs"].items()}
    assert labels == {key: sorted(words) for key, words in allowlist["margin_labels"].items()}
    assert sections == {}
