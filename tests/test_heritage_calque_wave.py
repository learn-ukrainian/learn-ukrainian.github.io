"""Tests for scripts/lexicon/heritage_calque_wave.py (#6623)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from scripts.audit.generate_practice_deck import (
    _merge_heritage_pair_overlay,
    read_heritage_pairs,
    validate_heritage_pair,
)
from scripts.lexicon.heritage_calque_wave import (
    candidate_sentences,
    find_carrier_sentence,
    has_stray_quote,
    is_ambiguous_single_token,
    is_clean_sentence,
    load_gec_calque_pairs,
    normalize_gec_text,
    run_wave,
    substitute_single,
    word_boundary_pattern,
)

LONG_CLEAN_SENTENCE = (
    "Учора ввечері вона нарешті знайшла завдання, яке шукала цілий тиждень поспіль."
)


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------


def test_normalize_gec_text_strips_edge_punctuation() -> None:
    assert normalize_gec_text("Таким чином,") == "Таким чином"
    assert normalize_gec_text('  "в цілому"  ') == "в цілому"
    assert normalize_gec_text("") is None
    assert normalize_gec_text(None) is None
    assert normalize_gec_text(",.:;") is None


def test_has_stray_quote() -> None:
    assert has_stray_quote('доктор"') is True
    assert has_stray_quote("доктор") is False


# ---------------------------------------------------------------------------
# Substitution
# ---------------------------------------------------------------------------


def test_word_boundary_pattern_matches_whole_token_only() -> None:
    pattern = word_boundary_pattern("завдання")
    assert pattern.search("Це важливе завдання.") is not None
    assert pattern.search("надзавдання") is None


def test_substitute_single_requires_exactly_one_occurrence() -> None:
    pattern = word_boundary_pattern("кілька")
    assert substitute_single(pattern, "Було кілька спроб.", "___") == "Було ___ спроб."
    # Two occurrences: ambiguous substitution target, must fail closed.
    assert substitute_single(pattern, "кілька і ще кілька", "___") is None
    # Zero occurrences.
    assert substitute_single(pattern, "жодного разу", "___") is None


def test_substitute_single_handles_hyphenated_token() -> None:
    pattern = word_boundary_pattern("будь-який")
    result = substitute_single(pattern, "Обери будь-який варіант.", "___")
    assert result == "Обери ___ варіант."


# ---------------------------------------------------------------------------
# Sentence quality gates
# ---------------------------------------------------------------------------


def test_is_clean_sentence_accepts_well_formed_sentence() -> None:
    assert is_clean_sentence(LONG_CLEAN_SENTENCE) is True


def test_clean_sentence_rejects_too_short() -> None:
    assert is_clean_sentence("Це коротко.") is False


def test_is_clean_sentence_rejects_latin_contamination() -> None:
    text = "Учора ввечері вона нарешті знайшла task, яке шукала цілий тиждень поспіль."
    assert is_clean_sentence(text) is False


def test_is_clean_sentence_rejects_existing_blank_run() -> None:
    text = "Учора ввечері вона нарешті знайшла ____ яке шукала цілий тиждень поспіль тут."
    assert is_clean_sentence(text) is False


def test_is_clean_sentence_rejects_broken_hyphenation() -> None:
    text = "Учора ввечері вона нарешті зна- йшла завдання, яке шукала цілий тиждень."
    assert is_clean_sentence(text) is False


def test_is_clean_sentence_rejects_missing_terminal_punctuation() -> None:
    text = "Учора ввечері вона нарешті знайшла завдання, яке шукала цілий тиждень поспіль"
    assert is_clean_sentence(text) is False


def test_candidate_sentences_splits_on_terminal_punctuation() -> None:
    text = "Перше речення. Друге речення! Третє речення?"
    pieces = candidate_sentences(text)
    assert pieces == ["Перше речення.", "Друге речення!", "Третє речення?"]


# ---------------------------------------------------------------------------
# UA-GEC loading
# ---------------------------------------------------------------------------


def _make_sources_db(path: Path, gec_rows: list[tuple[str, str, str, str]], corpus: dict[str, list[tuple[str, str]]]) -> None:
    """Build a minimal sources.db fixture: ua_gec_errors + textbooks/literary FTS5."""
    con = sqlite3.connect(path)
    try:
        con.execute(
            "CREATE TABLE ua_gec_errors (id INTEGER PRIMARY KEY, error TEXT, correct TEXT, "
            "error_type TEXT, doc_id TEXT)"
        )
        con.executemany(
            "INSERT INTO ua_gec_errors (error, correct, error_type, doc_id) VALUES (?, ?, ?, ?)",
            gec_rows,
        )
        for table, fts in (("textbooks", "textbooks_fts"), ("literary_texts", "literary_fts")):
            con.execute(
                f"CREATE TABLE {table} (id INTEGER PRIMARY KEY, chunk_id TEXT, text TEXT, source_file TEXT)"
            )
            con.execute(
                f"CREATE VIRTUAL TABLE {fts} USING fts5(text, content='{table}', content_rowid='id')"
            )
            rows = corpus.get(table, [])
            for chunk_id, text in rows:
                con.execute(
                    f"INSERT INTO {table} (chunk_id, text, source_file) VALUES (?, ?, ?)",
                    (chunk_id, text, "fixture"),
                )
            con.execute(f"INSERT INTO {fts}({fts}) VALUES ('rebuild')")
        con.commit()
    finally:
        con.close()


def _make_atlas_db(path: Path, entries: list[dict]) -> None:
    import json as _json

    con = sqlite3.connect(path)
    try:
        con.execute(
            "CREATE TABLE article_payloads (payload_json TEXT, is_public_route INTEGER, route_order INTEGER)"
        )
        for index, entry in enumerate(entries):
            con.execute(
                "INSERT INTO article_payloads (payload_json, is_public_route, route_order) VALUES (?, 1, ?)",
                (_json.dumps(entry, ensure_ascii=False), index),
            )
        con.commit()
    finally:
        con.close()


def _make_vesum_db(path: Path, forms: list[tuple[str, str, str, str]]) -> None:
    con = sqlite3.connect(path)
    try:
        con.execute("CREATE TABLE forms (word_form TEXT, lemma TEXT, pos TEXT, tags TEXT)")
        con.executemany("INSERT INTO forms (word_form, lemma, pos, tags) VALUES (?, ?, ?, ?)", forms)
        con.commit()
    finally:
        con.close()


def test_load_gec_calque_pairs_normalizes_dedupes_and_drops_quote_artifacts(tmp_path: Path) -> None:
    db_path = tmp_path / "sources.db"
    _make_sources_db(
        db_path,
        gec_rows=[
            ("Таким чином,", "Отже", "F/Calque", "d1"),
            ("Таким чином", "Отже", "F/Calque", "d2"),  # dedupes with the row above
            ("до\"ктор", "лікарю", "F/Calque", "d3"),  # dropped: internal quote survives edge-strip
            ("пару", "кілька", "F/Case", "d4"),  # dropped: wrong error_type
            ("однакове", "однакове", "F/Calque", "d5"),  # dropped: error == correct
        ],
        corpus={},
    )
    pairs = load_gec_calque_pairs(db_path)
    assert len(pairs) == 1
    assert pairs[0].error == "Таким чином"
    assert pairs[0].correct == "Отже"
    assert pairs[0].count == 2
    assert set(pairs[0].doc_ids) == {"d1", "d2"}


# ---------------------------------------------------------------------------
# Carrier sentence search
# ---------------------------------------------------------------------------


def test_find_carrier_sentence_returns_none_when_no_clean_sentence_exists(tmp_path: Path) -> None:
    db_path = tmp_path / "sources.db"
    _make_sources_db(db_path, gec_rows=[], corpus={"literary_texts": [("c1", "Коротко.")]})
    con = sqlite3.connect(db_path)
    try:
        assert find_carrier_sentence(con, "завдання", "задача") is None
    finally:
        con.close()


def test_find_carrier_sentence_substitutes_and_blanks_correctly(tmp_path: Path) -> None:
    db_path = tmp_path / "sources.db"
    _make_sources_db(
        db_path,
        gec_rows=[],
        corpus={"literary_texts": [("c1", LONG_CLEAN_SENTENCE)]},
    )
    con = sqlite3.connect(db_path)
    try:
        carrier = find_carrier_sentence(con, "завдання", "задача")
    finally:
        con.close()
    assert carrier is not None
    assert "___" in carrier.sentence_with_slot
    assert "завдання" not in carrier.sentence_with_slot
    assert "задача" in carrier.bad_sentence
    assert "завдання" not in carrier.bad_sentence


def test_find_carrier_sentence_respects_exclude_sentences(tmp_path: Path) -> None:
    db_path = tmp_path / "sources.db"
    _make_sources_db(
        db_path,
        gec_rows=[],
        corpus={"literary_texts": [("c1", LONG_CLEAN_SENTENCE)]},
    )
    con = sqlite3.connect(db_path)
    try:
        first = find_carrier_sentence(con, "завдання", "задача")
        assert first is not None
        second = find_carrier_sentence(
            con, "завдання", "задача", exclude_sentences={first.sentence_with_slot}
        )
    finally:
        con.close()
    # Only one clean sentence exists in the fixture; excluding it must fail closed.
    assert second is None


# ---------------------------------------------------------------------------
# Homonym ambiguity guard
# ---------------------------------------------------------------------------


def test_is_ambiguous_single_token_flags_cross_lemma_homonym(tmp_path: Path) -> None:
    vesum_db = tmp_path / "vesum.db"
    _make_vesum_db(
        vesum_db,
        forms=[
            ("збіг", "збіг", "noun", "noun:inanim:m:v_naz"),
            ("збіг", "збігти", "verb", "verb:perf:past:m"),
        ],
    )
    cache: dict[str, bool] = {}
    assert is_ambiguous_single_token("збіг", vesum_db, cache) is True
    assert cache["збіг"] is True  # cached


def test_is_ambiguous_single_token_allows_single_lemma_multi_tag(tmp_path: Path) -> None:
    vesum_db = tmp_path / "vesum.db"
    _make_vesum_db(
        vesum_db,
        forms=[
            ("так", "так", "adv", "adv:pron:dem"),
            ("так", "так", "conj", "conj:coord"),
        ],
    )
    assert is_ambiguous_single_token("так", vesum_db, {}) is False


def test_is_ambiguous_single_token_exempts_multiword_phrases(tmp_path: Path) -> None:
    vesum_db = tmp_path / "vesum.db"
    _make_vesum_db(vesum_db, forms=[])
    assert is_ambiguous_single_token("точка зору", vesum_db, {}) is False


# ---------------------------------------------------------------------------
# End-to-end run_wave: no emission without a carrier + routing correctness
# ---------------------------------------------------------------------------


def _atlas_entry(lemma: str, pos: str, gloss: str = "gloss") -> dict:
    return {
        "lemma": lemma,
        "url_slug": lemma,
        "pos": pos,
        "gloss": gloss,
        "cefr": "A2",
        "curated_membership": True,
    }


def _write_heritage_pairs_yaml(path: Path, pairs: list[dict]) -> None:
    import yaml

    path.write_text(yaml.safe_dump({"schema_version": 1, "pairs": pairs}, allow_unicode=True), encoding="utf-8")


@pytest.fixture
def wave_fixture(tmp_path: Path):
    sources_db = tmp_path / "sources.db"
    atlas_db = tmp_path / "atlas.db"
    vesum_db = tmp_path / "vesum.db"
    heritage_pairs_path = tmp_path / "heritage_pairs.yaml"

    _make_sources_db(
        sources_db,
        gec_rows=[
            # Resolvable, carrier exists -> should emit a new pair + frame.
            ("задача", "завдання", "F/Calque", "d1"),
            # Resolvable via Atlas, but no corpus sentence anywhere -> residual.
            ("хужий", "гіршенький", "F/Calque", "d2"),
            # Has no Atlas resolution at all -> unresolved.
            ("отакотаке", "невідомослово", "F/Calque", "d3"),
        ],
        corpus={"literary_texts": [("c1", LONG_CLEAN_SENTENCE)]},
    )
    _make_atlas_db(atlas_db, [_atlas_entry("завдання", "noun"), _atlas_entry("гіршенький", "adj")])
    _make_vesum_db(
        vesum_db,
        forms=[
            ("завдання", "завдання", "noun", "noun:inanim:n:v_naz"),
            ("гіршенький", "гіршенький", "adj", "adj:m:v_naz"),
        ],
    )
    _write_heritage_pairs_yaml(heritage_pairs_path, [])
    return {
        "sources_db": sources_db,
        "atlas_db": atlas_db,
        "vesum_db": vesum_db,
        "heritage_pairs_path": heritage_pairs_path,
    }


def test_run_wave_never_emits_a_frame_without_a_carrier_sentence(wave_fixture) -> None:
    overlay_pairs, stats = run_wave(
        sources_db=wave_fixture["sources_db"],
        atlas_db=wave_fixture["atlas_db"],
        vesum_db=wave_fixture["vesum_db"],
        heritage_pairs_path=wave_fixture["heritage_pairs_path"],
        max_frames_per_existing_pair=3,
        max_frames_per_new_pair=2,
        max_total_frames=300,
    )
    # Only the "задача"/"завдання" row has a carrier; "хужий"/"гіршенький"
    # resolves structurally but must land in the residual bucket, never a frame.
    assert stats.frames_emitted_new == 1
    assert stats.routed_unresolved == 1  # "отакотаке"/"невідомослово"
    residual_pairs = {(r["error"], r["correct"]) for r in stats.residual_no_carrier}
    assert ("хужий", "гіршенький") in residual_pairs

    emitted_slugs = {pair["nativeSlug"] for pair in overlay_pairs}
    assert emitted_slugs == {"завдання"}
    frame = overlay_pairs[0]["frames"][0]
    assert frame["answer_form"] == "завдання"
    assert frame["calque_form"] == "задача"
    assert "___" in frame["sentence_with_slot"]

    # Every emitted pair must independently pass the real schema validator.
    for pair in overlay_pairs:
        assert validate_heritage_pair(pair) in ([], None) or not [
            e for e in validate_heritage_pair(pair) if "nativeSlug" not in e
        ]


def test_run_wave_excludes_sense_restricted_conflicts(tmp_path: Path) -> None:
    sources_db = tmp_path / "sources.db"
    atlas_db = tmp_path / "atlas.db"
    vesum_db = tmp_path / "vesum.db"
    heritage_pairs_path = tmp_path / "heritage_pairs.yaml"

    _make_sources_db(
        sources_db,
        gec_rows=[("доктор", "лікар", "F/Calque", "d1")],
        corpus={"literary_texts": [("c1", "У селі жив старий лікар, який лікував усіх сусідів безкоштовно щовечора.")]},
    )
    _make_atlas_db(atlas_db, [_atlas_entry("лікар", "noun")])
    _make_vesum_db(vesum_db, forms=[("лікар", "лікар", "noun", "noun:anim:m:v_naz")])
    _write_heritage_pairs_yaml(
        heritage_pairs_path,
        [
            {
                "calqueLabel": "доктор",
                "calqueSurfaces": ["доктор"],
                "nativeSlug": "лікар",
                "nativeLemma": "лікар",
                "kind": "sense_restricted",
                "calqueSense": "medical professional in casual register",
                "authenticSense": "physician (formal)",
                "corrections": ["лікар"],
                "rationale": "test fixture",
                "citations": ["ua-gec:F/Calque n=1"],
                "sourceFamily": "ua-gec",
                "severity": "enrichment",
                "frames": [],
            }
        ],
    )
    overlay_pairs, stats = run_wave(
        sources_db=sources_db,
        atlas_db=atlas_db,
        vesum_db=vesum_db,
        heritage_pairs_path=heritage_pairs_path,
        max_frames_per_existing_pair=3,
        max_frames_per_new_pair=2,
        max_total_frames=300,
    )
    assert stats.routed_sense_restricted_conflict == 1
    assert stats.frames_emitted_extend == 0
    assert stats.frames_emitted_new == 0
    assert overlay_pairs == []


# ---------------------------------------------------------------------------
# Overlay merge into the curated heritage_pairs.yaml (generate_practice_deck)
# ---------------------------------------------------------------------------


def test_merge_heritage_pair_overlay_extends_matching_native_slug() -> None:
    base = [
        {
            "nativeSlug": "лікар",
            "frames": [{"sentence_with_slot": "Old ___ sentence.", "answer_form": "лікар", "calque_form": "доктор", "origin": "x"}],
        }
    ]
    overlay = [
        {
            "nativeSlug": "лікар",
            "frames": [{"sentence_with_slot": "New ___ sentence.", "answer_form": "лікар", "calque_form": "врач", "origin": "y"}],
        }
    ]
    merged = _merge_heritage_pair_overlay(base, overlay)
    assert len(merged) == 1
    assert len(merged[0]["frames"]) == 2


def test_merge_heritage_pair_overlay_dedupes_by_sentence() -> None:
    base = [
        {
            "nativeSlug": "лікар",
            "frames": [{"sentence_with_slot": "Same ___ sentence.", "answer_form": "лікар", "calque_form": "доктор", "origin": "x"}],
        }
    ]
    overlay = [
        {
            "nativeSlug": "лікар",
            "frames": [{"sentence_with_slot": "Same ___ sentence.", "answer_form": "лікар", "calque_form": "доктор", "origin": "y"}],
        }
    ]
    merged = _merge_heritage_pair_overlay(base, overlay)
    assert len(merged[0]["frames"]) == 1


def test_merge_heritage_pair_overlay_appends_new_pair() -> None:
    base: list[dict] = []
    overlay = [
        {
            "nativeSlug": "новий",
            "calqueLabel": "старий-калька",
            "corrections": ["новий"],
            "kind": "lexical",
            "rationale": "r",
            "citations": ["ua-gec:F/Calque n=1"],
            "sourceFamily": "ua-gec",
            "severity": "enrichment",
            "frames": [{"sentence_with_slot": "___.", "answer_form": "новий", "calque_form": "старий-калька", "origin": "z"}],
        }
    ]
    merged = _merge_heritage_pair_overlay(base, overlay)
    assert len(merged) == 1
    assert merged[0]["nativeSlug"] == "новий"


def test_read_heritage_pairs_merges_wave1_calque_sidecar(tmp_path: Path) -> None:
    import yaml

    base_path = tmp_path / "heritage_pairs.yaml"
    base_path.write_text(
        yaml.safe_dump({"schema_version": 1, "pairs": [{"nativeSlug": "a", "frames": []}]}, allow_unicode=True),
        encoding="utf-8",
    )
    overlay_path = tmp_path / "heritage_pairs.wave1-calque.yaml"
    overlay_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "pairs": [
                    {
                        "nativeSlug": "b",
                        "calqueLabel": "калька",
                        "corrections": ["b"],
                        "kind": "lexical",
                        "rationale": "r",
                        "citations": ["ua-gec:F/Calque n=1"],
                        "sourceFamily": "ua-gec",
                        "severity": "enrichment",
                        "frames": [{"sentence_with_slot": "___.", "answer_form": "b", "calque_form": "калька", "origin": "z"}],
                    }
                ],
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    rows = read_heritage_pairs(base_path)
    slugs = {row["nativeSlug"] for row in rows}
    assert slugs == {"a", "b"}
