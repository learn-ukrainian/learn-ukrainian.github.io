"""Structural settle contract: one decision, bounded own receipts, exact prompt."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator

from scripts.review import findings_db as db
from scripts.review import settle
from scripts.review.prompts.check import check_prompt
from scripts.review.prompts.eligibility import pin_refusals
from scripts.review.receipts import ledger
from tests.review.test_prompts import _setup_lesson_fixture
from yaml_activities import ActivityParser

pytestmark = pytest.mark.reads_content


@dataclass
class World:
    root: Path
    db_path: Path
    document: Path
    prior_ledger: Path
    manifest: Path
    prompt: Path
    own_ledger: Path
    item_id: int

    def current_hash(self) -> str:
        return hashlib.sha256(self.manifest.read_bytes()).hexdigest()

    def call(
        self,
        tool: str,
        result: str,
        *,
        hits: int = 1,
        status: str = "ok",
        arguments: dict[str, Any] | None = None,
        review_id: str = "settle-R",
        attempt_id: str = "settle-A",
    ) -> str:
        return ledger.append(
            self.own_ledger,
            review_id=review_id,
            attempt_id=attempt_id,
            manifest_sha256=self.current_hash(),
            tool=tool,
            server_version="fixture",
            arguments=arguments or {},
            snapshots={},
            status=status,
            result=result,
            outcome_facts={
                "call_status": "ok",
                "hits": hits,
                "status": "hits_found" if hits else "no_hits",
                "unavailable": False,
            },
        )

    def reply(
        self, outcome: str, evidence: list[dict[str, str]] | None = None, searches: list[dict[str, str]] | None = None
    ) -> bytes:
        return yaml.safe_dump(
            {
                "settle_schema": 1,
                "item_id": self.item_id,
                "review_id": "settle-R",
                "attempt_id": "settle-A",
                "manifest_sha256": self.current_hash(),
                "outcome": outcome,
                "reason": "The cited result addresses the sense in context.",
                "evidence": evidence or [],
                "broadened_searches": searches or [],
            },
            sort_keys=False,
        ).encode()


def _world(
    root: Path,
    document: Path,
    manifest_hash: str,
    *,
    quote: str = "construction",
    scope: dict[str, Any] | None = None,
    lesson_n: int | None = 2,
    kind: str | None = None,
    prepare: bool = True,
) -> World:
    database = root / "findings.sqlite"
    prior = root / "prior.jsonl"
    ledger.create_empty_ledger(prior)
    prior_id = ledger.append(
        prior,
        review_id="original-R",
        attempt_id="original-A",
        manifest_sha256=manifest_hash,
        tool="search_text",
        server_version="fixture",
        arguments={"query": quote},
        snapshots={},
        status="ok",
        result="No results found.",
        outcome_facts={"call_status": "ok", "hits": 0, "status": "no_hits", "unavailable": False},
    )
    finding = {
        "id": "F-1",
        "status": "active",
        "dimension": "language",
        "sub_dimension": "calque",
        "severity": "MINOR",
        "claim": "This construction may not fit the intended sense.",
        "locations": [] if scope is not None else [{"tab": "urok", "quote": quote}],
        "unsupported_by_source": {"searches": [{"receipt": prior_id, "outcome": "no_hits"}]},
    }
    if scope is not None:
        finding["scope"] = scope
    with db.connect(database) as conn, db.transaction(conn):
        db.insert_attempt(
            conn,
            {
                "review_id": "original-R",
                "attempt_id": "original-A",
                "kind": kind or ("plan" if lesson_n is None else "lesson"),
                "level": "a1",
                "slug": "fixture-module",
                "lesson_n": lesson_n,
                "manifest_sha256": manifest_hash,
                "reviewer_model": "fixture",
                "reviewer_family": "fixture",
                "harness": "fixture",
                "verdict": "APPROVE",
                "validated_at": "2026-09-25T00:00:00+00:00",
                "task_id": "fixture-task",
            },
        )
        db.insert_finding(conn, "original-R", "original-A", finding, layer=None, seed_id=None)
        item_id = db.open_settle_item(
            conn,
            ref="original-R/original-A/F-1",
            kind="unsupported_by_source",
            level="a1",
            slug="fixture-module",
            lesson_n=lesson_n,
            manifest_sha256=manifest_hash,
            opened_at="2026-09-25T00:00:00+00:00",
        )
    world = World(
        root,
        database,
        document,
        prior,
        root / "settle.manifest.yaml",
        root / "settle.prompt.md",
        root / "settle.jsonl",
        item_id,
    )
    if prepare:
        settle.prepare(
            item_id,
            db_path=database,
            document_path=document,
            prior_ledger=prior,
            review_id="settle-R",
            attempt_id="settle-A",
            manifest_path=world.manifest,
            prompt_path=world.prompt,
            repo_root=root,
        )
        ledger.create_empty_ledger(world.own_ledger)
    return world


@pytest.fixture
def world(tmp_path: Path) -> World:
    root = tmp_path
    document = root / "site/src/content/docs/a1/fixture-module/2.mdx"
    document.parent.mkdir(parents=True)
    document.write_text("In context this construction expresses the intended sense.\n", encoding="utf-8")
    module_list = root / "curriculum/l2-uk-en/curriculum.yaml"
    module_list.parent.mkdir(parents=True)
    module_list.write_text(
        yaml.safe_dump({"levels": {"a1": {"type": "core", "modules": ["fixture-module"]}}}), encoding="utf-8"
    )
    return _world(root, document, "a" * 64)


def _evidence(
    world: World, tool: str = "query_pravopys", *, hits: int = 1, result: str = "Rule excerpt."
) -> list[dict[str, str]]:
    return [{"receipt": world.call(tool, result, hits=hits), "quote": result}]


@pytest.mark.parametrize("outcome", ["refuted", "supported_defect"])
def test_sourced_outcomes_accept_a_hit_receipt(world: World, outcome: str) -> None:
    result, receipts = settle.validate_reply(
        world.reply(outcome, _evidence(world)), world.manifest.read_bytes(), world.own_ledger
    )
    assert result == outcome and len(receipts) == 1


@pytest.mark.parametrize("outcome", ["refuted", "supported_defect"])
def test_sourced_outcomes_refuse_no_hit(world: World, outcome: str) -> None:
    with pytest.raises(settle.SettleError, match="needs a cited receipt with hits"):
        settle.validate_reply(
            world.reply(outcome, _evidence(world, hits=0)), world.manifest.read_bytes(), world.own_ledger
        )


def test_source_conflict_accepts_two_distinct_authorities(world: World) -> None:
    evidence = _evidence(world, "query_pravopys") + _evidence(world, "query_sum20", result="Dictionary excerpt.")
    assert (
        settle.validate_reply(world.reply("source_conflict", evidence), world.manifest.read_bytes(), world.own_ledger)[
            0
        ]
        == "source_conflict"
    )


def test_source_conflict_refuses_two_calls_to_one_authority(world: World) -> None:
    evidence = _evidence(world, "inspect_word") + _evidence(world, "verify_words", result="Second analysis.")
    with pytest.raises(settle.SettleError, match="two different sources"):
        settle.validate_reply(world.reply("source_conflict", evidence), world.manifest.read_bytes(), world.own_ledger)


def test_source_conflict_refuses_a_second_source_without_hits(world: World) -> None:
    evidence = _evidence(world, "query_pravopys") + _evidence(world, "query_sum20", hits=0, result="No entry.")
    with pytest.raises(settle.SettleError, match="two different sources"):
        settle.validate_reply(world.reply("source_conflict", evidence), world.manifest.read_bytes(), world.own_ledger)


def _broadened(
    world: World, *, result: str | None = None, status: str = "ok", category_only: str | None = None
) -> list[dict[str, str]]:
    calls = [
        ("lemma", "inspect_word", {}),
        ("construction", "search_style_guide", {}),
        ("style_prose", "search_text", {"source_file": "antonenko-davydovych-yak-my-hovorymo"}),
        ("ua_gec_context", "search_ua_gec_errors", {}),
        ("grac", "query_grac", {}),
        ("pravopys", "query_pravopys", {}),
        ("counterevidence", "query_sum20", {}),
    ]
    searches = []
    for category, tool, arguments in calls:
        selected = category_only is None or category == category_only
        text = result if selected and result is not None else f"{category}: no results"
        searches.append(
            {
                "category": category,
                "receipt": world.call(tool, text, hits=0, arguments=arguments, status=status if selected else "ok"),
                "quote": text,
            }
        )
    return searches


def test_unresolved_accepts_each_broadened_search(world: World) -> None:
    reply = world.reply("unresolved", searches=_broadened(world))
    result, receipts = settle.validate_reply(reply, world.manifest.read_bytes(), world.own_ledger)
    assert result == "unresolved" and len(receipts) == 7


@pytest.mark.parametrize("result", ["No results found.", "Successful source excerpt."])
def test_unresolved_accepts_successful_broadened_receipts(world: World, result: str) -> None:
    searches = _broadened(world, result=result)
    outcome, receipts = settle.validate_reply(
        world.reply("unresolved", searches=searches), world.manifest.read_bytes(), world.own_ledger
    )
    assert outcome == "unresolved"
    assert receipts == [search["receipt"] for search in searches]


@pytest.mark.parametrize("category_only", [None, *settle.SEARCH_TOOLS])
@pytest.mark.parametrize(
    "status,result,classified_status",
    [
        ("ok", "invalid_input: empty query", "error"),
        ("ok", '{"status": "invalid_input"}', "error"),
        ("ok", '{"error_code": "invalid_input"}', "error"),
        ("ok", '{"disposition": "invalid_input"}', "error"),
        ("error", "Sources call failed.", "error"),
        ("refused", "Sources call refused.", "refused"),
        ("ok", '{"status": "unavailable"}', "unavailable"),
    ],
)
def test_unresolved_refuses_unsuccessful_broadened_receipts(
    world: World, category_only: str | None, status: str, result: str, classified_status: str
) -> None:
    # World.call deliberately supplies no-hit facts: classify the stored call,
    # rather than trusting stale or caller-supplied outcome_facts.
    searches = _broadened(world, result=result, status=status, category_only=category_only)
    category = category_only or "lemma"
    with pytest.raises(
        settle.SettleError, match=f"broadened_search_call_unsuccessful: {category}: {classified_status}"
    ):
        settle.validate_reply(
            world.reply("unresolved", searches=searches), world.manifest.read_bytes(), world.own_ledger
        )


def test_unresolved_refuses_missing_broadened_search(world: World) -> None:
    with pytest.raises(settle.SettleError, match="every required broadened search"):
        settle.validate_reply(
            world.reply("unresolved", searches=_broadened(world)[:-1]), world.manifest.read_bytes(), world.own_ledger
        )


def test_unresolved_refuses_wrong_tool_and_duplicate_receipt(world: World) -> None:
    searches = _broadened(world)
    searches[0]["receipt"] = searches[1]["receipt"]
    searches[0]["quote"] = searches[1]["quote"]
    with pytest.raises(settle.SettleError, match="duplicated or uses the wrong tool"):
        settle.validate_reply(
            world.reply("unresolved", searches=searches), world.manifest.read_bytes(), world.own_ledger
        )


def test_unresolved_refuses_style_search_without_the_prose_source(world: World) -> None:
    searches = _broadened(world)
    replacement = world.call("search_text", "other style result", hits=0, arguments={"source_file": "other"})
    searches[2] = {"category": "style_prose", "receipt": replacement, "quote": "other style result"}
    with pytest.raises(settle.SettleError, match="contract's source_file"):
        settle.validate_reply(
            world.reply("unresolved", searches=searches), world.manifest.read_bytes(), world.own_ledger
        )


def test_return_has_exactly_one_outcome_and_unique_yaml_keys(world: World) -> None:
    valid = world.reply("refuted", _evidence(world))
    assert settle.validate_reply(valid, world.manifest.read_bytes(), world.own_ledger)[0] == "refuted"
    with pytest.raises(settle.SettleError, match="exactly the settle return fields"):
        settle.validate_reply(valid + b"other_outcome: unresolved\n", world.manifest.read_bytes(), world.own_ledger)
    with pytest.raises(settle.SettleError, match="duplicate reply key"):
        settle.validate_reply(valid + b"outcome: unresolved\n", world.manifest.read_bytes(), world.own_ledger)


def test_receipts_must_belong_to_this_ledger_and_quotes_to_result(world: World) -> None:
    evidence = _evidence(world)
    assert (
        settle.validate_reply(world.reply("refuted", evidence), world.manifest.read_bytes(), world.own_ledger)[0]
        == "refuted"
    )
    wrong = [{"receipt": "rr-outside", "quote": "Rule excerpt."}]
    with pytest.raises(settle.SettleError, match="outside this settle attempt ledger"):
        settle.validate_reply(world.reply("refuted", wrong), world.manifest.read_bytes(), world.own_ledger)
    wrong_quote = [{**evidence[0], "quote": "invented quote"}]
    with pytest.raises(settle.SettleError, match="not in the stored receipt result"):
        settle.validate_reply(world.reply("refuted", wrong_quote), world.manifest.read_bytes(), world.own_ledger)


def test_foreign_attempt_receipt_is_refused_even_in_the_same_file(world: World) -> None:
    world.call("query_pravopys", "Foreign result.", review_id="other-R")
    with pytest.raises(settle.SettleError, match="another settle attempt"):
        settle.validate_reply(world.reply("refuted", _evidence(world)), world.manifest.read_bytes(), world.own_ledger)


def test_call_budget_is_loaded_and_enforced(world: World, tmp_path: Path) -> None:
    params = yaml.safe_load(db.PARAMETERS_PATH.read_text(encoding="utf-8"))
    params["settle_call_budget"]["value"] = 2
    custom = tmp_path / "parameters.yaml"
    custom.write_text(yaml.safe_dump(params), encoding="utf-8")
    settle.prepare(
        world.item_id,
        db_path=world.db_path,
        document_path=world.document,
        prior_ledger=world.prior_ledger,
        review_id="settle-R",
        attempt_id="settle-A",
        manifest_path=world.manifest,
        prompt_path=world.prompt,
        repo_root=world.root,
        parameters_path=custom,
    )
    assert yaml.safe_load(world.manifest.read_text())["call_budget"] == 2
    assert "Sources call budget: 2" in world.prompt.read_text()
    evidence = _evidence(world)
    world.call("query_sum20", "Second result.")
    assert (
        settle.validate_reply(world.reply("refuted", evidence), world.manifest.read_bytes(), world.own_ledger)[0]
        == "refuted"
    )
    world.call("query_grac", "Third result.")
    with pytest.raises(settle.SettleError, match="call budget exceeded"):
        settle.validate_reply(world.reply("refuted", evidence), world.manifest.read_bytes(), world.own_ledger)


@pytest.mark.parametrize(
    "outcome,operator", [("refuted", 0), ("supported_defect", 0), ("source_conflict", 1), ("unresolved", 1)]
)
def test_record_closes_item_or_marks_operator_and_refuses_second_attempt(
    world: World, outcome: str, operator: int
) -> None:
    if outcome == "unresolved":
        reply = world.reply(outcome, searches=_broadened(world))
    elif outcome == "source_conflict":
        reply = world.reply(outcome, _evidence(world) + _evidence(world, "query_sum20", result="Other source."))
    else:
        reply = world.reply(outcome, _evidence(world))
    reply_path = world.root / "seat-reply.yaml"
    reply_path.write_bytes(reply)
    assert (
        settle.record(
            reply_path,
            manifest_path=world.manifest,
            ledger_path=world.own_ledger,
            db_path=world.db_path,
            decided_by="language-seat",
            repo_root=world.root,
        )
        == outcome
    )
    with db.connect(world.db_path) as conn:
        row = conn.execute("SELECT * FROM settle_items WHERE item_id = ?", (world.item_id,)).fetchone()
        assert row["outcome"] == outcome and row["needs_operator"] == operator
        assert row["receipts_json"] and row["decided_by"] == "language-seat"
    saved = world.root / "curriculum/l2-uk-en/evidence/a1/_state/fixture-module" / f"settle-{world.item_id}.reply.yaml"
    assert saved.read_bytes() == reply
    with pytest.raises(db.SettleAlreadyDecided):
        settle.record(
            reply_path,
            manifest_path=world.manifest,
            ledger_path=world.own_ledger,
            db_path=world.db_path,
            decided_by="language-seat",
            repo_root=world.root,
        )


def test_a_competing_identical_retry_that_loses_the_database_race_leaves_the_saved_reply_intact(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Codex's #8774 r5 reproduction: this call finds the reply already saved, then loses the database race.

    A competing recorder saves the byte-identical reply and wins ``record_settle_outcome`` in the
    gap between this call's own ``_save_exclusive`` (which finds the file already there, matching
    bytes, and is let through) and its own ``record_settle_outcome`` (which then raises
    ``SettleAlreadyDecided``, since the competing recorder committed first). The exception cleanup
    must know this call did not create ``saved`` and leave the competing recorder's file alone,
    instead of deleting the only saved copy of the decided outcome's reply.
    """
    reply = world.reply("refuted", _evidence(world))
    reply_path = world.root / "seat-reply.yaml"
    reply_path.write_bytes(reply)
    saved = world.root / "curriculum/l2-uk-en/evidence/a1/_state/fixture-module" / f"settle-{world.item_id}.reply.yaml"
    saved.parent.mkdir(parents=True, exist_ok=True)
    settle._save_exclusive(saved, reply)  # the competing recorder already saved the identical reply

    real_record_outcome = db.record_settle_outcome

    def competing_write_lands_first(
        conn: Any, item_id: int, outcome: str, receipts: list[str], decided_by: str, **kwargs: Any
    ) -> None:
        with db.connect(world.db_path) as other_conn:  # the competing recorder's own connection, committing first
            real_record_outcome(other_conn, item_id, outcome, receipts, "the-competing-seat", **kwargs)
        real_record_outcome(conn, item_id, outcome, receipts, decided_by, **kwargs)

    monkeypatch.setattr(settle.db, "record_settle_outcome", competing_write_lands_first)

    with pytest.raises(db.SettleAlreadyDecided):
        settle.record(
            reply_path,
            manifest_path=world.manifest,
            ledger_path=world.own_ledger,
            db_path=world.db_path,
            decided_by="language-seat",
            repo_root=world.root,
        )

    assert saved.exists(), "the cleanup deleted the competing recorder's saved reply"
    assert saved.read_bytes() == reply
    with db.connect(world.db_path) as conn:
        row = conn.execute(
            "SELECT outcome, decided_by FROM settle_items WHERE item_id = ?", (world.item_id,)
        ).fetchone()
        assert row["outcome"] == "refuted" and row["decided_by"] == "the-competing-seat"  # the winner's


def test_the_call_that_created_the_saved_reply_and_then_lost_the_database_race_leaves_it_intact(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The opposite ordering from the reproduction above (#8774 r7).

    Here no reply is saved yet, so this call's own ``_save_exclusive`` is the one that creates
    ``saved`` (``created`` is True). A competing recorder with a byte-identical reply then wins
    ``record_settle_outcome`` before this call's own write reaches the database, so this call's
    write raises ``SettleAlreadyDecided``. Because ``created`` is True for this call, cleanup that
    keys off ``created`` alone unlinks the file the winner's decision relies on — the file is the
    reply of record regardless of which of the two identical-bytes calls happened to create it.
    """
    reply = world.reply("refuted", _evidence(world))
    reply_path = world.root / "seat-reply.yaml"
    reply_path.write_bytes(reply)
    saved = world.root / "curriculum/l2-uk-en/evidence/a1/_state/fixture-module" / f"settle-{world.item_id}.reply.yaml"
    assert not saved.exists()  # this call's own _save_exclusive will be the one to create it

    real_record_outcome = db.record_settle_outcome

    def competing_write_lands_first(
        conn: Any, item_id: int, outcome: str, receipts: list[str], decided_by: str, **kwargs: Any
    ) -> None:
        with db.connect(world.db_path) as other_conn:  # the competing recorder's own connection, committing first
            real_record_outcome(other_conn, item_id, outcome, receipts, "the-competing-seat", **kwargs)
        real_record_outcome(conn, item_id, outcome, receipts, decided_by, **kwargs)

    monkeypatch.setattr(settle.db, "record_settle_outcome", competing_write_lands_first)

    with pytest.raises(db.SettleAlreadyDecided):
        settle.record(
            reply_path,
            manifest_path=world.manifest,
            ledger_path=world.own_ledger,
            db_path=world.db_path,
            decided_by="language-seat",
            repo_root=world.root,
        )

    assert saved.exists(), "the cleanup deleted the reply this call created, which the winner's decision relies on"
    assert saved.read_bytes() == reply
    with db.connect(world.db_path) as conn:
        row = conn.execute(
            "SELECT outcome, decided_by FROM settle_items WHERE item_id = ?", (world.item_id,)
        ).fetchone()
        assert row["outcome"] == "refuted" and row["decided_by"] == "the-competing-seat"  # the winner's


def test_record_retries_after_an_interruption_between_the_save_and_the_outcome(world: World) -> None:
    reply = world.reply("refuted", _evidence(world))
    reply_path = world.root / "seat-reply.yaml"
    reply_path.write_bytes(reply)
    saved = world.root / "curriculum/l2-uk-en/evidence/a1/_state/fixture-module" / f"settle-{world.item_id}.reply.yaml"
    saved.parent.mkdir(parents=True, exist_ok=True)
    settle._save_exclusive(saved, reply)  # the earlier run saved the reply, then was terminated before recording
    with db.connect(world.db_path) as conn:
        row = conn.execute("SELECT outcome FROM settle_items WHERE item_id = ?", (world.item_id,)).fetchone()
        assert row["outcome"] is None
    assert (
        settle.record(
            reply_path,
            manifest_path=world.manifest,
            ledger_path=world.own_ledger,
            db_path=world.db_path,
            decided_by="language-seat",
            repo_root=world.root,
        )
        == "refuted"
    )
    with db.connect(world.db_path) as conn:
        row = conn.execute("SELECT * FROM settle_items WHERE item_id = ?", (world.item_id,)).fetchone()
        assert row["outcome"] == "refuted" and row["decided_by"] == "language-seat"
    assert saved.read_bytes() == reply


def test_record_refuses_a_retry_whose_reply_bytes_differ_from_the_one_already_saved(world: World) -> None:
    reply = world.reply("refuted", _evidence(world))
    other_reply = world.reply("supported_defect", _evidence(world, "query_pravopys"))
    reply_path = world.root / "seat-reply.yaml"
    reply_path.write_bytes(reply)
    saved = world.root / "curriculum/l2-uk-en/evidence/a1/_state/fixture-module" / f"settle-{world.item_id}.reply.yaml"
    saved.parent.mkdir(parents=True, exist_ok=True)
    settle._save_exclusive(saved, other_reply)  # a different reply is already on disk for this item
    with pytest.raises(settle.SettleError, match="a different reply is already saved"):
        settle.record(
            reply_path,
            manifest_path=world.manifest,
            ledger_path=world.own_ledger,
            db_path=world.db_path,
            decided_by="language-seat",
            repo_root=world.root,
        )
    with db.connect(world.db_path) as conn:
        row = conn.execute("SELECT outcome FROM settle_items WHERE item_id = ?", (world.item_id,)).fetchone()
        assert row["outcome"] is None
    assert saved.read_bytes() == other_reply  # untouched: the retry was refused, not allowed to overwrite it


def test_prepare_refuses_missing_span_and_foreign_document(world: World) -> None:
    foreign = world.root / "site/src/content/docs/a1/other-module/2.mdx"
    foreign.parent.mkdir(parents=True)
    foreign.write_text("construction", encoding="utf-8")
    with pytest.raises(settle.SettleError, match="expected"):
        settle.prepare(
            world.item_id,
            db_path=world.db_path,
            document_path=foreign,
            prior_ledger=world.prior_ledger,
            review_id="settle-R",
            attempt_id="settle-A",
            manifest_path=world.manifest,
            prompt_path=world.prompt,
            repo_root=world.root,
        )
    world.document.write_text("The quote is no longer here.", encoding="utf-8")
    with pytest.raises(settle.SettleError, match="disputed quote is absent"):
        settle.prepare(
            world.item_id,
            db_path=world.db_path,
            document_path=world.document,
            prior_ledger=world.prior_ledger,
            review_id="settle-R",
            attempt_id="settle-A",
            manifest_path=world.manifest,
            prompt_path=world.prompt,
            repo_root=world.root,
        )


def test_repeated_quote_exposes_each_context_to_the_seat() -> None:
    finding = {"locations": [{"tab": "urok", "quote": "construction"}]}
    spans = settle._context("first construction here. Second construction there.", finding)
    assert [span["occurrence"] for span in spans] == [1, 2]
    assert all(span["quote"] == "construction" for span in spans)


def test_settle_manifest_requires_its_pinned_document(world: World) -> None:
    manifest = yaml.safe_load(world.manifest.read_text())
    assert not pin_refusals(manifest, world.root)
    manifest["inputs"].clear()
    assert pin_refusals(manifest, world.root)[0].code == "manifest_schema_invalid"


def test_record_refuses_document_changed_since_prepare(world: World) -> None:
    reply = world.root / "seat-reply.yaml"
    reply.write_bytes(world.reply("refuted", _evidence(world)))
    world.document.write_text(world.document.read_text() + "Changed.\n")
    with pytest.raises(settle.SettleError, match="document changed"):
        settle.record(
            reply,
            manifest_path=world.manifest,
            ledger_path=world.own_ledger,
            db_path=world.db_path,
            decided_by="language-seat",
            repo_root=world.root,
        )


def test_rendered_prompt_from_real_engine_fixture_passes_checker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_manifest, _doc, digest = _setup_lesson_fixture(tmp_path, monkeypatch, lesson_n=2)
    document = tmp_path / "site/src/content/docs/a1/fixture-module/2.mdx"
    text = document.read_text(encoding="utf-8")
    quote = re.search(r"[A-Za-z]{5,}", text)
    assert quote is not None
    world = _world(tmp_path, document, hashlib.sha256(source_manifest.read_bytes()).hexdigest(), quote=quote.group())
    prompt = world.prompt.read_text(encoding="utf-8")
    sidecar = world.prompt.with_name(world.prompt.name + ".sha256")
    assert hashlib.sha256(prompt.encode()).hexdigest() == sidecar.read_text().strip()
    checked = check_prompt(prompt, world.manifest, repo_root=tmp_path, recorded_sha256=sidecar.read_text().strip())
    assert checked.passed, checked.errors
    assert not pin_refusals(yaml.safe_load(world.manifest.read_text()), tmp_path)
    assert digest


def test_no_cyrillic_typed_in_new_code_template_or_fixture() -> None:
    root = Path(__file__).resolve().parents[2]
    for path in (root / "scripts/review/settle.py", root / "scripts/review/prompts/settle.md.j2", Path(__file__)):
        assert re.search(r"[\u0400-\u04ff]", path.read_text(encoding="utf-8")) is None, path


# A lesson page: two activities inside Exercises, and the neighbouring Lesson and Vocabulary tabs.
_LESSON = (
    '<Tabs syncKey="module-tab">\n'
    '<TabItem label="Lesson">\n'
    "ONLY THE LESSON TAB\n"
    "</TabItem>\n"
    '<TabItem label="Activities">\n'
    '<span id="a1"></span>\n'
    "\n"
    "### First activity\n"
    "\n"
    "ONLY ACTIVITY A1\n"
    "\n"
    '<span id="a2"></span>\n'
    "\n"
    "### Second activity\n"
    "\n"
    "ONLY ACTIVITY A2\n"
    "</TabItem>\n"
    '<TabItem label="Vocabulary">\n'
    "ONLY THE VOCABULARY TAB\n"
    "</TabItem>\n"
    "</Tabs>\n"
)
_ACTIVITY_A1 = '<span id="a1"></span>\n\n### First activity\n\nONLY ACTIVITY A1\n\n'
_PLAN = """\
lessons:
  - n: 1
    title: Lesson one
    steps:
      - id: s1
        teach: first step only
      - id: s2
        teach: second step only
    activities:
      - id: a1
        focus: first activity
      - id: a2
        focus: second activity
  - n: 2
    title: Lesson two
    steps:
      - id: s1
        teach: other lesson step
"""
_LESSON_ONE = "\n".join(
    [
        "1",
        "Lesson one",
        "s1",
        "first step only",
        "s2",
        "second step only",
        "a1",
        "first activity",
        "a2",
        "second activity",
    ]
)
_QUOTED_STEP = (
    "Read the disputed construction in its quoted context and identify the sense actually used. "
    "If the same quote occurs more than once, compare every numbered context with the finding's location; "
    "if that still leaves the sense ambiguous, return `unresolved`."
)
_QUOTED_PROCEDURE = (
    _QUOTED_STEP,
    "2. Broaden the search to the lemma and the construction. Search style-guide prose through `search_text` with "
    "`source_file` set. Search UA-GEC and fetch the sentence context of a relevant result. Query live GRAC where "
    "available and Pravopys. Record unavailable results as unavailable, never as an empty search.",
    "3. Search for counterevidence as hard as for support. A corpus or error pair about a different construction does "
    "not establish this finding. A matching, unmarked VESUM analysis in this sense cannot be flagged on preference "
    "alone unless Pravopys or the style guide marks it. No unfamiliar word is called a Russianism without the "
    "heritage check.",
    "4. State your judgment in the reply. For `refuted`, explain why a cited source attests this construction "
    "**in this sense**. For `supported_defect`, identify positive evidence of the norm that the construction departs "
    "from. For `source_conflict`, cite two different authorities and send it to the operator. For `unresolved`, cite "
    "the complete broadened search record and send it to the operator. Do not change learner content yourself.",
    "Include `reason` explaining the sense and what the quoted results establish.",
    'reason: "Explain the source judgment in this sense, with no invented facts."',
)
_ABSENCE_STEP = (
    "Read the scoped unit below. The dispute is about something missing from that unit. "
    "Name what the scoped unit lacks."
)
_ABSENCE_PROCEDURE = (
    _ABSENCE_STEP,
    "2. Find which source says it should be in the unit.",
    "which source says it should be there, and what you found in the unit.",
    "Include `reason` naming what the scoped unit lacks, which source says it should be there, and what you found "
    "in the unit.",
    'reason: "Name what the scoped unit lacks, which source says it should be there, and what you found in the unit."',
)
_ABSENCE_LINE = "The dispute is about something missing from this unit."


def _prepared_spans(world: World) -> list[dict[str, Any]]:
    manifest = yaml.safe_load(world.manifest.read_text(encoding="utf-8"))
    loaded = yaml.safe_load(manifest["disputed_spans_text"])
    assert isinstance(loaded, list)
    return loaded


def test_a_lesson_absence_scoped_to_a_tab_is_that_tab_alone() -> None:
    spans = settle._context(_LESSON, {"locations": [], "scope": {"tab": "urok"}})
    assert spans == [{"absence": True, "locator": {"tab": "urok"}, "context": "\nONLY THE LESSON TAB\n"}]
    assert "ONLY ACTIVITY A1" not in spans[0]["context"]
    assert "ONLY THE VOCABULARY TAB" not in spans[0]["context"]

    workbook = settle._context(_LESSON, {"locations": [], "scope": {"tab": "vpravy"}})
    assert "ONLY ACTIVITY A1" in workbook[0]["context"]
    assert "ONLY ACTIVITY A2" in workbook[0]["context"]
    assert "ONLY THE LESSON TAB" not in workbook[0]["context"]
    assert "ONLY THE VOCABULARY TAB" not in workbook[0]["context"]


def test_engine_tab_labels_resolve_to_the_same_tab() -> None:
    lesson = "\u0423\u0440\u043e\u043a"
    workbook = "\u0417\u043e\u0448\u0438\u0442"
    document = (
        f'<TabItem label="{lesson} \u2014 Lesson">\nONLY THE LESSON TAB\n</TabItem>\n'
        f'<TabItem label="{workbook}">\nONLY THE WORKBOOK\n</TabItem>\n'
    )
    lesson_span = settle._context(document, {"locations": [], "scope": {"tab": "urok"}})
    workbook_span = settle._context(document, {"locations": [], "scope": {"tab": "vpravy"}})
    assert lesson_span[0]["context"] == "\nONLY THE LESSON TAB\n"
    assert "ONLY THE WORKBOOK" not in lesson_span[0]["context"]
    assert workbook_span[0]["context"] == "\nONLY THE WORKBOOK\n"
    assert "ONLY THE LESSON TAB" not in workbook_span[0]["context"]


def test_a_lesson_absence_scoped_to_an_activity_is_that_block_alone() -> None:
    spans = settle._context(_LESSON, {"locations": [], "scope": {"tab": "vpravy", "activity": "a1"}})
    assert spans == [
        {
            "absence": True,
            "locator": {"tab": "vpravy", "activity": "a1"},
            "context": _ACTIVITY_A1,
        }
    ]
    assert "ONLY ACTIVITY A2" not in spans[0]["context"]
    assert "### Second activity" not in spans[0]["context"]
    assert "ONLY THE LESSON TAB" not in spans[0]["context"]

    headed = '<TabItem label="vpravy">\n### a1\n\nONLY HEADING A1\n\n### a2\n\nONLY HEADING A2\n</TabItem>\n'
    with pytest.raises(settle.SettleError, match="scope names a unit absent from the document"):
        settle._context(headed, {"locations": [], "scope": {"tab": "vpravy", "activity": "a1"}})


def test_a_plan_absence_is_that_plan_unit_alone() -> None:
    cases = [
        (
            {"lesson": 1, "step": "s1"},
            "s1\nfirst step only",
            ("second step only", "first activity", "other lesson step"),
        ),
        ({"lesson": 1, "activity": "a1"}, "a1\nfirst activity", ("second activity", "first step only", "Lesson two")),
        ({"lesson": 1}, _LESSON_ONE, ("Lesson two", "other lesson step")),
    ]
    for scope, expected, excluded in cases:
        spans = settle._context(_PLAN, {"locations": [], "scope": scope})
        assert spans == [{"absence": True, "locator": scope, "context": expected}], scope
        assert all(text not in spans[0]["context"] for text in excluded), scope


def test_an_absence_without_a_resolvable_scope_fails_closed() -> None:
    for finding in (
        {"locations": []},
        {"locations": [], "scope": {}},
        {"locations": [], "scope": {"lesson": 1, "step": "s1", "activity": "a1"}},
        {"locations": [], "scope": {"tab": ""}},
    ):
        with pytest.raises(settle.SettleError, match="finding has no quoted disputed span"):
            settle._context(_PLAN, finding)


@pytest.mark.parametrize(
    "document,scope",
    [
        (_LESSON, {"tab": "no-such-tab"}),
        (_LESSON, {"tab": "urok", "activity": "a1"}),
        (_LESSON, {"tab": "vpravy", "activity": "a404"}),
        (_PLAN, {"lesson": 9}),
        (_PLAN, {"lesson": 1, "step": "s404"}),
        (_PLAN, {"lesson": 1, "activity": "a404"}),
        (_PLAN, {"tab": "urok"}),
    ],
)
def test_a_scope_that_names_a_missing_unit_fails_closed(document: str, scope: dict[str, Any]) -> None:
    with pytest.raises(settle.SettleError, match="scope names a unit absent from the document"):
        settle._context(document, {"locations": [], "scope": scope})


def test_two_tabs_with_one_key_fail_closed() -> None:
    document = '<TabItem label="urok">\nONE\n</TabItem>\n<TabItem label="Lesson">\nTWO\n</TabItem>\n'
    with pytest.raises(settle.SettleError, match="scope names more than one unit in the document"):
        settle._context(document, {"locations": [], "scope": {"tab": "urok"}})


def test_rendered_settle_prompt_for_an_absence_item_shows_the_scoped_unit(tmp_path: Path) -> None:
    document = tmp_path / "site/src/content/docs/a1/fixture-module/2.mdx"
    document.parent.mkdir(parents=True)
    document.write_text(_LESSON, encoding="utf-8")
    module_list = tmp_path / "curriculum/l2-uk-en/curriculum.yaml"
    module_list.parent.mkdir(parents=True)
    module_list.write_text(
        yaml.safe_dump({"levels": {"a1": {"type": "core", "modules": ["fixture-module"]}}}), encoding="utf-8"
    )
    manifest_hash = _pin_provenance(tmp_path, _provenance([_span(text="ONLY ACTIVITY A1")]), direct=True)
    world = _world(tmp_path, document, manifest_hash, scope={"tab": "vpravy", "activity": "a1"})
    assert _prepared_spans(world) == [
        {"absence": True, "locator": {"tab": "vpravy", "activity": "a1"}, "context": _ACTIVITY_A1}
    ]
    prompt = world.prompt.read_text(encoding="utf-8")
    instructions = prompt.split("## Original Finding (Data)", 1)[0]
    assert all(line in instructions for line in _ABSENCE_PROCEDURE)
    assert all(line not in instructions for line in _QUOTED_PROCEDURE)
    assert _ABSENCE_LINE in prompt
    assert "## Scoped Unit (Data)" in prompt
    assert "ONLY ACTIVITY A1" in prompt
    assert "ONLY ACTIVITY A2" not in prompt
    assert "ONLY THE LESSON TAB" not in prompt
    assert "ONLY THE VOCABULARY TAB" not in prompt
    assert "## Disputed Span In Context (Data)" not in prompt
    sidecar = world.prompt.with_name(world.prompt.name + ".sha256")
    checked = check_prompt(prompt, world.manifest, repo_root=tmp_path, recorded_sha256=sidecar.read_text().strip())
    assert checked.passed, checked.errors


def test_prepare_scopes_a_plan_absence_finding_to_that_plan_unit(tmp_path: Path) -> None:
    document = tmp_path / "curriculum/l2-uk-en/lesson-plans/a1/fixture-module.yaml"
    document.parent.mkdir(parents=True)
    document.write_text(_PLAN, encoding="utf-8")
    world = _world(tmp_path, document, "c" * 64, scope={"lesson": 1, "step": "s1"}, lesson_n=None)
    assert _prepared_spans(world) == [
        {"absence": True, "locator": {"lesson": 1, "step": "s1"}, "context": "s1\nfirst step only"}
    ]
    prompt = world.prompt.read_text(encoding="utf-8")
    assert "first step only" in prompt
    assert "second step only" not in prompt
    assert "other lesson step" not in prompt
    assert _ABSENCE_LINE in prompt


def test_the_quoted_span_and_its_prompt_stay_unchanged(world: World) -> None:
    spans = settle._context(_LESSON, {"locations": [{"tab": "urok", "quote": "ONLY THE LESSON TAB"}]})
    assert set(spans[0]) == {"quote", "context", "location", "occurrence"}
    assert spans[0]["quote"] == "ONLY THE LESSON TAB" and spans[0]["occurrence"] == 1
    assert spans[0]["location"] == '{"tab": "urok", "quote": "ONLY THE LESSON TAB"}'
    prepared = _prepared_spans(world)
    assert prepared[0]["quote"] == "construction" and "absence" not in prepared[0]
    prompt = world.prompt.read_text(encoding="utf-8")
    instructions = prompt.split("## Original Finding (Data)", 1)[0]
    assert all(line in instructions for line in _QUOTED_PROCEDURE)
    assert all(line not in instructions for line in _ABSENCE_PROCEDURE)
    assert "## Disputed Span In Context (Data)" in prompt
    assert _ABSENCE_LINE not in prompt
    assert "## Scoped Unit (Data)" not in prompt


def test_search_text_source_label_names_the_file(world: World) -> None:
    textbook = "4-klas-ukrayinska-mova-zaharijchuk-2021-1"
    guide = "antonenko-davydovych-yak-my-hovorymo"
    assert settle.SOURCES["search_text"] == "style_guide"
    assert settle._source({"tool": "search_text", "arguments": {"source_file": textbook}}) == f"search_text:{textbook}"
    assert settle._source({"tool": "search_text", "arguments": {"source_file": guide}}) == f"search_text:{guide}"
    assert settle._source({"tool": "search_text", "arguments": {}}) is None
    assert settle._source({"tool": "search_style_guide", "arguments": {"source_file": guide}}) == "style_guide"
    different = [
        {
            "receipt": world.call("search_text", "Textbook page.", arguments={"source_file": textbook}),
            "quote": "Textbook page.",
        },
        {
            "receipt": world.call("search_text", "Style guide page.", arguments={"source_file": guide}),
            "quote": "Style guide page.",
        },
    ]
    assert (
        settle.validate_reply(world.reply("source_conflict", different), world.manifest.read_bytes(), world.own_ledger)[
            0
        ]
        == "source_conflict"
    )
    same_file = [
        {
            "receipt": world.call("search_text", "First page.", arguments={"source_file": textbook}),
            "quote": "First page.",
        },
        {
            "receipt": world.call("search_text", "Second page.", arguments={"source_file": textbook}),
            "quote": "Second page.",
        },
    ]
    with pytest.raises(settle.SettleError, match="two different sources"):
        settle.validate_reply(world.reply("source_conflict", same_file), world.manifest.read_bytes(), world.own_ledger)


def _span(**overrides: Any) -> dict[str, Any]:
    text = str(overrides.get("text", ""))
    span: dict[str, Any] = {
        "tab": "vpravy",
        "step": "s1",
        "activity": "a1",
        "item": None,
        "block": "instruction",
        "span": 0,
        "start": 0,
        "end": len(text),
        "source": "writer_prose",
        "ref": None,
        "role": "instruction",
        "text": text,
        "record_kind": None,
        "record_side": None,
        "option_origin": None,
        "is_key": None,
    }
    span.update(overrides)
    span["end"] = int(span["start"]) + len(str(span["text"]))
    return span


def _provenance(spans: list[dict[str, Any]], *, n: int = 2) -> dict[str, Any]:
    document = {
        "provenance_schema": 1,
        "lesson": {"level": "a1", "slug": "fixture-module", "n": n},
        "spans": spans,
    }
    schema = Path(__file__).resolve().parents[2] / "schemas" / "lesson-provenance-v1.schema.json"
    Draft202012Validator(json.loads(schema.read_text(encoding="utf-8"))).validate(document)
    return document


def _engine_activities_page(activities: list[dict[str, Any]]) -> str:
    """One A1 workbook tab, rendered by the same activity writer the engine calls."""
    parser = ActivityParser()
    parts = [parser._activity_to_mdx(parser._parse_activity(activity), False) for activity in activities]
    label = "\u0412\u043f\u0440\u0430\u0432\u0438 \u2014 Activities"
    body = "\n\n".join(parts).strip()
    return (
        '\n<Tabs syncKey="module-tab">\n'
        f'<TabItem label="{label}">\n\n{body}\n\n</TabItem>\n'
        "</Tabs>\n\n<HashTabSync />\n"
    )


_ENGINE_ACTIVITIES = [
    {
        "id": "a1",
        "type": "quiz",
        "title": "Choose the right answer",
        "instruction": "Pick the first",
        "items": [
            {
                "question": "ONLY ACTIVITY A1",
                "options": [{"text": "yes", "correct": True}, {"text": "no", "correct": False}],
            }
        ],
    },
    {
        "id": "a2",
        "type": "quiz",
        "title": "Name the picture",
        "instruction": "Pick the second",
        "items": [
            {
                "question": "ONLY ACTIVITY A2",
                "options": [{"text": "cat", "correct": True}, {"text": "dog", "correct": False}],
            }
        ],
    },
]


def _engine_provenance() -> dict[str, Any]:
    spans = [
        _span(text="Pick the first", role="instruction", block="instruction"),
        _span(text="ONLY ACTIVITY A1", role="item_prompt", block="prompt", item=0),
        _span(text="yes", role="item_option", block="opt_0", item=0, option_origin="writer_typed", is_key=True),
        _span(text="no", role="item_option", block="opt_1", item=0, option_origin="writer_typed", is_key=False),
        _span(activity="a2", text="Pick the second", role="instruction", block="instruction"),
        _span(activity="a2", text="ONLY ACTIVITY A2", role="item_prompt", block="prompt", item=0),
        _span(
            activity="a2",
            text="cat",
            role="item_option",
            block="opt_0",
            item=0,
            option_origin="writer_typed",
            is_key=True,
        ),
        _span(
            activity="a2",
            text="dog",
            role="item_option",
            block="opt_1",
            item=0,
            option_origin="writer_typed",
            is_key=False,
        ),
    ]
    return _provenance(spans)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _pin_provenance(root: Path, provenance: dict[str, Any], *, direct: bool) -> str:
    """Write the provenance file and a lesson manifest that pins it. Return the manifest sha256."""
    state = root / "curriculum/l2-uk-en/evidence/a1/_state/fixture-module"
    state.mkdir(parents=True)
    provenance_path = state / "lesson-2.provenance.yaml"
    provenance_bytes = yaml.safe_dump(provenance, allow_unicode=True, sort_keys=False).encode()
    provenance_path.write_bytes(provenance_bytes)
    provenance_pin = {
        "path": "curriculum/l2-uk-en/evidence/a1/_state/fixture-module/lesson-2.provenance.yaml",
        "sha256": _sha256(provenance_bytes),
    }
    if direct:
        manifest: dict[str, Any] = {"kind": "lesson", "level": "a1", "slug": "fixture-module", "lesson": 2}
        manifest["inputs"] = {"provenance": provenance_pin}
    else:
        digest = {"digest_schema": 1, "sources": [{"lesson": 2, "provenance_sha256": provenance_pin["sha256"]}]}
        digest_bytes = yaml.safe_dump(digest, sort_keys=False).encode()
        digest_path = state / "digest-upto-2.yaml"
        digest_path.write_bytes(digest_bytes)
        manifest = {
            "kind": "lesson",
            "level": "a1",
            "slug": "fixture-module",
            "lesson": 2,
            "module_digest": {
                "path": "curriculum/l2-uk-en/evidence/a1/_state/fixture-module/digest-upto-2.yaml",
                "sha256": _sha256(digest_bytes),
            },
        }
    manifest_bytes = yaml.safe_dump(manifest, sort_keys=False).encode()
    digest_hex = _sha256(manifest_bytes)
    history = state / "manifests" / "lesson-2" / f"{digest_hex}.yaml"
    history.parent.mkdir(parents=True)
    history.write_bytes(manifest_bytes)
    return digest_hex


def _module_list(root: Path) -> None:
    path = root / "curriculum/l2-uk-en/curriculum.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump({"levels": {"a1": {"type": "core", "modules": ["fixture-module"]}}}), encoding="utf-8"
    )


def test_an_engine_rendered_activity_absence_resolves_through_provenance(tmp_path: Path) -> None:
    page = _engine_activities_page(_ENGINE_ACTIVITIES)
    assert "### Choose the right answer" in page
    assert "### Name the picture" in page
    assert "<span id=" not in page
    assert "a1" not in page and "a2" not in page
    document = tmp_path / "site/src/content/docs/a1/fixture-module/2.mdx"
    document.parent.mkdir(parents=True)
    document.write_text(page, encoding="utf-8")
    _module_list(tmp_path)
    manifest_hash = _pin_provenance(tmp_path, _engine_provenance(), direct=True)
    world = _world(tmp_path, document, manifest_hash, scope={"tab": "vpravy", "activity": "a1"})
    context = _prepared_spans(world)[0]["context"]
    assert "### Choose the right answer" in context
    assert "ONLY ACTIVITY A1" in context
    assert "Pick the first" in context
    assert "ONLY ACTIVITY A2" not in context
    assert "### Name the picture" not in context
    assert "Pick the second" not in context
    instructions = world.prompt.read_text(encoding="utf-8").split("## Original Finding (Data)", 1)[0]
    assert all(line in instructions for line in _ABSENCE_PROCEDURE)
    assert all(line not in instructions for line in _QUOTED_PROCEDURE)


def test_an_engine_rendered_activity_without_manifest_refuses(tmp_path: Path) -> None:
    document = tmp_path / "site/src/content/docs/a1/fixture-module/2.mdx"
    document.parent.mkdir(parents=True)
    document.write_text(_engine_activities_page(_ENGINE_ACTIVITIES), encoding="utf-8")
    _module_list(tmp_path)
    with pytest.raises(settle.SettleError, match="lesson_manifest_unavailable_for_activity_provenance"):
        _world(tmp_path, document, "d" * 64, scope={"tab": "vpravy", "activity": "a1"})


def test_old_lesson_manifest_without_provenance_pin_refuses(tmp_path: Path) -> None:
    document = tmp_path / "site/src/content/docs/a1/fixture-module/2.mdx"
    document.parent.mkdir(parents=True)
    document.write_text(_engine_activities_page(_ENGINE_ACTIVITIES), encoding="utf-8")
    _module_list(tmp_path)
    manifest_hash = _pin_provenance(tmp_path, _engine_provenance(), direct=False)
    with pytest.raises(settle.SettleError, match="lesson_manifest_missing_provenance_pin"):
        _world(tmp_path, document, manifest_hash, scope={"tab": "vpravy", "activity": "a1"})


def test_a_provenance_pin_that_does_not_match_is_refused(tmp_path: Path) -> None:
    document = tmp_path / "site/src/content/docs/a1/fixture-module/2.mdx"
    document.parent.mkdir(parents=True)
    document.write_text(_engine_activities_page(_ENGINE_ACTIVITIES), encoding="utf-8")
    _module_list(tmp_path)
    manifest_hash = _pin_provenance(tmp_path, _engine_provenance(), direct=True)
    provenance_path = tmp_path / "curriculum/l2-uk-en/evidence/a1/_state/fixture-module/lesson-2.provenance.yaml"
    provenance_path.write_text(provenance_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(
        settle.SettleError, match="lesson_manifest_provenance_pin_invalid: lesson manifest pin does not match the file"
    ):
        _world(tmp_path, document, manifest_hash, scope={"tab": "vpravy", "activity": "a1"})


@pytest.mark.parametrize(
    "document,scope",
    [
        (
            _PLAN
            + "  - n: 1\n    title: Also lesson one\n    steps:\n      - id: s9\n        teach: duplicate lesson\n",
            {"lesson": 1},
        ),
        (
            "lessons:\n  - n: 1\n    title: Lesson one\n    steps:\n      - id: s1\n        teach: first copy\n"
            "      - id: s1\n        teach: second copy\n",
            {"lesson": 1, "step": "s1"},
        ),
        (
            "lessons:\n  - n: 1\n    title: Lesson one\n    activities:\n      - id: a1\n        focus: first copy\n"
            "      - id: a1\n        focus: second copy\n",
            {"lesson": 1, "activity": "a1"},
        ),
    ],
)
def test_duplicate_plan_ids_are_refused(document: str, scope: dict[str, Any]) -> None:
    with pytest.raises(settle.SettleError, match="scope names more than one unit in the document"):
        settle._context(document, {"locations": [], "scope": scope})


def test_prepare_refuses_a_duplicate_plan_lesson_before_writing(tmp_path: Path) -> None:
    document = tmp_path / "curriculum/l2-uk-en/lesson-plans/a1/fixture-module.yaml"
    document.parent.mkdir(parents=True)
    document.write_text(
        _PLAN + "  - n: 1\n    title: Also lesson one\n    steps:\n      - id: s9\n        teach: duplicate lesson\n",
        encoding="utf-8",
    )
    world = _world(tmp_path, document, "e" * 64, scope={"lesson": 1, "step": "s1"}, lesson_n=None, prepare=False)
    with pytest.raises(settle.SettleError, match="scope names more than one unit in the document"):
        settle.prepare(
            world.item_id,
            db_path=world.db_path,
            document_path=document,
            prior_ledger=world.prior_ledger,
            review_id="settle-R",
            attempt_id="settle-A",
            manifest_path=world.manifest,
            prompt_path=world.prompt,
            repo_root=world.root,
        )
    assert not world.manifest.exists()
    assert not world.prompt.exists()


def test_a_duplicate_activity_id_in_the_lesson_is_refused() -> None:
    document = (
        '<TabItem label="vpravy">\n<span id="a1"></span>\n### First\nONE\n'
        '<span id="a1"></span>\n### Second\nTWO\n</TabItem>\n'
    )
    with pytest.raises(settle.SettleError, match="scope names more than one unit in the document"):
        settle._context(document, {"locations": [], "scope": {"tab": "vpravy", "activity": "a1"}})

    page = _engine_activities_page(_ENGINE_ACTIVITIES[:1] + _ENGINE_ACTIVITIES[:1])
    provenance = _provenance(
        [
            _span(text="Pick the first", role="instruction", block="instruction"),
            _span(text="ONLY ACTIVITY A1", role="item_prompt", block="prompt", item=0),
        ]
    )
    with pytest.raises(settle.SettleError, match="scope names more than one unit in the document"):
        settle._context(page, {"locations": [], "scope": {"tab": "vpravy", "activity": "a1"}}, provenance)

    two_steps = _provenance(
        [
            _span(text="ONLY ACTIVITY A1", role="item_prompt", block="prompt", item=0, step="s1"),
            _span(text="OTHER STEP", role="item_prompt", block="prompt", item=0, step="s2"),
        ]
    )
    with pytest.raises(settle.SettleError, match="scope names more than one unit in the document"):
        settle._context(page, {"locations": [], "scope": {"tab": "vpravy", "activity": "a1"}}, two_steps)


@pytest.mark.parametrize(
    "tool,authority",
    [
        ("verify_word", "vesum"),
        ("verify_lemma", "vesum"),
        ("search_slovnyk_me", "slovnyk_me"),
        ("search_esum", "esum"),
        ("search_grinchenko_1907", "grinchenko"),
    ],
)
def test_facet_tool_authorities_can_supply_lemma_and_counterevidence(world, tool, authority):
    assert settle._source({"tool": tool}) == authority
    assert tool in settle.SEARCH_TOOLS["lemma"]
    assert tool in settle.SEARCH_TOOLS["counterevidence"]
    assert (
        settle.validate_reply(
            world.reply("refuted", _evidence(world, tool)), world.manifest.read_bytes(), world.own_ledger
        )[0]
        == "refuted"
    )


@pytest.mark.parametrize("facet", ["meaning", "norm", "stress"])
@pytest.mark.parametrize("outcome", ["supported_defect", "refuted", "source_conflict"])
def test_sum11_cannot_settle_language_authority(world, facet, outcome):
    assert "search_definitions" not in settle.SOURCES
    assert all("search_definitions" not in tools for tools in settle.SEARCH_TOOLS.values())
    assert settle._source({"tool": "search_definitions"}) is None
    evidence = _evidence(world, "search_definitions", result=f"Historical {facet} contrast.")
    if outcome == "source_conflict":
        evidence += _evidence(world, "query_sum20", result="Modern dictionary evidence.")
    with pytest.raises(
        settle.SettleError, match=r"needs (a cited receipt with hits|hit receipts from two different sources)"
    ):
        settle.validate_reply(world.reply(outcome, evidence), world.manifest.read_bytes(), world.own_ledger)


def test_sum11_cannot_be_a_broadened_counterevidence_search(world):
    receipt = world.call("search_definitions", "Contrast only.")
    searches = [{"category": "counterevidence", "receipt": receipt, "quote": "Contrast only."}]
    with pytest.raises(settle.SettleError, match="wrong tool"):
        settle.validate_reply(
            world.reply("unresolved", searches=searches), world.manifest.read_bytes(), world.own_ledger
        )


@pytest.mark.parametrize("record_kind", ["retired", "malformed", "replacement"])
def test_prepare_plan_uses_exact_byte_retirement_before_context_or_writes(tmp_path, record_kind, monkeypatch):
    from scripts.curriculum.validate.loader import PlanError

    document = tmp_path / "curriculum/l2-uk-en/lesson-plans/a1/fixture-module.yaml"
    document.parent.mkdir(parents=True)
    document.write_text(_PLAN, encoding="utf-8")
    world = _world(tmp_path, document, "c" * 64, scope={"lesson": 1, "step": "s1"},
                   lesson_n=None, prepare=False)
    record = {
        "retirement_schema": 1,
        "plans": [{"slug": "fixture-module", "old_position": 1,
                   "sha256": hashlib.sha256(document.read_bytes()).hexdigest()}],
        "routes": [],
    }
    (document.parent / "_retired.yaml").write_text(
        "invalid: true" if record_kind == "malformed" else yaml.safe_dump(record)
    )
    if record_kind == "replacement":
        document.write_text(_PLAN + "\n", encoding="utf-8")
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    kwargs = dict(db_path=world.db_path, document_path=document, prior_ledger=world.prior_ledger,
                  review_id="settle-R", attempt_id="settle-A", manifest_path=world.manifest,
                  prompt_path=world.prompt, repo_root=tmp_path)
    if record_kind == "replacement":
        settle.prepare(world.item_id, **kwargs)
        manifest = yaml.safe_load(world.manifest.read_text())
        assert manifest["inputs"]["document"]["sha256"] == hashlib.sha256(document.read_bytes()).hexdigest()
        assert _prepared_spans(world)[0]["context"] == "s1\nfirst step only"
    else:
        monkeypatch.setattr(settle, "_original_finding", lambda *args: pytest.fail("finding read before retirement"))
        with pytest.raises(PlanError, match="plan_retired" if record_kind == "retired" else "retirement_record_invalid"):
            settle.prepare(world.item_id, **kwargs)
        assert not world.manifest.exists() and not world.prompt.exists()
        assert {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before
