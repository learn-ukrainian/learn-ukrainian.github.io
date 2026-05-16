# Dispatch — code-review benchmark harness for cross-model PR review

**Agent:** codex
**Model:** gpt-5.5
**Effort:** medium
**Mode:** danger (worktree)
**Base:** origin/main

## Why

The judge calibration matrix (PR #2037, `audit/2026-05-17-judge-calibration-matrix/`) empirically validated Grok for **cleanliness/Russianism classification** (xhigh+MCP: F1 78.6%, case_acc 100%). But "use Grok best to offload Codex" — the active strategic question — has a different load-bearing claim: **Grok-as-code-reviewer**. Onboarding (#2021) anecdotally found Grok caught issue #2018 + 3 regex edge cases that Claude missed. We have ZERO matrix-style empirical data on that lane. That's the gap this benchmark closes.

Without it, we can't responsibly route real Codex review traffic to Grok or any other model.

## What you're building

A new harness `scripts/audit/code_review_benchmark.py` that runs a structured "review this PR diff" task across multiple models × harnesses × efforts × ±MCP and scores findings against a curated gold-standard corpus.

The matrix shape is identical to `scripts/audit/judge_calibration_matrix.py` — model it directly. The differences are: (a) input cases are PR diffs, (b) verdict is a structured list of findings, (c) scoring is precision/recall/F1 on findings matched against gold.

## Concrete plan

### Step 1 — git worktree

```bash
git worktree add -b codex/code-review-benchmark-2026-05-16 \
  .worktrees/dispatch/codex/code-review-benchmark-2026-05-16 origin/main
cd .worktrees/dispatch/codex/code-review-benchmark-2026-05-16
```

### Step 2 — corpus structure

Create `audit/code-review-benchmark/corpus/` with one YAML file per case. Each file has:

```yaml
case_id: pr-2025-openai-proxy
pr_number: 2025
title: "OpenAI-compat HTTP proxy at :8767"
diff_path: corpus/pr-2025-openai-proxy.diff       # actual unified diff
context: |
  Two-paragraph human-written context on what the PR does and what risk
  classes the reviewer should be on the lookout for.
gold_findings:
  - id: arg-max
    severity: HIGH
    category: security
    location: scripts/ai_agent_bridge/openai_proxy.py
    description: >
      Prompts >256KB hit ARG_MAX/E2BIG because the proxy passes the prompt
      via argv to the upstream CLI. Should use stdin.
  - id: error-envelope
    severity: HIGH
    category: spec-compliance
    location: scripts/ai_agent_bridge/openai_proxy.py
    description: >
      422 validation errors return FastAPI's default `{detail: [...]}` shape,
      which violates OpenAI's `{error: {message, type, code}}` envelope.
  - id: healthz-fork
    severity: MEDIUM
    category: dos-surface
    location: scripts/ai_agent_bridge/openai_proxy.py
    description: >
      /healthz forks 4 subprocesses per request to probe upstream backends —
      trivial DoS amplifier.
  - id: host-flag
    severity: LOW
    category: security
    location: scripts/ai_agent_bridge/openai_proxy.py
    description: >
      --host accepts non-localhost values without requiring an explicit
      --allow-remote flag.
```

### Step 3 — initial corpus (3 cases)

Use these 3 PRs from this repo for the starter corpus. The gold findings are already in the issue tracker for each:

1. **`pr-2025-openai-proxy`** — diff from PR #2025 (commit `db04f07bed` on `codex/proxy` branch — fetch with `git fetch origin codex/proxy` then `git show db04f07bed`). Gold findings: issues #2027 (HIGH ARG_MAX), #2028 (HIGH 422 envelope), #2029 (MED /healthz fork), #2030 (LOW --host).
2. **`pr-2031-activity-schema`** — diff from PR #2031 (commit on `codex/2018-activity-schema-gate` branch). Gold finding: Grok-via-onboarding caught the missing alias handling that activity_schema gate enforces (this is what unblocked #2018). The expected finding: "writer can emit non-canonical aliases like `error_field:` for what should be `error:` — schema gate must reject."
3. **`pr-2038-m20-three-fixes`** — diff from PR #2038. Three gold findings, one per fix bundled in the PR: vesum-reviewer-anchor-leak, textbook-grounding plan reference swap, warning-quote strip in `_strip_metalinguistic`.

For each, save the actual diff to `corpus/{case_id}.diff` (output of `git show <SHA>` or `git diff <BASE>..<HEAD>`).

### Step 4 — harness shape

`scripts/audit/code_review_benchmark.py`:

```python
# CLI: ./scripts/audit/code_review_benchmark.py --corpus audit/code-review-benchmark/corpus --out audit/2026-05-17-code-review-benchmark [--family xai openai google anthropic] [--harness native_cli hermes] [--mcp with_mcp without_mcp]
```

Reuse from `_judge_eval_lib.py`:
- `PROJECT_ROOT`, `utc_timestamp`
- `aggregate` and `score_case` (parameterize over finding-matching, see step 6)
- Hermes / native_cli invocation patterns (model→family→harness routing)
- Output: `probe-results.jsonl` (one row per cell) + `REPORT.md` + `REPORT.html` matching judge_calibration_matrix's format

Differences from judge_calibration_matrix:
- Prompt is "review this diff and emit JSON `[{id, severity, category, location, description}, ...]`" instead of "classify this sentence."
- Scoring is finding-set matching (described in step 6), not single-verdict classification.

### Step 5 — review prompt

Create `audit/code-review-benchmark/prompts/review-v1.txt`. Template:

```
You are a meticulous code reviewer. Read the diff below and return findings as a JSON array.

Each finding must have: id (short kebab-case), severity (HIGH|MEDIUM|LOW), category (security|spec-compliance|dos-surface|performance|correctness|other), location (file:line), description (one paragraph).

Return ONLY a JSON array, no preamble, no postscript. If the diff is clean, return [].

--- BEGIN DIFF ---
{DIFF}
--- END DIFF ---

Context: {CONTEXT}
```

### Step 6 — scoring

For each cell (model × harness × effort × mcp), the model emits a list of findings. Gold has its own list. Match by:

1. **Severity-weighted Jaccard:** treat each finding as a (category, severity, location-file) tuple. A model finding "matches" a gold finding if all three tuple components agree (location matches at file level, not exact line — line numbers shift between diffs).
2. **Precision** = matched / model-emitted
3. **Recall** = matched / gold-total
4. **F1** = 2PR/(P+R)
5. Also report **catastrophic-miss** counts (HIGH-severity gold findings that the model didn't surface at all).

Per-cell row in REPORT.md leaderboard sorted by F1 desc, secondary sort by recall-on-HIGH.

### Step 7 — initial run

Run a SMOKE (single small cell) first to validate the pipeline end-to-end:

```bash
.venv/bin/python scripts/audit/code_review_benchmark.py \
  --corpus audit/code-review-benchmark/corpus \
  --out audit/2026-05-17-code-review-benchmark-smoke \
  --family openai --harness hermes --case pr-2031-activity-schema
```

Then full matrix run will be the orchestrator's call after PR lands.

### Step 8 — tests

`tests/audit/test_code_review_benchmark.py`:

1. CLI parses arguments correctly.
2. Corpus loader rejects malformed YAML.
3. Scorer returns F1=1.0 for perfect match.
4. Scorer returns F1=0.0 for empty model output against non-empty gold.
5. Scorer handles severity-weighted Jaccard correctly (location file match, not line).

### Step 9 — verify deterministically (#M-4 preamble)

| Claim | Tool + raw output |
|---|---|
| Harness exists | `ls -la scripts/audit/code_review_benchmark.py` |
| Corpus has 3 cases | `ls audit/code-review-benchmark/corpus/*.yaml` |
| Tests pass | `.venv/bin/pytest tests/audit/test_code_review_benchmark.py -v` final line |
| Lint clean | `.venv/bin/ruff check scripts/audit/code_review_benchmark.py tests/audit/test_code_review_benchmark.py` |
| Smoke run completes | Smoke `REPORT.md` produced; quote summary line |

The full multi-family matrix run is OUT of scope. Just the harness + corpus + smoke validation.

### Step 10 — commit, push, PR

```bash
git add scripts/audit/code_review_benchmark.py \
        scripts/audit/_judge_eval_lib.py \
        audit/code-review-benchmark/ \
        tests/audit/test_code_review_benchmark.py
.venv/bin/ruff check scripts/audit/code_review_benchmark.py tests/audit/test_code_review_benchmark.py
.venv/bin/pytest tests/audit/test_code_review_benchmark.py -v
git commit -m "feat(audit): code-review benchmark harness + 3-case corpus + smoke"
git push -u origin codex/code-review-benchmark-2026-05-16
gh pr create --title "feat(audit): code-review benchmark harness" --body "..."  # body with raw outputs from step 9
```

**DO NOT auto-merge.** Orchestrator runs the full matrix post-merge.

## Out of scope

- Full matrix run across all families × efforts × MCP (orchestrator post-merge)
- Adding more cases to the corpus beyond 3 starter cases
- Wiring the benchmark output into the routing-budget endpoint (separate PR)

## Reference

- `scripts/audit/judge_calibration_matrix.py` — template harness shape
- `scripts/audit/_judge_eval_lib.py` — shared utilities to reuse
- `audit/2026-05-17-judge-calibration-matrix/REPORT.md` — output format to mirror
- Issues #2027, #2028, #2029, #2030 — gold findings for `pr-2025-openai-proxy` case
- `docs/best-practices/hermes-usage.md` — Hermes invocation patterns
