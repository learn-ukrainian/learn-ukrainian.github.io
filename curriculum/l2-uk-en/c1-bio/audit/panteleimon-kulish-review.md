# Audit Report: M33 — panteleimon-kulish.md
**Level:** C1 | **Module:** M33 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:13

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
| 1 | quiz | Життя та діяльність Пантелеймона Куліша | 6 | 5 | ✅ |
| 2 | match-up | Термінологія українського мовознавства | 12 | 6 | ✅ |
| 3 | cloze | Біографія Пантелеймона Куліша | 13 | 1 | ✅ |
| 4 | true-false | Факти про Пантелеймона Куліша | 8 | 5 | ✅ |
| 5 | fill-in | Лексика українського національного відродження | 6 | 6 | ✅ |
| 6 | select | Внесок Куліша в українську культуру | 5 | 5 | ✅ |
| 7 | error-correction | Граматичні вправи | 5 | 5 | ✅ |
| 8 | unjumble | Твердження про Куліша | 5 | 5 | ✅ |
| 9 | comparative-study | Порівняння: Куліш і Шевченко | 1 | 1 | ✅ |
| 10 | group-sort | Внесок Куліша в українську культуру | 12 | 1 | ✅ |
| 11 | essay-response | Аналітичне есе: Куліш і Шевченко | 1 | 1 | ✅ |
| 12 | fill-in | Роман «Чорна рада» | 6 | 6 | ✅ |

**Summary:**
- Total activities: 12 (target: 3-9) ❌
- Unique types: 11 (minimum: 3) ✅
- Priority types used: 3/6 (comparative-study, essay-response, quiz) ✅
- Required types used: 5/6 (essay-response, fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in panteleimon-kulish.yaml: Schema validation error at key '11': {'type': 'fill-in', 'title': 'Роман «Чорна рада»', 'instruction': 'Заповніть пропуски в тексті про перший історичний роман.', 'items': [{'sentence': '«Чорна рада» описує події _____ року.', 'answer': '1663', 'options': ['1663', '1654', '1648', '1709']}, {'sentence': 'Головний конфлікт роману — боротьба за _____.', 'answer': 'булаву', 'options': ['булаву', 'землю', 'віру', 'гроші']}, {'sentence': 'Куліш писав роман двома мовами: українською та _____.', 'answer': 'російською', 'options': ['російською', 'польською', 'німецькою', 'французькою']}, {'sentence': 'Події відбуваються в місті _____.', 'answer': 'Ніжин', 'options': ['Ніжин', 'Київ', 'Чигирин', 'Батурин']}, {'sentence': '«Чорна рада» — це перший український _____ роман.', 'answer': 'історичний', 'options': ['історичний', 'пригодницький', 'соціальний', 'психологічний']}, {'sentence': 'Автор називає свій твір _____.', 'answer': 'хронікою', 'options': ['хронікою', 'літописом', 'поемою', 'драмою']}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 1 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2418/4000 (raw: 2500)
- **Activities:** ✅ 12/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 11/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 10/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 12 (target 3-9); 1 cloze with year blanks; 1 fill-in with year answers
- **Immersion:** 🇺🇦 100.0% (target 95-100% (biography))
- **Richness:** ✅ 97% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 8 | 4 | 100% | 19% | 19.0% |
| engagement | 8 | 6 | 100% | 14% | 14.3% |
| quotes | 10 | 3 | 100% | 14% | 14.3% |
| cultural | 8 | 4 | 100% | 10% | 9.5% |
| visual | 3 | 4 | 75% | 10% | 7.1% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.97 | - | 97% | 5% | 4.6% |
| paragraph_var | 0.91 | - | 91% | 5% | 4.3% |
| questions | 7 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Вступ** | ✅ | 139 | Included in Core |
| **Життєпис** | ⚪️ | 1163 | Skipped |
| **Внесок** | ⚪️ | 162 | Skipped |
| **Останні роки** | ⚪️ | 258 | Skipped |
| **Спадщина** | ⚪️ | 137 | Skipped |
| **Порівняльний аналіз** | ✅ | 353 | Included in Core |
| **Підсумок** | ✅ | 131 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 75 | Skipped |