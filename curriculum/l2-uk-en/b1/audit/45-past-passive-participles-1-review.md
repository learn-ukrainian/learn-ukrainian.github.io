# Audit Report: 45-past-passive-participles-1.md
**Phase:** B1.4 | **Level:** B1 | **Pedagogy:** TTT | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Теоретичні знання про пасивні дієприкметники минулого часу' Q6 prompt length 11 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Теоретичні знання про пасивні дієприкметники минулого часу' Q9 prompt length 11 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Побудова речень з пасивними дієприкметниками' item 1 has 6 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Побудова речень з пасивними дієприкметниками' item 2 has 7 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Побудова речень з пасивними дієприкметниками' item 3 has 5 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Побудова речень з пасивними дієприкметниками' item 4 has 6 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Побудова речень з пасивними дієприкметниками' item 5 has 5 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Побудова речень з пасивними дієприкметниками' item 6 has 5 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Побудова речень з пасивними дієприкметниками' item 7 has 5 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Побудова речень з пасивними дієприкметниками' item 8 has 6 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY]** mark-the-words 'Знайдіть пасивні дієприкметники в тексті' has 0 items (minimum: 6)
  - FIX: Add more items. B1 mark-the-words requires at least 6 items.
- **[MISSING_FIELD]** mark-the-words 'Знайдіть пасивні дієприкметники в тексті' is missing 'correct_words' array
  - FIX: Add 'correct_words' array with correct words
- **[YAML_SCHEMA_VIOLATION]** Schema error in 45-past-passive-participles-1.yaml: [знайдіть-пасивні-дієприкметники-в-тексті] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Warm-up|Introduction|Objectives|Контекст|Вступ|Розминка|Тест' per template 'b1-grammar-module-template'
  - FIX: Add '## Warm-up' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Practice|Exercises|Activity|Практика|Вправи' found: Практика, Корисні вправи для самостійної практики
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**🔄 REWRITE** (severity 75/100)

- 16 violations (severe - consider revision)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ✅ 1562/1500
- **Activities:** ❌ 11/12
- **Density:** ❌ 1 < 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 55/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 13 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.9% (target 85-100% (B1.3-4 Complex))
- **Richness:** ✅ 99% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 39 | 24 | 100% | 20% | 20.0% |
| engagement | 7 | 5 | 100% | 15% | 15.0% |
| dialogues | 11 | 4 | 100% | 15% | 15.0% |
| variety | 0.94 | - | 94% | 10% | 9.4% |
| cultural | 3 | 3 | 100% | 10% | 10.0% |
| realworld | 4 | 3 | 100% | 10% | 10.0% |
| visual | 7 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 18 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **99.4%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Знайдіть пасивні дієприкметники в тексті | mark-the-words | 0 | 6 | Add 6 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 63 | Included in Core |
| **Діагностика** | ✅ | 79 | Included in Core |
| **Теоретичне пояснення** | ⚪️ | 493 | Skipped |
| **Практика** | ⚪️ | 173 | Skipped |
| **Приклади використання** | ⚪️ | 197 | Skipped |
| **Пасивні дієприкметники у формальному листуванні** | ⚪️ | 110 | Skipped |
| **Пасивні дієприкметники в українській культурі та літературі** | ✅ | 257 | Included in Core |
| **Порівняння з активними конструкціями** | ⚪️ | 29 | Skipped |
| **Практичні поради для запам'ятовування** | ⚪️ | 102 | Skipped |
| **Підсумок** | ✅ | 59 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |