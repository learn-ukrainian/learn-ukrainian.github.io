from __future__ import annotations

import json
import sqlite3

import pytest

from scripts.audit.generate_sentence_inventory import (
    VesumSentenceVerifier,
    _candidate_sentences,
    build_inventory,
    discover_practice_lexeme_paths,
    filter_residual_targets,
    load_daily_lemmas,
    load_daily_targets,
    load_inventory_rows,
    load_practice_targets,
    main,
    merge_inventory_rows,
    write_inventory,
)


def _sources_db(tmp_path):
    db = tmp_path / "sources.db"
    conn = sqlite3.connect(db)
    conn.executescript(
        """
        CREATE TABLE textbooks (id INTEGER PRIMARY KEY, chunk_id TEXT, title TEXT, text TEXT);
        CREATE VIRTUAL TABLE textbooks_fts USING fts5(title, text, content='textbooks', content_rowid='id');
        CREATE TABLE external_articles (id INTEGER PRIMARY KEY, chunk_id TEXT, title TEXT, text TEXT, source_file TEXT);
        CREATE VIRTUAL TABLE external_fts USING fts5(title, text, content='external_articles', content_rowid='id');
        INSERT INTO textbooks VALUES (1, 'grade-1-p-4', 'Grade 1', 'Ми живемо в Україні. Наша мова — українська.');
        INSERT INTO textbooks_fts(rowid, title, text) VALUES (1, 'Grade 1', 'Ми живемо в Україні. Наша мова — українська.');
        INSERT INTO external_articles VALUES (1, 'private-local-id', 'Private title', 'Я читаю українською щодня.', 'ulp_youtube');
        INSERT INTO external_fts(rowid, title, text) VALUES (1, 'Private title', 'Я читаю українською щодня.');
        """
    )
    conn.commit()
    conn.close()
    return db


def test_extracts_attributed_textbook_sentence(tmp_path) -> None:
    rows = build_inventory([{"lemma": "Україні", "lemmaId": "ukraini", "cefr": "A1"}], _sources_db(tmp_path))

    assert rows == [
        {
            "lemma": "Україні",
            "lemmaId": "ukraini",
            "sentence": "Ми живемо в Україні.",
            "targetForm": "Україні",
            "cefr": "A1",
            "uses": ["example"],
            "provenance": {
                "source": "textbook",
                "label": "Ukrainian school textbook",
                "locator": "grade-1-p-4",
                "title": "Grade 1",
            },
            "license": {
                "status": "not_openly_licensed",
                "useBasis": "short educational quotation with attribution",
            },
        }
    ]


def test_ulp_provenance_never_exposes_private_locator(tmp_path) -> None:
    rows = build_inventory(
        [{"lemma": "українською", "lemmaId": "ukrainskoiu"}], _sources_db(tmp_path), include_ulp=True
    )

    assert rows[0]["provenance"] == {"source": "ulp", "label": "Ukrainian Lessons Podcast"}
    assert "private-local-id" not in json.dumps(rows, ensure_ascii=False)
    assert "Private title" not in json.dumps(rows, ensure_ascii=False)


