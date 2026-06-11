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
    is_clean_etymology,
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
                "комп’ютер",
                "0",
                """
                {{=uk=}}
                ===Морфосинтаксичні ознаки===
                {{імен uk}}
                ===Етимологія===
                Від {{етимологія:комп’ютер|uk}}.
                ===Переклад===
                {{переклад|пристрій}}
                """,
            ),
            (
                "Шаблон:етимологія:комп’ютер",
                "10",
                '{{lang-en|[[дієслово|дієсл.]] to [[compute]]}} — "обчислити"<noinclude>[[Категорія:Шаблони етимології|комп’ютер]]</noinclude>',
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
        ["Добрий день", "комп'ютер"],
        refresh=False,
        dry_run=False,
        max_text_chars=1200,
    )
    assert (scanned, loaded, skipped) == (1, 1, 1)

    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT requested_lemma, headword, etymology_text, section_raw FROM wiktionary_etymology"
    ).fetchone()
    assert row[0] == "комп'ютер"
    assert row[1] == "комп’ютер"
    assert "англ." in row[2]
    assert "дієсл. to compute" in row[2]
    assert "обчислити" in row[2]
    assert "Категорія" not in row[2]
    assert "{{етимологія:комп’ютер|uk}}" in row[3]

    scanned_again, loaded_again, skipped_again = ingest_wiktionary_etymology(
        db_path,
        dump,
        ["Добрий день", "комп'ютер"],
        refresh=False,
        dry_run=False,
        max_text_chars=1200,
    )
    assert (scanned_again, loaded_again, skipped_again) == (0, 0, 1)
    assert conn.execute("SELECT count(*) FROM wiktionary_etymology").fetchone()[0] == 1
    conn.close()


def test_quality_gate_accepts_clean_and_rejects_garbage_samples() -> None:
    rejected = {
        "звук": "Від звати Від звати Від зов",
        "йти": "Від ? 3 Дієслова",
        "ключ": "Від uk Від uk Від uk Від be Від ru",
        "молоко": "Від Від ? 6 6 Предметні слова Напої",
        "потім": "Від uk Від uk Від uk",
        "книга": "Від від праслов’янського *kъnъ Від",
        "робота": (
            "Від слова раб. Тобто раб це людина що робить роботу. "
            "Або робота це те що робить раб."
        ),
    }
    for lemma, text in rejected.items():
        assert not is_clean_etymology(text, lemma=lemma), lemma

    accepted = {
        "комп'ютер": 'Від англ. дієсл. to compute — "обчислити"',
        "кава": "Запозичено з арабської через османську турецьку.",
        "стіл": "Від psl *stolъ, від якого також походять споріднені слова.",
        "приголосний": "Похідне утворення від голос, див. голос.",
        "дім": "Від прасл. *domъ.",
        "форма": "Від лат. forma.",
    }
    for lemma, text in accepted.items():
        assert is_clean_etymology(text, lemma=lemma), lemma


def test_low_quality_wiktionary_work_row_is_not_stored(tmp_path: Path) -> None:
    dump = _write_dump(
        tmp_path,
        [
            (
                "робота",
                "0",
                """
                {{=uk=}}
                ===Етимологія===
                Від слова [[раб]]. Тобто раб це людина що робить роботу.
                Або робота це те що робить раб.
                """,
            ),
        ],
    )
    db_path = tmp_path / "sources.db"

    scanned, loaded, skipped = ingest_wiktionary_etymology(
        db_path,
        dump,
        ["робота"],
        refresh=True,
        dry_run=False,
        max_text_chars=1200,
    )
    assert (scanned, loaded, skipped) == (1, 0, 0)

    conn = sqlite3.connect(db_path)
    assert conn.execute("SELECT count(*) FROM wiktionary_etymology").fetchone()[0] == 0
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
    upsert_wiktionary_row(
        conn,
        _wiktionary_row("комп'ютер", 'Від англ. дієсл. to compute — "обчислити".'),
    )
    assert _etymology(conn, "комп'ютер") == {
        "text": 'Від англ. дієсл. to compute — "обчислити".',
        "source": "Вікісловник (uk.wiktionary)",
        "source_url": "https://uk.wiktionary.org/wiki/комп'ютер",
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
