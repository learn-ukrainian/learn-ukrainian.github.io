# Audit Report: M60 — 60-synonyms-character.md
**Level:** B2 | **Module:** M60 | **Phase:** B2.2 | **Pedagogy:** CBI | **Target:** 2000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-05 22:35:33

## Configuration
**Type:** B2-vocab
**Word Target:** 2000 words
**Activities:** 10-14 required
**Items per Activity:** ≥14 items
**Unique Types:** ≥4 types required
**Priority Types:** mark-the-words, match-up, quiz, translate
**Required Types:** fill-in, reading, true-false
**Engagement:** ≥6 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥35 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | match-up | Знайдіть точне слово | 12 | 8 | ✅ |
| 2 | quiz | Портрет особистості | 8 | 8 | ✅ |
| 3 | group-sort | Світло і Тіні | 24 | 14 | ✅ |
| 4 | unjumble | Складіть характеристику | 8 | 6 | ✅ |
| 5 | cloze | Портрет волонтера | 19 | 14 | ✅ |
| 6 | fill-in | Відтінки розуму | 10 | 8 | ✅ |
| 7 | error-correction | Виправте портрет | 8 | 6 | ✅ |
| 8 | translate | Переклад характеру | 8 | 6 | ✅ |
| 9 | true-false | Нюанси натури | 8 | 8 | ✅ |
| 10 | select | Всі відтінки інтелекту | 6 | 6 | ✅ |
| 11 | match-up | Регістри та Риси | 12 | 8 | ✅ |
| 12 | match-up | Натура та Вчинки | 12 | 8 | ✅ |
| 13 | quiz | Характер у літературі | 8 | 8 | ✅ |
| 14 | select | Чесноти та Вади | 6 | 6 | ✅ |
| 15 | essay-response | Творче завдання: Мій характер | 1 | 1 | ✅ |
| 16 | reading | Текст для аналізу: Синоніми: Характер та Особистість | 3 | 3 | ✅ |

**Summary:**
- Total activities: 16 (target: 10-14) ❌
- Unique types: 12 (minimum: 4) ✅
- Priority types used: 3/4 (match-up, quiz, translate) ✅
- Required types used: 3/3 (fill-in, reading, true-false) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 60-synonyms-character.yaml: Schema validation error at key '13': {'type': 'select', 'title': 'Чесноти та Вади', 'instruction': 'Оберіть усі слова, що позначають позитивні якості (6 елементів).', 'items': [{'question': 'Які слова описують шляхетну людину? (Оберіть 6)', 'options': [{'text': 'милосердний', 'correct': True}, {'text': 'чуйний', 'correct': True}, {'text': 'щедрий', 'correct': True}, {'text': 'принциповий', 'correct': True}, {'text': 'незламний', 'correct': True}, {'text': 'сумлінний', 'correct': True}]}, {'question': 'Оберіть вади характеру:', 'options': [{'text': 'байдужість', 'correct': True}, {'text': 'егоїзм', 'correct': True}, {'text': 'жорстокість', 'correct': True}, {'text': 'мудрість', 'correct': False}]}, {'question': 'Які слова описують активну доброту?', 'options': [{'text': 'жертовний', 'correct': True}, {'text': 'невтомний', 'correct': True}, {'text': 'дбайливий', 'correct': True}, {'text': 'пасивний', 'correct': False}]}, {'question': 'Оберіть ознаки емоційного інтелекту:', 'options': [{'text': 'емпатія', 'correct': True}, {'text': 'співпереживання', 'correct': True}, {'text': 'чуйність', 'correct': True}, {'text': 'агресія', 'correct': False}]}, {'question': 'Які слова вказують на професійний характер?', 'options': [{'text': 'пунктуальний', 'correct': True}, {'text': 'відповідальний', 'correct': True}, {'text': 'сумлінний', 'correct': True}, {'text': 'лінивий', 'correct': False}]}, {'question': 'Оберіть риси сучасного лідера:', 'options': [{'text': 'харизматичний', 'correct': True}, {'text': 'далекоглядний', 'correct': True}, {'text': 'гнучкий', 'correct': True}, {'text': 'жорсткий', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 1 violations (minor)

## Gates
- **Words:** ✅ 2683/2000 (raw: 2769)
- **Activities:** ✅ 16/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 12/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 14/6
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 18 < 35 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.4% (target 90-100% (vocab))
- **Richness:** ✅ 96% (phraseology)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 96% (minimum: 95%)
**Module Type:** phraseology

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| engagement | 16 | 4 | 100% | 25% | 25.0% |
| variety | 0.93 | - | 93% | 17% | 15.5% |
| cultural | 4 | - | 100% | 17% | 16.7% |
| visual | 10 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 0.67 | - | 67% | 8% | 5.6% |
| examples | 72 | - | 100% | 8% | 8.3% |
| realworld | 9 | - | 100% | 8% | 8.3% |
| questions | 13 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **96.1%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 72 | Included in Core |
| **Розминка — Описуємо людину** | ⚪️ | 708 | Skipped |
| **Smart** | ⚪️ | 616 | Skipped |
| **Kind** | ⚪️ | 701 | Skipped |
| **Практика — психологічний портрет** | ⚪️ | 574 | Skipped |
| **Підсумок** | ✅ | 12 | Included in Core |