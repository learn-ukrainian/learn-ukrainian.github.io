# 2026-06-15 Claude Dispatch Sunset

**Status:** TRANSITION PLAN.
**Date:** 2026-05-19
**Cutover:** 2026-06-15
**Scope:** Eliminate orchestrator-fired `delegate.py --agent claude` invocations
before the hard rule takes effect.

---

## The Hard Rule

The current `claude_extensions/memory/MEMORY.md` #M0 row still records the
pre-cutover assignment:

> `delegate.py dispatch --agent claude --mode read-only --model claude-opus-4-7 --effort xhigh`

The current file does not contain a distinct `post_2026_06_15` paragraph under
rule M0. The post-cutover hard rule is in
`scripts/config/agent_fallback_substitutions.yaml`:

> Per user direction 2026-05-13 ("you should delegate only to codex and gemini
> after june 15th"): after the agentic credit pool launches, NO `delegate.py
> --agent claude` invocations. Code dispatches route to codex/gemini; Claude
> programmatic surfaces use the substitution chain above from day one, not
> only at near_cap. The $200/mo pool is reserved for user's own cold-start
> review sessions, not orchestrator dispatches.

The agent activity matrix frames the same rule in routing terms:

> Post-June-15: NO `delegate.py --agent claude`; inline-via-curriculum-writer subagent only.

This plan treats the YAML block as the canonical substitution source and the
matrix as the current routing status view.

---

## What Changes On 2026-06-15

Starting 2026-06-15:

- No orchestrator-fired `delegate.py --agent claude` invocations.
- No `ab review-deep` implementation that shells into `delegate.py --agent claude`.
- No new dispatch briefs that require Claude headless work through `delegate.py`.
- Code dispatches route to Codex or Gemini.
- Claude programmatic surfaces use the substitution chain from day one, not only
  when the routing budget is near cap.
- The $200/month agentic credit pool is reserved for the user's own cold-start
  review sessions.
- No overage.

This is a routing rule, not a quality claim. Any substitute that has not been
empirically tested in the target role is marked pending verification.

---

## Canonical Substitution Chain

`scripts/config/agent_fallback_substitutions.yaml` is quoted in full:

```yaml
# Agent fallback substitution map — canonical source of truth.
# Consumed by /api/state/routing-budget (when extended in follow-up PR) and
# referenced by orchestrator routing decisions (MEMORY.md, this file).
#
# Trigger condition: when a budget bucket is at status `near_cap` or higher
# (burn_pct > 90), the orchestrator MUST use the substitution path below
# instead of the surface that would drain the depleted bucket.
#
# Provenance: user direction 2026-05-13 — "you need to store this and add to
# router" (paste of the substitution table built during the budget-economics
# discussion that day).

substitutions:
  - currently_uses: "delegate.py --agent claude (adversarial review)"
    fallback: 'Agent(subagent_type="general-purpose", model="opus")'
    fallback_note: "Agent tool subagents run as children of this session"
    budget_bucket: "interactive (orchestrator session, not programmatic)"

  - currently_uses: "delegate.py --agent claude (code dispatch >50 LOC)"
    fallback: |
      (a) Codex via `delegate.py --agent codex` (separate weekly quota), OR
      (b) inline by orchestrator if context-continuity gives it an edge
    budget_bucket: "Codex weekly quota OR interactive"

  - currently_uses: "ab ask-claude (one-shot consult)"
    fallback: |
      Orchestrator inline reasoning (orchestrator IS Claude), OR
      Agent(subagent_type="general-purpose", model="opus")
    budget_bucket: "interactive"

  - currently_uses: "ab discuss (Codex + Claude adversarial)"
    fallback: |
      Codex via `delegate.py --agent codex` + Agent subagent for Claude role,
      OR escalate to user for cold-start interactive Claude (highest-stakes
      adversarial dynamic only)
    budget_bucket: "Codex + interactive"

  - currently_uses: "delegate.py --agent codex"
    fallback: "(unaffected — separate weekly quota)"
    budget_bucket: "Codex weekly"

  - currently_uses: "delegate.py --agent gemini"
    fallback: "(unaffected — separate quota)"
    budget_bucket: "Gemini"

post_2026_06_15_hard_rule: |
  Per user direction 2026-05-13 ("you should delegate only to codex and gemini
  after june 15th"): after the agentic credit pool launches, NO `delegate.py
  --agent claude` invocations. Code dispatches route to codex/gemini; Claude
  programmatic surfaces use the substitution chain above from day one, not
  only at near_cap. The $200/mo pool is reserved for user's own cold-start
  review sessions, not orchestrator dispatches.
```

Do not add substitutions outside this map in implementation work. If a new
substitution path is needed, update the YAML first and route that change through
review.

---

## Current Claude-Dispatch Call Sites

The grep surface has three classes:

1. Active code that constructs a Claude dispatch.
2. Active policy/docs that tell agents to use Claude dispatch.
3. Historical dispatch briefs and reports that mention prior Claude dispatches.

Only class 1 and class 2 require code/doc changes before 2026-06-15. Class 3 is
historical record; do not rewrite history unless a doc is loaded as current
policy.

| Where | Today's use | Post-June-15 substitute | Status |
| --- | --- | --- | --- |
| `scripts/ai_agent_bridge/_dispatch_wrappers.py:198-215` | `ab review-deep` builds a command with `scripts/delegate.py dispatch --agent claude --mode read-only --model claude-opus-4-7`. | YAML adversarial-review fallback: `Agent(subagent_type="general-purpose", model="opus")`. If that cannot be launched from the CLI wrapper, disable or re-route the wrapper to an approved Codex/Gemini path. | pending verification |
| `docs/best-practices/agent-bridge.md:161-165` | Documents `ab review-deep` as hardcoded Claude review. | Update after the wrapper changes. | pending implementation |
| `claude_extensions/memory/MEMORY.md:44` | Per-task model assignment row for adversarial review. | YAML adversarial-review fallback. | pending memory update |
| `claude_extensions/rules/model-assignment.md:14` | Deploy-rule mirror of the adversarial-review Claude dispatch row. | YAML adversarial-review fallback. | pending rule update |
| `docs/best-practices/agent-activity-matrix.md:29` | Roster row says full dispatch pre-June-15 and no Claude delegate post-June-15. | Already states the hard rule. | verified as policy |
| `docs/best-practices/agent-activity-matrix.md:133` | Marks Claude headless as primary pre-June-15 for adversarial design review. | Matrix already names Codex as primary post-June-15 in the following row. | pending matrix cleanup after cutover |
| `docs/best-practices/agent-activity-matrix.md:225` | Invocation cheat sheet for adversarial review pre-June-15. | Replace with post-cutover substitute or mark historical. | pending doc update |
| `docs/agents/AGENT-CAPABILITY-MATRIX.md:38` | Agent inventory lists `delegate.py --agent claude` until cutoff. | Keep as cutoff note or replace with post-cutover status. | pending doc update |
| `docs/agents/AGENT-CAPABILITY-MATRIX.md:315-316` | Cheat sheet shows a Claude dispatch command. | Replace or mark pre-cutover only. | pending doc update |
| `scripts/config/agent_fallback_substitutions.yaml:14-23` | Canonical substitution entries for Claude dispatch uses. | Already canonical. | verified |
| `scripts/config/agent_fallback_substitutions.yaml:46-52` | Canonical hard rule. | Already canonical. | verified |

Historical records found by grep:

| Where | Treatment |
| --- | --- |
| `docs/dispatch-queue/2026-05-06-afternoon.md:46` | Historical queue item that created `ab review-deep`; do not edit unless the queue is being revived. |
| `docs/dispatch-briefs/2026-05-06-1754-claude-keychain-user-env.md:25,114` | Historical auth-fix brief; do not edit. |
| `docs/dispatch-briefs/2026-05-13-routing-budget-observability.md:19,31` | Historical routing-budget test brief; do not edit. |
| `docs/dispatch-briefs/2026-05-19-four-deliverable-docs-codex.md:116,121,122` | This dispatch brief; do not edit as part of the plan. |
| `docs/session-state/2026-04-22-afternoon-ops-infra-pass.md:39` | Historical session state; do not edit. |
| `docs/session-state/2026-05-06-evening-tech-debt-arc-and-auth-cascades.md:130` | Historical failed review attempt; do not edit. |
| `docs/session-state/2026-05-13-late-routing-economics-corpus-expansion-brief.md:73` | Historical source for the routing economics shift; cite, do not edit. |
| `docs/session-state/current.md:41` | Rolling handoff file; update only through the normal session-state process. |
| `audit/INDEX-bakeoff-evidence.md:103,113,118` | Evidence index; do not edit for the cutover unless regenerating the index. |
| `audit/2026-05-17-harness-layered-audit/REPORT.md:23,101` | Historical audit recommending enforcement; do not edit. |
| `audit/2026-05-18-docs-gaps-and-reorganization/REPORT.md:157` | Gap audit source; orchestrator will update after this PR merges. |

---

## Adjacent Claude Programmatic Surfaces

These are not `delegate.py --agent claude` call sites, but they use Claude
programmatically and should be reviewed before cutover:

| Where | Today's use | Post-June-15 handling | Status |
| --- | --- | --- | --- |
| `scripts/audit/naturalness_check.py:144-160` | Calls `ab ask-claude` for naturalness checking. | YAML `ab ask-claude` fallback: orchestrator inline reasoning or Agent subagent. | pending verification |
| `scripts/audit/russianism_judge.py:231-239` | Uses `ab ask-claude` when `judge-family=claude`. | YAML `ab ask-claude` fallback. Keep Claude judge only where explicitly paid by user cold-start session or replaced by another validated judge. | pending verification |
| `scripts/audit/russianism_eval.py:149-150` | Builds an `ask-claude` evaluation command. | Same as above. | pending verification |
| `scripts/audit/code_review_benchmark.py:415` | Direct `claude -p` benchmark path. | Treat as benchmark-only or disable in post-cutover default runs. | pending verification |
| `scripts/audit/judge_calibration_matrix.py:303` | Direct `claude -p` calibration path. | Treat as calibration-only; do not run automatically after cutover. | pending verification |

These surfaces are outside the exact `delegate.py --agent claude` hard rule, but
they draw from the same Claude programmatic budget concern. They should be made
opt-in, substituted, or explicitly documented as user-funded cold-start work.

---

## Pre-Cutover Verification Checklist

Run these before 2026-06-15, ordered by load-bearingness:

| Order | Verification | Why it is first-class | Owner path |
| --- | --- | --- | --- |
| 1 | A1 m20 6-writer V7 bakeoff using the methodology in [`writer-bakeoff-methodology.md`](../best-practices/pipeline/writer-bakeoff-methodology.md). | V7 writer is the largest quality risk after Claude dispatch ends. | Codex dispatch after DeepSeek wiring. |
| 2 | DeepSeek V7 writer wiring smoke. | The handoff marks DeepSeek-v4-pro as high priority and cheap, but not yet wired as V7 writer. | Codex code dispatch, then bakeoff. |
| 3 | `ab review-deep` substitute dry run. | It is the active code path that constructs a Claude dispatch today. | Update wrapper or disable post-cutover command. |
| 4 | Adversarial design review substitute. | Matrix says Claude headless is primary pre-cutover and Codex primary post-cutover. Verify the workflow and report format. | Codex xhigh or approved Agent fallback. |
| 5 | `ab ask-claude` substitutes for audit scripts. | Naturalness/Russianism scripts can otherwise keep burning Claude programmatic calls. | Audit-script owner. |
| 6 | Documentation sweep. | Agents load docs and rules. Stale examples become accidental dispatches. | Docs PR after code substitutions. |
| 7 | Harness rule for post-cutover denial. | The 2026-05-17 harness audit already proposed a date-check guard. | Separate harness PR. |

Every substitute that has not passed its role-specific test remains pending
verification. Do not promote pending substitutes to primary routing language.

---

## V7 Writer Special Case

`claude-tools` is the current A1/A2 V7 writer according to
[`docs/decisions/2026-05-06-writer-selection-codex-gpt55.md`](../decisions/2026-05-06-writer-selection-codex-gpt55.md).
The revised decision says claude-tools won A1/my-morning on content merit, while
codex-tools remained viable and should be re-bakeoffed for B1+/seminar scope.

Post-June-15 alternatives, in priority order for A1 replacement work:

| Priority | Candidate | Status |
| --- | --- | --- |
| 1 | `codex-tools` with register-tuned settings | pending verification for A1 register. Tooling is functional; A1 content-register gap remains. |
| 2 | `deepseek-tools` | pending V7 writer wiring; handoff marks it high priority. |
| 3 | `gemini-tools` | pending re-bakeoff; last module-writer signal was infrastructure failure, not a clean quality loss. |

The 2026-05-19 handoff corrected the strategic sequence:

> **Skip A1 entirely → REVERSED.** Finish A1 m20 first; slowly build A1 thereafter.
>
> A1 is the PRECISION test ("how precisely they follow the prompt"). Don't skip it for Chinese-model bakeoff.
>
> DeepSeek-v4-pro as V7 writer is high priority (cheap + already-validated quality elsewhere)

Do not let the sunset plan silently skip A1. A1 remains the precision test.

---

## If No A1 Writer Alternative Passes

If the A1 m20 6-writer bakeoff finds no post-cutover writer that matches the A1
quality bar, the options are:

| Option | Policy | Recommendation |
| --- | --- | --- |
| A | Ship the next-best writer with an explicit quality caveat. | Only if the user explicitly accepts the caveat. |
| B | Keep `claude-tools` for A1 by extending the user's cold-start sessions to writer dispatches. | No. User direction excludes this for orchestrator dispatches and says no overage. |
| C | Pause A1 module production and ship A2+ or non-A1 tracks first. | Default recommendation. |

Option C is the default because it preserves quality and respects the budget
rule. Option A is acceptable only as an explicit user override for a known
quality downgrade. Option B is out under the current hard rule.

---

## What Also Needs To Change

[`docs/decisions/pending/2026-05-14-agent-sdk-adoption.md`](../decisions/pending/2026-05-14-agent-sdk-adoption.md)
is already marked `RECONSIDER`. That is the correct status.

The SDK card's original efficiency premise depended on using a Claude
programmatic pool after 2026-06-15. The current hard rule says that pool is
reserved for user cold-start review sessions, not orchestrator dispatches.

Action:

- Reconsider the SDK decision as host-agnostic in-process agent runtime work, not
  as Claude-pool-funded V7 writer work.
- Do not auto-deny the SDK pattern; mid-stream hooks may still be useful with a
  non-Claude host.
- Do not implement a Claude SDK writer default under the old premise.

---

## Implementation Tasks By Surface

| Surface | Change before cutover | Verification |
| --- | --- | --- |
| `scripts/ai_agent_bridge/_dispatch_wrappers.py` | Remove or substitute the `claude` agent in `build_review_deep_command`. | `ab review-deep --dry-run` must not write a task state with `agent=claude`. |
| `docs/best-practices/agent-bridge.md` | Rewrite `ab review-deep` documentation after the wrapper changes. | Grep for `review-deep` plus `--agent claude` in docs. |
| `claude_extensions/memory/MEMORY.md` | Replace the pre-cutover adversarial-review row or mark it as historical with the YAML fallback. | Deploy-rule sync should no longer expose a current Claude delegate command. |
| `claude_extensions/rules/model-assignment.md` | Mirror the memory change. | `npm run claude:deploy` output, if deployment is in scope for that PR. |
| `docs/best-practices/agent-activity-matrix.md` | Move pre-June-15 Claude rows to historical or runner-up language after cutover. | Matrix still names a primary substitute for each load-bearing role. |
| `docs/agents/AGENT-CAPABILITY-MATRIX.md` | Remove cheat-sheet commands that launch Claude delegate after cutover. | Grep for direct Claude delegate examples. |
| Audit scripts using `ask-claude` | Make Claude-family runs opt-in or route through the YAML fallback. | Dry-run each affected script path with a non-Claude family. |
| Harness guard | Deny post-cutover `delegate.py --agent claude` commands unless an explicit user override is added later. | Date-gated shell-hook test. |

The implementation order should follow the verification checklist. Code paths
that can launch work come before documentation examples. Documentation examples
come before historical cleanup. Historical reports stay unchanged unless they are
being treated as live policy.

---

## Cutover Dry Run

Run a dry run during week 4, before 2026-06-15:

1. Grep current scripts for direct `delegate.py --agent claude` and split-argv
   Claude delegate construction.
2. Grep current docs and rules for Claude delegate commands that are not marked
   pre-cutover or historical.
3. Run `ab review-deep --dry-run` against a harmless target and inspect the
   generated task state.
4. Run the V7 writer bakeoff scorer against the A1 replacement bakeoff report.
5. Confirm the matrix has a post-cutover primary or a documented pause for A1.
6. Confirm the SDK adoption card is still `RECONSIDER` and no implementation
   brief treats Claude SDK as the post-cutover writer default.
7. Confirm the fallback YAML still contains the hard-rule block.

Dry-run pass criteria:

| Check | Pass condition |
| --- | --- |
| Script grep | No active launcher constructs `delegate.py --agent claude`. |
| Docs grep | Current policy docs do not instruct agents to launch Claude delegate after cutover. |
| Wrapper dry run | Generated task state does not set `agent` to `claude`. |
| Writer route | A1 has a validated substitute or an explicit production pause. |
| SDK route | No Claude SDK writer default is queued under the old pool premise. |
| Fallback config | YAML hard rule remains present and unweakened. |

If any dry-run check fails, freeze new Claude-dispatch work and fix the failing
surface before 2026-06-15.

---

## Calendar

The calendar is four weeks from 2026-05-18:

| Window | Milestone |
| --- | --- |
| Week 1: 2026-05-18 to 2026-05-24 | Enumerate call sites, open or queue verification dispatches, and land this plan. |
| Week 2: 2026-05-25 to 2026-05-31 | Run verification dispatches: DeepSeek writer wiring, A1 bakeoff, `ab review-deep` substitute dry run. |
| Week 3: 2026-06-01 to 2026-06-07 | Update routing rules, wrappers, docs, and tests based on verification results. |
| Week 4: 2026-06-08 to 2026-06-14 | Freeze routing, dry-run denial guard, document lessons, and ensure no current docs recommend Claude dispatch. |
| Cutover: 2026-06-15 | Enforce no orchestrator-fired `delegate.py --agent claude`; use substitutes from the YAML chain. |

No new deadline is introduced here. This calendar is the plan for meeting the
already-decided 2026-06-15 rule.

---

## Open Questions For User

1. If the A1 bakeoff finds no post-cutover writer matching `claude-tools`, do we
   pause A1 by default, or ship the next-best writer with an explicit caveat?
2. Should `ab review-deep` become a Codex/Gemini wrapper after cutover, or should
   it be disabled unless an interactive Agent fallback is available?
3. Should the SDK adoption card be rewritten as a host-agnostic runtime/hook
   proposal, or shelved until after writer replacement is solved?

---

## Verification Evidence

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: nl -ba claude_extensions/memory/MEMORY.md | sed -n '1,70p'
raw: 36  ## #M0 — PER-TASK MODEL ASSIGNMENT (HARD RULE, 2026-05-06)
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: nl -ba claude_extensions/memory/MEMORY.md | sed -n '1,70p'
raw: 44  | Adversarial review of design / ADR / architecture | `delegate.py dispatch --agent claude --mode read-only --model claude-opus-4-7 --effort xhigh` (headless Opus, separate billing) |
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: nl -ba scripts/config/agent_fallback_substitutions.yaml
raw: 46  post_2026_06_15_hard_rule: |
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: nl -ba docs/best-practices/agent-activity-matrix.md | sed -n '18,36p'
raw: 29  | **Claude** | Opus 4.7 (orchestrator inline + headless dispatch + Q&A); Sonnet 4.7 (mid-tier headless); Haiku (cheap Explore subagent grep/read) | Anthropic API (interactive, weekly cap $690 — doubled until mid-July 2026 promo); $200/mo agentic pool launches 2026-06-15 (RESERVED for user cold-start, NOT orchestrator) | Interactive cap shared with user sessions | **Pre-June-15: full dispatch.** Post-June-15: NO `delegate.py --agent claude`; inline-via-curriculum-writer subagent only. |
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: rg -n 'delegate\.py[^\n]*--agent claude|--agent claude[^\n]*delegate\.py' scripts
raw: scripts/config/agent_fallback_substitutions.yaml:14:  - currently_uses: "delegate.py --agent claude (adversarial review)"
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: nl -ba scripts/ai_agent_bridge/_dispatch_wrappers.py | sed -n '190,235p'
raw: 198  def build_review_deep_command(target: str, prompt_file: Path, effort: str) -> list[str]:
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: nl -ba scripts/ai_agent_bridge/_dispatch_wrappers.py | sed -n '190,235p'
raw: 203          "--agent",
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: nl -ba scripts/ai_agent_bridge/_dispatch_wrappers.py | sed -n '190,235p'
raw: 204          "claude",
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: rg -n 'delegate\.py[^\n]*--agent claude|--agent claude[^\n]*delegate\.py' docs/dispatch-briefs docs/dispatch-queue docs/agents docs/best-practices docs/decisions docs/session-state claude_extensions audit --glob '!**/*.html' --glob '!audit/bakeoff-2026-05-13-midday/**' --glob '!audit/incidents/**'
raw: docs/best-practices/agent-activity-matrix.md:225:| Adversarial review (pre-June-15) | `.venv/bin/python scripts/delegate.py dispatch --agent claude --mode read-only --model claude-opus-4-7 --effort xhigh --task-id X --prompt-file BRIEF` |
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: nl -ba docs/decisions/2026-05-06-writer-selection-codex-gpt55.md | sed -n '1,155p'
raw: 120  - **Status:** ACCEPTED → REVISED (night) → **REVISED-AGAIN 2026-05-13 midday on empirical fair-env evidence**. New ACCEPTED default writer for **A1 + A2 scope: claude-tools**. Effective immediately.
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: nl -ba docs/session-state/2026-05-19-handoff-gap-audit-and-qwen-integration.md | sed -n '104,120p'
raw: 114  **Strategy direction (user-corrected mid-session):**
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: nl -ba docs/decisions/pending/2026-05-14-agent-sdk-adoption.md | sed -n '1,235p'
raw: 3  **Status:** RECONSIDER — surfaced 2026-05-13, demoted same day after user routing direction shifted the cost premise. Adoption is not cancelled; the sequencing and the "wins" framing both need a rethink before re-PROPOSED.
```
