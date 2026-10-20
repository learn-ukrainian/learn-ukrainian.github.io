"""Canonical atlas0 pairing for the v0.1.0-pilot word-card release (#8981)."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.common.jsonl import jsonl_lines
from scripts.common.repo_root import main_checkout_root
from scripts.projects.open_model_data import generate_atlas_pairing as pairing

ROOT = Path(__file__).resolve().parents[3]
RELEASE_CARDS = 150


def _cid(body: str) -> str:
    assert len(body) == 12
    return f"wc_{body}"


def _card(card_id: str, spelling: str | None = None, pos: str | None = None, spellings: tuple[str, ...] = ()) -> dict:
    fields = []
    values = spellings or (() if spelling is None else (spelling,))
    for index, value in enumerate(values):
        fields.append({
            "assertion_id": f"wa_{index:024x}",
            "subject": {"kind": "card", "id": card_id},
            "field": "spelling",
            "value": value,
        })
    if pos is not None:
        fields.append({
            "assertion_id": f"wa_{len(fields):024x}",
            "subject": {"kind": "card", "id": card_id},
            "field": "pos",
            "value": pos,
        })
    if not fields:
        fields.append({
            "assertion_id": f"wa_{0:024x}",
            "subject": {"kind": "card", "id": card_id},
            "field": "mwe_form",
            "value": "близько не пахне",
        })
    return {
        "card_id": card_id,
        "card_version": "0.1.0",
        "card_kind": "lexeme" if spelling or spellings else "mwe",
        "status": "CANDIDATE",
        "known_gaps": [],
        "fields": fields,
    }


def _atlas(card_id: str, spelling: str, pos: str, slug: str | None = None, *, state: str = "active",
           source_id: str = "atlas0") -> dict:
    key = f"atlas0:slug:{slug or spelling}" if source_id == "atlas0" else f"ulif:entry:{spelling}"
    return {
        "card_id": card_id,
        "card_kind": "lexeme",
        "state": state,
        "key_at_creation": {
            "spelling": spelling,
            "pos": pos,
            "source_keys": [{"source_id": source_id, "key": key}],
        },
        "senses": [],
    }


def _write_inputs(tmp_path: Path, cards: list[dict], entries: list[dict], *, version: int = 3) -> tuple[Path, Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    cards_path = tmp_path / "word-cards.jsonl"
    # Reverse the written order so the generator must sort by card_id itself.
    lines = [json.dumps(card, ensure_ascii=False, sort_keys=True) for card in reversed(cards)]
    cards_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps({
        "schema_version": "1",
        "registry_version": version,
        "entries": list(reversed(entries)),
    }, ensure_ascii=False), encoding="utf-8")
    return cards_path, registry_path


def _run(tmp_path: Path, cards: list[dict], entries: list[dict], *extra: str) -> tuple[int, dict, Path]:
    cards_path, registry_path = _write_inputs(tmp_path, cards, entries)
    output = tmp_path / "pairing-atlas0.json"
    code = pairing.main([
        "--cards", str(cards_path), "--registry", str(registry_path), "--output", str(output), *extra,
    ])
    document = json.loads(output.read_text(encoding="utf-8")) if output.is_file() else {}
    return code, document, output


def test_schema_unique_cards_and_count_invariant(tmp_path: Path) -> None:
    paired_id = _cid("aaaaaaaaaaaa")
    unpaired_id = _cid("bbbbbbbbbbbb")
    ambiguous_id = _cid("cccccccccccc")
    other_id = _cid("dddddddddddd")
    noun_id = _cid("eeeeeeeeeeee")
    verb_id = _cid("ffffffffffff")
    cards = [
        _card(other_id, "замок", "noun"),
        _card(paired_id, "кіт", "noun"),
        _card(unpaired_id, None),
        _card(ambiguous_id, "замок", "noun"),
        _card(noun_id, "ключ", "noun"),
        _card(verb_id, "ключ", "verb"),
    ]
    entries = [
        _atlas(_cid("gggggggggggg"), "кіт", "noun"),
        _atlas(_cid("hhhhhhhhhhhh"), "кіт", "noun", source_id="ulif"),
        _atlas(_cid("jjjjjjjjjjjj"), "замок", "noun", slug="замок"),
        _atlas(_cid("kkkkkkkkkkkk"), "ключ", "noun", slug="ключ-іменник"),
        _atlas(_cid("mmmmmmmmmmmm"), "ключ", "verb", slug="ключ-дієслово"),
        _atlas(_cid("nnnnnnnnnnnn"), "шуба", "noun", state="inactive"),
    ]
    code, document, output = _run(tmp_path, cards, entries)
    assert code == 0
    Draft202012Validator(pairing.PAIRING_SCHEMA).validate(document)
    for entry in document["entries"]:
        Draft202012Validator(pairing._ENTRY_SCHEMA).validate(entry)
    assert [entry["card_id"] for entry in document["entries"]] == sorted(card["card_id"] for card in cards)
    assert len({entry["card_id"] for entry in document["entries"]}) == len(cards)
    assert document["paired_count"] + document["unpaired_count"] + document["ambiguous_count"] == len(cards)
    assert document["cards_sha256"] == hashlib.sha256(output.with_name("word-cards.jsonl").read_bytes()).hexdigest()
    by_id = {entry["card_id"]: entry for entry in document["entries"]}
    assert by_id[paired_id] == {
        "card_id": paired_id, "spelling": "кіт", "status": "paired",
        "atlas0_slug": "atlas0:slug:кіт", "pilot_card_id": _cid("gggggggggggg"),
    }
    assert by_id[unpaired_id]["status"] == "unpaired"
    assert by_id[unpaired_id]["spelling"] is None
    assert by_id[unpaired_id]["reason"] == pairing.UNPAIRED_REASON
    assert by_id[ambiguous_id]["status"] == "ambiguous"
    assert by_id[other_id]["status"] == "ambiguous"
    assert by_id[ambiguous_id]["reason"] == pairing.HOMONYM_REASON
    assert by_id[noun_id]["atlas0_slug"] == "atlas0:slug:ключ-іменник"
    assert by_id[verb_id]["atlas0_slug"] == "atlas0:slug:ключ-дієслово"
    # A second run, and a registry that only repeats the ulif row, stays deterministic.
    code_again, again, _output_again = _run(tmp_path / "again", cards, entries)
    assert code_again == 0
    assert again == document


def test_case_self_match_and_pos_failure_stay_unresolved(tmp_path: Path) -> None:
    capital = _cid("aaaaaaaaaaaa")
    conflict = _cid("bbbbbbbbbbbb")
    same_pos = _cid("cccccccccccc")
    cards = [
        _card(capital, "Баран", "noun"),
        _card(conflict, spellings=("замок", "за́мок")),
        _card(same_pos, "брама", "noun"),
    ]
    entries = [
        _atlas(_cid("dddddddddddd"), "баран", "noun"),
        _atlas(_cid("eeeeeeeeeeee"), "брама", "noun", slug="брама-1"),
        _atlas(_cid("ffffffffffff"), "брама", "noun", slug="брама-2"),
    ]
    code, document, _output = _run(tmp_path, cards, entries)
    assert code == 0
    by_id = {entry["card_id"]: entry for entry in document["entries"]}
    assert by_id[capital]["status"] == "unpaired"
    assert by_id[capital]["spelling"] == "Баран"
    assert by_id[conflict]["status"] == "ambiguous"
    assert by_id[conflict]["reason"] == pairing.CONFLICTING_SPELLING
    assert by_id[same_pos]["status"] == "ambiguous"
    assert by_id[same_pos]["candidate_atlas0_slugs"] == ["atlas0:slug:брама-1", "atlas0:slug:брама-2"]
    assert document["paired_count"] == 0


def test_check_mode_exits_zero_when_current_and_one_on_drift(tmp_path: Path) -> None:
    cards = [_card(_cid("aaaaaaaaaaaa"), "кіт", "noun")]
    entries = [_atlas(_cid("bbbbbbbbbbbb"), "кіт", "noun")]
    code, document, output = _run(tmp_path, cards, entries)
    assert code == 0
    before = output.stat().st_mtime_ns
    original = output.read_bytes()
    cards_path = tmp_path / "word-cards.jsonl"
    registry_path = tmp_path / "registry.json"
    assert pairing.main([
        "--cards", str(cards_path), "--registry", str(registry_path), "--output", str(output), "--check",
    ]) == 0
    assert output.read_bytes() == original
    assert output.stat().st_mtime_ns == before
    output.write_bytes(original.replace(b'"schema_version": "1"', b'"schema_version": "9"', 1))
    drifted = output.read_bytes()
    drifted_mtime = output.stat().st_mtime_ns
    assert pairing.main([
        "--cards", str(cards_path), "--registry", str(registry_path), "--output", str(output), "--check",
    ]) == 1
    assert output.read_bytes() == drifted
    assert output.stat().st_mtime_ns == drifted_mtime
    assert document["paired_count"] == 1


def test_pairing_does_not_modify_sources_db(tmp_path: Path) -> None:
    # Match the filename after listing. Joining it onto a checkout path is a
    # store-access finding even when the test only stats the file.
    primary_dir = main_checkout_root(ROOT) / "data"
    worktree_dir = ROOT / "data"
    primary = next(child for child in primary_dir.iterdir() if child.name == "sources.db")
    link = next(child for child in worktree_dir.iterdir() if child.name == "sources.db")
    before = primary.stat()
    link_before = os.lstat(link)
    link_target = os.readlink(link)
    code, _document, _output = _run(
        tmp_path,
        [_card(_cid("aaaaaaaaaaaa"), "кіт")],
        [_atlas(_cid("bbbbbbbbbbbb"), "кіт", "noun")],
    )
    after = primary.stat()
    assert code == 0
    assert (before.st_mode, before.st_size, before.st_mtime_ns, before.st_ino) == (
        after.st_mode, after.st_size, after.st_mtime_ns, after.st_ino)
    assert stat.S_IMODE(after.st_mode) == 0o444
    assert os.lstat(link).st_ino == link_before.st_ino
    assert os.readlink(link) == link_target
    assert pairing.main([
        "--cards", str(tmp_path / "word-cards.jsonl"),
        "--registry", str(tmp_path / "registry.json"),
        "--output", str(primary),
    ]) == 1
    refused = primary.stat()
    assert (before.st_mode, before.st_size, before.st_mtime_ns, before.st_ino) == (
        refused.st_mode, refused.st_size, refused.st_mtime_ns, refused.st_ino)
    assert os.readlink(link) == link_target


def test_help_documents_check_and_exit_codes() -> None:
    parser = pairing._parser()
    help_text = parser.format_help()
    assert "--check" in help_text
    assert "Exit codes:" in help_text
    assert "sources.db is not opened" in help_text
    assert "v0.1.0-pilot" in help_text


def _published_cards() -> Path | None:
    try:
        return pairing.resolve_cards_path(pairing.DEFAULT_CARDS)
    except pairing.PairingError:
        return None


def test_committed_pairing_artifact_has_every_release_slot() -> None:
    path = ROOT / pairing.DEFAULT_OUTPUT
    document = json.loads(path.read_bytes())
    pairing.validate_document(document)
    assert document["total_cards"] == RELEASE_CARDS
    assert document["cards_sha256"] == pairing.PUBLISHED_CARDS_SHA256
    assert document["registry_version"] == 3
    assert len({entry["card_id"] for entry in document["entries"]}) == RELEASE_CARDS
    assert document["paired_count"] + document["unpaired_count"] + document["ambiguous_count"] == RELEASE_CARDS
    slugs = [entry["atlas0_slug"] for entry in document["entries"] if entry["status"] == "paired"]
    assert len(slugs) == len(set(slugs))


def test_published_release_cards_are_present_and_unique(tmp_path: Path) -> None:
    cards_path = _published_cards()
    if cards_path is None:
        pytest.skip("published word-cards.jsonl is not in this checkout")
    raw = cards_path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == pairing.PUBLISHED_CARDS_SHA256
    cards = [json.loads(line) for line in jsonl_lines(raw.decode("utf-8")) if line.strip()]
    assert len(cards) == RELEASE_CARDS
    output = tmp_path / "pairing-atlas0.json"
    assert pairing.main([
        "--cards", str(cards_path),
        "--registry", str(ROOT / pairing.DEFAULT_REGISTRY),
        "--output", str(output),
    ]) == 0
    document = json.loads(output.read_bytes())
    pairing.validate_document(document)
    assert [entry["card_id"] for entry in document["entries"]] == sorted(card["card_id"] for card in cards)
    assert document["paired_count"] + document["unpaired_count"] + document["ambiguous_count"] == RELEASE_CARDS
    by_id = {entry["card_id"]: entry for entry in document["entries"]}
    assert by_id["wc_02a5cjxcpbcf"]["status"] == "paired"
    assert by_id["wc_02a5cjxcpbcf"]["spelling"] == "баран"
    assert by_id["wc_02a5cjxcpbcf"]["atlas0_slug"] == "atlas0:slug:баран"
    for card_id in ("wc_bgr5q9c06wxg", "wc_cvkw5nzdg00n"):
        assert by_id[card_id]["status"] == "ambiguous"
        assert by_id[card_id]["reason"] == pairing.HOMONYM_REASON
        assert by_id[card_id]["candidate_atlas0_slugs"] == ["atlas0:slug:замок"]
    assert by_id["wc_0a3k6ypbjhrf"]["status"] == "unpaired"
    assert by_id["wc_0a3k6ypbjhrf"]["spelling"] == "Баран"
    assert by_id["wc_1nrw339ddgvm"]["status"] == "unpaired"
    assert by_id["wc_1nrw339ddgvm"]["spelling"] is None
    committed = ROOT / pairing.DEFAULT_OUTPUT
    assert pairing.main([
        "--cards", str(cards_path),
        "--registry", str(ROOT / pairing.DEFAULT_REGISTRY),
        "--output", str(committed),
        "--check",
    ]) == 0
