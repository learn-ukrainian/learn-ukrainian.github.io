# Repo Cleanup Plan — 2026 Q2

> **Status:** PROPOSED, awaiting Phase 0 completion before Phase 1 kicks off.
> **Anchor issue:** filed as the epic-tracker, see issue with title `[EPIC] Repo cleanup — stale code + obsolete docs sprint`.
> **Last updated:** 2026-05-10
> **Owner:** orchestrator (Claude) for Phases 0-2; dispatched per-category for Phase 3.

## Why this plan exists

The repo accumulated significant litter through V5→V6→V7 transitions, multiple rename attempts, and orchestration experiments. The recent record proves ad-hoc cleanup is **high risk** on this codebase:

| Attempt | Outcome |
|---|---|
| `f4bab7125f` (chore: repository cleanup) | Broke 14 tests — moved files out of `audit/` without updating `ALLOWED_ROOTS`, missed call sites in 4+ Python files |
| `ae987beaf8` (docs: align documentation) | Renamed `PLAYGROUNDS_DIR` → `DASHBOARDS_DIR` in config but missed callers in `scripts/api/main.py` and 14 test sites |
| PR #1862 (Gemini's playground→dashboards refactor) | 10 critical findings: didn't fix the 14 broken tests, hallucinated 250 LoC of `IMMERSION_POLICIES` disguised as "config", broke `delegate.py` worktree symlinks, vandalized A1 curriculum metadata, committed a 60KB `.bak` file. CLOSED. |

The pattern: this codebase has many lateral connections (imports across script boundaries, tests that walk filesystem paths, hardcoded references in MDX files, prompt templates referencing build paths). "Delete what looks unused" approaches fail because what *looks* unused often has a hidden caller.

**Conclusion:** cleanup must be **tooling-first**, **one-category-per-PR**, and **adversarial-review-mandatory**.

## Scope — 10 categories

Inventory categorized by risk profile. Each row becomes a separate PR (or a small batch of related PRs) in Phase 3, never bundled across categories.

