# Writer Bakeoff Methodology

**Status:** SPECIFICATION.
**Date:** 2026-05-19
**Scope:** Fair multi-writer bakeoffs for the V7 single-module pipeline.
**Source:** `audit/2026-05-18-docs-gaps-and-reorganization/REPORT.md` gap
§1.2 and the locked handoff
`docs/session-state/2026-05-19-handoff-gap-audit-and-qwen-integration.md`.

---

## Why This Doc Exists

The agent activity matrix already records bakeoff outcomes. It does not define a
methodology for running a fair bakeoff.

The 2026-05-18 gap audit names the missing spec directly: the matrix has a table
of past bakeoff outcomes, but no methodology document. This file is the
canonical method for future writer bakeoffs.

Past bakeoffs remain useful evidence. They are not automatically reusable as
methodology. A result table answers "what happened in that run." A methodology
answers "what conditions make a result fair enough to update routing policy."

The V7 writer choice is now a high-leverage routing decision because the current
A1 writer lane sunsets on 2026-06-15. The cost difference between writers is
large enough to matter, but quality remains first. This methodology keeps those
two pressures in the right order: measure quality deterministically first, then
normalize cost per passing module.

---

## What A Fair Test Requires

A V7 writer bakeoff is fair only when these inputs are identical across writers:

| Surface | Requirement |
| --- | --- |
| Prompt | Same rendered writer prompt, except for adapter-required invocation wrapper. |
| Module | Same `{level}/{slug}` and same source plan. |
| MCP config | Same source server availability and same retrieval namespace. |
| Effort tier | Same reasoning effort tier when the adapter exposes one. |
| Worktree | Separate worktree per writer. |
| Pipeline code | Same base commit. |
| Scoring | Same deterministic prompt-fidelity rubric. |

Separate worktrees are required because V7 builds write multiple artifacts:
`module.md`, `activities.yaml`, `vocabulary.yaml`, `resources.yaml`, gate JSON,
tool traces, and MDX. A shared worktree lets one writer's artifacts contaminate
another writer's run.

Do not compare a run made before a pipeline bug fix with a run made after that
fix as if they were the same condition. If the code changes, restart the bakeoff
or split the report into separate cohorts.

> **In-flight contract change (#2148 γ-shape).** The decision card at
> [`docs/decisions/pending/2026-05-18-wiki-obligation-emission-contract.md`](../../decisions/pending/2026-05-18-wiki-obligation-emission-contract.md)
> would render `implementation_map.json` into the writer prompt as a new
> `IMPLEMENTATION_MAP_CONTRACT` block. If γ lands before a planned bakeoff,
> treat all writers' prior runs as a different cohort. Include a baseline
> run of the current default writer (claude-tools) on the post-γ prompt as
> the new control — every other writer's first test is against the new
> prompt by default.

---

## Per-Level Scope Rule

A1 results do not transfer to B1+.

The matrix states the reason: A1 is register-precision work with heavy English
scaffold and ULP-derived immersion constraints. B1+ is register-relaxed by
comparison because Ukrainian density rises sharply and the writer's high-UK bias
can become an advantage.

Default rule:

| Target routing decision | Required evidence |
| --- | --- |
| A1 writer routing | A1 bakeoff. |
| A2 transition routing | A2 bakeoff, or A1 evidence explicitly accepted as temporary. |
| B1/B2 core routing | B1+ bakeoff. |
| C1/C2 advanced routing | Advanced-core bakeoff, unless B1+ evidence is explicitly accepted as proxy. |
| Seminar routing | Track-bucket canary bakeoff for the seminar class. |

A single A1 bakeoff never licenses a B1+ ranking. A single B1+ bakeoff never
licenses a literary, history, biography, paleography, or folklore seminar
ranking.

---

## Writer Roster

Current roster as of 2026-05-19:

| Writer | Status for V7 writer bakeoffs |
| --- | --- |
| `claude-tools` | Current A1 writer default; lane ends 2026-06-15. |
| `codex-tools` | Tool wiring confirmed; A1 register gap remains the known weakness. |
| `gemini-tools` | Primary for wiki writing; V7 module writer needs re-bakeoff. |
| `deepseek-tools` | Pending V7 writer wiring; DeepSeek adapter and write-mode dispatch evidence exist in the repo history. |
| `kimi` | Excluded per user direction 2026-05-18. |
| `qwen-tools` | Qwen-3.6-plus default; Qwen-3.6-flash, Qwen-3.6-max-preview, and Qwen-3.6-35b-a3b:thinking variants are available for role bakeoffs. |
| `grok-tools` | Known weak as writer; issue #2039 records under-target output and token truncation. |

Do not silently add a writer to the roster. Adding a writer changes cost, runtime,
and interpretation of the report. Update the dispatch brief and the report scope
before running.

Do not silently remove a writer from the roster. If a writer is excluded because
it is unavailable, unwired, over budget, or intentionally out of scope, record
that as an exclusion in the report.

---

## Current State Reference

The matrix is the current routing source of truth. This methodology explains how
to update it.

From matrix §8.1, the current A1 writer ranking says:

> `claude-tools`: "Default. 1224 words / 4 MCP / VESUM 159/159. Lane ends 2026-06-15."

> `codex-tools`: "Tools confirmed (11 calls). Content register gap: 996/1200, 51% immersion. Underperforms at A1."

> `grok-tools`: "52% word count + truncation per #2039. Probably out."

From matrix §8.10:

> "DeepSeek has earned primary slots on quality, not just cost. Qwen integration just landed; needs role-specific bakeoffs to know if it earns slots or stays runner-up."

From matrix §8.11:

> "Writer rankings do not transfer across registers"

and:

> "Total bakeoff cost to close all current slots: **~$50-80** spread across 5 dispatches."

The source matrix uses validation glyphs. This methodology normalizes them to
words in order to keep new specs glyph-free while preserving the routing
meaning:

| Matrix meaning | This doc's wording |
| --- | --- |
| empirical bakeoff data | validated |
| gut-routing or limited data | limited data |
| no bakeoff, needs validation | pending verification |
| excluded | excluded |

---

## Measurement Schema

The deterministic prompt-fidelity rubric is quoted from the 2026-05-19 handoff:

> **Prompt-fidelity rubric (deterministic, no LLM judge):**
> - Word count within ±50 of target
> - All 4 sections in band
> - Lands within derived immersion band (`compute_immersion_band()`)
> - ≥4 MCP tool calls
> - VESUM 100% (no invented forms)
> - `unknown_vocabulary` gate: 0 violations
> - `<!-- bad -->` marker discipline: 100%
> - Implementation map completeness: 100%

The rubric is deterministic by design. Do not replace it with an LLM judge.

Scoring rules:

| Rubric item | Deterministic source |
| --- | --- |
| Word count within target band | Module word-count gate output or deterministic counter. |
| All four sections in band | Section-budget parser and plan outline. |
| Derived immersion band | `compute_immersion_band()` output and immersion gates. |
| MCP tool calls | Writer telemetry / tool trace. |
| VESUM 100% | VESUM gate output. |
| `unknown_vocabulary` 0 | Learner-state vocabulary gate output. |
| Negative-example marker discipline | Markdown/YAML marker scan. |
| Implementation map completeness | `implementation_map.json` and wiki coverage gate output. |

The first-pass score is strict: a writer either passes all rubric items on the
first pipeline pass, or it does not. Correction behavior is tracked separately.

---

## Cost Normalization

Normalize cost as dollars per passing module.

For each writer:

```text
cost_per_passing_module = total_writer_cost / first_pass_modules_passing_rubric
```

If a writer has zero first-pass passes, do not compute a misleading dollar
ratio. Mark the cost result as `no passing module` and record raw cost.

Bakeoff total cost is:

```text
sum(per_writer_module_costs)
```

Quality verdict is:

```text
first_pass_pass_rate_against_rubric
```

Correction passes do not count toward the first-pass score. They are reported as
a separate `correction_responsiveness` sub-score:

| Sub-score | Meaning |
| --- | --- |
| `not_attempted` | No correction phase ran. |
| `converged` | Correction made the module pass without regressing prior gates. |
| `regressed` | Correction broke a previously passing gate. |
| `terminal` | Correction hit a structured terminal. |

This split prevents a writer that needs repeated rescue from tying a writer that
passes the rubric on the first attempt.

---

## Cost Reality Check

The 2026-05-19 handoff corrects prior cost estimates:

> **Cost reality check:** Earlier session estimates ($20-50 per round) were 5-10× too high. Actual:
> - A1 m20 6-writer bakeoff: ~$6-15 total
> - Plus DeepSeek wiring dispatch: ~$3-5
> - **Total to answer "which writer for A1, including Chinese models" empirically: ~$10-20**

The matrix separately estimates the full table-population cost:

> "Total bakeoff cost to close all current slots: **~$50-80** spread across 5 dispatches."

Use the handoff number for the A1 m20 6-writer bakeoff. Use the matrix number
for closing the current §8.11 routing table.

Do not invent new thresholds or budget bands in this document. Config thresholds
belong in the pipeline and audit config files. Reports may include observed cost
from actual runs.

---

## When To Bakeoff

Run a bakeoff when any of these is true:

| Trigger | Rule |
| --- | --- |
| Stale evidence | `last_verified` is more than 60 days old for the role being used. |
| New target register | Writer has never been tested in the target register. |
| New adapter wiring | Writer adapter or MCP configuration changed materially. |
| Pipeline bug fix | A scoring-relevant pipeline bug changed the conditions. |
| Routing promotion | A writer is about to become primary for a track bucket. |
| Sunset pressure | A current primary lane is ending and no validated replacement exists. |

Target-register examples:

- A1 register-precision.
- B1+ register-relaxed core.
- Seminar narrative.
- Seminar decolonization-sensitive history.
- Literary essay.
- Paleography / Ruthenian source handling.

Otherwise, trust the matrix. Do not re-run bakeoffs as routine ceremony when the
current cell is recent, target-register-matched, and backed by deterministic
evidence.

---

## Bakeoff Lifecycle

1. Dispatch all writers in parallel worktrees, within the active agent cap.
2. Wait for every writer to finalize by monitoring per-task JSONL.
3. Score deterministically against the prompt-fidelity rubric.
4. Write the report at `audit/bakeoff-{date}-{scope}/REPORT.md`.
5. Update `docs/best-practices/agent-activity-matrix.md` with `last_verified`
   and quality status cells.
6. Close the open evaluation row in §7 of the matrix if the bakeoff was queued
   there.

The report must include:

| Report field | Required content |
| --- | --- |
| Scope | Target level, slug, writers, models, effort tiers, base commit. |
| Prompt identity | Rendered prompt hash or archived prompt path per writer. |
| MCP identity | Config source and server availability. |
| Worktrees | Worktree path per writer. |
| First-pass table | One row per writer per rubric item. |
| Correction table | Correction responsiveness, separate from first-pass score. |
| Cost table | Raw cost and cost per passing module. |
| Decision | Matrix update or explicit no-change. |
| Exclusions | Any writer omitted from the expected roster and why. |

The report may include qualitative notes, but qualitative notes do not override
the deterministic rubric.

---

## Valid And Invalid Comparisons

Valid:

- Same module, same prompt, same MCP config, same effort tier, separate
  worktrees.
- Same writer roster across all first-pass runs.
- Deterministic rubric applied to archived artifacts.
- Cost normalized after pass/fail is known.
- Correction responsiveness tracked separately.

Invalid:

- Different prompts across writers.
- Different MCP config across writers.
- Different `model_reasoning_effort` settings when the adapter supports effort.
- Comparing a pre-bug-fix run with a post-bug-fix run as if equivalent.
- LLM judge as the primary verdict.
- Counting correction-pass success as first-pass success.
- Letting one writer reuse another writer's worktree or artifacts.
- Updating the matrix from an unarchived run with missing prompt or telemetry.

---

## Anti-Patterns

### Minimal Prompt Theater

A "minimal prompt" test is not fair if the production pipeline uses a richer
rendered prompt. Use the actual V7 prompt unless the report explicitly asks a
separate research question about prompt sensitivity.

### Per-Writer Prompt Tuning Hidden As Fairness

Per-writer tuned variants can be useful, but they are a different bakeoff mode.
Do not compare writer A with a tuned prompt against writer B with the baseline
prompt and call the result a fair baseline bakeoff.

### Judge-First Scoring

An LLM judge can help explain why a deterministic score happened. It cannot be
the primary verdict for the rubric. The rubric was chosen because the pass/fail
items are machine-checkable.

### Cost-First Promotion

Do not promote a cheaper writer until it meets the quality bar for the target
register. Cost only breaks ties among passing writers or informs whether a
runner-up deserves more testing.

### A1 Overgeneralization

Do not carry A1 rankings to B1+ without a B1+ test. The source matrix says
register inversion can change the ranking.

---

## Open Implementation Notes

The bakeoff runner already has pieces of this methodology, but this doc is the
policy source:

- `scripts/audit/bakeoff_run.py` has a default writer set.
- `scripts/audit/bakeoff_aggregate.py` includes prompt-adherence aggregation.
- The matrix is the routing record.
- V7 run preservation is specified separately in
  [`v7-build-preservation.md`](v7-build-preservation.md).

When the preservation layer ships, bakeoff reports should reference archived run
directories instead of ad hoc artifact folders.

---

## Verification Evidence

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: nl -ba audit/2026-05-18-docs-gaps-and-reorganization/REPORT.md | sed -n '20,70p'
raw: 45  ### 1.2 — Multi-writer fairness bakeoff methodology
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: nl -ba docs/session-state/2026-05-19-handoff-gap-audit-and-qwen-integration.md | sed -n '52,151p'
raw: 122  ### Bakeoff plan for next session
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: nl -ba docs/session-state/2026-05-19-handoff-gap-audit-and-qwen-integration.md | sed -n '52,151p'
raw: 129  **Cost reality check:** Earlier session estimates ($20-50 per round) were 5-10× too high. Actual:
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: nl -ba docs/session-state/2026-05-19-handoff-gap-audit-and-qwen-integration.md | sed -n '52,151p'
raw: 134  **Prompt-fidelity rubric (deterministic, no LLM judge):**
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: nl -ba docs/best-practices/agent-activity-matrix.md | sed -n '268,286p'
raw: 272  ### 8.1 V7 module writer (A1 register-precision; B1+ register-relaxed)
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: nl -ba docs/best-practices/agent-activity-matrix.md | sed -n '364,385p'
raw: 377  **Honest take:** DeepSeek has earned primary slots on quality, not just cost. Qwen integration just landed; needs role-specific bakeoffs to know if it earns slots or stays runner-up.
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: nl -ba docs/best-practices/agent-activity-matrix.md | sed -n '387,427p'
raw: 387  ### 8.11 Track-level V7 writer routing — STUBBED, pending bakeoff (added v1.2.1 / 2026-05-18)
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: gh issue view 2039 --json number,title,state,url
raw: {"number":2039,"state":"OPEN","title":"[v7/writer] grok-tools writer produces under-target module.md (~52% of word count) + token-truncation artifact","url":"https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/2039"}
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: gh pr view 2107 --json number,title,state,mergedAt,url
raw: {"mergedAt":"2026-05-17T20:03:50Z","number":2107,"state":"MERGED","title":"feat(agent-runtime): wire DeepSeek v4 (pro + flash) for dispatch + ab discuss","url":"https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/2107"}
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: gh pr view 2112 --json number,title,state,mergedAt,url
raw: {"mergedAt":"2026-05-17T20:33:16Z","number":2112,"state":"MERGED","title":"feat(api): artifacts feed surfaces MD docs and decouples discovery from serving roots (#2106)","url":"https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/2112"}
```
