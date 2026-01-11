# Audit Report: 60-synonyms-character.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть точне слово' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** group-sort 'Світло і Тіні' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY]** match-up 'Регістри та Риси' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Натура та Вчинки' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Характер у літературі' Q1 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Характер у літературі' Q2 prompt length 4 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Характер у літературі' Q3 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Характер у літературі' Q5 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Характер у літературі' Q6 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Характер у літературі' Q7 prompt length 3 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Характер у літературі' Q8 prompt length 4 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 60-synonyms-character.yaml: Array validation: {'type': 'select', 'title': 'Чесноти та Вади', 'instruction': 'Оберіть усі слова, що позначають позитивні якості (6+ елементів).', 'items': [{'question': 'Які слова описують шляхетну людину? (6+)', 'options': [{'text': 'милосердний', 'correct': True}, {'text': 'чуйний', 'correct': True}, {'text': 'щедрий', 'correct': True}, {'text': 'принциповий', 'correct': True}, {'text': 'незламний', 'correct': True}, {'text': 'сумлінний', 'correct': True}, {'text': 'турботливий', 'correct': True}]}, {'question': 'Оберіть вади характеру:', 'options': [{'text': 'байдужість', 'correct': True}, {'text': 'егоїзм', 'correct': True}, {'text': 'жорстокість', 'correct': True}, {'text': 'мудрість', 'correct': False}]}, {'question': 'Які слова описують активну доброту?', 'options': [{'text': 'жертовний', 'correct': True}, {'text': 'невтомний', 'correct': True}, {'text': 'дбайливий', 'correct': True}, {'text': 'пасивний', 'correct': False}]}, {'question': 'Оберіть ознаки емоційного інтелекту:', 'options': [{'text': 'емпатія', 'correct': True}, {'text': 'співпереживання', 'correct': True}, {'text': 'чуйність', 'correct': True}, {'text': 'агресія', 'correct': False}]}, {'question': 'Які слова вказують на професійний характер?', 'options': [{'text': 'пунктуальний', 'correct': True}, {'text': 'відповідальний', 'correct': True}, {'text': 'сумлінний', 'correct': True}, {'text': 'лінивий', 'correct': False}]}, {'question': 'Оберіть риси сучасного лідера:', 'options': [{'text': 'харизматичний', 'correct': True}, {'text': 'далекоглядний', 'correct': True}, {'text': 'гнучкий', 'correct': True}, {'text': 'жорсткий', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 60-synonyms-character.yaml: [index-7] translate: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 60-synonyms-character.yaml: [index-13] select: 'items.0.options' - [{'text': 'милосердний', 'correct': True}, {'text': 'чуйний', 'correct': True}, {'text': 'щедрий', 'correct': True}, {'text': 'принциповий', 'correct': True}, {'text': 'незламний', 'correct': True}, {'text': 'сумлінний', 'correct': True}, {'text': 'турботливий', 'correct': True}] is too long
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
- 17 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2342/1750
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 13/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 115/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 15 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.3% (target 90-100% (vocab))
- **Richness:** ✅ 96% (phraseology)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 96% (minimum: 95%)
**Module Type:** phraseology

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| engagement | 15 | 4 | 100% | 25% | 25.0% |
| variety | 0.93 | - | 93% | 17% | 15.5% |
| cultural | 4 | - | 100% | 17% | 16.7% |
| visual | 11 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 0.74 | - | 74% | 8% | 6.2% |
| examples | 56 | - | 100% | 8% | 8.3% |
| realworld | 9 | - | 100% | 8% | 8.3% |
| questions | 9 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **96.7%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 72 | Included in Core |
| **Вступ: Мозаїка людської душі** | ⚪️ | 101 | Skipped |
| **Частина 1: Сяйво розуму — Від «кмітливості» до «мудрості»** | ✅ | 218 | Included in Core |
| **Частина 2: Тепло серця — Від «доброти» до «самопожертви»** | ✅ | 230 | Included in Core |
| **Частина 3: Тіні характеру — Від «байдужості» до «жорстокості»** | ✅ | 159 | Included in Core |
| **Частина 4: Характер в українській літературі та філософії** | ✅ | 91 | Included in Core |
| **Частина 5: Практичний додаток — Регістри та Портрет** | ✅ | 16 | Included in Core |
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