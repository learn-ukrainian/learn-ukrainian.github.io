# Dispatch brief — Russianism judge calibration matrix (multi-model × multi-harness × ±MCP)

> **Owner:** Codex
> **Filed:** 2026-05-17 (prepared 2026-05-16 night; fire when user returns)
> **Scope:** Generalize the existing `scripts/audit/grok_judge_calibration.py`
> into a model-agnostic, harness-agnostic calibration matrix runner.
> Implementation only — the orchestrator drives the actual matrix run
> after this PR merges.

---

## Why this matters

Tonight's Grok 4.3 onboarding (PR #2021) tested ONE model across efforts
and MCP states (4 rounds × Grok-medium/high/xhigh × ±MCP). User wants
to:

1. **Extend the matrix** across Claude opus-4-7/4-6 + sonnet-4-6 + 4-5
   variants + haiku-4-5, plus GPT 5.5/5.4/5.3-codex/5.3-codex-spark/5.2,
   plus Gemini 3.0-flash + 3.1-pro — each at the efforts the model
   actually supports.
2. **Add a HARNESS comparison dimension** — for Claude and OpenAI we
   can route via TWO harnesses (native CLI vs `hermes -z`). The Grok
   onboarding study confounded model and harness; this matrix isolates
   them so we know whether "Hermes is better" is a real claim.
3. **Generate one consolidated leaderboard** the orchestrator can use
   for #M0 routing decisions.

## Pre-locked test matrix

**Per-model effort palettes** (per-CLI-help discovery this session, NOT guessed):

| Provider | Models | Native CLI efforts | Hermes routes to |
|---|---|---|---|
| xAI Grok | grok-4.3 | (N/A; only Hermes route) | low, minimal, medium, high, xhigh |
| Anthropic | claude-opus-4-7 | low, medium, high, xhigh, **max** | same via Hermes anthropic provider |
| Anthropic | claude-opus-4-6, sonnet-4-6, opus-4-5-20251101, sonnet-4-5-20250929, opus-4-20250514, sonnet-4-20250514, haiku-4-5-20251001 | low, medium, high, xhigh (max only confirmed for 4-7) | same via Hermes |
| OpenAI | gpt-5.5, gpt-5.4, gpt-5.4-mini, gpt-5.3-codex, gpt-5.3-codex-spark, gpt-5.2 | low, medium, high (verify per model; not enumerated in `codex exec --help`) | same via Hermes openai-codex provider |
| Google | gemini-3.0-flash-preview, gemini-3.1-pro-preview | **NONE — CLI does not expose effort flag** (verified empirically; model itself reports "I support none of low/medium/high/xhigh"); Hermes-for-Gemini is **forbidden by Google ToS** (confirmed by user) | (forbidden) |

**Dimension shape** (computed at runtime; cells where the combination is
unsupported get `result: "n/a"`, `reason: "<explanation>"`, never
fabricated):

- **family** ∈ {xai, anthropic, openai, google}
- **model** ∈ (per provider list above)
- **harness** ∈ {native_cli, hermes} — google is `native_cli`-only
- **effort** ∈ (per-model palette, detected via probe + skip)
- **mcp_state** ∈ {with_mcp, without_mcp}

**Estimated cell count**: ~80-100 cells (sparse where unsupported).

## Pre-flight: read these first

1. `audit/2026-05-15-grok-4.3-judge-calibration/CONSOLIDATED-REPORT.md` —
   methodology + 12-case gold structure
2. `scripts/audit/grok_judge_calibration.py` — existing harness; extract
   common code (case loading, scoring, JSONL writing) into a shared
   `_judge_eval_lib.py` module
3. `scripts/audit/grok_stage_runner.py` — atomic config-swap pattern for
   per-call Hermes effort
4. `scripts/agent_runtime/adapters/{claude,codex,gemini}.py` — for
   native-CLI effort flag wiring conventions
5. `~/.hermes/config.yaml` lines around `model.default` and
   `reasoning_effort` — for Hermes per-call config-swap
6. `origin/pr-2006:eval/russianism/calibration-cases.jsonl` — the 12-case
   Antonenko-grounded gold (fetch via `git show`, not from local
   workspace, since PR #2006 may not be merged)

## #M-4 deterministic-evidence preamble

Every claim in the PR body must quote raw command + cwd + output. Specific
required evidence:

| Claim | Evidence |
|---|---|
| "Effort palette correctly detected per model" | Sample probe-result JSONL showing which effort × model combos returned valid responses vs which were skipped |
| "Hermes route for Claude works" | `hermes -z -m claude-opus-4-7 "Reply PONG."` raw output showing non-empty response (NOTE: as of 2026-05-16 this returned empty stdout in orchestrator probe — debug recipe in this brief) |
| "Hermes route for OpenAI works" | `hermes -z -m gpt-5.5 "Reply PONG."` raw output (already known good: returned `PONG`) |
| "Smoke matrix passes" | `pytest tests/audit/test_judge_calibration_matrix.py -v` raw summary |
| "Cell skipping is logged, not fabricated" | Sample run output showing `result: "n/a"`, `reason: "..."` for unsupported combos |
| "Commit landed" | `git log -1 --oneline` raw |
| "PR opened" | `gh pr view --json url -q '.url'` raw URL |

## Numbered steps (MANDATORY)

### 1. Worktree (created by dispatch wrapper)

`.worktrees/dispatch/codex/judge-calibration-matrix-2026-05-17/` from main.

### 2. Read existing harness + extract common module

Extract from `scripts/audit/grok_judge_calibration.py`:
- 12-case gold loader (`git show origin/pr-2006:eval/russianism/calibration-cases.jsonl`)
- Scoring function (F1, case_acc, precision, recall)
- Per-cell JSONL writer
- Leaderboard table builder

Land as `scripts/audit/_judge_eval_lib.py` (~150 LOC). Refactor
`grok_judge_calibration.py` to import from it (no behavior change).

### 3. Implement `scripts/audit/judge_calibration_matrix.py`

CLI shape:
```
python scripts/audit/judge_calibration_matrix.py \
    --families xai,anthropic,openai,google \
    --harnesses native_cli,hermes \
    --models <comma-separated-or-omit-for-all-supported> \
    --efforts <comma-separated-or-omit-for-per-model-palette> \
    --mcp-states with_mcp,without_mcp \
    --out-dir audit/2026-05-17-judge-calibration-matrix/ \
    --smoke           # 1 cell per family for validation
    --dry-run         # print matrix without running
    --resume          # skip cells already complete in out-dir
    --max-parallel 4  # per-family parallelism (within family only; cross-family stays serial to avoid quota interference)
```

**Cell key format** (used in output paths):
```
{family}/{model}/{harness}/{effort}-{mcp_state}.json
```

E.g.:
```
audit/2026-05-17-judge-calibration-matrix/anthropic/claude-opus-4-7/hermes/max-with_mcp.json
audit/2026-05-17-judge-calibration-matrix/xai/grok-4.3/hermes/medium-without_mcp.json
audit/2026-05-17-judge-calibration-matrix/google/gemini-3.1-pro-preview/native_cli/default-with_mcp.json
```

**Per-cell output shape** (per Grok onboarding precedent):
```json
{
  "cell": {
    "family": "anthropic",
    "model": "claude-opus-4-7",
    "harness": "hermes",
    "effort": "max",
    "mcp_state": "with_mcp"
  },
  "started_at": "2026-05-17T...",
  "finished_at": "2026-05-17T...",
  "duration_s": 287.4,
  "n_cases": 12,
  "judgments": [{ "case_id": "cal_clean_short_prose", "true_label": "clean", "model_label": "clean", "model_confidence": "high", "raw_response_chars": 423 }, ...],
  "scores": {
    "f1": 0.85,
    "case_acc": 0.917,
    "precision": 0.91,
    "recall": 0.80
  },
  "raw_telemetry": {
    "harness": "hermes",
    "harness_version": "...",
    "model_id": "claude-opus-4-7",
    "effort_actual": "max",
    "mcp_servers": ["sources"],
    "errors": []
  }
}
```

**Per-cell output for unsupported combo:**
```json
{
  "cell": { ... },
  "result": "n/a",
  "reason": "claude-sonnet-4-6 does not accept effort=max via native CLI (CLI returned: <verbatim error>)",
  "checked_at": "2026-05-17T..."
}
```

NEVER skip a cell silently. Every combo gets a file, even unsupported.

### 4. Harness routing implementations

#### native_cli routes

- **Claude**: `claude -p --bare --model <model> --effort <effort> "<prompt>"` (+ MCP via project `.mcp.json`)
- **Codex**: `codex exec --model <model> -c model_reasoning_effort=<effort> "<prompt>"` (+ MCP via project `.mcp.json`)
- **Gemini**: `gemini -m <model> -p "<prompt>"` (effort NOT routed — no flag)

#### hermes route

- Atomic config swap of `~/.hermes/config.yaml` for effort:
  - Backup config → write new effort → run `hermes -z "<prompt>" -m <model>` → restore backup
  - Mutex/lock to prevent concurrent runs trampling each other (use `fcntl.flock` on the config file path)
- MCP: leave Hermes's `sources` MCP registration in place; for
  `mcp_state=without_mcp`, temporarily disable it via `hermes mcp disable
  sources` (and re-enable after the cell)

### 5. Top-level leaderboard generation

After all cells run, generate `audit/2026-05-17-judge-calibration-matrix/REPORT.html` (per project audit template) + `REPORT.md` companion. Structure:

- Summary stats (cells passed / n/a / errored)
- **Sorted leaderboard table** by F1 descending, with columns: family, model, harness, effort, mcp_state, F1, P, R, case_acc, avg_dur, n/a-count
- **Harness-comparison subtable**: for each (model, effort, mcp_state) where both harnesses ran, the F1 delta (hermes - native_cli)
- **MCP-impact subtable**: for each (model, harness, effort) where both MCP states ran, the case_acc delta (with - without)
- **Effort-scaling subtable**: for each (model, harness, mcp_state), the F1 across efforts (does max always win? does high underperform medium per Grok finding?)
- **Failure log**: every cell with `result: "n/a"` or non-empty `errors`, with reason

### 6. Tests

`tests/audit/test_judge_calibration_matrix.py`:

1. `test_cell_key_format` — paths constructed correctly
2. `test_unsupported_effort_returns_n_a_not_fabricated` — when a model's effort palette doesn't include the requested level, returns `result: "n/a"` with reason, never a fake score
3. `test_resume_skips_existing_cells` — if `audit/.../REPORT.md` exists for a cell, it's not re-run
4. `test_hermes_config_swap_is_atomic` — mock-test that backup→write→restore happens; on exception, backup is restored
5. `test_score_calculation_matches_grok_baseline` — feed the exact judgments from `audit/2026-05-15-grok-4.3-judge-calibration-with-mcp/judgments.jsonl`; assert scores match the existing REPORT.md F1/case_acc figures (regression guard)
6. `test_leaderboard_sorted_by_f1_descending` — given mock per-cell results, assert REPORT.md top row has highest F1

### 7. Debug recipe for orchestrator (NOT in PR; this is a runbook for the matrix-driver)

Document this in `docs/runbooks/judge-calibration-matrix-runbook.md`:

```
# Pre-flight: claude-via-hermes empty-output debug

Before running the full matrix, verify both Hermes routes return non-empty:

  hermes -z "Reply PONG." -m gpt-5.5            # expect: PONG (known good)
  hermes -z "Reply PONG." -m claude-opus-4-7    # 2026-05-16 returned empty; debug:
    - hermes -z "..." -m claude-opus-4-7 --provider anthropic   # explicit provider
    - hermes -z "..." -m claude-opus-4-7 2>&1 | head -200       # check stderr
    - HERMES_DEBUG=1 hermes -z "..." -m claude-opus-4-7         # if debug env var exists
    - check ~/.hermes/logs/ for last call's full trace
    - try claude-opus-4-6 to see if it's an opus-4-7-specific issue
    - try claude-sonnet-4-6 to see if it's an opus-tier issue

If still empty after debug: report and fall back to claude native_cli for the matrix; document the Hermes-Claude blocker as a follow-up issue.

# Per-family run (recommended after smoke passes):

python scripts/audit/judge_calibration_matrix.py \
    --families xai \
    --harnesses hermes \
    --out-dir audit/2026-05-17-judge-calibration-matrix/

python scripts/audit/judge_calibration_matrix.py \
    --families anthropic \
    --harnesses native_cli,hermes \
    --resume \
    --out-dir audit/2026-05-17-judge-calibration-matrix/

python scripts/audit/judge_calibration_matrix.py \
    --families openai \
    --harnesses native_cli,hermes \
    --resume \
    --out-dir audit/2026-05-17-judge-calibration-matrix/

python scripts/audit/judge_calibration_matrix.py \
    --families google \
    --harnesses native_cli \
    --resume \
    --out-dir audit/2026-05-17-judge-calibration-matrix/

# Then generate the consolidated leaderboard:
python scripts/audit/judge_calibration_matrix.py --build-report-only --out-dir audit/2026-05-17-judge-calibration-matrix/
```

### 8. Lint + pytest

```
.venv/bin/ruff check scripts/audit/_judge_eval_lib.py scripts/audit/judge_calibration_matrix.py tests/audit/test_judge_calibration_matrix.py
# venv symlinked into worktree by delegate.py
.venv/bin/python -m pytest tests/audit/test_judge_calibration_matrix.py -v
# venv symlinked into worktree by delegate.py
.venv/bin/python -m pytest tests/audit/ -x -q
```

### 9. Smoke run (in dispatch — small, ~5 min, validates harness without burning quota)

ONLY in the dispatch:
```
python scripts/audit/judge_calibration_matrix.py \
    --smoke \
    --out-dir audit/2026-05-17-judge-calibration-matrix-smoke/
```

Smoke = 1 cell per family at the cheapest model × medium effort × with_mcp. ~5 cells × ~30s each = ~3 min wall-clock. Confirms each route works end-to-end. DO NOT run the full matrix in the dispatch — the orchestrator drives that.

### 10. Commit + PR

Standard pattern. Branch `codex/judge-calibration-matrix-2026-05-17`.
Base main. Body must quote raw evidence from #M-4 table.

DO NOT auto-merge.

## Acceptance criteria

- [ ] `_judge_eval_lib.py` exists and `grok_judge_calibration.py` imports from it (no behavior change in the existing harness)
- [ ] `judge_calibration_matrix.py` runs with `--smoke` and produces 5 cells worth of JSON (one per family)
- [ ] Unsupported effort × model combos write `result: "n/a"` with reason (test asserts this)
- [ ] Score-regression test passes (matches existing Grok REPORT.md exactly)
- [ ] Runbook `docs/runbooks/judge-calibration-matrix-runbook.md` exists with per-family commands + debug recipe
- [ ] PR body has #M-4 evidence for each claim

## Out of scope (file follow-ups; do NOT include)

- The actual full-matrix run (orchestrator's job after merge)
- Per-cell cost telemetry → Monitor API (separate; can add as Phase 2)
- Cross-test-set generalization (sticking to the 12-case Antonenko gold for v1; future work can add UA-GEC pulls)
- A web UI for browsing per-cell results (HTML report is enough for v1)
- Gemini-via-Hermes (Google ToS violation per user; explicitly excluded)

## Failure modes to avoid

- **Don't fabricate cell results.** Every combo gets a file: real score OR `n/a` with reason.
- **Don't run the full matrix in the dispatch.** Smoke only (~3 min). Full matrix is orchestrator-driven after merge.
- **Don't mutate `~/.hermes/config.yaml` without atomic backup-swap-restore + flock.** Concurrent matrix runs would trample each other's effort settings.
- **Don't auto-merge.** Orchestrator reviews + merges.
- **Don't include `gemini × hermes` cells.** Forbidden by Google ToS.
- **Don't probe Claude-via-Hermes until the empty-output debug recipe is run.** Save the orchestrator's Claude quota.

---

*Brief format: MD per #M-2 (ai → ai). Companion to:
`audit/2026-05-15-grok-4.3-judge-calibration/REPORT.html` (the existing
single-model baseline this matrix generalizes from).*
