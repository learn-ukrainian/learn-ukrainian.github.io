# Audit Report: M60 — 60-synonyms-character.md

**Level:** B2 | **Module:** M60 | **Phase:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:28:25

## Configuration

**Type:** B2-vocab
**Word Target:** 1750 words
**Activities:** 10-14 required
**Items per Activity:** ≥14 items
**Unique Types:** ≥4 types required
**Priority Types:** mark-the-words, match-up, quiz, translate
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

**Summary:**
- Total activities: 15 (target: 10-14) ❌
- Unique types: 11 (minimum: 4) ✅
- Priority types used: 3/4 (match-up, quiz, translate) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[YAML_SCHEMA_VIOLATION]** Schema error in 60-synonyms-character.yaml: Schema validation error at key '13': {'type': 'select', 'title': 'Чесноти та Вади', 'instruction': 'Оберіть усі слова, що позначають позитивні якості (6 елементів).', 'items': [{'question': 'Які слова описують шляхетну людину? (Оберіть 6)', 'options': [{'text': 'милосердний', 'correct': True}, {'text': 'чуйний', 'correct': True}, {'text': 'щедрий', 'correct': True}, {'text': 'принциповий', 'correct': True}, {'text': 'незламний', 'correct': True}, {'text': 'сумлінний', 'correct': True}]}, {'question': 'Оберіть вади характеру:', 'options': [{'text': 'байдужість', 'correct': True}, {'text': 'егоїзм', 'correct': True}, {'text': 'жорстокість', 'correct': True}, {'text': 'мудрість', 'correct': False}]}, {'question': 'Які слова описують активну доброту?', 'options': [{'text': 'жертовний', 'correct': True}, {'text': 'невтомний', 'correct': True}, {'text': 'дбайливий', 'correct': True}, {'text': 'пасивний', 'correct': False}]}, {'question': 'Оберіть ознаки емоційного інтелекту:', 'options': [{'text': 'емпатія', 'correct': True}, {'text': 'співпереживання', 'correct': True}, {'text': 'чуйність', 'correct': True}, {'text': 'агресія', 'correct': False}]}, {'question': 'Які слова вказують на професійний характер?', 'options': [{'text': 'пунктуальний', 'correct': True}, {'text': 'відповідальний', 'correct': True}, {'text': 'сумлінний', 'correct': True}, {'text': 'лінивий', 'correct': False}]}, {'question': 'Оберіть риси сучасного лідера:', 'options': [{'text': 'харизматичний', 'correct': True}, {'text': 'далекоглядний', 'correct': True}, {'text': 'гнучкий', 'correct': True}, {'text': 'жорсткий', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation

**📝 UPDATE** (severity 5/100)

- 1 violations (minor)

## Gates

- **Words:** ✅ 2671/1750 (raw: 2879)
- **Activities:** ✅ 15/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 14/6
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 18 < 35 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.4% (target 90-100% (vocab))
- **Richness:** ✅ 97% (grammar)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details

**Score:** 97% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown

| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 76 | 24 | 100% | 20% | 20.0% |
| engagement | 16 | 5 | 100% | 15% | 15.0% |
| dialogues | 5 | 4 | 100% | 15% | 15.0% |
| variety | 0.94 | - | 94% | 10% | 9.4% |
| cultural | 4 | 3 | 100% | 10% | 10.0% |
| realworld | 9 | 3 | 100% | 10% | 10.0% |
| visual | 10 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 0.72 | - | 72% | 5% | 3.6% |
| questions | 14 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **98.0%** |

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 72 | Included in Core |
| **Вступ: Мозаїка людської душі** | ✅ | 101 | Included in Core |
| **Частина 1: Сяйво розуму — Від «кмітливості» до «мудрості»** | ✅ | 218 | Included in Core |
| **Частина 2: Тепло серця — Від «доброти» до «самопожертви»** | ✅ | 230 | Included in Core |
| **Частина 3: Тіні характеру — Від «байдужості» до «жорстокості»** | ✅ | 159 | Included in Core |
| **Частина 4: Характер в українській літературі та філософії** | ✅ | 91 | Included in Core |
| **Частина 5: Фразеологізми про характер** | ✅ | 210 | Included in Core |
| **Вживання у контексті** | ✅ | 135 | Included in Core |
| **Частина 6: Формування особистості в сучасному світі** | ✅ | 70 | Included in Core |
| **Частина 6: Характер та професійний успіх** | ✅ | 110 | Included in Core |
| **Частина 7: Українська незламність — Нова риса епохи** | ✅ | 126 | Included in Core |
| **Частина 8: Саморозвиток та робота над собою** | ✅ | 83 | Included in Core |
| **Частина 9: Лідерство та моральний авторитет** | ✅ | 164 | Included in Core |
| **Частина 10: Формування характеру через мову** | ✅ | 328 | Included in Core |
| **Частина 11: Еволюція характеру в цифрову добу** | ✅ | 146 | Included in Core |
| **Частина 12: Роль оточення у формуванні натури** | ✅ | 95 | Included in Core |
| **Частина 13: Характер в українському фольклорі та міфології** | ✅ | 89 | Included in Core |
| **Частина 14: Характер і сучасні виклики** | ✅ | 85 | Included in Core |
| **Підсумок** | ✅ | 49 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |
