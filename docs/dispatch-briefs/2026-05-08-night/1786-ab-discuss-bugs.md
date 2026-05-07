# Dispatch brief: ab discuss + ask-* infrastructure bugs (#1786)

> **Issue:** #1786. Single PR closes the issue (preferred for atomicity).
> **Scope:** ~100-150 LOC + tests across `_channels_cli.py` and discuss-subagent spawning.
> **Agent:** Codex
> **Worktree:** mandatory.

## Worktree instructions (mandatory)

```bash
.venv/bin/python scripts/delegate.py dispatch \
    --agent codex --mode danger --worktree --base origin/main \
    --task-id codex-1786-ab-discuss-bugs \
    --prompt-file docs/dispatch-briefs/2026-05-08-night/1786-ab-discuss-bugs.md
```

## What to build

Three independent fixes in one PR. They share test setup so atomicity helps.

### Fix B.1 — `ab discuss` truncates root message in round-2+ prompts

**Symptom**: Round-2+ agents see `... [N older messages omitted] ...` in their prompts and the original question is gone.

**Diagnosis** (verbatim, from `architecture` thread `1c1b5d54966742ffacd1bf60e0893c1c`):
> "In round 2 my prompt shows `... [15 older messages omitted] ...` — the root message was truncated out entirely from my view. With `needed_history = 1 + N*max_rounds + 10` (see `scripts/ai_agent_bridge/_channels_cli.py:1256`), the design is to preserve the root, so the truncation happened at the prompt-render boundary, not from history sizing."

**Fix**: in `_channels_cli.py:1256` (or the prompt-render boundary nearby), pin the root message into the prompt unconditionally — it's the question, it must always be visible. Truncate against history, not the root.

**Test**: discussion with `--max-rounds 4` in a channel with 200+ prior msgs; assert root message body appears verbatim in round-4 prompt.

### Fix B.2 — Discuss subagent missing `Write` + `ExitPlanMode`

**Symptom**: Round-1 and round-2 Claude replies come back with "I have a tooling problem" complaints. Subagent has `Glob, Grep, LSP, Read, MCP sources, MCP claude_ai_Google_Drive` but is missing `Write, Edit, Bash, Agent, ExitPlanMode, AskUserQuestion`.

**Decide which fix is right** (do not arbitrarily pick — verify):
1. **Option A**: Don't put discuss subagents in plan mode. They're commenting, not planning. If this is the right call, find the spawn site and remove plan mode.
2. **Option B**: Plan mode is intentional (e.g. for safety in shared channel). Then attach `Write` + `ExitPlanMode` to the allowed-tools list so the subagent can complete the workflow.

**Investigate first**: trace where the subagent is spawned. Look at the system-prompt and tool-allowlist construction. The right fix depends on intent.

**Test**: spawn a discuss subagent, capture its tool list, assert it has `Write` (or that it's not in plan mode at all).

### Fix B.3 — `ask-*` defaults `--from` to "gemini"

**Symptom**: When Claude (orchestrator) calls `ask-codex` without `--from claude`, broker logs `From: gemini → To: codex`. Misleading telemetry.

**Fix**: detect caller identity from environment. Suggested order:
1. If `CLAUDE_AGENT_NAME` env var set, use that
2. Else if `CODEX_SESSION` env var set, default to "codex"
3. Else if running under a known wrapper, infer
4. **Fall through to error**, not to "gemini" — better to fail loud than mislabel

**Test**: invoke `ask-codex` with no `--from`, no `CLAUDE_AGENT_NAME`, no `CODEX_SESSION` → expect non-zero exit with informative error. With `CLAUDE_AGENT_NAME=claude` → expect "from claude".

## Acceptance criteria

- B.1 fix lands with regression test (root preserved in round-N prompt for N up to max-rounds, in a channel with >200 prior msgs)
- B.2 fix decided + applied (option A or B chosen with explicit rationale in PR body) with regression test
- B.3 fix lands with regression test asserting `--from` is caller-detected, not hardcoded
- All three changes in single PR for atomicity
- `docs/best-practices/agent-bridge.md` updated if behavior changes user-visibly
- `ruff check` clean
- `.venv/bin/pytest tests/ai_agent_bridge/ -x` passes

## Numbered execution steps

1. `git worktree add` — handled by delegate runner.
2. Read `scripts/ai_agent_bridge/_channels_cli.py` (focus around line 1256, plus the discuss-spawning logic).
3. Read `scripts/ai_agent_bridge/__main__.py` for the `ask-*` and `discuss` entry points.
4. Read `docs/best-practices/agent-bridge.md` for current documented behavior.
5. Pull the failed-discussion thread for context (commands in `docs/session-state/2026-05-07-kubedojo-paradigm-followups.md` "Don't lose this evidence" section) — only if helpful.
6. Implement B.1 fix.
7. Implement B.2 fix (with rationale in commit message and PR body).
8. Implement B.3 fix.
9. Add regression tests for all three.
10. Run `.venv/bin/ruff check` on touched files.
11. Run `.venv/bin/pytest tests/ai_agent_bridge/ -x` (or wherever the bridge tests live).
12. Commit: `fix(ab-bridge): root preserved in discuss rounds, subagent tools fixed, ask-* --from defaults from env (#1786)`
13. `git push -u origin codex-1786-ab-discuss-bugs`
14. `gh pr create` with detailed body covering all 3 fixes + the B.2 option-A-vs-B decision.
15. **Do NOT auto-merge.** Report PR URL.

## Out of scope

- Don't refactor the broker DB schema.
- Don't change `discuss --max-rounds` semantics or convergence detection.
- Don't add new channel features.
