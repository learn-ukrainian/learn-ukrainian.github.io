# Audit Report: 60-synonyms-character.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть точне слово' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Портрет особистості' Q1 prompt length 11 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Портрет особистості' Q2 prompt length 11 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Портрет особистості' Q3 prompt length 13 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Портрет особистості' Q4 prompt length 11 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Портрет особистості' Q5 prompt length 12 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Портрет особистості' Q6 prompt length 14 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Портрет особистості' Q7 prompt length 13 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Портрет особистості' Q8 prompt length 10 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY]** group-sort 'Світло і Тіні' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY]** match-up 'Регістри та Риси' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Натура та Вчинки' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Характер у літературі' Q1 prompt length 5 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Характер у літературі' Q2 prompt length 4 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Характер у літературі' Q3 prompt length 6 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Характер у літературі' Q4 prompt length 10 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Характер у літературі' Q5 prompt length 7 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Характер у літературі' Q6 prompt length 6 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Характер у літературі' Q7 prompt length 3 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Характер у літературі' Q8 prompt length 4 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 60-synonyms-character.yaml: [переклад-характеру] translate: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 60-synonyms-character.yaml: [характер-у-літературі] quiz: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 60-synonyms-character.yaml: [чесноти-та-вади] select: 'items.0.options' - [{'text': 'милосердний', 'correct': True}, {'text': 'чуйний', 'correct': True}, {'text': 'щедрий', 'correct': True}, {'text': 'принциповий', 'correct': True}, {'text': 'незламний', 'correct': True}, {'text': 'сумлінний', 'correct': True}, {'text': 'турботливий', 'correct': True}] is too long
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: vocab) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[VOCAB_PLAN_MISSING]** Missing vocabulary from plan (13 words): інтелектуальний, освічений, геніальний, злий, риса...
  - FIX: Add missing words from curriculum plan to module vocabulary section.

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 25 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2232/1750
- **Activities:** ✅ 14/13
- **Density:** ✅ All > 16
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 12/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 115/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 24 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.9% (target 98-100% (vocab))
- **Richness:** ✅ 97% (content)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** content

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 55 | 15 | 100% | 25% | 25.0% |
| engagement | 13 | 5 | 100% | 19% | 18.7% |
| variety | 0.93 | - | 93% | 12% | 11.6% |
| cultural | 4 | 4 | 100% | 12% | 12.5% |
| realworld | 9 | 3 | 100% | 12% | 12.5% |
| visual | 11 | 4 | 100% | 6% | 6.2% |
| paragraph_var | 0.75 | - | 75% | 6% | 4.7% |
| questions | 9 | 4 | 100% | 6% | 6.2% |
| **TOTAL** | | | | | **97.6%** |

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
| **Need More Practice?** | ⚪️ | 0 | Skipped |