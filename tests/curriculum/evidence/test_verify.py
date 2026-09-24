"""Tests for scripts.curriculum.evidence.verify (words-verify)."""

import sqlite3

import pytest
import yaml

from scripts.curriculum.evidence import codes, lock, registry, sources, verify, words


@pytest.fixture
def clean_store(synthetic_vesum, synthetic_sources, tmp_path, monkeypatch):
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

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        words.build_words(
            "a1",
            req,
            evidence_dir=tmp_path,
            sources_instance=api,
            mcp_commit="a" * 40,
        )

    return tmp_path


def test_verify_clean_store_passes(clean_store, synthetic_vesum, synthetic_sources, monkeypatch):
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

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = verify.verify_words_store("a1", evidence_dir=clean_store, sources_instance=api)

    assert res["status"] == "ok"
    assert res["errors"] == []
    assert res["warnings"] == []


def test_verify_fails_on_lock_mismatch(clean_store, synthetic_vesum, synthetic_sources):
    store_file = clean_store / "_words.yaml"
    store_file.write_text("corrupted content", encoding="utf-8")

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = verify.verify_words_store("a1", evidence_dir=clean_store, sources_instance=api)

    assert res["status"] == "failed"
    assert any(codes.LOCK_MISMATCH in err for err in res["errors"])


def test_verify_fails_on_registry_mismatch(clean_store, synthetic_vesum, synthetic_sources):
    reg_file = clean_store / "_words.registry.yaml"
    records = registry.load(reg_file)
    records.append(
        {
            "id": "W-099",
            "lemma": "extra",
            "pos": "noun",
            "entry": {"source": "vesum", "entry_id": 99},
            "allocated_at_build": "extra",
        }
    )
    lock.write(reg_file, lock.yaml_bytes(records))

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = verify.verify_words_store("a1", evidence_dir=clean_store, sources_instance=api)

    assert res["status"] == "failed"
    assert any(codes.REGISTRY_MISMATCH in err for err in res["errors"])


def test_verify_fails_on_form_mismatch(clean_store, synthetic_vesum, synthetic_sources, monkeypatch):
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

    # Delete synthetic-b from VESUM
    with sqlite3.connect(synthetic_vesum) as conn:
        conn.execute("DELETE FROM forms_all WHERE word_form = 'synthetic-b'")

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = verify.verify_words_store("a1", evidence_dir=clean_store, sources_instance=api)

    assert res["status"] == "failed"
    assert any(codes.FORM_MISMATCH in err for err in res["errors"])


def test_verify_fails_on_learner_marker_violation(clean_store, synthetic_vesum, synthetic_sources, monkeypatch):
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

    # In store, set learner: true on synthetic-b (which has marker 'alt' in VESUM)
    store_file = clean_store / "_words.yaml"
    doc = yaml.safe_load(store_file.read_text("utf-8"))
    for f in doc["words"][0]["forms"]:
        if f["form"] == "synthetic-b":
            f["learner"] = True
    lock.write(store_file, lock.yaml_bytes(doc))

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = verify.verify_words_store("a1", evidence_dir=clean_store, sources_instance=api)

    assert res["status"] == "failed"
    assert any(codes.LEARNER_MARKER in err for err in res["errors"])


def test_verify_fails_on_unchecked_ulif_stress(clean_store, synthetic_vesum, synthetic_sources, monkeypatch):
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

    store_file = clean_store / "_words.yaml"
    doc = yaml.safe_load(store_file.read_text("utf-8"))
    doc["words"][0]["forms"][0]["stress_source"] = "ulif"
    lock.write(store_file, lock.yaml_bytes(doc))

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = verify.verify_words_store("a1", evidence_dir=clean_store, sources_instance=api)

    assert res["status"] == "failed"
    assert any(codes.UNCHECKED_ULIF in err for err in res["errors"])


