"""Tests for wiki/sources_db.py and wiki/build_sources_db.py."""

import json
import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))


@pytest.fixture()
def sample_data(tmp_path):
    """Create sample JSONL files for all source types."""
    # External articles
    ext_dir = tmp_path / "external"
    ext_dir.mkdir()
    blogs = [
        {"url": "https://example.com/genitive", "title": "Родовий відмінок",
         "domain": "example.com", "char_count": 400,
         "text": (
             "Родовий відмінок вживається для позначення належності, частини від цілого, "
             "а також після багатьох прийменників. Він є одним із найчастіше вживаних "
             "відмінків в українській мові. Іменники першої відміни в родовому відмінку "
             "мають закінчення -и або -і, а іменники другої відміни — закінчення -а (-я) "
             "або -у (-ю) залежно від лексичного значення."
         )},
        {"url": "https://example.com/dative", "title": "Давальний відмінок",
         "domain": "example.com", "char_count": 350,
         "text": (
             "Давальний відмінок вказує на адресата дії або особу, для якої щось робиться. "
             "В українській мові давальний відмінок часто вживається з дієсловами, що "
             "позначають передачу, повідомлення, допомогу. Наприклад: дати книгу другові, "
             "розповісти матері, допомогти сусідові. Закінчення залежать від відміни іменника."
         )},
    ]
    with open(ext_dir / "test_blogs.jsonl", "w") as f:
        for e in blogs:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    # Textbooks
    tb_dir = tmp_path / "textbooks" / "grade-05"
    tb_dir.mkdir(parents=True)
    chunks = [
        {"chunk_id": "5-klas-test_s001", "section_title": "Іменник",
         "text": (
             "Родовий відмінок іменників вживається для позначення належності, "
             "частини від цілого, а також після деяких прийменників. "
             "Наприклад: книга вчителя, склянка води, біля школи. "
             "У родовому відмінку іменники першої відміни мають закінчення -и, -і, "
             "а іменники другої відміни — закінчення -а (-я) або -у (-ю) залежно від "
             "лексичного значення слова. Правильне вживання відмінкових форм є ознакою "
             "грамотного мовлення."
         ),
         "grade": "5", "author": "avramenko", "token_count": 50},
    ]
    with open(tb_dir / "5-klas-test.jsonl", "w") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    # Dictionaries (on fake gdrive)
    gdrive = tmp_path / "gdrive"

    # Literary texts (under gdrive, same as real layout)
    lit_dir = gdrive / "literary_texts"
    lit_dir.mkdir(parents=True)
    lit = [
        {"chunk_id": "lit-test-0", "title": "Козацькі думи",
         "author": "Народ", "section_title": "Козацькі думи",
         "text": (
             "Ой у полі козак лежить, кінь коло нього ходить. Козацькі думи — один із "
             "найдавніших жанрів українського фольклору. Вони оспівують героїчні подвиги "
             "козаків, їхню боротьбу за волю та незалежність. Думи виконувалися кобзарями "
             "та лірниками під акомпанемент бандури або ліри. Цей жанр не має аналогів "
             "в інших слов'янських літературах і є унікальним надбанням української культури."
         )},
    ]
    with open(lit_dir / "test-kozak.jsonl", "w") as f:
        for c in lit:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    for name, entries in [
        ("sum11", [{"word": "слово", "definition": "Одиниця мови", "text": "слово — одиниця мови", "source": "СУМ"}]),
        ("grinchenko", [{"word": "хата", "definition": "Будинок", "source": "Грінченко"}]),
        ("balla-en-uk", [{"word": "house", "definition": "будинок, хата", "text": "house — будинок", "source": "Балла"}]),
        ("dmklinger-uk-en", [{"word": "дім", "pos": "noun", "translations": ["house", "home"], "text": "дім — house", "source": "DM"}]),
        ("ukrajinet", [{"synset_id": "s1", "words": "великий, здоровий, чималий", "text": "великий синонім", "source": "UNet"}]),
        ("wiktionary", [{"word": "кіт", "definitions": "Домашня тварина", "synonyms": "", "antonyms": "", "text": "кіт", "source": "Wikt"}]),
        ("frazeolohichnyi", [{"word": "вода", "definition": "Не розлий вода", "text": "вода — фразеологізм", "source": "Фраз"}]),
        ("antonenko-davydovych", [{"word": "процент", "section": "Лексика", "text": "Кажіть відсоток", "source": "АД"}]),
    ]:
        d = gdrive / name
        d.mkdir(parents=True)
        with open(d / "chunks.jsonl", "w") as f:
            for e in entries:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")

    # PULS CEFR (local — must be under data/ to match PROJECT_ROOT layout)
    puls_dir = tmp_path / "data" / "puls"
    puls_dir.mkdir(parents=True)
    with open(puls_dir / "entries.jsonl", "w") as f:
        f.write(json.dumps({"word": "добре", "guideword": "", "level": "A1",
                            "pos": "прислівник", "type": "значення",
                            "text": "добре (A1)", "source": "PULS"}, ensure_ascii=False) + "\n")

    return {
        "ext_dir": ext_dir,
        "tb_dir": tmp_path / "textbooks",
        "gdrive": gdrive,
        "project_root": tmp_path,
        "db_path": tmp_path / "test.db",
    }


