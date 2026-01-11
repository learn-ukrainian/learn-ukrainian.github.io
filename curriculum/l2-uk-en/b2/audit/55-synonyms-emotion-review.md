# Audit Report: 55-synonyms-emotion.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть значення' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Емоційні речення' item 1 has 6 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Емоційні речення' item 2 has 5 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Емоційні речення' item 3 has 5 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Емоційні речення' item 4 has 5 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Емоційні речення' item 5 has 5 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Емоційні речення' item 6 has 6 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Емоційні речення' item 7 has 6 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Емоційні речення' item 8 has 5 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY]** group-sort 'Позитивні чи Негативні?' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY]** match-up 'Контексти вживання (Емоції)' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Психологічні нюанси' Q2 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Психологічні нюанси' Q4 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Психологічні нюанси' Q8 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 55-synonyms-emotion.yaml: Array validation: {'type': 'translate', 'title': 'Переклад почуттів', 'instruction': 'Знайдіть найточніший український синонім до англійського слова.', 'items': [{'source': 'Fury / Rage', 'options': [{'text': 'лють', 'correct': True}, {'text': 'сум', 'correct': False}, {'text': 'втіха', 'correct': False}, {'text': 'радість'}], 'explanation': 'Це слова на позначення найвищого ступеня гніву.'}, {'source': 'Grief / Deep sorrow', 'options': [{'text': 'горе', 'correct': True}, {'text': 'задоволення', 'correct': False}, {'text': 'хвилювання', 'correct': False}, {'text': 'екстаз'}], 'explanation': 'Горе описує глибоке страждання.'}, {'source': 'Pleasure (sensory)', 'options': [{'text': 'насолода', 'correct': True}, {'text': 'тривога', 'correct': False}, {'text': 'паніка', 'correct': False}, {'text': 'злість'}], 'explanation': 'Насолода — це задоволення від відчуттів.'}, {'source': 'Anxiety / Unease', 'options': [{'text': 'тривога', 'correct': True}, {'text': 'щастя', 'correct': False}, {'text': 'лють', 'correct': False}, {'text': 'втіха'}], 'explanation': 'Тривога — це неспокій через майбутні події.'}, {'source': 'Despair / Hopelessness', 'options': [{'text': 'розпач', 'correct': True}, {'text': 'захоплення', 'correct': False}, {'text': 'ейфорія', 'correct': False}, {'text': 'радість'}], 'explanation': 'Розпач — стан втрати надії.'}, {'source': 'Satisfaction', 'options': [{'text': 'задоволення', 'correct': True}, {'text': 'жах', 'correct': False}, {'text': 'меланхолія', 'correct': False}, {'text': 'агресія'}], 'explanation': 'Задоволення виникає після виконаної праці.'}, {'source': 'Delight / Consolation', 'options': [{'text': 'втіха', 'correct': True}, {'text': 'паніка', 'correct': False}, {'text': 'гнів', 'correct': False}, {'text': 'страх'}], 'explanation': 'Втіха — це тиха і приємна радість.'}, {'source': 'Nostalgic longing', 'options': [{'text': 'туга', 'correct': True}, {'text': 'екстаз', 'correct': False}, {'text': 'ейфорія', 'correct': False}, {'text': 'задоволення'}], 'explanation': "Туга часто пов'язана з пам'яттю про щось рідне."}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 55-synonyms-emotion.yaml: [index-9] translate: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: vocab) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Фразеологізми' per template 'b2-phraseology-module-template'
  - FIX: Add '## Фразеологізми' section as specified in docs/l2-uk-en/templates/b2-phraseology-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Вживання у контексті' per template 'b2-phraseology-module-template'
  - FIX: Add '## Вживання у контексті' section as specified in docs/l2-uk-en/templates/b2-phraseology-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 19 violations (severe - consider revision)

## Gates
- **Words:** ✅ 1883/1750
- **Activities:** ✅ 13/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 104/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 17 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.1% (target 90-100% (vocab))
- **Richness:** ✅ 100% (phraseology)
- **Grammar:** ⏳ Pending validation

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
| examples | 53 | - | 100% | 8% | 8.3% |
| realworld | 6 | - | 100% | 8% | 8.3% |
| questions | 10 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 87 | Included in Core |
| **Вступ: Мова як інструмент душі та дзеркало серця** | ⚪️ | 220 | Skipped |
| **Частина 1: Світло радості — Від задоволення до екстазу** | ✅ | 238 | Included in Core |
| **Частина 2: Сутінки суму — Від печалі до повного розпачу** | ✅ | 237 | Included in Core |
| **Частина 3: Вогонь гніву та Тінь паралізуючого страху** | ✅ | 286 | Included in Core |
| **Культурний код: Емоції в українській ментальності та філософії** | ✅ | 423 | Included in Core |
| **Емоції та почуття в українській класичній літературі** | ⚪️ | 124 | Skipped |
| **Практичний додаток: Таблиця інтенсивності та Регістрів** | ⚪️ | 68 | Skipped |
| **Підсумок** | ✅ | 90 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |