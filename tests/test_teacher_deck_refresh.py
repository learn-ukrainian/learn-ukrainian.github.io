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
        {"entryId": "a", "en": "To read (impf)"},
        {"entryId": "b", "en": "To read (perf)"},
        {"entryId": "c", "en": "Cat"},
    ]
    assert shard.overlap_graph(entries) == {"a": ["b"], "b": ["a"], "c": []}


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
]
LESSONS = [
    ("01.09.2025", ["The cat is sleeping on the table.", "Кіт спить на столі."]),
    ("08.09.2025", ["I drink green tea every morning.", "Я п'ю зелений чай щоранку."]),
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
]
ATLAS = {
    "кіт": ("noun", ["cat"], None),
    "собака": ("noun", ["dog", "hound (hunting dog)"], "соба́ка"),
    "будинок": ("noun", ["house"], "буди́нок"),
    "стіл": ("noun", ["table", "desk"], None),
    "вікно": ("noun", ["window"], "вікно́"),
    "читати": ("verb", ["to read"], "чита́ти"),
    "зелений чай": ("phrase", ["green tea"], None),
}


def _p(text: str, style: str = "") -> str:
    prop = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    return f"<w:p>{prop}<w:r><w:t>{text}</w:t></w:r></w:p>"


def _write_docx(path: Path, table: list[tuple[str, str]]) -> None:
    body = "".join(_p(date) + "".join(_p(line) for line in lines) for date, lines in LESSONS)
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
    vesum = tmp_path / "vesum.db"
    with sqlite3.connect(vesum) as conn:
        conn.execute("CREATE TABLE forms (word_form TEXT, lemma TEXT, pos TEXT, tags TEXT)")
        conn.executemany("INSERT INTO forms VALUES (?, ?, ?, ?)", VESUM_FORMS)
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
    }


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
            *extra,
        ]
    )


def _check(deck_dir: Path, world: dict[str, Path] | None = None) -> tuple[int, str]:
    args = ["--deck-dir", str(deck_dir)]
    if world:
        args += ["--docx", str(world["docx"]), "--vesum-db", str(world["vesum"]), "--sources-db", str(world["sources"])]
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
    assert "table: 12 rows, 12 distinct source keys, 11 entries, 1 merged" in first_output
    assert "teacher deck check: PASS" in first_output
    assert "[2025-09-01] Кіт спить на столі." in first_output

    deck = json.loads((world["out"] / shard.DECK_FILE).read_text(encoding="utf-8"))
    cloze = json.loads((world["out"] / shard.CLOZE_FILE).read_text(encoding="utf-8"))
    entries = {entry["key"]: entry for entry in deck["entries"]}
    assert entries["кіт"]["en"] == "Cat" and entries["кіт"]["sourceRows"] == [1, 9]
    # Aspect partners share "read": no EN->UK prompt for either.
    assert entries["читати"]["cards"]["production"] is None
    assert entries["прочитати"]["cards"]["production"] is None
    assert entries["вікно"]["cards"]["production"]["cardId"] == f"{entries['вікно']['entryId']}:production"
    by_entry = {}
    for item in cloze["cloze"]:
        by_entry.setdefault(item["entryId"], []).append(item)
    cat_items = by_entry[entries["кіт"]["entryId"]]
    assert cat_items[0]["source"] == "teacher-lesson"
    assert cat_items[0]["clozeEn"] == "The cat is sleeping on the table."
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

    before = _hashes(world)
    assert _refresh(world) == 0
    second_output = capsys.readouterr().out
    assert "no-op: artifacts unchanged" in second_output
    assert "publish: skipped (pointer NOT updated)" in second_output
    assert "inserted 0, unchanged 2" in second_output
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


def _plant(world: dict[str, Path], tmp_path: Path, name: str, mutate) -> tuple[int, str]:
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
    return _check(planted)


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
        entry = next(entry for entry in deck["entries"] if entry["key"] == "читати")
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
        deck["entries"][0]["en"] = "Kitten"

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
        expect_keys=12,
        vesum_db=world["vesum"],
        sources_db=world["sources"],
    )
    report, summary = checker.run(args)
    assert report.errors == []
    assert summary["matrix"]["recognition-flashcard"] == {"single": 7, "multiword": 4}
    assert summary["matrix"]["production-flashcard"] == {"single": 5, "multiword": 4}
    assert summary["matrix"]["stress"]["multiword"] == 0
    residuals = summary["residuals"]
    assert {uk for uk, _reason in residuals["productionOmitted"]} == {"Читати", "Прочитати"}
    assert {uk for uk, _reason in residuals["noAtlas"]} == {"Прочитати", "Чорна кава", "Свіжий хліб", "Теплий дім"}
    assert residuals["refusedGroups"] == []


class FakeRelease:
    """In-memory stand-in for the GitHub release used by --publish (no network)."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.assets: dict[str, bytes] = {}
        self.uploads = 0
        release = teacher_deck.release
        monkeypatch.setattr(release, "_release_asset_names", lambda **_kw: set(self.assets))
        monkeypatch.setattr(release, "upload_release_asset", self.upload)
        monkeypatch.setattr(release, "verify_existing_release_asset", self.verify)
        monkeypatch.setattr(release, "_download_release_asset", lambda name, **_kw: self.assets[name])

    def upload(self, path: Path, *, asset_name: str, release_tag: str, repo: str, clobber: bool) -> None:
        assert release_tag == teacher_deck.RELEASE_TAG and clobber is False
        self.assets[asset_name] = path.read_bytes()
        self.uploads += 1

    def verify(self, name: str, *, expected_gz_bytes: bytes, release_tag: str, repo: str) -> None:
        assert self.assets[name] == expected_gz_bytes


def test_publish_uploads_once_pins_the_pointer_and_carries_order_keys_from_the_asset(
    world: dict[str, Path], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    fake = FakeRelease(monkeypatch)
    assert _refresh(world, "--publish") == 0
    assert "publish: uploaded lexicon-teacher-deck-teacher-v1-" in capsys.readouterr().out
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
    assert fake.uploads == 1
    assert json.loads(world["pointer"].read_text(encoding="utf-8")) == pointer
