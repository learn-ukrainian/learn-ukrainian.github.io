# Audit Report: M53 — ivan-lypa.md

**Level:** C1 | **Module:** M53 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
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
| 1 | quiz | «Витоки українського самостійництва та 'Братство тарасівців'» | 5 | 5 | ✅ |
| 2 | match-up | «Ключові віхи біографії та державної служби» | 8 | 6 | ✅ |
| 3 | fill-in | «Політична та літературна термінологія» | 6 | 6 | ✅ |
| 4 | true-false | «Державна діяльність та ідеологічна спадщина» | 5 | 5 | ✅ |
| 5 | select | «Діяльність та оточення діяча» | 5 | 5 | ✅ |
| 6 | error-correction | «Граматика та історичний наратив» | 5 | 5 | ✅ |
| 7 | group-sort | «Діяльність в Одесі та Державна служба» | 12 | 1 | ✅ |
| 8 | unjumble | «Програмні тези самостійника» | 5 | 5 | ✅ |
| 9 | quiz | «Літературна та ідейна спадщина» | 5 | 5 | ✅ |
| 10 | essay-response | «Постать Івана Липи як міст між епохами» | 1 | 1 | ✅ |
| 11 | critical-analysis | «Аналіз метафоричної мови лідера» | 1 | 1 | ✅ |
| 12 | comparative-study | «Липа та Винниченко — Два бачення України» | 1 | 1 | ✅ |

**Summary:**
- Total activities: 12 (target: 3-9) ❌
- Unique types: 11 (minimum: 3) ✅
- Priority types used: 4/6 (comparative-study, critical-analysis, essay-response, quiz) ✅
- Required types used: 5/6 (essay-response, fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[YAML_SCHEMA_VIOLATION]** Schema error in ivan-lypa.yaml: Schema validation error at key '7': {'type': 'unjumble', 'title': '«Програмні тези самостійника»', 'items': [{'words': ['«Самостійність»', '«це»', '«не»', '«лише»', '«зовнішній»', '«політичний»', '«статус»', '«це»', '«насамперед»', '«стан»', '«душі»', '«справді»', '«вільної»', '«та»', '«відповідальної»', '«людини»'], 'answer': '«Самостійність це не лише зовнішній політичний статус це насамперед стан душі справді вільної та відповідальної людини»'}, {'words': ['«Ми»', '«маємо»', '«нарешті»', '«науково»', '«та»', '«політично»', '«обґрунтувати»', '«абсолютну»', '«необхідність»', '«повної»', '«незалежності»', '«нашої»', '«України»', '«від»', '«будь-яких»', '«імперій»'], 'answer': '«Ми маємо нарешті науково та політично обґрунтувати абсолютну необхідність повної незалежності нашої України від будь-яких імперій»'}, {'words': ['«Наша»', '«головна»', '«зброя»', '«у»', '«цій»', '«важкій»', '«боротьбі»', '«це»', '«рідне»', '«слово»', '«чітка»', '«організація»', '«та»', '«незламна»', '«віра»', '«у»', '«свою»', '«правоту»'], 'answer': '«Наша головна зброя у цій важкій боротьбі це рідне слово чітка організація та незламна віра у свою правоту»'}, {'words': ['«Кожен»', '«свідомий»', '«українець»', '«має»', '«постійно»', '«відчувати»', '«себе»', '«частиною»', '«єдиного»', '«державного»', '«тіла»', '«а»', '«не»', '«просто»', '«мешканцем»', '«чужої»', '«губернії»'], 'answer': '«Кожен свідомий українець має постійно відчувати себе частиною єдиного державного тіла а не просто мешканцем чужої губернії»'}, {'words': ['«Без»', '«власної»', '«незалежної»', '«держави»', '«наш»', '«талановитий»', '«народ»', '«приречений»', '«бути»', '«лише»', '«пасивним»', '«добривом»', '«для»', '«розквіту»', '«інших»', '«сусідніх»', '«імперій»'], 'answer': '«Без власної незалежної держави наш талановитий народ приречений бути лише пасивним добривом для розквіту інших сусідніх імперій»'}]} is not valid under any of the given schemas
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
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation

**📝 UPDATE** (severity 35/100)

- 6 violations (moderate)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates

- **Words:** ❌ 1977/4000 (raw: 2244)
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
- **Immersion:** 🇺🇦 99.8% (target 95-100% (biography))
- **Richness:** ✅ 100% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details

**Score:** 100% (minimum: 95%)
**Module Type:** biography

### Score Breakdown

| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 5 | 4 | 100% | 19% | 19.0% |
| engagement | 7 | 6 | 100% | 14% | 14.3% |
| quotes | 12 | 3 | 100% | 14% | 14.3% |
| cultural | 6 | 4 | 100% | 10% | 9.5% |
| visual | 4 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 1.00 | - | 100% | 5% | 4.8% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 9 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 91 | Included in Core |
| **Вступ** | ✅ | 302 | Included in Core |
| **Біографія** | ⚪️ | 1030 | Skipped |
| **Історичний контекст** | ✅ | 210 | Included in Core |
| **Порівняльний аналіз** | ✅ | 89 | Included in Core |
| **Критичне мислення** | ⚪️ | 170 | Skipped |
| **Summary** | ✅ | 85 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |
