# Audit Report: 53-idioms-animals-ii.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## LINT ERRORS
- ❌ Line 31: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 51: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 141: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 143: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 166: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 203: Use Ukrainian angular quotes («...») instead of ASCII quotes (").

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть значення' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть ситуацію' Q2 prompt length 14 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть ситуацію' Q3 prompt length 11 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть ситуацію' Q4 prompt length 12 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть ситуацію' Q5 prompt length 12 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть ситуацію' Q6 prompt length 12 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть ситуацію' Q7 prompt length 14 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть ситуацію' Q8 prompt length 12 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY]** group-sort 'Класифікація за емоціями' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть ідіому' item 1 has 4 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть ідіому' item 2 has 5 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть ідіому' item 3 has 6 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть ідіому' item 4 has 5 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть ідіому' item 5 has 6 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть ідіому' item 6 has 5 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть ідіому' item 7 has 5 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть ідіому' item 8 has 4 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY]** match-up 'Тварини та Стихії' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Антоніми за змістом' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Походження та Традиції' Q1 prompt length 14 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Походження та Традиції' Q2 prompt length 8 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Походження та Традиції' Q3 prompt length 7 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Походження та Традиції' Q4 prompt length 9 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Походження та Традиції' Q5 prompt length 13 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Походження та Традиції' Q6 prompt length 8 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Походження та Традиції' Q7 prompt length 10 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Походження та Традиції' Q8 prompt length 9 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 53-idioms-animals-ii.yaml: [переклад-на-українську] translate: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 53-idioms-animals-ii.yaml: [походження-та-традиції] quiz: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: vocab) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[VOCAB_PLAN_MISSING]** Missing vocabulary from plan (15 words): заєць, хижак, порівняння, зменшення, м'ясо...
  - FIX: Add missing words from curriculum plan to module vocabulary section.

## Recommendation
**📝 UPDATE** (severity 70/100)

- Revision recommended (severity 70/100)
- 31 violations (severe - consider revision)
- 6 format errors (many)

## Gates
- **Words:** ⚠️ 1719/1750 (31 short)
- **Activities:** ✅ 13/13
- **Density:** ✅ All > 16
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 112/35
- **Structure:** ✅ Valid Structure
- **Lint:** ❌ 6 Format Errors
- **Pedagogy:** ❌ 30 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.9% (target 98-100% (vocab))
- **Richness:** ✅ 98% (content)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 98% (minimum: 95%)
**Module Type:** content

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 39 | 15 | 100% | 25% | 25.0% |
| engagement | 8 | 5 | 100% | 19% | 18.7% |
| variety | 0.99 | - | 99% | 12% | 12.4% |
| cultural | 6 | 4 | 100% | 12% | 12.5% |
| realworld | 7 | 3 | 100% | 12% | 12.5% |
| visual | 3 | 4 | 75% | 6% | 4.7% |
| paragraph_var | 0.99 | - | 99% | 6% | 6.2% |
| questions | 8 | 4 | 100% | 6% | 6.2% |
| **TOTAL** | | | | | **98.2%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 77 | Included in Core |
| **Вступ: Світ навколо нас як джерело мудрості** | ⚪️ | 209 | Skipped |
| **Частина 1: Птахи та Ссавці — Неуважність та Стратегія** | ✅ | 247 | Included in Core |
| **Частина 2: Риби — Майстерність та Хаос у водній стихії** | ✅ | 244 | Included in Core |
| **Частина 3: Комахи — Від ідеальної чистоти до перебільшення** | ✅ | 149 | Included in Core |
| **Культурний код: Тварини, Стихії та Українська ментальність** | ✅ | 445 | Included in Core |
| **Природа в українській класичній поезії** | ⚪️ | 117 | Skipped |
| **Практичний додаток: Нюанси використання та Регістри** | ⚪️ | 141 | Skipped |
| **Підсумок** | ✅ | 90 | Included in Core |
| **Need More Practice?** | ⚪️ | 0 | Skipped |