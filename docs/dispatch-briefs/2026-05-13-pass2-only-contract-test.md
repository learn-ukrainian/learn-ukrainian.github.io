# Codex dispatch brief — Pass-2-only contract test (Track B from twopass convergence)

> **Issue:** none yet — file 1 follow-up issue for the experiment scaffold + verdict report.
> **Mode:** danger
> **Worktree:** `.worktrees/dispatch/codex/pass2-only-contract-test-2026-05-13/`
> **Base:** `origin/main`
> **Hard timeout:** 7200s
> **Silence timeout:** 1800s
> **Effort:** high

---

## Why this exists

Multi-agent discussion `twopass-workflow-2026-05-13` converged on staged option C with the cheap experiment FIRST: before any V7 pipeline rewrite, test whether a Pass-2 step can take a Ukrainian-only artifact and produce an L2-EN module that (a) preserves the Ukrainian content byte-identical at numbered anchors, (b) hits the 18-22% immersion sweet spot in the EN-scaffolded output.

If this contract test PASSES → a full two-pass `a1/my-morning` bakeoff is justified.
If it FAILS → full two-pass is premature; we ship single-pass with the prompt tune (Track A in flight).

**Cost:** roughly 1-3 LLM calls per run; experiment fits in ~30-60 min compute.

---

## #M-4 preamble — verifiable claims this experiment will produce

| Claim | Deterministic tool | Output format |
|---|---|---|
| "Pass 1 artifact created with hash-anchored UK content" | `sha256sum audit/twopass-pass2-only-2026-05-13/pass1_stripped.md` | quote SHA |
| "Pass 2 preserved Pass 1 hash anchors byte-identical" | `diff -u <(grep -A 200 '<!-- ANCHOR' pass1.md) <(grep -A 200 '<!-- ANCHOR' pass2.md)` returns empty | quote diff output |
| "Pass 2 hit immersion 18-22%" | re-run `python_qg.json immersion` on the Pass 2 artifact | quote `immersion.pct` value |
| "Anchor preservation gate works in isolation" | unit test asserting hash mismatch ⇒ failure | quote pytest line |
| "Tests pass" | `.venv/bin/pytest tests/` for any new test | quote summary |

Inline "I checked X" claims without quoted raw output = hallucination per #M-4.

---

## Experiment design

### Step 1 — strip EN scaffolding from existing claude artifact to simulate Pass 1

Source: `audit/bakeoff-2026-05-13-midday/claude/module.md` (1205w, English-first L2-EN module).

Strip:
- All English explanatory prose
- English gloss lines under Ukrainian examples
- English scaffolding (section labels, transition phrases)
- The "Hint" / "Tip" / "Watch out" English callouts

Keep (these become numbered Ukrainian anchors):
- Every Ukrainian dialogue line, numbered `<!-- ANCHOR uk-dlg-N -->` preceding it
- Every Ukrainian example sentence, numbered `<!-- ANCHOR uk-ex-N -->` preceding it
- Every Ukrainian grammar table cell, numbered `<!-- ANCHOR uk-tbl-N -->` preceding it
- Every Ukrainian vocab lemma in vocabulary.yaml as-is

