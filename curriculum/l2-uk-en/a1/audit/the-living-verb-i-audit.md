# Audit Report: M15 — the-living-verb-i.md
**Level:** A1 | **Module:** M15 | **Phase:** A1.2 | **Pedagogy:** PPP | **Target:** 1200
**Overall Status:** ❌ FAIL
**Generated:** 2026-03-18 04:06:19

## Configuration
**Type:** A1-grammar
**Word Target:** 1200 words
**Activities:** 0-4 required
**Items per Activity:** ≥6 items
**Unique Types:** ≥0 types required
**Priority Types:** anagram, classify, fill-in, image-to-letter, match-up, quiz, unjumble, watch-and-repeat
**Engagement:** ≥3 callouts
**Immersion:** 0-100%
**Vocab Target:** ≥1 words
**Transliteration:** Allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | match-up | Match pronoun to verb form | 18 | 6 | ✅ |
| 2 | fill-in | Choose the correct verb form | 30 | 6 | ✅ |
| 3 | fill-in | Conjugate correctly | 20 | 6 | ✅ |

**Summary:**
- Total activities: 3 (target: 0-4) ✅
- Unique types: 2 (minimum: 0) ✅
- Priority types used: 2/8 (fill-in, match-up) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in the-living-verb-i.yaml: Schema validation error at key '2': {'type': 'fill-in', 'title': 'Conjugate correctly', 'instruction': 'Вставте правильну форму дієслова.', 'items': [{'sentence': 'Що ти ___? (читати)', 'answer': 'читаєш', 'translation': 'What are you reading?'}, {'sentence': 'Я ___ зараз. (працювати)', 'answer': 'працюю', 'translation': 'I am working now.'}, {'sentence': 'Де він ___? (відпочивати)', 'answer': 'відпочиває', 'translation': 'Where is he resting?'}, {'sentence': 'Ми ___ вас. (розуміти)', 'answer': 'розуміємо', 'translation': 'We understand you.'}, {'sentence': 'Що ви ___? (вивчати)', 'answer': 'вивчаєте', 'translation': 'What are you studying?'}, {'sentence': 'Вони ___ листи. (писати)', 'answer': 'пишуть', 'translation': 'They write letters.'}, {'sentence': 'Я не ___. (знати)', 'answer': 'знаю', 'translation': "I don't know."}, {'sentence': 'Ти ___ на гітарі? (грати)', 'answer': 'граєш', 'translation': 'Do you play the guitar?'}, {'sentence': 'Вона ___ друга. (чекати)', 'answer': 'чекає', 'translation': 'She is waiting for a friend.'}, {'sentence': 'Ми ___ про це. (думати)', 'answer': 'думаємо', 'translation': 'We think about this.'}, {'sentence': 'Ви ___ радіо? (слухати)', 'answer': 'слухаєте', 'translation': 'Are you listening to the radio?'}, {'sentence': 'Вони ___ мене. (питати)', 'answer': 'питають', 'translation': 'They ask me.'}, {'sentence': 'Я ___ швидко. (читати)', 'answer': 'читаю', 'translation': 'I read fast.'}, {'sentence': 'Ти ___ гарно. (писати)', 'answer': 'пишеш', 'translation': 'You write beautifully.'}, {'sentence': 'Він ___ все. (знати)', 'answer': 'знає', 'translation': 'He knows everything.'}, {'sentence': 'Ми ___ разом. (працювати)', 'answer': 'працюємо', 'translation': 'We work together.'}, {'sentence': 'Ви ___ добре. (відпочивати)', 'answer': 'відпочиваєте', 'translation': 'You are resting well.'}, {'sentence': 'Вони ___ українську. (розуміти)', 'answer': 'розуміють', 'translation': 'They understand Ukrainian.'}, {'sentence': 'Я ___ слова. (вивчати)', 'answer': 'вивчаю', 'translation': 'I am studying words.'}, {'sentence': 'Ти ___ тут. (чекати)', 'answer': 'чекаєш', 'translation': 'You wait here.'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple headers contain 'Summary': Підсумок (Summary), Культурний аспект та підсумок (Cultural Insight and Summary)
  - FIX: RENAME one header to NOT contain 'Summary'. Example: 'Агіографічна спадщина' → 'Житійна творчість' (removes the duplicate word).

## Recommendation
**📝 UPDATE** (severity 5/100)

- 2 violations (minor)

## Gates
- **Words:** ✅ 1329/1200 (raw: 1572)
- **Activities:** ✅ 3/0
- **Density:** ✅ All > 6
- **Unique_types:** ✅ 2/0 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 4/3
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 12/1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 17.6% (target 15-25% (M15))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ✅ Content aligned with research

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Вступ (Introduction)** | ✅ | 224 | Included in Core |
| **Презентація (Presentation)** | ✅ | 313 | Included in Core |
| **Практика (Practice)** | ✅ | 479 | Included in Core |
| **Культурний аспект та підсумок (Cultural Insight and Summary)** | ✅ | 263 | Included in Core |
| **Підсумок (Summary)** | ✅ | 50 | Included in Core |