"""Unit tests for activity quality gate additions (Issue #7944)."""


from scripts.audit.checks.activity_validation import (
    check_activity_intentional_error_leak,
    check_fill_in_blank_formatting,
)


def test_activity_intentional_error_leak_detected():
    # A standard fill-in activity accidentally having an editing prompt from a textbook
    leaked_act = [
        {
            "type": "fill-in",
            "title": "Відредагуйте речення в зошиті",
            "instruction": "Заповніть пропуски",
            "items": [
                {
                    "sentence": "Ми вирішили заповнити _____ форму.",
                    "answer": "нову",
                    "options": ["нову", "стару"],
                }
            ],
        }
    ]
    violations = check_activity_intentional_error_leak(leaked_act)
    assert len(violations) == 1
    assert violations[0]["type"] == "INTENTIONAL_ERROR_LEAK"
    assert violations[0]["severity"] == "critical"

    # Contrastive table pattern in sentence item
    leaked_item = [
        {
            "type": "quiz",
            "title": "Тест з граматики",
            "items": [
                {
                    "question": "НЕПРАВИЛЬНО / ПРАВИЛЬНО: як краще сказати?",
                    "options": [
                        {"text": "брати участь", "correct": True},
                        {"text": "приймати участь", "correct": False},
                    ],
                }
            ],
        }
    ]
    v_item = check_activity_intentional_error_leak(leaked_item)
    assert len(v_item) == 1
    assert v_item[0]["type"] == "INTENTIONAL_ERROR_LEAK"


def test_activity_intentional_error_allowed_for_error_types():
    # Error correction activity properly typed
    proper_act = [
        {
            "type": "error-correction",
            "title": "Відредагуйте речення",
            "instruction": "Знайдіть помилку і виправте її",
            "items": [
                {
                    "sentence": "Він приймав участь у змаганнях.",
                    "error": "приймав участь",
                    "answer": "брав участь",
                    "options": ["брав участь", "був учасником"],
                    "explanation": "Калька з російської: правильно 'брати участь'.",
                }
            ],
        }
    ]
    assert check_activity_intentional_error_leak(proper_act) == []

    essay_act = [
        {
            "type": "essay-response",
            "title": "Редакторська колонка",
            "instruction": "Відредагуйте речення і поясніть помилку",
            "items": [],
        }
    ]
    assert check_activity_intentional_error_leak(essay_act) == []


def test_fill_in_blank_formatting():
    # Valid fill-in
    valid = [
        {
            "type": "fill-in",
            "title": "Вставте потрібне слово",
            "items": [
                {
                    "sentence": "Сьогодні ми йдемо до _____ читати книгу.",
                    "answer": "бібліотеки",
                    "options": ["бібліотеки", "школи"],
                }
            ],
        }
    ]
    assert check_fill_in_blank_formatting(valid) == []

    # Missing blank
    missing = [
        {
            "type": "fill-in",
            "title": "Вставте потрібне слово",
            "items": [
                {
                    "sentence": "Сьогодні ми йдемо до бібліотеки.",
                    "answer": "бібліотеки",
                }
            ],
        }
    ]
    v_missing = check_fill_in_blank_formatting(missing)
    assert len(v_missing) == 1
    assert v_missing[0]["type"] == "FILL_IN_MISSING_BLANK"

    # Empty sentence
    empty = [
        {
            "type": "fill-in",
            "title": "Вставте потрібне слово",
            "items": [
                {
                    "sentence": "",
                    "answer": "тест",
                }
            ],
        }
    ]
    v_empty = check_fill_in_blank_formatting(empty)
    assert len(v_empty) == 1
    assert v_empty[0]["type"] == "FILL_IN_EMPTY_SENTENCE"

    # Multiple blanks with single answer
    multi = [
        {
            "type": "fill-in",
            "title": "Вставте слово",
            "items": [
                {
                    "sentence": "Перше _____ і друге _____ слово.",
                    "answer": "одне",
                }
            ],
        }
    ]
    v_multi = check_fill_in_blank_formatting(multi)
    assert len(v_multi) == 1
    assert v_multi[0]["type"] == "FILL_IN_MULTIPLE_BLANKS"
