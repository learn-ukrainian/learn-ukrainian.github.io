# Рецензія: The Accusative II: People

**Level:** A1 | **Module:** 12
**Overall Score:** 7.5/10
**Status:** FAIL
**Reviewed:** 2026-02-08

## Plan Verification

```
Plan-Content Alignment: [FAIL]
- Sections: [Unable to verify - Plan file missing]
- Vocabulary: [FAIL - Significant gap: words in text/activities not in vocab file]
- Grammar scope: [FAIL - Plural Accusative used in dialogue]
- Objectives: [Pass - Animate accusative concept covered well]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Clear explanations, good flow, but hindered by vocab gaps. |
| 2 | Coherence | 8/10 | <7 | Logical progression, but "колега" usage contradicts the presented rules. |
| 3 | Relevance | 9/10 | <7 | Very useful topic for A1. |
| 4 | Educational | 6/10 | <7 | Missing explanation for masculine nouns ending in -a (колега); vocab gaps. |
| 5 | Language | 9/10 | <8 | Natural Ukrainian, correct grammar (except scope creep). |
| 6 | Pedagogy | 6/10 | <7 | Unexplained grammar exception ("колега"); Scope creep ("пасажирів"). |
| 7 | Immersion | 8/10 | <6 | Good amount of Ukrainian text and dialogues. |
| 8 | Activities | 6/10 | <7 | Lazy distractors ("вони") in unjumbles; testing untaught vocabulary. |
| 9 | Richness | 8/10 | <6 | Good cultural context (professions), proverbs. |
| 10 | Beginner Safety | 6/10 | <7 | "Колега" confusion (masc noun, fem endings) without explanation is a trap. |
| 11 | LLM Fingerprint | 7/10 | <7 | Repetitive distractors in activities; formulaic structure. |
| 12 | Linguistic Accuracy | 10/10 | <9 | The Ukrainian itself is grammatically correct. |

**Weighted Overall:** (12 + 8 + 9 + 7.2 + 9.9 + 7.2 + 8 + 7.8 + 7.2 + 7.8 + 7 + 15) / 14.0 = **7.64/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [FAIL] - Line 129: "пасажирів" (Genitive/Accusative Plural) is Level A2+.
- Activity errors: [FAIL] - Testing vocabulary not present in the module (продавець, менеджер, etc.).
- Beginner safety: 3/5 (Confusion on "колега", missing vocab)

## Critical Issues Found

### Issue 1: Grammar Scope Creep (Plural)
- **Location**: Line 129 / Mini-Dialogue 2
- **Original**: "Він возить **пасажирів** до центру."
- **Problem**: "пасажирів" is Accusative Plural (Animate). Module 12 covers Singular. Plural declension is a much later topic.
- **Fix**: Change to singular or a lexicalized phrase. "Він возить **клієнтів**" is also plural. Better: "Він возить **директора**" (singular) or "Він працює водієм". Simple fix: "Він возить **людей**" (if "люди" is known) or just "Він — водій таксі". Let's use singular animate: "Він возить **шефа**" (boss).

### Issue 2: Pedagogical Trap ("Колега")
- **Location**: Throughout text (Line 71, 76, 116) and Dialogue 1
- **Original**: "Вона знає мого колегу." / "Він мій колега"
- **Problem**: The text explicitly teaches that masculine animate nouns take -а/-я (implicitly assuming consonant/soft sign ending) or -о -> -а. It mentions Feminine nouns take -у. "Колега" is a masculine noun ending in -а. It declines like a feminine noun (Acc: колегу) but takes masculine adjectives (Acc: мого). This contradicts the simplified rules presented and confuses learners ("Is it feminine? Why 'мого'?").
- **Fix**: Add a specific "Grammar Note" box about Masculine Nouns ending in -a (like колега, Микола, тато - wait, тато is -o). OR replace "колега" with a regular masculine noun like "друг" or "студент" in the early examples to avoid confusion, introducing "колега" only with a note.

### Issue 3: Missing Vocabulary
- **Location**: Text & Activities
- **Original**: Words used: колега, офіціант, директор, гість, дядько, продавець, менеджер.
- **Problem**: These words are used in examples, dialogues, and activities but are NOT in the vocabulary file (`12-the-accusative-ii-people.yaml`) nor introduced in a table.
- **Fix**: Add these words to the vocabulary file.

### Issue 4: Lazy Activity Distractors
- **Location**: Activities file, `unscramble` items (last 2 activities)
- **Original**: Distractor "вони" used for EVERY single item.
- **Problem**: This is lazy LLM generation. It makes the activity too easy (just remove "вони") and boring.
- **Fix**: Use relevant words as distractors (e.g., incorrect case forms like "студент" vs "студента").

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 129 | пасажирів | пасажира / людей | Scope (Plural) |

## Beginner Safety Audit

"Would I Continue?" Test: 3/5
- Overwhelmed? **Fail** (Encountering "колегу" without knowing why it looks feminine but is masculine)
- Instructions clear? **Pass**
- Quick wins? **Pass**
- Ukrainian scary? **Fail** (Hidden rules not explained)
- Come back tomorrow? **Pass** (Content is interesting)

## Fix Plan to Reach 9/10

### Educational & Pedagogy: 6/10 → 9/10

**What to fix:**
1.  **Add Grammar Note**: Insert a `> [!note]` box after "Masculine Nouns Ending in -о" titled "Masculine Nouns Ending in -a".
    - Content: "Some masculine nouns end in **-а** (like **колега** - colleague). They decline just like feminine nouns (**-а** → **-у**), but they are still masculine! Example: **мій** колега (Nom) → **мого** колег**у** (Acc)."
2.  **Fix Scope Creep**: Line 129. Change "Він возить **пасажирів**" to "Він возить **директора**" (He drives the director) or "Він возить **людей**" (people - common irreg plural, acceptable as set phrase) or "Він часто возить **гостей**" (guests). Best to stick to singular animate to practice the rule: "Він возить **президента**" (fun!) or "Він возить **мого тата**". Let's go with "Він возить **людей**" (common concept) or change sentence to "Він **водій таксі**".
    - Replacement: "Він возить **людей**." (safest natural) or "Він возить **туристів**" (plural again).
    - Strict Singular Fix: "Він возить **свого шефа**." (He drives his boss).
3.  **Vocabulary**: Add the missing 7-8 nouns to the vocabulary YAML.

### Activities: 6/10 → 9/10

**What to fix:**
1.  **Fix Distractors**: In `activities/12-the-accusative-ii-people.yaml`, update the `quiz` (unscramble/order) items. Remove the generic "вони" distractor.
    - Instead of just `["text", "distractor"]` format, usually these are `unjumble`.
    - Wait, the file uses `type: quiz` with `options` for ordering?
    - `question: 'Correct sentence order for: "I see the student..."'`
    - `options: [{text: "Я бачу студента...", correct: true}, {text: "бачу Я...", correct: false}, {text: "Incorrect order...", correct: false}, {text: "вони", correct: false}]`
    - This is a weird format for "Order the sentence". Usually it's `unjumble`.
    - **Action**: Change these to `type: unjumble` OR improve the distractors in the `quiz` format to be case-based. e.g. "Я бачу студент..." (wrong case).
    - Since I cannot edit the yaml structure deeply without risk, I suggest **replacing the lazy distractors** in the text-based quiz with case errors.
    - E.g. Option 1: "Я бачу студента..." (Correct), Option 2: "Я бачу студент..." (Wrong case), Option 3: "Я студента бачу..." (Word order).

### Projected Overall After Fixes

With "колега" explained, vocabulary added, and scope creep fixed:
- Educational: 9/10
- Pedagogy: 9/10
- Activities: 8/10
- Beginner Safety: 9/10
**Projected Score:** ~9.1/10

## Verification Summary

- Content lines read: 172
- Activity items checked: 40+
- Ukrainian sentences verified: 30+
- IPA transcriptions checked: 10
- Issues found: 4 Major (Scope, Pedagogy, Vocab, Activities)

## Verdict

**FAIL**

The module fails on **Grammar Scope** (plural usage) and **Pedagogical Clarity** (the "колега" trap). It also has significant **Vocabulary Gaps** where the text uses words not listed in the vocabulary file. These must be fixed before approval.
