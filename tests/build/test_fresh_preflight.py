"""Tests for fresh build engine Part E2 preflight verification and gap reports (#8431 §4, §7 row 0)."""

from __future__ import annotations

import pytest
import yaml

from scripts.build.fresh.preflight import compute_homographs, preflight_lesson
from scripts.curriculum.resolver.inputs import Allowlist


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
    """Culture need passes when T- is present; fails when missing."""
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


def test_homograph_list_computation():
    """Homograph list identifies words with multiple readings (via resolver ambiguity logic)."""
    records = [
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
                },
                {
                    "form": "стіл",
                    "tags": "noun:inanim:m:v_zna",
                    "stressed": "сті́л",
                    "stress_source": "vesum",
                    "learner": True,
                },
            ],
        },
    ]
    allowlist = Allowlist.from_records(records, words_lock="test-lock")
    homographs = compute_homographs(allowlist)

    # "замок" has 2 competing records/stresses -> homograph
    assert "замок" in homographs
    # "стіл" has 2 syncretic forms of the SAME record with identical stress -> NOT a homograph
    assert "стіл" not in homographs
    assert homographs == ["замок"]


def test_failed_preflight_writes_gap_report(tmp_path, clean_word_store, clean_pack):
    """Failed preflight writes gap report to disk and makes no call."""
    gap_file = tmp_path / "gap_report.yaml"
    plan_entry = {
        "steps": [{"id": "s2", "needs": ["example"], "ref": "EX-missing"}],
        "inventory": {"vocabulary": {"core": []}},
    }
    res = preflight_lesson(plan_entry, pack=clean_pack, word_store=clean_word_store, gap_report_path=gap_file)
    assert res.passed is False
    assert res.status == "evidence_gap"
    assert gap_file.is_file()

    content = yaml.safe_load(gap_file.read_text(encoding="utf-8"))
    assert content["status"] == "evidence_gap"
    assert len(content["gaps"]) == 1
    assert content["gaps"][0]["step"] == "s2"
    assert content["gaps"][0]["need"] == "example"
