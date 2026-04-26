# 2026-04-26 — Reboot agent responsibilities

> **Status**: ACTIVE — clarifies but does not supersede `docs/north-star.md`
> **EPIC**: #1577 (curriculum reboot)
> **Authority chain**: `docs/north-star.md` → `docs/lesson-contract.md` → this decision
> **Supersedes**: nothing formally; **clarifies** the V6-era writer/reviewer language in `claude_extensions/rules/pipeline.md` (which predates the reboot and has been read by agents as still-binding policy)
> **Expiry**: revisit when Phase 5+ batch module writing approaches; the module-writer choice (left open here) gets decided then

## Why this doc exists

Three things forced an explicit responsibilities decision on 2026-04-26:

1. **A 5h Opus limit drained overnight** when the user ran batch wiki rebuilds with `--writer=claude` for hist/lit/bio (~167 articles). The drain wasn't on the reboot work proper — it was wiki content generation, which is a different cost class.
2. **My Phase 4 brief baked `claude-tools` (Opus 4.7 xhigh) into the pipeline** as the module writer, citing the pre-reboot `pipeline.md` rule. The user noticed and asked: "we have not decided who the module writer is in the reboot? right?" — correct, no reboot-era decision exists.
3. **Phase 0 (North Star + Lesson Contract) is silent on agent roles by design** — it specifies what the writer/reviewer must do, not who they are. That silence was right at Phase 0 but is now causing the inheritance problem above.

This doc fills the gap with the responsibilities policy that's actually in force right now, and explicitly marks what's still open.

## Agent role matrix

| Agent | What it's for in the reboot | What it's NOT for | Cost class |
|---|---|---|---|
| **Claude** (Opus / Sonnet) | Coding, architecture, orchestration, ADR drafting, plan/brief authoring, adversarial review of architecture, cultural/creative nuance reviews when used in pipeline | Batch wiki content generation. Batch module content generation (until/unless explicitly decided). | Metered (5h rolling Opus limit, observed 2026-04-26). |
| **Codex** (`gpt-5.5`) | Mechanical refactors, pre-commit hooks, golden-corpus fixtures, CI diff checks, pattern-applying. Primary pipeline reviewer (cross-agent, max 2 fix attempts). Implementation work in delegated worktrees. | Architecture decisions made in isolation. Self-review of own implementations. | Metered separately from Claude; current dispatch cap **2 in flight**. |
| **Gemini** (`gemini-3.1-pro-preview`) | **Wiki content generation (default and only).** Long-form writing where token volume is high. Adversarial review of architecture (panel discussions). Research + exercises in v6 pipeline (existing `gemini-tools` writer mode). | Reviewing its own work (`SELF_REVIEW_DETECTED` gate enforces). | Subscription, **unmetered**. |

The **6:4 Codex:Claude split** (per the original architectural intent) still holds for open coding work: prefer Codex dispatch for mechanical work; reserve Claude inline / dispatch for architecture, ADRs, content-writing briefs, linguistic correctness, browser/UI testing.

## Specific policies in force

### 1. Wiki writer: Gemini, always

`scripts/wiki/compile.py` defaults to `--writer gemini` (line 859). Never pass `--writer=claude` or `--writer=claude-tools` for wiki rebuilds. Wiki content generation is high-token-volume and routes to the unmetered Gemini subscription.

This decision is permanent for the reboot's MVP scope (a1+a2+b1 wikis ship via Gemini). Reconsider only if Gemini quality on wiki content fails the LLM QG bar in a measurable, reproducible way that switching writers would actually fix.

### 2. Pipeline reviewer: Codex

The pipeline reviewer is Codex (`codex-tools`), per the existing post-reboot policy (verified in `tests/test_determine_reviewer.py` and `scripts/build/v6_build.py`). An LLM may not review its own work (`SELF_REVIEW_DETECTED` gate). When Phase 4+ runs the per-dim LLM QG defined in `docs/decisions/2026-04-26-llm-qg-per-dim-thresholds.md`, those per-dim reviewer calls are Codex.

Claude reserved for cultural/creative nuance dimensions (decolonization, engagement, dialogue) when those reviewer agents need a different voice than Codex.

### 3. Module writer: NOT YET DECIDED

This is the open item. Phase 0 (North Star + Lesson Contract) deliberately doesn't pin a writer. The Phase 4 brief and `linear_pipeline.py` (PR #1594) currently bake in `claude-opus-4-7` because my brief inherited the V6-era `pipeline.md:17` rule. **That bake-in is to be removed** (see "Implementation cleanups required" below).

The actual module-writer choice will be made when Phase 5+ batch module writing approaches, with these three options on the table:

- **`claude-tools`** (Opus 4.7 xhigh) — V6 default. Strong on cultural/creative nuance; metered; would need careful budgeting at Phase 5+ scale (218 modules × multi-call writer work).
- **`gemini-tools`** (Gemini 3.1 Pro Preview) — same writer that owns wikis. Consistent with the wiki-writer-is-Gemini policy. Subscription-unmetered.
- **Hybrid** (e.g. Claude for A1-checkpoint or B1+ where cultural/dialogue density is highest, Gemini elsewhere). More architectural complexity but lets each agent play to strengths.

Decision criteria when we get to Phase 5+ (based on a strict bakeoff unit):

1. Does the writer reliably hit the LLM QG floor (PASS at every dim, A1 floors `pedagogical=naturalness=decolonization=9.0, engagement=tone=8.0`)? This must be tested using the same frozen Phase 4 exemplar prompt, same wiki packet, same reviewer model, and across N attempts/max retries.
2. What is the PASS rate and token cost per successful module for the chosen writer? Affects whether a 218-module fan-out is feasible at all.
3. Does the chosen writer integrate cleanly with the existing `scripts/agent_runtime/adapters/` harness without needing per-writer special cases?

### 4. Phase boundary: who runs what right now

| Reboot phase | What's running | Agent doing the work |
|---|---|---|
| Phase 0 (North Star + Lesson Contract) | Done | Claude + Codex + Gemini (3-agent review) |
| Phase 1 (Salvage) | Done | Claude + Codex |
| Phase 2 (Config audit, #1583) | Done | Codex |
| Phase 3 (Lesson schema, #1584) | Done | Claude (design) + Codex (impl) |
| Phase 4 prereq #1586 (per-dim QG floors) | Done | Codex |
| Phase 4 prereq #1591/#1592 (citation-shift fix) | Done; verified at scale | Codex (#1592) + Claude (verifier) |
| Wiki rebuild post-fix | a1+a2+b1 done (218/218); bio+hist+lit Gemini in flight | Gemini (writer) |
| **Phase 4 (A1/20 my-morning exemplar)** | **Scaffold landed in PR #1594 draft; needs writer-config decoupling + live writer call + live LLM QG** | Codex (next dispatch) |
| Phase 5+ (fan-out) | Gated on Phase 4 ship | Module writer decision pending (see §3) |

## Implementation cleanups required

This decision doc creates code-level work to honor it:

1. **`linear_pipeline.py:202-226` is hardcoded to `claude-opus-4-7`.** Refactor to accept `writer: str` (e.g. `"claude-tools" | "gemini-tools"`) and route through `scripts.agent_runtime.runner.invoke` with the appropriate model/effort. The call site picks the writer at dispatch time, not at code-write time. **Tracked as a Phase 4 follow-up against PR #1594.**
2. **`claude_extensions/rules/pipeline.md` updates:** 
   - Line 17: Replace "Writer default: `claude-tools` (Opus)" with "Reboot module writer: NOT YET DECIDED — see `docs/decisions/2026-04-26-reboot-agent-responsibilities.md` §3." 
   - Line 22: Decouple the "Claude" identity from the "writer" role to respect the TBD state.
   - Line 26: Update the review paradigm to `[Writer] builds → [Non-Writer] reviews (usually Codex)` instead of hardcoding `Gemini builds → Claude reviews`.
   - Apply same edits in `.claude/rules/pipeline.md` after `npm run claude:deploy`.
3. **`docs/architecture/ARCHITECTURE.md` updates:** Patch or deprecate lines (e.g., 7, 96, 190) that repeatedly hardcode the obsolete `Gemini builds, Claude reviews` paradigm.
4. **Reviewer policy tests:** Ensure that codebase tests (`tests/test_determine_reviewer.py`) properly reflect the new Codex policy. (Note: Prior references to `MEMORY.md` have been removed as it is not present in the current checkout).
5. **The Phase 4 brief at `.worktree-briefs/codex-phase-4-a1-20-exemplar.md`** mentions `claude-tools` writer harness. When the brief is re-issued for Phase 4 round 2, parameterize the writer reference instead of hardcoding it.
6. **`scripts/build/v6_build.py` cleanup:** Lines 29 and 10706-10707 still advertise and default `claude-tools` as the writer. If V6 is legacy only, this behavior is legacy and not reboot policy. Update or deprecate to prevent agents from misinterpreting it during the reboot.

## What this clarifies / supersedes

- **Clarifies** `claude_extensions/rules/pipeline.md:17` — the `claude-tools` writer default is V6-era and inherited; not a reboot-era decision. The pipeline.md edit per "Implementation cleanups required" §2 makes this explicit.
- **Clarifies** pipeline review tests and policies (`tests/test_determine_reviewer.py`) — same.
- **Does not supersede** `docs/north-star.md` or `docs/lesson-contract.md`. Those describe what the writer/reviewer must do; this doc describes who they are.

## Open questions deferred to later

- **Module writer choice** — decide when Phase 5+ approaches (see §3 criteria).
- **MCP-vs-direct-SQLite tension in QG paths** — Codex's Phase 4 dispatch hit the missing `data/vesum.db` in a sparse worktree and concluded "blocked." The required fix is worktree provisioning (e.g., symlink/copy `data/vesum.db` in `delegate.py` or native Python resolving the main checkout DB). Do NOT bless MCP fallback inside pipeline code, as it conflicts with the agreed Phase 4 boundary.
- **Claude (orchestrator) vs. Claude (writer)** — the user's framing reserved Claude for "coding, architecture, organizing." Whether that excludes Claude from being chosen as module writer in §3 is left open; the user explicitly said "if we decide that claude will be writing a1 thats fine, we will adjust." So §3 stays open with all three options, including a Claude-as-writer option.
