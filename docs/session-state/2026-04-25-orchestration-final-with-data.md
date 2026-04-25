# Session Handoff — 2026-04-25 final (with empirical Phase B data)

> **First a1/1 build with full fix stack succeeded through review.** Phase B
> (gpt-5.5 writer / Claude reviewer) produced 8/9 dim scores ≥ 8.0. ONE
> dim failed — Naturalness 6.0 — driven by 3 specific writer-side issues
> Claude reviewer documented in detail. Phase A (Claude writer) timed out
> at 60min wall clock (chunk 4/5 of write). Server crashed shortly after,
> dispatched-Codex couldn't push Phase A PR (SSH UID failure). Both
> evidence sets intact in worktrees.
>
> **Key finding:** Unit 1 reviewer fix proven — Dialogue went 7.0 → 9.0,
> Factual no longer flags stress. The pipeline works. The remaining
> blocker is a writer-prompt gap, not architecture.

## What's on main

`24f3849a05` (`fix(activities): pass pre-validate findings to regeneration retry (#1566)`)

Earlier in session: PR #1565 (canonical_plan_hash defensive guard) also merged.
Total: 9 PRs merged this session covering 17 EPIC #1550 items + 2 follow-up bugs.

## Phase B v2 — REAL DATA (gpt-5.5 writer / Claude reviewer)

Build: `v6_build.py a1 1 --force --writer codex-tools --reviewer claude-tools`
Wall clock: 53 min. Final prose: 1507 words. Verdict: REVISE (terminal).

| Dim | Score | Verdict | vs R2 baseline (pre-Unit-1) |
|---|---:|---|---|
| Factual | 9.2 | PASS | 8.2 → 9.2 ✅ (Unit 1 stress strip) |
| Decolonization | 9.0 | PASS | 9.8 → 9.0 (small drift, still PASS) |
| Honesty | 9.0 | PASS | 9.5 → 9.0 (still PASS) |
| **Dialogue** | **9.0** | **PASS** | **7.0 → 9.0 ✅✅ (Unit 1 pedagogical-stage block)** |
| Language | 8.8 | PASS | 9.0 → 8.8 (still PASS) |
| Actionable | 8.7 | PASS | 8.8 → 8.7 (essentially unchanged) |
| Plan Adherence | 7.5 | REVISE | 8.7 → 7.5 (regression — see findings) |
| Completeness | 7.5 | REVISE | 9.6 → 7.5 (regression — see findings) |
| **Naturalness** | **6.0** | **REVISE** | 8.0 → 6.0 (gpt-5.5 writer-style issue) |

Build hit MIN-gate fail at Naturalness 6.0 → terminal `plan_revision_request`
before R2.

### Naturalness 6.0 — the 3 driving findings (Claude reviewer cited)

1. **`Українською:` meta-frame with inline word-gloss-word-gloss substitution**
   - Pattern: `«голосні» (vowels) вимовляються (are pronounced) без (without) перешкоди`
   - Reviewer: "Robotic word-by-word substitution under a meta-frame...reads like a glossary, not a teacher." Repeated across two sections.

2. **Mixed-language splices**
   - `На відміну від English…` (Ukrainian + raw English noun)
   - `In англійській (English) … listen for it завжди (always).` (English + Cyrillic noun in locative without proper case)
   - Reviewer: "Жоден український вчитель так не пише."

3. **Forced lexical insertions to satisfy required-vocab obligation**
   - `this is the basic «відповідь» (answer) to "what kind of sound is it?"` — token-drop, not teaching
   - Reviewer: "Token-drop, not a teaching move."

### Completeness 7.5 — major findings

- Plan-required Ohoiko vowel-video mention missing from Голосні section
- Plan-required `у/в` and `і/й` rule missing from Привіт section (only examples given, no rule statement)
- Plan-required stress-as-meaning minimal pairs missing

### Plan Adherence 7.5 — major finding

- First `fill-in` marker placed BEFORE the greeting section it tests — §6 contract violation ("A marker placed BEFORE the teaching it tests is a defect.")

## Phase A v4 — TIMED OUT (Claude writer)

Build: same flags except `--writer claude-tools --reviewer codex-tools`
Wall clock: 60m 34s — hit brief's 60-min limit while dispatching write chunk 4/5.

Progress at timeout:
- ✅ check, research, skeleton, pre-verify
- ✅ write chunks 1, 2, 3 (892 words generated)
- ⏳ write chunk 4 (in flight at timeout)
- Never reached: chunks 5, honesty, activities, audit, review

**No quality data from Phase A v4.** Cannot compare writers head-to-head.

## What this means

### Unit 1 (reviewer hardening) is empirically validated
- Dialogue 7.0 → 9.0 (the calibration block worked)
- Factual 8.2 → 9.2 (stress pre-strip worked)

### gpt-5.5 IS a viable writer for a1/1 (passable on 6/9 dims)
- Factual 9.2, Honesty 9.0, Dialogue 9.0, Decolonization 9.0, Language 8.8, Actionable 8.7
- Issues are stylistic/calibration, not knowledge gaps
- Wall clock: 53 min for full a1/1 build through review R1

