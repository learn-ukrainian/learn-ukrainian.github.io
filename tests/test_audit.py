import pytest
from scripts.audit.cleaners import clean_for_stats, calculate_immersion
from scripts.audit.gates import evaluate_word_count, evaluate_activity_count, evaluate_density, evaluate_naturalness
from scripts.audit.checks.markdown_format import check_markdown_format, check_table_column_consistency
from scripts.audit.checks.content_quality import validate_characters_in_content

def test_clean_for_stats():
    text = """
---
title: Test
---
# Header
| Col 1 | Col 2 |
|-------|-------|
| Val 1 | Val 2 |

> [!answer] Solution
> [!note] Engagement

Content word.
"""
    cleaned = clean_for_stats(text)
    assert "Content word." in cleaned
    assert "Header" not in cleaned
    assert "Col 1" not in cleaned
    assert "[!answer]" not in cleaned
    assert "[!note]" in cleaned # Engagement should stay

def test_calculate_immersion():
    # 100% Cyrillic
    assert calculate_immersion("Привіт світ") == 100.0
    # 100% Latin
    assert calculate_immersion("Hello world") == 0.0
    # 50/50
    # "Привіт" (6) + "Hello" (5) = 11 total. 6/11 = 54.54...
    imm = calculate_immersion("Привіт Hello")
    assert 54 < imm < 55

def test_evaluate_word_count():
    # Target 1000
    target = 1000
    # PASS: 1000+
    res = evaluate_word_count(1000, target)
    assert res.status == 'PASS'

    # WARN: 900-999
    res = evaluate_word_count(950, target)
    assert res.status == 'WARN'

    # FAIL: <900
    res = evaluate_word_count(899, target)
    assert res.status == 'FAIL'

def test_evaluate_activity_count():
    # Target 3
    assert evaluate_activity_count(3, 3).status == 'PASS'
    assert evaluate_activity_count(2, 3).status == 'FAIL'

def test_check_markdown_format_headers():
    content = """---
title: Test
---
# First H1 (Title)
# Second H1 (Illegal)
## Correct H2
"""
    violations = check_markdown_format(content)
    # The second H1 should be a violation
    assert any(v['type'] == 'HEADING_LEVEL' for v in violations)

def test_check_table_column_consistency():
    content = """
| Col 1 | Col 2 |
|-------|-------|
| Row 1 | Row 1 |
| Row 2 |
"""
    violations = check_table_column_consistency(content)
    assert len(violations) > 0
    assert violations[0]['type'] == 'TABLE_COLUMN_MISMATCH'

def test_forbidden_headers():
    content = """
# Test
## Activities
## Vocabulary
"""
    violations = check_markdown_format(content, level_code='b1')
    assert any(v['type'] == 'FORBIDDEN_HEADER' for v in violations)

def test_russian_character_detection():
    # Modern Ukrainian with Russian character 'ы'
    content = "Це речення з помилкою: рыби"
    violations = validate_characters_in_content(content, level_code='A1')
    assert any(v['type'] == 'RUSSIAN_CHARACTERS' for v in violations)

    # Russian characters inside quotes (allowed for educational context)
    content = 'Він сказав: "ы" (це російська літера)'
    violations = validate_characters_in_content(content, level_code='A1')
    assert len(violations) == 0

def test_evaluate_naturalness():
    # PASS >= 8
    assert evaluate_naturalness(8, "PASS").status == "PASS"
    # FAIL < 8
    assert evaluate_naturalness(7, "PASS").status == "FAIL"
    # INFO if PENDING
    assert evaluate_naturalness(0, "PENDING").status == "INFO"
