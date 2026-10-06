"""SYNTHETIC per-hyphen decisions through actual held SQLite snapshots."""

import json
import sqlite3

import pytest

from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.snapshot import SnapshotReader
from scripts.projects.open_model_data.review_build.transforms import (
    Result,
    fold_word,
    source_text_defects,
    transform,
    unresolved_overlaps,
)


@pytest.fixture
def held(tmp_path):
    source, vesum = tmp_path / "SYNTHETIC-source.db", tmp_path / "SYNTHETIC-vesum.db"
    with sqlite3.connect(source) as db:
        db.execute(
            "CREATE TABLE texts(id INTEGER PRIMARY KEY, source_id TEXT, text TEXT, alternatives TEXT, count INTEGER)"
        )
    with sqlite3.connect(vesum) as db:
        db.execute("CREATE TABLE forms(id INTEGER PRIMARY KEY, form TEXT, folded TEXT)")
    policy = {
        "store": "vesum.db",
        "table": "forms",
        "field": "form",
        "lookup_field": "folded",
        "normalizer": "vesum_fold",
        "witness": {
            "store": "sources.db",
            "table": "texts",
            "field": "text",
            "source_column": "source_id",
            "source_id": "SYNTHETIC",
            "alternatives_field": "alternatives",
            "count_field": "count",
        },
    }

    def run(text, forms=(), witnesses=(), alternatives=()):
        with sqlite3.connect(source) as db:
            db.executemany(
                "INSERT INTO texts VALUES(?,?,?,?,?)",
                [
                    (
                        i,
                        "SYNTHETIC",
                        t,
                        json.dumps(list(alternatives)) if i == 1 else "[]",
                        len(alternatives) if i == 1 else 0,
                    )
                    for i, t in enumerate((text, *witnesses), 1)
                ],
            )
        with sqlite3.connect(vesum) as db:
            db.executemany("INSERT INTO forms VALUES(?,?,?)", [(i, f, fold_word(f)) for i, f in enumerate(forms, 1)])
        with SnapshotReader({"sources.db": source, "vesum.db": vesum}) as reader:
            result = transform("dehyphenate@2", text, policy, reader)
            return result, source_text_defects(result.text, policy, reader, original=text), reader.snapshots()

    run.source, run.vesum, run.policy = source, vesum, policy
    return run


@pytest.mark.parametrize(
    "forms,witnesses,expected,kind,unresolved",
    [
        (["SYNTHETICmore"], [], "SYNTHETICmore", "vesum_form", False),
        ([], ["SYNTHETICmore"], "SYNTHETICmore", "held_text", False),
        (["SYNTHETIC-more"], [], "SYNTHETIC-more", "vesum_hyphenated_form", False),
        (["SYNTHETICmore", "SYNTHETIC-more"], [], "SYNTHETIC-\nmore", None, True),
        (["SYNTHETIC-more"], ["SYNTHETICmore"], "SYNTHETIC-more", "vesum_hyphenated_form", False),
        ([], [], "SYNTHETIC-\nmore", None, True),
    ],
)
def test_every_decision_branch_and_join_refusal(held, forms, witnesses, expected, kind, unresolved):
    result, _, pins = held("SYNTHETIC-\nmore", forms, witnesses, ["SYNTHETIC-more"])
    assert result.text == expected
    assert bool(result.unresolved) == unresolved
    assert [e[3] for e in result.join_evidence] == ([kind] if kind else [])
    assert bool(result.joins) == (kind in {"held_text", "vesum_form"})
    assert "sources.db:texts" in pins


@pytest.mark.parametrize(
    "raw,alternative",
    [
        ("SYNTHETIC-\nmore", "SYNTHETIC-more"),
        ("SYNTHETIC- \r\n more", "SYNTHETICmore"),
        ("SYNTHETIC-more", "SYNTHETICmore"),
        ("SYNTHETIC-more", "SYNTHETIC-more"),
        ("SYŃTHETIC-\nmore", "SYNTHETIC-more"),
        ("SYN’THETIC-\nmore", "SYN’THETIC-more"),
    ],
)
def test_stored_inline_and_printed_alternatives_stress_and_apostrophes(held, raw, alternative):
    target = raw.replace("- \r\n ", "").replace("-\n", "").replace("-", "")
    result, _, _ = held(raw, [fold_word(target)], [], [alternative])
    assert result.text == target
    assert not result.unresolved
    assert result.join_evidence[0][3] == "vesum_form"


