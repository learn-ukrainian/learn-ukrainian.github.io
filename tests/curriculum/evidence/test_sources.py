import hashlib
import json
import sqlite3

import pytest

from scripts.curriculum.evidence import codes, sources


def test_paradigm_grouping_keeps_entry_identity_and_order(synthetic_vesum):
    with sources.Sources(vesum_db=synthetic_vesum) as api:
        result = api.inspect_lemma_forms("synthetic", "noun")
    assert set(result.forms_by_entry) == {10, 20}
    assert [row["word_form"] for row in result.forms_by_entry[10]] == ["synthetic-a", "synthetic-b"]
    assert len(result.raw["forms"]) == 4  # untouched source envelope also has verb POS
    assert result.forms_by_entry[10][1]["markers"][0]["marker"] == "alt"
    assert result.content_hash == hashlib.sha256(b"synthetic-vesum").hexdigest()


@pytest.mark.parametrize("status", ["ok", "ambiguous", "not_found", "invalid_input"])
def test_stress_preserves_oracle_and_maps_tags(monkeypatch, status):
    raw = {
        "status": status,
        "matches": [{"synthetic": "source bytes"}],
        "unresolvable_by_tags": True,
        "source": {"digest": "a" * 64},
    }
    calls = []

    def oracle(word, *, tags):
        calls.append((word, tags))
        return raw

    monkeypatch.setattr(sources.stress, "verify_stress", oracle)
    result = sources.stress_for_form("synthetic’form", "noun:f:v_rod")
    assert result.raw is raw
    assert result.content_hash == "a" * 64
    assert calls == [("synthetic'form", ["Case=Gen", "Gender=Fem", "Number=Sing", "upos=NOUN"])]


def test_stress_batch_deduplicates_only_same_form_and_tags(monkeypatch):
    calls = []

    def oracle(word, *, tags):
        calls.append((word, tags))
        return {"status": "not_found", "matches": [], "source": {"digest": "b" * 64}}

    monkeypatch.setattr(sources.stress, "verify_stress", oracle)
    progress = []
    with sources.Sources(report=progress.append) as api:
        result = api.stress_many(
            [
                ("synthetic", "noun:f:v_naz"),
                ("synthetic", "noun:f:v_naz"),
                ("synthetic", "noun:f:v_rod"),
                ("synthetic-oblique", "noun:f:v_dav"),
            ]
        )
    assert len(result) == len(calls) == 3
    assert progress == ["stress: 3/3"]


def test_readonly_uri_and_ulif_group_gate(monkeypatch, synthetic_sources):
    actual_connect = sqlite3.connect
    calls = []

    def connect(database, **kwargs):
        calls.append((database, kwargs))
        return actual_connect(database, **kwargs)

    monkeypatch.setattr(sources.sqlite3, "connect", connect)
    with sources.Sources(sources_db=synthetic_sources) as api:
        result = api.ulif_entries(["synthetic", "synthetic-checked", "synthetic-mixed", "synthetic-missing"])
        assert not api.ulif_group_checked(result.raw["synthetic"])
        assert api.ulif_group_checked(result.raw["synthetic-checked"])
        assert not api.ulif_group_checked(result.raw["synthetic-mixed"])
        assert not api.ulif_group_checked(result.raw["synthetic-missing"])
        assert result.raw["synthetic"][0]["sections"][0]["payload_json"] == '{"synthetic": ["source-bytes"]}'
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            api._db().execute("DELETE FROM ulif_dictua_entries")
        assert api.journal_mode == "delete"
        assert api.snapshot_age() > 0
    assert calls == [(synthetic_sources.resolve().as_uri() + "?mode=ro", {"uri": True, "isolation_level": None})]
    # rows-v2: the identity of a read is the digest of the rows it returned, never the file.
    assert result.content_hash == sources.batch_digest(result.raw)
    assert result.metadata == {"scheme": "rows-v2"}
    assert api.snapshot_age() == 0.0


