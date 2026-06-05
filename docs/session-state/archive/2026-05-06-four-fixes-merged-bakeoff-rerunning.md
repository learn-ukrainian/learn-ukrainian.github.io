# Session Handoff — 2026-05-06 (four fixes merged, bakeoff re-running)

> **Predecessor:** `2026-05-06-runbook-strand-1-and-bakeoff-validation.md` (the runbook this session executed)
> **Mode:** Orchestrator-only overnight session. User instruction: "keep grinding until 50% ctx, delegate everything."
> **Earlier draft:** `2026-05-06-strand-1-vesum-and-textbook-grounding.md` (now stale — superseded by this file).

---

## TL;DR — what happened tonight

**Mission:** find the writer (Claude / Gemini / Codex) that can produce A1 Ukrainian content. The writer-selection bakeoff was blocked by 3 prompt/pipeline failures (#1720). Strands 2+3 of #1720 shipped last session via #1721. This session shipped strand 1 + 3 NEW pipeline-bug fixes that emerged when I read the prior bakeoff's `python_qg.json` and traced the actual failures.

**Four PRs merged tonight:**

| PR | Issue | Fix | Main commit |
|---|---|---|---|
| #1726 | #1720 strand 1 | tool-theatre detection (cited tools must match actual trace) | `1661fbe081` |
| #1727 | #1722 | vesum_verified treats -ся as postfix; allows proper-noun case forms | `4c43d2aa32` |
| #1728 | #1723 | citations_resolve loads plan_references as allowlist; author+grade+page matching | `5bd073898f` |
| #1729 | #1724 | immersion sentence splitter recognizes dialogue/table/bullet boundaries | `5a03385139` |

**Main is at `5a03385139`.** All 4 fixes deployed. Bakeoff re-running.

**Bakeoff dispatched** as task `bakeoff-validation-2026-05-06` at 02:42 UTC. Wipes `audit/bakeoff-2026-05-05/` first, then runs all 3 writers + 6 cross-family reviews + aggregator. Hard timeout 120 min. Wait task firing notification on completion.

---

## Three issues filed but NOT YET dispatched

These survived the night unaddressed. Pick up in next session if bakeoff outcomes warrant.

- **#1725** — `[V7 prompts] Writers cite textbooks without using them — author-anchored organic content (NOT verbatim quote)`. **The most user-impactful finding.** All 3 writers in the 2026-05-06 bakeoff cited textbook references in `<plan_reasoning verification>` but never called `mcp__sources__search_text` to retrieve the actual content. They invent dialogues from training data. The corpus has rich content the writers should be using:
  - Avramenko Grade 6 p.10 — actual native morning-routine text ("Я прокидаюсь о сьомій годині. Виконую кілька фізичних вправ. Потім загартовуюся контрастним душем")
  - Zaharijchuk Grade 4 p.162 — complete -ся drill paradigm
  - Karaman Grade 10 p.176 — grammar block on -ся as descended from "коротка форма зворотного займенника себе в Зн. в. однини"
  - Vashulenko Grade 2 p.48 — folktale dialogue using reflexive verbs in register

  **User reframed the issue twice this evening:**
  1. Initial proposal: verbatim quote ≥30 words per reference + new `textbook_grounding` gate that string-matches blockquotes against search results.
  2. **User correction:** "it should not be required to quote but it should search for dialogs and use them, we need him to create organic content and not fulfilling an instruction." Verbatim-quote framing rejected. Refined to: pre-load textbook excerpts into `knowledge_packet.md`; writer reads for register/cadence/voice; no quote-mandate gate.
  3. **User refinement:** "cannot we tell him to use some the others style?" Author-anchored: each section gets a `style_anchor` (Karaman / Avramenko / Vashulenko / etc.) telling the writer which author's stylistic register to absorb for that section.

  See #1725 for the full evolved proposal (3 phase A's: A1 = packet enrichment, A2 = per-section style_anchor in plans, B = prompt nudge "absorb don't copy").

- **#1718** — `[chore] Triage orphaned dirty tree on main from 2026-05-05 morning session`. Predecessor handoff said "leave it alone" — the runbook explicitly told me not to touch it. Still untouched. User decision needed: commit-as-is, stash, or split.

- **CodeQL alerts #16, #17, #20, #21, #22, #23, #166, #167** — false-positive dismissal still blocked on `gh auth refresh -s code-scanning` from the user side. Tried tonight; got 403 on all 8. Needs user action.

---

## Other work tonight

- **#1688 closed** as superseded — playgrounds portion handled by #1713 (already merged); podcast portion blocked on the same code-scanning token scope. Worktree + branch cleaned.
- **3 stale worktrees cleaned** — `gemini/codeql-D-js-html-xss` (from closed #1688), `codex/1720-strand-1` (post-merge), `codex/1722-vesum-postfix` (post-merge), `codex/1723-citations-from-plan` (post-merge), `codex/1724-immersion-splitter` (post-merge). All branches deleted.
- **8 dispatch briefs written** in `docs/dispatch-briefs/2026-05-06-*.md`.
- **5 issues filed:** #1722, #1723, #1724, #1725, plus the strand-1 close-out comment on #1720.

---

## Critical findings preserved

### 1. Production state is bare

`starlight/src/content/docs/a1/` has ONE published module (`my-morning.mdx`, 1854 words, marked `draft: true`). The A1 landing page declares 55 modules; all show `status: "locked"`. **The V7 pipeline has never successfully published an A1 module end-to-end.** The "agents suddenly creating junk" framing was wrong — there's no regression because there's no working baseline.

### 2. Writers' initial drafts are competitive

All 3 writers in the 2026-05-06 22:19 bakeoff produced 1400-1450 word initial drafts that hit the 1200 target. Quality of the Ukrainian text is reasonable on first pass. The "n/a everywhere" REPORT.md was because no writer survived the python_qg gates — pipeline plumbing failure, not writer-prose failure.

### 3. Writers don't interactively use the wiki / textbooks (#1725)

`tool_calls_total = 0` for every writer. They use the pre-packaged 227-line `knowledge_packet.md` (wiki pedagogy excerpts) but never call `search_text` to query interactively. They cite textbook authors by name without quoting them. The corpus has rich textbook content (Avramenko, Zaharijchuk, Karaman, Vashulenko verified) that the writers ignore.

### 4. Per-writer behavioral signal

The 12 stray Python debugging files in `audit/bakeoff-2026-05-05/gemini/` (`count_words.py`, `split_test.py`, `test_parse*.py`, etc.) reveal Gemini's failure mode is unique — when stuck, it tries to debug. It even imported `scripts.audit.alignment_audit` from the project. Claude and Codex emitted one attempt and stopped. Useful for writer-selection: Gemini is most adaptive but generates noise; Claude/Codex are cleaner.

### 5. Preview signal favoring Claude (very preliminary)

PR #1729's body notes: with all 4 fixes applied to the 2026-05-06 bakeoff outputs (i.e. re-running `_immersion_gate` only, not the full bakeoff), **Claude passes; Gemini fails only on low Ukrainian pct; GPT-5.5 fails only on high pct**. This is from OLD writer outputs (which never used tools). The fresh bakeoff with strand-1 enforcing tool-call honesty will produce different drafts.

---

## What to do next session (in priority order)

1. **Read REPORT.md from the bakeoff re-run.** Path: `audit/bakeoff-2026-05-05/REPORT.md`. Predecessor runbook step 4 has the interpretation framework:
   - Strand 1 acceptance: `tool_theatre_violations: []` AND `tool_calls_total > 0` for ≥1 writer
   - Strand 2: `gate_present=true` for ≥1 writer
   - Strand 3 + #1722/#1723/#1724: ≥1 writer publishes a `module.md` → ≥1 review runs
   - Winner: `min_dim ≥ 8` AND `weighted_score ≥ 8.5` AND `tool_call_density > 0.5/100w`
2. **If a winner emerges**: file the writer-selection decision per `docs/decisions/2026-04-26-reboot-agent-responsibilities.md` §3. Surface to user for sign-off. **This is the milestone the entire #1577 EPIC has been building toward.** Update `pipeline.md` rule with the chosen writer.
3. **If outcome C/D (still failing somewhere)**: diagnose. The 4 fixes addressed every failure I could identify in the prior `python_qg.json`. New failures = new findings. Possibly fire #1725 (textbook-grounding via packet enrichment) as the next strand.
4. **#1725 design call**: even with strand 1 forcing tool calls, the writer's prose may still be invented (just with a tool call attached). The packet-enrichment fix is the deeper content-quality lever. Decide: implement via dispatch, or hand-prototype on one module first?
5. **Triage #1718**: get user decision on the orphaned dirty tree. Until that's resolved, every session inherits it.

---

## Cold-start protocol

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
source ./.envrc

curl -s http://localhost:8765/api/state/manifest
curl -s http://localhost:8765/api/orient
curl -s 'http://localhost:8765/api/comms/inbox?agent=claude'

git fetch origin main && git pull --ff-only origin main && git status -s
git worktree list

# Read THIS handoff first; then predecessor runbook
#   docs/session-state/2026-05-06-four-fixes-merged-bakeoff-rerunning.md (this)
#   docs/session-state/2026-05-06-runbook-strand-1-and-bakeoff-validation.md (predecessor runbook)

# Check bakeoff status
.venv/bin/python scripts/delegate.py status bakeoff-validation-2026-05-06
ls -la audit/bakeoff-2026-05-05/

# If complete: read REPORT.md
cat audit/bakeoff-2026-05-05/REPORT.md
```

---

## Statistics

- **PRs merged:** 4 (#1726 strand-1, #1727 vesum, #1728 citations, #1729 immersion). All Codex-authored, Claude-reviewed, orchestrator-merged.
- **PRs closed (other):** 1 (#1688 superseded).
- **Issues filed:** 4 (#1722, #1723, #1724, #1725).
- **Codex dispatches:** 4 fix dispatches (sequential pairs: 1722+1723, then 1724) + 1 bakeoff (running).
- **Worktrees cleaned:** 5 (4 post-merge + 1 stale-from-#1688).
- **Inline rebase events:** 1 (rebased citations on top of vesum after vesum merged; force-pushed; CI re-ran clean).
- **Commits to main:** 4 (one per PR).
- **MCP tool calls (orchestrator):** 2 (`search_text` for textbook-corpus verification — confirmed real content exists).
- **User reframings preserved:** 2 on #1725 (verbatim → organic; organic → author-anchored).
- **Estimated wall time:** 02:00–02:45 UTC (45 min) from start to bakeoff dispatch.

---

## In flight at handoff write

- `bakeoff-validation-2026-05-06` Codex dispatch (PID 15890; running; expected 25-90 min wall).
- Wait task on the bakeoff in background (will fire `task-notification` on completion).

When the bakeoff lands, the orchestrator (next session, or this session if context permits) reads REPORT.md and proceeds to step 4–5 of the runbook.
