# Audit Report: M61 — andrey-sheptytsky.md
**Level:** C1-BIO | **Module:** M61 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4300
**Naturalness:** 10/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-07 00:22:03

## Configuration
**Type:** C1-biography
**Word Target:** 4300 words
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
| 1 | reading | Андрей Шептицький: Моральний опір | 2 | 1 | ✅ |
| 2 | essay-response | Есе: Український Мойсей | 1 | 1 | ✅ |
| 3 | critical-analysis | Аналіз етичного імперативу | 1 | 1 | ✅ |
| 4 | comparative-study | Шептицький та Вишинський: Духовний опір | 1 | 1 | ✅ |
| 5 | true-false | Факти про Андрея Шептицького | 10 | 5 | ✅ |

**Summary:**
- Total activities: 5 (target: 3-9) ✅
- Unique types: 5 (minimum: 3) ✅
- Priority types used: 4/6 (comparative-study, critical-analysis, essay-response, reading) ✅
- Required types used: 2/2 (essay-response, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in andrey-sheptytsky.yaml: ⚠️ YAML uses dictionary wrapper (`activities:` key). Activities MUST be a bare list at root level. Run auto-fix: .venv/bin/python scripts/audit_module.py --fix <file.md>
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 1 violations (minor)

## Gates
- **Words:** ✅ 4940/4300 (raw: 5368)
- **Activities:** ✅ 5/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 5/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ❌ 4/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 25/24
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (5 activities)
- **Immersion:** 🇺🇦 100.0% (target 95-100% (biography))
- **Richness:** ❌ 92% < 95% min (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 10/10 (High)

## Richness Details
**Score:** 92% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 5 | 4 | 100% | 19% | 19.0% |
| engagement | 3 | 6 | 50% | 14% | 7.1% |
| quotes | 15 | 3 | 100% | 14% | 14.3% |
| cultural | 4 | 4 | 100% | 10% | 9.5% |
| visual | 5 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.95 | - | 95% | 5% | 4.5% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 11 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **92.6%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 107 | Included in Core |
| **Вступ: Духовний архітектор нації** | ✅ | 320 | Included in Core |
| **Повернення до коріння: Від графа до монаха (1865-1901)** | ⚪️ | 603 | Skipped |
| **Будівничий інституцій: Церква, наука, музей** | ⚪️ | 724 | Skipped |
| **Між вогнями: Перша світова та визвольні змагання** | ⚪️ | 652 | Skipped |
| **Моральний імператив: Голокост та «Не убий» (1941-1944)** | ⚪️ | 816 | Skipped |
| **Смерть і спадщина: Камертон української совісті** | ⚪️ | 693 | Skipped |
| **Порівняльний аналіз: Шептицький та європейські духовні лідери** | ✅ | 139 | Included in Core |
| **Критичне мислення** | ⚪️ | 182 | Skipped |
| **Есе** | ⚪️ | 99 | Skipped |
| **Зразок відповіді** | ⚪️ | 444 | Skipped |
| **Підсумок: Камертон української совісті** | ✅ | 161 | Included in Core |
| **Activities** | ➖ | 0 | Excluded Type |
| **Vocabulary** | ➖ | 0 | Excluded Type |