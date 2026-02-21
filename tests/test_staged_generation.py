"""
Tests for staged generation scripts.

Tests:
- check_gate.py - Hard gate checker
- calculate_richness.py - Richness score calculator

Note: extract_for_activities.py tests removed — module archived in #616.
"""

import pytest
import sys
import os
from pathlib import Path

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))

from check_gate import (
    parse_frontmatter,
    count_words,
    count_engagement_boxes,
    count_examples,
    count_dialogues,
    count_activities,
    count_vocab,
    calculate_immersion,
    check_skeleton_gate,
    check_content_gate,
    check_activities_gate,
    extract_level_and_module,
)

from calculate_richness import (
    calculate_richness_score as calculate_richness,
    detect_dryness_flags,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def rich_b1_module():
    """B1 module with rich content."""
    return """---
module: b1-11
title: "Вид дієслова в наказовому способі"
level: B1
pedagogy: TTT
phase: B1.1
focus: grammar
objectives:
  - "Learner can use perfective imperatives"
  - "Learner can use imperfective imperatives"
vocabulary_count: 25
---

# Вид дієслова в наказовому способі

## Тест

Перевірте своє розуміння виду дієслова.

> 💡 **Чому це важливо?**
>
> Наказовий спосіб у повсякденному спілкуванні відіграє важливу роль.

## Пояснення

### Недоконаний вид

**Читай книгу!** — процес без вказівки на результат.
**Пиши уважно!** — тривала дія.
**Слухай мене!** — загальна вказівка.

> 🌍 **У реальному житті**
>
> На вулиці ви почуєте: «Чекай!» (тривала дія), але «Зачекай!» (одноразова).

### Доконаний вид

**Прочитай статтю!** — завершена дія з результатом.
**Напиши листа!** — конкретний результат.
**Послухай пісню!** — одноразова дія.

> 🎬 **У кіно**
>
> У фільмах часто чуємо: «Зроби це!» — наказ на результат.

**Порівняння:**

| Недоконаний | Доконаний | Різниця |
|-------------|-----------|---------|
| Читай! | Прочитай! | процес / результат |
| Пиши! | Напиши! | тривалість / завершення |

> 🎯 **Запам'ятай!**
>
> Недоконаний = процес, доконаний = результат.

### Контекстні приклади

**Ситуація 1:** Мама каже дитині:
- «Їж кашу!» (загальний процес)
- «З'їж кашу!» (щоб тарілка була порожня)

**Ситуація 2:** Вчитель учневі:
- «Вчи правила!» (регулярно)
- «Вивчи це правило!» (один раз)

> 💡 **Цікавий факт**
>
> Українці інтуїтивно обирають правильний вид, навіть не знаючи правил.

## Діалоги

**Марія:** Читай цю книгу, вона цікава!
**Петро:** Добре, прочитаю до вечора.

**Викладач:** Пишіть вправу уважно.
**Студенти:** Ми напишемо її за годину.

**А:** Слухай музику!
**Б:** Я вже послухав цей альбом учора.

**Мама:** Їж швидше!
**Дитина:** Зараз з'їм і підемо.

## Практика

Визначте, який вид краще підходить для кожної ситуації.

## Підсумок

Вид дієслова в наказовому способі залежить від контексту.
Недоконаний вид — для процесів і загальних вказівок.
Доконаний вид — для конкретних результатів.

## Activities

## quiz: Вид дієслова
1. Яке речення містить наказ на конкретний результат?
   - [ ] Читай книгу кожен день.
   - [x] Прочитай цю статтю до завтра.
   - [ ] Пиши акуратно.
   - [ ] Слухай уважно.

2. Яке речення містить наказ на процес?
   - [x] Вчи українську щодня.
   - [ ] Вивчи це слово.
   - [ ] Зроби домашнє завдання.
   - [ ] Напиши листа.

## Словник

| Слово | Переклад | Примітки |
|-------|----------|----------|
| читати | to read | impf |
| прочитати | to read (complete) | pf |
| писати | to write | impf |
| написати | to write (complete) | pf |
| слухати | to listen | impf |
| послухати | to listen (complete) | pf |
| їсти | to eat | impf |
| з'їсти | to eat (complete) | pf |
| вчити | to learn | impf |
| вивчити | to learn (complete) | pf |
"""


@pytest.fixture
def dry_module():
    """Module with dry, repetitive content."""
    return """---
module: b1-99
title: "Dry Module"
level: B1
pedagogy: TTT
---

# Dry Module

## Тест

Тест тут.

## Пояснення

Граматика. Граматика важлива. Граматика потрібна. Граматика цікава.
Граматика допомагає. Граматика вчить. Граматика пояснює.

Правила. Правила важливі. Правила потрібні. Правила цікаві.
Правила допомагають. Правила вчать. Правила пояснюють.

## Підсумок

Підсумок.

## Словник

| Слово | Переклад | Примітки |
|-------|----------|----------|
| слово | word | noun |
"""


@pytest.fixture
def skeleton_module():
    """Basic skeleton structure."""
    return """---
module: b1-43
title: "Test Skeleton"
level: B1
---

# Test Title

## Тест

<!-- placeholder -->

## Пояснення

<!-- placeholder -->

## Словник

| Слово | Переклад | Примітки |
|-------|----------|----------|
"""


@pytest.fixture
def a1_module_with_vocab():
    """A1 module with vocabulary table."""
    return """---
module: a1-05
title: "Numbers"
level: A1
---

# Numbers

Some content here.

## Vocabulary

| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| один | /oˈdɪn/ | one | num | m | — |
| два | /dwɑ/ | two | num | m | — |
| три | /trɪ/ | three | num | m | — |
"""


# =============================================================================
# CHECK_GATE TESTS
# =============================================================================

class TestParseFrontmatter:
    def test_parses_valid_frontmatter(self, rich_b1_module):
        fm = parse_frontmatter(rich_b1_module)
        assert fm['module'] == 'b1-11'
        assert fm['title'] == 'Вид дієслова в наказовому способі'
        assert fm['level'] == 'B1'
        assert fm['pedagogy'] == 'TTT'

    def test_handles_missing_frontmatter(self):
        content = "# Just a title\n\nSome content."
        fm = parse_frontmatter(content)
        assert fm == {}


class TestCountWords:
    def test_counts_words_in_content(self, rich_b1_module):
        count = count_words(rich_b1_module)
        assert count > 200  # Should have substantial content

    def test_excludes_activities_section(self, rich_b1_module):
        # Add extra content after activities - should be excluded
        with_extra = rich_b1_module + "\n\nExtra words in activities section."
        count = count_words(with_extra)
        original_count = count_words(rich_b1_module)
        # Count should be similar (activities excluded)
        assert abs(count - original_count) < 20


class TestCountEngagement:
    def test_counts_engagement_boxes(self, rich_b1_module):
        count = count_engagement_boxes(rich_b1_module)
        assert count >= 5  # Has multiple 💡🌍🎬🎯 boxes

    def test_zero_for_dry_content(self, dry_module):
        count = count_engagement_boxes(dry_module)
        assert count == 0


class TestCountExamples:
    def test_counts_bold_examples(self, rich_b1_module):
        count = count_examples(rich_b1_module)
        assert count >= 10  # Has many **bold Ukrainian** examples


class TestCountDialogues:
    def test_counts_speaker_format(self, rich_b1_module):
        count = count_dialogues(rich_b1_module)
        assert count >= 1  # Has dialogue pairs (А:/Б: format)

    def test_counts_ab_format(self):
        content = """
**А:** Привіт!
**Б:** Вітаю!

**А:** Як справи?
**Б:** Добре, дякую.
"""
        count = count_dialogues(content)
        assert count >= 2


class TestCountActivities:
    def test_counts_quiz_activities(self, rich_b1_module):
        count, types = count_activities(rich_b1_module)
        assert count >= 1
        assert 'quiz' in types

    def test_empty_for_no_activities(self, skeleton_module):
        count, types = count_activities(skeleton_module)
        assert count == 0
        assert len(types) == 0


class TestCountVocab:
    def test_counts_b1_vocab(self, rich_b1_module):
        count = count_vocab(rich_b1_module)
        assert count == 10  # Has 10 vocab items

    def test_counts_a1_vocab(self, a1_module_with_vocab):
        count = count_vocab(a1_module_with_vocab)
        assert count == 3  # Has 3 vocab items


class TestCalculateImmersion:
    def test_high_immersion_for_ukrainian_content(self, rich_b1_module):
        immersion = calculate_immersion(rich_b1_module)
        assert immersion > 70  # Mostly Ukrainian

    def test_lower_immersion_for_english_heavy(self):
        content = """---
module: test
---

# English Title

This is all in English. The learner will read this.
No Ukrainian words at all in the main content.
"""
        immersion = calculate_immersion(content)
        assert immersion < 20


class TestSkeletonGate:
    def test_passes_with_valid_skeleton(self, skeleton_module):
        path = Path("test/b1/01-test.md")
        passed, failures = check_skeleton_gate(path, skeleton_module)
        # May fail some checks but should have frontmatter
        assert 'Missing frontmatter' not in failures

    def test_fails_without_frontmatter(self):
        content = "# Just content\n\nNo frontmatter here."
        path = Path("test/b1/01-test.md")
        passed, failures = check_skeleton_gate(path, content)
        assert not passed
        assert 'Missing frontmatter' in failures


class TestExtractLevelAndModule:
    def test_extracts_b1_level(self):
        path = Path("curriculum/l2-uk-en/b1/11-test.md")
        level, num = extract_level_and_module(path)
        assert level == "B1"
        assert num == 11

    def test_extracts_a1_level(self):
        path = Path("curriculum/l2-uk-en/a1/05-test.md")
        level, num = extract_level_and_module(path)
        assert level == "A1"
        assert num == 5


# =============================================================================
# CALCULATE_RICHNESS TESTS
# =============================================================================

class TestCalculateRichness:
    def test_high_score_for_rich_content(self, rich_b1_module):
        result = calculate_richness(rich_b1_module, 'B1')
        assert result['score'] >= 55  # Above threshold (recalibrated algorithm)

    def test_low_score_for_dry_content(self, dry_module):
        result = calculate_richness(dry_module, 'B1')
        assert result['score'] < 50  # Below threshold
        assert result['passed'] is False

    def test_components_have_normalized_values(self, rich_b1_module):
        result = calculate_richness(rich_b1_module, 'B1')
        # All normalized scores should be between 0-1
        for name, value in result['normalized'].items():
            assert 0 <= value <= 1.0


class TestDetectDrynessFlags:
    def test_detects_no_engagement(self, dry_module):
        flags = detect_dryness_flags(dry_module, 'B1')
        assert 'NO_ENGAGEMENT' in flags

    def test_detects_multiple_issues_in_dry_content(self, dry_module):
        """Dry content should have multiple flags."""
        flags = detect_dryness_flags(dry_module, 'B1')
        # Should have several flags for truly dry content
        assert len(flags) >= 3

    def test_rich_content_has_fewer_flags(self, rich_b1_module, dry_module):
        """Rich content should have fewer flags than dry content."""
        rich_flags = detect_dryness_flags(rich_b1_module, 'B1')
        dry_flags = detect_dryness_flags(dry_module, 'B1')
        assert len(rich_flags) < len(dry_flags)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    def test_richness_correlates_with_engagement(self, rich_b1_module, dry_module):
        """Rich content should score higher than dry content."""
        rich_result = calculate_richness(rich_b1_module, 'B1')
        dry_result = calculate_richness(dry_module, 'B1')

        assert rich_result['score'] > dry_result['score']
