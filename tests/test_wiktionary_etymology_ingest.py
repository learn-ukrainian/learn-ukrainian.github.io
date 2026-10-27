import bz2
import sqlite3
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock
from xml.sax.saxutils import escape

import pytest

from scripts.ingest import wiktionary_etymology_ingest as wiktionary
from scripts.ingest.wiktionary_etymology_ingest import (
    WiktionaryPage,
    ensure_wiktionary_etymology_schema,
    ingest_wiktionary_etymology,
    is_clean_etymology,
    lookup_key,
    parse_wiktionary_page,
)


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


@pytest.mark.parametrize(
    ("user_agent", "expected_header"),
    [
        (
            None,
            "learn-ukrainian-wiktionary-etymology/1.0 "
            "(noncommercial educational lookup; issue 2882; "
            "https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues)",
        ),
        (
            "AtlasTransportTest/2.0 (+https://example.org/contact)",
            "AtlasTransportTest/2.0 (+https://example.org/contact)",
        ),
    ],
    ids=["default-public-contact", "explicit-override"],
)
def test_download_dump_request_omitted_contact_or_clobbered_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    user_agent: str | None,
    expected_header: str,
) -> None:
    payload = _write_dump(tmp_path, []).read_bytes()
    transport = Mock(return_value=BytesIO(payload))
    monkeypatch.setattr(wiktionary, "urlopen", transport)
    destination = tmp_path / "download" / "dump.xml.bz2"

    if user_agent is None:
        wiktionary.download_dump(destination)
    else:
        wiktionary.download_dump(destination, user_agent=user_agent)

    request = transport.call_args.args[0]
    assert request.get_header("User-agent") == expected_header
    assert request.full_url == (
        "https://dumps.wikimedia.org/ukwiktionary/20260601/"
        "ukwiktionary-20260601-pages-articles.xml.bz2"
    )
    assert transport.call_count == 1
    assert transport.call_args.kwargs == {"timeout": 120}
    assert destination.read_bytes() == payload


def test_downloaded_unpinned_archive_is_rejected_before_database_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _write_dump(tmp_path, []).read_bytes()
    monkeypatch.setattr(wiktionary, "urlopen", Mock(return_value=BytesIO(payload)))
    destination = tmp_path / "download" / "dump.xml.bz2"
    database = tmp_path / "sources.db"

    with pytest.raises(
        ValueError,
        match="sha256 mismatch: expected "
        "a3544dc777eb152d0bdb57c394c0cf7074f0f0a3e70b0ec953449055dea5d604, got ",
    ):
        wiktionary.main([
            "--download", "--dump", str(destination),
            "--db", str(database), "--lemma", "fixture",
        ])

    assert destination.read_bytes() == payload
    assert not database.exists()


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
