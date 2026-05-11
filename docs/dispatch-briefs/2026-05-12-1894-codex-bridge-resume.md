# Codex dispatch brief — Codex bridge warm-cache (mirror Gemini #1887)

> **Issue:** #1894
> **Mode:** danger (full sandbox bypass for tests + commits)
> **Worktree:** `.worktrees/dispatch/codex/1894-codex-bridge-resume/`
> **Base:** `origin/main` (currently `0e97806d7`)
> **Hard timeout:** 1800s (30 min)
> **Silence timeout:** 600s (10 min)
> **Effort:** high

---

## ⚠️ CRITICAL — fresh-shell behavior

**Each bash block runs in a FRESH SHELL. CWD does NOT persist across blocks.** Every command that uses `.venv/`, `scripts/`, or files in MAIN checkout MUST be prefixed with `cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/1894-codex-bridge-resume && ...` (or absolute path).

Inside the worktree, `.venv/` exists ONLY because git worktrees do not copy gitignored dirs. Use the MAIN checkout's `.venv` via absolute path: `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python`.

---

## Goal

Enable Anthropic-style prompt-cache reuse across `ab discuss` rounds for Codex, mirroring the Gemini fix shipped in PR #1889 (#1887). Today Codex's registry policy is `resume_policy="never"` and the adapter defensively drops `session_id` (codex.py:162-165). Every round spawns a fresh `codex exec`, paying full cold-start each call.

After this fix:
- `CodexAdapter`'s registry entry uses `resume_policy="bridge_only"`.
- Bridge invocations: first round creates a fresh session; round 2+ uses `codex exec resume <SESSION_ID>` to warm-resume.
- Dispatch invocations: `runner.py:288-324` policy enforcement at the runtime layer already drops `session_id` for non-bridge entrypoints — worktree isolation stays intact, no adapter change needed for dispatch path.
- `codex-desktop` registry entry stays `resume_policy="never"` (cli_available=False, no actual CLI usage to optimize).

---

## ⚠️ KEY DIFFERENCE FROM GEMINI #1887 — CLI SHAPE IS A SUBCOMMAND, NOT A FLAG

Gemini's resume was a top-level flag injection (`--resume <uuid>` or `--session-id <uuid>`). **Codex's resume is a SUBCOMMAND of `codex exec`:**

```
# First call (no session known yet):
codex exec [OPTIONS] -          # session UUID auto-generated, parsed from stdout

# Resume call (session known from prior round):
codex exec resume [OPTIONS] <SESSION_ID> [PROMPT]
```

Verify yourself in the worktree:

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/1894-codex-bridge-resume && codex exec --help | head -10 && echo --- && codex exec resume --help | head -20
```

Quote the raw output of both `--help` calls in your final response so we have deterministic evidence the CLI shape didn't drift between dispatch time and write time.

Codex CLI also has no `--session-id <uuid>` "create with this UUID" form (unlike Gemini/Claude). Codex generates its own UUID on first invocation and prints `session id: <uuid>` as the **5th header line of normal `codex exec` stdout** — `codex.py:_SESSION_RE` (line 45) already parses it, and `parse_response` already surfaces it as `ParseResult.session_id` (lines 369-372, 412). So the first-round capture pipeline is COMPLETE today; the bridge just doesn't use it yet. `is_new_session` semantics from Gemini don't translate directly: for Codex, first-call is simply "the call without a `resume` subcommand," and the bridge stores whatever UUID comes back in `ParseResult.session_id` to feed into round 2.

**Quick sanity check before coding** — run a real `codex exec` to confirm the UUID still lands at line 5 of stdout (CLI version 0.130.0 was the last tested version). Quote the first 6 lines of stdout in your response.

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/1894-codex-bridge-resume && echo "say hi" | codex exec --color never -s read-only -m gpt-5.5 -o /tmp/codex-1894-probe.txt - 2>&1 | head -6
```

---

## Numbered steps

