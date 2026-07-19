# Fleet shared doctrine — roles, cost discipline, living classification

**Status:** operator doctrine (binding for routing judgment; see precedence)  
**Classification state:** drafted 2026-07-19 (Sol draft review #3593 `APPROVE_WITH_AMENDS` applied)  
**Maintains with:** [`fleet-role-scorecard.md`](fleet-role-scorecard.md)  
**Complements:**

- `agents_extensions/shared/rules/model-assignment.md` — machine routing / LANGUAGE-LANES  
- [`agent-bridge.md`](agent-bridge.md) — review isolation, `review-pr`, worktree reaper  
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
| **Ceiling model** | Sol, Fable 5, and any future peer (e.g. expected xAI Fable/Sol-class) reserved for hard design/diagnostic/architecture. |
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

## 4. Cost discipline (Sol / Fable / future xAI ceiling)

- Use ceiling models **often** on *qualifying* hard work — not rarely, and not as free general labor.  
- **Never** default ceiling models as orchestrator or first-pass implementer.  
- **Escalation triggers (immediate):** security; high blast radius; unclear invariants; architectural ambiguity with multiple viable options; release-level uncertainty.  
- **Escalation after evidence-backed attempts:** repeated failed **root-cause** fixes (not blind “retry 2×”).  
- **Do not** escalate merely because the task is “important.”  
- **SuperGrok Heavy** (and similar plans): **verified capacity entitlement** for longer/more parallel Grok worker runs — **not** a stable capability rank. Re-check when plan or routing changes.  
- **Future xAI Fable/Sol-class:** candidate ceiling advisor/hard coder **after bakeoff**; do not auto-promote to orchestrator.

### Effort guidance (per model)

| Model | Effort |
|---|---|
| Sol | Floor **`high`**; prefer **`xhigh`/`max`** for qualifying hard decisions |
| Fable 5 | Prefer **`xhigh`** for ceiling work |
| Terra (orchestrating hard stream) | **`xhigh`** |
| Terra (routine implement) | **`medium`–`high`**, escalate with risk |
| Opus orchestrating | **`high`+** |
| Luna / Claude Haiku recon | **`medium`** default; never sole authority |

---

## 5. Orchestration vs work vs review

| Activity | Entry |
|---|---|
| Thin orchestration | Interactive Opus / Terra (one owner per stream) |
| Implementation | `scripts/delegate.py dispatch --worktree` |
| Formal code CF review | `scripts/ai_agent_bridge` **`review-pr`** (pointer-only; sealed when available) |
| Advisory design | Bounded Sol/Fable ask with **explicit decision question** |
| Multi-agent debate | `discuss` — **not** the merge gate |

Interactive orchestrators stay **thin** (status, route, approve, merge). Workers hold bulk context in worktrees.

---

## 6. Cross-family review (necessary, not sufficient)

For work in the **repository review-gate scope** (consequential PRs that must pass the operator CF gate before merge):

1. Reviewer **family ≠ author family**.  
2. Reviewer must be **qualified for the task family** (code/infra vs VESUM language vs folk).  
3. Prefer `review-pr` / sealed isolation; never primary-checkout toolful review.  
4. Record provenance on the PR (implementer + reviewer model/family/harness; note advisor if material).  
5. **Conditional selection:** do not offer Terra as CF for OpenAI-authored PRs, or Sonnet as CF for Anthropic-authored PRs, etc.

Authoritative CF quality ladder remains in `model-assignment.md`; this doctrine does not lower that floor.

---

## 7. Language + evidence

- **LANGUAGE-LANES** for load-bearing Ukrainian judgment: `agy` / `codex` / `claude` / `grok-4.5` only (see model-assignment).  
- **Gemini 3.1 Pro via AGY** is the designated UA specialist; outputs remain **hypotheses until VESUM/`sources`-backed**.  
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

- Sol/Fable for search, format, routine tests, first-pass CRUD.  
- Sol/Fable only at the end to bless a design they never challenged.  
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
