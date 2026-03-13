# Prompt Consultation: Diagnose Template Issues

> **You are Gemini, acting as a prompt engineering consultant.**
> **Your task: Analyze WHY a template produced bad output, and propose a specific fix to the template itself.**

## Context

A module build failed or produced low-quality output. Instead of fixing the content, we want to fix the ROOT CAUSE in the template that generated it.

## The Failures

These specific issues were found during review:

```
{REVIEW_FAILURES}
```

## The Template Excerpt

This is the relevant section of the template that generated the failing output:

```
{TEMPLATE_EXCERPT}
```

## The Module Output (excerpt)

This is what the template actually produced:

```
{OUTPUT_EXCERPT}
```

## Your Analysis

Answer these questions:

1. **Root Cause**: What specific instruction (or missing instruction) in the template caused each failure?
2. **Proposed Change**: For each root cause, provide a specific FIND/REPLACE edit to the template.
3. **Scope**: Is this fix specific to this module type, or does it apply to all modules?
4. **Action**: Should the module be rebuilt with the fixed template, or can the content be patched?

## Output Format

```
===CONSULTATION_START===
root_cause: |
  {detailed explanation of what in the template caused the failures}

proposed_changes:
  - find: |
      {exact text to find in the template}
    replace: |
      {exact replacement text}
    file: "{template filename}"
    rationale: "{why this change fixes the root cause}"

scope: {this_module|all_modules}
action: {rebuild|fix}
confidence: {high|medium|low}

additional_notes: |
  {any other observations about the template quality}
===CONSULTATION_END===
```

## Rules

- Be SPECIFIC — quote exact template lines, not vague descriptions
- Proposed changes must be valid FIND/REPLACE pairs (the "find" text must exist in the template)
- If the template is fundamentally fine and the issue is a one-off LLM mistake, say so (scope: this_module, action: fix)
- If the template is missing a critical instruction that would prevent the class of error, propose adding it
- Do NOT propose changes that would break other modules