def test_inventory_can_keep_multiple_unique_sentences_per_lemma(tmp_path) -> None:
    db = _sources_db(tmp_path)
    conn = sqlite3.connect(db)
    conn.executescript(
        """
        INSERT INTO textbooks VALUES (
            2,
            'grade-1-p-5',
            'Grade 1',
            'Ми часто говоримо про Україну, але живемо в Україні.'
        );
        INSERT INTO textbooks_fts(rowid, title, text) VALUES (
            2,
            'Grade 1',
            'Ми часто говоримо про Україну, але живемо в Україні.'
        );
        INSERT INTO textbooks VALUES (
            3,
            'grade-1-p-6',
            'Grade 1',
            'Україні добре, коли діти читають українською.'
        );
        INSERT INTO textbooks_fts(rowid, title, text) VALUES (
            3,
            'Grade 1',
            'Україні добре, коли діти читають українською.'
        );
        """
    )
    conn.commit()
    conn.close()

    rows = build_inventory(
        [{"lemma": "Україні", "lemmaId": "ukraini", "cefr": "A1"}],
        db,
        max_per_lemma=2,
    )

    assert len(rows) == 2
    assert len({row["sentence"] for row in rows}) == 2
    assert {row["sentence"] for row in rows} <= {
        "Ми живемо в Україні.",
        "Ми часто говоримо про Україну, але живемо в Україні.",
        "Україні добре, коли діти читають українською.",
    }
    assert all(row["targetForm"] == "Україні" for row in rows)
    assert {row["provenance"]["locator"] for row in rows} <= {
        "grade-1-p-4",
        "grade-1-p-5",
        "grade-1-p-6",
    }


def test_textbook_search_prefers_language_books_and_skips_ranked_noise(tmp_path) -> None:
    db = _sources_db(tmp_path)
    conn = sqlite3.connect(db)
    conn.execute("ALTER TABLE textbooks ADD COLUMN subject TEXT DEFAULT 'ukrmova'")
    conn.execute(
        "INSERT INTO textbooks (id, chunk_id, title, text, subject) VALUES (?, ?, ?, ?, ?)",
        (2, "physics-noise", "Physics", "Місто спить, а люди читають.", "fizyka"),
    )
    conn.execute(
        "INSERT INTO textbooks_fts(rowid, title, text) VALUES (?, ?, ?)",
        (2, "Physics", "Місто спить, а люди читають."),
    )
    for row_id in range(3, 23):
        noise = "Прочитай місто і запиши відповідь."
        conn.execute(
            "INSERT INTO textbooks (id, chunk_id, title, text, subject) VALUES (?, ?, ?, ?, ?)",
            (row_id, f"noise-{row_id}", "Ukrainian textbook", noise, "ukrmova"),
        )
        conn.execute(
            "INSERT INTO textbooks_fts(rowid, title, text) VALUES (?, ?, ?)",
            (row_id, "Ukrainian textbook", noise),
        )
    clean = "Місто спить, а люди читають."
    conn.execute(
        "INSERT INTO textbooks (id, chunk_id, title, text, subject) VALUES (?, ?, ?, ?, ?)",
        (23, "language-clean", "Ukrainian textbook", clean, "ukrmova"),
    )
    conn.execute(
        "INSERT INTO textbooks_fts(rowid, title, text) VALUES (?, ?, ?)",
        (23, "Ukrainian textbook", clean),
    )
    conn.commit()
    conn.close()

    rows = build_inventory([{"lemma": "місто", "lemmaId": "misto", "cefr": "A1"}], db)

    assert rows[0]["sentence"] == clean
    assert rows[0]["provenance"]["locator"] == "language-clean"


def test_textbook_search_excludes_ulp_mirrors(tmp_path) -> None:
    db = _sources_db(tmp_path)
    conn = sqlite3.connect(db)
    conn.execute("ALTER TABLE textbooks ADD COLUMN source_file TEXT DEFAULT 'grade-1'")
    conn.execute("ALTER TABLE textbooks ADD COLUMN subject TEXT DEFAULT 'ukrmova'")
    conn.execute(
        "INSERT INTO textbooks (id, chunk_id, title, text, source_file, subject) VALUES (?, ?, ?, ?, ?, ?)",
        (
            2,
            "ulp-noise",
            "Podcast notes",
            "Публічний транскрипт містить приклади.",
            "ulp-5-00-lesson-notes",
            "ukrmova",
        ),
    )
    conn.execute(
        "INSERT INTO textbooks_fts(rowid, title, text) VALUES (?, ?, ?)",
        (2, "Podcast notes", "Публічний транскрипт містить приклади."),
    )
    clean = "Цей транскрипт містить приклади з підручника."
    conn.execute(
        "INSERT INTO textbooks (id, chunk_id, title, text, source_file, subject) VALUES (?, ?, ?, ?, ?, ?)",
        (3, "language-clean", "Ukrainian textbook", clean, "4-klas-ukrmova", "ukrmova"),
    )
    conn.execute(
        "INSERT INTO textbooks_fts(rowid, title, text) VALUES (?, ?, ?)",
        (3, "Ukrainian textbook", clean),
    )
    conn.commit()
    conn.close()

    rows = build_inventory([{"lemma": "транскрипт", "lemmaId": "transkript", "cefr": "C1"}], db)

    assert rows[0]["sentence"] == clean
    assert rows[0]["provenance"]["locator"] == "language-clean"


