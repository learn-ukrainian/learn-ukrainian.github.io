from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest

from scripts.audit import _judge_eval_lib as judge
from scripts.storage import topology


def _sources_db(path: Path, label: str) -> Path:
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE style_guide (word TEXT, section TEXT, page INTEGER, text TEXT, word_lower TEXT);
        CREATE TABLE grinchenko (word TEXT);
        CREATE TABLE esum_etymology (lemma TEXT);
        CREATE TABLE textbooks (id INTEGER PRIMARY KEY, title TEXT, text TEXT, source_file TEXT);
        CREATE VIRTUAL TABLE textbooks_fts USING fts5(title, text);
        CREATE TABLE ua_gec_errors (id INTEGER PRIMARY KEY, error TEXT, correct TEXT, error_type TEXT, doc_id TEXT);
        CREATE VIRTUAL TABLE ua_gec_errors_fts USING fts5(error);
        """
    )
    word = f"сентинель{label}"
    conn.execute("INSERT INTO style_guide VALUES (?, 'fixture', 1, ?, ?)", (word, label, word))
    conn.execute("INSERT INTO grinchenko VALUES (?)", (word,))
    conn.execute("INSERT INTO esum_etymology VALUES (?)", (word,))
    title = "Antonenko fixture p. 7"
    prose = f"{word} правильно русизм"
    conn.execute("INSERT INTO textbooks(title, text, source_file) VALUES (?, ?, ?)",
                 (title, prose, judge.ANTONENKO_SOURCE))
    conn.execute("INSERT INTO textbooks_fts(title, text) VALUES (?, ?)", (title, prose))
    conn.execute("INSERT INTO ua_gec_errors(error, correct, error_type, doc_id) VALUES (?, ?, ?, ?)",
                 (word, "fixture correction", "F/Calque", "synthetic"))
    conn.execute("INSERT INTO ua_gec_errors_fts(error) VALUES (?)", (word,))
    conn.commit()
    conn.close()
    return path


def _vesum_db(path: Path, known: str) -> Path:
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE forms (word_form TEXT)")
    conn.execute("INSERT INTO forms VALUES (?)", (known,))
    conn.commit()
    conn.close()
    return path


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def stores(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    return (
        _sources_db(tmp_path / "sources-a.db", "альфа"),
        _sources_db(tmp_path / "sources-b.db", "браво"),
        _vesum_db(tmp_path / "vesum-a.db", "сентинельальфа"),
        _vesum_db(tmp_path / "vesum-b.db", "сентинельбраво"),
    )


def test_five_readers_use_current_bindings_and_explicit_precedence(
    stores: tuple[Path, Path, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    source_a, source_b, vesum_a, vesum_b = stores
    monkeypatch.setenv("LU_SOURCES_DB", str(source_a))
    monkeypatch.setenv("LU_VESUM_DB", str(vesum_a))
    text = "сентинельальфа"

    connections: list[sqlite3.Connection] = []
    open_readonly = judge._open_readonly

    def tracked_open(path: str | Path) -> sqlite3.Connection:
        conn = open_readonly(path)
        assert conn.execute("PRAGMA query_only").fetchone()[0] == 1
        connections.append(conn)
        return conn

    monkeypatch.setattr(judge, "_open_readonly", tracked_open)
    before = {path: _digest(path) for path in stores}

    assert judge.retrieve_antonenko(text)[0]["headword"] == "сентинельальфа"
    monkeypatch.setenv("LU_SOURCES_DB", str(source_b))
    assert judge.retrieve_antonenko("сентинельбраво")[0]["headword"] == "сентинельбраво"
    assert judge.retrieve_antonenko("сентинельальфа", db_path=source_a)[0]["headword"] == "сентинельальфа"
    assert judge._heritage_check(text, db_path=source_a)[0]["token"] == "сентинельальфа"
    assert judge._antonenko_fulltext_search(text, db_path=source_a)[0]["page"] == 7
    assert judge.retrieve_ua_gec(text, db_path=source_a)[0]["error"] == "сентинельальфа"
    monkeypatch.setenv("LU_SOURCES_DB", str(source_a))
    assert judge._heritage_check(text)[0]["token"] == "сентинельальфа"
    assert judge._antonenko_fulltext_search(text)[0]["page"] == 7
    assert judge.retrieve_ua_gec(text)[0]["error"] == "сентинельальфа"
    assert judge._vesum_unknown("сентинельальфа") == []

    monkeypatch.setenv("LU_VESUM_DB", str(vesum_b))
    assert judge._vesum_unknown("сентинельальфа") == ["сентинельальфа"]
    assert judge._vesum_unknown("сентинельальфа", db_path=vesum_a) == []

    assert connections
    for conn in connections:
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            conn.execute("SELECT 1")
    assert {path: _digest(path) for path in stores} == before


def test_aggregate_executes_six_channels_and_prompt_assertions_on_fixtures(
    stores: tuple[Path, Path, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    source_a, _, vesum_a, _ = stores
    monkeypatch.setenv("LU_SOURCES_DB", str(source_a))
    monkeypatch.setenv("LU_VESUM_DB", str(vesum_a))
    monkeypatch.setattr(judge, "_russian_shadow_check", lambda _text: {"available": True, "triggered_tokens": []})
    monkeypatch.setattr(judge, "_ua_gec_calque_search", lambda _text: [{"error": "fixture", "correct": "fixture", "tag": "F/Calque", "overlap": 1}])

    evidence = judge.retrieve_evidence("сентинельальфа")
    assert set(evidence) == {
        "antonenko", "antonenko_fulltext", "heritage_attested", "russian_shadow",
        "vesum_unknown_tokens", "ua_gec_calques",
    }
    prompt = judge.build_judge_prompt_h2("Доброго дня!", evidence)
    for heading in (
        "Antonenko-Davydovych — keyed headword entries",
        "Antonenko-Davydovych — full-book prose hits",
        "Heritage attestation",
        "Russian-shadow morphology hits",
        "VESUM-unknown Cyrillic tokens",
        "UA-GEC corpus",
    ):
        assert heading in prompt
    assert "Default verdict: CLEAN" in prompt
    assert "Доброго дня!" in prompt
    assert "stylistic preference of the annotator" in prompt


@pytest.mark.parametrize("kind", ["empty", "relative", "uri", "missing", "network", "unknown"])
def test_refusals_are_path_free_and_never_fall_back_to_valid_environment(
    stores: tuple[Path, Path, Path, Path], monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    source_a, _, _, _ = stores
    monkeypatch.setenv("LU_SOURCES_DB", str(source_a))
    if kind == "empty":
        monkeypatch.setenv("LU_SOURCES_DB", " ")
        explicit = None
        path_hint = None
    elif kind == "relative":
        explicit = Path("relative-fixture.db")
        path_hint = str(explicit)
    elif kind == "uri":
        explicit = Path(f"file:{source_a}")
        path_hint = str(explicit)
    elif kind == "missing":
        explicit = source_a.with_name("missing-fixture.db")
        path_hint = str(explicit)
    else:
        explicit = source_a
        path_hint = str(explicit)
        if kind == "network":
            monkeypatch.setattr(topology, "_path_looks_like_network", lambda _path: True)
        else:
            monkeypatch.setattr(topology, "_fs_type_for_path", lambda _path: None)

    with pytest.raises(RuntimeError, match="sources read store refused") as exc:
        judge.retrieve_antonenko("сентинельальфа", db_path=explicit)
    if path_hint:
        assert path_hint not in str(exc.value)


def test_invalid_environment_refuses_aggregate_instead_of_returning_clean_evidence(
    stores: tuple[Path, Path, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    source_a, _, vesum_a, _ = stores
    monkeypatch.setenv("LU_SOURCES_DB", str(source_a))
    monkeypatch.setenv("LU_VESUM_DB", str(vesum_a))
    evidence = judge.retrieve_evidence("сентинельальфа")
    assert evidence["antonenko"]

    monkeypatch.setenv("LU_SOURCES_DB", "relative-fixture.db")
    with pytest.raises(RuntimeError, match="relative_override") as exc:
        judge.retrieve_evidence("сентинельальфа")
    assert "relative-fixture.db" not in str(exc.value)
