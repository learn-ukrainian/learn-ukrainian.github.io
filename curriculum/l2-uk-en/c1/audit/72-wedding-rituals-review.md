# Audit Report: M72 — 72-wedding-rituals.md
**Level:** C1 | **Module:** M72 | **Phase:** C1 | **Pedagogy:** CBI | **Target:** 3000
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:29:39

## Configuration
**Type:** C1-cultural
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
| 1 | quiz | Розуміння весільної обрядовості | 8 | 5 | ✅ |
| 2 | match-up | Весільні чини та ролі | 8 | 6 | ✅ |
| 3 | group-sort | Атрибути весільних етапів | 12 | 12 | ✅ |
| 4 | cloze | Семіотика весільного хліба | 15 | 12 | ✅ |
| 5 | match-up | Весільна термінологія та дієслова | 8 | 6 | ✅ |
| 6 | select | Атрибути та символи шлюбу | 6 | 5 | ✅ |
| 7 | true-false | Факти та міфи про українське весілля | 8 | 5 | ✅ |
| 8 | essay-response | Аналіз весілля як сакральної містерії переходу | 1 | 1 | ✅ |
| 9 | unjumble | Весільні віншування та приказки | 6 | 5 | ✅ |
| 10 | fill-in | Граматика весільних дій | 8 | 6 | ✅ |
| 11 | cloze | Духовна сила весілля | 16 | 12 | ✅ |
| 12 | select | Традиції весільної перезви | 6 | 5 | ✅ |

**Summary:**
- Total activities: 12 (target: 12-16) ✅
- Unique types: 9 (minimum: 4) ✅
- Priority types used: 2/3 (fill-in, unjumble) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 72-wedding-rituals.yaml: Schema validation error at key 'words': ['Традиційне', 'українське', 'весілля', 'є', 'величним', 'гімном', 'життю', 'та', 'неперервності', 'людського', 'роду'] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 1 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2100/3000 (raw: 2207)
- **Activities:** ✅ 12/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 9/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/7
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 25 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (12 activities)
- **Immersion:** 🇺🇦 99.9% (target 90-100% (cultural))
- **Richness:** ✅ 99% (content)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 0/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** content

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 17 | 15 | 100% | 25% | 25.0% |
| engagement | 8 | 5 | 100% | 19% | 18.7% |
| variety | 0.97 | - | 97% | 12% | 12.1% |
| cultural | 7 | 4 | 100% | 12% | 12.5% |
| realworld | 5 | 3 | 100% | 12% | 12.5% |
| visual | 9 | 4 | 100% | 6% | 6.2% |
| paragraph_var | 1.00 | - | 100% | 6% | 6.2% |
| questions | 7 | 4 | 100% | 6% | 6.2% |
| **TOTAL** | | | | | **99.6%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 104 | Included in Core |
| **Вступ** | ✅ | 191 | Included in Core |
| **Презентація** | ⚪️ | 626 | Skipped |
| **Семіотика весільних дарів: Мова речей** | ⚪️ | 123 | Skipped |
| **Культурна трагедія: Втрачені коди та радянське «комсомольське весілля»** | ✅ | 204 | Included in Core |
| **Лінгвістичний коментар: Специфічний весільний реєстр лексики** | ⚪️ | 122 | Skipped |
| **Аналіз** | ✅ | 294 | Included in Core |
| **Підсумок** | ✅ | 223 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 213 | Skipped |