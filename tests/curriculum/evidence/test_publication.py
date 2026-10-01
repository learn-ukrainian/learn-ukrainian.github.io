"""Exact-source permission, attribution, and publication-vs-grounding regressions."""

import pytest
import yaml

from scripts.curriculum.evidence import publication

BOOK = "1-klas-bukvar-zaharijchuk-2025-1"
PRIVATE = [*(f"ulp-{i}-00-lesson-notes" for i in range(1, 7)), "anna-ohoiko-1000-words-2nd-ed", "anna-ohoiko-500-verbs"]


def record(file=BOOK, quote="Synthetic excerpt", page=39):
    return {"id": "T-001", "source": {"kind": "textbook", "file": file, "page": page}, "quote": quote}


def test_policy_denominator_and_private_denials():
    entries = publication.load_registry()
    allowed = {key: entry for key, entry in entries.items() if entry["publish"]["allowed"]}
    assert len(allowed) == 163
    assert {entry["grade"] for entry in allowed.values()} == set(range(1, 12))
    assert {key for key, entry in entries.items() if not entry["publish"]["allowed"]} == set(PRIVATE)
    for key, entry in allowed.items():
        assert entry["file"] == key
        assert entry["publish"] == {
            "allowed": True,
            "limit_chars": 800,
            "attribution": "{author}, {title}, grade {grade}, {year}, page {page}",
        }


def test_attribution_and_exact_character_boundary():
    attribution = publication.quote_attribution(record(quote="x" * 800))
    entry = publication.load_registry()[BOOK]
    assert attribution == f"{entry['author']}, {BOOK}, grade 1, 2025, page 39"
    with pytest.raises(ValueError, match=r"^publication_limit:"):
        publication.quote_attribution(record(quote="x" * 801))
    # Unicode characters, not UTF-8 bytes; whitespace is counted, never stripped.
    assert publication.quote_attribution(record(quote="é" * 800)) == attribution
    with pytest.raises(ValueError, match=r"^publication_limit:"):
        publication.quote_attribution(record(quote="é" * 800 + " "))


@pytest.mark.parametrize("file", [*PRIVATE, "unregistered", BOOK + ".txt"])
def test_denied_and_unregistered_sources(file):
    rec = record(file)
    rec["source"]["publish"] = {"allowed": True, "limit_chars": 9999, "attribution": "Fake"}
    with pytest.raises(ValueError, match=r"^publication_right:"):
        publication.quote_attribution(rec)


@pytest.mark.parametrize("mutation", ["page", "author", "title", "year", "grade", "template"])
def test_attribution_is_required(mutation):
    entries = publication.load_registry()
    rec = record()
    if mutation == "page":
        rec["source"]["page"] = None
    elif mutation == "template":
        entries[BOOK]["publish"]["attribution"] = "Source"
    else:
        entries[BOOK][mutation] = None
    with pytest.raises(ValueError, match=r"^publication_attribution:"):
        publication.quote_attribution(rec, entries)


@pytest.mark.parametrize(
    "right", [{}, {"allowed": "true"}, {"allowed": True, "limit_chars": True}, {"allowed": True, "limit_chars": 0}]
)
def test_malformed_right_fails_closed(right):
    entries = publication.load_registry()
    entries[BOOK]["publish"] = right
    with pytest.raises(ValueError, match=r"^publication_right:"):
        publication.quote_attribution(record(), entries)


def test_source_kind_and_registry_identity_cannot_be_spoofed():
    rec = record()
    rec["source"]["kind"] = "literary"
    with pytest.raises(ValueError, match=r"^publication_right:"):
        publication.quote_attribution(rec)
    entries = publication.load_registry()
    entries[BOOK]["file"] = "another-source"
    with pytest.raises(ValueError, match=r"^publication_right:"):
        publication.quote_attribution(record(), entries)


@pytest.mark.parametrize("content", ["sources: []", "[]", "sources: [", "sources: null"])
def test_unavailable_or_malformed_registry(tmp_path, content):
    path = tmp_path / "registry.yaml"
    assert publication.load_registry(path) == {}
    path.write_text(content)
    assert publication.load_registry(path) == {}


def test_registry_is_reread_after_permission_withdrawal(tmp_path):
    entries = publication.load_registry()
    path = tmp_path / "registry.yaml"
    path.write_text(yaml.safe_dump({"sources": entries}))
    assert publication.quote_attribution(record(), publication.load_registry(path))
    entries[BOOK]["publish"]["allowed"] = False
    path.write_text(yaml.safe_dump({"sources": entries}))
    with pytest.raises(ValueError, match=r"^publication_right:"):
        publication.quote_attribution(record(), publication.load_registry(path))


def test_quoted_records_separates_grounding():
    lesson = {
        "steps": [
            {"id": "s1", "needs": ["quote"], "evidence": ["T-001"], "explains": ["T-002"], "ref": "T-003"},
            {"id": "s2", "needs": ["culture"], "explains": ["T-004"]},
        ]
    }
    expected = {"T-001": "s1", "T-002": "s1", "T-003": "s1"}
    assert publication.quoted_records(lesson) == expected
    assert publication.quoted_records({"lessons": [lesson]}) == expected
