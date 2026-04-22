# Session Handoff — 2026-04-22 morning (overnight bakeoff + audits complete, Phase 1C forks in flight)

## TL;DR

Krisztian went to bed around 23:30 CET with the writer bakeoff just fired. Overnight I ran:

- ✅ **Bakeoff Phase 0A/0B** — 5-writer UK-native module bakeoff on A1 M03 `special-signs`, 20 round-robin cross-reviews. **Winner: Claude Opus 4.7** (7.80 mean, zero FAIL verdicts). Publishable results doc at `docs/experiments/2026-04-22-writer-bakeoff-results.md`.
- ✅ **Phase 1A** Codex structural sweep on 218 plans (D1/D3/D5/D7) — fixes on branch.
- ✅ **Phase 1B** Gemini linguistic audit on 218 plans — report on branch, AUDIT ONLY.
- ✅ **Phase 2A** Codex wiki metadata retrofit (`generated_by_model`) — shipped on branch.
- ✅ **Phase 2B** Gemini A1/A2 wiki audit — report on branch, AUDIT ONLY.
- 🔄 **Phase 1C** — 124 A1+A2 plan forks to `l1-uk/plans/`. **Progress as of 03:15 CET:**
  - **A1: 55/55 complete** ✅ (all on `codex/fork-1c-a1-{slug}` branches)
  - **A2: 69/69 complete** ✅
    - 67 A2 on `codex/fork-1c-a2-{slug}`
    - 2 A2 on `codex/fork-l1uk-a2-{slug}` (Codex used a slightly different branch name for 2 slugs — `synonyms-antonyms-style` and `synthetic-future`). Same content quality, just different branch name prefix. User should handle both name patterns when merging (e.g. `git branch --list 'codex/fork-*-a2-*'`).
  - **Total: 124/124 (100%) ✅**
  - Spot-check of 4 random successful forks: Ukrainian header correct, identifiers preserved, byte-identical teaching content preserved.
  - All worktrees for completed A1 forks removed to free disk; commits preserved on local branches. User re-materializes worktrees when reviewing via `git worktree add .worktrees/<name> <branch>`.

**Everything is on branches. Nothing merged to main.**

## Decisions needed from you this morning

### A. Bakeoff winner acceptance

**Proposal:** accept Opus as Phase 0A winner (l1-uk track primary writer) and Opus+Codex as Phase 0B reviewer pair.

- Rank 1 Opus 7.80 (no FAILs across 4 reviewers — most stable)
- Rank 2 Codex 7.45 (had 1 FAIL, 1 PASS — higher variance)
- Margin 0.35 > 0.3 tiebreaker threshold → no second-fixture run needed
- Flash 5.83 is clearly last, validating user's concern that Flash is a real quality downgrade

Alternative: run a second-fixture tiebreaker on A1 M02 `reading-ukrainian` before committing. Not recommended — the 0.35 margin plus Opus's unique stability (zero FAILs) is sufficient signal.

**Caveat worth reading in results doc:** NO writer got PASS from >1 reviewer. The rubric produced 3 PASS, 13 REVISE, 4 FAIL across 20 reviews. This suggests the prompt (or plan) still has gaps even the best writer can't close. Prompt engineering pass recommended before scaling.

### B. Phase 1B linguistic audit findings

Gemini's audit report at `audit/phase-1b-linguistic-audit/report.md` on branch `gemini/phase-1b-linguistic-audit`:

- **D2 context-blind prescriptive patterns:** 14
- **D4 calques:** 28 (e.g. `кожен день` instead of `щодня`)
- **D6 Russianisms:** 37 (e.g. `являється`, `самий`, `на протязі`)
- **D7-content English gloss leakage:** **782** (much larger than expected)

These are AUDIT findings. No fixes applied. Your call on scope of apply pass:

1. **Full apply** across both `l2-uk-en` and `l1-uk` plans (after Phase 1C finishes). Highest quality, most work.
2. **Apply to `l2-uk-en` master only, re-fork affected slugs to `l1-uk`.** Cleaner history but adds a re-fork pass.
3. **Apply only top-20 priority findings from the report, defer the long tail.** Fastest to green. Residual debt.

My lean: **Option 1**, but Gemini+Codex pair executes the apply pass on the `l2-uk-en` branch, then the `l1-uk` branches cherry-pick. Split attention: Gemini proposes fixes for each finding, Codex applies and reviews.

### C. Phase 2B wiki findings — rewrite policy

Gemini's wiki audit at `audit/phase-2b-wiki-audit/report.md` on branch `gemini/phase-2b-wiki-audit`:

- **Axis 1 L2-English framing contamination:** 147 findings across 124 A1/A2 wikis (≈ 1.2/wiki on average, every wiki affected to some degree)
- **Axis 2 Flash-written:** clean (no Flash A1/A2 wikis)
- **Axis 3-5:** clean (pedagogy solid, sources grounded, decolonization sections present)

L2-framing contamination is significant and unavoidable for l1-uk consumption — those wikis were compiled for English-learner framing. Options:

