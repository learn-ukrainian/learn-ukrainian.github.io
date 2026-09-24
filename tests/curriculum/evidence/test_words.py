"""Tests for scripts.curriculum.evidence.words building the level word store."""

import json
import sqlite3
import stat

import pytest
import yaml

from scripts.curriculum.evidence import codes, lock, registry, sources, words


def test_monosyllable_never_calls_oracle(synthetic_vesum, synthetic_sources, tmp_path, monkeypatch):
    calls = []

    def fail_oracle(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("Oracle should not be called for monosyllable")

    monkeypatch.setattr(sources.stress, "verify_stress", fail_oracle)

    # In synthetic_vesum, let's add a 1-vowel form and a 2-vowel form
    with sqlite3.connect(synthetic_vesum) as conn:
        conn.execute("DELETE FROM forms_all")
        conn.execute("INSERT INTO forms_all VALUES (1, 100, 'ма', 'мама', 'noun', 'noun:f:v_kly:short', '', '')")

    req_path = tmp_path / "req.yaml"
    req_path.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "level": "a1",
                "words": [{"lemma": "мама", "pos": "noun", "want": "new"}],
            }
        ),
        encoding="utf-8",
    )

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = words.build_words(
            "a1",
            req_path,
            evidence_dir=tmp_path,
            sources_instance=api,
            dry_run=True,
        )

    assert calls == []
    word = res["store"]["words"][0]
    form_entry = word["forms"][0]
    assert form_entry["form"] == "ма"
    assert form_entry["stress_source"] == "none"
    assert form_entry["stressed"] == "ма"


