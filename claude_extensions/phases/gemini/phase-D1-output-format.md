## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.
> **NO FIX OUTPUT** — this step produces the review only. Fixes are handled in a separate step if needed.

### Output Block 1: Review

```
===REVIEW_START===
# Рецензія: {TOPIC_TITLE}

**Level:** {LEVEL} | **Module:** {MODULE_NUM}
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

## Scores    <!-- REQUIRED — rejection if missing -->

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
| 13 | Factual Accuracy | X/10 | <8 | [specific finding or "N/A — core track"] |

**Weighted Overall:** {show calculation} = **X.X/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN] or [list]
- Calques: [CLEAN] or [list]
- Grammar scope: [CLEAN] or [list]
- Activity errors: [CLEAN] or [list]
- Beginner safety: X/5
- Factual accuracy: [CLEAN] or [list of discrepancies]

## Critical Issues Found    <!-- REQUIRED — rejection if missing -->

### Issue 1: {Category}
- **Location**: Line {N} / Section "{name}"
- **Original**: «{exact Ukrainian text verified via Grep}»
- **Problem**: {why it's wrong}
- **Fix**: {concrete replacement}

[... more issues ...]

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| {N} | «{original}» | «{fixed}» | Russianisms / Calque / Scope / Grammar |

## Beginner Safety Audit

"Would I Continue?" Test: X/5
- Overwhelmed? [Pass/Fail]
- Instructions clear? [Pass/Fail]
- Quick wins? [Pass/Fail]
- Ukrainian scary? [Pass/Fail]
- Come back tomorrow? [Pass/Fail]

## Strengths
- [Specific strength with evidence]

## Fix Plan to Reach 9/10 (REQUIRED if score < 9.0)

### {Dimension Name}: {current}/10 -> 9/10
**What to fix:**
1. Line {N}: Change «{current}» -> «{replacement}» — {why}
2. Section "{name}": {action} — {impact}

**Expected score after fix:** {X}/10

### Projected Overall After Fixes
```
{Recalculate weighted overall with projected scores}
```

## Factual Verification    <!-- REQUIRED for seminar tracks — rejection if missing -->

- Research notes consulted: {YES/NO/NOT_APPLICABLE}
- Key Facts Ledger present: {YES/NO}
- Dates checked: {X} ({all correct / N discrepancies listed below})
- Named figures verified: {X}
- Primary quotes cross-referenced: {X/Y matched}
- Chronological sequence: {CONSISTENT / ISSUES}
- Claims without research grounding: {N found — listed below if any}

{If discrepancies found, list each one:}
{- Line N: Prose says "X" but research says "Y" for [event/date/attribution]}

## Verification Summary    <!-- REQUIRED — rejection if missing -->

- Content lines read: {X}
- Activity items checked: {X}
- Ukrainian sentences verified: {X}
- IPA transcriptions checked: {X}
- Factual claims verified: {X}
- Issues found: {X}

## Verdict    <!-- REQUIRED — rejection if missing -->

**PASS** or **FAIL**

{1-3 sentences. If FAIL, list blocking issues.}

===REVIEW_END===
```

### Output Block 2: Friction Report (MANDATORY)

```
===FRICTION_START===
**Phase**: Phase D.1: Evidence Review
**Step**: {what you were doing when friction occurred, or "Full Phase D.1"}
**Friction Type**: NONE | YAML_SCHEMA_VIOLATION | TOKEN_LIMIT_TRUNCATION | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## CRITICAL: Output Format Reminder

Your output MUST start with `===REVIEW_START===` and end with `===REVIEW_END===`. The extraction pipeline uses these exact delimiters. Any output without these delimiters is **automatically discarded** and the entire phase fails. Do not write a summary or conversational response — output the structured review inside the delimiters.
