---
date: 2026-05-26
session: "Overnight orchestrator-driven session. User went to sleep early in session asking me to drive the project, send the m20 task to running Codex UI, prioritize #2285 (agent bridge UI), and add Antigravity UI to that scope. Codex UI had just reported m20 attempt #3 failed at python_qg (chunk_context_calls=0, search_attempt_count=0, vocab_count 20/25 with empty unused_recommended). User framed this as escalation-worthy but I pushed back — failures were proximate-fixable (writer ignoring buried obligations + plan having no pad headroom), not architecture-blocked. Built the agent bridge codex adapter (Lane 1 from #2285), empirically verified it sends + receives against the running m20 Codex UI session, then shipped 3 PRs: writer-prompt + plan fixes (#2297 — m20 unblocker), agent bridge (#2299 — closes codex part of #2285), doc-backlog hygiene (#2298 — 28 untracked carry-overs)."
status: bridge-shipped-m20-fixes-in-CI-routing-pivot-half-done
main_sha: c30fb45f2a (origin/main — no merges from this session yet at handoff time)
main_green: clean
working_tree_dirty: 0 files (handoff doc itself is the only new untracked)
prs_opened_this_session: ["#2297 fix(a1-m20): plan recommended-pool + writer-prompt pre-emit checklist", "#2298 docs(orchestration): commit dispatch-brief + session-state backlog + lint fixes", "#2299 feat(bridge): ab send-codex-ui — Lane 1 send to running Codex Desktop (#2285)"]
prs_merged_this_session: []
prs_pending_at_handoff: ["#2297 awaiting Test (pytest) — Frontend/Lint/Analyze/Quality/Secret all PASS; review/review FAIL (advisory, pre-existing)", "#2298 awaiting CI", "#2299 awaiting CI"]
issues_closed_this_session: []
issues_filed_this_session: []
issues_open_at_handoff_after_routing: ["#2278 ULP conditional injection (gemini-pro, brief NOT yet written)", "#2279 worktree-branch hook (agy, brief NOT yet written)", "#2280 services.sh preflight (agy or gemini-pro, brief NOT yet written)", "#2281 CI canary starlight (gemini-pro, brief NOT yet written)", "#2285 agent bridge — Cursor + Claude Desktop + Antigravity adapters remaining (codex part shipped via #2299)", "#2287 cursor --resume — DISPATCHED to agy, in-flight at handoff", "#2291 CI gate MDX-source parity — DISPATCHED to gemini-3.1-pro, in-flight at handoff"]
active_dispatches: ["issue-2287-cursor-resume-agy-2026-05-26 (agy, gemini-3.5-flash-high, started 23:47:31Z)", "issue-2291-mdx-source-parity-gate-gemini-2026-05-26 (gemini-3.1-pro-preview, started 23:47:34Z)"]
codex_ui_session: "thread 019e6063-c3da-78d1-acaa-4cd684a08786 idle (last task_complete at 22:37:11Z = m20 attempt #3 fail report). RELAY READY at docs/dispatch-briefs/2026-05-26-m20-anchor-retry-codex-ui-relay.md — fire via `ab send-codex-ui --thread 019e6063-... --cwd ~/.codex/worktrees/3a9a/learn-ukrainian/.worktrees/dispatch/codex/a1-m20-anchor-2026-05-26 --from-file docs/dispatch-briefs/2026-05-26-m20-anchor-retry-codex-ui-relay.md --timeout 3600` ONCE #2297 merges."
empirical_bridge_findings: "codex exec resume <UUID> APPENDS events to original session JSONL (live UI process and resume subprocess share state). ALSO creates parallel rollout JSONL (harmless overhead). Resume subprocess inherits CALLER cwd, not UI session cwd. PONG round-trip 9.8s exit 0. Live-UI-window-refresh not verified empirically — but on-disk thread state is consistent so re-opening UI shows the appended turn."
---

# 2026-05-26 — overnight: bridge built, m20 fixes in CI, routing pivot half done

## State at handoff (compact)

