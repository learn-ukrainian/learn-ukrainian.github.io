        # Phase 6b: Apply Prose Fixes

        Read the review below and fix the issues in the content file.

        ## Review

        # Рецензія: Describing Things - Adjectives

**Level:** A1 | **Module:** 26
**Overall Score:** 8.9/10
**Status:** PASS
**Reviewed:** 2026-02-16

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: Matches plan exactly.
- Vocabulary: 12/8 required (includes required + recommended).
- Grammar scope: PASS (Covers hard/soft groups).
- Objectives: PASS (All addressed).
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Very supportive tone ("Ми гуляємо Києвом...", "Не бійтеся..."). Clear structure. |
| 2 | Coherence | 9/10 | <7 | Logical progression from gender basics to specific adjective types. |
| 3 | Relevance | 10/10 | <7 | Essential vocabulary (good/bad/new/old) used in practical "Real Estate" context. |
| 4 | Educational | 9/10 | <7 | "Bricks and Pillows" mnemonic is excellent for A1. |
| 5 | Language | 8/10 | <8 | **Major IPA Error**: systematic misuse of `[tʃ]` for "ц". |
| 6 | Pedagogy | 9/10 | <7 | Strong PPP structure. Clear explanations. |
| 7 | Immersion | 10/10 | <6 | 54% is perfect for A1.3 (Target 35-55%). |
| 8 | Activities | 10/10 | <7 | Excellent density (10 activities) and variety. |
| 9 | Richness | 8/10 | <6 | "Symbol and pride" phrase is slightly unnatural/abstract for A1. |
| 10 | Beginner Safety | 8/10 | <7 | Introduction of undefined word "вечірній" in mnemonic section. |
| 11 | LLM Fingerprint | 8/10 | <7 | "In this module, you learned...", "Size matters" cliche. |
| 12 | Linguistic Accuracy | 8/10 | <9 | IPA transcription errors affect accuracy score. |

**Weighted Overall:** 8.86/10 = **8.9/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [CLEAN]
- Beginner Safety: 4/5 (Scope creep with "вечірній")

## Critical Issues Found

### Issue 1: IPA Transcription Error (Systematic)
- **Location**: Multiple lines (Sections 1, 3, 4, 5)
- **Original**: «Це» transcribed as `[tʃɛ]`; «Цікавий» as `[tʃiˈkɑʋɪj]`; «Цей» as `[tʃɛj]`
- **Problem**: `tʃ` represents the sound "ч" (ch), not "ц" (ts). "Це" should be `[t͡sɛ]`. Using `[tʃɛ]` teaches students to say "Che" instead of "Tse".
- **Fix**: Replace all instances of `tʃ` corresponding to letter "ц" with `t͡s` (or `ts`).
    - `[tʃɛ]` → `[t͡sɛ]`
    - `[tʃiˈkɑʋɪj]` → `[t͡sʲiˈkɑʋɪj]`
    - `[tʃɛj]` → `[t͡sɛj]`
    - `[tʃiˈkɑʋɛ]` → `[t͡sʲiˈkɑʋɛ]`

### Issue 2: Scope Creep (Undefined Vocabulary)
- **Location**: Section "Mnemonic: Bricks and Pillows"
- **Original**: «Слова синій, **вечірній** — м'які.»
- **Problem**: The word "вечірній" (evening - adj) appears here for the first time without translation or context. It is not in the vocabulary list. This adds unnecessary cognitive load for a simple mnemonic example.
- **Fix**: Use a known word if possible, or gloss it immediately: «...синій, вечірній (evening)...», or simply remove it and just use «синій». Recommended: Remove «вечірній» to keep focus on the

        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/describing-things-adjectives.md`

        ## Instructions

        1. Fix issues from the review — word/sentence changes, grammar, clarity
        2. Skip major structural rewrites
        3. After fixing, run IPA lint: `.venv/bin/python scripts/lint_ipa.py /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/describing-things-adjectives.md --fix`
