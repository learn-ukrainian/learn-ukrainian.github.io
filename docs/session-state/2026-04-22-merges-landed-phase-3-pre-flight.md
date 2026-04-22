# Session Handoff — 2026-04-22: all merges landed, l1-uk plans clean, ready for Phase 3

> **Status:** COMPLETE — all merges landed, pushed to origin.

## TL;DR

Overnight autonomous bakeoff + 124-plan fork batch → morning decisions locked (Opus writer, Codex reviewer) → careful sequential merges → Phase 1B-apply verification-then-fix pass → Phase 2C wiki L2-framing strip → **ready to start Phase 3 (l1-uk A1+A2 module build, 124 modules total).**

Main at **`90f49b629`** (post all merges, pushed to origin). Every step tracked on its own branch pre-merge, tests verified between merges, pushed to origin.

## Prior session chain

| Session | File |
|---|---|
| Yesterday evening | `2026-04-21-evening-strategic-audit.md` (mirrored in `current.md`) |
| Overnight autonomous | `2026-04-22-overnight-bakeoff-and-124-plan-forks.md` |
| This morning (decisions + merges) | `2026-04-22-decisions-locked-and-merge-prep.md` |
| **This handoff** | `2026-04-22-merges-landed-phase-3-pre-flight.md` |

## What landed today (in merge order)

| # | Merge | Commit | Scope | Tests |
|---|---|---|---|---|
| 1 | Phase 1A structural plan sweep | `2f3f638d0` | 441 Latin M## + 33 homoglyph + 456 format fixes across 218 plans (a1/a2/b1) | 9 passed |
| 2 | Phase 2A wiki `generated_by_model` retrofit | `90fa1dc24` | Compiler + backfill + scan tool; 228 wikis backfilled, 18 Flash flagged | 59 passed |
| 3 | 124 l1-uk plan forks | `4090617d3`…`5036a688e` | A1 55/55 + A2 69/69 at `curriculum/l1-uk/plans/` | — |
| 4 | Phase 1B linguistic audit report (no fixes) | `5290100d1` | 861 findings at `audit/phase-1b-linguistic-audit/report.md` | — |
| 5 | Phase 2B A1/A2 wiki audit report (no rewrites) | `d8b57a8c2` | 147 L2-framing findings at `audit/phase-2b-wiki-audit/report.md` | — |
| 6 | Bakeoff artifacts | `ed769d38f` | Results doc, 20 reviews, aggregate.json, prompts, scripts, exec plan, session state | — |
| 7 | Phase 1B-apply | `262e6071a` | 425/861 verified fixes applied, 436 skipped as false-positive/pedagogical. Breakdown: D7-content 416/782, D4 8/28, D6 1/37, D2 0/14. Report at `audit/phase-1b-apply/report.md` | 50 passed |
| 8 | Phase 2C wiki L2-framing strip | `90f49b629` | Deterministic script `scripts/wiki/strip_l2_framing.py` removed L2 sections + framing sentences from 124 A1/A2 wikis. 127 files, +664/-1597 | 54 passed (+4 new strip tests) |

Origin `main` pushed to `90f49b629` — all 8 merges live.

## Locked decisions (from morning session)

1. **Phase 0A writer winner:** Claude Opus 4.7 — 7.80 mean, zero FAIL verdicts
2. **Phase 0B reviewer pair:** Codex primary + Opus escalation for borderline (7.0-8.0 from Codex)
3. **Phase 1B apply scope:** full apply across l2-uk-en + l1-uk, verified-then-applied to skip false positives
4. **Phase 2B wiki policy:** programmatic strip first, Opus rewrite only for residue
5. **Phase 1C leak-inheritance:** accept forks as-is, clean via 1B-apply (decision 3)

## Publishable bakeoff artifacts

- `docs/experiments/2026-04-22-writer-bakeoff-results.md` — results writeup (Opus winner, methodology, caveats)
- `docs/experiments/2026-04-21-writer-bakeoff-a1-m03.md` — experiment design doc
- `docs/experiments/writer-bakeoff-2026-04-22-prompts/` — adapted writer prompt, reviewer prompt, aggregation script (for reproducibility)
- `experiments/writer-bakeoff-2026-04-22/reviews/` — 20 round-robin review YAMLs + `_aggregate.json`

