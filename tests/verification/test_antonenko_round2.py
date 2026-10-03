"""Review counterexamples and fail-closed citation proof for #9640."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest

from scripts.curriculum.resolver.tokenize import tokenize
from scripts.verification.antonenko_patterns import PATTERNS, find_book_calques
from scripts.verification.verify_antonenko_citations import audit_citations, main, normalize

MORPHOLOGY = {
    **json.loads(Path(__file__).with_name("antonenko_fixtures.json").read_text())["morphology"],
    **json.loads(Path(__file__).with_name("antonenko_round2_fixtures.json").read_text()),
}

WITHHELD = [
    "Він прийняв пропозицію стати директором",
    "Король прийняв пропозицію султана",
    "Збори прийняли пропозицію",
    "Збори прийняли постанову",
    "По моїй думці так не можна робити",
    "Як не дивно, він прийшов",
    "Як правило, він читає ввечері",
    "Вони прийняли всі необхідні міри",
    "Ми прийняли міри",
    "Нанести шкоду можна тільки, нанісши грязюки чи снігу до хати",
    "Це наносить шкоду",
    "Вони втратили свідомість своєї відповідальності",
    "Вони втратили свідомість обов'язку",
    "Він повернувся до свідомості свого обов'язку",
    "Він стояв на протязі кілька хвилин",
    "Він сидів на протязі години дві й застудився",
    "Він стояв на протязі дві години",
    "Він стояв на протязі цілу годину",
    "На протязі 2 років ми працювали",
    "Він сидів на протязі години 2",
]


@pytest.mark.parametrize("text", WITHHELD)
def test_review_counterexamples_have_no_firm_book_finding(text):
    findings = find_book_calques(text, tokenize(text), MORPHOLOGY)
    if "на протязі" in text.lower():
        assert len(findings) == 1
        assert findings[0]["detail"]["status"] == "suspicion"
    else:
        assert findings == []


@pytest.mark.parametrize("duration", ["двох років", "цього року", "останніх років"])
def test_genitive_duration_modifiers_remain_supported(duration):
    text = f"На протязі {duration} ми працювали"
    assert any(
        f["detail"]["pattern_id"] == "temporal-protiah" for f in find_book_calques(text, tokenize(text), MORPHOLOGY)
    )


@pytest.mark.parametrize("text", ["Хлопчик утратив свідомість", "Хлопчик утрачає свідомість"])
def test_u_variant_consciousness_loss(text):
    findings = find_book_calques(text, tokenize(text), MORPHOLOGY)
    assert len(findings) == 1
    assert findings[0]["detail"]["pattern_id"] == "consciousness-loss"
    assert text[findings[0]["start"] : findings[0]["end"]] == findings[0]["form"]


@pytest.mark.parametrize("text", ["Хлопчик утратив книжку", "Хлопчик утрачає свідомість свого обов'язку"])
def test_u_variant_negative_counterparts(text):
    assert not find_book_calques(text, tokenize(text), MORPHOLOGY)


def test_postposed_numeral_in_next_sentence_does_not_erase_duration():
    text = "На протязі години. Дві книжки впали"
    assert len(find_book_calques(text, tokenize(text), MORPHOLOGY)) == 1


def test_citation_typography_normalization():
    assert normalize("Ні–ні та\n й") == normalize("ні-ні та й")
    assert normalize("п’ятницях") == normalize("п'ятницях")
    assert normalize("по-моєму") != normalize("по моїй думці")


@pytest.mark.parametrize("defect", ["missing_chunk", "wrong_source", "absent_form", "missing_anchor", "orphan_anchor"])
def test_citation_audit_rejects_missing_or_misattributed_evidence(defect, monkeypatch):
    from scripts.verification import verify_antonenko_citations as audit

    pattern = PATTERNS[0]
    anchors = {pattern.id: "прийняли участь"}
    if defect == "missing_anchor":
        anchors = {}
    if defect == "orphan_anchor":
        anchors["orphan"] = "участь"
    monkeypatch.setattr(audit, "EVIDENCE_FORMS", anchors)
    if defect == "missing_anchor":
        pattern = replace(pattern, id="missing")
    with sqlite3.connect(":memory:") as conn:
        conn.execute("CREATE TABLE textbooks (chunk_id TEXT, source_file TEXT, text TEXT)")
        if defect != "missing_chunk":
            conn.execute(
                "INSERT INTO textbooks VALUES (?, ?, ?)",
                (
                    pattern.chunk_id,
                    "other" if defect == "wrong_source" else audit.SOURCE_FILE,
                    "брати участь" if defect == "absent_form" else "прийняли участь",
                ),
            )
        result = audit_citations(conn, (pattern,))
    assert defect in {f["reason"] for f in result["failures"]}


def test_citation_cli_reports_receipt_read_only(tmp_path, monkeypatch, capsys):
    from scripts.verification import verify_antonenko_citations as audit

    db = tmp_path / "sources.db"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE textbooks (chunk_id TEXT, source_file TEXT, text TEXT)")
    before = db.read_bytes()
    monkeypatch.setattr("sys.argv", ["verify_antonenko_citations", "--database", str(db)])
    assert main() == 1
    assert len(json.loads(capsys.readouterr().out)["failures"]) == len(PATTERNS)
    assert db.read_bytes() == before
    monkeypatch.setattr(audit, "audit_citations", lambda conn: {"failures": []})
    assert main() == 0
