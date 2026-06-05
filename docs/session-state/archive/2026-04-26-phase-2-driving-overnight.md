# Session Handoff — 2026-04-26 overnight (Phase 0 closed, Phase 2 dispatched)

> **State:** EPIC #1577 Phase 0 closed and committed. Wiki content
> snapshot landed as the diff baseline before user-initiated wiki
> rebuild. User going to sleep; this session continues as orchestrator.
> Phase 2 (config audit) being dispatched to Codex per the EPIC plan
> the user explicitly endorsed ("we have a plan. drive it pls").

---

## What's on main (7 unpushed commits, push pending)

```
ebe1a89b3f  fix(sources-db): file-size primary guard + recovery runbook (#1563)  ← Codex parallel
0331cb7b84  docs(session): land parallel-session handoffs + finding-normalizer telemetry
3db11f4828  fix(wiki): file-size guard in _db_is_populated to prevent sources.db wipe (#1563)
1194b95eeb  content(wiki): snapshot pre-rebuild — 1137 files baseline for diff against new pipeline
3db7c11dc1  chore(gitignore): exclude db backups, diff artifacts; untrack corpus_audit reports
de97c45572  docs(phase-0): land North Star + Lesson Contract — EPIC #1577 #1578
(this session also writes one more handoff commit before push)
```

This session pushes all 7 to `origin/main` immediately after writing
this handoff so nothing is lost if anything crashes overnight.

## What was accomplished this session (2026-04-25 evening → 2026-04-26 early morning)

### Phase 0 — North Star + Lesson Contract (#1578 CLOSED)

Two documents drafted, panel-reviewed, and shipped:

- **`docs/north-star.md`** (422 lines) — WHO/WHY/HOW/VOICE/SHIPPABLE/WRONG.
  Reframes A1+A2+B1 as the L2 escalator (the seminars are the
  destination); pins B1+ at 100 % Ukrainian; Словник (Tab 2) is the
  ONLY sanctioned English at B1+; flags `scripts/config.py`
  IMMERSION_POLICIES B1 bands as stale (cleanup → #1582).

- **`docs/lesson-contract.md`** (446 lines) — 1:1 component map across
  4 tabs (Урок / Словник / Вправи / Ресурси). Activity matrix sourced
  directly from `docs/best-practices/activity-pedagogy.md`. Tab 2
  stays slim per EPIC #1581. 7 panel-resolved policies are now binding
  contract.

Both signed off by Codex + Gemini in `architecture` channel thread
`6de2be4789394536abdb6356cd5bb006` (round 2, both `[AGREE]`).

`scripts/build/phases/v6-write.md` v2.6.0 — `{NORTH_STAR}` +
`{LESSON_CONTRACT}` placeholder injection added at the top of the
writer prompt (AC-3 proof for #1578). Substitution code lands in
Phase 3 lesson schema work.

### Side EPICs filed during Phase 0

- **#1580** — Kaikki English-Wiktionary etymology ingest. Repurposed
  as data sub-task of #1581.
- **#1581** — EPIC: site-wide `/dictionary/{lemma}/` section
  aggregating 10 source dictionaries (9 existing + Ukrainian
  Wiktionary). Inspired by motî iOS app — verified motî has zero
  Slavic-language processing; we strictly dominate motî for Ukrainian
  on every dimension once #1581 ships.
- **#1582** — Phase 2 sub-issue: `scripts/config.py` IMMERSION_POLICIES
  B1 cleanup (delete `b1-m01-05`, collapse `b1-core` to 100 %).

### Git hygiene (pre-wiki-rebuild diff baseline)

Checkpoint commits before user-initiated wiki rebuild:

- `.gitignore` — added `data/*.db.bak-*`, `/*.diff`, `/*.patch`
  patterns; renamed `data/alona-lessons/` → `data/native-reviewer-lessons/`
  on disk to match existing role-anonymous gitignore pattern (privacy
  rule + saved 113 MB from accidental commit risk).
- Wiki content snapshot — 1137 files / +83 K lines preserved as the
  pre-rebuild baseline. Every regenerated wiki article will diff
  cleanly against its pre-reboot version.
- Session-state files — 4 new handoffs from parallel sessions landed;
  `current.md` shrunk from 388 → ~50 lines as a multi-agent index.
- `scripts/build/finding-normalizer-growth.yaml` — running telemetry
  preserved.

### #1582 → folded into broader Phase 2 audit

The user pushed back on my "Phase 3 first" recommendation: *"if you
delay phase 2 it might bite later."* Correct — Phase 3 lesson-schema
work would consume `LEVEL_CONFIG`, `IMMERSION_POLICIES`,
`LEVEL_THRESHOLDS`, `ACTIVITY_CONFIGS`, `TRACK_CONFIG`,
`PROPER_NAME_WHITELIST`, every of which is suspect of V6-era drift
beyond just the #1582 B1 bands. Phase 2 must run first.

## What's ACTIVELY IN PROGRESS (do not touch)

### User-initiated work — in flight

- **Wiki rebuild** — user starts rebuilding `wiki/` content right after
  this handoff lands. The 1137-file snapshot at `1194b95eeb` is the
  baseline. Wiki rebuild is OUT of this session's scope; it's the
  user's work + parallel agent (likely Gemini cron). DO NOT touch
  `wiki/` for any reason this session.

### This session's overnight execution (in flight after handoff lands)

- **Phase 2 sub-issue filing under EPIC #1577** — about to be filed.
- **Codex dispatch — Phase 2 config audit** — about to be dispatched.
  Worktree: `.worktrees/codex-phase-2-config-audit`. Brief: read
  Phase 0 docs as policy authority, audit every config table in
  `scripts/config.py` + `scripts/audit/config.py` +
  `scripts/common/thresholds.py` against committed Phase 0 policy,
  emit fixes inline where mechanical, file findings as sub-issues
  where judgment-calls. Includes #1582's B1 cleanup as one fix.
- **Monitoring** — `ab channel watch architecture` and inbox tail
  via Monitor tool. No polling.

### Other parallel agent sessions (do NOT clobber)

- **Orchestration session** — owner of
  `docs/session-state/2026-04-25-orchestration-final-with-data.md`,
  EPIC #1550 a1/1 verification (Unit 6 A/B). Now landed on main.
  Codex (parallel agent identity) committed `ebe1a89b3f` for #1563
  while this session was working on Phase 0; suggests their session
  is still active or just finished.
- **Wiki agent session** — owner of
  `docs/session-state/2026-04-25-wiki-retrieval-overhaul-1553.md` and
  `2026-04-25-bakeoff-merged-pre-cold-encode.md`. Wiki rebuild work
  upstream of user's manual rebuild starting now.

## What this session WILL do overnight (ordered, AGGRESSIVE)

Per user direction (2026-04-25 22:50 CET): *"not just phase 2 but as
much as you can"*. Run as much of the EPIC as possible overnight via
parallel agent dispatches; orchestrate, integrate, merge, advance.
Hard cap: dispatch budget per MEMORY #0 (max 2 Codex + 2 Claude in
flight; Gemini uncapped).

### Push first, then parallel dispatches

1. **Push all 7+ commits to `origin/main` immediately.** Preserve
   work before anything else.

### Wave 1 — Phase 2 audit (Codex, dispatched first)

2. **File Phase 2 sub-issue under EPIC #1577** — full config audit
   scope (broader than #1582), with #1582 as one closeout sub-task.
3. **Dispatch Codex for Phase 2 audit** via
   `delegate.py dispatch --agent codex --task-id phase-2-config-audit
   --worktree .worktrees/codex-phase-2-config-audit --mode danger
   --prompt-file <brief>`. Mandatory worktree.
4. **Monitor via Monitor tool** — no polling.

### Wave 2 — Phase 3 lesson schema (in parallel with Wave 1)

5. **Draft Phase 3 lesson schema YAML inline** while Codex runs
   Wave 1. Phase 3 = formalize `{NORTH_STAR}` + `{LESSON_CONTRACT}`
   prompt-template substitution mechanism + per-component prop
   schemas (the data shape every Starlight component consumes).
   Inline because architecture authoring is Claude's strength and
   the work doesn't conflict with Codex's audit (different files).
6. **File Phase 3 sub-issue under EPIC #1577** with the design.
7. **3-agent review on the Phase 3 design** via `ab discuss
   architecture --with codex,gemini --max-rounds 2`. Run in
   background; wait for both `[AGREE]` (or apply findings).

### Wave 3 — Phase 4 exemplar setup (after Phase 2 + Phase 3 done)

8. **Build the Phase 4 exemplar pipeline brief** — A1/20 `my-morning`
   per the EPIC's chosen exemplar slug. Brief specifies:
   - Pipeline = linear, fail-fast (no V6 convergence loop)
   - Writer prompt = v2.6.0+ with `{NORTH_STAR}` + `{LESSON_CONTRACT}`
     substituted live
   - Python QG = the rules from Lesson Contract §5
   - LLM QG = single-pass per dim, MIN aggregator, no rewrite
9. **Dispatch the Phase 4 exemplar build** if Wave 1 + Wave 2 land
   clean and dispatch budget allows.
10. **Monitor and integrate findings** from each wave as `<task-notification>`s arrive.

### Throughout — handoff hygiene

11. **Update this handoff** as each wave lands (status table at top:
    Phase 2 status, Phase 3 status, Phase 4 status).
12. **Write a morning handoff** before context approaches 400 K
    threshold. Diary handoff at
    `docs/session-state/2026-04-26-morning-handoff.md`.

### Decision tree for things going sideways

- **Codex Wave 1 fails / asks questions:** respond via
  `ab post architecture codex "..."`, do NOT solo-decide; if blocking
  for >2 hr with no resolution, file as a Phase 2 follow-up issue
  with the unresolved question and proceed to Wave 2.
- **Codex PR has CI failures:** investigate root cause → push fix
  to the Codex worktree branch OR file follow-up issue. Do not merge
  red CI.
- **Phase 3 design rejected by panel:** apply findings, redraft, one
  more round. If still rejected, file as design-debate issue and
  hand back to user.
- **Dispatch budget hit (2 Codex in flight):** queue further work as
  briefs in scratch files; do not fire-and-await sequentially because
  it wastes wall time.
- **Context cap approaching 400 K:** write morning handoff
  IMMEDIATELY at landing point; end session. The next session starts
  fresh with this handoff + the morning handoff.

## Anti-checklist (this session must NOT)

1. **NOT touch `wiki/`** — user is rebuilding it in parallel.
2. **NOT touch the `_archive/`, `data/`, `testbed/reference/` trees** —
   sacred reference state per salvage manifest §1 KEEP.
3. **NOT modify plans** in `curriculum/l2-uk-en/plans/` — sacred per
   EPIC #1577 critical invariants §1.
4. **NOT do solo architecture decisions** — Phase 2 audit Codex
   dispatches its own findings; for any architectural call, escalate
   to `ab discuss architecture` for 3-agent. Per anti-checklist #1.
5. **NOT use `git add -A`** — only specific filenames, every commit.
6. **NOT push without first verifying** the working tree state.
7. **NOT use `--no-verify` on commits** — pre-commit hooks must run.
8. **NOT spin > 2 Codex dispatches in flight** — DISPATCH CAP per
   MEMORY #0.
9. **NOT poll** the dispatch with sleep loops or ScheduleWakeup —
   Monitor tool only.
10. **NOT amend commits** — always new commits per critical-rules.md.
11. **NOT touch `data/native-reviewer-lessons/`** — IP-sensitive
    teacher material; gitignored but on disk.
12. **NOT name the user's two private teachers anywhere committed** —
    salvage manifest §1, MEMORY rule.

## Critical context for the morning session

- **EPIC #1577 phases: 0 ✅ done | 1 ✅ done | 2 in flight tonight | 3 next.**
- **Plans are sacred.** No phase touches plans.
- **B1+ = 100 % Ukrainian.** Словник only English. Period.
- **A1+A2+B1 is the L2 escalator; the seminars are the destination.**
- **Codex (parallel session) was active near midnight 2026-04-26.**
  If overnight Codex dispatches conflict with their parallel work,
  coordinate via `ab post architecture codex "..."`.
- **Wiki rebuild is happening in parallel.** Wiki tree IS in
  flux while we work on config audit. Don't read wiki content as
  authoritative for anything Phase 2 needs.

## Channel + thread references

- Phase 0 sign-off thread: `architecture` `6de2be4789394536abdb6356cd5bb006`
- Salvage manifest sign-off thread: `architecture` `e7e27b8e...`
- Reboot decision threads: `architecture` `0b748a12cadc...`,
  `d36b068bcdee...`
- Phase 2 dispatch (about to be filed): channel `architecture`,
  thread auto-assigned at dispatch time

## Files in flight when this handoff was written

- `docs/session-state/2026-04-26-phase-2-driving-overnight.md` (this file)
- `docs/session-state/current.md` — to be updated with new row
  pointing here

## Cold-start protocol for the next session

1. Read this handoff fully.
2. `gh issue view 1577` — EPIC status.
3. `gh issue view <Phase-2-sub-issue>` — see comment trail for what
   Codex did.
4. `git log --oneline -15` — see what landed overnight.
5. `gh pr list --state all --limit 10` — see Codex's Phase 2 PR (if
   merged) or in-flight PRs.
6. `ab channel tail architecture -n 30` — recent agent discussion.
7. Continue per the plan: Phase 3 (lesson schema YAML) starts when
   Phase 2 audit closes.
