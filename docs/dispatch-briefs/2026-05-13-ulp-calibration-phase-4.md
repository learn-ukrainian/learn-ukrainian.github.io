---
date: 2026-05-13
agent: codex
mode: danger
worktree: true
effort: high
task_id: ulp-calibration-phase-4-2026-05-13
hard_timeout: 7200
silence_timeout: 1800
references:
  - docs/decisions/2026-05-13-ulp-derived-student-aware-immersion.md  # Phase 4 spec
  - scripts/config.py  # placeholders + flag
  - scripts/build/learner_immersion.py  # existing freq-map infra
  - scripts/audit/checks/recycle_cadence.py  # gate to calibrate
  - docs/references/private/ULP*.txt  # source corpus (6 seasons, gitignored)
  - AGENTS.md  # pre-submit checklist (lines 11-26 verbatim)
---

# Dispatch — ULP-derived immersion calibration replay (Phase 4)

## Goal

Calibrate the `_ULP_VOCAB_KNEE_PER_BAND` + `_RECYCLE_CADENCE_DEFAULTS` constants in `scripts/config.py` from empirical lemma-frequency analysis of the ULP S1–S6 corpus, emit a calibration report at `audit/ulp-calibration-2026-05-13/`, and flip the `USE_ULP_IMMERSION_DERIVATION` feature flag from `False` → `True` once Phase 4 acceptance criteria are met. Phase 4 closure per `docs/decisions/2026-05-13-ulp-derived-student-aware-immersion.md` § "Implementation phases" → Phase 4.

This is mechanical empirical work: read corpus → build distribution → fit constants → write report → flip flag. The DESIGN is already decided (Decision Card ACCEPTED 2026-05-13); your job is the empirical calibration only.

## Background

PR #1939 (PR1) and PR #1943 (PR2) shipped the structure. `compute_immersion_band(track, module_num, learner_state)` already routes to ULP-derived logic when the flag is True, but the calibration constants are placeholders. Without Phase 4, flipping the flag is unsafe (current placeholders are stub values, not empirically grounded).

The Decision Card sets Phase 4's acceptance criterion: "tune `_ULP_VOCAB_KNEE_PER_BAND` constants so the derived bands match (within tolerance) the structural distribution observed in ULP S1→S6." Translation: when `USE_ULP_IMMERSION_DERIVATION=True` is set and `compute_immersion_band` runs on a hypothetical learner-state derived from ULP-style cumulative-vocab progression, the resulting band shape must reproduce ULP's empirical UK-density curve.

## Inputs available

| Resource | Path / Reference |
|---|---|
| ULP corpus (TXT-extracted) | `docs/references/private/ULP 1-00 Lesson Notes (all in one file) (2023).txt` through `ULP 6-00`. Sizes: 588KB / 903KB / 1.3MB / 1.9MB / 2.1MB / 2.4MB. Gitignored. |
| Companion vocab corpora | `1000-Ukrainian-Words-2.0-…txt`, `500+ Ukrainian Verbs - …txt` (same dir). |
| Lemma-frequency map infra | `scripts/build/learner_immersion.py` (project-modules-aware; adapt or write a parallel ULP extractor) |
| Current placeholder constants | `scripts/config.py:605` `_ULP_VOCAB_KNEE_PER_BAND` + `:629` `_RECYCLE_CADENCE_DEFAULTS` (both flagged `PHASE_4_PLACEHOLDER`) |
| Feature flag | `scripts/config.py:155` `USE_ULP_IMMERSION_DERIVATION: bool = False` |
| Calibration audit format precedent | `audit/immersion-gate-calibration-2026-05-13/` (`raw.jsonl` + `REPORT.html`) |
| VESUM lemmatization | `mcp__sources__verify_words` for batch lemma resolution; `mcp__sources__check_modern_form` for cleanup |
| Existing audit gate to verify against | `scripts/audit/checks/recycle_cadence.py` (currently WARN at A1) |

## Empirical task (method is yours; below is shape, not script)

1. **Build a per-lesson lemma-frequency table** from the 6 ULP TXT corpora. Per ULP lesson (the corpus has clear lesson boundaries; use the in-text "Lesson N" delimiters): record `(season, lesson_num, all_lemmas_introduced, all_lemmas_repeated_from_earlier, total_uk_token_count, total_en_token_count, uk_density_pct)`. Lemma resolution via VESUM (`mcp__sources__verify_words`); rejected/non-lemma forms surface in the report but don't count toward density.
2. **Choose a CEFR-family mapping for ULP seasons.** ULP S1 is explicitly beginner; S6 is upper. The mapping isn't documented by ULP directly — derive it empirically (e.g. cumulative-vocab-count quantiles, or per-season UK-density curve shape). Document your reasoning in the report. The mapping decides which `_ULP_VOCAB_KNEE_PER_BAND` family gets which constants.
3. **Identify the "knee"** for each CEFR family: the cumulative-vocab-count at which the empirical band changes shape (advisory_pct_min/max transitions). Fit `_ULP_VOCAB_KNEE_PER_BAND[family]` from the data, not from preconception.
4. **Recycle cadence**: from the per-lesson lemma table, compute the empirical distribution of "how often a lemma re-surfaces N lessons after first introduction." Fit `_RECYCLE_CADENCE_DEFAULTS` from that distribution (cadence = mean / median revisit lag; floor = minimum revisit count to consider "consolidated").
5. **Backward-compatibility check.** When `USE_ULP_IMMERSION_DERIVATION=True` is set, the bands for `a1` modules m01–m03 must match (within ±2 percentage points on advisory_pct_min/max) the current static `IMMERSION_POLICIES["a1-m01-03"]`. We've built one A1 module (`my-morning`) — its rebuild post-flip must not regress on existing structural gates. If your calibration would shift m01–m03 bands by >2pp, that's a calibration failure, NOT a Decision Card change — re-fit.

## Deliverables

1. **`audit/ulp-calibration-2026-05-13/raw.jsonl`** — one JSON object per ULP lesson with fields above (`season`, `lesson_num`, `cumulative_vocab_count`, `new_lemmas`, `recycled_lemmas`, `uk_density_pct`, `en_density_pct`, `uk_token_count`, `en_token_count`).
2. **`audit/ulp-calibration-2026-05-13/REPORT.html`** — human-readable summary (HTML per #M-2 since ai→human): season-by-season UK-density curve, knee identification, family mapping rationale, sensitivity analysis (which neighboring constant values would give equivalent bands), chosen final constants, backward-compatibility table for a1 m01–m03 before/after flag flip.
3. **`scripts/config.py` edits**: replace the two `PHASE_4_PLACEHOLDER` blocks with calibrated constants. Flip `USE_ULP_IMMERSION_DERIVATION` to `True`. Inline comment on each block: `# Calibrated 2026-05-13 from ULP S1-S6 replay. Audit: audit/ulp-calibration-2026-05-13/REPORT.html`.
4. **Tests** at `tests/test_ulp_immersion_calibration.py`: parametrize `compute_immersion_band` calls for representative `(track, module_num, learner_state)` triples — verify band shape under flag-on matches expected calibration. Include a regression test asserting m01-m03 backward-compat.
5. **Conventional commit + PR**.

## #M-4 verifiable claims (paste raw output, never "I checked X")

| Claim in body or commit | Required tool-evidence |
|---|---|
| "ULP S1 lesson 1 UK density = X%" | raw lemma-count numerator + total-token-count denominator + the per-lesson JSONL line |
| "Knee for `a1` family at cumulative-vocab=N" | scatter / regression output + the JSONL slice it was computed from |
| "Recycle cadence for `a1` = M every Q lessons" | per-lemma revisit-lag distribution emit + summary statistics |
| "Tests pass" | `.venv/bin/python -m pytest tests/test_ulp_immersion_calibration.py` final summary line raw |
| "Ruff clean" | `.venv/bin/ruff check scripts/config.py tests/test_ulp_immersion_calibration.py` "All checks passed!" raw |
| "Backward compat on a1 m01-m03" | before/after `compute_immersion_band` output dump, side-by-side, both runs in the report |

## 8-step process (numbered, no exceptions)

1. **Worktree setup.** `git fetch origin && git worktree add -b codex/ulp-calibration-phase-4-2026-05-13 .worktrees/dispatch/codex/ulp-calibration-phase-4-2026-05-13 origin/main` — work inside this worktree exclusively. (Per `delegate.py --mode danger --worktree` your wrapper sets this; document the path in the commit body.)
2. **File-level work.** Build extractor → build raw.jsonl → fit constants → write `scripts/config.py` edits → write `REPORT.html` → write tests.
3. **Run the test suite** for affected paths: `.venv/bin/python -m pytest tests/test_ulp_immersion_calibration.py tests/test_audit_recycle_cadence.py -v` (the latter exists per PR #1943; confirm calibration doesn't regress).
4. **Run ruff**: `.venv/bin/ruff check scripts/config.py tests/test_ulp_immersion_calibration.py` — zero warnings/errors.
5. **Commit** with conventional message (subject ≤ 70 char): `feat(immersion): Phase 4 ULP calibration — fit constants + flip flag` and a body summarizing the empirical findings + the backward-compat verification. `Co-Authored-By: Codex <noreply@openai.com>` line.
6. **Push** the branch: `git push -u origin codex/ulp-calibration-phase-4-2026-05-13`.
7. **Open PR** with `gh pr create --title "..." --body "$(cat <<EOF ... EOF)"` referencing the Decision Card + the audit report.
8. **DO NOT auto-merge.** Orchestrator reviews + merges manually. `--allow-merge` is OFF on this dispatch (default).

## Pre-submit checklist — `AGENTS.md:11-26` MANDATORY (paste verbatim, verify EVERY box before push)

- [ ] `.python-version` unchanged (must be `3.12.8`)
- [ ] `.yamllint` unchanged
- [ ] `.markdownlint.json` unchanged
- [ ] No `status/*.json` files in the diff
- [ ] No `audit/*-review.md` files in the diff (the calibration report at `audit/ulp-calibration-2026-05-13/REPORT.html` is fine — it's a calibration artifact, not a review artifact)
- [ ] No `review/*-review.md` files in the diff
- [ ] No `sys.executable` anywhere in code (use `.venv/bin/python`)
- [ ] No `@pytest.mark.skip` with empty `pass` bodies
- [ ] No assertions weakened (e.g., `is True` → `isinstance(..., bool)`)
- [ ] Every changed file is directly related to ULP calibration
- [ ] Total files changed < 20 (Phase 4 should comfortably fit; if more, you've included artifacts)
- [ ] Code runs without `NameError`, `KeyError`, or `ImportError`

If you cannot check every box, your PR WILL be rejected.

## Anti-patterns specific to this work

- ❌ **Don't invent numbers**. Every constant must come from a JSONL line you can point to. Pre-trained guesses on "what looks like a reasonable knee" are forbidden — fit from data.
- ❌ **Don't reuse the static `IMMERSION_POLICIES` values** as the ULP-derived calibration. They're the v6/early-V7 inheritance the card explicitly redirects from. The backward-compat check is the m01-m03 *transition* (so flipping doesn't regress), not the whole curve.
- ❌ **Don't skip the report.** The HTML report is the audit trail. A PR with constants + tests but no `REPORT.html` is incomplete.
- ❌ **Don't flip the flag without the report passing review.** The flip is a load-bearing change: every subsequent A1 build inherits it. Audit trail before deploy.
- ❌ **Don't `git checkout -b` in the main project dir** — always work inside the worktree from step 1. (Per `claude_extensions/agents/curriculum-maintainer.md` failure-modes lesson 2026-05-14.)
- ❌ **Don't bypass blocking CI.** Per #M-0.5: pytest, ruff, frontend, schema-drift, gitleaks, radon, prompt-lint = ALL blocking. Advisory `review/review` (Gemini-Dispatch) is the only non-blocking failure.

## Acceptance (closes Phase 4 of the Decision Card)

Phase 4 is "done" when:

1. Constants in `scripts/config.py` are empirically derived (justified by `audit/ulp-calibration-2026-05-13/REPORT.html`).
2. `USE_ULP_IMMERSION_DERIVATION=True` is committed.
3. Backward-compat verified: a1 m01-m03 advisory band stays within ±2pp of pre-flip values.
4. Tests pass; ruff clean.
5. PR opened (NOT merged) — orchestrator reviews report + merges.

Post-merge, the orchestrator will trigger **Phase 5** (second A1 pilot — pick `a1/around-the-city` or `a1/at-the-cafe`, user-run V7 build, verify student-aware lesson building generalizes).
