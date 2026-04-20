# Session Handoff — 2026-04-20 ~03:15 local (mid-#1340-rethink)

User requested handoff before running the next empirical test. Context was at 53% — not urgent but we've done enough that a clean start with just the handoff is leaner than continuing.

## TL;DR — what you need to do on pick-up

One empirical test to run, then decide. See **"Next action"** section below.

## Phase 1 status — mostly green, one architectural question unresolved

| Step | Status | Evidence |
|---|---|---|
| #1337 schema ship | ✅ DONE | commit `45432e7db`. 5,276 sections, 98.83% backfill in production `data/sources.db` |
| #1339 grade filter | ✅ DONE INCIDENTALLY — **but see section below, this decision may need UNDOING** | Fixed in stage-c by converting `_TRACK_GRADE_RANGES` to strings matching the TEXT column |
| #1348 stage-d tests + ADR | ✅ DONE | commit `83dc10279`. 33 tests green (1 slow-marked test skipped as expected) |
| #1348 stage-e cold encode | ⚙️ RUNNING in background | `data/embeddings/manifest.db` has textbook_sections (5,276) + external (2,398, includes 1,199 orphan dupes) + modern_literary 57% (61,507 of 107,436). Log tail at `/tmp/cold-encode.log`. No process in `ps aux` grep but shards keep appearing — don't kill. |
| Concurrency bugfix | ✅ DONE | commit `3704d2f2f`. Fixed dense_rerank RLock (was self-deadlocking) + MLX bridge threading.Lock (was interleaving stdin/stdout). |
| #1340 re-validation | ❌ **FAILED 3/10 modern vs 6/10 legacy** — see next section | commit `0566cae2d` (playback patch only, no diagnostic outputs committed). Report: `wiki/.reviews/diagnostics/a1-sounds-letters-comparison.md` |

## The architectural question surfaced mid-#1340

### #1340 FAILED, and tri-agent said Path D (bound section serving), but then user pushed back harder

**Run-1 outcome**: Modern retrieval returned 7 sections = 59,631 chars (at 60K cap). One section was 20,633 chars (33% of cap). Legacy returned 40 chunks = ~48K chars.

**First tri-agent round** (thread `67bee51b2d9f`): converged on **Path D** — keep section-level retrieval, bound per-section serving to matched chunks + ±1 neighbors, per-section ceiling ~4-6K chars.

**User then challenged the grade-filter assumption** (in the question that triggered this handoff):
- `_TRACK_GRADE_RANGES` at `scripts/wiki/sources_db.py:792` maps A1→Grades 1-4 strictly
- Decision provenance: comment added 2026-04-18 based on one symptom ("Grade 10 morphology text appeared in A1 vowels lesson")
- User's point: CEFR (L2 framework) ≠ school grades (L1 native staging). Grade 5 systematic phonetics is exactly what an L2 A1 learner needs — adult metacognition makes it appropriate, unlike a native Grade 1 student who lacks that scaffolding.
- Grade 10 morphology was surfacing because the pre-#1348 pipeline used FTS5-only (keyword match). Post-#1348 dense rerank should filter topic relevance naturally — making the grade filter a band-aid for a cured disease.
- **Codex's "larynx_touch_exercise is unreachable for A1 (only in Grade 5)" claim in the tri-agent discussion was WRONG.** User caught it. I had endorsed it.

### Path forward (user-approved, before handoff)

**Empirical test**: remove `_TRACK_GRADE_RANGES` filter entirely, rerun `#1340` playback, see if concept coverage improves. Dense retrieval + per-track corpus priors should handle relevance without the grade filter crutch.

Parallel: still implement Path D (bounded section serving). The 20K-section budget-cannibalization problem is independent of the grade filter question.

## Next action (what to do on pick-up)

### 1. Empirical test: remove the grade filter, re-run #1340

**Edit `scripts/wiki/sources_db.py` around line 196-202 and line 785-799:**

Option: fully remove the filter
```python
# DELETE this block (currently around line 196-202):
extra_where = ["s.parent_section_id IS NOT NULL"]
extra_params: list[object] = []
if track in _TRACK_GRADE_RANGES:
    grades = _TRACK_GRADE_RANGES[track]
    placeholders = ",".join("?" * len(grades))
    extra_where.append(f"s.grade IN ({placeholders})")
    extra_params.extend(grades)

# REPLACE with:
extra_where = ["s.parent_section_id IS NOT NULL"]
extra_params: list[object] = []
# Grade filter intentionally removed: CEFR (L2 framework) does not map
# to Ukrainian school grades (L1 native staging). Dense retrieval +
# per-track priors in track_priors.yaml should handle topic relevance
# without an a-priori grade cutoff. Verified this by running the
# #1340 diagnostic before and after — see wiki/.reviews/diagnostics/.
```

Keep `_TRACK_GRADE_RANGES` dict as dead code for now (might resurrect as a soft prior, not hard filter). Add a deprecation comment on the dict. Or rip it entirely — your call.

**Then rerun**:
```bash
.venv/bin/python scripts/wiki/diagnostics/retrieval_playback.py --track a1 --slug sounds-letters-and-hello --strategy modern_dense
.venv/bin/python scripts/wiki/diagnostics/retrieval_playback.py --track a1 --slug sounds-letters-and-hello --compare
cat wiki/.reviews/diagnostics/a1-sounds-letters-comparison.md
```

