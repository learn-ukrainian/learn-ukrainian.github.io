"""The frozen review-scoring contract (#9623, designated decision 2026-10-03).

Oracle cases are the worked table of the approved amendment; every expected count
is written here as a literal, never computed by the code under test. Columns:
(hits, protected spans affected, changed correct tokens, extra insertion sites,
wrong corrections). The decision's third column ("other false alarms") is the sum
of the token and insertion columns.
"""

from __future__ import annotations

import inspect
import itertools
import json
import random
from pathlib import Path
from typing import Any

import pytest

from scripts.eval.uk_preamble import scoring
from scripts.eval.uk_preamble.common import HarnessError, token_keys, tokenize
from scripts.eval.uk_preamble.dataset import ReviewItem, Span, load_set, review_geometry
from scripts.eval.uk_preamble.prompts import validate_response
from scripts.eval.uk_preamble.scoring import align, review_counts, score_review_item

# --------------------------------------------------------------------------- builders


def _span(text: str, fragment: str | int, ident: str, kind: str, accepted=(), occurrence: int = 0) -> Span:
    """A span over ``fragment`` (its ``occurrence``-th match), or an empty span at an integer offset."""
    if isinstance(fragment, int):
        return Span(ident, fragment, fragment, "", kind, tuple(accepted))
    start = -1
    for _ in range(occurrence + 1):
        start = text.index(fragment, start + 1)
    return Span(ident, start, start + len(fragment), fragment, kind, tuple(accepted))


def make_item(text: str, errors=(), protected=()) -> ReviewItem:
    """``errors``: (fragment or offset, accepted forms[, occurrence]); ``protected``: fragments."""
    return ReviewItem(
        "T",
        text,
        tuple(_span(text, error[0], f"e{k}", "other", error[1], *error[2:]) for k, error in enumerate(errors)),
        tuple(_span(text, fragment, f"p{k}", "regional") for k, fragment in enumerate(protected)),
    )


def counts(item: ReviewItem, corrected: str) -> tuple[int, int, int, int, int]:
    c = review_counts(item, corrected)
    return len(c.hits), len(c.protected), len(c.tokens), len(c.insertions), len(c.wrong)


def schema_valid(text: str, corrected: str, corrections: list[dict[str, Any]]) -> dict[str, Any]:
    """An answer entry that has passed the real response validator."""
    entry = {"id": "T", "corrected_text": corrected, "corrections": corrections, "style_suggestions": []}
    (result,) = validate_response("review", json.dumps({"items": [entry]}, ensure_ascii=False), ["T"])
    assert result.error is None, result.error
    return result.entry


def claim(text: str, start: int, end: int, replacement: str, span: str | None = None) -> dict[str, Any]:
    return {
        "span": text[start:end] if span is None else span,
        "start": start,
        "end": end,
        "correction": replacement,
        "error_type": "other",
        "evidence": "test",
    }


# --------------------------------------------------------------------------- oracle table

C5_TEXT = "Ми слухали цікаву лекцію на протязі години."
C6_TEXT = "Тарас Шевченко і Леся Українка писали на протязі життя."
C9B_TEXT = "Діяли відповідно наказу."

