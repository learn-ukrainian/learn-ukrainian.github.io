# Audit Report: 56-synonyms-size.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть відповідність' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точний синонім' Q1 prompt length 12 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точний синонім' Q2 prompt length 12 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точний синонім' Q3 prompt length 10 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точний синонім' Q4 prompt length 10 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точний синонім' Q5 prompt length 11 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точний синонім' Q6 prompt length 11 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точний синонім' Q7 prompt length 12 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точний синонім' Q8 prompt length 12 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY]** match-up 'Регістри та розміри' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Параметри та об'єкти' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Ранжування інтенсивності' Q1 prompt length 7 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Ранжування інтенсивності' Q2 prompt length 5 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Ранжування інтенсивності' Q3 prompt length 8 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Ранжування інтенсивності' Q4 prompt length 7 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Ранжування інтенсивності' Q5 prompt length 6 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Ранжування інтенсивності' Q6 prompt length 5 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Ранжування інтенсивності' Q7 prompt length 7 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Ранжування інтенсивності' Q8 prompt length 6 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 56-synonyms-size.yaml: [перекладіть-масштаб] translate: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 56-synonyms-size.yaml: [ранжування-інтенсивності] quiz: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: vocab) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[VOCAB_PLAN_MISSING]** Missing vocabulary from plan (15 words): вузький, довгий, короткий, тонкий, об'ємний...
  - FIX: Add missing words from curriculum plan to module vocabulary section.

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 23 violations (severe - consider revision)

## Gates
- **Words:** ✅ 1787/1750
- **Activities:** ✅ 14/13
- **Density:** ✅ All > 16
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 112/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 22 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.9% (target 98-100% (vocab))
- **Richness:** ✅ 95% (content)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** content

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 41 | 15 | 100% | 25% | 25.0% |
| engagement | 4 | 5 | 80% | 19% | 15.0% |
| variety | 0.98 | - | 98% | 12% | 12.2% |
| cultural | 5 | 4 | 100% | 12% | 12.5% |
| realworld | 8 | 3 | 100% | 12% | 12.5% |
| visual | 4 | 4 | 100% | 6% | 6.2% |
| paragraph_var | 1.00 | - | 100% | 6% | 6.2% |
| questions | 7 | 4 | 100% | 6% | 6.2% |
| **TOTAL** | | | | | **96.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 64 | Included in Core |
| **Вступ: Велич і мізерність навколо нас** | ⚪️ | 118 | Skipped |
| **Частина 1: Від великого до колосального — Архітектура та простір** | ✅ | 376 | Included in Core |
| **Частина 2: Світ у краплині води — Увага до деталей** | ✅ | 378 | Included in Core |
| **Частина 3: Параметри, виміри та їхня роль у науці** | ✅ | 263 | Included in Core |
| **Частина 4: Мистецтво порівняння та гіперболи в літературі** | ✅ | 137 | Included in Core |
| **Частина 5: Практичний додаток — Регістр має значення** | ✅ | 165 | Included in Core |
| **Частина 6: Індустріальний масштаб та урбаністика** | ✅ | 226 | Included in Core |
| **Підсумок** | ✅ | 60 | Included in Core |
| **Need More Practice?** | ⚪️ | 0 | Skipped |