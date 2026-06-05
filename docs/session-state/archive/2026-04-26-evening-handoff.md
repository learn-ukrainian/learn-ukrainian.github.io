# Session Handoff — 2026-04-26 evening

> **Predecessors:** `2026-04-26-overnight-claude.md` → `2026-04-26-autonomous-orchestration.md` → this file.
> **Mode:** Wrapping the day's work cleanly while round-3 grinds. Context-budget hygiene; not blocked by anything.
> **Active dispatch:** Codex round-3 worker still running (pid 11965, ~5 min in of expected 30-90).

---

## TL;DR — what shipped today

Today the reboot moved from **"Phase 4 scaffold drafted with TODOs"** → **"infrastructure ready, exemplar attempted twice, JSON migration in flight."** Six PRs merged in sequence. The reboot's mechanical foundation is now solid.

```
698befbef5  feat(phase-4): pipeline robustness from round-2 dispatch attempt (#1597)  ← TODAY
c91ae3bbe1  feat(phase-4): linear pipeline + A1/20 exemplar draft (#1594)             ← TODAY (squash)
0f03c6acd0  feat(delegate): symlink data DBs into worktrees (#1595)                    ← TODAY
b532271f3d  docs(reboot): ADR for agent responsibilities + V5/V6 legacy markers       ← TODAY
b7db136b1d  chore(wiki): rebuild a1+a2+b1 post citation-shift fix                      ← TODAY
d102a79887  feat(thresholds): per-level per-dim LLM QG floors (#1593)                  ← overnight
```

Plus PR #1596 squash-merged into #1594's branch (writer decouple, not its own commit on main).

---

## Reboot phase ledger (current)

