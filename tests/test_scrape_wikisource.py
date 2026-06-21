from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from rag import scrape_wikisource as sw


def _poem_wikitext(title: str = "Дума про козака Голоту") -> str:
    return f"""{{{{заголовок|назва={title}|автор=Народна творчість}}}}
<poem>
Ой полем [[Килія|киліїмським]],
То шляхом битим гординським,<ref>Примітка.</ref>
Ой там гуляв козак [[Голота]],
Не боїться ні огня, ні меча, ні третього болота.
</poem>

[[Категорія:Думи]]
"""


def _sample_fetch_parse(title: str) -> tuple[str, str]:
    return _poem_wikitext(title), ""


def _init_literary_db(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    conn.executescript(
        """
        CREATE TABLE literary_texts (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            text TEXT NOT NULL DEFAULT '',
            source_file TEXT NOT NULL DEFAULT '',
            source_url TEXT DEFAULT '',
            author TEXT DEFAULT '',
            work TEXT DEFAULT '',
            work_id TEXT DEFAULT '',
            year INTEGER,
            genre TEXT DEFAULT '',
            language_period TEXT DEFAULT '',
            char_count INTEGER DEFAULT 0
        );
        CREATE VIRTUAL TABLE literary_fts USING fts5(
            title,
            text,
            content='literary_texts',
            content_rowid='id',
            tokenize='unicode61'
        );
        """
    )
    conn.close()


def test_extract_text_prefers_poem_wikitext_and_strips_markup() -> None:
    text = sw.extract_text(_poem_wikitext(), "<p>fallback should not be used</p>")

    assert text.splitlines() == [
        "Ой полем киліїмським,",
        "То шляхом битим гординським,",
        "Ой там гуляв козак Голота,",
        "Не боїться ні огня, ні меча, ні третього болота.",
    ]
    assert "{{" not in text
    assert "[[" not in text
    assert "<ref" not in text
    assert "Категорія:Думи" not in text


def test_extract_text_html_fallback_preserves_verse_lines() -> None:
    html = """
    <div class="mw-parser-output">
      <div id="headertemplate" class="ws-noexport">Вікістаття • Вікідані</div>
      <dl>
        <dd><b>Дума про козака Голоту</b></dd>
        <dd>Ой полем киліїмським,</dd>
        <dd>То шляхом битим гординським,</dd>
        <dd>Ой там гуляв козак Голота.</dd>
      </dl>
      <div class="poem">
        <p>fallback duplicate should not win</p>
      </div>
      <div class="catlinks">Категорії: Думи</div>
    </div>
    """

    text = sw.extract_text("{{заголовок|назва=Тест}}", html)

    assert text.splitlines() == [
        "Ой полем киліїмським,",
        "То шляхом битим гординським,",
        "Ой там гуляв козак Голота.",
    ]
    assert "Вікістаття" not in text
    assert "Категорії" not in text


def test_version_target_title_uses_first_content_link() -> None:
    wikitext = """{{версії|nointro=так}}
* [[Історія Слободської України/Боротьба з татарами/Вдова Івана Сірка і Сірченки|Вдова Івана Сірка і Сірченки]]
  // {{fine|[[Автор:Дмитро Багалій|Багалій Д. І.]]}}
[[Категорія:Думи]]
"""

    assert (
        sw._version_target_title(wikitext)
        == "Історія Слободської України/Боротьба з татарами/Вдова Івана Сірка і Сірченки"
    )


def test_skip_titles_file_omits_candidate_from_jsonl(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(sw, "LITERARY_DIR", tmp_path / "literary_texts")
    monkeypatch.setattr(sw, "discover_category_pages", lambda _category: ["Дума про козака Голоту", "Самійло Кішка"])
    monkeypatch.setattr(sw, "fetch_parse", _sample_fetch_parse)
    monkeypatch.setattr(sw.time, "sleep", lambda _seconds: None)

    skip_file = tmp_path / "skip.txt"
    skip_file.write_text("Самійло Кішка\n", encoding="utf-8")

    sw.scrape_category("Категорія:Думи", dry_run=True, skip_titles_file=skip_file)

    output_path = tmp_path / "literary_texts" / "wikisource-folk-dumy.jsonl"
    rows = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    assert rows[0]["title"] == "Дума про козака Голоту"
    assert "Самійло Кішка" not in output_path.read_text(encoding="utf-8")


def test_generated_jsonl_passes_ukrlib_audit(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(sw, "LITERARY_DIR", tmp_path / "literary_texts")
    monkeypatch.setattr(sw, "discover_category_pages", lambda _category: ["Дума про козака Голоту"])
    monkeypatch.setattr(sw, "fetch_parse", _sample_fetch_parse)

    sw.scrape_category("Категорія:Думи", dry_run=True)

    output_path = tmp_path / "literary_texts" / "wikisource-folk-dumy.jsonl"
    passed, errors = sw.audit_jsonl(output_path)
    assert passed is True
    assert errors == []


def test_ingest_replaces_rows_and_rebuilds_fts(tmp_path: Path, monkeypatch) -> None:
    lit_dir = tmp_path / "literary_texts"
    db_path = tmp_path / "sources.db"
    _init_literary_db(db_path)

    monkeypatch.setattr(sw, "LITERARY_DIR", lit_dir)
    monkeypatch.setattr(sw, "discover_category_pages", lambda _category: ["Дума про козака Голоту"])
    monkeypatch.setattr(sw, "fetch_parse", _sample_fetch_parse)

    result = sw.main([
        "--category",
        "Категорія:Думи",
        "--ingest",
        "--db",
        str(db_path),
        "--limit",
        "1",
    ])

    assert result == 0
    conn = sqlite3.connect(str(db_path))
    rows = conn.execute(
        """
        SELECT title, source_file, source_url, author, work, year, genre, language_period
        FROM literary_texts
        """
    ).fetchall()
    assert rows == [
        (
            "Дума про козака Голоту",
            "wikisource-folk-dumy",
            "https://uk.wikisource.org/wiki/%D0%94%D1%83%D0%BC%D0%B0_%D0%BF%D1%80%D0%BE_%D0%BA%D0%BE%D0%B7%D0%B0%D0%BA%D0%B0_%D0%93%D0%BE%D0%BB%D0%BE%D1%82%D1%83",
            "Народна творчість",
            "Народна творчість. Дума про козака Голоту",
            1600,
            "Дума",
            "middle_ukrainian",
        )
    ]
    fts_rows = conn.execute(
        "SELECT rowid, title FROM literary_fts WHERE literary_fts MATCH ?",
        ("киліїмським",),
    ).fetchall()
    conn.close()
    assert fts_rows == [(1, "Дума про козака Голоту")]