Output: `audit/twopass-pass2-only-2026-05-13/pass1_stripped.md` + `pass1_anchors.json` (hash of each anchor's content).

### Step 2 — Pass 2 prompt: derive L2-EN module from Pass 1 anchors

Write `audit/twopass-pass2-only-2026-05-13/pass2_prompt.md`. Prompt contract:

- Input: the Pass 1 stripped artifact + the anchors.json.
- Task: produce a full L2-EN module (4 V7 artifacts: module.md, activities.yaml, vocabulary.yaml, resources.yaml).
- Hard constraints:
  - Every `<!-- ANCHOR uk-N -->` block from Pass 1 MUST appear in Pass 2 module.md byte-identical. Pass 2 may add English scaffolding AROUND each anchor but MUST NOT modify the Ukrainian inside the anchor.
  - Target immersion: 18-22% Ukrainian-only in EN scaffolding. Hard cap: 24%.
  - All 4 artifacts must conform to V7 schema (use existing schemas as reference).
- Writer: claude-tools (current V7 writer per ADR-2026-05-06 REVISED-AGAIN). Use the `claude` adapter via `scripts/agent_runtime/`.

Single Pass-2 LLM call. Capture full output.

### Step 3 — deterministic anchor-preservation gate

Write `audit/twopass-pass2-only-2026-05-13/check_anchors.py`. Reads:
- `pass1_anchors.json` (hash-per-anchor)
- `pass2_output/module.md` (Pass 2 module)

Extracts each `<!-- ANCHOR uk-N -->` block from Pass 2, hashes it, compares against pass1_anchors.json. ANY mismatch = FAIL with the anchor ID + diff.

Run it. Capture verdict.

### Step 4 — immersion check on Pass 2 output

Run the existing `immersion` gate from `scripts/build/linear_pipeline.py` (or a minimal driver that calls just that gate's function) against `pass2_output/module.md`. Capture `pct`.

### Step 5 — verdict report

Write `audit/twopass-pass2-only-2026-05-13/REPORT.md` containing:
- Pass 1 stripped artifact stats (word count, anchor count)
- Pass 2 LLM call cost / duration
- Anchor preservation result (PASS / FAIL with mismatched anchors listed)
- Immersion result (`pct`, target 18-22%, cap 24%)
- VERDICT: one of
  - **GREEN — anchors preserved + immersion 18-22%** ⇒ full two-pass `a1/my-morning` bakeoff is justified next
  - **YELLOW — anchors preserved BUT immersion outside band** ⇒ Pass 2 prompt needs tuning; not yet ready
  - **RED — anchor preservation failed** ⇒ Pass 2 contract is unenforceable via LLM alone; full two-pass is premature

---

## Numbered steps (mandatory checklist)

1. **Worktree setup:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian && \
   git worktree add -b codex/pass2-only-contract-test-2026-05-13 .worktrees/dispatch/codex/pass2-only-contract-test-2026-05-13 origin/main
   ```
2. **Build experiment directory:** `audit/twopass-pass2-only-2026-05-13/` with subdirs `pass1_stripped/`, `pass2_output/`, plus the scripts.
3. **Step 1: strip script** — write `scripts/strip_for_pass1.py` (oneoff). Run on the source artifact. Quote anchor count.
4. **Step 2: Pass 2 prompt + invocation** — write the prompt file and a minimal runner that invokes the claude adapter once. Capture full output to `pass2_output/`. Quote duration + token counts.
5. **Step 3: anchor-preservation gate** — write `check_anchors.py`. Run. Quote verdict.
6. **Step 4: immersion check** — invoke existing immersion gate on `pass2_output/module.md`. Quote `pct`.
7. **Step 5: REPORT.md** — synthesize. State VERDICT (GREEN/YELLOW/RED).
8. **Tests:** add a test for `check_anchors.py` with a fixture that has both matching and mismatched anchors. Run pytest. Quote summary.
9. **Ruff:** `ruff check audit/twopass-pass2-only-2026-05-13/ scripts/strip_for_pass1.py`. Quote.
10. **Commit + push + open PR** with REPORT.md as the body. Title: `experiment(twopass): Pass-2-only contract test — VERDICT=X`.
11. **DO NOT auto-merge.** Hand back for review.

---

## What blocks merge

- The experiment isn't actually run (no LLM call captured, just scaffolding).
- The anchor gate isn't deterministic (uses fuzzy matching, regex shenanigans, "close enough" heuristics).
- The REPORT.md verdict isn't grounded in tool output.
- The strip script destroys Ukrainian content beyond English scaffolding (verify with sample read).

---

## Out of scope

- Any change to V7 pipeline (`scripts/build/linear_pipeline.py`, `scripts/build/v7_build.py`)
- Any change to `l2-uk-direct` pipeline
- Re-running the original a1/my-morning bakeoff
- A second Pass 2 LLM call to try different prompts (one experiment, one verdict)

---

## Related

- Convergence channel: `twopass-workflow-2026-05-13`
- Predecessor: `docs/session-state/2026-05-13-afternoon-bakeoff-and-twopass-brief.md`
- Source artifact: `audit/bakeoff-2026-05-13-midday/claude/`
- Companion (Track A): `docs/dispatch-briefs/2026-05-13-pipeline-gate-trio.md` + `2026-05-13-writer-prompt-tune.md`