def test_unchecked_ulif_yields_no_ulif_stress(synthetic_vesum, synthetic_sources, tmp_path, monkeypatch):
    # Oracle returns ambiguous for synthetic-b
    def mock_stress(word, *, tags):
        if word == "synthetic-b":
            return {
                "status": "ambiguous",
                "matches": [
                    {
                        "stressed_form": "syn-1",
                        "unstressed_form": "synthetic-b",
                        "vowel_index": 1,
                        "vowel_indices": [1],
                        "vesum": None,
                        "required_tags": [],
                        "override_applied": False,
                    },
                    {
                        "stressed_form": "syn-2",
                        "unstressed_form": "synthetic-b",
                        "vowel_index": 2,
                        "vowel_indices": [2],
                        "vesum": None,
                        "required_tags": [],
                        "override_applied": False,
                    },
                ],
                "unresolvable_by_tags": True,
                "source": {"digest": "d" * 64},
            }
        return {
            "status": "ok",
            "matches": [
                {
                    "stressed_form": "synthetic-a-stressed",
                    "unstressed_form": "synthetic-a",
                    "vowel_index": 1,
                    "vowel_indices": [1],
                    "vesum": None,
                    "required_tags": [],
                    "override_applied": False,
                }
            ],
            "unresolvable_by_tags": False,
            "source": {"digest": "d" * 64},
        }

    monkeypatch.setattr(sources.stress, "verify_stress", mock_stress)

    req_path = tmp_path / "req.yaml"
    req_path.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "level": "a1",
                "words": [
                    {
                        "lemma": "synthetic",
                        "pos": "noun",
                        "want": "new",
                        "entry": {"source": "vesum", "entry_id": 10},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = words.build_words(
            "a1",
            req_path,
            evidence_dir=tmp_path,
            sources_instance=api,
            dry_run=False,
        )

    word = res["store"]["words"][0]
    assert word["ulif"] == "pending"
    for f in word["forms"]:
        assert f["stress_source"] != "ulif"

    # Pending form has no stressed key and has stress_candidates + unresolvable_by_tags
    pending_form = next(f for f in word["forms"] if f["form"] == "synthetic-b")
    assert pending_form["stress_source"] == "pending"
    assert "stressed" not in pending_form
    assert len(pending_form["stress_candidates"]) == 2
    assert pending_form["unresolvable_by_tags"] is True


def test_checked_ulif_entry_yields_ulif_stress(synthetic_vesum, synthetic_sources, tmp_path):
    # Setup checked ULIF entry with paradigm section
    with sqlite3.connect(synthetic_sources) as conn:
        conn.execute(
            "INSERT INTO ulif_dictua_sections VALUES (10, 2, 'paradigm', 0, '', ?)",
            (json.dumps({"synthetic-a": "synthetic-a-ulif-stressed"}),),
        )

    req_path = tmp_path / "req.yaml"
    req_path.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "level": "a1",
                "words": [
                    {
                        "lemma": "synthetic-checked",
                        "pos": "noun",
                        "want": "new",
                        "entry": {"source": "vesum", "entry_id": 10},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with sqlite3.connect(synthetic_vesum) as conn:
        conn.execute("DELETE FROM forms_all")
        conn.execute(
            "INSERT INTO forms_all VALUES (1, 10, 'synthetic-a', 'synthetic-checked', 'noun', 'noun:f:v_naz', '', '')"
        )

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = words.build_words(
            "a1",
            req_path,
            evidence_dir=tmp_path,
            sources_instance=api,
            dry_run=True,
        )

    word = res["store"]["words"][0]
    assert word["ulif"]["source"] == "ulif"
    assert word["ulif"]["key"] == ["synthetic-original", 1]
    assert len(word["ulif"]["row_sha256"]) == 64  # the entry row with its ordered sections
    assert len(word["forms"]) == 1
    assert word["forms"][0]["form"] == "synthetic-a"
    assert word["forms"][0]["stress_source"] == "ulif"
    assert word["forms"][0]["stressed"] == "synthetic-a-ulif-stressed"


def test_homograph_with_ulif_entry_id_resolves_and_records_key(
    synthetic_vesum, synthetic_sources, tmp_path, monkeypatch
):
    monkeypatch.setattr(
        sources.stress,
        "verify_stress",
        lambda w, **kw: {
            "status": "ok",
            "matches": [
                {
                    "stressed_form": f"{w}-stressed",
                    "unstressed_form": w,
                    "vowel_index": 0,
                    "vowel_indices": [0],
                    "vesum": None,
                    "required_tags": [],
                    "override_applied": False,
                }
            ],
            "source": {"digest": "c" * 64},
        },
    )

    with sqlite3.connect(synthetic_sources) as conn:
        conn.execute(
            "INSERT INTO ulif_dictua_entries VALUES (15, 'synthetic', 2, 'synthetic-original', 'noun', '', 0, 'ok', 'synthetic-time')"
        )

    req_path = tmp_path / "req.yaml"
    req_path.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "level": "a1",
                "words": [
                    {
                        "lemma": "synthetic",
                        "pos": "noun",
                        "want": "new",
                        "entry": {"source": "ulif", "homonym_index": 2},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = words.build_words(
            "a1",
            req_path,
            evidence_dir=tmp_path,
            sources_instance=api,
            dry_run=False,
        )

    word = res["store"]["words"][0]
    assert word["entry"] == {"source": "ulif", "key": ["synthetic-original", 2]}
    assert len(word["forms"]) == 1
    assert word["forms"][0]["form"] == "synthetic-a"
    reg = registry.load(tmp_path / "_words.registry.yaml")
    assert reg[0]["entry"] == {"source": "ulif", "key": ["synthetic-original", 2]}


def test_missing_ulif_homonym_rejected_multi_entry(synthetic_vesum, synthetic_sources, tmp_path):
    # Fixture has only ULIF homonym 1 for "synthetic"; homonym 2 is not in the source.
    req_path = tmp_path / "req.yaml"
    req_path.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "level": "a1",
                "words": [
                    {
                        "lemma": "synthetic",
                        "pos": "noun",
                        "want": "new",
                        "entry": {"source": "ulif", "homonym_index": 2},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        with pytest.raises(ValueError, match=codes.INVALID_REQUEST):
            words.build_words(
                "a1",
                req_path,
                evidence_dir=tmp_path,
                sources_instance=api,
                dry_run=True,
            )


def test_missing_ulif_homonym_rejected_single_entry(synthetic_vesum, synthetic_sources, tmp_path):
    # "synthetic-checked" has a single checked ULIF homonym (1) and one VESUM entry.
    with sqlite3.connect(synthetic_vesum) as conn:
        conn.execute("DELETE FROM forms_all")
        conn.execute(
            "INSERT INTO forms_all VALUES (1, 10, 'synthetic-a', 'synthetic-checked', 'noun', 'noun:f:v_naz', '', '')"
        )

    req_path = tmp_path / "req.yaml"
    req_path.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "level": "a1",
                "words": [
                    {
                        "lemma": "synthetic-checked",
                        "pos": "noun",
                        "want": "new",
                        "entry": {"source": "ulif", "homonym_index": 2},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        with pytest.raises(ValueError, match=codes.INVALID_REQUEST):
            words.build_words(
                "a1",
                req_path,
                evidence_dir=tmp_path,
                sources_instance=api,
                dry_run=True,
            )


def test_homograph_without_entry_is_unresolved(synthetic_vesum, synthetic_sources, tmp_path):
    req_path = tmp_path / "req.yaml"
    req_path.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "level": "a1",
                "words": [{"lemma": "synthetic", "pos": "noun", "want": "new"}],
            }
        ),
        encoding="utf-8",
    )

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = words.build_words(
            "a1",
            req_path,
            evidence_dir=tmp_path,
            sources_instance=api,
            dry_run=True,
        )

    word = res["store"]["words"][0]
    assert word["entry"] == "unresolved"
    assert word["forms"] == []
    assert len(word["candidates"]) == 2
    cands = {c["entry_id"] for c in word["candidates"]}
    assert cands == {10, 20}


def test_homograph_with_entry_id_resolves_one_entry(synthetic_vesum, synthetic_sources, tmp_path, monkeypatch):
    monkeypatch.setattr(
        sources.stress,
        "verify_stress",
        lambda w, **kw: {
            "status": "ok",
            "matches": [
                {
                    "stressed_form": f"{w}-stressed",
                    "unstressed_form": w,
                    "vowel_index": 0,
                    "vowel_indices": [0],
                    "vesum": None,
                    "required_tags": [],
                    "override_applied": False,
                }
            ],
            "source": {"digest": "c" * 64},
        },
    )

    req_path = tmp_path / "req.yaml"
    req_path.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "level": "a1",
                "words": [
                    {
                        "lemma": "synthetic",
                        "pos": "noun",
                        "want": "new",
                        "entry": {"source": "vesum", "entry_id": 20},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = words.build_words(
            "a1",
            req_path,
            evidence_dir=tmp_path,
            sources_instance=api,
            dry_run=True,
        )

    word = res["store"]["words"][0]
    assert word["entry"] == {"source": "vesum", "entry_id": 20}
    assert len(word["forms"]) == 1
    assert word["forms"][0]["form"] == "synthetic-a"


def test_trie_knows_lemma_not_oblique_form(synthetic_vesum, synthetic_sources, tmp_path, monkeypatch):
    def mock_stress(word, *, tags):
        if "Case=Gen" in str(tags):
            return {"status": "not_found", "matches": [], "source": {"digest": "t" * 64}}
        return {
            "status": "ok",
            "matches": [
                {
                    "stressed_form": f"{word}-stressed",
                    "unstressed_form": word,
                    "vowel_index": 0,
                    "vowel_indices": [0],
                    "vesum": None,
                    "required_tags": [],
                    "override_applied": False,
                }
            ],
            "source": {"digest": "t" * 64},
        }

    monkeypatch.setattr(sources.stress, "verify_stress", mock_stress)

    req_path = tmp_path / "req.yaml"
    req_path.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "level": "a1",
                "words": [
                    {
                        "lemma": "synthetic",
                        "pos": "noun",
                        "want": "new",
                        "entry": {"source": "vesum", "entry_id": 10},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = words.build_words(
            "a1",
            req_path,
            evidence_dir=tmp_path,
            sources_instance=api,
            dry_run=True,
        )

    word = res["store"]["words"][0]
    form_naz = next(f for f in word["forms"] if f["form"] == "synthetic-a")
    form_rod = next(f for f in word["forms"] if f["form"] == "synthetic-b")
    assert form_naz["stress_source"] == "trie"
    assert form_naz["stressed"] == "synthetic-a-stressed"
    assert form_rod["stress_source"] == "pending"
    assert "stressed" not in form_rod


@pytest.mark.parametrize("marker", sorted(codes.EXCLUDING_MARKERS))
def test_excluding_markers_flag_learner_false(synthetic_vesum, synthetic_sources, tmp_path, monkeypatch, marker):
    monkeypatch.setattr(
        sources.stress,
        "verify_stress",
        lambda w, **kw: {
            "status": "ok",
            "matches": [
                {
                    "stressed_form": f"{w}-stressed",
                    "unstressed_form": w,
                    "vowel_index": 0,
                    "vowel_indices": [0],
                    "vesum": None,
                    "required_tags": [],
                    "override_applied": False,
                }
            ],
            "source": {"digest": "t" * 64},
        },
    )

    with sqlite3.connect(synthetic_vesum) as conn:
        conn.execute("DELETE FROM forms_all")
        conn.execute("DELETE FROM form_markers")
        conn.execute("INSERT INTO forms_all VALUES (1, 10, 'form-m', 'marked', 'noun', 'noun:f:v_naz', '', '')")
        conn.execute("INSERT INTO form_markers VALUES (1, ?, 'test', 'test')", (marker,))

    req_path = tmp_path / "req.yaml"
    req_path.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "level": "a1",
                "words": [{"lemma": "marked", "pos": "noun", "want": "new"}],
            }
        ),
        encoding="utf-8",
    )

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = words.build_words(
            "a1",
            req_path,
            evidence_dir=tmp_path,
            sources_instance=api,
            dry_run=True,
        )

    word = res["store"]["words"][0]
    assert len(word["forms"]) == 1
    assert word["forms"][0]["learner"] is False
    assert any((m["marker"] if isinstance(m, dict) else m) == marker for m in word["forms"][0]["markers"])


def test_gloss_absent_when_no_row_and_present_when_matching(synthetic_vesum, synthetic_sources, tmp_path, monkeypatch):
    monkeypatch.setattr(
        sources.stress,
        "verify_stress",
        lambda w, **kw: {
            "status": "ok",
            "matches": [
                {
                    "stressed_form": f"{w}-stressed",
                    "unstressed_form": w,
                    "vowel_index": 0,
                    "vowel_indices": [0],
                    "vesum": None,
                    "required_tags": [],
                    "override_applied": False,
                }
            ],
            "source": {"digest": "t" * 64},
        },
    )

    req_path = tmp_path / "req.yaml"
    req_path.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "level": "a1",
                "words": [
                    {
                        "lemma": "synthetic",
                        "pos": "verb",
                        "want": "new",
                        "entry": {"source": "vesum", "entry_id": 30},
                    },
                    {
                        "lemma": "synthetic-no-gloss",
                        "pos": "noun",
                        "want": "new",
                        "entry": {"source": "vesum", "entry_id": 40},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    with sqlite3.connect(synthetic_vesum) as conn:
        conn.execute(
            "INSERT INTO forms_all VALUES (5, 40, 'synthetic-ng', 'synthetic-no-gloss', 'noun', 'noun:m:v_naz', '', '')"
        )

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = words.build_words(
            "a1",
            req_path,
            evidence_dir=tmp_path,
            sources_instance=api,
            dry_run=True,
        )

    w_verb = next(w for w in res["store"]["words"] if w["lemma"] == "synthetic")
    w_none = next(w for w in res["store"]["words"] if w["lemma"] == "synthetic-no-gloss")

    assert w_verb["gloss_en"] == "wrong POS"
    assert w_verb["gloss_source"]["table"] == "dmklinger_uk_en"
    assert w_verb["gloss_source"]["id"] == 3
    with sqlite3.connect(synthetic_sources) as conn:
        conn.row_factory = sqlite3.Row
        row = dict(conn.execute("SELECT * FROM dmklinger_uk_en WHERE id = 3").fetchone())
    assert w_verb["gloss_source"]["row_sha256"] == sources.row_digest(row)

    assert "gloss_en" not in w_none
    assert "gloss_source" not in w_none


def test_determinism_two_builds_byte_identical(synthetic_vesum, synthetic_sources, tmp_path, monkeypatch):
    monkeypatch.setattr(
        sources.stress,
        "verify_stress",
        lambda w, **kw: {
            "status": "ok",
            "matches": [
                {
                    "stressed_form": f"{w}-stressed",
                    "unstressed_form": w,
                    "vowel_index": 0,
                    "vowel_indices": [0],
                    "vesum": None,
                    "required_tags": [],
                    "override_applied": False,
                }
            ],
            "source": {"digest": "t" * 64},
        },
    )

    req_path = tmp_path / "req.yaml"
    req_path.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "level": "a1",
                "words": [
                    {
                        "lemma": "synthetic",
                        "pos": "noun",
                        "want": "new",
                        "entry": {"source": "vesum", "entry_id": 10},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    dir1 = tmp_path / "run1"
    dir2 = tmp_path / "run2"

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        words.build_words(
            "a1",
            req_path,
            evidence_dir=dir1,
            sources_instance=api,
            dry_run=False,
            stamp=False,
            mcp_commit="f" * 40,
        )
        words.build_words(
            "a1",
            req_path,
            evidence_dir=dir2,
            sources_instance=api,
            dry_run=False,
            stamp=False,
            mcp_commit="f" * 40,
        )

    f1 = (dir1 / "_words.yaml").read_bytes()
    f2 = (dir2 / "_words.yaml").read_bytes()
    l1 = (dir1 / "_words.yaml.lock").read_bytes()
    l2 = (dir2 / "_words.yaml.lock").read_bytes()

    assert f1 == f2
    assert l1 == l2
    assert lock.check(dir1 / "_words.yaml")
    assert lock.check(dir2 / "_words.yaml")


def test_id_never_reused_after_tombstone(synthetic_vesum, synthetic_sources, tmp_path, monkeypatch):
    monkeypatch.setattr(
        sources.stress,
        "verify_stress",
        lambda w, **kw: {
            "status": "ok",
            "matches": [
                {
                    "stressed_form": f"{w}-stressed",
                    "unstressed_form": w,
                    "vowel_index": 0,
                    "vowel_indices": [0],
                    "vesum": None,
                    "required_tags": [],
                    "override_applied": False,
                }
            ],
            "source": {"digest": "t" * 64},
        },
    )

    # Initial build allocating W-001
    req1 = tmp_path / "req1.yaml"
    req1.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "level": "a1",
                "words": [
                    {
                        "lemma": "synthetic",
                        "pos": "noun",
                        "want": "new",
                        "entry": {"source": "vesum", "entry_id": 10},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        words.build_words("a1", req1, evidence_dir=tmp_path, sources_instance=api)

    reg_records = registry.load(tmp_path / "_words.registry.yaml")
    assert reg_records[0]["id"] == "W-001"

    # Retire W-001
    registry.retire(reg_records, "W-001")
    registry.write(tmp_path / "_words.registry.yaml", reg_records)

    # Now allocate another word
    req2 = tmp_path / "req2.yaml"
    req2.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "level": "a1",
                "words": [
                    {
                        "lemma": "synthetic",
                        "pos": "verb",
                        "want": "new",
                        "entry": {"source": "vesum", "entry_id": 30},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = words.build_words("a1", req2, evidence_dir=tmp_path, sources_instance=api)

    assert res["store"]["words"][0]["id"] == "W-002"


def test_file_and_directory_permissions(synthetic_vesum, synthetic_sources, tmp_path, monkeypatch):
    monkeypatch.setattr(
        sources.stress,
        "verify_stress",
        lambda w, **kw: {
            "status": "ok",
            "matches": [
                {
                    "stressed_form": f"{w}-stressed",
                    "unstressed_form": w,
                    "vowel_index": 0,
                    "vowel_indices": [0],
                    "vesum": None,
                    "required_tags": [],
                    "override_applied": False,
                }
            ],
            "source": {"digest": "t" * 64},
        },
    )

    req = tmp_path / "req.yaml"
    req.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "level": "a1",
                "words": [
                    {
                        "lemma": "synthetic",
                        "pos": "noun",
                        "want": "new",
                        "entry": {"source": "vesum", "entry_id": 10},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    out_dir = tmp_path / "nested" / "ev"
    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        words.build_words("a1", req, evidence_dir=out_dir, sources_instance=api)

    assert stat.S_IMODE(out_dir.stat().st_mode) == 0o755
    store_file = out_dir / "_words.yaml"
    lock_file = out_dir / "_words.yaml.lock"
    assert stat.S_IMODE(store_file.stat().st_mode) == 0o644
    assert stat.S_IMODE(lock_file.stat().st_mode) == 0o644


OK_ORACLE = {
    "status": "ok",
    "matches": [
        {
            "stressed_form": "synthetic-stressed",
            "unstressed_form": "synthetic",
            "vowel_index": 0,
            "vowel_indices": [0],
            "vesum": None,
            "required_tags": [],
            "override_applied": False,
        }
    ],
    "source": {"digest": "t" * 64},
}


def _oracle(monkeypatch):
    monkeypatch.setattr(
        sources.stress,
        "verify_stress",
        lambda w, **kw: {**OK_ORACLE, "matches": [{**OK_ORACLE["matches"][0], "stressed_form": f"{w}-stressed"}]},
    )


def _request(tmp_path, words_list, name="req.yaml"):
    req_path = tmp_path / name
    req_path.write_text(yaml.safe_dump({"request_schema": 1, "level": "a1", "words": words_list}), encoding="utf-8")
    return req_path


SYNTHETIC_NOUN = {"lemma": "synthetic", "pos": "noun", "want": "new", "entry": {"source": "vesum", "entry_id": 10}}


def test_store_records_rows_v2_identities_and_aggregate(synthetic_vesum, synthetic_sources, tmp_path, monkeypatch):
    _oracle(monkeypatch)
    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = words.build_words("a1", _request(tmp_path, [SYNTHETIC_NOUN]), evidence_dir=tmp_path, sources_instance=api)
    store = res["store"]
    word = store["words"][0]
    with sqlite3.connect(synthetic_sources) as conn:
        conn.row_factory = sqlite3.Row
        gloss_row = dict(conn.execute("SELECT * FROM dmklinger_uk_en WHERE id = 1").fetchone())
        cefr_row = dict(conn.execute("SELECT * FROM puls_cefr WHERE id = 1").fetchone())
    assert word["gloss_source"] == {"table": "dmklinger_uk_en", "id": 1, "row_sha256": sources.row_digest(gloss_row)}
    assert word["cefr"] == {"level": "A1", "source": "puls", "row_id": 1, "row_sha256": sources.row_digest(cefr_row)}
    assert store["built_with"]["sources_db_scheme"] == "rows-v2"
    cited = words.cited_rows(word)
    # The morphology check may flag the synthetic lemma as a shadow and add heritage pairs; the
    # gloss and CEFR rows are always cited.
    assert {pair for pair in cited if not pair[0].startswith("heritage:")} == {
        ("dmklinger_uk_en:1", word["gloss_source"]["row_sha256"]),
        ("puls_cefr:1", word["cefr"]["row_sha256"]),
    }
    assert store["built_with"]["sources_db"] == sources.aggregate_digest(cited)
    assert res["snapshot"]["journal_mode"] == "delete"
    assert lock.check(tmp_path / "_words.yaml")


def test_allocated_at_build_is_the_request_read_set(synthetic_vesum, synthetic_sources, tmp_path, monkeypatch):
    _oracle(monkeypatch)
    req = _request(tmp_path, [SYNTHETIC_NOUN])

    def build(evidence_dir):
        with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
            words.build_words("a1", req, evidence_dir=evidence_dir, sources_instance=api, mcp_commit="f" * 40)
        return registry.load(evidence_dir / "_words.registry.yaml")

    first = build(tmp_path / "one")
    assert build(tmp_path / "two") == first  # deterministic for the same request and sources

    # An uncited candidate in the gloss batch changes (the second row is never copied):
    # the read set is different, so a fresh allocation records a different fingerprint …
    with sqlite3.connect(synthetic_sources) as conn:
        conn.execute("UPDATE dmklinger_uk_en SET text = 'uncited candidate edit' WHERE id = 2")
    third = build(tmp_path / "three")
    assert third[0]["allocated_at_build"] != first[0]["allocated_at_build"]

    # … while an existing ledger row is never rewritten by a later build.
    again = _request(tmp_path, [{**SYNTHETIC_NOUN, "want": "W-001"}], name="again.yaml")
    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        words.build_words("a1", again, evidence_dir=tmp_path / "one", sources_instance=api, mcp_commit="f" * 40)
    assert registry.load(tmp_path / "one" / "_words.registry.yaml") == first


def test_legacy_store_migrates_only_when_the_request_covers_all_active_ids(
    synthetic_vesum, synthetic_sources, tmp_path, monkeypatch
):
    _oracle(monkeypatch)
    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        words.build_words("a1", _request(tmp_path, [SYNTHETIC_NOUN]), evidence_dir=tmp_path, sources_instance=api)
    store_path = tmp_path / "_words.yaml"
    doc = yaml.safe_load(store_path.read_text(encoding="utf-8"))
    doc["built_with"].pop("sources_db_scheme")
    doc["built_with"]["sources_db"] = "b" * 64
    doc["words"][0]["gloss_source"].pop("row_sha256")
    doc["words"][0]["cefr"] = {"level": "A1", "source": "puls"}
    lock.write(store_path, lock.yaml_bytes(doc))
    assert words.store_scheme(doc) == "file-v1"

    with sqlite3.connect(synthetic_vesum) as conn:
        conn.execute(
            "INSERT INTO forms_all VALUES (5, 40, 'synthetic-ng', 'synthetic-other', 'noun', 'noun:m:v_naz', '', '')"
        )
    other = {"lemma": "synthetic-other", "pos": "noun", "want": "new", "entry": {"source": "vesum", "entry_id": 40}}

    partial = _request(tmp_path, [other], name="partial.yaml")
    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        with pytest.raises(ValueError, match=codes.INVALID_REQUEST) as excinfo:
            words.build_words("a1", partial, evidence_dir=tmp_path, sources_instance=api)
    assert "legacy store" in str(excinfo.value) and "W-001" in str(excinfo.value)

    full = _request(tmp_path, [{**SYNTHETIC_NOUN, "want": "W-001"}, other], name="full.yaml")
    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = words.build_words("a1", full, evidence_dir=tmp_path, sources_instance=api)
    assert res["store"]["built_with"]["sources_db_scheme"] == "rows-v2"
    assert all("row_sha256" in w["gloss_source"] for w in res["store"]["words"] if "gloss_source" in w)


def _shadow_everything(monkeypatch):
    from scripts.verification import check_ru_morph

    monkeypatch.setattr(
        check_ru_morph,
        "check_russian_patterns_batch",
        lambda requested, *, verified_words: {w: {"matches_russian": True, "confidence": 0.9} for w in requested},
    )


def test_heritage_hits_carry_the_identity_of_the_rows_they_were_read_from(
    synthetic_vesum, synthetic_sources, tmp_path, monkeypatch
):
    _oracle(monkeypatch)
    _shadow_everything(monkeypatch)
    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = words.build_words("a1", _request(tmp_path, [SYNTHETIC_NOUN]), evidence_dir=tmp_path, sources_instance=api)
    word = res["store"]["words"][0]
    assert word["shadow"]["russian_shadow"] is True
    hits = word["heritage"]
    assert hits and hits[0]["source_family"] == "style_guide"  # the synthetic style-guide row contains the lemma
    assert hits[0]["text"] == "synthetic note explanation text"
    assert all(sources.heritage_hit_digest(hit) == hit["row_sha256"] for hit in hits)
    assert ("heritage:synthetic:0", hits[0]["row_sha256"]) in words.cited_rows(word)
    words.validate_store_data(res["store"])
