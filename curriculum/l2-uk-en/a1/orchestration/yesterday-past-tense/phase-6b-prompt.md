        # Phase 6b: Apply Prose Fixes

        Read the review below and fix the issues in the content file.

        ## Review

        # Рецензія: Yesterday - Past Tense

**Level:** A1 | **Module:** 21
**Overall Score:** 9.0/10
**Status:** PASS
**Reviewed:** 2026-02-16

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: PASS
- Vocabulary: PASS (All required words present)
- Grammar scope: PASS
- Objectives: PASS
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Very welcoming tone ("Welcome to the Past"), clear "Today vs Yesterday" contrast. |
| 2 | Coherence | 9/10 | <7 | Logical progression from pronouns to verbs to practice. |
| 3 | Relevance | 10/10 | <7 | Perfectly aligned with A1 goals (basic past tense). |
| 4 | Educational | 9/10 | <7 | Clear tables, explicit focus on gender agreement. |
| 5 | Language | 8/10 | <8 | Generally good, but contains a few unnatural calques ("їв сніданок", "був дощ"). |
| 6 | Pedagogy | 8/10 | <7 | Good pacing, but introduces reflexive verb "дивилися" without explaining the reflexive past ending. |
| 7 | Immersion | 10/10 | <6 | 39% immersion is perfect for A1.3. |
| 8 | Activities | 9/10 | <7 | Excellent variety and volume (fill-in, match-up, group-sort, quiz). |
| 9 | Richness | 9/10 | <6 | Good use of Ivan Fedorov history bite. |
| 10 | Beginner Safety | 10/10 | <7 | "Would I Continue?" 5/5. Very safe and encouraging. |
| 11 | LLM Fingerprint | 9/10 | <7 | Narrative feels personal and distinct. |
| 12 | Linguistic Accuracy | 9/10 | <9 | Grammar explanations are accurate. |

**Weighted Overall:** 9.0/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [List] "їв сніданок" (ate breakfast), "був дощ" (was rain).
- Grammar scope: [CLEAN]
- Activity errors: [CLEAN]
- Beginner Safety: 5/5

## Critical Issues Found

### Issue 1: Calque "to eat breakfast"
- **Location**: Section "Практика: Розповідь про вчора", Line 172
- **Original**: «Зранку я пив каву і **їв сніданок**.»
- **Problem**: "Їсти сніданок" is a direct translation of "eat breakfast". The natural Ukrainian verb is "снідати" or phrasing "їв [щось] на сніданок".
- **Fix**: «Зранку я **снідав** і пив каву.»

### Issue 2: Unnatural weather expression
- **Location**: Activities, Group Sort "Past vs Present", Item 6
- **Original**: «Вчора **був дощ**.»
- **Problem**: While understandable, native speakers typically say "падав дощ" or "йшов дощ". "Був дощ" is borderline.
- **Fix**: «Вчора **йшов** дощ.»

### Issue 3: Unexplained Reflexive Verb
- **Location**: Section "The Power of Plural", Line 116
- **Original**: «**Ви дивилися** фільм?»
- **Problem**: The module explains the rule "drop -ти, add -ли". It does NOT explain reflexive verbs (-тися). A student applying the taught rule to "дивитися" would be confused.
- **Fix**: Change to a non-reflexive verb: «**Ви бачили** фільм?» OR add a brief note about reflexive endings.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 172 | «їв сніданок» | «снідав»

        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/yesterday-past-tense.md`

        ## Instructions

        1. Fix issues from the review — word/sentence changes, grammar, clarity
        2. Skip major structural rewrites
        3. After fixing, run IPA lint: `.venv/bin/python scripts/lint_ipa.py /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/yesterday-past-tense.md --fix`
