# Audit Report: M50 — mariya-zankovetska.md
**Level:** C1-BIO | **Module:** M50 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-04 11:41:42

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
| 1 | true-false | «Факти про життя актриси» | 8 | 5 | ✅ |
| 2 | critical-analysis | «Лінгвістичний аналіз прямої мови» | 1 | 1 | ✅ |
| 3 | critical-analysis | «Аналіз культурної стратегії театру корифеїв» | 1 | 1 | ✅ |
| 4 | essay-response | «Аналіз — Мистецтво та Громадянська Позиція» | 1 | 1 | ✅ |
| 5 | comparative-study | «Заньковецька та Сара Бернар — Тріумф Жінки» | 1 | 1 | ✅ |
| 6 | reading | «Первинні джерела — Листи про місію актриси» | 3 | 1 | ✅ |
| 7 | reading | «Наукова розвідка про театр корифеїв» | 3 | 1 | ✅ |
| 8 | essay-response | «Творча робота — Голос Нації» | 1 | 1 | ✅ |

**Summary:**
- Total activities: 8 (target: 3-9) ✅
- Unique types: 5 (minimum: 3) ✅
- Priority types used: 4/6 (comparative-study, critical-analysis, essay-response, reading) ✅
- Required types used: 2/2 (essay-response, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in mariya-zankovetska.yaml: Schema validation error at key '6': {'type': 'reading', 'title': '«Наукова розвідка про театр корифеїв»', 'resource': {'type': 'article', 'url': 'https://shron1.chytomo.com/teatr-koryfeiv-yak-tse-bulo-naspravdi/', 'title': '«Театр корифеїв — шлях від аматорства до професіоналізму»'}, 'tasks': ['«Як автор статті використовує біографічну лексику щодо Заньковецької?»', '«Знайдіть приклади академічного регістру в описі театральних реформ.»', '«Порівняйте оцінку внеску Заньковецької в статті з матеріалом модуля.»']} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Останні роки' per template 'c1-biography-module-template.md'
  - FIX: Add '## Останні роки' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple headers contain 'Спадщина': Спадщина, Вплив на сучасників
  - FIX: RENAME one header to NOT contain 'Спадщина'. Example: 'Агіографічна спадщина' → 'Житійна творчість' (removes the duplicate word).

## Recommendation
**📝 UPDATE** (severity 25/100)

- 3 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2002/4000 (raw: 2277)
- **Activities:** ✅ 8/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 5/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (8 activities)
- **Immersion:** 🇺🇦 100.0% (target 95-100% (biography))
- **Richness:** ✅ 95% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 4 | 4 | 100% | 19% | 19.0% |
| engagement | 7 | 6 | 100% | 14% | 14.3% |
| quotes | 10 | 3 | 100% | 14% | 14.3% |
| cultural | 2 | 4 | 50% | 10% | 4.8% |
| visual | 10 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 20 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 6 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **95.1%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 87 | Included in Core |
| **Вступ** | ✅ | 203 | Included in Core |
| **Життєпис** | ⚪️ | 174 | Skipped |
| **Внесок** | ⚪️ | 256 | Skipped |
| **Спадщина** | ⚪️ | 226 | Skipped |
| **Історичний контекст** | ✅ | 462 | Included in Core |
| **Порівняльний аналіз** | ✅ | 188 | Included in Core |
| **Есе** | ⚪️ | 45 | Skipped |
| **Критерії оцінювання** | ⚪️ | 0 | Skipped |
| **Зразок відповіді** | ⚪️ | 294 | Skipped |
| **Підсумок** | ✅ | 67 | Included in Core |
| **Activities** | ➖ | 0 | Excluded Type |
| **Потрібно більше практики?** | ⚪️ | 17 | Skipped |