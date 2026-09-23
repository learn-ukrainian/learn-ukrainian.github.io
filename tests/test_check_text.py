"""Tests for check_text (#8398 part C).

Validates:
- MCP tool listing, description, and read-only annotations
- Synthetic tests: input errors, dedup, locations, item IDs, truncation order,
  501 stress chunking, UA-GEC whole span matching, UA-GEC sub-span non-matching,
  shadow score signals in suspicions only
- Real corpus fixture (>=600 tokens): unmodified chunk invariants, planted VESUM
  and UA-GEC errors reported at exact locations, monosyllable stress immunity
- In-process warm call performance (<2.0s) and before/after tool call comparison
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
from scripts.verification.check_text import check_text
from scripts.verification.stress import STRESS_BATCH_CAP
from scripts.verification.vesum import verify_words

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCES_SERVER_PATH = PROJECT_ROOT / ".mcp" / "servers" / "sources" / "server.py"

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


def test_mcp_call_tool_dispatch(server_module):
    result = _run(server_module.call_tool("check_text", {"text": "Це гарний день."}))
    assert len(result) == 1
    payload = json.loads(result[0].text)
    assert "provenance" in payload
    assert "summary" in payload
    assert "problems" in payload
    assert "suspicions" in payload
    assert payload["summary"]["tokens"] >= 3


# ── Synthetic Tests: Input Errors ────────────────────────────────────────────


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
    # Combining acute accent: U+0301
    res = check_text(text="Це гарна́ хата.")
    assert res.get("status") == "error"
    assert res.get("error_code") == "accent_in_input"


def test_input_errors_accent_in_items():
    items = [{"id": "item-1", "text": "Це чиста вода."}, {"id": "item-2", "text": "Це гарна́ хата."}]
    res = check_text(items=items)
    assert res.get("status") == "error"
    assert res.get("error_code") == "accent_in_input"


# ── Synthetic Tests: Dedup & Locations ───────────────────────────────────────


def test_synthetic_dedup_and_locations():
    # "води" appears 3 times in text at distinct positions
    text = "Немає води тут, і немає води там, без води знову."
    # We test with only checks=['stress'] where 'води' is ambiguous (во́ди vs води́)
    res = check_text(text=text, checks=["stress"])
    assert res.get("status") != "error"
    problems = res["problems"]
    vody_problems = [p for p in problems if p["form"] == "води" and p["check"] == "stress"]
    assert len(vody_problems) == 1, "Should deduplicate 'води' to a single problem entry"
    locs = vody_problems[0]["locations"]
    assert len(locs) == 3, f"Expected 3 locations for 'води', got {locs}"
    # Verify locations are [None, start, end]
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
    # All 4 words (замок, атлас, обід, орган) are ambiguous in stress
    res = check_text(items=items, checks=["stress"], max_findings=2)
    assert res.get("status") != "error"
    summary = res["summary"]
    assert summary["truncated"] is True
    assert summary["uncut_count"] >= 4
    total_findings = len(res["problems"]) + len(res["suspicions"])
    assert total_findings == 2

    # Deterministic order: item-A findings must precede item-B findings
    first_item_id = res["problems"][0]["locations"][0][0]
    second_item_id = res["problems"][1]["locations"][0][0]
    assert first_item_id == "item-A"
    assert second_item_id == "item-A"


# ── Synthetic Tests: Stress Chunking at 501 Forms ────────────────────────────


def test_synthetic_stress_chunk_501_forms():
    # Build 501 distinct multi-syllable synthetic Cyrillic words
    # e.g., 'слово000а' ... 'слово500а' (has multiple vowels)
    words = [f"балачка{i:03d}а" for i in range(501)]
    text = " ".join(words)

    with patch("scripts.verification.check_text.verify_stresses", wraps=__import__("scripts.verification.stress", fromlist=["verify_stresses"]).verify_stresses) as mock_stresses:
        res = check_text(text=text, checks=["stress"])
        assert res.get("status") != "error"
        # STRESS_BATCH_CAP is 500, so verify_stresses should be called twice (500 + 1)
        assert mock_stresses.call_count == 2
        first_call_len = len(mock_stresses.call_args_list[0][0][0])
        second_call_len = len(mock_stresses.call_args_list[1][0][0])
        assert first_call_len == STRESS_BATCH_CAP
        assert second_call_len == 1
        assert res["summary"]["unique_forms"] == 501


# ── Synthetic Tests: UA-GEC Whole Span vs Sub-Span ───────────────────────────


def test_synthetic_ua_gec_one_word_whole_span(tmp_path, monkeypatch):
    # Mock UA-GEC index with one 1-word error: 'коментарій' -> 'коментар'
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
    monkeypatch.setattr("scripts.verification.check_text._get_ua_gec_index", lambda: (mock_index, 1))

    text = "Мій коментарій важливий."
    res = check_text(text=text, checks=["ua_gec"])
    assert res.get("status") != "error"
    problems = res["problems"]
    assert len(problems) == 1
    p = problems[0]
    assert p["check"] == "ua_gec"
    assert p["form"] == "коментарій"
    assert p["detail"]["error_type"] == "F/Calque"
    assert p["detail"]["corrections"] == [{"correct": "коментар", "doc_ids": ["doc1"]}]


def test_synthetic_ua_gec_sub_span_not_matched(tmp_path, monkeypatch):
    # Mock UA-GEC index with 2-word error: 'написання постів' -> 'писати дописи'
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
    monkeypatch.setattr("scripts.verification.check_text._get_ua_gec_index", lambda: (mock_index, 2))

    # Text contains only the sub-span 'написання', NOT 'написання постів'
    text_subspan = "Триває написання нового твору."
    res_subspan = check_text(text=text_subspan, checks=["ua_gec"])
    assert len(res_subspan["problems"]) == 0, "Sub-span of longer UA-GEC error must NOT match"

    # Text contains the whole 2-word span: must match
    text_full = "Триває написання постів щодня."
    res_full = check_text(text=text_full, checks=["ua_gec"])
    assert len(res_full["problems"]) == 1
    assert res_full["problems"][0]["form"] == "написання постів"
    loc = res_full["problems"][0]["locations"][0]
    assert text_full[loc[1] : loc[2]] == "написання постів"


# ── Synthetic Tests: Shadow Score Signals in Suspicions Only ──────────────────


def test_synthetic_shadow_score_signals_appear_only_in_suspicions():
    # 'врач' has Russian confidence 1.0, but is NOT in KNOWN_SHADOW_LEMMAS or CURATED_CALQUES.
    # 'получити' IS in KNOWN_SHADOW_LEMMAS.
    text = "Мій лікар не врач, але треба получити квиток."
    res = check_text(text=text, checks=["russian_shadow"])
    assert res.get("status") != "error"

    problems = [p for p in res["problems"] if p["check"] == "russian_shadow"]
    suspicions = [s for s in res["suspicions"] if s["check"] == "russian_shadow"]

    problem_forms = {p["form"] for p in problems}
    suspicion_forms = {s["form"] for s in suspicions}

    assert "получити" in problem_forms, "Curated shadow must be in problems"
    assert "получити" not in suspicion_forms

    assert "врач" in suspicion_forms, "Score/heuristic shadow must be in suspicions"
    assert "врач" not in problem_forms, "Score/heuristic shadow must NEVER be in problems"

    # Check suspicion label
    vrach_suspicion = next(s for s in suspicions if s["form"] == "врач")
    assert vrach_suspicion["detail"]["label"] == "suspicion, not a verdict"
    assert vrach_suspicion["detail"]["curated"] is False


# ── Real Corpus Fixture Tests ────────────────────────────────────────────────


def _load_textbook_fixture() -> tuple[str, str] | None:
    sources_path = _sources_path()
    if not sources_path.is_file() or not Path(VESUM_DB_PATH).is_file():
        return None
    conn = sqlite3.connect(f"file:{sources_path}?mode=ro", uri=True)
    try:
        cur = conn.execute(
            "SELECT chunk_id, text FROM textbooks WHERE char_count > 4000 ORDER BY id LIMIT 10"
        )
        for cid, text in cur.fetchall():
            tokens = [t for t in tokenize(text) if t.kind not in SKIPPED_KINDS]
            if len(tokens) >= 600:
                return cid, text
    finally:
        conn.close()
    return None


def test_acceptance_textbook_fixture_correctness_and_planted():
    fixture = _load_textbook_fixture()
    if fixture is None:
        pytest.skip("data/sources.db or vesum.db not provisioned")
    chunk_id, original_text = fixture
    tokens = [t for t in tokenize(original_text) if t.kind not in SKIPPED_KINDS]
    assert len(tokens) >= 600, f"Chunk {chunk_id} has {len(tokens)} tokens, expected >= 600"

    # 1. Unmodified chunk check
    res_clean = check_text(text=original_text, checks=["vesum", "stress"])
    assert res_clean.get("status") != "error"

    # Invariant: forms that VESUM has (including sentence-initial capitals) must not yield no_vesum_row
    vesum_problems = {p["form"] for p in res_clean["problems"] if p["check"] == "vesum"}
    sent_init_caps = {t.lookup for t in tokens if t.sentence_initial and t.capitalised}
    for p_form in vesum_problems:
        # Check that this form is genuinely absent from VESUM
        direct = verify_words([p_form]).get(p_form, [])
        lower_retry = (
            verify_words([p_form[:1].lower() + p_form[1:]]).get(p_form[:1].lower() + p_form[1:], [])
            if p_form in sent_init_caps
            else []
        )
        assert not direct and not lower_retry, (
            f"Form {p_form!r} is attested in VESUM but was reported as no_vesum_row"
        )

    # Invariant: no monosyllable is flagged by stress
    stress_problems = {p["form"] for p in res_clean["problems"] if p["check"] == "stress"}
    ukrainian_vowels = frozenset("аеєиіїоуюяАЕЄИІЇОУЮЯ")
    for s_form in stress_problems:
        vowel_count = sum(1 for ch in s_form if ch in ukrainian_vowels)
        assert vowel_count >= 2, f"Monosyllable {s_form!r} was flagged by stress"

    # 2. Planted items:
    # Query VESUM to verify two absent forms
    planted_vesum_1 = "бзюкавий"
    planted_vesum_2 = "хряпочка"
    assert not verify_words([planted_vesum_1]).get(planted_vesum_1)
    assert not verify_words([planted_vesum_2]).get(planted_vesum_2)
    logger.info("Planted VESUM absent forms: %s, %s", planted_vesum_1, planted_vesum_2)

    # Query UA-GEC for an F/Calque row
    sources_path = _sources_path()
    conn = sqlite3.connect(f"file:{sources_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            "SELECT id, error, correct FROM ua_gec_errors WHERE error_type = 'F/Calque' AND length(error) > 5 LIMIT 1"
        )
        gec_row = cur.fetchone()
    finally:
        conn.close()

    assert gec_row is not None
    planted_gec_id = gec_row["id"]
    planted_gec_error = gec_row["error"]
    logger.info("Planted UA-GEC row id=%d, error=%s", planted_gec_id, planted_gec_error)

    # Plant into text
    # Plant absent 1 near start, absent 2 in middle, and gec_error inside a sentence
    modified_text = (
        f"{planted_vesum_1} було видно. "
        + original_text[:500]
        + f" Тут сталося {planted_gec_error}, і все. "
        + original_text[500:1000]
        + f" З'явилася {planted_vesum_2} раптом. "
        + original_text[1000:]
    )

    res_modified = check_text(text=modified_text, checks=["vesum", "ua_gec"])
    assert res_modified.get("status") != "error"

    problems = res_modified["problems"]

    # Verify planted VESUM 1
    p1 = next((p for p in problems if p["form"] == planted_vesum_1 and p["check"] == "vesum"), None)
    assert p1 is not None, f"Planted {planted_vesum_1} not detected"
    loc1 = p1["locations"][0]
    assert modified_text[loc1[1] : loc1[2]] == planted_vesum_1

    # Verify planted VESUM 2
    p2 = next((p for p in problems if p["form"] == planted_vesum_2 and p["check"] == "vesum"), None)
    assert p2 is not None, f"Planted {planted_vesum_2} not detected"
    loc2 = p2["locations"][0]
    assert modified_text[loc2[1] : loc2[2]] == planted_vesum_2

    # Verify planted UA-GEC
    p_gec = next((p for p in problems if p["check"] == "ua_gec" and planted_gec_error.lower() in p["form"].lower()), None)
    assert p_gec is not None, f"Planted UA-GEC error {planted_gec_error} not detected"
    loc_gec = p_gec["locations"][0]
    assert modified_text[loc_gec[1] : loc_gec[2]] == planted_gec_error


def test_speed_warm_call_under_2s():
    fixture = _load_textbook_fixture()
    if fixture is None:
        pytest.skip("data/sources.db or vesum.db not provisioned")
    chunk_id, text = fixture

    # Warm-up call (loads in-memory indices, caches)
    check_text(text=text)

    # Measured warm call with all four checks
    t0 = time.perf_counter()
    res = check_text(text=text)
    elapsed = time.perf_counter() - t0

    assert elapsed < 2.0, f"check_text warm call took {elapsed:.3f}s, expected < 2.0s"
    assert res.get("status") != "error"
    assert res["summary"]["tokens"] >= 600

    # Scripted comparison with previous multi-tool pattern:
    tokens = [t for t in tokenize(text) if t.kind not in SKIPPED_KINDS]
    unique_forms = list({t.lookup for t in tokens})

    # Individual calls that were previously required:
    # 1. verify_words (1 batch call)
    # 2. check_russian_shadow (1 call per unique form, schema takes one word)
    # 3. verify_stresses (1 batch call)
    # 4. search_ua_gec_errors (queries per phrase)
    simulated_calls = 1 + len(unique_forms) + 1 + 10  # ~ len(unique_forms) + 12 calls
    single_call = 1

    check_text_json = json.dumps(res, ensure_ascii=False)
    logger.info(
        "Performance comparison for chunk %s (%d tokens, %d unique forms):\n"
        "  - check_text: %d call, %.3fs, %d response chars\n"
        "  - legacy per-tool pattern: ~%d calls",
        chunk_id,
        len(tokens),
        len(unique_forms),
        single_call,
        elapsed,
        len(check_text_json),
        simulated_calls,
    )
