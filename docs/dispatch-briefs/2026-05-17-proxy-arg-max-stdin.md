# Dispatch: fix ARG_MAX/E2BIG by passing prompt via stdin (#2027)

## Why this matters

`scripts/ai_agent_bridge/openai_proxy.py` passes the full flattened
prompt as an argv flag (`--prompt=...`, `--oneshot=...`) to the
underlying CLI for all three backends (`_gemini_backend`,
`_claude_backend`, `_hermes_backend`). On macOS argv is bounded at
~256 KB; Linux varies 128 KB–2 MB. Real OpenAI clients send 100K+
token prompts that EASILY exceed this. Result: subprocess crashes at
spawn with `OSError [Errno 7] Argument list too long`, which the proxy
surfaces as HTTP 502.

This is a HIGH-severity proxy bug surfaced by Gemini's adversarial
review of PR #2025 (audit/2026-05-16-openai-proxy-gemini-review/REPORT.md).

## Files

- `scripts/ai_agent_bridge/openai_proxy.py` lines ~150-230 (the three
  `_*_backend` functions). Confirm exact line numbers — file may have
  shifted since the audit.
- `tests/ai_agent_bridge/test_openai_proxy.py` (or wherever the proxy
  tests live; `find tests -name 'test_*openai*proxy*'`).

## What to do (verifiable steps)

1. **Worktree setup.** You were spawned with `--worktree`; verify
   `git rev-parse --show-toplevel` + `git branch --show-current` and
   cite raw output.

2. **Reproduce the failure.** From the worktree:
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian
   # start the proxy if not already up
   PROMPT=$(python3 -c "print('x' * 300000)")
   curl -sX POST http://127.0.0.1:8767/v1/chat/completions \
     -H 'content-type: application/json' \
     -d "{\"model\":\"gemini-3.1-pro-preview\",\"messages\":[{\"role\":\"user\",\"content\":\"$PROMPT\"}]}" | head -c 500
   cd -  # back to worktree
   ```
   Quote the raw 502 response (or whatever error you get).

3. **Refactor.** For each of the 3 backends, change the prompt-passing
   pattern from `--flag=PROMPT` to **stdin**:
   - Pass an empty/short positional prompt, or use the CLI's
     `--stdin` mode (check each tool's `--help`).
   - Feed `prompt` via `subprocess.run(input=prompt, ...)`.

   Each CLI's stdin mode differs — check `gemini --help`, `claude --help`,
   `hermes --help`. The right flag is usually `--stdin`, `-`, or
   bare omission of the prompt flag.

4. **Add a regression test.** New `tests/ai_agent_bridge/test_openai_proxy_arg_max.py`
   with one parametrized test per backend that:
   - Constructs a 300KB prompt.
   - Mocks the subprocess call to capture argv + stdin payload.
   - Asserts `prompt not in any argv element` (no argv leak).
   - Asserts `prompt == captured stdin`.

5. **Verify.** Run the failing curl reproduction again — should now
   return a real completion (or rate-limit error from the underlying
   API, NOT a 502 spawn-failure). Quote the raw output.

6. **Commit + push + PR.**
   ```
   fix(bridge/proxy): pass prompt via stdin to avoid ARG_MAX (#2027)
   ```
   PR body includes per-backend before/after argv snippet + the curl
   reproduction outputs (before: 502, after: real reply). Closes #2027.

## Verifiable claims required in the PR body

Per `docs/best-practices/deterministic-over-hallucination.md`:

| Claim | Evidence |
|---|---|
| "Reproduced ARG_MAX failure pre-fix" | raw curl + 502 response |
| "Three backends refactored to stdin" | per-backend diff snippet (3 entries) |
| "Reproduction succeeds post-fix" | raw curl + non-502 response |
| "Regression test pinned" | raw pytest output: `N passed in M.MMs` for the new test |

## Out of scope

- DO NOT touch the other 3 issues bundled in the original
  proxy-bundle dispatch (#2028 422 envelope, #2029 /healthz DoS,
  #2030 --host non-localhost). They will be separate PRs. Each issue
  one PR keeps review small and rollback granular.
- DO NOT change the proxy's auth, routing, or model-mapping logic.

## Acceptance

- PR opens; body includes the raw evidence lines above
- `Test (pytest)` CI required check passes
- Regression test added
- Closes #2027

## Pointers

- Issue: `gh issue view 2027`
- Original bundle (hung): `proxy-bundle-2026-05-17` (silence_timeout
  with response_chars=0; per #2071 likely environmental — re-fire one
  scope at a time)
- Trailer: every commit gets `X-Agent: codex/2027-proxy-stdin-fix`
