# Grok Infra Session Handoff — 2026-07-09

**Agent:** Grok (xAI)
**Focus:** Infra & harness reliability under epic #4707 (explicit issues: 4321, 4358, 4609 + memory capture)
**Session type:** Routing/bridge fixes + durable operational memory + session handoff preparation

> **For a brand new clean Grok session (load this first):**
> Follow the checklist below exactly. This file + the shared MEMORY + recent PRs give you full context. Do not start coding until you have run the cold-start steps.

## New Clean Session Cold-Start Checklist (MANDATORY)

1. `cd /Users/krisztiankoos/projects/learn-ukrainian` (or your workspace root)
2. `git status --short --branch`
3. `git worktree list`
4. **Read this entire file.**
5. Read the durable memory: `agents_extensions/shared/memory/MEMORY.md` (fleet, bridge, API, CodexBar sections) and `agents_extensions/codex/memory/MEMORY.md` (cross-ref).
6. `cat docs/session-state/current.grok.md` (if present) and the newest `docs/session-state/*grok*.md`.
7. If the local Monitor API is running (`npm run api` or equivalent in another terminal):
   - `curl -s http://localhost:8765/api/state/summary`
   - `curl -s http://localhost:8765/api/state/orient`
   - `curl -s http://localhost:8765/api/state/manifest`
