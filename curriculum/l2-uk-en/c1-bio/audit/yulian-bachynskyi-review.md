# Audit Report: M70 — yulian-bachynskyi.md
**Level:** C1-BIO | **Module:** M70 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 10/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-07 00:22:08

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
| 1 | reading | Юліан Бачинський: Маніфест неминучості | 2 | 1 | ✅ |
| 2 | essay-response | Есе: Пророцтво про самостійність | 1 | 1 | ✅ |
| 3 | critical-analysis | Аналіз економічного самостійництва | 1 | 1 | ✅ |
| 4 | comparative-study | Два шляхи до свободи: Бачинський та Міхновський | 1 | 1 | ✅ |
| 5 | true-false | Факти про Юліана Бачинського | 10 | 5 | ✅ |

**Summary:**
- Total activities: 5 (target: 3-9) ✅
- Unique types: 5 (minimum: 3) ✅
- Priority types used: 4/6 (comparative-study, critical-analysis, essay-response, reading) ✅
- Required types used: 2/2 (essay-response, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in yulian-bachynskyi.yaml: ⚠️ YAML uses dictionary wrapper (`activities:` key). Activities MUST be a bare list at root level. Run auto-fix: .venv/bin/python scripts/audit_module.py --fix <file.md>
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 1 violations (minor)

## Gates
- **Words:** ❌ 3574/4000 (raw: 4032)
- **Activities:** ✅ 5/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 5/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 26/24
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (5 activities)
- **Immersion:** 🇺🇦 98.9% (target 95-100% (biography))
- **Richness:** ✅ 97% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 10/10 (High)

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 9 | 4 | 100% | 19% | 19.0% |
| engagement | 5 | 6 | 83% | 14% | 11.9% |
| quotes | 15 | 3 | 100% | 14% | 14.3% |
| cultural | 5 | 4 | 100% | 10% | 9.5% |
| visual | 7 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.95 | - | 95% | 5% | 4.5% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 10 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.3%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 95 | Included in Core |
| **Вступ: Перший самостійник** | ✅ | 323 | Included in Core |
| **Витоки: Галицький радикалізм та марксистський метод (1870-1894)** | ⚪️ | 637 | Skipped |
| **«Ukraina Irredenta»: Маніфест неминучості (1895)** | ⚪️ | 642 | Skipped |
| **Дипломатія та державотворення (1917-1923)** | ⚪️ | 608 | Skipped |
| **Трагедія повернення: Радянський зашморг (1933-1940)** | ⚪️ | 605 | Skipped |
| **Порівняльний аналіз: Ідеологія самостійності** | ✅ | 64 | Included in Core |
| **Критичне мислення** | ⚪️ | 114 | Skipped |
| **Есе** | ⚪️ | 69 | Skipped |
| **Зразок відповіді** | ⚪️ | 317 | Skipped |
| **Підсумок: Пророцтво, що стало дійсністю** | ✅ | 100 | Included in Core |
| **Activities** | ➖ | 0 | Excluded Type |
| **Vocabulary** | ➖ | 0 | Excluded Type |