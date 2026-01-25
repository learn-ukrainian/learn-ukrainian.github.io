# Audit Report: M71 — ivan-ohienko.md
**Level:** C1 | **Module:** M71 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-25 19:27:24

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
| 1 | quiz | Життя та діяльність Івана Огієнка | 6 | 5 | ✅ |
| 2 | match-up | Термінологія церковного та мовознавчого життя | 12 | 6 | ✅ |
| 3 | cloze | Біографія Івана Огієнка | 12 | 1 | ✅ |
| 4 | true-false | Факти про Івана Огієнка | 8 | 5 | ✅ |
| 5 | fill-in | Лексика церковного та наукового життя | 6 | 6 | ✅ |
| 6 | select | Сфери діяльності Івана Огієнка | 5 | 5 | ✅ |
| 7 | error-correction | Граматичні вправи | 5 | 5 | ✅ |
| 8 | unjumble | Твердження про Огієнка | 5 | 5 | ✅ |
| 9 | group-sort | Сфери діяльності Івана Огієнка | 12 | 1 | ✅ |
| 10 | essay-response | Аналітичне есе: Мова і віра | 1 | 1 | ✅ |
| 11 | comparative-study | Порівняння: Куліш та Огієнко | 1 | 1 | ✅ |
| 12 | fill-in | Праця «Українська церква» | 6 | 6 | ✅ |

**Summary:**
- Total activities: 12 (target: 3-9) ❌
- Unique types: 11 (minimum: 3) ✅
- Priority types used: 3/6 (comparative-study, essay-response, quiz) ✅
- Required types used: 5/6 (essay-response, fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in ivan-ohienko.yaml: Schema validation error at key '11': {'type': 'fill-in', 'title': 'Праця «Українська церква»', 'instruction': 'Заповніть пропуски в тексті про історичну працю Огієнка.', 'items': [{'sentence': 'У праці «Українська церква» Огієнко доводив право українців на власну _____.', 'answer': 'церкву', 'options': ['церкву', 'державу', 'армію', 'школу']}, {'sentence': 'Він аналізував історію _____ церкви.', 'answer': 'української', 'options': ['української', 'російської', 'польської', 'грецької']}, {'sentence': 'Огієнко вважав, що богослужіння має відбуватися _____ мовою.', 'answer': 'рідною', 'options': ['рідною', 'латинською', "церковнослов'янською", 'грецькою']}, {'sentence': 'Книга була видана під час _____ світової війни.', 'answer': 'Другої', 'options': ['Другої', 'Першої', 'Третьої', 'Холодної']}, {'sentence': 'Ця праця стала теоретичною основою для _____.', 'answer': 'автокефалії', 'options': ['автокефалії', 'унії', 'розколу', 'реформи']}, {'sentence': 'Огієнко писав, що церква має служити _____ інтересам народу.', 'answer': 'національним', 'options': ['національним', 'політичним', 'економічним', 'особистим']}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 1 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2248/4000 (raw: 2382)
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
- **Content_heavy:** ⚠️ Too many activities: 12 (target 3-9); 1 cloze with year blanks
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
| primary_sources | 9 | 4 | 100% | 19% | 19.0% |
| engagement | 11 | 6 | 100% | 14% | 14.3% |
| quotes | 10 | 3 | 100% | 14% | 14.3% |
| cultural | 7 | 4 | 100% | 10% | 9.5% |
| visual | 11 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.97 | - | 97% | 5% | 4.6% |
| paragraph_var | 0.98 | - | 98% | 5% | 4.7% |
| questions | 8 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Вступ** | ✅ | 169 | Included in Core |
| **Життєпис** | ⚪️ | 1249 | Skipped |
| **Внесок** | ⚪️ | 115 | Skipped |
| **Останні роки** | ⚪️ | 104 | Skipped |
| **Спадщина** | ⚪️ | 173 | Skipped |
| **Порівняльний аналіз** | ✅ | 202 | Included in Core |
| **Підсумок** | ✅ | 135 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 101 | Skipped |