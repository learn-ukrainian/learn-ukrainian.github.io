# Code Editing Safety

General-purpose rules for safe, reliable code editing. Reusable across projects.

## 1. Step 0: Clean Before Refactoring

Before ANY structural refactor on a file >300 LOC, first remove dead code: unused imports, unused exports, dead props, orphaned functions, debug logs. Commit cleanup separately. Dead code wastes context tokens and accelerates compaction, making the actual refactor more likely to fail from context decay.

## 2. Context Decay: Re-read Before Editing

After 10+ messages in a conversation, ALWAYS re-read a file before editing it. Do not trust your memory of file contents — auto-compaction may have silently summarized away the details. Editing against stale mental state produces broken output.

**Rule:** If you last read a file more than 5 tool calls ago, re-read it before editing.

## 3. Large File Reading: Use Chunks

The Read tool returns up to 2,000 lines by default. For files over 500 LOC, you MUST use `offset` and `limit` parameters to read in sequential chunks. Never assume a single read captured the complete file. If you need the full picture, read in 1000-line chunks and note what you've covered.

## 4. Rename/Refactor Checklist (Grep Is Not an AST)

Grep is text matching, not semantic analysis. When renaming or changing any function, type, variable, or constant, you MUST search separately for ALL of these:

1. **Direct calls and references** — `functionName(`
2. **Type-level references** — interfaces, generics, type annotations
3. **String literals** — `"functionName"`, template literals, logging
4. **Dynamic imports** — `import()`, `require()`, `__import__()`, `importlib`
5. **Re-exports and barrel files** — `__init__.py`, `index.ts`, `__all__`
6. **Test files and mocks** — test fixtures, mock definitions, parametrize decorators

Do not assume a single grep caught everything. After making all changes, grep once more for the OLD name to confirm zero remaining references.

## 5. Senior Dev Suggestion

While completing a task, if you notice architectural flaws, duplicated state, inconsistent patterns, or code that a senior engineer would reject in review — **flag it explicitly** with a brief explanation of what's wrong and what you'd propose instead. Do not silently fix it, and do not silently ignore it. Present the case, let the user decide.

Format: `**Suggestion:** [what's wrong] → [what I'd do instead]. Want me to fix this?`

## 6. Verification Before Declaring Done

Never report a task as complete until you have run the project's verification tools. The specific tools depend on the project:

- **Python projects:** `.venv/bin/ruff check`, `.venv/bin/pytest` (affected files)
- **TypeScript/JS projects:** `npx tsc --noEmit`, `npx eslint . --quiet`, `npm test`
- **Other:** Whatever the project's CI runs — find it in CI config or `Makefile`

If no verification tools are configured, state that explicitly instead of claiming success. "Done" means "verified," not "files written."

## 7. Sub-Agent Utilization

For tasks touching >5 independent files or requiring parallel investigation, launch sub-agents. Each gets its own context window, preventing context decay on the main thread.

**When to use sub-agents:**
- Refactors spanning many files (batch into groups of 5-8 per agent)
- Research tasks that would pollute main context (exploring options, reading many files)
- Independent parallel work (tests + implementation, multiple modules)
- Long-running operations (use `run_in_background`)

**When NOT to use sub-agents:**
- Sequential work where each step depends on the previous
- Simple changes to 1-3 files
- Tasks requiring tight coordination with the user

One task per sub-agent. Keep the main context clean for decision-making.