1. **Verify worktree base.** From inside the worktree:
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/1894-codex-bridge-resume && git log --oneline -3
   ```
   Top commit must be `0e97806d7` (or descendant) and the branch must be `codex/1894-codex-bridge-resume`.

2. **Read these files first (do not skip):**
   - `scripts/agent_runtime/adapters/codex.py:1-30` — class-level design rationale (cross-worktree contamination footgun). Bridge case must preserve dispatch's `never` semantics.
   - `scripts/agent_runtime/adapters/codex.py:140-225` — current `build_invocation_plan` (you will modify this).
   - `scripts/agent_runtime/adapters/gemini.py:175-260` — Gemini's bridge_only pattern (your reference).
   - `scripts/agent_runtime/adapters/claude.py:153-237` — Claude's reference pattern (mentioned in Gemini docstring).
   - `scripts/agent_runtime/registry.py:37-50` — change `"codex"` entry `"resume_policy": "never"` → `"bridge_only"`. **Leave `"codex-desktop"` (line 62) untouched** — cli_available=False, no CLI usage to optimize.
   - `scripts/agent_runtime/runner.py:288-324` — policy enforcement for non-bridge entrypoints. Confirm this drops `session_id` for `entrypoint="delegate"` even after the policy change, so dispatch worktree isolation is preserved.
   - `tests/test_agent_runtime.py` — locate Gemini's bridge_only tests (commit `a5d68ffacc` added them); mirror their shape for Codex.
   - `tests/test_channels_discuss_resume.py` — the end-to-end smoke test (Gemini coverage added in `a5d68ffacc`). Add Codex coverage.

3. **Registry change (1 line)** in `scripts/agent_runtime/registry.py`:
   ```python
   # line 49
   "resume_policy": "bridge_only",   # was "never"
   ```

4. **Adapter change** in `scripts/agent_runtime/adapters/codex.py`:

   a. **Update the class docstring** (lines 8-13) — replace the "Fresh session always" rationale with the new semantics: dispatch path still fresh-session (worktree isolation), bridge path may warm-resume. Reference issue #1894.

   b. **Update `build_invocation` (around lines 140-225)** — stop dropping `session_id`. Conditional command shape:

   ```python
   has_session_to_resume = session_id is not None

   cmd: list[str] = [codex_bin, "exec"]
   if has_session_to_resume:
       cmd.append("resume")    # SUBCOMMAND — must come immediately after "exec"
   cmd.extend(self._tool_config_flags(tool_config))
   # ... rest of flags (-c, --skip-git-repo-check, -C, --color, -o, -m, mode flags)
   if has_session_to_resume:
       cmd.append(session_id)   # POSITIONAL — must come after all options
   cmd.append("-")  # Read prompt from stdin (works for both subcommands — `codex exec resume` also accepts `-` as PROMPT positional)
   ```

   **Verify** that `codex exec resume [OPTIONS] [SESSION_ID] [PROMPT]` accepts `-` as prompt (stdin) just like `codex exec` does. The `resume --help` output shows `[PROMPT]` arg with `If '-' is used, read from stdin`. Confirm by quoting that help line in your response.

   c. **Remove the defensive `_ = session_id` line** (line 165 in current file) and its comment — that comment will no longer be true.

   d. **Keep parse_response unchanged.** `_SESSION_RE` already extracts the UUID from stdout; that's the only thing the bridge needs.

5. **Tests** — add to `tests/test_agent_runtime.py`:

   - `test_codex_adapter_bridge_creates_then_resumes`: first call with `session_id=None` → cmd is `["codex", "exec", ..., "-"]`; second call with `session_id="<uuid>"` → cmd is `["codex", "exec", "resume", ..., "<uuid>", "-"]`.
   - `test_codex_adapter_dispatch_ignores_session_id_via_runner_policy`: invoke through `runner.py` with `entrypoint="delegate"` and `session_id="<uuid>"` — assert the policy layer drops session_id before reaching the adapter (or equivalent assertion against the existing 192-test suite shape; mirror whatever shape the Gemini test took).
   - Update `tests/test_channels_discuss_resume.py` to include Codex in the multi-agent round-2 session-reuse assertion (the existing test verifies Gemini + Claude UUIDs match across rounds; extend to Codex).

6. **Run the full agent-runtime suite** + relevant ones:
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/1894-codex-bridge-resume && /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python -m pytest tests/test_agent_runtime.py tests/test_channels_discuss_resume.py -v 2>&1 | tail -30
   ```
   Quote the raw final summary line in your response (e.g. `192 passed in 27.95s`). Bare "tests pass" is not acceptable per #M-4.

