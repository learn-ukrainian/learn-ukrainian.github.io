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

## 1. Current role → models (updated 2026-09-28)

| Role | Primary | Secondary / volume | Effort | Confidence |
|---|---|---|---|---|
| Ceiling advisor/designer | Claude Opus 5.5 / GPT-6.1 Sol | — | `high` | provisional |
| Accountable orchestrator | GPT-6.1 Sol, Claude Opus 5.5 | — | `high` | provisional |
| General implementer | GPT-6.1 Sol, Claude Sonnet 5.5 for well-scoped non-security code, Grok 4.7 | GPT-6 Luna for bounded work under a Sol advisory envelope; Gemini 3.8 Flash for well-defined work; K3 (web, UI and backend code only); Cursor (**pin family**). Security-sensitive code authoring goes to Opus 5.5 or Codex Sol; Ukrainian curriculum content stays with sanctioned language lanes (Opus 5.5 for Claude). | `high` by task fit | provisional |
| Polished written deliverables in English | Claude Sonnet 5.5 | Reports, runbooks, write-ups, PR/issue prose, decks, spreadsheets, and design review of pages/artifacts | By task fit | provisional |
| Hard implementer | GPT-6.1 Sol, Claude Opus 5.5 | Escalate hard design judgment to Opus 5.5 / Sol 6.1 | `high` | provisional |
| UI / visual product design | Claude Opus 5.5 / GPT-6.1 Sol | K3 implements the approved design as web/UI code only (Kimi: web, UI and backend coding only — no Ukrainian-language content, no reviews, consults, design or rules) | `high` | provisional |
| Code/security CF review | **Author-family-conditional** (see §3); for security-sensitive diffs (hooks/guards, launchers, credential or secret handling, dispatch admission, sandbox/permission logic), resolve the reviewer with `--risk critical`, which excludes Sonnet 5.5; resolver enforcement at lower risk levels is tracked in #9125 | — | `high`+ | provisional |
| Critical CF review | GPT-6.1 Sol ↔ Opus 5.5 **cross-family** | — | `high` | provisional |
| Ukrainian language | Gemini 3.8 Flash High (AGY) | LANGUAGE-LANES: GPT-6.1 Sol / Claude Opus 5.5 + sources | `high` | provisional (morphology remains VESUM-gated) |
| Recon / triage | GPT-6 Luna, Claude Haiku, Gemini 3.8 Flash | — | Luna `high` with exact owned paths + objective scope ceiling, from a Sol advisory envelope (always required, #9275); others by task fit; never sole release | provisional |

**One orchestrator per stream.** Advisors recommend; orchestrator owns terminal disposition.

---

## 2. Model cards (strengths / weaknesses / project notes)

| Model | Strengths | Weaknesses | Route / egress notes | Project seat |
|---|---|---|---|---|
| **Fable 5.1** | Selectable Claude model | Costly as bulk worker | Anthropic | No advisory, approval or review role (#9583) |
| **GPT-6.1 Sol** | Accountable driving, coding, adversarial review, and hard OpenAI advisory judgment | Same-family review of OpenAI work is not independent | OpenAI / native Codex | Regular driver, coder, reviewer and advisor @ high; designated approver with Opus 5.5 (#9583, #9616) |
| **Claude Opus 5.5** | Hard Claude-lane coding, deep code review and hard advisory judgment | Costly as bulk worker | Anthropic / native Claude or verified Cursor slug | Hard coding, review and advisor @ high; designated approver with Sol 6.1 (#9583, #9616) |
| **GPT-6 Luna** | Fast bounded implementation, recon, and mechanical checks | Never sole architecture/security/language/release authority | OpenAI / native Codex | Bounded worker / recon @ high |
| **Claude Haiku** | Fast cheap recon/triage on Anthropic lane; good for log/search skim | Never sole architecture/security/language/release authority | Anthropic | Recon (with Luna / 3.5 Flash) |
| **Sonnet 5.5** | Well-scoped everyday coding and bug fixes; polished English reports, runbooks, write-ups, PR/issue prose, decks, spreadsheets, design review of pages/artifacts; faster and uses fewer tokens than Sonnet 5 | Weaker than Opus 5.5 on complex, open-ended work; security-sensitive code authoring (hooks/guards, launchers, credentials/secrets, dispatch admission, sandbox/permissions) goes to Opus 5.5 or Codex Sol; Ukrainian curriculum content stays with sanctioned language lanes (Opus 5.5 for Claude); escalate hard judgment to Opus 5.5 / Sol 6.1; designated approval remains separate | Anthropic | Provisional practical worker: after 10 recorded Sonnet 5.5 review or implementation outcomes, adopt or demote with evidence (#9111) |
| **Grok 4.7** | Strong coding agent; token-efficient; good CF review value | Prefer worker/reviewer not sole orchestrator; native Grok never judges | xAI; SuperGrok Heavy = capacity entitlement (re-verify) | Worker; code/infra CF review only as the attested Cursor seat `grok-4.7-high` below critical (#9488) |
| **Gemini 3.8 Flash High** | Multilingual / designated UA language seat; semantic review | Not bulk CRUD default; language outputs need sources | Google / AGY | Language lane (3.1 Pro only on explicit request (operator 2026-09-22)) |
| **K3** | Long-horizon web, UI and backend coding (implementer only) | Maintainability ≠ demo; Moonshot route/egress; never reviewer, consult, advisor, design sign-off or Ukrainian-language seat | Moonshot | UI + long implement |
| **GLM-5.3** | Deep bug/security; large-context code coherence | Weak UA pedagogy; **LOCAL-ONLY** China-egress | Zhipu / opencode local | Local CF code only; never CI |
| **DeepSeek V4 Flash** | Consult-only for non-language work via `ask-deepseek` | Excluded from dispatch, implementation and review; Pro is retired | **First-party only** (`deepseek/` via OpenCode); OpenRouter deepseek refused | Active catalog identity, no worker or reviewer route |
| **Cursor** (`grok-4.7` / `composer-2.5`; Auto) | Mechanical code/infra when free; first-class worker (#6468) | Auto only for a well-defined coding dispatch (owned paths, PASS DoR card; operator decision 2026-09-30); driver seat, review, design, consults and recon pin a concrete model; Auto never formal CF identity; adapter gate #6469 | Cursor harness multi-model | Worker (impl) |

---

## 3. Author-family-conditional CF review (required)

Never use a fixed unordered list that can pick the author’s family.

| Author family | Prefer CF reviewers (code/infra) | Avoid as sole CF |
|---|---|---|
| Anthropic (Opus/Sonnet/Fable) | Grok, GPT-6.1 Sol, GLM local, Gemini | Sonnet/Opus/Fable self-family |
| OpenAI (GPT-6.1 Sol, GPT-6 Luna) | Grok, Opus/Sonnet, GLM local, Gemini; for security-sensitive diffs use `--risk critical`, which excludes Sonnet 5.5 (#9125 tracks resolver enforcement at lower risk levels) | GPT-6 self-family |
| xAI (Grok) | Opus/Sonnet, GPT-6.1 Sol, GLM local, Gemini; for security-sensitive diffs use `--risk critical`, which excludes Sonnet 5.5 (#9125 tracks resolver enforcement at lower risk levels) | Grok self-family |
| Google (Gemini via AGY) | Grok, OpenAI, Anthropic, GLM local | Gemini self-family alone for CF of Gemini-authored infra |
| Moonshot (K3, Cursor Composer) | Grok, OpenAI, Anthropic, GLM local, Gemini (K3 is never itself a reviewer) | K3 / Composer self-family |
| Zhipu (GLM) | Grok, OpenAI, Anthropic, Gemini | GLM self-family |

**Task-family qualification overrides:** language CF must be LANGUAGE-LANES-qualified; FOLK remains GPT↔Claude per folk rubric.

---

## 4. Evidence ledger (promotion / demotion)

### 4.1 Minimum fields per bakeoff cell

| Field | Example |
|---|---|
| date | 2026-07-19 |
| task_family | infra-fix / ui / language / cf-review / orchestrate |
| model | `gpt-6.1-sol` |
| family | OpenAI |
| harness | codex |
| effort | high |
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
| New xAI ceiling model | Bakeoff vs Opus 5.5 / Sol 6.1 before **advisor** seat |
| 2 consecutive fails on validated cell | Demote to provisional; consider deprecated for that task family |
| Validated win on hard cell | May promote within role (not auto-orchestrator) |

Store bakeoff notes under `docs/best-practices/fleet-bakeoffs/` (create when first probe is recorded) or link GH issue.

---

## 5. Escalation ladder (implementation)

```
GPT-6 Luna / Claude Haiku / Gemini 3.8 Flash recon
  → GPT-6.1 Sol / Opus 5.5 / Sonnet 5.5 (well-scoped everyday work and polished English deliverables) / Grok 4.7 implement (worktree)
    → security-sensitive code (hooks/guards, launchers, credentials/secrets, dispatch admission, sandbox/permissions): Opus 5.5 or Codex Sol, never Sonnet 5.5
    → Ukrainian curriculum content: sanctioned language lanes (Opus 5.5 for Claude), never Sonnet 5.5
    → escalate immediately if security / high blast radius / unclear invariants / multi-architecture
    → otherwise escalate after evidence-backed root-cause attempts fail
      → Opus 5.5 / Sol 6.1 (high) for hard advisory judgment
        → orchestrator integrates
        → CF review: other family + task-qualified
```

---

## 6. SuperGrok Heavy and future xAI ceiling

| Entitlement | Treat as | Do not treat as |
|---|---|---|
| SuperGrok Heavy | Verified **capacity** for longer/more parallel Grok workers | Automatic intelligence rank or orchestrator promotion |
| Future xAI ceiling-class | **Candidate** ceiling advisor + hard coder after bakeoff | Auto king of fleet / sole orchestrator |

Re-verify capacity and routing when the subscription plan or API routing changes.

---

## 7. Fallback / substitution

1. Prefer `scripts/config/agent_fallback_substitutions.yaml` + harness table in model-assignment.
2. Never silently lower quality floor on consequential work.
3. Always **NOTE** substitution (model, family, harness, reason) on PR or orchestration artifact.

---

## 8. Quick routing card

```text
Routine code/fix          → GPT-6.1 Sol high | GPT-6 Luna high when bounded (Sol envelope) | Sonnet 5.5 for well-scoped non-security work | Grok 4.7
Security-sensitive code  → Claude Opus 5.5 | Codex Sol (hooks/guards, launchers, credentials/secrets, dispatch admission, sandbox/permissions; never Sonnet 5.5)
Polished English work     → Sonnet 5.5 (reports, runbooks, write-ups, PR/issue prose, decks, spreadsheets, design review)
Ukrainian curriculum      → sanctioned language lanes; Opus 5.5 for Claude (never Sonnet 5.5)
Hard code                 → GPT-6.1 Sol high | Claude Opus 5.5 high; Opus/Sol advice
Orchestrate stream        → GPT-6.1 Sol high | Claude Opus 5.5 high (exactly one)
UI / visual product       → Opus/Sol design → K3 or Sol/Opus/Grok implement web/UI code → Opus/Sol first if systems-hard
UA language                 → Gemini 3.8 Flash High (AGY) + VESUM/sources (3.1 Pro only on explicit request, operator 2026-09-22)
Security/bug CF             → author-family-conditional (Grok/GLM/Opus/…)
Architecture decision       → Opus/Sol advice → designated approval (operator, or Opus 5.5 + Sol 6.1: the non-author's approval when one authored it, both otherwise) → orchestrator integrates
Recon                     → GPT-6 Luna high (Sol envelope) | Claude Haiku | Gemini 3.8 Flash (Sol envelope)
```

---

## 9. Change log

| Date | Change | Confidence note | By |
|---|---|---|---|
| 2026-07-19 | Initial scorecard from operator intent + web research + Sol #3588/#3593 | **drafted / provisional** — not full bakeoff-validated | grok/fleet-doctrine-scorecard |
| 2026-07-19 | Add Claude Haiku to recon seat (with Luna / Gemini 3.5 Flash) | provisional | grok/fleet-scorecard-haiku-recon |
| 2026-10-03 | Opus 5.5 and Sol 6.1 replace Fable / Astra as advisors and designated approvers (both approve, neither the author; operator decides on disagreement); Fable holds no advisory, approval or review role (#9583) | operator decision | claude/impl-9583 |
| 2026-10-03 | Designated approval: Opus 5.5 and Sol 6.1 agreeing; when one of them authored the proposal, the other's approval completes it; any other author needs both; operator decides on disagreement (#9616) | operator decision | claude/impl-9616 |

**Approval authority:** operator for ceiling-seat changes; orchestrator may update provisional notes and evidence ledger.
