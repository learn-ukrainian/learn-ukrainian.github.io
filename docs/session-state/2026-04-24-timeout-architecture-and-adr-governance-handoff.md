# Session Handoff — 2026-04-24 ~07:50 UTC: timeout architecture + ADR governance

> **TL;DR** Session ran from ADR-007 / FTS5 cleanup (start-of-day) through
> pilot-blocker debugging to governance tooling. Net: timeout architecture
> clarified (ADR-009 codifies the "hard_timeout is a leak guard, not a
> productivity heuristic" principle), ADR governance now has enforcement,
> and 2 Codex dispatches are in flight. Context at handoff: ~410K.
>
> **Two Codex PRs pending review:**
> - `codex-1520-liveness-probe-phase1` — composite liveness probe substrate (#1520 Phase 1)
> - `codex-1519-git-hygiene-endpoint` — /api/git/hygiene Monitor API endpoint
>
> **Pilot fire is USER-FIRED, still pending.** Build infrastructure is healthy but the a1/sounds-letters-and-hello pilot hasn't been re-fired since the plan-stress-mark fix + the 24h timeout unification. When user re-fires: `.venv/bin/python scripts/build/v6_build.py a1 1 --writer claude-tools --reviewer codex-tools`.

---

## What shipped this session (newest first, all on main)

| Commit | Subject | Notes |
|---|---|---|
| `ad6592b074` | `feat(adr-management)` — automation + ADR-009 + best-practices doc | `scripts/audit/check_adrs.py`, `docs/best-practices/adr-management.md`, ADR-009 on timeout design, SessionStart hook wiring |
| `fa8b4ee0c1` | `refactor(timeouts)` — unify all LLM-dispatch hard_timeouts to 24h | Four files, three hidden caps removed (`_gemini_per_rung_timeout`, `CASCADE_PER_CALL_MAX_S`, `effective_timeout` default). Codex + Gemini reviewed via `ab discuss` thread `0f94b8c0`. |
| `1029a66f0d` | `fix(plans)` — strip U+0301 stress marks from 6 contaminated plans | 85 marks total. Version-bumped + .yaml.bak snapshots per immutability hook. Also removed erroneous `.yaml.bak` gitignore line I'd let through in phase-1 hygiene commit. |
| `925a53af89` | `fix(skeleton)` — use thinking model + timeout bump | Superseded by `fa8b4ee0c1` (24h unification) but kept in history for the diagnostic reasoning. |
| `1091f94126` | `feat(git-hygiene)` — policy doc + SessionStart hook + MEMORY.md trim | Three layers: `docs/best-practices/git-hygiene.md`, hook step 12, MEMORY.md 281→168 lines. |
| `0c9ef14654` | `feat(wiki)` — incremental wiki snapshot batch 2 | Second parallel-build snapshot. |
| `c5678251e5` | `chore(curriculum)` — reset a1/colors artifacts to unbuilt state | 99 stale files removed; slug still in manifest, regenerates on next build. |
| `3aa5880304` | `chore(git)` — gitignore .worktree-briefs/ + clean 43 historical briefs | Layer 1 of git-hygiene plan. |
| `e662904a89` | `feat(wiki)` — snapshot built wikis batch 2026-04-24 (768 files) | First parallel-build snapshot. |
| `ce8d9d5485` | `fix(alignment-manifest)` — exclude FTS5 shadow tables (#1517 → #1518) | First pilot-block fix of the day. |
| `a1191de03c` | `fix(tests)` — gpt-5.4 → gpt-5.5 post-migration | Direct-to-main; main-breaking test. |

**13 commits. 3 PRs merged. 0 dirty files at handoff (modulo the user's active pilot-build churn in `curriculum/l2-uk-en/a1/sounds-letters-and-hello*`, which is exempt).**

---

## Issues filed this session

| # | Title | Status |
|---|---|---|
| #1517 | FTS5 shadow-table crash on sources_hash | closed via #1518 |
| #1519 | Monitor API /api/git/hygiene endpoint | **open, Codex dispatching** |
| #1520 | EPIC: Composite K8s-style liveness probes | open, Phase 1 Codex dispatching |
| #1521 | (skipped — not in our sequence) | — |
| #1522 | Governance: postmortem management | open, follow-up |
| #1523 | Monitor API /api/state/governance endpoint | open, follow-up |

---

## Active Codex dispatches (as of handoff)

```
codex-1519-git-hygiene-endpoint   running   started 2026-04-24T07:47:00Z
codex-1520-liveness-probe-phase1  running   started 2026-04-24T07:46:59Z
```

Brief files: `.worktree-briefs/codex-1519-git-hygiene-endpoint.md` and `codex-1520-liveness-probe-phase1.md` (both gitignored per policy, written for the dispatchers).

**Next session MUST** triage these PRs on arrival:
1. Verify branch-base freshness (`git fetch origin main && git log HEAD..origin/main` — must be empty)
2. Read PR body + diff
3. Run tests locally in the worktree
4. Inline adversarial review (Gemini Code Assist quota was out last session — do it myself)
5. Merge if clean (`gh pr merge N --squash --delete-branch`)
6. Remove worktree + local branch

---

## Architecture change that needs permanent awareness: ADR-009

**Read `docs/architecture/adr/adr-009-dispatch-timeout-unification-and-liveness.md`** before touching anything in `scripts/agent_runtime/`, `scripts/ai_llm/fallback.py`, or `scripts/batch/batch_gemini_config.py`.

Summary: all LLM-dispatch `hard_timeout` values are now `_ONE_DAY` (86400s). This is intentional — hard_timeout is a leak guard, not a phase-duration tuning knob. Kill decisions for productive LLM work belong to external observability (Monitor tool on JSONL events, `/api/delegate/active`, per-CLI session files).

**If you find yourself tempted to set a shorter timeout for some phase, STOP.** Read ADR-009 and bridge thread `0f94b8c0`. The only legitimate sub-24h timeout is `TIMEOUT_REVIEW_GEMINI_PROBE = 300` which is a genuine liveness probe.

**Future replacement: #1520 EPIC** — K8s-style composite liveness probes. Phase 1 (signal primitives) is mid-flight via Codex. Phases 2-4 (watchdog integration, per-CLI probe descriptors, Monitor API surface) land separately.

---

## Governance surfaces now active

Three governance automation surfaces, same pattern each time:

| Surface | Script | SessionStart step | Policy doc |
|---|---|---|---|
| Decisions (ephemeral, expiring) | `scripts/check_decisions.py` | step 10 | `docs/decisions/INDEX.md` (established) |
| ADRs (permanent) | `scripts/audit/check_adrs.py` | step 10b (**new**) | `docs/best-practices/adr-management.md` (**new**) |
| Git hygiene (dirty-tree) | inline in session-setup.sh | step 12 | `docs/best-practices/git-hygiene.md` |
| Postmortems | (**pending #1522**) | — | (**pending #1522**) |

`check_adrs.py` flags errors (blocking) + warnings (advisory). Currently surfaces 6 historical ADRs (001-006) missing `Deciders` field as warnings — acceptable, predate the convention.

`--rebuild-index` regenerates the README table between sentinel comments. Pre-commit + manual use.

`--check-promotions` flags active decisions past 180 days as ADR candidates.

---

## Pipeline state (NOT work-status, just metrics)

| Track | Total | Wiki compiled | Content done |
|---|---|---|---|
| a1 | 55 | 100% | 1 (pre-ADR-007) |
| a2 | 69 | 100% | 0 |
| b1 | 94 | 100% | 0 |
| b2 | 93 | 78% | 0 |
| c1 | 133 | 83% | 0 |
| c2 | 110 | 0% | 0 |
| hist | 140 | 2.9% | 0 |
| bio | 180 | 67% | 0 |
| other seminars | — | low | 0 |

User mentioned wikis "actively being built in parallel" — source of 769+ `wiki/**` commits this session. Two snapshot commits: `e662904a89` (768 files) + `0c9ef14654` (5 files).

---

## Open issues that did NOT get addressed this session

| # | Title | Why not |
|---|---|---|
| #1481 | Targeted test selection on PRs | Low priority; Codex slots occupied |
| #1480 | Local Docker-pytest CI-parity | Same |
| #1451 | EPIC Alignment-Pipeline Runtime Contracts | Umbrella; per-phase work landed instead |
| #1435 | Backfill source attribution across 227 wikis | User's parallel build will affect this; defer |
| #1398 | Wire --effort for Gemini | Blocked on gemini-cli exposing flag |
| #1395 | /api/git/cleanup endpoint | Deferred in favor of #1519 |
| #1377 | Wiki corpus expansion | User-executed, running in background |
| #1373 | A.6 ingest 55 A1 wikis to sources.db | Codex-assigned, not fired yet |
| #1365 | EPIC: Two-track build rollout | Meta |
| #1351 | Rank-order diagnostic test for CEFR retrieval | Low priority |
| #1316 | Early-literacy review calibration | May surface when the a1 pilot review fires — triage then |

---

## Plan-check completeness bug (NOTED BUT NOT FIXED)

When the a1 plan failed CHECK at step 2 this session, the error said "found in: vocabulary_hints, content_outline" but stress marks were actually in 4 fields (also `activity_hints`, `grammar`). The check is under-reporting which fields can have the issue.

This is a real bug in `scripts/audit/checks/*` or `scripts/build/phases/plan_contract.py` — haven't located the exact check yet. Low-urgency (fix was applied without knowing full scope, all 6 plans now clean). File as issue next session if time allows.

---

## MEMORY.md status

Trimmed from 281 → 168 lines this session. Under the 200 hard limit, slightly over the 150 soft budget. Two sections extracted to sibling topic files:
- `memory/gpt-5.5-rollout.md`
- `memory/agent-debug.md`

Session-setup hook reports as INFO (not ISSUE) because we're under 200.

---

## What the next session should do (priority order)

1. **Run orientation** via `curl -s http://localhost:8765/api/orient` (don't read CLAUDE.md directly). Check `/api/comms/inbox?agent=claude` for any messages from the Codex dispatches.
2. **Check on the two Codex PRs** from this session (grep `gh pr list --author @me` for `codex-1519-git-hygiene-endpoint` and `codex-1520-liveness-probe-phase1`). Review + merge if clean.
3. **If user re-fires the pilot** (or has results from it) → triage per the Monitor event stream.
4. **If nothing above is actionable**, pick from open issues. Candidates: #1480 (Docker-pytest), #1481 (testmon), #1522 (postmortem governance — mirrors the ADR work just shipped, clean pattern to replicate).

---

## Things NOT to do

- **Do not set phase-specific timeouts < 24h.** Read ADR-009 first. If you think there's a reason, it's wrong — one of the 3 hidden caps that Codex + Gemini already caught.
- **Do not touch `wiki/**` or `curriculum/l2-uk-en/a1/sounds-letters-and-hello*`.** Both active user-side work (wiki build + pilot).
- **Do not file new Monitor API endpoints** before considering consolidation with #1523 (governance). User explicitly pushed back on endpoint sprawl.
- **Do not ask "should I merge?"** Memory #0H — merging is my job after review.

---

## Context accounting

- Start of session: fresh (~60K after cold start)
- Peak (handoff write): ~410K
- User gave 20-minute heads-up to prep handoff; landing well within that
- No /compact used, no --resume. Fresh next session + this diary handoff is the pattern per MEMORY.md.

---

*Generated 2026-04-24 ~07:50 UTC. Two Codex PRs pending arrival; everything else clean. `git status` shows only user's active pilot-build churn (exempt per git-hygiene policy).*
