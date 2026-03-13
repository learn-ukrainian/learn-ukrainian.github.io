# Prompt Consultation: Diagnose Template Issues

> **You are Gemini, acting as a prompt engineering consultant.**
> **Your task: Analyze WHY a template produced bad output, and propose a specific fix to the template itself.**

## Context

A module build failed or produced low-quality output. Instead of fixing the content, we want to fix the ROOT CAUSE in the template that generated it.

## The Failures

These specific issues were found during review:

```
# Audit Report: M06 — being-and-becoming.md
**Level:** A2 | **Module:** M06 | **Phase:** A2.1 | **Pedagogy:** PPP | **Target:** 2000
**Overall Status:** ❌ FAIL
**Generated:** 2026-03-13 18:26:54

## Configuration
**Type:** A2-grammar
**Word Target:** 2000 words
**Activities:** 10-14 required
**Items per Activity:** ≥8 items
**Unique Types:** ≥4 types required
**Priority Types:** error-correction, fill-in, unjumble
**Required Types:** fill-in, match-up, quiz
**Engagement:** ≥4 callouts
**Immersion:** 0-100%
**Vocab Target:** ≥1 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | fill-in | Past Roles with 'Бути' | 12 | 8 | ✅ |
| 2 | fill-in | Future and Becoming | 12 | 8 | ✅ |
| 3 | quiz | What Do You Work As? | 10 | 8 | ✅ |
| 4 | match-up | Person and Profession Match | 10 | 8 | ✅ |
| 5 | fill-in | Career Aspirations | 8 | 8 | ✅ |
| 6 | true-false | Grammar Rules: True or False? | 8 | 8 | ✅ |
| 7 | group-sort | Masculine vs Feminine Professions | 8 | 8 | ✅ |
| 8 | unjumble | Sentence Builder | 6 | 6 | ✅ |
| 9 | fill-in | Identity vs Role | 8 | 8 | ✅ |
| 10 | quiz | Perfective vs Imperfective | 8 | 8 | ✅ |

**Summary:**
- Total activities: 10 (target: 10-14) ✅
- Unique types: 6 (minimum: 4) ✅
- Priority types used: 2/3 (fill-in, unjumble) ✅
- Required types used: 3/3 (fill-in, match-up, quiz) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Sentence Builder' item 1 has 3 words (target: 5-10)
  - FIX: Adjust sentence length to 5-10 words to match A2 complexity.
- **[METALANGUAGE]** Metalanguage terms used but not in vocabulary: орудний
  - FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.

## Recommendation
**📝 UPDATE** (severity 45/100)

- Revision recommended (severity 45/100)
- 2 violations (minor)
- Immersion 29% off target (major rebalancing needed)

## Gates
- **Words:** ✅ 2584/2000 (raw: 2773)
- **Activities:** ✅ 10/10
- **Density:** ✅ All > 8
- **Unique_types:** ✅ 6/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 5/4
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 25/1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** ❌ 16.3% LOW (target 45-65% (A2.1))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ✅ Content aligned with research

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Being and Becoming** | ✅ | 43 | Included in Core |
| **Вступ** | ✅ | 481 | Included in Core |
| **Презентація: Дієслова та відмінювання** | ✅ | 453 | Included in Core |
| **Соціокультурний контекст: Фемінітиви та IT** | ✅ | 477 | Included in Core |
| **Практика та запобігання помилкам** | ✅ | 450 | Included in Core |
| **Діалоги та кар'єрні плани** | ✅ | 506 | Included in Core |
| **Підсумок** | ✅ | 174 | Included in Core |
```

## Files to Analyze

Read these files to understand the full context:

- **Base template** (the file to fix): `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/phases/gemini/beginner-full-rag.md`
- **Rendered prompt** (what was actually sent to the LLM): `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/orchestration/being-and-becoming/activities-prompt.md`
- **Module output** (what the LLM produced): `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/being-and-becoming.md`

The base template is the SOURCE file — your FIND/REPLACE proposals must target text in the **base template**, not the rendered prompt (which has variables substituted).

## Your Analysis

Answer these questions:

1. **Root Cause**: What specific instruction (or missing instruction) in the **base template** caused each failure?
2. **Proposed Change**: For each root cause, provide a specific FIND/REPLACE edit to the **base template**.
3. **Scope**: Is this fix specific to this module type, or does it apply to all modules using this template?
4. **Action**: Should the module be rebuilt with the fixed template, or can the content be patched?

## Output Format

Output ONLY the YAML between the delimiters. No markdown fences, no commentary outside the delimiters.

===CONSULTATION_START===
root_cause: |
  {detailed explanation of what in the template caused the failures}

proposed_changes:
  - find: |
      {exact text to find in the BASE TEMPLATE file}
    replace: |
      {exact replacement text}
    file: "{base template filename, e.g. core-content.md}"
    rationale: "{why this change fixes the root cause}"

scope: {this_module|all_modules}
action: {rebuild|fix}
confidence: {high|medium|low}

additional_notes: |
  {any other observations about the template quality}
===CONSULTATION_END===

## Rules

- READ the base template file before proposing changes — do not guess at its contents
- Be SPECIFIC — quote exact template lines from the base template, not the rendered prompt
- Proposed changes must be valid FIND/REPLACE pairs (the "find" text must exist in the **base template**)
- If the template is fundamentally fine and the issue is a one-off LLM mistake, say so (scope: this_module, action: fix)
- If the template is missing a critical instruction that would prevent the class of error, propose adding it
- Do NOT propose changes that would break other modules
- Output ONLY valid YAML between the delimiters — no markdown code fences inside