class TestBuildSourcesDb:
    def test_builds_all_tables(self, sample_data, monkeypatch):
        import wiki.build_sources_db as bdb
        from wiki.build_sources_db import build

        monkeypatch.setattr(bdb, "PROJECT_ROOT", sample_data["project_root"])

        db = build(
            db_path=sample_data["db_path"],
            external_dir=sample_data["ext_dir"],
            textbook_dir=sample_data["tb_dir"],
            gdrive_dir=sample_data["gdrive"],
        )
        assert db.exists()

        conn = sqlite3.connect(str(db))
        # Check each table has data
        assert conn.execute("SELECT COUNT(*) FROM external_articles").fetchone()[0] == 2
        assert conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM literary_texts").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM sum11").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM grinchenko").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM balla_en_uk").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM dmklinger_uk_en").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM ukrajinet").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM wiktionary").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM frazeolohichnyi").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM style_guide").fetchone()[0] == 1

        # FTS works
        fts = conn.execute(
            "SELECT COUNT(*) FROM textbooks_fts WHERE textbooks_fts MATCH '\"родовий\"'"
        ).fetchone()[0]
        assert fts >= 1
        conn.close()

    def test_rebuilds_cleanly(self, sample_data, monkeypatch):
        import wiki.build_sources_db as bdb
        from wiki.build_sources_db import build

        monkeypatch.setattr(bdb, "PROJECT_ROOT", sample_data["project_root"])

        build(sample_data["db_path"], sample_data["ext_dir"],
              sample_data["tb_dir"], sample_data["gdrive"])
        build(sample_data["db_path"], sample_data["ext_dir"],
              sample_data["tb_dir"], sample_data["gdrive"])

        conn = sqlite3.connect(str(sample_data["db_path"]))
        assert conn.execute("SELECT COUNT(*) FROM sum11").fetchone()[0] == 1
        conn.close()


