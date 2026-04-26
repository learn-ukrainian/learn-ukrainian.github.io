# Session Handoff — 2026-04-26 (Round-3 diagnostic, QG bugfixes shipped)

> **Predecessor:** `2026-04-26-evening-handoff.md` (Phase 4 round 3 dispatched)
> **Mode:** Cleaning up at the end of the session. 8% budget remaining.
> **Successor scope:** decide round 3.5 (prompt-tighten) vs round 4 (writer bakeoff) for Phase 4.

---

## TL;DR — what shipped

```
a6b9e7f417  fix(phase-4): eliminate Python QG false positives masking round-3 signal (#1599)
3603f11774  feat(phase-4): strict-JSON writer contract (#1577 round 3 step 0) (#1598)
```

Both merged this session, after a corrected adversarial-review sequence (3-agent panel: bot + Gemini + Codex). The merge unblocks Phase 4 fan-out planning, but **round 3 itself is NOT closed**: there are real writer failures still on the table.

---

## What round 3 actually told us (post-bugfix, honest signal)

The round-3 A1/20 exemplar (`my-morning`) failed 5 Python QG gates. Diagnostic showed **4 of those 5 failures were Python QG bugs**, not writer issues. After PR #1599 the gates run honestly. Three real writer failures remain:

| Gate | State | Root cause | Fix layer |
|---|---|---|---|
| `plan_sections` | 3 sections 25–40% over budget | Gemini wrote chatty English meta-narration ("Welcome to the start of our journey...", "Now that you have seen these verbs..."). Same root cause as immersion. | Writer prompt OR bakeoff |
| `immersion.pct` | 11.72% (need 15-35%) | Same chatty over-writing dilutes Ukrainian ratio. | Writer prompt OR bakeoff |
| `component_props` | 3 errors: `act-my-morning-4` (fill-in) + `act-my-morning-8` (fill-in) used `passage:` curly-blank syntax instead of `items:`; `act-my-morning-6` (order) needs `correct_order` field | Writer prompt gap — schema not in prompt | Writer prompt + maybe schema relaxation |
| `vesum_verified` | 3 missing: `Караман`, `Ліна`, `Настя` | Proper names not in whitelist (textbook author + dialogue characters) | One-line data fix to `PROPER_NAME_WHITELIST` |

**The real architectural question for next session:** round 3.5 (prompt-tighten with same Gemini) or round 4 bakeoff (claude-tools vs gemini-tools)?

My recommendation from earlier in the session (still valid): **start with round 3.5 prompt-tighten.** Concretely:

1. Add to `linear-write.md`: explicit "no English meta-narration / no pedagogical introductions / open each section directly with grammar or Ukrainian examples"
2. Render component-prop schema requirements (per `docs/lesson-schema.yaml`) into the writer prompt so it knows fill-in needs `items:` not `passage:`
3. Expand `PROPER_NAME_WHITELIST` for textbook authors + dialogue characters
4. Re-run round 3 with the tightened prompt + same Gemini
5. If Gemini STILL produces meta-narration after explicit prohibition, **THAT'S** the bakeoff signal (per ADR §3, Phase 5+ entrance gate pulled forward)

Rationale: chatty over-writing is highly fixable in prose. If a prompt tweak fixes it, we save Claude budget for the actual content. If Gemini ignores explicit prohibition, that's strong evidence for bakeoff.

If user prefers bakeoff first, that's also valid — it pulls the Phase 5+ gate forward and gives empirical data on writer choice immediately.

---

## How today's review sequence went (corrected workflow)

The first round of reviews on these PRs **bypassed the mandatory adversarial review step.** Only the automated `gemini-code-assist` bot left drive-by comments; the explicit `--model gemini-3.1-pro-preview` Gemini review was skipped, and Codex (gpt-5.5) was not consulted at all.

User pushback corrected this mid-session. The corrected sequence:

1. **Read bot findings** — classified false alarms vs real (3 on #1598, 2 on #1599)
2. **/simplify 3-agent panel** (reuse / quality / efficiency) — surfaced walker dup, regex hoisting, fixture dup, etc.
3. **Adversarial review with both Gemini AND Codex on each PR** (4 reviews total in parallel) — surfaced 7 NEW correctness issues missed by prior rounds
4. **Cross-agent triage** — agreement on 6 issues, one disagreement (outer-fence-strip — went with Codex per Path 1 alignment)
5. **All real findings addressed** — 10 fixes across both PRs, 16 new regression-guard tests
6. **Final CI green on both** → squash-merge → branch delete → worktree cleanup

**Lesson** (added to MEMORY ought to be a future task): when shipping coding PRs, **all three agents must be in the loop** before merge. The bot's drive-by review is not a substitute. Gemini+Codex parallel review is the standard.

**Cost data**: each adversarial review took ~2-4 min. 4 in parallel is essentially the time of one. Vastly cheaper than the bug-then-fix loop that would have followed silent merge.

---

## Worktree state (cleaned)

```
/Users/krisztiankoos/projects/learn-ukrainian                                  [main]
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/codex-interactive     (stale, detached HEAD — flagged for prior session, NOT my problem)
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/verify-a1-1-phaseA-v5 (user's preserved manual patches, DO NOT touch)
```

Both `codex-phase4-round3-json-exemplar` and `dispatch/claude/phase4-qg-bugfixes` worktrees removed post-merge. Branches were squash-deleted by GitHub on merge.

**The main checkout's HEAD is at `b532271f3d`, behind origin/main `a6b9e7f417` by 5 commits**: that's the user's working tree. Don't `git pull` from there without checking — user may have uncommitted work in progress.

---

## Stashes — round-3 diagnostic artifacts

The failed Gemini exemplar artifacts (the actual round-3 module.md/activities.yaml/vocabulary.yaml/resources.yaml that Gemini generated) survive in the repo's global stash list:

```
stash@{0}  On codex/phase4-round3-json-exemplar: round-3 diagnostic artifacts
stash@{1}  On codex/phase4-round3-json-exemplar: round-3 diagnostic artifacts (keep out of cleanup commit)
```

(`{0}` and `{1}` are duplicates from my session — same content, kept both for safety.)

To inspect them in the next session for round-3.5 planning:

```bash
git stash show -p stash@{0}                # see the diff
mkdir -p /tmp/round-3-failed-artifacts
git checkout stash@{0} -- curriculum/l2-uk-en/a1/my-morning/
# ...inspect...
# To recover the in-progress diagnostic state without applying:
git stash show -p stash@{0} > /tmp/round-3-failed-artifacts.diff
```

Or apply directly via `git stash apply stash@{0}` (in any worktree).

These artifacts are useful evidence for the round 3.5 vs round 4 decision: they show concretely how Gemini's chatty meta-narration looks, so prompt-tightening attempts can target the specific patterns.

**Future cleanup** (lower-priority): once round 3 is fully closed (3.5 ships or bakeoff completes), drop both stashes.

---

## Active background tasks at handoff time

- **None of mine.** All my background watchers/dispatches completed.
- 4 user-launched Gemini wiki rebuilds may still be running (pids 6803, 13598, 13629, 56100 — bio/hist/lit/b2). These are **not orchestrator work**. When user's `pgrep -f "compile.py.*--track"` is empty, follow the `b7db136b1d` commit pattern to land the wiki updates.

---

## Open coding issues NOT touched today

Same list as the evening handoff predecessor, all deferred:

- #1573, #1571, #1570 — Wiki ingestion bugs (Ukrainian wiki ingestion)
- #1553 — Wiki retrieval overhaul
- #1377 — Wiki corpus expansion to B1+/seminar tracks
- #1373 — Ingest 55 Ukrainian-canonical A1 wikis
- #1351, #1350 — Diagnostic / Bright Kids ingestion
- #1333 — Corpus gap analysis
- #1201 — Release: v1.0 launch

None are Phase-4-blockers per current scope.

---

## Cold-start protocol for next session

```bash
# 1. Verify state
git -C /Users/krisztiankoos/projects/learn-ukrainian log --oneline origin/main -5
# Should see: a6b9e7f417 (fix QG) → 3603f11774 (strict-JSON) → 698befbef5 (round-2 hardening)

gh pr list --state open --limit 10  # phase-4 should have NO open PRs

# 2. Read this handoff (or the index in current.md)

# 3. If picking up round 3.5 planning, recover the failed Gemini artifacts:
git stash show -p stash@{0}  # or stash@{1}

# 4. Decide: prompt-tighten round 3.5 vs writer bakeoff round 4. The brief
#    for either is in this handoff above.
```

---

## Final stats for the session

- **2 PRs shipped** (#1598 strict-JSON contract, #1599 QG bugfixes)
- **6 commits to main** (squash-merged, including pre-merge cleanups)
- **51 tests pass** total across the two PRs (33 in #1599's branch + 18 in #1598's branch — overlap not deduplicated since they were on separate branches)
- **4 adversarial review reports archived** in the bridge message store (IDs 472, 473, 474, 475 — Gemini + Codex × 2 PRs)
- **1 architectural decision deferred** — round 3.5 vs round 4 bakeoff
- **1 architectural decision recorded** — outer-fence-strip rejected; strict-fail-as-unnamed aligns with Path 1
- **0 open Phase 4 PRs** at handoff time
- **1 known limitation documented** in `_JSX_BLOCK_RE` docstring: regex cannot fully parse JSX (nested same-name components, JSX comments, `<Capital>` literals in string props). Acceptable for QG gate purpose; a real JSX tokenizer is a separate concern.

---

## Decision journal note

Today's decisions (informal — not yet promoted to ADR-level docs):

1. **Adversarial review must run all 3 agents** (bot + Gemini + Codex) before merge. The drive-by `gemini-code-assist` bot is not a substitute for explicit `--model gemini-3.1-pro-preview` review. Cost: ~2-4 min per review, 4 in parallel = effectively 1 review's wallclock. Cheaper than silent-merge then bug-then-fix.

2. **Strict-JSON writer contract is canonical for Phase 4.** Path 1 alignment: no YAML repair, no heuristic JSON cleanup, no LLM regen on parse failure. Outer-fence-strip explicitly rejected as same-class fix.

3. **Python QG must walk artifacts structurally**, not text-grep YAML dumps. The naïve text-blob approach produced 4 distinct false-positive classes (markdown link text, JSX object literals, intentional misspellings in `error-correction`, sentence-initial capitalization). Structural walking + per-field semantics is the correct model.

The Path-1 strict-JSON discussion is recorded in architecture-channel thread `0e3e9b7042c34c6d9b6f87bfcfc7f0fa`. The QG-bugfix discussion is informal — could be promoted to an ADR if "QG must walk structurally" becomes a recurring guideline.
