# Session Handoff — 2026-04-18 (updated afternoon)

You're starting cold. Boot via the API, not the filesystem:

```python
from ai_agent_bridge.monitor_client import MonitorClient
boot = MonitorClient().bootstrap()      # manifest + cached rules + this file
```

Then `curl /api/orient` for live state and `curl /api/comms/inbox?agent=claude` for unread messages. **Do not** read `CLAUDE.md` or `claude_extensions/rules/*.md` directly — they're served by `/api/rules` with hash-based 304s. See `docs/MONITOR-API.md` for the full endpoint table.

## 🔴 IN FLIGHT — Dimensional review system (paused mid-design, 2026-04-18 PM)

User idea: replace single-score reviews with **dimensional reviews** (per-dimension personas, per-dimension minimum score gates, no weighted averaging). User's explicit sequencing: **wiki first, then modules.**

**Current step** — finished reading code (task #1 ✅). Paused before writing the design doc. Next concrete action: write `docs/design/dimensional-review.md` (task #3).

**Key findings from code read (don't re-discover):**
- **Module review is ALREADY dimensional but single-call.** `scripts/build/phases/v6-review.md` has 9 weighted dimensions: Plan adherence (15%), Linguistic accuracy (15%), Pedagogical quality (15%), Vocab coverage (10%), Exercise quality (15%), Engagement & tone (10%), Structural integrity (5%), Cultural accuracy / decolonization (5%), Dialogue quality (10%). **Engagement and decolonization are already dimensions** — earlier-session claude missed this. Work for modules is REFACTOR: split dims across specialist parallel reviewers, per-dim minimum gates instead of weighted average.
- **Wiki review has NO semantic layer.** `scripts/wiki/quality_gate.py` is 212 lines of mechanical checks (word count, AI-thinking leakage regex, fence wrapping, truncation, placeholders). No LLM review. Work for wiki is NET-NEW.
- **Reviewer-as-fixer contract** (`v6-review.md` 158-173) — reviewer outputs `<fixes>` find/replace + optional `<rewrite-block>`. For parallel dimensional reviewers on modules, fixes will conflict. Unresolved: Option A (sequential fix-apply, parallel scoring) vs Option B (diagnose-only reviewers + single patcher). Leaning Option B.
- **Self-review rule currently overridden.** Pipeline rule says LLM-never-reviews-own-work (enforced by `SELF_REVIEW_DETECTED`). Memory says we're on `--writer gemini-tools --reviewer gemini-tools` due to Claude/Codex capacity. A/B experiment must cover BOTH regimes so results survive capacity return.

## 🟢 POLICY CHANGE 2026-04-18 PM — Codex is the primary reviewer

User override: **stop Gemini self-reviewing.** Codex has 10× usage through 2026-05-17 (memory #1); use it. User will signal if usage gets hot.

- Build command when reviewing modules: **`--writer gemini-tools --reviewer codex-tools`** (explicit; don't rely on "cross-agent default" since that can pick Claude which we want to conserve).
- Memory rule "Reviewer Constraint — use Gemini-reviews-Gemini" is now **stale** — trigger condition ("user says switch back to cross-agent") was met today. Don't re-assert the self-review pattern from memory.
- Affects dimensional review design: Codex is primary reviewer candidate for most dimensions, not the capacity-constrained fallback. Claude conserved for dimensions needing cultural/creative nuance (decolonization framing, engagement).
- A/B experiment still needs to cover multiple agents but the baseline is now Codex, not Gemini-self.

**Design decisions already landed this session:**
1. Wiki reviewer set: 4 dims (factual accuracy, source grounding, Ukrainian perspective, register). **No engagement dim on wiki** — wiki is AI-consumption reference, not learner-facing.
2. Parallel calls with cached shared prefix (Regime C) — NOT multi-persona single-call (Regime A, harmonizes) or sequential (too many turns).
3. Evidence-first scoring: reviewer outputs concrete friction/delight findings FIRST, score derived from them. Kills sycophancy and score inflation.
4. Sharp personas only — "17yo London diaspora, phone, 20 min" beats "a student". Personas versioned in code, not drifting in prompts.
5. Drop "aim for highest possible" — just enforce minimum gates honestly.
6. Engagement uses student personas; other dims use specialist personas (linguist, pedagogue, decolonization reader).
7. **Humor is structural, not decorative.** Ukrainian culture survives empire/war through irony. But humor-under-siege, not cheerful-imperial-erasure. Chipper register while Kharkiv is bombed = failure.
8. **Genre-mixing at two levels**: within a work (Shevchenko's *Сон*) AND across media/life (Zhadan's prose + rock + radio + video). Module needs wholeness across its span, not humor on every page.
9. **Shevchenko = engagement lineage anchor** (foundational: proved Ukrainian carries literature by doing it; used folk meters; refused single register).
10. **Zhadan = contemporary engagement north-star.** Single test: "Would this module land for a reader whose literary home is Zhadan?" Novelist + poet + rock + radio + rap collab + Kharkiv volunteer = embodies every principle in one person.
11. **Outward clarity** added to cultural accuracy rubric — Ukrainian voices that see other societies with artistic authority (Zhadan-on-Hungary-golden-visa). Decolonization ≠ parochialism. Curriculum presents Ukrainian as a clear-sighted perspective on the world, not only as a subject for outsiders.
12. **Humor touchstones**: Zhadan and band (including "300 китайців у Будапешті"), Телебачення Торонто, Наші без раші (user-recommended, not personally verified by lead dev).
13. **Calibration limit acknowledged in doc**: reviewer prompt catches structural failures; it cannot judge "did this land tonally as Zhadan-register or as fake-Zhadan." Native ear (Tetiana / user) is the only reliable final calibrator for engagement tone.
14. **Bulgakov added to don't-reference list** (Russian-imperial writer, portrayed Ukrainian 1918-19 forces as bandits; being removed from Ukrainian canon since 2022). User caught my error in earlier persona draft. Same principle applies to Gogol, Akhmatova, Pasternak.

**Fact corrections for persona writing (from user):**
- **Yulia Svyrydenko** is current PM (since 2025-07-17, appointed by Zelensky, second female PM in Ukrainian history). User framing: "awesome, a true Ukrainian." Safe to reference positively.
- **Yulia Tymoshenko** — DON'T reference in personas. User framing: "Russian sellout." Do not invoke as neutral shorthand.
- **President = highest Ukrainian leader.** PM heads government but is not top. I wrote them as equivalent earlier; that was wrong.
- **No inventing historical figures for examples.** I fabricated "Hetman Tymoshenko" — there is no such person. Verify via Wikipedia/sources MCP before naming anyone.
- **Bulgakov is NOT Ukrainian canon.** Russian-imperial writer born in Kyiv, wrote sympathetically of White Russian cause in *The White Guard*, portrayed Ukrainian 1918-19 forces as bandits. Since 2022 being removed from Ukrainian cultural institutions. I used him as aspirational reading in the C1-C2 persona — user caught it. Same trap applies to Gogol, Akhmatova, Pasternak — Russian-imperial figures with Ukrainian biographical ties are NOT Ukrainian writers. Full corrections + safe Ukrainian literary references in design doc Appendix C.
- **BIO seminar track = BIOGRAPHIES of Ukrainian figures, not biology.** User corrected mid-session. Verify track-code semantics before assuming.
- **No current production wiki.** The 5 compiled wiki files I'd been analyzing are test artifacts. User: "we deleted them, we are rebuilding them." This changes migration framing to clean-rebuild framing. Rebuild scope per user: A1, A2, B1, seminar first (B2+/C1+ later). Wiki should be strictly Ukrainian across all levels — policy locks in at rebuild start.
- **Wiki source-duplication bug (#1323 incomplete)**: compiled wikis contain a `## Джерела` prose section at the bottom duplicating the sibling `.sources.yaml`. Example: `wiki/linguistics/oes/walls-speak-intro.md` lines 93-147. #1323's AC "no remaining legacy (Source N: patterns" only caught OLD syntax. Compile prompt probably still emits the section. Decision: fold the fix into #1323 extension (not dimensional review). New task added.

**Open design questions before implementation:**
- [ ] Option A vs Option B for fix-conflict resolution (leaning B — diagnose-only + single patcher)
- [ ] Exact A/B experiment spec: which 5-10 wiki artifacts? Ground truth source?
- [ ] Cost estimate at scale (Gemini doesn't support Claude-style prompt caching; reviewer choice affects cost math materially)
- [ ] Migration path for module `<fixes>` contract if we go Option B

**Task list**: `TaskList` from this session — 8 tasks, #1 done, #2 done, #8 in progress (this file).

**Phase 1 progress (2026-04-18 PM):**
1. ~~Write design doc~~ ✅ DONE — `docs/design/dimensional-review.md` (450 lines after Codex review revisions)
2. ~~Codex adversarial review~~ ✅ DONE — 10 findings absorbed. App D of design doc.
3. ~~Decide adapter path (task #11)~~ ✅ RESOLVED — Path A (fix adapter) for failover resilience per user 2026-04-18 PM.
4. ~~Fix CodexAdapter (task #13, issue #1325)~~ ✅ DONE — Codex committed `a21ffbfc7`. Smoke test passed (real `codex exec` with MCP stdio config, `search_external` executed, logged to `logs/mcp-sources-requests.jsonl`).
5. ~~Fix compile prompt for `## Джерела` (task #9)~~ ✅ DONE — surgical fix to `scripts/wiki/prompts/compile_article.md` (only prompt with the bug; three briefs were already clean).
6. **Phase 1 Step 2 — quality_gate.py code gates (task #14, issue #1326)**: delegated to Codex, PID 95678, running. Adds two checks: no `## Джерела` section + citation-registry consistency ([S#] orphans, unused YAML entries, missing sidecar). Task status file: `batch_state/tasks/codex-quality-gate-1326.json`.
7. ~~Phase 1 Step 3 — source-grounding reviewer prompt~~ ✅ DONE — `scripts/wiki/prompts/review_source_grounding.md` (169 lines). Evidence-first JSON schema, 5 failure modes defined (OVERCLAIM, MISATTRIBUTION, UNSUPPORTED_CLAIM, STALE_CITATION, WEAK_SUPPORT), severity-counted scoring rubric, English instructions + Ukrainian artifact per §2 principle 11.

**Remaining decisions (not blocking Phase 1):**
- §9 question 3 — engagement per-level weights (user/Tetiana calibration needed before freezing)
- §9 question 4 — orchestrator availability detection (resolve during Phase 1 Step 2 wrap-up or when building orchestrator)

**Next concrete action when Codex returns on #1326:**
- Verify his work (commit landed? tests pass? smoke test documented?)
- Close task #14
- Optional pilot: run review_source_grounding.md prompt on a real test wiki (e.g., walls-speak-intro.md) through Codex-with-MCP or Gemini to validate prompt output shape
- Session handoff

**Phase 2+ waits:** orchestrator (scripts/wiki/review_orchestrator.py), remaining 3 wiki dim prompts (factual, decolonization, register), seeded benchmark per §7b.

## Decisions waiting on you (the only reason this file isn't `git log`)

| # | Decision | Resolve by |
|---|---|---|
| 1 | **Phase B kickoff?** Different pipeline from Phase A; could proceed without re-verify, or run a 2-slug Phase A re-verify first. | Say "go Phase B" or "rerun Phase A". |
| 2 | **Merge #1323 + #1324 round-2 patches** as-is, or queue another Gemini re-verify? | Spot-check the regression tests; Gemini-quota-sensitive. |
| 3 | **`rclone config`** for Phase C activation. Backup scripts ready, no Drive remote yet. OAuth needs your browser. | `rclone config`, then install cron from `docs/ops/gdrive-backup.md`. |
| 4 | **Restore the agent-watcher LaunchAgent?** Unloaded this session; backup at `~/Library/LaunchAgents/com.learn-ukrainian.agent-watcher.plist.disabled-2026-04-18`. | Leave unloaded unless you want auto-broker draining back. |
| 5 | **Push the cold-start-handoff pattern further?** User explicitly parked these for after `/clear`. Three deltas: (a) `scripts/cold-start.sh` shell wrapper around `MonitorClient().bootstrap()` for symmetry with `scripts/ops/smoketest_bridge_stdout_only.sh`. (b) Wire the bridge smoketest into the pre-commit hook for any change touching `scripts/ai_agent_bridge/_gemini.py` or `_cli.py` so this regression class can't sneak back. (c) Audit other `docs/session-state/*.md` for the same bloat pattern (duplicating API-served state) and trim. | Pick one or all three when you resume. |

## Behavior changes future callers may trip on

These belong here (not in commit messages) because they change a contract callers may have memorized:

- **`scripts/wiki/state.py:is_compiled`** now AND-checks the on-disk `.md` file and self-purges stale rows. Don't add a redundant file-existence check at call sites.
- **`scripts/ai_agent_bridge` `--stdout-only`** now actually writes Gemini's response to stdout (was previously suppressing it AND polluting stdout with `[gemini] attempt N/M` preamble). Wiki review parser depends on this. Verify with `bash scripts/ops/smoketest_bridge_stdout_only.sh` after any bridge change.
- **`services.sh restart`** is serialized cross-process via `mkdir`-based lock at `.pids/.restart.lock.d/`. Stale lock auto-reclaims when holder PID is dead.

Everything else (commit log, PR/issue list, pipeline state, in-flight workers, recent handoffs, ahead-of-origin count) is one `gh`/`git`/`curl /api/orient` call away — don't snapshot it here.

## Archived

Earlier in-flight running-log handoff: `docs/session-state/2026-04-18-am-autonomous-handoff.md`.
