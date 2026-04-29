# Session Handoff — 2026-04-28 / 04-29 (Phase 4 architectural correction + ADR-008)

> **Predecessor:** `2026-04-28-wiki-cleanup-and-hygiene-flush.md`
> **Successor scope:** Phase 4 retrieval-layer migration (#1631) + ADR-008 implementation (#1632) → enables round-4 bakeoff (#1622)
> **Mode:** Clean exit. Zero dirty files. No background tasks owed.

---

## TL;DR — what shipped (3 commits to main, all pushed)

```
f4df43af06  docs(adr): ADR-008 — targeted gate-specific correction paths (PROPOSED) (#1633)
ad54161ec0  revert: Qdrant fail-fast on deprecated retrieval path (#1628) (#1630)
b5d894d009  feat(qg): per-type extra-field validation in WRITER_JSON_SCHEMAS (#1624) (#1627)
e0f8db8fb1  fix(qg): VESUM gate skips errorWord/error fields in error-correction activities (#1623) (#1626)
ba90cf16cb  fix(infra): fail-fast knowledge packet on Qdrant unavailability + liveness probe (#1625) (#1628)  ← REVERTED by ad54161ec0
253f3c00c4  feat(phase-4): A1/20 round-3.5 verification (#1620) (#1621)
```

5 PRs merged this session (#1621, #1626, #1627, #1628, #1630, #1633), 1 reverted (#1628 by #1630), 4 issues filed (#1622, #1623, #1624, #1625, #1629, #1631, #1632), 4 issues closed (#1620, #1623, #1624, #1625, #1629).

Final state: `git status -s` empty, HEAD = origin/main, only `main` branch, only main worktree.

---

## Three arcs in one session

### Arc 1 — Phase 4 round-3.5 verification → bakeoff trigger verdict

Dispatched Codex round-3.5 verification on A1/20 `my-morning` per the predecessor's open question ("did Gemini comply with anti-meta-narration directives on a fresh build?"). Codex completed 1225s; produced PR #1621 with verdict `Round 3.5 = round-4 bakeoff trigger`.

**Diagnostic findings (cross-agent reviewed):**
- Strict-JSON parser failure on attempt 1 (whitelist bug, not real schema violation) → corrective redispatch fired
- Word count 1020/1200 (15% short)
- Підсумок section 41% short
- Anti-meta-narration ban bypassed via paragraph-level rephrasing (6+ violations, only 3 quoted in dispatch report)
- JSX prop-stuffing in `<DialogueBox>` — gates immersion check
- Two of the dispatch's "failures" were tool bugs, not writer failures

**Cross-agent review on PR #1621 (Gemini + Codex parallel):**
- Gemini: MERGE as diagnostic record
- Codex: REVISE — HIGH blocker: failed Gemini outputs would overwrite canonical curriculum files

**Acted on Codex's REVISE:** restored `curriculum/l2-uk-en/a1/my-morning/*` to round-3 baseline (`c91ae3bbe1` from #1594), preserved failed Gemini outputs at `experiments/phase-4/round-3.5/` for evidence. Then merged.

### Arc 2 — Three-agent gate fix dispatch (Codex / Claude / Gemini)

Per user directive 2026-04-28 ("don't send all coding to codex, send it to all 3 agents"), dispatched 3 gate-bug fixes in parallel:

| # | Agent | Task | Outcome | Merge |
|---|---|---|---|---|
| #1623 | **Codex** | VESUM gate skip errorWord/error in error-correction | One-shot win, 5 min, no rework | `e0f8db8fb1` (#1626) |
| #1624 | **Claude** (×3 rounds) | Per-type extra-field validation + 2-gate consistency | 3 REVISE rounds — Round 1: lesson-schema as wrong source; Round 2: built explicit map; Round 3 (orchestrator inline): 2-gate consistency fix in `_component_prop_gate` | `b5d894d009` (#1627) |
| #1625 | **Gemini** (×2 rounds) | Qdrant fail-fast + liveness probe | Functional but rate_limited 2× before summary; orchestrator filled in finding disposition from code inspection | `ba90cf16cb` (#1628) — **REVERTED later, see Arc 3** |

**Multi-agent code policy signal observed (empirically, in this session):**
- **Codex** (mechanical bug fixes): one-shot win, fastest, highest first-pass quality
- **Claude** (architectural depth): finds adjacent issues but iterates 1–2 REVISE rounds; in this session caught its own missing schema layer twice
- **Gemini** (Python infra): viable, but: hits rate limits aggressively (2× in this run), missing summary on cutoff (orchestrator must reconstruct from code), boundary correctness below baseline on first pass; **iterates well** when given specific Codex findings
- **Orchestrator inline** as backup when dispatch hits infra friction (#1627 round-3 hit Qdrant probe + branch-name mismatch; closed inline in 10 min vs another infra cycle)

### Arc 3 — User-caught architectural drift → corrective sweep

After #1626 + #1627 + #1628 merged, user pushed back: *"we don't use Qdrant anymore? why do you want to introduce it back?"*

**Investigation revealed real architectural drift:**
- `scripts/build/research/build_knowledge_packet.py` calls `scripts/rag/query.py` → Qdrant
- That path is **deprecated**. The reboot architecture per user 2026-04-28: `Build wiki: SQLite FTS5 sources MCP + Gemini → wiki/{domain}/{slug}.md` then `Build module: wiki article + MCP for dictionary verification → module`.
- V6 already had the right infrastructure: `_build_wiki_packet` + `compress_wiki_packet` (already in tree, used by `plan_contract.py`).
- V7 `linear_pipeline.py` was inadvertently calling the V6-era Qdrant path instead of the V6 wiki path.

**My mistake (recorded for next session):** inherited "Qdrant outage" framing from the round-3.5 dispatch report; cross-agent review accepted that framing; PR #1628 acted on it. Nobody questioned the premise that Qdrant should be in the architecture. Memory rule #0G (don't inherit failure-class claims without branch verification) was the relevant guard — it caught the round-3.5 inheritance trap on the dispatch artifact, but didn't catch this larger inheritance trap on the architecture itself.

**User then asked broader architectural questions** (auto-heal won't be needed?, what's V7 different from V6?), which surfaced a SECOND architectural issue: ADR-007 enforcement is too brittle for 1700-module Phase-5 fan-out without correction paths. User: *"human triage is not feasible we have to be able to fix detected errors and mistakes"*.

**Corrective sweep:**

| Action | Artifact |
|---|---|
| Wrote ADR-008: targeted gate-specific correction paths | `docs/decisions/2026-04-28-targeted-gate-correction-paths.md` |
| Cross-agent reviewed ADR-008 v1 | Both Gemini + Codex returned REVISE; v2 incorporated all four hard constraints they aligned on |
| Reverted PR #1628 | PR #1630 → `ad54161ec0` |
| Filed real Phase-4 retrieval fix issue | **#1631** wiki migration |
| Filed ADR-008 implementation issue | **#1632** |
| Closed superseded issues | #1625, #1629 (both pointed at #1631 as supersession) |
| Updated round-4 bakeoff prereqs | #1622 comment: prereqs are #1631 + #1632, not "Qdrant up" |
| Merged ADR-008 (PROPOSED status) | PR #1633 → `f4df43af06` |

---

## Open / pending state

### ADR-008 — PROPOSED, awaiting user signoff to flip to ACCEPTED

`docs/decisions/2026-04-28-targeted-gate-correction-paths.md` is on main as PROPOSED. The status flip to ACCEPTED is a separate user action — it's a binding architectural decision and the PR description explicitly invited the user to read before signing off. The implementation issue (#1632) does not require ACCEPTED status to start work, but the doc-level status reflects whether user has reviewed/agreed.

**TL;DR for next session if user reads ADR-008 fresh**: each Python QG gate gets ONE bounded correction attempt under four hard architectural constraints (patch-bounded / full revalidation / pipeline-assisted dictionary / one attempt per gate). Preserves everything ADR-007 killed. Refines, doesn't supersede.

### Round-4 bakeoff (#1622) — blocked on TWO prereqs (was: ONE)

Original brief said "ensure Qdrant up before dispatch." Updated comment on #1622 documents the corrected prereqs:
1. **#1631 wiki migration** — port V6's `_build_wiki_packet` + `compress_wiki_packet` into V7 linear_pipeline; remove Qdrant dependency entirely
2. **#1632 ADR-008 implementation** — per-gate corrective paths in linear_pipeline

Both are independent and can dispatch in parallel.

### Currently NO active dispatches, NO active worktrees, NO background tasks

`git worktree list` is main-only. `pgrep -f _worker` returns empty. State files in `batch_state/tasks/` show all done/finalized.

---

## What's next (cold-start prioritization)

### Path A: Dispatch the wiki migration (#1631) and ADR-008 implementation (#1632) in parallel

Both are independent, both block the round-4 bakeoff (#1622). Per memory rule #0 dispatch caps (max 2 Codex, 2 Claude, Gemini uncapped):

- **#1631 wiki migration** → Claude (architectural — port + integrate; touches retrieval seam)
- **#1632 ADR-008 implementation** → Codex (mechanical — implement the four hard-constraint invariants per the ADR table; well-scoped)

Could also send #1631 to Codex if user prefers, given the V6 reader is already written and this is mostly a port. The architectural depth required is moderate — choose by whoever has cleaner availability.

### Path B: Just dispatch #1631 first, then #1632 sequentially

Lower risk of overlap if the migration touches `linear_pipeline.run_python_qg` (which #1632 also modifies). Safer for less-experienced infra.

### Path C: User wants to review ADR-008 before #1632 dispatches

Reasonable. ADR-008 is a binding architectural decision with cross-agent validation; reading the 13K-byte doc fresh and signing off (or pushing back further) is appropriate. #1631 can dispatch independently in this window.

### What user said to me in this session

User pushed back hard and correctly twice:
1. "we don't use Qdrant anymore" — caught architectural drift
2. "human triage is not feasible we have to be able to fix detected errors" — set the principle for ADR-008
3. "i dont fucking know, we have to find out which one is best. if i would know i would not use you" — when I kept asking decision questions instead of leading

Lesson recorded: lead and decide, push back when the user is wrong, but don't waste the user's time asking what tradeoffs they prefer when adversarial review has already given me the data to choose.

---

## Worth-knowing details

### The pattern that's working: parallel adversarial review via bridge

Used 7 times this session (PRs #1621, #1626, #1627 round-1, #1627 round-2, #1627 final, #1628, ADR-008). Pattern:

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini "..." \
    --task-id <task> --model gemini-3.1-pro-preview &
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-codex "..." \
    --task-id <task> --to-model gpt-5.5 &
# wait + watcher pattern
```

Cost: ~3-5 min wallclock per round per reviewer. Findings: typically 5-10 per PR, with 2-3 of them genuine BLOCKERS. Without parallel review, those would have shipped silently.

Notable: Codex caught the 2-gate inconsistency in #1627 that I missed in inline review, AND the architectural drift back to ladder in ADR-008 v1 that I missed in v1 design. Gemini caught the immersion-gate-should-be-reviewer assignment in ADR-008. Both reviewers catch DIFFERENT classes of issue — keep the parallel-review discipline.

### Gemini code dispatch realities

Gemini did substantive Python infra work in #1625 (first pass) and the REVISE pass. Both ended `rate_limited` before final summary. Pattern: Gemini commits the work, pushes, then hits rate limit on the PR-creation / response-summary step. Orchestrator must:
1. Pull the branch state
2. Inspect commits to verify scope completeness
3. Author the PR body manually
4. Reply to review comments manually

This adds ~10-15 min orchestrator overhead per Gemini code dispatch vs Codex/Claude. Factor in when planning dispatch capacity.

### gh auth in delegate worktrees

Both Claude and Gemini dispatches in this session reported `gh auth status: not logged in` from inside the delegate worktree. They committed + pushed branches successfully (git push works fine from worktrees), but `gh pr create` fails. Orchestrator (main checkout) opens the PR with the dispatch's authored body.

This is a known infra gap. `~/.bash_secrets` has `GITHUB_TOKEN` but doesn't propagate to dispatched subprocesses. File a follow-up issue if it bites again.

### Qdrant probe + branch-name mismatch friction

Two Codex dispatch attempts on #1627 round-3 failed:
1. First: just-merged #1628 fail-fast probe blocked dispatch (Qdrant down → won't launch). Perfect demonstration of the merged fix, but blocked us.
2. Second with `--allow-degraded-rag`: branch-name-from-task-id mismatch (`codex-1627-...` task-id expected `codex/1627-...` branch, but worktree was on Claude's `claude/1624-...` branch).

Resolution: orchestrator inline (15 LOC code + 200 LOC tests). The Qdrant probe is gone now (PR #1630 reverted). The branch-name convention quirk remains — task-ids that span agent dispatches (e.g. cumulative-commit pattern with different agents) need careful task-id reuse.

### `experiments/phase-4/round-3.5/` preserved

Failed Gemini round-3.5 outputs are at `experiments/phase-4/round-3.5/` with a README documenting the failure modes. Useful evidence for the round-4 bakeoff comparison once it fires.

---

## Cold-start protocol for next session

```bash
# 1. Verify clean state
git status -s              # should be empty
git worktree list          # main only
git branch --list          # * main only

# 2. Verify recent main commits
git log --oneline -8
# Expected top: f4df43af06 (ADR-008 PROPOSED) → ad54161ec0 (revert #1628) →
#               b5d894d009 (#1627) → ba90cf16cb (#1628 — reverted) → e0f8db8fb1 (#1626) →
#               253f3c00c4 (round-3.5 verification)

# 3. Read this handoff. Then read ADR-008 if user wants to sign off.

# 4. Check #1631, #1632, #1622 state
gh issue view 1631  # wiki migration
gh issue view 1632  # ADR-008 implementation
gh issue view 1622  # round-4 bakeoff (blocked on #1631 + #1632)

# 5. Default action: dispatch #1631 (Claude or Codex) and #1632 (Codex) in parallel
#    Or: pause for user signoff on ADR-008 ACCEPTED status if user wants review-first.
```

---

## Final stats

- **3 PRs shipped** to main this session (#1626 Codex, #1627 Claude×3-round, #1633 ADR-008)
- **2 PRs shipped + later reverted** (#1628 Gemini, then #1630 revert) — net 0
- **1 PR shipped** for the round-3.5 verification (#1621)
- **5 issues filed** (#1622 bakeoff, #1623 vesum gate, #1624 per-type validation, #1625 qdrant, #1631 wiki migration, #1632 ADR-008 impl)
- **5 issues closed** (#1620 round-3.5, #1623 vesum gate done, #1624 per-type done, #1625 qdrant superseded, #1629 qdrant residuals superseded)
- **1 ADR written + cross-agent reviewed** (ADR-008 PROPOSED on main)
- **3-agent dispatch validated** as a workflow (Codex/Claude/Gemini all shipped real Python code; quality + cost profiles documented in this handoff for next time)
- **0 dirty files** at session close
- **0 background tasks** owed
