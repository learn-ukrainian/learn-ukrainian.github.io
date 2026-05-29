---
date: 2026-05-29
session: "Autonomous overnight. Made codex the VALIDATED V7 writer (2 root-cause fixes merged + live-validated). Merged #2401 (10 bio dossiers). m20 (Step 7) cascade reached its 3rd gate — blocked at wiki_coverage err-obligations. User wants: (1) restart fresh on the bugfixed pipeline, (2) this handoff, (3) an ARCHITECTURE-ALIGNMENT discussion on the per-module generated-prompt approach (colleagues firing async)."
status: codex-writer-validated · m20-blocked-at-err-obligation-yaml · architecture-discussion-async
main_sha: 313d9e89da
main_green: yes (review/review advisory only)
---

# 2026-05-29 — Codex is the validated V7 writer; m20 at err-obligation blocker; architecture discussion open

## ⭐ LEAD AGENDA (user's question — answer this first in the fresh session)
**"We generate writer + reviewer prompts PER MODULE from rules + config (config.py, curriculum.yaml) + audience/level + the module plan + the module wiki + MCP/RAG corpus. Are we aligned? Is this the right path? Colleagues' opinions + improvements?"**

- **Colleagues firing ASYNC NOW** — channel `v7.2-prompt-architecture-alignment-2026-05-29` (codex+gemini+cursor, 2 rounds, bg task `bg3pxroax`). **Read their responses first thing** (`ab read` / channel watch) and synthesize.
- **My (Claude) view — the architecture is RIGHT, the execution has friction:**
  - ✅ Single-source-of-truth (wiki → writer + reviewer + gate) directly kills the gate-vs-prompt drift class that caused ~5+ failures this month. Per-module specificity is correct for 1713 modules. Deterministic, no-LLM composition is reproducible/testable/versionable. Genuine improvement over V7.0's "universal template the writer adapts" (which produced the adaptation + drift failures).
  - ⚠️ **Single biggest risk = prompt bloat fighting instruction-following.** The generated writer prompt is **143KB (> our 130KB ceiling)**. Inlining all reference text degrades adherence. Highest-ROI change: a LEANER prompt that leans on MCP fetch-at-write-time + a **few-shot exemplar** (the Pt-10 9.5/10 baseline `.worktrees/builds/a1-my-morning-20260527-185032`) instead of verbose rules.
  - ⚠️ **Correction-loop is the fragile load-bearing path.** The architecture pushes "did the writer emit all 18 obligations?" onto a correction loop that can't reliably fill structured-artifact gaps (see m20 blocker). Better: maximize **first-pass completeness** — the generator pre-seeds activity/impl_map stubs for structured obligations (esp. error-correction activities) that the writer fills, vs. relying on correction.
  - ⚠️ Writer literalism cuts both ways: a malformed fragment propagates to every module (tonight's DialogueBox bug), BUT one fragment fix also propagates everywhere — net positive WITH surgical fragment discipline + tests.

## What SHIPPED this session (main `313d9e89da`, all CI green)
| # | Fix | Detail |
|---|---|---|
| **#2403** `eb7b4c1857` | Codex "tool theatre" = a **TIMEZONE capture bug** | `_candidate_rollout_dirs` scanned UTC-date dirs; codex (22:12Z = 00:12 Budapest) wrote local-date `2026/05/29`. Now scans UTC±1 + local±1 under scoped home; sibling-fixed `check_early_reap`+`liveness_signal_paths`; regression test. **VALIDATED:** codex now captures 11+ MCP calls incl `verify_words ×51`. (2nd time this was a measurement artifact — cf. PR #1907.) |
| `196a4ca7e5` | `<DialogueBox>` directive example missing `/>` | Gate regex `<DialogueBox\b(?:[^>]*/>|.*?</DialogueBox>)` counts only self-closed/closed tags. Codex copied the malformed example → 16 valid dialogues counted ZERO → false `too_few_uk_dialogue_lines`. claude self-corrected, masking it. Fixed example in R-CLEAN-TABLES + linear-write.md + linear-write-grok.md + explicit requirement + test. **VALIDATED:** l2_exposure_floor now passes. |
| **#2401** `107f4b081c` | 10 Розстріляне-Відродження bio dossiers merged | Overnight "fabrication" claim DISPROVEN — codex cited REAL plan files (`test -e` verified 9/10). One flagged НЛО citation in mykhail-semenko (demoted T2) noted on #2317. |

## ⛔ m20 (Step 7) BLOCKER — P0 next, dispatch-ready
Cascade: `mcp_tools_never_invoked` ✅ → `l2_exposure_floor` ✅ → **`wiki_coverage_gate` ❌ stuck 66.7% (12/18)** on err-1..err-6 (`l2_error`, `implementation_map_missing`):
- The writer doesn't emit error-correction activities + `implementation_map` entries on first pass.
- The correction loop's `implementation_map` injection produces **invalid YAML**: (1) newline-concat `...вмиваюся.    implementation_map:` → `mapping values are not allowed here`; (2) IPA apostrophe-doubling `[прокидайес'':а]` (sibling of PR #2184).
- **Fix in `scripts/build/linear_pipeline.py`** (wiki_coverage correction YAML injection — search `wiki_coverage_correction_yaml_invalid` + the activities.yaml fix-application path). **HIGH VALUE: blocks err-coverage for EVERY A1/A2 module with l2_error obligations.** Then re-fire `v7_build.py a1 my-morning --writer codex-tools --use-generator --worktree` → expect PASS → promote (replaces live PR #2364).
- **NB this overlaps the architecture discussion** (first-pass completeness vs correction-loop) — decide the fix layer with the colleagues' input.

## Follow-ups
- **P2 gate-vs-fix-cap mismatch:** `_validate_reviewer_fix_shapes(max_lines=6, max_chars=240)` makes `l2_exposure_floor` (any large-structural gate) un-auto-fixable — a 14-line dialogue injection always exceeds the cap. Example fix mitigates for compliant writers; cap mismatch is latent.
- **Reviewer-prompt artifact asymmetry:** writer prompt saved early/always (`writer_prompt.md`); reviewer prompts (`llm-qg-{dim}-prompt.md`, `wiki-coverage-review-prompt.md`) saved only when the LLM-review phase is reached. A build that fails at a deterministic gate (every m20 attempt) has NO reviewer-prompt artifact. If we want both prompts always-on-disk, render+persist both at generation time.

## Bio scope (corrected — overnight "fabrication" premise was HALF wrong)
- **#2401 Block A (codex): ✅ MERGED.** Real plan citations, not fabricated.
- **#2400 Block D (gemini): HELD — GENUINE fabrication** (~20 nonexistent `plans/...yaml` cited as "Existing" + metadata `#2318`→#2317, "Gemini 1.5 Pro"→gemini-3.1-pro). Needs relabel-fabricated→Candidate(Phase2+) + metadata. Correction must push to the SAME gemini branch (amend the PR).
- **C345 (claude):** 15 dossiers committed LOCAL `a2e02ba158`, branch UNPUSHED → push+PR+Section-7 verify.
- **C12 (claude):** 0 dossiers — FAILED → re-fire émigré C.1+C.2 (11 figures) via NON-claude agent.
- **R5 (agy):** 3 dossiers uncommitted in worktree (hlib-babich, maks-levin, viktor-hurniak) of ~12 → commit+push+continue.

## Writer policy (CONFIRMED)
**codex-tools IS the V7 writer** (own quota; makes real MCP calls now). **gemini is NOT free** (user correction — drop that framing). claude-tools FAILED tonight (CLI hung 883s, no response) + sunset post-2026-06-15. Reviewer = non-writer (codex/deepseek).

## Cold-start sequence (fresh session)
1. Read this brief. Confirm main ≥ `313d9e89da`.
2. **Read the architecture-discussion channel** `v7.2-prompt-architecture-alignment-2026-05-29` (colleagues' responses) → synthesize → align with user on the path + improvements BEFORE more m20 work.
3. Orient via Monitor API (`/api/orient`, inbox).
4. P0: fix the err-obligation YAML-injection bug (decide layer per discussion) → re-fire codex m20 → promote.
5. Bio: #2400 correct+merge, C345 push+PR, R5 finalize, C12 re-fire.
6. Build forensics retained (#M-10): `.worktrees/builds/a1-my-morning-20260528-{221218,221953,222759,230427,232046}`.

## What NOT to do
- ❌ Don't re-fire claude-tools as writer (failed + sunset). Codex is the writer.
- ❌ Don't call gemini "free."
- ❌ Don't promote m20 until err-obligations clear + full ACs pass.
- ❌ Don't merge #2400 until its fabricated paths are relabeled + metadata fixed.
- ❌ Don't re-litigate the 2 shipped fixes (capture bug + DialogueBox) — validated.
