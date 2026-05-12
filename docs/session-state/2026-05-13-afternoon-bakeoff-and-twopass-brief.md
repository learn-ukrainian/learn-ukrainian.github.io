---
date: 2026-05-13
session: "Afternoon — full pipeline cleanup, fair-env bakeoff verdict (claude-tools for A1/A2 on merit), two-pass workflow idea queued for multi-agent discussion"
status: ok
detail: 2026-05-13-afternoon-bakeoff-and-twopass.html
main_sha: 9f1bf99caa
main_green: true
open_prs: 0
active_dispatches: 0
merged_today: [1902, 1904, 1906, 1907]
rejected_today: []
filed_today: [1903, 1905, 1908]
closed_today: [1900, 1901]
in_flight: []
blocked: ["a1/my-morning publication — claude artifact has 5 soft gate fails; needs prompt-tuning round OR pipeline gate-side followups OR two-pass workflow experiment"]
next_p0: "Open multi-agent discussion (claude + codex + gemini via `ab discuss`) on the TWO-PASS WORKFLOW IDEA: simulate a Ukrainian teacher writing the L1 module first (curriculum/l2-uk-direct or l1-uk), then deriving the L2-EN module from their own work. Get colleagues' read on (a) whether the decoupling helps AI specifically, (b) compute cost vs quality gain, (c) what the Pass 2 prompt looks like. After discussion converges, design + run one a1/my-morning two-pass test."
agents: [claude, codex]
worktrees_open: 2
ci_notes: |
  All 4 fix PRs merged with clean CI (#1902 OSError, #1906 writer-telemetry, #1907 rollout-matcher, #1904 vesum-gate after gitleaks transient-infra retry). Main green at `9f1bf99caa`. ADR `2026-05-06-writer-selection-codex-gpt55.md` REVISED-AGAIN with empirical fair-env evidence.
incidents:
  - "Two transient CI issues today: PR #1904 gitleaks failed on Docker GHCR pull timeout (Client.Timeout, exit 125) — resolved via empty-commit push. Per-PR pattern: Gemini-Dispatch advisory `review / review` keeps failing, which is non-blocking per #M-0.5."
  - "Claude bakeoff today produced a 1205-word artifact with 9 MCP calls + populated result_summary (writer-telemetry fix lands cleanly on claude adapter). Failed python_qg after ADR-008 retry on 5 soft fails: plan_sections (1 over budget), citations_resolve (prose citations don't match references[]), textbook_grounding HARD (gate parser can't read MCP formatted-text result), vesum_verified (error-correction sentence-level exclusion gap), immersion 25.4% vs cap 24%."
  - "Codex bakeoff today (retry 2 post schema-fix `author`+`role`) produced a complete 996-word artifact with 5 MCP calls (rollout-matcher fix VISIBLY works — pre-fix bakeoffs reported tool_calls_total=0 for 3 cycles, all measurement artifact). Failed python_qg on 7 fails: word_count (996/1200 under), all 4 section budgets under, formatting (missing model-answer callout), immersion 51.77% (2× cap), citations, textbook_grounding HARD, truncation artifact `равцова` for Кравцова."
---

# Brief — 2026-05-13 afternoon — pipeline cleanup, fair-env bakeoff, two-pass idea queued

> Machine-readable companion to `2026-05-13-afternoon-bakeoff-and-twopass.html`.
> Predecessor: `2026-05-13-midday-pipeline-gate-fixes-brief.md`.

## TL;DR

- **Pipeline fully fixed today.** All 4 PRs merged: #1902 (#1901 OSError) + #1907 (#1903 codex rollout matcher) + #1906 (writer-telemetry result_summary) + #1904 (vesum distractor exclusion) + schema fix for `author`/`role` in resources.yaml.
- **First fair-env bakeoff complete** (`audit/bakeoff-2026-05-13-midday/`). Both writers produced complete artifacts. **Claude-tools wins A1 on content merit** (1205w vs 996w; 1 vs 4 section budget misses; 25.4% vs 51.77% immersion). User decision: **claude-tools is the V7 writer for A1+A2**.
- **ADR REVISED-AGAIN** (`9f1bf99caa`) — the 3 pre-fix bakeoffs are now explicitly disqualified as evidence (rollout-matcher artifact). Codex-tools NOT disqualified globally; re-bakeoff at B1+/seminar deferred until A1/A2 ships.
- **Three issues filed today:** #1903 (codex rollout-matcher fix, merged via #1907) · #1905 (pipeline replay-mode regression suite under #1865 EPIC) · #1908 (layered-harness audit — push advisory rules to hooks/permission denies).
- **User's two-pass workflow idea is queued as P0 for next session opening** — simulate a Ukrainian teacher writing L1 first, then deriving L2-EN. Wants multi-agent discussion (claude + codex + gemini) before designing the test.
- A1/my-morning publication still blocked on 5 soft gate fails (claude artifact) — needs writer-prompt tuning OR pipeline gate-side followups OR the two-pass experiment.

## Session totals

| Type | Count | Detail |
|---|---|---|
| Commits to main | 9 | `492d781dfd` hook fix · `c6bb2faabb` rules sync · `30dfc4ab6b` brief · `2c38ebd11c` #1902 OSError · `ae82644c1c` brief · `02d8a3a6a1` #1906 telemetry · `af5b169234` #1907 matcher · `49b151eca9` #1904 vesum · `69fdee140c` #1900 audit · `7393a2b2b6` midday handoff · `9f1bf99caa` ADR + bakeoff artifacts |
| PRs merged | 4 | #1902 #1906 #1907 #1904 |
| Issues filed | 3 | #1903 #1905 #1908 |
| Issues closed | 2 | #1900 #1901 |
| Bakeoffs run | 2 (claude+codex) | `audit/bakeoff-2026-05-13-midday/` |
| ADR revisions | 1 | writer-selection REVISED-AGAIN with fair-env evidence |
| MEMORY edits | 1 | #2 thresholds: 500K+ handoff zone (was 300K), per user's "we spend lots of tokens on handoffs" feedback |

## What the bakeoff actually showed

| Metric | claude-tools | codex-tools |
|---|---|---|
| Module produced | 1205w | 996w (−204 under target) |
| Section budgets (4× 270-330) | 1 over (336w) | All 4 under (152-172w) |
| Formatting (model-answer callout) | ✅ | ❌ missing |
| Immersion vs `a1-m15-24` cap 24% | 25.4% (1.4 over) | 51.77% (27 over — 2× cap) |
| MCP tool calls | 9 (3× verify_words, 5× search_text, 1× search_style_guide, populated `result_summary`) | 5 (2× verify_words, 3× search_text, empty `result_summary` — codex-side capture gap remains as followup) |
| Truncation artifacts | none | `равцова` for Кравцова |
| Language quality (russianisms/surzhyk/calques/paronyms) | ✅ all | ✅ all |
| 9 other structural gates | ✅ | ✅ |

Both failed `python_qg` after ADR-008 correction retry. Claude's content quality is closer to A1 policy + budget targets. The "codex tool_calls_total=0" pattern from 3 pre-fix bakeoffs was 100% measurement artifact of the rollout-matcher bug.

## THE next-session opening — two-pass workflow discussion

> User stated at session close: *"i wuld like to simulate: a ukraian writes the lesson (plans it and writes in down in ukraian ) this is the l1 version, then based on his ukranian work writes the lessons for english speakers. does this make sense for AI ?"* And: *"we do it in the new session and the start the nre sesion with discusdsing this what we talked about with the collegesas well"*

**Opening action for next session:** open a multi-agent discussion channel with Codex + Gemini on the two-pass workflow idea. Command shape:

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py discuss \
  twopass-workflow-2026-05-13 \
  --with codex,gemini \
  --context-file docs/session-state/2026-05-13-afternoon-bakeoff-and-twopass-brief.md \
  --topic "Should V7 split content production into two passes: Pass 1 writes UK-only (l2-uk-direct or l1-uk), Pass 2 derives the L2-EN module from Pass 1's validated UK content? See brief for empirical context."
```

### What to surface to colleagues

1. **The empirical observation today:** claude-tools went English-first (25.4% UK), codex-tools went Ukrainian-first (51.77% UK). Neither hit the policy sweet spot of 18-22%. Both look like "compromise outputs" where one concern bled into the other (single-pass writer doing both ped-linguistic + EN-scaffolding decisions concurrently).

2. **The hypothesis:** decoupling lets Pass 1 focus on Ukrainian linguistic depth + decolonized pedagogy without English-scaffolding pressure, then Pass 2 focuses purely on English scaffolding without changing UK content. Independently tunable prompts; each smaller than today's 127 KB.

3. **The Pass-1 free bonus:** Pass 1 artifact is independently shippable to `l2-uk-direct` track (L1-agnostic learners). NOT throwaway work.

4. **The risks claude already named (don't hide these from colleagues):**
   - 2× LLM compute per module
   - Pass 2 translation loss (some pedagogical decisions are inherently bilingual — gloss decisions, false-friend warnings)
   - "Ukrainian-first" doesn't automatically mean "better Ukrainian" — codex tried this and produced *more* but not *better* (truncation, missing structure)
   - Reviewer phase also doubles

5. **The pragmatic check (claude's recommendation):** run ONE test on a1/my-morning before committing — build `l2-uk-direct/a1/my-morning`, compare UK content depth to today's bakeoff outputs, decide based on evidence.

### Open questions for the colleagues

- Does Codex see a pipeline-side reason this would be unusually expensive or risky?
- Does Gemini (wiki writer + closer to the corpus) have a view on whether Pass 1 could draw from richer source material than today's knowledge_packet?
- Are there prior-art workflows from other curriculum projects (kubedojo, etc.) that map cleanly?
- Is the `l2-uk-direct` track's V7 build path actually wired up, or would it need scaffolding first?

### Decision shape expected

After 1-3 rounds of multi-agent discussion + 1 user signoff: either
- (a) Run one a1/my-morning two-pass test → empirical evidence drives next move.
- (b) Skip two-pass, tune the single-pass claude prompt (budget/citation/immersion discipline) + fix the remaining pipeline gate gaps → ship a1/my-morning under single-pass.
- (c) Do BOTH in parallel (low-cost) and pick winner.

## Pipeline state — what's actually fixed vs still has gaps

### Fixed and shipped today

- `_prepare_query` OSError on >255-byte Cyrillic queries → bounded byte-length probe + try/except OSError (#1901 / #1902)
- Codex rollout-matcher fail-fast on AGENTS.md envelope → iterate-all (#1903 / #1907)
- Writer-telemetry: `result_summary` was empty for `search_text` → adapters populate `result` from output_summary + summarizer preserves textbook items (#1906) [WORKS for claude adapter; codex adapter has separate codex-side capture gap NOT fixed]
- Vesum gate: MC distractor (`correct: false`) + pronunciation transcription exclusions (#1904)
- `resources.yaml` schema accepts `author` + `role` fields (this session's inline 5-LOC fix)
- ADR REVISED-AGAIN with truthful empirical verdict

### Still-open pipeline followups (NOT blocking the two-pass discussion)

These remain — file follow-up issues OR fold into the next pipeline-fix dispatch when prioritized:

1. **`vesum_verified` gate's `error-correction` exclusion is incomplete** — current code excludes `error:`/`errorWord:`/`error_word:` fields but NOT `sentence:` fields. Today's claude artifact had `снідаюся`/`йдуся` in `sentence: "Я снідаюся..."` flagged. Plus `діал` (abbreviation for `діалектне` in didactic prose).
2. **`textbook_grounding` gate's `_is_textbook_result()` parser** — MCP returns formatted markdown text (`### Result 1 - Source: Grade X, author / Text: ...`); the gate looks for structured fields (`source_type='textbook'`). The writer-telemetry fix captures the data correctly now; the parser hasn't been taught to read it. Today's HARD blocker on both writers.
3. **Codex-side `result_summary` capture** — writer-telemetry fix #1906 worked for claude (verified: `result_summary={count: 1, items: [{type: 'text', text: 'Found 5 res...'}]}`). Codex still emits `result_summary={}` because the codex adapter path is different. Separate fix needed.
4. **Immersion display vs policy** — `python_qg.json` shows `max_pct: 35` but policy `a1-m15-24` actually caps at 24%. Either policy lookup is wrong OR the display field is misleading. Cosmetic but confusing.
5. **claude writer prompt tuning** for budget/citation/immersion adherence — out of pipeline scope, this is a writer-prompt-engineering item.

## Carry-over queue (priority-ordered)

| # | Item | State |
|---|---|---|
| 1 | **Multi-agent discussion: two-pass workflow** | 📋 P0 — opening action for next session, command + context above |
| 2 | After discussion: decide path (two-pass test / tune single-pass / both) | 📋 Decision point |
| 3 | **a1/my-morning publication** (still blocked) | 📋 Blocks on #1 outcome |
| 4 | **#1905** Pipeline replay-mode regression suite (under EPIC #1865) | 📋 Structural fix; prevents future "build cost reveals what test would have caught" |
| 5 | **#1908** Layered-harness audit — push rules to hooks (under EPIC #1865) | 📋 Structural fix; prevents recurrence of advisory-rule violations |
| 6 | Pipeline followups 1-4 above (vesum sentence exclusion / textbook_grounding parser / codex result_summary / immersion display) | 📋 Bundle for one Codex dispatch when scope is right |
| 7 | Autonomous-dispatch decision card (`docs/decisions/pending/2026-05-12-autonomous-codex-dispatch-narrow-class.md`) | 📋 Still pending signoff |
| 8 | Decision-graph UI + multi-UI-channel — pending Decision Cards | 📋 Background |
| 9 | Worktree cleanup: only `bakeoff-2026-05-12-night` + `codex-interactive` remain — both intentional | ✓ Already clean |
| 10 | Codex rebakeoff at B1+/seminar scope | 📋 Deferred until A1/A2 ships |

## Pending Decision Cards (unchanged from morning)

| File | Status |
|---|---|
| `2026-05-12-autonomous-codex-dispatch-narrow-class.md` | PROPOSED |
| `2026-05-09-decision-graph-view.md` | PROPOSED |
| `2026-05-06-multi-ui-channel-participation.md` | PROPOSED |

## Handoff economics — encoded this session

MEMORY #2 thresholds were raised this session per user feedback: handoffs cost ~20-35K tokens (write brief + cold-start next + re-orient). Below 400K stay in session, 400-500K natural breaks only, 500K+ real handoff zone. Auto-compact at 750K still forbidden.

THIS handoff is user-requested for a topic shift (move two-pass discussion into a fresh session with multi-agent context), not budget-triggered.

## Predecessor brief

`docs/session-state/2026-05-13-midday-pipeline-gate-fixes-brief.md` — sets up the 3 fix dispatches that landed during this session. Read for context on the #1900 codex MCP visibility investigation that surfaced the rollout-matcher bug (the headline reframe of this whole day).

---

*Format spec: `claude_extensions/rules/workflow.md` § "Two-tier handoffs". Companion HTML: `2026-05-13-afternoon-bakeoff-and-twopass.html`. Opening action for next session: `ab discuss twopass-workflow-2026-05-13 --with codex,gemini`.*