| Phase | Status | Anchor |
|---|---|---|
| 0 — North Star + Lesson Contract | ✅ done | `de97c45572` |
| 1 — Salvage manifest | ✅ done | (multiple) |
| 2 — Config audit (#1583) | ✅ done | `f0635c70ad` |
| 3 — Lesson schema + prompt substitution (#1584) | ✅ done | `d79457e5e9` |
| #1586 — Per-level per-dim LLM QG floors | ✅ done | `d102a79887` |
| #1591/#1592 — Wiki citation-shift fix | ✅ done; verified at scale | `04aae723ab` |
| Wiki rebuild a1+a2+b1 (218/218 articles, 0 orphans) | ✅ done; committed | `b7db136b1d` |
| Reboot agent-responsibilities ADR | ✅ done | `b532271f3d` |
| ADR cleanup #1 (writer decouple in linear_pipeline.py) | ✅ done | folded into `c91ae3bbe1` |
| ADR cleanup §97 (VESUM symlink in delegate.py, #1595) | ✅ done | `0f03c6acd0` |
| **4 round 1** — A1/20 scaffold (#1594) | ✅ done | `c91ae3bbe1` |
| **4 round 2** — partial (writer YAML parse failed; infra hardening landed, #1597) | ✅ partial; merged | `698befbef5` |
| **4 round 3** — strict JSON live exemplar | 🔄 IN FLIGHT (Codex pid 11965) | — |
| Wiki rebuild bio/hist/lit/b2 (Gemini) | 🔄 in flight (slow; user-launched) | — |
| 5+ — Fan-out (A1/4–A1/55 → A2 → B1) | ⏸️ gated on round 3 ship | — |
| 8 — A1/1, A1/2, A1/3 (literacy bootstrap) | ⏸️ saved for last | — |

---

## What's IN FLIGHT right now

### Codex round-3 dispatch

- **Task ID:** `codex-phase4-round3-json-exemplar`
- **Worktree:** `.worktrees/codex-phase4-round3-json-exemplar`
- **Branch:** `codex/phase4-round3-json-exemplar` (off `origin/main` = `698befbef5`)
- **Worker:** pid 11965 (`gpt-5.5`, hard-timeout 4h)
- **Brief:** `.worktree-briefs/codex-phase4-round3-json-exemplar.md`
- **Watcher:** background task `bvqto3zog` — fires `<task-notification>` on terminal status
- **Symlinks:** `data/vesum.db` + `data/sources.db` confirmed working in the worktree

**What round 3 should produce (in order):**
1. **Step 0 commit** — `feat(phase-4): strict JSON output for writer artifacts (#1577 round 3)` — `linear-write.md` migrated to demand fenced JSON blocks for `resources` / `vocabulary` / `activities`; `linear_pipeline.py` parser uses `json.loads` + schema validation, no auto-repair; 3 new tests covering happy path / YAML-block rejection / invalid-JSON rejection.
2. **Step 1** — Live `gemini-tools` writer call with the new strict-JSON prompt. Max 1 corrective redispatch on parse failure (the parse error gets fed back into the prompt as context for the retry).
3. **Step 2** — Real Python QG via VESUM symlink (no fake stub).
4. **Step 3** — 5 independent Codex per-dim LLM QG calls (`pedagogical, naturalness, decolonization, engagement, tone`).
5. **Step 4** — `aggregate_review(scores, "A1")`; PASS = continue, REVISE/REJECT = fail-fast surface.
6. **Step 5** (only on PASS) — stress annotate + MDX + Starlight smoke build.
7. **Step 6** — round-3 exemplar report.
8. **Steps 7-15** — commit, push, PR with author signoff string.

### Wiki rebuilds (user-launched, slow)

| PID | Track | Path |
|---|---|---|
| 6803 | bio | `wiki/figures/` |
| 13598 | lit | `wiki/literature/works/` |
| 13629 | hist | `wiki/periods/` + `wiki/historiography/` |
| 56100 | b2 | `wiki/grammar/b2/` |

All `--writer=gemini --all --force`. Slow throughput (~10-15% in 1.5h). Will continue running for many hours. NOT blocking anything reboot-related. When they finish (or user interrupts), the pattern is: `git add wiki/{figures,literature,periods,historiography,grammar/b2}/ && git commit -m "chore(wiki): rebuild bio/hist/lit/b2 (#1591 follow-up)"` similar to the `b7db136b1d` pattern.

---

## Today's key architectural decisions (recorded)

### 1. Wiki writer = Gemini, ALWAYS

User stated 2026-04-26 AM after the 5h Opus drain on overnight batch wiki rebuild: "I decided to use gemini for now for all wiki. opus is too expensive and i need claude for coding and architecting and organizing." Locked in `docs/decisions/2026-04-26-reboot-agent-responsibilities.md` §1. `compile.py` defaults to gemini.

### 2. Reboot module writer = NOT YET DECIDED

ADR §3. Phase 0 (North Star + Lesson Contract) deliberately doesn't pin a writer. The Phase 4 brief inherited V6-era `pipeline.md:17` `claude-tools` default — that bake-in is now removed (`linear_pipeline.py` parameterized via `WRITER_DEFAULTS`). Decision deferred to Phase 5+ approach via strict bakeoff (same prompt, same packet, same reviewer, N attempts; compare PASS rate + token cost).

### 3. Path 1 chosen for round 3 (3-agent panel signed off)

Round 2 failed at YAML parsing (`notes: Зворотні дієслова: суфікс ...` — unescaped colon). Three paths surfaced:
- **Path 1 (chosen):** force JSON-only structured output, fail-fast on parse error, max 1 corrective redispatch
- Path 2 (rejected): switch to `claude-tools` — measures wrong number, burns Claude budget
- Path 3 (rejected): bakeoff — premature; need ONE working writer first

Panel review: architecture channel thread `0e3e9b7042c3` — both Codex + Gemini [AGREE] at round 1. Codex's tightening (incorporated): "strict JSON + schema validation, NOT 'JSON-ish with repair'... no YAML-repair pre-parsers; no heuristic JSON cleanup; no LLM-driven regen on parse failure."

### 4. ADR cleanup landed inline

- `pipeline.md` (claude_extensions + .claude via deploy): removed V6-era `claude-tools` writer hardcode + `Gemini builds → Claude reviews` paradigm. Now points at the ADR.
- `docs/architecture/ARCHITECTURE.md`: V5/V6-ERA banner + line-7/96/190 annotations.
- `scripts/build/v6_build.py`: legacy markers on docstring (line 29) + argparse help (10706-10707).
- `MEMORY.md` REVIEWER POLICY: rewritten to match ADR.
- `tests/test_determine_reviewer.py`: already aligned (21 tests passing).

---

## Open architectural questions still pending user decision

1. **Phase 5+ batch module-writer choice** — explicitly deferred per ADR §3; bakeoff at Phase 5+ entrance, not now.
2. **PR #1597's pre-existing test debt** — bundled `gpt-5.4` → `gpt-5.5` updates and `_TEST_PYTHON` → `sys.executable`. Both blocked the pre-commit hook on `test_agent_runtime.py`. They're now fixed but not their own commit/PR; if there's a strong case to extract them retroactively, it's a future cleanup.
3. **What happens if round 3 fails for content reasons** (LLM QG dim < floor on pedagogical/naturalness/decolonization despite JSON parse success)? That's the diagnostic signal for a Phase 4 round 4 = real bakeoff (Claude vs Gemini on the same exemplar prompt). Both panel members confirmed this is the right next step IF round 3 surfaces content failures, but it's a future decision based on real data.

---

## Cold-start protocol for next session

If the next session picks up before round 3 finishes:

```bash
# 1. Get the lay of the land
git -C /Users/krisztiankoos/projects/learn-ukrainian log --oneline origin/main -5
gh pr list --state open --limit 10 --json number,title,isDraft,baseRefName

# 2. Check round-3 status
.venv/bin/python scripts/delegate.py status codex-phase4-round3-json-exemplar
# If running: leave it alone, the watcher (bvqto3zog) will fire
# If done with worktree_dirty_on_exit=true: read result file, follow the
#    overnight pattern (commit substantial work as draft PR for visibility)
# If done with worktree_dirty_on_exit=false: review the PR, merge if green
# If failed/timeout: read stderr_excerpt, decide whether to re-dispatch
#    with tightened brief

# 3. If round 3 ships PASS:
#    - Review the round-3 PR (artifacts under curriculum/l2-uk-en/a1/my-morning/)
#    - Verify the LLM QG report has 5 dim entries + aggregate verdict PASS
#    - Verify Python QG report shows VESUM gate green + 4 separate vocab gates
#    - Confirm the literal "**Phase 4 author signoff:** confirmed." string in PR body
#    - Merge --squash --delete-branch
#    - Phase 4 ships; Phase 5 fan-out planning unblocks

# 4. If round 3 ships REVISE/REJECT (LLM QG content failure):
#    - Read the per-dim LLM QG report carefully — which dim failed, why
#    - If pedagogical/naturalness/decolonization failed: writer-prompt regression
#      OR genuine Gemini content limitation. Either way, that's the signal to
#      run round 4 as a writer bakeoff (claude-tools vs gemini-tools on the
#      same exemplar prompt) per ADR §3.
#    - If only engagement/tone failed: less critical, may be prompt-tuning territory.

# 5. Bio/hist/lit/b2 wiki rebuilds:
#    - Check pgrep -f "compile.py.*--track" — if any still running, leave
#    - When all done: commit the wiki changes (mirror b7db136b1d pattern)
#    - Don't touch while user has active rebuild processes running
```

---

## Active background tasks at handoff time

- `bvqto3zog` — `delegate.py wait codex-phase4-round3-json-exemplar` (fires on terminal status)
- 4 wiki rebuild processes (PIDs 6803, 13598, 13629, 56100) — user-launched, no orchestrator action

---

## Worktrees at handoff time

```
/Users/krisztiankoos/projects/learn-ukrainian                                              <main>
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/codex-interactive                 (stale, detached HEAD)
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/codex-phase4-round3-json-exemplar (in flight)
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/verify-a1-1-phaseA-v5             (stale, has uncommitted changes — DO NOT remove without user)
```

`codex-interactive` is clean (no uncommitted) but I couldn't confirm autonomously that its branch is fully merged. Safe-ish to remove if user confirms. `verify-a1-1-phaseA-v5` has 11 uncommitted M+D files — leave it alone.

---

## Open coding issues NOT addressed today (deferred to user)

- #1573, #1571, #1570 — Wiki ingestion bugs (Ukrainian wiki ingestion)
- #1553 — Wiki retrieval overhaul
- #1377 — Wiki corpus expansion to B1+/seminar tracks
- #1373 — Ingest 55 Ukrainian-canonical A1 wikis
- #1351, #1350 — Diagnostic / Bright Kids ingestion
- #1333 — Corpus gap analysis
- #1201 — Release: v1.0 launch

None are reboot-blockers per current scope. Reviewing them is a separate session item.

---

## Lessons learned today

1. **`delegate.py` enforces task-id↔branch convention** — passing `--worktree PATH-EXISTS` with a different task-id than the worktree's branch fails. For stacked PRs (like writer-decouple stacked on PR #1594), use `--base codex/phase-4-a1-20-exemplar` and a fresh worktree path that matches the new task-id.

2. **The "dispatch CLI exits fast" pattern** — `delegate.py dispatch` daemonizes the worker and returns immediately. The first task-notification fires for the dispatcher CLI, not the worker. Use `delegate.py wait <task-id>` in a separate background command for the actual completion notification.

3. **`worktree_dirty_on_exit: true` is Codex's "fail-fast" signal** — Codex deliberately doesn't commit when work is incomplete. Two appearances today (round 1 + round 2). The orchestrator pattern is: read result file, if substantive work shipped, commit + push + open as draft PR.

4. **3-agent panel rounds run in parallel via ThreadPoolExecutor** — round-N responses get written in parallel, so an agent's edit to a file during round-N may not be visible to other agents responding in round-N. Their responses might cite stale state. Always check the actual file state after the round completes.

5. **Pre-commit hook + worktrees + .venv** — delegated worktrees don't have their own `.venv`, but the pre-commit hook tries to run pytest. Tests that hardcode `<repo>/.venv/bin/python` fail. Fix: use `sys.executable`. Now done in `tests/test_agent_runtime.py`; same pattern needed elsewhere if other tests are similarly hardcoded.

6. **The 5h Opus rolling limit is real** — batch token-heavy work (wiki rebuild, batch module writing) drains it fast. Reserve Opus for coding/architecture/orchestrating; route content generation to Gemini (unmetered subscription).

---

## Decision journal note

ADR `docs/decisions/2026-04-26-reboot-agent-responsibilities.md` is the authority for the responsibilities split clarified today. ADR `docs/decisions/2026-04-26-llm-qg-per-dim-thresholds.md` (yesterday) is the authority for the LLM QG aggregator. Both reference each other and the North Star + Lesson Contract. Future ADRs that change these should explicitly supersede them.

The Path-1 decision discussion is recorded in the architecture channel thread `0e3e9b7042c34c6d9b6f87bfcfc7f0fa`. Not yet promoted to a formal ADR — could be, if the JSON migration becomes a permanent contract rather than a tactical round-3 fix.
