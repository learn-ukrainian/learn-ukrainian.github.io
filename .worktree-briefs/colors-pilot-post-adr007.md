# Runbook — Colors 1-module pilot (post-ADR-007)

> **Not a dispatch brief.** This is the runbook for the colors pilot fire
> once ADR-007 lands. The pilot is the canary for the entire new stack:
> reviewer-as-fixer parity, per-dim MIN wiki review, post-processor
> mutation invariant, unified thresholds, and the claude-tools writer at
> `claude-opus-4-7 xhigh`. If the pilot green, A1 full rebuild follows.
>
> **Fire-er**: user or main-session Claude, not a dispatch.

---

## 0. Pre-flight: GATE CHECKS (all must pass)

Every check below must return the indicated state. **If any fails, do
not fire the pilot.** The whole point is that the pilot tests the *new*
stack; any stale path invalidates the test.

### 0.1 EPIC #1451 Phase 2-A merged (threshold source of truth)

```bash
gh pr view 1498 --json state,mergedAt
# expect: state=MERGED, mergedAt set
```

### 0.2 ADR-007 PR wave fully merged

ADR-007 comprises PR-A (kill tiers M1/M2/M3), PR-B (kill `<rewrite-block>`
protocol M4), PR-C (kill WORD_BUDGET auto-heal M5), PR-D (kill shared
rewrite infrastructure M6), PR-E (migrate convergence terminal to
`plan_revision_request`), PR-F (invariant test: grep for removed names
returns zero). Expect dispatch labels `adr007:pr-a`, `adr007:pr-b`, etc.

```bash
gh pr list --state merged --search 'adr007 in:title' --limit 10
# expect: all of PR-A, PR-B, PR-C, PR-D, PR-E, PR-F present and merged
```

### 0.3 Other critical-path PRs merged

```bash
gh pr view <N> --json state  # for each of:
#   - #1462 (post-processor mutation invariant)
#   - #1455 (wiki review per-dim MIN)
# expect: state=MERGED on both
```

### 0.4 Rewrite strategies are CODE-LEVEL gone

This is ADR-007 PR-F's invariant, but reverify before firing. Any match
here means the pilot would exercise a dead path that technically still
exists.

```bash
grep -RE 'section_rewrite|full_rewrite|writer_swap|<rewrite-block' \
    scripts/build/ tests/ | grep -v 'test_.*invariant\|_historical'
# expect: ZERO matches (or only the invariant test file itself matching
#         its own forbidden-pattern list)
```

### 0.5 Fresh main + rebase evidence

```bash
git fetch origin main
git log --oneline origin/main | head -10
# expect: the ADR-007 PR-A/B/C/D/E/F commits visible + #1462 + #1455 + #1498
```

### 0.6 Wiki corpus available for colors

```bash
ls wiki/pedagogy/a1/colors* 2>&1
# Colors pilot pulls from A1 wiki corpus for source grounding.
# If colors has no pedagogy brief yet, either ingest one first or
# accept that the pilot exercises chunk-level retrieval only.
```

### 0.7 State reset (MANDATORY — stale state would mask regressions)

```bash
.venv/bin/python scripts/build/v6_build.py a1 10 --force
# --force wipes lesson .md, activities, vocab, reviews, audit, status,
# orchestration state + prompts + dispatch, knowledge packet, and
# published MDX. Preserves plan YAML + discovery + code/config.
#
# DO NOT SKIP THIS STEP. The colors module has smoke-build residue from
# the 2026-04-23 pre-ADR R1 REJECT; any resumed state would mix old and
# new pipelines.
```

---

## 1. Expected writer/reviewer config

| Setting | Value | Why |
|---|---|---|
| Writer agent | `claude-tools` | Per MEMORY REVIEWER POLICY: Opus 4.7 is least-affected by March-April regression; decolonization / factual / dim-naturalness wins |
| Writer model | `claude-opus-4-7` | Per #1474 postmortem must-change |
| Writer effort | `xhigh` | Per #1474 — `high` underperforms prior versions on Opus 4.7; xhigh restores parity |
| Reviewer | `codex-tools` | Per MEMORY REVIEWER POLICY: Codex primary pipeline reviewer; Gemini self-review off |
| Review threshold | default (from #1498 unified table) | Do not override |
| CLI | Claude CLI ≥ 2.1.116, Codex CLI ≥ 0.122.0 | Per #1472 gate + local Codex upgrade |

Verify CLI versions before firing:

```bash
claude --version  # expect >= 2.1.116
codex --version   # expect >= 0.122.0
```

---

## 2. The command

```bash
.venv/bin/python scripts/build/v6_build.py a1 10 \
    --writer claude-tools --reviewer codex-tools
```

Notes:
- Do not pass `--writer-model` or `--writer-effort`: the `#1472` / #1474
  wiring routes `claude-tools` to `claude-opus-4-7 xhigh` automatically.
  Passing them re-opens the silent-default inheritance path.
- Do not pass `--review-threshold`. #1498 unified the source of truth;
  the default is correct by construction.
- Do not pass `--resume`. Pilot must start from `--force`-cleaned state.
- Do not pass `--step all`. Default is end-to-end; explicit `all`
  re-runs all phases (expensive) instead of resuming.

---

## 3. Monitor the build

Per MEMORY #0B — never poll. Use the `Monitor` tool:

```
Monitor(
    command=".venv/bin/python -u scripts/build/v6_build.py a1 10 \
        --writer claude-tools --reviewer codex-tools 2>&1 \
        | grep --line-buffered '^{\"event\"'",
    description="colors pilot events",
    persistent=True,
    timeout_ms=3600000
)
```

Each JSONL line becomes one notification. Key events:
- `module_start` — build begins
- `phase_done {phase: ...}` — each phase completion
- `review_score {score: X, dim: ...}` — per-dim reviewer scores
- `module_done {score: X}` — terminal success
- `module_failed {reason: ...}` — terminal failure
- `plan_revision_request` — new post-ADR-007 terminal (see §5)

Expected wall time on green path: **40–55 minutes** (writer ~8m, review
~10m, fixes + re-review ~10m, activities + exercises ~10m, audit ~2m,
publish ~3m).

---

## 4. Success criteria for "pilot green"

All of the following must hold on the terminal `module_done`:

1. **Overall MIN score ≥ 8.0** on the codex-tools reviewer across all
   9 dims. `8.0` is the threshold from #1498's unified table; do not
   accept partial pass.
2. **Naturalness dim ≥ 9.0** per the A1 level config (`config/levels/a1.yaml`).
   This is the decolonization-sensitive dim; pilot must not regress.
3. **Zero rewrite-class state transitions** in orchestration state:
   ```bash
   grep -E 'full_rewrite|section_rewrite|writer_swap|rewrite-block' \
       curriculum/l2-uk-en/a1/orchestration/colors/state.json
   # expect: ZERO matches
   ```
4. **No `WORD_BUDGET` auto-heal events** in state (#1462 + ADR-007 PR-C
   killed that path; any occurrence is a smoke-test fail).
5. **All audit gates green**:
   ```bash
   .venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/a1/colors.md
   # expect: exit 0, all gates PASS
   ```
6. **Status file shows `status: "locked"`**:
   ```bash
   cat curriculum/l2-uk-en/a1/status/colors.json
   # expect: status = "locked", audit all green, review score recorded
   ```
7. **Citation invariant passes on the new module**:
   ```bash
   .venv/bin/pytest tests/test_citation_resolution_invariant.py -x -v
   # expect: no new xfails from a1/colors.md
   ```

If all seven hold: **pilot green. Proceed to §7.**

---

## 5. Failure modes + remediation

### 5.1 MIN dim < 8 on codex-tools reviewer

- The reviewer emitted `<fixes>` for low-scoring dims. Pipeline applied
  them, re-reviewed, still below threshold.
- Under ADR-007, **there is no M2/M3/M4/M5 escalation.** The module
  either healed via `<fixes>` or hit `plan_revision_request` terminal.
- If `plan_revision_request`: the plan or writer prompt is under-specified
  for the dim that failed. **Do not re-run the pilot.** Read the failed
  dim's fixes trail (`curriculum/l2-uk-en/a1/orchestration/colors/review-structured-r*.yaml`),
  identify which of (plan / writer prompt / source grounding) needs
  revision, open a new issue, halt pilot until fixed.

### 5.2 `WORD_BUDGET` ERROR on contract compliance

- ADR-007 PR-C removed auto-heal. WORD_BUDGET under-shortfall either:
  a. **Fixed via reviewer `<fixes> insert_after:`** — this is the
     allowed repair path. Re-review should clear it.
  b. **Hit `budget_exhausted` terminal** — the `<fixes>` insert_after
     attempt failed (e.g. structural mismatch). Halt pilot, diagnose.
- **Do not lower the budget** to make the pilot pass. Thresholds are
  non-negotiable (MEMORY #1).

### 5.3 Non-terminal hang (no event for > 5 min)

- Likely CLI subprocess wedged (known failure class for Codex CLI
  under specific prompt-shape triggers).
- Check `~/.codex/sessions/2026/04/24/rollout-*.jsonl` for the most
  recent dispatch; tail its function_call events.
- If wedged: SIGINT the pilot, inspect the stuck prompt, file issue,
  halt.

### 5.4 Dispatch agent version mismatch

- If CLI version regressed mid-session, the #1472 gate fires a hard
  error early. Upgrade CLI, re-fire.

### 5.5 Audit gate regression

- All 7 audit gates must pass. If one fails post-build, this is
  diagnostic signal for the specific quality dim. Read the gate output,
  identify root cause, halt pilot. Do NOT pass `--force-publish`.

---

## 6. Post-pilot: artifact capture

Whether green or red, capture evidence before moving on:

```bash
# Snapshot for the session-state archive
mkdir -p docs/session-state/colors-pilot-$(date +%Y-%m-%d)
cp curriculum/l2-uk-en/a1/colors.md \
   curriculum/l2-uk-en/a1/orchestration/colors/state.json \
   curriculum/l2-uk-en/a1/orchestration/colors/review-structured-*.yaml \
   curriculum/l2-uk-en/a1/audit/colors.json \
   curriculum/l2-uk-en/a1/status/colors.json \
   docs/session-state/colors-pilot-$(date +%Y-%m-%d)/

# Commit the evidence regardless of outcome — future agents
# need both green and red artifacts for reference.
git add docs/session-state/colors-pilot-$(date +%Y-%m-%d)/
git commit -m "docs(pilot): colors post-ADR-007 pilot evidence snapshot"
```

---

## 7. If pilot green → A1 full rebuild

The next runbook is the A1 full rebuild. Do NOT fire it inline from
this session; it is a 40h+ job requiring 2+ days wall time.

Next brief to write (not yet drafted): `.worktree-briefs/a1-full-rebuild-post-colors.md`
- Command template: `.venv/bin/python scripts/build/v6_build.py a1 1 --range 55 --resume`
- Pre-reqs: colors pilot green + Krisztian go-ahead
- Monitoring: Monitor tool, batch_done events per module
- Mid-run pause plan: SIGINT → `--resume` from last module

**Recommended next action after pilot green**: announce the result,
capture evidence, then ask the user before firing A1 batch. Batch builds
are overnight-class work and need explicit go-ahead (not assumed from a
green pilot).

## 8. If pilot red → root-cause diagnosis

- Halt. No re-fire until root cause is understood.
- Open a dispatch brief targeted at the specific failure class.
- Do NOT treat "pilot red" as a reason to lower thresholds, revive
  rewrite strategies, or re-enable WORD_BUDGET auto-heal. The whole
  point of ADR-007 is that pipeline-level heuristics mask content
  problems; pilot-red is the honest signal to fix the content.

---

*Runbook drafted 2026-04-23 late evening. Version-frozen at ADR-007*
*approval; update this file if the threshold table, writer default, or*
*event schema changes. Canonical gate list is §0 — if you edit it,*
*every other section downstream needs to reflect the change.*
