# Fleet role scorecard — living model classification

**Status:** living scorecard (**classification drafted** 2026-07-19 — not all cells fully bakeoff-validated)  
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

## 1. Role → models (operator 2026-07-19 + Sol amends)

| Role | Primary | Secondary / volume | Effort | Confidence |
|---|---|---|---|---|
| Ceiling advisor/designer | Sol, Fable 5 | — | Sol ≥`high` (prefer `xhigh`/`max`); Fable prefer `xhigh` | provisional |
| Accountable orchestrator | Opus 4.8, Terra | — | Opus `high`+; Terra `xhigh` when owning hard streams | provisional |
| General implementer | Sonnet 5, Terra, Grok 4.5 | Gemini 3.5 Flash, K3, Cursor (**pin family**) | `high` default | provisional |
| Hard implementer | Sol, Fable 5 | Prefer Sonnet/Terra first unless known ceiling task | `xhigh` | provisional |
| UI / visual product design | K3 | Sol (systems UX adjudication only) | K3 `high`; Sol `xhigh` | provisional (K3 UI primacy needs bakeoffs) |
| Code/security CF review | **Author-family-conditional** (see §3) | — | `high`+ | provisional |
| Critical CF review | Sol ↔ Fable/Opus **cross-family** | — | `xhigh` | provisional |
| Ukrainian language | Gemini 3.1 Pro (AGY) | LANGUAGE-LANES: codex/claude/grok-4.5 + sources | `high` | provisional (UA primacy AGY; morphology still VESUM-gated) |
| Recon / triage | Luna, Claude Haiku, Gemini 3.5 Flash | — | `medium`–`high`; never sole release | provisional |

**One orchestrator per stream.** Advisors recommend; orchestrator owns terminal disposition.

---

## 2. Model cards (strengths / weaknesses / project notes)

| Model | Strengths | Weaknesses | Route / egress notes | Project seat |
|---|---|---|---|---|
| **Fable 5** | Ceiling coding; long hard tasks; architecture; lead grows with difficulty | ~2× Opus price; safety reroutes possible | Anthropic | Ceiling advisor + hard code |
| **Sol** | Frontier coding/agent claims; synthesis; hard debug; design judgment; multi-agent `ultra` class capabilities in family docs | Expensive; OpenAI-family CF limits if author is OpenAI | OpenAI / Codex | Ceiling advisor; floor `high` |
| **Opus 4.8** | Durable long agentic sessions; orchestration; architecture | Costly as bulk worker | Anthropic | Prefer orchestrator |
| **Terra** | Balanced implementer/orchestrator; strong everyday agentic | Not Sol/Fable ceiling | OpenAI / Codex | Orchestrator + worker |
| **Luna** | Fast recon, cheap mechanical checks | Never sole architecture/security/language/release authority | OpenAI / Codex | Recon |
| **Claude Haiku** | Fast cheap recon/triage on Anthropic lane; good for log/search skim | Never sole architecture/security/language/release authority | Anthropic | Recon (with Luna / 3.5 Flash) |
| **Sonnet 5** | Near-flagship coding at better cost; daily driver agentic | Escalate systemic ambiguity | Anthropic | Default worker |
| **Grok 4.5** | Strong coding agent; token-efficient; good CF review value | Prefer worker/reviewer not sole orchestrator | xAI; SuperGrok Heavy = capacity entitlement (re-verify) | Worker + CF review |
| **Gemini 3.5 Flash** | Fast agentic/coding volume | Not release authority | Google / AGY | Volume worker |
| **Gemini 3.1 Pro** | Multilingual / designated UA language seat; semantic review | Not bulk CRUD default; language outputs need sources | Google / AGY | Language lane |
| **K3** | Long-horizon coding; frontend/visual ideation | Maintainability ≠ demo; Moonshot route/egress | Moonshot | UI + long implement |
| **GLM-5.2** | Deep bug/security; large-context code coherence | Weak UA pedagogy; **LOCAL-ONLY** China-egress | Zhipu / opencode local | Local CF code only; never CI |
| **DeepSeek V4 Pro** | Economical coding and PR review | Not folk/UA cultural gate | Route-dependent (first-party vs openrouter) | Infra/code CF |
| **Cursor Composer 2.5** | IDE-native implementation | **Harness**; pin backing **family** for CF | Cursor | Worker |