ORACLE = {
    # R1a: a fix plus a neighbouring rewrite (one claim or none: claims never matter).
    "R1a": (make_item("bad safe", [("bad", ["good"])]), "good fine", (1, 0, 1, 0, 0)),
    # R1b: two fixes around an unchanged protected span.
    "R1b": (
        make_item("bad1 prot bad2", [("bad1", ["good1"]), ("bad2", ["good2"])], ["prot"]),
        "good1 prot good2",
        (2, 0, 0, 0, 0),
    ),
    # R2: round-2 probe; the suffix growth on a correct word is one changed token.
    "R2": (make_item("bad safe", [("bad", ["good"])]), "good safer", (1, 0, 1, 0, 0)),
    # R3: round-3 probe; the deleted repeated token is one false alarm.
    "R3": (make_item("safe safe bad", [("bad", ["good"])]), "safe  good", (1, 0, 1, 0, 0)),
    # C5: multi-token collateral rewrite; character costs keep the seed's fix on the seed.
    "C5": (
        make_item(C5_TEXT, [("на протязі години", ["протягом години", "упродовж години"])]),
        "Ми прослухали надзвичайно цікаву доповідь протягом години.",
        (1, 0, 2, 1, 0),
    ),
    # C6: one run across two protected spans; each span counts once, "і" once.
    "C6": (
        make_item(C6_TEXT, [("на протязі життя", ["протягом життя"])], ["Тарас Шевченко", "Леся Українка"]),
        "Поети писали протягом життя.",
        (1, 2, 1, 0, 0),
    ),
    # C7: adjacent seeds, one-for-one.
    "C7": (
        make_item("Цей пункт являється слідуючим кроком.", [("являється", ["є"]), ("слідуючим", ["наступним"])]),
        "Цей пункт є наступним кроком.",
        (2, 0, 0, 0, 0),
    ),
    # C7c: adjacent seeds whose fixes change the number of words (X -> A, Y -> C D).
    "C7c": (make_item("X Y", [("X", ["A"]), ("Y", ["C D"])]), "A C D", (2, 0, 0, 0, 0)),
    # C7d: X -> A B, Y -> C D.
    "C7d": (make_item("X Y", [("X", ["A B"]), ("Y", ["C D"])]), "A B C D", (2, 0, 0, 0, 0)),
    # C8: repeated-token tie; the seed is the second A.
    "C8": (make_item("p A x A q", [("A", ["B"], 1)]), "p A B q", (1, 0, 1, 0, 0)),
    # C8b: DOCUMENTED RESIDUAL. The seed is the first A; the text alone is ambiguous and the
    # fixed tie order deletes the seed, so the fix is a miss and x counts as changed.
    "C8b": (make_item("p A x A q", [("A", ["B"], 0)]), "p B A q", (0, 0, 1, 0, 1)),
    # C9a: an insertion at a seed's edge that the accepted form does not need is collateral.
    "C9a": (make_item("x bad y", [("bad", ["good"])]), "x very good y", (1, 0, 0, 1, 0)),
    # C9b: a narrow seed whose accepted form needs the edge insertion (left, then right edge).
    "C9b-left": (make_item(C9B_TEXT, [("наказу", ["до наказу"])]), "Діяли відповідно до наказу.", (1, 0, 0, 0, 0)),
    "C9b-right": (
        make_item(C9B_TEXT, [("відповідно", ["відповідно до"])]),
        "Діяли відповідно до наказу.",
        (1, 0, 0, 0, 0),
    ),
    # C10a: an insertion at a protected span's edge is an ordinary insertion site.
    "C10a": (
        make_item("Збірка «Кобзар» уперше вийшла 1840 року.", [], ["«Кобзар»"]),
        "Збірка «Кобзар», уперше вийшла 1840 року.",
        (0, 0, 0, 1, 0),
    ),
    # C10b: an insertion strictly inside a protected span affects it.
    "C10b": (
        make_item("Вірш написав Тарас Шевченко.", [], ["Тарас Шевченко"]),
        "Вірш написав Тарас Григорович Шевченко.",
        (0, 1, 0, 0, 0),
    ),
}


@pytest.mark.parametrize("case", list(ORACLE))
def test_oracle_table(case):
    item, corrected, expected = ORACLE[case]
    assert counts(item, corrected) == expected


def test_c8b_residual_is_pinned():
    """The documented residual: if this starts crediting the seed, the contract changed and needs a decision."""
    item, corrected, _ = ORACLE["C8b"]
    result = review_counts(item, corrected)
    assert result.hits == frozenset() and result.wrong == frozenset({"e0"})


def test_oracle_counts_feed_the_scored_record():
    item, corrected, _ = ORACLE["C5"]
    record = score_review_item(item, schema_valid(item.text, corrected, []))
    assert (record["hits"], record["fa_protected"], record["fa_tokens"], record["fa_insertions"]) == (1, 0, 2, 1)
    assert record["false_alarms"] == 3 and record["fa_inserted_tokens"] == 1


# --------------------------------------------------------------------------- the reviewers' and Sol's probes


def test_probe_round1_combined_fix_and_correct_text_rewrite_is_one_false_alarm():
    text = "Цей пункт являється без сумніву слідуючим кроком."
    item = make_item(text, [("являється", ["є"]), ("слідуючим", ["наступним"])], ["без сумніву"])
    assert counts(item, "Цей пункт є без сумніву наступним кроком.") == (2, 0, 0, 0, 0)
    assert counts(item, "Цей пункт є без сумніву наступним етапом.") == (2, 0, 1, 0, 0)
    assert counts(item, "Цей пункт є безперечно наступним кроком.") == (2, 1, 0, 0, 0)


@pytest.mark.parametrize(
    "corrections",
    [
        [claim("bad safe", 0, 3, "good"), claim("bad safe", 4, 8, "safer")],
        [claim("bad safe", 0, 3, "good"), claim("bad safe", 8, 8, "r")],
        [claim("bad safe", 0, 8, "good safer")],
        [],
    ],
    ids=["word", "insertion", "combined", "unlogged"],
)
def test_probe_round2_safe_to_safer_scores_one_false_alarm_however_logged(corrections):
    item = make_item("bad safe", [("bad", ["good"])])
    record = score_review_item(item, schema_valid("bad safe", "good safer", corrections))
    assert (record["hits"], record["false_alarms"], record["fa_tokens"]) == (1, 1, 1)


@pytest.mark.parametrize(
    "corrections",
    [
        [claim("safe safe bad", 5, 9, ""), claim("safe safe bad", 10, 13, "good")],
        [claim("safe safe bad", 0, 13, "safe  good")],
        [],
    ],
    ids=["separate", "combined", "empty"],
)
def test_probe_round3_repeated_token_is_one_hit_and_one_false_alarm_however_logged(corrections):
    item = make_item("safe safe bad", [("bad", ["good"])])
    record = score_review_item(item, schema_valid("safe safe bad", "safe  good", corrections))
    assert (record["hits"], record["false_alarms"], record["fa_tokens"], record["wrong_corrections"]) == (1, 1, 1, 0)


def test_probe_wrong_correction_confined_to_seed_is_a_miss_not_a_false_alarm():
    item = make_item("x bad y", [("bad", ["good"])])
    assert counts(item, "x worse y") == (0, 0, 0, 0, 1)


PAIR_TEXT = "p badone badtwo q"
PAIR_ERRORS = [("badone", ["goodone"]), ("badtwo", ["goodtwo"])]
PAIR = make_item(PAIR_TEXT, PAIR_ERRORS)
TRIPLE = make_item(
    "p badone badtwo badthree q", [("badone", ["goodone"]), ("badtwo", ["goodtwo"]), ("badthree", ["goodthree"])]
)
# The second seed's accepted form needs the insertion between the seeds (like ``відповідно до``).
NEEDS_INNER = make_item("p badfirst badsecond q", [("badfirst", ["goodfirst"]), ("badsecond", ["до goodsecond"])])

