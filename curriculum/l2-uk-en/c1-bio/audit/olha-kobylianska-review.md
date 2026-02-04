# Audit Report: M57 — olha-kobylianska.md
**Level:** C1-BIO | **Module:** M57 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-04 11:41:46

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
| 1 | true-false | Правда про Ольгу Кобилянську | 8 | 5 | ✅ |
| 2 | comparative-study | Кобилянська та Леся Українка - Обличчя модерну | 1 | 1 | ✅ |
| 3 | reading | Аналіз «музичної» прози Кобилянської | 3 | 1 | ✅ |
| 4 | reading | Епістолярний діалог геніїв | 3 | 1 | ✅ |
| 5 | authorial-intent | Наміри авторки в образі «Гірської орлиці» | 1 | 1 | ✅ |
| 6 | essay-response | «Ольга Кобилянська: Від провінційної дівчини до ікони модерну» | 1 | 1 | ✅ |

**Summary:**
- Total activities: 6 (target: 3-9) ✅
- Unique types: 5 (minimum: 3) ✅
- Priority types used: 4/6 (authorial-intent, comparative-study, essay-response, reading) ✅
- Required types used: 2/2 (essay-response, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in olha-kobylianska.yaml: Schema validation error at key '3': {'type': 'reading', 'title': 'Епістолярний діалог геніїв', 'resource': {'type': 'primary_source', 'url': 'https://shron1.chtyvo.org.ua/Ukrainka_Lesia/Lysty_do_Olhy_Kobylianskoi.pdf', 'title': '«Листи Лесі Українки до Ольги Кобилянської»'}, 'tasks': ['«Який регістр спілкування (інтимний, дружній, офіційний) домінує у цих листах? Наведіть приклади пестливих слів та звертань.»', '«Які творчі поради дає Леся Українка своїй подрузі щодо модернізації стилю? Випишіть ключові фрази.»', '«Знайдіть у листах згадки про європейських письменників, якими захоплювалися обидві авторки.»']} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Життєпис' per template 'c1-biography-module-template.md'
  - FIX: Add '## Життєпис' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Внесок' per template 'c1-biography-module-template.md'
  - FIX: Add '## Внесок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple headers contain 'Спадщина': Останні роки та спадщина: Гірська самота, Вплив на сучасників
  - FIX: RENAME one header to NOT contain 'Спадщина'. Example: 'Агіографічна спадщина' → 'Житійна творчість' (removes the duplicate word).
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Підсумок' per template 'c1-biography-module-template.md'
  - FIX: Add '## Підсумок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 35/100)

- 6 violations (moderate)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 1983/4000 (raw: 2175)
- **Activities:** ✅ 6/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 5/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (6 activities)
- **Immersion:** 🇺🇦 99.7% (target 95-100% (biography))
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
| quotes | 4 | 3 | 100% | 14% | 14.3% |
| cultural | 4 | 4 | 100% | 10% | 9.5% |
| visual | 5 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 27 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 7 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 76 | Included in Core |
| **Вступ** | ✅ | 209 | Included in Core |
| **Біографія** | ⚪️ | 1131 | Skipped |
| **Історичний контекст** | ✅ | 295 | Included in Core |
| **Порівняльний аналіз** | ✅ | 136 | Included in Core |
| **Summary** | ✅ | 136 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |