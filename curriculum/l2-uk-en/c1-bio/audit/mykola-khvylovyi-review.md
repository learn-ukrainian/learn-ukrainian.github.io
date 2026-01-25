# Audit Report: M84 — mykola-khvylovyi.md
**Level:** C1 | **Module:** M84 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-25 19:27:31

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
| 1 | quiz | Розуміння тексту: Життя Миколи Хвильового | 5 | 5 | ✅ |
| 2 | fill-in | Лексика: Література та Політика | 6 | 6 | ✅ |
| 3 | error-correction | Граматика: Біографічні факти | 5 | 5 | ✅ |
| 4 | match-up | Літературний словник | 8 | 6 | ✅ |
| 5 | select | Лінгвістичний аналіз памфлету | 5 | 5 | ✅ |
| 6 | group-sort | Життя та творчість Хвильового | 12 | 1 | ✅ |
| 7 | true-false | Міфи та правда про Хвильового | 5 | 5 | ✅ |
| 8 | authorial-intent | Намір автора: Передсмертна записка | 1 | 1 | ✅ |
| 9 | essay-response | Аналіз трагедії: Ідеаліст у пастці | 1 | 1 | ✅ |
| 10 | comparative-study | Порівняння: Хвильовий та Маяковський | 1 | 1 | ✅ |
| 11 | critical-analysis | Аналіз будинку «Слово» | 1 | 1 | ✅ |
| 12 | translate | Переклад термінів: Література та Історія | 5 | 5 | ✅ |
| 13 | reading | Новела «Я (Романтика)» | 3 | 1 | ✅ |

**Summary:**
- Total activities: 13 (target: 3-9) ❌
- Unique types: 13 (minimum: 3) ✅
- Priority types used: 6/6 (authorial-intent, comparative-study, critical-analysis, essay-response, quiz, reading) ✅
- Required types used: 6/6 (essay-response, fill-in, group-sort, match-up, quiz, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in mykola-khvylovyi.yaml: Schema validation error at key '12': {'type': 'reading', 'title': 'Новела «Я (Романтика)»', 'resource': {'type': 'primary_source', 'url': 'https://ukrlib.com.ua/', 'title': 'Микола Хвильовий: Я (Романтика)'}, 'tasks': ['Знайдіть у тексті опис внутрішнього конфлікту чекіста.', 'Як автор використовує слово "запах"?', 'Які символи революції присутні в новелі?']} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Життєпис' per template 'c1-biography-module-template.md'
  - FIX: Add '## Життєпис' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Внесок' per template 'c1-biography-module-template.md'
  - FIX: Add '## Внесок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Останні роки' per template 'c1-biography-module-template.md'
  - FIX: Add '## Останні роки' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md

## Recommendation
**📝 UPDATE** (severity 35/100)

- 4 violations (moderate)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2236/4000 (raw: 2496)
- **Activities:** ✅ 13/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 13/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 13 (target 3-9)
- **Immersion:** 🇺🇦 100.0% (target 95-100% (biography))
- **Richness:** ❌ 92% < 95% min (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 92% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 7 | 4 | 100% | 19% | 19.0% |
| engagement | 9 | 6 | 100% | 14% | 14.3% |
| quotes | 13 | 3 | 100% | 14% | 14.3% |
| cultural | 1 | 4 | 25% | 10% | 2.4% |
| visual | 12 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 28 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **92.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 106 | Included in Core |
| **Вступ** | ✅ | 228 | Included in Core |
| **Біографія** | ⚪️ | 663 | Skipped |
| **Сучасний контекст** | ✅ | 230 | Included in Core |
| **Історичний контекст** | ✅ | 382 | Included in Core |
| **Порівняльний аналіз** | ✅ | 184 | Included in Core |
| **Підсумок** | ✅ | 129 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 203 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 111 | Skipped |