# Designated decision 2026-10-03 (2) on #9623 (rule by gpt-6.1-sol, approved with amendments by
# claude-opus-5-5): a wrong correction is a miss, never a false alarm, for a seed's own tokens and
# the insertions strictly inside it; an insertion at a seed's edge, including between two seeds, is
# collateral unless an accepted form needs it. Every row is the decision's hand count.
CLUSTER_ORACLE = {
    "pair-both-correct": (PAIR, "p goodone goodtwo q", (2, 0, 0, 0, 0)),
    "pair-both-correct-inner-insertion": (PAIR, "p goodone extra goodtwo q", (2, 0, 0, 1, 0)),
    # The conformance review's reproduction: making both fixes worse never removes the insertion's false alarm.
    "pair-both-wrong-inner-insertion": (PAIR, "p worseone extra worsetwo q", (0, 0, 0, 1, 2)),
    "pair-correct-wrong-inner-insertion": (PAIR, "p goodone extra worsetwo q", (1, 0, 0, 1, 1)),
    "pair-wrong-correct-inner-insertion": (PAIR, "p worseone extra goodtwo q", (1, 0, 0, 1, 1)),
    "pair-both-untouched-inner-insertion": (PAIR, "p badone extra badtwo q", (0, 0, 0, 1, 0)),
    "pair-both-correct-outer-left-insertion": (PAIR, "p very goodone goodtwo q", (2, 0, 0, 1, 0)),
    "pair-both-correct-outer-right-insertion": (PAIR, "p goodone goodtwo very q", (2, 0, 0, 1, 0)),
    # aax -> aaa, insert bbb between the seeds, yyy -> zzz: aax's slice plus its right edge is its
    # accepted form "aaa bbb", so the insertion is used and earns no false alarm.
    "inner-insertion-used-as-edge": (
        make_item("p aax yyy q", [("aax", ["aaa bbb"]), ("yyy", ["ccc"])]),
        "p aaa bbb zzz q",
        (1, 0, 0, 0, 1),
    ),
    # Opus: the inner "до" is consumed by the second seed's accepted form ...
    "inner-insertion-needed-by-accepted-form": (NEEDS_INNER, "p worsefirst до goodsecond q", (1, 0, 0, 0, 1)),
    # ... and is collateral when no accepted form uses it (documented edge case), as for one seed:
    "inner-insertion-not-needed-next-to-wrong": (NEEDS_INNER, "p worsefirst до worsesecond q", (0, 0, 0, 1, 2)),
    "single-seed-wrong-with-edge-insertion": (
        make_item("x bad y", [("bad", ["good"])]),
        "x worse extra y",
        (0, 0, 0, 1, 1),
    ),
    # Opus: both seeds want the shared B; the first seed in edge-use order takes it, the second cannot reuse it.
    "shared-insertion-first-seed-takes-it": (
        make_item("p X Y q", [("X", ["A B"]), ("Y", ["B C"])]),
        "p A B C q",
        (1, 0, 0, 0, 1),
    ),
    # Documented edge case: text fused into a seed's own token is a wrong correction, not a false alarm.
    "text-fused-into-seed-token": (PAIR, "p goodoneextra goodtwo q", (1, 0, 0, 0, 1)),
    # Three adjacent seeds with unused insertions in both gaps: h/0/2/0/(3-h) in the decision's order.
    "triple-correct-correct-correct": (TRIPLE, "p goodone extra goodtwo more goodthree q", (3, 0, 0, 2, 0)),
    "triple-correct-correct-wrong": (TRIPLE, "p goodone extra goodtwo more worsethree q", (2, 0, 0, 2, 1)),
    "triple-correct-wrong-correct": (TRIPLE, "p goodone extra worsetwo more goodthree q", (2, 0, 0, 2, 1)),
    "triple-correct-wrong-wrong": (TRIPLE, "p goodone extra worsetwo more worsethree q", (1, 0, 0, 2, 2)),
    "triple-wrong-correct-correct": (TRIPLE, "p worseone extra goodtwo more goodthree q", (2, 0, 0, 2, 1)),
    "triple-wrong-correct-wrong": (TRIPLE, "p worseone extra goodtwo more worsethree q", (1, 0, 0, 2, 2)),
    "triple-wrong-wrong-correct": (TRIPLE, "p worseone extra worsetwo more goodthree q", (1, 0, 0, 2, 2)),
    "triple-wrong-wrong-wrong": (TRIPLE, "p worseone extra worsetwo more worsethree q", (0, 0, 0, 2, 3)),
}