## Tooling incidents resolved

1. **pyenv-shim lock.** Hung `pyenv-rehash` process from yesterday 9:00 AM held the shim lock — every `.venv/bin/python` call waited 60s. Killed-already-died process, removed stale lock, Python now runs in 25 ms.
2. **Disk full (overnight).** Hit 100% used during A2 fork batch — worktrees consume hundreds of MB each. Cleaned completed fork worktrees as they landed; branches preserved. 35 GB free at end.
3. **Shell `&` parallelism race (overnight).** First fire script for 124 forks fired all at once because delegate state-machine registration raced with the throttle check. Fixed by switching to `xargs -P N` with synchronous dispatch+wait.
4. **Branch name inconsistency (overnight).** 2 A2 forks ended up on `codex/fork-l1uk-a2-*` instead of `codex/fork-1c-a2-*`. Merge script matched both patterns.

## What Phase 1B-apply did

**Total applied: 425 of 861 findings (49%).** Codex re-read each flagged line in-situ, classified it (REAL_DEFECT / FALSE_POSITIVE / PEDAGOGICAL), applied only real defects, and mirrored fixes into the matching l1-uk fork where the slug existed.

**Breakdown:**

| Category | Total | Applied | Skipped | Reasons for skip |
|---|---|---|---|---|
| D7-content (English gloss leaks) | 782 | 416 (53%) | 366 | Morphology-only tags `(m)`/`(f)` preserved; vocabulary_hints and speaker-role annotations kept |
| D4 (calques) | 28 | 8 (29%) | 20 | Pedagogical discussions of invitation forms; acceptable contextual phrasing; literal culinary sense |
| D6 (Russianisms) | 37 | 1 (3%) | 36 | Pedagogical error lists teaching the wrong form; legitimate identity use of `самий`; literal `з'являється` |
| D2 (context-blind) | 14 | 0 (0%) | 14 | Grammar rule explanations (`має бути + case`), vocabulary glosses, natural quoted emphasis |

Key finding: Gemini's regex-based audit produced many false positives (51% of findings were pedagogical, not defects). The "verify-before-apply" instruction was load-bearing. Applying all 861 blindly would have damaged legitimate teaching content.

No REQUIRES_HUMAN_REVIEW findings flagged — Codex made a confident classification on every finding.

## What Phase 2C did

Codex wrote `scripts/wiki/strip_l2_framing.py` — a deterministic cleanup script (NOT an LLM rewrite). Script has `--dry-run`, `--apply`, and `--report` modes. It operates on three patterns identified in the Phase 2B audit:

1. Whole sections titled for L2 / English learners (`## Типові помилки L2 (англомовні учні)` etc.)
2. Transitional sentences explicitly addressing English speakers (`англомовні учні`, `English speakers often`, `Unlike in English`)
3. Comparison tables explicitly captioned against English grammar

**Result:** 124 wikis changed, +664 / -1597 lines. Mostly deletions as expected.

**Preserved:** Ukrainian pedagogy, IPA notation, textbook citations (`[S1]`/`[S2]`/`[S4]`), mnemonics, decolonization sections, `<!-- wiki-meta -->` blocks, `generated_by_model` metadata.

**Tests added:** 4 new tests in `tests/test_strip_l2_framing.py` verifying idempotency, wiki-meta preservation, minimum-content threshold, and pattern matching.

**Report:** `audit/phase-2c-wiki-strip/report.md`

## Ready for Phase 3 (l1-uk A1+A2 module build)

### Pre-flight status

- ✅ Plans clean: 218 l2-uk-en + 124 l1-uk, Phase 1A structural fixes + Phase 1B verified fixes applied
- ✅ Wikis clean: `generated_by_model` metadata present, L2-framing stripped (after 2C)
- ✅ Writer: Opus 4.7 via `claude -p --model claude-opus-4-7`
- ✅ Reviewer: Codex primary (with Opus escalation for borderline)
- ✅ Adapted system prompts available: `docs/experiments/writer-bakeoff-2026-04-22-prompts/`

### Phase 3 dispatch shape

