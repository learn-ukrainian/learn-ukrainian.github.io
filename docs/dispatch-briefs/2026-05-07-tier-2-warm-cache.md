# Codex dispatch brief — Tier 2 warm-cache fix for `ab discuss` (closes #1782 sub-task 1)

> **Issue:** #1782 (umbrella for persistent-listener architecture)
> **Mode:** danger (full sandbox bypass for tests + commits)
> **Worktree:** `.worktrees/dispatch/codex/tier-2-warm-cache/`
> **Hard timeout:** 1800s (30 min)
> **Silence timeout:** 600s (10 min — short-loop work, not bakeoff)
> **Effort:** medium

---

## ⚠️ CRITICAL — fresh-shell behavior

**Each bash block runs in a FRESH SHELL. CWD does NOT persist across blocks.** Every command that uses `.venv/`, `scripts/`, or files in MAIN checkout MUST be prefixed with `cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/tier-2-warm-cache && ...` (or absolute path). The bakeoff brief was bitten by this earlier today; do not repeat the trap.

Inside the worktree, `.venv/` exists ONLY because git worktrees do not copy gitignored dirs. Use the MAIN checkout's `.venv` via absolute path: `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python`.

---

## Goal

Make `ab discuss` use Anthropic prompt cache across rounds for Claude + Gemini, while leaving Codex on cold-start (its registry policy is `resume_policy="never"`).

Today's behavior (`scripts/ai_agent_bridge/_channels_cli.py:1144-1155`): every round spawns fresh subprocesses with no `session_id`, paying full prompt-cache creation cost each call. The asymmetry: `ab ask-claude` (`_claude.py:117-123`) DOES pass `session_id` and warm-resumes via `--resume`. `ab discuss` does not.

After this fix: round 1 creates a named session per Claude/Gemini agent; round 2+ reuses via `--resume`. Codex stays fresh per registry policy.

---

## Constraints discovered (do not violate)

`scripts/agent_runtime/runner.py:288-324` enforces resume policy. Reproducing the docstring:

```
Codex is always fresh-session.
Claude/Gemini bridge paths may keep resume (cache economics).
delegate/dispatch never use resume (worktree is the isolation boundary).
```

Today's `ab discuss` calls `runtime_invoke(...)` with `entrypoint="delegate"`. Naive "thread session_id through" would CRASH with `ValueError: Agent 'claude' has resume_policy='bridge_only' but session_id was passed from entrypoint='delegate'`. So:

1. **Switch entrypoint** of `ab discuss` from `"delegate"` to `"bridge"` (line 1153).
2. **Per-agent gate** session_id only for agents whose `resume_policy in {"bridge_only"}`. Look up via `agent_runtime.registry.get_agent_entry(agent_name)`. The registry says Claude=`bridge_only`, Gemini=`bridge_only`, Codex=`never`. Other agents (gemma_local, openai-fallback, etc.) — gate by policy lookup, not hardcoded list.

---

## Numbered steps

