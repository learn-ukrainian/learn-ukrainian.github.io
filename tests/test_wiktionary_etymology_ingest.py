import bz2
import sqlite3
from pathlib import Path
from xml.sax.saxutils import escape

from scripts.ingest.goroh_etymology_ingest import ensure_goroh_etymology_schema, upsert_goroh_row
from scripts.ingest.wiktionary_etymology_ingest import (
    WIKTIONARY_DUMP_DATE,
    WiktionaryPage,
    content_hash,
    ensure_wiktionary_etymology_schema,
    ingest_wiktionary_etymology,
    lookup_key,
    parse_wiktionary_page,
    upsert_wiktionary_row,
)
from scripts.lexicon.enrich_manifest import _etymology, _single_word_etymology_coverage


def _write_dump(tmp_path: Path, pages: list[tuple[str, str, str]]) -> Path:
    body = "\n".join(
        f"""
        <page>
          <title>{escape(title)}</title>
          <ns>{ns}</ns>
          <revision>
            <text xml:space="preserve">{escape(text)}</text>
          </revision>
        </page>
        """
        for title, ns, text in pages
    )
    path = tmp_path / "ukwiktionary-test.xml.bz2"
    with bz2.open(path, "wt", encoding="utf-8") as fh:
        fh.write(f'<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.11/">\n{body}\n</mediawiki>')
    return path


def _wiktionary_row(requested_lemma: str, text: str) -> dict[str, str]:
    return {
        "requested_lemma": requested_lemma,
        "headword": requested_lemma,
        "lang": "uk",
        "etymology_text": text,
        "section_raw": text,
        "source_url": f"https://uk.wiktionary.org/wiki/{requested_lemma}",
        "dump_date": WIKTIONARY_DUMP_DATE,
        "retrieved_at": "2026-06-01T00:00:00+00:00",
        "content_hash": content_hash(text),
    }


def _conn_with_etymology_tables() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    ensure_goroh_etymology_schema(conn)
    ensure_wiktionary_etymology_schema(conn)
    conn.execute(
        """
        CREATE TABLE esum_etymology (
            lemma TEXT NOT NULL,
            etymology_text TEXT NOT NULL DEFAULT '',
            vol TEXT DEFAULT '',
            page TEXT DEFAULT ''
        )
        """
    )
    return conn


def test_wiktionary_schema_and_ingest_are_idempotent_with_phrase_skip(tmp_path: Path) -> None:
    dump = _write_dump(
        tmp_path,
        [
            (
                "робота",
                "0",
                """
                {{=uk=}}
                ===Морфосинтаксичні ознаки===
                {{імен uk}}
                ===Етимологія===
                {{етимологія:робити|uk}}
                ===Переклад===
                {{переклад|дія}}
                """,
            ),
            (
                "Шаблон:етимологія:робити",
                "10",
                "Від слова [[раб]] (давньо-руською робъ).<noinclude>[[Категорія:Шаблони етимології|робити]]</noinclude>",
            ),
        ],
    )
    db_path = tmp_path / "sources.db"

    conn = sqlite3.connect(db_path)
    ensure_wiktionary_etymology_schema(conn)
    ensure_wiktionary_etymology_schema(conn)
    conn.close()

    scanned, loaded, skipped = ingest_wiktionary_etymology(
        db_path,
        dump,
        ["Добрий день", "робота"],
        refresh=False,
        dry_run=False,
        max_text_chars=1200,
    )
    assert (scanned, loaded, skipped) == (1, 1, 1)

    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT requested_lemma, headword, etymology_text, section_raw FROM wiktionary_etymology"
    ).fetchone()
    assert row[0] == "робота"
    assert row[1] == "робота"
    assert "раб" in row[2]
    assert "Категорія" not in row[2]
    assert not row[2].endswith("робити")
    assert "{{етимологія:робити|uk}}" in row[3]

    scanned_again, loaded_again, skipped_again = ingest_wiktionary_etymology(
        db_path,
        dump,
        ["Добрий день", "робота"],
        refresh=False,
        dry_run=False,
        max_text_chars=1200,
    )
    assert (scanned_again, loaded_again, skipped_again) == (0, 0, 1)
    assert conn.execute("SELECT count(*) FROM wiktionary_etymology").fetchone()[0] == 1
    conn.close()


def test_multilingual_numbered_etymology_extracts_only_ukrainian_section() -> None:
    page = WiktionaryPage(
        title="комп’ютер",
        text="""
        {{=en=}}
        ===Etymology===
        English text must not leak.

        {{=uk=}}
        ===Семантичні властивості===
        ==== Значення ====
        # пристрій
        ===Етимологія 1===
        Від {{етимологія:комп’ютер|uk}}.
        ===Етимологія 2===
        Також пов'язане з [[рахунок|рахунком]].

        {{=pl=}}
        ===Etymologia===
        Polish text must not leak.
        """,
    )
    row = parse_wiktionary_page(
        page,
        requested_lemma="комп'ютер",
        template_map={
            lookup_key("етимологія:комп’ютер"): '{{lang-en|[[дієслово|дієсл.]] to [[compute]]}} – "обчислити"'
        },
    )

    assert row is not None
    assert row["requested_lemma"] == "комп'ютер"
    assert row["headword"] == "комп’ютер"
    assert "English text" not in row["etymology_text"]
    assert "Polish text" not in row["etymology_text"]
    assert "англ." in row["etymology_text"]
    assert "дієсл. to compute" in row["etymology_text"]
    assert "обчислити" in row["etymology_text"]
    assert "рахунком" in row["etymology_text"]


def test_etymology_precedence_and_phrase_skip() -> None:
    conn = _conn_with_etymology_tables()
    upsert_goroh_row(
        conn,
        {
            "requested_lemma": "робота",
            "headword": "робота",
            "etymology_text": "Горох має першість.",
            "source_url": "https://goroh.pp.ua/Етимологія/робота",
            "retrieved_at": "2026-06-01T00:00:00+00:00",
            "content_hash": "goroh",
        },
    )
    upsert_wiktionary_row(conn, _wiktionary_row("робота", "Вікісловник має бути fallback."))

    assert _etymology(conn, "робота") == {
        "text": "Горох має першість.",
        "source": "Горох (за ЕСУМ)",
        "source_url": "https://goroh.pp.ua/Етимологія/робота",
    }

    conn.execute("DELETE FROM goroh_etymology")
    conn.execute(
        "INSERT INTO esum_etymology VALUES (?, ?, ?, ?)",
        ("робота", "ЕСУМ має першість над Вікісловником.", "5", "10"),
    )
    assert _etymology(conn, "робота") == {
        "text": "ЕСУМ має першість над Вікісловником.",
        "source": "ЕСУМ, т. 5, с. 10",
    }

    conn.execute("DELETE FROM esum_etymology")
    assert _etymology(conn, "робота") == {
        "text": "Вікісловник має бути fallback.",
        "source": "Вікісловник (uk.wiktionary)",
        "source_url": "https://uk.wiktionary.org/wiki/робота",
    }

    upsert_wiktionary_row(conn, _wiktionary_row("Добрий день", "Phrase row should never render."))
    assert _etymology(conn, "Добрий день") is None

    assert _single_word_etymology_coverage(
        {
            "entries": [
                {"lemma": "робота", "enrichment": {"etymology": {"text": "x"}}},
                {"lemma": "Добрий день", "enrichment": {"etymology": {"text": "phrase"}}},
                {"lemma": "добре"},
                {"lemma": None, "enrichment": {"etymology": {"text": "bad"}}},
            ]
        }
    ) == (1, 2)
