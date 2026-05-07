# Codex dispatch brief — #1754 Claude headless OAuth (USER env var)

> **Worktree:** `.worktrees/dispatch/codex/1754-keychain-user-env`
> **Branch:** `codex/1754-keychain-user-env`
> **Base:** `main`
> **Mode:** danger
> **Effort:** medium
> **Hard timeout:** 1800s (30 min — small fix)
> **Reviewer:** Claude (orchestrator, inline post-PR)

## Worktree instructions (mandatory)

Work in a git worktree at `.worktrees/dispatch/codex/1754-keychain-user-env`. Do NOT create a feature branch in the main checkout. Concrete setup:

```bash
git worktree add -b codex/1754-keychain-user-env .worktrees/dispatch/codex/1754-keychain-user-env
cd .worktrees/dispatch/codex/1754-keychain-user-env
# do work, commit, push
```

The main checkout stays untouched on `main`. After PR merges, the orchestrator cleans up the worktree.

## Goal

Fix #1754: `delegate.py dispatch --agent claude` fails with `Not logged in · Please run /login` on a Claude Pro/Max OAuth machine without `ANTHROPIC_API_KEY` set.

## Root cause (already diagnosed — do not re-investigate)

The diagnosis is empirically validated by the orchestrator. **Trust this and just implement.**

`scripts/agent_runtime/env_sanitize.py` builds a scrubbed env for spawned agent processes. Claude CLI on macOS retrieves OAuth tokens from the **macOS keychain**, not from env vars. The keychain lookup uses `$USER` (and some libs fall back to `$LOGNAME`) to determine which user's keychain to query. The current `_SAFE_NAME_ALLOWLIST` does NOT include `USER` or `LOGNAME`, so keychain lookup silently fails → CLI reports "Not logged in".

Reproduction (validated by orchestrator):

```bash
# Fails ("Not logged in"):
env -i HOME=$HOME PATH=$PATH claude -p "say PONG" --model claude-haiku-4-5

# Works ("PONG"):
env -i HOME=$HOME PATH=$PATH USER=$USER claude -p "say PONG" --model claude-haiku-4-5
```

Adding `USER` alone fixes it; adding `LOGNAME` is defense-in-depth for libs that prefer it.

## Implementation

### 1. Code change (2 lines)

`scripts/agent_runtime/env_sanitize.py` — add `USER` and `LOGNAME` to `_SAFE_NAME_ALLOWLIST` (around line 38). Keep alphabetical order. Preserve existing `ANTHROPIC_API_KEY` / `CLAUDE_API_KEY` allowlist for non-OAuth users — both paths must continue to work.

### 2. Tests

Add to `tests/test_env_sanitize.py` (create if missing — check first):

- `test_user_and_logname_pass_through` — assert `build_agent_env(provider="claude")` includes `USER` and `LOGNAME` if present in `os.environ`.
- `test_user_logname_not_provider_specific` — assert pass-through happens for ALL providers (gemini/codex/bridge too — they're benign for any subprocess).
- `test_anthropic_api_key_still_passes_through_for_claude` — regression test: API-key fallback path is preserved.
- `test_secrets_still_scrubbed` — regression test: `GITHUB_TOKEN` (sensitive name) still gets stripped.

### 3. Subprocess integration test

Add `tests/test_claude_dispatch_keychain.py`:

- Skip on non-macOS (`sys.platform != "darwin"`) AND when keychain is not available (e.g., CI without OAuth).
- Spawn `claude -p "say PONG"` via subprocess with `env=build_agent_env(provider="claude")`.
- Assert exit 0 and stdout contains "PONG".

This is the gate that proves the fix works end-to-end. Mark with `pytest.mark.macos_keychain` or skip-if so CI doesn't fail.

### 4. Documentation

Add a section to `docs/best-practices/agent-bridge.md` titled **"Spawned-agent env hygiene — what's allowed and why"**. Document:
- The `_SAFE_NAME_ALLOWLIST` and why `USER` + `LOGNAME` are safe to pass (they're identity vars, not secrets).
- The provider-specific token allowlist (`ANTHROPIC_API_KEY`, `GH_TOKEN`, etc).
- The "Claude OAuth uses macOS keychain → needs `USER`" gotcha so future debugging is faster.

Reference #1754 in the section.

## Validation before opening PR

```bash
.venv/bin/pytest tests/test_env_sanitize.py -v
# If on macOS with keychain:
.venv/bin/pytest tests/test_claude_dispatch_keychain.py -v
.venv/bin/ruff check scripts/agent_runtime/env_sanitize.py tests/
```

Plus a smoke test: actually run a tiny Claude dispatch from your worktree and confirm it returns:

```bash
.venv/bin/python scripts/delegate.py dispatch \
    --agent claude --model claude-haiku-4-5 --mode read-only \
    --task-id smoke-1754 --hard-timeout 60 \
    --prompt "say only the word PONG"
# Expect: status done, stdout "PONG"
```

## PR

Open as `fix(env_sanitize): add USER + LOGNAME for macOS keychain access (#1754)`.

PR body must include:
- Root cause (one paragraph)
- The before/after `env -i` reproduction
- Confirmation that ANTHROPIC_API_KEY fallback is preserved
- Note that GH_TOKEN passthrough (#1752) is unrelated — this is the OAuth-keychain analog
- `Closes #1754`

**NO auto-merge.** Orchestrator (Claude) reviews and merges.

## Acceptance criteria mapping (from #1754)

- [x] Diagnose why headless Claude CLI fails OAuth in dispatch subprocess → **macOS keychain access requires `$USER`**
- [ ] Fix so `delegate.py dispatch --agent claude` succeeds on Pro/Max OAuth machine without `ANTHROPIC_API_KEY` → 2-line allowlist add
- [ ] Preserve API-key fallback → no changes to provider secret allowlist
- [ ] Don't leak Anthropic credentials to other dispatches → `USER`/`LOGNAME` are identity vars, not creds
- [ ] Don't break interactive Claude → no changes to interactive path
- [ ] Unit test → `test_env_sanitize.py` additions
- [ ] Document in `agent-bridge.md` → "Spawned-agent env hygiene" section
