# Audit Report: 61-synonyms-time.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть часовий відтінок' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Точність моменту' Q7 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY]** match-up 'Регістри та Час' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Час та Події' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Час у мистецтві' Q1 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Час у мистецтві' Q2 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Час у мистецтві' Q3 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Час у мистецтві' Q5 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Час у мистецтві' Q6 prompt length 8 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Час у мистецтві' Q7 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Час у мистецтві' Q8 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 61-synonyms-time.yaml: [знайдіть-часовий-відтінок] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 61-synonyms-time.yaml: [точність-моменту] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 61-synonyms-time.yaml: [шкала-часу] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 61-synonyms-time.yaml: [складіть-часове-речення] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 61-synonyms-time.yaml: [ритм-історії] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 61-synonyms-time.yaml: [оберіть-часову-одиницю] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 61-synonyms-time.yaml: [виправте-час] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 61-synonyms-time.yaml: [переклад-термінів-часу] translate: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 61-synonyms-time.yaml: [нюанси-тривалості] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 61-synonyms-time.yaml: [теперішній-час] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 61-synonyms-time.yaml: [регістри-та-час] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 61-synonyms-time.yaml: [час-та-події] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 61-synonyms-time.yaml: [час-у-мистецтві] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 61-synonyms-time.yaml: [масштаби-часу] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: vocab) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення|Граматика|Теорія' per template 'b2-module-template'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b2-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 27 violations (severe - consider revision)

## Gates
- **Words:** ✅ 1872/1750
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 65/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 26 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.1% (target 98-100% (vocab))
- **Richness:** ✅ 98% (content)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 98% (minimum: 95%)
**Module Type:** content

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 29 | 15 | 100% | 25% | 25.0% |
| engagement | 8 | 5 | 100% | 19% | 18.7% |
| variety | 0.97 | - | 97% | 12% | 12.1% |
| cultural | 4 | 4 | 100% | 12% | 12.5% |
| realworld | 9 | 3 | 100% | 12% | 12.5% |
| visual | 5 | 4 | 100% | 6% | 6.2% |
| paragraph_var | 0.79 | - | 79% | 6% | 4.9% |
| questions | 5 | 4 | 100% | 6% | 6.2% |
| **TOTAL** | | | | | **98.3%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 79 | Included in Core |
| **Вступ: Плин часу в українському просторі** | ⚪️ | 86 | Skipped |
| **Частина 1: Теперішній момент — Від «зараз» до «наразі»** | ✅ | 174 | Included in Core |
| **Частина 2: Минуле — Від «щойно» до «вічності»** | ✅ | 124 | Included in Core |
| **Частина 3: Масштаби часу — Від миті до епохи** | ✅ | 103 | Included in Core |
| **Частина 4: Час в українській культурі — «Розстріляне відродження»** | ✅ | 62 | Included in Core |
| **Частина 5: Практичний додаток — Ритм повідомлення** | ✅ | 48 | Included in Core |
| **Частина 6: Майбутнє — Від «завтра» до «згодом»** | ✅ | 69 | Included in Core |
| **Частина 7: Час у цифрову епоху** | ✅ | 80 | Included in Core |
| **Частина 8: Час у народній уяві та обрядах** | ✅ | 86 | Included in Core |
| **Частина 9: Історична пам'ять та тяглість поколінь** | ✅ | 86 | Included in Core |
| **Частина 10: Психологія сприйняття часу** | ✅ | 110 | Included in Core |
| **Частина 11: Час у сучасному мистецтві та медіа** | ✅ | 91 | Included in Core |
| **Частина 12: Майбутнє як простір надії та планування** | ✅ | 259 | Included in Core |
| **Частина 14: Час у науковому пізнанні світу** | ✅ | 97 | Included in Core |
| **Частина 15: Сприйняття часу в різних культурах** | ✅ | 161 | Included in Core |
| **Підсумок** | ✅ | 47 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |