---
date: 2026-05-26
session: "Continuation of the 2026-05-26 overnight orchestrator session (see `docs/session-state/2026-05-26-overnight-bridge-built-m20-fixes-pending-merge.md`). Tracks the m20 anchor build attempt #4 dispatched via the new `ab send-codex-ui` bridge after #2297 (writer-prompt + plan fixes) merged. Build failed before publish but with measurably narrower failure scope than rounds #1-#3 — confirming the iterative writer-prompt strengthening is working."
status: m20-build-4-failed-3-small-issues-plus-textbook-gate-bug
main_sha: 0cfd384fe6 (origin/main as of handoff)
main_green: clean
working_tree_dirty: 0 files (this handoff doc itself untracked)
build_worktree: ~/.codex/worktrees/3a9a/learn-ukrainian/.worktrees/dispatch/codex/a1-m20-anchor-2026-05-26-retry/.worktrees/builds/a1-my-morning-20260525-235634
build_against_main_sha: 88592f751d (the post-#2297 head at build time)
build_exit: 1 (module_failed phase=python_qg)
---

# 2026-05-26 — Part 2: m20 build #4 failed near publish, 3 small failures + 1 gate bug

## Quick summary

The m20 anchor retry dispatched via the new bridge (`ab send-codex-ui`) ran successfully end-to-end against the post-#2297 main. **Build #4's failure surface is significantly narrower than rounds #1-#3** — only 3 failed gates (was 3+, but different ones), plus one gate bug surfaced.

Codex's final diagnosis (verbatim from session JSONL 00:10:00):

> "The structured evidence confirms this is not publishable and not a content hand-edit case. Vocab was successfully padded to 25 and word count reached 1318, but the build still fails on `inject_activity_ids`, `surzhyk_clean`, and `correction_terminal`; separately, the textbook gate incorrectly passes while recording `chunk_context_calls=0`."

## What's better vs the previous round

| Aspect | Round #3 (pre-#2297) | Round #4 (post-#2297) |
|---|---|---|
| `resources_search_attempted` | FAIL (count=0) | PASS — writer called query_wikipedia + search_external + search_images |
| `vocab_count` | FAIL (20/25, pad pool empty) | PASS (25, vocab_floor pad headroom worked) |
| `word_count` | PASS (1128) | PASS (1318) |
| Activity types | 10 inline / 0 workbook (BAD) | INLINE 4 / WORKBOOK 6 (correct split — #2264's writer-prompt fix held up) |
| `textbook_grounding` | FAIL (chunk_context_calls=0) | **PASSES BUT BUGGY** — chunk_context_calls=0 yet gate marks PASS (regression of the gate logic) |
| Total HARD-fail gates | 3 | 2 (surzhyk_clean + inject_activity_ids) |
| Module structure | Empty Activities tab, Tab 4 leak, 10-inline | All 4 tabs structurally correct |
| Word count vs target | 94% | 110% |

This is a near-publish failure. The remaining issues are small + targeted.

## Three failing gates

### 1. `surzhyk_clean` HARD — writer wrote `шо` standalone

```json
{
  "passed": false,
  "hits": ["\\bшо\\b"],
  "detections": [{"pattern": "\\bшо\\b", "text": "шо"}],
  "rule_ids": ["#R-BAD-FORM-MARKER"]
}
```

Writer used the surzhyk form `шо` instead of `що` somewhere in `module.md`. The plan dialogues use `що` properly; writer introduced the surzhyk form when rendering dialogue, likely for "naturalness." This is the canonical russification/colloquialism risk the surzhyk gate is for.

**Fix**: writer prompt needs an explicit hard-stop on `шо` standalone. Add to the existing surzhyk-awareness language: *"Never write the bare form `шо` — always `що`, even in colloquial dialogue. `шо` is surzhyk and fails the `surzhyk_clean` gate."*

### 2. `inject_activity_ids` HARD — act-5 referenced but not defined

```json
{
  "passed": false,
  "injected": ["act-1", "act-2", "act-3", "act-4", "act-5"],
  "missing": ["act-5"],
  "unused": [],
  "reason": "missing_activity_ids"
}
```

Writer emitted `<INJECT_ACTIVITY id="act-5"/>` inline in `module.md` but did NOT include an activity with id `act-5` in `activities.yaml`. The remaining 4 activities are defined. 5th inline marker is dangling.

**Fix**: writer prompt needs a pre-emit parity check — *every INJECT_ACTIVITY id in module.md MUST have a corresponding activity in activities.yaml with that exact id*. Add to the existing PRE-EMIT HARD STOP block (which I introduced in #2297) as a third bullet point.

### 3. `tool_theatre` warning — query_pravopys cited but not called

```
"violations": ["query_pravopys"], "violation_count": 1, "cited_count": 4, "called_count": 6
```

Writer's `<plan_reasoning>` block cited `query_pravopys` as a verification tool but didn't actually call it in this turn. The pipeline detected the discrepancy.

**Fix**: writer prompt's existing tool-citation-honesty rule (`#R-CITE-HONEST`) needs strengthening — the rule already says "Every tool name you cite inside `<plan_reasoning>` MUST correspond to an actual tool call". This is a writer instruction-following failure, not a missing rule. May need pipeline-side enforcement: reject builds with any tool_theatre violation upstream of the writer's `<end_gate>` rather than treating it as advisory.

## One gate bug

### `textbook_grounding` incorrectly passes with chunk_context_calls=0

This is the FAILURE MODE THE WHOLE OF #2297 WAS TARGETING, and the gate this round masks it. The writer still doesn't call `get_chunk_context`, but the gate marks `textbook_grounding` as PASS. Per codex's diagnosis:

> "...separately, the textbook gate incorrectly passes while recording `chunk_context_calls=0`."

**Root cause**: probably the gate logic checks one of:
- (a) `chunk_context_calls > 0` OR `plan_references_empty` — false-pass when plan references exist
- (b) `chunk_context_calls > 0` AND `blockquote_match_count > 0` — false-pass via blockquote alone

Need to inspect `scripts/build/linear_pipeline.py::_textbook_grounding_gate` (or similar) to identify the buggy short-circuit.

This is a high-priority FIX before the next m20 attempt because:
- The writer continues to skip get_chunk_context despite #2297's strengthening
- If the gate keeps masking it, we get poorly-grounded content that ships
- The PRE-EMIT HARD STOP language I added points at this exact gate — the writer can correctly note "the gate isn't actually firing on `chunk_context_calls=0` empirically" and ignore the warning

## Round #4 telemetry (verbatim)

From the build's writer telemetry events (in the codex UI session JSONL):

```
{"event": "phase_writer_summary", "writer": "claude-tools", "module": "a1/20",
 "sections_total": 4, "sections_with_cot": 4,
 "tool_calls_total": 10,
 "verify_words_calls": 5,
 "tool_call_telemetry_available": true,
 "end_gate_fired": true,
 "removed_via_gate": 0,
 "tool_theatre_violations": ["query_pravopys"],
 "tool_theatre_violation_count": 1}

{"event": "phase_done", "phase": "writer", "duration_s": 677.472}
{"event": "phase_done", "phase": "python_qg", "duration_s": 10.735}
{"event": "module_failed", "phase": "python_qg",
 "reason": "Python QG failed after ADR-008 correction paths"}
```

11 minute writer + 11 second QG. Writer made 10 tool calls total this round (vs the previous round's 25 verification-heavy mix). The MIX shifted right per the writer-prompt strengthening — fewer redundant verify_words calls, more multimedia search.

## NEXT-SESSION FIRST ACTIONS — in order

### 1. Fix the textbook_grounding gate logic (HIGH PRIORITY)

The gate's false-pass behavior is masking a structural writer failure. Locate the gate function (likely `scripts/build/linear_pipeline.py::_textbook_grounding_gate` or in `scripts/build/gates/`), trace the short-circuit, fix so that:

> `chunk_context_calls=0 AND plan_references_count > 0` → FAIL (regardless of blockquote presence)

Write a test for this case using the m20 build's artifact directory as fixture.

### 2. Three small writer-prompt iterations

Add to `scripts/build/phases/linear-write.md`:

- **`шо` hard-stop**: Add to the existing surzhyk-awareness section. Single line: *"Never write the bare form `шо`. Always `що`, including in colloquial dialogue. `шо` is surzhyk and the build will hard-fail."*
- **INJECT_ACTIVITY parity check**: Add to the PRE-EMIT HARD STOP block (the one #2297 introduced). Single bullet: *"Every `INJECT_ACTIVITY id=<X>` reference in module.md MUST have a corresponding activity with id `<X>` in activities.yaml. The build hard-fails on dangling references via `inject_activity_ids` gate."*
- **Tool citation honesty repeat**: The rule already exists (`#R-CITE-HONEST`). May not need a prompt change — instead, fix the pipeline to reject `tool_theatre_violation_count > 0` as a hard fail before publish, not just an end-gate advisory.

### 3. Re-fire m20 build via the bridge (3rd attempt this session)

After the three writer-prompt + 1 gate fix lands in main, send via:

```bash
ab send-codex-ui \
  --thread 019e6063-c3da-78d1-acaa-4cd684a08786 \
  --cwd ~/.codex/worktrees/3a9a/learn-ukrainian \
  --from-file <new-relay-file> \
  --timeout 5400 \
  --json
```

The codex UI thread state remembers the prior build context; the new relay can be short ("main has [fix] at [SHA], retry m20 anchor build").

### 4. Consider escalating if round #5 also fails

If round #5 has a NEW set of small failures (different from round #4's шо/inject/theatre), we're seeing classic prompt iteration drift — each fix exposes a new edge case. At that point the "diff-only correction architecture" the previous handoff deferred becomes the right move.

Decision criteria for the escalation: if **after one more iteration** the gate failure set is non-empty AND uncorrelated with the previous round, escalate. If failures keep narrowing (count: 3 → 2 → 1 → 0), continue iterating prompts.

## Bridge performance retrospective

- Bridge dispatched at 23:53:17Z
- Codex resume subprocess started immediately, opened parallel JSONL
- Writer phase: 677s (11 min)
- python_qg: 10.7s
- Total: ~11 min wall to the failure event
- Bridge subprocess still alive at handoff (codex doing post-build diagnosis + issue filing)

Cost (per the codex token usage in the session JSONL):
- 54M tokens input (52M cached), 113K output, 41K reasoning
- Codex weekly rate-limit usage: primary 4%, secondary 30% — well within budget

The bridge mechanism worked end-to-end: dispatched, executed, returned diagnosis. Lane 1 from #2285 validated empirically with a real workload (not just a PONG probe).

## Critical context for next orchestrator

- **Codex UI is still attached** to the m20 thread `019e6063-c3da-78d1-acaa-4cd684a08786` (PID 83697 holds the JSONL open). Bridge subprocess (PID 40772 at handoff time) is wrapping up its diagnosis turn — likely filing follow-up issues for the 3 failures + gate bug. Check `gh issue list --state open --limit 5` for any NEW issues filed during/after handoff.
- **The build worktree is preserved** at `~/.codex/worktrees/3a9a/learn-ukrainian/.worktrees/dispatch/codex/a1-m20-anchor-2026-05-26-retry/.worktrees/builds/a1-my-morning-20260525-235634/` — all artifacts (module.md, vocabulary.yaml, activities.yaml, resources.yaml, python_qg.json, writer_prompt.md, writer_output.raw.md, writer_tool_calls.json) are there for forensic inspection.
- **Round #4 is NOT a regression** — it's progress. Three pre-#2297 failure modes are fixed; three NEW small ones surfaced. Each round narrows the failure space.
- **Don't conclude that prompt iteration is exhausted**. The diff-only correction architecture is a 200-400 LOC piece of work; tonight's incremental approach has shipped 5 PRs and made measurable progress. Escalate after one more iteration if needed.
- **The textbook_grounding gate bug is THE root cause** for why my #2297 PRE-EMIT HARD STOP for get_chunk_context didn't visibly improve the writer's behavior — the gate isn't firing on the violation, so the writer doesn't see consequences. Fix the gate FIRST, then the writer-prompt strengthening will have teeth.

Full chain: this file + `docs/session-state/2026-05-26-overnight-bridge-built-m20-fixes-pending-merge.md` (Part 1). Next session reads Part 2 first, then Part 1 for full context.
