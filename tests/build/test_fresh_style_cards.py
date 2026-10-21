"""E1.3 of the create-path engine: the three style cards, their sidecar hashes and their sourced exemplars."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest
import yaml

from scripts.lib.readonly_sqlite import open_readonly

REPO = Path(__file__).resolve().parents[2]
CARDS = REPO / "docs" / "style-cards"
BANDS = {"a1": ["a1"], "a2": ["a2"], "b1plus": ["b1", "b2"]}
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
    assert sidecar == f"{digest}  {band}.md\n"
    assert digest == hashlib.sha256(raw).hexdigest(), "the sidecar must be regenerated when the card changes"
    assert front["card_version"] == 1
    assert front["band"] == band
    assert front["levels"] == BANDS[band]


@pytest.mark.parametrize("band", sorted(BANDS))
def test_card_ukrainian_is_only_exemplars_or_contract_terms(band: str) -> None:
    """Cyrillic is sourced exemplar text, contract terminology or approved policy notation."""
    front, body, _ = read_card(band)
    allowed = {norm(t) for e in front["exemplars"] for t in e["text"]}
    allowed |= {norm(e["source"]) for e in front["exemplars"]}
    contract_terms = {"звук", "літера", "відмінок", "наголос", "ти", "ви", "Урок", "Ресурси", "Словник", "Правопис", "ЕСУМ"}
    # Policy notation names alternations and the cited §158 I.11 note 2 defect,
    # not new learner-facing exemplars. Match the approved fragments exactly.
    policy_notation = ('у/в, і/й and з/із/зі', '"а втім, часу..."')
    for line in body.splitlines():
        if not re.search(r"[Ѐ-ӿ]", line):
            continue
        stripped = norm(line.lstrip("> ").strip())
        if stripped in allowed:
            continue
        for fragment in policy_notation:
            line = line.replace(fragment, "")
        for run in re.findall(r"[Ѐ-ӿ][Ѐ-ӿ'’\-]*", line):
            assert run in contract_terms or any(run in a for a in allowed), f"{band}: unsourced Ukrainian {run!r} in: {line[:80]}"


@pytest.mark.parametrize("band", sorted(BANDS))
def test_card_exemplars_are_attested_in_the_corpus(band: str, requires_sources_db: Path) -> None:
    """Each exemplar text is a whitespace-normalised substring of its corpus record (R-35)."""
    front, _, _ = read_card(band)
    con = open_readonly(requires_sources_db)
    try:
        for exemplar in front["exemplars"]:
            row = con.execute(f"select text from {exemplar['table']} where chunk_id = ?", (exemplar["chunk_id"],)).fetchone()
            assert row, f"{exemplar['chunk_id']} not in {exemplar['table']}"
            record = norm(row[0])
            for text in exemplar["text"]:
                assert norm(text) in record, f"{exemplar['id']}: not attested: {text}"
    finally:
        con.close()
