# Codex dispatch brief — Card 1 Phase A — split immersion gate into 4 structural gates

> **Decision card:** `docs/decisions/2026-05-13-immersion-gate-tab-aware-structural.md` (ACCEPTED)
> **Phase:** A — gate code split + config schema extension. Phase B (replay calibration) follows in a separate dispatch.
> **Issues:** none yet — file 1 follow-up issue for Gate 4 (Progressive Challenge) deferral and reference it in PR body.
> **Mode:** danger
> **Worktree:** `.worktrees/dispatch/codex/immersion-gate-phase-a-2026-05-13/`
> **Base:** `origin/main` (currently `d6719cc00f`)
> **Hard timeout:** 7200s
> **Silence timeout:** 1800s
> **Effort:** high

---

## ⚠️ CRITICAL — fresh-shell behavior

Each bash block runs in a FRESH SHELL. CWD does NOT persist across blocks. Every command that uses `.venv/`, `scripts/`, or files in MAIN checkout MUST be prefixed with `cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/immersion-gate-phase-a-2026-05-13 && ...` or absolute path.

Inside the worktree, `.venv/` is gitignored. Use MAIN checkout's `.venv` via absolute path: `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python`.

---

## Goal

Replace the single `_immersion_gate()` global-% check at `scripts/build/linear_pipeline.py:4668-4711` with **three failure-mode-targeted gates** (Gates 1, 2, 3 from the Decision Card; Gate 4 deferred to a follow-up issue because it requires `plan.targets` schema fields that don't exist yet). Keep the original `_immersion_gate()` as `_advisory_immersion_pct()` — it still emits pct/min/max telemetry but ALWAYS reports `passed=true`. Hard fail/pass decisions move to the three new gates.

This is a deterministic, replay-friendly change. **No LLM-driven content evaluation; no calibration of numeric thresholds in this Phase** — placeholder thresholds only. Phase B (separate dispatch, replay-only against deployed A1 modules in `_archive/a1-backup-2026-04-08/content/`) calibrates the values.

After this Phase A merges, `python_qg` on existing bakeoff artifacts (`audit/bakeoff-2026-05-13-midday/claude/`) should report:
- A new `immersion_advisory` key with the old pct/min/max payload, `passed=true` always (telemetry only)
- New keys `l2_exposure_floor`, `long_uk_ceiling`, `component_density` each with `passed/required/observed/reason` structure
- The aggregate "immersion" gate slot in `record(...)` calls is REMOVED; the three new gates each get their own record entry. Pipeline orchestration code that consumed the old `immersion.passed` boolean needs updating — find and fix all call sites.

---

## #M-4 preamble — verifiable claims this work will produce

| Claim | Deterministic tool | Output format |
|---|---|---|
| "Old _immersion_gate renamed/demoted to advisory" | `grep -n 'def _advisory_immersion_pct\|def _immersion_gate' scripts/build/linear_pipeline.py` | quote both grep lines (old absent, new present) |
| "Three new gate functions exist" | `grep -n 'def _l2_exposure_floor_gate\|def _long_uk_ceiling_gate\|def _component_density_gate' scripts/build/linear_pipeline.py` | quote 3 grep lines |
| "IMMERSION_POLICIES schema extended" | `.venv/bin/python -c "from scripts.config import IMMERSION_POLICIES; b = IMMERSION_POLICIES['a1'][3]; print(sorted(b.keys()))"` | quote stdout |
| "Advisory pct still computed" | new `_advisory_immersion_pct()` returns dict with `pct`, `min_pct`, `max_pct`, `policy`, `passed=True` (always) | quote a test assertion + result |
| "All three new gates pass on a synthetic happy-path fixture" | a new test in `tests/test_immersion_gates.py` (new file) using a synthetic markdown that meets placeholder thresholds | quote final `pytest` summary |
| "All three new gates fail on synthetic adversarial fixtures" | each gate has at least one fixture that exercises its specific failure mode | quote final `pytest` summary |
| "Call sites updated" | `grep -n '_immersion_gate(' scripts/build/linear_pipeline.py` shows no callers (only the rename target if any) | quote grep |
| "Tests pass" | `.venv/bin/pytest tests/test_immersion_gates.py tests/test_linear_pipeline*.py -x` | quote final summary line raw |
| "Lint clean" | `.venv/bin/ruff check scripts/build/linear_pipeline.py scripts/config.py tests/test_immersion_gates.py` | quote final line raw |

Inline "I checked X" claims without quoted raw output = hallucination per #M-4. Quote.

---

## The four gates (per Decision Card §What's being proposed)

### Gate 1 — L2 Exposure Floor (ship in Phase A)

**Catches:** "essay about Ukrainian, not Ukrainian content" — module is mostly English prose with too little actual Ukrainian.

**Logic:** Count, per module text:
- UK dialogue lines (blockquoted lines containing Ukrainian script, OR JSX `<DialogueBox>` `text=...` props with Ukrainian)
- Vocab entries (lines/cells in bilingual tables with both Ukrainian and English columns, OR JSX `<VocabCard>` instances)
- UK example sentences in bulleted lists (lines starting with `- ` or `* ` containing Ukrainian script)
- UK tab-3 activities (if `activities.yaml` is available in scope, count entries; otherwise count `<inject activity_id=...>` markers — to be confirmed against actual call-site signature)

Pass when each count ≥ the band's `min_*` threshold. Fail with `reason="too_few_{dimension}"` listing the failing dimension.

**Heuristic detection rules** (per Gemini's read; if a primitive doesn't exist, add the simplest one that works):
- Blockquoted UK line: `^>\s` prefix AND contains at least one Cyrillic character matched by existing `_UK_WORD_RE`
- Bilingual table cell: a markdown table row containing both Cyrillic AND Latin tokens, parsed with a permissive splitter
- UK example bullet: line starts with `^[-*]\s` AND contains Cyrillic

### Gate 2 — Long-UK-Without-Gloss Ceiling (ship in Phase A)

**Catches:** "wall of Ukrainian at A1" — a long UK-only run without inline English support.

**Logic:** Walk the module body. Whenever a run of pure-UK tokens exceeds `max_unsupported_uk_words` AND no English support (parenthetical gloss `(...)`, an EN word in proximity within `support_proximity` tokens, or an immediately following EN sentence) is present, FAIL with `reason="long_uk_without_gloss"` and report the offending run (capped to first 5).

**Reuse** the existing `_long_ukrainian_sentences()` machinery at line 4725 as the per-sentence primitive — extend it to span across sentence boundaries when the run is unbroken by English support tokens. Don't delete the existing helper; add a new one (`_unsupported_uk_runs(text, max_unsupported, support_proximity)`) that returns a list of offending strings.

### Gate 3 — Component-Aware Language Density (ship in Phase A, minimum viable)

**Catches:** "wrong language for the wrong purpose" — e.g. a `<DialogueBox>` containing mostly English, or a `<RuleBox>` containing a wall of Ukrainian explanation at A1 early.

**Logic:** For each detectable component instance (JSX block matched by `_JSX_BLOCK_RE`), classify by tag and compute UK-token-ratio of its body. Compare against the band's component-specific expectation:
- `<DialogueBox>` ≥95% UK in its body
- `<RuleBox>` EN-dominant at A1 early (≤30% UK in body)
- `<VocabCard>` bilingual by construction — exempt from this gate (covered by Gate 1)
- Unknown components → ignored (don't fail open or closed; emit a telemetry note)

Fail with `reason="component_density_mismatch"` and list (component_tag, observed_pct, expected_range).

**Minimum-viable for Phase A:** if `<DialogueBox>` / `<RuleBox>` is the only pair you can cleanly detect from existing fixtures, ship just those two. The rule lives in `IMMERSION_POLICIES[level][band].required_components` and can be extended in Phase B without code churn.

### Gate 4 — Progressive Challenge (DEFER to follow-up)

**Catches:** "floor-gaming with dull padding."

**Defer reason:** Requires `plan.targets.grammar` and `plan.targets.vocabulary` fields that current plan schema doesn't have. File a follow-up GH issue titled `Phase A follow-up: Gate 4 (Progressive Challenge) — needs plan.targets schema`; reference it in the PR body. Do NOT extend plan schema in this PR.

---

## `IMMERSION_POLICIES` schema extension

Current band record (e.g. `scripts/config.py:152` band `a1-m01-03`):

```python
{
    "key": "a1-m01-03",
    "max_module": 3,
    "min_pct": 5,
    "max_pct": 25,
    "rule": "TARGET: 5-25% Ukrainian...",
}
```

Phase A schema (rename `min_pct`/`max_pct` to `advisory_pct_min`/`advisory_pct_max` and add structural fields):

```python
{
    "key": "a1-m01-03",
    "max_module": 3,
    # Advisory (telemetry only)
    "advisory_pct_min": 5,
    "advisory_pct_max": 25,
    # Gate 1 — L2 Exposure Floor (placeholder values; Phase B calibrates)
    "min_uk_dialogue_lines": 0,        # m01-03 are pre-dialogue letter-learning
    "min_vocab_entries": 5,
    "min_uk_example_sentences": 3,
    "min_uk_tab3_activities": 0,
    # Gate 2 — Long-UK-Without-Gloss Ceiling
    "max_unsupported_uk_words": 10,    # very tight at m01-03
    "support_proximity": 8,
    # Gate 3 — Component-Aware Language Density
    "required_components": {
        # Empty for very-early bands; later bands list e.g. {"DialogueBox": (95, 100), "RuleBox": (0, 30)}
    },
    # Writer prompt rule — adjusted for new gate model (see below)
    "rule": "...",
}
```

**The `rule` strings ALSO need updating** because they're injected into the writer prompt and currently encode the old percentage-target language ("TARGET: 5-25% Ukrainian"). Phase A scope: rewrite the `rule` strings to remove percentage-as-primary-target and substitute structural directives. Keep them roughly the same length so prompt token budget is unchanged. Suggested template per band:

```
"STRUCTURAL TARGETS (band-specific):\n"
"- At least N UK dialogue lines (band: {min_uk_dialogue_lines})\n"
"- At least N vocab entries (band: {min_vocab_entries})\n"
"- At least N UK example sentences in bulleted lists (band: {min_uk_example_sentences})\n"
"- No UK-only run longer than K words without inline English support (band: {max_unsupported_uk_words})\n"
"LANGUAGE ROLES:\n"
"- THEORY & EXPLANATION: ...(carry over from existing band rule)\n"
"- UKRAINIAN CONTENT: ...(carry over)\n"
"- TABLES: ...(carry over)\n"
"- STRUCTURAL RULE: ...(carry over, drop the percent reference)\n"
"Ukrainian sentences max 10 words."  # carry over the existing per-band sentence cap
```

You may leave the existing band-by-band language ROLES sections largely intact — they're already structural, not percentage-based. Only the explicit "TARGET: X-Y% Ukrainian" line needs replacing.

**Backward compatibility:** the `get_immersion_range(level, sequence)` and `get_immersion_policy(level, sequence)` helpers (used elsewhere) should still work. Either:
- (preferred) update both helpers to return the new keys: `get_immersion_range` returns `(advisory_pct_min, advisory_pct_max)` (existing callers see the same shape via the rename); add new `get_immersion_structural(level, sequence)` helper for the new fields.
- (alternative) keep `min_pct`/`max_pct` as aliases pointing to advisory values. Cleaner: do the rename and audit callers.

Pick the approach with fewer call-site changes. Run `grep -rn 'min_pct\|max_pct\|get_immersion_range\|get_immersion_policy' scripts/ tests/` to find callers before deciding.

---

## Call site at `linear_pipeline.py:3246`

Currently:
```python
record("immersion", _immersion_gate(module_text, plan))
```

Phase A:
```python
record("immersion_advisory", _advisory_immersion_pct(module_text, plan))
record("l2_exposure_floor", _l2_exposure_floor_gate(module_text, plan))
record("long_uk_ceiling", _long_uk_ceiling_gate(module_text, plan))
record("component_density", _component_density_gate(module_text, plan))
# Gate 4 (progressive_challenge) deferred — needs plan.targets schema
```

**Check what `record(...)` does** — if its output keys are referenced by downstream code (audit JSON shape, prompt-injection for REVISE rounds, telemetry consumers, etc.), update those consumers. `grep -rn '"immersion"' scripts/ tests/` to find readers. The `immersion.passed` boolean was load-bearing for verdict aggregation — the aggregator needs to AND the three new gates' passed booleans into the "immersion" hard-pass decision OR consume them individually.

**The aggregator question:** the safest shape is to have the orchestration code treat any of `l2_exposure_floor`, `long_uk_ceiling`, `component_density` as HARD-fail dimensions individually, so each becomes its own line in the verdict report. If a single aggregated `immersion.passed` boolean is required by some downstream consumer (e.g. an HTML dashboard or a Decision Card replay script), compute it as `all([l2_exposure_floor.passed, long_uk_ceiling.passed, component_density.passed])` at the aggregator level, NOT inside each gate function.

---

## Test plan (new file: `tests/test_immersion_gates.py`)

Add at minimum:

1. **`test_advisory_pct_always_passes`** — synthesize a module text with pct=0% UK and confirm `_advisory_immersion_pct()` returns `passed=True` AND emits correct pct/min/max telemetry.
2. **`test_l2_exposure_floor_pass`** — synthesize a module meeting Gate 1 placeholders → `passed=True`.
3. **`test_l2_exposure_floor_fail_dialogue_lines`** — synthesize a module with zero UK dialogue lines when band requires ≥3 → `passed=False`, reason cites `too_few_uk_dialogue_lines`.
4. **`test_l2_exposure_floor_fail_vocab_entries`** — same shape for vocab.
5. **`test_long_uk_ceiling_pass`** — a normal A1 module with parenthetical glosses → `passed=True`.
6. **`test_long_uk_ceiling_fail`** — synthesize 30+ Cyrillic tokens in a row with no Latin character → `passed=False`, reason cites `long_uk_without_gloss`, offending run captured (truncated).
7. **`test_component_density_dialoguebox_pass`** — `<DialogueBox text="Привіт!" .../>` → component density passes.
8. **`test_component_density_rulebox_fail_at_a1_early`** — `<RuleBox>` containing 80% Cyrillic at band `a1-m01-03` → fails (because A1 early expects EN-dominant rule prose).
9. **`test_immersion_policies_schema`** — for every (level, band) tuple in `IMMERSION_POLICIES`, assert the new schema keys exist; assert `advisory_pct_min` and `advisory_pct_max` are int; assert all `min_*` fields are int; assert `required_components` is a dict.
10. **`test_old_immersion_gate_removed`** — `grep`-style assertion that `_immersion_gate` is no longer defined OR that the rename happened; pick one and stick with it.

Also update existing tests that reference `min_pct`/`max_pct` or the old `_immersion_gate` directly. `grep -rn '_immersion_gate\|min_pct\|max_pct' tests/` first.

---

## Numbered steps (mandatory checklist)

1. **Worktree setup:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian && \
   git worktree add -b codex/immersion-gate-phase-a-2026-05-13 .worktrees/dispatch/codex/immersion-gate-phase-a-2026-05-13 origin/main
   ```

2. **Read first, change second.** Read these files end-to-end before editing:
   - `scripts/config.py:140-260` (IMMERSION_POLICIES + helpers)
   - `scripts/build/linear_pipeline.py:4668-4731` (existing gate + helpers)
   - `scripts/build/linear_pipeline.py:3240-3260` (call site)
   - `docs/decisions/2026-05-13-immersion-gate-tab-aware-structural.md` (the accepted card)
   - any existing immersion gate test files (`grep -l immersion tests/`)

   Run `grep -rn 'get_immersion_range\|get_immersion_policy\|_immersion_gate(\|"immersion"\|min_pct\|max_pct' scripts/ tests/` and document the full caller graph in a scratch note. Don't start editing until you understand every consumer.

3. **File-level work** — implement the three new gates + advisory pct + schema extension. Aim for ~150-300 LOC of new code total; rename + minor delta in callers. Each gate function should follow the same shape as existing gates (return dict with `passed`, plus diagnostic fields).

4. **Test suite:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/immersion-gate-phase-a-2026-05-13 && \
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/pytest tests/test_immersion_gates.py tests/test_linear_pipeline*.py -x
   ```
   Quote final summary line raw.

5. **Ruff:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/immersion-gate-phase-a-2026-05-13 && \
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/ruff check scripts/build/linear_pipeline.py scripts/config.py tests/test_immersion_gates.py
   ```
   Quote final line raw.

6. **Replay sanity** — for the claude bakeoff artifact at `audit/bakeoff-2026-05-13-midday/claude/module.md`, write a small standalone driver that calls the four functions directly on the file (no full pipeline). Capture the four gates' JSON output. Include before/after comparison in the PR body, even though Phase A doesn't claim threshold calibration is correct yet — this is a sanity check that the gates EXECUTE on real content, not a verdict.

7. **File the Gate 4 follow-up issue:**
   ```bash
   gh issue create --title "Phase A follow-up: Gate 4 (Progressive Challenge) — needs plan.targets schema" \
     --body "Deferred from PR opened by this task. Gate 4 of Decision Card 2026-05-13-immersion-gate-tab-aware-structural requires plan.targets.grammar and plan.targets.vocabulary fields. Plan schema doesn't currently encode these. Track plan schema extension + Gate 4 ship here."
   ```
   Quote the returned URL in the PR body.

8. **Commit** with conventional message: `feat(linear_pipeline): split immersion gate into 3 structural gates (Card 1 Phase A)`. One commit, all changes together (gates + tests + config schema). Body should reference the Decision Card and the deferred Gate 4 issue.

9. **Push:** `git push -u origin codex/immersion-gate-phase-a-2026-05-13`.

10. **Open PR** via `gh pr create`. Body must include:
    - Link to `docs/decisions/2026-05-13-immersion-gate-tab-aware-structural.md`
    - The four new gates' before/after JSON on the claude bakeoff artifact
    - Confirmation that placeholder thresholds are explicitly labeled "Phase B calibrates"
    - Link to the Gate 4 follow-up issue
    - Confirmation: `_immersion_gate` removed; `_advisory_immersion_pct` is the rename; three new gate functions exist

11. **DO NOT auto-merge.** Hand back for orchestrator review.

---

## What blocks the merge

- Tests failing.
- Ruff failing.
- Existing immersion-gate callers broken without being updated.
- Schema extension making `IMMERSION_POLICIES` import-time invalid (e.g. type mismatches).
- Any of the three new gates referencing `plan.targets` (that's Gate 4 territory; defer).
- Removing the `_long_ukrainian_sentences()` helper — Gate 2 extends it, doesn't replace it.
- Hard-coding numeric thresholds anywhere outside `scripts/config.py:IMMERSION_POLICIES` (SSOT violation).
- Phase A claiming threshold values are calibrated — they're explicitly placeholders; Phase B calibrates.

---

## Pre-submit checklist (per AGENTS.md:11-26)

- [ ] `.python-version` unchanged
- [ ] `.yamllint` and `.markdownlint.json` unchanged
- [ ] No `status/*.json` or `audit/*-review.md` files in diff
- [ ] No `sys.executable` — use `.venv/bin/python`
- [ ] No `@pytest.mark.skip` with empty `pass` bodies
- [ ] No assertion-weakening
- [ ] Every changed file directly related to gate split + schema extension
- [ ] Total files changed < 20
- [ ] No `NameError` / `KeyError` / `ImportError` on import

---

## Anti-pattern catalog (specific to this task)

- ❌ Calibrating threshold values empirically inside this PR (Phase B's job).
- ❌ Extending plan schema to fit Gate 4 (separate follow-up issue).
- ❌ Removing the old `_immersion_gate` without checking call sites — find all callers first.
- ❌ Inlining a "global immersion pct" pass/fail anywhere downstream. The advisory pct is telemetry only; no consumer should branch on it.
- ❌ Writing test fixtures that hit MCP or network. All fixtures are inline strings.
- ❌ Reformatting unrelated regions of `linear_pipeline.py` while you're in there. Keep the diff tight.

---

## Related

- Decision card (ACCEPTED): `docs/decisions/2026-05-13-immersion-gate-tab-aware-structural.md`
- Predecessor handoff: `docs/session-state/2026-05-13-evening-immersion-reframe-and-writer-split-brief.md`
- Lesson Contract authority: `docs/lesson-contract.md` §4.6
- Pipeline gate trio (just-merged, related but separate): PR #1913 / `docs/dispatch-briefs/2026-05-13-pipeline-gate-trio.md`
- Held PR #1909 (writer-prompt-tune) — depends on this; revisit after merge.
- Held PR #1915 (Track B research artifacts) — depends on this; re-evaluate YELLOW verdict after new gates land.
- Phase B follow-up brief: `docs/dispatch-briefs/2026-05-13-immersion-gate-phase-b.md` (replay-only, queued for after Phase A merges)
