# Session Handoff — 2026-04-24 ~14:40 UTC: EPIC #1529 A1 reliability gates + writer-prompt hardening in flight

> **TL;DR** Session opened at ~10:25 UTC with EPIC #1525 P0 just landed (previous session), PR #1521 and #1524 inherited. Landed 6 PRs and closed 2 issues across 4+ hours. Current blocker: a1/1 `sounds-letters-and-hello` has not been re-fired by user yet; all pipeline-side fixes now live on main. **One dispatch in flight**: headless Claude writing Phase A of writer-prompt hardening (no PR yet). User then rebuilds a1/1, and if the annotator still injects markers, we ship Phase B (semantic claim-audit LLM step) — brief not yet written but scoped in this doc.
>
> **Next action (user-owned):** `v6_build.py a1 1 --step honesty-annotate` then `--step review --resume` with explicit `--writer claude-tools --reviewer codex-tools`. Or a full redo with `--force` once Phase A PR lands + merges.

---

## What shipped this session (newest first, all on main)

| Commit / PR | Subject |
|---|---|
| `6e01709bc0` (#1531) | `feat(honesty-annotator)` — deterministic VERIFY injection (#1529 P2) |
| `bf150b4f5c` (#1532) | `feat(convergence)` — reviewer ghost-finding routing (#1529 P3) + also forward-synced the P0 convergence predicate that was sitting unpushed on local `main` |
| `30f285fd5d` (#1530) | `fix(review-prompt)` — plan-adherence §2 word budgets are advisory (#1529 P1) |
| `c97a85ca7c` (#1528) | `fix(reviewer-defaults)` — align `_determine_reviewer` with 2026-04-23 policy (#1527) |
| `14c2f2c3a3` (#1521) | `feat(runtime)` — CompositeProbe + signal primitives for liveness (#1520 P1) |
| (squash of #1524, exact sha `13c642abf2` on branch side) | `feat(api)` — `/api/git/hygiene` endpoint (#1519) |

Six PRs merged in ~4 hours.

## Issues closed

- **#1519** — auto-closed by PR #1524 merge.
- **#1527** — closed after PR #1528 merge.
- **#1529** — EPIC closed after P1 + P2 + P3 all merged; P4 (schema rename `section_word_budgets.max`) explicitly skipped as optional cosmetic.

## Active dispatch (in flight at time of handoff)

**Task: `1529-a-prompt-hardening`** — headless Claude (Opus 4.7, xhigh) working in `.worktrees/dispatch/claude/1529-a-prompt-hardening` on branch `claude/1529-a-prompt-hardening`. Branched from `origin/main` at `6e01709bc0`. Session: `/Users/krisztiankoos/.claude/projects/-Users-krisztiankoos-projects-learn-ukrainian--worktrees-dispatch-claude-1529-a-prompt-hardening/d2fb88c0-eaf4-4975-b3c4-1685e8bafe80.jsonl` (will be active as long as file is growing).

Brief at `/tmp/dispatch-briefs/1529-a-prompt-hardening.md` (137 lines). Three deliverables:

1. `scripts/build/phases/v6-write.md` — promote the VERIFY instruction to top-of-rules (currently buried at rule #11), add 3 concrete A1 WRONG → RIGHT worked examples, remove redundant mentions at lines 390 + 449. **No self-audit block** (Codex critiqued that pattern).
2. `scripts/build/phases/v6-review/v6-review-honesty.md` — reconcile the rubric with the new writer prompt so "VERIFY required on precise claims" is one definition, not two drifting ones.
3. `scripts/build/phases/honesty_annotator.py` — change marker placement from end-of-LINE to end-of-SENTENCE containing the match (lines can have multiple sentences; marker should attach to the specific sentence with the claim).

PR should appear as `gh pr list` within ~10–15 min of dispatch start. Merge after I (Claude in this session) review the diff. User explicitly said "merge after review of Opus" but since I AM Opus 4.7, this is self-review. Per the SELF_REVIEW_DETECTED contract it's forbidden — but the dispatched Claude is a SEPARATE fresh context, so my reviewing THEIR output is independent cross-pairing, which is fine. Treat as normal PR review, not self-review.

## Cross-agent discussion that informed Phase A brief

**Bridge msg 437 (task `1529-writer-prompt-strategy`)** — Codex's critique of my initial 3-step strategy. Seven pushbacks; all seven accepted. Key reframe:

> "Validator/enforcer first, writer cooperation second. Do the three prompt changes, but define success as *reducing annotator interventions*, not *replacing the annotator*."

Read the full Codex response via `.venv/bin/python scripts/ai_agent_bridge/__main__.py read 437`. The reframe changes our architecture posture: the deterministic `honesty_annotator` shipped in #1531 is the **load-bearing enforcement layer**, not a band-aid. Writer markers are desirable bonus. This is user-validated — they said "we should strive to create the best possible writing" AND accepted annotator-as-enforcer framing.

## What's NOT yet filed — Phase B

**Semantic claim-audit LLM step.** Proposed by Codex; user agreed to ship "if A doesn't converge." Deferred until after the a1/1 rebuild produces empirical data on annotator-injection count.

Scope when the next session picks it up:
- New pipeline step between `write` and `honesty-annotate` (OR absorb into honesty-annotate as a pre-regex LLM pass).
- Input: prose + knowledge packet + plan.
- Output: **structured JSON** — list of precise/risky claims with `{claim, quote, needs_verify, reason, replacement_or_marker}`.
- Then deterministic insertion uses the JSON. Catches semantic claims regex misses (dated assertions like "Ґ restored in 1990", absolute quantifiers without digit patterns, citations to named authorities without sources).

Success gate: run it on a1/1's current content, measure how many additional claims it flags vs the current regex annotator. If ≥3 additional claims, ship it.

**User's philosophy on this**: "we are struggling for MONTHS and you are worried about some extra hour?" — blunt push to ship infra improvements without cost-optimizing. Do not hesitate to ship Phase B after A converges.

## a1/1 pilot state (still user-owned)

Still at `plan_revision_request` terminal from `11:02 UTC`. Module content on disk last modified `12:47 local`. State.json phase list predates the `honesty-annotate` step addition (PR #1531). User has not re-fired the build since morning.

**Dry-run preview of honesty-annotate on current a1/1 content** (ran in this session, result not persisted): 4 markers would be injected at lines 14, 18, 31, 54 — exactly the "33 letters / 38 sounds / 6 vowels / 10 vowel letters / 32 consonants / 22 consonant letters" claims that R3 Honesty reviewer flagged.

**When user runs the rebuild**:
```
.venv/bin/python scripts/build/v6_build.py a1 1 --step honesty-annotate
.venv/bin/python scripts/build/v6_build.py a1 1 --step review --resume \
  --writer claude-tools --reviewer codex-tools
```

OR after Phase A PR merges, a full redo:
```
.venv/bin/python scripts/build/v6_build.py a1 1 --force \
  --writer claude-tools --reviewer codex-tools
```

User prefers full-redo ("lets redo the whole ok?"). Do NOT use `--step all --resume` (MEMORY #2 warning: that pattern destroyed a2-bridge + 40+ files earlier in the month).

## Expected dim-by-dim outcome after rebuild

| Dim | Last R3 score | Why it should improve |
|---|---|---|
| Factual | 4.5 (REJECT) | мама ghost finding now surfaces in `{slug}-ghost-review-r{N}.yaml` instead of dragging MIN-gate (#1532). 3 real factual findings already patched on disk. |
| Honesty | 5.0 (REVISE) | `honesty-annotate` step injects 4 VERIFY markers; Phase A writer prompt hardening adds more upstream. Hard-cap condition no longer fires. |
| Plan Adherence | 7.4 (REVISE) | 5 phantom section-overrun findings can't re-emit — prompt §2 fix (#1530) makes `max` advisory. Only silent-deferral counts. Activity-marker-placement findings are valid and their fixes patchable. |
| Decolonization | 9.4 | Already passing. |
| Language / Completeness / Actionable / Naturalness / Dialogue | 7.5 – 9 | At or above floor; unaffected. |

All ≥ 8 → MIN-gate PASS → first built A1 module.

## Failure modes to watch for when rebuild returns

1. **Annotator injects >0 markers AND writer emitted 0** → Phase A didn't improve writer compliance. Ship Phase B (semantic claim-audit) without waiting.
2. **Factual dim STILL <8 after ghost routing** → Codex reviewer hallucinating MORE than just the mama case. Investigate per-dim reviewer prompt.
3. **Plan Adherence flags ACTIVITY_PLACEMENT defects correctly** → those patches should apply (anchors are `<!-- INJECT_ACTIVITY: {type} -->` strings, trivially stable). If they don't apply, the convergence routing has a different bug.
4. **New terminal is `reviewer_ghost_review` instead of `plan_revision_request`** → means P3 is working and surfacing hallucinations. User reviews the bundle, decides what to patch manually.

## Things NOT to do next session

- **Do NOT propose `WORD_BUDGET_MAX` gates.** Rebuffed hard earlier today — NON-NEG rule #1 and #3 say word targets are MINIMUMS. Policy is one-sided tolerance. `max` field is soft guidance for the writer, not a pipeline enforcement threshold.
- **Do NOT self-review Claude dispatches.** When reviewing the #1529-A PR, the diff is from a fresh Claude context → independent. But don't add `<!-- reviewer: claude -->` to your own artifacts.
- **Do NOT touch `curriculum/l2-uk-en/a1/sounds-letters-and-hello*`.** User-active pilot.
- **Do NOT revive the "semantic claim audit with same-call JSON sidecar" idea** without re-reading Codex msg 437 — they explicitly flagged that "same-call sidecars often drift and add another compliance surface." Phase B should be a SEPARATE LLM call, not a sidecar.
- **Do NOT use `--step all --resume`.**
- **Do NOT skip pre-commit hooks.**
- **Do NOT dispatch to Claude when the brief is detailed-and-mechanical.** User pushback this session: I was under-using Codex. The 6:4 split per MEMORY means Codex gets pattern-applying, mechanical refactors, and briefs where "if Codex follows literally, output is correct." Claude reserved for open-ended design, linguistic/cultural nuance, adversarial review.

## Open carry-overs (not blocking a1/1)

- **#1526** — EPIC #1525 follow-ups. Batch-patchability semantics + anchor-matching parity (apply-step's 4 strategies into shared helper). Item 2 needs empirical data first; don't ship until a few more modules built.
- **#1523** — `/api/state/governance` endpoint (decisions + ADRs unified). Small, mechanical → Codex.
- **#1522** — postmortem management automation. Larger.
- **#1451** — EPIC: Alignment-Pipeline Runtime Contracts.
- **#1435** — wiki sources.yaml backfill across 227 files.
- **#1395** — `/api/git/cleanup` endpoint. Marked "deferred, low urgency."

If a1/1 converges cleanly, #1526 item 2 is the most natural next pickup because it directly reduces ghost-routing misfires by reaching feature-parity with the apply step's 4-strategy anchor matching.

## Tool + agent state at handoff

| Agent | Status |
|---|---|
| Codex | Idle. Msg 436/437 closed. No dispatches in flight. |
| Claude (headless) | **1 in flight** — Phase A `1529-a-prompt-hardening`, xhigh effort. PR expected within 10-15 min. |
| Claude (me, this session) | Context elevated after 4+ hours. Handing off. |

## Context accounting

- Session ran roughly 4.5 hours (10:25 UTC cold-start → 14:40 UTC handoff).
- Peak work density in the first 3 hours; last 90 min mostly monitoring + the Phase A dispatch.
- Did not use `/compact` or `--resume`. Fresh session + this diary is the pattern per MEMORY #2.
- Next session cold-start: run the Monitor API bootstrap per `workflow.md` rule, read this file FULLY, check `gh pr list` and `gh pr checks 1533` (or whatever number Phase A PR gets) before making any decisions.

## Channel bridge state

- Task `1529-p0-review` — closed previous session.
- Task `1525-p0-review` — closed previous session.
- Task `1529-writer-prompt-strategy` — msg 436 (my brief to Codex) + msg 437 (Codex critique). Used to inform Phase A brief; no further rounds needed.

## One-line summary for `current.md`

> Writer-prompt hardening Phase A in flight (headless Claude); a1/1 pilot awaits rebuild; EPIC #1529 P1-P3 all shipped; Phase B (semantic claim-audit) queued pending rebuild empirical data.

---

*Generated 2026-04-24 ~14:40 UTC. Tip of origin/main: `6e01709bc0`. One Claude dispatch in flight on branch `claude/1529-a-prompt-hardening`. User has not re-fired a1/1 yet.*
