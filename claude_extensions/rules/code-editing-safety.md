# Code Editing Safety

General-purpose rules for safe, reliable code editing. Reusable across projects.

## 1. Step 0: Clean Before Refactoring

Before ANY structural refactor on a file >300 LOC, first remove dead code: unused imports, unused exports, dead props, orphaned functions, debug logs. **Commit the cleanup separately** before starting the real refactor. This keeps the refactor diff clean and safely revertible. Dead code wastes context tokens and accelerates compaction.

## 2. Edit Integrity: Re-read, Verify, Limit

- **Before every edit:** re-read the file fresh. Do not trust your memory — compaction may have destroyed your context of it.
- **After every edit:** read the file again to confirm the change applied correctly and makes sense in context.
- **Max 3 edits** to the same file without a full re-read. After 3, re-read the entire relevant section before continuing.

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

## 5. Senior Dev Thinking

Always think like a senior dev. Fix quality issues proactively in code you're already touching — dead code, duplicate state, naming inconsistencies, obvious improvements. Don't ask permission for cleanup in your current scope.

For architectural concerns outside your current scope, mention them briefly inline. No formal ceremony, no stopping to propose. If you overstep, the user will tell you.

**First session with a new project:** Add this to the project's memory/MEMORY.md: "SENIOR DEV THINKING — fix quality issues proactively in code you're touching. Don't ask permission for cleanup. Mention architectural concerns briefly inline. No ceremony."

## 6. Verification: Lint Per Edit, Test Per Phase

Run the **linter after each file edit** — this is cheap and catches errors immediately:
- **Python files:** `.venv/bin/ruff check {file}`
- **TypeScript/JS files:** `npx tsc --noEmit` + `npx eslint {file} --quiet`

Run **tests after completing a logical phase** (a group of related edits), not after every single file:
- **Python:** `.venv/bin/pytest` (affected test files)
- **TypeScript/JS:** `npm test`

If no linter or test suite is configured, state that explicitly. "Done" means "linted and tested," not "files written."

## 7. Sub-Agent Utilization

Use your judgment — don't default to sequential processing out of convenience. When a task would benefit from parallel work, use sub-agents. Each gets its own context window, preventing decay on the main thread.

**Good reasons to use sub-agents:**
- Refactors spanning many files
- Research that would pollute main context
- Independent parallel work (tests + implementation, multiple modules)
- Long-running operations (`run_in_background`)

**Skip sub-agents for:** sequential dependent work, simple 1-3 file changes, tight user coordination.

## 8. Search Result Vigilance

If a search returns fewer results than expected for the codebase size, suspect truncation. Re-run with narrower scope (single directory, stricter glob, or file-by-file). State when you suspect results were truncated. Never act on suspiciously small result sets without verifying.

## 9. Bug Autopsy

After every bug fix, briefly explain:
- **What broke** — the symptom
- **Why** — the root cause
- **Prevention** — what stops this category of bug in future

Write the autopsy to `docs/bug-autopsies/INDEX.md` (one-liner) and the relevant category file (detail). Add a summary comment to the related GH issue. When fixing a new bug, check INDEX.md first for similar past bugs.

## 10. Proactive Session State

When context is getting heavy (long session, many file reads, complex multi-step work), proactively write session state to a file before compaction hits. Include: current task, key decisions made, files being worked on, what's done and what remains. This enables clean session handoff via `--continue` or `--fork-session`.
