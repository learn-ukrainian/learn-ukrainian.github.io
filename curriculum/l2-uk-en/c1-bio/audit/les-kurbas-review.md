# Audit Report: M77 — les-kurbas.md
**Level:** C1 | **Module:** M77 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:38

## Configuration
**Type:** C1-biography
**Word Target:** 4000 words
**Activities:** 3-9 required
**Items per Activity:** ≥1 items
**Unique Types:** ≥3 types required
**Priority Types:** authorial-intent, comparative-study, critical-analysis, essay-response, quiz, reading
**Required Types:** essay-response, fill-in, group-sort, match-up, quiz, reading
**Engagement:** ≥5 callouts
**Immersion:** 95-100%
**Vocab Target:** ≥24 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | quiz | Розуміння тексту: Феномен Курбаса | 5 | 5 | ✅ |
| 2 | fill-in | Театральна та біографічна лексика | 6 | 6 | ✅ |
| 3 | error-correction | Граматика: Аналіз театральних подій | 5 | 5 | ✅ |
| 4 | match-up | Театральний словник Курбаса | 8 | 6 | ✅ |
| 5 | select | Лінгвістичний аналіз цитати про театр | 5 | 5 | ✅ |
| 6 | group-sort | Класифікація театральних систем | 12 | 1 | ✅ |
| 7 | true-false | Факти про життя Леся Курбаса | 5 | 5 | ✅ |
| 8 | authorial-intent | Намір автора: Сповідь режисера | 1 | 1 | ✅ |
| 9 | essay-response | Аналіз спадщини: Курбас і модерна Україна | 1 | 1 | ✅ |
| 10 | comparative-study | Порівняння: Курбас vs Брехт | 1 | 1 | ✅ |
| 11 | critical-analysis | Аналіз трагедії Сандармоху | 1 | 1 | ✅ |
| 12 | translate | Переклад термінів театрального авангарду | 5 | 5 | ✅ |
| 13 | reading | Маніфести «Березоля» | 3 | 1 | ✅ |

**Summary:**
- Total activities: 13 (target: 3-9) ❌
- Unique types: 13 (minimum: 3) ✅
- Priority types used: 6/6 (authorial-intent, comparative-study, critical-analysis, essay-response, quiz, reading) ✅
- Required types used: 6/6 (essay-response, fill-in, group-sort, match-up, quiz, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in les-kurbas.yaml: Schema validation error at key '12': {'type': 'reading', 'title': 'Маніфести «Березоля»', 'resource': {'type': 'primary_source', 'url': 'https://elib.nlu.org.ua/', 'title': 'Лесь Курбас: Програма Березіль'}, 'tasks': ['Знайдіть у тексті маніфесту слова, що означають «рух» та «зміну».', 'Який відмінок використовується для означення мети театру?', 'Поясніть термін «інтелектуалізація» за текстом.']} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Життєпис' per template 'c1-biography-module-template.md'
  - FIX: Add '## Життєпис' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Внесок' per template 'c1-biography-module-template.md'
  - FIX: Add '## Внесок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Останні роки' per template 'c1-biography-module-template.md'
  - FIX: Add '## Останні роки' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Спадщина|Вплив' found: Вплив на світову театральну думку, Вплив на сучасний театральний процес
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).

## Recommendation
**📝 UPDATE** (severity 35/100)

- 5 violations (moderate)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2050/4000 (raw: 2292)
- **Activities:** ✅ 13/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 13/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 13 (target 3-9)
- **Immersion:** 🇺🇦 99.7% (target 95-100% (biography))
- **Richness:** ✅ 95% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 5 | 4 | 100% | 19% | 19.0% |
| engagement | 6 | 6 | 100% | 14% | 14.3% |
| quotes | 15 | 3 | 100% | 14% | 14.3% |
| cultural | 2 | 4 | 50% | 10% | 4.8% |
| visual | 9 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 12 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **95.1%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 102 | Included in Core |
| **Вступ** | ✅ | 256 | Included in Core |
| **Біографія** | ⚪️ | 1063 | Skipped |
| **Історичний контекст** | ✅ | 231 | Included in Core |
| **Порівняльний аналіз** | ✅ | 146 | Included in Core |
| **Підсумок** | ✅ | 150 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 102 | Skipped |