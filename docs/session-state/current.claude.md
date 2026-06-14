# Current — Claude Session Handoff (2026-06-14)

> Router: read `docs/session-state/current.md` first (if present).
> **Latest detailed handoff: `docs/session-state/2026-06-14-claude-infra-rescope-vesum-gate-plus-fixes.md`** (read its §Addendum for the post-handoff continuation).

> **ROLE (user-corrected 2026-06-14):** main orchestrator = **infra / tooling / tech-debt / general features / integration / merge** — NOT tracks. Drive the infra backlog; track issues (folk/bio/lit/seminar) are track-orchestrator-owned.

> **🔄 IN-FLIGHT — REVIEW ON LAND (no auto-merge):** Codex dispatch `2928-heritage-fixture-ci` (#2928) — commit a small `tests/fixtures/heritage_sample.db` so `test_heritage_classifier` runs on CI (parametrize `db_path`, drop the size-gate skip). When its PR opens, verify the 5 cases PASS (not skip) and assertions are unchanged, then merge. Monitor: `/api/delegate/active` until `total=0`.

> **🎯 Next infra queue:** #3087 (route noisy wiki reviewer dims off Gemini-family), #2126 (review/review CI failing ~45s), #2732/#2261 (deps), #2279 (enforce worktree-only branch creation). #3097 slovnyk mirror = DESIGN-GATED (network; needs user sign-off). Full stack + watch-items in the dated handoff.

> **✅ Shipped this session (all merged):** #3126 (conformance gate), #3128 (synonym wrong-sense + typo), #3133 (vesum `як «X»` citation fix — unblocks folk), **#3136/#2991** (correction loop patches YAML artifacts, not just module.md — reviewed APPROVE; removed the old vesum-masking anti-pattern), **#3139/#3045** (non-lossy postmortem regen + `--check`). Closed #2997, #2368, #2991. Resolved #3094/#3098/#3116.

> ⚠️ Watch-items: #2842 core.bare flip root-cause unknown (canary live); 2 stale ADR DRAFTs (adr-008/010) need owner finalize; #2368 detached-delegate liveness uses launcher-PID (zombie under-count risk). Pre-existing local RED: `test_build_knowledge_packet_reads_wiki_and_sources` (data-dependent, not mine).

Prior handoff (superseded): `2026-06-14-claude-s6-calque-integrated-stale-server-fix-reenrich.md`.
