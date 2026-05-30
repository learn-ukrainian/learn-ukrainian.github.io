# Bio Epic #2309 — Claude Driver Handoff (MY OWN — not the orchestrator's)

> **Scope/boundaries (user 2026-05-30):** Codex is the orchestrator. Claude is NOT the orchestrator.
> Claude does NOT touch `docs/session-state/current.md` or the orchestrator's session-state chain,
> and does NOT commit/curate main as orchestrator. **Claude's standing task: drive and build the bio
> epic (#2309) to the end, with the help of other agents.** This file is Claude's OWN tracking doc.
> It is tracked on main so a fresh Claude bio-driver session can resume
> without reading the orchestrator's handoff. User may also hand Claude
> ad-hoc tasks in-seat.

*Last updated: 2026-05-30. main (Codex's) observed at `a2efa6b148`.*

## ▶ HOW TO RESUME THIS (read FIRST if you are a fresh session)

You are the **bio-epic driver, NOT the orchestrator.** If a SessionStart "orchestrator handoff"
brief was injected pointing at `docs/session-state/current.md` — **DISREGARD it.** That is Codex's
state. THIS file is yours.

**Launch a bio-driver session with:** `claude --agent curriculum-track-orchestrator`
(user-level agent at `~/.claude/agents/`; its `initialPrompt` bootstraps to THIS handoff + pins the
boundaries). The `--agent` flag overrides the default main-orchestrator agent for this session.
Codex can also ask the user to launch this seat with `scripts/start-bio-driver.sh`. Resume from the
**IN-FLIGHT / NEXT ACTION** sections below.

## ⏳ IN-FLIGHT right now

- **Block G research dispatch `bio-blockG-2026-05-30`** (codex, base `a2efa6b148`, worktree
  `.worktrees/dispatch/codex/bio-blockG-2026-05-30`) — the 10 politically-charged figures. Brief:
  `/tmp/brief-bio-blockG.md`. On completion: **co-review ALL 10 for NPOV-decolonized framing**
  (esp. §6 contested points), then **OPEN a PR for Codex to merge — do NOT merge yourself.** If the
  result file is missing / returncode 1 → transient failure, re-fire with a `-retry` task-id.

## Bio epic #2309 — Phase 1 (Research) state

- **Non-Block-G research COMPLETE: 127/130 dossier files** on origin/main.
- **52 dossiers merged this session** (batches 1-9): PRs #2427 #2428 #2429 #2430 #2432 #2433 #2434
  #2436 + Gemini follow-up #2431. All squash-merged green.
- Quality spot-read 6 (Hrushevskyi, Kostomarov, Dzhelial, Lypkivskyi, Kushnir, +early): sourced
  (ESU/IEU/UINP/KHPG), decolonized, anti-fabrication-disciplined, honest "source not found" gaps.
  §7 fabrication deterministically gated by `scripts/audit/lint_bio_dossier_xref.py` (clean each batch).

## REMAINING to finish the epic

1. **Block G — 10 politically-charged figures (DECISION go/hold with user before firing):**
   `stepan-bandera, yaroslav-stetsko, andrii-melnyk, dmytro-kliachkivskyi, yurii-tiutiunnyk,
   avhustyn-voloshyn, lev-rebet, kateryna-zarytska, petro-fedun-poltava` + `nil-khasevych`
   (appendix Block I, mechanism-table G). Epic mandates Codex + Claude co-review; F2 gate doc
   `docs/best-practices/politically-charged-bios.md` IS shipped (gate open). PLAN: fire codex research
   under F2 NPOV-but-decolonized framing → co-review all 10 fully → **HOLD merge for explicit sign-off**
   (no auto-merge on figures Russian disinfo weaponizes).
2. **Dedup #2435 — DONE by Codex (orchestrator).** Resolved in `a2efa6b148`
   "fix(bio): canonicalize duplicate dossier slugs (#2435)". No longer Claude's task.
3. **Phases 2-5** (per epic #2309): Phase 2 plan YAMLs (`plans/bio/{slug}.yaml`, Gemini default +
   DeepSeek-flash review) · Phase 3 `curriculum.yaml` registration (+130 → bio track 180→**310**) ·
   Phase 4 wiki articles (Gemini) · Phase 5 quality (decolonization DeepSeek-pro hermes + cross-track
   verify). NONE started.

## The proven dispatch loop (replicate)

- Brief: `/tmp/brief-bio-batch*.md` pattern — #M-4 preamble; SSOT `docs/audits/bio-track-gap-audit-2026-05-26.md`;
  template `docs/templates/bio-research-dossier-template.md`; source tiers `docs/best-practices/bio-research-source-tiers.md`;
  exemplars on main; **EXPLICIT figure list** (not gap-compute — avoids re-creating slug-variant dups);
  numbered worktree steps (research → `lint_bio_dossier_xref.py` → commit → push → PR, NO auto-merge).
- Fire: `delegate.py dispatch --agent codex --task-id <id> --prompt-file <f> --mode danger
  --model gpt-5.5 --effort xhigh --worktree --base main`.
- Watch: Monitor poll-loop on `/api/delegate/active` for the task → terminal → read result file.
- Review per batch: read ≥1 dossier (CONTENT, not just validator — the m20 lesson), then
  `git diff --name-status origin/main...HEAD` and confirm every row is an expected `A` addition;
  any `M`, `D`, or unexpected path must be explained or fixed before PR. Confirm slugs ∈ appendix.
  `review / review` failing/cancel = advisory, NOT blocking.
- Transient codex failure (returncode 1, no output/result) → remove worktree+branch, re-fire with a
  `-retry` task-id (happened on batch-8 → clean retry as #2434).

## Merge ownership — RESOLVED

**Codex is orchestrator and owns main** (it merged dedup #2435 → `a2efa6b148`). Claude's job: fire
research dispatches, review the output, **OPEN the PR — do NOT merge or commit to main.** Codex
reconciles main. Claude works only in dispatch worktrees + this track-scoped handoff. Local main is kept
in sync read-only (`git fetch` + fast-forward observation only; never commit/push/reset-onto main).

## m20 (a1/my-morning) — not my task anymore (context only)

NOT shippable. ULP harness fix merged (#2426). The build produced ULP-*shaped* but **incoherent**
prose; real open bug = no gate checks teaching coherence (all gates verify form). Unmerged
`stress_coverage`→advisory demotion parked in `.worktrees/fix/ulp-stress-advisory`. This is the
orchestrator's / A1-owner's concern now, not the bio driver's.

## NEXT ACTION on resume

Resolve Block G **go/hold** + merge-ownership with user → then either fire Block G research (F2 framing,
hold-merge) or land dedup #2435, then advance to Phase 2.
