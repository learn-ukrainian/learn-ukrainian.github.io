# Рецензія: Questions & Negation

**Level:** A1 | **Module:** 7
**Overall Score:** 8.1/10
**Status:** FAIL
**Reviewed:** 2026-02-18

## Plan Verification

```
Plan-Content Alignment: FAIL
- Sections: PASS
- Vocabulary: FAIL (Table in Markdown is effectively empty, missing 95% of words)
- Grammar scope: PASS
- Objectives: PASS
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Engaging tone, but slightly overdramatic metaphors. |
| 2 | Coherence | 9/10 | <7 | Logical flow from concepts to practice. |
| 3 | Relevance | 10/10 | <7 | Essential core grammar (questions/negation). |
| 4 | Educational | 9/10 | <7 | Clear explanations of "Do-support" absence. |
| 5 | Language | 9/10 | <8 | Natural examples, good spoken/written distinction. |
| 6 | Pedagogy | 8/10 | <7 | Good progression, but ALF quote introduces complex grammar unexplained. |
| 7 | Immersion | 10/10 | <6 | 34% is ideal for A1.1. |
| 8 | Activities | 9/10 | <7 | Excellent variety and relevance. |
| 9 | Richness | 4/10 | <6 | **Critical Fail:** Vocabulary table is empty (1 word). |
| 10 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 4/5. Encouraging. |
| 11 | LLM Fingerprint | 6/10 | <7 | **Fail:** High metaphor density ("spices", "ping-pong", "wall/shield"). |
| 12 | Linguistic Accuracy | 9/10 | <9 | No obvious errors found. |

**Weighted Overall:** (8*1.5 + 9*1.0 + 10*1.0 + 9*1.2 + 9*1.1 + 8*1.2 + 10*1.0 + 9*1.3 + 4*0.9 + 8*1.3 + 6*1.0 + 9*1.5) / 14.0 = **8.1/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [CLEAN]
- Beginner Safety: 4/5

## Critical Issues Found

### Issue 1: Missing Vocabulary Table
- **Location**: Section "Vocabulary" (End of file)
- **Original**: Table contains only one row: `| дієслово | | verb | ... |`
- **Problem**: The module introduces ~20 key words (чи, не, ні, так, хто, що, де, коли, etc.) which are listed in the plan and YAML, but missing from the student-facing Markdown table. This breaks the "Vocabulary scope" requirement and makes the module incomplete for study.
- **Fix**: Populate the Markdown table with all 20 vocabulary items.

### Issue 2: LLM Fingerprint (Metaphor Density)
- **Location**: Throughout the text
- **Original**:
    - "Conversation is a two-way street."
    - "Think of **Ні** as a wall... and **не** as a shield..."
    - "Intonation is not just decoration; it is punctuation you can hear."
    - "Conversation is like ping-pong."
    - "питання та заперечення — це спеції мови."
- **Problem**: 5+ distinct metaphors in one module triggers the "Metaphor density test" (<7). It feels artificially "writerly" rather than like a clear, direct tutor.
- **Fix**: Remove 2-3 metaphors. Simplify the Conclusion and Intro.

### Issue 3: Advanced Grammar in Cultural Hook (ALF)
- **Location**: Section "Культурний гачок: Легендарний АЛЬФ"
- **Original**: «Ти не любиш котів? Ти просто не вмієш їх готувати!»
- **Problem**: This quote uses Genitive Plural (`котів`) and Accusative/Genitive pronoun (`їх`), which are A2/B1 concepts. A beginner might be confused why it's not `коти` or `вони`.
- **Fix**: Add a small footnote or `[!note]` saying: "Don't worry about the word endings here just yet—focus on the meaning!" to preserve Beginner Safety.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| N/A | N/A | N/A | N/A |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? [Pass]
- Instructions clear? [Pass]
- Quick wins? [Pass]
- Ukrainian scary? [Borderline] (ALF quote is complex)
- Come back tomorrow? [Pass]

## Strengths
- **"Do" Trap Explanation**: The distinction between English "Do" and Ukrainian verb structure is explained perfectly for English speakers.
- **Intonation Visuals**: The advice to "draw the line" or "raise eyebrows" is excellent practical pedagogy.
- **Cultural Context**: The distinction between standard «що» and spoken «шо» is pragmatic and authentic.

## Fix Plan to Reach 9/10

### Richness: 4/10 → 10/10
**What to fix:**
1. **Vocabulary Table**: Add the missing 19 rows (чи, не, ні, так, хто, що, де, коли, чому, як, скільки, куди, завжди, ніколи, зазвичай, знати, розуміти, сирник, смачно, звичайно).

### LLM Fingerprint: 6/10 → 9/10
**What to fix:**
1. **Intro**: Change "Conversation is a two-way street..." to something simpler like "Conversation requires questions, not just statements."
2. **Conclusion**: Remove "питання та заперечення — це спеції мови." Just say "Questions allow you to be an active participant."

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. **ALF Section**: Add `> [!tip] Grammar Note: Don't worry about the form 'котів' (cats) yet. Just enjoy the phrase!`

**Expected score after fix:** 9.5/10

### Projected Overall After Fixes
```
(8*1.5 + 9*1.0 + 10*1.0 + 9*1.2 + 9*1.1 + 9*1.2 + 10*1.0 + 9*1.3 + 10*0.9 + 9*1.3 + 9*1.0 + 9*1.5) / 14.0 = 9.1/10
```

## Verification Summary

- Content lines read: 352
- Activity items checked: 45
- Ukrainian sentences verified: ~40
- IPA transcriptions checked: 20
- Issues found: 3 (1 Critical)

## Verdict

**FAIL**

The module is pedagogical sound and engaging, but the **Vocabulary Table is effectively empty**, missing almost all the words taught in the lesson. This is a critical structural failure. Additionally, the text suffers from **excessive metaphorical density** (LLM fingerprint), making it feel artificial. These must be fixed before passing.
