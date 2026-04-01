# Plan: Update code-editing-safety.md with investigated workarounds

## Context

Investigated 10 workarounds from iamfakeguru/claude-md repo and X thread. Discussed each one with user. All 10 adopted (some modified). Need to update `claude_extensions/rules/code-editing-safety.md` to reflect the agreed decisions.

## Changes to code-editing-safety.md

### Section 1: Step 0 — add "commit cleanup separately"
- Current: clean dead code before refactors
- Add: commit the cleanup separately before starting the real refactor

### Section 2: Context Decay — tighten to "re-read fresh before every edit"
- Current: "re-read after 10+ messages" / "5 tool calls ago"
- Change to: always re-read fresh before editing. Read after edit to confirm. Max 3 edits to same file without re-reading.

### Section 3: Large File Reading — change from guidance to hard rule
- Current: "you MUST use offset and limit"
- Already a hard rule, keep as-is.

### Section 4: Rename Checklist — already adopted, keep as-is

### Section 5: Senior Dev Suggestion — rewrite
- Current: formal "flag and propose" format with `**Suggestion:** ...`
- Change to: always think like a senior dev. Fix quality issues proactively in code you're touching. For architectural concerns outside your current scope, mention briefly inline. No ceremony.

### Section 6: Verification — tighten to per-edit linting
- Current: "run project verification tools before declaring done"
- Change to: run linter after each file edit (ruff for .py, tsc+eslint for .ts/.js). Run tests after completing a logical phase. "Done" means verified.

### Section 7: Sub-Agent Utilization — soften to judgment call
- Current: hard threshold at >5 files
- Change to: use judgment, stop defaulting to sequential out of convenience. When parallel work would help, use sub-agents.

### New Section 8: Search Result Vigilance
- If search results look suspiciously small for the codebase size, suspect truncation. Re-run with narrower scope. State when truncation is suspected.

### New Section 9: Bug Autopsy
- After every bug fix, briefly explain: what broke, why it happened, what prevents the category in future.
- Write entry to `docs/bug-autopsies/INDEX.md` (one-liner) + category file (detail).
- Add autopsy summary as comment on the related GH issue.
- Structure: `docs/bug-autopsies/INDEX.md` + `docs/bug-autopsies/{category}.md`
- Read INDEX.md only when fixing a bug — grep for symptom/category, read detail file if match.

### New Section 10: Proactive Session State
- When context is getting heavy (long session, many file reads), proactively write key state (current task, decisions, files being worked on) to a context file before compaction hits.

## Files to modify
- `claude_extensions/rules/code-editing-safety.md` — rewrite with all 10 agreed workarounds
- Create `docs/bug-autopsies/INDEX.md` — empty index for bug autopsy knowledgebase
- Deploy via `npm run claude:deploy`
- Copy updated version to `~/.claude/rules/code-editing-safety.md`
- Commit

## Verification
- `wc -l` on the file — must stay under 200 lines, split if >150
- `npm run claude:deploy` succeeds
- All rules files under 200 lines
