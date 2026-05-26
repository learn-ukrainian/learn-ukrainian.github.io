---
date: 2026-05-26
session: "Close-of-session direction update for the 2026-05-26 overnight orchestrator run. Captures user feedback after Pt 2 handoff (#2303) merged: (1) bridge priority reorder — **Claude Desktop next, then Cursor, Antigravity deferred** (too new to justify effort yet); (2) major insight — **both Codex Desktop AND Claude Code Desktop expose `/goal` inside the UI**, so the agent bridge should drive `/goal` runs INTO running UI sessions, not just plain prompts. The bridge becomes a dispatcher for predicate-bounded batch work that benefits from the running UI's warm context + visible operator view."
status: session-closed-direction-updated-for-next-session
main_sha: 894723f0f4 (origin/main at handoff)
main_green: clean
working_tree_dirty: 0 files (just this doc untracked then committed)
---

# 2026-05-26 — Part 3 (session close): direction update for the bridge work

This is the close-of-session pointer for the 2026-05-26 overnight orchestrator run. **Reads as a delta**, not a re-statement — Pt 1 and Pt 2 stand. Next session should read this first, then Pt 2 (active blockers), then Pt 1 (full context).

## What changed at session close

After Pt 2 merged (#2303), the user sent two direction updates that override the "next-steps" sections of both prior handoffs:

### 1. Bridge target priority — reordered

| Old order (Pt 1) | New order (this doc) |
|---|---|
| 1. Codex Desktop (shipped via #2299) | 1. Codex Desktop ✅ (shipped #2299) |
| 2. Cursor | 2. **Claude Code Desktop** (NEXT) |
| 3. Claude Code Desktop | 3. Cursor |
| 4. Antigravity UI | 4. ~~Antigravity UI~~ — **deferred**, "way too new to waste efforts on it" |

Antigravity adapter work that was scoped into the bridge in Pt 1 (per user direction earlier in the session — *"ah and we have to add agy ui or antigravity ui for 2285"*) is now reversed. The `~/.agy/*` allowlist entries added to `scripts/audit/known_user_paths.yaml` in #2298 stay (cost zero), but no Antigravity adapter implementation should ship until the tool is proven stable enough to be worth the surface area.

### 2. `/goal` works inside the running UI sessions — bridge should drive it

Critical insight: **Codex Desktop AND Claude Code Desktop both expose `/goal` as a slash command inside the running session.** That's the predicate-bounded batch driver from `claude_extensions/rules/goal-driven-runs.md` — but available IN the UI, not just in a fresh `claude -p "/goal ..."` headless spawn.

This reframes the bridge:

- **Today's bridge** (`ab send-codex-ui --thread <UUID> "<message>"`): sends a plain prompt; codex processes it as a normal turn; no goal-driver semantics.
- **The bridge we want**: a thin `--goal` mode that wraps the message in a `/goal` invocation INSIDE the running UI, then tails the JSONL for the standard goal-status grammar (`GOAL_STATUS turn=N/M`, `GOAL_DONE reason=...`, `GOAL_ABORT reason=...`, `GOAL_WAIT signal=...`).

Why this matters:

1. **Warm context.** The running UI session has the project state cached; firing `/goal` in-session preserves that. A fresh `claude -p "/goal ..."` reloads cold.
2. **Operator view.** With `/goal` in-session, the human can SEE the goal driver's progress in the UI overlay panel (Claude Code 2.1.139+) without re-attaching to a separate transcript.
3. **Goal-status as the unified ack.** The bridge today returns `final_message` heuristically. With goal mode, the terminal status is structured: `GOAL_DONE` (success), `GOAL_ABORT` (predicate failure), `GOAL_WAIT` (async suspend). The bridge subprocess can exit with a deterministic code based on which terminal status landed.
4. **One mechanism, two transports.** Headless `claude -p "/goal ..."` and bridged-in-UI `/goal` end up using the SAME status-line grammar and the same hook (`claude_extensions/hooks/goal-driver-stop.sh`). Tooling consolidates.

The work decomposes:

- **Bridge codex side** (`scripts/ai_agent_bridge/_ui_codex.py`): add `--goal <predicate>` flag. When set, prefix the message with `/goal ` and adjust the JSONL parsing to look for `GOAL_*` lines in agent_message events. Return code: 0 on `GOAL_DONE`, 2 on `GOAL_ABORT`, 1 on no-terminal-status, separate code on `GOAL_WAIT`.
- **Bridge Claude Desktop side** (new — to be built): `ab send-claude-desktop --session <ID> --goal <predicate> "<msg>"` mirroring the codex shape, but using `claude -p --resume <session-id>` instead of `codex exec resume`. JSONL path: `~/.claude/projects/<encoded-path>/sessions/<UUID>.jsonl` (verify empirically before committing).
- **Shared `_ui_base.py`**: once codex AND claude adapters exist, extract `Bridge-ID` + `find_session_file` + `_extract_final_message` + `_goal_status_parser` into a shared base.

### What about a `/goal` for m20?

Tonight's m20 build #4 dispatch was a single relay message — codex received it and ran the build, but there was no goal-driver predicate. If we re-dispatched as `/goal` with predicate "m20 anchor build passes §4 ten-check + ULP fidelity AND PR is open", the bridge would have a clean terminal signal (`GOAL_DONE` vs `GOAL_ABORT reason="textbook_grounding gate bug"`).

Worth doing for round #5 — after the textbook_grounding gate fix lands, fire the retry as `/goal` not a plain relay.

## Correction to Pt 2 — `шо` is NOT surzhyk, and it's a TEACHING opportunity not a defect

User pushback at session close (twice), verified before pushing this doc:

- Antonenko-Davydovych (the canonical russianism authority) has NO entry for `шо/що`. If it were a russianism his methodology would catch it.
- Russian has `что` (colloquially `[што]`, spelled `что`/`чё`) — NOT `шо`. So `шо` cannot be a calque from Russian.
- `шо` is a native Ukrainian phonetic reduction of `що`, widespread in colloquial speech across all regions, including monolingual Ukrainian-speaking areas.

**Pedagogical reframing** (user direction, second pass):

> "шо is completely fine, it is used everyday, but not literary, it is colloquial, it is good if the learners know that and use it appropriately"

So the diglossia IS the teaching content, not a gate-fail signal. The right learner exposure is:

- **Tab 1 narration / teacher voice / teaching prose**: literary `що`
- **Tab 1 dialogues (especially informal, e.g. roommate / friend / family)**: `шо` is natural and SHOULD appear, ideally with a one-line register note so the learner knows it's colloquial-only
- **Tab 2 vocab**: include `що` with the literary register tag; mention `шо` as a colloquial variant if the module's dialogues use it
- **Tab 3 activities**: respect the register of the prompt's context
- **m20 specifically** is a roommate dialogue (Ліна + Настя on morning routines) — natural place to MODEL the colloquial register, NOT punish it. Build #4's `шо` may have been pedagogically correct in context.

The `surzhyk_clean` gate's `\bшо\b` pattern is a **false positive** of the gate, AND the gate's hard-fail behavior is the wrong shape for this form. Surzhyk is Russian-pattern lexicon/morphology (`конешно` instead of `звичайно`, `сабственно` instead of `власне`, wrong-case constructions like `по дорозі в`) — not native phonetic reductions like `шо`.

**Revised fix** (incorporating the pedagogical reframe):
1. **Remove** `\bшо\b` from `surzhyk_clean` hard-fail patterns. It's never a russianism.
2. **Add a separate `register_consistency` linter** (or extend an existing one) that warns when `шо` appears OUTSIDE a `<DialogueBox>` / blockquote / explicit colloquial-tagged context in A1-B2 modules. Warning, not hard-fail. Lets writers use it intentionally with confidence.
3. **Writer prompt addition** (the only writer-side change): a one-liner under the dialogue-style guidance: *"`шо` is acceptable inside dialogue blocks (`<DialogueBox>` or `>` blockquotes) when the register is colloquial; never in teacher-voice narration. Mention the literary↔colloquial pair in vocab when the module surfaces it."*

This is a **gate fix + small writer-prompt addition + small linter addition**, not a writer-prompt restriction. Net result: the module CAN ship `шо` in dialogue and it's pedagogically richer for it.

## What's still true from Pt 2 (active blockers, revised)

The Pt 2 handoff's ordered action list partially stands. Restating with the corrections + direction updates applied:

1. **Fix textbook_grounding gate bug** — gate PASSES with `chunk_context_calls=0` while writer correctly self-reports the zero. Locate the gate function, fix the short-circuit. Test with the m20 build #4 artifact as fixture.
2. **Fix surzhyk_clean gate false positive on `шо`** — remove the pattern from hard-fail (it's native colloquial, not surzhyk); add a separate `register_consistency` linter that WARNS when `шо` appears outside DialogueBox/blockquote in A1-B2 modules. m20's roommate dialogue SHOULD use `шо` for register authenticity. Pedagogical opportunity, not a defect.
3. **3 small writer-prompt additions**: INJECT_ACTIVITY parity in PRE-EMIT HARD STOP block, tool-citation enforcement upstream of `<end_gate>`, AND a one-line diglossia guidance: `шо` is OK inside dialogue blocks, never in teacher-voice narration; mention the literary↔colloquial pair in vocab when modules surface it.
4. **Re-fire m20 via the bridge** — and **use `--goal` mode** if the bridge has it by then (otherwise plain relay).
5. **Build Claude Desktop bridge adapter** in parallel — mirroring `_ui_codex.py`, targeting `claude -p --resume <session-id>` + `~/.claude/projects/<...>/sessions/*.jsonl`.
6. **Routing pivot remaining** (#2278, #2279, #2280, #2281) — briefs still TBW. Each is small/medium scope, all to gemini-pro or agy (now that codex weekly is fresh again).
7. **`/goal` mode on the bridges** — codex first, then Claude Desktop. Status-line parser is the new shared piece.

## What I did NOT do tonight, but is now clearly out of scope per the direction update

- ❌ **Antigravity bridge adapter** — deferred. Don't write the adapter; don't add the `~/.agy/*` allowlist entries to anywhere new (those entries in `scripts/audit/known_user_paths.yaml` from #2298 are fine to keep — they cost zero and signal "we considered it then deferred").
- ❌ **`agy` references in #2285's body/comments as a "4th target"** — leave the issue body alone (it's history), but next-session edits to #2285 should reflect the 3-target scope (Codex, Claude Desktop, Cursor) and note Antigravity as "deferred until tool maturity warrants it."

## Recommended next-session opening sequence

1. **Read this Pt 3 first** (you are reading it now if you wrote a cold-start handoff loop correctly).
2. **Read Pt 2** at `docs/session-state/2026-05-26-overnight-pt2-m20-build-4-failed-near-publish.md` for the m20 build #4 forensic detail.
3. **Skim Pt 1** at `docs/session-state/2026-05-26-overnight-bridge-built-m20-fixes-pending-merge.md` if you need the bridge-empirics + PR-by-PR history.
4. **Check `gh issue view 2294`** — codex reopened it with the round #4 evidence. Use the diagnostic in your gate-fix work.
5. **Check `gh issue view 2285`** — the agent bridge issue. Comment with the priority reorder (Claude Desktop → Cursor → Antigravity deferred) and the `/goal`-in-UI insight from this Pt 3 BEFORE writing code, so the design record reflects the current direction.
6. **Then execute**: gate fix → writer-prompt strengthens → re-fire m20 → start Claude Desktop bridge adapter in parallel.

## Critical context for the next orchestrator (don't lose these)

- **`/goal` in UI is the unlock.** Both Codex Desktop and Claude Code Desktop run `/goal` natively. The bridge wraps this. Stop thinking of the bridge as a "send message to UI" mechanism — it's a "fire `/goal` into a running UI with deterministic status grammar" mechanism. The plain-message mode (`ab send-codex-ui` without `--goal`) is the FALLBACK, not the default.
- **Antigravity is paused, not killed.** When the tool matures (operator judgment call — not on a fixed timeline), the adapter is straightforward (mirror `_ui_codex.py` with appropriate session path). Don't burn cycles on it now.
- **The textbook_grounding gate bug is the single highest-leverage fix.** Once that gate enforces `chunk_context_calls > 0` when `plan_references_count > 0`, the writer-prompt PRE-EMIT HARD STOP from #2297 will have teeth. Without it, the writer keeps ignoring the obligation because the gate isn't actually firing.
- **m20 build #4 succeeded structurally.** Vocab 25, words 1318, INLINE 4 / WORKBOOK 6, Tab 4 clean — the module's SHAPE is right. Remaining work: 1 writer-prompt parity check (INJECT_ACTIVITY), 1 enforcement strengthening (tool-citation), 1 diglossia guidance (шо in dialogue), **2 gate fixes** (`textbook_grounding` false-pass + `surzhyk_clean` false-positive on шо), and 1 new linter (register_consistency warning). Round #5 should ship.
- **The `шо` lesson** (TWO corrections from user, captured here): I called it surzhyk in Pt 2 based on the gate's classification, not on linguistic evidence. User caught the error. Antonenko-Davydovych has no entry; Russian lacks the form; it's native colloquial. Then user reframed AGAIN: `шо` isn't just "not a defect" — it's a TEACHING TARGET. Learners benefit from knowing the literary↔colloquial pair and when each is appropriate. The pipeline should facilitate teaching the diglossia, not suppress one side of it. Mirrors MEMORY #M-4 (deterministic over hallucination) — verify before classifying Ukrainian forms, especially when the gate's label disagrees with the linguistic record. Don't trust automated classification as evidence of a russianism without an authority check. And: every "gate fail" should pass through "is this actually a pedagogical bug, or is the gate measuring the wrong thing?" before becoming a writer-prompt restriction.

Session totals (final): **7 PRs merged** (#2297, #2298, #2299, #2300, #2301, #2302, #2303 — and this Pt 3 will be #2304 when CI clears). Working tree clean. Main at `894723f0f4`.

End of 2026-05-26 overnight orchestrator session.
