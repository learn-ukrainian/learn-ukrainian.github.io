---
date: 2026-05-28
session: "Continuation of Pt 12 (V7.1 m20 pilot returned terminal PASS + tone REJECT 3.0). Surfaced multi-agent direction discussion on channel `v7.1-empirical-direction-2026-05-28` grounded in 3 m20 artifacts (V7+codex baseline 9.5/10; V7.1+claude 3.0 tone; V7.1+codex pipeline-incomplete). Outcome: 2× VOTE D (codex+cursor) + 1× VOTE C (gemini, with hallucinated evidence). User preferred V7.1-claude reads-as-whole (B2 reader, didn't notice the 3 UK-connector slips). Cursor's reply was lost by the bridge JSONL parser; recovered from cursor session transcript on disk. Bridge fix dispatched to codex (PR pending)."
status: direction-converged-on-D-with-cursor-sharpening-bridge-fix-in-flight
main_sha_upstream: bc24fb31bd
main_sha_local: 20ab69072d (unchanged per user direction)
main_green: yes
working_tree_dirty: see "Untracked artifacts" below
session_close: 2026-05-28 ~12:00 local
---

# 2026-05-28 — Part 13: Direction discussion 2D + 1C, bridge fix in flight

**Read the TL;DR. Read the convergence + dissent. Then the recommended path.**

## TL;DR

After Pt 12's V7.1 m20 pilot returned terminal PASS but tone REJECT 3.0 with multiple pipeline regressions, fired a 3-agent direction discussion grounded in three concrete m20 artifacts. Result:

- **Codex → [VOTE: D]** twice (rounds 1+2): ship Pt 10 baseline as the anchor; redesign V7.1 off the critical path. Strategic signal: codex's own tool-call count crashed 20→4 under V7.1 — the architectural risk, not the tone score.
- **Cursor → [VOTE: D]** with sharpening: agree with codex on direction, but **sequence the fix** as Regression-1+2-only first (silent exit + translate schema), THEN re-fire V7.1+codex apples-to-apples, THEN decide charter fate. Cursor independently caught gemini's hallucinated evidence quotes.
- **Gemini → [VOTE: C]**: partial revert — revert PR #2377 (charter), keep PR #2379 (gates). Strong design critique of the "Renderer" framing as "turning a peer-tutor into a confused prompter," but cited specific lines (`Контролюй чистоту словника`, `Крок 5: Розширення`) that do NOT exist in `/tmp/v71-claude-module.md` (independently verified by cursor + grep). Core argument may be right; evidence is unreliable.

**Plus a fourth signal: the user's own gut.** Reading the three artifacts, user said V7.1-claude is "a whole, maybe needs improvements" and noted *"i am also b2ish, i didn't even notice"* — meaning the 3 UK-connector slips that drove tone REJECT 3.0 are invisible to a B2-and-up reader. The reviewer rubric may be over-penalizing on absolute "any UK-in-EN slip = REJECT" when the proportional impact on the actual A1 learner is small.

**Final convergent path (3 colleagues + user signal)**:

1. **Ship Pt 10 (V7-hardened + codex-tools, 9.5/10)** as the m20 anchor — IT IS THE PROVEN ARTIFACT.
2. **One small PR** fixing only Regressions 1 + 2 (silent exit + translate schema). Cursor's sequencing — NO charter changes bundled.
3. **Re-fire V7.1 + codex-tools** with #1+#2 fixed. Empirical: does codex's tool-call count recover (4 → ~20)? Does the build complete through llm_qg?
4. **Then decide on charter** (PR #2377):
   - If V7.1+codex re-fire scores 9+ → keep charter, surgically sharpen `#R-AUDIENCE-LANGUAGE-A1` + adjust tone reviewer rubric to be proportional (the user's B2 insight)
   - If V7.1+codex re-fire still degraded → revert charter (Option C), keep gates from PR #2379

Don't revert the charter before measuring it fairly. Don't fix the reviewer rubric before measuring writer behavior. Each step is a single variable.

## What landed on origin/main during this session

Nothing this session. Origin/main is still at `bc24fb31bd` (post #2379 V7.1 Day 2). Local main checkout stays at `20ab69072d` per user direction.

## In-flight work at session close

- **Codex dispatch `bridge-cursor-jsonl-parser-fix-2026-05-28`** — fired ~12:00 local, ETA 30-60 min. Background task ID `blshvaydi`. Brief: `docs/dispatch-briefs/2026-05-28-bridge-cursor-jsonl-parser-fix-codex.md`. Expected output: PR fixing `CursorAdapter.parse_response` to recognize cursor-agent v2026.05.27's `{role: assistant, message: {content: [...]}}` event shape, plus session-log fallback so future parser misses still recover the response from `~/.cursor/projects/.../agent-transcripts/<session_id>/`. Worktree: `.worktrees/dispatch/codex/bridge-cursor-jsonl-parser-fix-2026-05-28/`.

## The three artifacts (kept for future reference)

All three saved to `/tmp/` for direct human comparison. Open in TextEdit (or any markdown viewer). They will disappear on next reboot — promote to `audit/2026-05-28-v7.1-direction-discussion/` if you want them permanent.

| File | Lines | Bytes | Writer | Pipeline | Score |
|---|---|---|---|---|---|
| `/tmp/pt10-baseline-module.md` | 152 | 10100 | codex-tools (gpt-5.5) | V7-hardened (pre-V7.1) | 9.5/10 llm_qg PASS; word_count 1058<1104 |
| `/tmp/v71-claude-module.md` | 143 | 13200 | claude-tools (Opus 4.7) | V7.1 (Day 1 + Day 2) | terminal PASS + tone REJECT 3.0 |
| `/tmp/v71-codex-module.md` | 113 | 9800 | codex-tools (gpt-5.5) | V7.1 (Day 1 + Day 2) | incomplete (pipeline exit after python_qg) |

Forensic build branches with full artifact trails (never deleted per #M-10):

- `build/a1/my-morning-20260527-185032` — Pt 10 baseline. **Receipts**: `batch_state/api_usage/usage_codex-dispatch_2026-05-27.jsonl` (codex/gpt-5.5/282.85s+60.37s), `writer_tool_calls.json` (20 calls / 8 distinct tools).
- `build/a1/my-morning-20260528-014807` — V7.1+claude pilot (Pt 12). Full pipeline output through llm_qg incl. `llm_qg.json` showing dimension breakdown.
- `build/a1/my-morning-20260528-060820` — V7.1+codex pilot. Stopped after python_qg.

## The multi-agent discussion in full

Channel: `v7.1-empirical-direction-2026-05-28` (in `.mcp/servers/message-broker/messages.db`).

Question doc: `audit/2026-05-28-v7.1-direction-discussion/question.md` (commit when ready, currently untracked).

Channel messages stored:

| Agent | Round | Stored chars | Real content |
|---|---|---|---|
| user | r0 | 7725 | The question (V7.1 vs V7-hardened, with 3 artifacts + 5 options) |
| codex | r1 | 2632 | Full reply, [VOTE: D] |
| gemini | r1 | 3384 | Full reply, [VOTE: C] |
| cursor | r1 | 510 | `[failed: ...]` — bridge parse error, real reply on disk |
| codex | r2 | (in log) | "I keep my vote: [VOTE: D]" |
| gemini | r2 | (no data) | not captured this run |
| cursor | r2 | 510 | `[failed: ...]` — same bridge bug |

**Cursor's actual replies recovered from**: `~/.cursor/projects/Users-krisztiankoos-projects-learn-ukrainian/agent-transcripts/656c0b63-d5b4-4bdf-89cf-e936d00e6b09/656c0b63-d5b4-4bdf-89cf-e936d00e6b09.jsonl` (11 lines, mix of assistant text blocks + tool_use blocks). The substantive r1 reply is at line 8 (text-block), r2 final reply is at line 11.

## Key insights from the discussion

### Codex r1 — strategic framing

> "If forced into B/C later, I would attack silent exit first operationally, because without terminal telemetry every retry is suspect. ... Strategically, though, the root quality regression is Codex utilization 20 → 4; schema drift and A1 tone are local prompt bugs, while the tool-call collapse means V7.1 is no longer the same controlled writer experiment."

Sharp blind-spot calls codex flagged (file as follow-ups):

- The V7.1 completeness gate may be too shallow — "a lesson can mention required words in a list and still not teach them." Mention ≠ teach.
- The writer prompt only documents `translate` schema strictness for `error-correction` (line 6543 of linear_pipeline.py), not other activity types — this is why Regression 2 (`source`/`target` field drift) wasn't caught at prompt-write time.
- `learner_state._load_vocab` returns an empty built vocab list silently without falling back to plan vocab when the file exists but has the new shape — may weaken allowlist coverage without firing any diagnostic.

### Gemini r1 — strong design critique, weak evidence

Core thesis is sharp and worth keeping:

> "The 'Renderer Charter' has turned a peer-tutor into a confused prompter. It treats the 'Wiki Teaching Brief' as a document to be summarized rather than a knowledge source to be synthesized for a learner. ... The wiki_completeness_gate and the Wiki Teaching Brief itself have a structural blind spot: they do not distinguish between content-to-teach and meta-instructions-for-the-writer."

But the specific quotes gemini cites (`Контролюй чистоту словника`, `Крок 5: Розширення`) are NOT in `/tmp/v71-claude-module.md`. Independently verified by:
- My grep: zero matches
- Cursor's grep (in r2): zero matches

Take gemini's framing-level insight (the renderer-charter dissolved the distinction between teacher-only meta and learner-facing prose). Distrust their evidence-citing claims this turn. Treat as a useful design-pattern observation, not as forensic data.

### Cursor r2 — sharpest synthesis

The full text is at line 11 of the session transcript. Key passages:

> "Codex calls 20→4 tool calls the 'strategic root cause.' I agree it is the main V7.1 architecture risk, but it is not yet the decision root tonight: v71-codex never completed the pipeline. ... Silent exit + translate schema remain the gating defects; utilization is a hypothesis to test on the next codex pilot, not grounds to revert charter before that pilot runs."

> "**[VOTE: D]** — align with Codex on the directional call. ... Implementation detail (still my round-1 E, now explicit under D): one small PR fixing only silent exit (1) and `translate` `source`/`target` (2) so the next experiment is V7.1 gates + codex-tools with apples-to-apples telemetry. **Do not** bundle charter surgery into that PR."

> "After a clean codex re-pilot: if tone/tools recover → keep charter and sharpen `#R-AUDIENCE-LANGUAGE-A1`; if not → C (revert #2377, keep #2379)."

Cursor's contribution is the **sequencing discipline**: don't bundle the charter decision into the pipeline-fix PR. Measure first; decide second. This is what landed as the recommended path.

### User signal — B2 reader didn't notice the tone REJECT

User read all 3 artifacts and said V7.1-claude reads as a coherent whole. The 3 UK-connector slips (`або -сь після голосних`, `наприклад`, `поява вставного «л»`) that drove the LLM reviewer to score tone 3.0 are invisible to a B2+ reader because UK connectors process transparently at that level.

The actual A1 target reader is somebody who's already opted into learning Ukrainian — they'd hit `наприклад` as friction once and recognize it as "for example" from context. The reviewer's harsh 3.0 score is structural-rule strictness, not proportional-harm assessment.

**Therefore the recommended path's Step 4** explicitly includes "adjust the tone reviewer rubric to be proportional" (count distinct violations per 100 lines of EN prose, REJECT only when ≥3, REVISE 7-8 below that). User's insight surfaced what would otherwise be a hidden reviewer rubric bug.

## Cold-start sequence for next session

1. **Read this brief end-to-end** + the V7.1 ADR (`docs/decisions/pending/2026-05-27-v7.1-wiki-driven-writer.md` on origin/main).
2. **Check codex bridge-fix dispatch status**: `curl -s http://localhost:8765/api/orient | jq '.delegate'`. If task `bridge-cursor-jsonl-parser-fix-2026-05-28` is `done`, find its PR via `gh pr list --state open --search "head:codex/bridge-cursor-jsonl-parser-fix-2026-05-28"`. Review + merge if clean.
3. **Read cursor's full r2 reply** at `~/.cursor/projects/Users-krisztiankoos-projects-learn-ukrainian/agent-transcripts/656c0b63-d5b4-4bdf-89cf-e936d00e6b09/656c0b63-d5b4-4bdf-89cf-e936d00e6b09.jsonl` line 11 — the synthesized recommendation lives there.
4. **Decide the Step-1 action**: ship Pt 10 baseline as m20 anchor. This involves running `scripts/sync/promote_module.py --latest --level a1 --slug my-morning` against the Pt 10 build worktree at `.worktrees/builds/a1-my-morning-20260527-185032/`. Verify Path B's word_count tolerance fix (PR #2372, on origin/main) applies to this build — currently 1058 words vs 1104 minimum, but tolerance is 8% so 1058 > 0.92 × 1200 = 1104 by exactly 0 words... actually 1104. May need a fresh build pass to refresh the gate state under the merged ceiling.
5. **Fire the Step-2 PR**: small fix for Regression 1 (silent exit) + Regression 2 (translate schema) only. Cursor said: do NOT bundle charter changes. Dispatch shape: codex, similar to the bridge-fix dispatch. Brief lives at `docs/dispatch-briefs/...` (write fresh in next session).
6. **Step 3** (after Step 2 PR merges): re-fire `v7_build.py a1 my-morning --writer codex-tools --worktree` to get the apples-to-apples V7.1 + codex measurement. Compare against Pt 10's 9.5/10 + 20 tool calls + dimension scores.

## Issues open at session close

- **#2378** — V7.1 follow-up: aggressive trim of `linear-write.md` to drop ceiling back below 130KB. Filed earlier this session. Tech-debt label. Don't address before Steps 1-3 land.
- **#2380** — V7.1 build pipeline regressions surfaced by m20 pilot (silent exit, schema drift, tone, codex utilization). 2026-05-28 correction comment appended fixing the "Pt 10 was claude-tools" misattribution. Add a comment when bridge-fix PR lands to mark Regression 5 (bridge cursor JSONL parser).
- Pending issue (file in next session): "bridge `ab discuss` truncates failed cursor responses + doesn't surface session-transcript fallback" — overlaps with the bridge-fix dispatch but worth tracking the workflow surface separately.

## Worktrees on disk at handoff

```
/Users/krisztiankoos/projects/learn-ukrainian                                                          main (local at 20ab69072d, reference)
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/builds/a1-my-morning-20260527-163310          Pt 9 forensic (keep)
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/builds/a1-my-morning-20260527-185032          ⭐ Pt 10 baseline 9.5/10 (keep — the ship candidate)
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/claude/v7.1-day3-codex-pilot-2026-05-28    V7.1+codex pilot trigger (can remove — codex PR for the build's nested branch landed)
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/claude/v7.1-day3-m20-pilot-2026-05-28      V7.1+claude pilot trigger (can remove — preview server attempt didn't pan out)
```

Build branches in the local git database for forensic continuity:

```
build/a1/my-morning-20260527-163310    Pt 9 clean writer (V7-hardened)
build/a1/my-morning-20260527-185032    ⭐ Pt 10 baseline (V7-hardened + codex 9.5/10) — KEEP
build/a1/my-morning-20260528-014807    V7.1 + claude pilot (failed)
build/a1/my-morning-20260528-060820    V7.1 + codex pilot (incomplete)
```

## Untracked artifacts at session close

These accumulate; clean up before/after next session's PRs land:

```
audit/2026-05-27-codex-brain-pick-m20/             (carried from Pt 11 — already in main via PR #2374; safe to remove locally)
audit/2026-05-27-wiki-driven-pivot-discussion/     (carried from Pt 11 — already in main)
audit/2026-05-28-v7.1-direction-discussion/question.md   (THIS session's discussion question — commit if you want it permanent)
docs/decisions/pending/2026-05-27-v8-wiki-driven-writer.md   (superseded predecessor — already in main via PR #2374)
docs/dispatch-briefs/2026-05-27-{7 files}.md       (carried — already in main)
docs/dispatch-briefs/2026-05-28-bridge-cursor-jsonl-parser-fix-codex.md   (THIS session)
docs/session-state/2026-05-27-pt9-...md            (carried — already in main)
docs/session-state/2026-05-27-pt10-...md           (carried — already in main)
docs/session-state/2026-05-27-pt11-...md           (carried — already in main)
docs/session-state/2026-05-28-pt12-...md           (added in Pt 12, never committed; has the 2026-05-28 morning correction inline)
docs/session-state/2026-05-28-pt13-...md           (this file)
```

When you sync local main forward (if you decide to), most of these disappear since they're already on origin/main.

## Cap status

V7.1 ADR cap: 3 refires under V7.1 before ship-or-escalate. **Refire 1 used = V7.1+claude (Pt 12). Refire 2 used = V7.1+codex (this session, pipeline-incomplete).** 1 refire remaining before escalation, which is enough for the Step-3 "apples-to-apples with Regressions 1+2 fixed" measurement.

## One-paragraph fresh-session context dump

If next session is a brand-new orchestrator: V7.1 pilot fired tonight scored tone REJECT 3.0 (vs Pt 10 baseline 9.5/10 from V7-hardened+codex), four pipeline regressions surfaced (#2380), 3-agent direction discussion converged 2× VOTE D + 1× VOTE C, user's B2 read found V7.1-claude pedagogically coherent despite reviewer rubric being harsh, cursor's reply was lost by bridge JSONL parser bug but recovered from cursor session transcript, bridge fix dispatched to codex (PR pending), recommended path is ship Pt 10 + tiny pipeline-fix PR + re-fire V7.1+codex apples-to-apples + only then decide charter fate. Cap: 1 V7.1 refire remaining.

End of 2026-05-28 Pt 13. ~3.5h continuation of Pt 12 + autonomous loop. Hand off cleanly.