1. **Verify worktree starts on main + #1781 merged.** From inside the worktree:
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/tier-2-warm-cache && git log --oneline -3
   ```
   Top commit must be `6014cbab74 fix(prompts): add hard stop rule after writer artifacts (#1781)` or descendant.

2. **Read the rounds loop and `_invoke_one`** to understand the flow:
   - `scripts/ai_agent_bridge/_channels_cli.py:1133-1175` — `_invoke_one` (called per agent per round)
   - `scripts/ai_agent_bridge/_channels_cli.py:1177-1410` — main rounds loop
   - `scripts/ai_agent_bridge/_claude.py:117-123` — reference pattern for session_id usage
   - `scripts/agent_runtime/runner.py:288-324` — the policy enforcement
   - `scripts/agent_runtime/registry.py:34-93` — resume_policy values per agent
   - `scripts/agent_runtime/adapters/claude.py:222-237` — how the adapter consumes `is_new_session` tool_config + session_id

3. **Implement the change** in `scripts/ai_agent_bridge/_channels_cli.py`:

   a. Above the rounds loop (around line 1175, before `for round_idx in range(...)`), initialize a per-agent session_id store. Pseudocode:
   ```python
   from agent_runtime.registry import get_agent_entry  # at top with other imports

   discussion_session_ids: dict[str, str] = {}  # agent_name → session_id (only for resumable agents)
   ```

   b. In `_invoke_one` (line 1133), accept session_id state and look up policy. Pseudocode:
   ```python
   def _invoke_one(
       agent_name: str, prompt_text: str, round_idx: int
   ) -> tuple[str, str, bool]:
       # Resolve resume policy
       try:
           policy = get_agent_entry(agent_name).get("resume_policy", "never")
       except KeyError:
           policy = "never"  # safe default for unknown agents

       session_id_to_pass: str | None = None
       is_new_session = False
       if policy == "bridge_only":
           if agent_name not in discussion_session_ids:
               import uuid
               discussion_session_ids[agent_name] = str(uuid.uuid4())
               is_new_session = True
           session_id_to_pass = discussion_session_ids[agent_name]

       # Merge with existing read-only tool config
       tool_config = dict(_DISCUSSION_READONLY_TOOL_CONFIG)
       if is_new_session:
           tool_config["is_new_session"] = True

       try:
           result = runtime_invoke(
               agent_name,
               prompt_text,
               mode="read-only",
               cwd=REPO_ROOT,
               task_id=f"discuss-{correlation_id[:8]}-r{round_idx}-{agent_name}",
               tool_config=tool_config,
               entrypoint="bridge",          # ← was "delegate"
               session_id=session_id_to_pass, # ← was absent
               hard_timeout=900,
           )
       except RateLimitedError as exc:
           ...  # existing handling unchanged
   ```

   c. Closure capture: `_invoke_one` is a nested function — `discussion_session_ids` MUST be captured by closure from the outer scope. Confirm it's defined before `_invoke_one`'s definition is referenced (or declare `nonlocal` if Python complains).

   d. **DO NOT** mutate `_DISCUSSION_READONLY_TOOL_CONFIG` in place — copy it (`dict(_DISCUSSION_READONLY_TOOL_CONFIG)`) before adding `is_new_session`. The original is module-scoped.

4. **Add a unit test** at `tests/test_channels_discuss_resume.py`:

   ```python
   """Tier 2 warm-cache fix for ab discuss — closes #1782 sub-task 1."""
   from unittest.mock import patch, MagicMock
   import pytest


   def test_discuss_passes_session_id_for_resumable_agents(monkeypatch):
       """Claude + Gemini get a session_id; Codex does not (registry policy)."""
       from ai_agent_bridge import _channels_cli

       captured_invokes = []

       def fake_runtime_invoke(agent, prompt, **kwargs):
           captured_invokes.append((agent, kwargs))
           res = MagicMock()
           res.ok = True
           res.response = f"[reply from {agent}]"
           return res

       monkeypatch.setattr(_channels_cli, "runtime_invoke", fake_runtime_invoke)
       # ... drive _invoke_one (or run a 2-round discussion in a fixture)
       # Assertions:
       # - claude/gemini calls have session_id != None
       # - codex calls have session_id == None
       # - round 1 has tool_config["is_new_session"] == True for resumable agents
       # - round 2 has same session_id as round 1 + no is_new_session flag
       # - All calls have entrypoint="bridge" (was "delegate")


   def test_discuss_entrypoint_is_bridge_not_delegate(monkeypatch):
       """The entrypoint switch is the load-bearing change for the resume policy gate."""
       # ... assert entrypoint="bridge" appears in every runtime_invoke call
       pass


   def test_discuss_unknown_agent_defaults_to_no_resume(monkeypatch):
       """Agents not in registry get resume_policy='never' equivalent — no session_id."""
       # ... assert _invoke_one('mystery-agent', ...) does not crash; session_id is None
       pass
   ```

   Fill in the fixture/driver so the assertions actually run. The test must FAIL on current main (no session_id passed) and PASS after the fix. If the existing test infrastructure makes it hard to drive `_invoke_one` directly, mock at the `runtime_invoke` boundary inside an actual `discuss` CLI invocation via `subprocess` against a test channel.

5. **Run tests:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/tier-2-warm-cache && /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/pytest tests/test_channels_discuss_resume.py -v
   ```
   All 3 tests must pass.

6. **Run ruff on the changed files:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/tier-2-warm-cache && /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/ruff check scripts/ai_agent_bridge/_channels_cli.py tests/test_channels_discuss_resume.py
   ```
   Must exit 0.

7. **Commit:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/tier-2-warm-cache && git add scripts/ai_agent_bridge/_channels_cli.py tests/test_channels_discuss_resume.py
   git commit -m "$(cat <<'EOF'
   feat(ab-discuss): tier-2 warm-cache via bridge entrypoint + per-agent session_id (#1782)

   Switch ab discuss from entrypoint="delegate" to "bridge" and pass a
   per-(agent, discussion) session_id when the agent's resume_policy
   permits it (Claude, Gemini per registry). Codex stays fresh-session
   per its resume_policy="never" — registry-driven, not hardcoded.

   Round 1 generates a fresh UUID per resumable agent and passes
   tool_config["is_new_session"]=True so the adapter uses --session-id.
   Round 2+ reuses the same UUID without is_new_session, so the adapter
   uses --resume and hits the warm Anthropic prompt cache.

   This fixes the per-round full-prompt-cache-creation cost for 2 of 3
   discuss participants and is expected to fix the round-2 root-truncation
   bug as a side effect (warm cache implies the root is by definition
   still in scope).

   Sub-task 1 of #1782 (persistent agent listeners umbrella). Tier 3
   (full daemon listeners) deferred per pending Multi-UI ADR ACCEPTANCE.

   Co-Authored-By: Codex (gpt-5.5) via delegate.py dispatch
   EOF
   )"
   ```

8. **Push + open PR:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/tier-2-warm-cache && git push -u origin codex/tier-2-warm-cache
   /Users/krisztiankoos/.bash_secrets exists in main checkout — ensure GH_TOKEN is sourced before gh calls or rely on the dispatch's existing auth setup. If gh fails with 401, report don't fix.
   gh pr create --title "feat(ab-discuss): tier-2 warm-cache via bridge entrypoint + per-agent session_id (#1782)" --body "$(cat <<'EOF'
   ## Summary

   - Switch \`ab discuss\` from \`entrypoint="delegate"\` to \`"bridge"\` in \`_channels_cli.py:1153\`
   - Add per-(agent, correlation_id) \`session_id\` store; round 1 generates fresh UUID with \`is_new_session=True\`, round 2+ reuses for \`--resume\`
   - Gate session_id on \`agent_runtime.registry.get_agent_entry(agent).resume_policy == "bridge_only"\` — Claude/Gemini opt-in, Codex stays fresh
   - Add \`tests/test_channels_discuss_resume.py\` with 3 regression tests

   ## Why

   \`ab discuss\` was paying full Anthropic prompt-cache creation cost on every round for every participant. \`ab ask-claude\` already uses session_id (\`_claude.py:117-123\`) but \`ab discuss\` did not. Asymmetric. Codex's resume_policy enforcement (\`runner.py:288-324\`) requires the entrypoint switch to satisfy the bridge-only constraint.

   Closes sub-task 1 of #1782. Tier 3 (daemon listeners) deferred until pending Multi-UI ADR ACCEPTED.

   ## Test plan

   - [x] \`pytest tests/test_channels_discuss_resume.py -v\` — 3 tests pass
   - [x] \`ruff check\` clean
   - [ ] Manual smoke (post-merge): \`ab discuss architecture "test brief" --with claude,gemini,codex --max-rounds 2\` → check Anthropic API logs for cache hit on round-2 Claude call
   - [ ] Round-2 root-truncation bug expected to be fixed as side effect (warm cache → root preserved)

   🤖 Generated with [Codex via delegate.py dispatch]
   EOF
   )"
   ```

---

## Reporting (concise)

- File-by-file LOC summary
- Test pass/fail count
- Ruff exit
- PR URL
- Any policy enforcement crashes encountered (`ValueError` from `runner._enforce_resume_policy`) and how resolved

## Constraints

- Do NOT modify `runner.py:288-324` policy logic — adapt to it, don't change it
- Do NOT modify the registry `resume_policy` values — they're load-bearing
- Do NOT auto-merge the PR — leave open for review per project policy
- Do NOT add session_id for Codex (its policy is `never`; would crash)
- If `_invoke_one` closure pattern doesn't work, refactor minimally (e.g. add a `session_ids` parameter) — don't restructure the whole function
