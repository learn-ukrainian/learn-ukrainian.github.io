"""Exact-source permission, attribution, and publication-vs-grounding regressions."""

import re
from unittest.mock import patch

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
    assert len(allowed) == 148
    unconfirmed = {key for key, entry in entries.items() if entry["publish"].get("reason") == "title_unconfirmed"}
    assert len(unconfirmed) == 15
    assert len(allowed) + len(unconfirmed) == 163
    assert {entry["grade"] for entry in allowed.values()} == set(range(1, 12))
    assert {key for key, entry in entries.items() if not entry["publish"]["allowed"] and key not in unconfirmed} == set(
        PRIVATE
    )
    for key, entry in allowed.items():
        assert entry["file"] == key
        assert entry["publish"] == {
            "allowed": True,
            "limit_chars": 800,
            "attribution": "ukrainian-short",
        }


def test_attribution_and_exact_character_boundary():
    attribution = publication.quote_attribution(record(quote="x" * 800))
    assert attribution == "Захарійчук, «Українська мова. Буквар», 1 клас, ч. 1, 2025, с. 39"
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


@pytest.mark.parametrize("content", ["sources: []", "[]", "sources: [", "sources: null", "sources: {book: null}"])
def test_unavailable_or_malformed_registry(tmp_path, content):
    path = tmp_path / "registry.yaml"
    with pytest.raises(ValueError, match=r"^publication_registry_unreadable:"):
        publication.load_registry(path)
    path.write_text(content)
    with pytest.raises(ValueError, match=r"^publication_registry_unreadable:"):
        publication.load_registry(path)


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


@pytest.mark.parametrize("field", ["grade", "page"])
@pytest.mark.parametrize("value", [0, -1, True, "1", 1.5, None])
def test_positive_integer_grade_and_page(field, value):
    entries = publication.load_registry()
    rec = record()
    (entries[BOOK] if field == "grade" else rec["source"])[field] = value
    with pytest.raises(ValueError, match=r"^publication_attribution:"):
        publication.quote_attribution(rec, entries)


def test_registry_is_cached_and_caller_mutations_are_isolated(tmp_path):
    path = tmp_path / "registry.yaml"
    path.write_text(yaml.safe_dump({"sources": publication.load_registry()}))
    with patch.object(publication.yaml, "safe_load", wraps=yaml.safe_load) as parse:
        entries = publication.load_registry(path)
        entries[BOOK]["publish"]["allowed"] = False
        assert publication.quote_attribution(record(), publication.load_registry(path))
        assert parse.call_count == 1


def test_registry_read_error_has_typed_reason(tmp_path):
    path = tmp_path / "registry.yaml"
    path.write_text("sources: {}")
    with patch.object(publication.Path, "read_text", side_effect=PermissionError):
        with pytest.raises(ValueError, match=r"^publication_registry_unreadable:"):
            publication.load_registry(path)


def test_every_allowed_source_has_confirmed_human_bibliography():
    for key, entry in publication.load_registry().items():
        if not entry["publish"]["allowed"]:
            continue
        citation = publication.quote_attribution(record(file=key))
        assert key not in citation
        assert not re.search(r"[A-Za-z]", citation)
        assert f"«{entry['title']}»" in citation
        assert ", с. 39" in citation
        assert entry["title_provenance"].get("heading") or entry["title_provenance"].get("title_text")
        if re.search(r"-20\d\d-[12]$", key):
            assert entry["part"] in (1, 2)
            assert entry["title_provenance"]["part_label"]


def test_unconfirmed_title_cannot_publish_even_with_allow_claim():
    entries = publication.load_registry()
    entries[BOOK]["title_provenance"] = None
    with pytest.raises(ValueError, match=r"^publication_attribution:"):
        publication.quote_attribution(record(), entries)
    for key, entry in entries.items():
        if entry["publish"].get("reason") == "title_unconfirmed":
            with pytest.raises(ValueError, match=r"^publication_right:"):
                publication.quote_attribution(record(file=key), entries)


def test_grade_ranges_and_parts_are_recorded_data():
    entries = publication.load_registry()
    key = "10-11-klas-mystectvo-nazarenko-2018"
    assert entries[key]["grade"] == 10
    assert entries[key]["grade_end"] == 11
    assert publication.quote_attribution(record(file=key, page=12)) == "Назаренко, «Мистецтво», 10–11 клас, 2018, с. 12"
    entries[BOOK]["part"] = 7
    assert "ч. 7" in publication.quote_attribution(record(), entries)


@pytest.mark.parametrize(
    "field,value",
    [
        ("grade_end", 0),
        ("grade_end", "11"),
        ("part", 0),
        ("part", True),
        ("title", BOOK),
        ("title", "English"),
        ("author", "Author"),
    ],
)
def test_invalid_bibliography_cannot_reach_learner(field, value):
    entries = publication.load_registry()
    entries[BOOK][field] = value
    with pytest.raises(ValueError, match=r"^publication_attribution:"):
        publication.quote_attribution(record(), entries)
