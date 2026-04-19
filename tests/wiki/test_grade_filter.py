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


def test_search_textbooks_a1_track_stays_within_grades_1_to_4():
    from wiki import sources_db

    assert sources_db._TRACK_GRADE_RANGES["a1"] == ("1", "2", "3", "4")

    results = sources_db.search_textbooks(
        A1_PLAYBACK_KEYWORDS,
        max_total=40,
        track="a1",
    )

    assert results
    returned_grades = {str(row["grade"]).strip() for row in results}
    assert returned_grades <= {"1", "2", "3", "4"}
    assert returned_grades & {"3", "4"}
