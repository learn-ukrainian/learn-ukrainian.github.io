# Audit Report: M39 — mykhailo-drahomanov.md
**Level:** C1 | **Module:** M39 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:15

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
| 1 | quiz | Глибокий аналіз політичної філософії Михайла Драгоманова | 12 | 5 | ✅ |
| 2 | unjumble | Політичні тези та ідеологеми Драгоманова | 12 | 5 | ✅ |
| 3 | cloze | Життя та ідеї Михайла Драгоманова | 12 | 1 | ✅ |
| 4 | true-false | Факти та міфи про Драгоманова | 12 | 5 | ✅ |
| 5 | fill-in | Політична та наукова лексика | 12 | 6 | ✅ |
| 6 | match-up | Терміни та ідеологічні концепти | 12 | 6 | ✅ |
| 7 | select | Аналіз політичної стратегії та впливів | 6 | 5 | ✅ |
| 8 | error-correction | Корекція граматики та стилістики | 12 | 5 | ✅ |
| 9 | group-sort | Класифікація ідей та етапів життя | 24 | 1 | ✅ |
| 10 | essay-response | Аналітичне завдання: Свобода та Мораль | 1 | 1 | ✅ |
| 11 | comparative-study | Порівняння: Еволюція vs Революція | 1 | 1 | ✅ |
| 12 | match-up | Географія та події в житті мислителя | 12 | 6 | ✅ |
| 13 | quiz | Наукові досягнення та фольклористика | 12 | 5 | ✅ |
| 14 | unjumble | Синтаксис та логіка драгоманівських роздумів | 12 | 5 | ✅ |
| 15 | comparative-study | Аналіз: Драгоманов та Грушевський | 1 | 1 | ✅ |
| 16 | reading | Читання та аналіз першоджерел | 3 | 1 | ✅ |
| 17 | essay-response | Есе: Архітектор Європейської України | 1 | 1 | ✅ |

**Summary:**
- Total activities: 17 (target: 3-9) ❌
- Unique types: 12 (minimum: 3) ✅
- Priority types used: 4/6 (comparative-study, essay-response, quiz, reading) ✅
- Required types used: 6/6 (essay-response, fill-in, group-sort, match-up, quiz, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in mykhailo-drahomanov.yaml: Schema validation error at key '15': {'type': 'reading', 'title': 'Читання та аналіз першоджерел', 'resource': {'type': 'article', 'url': 'https://shron1.chytomo.com/drahomanov-ukrainska-literatura-zaboronena-rosijskym-uryadom/', 'title': 'Українська література, заборонена російським урядом (конспект)'}, 'tasks': ['Які саме факти утисків наводить автор у своїй паризькій доповіді?', 'Як Драгоманов аргументує важливість української мови для загальноєвропейської культури?', 'Які прогнози він робить щодо майбутнього українського слова?']} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Останні роки' per template 'c1-biography-module-template.md'
  - FIX: Add '## Останні роки' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md

## Recommendation
**📝 UPDATE** (severity 25/100)

- 2 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2082/4000 (raw: 2340)
- **Activities:** ✅ 17/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 12/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 17 (target 3-9)
- **Immersion:** 🇺🇦 99.4% (target 95-100% (biography))
- **Richness:** ✅ 99% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 12 | 4 | 100% | 19% | 19.0% |
| engagement | 6 | 6 | 100% | 14% | 14.3% |
| quotes | 15 | 3 | 100% | 14% | 14.3% |
| cultural | 4 | 4 | 100% | 10% | 9.5% |
| visual | 7 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.95 | - | 95% | 5% | 4.5% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 13 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 74 | Included in Core |
| **Вступ** | ✅ | 154 | Included in Core |
| **Життєпис** | ⚪️ | 466 | Skipped |
| **Внесок** | ⚪️ | 252 | Skipped |
| **Спадщина** | ⚪️ | 70 | Skipped |
| **Історичний контекст** | ✅ | 483 | Included in Core |
| **Порівняльний аналіз** | ✅ | 100 | Included in Core |
| **Критичне мислення** | ⚪️ | 94 | Skipped |
| **Есе** | ⚪️ | 46 | Skipped |
| **Критерії оцінювання** | ⚪️ | 0 | Skipped |
| **Зразок відповіді** | ⚪️ | 247 | Skipped |
| **Підсумок** | ✅ | 79 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 17 | Skipped |