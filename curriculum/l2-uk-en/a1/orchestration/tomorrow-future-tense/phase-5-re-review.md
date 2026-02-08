# Рецензія: Tomorrow - Future Tense

**Level:** A1 | **Module:** 22
**Overall Score:** 8.6/10
**Status:** FAIL
**Reviewed:** 2026-02-08

## Plan Verification

Plan-Content Alignment: [FAIL]
- Sections: [missing "Practice 2" / explicit "telling about own plans" section]
- Vocabulary: [FAIL - Vocabulary YAML file is missing almost all required words. Content uses them, but YAML is incomplete.]
- Grammar scope: [FAIL - "спробую" and "постараюся" (Perfective Future) used in activities but strictly out of scope for A1 M22.]
- Objectives: [PASS]

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Clear explanations, good use of formatting. |
| 2 | Coherence | 9/10 | <7 | Logical progression from conjugation to context. |
| 3 | Relevance | 10/10 | <7 | Future tense is essential communication. |
| 4 | Educational | 9/10 | <7 | Good handling of the Aspect distinction warning. |
| 5 | Language | 9/10 | <8 | Natural sentences, though one minor unnatural imperfective usage ("буду дзвонити"). |
| 6 | Pedagogy | 8/10 | <7 | Good PPP, but activity ambiguity lowers score. |
| 7 | Immersion | 8/10 | <6 | Good amount of examples. |
| 8 | Activities | 6/10 | <7 | **FAIL**: Ambiguous fill-in items (multiple correct answers); Scope creep (perfective future forms). |
| 9 | Richness | 5/10 | <6 | **FAIL**: Vocabulary YAML is practically empty (6 items vs ~20 in plan). |
| 10 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5. Very approachable. |
| 11 | LLM Fingerprint | 9/10 | <7 | Feels structured and clean. |
| 12 | Linguistic Accuracy | 10/10 | <9 | Grammar is correct. |

**Weighted Overall:** (9*1.5 + 9*1 + 10*1 + 9*1.2 + 9*1.1 + 8*1.2 + 8*1 + 6*1.3 + 5*0.9 + 9*1.3 + 9*1 + 10*1.5) / 14.0 = **120.5 / 14.0 = 8.61**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [FAIL] - Use of "спробую", "постараюся" (Perfective Future) in activities without explanation.
- Activity errors: [FAIL] - Multiple valid answers in "Planning Expressions" fill-in.
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Empty Vocabulary File
- **Location**: `vocabulary/22-tomorrow-future-tense.yaml`
- **Original**: File contains only 6 items (`весна`, `побачитися`, etc.).
- **Problem**: Missing ALL core plan words: `завтра`, `буду`, `наступний`, `план`, `хотіти`, `збиратися`, `незабаром`, `потім`, `тиждень`, `рік`, `сподіватися`, `мріяти`, `планувати`, `обіцяти`.
- **Fix**: Populate the vocabulary YAML with all words listed in the Plan and used in the Content.

### Issue 2: Ambiguous Fill-in Activities
- **Location**: `activities/22-tomorrow-future-tense.yaml` - "Planning Expressions"
- **Original**: "Я ___ поїхати до Києва наступного місяця." (Options: планую, мрію, обіцяю, сподіваюся)
- **Problem**: Grammatically and semantically, ALL options fit. "I dream to go", "I promise to go", "I hope to go", "I plan to go". Without context, this is a guessing game.
- **Fix**: Adjust options to be mutually exclusive grammatically (e.g. use different cases if applicable, though here infinitives work for all) or semantically (make distractors obviously wrong contextually). Or provide English cue: "I ___ (plan) to go...".

### Issue 3: Grammar Scope Creep in Activities
- **Location**: `activities/22-tomorrow-future-tense.yaml` - "Levels of Certainty"
- **Original**: Items include `спробую`, `постараюся`.
- **Problem**: These are **Perfective Future** forms (Simple Future). The lesson explicitly focuses on **Compound Future** (буду + inf) and says perfective future is coming in A2. Testing students on untaught morphology is unfair.
- **Fix**: Remove these items or replace with compound forms (e.g., `буду пробувати`) or intention verbs (`хочу спробувати`).

### Issue 4: Slightly Unnatural Imperfective
- **Location**: `activities/22-tomorrow-future-tense.yaml` - Unjumble item 12
- **Original**: "Я буду дзвонити тобі пізніше"
- **Problem**: "I will be calling you later" (process). A simple promise "I will call you later" is usually perfective "Я подзвоню тобі пізніше". While "буду дзвонити" isn't wrong, it sounds like "I will be in the process of calling you".
- **Fix**: Change to a verb where process is more natural, e.g., "Я буду працювати пізніше" or accept it as a pedagogical simplification (but be aware). Suggested replacement: "Я буду писати тобі" (I will be writing to you) or stick to clearly duration-based verbs.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Act 12 | Я буду дзвонити тобі пізніше | Я буду працювати пізніше / Я подзвоню (A2) | Naturalness |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? [Pass]
- Instructions clear? [Pass]
- Quick wins? [Pass]
- Ukrainian scary? [Pass]
- Come back tomorrow? [Pass]

## Strengths
- Excellent explanation of the "Aspect Awareness" to prevent confusion.
- Clear, structured conjugation tables.
- Good integration of IPA.

## Fix Plan to Reach 9/10

### Activities: 6/10 → 9/10

**What to fix:**
1. **Ambiguity**: In "Planning Expressions" fill-in, add English cues to the sentences (e.g., "Я ___ (plan) поїхати...") OR change distractors to verbs that don't take infinitive (e.g., nouns or adverbs).
2. **Scope**: In "Levels of Certainty" group-sort, remove `спробую` and `постараюся`. Replace with `хочу` (want) or `маю намір` (intend) if not already there, or just reduce item count.
3. **Naturalness**: In "Future Plans" unjumble, change "Я буду дзвонити тобі пізніше" to "Я буду працювати пізніше" or "Ми будемо обідати пізніше" to avoid the perfective/imperfective friction.

### Richness: 5/10 → 10/10

**What to fix:**
1. **Vocabulary YAML**: Run a full sync. Add: `завтра`, `післязавтра`, `наступний`, `скоро`, `потім`, `планувати`, `мріяти`, `сподіватися`, `обіцяти`, `вирішити`, `хотіти`, `збиратися`, `незабаром`. Ensure IPA and translations are present.

### Content Alignment
1. Add a small "Practice 2" section or a `> [!speaking]` callout at the end prompting the student: "Tell us 3 things you will do tomorrow using 'Я буду...'". This satisfies the Plan's "Розповідь про свої плани на завтра".

## Verdict

**FAIL**

Blocking issues: **Empty Vocabulary File** (Major data integrity issue) and **Ambiguous Activities** (Pedagogical failure). Fixing the vocabulary file and tightening the activity logic will easily push this to a Pass.