def test_gloss_exact_spelling_pos_and_order(synthetic_sources):
    with sources.Sources(sources_db=synthetic_sources) as api:
        result = api.gloss_rows(
            [
                ("synthetic", "noun"),
                ("synthetic", "adj"),
                ("synthetic-adj", "adj"),
                ("synthetic-missing", "noun"),
                ("synthet", "noun"),
            ]
        )
    assert [row["id"] for row in result.raw["synthetic", "noun"]] == [1, 2]
    assert json.loads(result.raw["synthetic", "noun"][0]["translations"])[0] == "first translation"
    assert result.raw["synthetic", "adj"] == []
    assert result.raw["synthetic-missing", "noun"] == []
    assert result.raw["synthet", "noun"] == []
    assert result.raw["synthetic-adj", "adj"][0]["id"] == 4


def test_gloss_pronoun_and_function_word_rows_ignore_alphabet_letters(synthetic_sources):
    # Source-derived first-translation fixtures: sources.db dmklinger_uk_en ids
    # 15 (я pronoun), 19149 (я letter-name noun), 19148 (ж), and 2582 (і).
    with sqlite3.connect(synthetic_sources) as conn:
        conn.executemany(
            "INSERT INTO dmklinger_uk_en VALUES (?,?,?,?,?,?)",
            [
                (15, "я", "pronoun", '["I (personal pronoun)"]', "", "synthetic"),
                (19149, "я", "noun", '["ya (a letter of the Cyrillic alphabet)"]', "", "synthetic"),
                (19148, "ж", "particle", '["The ninth letter of the Ukrainian alphabet"]', "", "synthetic"),
                (13, "у", "particle", '["in (preposition)"]', "", "synthetic"),
                (2582, "і", "particle", '["and (conjunction)"]', "", "synthetic"),
                (25, "цей", "pronoun", '["this (pronoun)"]', "", "synthetic"),
                (16, "ні", "particle", '["no (preposition)"]', "", "synthetic"),
            ],
        )
    with sources.Sources(sources_db=synthetic_sources) as api:
        result = api.gloss_rows(
            [
                ("я", "noun"),
                ("ж", "part"),
                ("у", "prep"),
                ("і", "conj"),
                ("цей", "adj"),
                ("ні", "part"),
            ]
        )
    assert [r["id"] for r in result.raw["я", "noun"]] == [15, 19149]
    assert [r["id"] for r in sources.filter_pronominal_gloss_rows(result.raw["я", "noun"], "я", "noun", True)] == [15]
    assert [r["id"] for r in sources.filter_pronominal_gloss_rows(result.raw["я", "noun"], "я", "noun", False)] == [
        19149
    ]
    assert result.raw["ж", "part"] == []
    assert [r["id"] for r in result.raw["у", "prep"]] == [13]
    assert [r["id"] for r in result.raw["і", "conj"]] == [2582]
    assert [r["id"] for r in result.raw["цей", "adj"]] == [25]
    assert result.raw["ні", "part"] == []


def test_function_gloss_prefers_labelled_row_over_particle(synthetic_sources):
    # The particle translation is copied from sources.db dmklinger_uk_en id 2582 (і).
    # The labelled row is a deliberate collision: this DB currently has no conjunction-labelled rows.
    translation = '["and (used to connect two similar words, phrases, et cetera) (conjunction)"]'
    with sqlite3.connect(synthetic_sources) as conn:
        conn.executemany(
            "INSERT INTO dmklinger_uk_en VALUES (?,?,?,?,?,?)",
            [
                (2582, "і", "particle", translation, "", "sources.db:2582"),
                (2583, "і", "conjunction", translation, "", "test collision from sources.db:2582"),
            ],
        )
    with sources.Sources(sources_db=synthetic_sources) as api:
        assert [row["id"] for row in api.gloss_rows([("і", "conj")]).raw["і", "conj"]] == [2583]
    with sqlite3.connect(synthetic_sources) as conn:
        conn.execute("DELETE FROM dmklinger_uk_en WHERE id = 2583")
    with sources.Sources(sources_db=synthetic_sources) as api:
        assert [row["id"] for row in api.gloss_rows([("і", "conj")]).raw["і", "conj"]] == [2582]


