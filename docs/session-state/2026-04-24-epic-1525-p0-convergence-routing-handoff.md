# Session Handoff — 2026-04-24 ~10:20 UTC: EPIC #1525 P0 landed (convergence routing predicate)

> **TL;DR** Pilot `a1/sounds-letters-and-hello` R1 hit a routing bug — 9 clean
> reviewer `<fixes>` were dropped on the floor because the topology classifier
> misclassified 5 findings as `cross_section`. Filed EPIC #1525, ran full cross-agent
> design review, landed P0 as commit `23ee12b0fc`. ADR-007 held unchanged per
> consensus. User to re-fire the build next session.
>
> **Next action (user-owned):** `.venv/bin/python scripts/build/v6_build.py a1 1 --step review --resume`.
> Expected: pipeline re-reads cached R1, applies 19 `<fixes>` deterministically, re-enriches, re-reviews. Monitor via JSONL events.

---

## What shipped this session (newest first, all on main)

| Commit | Subject |
|---|---|
| `23ee12b0fc` | `feat(convergence)` — validated-patchability predicate for routing (+#1525 P0) |

One commit. Small-looking on its face (4 files, 677 insertions) but architecturally load-bearing: changes how the convergence loop decides between `patch` and `plan_revision_request`.

## Architecture decision — DO NOT re-propose revisiting ADR-007 without new empirical data

User asked whether ADR-007 (accepted 2026-04-24, kills all LLM-regen tiers) was over-aggressive in light of a1/sounds-letters-and-hello R1. I fired a 3-round cross-agent discussion:

**Thread**: `ab channel tail architecture --thread 8aaa5760a2814e1192dac1b61b1b4098`

**Unanimous consensus (Claude + Gemini + Codex, round-2 AGREE)**: **Hold ADR-007 for runtime behavior. Fix the routing, not the tier structure.** The a1/1 failure was a routing bug (heuristic classifier misfire), not evidence for reviving scoped-regen. Codex specifically refined the design: don't make "has `<fixes>`" synonymous with `local_to_prose`; route on **validated patch eligibility** (parsed fix + anchor validates against current content + not plan-level).

Scoped-regen research relegated to shadow-mode RFC (filed as #1526 follow-up). If someone proposes reintroducing a regen tier, they need new empirical data that shows it beats deterministic patching without colors-class regression. ADR-007 expiry: 2027-04-23.

## Issues filed this session

| # | Title | Status |
|---|---|---|
| **#1525** | EPIC: Convergence loop — routing fix + human-review drawer | **open, P0 done, P1-P3 pending** |
| **#1526** | EPIC #1525 follow-ups: batch-patchability semantics + anchor-matching parity | open |

## EPIC #1525 phase breakdown

- [x] **P0** — Validated-patchability predicate replaces heuristic-only routing. Landed `23ee12b0fc`.
- [ ] **P1** — Observability: `ConvergenceDecision.patchability_audit` field + JSONL `convergence_decision` events + Monitor API `/api/state/convergence/{track}/{slug}` + dashboard card. All audit data is ALREADY present on each finding dict (`topology_classifier_output`, `patchability`, `patchability_reason`) — just needs to be surfaced.
- [ ] **P2** — Human-review drawer: rewire `plan_revision_request` terminal to write `human-review/{track}/{slug}/` bundle (findings, current content, attempted fixes, history, adjudication prompt) + Monitor API endpoints + dashboard surface.
- [ ] **P3** — Cleanup + invariants: remove dead-letter YAML references, add invariant test, docs, ADR-007 appendix.

## What the next session MUST do (priority order)

1. **If user re-fired the build overnight**: triage via Monitor event stream. Expected success path: r2 REVISE → fixes applied → r3 PASS (or module_done on r2 if all pass). If still failing, pull the r2 review artifacts and examine.
2. **If user has NOT re-fired**: remind them. The whole P0 work is predicated on this next build run validating the predicate against real pipeline behavior.
3. **If pilot converges**: P1 is the right next phase. Observability is cheap (data already populated, just needs plumbing) and unlocks P2/P3.
4. **If pilot fails**: don't panic — diff what went wrong. Possibilities:
   - Apply step's stress-mark normalization succeeds where my predicate says `anchor_missing` (documented asymmetry, filed as #1526 follow-up)
   - R1 findings route to patch but R2 still fails on REVISE for different reasons (Factual overgeneralizations may persist after the find/replace is surgical but the underlying writer-side defect isn't addressed)

## The two Codex PRs I did NOT close this session

Both inherited from yesterday's handoff. Still open:

- **PR #1521** — `codex-1520-liveness-probe-phase1` — clean diff (391 adds, 0 deletes, 2 files, 24 tests, 100% coverage). CI green except advisory Gemini-Dispatch review. **Should merge** per MEMORY #0H action-bias policy. Didn't get to it this session because the pilot diagnostic took precedence.
- **Branch `codex-1519-git-hygiene-endpoint`** — worktree at `/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/codex-1519-git-hygiene-endpoint`. Orient this morning showed it at main's HEAD (no commits). Mid-session git worktree list showed it at `723fa15181` (not main) — so SOMETHING happened between orientation and commit, but no PR was filed. Needs investigation next session. Either Codex is still working in that worktree (unlikely, would show in delegate logs) or it crashed silently.

## Files touched (and why)

| File | Why |
|---|---|
| `scripts/build/patchability.py` (NEW, 215 LOC) | New predicate module — `AnchorValidation` dataclass + `compute_anchor_validation` + `classify_patchability` + `PatchabilityStatus` |
| `scripts/build/convergence_loop.py` (+42 LOC) | `ReviewObservation.parsed_fixes` + `.module_content` fields. `_normalize_observation` runs the predicate, overrides topology to `local_to_prose` iff `patch_ok`. Per-finding audit trail. |
| `scripts/build/v6_build.py` (+15 LOC, -4 LOC) | Single `read_bytes` feeds both content and sha256 hash. `parsed_fixes` stored as tuple once, reused for `patch_available` bool. |
| `tests/test_patchability.py` (NEW, 401 LOC) | 18 tests inc. golden fixture from the pilot + dispatch-order parity with apply step + empty-tuple telemetry regression guard |
| `tests/test_convergence_loop.py` (+10 LOC) | Boy-scout: added `pytest.skip` for pre-existing fixture-missing test (reads live curriculum review-r2.md/r3.md, operators can delete between builds). Follow-up #1526 to move fixtures into `tests/fixtures/`. |

## The 3-part patchability predicate (for the next agent session)

Read `scripts/build/patchability.py` before touching anything in convergence routing. The semantic:

```
Finding is "validated patchable" iff ALL three hold:
  1. parsed_fixes non-empty (reviewer emitted <fixes>)
  2. Every fix's anchor (find or insert_after) is present in current
     module content — validated ONCE per observation via
     compute_anchor_validation(fixes, content), NOT per finding
  3. Finding is NOT plan_level (preserves ADR-007 plan_revision_request
     routing for genuine plan defects)
```

When the predicate validates, `_normalize_observation` overrides the topology classifier's output to `local_to_prose` for that finding, which lets `select_strategy` route the whole set to the deterministic patch tier. Otherwise the classifier's output stays intact.

**`ReviewObservation.parsed_fixes` and `module_content` defaults are `None`, not `()` / `""`.** This matters — the distinction between "legacy caller didn't populate" (None → `not_evaluated`) and "reviewer emitted zero fixes" (() → `no_fixes`) is load-bearing. Don't collapse them. See `test_empty_parsed_fixes_tuple_reports_no_fixes_not_unevaluated` for the regression guard.

**Dispatch order MUST mirror `_apply_review_fixes` at `v6_build.py:8180`** — `insert_after` checked BEFORE `find`. Codex caught this in round-1 review. See `test_mixed_shape_fix_validates_insert_after_first` for the regression guard.

**Anchor matching is plain `str in content`** — STRICTER than the apply step's 4-strategy match (exact / whitespace-normalized / stress-mark-aware / punctuation-normalized regex). False negatives escalate to human review, not silent ship. Intentional for P0. Parity backport is a #1526 follow-up.

## Things NOT to do next session

- **Do NOT propose reviving scoped-regen or `<rewrite-block>` or `<writer_directives>` tiers.** ADR-007 holds unchanged per cross-agent consensus. The burden of proof for reviving regen is new empirical data, not a new theoretical argument. 12-month expiry on ADR-007 (2027-04-23) exists for this reason.
- **Do NOT touch `wiki/**` or `curriculum/l2-uk-en/a1/sounds-letters-and-hello*`.** Both user-active.
- **Do NOT file new issues for the patchability follow-ups** — they're all tracked in #1526. Add comments to #1526 if you find new evidence; don't sprawl.
- **Do NOT skip pre-commit hooks** (`--no-verify`). Pre-commit hook runs `tests/test_{module}.py` for each staged `.py`. Boy-scout any fragile test in blast radius, don't bypass.
- **Do NOT merge Honesty + Factual dims without user approval.** User flagged them as potentially mergeable earlier in this session, we discussed, no decision. Still open.
- **Do NOT ask "should I merge PR #1521?"** — memory #0H, it's my job. Read + merge when the build triage is done.

## Open things the next session may want to close

- **Merge PR #1521** (#1520 liveness-probe P1) — clean, inherited, overdue
- **Triage #1519 Codex dispatch** — worktree exists at `.worktrees/codex-1519-git-hygiene-endpoint`, no PR. Check `delegate_logs`, check if codex process is dead, commit cleanup if orphaned.
- **#1526 stress-match parity** — medium priority, blocking visibility-into-P0-effectiveness. Tied to how many real reviewer fixes need strategies 2-4.

## Architecture change that needs permanent awareness

> **`scripts/build/patchability.py`** is now load-bearing. It replaces the
> fragile heuristic-only routing in `finding_topology.py` as the authoritative
> signal for deciding whether a finding can be deterministically patched.
>
> `finding_topology.classify_topology` is still called — its output is preserved
> in `topology_classifier_output` for telemetry — but the patchability predicate
> OVERRIDES its output to `local_to_prose` when validation passes.
>
> If you find yourself wanting to revive the `classify_topology` heuristics as
> the primary routing signal: STOP. Read the cross-agent thread `8aaa5760`
> and the commit message of `23ee12b0fc`. The heuristics mis-fired on 5 Plan
> Adherence findings in the pilot — that's why we replaced them.

## Cross-agent bridge state

- `1525-p0-review` task — Codex round-1 + round-2 complete. Thread can be re-read: `.venv/bin/python scripts/ai_agent_bridge/__main__.py conversation 433 434 435` or load messages 432-435 individually.
- `architecture` channel — thread `8aaa5760a2814e1192dac1b61b1b4098` (ADR-007 revisit discussion). Still readable via `ab channel tail architecture --thread 8aaa5760a2814e1192dac1b61b1b4098`.

## Context accounting

- Start of session: fresh (~60K after cold start / orient)
- Peak (handoff write): ~400K estimated
- No /compact used, no --resume. Diary handoff is the pattern.
- If the next session sees `--continue`/`--resume` offered: decline per MEMORY #2.

---

*Generated 2026-04-24 ~10:25 UTC. Commit `23ee12b0fc` on main. Build re-fire pending user action.*
