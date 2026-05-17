# Dispatch: --host non-localhost guard for openai proxy (#2030)

## Why this matters

`ab serve --openai --host 0.0.0.0` silently binds the unauthenticated
proxy to all interfaces. Phase 1 was explicitly localhost-only, no
auth. Anyone on the LAN can hit four agent CLIs through this proxy if
the user forgets the implication of `--host`.

Severity LOW per the audit (default is safe; only triggers with
explicit override), but it's a security ergonomics gap that's easy to
close.

## Files

- `scripts/ai_agent_bridge/_cli.py` — argparse for the `serve` /
  `serve --openai` subcommand. The `--host` flag and its handler.
- `tests/ai_agent_bridge/` — find the existing serve-command tests
  with `grep -rln "serve.*--host" tests/`.

## What to do (verifiable steps)

1. **Worktree setup.** Cite `git rev-parse --show-toplevel` +
   `git branch --show-current` raw output.

2. **Reproduce.** From the worktree:
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian
   .venv/bin/python scripts/ai_agent_bridge/__main__.py serve --openai --host 0.0.0.0 --help
   # observe: --host is accepted without warning
   cd -
   ```
   Quote the raw output.

3. **Add the guard.** Mirror the issue's recommended snippet. Add a
   `--allow-remote` boolean flag (default False) to the serve
   subparser. After argparse parses, before the proxy binds:
   ```python
   if args.host != "127.0.0.1" and not args.allow_remote:
       parser.error(
           "refusing to bind to non-localhost host without --allow-remote. "
           "the proxy has no auth and exposes 4 agent CLIs to anyone on the network."
       )
   ```
   Keep the message clear about WHY.

4. **Test.**
   - Add a test: `ab serve --openai --host 0.0.0.0` exits non-zero
     with the error message.
   - Add a test: `ab serve --openai --host 0.0.0.0 --allow-remote`
     does not exit (mock the bind step; just verify the guard passes).
   - Add a test: `ab serve --openai` (default 127.0.0.1) does not
     require the flag.

5. **Commit + push + PR.**
   ```
   fix(bridge/proxy): require --allow-remote for non-localhost bind (#2030)
   ```

## Verifiable claims required in the PR body

| Claim | Evidence |
|---|---|
| "Reproduced unsafe bind pre-fix" | raw `serve --host 0.0.0.0 --help` output |
| "Guard rejects unguarded non-localhost" | raw pytest output for the rejection test |
| "Guard allows localhost without flag" | raw pytest output for the localhost test |
| "Guard allows non-localhost with flag" | raw pytest output for the opt-in test |

## Out of scope

- Don't add proxy auth (out of scope, would be a separate Phase 2).
- Don't change the default host. Don't touch other serve flags.

## Acceptance

- PR opens; 3 new tests; raw evidence in body
- `Test (pytest)` CI required check passes
- Closes #2030

## Pointers

- Issue: `gh issue view 2030`
- Original bundle (hung): `proxy-bundle-2026-05-17` — #2027/#2028/#2029/#2030 are split.
- Trailer: every commit gets `X-Agent: gemini/2030-proxy-allow-remote`