@pytest.mark.parametrize("case", list(CLUSTER_ORACLE))
def test_insertions_between_and_around_adjacent_seeds(case):
    """The decision's worked cases; with no claims the unapplied diagnostic (its fourth column) is 0."""
    item, corrected, expected = CLUSTER_ORACLE[case]
    assert counts(item, corrected) == expected
    record = score_review_item(item, schema_valid(item.text, corrected, []))
    assert record["logging"]["unapplied_claims"] == 0


def test_probe_joining_two_words_is_a_real_change():
    """Writing words together or apart is its own normative domain: не має -> немає counts both tokens."""
    item = make_item("Він не має часу.")
    assert counts(item, "Він немає часу.") == (0, 0, 2, 0, 0)


# --------------------------------------------------------------------------- invariance to every claim list


def _apply(text: str, edits: list[tuple[int, int, str]]) -> str:
    for start, end, replacement in reversed(edits):
        text = text[:start] + replacement + text[end:]
    return text


def _partitions(items: list[int]):
    if not items:
        yield []
        return
    first, rest = items[0], items[1:]
    for partition in _partitions(rest):
        yield [[first], *partition]
        for k in range(len(partition)):
            yield [*partition[:k], [first, *partition[k]], *partition[k + 1 :]]


def _groupings(text: str, edits: list[tuple[int, int, str]]) -> list[list[dict[str, Any]]]:
    """Every partition of ``edits`` (disjoint, in source order), each block logged as one claim over its extent.

    A block's claim covers the source from its first edit's start to its last
    edit's end and replaces it with that stretch as corrected (other edits lying
    inside the extent included), so blocks may overlap edits of other blocks.
    """

    def block_claim(block: list[int]) -> dict[str, Any]:
        start, end = min(edits[k][0] for k in block), max(edits[k][1] for k in block)
        inside = [
            (s - start, e - start, r)
            for k, (s, e, r) in enumerate(edits)
            if k in block or (start <= s and e <= end and not (s == e and s in (start, end)))
        ]
        return claim(text, start, end, _apply(text[start:end], inside))

    return [[block_claim(block) for block in partition] for partition in _partitions(list(range(len(edits))))]


def _claim_lists(text: str, edits: list[tuple[int, int, str]], rng: random.Random):
    """Schema-valid claim lists for one corrected text, seeded, and exhaustive over groupings.

    Empty; every partition of the edits; and each of those with irrelevant,
    unapplied, duplicated, unanchored, relocated and no-op claims mixed in.
    """
    groupings = [[], *_groupings(text, edits)]
    noise_pool = [
        claim(text, 0, 0, "Отже, "),
        claim(text, len(text), len(text), " Кінець."),
        {**claim(text, 0, 3, "zzz"), "span": "неіснуючий фрагмент"},
        {**claim(text, 0, 1, "Q"), "start": len(text), "end": len(text)},
    ]
    for _ in range(6):
        start = rng.randrange(len(text))
        end = rng.randrange(start, len(text) + 1)
        noise_pool.append(claim(text, start, end, rng.choice(["", "x", "інше слово", text[start:end], "—"])))
    lists = list(groupings)
    for grouping in groupings:
        for _ in range(4):
            mixed = grouping + rng.sample(noise_pool, rng.randrange(1, 4))
            if grouping and rng.random() < 0.5:
                mixed.append(grouping[0])
            rng.shuffle(mixed)
            lists.append(mixed)
    return _apply(text, edits), lists


INVARIANCE = [
    # (text, errors, protected, edits, expected primary counts)
    ("safe safe bad", [("bad", ["good"])], [], [(5, 9, ""), (10, 13, "good")], (1, 0, 1, 0, 0)),
    (
        "Цей пункт являється без сумніву слідуючим кроком.",
        [("являється", ["є"]), ("слідуючим", ["наступним"])],
        ["без сумніву"],
        [(10, 19, "є"), (20, 31, "безперечно"), (32, 41, "наступним"), (42, 48, "етапом")],
        (2, 1, 1, 0, 0),
    ),
    ("Я знаю що він прийде.", [(6, [","])], [], [(6, 6, ","), (10, 14, "")], (1, 0, 1, 0, 0)),
    ("X Y", [("X", ["A"]), ("Y", ["C D"])], [], [(0, 1, "A"), (2, 3, "C D")], (2, 0, 0, 0, 0)),
    ("x bad y", [("bad", ["good"])], [], [(2, 2, "very "), (2, 5, "good")], (1, 0, 0, 1, 0)),
    (PAIR_TEXT, PAIR_ERRORS, [], [(2, 8, "worseone"), (9, 9, "extra "), (9, 15, "worsetwo")], (0, 0, 0, 1, 2)),
]


@pytest.mark.parametrize(("text", "errors", "protected", "edits", "expected"), INVARIANCE)
def test_every_schema_valid_claim_list_gives_identical_primary_counts(text, errors, protected, edits, expected):
    item = make_item(text, errors, protected)
    primary_keys = ("hits", "fa_protected", "fa_tokens", "fa_insertions", "false_alarms", "wrong_corrections")
    for seed in range(3):
        corrected, lists = _claim_lists(text, edits, random.Random(9623 + seed))
        assert len(lists) >= 10
        seen = set()
        for corrections in lists:
            record = score_review_item(item, schema_valid(text, corrected, corrections))
            primary = tuple(record[k] for k in primary_keys)
            seen.add((primary, tuple(e["hit"] for e in record["errors"]), tuple(record["protected_touched"])))
            assert (record["hits"], record["fa_protected"], record["fa_tokens"], record["fa_insertions"]) == expected[
                :4
            ]
            assert record["wrong_corrections"] == expected[4]
        assert len(seen) == 1, seen


@pytest.mark.parametrize(("text", "errors", "protected", "edits", "expected"), INVARIANCE)
def test_claim_generator_logs_the_edits_faithfully(text, errors, protected, edits, expected):
    """Guard for the generator: every non-overlapping grouping, applied to the source, gives the corrected text."""
    corrected = _apply(text, edits)
    groupings = _groupings(text, edits)
    assert len(groupings) == [1, 1, 2, 5, 15][len(edits)]  # Bell numbers: every partition is generated
    for corrections in groupings:
        ordered = sorted(corrections, key=lambda c: (c["start"], c["end"]))
        if all(a["end"] <= b["start"] for a, b in itertools.pairwise(ordered)):
            assert _apply(text, [(c["start"], c["end"], c["correction"]) for c in ordered]) == corrected


# --------------------------------------------------------------------------- logging diagnostics


def test_broad_wrong_claim_covers_the_change_but_is_not_applied():
    text = "Ми обговорювали питання на протязі години."
    item = make_item(text, [("на протязі години", ["протягом години", "упродовж години"])])
    corrected = "Ми обговорювали питання протягом години."
    record = score_review_item(
        item, schema_valid(text, corrected, [claim(text, 0, len(text) - 1, "Ми впродовж години")])
    )
    assert record["hits"] == 1
    logging = record["logging"]
    assert (logging["change_units"], logging["claimed_change_units"]) == (1, 1)
    assert (logging["applied_claims"], logging["unapplied_claims"]) == (0, 1)


@pytest.mark.parametrize(
    ("text", "corrected", "corrections"),
    [
        ("bad safe", "good safer", [claim("bad safe", 0, 3, "good"), claim("bad safe", 8, 8, "r")]),
        ("Я знаю що він прийде.", "Я знаю, що він прийде.", [claim("Я знаю що він прийде.", 6, 6, ",")]),
        ("Я знаю що він прийде.", "Я знаю, що він прийде.", [claim("Я знаю що він прийде.", 7, 7, ", ")]),
        ("Я знаю що він прийде.", "Я знаю, що він прийде.", [claim("Я знаю що він прийде.", 2, 6, "знаю,")]),
    ],
    ids=["suffix-insertion", "comma-after-word", "comma-before-word", "comma-in-replacement"],
)
def test_claims_glued_to_words_are_read_with_them_and_count_as_applied(text, corrected, corrections):
    record = score_review_item(make_item(text), schema_valid(text, corrected, corrections))
    logging = record["logging"]
    assert (logging["applied_claims"], logging["unapplied_claims"], logging["noop_claims"]) == (len(corrections), 0, 0)
    assert logging["claimed_change_units"] == logging["change_units"]


def test_inserted_tokens_are_reported_but_an_insertion_site_counts_once():
    text = "Я прийду завтра."
    item = make_item(text)
    record = score_review_item(item, schema_valid(text, "Я прийду завтра, якщо буде змога і час.", []))
    assert (record["fa_insertions"], record["false_alarms"], record["fa_inserted_tokens"]) == (1, 1, 6)


# --------------------------------------------------------------------------- canonical alignment


def test_alignment_tie_order_and_character_costs():
    tags = lambda a, b: [op.tag for op in align(a.split(), b.split())]  # noqa: E731
    assert tags("p A x A q", "p A B q") == ["equal", "equal", "delete", "substitute", "equal"]
    assert tags("p A x A q", "p B A q") == ["equal", "delete", "substitute", "equal", "equal"]
    assert tags("safe safe bad", "safe good") == ["equal", "delete", "substitute"]
    assert tags("x bad y", "x very good y") == ["equal", "insert", "substitute", "equal"]
    # Character edits break the token-edit tie: "на" is deleted, "протязі" becomes "протягом".
    assert tags("на протязі", "протягом") == ["delete", "substitute"]
    # Token edits come first: one substitution beats a delete plus an insert even with no shared characters.
    assert tags("abc", "xyz") == ["substitute"]
    assert tags("", "") == [] and tags("a", "") == ["delete"] and tags("", "a") == ["insert"]


def test_alignment_is_deterministic_and_free_of_difflib():
    a, b = token_keys(C5_TEXT), token_keys("Ми прослухали надзвичайно цікаву доповідь протягом години.")
    assert align(a, b) == align(list(a), list(b)) == align(a, b)
    source = inspect.getsource(scoring)
    assert not hasattr(scoring, "difflib") and "import difflib" not in source and "SequenceMatcher" not in source


# --------------------------------------------------------------------------- tokeniser


@pytest.mark.parametrize(
    ("text", "keys"),
    [
        ("мʼята м'ята м’ята м‘ята", ("м'ята",) * 4),
        ("будь‑який будь‐який будь-який", ("будь-який",) * 3),
        ("во́да", ("во́да",)),
        ("сло­во", ("слово",)),
        ("a​b a‌b a‍b a⁠b ﻿ab", ("ab",) * 5),
        ("Так… ні... так.", ("Так", "...", "ні", "...", "так", ".")),
        ("a - b – c — d", ("a", "-", "b", "–", "c", "—", "d")),
        ('«Кобзар» "Кобзар"', ("«", "Кобзар", "»", '"', "Кобзар", '"')),
        ("a b\n\tc", ("a", "b", "c")),
        ("Київ київ", ("Київ", "київ")),
        ("йти", ("йти",)),
        ("-слово 'слово", ("-", "слово", "'", "слово")),
    ],
    ids=[
        "apostrophes",
        "hyphens",
        "stress-mark",
        "soft-hyphen",
        "zero-width",
        "ellipsis",
        "dashes-distinct",
        "quotes-distinct",
        "whitespace-never-a-token",
        "case-sensitive",
        "nfc",
        "edge-joiners",
    ],
)
def test_tokeniser_folding(text, keys):
    assert tuple(t.key for t in tokenize(text)) == keys


