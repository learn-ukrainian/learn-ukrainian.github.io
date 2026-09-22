"""Tests for fresh build engine Part E2 preflight verification and gap reports (#8431 §4, §7 row 0)."""

from __future__ import annotations

import stat

import pytest
import yaml

from scripts.build.fresh.preflight import preflight_lesson
from scripts.curriculum.evidence import lock


@pytest.fixture
def clean_word_store():
    return {
        "words": [
            {
                "id": "W-001",
                "lemma": "слово",
                "pos": "noun",
                "forms": [
                    {
                        "form": "слово",
                        "tags": "noun:inanim:n:v_naz",
                        "stressed": "сло́во",
                        "stress_source": "vesum",
                        "learner": True,
                    },
                    {
                        "form": "слова",
                        "tags": "noun:inanim:n:v_rod",
                        "stressed": "сло́ва",
                        "stress_source": "vesum",
                        "learner": True,
                    },
                ],
            }
        ]
    }


@pytest.fixture
def clean_pack():
    return {
        "texts": [
            {
                "id": "T-001",
                "kind": "culture",
                "source": {"table": "textbooks", "chunk_id": "c1"},
                "text": "attested culture text",
            },
            {
                "id": "T-002",
                "kind": "quote",
                "source": {"table": "textbooks", "chunk_id": "c2"},
                "text": "attested quote text",
            },
        ],
        "examples": [
            {
                "id": "EX-001",
                "kind": "example",
                "source": {"table": "textbooks", "chunk_id": "c3"},
                "example": "attested example",
            }
        ],
        "errors": [
            {
                "id": "E-001",
                "kind": "error",
                "incorrect": "bad",
                "correct": "good",
            }
        ],
        "videos": [
            {
                "id": "V-001",
                "kind": "video",
                "url": "https://example.com/v1",
            }
        ],
    }


def test_preflight_example_need(clean_word_store, clean_pack):
    """Example need passes when EX- is cited and present; fails when missing."""
    plan_entry = {
        "steps": [{"id": "s1", "needs": ["example"], "ref": "EX-001"}],
        "inventory": {"vocabulary": {"core": []}},
    }
    res = preflight_lesson(plan_entry, pack=clean_pack, word_store=clean_word_store)
    assert res.passed is True
    assert res.gaps == []

    # Missing EX-
    plan_entry_bad = {
        "steps": [{"id": "s1", "needs": ["example"], "ref": "EX-999"}],
        "inventory": {"vocabulary": {"core": []}},
    }
    res_bad = preflight_lesson(plan_entry_bad, pack=clean_pack, word_store=clean_word_store)
    assert res_bad.passed is False
    assert any(g.need == "example" and g.step == "s1" for g in res_bad.gaps)


def test_preflight_quote_need_publication_right_gap(clean_word_store, clean_pack):
    """WP 21 is not on main: every quote need is a publication_right gap, never a pass."""
    plan_entry = {
        "steps": [{"id": "s1", "needs": ["quote"], "explains": ["T-002"]}],
        "inventory": {"vocabulary": {"core": []}},
    }
    res = preflight_lesson(plan_entry, pack=clean_pack, word_store=clean_word_store)
    assert res.passed is False
    assert len(res.gaps) == 1
    assert res.gaps[0].step == "s1"
    assert res.gaps[0].need == "publication_right"


def test_preflight_quote_with_publish_allowed_true_still_produces_gap(clean_word_store):
    """Finding 2: until WP 21 lands, a quote need is ALWAYS a publication_right gap, whatever pack says."""
    pack_with_allowed = {
        "texts": [
            {
                "id": "T-002",
                "kind": "quote",
                "source": {
                    "table": "textbooks",
                    "chunk_id": "c2",
                    "publish": {"allowed": True, "limit_chars": 500, "attribution": "Source"},
                },
                "text": "attested quote text",
            },
        ],
    }
    plan_entry = {
        "steps": [{"id": "s1", "needs": ["quote"], "explains": ["T-002"]}],
        "inventory": {"vocabulary": {"core": []}},
    }
    res = preflight_lesson(plan_entry, pack=pack_with_allowed, word_store=clean_word_store)
    assert res.passed is False
    assert any(g.need == "publication_right" for g in res.gaps)


def test_preflight_record_kind_mismatch_fails(clean_word_store, clean_pack):
    """Finding 3: record kind must match _NEED_KIND_MAP (e.g. quote cannot be satisfied by culture record)."""
    # T-001 has kind 'culture'; step needs 'quote'
    plan_entry_quote_mismatch = {
        "steps": [{"id": "s1", "needs": ["quote"], "explains": ["T-001"]}],
        "inventory": {"vocabulary": {"core": []}},
    }
    res1 = preflight_lesson(plan_entry_quote_mismatch, pack=clean_pack, word_store=clean_word_store)
    assert res1.passed is False
    assert any("kind 'culture', expected 'quote'" in g.detail for g in res1.gaps)

    # T-002 has kind 'quote'; step needs 'culture'
    plan_entry_culture_mismatch = {
        "steps": [{"id": "s1", "needs": ["culture"], "explains": ["T-002"]}],
        "inventory": {"vocabulary": {"core": []}},
    }
    res2 = preflight_lesson(plan_entry_culture_mismatch, pack=clean_pack, word_store=clean_word_store)
    assert res2.passed is False
    assert any("kind 'quote', expected 'culture'" in g.detail for g in res2.gaps)


def test_preflight_missing_pack_or_words_fails_closed(clean_word_store, clean_pack):
    """Finding 3: a missing pack or word store fails closed."""
    plan_entry = {"steps": [{"id": "s1"}], "inventory": {"vocabulary": {"core": []}}}
    res_no_pack = preflight_lesson(plan_entry, pack=None, word_store=clean_word_store)
    assert res_no_pack.passed is False
    assert any(g.need == "pack_missing" for g in res_no_pack.gaps)

    res_no_words = preflight_lesson(plan_entry, pack=clean_pack, word_store=None)
    assert res_no_words.passed is False
    assert any(g.need == "words_missing" for g in res_no_words.gaps)


def test_preflight_lock_verification(tmp_path, clean_word_store, clean_pack):
    """Finding 3: pack and word store lock verification via lock.check."""
    pack_file = tmp_path / "mod.yaml"
    pack_file.write_text(yaml.safe_dump(clean_pack), encoding="utf-8")
    words_file = tmp_path / "_words.yaml"
    words_file.write_text(yaml.safe_dump(clean_word_store), encoding="utf-8")

    # Missing lock sidecars
    plan_entry = {"steps": [{"id": "s1"}], "inventory": {"vocabulary": {"core": []}}}
    res = preflight_lesson(
        plan_entry,
        pack=clean_pack,
        word_store=clean_word_store,
        pack_path=pack_file,
        words_path=words_file,
    )
    assert res.passed is False
    assert any(g.need in ("pack_lock", "words_lock") for g in res.gaps)

    # Now create valid lock sidecars
    lock.write(pack_file)
    lock.write(words_file)
    res_locked = preflight_lesson(
        plan_entry,
        pack=clean_pack,
        word_store=clean_word_store,
        pack_path=pack_file,
        words_path=words_file,
    )
    assert res_locked.passed is True


def test_preflight_error_need(clean_word_store, clean_pack):
    """Error need passes when E- is present in pack; fails when missing."""
    plan_entry = {
        "steps": [{"id": "s1", "needs": ["error"], "practice": ["a1"]}],
        "activities": [{"id": "a1", "type": "error-correction", "error_refs": ["E-001"]}],
        "inventory": {"vocabulary": {"core": []}},
    }
    res = preflight_lesson(plan_entry, pack=clean_pack, word_store=clean_word_store)
    assert res.passed is True

    plan_entry_bad = {
        "steps": [{"id": "s1", "needs": ["error"], "practice": ["a1"]}],
        "activities": [{"id": "a1", "type": "error-correction", "error_refs": ["E-999"]}],
        "inventory": {"vocabulary": {"core": []}},
    }
    res_bad = preflight_lesson(plan_entry_bad, pack=clean_pack, word_store=clean_word_store)
    assert res_bad.passed is False
    assert any(g.need == "error" for g in res_bad.gaps)


def test_preflight_video_need(clean_word_store, clean_pack):
    """Video need passes when V- is present; fails when missing."""
    plan_entry = {
        "steps": [{"id": "s1", "needs": ["video"], "ref": "V-001"}],
        "inventory": {"vocabulary": {"core": []}},
    }
    res = preflight_lesson(plan_entry, pack=clean_pack, word_store=clean_word_store)
    assert res.passed is True

    plan_entry_bad = {
        "steps": [{"id": "s1", "needs": ["video"], "ref": "V-999"}],
        "inventory": {"vocabulary": {"core": []}},
    }
    res_bad = preflight_lesson(plan_entry_bad, pack=clean_pack, word_store=clean_word_store)
    assert res_bad.passed is False
    assert any(g.need == "video" for g in res_bad.gaps)


def test_preflight_culture_need(clean_word_store, clean_pack):
    """Culture need passes when T- is present with kind 'culture'; fails when missing."""
    plan_entry = {
        "steps": [{"id": "s1", "needs": ["culture"], "explains": ["T-001"]}],
        "inventory": {"vocabulary": {"core": []}},
    }
    res = preflight_lesson(plan_entry, pack=clean_pack, word_store=clean_word_store)
    assert res.passed is True

    plan_entry_bad = {
        "steps": [{"id": "s1", "needs": ["culture"], "explains": ["T-999"]}],
        "inventory": {"vocabulary": {"core": []}},
    }
    res_bad = preflight_lesson(plan_entry_bad, pack=clean_pack, word_store=clean_word_store)
    assert res_bad.passed is False
    assert any(g.need == "culture" for g in res_bad.gaps)


