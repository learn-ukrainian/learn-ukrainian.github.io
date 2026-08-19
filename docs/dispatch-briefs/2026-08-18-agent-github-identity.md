# Dispatch — agent GitHub identity + secretless default shell (A+J)

Advisor packet: Fable + Sol [AGREE] 2026-08-18. Operator: implement, keep fleet fluid.
Research classification: infra/harness; no matching registry records known → pointer-free (omit `--research-*`).

## Worktree instructions (mandatory)

Work in a git worktree under `.worktrees/dispatch/<agent>/<task>/` (auto-created by
`--worktree`). Do NOT branch in the primary checkout.

## Owned paths (disjoint — do not touch others)

- `scripts/agent_runtime/env_sanitize.py`
- `scripts/agent_runtime/agent_github_identity.py` (new)
- `scripts/delegate.py` (GH_TOKEN inject only: `_resolve_github_token`, `_inject_gh_token_for_agent`, `_GH_TOKEN_AGENTS`)
- `tests/test_agent_runtime_env_sanitize.py`
- `tests/test_env_sanitize.py`
- `tests/test_agent_github_identity.py` (new)
- `docs/runbooks/agent-github-identity.md` (new)

Do not edit `.github/workflows/**`, `CODEOWNERS`, or `agents_extensions/`.

## Outcome

Dispatch-spawned agents must not inherit the operator's GitHub authority or
ambient cloud/prod secrets. Ordinary `git push` and `gh pr create` must still
work without a new per-command ritual.

## Implementation contract

1. New `scripts/agent_runtime/agent_github_identity.py`:
   - Resolve in order: (a) GitHub App installation token from
     `LU_AGENT_GITHUB_APP_ID` + `LU_AGENT_GITHUB_APP_PRIVATE_KEY` +
     `LU_AGENT_GITHUB_APP_INSTALLATION_ID`; (b) `LU_AGENT_GITHUB_TOKEN`;
     (c) **legacy** operator `GH_TOKEN`/`GITHUB_TOKEN` / `~/.bash_secrets`
     only if neither (a) nor (b) is set.
   - Never print token values. Tests use fakes only.
   - App mint: JWT → `POST /app/installations/{id}/access_tokens`. Request
     repositories-scoped token. Do not request `workflows`, `admin`, or
     org-secret permissions.
   - Set `LU_AGENT_GITHUB_IDENTITY_SOURCE` to `app` | `token` | `legacy`.
   - If source is `legacy`, stderr one-line warning that operator identity is
     still in use and App setup is required. Do **not** fail dispatch (fluidity).
2. `build_agent_env`:
   - Stop treating parent `GH_TOKEN` as a provider secret to copy for
     claude/codex/bridge. Inject only the resolved **agent** identity.
   - After sanitizing, apply identity: `GH_TOKEN=<resolved>` when present;
     never pass `GITHUB_TOKEN` (gh reads `GH_TOKEN`).
   - Tighten git isolation: the copied `GIT_CONFIG_GLOBAL` must **not** keep
     `credential.helper=osxkeychain` as a path to the operator keychain for
     github.com. Prefer `http.https://github.com/.extraheader` /
     `GIT_ASKPASS` using the injected token. Do not brick `user.name`/`user.email`.
   - Continue stripping AWS/cloud/prod-looking names (already true). Do not
     strip lane model keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, etc.).
   - Do not unset `HOME` in a way that breaks the CLI. Isolating GitHub
     credentials is the goal, not a fake `$HOME`.
3. `delegate.py`: `_inject_gh_token_for_agent` must use
   `agent_github_identity`, not `_read_github_token_from_bash_secrets` as the
   primary path. Apply identity to **all dispatch agents that push** (not only
   `{codex, claude, bridge}`) so kimi/agy/grok/cursor/deepseek cannot fall back
   to operator `gh auth` via keychain. Keep the function small.
4. Runbook: one-time GitHub App setup (contents + pull-requests on this repo,
   no workflows/admin). Env var names. How to confirm `LU_AGENT_GITHUB_IDENTITY_SOURCE=app`.
   State that legacy fallback is temporary.

## Tests (must exist and pass)

- Parent `GH_TOKEN`/`GITHUB_TOKEN` are **not** copied when
  `LU_AGENT_GITHUB_TOKEN` is set; injected value is the agent token.
- App-mint path is unit-tested with HTTP mocked (no live GitHub).
- Legacy fallback still injects operator token and sets source=`legacy`.
- `CUSTOM_TOKEN`, AWS keys, etc. still stripped (existing tests).
- Update `test_build_agent_env_passes_only_current_provider_credentials` which
  currently asserts claude/codex/bridge inherit parent `GH_TOKEN`.

## Verify

```bash
.venv/bin/python -m pytest tests/test_agent_runtime_env_sanitize.py tests/test_env_sanitize.py tests/test_agent_github_identity.py -q
.venv/bin/python -m ruff check scripts/agent_runtime/env_sanitize.py scripts/agent_runtime/agent_github_identity.py scripts/delegate.py
```

Quote raw pytest/ruff output. Do not weaken tests.

## Git

1. Confirm you are in the dispatch worktree.
2. Implement + tests.
3. Commit conventional: `feat(harness): scoped agent GitHub identity at dispatch`
   with trailer `X-Agent: codex/agent-gh-identity-aj`
4. `git push -u origin HEAD` and `gh pr create`. **NO merge. NO auto-merge.**

PR title: `feat(harness): scoped agent GitHub identity at dispatch`
PR body: advisor packet A+J; App-first, dedicated token, legacy fallback with warning; secretless default except lane model keys.

## Stop / non-goals

- Do not create the GitHub App (operator one-time).
- Do not add per-command `git`/`gh` approval.
- Do not edit workflows or CODEOWNERS.
- Do not fail dispatch when App is unset (legacy warning only).