8. `gh pr list --state open --limit 20`
9. `gh issue list --state open --search "4707 or 4609 or 4321 or 4358" --limit 10`
10. Re-confirm user identity and preferences: Hungarian male who loves k8s and the Ukrainian language.
11. Review any open grok dispatch worktrees before touching code.
12. **Never pick new harness-stream infra issues without first consulting the user** (harness stream is primarily Claude's lane).

Only after completing the checklist, report status and ask "ready for next task?" or "continue with X?"

## User Context
- Hungarian male.
- Loves Kubernetes (k8s) and the Ukrainian language (this project is a perfect intersection).
- Prefers direct execution, high quality, no shortcuts. Use precise tool-backed facts.
- Communication style: concise, technical, values proper handoffs for session switches.

## Current Work State (as of 2026-07-09)

### Completed + Merged
- **#4321 + #4358** (DeepSeek first-party default + fleet reliability + egress guard):
  PR #4815 merged.
  - `scripts/agent_runtime/adapters/hermes_deepseek.py`: default_provider="deepseek", provider_forced=True.
  - Guard `is_deepseek_first_party_forbidden_in_ci` (with PYTEST_CURRENT_TEST bypass for tests).
  - Opt-in via `--provider openrouter`.
  - Tests updated. Issues closed where appropriate.
  - X-Agent trailers used.

- **Memory capture PR** (durable fleet + API + CodexBar knowledge):
  PR #4819 merged.
  Updated:
  - `agents_extensions/shared/memory/MEMORY.md` (major new section on fleet comms, ask-*/discuss via bridge, delegate --worktree, Monitor API cold-start sequence, CodexBar.app vs project tools like codex-usage / cost_report.py / /api/runtime/*, gh/MCP, dependabot handling).
  - `agents_extensions/codex/memory/MEMORY.md` (cross-reference).
  - `agents_extensions/shared/quick-ref/monitor-api.md` (cold-start sequence + usage; fixed fence/spelling from review).
  - All changes reviewed by Codex via bridge (`ask-codex --review`).

### In Progress / Open
- **#4609**: `[bridge] openai_proxy._gemini_backend() completions still invoke retired gemini CLI`
  **PR #4818** (branch `grok/4609-openai-proxy-agy`) — **OPEN**, **MERGEABLE**, **CLEAN** (as of latest checks).
  Worktree: `.worktrees/dispatch/grok/4609-openai-proxy-agy` (commit 9f1364ab75 "test(bridge): update proxy gemini tests for AGY model names...")

  Key changes landed:
  - Migrated `_gemini_backend` to use AgyAdapter (consistent with health probe in sibling work).
  - Model resolution now uses AGY display labels: "Gemini 3.1 Pro (High)", "Gemini 3.5 Flash (High)", etc. (via `_AGY_MODEL_BY_NORMALIZED` + `_normalize_model`).
  - Large-prompt handling: manual command construction with `["agy", "-p", "-", "--model", agy_model]` + stdin (avoids argv length limits; fixed arg-max regression).
  - `_run_backend_command` accepts env override.
  - Routes and tests updated (`tests/agent_runtime/adapters/test_openai_proxy.py`).
  - Addressed Codex review feedback (spelling, fence, model names, stdin path).
  - Commits carry `X-Agent: grok/4609-openai-proxy-agy`.

  **Next actions (do in order):**
  1. Re-confirm latest `gh pr checks 4818` (or watch) — recent run showed Test (pytest) pass, CI Gate pass, ruff pass, etc. Many other gates skipping (normal for this change).
  2. If all relevant checks green and mergeable: `gh pr merge 4818 --squash --delete-branch`.
  3. Cleanup:
     `git worktree remove .worktrees/dispatch/grok/4609-openai-proxy-agy`
     `git branch -d grok/4609-openai-proxy-agy`
  4. Close #4609 with a comment including the X-Agent trailer and summary of what was delivered.
  5. Update this handoff or create follow-up dated note if needed.
  6. Report to user: "4609 closed. Ready to pick next issue?"

### Git / Hygiene State
- Primary checkout on `main` (up to date with origin after prior resets).
- Relevant grok worktree still active for 4609 until cleanup.
- All work strictly in `.worktrees/dispatch/grok/<task>/` subtree layout.
- Main had an untracked copy of an earlier version of this handoff (created outside worktree in prior steps). Authoritative version now committed via this handoff-final worktree.
- No status/*.json, audit/*-review.md, review/*-review.md, or data/telemetry files in changes.
- `.python-version` untouched (3.12.8).
- All Python calls use `.venv/bin/python`.
- Every commit has `X-Agent: grok/...` trailer.

Other active worktrees (do not touch):
- Various agy/, codex/, claude-*, cursor/* etc.

## Key Operational Knowledge (condensed — read the MEMORY files for full detail)

**Fleet communication & delegation:**
- ` .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-codex "..." --task-id foo --review `
- ` .venv/bin/python scripts/ai_agent_bridge/__main__.py discuss ... `
- ` scripts/delegate.py dispatch --agent codex --brief ... --worktree `
- Always pass `--worktree` for Codex/Gemini/Claude dispatches that edit.

**Local Monitor API (cold start + status):**
- Start: usually `npm run api` (or the project's monitor server).
- `http://localhost:8765/api/state/manifest`
- `http://localhost:8765/api/state/orient`
- `http://localhost:8765/api/state/summary`
- `http://localhost:8765/api/state/failing?track=...`
- `http://localhost:8765/api/runtime/agents`, `/api/delegate/active`, contracts, etc.
- Use for queue, build status, active dispatches instead of guessing from memory.

**CodexBar.app vs project tools:**
- CodexBar.app is the local Mac app showing 5h/weekly/monthly usage.
- Project equivalents: `codex-usage`, `scripts/cost_report.py`, dashboards, `/api/runtime/*` endpoints.
- When on limit, the project routes via harness substitutions (see `scripts/config/agent_fallback_substitutions.yaml`).

**gh + MCP:**
- Use `gh` CLI directly for PRs, issues, checks.
- MCP github server available for advanced queries (search first with search_tool then use_tool).

**Dependabot:**
- Handle via normal PR review/merge flow. Recognized by subject or committer.

**Session handoffs:**
- Use `docs/session-state/YYYY-MM-DD-<agent>-<topic>.md`
- For Codex threads there is also `thread_handoff.py` and `.agent/*-thread-handoff.md` (gitignored local).
- Always produce loadable handoff before user switches to a fresh clean session.

## Completed Verification in This Session (highlights)
- DeepSeek guard now properly bypasses under `PYTEST_CURRENT_TEST`.
- openai_proxy large prompt regression fixed (stdin not argv).
- AGY model names resolved to user-facing labels.
- All PRs used worktrees + trailers + cross-family review (Codex).
- Memory additions survived review (spelling "CodexBar", fence fixes applied).
- Main cleaned (reset --hard where needed after merges).

## What to Do in the Next Session
- Finish the 4818 merge + cleanup + #4609 close (see "In Progress" section).
- Once done, tell the user the current assigned items are complete and ask what to pick next (or whether to take another from the harness epic list).
- Keep all future edits in proper dispatch/grok/ worktrees.
- Update handoff early when context is about to be lost (user explicitly wants loadable handoff on session switch).
- Max quality, tool-backed claims, no artifacts.

## Useful Commands

```bash
# Orientation
git status --short --branch
git worktree list

# Monitor API (if running)
curl -s http://localhost:8765/api/state/summary | cat
curl -s http://localhost:8765/api/orient | cat

# Fleet
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-codex "review this please" --task-id review-4818 --review -
.venv/bin/python scripts/delegate.py dispatch --agent codex --worktree --brief ...

# PR hygiene
gh pr checks 4818 --watch
gh pr merge 4818 --squash --delete-branch

# Post-merge cleanup (after merge)
git worktree remove .worktrees/dispatch/grok/4609-openai-proxy-agy
git branch -d grok/4609-openai-proxy-agy

# Handoff creation pattern (when needed)
# (edit docs/session-state/ under a grok dispatch worktree, commit with trailer)
```

## Notes for Successor Grok
- Detailed conversation transcript segments (when present) live in local Grok session storage under the user's home directory (machine-specific, never committed to the repo). Rely on this handoff file, agents_extensions/*/MEMORY.md, PR bodies, and git history for portable context across clean sessions.
- Always run the full checklist on cold start.
- The user will say something like "switch to a new clean session" when they want to start fresh — have the handoff ready and committed.

**Handoff prepared so a new clean Grok session can load full context at start without loss.**

X-Agent: grok/2026-07-09-handoff-final
