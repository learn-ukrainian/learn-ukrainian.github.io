# Phase 5: Critical Deep Review

> **You are executing Phase 5 of an orchestrated rebuild.**
> **Your ONLY task: Perform a rigorous, evidence-based review.**
> **Every score must be backed by specific findings. Every finding must cite a line number.**

## Files to Read (ALL REQUIRED)

Read ALL of these files from disk before writing anything:

1. **Content** (the lesson you're reviewing): `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/08-the-living-verb-ii.md`
2. **Activities**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/08-the-living-verb-ii.yaml`
3. **Vocabulary**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/08-the-living-verb-ii.yaml`
4. **Plan** (source of truth for scope): `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/08-the-living-verb-ii.yaml`
5. **Meta** (build config): `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/meta/08-the-living-verb-ii.yaml`
6. **Research notes** (if exists): `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/the-living-verb-ii-research.md`

**Do not proceed until you have read every line of the content and every activity item.**

## Audit Metrics (Facts from Claude)

```
Word count:       994 / 972 (102%%)
Activities:       8
Vocabulary items: 0
Engagement boxes: 8
Immersion:        ?% (target: 10-25% (M08))
Audit status:     PASS
```

---

## STEP 1: PLAN VERIFICATION

Cross-check content against the plan file:

1. **Outline compliance**: Is every section from `content_outline` present as an H2/H3?
2. **Vocabulary scope**: List every Ukrainian vocabulary word taught in the content. Compare against `vocabulary_hints.required` in the plan. Flag any word NOT in the plan.
3. **Grammar scope**: What grammar does this module teach? What grammar from LATER modules appears in examples or dialogues? (This is scope creep — flag it.)
4. **Objectives**: Are all learning objectives from the plan addressed in the content?

Report findings as:
```
Plan-Content Alignment: [PASS/FAIL]
- Sections: [all present / missing: X, Y]
- Vocabulary: [X/Y from plan used, Z extra words found]
- Grammar scope: [clean / scope creep: specific items]
- Objectives: [all covered / missing: X]
```

---

## STEP 2: DEEP VERIFICATION (Line by Line)

### Ukrainian Sentences
Go through the file section by section. For EACH Ukrainian sentence:
- Is grammar correct? (cases, verb forms, agreement)
- Does it sound natural? (not robotic, not calqued from English)
- Are there Russianisms? (check against list below)
- Is vocabulary appropriate for the level?

### English Sentences
- Is it clear and accessible?
- Warm tutor voice or cold textbook?
- Over-explaining simple things? Under-explaining complex ones?

### IPA Transcriptions (if present)
- Every transcription must be checked for correct stress placement
- Ukrainian stress is unpredictable — verify each one
- Watch for English approximations instead of Ukrainian phonemes

### Activities (EVERY ITEM)
Check each activity item individually:
- **quiz**: Grammatically correct? Exactly one correct answer? Options plausible?
- **fill-in**: Sentence correct with answer filled in? Distractors plausible?
- **match-up**: All pairs correct? No duplicates?
- **true-false**: True statements actually true? False clearly false?
- **unjumble**: Answer forms a correct, natural sentence?
- **group-sort**: Items correctly categorized?
- **anagram**: Solution correct? Hint clear?

Count as you go. You MUST report how many items you checked.

---

## STEP 3: AUTO-FAIL CHECKLIST

Check EVERY category. Report "[CLEAN]" or list specific findings.

### Russianisms
| Wrong | Correct |
|-------|---------|
| кушать | їсти |
| приймати участь | брати участь |
| самий кращий | найкращий |
| слідуючий | наступний |
| на протязі | протягом |
| любий (any) | будь-який |
| отвічати | відповідати |
| вообще | взагалі |
| получати | отримувати |
| відноситися | ставитися |

**Finding:** [CLEAN] or [list with line numbers]

### Calques
| Wrong | Correct |
|-------|---------|
| робити сенс | мати сенс |
| брати місце | відбуватися |
| це є | це (usually) |

**Finding:** [CLEAN] or [list with line numbers]

### Grammar Scope Violations
At module 08, students know ONLY modules 1-7. Any grammar from later modules is scope creep.
- Past tense (if not yet taught)
- Cases not yet introduced
- Verb forms not yet taught

**Finding:** [CLEAN] or [list specific violations with line numbers]

### Activity Errors
- Wrong answer marked as correct
- Multiple valid answers but only one accepted
- Grammatically incorrect sentences
- Duplicate items

**Finding:** [CLEAN] or [list with activity number and item number]

### Beginner Safety ("Would I Continue?" Test)
| Question | Result |
|----------|--------|
| Did I feel overwhelmed? | [Pass/Fail] |
| Were instructions clear? | [Pass/Fail] |
| Did I get quick wins? | [Pass/Fail] |
| Was Ukrainian scary? | [Pass/Fail] |
| Would I come back tomorrow? | [Pass/Fail] |
| **Total** | **X/5** |

Emotional beats found:
- Welcome/orientation: [yes/no, where]
- Curiosity trigger: [yes/no, where]
- Quick wins: [count, where]
- Encouragement: [count, where]
- Progress marker: [yes/no, where]

---

## STEP 4: SCORE DIMENSIONS

**Score ONLY after completing Steps 1-3.** Each score must link to specific findings.

### Scoring Rules
- **9-10**: Excellent — no issues found in this dimension
- **7-8**: Good — minor issues found
- **5-6**: Needs work — multiple issues
- **<5**: Serious problems — major rewrite needed
- **If you found 3 grammar errors, Language cannot be 9**
- **If scope creep found, Relevance and Pedagogy cannot be 8+**

### Auto-Fail Thresholds
| Dimension | Auto-fail if below |
|-----------|-------------------|
| Experience Quality | <7 |
| Coherence | <7 |
| Relevance | <7 |
| Educational | <7 |
| Language | <8 |
| Pedagogy | <7 |
| Immersion | <6 |
| Activities | <7 |
| Richness | <6 |
| Beginner Safety | <7 |
| LLM Fingerprint | <7 |
| Linguistic Accuracy | <9 |

### Weighted Overall Score
```
Overall = (Experience × 1.5 + Coherence × 1.0 + Relevance × 1.0 + Educational × 1.2 +
          Language × 1.1 + Pedagogy × 1.2 + Immersion × 1.0 + Activities × 1.3 +
          Richness × 0.9 + Beginner_Safety × 1.3 + LLM × 1.0 + Linguistic_Accuracy × 1.5) / 14.0
```

**Quality target: 9.0+ overall AND no dimension below its auto-fail threshold.**
**If the score is below 9.0, you MUST provide a Fix Plan (see output format) with specific actions to reach 9/10.** The fix plan drives the iteration loop — Claude will send fixes to Gemini until the module reaches 9.0+.

---

## OUTPUT FORMAT

Write your complete review to the output file specified in the task: **/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/orchestration/the-living-verb-ii/phase-5-re-review.md**

Use this exact markdown structure:
# Рецензія: The Living Verb II

**Level:** A1 | **Module:** 08
**Overall Score:** {X.X}/10
**Status:** PASS / FAIL
**Reviewed:** {date}

## Plan Verification

```
Plan-Content Alignment: [PASS/FAIL]
- Sections: [status]
- Vocabulary: [X/Y from plan, Z extra]
- Grammar scope: [status]
- Objectives: [status]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | X/10 | <7 | [specific finding] |
| 2 | Coherence | X/10 | <7 | [specific finding] |
| 3 | Relevance | X/10 | <7 | [specific finding] |
| 4 | Educational | X/10 | <7 | [specific finding] |
| 5 | Language | X/10 | <8 | [specific finding] |
| 6 | Pedagogy | X/10 | <7 | [specific finding] |
| 7 | Immersion | X/10 | <6 | [actual % vs target] |
| 8 | Activities | X/10 | <7 | [specific finding] |
| 9 | Richness | X/10 | <6 | [specific finding] |
| 10 | Beginner Safety | X/10 | <7 | ["Would I Continue?" X/5] |
| 11 | LLM Fingerprint | X/10 | <7 | [specific finding] |
| 12 | Linguistic Accuracy | X/10 | <9 | [specific finding] |

**Weighted Overall:** {show calculation} = **X.X/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN] or [list]
- Calques: [CLEAN] or [list]
- Grammar scope: [CLEAN] or [list]
- Activity errors: [CLEAN] or [list]
- Beginner safety: X/5

## Critical Issues Found

### Issue 1: {Category}
- **Location**: Line {N} / Section "{name}"
- **Original**: "{exact text}"
- **Problem**: {why it's wrong}
- **Fix**: {concrete replacement}

[... more issues ...]

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| {N} | "{original}" | "{fixed}" | Russianisms / Calque / Scope / Grammar |

## Beginner Safety Audit

"Would I Continue?" Test: X/5
- Overwhelmed? [Pass/Fail]
- Instructions clear? [Pass/Fail]
- Quick wins? [Pass/Fail]
- Ukrainian scary? [Pass/Fail]
- Come back tomorrow? [Pass/Fail]

Emotional beats: X found
- Welcome: [location or "missing"]
- Curiosity: [location or "missing"]
- Quick wins: [count + locations]
- Encouragement: [count + locations]
- Progress: [location or "missing"]

## Strengths
- [Specific strength with evidence from content]

## Fix Plan to Reach 9/10 (REQUIRED if score < 9.0)

For EACH dimension scoring below 9, provide a concrete action plan:

### {Dimension Name}: {current}/10 → 9/10

**What to fix:**
1. Line {N}: Change "{current text}" → "{replacement text}" — {why this raises the score}
2. Section "{name}": {specific action} — {expected impact}
3. ...

**Expected score after fix:** {X}/10

[Repeat for every dimension below 9. Be specific — line numbers, exact replacements, section names.]

### Projected Overall After Fixes

```
{Recalculate weighted overall with projected dimension scores}
```

## Verification Summary

- Content lines read: {X}
- Activity items checked: {X}
- Ukrainian sentences verified: {X}
- IPA transcriptions checked: {X}
- Issues found: {X}
- Naturalness score recommendation: {X}/10

## Verdict

**PASS** or **FAIL**

{1-3 sentences linking verdict to specific findings. If FAIL, list the blocking issues.}

## Boundaries

- Do NOT modify any files OTHER than the output file
- Do NOT score generously — honesty prevents bad curriculum
- Do NOT skip any step or dimension
- Do NOT fabricate issues — every critique must cite a specific line number
- Do NOT give vague feedback like "could be improved" — say exactly what and where