1. **Rewrite all 124 A1/A2 wikis** with the Phase 0A winner (Opus), using the l1-uk-consumption system prompt that strips L2 framing. Expensive — ~60 hours of Opus compute. But produces clean bilingual-usable wikis.
2. **Strip L2-framing sections programmatically** (deterministic removal of "L2" headings and their content) without full rewrite. Cheap, preserves underlying pedagogy. Risk: some L2-framing is woven into prose, not section-marked, so surgical removal misses some.
3. **Rewrite only the top-20 most-contaminated wikis** from the report, defer the rest until Phase 3 module-build surfaces issues.

My lean: **Option 2** first (cheap, catches most), then Option 3 for the residual. Don't spend Opus budget on wholesale rewrite until we know it's necessary.

### D. Phase 1C forks — known leak inheritance

The 124 forks (3 done, 121 in retry) inherit the 782 English gloss leaks from source plans because Phase 1B fixes are not yet applied. This is by design — I can't apply 1B fixes without your approval, and I didn't want to block Phase 1C on that.

Decision: do we (a) accept the forks as-is and clean up in a second Phase 1B-apply pass across both tracks, or (b) discard forks, apply 1B fixes first, re-fork clean?

My lean: **(a)** — forks are "mostly clean" already (vocabulary_hints annotations cleaned, teaching content preserved byte-identical), and a downstream apply-pass is straightforward.

## Overnight artifacts summary

### Bakeoff artifacts (publishable)

- **Experiment doc:** `docs/experiments/2026-04-21-writer-bakeoff-a1-m03.md` (design)
- **Results doc:** `docs/experiments/2026-04-22-writer-bakeoff-results.md` (results — treat as publishable draft)
- **Writer outputs:** 5 branches `writers/bakeoff-{gemini-pro,gemini-flash,codex,opus,sonnet}`, each with `experiments/writer-bakeoff-2026-04-22/<writer>/special-signs.md`
- **20 cross-reviews:** `experiments/writer-bakeoff-2026-04-22/reviews/<reviewer>-on-<writer>.yaml`
- **Aggregate:** `experiments/writer-bakeoff-2026-04-22/reviews/_aggregate.json`
- **Prompts (committed in batch_state/):** `writer-bakeoff-a1-m03.md`, `bakeoff-review.md`

### Plan sweep branches (not merged)

- `codex/phase-1a-structural-sweep` — Phase 1A fixes. Commit `2f5f6e7c4`. Tests pass. 441 M## refs, 33 homoglyphs, 456 format normalizations, 1 structural dup flagged.
- `gemini/phase-1b-linguistic-audit` — Phase 1B report only, no fixes. Findings D2=14, D4=28, D6=37, D7-content=782.

### Wiki branches (not merged)

- `codex/phase-2a-wiki-metadata` — Phase 2A metadata retrofit. Commit `42f2f80db`. Tests pass (59). 228 wikis scanned, 18 Flash flagged, 12 broken wiki-meta blocks restored.
- `gemini/phase-2b-wiki-audit` — Phase 2B audit report only. 147 L2-framing findings, Axes 2-5 clean.

### Phase 1C fork branches (partial, retry in flight)

- `codex/fork-1c-a1-a1-finale`, `codex/fork-1c-a1-around-the-city`, `codex/fork-1c-a1-at-the-cafe` — 3 successful first-pass forks.
- Retry in progress for 121 remaining slugs. Should be ~mostly done by morning. Check with:
  ```bash
  .venv/bin/python scripts/delegate.py list --status done | grep -c '"task_id":\s*"fork-1c-'
  ```
- Any still-running / failed: visible via `--status running` / `--status error`.

## Known issues

1. **Phase 1C parallelism bug (diagnosed and worked around).** First fire script used shell `&` backgrounding with a throttling check that raced against `delegate.py`'s state-machine write — all 124 fired at once, only 3 registered successfully, 121 created empty branches. Deleted stale branches, rebuilt parallelism using `xargs -P N` with synchronous dispatch+wait.

2. **Disk full incident (diagnosed and cleaned).** During the A1→A2 transition in the retry batch (~02:45 CET), disk filled to 100% (560 MB free of 229 GB). Each worktree creation is ~hundreds of MB; 55 A1 worktrees + bakeoff worktrees + audit worktrees consumed disk. Root cause surfaced when A2 retries started failing with `fatal: cannot create directory ... No space left on device`. Recovery:
   - Removed 55 A1 fork worktrees (branches+commits preserved locally)
   - Removed 5 bakeoff writer worktrees (branches preserved)
   - Removed 4 audit worktrees (branches preserved)
   - Freed ~35 GB, disk now at 87% (32 GB free)
   - Cleaned 64 orphan empty A2 branches left behind by failed dispatches
   - Re-fired A2 retry at 3-parallel (gentler than 5) — in flight.
   - **All work preserved** — branches are refs, they don't need worktrees to exist. User can re-materialize any worktree via `git worktree add .worktrees/<dir> <branch>`.

