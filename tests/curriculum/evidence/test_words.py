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
    assert word["ulif"] == {"source": "ulif", "key": ["synthetic-original", 1]}


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
    assert w_verb["gloss_source"] == {"table": "dmklinger_uk_en", "id": 3}

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
