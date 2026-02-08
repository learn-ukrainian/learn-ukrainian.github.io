# Рецензія: Yesterday - Past Tense

**Level:** A1 | **Module:** 21
**Overall Score:** 7.5/10
**Status:** FAIL
**Reviewed:** 2026-02-08

## Plan Verification

Plan-Content Alignment: [FAIL]
- Sections: [PASS] All outlined sections present.
- Vocabulary: [FAIL] Required verb "ходити" missing from presentation. Recommended "спати" missing. "Жила" (verb) misidentified as "vein" (noun) in vocab file. Core time adverbs missing from vocab file.
- Grammar scope: [PASS] Mostly clean, though perfective "пішов" appears in summary unexpectedly.
- Objectives: [PASS] Covers past tense formation and usage.

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Good flow, but the sudden introduction of "пішов" in the summary is jarring. |
| 2 | Coherence | 8/10 | <7 | Concepts build logically, but vocabulary file is disconnected from content. |
| 3 | Relevance | 9/10 | <7 | High utility topic. |
| 4 | Educational | 7/10 | <7 | Missing plan-required verbs "ходити" and "спати" in the presentation tables. |
| 5 | Language | 9/10 | <8 | Ukrainian sentences in content are natural. |
| 6 | Pedagogy | 6/10 | <7 | **CRITICAL:** Activity "fill-in" items use "Я" (I) as subject but accept only one gender, penalizing students of the other gender. |
| 7 | Immersion | 6/10 | <6 | Heavy English explanation, low target language density. |
| 8 | Activities | 6/10 | <7 | **CRITICAL:** Gender ambiguity in fill-in exercises. Missing vocabulary coverage in activities. |
| 9 | Richness | 7/10 | <6 | Good use of "Червона рута" quote. |
| 10 | Beginner Safety | 8/10 | <7 | Explanations are welcoming and clear. |
| 11 | LLM Fingerprint | 9/10 | <7 | Feels relatively handcrafted. |
| 12 | Linguistic Accuracy | 7/10 | <9 | **CRITICAL:** Vocabulary file defines "жила" as "vein" (noun) instead of "lived" (verb). |

**Weighted Overall:** 104.5 / 14.0 = **7.46/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: **[FAIL]** Ambiguous gender answers in "fill-in" activities.
- Beginner safety: 4/5 (Confusion in activities)

## Critical Issues Found

### Issue 1: Linguistic Accuracy (Vocabulary File)
- **Location**: `vocabulary/21-yesterday-past-tense.yaml` Item "жила"
- **Original**: `translation: vein`, `pos: noun`
- **Problem**: The module uses "жила" as the past tense feminine form of "жити" (to live). The vocabulary file completely misinterprets it as the homonym "vein".
- **Fix**: Remove this item or correct it to the lemma "жити" (though lemmas should be infinitives). Since it's a grammar form, it arguably shouldn't be in the vocab file as a new lemma unless explaining the form. Better to replace with missing adverbs like "вчора".

### Issue 2: Pedagogy / Activity Logic
- **Location**: `activities/21-yesterday-past-tense.yaml` Type "fill-in", Items 8 and 13 (in list read)
- **Original**:
  - `sentence: Вранці я ___ каву в кафе.` -> `answer: пив` (Option `пила` exists)
  - `sentence: Я ___ музику.` -> `answer: слухала` (Option `слухав` exists)
- **Problem**: A female student answering "Я пила" will be marked wrong. A male student answering "Я слухав" will be marked wrong. In a module specifically teaching gender agreement, this is confusing and frustrating.
- **Fix**: Change subjects to specific names or 3rd person pronouns to enforce the specific gender answer. E.g., "Андрій ___ каву" (пив), "Марія ___ музику" (слухала).

### Issue 3: Plan Compliance (Vocabulary)
- **Location**: Content vs Plan
- **Original**: Plan requires "ходити" and recommends "спати".
- **Problem**: "Ходити" is absent from the "Key Verbs" table. "Спати" is absent entirely. "Ходити" is a high-frequency motion verb essential for A1.
- **Fix**: Add "ходити" and "спати" to the "Key Verbs in Past Tense" table in the Presentation section.

### Issue 4: Vocabulary File Completeness
- **Location**: `vocabulary/21-yesterday-past-tense.yaml`
- **Original**: Missing core new words.
- **Problem**: The lesson introduces critical time adverbs (`вчора`, `позавчора`, `давно`, `колись`, `раніше`), but they are not in the vocabulary file.
- **Fix**: Add these terms to the vocabulary YAML.

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? [Pass]
- Instructions clear? [Pass]
- Quick wins? [Pass]
- Ukrainian scary? [Pass]
- Come back tomorrow? [Fail] (If I get marked wrong for my gender in the quiz, I might be annoyed).

Emotional beats:
- Welcome: Yes (Warm-up).
- Curiosity: Yes (Song quote).
- Quick wins: Clear rules.
- Encouragement: "It's surprisingly easy!"

## Strengths
- Clear explanation of the -в/-ла/-ло/-ли pattern.
- Good use of cultural context ("Червона рута").
- Natural-sounding dialogues.

## Fix Plan to Reach 9/10

### Linguistic Accuracy: 7/10 → 10/10
**What to fix:**
1.  `vocabulary/21-yesterday-past-tense.yaml`: Delete the entry for `жила` (vein).
2.  `vocabulary/21-yesterday-past-tense.yaml`: Add missing adverbs: `вчора`, `позавчора`, `давно`, `недавно`, `раніше`, `колись`, `минулого тижня` (phrase).

### Activities: 6/10 → 9/10
**What to fix:**
1.  `activities/21-yesterday-past-tense.yaml`: In `fill-in` (Transform to Past Tense), change "Я ___ музику" to "Марина ___ музику" (or similar).
2.  `activities/21-yesterday-past-tense.yaml`: In `fill-in` (Complete with Past Tense), change "Вранці я ___ каву" to "Мій брат ___ каву".
3.  Ensure all "Я/Ти" questions have context cues (e.g., "(female speaker)") OR use 3rd person subjects to avoid ambiguity.

### Educational / Plan Alignment: 7/10 → 9/10
**What to fix:**
1.  `21-yesterday-past-tense.md`: In section "Key Verbs in Past Tense", add rows for:
    -   `ходити` | `ходив` | `ходила` | `ходили` | `was walking/going`
    -   `спати` | `спав` | `спала` | `спали` | `was sleeping`
2.  `21-yesterday-past-tense.md`: In "Summary", explicitly mention `йти` (to go) in the irregular verbs list with its full forms if it's required by plan, or better, move it to the Presentation section as a "Special Verb" note.

### Projected Overall After Fixes
New Weighted Score: ~9.2/10

## Verdict

**FAIL**

Blocking issues:
1.  **Data Integrity**: Vocabulary file defines a verb as a "vein".
2.  **Activity Logic**: Gender-ambiguous questions penalize correct answers.
3.  **Plan Compliance**: Missing required verbs in instruction.

Fix these 3 issues to pass.