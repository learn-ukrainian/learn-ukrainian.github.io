# Audit Report: M55 — 55-synonyms-emotion.md
**Level:** B2 | **Module:** M55 | **Phase:** B2.2 | **Pedagogy:** CBI | **Target:** 2000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-05 22:04:13

## Configuration
**Type:** B2-vocab
**Word Target:** 2000 words
**Activities:** 10-14 required
**Items per Activity:** ≥14 items
**Unique Types:** ≥4 types required
**Priority Types:** mark-the-words, match-up, quiz, translate
**Required Types:** fill-in-the-blank, reading, true-false
**Engagement:** ≥6 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥35 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | match-up | Знайдіть значення | 12 | 8 | ✅ |
| 2 | quiz | Оберіть точне слово | 8 | 8 | ✅ |
| 3 | fill-in | Емоційні пропуски | 8 | 8 | ✅ |
| 4 | true-false | Правда про почуття | 8 | 8 | ✅ |
| 5 | group-sort | Шкала інтенсивності | 20 | 14 | ✅ |
| 6 | unjumble | Емоційні речення | 8 | 6 | ✅ |
| 7 | cloze | Психологічний портрет | 20 | 14 | ✅ |
| 8 | error-correction | Відтінки значень | 8 | 6 | ✅ |
| 9 | select | Оберіть ознаки емоції | 8 | 6 | ✅ |
| 10 | translate | Переклад почуттів | 8 | 6 | ✅ |
| 11 | group-sort | Позитивні чи Негативні? | 19 | 14 | ✅ |
| 12 | match-up | Контексти вживання (Емоції) | 12 | 8 | ✅ |
| 13 | quiz | Психологічні нюанси | 8 | 8 | ✅ |
| 14 | essay-response | Творче завдання: Емоційний ландшафт | 1 | 1 | ✅ |
| 15 | reading | Текст для аналізу: Синоніми: Емоції та почуття | 3 | 3 | ✅ |

**Summary:**
- Total activities: 15 (target: 10-14) ❌
- Unique types: 12 (minimum: 4) ✅
- Priority types used: 3/4 (match-up, quiz, translate) ✅
- Required types used: 2/3 (reading, true-false) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[INVALID_ACTIVITY_TYPE]** Invalid activity types in activity_hints: ['fill-in-the-blank']. Valid types: ['match-up', 'fill-in', 'quiz', 'true-false', 'group-sort', 'unjumble', 'error-correction', 'anagram', 'select', 'translate', 'cloze', 'mark-the-words', 'reading', 'essay-response', 'critical-analysis', 'comparative-study', 'authorial-intent', 'creative-writing', 'etymology-trace', 'transcription', 'grammar-identify', 'paleography-analysis', 'dialect-comparison', 'translation-critique', 'phonology-lab', 'grammar-lab', 'parallel-text', 'historical-writing', 'register-identify', 'loanword-trace', 'comparative-style']
  - FIX: Replace invalid types with valid ones from: match-up, fill-in, quiz, true-false, group-sort, unjumble, error-correction, anagram, select, translate, cloze, mark-the-words, reading, essay-response, critical-analysis, comparative-study, authorial-intent, creative-writing, etymology-trace, transcription, grammar-identify, paleography-analysis, dialect-comparison, translation-critique, phonology-lab, grammar-lab, parallel-text, historical-writing, register-identify, loanword-trace, comparative-style