- **Main**: `c30fb45f2a` — no merges from this session yet (3 PRs open)
- **Open PRs from this session**: #2297, #2298, #2299 (in CI)
- **Active dispatches**: 2 (agy on #2287, gemini-pro on #2291)
- **Active builds**: 0
- **Codex UI session**: idle since 22:37:11Z (m20 attempt #3 fail report). Relay file ready to fire via the new bridge ONCE #2297 merges.

## Major shipments — empirical bridge + m20 unblockers

### 1. Agent bridge codex part (#2299, closes codex side of #2285)

The codex part of #2285 is shipped — `ab send-codex-ui --thread <UUID> "<msg>"` injects a turn into a running Codex Desktop UI session via `codex exec resume <UUID> --json -`. Empirically verified against the live m20 session: round-trip PONG in 9.8s, exit 0, final message correctly extracted.

Three findings worth re-stating:

1. **JSONL behaviour**: `codex exec resume` APPENDS to the original session JSONL the live UI process holds open, AND creates a parallel rollout JSONL. Both reflect the same turn. Bridge state should track by thread UUID, not by specific filename.

2. **CWD inheritance**: The resume subprocess inherits the CALLER's cwd, not the UI session's cwd. Pass `--cwd` explicitly when you want codex to run shell commands against a specific worktree.

3. **Open question on UI-window live refresh remains open** — I couldn't verify whether the visible Codex Desktop window updates in real time while user is asleep. Thread state is consistent on disk regardless; re-opening the same thread in the UI shows the appended events.

### 2. m20 unblocker fixes (#2297)

The previous m20 attempt failed 3 gates: textbook_grounding (chunk_context_calls=0), resources_search_attempted (search_attempt_count=0), vocab_count (20/25, no pad headroom). I pushed back on the "escalation to architecture" framing — these were proximate-fixable.

Two fixes in #2297:

- **Plan edit** (`curriculum/l2-uk-en/plans/a1/my-morning.yaml` v1.2.3 → v1.2.4): add `targets.new_vocabulary` block (12 deduped lemmas — what the dispatch brief expected at v1.2.3 but wasn't there) + expand `vocabulary_hints.recommended` from 8 → 18 (added 10 VESUM-verified morning-routine lemmas: чистити зуби, причісуватися, рушник, мило, зубна паста, будильник, сніданок, рано, швидко, готовий).

- **Writer prompt** (`scripts/build/phases/linear-write.md`): MANDATORY rhetoric at line 123/164-179 was getting forgotten by emission time in a 105KB prompt (recency bias). Two strengthenings:
  - End-gate `<end_gate>` block now requires `<chunk_context_calls>N</chunk_context_calls>` + `<chunk_context_chunk_ids>` + `<resources_search_calls>N</resources_search_calls>` + `<resources_search_tools>` sub-nodes with explicit counts. Pipeline can post-hoc compare against telemetry; mismatches surface as tool_theatre.
  - New "PRE-EMIT HARD STOP" callout right before artifact emission, naming the qualifying tools explicitly (search_text alone DOES NOT count toward textbook_grounding; verify_words / cefr_level / style_guide DO NOT count toward resources_search_attempted).

If #2297 lands and codex UI re-runs the build, three gates that failed should now pass. If they STILL fail after this strengthening, then escalation to architecture (diff-only correction) becomes justified.

### 3. Doc hygiene (#2298)

28 untracked orchestration artifacts committed. Lint fixes: glob support in `lint_session_state.py` (codex ephemeral paths can't be enumerated), `ALLOWLIST_VENV_GUARD` mirror in `lint_dispatch_brief.py` for grandfathered historical briefs.

## Routing pivot — 2 of 7 dispatched

Per user direction 2026-05-26 (codex resets soon, spread load to Google quota):

- **#2287 cursor --resume**: DISPATCHED to **agy**, running at handoff (age ~100s, alive).
- **#2291 CI gate MDX-source parity**: DISPATCHED to **gemini-3.1-pro-preview**, running at handoff (age ~100s, alive).
- **Remaining for next session**: #2278 (ULP conditional injection, gemini-pro), #2279 (worktree-branch hook, agy), #2280 (services.sh preflight, agy or gemini-pro), #2281 (starlight canary, gemini-pro). All four have NO briefs yet — write briefs first, then dispatch.

## NEXT-SESSION FIRST ACTIONS — in order

### 1. CI green-check for the 3 session PRs

```bash
gh pr checks 2297 && gh pr checks 2298 && gh pr checks 2299
```

For each PR with all-blocking-green (review/review failure is advisory — pre-existing, ignore):

```bash
gh pr merge <N> --squash --delete-branch
```

**Order**: #2297 FIRST (blocks the m20 relay). #2298 + #2299 in any order after.

### 2. Send m20 build task to codex UI via the new bridge

After #2297 merges, fire the relay:

```bash
ab send-codex-ui \
  --thread 019e6063-c3da-78d1-acaa-4cd684a08786 \
  --cwd ~/.codex/worktrees/3a9a/learn-ukrainian/.worktrees/dispatch/codex/a1-m20-anchor-2026-05-26 \
  --from-file docs/dispatch-briefs/2026-05-26-m20-anchor-retry-codex-ui-relay.md \
  --timeout 3600 \
  --json
```

This uses the bridge I shipped tonight. The relay text already includes the §4 + ULP rubric reference + the explicit fix-delta + the bridge-id-echo ask.

If `--timeout 3600` is hit but no PR has opened yet, that's just the resume subprocess timing out — the codex UI session continues running in the background. Poll for the PR opening separately:

```bash
gh pr list --state open --head 'codex/a1-m20-anchor-*' --json number,title
```

### 3. Watch the 2 in-flight dispatches

- agy on #2287: ~30-45 min wall estimated. Small mechanical edit, low risk.
- gemini-pro on #2291: ~1.5-2.5h wall estimated. New audit script + CI workflow + pre-commit hook + tests + YAML allowlist. Bigger scope.

Check `/api/delegate/active` for status. Either PRs open or `done` status with summary in the delegate log. When PRs land, review + merge if blocking-green.

### 4. Routing pivot — file remaining 4 briefs + fire

Suggested order:
- **#2279** (worktree-branch enforcement hook) → agy. Smallest scope (~30 LOC + tests). Brief takes ~15 min to write.
- **#2280** (services.sh preflight) → agy. Shell-script scope (~50 LOC + tests). Brief ~15 min.
- **#2281** (starlight canary) → gemini-3.1-pro. New CI workflow + smoke test design. Brief ~25 min.
- **#2278** (ULP conditional injection broader scope) → gemini-3.1-pro. Larger architectural — extends `_ulp_practices_rule` from a1 m01-m25 to m26-m55 + adds a1 m41 S2 step-change content. Brief ~30 min, dispatch wall-clock ~2-3h.

Total dispatch wall-clock if all 4 fire in parallel: ~3h (the slowest is the gate). Spread across 2-3 next-sessions if needed.

## Pending follow-ups (not yet filed)

### Antigravity UI adapter — design + first impl

#2285 codex part is shipped (#2299). Per user direction tonight, Antigravity UI is the 4th target. Open empirical questions for the Antigravity bridge:

- Does Antigravity CLI ship a `--resume <session-id>` primitive equivalent to `codex exec resume` and `cursor-agent --resume`? Need `agy --help | rg resume`.
- Where does Antigravity store session JSONLs / transcripts? Inspect `~/.agy/` or wherever the CLI's state lives.
- Does the IDE chat panel reflect CLI-injected turns?

A follow-up commit on the #2285 branch should:
1. Empirically verify the answers above.
2. Build `ab send-antigravity-ui` mirroring the codex adapter shape (`scripts/ai_agent_bridge/_ui_codex.py`).
3. Cross-cutting refactor: extract shared `Bridge-ID` + `find_session_file` + `_extract_final_message` into `_ui_base.py` once we have 2+ adapters in flight.

### Diff-only correction architecture — STILL deferred

Pre-handoff: deferred until #2297's prompt-strengthening proves insufficient. If the m20 retry passes after #2297 lands, this stays deferred. If the same gates still fail, file as its own issue and prioritize.

### lsof-based UI lifecycle detection for the bridge

#2285 design (2026-05-25 user comment) requires probing whether the UI process holds the rollout JSONL open. My bridge in #2299 doesn't yet implement this — it just runs `codex exec resume` and parses the event stream. The lifecycle layer (probe → revive → file-rotation → in-flight-salvage) is follow-up work.

## Critical context for next orchestrator

- **CI hook chain**: pre-commit auto-fix hooks (trailing-whitespace, end-of-file-fixer, ruff --fix, plan-version-backup) repeatedly modified files during this session's commits, causing 2-3 "auto-fix rolled back" cycles per commit. The fix is to re-stage after auto-fix and re-commit. Adds ~30s per commit. Pattern documented in `docs/orchestrator-frictions.md` (now committed via #2298) — consider adding a wrapper script.

- **Plan version bump rule**: Every plan edit needs a `.yaml.bak` snapshot of the previous version in the SAME commit, AND a bumped `version:` field. Hook: `scripts/pre_commit/check_plan_immutability.py`. Got me on the first m20 fix commit attempt; resolved by `git show HEAD:<plan> > <plan>.bak`.

- **`codex exec resume` cwd inheritance**: when invoking the bridge for codex UI work that needs to operate on a specific worktree, ALWAYS pass `--cwd <path>`. The empirical probe ran in MY project root and saw the unpushed local commit b6a34e3174 instead of the dispatch worktree's HEAD. The m20 relay command above includes `--cwd` explicitly.

- **review/review CI failure is advisory + pre-existing**: every PR opened tonight failed `review/review` at ~2m18s. This is the gemini-review CI fix from #2277 not yet propagated through retries. NOT blocking; merge with blocking-green only.

- **Codex UI thread UUID** for m20: `019e6063-c3da-78d1-acaa-4cd684a08786`. Codex PID 83697 had the rollout file open for write at probe time. If the codex process restarts (memory bloat → close), the thread UUID persists but the PID changes. To re-find: `find ~/.codex/sessions -name "rollout-*${UUID}*.jsonl" -mmin -120 | xargs lsof | grep codex`.

## Knowledge encoded this session (auto-loaded next cold-start)

- **Bridge empirics codified in `scripts/ai_agent_bridge/_ui_codex.py` module docstring** — durable doc, not just a memory entry.
- **The PRE-EMIT HARD STOP pattern** for writer-prompt obligations works on the second-iteration principle: name the negative space (which tools DO NOT count). Buried "MANDATORY" rhetoric is recency-defeated; named negatives close the loophole the writer reasoned its way through.
- **Lane 0 vs Lane 1 from #2285**: Lane 1 (resume into running session) is implemented and works. Lane 0 (fresh-spawn with handoff blob, e.g. headless `delegate.py dispatch`) is still the right path for phase-boundary handoffs because UI lifecycle (Electron memory bloat → user closes Codex Desktop overnight) is a first-class concern. Use Lane 1 only when conversation continuity matters (trailblazer/anchor sessions), Lane 0 for everything else.

Full handoff: this file. Next session first item: check #2297 #2298 #2299 CI, merge in order, then fire the m20 relay via the bridge.
