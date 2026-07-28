"""Unit tests for #5917 activity case-drill audit gate on VESUM indeclinables."""

from scripts.audit.checks.activity_validation import check_indeclinable_case_drills
from scripts.yaml_activities import FillInActivity, FillInItem


def test_zavdiaky_case_drill_must_fail():
    """Acceptance test: case drill on 'завдяки' (prep) must FAIL the gate."""
    activity = FillInActivity(
        type="fill-in",
        title="Preposition Case Drill",
        instruction="Put the word „завдяки” in the correct case.",
        items=[
            FillInItem(
                sentence="___ допомозі друзів ми закінчили проект.",
                answer="Завдяки",
                options=["Завдяки", "Завдякам"],
            )
        ],
    )
    violations = check_indeclinable_case_drills([activity])
    assert len(violations) == 1
    assert violations[0]["type"] == "INDECLINABLE_CASE_DRILL"
    assert violations[0]["severity"] == "critical"
    assert "завдяки" in violations[0]["message"]
    assert "prep" in violations[0]["message"] or "prep" in violations[0]["pedagogical_issue"]


def test_real_noun_case_drill_must_pass():
    """Control test: case drill on 'книга' (noun) must PASS the gate."""
    activity = FillInActivity(
        type="fill-in",
        title="Noun Case Drill",
        instruction="Put the word „книга” in the correct case.",
        items=[
            FillInItem(
                sentence="Я читаю цікаву ___.",
                answer="книжку",
                options=["книга", "книжку", "книзі"],
            )
        ],
    )
    violations = check_indeclinable_case_drills([activity])
    assert len(violations) == 0


def test_numeral_case_drill_must_pass():
    """Control test: case drill on numeral 'два' (numr) must PASS the gate (#5956)."""
    activity = FillInActivity(
        type="fill-in",
        title="Numeral Case Drill",
        instruction="Put the number „два” in the correct case.",
        items=[
            FillInItem(
                sentence="У мене немає ___ гривень.",
                answer="двох",
                options=["два", "двох", "двом"],
            )
        ],
    )
    violations = check_indeclinable_case_drills([activity])
    assert len(violations) == 0


def test_indeclinable_neutral_prompt_must_pass():
    """Control test: neutral insertion prompt on 'завдяки' must PASS the gate."""
    activity = FillInActivity(
        type="fill-in",
        title="Preposition Practice",
        instruction="Fill in the blank with the word „завдяки”.",
        items=[
            FillInItem(
                sentence="___ допомозі друзів ми закінчили проект.",
                answer="Завдяки",
                options=["Завдяки", "Завдякам"],
            )
        ],
    )
    violations = check_indeclinable_case_drills([activity])
    assert len(violations) == 0


def test_indeclinable_noun_case_drill_must_fail():
    """Control test: case drill on indeclinable noun 'метро' must FAIL the gate."""
    activity = FillInActivity(
        type="fill-in",
        title="Indeclinable Noun Drill",
        instruction="Поставте слово „метро” у правильному відмінку.",
        items=[
            FillInItem(
                sentence="Ми їдемо в ___.",
                answer="метро",
                options=["метро"],
            )
        ],
    )
    violations = check_indeclinable_case_drills([activity])
    assert len(violations) == 1
    assert violations[0]["type"] == "INDECLINABLE_CASE_DRILL"
    assert "метро" in violations[0]["message"]


def test_ukrainian_adverb_case_drill_must_fail():
    """Case drill on 'згодом' (adv) with Ukrainian prompt must FAIL the gate."""
    activity = {
        "type": "fill-in",
        "title": "Adverb Drill",
        "instruction": "Поставте слово „згодом” у правильному відмінку.",
        "items": [
            {
                "sentence": "___ він відповів.",
                "answer": "згодом",
                "options": ["згодом", "потім"],
            }
        ],
    }
    violations = check_indeclinable_case_drills([activity])
    assert len(violations) == 1
    assert violations[0]["type"] == "INDECLINABLE_CASE_DRILL"
    assert "згодом" in violations[0]["message"]


def test_item_level_prompt_case_drill_must_fail():
    """Item-level prompt demanding case form of indeclinable must FAIL."""
    activity = {
        "type": "fill-in",
        "title": "Preposition Quiz",
        "instruction": "Complete the sentence.",
        "items": [
            {
                "question": "Which case form of „завдяки” should be used here?",
                "sentence": "___ допомозі...",
                "answer": "Завдяки",
                "options": ["Завдяки"],
            }
        ],
    }
    violations = check_indeclinable_case_drills([activity])
    assert len(violations) == 1
    assert violations[0]["type"] == "INDECLINABLE_CASE_DRILL"
