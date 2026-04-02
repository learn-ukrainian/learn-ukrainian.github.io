# Prompt & Context Engineering Review: verbs-group-one

**Track:** a1 | **Sequence:** 16
**Pipeline:** v6
**Writer:** claude-tools (claude-opus-4-6) | **Reviewer:** gemini-tools + claude-tools
**Validate attempts:** 2 (first attempt rejected for missing heading, rewritten FROM SCRATCH)
**Review rounds:** 2 (R1: Gemini, R2: Claude — both REVISE → fixes applied)
**Friction reports:** None (no `phase-2-friction-*.md` found)
**Gemini self-audit iterations:** N/A (Claude was the writer)

---

## Context Engineering Analysis

### Instruction → Understanding → Output Gap

| Instruction (from prompt) | What writer produced | Gap type | Evidence |
|--------------------------|---------------------|----------|----------|
| Section Structure lists 5 H2s including BOTH `## Підсумок — Summary` AND `## Підсумок` | First attempt wrote only one summary heading | **instruction_conflict** | Prompt line 661-662 lists two separate summary sections; skeleton has only one (`## Підсумок — Summary`). First attempt picked one, validation expected the other → FROM SCRATCH rewrite triggered. |
| Skeleton says "Group I infinitives end in -ати, -увати, or -яти (вивчати, малювати)" | Writer faithfully reproduced the skeleton's -яти classification | **context_gap** (bad skeleton) | Skeleton P1 in Section 2 explicitly says `-яти (вивчати, малювати)`. VESUM confirms вивчати = -ати, малювати = -ювати. The skeleton injected a **factual error** that the writer reproduced. Pre-verify did NOT catch this. |
| "Fix: Reclassify вивчати under -ати" (R2 fix) | Fix applied in Section 2 only; Summary (line 97) still says "-яти" | **fix_scope_gap** | R2 `<fixes>` had one find/replace targeting Section 2 text. Summary section has the same claim in different wording: "Group I verbs have infinitives ending in **-ати**, **-увати**, or **-яти**." This was NOT caught by the fix. |
| Pre-verify flagged навчатися as B1 (CEFR ⚠️) | Writer used навчатися in Dialogue 2 anyway | **instruction_too_weak** | Pre-verify says "consider replacing with учуся / я вчуся" but doesn't say MUST. Writer followed skeleton which uses навчатися. Skeleton overrode the advisory. |

### Gemini Self-Audit Findings
N/A — Claude was the writer for this module. No `===SELF_AUDIT_START===` block.

### Root Cause Verdict

**Primary gap**: `instruction_conflict` + `context_gap`

**Explanation**: Two structural problems in the prompt template caused avoidable failures:

1. The **Section Structure block** and the **Skeleton** contradict each other on summary headings (5 sections vs 4). This caused the first attempt to fail validation and triggered a full FROM SCRATCH rewrite — wasting an entire generation cycle.

2. The **Skeleton** contained a factual error about Ukrainian morphology (-яти classification) that the writer faithfully reproduced. The pre-verify phase verified individual VESUM words but did NOT verify the skeleton's morphological claims. The R2 fix only patched one instance; the same error persists in the Summary section of the shipped module.

---

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| **Duplicate summary section** | **HIGH** | v6-prompt.md (Section Structure block) | Lines 661-662 list `## Підсумок — Summary` (~300 words) AND `## Підсумок` (~150 words) as separate sections. The skeleton has only one summary section. The plan `content_outline` has only one. This contradiction caused the first attempt to fail. |
| Skeleton says "Write from SCRATCH" on heading failure | MEDIUM | correction-attempt-1.md (correction directive template) | A missing H2 heading triggered a full rewrite. This is disproportionate — a targeted fix ("add this heading") would preserve the working content. FROM SCRATCH rewrites waste tokens and can introduce NEW errors. |
| Pre-verify advisories not binding | LOW | v6-prompt.md | Pre-verify says "consider replacing" for CEFR warnings. The skeleton then uses the flagged word anyway. Either make pre-verify CEFR flags binding (MUST replace) or remove them from pre-verify output. Currently they create noise the writer ignores. |

---

## Context Gaps

