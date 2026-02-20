# Рецензія: Reflexive Verbs (-ся)

**Level:** A1 | **Module:** 9
**Overall Score:** 9.6/10
**Status:** PASS
**Reviewed:** 2026-02-19

## Plan Verification

- **Plan-Content Alignment**: PASS. All sections (Rozmynka, Theory, Practice, Culture) and points are covered.
- **Vocabulary**: PASS. Covers required list (*вмиватися, одягатися, дивитися* etc.).
- **Grammar scope**: PASS. Focuses strictly on present tense and the concept of reflexivity.
- **Objectives**: PASS. All learning objectives addressed.

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 10/10 | <7 | Excellent "Mirror" and "Laser Beam" analogies make the concept intuitive. |
| 2 | Coherence | 10/10 | <7 | Logical progression from concept → form → usage → culture. |
| 3 | Relevance | 10/10 | <7 | Focuses on high-frequency daily routine verbs immediately useful for A1. |
| 4 | Educational | 10/10 | <7 | Clear, scaffolded explanations. "The Myself Redundancy" warning is crucial. |
| 5 | Language | 9/10 | <8 | Natural Ukrainian. Minor note: *підніматися* (to rise) is used for "getting out of bed" to fit the reflexive theme, where *вставати* might be more common, but it's acceptable. |
| 6 | Pedagogy | 9/10 | <7 | Strong scaffolding. One error in activity explanation regarding phonetics rules. |
| 7 | Immersion | 10/10 | <6 | Perfect balance for A1. Heavy English support for complex concepts. |
| 8 | Activities | 9/10 | <7 | Good variety (Sort, Match, Quiz, Fill-in). One factual error in the "Select Suffix" drill explanation. |
| 9 | Richness | 9/10 | <6 | "Maxim's Morning" story and "Gym Dialogue" provide excellent context. Could use more IPA for key verbs. |
| 10 | Beginner Safety | 10/10 | <7 | Very encouraging tone. "Would I Continue?" test: 5/5. |
| 11 | LLM Fingerprint | 10/10 | <7 | Voice is distinct ("Patient Tutor"), avoids generic AI patterns. |
| 12 | Linguistic Accuracy | 9/10 | <9 | Generally accurate. One explanation about *надіються* is linguistically confused. |

**Weighted Overall:** 9.6/10

## Auto-Fail Checklist Results

- Russianisms: CLEAN. "Вибачаюсь" is handled correctly as a cultural teaching point.
- Calques: CLEAN.
- Grammar scope: CLEAN.
- Activity errors: 1 error found in explanation.
- Beginner Safety: 5/5.

## Critical Issues Found

### Issue 1: False Linguistic Explanation in Activity
- **Location**: `activities/reflexive-verbs.yaml`, Item 6 in "Оберіть правильний суфікс".
- **Original**: `explanation: Після голосної 'ю' у слові 'надіються' (вони) ми вживаємо -ся...`
- **Problem**: This is linguistically incorrect. The form *надіють-ся* attaches *-ся* to the consonant *ть* (part of the ending *-ють*), not to the vowel *ю*. The "Golden Rule" (consonant + ся) applies perfectly here.
- **Fix**: Correct the explanation to state that the word ends in a consonant *ть*.

### Issue 2: Missing IPA for Key Verbs
- **Location**: Content body.
- **Problem**: While `vocabulary.yaml` has IPA, the prompt requires IPA on the "first occurrence" in the text for A1. Key verbs like *вмиватися*, *одягатися*, *зустрічатися* are introduced without inline IPA.
- **Fix**: Add IPA to the main Theory section where these verbs are first defined.

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? No, the pacing is excellent.
- Instructions clear? Yes, English explanations are very clear.
- Quick wins? Yes, the "Mirror" analogy gives an instant "Aha!" moment.
- Ukrainian scary? No, well-scaffolded.
- Come back tomorrow? Yes.

## Strengths
- The **"Laser Beam" and "Mirror" analogies** are fantastic for visualizing the grammar.
- **Cultural insight** on pronunciation (the "Bee" sound) is practical and engaging.
- **"The Myself Redundancy"** is a great proactive correction of a common learner mistake.

## Fix Plan to Reach 10/10

### Pedagogy / Activities
**What to fix:**
1.  `activities/reflexive-verbs.yaml`: Correct the explanation for *надіються*.
2.  `reflexive-verbs.md`: Add inline IPA for the first introduction of key reflexive verbs types.

## Verification Summary

- Content lines read: ~220
- Activity items checked: ~50
- Ukrainian sentences verified: Yes
- IPA transcriptions checked: Yes
- Issues found: 2 (1 Error, 1 Enhancement)

## Verdict

**PASS**

Excellent module that perfectly fits the "Patient Tutor" persona. The content is safe, supportive, and linguistically interesting. One technical error in an activity explanation needs fixing.