**Expected outcome** (hypothesis — be empirical about it):
- Modern coverage goes UP from 3/10 because Grade 5-7 phonetics material is now reachable
- If Grade 10 morphology text starts appearing inappropriately, dense retrieval has a different problem we need to diagnose separately
- If modern still underperforms legacy after grade filter removed, the Path D section-serving fix is next

**Important**: cold encode is still running in background for modern_literary/archaic/wikipedia. The MLX bridge concurrency issue was fixed in commit `3704d2f2f`, but running the playback while cold encode is active means competing for the MLX worker's subprocess. If the playback hangs, kill cold encode (ps aux → kill PID), run playback, resume cold encode with `--resume`.

### 2. Based on test result, decide fix direction

Three outcomes:
- **A. Coverage ≥ 8/10 on reachable concepts after filter removal**: ship as-is. Grade filter removal is the fix. Path D section-serving fix becomes a nice-to-have optimization, not a blocker. Close #1340 after confirming, ship A1+A2 wiki batch.
- **B. Coverage improves but still < 8/10**: dispatch Codex on Path D (bounded section serving) + rerun. This is the most likely outcome.
- **C. Coverage regresses or stays at 3/10**: the section-level retrieval itself has deeper issues. Re-open tri-agent discussion with empirical data. Consider Path A (full chunk-level retrieval) as last resort.

### 3. After that lands, dispatch #1348 remaining work

- Cold encode completion: likely finished by the time you pick up (modern_literary at 57%, ~3-4 more hours from snapshot time + ~3 hours for remaining corpora = completion around noon local if not already)
- Then: `#1344` canary wiki rebuilds, then A1+A2 wiki batch (per roadmap).

## Key architectural reasoning user gave (verbatim-ish, internalize this)

> "who decided that class 5 content cannot be used in A1? we cannot map CEFR with grades for L1 learners."

The reasoning is:
- CEFR levels (A1/A2/B1/...) describe what an L2 learner can DO in the target language
- School grades (1-11) describe staged curriculum for NATIVE speakers who already speak the language fluently
- These are orthogonal scaffolding systems
- Content APPROPRIATE for L2 A1 may live anywhere in the L1 grade range — Grade 5 systematic phonetics is classic example (rich, explicit, perfect for L2 adult metacognition; not for a native Grade 1 who doesn't yet have the mental model)
- Topic relevance (does this teach basic sounds?) matters more than grade origin
- Dense retrieval finds topic relevance; let it do its job, don't pre-filter

When future design questions arise about "filter by grade," recall: the user's framework is L2 CEFR learners, curriculum spec defines what they need, topic relevance determines fit, grade is metadata not a gate.

## Supporting files

- **Roadmap**: `docs/architecture/ROADMAP-two-track-build-plan.md` — two-track design, Phase 1 steps, reviewer-load policy
- **Tri-agent discussion threads** (in `architecture` channel):
  - `67bee51b2d9f` — Path D convergence (superseded by user's grade-filter challenge)
  - `c5fb1e5512ae` — bootstrap framing convergence
  - `ab2a2a21c344` — initial L1-UK pivot discussion
- **Dispatches already fired (DONE)**: `docs/session-state/pending-dispatches/1337-ship.md`, `1348-stage-d.md`, `1340-playback-patch.md`
- **#1339 dispatch drafted but UNNEEDED**: `docs/session-state/pending-dispatches/1339-grade-filter.md` — was already fixed incidentally by stage-c. But now the whole #1339 framing is suspect per user's pushback; may want to close #1339 not as "fixed" but as "wrong premise."

## Open user decisions still pending from earlier in session

These were surfaced but not resolved — worth checking in morning:

1. **D1 from roadmap** (L1-UK integration path): A (unpark l2-uk-direct) / B (new l1-uk/) / C (shadow mode under l2-uk-en/, Claude rec). Not blocking anything immediately; next choice point is post-canary.
2. **A2 metalanguage word_target inconsistency**: 3 plans at 4000 vs 3 plans at 2000, all same A2.9 bridge phase. My rec: all 6 → 3000. ~5 min fix.
3. **Feedback feature question**: user asked about building learner feedback; Claude recommended GH-issue pointer, not feature build. User seemed aligned but not finalized.

## Commits since session start

```
3704d2f2f fix(wiki): resolve search_sources re-entrant deadlock + MLX thread-safety
0566cae2d feat(diagnostics): add modern_dense strategy + #1340 comparison report (#1340)
83dc10279 test(wiki): stress + fault-injection tests, ADR-006 revision (#1348 stage-d)
45432e7db feat(sources): ship #1337 schema + extraction for textbook parent sections
63ba03e0b docs: two-track build roadmap + overnight handoff + queued dispatches
```

## Known-background processes

- Cold encode: still running, modern_literary shard 81 at elapsed 13,116s. Log at `/tmp/cold-encode.log`. Manifest at `data/embeddings/manifest.db`. Don't kill unless you need MLX bridge free.

## Name-privacy policy (locked)

Never use real person names in anything that lands on public GitHub (issue bodies, comments, commit messages, PR descriptions, committed docs). Session-state files that stay local-only may use names.
