# Audit Report: M54 — sofiya-okunevska.md
**Level:** C1 | **Module:** M54 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:23

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
| 1 | quiz | «Освіта, перешкоди та початок наукового шляху» | 5 | 5 | ✅ |
| 2 | match-up | «Хронологія життя та професійних досягнень» | 8 | 6 | ✅ |
| 3 | fill-in | «Професійна термінологія та науковий внесок» | 6 | 6 | ✅ |
| 4 | true-false | «Факти, міфи та суспільна діяльність» | 5 | 5 | ✅ |
| 5 | select | «Громадська роль та соратники» | 5 | 5 | ✅ |
| 6 | error-correction | «Граматика та історичний стиль» | 5 | 5 | ✅ |
| 7 | group-sort | «Сфери впливу та атрибути діяльності» | 12 | 1 | ✅ |
| 8 | unjumble | «Принципи та цитати лікарки» | 5 | 5 | ✅ |
| 9 | essay-response | «Інтелектуальний подвиг Софії Окуневської» | 1 | 1 | ✅ |
| 10 | critical-analysis | «Аналіз етичної позиції лікарки» | 1 | 1 | ✅ |
| 11 | comparative-study | «Порівняльна характеристика першопрохідців» | 1 | 1 | ✅ |
| 12 | quiz | «Спадщина та пам'ять у сучасній Україні» | 5 | 5 | ✅ |

**Summary:**
- Total activities: 12 (target: 3-9) ❌
- Unique types: 11 (minimum: 3) ✅
- Priority types used: 4/6 (comparative-study, critical-analysis, essay-response, quiz) ✅
- Required types used: 5/6 (essay-response, fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in sofiya-okunevska.yaml: Schema validation error at key '7': {'type': 'unjumble', 'title': '«Принципи та цитати лікарки»', 'items': [{'words': ['«Медицина»', '«для»', '«сучасної»', '«жінки»', '«це»', '«не»', '«лише»', '«фах»', '«а»', '«вища»', '«форма»', '«важливого»', '«соціального»', '«служіння»', '«своєму»', '«народу»'], 'answer': '«Медицина для сучасної жінки це не лише фах а вища форма важливого соціального служіння своєму народу»'}, {'words': ['«Знання»', '«це»', '«єдина»', '«зброя»', '«яку»', '«ми»', '«маємо»', '«використовувати»', '«для»', '«визволення»', '«нашого»', '«народу»', '«від»', '«темряви»', '«і»', '«хвороб»'], 'answer': '«Знання це єдина зброя яку ми маємо використовувати для визволення нашого народу від темряви і хвороб»'}, {'words': ['«Якщо»', '«ми»', '«не»', '«навчимо»', '«жінку»', '«бути»', '«самостійною»', '«ми»', '«ніколи»', '«не»', '«збудуємо»', '«здорову»', '«та»', '«сильну»', '«європейську»', '«націю»'], 'answer': '«Якщо ми не навчимо жінку бути самостійною ми ніколи не збудуємо здорову та сильну європейську націю»'}, {'words': ['«Ми»', '«маємо»', '«йти»', '«туди»', '«де»', '«сьогодні»', '«є»', '«найбільше»', '«страждання»', '«і»', '«нести»', '«людям»', '«не»', '«лише»', '«ліки»', '«а»', '«й»', '«надію»'], 'answer': '«Ми маємо йти туди де сьогодні є найбільше страждання і нести людям не лише ліки а й надію»'}, {'words': ['«Професійний»', '«успіх»', '«української»', '«жінки»', '«є»', '«найкращим»', '«доказом»', '«життєздатності»', '«нашої»', '«культури»', '«перед»', '«обличчям»', '«усього»', '«цивілізованого»', '«світу»'], 'answer': '«Професійний успіх української жінки є найкращим доказом життєздатності нашої культури перед обличчям усього цивілізованого світу»'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Життєпис' per template 'c1-biography-module-template.md'
  - FIX: Add '## Життєпис' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Внесок' per template 'c1-biography-module-template.md'
  - FIX: Add '## Внесок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Підсумок' per template 'c1-biography-module-template.md'
  - FIX: Add '## Підсумок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 35/100)

- 5 violations (moderate)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2162/4000 (raw: 2419)
- **Activities:** ✅ 12/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 11/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 12 (target 3-9)
- **Immersion:** 🇺🇦 99.9% (target 95-100% (biography))
- **Richness:** ✅ 99% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 4 | 4 | 100% | 19% | 19.0% |
| engagement | 7 | 6 | 100% | 14% | 14.3% |
| quotes | 6 | 3 | 100% | 14% | 14.3% |
| cultural | 5 | 4 | 100% | 10% | 9.5% |
| visual | 4 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 8 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.9%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 90 | Included in Core |
| **Вступ** | ✅ | 306 | Included in Core |
| **Біографія** | ⚪️ | 1165 | Skipped |
| **Історичний контекст** | ✅ | 255 | Included in Core |
| **Порівняльний аналіз** | ✅ | 92 | Included in Core |
| **Критичне мислення** | ⚪️ | 174 | Skipped |
| **Summary** | ✅ | 80 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |