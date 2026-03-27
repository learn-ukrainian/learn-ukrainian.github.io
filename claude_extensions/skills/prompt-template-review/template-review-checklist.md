# Prompt Template Review Checklist

Reviews pipeline prompt templates (`scripts/build/phases/*.md`) and the Python code that fills their placeholders.

---

## Step 1: Inventory templates

List all `.md` files in `scripts/build/phases/`. For each template, extract:
- All `{PLACEHOLDER}` tokens (regex: `\{[A-Z_]+\}`)
- All instruction sections (H2 headings)
- Exercise format instructions (DSL vs INJECT_ACTIVITY markers)
- Tool prefix references (`mcp__rag__` vs `rag_`)

---

## Step 2: Verify placeholder replacement

For each placeholder found in each template, search `scripts/build/v6_build.py` for the corresponding replacement code.

Check:
- Is every `{PLACEHOLDER}` in the template replaced by Python code before dispatch?
- Are there any placeholders in the template that don't appear in any `replacements = {}` dict?
- Are there any replacements in Python that don't correspond to a placeholder in the template?

**Known pattern**: `step_write()` builds a `replacements` dict and calls `prompt.replace(key, value)` for each. Check that dict covers all placeholders.

Flag: `UNREPLACED: {PLACEHOLDER} in {template} — no replacement found in v6_build.py`

---

## Step 3: Cross-template consistency

Compare instructions ACROSS templates for contradictions:

### 3a. Exercise format
- Does `v6-write.md` say "INJECT_ACTIVITY markers only"?
- Does `v6-write-seminar.md` say "write exercises directly in DSL"?
- Does the chunk prompt in `_build_chunk_prompt()` match the main write prompt?
- Do all templates agree on what the writer should produce?

### 3b. Tool prefix
- Does each template use the correct tool prefix for its agent?
- `mcp__rag__` for Claude, `rag_` for Gemini
- Is the prefix dynamically set based on the actual dispatched agent, or hardcoded?

### 3c. Formatting instructions
- Do all templates agree on dialogue format (blockquote `>` vs `<div class="dialogue">`)?
- Do all templates agree on stress marks (writer adds vs tool adds later)?
- Do all templates agree on vocabulary tables (writer adds vs ENRICH adds)?

### 3d. Word target references
- Do all templates use `{WORD_TARGET}` consistently?
- Are ceiling/overshoot calculations consistent (1.1x vs 1.5x)?

---

## Step 4: Detect stale instructions

For each template, check if instructions reference:

- **Deprecated pipeline steps**: V5 pipeline, `build_module_v5.py`, old phase names
- **Deprecated exercise format**: DSL blocks (:::quiz) in templates that should use INJECT_ACTIVITY markers
- **Deprecated file paths**: Old orchestration structure, removed scripts
- **Outdated component names**: Components that were renamed or removed
- **Outdated activity types**: Types that don't exist in `schemas/activity-v2.schema.json`

---

## Step 5: Verify template-to-dispatch alignment

For each template, trace the dispatch path in `v6_build.py`:

1. Which function loads this template?
2. What model is dispatched? (Check for hardcoded model vs config-driven)
3. Are MCP tools enabled? Does the template's tool instruction section match?
4. What timeout is set? Is it sufficient for the prompt size?

---

## Step 6: Report

```
## Prompt Template Review

### Templates reviewed
- {template1}: {N} placeholders, {M} instruction sections
- {template2}: ...

### Unreplaced placeholders
{list or "None found"}

### Cross-template contradictions
{list with severity ratings, or "Consistent"}

### Stale instructions
{list with specific lines, or "None found"}

### Dispatch alignment issues
{list or "All aligned"}

### Summary
{X issues found: Y critical, Z major, W minor}
```
