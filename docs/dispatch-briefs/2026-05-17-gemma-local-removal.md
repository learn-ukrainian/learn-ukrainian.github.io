# Dispatch brief — remove `gemma-local` agent lane

**Agent:** Gemini (mechanical removal across files — DEFAULT for routine pattern-applying work per MEMORY #M0)
**Mode:** danger (commits + PR open; NO auto-merge)
**Worktree:** required (per #1952, enforced by `delegate.py dispatch`)
**Scope:** purge the `gemma-local` agent lane from production code per user direct order 2026-05-17 night: "we wont use local gemma."

---

## Why

`gemma-local` was added as a candidate cheap on-machine summarization lane months ago. The capability matrix audit (`docs/agents/AGENT-CAPABILITY-MATRIX.md`, 2026-05-17 evening pass) found it surfacing in `/api/orient` `runtime.agents` with no recent use and no defined routing — "either resurrect or remove." User decision tonight is REMOVE.

Closes carry-over P0 item 6 from `docs/session-state/2026-05-17-late-night-deepseek-shipped-and-6pr-cascade.md`.

---

## Files to change

| File | Action |
|---|---|
| `scripts/agent_runtime/registry.py` | Remove the `"gemma-local"` entry at line 102 |
| `scripts/agent_runtime/gemma_local_cli.py` | Delete the file |
| `scripts/agent_runtime/adapters/gemma_local.py` | Delete the file |
| `scripts/build/dispatch.py` | Remove the `is_gemma_local` branch + the gemma-local default-model line (lines ~391, 395, 404-405, 418 in current main — grep `gemma`) |
| `tests/test_dispatch.py` | Remove or skip any test fixture that references `gemma-local` |
| `tests/test_agent_runtime.py` | Same — remove fixtures + assertions for gemma-local |
| `tests/test_agent_runtime_effort.py` | Same |
| `tests/rag/test_benchmark_harness.py` | Check if it parametrizes over agents including gemma; if so, drop the gemma parameter case |

Also search the codebase one final time before pushing:

```bash
grep -rln "gemma-local\|gemma_local\|GemmaLocal" --include="*.py" --include="*.md" --include="*.yaml" --include="*.json" \
  scripts/ tests/ docs/agents/ claude_extensions/rules/ 2>/dev/null
```

For any orphan reference found in docs (e.g., `docs/agents/AGENT-CAPABILITY-MATRIX.md` row 7 mentions `gemma-local`), update those docs in the same PR to mark the lane as REMOVED with a one-line note pointing at this PR.

---

## What you DON'T touch

* **Do not touch** the live `path3-pr2-fix-proposals-20260517-211756` Codex dispatch worktree at `.worktrees/dispatch/codex/path3-pr2-fix-proposals-20260517-211756/` — it's running PR2 work right now.
* Do not touch `scripts/agent_runtime/adapters/hermes_deepseek.py` (newly landed PR #2107) or any DeepSeek/Grok/Codex/Gemini adapter — scope is gemma-local only.
* Do not edit `/api/orient` runtime.agents listing source IF it reads from the registry (it likely does — the removal from registry.py will propagate). Check the source: `grep -n "runtime.*agents\|agent.*list" scripts/api/` and if there's a hardcoded list, drop `gemma-local` from it too.

---

## Verifiable claims this PR must produce (per #M-4)

| Claim | Tool + raw output to quote in PR body |
|---|---|
| Registry entry removed | `git diff scripts/agent_runtime/registry.py` showing the deleted block |
| Adapter + CLI files deleted | `git diff --stat origin/main` showing both `gemma_local_cli.py` and `adapters/gemma_local.py` as deleted (negative line counts) |
| dispatch.py routing removed | `git diff scripts/build/dispatch.py` showing each `gemma`-touching line removed |
| Tests still green | `.venv/bin/pytest tests/test_dispatch.py tests/test_agent_runtime.py tests/test_agent_runtime_effort.py tests/rag/test_benchmark_harness.py -v` final summary line raw |
| Full pytest still green | `.venv/bin/pytest tests/ -q --ignore=tests/build/` (the `tests/build/` subset is dominated by V7 build tests that can take a while; skipping keeps the run fast — IF anything in `tests/build/` references gemma, drop that ignore and quote the longer run instead) final summary line raw |
| Ruff clean | `.venv/bin/ruff check scripts/agent_runtime/ scripts/build/dispatch.py tests/` raw output |
| No remaining grep hits | `grep -rln "gemma-local\|gemma_local\|GemmaLocal" scripts/ tests/ docs/agents/ claude_extensions/ 2>/dev/null` raw output (must be empty OR only mention historical docs that are deliberately preserved with a one-line "REMOVED" note) |
| API orient no longer lists gemma-local | `curl -s --max-time 2 http://localhost:8765/api/orient | python3 -c "import json,sys; d=json.load(sys.stdin); print('gemma-local in runtime.agents:', 'gemma-local' in d['runtime']['agents'])"` raw output should be `False` (NOTE: api needs `./services.sh restart api` after the registry change. If you can't restart the API from inside the worktree, mention that in the PR body and leave the restart to the orchestrator) |
| Commit landed + PR opened | `git log -1 --oneline` raw + `gh pr view --json url` raw URL |

**No claim allowed without its raw output line.** Per #M-4.

---

## Worktree setup

`delegate.py dispatch --worktree` handles creation. Branch name: `chore/remove-gemma-local`.

---

## Verification (must run all BEFORE pushing)

```bash
# venv symlinked into worktree by delegate.py
.venv/bin/pytest tests/test_dispatch.py tests/test_agent_runtime.py tests/test_agent_runtime_effort.py tests/rag/test_benchmark_harness.py -v
.venv/bin/pytest tests/ -q --ignore=tests/build/
.venv/bin/ruff check scripts/agent_runtime/ scripts/build/dispatch.py tests/
.venv/bin/python -m pre_commit run --files \
    scripts/agent_runtime/registry.py \
    scripts/build/dispatch.py \
    tests/test_dispatch.py \
    tests/test_agent_runtime.py \
    tests/test_agent_runtime_effort.py
grep -rln "gemma-local\|gemma_local\|GemmaLocal" scripts/ tests/ docs/agents/ claude_extensions/ 2>/dev/null  # expect empty
git diff --stat origin/main
git diff --name-only origin/main
```

Per #M-7: pre-commit ≠ pytest. Both required.

---

## Commit + PR

Conventional commit message:

```
chore(agent-runtime): remove gemma-local lane (user direction 2026-05-17)

Per user direct order tonight: "we wont use local gemma." Capability
matrix audit (2026-05-17 evening) had flagged gemma-local as listed-but-
unused; decision to remove vs resurrect resolves as REMOVE.

Removes:
* registry entry "gemma-local"
* scripts/agent_runtime/gemma_local_cli.py (deleted)
* scripts/agent_runtime/adapters/gemma_local.py (deleted)
* scripts/build/dispatch.py gemma_local routing branches
* test fixtures referencing gemma-local in:
  - tests/test_dispatch.py
  - tests/test_agent_runtime.py
  - tests/test_agent_runtime_effort.py
  - tests/rag/test_benchmark_harness.py (if applicable)
* Optional: capability matrix row 7 marked REMOVED with one-line note

API restart needed after merge so /api/orient runtime.agents reflects:
  ./services.sh restart api

Closes carry-over P0 item 6 from 2026-05-17 late-night handoff.

Verification:
* relevant unit tests: <quote pytest final line>
* full pytest: <quote pytest final line>
* ruff: <quote raw>
* grep gemma → empty: <quote raw>
```

PR title: `chore(agent-runtime): remove gemma-local lane (user direction 2026-05-17)`

PR body:

```markdown
## Summary

Removes the `gemma-local` agent lane from production per user direct order tonight ("we wont use local gemma"). Carry-over P0 item 6 from the 2026-05-17 late-night handoff. Capability matrix audit had flagged the lane as listed-but-unused; decision tonight is REMOVE.

## Files changed

* `scripts/agent_runtime/registry.py` — entry removed
* `scripts/agent_runtime/gemma_local_cli.py` — deleted
* `scripts/agent_runtime/adapters/gemma_local.py` — deleted
* `scripts/build/dispatch.py` — gemma_local routing branches removed
* tests/* — fixtures referencing gemma-local removed
* docs/agents/AGENT-CAPABILITY-MATRIX.md — row 7 marked REMOVED (optional, in same PR)

## Verifiable claims (per #M-4)

* <git diff --stat raw>
* relevant unit tests: <pytest final line>
* full pytest (excluding tests/build/): <pytest final line>
* ruff: <raw All checks passed>
* grep "gemma" empty: <raw empty output>
* (API restart needed post-merge to refresh /api/orient runtime.agents)

## Test plan

- [x] Tests touching agent registry / dispatch still pass
- [x] No remaining grep hits on `gemma-local` / `gemma_local` / `GemmaLocal`
- [x] Ruff clean
```

NO `--auto-merge`. Leave the PR open; orchestrator merges after CI green.

---

## Anti-fabrication preamble

If anything in this brief surprises you — the registry has additional gemma-related entries beyond line 102, dispatch.py has branches outside lines 391/395/404-405/418, or a test imports `GemmaLocal` from somewhere else — STOP and quote the surprise verbatim before patching.

If the API's `runtime.agents` source is in a YAML/JSON config rather than reading from the registry, include the config update in the same PR.

If you find a test that DOES depend on `gemma-local` for a real assertion (not just a parameter case), STOP and quote it — we may need to migrate the test rather than delete it.
