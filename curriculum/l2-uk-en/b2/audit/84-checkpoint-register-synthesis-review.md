# Audit Report: M84 — 84-checkpoint-register-synthesis.md
**Level:** B2 | **Module:** M84 | **Phase:** B2 | **Pedagogy:** Test | **Target:** 1750
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:28:42

## Configuration
**Type:** B2-checkpoint
**Word Target:** 1750 words
**Activities:** 15-19 required
**Items per Activity:** ≥14 items
**Unique Types:** ≥4 types required
**Priority Types:** cloze, error-correction, fill-in, quiz
**Engagement:** ≥4 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥10 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | quiz | Читання: Розуміння тексту | 10 | 8 | ✅ |
| 2 | quiz | Аудіювання (Симуляція) | 10 | 8 | ✅ |
| 3 | quiz | Граматика: Пасив | 10 | 8 | ✅ |
| 4 | quiz | Граматика: Дієприкметники | 10 | 8 | ✅ |
| 5 | fill-in | Граматика: Вид дієслова | 10 | 8 | ✅ |
| 6 | fill-in | Граматика: Рух | 8 | 8 | ✅ |
| 7 | fill-in | Граматика: Відмінки | 8 | 8 | ✅ |
| 8 | match-up | Лексика: Синоніми | 12 | 8 | ✅ |
| 9 | match-up | Лексика: Ідіоми | 12 | 8 | ✅ |
| 10 | quiz | Лексика: Визначення | 8 | 8 | ✅ |
| 11 | match-up | Історія: Дати | 12 | 8 | ✅ |
| 12 | quiz | Культура: Факти | 8 | 8 | ✅ |
| 13 | group-sort | Письмо: Структура есе | 14 | 14 | ✅ |
| 14 | group-sort | Письмо: Стилі та Реєстри | 15 | 14 | ✅ |
| 15 | quiz | Говоріння (Симуляція) | 8 | 8 | ✅ |
| 16 | error-correction | Виправлення помилок (B2 Final Exam) | 8 | 6 | ✅ |
| 17 | cloze | Філософія вивчення мови | 16 | 14 | ✅ |
| 18 | translate | Фрази для дискусій та дебатів | 6 | 6 | ✅ |
| 19 | select | Вибір правильного дієслова руху | 8 | 6 | ✅ |
| 20 | match-up | Антоніми та відтінки значень | 12 | 8 | ✅ |
| 21 | essay-response | Фінальний звіт: Моє бачення майбутнього України | 1 | 1 | ✅ |

**Summary:**
- Total activities: 21 (target: 15-19) ❌
- Unique types: 10 (minimum: 4) ✅
- Priority types used: 4/4 (cloze, error-correction, fill-in, quiz) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 84-checkpoint-register-synthesis.yaml: Schema validation error at key '17': {'type': 'translate', 'title': 'Фрази для дискусій та дебатів', 'items': [{'source': 'I totally agree with your point of view.', 'options': [{'text': 'Я повністю згоден з вашою точкою зору.', 'correct': True}, {'text': 'Я думаю так само як і ви зараз.', 'correct': False}, {'text': 'Ваша думка мені дуже подобається.', 'correct': False}, {'text': 'Ви кажете правду, я вірю вам.', 'correct': False}]}, {'source': 'On the other hand, we should consider risks.', 'options': [{'text': 'З іншого боку, нам варто зважити на ризики.', 'correct': True}, {'text': 'З іншої руки, ми маємо думати про проблеми.', 'correct': False}, {'text': 'Але також є дуже великі небезпеки.', 'correct': False}, {'text': 'Навпаки, ми забули про всі ризики.', 'correct': False}]}, {'source': 'Summarizing the above, I would like to emphasize...', 'options': [{'text': 'Підсумовуючи вищесказане, я хотів би підкреслити...', 'correct': True}, {'text': 'Коротко кажучи про все, я скажу...', 'correct': False}, {'text': 'Наприкінці своєї промови я наголошу на...', 'correct': False}, {'text': 'Отже, я думаю, що це важливо знати...', 'correct': False}]}, {'source': 'Could you please clarify this point?', 'options': [{'text': 'Чи не могли б ви уточнити цей момент?', 'correct': True}, {'text': 'Що ви мали на увазі під цим словом?', 'correct': False}, {'text': 'Поясніть мені ще раз, я не зрозумів.', 'correct': False}, {'text': 'Кажіть простіше, будь ласка, я чекаю.', 'correct': False}]}, {'source': 'I am afraid I cannot support this idea.', 'options': [{'text': 'Боюсь, що я не можу підтримати цю ідею.', 'correct': True}, {'text': 'Я не хочу допомагати вам у цій справі.', 'correct': False}, {'text': 'Ця ідея мені зовсім не подобається.', 'correct': False}, {'text': 'Я маю великий страх перед вашою ідеєю.', 'correct': False}]}, {'source': 'According to the latest research data...', 'options': [{'text': 'Згідно з останніми даними досліджень...', 'correct': True}, {'text': 'Як кажуть нові наукові книжки...', 'correct': False}, {'text': 'Через останні результати нашої роботи...', 'correct': False}, {'text': 'По даним, які ми отримали вчора...', 'correct': False}]}], 'instruction': 'Оберіть найбільш влучний академічний переклад фрази для ведення професійної дискусії.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 1 violations (minor)

## Gates
- **Words:** ✅ 1796/1750 (raw: 1980)
- **Activities:** ✅ 21/15
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/4
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 5 < 10 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 21 (target 15-19)
- **Immersion:** 🇺🇦 99.8% (checkpoint - no gate)
- **Richness:** ❌ 80% < 95% min (grammar)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 80% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 41 | 24 | 100% | 20% | 20.0% |
| engagement | 6 | 5 | 100% | 15% | 15.0% |
| dialogues | 0 | 4 | 0% | 15% | 0.0% |
| variety | 0.91 | - | 91% | 10% | 9.1% |
| cultural | 2 | 3 | 67% | 10% | 6.7% |
| realworld | 6 | 3 | 100% | 10% | 10.0% |
| visual | 10 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 19 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **80.8%** |

### Dryness Flags & Fixes
- ❌ **NO_DIALOGUE**
  - FIX:
    Add 4+ mini-dialogues. Use this exact format:
    
    **Діалог: [Location in Ukraine]**
    
    > — [Speaker 1 line with **bolded** grammar examples]
    > — [Speaker 2 response with **bolded** grammar examples]
    > — [Speaker 1 continuation]
    > — [Speaker 2 conclusion]
    
    Example locations: На Бесарабському ринку, У львівській кав'ярні, В одеському трамваї, На Подолі

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 52 | Included in Core |
| **Огляд** | ⚪️ | 84 | Skipped |
| **Навички** | ⚪️ | 45 | Skipped |
| **Skill 1: Читання та аналіз (Analytical Reading)** | ⚪️ | 0 | Skipped (using YAML) |
| **Skill 2: Аудіювання в реальному часі (Active Listening)** | ⚪️ | 268 | Skipped |
| **Skill 3: Граматична точність та лексична гнучкість (Language Use)** | ⚪️ | 320 | Skipped |
| **Skill 4: Академічне та професійне письмо (Writing Skills)** | ⚪️ | 253 | Skipped |
| **Інтеграційне завдання** | ⚪️ | 250 | Skipped |
| **Підсумок** | ✅ | 115 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 125 | Skipped |