def test_token_offsets_point_into_the_original_text():
    text = "Мʼята… ось"
    tokens = tokenize(text)
    assert [(t.start, t.end) for t in tokens] == [(0, 5), (5, 6), (7, 10)]
    assert [text[t.start : t.end] for t in tokens] == ["Мʼята", "…", "ось"]


def test_stress_mark_on_a_correct_word_is_one_changed_token():
    item = make_item("Ми пили воду.")
    assert counts(item, "Ми пили во́ду.") == (0, 0, 1, 0, 0)
    assert counts(item, "Ми пили во­ду​.") == (0, 0, 0, 0, 0)


# --------------------------------------------------------------------------- dataset validation


def _write(tmp_path: Path, data: dict[str, Any]) -> Path:
    path = tmp_path / "set.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def _error(text: str, start: int, end: int, ident: str, accepted: list[str]) -> dict[str, Any]:
    return {
        "id": ident,
        "start": start,
        "end": end,
        "span": text[start:end],
        "error_type": "lexical-russianism",
        "accepted": accepted,
    }


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda r: r["errors"].__setitem__(0, _error(r["text"], 11, 19, "R3-e1", ["є"])), "token boundaries"),
        (lambda r: r["errors"].__setitem__(0, _error(r["text"], 10, 18, "R3-e1", ["є"])), "token boundaries"),
        (lambda r: r["errors"].append(_error(r["text"], 10, 29, "R3-e3", ["є наступним"])), "overlap"),
        (lambda r: r["errors"].append(_error(r["text"], 9, 10, "R3-e3", [","])), "no token"),
        (lambda r: r["errors"][0].update(accepted=["являється"]), "tokenises to the seed's own tokens"),
        (
            lambda r: r["protected"].append({"id": "R3-p1", "start": 4, "end": 7, "span": "пун", "kind": "x"}),
            "token boundaries",
        ),
    ],
    ids=[
        "seed-starts-mid-word",
        "seed-ends-mid-word",
        "seeds-overlap",
        "whitespace-only",
        "accepted-is-seed",
        "protected-mid-word",
    ],
)
def test_set_validation_refuses_spans_off_the_scoring_contract(tmp_path, mini_set_dict, mutate, message):
    r3 = next(r for r in mini_set_dict["review"] if r["id"] == "R3")
    assert r3["text"] == "Цей пункт являється слідуючим кроком."
    mutate(r3)
    with pytest.raises(HarnessError, match=message):
        load_set(_write(tmp_path, mini_set_dict))


def test_set_validation_refuses_apostrophe_variant_as_accepted_form(tmp_path, mini_set_dict):
    r2 = next(r for r in mini_set_dict["review"] if r["id"] == "R2")
    r2["protected"] = [p for p in r2["protected"] if p["id"] != "R2-p2"]
    start = r2["text"].index("п'ятницю")
    r2["errors"] = [_error(r2["text"], start, start + 8, "R2-e1", ["пʼятницю"])]
    with pytest.raises(HarnessError, match="tokenises to the seed's own tokens"):
        load_set(_write(tmp_path, mini_set_dict))


def test_set_validation_refuses_two_insertion_seeds_at_one_point():
    text = "Я знаю що він прийде."
    with pytest.raises(HarnessError, match="overlap"):
        review_geometry(make_item(text, [(6, [","]), (6, [";"])]))


def test_mini_set_passes_validation(tmp_path, mini_set_dict):
    eval_set = load_set(_write(tmp_path, mini_set_dict))
    assert [len(review_geometry(item).seeds) for item in eval_set.review] == [2, 0, 2, 1]