def test_verify_unresolved_cited_fails_and_uncited_passes(synthetic_vesum, synthetic_sources, tmp_path, monkeypatch):
    req = tmp_path / "req.yaml"
    req.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "level": "a1",
                "words": [{"lemma": "synthetic", "pos": "noun", "want": "new"}],
            }
        ),
        encoding="utf-8",
    )

    plans_dir = tmp_path / "plans"
    plans_dir.mkdir()

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        words.build_words(
            "a1",
            req,
            evidence_dir=tmp_path,
            plans_dir=plans_dir,
            sources_instance=api,
        )

    # When no plan cites W-001: passes
    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = verify.verify_words_store(
            "a1",
            evidence_dir=tmp_path,
            plans_dir=plans_dir,
            sources_instance=api,
        )

    assert res["status"] == "ok"
    assert res["unresolved_uncited_count"] == 1

    # Now add a plan citing W-001
    (plans_dir / "lesson-01.yaml").write_text("uses: [W-001]", encoding="utf-8")

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = verify.verify_words_store(
            "a1",
            evidence_dir=tmp_path,
            plans_dir=plans_dir,
            sources_instance=api,
        )

    assert res["status"] == "failed"
    assert any(codes.UNRESOLVED_CITED in err for err in res["errors"])


def test_verify_stress_mismatch_without_source_change(clean_store, synthetic_vesum, synthetic_sources, monkeypatch):
    # Oracle returns different stress now, but source hashes are unchanged
    monkeypatch.setattr(
        sources.stress,
        "verify_stress",
        lambda w, **kw: {
            "status": "ok",
            "matches": [
                {
                    "stressed_form": f"{w}-NEW-STRESS",
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

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = verify.verify_words_store("a1", evidence_dir=clean_store, sources_instance=api)

    assert res["status"] == "failed"
    assert any(codes.STRESS_MISMATCH in err for err in res["errors"])


def test_verify_source_changed_strict_vs_nonstrict(clean_store, synthetic_vesum, synthetic_sources, monkeypatch):
    # Change trie digest so source_version_changed becomes True
    monkeypatch.setattr(
        sources.stress,
        "source_info",
        lambda: {"digest": "x" * 64, "path": "mock"},
    )
    monkeypatch.setattr(
        sources.stress,
        "verify_stress",
        lambda w, **kw: {
            "status": "ok",
            "matches": [
                {
                    "stressed_form": f"{w}-NEW-STRESS",
                    "unstressed_form": w,
                    "vowel_index": 0,
                    "vowel_indices": [0],
                    "vesum": None,
                    "required_tags": [],
                    "override_applied": False,
                }
            ],
            "source": {"digest": "x" * 64},
        },
    )

    # Non-strict: warning and status == "warning", not failed!
    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res_nonstrict = verify.verify_words_store("a1", evidence_dir=clean_store, sources_instance=api, strict=False)

    assert res_nonstrict["status"] == "warning"
    assert res_nonstrict["errors"] == []
    assert any(codes.SOURCE_CHANGED in w for w in res_nonstrict["warnings"])

    # Strict: fails with error!
    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res_strict = verify.verify_words_store("a1", evidence_dir=clean_store, sources_instance=api, strict=True)

    assert res_strict["status"] == "failed"
    assert any(codes.SOURCE_CHANGED in err for err in res_strict["errors"])


def test_verify_fails_on_missing_paradigm_forms(clean_store, synthetic_vesum, synthetic_sources):
    store_path = clean_store / "_words.yaml"
    data = yaml.safe_load(store_path.read_text(encoding="utf-8"))
    data["words"][0]["forms"] = []
    store_bytes = lock.yaml_bytes(data)
    lock.write(store_path, store_bytes)

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = verify.verify_words_store("a1", evidence_dir=clean_store, sources_instance=api, strict=True)

    assert res["status"] == "failed"
    assert any(codes.FORM_MISMATCH in err for err in res["errors"])


def test_verify_fails_on_unsupported_gloss(clean_store, synthetic_vesum, synthetic_sources):
    store_path = clean_store / "_words.yaml"
    data = yaml.safe_load(store_path.read_text(encoding="utf-8"))
    data["words"][0]["gloss_en"] = "invented gloss"
    data["words"][0]["gloss_source"] = {"table": "dmklinger_uk_en", "id": 99999}
    store_bytes = lock.yaml_bytes(data)
    lock.write(store_path, store_bytes)

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = verify.verify_words_store("a1", evidence_dir=clean_store, sources_instance=api, strict=True)

    assert res["status"] == "failed"
    assert any(codes.GLOSS_MISMATCH in err for err in res["errors"])


def test_verify_fails_on_unsupported_cefr(clean_store, synthetic_vesum, synthetic_sources):
    store_path = clean_store / "_words.yaml"
    data = yaml.safe_load(store_path.read_text(encoding="utf-8"))
    data["words"][0]["cefr"] = {"level": "C2", "source": "puls"}
    store_bytes = lock.yaml_bytes(data)
    lock.write(store_path, store_bytes)

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = verify.verify_words_store("a1", evidence_dir=clean_store, sources_instance=api, strict=True)

    assert res["status"] == "failed"
    assert any(codes.CEFR_MISMATCH in err for err in res["errors"])


def test_verify_fails_on_missing_ulif_homonym(tmp_path, synthetic_vesum, synthetic_sources, monkeypatch):
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

    # ULIF homonym 2 exists at build time, so the store resolves legitimately.
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
        words.build_words("a1", req_path, evidence_dir=tmp_path, sources_instance=api, dry_run=False)

    # The ULIF homonym disappears from the source; the stored key must no longer verify.
    with sqlite3.connect(synthetic_sources) as conn:
        conn.execute("DELETE FROM ulif_dictua_entries WHERE id = 15")

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = verify.verify_words_store("a1", evidence_dir=tmp_path, sources_instance=api, strict=True)

    assert res["status"] == "failed"
    assert any(codes.FORM_MISMATCH in err for err in res["errors"])


def test_verify_checked_ulif_stress_passes_and_mismatch_fails(tmp_path, synthetic_vesum, synthetic_sources):
    import json

    # Setup checked ULIF entry with paradigm section
    with sqlite3.connect(synthetic_sources) as conn:
        conn.execute(
            "INSERT INTO ulif_dictua_sections VALUES (10, 2, 'paradigm', 0, '', ?)",
            (json.dumps({"synthetic-a": "synthetic-a-ulif-stressed"}),),
        )

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
                        "entry": {"source": "vesum", "entry_id": 10},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        words.build_words("a1", req_path, evidence_dir=tmp_path, sources_instance=api, dry_run=False)

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = verify.verify_words_store("a1", evidence_dir=tmp_path, sources_instance=api, strict=True)
    assert res["status"] == "ok"

    # Now tamper with stored stress to wrong stress
    store_path = tmp_path / "_words.yaml"
    data = yaml.safe_load(store_path.read_text(encoding="utf-8"))
    data["words"][0]["forms"][0]["stressed"] = "synthetic-a-wrong"
    lock.write(store_path, lock.yaml_bytes(data))

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res_fail = verify.verify_words_store("a1", evidence_dir=tmp_path, sources_instance=api, strict=True)
    assert res_fail["status"] == "failed"
    assert any(codes.STRESS_MISMATCH in err for err in res_fail["errors"])


def _oracle(monkeypatch, suffix="-stressed"):
    monkeypatch.setattr(
        sources.stress,
        "verify_stress",
        lambda w, **kw: {
            "status": "ok",
            "matches": [
                {
                    "stressed_form": f"{w}{suffix}",
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


def _verify(synthetic_sources, synthetic_vesum, evidence_dir, *, strict):
    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        return verify.verify_words_store("a1", evidence_dir=evidence_dir, sources_instance=api, strict=strict)


def _checked_ulif_store(tmp_path, synthetic_vesum, synthetic_sources):
    import json

    with sqlite3.connect(synthetic_sources) as conn:
        conn.execute(
            "INSERT INTO ulif_dictua_sections VALUES (10, 2, 'paradigm', 0, '', ?)",
            (json.dumps({"synthetic-a": "synthetic-a-ulif-stressed"}),),
        )
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
                        "entry": {"source": "vesum", "entry_id": 10},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = words.build_words("a1", req_path, evidence_dir=tmp_path, sources_instance=api)
    return res["store"]


def test_verify_ulif_row_drift_is_source_changed_not_stress_mismatch(tmp_path, synthetic_vesum, synthetic_sources):
    """ULIF stress provenance: the paradigm payload the stress was copied from is part of ulif.row_sha256."""
    import json

    store = _checked_ulif_store(tmp_path, synthetic_vesum, synthetic_sources)
    word = store["words"][0]
    assert word["forms"][0]["stress_source"] == "ulif"
    assert ("ulif_dictua_entries:synthetic-checked:1", word["ulif"]["row_sha256"]) in words.cited_rows(word)
    assert _verify(synthetic_sources, synthetic_vesum, tmp_path, strict=True)["status"] == "ok"

    with sqlite3.connect(synthetic_sources) as conn:
        conn.execute(
            "UPDATE ulif_dictua_sections SET payload_json = ? WHERE id = 10",
            (json.dumps({"synthetic-a": "synthetic-A-restressed"}),),
        )

    res = _verify(synthetic_sources, synthetic_vesum, tmp_path, strict=False)
    assert res["status"] == "warning"
    assert res["errors"] == []
    assert any(codes.SOURCE_CHANGED in w and "ulif of W-001" in w for w in res["warnings"])
    assert any(codes.SOURCE_CHANGED in w and "synthetic-a-ulif-stressed" in w for w in res["warnings"])
    assert res["cited_rows_drifted_words"] == 1
    assert res["source_version_changed"] is False  # VESUM and the trie did not move; the cited row did

    res = _verify(synthetic_sources, synthetic_vesum, tmp_path, strict=True)
    assert res["status"] == "failed"
    assert all(codes.STRESS_MISMATCH not in e for e in res["errors"])
    assert any(codes.SOURCE_CHANGED in e for e in res["errors"])


def test_verify_gloss_row_metadata_drift_is_never_silent(clean_store, synthetic_vesum, synthetic_sources, monkeypatch):
    _oracle(monkeypatch)
    with sqlite3.connect(synthetic_sources) as conn:
        conn.execute("UPDATE dmklinger_uk_en SET source = 'reingested' WHERE id = 1")  # copied value untouched
    res = _verify(synthetic_sources, synthetic_vesum, clean_store, strict=False)
    assert res["status"] == "warning"
    assert res["errors"] == []
    assert any(codes.SOURCE_CHANGED in w and "gloss_source of W-001" in w for w in res["warnings"])
    res = _verify(synthetic_sources, synthetic_vesum, clean_store, strict=True)
    assert res["status"] == "failed"
    assert not any(codes.GLOSS_MISMATCH in e for e in res["errors"])

    with sqlite3.connect(synthetic_sources) as conn:
        conn.execute("UPDATE puls_cefr SET level = 'B2' WHERE id = 1")  # copied value changes: error in every mode
    res = _verify(synthetic_sources, synthetic_vesum, clean_store, strict=False)
    assert res["status"] == "failed"
    assert any(codes.CEFR_MISMATCH in e for e in res["errors"])
    assert any(codes.SOURCE_CHANGED in w and "cefr of W-001" in w for w in res["warnings"])


def test_verify_legacy_store_and_tampered_identities(clean_store, synthetic_vesum, synthetic_sources, monkeypatch):
    _oracle(monkeypatch)
    store_path = clean_store / "_words.yaml"
    built = yaml.safe_load(store_path.read_text(encoding="utf-8"))

    legacy = yaml.safe_load(lock.yaml_bytes(built))
    legacy["built_with"].pop("sources_db_scheme")
    legacy["built_with"]["sources_db"] = "b" * 64
    legacy["words"][0]["gloss_source"].pop("row_sha256")
    legacy["words"][0]["cefr"] = {"level": "A1", "source": "puls"}
    lock.write(store_path, lock.yaml_bytes(legacy))
    res = _verify(synthetic_sources, synthetic_vesum, clean_store, strict=False)
    assert (res["status"], res["errors"], res["sources_db_scheme"]) == ("warning", [], "file-v1")
    assert any(codes.LEGACY_IDENTITY in w for w in res["warnings"])
    res = _verify(synthetic_sources, synthetic_vesum, clean_store, strict=True)
    assert res["status"] == "failed"
    assert any(codes.LEGACY_IDENTITY in e for e in res["errors"])

    missing = yaml.safe_load(lock.yaml_bytes(built))
    missing["words"][0]["gloss_source"].pop("row_sha256")
    lock.write(store_path, lock.yaml_bytes(missing))
    res = _verify(synthetic_sources, synthetic_vesum, clean_store, strict=False)
    assert res["status"] == "failed"
    assert any(codes.FORM_MISMATCH in e and "no row_sha256" in e for e in res["errors"])
    assert any(codes.LOCK_MISMATCH in e and "aggregate" in e for e in res["errors"])

    edited = yaml.safe_load(lock.yaml_bytes(built))
    edited["words"][0]["cefr"]["row_sha256"] = "0" * 64
    lock.write(store_path, lock.yaml_bytes(edited))
    res = _verify(synthetic_sources, synthetic_vesum, clean_store, strict=False)
    assert res["status"] == "failed"
    assert any(codes.LOCK_MISMATCH in e and "aggregate" in e for e in res["errors"])


def test_verify_heritage_source_change(tmp_path, synthetic_vesum, synthetic_sources, monkeypatch):
    from scripts.verification import check_ru_morph

    _oracle(monkeypatch)
    monkeypatch.setattr(
        check_ru_morph,
        "check_russian_patterns_batch",
        lambda requested, *, verified_words: {w: {"matches_russian": True, "confidence": 0.9} for w in requested},
    )
    req = tmp_path / "req.yaml"
    req.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "level": "a1",
                "words": [
                    {"lemma": "synthetic", "pos": "noun", "want": "new", "entry": {"source": "vesum", "entry_id": 10}}
                ],
            }
        ),
        encoding="utf-8",
    )
    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = words.build_words("a1", req, evidence_dir=tmp_path, sources_instance=api)
    assert res["store"]["words"][0]["heritage"][0]["source_family"] == "style_guide"
    assert _verify(synthetic_sources, synthetic_vesum, tmp_path, strict=True)["status"] == "ok"

    with sqlite3.connect(synthetic_sources) as conn:
        conn.execute("UPDATE style_guide SET text = 'rewritten heritage explanation' WHERE id = 1")
    res = _verify(synthetic_sources, synthetic_vesum, tmp_path, strict=False)
    assert res["status"] == "warning"
    assert res["errors"] == []
    assert any(codes.SOURCE_CHANGED in w and "heritage of W-001" in w for w in res["warnings"])
    res = _verify(synthetic_sources, synthetic_vesum, tmp_path, strict=True)
    assert res["status"] == "failed"
    assert any(codes.SOURCE_CHANGED in e and "heritage of W-001" in e for e in res["errors"])

    # A hand-edited hit no longer matches its own recorded identity.
    store_path = tmp_path / "_words.yaml"
    doc = yaml.safe_load(store_path.read_text(encoding="utf-8"))
    doc["words"][0]["heritage"][0]["text"] = "typed by hand"
    lock.write(store_path, lock.yaml_bytes(doc))
    res = _verify(synthetic_sources, synthetic_vesum, tmp_path, strict=False)
    assert res["status"] == "failed"
    assert any(codes.LOCK_MISMATCH in e and "heritage[0]" in e for e in res["errors"])
