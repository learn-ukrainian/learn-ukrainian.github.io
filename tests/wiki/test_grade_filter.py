# #1340 (2026-04-20): grade filter REMOVED. CEFR L2 levels do not map onto
# Ukrainian L1 school grades, and dense rerank handles topic relevance natively.
# These tests now assert the OPPOSITE of #1339: that no a-priori grade gate
# is applied, and that search_textbooks returns rows from across the full
# Grades 1-11 corpus when the keywords are broad enough.
#
# If a future change re-introduces grade-aware retrieval, prefer a SOFT
# prior (additive boost in dense rerank) over a hard SQL filter, and
# update these tests to reflect the new contract — do not silently restore
# the old assertion.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))


A1_PLAYBACK_KEYWORDS = {
    "голосний",
    "голосні",
    "добре",
    "звук",
    "звуки",
    "літера",
    "літери",
    "мама",
    "молоко",
    "нормально",
    "привіт",
    "приголосний",
    "приголосні",
    "підсумок",
    "справи",
    "тато",
    "чудово",
}


def test_search_textbooks_does_not_apply_hard_grade_filter():
    """A1 retrieval must reach Grade 5+ phonetics chunks (not just Grades 1-4).

    Grade 5+ Ukrainian-language textbooks contain the explicit, systematic
    phonetics treatment that adult L2 A1 learners benefit from (see
    sounds-letters-and-hello-knowledge-packet.md). Pre-filtering them out
    by grade — as #1339 did — strands relevant pedagogy in unreachable
    rows. This test guards against accidental reintroduction of that gate.
    """
    from wiki import sources_db

    # The deprecation note explicitly removed the symbol; tests must not
    # depend on it.
    assert not hasattr(sources_db, "_TRACK_GRADE_RANGES"), (
        "_TRACK_GRADE_RANGES was removed in #1340; do not re-add it as a "
        "hard SQL filter. If you need a soft prior, build a separate "
        "rerank-time boost rather than a SQL gate."
    )

    results = sources_db.search_textbooks(
        A1_PLAYBACK_KEYWORDS,
        max_total=40,
        track="a1",
    )

    assert results, "search_textbooks should still return results for A1 keywords"
    returned_grades = {str(row["grade"]).strip() for row in results if row.get("grade") is not None}
    # The whole point: at least one Grade 5+ row must come through, otherwise
    # we still have a hidden filter somewhere.
    grade_5_plus = {grade for grade in returned_grades if grade.isdigit() and int(grade) >= 5}
    assert grade_5_plus, (
        f"Expected Grade 5+ chunks to be reachable for A1 retrieval after #1340, "
        f"got only grades: {sorted(returned_grades)}"
    )
