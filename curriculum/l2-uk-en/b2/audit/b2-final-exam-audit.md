# Audit Report: M95 — b2-final-exam.md
**Level:** B2 | **Module:** M95 | **Phase:** B2.4 | **Pedagogy:** TTT | **Target:** 4000
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-25 20:35:54

## Configuration
**Type:** B2-checkpoint
**Word Target:** 4000 words
**Activities:** 15-19 required
**Items per Activity:** ≥14 items
**Unique Types:** ≥4 types required
**Priority Types:** cloze, error-correction, fill-in, quiz
**Required Types:** essay-response, reading, true-false
**Engagement:** ≥4 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥10 words
**Transliteration:** Not allowed

## PEDAGOGICAL VIOLATIONS
- **[RUSSICISM_DETECTED]** Found 2 Russicism(s) in content: 'приймати участь' → брати участь; 'получати' → отримувати
  - FIX: Replace Russicisms with standard Ukrainian equivalents. These are Russian calques that have standard Ukrainian forms. See Phase B prompt 'Russianisms Pre-Output Scan' table.
- **[EUPHONY]** Line 42: «в процесі» — в перед збігом приголосних; має бути «у процесі»
  - FIX: Replace «в» with «у» (before consonant cluster)
- **[EUPHONY]** Line 55: «в своїх» — в перед збігом приголосних; має бути «у своїх»
  - FIX: Replace «в» with «у» (before consonant cluster)
- **[EUPHONY]** Line 78: «в професійному» — в перед збігом приголосних; має бути «у професійному»
  - FIX: Replace «в» with «у» (before consonant cluster)
- **[EUPHONY]** Line 108: «в графіку» — в перед збігом приголосних; має бути «у графіку»
  - FIX: Replace «в» with «у» (before consonant cluster)
- **[EUPHONY]** Line 205: «помилкою і ознакою» — і між голосними; має бути «й ознакою»
  - FIX: Replace «і» with «й» (between vowels)
- **[EUPHONY]** Line 269: «в цьому» — в перед збігом приголосних; має бути «у цьому»
  - FIX: Replace «в» with «у» (before consonant cluster)
- **[LLM_FINGERPRINT_REPETITION]** Repetitive LLM rhetorical patterns (8 total): 'не просто X, а Y' x6, 'не лише X, а й Y' x2 — robotic prose
  - FIX: Vary sentence structures. Replace formulaic 'не просто X, а Y' with diverse rhetorical devices
- **[YAML_SCHEMA_VIOLATION]** Schema error in b2-final-exam.yaml: Schema validation error at key 'words': ['сучасна', 'конкуренція', 'вимагає', 'нових', 'підходів'] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 55/100)

- Revision recommended (severity 55/100)
- 9 violations (significant)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ❌ 3419/4000 (raw: 3799)
- **Activities:** ❌ 0/15
- **Density:** ❌ 0 < 14
- **Unique_types:** ❌ 0/4 types
- **Priority:** ❌ No priority types
- **Engagement:** ❌ 0/4
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 30/10
- **Structure:** ✅ Valid Structure
- **Ipa:** ✅ Clean IPA
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too few activities: 0 (target 15-19)
- **Immersion:** 🇺🇦 98.4% (checkpoint - no gate)
- **Richness:** ❌ 69% < 85% min (checkpoint)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ✅ Content aligned with research

## Richness Details
**Score:** 69% (minimum: 85%)
**Module Type:** checkpoint

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| activity_types | 8 | 8 | 100% | 25% | 25.0% |
| review_sections | 25 | 3 | 100% | 20% | 20.0% |
| variety | 0.97 | - | 97% | 15% | 14.5% |
| engagement | 0 | 3 | 0% | 10% | 0.0% |
| cultural | 0 | - | 0% | 10% | 0.0% |
| visual | 0 | 3 | 0% | 10% | 0.0% |
| paragraph_var | 1.00 | - | 100% | 10% | 10.0% |
| **TOTAL** | | | | | **69.5%** |

### Dryness Flags & Fixes
- ❌ **NO_ENGAGEMENT**
  - FIX:
    Add 2+ engagement boxes. Use this exact format:
    
    > 💡 **Чи знали ви?**
    >
    > [Interesting fact about the grammar/vocabulary topic in Ukrainian]
    
    > 🇺🇦 **Культурний момент**
    >
    > [Cultural context connecting grammar to Ukrainian life/places]
    
    > 🌍 **У реальному житті**
    >
    > [Practical scenario where this grammar is used]

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **B2 Підсумковий іспит** | ✅ | 60 | Included in Core |
| **Огляд — Фінальний іспит B2** | ✅ | 550 | Included in Core |
| **Частина 1: Читання та академічна ідентичність** | ✅ | 778 | Included in Core |
| **Частина 2: Письмо та стилістична вправність** | ✅ | 639 | Included in Core |
| **Частина 3: Слухання та лексична точність** | ✅ | 624 | Included in Core |
| **Частина 4: Говоріння та підсумок рівня** | ✅ | 615 | Included in Core |
| **Підсумок** | ✅ | 153 | Included in Core |