class TestSourcesDb:
    def _build_and_patch(self, sample_data, monkeypatch):
        import wiki.build_sources_db as bdb
        import wiki.sources_db as sdb
        from wiki.build_sources_db import build
        monkeypatch.setattr(bdb, "PROJECT_ROOT", sample_data["project_root"])

        build(sample_data["db_path"], sample_data["ext_dir"],
              sample_data["tb_dir"], sample_data["gdrive"])
        monkeypatch.setattr(sdb, "SOURCES_DB_PATH", sample_data["db_path"])
        monkeypatch.setattr(sdb, "_conn", None)

    def test_search_textbooks(self, sample_data, monkeypatch):
        self._build_and_patch(sample_data, monkeypatch)
        from wiki.sources_db import search_textbooks
        results = search_textbooks({"родовий", "відмінок"}, max_total=5)
        assert len(results) >= 1
        assert results[0]["source_type"] == "textbook"

    def test_search_external(self, sample_data, monkeypatch):
        self._build_and_patch(sample_data, monkeypatch)
        from wiki.sources_db import search_external
        results = search_external({"родовий", "відмінок"}, max_total=5)
        assert len(results) >= 1
        assert results[0]["source_type"] == "external"

    def test_search_literary(self, sample_data, monkeypatch):
        self._build_and_patch(sample_data, monkeypatch)
        from wiki.sources_db import search_literary
        results = search_literary({"козак"}, max_total=5)
        assert len(results) >= 1

    def test_search_definitions(self, sample_data, monkeypatch):
        self._build_and_patch(sample_data, monkeypatch)
        from wiki.sources_db import search_definitions
        results = search_definitions("слово")
        assert len(results) == 1
        assert "Одиниця мови" in results[0]["definition"]

    def test_search_etymology(self, sample_data, monkeypatch):
        self._build_and_patch(sample_data, monkeypatch)
        from wiki.sources_db import search_etymology
        results = search_etymology("хата")
        assert len(results) == 1

    def test_translate_en_uk(self, sample_data, monkeypatch):
        self._build_and_patch(sample_data, monkeypatch)
        from wiki.sources_db import translate_en_uk
        results = translate_en_uk("house")
        assert len(results) == 1

    def test_search_synonyms(self, sample_data, monkeypatch):
        self._build_and_patch(sample_data, monkeypatch)
        from wiki.sources_db import search_synonyms
        results = search_synonyms("великий")
        assert len(results) >= 1

    def test_query_cefr_level(self, sample_data, monkeypatch):
        self._build_and_patch(sample_data, monkeypatch)
        from wiki.sources_db import query_cefr_level
        results = query_cefr_level("добре")
        assert len(results) >= 1
        assert results[0]["level"] == "A1"

    def test_search_style_guide(self, sample_data, monkeypatch):
        self._build_and_patch(sample_data, monkeypatch)
        from wiki.sources_db import search_style_guide
        results = search_style_guide("процент")
        assert len(results) == 1

    def test_lookup_by_url(self, sample_data, monkeypatch):
        self._build_and_patch(sample_data, monkeypatch)
        from wiki.sources_db import lookup_by_url
        result = lookup_by_url("https://example.com/genitive")
        assert result is not None
        assert result["title"] == "Родовий відмінок"

    def test_missing_db(self, tmp_path, monkeypatch):
        import wiki.sources_db as sdb
        monkeypatch.setattr(sdb, "SOURCES_DB_PATH", tmp_path / "nope.db")
        monkeypatch.setattr(sdb, "_conn", None)
        assert sdb.search_textbooks({"test"}) == []
        assert sdb.search_definitions("test") == []
        assert sdb.lookup_by_url("https://x.com") is None
        assert sdb.source_count() == 0


