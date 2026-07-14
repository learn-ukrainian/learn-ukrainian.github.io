# Current — claude-atlas role handoff (durable layer)

> Role: atlas/practice-hub lane driver (umbrella #4387).
> Launch: `./start-claude.sh --agent curriculum-orchestrator --epic atlas` — the
> SessionStart banner binds the lane (PR #5074); never self-assign "main orchestrator".
> Session-layer SSOT (gitignored, richest detail): `.claude/atlas-epic/CLAUDE-DRIVER-HANDOFF.md`.
> Thread rollover packets: `.agent/thread-rollovers/claude-atlas/` (strict continuity protocol).

## State as of 2026-07-14 (~15:45Z)

- **Anchor release SHIPPED + LIVE-verified**: 115 three-seat-verified EN anchors published
  through the #5138 richness gate (its first production run; 158→43 gloss-less); pointer flip
  #5149 merged; live canary косуля→'roe deer' curl-verified. #5133/#4515/#4383/#5082/#5077 CLOSED.
- **Practice Zone**: all #4383 ACs met (paronym mode surfaced #5115, thin-deck CI warnings,
  coverage table #5117). Fill tracks: #4506 (paronym), heritage calques.
- **Intake machinery merged**: #5136 (curriculum, phase-1: 754 auto / 19,337 review / 5,416 reject)
  + #5141 (Ohoiko adapter, family-neutral core, parity-tested). BOTH epics await next phases:
  #4222 review-queue triage (two design asks pending in bridge: task-ids 4222-triage-design +
  4222-triage-design-grok — READ REPLIES via `ab asks` before designing); #4223 phase-2 = the
  actual private-corpus extraction run — MAIN CHECKOUT ONLY (dispatch worktrees can't see
  docs/references/private/), CLI: `python -m scripts.lexicon.ohoiko_atlas_intake` (fail-closed).
- **43 anchor nulls remain** (documented NULL-OK in data/lexicon/anchor_curation_worksheet.yaml)
  — next curation round = translation-authoring from СУМ-11 senses via the proven three-seat
  protocol; they fail closed at publish until then.
- **Hard-won session mechanics**: fingerprint-sidecar PRs serially conflict (#5147 — until fixed,
  SERIALIZE lexicon PRs, rebase+regen after each merge); cursor workers die on GH secondary
  limits post-push (#5146 — verify their pushed work yourself); no full-manifest enrich on 16GB
  machines (targeted runs only); delegate worktree nesting guard (#5127); venv cross-repo
  contamination tripwire (#5134); deepseek stalls → grok-build failover works.
