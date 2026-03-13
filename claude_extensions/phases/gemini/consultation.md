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

## Files to Analyze

Read these files to understand the full context:

- **Base template** (the file to fix): `{BASE_TEMPLATE_PATH}`
- **Rendered prompt** (what was actually sent to the LLM): `{RENDERED_PROMPT_PATH}`
- **Module output** (what the LLM produced): `{MODULE_OUTPUT_PATH}`

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
