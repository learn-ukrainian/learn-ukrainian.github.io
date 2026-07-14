# Current — claude-atlas role handoff (durable layer)

> Role: atlas/practice-hub lane driver (umbrella #4387).
> Launch: `./start-claude.sh --agent curriculum-orchestrator --epic atlas`; never self-assign "main orchestrator".
> Session-layer SSOT (gitignored, richest detail incl. BINDING user orders): `.claude/atlas-epic/CLAUDE-DRIVER-HANDOFF.md`.
> Thread rollover packets: `.agent/thread-rollovers/claude-atlas/`.

## State as of 2026-07-14 (~23:55Z session end)

- **CRITICAL IN-FLIGHT**: a detached grow run survives the session (pid + worktree + log recorded in the
  driver handoff). On its exit: promote via the hardened machinery (#5172 — anchor-fill at promotion),
  then ONE combined publish through the #5138 gate (expansion + 195 verified anchors #5145/#5182 +
  attribution migration #5166) → pointer-flip PR → live canaries.
- **Shipped today (atlas lane)**: both user-reported bugs (matching render #5164 — CSS never shipped, root-caused;
  8k-words → expansion in flight); УМІФ source-attribution guideline (#5162 doc, #5166 fail-closed impl,
  #5163 closes at the publish); anchors 196→195+1 abstention (three-seat, heritage-defense precedent
  «світлина» — СУМ-20 modern beats СУМ-11 Soviet marks); cloze 22→52 reviewed A1 (#5183); review-queue
  machinery live (batch-0 94/6, reject-rules R1); entry-model epic STARTED (#5184 p1 merged, byte-identical).
- **Behavioral orders (BINDING, in driver handoff header)**: UI testing never inline — delegate whole;
  hard-bug diagnosis stays inline, fixes route out; no idling — keep all lanes loaded during waits.
- **Lane health**: glm ask lane dead (#5091 datapoint); cursor dies post-push on GH secondary limits
  (#5146) — verify its pushed work yourself; deepseek stalls → grok-build failover; SERIALIZE
  fingerprint-carrying lexicon PRs (#5147).
- **Queue order**: (1) grow→promote→publish arc; (2) review-queue batch-1 (add UA-GEC-count +
  СУМ-11-marking pre-filters per calibration lessons); (3) #4223/#4222 next batches; (4) entry-model
  p2 = 336 thin-page redirects (recommendation given, user nod pending); (5) #4384 backend epic.
