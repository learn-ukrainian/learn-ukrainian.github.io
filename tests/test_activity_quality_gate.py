"""Unit tests for activity quality gate additions (Issue #7944)."""


from scripts.audit.checks.activity_validation import (
    check_error_correction_stem_quality,
)


def test_error_correction_meta_stem_hard_fails():
    bad = [
        {
            "type": "error-correction",
            "id": "act-4",
            "title": "Ви́прав па́стки",
            "items": [
                {
                    "sentence": 'Не пиши́ сімя без апо́строфа. — Do not write "сімя" without an apostrophe.',
                    "error": "сімя",
                    "correction": "сім'я́",
                    "options": ["сім'я́", "сімя"],
                    "explanation": "У сло́ві сім'я́ потрі́бен апо́строф. — Apostrophe needed.",
                }
            ],
        }
    ]
    v = check_error_correction_stem_quality(bad, level="a1")
    assert any(x["type"] == "ERROR_CORRECTION_META_STEM" and x["severity"] == "critical" for x in v)


def test_error_correction_natural_stem_ok():
    good = [
        {
            "type": "error-correction",
            "id": "act-ec",
            "title": "Ви́прав",
            "items": [
                {
                    "sentence": "У мене́ вели́ка сімя.",
                    "error": "сімя",
                    "correction": "сім'я́",
                    "options": ["сім'я́", "сімя"],
                    "explanation": "У сло́ві сім'я́ потрі́бен апо́строф. — Apostrophe needed.",
                }
            ],
        }
    ]
    assert check_error_correction_stem_quality(good, level="a1") == []


def test_error_correction_en_in_stem_warning_on_a1_critical_on_a2():
    bilingual_stem = [
        {
            "type": "error-correction",
            "title": "EC",
            "items": [
                {
                    "sentence": "У лі́сі спить мале́нький йіжа́к. — In the forest sleeps a little hedgehog.",
                    "error": "йіжа́к",
                    "correction": "їжа́к",
                    "options": ["їжа́к", "йіжа́к"],
                    "explanation": "Пишемо ї. — We write ї.",
                }
            ],
        }
    ]
    a1 = check_error_correction_stem_quality(bilingual_stem, level="a1")
    assert len(a1) == 1 and a1[0]["type"] == "ERROR_CORRECTION_EN_IN_STEM"
    assert a1[0]["severity"] == "warning"
    a2 = check_error_correction_stem_quality(bilingual_stem, level="a2")
    assert a2[0]["severity"] == "critical"
