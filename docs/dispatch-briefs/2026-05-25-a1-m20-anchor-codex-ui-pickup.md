# Codex UI pickup — a1/m20 anchor build (sequenced, hard-stop on infra fixes)

> **Surface**: Codex UI (interactive Codex Desktop), continuing the hot session that just shipped b1/adjectives-comparative via PR #2273 (plumbing) + #2274 (content). Do NOT run via `delegate.py dispatch` — the headless lane was tried and exited on a stop condition at 45s (#2275 .venv missing).
>
> **Why you**: visual MDX inspection, interactive judgment calls when ULP fidelity is borderline, and you can sort out blockers inline. Headless agents will pattern-match against your m20 ship for the 123 follow-on A1+A2 modules — make it the verbatim QA bar.
>
> **Boundaries (read this twice)**:
> - This is a **3-phase sequenced delivery**, not a single big PR. Phase 1 + Phase 2 must merge to main BEFORE Phase 3 (m20 build) starts. The b1 anchor (#2274) shipped with a Tab 4 metadata leak accepted; the a1 anchor will NOT — leak gets root-caused + fixed first.
> - "Trailblaze" license is for in-scope blockers only. If you find a tangentially-related rough edge (e.g. wiki_coverage_gate workbook+error-correction keyword bypass), FILE an issue, do NOT fix it inside the m20 work. Scope discipline keeps each PR mergeable in one review pass.

## Context (3-minute orient)

- Main HEAD: `d2a67632f8` as of brief write. Recent ships: #2272 (learner_state plan-fallback), #2274 (b1 adjectives-comparative anchor), #2276 (ULP presentation-pattern SSOT + m04 vocab), #2277 (gemini-review CI fix).
- Open issues in your scope: **#2275** (worktree symlinks — .venv + node_modules missing), **Tab 4 metadata leak** (not filed yet — file it as part of Phase 1 below).
- Reference docs you'll re-read:
  - `docs/best-practices/v7-design-and-corpus.md` §4 (the 10-check verify-before-promote)
  - `docs/best-practices/ulp-presentation-pattern.md` (the 7 Ohoiko practices — m20 is mid-S1)
  - `docs/dispatch-briefs/2026-05-26-a1-m20-anchor-codex.md` (the full m20 contract — your Phase 3 reference, ignore the dispatch ceremony at the top, use the §4 ten-check + ULP fidelity sections)
  - `curriculum/l2-uk-en/plans/a1/my-morning.yaml` v1.2.3 (m20 plan)

## Phase 1 — Tab 4 metadata leak (root-cause + fix, standalone PR)

**Hard rule**: this PR ships and merges BEFORE Phase 3 starts. Do not bundle Phase 3 here.

### The leak
The 2026-05-23 m20 ship (commit `944f4200e4`, reverted) had Tab 4 with strings like `writer telemetry retrieved chunk_id: ...` × 6 in the Ресурси tab. The b1/adjectives-comparative ship (#2274) had a similar pattern in its Tab 4. Root cause is unverified. Two candidate sites:

1. **mdx-assembler** — `scripts/generate_mdx/core.py::format_resources_for_mdx()` (or similar) might be inlining `resources.yaml` metadata fields verbatim instead of rendering only `{title, url, source}`.
2. **writer prompt** — `scripts/build/phases/linear-write.md` Tab 4 / Ресурси section might be instructing the writer to include `chunk_id`/`retrieved chunk` annotations in the rendered prose.

### Steps
1. Create a worktree: `git worktree add -B fix/mdx-tab4-metadata-leak .worktrees/fix/mdx-tab4-metadata-leak origin/main`.
2. Reproduce the leak locally:
   - Find the most recent build artifact with Tab 4 metadata: `grep -rl 'chunk_id\|retrieved chunk\|writer telemetry' curriculum/l2-uk-en/*/build-*/ | head -5`
   - If no archived artifact has it (because the m20 revert nuked the evidence), grep the b1/adjectives-comparative shipped MDX: `grep -nE 'chunk_id|retrieved chunk|writer telemetry|wiki_query_id|vesum_query_id' curriculum/l2-uk-en/b1/adjectives-comparative/adjectives-comparative.mdx`
   - Quote the exact leaked strings so you know what you're hunting.
3. Trace: is the leak in the writer's `module.md` raw output, in `resources.yaml`, or only in the rendered `.mdx`?
   - `module.md` leak → writer-prompt fix in `scripts/build/phases/linear-write.md`
   - `resources.yaml` leak → upstream wiki resolver / Tab 4 builder issue
   - `.mdx`-only leak → mdx-assembler fix in `scripts/generate_mdx/core.py`
4. Fix at the right layer. Add a test that asserts the rendered MDX for a sample resources.yaml does NOT contain pipeline-metadata strings.
5. Run pytest + ruff. Quote raw outputs.
6. Commit + push + open PR. Title: `fix(mdx): drop pipeline metadata from Tab 4 Resources tab`. Body cites the leaked strings + the layer fixed + the test asserting no regression.
7. **STOP**. Wait for the PR to merge before Phase 2.

### Stop conditions for Phase 1
- Root cause is in a layer outside the mdx-assembler / writer prompt (e.g., learner-state injecting metadata into the resources block) → diagnose, file a separate issue, ship the partial fix you DID land, hand off to orchestrator.
- Test failure that isn't trivially fixed → STOP, surface, do not force-push past a real failure.

## Phase 2 — #2275 worktree symlinks (.venv + node_modules) — standalone PR

**Hard rule**: this PR ships and merges BEFORE Phase 3 starts.

### Scope
- Read `gh issue view 2275` for the full design proposal.
- IN-SCOPE: extend `scripts/delegate.py::_provision_data_symlinks` with three more entries — `.venv`, `node_modules`, `starlight/node_modules`. Same skip-if-source-missing + skip-if-target-exists semantics as the existing `data/vesum.db` + `data/sources.db` entries. ~6-10 LOC change.
- OUT-OF-SCOPE for this PR (file as follow-up sub-issues if you want):
  - `--no-share-deps` opt-out flag (for dep-change dispatches like #2261 torchvision)
  - `delegate.py provision-deps --worktree <path>` backfill helper
  - Rename `_provision_data_symlinks` to `_provision_worktree_symlinks` (or similar)

### Steps
1. Worktree: `git worktree add -B fix/issue-2275-worktree-symlinks .worktrees/fix/issue-2275-worktree-symlinks origin/main`.
2. Edit `scripts/delegate.py:534` to add three more entries to the symlink-target tuple. Verify the symlink-creation code handles directory targets correctly (the existing code is for files; dir symlinks work with the same `symlink_to` call but verify the parent-dir-mkdir logic doesn't break for `.venv` whose parent IS the worktree root).
3. Add a test to `tests/test_delegate_data_symlinks.py` (already exists per repo grep): assert that a freshly-created dispatch worktree gets `.venv` and `node_modules` symlinks pointing to the main repo's versions.
4. Manual smoke test: create a throwaway dispatch worktree, verify `.venv/bin/python --version` resolves correctly through the symlink.
5. pytest + ruff. Quote raw outputs.
6. Commit + push + open PR. Title: `fix(delegate): symlink .venv + node_modules into dispatch worktrees (closes #2275)`.
7. **STOP**. Wait for merge before Phase 3.

### Stop conditions for Phase 2
- The existing function's parent-mkdir logic doesn't generalize to dir symlinks at worktree-root level → adjust to a tuple-of-tuples (relative_path, is_dir) shape if needed. That's still in-scope.
- `_provision_data_symlinks` is called from multiple code paths (line 597 + 628 in current main); verify both paths still work after the change.

## Phase 3 — a1/m20 anchor build (the actual ship)

**Pre-condition**: Phase 1 PR + Phase 2 PR BOTH merged to main. Verify with `git pull && git log -3 --oneline origin/main` showing both merge commits.

### Contract
The full contract is in `docs/dispatch-briefs/2026-05-26-a1-m20-anchor-codex.md`. Treat sections "Verifiable claims preamble (#M-4)", "Steps", "Hard constraints", "Stop conditions", and "Output format" as the binding spec. Ignore the dispatch ceremony at the top (you're not running via delegate.py).

### Key non-negotiables (repeat from the brief — this is the anchor, not a beta build)

1. **Tab 4 has NO metadata leak.** Phase 1 fixed it; verify in your m20 MDX with `grep -E 'chunk_id|retrieved chunk|writer telemetry|wiki_query_id|vesum_query_id' my-morning.mdx` → must be empty.
2. **INLINE 4-6 / WORKBOOK 6-9 (A1 10-total).** Per `linear-review-dim.md:128`. The 944f4200e4 revert was caused by 10 inline / 0 workbook — do NOT recur.
3. **Vocab 25-40 lemmas.** Plan has 27 candidates (12 targets + 7 required + 8 recommended). 25 is floor, 40 is ceiling.
4. **ULP S1 baseline** (m20 is mid-S1, NOT a boundary). All 7 practices per `docs/best-practices/ulp-presentation-pattern.md` with A1-grammar-focused adjustments (the "X sounds like Y" anti-pattern doesn't apply; the EN-first reflexive-verb explanation anti-pattern DOES).
5. **Named persona for Tab 1 dialogues**: Ліна + Настя (per plan's `dialogue_situations`).
6. **Stress marks on every multi-syllable UK term**, throughout Tab 1, Tab 2, Tab 3.
7. **§4 ten-check** all-PASS or explicit follow-up issue cited per FAIL. Quote raw evidence per row.

### Wall-clock estimate
- Build: 15-25 min (claude-tools writer default, the V7 standard since 2026-05-12)
- §4 verify + ULP fidelity check: 10-25 min interactive
- Total Phase 3: 25-50 min

### Steps (abbreviated — full version in the m20 brief)
1. Worktree: `git worktree add -B codex/a1-m20-anchor-2026-05-26 .worktrees/codex/a1-m20-anchor origin/main`.
2. Verify Phase 1 + Phase 2 are in main (`git log --oneline -5`).
3. Fire build: `.venv/bin/python -u scripts/build/v7_build.py a1 my-morning --worktree 2>&1 | tee build.log`. Phase 2 fix means .venv symlink is now in the dispatch worktree.
4. Run the §4 ten-check verbatim. Render MDX locally + click through tabs in browser.
5. Run the ULP 7-practices fidelity check. Quote 2-3 verbatim MDX excerpts per practice.
6. pytest + ruff. Quote raw.
7. Commit: `feat(a1): publish m20 my-morning anchor module — reflexive verbs A1.3`.
8. Push + open PR with the output format from the m20 brief.
9. **DO NOT auto-merge**. Tag orchestrator (Claude main) in the PR body.

## Phase 4 — anchor reference update (after Phase 3 merges)

Update `docs/dispatch-briefs/2026-05-26-a1-m20-anchor-codex.md` with verbatim MDX excerpts from the shipped m20:
- The Tab 1 dialogue render (with Ліна + Настя)
- The Tab 2 FlashcardDeck + VocabCards block
- The Tab 3 inline+workbook activity split rendering
- The Tab 4 Resources tab (CLEAN, no leak)

These excerpts become the verbatim QA bar for the 123 follow-on A1+A2 headless builds. Without them, headless agents pattern-match from the brief's prose — fragile. With them, headless agents pattern-match from real MDX — robust.

Commit + push as `docs(dispatch): update a1-m20 anchor brief with shipped MDX excerpts`.

## What to do if a phase fails partway through

- **Phase 1 fails to root-cause the leak**: ship what you DID find (e.g. the leak source is `linear-write.md` not the assembler), file a follow-up issue, hand off to orchestrator. Do NOT proceed to Phase 2 if the leak isn't actually fixed.
- **Phase 2 fails on a test**: ship the test as a regression-locker even if the fix is incomplete. Surface the gap.
- **Phase 3 §4 check fails for a reason outside your scope**: stop, file the issue, surface. The anchor must be clean; a half-clean anchor is worse than no anchor.

## Output / handoff

After each phase merges, post a short status update in this chat (or wherever the orchestrator pickup happens) with:
- PR URL
- Key evidence quoted (test names, raw pytest/ruff output, grep results showing the leak gone, the §4 ten-check table)
- Next phase status (started / blocked / ready)

After Phase 4 lands, the orchestrator (Claude main) picks up: fires headless dispatches for a1 m01-m19 + m21-m55 + A2 modules using your m20 ship as the verbatim QA bar.

---

**Anchor mantra**: this build sets the standard for 123 follow-on modules. A 95%-right anchor that ships fast costs 123× more in rebuild cycles later than a 99%-right anchor that takes one extra fix cycle now. Don't shortcut Phase 1 or Phase 2.
