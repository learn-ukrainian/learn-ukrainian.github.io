"""Tests for deterministic grow needs_review triage (#5230 arc)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from scripts.lexicon import triage_needs_review as triage
from scripts.wiki import sources_db as sdb


def _held(
    lemma: str,
    *,
    pos: str | None = "noun",
    reason: str = "missing dictionary definition",
) -> triage.HeldEntry:
    return triage.HeldEntry(lemma=lemma, pos=pos, held_reason=reason, raw={})


def test_empty_input_returns_empty_records() -> None:
    records = triage.triage_held_entries(
        [],
        lookups={key: (lambda words: {w: [] for w in words}) for key in triage.SOURCE_HIT_KEYS},
        vesum_fn=lambda words: {w: [] for w in words},
    )
    assert records == []
    summary = triage.build_summary_markdown([])
    assert "Total held: **0**" in summary
    assert f"`{triage.MACHINE_PROMOTE}`: 0" in summary


def test_gloss_priority_order_sum11_over_dmklinger() -> None:
    lookups = {
        "sum11": lambda words: {
            "хата": [{"definition": "СУМ gloss", "word": "хата"}],
        },
        "dmklinger": lambda words: {
            "хата": [{"translations": json.dumps(["house"]), "word": "хата"}],
        },
        "grinchenko": lambda words: {"хата": [{"definition": "Грінченко"}]},
        "slovnyk_me": lambda words: {"хата": []},
        "balla": lambda words: {"хата": []},
        "esum": lambda words: {"хата": []},
        "puls_cefr": lambda words: {"хата": [{"level": "A1"}]},
    }
    records = triage.triage_held_entries(
        [_held("хата")],
        lookups=lookups,
        vesum_fn=lambda words: {w: [{"lemma": w, "pos": "noun", "tags": ""}] for w in words},
    )
    assert len(records) == 1
    rec = records[0]
    assert rec["best_gloss"] == {"text": "СУМ gloss", "source": "sum11"}
    assert rec["machine_action"] == triage.MACHINE_PROMOTE
    assert rec["cefr"] == "A1"
    assert rec["vesum_valid"] is True
    assert rec["sources_hit"]["sum11"] == 1
    assert rec["sources_hit"]["dmklinger"] == 1


def test_gloss_priority_falls_through_to_dmklinger() -> None:
    lookups = {
        "sum11": lambda words: {w: [] for w in words},
        "dmklinger": lambda words: {
            w: [{"translations": '["work", "job"]', "word": w}] for w in words
        },
        "grinchenko": lambda words: {w: [] for w in words},
        "slovnyk_me": lambda words: {w: [] for w in words},
        "balla": lambda words: {w: [] for w in words},
        "esum": lambda words: {w: [] for w in words},
        "puls_cefr": lambda words: {w: [] for w in words},
    }
    records = triage.triage_held_entries(
        [_held("робота")],
        lookups=lookups,
        vesum_fn=lambda words: {w: [] for w in words},
    )
    assert records[0]["best_gloss"] == {"text": "work", "source": "dmklinger"}
    assert records[0]["machine_action"] == triage.MACHINE_PROMOTE
    assert records[0]["vesum_valid"] is False


def test_truly_missing_when_no_gloss_sources() -> None:
    empty = {key: (lambda words: {w: [] for w in words}) for key in triage.SOURCE_HIT_KEYS}
    # esum alone must not promote — etymology is not a gloss source.
    empty["esum"] = lambda words: {
        w: [{"lemma": w, "etymology_text": "from X"}] for w in words
    }
    records = triage.triage_held_entries(
        [_held("а-а-а")],
        lookups=empty,
        vesum_fn=lambda words: {w: [{"lemma": w}] for w in words},
    )
    assert records[0]["best_gloss"] is None
    assert records[0]["machine_action"] == triage.MACHINE_MISSING
    assert records[0]["sources_hit"]["esum"] == 1
    assert records[0]["vesum_valid"] is True


def test_heritage_carve_out_regardless_of_hits() -> None:
    lookups = {
        "sum11": lambda words: {
            w: [{"definition": "still has a gloss", "word": w}] for w in words
        },
        "dmklinger": lambda words: {w: [] for w in words},
        "grinchenko": lambda words: {w: [] for w in words},
        "slovnyk_me": lambda words: {w: [] for w in words},
        "balla": lambda words: {w: [] for w in words},
        "esum": lambda words: {w: [] for w in words},
        "puls_cefr": lambda words: {w: [] for w in words},
    }
    records = triage.triage_held_entries(
        [
            _held(
                "верф",
                reason="heritage_status flags russianism; heritage_status flags calque_warning",
            )
        ],
        lookups=lookups,
        vesum_fn=lambda words: {w: [] for w in words},
    )
    assert records[0]["best_gloss"] is not None
    assert records[0]["machine_action"] == triage.MACHINE_HERITAGE


def test_load_held_entries_from_grow_payload(tmp_path: Path) -> None:
    path = tmp_path / "grow_candidates.json"
    path.write_text(
        json.dumps(
            {
                "needs_review": [
                    {
                        "entry": {"lemma": "те́ст", "pos": "noun"},
                        "reason": "missing dictionary definition",
                    },
                    {
                        "entry": {"lemma": "верф", "pos": "noun"},
                        "reason": "heritage_status flags curated_calque",
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    held = triage.load_held_entries(path)
    assert [h.lemma for h in held] == ["тест", "верф"]  # stress stripped
    assert held[1].held_reason.startswith("heritage_status")


def test_dmklinger_batch_strips_u0301(tmp_path: Path) -> None:
    """Plain-string equality misses stressed headwords; batch must strip U+0301."""
    db = tmp_path / "sources.db"
    conn = sqlite3.connect(db)
    conn.execute(
        """
        CREATE TABLE dmklinger_uk_en (
            id INTEGER PRIMARY KEY,
            word TEXT NOT NULL,
            pos TEXT,
            translations TEXT,
            text TEXT,
            source TEXT
        )
        """
    )
    # Combining acute after о: роб + о + U+0301 + та
    stressed = "роб" + "о\u0301" + "та"
    conn.execute(
        "INSERT INTO dmklinger_uk_en(word, pos, translations, text, source) VALUES (?,?,?,?,?)",
        (stressed, "n", json.dumps(["work"]), f"{stressed}: work", "dmklinger"),
    )
    conn.commit()
    conn.close()

    plain = sdb.search_dmklinger_uk_en_batch(["робота"], db_path=db)
    stressed_query = sdb.search_dmklinger_uk_en_batch([stressed], db_path=db)
    # Control: exact equality batch on sum11-style would miss; dmklinger batch must hit.
    assert len(plain["робота"]) == 1
    assert "work" in plain["робота"][0]["translations"]
    assert len(stressed_query[stressed]) == 1

    # Sanity: replace-based match is required — naive equality fails.
    conn = sqlite3.connect(db)
    naive = conn.execute(
        "SELECT word FROM dmklinger_uk_en WHERE word = ? COLLATE NOCASE",
        ("робота",),
    ).fetchall()
    conn.close()
    assert naive == []


def test_batch_dict_siblings_with_fixture_db(tmp_path: Path) -> None:
    db = tmp_path / "sources.db"
    conn = sqlite3.connect(db)
    conn.executescript(
        """
        CREATE TABLE sum11 (
            id INTEGER PRIMARY KEY, word TEXT, definition TEXT,
            text TEXT, source TEXT
        );
        CREATE TABLE grinchenko (
            id INTEGER PRIMARY KEY, word TEXT, definition TEXT, source TEXT
        );
        CREATE TABLE balla_en_uk (
            id INTEGER PRIMARY KEY, word TEXT, definition TEXT,
            text TEXT, source TEXT
        );
        CREATE TABLE puls_cefr (
            id INTEGER PRIMARY KEY, word TEXT, guideword TEXT, level TEXT,
            pos TEXT, type TEXT, text TEXT, source TEXT
        );
        CREATE TABLE esum_etymology_meta (
            id INTEGER PRIMARY KEY, lemma TEXT, vol INTEGER, page INTEGER,
            entry_hash TEXT, etymology_text TEXT, cognates TEXT, source TEXT
        );
        CREATE TABLE slovnyk_me_entries (
            id INTEGER PRIMARY KEY,
            dictionary_slug TEXT,
            word TEXT,
            normalized_word TEXT,
            definition TEXT,
            text TEXT,
            is_modern INTEGER DEFAULT 1,
            is_dialect INTEGER DEFAULT 0,
            is_russianism INTEGER DEFAULT 0,
            sovietization_risk INTEGER DEFAULT 0
        );
        """
    )
    conn.execute(
        "INSERT INTO sum11(word, definition, text, source) VALUES (?,?,?,?)",
        ("слово", "одиниця мови", "слово: одиниця", "СУМ-11"),
    )
    conn.execute(
        "INSERT INTO grinchenko(word, definition, source) VALUES (?,?,?)",
        ("слово", "мова", "Грінченко"),
    )
    conn.execute(
        "INSERT INTO balla_en_uk(word, definition, text, source) VALUES (?,?,?,?)",
        ("word", "слово", "word: слово", "Балла"),
    )
    conn.execute(
        "INSERT INTO puls_cefr(word, guideword, level, pos, type, text, source) "
        "VALUES (?,?,?,?,?,?,?)",
        ("слово", "", "A1", "іменник", "значення", "слово (A1)", "PULS"),
    )
    conn.execute(
        "INSERT INTO esum_etymology_meta"
        "(lemma, vol, page, entry_hash, etymology_text, cognates, source) "
        "VALUES (?,?,?,?,?,?,?)",
        ("слово", 1, 1, "h", "etym", "[]", "ЕСУМ"),
    )
    conn.execute(
        "INSERT INTO slovnyk_me_entries"
        "(dictionary_slug, word, normalized_word, definition, text) "
        "VALUES (?,?,?,?,?)",
        ("ukreng", "слово", "слово", "word (en)", "слово — word"),
    )
    conn.commit()
    conn.close()

    assert sdb.search_definitions_batch(["слово"], db_path=db)["слово"][0]["definition"]
    assert sdb.search_grinchenko_batch(["слово"], db_path=db)["слово"]
    assert sdb.search_balla_en_uk_batch(["word"], db_path=db)["word"]
    assert sdb.query_cefr_levels(["слово"], db_path=db)["слово"][0]["level"] == "A1"
    assert sdb.search_esum_batch(["слово"], db_path=db)["слово"]
    assert sdb.search_slovnyk_me_entries_batch(["слово"], db_path=db)["слово"]
    # Missing lemmas stay empty (no KeyError).
    assert sdb.search_definitions_batch(["відсутнє"], db_path=db)["відсутнє"] == []


def test_run_triage_write_and_probe(tmp_path: Path) -> None:
    candidates = tmp_path / "grow_candidates.json"
    candidates.write_text(
        json.dumps(
            {
                "needs_review": [
                    {
                        "entry": {"lemma": "alpha", "pos": "noun"},
                        "reason": "missing dictionary definition",
                    },
                    {
                        "entry": {"lemma": "beta", "pos": "verb"},
                        "reason": "heritage_status flags curated_calque",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "needs-review-triage.json"
    summary = tmp_path / "needs-review-triage-summary.md"

    lookups = {
        "sum11": lambda words: {
            w: ([{"definition": "gloss"}] if w == "alpha" else []) for w in words
        },
        "dmklinger": lambda words: {w: [] for w in words},
        "grinchenko": lambda words: {w: [] for w in words},
        "slovnyk_me": lambda words: {w: [] for w in words},
        "balla": lambda words: {w: [] for w in words},
        "esum": lambda words: {w: [] for w in words},
        "puls_cefr": lambda words: {w: [] for w in words},
    }

    probe = triage.run_triage(
        candidates_path=candidates,
        db_path=tmp_path / "missing.db",
        out_path=out,
        summary_path=summary,
        write=False,
        lookups=lookups,
        vesum_fn=lambda words: {w: [] for w in words},
    )
    assert probe.written is False
    assert not out.exists()
    assert probe.counts_by_action[triage.MACHINE_PROMOTE] == 1
    assert probe.counts_by_action[triage.MACHINE_HERITAGE] == 1

    written = triage.run_triage(
        candidates_path=candidates,
        db_path=tmp_path / "missing.db",
        out_path=out,
        summary_path=summary,
        write=True,
        lookups=lookups,
        vesum_fn=lambda words: {w: [] for w in words},
    )
    assert written.written is True
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["counts"]["total"] == 2
    assert summary.exists()
    assert "machine_action" in summary.read_text(encoding="utf-8")


def test_cli_refuses_without_write_or_probe() -> None:
    with pytest.raises(SystemExit) as exc:
        triage.main([])
    assert exc.value.code == 2


def test_cli_help_is_clean() -> None:
    with pytest.raises(SystemExit) as exc:
        triage.main(["--help"])
    assert exc.value.code == 0


def test_cli_probe_with_injected_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    candidates = tmp_path / "grow_candidates.json"
    candidates.write_text(json.dumps({"needs_review": []}), encoding="utf-8")

    # Force empty probe path — no real DB required.
    monkeypatch.setattr(
        triage,
        "run_triage",
        lambda **kwargs: triage.TriageResult(
            entries=[],
            summary_md=triage.build_summary_markdown([]),
            counts_by_action={},
            candidates_found=True,
            written=False,
            dry_run=True,
        ),
    )
    code = triage.main(["--probe", "--candidates", str(candidates)])
    assert code == 0
    out = capsys.readouterr().out
    assert "probe (read-only)" in out
    assert "Held triaged: 0" in out
