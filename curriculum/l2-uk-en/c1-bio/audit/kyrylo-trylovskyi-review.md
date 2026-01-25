# Audit Report: M51 — kyrylo-trylovskyi.md
**Level:** C1 | **Module:** M51 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-25 19:27:12

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
| 1 | quiz | «Організаційна стратегія та витоки руху» | 5 | 5 | ✅ |
| 2 | match-up | «Хронологія та ключові віхи діяльності» | 8 | 6 | ✅ |
| 3 | fill-in | «Лексика та ідеологія січового руху» | 6 | 6 | ✅ |
| 4 | true-false | «Діяльність, вплив та спадщина» | 5 | 5 | ✅ |
| 5 | select | «Політичні ролі та досягнення» | 5 | 5 | ✅ |
| 6 | error-correction | «Аналіз біографічного наративу» | 5 | 5 | ✅ |
| 7 | group-sort | «Атрибути та принципи 'Січі'» | 12 | 1 | ✅ |
| 8 | unjumble | «Програмні висловлювання лідера» | 5 | 5 | ✅ |
| 9 | quiz | «Військове та політичне значення» | 5 | 5 | ✅ |
| 10 | essay-response | «Феномен 'легальної армії' Трильовського» | 1 | 1 | ✅ |
| 11 | critical-analysis | «Аналіз ідеологічного перелому» | 1 | 1 | ✅ |
| 12 | comparative-study | «Дві стратегії одного визволення» | 1 | 1 | ✅ |

**Summary:**
- Total activities: 12 (target: 3-9) ❌
- Unique types: 11 (minimum: 3) ✅
- Priority types used: 4/6 (comparative-study, critical-analysis, essay-response, quiz) ✅
- Required types used: 5/6 (essay-response, fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in kyrylo-trylovskyi.yaml: Schema validation error at key '7': {'type': 'unjumble', 'title': '«Програмні висловлювання лідера»', 'items': [{'words': ['«Ми»', '«хочемо»', '«бути»', '«свідомим»', '«народом»', '«а»', '«не»', '«просто»', '«племенем»', '«ми»', '«прагнемо»', '«мати»', '«свою»', '«волю»', '«і»', '«власну»', '«державу»'], 'answer': '«Ми хочемо бути свідомим народом а не просто племенем ми прагнемо мати свою волю і власну державу»'}, {'words': ['«Тільки»', '«сильна»', '«та»', '«організована»', '«нація»', '«може»', '«здобути»', '«собі»', '«законне»', '«право»', '«на»', '«гідне»', '«життя»', '«під»', '«цим»', '«сонцем»'], 'answer': '«Тільки сильна та організована нація може здобути собі законне право на гідне життя під цим сонцем»'}, {'words': ['«Січ»', '«це»', '«справжня»', '«школа»', '«де»', '«кується»', '«нова»', '«українська»', '«людина»', '«свідома»', '«своєї»', '«сили»', '«та»', '«дисциплінована»', '«у»', '«діях»'], 'answer': '«Січ це справжня школа де кується нова українська людина свідома своєї сили та дисциплінована у діях»'}, {'words': ['«Не»', '«плакати»', '«нам»', '«треба»', '«над»', '«своєю»', '«гіркою»', '«долею»', '«а»', '«щоденно»', '«гартувати»', '«власні»', "«м'язи»", '«і»', '«незламний»', '«національний»', '«дух»'], 'answer': "«Не плакати нам треба над своєю гіркою долею а щоденно гартувати власні м'язи і незламний національний дух»"}, {'words': ['«Кожен»', '«свідомий»', '«українець»', '«має»', '«відчути»', '«себе»', '«частиною»', '«єдиної»', '«та»', '«могутньої»', '«національної»', '«сили»', '«яка»', '«здатна»', '«змінити»', '«світ»'], 'answer': '«Кожен свідомий українець має відчути себе частиною єдиної та могутньої національної сили яка здатна змінити світ»'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Життєпис' per template 'c1-biography-module-template.md'
  - FIX: Add '## Життєпис' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Внесок' per template 'c1-biography-module-template.md'
  - FIX: Add '## Внесок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Спадщина|Вплив' found: Спадщина в діаспорі: Січовий вогонь за океаном, Вплив на сучасників: Харизма лідера
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Підсумок' per template 'c1-biography-module-template.md'
  - FIX: Add '## Підсумок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 35/100)

- 6 violations (moderate)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2090/4000 (raw: 2327)
- **Activities:** ✅ 12/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 11/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 11/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 12 (target 3-9)
- **Immersion:** 🇺🇦 99.9% (target 95-100% (biography))
- **Richness:** ✅ 97% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 5 | 4 | 100% | 19% | 19.0% |
| engagement | 11 | 6 | 100% | 14% | 14.3% |
| quotes | 7 | 3 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 7 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 1.00 | - | 100% | 5% | 4.8% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 10 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.6%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 95 | Included in Core |
| **Вступ** | ✅ | 299 | Included in Core |
| **Біографія** | ⚪️ | 1156 | Skipped |
| **Історичний контекст** | ✅ | 245 | Included in Core |
| **Порівняльний аналіз** | ✅ | 74 | Included in Core |
| **Критичне мислення** | ⚪️ | 160 | Skipped |
| **Summary** | ✅ | 61 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |