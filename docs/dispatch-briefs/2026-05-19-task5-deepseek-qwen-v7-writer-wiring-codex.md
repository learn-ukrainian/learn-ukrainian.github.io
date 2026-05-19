# Dispatch — Task #5: wire `deepseek-tools` + `qwen-tools` as V7 writer families

**Agent:** codex
**Model:** `gpt-5.5`
**Effort:** `xhigh`
**Mode:** `danger` (worktree-isolated, can commit + push + open PR)
**Task ID:** `task5-deepseek-qwen-v7-wiring-20260519`
**Predecessor pattern:** PR #2033 (grok-tools wiring) — read its body for the deterministic-evidence shape we want.
**Issue:** none yet (this is task #5 from the 2026-05-19 carry-over queue; not blocking a single issue, but blocking task #6 (the 3-writer bakeoff)).
**Estimated effort:** half-day (~3-5 hours). Single PR.
**Reviewer policy:** human-merge after CI green; no `--admin` bypass.
**Status at dispatch time:** PR for #2148 γ must have merged first (task #5 touches the same `WRITER_CHOICES` tuple). If γ is still open, queue this brief and re-fire after γ lands.

---

## Why this exists

The V7 writer registry today is `("claude-tools", "gemini-tools", "codex-tools", "grok-tools")`. Two adapter implementations are already shipped on main but not surfaced to the V7 build path:

- `scripts/agent_runtime/adapters/hermes_deepseek.py` (`HermesDeepSeekAdapter`) — PR #2107 (`6abf72ea7e` neighborhood)
- `scripts/agent_runtime/adapters/hermes_qwen.py` (`HermesQwenAdapter`) — earlier 2026-05-18 session

The pre-approved task #6 bakeoff (deepseek + qwen + gemini, ~$6-10) is **blocked on these two missing writer-family entries**. This dispatch closes that gap by mirroring PR #2033's grok-tools wiring.

Per `memory/MEMORY.md` writer/reviewer policy: this is a wiring-only PR. No content semantics change. The bakeoff that follows is a separate dispatch.

---

## Pre-flight #M-4 evidence preamble (READ FIRST — mandatory)

Per `memory/MEMORY.md` #M-4 (deterministic-over-hallucination) and `docs/best-practices/deterministic-over-hallucination.md`. Every verifiable claim in the PR body MUST quote a tool-output triple (command + cwd + raw output). The claims and their tools:

| Claim in PR body | Required deterministic tool | Output format |
|---|---|---|
| "`deepseek-tools` registered in `WRITER_CHOICES`" | `grep -n "WRITER_CHOICES\\|WRITER_DEFAULTS" scripts/build/linear_pipeline.py` | quote matched lines raw |
| "`qwen-tools` registered in `WRITER_CHOICES`" | same | same |
| "Adapter classes importable" | `.venv/bin/python -c "from scripts.agent_runtime.adapters.hermes_deepseek import HermesDeepSeekAdapter; from scripts.agent_runtime.adapters.hermes_qwen import HermesQwenAdapter; print(HermesDeepSeekAdapter, HermesQwenAdapter)"` | quote raw output |
| "All adapter tests pass" | `.venv/bin/python -m pytest tests/agent_runtime/adapters/ -v` | quote final `N passed in M.MMs` line raw |
| "V7 routing tests pass" | `.venv/bin/python -m pytest tests/test_v7_writer_dispatch.py -v` | same |
| "Lint clean" | `.venv/bin/ruff check scripts/agent_runtime/ scripts/build/linear_pipeline.py scripts/build/v7_build.py tests/agent_runtime/` | quote `All checks passed!` raw |
| "Help string includes both new writers" | `.venv/bin/python scripts/build/v7_build.py --help 2>&1 \| grep -E "deepseek\\|qwen"` | quote matched lines raw |
| "Smoke build succeeded" | see Step 9 below; quote relevant `phase_done` JSONL events | (raw events) |

Do NOT write "I confirmed X" without a quoted command+output triple. The dispatch brief lint hook will run; quoted outputs are the reviewer's first stop.

---

## Anchor facts (deterministically verified for you)

The orchestrator pre-verified the following with tool calls. You SHOULD re-read each anchor file before editing it (per `code-editing-safety.md` rule 2).

1. **Existing adapters** — both shipped on main:
   - `scripts/agent_runtime/adapters/hermes_deepseek.py` (`HermesDeepSeekAdapter`)
   - `scripts/agent_runtime/adapters/hermes_qwen.py` (`HermesQwenAdapter`)
   Read their constructors and `default_model` to confirm shapes before wiring.

2. **Runtime registry** at `scripts/agent_runtime/registry.py:114-130` already has entries for both agents:
   ```
   "deepseek": {"adapter": "...:HermesDeepSeekAdapter", "default_model": "deepseek-v4-pro"}
   "qwen": {"adapter": "...:HermesQwenAdapter", "default_model": "qwen/qwen3.6-plus"}
   ```
   You do NOT add agents — they exist. You add the **`-tools` writer-family layer** on top.

3. **`scripts/build/linear_pipeline.py` lines 66-85** define the four wiring tuples that need new entries:
   ```python
   WRITER_CHOICES = ("claude-tools", "gemini-tools", "codex-tools", "grok-tools")
   WRITER_DEFAULTS: dict[str, dict[str, str]] = {
       "claude-tools": {"model": "claude-opus-4-7", "effort": "xhigh"},
       "gemini-tools": {"model": "gemini-3.1-pro-preview", "effort": "high"},
       "codex-tools": {"model": "gpt-5.5", "effort": "high"},
       "grok-tools": {"model": "grok-4.3", "effort": "medium"},
   }
   ...
   REVIEWER_CHOICES = ("claude-tools", "gemini-tools", "codex-tools", "grok-tools")
   REVIEWER_DEFAULTS: dict[str, dict[str, str]] = { ... mirror ... }
   ```
   Models + efforts you add:
   - `"deepseek-tools": {"model": "deepseek-v4-pro", "effort": "high"}`
   - `"qwen-tools": {"model": "qwen/qwen3.6-plus", "effort": "high"}`
   (Effort=high per night handoff user direction — upper-tier production, not budget flash.)

4. **`scripts/build/linear_pipeline.py` line 2593** (the `_runtime_tool_config` agent-label branch) currently bundles `gemini-tools` and `grok-tools` under the same shape:
   ```python
   elif agent_label in {"gemini-tools", "grok-tools"}:
       agent_kwargs = {"mcp_servers": ["sources"]}
   ```
   This needs extending. `deepseek-tools` + `qwen-tools` both also use the same shape — group them with the existing pair. Suggested:
   ```python
   elif agent_label in {"gemini-tools", "grok-tools", "deepseek-tools", "qwen-tools"}:
       agent_kwargs = {"mcp_servers": ["sources"]}
   ```
   The error path on line 2598-2601 must be updated to list all 6 expected `-tools` labels.

5. **`scripts/agent_runtime/tool_config.py` lines 25-35** (`canonical_agent` mapping) has `claude/gemini/codex/grok/deepseek` but is **MISSING qwen**:
   ```python
   if agent.startswith("claude"):    return "claude"
   if agent.startswith("gemini"):    return "gemini"
   if agent.startswith("codex"):     return "codex"
   if agent.startswith("grok"):      return "grok"
   if agent.startswith("deepseek"):  return "deepseek"
   return None
   ```
   **Add `if agent.startswith("qwen"): return "qwen"` before the final `return None`.** Without this, `_runtime_tool_config("qwen-tools")` resolves `canonical_agent = "qwen"` from `agent_label.split("-", 1)[0]` (correct), but the global `canonical_agent_for_label` helper at this module — which other call sites use — returns `None`. Verify by grepping for `canonical_agent_for_label`/`canonical_agent` use sites BEFORE editing.

6. **`scripts/agent_runtime/tool_config.py` line 234** has the Hermes-routing branch:
   ```python
   if canonical_agent in ("grok", "deepseek"):
       # Both route through Hermes; tool_config translation is identical
       ...
       return ({"hermes_mcp_servers": mcp_servers}, ...)
   ```
   **Extend the tuple to `("grok", "deepseek", "qwen")`** and update the comment to say "grok, deepseek, and qwen all route through Hermes."

7. **`scripts/build/v7_build.py`** — read the `_writer_prompt`, `_resolve_writer`, and `--writer` argparse-help shaping. PR #2033 added a `grok -> grok-tools` alias. Mirror that for `deepseek -> deepseek-tools` and `qwen -> qwen-tools` (so the CLI accepts `--writer deepseek` ergonomic shorthand).

8. **Tests** — adapter contract test pattern lives at `tests/agent_runtime/adapters/test_hermes_grok_adapter.py` (7 cases). New test files:
   - `tests/agent_runtime/adapters/test_hermes_deepseek_adapter.py` — if not already present from PR #2107, add it; otherwise verify coverage. Grep first: `find tests -name "test_hermes_deepseek*" -o -name "test_hermes_qwen*"`.
   - `tests/agent_runtime/adapters/test_hermes_qwen_adapter.py` — new.
   - `tests/test_v7_writer_dispatch.py` — extend with 2 new test cases covering `deepseek-tools` + `qwen-tools` routing (mirror the grok-tools cases in that file).

9. **Smoke build** — see Step 9 below. Single A1 module dry-run with each new writer, verifying the writer phase reaches a real output (not a wiring error). Do NOT push the smoke build's curriculum artifacts; just verify the pipeline accepts the writer.

---

## Pipeline-wiring policy guardrails (READ BEFORE EDITING)

The pipeline rule (`claude_extensions/rules/pipeline.md`) names claude-tools as the **default** V7 writer. This dispatch does NOT change that default. Both new writers are **opt-in via `--writer deepseek-tools`** or `--writer qwen-tools` on the v7_build.py CLI. The `WRITER_DEFAULTS` entry sets *defaults for that family*, not the project default.

`SELF_REVIEW_DETECTED` audit gate (per `claude_extensions/rules/pipeline.md`) enforces no-self-review. Add a smoke check or note in the PR body confirming neither new writer accidentally pairs itself as reviewer.

---

## What to build (worked example)

### Step 1 — `scripts/build/linear_pipeline.py`

(a) Extend `WRITER_CHOICES` (line 66):
```python
WRITER_CHOICES = (
    "claude-tools",
    "gemini-tools",
    "codex-tools",
    "grok-tools",
    "deepseek-tools",
    "qwen-tools",
)
```

(b) Extend `WRITER_DEFAULTS` (line 67-72):
```python
WRITER_DEFAULTS: dict[str, dict[str, str]] = {
    "claude-tools": {"model": "claude-opus-4-7", "effort": "xhigh"},
    "gemini-tools": {"model": "gemini-3.1-pro-preview", "effort": "high"},
    "codex-tools": {"model": "gpt-5.5", "effort": "high"},
    "grok-tools": {"model": "grok-4.3", "effort": "medium"},
    "deepseek-tools": {"model": "deepseek-v4-pro", "effort": "high"},
    "qwen-tools": {"model": "qwen/qwen3.6-plus", "effort": "high"},
}
```

(c) Mirror `REVIEWER_CHOICES` + `REVIEWER_DEFAULTS` identically.

(d) Extend the `_runtime_tool_config` branch at line 2593:
```python
elif agent_label in {"gemini-tools", "grok-tools", "deepseek-tools", "qwen-tools"}:
    agent_kwargs = {"mcp_servers": ["sources"]}
```

(e) Update the error message at line 2598-2601 to enumerate all six expected `-tools` labels.

### Step 2 — `scripts/agent_runtime/tool_config.py`

(a) Add qwen to `canonical_agent` mapping (line 35, before `return None`):
```python
if agent.startswith("qwen"):
    return "qwen"
```

(b) Extend the Hermes-routing tuple at line 234:
```python
if canonical_agent in ("grok", "deepseek", "qwen"):
    # grok, deepseek, and qwen all route through Hermes; tool_config translation
    # is identical (Hermes reads MCP servers from ~/.hermes/config.yaml).
    ...
```

### Step 3 — `scripts/build/v7_build.py`

Mirror PR #2033's grok aliasing. Two new alias entries:
- `deepseek` -> `deepseek-tools`
- `qwen` -> `qwen-tools`

Update `--writer` argparse-help string + the writer-cwd handling. If gemini-tools is the only writer that uses `PROJECT_ROOT` as cwd (per existing `v7_build.py` comment at line 738-742), confirm deepseek-tools + qwen-tools do NOT need this special-case — they should run from `module_dir` like claude/codex/grok (Hermes reads MCP from `~/.hermes/config.yaml`, not from cwd).

### Step 4 — Adapter contract tests

Read `tests/agent_runtime/adapters/test_hermes_grok_adapter.py` (155 LOC, 7 tests). Create symmetric test files:

(a) `tests/agent_runtime/adapters/test_hermes_qwen_adapter.py` — mirror the 7 grok adapter cases against `HermesQwenAdapter`. Verify:
- `invoke()` returns expected shape.
- `model` defaults to `"qwen/qwen3.6-plus"` per registry.
- `effort=high` is accepted.
- MCP server config is read from `~/.hermes/config.yaml` (not per-call payload).
- Error paths produce identifiable exceptions, not silent empty stdout.
- `tool_calls_total=None` (NOT 0) is the canonical telemetry-gap signal (per PR #2033 lesson).

(b) `tests/agent_runtime/adapters/test_hermes_deepseek_adapter.py` — if not already present (grep first), mirror the same 7 cases for `HermesDeepSeekAdapter`.

### Step 5 — V7 routing tests

`tests/test_v7_writer_dispatch.py` — read existing grok-tools coverage (cases 13-15 or thereabouts per PR #2033's "15 passed"). Add ≥2 new cases:
- `test_writer_deepseek_tools_routes_through_hermes` — assert that `--writer deepseek-tools` resolves to `HermesDeepSeekAdapter` via the runtime registry.
- `test_writer_qwen_tools_routes_through_hermes` — same for qwen.
- `test_writer_deepseek_alias_resolves_to_deepseek_tools` — CLI shorthand.
- `test_writer_qwen_alias_resolves_to_qwen_tools` — CLI shorthand.

### Step 6 — Self-review guard

Verify (in test or in code) that the SELF_REVIEW_DETECTED audit gate trips when `writer == reviewer == "deepseek-tools"` (and same for qwen). PR #2033 should have a parallel test for grok; mirror it.

### Step 7 — Documentation

(a) Update `claude_extensions/rules/pipeline.md` writer-family enumeration if it lists specific tools (grep first to confirm). The default-writer wording (`claude-tools`) does NOT change; only the set of *available* tools.

(b) Update `docs/SCRIPTS.md` `v7_build.py` entry's `--writer` enumeration if present.

### Step 8 — Lint + test sweep

Run the full sweep from the worktree (`.venv/bin/python` needs the main repo's `.venv`; either symlink or cd to main):
```
cd /Users/krisztiankoos/projects/learn-ukrainian
.venv/bin/ruff check scripts/agent_runtime/ scripts/build/linear_pipeline.py scripts/build/v7_build.py tests/agent_runtime/
.venv/bin/python -m pytest tests/agent_runtime/adapters/ tests/test_v7_writer_dispatch.py tests/test_agent_runtime.py -v
cd -
```
All must be green. Quote the final `N passed in M.MMs` and `All checks passed!` lines verbatim in the PR body.

### Step 9 — Smoke build (LOCAL, no commit of curriculum artifacts)

Verify each new writer reaches the writer phase (not a wiring error) on a single existing A1 module. Use `a1/my-morning` with a worktree that's reaped after smoke verification. Per `memory/MEMORY.md` BUILDS rule: V7 builds may be agent-run during autonomous orchestration **with `--worktree`**.

```
cd /Users/krisztiankoos/projects/learn-ukrainian
.venv/bin/python -u scripts/build/v7_build.py a1 my-morning --writer deepseek-tools --worktree 2>&1 | grep --line-buffered '^{"event"' | head -50
.venv/bin/python -u scripts/build/v7_build.py a1 my-morning --writer qwen-tools --worktree 2>&1 | grep --line-buffered '^{"event"' | head -50
```

Acceptance: each smoke run emits at least `mcp_config_resolved`, `writer_tool_call` (≥1), and either `phase_done` or a non-wiring-error `module_failed`. The smoke purpose is to verify the writer is *invoked correctly*, not that it produces an A1-compliant module — that's the bakeoff's job.

**Capture telemetry to `audit/2026-05-19-task5-smoke/`** under deepseek/ and qwen/ subdirs (JSONL event stream + first 100 lines of writer_output if reached). Quote the `phase_done` or `module_failed` lines in the PR body.

Do NOT commit the smoke worktrees. Reap with `git worktree remove --force .worktrees/builds/...`.

### Step 10 — Commit + push + open PR

Single commit. Conventional message:
```
git add -A
git commit -m "feat(v7): wire deepseek-tools + qwen-tools writer families (task #5)"
git push -u origin codex/task5-deepseek-qwen-v7-wiring-20260519
gh pr create --base main --head codex/task5-deepseek-qwen-v7-wiring-20260519 --title "feat(v7): wire deepseek-tools + qwen-tools writer families (task #5)" --body-file <(... see PR body template below ...)
```

**Do NOT auto-merge.** Orchestrator reviews + merges after CI green.

---

## Out of scope (intentional)

- **No `--writer X` self-review changes** beyond the existing audit gate guard.
- **No prompt-template additions.** `linear-write.md` is the canonical writer prompt for non-grok writers; deepseek-tools + qwen-tools share that template. No `linear-write-deepseek.md` / `linear-write-qwen.md` until a bakeoff signal indicates it.
- **No correction-prompt variant** for the new writers. Same rationale.
- **No m20 build under the new writers.** That's task #6 (the 3-writer bakeoff).
- **No removal of grok-tools.** All four pre-existing writer families stay.

---

## Numbered execution checklist (MANDATORY)

1. **Worktree setup.**
   ```
   cd /Users/krisztiankoos/projects/learn-ukrainian
   git fetch origin
   git worktree add -b codex/task5-deepseek-qwen-v7-wiring-20260519 .worktrees/dispatch/codex/task5-deepseek-qwen-v7-wiring-20260519 origin/main
   cd .worktrees/dispatch/codex/task5-deepseek-qwen-v7-wiring-20260519
   ```
   → verify: `git rev-parse --abbrev-ref HEAD` outputs `codex/task5-deepseek-qwen-v7-wiring-20260519`.

2. **Re-read anchor files BEFORE editing each** — `scripts/build/linear_pipeline.py` (lines 60-90 + 2570-2630), `scripts/agent_runtime/tool_config.py` (lines 20-50 + 220-260), `scripts/build/v7_build.py` writer-resolution section, `scripts/agent_runtime/registry.py`, both new adapter files, the grok adapter test, the v7 dispatch test, `claude_extensions/rules/pipeline.md` writer-family section.

3. **Implement steps 1-3** above (linear_pipeline + tool_config + v7_build). After each file edit, run `.venv/bin/ruff check <file>` from main repo cwd.

4. **Add adapter contract tests** (step 4 above).

5. **Add v7 routing tests + self-review guard** (steps 5-6 above).

6. **Update documentation** (step 7 above).

7. **Lint + test sweep** (step 8 above) — quote outputs raw in PR body.

8. **Smoke build** (step 9 above) — quote `phase_done`/`module_failed` lines.

9. **Commit + push + open PR** (step 10 above). NO `--no-verify`. NO auto-merge.

---

## PR body template

```markdown
## Summary

Wires `deepseek-tools` + `qwen-tools` as V7 writer families. Both adapters were already shipped on main (`HermesDeepSeekAdapter`, `HermesQwenAdapter`); this PR surfaces them to the V7 writer-selection layer so the upcoming 3-writer bakeoff (task #6: deepseek + qwen + gemini at ~$6-10) is unblocked. Mirrors PR #2033's grok-tools wiring pattern.

## Files changed

- `scripts/build/linear_pipeline.py` — extend `WRITER_CHOICES`, `WRITER_DEFAULTS`, `REVIEWER_CHOICES`, `REVIEWER_DEFAULTS`, and the `_runtime_tool_config` agent-label branch.
- `scripts/agent_runtime/tool_config.py` — add qwen to `canonical_agent` mapping; extend Hermes-routing tuple to include qwen.
- `scripts/build/v7_build.py` — alias `deepseek -> deepseek-tools`, `qwen -> qwen-tools`; update `--writer` help string.
- `tests/agent_runtime/adapters/test_hermes_qwen_adapter.py` — new, 7 contract cases (mirror grok adapter test).
- `tests/agent_runtime/adapters/test_hermes_deepseek_adapter.py` — added if missing, otherwise verified.
- `tests/test_v7_writer_dispatch.py` — extend with 4 new cases for deepseek/qwen routing + CLI aliases.
- `claude_extensions/rules/pipeline.md`, `docs/SCRIPTS.md` — docs touch-ups if writer-family enumerations exist.

## Verification evidence

(quote raw `pytest`, `ruff`, `python --help`, smoke `phase_done` outputs here)

## Out of scope

- claude-tools remains the default V7 writer.
- No prompt-template variants for the new writers (they share `linear-write.md`).
- m20 bakeoff under the new writers is task #6 (separate dispatch).

## Cross-links

- Pattern PR: #2033 (grok-tools wiring)
- DeepSeek adapter PR: #2107
- Qwen adapter session: 2026-05-18 (handoff `docs/session-state/2026-05-19-handoff-gap-audit-and-qwen-integration.md`)
- Carry-over queue task #5: `docs/session-state/2026-05-19-night-gap-audit-closure-and-qwen-judge-brief.md`
```

---

## Failure-mode planning

If you hit any of the following, STOP and report — do NOT push a half-fix:

1. **`tests/test_v7_writer_dispatch.py` regresses on a pre-existing grok-tools case.** Means the wiring extension broke a parallel path. Re-read the existing case before adding the new ones.

2. **MCP config resolves `config_empty` for deepseek-tools or qwen-tools.** Means the user's `~/.hermes/config.yaml` doesn't include MCP servers for these. Do NOT mutate the user's hermes config from this PR — file a follow-up issue and leave the wiring code in place; the bakeoff (task #6) will then surface the gap.

3. **Smoke build raises `LinearPipelineError: Unknown -tools writer ...`.** Means step 1(d) error-path text wasn't updated. Fix the enumeration and re-run smoke.

4. **Qwen smoke build returns rc=0 + empty stdout** (the 2026-05-16 Claude-via-Hermes failure mode noted in #M0). Capture telemetry, file as follow-up, do NOT block the PR — it ships the wiring; the auth/runtime failure is a separate hermes-config issue.

5. **`tests/test_agent_runtime.py` regresses on a pre-existing case.** Means the canonical_agent / Hermes-routing extension broke something else. Re-read the offending test before forcing it through.

---

## Provenance

- Predecessor pattern: PR #2033 (grok-tools wiring)
- DeepSeek adapter: PR #2107 + 2026-05-17 night handoff
- Qwen adapter: 2026-05-18 morning session + `scripts/agent_runtime/adapters/hermes_qwen.py`
- User direction (effort=high, upper-tier production models): `docs/session-state/2026-05-19-night-gap-audit-closure-and-qwen-judge-brief.md`
- Carry-over queue: same handoff, task #5
- Dispatch authored: 2026-05-19 (Claude orchestrator, this session, pre-staged while #2148 γ in flight)
