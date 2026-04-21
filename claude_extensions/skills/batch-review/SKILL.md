---
name: batch-review
description: Batch prompt-review + content-review across multiple modules using parallel subagents. Writes reports to audit/ and orchestration/, then aggregates cross-module findings and proposes template auto-fixes.
argument-hint: <track start-end>
effort: xhigh
---

# Batch Review: $ARGUMENTS

## Parse Arguments

The user provides: `{track} {start}-{end}` or `{track} {num}` (single module).

Examples:
- `a1 5-10` — review modules 5 through 10 in A1
- `a1 8` — review just module 8
- `hist 1-20` — review HIST modules 1-20

## Resolve Module Slugs

For each module number in the range, resolve the slug. Use the curriculum index:

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from batch_gemini_config import get_module_index
idx = get_module_index('{track}')
for n in range({start}, {end}+1):
    slug = idx['num_to_slug'].get(n)
    if slug: print(f'{n} {slug}')
"
```

## Filter: Only Review Built Modules

Skip modules that don't have content yet. Check:
- `curriculum/l2-uk-en/{track}/{slug}.md` exists
- `curriculum/l2-uk-en/{track}/orchestration/{slug}/state-v5.json` (or `state.json`) exists

List the modules to review and any skipped modules.

## Dispatch Subagents (Max 4 Parallel)

Split the reviewable modules into chunks of 2-3 modules each.
Spawn up to 4 subagents using the Agent tool, each processing its chunk.

**Each subagent receives this task:**

For each module in your chunk:

### Part 1: Prompt Review

Read ALL files in `curriculum/l2-uk-en/{track}/orchestration/{slug}/`:
- `phase-2-prompt.md`, `phase-2-friction-1.md` (content prompt + friction)
- `phase-C-prompt.md`, `phase-C-friction.md` (activities prompt + friction)
- `phase-A-prompt.md`, `phase-A-output.md` (research)
- `placeholders.yaml` (injected context)
- `state-v5.json` or `state.json` (pipeline state, attempt counts)
- `completion.md` (final verdict)
- `validate-fix*-prompt.md` (validation fix attempts)
- `screen-result.json` (VESUM screening)

Follow the analysis framework from the prompt-review skill prompt (in `claude_extensions/skills/prompt-review/prompt-review-prompt.md`). Produce the full prompt-review report.

Write to TWO locations:
1. `curriculum/l2-uk-en/{track}/audit/{slug}-prompt-review.md`
2. `curriculum/l2-uk-en/{track}/orchestration/{slug}/prompt-review.md`

### Part 2: Content Review

Read the module files:
- `curriculum/l2-uk-en/{track}/{slug}.md` (content)
- `curriculum/l2-uk-en/{track}/activities/{slug}.yaml` (activities)
- `curriculum/l2-uk-en/{track}/vocabulary/{slug}.yaml` (vocabulary, if exists)
- `curriculum/l2-uk-en/{track}/meta/{slug}.yaml` (meta)
- `curriculum/l2-uk-en/plans/{track}/{slug}.yaml` (plan)

Follow the content review prompt (in `claude_extensions/skills/content-review/content-review-prompt.md`). Use RAG tools for linguistic verification:
- `mcp__sources__verify_word` for suspicious Ukrainian words
- `mcp__sources__search_text` for grammar verification against textbooks
- `mcp__sources__query_r2u` for Russicism checking

Produce the full content-review report with grade (A/B/C/F).

Write to TWO locations:
1. `curriculum/l2-uk-en/{track}/audit/{slug}-content-review.md`
2. `curriculum/l2-uk-en/{track}/orchestration/{slug}/content-review.md`

### Return Format

Return a JSON summary for the main agent:
```json
{
  "modules": [
    {
      "num": N,
      "slug": "...",
      "prompt_review": {"template_health": "GOOD/NEEDS_WORK/BROKEN", "fix_count": N, "top_fix": "..."},
      "content_review": {"grade": "A/B/C/F", "critical_count": N, "high_count": N, "issues_summary": "..."}
    }
  ]
}
```

## Aggregate Results

After all subagents return, the main agent:

1. **Collect all findings** — read all generated reports
2. **Cross-module pattern analysis** — identify recurring issues:
   - Same friction type across 3+ modules = template-level bug
   - Same content issue across 3+ modules = systematic prompt problem
   - Same VESUM failures = pipeline limitation
3. **Write cross-module summary** to `curriculum/l2-uk-en/{track}/audit/batch-review-summary-M{start}-M{end}.md`
4. **Propose auto-fixes** — for template-level patterns, list specific file + diff changes

### Auto-Fix Categories

| Category | Auto-fixable? | Target File |
|----------|--------------|-------------|
| Missing constraint/ban | YES | `scripts/pipeline_lib.py` (PEDAGOGICAL_CONSTRAINTS) |
| Missing context injection | YES | `claude_extensions/phases/gemini/*.md` templates |
| Immersion variety issues | YES | `claude_extensions/phases/gemini/beginner-content.md` |
| VESUM false positives | YES | `scripts/rag_batch_verify.py` |
| Content quality (per-module) | NO — needs rebuild | Flag for `--rebuild` |
| Pedagogical structure | NO — needs rebuild | Flag for `--rebuild` |

For auto-fixable issues: present the diff and ask user for confirmation before applying.
For rebuild-needed issues: list modules that need rebuilding and why.

## Output

Print a summary table:

```
Batch Review: {track} M{start}-M{end}
Reviewed: N modules | Skipped: M modules

| # | Slug | Prompt | Content | Grade | Issues |
|---|------|--------|---------|-------|--------|
| 5 | syllables-and-transfer | GOOD | B | 1H 2M |
| 6 | stress-and-intonation | GOOD | A | 0 |
...

Template fixes proposed: N (see batch-review-summary)
Modules needing rebuild: M
```