def test_kaikki_exact_readonly_and_alignment(tmp_path):
    side = tmp_path / "kaikki.sqlite"
    # POS and gloss arrays copied from local side-db-v1 content_sha256 251974b6...:
    # lemma_key вона has pron; після has adv+prep.
    with sqlite3.connect(side) as conn:
        conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
        conn.execute("CREATE TABLE kaikki (lemma_key TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        conn.executemany(
            "INSERT INTO meta VALUES (?, ?)",
            [
                ("schema_version", "side-db-v1"),
                ("kind", "kaikki"),
                ("content_sha256", "a" * 64),
                ("row_count", "2"),
            ],
        )
        conn.executemany(
            "INSERT INTO kaikki VALUES (?, ?)",
            [
                ("вона", json.dumps({"pos": ["pron"], "glosses": ["she (person)", "it (feminine gender)"]})),
                ("після", json.dumps({"pos": ["adv", "prep"], "glosses": ["after (in time)", "later, afterwards"]})),
            ],
        )
    with sources.Sources(kaikki_db=side) as api:
        result = api.kaikki_rows(["вона", "після", "synthetic-absent"])
        assert result.content_hash == "a" * 64
        assert result.raw["synthetic-absent"] is None
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            api._kaikki_conn.execute("DELETE FROM kaikki")
    assert sources.aligned_kaikki_gloss(result.raw["вона"], "noun", True) == (
        "she (person); it (feminine gender)",
        None,
    )
    assert sources.aligned_kaikki_gloss(result.raw["після"], "prep", False) == (None, "kaikki_multi_pos")
    assert sources.aligned_kaikki_gloss(result.raw["вона"], "verb", False) == (None, "kaikki_pos_mismatch")
    assert sources.aligned_kaikki_gloss(result.raw["synthetic-absent"], "noun", True) == (None, "kaikki_absent")


@pytest.mark.parametrize(
    "gloss",
    [
        "(bad", "bad)", "[bad", "bad]", "(bad]", "[bad)",
        "“bad", "bad”", '"bad',
        ")bad", "]bad", "”bad", ",bad", ";bad", ".bad",
        "мною",
        # Copied from Kaikki side-db-v1 content_sha256
        # 251974b612a9bb54902920f8427ff357f648f60c18277a1635f501c02cab43c5.
        "“under”), used before awkward consonant clusters and chiefly before мно́ю (mnóju)",
        "“over”), used before awkward consonant clusters and chiefly before мно́ю (mnóju)",
        "“in front of”), used before awkward consonant clusters and chiefly before мно́ю (mnóju)",
    ],
)
def test_kaikki_refuses_each_malformed_gloss(gloss):
    payload = {"pos": ["prep"], "glosses": [gloss]}
    assert sources.aligned_kaikki_gloss(payload, "prep", False) == (None, "kaikki_malformed")


def test_kaikki_refuses_entire_entry_if_one_gloss_is_malformed():
    payload = {"pos": ["prep"], "glosses": ["under", "bad)"]}
    assert sources.aligned_kaikki_gloss(payload, "prep", False) == (None, "kaikki_malformed")
    payload["glosses"] = ["under (a roof)", 'beneath "something" [figurative]']
    assert sources.aligned_kaikki_gloss(payload, "prep", False) == (
        'under (a roof); beneath "something" [figurative]', None
    )


def test_missing_kaikki_fails_closed_with_named_code(tmp_path):
    with sources.Sources(kaikki_db=tmp_path / "missing.sqlite") as api:
        with pytest.raises(FileNotFoundError, match=codes.SOURCE_UNAVAILABLE):
            api.kaikki_rows(["вона"])