def test_inventory_rejects_non_positive_sentence_cap(tmp_path) -> None:
    with pytest.raises(ValueError, match="max_per_lemma"):
        build_inventory([], _sources_db(tmp_path), max_per_lemma=0)


def test_candidate_sentences_reject_formula_and_worksheet_fragments() -> None:
    rejected = (
        ("а", "2) Якщо а > 0, то нерівність перепишемо у вигляді ."),
        ("ом", "Дано: U = 30 В R R R 1 2 3 = Ом. Знайти I1?"),
        ("Іван", "У поемі є назви, ОКРІМ А Синопу Б Дніпра В Стамбула Г Царграда."),
        ("би", "2) Якби знав, де впаду, сінця (б/би) підстелив."),
    )
    for lemma, sentence in rejected:
        assert list(_candidate_sentences(sentence, lemma)) == []


def test_candidate_sentences_reject_source_bookkeeping_and_ocr_fragments() -> None:
    rejected = (
        ("де", "33.2 де Сформулюємо означення нескінченної границі функції."),
        ("а", "х є (-“; -а) (мал."),
        ("у", "Запишіть у вигляді визначеного інтеграла площу фігури."),
        ("ні", "У яких реченнях ні є часткою?"),
        ("ми", "просто було емоційно важко, але ми втомилися."),
        ("ти", "Вис\u00adко\u00adчи\u00adти як Пилип із конопель."),
        ("а", "Розглянемо кожний з них окремо, враховуючи ОДЗ параметра а."),
        ("а", "Прямі а і Ь лежать в одній площині - площині р і не збігаються."),
        ("у", "Сила у З Н розтягує пружину на 1 см."),
        ("ні", "Чеснота ні/ коли не старіє."),
        ("я", "☆☆☆ Я можу назвати найголовніші життєві навички."),
        ("з", "Збережіть презентацію у вашій папці у файлі з тим самим іменем."),
        ("а", "Пачка офісного паперу формату А4 містить 500 аркушів."),
        ("я", "Назва емоції: втома ____________________ Як я почуваюсь?"),
        ("зі", "Правило свердлика Як і штабовий магніт, котушка зі струмом має два полюси."),
        ("аеродром", "Спиши текст про аеродром."),
        ("змінити", "Поясни, що означає змінити форму слова."),
        ("ґрунт", "Поясни, навіщо розпушують і зволожують ґрунт, у якому вирощують рослини."),
        ("відродження", "Приãадайте значення поняття «національне відродження»."),
        ("ні", "Чеснота ні́/ коли не старіє."),
        ("обстрілювати", "Коли й ця спроба провалилася, вони почали обстрілювати місУ результаті якої операції?"),
        ("злий", "Злий, старий, здоровий, добрий, синій, чорний, гіркий, білий, червоний."),
        ("рівнина", "Гори Пагорби Рівнина Каньйон Мал."),
        ("пошкодження", "Причини й можливі наслідки пошкодження ДНК Молекула ДНК."),
        ("відповідність", "854.• Кожному числу поставили у відповідність відстань від точки."),
        ("скільки", "21.10.• Скільки трицифрових чисел можна записати?"),
        ("ціле", "Кожен елемент візерунка містить нескінченне ціле; • духовні якості переважають."),
        ("воло", "Воло..ий горіх ще називають гре..им."),
        ("вид", "Вид односкладного речення Приклад 1 безособове 2 означено-особове."),
        ("воно", "Г воно доходить до моєї кімнати."),
        ("о", "Джейн — О, я знаю."),
        ("умова", "Умова: написання міста має відповідати темі уроку."),
        ("сім", "Краще один раз побачити, Де сім господинь, там хата не метена."),
        ("наголосити", "Щоб наголосити на результаті, використовуємо форму: Підсніжники зірвано."),
        ("мільярд", "Числівники тисяча, мільйон, мільярд відмінюємо як іменники і т."),
        ("теперішній", "Форми часу: теперішній, минулий та майбутній."),
        ("репортаж", "Ви маєте зробити репортаж про події."),
        ("ютуб", "Слова: ютуб, нік, омбудсмен."),
    )
    for lemma, sentence in rejected:
        assert list(_candidate_sentences(sentence, lemma)) == []


