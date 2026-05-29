---
date: 2026-05-29
session: "Autonomous orchestrator. m20 tone blocker root-caused + fixed + merged (#2417). Build to MEASURE tone blocked by claude-tools runtime hang (writer bypassed its 30-min timeout). #2418 filed."
status: tone-fix-SHIPPED-and-structurally-validated · tone-SCORE-measurement-pending-on-clean-build · build-runtime-hang-blocker
main_sha: fa4abd9c53
main_green: yes
---

# 2026-05-29 Pt3 — m20 tone blocker fixed & shipped (#2417); tone-score measurement blocked by a build runtime hang

## ⭐ THE WIN (shipped this session): m20 tone REVISE root-caused to ONE sentence, fixed deterministically

Build #6 (Pt2) = 7.6 REVISE, gap = **TONE alone**. The handoff hypothesised "wire the warm exemplar."
Reading the tone-reviewer evidence **refuted that**: 4/5 of tone is already exemplary (2 FOR quotes, warm
peer voice). The entire 7.6 rested on **one body-prose sentence**:
> "These rules come from the Knowledge Packet's phonetic obligations for this module."
A meta-narration leak naming an INTERNAL artifact, which `scaffolding_leak` (#2412) didn't catch.

**Two root causes, both fixed in PR #2417 (MERGED, squash `fa4abd9c53`, all required CI green):**
1. **Gate** — `_scaffolding_leak_gate` extended with `_SCAFFOLDING_ARTIFACT_RE`
   (`knowledge packet|implementation map|wiki manifest|wiki coverage gate`, separator `[\s_-]+` so
   snake_case identifier forms `knowledge_packet.md` etc. leak too — gemini-bot review catch). VERIFY
   comments + fenced code already excluded upstream, so honest in-comment provenance citations don't trip it.
2. **Prompt** — `scripts/build/universal_rules/R-CITE-HONEST.md` said "Name the source in the text",
   which INVITED the leak. Tightened: packet provenance → `<!-- VERIFY -->` comments ONLY; real published
   sources may still be named in prose; internal artifacts never.
Theme reinforced: advisory rules don't bind a stochastic writer — deterministic gates do.

**VALIDATED structurally** (build #7 artifact `.worktrees/builds/a1-my-morning-20260529-160901/.../`):
`scaffolding_leak` now `{passed:true, offending:[]}`, and the new `module.md` has **0 body-prose
artifact leaks**. The writer no longer names the Knowledge Packet. ✅
Tests: 10/10 gate + 67 registry/prompt-gen + 97 pipeline, ruff clean.

## ⛔ BLOCKER: can't yet MEASURE the tone-dim SCORE — builds won't complete

To confirm tone clears the promote bar (~8 / no-REVISE) I need a full build through LLM review. Three tries:
- **#7** (`160901`) — FAILED at `python_qg` but NOT on scaffolding_leak (✅). Failed on `chunk_context_for_all_refs`
  + `resources_search_attempted` (=0). Root cause = **writer non-determinism**: build #6 called
  `get_chunk_context`×2 + `search_images`×1; build #7 called NEITHER (poured 35 calls into linguistic
  verify instead). Gates correct; writer just skipped retrieval. NOT caused by #2417 (those gates are in
  prompt sections I didn't touch). → re-ran.
- **#8** (`163530`) — **HUNG**: ran 61 min with 0 writer events, bypassing its own
  `DEFAULT_WRITER_TIMEOUT_S=1800` (30 min). Monitor's 1h timeout killed it. Files are seeds only.
  Sources MCP healthy (`mcp_rag:true`); `recent_outcomes.rate_limited:2`. Leading hypothesis:
  **claude-tools writer contends with the interactive Claude seat for quota** (#M0) → long backoff that
  the 30-min writer-timeout doesn't bound. Secondary: writer-timeout not engaging (possible bug).
- **#9** (in flight) — re-fired DETACHED via Bash `run_in_background` + `timeout --signal=TERM 2700`
  (45-min wall-clock cap, kill-proof vs monitor timeout), log `/tmp/m20-build9.jsonl`, task `bortezwfo`.
  Went quiet to free quota for the writer.

## NEXT (resume here)
1. Check build #9 result (`/tmp/m20-build9.jsonl` + `.worktrees/builds/a1-my-morning-<stamp>/.../`):
   - python_qg: scaffolding_leak pass (expected) + did writer call get_chunk_context + a multimedia search?
   - If it reached `module_done`: read `llm-qg-tone-response.raw.md` + `llm_qg.json` → **tone dim score/verdict**.
2. **Hypothesis to confirm:** removing the one leak sentence lifts tone to ≥8 with NO exemplar wiring needed.
   If tone still lags → read what it now flags, then consider #2389 part-3 exemplar wiring.
3. If build #9 ALSO hangs → decisive evidence of claude-tools-during-interactive contention.
   Options: run the build when the interactive seat is idle, OR switch writer (codex-tools/gemini-tools —
   but that loses clean tone-comparison to #6's 7.6; still answers "clears the bar?").
4. **Verify-before-promote (#M-11) = Section 4 ten-check on RENDERED MDX** (not just tone). Watch Section-5
   known-broken assembler issues (Tab3 fallback, Tab4 stale resources, inline-and-aggregate P2).
5. **DO NOT PROMOTE** until tone clears AND the 10-check passes. Live PR #2364 (pre-V7.2) stays; delete
   `starlight/src/content/docs/a1/my-morning-v72-preview.mdx` (untracked in main tree) on promote.

## Also shipped / filed
- **#2418** (filed) — V7 retrieval gates (`resources_search_attempted` / `chunk_context_for_all_refs`)
  hard-fail on stochastic writer omissions with NO ADR-008 correction path. Proposed: writer-side
  correction path that re-prompts the specific missing retrievals. Evidence = #6-vs-#7 tool histograms.
- #2380 left OPEN (multi-regression umbrella; m20 promote is the right holistic close-signal).
- delegate `sec7-validator-2410` shows `needs_finalize` but #2413 merged / #2410 closed — stale record, work landed.

## Guards reinforced
- **Verify deterministically, don't trust signals**: `gh pr checks --watch` exited 0 on the PREVIOUS commit's
  pytest (false green) — caught by reading `statusCheckRollup` on the actual HEAD before merge.
- **#M-11 read-the-artifact**: build #7's python_qg "fail" looked alarming; reading it proved the FIX worked
  (scaffolding_leak ✅) and the failure was elsewhere (writer retrieval).
- Build worktrees `160901` (#7) + `163530` (#8) left on disk (NOT deleted — #M-10); #8 artifacts are seeds.
