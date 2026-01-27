# Audit Report: M46 — ivan-franko.md

**Level:** C1 | **Module:** M46 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:19

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
| 1 | quiz | Розуміння тексту про Івана Франка | 8 | 5 | ✅ |
| 2 | fill-in | Біографічна та академічна лексика | 8 | 6 | ✅ |
| 3 | error-correction | Граматика в біографічному контексті | 8 | 5 | ✅ |
| 4 | match-up | Відповідність біографічних термінів | 12 | 6 | ✅ |
| 5 | select | Лінгвістичний аналіз первинного джерела | 6 | 5 | ✅ |
| 6 | unjumble | Конструкції біографічного наративу | 8 | 5 | ✅ |
| 7 | cloze | Життєвий подвиг Каменяра | 17 | 1 | ✅ |
| 8 | true-false | Історична правда про Івана Франка | 8 | 5 | ✅ |
| 9 | group-sort | Класифікація спадщини Франка | 17 | 1 | ✅ |
| 10 | comparative-study | Франко та Шевченко як два типи лідерства | 1 | 1 | ✅ |
| 11 | reading | Аналіз публіцистичного стилю Франка | 3 | 1 | ✅ |
| 12 | reading | Дослідження поетичного модернізму | 3 | 1 | ✅ |
| 13 | authorial-intent | Наміри автора в поемі «Мойсей» | 1 | 1 | ✅ |
| 14 | essay-response | «Іван Франко та Тарас Шевченко — Два обличчя українського відродження» | 1 | 1 | ✅ |

**Summary:**
- Total activities: 14 (target: 3-9) ❌
- Unique types: 13 (minimum: 3) ✅
- Priority types used: 5/6 (authorial-intent, comparative-study, essay-response, quiz, reading) ✅
- Required types used: 6/6 (essay-response, fill-in, group-sort, match-up, quiz, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[CONTENT_REDUNDANCY]** Redundant information detected in lesson (75% overlap): "Його називають «Титаном праці» за колосальну продуктивність — понад 5000 творів у різних галузях зна...". Shares significant keywords with sentence at index 1.
  - FIX: Remove redundant paragraphs. Ensure each section adds new unique value.
- **[YAML_SCHEMA_VIOLATION]** Schema error in ivan-franko.yaml: Schema validation error at key '11': {'type': 'reading', 'title': 'Дослідження поетичного модернізму', 'resource': {'type': 'primary_source', 'url': 'https://www.i-franko.name/uk/Poetry/ZivjaleLystja.html', 'title': "«Іван Франко — Збірка «Зів'яле листя»»"}, 'tasks': ['«Проаналізуйте використання емоційно забарвлених прикметників у першому «жмутку» поезій.»', '«Порівняйте мову інтимної лірики Франка з його публіцистичним стилем. Які відмінності у виборі дієслів ви помітили?»', '«Знайдіть приклади порівнянь та метафор, які автор використовує для опису душевного стану.»']} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE

- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Спадщина|Вплив' found: Вплив на сучасників, Спадщина
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).

## Recommendation

**📝 UPDATE** (severity 25/100)

- 3 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates

- **Words:** ❌ 2003/4000 (raw: 2224)
- **Activities:** ✅ 14/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 13/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ⚠️ Too many activities: 14 (target 3-9)
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
| primary_sources | 4 | 4 | 100% | 19% | 19.0% |
| engagement | 7 | 6 | 100% | 14% | 14.3% |
| quotes | 7 | 3 | 100% | 14% | 14.3% |
| cultural | 6 | 4 | 100% | 10% | 9.5% |
| visual | 5 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.97 | - | 97% | 5% | 4.6% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 9 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.9%** |

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 69 | Included in Core |
| **Вступ** | ✅ | 214 | Included in Core |
| **Життєпис** | ⚪️ | 205 | Skipped |
| **Внесок** | ⚪️ | 655 | Skipped |
| **Спадщина** | ⚪️ | 199 | Skipped |
| **Історичний контекст** | ✅ | 334 | Included in Core |
| **Порівняльний аналіз** | ✅ | 152 | Included in Core |
| **Підсумок** | ✅ | 159 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 16 | Skipped |
