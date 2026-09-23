"""Tests for check_text (#8398 part C).

Validates:
- MCP tool listing, description, and read-only annotations
- Synthetic tests: input errors (both/neither/caps/accents/checks/max_findings),
  dedup, locations, item IDs, truncation order, 501 stress chunking,
  stress_forms case insensitivity and ambiguity resolution,
  UA-GEC multi-token problems vs single-token suspicions, sub-span non-matching,
  UA-GEC overlapping hits, skipped-kind token dropping and counting in provenance,
  shadow curated list attribution and suspicion separation
- Regression test proving is_russian_pattern output keys are unchanged (M2)
- Real corpus fixture (>=600 tokens): unmodified chunk invariants, UA-GEC clean
  finding count, query-selected planted VESUM and deterministic UA-GEC errors
  substituted and reported at exact locations, monosyllable stress immunity
- In-process warm call performance (<2.0s)
- Benchmark script reduced run assertion (1 call and faster than per-tool path)
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import logging
import sqlite3
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.curriculum.evidence.sources import _sources_path
from scripts.curriculum.resolver.codes import SKIPPED_KINDS
from scripts.curriculum.resolver.tokenize import tokenize
from scripts.rag.config import VESUM_DB_PATH
from scripts.verification.check_ru_morph import is_russian_pattern
from scripts.verification.check_text import check_text
from scripts.verification.stress import STRESS_BATCH_CAP
from scripts.verification.vesum import verify_words

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCES_SERVER_PATH = PROJECT_ROOT / ".mcp" / "servers" / "sources" / "server.py"
PINNED_FIXTURE_CHUNK_ID = "private-teacher-lessons-a_43833086dcbaea83555d"

logger = logging.getLogger(__name__)


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def server_module():
    spec = importlib.util.spec_from_file_location("sources_server_check_text", SOURCES_SERVER_PATH)
    srv = importlib.util.module_from_spec(spec)
    sys.modules["sources_server_check_text"] = srv
    spec.loader.exec_module(srv)
    return srv


# ── MCP Tool Listing & Annotations ──────────────────────────────────────────


def test_tool_listed_in_mcp_server(server_module):
    tools = _run(server_module.list_tools())
    tool = next((t for t in tools if t.name == "check_text"), None)
    assert tool is not None, "check_text must be registered in sources server list_tools"
    assert (
        tool.description
        == "check a lesson, a passage or a set of exercise items in one call; problems are sourced, suspicions are labelled"
    )
    assert tool.annotations is not None
    assert tool.annotations.read_only_hint is True
    assert tool.annotations.destructive_hint is False
    assert "text" in tool.input_schema["properties"]
    assert "items" in tool.input_schema["properties"]
    assert "checks" in tool.input_schema["properties"]
    assert "stress_forms" in tool.input_schema["properties"]
    assert "max_findings" in tool.input_schema["properties"]
    assert "ua_gec_tags" in tool.input_schema["properties"]


def test_mcp_call_tool_dispatch(server_module, requires_vesum_db, requires_sources_db):
    result = _run(server_module.call_tool("check_text", {"text": "Це гарний день."}))
    assert len(result) == 1
    payload = json.loads(result[0].text)
    assert "provenance" in payload
    assert "summary" in payload
    assert "problems" in payload
    assert "suspicions" in payload
    assert payload["summary"]["tokens"] >= 3


# ── M2: Existing Tool Output Keys Preserved ──────────────────────────────────


def test_is_russian_pattern_output_keys_unchanged():
    expected_keys = {"matches_russian", "russian_lemma", "ukrainian_alternative", "confidence"}

    res_clean = is_russian_pattern("слово")
    assert set(res_clean.keys()) == expected_keys
    assert "is_curated" not in res_clean

    res_calque = is_russian_pattern("получити")
    assert set(res_calque.keys()) == expected_keys
    assert "is_curated" not in res_calque

    res_empty = is_russian_pattern("")
    assert set(res_empty.keys()) == expected_keys
    assert "is_curated" not in res_empty


# ── Synthetic Tests: Input Errors (M3 & Minor 1) ────────────────────────────


def test_input_errors_both():
    res = check_text(text="Привіт.", items=[{"id": 1, "text": "Світ."}])
    assert res.get("status") == "error"
    assert res.get("error_code") == "invalid_input"
    assert "both" in res.get("error", "")


def test_input_errors_neither():
    res = check_text()
    assert res.get("status") == "error"
    assert res.get("error_code") == "invalid_input"
    assert "neither" in res.get("error", "")


def test_input_errors_item_cap():
    items = [{"id": i, "text": f"Слово {i}"} for i in range(201)]
    res = check_text(items=items)
    assert res.get("status") == "error"
    assert res.get("error_code") == "invalid_input"
    assert "200" in res.get("error", "")


def test_input_errors_accent_in_text():
    res = check_text(text="Це гарна́ хата.")
    assert res.get("status") == "error"
    assert res.get("error_code") == "accent_in_input"


def test_input_errors_accent_in_items():
    items = [{"id": "item-1", "text": "Це чиста вода."}, {"id": "item-2", "text": "Це гарна́ хата."}]
    res = check_text(items=items)
    assert res.get("status") == "error"
    assert res.get("error_code") == "accent_in_input"


def test_input_errors_invalid_checks():
    for bad_checks in ([], ["shadow"], ["ua-gec"], ["vesum", "nonexistent"], "vesum"):
        res = check_text(text="Привіт.", checks=bad_checks)
        assert res.get("status") == "error"
        assert res.get("error_code") == "invalid_input"
        assert "checks" in res.get("error", "")


def test_input_errors_invalid_ua_gec_tags():
    # Minor 1: validate ua_gec_tags against ingest tags, reject unknown/empty/bare strings
    for bad_tags in ([], ["F/calque"], ["nonexistent"], "F/Calque", 123):
        res = check_text(text="Привіт.", ua_gec_tags=bad_tags)
        assert res.get("status") == "error"
        assert res.get("error_code") == "invalid_input"
        assert "ua_gec_tags" in res.get("error", "")


def test_input_errors_invalid_max_findings():
    for bad_val in (0, -1, -100, True, False, 1.5, "10", None):
        res = check_text(text="Привіт.", max_findings=bad_val)
        assert res.get("status") == "error"
        assert res.get("error_code") == "invalid_input"
        assert "max_findings" in res.get("error", "")


# ── Synthetic Tests: Dedup & Locations ───────────────────────────────────────


def test_synthetic_dedup_and_locations():
    text = "Немає води тут, і немає води там, без води знову."
    res = check_text(text=text, checks=["stress"])
    assert res.get("status") != "error"
    problems = res["problems"]
    vody_problems = [p for p in problems if p["form"] == "води" and p["check"] == "stress"]
    assert len(vody_problems) == 1, "Should deduplicate 'води' to a single problem entry"
    locs = vody_problems[0]["locations"]
    assert len(locs) == 3, f"Expected 3 locations for 'води', got {locs}"
    for loc in locs:
        assert loc[0] is None
        assert text[loc[1] : loc[2]] == "води"


def test_synthetic_item_id_path():
    items = [
        {"id": "exercise-1", "text": "Тут замок."},
        {"id": "exercise-2", "text": "Там також стоїть замок."},
    ]
    res = check_text(items=items, checks=["stress"])
    assert res.get("status") != "error"
    zamok_problems = [p for p in res["problems"] if p["form"] == "замок" and p["check"] == "stress"]
    assert len(zamok_problems) == 1
    locs = zamok_problems[0]["locations"]
    assert len(locs) == 2
    assert locs[0][0] == "exercise-1"
    assert locs[1][0] == "exercise-2"
    assert items[0]["text"][locs[0][1] : locs[0][2]] == "замок"
    assert items[1]["text"][locs[1][1] : locs[1][2]] == "замок"


# ── Synthetic Tests: Truncation Order & Uncut Count ──────────────────────────


def test_synthetic_truncation_order_and_uncut_count():
    items = [
        {"id": "item-A", "text": "Ось замок і атлас."},
        {"id": "item-B", "text": "А ось обід і орган."},
    ]
    res = check_text(items=items, checks=["stress"], max_findings=2)
    assert res.get("status") != "error"
    summary = res["summary"]
    assert summary["truncated"] is True
    assert summary["uncut_count"] >= 4
    total_findings = len(res["problems"]) + len(res["suspicions"])
    assert total_findings == 2

    first_item_id = res["problems"][0]["locations"][0][0]
    second_item_id = res["problems"][1]["locations"][0][0]
    assert first_item_id == "item-A"
    assert second_item_id == "item-A"


# ── Synthetic Tests: Stress Chunking at 501 Forms ────────────────────────────


def test_synthetic_stress_chunk_501_forms():
    words = [f"балачка{i:03d}а" for i in range(501)]
    text = " ".join(words)

    with patch(
        "scripts.verification.check_text.verify_stresses",
        wraps=__import__("scripts.verification.stress", fromlist=["verify_stresses"]).verify_stresses,
    ) as mock_stresses:
        res = check_text(text=text, checks=["stress"])
        assert res.get("status") != "error"
        assert mock_stresses.call_count == 2
        first_call_len = len(mock_stresses.call_args_list[0][0][0])
        second_call_len = len(mock_stresses.call_args_list[1][0][0])
        assert first_call_len == STRESS_BATCH_CAP
        assert second_call_len == 1
        assert res["summary"]["unique_forms"] == 501


# ── Stress: Forms Case-Insensitivity & Ambiguity Resolution (Minor 4) ────────


def test_stress_forms_case_insensitive_and_ambiguity_resolution():
    text = "Води немає тут."
    res_ambig = check_text(text=text, checks=["stress"])
    assert any(p["form"] == "Води" and p["detail"]["status"] == "ambiguous" for p in res_ambig["problems"])

    # With case-insensitive asserted stress reading, ambiguity is resolved
    res_resolved = check_text(
        text=text,
        checks=["stress"],
        stress_forms=["води́"],
    )
    stress_probs = [p for p in res_resolved["problems"] if p["check"] == "stress"]
    assert len(stress_probs) == 0, "Asserted stress reading should resolve ambiguity"

    # With unaccented or invalid asserted stress, word remains reported as ambiguous (not unbriefed stress_mismatch)
    res_invalid_asserted = check_text(
        text=text,
        checks=["stress"],
        stress_forms={"води": "води"},
    )
    probs = [p for p in res_invalid_asserted["problems"] if p["check"] == "stress"]
    assert len(probs) == 1
    assert probs[0]["detail"]["status"] == "ambiguous"


# ── Synthetic Tests: UA-GEC Whole Span, Overlapping, and Skipped Kinds ──────


def _opts_into_vesum(request: pytest.FixtureRequest) -> bool:
    """Real-database tests skip when the file is absent; hermetic tests mock it."""
    names = request.fixturenames
    return "requires_vesum_db" in names or "hermetic_ua_gec_vesum" in names


@pytest.fixture(autouse=True)
def _vesum_path_absent_unless_opt_in(request, monkeypatch, tmp_path):
    """Match CI, where ``data/vesum.db`` is not provisioned.

    ``check_text`` fails closed when ``_vesum_path_resolved`` is not a file.
    Leave that path missing unless the test opts into ``hermetic_ua_gec_vesum``
    or ``requires_vesum_db`` (the latter skips when the database is absent).
    A test body that monkeypatches the same attribute still wins.
    """
    if _opts_into_vesum(request):
        return
    missing = tmp_path / "vesum-not-provisioned.db"
    monkeypatch.setattr(
        "scripts.verification.check_text._vesum_path_resolved",
        lambda: missing,
    )


@pytest.fixture
def hermetic_ua_gec_vesum(monkeypatch, tmp_path):
    """Temp VESUM file plus a ``verify_words`` mock. Never opens the live database.

    The returned mapping starts empty. Empty rows are not closed-class, so a
    multi-token calque stays a problem. Put closed-class analyses in the
    mapping before calling ``check_text`` when a test needs that decision.
    """
    vesum_file = tmp_path / "vesum.db"
    vesum_file.touch()
    analyses: dict[str, list] = {}
    monkeypatch.setattr("scripts.verification.check_text._vesum_path_resolved", lambda: vesum_file)

    def _verify(words, **kwargs):
        return {word: list(analyses.get(word, [])) for word in words}

    monkeypatch.setattr("scripts.verification.check_text.verify_words", _verify)
    return analyses


@pytest.mark.usefixtures("hermetic_ua_gec_vesum")
def test_synthetic_ua_gec_single_token_to_suspicion(monkeypatch):
    mock_index = {
        ("коментарій",): [
            {
                "id": 101,
                "error": "коментарій",
                "correct": "коментар",
                "error_type": "F/Calque",
                "doc_id": "doc1",
                "is_native": 0,
            }
        ]
    }
    monkeypatch.setattr("scripts.verification.check_text._get_ua_gec_index", lambda: (mock_index, 1, 0))

    text = "Мій коментарій важливий."
    res = check_text(text=text, checks=["ua_gec"])
    assert res.get("status") != "error"
    assert len(res["problems"]) == 0
    assert len(res["suspicions"]) == 1
    s = res["suspicions"][0]
    assert s["check"] == "ua_gec"
    assert s["form"] == "коментарій"
    assert s["detail"]["status"] == "suspicion"
    assert s["detail"]["label"] == "UA-GEC correction in one document's context; suspicion, not a verdict"
    assert s["detail"]["error_type"] == "F/Calque"
    assert s["detail"]["doc_ids"] == ["doc1"]
    assert s["detail"]["corrections"] == [{"correct": "коментар", "doc_ids": ["doc1"]}]


# Backward-compatible alias for existing test node id
test_synthetic_ua_gec_one_word_whole_span = test_synthetic_ua_gec_single_token_to_suspicion


@pytest.mark.usefixtures("hermetic_ua_gec_vesum")
def test_synthetic_ua_gec_multi_token_stays_in_problems(monkeypatch):
    mock_index = {
        ("написання", "постів"): [
            {
                "id": 202,
                "error": "написання постів",
                "correct": "писати дописи",
                "error_type": "F/Calque",
                "doc_id": "doc2",
                "is_native": 0,
            }
        ]
    }
    monkeypatch.setattr("scripts.verification.check_text._get_ua_gec_index", lambda: (mock_index, 2, 0))

    text = "Триває написання постів щодня."
    res = check_text(text=text, checks=["ua_gec"])
    assert res.get("status") != "error"
    assert len(res["suspicions"]) == 0
    assert len(res["problems"]) == 1
    p = res["problems"][0]
    assert p["check"] == "ua_gec"
    assert p["form"] == "написання постів"
    assert p["detail"]["status"] == "ua_gec_error"
    assert p["detail"]["error_type"] == "F/Calque"
    assert p["detail"]["doc_ids"] == ["doc2"]
    assert p["detail"]["corrections"] == [{"correct": "писати дописи", "doc_ids": ["doc2"]}]


@pytest.mark.usefixtures("hermetic_ua_gec_vesum")
def test_synthetic_ua_gec_collocation_goes_to_suspicion(monkeypatch):
    # Driver settlement 2: F/Collocation of any length goes to suspicions
    mock_index = {
        ("брати", "участь"): [
            {
                "id": 303,
                "error": "брати участь",
                "correct": "взяти участь",
                "error_type": "F/Collocation",
                "doc_id": "doc3",
                "is_native": 0,
            }
        ],
    }
    monkeypatch.setattr("scripts.verification.check_text._get_ua_gec_index", lambda: (mock_index, 2, 0))

    text = "Він вирішив брати участь у змаганнях."
    res = check_text(text=text, checks=["ua_gec"])
    assert res.get("status") != "error"
    assert len(res["problems"]) == 0
    assert len(res["suspicions"]) == 1
    s = res["suspicions"][0]
    assert s["form"] == "брати участь"
    assert s["detail"]["status"] == "suspicion"
    assert s["detail"]["label"] == "UA-GEC correction in one document's context; suspicion, not a verdict"


def test_synthetic_ua_gec_closed_class_calque_goes_to_suspicion(monkeypatch, hermetic_ua_gec_vesum):
    # Closed-class rule: multi-token F/Calque consisting only of closed-class words goes to suspicions
    mock_index = {
        ("як", "він"): [
            {
                "id": 6663,
                "error": ", як він",
                "correct": " за нього",
                "error_type": "F/Calque",
                "doc_id": "1334",
                "is_native": 0,
            }
        ],
    }
    monkeypatch.setattr("scripts.verification.check_text._get_ua_gec_index", lambda: (mock_index, 2, 0))
    hermetic_ua_gec_vesum.update(
        {
            "як": [{"lemma": "як", "pos": "conj", "tags": "conj:subord"}],
            "він": [{"lemma": "він", "pos": "noun", "tags": "noun:unanim:m:v_naz:pron:pers:3"}],
        }
    )

    text = "Він сказав так, як він думав."
    res = check_text(text=text, checks=["ua_gec"])
    assert res.get("status") != "error"
    assert len(res["problems"]) == 0
    assert len(res["suspicions"]) == 1
    s = res["suspicions"][0]
    assert s["form"] == "як він"
    assert s["detail"]["status"] == "suspicion"
    assert s["detail"]["label"] == (
        "UA-GEC correction of function words; depends on sentence context; suspicion, not a verdict"
    )


@pytest.mark.usefixtures("hermetic_ua_gec_vesum")
def test_synthetic_ua_gec_sub_span_not_matched(monkeypatch):
    mock_index = {
        ("написання", "постів"): [
            {
                "id": 202,
                "error": "написання постів",
                "correct": "писати дописи",
                "error_type": "F/Calque",
                "doc_id": "doc2",
                "is_native": 0,
            }
        ]
    }
    monkeypatch.setattr("scripts.verification.check_text._get_ua_gec_index", lambda: (mock_index, 2, 0))

    text_subspan = "Триває написання нового твору."
    res_subspan = check_text(text=text_subspan, checks=["ua_gec"])
    assert len(res_subspan["problems"]) == 0, "Sub-span of longer UA-GEC error must NOT match"
    assert len(res_subspan["suspicions"]) == 0

    text_full = "Триває написання постів щодня."
    res_full = check_text(text=text_full, checks=["ua_gec"])
    assert len(res_full["problems"]) == 1
    assert res_full["problems"][0]["form"] == "написання постів"
    loc = res_full["problems"][0]["locations"][0]
    assert text_full[loc[1] : loc[2]] == "написання постів"


@pytest.mark.usefixtures("hermetic_ua_gec_vesum")
def test_synthetic_ua_gec_overlapping_hits(monkeypatch):
    # Minor 1: test every full-span match, including overlapping spans starting inside earlier match
    mock_index = {
        ("у", "цілому"): [
            {
                "id": 1,
                "error": "у цілому",
                "correct": "загалом",
                "error_type": "F/Calque",
                "doc_id": "d1",
                "is_native": 0,
            }
        ],
        ("цілому",): [
            {
                "id": 2,
                "error": "цілому",
                "correct": "повному",
                "error_type": "F/Collocation",
                "doc_id": "d2",
                "is_native": 0,
            }
        ],
    }
    monkeypatch.setattr("scripts.verification.check_text._get_ua_gec_index", lambda: (mock_index, 2, 0))
    text = "Все відбулося у цілому добре."
    res = check_text(text=text, checks=["ua_gec"])
    assert res.get("status") != "error"
    prob_forms = {p["form"] for p in res["problems"]}
    susp_forms = {s["form"] for s in res["suspicions"]}
    assert "у цілому" in prob_forms, "Outer match must be reported as problem"
    assert "цілому" in susp_forms, "Overlapping inner match must be reported as suspicion"
    assert len(res["problems"]) == 1
    assert len(res["suspicions"]) == 1


@pytest.mark.usefixtures("hermetic_ua_gec_vesum")
def test_synthetic_ua_gec_skipped_kind_breaks_contiguity(monkeypatch):
    # Minor 3 / Settlement 5: skipped-kind tokens (latin, digits) break contiguity on text side
    mock_index = {
        ("написання", "постів"): [
            {
                "id": 202,
                "error": "написання постів",
                "correct": "писати дописи",
                "error_type": "F/Calque",
                "doc_id": "doc2",
                "is_native": 0,
            }
        ]
    }
    monkeypatch.setattr("scripts.verification.check_text._get_ua_gec_index", lambda: (mock_index, 2, 0))

    # Digit between words breaks contiguity
    text_digit = "Триває написання 2 постів щодня."
    res_digit = check_text(text=text_digit, checks=["ua_gec"])
    assert len(res_digit["problems"]) == 0
    assert len(res_digit["suspicions"]) == 0

    # Latin word between words breaks contiguity
    text_latin = "Триває написання post постів щодня."
    res_latin = check_text(text=text_latin, checks=["ua_gec"])
    assert len(res_latin["problems"]) == 0
    assert len(res_latin["suspicions"]) == 0

    # Contiguous words without skipped kind match
    text_clean = "Триває написання постів щодня."
    res_clean = check_text(text=text_clean, checks=["ua_gec"])
    assert len(res_clean["problems"]) == 1
    assert res_clean["problems"][0]["form"] == "написання постів"


@pytest.mark.usefixtures("hermetic_ua_gec_vesum")
def test_synthetic_ua_gec_skipped_kind_tokens_dropped_and_counted(monkeypatch):
    # Settlement 1: synthetic index count in provenance, not hard-coding against live database
    mock_index = {
        ("привіт",): [
            {
                "id": 1,
                "error": "привіт",
                "correct": "вітаю",
                "error_type": "F/Calque",
                "doc_id": "d1",
                "is_native": 1,
            }
        ]
    }
    monkeypatch.setattr("scripts.verification.check_text._get_ua_gec_index", lambda: (mock_index, 1, 5))
    res = check_text(text="Привіт.", checks=["ua_gec"])
    assert res.get("status") != "error"
    prov = res["provenance"]
    assert "ua_gec_dropped_skipped_kind_rows" in prov
    assert prov["ua_gec_dropped_skipped_kind_rows"] == 5


def test_real_ua_gec_skipped_kind_tokens_dropped_and_counted(requires_sources_db, requires_vesum_db):
    # Settlement 1: real database variant asserts >= 1
    res = check_text(text="Привіт.", checks=["ua_gec"])
    assert res.get("status") != "error"
    prov = res["provenance"]
    assert "ua_gec_dropped_skipped_kind_rows" in prov
    assert prov["ua_gec_dropped_skipped_kind_rows"] >= 1


# ── Russian Shadow: Curated Lists and Suspicions (Minor 5) ───────────────────


def test_synthetic_shadow_curated_and_suspicion_split(requires_vesum_db):
    # 'бажаючий' is in CURATED_CALQUES (with ukrainian alternative 'охочий')
    # 'получити' is in KNOWN_SHADOW_LEMMAS
    # 'врач' is Russian confidence 1.0, not in curated lists
    text = "Бажаючий лікар не врач, але треба получити дозвіл."
    res = check_text(text=text, checks=["russian_shadow"])
    assert res.get("status") != "error"

    problems = [p for p in res["problems"] if p["check"] == "russian_shadow"]
    suspicions = [s for s in res["suspicions"] if s["check"] == "russian_shadow"]

    prob_forms = {p["form"] for p in problems}
    susp_forms = {s["form"] for s in suspicions}

    assert "Бажаючий" in prob_forms or "бажаючий" in prob_forms
    assert "получити" in prob_forms
    assert "врач" in susp_forms
    assert "врач" not in prob_forms

    p_calque = next(p for p in problems if p["form"] in ("бажаючий", "Бажаючий"))
    assert p_calque["detail"]["curated"] is True
    assert p_calque["detail"]["curated_list"] == "curated_calques"
    assert "охочий" in p_calque["detail"]["ukrainian_alternative"]

    p_shadow = next(p for p in problems if p["form"] == "получити")
    assert p_shadow["detail"]["curated"] is True
    assert p_shadow["detail"]["curated_list"] == "known_shadow_lemmas"

    s_vrach = next(s for s in suspicions if s["form"] == "врач")
    assert s_vrach["detail"]["curated"] is False
    assert s_vrach["detail"]["label"] == "suspicion, not a verdict"


# ── Structured Source Unavailable Errors (Settlement 1 / N1) ─────────────────


def test_synthetic_ua_gec_source_unavailable_when_db_missing(monkeypatch):
    monkeypatch.setenv("LU_SOURCES_DB", "/nonexistent/sources.db")
    monkeypatch.setattr(
        "scripts.verification.check_text._sources_path_resolved",
        lambda: Path("/nonexistent/sources.db"),
    )
    res = check_text(text="Це гарний день.", checks=["ua_gec"])
    assert res.get("status") == "error"
    assert res.get("error_code") == "source_unavailable"
    assert "sources database not found" in res.get("error", "")


def test_synthetic_vesum_source_unavailable_when_db_missing(monkeypatch):
    monkeypatch.setenv("VESUM_DB_PATH", "/nonexistent/vesum.db")
    monkeypatch.setattr(
        "scripts.verification.vesum._resolve_vesum_db_path",
        lambda db_path=None: Path("/nonexistent/vesum.db"),
    )
    res = check_text(text="Це гарний день.", checks=["vesum"])
    assert res.get("status") == "error"
    assert res.get("error_code") == "source_unavailable"
    assert "VESUM database not found" in res.get("error", "")


def test_ua_gec_only_missing_vesum_is_source_unavailable(monkeypatch):
    """Closed-class spans must not become problems when VESUM cannot be read."""
    mock_index = {
        ("як", "він"): [
            {
                "id": 6663,
                "error": ", як він",
                "correct": " за нього",
                "error_type": "F/Calque",
                "doc_id": "1334",
                "is_native": 0,
            }
        ],
    }
    monkeypatch.setattr("scripts.verification.check_text._get_ua_gec_index", lambda: (mock_index, 2, 0))
    missing = Path("/nonexistent/vesum-check-text.db")
    monkeypatch.setattr("scripts.verification.check_text._vesum_path_resolved", lambda: missing)

    res = check_text(text="Він сказав так, як він думав.", checks=["ua_gec"])

    assert res == {
        "status": "error",
        "error_code": "source_unavailable",
        "error": f"source_unavailable: VESUM database not found at {missing}",
    }
    assert "problems" not in res


def test_ua_gec_network_sources_path_returns_source_unavailable(monkeypatch):
    from scripts.storage.topology import ActiveDatabaseNetworkError

    def raise_network() -> Path:
        raise ActiveDatabaseNetworkError(
            "Active sources.db must remain on local storage; "
            "refused network path (repository_data_on_network_filesystem)."
        )

    monkeypatch.setattr("scripts.verification.check_text._sources_path_resolved", raise_network)
    res = check_text(text="Це гарний день.", checks=["ua_gec"])
    assert res.get("status") == "error"
    assert res.get("error_code") == "source_unavailable"
    assert str(res.get("error", "")).startswith("source_unavailable:")
    assert "refused network path" in res.get("error", "")


# ── Real Corpus Fixture Tests (Minor 3, Minor 6, Minor 7) ────────────────────


def _load_textbook_fixture() -> tuple[str, str] | None:
    sources_path = _sources_path()
    if not sources_path.is_file() or not Path(VESUM_DB_PATH).is_file():
        return None
    conn = sqlite3.connect(f"file:{sources_path}?mode=ro", uri=True)
    try:
        # Minor 7: Pin by chunk_id
        cur = conn.execute(
            "SELECT chunk_id, text FROM textbooks WHERE chunk_id = ?",
            (PINNED_FIXTURE_CHUNK_ID,),
        )
        row = cur.fetchone()
        if row:
            return row[0], row[1]
        # Fallback if specific chunk missing
        cur = conn.execute("SELECT chunk_id, text FROM textbooks WHERE char_count > 4000 ORDER BY id LIMIT 10")
        for cid, text in cur.fetchall():
            tokens = [t for t in tokenize(text) if t.kind not in SKIPPED_KINDS]
            if len(tokens) >= 600:
                return cid, text
    finally:
        conn.close()
    return None


def test_acceptance_textbook_fixture_correctness_and_planted(requires_vesum_db, requires_sources_db):
    fixture = _load_textbook_fixture()
    if fixture is None:
        pytest.skip("data/sources.db or vesum.db not provisioned")
    chunk_id, original_text = fixture
    tokens = [t for t in tokenize(original_text) if t.kind not in SKIPPED_KINDS]
    assert len(tokens) >= 600, f"Chunk {chunk_id} has {len(tokens)} tokens, expected >= 600"

    # 1. Unmodified chunk check
    res_clean = check_text(text=original_text, checks=["vesum", "stress", "ua_gec"])
    assert res_clean.get("status") != "error"

    # Provenance check (Minor 6: canonical VESUM metadata digest)
    conn_v = sqlite3.connect(f"file:{requires_vesum_db}?mode=ro", uri=True)
    cur_v = conn_v.execute("SELECT value FROM vesum_build_metadata WHERE key = 'canonical_jsonl_sha256'")
    expected_vesum_digest = cur_v.fetchone()[0]
    conn_v.close()
    assert res_clean["provenance"]["vesum_version"] == expected_vesum_digest

    # Invariant: forms that VESUM has (including sentence-initial capitals) must not yield no_vesum_row
    vesum_problems = {p["form"] for p in res_clean["problems"] if p["check"] == "vesum"}
    sent_init_caps = {t.lookup for t in tokens if t.sentence_initial and t.capitalised}
    for p_form in vesum_problems:
        direct = verify_words([p_form]).get(p_form, [])
        lower_retry = (
            verify_words([p_form[:1].lower() + p_form[1:]]).get(p_form[:1].lower() + p_form[1:], [])
            if p_form in sent_init_caps
            else []
        )
        assert not direct and not lower_retry, f"Form {p_form!r} is attested in VESUM but was reported as no_vesum_row"

    # Invariant: no monosyllable is flagged by stress
    stress_problems = {p["form"] for p in res_clean["problems"] if p["check"] == "stress"}
    ukrainian_vowels = frozenset("аеєиіїоуюяАЕЄИІЇОУЮЯ")
    for s_form in stress_problems:
        vowel_count = sum(1 for ch in s_form if ch in ukrainian_vowels)
        assert vowel_count >= 2, f"Monosyllable {s_form!r} was flagged by stress"

    # Minor 3 / Settlement 2: UA-GEC findings on clean fixture (collocations & single-token to suspicions)
    gec_clean_problems = [p for p in res_clean["problems"] if p["check"] == "ua_gec"]
    gec_clean_suspicions = [s for s in res_clean["suspicions"] if s["check"] == "ua_gec"]
    clean_problem_spans = [p["form"] for p in gec_clean_problems]
    clean_suspicion_spans = [s["form"] for s in gec_clean_suspicions]
    print(
        f"\nClean fixture UA-GEC findings: {len(gec_clean_problems)} problems {clean_problem_spans}, "
        f"{len(gec_clean_suspicions)} suspicions {clean_suspicion_spans}"
    )
    logger.info(
        "Clean fixture UA-GEC findings: %d problems %s, %d suspicions %s",
        len(gec_clean_problems),
        clean_problem_spans,
        len(gec_clean_suspicions),
        clean_suspicion_spans,
    )

    # 2. Planted items (Minor 7: query-selected and substituted into text)
    candidate_absent = ["бзюкавий", "хряпочка", "дзиґомонець", "псевдословорія"]
    v_results = verify_words(candidate_absent)
    selected_absent = [w for w in candidate_absent if not v_results.get(w)][:2]
    assert len(selected_absent) == 2
    planted_vesum_1, planted_vesum_2 = selected_absent

    # Deterministic multi-word UA-GEC row 3010 (F/Calque: 'написання постів')
    conn = sqlite3.connect(f"file:{requires_sources_db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute("SELECT id, error, correct FROM ua_gec_errors WHERE id = 3010")
        gec_row = cur.fetchone()
    finally:
        conn.close()

    assert gec_row is not None
    assert gec_row["id"] == 3010
    planted_gec_error = gec_row["error"]

    # Substitute into text at token locations
    t1 = tokens[20]
    t_gec = tokens[100]
    t2 = tokens[200]

    modified_text = (
        original_text[: t1.start]
        + planted_vesum_1
        + original_text[t1.end : t_gec.start]
        + planted_gec_error
        + original_text[t_gec.end : t2.start]
        + planted_vesum_2
        + original_text[t2.end :]
    )

    res_modified = check_text(text=modified_text, checks=["vesum", "ua_gec"])
    assert res_modified.get("status") != "error"

    problems = res_modified["problems"]

    p1 = next((p for p in problems if p["form"] == planted_vesum_1 and p["check"] == "vesum"), None)
    assert p1 is not None, f"Planted {planted_vesum_1} not detected"
    loc1 = p1["locations"][0]
    assert modified_text[loc1[1] : loc1[2]] == planted_vesum_1

    p2 = next((p for p in problems if p["form"] == planted_vesum_2 and p["check"] == "vesum"), None)
    assert p2 is not None, f"Planted {planted_vesum_2} not detected"
    loc2 = p2["locations"][0]
    assert modified_text[loc2[1] : loc2[2]] == planted_vesum_2

    p_gec = next(
        (p for p in problems if p["check"] == "ua_gec" and p["form"] == planted_gec_error),
        None,
    )
    assert p_gec is not None, f"Planted UA-GEC error {planted_gec_error} not detected in problems"
    loc_gec = p_gec["locations"][0]
    assert modified_text[loc_gec[1] : loc_gec[2]] == planted_gec_error
    assert not any(s["form"] == planted_gec_error for s in res_modified["suspicions"])


def test_speed_warm_call_under_2s(requires_vesum_db, requires_sources_db):
    fixture = _load_textbook_fixture()
    if fixture is None:
        pytest.skip("data/sources.db or vesum.db not provisioned")
    _, text = fixture

    # Warm-up call
    check_text(text=text)

    # Measured warm call with all four checks
    t0 = time.perf_counter()
    res = check_text(text=text)
    elapsed = time.perf_counter() - t0

    assert elapsed < 2.0, f"check_text warm call took {elapsed:.3f}s, expected < 2.0s"
    assert res.get("status") != "error"
    assert res["summary"]["tokens"] >= 600


# ── M1 Benchmark Script Reduced Acceptance Test (Minor 2) ───────────────────


def test_bench_check_text_reduced(requires_vesum_db, requires_sources_db):
    from scripts.verification.bench_check_text import run_benchmark

    res = run_benchmark(reduced=True)
    assert res["check_text"]["calls"] == 1
    assert res["check_text"]["calls"] < res["legacy"]["calls"]
    assert res["check_text"]["chars"] < res["legacy"]["chars"]
