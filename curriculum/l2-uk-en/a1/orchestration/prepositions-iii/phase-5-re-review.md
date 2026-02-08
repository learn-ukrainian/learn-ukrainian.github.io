# Рецензія: Prepositions III

**Level:** A1 | **Module:** 30
**Overall Score:** 9.4/10
**Status:** PASS
**Reviewed:** 2026-02-08

## Plan Verification

Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [8/8 from plan used, 6 extra words found (directions)]
- Grammar scope: [minor scope creep in activities (past tense)]
- Objectives: [all covered]

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 10/10 | <7 | Clear, logical flow, good use of humor and "myth busting". |
| 2 | Coherence | 10/10 | <7 | Excellent connection between concepts (Where/Where to/Where from). |
| 3 | Relevance | 10/10 | <7 | Highly practical (asking directions, saying where you're from). |
| 4 | Educational | 10/10 | <7 | Explanations are crystal clear. |
| 5 | Language | 10/10 | <8 | Natural Ukrainian examples. |
| 6 | Pedagogy | 9/10 | <7 | Slight deduction for untaught Past Tense in activities. |
| 7 | Immersion | 9/10 | <6 | Good balance. |
| 8 | Activities | 9/10 | <7 | varied and relevant, but see Scope notes. |
| 9 | Richness | 9/10 | <6 | Good context (City, Dialogues). |
| 10 | Beginner Safety | 9/10 | <7 | Very safe, except for a few past tense verbs in activities. |
| 11 | LLM Fingerprint | 10/10 | <7 | No "robotic" feel. |
| 12 | Linguistic Accuracy | 9/10 | <9 | Minor IPA formatting issues in vocab file. |

**Weighted Overall:** (15 + 10 + 10 + 12 + 11 + 10.8 + 9 + 11.7 + 8.1 + 11.7 + 10 + 13.5) / 14.0 = **9.48/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [Minor violation: Past tense in activities]
- Activity errors: [CLEAN]
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Grammar Scope (Past Tense in Activities)
- **Location**: `activities/30-prepositions-iii.yaml` (fill-in "Де чи Куди?", fill-in "Choose the Preposition")
- **Original**: `___ ти приїхав?`, `___ він повернувся?`, `Ми приїхали ___ Львова.`
- **Problem**: Uses Past Tense (`приїхав`, `повернувся`) which is likely not yet taught or solidified at Module 30 (usually A1.3). Prerequisite list does not include Past Tense.
- **Fix**: Change to Present Tense or simple "to be" constructions.
    - `___ ти приїхав?` -> `___ ти їдеш?` (Where are you coming/driving from?) OR `___ ти?` (Where are you from? - implies origin)
    - `___ він повернувся?` -> `___ він йде?` (Where is he coming from?)
    - `Ми приїхали ___ Львова.` -> `Ми їдемо ___ Львова.` (We are driving from Lviv).

### Issue 2: IPA Formatting in Vocabulary File
- **Location**: `vocabulary/30-prepositions-iii.yaml`
- **Original**: `ipa: /pr'jamo/`, `ipa: /bl'yzko/`, `ipa: /zʋ'idkɪ/`
- **Problem**: Uses `'` as a stress marker and non-standard symbols instead of standard IPA `ˈ` used in the content file (e.g., `/ˈzvidkɪ/`).
- **Fix**: Standardize IPA.
    - `прямо`: `/ˈprjɑmɔ/`
    - `близько`: `/ˈblɪzkɔ/`
    - `звідки`: `/ˈzʋidkɪ/`

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Vocab | /pr'jamo/ | /ˈprjɑmɔ/ | IPA Format |
| Activity | приїхав (past) | їдеш (present) | Scope |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? [Pass]
- Instructions clear? [Pass]
- Quick wins? [Pass] (The "Where/Where to" logic is a huge win)
- Ukrainian scary? [Pass]
- Come back tomorrow? [Pass]

Emotional beats: 4 found
- Welcome: "Let's start! (Let's begin our journey...)"
- Curiosity: "The Three Key Questions" table.
- Quick wins: "Myth vs Fact" section.
- Encouragement: "Це була чудова робота! Ви великі молодці!" in Summary.

## Strengths
- **Conceptual Clarity**: The distinction between Де (Locative), Куди (Acc/Gen), and Звідки (Gen) is explained perfectly with a table.
- **Practicality**: Asking for directions and stating origin are high-value skills.
- **Activity Design**: The "Choose the Preposition" activity cleverly uses case endings (`школи` vs `школу`) to force the correct preposition choice (`до` vs `в`).

## Verification Summary

- Content lines read: ~160
- Activity items checked: ~40
- Ukrainian sentences verified: ~30
- IPA transcriptions checked: ~20
- Issues found: 2 (Scope, IPA format)
- Naturalness score recommendation: 10/10

## Verdict

**PASS**

The content is excellent, linguistically accurate, and pedagogically sound. The score is high (9.4). The only issues are minor scope creep (past tense in activities) and IPA formatting in the vocabulary file, which are easily fixed but do not block approval.