---

## 3. Author-family-conditional CF review (required)

Never use a fixed unordered list that can pick the author’s family.

| Author family | Prefer CF reviewers (code/infra) | Avoid as sole CF |
|---|---|---|
| Anthropic (Opus/Sonnet/Fable) | Grok, Sol/Terra (OpenAI), GLM local, DeepSeek, K3, Gemini | Sonnet/Opus/Fable self-family |
| OpenAI (Sol/Terra/Luna) | Grok, Opus/Sonnet/Fable, GLM local, DeepSeek, K3, Gemini | Sol/Terra/Luna self-family |
| xAI (Grok) | Opus/Sonnet/Fable, Sol/Terra, GLM local, DeepSeek, K3, Gemini | Grok self-family |
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
4. CF code review of a known PR (sealed `review-pr`)  
5. UA lemma/stress sample with `sources` MCP  

### 4.3 Thresholds (starting policy)

| Event | Action |
|---|---|
| New major model release | Mark affected rows **provisional**; run ≥3 relevant cells |
| New xAI ceiling model | Bakeoff vs Sol/Fable before **advisor** seat |
| 2 consecutive fails on validated cell | Demote to provisional; consider deprecated for that task family |
| Validated win on hard cell | May promote within role (not auto-orchestrator) |

Store bakeoff notes under `docs/best-practices/fleet-bakeoffs/` (create when first probe is recorded) or link GH issue.

---

## 5. Escalation ladder (implementation)

```
Luna / Claude Haiku / Gemini 3.5 Flash recon
  → Sonnet 5 / Grok 4.5 / Terra implement (worktree)
    → escalate immediately if security / high blast radius / unclear invariants / multi-architecture
    → otherwise escalate after evidence-backed root-cause attempts fail
      → Sol or Fable (xhigh) advisory or hard implement
        → orchestrator integrates
        → CF review: other family + task-qualified
```

---

## 6. SuperGrok Heavy and future xAI ceiling

| Entitlement | Treat as | Do not treat as |
|---|---|---|
| SuperGrok Heavy | Verified **capacity** for longer/more parallel Grok workers | Automatic intelligence rank or orchestrator promotion |
| Future xAI Fable/Sol-class | **Candidate** ceiling advisor + hard coder after bakeoff | Auto king of fleet / sole orchestrator |

Re-verify capacity and routing when the subscription plan or API routing changes.

---

## 7. Fallback / substitution

1. Prefer `scripts/config/agent_fallback_substitutions.yaml` + harness table in model-assignment.  
2. Never silently lower quality floor on consequential work.  
3. Always **NOTE** substitution (model, family, harness, reason) on PR or orchestration artifact.

---

## 8. Quick routing card

```text
Routine code/fix          → Sonnet 5 | Terra | Grok 4.5
Hard code (ceiling)         → Sol | Fable 5 (after mid-tier wall or known ceiling)
Orchestrate stream          → Opus 4.8 | Terra xhigh  (exactly one)
UI / visual product         → K3 explore → Sonnet/Terra/Grok implement → Sol if systems-hard
UA language                 → Gemini 3.1 Pro (AGY) + VESUM/sources
Security/bug CF             → author-family-conditional (Grok/GLM/DeepSeek/Opus/…)
Architecture decision       → Sol/Fable advisory → orchestrator decides
Recon                       → Luna | Claude Haiku | Gemini 3.5 Flash
```

---

## 9. Change log

| Date | Change | Confidence note | By |
|---|---|---|---|
| 2026-07-19 | Initial scorecard from operator intent + web research + Sol #3588/#3593 | **drafted / provisional** — not full bakeoff-validated | grok/fleet-doctrine-scorecard |
| 2026-07-19 | Add Claude Haiku to recon seat (with Luna / Gemini 3.5 Flash) | provisional | grok/fleet-scorecard-haiku-recon |

**Approval authority:** operator for ceiling-seat changes; orchestrator may update provisional notes and evidence ledger.