def test_kaikki_env_path_override(monkeypatch, tmp_path):
    side = tmp_path / "kaikki.sqlite"
    monkeypatch.setenv("LEXICON_KAIKKI_SIDE_DB", str(side))
    assert sources.Sources().kaikki_db == side


def test_pronoun_tags_reach_conditioned_stress_oracle(monkeypatch):
    calls = []

    def oracle(word, *, tags):
        calls.append((word, tags))
        return {"status": "not_found", "matches": [], "source": {"digest": "a" * 64}}

    monkeypatch.setattr(sources.stress, "verify_stress", oracle)
    sources.stress_for_form("цьому", "adj:m:v_dav:pron:dem")
    sources.stress_for_form("цьому", "adj:m:v_mis:pron:dem")
    assert calls[0][1] == ["Case=Dat", "Gender=Masc", "Number=Sing", "PronType=Dem", "upos=PRON"]
    assert calls[1][1] == ["Case=Loc", "Gender=Masc", "Number=Sing", "PronType=Dem", "upos=PRON"]


def test_cefr_and_heritage_use_readonly_connection(monkeypatch, synthetic_sources):
    from scripts.wiki import sources_db

    seen = []

    def heritage(word, *, include_live_slovnyk):
        assert not include_live_slovnyk
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            sources_db._get_conn().execute("DELETE FROM puls_cefr")
        seen.append(word)
        return [{"synthetic": "unchanged"}]

    monkeypatch.setattr(sources_db, "search_heritage", heritage)
    with sources.Sources(sources_db=synthetic_sources) as api:
        assert api.cefr_levels(["synthetic"]).raw["synthetic"][0]["level"] == "A1"
        hits = api.heritage(["syntheticʼform"]).raw["synthetic'form"]
    # Every hit carries the identity of what was copied (its own digest excluded from itself).
    assert hits == [{"synthetic": "unchanged", "row_sha256": sources.row_digest({"synthetic": "unchanged"})}]
    assert sources.heritage_hit_digest(hits[0]) == hits[0]["row_sha256"]
    assert seen == ["synthetic'form"]
    assert sources_db._active_connection.get() is None


def test_verify_words_batches_and_normalizes(monkeypatch, synthetic_vesum):
    calls = []

    def verify(words, *, pos_filter, db_path):
        calls.append((words, pos_filter, db_path))
        return {word: [] for word in words}

    monkeypatch.setattr(sources.vesum, "verify_words", verify)
    with sources.Sources(vesum_db=synthetic_vesum) as api:
        result = api.verify_words([f"synthetic’{i}" for i in range(501)], "noun")
    assert [len(call[0]) for call in calls] == [500, 1]
    assert calls[0][0][0] == "synthetic'0"
    assert calls[0][1:] == ("noun", synthetic_vesum)
    assert len(result.raw) == 501


