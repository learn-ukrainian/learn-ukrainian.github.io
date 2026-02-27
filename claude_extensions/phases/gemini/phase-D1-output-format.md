## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.
> **NO FIX OUTPUT** — this step produces the review only. Fixes are handled in a separate step if needed.

### Output Block 0: Citation Bank (BEFORE the review)

**MANDATORY** — Build this FIRST by reading files with Read tool and copy-pasting exact quotes.
Each citation must be verified with Grep before adding to the bank.
Use `「...」` (CJK corner brackets) for ALL Ukrainian citations — NOT `«»` (those appear inside Ukrainian text and cause parsing collisions).

```
===CITATION_BANK_START===
1. Line {N}: 「{exact Ukrainian text copy-pasted from Read output}」
2. Line {N}: 「{exact Ukrainian text copy-pasted from Read output}」
3. Line {N}: 「{exact Ukrainian text copy-pasted from Read output}」
...
===CITATION_BANK_END===
```

**Rules:**
- Every entry MUST be copy-pasted verbatim from Read tool output — zero rewording
- Verify each with Grep before adding: `Grep pattern="first 5 words" path="{CONTENT_PATH}"`
- If Grep returns no match, you paraphrased — delete and re-copy
- Minimum 8 citations for modules >2000 words
- In the review body below, you may ONLY use `「」` citations that appear in this bank

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

{SCORING_OUTPUT_TABLE}

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
- **Original**: 「{exact Ukrainian text from Citation Bank}」
- **Problem**: {why it's wrong}
- **Fix**: {concrete replacement}

[... more issues ...]

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| {N} | 「{original}」 | 「{fixed}」 | Russianisms / Calque / Scope / Grammar |

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
1. Line {N}: Change 「{current}」 -> 「{replacement}」 — {why}
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
- Citations in bank: {X}
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

**CITATION RULE (LAST REMINDER):** Every `「」`-quoted Ukrainian text in your review MUST appear verbatim in the source files. If you cannot find it with Grep, do NOT cite it — you are hallucinating. Use your Citation Bank as the single source of verified quotes.

Your output MUST contain `===CITATION_BANK_START===` / `===CITATION_BANK_END===` BEFORE `===REVIEW_START===` / `===REVIEW_END===`. The extraction pipeline uses these exact delimiters. Any output without these delimiters is **automatically discarded** and the entire phase fails. Do not write a summary or conversational response — output the citation bank, then the structured review inside the delimiters.