| # | Category | Risk | Examples (illustrative, NOT exhaustive) | Detection method |
|---|---|---|---|---|
| **A** | Marked-obsolete code | M | `scripts/build/v5_build.py`, `v6_build.py`, `pipeline_v5.py` (have OBSOLETE banner per #1853) | grep for OBSOLETE banner; check for live callers |
| **B** | Dead Python modules | L | Functions/classes with zero in-repo callers | `vulture` ≥80% confidence + manual triage |
| **C** | Stale docs | L (if no broken links) | `docs/RUNBOOK-BUILD.md` entirely V6; `docs/WORKSTREAMS.md` V6 sections; `docs/lesson-schema-design.md` V6 mentions | grep `v6_build`/`pipeline_v5` outside autopsies + session-state |
| **D** | Generated artifacts that escaped | L | `*.bak` files, `.coverage`, orphan `audit/*-review.md` that shouldn't be tracked | git ls-files + extension grep + .gitignore audit |
| **E** | Old session-state archive | L | `docs/session-state/*.md/*.html` from >30 days ago (move to `docs/session-state/archive/`) | mtime sort + handoff-index reconcile |
| **F** | Orphaned orchestration artifacts | M | Per-module orchestration dirs from failed/superseded builds | filesystem scan + cross-ref against `status.json` |
| **G** | Duplicate files from incomplete renames | **H** | `scripts/build_dashboards.py` AND `scripts/build/build_dashboards.py`; same for `generate_dashboard_data.py` | exact-name collisions across `scripts/` |
| **H** | Stale `experiments/` content | L | `experiments/phase-4/round-3.5/` preserved as evidence | git log last-meaningful-access |
| **I** | Old audit JSONs | M | Pre-V7 audit JSONs that may not match current schema | schema validate + age sort |
| **J** | Stale test fixtures | **H** | Tests for deleted features that pass vacuously (untested code paths look "covered") | coverage report + manual review |

**Risk legend:** L = safe with grep-level review; M = needs adversarial review (a second agent reads the PR); H = needs adversarial review + smoke build + manual sanity check.

**Total scope guess:** several hundred files, ~5-15K LoC removable. Far too big for one PR.

## Phased timeline

### Phase 0 — Stabilize main (in flight, ~2026-05-10 evening)

- Codex dispatch `codex-dashboards-rename` (in progress) completes the playgrounds→dashboards rename
- Main back to all-green (14 currently-failing tests pass)
- Unblocks any future Python PR (currently every code PR hits the same 14 failures)

**Exit criterion:** `Test (pytest)` green on a code-touching PR.

### Phase 1 — Build the inventory tool (1 dedicated half-day, orchestrator inline)

Build `scripts/audit/find_dead_code.py`:

- Run `vulture` for unused Python (confidence ≥80%)
- `ugrep -rn` for symbols outside `tests/`, `scripts/`, `dashboards/`
- Filesystem orphan scan (files no commit touched in >90 days AND nothing imports/references)
- Cross-ref against `git ls-files` to find tracked-but-orphaned files
- Output structured report to `audit/cleanup-inventory-YYYY-MM-DD.md` with per-category buckets
- Recurring tool — designed to be re-run quarterly, not single-use

**Exit criterion:** tool runs, produces a report with concrete `file:line` hits in each of the 10 categories.

### Phase 2 — Inventory + decisions (~1 hour orchestrator work)

- Run the tool
- Triage output into PASS / REVIEW / KEEP buckets
- Batch REVIEW items into the 10 categories
- Per-category policy decisions (delete vs archive-first vs leave)
- File the per-category sub-issues NOW (just-in-time, not earlier)

**Exit criterion:** 10 categorized sub-issues filed under the epic, each with a concrete file list + proposed PR scope.

### Phase 3 — Cleanup sprint (1 weekend OR a 1-2 day window with NO concurrent feature work)

- One PR per category. Title format: `cleanup(<category>): <what>`
- Parallel dispatches OK by category fit:
  - **Codex** → Categories B (dead Python), G (duplicates), J (stale fixtures) — mechanical + security-relevant
  - **Gemini** → Categories C (stale docs), E (session-state archive), H (`experiments/`) — docs-near-code
  - **Claude inline** → Category A (marked-obsolete code, needs context), I (audit JSONs, schema-aware)
  - **Claude headless adversarial** → reviews each PR before merge
- 3-agent quorum review on each PR — afternoon-shift's validated pattern for refactors >30 LoC

**Exit criterion:** all 10 sub-issues closed, main green throughout.

### Phase 4 — Archive grace period (1 quarter)

- Items deleted go to `archive/YYYY-MM-DD-cleanup-N/` first, NOT `git rm`
- Reversibility budget: anything missed in this quarter can be restored with one `git mv`
- After 1 quarter (= ~2026-Q3), nothing has resurfaced from any category → safe to hard-delete

**Exit criterion:** calendar date reached, no resurrection requests pending.

### Phase 5 — Hard delete (calendar-driven)

- `git rm` from `archive/` in a single audit-trail PR per cleanup batch
- Quarterly recurring cleanup runs scheduled going forward (tool from Phase 1 re-runs automatically)

**Exit criterion:** the work becomes routine maintenance, not a special project.

## Critical rules for cleanup PRs (LESSONS PAID FOR)

These rules are not suggestions — each one was paid for by a real incident in the historical record above.

1. **One category per PR.** Mixing "remove v6" with "stale docs" = unreviewable = something gets missed.
2. **Adversarial review mandatory.** Every cleanup PR gets a second-agent review BEFORE merge. Solo cleanups are how curriculum metadata gets vandalized (#1862 §6).
3. **No "while I'm here" scope expansion.** The brief defines scope. ANY out-of-scope change = REJECT. #1862 was 22 files for an 8-file task.
4. **Archive before delete.** Move to `archive/YYYY-MM-DD-cleanup-N/` first. Hard `git rm` is a follow-up PR after grace period.
5. **Run tests AND smoke build before merge.** Tests catch import breaks; smoke build catches MDX/template/Astro breaks that pytest misses.
6. **NEVER touch curriculum content in a cleanup PR.** Curriculum changes need a dedicated content-review pass with VESUM verification.
7. **`.bak`, `.coverage`, build outputs NEVER get committed.** Pre-commit hook should catch these; if it doesn't, audit the hook (#1862 shipped a 60KB `.bak`).
8. **Top-of-file invariants are sacred.** Shebangs on line 1. Module docstrings before imports. `__future__` imports first. Mechanical refactors that disturb these = REJECT (#1862 §4).
9. **Path constants vs path strings — know the difference.** `Path("/a") / Path("/b")` discards `/a`. Renaming string literals to absolute Path constants without checking call sites is a #1862 §3-class bug.

## Dispatch routing per category (Phase 3 guidance)

When Phase 3 starts, route per #M0 + category fit:

| Category | Best agent | Why |
|---|---|---|
| A — Marked-obsolete code | Claude inline | Needs project context (which v6 paths are referenced where, what autopsies preserve) |
| B — Dead Python modules | Codex | Mechanical pattern-matching |
| C — Stale docs | Gemini | Docs-near-code, semantic judgment about what's stale vs forensic |
| D — Generated artifacts | Codex | Mechanical gitignore + git ls-files diff |
| E — Old session-state | Gemini | Docs-near-code, low risk |
| F — Orphaned orchestration | Claude inline | Needs cross-ref against status.json — schema-aware |
| G — Duplicate file pairs | **Claude inline + adversarial Codex review** | High risk — both files might have unique logic |
| H — Stale `experiments/` | Gemini | Low risk, docs-adjacent |
| I — Old audit JSONs | Claude inline | Schema-aware |
| J — Stale test fixtures | **Codex with mandatory coverage report** | High risk — fixtures may exercise paths nothing else covers |

## What is OUT OF SCOPE for this plan

To prevent scope creep within the cleanup plan itself:

- **Curriculum content cleanup** — separate workstream, needs pedagogical review
- **Plan files (`plans/`)** — version-locked, owned by content track
- **Dependency upgrades** — `#1634` lockfile resolver migration is the canonical thread; do not bundle
- **CI/CD workflow refactors** — covered by PR-C deferred (`gemini-dispatch.yml` router job)
- **Schema migrations** — covered by ADR-008 implementation thread (`#1632`)
- **MEMORY rule trimming** — recurring orchestrator hygiene, not a cleanup-sprint concern

## Reading list (auto-loaded context for any agent picking this up)

- `memory/MEMORY.md` — #M0 model assignment, #M-4 deterministic-over-hallucination
- `claude_extensions/rules/non-negotiable-rules.md` — pre-submit checklist
- `claude_extensions/rules/delegate-must-use-worktree.md` — every dispatch in worktree
- This document
- The closed PR #1862 review at `https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/1862#issuecomment-4416372755` — canonical anti-pattern reference