def test_proper_name_form_case_is_attested_by_folded_index(held):
    result, _, _ = held("Syn-\nThetic", ["SynThetic"], [], ["Syn-Thetic"])
    assert result.text == "SynThetic"
    assert not result.unresolved


@pytest.mark.parametrize(
    "witness",
    ["prefixSYNTHETICmore", "SYNTHETICmoreSuffix", "other-SYNTHETICmore", "SYNTHETICmore-other", "SYŃTHETIC-more"],
)
def test_held_witness_must_be_whole_unhyphenated_token(held, witness):
    result, _, _ = held("SYNTHETIC-\nmore", [], [witness], ["SYNTHETIC-more"])
    assert result.unresolved
    assert not result.joins


def test_unmatched_and_duplicate_alternatives_stay_unresolved(held):
    result, _, _ = held(
        "SYNTHETIC-\nmore", ["SYNTHETICmore"], [], ["SYNTHETIC-more", "SYNTHETIC-more", "OTHER-reading"]
    )
    assert len(result.unresolved) == 2
    assert result.unresolved[0][0] == -1


def test_raw_split_precedes_unrelated_inline_alternative(held):
    result, _, _ = held("SYNTHETIC-more and SYNTHETIC-\nmore", ["SYNTHETICmore"], [], ["SYNTHETIC-more"])
    assert result.text == "SYNTHETIC-more and SYNTHETICmore"
    assert len(result.joins) == 1


def test_mixed_resolved_and_unresolved_splits(held):
    result, _, _ = held("SYNTHETIC-\nmore UNKNOWN-\nmore", ["SYNTHETICmore"], [], ["SYNTHETIC-more", "UNKNOWN-more"])
    assert len(result.joins) == len(result.unresolved) == 1


@pytest.mark.parametrize(
    "forms,witnesses,defect",
    [
        (["ALPHA", "BETA"], ["ALPHA BETA"], True),
        (["ALPHA", "BETA", "ALPHABETA"], ["ALPHA BETA"], True),
        (["ALPHA", "BETA"], ["ALPHA BETA ALPHABETA"], False),
        (["ALPHA", "BETA"], [], False),
        (["ALPHA"], ["ALPHA BETA"], True),
    ],
)
def test_source_defect_signal_requires_positive_original_boundary_evidence(held, forms, witnesses, defect):
    held("SYNTHETIC unrelated", forms, witnesses)
    with SnapshotReader({"sources.db": held.source, "vesum.db": held.vesum}) as reader:
        assert not source_text_defects("ALPHABETA", held.policy, reader, original="ALPHABETA")
        original = witnesses[0] if witnesses else "SYNTHETIC other text"
        defects = source_text_defects("ALPHABETA", held.policy, reader, original=original)
        assert bool(defects) == defect
        assert not source_text_defects("ALPHABETA", held.policy, reader)


@pytest.mark.parametrize("span,expected", [(None, True), ((0, 3), False), ((3, 8), True), ((8, 12), False)])
def test_unresolved_visibility_uses_transformed_offsets_and_half_open_spans(span, expected):
    result = Result("SYNTHETIC", join_evidence=((0, 5, "ABC", "held_text"),), unresolved=((5, 10, "UNKNOWN"),))
    assert unresolved_overlaps(result, span) is expected


def test_unlocated_metadata_is_unknown_for_every_carried_span():
    assert unresolved_overlaps(Result("SYNTHETIC", unresolved=((-1, -1, "UNKNOWN"),)), (0, 3))
    assert not unresolved_overlaps(Result("SYNTHETIC"), None)


