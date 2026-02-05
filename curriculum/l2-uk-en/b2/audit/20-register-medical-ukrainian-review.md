# Audit Report: M20 — 20-register-medical-ukrainian.md
**Level:** B2 | **Module:** M20 | **Phase:** B2.1b | **Pedagogy:** Not Specified | **Target:** 3800
**Naturalness:** 8/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-05 22:11:36

## Configuration
**Type:** B2-grammar
**Word Target:** 3800 words
**Activities:** 10-14 required
**Items per Activity:** ≥14 items
**Unique Types:** ≥4 types required
**Priority Types:** cloze, error-correction, fill-in, unjumble
**Required Types:** error-correction, essay-response, fill-in, match-up, quiz, reading
**Engagement:** ≥6 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥25 words
**Transliteration:** Not allowed

## PEDAGOGICAL VIOLATIONS
- **[SECTION_ORDER]** Content section '## Практика і підсумок' appears after end section '# Підсумок'
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[CONTENT_REDUNDANCY]** Redundant information detected in lesson (71% overlap): "Якщо температура підніметься вище 38,5° — давайте жарознижувальне.". Shares significant keywords with sentence at index 12.
  - FIX: Remove redundant paragraphs. Ensure each section adds new unique value.
- **[ROBOTIC_STRUCTURE]** Robotic structure: 3 sentences start with '✅ правильно:...'.
  - FIX: Vary sentence structure.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 20-register-medical-ukrainian.yaml: YAML parse error: while parsing a block mapping
  in "<unicode string>", line 1274, column 3:
    - type: reading
      ^
expected <block end>, but found '<scalar>'
  in "<unicode string>", line 1276, column 85:
     ... лкування у сфері охорони здоров'я'
                                         ^
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: grammar) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.

## Recommendation
**📝 UPDATE** (severity 40/100)

- Revision recommended (severity 40/100)
- 5 violations (moderate)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ❌ 2783/3800 (raw: 3488)
- **Activities:** ❌ 0/10
- **Density:** ❌ 0 < 14
- **Unique_types:** ❌ 0/4 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 10/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 35/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 5 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.3% (target 90-100% (grammar))
- **Richness:** ✅ 99% (style)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 8/10 (High)

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** style

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| exemplar_texts | 6 | 2 | 100% | 25% | 25.0% |
| model_answers | 100 | 3 | 100% | 20% | 20.0% |
| engagement | 9 | 5 | 100% | 15% | 15.0% |
| register_analysis | 15 | 5 | 100% | 15% | 15.0% |
| visual | 12 | 4 | 100% | 10% | 10.0% |
| variety | 0.91 | - | 91% | 5% | 4.6% |
| cultural | 6 | - | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **99.5%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 67 | Included in Core |
| **Вступ — Медичний регістр** | ✅ | 18 | Included in Core |
| **Опис симптомів** | ⚪️ | 226 | Skipped |
| **Діалог лікар-пацієнт** | ✅ | 821 | Included in Core |
| **Медичні інструкції** | ⚪️ | 789 | Skipped |
| **Медична документація** | ⚪️ | 599 | Skipped |
| **Підсумок** | ✅ | 0 | Included in Core |
| **Типові помилки та русизми** | ✅ | 77 | Included in Core |
| **Практика і підсумок** | ✅ | 186 | Included in Core |