# Codex dispatch brief — #1709 + #1710 Gemini adapter: -p flag + API-first auth

> **Issues:** #1709 (stdin-pipe → -p flag) and #1710 (auth-mode priority flip — API first). Both fixed in this single PR.
> **Branch base:** `origin/main`
> **Worktree:** `.worktrees/dispatch/codex/1709-gemini-adapter-p-flag/`
> **Branch name:** `codex/1709-gemini-adapter-p-flag`
> **Mode:** danger
> **Hard timeout:** 3600s (60 min)
> **Effort:** medium
> **Reviewer for cross-family:** Claude (Gemini is broken right now, so it cannot review; Codex is the author)

## Goal

Fix the gemini-cli integration regression. Gemini was the historical workhorse writer for this project; it currently hangs indefinitely on every non-TTY invocation because the adapter pipes the prompt via stdin and gemini-cli at v0.40.1 treats that as REPL keystrokes, not a one-shot prompt. Switch to `-p PROMPT` (CLI flag).

Verified working invocation (orchestrator, 2026-05-05 20:15 CEST):

```bash
gemini -y -m gemini-3.1-pro-preview -p "what is 2+2? answer in 1 word"
# returns "Four." in <5s, exit 0
```

Broken invocation (current adapter):

```bash
echo "what is 2+2?" | timeout 30 gemini -m gemini-3.1-pro-preview --approval-mode=yolo
# returns generic "Hi, how can I help?" — ignores piped prompt; in real bakeoff hangs forever
```

## What to change

### `scripts/agent_runtime/adapters/gemini.py`

The current `InvocationPlan` (line 187-197) sets `stdin_payload=prompt` and a `cmd` that doesn't include the prompt. Switch it:

1. **Determine prompt-passing mechanism.** Check whether gemini-cli v0.40.1 supports `-p @file` (file reference). Test:
   ```bash
   echo "test prompt" > /tmp/gemini-test.txt
   gemini -y -m gemini-3.1-pro-preview -p @/tmp/gemini-test.txt
   ```
   - If file-ref works: use `-p @PATH` for prompts > 100KB; inline `-p "PROMPT"` for ≤100KB.
   - If only inline works: write to temp file always and use process substitution `$(cat /tmp/...)`, OR inline if small enough.
   - If neither works for large prompts: report back via PR comment; we'll re-design.

2. **Update `cmd` builder** to append `-p` and the prompt (or file ref) after the model+approval flags.

3. **Drop `stdin_payload=prompt`** from the returned `InvocationPlan`. Set to `None` or empty string.

4. **Preserve all other behavior:**
   - `--approval-mode=yolo` for write modes (workspace-write, danger)
   - `--allowed-mcp-server-names` from `tool_config["mcp_server_names"]`
   - Auth mode env unsets (subscription mode strips API env vars)
   - `liveness_signal_paths` — still derived from cwd, untouched
   - `parse_response` — still reads chat session JSON, untouched

5. **Temp-file lifecycle:** if you write prompts to a temp file, ensure cleanup. Use `tempfile.NamedTemporaryFile(delete=False)` with explicit unlink in a `try/finally`, or `tempfile.TemporaryDirectory()` scoped to the InvocationPlan lifetime. Don't leak temp files in `/tmp`.

6. **Logging:** add a debug log line stating prompt length and whether inline or file-ref was used. Helps next debug session.

### `scripts/agent_runtime/runner.py`

If the runner currently opens a stdin pipe based on `stdin_payload`, ensure it correctly handles the case where `stdin_payload` is None/empty — don't open a useless pipe that gemini-cli might still try to read.

### Auth-mode priority flip — API first, OAuth/subscription fallback

User-stated 2026-05-05 20:18 CEST: "we should prio api and then oauth for gemini". Today the policy is reversed — commit `4f0fae3c0b fix(gemini): always-subscription auth-mode policy — blunt fix for #1416` forces subscription/OAuth and strips API env vars. Reverse this:

1. **Default `resolve_gemini_auth_mode()`** (in `scripts/agent_runtime/adapters/gemini.py` or wherever it lives — find via `grep -rn 'def resolve_gemini_auth_mode'`) should return `"api"` when `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) is set in env, falling back to `"subscription"` only when no API key is available.

2. **Existing fallback ladder** (per commit `7444275212 Add Gemini API/OAuth fallback ladder`) should be preserved but the rung order may need adjusting — API rungs first, OAuth/subscription rungs last. Find the ladder via `grep -rn 'fallback' scripts/agent_runtime/`. Verify the ladder still triggers on rate-limit / capacity errors per `805f67413c` and `363b5e3c3e` semantics.

3. **`--no-set-api-key-from-env`** or equivalent: if the adapter currently does `env_unsets = GEMINI_AUTH_ENV_VARS` for subscription mode (line 184-185 today), invert: when API mode is active, KEEP env vars; when subscription mode is active (fallback), strip them.

4. **Document the new precedence** in `docs/best-practices/agent-cooperation.md` (or wherever Gemini auth is documented) and in the adapter docstring.

5. **Bridge env-var hint:** if the user has `KUBEDOJO_GEMINI_SUBSCRIPTION=1`-style env override (per kubedojo `c77aa71e`), respect that override. We use `GEMINI_AUTH_MODE` per `#1184/#1416` — keep that escape hatch. Users who explicitly set `GEMINI_AUTH_MODE=subscription` get subscription regardless of API key presence; users who set `GEMINI_AUTH_MODE=api` get API regardless of OAuth creds.

### Auth-mode acceptance

- [ ] No `GEMINI_API_KEY` set + no `GEMINI_AUTH_MODE` override → subscription/OAuth (preserves current behavior for users without an API key)
- [ ] `GEMINI_API_KEY` set + no `GEMINI_AUTH_MODE` override → **API mode** (NEW default)
- [ ] `GEMINI_AUTH_MODE=subscription` env override → subscription (regardless of API key presence)
- [ ] `GEMINI_AUTH_MODE=api` env override → API (regardless of OAuth creds presence; fail fast if no API key)
- [ ] Fallback ladder triggers API → subscription transition on rate-limit (no behavior change to ladder semantics, only rung order)
- [ ] Unit tests for all four matrix cells above

### Tests

#### Unit test in `tests/test_agent_runtime_gemini_adapter.py` (new file or extend existing)

Parametrized cases:
- Small prompt (200 chars) → cmd contains `-p PROMPT` inline, no stdin
- Large prompt (200 KB) → cmd contains `-p @PATH` file ref (assuming gemini-cli supports it; otherwise document the actual mechanism used)
- `tool_config["mcp_server_names"]` set → cmd contains `--allowed-mcp-server-names sources` (or whatever)
- Auth mode subscription → `env_unsets` includes the GEMINI_AUTH_ENV_VARS
- `effort` arg passed → adapter logs debug message but cmd unchanged (existing semantic)

Mock the actual subprocess call. Don't invoke real gemini-cli in the unit test.

#### Smoke test (new file or extend `tests/test_v7_writer_dispatch.py`)

If feasible without making a real LLM call: parametrize `gemini-tools` writer dispatch with a fake gemini binary on $PATH that just echoes its `-p` argument back. Assert the writer phase consumes that fake output and emits the expected JSONL events. (If too involved for this PR, skip — note in PR body.)

## Numbered execution steps

1. Verify worktree base clean (`git log --oneline HEAD..origin/main` empty). Issue #1709 is already filed.
2. Test gemini-cli `-p @file` capability locally:
   ```bash
   echo "test" > /tmp/gemini-test.txt
   timeout 30 gemini -y -m gemini-3.1-pro-preview -p @/tmp/gemini-test.txt
   ```
   Document result in PR body.
3. Implement adapter changes in `scripts/agent_runtime/adapters/gemini.py`.
4. Update runner.py if needed for stdin handling.
5. Add unit tests. Run `.venv/bin/pytest tests/test_agent_runtime_gemini_adapter.py -v` (or whatever the file ends up named).
6. Smoke test:
   ```bash
   .venv/bin/python scripts/build/v7_build.py a1 my-morning --writer gemini-tools --dry-run
   ```
   Then the actual write (small wall-time risk; user has authorized this fix to verify):
   ```bash
   .venv/bin/python -u scripts/build/v7_build.py a1 my-morning --writer gemini-tools --out /tmp/v7-gemini-smoke --telemetry-out /tmp/v7-gemini-smoke.jsonl
   ```
   Expected: completes within 15 min wall, emits `phase_writer_summary` event, exit 0. If hangs >15 min, kill and report.
7. `.venv/bin/ruff check scripts/agent_runtime/ tests/`
8. **Get review from Claude** (cross-family — Codex is author; Gemini is broken so unavailable; Claude is the only working reviewer):
   ```bash
   git add -A
   git diff --cached > /tmp/issue-1709-diff.txt
   .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-claude \
       "Adversarial review for #1709. Read /tmp/issue-1709-diff.txt. Focus: (1) does the adapter still preserve --approval-mode/--allowed-mcp-server-names/auth-mode semantics? (2) is the temp-file lifecycle leak-safe? (3) are the unit tests sufficient — do they exercise the failure modes (large prompts, missing file, MCP config)? (4) any subtle env or runner changes that could break claude or codex adapters?" \
       --task-id issue-1709-review
   ```
9. Apply feedback or argue back in writing.
10. After review CLEAN: commit with `Reviewed-By: claude-opus-4-7 (issue-1709-review)` trailer.
11. `git push -u origin codex/1709-gemini-adapter-p-flag`
12. `gh pr create --title "fix(gemini): switch adapter from stdin-pipe to -p flag (#1709)"` with body documenting:
    - The reproduction (broken vs working invocation)
    - The mechanism chosen for prompt passing (inline vs `-p @file`)
    - Unit test coverage
    - Smoke test result (wall time, expected events)
    - DO NOT enable auto-merge.

## Constraints

- **No edits on main**, no auto-merge
- **No skip on tests** — if the smoke test hangs, that's the bug, not a reason to skip
- **Don't change v6_build.py** (legacy)
- **Don't change claude or codex adapters**
- **Don't extend the InvocationPlan dataclass** unless necessary; prefer minimal surface change
- **Document the v0.40.1 gemini-cli behavior** you find. The next reader needs to know whether `-p @file` works or whether we used a workaround

## Out of scope

- Writer-level timeout in v7_build.py (#1708 — defense-in-depth, separate PR)
- Resume-logic refinement in bakeoff_run.py (#1707 — separate PR)
- Re-running the bakeoff (orchestrator runs that after this merges)

## Failure expectations

If the smoke test in step 6 hangs again after your fix, that means `-p` has its own non-TTY issue or gemini-cli has a deeper bug. STOP, report what you observed in the PR body, and we'll re-strategize. Don't try a third workaround speculatively.
