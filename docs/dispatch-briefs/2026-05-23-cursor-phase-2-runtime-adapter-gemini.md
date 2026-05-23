# Gemini dispatch — Cursor runtime adapter (Phase 2 of 3)

## Mission

Add `cursor` as a first-class agent in `scripts/agent_runtime/` so `scripts/delegate.py --agent cursor` can dispatch code work to cursor-agent (binary: `agent` / `cursor-agent`). This mirrors the existing codex/gemini/opencode/hermes adapters and unlocks `composer-2.5` (and via subscription: gpt-5.5, claude-opus-4-7-thinking-high, gpt-5.3-codex, grok-4.20-reasoning) for `delegate.py` execution paths.

**Phase 2 of 3.** Phase 1 (bridge `ab ask-cursor`) shipped as PR #2252 / commit `c6d4345119`. Phase 3 (V7 writer/reviewer wiring) is a separate dispatch after Phase 2 merges — DO NOT touch Phase 3 surfaces in this PR.

**Quality bar:** every claim in your output tool-backed (MEMORY #M-4). Every test that touches a file you change must be discovered + run (the #2253 regression-class fix; see Step 2 below).

## Design spec — READ FIRST

`docs/dispatch-briefs/2026-05-23-cursor-phase-2-3-v7-writer-reviewer-design.md` is the **load-bearing** spec for Phase 2 + Phase 3. Read it in full before touching any code. The "Orchestrator review — incorporated before dispatch" block at the top lists three non-negotiables, two of which apply to Phase 3 but inform Phase 2's adapter shape.

Phase 2 scope from the spec:
- §1 (Adapter shape) — entire section
- §2 (`--trust` / `--approve-mcps` / `--yolo` security boundary) — entire section
- §6 (Tests that must be updated) → "Phase 2 — adapter + registry + delegate" table

Phase 3 sections (§3, §4, §5, §6 Phase 3 rows) are **out of scope** for this PR.

## Reference adapters — READ BEFORE WRITING CODE

| Adapter | Why read |
|---|---|
| `scripts/agent_runtime/adapters/gemini.py` | Stdout-based I/O pattern (no `-o` file), rate-limit detection, `effort` no-op logging. Cursor mirrors this for I/O. |
| `scripts/agent_runtime/adapters/codex.py` | Per-invocation MCP scoping via `tool_config` env/path overrides. Cursor mirrors this for `cursor_workspace` config. |
| `scripts/agent_runtime/adapters/hermes_qwen.py` | Liveness `()` pattern when no mtime file exists. |
| `scripts/agent_runtime/registry.py` | Registration shape (AGENTS dict, ~L37–157). |
| `scripts/agent_runtime/tool_config.py` | `_canonical_agent_name` (~L23–39), `build_mcp_tool_config` (~L171+). |
| `scripts/delegate.py` | `--agent` choices enum (~L1552–1554). |

## #M-4 deterministic preamble — verifiable claims and tools

| Claim in your PR body or commit | Tool to ground it |
|---|---|
| "Gemini adapter's writer-path arg list is X" | `grep -n 'build_invocation' scripts/agent_runtime/adapters/gemini.py` + paste raw |
| "Codex adapter handles per-invocation MCP via Y" | `grep -n 'tool_config\|CODEX_HOME' scripts/agent_runtime/adapters/codex.py` + paste raw |
| "Registry entry shape mirrors X" | `grep -A8 '"codex":\|"gemini":\|"opencode":' scripts/agent_runtime/registry.py` + paste raw |
| "Adapter tests pass" | `.venv/bin/python -m pytest tests/agent_runtime/adapters/ tests/test_agent_runtime.py -q` final summary |
| "Tests touching files I changed all run" | `discover_tests_for_files.sh` (Step 2 below) — paste the output list, then run them |
| "Smoke works" | `.venv/bin/python scripts/delegate.py dispatch --agent cursor --model composer-2.5 --dry-run --task "echo OK"` — paste raw |
| "Lint clean" | `.venv/bin/ruff check <files>` + raw `All checks passed!` line |
| "Commit landed" | `git log -1 --oneline` raw |
| "PR opened" | `gh pr view --json url` raw URL |

## Steps

1. Worktree provided (`--worktree` mode). Confirm with `git rev-parse --show-toplevel` + paste raw.

2. **Test-discovery (the #2253 fix — non-negotiable).** Before writing code, list every test file that already references the files you'll touch:

   ```bash
   for f in \
     scripts/agent_runtime/registry.py \
     scripts/agent_runtime/tool_config.py \
     scripts/delegate.py; do
     echo "=== tests referencing $f ==="
     grep -rl "$(basename $f .py)" tests/ 2>/dev/null
   done
   ```

   Paste raw output. Every file in that list MUST be run as part of Step 11 (regression check). The bug that produced PR #2253 was a brief that listed tests from memory instead of discovering them — do not repeat.

3. Read the 6 reference files listed above in full. Quote the relevant section in your commit body (e.g. "gemini.py L302–313 stdin-payload pattern").

4. Read the design spec §1 + §2 + §6-Phase-2 in full.

5. Create `scripts/agent_runtime/adapters/cursor.py`:

   ```python
   class CursorAdapter:
       name: str = "cursor"
       default_model: str = "composer-2.5"
       supported_modes: frozenset[str] = frozenset({"read-only", "workspace-write", "danger"})
   ```

   Binary resolution mirrors the bridge:
   ```python
   cursor_bin = shutil.which("agent") or shutil.which("cursor-agent") or "agent"
   ```

   `build_invocation()` — argv shapes from spec §1:
   - **Writer path** (`mode="workspace-write"`):
     `agent -p [stdin] --model <m> --output-format stream-json --trust --approve-mcps --mode plan --sandbox enabled --workspace <cwd>`
   - **Reviewer path** (`mode="read-only"`):
     `agent -p [stdin] --model <m> --output-format stream-json --trust --mode ask --workspace <cwd>`
   - **Danger mode** (`mode="danger"`): same as writer path but NO `--mode plan` (file edits allowed). Use sparingly — most delegate calls should use `workspace-write` or `read-only`.
   - **DO NOT pass `--yolo` / `--force` in any path.** See spec §2 "What not to use".

   Prompt delivery via stdin (mirror gemini.py L302–313). Parse stdout as JSONL via `parse_json_events(..., source="cursor")`, normalize tool calls via `normalize_tool_calls`, return `ParseResult` with `tool_calls` populated. Rate-limit detection: stderr/stdout pattern match mirroring gemini.py L405–439.

   `tool_config` keys handled (document in docstring; ignore unknown):
   ```python
   {
       "output_format": "stream-json",
       "cursor_workspace": str,
       "approve_mcps": bool,
       "cursor_mode": "plan" | "ask",
       "sandbox": "enabled" | "disabled",
   }
   ```

   `effort` is logged + no-op (cursor CLI has no equivalent flag today). Liveness returns `()` (rely on stdout streaming, like Hermes).

6. Register in `scripts/agent_runtime/registry.py`:

   ```python
   "cursor": {
       "adapter": "scripts.agent_runtime.adapters.cursor:CursorAdapter",
       "default_model": "composer-2.5",
       "cost_tier": "low",
       "capabilities": frozenset({"content_writing", "content_review", "adversarial_review"}),
       "cli_available": True,
       "resume_policy": "never",
   },
   ```

7. Extend `scripts/agent_runtime/tool_config.py`:
   - `_canonical_agent_name()` (~L23–39): `if agent.startswith("cursor"): return "cursor"`
   - `build_mcp_tool_config()` (~L171+): cursor branch returning the dict shape above. Diagnostic `config_path` should point at `{workspace}/.cursor/mcp.json` (not repo `.mcp.json`).

   **Important:** for Phase 2, the `workspace` value defaults to `cwd` of the subprocess. The actual scoped-workspace materialization (`_ensure_cursor_writer_workspace`) lands in Phase 3 — for Phase 2 just expose the config shape so adapters can pass through `cursor_workspace` when callers supply it.

8. Extend `scripts/delegate.py` `--agent` choices enum (~L1552–1554): add `"cursor"`.

9. Create tests (mirror the existing patterns; discover what already exists first):
   - **`tests/agent_runtime/adapters/test_cursor_adapter.py`** (NEW) — argv assembly per mode (writer / reviewer / danger), `--yolo` absent in ALL paths, `tool_config` translation, `parse_response` on a fixture stdout. Use `shutil.which` mock so tests don't need cursor-agent installed.
   - **`tests/test_agent_runtime.py`** — extend `test_registry_has_known_agents` (~L168–179) hardcoded agent set with `"cursor"`; add `test_load_adapter_cursor`; extend `test_validate_agent_name_rejects_tools_suffix` parametrize (~L233) with `("cursor-tools", "cursor")`.
   - **`tests/test_cursor_integration.py`** (NEW, mirror `tests/test_grok_integration.py`) — registry exposes `cursor`; `delegate.py dispatch --agent cursor --dry-run` parses.

10. `.venv/bin/ruff check scripts/agent_runtime/adapters/cursor.py scripts/agent_runtime/registry.py scripts/agent_runtime/tool_config.py scripts/delegate.py tests/agent_runtime/ tests/test_agent_runtime.py tests/test_cursor_integration.py` — expect `All checks passed!`. Paste raw.

11. Run **all** tests discovered in Step 2 + new test files:

    ```bash
    # venv symlinked from main checkout — see docs/best-practices/code-quality.md
    .venv/bin/python -m pytest \
      tests/agent_runtime/ \
      tests/test_agent_runtime.py \
      tests/test_cursor_integration.py \
      tests/bridge/test_ask_cursor.py \
      <any-other-files-discovered-in-step-2> \
      -q --timeout 30
    ```

    Paste raw final summary (`N passed in M.MMs`). If any test fails, FIX IT — do not skip, do not lower coverage. Pre-commit passing != tests passing (#M-7).

12. Dry-run smoke:
    ```bash
    # venv symlinked
    .venv/bin/python scripts/delegate.py dispatch --agent cursor --model composer-2.5 --dry-run --task "echo OK" 2>&1 | tail -20
    ```
    Paste raw. Expect clean parse — no traceback.

13. `git add scripts/agent_runtime/adapters/cursor.py scripts/agent_runtime/registry.py scripts/agent_runtime/tool_config.py scripts/delegate.py tests/agent_runtime/adapters/test_cursor_adapter.py tests/test_agent_runtime.py tests/test_cursor_integration.py`

14. Commit:
    ```
    feat(runtime): cursor adapter (cursor-agent / composer-2.5 — Phase 2 of cursor integration)

    Adds CursorAdapter alongside codex/gemini/opencode in scripts/agent_runtime/.
    Enables `delegate.py --agent cursor` for code-execution dispatches via the
    cursor-agent CLI (`agent`). Mirrors gemini I/O + codex MCP scoping patterns.

    Writer path uses --mode plan + --approve-mcps + --sandbox enabled (no --yolo).
    Reviewer path uses --mode ask (read-only, no MCP). All paths use --trust for
    headless workspace-trust bypass.

    Phase 1 bridge (`ab ask-cursor`) shipped in PR #2252 / commit c6d4345119.
    Phase 3 (V7 writer/reviewer wiring + SELF_REVIEW_DETECTED hardening) is a
    separate PR per docs/dispatch-briefs/2026-05-23-cursor-phase-2-3-v7-writer-reviewer-design.md.
    ```

15. `git push -u origin <branch>`

16. `gh pr create --title "feat(runtime): cursor adapter — Phase 2 of cursor integration" --body "<summary + design-spec link + smoke output + test plan + tests-discovered list from Step 2>"`

17. **NO auto-merge.** Orchestrator reviews + merges.

## Hard scope limits — Phase 3 forbidden surfaces

DO NOT touch in this PR (each is Phase 3):

- `scripts/build/linear_pipeline.py` — WRITER_*, REVIEWER_*, WRITER_SPECIFIC_DIRECTIVES, `_runtime_tool_config`, `_ensure_cursor_writer_workspace`, `invoke_writer`
- `scripts/build/v7_build.py` — WRITER_ALIASES, `_reviewer_for_writer`, `_run_llm_qg`
- `scripts/build/phases/linear-write*.md` — writer prompt
- `scripts/audit/checks/review_gaming.py` — `_model_family` hardening (Phase 3 required gate)
- `claude_extensions/rules/pipeline.md` — policy doc update (Phase 3)
- `scripts/config/agent_fallback_substitutions.yaml` — fallback map (could optionally add to Phase 2 if trivial; skip otherwise)

If you find yourself editing any of those, STOP — that's Phase 3 work. Open Phase 2 PR with what you have.

## Acceptance criteria

- `delegate.py --agent cursor --dry-run --task ...` parses cleanly (no traceback).
- `delegate.py --help` shows `cursor` in `--agent` choices.
- `agent_runtime` registry exposes `cursor` with `default_model="composer-2.5"`.
- All tests discovered in Step 2 + new tests pass.
- Ruff clean.
- No out-of-scope file changes (Phase 3 surfaces untouched).
- PR body cites: design-spec doc, tests-discovered list, dry-run smoke raw output, test summary raw output.

## Estimated LOC budget

~250–300 LOC total:
- `adapters/cursor.py`: ~150 LOC
- `registry.py` + `tool_config.py` + `delegate.py`: ~30 LOC
- Tests: ~100 LOC across 3 files

Over budget? Stop and re-scope — likely you crossed into Phase 3.

---

## Related docs

- Design spec: `docs/dispatch-briefs/2026-05-23-cursor-phase-2-3-v7-writer-reviewer-design.md`
- Phase 1: `docs/dispatch-briefs/2026-05-23-cursor-phase-1-bridge-gemini.md`
- Agent runtime guide: `docs/agent-runtime-guide.md`
- Session context: `docs/session-state/2026-05-23-judge-cal-leaderboard-cursor-wired-issues-sweep.md`
