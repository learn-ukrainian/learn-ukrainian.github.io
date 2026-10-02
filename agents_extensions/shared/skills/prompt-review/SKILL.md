---
name: prompt-review
description: Diagnose prompt and context engineering problems in a module orchestration folder.
argument-hint: <path-to-orchestration-folder | track slug>
effort: xhigh
---

# Prompt Engineering Review: $ARGUMENTS

For GPT-6.1 Sol (`gpt-6.1-sol`), use `high`, including advisory and
escalation turns. This overrides the shared effort above for Sol only;
other providers retain their effort rules and explicit overrides.

## Parse Arguments

The user provides one of these argument patterns:

1. **Full path**: `curriculum/l2-uk-en/a1/orchestration/the-cyrillic-code-i/`
2. **Track + slug**: `a1 the-cyrillic-code-i`
3. **Track + range**: `a1 1-6` (review orchestration folders for modules 1-6)

Parse the arguments to locate the orchestration folder:

- **Orchestration dir**: `curriculum/l2-uk-en/{track}/orchestration/{slug}/`

If a range is given, process each module's orchestration folder in sequence.

## Execute

Read and follow the full prompt review prompt at [prompt-review-prompt.md](prompt-review-prompt.md).

**Output path**: Save the review to `curriculum/l2-uk-en/{track}/audit/{slug}-prompt-review.md`

For batch runs, also produce a cross-module summary: `curriculum/l2-uk-en/{track}/audit/prompt-review-summary.md`

Reference issue #731.
