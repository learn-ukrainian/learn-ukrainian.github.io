# Audit Report: 88-interviu-ta-podkasty.md
**Phase:** B1.8 | **Level:** B1 | **Pedagogy:** PPP | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про слухання подкастів' item 1 has 7 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про слухання подкастів' item 2 has 7 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про слухання подкастів' item 3 has 7 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про слухання подкастів' item 4 has 6 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про слухання подкастів' item 5 has 7 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про слухання подкастів' item 7 has 6 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про слухання подкастів' item 8 has 7 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про слухання подкастів' item 9 has 5 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про слухання подкастів' item 10 has 7 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про слухання подкастів' item 11 has 6 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про слухання подкастів' item 12 has 7 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 88-interviu-ta-podkasty.yaml: [стратегії-слухання-та-розуміння-подкастів] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 88-interviu-ta-podkasty.yaml: [факти-про-стратегії-слухання] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 88-interviu-ta-podkasty.yaml: [терміни-слухання-та-їх-значення] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 88-interviu-ta-podkasty.yaml: [слова-для-обговорення-аудіоконтенту] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 88-interviu-ta-podkasty.yaml: [помилки-в-реченнях-про-слухання] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 88-interviu-ta-podkasty.yaml: [стратегії-ефективного-слухання] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 88-interviu-ta-podkasty.yaml: [категоризація-термінів-аудіоконтенту] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 88-interviu-ta-podkasty.yaml: [складіть-речення-про-слухання-подкастів] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 88-interviu-ta-podkasty.yaml: [оберіть-усі-правильні-варіанти] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 88-interviu-ta-podkasty.yaml: [перекладіть-речення-про-слухання] translate: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 88-interviu-ta-podkasty.yaml: [знайдіть-слова,-пов'язані-зі-слуханням] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення|Граматика|Теорія' per template 'b1-grammar-module-template'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Підсумок' found: Підсумок, Завдання: Підсумок подкасту
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 24 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2074/1500
- **Activities:** ✅ 11/10
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/4
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 32/15
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 22 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.0% (target 85-100% (B1.7-8 Ukraine))
- **Richness:** ✅ 99% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 45 | 24 | 100% | 20% | 20.0% |
| engagement | 8 | 5 | 100% | 15% | 15.0% |
| dialogues | 4 | 4 | 100% | 15% | 15.0% |
| variety | 0.97 | - | 97% | 10% | 9.7% |
| cultural | 3 | 3 | 100% | 10% | 10.0% |
| realworld | 10 | 3 | 100% | 10% | 10.0% |
| visual | 3 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 40 | 5 | 100% | 5% | 5.0% |
| proverbs | 2 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **99.7%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 44 | Included in Core |
| **Вступ** | ⚪️ | 146 | Skipped |
| **Презентація** | ⚪️ | 997 | Skipped |
| **Практика** | ⚪️ | 410 | Skipped |
| **Продукція** | ⚪️ | 262 | Skipped |
| **Підсумок** | ✅ | 105 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |