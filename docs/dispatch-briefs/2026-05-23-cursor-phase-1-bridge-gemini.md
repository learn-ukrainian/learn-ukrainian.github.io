# Gemini dispatch — `ab ask-cursor` bridge subcommand (cursor-agent integration Phase 1 of 3)

## Mission

Add `ab ask-cursor` to the `scripts/ai_agent_bridge` CLI so the project can route Q&A / discussions / single-shot reads through Cursor Agent (currently default model `composer-2.5`). This mirrors the PR-D1 pattern that added `ab ask-hermes` and `ab ask-opencode` in commit `18f4c20155` (PR #2245). **Quality bar: every action is tool-backed** (MEMORY #M-4).

Phase 1 of a 3-phase integration. Phase 2 (delegate.py adapter) and Phase 3 (V7 writer + reviewer wiring) follow as separate PRs after this one merges.

## Why cursor

User added a cursor subscription with a 10x usage promotion (2026-05-23). Cursor exposes Composer 2.5, GPT-5.5, Opus 4.7, GPT-5.3 codex, and many others through one subscription + CLI. Wiring cursor as a first-class bridge unlocks all of those for Q&A/discussions immediately.

## Reference patterns (READ BEFORE WRITING CODE)

The shape is well-established. Read all three before writing:

1. `scripts/ai_agent_bridge/_opencode.py` — closest analog (text-CLI one-shot via subprocess, default model openrouter/qwen/qwen3.7-max).
2. `scripts/ai_agent_bridge/_hermes.py` — text-CLI one-shot via subprocess, default model qwen/qwen3.6-plus.
3. `scripts/ai_agent_bridge/_cli.py` — registration shape for new `ask-*` subcommands.

Tests: `tests/bridge/` directory contains existing `ask-*` test files. Mirror their structure for `test_ask_cursor.py`.

## Cursor CLI invocation shape (verified by orchestrator 2026-05-23)

Binary: `agent` (symlinked to `~/.local/bin/agent` and `~/.local/bin/cursor-agent`). Auth: OAuth via `agent login` (already authenticated for this user).

Headless one-shot:
```
agent -p PROMPT --model MODEL --output-format text --trust
```

- `-p` / `--print` — non-interactive headless mode (required for scripted use).
- `--model` — model id. Default for `ab ask-cursor` should be `composer-2.5`. The `--list-models` flag enumerates available models.
- `--output-format text` — plain text output. Other choices: `json`, `stream-json`.
- `--trust` — bypasses workspace-trust interactive prompt. Required for non-interactive runs. The judge-style prompts we'll route through `ab ask-cursor` do not request file edits, so `--trust` is safe (it only unlocks shell + write tools if the model decides to use them).
- (Do NOT add `--yolo` or `--approve-mcps` by default — those force-approve any prompted action, which is unsafe for cold Q&A. The opencode/hermes bridges don't auto-approve MCP either.)

Verified smoke test: `agent -p 'Reply with exactly the single word: OK' --model composer-2.5 --output-format text --trust` returns `OK` cleanly in ~2-3s.

## #M-4 deterministic preamble

| Claim in your output | Tool to ground it |
|---|---|
| "Existing bridge file at PATH does X" | `cat scripts/ai_agent_bridge/_opencode.py` and quote the section |
| "Test file at PATH covers Y" | `ls tests/bridge/ && grep -l ...` |
| "CLI register entry point at line N of `_cli.py`" | `grep -n 'ask-opencode\|ask-hermes' scripts/ai_agent_bridge/_cli.py` |
| "Smoke works locally" | run `.venv/bin/python -m scripts.ai_agent_bridge ask-cursor --task-id smoke-test 'Reply: OK'` and paste raw output |
| "Tests pass" | `.venv/bin/python -m pytest tests/bridge/ -q` final summary raw |

## Steps

1. Worktree already provided (`--worktree` mode).
2. Read the 3 reference files in full:
   - `scripts/ai_agent_bridge/_opencode.py`
   - `scripts/ai_agent_bridge/_hermes.py`
   - `scripts/ai_agent_bridge/_cli.py`
3. Read existing tests as structural model:
   - `tests/bridge/test_ask_opencode*.py` (or wherever the PR-D1 tests landed — `grep -rl ask_opencode tests/`)
4. Create `scripts/ai_agent_bridge/_cursor.py` mirroring `_opencode.py`:
   - Module docstring explaining cursor-agent CLI shape (cite the verified invocation above)
   - `CURSOR_DEFAULT_MODEL = "composer-2.5"` constant
   - Subprocess invocation: `agent -p PROMPT --model MODEL --output-format text --trust` (the same args list shown above)
   - Error handling for `FileNotFoundError` (cursor not installed) and `subprocess.TimeoutExpired`
   - Use the same channel-routing / message-shape helpers `_opencode.py` uses
5. Register in `scripts/ai_agent_bridge/_cli.py`:
   - Add `ask-cursor` parser entry mirroring the `ask-opencode` entry exactly
   - Same flags: `--task-id`, `--type`, `--data`, `--model`, `--from`, `--from-model`, `--to-model`, `--no-timeout`, `content` positional
   - Default `--model` value: `composer-2.5`
6. Add tests at `tests/bridge/test_ask_cursor.py`:
   - Mirror the test cases in `test_ask_opencode*.py`
   - Mock the `subprocess.run` call so tests don't hit the real cursor-agent
   - Cover: default-model invocation, custom `--model` override, `FileNotFoundError` path, timeout path, stdin content via `content='-'`
   - Aim for ~8 test cases matching the opencode test file's coverage
7. Run targeted tests: `.venv/bin/python -m pytest tests/bridge/ -q --timeout 30`. Paste raw final summary.
8. Run smoke (NETWORK CALL — ~5s, no cost since you have subscription):
   ```
   # venv symlinked from main checkout
   .venv/bin/python -m scripts.ai_agent_bridge ask-cursor --task-id smoke-test 'Reply with exactly the single word: OK'
   ```
   Paste raw output. Expect to see `OK` in the response.
9. `.venv/bin/ruff check scripts/ai_agent_bridge/_cursor.py tests/bridge/test_ask_cursor.py scripts/ai_agent_bridge/_cli.py` — expect clean.
10. `git add scripts/ai_agent_bridge/_cursor.py scripts/ai_agent_bridge/_cli.py tests/bridge/test_ask_cursor.py`
11. Commit: `feat(bridge): ab ask-cursor subcommand (cursor-agent / composer-2.5 — Phase 1 of cursor integration)`
12. `git push -u origin <branch>`
13. `gh pr create --title "feat(bridge): ab ask-cursor subcommand (cursor-agent / composer-2.5 — Phase 1)" --body "<summary + smoke output + test plan>"`
14. **NO auto-merge.** Orchestrator reviews.

## Hard scope limits

- **Phase 1 = bridge subcommand ONLY.** Do NOT touch:
  - `scripts/agent_runtime/adapters/` (Phase 2)
  - `scripts/delegate.py` `--agent` choices enum (Phase 2)
  - `scripts/build/linear_pipeline.py` (Phase 3)
  - `scripts/build/phases/linear-write*.md` (Phase 3)
  - `scripts/config/agent_fallback_substitutions.yaml` (Phase 2)
  - V7 writer/reviewer registration anywhere (Phase 3)

If `_cli.py` registration also requires a touch to `__init__.py` or `__main__.py` for module-import discoverability, do that — it's part of registering the bridge. But nothing outside `ai_agent_bridge/` + `tests/bridge/`.

## Acceptance criteria

- `ab ask-cursor` is a working CLI subcommand parallel to `ab ask-opencode`.
- `.venv/bin/python -m scripts.ai_agent_bridge ask-cursor --help` shows the new subcommand.
- Smoke output (the literal `OK` reply from composer-2.5) is quoted in the PR body.
- Tests pass.
- PR opens cleanly with no out-of-scope file changes.
