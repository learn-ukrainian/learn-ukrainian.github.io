# Dispatch brief — Issue #2022: reconcile Gemini 3.0 OpenAI proxy route with available CLI models

**Agent:** Gemini 3.1 pro preview
**Mode:** danger (commits + PR open; NO auto-merge)
**Worktree:** required
**Issue:** #2022 — `gemini-3.0-flash-preview` exposed by proxy but rejected by local Gemini CLI
**Severity:** LOW (smoke-fail in OpenAI proxy route; broken model alias)

---

## Why

The OpenAI-compatible proxy in `scripts/ai_agent_bridge/openai_proxy/`
advertises `gemini-3.0-flash-preview` as a model alias, but the
underlying Gemini CLI rejects it with `ModelNotFoundError`. Same
proxy + backend WORKS with `gemini-3.1-pro-preview`. Either the alias
should map to a valid CLI model OR the alias should be removed from
the advertised list (so the OpenAI API surface only exposes models the
CLI actually accepts).

User-visible failure: any client calling `/v1/chat/completions` with
`model="gemini-3.0-flash-preview"` gets a 5xx. Misleading.

## What you build

### 1. Inspect the proxy's Gemini backend model handling

Locate where the model alias is registered (search for
`gemini-3.0-flash-preview` in `scripts/ai_agent_bridge/openai_proxy/`).
Three likely places:
- A `MODEL_ALIASES` dict mapping OpenAI-style names → CLI-style names.
- A `register_models()` call.
- A hardcoded list in the `/v1/models` endpoint.

Quote what you find.

### 2. Decide: REMAP or REMOVE

Run `gemini --help` and `gemini --list-models` (or whatever the CLI
surfaces) to enumerate the CLI's actually-available models. If a
modern Gemini Flash-class model exists in the CLI, REMAP the alias to
that name. If no Flash-class model is available, REMOVE the alias
from the proxy.

State your decision + evidence in the PR body.

### 3. Update the proxy

Either:
- **REMAP**: change the alias mapping so `gemini-3.0-flash-preview`
  routes to the CLI's actually-accepted name (e.g. `gemini-2.0-flash`,
  whatever the CLI takes).
- **REMOVE**: drop the alias from the registered models list and from
  the `/v1/models` enumeration. Add a comment explaining the removal
  references issue #2022.

### 4. Tests

Add or update tests in `tests/ai_agent_bridge/` (locate existing
openai_proxy tests). Required:

1. **Alias resolution**: `/v1/chat/completions` with the alias →
   handler hits the CLI with the expected resolved model name (mock
   the CLI invocation, assert the arg passed). If REMOVE, instead
   assert the alias returns a 404/400 with a clear "unknown model"
   error.
2. **Model list**: `/v1/models` reflects the new state (alias listed
   if remapped, absent if removed).
3. **Smoke**: live invocation must NOT regress for
   `gemini-3.1-pro-preview` (assert it still works after the change).

### 5. Document the alias map

In the proxy README/docstring or wherever the alias table is, document
the mapping table after the change so future maintainers don't
re-introduce a stale alias.

---

## Verifiable claims (per #M-4)

| Claim | Tool + raw output |
|---|---|
| Located the alias registration | `git diff origin/main -- scripts/ai_agent_bridge/openai_proxy/` raw |
| Decision (REMAP vs REMOVE) supported by CLI evidence | `gemini --help` or model-list command raw output |
| New/updated tests pass | `.venv/bin/pytest tests/ai_agent_bridge/ -v` final summary raw |
| Ruff clean | `.venv/bin/ruff check scripts/ai_agent_bridge/openai_proxy/ tests/ai_agent_bridge/` raw |
| Pre-commit clean | `pre_commit run --files <changed>` raw |
| Commit + PR | `git log -1 --oneline` + `gh pr view --json url` raw |
| Smoke validation (live) | If `ab serve --openai` works in the worktree, run the curl from the issue body and quote raw output proving the alias now works (REMAP) or fails cleanly (REMOVE). Skip with a note if `ab serve` requires extra setup beyond the worktree. |

**No claim allowed without its raw output line.** Per #M-4.

## Worktree setup

`delegate.py dispatch --worktree` handles it. Branch:
`fix/2022-gemini-3-proxy-mapping`.

## Verification

```bash
# venv symlinked from main; run from worktree root
.venv/bin/pytest tests/ai_agent_bridge/ -v
.venv/bin/ruff check scripts/ai_agent_bridge/openai_proxy/ tests/ai_agent_bridge/
.venv/bin/python -m pre_commit run --files <changed files>
git diff --stat origin/main
```

## Commit + PR

Conventional commit. No `--auto-merge`. Title: `fix(bridge/proxy):
reconcile Gemini 3.0 alias with available CLI models (#2022)`.

## Out of scope

- Don't change the Claude or Codex backends — separate routes.
- Don't add new model aliases beyond fixing the broken one (don't
  scope-creep into "add all current Gemini models").
- Don't update the dispatcher's separate model routing (delegate.py).
  This is proxy-only.

## Anti-fabrication

If the alias is NOT actually registered anywhere in the proxy code
(maybe it was advertised dynamically via the CLI's own model list),
STOP and quote what you found. The fix shape changes if the source of
the alias is upstream (then the proxy needs a filter, not a remap).