def test_candidate_sentences_rejects_vesum_imperative_commands(tmp_path) -> None:
    vesum_db = tmp_path / "vesum.db"
    conn = sqlite3.connect(vesum_db)
    conn.execute("CREATE TABLE forms (word_form TEXT, lemma TEXT, tags TEXT, pos TEXT)")
    conn.executemany(
        "INSERT INTO forms VALUES (?, ?, ?, ?)",
        [
            ("побудуй", "побудувати", "verb:perf:impr:s:2", "verb"),
            ("з'ясуйте", "з'ясувати", "verb:perf:impr:p:2", "verb"),
            ("коли", "колоти", "verb:imperf:impr:s:2", "verb"),
        ],
    )
    conn.commit()
    conn.close()
    verifier = VesumSentenceVerifier(vesum_db)
    try:
        assert verifier.has_imperative("З’ясуйте") is True
        assert list(
            _candidate_sentences(
                "Побудуй звукову схему слова грудень.",
                "грудень",
                vesum=verifier,
            )
        ) == []
        assert list(
            _candidate_sentences(
                "З’ясуйте, як називається обласний центр.",
                "центр",
                vesum=verifier,
            )
        ) == []
        sentence = "Коли гриміло, казали, що то Ілля по небесному мосту калачі везе."
        assert list(_candidate_sentences(sentence, "Ілля", vesum=verifier)) == [sentence]
    finally:
        verifier.close()


def test_candidate_sentences_keeps_a_clean_short_function_word() -> None:
    sentence = "Ми говоримо, а ви читаєте."

    assert list(_candidate_sentences(sentence, "а")) == [sentence]


def test_candidate_sentences_matches_apostrophe_variants() -> None:
    sentence = "У мене є сім’я."

    assert list(_candidate_sentences(sentence, "сім'я")) == [sentence]


def test_daily_lemmas_and_written_schema(tmp_path) -> None:
    pool = tmp_path / "daily.json"
    pool.write_text(
        json.dumps([{"lemma": "дім", "slug": "dim", "cefr": "A1"}, {"lemma": "дім"}, {"lemma": ""}]),
        encoding="utf-8",
    )
    assert load_daily_lemmas(pool) == ["дім"]
    assert load_daily_targets(pool) == [{"lemma": "дім", "lemmaId": "dim", "cefr": "A1"}]
    out = tmp_path / "inventory.json"
    write_inventory([], out)
    assert json.loads(out.read_text(encoding="utf-8")) == {
        "schema": "atlas-sentence-inventory",
        "schemaVersion": 1,
        "rows": [],
    }


