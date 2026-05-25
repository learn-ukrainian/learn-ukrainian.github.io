# Dispatch brief — wire cursor-agent --resume into the cursor adapter (#2287)

**Agent**: agy (Antigravity CLI / Gemini-3.5-Flash-High)
**Mode**: workspace-write (small mechanical edit)
**Effort**: medium
**Branch base**: `origin/main`
**Task ID**: `issue-2287-cursor-resume-agy-2026-05-26`

## Context (one-shot read)

The cursor adapter at `scripts/agent_runtime/adapters/cursor.py:75` carries a stale comment claiming `cursor-agent` doesn't support session resume. The 2026-05-25 Cursor consultation (msg #1080 in agent bridge, task `ui-bridge-design-cursor-2026-05-25`) empirically refuted this on the current machine:

```bash
$ cursor-agent --help | rg -i 'resume|session'
  --resume [chatId]            Select a session to resume (default: false)
  --continue                   Continue previous session (default: false)
  ls                           Resume a chat session
  resume                       Resume the latest chat session
```

The adapter never tries `--resume` so the stale comment is the only blocker. Fix is small + surgical.

## Read first

- `scripts/agent_runtime/adapters/cursor.py` — full file (~200 LOC; focus on lines 60-100)
- `scripts/agent_runtime/adapters/codex.py` — analogous `--resume` plumbing already wired (look for `_rollout_matches_plan` or similar resume-handling)
- `gh issue view 2287` — original issue body
- `docs/best-practices/harness-engineering.md` — adapter-pattern conventions

## Required steps (numbered)

1. **Worktree setup**:
   - `git worktree add -b agy/issue-2287-cursor-resume .worktrees/dispatch/agy/issue-2287-cursor-resume-2026-05-26 origin/main`
   - `cd .worktrees/dispatch/agy/issue-2287-cursor-resume-2026-05-26`
   - `ln -s ../../../../.venv .venv` (# venv symlinked)

2. **Read** `scripts/agent_runtime/adapters/cursor.py` start-to-end and `scripts/agent_runtime/adapters/codex.py` for the analogous resume-handling pattern.

3. **Remove the stale comment** at line 75 (or wherever it lives — exact line may have shifted slightly):
   - Old: `# cursor-agent does not yet support resume` (or similar phrasing)
   - New: nothing (delete the comment outright; the wired behaviour speaks for itself)

4. **Wire `--resume <chatId>` into the cursor adapter** mirroring the codex adapter's approach:
   - Probe whether a session-id is available for the current task
   - If yes AND `--resume` would extend the same conversation: pass `--resume <chatId>` to the `cursor-agent` argv
   - If no (first dispatch for this task-id): omit `--resume`, behaviour unchanged
   - Idempotent: re-running the same task-id should reuse the same chatId

5. **Where to find / derive the chatId**:
   - Cursor stores sessions under `~/.cursor/projects/<encoded-project-path>/agent-transcripts/<uuid>/<uuid>.jsonl` per the 2026-05-25 consultation
   - SQLite store at `~/.cursor/chats/<hash>/<uuid>/store.db` (IDE-internal — use the JSONL path for adapter-side tracking)
   - The adapter likely already stores some session-id in `batch_state/` or via the runtime's task-id mapping. Reuse that storage, do NOT invent a new persistence layer.

6. **Update the stale comment's references** if any other comments or docstrings in `cursor.py` or `agent_runtime/` repeat the false "no resume" claim. Grep:
   ```bash
   grep -rn "no resume\|does not.*resume\|doesn't.*resume" scripts/agent_runtime/
   ```

7. **Write a unit test** at `tests/agent_runtime/test_cursor_adapter_resume.py`:
   - Mock `cursor-agent` CLI; verify the adapter passes `--resume <chatId>` when a prior session-id is available
   - Verify the adapter omits `--resume` on first invocation for a new task-id
   - Verify the chatId-resolution path doesn't crash when the transcript dir is missing
   - Use the existing `tests/agent_runtime/test_*.py` files as the harness pattern

8. **Run targeted tests** (do not use the pytest fail-fast flag — see #1942):
   ```bash
   .venv/bin/pytest tests/agent_runtime/test_cursor_adapter_resume.py -v
   .venv/bin/pytest tests/agent_runtime/ -q
   .venv/bin/ruff check scripts/agent_runtime/adapters/cursor.py tests/agent_runtime/
   ```

9. **Commit** (conventional commit format):
   ```
   fix(cursor-adapter): wire --resume; remove stale "no resume" comment (#2287)
   ```
   With X-Agent trailer + Co-Authored-By: Antigravity CLI <noreply@google.com>.

10. **Push + PR**:
    - `git push -u origin agy/issue-2287-cursor-resume`
    - `gh pr create --base main --head agy/issue-2287-cursor-resume --title "..." --body @PR_BODY.md`
    - PR body: closes #2287, links empirical test results in the consultation thread, brief explanation of the wiring approach.

## Hard constraints

- **No pytest fail-fast flag** in any commit or PR body (#1942).
- **No bridge calls mid-dispatch** (`ab ask-gemini`, `ab discuss`) — silence-timeout lesson from #2289.
- **Stay in your worktree** for ALL git operations.
- **Do NOT auto-merge.** Open the PR, tag for orchestrator review.

## Done criteria

- PR opened with the fix + tests
- Tests pass (paste raw pytest output in PR body per #M-4)
- Ruff clean (paste raw output)
- Stale comment removed; no remaining false "no resume" claims in `agent_runtime/`
- PR body has the X-Agent trailer + closes #2287

## Estimated cost

- Wall-clock: 30-45 min
- Code change: ~20-40 LOC + ~50-80 LOC test