7. **Ruff:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/1894-codex-bridge-resume && /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/ruff check scripts/agent_runtime/adapters/codex.py scripts/agent_runtime/registry.py tests/test_agent_runtime.py tests/test_channels_discuss_resume.py 2>&1 | tail -10
   ```
   Quote raw output.

8. **Commit** with X-Agent trailer:
   ```
   fix(codex-adapter): honor bridge_only session resume — mirror gemini.py pattern (#1894)

   <2-3 line body — why this matters: bridge multi-round prompt-cache reuse; dispatch path preserved>

   Tests: <quote raw pytest summary line>

   X-Agent: codex/1894-codex-bridge-resume
   ```

9. **Push + PR.** Push the branch and `gh pr create`. Reference issue with `Closes #1894`. Use HEREDOC for body. Do NOT auto-merge.

---

## Pre-submit checklist (MANDATORY — verify EVERY item before pushing)

From `AGENTS.md:11-26`. PRs failing this checklist are rejected.

- [ ] `.python-version` unchanged (must be `3.12.8`)
- [ ] `.yamllint` and `.markdownlint.json` unchanged
- [ ] No `status/*.json`, `audit/*-review.md`, or `review/*-review.md` files in the diff (generated artifacts)
- [ ] No `sys.executable` anywhere in code — use `.venv/bin/python`
- [ ] No `@pytest.mark.skip` with empty `pass` bodies
- [ ] No assertions weakened (e.g. `is True` → `isinstance(..., bool)`)
- [ ] Every changed file directly related to #1894
- [ ] Total files changed < 20 (more = artifact pollution — only `registry.py`, `codex.py`, `test_agent_runtime.py`, `test_channels_discuss_resume.py` should be in the diff; possibly also adapter docstring updates if you touch any sibling adapter)
- [ ] Code runs without `NameError` / `KeyError` / `ImportError`
- [ ] X-Agent trailer present on every commit

---

## #M-4 deterministic-verification block (MANDATORY)

Per `memory/MEMORY.md` #M-4 and `docs/best-practices/deterministic-over-hallucination.md`. Every verifiable claim in your final response must include the raw tool output that backs it. The verifiable claims this work will produce:

| Claim | Tool | Output form |
|---|---|---|
| CLI shape of `codex exec` | `codex exec --help` | Quote first 10 lines |
| CLI shape of `codex exec resume` | `codex exec resume --help` | Quote first 20 lines |
| Registry change applied | `grep -n resume_policy scripts/agent_runtime/registry.py` | Quote line 49 |
| Adapter no longer drops session_id | `grep -n "_ = session_id" scripts/agent_runtime/adapters/codex.py` | Quote (must be empty) |
| Test pass count | `pytest tests/test_agent_runtime.py tests/test_channels_discuss_resume.py` | Quote final summary line raw |
| Ruff clean | `ruff check scripts/agent_runtime/adapters/codex.py scripts/agent_runtime/registry.py tests/test_agent_runtime.py tests/test_channels_discuss_resume.py` | Quote raw output (expect "All checks passed!" or zero errors) |
| Branch base | `git log --oneline -3` from worktree | Quote 3 lines |
| Final commit + X-Agent trailer | `git log -1 --format=full` | Quote raw |

"I verified X" without quoted tool output is treated as hallucination.

---

## Out of scope (do NOT touch)

- Anything outside `scripts/agent_runtime/{adapters/codex.py,registry.py}` and the two test files. No sibling-adapter refactor, no shared utility extraction.
- `codex-desktop` registry entry (`cli_available=False` — leave at `"never"`).
- Cross-directory session resume (`codex resume --all`) — bridge use case is in-repo only; rejected as out-of-scope in the issue body.
- Changing dispatch worktree-isolation semantics. Dispatch path stays fresh-session via `runner.py:288-324` policy enforcement.

---

## References (read these BEFORE coding)

- Issue: https://github.com/krisztiankoos/learn-ukrainian/issues/1894
- Prior art: PR #1889 (commit `a5d68ffacc`) — Gemini bridge_only resume
- Reference: `scripts/agent_runtime/adapters/claude.py:153-237`
- Registry: `scripts/agent_runtime/registry.py:34-93`
- Policy enforcement: `scripts/agent_runtime/runner.py:288-324`
- Current Codex adapter: `scripts/agent_runtime/adapters/codex.py` (especially L10-13 and L162-165)