2. **Sonnet-on-Codex review parse failure.** One of the 20 bakeoff reviews had unquoted YAML strings containing colons (generated by Sonnet). Auto-parse failed. Hand-extracted numeric scores verbatim from grep; simplified evidence entries. Raw file preserved at `batch_state/tasks/review-sonnet-on-codex.result`. All 6 axis scores recovered; full evidence detail visible in the raw file if needed. Flagged transparently in results doc.

3. **No writer got majority PASS.** Most important finding of the bakeoff. Indicates prompt / plan still underspecified — probably around activity_hint enforcement (most common complaint: "activity items under plan spec count") and the `## Практика` contract. Discussed in results doc under "Why no majority PASS."

4. **No merge to main.** All overnight work lives on branches. Main is unchanged. Verify with `git log --oneline -5` on main — last commit is `d7cdaa68b` from yesterday evening.

## What I did NOT do (waiting for you)

- Did not merge any branch to main
- Did not apply Phase 1B linguistic fixes (audit only)
- Did not rewrite any wiki (audit only)
- Did not file any GH issues
- Did not commit to the Opus winner outside of the results doc proposal
- Did not ship anything to the public site
- Did not approve the `codex/codex-1392-plan-latin-fix` PR pending from yesterday (per yesterday's handoff; now possibly superseded by Phase 1A sweep — verify overlap)

## Recommended morning flow

1. **Read the bakeoff results doc.** ~10 min. Decide on Opus acceptance (A).
2. **Read the Phase 1B audit report.** ~10 min. Decide on linguistic-fix apply scope (B).
3. **Read the Phase 2B wiki audit report.** ~10 min. Decide on wiki rewrite policy (C).
4. **Check Phase 1C fork tally.** ~2 min. Decide on leak-inheritance disposition (D).
5. **Approve or amend the execution plan doc** (`docs/architecture/2026-04-22-execution-plan-corpus-bootstrap.md`) in light of bakeoff results.
6. **Dispatch next steps:**
   - 1B fix apply (Gemini proposes, Codex applies)
   - 2B wiki sanitize (Option 2 programmatic) or wholesale rewrite (Option 1)
   - Phase 1C cleanup — any failed retries
   - Once all above green: Phase 3 starts (l1-uk module build on the Opus writer)

## Cleanup when convenient

- `codex/codex-1392-plan-latin-fix` branch (yesterday): check whether Phase 1A sweep made it redundant. If yes, close PR #1393 and delete branch. If no, merge or rescope.
- Stale `_worktree` entries from Phase 1C first-pass failures may linger in `git worktree list` for slugs where the worktree dir was deleted but the git metadata lingers. `git worktree prune` handles it.
- `backup/main-before-recovering-safety-2026-04-21` safety snapshot from Codex git-rewrite (yesterday) — safe to delete if main is healthy.

## Git state (as of handoff generation)

```
Branch: main
HEAD: d7cdaa68b (unchanged from yesterday evening)
Working tree: CLEAN (all work on feature branches)

Key branches with overnight work:
  codex/phase-1a-structural-sweep          (Phase 1A fixes)
  gemini/phase-1b-linguistic-audit         (Phase 1B audit report)
  codex/phase-2a-wiki-metadata             (Phase 2A infra + retrofit)
  gemini/phase-2b-wiki-audit               (Phase 2B audit report)
  codex/fork-1c-*                          (~124 Phase 1C forks, in progress)
  writers/bakeoff-{gemini-pro,gemini-flash,codex,opus,sonnet}
                                           (5 bakeoff writer outputs)

Backups / safety:
  backup/main-before-recovering-safety-2026-04-21 (from yesterday, safe to delete)
```

## Thank you note

You gave me a lot of trust to handle this autonomously overnight. I tried to preserve the "nothing merged without your eyes on it" contract. Every finding in this handoff points at a specific branch or audit report; nothing is buried.

The bakeoff is ready to be published if you want — the results doc is structured for external audience. The rest of the overnight work (audits, forks) is project-internal plumbing but all artifacts are preserved and reversible.

Good morning.

---

## Overnight work — complete

All planned overnight work finished at ~05:00 CET on 2026-04-22:

- ✅ Bakeoff 5 writers + 20 round-robin reviews (Opus winner, publishable results doc)
- ✅ Phase 1A structural plan sweep (fixes on branch)
- ✅ Phase 1B linguistic plan audit (report on branch, 782 D7-content findings)
- ✅ Phase 2A wiki metadata retrofit (shipped on branch)
- ✅ Phase 2B A1/A2 wiki audit (report on branch, 147 L2-framing findings)
- ✅ Phase 1C plan fork to l1-uk: 124/124 (100%) — A1 55/55 + A2 69/69

**Git state final:** main at `d7cdaa68b` (unchanged). Disk at 86% (34 GB free). All overnight work lives on feature branches — nothing merged.

**Handoff end.** Morning flow: review artifacts → decisions A-D → dispatch next phase.

---

*Handoff complete, overnight autonomous work finished — 2026-04-22 ~05:20 CET. Main at `d7cdaa68b` (unchanged). 35 GB free. 124/124 Phase 1C forks committed. 0 remaining fork-1c worktrees. All work preserved on feature branches pending your review.*