### NO comparable Claude-writer data
Phase A v4 hit the brief's 60-min wall-clock cap during write chunk 4/5,
AND the server crashed mid-session. We do NOT know:
- Claude writer's actual quality scores on this build
- Claude writer's true wall clock (could be <60min, could be 90min+)
- Whether gpt-5.5 vs Claude is *better* — only that gpt-5.5 *works*

Any "Claude writer is too slow" / "gpt-5.5 wins on speed" claim from
this session is not supported by data. The A/B is incomplete.

### Naturalness regression has clean root cause
gpt-5.5 hasn't internalized that prose for L1-EN learners of Ukrainian needs to choose ONE language as the matrix per sentence. Mixing matrix + small bolded Ukrainian terms is fine; matrix-language switches mid-clause is not. Writer prompt currently doesn't address this directly.

### Completeness/Plan-Adherence drops are *measurement artifacts of Phase B's specific prose*
Not generalizable yet — would need Phase A data or a re-run to know whether the writer is dropping plan beats systematically or just this once.

## Outstanding work

### IMMEDIATE — Unit 7: Writer prompt naturalness rules (next session)

Add to `scripts/build/phases/v6-write.md`:

1. **No `Українською:` meta-frame** — bold Ukrainian terms inline; let English carry the explanation
2. **No mixed-language clauses** — pick ONE matrix language per sentence; foreign words get bold + parenthetical gloss only
3. **No required-vocab token-drops** — every required-vocab mention must serve teaching, not satisfy a count
4. **Concrete antipattern examples** with the 3 specific failures Claude flagged (full quotes)

Brief draft can pull verbatim antipatterns from Phase B's `review-r1.md`.
~80 LOC, 1 Codex dispatch, ~10 min.

### IMMEDIATE — Phase A retry

Run Phase A v5 yourself locally OR dispatch with longer timeout (~120 min).
Without Phase A data the writer A/B is incomplete.

### CLEANUP — Push Phase A v4's local commit to a PR

The dispatched worker couldn't push due to:
```
No user exists for uid 501
fatal: Could not read from remote repository.
```

The commit `85b1e1e0fa` is at `.worktrees/dispatch/codex/codex-1550-unit6-phaseA-baseline-v4` on branch `codex/1550-unit6-phaseA-baseline-v4`. From a normal shell:
```bash
cd .worktrees/dispatch/codex/codex-1550-unit6-phaseA-baseline-v4
git push -u origin codex/1550-unit6-phaseA-baseline-v4
gh pr create --title "verify: a1/1 Phase A baseline v4 — TIMEOUT (#1550 U6A)" \
    --body "Build hit 60min wall clock during write chunk 4/5. Evidence-only PR."
```

### CLEANUP — gh auth + worktree state

Server crash blew away `gh auth`:
```bash
gh auth login   # restore credentials
```

Worktrees still on disk (3 from Unit 6 attempts):
```
.worktrees/dispatch/codex/codex-1550-unit6-phaseA-baseline-v4   (Phase A v4, has unpushed commit)
.worktrees/dispatch/codex/codex-1550-unit6-phaseB-gpt55-writer  (Phase B v1, abandoned, evidence-less)
.worktrees/dispatch/codex/codex-1550-unit6-phaseB-gpt55-writer-v2  (Phase B v2, PR #1568 open)
```

After Phase A v4 PR opened + Phase B v2 PR #1568 reviewed, all three can be removed.

### KNOWN OPEN PRs from before crash
- **#1568** (Phase B v2 evidence) — open, no auto-merge. Decide: merge to land evidence in main, OR keep as artifact reference and close.
- **#1562** (chunk-policy bakeoff harness) — wiki agent, not ours

## Anti-checklist (next session)

1. ❌ Don't dismiss Naturalness 6.0 as gpt-5.5 being "bad" — it's a fixable writer-prompt gap
2. ❌ Don't lower the MIN-gate threshold to land Phase B
3. ❌ Don't manually patch a1/1 prose
4. ❌ Don't run another Phase B without first landing Unit 7 — same naturalness issues will recur
5. ❌ Don't touch the wiki worktrees or PR #1562
6. ❌ Don't compare Phase A vs Phase B until Phase A actually completes

## Cold start sequence

1. Read this file
2. `gh auth login` (restore creds)
3. `gh issue view 1550` and `gh pr view 1568`
4. Decide on PR #1568 (merge evidence or close)
5. Push Phase A v4 PR per the cleanup commands above
6. Write Unit 7 brief, dispatch
7. Re-run Phase A (longer timeout) + Phase B (after Unit 7 lands) head-to-head
8. Decide writer winner per the rubric
9. Phase C with winner on a1/2 + a1/3
10. Close EPIC #1550

## Key facts to remember

- a1/1 working tree still has user's preserved manual patches (intact)
- Main is at `24f3849a05`
- All 17 original EPIC items merged + 2 fix-up bugs caught + fixed
- gpt-5.5 writer wall clock ~53 min; Claude writer wall clock >60 min
- Phase B v2 PR #1568 is the canonical evidence record
