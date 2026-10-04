"""Synthetic Unicode boundary regressions through A1 reference readers (#9556)."""

import json

import pytest
import yaml
from jsonl_reader_cases import VALUE

from scripts.curriculum.evidence import sense_bindings
from scripts.ingest import prove_ohoiko_a1_reference as proof


@pytest.mark.parametrize("ending", ["\n", "\r\n", ""], ids=["LF", "CRLF", "unterminated"])
def test_private_entries_preserves_unicode_separators(ending, tmp_path):
    inventory = [{"locator": "p200 fixture#1", "stressed": "synthetic"}]
    record = {"locator": inventory[0]["locator"], "printed_label": "synthetic", "meaning": VALUE}
    path = tmp_path / "meanings.jsonl"
    path.write_bytes(("\n \t\r\n" + json.dumps(record, ensure_ascii=False) + ending).encode("utf-8"))

    assert sense_bindings.private_entries(path, inventory) == {record["locator"]: record}


@pytest.mark.parametrize("ending", ["\n", "\r\n", ""], ids=["LF", "CRLF", "unterminated"])
def test_prove_meanings_preserves_unicode_separators(ending, tmp_path, monkeypatch):
    row = {"locator": "p200 fixture", "kind": "word", "lemma": "fixture", "stressed": "fixture", "pos": "noun"}
    inventory = tmp_path / "inventory.yaml"
    inventory.write_text(yaml.safe_dump({"sources": [{"headwords": [row]}]}), encoding="utf-8")
    record = {"locator": row["locator"] + "#1", "printed_label": "fixture", "meaning": VALUE}
    meanings = tmp_path / "meanings.jsonl"
    meanings.write_bytes(("\n \t\r\n" + json.dumps(record, ensure_ascii=False) + ending).encode("utf-8"))

    class Page:
        def get_text(self, mode):
            assert mode == "rawdict"
            return {"blocks": []}

    class Document:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def __getitem__(self, index):
            return Page()

    monkeypatch.setattr(proof.pymupdf, "open", lambda _: Document())
    monkeypatch.setattr(
        proof, "raw_glossary_meanings", lambda lines, page: [(proof.signature(row), VALUE)] if page == 200 else []
    )

    assert proof.prove_meanings(tmp_path / "unused.pdf", inventory, meanings) == {
        "expected_entries": 1,
        "actual_entries": 1,
        "accounted_lines": 0,
        "unexplained_differences": 0,
        "duplicate_locators": 0,
        "unknown_locators": 0,
        "invalid_labels": 0,
        "mismatch_locators": [],
    }
