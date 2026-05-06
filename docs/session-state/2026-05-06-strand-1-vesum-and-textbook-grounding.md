# Session Handoff — 2026-05-06 (strand-1 dispatch + vesum tokenizer + textbook-grounding investigation)

> **Predecessor:** `2026-05-06-runbook-strand-1-and-bakeoff-validation.md` (the runbook this session executed)
> **Mode:** Orchestrator-only overnight session. User went to bed early; instruction was "keep grinding until 50% ctx, delegate everything."

---

## Where we are

**Mission:** find the writer (Claude / Gemini / Codex) that can produce A1 Ukrainian content. The writer-selection bakeoff has been blocked by 3 prompt/pipeline failures (#1720). Strands 2+3 of #1720 shipped via #1721 last session. **This session attacked strand 1 + uncovered the deeper python_qg gate bugs that would block bakeoff publication even after strand 1 lands.**

The actual situation, honestly:

- **Production has 1 published A1 module** (`starlight/src/content/docs/a1/my-morning.mdx`, 1854 words, marked `draft: true`). The other 54 A1 modules show `status: "locked"` on the landing page. The V7 reboot pipeline has never successfully published an A1 module end-to-end.
- **The "junk" framing is misleading.** All 3 bakeoff writers produce reasonable initial drafts (1400-1450 words, hits the 1200 target). The "all n/a" REPORT.md is because no module gets through python_qg → no review runs → no scores. Pipeline gates fail, not the prose.
- **Writers don't call MCP tools.** `tool_calls_total = 0` for every writer in the 2026-05-06 22:19 bakeoff. They cite tools in `<plan_reasoning verification>` blocks without calling them. They use the pre-packaged `knowledge_packet.md` (227 lines of wiki pedagogy excerpts) but never query `search_text` to retrieve textbook content interactively.

---

## What shipped tonight

### Dispatches in flight (status as of handoff write)

| Issue | Branch | PR | Status |
|---|---|---|---|
| **#1720 strand 1** (tool-theatre detection) | `codex/1720-strand-1` | not-yet-opened | Codex finished impl (commit `bb0746c5db`); presumed in adversarial-review or PR-creation phase. Wall: 12.5 min as of write. |
| **#1722** (vesum tokenizer postfix-aware) | `codex/1722-vesum-postfix` | not-yet-opened | Just dispatched; ~1 min wall. |

### Issues filed this session

- **#1722** — `[python_qg] vesum_verified tokenizer splits reflexive verbs at -ся, falsely flags suffix fragments`. Terminal failure for Claude in 2026-05-06 bakeoff. Tokenizer breaks `вмиваєшся` → `вмиваєш` + `ся` and checks suffix fragments (`шся`, `тся`, `ться`) against VESUM. Plus rejects proper-noun genitive forms (`Білоуса`, `Дмитра`). Codex dispatch in flight.
- **#1723** — `[python_qg] citations_resolve rejects textbook references already declared in the plan`. Writer cites Караман / Кравцова / Захарійчук (as the plan declared); resolver fails them as "unknown" because it isn't loading the plan's `references` field as the allowlist. NOT yet dispatched.
- **#1724** — `[python_qg] immersion gate flags dialogue blocks as 'long Ukrainian sentences'`. Sentence splitter doesn't recognize line-leading em-dash (`—`) as a dialogue boundary, joins 4-turn dialogues into one mega-sentence. Markdown table rows similarly merged. NOT yet dispatched.
- **#1725** — `[V7 prompts] Writers cite textbooks without quoting them — mandate verbatim retrieval, not just citation`. **The big content-quality finding.** All 3 writers mention textbook references but never quote them. Verified the corpus HAS the content (Avramenko Grade 6 p.10 morning routine; Zaharijchuk Grade 4 p.162 -ся drill; Karaman Grade 10 p.176 grammar block; Vashulenko Grade 2 p.48 folk-dialogue with reflexive verbs). Three-phase fix proposed (writer prompt mandate + new `textbook_grounding` gate + knowledge-packet augmentation). NOT yet dispatched. **This is the most user-impactful finding of the session.**

### Other work

- **#1688 closed** as superseded — playgrounds portion handled by #1713; podcast portion blocked on token-scope refresh.
- **CodeQL false-positive dismissal attempted** for #16, #17, #20, #21, #22, #23, #166, #167 — all 8 returned `403 Resource not accessible by personal access token`. Same scope gap predecessor flagged. Needs `gh auth refresh -s code-scanning` + retry.
- **Stale worktree cleanup** — removed `.worktrees/dispatch/gemini/codeql-D-js-html-xss` + branch.

---

## Critical findings — read these before next session

### 1. Strand 1 alone won't unblock the bakeoff

The 2026-05-06 bakeoff's `audit/bakeoff-2026-05-05/claude/python_qg.json` shows the actual failure path: writer DOES produce a 1276-word module with all structural gates green (word_count ✓, plan_sections ✓, formatting_standards ✓), then dies at `vesum_verified` (8 false-missing tokens, 6 of which are -ся suffix fragments) → `correction_terminal: gate: vesum_verified`. **This is a TOKENIZER bug, not a writer bug.** No amount of writer-prompt strengthening fixes it. #1722 is the real bakeoff blocker.

Citations_resolve and immersion gates also fail on the same Claude output. #1723 and #1724.

### 2. The writers ARE getting wiki content — passively

`audit/bakeoff-2026-05-05/{writer}/knowledge_packet.md` is **227 lines, identical for all 3 writers**. It contains pedagogy excerpts from `pedagogy/a1/my-morning.md` covering: "Послідовність введення" (sequencing), "Типові помилки L2" (common errors), "Словниковий мінімум" (A1 vocabulary), "Приклади з підручників" (textbook example formats).

So writers DO see wiki guidance. They do NOT see verbatim textbook content. The packet describes textbook formats by reference (e.g. "Вправа 1: Аналіз вимови та правопису (Клас 4, Білоус/Заболотний)") but does not embed the actual text. To get verbatim text the writer must call `search_text` — none did. **This is the gap #1725 addresses.**

### 3. Gemini's failure mode is unique — it tries to debug

The Gemini bakeoff dir has 12 stray Python debugging files (`count_words.py`, `split_test.py`, `test_parse*.py`, etc.) — Gemini wrote them while trying to debug why its correction-pass output wasn't parsing. It even imported `scripts.audit.alignment_audit` from the project. Claude and Codex emitted one attempt and stopped. Gemini iterated 14 times in its scratch dir.

This is informative for writer-selection: Gemini is the most adaptive but generates noise; Claude/Codex are cleaner but may need more guidance to recover from failures. Document this in the writer-selection decision when bakeoff produces clean signal.

### 4. Strand 1 implementation is solid

Reviewed Codex's commit `bb0746c5db` before PR opens. Diff:
- `+278` `-3` across 6 files
- Adds `tool_theatre` to `WRITER_CORRECTION_GATES` and as the FIRST gate in `PYTHON_QG_GATE_ORDER` (so it fails fast)
- Extends `WRITER_TOOL_NAMES` proactively with `search_esum`, `search_heritage`, `search_slovnyk_me`
- `_PLAN_REASONING_BLOCK_RE` matches the brief (non-greedy DOTALL)
- `detect_tool_theatre()` returns sorted diff; canonical-only as instructed
- 7 tests added (one extra: `test_detect_tool_theatre_returns_all_citations_when_trace_empty`)
- `test_writer_prompt_mandates_tool_call_match` asserts 6 specific text fragments — strong regression detector
- v7_build.py emits `phase_writer_summary` even on dry-run path so brief's validation works

**Pre-PR review is favorable. Plan to merge after CI green + final adversarial-review pass.**

---

## Open dispatches when you wake up

```bash
# Status of the two in-flight Codex dispatches
.venv/bin/python scripts/delegate.py status 1720-strand-1
.venv/bin/python scripts/delegate.py status 1722-vesum-postfix

# Any PRs?
gh pr list --head codex/1720-strand-1
gh pr list --head codex/1722-vesum-postfix
```

If both PRs are open + green CI: review each, merge, then proceed to bakeoff re-run.
If one is failing: fix or escalate per the runbook outcome scenarios.

---

## What to do next session (in order)

1. **Review + merge strand-1 PR** when it opens. Already pre-reviewed the commit (above). Verify CI green; verify `bakeoff_aggregate.py` doesn't choke on the new `tool_theatre_violations` field.
2. **Review + merge vesum-tokenizer PR** when it opens. Verify it actually fixes the 8 missing tokens against the prior bakeoff output (the brief mandates this validation).
3. **DECIDE before re-running bakeoff:** do you also want #1723 (citations_resolve) and #1724 (immersion) fixed first? They're not the terminal failure (#1722 is) but they're listed as failed in the same python_qg.json. If you re-run bakeoff with only #1722 fixed, you'll likely get past `vesum_verified` and die at `citations_resolve` next. Recommend dispatching #1723 + #1724 in parallel BEFORE re-running.
4. **Re-run bakeoff** via `docs/dispatch-briefs/2026-05-05-bakeoff-full-execute.md` (still valid). 25-90 min wall. Monitor with `delegate.py wait`.
5. **Interpret REPORT.md per runbook step 4.** Strand 1 acceptance: `tool_theatre_violations: []` AND `tool_calls_total > 0` for ≥1 writer. Strand 2: `gate_present=true`. Strand 3: ≥1 writer publishes. python_qg gate fixes: ≥1 writer reaches review. Winner: min_dim ≥ 8 AND weighted ≥ 8.5 AND tool_call_density > 0.5/100w.
6. **If winner emerges:** file writer-selection decision per `docs/decisions/2026-04-26-reboot-agent-responsibilities.md` §3. Surface to user for sign-off. **This is the milestone the entire #1577 EPIC has been building toward.**
7. **If outcome C/D (still failing):** the next strand is #1725 (textbook-grounding). Without verbatim textbook quoting, even a "winning" writer is producing inauthentic A1 content. Plan that strand AFTER bakeoff success on the structural gates.

---

## User context to preserve

User flagged 2026-05-06 evening:
- "be honest, how come the agent suddenly create junk, can you compare it to the current a1 content on the production site? can you tell me where we at compared to that"
- "the agents are not using the textbook dialogs"
- "are they even using the wiki?"

**Honest answers preserved here for next session's continuity:**

1. Agents aren't *suddenly* creating junk — V7 pipeline has never published an A1 module. Production has 1 hand-curated draft. There's no regression because there's nothing to regress from.
2. Writers DON'T use textbook dialogs. The corpus has them (Avramenko/Zaharijchuk/Karaman/Vashulenko verified 2026-05-06 via `search_text`). Writers invent dialogues. #1725 fixes this.
3. Writers DO use wiki — but only the pre-packaged pedagogical excerpts in `knowledge_packet.md`. They do NOT query interactively (`tool_calls_total = 0`). Strand 1 + #1725 address this.

---

## Statistics

- **Issues filed:** 4 (#1722, #1723, #1724, #1725)
- **Issues closed:** 1 (#1688)
- **PRs opened:** 0 (both Codex dispatches in adversarial-review or PR-creation phase as of write)
- **Codex dispatches active:** 2 (strand-1 + vesum-postfix)
- **Worktrees cleaned:** 1 (`gemini/codeql-D-js-html-xss`)
- **MCP tool calls (orchestrator):** 2 (`search_text` for textbook-corpus verification — to confirm content exists)
- **Most-impactful finding:** #1725 — verbatim textbook quoting gap. Surfaced via user's pointed question.

---

## Cold-start protocol for next session

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
source ./.envrc

curl -s http://localhost:8765/api/state/manifest
curl -s http://localhost:8765/api/orient
curl -s 'http://localhost:8765/api/comms/inbox?agent=claude'

git fetch origin main && git pull --ff-only origin main && git status -s
git worktree list

# Read THIS handoff + predecessor runbook
#   docs/session-state/2026-05-06-strand-1-vesum-and-textbook-grounding.md (this)
#   docs/session-state/2026-05-06-runbook-strand-1-and-bakeoff-validation.md (predecessor)

# Check both Codex dispatches
.venv/bin/python scripts/delegate.py status 1720-strand-1
.venv/bin/python scripts/delegate.py status 1722-vesum-postfix
gh pr list --head codex/1720-strand-1
gh pr list --head codex/1722-vesum-postfix
```
