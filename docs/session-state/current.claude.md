# Current — Claude Session Handoff (2026-06-15)

> Router: read `docs/session-state/current.md` first (if present).
> **Latest detailed handoff: `docs/session-state/2026-06-15-claude-parallel-fanout-atlas-infra.md`** — read it in full.

> **ROLE:** main orchestrator = **infra / tooling / tech-debt / general features / integration / merge** — NOT tracks. Track issues (folk/bio/lit/seminar) are track-orchestrator-owned.

> **✅ Shipped (merged):** **#3164** (telemetry PR1, honest cost layer), **#3166** (lit-slug CI gate #2526), **#3168** (Atlas §7 wrong-sense synonyms #3116), **#3170** (Atlas §6 calque layer #3098), `3752cc3df2` (manifest regen — §7 live). Closed **#2261** (torchvision moot), **#3167** (bad agy deps). Documented **#2732** (real fix = isolate marker-pdf + resolver-lock; needs decision).

> **🔄 IN FLIGHT (3 dispatches, Monitor `bvwp5jsuh`):** `atlas-populate-2882` (codex #2882), `replay-suite-1905` (codex #1905), `literary-srcurl-2901` (grok-build #2901). **Review-on-land protocol + the post-Atlas-merge manifest-regen step are in the detailed handoff** — follow them.

> **🎯 Next:** #3150 (Atlas auto-freshness — HOLD until #2882 lands, shared lexicon pipeline), #2732 proper fix (needs decision), #1908, #3079, #3162. Consider filing: §6 calque note should also surface on the replacement-word page (else dormant — only `виглядати` fires today).

> ⚠️ Watch: VERIFY dispatch self-reports (agy stalled on #3167; grok #3170 citations passed MCP check). Atlas dispatches = **code-only / never commit `lexicon-manifest.json`** (orchestrator regenerates after merge). agy unreliable for fiddly resolution — route hard work to codex.

Prior handoff (superseded): `2026-06-14-claude-cursor-grok-reviewer-fixes-bakeoff.md`.
