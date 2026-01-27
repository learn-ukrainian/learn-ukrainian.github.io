# Audit Report: M82 — 82-obrazotvorche-mystetstvo-2.md

**Level:** C1 | **Module:** M82 | **Phase:** C1 | **Pedagogy:** CBI | **Target:** 3000
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:29:45

## Configuration

**Type:** C1-fine-arts
**Word Target:** 3000 words
**Activities:** 12-16 required
**Items per Activity:** ≥12 items
**Unique Types:** ≥4 types required
**Priority Types:** error-correction, fill-in, unjumble
**Engagement:** ≥7 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥25 words
**Transliteration:** Not allowed

## Activity Breakdown

| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | quiz | Мистецтво XX-XXI століття | 12 | 5 | ✅ |
| 2 | match-up | Митці та їхні твори/стилі | 10 | 6 | ✅ |
| 3 | cloze | Феномен Марії Примаченко | 12 | 12 | ✅ |
| 4 | fill-in | Термінологія сучасного мистецтва | 10 | 6 | ✅ |
| 5 | essay-response | Есе: Мистецтво і тоталітаризм | 1 | 1 | ✅ |
| 6 | true-false | Міфи та реальність | 10 | 5 | ✅ |
| 7 | group-sort | Класифікація творчості | 15 | 12 | ✅ |
| 8 | mark-the-words | Аналіз опису картини | 7 | 5 | ✅ |
| 9 | translate | Мистецькі концепції | 8 | 5 | ✅ |
| 10 | unjumble | Тези про сучасне мистецтво | 6 | 5 | ✅ |
| 11 | select | Творчість Івана Марчука | 8 | 5 | ✅ |
| 12 | critical-analysis | Аналіз творчості Алли Горської | 1 | 1 | ✅ |
| 13 | comparative-study | Наївне vs Професійне | 1 | 1 | ✅ |
| 14 | reading | Маніфест шістдесятників | 3 | 3 | ✅ |
| 15 | unjumble | Цитати Марії Примаченко | 8 | 5 | ✅ |
| 16 | true-false | Інституції сучасного мистецтва | 10 | 5 | ✅ |
| 17 | fill-in | Мурали Києва | 10 | 6 | ✅ |

**Summary:**
- Total activities: 17 (target: 12-16) ❌
- Unique types: 14 (minimum: 4) ✅
- Priority types used: 2/3 (fill-in, unjumble) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[COMPLEXITY_WORD_COUNT]** unjumble 'Цитати Марії Примаченко' item 4 has 10 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 82-obrazotvorche-mystetstvo-2.yaml: Schema validation error at key 'words': ['Я', 'люблю', 'малювати', 'людям', 'на', 'велику', 'радість', 'щоб', 'всі', 'були', 'щасливі'] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation

**📝 UPDATE** (severity 25/100)

- 2 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates

- **Words:** ❌ 1987/3000 (raw: 2098)
- **Activities:** ✅ 17/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 14/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/7
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 25 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ⚠️ Too many activities: 17 (target 12-16)
- **Immersion:** 🇺🇦 98.9% (target 90-100% (fine-arts))
- **Richness:** ✅ 98% (content)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 0/10 (PENDING) - Naturalness check required

## Richness Details

**Score:** 98% (minimum: 95%)
**Module Type:** content

### Score Breakdown

| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 30 | 15 | 100% | 25% | 25.0% |
| engagement | 7 | 5 | 100% | 19% | 18.7% |
| variety | 0.99 | - | 99% | 12% | 12.4% |
| cultural | 5 | 4 | 100% | 12% | 12.5% |
| realworld | 8 | 3 | 100% | 12% | 12.5% |
| visual | 3 | 4 | 75% | 6% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 6% | 6.2% |
| questions | 5 | 4 | 100% | 6% | 6.2% |
| **TOTAL** | | | | | **98.3%** |

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 84 | Included in Core |
| **Вступ: Мистецтво в лещатах ідеології** | ✅ | 121 | Included in Core |
| **Наївне мистецтво: Душа народу** | ⚪️ | 357 | Skipped |
| **Шістдесятники: Мистецтво спротиву** | ⚪️ | 225 | Skipped |
| **Іван Марчук: Геній пльонтанізму** | ⚪️ | 183 | Skipped |
| **Сучасне мистецтво: Нова хвиля та інституції** | ⚪️ | 581 | Skipped |
| **Аналіз** | ✅ | 206 | Included in Core |
| **Підсумок** | ✅ | 93 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 137 | Skipped |
