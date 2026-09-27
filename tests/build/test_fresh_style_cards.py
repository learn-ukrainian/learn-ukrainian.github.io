"""E1.3 of the create-path engine: the three style cards, their sidecar hashes and their sourced exemplars."""

from __future__ import annotations

import hashlib
import re
import sqlite3
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
CARDS = REPO / "docs" / "style-cards"
BANDS = {"a1": ["a1"], "a2": ["a2"], "b1plus": ["b1", "b2"]}
COMBINING = ("̀", "́")


def read_card(band: str) -> tuple[dict, str, bytes]:
    raw = (CARDS / f"{band}.md").read_bytes()
    text = raw.decode("utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert match, f"{band}.md has no YAML frontmatter"
    return yaml.safe_load(match.group(1)), text[match.end():], raw


def norm(s: str) -> str:
    return " ".join(s.split())


@pytest.mark.parametrize("band", sorted(BANDS))
def test_card_sidecar_hash_matches(band: str) -> None:
    front, _, raw = read_card(band)
    sidecar = (CARDS / f"{band}.sha256").read_text(encoding="utf-8")
    digest, _, name = sidecar.strip().partition("  ")
    assert name == f"{band}.md"
    assert digest == hashlib.sha256(raw).hexdigest(), "the sidecar must be regenerated when the card changes"
    assert front["card_version"] == 1
    assert front["band"] == band
    assert front["levels"] == BANDS[band]


@pytest.mark.parametrize("band", sorted(BANDS))
def test_card_covers_the_contract_sections(band: str) -> None:
    _, body, _ = read_card(band)
    for heading in (
        "## 1. Presentation practices",
        "## 2. Voice",
        "## 3. Conversational rules",
        "## 4. Lesson shape",
        "## 5. Activity rules",
        "## 6. Ukrainian on its own terms",
        "## 7. The language rule",
        "## 8. The draft: schema, block kinds, markup, gaps",
        "## 9. What you may not do",
        "## 10. Exemplars",
    ):
        assert heading in body, heading
    for dimension in ("`learner_fit`", "`language` / `calque`", "`language` / `register`", "`language` / `agreement`", "`evidence_use`"):
        assert dimension in body, f"conversational rules name the reviewer's dimension: {dimension}"
    assert "{{gloss:W-…}}" in body and "{{uk:…}}" in body
    assert "explanation" in body and "error_ref" in body


@pytest.mark.parametrize("band", sorted(BANDS))
def test_card_ukrainian_is_only_exemplars_or_contract_terms(band: str) -> None:
    """Every Cyrillic run in the card is an exemplar line or one of the contract's own terms (§5 table, tab names)."""
    front, body, _ = read_card(band)
    allowed = {norm(t) for e in front["exemplars"] for t in e["text"]}
    allowed |= {norm(e["source"]) for e in front["exemplars"]}
    contract_terms = {"звук", "літера", "відмінок", "наголос", "ти", "ви", "Урок", "Ресурси", "Словник"}
    for line in body.splitlines():
        if not re.search(r"[Ѐ-ӿ]", line):
            continue
        stripped = norm(line.lstrip("> ").strip())
        if stripped in allowed:
            continue
        for run in re.findall(r"[Ѐ-ӿ][Ѐ-ӿ'’\-]*", line):
            assert run in contract_terms or any(run in a for a in allowed), f"{band}: unsourced Ukrainian {run!r} in: {line[:80]}"


@pytest.mark.parametrize("band", sorted(BANDS))
def test_card_exemplars_are_declared_with_record_ids_and_quoted_in_body(band: str) -> None:
    front, body, _ = read_card(band)
    assert front["exemplars"], "a card without exemplars would still be valid, but these cards carry sourced ones"
    for exemplar in front["exemplars"]:
        assert exemplar["table"] in ("textbooks", "literary_texts")
        assert exemplar["chunk_id"] and exemplar["source"] and exemplar["domain"]
        assert f"`{exemplar['chunk_id']}`" in body
        for text in exemplar["text"]:
            assert not any(c in text for c in COMBINING), "exemplars are plain corpus text; stress is the engine's"
            assert f"> {text}" in body, f"exemplar text of {exemplar['id']} must be quoted verbatim in the body"


@pytest.mark.parametrize("band", sorted(BANDS))
def test_card_exemplars_are_attested_in_the_corpus(band: str, requires_sources_db: Path) -> None:
    """Each exemplar text is a whitespace-normalised substring of its corpus record (R-35)."""
    front, _, _ = read_card(band)
    con = sqlite3.connect(f"file:{requires_sources_db}?mode=ro", uri=True)
    try:
        for exemplar in front["exemplars"]:
            row = con.execute(f"select text from {exemplar['table']} where chunk_id = ?", (exemplar["chunk_id"],)).fetchone()
            assert row, f"{exemplar['chunk_id']} not in {exemplar['table']}"
            record = norm(row[0])
            for text in exemplar["text"]:
                assert norm(text) in record, f"{exemplar['id']}: not attested: {text}"
    finally:
        con.close()


@pytest.mark.repo_wide
def test_the_three_bands_and_nothing_else() -> None:
    names = sorted(p.name for p in CARDS.iterdir())
    assert names == sorted([f"{b}.md" for b in BANDS] + [f"{b}.sha256" for b in BANDS])
