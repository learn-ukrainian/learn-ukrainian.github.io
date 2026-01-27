# Audit Report: M55 — mykola-vasylenko.md

**Level:** C1 | **Module:** M55 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:24

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
| 1 | quiz | «Наукова та політична діяльність» | 5 | 5 | ✅ |
| 2 | match-up | «Хронологія життя» | 8 | 6 | ✅ |
| 3 | fill-in | «Лексика державотворення» | 6 | 6 | ✅ |
| 4 | true-false | «Факти та міфи» | 5 | 5 | ✅ |
| 5 | select | «Наукові інтереси та досягнення» | 5 | 5 | ✅ |
| 6 | error-correction | «Граматика біографічного опису» | 5 | 5 | ✅ |
| 7 | group-sort | «Етапи діяльності» | 12 | 1 | ✅ |
| 8 | unjumble | «Цитати та принципи» | 5 | 5 | ✅ |
| 9 | essay-response | «Василенко і Гетьманат» | 1 | 1 | ✅ |
| 10 | critical-analysis | «Репресії проти інтелігенції» | 1 | 1 | ✅ |
| 11 | comparative-study | «Василенко та Грушевський» | 1 | 1 | ✅ |
| 12 | quiz | «Спадщина та вшанування пам'яті» | 5 | 5 | ✅ |

**Summary:**
- Total activities: 12 (target: 3-9) ❌
- Unique types: 11 (minimum: 3) ✅
- Priority types used: 4/6 (comparative-study, critical-analysis, essay-response, quiz) ✅
- Required types used: 5/6 (essay-response, fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[YAML_SCHEMA_VIOLATION]** Schema error in mykola-vasylenko.yaml: Schema validation error at key '7': {'type': 'unjumble', 'title': '«Цитати та принципи»', 'items': [{'words': ['«Справжня»', '«наука»', '«повинна»', '«бути»', '«поза»', '«політикою»', '«але»', '«вона»', "«зобов'язана»", '«вірно»', '«служити»', '«своєму»', '«рідному»', '«народу»', '«та»', '«сприяти»', '«його»', '«розвитку»'], 'answer': "«Справжня наука повинна бути поза політикою але вона зобов'язана вірно служити своєму рідному народу та сприяти його розвитку»"}, {'words': ['«Створення»', '«власної»', '«академії»', '«наук»', '«стало»', '«найважливішим»', '«історичним»', '«кроком»', '«для»', '«культурного»', '«та»', '«політичного»', '«самоствердження»', '«модерної»', '«української»', '«нації»'], 'answer': '«Створення власної академії наук стало найважливішим історичним кроком для культурного та політичного самоствердження модерної української нації»'}, {'words': ['«Тільки»', '«глибоке»', '«і»', "«об'єктивне»", '«вивчення»', '«минулого»', '«дає»', '«нам»', '«надійний»', '«ключ»', '«до»', '«розуміння»', '«складних»', '«сучасних»', '«процесів»', '«державотворення»'], 'answer': "«Тільки глибоке і об'єктивне вивчення минулого дає нам надійний ключ до розуміння складних сучасних процесів державотворення»"}, {'words': ['«Микола»', '«Василенко»', '«залишився»', '«вірним»', '«своїм»', '«високим»', '«моральним»', '«принципам»', '«навіть»', '«під»', '«тиском»', '«надзвичайно»', '«жорстоких»', '«сталінських»', '«репресій»'], 'answer': '«Микола Василенко залишився вірним своїм високим моральним принципам навіть під тиском надзвичайно жорстоких сталінських репресій»'}, {'words': ['«Історія»', '«національного»', '«права»', '«дозволяє»', '«зрозуміти»', '«як»', '«саме»', '«формувалася»', '«унікальна»', '«політична»', '«культура»', '«українського»', '«народу»', '«протягом»', '«багатьох»', '«століть»'], 'answer': '«Історія національного права дозволяє зрозуміти як саме формувалася унікальна політична культура українського народу протягом багатьох століть»'}]} is not valid under any of the given schemas
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

- **Words:** ❌ 1965/4000 (raw: 2226)
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
| primary_sources | 11 | 4 | 100% | 19% | 19.0% |
| engagement | 7 | 6 | 100% | 14% | 14.3% |
| quotes | 11 | 3 | 100% | 14% | 14.3% |
| cultural | 4 | 4 | 100% | 10% | 9.5% |
| visual | 6 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 13 | 2 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 9 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 114 | Included in Core |
| **Вступ** | ✅ | 198 | Included in Core |
| **Біографія** | ⚪️ | 1014 | Skipped |
| **Історичний контекст** | ✅ | 202 | Included in Core |
| **Порівняльний аналіз** | ✅ | 152 | Included in Core |
| **Критичне мислення** | ⚪️ | 136 | Skipped |
| **Summary** | ✅ | 149 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |
