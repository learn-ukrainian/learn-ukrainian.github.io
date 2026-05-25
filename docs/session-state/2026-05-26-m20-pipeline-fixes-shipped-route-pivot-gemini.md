---
date: 2026-05-26
session: "Picked up from 2026-05-25 evening handoff (3 PRs ready to merge). User confirmed quota reset + Codex UI handled m20 anchor end-to-end via 3-phase sequenced delivery (Tab 4 leak fix → #2275 venv symlinks → m20 build). Phase 3 m20 retry exposed systemic pipeline gaps: writer-prompt under-specified ULP S1 baseline, conflicting dialogue-gloss instruction, missing resource-search obligation, ADR-008 correction loop regresses passing gates, vocabulary.yaml has no correction path. Three headless codex dispatches systematically fixed each: writer-prompt fix (#2289), b1 backfill (#2293) + caution wording polish (#2295), correction-loop surgical + vocab_floor (#2296). Plus codex UI shipped b1 backfill of MDX-only #2274 ship (artifact graph integrity restored). All shipped clean. m20 retry now unblocked but the actual rebuild + PR has NOT yet shipped — codex UI was last seen as the relay target for the final retry-and-ship pass."
status: m20-pipeline-fixes-shipped-rebuild-pending-routing-pivot-to-gemini
main_sha: c30fb45f2a
main_green: clean (review/review advisory still red on every PR until next test cycle of the gemini-review CI fix from #2277)
working_tree_dirty: pre-existing carry-overs from 2026-05-24 (audit reports + dispatch briefs); current session shipped audit briefs uncommitted
prs_opened_this_session: ["#2282 (orchestrator, MERGED) docs(dispatch-briefs): a1/m20 anchor pickup + dispatch contract", "#2284 (codex UI Phase 1, MERGED) fix(mdx): drop pipeline metadata from resources tab — closes #2283", "#2286 (codex UI Phase 2, MERGED) fix(delegate): symlink deps into dispatch worktrees — closes #2275", "#2289 (headless codex, MERGED-by-orchestrator-after-silence-timeout) fix(writer-prompt): ULP S1 baseline + resource-search obligation + dialogue-gloss reconciliation", "#2293 (codex UI parallel thread, MERGED) fix(b1): backfill adjectives comparative source artifacts — closes #2290", "#2295 (codex UI, MERGED) fix(b1): clarify comparative caution wording", "#2296 (headless codex, MERGED) fix(correction-loop): surgical prompts and vocab floor"]
prs_merged_this_session: ["#2282 #2284 #2286 #2289 #2293 #2295 #2296 — all 7 merged clean (advisory review/review red only)"]
prs_pending_at_handoff: []
issues_closed_this_session: ["#2283 Tab 4 metadata leak (closed by #2284)", "#2288 V7 m20 anchor blocker — ULP S1 baseline + resource discovery (closed by #2289)", "#2290 b1 source artifacts missing (closed by #2293)", "#2292 CI gate (duplicate of #2291; closed as dup)", "#2294 m20 retry blocker — QG correction regression + vocab floor (closed by #2296)"]
issues_filed_this_session: ["#2278 [v7] Conditional ULP-injection via {IMMERSION_RULE} for letter_module:true plans only", "#2279 [harness] enforce worktree-only branch creation in main project dir (no `git checkout -b`)", "#2280 [services.sh] pre-flight version-drift check before starting starlight", "#2281 [ci] canary smoke test on PRs touching starlight/package.json or starlight/astro.config.mjs", "#2283 Tab 4 Resources tab can leak pipeline metadata (CLOSED)", "#2285 [harness] agent bridge — send + receive to running Codex UI / Cursor / Claude Code Desktop sessions", "#2287 [adapter] cursor-agent --resume is supported; remove stale comment + wire it in", "#2288 V7 m20 anchor blocker — ULP S1 baseline + resource discovery (CLOSED by #2289)", "#2290 b1/adjectives-comparative MDX-only ship (CLOSED by #2293)", "#2291 [ci] reject PRs that ship MDX without corresponding curriculum/ source artifacts", "#2294 m20 anchor retry blocker — QG correction regresses VESUM (CLOSED by #2296)"]
issues_open_at_handoff: ["#2275 (extended scope: embed-venv + data/external_articles/*.jsonl symlinks)", "#2278 (ULP conditional injection, broader scope)", "#2279 (worktree-branch enforcement hook)", "#2280 (services.sh preflight)", "#2281 (CI canary on starlight)", "#2285 (agent bridge UI integration — large design issue)", "#2287 (cursor adapter --resume cleanup)", "#2291 (CI gate for MDX-source parity)"]
active_dispatches: []
active_builds: []
codex_ui_session: "active; was last relayed the 'm20 retry final pass with correction-loop fix in main' message after #2296 merged at c30fb45f2a. Has not yet produced m20 anchor PR. May still be running the rebuild or may be idle awaiting next instruction. Existing worktree at ~/.codex/worktrees/3a9a/learn-ukrainian/.worktrees/dispatch/codex/a1-m20-anchor-2026-05-26 is reusable for the retry."
headless_codex_silence_timeout_lesson: "PR #2289 hit a 30-min silence timeout because codex called `ab ask-gemini` for adversarial review and waited. ALL future headless dispatch briefs MUST explicitly forbid mid-dispatch bridge invocations ('NO ab ask-gemini or ab discuss calls during this dispatch — let orchestrator review post-merge'). This was added to #2296's brief and #2296 shipped clean in 15 min. Memorize for ALL future headless dispatches."
b1_quality_assessment: "b1/adjectives-comparative now structurally complete after 3 PRs (#2274 anchor + #2293 source backfill + #2295 pedagogical caution polish). _load_vocab returns 41 lemmas; module.md/activities.yaml/resources.yaml/vocabulary.yaml present; Tab 4 clean; DialogueBox dialogues; pedagogically clear caution block separating comparative from superlative. Genuinely high-quality reference for B1 builds."
session_arc_compact: "(1) merge 4-PR carryover. (2) fire codex UI on m20 3-phase. (3) Phase 1 (Tab 4 leak fix) + Phase 2 (#2275 venv symlinks) shipped clean. (4) Phase 3 m20 build failed: writer prompt didn't enforce ULP, didn't search resources, conflicting dialogue-gloss. (5) headless codex shipped writer-prompt fix #2289 (silence-timeout on ab-ask-gemini bridge — orchestrator manually committed his finished work). (6) Phase 3 retry failed again: vesum_verified hallucinated 'що́стій', vocab stuck at 20, ADR-008 correction loop regressed passing gates. (7) Diagnosis: correction loop has architectural gaps — no path for vocabulary.yaml, prompt too generic, regenerates instead of patching. (8) Honest pushback from user: 'is not handfixing allowed; can pipeline notice near-miss and feedback constructively?' (9) Headless codex shipped correction-loop surgical fix + deterministic vocab_floor pad #2296 in 15 min clean. (10) m20 retry NOT YET shipped — codex UI relay sent but PR not visible at handoff time. (11) In parallel, codex UI surfaced + backfilled b1/adjectives-comparative source artifacts (#2293) + pedagogical caution polish (#2295). Plus 8 follow-up issues filed (#2278-#2281 + #2285 + #2287 + #2291). (12) Bridge design consultation with codex CLI + cursor agent yielded #2285 design doc — Lane 0 (fresh-spawn handoff) recommended over Lane 1 (resume-into-running-session) for phase boundaries; UI lifecycle (Electron memory bloat → close) is a first-class concern not edge case."
---

# 2026-05-26 — m20 pipeline fixes shipped, m20 anchor rebuild pending, routing pivot to Gemini

## State at handoff (compact)

- **Main**: `c30fb45f2a` (`fix(correction-loop): surgical prompts and vocab floor (#2296)`)
- **Open PRs**: 0 from this session (5 dependabot from morning still open, pre-existing)
- **Active dispatches**: 0
- **Active builds**: 0
- **Codex UI session**: hot, last relay sent after #2296 merged ("m20 retry with correction-loop fix"). May still be running rebuild or idle.
- **Codex weekly quota**: heavy usage this session (3 headless dispatches + multiple codex UI threads). User direction at handoff: "pivot routing to gemini-3.1-pro + agy (gemini-3.5-flash-high) — we have more usage at Google now, Codex has lots of pressure."

## All 7 PRs merged this session

1. **#2282** orchestrator: dispatch-briefs commit (so codex UI could see them)
2. **#2284** Phase 1 — codex UI: fix Tab 4 metadata leak in mdx-assembler
3. **#2286** Phase 2 — codex UI: extend `_provision_data_symlinks` with `.venv` + `node_modules` + `starlight/node_modules`
4. **#2289** headless codex: writer-prompt fix (ULP S1 baseline injection + resource-search obligation + dialogue-gloss reconciliation). NOTE: silence-timeout on `ab ask-gemini` review; orchestrator manually committed the finished work after diagnosis.
5. **#2293** codex UI parallel thread: backfill b1/adjectives-comparative source artifacts (module.md + activities.yaml + vocabulary.yaml + resources.yaml + stable IDs for 17 activities)
6. **#2295** codex UI: clarify b1 comparative caution wording (pedagogical: separate comparative vs superlative model)
7. **#2296** headless codex: correction-loop surgical per-gate prompts + deterministic vocab_floor pad path

## NEXT-SESSION FIRST ACTIONS — in order

### 1. Check m20 anchor PR status

Codex UI was relayed the "m20 retry now unblocked" message at end of session but no m20 anchor PR is visible at handoff. Options when next session starts:

- **If codex UI is still running**: tail his session JSONL, see if PR opens, watch + merge.
- **If codex UI is idle / closed**: paste relay text again:
  ```
  Phase 3 m20 retry — correction-loop fix is in main at c30fb45f2a.
  cd ~/.codex/worktrees/3a9a/learn-ukrainian/.worktrees/dispatch/codex/a1-m20-anchor-2026-05-26
  git pull
  .venv/bin/python -u scripts/build/v7_build.py a1 my-morning --worktree --no-resume 2>&1 | tee build.log
  Apply §4 ten-check + ULP fidelity per docs/dispatch-briefs/2026-05-26-a1-m20-anchor-codex.md.
  Anchor must ship FULL source artifacts (curriculum/l2-uk-en/a1/my-morning/*) AND rendered MDX — #2290 / b1 split-workflow gap must NOT recur.
  Close #2294 + #2288 in PR body.
  ```
- **If codex UI is unavailable**: fire headless codex on the same retry (now that pipeline fixes are in main, headless should work). Brief: "Phase 3 m20 anchor build retry against main c30fb45f2a per docs/dispatch-briefs/2026-05-26-a1-m20-anchor-codex.md. **NO ab ask-gemini mid-dispatch.** Ship FULL source artifacts."

### 2. ROUTING PIVOT — open issues to Gemini agents

Per user direction: pivot dispatch routing from codex (high pressure) to **gemini-3.1-pro** (deep work) + **agy** = Antigravity CLI / gemini-3.5-flash-high (mechanical fixes). Google has unused capacity from the AI Ultra subscription user added today.

Suggested routing:

| Issue | Agent | Why |
|---|---|---|
| **#2275 follow-up** (embed-venv + external_articles/*.jsonl symlinks) | agy | Small mechanical extension to existing function, well-scoped |
| **#2287** (cursor-agent --resume wiring) | agy | ~10-20 LOC adapter change + test |
| **#2279** (worktree-branch enforcement hook) | agy | Single shell hook + test |
| **#2280** (services.sh preflight version-drift) | agy or gemini-3.1-pro | Shell script + decision logic; gemini if you want polish |
| **#2281** (CI canary on starlight changes) | gemini-3.1-pro | New workflow file + smoke test design; needs judgment on test-pr fixtures |
| **#2291** (CI gate for MDX-source parity) | gemini-3.1-pro | New audit script + pre-commit + ci.yml wiring; needs legacy-track exemption design (see #2292 close note on #2291) |
| **#2278** (ULP conditional injection broader scope) | gemini-3.1-pro | Architectural — #2289 added `_ulp_practices_rule` for a1 m01-m25 trigger; broader scope is S2 step-change at m41 + per-plan trigger refinement |

KEEP on codex (or claude headless if quota allows):
- **#2285** (agent bridge UI integration — large design issue, multi-day scope)
- Anything that surfaces in m20 anchor or post-anchor cleanup that's architectural

### 3. Headless dispatch hygiene — MANDATORY for all future briefs

**EVERY headless dispatch brief must include**: "NO `ab ask-gemini` or `ab discuss` calls during this dispatch. If you want adversarial review, note as a manual follow-up step in the PR body; do not invoke from within the dispatch. Bridge calls block until the other agent responds; if the response is slow you'll hit the silence timeout and your work will be uncommitted."

This burned PR #2289 (orchestrator had to manually salvage). Encoded in #2296's brief and #2296 shipped clean in 15 min. **Lesson is now permanent.**

## Pending follow-ups (not yet filed, surface in next session if relevant)

- **Diff-only correction architecture** (the "big" 200-400 LOC fix that does parser-backed diff-only writer corrections — eliminates entire class of regenerate-and-break failures). #2296 explicitly noted this as a follow-up. Worth filing as its own issue when next session has bandwidth. Defer until m20 anchor ships clean — we may discover #2296's prompt-strengthening is "good enough."
- **A1 m41 S2 step-change content for `_ulp_practices_rule`** — current trigger is `a1` + `module_num <= 25` returning S1 baseline. Needs S2 content + trigger expansion for a1 m26-m55. Captured implicitly in #2278's broader scope.

## Critical context for next orchestrator

- **#2289 silence-timeout pattern is REAL.** Headless codex called `ab ask-gemini`, gemini never responded in time (or response was lost), dispatch killed at 30 min mark, work uncommitted in worktree. Orchestrator (me, this session) had to manually validate + commit + push + PR. If next session sees a similar pattern, the salvage workflow is:
  1. Check `find .worktrees/dispatch/<agent>/<task-id> -newer .git/HEAD -type f` for uncommitted changes
  2. Read the codex session JSONL last assistant message to understand what was attempted
  3. Run the relevant pytest manually to validate
  4. Commit with attribution (`Co-Authored-By: Codex GPT-5.5 (xhigh, headless dispatch) <noreply@openai.com>`)
  5. Push + open PR
- **b1 MDX-only ship pattern caught + fixed.** #2274 originally shipped MDX without source artifacts; #2293 backfilled. #2291 CI gate is the prevent-recurrence piece. **Until #2291 ships, manually verify** every module PR includes both `starlight/src/content/docs/{level}/{slug}.mdx` AND `curriculum/l2-uk-en/{level}/{slug}/*`. m20 anchor MUST satisfy this manually if it ships before #2291.
- **Bridge design (#2285) has a substantive design ready** — codex CLI + cursor agent consultation surfaced that all three agents (Codex Desktop, Cursor, Claude Desktop) have `--resume <id>` CLI primitives. AppleScript is unnecessary for orchestration. Lane 0 (fresh-spawn dispatch with handoff blob) recommended over Lane 1 (resume) for phase boundaries because UI lifecycle (Electron memory bloat → manual close) is a first-class concern. Full design in #2285 body + 2 comments.
- **Cursor adapter has stale "no resume" comment** (`scripts/agent_runtime/adapters/cursor.py:75`) — verified empirically that `cursor-agent --resume <chatId>` IS supported. Wire fix is #2287.

## Knowledge encoded this session (auto-loaded next cold-start)

- **Headless dispatch hygiene**: NO bridge calls mid-dispatch. Memorialized in #2296 brief; should propagate to ALL future briefs. Consider adding to `claude_extensions/rules/` as a permanent rule.
- **Anchor-build discipline**: 95% right is worse than 99% right. Codex UI's Phase 3 stop-at-gate refusal saved 124 pattern-matched modules from inheriting a broken anchor. Validate the same discipline for all future anchor work.
- **UI lifecycle as first-class concern** (per user direction this session): Electron apps bloat memory, MUST be closed. Bridge design must assume the UI is ephemeral. Lane 0 (fresh-spawn) is inherently immune; Lane 1 (resume) needs full lifecycle plumbing (probe, auto-revive, file rotation, in-flight salvage).
- **Surgical correction beats prompt-strength rhetoric**: telling an LLM "don't regenerate" is a negative constraint it ignores; giving it EXACT tokens to replace + locked previously-passing-gate snapshot reduces hallucination class.

Full handoff: this file. Next session first item: check m20 anchor PR status; if none, re-relay to codex UI or fire headless retry. Then pivot routing to gemini-3.1-pro + agy for the 7 open follow-up issues.
