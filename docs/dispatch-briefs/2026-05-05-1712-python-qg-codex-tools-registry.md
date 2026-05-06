# Codex dispatch brief — #1712 python_qg registry-name mismatch

> **Issue:** #1712 (already filed)
> **Branch base:** `origin/main`
> **Worktree:** `.worktrees/dispatch/codex/1712-python-qg-codex-tools-registry/`
> **Branch name:** `codex/1712-python-qg-codex-tools-registry`
> **Mode:** danger
> **Hard timeout:** 1800s (30 min — small targeted fix + tests)
> **Effort:** medium

## Goal

Fix the agent-name mismatch where `linear_pipeline.py:2367` calls `runtime_invoke("codex-tools", ...)` but the agent_runtime registry only has bare names (`claude`/`codex`/`gemini`/`gemma-local`/`grok`). This currently breaks `v7_build.py` end-to-end runs at the python_qg correction phase. Discovered via #1711's smoke test.

## What to change

### 1. Fix the immediate call site

`scripts/build/linear_pipeline.py:2360-2374` — change `runtime_invoke("codex-tools", ...)` to `runtime_invoke("codex", ...)`. The `tool_config` parameter is how the runtime distinguishes "with tools" from "without tools" — verify the existing `tool_config={"output_format": "text"}` is sufficient or if you need to add a `"tools_enabled": True` (or whatever the project uses).

### 2. Audit ALL `runtime_invoke` / `agent_runtime.runner.invoke` call sites

Grep:

```bash
grep -rn 'runtime_invoke\|agent_runtime\.runner\.invoke\|from scripts\.agent_runtime\.runner import invoke' scripts/
```

For each call site, cross-check the first positional arg (agent name) against the registered names in `scripts/agent_runtime/registry.py`. Fix any other mismatches the same way.

### 3. Defensive check at the registry boundary

In `scripts/agent_runtime/runner.py` (the `invoke` function), add input validation: if the caller passes an agent name with a `-tools` suffix that's not in the registry, raise a clear error message that says "agent_runtime registry uses bare names — pass 'codex' not 'codex-tools'; use tool_config to indicate tools-enabled". This prevents the failure mode from recurring silently.

### 4. Test

Unit test in `tests/test_agent_runtime.py` (or new file): parametrize call with `runtime_invoke("codex-tools", ...)` and assert it raises a clear ValueError mentioning the bare-name convention. Negative test, prevents regression.

Smoke test (locally, not in CI):

```bash
.venv/bin/python scripts/build/v7_build.py a1 my-morning --writer gemini-tools --out /tmp/v7-smoke-1712 --telemetry-out /tmp/v7-smoke-1712.jsonl
```

Should now complete past the python_qg phase. (Yes this calls Gemini for real — gemini-cli is now fixed via #1711, so it should work in <5 min wall.)

## Numbered execution steps

1. Verify worktree base clean (`git log --oneline HEAD..origin/main` empty).
2. Fix `linear_pipeline.py:2367` per Section 1.
3. Audit other call sites per Section 2. Document findings in PR body.
4. Add registry-boundary validation per Section 3.
5. Write tests per Section 4.
6. Local smoke per Section 4 (real Gemini call). Verify python_qg phase completes without `Available: [...]` error.
7. `.venv/bin/ruff check scripts/build/ scripts/agent_runtime/ tests/`
8. `.venv/bin/pytest tests/test_agent_runtime.py tests/test_linear_pipeline_telemetry.py -v`
9. **Cross-family review from Claude:**
   ```bash
   git add -A
   git diff --cached > /tmp/issue-1712-diff.txt
   .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-claude \
       "Adversarial review for #1712. Read /tmp/issue-1712-diff.txt. Focus: (1) is the linear_pipeline.py:2367 fix correct, or does it need additional tool_config keys to preserve tools-enabled semantics? (2) does the audit catch all sibling call sites? (3) is the registry-boundary validation tight enough to catch future mistakes without false-rejecting legitimate calls?" \
       --task-id issue-1712-review
   ```
10. Apply feedback or argue back in writing.
11. Commit with `Reviewed-By: claude-opus-4-7 (issue-1712-review)` trailer.
12. Push and open PR. Body MUST include: list of audited call sites + verdict, smoke test wall time + last event emitted, test additions.

## Constraints

- Don't rename writer-choice strings (`-tools` suffix is public API)
- Don't modify v6_build.py (legacy)
- Single PR; don't split per call-site
- No auto-merge

## Out of scope

- Refactoring agent_runtime registry to accept aliases (could be follow-up if multiple call sites are affected and you want a cleaner API)
- v7_build.py CLI surface changes
- Any change to v7_review.py beyond what the audit reveals