@pytest.fixture()
def external_search_db(tmp_path, monkeypatch):
    import wiki.sources_db as sdb

    db_path = tmp_path / "external-search.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(
        """
        CREATE TABLE external_articles (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT NOT NULL DEFAULT '',
            url TEXT NOT NULL DEFAULT '',
            url_normalized TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            text TEXT NOT NULL DEFAULT '',
            source_file TEXT NOT NULL DEFAULT '',
            domain TEXT DEFAULT '',
            char_count INTEGER DEFAULT 0,
            channel_id TEXT DEFAULT '',
            speaker TEXT DEFAULT '',
            register_tag TEXT DEFAULT '',
            decolonization_tag TEXT DEFAULT '',
            quality_tier INTEGER DEFAULT 2,
            publish_date TEXT DEFAULT '',
            duration_s INTEGER DEFAULT 0,
            chunk_start_ts INTEGER,
            chunk_end_ts INTEGER,
            video_id TEXT DEFAULT ''
        );
        CREATE VIRTUAL TABLE external_fts USING fts5(
            title, text, speaker, content='external_articles', content_rowid='id', tokenize='unicode61'
        );
        CREATE TRIGGER external_ai AFTER INSERT ON external_articles BEGIN
            INSERT INTO external_fts(rowid, title, text, speaker)
            VALUES (new.id, new.title, new.text, new.speaker);
        END;
        """
    )
    rows = [
        (
            "ext-ulp-000", "https://example.test/ulp", "https://example.test/ulp",
            "Козаки козаки козаки", "Козаки як навчальна тема для студентів. Козаки у простій мові.",
            "ulp_youtube", "example.test", 68, "ulp_youtube", "Anna Ohoiko",
            "scripted", "moderate", 1, "", 0, None, None, "ulp001",
        ),
        (
            "ext-realna-000", "https://example.test/realna", "https://example.test/realna",
            "Козаки та історія", "Козаки в історії України, деколонізація та пам'ять про козаків.",
            "realna_istoria", "example.test", 69, "realna_istoria", "Акім Галімов",
            "interview", "strong", 1, "", 0, None, None, "realna001",
        ),
        (
            "ext-imtgsh-000", "https://example.test/imtgsh", "https://example.test/imtgsh",
            "Козаки на пограниччі", "Козаки та історія державності. Шевченко, кордони, козаки.",
            "imtgsh", "example.test", 63, "imtgsh", "Редакційний голос каналу",
            "scripted", "strong", 2, "", 0, None, None, "imtgsh001",
        ),
        (
            "ext-other-000", "https://example.test/other", "https://example.test/other",
            "Козаки в блозі", "Козаки як тло для короткої нотатки.",
            "other_blogs", "example.test", 35, "other_blogs", "Multiple authors",
            "mixed", "neutral", 3, "", 0, None, None, "other001",
        ),
    ]
    conn.executemany(
        """INSERT INTO external_articles (
            chunk_id, url, url_normalized, title, text, source_file, domain, char_count,
            channel_id, speaker, register_tag, decolonization_tag, quality_tier,
            publish_date, duration_s, chunk_start_ts, chunk_end_ts, video_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(sdb, "SOURCES_DB_PATH", db_path)
    monkeypatch.setattr(sdb, "_conn", None)
    return db_path


def test_search_external_filters_and_returns_metadata(external_search_db):
    from wiki.sources_db import search_external

    results = search_external(
        {"козаки"},
        max_total=5,
        channel="realna_istoria",
        decolonization="strong",
        min_quality_tier=1,
    )

    assert len(results) == 1
    assert results[0]["channel_id"] == "realna_istoria"
    assert results[0]["speaker"] == "Акім Галімов"
    assert results[0]["register_tag"] == "interview"
    assert results[0]["decolonization_tag"] == "strong"
    assert results[0]["quality_tier"] == 1


def test_search_external_register_and_quality_filters(external_search_db):
    from wiki.sources_db import search_external

    results = search_external(
        {"козаки"},
        max_total=5,
        register="scripted",
        min_quality_tier=2,
    )

    assert {row["channel_id"] for row in results} == {"ulp_youtube", "imtgsh"}
    assert all(row["quality_tier"] <= 2 for row in results)


def test_search_external_track_reranks_hist_sources(external_search_db):
    from wiki.sources_db import search_external

    plain = search_external({"козаки"}, max_total=4)
    hist = search_external({"козаки"}, max_total=4, track="hist")

    assert plain[0]["channel_id"] == "ulp_youtube"
    assert hist[0]["channel_id"] in {"realna_istoria", "imtgsh"}
    hist_positions = {row["channel_id"]: index for index, row in enumerate(hist)}
    assert hist_positions["realna_istoria"] < hist_positions["ulp_youtube"]