124 module build dispatches (55 A1 + 69 A2), each:
- Own worktree + branch
- Opus writer → module markdown committed to worktree
- Codex reviewer scoring against the 6-axis rubric
- Heal loop capped at 2 rounds per rule §4 (PATCH not REGENERATE)
- If Codex score < 7 after heal, escalate to Opus reviewer
- If Opus agrees < 7, mark slug REQUIRES_HUMAN_REVIEW

### Throughput expectations

- Each module build: 10-20 min
- Review: ~5-10 min
- Heal + re-review (if needed): add 10-20 min
- Expected happy path: ~20 min per slug
- Parallelism: 5-8 concurrent (respect Codex and Opus rate limits)
- Total: 55 A1 / 6 parallel × 20 min = ~3 hours for A1 batch, similar for A2

### Known risks going into Phase 3

1. **Adapted writer prompt has known gap:** bakeoff showed NO writer achieved majority PASS — most common complaint was activity_hint count below plan spec. Before Phase 3 scale, the writer prompt should be hardened on the activity-count contract. Consider a 1-slug re-test on A1 M03 with the hardened prompt before batching.
2. **D2/D4/D6 fix residue:** Phase 1B-apply will skip some findings as "REQUIRES_HUMAN_REVIEW" — those plans may still have ambiguous prose that trips Phase 3 writing quality. Flag list should be reviewed before Phase 3.
3. **Opus reviewer escalation budget:** if Codex flags ~20% of modules as 7.0-8.0 borderline, that's 25 Opus reviews (A1+A2) — expected but check against weekly Claude budget.

## Operational notes

- **Git state:** main at `90f49b629`, pushed to origin
- **Disk:** 34 GB free (86% used)
- **Active worktrees:** 12 pre-existing unrelated worktrees (claude-prompt-budget-1280, codex-1392-plan-latin-fix, etc. — from previous sessions). All merged-today worktrees cleaned up post-merge. These 12 can be reviewed separately and deleted when their branches are resolved.
- **pyenv-shim:** clean (no stale lock)

## What is NOT done

- Phase 3 not started — this is the next user decision to fire
- Seminar tracks untouched (separate bakeoff needed when time)
- B1+ wikis unchanged (per decision — only A1/A2 wikis needed the L2-strip)
- Public deploy not triggered

## Commit order on main (full chain since yesterday evening)

```
90f49b629 Merge Phase 2C: deterministic L2-framing strip from A1/A2 wikis
070379821 fix(wiki): strip L2-English-learner framing from A1/A2 wikis (Phase 2C)
262e6071a Merge Phase 1B-apply: verified linguistic fixes (425 of 861)
978045c3c fix(plans): apply Phase 1B D2 context-blind fixes (0 verified of 14)
4f1acf856 fix(plans): apply Phase 1B D6 Russianism fixes (1 verified of 37)
4e950a7d5 fix(plans): apply Phase 1B D4 calque fixes (8 verified of 28)
f8a72f54b fix(plans): apply Phase 1B D7-content fixes (416 verified of 782)
ed769d38f docs(bakeoff): experiment artifacts, results, session state
d8b57a8c2 Merge Phase 2B: A1/A2 wiki quality audit report (AUDIT ONLY)
5290100d1 Merge Phase 1B: linguistic plan audit report (AUDIT ONLY, no fixes)
5036a688e Merge l1-uk plan forks batch 7 (4 slugs)
049c0cc55 Merge l1-uk plan forks batch 6 (20 slugs)
74107535a Merge l1-uk plan forks batch 5 (20 slugs)
8233e50cf Merge l1-uk plan forks batch 4 (20 slugs)
c2a8504d1 Merge l1-uk plan forks batch 3 (20 slugs)
a5f830360 Merge l1-uk plan forks batch 2 (20 slugs)
4090617d3 Merge l1-uk plan forks batch 1 (20 slugs)
90fa1dc24 Merge Phase 2A: wiki generated_by_model metadata retrofit (#1398)
2f3f638d0 Merge Phase 1A: structural plan sweep (D1/D3/D5/D7)
```

Plus 124 individual `plan(l1-uk/{level}): fork {slug}` commits interleaved within the plan-fork batch merges.

---

**Handoff complete.** Next decision: fire Phase 3 l1-uk module build (55 A1 + 69 A2 modules, Opus writer + Codex reviewer), OR harden the writer prompt first against bakeoff gap #1 (activity-count contract) before scaling.
