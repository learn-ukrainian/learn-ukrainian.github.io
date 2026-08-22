"""Tests for wiki/sources_db.py and wiki/build_sources_db.py."""

import json
import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from wiki import sources_db


@pytest.fixture()
def ua_gec_search_conn(monkeypatch: pytest.MonkeyPatch):
    """Small deterministic UA-GEC FTS database for query-safety tests."""

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE ua_gec_errors (
            id INTEGER PRIMARY KEY,
            error TEXT NOT NULL,
            correct TEXT NOT NULL,
            error_type TEXT NOT NULL,
            doc_id TEXT NOT NULL,
            is_native INTEGER NOT NULL,
            source_lang TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE VIRTUAL TABLE ua_gec_errors_fts USING fts5(
            error, correct, error_type,
            content='ua_gec_errors', content_rowid='id', tokenize='unicode61'
        )
        """
    )
    conn.execute(
        """
        INSERT INTO ua_gec_errors(id, error, correct, error_type, doc_id, is_native, source_lang)
        VALUES (1, 'приймати участь', 'брати участь', 'F/Calque', 'synthetic-doc', 1, 'uk')
        """
    )
    conn.execute(
        """
        INSERT INTO ua_gec_errors_fts(rowid, error, correct, error_type)
        VALUES (1, 'приймати участь', 'брати участь', 'F/Calque')
        """
    )
    monkeypatch.setattr(sources_db, "_get_conn", lambda: conn)
    yield conn
    conn.close()


@pytest.mark.parametrize("query", ['"брати участь', "брати\x00участь"])
def test_search_ua_gec_errors_treats_fts_control_input_as_literal_text(ua_gec_search_conn, query: str) -> None:
    results = sources_db.search_ua_gec_errors(query)

    assert [row["correct"] for row in results] == ["брати участь"]


@pytest.mark.parametrize("query", ['"', '  ""  '])
def test_search_ua_gec_errors_returns_empty_for_quote_only_query(ua_gec_search_conn, query: str) -> None:
    assert sources_db.search_ua_gec_errors(query) == []


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
         "grade": "5", "author": "avramenko", "author_uk": "Авраменко",
         "token_count": 50},
    ]
    with open(tb_dir / "5-klas-ukrmova-avramenko-2022.jsonl", "w") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    # Dictionaries (on fake gdrive)
    gdrive = tmp_path / "gdrive"

    historical_dir = (
        gdrive
        / "historical_language_corpus"
        / "canonical"
        / "saint-sophia-inscriptions"
    )
    historical_dir.mkdir(parents=True)
    historical_row = {
        "schema_version": "historical-source-record.v1",
        "collection_id": "saint-sophia-inscriptions",
        "source_record_id": "1",
        "title": "Графіті 1",
        "source_url": "https://saintsophia.dh.gu.se/inscription/1",
        "published": True,
        "original_transcription": "тестовий напис",
        "epidoc_text": "<ab>тестовий напис</ab>",
        "epidoc_interpretation": "",
        "interpretative_edition": "тестовий напис",
        "romanisation": "",
        "translation_ukr": "",
        "translation_eng": "",
        "commentary_ukr": "",
        "commentary_eng": "",
        "source_language_label": "Church Slavonic",
        "source_writing_system_label": "Cyrillic",
        "min_year": 1100,
        "max_year": 1200,
        "stage_label": None,
        "disposition": "text_bearing",
        "quality_flags": [],
        "metadata": {"portal_id": 1},
        "raw_record_sha256": "0" * 64,
    }
    with open(historical_dir / "historical_source_records.jsonl", "w") as f:
        f.write(json.dumps(historical_row, ensure_ascii=False) + "\n")

    # Literary texts (under gdrive, same as real layout)
    lit_dir = gdrive / "literary_texts"
    lit_dir.mkdir(parents=True)
    lit = [
        {"chunk_id": "lit-test-0", "title": "Козацькі думи",
         "author": "Народ", "section_title": "Козацькі думи",
         "source_url": "https://lit.example/kozak",
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
        ("antonenko-davydovych", [
            {"word": "процент", "section": "Лексика", "text": "Кажіть відсоток", "source": "АД"},
            {"word": "Приймати участь", "section": "Лексика",
             "text": "Приймати участь — калька з рос. Кажіть: брати участь.", "source": "АД"},
            {"word": "На протязі", "section": "Прийменники",
             "text": "На протязі — калька з рос. 'в течение'. Кажіть: протягом.", "source": ""},
        ]),
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
    def test_full_rebuild_rejects_unverified_native_text_anomaly(self):
        import wiki.build_sources_db as bdb

        repeated = "Рекомендовано Міністерством освіти і науки України"
        entry = {
            "chunk_id": "source_s0001",
            "text": f"{repeated}\n{repeated}",
            "extraction_mode": "native_text",
            "page_extraction_mode": "native_text",
        }

        with pytest.raises(ValueError, match="requires exact page-image verification"):
            bdb._require_production_textbook_entry(entry, source_file="7-klas-test-author-2024")

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
        assert conn.execute("SELECT subject FROM textbooks").fetchone()[0] == "ukrmova"
        assert conn.execute("SELECT COUNT(*) FROM literary_texts").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM historical_source_records").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM sum11").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM grinchenko").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM balla_en_uk").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM dmklinger_uk_en").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM ukrajinet").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM wiktionary").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM frazeolohichnyi").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM style_guide").fetchone()[0] == 3

        # FTS works
        fts = conn.execute(
            "SELECT COUNT(*) FROM textbooks_fts WHERE textbooks_fts MATCH '\"родовий\"'"
        ).fetchone()[0]
        assert fts >= 1
        historical_fts = conn.execute(
            "SELECT COUNT(*) FROM historical_source_records_fts "
            "WHERE historical_source_records_fts MATCH '\"напис\"'"
        ).fetchone()[0]
        assert historical_fts == 1
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

    def test_full_rebuild_uses_canonical_university_grade_label(
        self, sample_data, monkeypatch
    ):
        from scripts.wiki import build_sources_db as bdb
        from scripts.wiki.build_sources_db import build

        monkeypatch.setattr(bdb, "PROJECT_ROOT", sample_data["project_root"])
        grade_zero = sample_data["tb_dir"] / "grade-00"
        grade_zero.mkdir(parents=True)
        slug = "uni-ukrmova-lexicology-filon-khomik-2010"
        (grade_zero / f"{slug}.jsonl").write_text(
            json.dumps(
                {
                    "chunk_id": f"{slug}_s0000",
                    "section_title": "Лексикологія",
                    "text": "Український університетський текст.",
                    "grade": 0,
                    "author": "khomik",
                    "author_uk": "Хомік",
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        build(
            sample_data["db_path"],
            sample_data["ext_dir"],
            sample_data["tb_dir"],
            sample_data["gdrive"],
        )

        connection = sqlite3.connect(str(sample_data["db_path"]))
        grade = connection.execute(
            "SELECT grade FROM textbooks WHERE source_file = ?",
            (slug,),
        ).fetchone()[0]
        connection.close()
        assert grade == "university"


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

    def test_search_textbooks_subject_filter(self, sample_data, monkeypatch):
        self._build_and_patch(sample_data, monkeypatch)
        from wiki.sources_db import search_textbooks

        results = search_textbooks(
            {"родовий", "відмінок"},
            max_total=5,
            subject="ukrainska-mova",
        )
        assert len(results) >= 1
        assert {row["subject"] for row in results} == {"ukrmova"}

        assert (
            search_textbooks(
                {"родовий", "відмінок"},
                max_total=5,
                subject="ukrlit",
            )
            == []
        )

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

    def test_search_grinchenko_1907(self, sample_data, monkeypatch):
        self._build_and_patch(sample_data, monkeypatch)
        from wiki.sources_db import search_grinchenko_1907
        results = search_grinchenko_1907("хата")
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

    def test_ulif_materialized_relations_take_priority_over_fallbacks(self, sample_data, monkeypatch):
        self._build_and_patch(sample_data, monkeypatch)
        from wiki import sources_db as sdb

        stored = sdb.store_ulif_dictua_entry(
            word="великий",
            canonical_headword="великий",
            sections={
                "synonyms": [{
                    "sense_or_group_id": "synonyms:1",
                    "terms": [{"text": "величезний"}],
                    "register_labels": ["розм."],
                    "citations": ["Леся Українка"],
                }],
            },
            raw_responses={"synonyms": "<html>official synonym group</html>"},
            retrieved_at="2026-07-15T00:00:00+00:00",
            parser_version="ulif-dictua-v1",
            status="ok",
        )

        assert stored is not None
        assert sdb.resolve_ulif_dictua_raw_response(stored["raw_response_ref"])
        results = sdb.search_synonyms("великий", limit=5)
        assert results[0]["source_id"] == "ulif_dictua"
        assert results[0]["attribution_label"] == (
            "«Словники України» (Український мовно-інформаційний фонд НАН України)"
        )
        assert results[0]["sections"]["synonyms"][0]["terms"][0]["text"] == "величезний"
        assert results[1]["synset_id"] == "s1"

        conn = sqlite3.connect(str(sample_data["db_path"]))
        try:
            columns = {
                row[1] for row in conn.execute("PRAGMA table_info(ulif_dictua_entries)")
            }
            assert {
                "normalized_query", "canonical_headword", "raw_response_ref", "retrieved_at",
                "response_sha256", "parser_version", "status",
            } <= columns
            assert conn.execute("SELECT COUNT(*) FROM ulif_dictua_sections").fetchone()[0] == 1
        finally:
            conn.close()

        sdb.store_ulif_dictua_entry(
            word="вода",
            canonical_headword="вода",
            sections={
                "phraseology": [{
                    "sense_or_group_id": "phraseology:1",
                    "terms": [{"text": "води в рот набрати"}],
                    "text": "води в рот набрати",
                }],
            },
            raw_responses={"phraseology": "<html>official phraseology group</html>"},
            retrieved_at="2026-07-15T00:00:00+00:00",
            parser_version="ulif-dictua-v1",
            status="ok",
        )
        idioms = sdb.search_idioms("вода", limit=5)
        assert idioms[0]["source_id"] == "ulif_dictua"
        assert idioms[0]["sections"]["phraseology"][0]["terms"][0]["text"] == "води в рот набрати"

    def test_query_cefr_level(self, sample_data, monkeypatch):
        self._build_and_patch(sample_data, monkeypatch)
        from wiki.sources_db import query_cefr_level
        results = query_cefr_level("добре")
        assert len(results) >= 1
        assert results[0]["level"] == "A1"

    def test_batch_vocabulary_lookups(self, sample_data, monkeypatch):
        self._build_and_patch(sample_data, monkeypatch)
        from wiki.sources_db import query_cefr_levels, search_definitions_batch

        cefr = query_cefr_levels(["добре", "відсутнє"])
        definitions = search_definitions_batch(["слово", "слов", "відсутнє"])

        assert cefr["добре"][0]["level"] == "A1"
        assert cefr["відсутнє"] == []
        assert "Одиниця мови" in definitions["слово"][0]["definition"]
        assert "Одиниця мови" in definitions["слов"][0]["definition"]
        assert definitions["відсутнє"] == []

    def test_search_style_guide(self, sample_data, monkeypatch):
        self._build_and_patch(sample_data, monkeypatch)
        from wiki.sources_db import search_style_guide
        results = search_style_guide("процент")
        assert len(results) == 1

    def test_search_style_guide_lowercase_phrase_matches_capitalized_headword(
        self, sample_data, monkeypatch
    ):
        self._build_and_patch(sample_data, monkeypatch)
        from wiki.sources_db import search_style_guide

        results = search_style_guide("приймати участь")
        assert len(results) == 1
        assert results[0]["word"] == "Приймати участь"
        assert results[0]["source"] == "АД"

    def test_search_style_guide_substring_matches_multiword_headword(
        self, sample_data, monkeypatch
    ):
        self._build_and_patch(sample_data, monkeypatch)
        from wiki.sources_db import search_style_guide

        results = search_style_guide("протязі")
        assert len(results) == 1
        assert results[0]["word"] == "На протязі"
        # The fixture's `source` field is empty — search_style_guide fills
        # in the canonical attribution rather than returning "".
        assert results[0]["source"] == "Антоненко-Давидович"

    def test_search_style_guide_body_fallback_when_not_in_headword(
        self, sample_data, monkeypatch
    ):
        self._build_and_patch(sample_data, monkeypatch)
        from wiki.sources_db import search_style_guide

        # "протягом" is in the text of "На протязі" ("Кажіть: протягом."), but not in the headword.
        results = search_style_guide("протягом")
        assert len(results) >= 1
        assert results[0]["word"] == "На протязі"
        assert "протягом" in results[0]["text"]

    def test_search_style_guide_nonexistent_query_returns_empty(
        self, sample_data, monkeypatch
    ):
        self._build_and_patch(sample_data, monkeypatch)
        from wiki.sources_db import search_style_guide

        assert search_style_guide("нежиттєздатнийтермін") == []

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


def test_rebuild_author_uk_enrichment_regression(tmp_path, monkeypatch):
    import wiki.build_sources_db as bdb
    from wiki.build_sources_db import build

    # Create temporary report path so we don't overwrite actual docs
    monkeypatch.setattr(bdb, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(bdb, "DEFAULT_REPORT_PATH", tmp_path / "textbook_sections_audit.md")

    # Set up a minimal textbooks structure
    tb_dir = tmp_path / "textbooks" / "grade-05"
    tb_dir.mkdir(parents=True)

    # Row with author set and author_uk null
    chunk = {
        "chunk_id": "5-klas-test_s001",
        "section_title": "Іменник",
        "text": "Приклад тексту.",
        "grade": "5",
        "author": "avramenko",
        "author_uk": None,
        "token_count": 5
    }

    jsonl_path = tb_dir / "5-klas-ukrmova-avramenko-2022.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    # Fake empty directories for external, gdrive
    ext_dir = tmp_path / "external"
    ext_dir.mkdir()
    gdrive = tmp_path / "gdrive"
    gdrive.mkdir()

    db_path = tmp_path / "rebuild_test.db"
    build(
        db_path=db_path,
        external_dir=ext_dir,
        textbook_dir=tmp_path / "textbooks",
        gdrive_dir=gdrive,
        force=True,
    )

    # Verify that the textbook chunk was ingested and author_uk was populated from mapping
    conn = sqlite3.connect(str(db_path))
    row = conn.execute("SELECT author, author_uk FROM textbooks").fetchone()
    conn.close()
    assert row is not None
    assert row[0] == "avramenko"
    assert row[1] == "Авраменко"


def test_rebuild_author_absent_edge(tmp_path, monkeypatch):
    import wiki.build_sources_db as bdb
    from wiki.build_sources_db import build

    # Create temporary report path so we don't overwrite actual docs
    monkeypatch.setattr(bdb, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(bdb, "DEFAULT_REPORT_PATH", tmp_path / "textbook_sections_audit.md")

    # Set up a minimal textbooks structure
    tb_dir = tmp_path / "textbooks" / "grade-05"
    tb_dir.mkdir(parents=True)

    # Row with no author info (or empty author)
    chunk = {
        "chunk_id": "5-klas-test_s001",
        "section_title": "Іменник",
        "text": "Приклад тексту.",
        "grade": "5",
        "token_count": 5
    }

    jsonl_path = tb_dir / "5-klas-ukrmova-avramenko-2022.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    # Fake empty directories for external, gdrive
    ext_dir = tmp_path / "external"
    ext_dir.mkdir()
    gdrive = tmp_path / "gdrive"
    gdrive.mkdir()

    db_path = tmp_path / "rebuild_test.db"
    build(
        db_path=db_path,
        external_dir=ext_dir,
        textbook_dir=tmp_path / "textbooks",
        gdrive_dir=gdrive,
        force=True,
    )

    # Verify that the textbook chunk was ingested and author/author_uk are empty/default
    conn = sqlite3.connect(str(db_path))
    row = conn.execute("SELECT author, author_uk FROM textbooks").fetchone()
    conn.close()
    assert row is not None
    assert row[0] == ""
    assert row[1] == ""


def test_rebuild_author_unmapped_edge(tmp_path, monkeypatch):
    import wiki.build_sources_db as bdb
    from ingest.incremental_textbook_ingest import IngestError
    from wiki.build_sources_db import build

    # Create temporary report path so we don't overwrite actual docs
    monkeypatch.setattr(bdb, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(bdb, "DEFAULT_REPORT_PATH", tmp_path / "textbook_sections_audit.md")

    # Set up a minimal textbooks structure
    tb_dir = tmp_path / "textbooks" / "grade-05"
    tb_dir.mkdir(parents=True)

    # Row with author set to an unmapped transliteration and author_uk null
    chunk = {
        "chunk_id": "5-klas-test_s001",
        "section_title": "Іменник",
        "text": "Приклад тексту.",
        "grade": "5",
        "author": "unknown_author_name",
        "author_uk": None,
        "token_count": 5
    }

    jsonl_path = tb_dir / "5-klas-ukrmova-avramenko-2022.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    # Fake empty directories for external, gdrive
    ext_dir = tmp_path / "external"
    ext_dir.mkdir()
    gdrive = tmp_path / "gdrive"
    gdrive.mkdir()

    db_path = tmp_path / "rebuild_test.db"

    # Expect IngestError parity with incremental-ingest
    with pytest.raises(IngestError) as exc_info:
        build(
            db_path=db_path,
            external_dir=ext_dir,
            textbook_dir=tmp_path / "textbooks",
            gdrive_dir=gdrive,
            force=True,
        )
    assert "has no canonical Cyrillic form in AUTHOR_UK" in str(exc_info.value)


class TestForcedRebuildAtomicity:
    """#4859: build(force=True) must be failure-atomic.

    The pre-#4859 bug: build(force=True) unlinked the live sources.db
    (+ WAL/SHM) BEFORE parsing or validating any input, so any raise
    mid-rebuild (malformed JSONL, an unmapped-author IngestError, a
    validation failure) left NO usable sources.db. These tests populate a
    real DB first, then force a genuine rebuild — the case the pre-fix
    "rebuilds cleanly" test (see TestBuildSourcesDb above) never covered.
    """

    def test_force_rebuild_failure_leaves_original_db_intact(self, sample_data, monkeypatch):
        import wiki.build_sources_db as bdb
        from ingest.incremental_textbook_ingest import IngestError
        from wiki.build_sources_db import build

        monkeypatch.setattr(bdb, "PROJECT_ROOT", sample_data["project_root"])
        db_path = sample_data["db_path"]

        # First build: a real, populated DB with a readable sentinel row.
        build(db_path, sample_data["ext_dir"], sample_data["tb_dir"], sample_data["gdrive"])
        assert db_path.exists()
        original_bytes = db_path.read_bytes()
        original_mtime_ns = db_path.stat().st_mtime_ns

        # Inject a failure into the SECOND (forced) rebuild: a textbook
        # chunk whose author has no canonical Cyrillic form.
        bad_dir = sample_data["tb_dir"] / "grade-05"
        with open(bad_dir / "zzz-unmapped.jsonl", "w", encoding="utf-8") as f:
            f.write(json.dumps({
                "chunk_id": "bad-1", "section_title": "Зламаний",
                "text": "Текст без відповідного автора у мапі.",
                "grade": "5", "author": "totally_unmapped_author",
                "author_uk": None, "token_count": 5,
            }, ensure_ascii=False) + "\n")

        with pytest.raises(IngestError):
            build(db_path, sample_data["ext_dir"], sample_data["tb_dir"],
                  sample_data["gdrive"], force=True)

        # The pre-existing DB must be untouched — never unlinked, never
        # partially overwritten.
        assert db_path.exists()
        assert db_path.stat().st_mtime_ns == original_mtime_ns
        assert db_path.read_bytes() == original_bytes

        conn = sqlite3.connect(str(db_path))
        assert conn.execute("SELECT COUNT(*) FROM sum11").fetchone()[0] == 1
        assert conn.execute("SELECT word FROM sum11").fetchone()[0] == "слово"
        conn.close()

        # The failed rebuild must not leak its temp-build artifacts either.
        leftovers = list(db_path.parent.glob(f".{db_path.name}.*"))
        assert leftovers == [], f"temp build artifacts leaked: {leftovers}"

    def test_force_rebuild_success_swaps_atomically(self, sample_data, monkeypatch, capsys):
        import wiki.build_sources_db as bdb
        from wiki.build_sources_db import build

        monkeypatch.setattr(bdb, "PROJECT_ROOT", sample_data["project_root"])
        db_path = sample_data["db_path"]

        build(db_path, sample_data["ext_dir"], sample_data["tb_dir"], sample_data["gdrive"])
        first_inode = db_path.stat().st_ino

        build(db_path, sample_data["ext_dir"], sample_data["tb_dir"],
              sample_data["gdrive"], force=True)

        out = capsys.readouterr().out
        assert "Atomically replaced" in out

        # A real swap happened (new inode) — not an in-place rewrite of
        # the live file.
        assert db_path.stat().st_ino != first_inode

        conn = sqlite3.connect(str(db_path))
        assert conn.execute("SELECT COUNT(*) FROM sum11").fetchone()[0] == 1
        conn.close()

        leftovers = list(db_path.parent.glob(f".{db_path.name}.*"))
        assert leftovers == [], f"temp build artifacts leaked: {leftovers}"


class TestClipQuoteSafe:
    def test_clip_quote_safe_balances_unclosed_guillemets(self):
        from wiki.sources_db import clip_quote_safe

        # Text with an unclosed « after clipping
        text = "Опис: «давня рукописна книга псалмів із коментарями»."
        clipped = clip_quote_safe(text, max_chars=25)
        assert clipped.endswith("»")
        assert clipped.count("«") == clipped.count("»")

    def test_clip_quote_safe_strips_trailing_orphan_open_quote(self):
        from wiki.sources_db import clip_quote_safe

        text = "Початок «довга цитата»"
        clipped = clip_quote_safe(text, max_chars=9)
        assert clipped == "Початок"
        assert clipped.count("«") == 0
        assert clipped.count("»") == 0

    def test_clip_quote_safe_short_text_unchanged(self):
        from wiki.sources_db import clip_quote_safe

        text = "«Коротка цитата»"
        assert clip_quote_safe(text, max_chars=100) == text

    def test_clip_quote_safe_with_ellipsis(self):
        from wiki.sources_db import clip_quote_safe

        text = "«Довга цитата з книги Шевченка про мову»"
        clipped = clip_quote_safe(text, max_chars=20, ellipsis="…")
        assert clipped.endswith("…»")
        assert clipped.count("«") == clipped.count("»")

    def test_quote_safe_clip_alias(self):
        from wiki.sources_db import clip_quote_safe, quote_safe_clip

        assert quote_safe_clip is clip_quote_safe


@pytest.fixture()
def esum_heritage_rank_db(tmp_path):
    """Fixture DB with exact headwords and body-inner hits for ranking tests."""
    db_path = tmp_path / "esum_heritage_rank.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(
        """
        CREATE TABLE esum_etymology_meta (
            id INTEGER PRIMARY KEY,
            lemma TEXT NOT NULL,
            vol INTEGER NOT NULL,
            page INTEGER NOT NULL,
            entry_hash TEXT NOT NULL DEFAULT '',
            etymology_text TEXT NOT NULL,
            cognates TEXT NOT NULL DEFAULT '[]',
            source TEXT NOT NULL DEFAULT 'ЕСУМ'
        );
        CREATE VIRTUAL TABLE esum_etymology USING fts5(
            lemma,
            etymology_text,
            cognates,
            vol UNINDEXED,
            page UNINDEXED,
            tokenize = 'unicode61 remove_diacritics 0'
        );
        CREATE TABLE grinchenko (
            id INTEGER PRIMARY KEY,
            word TEXT NOT NULL,
            definition TEXT NOT NULL,
            source TEXT DEFAULT 'Грінченко'
        );
        CREATE TABLE style_guide (
            id INTEGER PRIMARY KEY,
            word TEXT NOT NULL,
            section TEXT DEFAULT '',
            text TEXT NOT NULL,
            source TEXT DEFAULT 'Антоненко-Давидович'
        );
        CREATE TABLE sum11 (
            id INTEGER PRIMARY KEY,
            word TEXT NOT NULL,
            definition TEXT NOT NULL,
            text TEXT DEFAULT '',
            source TEXT DEFAULT 'СУМ-11'
        );
        """
    )
    # 1. psaltyr: body contains "книга псалмів" and mentions "псл." (high heritage score)
    psaltyr_text = "псалтир — богослужебна книга псалмів Давида; псл. *pьsaltyrь."
    # 2. knyha: exact headword lemma
    knyha_text = "книга — книжка, зшиток аркушів; псл. *kъńiga."
    # 3. knyharnia: prefix lemma
    knyharnia_text = "книгарня — крамниця книг."

    conn.execute(
        """
        INSERT INTO esum_etymology_meta (id, lemma, vol, page, etymology_text, cognates, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (1, "псалтир", 4, 100, psaltyr_text, '["псл."]', "ЕСУМ vol. 4"),
    )
    conn.execute(
        """
        INSERT INTO esum_etymology (rowid, lemma, etymology_text, cognates, vol, page)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (1, "псалтир", psaltyr_text, '["псл."]', 4, 100),
    )

    conn.execute(
        """
        INSERT INTO esum_etymology_meta (id, lemma, vol, page, etymology_text, cognates, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (2, "книга", 2, 200, knyha_text, '["псл."]', "ЕСУМ vol. 2"),
    )
    conn.execute(
        """
        INSERT INTO esum_etymology (rowid, lemma, etymology_text, cognates, vol, page)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (2, "книга", knyha_text, '["псл."]', 2, 200),
    )

    conn.execute(
        """
        INSERT INTO esum_etymology_meta (id, lemma, vol, page, etymology_text, cognates, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (3, "книгарня", 2, 205, knyharnia_text, "[]", "ЕСУМ vol. 2"),
    )
    conn.execute(
        """
        INSERT INTO esum_etymology (rowid, lemma, etymology_text, cognates, vol, page)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (3, "книгарня", knyharnia_text, "[]", 2, 205),
    )

    # 4. golova: stressed headword in volume 1 (verifies diacritic normalization with volume filter)
    golova_text = "голова́ — частина тіла; псл. *golva."
    conn.execute(
        """
        INSERT INTO esum_etymology_meta (id, lemma, vol, page, etymology_text, cognates, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (4, "голова́", 1, 550, golova_text, '["псл."]', "ЕСУМ vol. 1"),
    )
    conn.execute(
        """
        INSERT INTO esum_etymology (rowid, lemma, etymology_text, cognates, vol, page)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (4, "голова́", golova_text, '["псл."]', 1, 550),
    )

    # Grinchenko entry for knyha
    conn.execute(
        "INSERT INTO grinchenko (word, definition) VALUES (?, ?)",
        ("книга", "Книга, книжка."),
    )

    # Style guide entries
    conn.execute(
        "INSERT INTO style_guide (word, text) VALUES (?, ?)",
        ("На протязі", "Кажіть: протягом."),
    )
    conn.execute(
        "INSERT INTO style_guide (word, text) VALUES (?, ?)",
        ("Приймати участь", "Кажіть: брати участь."),
    )

    # SUM11 entry
    conn.execute(
        "INSERT INTO sum11 (word, definition) VALUES (?, ?)",
        ("книга", "Зшите в один ексземпляр друковане або рукописне видання."),
    )

    conn.commit()
    conn.close()
    return db_path


class TestHeadwordFirstRanking:
    def test_search_esum_knyha_headword_ranks_above_psaltyr_body_hit(self, esum_heritage_rank_db):
        from wiki.sources_db import search_esum

        hits = search_esum("книга", db_path=esum_heritage_rank_db, limit=5)
        lemmas = [h["lemma"] for h in hits]

        # Exact headword 'книга' must rank above body-inner hit 'псалтир'
        assert lemmas[0] == "книга"
        assert "псалтир" in lemmas
        assert lemmas.index("книга") < lemmas.index("псалтир")

    def test_search_esum_quoted_and_stressed_headword_lookup(self, esum_heritage_rank_db):
        from wiki.sources_db import search_esum

        hits = search_esum("«кни́га»", db_path=esum_heritage_rank_db, limit=5)
        assert hits
        assert hits[0]["lemma"] == "книга"

    def test_search_esum_oversized_document_query_fails_closed_without_fuzzy_sql(self, esum_heritage_rank_db):
        from wiki.sources_db import search_esum, search_heritage

        oversized_document = ("український текст\n" * 3_000).strip()

        assert len(oversized_document.encode("utf-8")) > 50_000
        assert search_esum(oversized_document, db_path=esum_heritage_rank_db, limit=5) == []
        assert search_heritage(
            oversized_document,
            db_path=esum_heritage_rank_db,
            include_live_slovnyk=False,
            limit=5,
        ) == []

    def test_search_esum_oversized_exact_lemma_still_resolves(self, esum_heritage_rank_db):
        from wiki.sources_db import search_esum

        oversized_lemma = "а" * 25_001
        conn = sqlite3.connect(esum_heritage_rank_db)
        conn.execute(
            """
            INSERT INTO esum_etymology_meta (id, lemma, vol, page, etymology_text, cognates, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (99, oversized_lemma, 1, 999, "synthetic exact entry", "[]", "ЕСУМ synthetic"),
        )
        conn.commit()
        conn.close()

        hits = search_esum(oversized_lemma, db_path=esum_heritage_rank_db, limit=5)

        assert [hit["lemma"] for hit in hits] == [oversized_lemma]

    def test_search_esum_volume_filter_headword_and_body(self, esum_heritage_rank_db):
        from wiki.sources_db import search_esum

        # Volume 2 returns exact headword and prefix match, excludes vol 4 body hit
        hits_vol2 = search_esum("книга", volume=2, db_path=esum_heritage_rank_db, limit=5)
        lemmas_vol2 = [h["lemma"] for h in hits_vol2]
        assert "книга" in lemmas_vol2
        assert "книгарня" in lemmas_vol2
        assert "псалтир" not in lemmas_vol2
        assert all(h["vol"] == 2 for h in hits_vol2)

        # Volume 4 returns body hit, excludes vol 2 headword
        hits_vol4 = search_esum("книга", volume=4, db_path=esum_heritage_rank_db, limit=5)
        lemmas_vol4 = [h["lemma"] for h in hits_vol4]
        assert "псалтир" in lemmas_vol4
        assert "книга" not in lemmas_vol4
        assert all(h["vol"] == 4 for h in hits_vol4)

        # Stressed headword in DB resolves via meta path with volume filter
        hits_stressed = search_esum("голова", volume=1, db_path=esum_heritage_rank_db, limit=5)
        assert hits_stressed
        assert hits_stressed[0]["lemma"] == "голова́"
        assert hits_stressed[0]["vol"] == 1

    def test_search_heritage_knyha_ranks_above_psaltyr(self, esum_heritage_rank_db):
        from wiki.sources_db import search_heritage

        hits = search_heritage("книга", db_path=esum_heritage_rank_db, limit=10)
        words = [h["word"] for h in hits]

        # All headword matches (Grinchenko, ESUM) must rank ahead of 'псалтир' body hit
        assert words[0] == "книга"
        assert words[1] == "книга"
        assert "псалтир" in words
        assert words.index("книга") < words.index("псалтир")

    def test_search_style_guide_documented_examples_resolve(self, esum_heritage_rank_db):
        from wiki.sources_db import search_style_guide

        # Documented docstring examples: «На протязі», На протязі, протязі, «протязі»
        for query in ("«На протязі»", "На протязі", "протязі", "«протязі»"):
            hits = search_style_guide(query, db_path=esum_heritage_rank_db)
            assert len(hits) >= 1, f"Failed to return a row for {query!r}"
            assert hits[0]["word"] == "На протязі"

    def test_search_style_guide_headword_ranks_above_body_hit(self, esum_heritage_rank_db):
        from wiki.sources_db import search_style_guide

        # Headword hit "Приймати участь" must rank ahead of any entry having "участь" in body
        hits = search_style_guide("участь", db_path=esum_heritage_rank_db)
        assert len(hits) >= 1
        assert hits[0]["word"] == "Приймати участь"

    def test_search_style_guide_live_db_documented_examples(self):
        from wiki.sources_db import SOURCES_DB_PATH, search_style_guide

        if not SOURCES_DB_PATH.exists() or SOURCES_DB_PATH.stat().st_size < 1000:
            pytest.skip("sources.db not present")

        # "На протязі", "протязі", "Приймати участь" must all resolve against live DB
        for query in ("«На протязі»", "На протязі", "протязі", "«протязі»"):
            hits = search_style_guide(query)
            assert len(hits) >= 1, f"Failed to return a row for {query!r}"
            assert "протязі" in (hits[0]["word"] + hits[0]["text"]).lower()

        hits_uchast = search_style_guide("Приймати участь")
        assert len(hits_uchast) >= 1
        assert "приймати участь" in hits_uchast[0]["word"].lower()

    def test_search_definitions_quoted_and_case_variants(self, esum_heritage_rank_db):
        from wiki.sources_db import search_definitions

        for query in ("книга", "Книга", "«книга»", "«Книга»", "кни́га"):
            hits = search_definitions(query, db_path=esum_heritage_rank_db)
            assert len(hits) == 1, f"Failed for query {query!r}"
            assert hits[0]["word"] == "книга"