def test_preflight_paradigm_need(clean_word_store, clean_pack):
    """Paradigm need passes when word and forms exist; fails when missing or pending stress."""
    plan_entry = {
        "steps": [
            {
                "id": "s1",
                "needs": ["paradigm"],
                "paradigm": {"id": "P-01", "word": "W-001", "forms": ["noun:inanim:n:v_naz"]},
            }
        ],
        "inventory": {"vocabulary": {"core": []}},
    }
    res = preflight_lesson(plan_entry, pack=clean_pack, word_store=clean_word_store)
    assert res.passed is True

    # Word store with pending stress form
    pending_store = {
        "words": [
            {
                "id": "W-001",
                "lemma": "слово",
                "forms": [
                    {
                        "form": "слово",
                        "tags": "noun:inanim:n:v_naz",
                        "stressed": None,
                        "stress_source": "pending",
                        "learner": True,
                    },
                ],
            }
        ]
    }
    res_pending = preflight_lesson(plan_entry, pack=clean_pack, word_store=pending_store)
    assert res_pending.passed is False
    assert any(g.need == "word_form" and "pending stress" in g.detail for g in res_pending.gaps)


def test_preflight_cited_forms_pending_stress(clean_pack):
    """R-23: A cited form with stress_source == 'pending' fails preflight."""
    store_pending = {
        "words": [
            {
                "id": "W-010",
                "lemma": "тест",
                "forms": [
                    {
                        "form": "тест",
                        "tags": "noun:inanim:m:v_naz",
                        "stressed": None,
                        "stress_source": "pending",
                        "learner": True,
                    }
                ],
            }
        ]
    }
    plan_entry = {
        "steps": [{"id": "s1"}],
        "inventory": {
            "vocabulary": {"core": [{"evidence": "W-010", "lemma": "тест", "forms": ["noun:inanim:m:v_naz"]}]}
        },
    }
    res = preflight_lesson(plan_entry, pack=clean_pack, word_store=store_pending)
    assert res.passed is False
    assert any(g.need == "word_form" and "pending stress" in g.detail for g in res.gaps)


def test_homograph_list_restricted_to_lesson_words(clean_pack):
    """Finding 12: Homograph list is computed over the lesson's allowed words rather than entire _words.yaml."""
    store = {
        "words": [
            {
                "id": "W-001",
                "lemma": "замок",
                "forms": [
                    {
                        "form": "замок",
                        "tags": "noun:inanim:m:v_naz",
                        "stressed": "за́мок",
                        "stress_source": "vesum",
                        "learner": True,
                    }
                ],
            },
            {
                "id": "W-002",
                "lemma": "замок",
                "forms": [
                    {
                        "form": "замок",
                        "tags": "noun:inanim:m:v_naz",
                        "stressed": "замо́к",
                        "stress_source": "vesum",
                        "learner": True,
                    }
                ],
            },
            {
                "id": "W-003",
                "lemma": "стіл",
                "forms": [
                    {
                        "form": "стіл",
                        "tags": "noun:inanim:m:v_naz",
                        "stressed": "сті́л",
                        "stress_source": "vesum",
                        "learner": True,
                    }
                ],
            },
        ]
    }
    # Lesson inventory cites only W-003 ('стіл'), not W-001/W-002 ('замок')
    plan_entry = {
        "steps": [{"id": "s1"}],
        "inventory": {"vocabulary": {"core": [{"evidence": "W-003", "lemma": "стіл"}]}},
    }
    res = preflight_lesson(plan_entry, pack=clean_pack, word_store=store)
    # Even though store has ambiguous "замок", the lesson only allows "стіл", so homographs is empty
    assert res.homographs == []
    assert res.homograph_count == 0

    # If lesson cites W-001 and W-002, "замок" appears in homographs
    plan_entry_with_homograph = {
        "steps": [{"id": "s1"}],
        "inventory": {
            "vocabulary": {
                "core": [
                    {"evidence": "W-001", "lemma": "замок"},
                    {"evidence": "W-002", "lemma": "замок"},
                ]
            }
        },
    }
    res2 = preflight_lesson(plan_entry_with_homograph, pack=clean_pack, word_store=store)
    assert "замок" in res2.homographs
    assert res2.homograph_count == 1


def test_failed_preflight_writes_gap_report_atomically(tmp_path, clean_word_store, clean_pack):
    """Failed preflight writes gap report atomically with mode 0o644 (#8431 §4, Findings 4 & 11)."""
    gap_file = tmp_path / "gap_report.yaml"
    plan_entry = {
        "steps": [{"id": "s2", "needs": ["example"], "ref": "EX-missing"}],
        "inventory": {"vocabulary": {"core": []}},
    }
    res = preflight_lesson(plan_entry, pack=clean_pack, word_store=clean_word_store, gap_report_path=gap_file)
    assert res.passed is False
    assert res.status == "evidence_gap"
    assert gap_file.is_file()

    # Check file permissions are 0o644
    mode = stat.S_IMODE(gap_file.stat().st_mode)
    assert mode == 0o644

    content = yaml.safe_load(gap_file.read_text(encoding="utf-8"))
    assert content["status"] == "evidence_gap"
    assert len(content["gaps"]) == 1
    assert content["gaps"][0]["step"] == "s2"
    assert content["gaps"][0]["need"] == "example"
