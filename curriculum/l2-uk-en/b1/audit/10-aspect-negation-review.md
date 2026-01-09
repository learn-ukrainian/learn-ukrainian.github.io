# Audit Report: 10-aspect-negation.md
**Phase:** B1.1 | **Level:** B1 | **Pedagogy:** TTT | **Target:** 1500
**Overall Status:** ❌ FAIL

## LINT ERRORS
- ❌ Line 16: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 27: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 28: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 31: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 66: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 68: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 72: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 80: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 113: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 115: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 172: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 179: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 191: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 192: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 201: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 218: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 223: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 224: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 233: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 234: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 244: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 245: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 246: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 247: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 261: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 362: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 426: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 428: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 453: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 457: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 463: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 464: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 469: Use Ukrainian angular quotes («...») instead of ASCII quotes (").

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 10-aspect-negation.yaml: [речення-із-запереченням] unjumble: 'items.7' - Additional properties are not allowed ('scrambled' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 10-aspect-negation.yaml: [заперечні-слова-та-частки] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 10-aspect-negation.yaml: [переклад--заперечення] translate: 'items.5' - 'source' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[VOCAB_PLAN_MISSING]** Missing vocabulary from plan (15 words): ніде, ніщо, неможливо, жодний, абсолютно...
  - FIX: Add missing words from curriculum plan to module vocabulary section.

## Recommendation
**📝 UPDATE** (severity 60/100)

- Revision recommended (severity 60/100)
- 4 violations (moderate)
- 33 format errors (many)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ✅ 1861/1500
- **Activities:** ❌ 0/12
- **Density:** ❌ 0 < 14
- **Unique_types:** ❌ 0/4 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 8/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 19 < 25 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ❌ 33 Format Errors
- **Pedagogy:** ❌ 3 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 98.5% (target 85-100% (B1.1 Aspect))
- **Richness:** ✅ 95% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 31 | 24 | 100% | 20% | 20.0% |
| engagement | 19 | 5 | 100% | 15% | 15.0% |
| dialogues | 32 | 4 | 100% | 15% | 15.0% |
| variety | 0.90 | - | 90% | 10% | 9.0% |
| cultural | 2 | 3 | 67% | 10% | 6.7% |
| realworld | 4 | 3 | 100% | 10% | 10.0% |
| visual | 22 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 0.95 | - | 95% | 5% | 4.8% |
| questions | 37 | 5 | 100% | 5% | 5.0% |
| proverbs | 2 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **95.5%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 8 | Included in Core |
| **Тест** | ⚪️ | 194 | Skipped |
| **Пояснення** | ⚪️ | 0 | Skipped |
| **Основне правило: заперечення + недоконаний вид** | ⚪️ | 209 | Skipped |
| **Негативні наказові форми** | ⚪️ | 41 | Skipped |
| **Негативні питання** | ⚪️ | 12 | Skipped |
| **Практика** | ⚪️ | 0 | Skipped |
| **Алгоритм вибору виду в запереченні** | ⚪️ | 125 | Skipped |
| **Поширені помилки** | ✅ | 68 | Included in Core |
| **Практичні сценарії** | ⚪️ | 191 | Skipped |
| **Діалоги** | ✅ | 0 | Included in Core |
| **Діалог 1: У книгарні** | ✅ | 109 | Included in Core |
| **Діалог 2: Розмова про фільм** | ✅ | 127 | Included in Core |
| **Діалог 3: Обговорення курсової роботи** | ✅ | 159 | Included in Core |
| **Діалог 4: Попередження батьків** | ✅ | 125 | Included in Core |
| **Діалог 5: У ресторані** | ✅ | 126 | Included in Core |
| **Діалог 6: У лікаря** | ✅ | 151 | Included in Core |
| **Підсумок** | ✅ | 0 | Included in Core |
| **Основні правила заперечення** | ⚪️ | 120 | Skipped |
| **Таблиця вибору** | ⚪️ | 0 | Skipped |
| **Самоперевірка** | ⚪️ | 96 | Skipped |
| **Need More Practice?** | ⚪️ | 0 | Skipped |