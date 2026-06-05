# Session Handoff — 2026-04-26 overnight (Phase 3 closed, driving #1586 + Phase 4)

> **Continues from:** `2026-04-26-phase-3-impl-dispatched.md` (now obsolete — Phase 3 merged this session).
> **State:** EPIC #1577 Phases 0-3 ✅ shipped to main. Phase 4 (A1/20 `my-morning` exemplar) is next, blocked on #1586 (per-level per-dim LLM QG threshold schema).
> **User:** going to sleep. Wiki rebuild running in parallel. Strict rule: do **not** touch `wiki/` or `curriculum/l2-uk-en/{a1,a2,b1}/discovery/` — user-stated account-cancel level.
> **This session continues as orchestrator overnight.**

---

## What landed today (commits on main)

```
d79457e5e9  phase-3: lesson schema and prompt substitution (#1590)         ← Phase 3 impl, this session
67741940dd  feat(wiki): multi-agent writer support for compile.py (#1589)  ← wiki agent's PR, this session
f9f7360b12  test(post-reboot): self-skip vitest tabs assertion when module deleted  ← unblocks Frontend CI
f0635c70ad  phase-2: config audit per Phase 0 docs (#1583) (#1588)         ← Phase 2 audit, this session
a3ec8ed95b  docs(phase-3): land lesson-schema design v2 (#1584)            ← overnight session
a6745ecf02  security: scrub user email from rebuild surface
746b88ca52  docs(handoff): overnight session — drive Phase 2 + Phase 3 + set up Phase 4
ebe1a89b3f  fix(sources-db): file-size primary guard + recovery runbook (#1563)
```

## EPIC #1577 phase ledger

| Phase | Status | Anchor commit |
|---|---|---|
| 0 — North Star + Lesson Contract | ✅ done | `de97c45572` |
| 1 — Salvage manifest | ✅ done | (multiple) |
| 2 — Config audit | ✅ done | `f0635c70ad` |
| 3 design — Lesson schema | ✅ done | `a3ec8ed95b` |
| 3 impl — Schema + substitution + drift gate | ✅ done | `d79457e5e9` |
| **4 — A1/20 `my-morning` exemplar** | **NEXT — blocked on #1586** | — |
| 5 — A1/4–A1/55 fan-out | gated on Phase 4 | — |
| 6 — A2/30 exemplar → A2 fan-out | gated | — |
| 7 — B1/20 exemplar → B1 fan-out | gated | — |
| 8 — A1/1, A1/2, A1/3 (literacy bootstrap) | last | — |

## Open issues blocking the critical path

- **#1586 `reboot-blocker`** — per-level per-dim LLM QG threshold schema. Phase 4 LLM QG can't run cleanly until `LevelThresholds` can express per-dim floors and the aggregator fails on min-failing-dim, not weighted average. **This is the next thing.**
- **#1585 `mvp-deferred`** — retire legacy activity type registries after matrix alignment. Not blocking Phase 4. Defer.
- **#1587 `backlog`** — remove obsolete global `MAX_SENTENCE_LENGTH` fallback. Not blocking. Defer.

## What's ACTIVELY IN PROGRESS — DO NOT TOUCH

### User-initiated work (ABSOLUTE NO-TOUCH)

- **Wiki rebuild** — user is actively building wiki/. Modified files in main checkout's working tree are user's. Untracked `curriculum/l2-uk-en/{a1,a2,b1}/discovery/*.yaml` files are user's. **Touching either of these is account-cancel-level per user direction 2026-04-26 ~01:30 CET.** Forbidden code paths:
  - Anything that writes to `wiki/`
  - Anything that writes to `curriculum/l2-uk-en/{a1,a2,b1}/discovery/`
  - `scripts/wiki/compile.py` invocations of any kind
  - `scripts/wiki/discover_*` invocations of any kind
  - Force-pushes to wiki-related branches
- **Wiki agent session** — `docs/session-state/2026-04-25-wiki-retrieval-overhaul-1553.md` and `2026-04-25-cold-encode-complete.md`. Their work merged this session as PR #1589.

### This session's overnight plan (in-flight after handoff lands)

- **#1586 design + dispatch** — about to start.
- **Phase 4 brief draft + dispatch** — after #1586 merges.

### Other agent sessions

- **Orchestration session** — `docs/session-state/2026-04-25-orchestration-final-with-data.md`. EPIC #1550 a1/1 verification (Unit 6 A/B). All units landed.
- **Overnight orchestrator (closed)** — `docs/session-state/2026-04-26-phase-2-driving-overnight.md`. Their plan executed and shipped this session.

## Overnight execution plan (ordered)

### Wave 1 — #1586 (per-level per-dim LLM QG thresholds)

1. Read `scripts/common/thresholds.py` end-to-end (current `LevelThresholds` schema, `REVIEW_PASS_FLOOR` etc.).
2. Read Phase 0 SHIPPABLE point 7 in `docs/north-star.md` for the binding constraint.
3. Read `docs/best-practices/strict-reviewer-persona.md` — the canonical "MIN aggregator, not weighted average" reference.
4. Draft schema inline in a scratch file under `docs/decisions/` (NOT `docs/best-practices/` — that's contract). Schema shape candidate:
   ```python
   @dataclass(frozen=True)
   class LevelThresholds:
       target_words: int
       review_floors: dict[str, float]  # {"pedagogical": 8.0, "naturalness": 9.0, ...}
   ```
5. Draft the aggregator semantics: `pass_iff = all(score[dim] >= floor[dim] for dim in DIMS)`. Single source of truth — kill `REVIEW_PASS_FLOOR` global.
6. **3-agent review** via `ab discuss architecture --with codex,gemini --max-rounds 2` on the design doc. Land the design only after both `[AGREE]`.
7. Update issue #1586 with the design + acceptance criteria revision if needed.
8. Write Codex implementation brief under `/tmp/codex-brief-1586-llm-qg-thresholds.md`. Brief covers:
   - Schema migration (LevelThresholds + per-dim floors for every level)
   - Aggregator code change (single function, MIN, no weighted)
   - Removal of `REVIEW_PASS_FLOOR` / `REVIEW_REJECT_FLOOR` globals OR explicit isolation as legacy
   - Tests: one passing module, one single-dim-failing module
   - Worktree mandatory, slash convention `codex/1586-...` (delegate.py enforces)
9. Dispatch Codex via `delegate.py dispatch --agent codex --task-id codex-1586-llm-qg-thresholds --worktree .worktrees/codex-1586-llm-qg-thresholds --mode danger --prompt-file /tmp/codex-brief-1586-llm-qg-thresholds.md`.
10. **Pre-dispatch sanity:** `delegate.py list` (ALL statuses, not just running) to confirm no duplicate dispatch already in flight.
11. **Monitor with `Monitor` tool**, not ScheduleWakeup. Reference pattern that worked: poll `delegate.py status` every 30s, parse with python (jq + the venv-hint leak don't mix), exit on terminal status `done|failed|cancelled|timeout`. Note that running JSON has `elapsed_s`; finished JSON has `duration_s` — extractor must tolerate both.
12. When PR opens: review against the design (verify MIN aggregator, no weighted average remnants, tests cover failing-dim case). Merge if green CI.

### Wave 2 — Phase 4 brief + dispatch (after #1586 merges)

13. Re-read Phase 0 + Lesson Contract + Phase 3 design + the just-merged Phase 3 implementation. The exemplar build's success criteria are concrete:
    - Linear, fail-fast pipeline (no V6 convergence loop)
    - Writer prompt with `{NORTH_STAR}` + `{LESSON_CONTRACT}` substituted live (use `prompt_builder.render_prompt`)
    - Python QG = rules from Lesson Contract §5
    - LLM QG = single-pass per dim with MIN aggregator (uses #1586 schema)
14. Read `curriculum/l2-uk-en/plans/a1/my-morning.yaml` to understand the exemplar plan.
15. **Confirm A1/20 → my-morning** by reading `curriculum/l2-uk-en/curriculum.yaml` (plan number ↔ slug map).
16. Draft Phase 4 brief under `/tmp/codex-brief-phase-4-a1-20-my-morning.md`. Scope is large — partition into smaller dispatches if it would exceed reasonable Codex run length (the prior 1.5d-budgeted dispatches finished in ~14 min). Brief covers:
    - Pipeline orchestrator (single linear runner)
    - Writer phase using `prompt_builder.render_prompt(scripts/build/phases/v6-write.md)` with `{NORTH_STAR}` + `{LESSON_CONTRACT}` filled
    - Activities-author phase
    - Python QG runner against `lesson-schema.yaml`
    - LLM QG runner using #1586 thresholds
    - Output assembly to MDX
    - End-to-end test against the A1/20 plan
17. **3-agent review** on the brief before dispatch. This one is bigger; both panel agents must agree before firing.
18. Dispatch (worktree mandatory, slash convention).
19. Monitor as in Wave 1.
20. Review PR against the contract. Merge only if every Phase 4 success criterion is verifiable from the diff.

### Wave 3 — Handoff

21. **Context check at 300K (early signal), 400K (handoff zone), 450K (past target).** Self-check via:
    ```bash
    LATEST=$(ls -t ~/.claude/projects/-Users-krisztiankoos-projects-learn-ukrainian/*.jsonl | head -1)
    tail -200 "$LATEST" | jq -s '[.[] | select(.type == "assistant" and .message.usage != null)] | last | .message.usage | ((.input_tokens + .cache_read_input_tokens + .cache_creation_input_tokens))'
    ```
22. Write the morning handoff at `docs/session-state/2026-04-26-morning-after-overnight.md` before closing context window. Include exact state of every Wave above.

## Anti-checklist (this session must NOT)

1. **NOT touch `wiki/`** — user is rebuilding it. Account-cancel rule.
2. **NOT touch `curriculum/l2-uk-en/{a1,a2,b1}/discovery/`** — user's parallel work.
3. **NOT touch `curriculum/l2-uk-en/plans/`** — sacred per EPIC #1577 invariant.
4. **NOT use ScheduleWakeup as primary wake signal.** Monitor tool only.
5. **NOT skip `delegate.py list` (all statuses) before any dispatch.** Today I missed a prior `phase-3-implementation` dispatch and burned compute on a duplicate.
6. **NOT commit directly to main.** All work via PR.
7. **NOT `git add -A` or `git add .`** — specific files only.
8. **NOT solo-decide on architecture.** Anything load-bearing goes through 3-agent review (`ab discuss architecture`).
9. **NOT exceed 2 active Codex dispatches in flight** (per MEMORY DISPATCH CAP). Verify with `delegate.py list --status running` before adding a third.
10. **NOT amend commits.** Always new commits per critical-rules.md.
11. **NOT push without `--force-with-lease`** when force-pushing rebased branches.
12. **NOT try to "fix forward" overnight if something breaks.** Stop, write to handoff, leave for user.

## Decision tree for things going sideways

| Symptom | Action |
|---|---|
| Codex dispatch fails / asks question | Reply via `ab post architecture codex "..."`. Do NOT solo-decide on schema. |
| Codex PR has CI failures | Investigate root cause. Push fix to Codex worktree branch OR file follow-up issue. Do not merge red. |
| 3-agent review rejects design | Apply findings, redraft, one more round. If still rejected, file as design-debate issue and hand back to user. |
| Wiki rebuild collision suspected | STOP IMMEDIATELY. Do not investigate further. Write to handoff with timestamps and last actions. Wait for user. |
| Context approaches 400K | Write morning handoff IMMEDIATELY at landing point. End session. |
| #1586 design takes too long / unclear | Mark Phase 4 blocked in this handoff. Don't proceed with Phase 4 design without #1586 settled. |
| All planned work done before context fill | File ideas for Phase 5 (A1/4–A1/55 fan-out plan) but do NOT execute. Phase 5 is multi-week and needs user direction. |

## Cold-start protocol for next session (or me on wake)

1. Read this handoff fully.
2. `git log --oneline -10` — see what landed.
3. `gh pr list --state all --limit 5` — see Codex PRs (open or merged) from this session.
4. `gh issue view 1577` — EPIC status.
5. `gh issue view 1586` — design + sub-issue trail.
6. `delegate.py list` — see ALL dispatches (running, done, failed). Don't skip terminal ones.
7. `git worktree list` — see what dispatches have worktrees still around.
8. `ab channel tail architecture -n 30` — recent agent discussion.
9. Continue per the wave the prior iteration was on, OR per user direction if user is back.

## Channel + thread references

- Phase 3 design sign-off thread: `architecture` `911722b35b3d4cb7abe19059a1ba1044`
- Phase 0 sign-off thread: `architecture` `6de2be4789394536abdb6356cd5bb006`
- #1586 review thread: TBD (will create on `ab discuss architecture` invocation)

## Lessons learned this session (record for memory next session)

1. **`delegate.py list` defaults to ALL statuses; `--status running` filters out done dispatches.** I checked `--status running` (returned `[]`), missed a prior `phase-3-implementation` dispatch that finished with `worktree_dirty_on_exit: true`, and dispatched a duplicate. Cost: ~14 min Codex compute. Lesson: list ALL statuses before dispatching.
2. **Codex's `<20 changed files` rule is its own conservatism, not a CI gate.** No such check exists in `.github/workflows/`. Briefs can target the full scope; Codex will partition naturally.
3. **delegate.py `wait`/`status` JSON has different fields per status.** Running: `elapsed_s`. Done: `duration_s`. Extractors must handle both or use `.get()`.
4. **Shell hint `💡 Python project detected. Activate venv with: venv` leaks to stdout from a `cd`-triggered hook.** Breaks naive `jq` extractors. Workaround: invoke delegate.py as a subprocess from python, slice from `out.find('{')`.
5. **`gh pr checks --watch` exits 1 when ANY check is non-passing — including advisory `Frontend (build + vitest)`.** Read mergeStateStatus + actual check list, don't rely on watch exit code.
6. **PRs sitting in CI do NOT consume the 2-Codex-in-flight cap.** Only ACTIVELY RUNNING `delegate.py dispatch` agents count. Verify via `delegate.py list --status running`.
7. **Branch naming: `delegate.py dispatch` enforces slash convention** (`codex/<id>-<topic>`). Manually-created branches use hyphen (`codex-<id>-<topic>`). Don't mix; mind during `git push`.

## Known bugs — flagged by user this session, NOT mine to fix

- **Wiki canonical-anchor checker false-positives on teaching context** (user-flagged 2026-04-26 ~01:50 CET, user said "don't touch, we will fix it later"). When a wiki article cites a wrong form to teach against it (e.g. *"Не кажіть «Здрастуйте» — кажіть «Добрий день»"*), the checker sees «Здрастуйте» and adds a `<!-- VERIFY -->` marker even though the article is doing exactly the right thing. Symptom example: 4 violations on `pedagogy/a1/checkpoint-food-shopping.md` for `greeting_hello_formal` («Здрастуйте») and `copula_present_tense` («Я є студент»).
  - **Location**: `scripts/wiki/discipline.py:194` `validate_canonical_anchors` runs each forbidden regex against the full article body with zero context awareness.
  - **Likely fix shape**: skip the violation when `anchor["correct"]` (or any of `correct_alternates`) appears within ~120 chars of the match — teaching context always shows wrong + right side-by-side; real misuse only shows the wrong form. Suppress at *validate* time, not *flag* time, so the build-output noise + VERIFY-marker insertion both go away.
  - **Status**: user instructed "don't touch". Leave for user OR future session with explicit user approval.

## Files in flight when this handoff was written

- `docs/session-state/2026-04-26-overnight-1586-phase4.md` (this file)

## Worktree state at handoff write time

```
/Users/krisztiankoos/projects/learn-ukrainian                                  f9f7360b12 [main]   ← USER's
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/codex-interactive     3c8bc39bae (detached HEAD)
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/verify-a1-1-phaseA-v5 ab3178fb64 [verify/a1-1-phaseA-v5]
```

`main` is at `f9f7360b12` not `d79457e5e9` because user's main checkout hasn't pulled. Origin/main is at `d79457e5e9`. Don't pull in user's checkout — they may have uncommitted wiki rebuild work.
