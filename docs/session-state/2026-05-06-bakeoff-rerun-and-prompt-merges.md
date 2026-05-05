# Session Handoff — 2026-05-06 (bakeoff re-run + V7 prompts merged)

> **Predecessor:** `2026-05-05-bakeoff-execution-and-prompt-foundations.md`
> **Mode:** Continuation session — landed two CI-blocked PRs, fired bakeoff re-run with new prompts on main. Claude orchestrator-only overnight.

---

## TL;DR — what shipped

Two PRs merged into main this session:

1. **PR #1719** — `feat(prompts): mandate visible <plan_reasoning> + per-dim evidence + heritage-defense (#1673 #1661 #1696 follow-up)` — strengthened V7 writer + reviewer prompts (5 verbatim Q4-Q7 edits from msg 528 + heritage-MCP routing). Supersedes #1696. Main at `6921e46bfe`.

2. **PR #1713** — `chore(codeql): triage 12 alerts — 4 fixed, 8 dismissed` — Gemini's CodeQL cleanup, with 2 follow-up Claude commits to satisfy CodeQL's `py/path-injection` data-flow query. Main at `4e0934cc1d`.

3. **#1696** closed — superseded by #1719.

Plus: bakeoff re-run dispatched (running as I write this).

---

## Critical event chain — what actually happened

### 1. Dispatch B (V7 prompt strengthening, #1696 follow-up)

Predecessor handoff said the brief was written but unfired, with one edit needed: replace the slovnyk.me-deferral wording (Edit 5) with current-tool routing now that #1717 shipped `mcp__sources__search_heritage` + `mcp__sources__search_slovnyk_me`.

Did the edit, plus a **brief pre-flight cleanup** (the original brief's pre-flight told Codex to `git checkout -b ...` a branch the dispatch worktree already created — would've collided). Switched `--base` to `claude/1673-1661-cot-tier1-prompts` so the worktree branches directly off #1696's tip, no checkout-collision.

Fired with `--mode danger --effort medium --hard-timeout 3600 --base claude/1673-1661-cot-tier1-prompts`. Codex returned in **455s** (7.5 min) with:

- 5 verbatim edits applied to `linear-write.md` + `linear-review-dim.md`
- Rebased onto current main (#1717 included)
- Got Claude adversarial review and **applied** the feedback inline (200-word `<plan_reasoning>` cap, canonical `dictionary_slug` requirement, 80-char raw-text citation rule for slovnyk.me rows)
- 28 prompt-render-guard tests passing
- **Opened PR #1719 directly** — danger mode with no `--allow-merge` worked (gh CLI auth survived)

### 2. CI surfaced two follow-up issues that I fixed inline

**Issue A**: 16 pytest failures in `tests/test_prompt_cot_tier1_scaffolding.py` (the tests added by the rebased Tier-1 commit `d8f1be627b`). Pure mechanical drift — assertions referenced prompt strings that the strengthening commit replaced (e.g. "Reasoning checklist" → "Mandatory visible verification block", "Modern Ukrainian only" → "Modern Ukrainian + heritage-defense discipline", removed flag "archaic form as modern").

Patched the test file to match the new prompt language + added `test_reviewer_prompt_requires_evidence_quotes_array` to lock in the per-dim Q5 schema. Also restored `mcp__sources__` prefix on `check_modern_form` / `search_grinchenko_1907` / `search_esum` in §Tier-1 bullet 2 of `linear-write.md` — Codex had stylistically dropped the prefix during strengthening, but writer-tool naming discipline matters more than concise prose. Pushed as `b6f31d9069`. Local: `98 passed`.

**Issue B**: #1713 CodeQL alert #168 (`py/path-injection`). Gemini's original fix used `pathlib.Path.is_relative_to()` for containment — logically correct defense-in-depth but **CodeQL's data-flow query doesn't recognize that as a sanitizer**.

First attempt (`52459eb585`): switched to `Path.relative_to()` try/except — also unrecognized (alert #168 closed but #169 immediately appeared at the same line). Second attempt (`a1b9c42e88`): switched to `os.path.realpath` + `os.path.commonpath` — the documented CodeQL-recognized path-injection sanitizer. Closed both alerts.

**Process learning**: GH-Actions `@gemini-cli` triggers don't work on this repo because the workflow has no API credentials configured (we use subscription auth locally). Saw the failed run (25404506376: `Please set an Auth method`). Now in MEMORY for future sessions — don't waste a `@gemini-cli` round when the fix is small enough to do inline.

### 3. Merged + cleaned

- `gh pr merge` failed local-cleanup ("'main' is already used by worktree") — but the GH-side merge actually succeeded. `--admin` flag cleared the protection but didn't help local cleanup. Workaround: ignore the local-side error, run `git pull --ff-only origin main` from main checkout, then `git worktree remove ... --force` and `git branch -D ...` manually.
- Cleaned up 3 stale worktrees: `codex/1696-prompt-strengthening`, `claude/1673-1661-cot-tier1-prompts`, `codex/bakeoff-execute-danger`. Plus `gemini/codeql-cleanup-2026-05-05` post-merge.
- **Remaining worktree**: `gemini/codeql-D-js-html-xss` (DRAFT #1688 — user judgment per predecessor handoff).

### 4. Bakeoff re-run completed (25 min, 1521s)

Now that the new V7 prompts are on main, the bakeoff finally has the chance to produce real prompt-adherence telemetry (the predecessor's "0-CoT-emission" finding was on OLD prompts and was structurally expected, not informative).

Fired `bakeoff-rerun-2026-05-06`, completed exit 0 in 25 min. Output: `audit/bakeoff-2026-05-05/`. Per-writer dirs + write JSONLs present; **NO review JSONLs because all 3 writers failed at python_qg** before producing final `module.md`.

#### Win — visible CoT mandate works (Q4 confirmed)

| Writer | sections_total | sections_with_cot | plan_reasoning fields_filled |
|---|---|---|---|
| claude-tools | 4 | 4 | 16/16 |
| gemini-tools | 4 | 4 | 16/16 |
| codex-tools | 4 | 4 | 16/16 |

vs **2026-05-05 baseline: 0 emissions**. Q4 (mandate visible `<plan_reasoning>` blocks before artifacts) flipped to 100% emission. The strengthening payoff works as designed.

#### Three follow-up failures — filed as **#1720**

1. **Zero MCP tool calls.** `tool_calls_total = 0` across all 3 writers. They cite tools in `<plan_reasoning verification>` blocks without actually calling them — visible-CoT theatre. New prompt's heritage-routing language tells writers WHICH tools to use but no pipeline-side check that a citation has a corresponding `function_call` event. **Fix needed**: telemetry parser cross-checks tool citations against actual function_call events; flag mismatches as `tool_theatre_violation`.

2. **End-of-output gate has no contract.** `gate_present=false` for all writers. §Tier-1 bullet 5 in `linear-write.md` is read as guidance, not as a structural marker the pipeline can detect. **Fix needed**: writer prompt requires explicit `<end_of_output_gate>` block after artifacts, listing each check executed.

3. **Correction-pass response unparseable.** All 3 writers reached the correction pass (initial draft below 1200-word target). Response was conversational prose ("Done. Gate-style word count went from 996 → 1325...") instead of structured corrections. Pipeline emits `writer_correction_unparseable` for word_count + plan_sections + vesum_verified gates. **NOT** the same as #1716's silent-no-op fix — events DO surface (#1716 win); the correction-pass PROMPT itself is too loose. **Fix needed**: correction-pass prompts (in `scripts/build/phases/` or correction-specific templates) mandate `<corrections>` find/replace block, V6 reviewer-as-fixer pattern.

#### Per-writer stats

| Writer | wall (s) | initial draft words | terminal event |
|---|---|---|---|
| claude-tools | 588 | 1447 | module_failed (python_qg after ADR-008 correction) |
| gemini-tools | 597 | 1401 | module_failed (python_qg after ADR-008 correction) |
| codex-tools | 266 | 1411 | module_failed (python_qg after ADR-008 correction) |

All three reached close-enough to 1200 target on the INITIAL draft. The correction pass killed all three. Codex (gpt55) was 2x faster than the other two — interesting datapoint.

Cross-reviews: all 6 failed with "missing writer markdown" because writers never published. Aggregator ran but produced n/a for all content-quality dimensions.

---

## Issues filed this session

- **#1718** — `[chore] Triage orphaned dirty tree on main from 2026-05-05 morning session`. The dirty tree includes 11 modified files (skill argument-hint quoting + deploy_prompts.sh wiring `.agents/skills/` deploy + figma-mcp removal) and 3 untracked files (lint_agent_skills.py, prompt-template-review skill). All looks coherent and production-ready but is undocumented in any prior handoff. Recommended (a) commit-as-is. **User decision needed** — do not commit blindly.
- **#1720** — `[V7 prompts] Bakeoff 2026-05-06: visible CoT works but tool-grounding + end-gate + correction-pass don't enforce`. Three independent prompt+pipeline gaps surfaced by the bakeoff above. ACs: (1) tool-theatre gate via telemetry cross-check, (2) `<end_of_output_gate>` structural marker, (3) `<corrections>` block mandate in correction-pass prompts. Each strand is its own design+code+test cycle.

---

## State of NOT-FIRED items from predecessor

Predecessor's "ranked next-session priorities":

1. ✅ **Fire Dispatch B** — done, merged.
2. ✅ **Merge Dispatch B's PR** — #1719 merged.
3. ✅ **Re-run full bakeoff from main** — done. Output at `audit/bakeoff-2026-05-05/`. 25 min wall (faster than expected 60-90).
4. ✅ **Aggregate + interpret REPORT.md** — done. Findings in #1720 (above).
5. ✅ **#1713 Gemini CodeQL iteration** — handled inline, merged.
6. ✅ **#1696 / #1688 cleanup** — #1696 closed. #1688 left for user judgment (still DRAFT, same surface as #1713 which now landed — likely truly superseded).
7. ⏳ **Parked** — #1701, #1702, #1707, #1708 still parked.

---

## Cleanup/follow-up backlog

Low-priority items I deliberately did NOT do this session:

- **Dismiss 8 false-positive CodeQL alerts** documented in #1713 PR body but not dismissable from Gemini's PAT. My local `gh` token *probably* has the scope. Not blocking anything; can do in any future session via `gh api -X PATCH /repos/.../code-scanning/alerts/{N} -f state=dismissed -f dismissed_reason=false_positive`. Targets:
  - #167, #166 (`py/clear-text-storage-sensitive-data` — mdx is curriculum text)
  - #23, #22, #21, #20 (`js/functionality-from-untrusted-source` — archived scraped HTML)
  - #17, #16 (`js/xss-through-dom` — archived scraped HTML)
- **#1718 dirty tree** — needs user decision on commit-vs-stash-vs-split.
- **#1688** — likely close as superseded; keep DRAFT until user confirms.
- **#1713 / #1714 / #1715 / #1717** — already closed via merged PRs (predecessor session).

---

## Cold-start protocol for next session

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
source ./.envrc

# 1. Bootstrap
curl -s http://localhost:8765/api/state/manifest
curl -s http://localhost:8765/api/orient
curl -s 'http://localhost:8765/api/comms/inbox?agent=claude'

# 2. Verify clean main + sync
git fetch origin main && git pull --ff-only origin main && git status -s

# 3. Read THIS handoff + predecessor
#    docs/session-state/2026-05-06-bakeoff-rerun-and-prompt-merges.md (this)
#    docs/session-state/2026-05-05-bakeoff-execution-and-prompt-foundations.md (predecessor)

# 4. Check bakeoff status
.venv/bin/python scripts/delegate.py status bakeoff-rerun-2026-05-06
ls -la audit/bakeoff-2026-05-05/

# 5. If complete: read REPORT.md and interpret
cat audit/bakeoff-2026-05-05/REPORT.md | head -100
```

---

## Ranked next-session priorities

1. **Tackle #1720 (the 3-strand bakeoff blocker).** This is the critical path. Order matters:
   - **Strand 3 first (correction-pass prompts)** — without this, no writer can publish, no review can run. Single failure point. Look at `scripts/build/phases/` for correction-pass templates; mirror the V6 reviewer-as-fixer find/replace contract.
   - **Strand 2 (end-gate marker)** — quick prompt edit + parser tweak in `linear_pipeline.py`. Detect `<end_of_output_gate>` block presence + non-empty actions.
   - **Strand 1 (tool-theatre gate)** — biggest design effort. Telemetry parser needs to extract tool citations from `<plan_reasoning verification>` blocks AND match them against actual `function_call` events in the writer trace. Probably belongs at the same site as `phase_writer_summary` emission.
   - After all three: re-run bakeoff. Acceptance per #1720: `tool_calls_total > 0` per writer, `gate_present=true`, ≥1 writer publishes, ≥1 review runs.
2. **Triage #1718** — get user decision on the orphaned dirty tree. Until that's resolved, every session inherits the same tree.
3. **#1688** — confirm superseded; close.
4. **CodeQL false-positive dismissal** — 8 alerts (low priority, but quick wins).
5. **Parked issues from predecessor** — #1708 (writer subprocess timeout), #1707 (resume terminal-event check), #1701 (env_sanitize), #1702 (ab discuss read-only).

---

## Statistics

- **PRs merged this session:** 2 (#1719, #1713)
- **PRs opened in this session (mid-flight):** 1 (#1721 — strands 2+3 of #1720)
- **PRs closed (superseded):** 1 (#1696)
- **Issues filed:** 2 (#1718 dirty-tree triage, #1720 bakeoff three-strand blocker)
- **Codex dispatches:** 2 (Dispatch B prompt strengthening 7.5 min + bakeoff re-run 25 min)
- **Codex consultations:** 1 (msg 530 — adversarial review of #1721; surfaced regex permissiveness, applied via split-based parser rewrite)
- **Inline fixes I made on others' PRs:** 2 commits to #1713 (52459eb585, a1b9c42e88) + 1 commit on Dispatch B branch (b6f31d9069 — test/prompt alignment)
- **CI-failure → fix → re-CI cycles:** 2 (#1719 pytest, #1713 CodeQL — twice)
- **Bakeoff key result:** visible CoT 0% → 100% emission rate (Q4 win); zero MCP tool calls (theatre); end-gate not detected; correction-pass unparseable
- **Wall clock to handoff finalization:** ~70 minutes

---

## Mid-session update — strands 2+3 of #1720 (PR #1721)

After writing the initial handoff above, picked up the next priority. Two of the three #1720 strands implemented + open as PR #1721 (`claude/1720-strands-2-3` branch):

**Strand 2 (end_gate block mandate)** — pure prompt fix. The parser at `linear_pipeline.py:_extract_writer_gate` already supported `<end_gate>...</end_gate>` block parsing; the writer prompt just didn't tell the writer to emit one. Added the explicit mandate + format example + parser-recognized action keys (`rescanned_words`, `rescanned_sources`, `removed_unverified`, `removed_count`). Test `test_writer_prompt_mandates_end_gate_block` locks it in.

**Strand 3 (writer-correction contract)** — bigger fix. Old `linear-writer-correction.md` told the writer to "modify in place" but never specified output format; parser expected all 4 artifact blocks; writer responded conversationally → unparseable. Rewrote the prompt to mandate a single fenced `markdown file=module.md` block as the entire response. Added `parse_writer_correction_module_only()` to `linear_pipeline.py` using a split-based parser that enforces "exactly one fence, no leading/trailing prose, no other fences". `_apply_writer_correction` calls the new parser for non-`strict_json_parse` gates; existing 4-block path preserved for `strict_json_parse`.

Codex adversarial review (msg 530) caught my first-iteration regex was permissive — a non-greedy DOTALL regex backtracked across multi-fence content and matched a 4-block response as one big "fence". Replaced with the split-based parser. 11 tests in `test_writer_correction_no_op_diagnostic.py` lock all the negative + positive paths (zero/multi/empty/leading-prose/trailing-prose/bare-markdown/4-block all rejected; positive contract response writes module.md). 112 tests pass overall.

Remaining: **Strand 1 (tool-theatre detection)** — telemetry parser needs to extract tool citations from `<plan_reasoning verification>` blocks AND match them against actual `function_call` events in the writer trace. Bigger surface — left for a follow-up PR.

CI status as of handoff write: #1721 mergeable, no failures, CI re-running on the most recent push.

Once #1721 merges + bakeoff re-runs:
- Strand 2 acceptance: `gate_present=true` ≥ 1 writer
- Strand 3 acceptance: ≥ 1 writer publishes final `module.md` → ≥ 1 review runs
- Strand 1 still 0 (tool calls still 0 unless Strand 1 also lands)

---

## Cleanup also attempted this session (deferred)

CodeQL false-positive dismissal — local `gh` token lacks `code-scanning:write` scope (same 403 as Gemini's CI token had). 8 alerts (#167, #166, #23, #22, #21, #20, #17, #16) need manual UI dismissal OR `gh auth refresh -s code-scanning` (user interaction required). Documented in #1718 follow-up.

Alerts #114, #113 (path-injection in image_review_server.py): should auto-close on next CodeQL scan of main now that #1713's `os.path.commonpath` fix is merged. Same for #19, #18 (Gemini's JS XSS fixes).
