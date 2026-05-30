# Bio Epic #2309 — Claude Driver Handoff (MY OWN — not the orchestrator's)

> **Scope/boundaries (user 2026-05-30):** Codex is the orchestrator. Claude is NOT the orchestrator.
> Claude does NOT touch `docs/session-state/current.md` or the orchestrator's session-state chain,
> and does NOT commit/curate main as orchestrator. **Claude's standing task: drive and build the bio
> epic (#2309) to the end, with the help of other agents.** This file is Claude's OWN tracking doc.
> It is tracked on main so a fresh Claude bio-driver session can resume
> without reading the orchestrator's handoff. User may also hand Claude
> ad-hoc tasks in-seat.

*Last updated: 2026-05-30 (Claude session: infra fixes + Phase-2 pilot + first-batch co-review). main (Codex's) observed at `2490db006e`.*

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

- **Phase 2 is RUNNING and Codex-owned.** Pilot `dmytro-chyzhevskyi`/bio-222 proven (PR #2453).
  First scaled batch MERGED — #2457 Semenko (bio-181), #2458 Svidzinskyi (bio-182), #2456
  Drai-Khmara (bio-183). **Claude audited that batch: PASS** (validated clean, decolonized,
  anti-hagiographic, sourced — Soviet terror named with case numbers/dates).
- **Next batch (Codex's to fire):** bio-184 Mykola Voronyi, bio-185 Mykhailo Yalovyi, bio-186
  Hryhorii Epik.
- **⚠ DIVISION OF LABOR (settled 2026-05-30):** Codex GENERATES + MERGES Phase-2 plans (writer +
  DeepSeek-flash/Gemini review, both of which DO have the `sources` MCP). **Claude does NOT fire
  Phase-2 plan dispatches** — that caused a duplicate-PR collision on the pilot (#2453 vs my closed
  #2455). Claude's Phase-2 role is **co-reviewer on batches where stakes warrant** (politically
  charged figures, or when a second adversarial pass plausibly catches what Codex's reviewers
  miss), gated by a "did it catch anything?" bar — not run by default.
- Allocation rule (still current): the 130 version-locked audit-appendix slugs get `bio-181`
  through `bio-310` in appendix order, from `docs/bio-epic/phase-2-sequence-allocation.yaml`. Seven
  research dossiers already map to existing plans; do not create a duplicate plan for
  `levko-lukianenko` (legacy plan is `levko-lukyanenko` / `bio-134`).

## Bio epic #2309 — Phase 1 (Research) state

- **Phase 1 research COMPLETE: 137/137 dossier files** on origin/main. This is the 130 audit
  additions plus 7 research dossiers that document already-existing BIO plans.
- **52 dossiers merged this session** (batches 1-9): PRs #2427 #2428 #2429 #2430 #2432 #2433 #2434
  #2436 + Gemini follow-up #2431. All squash-merged green.
- **Block G research MERGED:** PR #2441 added the 10 F2/politically-charged dossier files after
  Claude+Codex co-review and Codex/orchestrator sign-off.
- Quality spot-read 6 (Hrushevskyi, Kostomarov, Dzhelial, Lypkivskyi, Kushnir, +early): sourced
  (ESU/IEU/UINP/KHPG), decolonized, anti-fabrication-disciplined, honest "source not found" gaps.
  §7 fabrication deterministically gated by `scripts/audit/lint_bio_dossier_xref.py` (clean each batch).

## REMAINING to finish the epic

1. **Block G — 10 politically-charged figures: DONE / MERGED (#2441).**
   `stepan-bandera, yaroslav-stetsko, andrii-melnyk, dmytro-kliachkivskyi, yurii-tiutiunnyk,
   avhustyn-voloshyn, lev-rebet, kateryna-zarytska, petro-fedun-poltava` + `nil-khasevych`
   (appendix Block I, mechanism-table G) are now on `main`.
2. **Dedup #2435 — DONE by Codex (orchestrator).** Resolved in `a2efa6b148`
   "fix(bio): canonicalize duplicate dossier slugs (#2435)". No longer Claude's task.
3. **Phases 2-5** (per epic #2309): Phase 2 plan YAMLs (`plans/bio/{slug}.yaml`, Gemini default +
   DeepSeek-flash review) must use `docs/bio-epic/phase-2-sequence-allocation.yaml` for `module` and
   `sequence` · Phase 3 `curriculum.yaml` registration (+130 -> bio track 180->**310**) · Phase 4 wiki
   articles (Gemini) · Phase 5 quality (decolonization DeepSeek-pro hermes + cross-track verify).

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

## Lessons from the 2026-05-30 Claude session (don't repeat)

1. **CHECK FOR CONCURRENT ORCHESTRATOR WORK BEFORE FIRING.** Before any dispatch on shared/epic
   territory: `gh pr list --state open` + `curl /api/delegate/active` + `git worktree list` for the
   SAME item. Two collisions this session from skipping this — the #2440 agent-file dup and the
   chyzhevskyi pilot dup (#2455, closed). Codex drives Phase-2 generation; assume it may already be
   on the obvious next item.
2. **VERIFY CAPABILITY/BEHAVIOR CLAIMS BEFORE STATING THEM (#M-4).** Two wrong assertions this
   session: a phantom "gemini-dispatch bug" (#2454 — actually duplicate-reaping of the orchestrator's
   concurrent run) and "DeepSeek/Gemini lack the `sources` MCP" (false — `.mcp.json`,
   `.gemini/settings.json`, MEMORY #M0 all show they have it). Run the tool before claiming.

## NEXT ACTION on resume

Phase 2 is Codex-owned and running; **do NOT fire Phase-2 plan dispatches** (collision risk — see
Division of Labor above). Claude's resume options, in order:
1. If a new Phase-2 batch has merged since this handoff, **co-review it** (validate + framing
   spot-read; escalate only if it catches something) — start with Codex's next batch
   bio-184/185/186 (Voronyi/Yalovyi/Epik).
2. Otherwise await user direction or an explicit co-review/ad-hoc assignment.

Claude still opens PRs and never merges/commits to main; Codex owns main merges + Phase-3
curriculum registration. Open follow-ups Claude filed: #2451 (4 sub-1200-word dossiers),
#2454 (duplicate-dispatch observability).
