# Current — Claude Session Handoff (2026-06-15)

> Router: read `docs/session-state/current.md` first (if present).
> **Latest detailed handoff: `docs/session-state/2026-06-15-claude-parallel-fanout-atlas-infra.md`** — read it in full.

> **ROLE:** main orchestrator = **infra / tooling / tech-debt / general features / integration / merge** — NOT tracks. Track issues (folk/bio/lit/seminar) are track-orchestrator-owned.

> **✅ Shipped (merged):** **#3164** (telemetry PR1, honest cost layer), **#3166** (lit-slug CI gate #2526), **#3168** (Atlas §7 wrong-sense synonyms #3116), **#3170** (Atlas §6 calque layer #3098), `3752cc3df2` (manifest regen — §7 live). Closed **#2261** (torchvision moot), **#3167** (bad agy deps). Documented **#2732** (real fix = isolate marker-pdf + resolver-lock; needs decision).

> **🔄 2nd+3rd wave ALL LANDED:** **#3177** (#2901) MERGED + source_url migration run (11,037 backfilled). **#3179** (#2882 Atlas populate) MERGED + manifest regenerated/committed (`e845b9834f`) → **antonyms(52)+phraseology(698)+etymology variant-match LIVE**, verify_manifest CLEAN. **#3178** (#1905) was already merged by another session; verified main green. Handoff threshold raised **82→88%** (`5ab70666f6`, user 2026-06-15, cost-math).

> **⚠️ OPEN ITEMS (next session):**
> - **#3197 (filed):** Atlas antonyms have a Wiktionary noise tail (`дочка→матка`, `він→ми`, `а→зет`) — needs a §7-style per-lemma sense/pedagogy filter in `_antonyms_wiktionary`, then regen. ~10/52 affected; shipped because ~80% correct + real-source, but flagged.
> - **#3195 (#3150 Atlas freshness) — HELD, do NOT merge as-is.** Faithful to my brief but the brief over-gated: fingerprint hashes vocab lemmas + `atlas` CI filter includes `vocabulary.yaml` → red-X on every content PR (advisory, non-blocking, but noisy). **Fix:** make the hard gate **lexicon-CODE-only** (drop vocab from the gating fingerprint + the CI trigger); vocab drift = orchestrator's periodic `make atlas`. Re-dispatch to codex with corrected brief (Makefile + check-script structure are good, keep them). Full refinement in PR #3195 comment.

> **🎯 Next:** #3150 (Atlas auto-freshness — HOLD until #2882 lands, shared lexicon pipeline), #2732 proper fix (needs decision), #1908, #3079, #3162. Consider filing: §6 calque note should also surface on the replacement-word page (else dormant — only `виглядати` fires today).

> ⚠️ Watch: VERIFY dispatch self-reports (agy stalled on #3167; grok #3170 citations passed MCP check). Atlas dispatches = **code-only / never commit `lexicon-manifest.json`** (orchestrator regenerates after merge). agy unreliable for fiddly resolution — route hard work to codex.

Prior handoff (superseded): `2026-06-14-claude-cursor-grok-reviewer-fixes-bakeoff.md`.
