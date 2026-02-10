# Рецензія: A1 Final Exam

**Level:** A1 | **Module:** 44
**Overall Score:** 8.7/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [All required sections present; "Presentation 3" points integrated into "Comprehensive Test" and "Practice"]
- Vocabulary: [7/8 from plan used; "києво-могилянський" from vocab file missing in text]
- Grammar scope: [Mostly clean; 1 instance of Instrumental case (A2 scope)]
- Objectives: [Met]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Strong narrative arc, clear instructions, celebratory tone. |
| 2 | Coherence | 9/10 | <7 | Logical flow from review to testing to narrative. |
| 3 | Relevance | 10/10 | <7 | Perfectly aligned with A1 final assessment goals. |
| 4 | Educational | 9/10 | <7 | Comprehensive review of key concepts. |
| 5 | Language | 8/10 | <8 | Minor scope creep (Instrumental case); one calque ("Вона має"). |
| 6 | Pedagogy | 9/10 | <7 | Good mix of TTT and narrative consolidation. |
| 7 | Immersion | 8/10 | <6 | Appropriate English scaffolding for an exam context. |
| 8 | Activities | 8/10 | <7 | One grammatical error in Fill-in activity. |
| 9 | Richness | 9/10 | <6 | Varied scenarios and a full narrative. |
| 10 | Beginner Safety | 10/10 | <7 | Encouraging, "Check Yourself" is low-stakes practice. |
| 11 | LLM Fingerprint | 8/10 | <7 | Vocabulary file contains hallucinations (lemmatization errors). |
| 12 | Linguistic Accuracy | 8/10 | <9 | Activity error and metadata errors reduce score. |

**Weighted Overall:** 122.4 / 14.0 = **8.74/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [Line 118: "Вона має багату..."]
- Grammar scope: [Line 104: "зеленим" (Instrumental case - A2)]
- Activity errors: [Activity "Dialogue Completion", Item 10: "Гарних вихідні"]
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Activity Grammar Error
- **Location**: `activities/44-a1-final-exam.yaml` / Type: `fill-in` / Item 10
- **Original**: `sentence: '«— _____ вихідні! — Дякую, навзаєм!»' answer: Гарних`
- **Problem**: This creates the sentence "Гарних вихідні!", which is grammatically incorrect. "Вихідні" is Nominative/Accusative Plural. "Гарних" is Genitive Plural. The phrase is "Гарних вихідних!" (Genitive) or "Гарні вихідні!" (Nominative).
- **Fix**: Change sentence to `'«— _____ вихідних! — Дякую, навзаєм!»'` (keeping answer "Гарних").

### Issue 2: Grammar Scope Creep (Instrumental Case)
- **Location**: Line 104 / Section "Narrative"
- **Original**: "Місто було дуже гарним і зеленим."
- **Problem**: "Зеленим" is Instrumental case. A1 curriculum typically covers only Nom, Acc, Gen, Loc. "Бути" + Instrumental is an A2 pattern.
- **Fix**: Use Nominative for simple A1 description: "Місто було дуже гарне і зелене."

### Issue 3: Calque
- **Location**: Line 118 / Section "Narrative"
- **Original**: "Вона має багату і глибоку історію."
- **Problem**: "Вона має" (She has) is a calque from English "It has".
- **Fix**: "У неї багата і глибока історія."

### Issue 4: Vocabulary File Hallucinations
- **Location**: `vocabulary/44-a1-final-exam.yaml`
- **Original**: `lemma: зеленити` (verb), `lemma: світило` (noun)
- **Problem**:
    - "Світило" in text is a verb ("Сонце світило" - shone), not a noun.
    - "Зеленити" (to make green) is not in text; "зеленим" (adjective) is.
    - "Києво-могилянський" is in the vocab file but MISSING from the text.
- **Fix**: Regenerate vocabulary file. Remove `зеленити`, `світило` (noun), `києво-могилянський`. Ensure `світити` (verb) is listed if desired.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 104 | "Місто було дуже гарним і зеленим" | "Місто було дуже гарне і зелене" | Scope (Instrumental) |
| 118 | "Вона має багату... історію" | "У неї багата... історія" | Calque |
| Act | "Гарних вихідні" | "Гарних вихідних" | Grammar |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? [No]
- Instructions clear? [Yes]
- Quick wins? [Yes - "Check Yourself"]
- Ukrainian scary? [No]
- Come back tomorrow? [Yes - "A2 will open up new worlds"]

Emotional beats: 4 found
- Welcome: Line 3 "Вітаємо!"
- Curiosity: Line 13 "Myth Buster"
- Quick wins: Line 65 "Check Yourself"
- Encouragement: Line 90 "Keep Learning"

## Strengths
- Excellent use of the "Final Exam" framing to celebrate progress rather than intimidate.
- The "Narrative: My First Trip" effectively consolidates vocabulary from previous modules (Cafe, Transport, City).
- "Check Yourself" interaction is a great low-stakes confidence builder.

## Fix Plan to Reach 9/10 (REQUIRED)

### Language: 8/10 → 9/10
**What to fix:**
1. Line 104: Change "Місто було дуже гарним і зеленим." → "Місто було дуже гарне і зелене." — Removes out-of-scope Instrumental case.
2. Line 118: Change "Вона має багату і глибоку історію." → "У неї багата і глибока історія." — Improves naturalness.

### Activities: 8/10 → 10/10
**What to fix:**
1. `activities/44-a1-final-exam.yaml`: Item 10 of "Dialogue Completion". Change sentence to `«— _____ вихідних! — Дякую, навзаєм!»` — Fixes grammar error.

### LLM Fingerprint: 8/10 → 10/10
**What to fix:**
1. `vocabulary/44-a1-final-exam.yaml`: Delete `зеленити`, `світило`, `києво-могилянський`. Add correct lemmas if needed (`зелений`, `світити`).

### Projected Overall After Fixes
(9*1.5 + 9*1 + 10*1 + 9*1.2 + 9*1.1 + 9*1.2 + 8*1 + 10*1.3 + 9*0.9 + 10*1.3 + 10*1 + 9*1.5) / 14.0 = **9.25/10**

## Verification Summary
- Content lines read: ~140
- Activity items checked: ~50
- Ukrainian sentences verified: ~40
- IPA transcriptions checked: 2 (Present in text)
- Issues found: 4 (1 Activity, 2 Content, 3 Vocab Metadata)
- Naturalness score recommendation: 9/10 (after fixes)

## Verdict

**FAIL**

The module is structurally sound and educationally effective, but it contains a functional grammatical error in the activities ("Гарних вихідні"), a scope violation (Instrumental case), and garbage data in the vocabulary file. These must be fixed to meet the V4 standard.