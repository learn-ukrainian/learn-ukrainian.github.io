"""The word store's two record shapes: lexical (lemma, pos, forms) and `kind: formula` (text, parts)."""

from scripts.curriculum.evidence.word_records import is_formula, lexical, printed

WORD = {"id": "W-001", "lemma": "день", "pos": "noun", "forms": []}
FORMULA = {"id": "W-002", "kind": "formula", "text": "Добрий день!", "parts": [{"word": "W-001", "form": "день"}]}


def test_accessors_read_both_record_shapes():
    assert [is_formula(WORD), is_formula(FORMULA)] == [False, True]
    assert lexical([WORD, FORMULA, "not a record"]) == [WORD]
    assert printed(WORD) == "день"
    assert printed(FORMULA) == "Добрий день!"
    assert printed({"id": "W-003"}) is None