| Missing Context | Impact | Fix |
|----------------|--------|-----|
| **Skeleton morphological claims not verified** | Writer reproduced factual error about -яти infinitives | Add a VESUM verification step for skeleton morphological claims (e.g., verify that all listed infinitive suffixes match VESUM's actual analysis of the example verbs) |
| **No prior module vocabulary list** | Writer couldn't verify which nouns/adjectives are "known from M08/M09" | Inject a vocabulary summary of prerequisite modules so the writer knows what's available |
| **Fix scope not validated** | R2 fix only targeted one location; same error existed in Summary | After applying `<fixes>`, grep the full content for the OLD text pattern to catch remaining instances |

---

## Friction Root Causes

No friction files were generated for this module (no `phase-2-friction-*.md` or `phase-C-friction.md`). This is itself notable — the writer (Claude) doesn't produce friction reports the way Gemini does.

| Friction Point | Root Cause Type | Details | Template Fix |
|---------------|-----------------|---------|-------------|
| First attempt rejected (missing heading) | **conflicting_guidance** | Section Structure lists 5 sections, skeleton lists 4, plan lists 4. Writer followed one source, validation expected another. | Remove the Section Structure block from prompts that have a skeleton — the skeleton IS the structure |
| -яти error shipped in Summary | **template_gap** | No post-fix verification step checks for remaining instances of the corrected error | Add grep-based verification after `<fixes>` application |

---

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|-------------|
| write | 2 | Missing H2 heading (prompt conflict between Section Structure and Skeleton) | **YES** — remove duplicate Section Structure block when skeleton exists |
| review | 2 | R1: vocative error + є-in-ють claim; R2: -яти classification error | **PARTIALLY** — the -яти error originated in the skeleton, not the writer. Skeleton verification would prevent it. Vocative error is a writer mistake (not preventable by prompt). |

---

## Residual Errors in Shipped Content

**CRITICAL**: The final published `verbs-group-one.md` (line 97) still contains:

> "Group I verbs have infinitives ending in **-ати**, **-увати**, or **-яти**."

This is the SAME morphological error that R2 caught and fixed in Section 2. The R2 fix targeted the longer sentence in Section 2 but missed this shorter restatement in the Summary. **This error is live in the shipped module.**

---

## Suggested Template Fixes

### Fix 1: Remove Section Structure block when skeleton exists (Priority: HIGH)
**Prevents:** First-attempt rejections due to heading mismatch
**Scope:** All modules (any track with skeleton-based writing)
**Template file:** `scripts/build/v6_build.py` (prompt assembly logic) or `scripts/build/templates/` (wherever Section Structure is injected)

The skeleton already defines the exact section structure with word budgets. The Section Structure block duplicates this information and introduces contradictions (5 sections vs 4). When a skeleton is present, the Section Structure block should be suppressed.

```diff
- ## Section Structure
-
- Write these sections as H2 headings, in this exact order:
-
- - `## Діалоги (Dialogues)` (~300 words)
- - `## Перша дієвідміна (Group I Verbs)` (~300 words)
- - `## Я, ти, він/вона (Persons)` (~300 words)
- - `## Підсумок — Summary` (~300 words)
- - `## Підсумок` (~150 words)
-
- Each section should follow the word budget specified. The total must reach 1200 words minimum.
+ [REMOVED — skeleton provides section structure when present]
```

### Fix 2: Post-fix grep verification (Priority: HIGH)
**Prevents:** Partially-fixed errors shipping (like -яти in Summary)
**Scope:** All modules across all tracks
**Template file:** Review fix application logic in `scripts/build/v6_build.py`

After applying `<fixes>` find/replace pairs, grep the FULL content for distinctive tokens from the OLD text. If any remain, flag for manual review or generate an additional fix.

```python
# After applying fixes:
for fix in fixes:
    old_tokens = extract_distinctive_tokens(fix["find"])
    for token in old_tokens:
        if token in updated_content:
            log.warning(f"Fix partially applied: '{token}' still found in content")
```

### Fix 3: Skeleton morphological claim verification (Priority: MEDIUM)
**Prevents:** Factual errors in skeleton being faithfully reproduced
**Scope:** All grammar-focus modules
**Template file:** Skeleton generation step (`scripts/build/v6_build.py`, skeleton phase)

When the skeleton claims a verb belongs to a specific infinitive suffix group (e.g., "-яти"), verify against VESUM's `verify_lemma` before injecting the skeleton into the content prompt. If VESUM disagrees, fix the skeleton before the write phase.

### Fix 4: Proportionate correction directives (Priority: MEDIUM)
**Prevents:** Wasted generation cycles from FROM SCRATCH rewrites
**Scope:** All modules
**Template file:** Correction directive template

A missing H2 heading is a structural issue, not a content quality issue. Instead of "Write from SCRATCH," use a targeted fix:

```diff
- CRITICAL: Your previous attempt failed the following checks.
- Write the module FROM SCRATCH.
+ CRITICAL: Your previous attempt failed the following checks.
+ Fix ONLY the listed issues. Keep all working content intact.
+ 
  - FIX: Missing section heading: 'Підсумок — Summary'
+   → Add this heading before the summary content.
```

### Fix 5: Bind CEFR pre-verify warnings to skeleton (Priority: LOW)
**Prevents:** Skeleton using B1 words that pre-verify flagged as above target
**Scope:** All core track modules (A1-B2)
**Template file:** Skeleton generation step

Pre-verify flagged навчатися as B1 (above A1 target). But the skeleton was generated BEFORE pre-verify ran (or ignored its output). Either: (a) run pre-verify before skeleton, or (b) feed CEFR warnings into skeleton generation.

---

## Pedagogical Violations in Shipped Content

From the audit report, two pedagogical violations are flagged but not fixed:

1. **`translate` activity at A1** — The ACTIVITIES pipeline generated a `translate` activity type, but translate is only allowed at A2+. This is an activities template issue, not a content prompt issue.
2. **Metalanguage terms** `множина`, `однина` used in content but not in vocabulary — minor, typical of conjugation tables.

---

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. **Remove Section Structure when skeleton exists** — would have prevented the first-attempt rejection and FROM SCRATCH rewrite (saves ~90s compute + eliminates risk of new errors)
2. **Post-fix grep verification** — would have caught the -яти error still present in the Summary section (a factual error is LIVE in the shipped module)
3. **Skeleton morphological verification via VESUM** — would have caught the -яти classification error BEFORE it reached the writer, preventing both review rounds from needing to flag it
