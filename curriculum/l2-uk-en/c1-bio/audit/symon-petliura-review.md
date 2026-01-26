# Audit Report: M67 — symon-petliura.md
**Level:** C1 | **Module:** M67 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:31

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
| 1 | quiz | «Постать Головного Отамана» | 12 | 5 | ✅ |
| 2 | fill-in | «Політична та військова лексика» | 12 | 6 | ✅ |
| 3 | error-correction | «Граматика в історичному контексті» | 12 | 5 | ✅ |
| 4 | match-up | «Політична термінологія епохи» | 12 | 6 | ✅ |
| 5 | select | «Лінгвістичний аналіз промов Петлюри» | 5 | 5 | ✅ |
| 6 | true-false | «Історичні факти та радянські міфи» | 12 | 5 | ✅ |
| 7 | reading | «Аналіз військових наказів Отамана» | 3 | 1 | ✅ |
| 8 | reading | «Вбивство Петлюри: Паризький процес» | 3 | 1 | ✅ |
| 9 | essay-response | «Отаман нашої волі: Спадщина Петлюри» | 1 | 1 | ✅ |
| 10 | comparative-study | «Республіка чи Гетьманат: Петлюра та Скоропадський» | 1 | 1 | ✅ |
| 11 | critical-analysis | «Аналіз військово-політичної логіки Петлюри» | 1 | 1 | ✅ |
| 12 | unjumble | «Відновлення гасел визвольної боротьби» | 12 | 5 | ✅ |
| 13 | translate | «Політична та військова термінологія» | 12 | 5 | ✅ |
| 14 | mark-the-words | «Пошук державницьких термінів» | 10 | 5 | ✅ |
| 15 | true-false | «Політичні принципи Петлюри» | 12 | 5 | ✅ |

**Summary:**
- Total activities: 15 (target: 3-9) ❌
- Unique types: 13 (minimum: 3) ✅
- Priority types used: 5/6 (comparative-study, critical-analysis, essay-response, quiz, reading) ✅
- Required types used: 5/6 (essay-response, fill-in, match-up, quiz, reading) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in symon-petliura.yaml: Schema validation error at key '7': {'type': 'reading', 'title': '«Вбивство Петлюри: Паризький процес»', 'resource': {'type': 'article', 'url': 'https://www.radiosvoboda.org/a/symon-petliura-vbyvstvo-sud/27756854.html', 'title': '«Вбивство Петлюри: Як радянська пропаганда перетворила вбивцю на героя»'}, 'tasks': ['«Доведіть, що процес над Шварцбардом був спецоперацією спецслужб.»', '«Які аргументи захисту вбивці використовувалися в суді?»', '«Чому європейська преса зайняла антиукраїнську позицію?»']} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Останні роки' per template 'c1-biography-module-template.md'
  - FIX: Add '## Останні роки' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Спадщина|Вплив' found: Спадщина, Спадщина Отамана
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).

## Recommendation
**📝 UPDATE** (severity 5/100)

- 3 violations (minor)

## Gates
- **Words:** ❌ 2037/4000 (raw: 2264)
- **Activities:** ✅ 15/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 13/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 15 (target 3-9)
- **Immersion:** 🇺🇦 100.0% (target 95-100% (biography))
- **Richness:** ✅ 99% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 6 | 4 | 100% | 19% | 19.0% |
| engagement | 7 | 6 | 100% | 14% | 14.3% |
| quotes | 6 | 3 | 100% | 14% | 14.3% |
| cultural | 5 | 4 | 100% | 10% | 9.5% |
| visual | 6 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 12 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 77 | Included in Core |
| **Вступ** | ✅ | 234 | Included in Core |
| **Життєпис** | ⚪️ | 844 | Skipped |
| **Внесок** | ⚪️ | 170 | Skipped |
| **Спадщина** | ⚪️ | 415 | Skipped |
| **Порівняльний аналіз** | ✅ | 126 | Included in Core |
| **Підсумок** | ✅ | 74 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 97 | Skipped |
| **Вправи** | ⚪️ | 0 | Skipped |
| **Словник** | ⚪️ | 0 | Skipped |