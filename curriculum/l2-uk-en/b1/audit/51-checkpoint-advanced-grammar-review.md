# Audit Report: 51-checkpoint-advanced-grammar.md
**Phase:** B1.4 | **Level:** B1 | **Pedagogy:** TTT | **Target:** 1200
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Пасивні дієприкметники — повна форма (M45)' Q4 prompt length 7 (target: 9-20)
  - FIX: Adjust prompt length to 9-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Пасивні дієприкметники — повна форма (M45)' Q8 prompt length 7 (target: 9-20)
  - FIX: Adjust prompt length to 9-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Пасивні дієприкметники — коротка форма (M46)' Q4 prompt length 6 (target: 9-20)
  - FIX: Adjust prompt length to 9-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Пасивні дієприкметники — коротка форма (M46)' Q5 prompt length 8 (target: 9-20)
  - FIX: Adjust prompt length to 9-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Пасивні дієприкметники — коротка форма (M46)' Q6 prompt length 6 (target: 9-20)
  - FIX: Adjust prompt length to 9-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Пасивні дієприкметники — коротка форма (M46)' Q8 prompt length 6 (target: 9-20)
  - FIX: Adjust prompt length to 9-20 words.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з дієприслівниками та дієприкметниками' item 1 has 6 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з дієприслівниками та дієприкметниками' item 2 has 5 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з дієприслівниками та дієприкметниками' item 3 has 5 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з дієприслівниками та дієприкметниками' item 4 has 4 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з дієприслівниками та дієприкметниками' item 5 has 5 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з дієприслівниками та дієприкметниками' item 7 has 5 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з дієприслівниками та дієприкметниками' item 8 has 5 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з дієприслівниками та дієприкметниками' item 9 has 5 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення з дієприслівниками та дієприкметниками' item 10 has 5 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 51-checkpoint-advanced-grammar.yaml: [index-13] unjumble: 'items.9' - Additional properties are not allowed ('scrambled' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 51-checkpoint-advanced-grammar.yaml: [index-16] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Вступ|Контекст|Розминка|Тест' per template 'b1-grammar-module-template'
  - FIX: Add '## Вступ' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Практика|Вправи' per template 'b1-grammar-module-template'
  - FIX: Add '## Практика' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 19 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2020/1200
- **Activities:** ✅ 19/10
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/3
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 28/10
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 17 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.1% (checkpoint - no gate)
- **Richness:** ✅ 98% (checkpoint)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 98% (minimum: 85%)
**Module Type:** checkpoint

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| activity_types | 11 | 8 | 100% | 25% | 25.0% |
| review_sections | 38 | 3 | 100% | 20% | 20.0% |
| variety | 0.91 | - | 91% | 15% | 13.7% |
| engagement | 5 | 3 | 100% | 10% | 10.0% |
| cultural | 2 | - | 100% | 10% | 10.0% |
| visual | 10 | 3 | 100% | 10% | 10.0% |
| paragraph_var | 0.96 | - | 96% | 10% | 9.6% |
| **TOTAL** | | | | | **98.2%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 82 | Included in Core |
| **Огляд** | ⚪️ | 89 | Skipped |
| **Skill 1: Дієприслівники недоконаного виду (M42)** | ⚪️ | 185 | Skipped |
| **Skill 2: Дієприслівники доконаного виду (M43)** | ⚪️ | 185 | Skipped |
| **Skill 3: Активні дієприкметники (M44)** | ⚪️ | 208 | Skipped |
| **Skill 4: Пасивні дієприкметники — повна форма (M45)** | ⚪️ | 172 | Skipped |
| **Skill 5: Пасивні дієприкметники — коротка форма (M46)** | ⚪️ | 181 | Skipped |
| **Skill 6: Пасивні конструкції (M47)** | ⚪️ | 146 | Skipped |
| **Skill 7: Демінутиви (M48)** | ⚪️ | 189 | Skipped |
| **Skill 8: Збірні числівники та дроби (M49)** | ⚪️ | 161 | Skipped |
| **Інтеграційне завдання** | ⚪️ | 182 | Skipped |
| **Підсумок** | ✅ | 130 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |