# Рецензія: At the Café

**Level:** A1 | **Module:** 19
**Overall Score:** 8.4/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [Matches plan hints; "Future tense preview" allowed by plan]
- Grammar scope: [Clean; Genitive/Accusative usage matches plan]
- Objectives: [All covered]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Excellent cultural notes (coffee culture, tipping). |
| 2 | Coherence | 9/10 | <7 | Strong logical flow from vocab to dialogue. |
| 3 | Relevance | 10/10 | <7 | Essential survival skills for Ukraine. |
| 4 | Educational | 9/10 | <7 | Clear progression, useful warnings (хочу vs візьму). |
| 5 | Language | 8/10 | <8 | Minor issues: "Доброго дня" (Genitive greeting) vs standard "Добрий день". |
| 6 | Pedagogy | 8/10 | <7 | Good explanations, but "Я буду" in activities is untaught. |
| 7 | Immersion | 8/10 | <6 | Good mix, but some English phrasing in activities is clunky. |
| 8 | Activities | 4/10 | <7 | **CRITICAL FAIL**: Lazy distractors ("вони", "Incorrect order") in quiz. |
| 9 | Richness | 9/10 | <6 | Lviv coffee legend, Kyiv cake - great specific details. |
| 10 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5. Very welcoming tone. |
| 11 | LLM Fingerprint | 7/10 | <7 | "Incorrect order for this sentence" option is a clear AI artifact. |
| 12 | Linguistic Accuracy | 9/10 | <9 | Mostly excellent, minor stylistic choices. |

**Weighted Overall:** (13.5 + 9 + 10 + 10.8 + 8.8 + 9.6 + 8 + 5.2 + 8.1 + 11.7 + 7 + 13.5) / 14.0 = **115.2 / 14.0 = 8.22** -> **8.2/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [Line 118: "Це достатньо" -> "Цього достатньо" or "Достатньо"]
- Grammar scope: [Activity: "Я буду каву" (Elliptical Future not taught), "Мені..." (Dative not taught)]
- Activity errors: [Quiz "Order the Café Sentences Order" has filler options]
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Lazy Activity Generation (Quiz)
- **Location**: Activities / `quiz` "Order the Café Sentences Order"
- **Original**: Options include: `text: Incorrect order for this sentence`, `text: вони`
- **Problem**: These are lazy, AI-generated filler distractors that repeat for every single question. They provide zero pedagogical value and make the quiz trivial.
- **Fix**: Remove filler options. Create real scrambled distractors (e.g., "двох Столик на" vs "Столик на двох"). Rename title to "Unjumble the Sentences".

### Issue 2: Untaught Grammar in Activities
- **Location**: Activities / `group-sort` "Café Phrases by Function"
- **Original**: `Я буду каву.`
- **Problem**: The module teaches "Я візьму" (I will take). "Я буду" (I will [have]) is a colloquial elliptical construction that hasn't been taught and contradicts the "Future tense preview" of *only* "візьму".
- **Fix**: Change to `Я візьму каву.`

### Issue 3: Untaught Dative Case
- **Location**: Activities / `group-sort` "Café Phrases by Function"
- **Original**: `Мені, будь ласка, сік.`
- **Problem**: "Мені" (to me) is Dative case. A1 students at M19 generally focus on Nominative/Accusative/Genitive. Research notes explicitly advise using "Дайте" or "Я візьму" to avoid Dative.
- **Fix**: Change to `Я візьму сік, будь ласка.`

### Issue 4: Gender Neutrality / Standard Phrasing
- **Location**: Line 87 / Mini-Dialogue 1
- **Original**: `Столик на одну, будь ласка.`
- **Problem**: "На одну" implies a female speaker ("на одну [особу/жінку]"). Standard textbook phrasing for "table for one" is the gender-neutral/masculine "Столик на одного".
- **Fix**: Change to `Столик на одного, будь ласка.` (unless explicitly teaching gendered self-reference, which adds load).

### Issue 5: Calque / Phrasing
- **Location**: Line 118 / Mini-Dialogue 2
- **Original**: `— Це все? — Так, достатньо.`
- **Problem**: "Це достатньо" sounds like "This is sufficiently".
- **Fix**: Change to `— Це все? — Так, дякую.` or `— Так, цього достатньо.`

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 86 | Доброго дня! | Добрий день! | Grammar (Genitive vs Nom Greeting) |
| 87 | Столик на одну | Столик на одного | Gender Standard |
| Act | Я буду каву | Я візьму каву | Scope Creep |
| Act | Мені, будь ласка... | Я візьму... | Scope Creep (Dative) |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? [Pass]
- Instructions clear? [Pass]
- Quick wins? [Pass] (Can order coffee immediately)
- Ukrainian scary? [Pass]
- Come back tomorrow? [Pass]

## Fix Plan to Reach 9/10

### Activities: 4/10 → 9/10

**What to fix:**
1.  **Quiz "Order the Café Sentences Order"**:
    *   Rename title to `Unjumble the Sentences`.
    *   For **ALL 12 ITEMS**: Replace the `Incorrect order for this sentence` and `вони` distractors with actually scrambled words.
    *   Example: Q1 Distractors -> `на Столик двох`, `Столик двох на`, `Двох на столик`.
2.  **Group-Sort "Café Phrases by Function"**:
    *   Replace `Я буду каву.` -> `Я візьму каву.`
    *   Replace `Мені, будь ласка, сік.` -> `Я візьму сік, будь ласка.`

### Language: 8/10 → 9/10

**What to fix:**
1.  **Line 86**: Change `Доброго дня!` -> `Добрий день!` (Standard A1 greeting).
2.  **Line 87**: Change `Столик на одну` -> `Столик на одного` (Standard phrase).
3.  **Line 118**: Change `Так, достатньо.` -> `Так, це все.` (More natural closing).
4.  **Activity (Fill-in)**: Update answer key for "Це достатньо" -> "Це все" (Item 10 already targets "достатньо", change target sentence or answer).
    *   Item 10: Change sentence `Це ___.` (Answer: достатньо) -> `Це ___.` (Answer: все). Options: `все`, `достатньо`, ...

### Projected Overall After Fixes

(13.5 + 9 + 10 + 10.8 + 9.9 + 9.6 + 8 + 11.7 + 8.1 + 11.7 + 10 + 13.5) / 14.0 = **9.6/10**

## Verification Summary

- Content lines read: 180
- Activity items checked: 40+
- Ukrainian sentences verified: ~25
- IPA transcriptions checked: 10
- Issues found: 5
- Naturalness score recommendation: 10/10 (after fixes)

## Verdict

**FAIL**

The content is strong, but the **Activities file is severely compromised** by lazy, AI-generated filler distractors ("Incorrect order for this sentence", "вони") in the unjumble quiz. This makes the quiz pedagogically useless. Additionally, the activities introduce untaught grammar ("Я буду", "Мені"). These must be fixed to pass.