def test_residual_target_filter_and_inventory_merge_preserve_existing_rows(tmp_path) -> None:
    inventory = tmp_path / "inventory.json"
    existing = {
        "lemma": "дім",
        "lemmaId": "dim",
        "sentence": "Це дім.",
        "targetForm": "дім",
        "uses": ["example"],
        "provenance": {"source": "fixture", "label": "Fixture"},
        "license": {"status": "fixture"},
    }
    write_inventory([existing], inventory)

    targets = [
        {"lemma": "дім", "lemmaId": "dim", "cefr": "A1"},
        {"lemma": "місто", "lemmaId": "misto", "cefr": "A1"},
    ]
    assert filter_residual_targets(targets, inventory) == [targets[1]]

    new_row = {**existing, "lemma": "місто", "lemmaId": "misto", "sentence": "Це місто."}
    merged = merge_inventory_rows(load_inventory_rows(inventory), [new_row])
    assert [row["lemmaId"] for row in merged] == ["dim", "misto"]


def _practice_shard(path, level, rows):
    path.write_text(
        json.dumps(
            {
                "schema": "atlas-practice-lexemes",
                "schemaVersion": 1,
                "level": level,
                "lexemes": rows,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_load_practice_targets_reads_all_shards_and_deduplicates_identity(tmp_path) -> None:
    a1 = tmp_path / "practice-lexemes.A1.json"
    a2 = tmp_path / "practice-lexemes.A2.json"
    _practice_shard(a1, "A1", [{"lemmaId": "dim", "lemma": "дім", "cefr": "A1"}])
    _practice_shard(a2, "A2", [{"lemmaId": "misto", "lemma": "місто"}])

    assert load_practice_targets([a2, a1, a1]) == [
        {"lemmaId": "dim", "lemma": "дім", "cefr": "A1"},
        {"lemmaId": "misto", "lemma": "місто", "cefr": "A2"},
    ]


def test_load_practice_targets_rejects_schema_and_level_conflicts(tmp_path) -> None:
    bad_schema = tmp_path / "bad.json"
    bad_schema.write_text(json.dumps({"schema": "wrong"}), encoding="utf-8")
    with pytest.raises(ValueError, match="atlas-practice-lexemes"):
        load_practice_targets([bad_schema])

    a1 = tmp_path / "practice-lexemes.A1.json"
    a2 = tmp_path / "practice-lexemes.A2.json"
    _practice_shard(a1, "A1", [{"lemmaId": "same", "lemma": "дім", "cefr": "A1"}])
    _practice_shard(a2, "A2", [{"lemmaId": "same", "lemma": "місто", "cefr": "A2"}])
    with pytest.raises(ValueError, match="conflicting practice target"):
        load_practice_targets([a1, a2])


def test_discover_practice_lexeme_paths_fails_closed_on_partial_hydration(tmp_path) -> None:
    for level in ("A1", "A2", "B1", "B2"):
        _practice_shard(tmp_path / f"practice-lexemes.{level}.json", level, [])
    with pytest.raises(FileNotFoundError, match=r"practice-lexemes\.C1\.json"):
        discover_practice_lexeme_paths(tmp_path)


def test_main_accepts_explicit_practice_targets(tmp_path) -> None:
    shard = tmp_path / "practice-lexemes.A1.json"
    _practice_shard(shard, "A1", [{"lemmaId": "ukraini", "lemma": "Україні"}])
    out = tmp_path / "inventory.json"

    assert main(
        [
            "--practice-lexemes",
            str(shard),
            "--sources-db",
            str(_sources_db(tmp_path)),
            "--vesum-db",
            str(tmp_path / "missing-vesum.db"),
            "--out",
            str(out),
        ]
    ) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["rows"][0]["lemmaId"] == "ukraini"


def test_main_rejects_mixed_daily_and_practice_target_modes(tmp_path) -> None:
    daily = tmp_path / "daily.json"
    daily.write_text(json.dumps([]), encoding="utf-8")
    shard = tmp_path / "practice-lexemes.A1.json"
    _practice_shard(shard, "A1", [])

    with pytest.raises(SystemExit):
        main(["--daily-pool", str(daily), "--practice-lexemes", str(shard)])
