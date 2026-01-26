# Audit Report: M58 — liudmyla-starytska.md
**Level:** C1 | **Module:** M58 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:26

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
| 1 | quiz | «Рід та походження» | 5 | 5 | ✅ |
| 2 | match-up | «Етапи життя та творчості» | 8 | 6 | ✅ |
| 3 | fill-in | «Лексика театрального та політичного життя» | 6 | 6 | ✅ |
| 4 | true-false | «Факти про процес СВУ» | 5 | 5 | ✅ |
| 5 | select | «Літературна та громадська діяльність» | 5 | 5 | ✅ |
| 6 | error-correction | «Граматика трагічного наративу» | 5 | 5 | ✅ |
| 7 | group-sort | «Родина та оточення» | 12 | 1 | ✅ |
| 8 | unjumble | «Думки про долю України» | 5 | 5 | ✅ |
| 9 | essay-response | «Трагедія роду Старицьких» | 1 | 1 | ✅ |
| 10 | critical-analysis | Процес СВУ: Театр абсурду | 1 | 1 | ✅ |
| 11 | comparative-study | «Дві поетеси, дві долі» | 1 | 1 | ✅ |
| 12 | quiz | «Пам'ять та вшанування» | 5 | 5 | ✅ |

**Summary:**
- Total activities: 12 (target: 3-9) ❌
- Unique types: 11 (minimum: 3) ✅
- Priority types used: 4/6 (comparative-study, critical-analysis, essay-response, quiz) ✅
- Required types used: 5/6 (essay-response, fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in liudmyla-starytska.yaml: Schema validation error at key '7': {'type': 'unjumble', 'title': '«Думки про долю України»', 'items': [{'words': ['«Ми»', '«завжди»', '«повинні»', '«стояти»', '«на»', '«сторожі»', '«нашої»', '«національної»', '«культури»', '«як»', '«єдиного»', '«порятунку»', '«від»', '«повної»', '«духовної»', '«смерті»'], 'answer': '«Ми завжди повинні стояти на сторожі нашої національної культури як єдиного порятунку від повної духовної смерті»'}, {'words': ['«Історія»', '«нашого»', '«великого»', '«народу»', '«це»', '«безперервний»', '«ланцюг»', '«боротьби»', '«за»', '«природне»', '«право»', '«бути»', '«собою»', '«на»', '«власній»', '«землі»'], 'answer': '«Історія нашого великого народу це безперервний ланцюг боротьби за природне право бути собою на власній землі»'}, {'words': ['«Театр»', '«завжди»', '«був»', '«для»', '«українців»', '«не»', '«просто»', '«розвагою»', '«а»', '«справжньою»', '«школою»', '«патріотизму»', '«та»', '«живого»', '«рідного»', '«слова»'], 'answer': '«Театр завжди був для українців не просто розвагою а справжньою школою патріотизму та живого рідного слова»'}, {'words': ['«Наша»', '«інтелігенція»', '«має»', '«великий»', '«борг»', '«перед»', '«народом»', '«який»', '«вона»', '«мусить»', '«сплатити»', '«своєю»', '«чесною»', '«працею»', '«та»', '«жертовністю»'], 'answer': '«Наша інтелігенція має великий борг перед народом який вона мусить сплатити своєю чесною працею та жертовністю»'}, {'words': ['«Навіть»', '«у»', '«найтемніші»', '«часи»', '«репресій»', '«ми»', '«не»', '«маємо»', '«права»', '«втрачати»', '«надію»', '«на»', '«відродження»', '«нашої»', '«вільної»', '«держави»'], 'answer': '«Навіть у найтемніші часи репресій ми не маємо права втрачати надію на відродження нашої вільної держави»'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Життєпис' per template 'c1-biography-module-template.md'
  - FIX: Add '## Життєпис' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Внесок' per template 'c1-biography-module-template.md'
  - FIX: Add '## Внесок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Спадщина' per template 'c1-biography-module-template.md'
  - FIX: Add '## Спадщина' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Підсумок' per template 'c1-biography-module-template.md'
  - FIX: Add '## Підсумок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 35/100)

- 6 violations (moderate)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2003/4000 (raw: 2232)
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
| primary_sources | 5 | 4 | 100% | 19% | 19.0% |
| engagement | 7 | 6 | 100% | 14% | 14.3% |
| quotes | 9 | 3 | 100% | 14% | 14.3% |
| cultural | 7 | 4 | 100% | 10% | 9.5% |
| visual | 6 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 11 | 2 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 13 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.9%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 89 | Included in Core |
| **Вступ** | ✅ | 177 | Included in Core |
| **Біографія** | ⚪️ | 1142 | Skipped |
| **Історичний контекст** | ✅ | 257 | Included in Core |
| **Порівняльний аналіз** | ✅ | 60 | Included in Core |
| **Критичне мислення** | ⚪️ | 142 | Skipped |
| **Summary** | ✅ | 136 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |