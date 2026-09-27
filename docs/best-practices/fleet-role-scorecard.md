# Fleet role scorecard — living model classification

**Status:** living scorecard (**classification refreshed** 2026-08-02 — not all cells fully bakeoff-validated)
**Doctrine:** [`fleet-shared-doctrine.md`](fleet-shared-doctrine.md)
**Machine routing:** `agents_extensions/shared/rules/model-assignment.md` (takes precedence on conflict)
**Evidence baseline:** public Jul 2026 model cards/roundups + project catalog + Sol advisories #3588 / #3593
**Owner:** accountable orchestrator (update after bakeoffs; operator approves role demotions/promotions for ceiling seats)

---

## 0. How to read this document

- Rows are **role assignments**, not a global IQ ranking.
- Each assignment has a **confidence**: `provisional` | `validated` | `deprecated`.
- **Provisional** = operator intent + public priors + Sol review; needs local bakeoff.
- **Validated** = recorded local bakeoff with harness/effort/outcome.
- **Deprecated** = do not route except explicit exception.
- Benchmarks and press numbers are **priors**; harness × effort can invert order.

---

## 1. Current role → models (updated 2026-09-23)

| Role | Primary | Secondary / volume | Effort | Confidence |
|---|---|---|---|---|
| Ceiling advisor/designer | GPT-6 Astra, Fable 5.1 | — | Astra `high`; Fable `high` | provisional |
| Accountable orchestrator | GPT-6 Sol, Claude Opus 5.5 | — | `high` | provisional |
| General implementer | GPT-6 Sol, Claude Sonnet 5, Grok 4.7 | GPT-6 Luna for bounded work; Gemini 3.8 Flash for well-defined work; K3; Cursor (**pin family**) | `high` by task fit | provisional |
| Hard implementer | GPT-6 Sol, Claude Opus 5.5 | Escalate hard design judgment to Astra or Fable | `high` | provisional |
| UI / visual product design | K3 | Astra for hard systems UX advice; Kimi consult non-UA | K3 `high`; Astra `high` | provisional (K3 UI primacy needs bakeoffs) |
| Code/security CF review | **Author-family-conditional** (see §3) | — | `high`+ | provisional |
| Critical CF review | GPT-6 Sol ↔ Fable/Opus **cross-family** | — | `high` | provisional |
| Ukrainian language | Gemini 3.8 Flash High (AGY) | LANGUAGE-LANES: GPT-6 Sol, Claude, Grok 4.7 + sources | `high` | provisional (morphology remains VESUM-gated) |
| Recon / triage | GPT-6 Luna, Claude Haiku, Gemini 3.8 Flash | — | Luna `high` with exact owned paths + objective scope ceiling; others by task fit; never sole release | provisional |

**One orchestrator per stream.** Advisors recommend; orchestrator owns terminal disposition.

---

## 2. Model cards (strengths / weaknesses / project notes)

| Model | Strengths | Weaknesses | Route / egress notes | Project seat |
|---|---|---|---|---|
| **Fable 5.1** | Hard advisory judgment and architecture | Costly as bulk worker | Anthropic | Ceiling advisor |
| **GPT-6 Astra** | Hard OpenAI advisory judgment | Same-family review of OpenAI work is not independent | OpenAI / native Codex | Ceiling advisor, not routine coding or CF |
| **GPT-6 Sol** | Accountable driving, coding, and adversarial review | Same-family review of OpenAI work is not independent | OpenAI / native Codex | Regular driver, coder, and reviewer @ high |
| **Claude Opus 5.5** | Hard Claude-lane coding and deep code review | Costly as bulk worker | Anthropic / native Claude or verified Cursor slug | Hard coding and review @ high |
| **GPT-6 Luna** | Fast bounded implementation, recon, and mechanical checks | Never sole architecture/security/language/release authority | OpenAI / native Codex | Bounded worker / recon @ high |
| **Claude Haiku** | Fast cheap recon/triage on Anthropic lane; good for log/search skim | Never sole architecture/security/language/release authority | Anthropic | Recon (with Luna / 3.5 Flash) |
| **Sonnet 5** | Near-flagship coding at better cost; daily driver agentic | Escalate systemic ambiguity | Anthropic | Default worker |
| **Grok 4.7** | Strong coding agent; token-efficient; good CF review value | Prefer worker/reviewer not sole orchestrator | xAI; SuperGrok Heavy = capacity entitlement (re-verify) | Worker + CF review |
| **Gemini 3.8 Flash High** | Multilingual / designated UA language seat; semantic review | Not bulk CRUD default; language outputs need sources | Google / AGY | Language lane (3.1 Pro only on explicit request (operator 2026-09-22)) |
| **K3** | Long-horizon coding; frontend/visual ideation | Maintainability ≠ demo; Moonshot route/egress | Moonshot | UI + long implement |
| **GLM-5.3** | Deep bug/security; large-context code coherence | Weak UA pedagogy; **LOCAL-ONLY** China-egress | Zhipu / opencode local | Local CF code only; never CI |
| **DeepSeek V4 Flash** | Economical coding + infra CF volume; Arena-practical frontend (operator preferred) | Not folk/UA/critical authority; Pro @ high = hard implement only (complex multi-file, hard lookup — 2026-08-13), never default | **First-party only** (`deepseek/` via OpenCode); OpenRouter deepseek refused | Infra/code CF + worker |
| **Cursor Auto** / Composer 2.5 | Mechanical code/infra when free; first-class worker (#6468) | Auto never formal CF identity; adapter gate #6469 | Cursor harness multi-model | Worker (impl) |

---

## 3. Author-family-conditional CF review (required)

Never use a fixed unordered list that can pick the author’s family.

| Author family | Prefer CF reviewers (code/infra) | Avoid as sole CF |
|---|---|---|
| Anthropic (Opus/Sonnet/Fable) | Grok, GPT-6 Sol, GLM local, DeepSeek, K3, Gemini | Sonnet/Opus/Fable self-family |
| OpenAI (GPT-6 Sol/Luna/Astra) | Grok, Opus/Sonnet/Fable, GLM local, DeepSeek, K3, Gemini | GPT-6 self-family |
| xAI (Grok) | Opus/Sonnet/Fable, GPT-6 Sol, GLM local, DeepSeek, K3, Gemini | Grok self-family |
| Google (Gemini via AGY) | Grok, OpenAI, Anthropic, GLM local, DeepSeek, K3 | Gemini self-family alone for CF of Gemini-authored infra |
| Moonshot (K3) | Grok, OpenAI, Anthropic, GLM local, DeepSeek, Gemini | K3 self-family |
| Zhipu (GLM) | Grok, OpenAI, Anthropic, DeepSeek, K3, Gemini | GLM self-family |

**Task-family qualification overrides:** language CF must be LANGUAGE-LANES-qualified; FOLK remains GPT↔Claude per folk rubric.

---

## 4. Evidence ledger (promotion / demotion)

### 4.1 Minimum fields per bakeoff cell

| Field | Example |
|---|---|
| date | 2026-07-19 |
| task_family | infra-fix / ui / language / cf-review / orchestrate |
| model | `gpt-5.6-terra` |
| family | OpenAI |
| harness | codex |
| effort | xhigh |
| route | first-party / openrouter / … |
| data_class | public-code |
| corpus_ref | fixed fixture path or PR # |
| outcome | pass/fail + notes |
| cost_estimate | optional |
| latency | optional |
| adjudicator | other family or operator |

### 4.2 Fixed evaluation corpus (minimum five cells)

1. Thin orchestrator decision (route + stop/go)
2. 200–500 LOC infra fix with tests
3. UI component (Practice/Atlas chrome)
4. CF code review of a known PR (exact-head `ask-* --type review`)
5. UA lemma/stress sample with `sources` MCP

### 4.3 Thresholds (starting policy)

| Event | Action |
|---|---|
| New major model release | Mark affected rows **provisional**; run ≥3 relevant cells |
| New xAI ceiling model | Bakeoff vs Astra/Fable before **advisor** seat |
| 2 consecutive fails on validated cell | Demote to provisional; consider deprecated for that task family |
| Validated win on hard cell | May promote within role (not auto-orchestrator) |

Store bakeoff notes under `docs/best-practices/fleet-bakeoffs/` (create when first probe is recorded) or link GH issue.

---

## 5. Escalation ladder (implementation)

```
GPT-6 Luna / Claude Haiku / Gemini 3.8 Flash recon
  → GPT-6 Sol / Opus 5.5 / Sonnet 5 / Grok 4.7 implement (worktree)
    → escalate immediately if security / high blast radius / unclear invariants / multi-architecture
    → otherwise escalate after evidence-backed root-cause attempts fail
      → Astra or Fable (high) for hard advisory judgment
        → orchestrator integrates
        → CF review: other family + task-qualified
```

---

## 6. SuperGrok Heavy and future xAI ceiling

| Entitlement | Treat as | Do not treat as |
|---|---|---|
| SuperGrok Heavy | Verified **capacity** for longer/more parallel Grok workers | Automatic intelligence rank or orchestrator promotion |
| Future xAI Fable/Astra-class | **Candidate** ceiling advisor + hard coder after bakeoff | Auto king of fleet / sole orchestrator |

Re-verify capacity and routing when the subscription plan or API routing changes.

---

## 7. Fallback / substitution

1. Prefer `scripts/config/agent_fallback_substitutions.yaml` + harness table in model-assignment.
2. Never silently lower quality floor on consequential work.
3. Always **NOTE** substitution (model, family, harness, reason) on PR or orchestration artifact.

---

## 8. Quick routing card

```text
Routine code/fix          → GPT-6 Sol high | GPT-6 Luna high when bounded | Sonnet 5 | Grok 4.7
Hard code                 → GPT-6 Sol high | Claude Opus 5.5 high; Astra/Fable advise when needed
Orchestrate stream        → GPT-6 Sol high | Claude Opus 5.5 high (exactly one)
UI / visual product       → K3 explore → Sol/Opus/Grok implement → Astra if systems-hard
UA language                 → Gemini 3.8 Flash High (AGY) + VESUM/sources (3.1 Pro only on explicit request, operator 2026-09-22)
Security/bug CF             → author-family-conditional (Grok/GLM/DeepSeek/Opus/…)
Architecture decision       → Astra/Fable advisory → orchestrator decides
Recon                     → GPT-6 Luna high | Claude Haiku | Gemini 3.8 Flash
```

---

## 9. Change log

| Date | Change | Confidence note | By |
|---|---|---|---|
| 2026-07-19 | Initial scorecard from operator intent + web research + Sol #3588/#3593 | **drafted / provisional** — not full bakeoff-validated | grok/fleet-doctrine-scorecard |
| 2026-07-19 | Add Claude Haiku to recon seat (with Luna / Gemini 3.5 Flash) | provisional | grok/fleet-scorecard-haiku-recon |

**Approval authority:** operator for ceiling-seat changes; orchestrator may update provisional notes and evidence ledger.
