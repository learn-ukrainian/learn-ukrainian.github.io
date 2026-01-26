# Audit Report: M127 — oleksandra-matviichuk.md
**Level:** C1 | **Module:** M127 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:57:20

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
| 1 | quiz | Розуміння біографії та діяльності | 5 | 5 | ✅ |
| 2 | fill-in | Біографічна та юридична лексика | 6 | 6 | ✅ |
| 3 | match-up | Термінологія прав людини та правосуддя | 8 | 6 | ✅ |
| 4 | error-correction | Граматика в біографічному та юридичному контекстах | 6 | 5 | ✅ |
| 5 | select | Лінгвістичний аналіз Нобелівської промови | 5 | 5 | ✅ |
| 6 | fill-in | Контекстуальна правозахисна лексика | 6 | 6 | ✅ |
| 7 | quiz | Аналіз впливу та історичного контексту | 5 | 5 | ✅ |
| 8 | match-up | Порівняльний аналіз правозахисних парадигм (Матвійчук vs Лук'яненко) | 8 | 6 | ✅ |
| 9 | quiz | Деколонізація та суб'єктність України | 5 | 5 | ✅ |
| 10 | true-false | Правда чи міф: Діяльність Олександри Матвійчук | 6 | 5 | ✅ |
| 11 | comparative-study | Порівняльний аналіз правозахисних парадигм | 1 | 1 | ✅ |
| 12 | essay-response | Письмове завдання: Роль особистості в історії правозахисту | 1 | 1 | ✅ |

**Summary:**
- Total activities: 12 (target: 3-9) ❌
- Unique types: 8 (minimum: 3) ✅
- Priority types used: 3/6 (comparative-study, essay-response, quiz) ✅
- Required types used: 4/6 (essay-response, fill-in, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in oleksandra-matviichuk.yaml: Schema validation error at key '9': {'type': 'true-false', 'title': 'Правда чи міф: Діяльність Олександри Матвійчук', 'items': [{'statement': 'Олександра Матвійчук стала першою в історії України жінкою, яка виступила з нобелівською лекцією.', 'correct': True, 'explanation': 'Це підтверджується текстом модуля як історичний факт.'}, {'statement': 'Ініціатива «Євромайдан SOS» була створена для фінансової підтримки політичних партій.', 'correct': False, 'explanation': 'Ініціатива була створена для надання юридичної допомоги переслідуваним учасникам протестів.'}, {'statement': 'Центр громадянських свобод був заснований у 2022 році відразу після початку повномасштабної війни.', 'correct': False, 'explanation': 'ЦГС був заснований значно раніше, у 2007 році.'}, {'statement': "Кампанія #LetMyPeopleGo фокусувалася на звільненні українських політв'язнів з російського полону.", 'correct': True, 'explanation': 'Це була одна з ключових міжнародних адвокаційних кампаній ЦГС.'}, {'statement': 'Матвійчук вважає, що правосуддя має здійснюватися виключно після повного закінчення бойових дій.', 'correct': False, 'explanation': 'Навпаки, вона наполягає на документуванні та покаранні злочинців під час війни.'}, {'statement': "Образ Матвійчук у світі часто називають прикладом «м'якої сили» України.", 'correct': True, 'explanation': 'Текст прямо вказує на це як на форму інтелектуального та правового впливу.'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[FORBIDDEN_HEADER_TONE]** Header '## Сучасний етап' is inappropriate for a deceased person. Use '## Останні роки' instead.
  - FIX: Rename '## Сучасний етап' to '## Останні роки' to maintain correct biographical tone.
- ❌ **[FORBIDDEN_HEADER_TONE]** Header '## Вплив' is inappropriate for a deceased person. Use '## Спадщина' instead.
  - FIX: Rename '## Вплив' to '## Спадщина' to maintain correct biographical tone.
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Спадщина|Вплив' found: Вплив, Вплив на сучасників та глобальний рух
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).

## Recommendation
**📝 UPDATE** (severity 35/100)

- 4 violations (moderate)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2213/4000 (raw: 2401)
- **Activities:** ✅ 12/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 8/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 12 (target 3-9)
- **Immersion:** 🇺🇦 95.7% (target 95-100% (biography))
- **Richness:** ✅ 97% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 15 | 4 | 100% | 19% | 19.0% |
| engagement | 8 | 6 | 100% | 14% | 14.3% |
| quotes | 9 | 3 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 9 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 25 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 12 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.6%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 92 | Included in Core |
| **Олександра Матвійчук: Захист прав людини** | ⚪️ | 50 | Skipped |
| **Вступ** | ✅ | 138 | Included in Core |
| **Життєпис** | ⚪️ | 346 | Skipped |
| **Внесок** | ⚪️ | 264 | Skipped |
| **Вплив** | ⚪️ | 181 | Skipped |
| **Епоха та середовище** | ⚪️ | 422 | Skipped |
| **Порівняльний аналіз** | ✅ | 167 | Included in Core |
| **Підсумок** | ✅ | 82 | Included in Core |
| **Есе** | ⚪️ | 425 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 46 | Skipped |