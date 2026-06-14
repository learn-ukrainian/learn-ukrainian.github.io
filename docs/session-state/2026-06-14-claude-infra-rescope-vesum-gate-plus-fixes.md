# Claude session handoff — 2026-06-14 (role re-scoped to INFRA backlog · vesum citation-gate fix shipped · #2991 dispatched)

> Router: `current.md` → `current.claude.md` → this. Read top-to-bottom.
> **Next session's first job:** review the in-flight Codex PR for **#2991** (correction-loop YAML artifacts) when it lands — see §In-flight.

## TL;DR
- **ROLE CORRECTION (user, mid-session):** main orchestrator = **infra / tooling / tech-debt / general features / integration / merge** — NOT tracks. Tracks (folk/bio/lit/seminar, incl. all `lane:bio owned-by-claude` issues) are track-orchestrator-owned. I had tunnel-visioned on ~5 cold-start lexicon issues and prematurely declared "done"; the user (correctly) pointed at the large infra backlog I wasn't driving. This session pivoted to driving that backlog.
- **Shipped to main:** #3126 (conformance gate in verify_manifest), #3128 (synonym wrong-sense + etym typo), **#3133 (vesum `як «X»` citation-frame fix — unblocks folk decolonization prose)**.
- **Closed:** #2997 (blockquote exemption verified active for folk), #2368 (delegate-active/orient unified — divergence gone).
- **Resolved-by-investigation:** #3094 (not-a-bug, stale index), #3098 (calque moat already complete), #3116 (wrong-sense synonym, prior reclassification corrected via Грінченко).
- **In-flight:** Codex dispatch `2991-vesum-correction-yaml` (HIGH, architectural) — see §In-flight.

## ✅ Shipped / merged this session
| PR/action | What |
|---|---|
| **#3126** | Wired §8 `validate_atlas_conformance` into `scripts/lexicon/verify_manifest.py` (#M-11 promote gate now runs conformance, not just structural hazards — the #3124 follow-up). + #3124 autopsy `Root cause` heading hygiene. |
| **#3128** | Per-lemma wrong-sense synonym exclusion `_WRONG_SENSE_SYNONYMS` in `enrich_manifest.py` (`шлях→кам'яниця`, `річка→звір` — sense-scoped, never global). + renamed typo'd consts `_DERIVATIONAL/_ORDINAL_ETYMLOGY_BASES` → `…_ETYMOLOGY_…`. |
| **#3133** | `_WARNING_QUOTE_RE` (linear_pipeline.py) now exempts the `як/as/like «X»` citation frame (guillemets-only), not just `не/not «X»`. Foreign terms cited in decolonization prose (`як «лєший»`) no longer false-flag the vesum gate. +5 tests incl. narrowness guards. **Folk track to validate the real `narodni-viruvannia` build.** |
| #2997 closed | Verified #2998's `_strip_quote_fidelity_verified_blockquotes` is active for `folk ∈ SEMINAR_LEVELS`. |
| #2368 closed | `/api/orient` + `/api/delegate/active` both route through `delegate_api.active_delegate_count`/`active_delegate_tasks` — divergence gone. Flagged residual: `_derived_task_status` zombie-reclassification could under-count detached delegates (separate watch-item). |
| -003403 reaped | Removed superseded folk build worktree (track-orchestrator flagged); branch `3e69cc84f5` preserved. |
| #3094 / #3116 | Issue comments with root-cause + dictionary evidence (correcting a prior session's `кам'яниця` misclassification). |

## 🔄 In-flight — #2991 Codex dispatch (REVIEW WHEN IT LANDS)
- **Task:** `2991-vesum-correction-yaml` · agent codex gpt-5.5 xhigh · branch `codex/2991-vesum-correction-yaml` · worktree `.worktrees/dispatch/codex/2991-vesum-correction-yaml` · base `37af044865`.
- **Brief:** `/tmp/2991-brief.md` (NOT committed — regenerate from #2991 if lost). Fix: extend the ADR-008 correction loop to apply literal find/replace (ADR-007 no-regen) to `activities.yaml`/`vocabulary.yaml`/`resources.yaml`, not just `module.md`. Repro: `гаівки` (ї→і typo) at `activities.yaml:17` uncorrectable.
- **Monitor (#M-8):** tail the codex session JSONL (scoped `CODEX_HOME/sessions/.../rollout-*.jsonl`) OR `ScheduleWakeup ~1200s` polling `/api/delegate/active` until `total=0`. On finalize: `gh pr list --state open` (codex opens a PR, no auto-merge), review the **attribution approach** + **rollback/teeth guarantees** + ADR-007 `tests/test_no_rewrite_contract.py` still green, then merge if clean.
- **Review focus:** must NOT broaden the gate or exempt forms (teeth-preserving); YAML must still parse post-patch; gate re-runs on patched artifacts; module.md path byte-unchanged.

## 🎯 Infra priority stack (the re-established queue)
- **P0:** #2991 (in-flight). ~~#2997~~ ✅ ~~#3132/#3133~~ ✅
- **P1 (next, both bounded):** **#3045** (`check_postmortems --regenerate-index` lossy — drops curated multi-incident rows), **#2928** (`heritage_classifier` tests skip on CI — add fixture coverage).
- **P2:** #2279 (enforce worktree-only branch creation — would automate the manual stash→worktree dance I did 5× this session), #2732/#2261 (deps), #2126 (review/review CI failing ~45s), #3087/#3079/#3063 (infra epics), **#3097** (slovnyk.me mirror — DESIGN-GATED + network-risky; needs user sign-off on the licensing two-bucket guardrail, NOT an unattended autorun).

## ⚠️ Watch-items / left for owners (NOT mine to close unilaterally)
- **#2842** core.bare: current state healthy (core.bare=false, canary `git_core_bare_ok` live). Left OPEN — the flip ROOT CAUSE is unknown; the canary only detects recurrence.
- **2 stale ADR DRAFTs:** adr-008 (54d), adr-010 (34d) — need an OWNER finalize/close decision.
- **#2368 zombie watch-item:** detached-delegate liveness uses launcher-PID, not a heartbeat — could under-count active delegates. Distinct ticket if it bites.
- **Pre-existing RED (local-only, data-dependent):** `tests/build/test_linear_pipeline_wiki_packet.py::test_build_knowledge_packet_reads_wiki_and_sources` fails on clean main (needs sources.db; ambiguous textbook candidates). Not my change; likely skips on CI.
- **Stale v6 test imports:** `tests/build/test_reviewer_dispatcher.py` + `test_activity_retry_feedback.py` import the removed `build.v6_build` → collection errors. Candidate cleanup (v6 is dead per pipeline policy).

## Restart
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin -q && git log -1 --oneline origin/main
curl -sS http://localhost:8765/api/delegate/active          # is #2991 still running?
gh pr list --state open --json number,title,headRefName --limit 20   # did codex open the #2991 PR?
cat /tmp/2991-brief.md                                       # the dispatch brief (regen from #2991 if gone)
# Next P1 after #2991 merges: #3045 (postmortem-index lossy), #2928 (heritage tests skip CI)
```
