"""Structural settle contract: one decision, bounded own receipts, exact prompt."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.review import findings_db as db
from scripts.review import settle
from scripts.review.prompts.check import check_prompt
from scripts.review.prompts.eligibility import pin_refusals
from scripts.review.receipts import ledger
from tests.review.test_prompts import _setup_lesson_fixture

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
            status="ok",
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


def _world(root: Path, document: Path, manifest_hash: str, *, quote: str = "construction") -> World:
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
        "locations": [{"tab": "urok", "quote": quote}],
        "unsupported_by_source": {"searches": [{"receipt": prior_id, "outcome": "no_hits"}]},
    }
    with db.connect(database) as conn, db.transaction(conn):
        db.insert_attempt(
            conn,
            {
                "review_id": "original-R",
                "attempt_id": "original-A",
                "kind": "lesson",
                "level": "a1",
                "slug": "fixture-module",
                "lesson_n": 2,
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
            lesson_n=2,
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


def _broadened(world: World) -> list[dict[str, str]]:
    calls = [
        ("lemma", "inspect_word", {}),
        ("construction", "search_style_guide", {}),
        ("style_prose", "search_text", {"source_file": "antonenko-davydovych-yak-my-hovorymo"}),
        ("ua_gec_context", "search_ua_gec_errors", {}),
        ("grac", "query_grac", {}),
        ("pravopys", "query_pravopys", {}),
        ("counterevidence", "query_sum20", {}),
    ]
    return [
        {
            "category": category,
            "receipt": world.call(tool, f"{category}: no results", hits=0, arguments=arguments),
            "quote": f"{category}: no results",
        }
        for category, tool, arguments in calls
    ]


def test_unresolved_accepts_each_broadened_search(world: World) -> None:
    reply = world.reply("unresolved", searches=_broadened(world))
    result, receipts = settle.validate_reply(reply, world.manifest.read_bytes(), world.own_ledger)
    assert result == "unresolved" and len(receipts) == 7


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
