# Dispatch — Add deepseek-tools + qwen-tools as V7 writer choices

**Agent:** codex
**Model:** `gpt-5.5`
**Effort:** `xhigh`
**Mode:** `danger` (worktree-isolated, can commit + push + open PR)
**Task ID:** `deepseek-qwen-writer-tools-20260519`
**Source direction:** User direction 2026-05-19 — required infrastructure before running a B1 writer bakeoff across 5 models (claude opus, gpt-5.5, deepseek-v4-pro, qwen-3.6-plus, gemini-3.1-pro-preview) with production-realistic native adapters. `v7_build.py --writer` currently only accepts `claude-tools, gemini-tools, codex-tools, grok-tools`; deepseek and qwen are missing.
**Estimated effort:** 1-2 hours.
**Reviewer policy:** human-merge after CI green; no `--admin` bypass (per `memory/MEMORY.md` #M-0.5).

---

## Why this exists (one paragraph)

Two V7 writer-tools adapters need to be added — `deepseek-tools` and `qwen-tools` — so `scripts/build/v7_build.py --writer` accepts them. The underlying `agent_runtime` already has Hermes-backed adapters (`HermesDeepSeekAdapter`, `HermesQwenAdapter`) used by `delegate.py` dispatches; this dispatch wires those existing adapters into the V7 writer pipeline by mirroring the `grok-tools` pattern (which is also Hermes-backed and already works). MCP tool wiring happens via `~/.hermes/config.yaml` for all three Hermes-routed writers, so no new MCP config layer is needed.

---

## Pre-flight #M-4 evidence preamble (READ FIRST — mandatory)

This dispatch must obey `memory/MEMORY.md` #M-4 (deterministic-over-hallucination) and `docs/best-practices/deterministic-over-hallucination.md`. Every verifiable claim in the PR body MUST quote a tool-output triple (command + cwd + raw output).

| Claim in PR body | Required deterministic tool | Output format |
|---|---|---|
| "Tests pass" | `.venv/bin/python -m pytest tests/test_v7_writer_dispatch.py tests/test_mcp_init_observability.py tests/agent_runtime/ -v` from repo root | quote final `N passed in M.MMs` line raw |
| "Lint clean" | `.venv/bin/ruff check scripts/build/ scripts/agent_runtime/ tests/` from repo root | quote `All checks passed!` or zero-error final line raw |
| "WRITER_CHOICES updated" | `.venv/bin/python -c "from scripts.build.linear_pipeline import WRITER_CHOICES; print(WRITER_CHOICES)"` from repo root | quote the printed tuple raw — must include both `deepseek-tools` and `qwen-tools` |
| "v7_build.py argparse accepts deepseek-tools + qwen-tools" | `.venv/bin/python scripts/build/v7_build.py a1 my-morning --writer deepseek-tools --dry-run 2>&1 \| tail -5` AND `.venv/bin/python scripts/build/v7_build.py a1 my-morning --writer qwen-tools --dry-run 2>&1 \| tail -5` from repo root | quote tail lines — `--dry-run` should reach the writer-prep phase without an argparse error |
| "MCP tool_config builds for both new writers" | `.venv/bin/python -c "from scripts.build import linear_pipeline; print(linear_pipeline._runtime_tool_config('deepseek-tools', event_sink=lambda *a, **k: None).get('hermes_mcp_servers'))"` AND same for `qwen-tools` from repo root | quote each printed value — expected: `['sources']` for both |
| "Commit landed" | `git log -1 --oneline` from worktree | quote line raw |
| "PR opened" | `gh pr view --json url -q .url` | quote URL raw |

Do NOT write "I confirmed X" without a quoted command+output triple. The reviewer will grep for evidence.

---

## Anchor facts (orchestrator pre-verified)

1. **Existing Hermes-routed writer-tools pattern: `grok-tools`** at `scripts/build/linear_pipeline.py:66-85`.
   - `WRITER_CHOICES = ("claude-tools", "gemini-tools", "codex-tools", "grok-tools")` (line 66)
   - `WRITER_DEFAULTS["grok-tools"] = {"model": "grok-4.3", "effort": "medium"}` (line 71)
   - `PROMPT_BY_WRITER["grok-tools"] = "linear-write-grok.md"` (line 74) — variant prompt
   - `CORRECTION_PROMPT_BY_WRITER["grok-tools"] = "linear-writer-correction-grok.md"` (line 77)
   - REVIEWER side mirrors writer side (lines 79-85).
   - `_runtime_tool_config` branches at line 2609: `elif agent_label in {"gemini-tools", "grok-tools"}: agent_kwargs = {"mcp_servers": ["sources"]}`.

2. **Hermes-MCP wiring already supports `grok` and `deepseek` as canonical agents.** From `scripts/agent_runtime/tool_config.py:23-35`:
   ```python
   def _canonical_agent_name(agent: str) -> str | None:
       if agent.startswith("claude"): return "claude"
       if agent.startswith("gemini"): return "gemini"
       if agent.startswith("codex"): return "codex"
       if agent.startswith("grok"): return "grok"
       if agent.startswith("deepseek"): return "deepseek"
       return None
   ```
   And the Hermes routing branch at line 234: `if canonical_agent in ("grok", "deepseek"): ...`
   **NEW canonical agent `qwen` MUST be added to BOTH places** for `qwen-tools` to work.

3. **Existing agent_runtime adapters** at `scripts/agent_runtime/adapters/`:
   - `hermes_grok.py` — HermesGrokAdapter
   - `hermes_deepseek.py` — HermesDeepSeekAdapter (already used by `--agent deepseek` dispatches)
   - `hermes_qwen.py` — HermesQwenAdapter (already used by `--agent qwen` dispatches; recently patched `c16e0cffc6` to force `--provider openrouter`)
   These are already registered in `scripts/agent_runtime/registry.py`. The V7 writer pipeline just needs to know about the `-tools` labels and route to them.

4. **v7_build.py aliases and argparse** at lines 33-39:
   ```python
   WRITER_ALIASES = {
       "claude": "claude-tools",
       "gemini": "gemini-tools",
       "codex": "codex-tools",
       "grok": "grok-tools",
   }
   WRITER_CHOICES = (*linear_pipeline.WRITER_CHOICES, *WRITER_ALIASES)
   ```
   Argparse choices flow from `WRITER_CHOICES`. Need to add `deepseek` → `deepseek-tools` and `qwen` → `qwen-tools` aliases.

5. **Hermes config has `sources` MCP** at `~/.hermes/config.yaml:463-465` (`mcp_servers.sources.enabled: true, url: http://127.0.0.1:8766/mcp`). No Hermes config changes needed.

6. **Default model + effort for the two new writers** (set in `WRITER_DEFAULTS`):
   - `deepseek-tools` → `{"model": "deepseek-v4-pro", "effort": "medium"}` (matching production deepseek dispatch defaults; effort low because deepseek-v4-pro has built-in reasoning)
   - `qwen-tools` → `{"model": "qwen/qwen3.6-plus", "effort": "medium"}` (qwen3.6-plus is the user's named production default per the recent multi-writer strategy conversation)

   These defaults can be overridden per-call. Effort levels reflect what Hermes' top-level `agent.reasoning_effort` accepts; if Hermes config disagrees, the adapters already log warnings (per `hermes_qwen.py` lines 134-147).

7. **No new prompt variants required initially.** `deepseek-tools` and `qwen-tools` use the DEFAULT `linear-write.md` (no entries in `PROMPT_BY_WRITER` / `CORRECTION_PROMPT_BY_WRITER`). If empirical testing later shows model-specific issues, variant prompts can be added in a follow-up.

8. **Tests that already mirror the writer-tools list** (need to be updated):
   - `tests/test_v7_writer_dispatch.py` (lines 85, 104-108) — asserts `WRITER_DEFAULTS[writer]` values + `WRITER_CHOICES` membership
   - `tests/test_mcp_init_observability.py` (lines 156-357) — multiple `_runtime_tool_config` tests with hardcoded writer labels
   These are the test fixtures that #M-7 flags as "files with hardcoded test fixture mirroring its content" — they MUST be updated as part of this dispatch.

---

## Numbered execution steps (mandatory order)

### Step 0 — Set up worktree

```bash
git worktree add .worktrees/dispatch/codex/deepseek-qwen-writer-tools-20260519 origin/main
cd .worktrees/dispatch/codex/deepseek-qwen-writer-tools-20260519
```

### Step 1 — `scripts/agent_runtime/tool_config.py`: add `qwen` support

1. In `_canonical_agent_name()` (lines 23-35), add the qwen branch BEFORE the final `return None`:
   ```python
   if agent.startswith("qwen"):
       return "qwen"
   ```
2. In the Hermes-routing branch (line 234), extend the tuple:
   ```python
   if canonical_agent in ("grok", "deepseek", "qwen"):
   ```
3. No changes needed for `deepseek` (already supported).

### Step 2 — `scripts/build/linear_pipeline.py`: register the new writer-tools

In the writer block (lines 66-91):

1. Extend `WRITER_CHOICES`:
   ```python
   WRITER_CHOICES = ("claude-tools", "gemini-tools", "codex-tools", "grok-tools", "deepseek-tools", "qwen-tools")
   ```
2. Add to `WRITER_DEFAULTS`:
   ```python
   "deepseek-tools": {"model": "deepseek-v4-pro", "effort": "medium"},
   "qwen-tools": {"model": "qwen/qwen3.6-plus", "effort": "medium"},
   ```
3. Skip `PROMPT_BY_WRITER` / `CORRECTION_PROMPT_BY_WRITER` — both new writers use the default prompts (no variant).
4. Mirror in `REVIEWER_CHOICES` (line 79) and `REVIEWER_DEFAULTS` (lines 80-85) using the same model + effort.
5. In `_runtime_tool_config` (line 2609), extend the branch:
   ```python
   elif agent_label in {"gemini-tools", "grok-tools", "deepseek-tools", "qwen-tools"}:
       agent_kwargs = {
           "mcp_servers": ["sources"],
       }
   ```
6. Update the error message at line 2614-2617:
   ```python
   raise LinearPipelineError(
       f"Unknown -tools writer {agent_label!r}; expected one of "
       "codex-tools / claude-tools / gemini-tools / grok-tools / deepseek-tools / qwen-tools."
   )
   ```

### Step 3 — `scripts/build/v7_build.py`: argparse + alias updates

1. Extend `WRITER_ALIASES` (line 33-38):
   ```python
   WRITER_ALIASES = {
       "claude": "claude-tools",
       "gemini": "gemini-tools",
       "codex": "codex-tools",
       "grok": "grok-tools",
       "deepseek": "deepseek-tools",
       "qwen": "qwen-tools",
   }
   ```
2. `WRITER_CHOICES` at line 39 auto-derives from `linear_pipeline.WRITER_CHOICES + WRITER_ALIASES` — no manual change needed.
3. Update the help-text examples at lines 541-542 if useful — optional.
4. Inspect line 439-443 (`_alternate_writer` or similar — the function that picks an alternate writer for cross-review). Decide whether `deepseek-tools` and `qwen-tools` should have alternate-writer mappings. If unclear, leave the function returning `claude-tools` as fallback (mirrors the existing default-fallback behavior).
5. Inspect `writer_cwd` logic at line 746 — `cwd = PROJECT_ROOT if writer == "gemini-tools" else module_dir`. The new writers should follow the `module_dir` default (same as claude-tools/codex-tools/grok-tools). No change needed.

### Step 4 — Update tests

1. **`tests/test_v7_writer_dispatch.py`**:
   - Find the parametrized writer tests at line 85-86 + line 104-108. Add `deepseek-tools` and `qwen-tools` to the parametrize list.
   - Verify the test still passes with the new writer entries.

2. **`tests/test_mcp_init_observability.py`**:
   - Add at least one positive-path test for `deepseek-tools` and one for `qwen-tools`, mirroring `test_runtime_tool_config_claude_tools_emits_resolution_event_success` (line 269).
   - Verify the error path: `test_runtime_tool_config_unknown_tools_writer_raises` (line 352) — confirm "phantom-tools" still raises (the error message updated in Step 2.6).

3. **`tests/agent_runtime/adapters/test_hermes_qwen_adapter.py`** + **`tests/agent_runtime/adapters/test_hermes_deepseek_adapter.py`**: These are the dispatch-adapter tests, NOT writer-tools tests. No changes needed unless you find existing assertions about writer-tools labels.

4. Run the full agent_runtime + build test suites and quote pass output in the PR body.

### Step 5 — Lint sweep

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
.venv/bin/ruff check scripts/build/ scripts/agent_runtime/ tests/
```

### Step 6 — Verification: dry-run for both new writers

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
.venv/bin/python scripts/build/v7_build.py a1 my-morning --writer deepseek-tools --dry-run 2>&1 | tail -10
.venv/bin/python scripts/build/v7_build.py a1 my-morning --writer qwen-tools --dry-run 2>&1 | tail -10
```

Both should reach the writer-prep phase without an argparse error. `--dry-run` stops before writer invocation, so no actual API calls. Confirm:
- No `argparse.ArgumentError: invalid choice` for the new writer values.
- No `LinearPipelineError: Unknown -tools writer`.
- MCP config resolution succeeds (the `mcp_config_resolved` event has `requested_servers=["sources"]` and `resolved_servers=["sources"]`).

### Step 7 — Commit + PR

```bash
git add scripts/agent_runtime/tool_config.py scripts/build/linear_pipeline.py scripts/build/v7_build.py tests/
git commit -m "$(cat <<'EOF'
feat(v7-writer): add deepseek-tools + qwen-tools writer choices

Adds two new V7 writer adapters mirroring the existing grok-tools
Hermes-backed pattern: deepseek-tools (model=deepseek-v4-pro) and
qwen-tools (model=qwen/qwen3.6-plus). Both route through Hermes which
reads MCP servers from ~/.hermes/config.yaml; no per-call MCP shape
translation needed.

Required for the upcoming B1 writer bakeoff with production-realistic
native adapters across all 5 named models (claude opus, gpt-5.5,
deepseek-v4-pro, qwen-3.6-plus, gemini-3.1-pro-preview). Without these
two adapters, deepseek and qwen could only be tested via raw
delegate.py dispatch with no MCP tool wiring, which is not
production-equivalent.

Changes:
- scripts/agent_runtime/tool_config.py: add `qwen` to
  _canonical_agent_name() + extend Hermes-routing branch
- scripts/build/linear_pipeline.py: add to WRITER_CHOICES,
  WRITER_DEFAULTS, REVIEWER_CHOICES, REVIEWER_DEFAULTS,
  _runtime_tool_config branches
- scripts/build/v7_build.py: add WRITER_ALIASES entries
- tests/test_v7_writer_dispatch.py + tests/test_mcp_init_observability.py:
  extend coverage for both new writers

No prompt variants added; both writers use the default linear-write.md.
If empirical testing later shows model-specific issues, variant prompts
can be added in a follow-up.

Co-Authored-By: Codex GPT-5.5 <noreply@openai.com>
EOF
)"
git push -u origin codex/deepseek-qwen-writer-tools-20260519
gh pr create --title "feat(v7-writer): add deepseek-tools + qwen-tools writer choices" --body "$(cat <<'EOF'
## Summary

Adds two new V7 writer adapters mirroring the existing grok-tools Hermes-backed pattern: `deepseek-tools` (model=`deepseek-v4-pro`) and `qwen-tools` (model=`qwen/qwen3.6-plus`). Both route through Hermes; MCP tool wiring via `~/.hermes/config.yaml`.

Required infrastructure for the upcoming B1 writer bakeoff across 5 named models. Without these, deepseek + qwen could only be tested via raw delegate.py dispatch with no MCP tool wiring, which is not production-equivalent.

## #M-4 evidence preamble

(Codex: fill in each row with the actual command + cwd + raw output during execution.)

- Tests pass: …
- Lint clean: …
- WRITER_CHOICES updated: …
- v7_build.py argparse accepts deepseek-tools + qwen-tools: …
- MCP tool_config builds for both new writers: …

## Test plan

- [x] `tests/test_v7_writer_dispatch.py` — extended parametrize for both new writers.
- [x] `tests/test_mcp_init_observability.py` — positive-path test for each new writer.
- [x] Ruff lint clean across modified scope.
- [x] `--dry-run` smoke test for both writer values (passes argparse + reaches writer-prep phase).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

**DO NOT auto-merge.** Per project policy, human reviews before merge.

---

## Out of scope for this dispatch

- **Prompt variants per writer** (`linear-write-deepseek.md`, `linear-write-qwen.md`). The grok variant exists because empirical testing showed grok needs different scaffolding; this dispatch starts with the default prompt for both new writers. If empirical testing in the B1 bakeoff shows model-specific issues, file a follow-up to add variants.
- **Actually running the B1 bakeoff.** That's the next dispatch after this one merges.
- **Promoting deepseek-tools or qwen-tools to V7 default writer.** That's a separate routing decision (matrix v1.3) gated on bakeoff data.
- **Reviewing the existing kimi/minimax routing through HermesQwenAdapter.** That's already handled by the recent provider-routing fix at `c16e0cffc6`; this dispatch doesn't touch that adapter beyond adding the `qwen-tools` label.

---

## Decision tree on test failure

| Failure mode | Disposition |
|---|---|
| `_runtime_tool_config` for new writer raises `Unknown -tools writer` | Step 2.5 incomplete — the branch in line 2609 didn't include the new writer. |
| `_canonical_agent_name()` returns None for `qwen` | Step 1.1 incomplete — the qwen branch wasn't added. |
| `--dry-run` argparse error | Step 3.1 incomplete — `WRITER_ALIASES` didn't include the new agent. |
| MCP `resolved_servers` is empty | Hermes config at `~/.hermes/config.yaml` doesn't have `mcp_servers.sources` enabled. **Escalate** — don't try to mutate the Hermes config from a dispatch; that's an operator decision. |
| Tests pass but PR-CI fails on a different test | Read the failing test, decide if it's affected by this change. If yes — extend coverage. If no (flake / unrelated) — file an issue and don't block this PR. |

---

## Cross-references

- Issue #2157 (escalated CoT-removal dispatch): not directly related, but the same operator drove both this morning. That dispatch is held pending revised scope; this one proceeds independently.
- HermesQwenAdapter provider-routing fix: `c16e0cffc6` on main 2026-05-19 (already addresses `moonshotai/*` + `minimax/*` routing; not in this dispatch's scope).
- v1 multi-agent routing audit: `audit/2026-05-19-multi-agent-routing-assessment/REPORT.html` (provides the empirical case for testing these models as V7 writers).
- B1 writer bakeoff plan: docs/projects/ua-eval-harness/README.md and the next-session work named in `docs/session-state/current.md`. Wait for this PR to merge before firing the bakeoff.
