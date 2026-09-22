import hashlib
import json
import sqlite3
from pathlib import Path

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
    assert calls == [(synthetic_sources.resolve().as_uri() + "?mode=ro", {"uri": True})]
    assert result.content_hash == hashlib.sha256(synthetic_sources.read_bytes()).hexdigest()


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
        assert api.heritage(["syntheticʼform"]).raw["synthetic'form"] == [{"synthetic": "unchanged"}]
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


def test_database_changes_fail_closed(synthetic_sources):
    with sources.Sources(sources_db=synthetic_sources) as api:
        api.gloss_rows([("synthetic", "noun")])
        with sqlite3.connect(synthetic_sources) as writer:
            writer.execute("DELETE FROM dmklinger_uk_en")
        with pytest.raises(ValueError, match=codes.SOURCE_CHANGED):
            api.gloss_rows([("synthetic", "noun")])


def test_wal_content_participates_in_hash(synthetic_sources):
    with sqlite3.connect(synthetic_sources) as writer:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("UPDATE dmklinger_uk_en SET text='synthetic WAL value' WHERE id=1")
        writer.commit()
        with sources.Sources(sources_db=synthetic_sources) as api:
            result = api.gloss_rows([("synthetic", "noun")])
        assert result.raw["synthetic", "noun"][0]["text"] == "synthetic WAL value"
        assert (
            result.metadata["wal_sha256"] == hashlib.sha256(Path(f"{synthetic_sources}-wal").read_bytes()).hexdigest()
        )
        assert result.content_hash != result.metadata["db_sha256"]


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
