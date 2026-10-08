# Fleet shared doctrine — roles, cost discipline, living classification

**Status:** operator doctrine (binding for routing judgment; see precedence)
**Classification state:** drafted 2026-07-19 (Sol draft review #3593 `APPROVE_WITH_AMENDS` applied)
**Maintains with:** [`fleet-role-scorecard.md`](fleet-role-scorecard.md)
**Complements:**

- `agents_extensions/shared/rules/model-assignment.md` — machine routing / LANGUAGE-LANES
- [`agent-bridge.md`](agent-bridge.md) — review isolation, cross-family review, worktree reaper
- `agents_extensions/shared/rules/operator-expectations.md` — operator contract

---

## 0. Precedence (fail closed)

When instructions conflict, apply **in this order**:

1. Operator contract (`operator-expectations.md` and hard repo gates)
2. `model-assignment.md` / served `/api/rules` machine routing
3. **This doctrine** + scorecard
4. Session preference / ad-hoc “use the smartest model”

If a scorecard row conflicts with LANGUAGE-LANES, egress, or review-gate rules → **fail closed** (refuse the route; do not invent a silent substitution).

---

## 1. Terminology

| Term | Meaning |
|---|---|
| **Family** | Independence unit for CF review (e.g. Anthropic, OpenAI, xAI, Google, Moonshot, Zhipu/GLM, DeepSeek, Cursor-backed-*pinned*). |
| **Provider** | Who hosts the weights/API (OpenAI, Anthropic, xAI, Google, …). |
| **Harness** | Runtime that invokes the model (native Claude CLI, Codex, Grok Build, AGY, Hermes, Cursor, opencode). **Cursor is a harness/product**, not automatically a family. |
| **Route** | Concrete path: provider + intermediary (if any) + region/retention class. |
| **Egress** | Where prompt/code data may leave (Western lab, China-route, local-only). |
| **CF review** | Cross-**family** formal review of a change; discussion/panel alone does **not** satisfy the gate. |
| **Consequential** | Work that can merge to `main`, change learner-facing Atlas/curriculum, alter security/CI gates, or spend non-trivial quota on multi-agent implementation. |
| **Ceiling model** | Opus 5.5 (`claude-opus-5-5`) / Sol 6.1 (`gpt-6.1-sol`) for hard design/diagnostic/architecture. Future peers require qualification. Historical “Sol” references in older evidence remain historical. Designated approval is given by the operator, or when `claude-opus-5-5` and `gpt-6.1-sol` agree; when one of them authored the proposal, the other's approval completes it; a proposal by any other agent needs both; if they disagree, the operator decides (#9583, #9616). Fable 5.1 (`claude-fable-5-1`) and the former Astra seat hold no advisory, approval or review role; `gpt-6-astra` is not routable. |
| **Provisional / validated / deprecated** | Scorecard assignment confidence (see scorecard § evidence). |

---

## 2. Core principle

**Roles beat models.** Models rotate on accelerated schedules; roles stay stable:

`advisor · orchestrator · worker · CF reviewer · language · UI · recon`

Assign by **role × task family × harness × route/egress**, not marketing rank or “newest frontier.”

---

## 3. Role definitions

| Role | Job | Must not |
|---|---|---|
| **Ceiling advisor** | Architecture options, ambiguous multi-system failure, security/reliability disposition, hard curriculum **policy**, final **advisory** synthesis after evidence exists | Routine orchestration; first-pass implementation; recon; formatting; rubber-stamp “bless” without evidence |
| **Accountable orchestrator** | **Exactly one per stream**: scope, sequence, dispatch, integration, review routing, **terminal disposition** (merge/close/handoff) | Be sole CF reviewer of own stream’s consequential PR; bulk worker coding in interactive session |
| **Worker** | Implementation, tests, refactors, PR drafts in worktrees | Self-approve own formal review gate |
| **Independent CF reviewer** | Outside author **family** and **qualified for task family** (code vs language vs folk) | Same family as author; unqualified lane (e.g. DeepSeek for folk); discuss-as-review |
| **Language seat** | Ukrainian phrasing, morphology **hypotheses**, CEFR/pedagogy with `sources` MCP | China-egress cheap coders as UA cultural/factual authority |
| **UI design seat** | Interaction/visual/frontend concepts | Skip maintainability/a11y because a demo looks pretty |
| **Recon** | Search, logs, triage, evidence collection | Sole release authority |

**Advisor vs orchestrator:** advisor “final synthesis” is **recommendation only**. The **accountable orchestrator alone** owns terminal disposition.

**Advisor conflict:** if high-risk work was **materially designed** by an advisor, obtain dissent/review **outside** both that advisor’s family and the author’s family where practical.

---

## 4. Cost discipline (Opus / Sol advisors; future xAI ceiling)

- **Cursor (operator 2026-09-22; Auto scope operator decision 2026-09-30):** prefer **`--agent cursor --model grok-4.7-high`** for mechanical **and** ordinary infra/code implement when fit allows — not LANGUAGE-LANES, not advisor/authority. Cursor Auto runs only a well-defined coding task (`--research-role implementation` write dispatch, owned paths, PASS DoR card); the driver seat, design, consults, discussions and recon pin `grok-4.7` or `composer-2.5`, and a review runs the approved concrete model the reviewer resolver selects. `cursor:auto` never CF-of-record.
- **Utilize, do not trim (operator 2026-08-08 / #6468):** free/behind seats (Cursor, AGY, Pool, **Z.AI/GLM**, **Kimi k3-256k**, Claude routine, Grok workers) with open in-scope work must be pulled before feeding Codex near_cap mechanical jobs. **Keep Kimi and Z.AI/GLM** — they are first-class. Cutting subscriptions is a last resort after sustained measured zero use, not a response to multi-driver complexity. Concurrent drivers (~2 Grok + 1 Claude + 1–4 Codex) share free pools; coordinate via `/api/delegate/active`.
- **DeepSeek:** excluded from dispatch, implementation and review. Flash remains active in the catalog; Pro is retired. `ask-deepseek` is consult-only for non-language work, LOCAL-ONLY, via first-party `deepseek/` through OpenCode.
- **OpenRouter:** mainly Pool + Gemma; not a general multi-model bus.
- **Timed pauses:** near_cap/paused lanes carry **return-at** (e.g. Codex 2026-08-10T19:47Z) — auto-return, never permanent neglect.
- **Cursor gate:** #6469 plan-only adapter **fixed** — cursor-first mechanical tier is active.

- Use ceiling models **often** on *qualifying* hard work — not rarely, and not as free general labor.
- **Never** default ceiling models as orchestrator or first-pass implementer.
- **Escalation triggers (immediate):** security; high blast radius; unclear invariants; architectural ambiguity with multiple viable options; release-level uncertainty.
- **Escalation after evidence-backed attempts:** repeated failed **root-cause** fixes (not blind “retry 2×”).
- **Do not** escalate merely because the task is “important.”
- **SuperGrok Heavy** (and similar plans): **verified capacity entitlement** for longer/more parallel Grok worker runs — **not** a stable capability rank. Re-check when plan or routing changes.
- **Future xAI ceiling-class:** candidate ceiling advisor/hard coder **after bakeoff**; do not auto-promote to orchestrator.

### Effort guidance (per model)

| Model | Effort |
|---|---|
| GPT-6.1 Sol (coding, review and advice; designated approver with Opus 5.5) | **`high`** for accountable driving, coding, adversarial review and consequential advisory judgment |
| GPT-6 Luna (bounded work and scouting) | **`high`** with exact owned paths and an objective scope ceiling from a complete Sol advisory envelope (always required, #9275); never sole authority |
| **Opus 5.5** (default Claude model + driver seat, operator 2026-09-22) | Orchestrating / epic driving **`high`** (the launcher default). Routine turns **`medium`** (the API default — and Opus 5.5 at `medium` beats Opus 5 at `high` on coding and knowledge work). See subsection below. |
| **Sonnet 5.5** (provisional Claude practical seat) | Fleet dispatches **`high`** by default. Well-specified agentic coding may use `medium`; harder or longer coding and reviews use `high`. See subsection below. |
| **Fable 5.1** (selectable Claude model; no advisory, approval or review role, #9583) | Standing default **`high`** (API default; start here and sweep). See subsection below — do **not** port an Opus/`xhigh` habit. |
| Fable 5 (retired) | Historical identity only; Opus 5.5 / Sol 6.1 for current advice |
| Opus 5.5 (advisory consults only) | **`high`**; `xhigh` only for a documented hard turn |
| Claude Haiku recon | **`medium`** default; never sole authority |

#### Former Fable effort guidance

[Historical effort notes](../decisions/agent-rules-routing-history.md) are
archived evidence, not a current driver, advisor, approval or review route.
Current effort and model identities come from the catalog and live profiles.

**Standing exceptions (do not step down):** skills whose frontmatter pins
`effort: xhigh` — `content-review`, `plan-review`, `plan-review-seminar`,
`batch-review`, `prompt-review` — retain their pinned effort. Historical model
notes never override these Ukrainian learner-content review floors.

#### Opus 5.5 `/effort` decision topology (operator 2026-09-22)

Short form of the bundled Claude API Opus 5.5 migration guidance. The level names match Fable 5.1's, but the depth behind them does not, and they do not map 1:1 from Opus 5.

| Level | When |
|---|---|
| **`high`** | Orchestration and epic driving (`start-claude-driver.sh` default), dispatch briefs, pedagogy calls, first-pass code review of consequential PRs. |
| **`medium`** | **API default.** Routine interactive turns, status checks, small edits, day-to-day coding. In Anthropic's testing, `medium` matched or beat Opus 5 at `high` on multistep repository coding with about half the tokens. |
| **`low`** | Simple lookups and quick questions; latency-sensitive turns. Searches less — raise it when the turn needs retrieval. |
| **`xhigh`** | Hard debugging, large multi-file refactors — and the curriculum/linguistic review skills that pin `effort: xhigh` (same standing exceptions as Fable 5.1). Turns run noticeably longer than on Opus 5. |
| **`max`** | Almost never; only after measured headroom at `xhigh`. Uncapped. |

Quirks that change the choice:

- **Thinking is always on.** Effort is the only control; `thinking: disabled` and `budget_tokens` return a 400. To get less thinking, **lower effort before adding "think less" prompts**.
- **More thinking per level than Opus 5**, most of all at `xhigh`/`max`. A setting carried over from Opus 5 means longer turns and more output tokens.
- **Effort ≠ response length** (same as Fable 5.1): trim output with prompting, not the dial.

#### Sonnet 5.5 /effort decision topology (operator 2026-09-28)

Sonnet 5.5 effort levels are recalibrated versus Sonnet 5; do not carry settings over. The API default is **`high`**, and fleet dispatches default to **`high`** until measured outcomes support a narrower choice.

| Level | When |
|---|---|
| **`medium`** | Well-specified agentic coding with a bounded task and explicit verification. |
| **`high`** | Default for fleet dispatches, harder or longer agentic coding, and code reviews. |
| **`low`** | Avoid for dispatched work: it can skip verification. |
| **`xhigh` / `max`** | Only after a measured quality gain on the task family. |

At `low` or `medium`, Sonnet 5.5 can check in before finishing. Make completion criteria and verification explicit even when choosing `medium`. Escalate complex, open-ended judgment to Opus 5.5 / Sol 6.1; designated authority decisions still require operator approval or Opus 5.5 and Sol 6.1 agreeing (when one of them authored the proposal, the other's approval completes it; any other author needs both).

---

## 5. Orchestration vs work vs review

| Activity | Entry |
|---|---|
| Thin orchestration | One accountable lead selected from the current catalog for the stream |
| Implementation | `scripts/delegate.py dispatch --worktree` |
| Formal code CF review | Qualified native toolful lane resolved through the canonical `local-code-review` workflow |
| Advisory design | Qualified advisor from the current catalog with an **explicit decision question** |
| Multi-agent debate | `discuss` — **not** the merge gate |

Interactive orchestrators stay **thin** (status, route, approve, merge). Workers hold bulk context in worktrees.

---

## 6. Cross-family review (necessary, not sufficient)

For work in the **repository review-gate scope** (consequential PRs that must pass the operator CF gate before merge):

1. Reviewer **family ≠ author family**.
2. Reviewer must be **qualified for the task family** (code/infra vs VESUM language vs folk).
3. Use a qualified native toolful review lane and the review-worktree contract in `agents_extensions/shared/skills/local-code-review/SKILL.md`; sealed formal review is retired.
4. Record provenance on the PR (implementer + reviewer model/family/harness; note advisor if material).
5. **Conditional selection:** do not offer GPT-6.1 Sol as CF for OpenAI-authored PRs, or Sonnet as CF for Anthropic-authored PRs, etc.

Authoritative CF quality ladder remains in `model-assignment.md`; this doctrine does not lower that floor.

---

## 7. Language + evidence

- **LANGUAGE-LANES** for load-bearing Ukrainian judgment: `agy` / `codex` / `claude` only (see model-assignment).
- **Gemini 3.1 Pro via AGY** is the designated UA specialist; outputs remain **hypotheses until VESUM/`sources`-backed**.
- Code review and CF seat eligibility follow `model-assignment.md` Code review row.
- VESUM validates **morphology/attestation** — not arbitrary cultural or historical claims.
- FOLK: GPT↔Claude cultural gate; **no DeepSeek** for folk culture.

---

## 8. Egress and data class (route-level)

Before dispatch, classify **data class** and **route**:

| Data class | Default |
|---|---|
| Public open-source code | Standard fleet routes OK |
| Curriculum drafts / unreleased content | Prefer Western lab routes; record route |
| Secrets, tokens, learner PII | **Default-deny** external routes |
| Local-only policy lanes (GLM, some DeepSeek) | Never CI; never sensitive classes |

Record when relevant: **provider, intermediary, region/retention, data class**. Brand labels (“China”) are insufficient without the concrete route.

---

## 9. Living classification

Models improve on an accelerated schedule. Classification is a **maintenance duty**, not a one-time opinion.

- After **every major release** (including SuperGrok Heavy changes / new xAI ceiling): re-probe scorecard cells.
- Else **quarterly** full re-score.
- Public benchmarks = **priors only**; local bakeoffs + evidence ledger drive promotion.
- Capability **peak is unknown**; **value** today is routing hygiene + harness + evidence, not waiting for AGI.

See scorecard for provisional/validated/deprecated states and re-probe protocol.

---

## 10. Fallback and substitution

When a preferred lane is at quota/outage:

1. Use `scripts/config/agent_fallback_substitutions.yaml` + model-assignment harness table.
2. **Never** silently lower quality floor for consequential work.
3. **Always** record substitution (model/family/harness + reason) in the PR or orchestration note.

---

## 11. Anti-patterns

- Ceiling advisory consults for search, format, routine tests, first-pass CRUD.
- Advisors only at the end to bless a design they never challenged.
- Any single model as sole orchestrator + implementer + CF reviewer on a consequential stream.
- Flash/Luna/Haiku as release authority.
- Discuss/panel counted as CF review.
- Cursor “review” without **pinned** backing model family.
- Unqualified language/folk reviewers.
- China-egress / local-only routes on unclassified or sensitive data.
- Blind “fail twice then escalate” without root-cause evidence.

---

## 12. Change control

| Field | Value |
|---|---|
| Approval authority | Operator; orchestrator may draft updates |
| Sol review of this draft | Bridge ask `sol-fleet-docs-draft-review` reply #3593 |
| Next action after major xAI ceiling ship | Bakeoff + scorecard bump before advisor promotion |

**Changelog**

| Date | Change | By |
|---|---|---|
| 2026-07-19 | Initial doctrine (research + Sol #3588/#3593 amends) | grok/fleet-doctrine-scorecard |
| 2026-07-19 | Haiku listed with Luna for recon effort guidance / anti-patterns | grok/fleet-scorecard-haiku-recon |
| 2026-09-09 | Fable 5.1 `/effort` decision topology: default high; medium/low routine; xhigh rare; max almost never; over-gather / low-search quirks | cursor-infra/fable-51-effort-guidance |
| 2026-09-22 | Opus 5.5 is the default Claude model and driver seat (@ high); Fable 5.1 stays advisor; Opus 5.5 `/effort` topology (API default medium, levels not 1:1 with Opus 5) | claude/opus-5-5-default |
| 2026-09-28 | Sonnet 5.5 replaces Sonnet 5 as the provisional Claude practical seat; recalibrated `/effort` topology and high fleet default | codex/impl-9111 |
| 2026-10-03 | Opus 5.5 and Sol 6.1 replace Fable / Astra as advisors and designated approvers (both approve, neither the author; operator decides on disagreement); Fable 5.1 stays selectable with no advisory, approval or review role (#9583) | claude/impl-9583 |
| 2026-10-03 | Designated approval: Opus 5.5 and Sol 6.1 agreeing; when one of them authored the proposal, the other's approval completes it; any other author needs both; operator decides on disagreement (#9616) | claude/impl-9616 |
