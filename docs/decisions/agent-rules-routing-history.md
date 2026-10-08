# Agent routing history

Historical evidence only; none of these seats, deadlines, grades or migration
notes authorize current routing. Use `scripts/config/model_catalog.yaml` and
`agents_extensions/shared/rules/model-assignment.md`.

### Historical Wave 1 CF SCORECARD fold (provisional, 2026-08-23)

Operator/CTO GO 2026-08-23. Letter grades are **advisory labels** on the existing
`quality_tiers` — not a parallel ranking and not a `reviewed_on` refresh. The former Foundry sequencing hold has ended; it is not a current gate.

| Seat | Provisional lock | Catalog tier (unchanged) | Wave 1 CF evidence |
| --- | --- | --- | --- |
| Fable (`claude-fable-5`, historical scorecard) | **S+** | `frontier_authority` | operator lock (no Wave 1 public CF cell required) |
| Historical `gpt-5.6-sol` / Codex (retired; not a route) | **A** / hard advisory in the 2026-08-23 scorecard | `frontier_authority` at the time | #7142 thorough/confirmational on docs; live hard advice now routes to the Sol advisor (`gpt-6.1-sol` @ high) |
| Historical Grok (`grok-4.6`; retired, not a route) | **≥B, NOT C** — do not demote | `frontier_practical` | #7133 pass with nits; residual-positional finding |
| Kimi (native `kimi` CLI) | historical evidence only; Kimi no longer reviews (coding only) | `frontier_practical` | #7143 pass with nits |
| AGY (`gemini-3.7-flash-high`) | historical fast scoped CF; no current code-review route | `frontier_practical` | #7137 pass, wall ~47s, low noise, concrete finding |
| GLM-5.3 | ships-heavier; **LOCAL-ONLY** (zai-coding-plan) | `frontier_practical` | #7144 pass with nits; solid root-cause; also #7121 fetch refspecs |

OpenRouter remains **mainly Pool + Gemma**. Kimi / Gemini (AGY) / GLM subscribed seats
**never** route through OpenRouter. Do not reopen Kimi-OpenRouter; keep the native
`kimi` CLI. This fold does not change review ladders, formal-eligibility bits, or
`reviewed_on` (2026-08-16) — notes and strengths only.


#### Fable 5.1 `/effort` decision topology (operator 2026-09-09)

Canonical short form of the bundled Claude API Fable 5.1 effort guidance (Claude Code `/effort` picker). Level names do **not** map to the same thinking depth across models.

These effort settings apply only when Fable 5.1 is explicitly selected; they do not change
the Opus 5.5 / Sol 6.1 routing defaults or the designated approval boundary.

| Level | When |
|---|---|
| **`high`** | **Default.** Orchestration, epic driving, first-pass **code** review, dispatch briefs, day-to-day coding. Also the starting point for **long deliverables** (long docs/code rewrites): stay at `high` unless a measured quality gain justifies more. |
| **`medium` / `low`** | Routine / quick interactive turns. Fable 5.1 at `low` often beats prior-gen `xhigh`/`max`; `medium` roughly matches Fable 5 cheaper. Prefer these for quick edits and questions. |
| **`xhigh`** | Capability-sensitive only: hard debugging, large multi-file refactors, long autonomous runs — and the standing floor for **curriculum/linguistic review skills** (see exceptions). Expect multi-minute turns. At `xhigh`/`max`, leave room for the final answer (provider: long outputs can exhaust the turn if thinking fills the budget). |
| **`max`** | Almost never — extremely hard, latency-insensitive problems after measured headroom at `xhigh`. Same long-output budget caution. |

**Standing exceptions (do not “step down” these):** skills whose frontmatter pins `effort: xhigh` — `content-review`, `plan-review`, `plan-review-seminar`, `batch-review`, `prompt-review` — stay at `xhigh`. They judge Ukrainian learner content; a miss is a durable error. This topology does **not** override those pins. Routine **code** CF may still use a cheaper first pass via dispatch routing.

Quirks that change the choice:

- **Higher effort on routine work over-gathers.** At `high+` on a simple task it deliberates too long and may tidy/refactor unasked code — **lower effort**, do not prompt around it.
- **`low` searches less.** Answers from memory more; bump effort when the turn needs retrieval for named products/libraries with stale knowledge.
- **Effort ≠ response length.** Over-long replies are a prompting fix (see Concise by default), not an effort dial. Separately: for long *deliverables*, prefer `high` first; only raise to `xhigh`/`max` with a measured benefit and output-budget headroom.


## 9. Change log

| Date | Change | Confidence note | By |
|---|---|---|---|
| 2026-07-19 | Initial scorecard from operator intent + web research + Sol #3588/#3593 | **drafted / provisional** — not full bakeoff-validated | grok/fleet-doctrine-scorecard |
| 2026-07-19 | Add Claude Haiku to recon seat (with Luna / Gemini 3.5 Flash) | provisional | grok/fleet-scorecard-haiku-recon |
| 2026-10-03 | Opus 5.5 and Sol 6.1 replace Fable / Astra as advisors and designated approvers (both approve, neither the author; operator decides on disagreement); Fable holds no advisory, approval or review role (#9583) | operator decision | claude/impl-9583 |
| 2026-10-03 | Designated approval: Opus 5.5 and Sol 6.1 agreeing; when one of them authored the proposal, the other's approval completes it; any other author needs both; operator decides on disagreement (#9616) | operator decision | claude/impl-9616 |

**Approval authority:** operator for ceiling-seat changes; orchestrator may update provisional notes and evidence ledger.