- **[YAML_SCHEMA_VIOLATION]** Schema error in 55-synonyms-emotion.yaml: Schema validation error at key '12': {'type': 'quiz', 'title': 'Психологічні нюанси', 'instruction': 'Дайте відповідь на складні питання про синоніми.', 'items': [{'question': 'Яке з цих слів має найбільш поетичний і специфічно український відтінок?', 'options': [{'text': 'журба', 'correct': True}, {'text': 'сум', 'correct': False}, {'text': 'гнів', 'correct': False}, {'text': 'страх', 'correct': False}], 'explanation': 'Журба — унікальне слово для української ліричної традиції.'}, {'question': 'Чим на вашу думку концептуально відрізняється агресія від простої людської злості?', 'options': [{'text': 'агресія — це прояв почуття у діях', 'correct': True}, {'text': 'злість — це завжди виключно фізична дія', 'correct': False}, {'text': 'це абсолютно повні синоніми без різниці', 'correct': False}, {'text': 'агресія — це зазвичай дуже приємне почуття', 'correct': False}], 'explanation': 'Агресія передбачає активний ворожий вплив.'}, {'question': 'Яке саме слово ви використаєте для опису медичного стану тривалого пригнічення?', 'options': [{'text': 'депресія', 'correct': True}, {'text': 'радість', 'correct': False}, {'text': 'втіха', 'correct': False}, {'text': 'насолода', 'correct': False}], 'explanation': 'Депресія — термін для тривалого клінічного стану.'}, {'question': "Що саме означає термін 'ейфорія' у сучасному загальному психологічному та медичному сенсі?", 'options': [{'text': 'піднесений, часто не зовсім адекватний стан', 'correct': True}, {'text': 'глибокий і спокійний сон без жодних сновидінь', 'correct': False}, {'text': 'раптове бажання плакати без жодної причини', 'correct': False}, {'text': 'почуття провини через старі помилки минулого', 'correct': False}], 'explanation': 'Ейфорія — це раптовий і сильний сплеск позитиву.'}, {'question': 'Яке слово найкраще описує стан людини, яка довго чекає на результат медичного тесту?', 'options': [{'text': 'тривога', 'correct': True}, {'text': 'насолода', 'correct': False}, {'text': 'захоплення', 'correct': False}, {'text': 'лють', 'correct': False}], 'explanation': 'Тривога — це неспокій через невідомість майбутнього.'}, {'question': 'В якому регіоні України, за текстом, лексика почуттів була особливо витонченою?', 'options': [{'text': 'Чернівці', 'correct': True}, {'text': 'Миколаїв', 'correct': False}, {'text': 'Полтава', 'correct': False}, {'text': 'Харків', 'correct': False}], 'explanation': 'У тексті згадуються Чернівці як місце перетину багатьох культур.'}, {'question': "Який автор у новелі 'Intermezzo' майстерно описував шлях від втоми до радості?", 'options': [{'text': 'Михайло Коцюбинський', 'correct': True}, {'text': 'Василь Стефаник', 'correct': False}, {'text': 'Леся Українка', 'correct': False}, {'text': 'Тарас Шевченко', 'correct': False}], 'explanation': 'Це класичний твір Коцюбинського про емоційне відновлення.'}, {'question': 'Що з переліченого нижче є головним ключем до серця українця у висловленні емоцій?', 'options': [{'text': 'щирість', 'correct': True}, {'text': 'холодний розрахунок', 'correct': False}, {'text': 'приховування почуттів', 'correct': False}, {'text': 'мовчання', 'correct': False}], 'explanation': 'Щирість — базова цінність української комунікації.'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 2 violations (minor)

## Gates
- **Words:** ❌ 1828/2000 (raw: 1990)
- **Activities:** ✅ 15/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 12/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/6
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 6 < 35 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.1% (target 90-100% (vocab))
- **Richness:** ✅ 100% (phraseology)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 100% (minimum: 95%)
**Module Type:** phraseology

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| engagement | 9 | 4 | 100% | 25% | 25.0% |
| variety | 1.00 | - | 100% | 17% | 16.7% |
| cultural | 4 | - | 100% | 17% | 16.7% |
| visual | 4 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 1.00 | - | 100% | 8% | 8.3% |
| examples | 41 | - | 100% | 8% | 8.3% |
| realworld | 7 | - | 100% | 8% | 8.3% |
| questions | 9 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 87 | Included in Core |
| **Розминка — Нюанси емоційної лексики** | ⚪️ | 220 | Skipped |
| **Joy** | ⚪️ | 1015 | Skipped |
| **Sadness** | ⚪️ | 124 | Skipped |
| **Практика — вибір точного слова** | ⚪️ | 182 | Skipped |
| **Підсумок** | ✅ | 200 | Included in Core |