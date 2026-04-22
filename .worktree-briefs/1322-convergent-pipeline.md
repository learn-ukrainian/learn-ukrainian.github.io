# Claude Brief — #1322 Convergent pipeline — replace heal loop, eliminate needs-human-review.yaml

**Issue:** https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1322
**Task ID:** `claude-1322-convergent-pipeline`
**Worktree:** `.worktrees/claude-1322-convergent-pipeline`
**Branch:** `claude/claude-1322-convergent-pipeline`
**Effort:** xhigh
**Model:** claude-opus-4-7
**Hard timeout:** 7200s (this is the largest dispatch tonight — ~800 LOC + spec was 4 review rounds before approval)

## Why this matters

v6 build pipeline currently has a heal loop that can leave modules in a fake-autonomous dead-end (`needs-human-review.yaml`). User policy: every build must converge to `pass` OR one of two honest human-dependent terminals (`plan_revision_request`, `budget_exhausted`). No silent hangs.

**Tonight's broader context:** A1+A2 module rebuilds are about to start (waiting on #1410 wire-up). Without convergent termination, partial-failure modules pile up as `needs-human-review.yaml` artifacts and we can't tell if a slug is "build it more" or "fix the plan." Convergent pipeline makes the rebuild batch tractable.

## Worktree instructions (mandatory)

    git worktree add -b claude/claude-1322-convergent-pipeline .worktrees/claude-1322-convergent-pipeline
    cd .worktrees/claude-1322-convergent-pipeline

DO NOT branch in main checkout.

## Hard prohibitions

1. **DO NOT MERGE the PR yourself.** Open it only.
2. **DO NOT use `gh pr merge` / `--admin` / `gh pr review --approve` for any reason.**
3. **DO NOT skip the spec.** Per the issue body, the v4 spec at `/tmp/pipeline-convergence-spec-final.md` is approved. **Commit that spec to `docs/architecture/convergent-pipeline-spec.md` as your FIRST commit** before any code. If `/tmp/pipeline-convergence-spec-final.md` doesn't exist on this fresh worktree, recover the spec from issue history (PR comments, `ab channel tail` history, or message #323 referenced in the issue).
4. **DO NOT phase the delivery.** Issue says "everything together, single implementation pass, ~800 LOC." Don't split into 3 PRs.
5. **DO NOT skip the end-to-end adversarial review** before opening PR.
6. **DO NOT branch in main checkout.**

## Read before coding (mandatory)

- **Issue body in full** — https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1322 — has the spec link, ship scope, AC list, and reviewer history (v2 → v3 → v4).
- `/tmp/pipeline-convergence-spec-final.md` (if still on disk; if not, recover from issue + bridge channel history).
- Current heal loop in `scripts/build/v6_build.py` — find via `grep -n "heal\|needs_human_review\|needs-human-review" scripts/build/v6_build.py`.
- Current state contract — anywhere `state["needs_human_review"]` is set, read, or cleaned up. Per issue this is at 4 callsites.
- The motivating-case stuck module: `A1/M01 sounds-letters-and-hello`. Look at its current status JSON + last review YAML to understand the convergence-failure pattern.

## Acceptance criteria (from #1322)

- AC-1: All new modules implemented: `module_memory.py`, `finding_normalizer.py`, `finding_topology.py`, `convergence_loop.py`, `track_constraints.py`
- AC-2: `state["needs_human_review"]` contract migrated to `state["terminal"]` across all 4 callsites (emission, cleanup, contradiction checks, ...)
- AC-3: `needs-human-review.yaml` deleted entirely from the codebase + any docs referring to it as a real terminal updated
- AC-4: Stuck `A1/M01 sounds-letters-and-hello` builds to convergence under the new loop (`pass` OR honest terminal — no fake `needs_human_review`)
- AC-5: Tests cover the 4 callsite migration + the convergence loop's terminal classification
- AC-6: End-to-end adversarial review (Gemini) before PR. Run:

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini \
  "Adversarial review of #1322 convergent pipeline. Read the diff in full. Look for: (1) state['terminal'] semantics ambiguity — can two terminals coexist, what wins, (2) finding_topology / finding_normalizer collapsing distinct findings into one (loss of signal), (3) convergence_loop infinite loop under pathological reviewer outputs, (4) track_constraints introducing track-coupling that violates the existing track-agnostic contract, (5) module_memory persistence semantics (does it survive --resume vs --force), (6) deleted needs-human-review.yaml leaving orphan-state in batch_state/ that breaks Monitor API." \
  --task-id 1322-review --model gemini-3.1-pro-preview
```

Address findings. If any are blocking, do a second round. Document.

## Workflow

1. Create worktree per worktree instructions
2. Recover + commit the v4 spec FIRST (`docs/architecture/convergent-pipeline-spec.md`)
3. Read all "Read before coding" files
4. Implement everything in one pass per AC-1 through AC-5 (commits can be granular within the implementation pass; just don't ship as separate PRs)
5. Run AC-6 adversarial review, address findings
6. Push, open PR with title `feat(v6): convergent pipeline — replace heal loop with terminal classifier (#1322)`
7. STOP. Do not merge.

## PR body template

```
## Summary
v6 pipeline now converges to `pass` or one of two honest human-dependent terminals (`plan_revision_request`, `budget_exhausted`). `needs-human-review.yaml` deleted entirely; `state["needs_human_review"]` migrated to `state["terminal"]` across all callsites. Stuck `A1/M01 sounds-letters-and-hello` now reaches an honest terminal.

- AC-1: 5 new modules — module_memory, finding_normalizer, finding_topology, convergence_loop, track_constraints
- AC-2: 4 callsites migrated to state["terminal"] contract
- AC-3: needs-human-review.yaml deleted; doc references updated
- AC-4: A1/M01 verified converges
- AC-5: Tests cover migration + convergence classification
- AC-6: End-to-end adversarial review (Gemini, N rounds) — findings addressed

Spec: docs/architecture/convergent-pipeline-spec.md (committed first per #1322 protocol).

Closes #1322.

## Test plan
- [ ] `.venv/bin/pytest tests/test_convergence*.py tests/test_module_memory*.py tests/test_finding_*.py tests/test_track_constraints*.py -v` — all green
- [ ] `.venv/bin/python scripts/build/v6_build.py a1 1 --resume` on sounds-letters-and-hello — terminates at honest state, not needs-human-review
- [ ] `grep -rn "needs.human.review\|needs_human_review" scripts/ docs/` returns only deletion-context references

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## Done when

PR opened, spec committed, all 6 ACs documented, adversarial review noted (possibly multi-round), dispatch reports `done`. User reviews + merges.
