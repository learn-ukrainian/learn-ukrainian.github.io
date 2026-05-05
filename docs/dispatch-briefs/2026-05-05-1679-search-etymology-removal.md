# Codex dispatch — #1679 Remove search_etymology deprecation alias

## Context

`search_etymology` is a deprecated alias in the MCP sources server. The follow-up issue is #1679; original issue #1658, original PR #1678. The alias was added with a 30-day deprecation window. Today is 2026-05-05; the window expires early June 2026, so we are at the boundary — user wants the work landed now while it's at the top of the issue queue.

The canonical name is `search_grinchenko_1907`. All call sites should already be migrated; this dispatch verifies + removes the alias + tests.

## Worktree instructions (mandatory)

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin main
git worktree add -b codex/1679-remove-search-etymology .worktrees/codex-1679 origin/main
cd .worktrees/codex-1679
```

If the worktree already exists from a previous attempt, reuse it (`cd .worktrees/codex-1679 && git fetch origin main && git rebase origin/main`).

## Numbered steps

1. **Locate the alias definition.** `git grep -n 'search_etymology' scripts/ tests/ docs/ claude_extensions/ .agents/`. Capture every match.

2. **Verify all real call sites use the canonical name.** For every match outside the alias-definition site:
   - If it's the alias definition (a `@server.tool()` or similar registration), that's the line to delete.
   - If it's a call site (`mcp__sources__search_etymology(...)`, `await search_etymology(...)`, prompt text, doc reference), replace with `search_grinchenko_1907`.
   - If it's a test asserting the alias works, delete or rewrite the test to assert canonical-name usage.
   - If it's an old session-state file or autopsy, leave as-is (historical record).

3. **Delete the alias definition.** This is in `scripts/sources_mcp_server/` or wherever MCP tools are registered. Search for the exact registration block (likely a function decorated with `@server.tool()` named `search_etymology`).

4. **Update prompts.** Grep `claude_extensions/rules/`, `scripts/build/phases/*.md`, `.agents/skills/*/SKILL.md` for `search_etymology` references. Replace with `search_grinchenko_1907`.

5. **Run the MCP server smoke test.** `.venv/bin/python -m pytest tests/test_sources_mcp* -x -q` (or whichever tests cover the MCP server). Verify nothing regresses.

6. **Run full test suite.** `.venv/bin/python -m pytest tests/ -x -q` (timing — should be ~5 min).

7. **Run ruff.** `.venv/bin/ruff check scripts/`

8. **Confirm the alias is truly gone.** `git grep -n 'search_etymology' scripts/ tests/ docs/ claude_extensions/ .agents/` — should return zero matches outside historical session-state files.

9. **Update doc references.** Grep `docs/` for `search_etymology` in CURRENT docs (not session-state archives). Replace with `search_grinchenko_1907` + add a one-line note in `docs/best-practices/` if there's a relevant doc explaining the rename.

10. **Commit.**
    ```
    chore(mcp): remove search_etymology deprecation alias (#1679)
    ```
    Body lists files touched + confirms zero remaining references.

11. **Push:** `git push -u origin codex/1679-remove-search-etymology`

12. **Open PR:**
    ```bash
    gh pr create --title "chore(mcp): remove search_etymology deprecation alias (#1679)" --body "$(cat <<'EOF'
## Summary

Removes the `search_etymology` deprecation alias from the MCP sources server. The canonical name is `search_grinchenko_1907`. The 30-day deprecation window opened with #1658/PR #1678 and expires early June 2026.

## What changed

- Deleted alias registration in `scripts/sources_mcp_server/...` (commit body lists exact path)
- Migrated remaining call sites to canonical name (list)
- Deleted alias-only tests
- Updated prompts in `claude_extensions/rules/...` and `scripts/build/phases/...`

## Verification

- `git grep search_etymology` returns zero matches outside historical session-state archives
- pytest passes
- ruff clean

Closes #1679.
EOF
)"
    ```

13. **Do NOT enable auto-merge.** Wait for cross-review.

## Acceptance criteria (from #1679)

- All dependent code uses `search_grinchenko_1907` (verified)
- Alias removed
- Tests pass
- ruff clean
- PR opened, references #1679

## Discipline

- No `--no-verify`
- Reference #1679 in commit messages
- Do NOT change unrelated MCP tools
- Worktree must be cleaned up post-merge (next session)
