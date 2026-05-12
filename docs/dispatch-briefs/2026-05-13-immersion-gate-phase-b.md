# Codex dispatch brief — Card 1 Phase B — empirical threshold calibration (replay-only, no LLM cost)

> **Decision card:** `docs/decisions/2026-05-13-immersion-gate-tab-aware-structural.md` (ACCEPTED)
> **Phase:** B — empirical calibration via replay against deployed A1 corpus + bakeoff artifacts. NO LLM-generated content; deterministic gates run against existing files.
> **Status:** **DO NOT FIRE until Phase A PR merges to main.** Phase A is dispatched separately and ships the gate code; Phase B tunes the threshold numbers Phase A defaults to placeholders.
> **Dependency:** Phase A's gate functions must be importable from `scripts.build.linear_pipeline` and `IMMERSION_POLICIES` must have the new schema fields.
> **Issues:** create one new issue: "Phase B calibration report — immersion gate tab-aware structural" and reference it from the PR body.
> **Mode:** danger
> **Worktree:** `.worktrees/dispatch/codex/immersion-gate-phase-b-2026-05-13/`
> **Base:** `origin/main` (whatever main is at fire time, post-Phase-A)
> **Hard timeout:** 7200s
> **Silence timeout:** 1800s
> **Effort:** high

---

## ⚠️ CRITICAL — fresh-shell behavior

Each bash block runs in a FRESH SHELL. CWD does NOT persist. Prefix every command with `cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/immersion-gate-phase-b-2026-05-13 && ...` or use absolute paths.

Inside worktree, `.venv/` is gitignored. Use `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python`.

---

## Goal

Run Phase A's three new gates (`_l2_exposure_floor_gate`, `_long_uk_ceiling_gate`, `_component_density_gate`) against:

1. **All 55 deployed A1 modules** in `curriculum/l2-uk-en/_archive/a1-backup-2026-04-08/content/` (verified: 55 `*.md` files at that path; deployed-A1 single-page MD corpus — read 5 of these in the 2026-05-13 evening session and characterized them as following correct structural patterns; this run validates that empirically across the full set)
2. **Today's bakeoff artifacts** at `audit/bakeoff-2026-05-13-midday/{claude,codex}/module.md`
3. **The just-built `a1/my-morning` V7 module** (if it exists at `curriculum/l2-uk-en/a1/my-morning/module.md`)

For each (band × gate × module) triple, capture pass/fail + observed values. Aggregate per-band stats. Recommend threshold values that minimize false-fail on the deployed corpus (the empirical baseline) while still catching today's bakeoff failure modes.

**No LLM cost.** All gates are deterministic Python; the only work is the run + analysis.

Output: a calibration report at `audit/immersion-gate-calibration-2026-05-13/REPORT.md` (or `.html` per #M-2 since it's ai→human), updated `IMMERSION_POLICIES` band threshold values, and PR opened with both.

---

## #M-4 preamble — verifiable claims this work will produce

| Claim | Deterministic tool | Output format |
|---|---|---|
| "All 55 deployed A1 modules read & gated" | `ls curriculum/l2-uk-en/_archive/a1-backup-2026-04-08/content/*.md \| wc -l` (cross-check count) + gate-run log per module | quote `ls` count + show summary table per band |
| "Today's bakeoff artifacts gated" | `ls audit/bakeoff-2026-05-13-midday/{claude,codex}/module.md` + gate-run log | quote `ls` output + show gate JSON per writer |
| "Threshold values updated in IMMERSION_POLICIES" | `git diff scripts/config.py` shows per-band threshold changes | quote a unified diff snippet per band |
| "Deployed corpus pass rate ≥95% under tuned thresholds" | the per-band pass-rate aggregation logic | quote the aggregation output table |
| "Bakeoff failure modes still caught" | gate-run on bakeoff artifact returns `passed=false` for the appropriate gate(s) | quote the relevant gate JSON |
| "Tests pass" | `.venv/bin/pytest tests/test_immersion_gates.py` | quote final summary line |
| "Lint clean" | `.venv/bin/ruff check scripts/config.py` | quote final line |

Inline "I checked X" claims without quoted raw output = hallucination per #M-4. Quote.

---

## Approach

### Step 1 — verify Phase A landed

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian && \
git log origin/main --oneline -10 | grep -i 'immersion-gate\|Phase A\|Card 1'
```

If no Phase A merge commit appears, ABORT — Phase A hasn't shipped yet. Print `GOAL_ABORT reason="phase_a_not_merged" next_action="wait for Phase A PR merge then re-fire"` and exit.

Else verify import works:

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/immersion-gate-phase-b-2026-05-13 && \
/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python -c "
from scripts.build.linear_pipeline import _l2_exposure_floor_gate, _long_uk_ceiling_gate, _component_density_gate, _advisory_immersion_pct
from scripts.config import IMMERSION_POLICIES
print('OK: imports work; a1 band count =', len(IMMERSION_POLICIES['a1']))
"
```

Quote stdout. If ImportError, ABORT.

### Step 2 — write a replay driver

Create `scripts/audit/immersion_gate_calibration.py` (new file). It:

1. Walks `curriculum/l2-uk-en/_archive/a1-backup-2026-04-08/content/*.md` (verified: 55 files at that path; sibling dirs at same parent are `activities/`, `vocabulary/`, `orchestration/`, `research/`, `status/` — only `content/` is the module-MD corpus)
2. For each `.md`, parses out level + sequence (from frontmatter OR from filename pattern — verify what's stable)
3. Constructs a `plan` dict with `level=a1`, `sequence=N`
4. Calls each of the three gates + advisory_pct against the body text
5. Records (filename, band, gate_name, passed, observed_dict) → CSV or JSONL
6. Also runs against `audit/bakeoff-2026-05-13-midday/{claude,codex}/module.md` (level a1, sequence 17 for my-morning — verify against `curriculum/l2-uk-en/curriculum.yaml`)
7. Emits two outputs:
   - `audit/immersion-gate-calibration-2026-05-13/raw.jsonl` — one record per (module, gate)
   - `audit/immersion-gate-calibration-2026-05-13/REPORT.md` — aggregated stats per band

### Step 3 — run the driver

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/immersion-gate-phase-b-2026-05-13 && \
/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python scripts/audit/immersion_gate_calibration.py
```

Quote the script's final stdout summary.

### Step 4 — analyze + tune thresholds

For each band (`a1-m01-03`, `a1-m04-06`, `a1-m07-14`, `a1-m15-24`, `a1-m25-34`, plus any a2 bands if present), examine the observed-value distribution across deployed modules in that band:

- **Gate 1 (L2 Exposure Floor)** — for each `min_*` field, plot the distribution of observed counts across deployed modules. Set the threshold at the 10th percentile (allow some headroom; we don't want to false-fail 90% of deployed content). If 10th percentile is below the Phase A placeholder, keep the placeholder (deployed corpus is on the right side of the bar). If above, lower toward 10th percentile.
- **Gate 2 (Long-UK Ceiling)** — observe the max-unsupported-run distribution. Place `max_unsupported_uk_words` at the 90th percentile or just above. The cap should accept normal-deployed content while still catching adversarial wall-of-UK.
- **Gate 3 (Component Density)** — observe per-component density distributions. The expected ranges should accommodate observed deployed content. Document any deployed components that fall outside the placeholder ranges — they need either threshold adjustment or human review.

**Calibration target:** zero false-fails on deployed A1 modules. The deployed modules are the empirical baseline of "what good A1 content looks like" until proven otherwise. If a gate would false-fail a deployed module, that's evidence the gate is wrong OR the deployed module has a real defect — flag both possibilities in the report.

**Cross-check:** today's bakeoff failure modes should still be caught by the new thresholds:
- Bakeoff claude's `vesum_verified` issue, `textbook_grounding` issue, and `immersion.pct=25.4%` cap were the failure modes the original gate trio (PR #1913) addressed. The structural gates should ALSO flag the underlying problems (the "wall of UK teaching prose" pattern showed up as 3 long-sentence violations — Gate 2 should catch this; not exposed if Phase A's placeholders are too lenient).

### Step 5 — write the report

`audit/immersion-gate-calibration-2026-05-13/REPORT.html` (HTML per #M-2, ai→human):

Structure:
1. Executive summary — proposed threshold changes per band, sized 5-line max
2. Methodology — what was gated, against what corpus
3. Per-band tables — observed distributions per gate per field; proposed value; rationale
4. False-fail analysis — any deployed module that would still fail under tuned thresholds; root-cause for each
5. Bakeoff-failure-mode validation — does the tuned set still catch today's failure modes?
6. Recommendations — accept thresholds + ship Phase C (writer prompt rewrite); OR loop back if calibration is inconclusive

Keep it HTML, ai→human readable.

### Step 6 — apply threshold changes + tests

Update `scripts/config.py:IMMERSION_POLICIES` with the calibrated values. Add a comment block above each band's structural fields citing the calibration report path.

Update or add test fixtures so the placeholder tests in `tests/test_immersion_gates.py` still pass with the new values.

Run:
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/immersion-gate-phase-b-2026-05-13 && \
/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/pytest tests/test_immersion_gates.py -x && \
/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/ruff check scripts/config.py scripts/audit/immersion_gate_calibration.py
```

Quote final summary lines.

### Step 7 — commit + PR

```bash
git add scripts/config.py scripts/audit/immersion_gate_calibration.py audit/immersion-gate-calibration-2026-05-13/ tests/test_immersion_gates.py
git commit -m "feat(immersion-gates): Phase B threshold calibration (Card 1)" -m "..." # full conventional body
git push -u origin codex/immersion-gate-phase-b-2026-05-13
gh pr create ...
```

PR body must include:
- Link to Phase A PR (merged) and to Decision Card
- Calibration REPORT excerpt — at minimum the executive summary
- Statement: "Deployed A1 corpus pass rate under tuned thresholds: N/55 modules pass all three structural gates"
- Statement on bakeoff failure-mode catch rate
- Recommendation (proceed to Phase C / loop back / amend)

**DO NOT auto-merge.** Hand back for orchestrator review.

---

## What blocks the merge

- Phase A not yet on `main` (Phase B can't even import — abort if so).
- Deployed corpus pass rate < 90% under any reasonable threshold combination — that's evidence the gates themselves are wrong, not just the numbers. Surface to orchestrator, don't ship.
- Replay driver loses or skips modules silently — verify counts at every step.
- Calibration report doesn't include false-fail analysis.
- Threshold changes that contradict the Decision Card's stated approach (e.g. re-introducing percentage-based hard fail).
- Editing Phase A's gate function bodies. Phase B's surface is `IMMERSION_POLICIES` only.

---

## Pre-submit checklist (per AGENTS.md:11-26)

- [ ] `.python-version` unchanged
- [ ] `.yamllint` and `.markdownlint.json` unchanged
- [ ] No `status/*.json` or `audit/*-review.md` files in diff (calibration report goes under `audit/immersion-gate-calibration-2026-05-13/` which IS the expected artifact location)
- [ ] No `sys.executable` — use `.venv/bin/python`
- [ ] No `@pytest.mark.skip` with empty `pass` bodies
- [ ] Threshold changes are all in `scripts/config.py:IMMERSION_POLICIES` (SSOT)
- [ ] Total files changed < 20

---

## Related

- Decision card: `docs/decisions/2026-05-13-immersion-gate-tab-aware-structural.md`
- Phase A brief (predecessor): `docs/dispatch-briefs/2026-05-13-immersion-gate-phase-a.md`
- Held PRs awaiting Phase B verdict: #1909 (writer-prompt-tune), #1915 (Track B research artifacts)
- Strategic Q answered by this Phase: "Is the V7 rebuild for A1 even necessary, or do deployed A1 modules pass new gates?" — answer surfaces in the calibration report
