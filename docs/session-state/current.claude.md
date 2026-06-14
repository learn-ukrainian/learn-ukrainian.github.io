# Current — Claude Session Handoff (2026-06-14)

> Router: read `docs/session-state/current.md` first (if present).
> **Latest detailed handoff: `docs/session-state/2026-06-14-claude-infra-rescope-vesum-gate-plus-fixes.md`** — read top-to-bottom.

> **ROLE (user-corrected mid-session 2026-06-14):** main orchestrator = **infra / tooling / tech-debt / general features / integration / merge** — NOT tracks. Drive the infra backlog; treat track issues (folk/bio/lit/seminar) as track-orchestrator-owned.

> **🔄 IN-FLIGHT — REVIEW FIRST:** Codex dispatch `2991-vesum-correction-yaml` (HIGH) — extend the V7 correction loop to patch `activities/vocabulary/resources.yaml`, not just `module.md`. When it opens a PR (no auto-merge), review the attribution + rollback/teeth guarantees + ADR-007 invariant, then merge if clean. Monitor: `/api/delegate/active` until `total=0`.

> **🎯 Then (P1, both bounded):** #3045 (`check_postmortems --regenerate-index` lossy), #2928 (`heritage_classifier` tests skip on CI). Full stack + watch-items in the dated handoff.

> **✅ Shipped this session:** #3126 (conformance gate), #3128 (synonym wrong-sense + typo), #3133 (vesum `як «X»` citation-frame fix — unblocks folk). Closed #2997, #2368. Resolved #3094/#3098/#3116.

Prior handoff (superseded): `2026-06-14-claude-s6-calque-integrated-stale-server-fix-reenrich.md`.