def test_gloss_batch_digest_is_canonical_over_tuple_keys(synthetic_sources):
    with sources.Sources(sources_db=synthetic_sources) as api:
        result = api.gloss_rows([("synthetic", "noun"), ("synthetic-adj", "adj")])
        reversed_order = api.gloss_rows([("synthetic-adj", "adj"), ("synthetic", "noun")])
    assert result.raw["synthetic", "noun"]  # non-empty batch keyed by tuples
    with pytest.raises(TypeError):
        json.dumps(result.raw)
    expected = hashlib.sha256(
        json.dumps(
            sorted(([list(key), rows] for key, rows in result.raw.items()), key=lambda pair: pair[0]),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()
    assert result.content_hash == expected
    assert reversed_order.content_hash == expected  # request order is not identity


def test_row_and_aggregate_digests_are_canonical():
    row = {"b": 1, "a": "Привіт", "c": None}
    assert sources.row_digest(row) == sources.row_digest({"c": None, "a": "Привіт", "b": 1})
    assert sources.row_digest(row) != sources.row_digest({**row, "c": ""})
    with pytest.raises(TypeError):
        sources.row_digest({"blob": b"bytes"})
    with pytest.raises(TypeError):
        sources.row_digest(["not", "a", "row"])
    empty = hashlib.sha256(b"[]").hexdigest()
    assert sources.aggregate_digest([]) == empty
    pairs = [("textbooks:c1", "a" * 64), ("style_guide:1", "b" * 64), ("textbooks:c1", "a" * 64)]
    assert sources.aggregate_digest(pairs) == sources.aggregate_digest(reversed(pairs[:2]))
    assert sources.aggregate_digest(pairs) != empty


def test_pinned_snapshot_ignores_commits_and_never_blocks_a_wal_writer(synthetic_sources_wal):
    progress = []
    with sources.Sources(sources_db=synthetic_sources_wal, report=progress.append) as api:
        before = api.gloss_rows([("synthetic", "noun")])  # first read pins the snapshot
        assert api.journal_mode == "wal"
        assert progress[0].startswith("snapshot: pinned; journal_mode: wal; wal_bytes: ")

        writer = sqlite3.connect(synthetic_sources_wal, timeout=2.0)
        with writer:
            writer.execute("UPDATE dmklinger_uk_en SET text='uncited WAL edit' WHERE id=4")  # uncited row
            writer.execute("UPDATE dmklinger_uk_en SET translations='[\"changed\"]' WHERE id=1")  # cited row
        writer.close()  # committed with no "database is locked" while the reader is pinned

        with sqlite3.connect(synthetic_sources_wal) as fresh:
            assert fresh.execute("SELECT translations FROM dmklinger_uk_en WHERE id=1").fetchone()[0] == '["changed"]'

        during = api.gloss_rows([("synthetic", "noun")])
        assert json.loads(during.raw["synthetic", "noun"][0]["translations"])[0] == "first translation"
        assert during.content_hash == before.content_hash  # the session never mixes source versions
    assert any(line.startswith("snapshot: released after ") and "journal_mode: wal" in line for line in progress)

    with sources.Sources(sources_db=synthetic_sources_wal) as api:
        after = api.gloss_rows([("synthetic", "noun")])
    assert after.content_hash != before.content_hash  # a new session sees the commit


def test_snapshot_stops_before_the_next_read_when_the_wal_exceeds_its_ceiling(synthetic_sources_wal):
    progress = []
    api = sources.Sources(sources_db=synthetic_sources_wal, report=progress.append, wal_ceiling_bytes=1024)
    api.gloss_rows([("synthetic", "noun")])
    writer = sqlite3.connect(synthetic_sources_wal, timeout=2.0)
    with writer:
        # A pinned reader keeps the WAL from being checkpointed past its mark, so this grows it.
        writer.executemany(
            "INSERT INTO dmklinger_uk_en (word, pos, translations, text, source) VALUES (?,?,?,?,?)",
            [("bulk", "noun", "[]", "x" * 4096, "synthetic")] * 64,
        )
    writer.close()
    assert api.wal_bytes() > 1024
    with pytest.raises(RuntimeError, match=codes.SNAPSHOT_LIMIT) as excinfo:
        api.gloss_rows([("synthetic", "noun")])
    assert "WAL" in str(excinfo.value) and "ceiling 1024" in str(excinfo.value)
    assert api._conn is None  # the snapshot was released before raising
    assert api.snapshot_age() == 0.0
    assert any(line.startswith("snapshot: released after ") for line in progress)
    api.close()


def test_snapshot_stops_when_free_disk_falls_below_the_floor(synthetic_sources):
    api = sources.Sources(sources_db=synthetic_sources, free_disk_floor_bytes=2**62)
    with pytest.raises(RuntimeError, match=codes.SNAPSHOT_LIMIT) as excinfo:
        api.gloss_rows([("synthetic", "noun")])
    assert "free disk" in str(excinfo.value)
    assert api._conn is None


def test_snapshot_limits_come_from_config_and_environment(monkeypatch, synthetic_sources):
    from scripts.curriculum.evidence import config

    assert config.WAL_CEILING_BYTES == 4 * 1024**3
    assert config.FREE_DISK_FLOOR_BYTES == 10 * 1024**3
    monkeypatch.setenv(config.WAL_CEILING_ENV, "12345")
    monkeypatch.setenv(config.FREE_DISK_FLOOR_ENV, "0")
    api = sources.Sources(sources_db=synthetic_sources)
    assert (api.wal_ceiling_bytes, api.free_disk_floor_bytes) == (12345, 0)
    monkeypatch.setenv(config.WAL_CEILING_ENV, "-1")
    with pytest.raises(ValueError, match=config.WAL_CEILING_ENV):
        sources.Sources(sources_db=synthetic_sources)


def test_journal_mode_from_header(synthetic_sources, tmp_path):
    assert sources.journal_mode_from_header(synthetic_sources) == "delete"
    with sqlite3.connect(synthetic_sources) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
    assert synthetic_sources.read_bytes()[18:20] == b"\x02\x02"
    assert sources.journal_mode_from_header(synthetic_sources) == "wal"
    assert sources.journal_mode_from_header(tmp_path / "missing.db") is None
    (tmp_path / "text.db").write_bytes(b"not a database at all, just bytes")
    assert sources.journal_mode_from_header(tmp_path / "text.db") is None


def test_missing_db_does_not_create_it(tmp_path):
    path = tmp_path / "synthetic-missing.db"
    with sources.Sources(sources_db=path) as api:
        with pytest.raises(FileNotFoundError, match=codes.SOURCE_UNAVAILABLE):
            api.ulif_entries(["synthetic"])
    assert not path.exists()


def test_vesum_change_without_metadata_refresh_fails_closed(synthetic_vesum):
    with sources.Sources(vesum_db=synthetic_vesum) as api:
        api.inspect_lemma_forms("synthetic", "noun")
        with sqlite3.connect(synthetic_vesum) as writer:
            writer.execute("DELETE FROM forms_all WHERE id=1")
        with pytest.raises(ValueError, match=codes.SOURCE_CHANGED):
            api.inspect_lemma_forms("synthetic", "noun")


def test_inspection_batch_normalizes_and_deduplicates(monkeypatch, synthetic_vesum):
    from types import SimpleNamespace

    calls = []
    raw = {"status": "not_found", "forms": []}

    def inspect(lemma, *, db_path):
        calls.append(lemma)
        return SimpleNamespace(as_dict=lambda: raw)

    monkeypatch.setattr(sources.vesum, "inspect_lemma", inspect)
    with sources.Sources(vesum_db=synthetic_vesum) as api:
        result = api.inspect_many([("synthetic’form", "noun"), ("synthetic'form", "noun")])
    assert calls == ["synthetic'form"]
    assert result["synthetic'form", "noun"].raw is raw
    assert result["synthetic'form", "noun"].forms_by_entry == {}


def test_russian_wrapper_uses_batch_and_copies_results(monkeypatch, synthetic_vesum):
    from scripts.verification import check_ru_morph

    calls = []
    raw = {"synthetic'form": {"matches_russian": True, "confidence": 0.75}}

    def check(words, *, verified_words):
        calls.append((words, verified_words))
        return raw

    monkeypatch.setattr(check_ru_morph, "check_russian_patterns_batch", check)
    with sources.Sources(vesum_db=synthetic_vesum) as api:
        result = api.russian_patterns(["syntheticʼform"])
    assert result.raw is raw
    assert calls == [(["synthetic'form"], set())]
    assert len(result.content_hash) == 64
