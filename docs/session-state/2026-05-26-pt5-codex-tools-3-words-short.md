---
date: 2026-05-26
session: "Part 5 of the 2026-05-26 multi-session day. Continuation of Pt 4 (codex-tools writer empirical win). Shipped PR #2344 (dialogue ≥15 + meta-narration ban) and fired m20 round #10. Result: codex-tools cleared 27 of 28 hard gates including the 2 new content gates that failed round #9. Only `word_count` failed — by THREE TOKENS (1101 vs 1104 floor). Near-miss, single-fix away from shipping m20."
status: m20-publishable-after-one-more-overshoot-bump-or-pivot-to-gemini
main_sha: a4219dcd12 (origin/main at handoff; round #10 build ran against a2ae631314 which is included)
main_green: clean
working_tree_dirty: 0 files (this handoff doc untracked until PR)
---

# 2026-05-26 — Part 5: codex-tools 27/28 gates, m20 3 tokens short

Read this Pt 5 first. Continuation of Pt 4 (`2026-05-26-pt4-codex-tools-writer-empirical-win.md`). Pt 4 captured rounds #4-#9; this Pt 5 captures round #10 + the next-action.

## TL;DR for the next orchestrator

1. **8 PRs landed across this multi-part session day.** Main went `894723f0f4` (Pt 3 close) → `a4219dcd12` (now). Latest Pt 4+Pt 5 PRs: #2305, #2306, #2307, #2308, #2339, #2340, #2341 (Pt 4 handoff), #2344.
2. **Round #10 m20 result: 27 of 28 hard gates ✅, `word_count` failed by 3 tokens** (1101 vs 1104 min). Writer telemetry shows codex doing everything right (`chunk_context_calls=2`, `tool_theatre=0`, dialogue lines jumped 13→33, engagement passed). This is the closest m20 has gotten to publishable in 10 rounds.
3. **Next action is tiny**: nudge the writer-prompt overshoot guidance from "10-15%" to "20%" OR investigate the actual `_word_count` vs writer's `wc -w` count gap. Either yields round #11 success.
4. **OR**: per user-stated sequence, pivot to gemini-3.1-pro for round #11 to compare A1 writer quality across writer pools before deciding the final A1 default.

## Round #10 forensic detail

Bridge subprocess `bridge-75872340` (subprocess `b6hzipsiv`), 446 seconds wall-clock, against main `a2ae631314` (after PR #2344 merged).

**Final event:**

```json
{"event":"module_failed","level":"a1","slug":"my-morning","phase":"python_qg","reason":"Python QG failed after ADR-008 correction paths"}
```

**Gate-by-gate (27/28):**

```
activity_schema=True          word_count=False (1101/1200, min 1104 — SHORT BY 3)
plan_sections=True            textbook_grounding=True
formatting_standards=True     resources_search_attempted=True
vesum_verified=True           immersion_advisory=True
citations_resolve=True        l2_exposure_floor=True (UK dialogue lines: 33)
plan_reference_match=True     long_uk_ceiling=True
component_density=True        inject_activity_ids=True
activity_types=True           ai_slop_clean=True
russianisms_strict=True       register_consistency=True
engagement_floor=True         component_props=True
russianisms_clean=True        surzhyk_clean=True
calques_clean=True            paronym_clean=True
previously_passed_regression=True   vocab_count=True
                              correction_terminal=False (word_count's single ADR-008 attempt failed)
```

**Writer telemetry:**

```
chunk_context_calls=2
search_text_calls=0
tool_theatre_violation_count=0
word_count=1101
l2_exposure_floor.uk_dialogue_lines=33
phase_writer_summary.tool_calls_total=16
raw writer_tool_calls.json records=27
```

**Build worktree (preserved per MEMORY #M-10):**

```
/Users/krisztiankoos/.codex/worktrees/3a9a/learn-ukrainian/.worktrees/builds/a1-my-morning-20260526-193657
```

## What caused the 3-token miss

Round #9 hit word_count=1126 (passed). Round #10 hit 1101 (failed by 3 tokens). Same writer, same model, same prompt + PR #2344's dialogue/meta-narration additions.

The mechanism: PR #2344's "≥15 UK dialogue surfaces" guidance worked SO well that codex emitted **33** dialogue lines (more than double the floor). But the writer redistributed its word budget — more dialogue, less prose. Net: word_count dropped by 25 tokens vs round #9.

This is a known interaction pattern: adding a hard floor on one section can eat the budget of another. The fix isn't to remove the dialogue floor — round #9's 13 lines also failed `l2_exposure_floor`. The fix is to make the overshoot framing on `word_count` more aggressive so the writer has headroom even after redistributing.

## Round-by-round m20 record (full)

| Round | Main SHA | Writer | Outcome | Failed gates | Word count | Dialogue lines |
|---|---|---|---|---|---|---|
| #4 | 88592f751d | claude-tools | failed | inject_activity_ids, surzhyk_clean (шо), textbook_grounding (false-pass), tool_theatre | 1318 | n/a |
| #5 | 3eef657f66 | claude-tools | failed | vocab schema (note vs notes — my typo) | n/a (build halted) | n/a |
| #6 | 3eef657f66 | claude-tools | failed | textbook_grounding (Step B skipped — now correctly enforcing), engagement_floor, tool_theatre | n/a (halted) | n/a |
| #7 | 3eef657f66 | codex-tools | failed | textbook_grounding (gate parser bug) | 1139 (95%) | n/a |
| #8 | 88e2e31f5a | codex-tools | failed | word_count (981/1200, 82%) | 981 | n/a |
| #9 | 8e6c44eea3 | codex-tools | failed | l2_exposure_floor (13/14), engagement_floor (meta phrase) | 1126 ✅ | 13 ❌ |
| #10 | a2ae631314 | codex-tools | failed | word_count (1101/1200, **3 tokens short** of 1104 floor) | 1101 ❌ | 33 ✅ |
| #11 (queued) | post-fix | codex-tools or gemini-tools | expected `module_done` | — | overshoot bumped to 20% | — |

## Next-session opening sequence

Two viable paths. Pick one (the user's stated sequence is "first codex, then gemini, then decide"):

### Path A: ship m20 with codex-tools (tightest scope)

Round #10 missed by **3 tokens out of 1200** (0.25%). One more writer-prompt tweak should close it:

1. **Open a small writer-prompt PR** updating `scripts/build/phases/linear-write.md` lines around the new "Word minimum" guidance (around line 248, added in PR #2340). Change "Overshoot by 10-15%" to "Overshoot by 20% (aim for ~1.2× the minimum)". Rationale: round #10 hit 1126 with a "10-15%" framing but redistributed it to 1101 when the dialogue floor kicked in; 20% gives headroom for that redistribution. Diff: 1 line.
2. **Optional + investigation-worthy**: the `_word_count` gate uses `_WORD_RE` on `_strip_comments(text)`. The 14% gap I noted in Pt 4 between `wc -w` (1140) and the gate count (981 round #8) is worth understanding — most likely `<DialogueBox uk="..." en="...">` JSX attribute words aren't all counted. If so, doubling dialogue lines (round #10) doubled the JSX overhead, eating into countable tokens. Pin via inspection of `_word_count` + JSX handling in `module.md` masking.
3. **Merge** and fire round #11 with `--writer codex-tools` via the bridge.
4. **Expected outcome**: `module_done` + m20 anchor PR.

### Path B: pivot to gemini-3.1-pro per the user's plan

Round #10's near-miss is unambiguous codex-tools success at A1 minus a writer-prompt nudge. The data is sufficient to call codex-tools the working A1 writer. Per the user's stated sequence "first codex, then gemini, then decide":

1. **Fire round #11 with gemini-3.1-pro** (via `--writer gemini-tools`, `agy-tools`, or `cursor-tools` — pick whichever quota pool has headroom). Brief should mirror the round #10 brief but flag the writer change.
2. **Expected outcomes**:
   - `module_done` cleanly: gemini-3.1-pro is the better A1 writer (or tied with codex). Update decision card to flip default to whichever writer pool is cheapest with adequate quality.
   - Fails on word_count or other content gate: data point for comparison; codex-tools' 27/28 score still wins. Ship Path A's tiny fix and use codex.
3. **After both data points**: update `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md` with the empirical comparison + new A1 writer default.

**Recommendation**: Path A first (tightest scope, m20 ships), then Path B for the decision-card revision. Path B alone leaves m20 unship-able if gemini also undershoots.

### Both paths require this prep

Before firing either round #11:

```bash
git fetch origin main
cd ~/.codex/worktrees/3a9a/learn-ukrainian
# Confirm origin/main is at a4219dcd12 OR later (must include PR #2344's a2ae631314)
git rev-parse origin/main
```

The bridge command is the same as rounds #4-#10:

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py send-codex-ui \
  --thread 019e6063-c3da-78d1-acaa-4cd684a08786 \
  --cwd /Users/krisztiankoos/.codex/worktrees/3a9a/learn-ukrainian \
  --from-file /tmp/m20-relay-round11.md \
  --timeout 5400 --json
```

## Critical context for the next orchestrator

1. **Round #10 is the closest m20 has ever been to publishable across 10 rounds.** All 4 prior failure categories (Step B, tool_theatre, schema, register) are fixed. The remaining failure is a 3-token shortfall on a 1200-token target = 0.25%. **Do not let this slip into a multi-round iteration loop** — it should be one tiny PR + one build.
2. **The codex UI thread `019e6063-c3da-78d1-acaa-4cd684a08786` has been used for ALL 7 rounds (#4-#10)** without issue (one GUI restart mid-session, recovered automatically). Session JSONL at `~/.codex/sessions/2026/05/25/rollout-2026-05-25T20-26-51-019e6063-c3da-78d1-acaa-4cd684a08786.jsonl` (~6MB now from accumulated build telemetry). Don't start a new thread; reuse this one.
3. **The 7 build worktrees** at `~/.codex/worktrees/3a9a/learn-ukrainian/.worktrees/builds/a1-my-morning-2026052[5-6]-*` are LOAD-BEARING for forensic analysis (per MEMORY #M-10). Round #10's at `a1-my-morning-20260526-193657`. Do NOT remove until m20 ships.
4. **Pt 4 + Pt 5 handoffs together are the canonical narrative** of this 10-round odyssey. Pt 4 covers rounds #4-#9 + the empirical writer comparison; Pt 5 covers round #10 + next action. Read Pt 4 first if context allows; Pt 5 standalone has the round table + decision matrix.
5. **8 PRs merged across Pt 4 + Pt 5**: #2305 (textbook_grounding Step B), #2306 (writer-prompt deltas), #2307 (surzhyk reclassify), #2308 (typo fix), #2339 (chunk_context parser), #2340 (word_count framing), #2341 (Pt 4 handoff), #2344 (dialogue floor + meta-narration ban). Pt 5 handoff PR pending.

## What's NOT been done that's still on the queue from earlier Pt 3

These remain unaddressed across the multi-session day, deprioritized while m20 was the focus:

- Claude Desktop bridge adapter (PR for `_ui_claude.py` mirroring `_ui_codex.py`)
- Routing pivot remaining: #2278, #2279, #2280, #2281
- `/goal`-in-UI mode for the bridge (codex side and Claude Desktop side)
- Update `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md` with the codex-tools-clears-Step-B finding (regardless of A vs B path above)

Pt 3 handoff `2026-05-26-session-close-pt3-direction-update.md` has the full context for those items.

End of 2026-05-26 Pt 5 handoff.
