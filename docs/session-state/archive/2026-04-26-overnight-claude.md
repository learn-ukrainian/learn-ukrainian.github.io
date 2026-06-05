# Session Handoff — 2026-04-26 overnight (Claude)

> **Predecessor:** `2026-04-26-overnight-1586-phase4.md`
> **Status updated (02:58 CET):** #1591 + #1586 both MERGED to main (`d102a79887`); smoke test still running waiting on Gemini rung 1.

---

## TL;DR for next session / morning

1. **Wiki rebuild was producing broken articles.** Citation-shift bug in `compile.py` — body cited [S1]..[SN] over pre-dedup positions while the registry was renumbered S1..SM after dedup. Fixed in PR #1592, merged at `04aae723ab`.
2. **The 3 in-flight rebuild processes were killed by user before fix.** ~21 a1 articles + similar for a2/b1 are partially regenerated with broken citations. They need re-running.
3. **#1586 (Phase 4 unblocker) is in flight via Codex** — per-level per-dim LLM QG threshold schema. Watch for the PR.
4. **#1567 (Hungarian textbook contamination) was fully closed.** Sources DB cleaned, manifest tombstoned, GDrive source files deleted.
5. **Two follow-up bugs surfaced** in the wiki compile flow but NOT fixed tonight (separate from #1591). See "Other findings" below.

---

## What landed on main (commits since session start)

```
d102a79887  feat(thresholds): per-level per-dim LLM QG floors (#1586) (#1593)  ← TONIGHT (just merged)
04aae723ab  fix(wiki): dedup sources before prompt to align body citations with registry (#1591) (#1592)  ← TONIGHT
d79457e5e9  phase-3: lesson schema and prompt substitution (#1590)
67741940dd  feat(wiki): multi-agent writer support for compile.py (#1569) (#1589)
f9f7360b12  test(post-reboot): self-skip vitest tabs assertion when module deleted
f0635c70ad  phase-2: config audit per Phase 0 docs (#1583) (#1588)
```

`main` is now at `d102a79887` in both the user's checkout (just pulled) and origin. Two PRs merged tonight: #1592 (citation-shift fix) + #1593 (per-level per-dim thresholds).

---

## What's IN FLIGHT or PARKED right now

### Codex dispatches (active)
- (none currently active — both #1591 and #1586 merged)

### Codex dispatches (completed)
- **#1591** — done in 285s. PR #1592 merged at `04aae723ab`. Worktree + branch cleaned up.
- **#1586** — done in 490s. PR #1593 merged at `d102a79887`. Worktree + branch cleaned up. Phase 4 LLM QG schema is now live on main.

### Background watchers (may still be alive)
- `delegate.py wait 1586-llm-qg-thresholds` — fires when Codex 1586 reaches terminal status
- `gh pr checks 1592 --watch` — ALREADY FIRED (1592 is merged)

### Wiki rebuild — RUNNING (post-fix, in flight)
- **Smoke test PASSED at 02:58 CET.** `i-want-i-can.md` recompiled cleanly: 9 chunks → 8 sources (deduped before prompt), body cites `S1, S2, S3, S4, S6, S7, S8` = registry IDs exactly, **0 orphans, 0 unused**, discipline checks 0 violations.
- **Bulk rebuild launched at 03:00 CET** — all 3 tracks in parallel:
  - **a1**: background task `b43zvz9cf`, log `/tmp/compile-a1.log` (~2-2.5h ETA)
  - **a2**: background task `b3m07b8vl`, log `/tmp/compile-a2.log` (~2.5-3h ETA)
  - **b1**: background task `bedrh9bgx`, log `/tmp/compile-b1.log` (~3-3.5h ETA)
- **Total wall-clock ETA**: rebuild fully done by ~06:00-06:30 CET.

### Wiki rebuild — earlier broken state (now superseded)
- Stopped by user at ~02:30 CET after the citation-shift bug surfaced
- All 3 `compile.py --track {a1,a2,b1} --all --force` processes killed
- The articles regenerated before the kill have the citation-shift bug; the new bulk rebuild overwrites them
- User explicitly authorized this turn: "take over and run the a1 a2 b1 wiki generation with --force flag" — the no-touch wiki rule is LIFTED for tonight's rebuild

---

## What was DONE this session (chronological)

### 1. #1567 closed — Hungarian textbook contamination
- **Diagnosed:** Both `5-klas-ukrmova-uhor-2022-1` and `6-klas-ukrmova-betsa-2023` are HU-instruction editions for Zakarpattia. Verified by reading id=6769 cover text: "підручник для 6 класу з навчанням угорською мовою."
- **sources.db deletion:** 491 textbooks rows + 205 textbook_sections rows. FTS index rebuilt. Smoke test: `magyar`/`beszélgetni`/`tagadó`/`jelölésük` all return 0 FTS matches.
- **Cold-encode preserved:** Tombstoned 883 active units in `data/embeddings/manifest.db` (`UPDATE embedding_units SET deleted=1 WHERE corpus='textbook_sections' AND parent_key IN (...)`). **No re-encode needed** — vectors stay on disk; retrieval filters tombstones.
- **GDrive source deletion:** Removed PDFs (~37 MB), JSONLs (1.3 MB), per-image directories (173 PNGs), `.annotate_progress` markers. Files cannot be re-ingested.
- **Backup:** `/tmp/sources.db.pre-1567-20260426-015357.bak` (1.5 GB).
- **AC2/AC3/AC5 skipped** per user direction "1567 is not need it is a waste of time" — source files deleted from GDrive is a stronger guarantee than a code-level ingest gate.

### 2. #1591 filed and fixed — citation-shift in `compile.py`
- **Symptom:** The user observed `⚠️  Sources registry validation issues: Missing registry entry for citation S9` in the running rebuild log.
- **Diagnosis:** Surveyed 23 recently-rebuilt a1 articles. **6/23 (26%) have body citations missing from registry.** Pattern revealed: shift, not random hallucination. User confirmed: "there is a sift dont you see" — yes.
- **Root cause:** `scripts/wiki/compiler.py` lines 374-390. `_build_sources_registry` deduplicated source chunks AFTER `_format_sources` had already labeled them positionally for the writer. `assign_source_ids` then renumbered the registry to a clean S1..SM sequence. Body's [S{i}] preserved Gemini's prompt position, registry had post-dedup IDs → off-by-K shift.
- **Worse than the visible warning:** Validator only catches off-the-end orphans. **Mid-shift citations resolve to the wrong source content silently** (body's [S7] points to registry's S7, but registry's S7 is what was originally Gemini's S8 after renumber).
- **Fix (PR #1592, merged):** Added `_dedup_sources_by_attribution` helper; called at `compile_article` entry BEFORE prompt is built. Writer and registry-builder now see the SAME deduplicated source list. Existing dedup in `_build_sources_registry` kept as defensive no-op safety net. 7 regression tests added.

### 3. #1586 design + dispatch — per-level per-dim LLM QG thresholds
- **Design doc** drafted (205 lines) — schema: `DimensionFloor` dataclass + `LevelThresholds.review_floors: Mapping[str, DimensionFloor]`. Aggregator: MIN — module PASSes only when every QG dim ≥ pass_floor; REJECTs if any dim < reject_floor.
- **5 QG dims** per North Star §7: Pedagogical, Naturalness, Decolonization, Engagement, Tone.
- **Per-level defaults table** in design doc: A1/A2/B1 strict at 9.0 on pedagogical+naturalness+decolonization; B2+ relaxed to 8.0 on pedagogical+naturalness; decolonization=9.0 across all levels; engagement+tone=8.0 across all levels. Reject floor 6.0 across all (level, dim).
- **Codex brief** at `/tmp/codex-brief-1586.md` includes the design verbatim. Dispatched and running.
- **3-agent review on the design was NOT done** — user pushed for action ("ok do it"), so the design went straight to Codex with a written self-review. If Codex's PR diverges materially from the design, hold for review before merging.

### 4. Issue-debt audit (read-only survey)
- 65 open issues, 25 are >30 days old
- **Most >30d issues are intentionally deferred** (`mvp-deferred`, `priority:later`) — large EPICs (C2, OES+RUTH, STEM domain), parked content tracks, monolingual lexicon, ZNO integration
- **Genuine "fixed-but-open" debt is rare** in the current set — most candidates were already addressed or have legitimate ownership
- Did NOT mass-close to avoid overriding user judgment on priorities

---

## What needs to happen next (ordered)

### A. Smoke test the citation-shift fix — ✅ DONE (02:58 CET, PASS)

Body cites and registry IDs aligned perfectly. Rebuild launched.

For reference, the command was:

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
.venv/bin/python scripts/wiki/compile.py --track a1 --slug i-want-i-can --force
```

Then verify:

```bash
.venv/bin/python <<'PY'
import re, yaml
body = open('wiki/pedagogy/a1/i-want-i-can.md').read()
reg = yaml.safe_load(open('wiki/pedagogy/a1/i-want-i-can.sources.yaml'))
cites = set(re.findall(r'\[(S\d+)\]', body))
reg_ids = {s['id'] for s in reg.get('sources', [])}
orphans = sorted(cites - reg_ids)
print('PASS' if not orphans else f'FAIL: orphans={orphans}')
PY
```

If `orphans = []` → fix works → proceed to bulk rebuild. If not → STOP, investigate, do not bulk-rebuild.

### B. Bulk rebuild — ✅ LAUNCHED at 03:00 CET (in flight)

Already running. Background task IDs and log paths are in the "Wiki rebuild — RUNNING" section above. Three Python processes, one per track, in parallel.

Monitor progress:
```bash
tail -F /tmp/compile-a1.log /tmp/compile-a2.log /tmp/compile-b1.log
```

Or check process state:
```bash
/bin/ps auxww | grep -E "compile\\.py" | grep -v grep
```

**Verify post-completion (after all 3 tracks done):**
```bash
.venv/bin/python -c "
import re, yaml
from pathlib import Path
total = bad = 0
for track, dir_ in [('a1', 'wiki/pedagogy/a1'), ('a2', 'wiki/grammar/a2'), ('b1', 'wiki/grammar/b1')]:
    for md in Path(dir_).glob('*.md'):
        yml = md.with_suffix('.sources.yaml')
        if not yml.exists():
            continue
        try:
            cites = set(re.findall(r'\\[(S\\d+)\\]', md.read_text()))
            reg_ids = {s['id'] for s in (yaml.safe_load(yml.read_text()) or {}).get('sources', [])}
            total += 1
            if cites - reg_ids:
                bad += 1
                print(f'  {md.name}: orphans = {sorted(cites - reg_ids)}')
        except Exception:
            pass
print(f'\\n{bad}/{total} articles have orphan citations (target: 0)')
"
```

Target: `0/total`. If non-zero, investigate the specific articles flagged.

### C. Review and merge #1586 PR when Codex finishes
- Diff against `docs/decisions/2026-04-26-llm-qg-per-dim-thresholds.md` — the design doc is the spec
- Check that `aggregate_review` uses MIN (not weighted average)
- Check per-level default floors match the table in the design
- CI must be green except advisory Gemini-Dispatch
- Merge with `gh pr merge {N} --squash --delete-branch`
- Clean up `.worktrees/codex-1586-llm-qg-thresholds` after merge

### D. Phase 4 brief draft (was Wave 3 of the original plan)
- Slug-agnostic (user noted earlier: "There are plenty of other [rebuilt articles] you could have chosen")
- Re-read Phase 0 + Lesson Contract + Phase 3 design + Phase 3 impl
- Save brief to `/tmp/codex-brief-phase-4-{exemplar-slug}.md`
- 3-agent review on the brief
- DO NOT dispatch the actual build until #1586 merges AND wiki rebuild is finished

---

## Other findings worth your attention (NOT fixed tonight)

### Phantom multi-digit citations beyond the shift bug
`wiki/pedagogy/a1/where-is-it.md` cited `[S1154]`, `[S1800]`, `[S1873]`, `[S2479]`, `[S3164]` — 4-digit numbers far beyond any registry. Looking at `_format_sources` line 343, the prompt prints:
```
(internal ref: `{display_ref}` — cite this source as `[S{i}]`)
```
For non-textbook sources, `display_ref` is the chunk_id verbatim. Some chunk_ids start with "S" + digits. **Gemini occasionally cites the internal_ref instead of the positional `[S{i}]`.** Separate bug from #1591. Recommend file as #1591-followup or new issue.

### Canonical-anchor false-positives still firing
The known canonical-anchor checker false-positive bug from predecessor handoff is still live. `i-want-i-can.md` got 5 VERIFY markers on `«Здрастуйте»`/`«Здравствуйте»`/`«Kiev»` — these were CITED IN TEACHING CONTEXT (the article teaches against them). User direction: "don't touch, we will fix it later." Leave alone.

### `delegate.py` "deprecated flat worktree layout" warning
Both #1591 and #1586 dispatches got a warning: "task '...' is using the DEPRECATED flat worktree layout. New dispatches should use `--worktree` (bare) to land in `.worktrees/dispatch/{agent}/{task}/`." Not blocking — just a deprecation. File a small infra issue if you want to migrate the convention.

---

## Decisions made without explicit approval (state for your review)

- **Tombstone vs full re-encode for #1567:** chose tombstone path (`deleted=1` in manifest); preserves your 4-hour cold-encode work. AC4 of the issue (full re-encode) is unnecessary — the schema's existing `deleted` flag is exactly the right tool.
- **6-klas Бетса textbook full delete (not surgical):** verified front matter id=6769 explicitly says "з навчанням угорською мовою" (HU-instruction edition). Full delete of all 245+115 rows. You confirmed via "you have to delete."
- **No prevention code for #1567 (AC3 + AC5):** per your direction "1567 is not need it is a waste of time." Source files deleted from GDrive instead.
- **Skipped 3-agent review on the #1586 design before Codex dispatch:** per your time pressure ("ok do it"). If the resulting PR has design issues, blame is on me — the brief instructed Codex to flag ambiguity rather than guess.

---

## Active worktrees at handoff write time

```
/Users/krisztiankoos/projects/learn-ukrainian                                          04aae723ab [main]
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/codex-1586-llm-qg-thresholds  d79457e5e9 [codex/1586-llm-qg-thresholds]
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/codex-interactive             3c8bc39bae (detached HEAD)
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/verify-a1-1-phaseA-v5         ab3178fb64 [verify/a1-1-phaseA-v5]
```

`codex-interactive` and `verify-a1-1-phaseA-v5` are stale from prior sessions — safe to clean up if no longer needed.

---

## Cold-start protocol for next session (if I drop context or you wake)

1. Read this handoff fully.
2. `git log --oneline origin/main -10` — see what landed.
3. `gh pr list --state open --limit 10` — see open PRs (especially #1586's PR).
4. `.venv/bin/python scripts/delegate.py list --status running` — see if Codex 1586 is still working.
5. `gh issue view 1577` — EPIC reboot status; Phase 4 status.
6. `gh issue view 1586` — design + sub-issue trail; check for new comments.
7. `gh issue view 1591` — confirms closed/merged.
8. Act per "What needs to happen next" section above.

---

## Continuation — 2026-04-26 03:18 CET (orchestrator session 2)

A second orchestrator picked up from this handoff while the wiki
rebuild was in flight. Step D (Phase 4 brief draft) is now done.

### Phase 4 brief — sign-off complete, dispatch parked for morning

The staged brief at
`.worktree-briefs/codex-phase-4-a1-20-exemplar.md` (348 → 428
lines after corrections) was put through two rounds of 3-agent
adversarial review on the `architecture` channel:

- **Threads:** initial review `2ba9a32a6b1d` (rounds 1/2), final
  sign-off `b01022b5c7f7` (round 1 only)
- **Round 1/2:** both agents `[DISAGREE]` — 10 concrete blockers
  (schema generator path wrong, A1 activity authority wrong, VESUM
  routing wrong layer, semantic outline coverage misclassified,
  vocab gates too coarse, `aggregate_review` caller validation
  missing, REVISE path violating ADR-007, writer harness
  under-specified, LLM QG report shape loose, author signoff
  unmechanical).
- **Round 3:** both agents `[AGREE]` after fixes applied.

The biggest finding was the **REVISE path violating ADR-007** —
the predecessor's brief said "scoped regeneration of THE failing
section only (max 1 attempt)". `GEMINI.md:52` + `tests/test_no_rewrite_contract.py`
forbid LLM rewrite paths in any review feedback loop. Collapsed
both REVISE and REJECT to fail-fast: surface findings on the PR,
hand off to human review, no retry. Brief explicitly bans
introducing any function or symbol from
`FORBIDDEN_SYMBOLS_ACTIVE`.

Full panel transcripts at:
```
.venv/bin/python scripts/ai_agent_bridge/__main__.py channel tail architecture --thread 2ba9a32a6b1d4a02b19b7cb9c70a01c9
.venv/bin/python scripts/ai_agent_bridge/__main__.py channel tail architecture --thread b01022b5c7f7416cbddcf347004cbd25
```

EPIC #1577 was commented with the same summary
([comment URL](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1577#issuecomment-4320971186)).

### Phase 4 dispatch — pending wiki rebuild

Dispatch command is included at the bottom of the brief. Pre-condition:
wiki rebuild must finish first (no concurrent `wiki/` reads with the
Phase 4 writer). Morning steps:

1. Confirm wiki rebuild finished:
   ```bash
   pgrep -f "compile.py.*--track" || echo "ALL DONE"
   tail -n 20 /tmp/compile-a1.log /tmp/compile-a2.log /tmp/compile-b1.log
   ```
2. Run the orphan-citation verifier (block C in this handoff above)
   to confirm 0/total orphans across all 3 tracks.
3. Dispatch:
   ```bash
   .venv/bin/python scripts/delegate.py dispatch \
     --agent codex \
     --task-id codex-phase-4-a1-20-exemplar \
     --worktree .worktrees/codex-phase-4-a1-20-exemplar \
     --mode danger \
     --prompt-file .worktree-briefs/codex-phase-4-a1-20-exemplar.md
   ```

### Wiki rebuild status snapshot (03:18 CET)

All 6 tracks running in parallel — 3 launched at 02:56 CET (a1/a2/b1
via Gemini), and 3 launched at 02:53/02:54 CET (hist/lit/bio via
Claude). Sample tail:

- `a1`: at `pedagogy/a1/checkpoint-communication`
- `a2`: at `grammar/a2/aspect-concept`
- `b1`: at `grammar/b1/alternation-consonants-nouns`

ETA still ~06:00-06:30 CET for full a1/a2/b1 completion.

### Update — 2026-04-26 05:37 CET: a1 rebuild DONE

a1 finished at 05:36:53 CET (9623s wall, 55 compiled, 0 failed).
Bulk-scale verification of the #1591/#1592 citation-shift fix:

```
0/55 a1 articles have orphan citations (target: 0)
```

Every body `[S{i}]` resolves to a registry entry across the entire
rebuilt track. Recorded on #1591
([comment](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1591)).

Still running:
- `a2`: at `grammar/a2/purpose-clauses`
- `b1`: at `grammar/b1/introductory-words`
- `hist/lit/bio`: claude writers, started 02:53/02:54 CET, still running

a1 is technically sufficient for Phase 4 dispatch (the my-morning
exemplar reads from `wiki/pedagogy/a1/`), but the brief's pre-condition
asks for ALL of a1/a2/b1 done before dispatch. Holding for full
completion to keep the rule simple and avoid `wiki/` contention.

### Update — 2026-04-26 06:23 CET: a2 rebuild DONE

a2 finished at 06:23:12 CET (12402s wall, 69 compiled, 0 failed).
Verification: `0/69 a2 articles have orphan citations`.

Combined: **0/124 orphans across 124 freshly-rebuilt a1+a2 articles.**
Recorded on #1591.

Still running:
- `b1`: at `grammar/b1/passive-voice-intro` (just past `introductory-words`)
- `hist/lit/bio`: still running

### Update — 2026-04-26 07:46 CET: b1 rebuild DONE

b1 finished at 07:46:46 CET (17415s wall, 94 compiled, 0 failed).
Verification: `0/100 b1 articles have orphan citations`.

**Combined: 0/224 orphans across all 224 a1+a2+b1 articles.**
The #1591/#1592 citation-shift fix is fully verified at scale.
Recorded as the post-mortem comment on #1591.

### Update — 2026-04-26 07:48 CET: Phase 4 DISPATCHED

All Phase 4 pre-conditions satisfied (a1/a2/b1 done; hist/lit/bio
still running but write to different `wiki/` paths from the A1
exemplar). Dispatched per the parked brief:

```bash
.venv/bin/python scripts/delegate.py dispatch \
  --agent codex \
  --task-id codex-phase-4-a1-20-exemplar \
  --worktree .worktrees/codex-phase-4-a1-20-exemplar \
  --mode danger \
  --hard-timeout 14400 \
  --prompt-file .worktree-briefs/codex-phase-4-a1-20-exemplar.md
```

State at handoff write time:
- **Codex worker pid 69739** (delegate.py `_worker`)
- **Bridge pid 69748** (node)
- **Codex binary pid 69749** (`gpt-5.5`, effort `high` per `~/.codex/config.toml`)
- **Hard timeout:** 4h (14400s)
- **Branch:** `codex/phase-4-a1-20-exemplar`
- **Worktree:** `.worktrees/codex-phase-4-a1-20-exemplar` (flat layout — deprecated but consistent with the night's other dispatches)
- **Base SHA:** `d102a798870f888fa95cc88b87974e6f8b234b6e`
- **Prompt size:** 21443 chars

EPIC #1577 commented with the same payload
([comment](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1577#issuecomment-4321369700)).

### Background watchers active

- `bsek6oywq` — `delegate.py wait codex-phase-4-a1-20-exemplar
  --timeout 15000 --poll-interval 30` — fires task-notification on
  Codex terminal status (done / failed / timeout / cancelled).

### Cold-start protocol if I drop context before Codex finishes

1. `gh pr list --search "codex-phase-4-a1-20-exemplar"` — see if
   Codex pushed a PR.
2. `.venv/bin/python scripts/delegate.py status codex-phase-4-a1-20-exemplar` — see status, duration, returncode.
3. `git -C .worktrees/codex-phase-4-a1-20-exemplar log --oneline origin/main..HEAD`
   — see what Codex committed (may be empty if Codex died before
   first commit).
4. If task is still `running`: leave alone, the watcher will fire
   its own notification.
5. If task is `done` and PR exists: review against the brief, merge
   if green CI + author signoff string present.
6. If task is `failed` / `timeout`: read `stderr_excerpt` from
   `delegate.py status`, decide whether to file a follow-up issue
   or re-dispatch with a tightened brief.

### Update — 2026-04-26 08:18 CET: Codex DONE, draft PR #1594 opened

Codex Phase 4 dispatch returned in **14 minutes (866s)** with
`worktree_dirty_on_exit: true`. Substantial work shipped (10 new
files, +1772 LOC, all tests + invariants green) but Codex
**deliberately did not commit** because three blockers prevented
end-to-end exemplar proof:

1. **`data/vesum.db` absent in sparse worktree** — `worktree.sparsePaths`
   excludes `data/`. Real VESUM verification can't run inside a
   delegated worktree as currently provisioned.
2. **No `.venv` in worktree** — Codex had to use the main repo `.venv`
   for pytest.
3. **Hand-authored draft instead of live writer call** — Codex
   didn't actually invoke `scripts.agent_runtime.runner.invoke`
   with `claude-tools`; instead they hand-wrote the prose. Phase 4's
   "end-to-end proof" criterion is therefore PROVISIONAL.

Orchestrator (Claude) action: rather than lose 14 min of substantial
Codex work to an untracked worktree, committed Codex's progress with
a clearly-marked WIP message at `d313499332`, pushed the branch, and
opened **draft PR #1594**.

- Pre-commit hooks (ruff + pytest on affected files): all green
- 8 new tests passing (`test_linear_pipeline.py` + `test_a1_20_exemplar.py`)
- 36 invariant tests passing (no-rewrite contract, thresholds per-dim,
  review floors table sync, lesson schema)
- MDX validates; Starlight `npm run build` passes

**EPIC #1577 commented** with the same payload
([comment](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1577#issuecomment-4321396076)).

### Morning user — Phase 4 next steps

PR #1594 has the full test plan in the description. TL;DR:

1. **Fix worktree provisioning** so `data/vesum.db` is available
   (sparse-paths adjustment or symlink) and `.venv` exists per-worktree
2. **Re-dispatch with explicit live-writer invocation** in the brief —
   Codex should call `scripts.agent_runtime.runner.invoke` with
   `claude-tools` reading `linear-write.md`, replacing the hand-authored
   draft prose
3. **Run 5 independent per-dim LLM QG reviewer calls** to replace the
   blocked `review/a1/my-morning.json` placeholder
4. **Decide branch strategy** — iterate on `codex/phase-4-a1-20-exemplar`
   or re-dispatch from clean state with infra blockers fixed first

### Lesson learned for the next dispatch brief

The brief had `git commit` and PR steps as "Process discipline" prose,
not numbered steps. Per MEMORY DISPATCH-BRIEF CHECKLIST (#1472 lesson
2026-04-23): "If step 7 is a footer 'PR notes' hint, Codex stops at
commit. Numbered beats footnoted." This brief had the same pattern
and Codex stopped before committing. Next Phase 4 re-dispatch should
make commit/push/PR explicit numbered steps, AND make the live writer
call an explicit numbered step (not a deferred suggestion).

### Final overnight state

- All 4 EPIC pre-Phase-4 phases on main: Phase 0/1/2/3 + #1586 + #1591
- Wiki rebuild verified at scale: 0/224 orphans across a1+a2+b1
- Phase 4 scaffold landed in draft PR #1594, gated on infra fixes +
  live writer + live LLM QG before merge
- Active dispatches: 0 Codex, 0 Claude (this orchestrator only)
- Active background tasks: hist/lit/bio seminar wiki rebuilds (PIDs
  46221/46370/46511, started 02:53/02:54 CET, no orchestrator
  ownership of those — user-launched)

### Worktrees at handoff finalization

```
/Users/krisztiankoos/projects/learn-ukrainian                                         d102a79887 [main]
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/codex-interactive            3c8bc39bae (detached HEAD)
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/codex-phase-4-a1-20-exemplar d313499332 [codex/phase-4-a1-20-exemplar]
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/verify-a1-1-phaseA-v5        ab3178fb64 [verify/a1-1-phaseA-v5]
```

The Phase 4 worktree should NOT be deleted in the morning — the
re-dispatch may want to reuse the branch + iterate.

### Active dispatches at handoff time

- **Codex:** none
- **Claude:** this orchestrator only
- **Gemini:** 6 wiki rebuild processes (3 Gemini + 3 Claude writers)

### What the morning user sees

If everything goes well overnight: wiki rebuild done by ~06:30 CET,
Phase 4 brief signed off and parked, EPIC #1577 commented, this
handoff updated. Morning dispatch is one `delegate.py dispatch`
command away — but verify wiki rebuild finished first.

### Lessons for the next session

- **Adversarial review caught a real architectural bug** in the
  predecessor's brief. The "scoped regen on REVISE" language slipped
  past the predecessor's self-review because the North Star and
  GEMINI.md disagree on the policy. North Star says scoped regen is
  allowed; ADR-007 + `tests/test_no_rewrite_contract.py` ban it.
  Resolution: pick the strictest interpretation for the exemplar
  (fail-fast). If a future need for deterministic find/replace patches
  surfaces, that's a separate ADR.
- **Bridge channels properly threaded the discussion** — the round-3
  sign-off referenced the round-1/2 thread cleanly via the agents
  reading the file fresh. No need to repaste round-1 findings.
