# Audit Report: M64 — 64-synonyms-action.md
**Level:** B2 | **Module:** M64 | **Phase:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:28:28

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
| 1 | match-up | Знайдіть характер дії | 12 | 8 | ✅ |
| 2 | quiz | Оберіть точну дію | 8 | 8 | ✅ |
| 3 | group-sort | Дія чи Результат? | 20 | 14 | ✅ |
| 4 | unjumble | Складіть дієве речення | 8 | 6 | ✅ |
| 5 | cloze | Проєкт перетворення | 18 | 14 | ✅ |
| 6 | fill-in | Професійне дієслово | 10 | 8 | ✅ |
| 7 | error-correction | Виправте вчинок | 8 | 6 | ✅ |
| 8 | translate | Переклад дії | 8 | 6 | ✅ |
| 9 | true-false | Нюанси чину | 8 | 8 | ✅ |
| 10 | select | Всі форми активності | 6 | 6 | ✅ |
| 11 | match-up | Дія та Регістри | 12 | 8 | ✅ |
| 12 | match-up | Дія та Її Об'єкт | 12 | 8 | ✅ |
| 13 | quiz | Філософія чину | 8 | 8 | ✅ |
| 14 | select | Творча та Технічна Дія | 6 | 6 | ✅ |
| 15 | essay-response | Творче завдання: Людина дії | 1 | 1 | ✅ |

**Summary:**
- Total activities: 15 (target: 10-14) ❌
- Unique types: 11 (minimum: 4) ✅
- Priority types used: 3/4 (match-up, quiz, translate) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-synonyms-action.yaml: Schema validation error at key '13': {'type': 'select', 'title': 'Творча та Технічна Дія', 'instruction': 'Оберіть усі слова, що описують складні та інноваційні процеси (6 елементів).', 'items': [{'question': 'Які терміни вказують на модернізацію та розвиток? (Оберіть 6)', 'options': [{'text': 'модернізувати', 'correct': True}, {'text': 'оптимізувати', 'correct': True}, {'text': 'інтегрувати', 'correct': True}, {'text': 'впроваджувати', 'correct': True}, {'text': 'трансформувати', 'correct': True}, {'text': 'удосконалювати', 'correct': True}]}, {'question': "Оберіть синоніми до слова 'створювати':", 'options': [{'text': 'творити', 'correct': True}, {'text': 'засновувати', 'correct': True}, {'text': 'фундадувати', 'correct': True}, {'text': 'руйнувати', 'correct': False}]}, {'question': "Які слова описують 'швидку реакцію':", 'options': [{'text': 'оперативно', 'correct': True}, {'text': 'негайно', 'correct': True}, {'text': 'миттєво', 'correct': True}, {'text': 'повільно', 'correct': False}]}, {'question': 'Оберіть слова для опису професійної дії:', 'options': [{'text': 'кваліфіковано', 'correct': True}, {'text': 'фахово', 'correct': True}, {'text': 'майстерно', 'correct': True}, {'text': 'абияк', 'correct': False}]}, {'question': "Які слова вказують на 'результативність':", 'options': [{'text': 'ефективно', 'correct': True}, {'text': 'продуктивно', 'correct': True}, {'text': 'успішно', 'correct': True}, {'text': 'марно', 'correct': False}]}, {'question': "Оберіть назви 'творчих процесів':", 'options': [{'text': 'натхнення', 'correct': True}, {'text': 'візуалізація', 'correct': True}, {'text': 'репетиція', 'correct': True}, {'text': 'рутина', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 1 violations (minor)

## Gates
- **Words:** ✅ 2180/1750 (raw: 2387)
- **Activities:** ✅ 15/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/6
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 14 < 35 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.4% (target 90-100% (vocab))
- **Richness:** ✅ 98% (grammar)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 98% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 68 | 24 | 100% | 20% | 20.0% |
| engagement | 9 | 5 | 100% | 15% | 15.0% |
| dialogues | 5 | 4 | 100% | 15% | 15.0% |
| variety | 0.96 | - | 96% | 10% | 9.6% |
| cultural | 3 | 3 | 100% | 10% | 10.0% |
| realworld | 8 | 3 | 100% | 10% | 10.0% |
| visual | 6 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 0.82 | - | 82% | 5% | 4.1% |
| questions | 9 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **98.7%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 87 | Included in Core |
| **Вступ: Енергія українського чину та перетворення** | ✅ | 109 | Included in Core |
| **Частина 1: Робити — Як ми змінюємо світ навколо себе** | ✅ | 286 | Included in Core |
| **Частина 2: Брати — Як ми взаємодіємо з ресурсами та об'єктами** | ✅ | 156 | Included in Core |
| **Частина 3: Категорії дії — Від вчинку до результату в аналізі** | ✅ | 144 | Included in Core |
| **Частина 4: Дія в українській культурі та філософії «чину»** | ✅ | 79 | Included in Core |
| **Частина 5: Фразеологізми про дію** | ✅ | 222 | Included in Core |
| **Вживання у контексті** | ✅ | 141 | Included in Core |
| **Частина 6: Дія в епоху глобальних перетворень** | ✅ | 101 | Included in Core |
| **Частина 7: Відповідальність за кожен крок та результат** | ✅ | 65 | Included in Core |
| **Частина 8: Мистецтво вчинку та Моральна Дія** | ✅ | 93 | Included in Core |
| **Частина 9: Технологічна дія: Від алгоритму до результату** | ✅ | 79 | Included in Core |
| **Частина 10: Дія як головний інструмент соціальних змін** | ✅ | 171 | Included in Core |
| **Частина 11: Дія в контексті відновлення міст** | ✅ | 90 | Included in Core |
| **Частина 12: Дія як самореалізація в Дніпро** | ✅ | 76 | Included in Core |
| **Частина 13: Дія у сучасному мистецтві та медіа** | ✅ | 121 | Included in Core |
| **Підсумок** | ✅ | 50 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |