# Audit Report: M38 — oleksander-potebnya.md
**Level:** C1 | **Module:** M38 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 10/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-01 23:29:20

## Configuration
**Type:** C1-biography
**Word Target:** 4000 words
**Activities:** 3-9 required
**Items per Activity:** ≥1 items
**Unique Types:** ≥3 types required
**Priority Types:** authorial-intent, comparative-study, critical-analysis, essay-response, quiz, reading
**Required Types:** essay-response, reading
**Engagement:** ≥5 callouts
**Immersion:** 95-100%
**Vocab Target:** ≥24 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | reading | Уривки з "Думка і мова" | 1 | 1 | ✅ |
| 2 | quiz | Життєвий шлях Олександра Потебні | 0 | 5 | ❌ |
| 3 | essay-response | Захист прав української мови | 1 | 1 | ✅ |
| 4 | comparative-study | Гумбольдт і Потебня | 1 | 1 | ✅ |
| 5 | critical-analysis | Символіка у фольклорі | 1 | 1 | ✅ |

**Summary:**
- Total activities: 5 (target: 3-9) ✅
- Unique types: 5 (minimum: 3) ✅
- Priority types used: 5/6 (comparative-study, critical-analysis, essay-response, quiz, reading) ✅
- Required types used: 2/2 (essay-response, reading) ✅
- Low density activities: 1

## PEDAGOGICAL VIOLATIONS
- **[LINGUISTIC_PURITY]** Found forbidden or historical characters outside of allowed context: ы
  - FIX: Remove non-Ukrainian characters (ё, ъ, ы, э, ѣ, etc.) or ensure they are inside a citation (> ) in the LIT track.
- **[COMPLEXITY]** quiz 'Життєвий шлях Олександра Потебні' has 0 items (minimum: 5)
  - FIX: Add more items. C1 quiz requires at least 5 items.
- **[HEADING_LEVEL]** Main section 'Vocabulary' uses H2 (##) but spec requires H1 (#)
  - FIX: Change '## Vocabulary' to '# Vocabulary' for top-level TOC compliance
- **[FORBIDDEN_HEADER]** Forbidden header '## Vocabulary' violates Clean MD standard (Issue #398)
  - FIX: Remove '## Vocabulary' header. This section is auto-injected from vocabulary/{slug}.yaml at build time. See docs/l2-uk-en/templates/ for correct pattern.
- **[FORBIDDEN_HEADER]** Forbidden header '## Зовнішні ресурси' violates Clean MD standard (Issue #398)
  - FIX: Remove '## Зовнішні ресурси' header. This section is auto-injected from docs/resources/external_resources.yaml at build time. See docs/l2-uk-en/templates/ for correct pattern.
- **[SECTION_ORDER]** '## Vocabulary' should come after 'external' section
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[SECTION_ORDER]** Content section '## Practice' appears after end section '# Activities'
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[LINGUISTIC_PURITY]** Found forbidden or historical characters outside of allowed context: ы
  - FIX: Remove non-Ukrainian characters (ё, ъ, ы, э, ѣ, etc.) or ensure they are inside a citation (> ) in the LIT track.
- **[YAML_SCHEMA_VIOLATION]** Schema error in oleksander-potebnya.yaml: Schema validation error at key '0': {'question': 'Що відображають фольклорні символи за Потебнею?', 'answers': ['Давнє міфологічне мислення', 'Випадкові фантазії', 'Художні прийоми', 'Релігійні догми'], 'correct': 'Давнє міфологічне мислення'} is not of type 'string'
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Життєпис' per template 'c1-biography-module-template.md'
  - FIX: Add '## Життєпис' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Внесок' per template 'c1-biography-module-template.md'
  - FIX: Add '## Внесок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Останні роки' per template 'c1-biography-module-template.md'
  - FIX: Add '## Останні роки' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Підсумок' per template 'c1-biography-module-template.md'
  - FIX: Add '## Підсумок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[FORBIDDEN_HEADER]** Forbidden header '## Vocabulary' violates Clean MD standard (Issue #398)
  - FIX: Remove '## Vocabulary' header. Template 'c1-biography-module-template.md' specifies this section is auto-injected from YAML sidecars.
- ❌ **[FORBIDDEN_HEADER]** Forbidden header '## Зовнішні ресурси' violates Clean MD standard (Issue #398)
  - FIX: Remove '## Зовнішні ресурси' header. Template 'c1-biography-module-template.md' specifies this section is auto-injected from YAML sidecars.

## Recommendation
**🔄 REWRITE** (severity 80/100)

- 15 violations (severe - consider revision)
- Structure issue: Missing '## Summary'
- Activity density below minimum

## Gates
- **Words:** ❌ 2138/4000 (raw: 2274)
- **Activities:** ✅ 5/3
- **Density:** ❌ 1 < 1
- **Unique_types:** ✅ 5/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 5/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 15 < 24 (soft target)
- **Structure:** ❌ Missing '## Summary'
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 9 violations
- **Content_heavy:** ✅ Content-heavy OK (5 activities)
- **Immersion:** 🇺🇦 98.9% (target 95-100% (biography))
- **Richness:** ❌ 54% < 95% min (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 10/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 54% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 0 | 4 | 0% | 19% | 0.0% |
| engagement | 5 | 6 | 83% | 14% | 11.9% |
| quotes | 0 | 3 | 0% | 14% | 0.0% |
| cultural | 2 | 4 | 50% | 10% | 4.8% |
| visual | 5 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 0.66 | - | 66% | 5% | 3.1% |
| questions | 1 | 3 | 33% | 5% | 1.6% |
| **TOTAL** | | | | | **54.6%** |

### Dryness Flags & Fixes
- ❌ **NO_QUOTES**
  - FIX:
    Add 2+ direct quotes from the subject. Use this format:
    
    > «[Exact quote from the person]»
    > — *[Person name], [context/year]*

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Життєвий шлях Олександра Потебні | quiz | 0 | 5 | Add 5 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Вступ — Український Гумбольдт** | ✅ | 393 | Included in Core |
| **Походження та освіта** | ⚪️ | 399 | Skipped |
| **"Думка і мова" (1862)** | ⚪️ | 450 | Skipped |
| **Харківська філологічна школа** | ⚪️ | 304 | Skipped |
| **Дослідження української мови** | ⚪️ | 330 | Skipped |
| **Спадщина та визнання** | ⚪️ | 262 | Skipped |
| **Activities** | ➖ | 0 | Excluded Type |
| **Vocabulary** | ➖ | 2 | Excluded Type |
| **Understanding** | ⚪️ | 6 | Skipped |
| **Analysis** | ⚪️ | 6 | Skipped |
| **Practice** | ⚪️ | 3 | Skipped |
| **Зовнішні ресурси** | ⚪️ | 49 | Skipped |