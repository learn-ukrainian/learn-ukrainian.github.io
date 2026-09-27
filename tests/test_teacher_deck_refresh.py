"""Teacher-table deck (#8843 P1): table sync rules, generator rules, refresh, independent checker.

Synthetic DOCX/SQLite fixtures only; the private teacher document is never read here.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import shutil
import sqlite3
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from scripts.audit import check_teacher_deck as checker
from scripts.audit.generate_practice_deck import TEACHER_CLOZE_GZIP_LIMIT, TEACHER_DECK_GZIP_LIMIT
from scripts.lexicon import teacher_deck
from scripts.lexicon import teacher_deck_shard as shard
from scripts.lexicon.sync_teacher_table_deck import (
    TeacherTableRow,
    build_deck_entries,
    entry_id_for_key,
    normalize_uk_key,
)

ROOT = Path(__file__).resolve().parents[1]
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
HEADING = "Combined Master Vocabulary Table (#3)"


# ----------------------------------------------------------------------------- table sync


def rows(*pairs: tuple[str, str]) -> list[TeacherTableRow]:
    return [TeacherTableRow(row=index, uk=uk, en=en) for index, (uk, en) in enumerate(pairs, start=1)]


def test_normalised_key_strips_stress_unifies_apostrophes_and_case() -> None:
    assert normalize_uk_key("  Зв’я́зок ") == "зв'язок"
    assert normalize_uk_key("ЗВʼЯЗОК") == normalize_uk_key("зв'язок")


def test_entry_id_depends_only_on_the_normalised_key() -> None:
    first = build_deck_entries(rows(("Кіт", "Cat"), ("Стіл", "Table"))).entries
    moved = build_deck_entries(rows(("Стіл", "Desk"), ("кі́т", "Tomcat"))).entries
    assert {e["key"]: e["entryId"] for e in first} == {e["key"]: e["entryId"] for e in moved}
    assert first[0]["entryId"] == entry_id_for_key("кіт")


def test_duplicates_merge_keep_every_distinct_meaning_and_are_reported() -> None:
    build = build_deck_entries(rows(("Єнот", "Raccoon"), ("Стіл", "Table"), ("єнот", "racoon"), ("Стіл", "table")))
    by_key = {entry["key"]: entry for entry in build.entries}
    assert by_key["єнот"]["en"] == "Raccoon; racoon"
    assert by_key["єнот"]["sourceRows"] == [1, 3]
    assert by_key["єнот"]["sourceKeys"] == ["Єнот", "єнот"]
    assert by_key["стіл"]["en"] == "Table"
    assert build.source_keys == ["Єнот", "Стіл", "єнот"]
    assert [(m["uk"], m["differentEnglish"]) for m in build.merges] == [("Єнот", True), ("Стіл", False)]


def test_first_seen_is_carried_forward_and_new_keys_are_newest() -> None:
    first = build_deck_entries(rows(("Кіт", "Cat"), ("Стіл", "Table")))
    # Reordered table with one new key in the middle: survivors keep their keys.
    second = build_deck_entries(rows(("Стіл", "Table"), ("Вікно", "Window"), ("Кіт", "Cat")), first.entries)
    order = {entry["key"]: entry["firstSeen"] for entry in second.entries}
    assert order["кіт"] == 1 and order["стіл"] == 2
    assert order["вікно"] == 3


def test_a_row_without_english_fails_the_sync() -> None:
    with pytest.raises(ValueError, match="no English"):
        build_deck_entries(rows(("Кіт", "")))


# ----------------------------------------------------------------------------- generator rules


def test_english_parts_follow_the_spec_normalisation() -> None:
    assert shard.english_parts("To pour solids / serve food (impf); The Cat, an owl") == [
        "pour solids / serve food",
        "cat",
        "owl",
    ]


def test_overlap_is_equality_or_whole_word_containment() -> None:
    assert shard.parts_overlap(["wipe"], ["wipe"])
    assert shard.parts_overlap(["break"], ["break down"])
    assert not shard.parts_overlap(["cat"], ["catalogue"])
    entries = [
        {"entryId": "a", "en": "To read (impf.)"},
        {"entryId": "b", "en": "To read (pf.)"},
        {"entryId": "c", "en": "Cat"},
    ]
    overlaps, partners = shard.overlap_graph(entries)
    assert overlaps == {"a": ["b"], "b": ["a"], "c": []}
    assert partners == {"a": [], "b": [], "c": []}


def test_source_aspects_that_differ_split_an_otherwise_identical_pair() -> None:
    entries = [
        {"entryId": "a", "en": "To wipe (impf.)"},
        {"entryId": "b", "en": "To wipe (pf.)"},
        {"entryId": "c", "en": "To wipe off (pf.)"},
        {"entryId": "d", "en": "To marry off (impf./pf.)"},
        {"entryId": "e", "en": "To marry off (pf.)"},
    ]
    aspects = {"a": "imperf", "b": "perf", "c": "perf", "d": "dual", "e": "perf"}
    overlaps, partners = shard.overlap_graph(entries, aspects)
    assert partners["a"] == ["b"] and partners["b"] == ["a"]
    # Containment is not "otherwise identical", and dual never splits.
    assert overlaps["a"] == ["c"] and overlaps["b"] == ["c"]
    assert overlaps["d"] == ["e"]
    assert checker.own_overlaps(entries, aspects) == (
        {key: set(value) for key, value in overlaps.items()},
        {key: set(value) for key, value in partners.items()},
    )


def _evidence(vesum: set[str], ulif: set[str]) -> shard.LemmaEvidence:
    return shard.LemmaEvidence(frozenset(vesum), False, frozenset(ulif), False)


@pytest.mark.parametrize(
    ("vesum", "ulif", "expected"),
    [
        ({"imperf"}, {"imperf"}, ("imperf", "agree")),
        ({"perf"}, set(), ("perf", "vesum-only")),
        (set(), {"perf"}, ("perf", "ulif-only")),
        ({"imperf", "perf"}, {"dual"}, ("dual", "agree")),
        (set(), {"dual"}, ("dual", "ulif-only")),
        ({"imperf"}, {"perf"}, ("unknown", "conflict")),
        ({"imperf", "perf"}, {"perf"}, ("unknown", "conflict")),
        ({"imperf", "perf"}, {"imperf", "perf"}, ("unknown", "homograph")),
        ({"imperf", "perf"}, set(), ("unknown", "vesum-only")),
        (set(), set(), ("unknown", "none")),
    ],
)
def test_aspect_comes_from_vesum_and_checked_ulif(vesum: set[str], ulif: set[str], expected: tuple[str, str]) -> None:
    assert shard.resolve_aspect(_evidence(vesum, ulif)) == expected
    assert checker.decide_aspect(vesum, ulif) == expected


@pytest.mark.parametrize(
    ("teacher", "aspect", "shown"),
    [
        ("To wipe (impf)", "perf", "To wipe (pf.)"),
        ("To implement (perf); to introduce", "imperf", "To implement; to introduce (impf.)"),
        (
            "To pour solids / serve food (impf); To pour solids / serve food (perf)",
            "dual",
            "To pour solids / serve food (impf./pf.)",
        ),
        ("To explode (impf)", "unknown", "To explode"),
        ("To bribe (idiom) (impf)", "imperf", "To bribe (idiom) (impf.)"),
        ("Cat", None, "Cat"),
    ],
)
def test_teacher_markers_are_replaced_by_the_source_label(teacher: str, aspect: str | None, shown: str) -> None:
    assert shard.display_english(teacher, aspect) == shown
    assert checker.own_display(teacher, aspect) == shown


@pytest.mark.parametrize(
    ("teacher", "senses", "rule", "index"),
    [
        ("Cat", ["tomcat"], "single-sense", 0),
        ("Dog", ["dog", "hound (hunting)"], "unique-match", 0),
        ("Fair", ["fair (just)", "fair (market)"], "ambiguous", None),
        ("Fair", ["market", "exhibition"], "no-match", None),
        ("Fair", [], "no-sense", None),
    ],
)
def test_mechanical_sense_rule(teacher: str, senses: list[str], rule: str, index: int | None) -> None:
    resolved = shard.resolve_sense(teacher, senses)
    assert (resolved["rule"], resolved["senseIndex"]) == (rule, index)
    assert resolved["usable"] is (index is not None)


def test_budget_constants_match_the_site_build_gate() -> None:
    script = (ROOT / "site/scripts/hydrate-teacher-deck.mjs").read_text(encoding="utf-8")
    limits = {
        name: int(value.replace("_", ""))
        for name, value in re.findall(r"export const (TEACHER_\w+_GZIP_LIMIT) = ([\d_]+);", script)
    }
    assert limits == {
        "TEACHER_DECK_GZIP_LIMIT": TEACHER_DECK_GZIP_LIMIT,
        "TEACHER_CLOZE_GZIP_LIMIT": TEACHER_CLOZE_GZIP_LIMIT,
    }


def test_checker_is_independent_of_the_generator() -> None:
    tree = ast.parse((ROOT / "scripts/audit/check_teacher_deck.py").read_text(encoding="utf-8"))
    imported = {
        node.module if isinstance(node, ast.ImportFrom) else alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert not any(str(name).startswith("scripts") for name in imported), imported


def test_committed_frozen_key_list_pins_the_denominator() -> None:
    frozen = json.loads((ROOT / "site/src/data/lexicon-teacher-deck-frozen-keys.json").read_text(encoding="utf-8"))
    assert frozen["docxSha256"].startswith("35da757f")
    assert len(frozen["keys"]) == frozen["sourceKeyCount"] == 1134
    assert frozen["entryCount"] == 1125
    assert frozen["rawDataRows"] == 1155


# ----------------------------------------------------------------------------- synthetic end-to-end

TABLE = [
    ("Кіт", "Cat"),
    ("Собака", "Dog"),
    ("Будинок", "House"),
    ("Стіл", "Table"),
    ("Вікно", "Window"),
    ("Читати", "To read (impf)"),
    ("Прочитати", "To read (perf)"),
    ("Зелений чай", "Green tea"),
    ("кіт", "cat"),
    ("Чорна кава", "Black coffee"),
    ("Свіжий хліб", "Fresh bread"),
    ("Теплий дім", "Warm home"),
    ("Писати", "To write (perf)"),  # the sources say imperfective: marker contradicted
    ("Женити", "To marry off (impf)"),  # ULIF: biaspectual
    ("Оженити", "To marry off (perf)"),
    ("Випробування", "Challenge / Trial"),  # a real overlap with Кинути виклик
    ("Кинути виклик", "To challenge"),
]
LESSONS = [
    ("01.09.2025", ["The cat is sleeping on the table.", "Кіт спить на столі."]),
    ("08.09.2025", ["I drink green tea every morning.", "Я п'ю зелений чай щоранку."]),
    ("15.09.2025", ["Olena bought a cat on 12 May.", "Олена купила кота 12 травня."]),
]
TEXTBOOK = "Собака лежить біля будинку. Наш собака лежить на траві."
VESUM_FORMS = [
    ("кіт", "кіт", "noun", "noun:anim:m:v_naz"),
    ("кота", "кіт", "noun", "noun:anim:m:v_rod"),
    ("коті", "кіт", "noun", "noun:anim:m:v_mis"),
    ("собака", "собака", "noun", "noun:anim:m:v_naz"),
    ("собаки", "собака", "noun", "noun:anim:m:v_rod"),
    ("собаці", "собака", "noun", "noun:anim:m:v_mis"),
    ("будинок", "будинок", "noun", "noun:inanim:m:v_naz"),
    ("будинку", "будинок", "noun", "noun:inanim:m:v_rod"),
    ("будинку", "будинок", "noun", "noun:inanim:m:v_mis"),
    ("стіл", "стіл", "noun", "noun:inanim:m:v_naz"),
    ("стола", "стіл", "noun", "noun:inanim:m:v_rod"),
    ("столі", "стіл", "noun", "noun:inanim:m:v_mis"),
    ("вікно", "вікно", "noun", "noun:inanim:n:v_naz"),
    ("вікні", "вікно", "noun", "noun:inanim:n:v_mis"),
    ("читати", "читати", "verb", "verb:imperf:inf"),
    ("прочитати", "прочитати", "verb", "verb:perf:inf"),
    ("спить", "спати", "verb", "verb:imperf:pres:s:3"),
    ("лежить", "лежати", "verb", "verb:imperf:pres:s:3"),
    ("п'ю", "пити", "verb", "verb:imperf:pres:s:1"),
    ("писати", "писати", "verb", "verb:imperf:inf"),
    ("женити", "женити", "verb", "verb:imperf:inf"),
    ("женити", "женити", "verb", "verb:perf:inf"),
    ("оженити", "оженити", "verb", "verb:perf:inf"),
    ("випробування", "випробування", "noun", "noun:inanim:n:v_naz"),
    ("кинути", "кинути", "verb", "verb:perf:inf"),
    ("виклик", "виклик", "noun", "noun:inanim:m:v_naz"),
    ("Олена", "Олена", "noun", "noun:anim:f:v_naz:prop:fname"),
]
# Checked ULIF entries (homonym_checked, label); the unchecked row must be ignored.
ULIF_ENTRIES = [
    ("читати", 1, "дієслово доконаного виду", 0),
    ("прочитати", 1, "дієслово доконаного виду", 1),
    ("писати", 1, "дієслово недоконаного виду", 1),
    ("женити", 1, "дієслово недоконаного і доконаного виду", 1),
    ("оженити", 1, "дієслово доконаного виду", 1),
    ("випробування", 1, "іменник середнього роду", 1),
]
ATLAS = {
    "кіт": ("noun", ["cat"], None),
    "собака": ("noun", ["dog", "hound (hunting dog)"], "соба́ка"),
    "будинок": ("noun", ["house"], "буди́нок"),
    "стіл": ("noun", ["table", "desk"], None),
    "вікно": ("noun", ["window"], "вікно́"),
    "читати": ("verb", ["to read"], "чита́ти"),
    "писати": ("verb", ["to write"], "писа́ти"),
    "зелений чай": ("phrase", ["green tea"], None),
}


def _p(text: str, style: str = "") -> str:
    prop = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    return f"<w:p>{prop}<w:r><w:t>{text}</w:t></w:r></w:p>"


def _write_docx(path: Path, table: list[tuple[str, str]], lessons: list[tuple[str, list[str]]] | None = None) -> None:
    body = "".join(_p(date) + "".join(_p(line) for line in lines) for date, lines in (lessons or LESSONS))
    header = "<w:tr>" + "".join(f"<w:tc>{_p(c)}</w:tc>" for c in ("Current", "Ukrainian", "English")) + "</w:tr>"
    data = "".join(
        f"<w:tr><w:tc>{_p(str(n))}</w:tc><w:tc>{_p(uk)}</w:tc><w:tc>{_p(en)}</w:tc></w:tr>"
        for n, (uk, en) in enumerate(table, start=1)
    )
    body += _p("Appendix", "Title") + _p(HEADING) + f"<w:tbl>{header}{data}</w:tbl>"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", f'<w:document xmlns:w="{W}"><w:body>{body}</w:body></w:document>')


@pytest.fixture
def world(tmp_path: Path) -> dict[str, Path]:
    docx = tmp_path / "master.docx"
    _write_docx(docx, TABLE)
    sources = tmp_path / "sources.db"
    with sqlite3.connect(sources) as conn:
        conn.executescript(
            """
            CREATE TABLE textbooks (
                id INTEGER PRIMARY KEY, chunk_id TEXT UNIQUE NOT NULL, title TEXT, text TEXT,
                source_file TEXT, grade TEXT, author TEXT, author_uk TEXT, char_count INTEGER);
            CREATE VIRTUAL TABLE textbooks_fts USING fts5(title, text, content='textbooks', content_rowid='id');
            CREATE TRIGGER textbooks_ai AFTER INSERT ON textbooks BEGIN
                INSERT INTO textbooks_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
            END;
            """
        )
        conn.execute(
            "INSERT INTO textbooks (chunk_id, title, text, source_file) VALUES (?, ?, ?, ?)",
            ("5-klas-test_s0001", "Сторінка 1", TEXTBOOK, "5-klas-test"),
        )
        conn.execute(
            "CREATE TABLE ulif_dictua_entries (id INTEGER PRIMARY KEY, normalized_query TEXT, homonym_index INTEGER, "
            "grammatical_label TEXT, homonym_checked INTEGER, status TEXT)"
        )
        conn.executemany(
            "INSERT INTO ulif_dictua_entries (normalized_query, homonym_index, grammatical_label, homonym_checked, "
            "status) VALUES (?, ?, ?, ?, 'ok')",
            ULIF_ENTRIES,
        )
    vesum = tmp_path / "vesum.db"
    with sqlite3.connect(vesum) as conn:
        conn.execute("CREATE TABLE forms_all (word_form TEXT, lemma TEXT, pos TEXT, tags TEXT)")
        conn.execute("CREATE VIEW forms AS SELECT word_form, lemma, tags, pos FROM forms_all")
        conn.executemany("INSERT INTO forms_all VALUES (?, ?, ?, ?)", VESUM_FORMS)
        conn.execute("CREATE TABLE vesum_build_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute("INSERT INTO vesum_build_metadata VALUES ('schema_version', 'fixture')")
    atlas = tmp_path / "atlas.db"
    with sqlite3.connect(atlas) as conn:
        conn.execute(
            "CREATE TABLE article_payloads (slug TEXT, route_order INTEGER, payload_json TEXT, is_public_route INTEGER)"
        )
        conn.execute("CREATE TABLE manifest_metadata (key TEXT PRIMARY KEY, value_json TEXT)")
        conn.execute("INSERT INTO manifest_metadata VALUES ('version', '\"fixture\"')")
        for order, (lemma, (pos, english, stressed)) in enumerate(sorted(ATLAS.items())):
            enrichment: dict[str, object] = {"translation": {"en": english}}
            if stressed:
                enrichment["stress"] = {"form": stressed, "source": "fixture"}
            payload = {"lemma": lemma, "url_slug": lemma, "gloss": english[0], "pos": pos, "enrichment": enrichment}
            conn.execute(
                "INSERT INTO article_payloads VALUES (?, ?, ?, 1)",
                (lemma, order, json.dumps(payload, ensure_ascii=False)),
            )
    verdicts = tmp_path / "verdicts.yaml"
    verdicts.write_text("approved: []\n", encoding="utf-8")
    withheld = tmp_path / "withheld.json"
    _write_ledger(withheld, {})
    return {
        "docx": docx,
        "sources": sources,
        "vesum": vesum,
        "atlas": atlas,
        "verdicts": verdicts,
        "out": tmp_path / "deck",
        "table": tmp_path / "table-deck.json",
        "frozen": tmp_path / "frozen-keys.json",
        "pointer": tmp_path / "pointer.json",
        "withheld": withheld,
    }


def _write_ledger(path: Path, withheld: dict[str, str], kept: tuple[str, ...] = ()) -> None:
    """Ledger fixture from sentences (hashed here, as the committed file never holds text)."""

    stamp = {"reviewer": "fixture", "reviewedAt": "2026-09-27"}
    payload = {
        "schema": shard.WITHHELD_SCHEMA,
        "schemaVersion": 1,
        "withheld": [
            {"sentenceSha256": shard.sentence_sha256(text), "code": code, **stamp} for text, code in withheld.items()
        ],
        "kept": [{"sentenceSha256": shard.sentence_sha256(text), **stamp} for text in kept],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _refresh(world: dict[str, Path], *extra: str) -> int:
    return teacher_deck.main(
        [
            "refresh",
            "--docx",
            str(world["docx"]),
            "--sources-db",
            str(world["sources"]),
            "--atlas-db",
            str(world["atlas"]),
            "--vesum-db",
            str(world["vesum"]),
            "--synonym-verdicts",
            str(world["verdicts"]),
            "--out-dir",
            str(world["out"]),
            "--table-deck",
            str(world["table"]),
            "--frozen-keys",
            str(world["frozen"]),
            "--pointer",
            str(world["pointer"]),
            "--withheld",
            str(world["withheld"]),
            *extra,
        ]
    )


def _check(deck_dir: Path, world: dict[str, Path] | None = None) -> tuple[int, str]:
    args = ["--deck-dir", str(deck_dir)]
    if world:
        args += ["--docx", str(world["docx"]), "--vesum-db", str(world["vesum"]), "--sources-db", str(world["sources"])]
        args += ["--atlas-db", str(world["atlas"]), "--withheld", str(world["withheld"])]
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/audit/check_teacher_deck.py"), *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    return result.returncode, result.stdout


def _hashes(world: dict[str, Path]) -> dict[str, str]:
    files = [*sorted(world["out"].iterdir()), world["table"], world["frozen"]]
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in files}


def test_refresh_builds_a_checked_deck_and_reruns_byte_identically(
    world: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    assert _refresh(world) == 0
    first_output = capsys.readouterr().out
    assert "table: 17 rows, 17 distinct source keys, 16 entries, 1 merged" in first_output
    assert "teacher deck check: PASS" in first_output
    assert "[2025-09-01] Кіт спить на столі." in first_output
    assert "teacher aspect markers in the English (stripped, never the authority): (impf) x2, (perf) x3" in first_output

    deck = json.loads((world["out"] / shard.DECK_FILE).read_text(encoding="utf-8"))
    cloze = json.loads((world["out"] / shard.CLOZE_FILE).read_text(encoding="utf-8"))
    entries = {entry["key"]: entry for entry in deck["entries"]}
    assert entries["кіт"]["en"] == "Cat" and entries["кіт"]["sourceRows"] == [1, 9]
    # An aspect pair split by the sources: the same English, each with an EN->UK card
    # whose prompt shows the source label (читати: VESUM only; the unchecked ULIF row is ignored).
    read, read_pf = entries["читати"], entries["прочитати"]
    assert (read["aspect"]["value"], read["aspect"]["basis"]) == ("imperf", "vesum-only")
    assert (read_pf["aspect"]["value"], read_pf["aspect"]["basis"]) == ("perf", "agree")
    assert read["aspectPartners"] == [read_pf["entryId"]] and read["conflicts"] == []
    assert read["cards"]["production"]["choice"]["prompt"] == "To read (impf.)"
    assert read_pf["cards"]["production"]["choice"]["prompt"] == "To read (pf.)"
    assert read["teacherEn"] == "To read (impf)"
    # The teacher's (perf) is contradicted by VESUM and ULIF: label from the sources,
    # disagreement recorded, grammar modes kept.
    write = entries["писати"]
    assert write["en"] == "To write (impf.)"
    assert write["aspect"]["markerAgrees"] is False and write["atlas"]["identityConflict"] is False
    assert write["cards"]["grammar"]["items"] == [{"mode": "stress", "id": f"{write['entryId']}:stress"}]
    # Dual aspect (ULIF) still overlaps its perfective partner: no EN->UK card for either.
    marry = entries["женити"]
    assert (marry["aspect"]["value"], marry["en"]) == ("dual", "To marry off (impf./pf.)")
    assert marry["cards"]["production"] is None and entries["оженити"]["cards"]["production"] is None
    # A real overlap stays an overlap.
    assert entries["кинути виклик"]["aspect"]["lemma"] == "кинути"
    assert entries["випробування"]["conflicts"] == [entries["кинути виклик"]["entryId"]]
    assert entries["випробування"]["cards"]["production"] is None
    assert entries["вікно"]["cards"]["production"]["cardId"] == f"{entries['вікно']['entryId']}:production"
    coverage = json.loads((world["out"] / shard.COVERAGE_FILE).read_text(encoding="utf-8"))
    assert [row["uk"] for row in coverage["residuals"]["aspectMarkerDisagreements"]] == ["Писати"]
    by_entry = {}
    for item in cloze["cloze"]:
        by_entry.setdefault(item["entryId"], []).append(item)
    cat_items = by_entry[entries["кіт"]["entryId"]]
    assert [item["source"] for item in cat_items] == ["teacher-lesson", "teacher-lesson"]
    assert cat_items[1]["clozeEn"] == "The cat is sleeping on the table."
    tea = by_entry[entries["зелений чай"]["entryId"]][0]
    assert tea["form"] == "зелений чай" and tea["sentence"] == "Я п'ю ___ щоранку."
    dog = by_entry[entries["собака"]["entryId"]][0]
    assert dog["source"] == "textbook" and dog["attribution"]["locator"] == "5-klas-test_s0001"
    table_labels = sorted(o["label"] for o in by_entry[entries["стіл"]["entryId"]][0]["options"])
    assert table_labels == ["будинку", "коті", "собаці", "столі"]  # same case slot, deck entries only
    assert entries["вікно"]["cards"]["grammar"]["items"] == [
        {"mode": "stress", "id": f"{entries['вікно']['entryId']}:stress"}
    ]
    assert entries["зелений чай"]["cards"]["grammar"] is None  # multiword: never grammar

    code, report = _check(world["out"], world)
    assert code == 0, report
    assert "teacher deck check: PASS" in report
    assert "entries without an EN->UK card: 4 (3 single-word, 1 multiword)" in report

    review = json.loads((world["out"] / shard.REVIEW_FILE).read_text(encoding="utf-8"))
    assert shard.REVIEW_FILE not in teacher_deck.PACKAGE_FILES
    # The empty ledger reviewed nothing: every served lesson cloze item is queued, one row
    # per item (Кіт спить на столі. serves кіт and стіл); the fixture VESUM lacks most
    # function words, so every sentence has unknown tokens.
    assert review["counts"] == {
        "servedLessonItems": 4,
        "servedLessonSentences": 3,
        "sentences": 4,
        "distinctSentences": 3,
        "flaggedSentences": {"proper_noun_tokens": 1, "vesum_unknown_tokens": 4, "digits_or_contact": 1},
    }
    olena = next(row for row in review["sentences"] if row["sentence"].startswith("Олена"))
    assert olena["lessonDate"] == "2025-09-15" and olena["entry"] == "Кіт"
    assert olena["flags"] == {
        "proper_noun_tokens": [{"token": "Олена", "reasons": ["vesum:fname", "vesum:prop"]}],
        "vesum_unknown_tokens": ["купила", "травня"],
        "digits_or_contact": [{"kind": "digits", "text": "12"}],
    }
    assert olena["sentenceSha256"] == shard.sentence_sha256(olena["sentence"])
    assert "queued items flagged: proper_noun_tokens 1, vesum_unknown_tokens 4, digits_or_contact 1" in first_output
    assert "lesson-sentence review queue: 4 of 4 served lesson cloze items (3 of 3 distinct sentences)" in first_output

    before = _hashes(world)
    assert _refresh(world) == 0
    second_output = capsys.readouterr().out
    assert "no-op: artifacts unchanged" in second_output
    assert "publish: skipped (pointer NOT updated)" in second_output
    assert "inserted 0, unchanged 3" in second_output
    assert _hashes(world) == before


def test_refresh_reports_meaning_changes_and_keeps_order_keys(
    world: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    assert _refresh(world) == 0
    capsys.readouterr()
    changed = [(uk, "Dwelling" if uk == "Будинок" else en) for uk, en in TABLE] + [("Лампа", "Lamp")]
    changed.insert(0, changed.pop(3))  # move Стіл to the top of the table
    _write_docx(world["docx"], changed)
    assert _refresh(world, "--skip-ingest") == 0
    output = capsys.readouterr().out
    assert "added entries: 1\n  Лампа = Lamp" in output
    assert "Будинок: en: 'House' -> 'Dwelling'" in output
    deck = json.loads((world["out"] / shard.DECK_FILE).read_text(encoding="utf-8"))
    order = {entry["key"]: entry["firstSeen"] for entry in deck["entries"]}
    assert order["стіл"] == 4 and order["лампа"] == max(order.values())


def _plant(world: dict[str, Path], tmp_path: Path, name: str, mutate, *, with_sources: bool = False) -> tuple[int, str]:
    planted = tmp_path / "planted"
    shutil.copytree(world["out"], planted)
    payload = json.loads((planted / name).read_text(encoding="utf-8"))
    mutate(payload)
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    (planted / name).write_bytes(data)
    manifest = json.loads((planted / shard.MANIFEST_FILE).read_text(encoding="utf-8"))
    for record in manifest["files"]:
        if record["path"] == name:
            record.update(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
    (planted / shard.MANIFEST_FILE).write_text(json.dumps(manifest), encoding="utf-8")
    return _check(planted, world if with_sources else None)


def test_checker_fails_when_an_answer_is_missing_from_its_options(world: dict[str, Path], tmp_path: Path) -> None:
    assert _refresh(world) == 0

    def drop_answer(cloze: dict) -> None:
        for option in cloze["cloze"][0]["options"]:
            if option["kind"] == "answer":
                option["label"] = "хата"

    code, report = _plant(world, tmp_path, shard.CLOZE_FILE, drop_answer)
    assert code == 1 and "must be the one answer among the options" in report


def test_checker_fails_on_an_en_uk_prompt_with_an_overlapping_meaning(world: dict[str, Path], tmp_path: Path) -> None:
    assert _refresh(world) == 0

    def add_production(deck: dict) -> None:
        entry = next(entry for entry in deck["entries"] if entry["key"] == "випробування")
        entry["cards"]["production"] = {"cardId": f"{entry['entryId']}:production", "choice": None}

    code, report = _plant(world, tmp_path, shard.DECK_FILE, add_production)
    assert code == 1 and "EN->UK production card although its English overlaps" in report


def test_checker_rederives_aspect_and_rejects_the_teacher_marker_as_authority(
    world: dict[str, Path], tmp_path: Path
) -> None:
    assert _refresh(world) == 0

    def trust_teacher(deck: dict) -> None:
        entry = next(entry for entry in deck["entries"] if entry["key"] == "писати")
        entry["aspect"].update(value="perf", markerAgrees=True)
        entry["en"] = "To write (pf.)"

    code, report = _plant(world, tmp_path, shard.DECK_FILE, trust_teacher, with_sources=True)
    assert code == 1 and "aspect {" in report and "!= sources" in report


def test_checker_fails_on_an_en_uk_card_for_a_dual_aspect_overlap(world: dict[str, Path], tmp_path: Path) -> None:
    assert _refresh(world) == 0

    def add_production(deck: dict) -> None:
        entry = next(entry for entry in deck["entries"] if entry["key"] == "женити")
        entry["cards"]["production"] = {"cardId": f"{entry['entryId']}:production", "choice": None}

    code, report = _plant(world, tmp_path, shard.DECK_FILE, add_production)
    assert code == 1 and "EN->UK production card although its English overlaps" in report


def test_checker_fails_on_a_multiword_cloze_without_the_verbatim_phrase(world: dict[str, Path], tmp_path: Path) -> None:
    assert _refresh(world) == 0

    def blank_last_word(cloze: dict) -> None:
        item = next(item for item in cloze["cloze"] if item["form"] == "зелений чай")
        item["sentence"] = "Я п'ю зелений ___ щоранку."
        item["form"] = "чай"
        for option in item["options"]:
            if option["kind"] == "answer":
                option["label"] = "чай"

    code, report = _plant(world, tmp_path, shard.CLOZE_FILE, blank_last_word)
    assert code == 1 and "multiword cloze without the whole phrase verbatim" in report


def test_checker_table_comparison_catches_a_changed_meaning(world: dict[str, Path], tmp_path: Path) -> None:
    assert _refresh(world) == 0

    def change_meaning(deck: dict) -> None:
        deck["entries"][0]["teacherEn"] = "Kitten"

    planted = tmp_path / "meaning"
    shutil.copytree(world["out"], planted)
    payload = json.loads((planted / shard.DECK_FILE).read_text(encoding="utf-8"))
    change_meaning(payload)
    (planted / shard.DECK_FILE).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    code, report = _check(planted, world)
    assert code == 1
    assert "manifest hash/size mismatch" in report and "!= table meanings" in report


def test_checker_matrix_and_residual_lists(world: dict[str, Path]) -> None:
    assert _refresh(world) == 0
    args = checker.argparse.Namespace(
        deck_dir=world["out"],
        docx=world["docx"],
        heading=HEADING,
        expect_keys=17,
        vesum_db=world["vesum"],
        sources_db=world["sources"],
    )
    report, summary = checker.run(args)
    assert report.errors == []
    assert summary["matrix"]["recognition-flashcard"] == {"single": 11, "multiword": 5}
    assert summary["matrix"]["production-flashcard"] == {"single": 8, "multiword": 4}
    assert summary["matrix"]["stress"]["multiword"] == 0
    assert summary["aspect"] == {
        "single": {"agree:dual": 1, "agree:imperf": 1, "agree:perf": 2, "vesum-only:imperf": 1},
        "multiword": {"vesum-only:perf": 1},
    }
    residuals = summary["residuals"]
    assert {uk for uk, _reason in residuals["productionOmitted"]} == {
        "Женити",
        "Оженити",
        "Випробування",
        "Кинути виклик",
    }
    assert {uk for uk, _reason in residuals["noAtlas"]} == {
        "Прочитати",
        "Чорна кава",
        "Свіжий хліб",
        "Теплий дім",
        "Женити",
        "Оженити",
        "Випробування",
        "Кинути виклик",
    }
    assert [uk for uk, _reason in residuals["aspectMarkerDisagreements"]] == ["Писати"]
    assert residuals["aspectUnknown"] == []
    assert residuals["refusedGroups"] == []


class FakeGh:
    """The `gh release` CLI in memory (no network); every other command runs for real."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, *, release_exists: bool = False, fail_upload: bool = False):
        self.assets: dict[str, bytes] | None = {} if release_exists else None
        self.fail_upload = fail_upload
        self.calls: list[str] = []
        self.titles: list[str] = []
        self._run = subprocess.run
        monkeypatch.setattr(subprocess, "run", self.run)

    def run(self, command, *args, **kwargs):
        if command[:2] != ["gh", "release"]:
            return self._run(command, *args, **kwargs)
        verb = command[2]
        assert command[3] == teacher_deck.RELEASE_TAG
        self.calls.append(verb + (" --json" if "--json" in command else ""))
        missing = self.assets is None
        if verb == "view" and "--json" not in command:
            return subprocess.CompletedProcess(command, 1 if missing else 0)
        if verb == "create":
            self.titles.append(command[command.index("--title") + 1])
            self.assets = {}
            return subprocess.CompletedProcess(command, 0)
        if missing or (verb == "upload" and self.fail_upload):
            raise subprocess.CalledProcessError(1, command)
        if verb == "view":
            names = [{"name": name} for name in self.assets]
            return subprocess.CompletedProcess(command, 0, stdout=json.dumps({"assets": names}))
        if verb == "upload":
            path = Path(command[4])
            self.assets[path.name] = path.read_bytes()
            return subprocess.CompletedProcess(command, 0)
        if verb == "download":
            return subprocess.CompletedProcess(command, 0, stdout=self.assets[command[command.index("-p") + 1]])
        raise AssertionError(command)


def test_first_publish_creates_the_release_then_uploads_then_pins_the_pointer(
    world: dict[str, Path], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    fake = FakeGh(monkeypatch)
    assert _refresh(world, "--publish") == 0
    assert "publish: uploaded lexicon-teacher-deck-teacher-v1-" in capsys.readouterr().out
    assert fake.titles == [teacher_deck.RELEASE_TITLE]
    assert fake.calls.index("create") < fake.calls.index("view --json") < fake.calls.index("upload")
    pointer = json.loads(world["pointer"].read_text(encoding="utf-8"))
    gz_bytes = fake.assets[teacher_deck.asset_name(pointer["deck_version"])]
    assert hashlib.sha256(gz_bytes).hexdigest() == pointer["gz_sha256"]
    unpacked = teacher_deck.unpack(gz_bytes, pointer)
    assert set(unpacked) == set(teacher_deck.PACKAGE_FILES)
    for record in pointer["files"]:
        assert hashlib.sha256(unpacked[record["path"]]).hexdigest() == record["sha256"]
    assert {r["path"] for r in pointer["files"] if r["published"]} == {shard.DECK_FILE, shard.CLOZE_FILE}

    # A fresh machine has no local set: the previous deck comes from the published asset.
    shutil.rmtree(world["out"])
    assert _refresh(world, "--publish", "--skip-ingest") == 0
    output = capsys.readouterr().out
    assert f"previous deck: published asset {pointer['deck_version']}" in output
    assert "already published (verified identical)" in output
    assert fake.calls.count("upload") == 1 and fake.calls.count("create") == 1
    assert json.loads(world["pointer"].read_text(encoding="utf-8")) == pointer


def _committed(world: dict[str, Path]) -> dict[str, bytes | None]:
    paths = [world["table"], world["frozen"], world["pointer"], *sorted(world["out"].iterdir())]
    return {path.name: path.read_bytes() if path.exists() else None for path in paths}


def test_a_failed_publish_changes_nothing_committed_facing(
    world: dict[str, Path], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _refresh(world) == 0
    before = _committed(world)
    _write_docx(world["docx"], [*TABLE, ("Лампа", "Lamp")])
    FakeGh(monkeypatch, release_exists=True, fail_upload=True)
    assert _refresh(world, "--publish", "--skip-ingest") == 2
    assert "cannot read inputs or reach the release" in capsys.readouterr().err
    assert _committed(world) == before and before["pointer.json"] is None
    leftovers = [path.name for path in world["out"].parent.iterdir() if path.name.startswith(".")]
    assert leftovers == []


def test_replace_published_set_restores_the_old_set_when_the_swap_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "deck"
    teacher_deck.replace_published_set({"a.json": b"old"}, out)
    real_rename = Path.rename

    def rename(self: Path, target: Path) -> Path:
        if self.name == ".deck.next":
            raise OSError("disk full")
        return real_rename(self, target)

    monkeypatch.setattr(Path, "rename", rename)
    with pytest.raises(OSError, match="disk full"):
        teacher_deck.replace_published_set({"a.json": b"new"}, out)
    assert (out / "a.json").read_bytes() == b"old"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["deck"]

    # An interrupted run that left only `.previous` behind is recovered first.
    monkeypatch.setattr(Path, "rename", real_rename)
    out.rename(tmp_path / ".deck.previous")
    assert teacher_deck.replace_published_set({"a.json": b"old"}, out) is False
    assert (out / "a.json").read_bytes() == b"old" and not (tmp_path / ".deck.previous").exists()


def test_commit_outputs_leaves_committed_files_untouched_when_the_swap_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "frozen.json"
    target.write_bytes(b"committed")

    def fail(*_args: object) -> bool:
        raise OSError("swap failed")

    monkeypatch.setattr(teacher_deck, "replace_published_set", fail)
    with pytest.raises(OSError):
        teacher_deck.commit_outputs({"a": b"x"}, tmp_path / "deck", {target: b"new"})
    assert target.read_bytes() == b"committed"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["frozen.json"]


# ----------------------------------------------------------------------------- reviewed lesson sentences


@pytest.mark.parametrize(
    ("sentence", "rule"),
    [
        ("Україна → держава в Європі.", "outline-arrow"),
        ("Я люблю каву/чай щоранку.", "slash-alternative"),
        ("Він купив (11) нових книжок.", "parenthetical-number-or-gloss"),
        ("У році (365) триста днів.", "parenthetical-number-or-gloss"),
        ("Вона (ходити) до школи щодня.", "parenthetical-number-or-gloss"),
        ("Пацієнт скаржиться на хронічну втому (хронічна втома).", "parenthetical-number-or-gloss"),
        ("Не маючи досвіду управлінця (обставина, дієприслів.", "parenthetical-number-or-gloss"),
        ("Петро Дорошенко народився в Чигирині (нині Черкаська область).", None),
        ("Він помер у тюремній лікарні [7].", "citation-marker"),
        ("Версія СБУ: це була диверсія.", "section-label"),
        ("Визначте рід іменників у реченні.", "worksheet-task"),
        ("2. Поясніть значення цих слів.", "worksheet-task"),
        ("Вулиця названа на честь ім.", "truncated-abbreviation"),
        ("Вживаються з: назвами істот чол.", "section-label"),
        ("Вживаються з назвами істот чол.", "truncated-abbreviation"),
        ("Мій брат живе у Львові.", None),
        ("Він сказав, що прийде (на жаль, пізно).", None),
        ("Ми бачили 2 фільми вчора.", None),
        ("Визначений день настав нарешті.", None),
    ],
)
def test_fragment_rules_match_in_generator_and_checker(sentence: str, rule: str | None) -> None:
    assert shard.lesson_fragment_reason(sentence) == rule
    assert (checker.fragment_shape(sentence) is None) is (rule is None)


def test_sentence_hash_is_nfc_and_whitespace_insensitive() -> None:
    import unicodedata

    text = "Кіт  спить\tна столі."
    nfd = unicodedata.normalize("NFD", "Їжак їсть яблуко.")
    assert shard.sentence_sha256(text) == shard.sentence_sha256("Кіт спить на столі.")
    assert shard.sentence_sha256(nfd) == shard.sentence_sha256("Їжак їсть яблуко.")
    assert checker.sentence_digest(text) == shard.sentence_sha256(text)
    assert checker.sentence_digest(nfd) == shard.sentence_sha256(nfd)


EXTRA_LESSON = (
    "22.09.2025",
    [
        "Визначте, де спить кіт.",
        "Кіт (11) спить на дивані.",
        "Наш кіт спить на дивані.",
        "Кіт лежить біля вікна.",
        "Мій кіт любить молоко.",
    ],
)


def test_withheld_and_fragment_sentences_are_never_selected_and_a_replacement_is(
    world: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    _write_docx(world["docx"], TABLE, [*LESSONS, EXTRA_LESSON])
    _write_ledger(
        world["withheld"],
        {"Наш кіт спить на дивані.": "ERR", "Кіт спить на столі.": "FRAG"},
        kept=("Кіт лежить біля вікна.",),
    )
    assert _refresh(world) == 0
    output = capsys.readouterr().out
    assert "fragment rule parenthetical-number-or-gloss 1, worksheet-task 1" in output
    assert "withheld by review ERR 1, FRAG 1 (ledger: 2 withheld, 1 kept)" in output
    cloze = json.loads((world["out"] / shard.CLOZE_FILE).read_text(encoding="utf-8"))
    served = {item["sentence"].replace(shard.BLANK, item["form"], 1): item for item in cloze["cloze"]}
    cat = entries_by_key(world)["кіт"]
    cat_sentences = [s for s, item in served.items() if item["entryId"] == cat["entryId"]]
    # The withheld newest sentence is skipped before selection: the third slot goes to the
    # next candidate (Олена …), which the 3-sentence cap excluded before.
    assert cat_sentences == ["Кіт лежить біля вікна.", "Мій кіт любить молоко.", "Олена купила кота 12 травня."]
    assert "Кіт спить на столі." not in served and "Наш кіт спить на дивані." not in served
    review = json.loads((world["out"] / shard.REVIEW_FILE).read_text(encoding="utf-8"))
    # "Кіт лежить біля вікна." is already kept: only unreviewed served sentences are queued.
    assert sorted(row["sentence"] for row in review["sentences"]) == [
        "Мій кіт любить молоко.",
        "Олена купила кота 12 травня.",
        "Я п'ю зелений чай щоранку.",
    ]
    assert review["counts"]["servedLessonItems"] == 4
    code, report = _check(world["out"], world)
    assert code == 0, report


def entries_by_key(world: dict[str, Path]) -> dict[str, dict]:
    deck = json.loads((world["out"] / shard.DECK_FILE).read_text(encoding="utf-8"))
    return {entry["key"]: entry for entry in deck["entries"]}


def test_checker_fails_when_a_withheld_sentence_is_served(world: dict[str, Path]) -> None:
    assert _refresh(world) == 0
    _write_ledger(world["withheld"], {"Я п'ю зелений чай щоранку.": "ERR"})
    code, report = _check(world["out"], world)
    assert code == 1 and "serves a sentence the language review withheld (ERR)" in report


def test_checker_rejects_a_ledger_that_carries_sentence_text(world: dict[str, Path]) -> None:
    assert _refresh(world) == 0
    ledger = json.loads(world["withheld"].read_text(encoding="utf-8"))
    ledger["withheld"] = [{"sentenceSha256": "0" * 64, "code": "ERR", "reviewer": "x", "reviewedAt": "d", "text": "…"}]
    world["withheld"].write_text(json.dumps(ledger), encoding="utf-8")
    code, report = _check(world["out"], world)
    assert code == 1 and "malformed withheld record" in report
    with pytest.raises(shard.TeacherDeckBuildError, match="malformed withheld record"):
        shard.read_sentence_reviews(world["withheld"])


def test_checker_fails_on_served_worksheet_debris(world: dict[str, Path], tmp_path: Path) -> None:
    assert _refresh(world) == 0

    def outline(cloze: dict) -> None:
        item = next(item for item in cloze["cloze"] if item["source"] == "teacher-lesson")
        item["sentence"] = item["sentence"].rstrip(".") + " → далі."

    code, report = _plant(world, tmp_path, shard.CLOZE_FILE, outline)
    assert code == 1 and "worksheet debris (outline arrow)" in report


def test_checker_rederives_the_atlas_sense_rule(world: dict[str, Path], tmp_path: Path) -> None:
    assert _refresh(world) == 0

    def other_sense(deck: dict) -> None:
        entry = next(entry for entry in deck["entries"] if entry["key"] == "собака")
        assert (entry["atlas"]["senseRule"], entry["atlas"]["senseIndex"]) == ("unique-match", 0)
        entry["atlas"]["senseIndex"] = 1

    code, report = _plant(world, tmp_path, shard.DECK_FILE, other_sense, with_sources=True)
    assert code == 1 and "Atlas sense unique-match/1 != mechanical rule unique-match/0" in report


def test_checker_rederives_identity_conflicts(world: dict[str, Path], tmp_path: Path) -> None:
    assert _refresh(world) == 0

    def invent_conflict(deck: dict) -> None:
        next(entry for entry in deck["entries"] if entry["key"] == "кіт")["atlas"]["identityConflict"] = True

    code, report = _plant(world, tmp_path, shard.DECK_FILE, invent_conflict, with_sources=True)
    assert code == 1 and "identityConflict True differs from the Atlas/sources" in report

    # The Atlas article turns into a noun for a source-known verb: the deck (built before) misses the conflict.
    with sqlite3.connect(world["atlas"]) as conn:
        payload = json.loads(
            conn.execute("SELECT payload_json FROM article_payloads WHERE slug = 'писати'").fetchone()[0]
        )
        payload["pos"] = "noun"
        conn.execute("UPDATE article_payloads SET payload_json = ? WHERE slug = 'писати'", (json.dumps(payload),))
    code, report = _check(world["out"], world)
    assert code == 1 and "identity conflicts differ from the Atlas/sources" in report


def test_checker_enforces_the_same_slot_distractor_rule(world: dict[str, Path], tmp_path: Path) -> None:
    assert _refresh(world) == 0
    table_id = entries_by_key(world)["стіл"]["entryId"]

    def wrong_case(cloze: dict) -> None:
        item = next(item for item in cloze["cloze"] if item["entryId"] == table_id)
        option = next(option for option in item["options"] if option["label"] == "будинку")
        option["label"] = "будинок"  # nominative in a locative slot

    code, report = _plant(world, tmp_path, shard.CLOZE_FILE, wrong_case, with_sources=True)
    assert code == 1 and "distractor 'будинок' does not fill the blank's grammatical slot" in report


def _review_queue(tmp_path: Path) -> tuple[Path, Path]:
    sentences = ["Кіт спить на столі.", "Кіт спить на столі.", "Я п'ю зелений чай щоранку.", "Мій кіт спить."]
    forms = ["кіт", "столі", "чай", "кіт"]
    items = [
        {"clozeId": f"c{i}", "sentence": text.replace(form, shard.BLANK, 1), "form": form}
        for i, (text, form) in enumerate(zip(sentences, forms, strict=True))
    ]
    queue = {"sentences": [{"clozeId": f"c{i}", "sentence": text} for i, text in enumerate(sentences)]}
    (tmp_path / "queue.json").write_text(json.dumps(queue), encoding="utf-8")
    (tmp_path / "cloze.json").write_text(json.dumps({"cloze": items}), encoding="utf-8")
    return tmp_path / "queue.json", tmp_path / "cloze.json"


def test_record_review_folds_results_into_a_text_free_ledger(tmp_path: Path) -> None:
    queue, cloze = _review_queue(tmp_path)
    (tmp_path / "part1.tsv").write_text("c0\tFRAG\nc1\tERR\n", encoding="utf-8")
    ledger = tmp_path / "ledger.json"
    common = ["--queue", str(queue), "--cloze", str(cloze), "--ledger", str(ledger), "--reviewed-at", "2026-09-27"]
    assert teacher_deck.main(["record-review", *common, "--results", str(tmp_path / "part1.tsv"),
                              "--positions", "0-2", "--reviewer", "r1"]) == 0  # fmt: skip
    payload = json.loads(ledger.read_text(encoding="utf-8"))
    assert "Кіт" not in ledger.read_text(encoding="utf-8")
    # One sentence reviewed through two cloze ids keeps the gravest code; c2 was reviewed and kept.
    assert [(row["sentenceSha256"], row["code"]) for row in payload["withheld"]] == [
        (shard.sentence_sha256("Кіт спить на столі."), "ERR")
    ]
    assert [row["sentenceSha256"] for row in payload["kept"]] == [shard.sentence_sha256("Я п'ю зелений чай щоранку.")]
    reviews = shard.read_sentence_reviews(ledger)
    assert not reviews.reviewed(shard.sentence_sha256("Мій кіт спить."))  # position 3 was not reviewed

    (tmp_path / "part2.tsv").write_text("c1\tERR\n", encoding="utf-8")
    assert teacher_deck.main(["record-review", *common, "--results", str(tmp_path / "part2.tsv"),
                              "--positions", "3-3", "--reviewer", "r2"]) == 1  # fmt: skip
    assert teacher_deck.main(["record-review", *common, "--results", str(tmp_path / "part2.tsv"),
                              "--positions", "0-9", "--reviewer", "r2"]) == 1  # fmt: skip