@pytest.mark.parametrize(
    "original,text,expected",
    [
        ("SYNTHETIC PART MORE and PART-\nMORE", "SYNTHETIC PART MORE and PARTMORE", ()),
        ("SYNTHETIC PART-\nMORE", "SYNTHETIC PART-MORE", ()),
        ("SYNTHETIC PART\nMORE", "SYNTHETIC PARTMORE", ("PARTMORE",)),
        ("SYNTHETIC PART MORE and PARTMORE", "SYNTHETIC PARTMORE and PARTMORE", ("PARTMORE",)),
    ],
)
def test_boundary_detector_requires_a_lost_separator_at_the_actual_position(original, text, expected):
    assert source_text_defects(text, {}, None, original=original) == expected


def test_v2_requires_held_reader():
    with pytest.raises(BuildError, match="transform_policy"):
        transform("dehyphenate@2", "SYNTHETIC-\nmore")


@pytest.mark.parametrize("alternatives,count", [("invalid", 0), ("{}", 0), ("[1]", 1), ("[]", 1), (" []", 0)])
def test_metadata_unavailable_fails_closed(held, alternatives, count):
    with sqlite3.connect(held.source) as db:
        db.execute("INSERT INTO texts VALUES(1,'SYNTHETIC','SYNTHETIC',?,?)", (alternatives, count))
    with SnapshotReader({"sources.db": held.source, "vesum.db": held.vesum}) as reader:
        with pytest.raises(BuildError, match="hyphen_metadata_unavailable"):
            reader.text_metadata("SYNTHETIC", held.policy)


def test_identical_text_conflicting_metadata_is_not_arbitrarily_selected(held):
    with sqlite3.connect(held.source) as db:
        db.executemany(
            "INSERT INTO texts VALUES(?,'SYNTHETIC','SYNTHETIC',?,?)", [(1, "[]", 0), (2, '["SYNTHETIC-other"]', 1)]
        )
    with SnapshotReader({"sources.db": held.source, "vesum.db": held.vesum}) as reader:
        with pytest.raises(BuildError, match="hyphen_metadata_unavailable"):
            reader.text_metadata("SYNTHETIC", held.policy)


def test_held_source_filter_and_metadata_are_pinned(held):
    with sqlite3.connect(held.source) as db:
        db.executemany(
            "INSERT INTO texts VALUES(?,?,?,?,?)",
            [(1, "SYNTHETIC", "SYNTHETIC-\nmore", "[]", 0), (2, "OTHER", "SYNTHETICmore", "[]", 0)],
        )
    with SnapshotReader({"sources.db": held.source, "vesum.db": held.vesum}) as reader:
        result = transform("dehyphenate@2", "SYNTHETIC-\nmore", held.policy, reader)
        assert result.unresolved
        pins = reader.snapshots()
    with sqlite3.connect(held.source) as db:
        db.execute("UPDATE texts SET alternatives=?,count=1 WHERE id=1", ('["SYNTHETIC-more"]',))
    with SnapshotReader({"sources.db": held.source, "vesum.db": held.vesum}) as reader:
        reader.held_texts(held.policy)
        assert reader.snapshots() != pins


@pytest.mark.parametrize(
    "raw,forms,expected,unresolved",
    [
        ("OTHER-SYNTHETIC-\nmore", ["SYNTHETICmore"], "OTHER-SYNTHETIC-\nmore", True),
        ("OTHER-SYNTHETIC-\nmore", ["OTHER-SYNTHETICmore"], "OTHER-SYNTHETICmore", False),
        ("SYNTHETIC-\nmore-OTHER", ["SYNTHETICmore-OTHER"], "SYNTHETICmore-OTHER", False),
        ("-SYNTHETIC-\nmore", ["SYNTHETICmore"], "-SYNTHETIC-\nmore", True),
        ("7SYNTHETIC-\nmore", ["SYNTHETICmore"], "7SYNTHETIC-\nmore", True),
        ("SYNTHETIC-\nmore7", ["SYNTHETICmore"], "SYNTHETIC-\nmore7", True),
    ],
)
def test_complete_compound_and_malformed_boundaries(held, raw, forms, expected, unresolved):
    result, _, _ = held(raw, forms, [], ["SYNTHETIC-more"])
    assert result.text == expected
    assert bool(result.unresolved) == unresolved
