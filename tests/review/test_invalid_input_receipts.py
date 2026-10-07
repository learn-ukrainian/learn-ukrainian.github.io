"""Real Sources rejections cannot supply review or settle evidence (#9979)."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from scripts.review import settle
from scripts.review.receipts import ledger
from scripts.review.receipts.outcomes import classify_outcome, search_outcome
from tests.review.test_r1_schema_ledger import _run
from tests.review.test_r1_schema_ledger import server_module as server_module
from tests.review.test_settle import World
from tests.review.test_settle import world as world

# Denominator: REVIEW_TOOLS handlers that return invalid_input. Server wrappers
# delegate validation where noted; non-review handlers are deliberately excluded.
# .mcp/servers/sources/server.py:
# verify_word:2478, verify_words:2482, verify_lemma:2585 ->
# packages/v4-runtime/src/learn_ukrainian_v4_runtime/sources_handlers.py:140,182,222
# inspect_word:2595, inspect_words:2641, verify_stress:2684 ->
# sources_handlers.py:278 and scripts/verification/stress.py:425,529
# check_text:2766 -> scripts/verification/check_text.py:224-324
# query_sum20:3508, query_pravopys:3639
INVALID_INPUT_TOOLS = {
    "verify_word": "word",
    "verify_words": "words",
    "verify_lemma": "lemma",
    "inspect_word": "word",
    "inspect_words": "words",
    "verify_stress": "word",
    "check_text": "text",
    "query_sum20": "word",
    "query_pravopys": "topic",
}


def _result(server, tool, arguments):
    output = _run(getattr(server, f"handle_{tool}")(arguments))
    content = output[0] if isinstance(output, tuple) else output
    return "\n".join(item.text for item in content)


def _receipt(world: World, tool, result, arguments):
    return ledger.append(
        world.own_ledger,
        review_id="settle-R",
        attempt_id="settle-A",
        manifest_sha256=world.current_hash(),
        tool=tool,
        server_version="fixture",
        arguments=arguments,
        snapshots={},
        status="ok",
        result=result,
    )


@pytest.mark.parametrize("tool,key", INVALID_INPUT_TOOLS.items())
@pytest.mark.parametrize("case", ["missing", "empty", "null", "wrong_type"])
def test_real_invalid_input_is_rejected_and_never_settles(server_module, world, tool, key, case):
    assert tool in ledger.REVIEW_TOOLS
    if case == "missing":
        arguments = {}
    elif case == "empty":
        # check_text accepts empty text, but rejects an empty checks selector.
        arguments = {key: [] if key == "words" else ""}
        if tool == "check_text":
            arguments["checks"] = []
    else:
        arguments = {key: None if case == "null" else 42}
    result = _result(server_module, tool, arguments)
    assert "invalid_input" in result
    receipt = _receipt(world, tool, result, arguments)
    record = ledger.lookup(world.own_ledger, receipt)
    assert record["outcome_facts"] == {
        "call_status": "ok",
        "hits": 0,
        "status": "error",
        "unavailable": False,
    }
    assert search_outcome(record["status"], record["outcome_facts"]) == "error"
    evidence = [{"receipt": receipt, "quote": result}]
    for outcome in ("supported_defect", "refuted"):
        with pytest.raises(settle.SettleError, match="needs a cited receipt with hits"):
            settle.validate_reply(world.reply(outcome, evidence), world.manifest.read_bytes(), world.own_ledger)
    other_tool = "query_sum20" if tool == "query_pravopys" else "query_pravopys"
    other = world.call(other_tool, "Valid authority excerpt.")
    with pytest.raises(settle.SettleError, match="two different sources"):
        settle.validate_reply(
            world.reply("source_conflict", [*evidence, {"receipt": other, "quote": "Valid authority excerpt."}]),
            world.manifest.read_bytes(),
            world.own_ledger,
        )


@pytest.mark.parametrize("tool", ["verify_words", "inspect_words"])
@pytest.mark.parametrize("words", [[""], [" "], [42], ["fixture", None], "fixture"])
def test_real_malformed_batches_are_rejected(server_module, tool, words):
    facts = classify_outcome(tool, "ok", _result(server_module, tool, {"words": words}))
    assert facts["status"] == "error" and facts["hits"] == 0


@pytest.mark.parametrize("field", ["status", "error_code", "disposition"])
def test_structured_invalid_input_is_rejected(field):
    facts = classify_outcome("verify_stress", "ok", json.dumps({field: "invalid_input", "matches": [{}]}))
    assert facts["status"] == "error" and facts["hits"] == 0


@pytest.mark.parametrize("word", ["fixture", "two words", "слово слово", "слово!"])
def test_real_stress_oracle_rejection_summary_is_not_evidence(server_module, monkeypatch, word):
    from scripts.verification import stress

    monkeypatch.setattr(stress, "source_info", lambda: {})
    result = _result(server_module, "verify_stress", {"word": word})
    assert " — invalid_input:" in result
    facts = classify_outcome("verify_stress", "ok", result)
    assert facts["status"] == "error" and facts["hits"] == 0


@pytest.mark.parametrize("tool", INVALID_INPUT_TOOLS)
def test_populated_real_handlers_keep_their_outcomes(server_module, monkeypatch, tmp_path, tool):
    """Run server formatters with populated controlled stores, never live lookups."""
    import rag.source_query as queries
    from scripts.verification import check_text, vesum
    from wiki import sources_db

    rows = [{"lemma": "fixture", "pos": "noun", "tags": "noun"}]
    stress = {"status": "ok", "input": "fixture", "matches": [{"stressed_form": "fixture"}]}
    backend = SimpleNamespace(
        verify_word=lambda *_args: rows,
        verify_words=lambda *_args: {"fixture": rows},
        verify_lemma=lambda *_args: rows,
        verify_stress=lambda *_args: stress,
        source_version=lambda: "a" * 64,
    )
    monkeypatch.setattr(server_module.v4_handlers, "backend", lambda: backend)
    inspection = vesum.WordInspection("fixture", vesum.InspectionStatus.CLEAN, rows, [], [], [], "a" * 64, {})
    monkeypatch.setattr(vesum, "inspect_word", lambda *_args, **_kwargs: inspection)
    monkeypatch.setattr(vesum, "inspect_words", lambda *_args, **_kwargs: {"fixture": inspection})
    monkeypatch.setattr(
        sources_db,
        "query_sum20",
        lambda *_args: [
            {
                "stressed_headword": "fixture",
                "pos": "noun",
                "grammar": "noun",
                "attribution_label": "fixture",
                "official_url": "https://example.invalid",
                "source_record_id": "fixture",
                "retrieved_at": "fixture",
                "content_sha256": "a" * 64,
                "parser_version": "fixture",
                "status": "ok",
                "senses": [{"register_labels": [], "sense_order": 1, "definition": "Fixture definition."}],
                "citations": [],
            }
        ],
    )
    monkeypatch.setattr(
        queries,
        "pravopys_offline",
        lambda *_args: {
            "status": "ok",
            "text": "Fixture rule.",
            "title": "fixture",
            "section": 1,
            "locator": "fixture",
            "url": "https://example.invalid",
            "file_sha256": "a" * 64,
            "retrieved_at": "fixture",
            "section_path": [],
        },
    )
    # A controlled VESUM miss yields one real check_text problem.
    marker = tmp_path / "vesum-fixture"
    marker.touch()
    monkeypatch.setattr(check_text, "_vesum_path_resolved", lambda: marker)
    monkeypatch.setattr(check_text, "verify_words", lambda *_args, **_kwargs: {})
    arguments = {"word": "fixture", "words": ["fixture"], "lemma": "fixture", "topic": "fixture"}
    if tool == "verify_stress":
        arguments.pop("lemma")
    if tool == "check_text":
        arguments = {"text": "слово", "checks": ["vesum"]}
    facts = classify_outcome(tool, "ok", _result(server_module, tool, arguments))
    assert facts == {"call_status": "ok", "hits": 1, "status": "hits_found", "unavailable": False}


@pytest.mark.parametrize("tool", ["verify_word", "query_sum20", "query_pravopys", "search_text"])
def test_invalid_input_in_source_text_is_not_a_rejection(tool):
    facts = classify_outcome(tool, "ok", "Found source evidence quoting invalid_input: example.")
    assert facts["status"] == "hits_found" and facts["hits"] == 1
