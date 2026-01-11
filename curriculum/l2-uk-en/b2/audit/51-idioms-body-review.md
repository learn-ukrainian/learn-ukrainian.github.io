# Audit Report: 51-idioms-body.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть відповідність' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть правильний фразеологізм' Q2 prompt length 8 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть правильний фразеологізм' Q3 prompt length 8 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть правильний фразеологізм' Q6 prompt length 8 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть правильний фразеологізм' Q7 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть правильний фразеологізм' Q8 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY]** group-sort 'Емоційне забарвлення' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 1 has 5 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 2 has 5 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 3 has 5 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 4 has 6 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 5 has 5 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 6 has 4 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 7 has 4 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 8 has 6 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY]** match-up 'Контекст вживання' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Антоніми' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Деталі значення' Q3 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Деталі значення' Q4 prompt length 8 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Деталі значення' Q5 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Деталі значення' Q6 prompt length 8 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Деталі значення' Q7 prompt length 8 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Деталі значення' Q8 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 51-idioms-body.yaml: Array validation: {'type': 'select', 'title': 'Синоніми', 'instruction': 'Оберіть синонім до фразеологізму.', 'items': [{'question': 'Синонім до камінь з душі:', 'options': [{'text': 'полегшення', 'correct': True}, {'text': 'страх', 'correct': False}, {'text': 'горе', 'correct': False}]}, {'question': "Синонім до душа в п'яти:", 'options': [{'text': 'переляк', 'correct': True}, {'text': 'радість', 'correct': False}, {'text': 'сміливість', 'correct': False}]}, {'question': 'Синонім до споріднена душа:', 'options': [{'text': 'однодумець', 'correct': True}, {'text': 'ворог', 'correct': False}, {'text': 'сусід', 'correct': False}]}, {'question': 'Синонім до від щирого серця:', 'options': [{'text': 'щиро', 'correct': True}, {'text': 'хитро', 'correct': False}, {'text': 'швидко', 'correct': False}]}, {'question': 'Синонім до серце крається:', 'options': [{'text': 'шкода', 'correct': True}, {'text': 'весело', 'correct': False}, {'text': 'байдуже', 'correct': False}]}, {'question': 'Синонім до брати до серця:', 'options': [{'text': 'перейматися', 'correct': True}, {'text': 'ігнорувати', 'correct': False}, {'text': 'забути', 'correct': False}]}, {'question': 'Синонім до всією душею:', 'options': [{'text': 'віддано', 'correct': True}, {'text': 'ліниво', 'correct': False}, {'text': 'часом', 'correct': False}]}, {'question': 'Синонім до душа нараспашку:', 'options': [{'text': 'відвертість', 'correct': True}, {'text': 'скритність', 'correct': False}, {'text': 'злість', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 51-idioms-body.yaml: [index-8] select: 'items.7.options' - [{'text': 'відвертість', 'correct': True}, {'text': 'скритність', 'correct': False}, {'text': 'злість', 'correct': False}] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: vocab) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Вступ|Контекст|Розминка' found: Вступ: Емоційний ландшафт, Вживання у контексті: Практика
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 27 violations (severe - consider revision)

## Gates
- **Words:** ✅ 1975/1750
- **Activities:** ✅ 13/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 102/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 26 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 98.9% (target 90-100% (vocab))
- **Richness:** ✅ 99% (phraseology)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** phraseology

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| engagement | 11 | 4 | 100% | 25% | 25.0% |
| variety | 0.98 | - | 98% | 17% | 16.3% |
| cultural | 4 | - | 100% | 17% | 16.7% |
| visual | 4 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 1.00 | - | 100% | 8% | 8.3% |
| examples | 17 | - | 100% | 8% | 8.3% |
| realworld | 7 | - | 100% | 8% | 8.3% |
| questions | 16 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **99.7%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 64 | Included in Core |
| **Вступ: Емоційний ландшафт** | ⚪️ | 238 | Skipped |
| **Частина 1: Душа — Дзеркало внутрішнього світу** | ✅ | 411 | Included in Core |
| **Частина 2: Серце — Центр болю та співчуття** | ✅ | 179 | Included in Core |
| **Культурний код: Кордоцентризм** | ✅ | 160 | Included in Core |
| **Фольклор і Пісні** | ⚪️ | 113 | Skipped |
| **Вживання у контексті: Практика** | ✅ | 317 | Included in Core |
| **Стилістичні поради** | ⚪️ | 324 | Skipped |
| **Підсумок** | ✅ | 59 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |