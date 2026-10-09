# Per-Task Model Assignment (HARD RULE)

<critical>

**Review admission:** `claude-fable-5` and `grok-4.6` are retired;
`claude-fable-5-1` holds no review role (#9583). Operator decision 2026-10-05 (#9769):
Grok 4.7 is a regular code/infra reviewer at every risk, including critical, through native
`--agent grok --model grok-4.7` and Cursor `--agent cursor --model grok-4.7-high`.
Operator decision 2026-10-07 (#9987): Grok reviewers have no sandbox and are
read-only: tracked-file reads only, with no shell, tests or scripts. Route
execution-dependent reviews to Opus 5.5 or Sol 6.1. Grok review briefs supply
the diff and CI evidence and never ask for execution. Risk admission is unchanged.
Grok never ranks ahead of an eligible, healthy Sol 6.1 or Opus 5.5; native Grok ranks before
the Cursor Grok transport fallback. The resolver chooses an eligible, healthy Sol 6.1 first at low,
medium and high risk; Sonnet is chosen at medium and low risk only when Sol is excluded (for example a
Sol-authored change), and at critical risk Opus 5.5 is chosen for non-Anthropic authors.
Neither transport reviews an xAI-authored change, including the unknown-Auto union {xAI, Moonshot},
or its own subject seat. Verdicts count only with runtime model attestation: native `modelUsage`
reports exactly one admitted model id; Cursor reports its pinned high-effort model itself.
Designated approval remains Opus 5.5 + Sol 6.1, and Kimi is unchanged.
The 2026-10-08 approval admits Gemini as a formal reviewer of low-risk and medium-risk code, and of
Ukrainian work when the reviewer uses the Sources MCP. High-risk and critical review use Opus 5.5,
Sol 6.1, or Grok 4.7. Gemini code review runs directly through native AGY in the exact-head dispatch
worktree, at low or medium risk only; security-sensitive paths raise the risk floor and exclude Gemini.
The source-blind AGY ACP wrapper is not the formal review route. Ukrainian reviews retain the Sources MCP gate.
This interim seat is revisited when Gemini 4 or a code-capable Gemini model is admitted.
`review_scheduler.risk_reviewer_models` admits Opus 5.5, Sol 6.1 and Grok 4.7 at high;
critical eligibility requires the catalog's `critical_review` role. These eligibility gates
apply to automatic ladders, explicit pins, custom ladders and delegate review
admission, including `--force-agent` and budget substitution or retention. DeepSeek is excluded from dispatch and
review, and Sonnet is excluded from critical security review. Historical
capability and transport descriptions below confer no routing permission.

**Gemini may drive epics (2026-10-08 approval):** `start-gemini-driver.sh --epic <lane>` launches a Gemini
epic driver through the shared driver path. The driver default is `gemini-3.1-pro-high`; `gemini-3.8-flash-high`
is also certified. No other Gemini model id is certified for the driver, and another provider's driver refuses a
Gemini model id. This replaces the #9584 driver exclusion. Design input and designated approval stay with
`gpt-6.1-sol` and `claude-opus-5-5` (#9583). Flash remains a strong seat for bounded, well-specified tasks,
including Ukrainian content review under a fixed brief. Task-level Flash rows below are unchanged. Gemini 4 is
re-evaluated when it is generally available.

**Resolver preference:** after hard gates, `review_scheduler.profile_risk_role_order`
prefers primary seats before last resort, then ranks semantic suitability before quality tier; health and quota break ties
within that suitability and tier. YAML rung order is a fallback inventory.
At `medium` and `low`, an eligible Opus seat can lose to Sonnet 5.5, because
Sonnet's roles match earlier in that profile's role order; when both match the
requested role equally, Opus's authority tier wins. The resolver's returned
`suitability_rank` and selection trace are the authority: inspect them rather than
inferring eligibility or priority from rung position or from this text.

Match the EXACT command — not a principle. Memory does not enforce; the dispatch tool does. Established 2026-05-06 after repeated drift on cost discipline.

## Haiku mechanical placement (#9996)

Claude Haiku 5.5 (`claude-haiku-5-5`, existing `economical` tier, native Claude,
`high` fleet effort) handles routine lockfile/pointer/smoke work first, with
Sonnet 5.5 fallback; mechanical classification, extraction and triage
(TypeSafe/Jev pre-LLM triage, CI failure classification and issue/DoR card checks);
and read-only recon/search as a peer of Luna. Deterministic checks still precede
model calls. Resolve catalog roles `routine_mechanical`, `mechanical_classification`
and `readonly_recon`; never pin model IDs in routing consumers.

Haiku dispatches declare the matching `--research-task-family` and narrow
`--owned-path` scopes. Classification and recon require `--mode read-only`.
Admission checks original and resolved pins, owned descendants and input content;
missing typing or unreadable input fails closed. Mechanical-only inputs are plain
UTF-8 without Cyrillic. Never route Ukrainian authoring/review/content, formal
review of record, design/advice/designated approval, security-sensitive code or
driver seats to Haiku. Claude's Ukrainian seat stays Opus 5.5.

Haiku is **not** a bounded implementation worker, even with a Sol envelope:
Anthropic's cited guidance qualifies classification/extraction/routing, not this
fleet's code authoring. Luna/Flash bounded admission and the Sol envelope remain
unchanged. Broader investigation stays with those existing routes. Haiku is not
a blanket budget substitute for stronger seats. Its API base prices are
$0.10/$0.50 per MTok input/output and $0.01 cache read through 100,000 prompt
tokens; above that, $0.50/$2.50 and $0.05 cache read. Native CLI subscription
usage never invents a blended token price. Sources: [Anthropic model overview](https://platform.claude.com/docs/en/models/overview)
and [pricing](https://platform.claude.com/docs/en/about-claude/pricing).

## Canonical model catalog and refresh contract

[Generated seats and ordered review ladders](catalog-routing-tables.md) are the
readable projection of `scripts/config/model_catalog.yaml`. Check drift with
the task-prescribed interpreter and
`-m agents_extensions.shared.skills.drive-epic.scripts.render_catalog_tables --check`;
regenerate with `--write`. Resolver admission, author-family exclusions, risk
floors and runtime health remain binding; these tables grant no permission.

The machine-readable inventory and reviewer ladders live in
`scripts/config/model_catalog.yaml`. It records current preferred models, model families,
quality tiers, strengths, weaknesses, transports, official sources, and risk-specific review
ladders. Provider pickers may expose additional legacy models; CodexBar is a health/quota signal,
not the inventory. The catalog is the union of runtime registry, native CLI catalogs, bridge routes,
Cursor's catalog, and CodexBar health.

The catalog expires after 30 days. Refresh means re-enumerating the live catalogs, checking current
official model documentation, checking local bakeoff deltas, updating `reviewed_on`, and running:

```bash
.venv/bin/python scripts/lint/lint_model_catalog.py
```

Selection order is binding: **independence and hard gates → primary before last resort → semantic suitability → review quality tier → health/quota within
that tier → cost among equivalent fits**. Formal code review uses the catalog's `review_ladders`
and the reviewer resolver for current routine and authority seat order; do not reconstruct a ladder
from historical prose. The Codex orchestrator, advanced coding, Ukrainian authoring, and red-team seats use **GPT-6.1 Sol (`gpt-6.1-sol`) @ high**.
Scouting and bounded repeatable work use **GPT-6 Luna @ high** (max only for an unusually
hard scouting task), always under a complete GPT-6.1 Sol advisory envelope (operator decision
2026-09-30, #9275; see *No direct bounded execution* below). **Operator 2026-09-29 (#9230), advisory effort set to high 2026-09-30 (#9360):** GPT-6.1 Sol is the only Sol and also holds
the former GPT-6 Astra advisory seat. Review, critique and design input use
**Opus 5.5 / Sol 6.1**; Fable and the former Astra seat hold no advisory, approval or
review role (operator decision 2026-10-03, #9583). `gpt-6-sol` and `gpt-6-astra` are not routable.
Token prices under
272K are Sol $2/$10 and Luna $0.10/$0.50 per million input/output tokens.
Cost never lowers the quality floor. An `unhealthy` route is unavailable; `degraded` and `near_cap`
only break ties inside a quality rung. `cursor:auto` is never an acceptable formal-review identity;
Composer is eligible only with its concrete `composer-2.5` model identity. The Cursor review endpoint is
formal only for the models it pins (`grok-4.7` today); other third-party non-Anthropic models Cursor
exposes may be added under the same runtime attestation rules (#9488).

A dispatch is review-typed when it passes any of `--require-review-verdict`,
`--review-attempt`, `--review-profile`, `--review-author-model` or `--review-risk`
(#9538). Review-typed dispatches judge an explicitly requested reviewer by the resolver's
per-candidate eligibility gates; ladder membership is not an allowlist. For the
code profile only, supply `--review-author-model` and `--review-risk` to allow
canonical reviewer substitution when admission or the budget guard requires it.
Every substitution emits a typed note, including with `--force-agent`, which
bypasses budget checks but does not waive reviewer eligibility. Ukrainian
reviews use `--review-profile ukrainian` without these code resolver flags.
A sole eligible cross-family reviewer in pace-only deficit is admitted with a
`REVIEW_BUDGET_RETAINED` NOTE when no valid substitute remains; near-cap, hot,
health, circuit, runtime headroom and subject gates still bind.

### Historical routing evidence

The [Wave 1 scorecard](../../../docs/decisions/agent-rules-routing-history.md)
is historical evidence only; live seats and ladders come from the catalog.

**Unknown-Auto AUTHORS (Cursor Auto) — allowlist-union family (#6955):** when the author ran
`cursor:auto` and reports `resolved_model=unknown`, the resolver attributes the author to the
**allowlist-union family {xAI, Moonshot}** (`grok-4.7` [xAI] | `composer-2.5` [Moonshot]) instead
of unattested-harness-with-quorum. Cursor-authored PRs require a **single** cross-family reviewer
from outside {xAI, Moonshot} (e.g. Claude, Codex/GPT, or GLM under local-only egress),
superseding the #6489 dual-family quorum as the default for unknown-Auto PRs (#6489 quorum remains
valid as fallback history). A declared `author_family` against an auto attestation is a fail-closed
conflict. Resolved-model attestation (or pinned `composer-2.5` / `grok-4.7` authorship) remains
the primary provenance path.

**Designated approval (operator decisions 2026-10-03, #9583, #9616):** a new architecture,
layout, process or policy decision is approved by the operator, or when two frontier families
agree through `claude-opus-5-5` and `gpt-6.1-sol`: when one of them authored the proposal, the
other's approval completes it; a proposal by any other agent (Gemini, Grok, Kimi or another seat)
needs both; if they disagree, the operator decides. Fable and the former Astra seat hold no advisory, approval, review or critique
role and are not a last resort for any of them.

**Claude default model: Opus 5.5 (operator directive 2026-09-22):**

- **Default Claude model and orchestrator seat**: **`claude-opus-5-5` (Opus 5.5)**. `start-claude-driver.sh`
  pins `claude-opus-5-5[1m]` @ `high` unless `--model` / `--effort` (or `LAUNCHER_MODEL` /
  `LAUNCHER_EFFORT`) override it; interactive `start-claude.sh` keeps the last TUI selection. Opus 5.5
  also takes advanced non-linguistic Claude-lane work (architecture, hard coding, deep code review).
- **Review, critique, design input and Ukrainian work**: Opus 5.5 / Sol 6.1 (#9583).
  Orchestration alone never confers approval authority.
- **Effort**: Opus 5.5's API default is `medium`, one level below Opus 5. Orchestrating runs at `high`;
  see `docs/best-practices/fleet-shared-doctrine.md` § Effort guidance for the full ladder.

**Claude Seat Routing: Opus 5.5 first, Sonnet practical (operator directive 2026-09-17;
Sonnet practical seat updated 2026-09-28; orchestration and advanced non-linguistic work
moved to Opus 5.5 on 2026-09-22, above):**

Operationalizes the Claude seat selection within the 2-Tier Formal Review Routing Policy and day-to-day task dispatch:
- **Advanced non-linguistic execution** (architecture, hard coding, deep code review, contested architectural implementation):
  **`claude-opus-5-5` (Opus 5.5)**.
- **Ukrainian-specific linguistic judgment**: Use **`claude-opus-5-5` (Opus 5.5)** whenever Ukrainian language norms and pedagogy are evaluated.
- **Advice and critical review**: **Opus 5.5 / Sol 6.1**. Designated approval (the two agreeing; when one authored the proposal, the other's approval completes it; any other author needs both) remains a separate authority boundary; orchestration alone does not confer it.
- **Everyday routine infrastructure and standard non-linguistic coding**:
  Use **`claude-sonnet-5-5` (Sonnet 5.5)** for well-scoped non-security work to preserve
  frontier rate limits and execution speed. Route authoring of security-sensitive code (hooks/guards,
  launchers, credentials/secrets, dispatch admission, sandbox/permissions) to
  **Opus 5.5 or Codex Sol**.
- **Polished written deliverables in English**: Use **Sonnet 5.5** for reports, runbooks, write-ups,
  PR/issue prose, decks, spreadsheets, and design review of pages or artifacts. Ukrainian curriculum
  content stays with sanctioned language lanes; use **Opus 5.5** for Claude-lane Ukrainian work.
- **Security-sensitive code authoring**: Route hooks and guards, launchers, credential or secret handling,
  dispatch admission, and sandbox/permission logic to **Opus 5.5 or Codex Sol**, not Sonnet 5.5.

### 2-Tier Formal Review Routing Policy (user directive 2026-07-22)

* **Everyday Routine Formal Reviews** (practical roles; Codex and other seats @ `high` effort):
  * **Claude seat**: `claude-sonnet-5-5` (preserves frontier window; fast & efficient). For the `code` and `infra` review profiles, security-sensitive changed paths automatically raise effective review risk to `critical`, even when the author requests low, medium or high. The shared `scripts/review/security_paths.py` classifier includes both rename names and deletions; owned paths can only add coverage. Resolve the target first. The resolver and every code/infra review-typed dispatch collect target changed paths before admission and require the catalog `critical_review` role, preserve cross-family and subject-seat exclusions, and refuse with a reason when no qualified reviewer is available (#9125). Catalog weaknesses remain descriptive.
  * **Codex seat**: `gpt-6.1-sol` @ `high` (standard review)
  * **GLM seat**: `glm-5.3` @ `high` (local-only; advisory `max`)
  * **Gemini seat**: `gemini-3.8-flash-high`. Ukrainian language/content review with the Sources MCP. The 2026-10-08 approval adds low-risk and medium-risk code review; high-risk and critical review use Opus 5.5, Sol 6.1, or Grok 4.7 until Gemini 4 qualifies. Native AGY dispatch enforces resolver admission; the ACP bridge refuses code review.
Every `code` or `infra` review-typed dispatch, including `ask-* --review`, resolves its target before admission:
branch/PR reviews collect literal changes from the base-branch merge-base to the pinned head;
attempts require the record's `target.changed_paths`. An unresolved target refuses with
`REVIEW_TARGET_UNRESOLVED`. Ukrainian-content review attempts use `--review-profile ukrainian`;
they do not collect paths or require a target for this floor. Owned directories
add security coverage with or without a trailing slash, and leading `./` is normalized.
Code-profile `closeout_cli resolve-reviewer` requires a resolved target or an owned path.

* **Complex tasks, deep reviews, and Anthropic advisory consultations**:
  * **Execution**: `claude-opus-5-5` for architecture, hard coding, and deep code review.
  * **Non-binding advisory consultation**: `claude-opus-5-5`. Operator directive 2026-07-31: when requesting
    Anthropic advisory input, use `ab ask-claude --type advisory --to-model claude-opus-5-5`;
    never substitute Sonnet. This consultation does not confer designated approval
    authority and does not satisfy the formal cross-family review gate.
* **Escalatory Advisor / Critical Authority Reviews** (reserved for architecture, security, or design escalation):
  * **Top advisors**: Opus 5.5 / Sol 6.1 for advice, critiques and design input; they hold
    designated approval by agreeing; when one authored the proposal, the other's approval
    completes it, and any other author needs both (#9583, #9616).
  * **Other advisors**: `glm-5.3` @ `max` (advisory) · `grok-4.7` @ `high`. Gemini 3.8 Flash is not an advisor for
    planning or design (operator decision 2026-10-03, #9584); its task-level uses stay as listed in the routing tables. (Kimi: web, UI and backend coding only —
    no Ukrainian-language content, no reviews, consults, design or rules.)
  * Legacy Terra qualification does not authorize a current Codex fallback; use
    the GPT-6 seat that fits the assigned role.
  * `gemini-3.8-flash-high` is currently the strongest lane for task-level Ukrainian content review
    under a fixed brief; this does not extend to planning, design or driving (operator decision 2026-10-03, #9584).
    Flash 3.8 is the live AGY default (operator GO 2026-09-02). The language-lane
    claim is the lmarena 2026-09-02 Text Arena category jump vs Gemini 3.7 Flash
    High: Writing, Literature & Language #7→#3; Multi-Turn #9→#4; Longer Query
    #13→#5; Hard Prompts (English) #23→#6; Hard Prompts #13→#7; Instruction
    Following #11→#9. Text Arena overall #7 (1494) vs Opus 5 High #8 (1492) and
    3.7 Flash High #10 (1491). Agent Arena #14 (+5.94%) vs 3.7 at #32 (+0.84%)
    is supporting agentic evidence, not the Ukrainian-lane reason.
    Operator 2026-09-22: 3.8 Flash High is better than 3.1 Pro; Flash is the deep default.
  * The **fresh-build lesson writer** defaults to **GPT-6.1 Sol @ high** (operator
    2026-09-27), confirmed or reversed by the measured writer selection in the
    pilot (#8425); Gemini's Ukrainian strength above is used for Ukrainian review.


*Everyday routine non-security PRs use practical seats (`sonnet` / Sol @ `high`);
authoring of security-sensitive code goes to Opus 5.5 or Codex Sol, and Ukrainian curriculum
content stays with sanctioned language lanes (Opus 5.5 for Claude).
Ordinary advice uses Opus 5.5 / Sol 6.1 @ `high`.*

**Three-role boundary (operator directive 2026-07-31):** advisory consultation is
non-binding model input (Anthropic → Opus); designated approval authority is the current
identity roster in `operator-expectations.md`; formal review is selected independently by
the canonical reviewer resolver. A routing-table change must never grant approval authority
or count as a formal review.

**Lane updates (user-reported 2026-07-18):**
* **grok**: the lane now offers **grok-4.7** (4.6 is retired and refused, including explicit pins), with selectable reasoning effort
  (`low`/`mid`/`high`) — set effort explicitly per dispatch; code/infra authoring runs `high`; native and Cursor Grok review code/infra with runtime attestation at every risk (see *Review admission*).
* **cursor** (operator 2026-09-22; Auto scope operator decision 2026-09-30, #9274): pass an
  explicit `--model`. `auto` is allowed only for a well-defined coding task — a write-capable
  implementation dispatch with `--owned-path` and a PASS DoR issue card; `delegate.py` refuses it
  otherwise (`cursor_auto_outside_coding_task`). The driver seat, formal or advisory review, design,
  consults, discussions, recon and any unclear or under-specified task pin a concrete approved model:
  `grok-4.7` (mechanical work in the Cursor Models pool: `--model grok-4.7-high`) or `composer-2.5`.
  Do not send Fast, `grok-4.6` or `grok-4.5`. A review of a Grok author uses the Other Models pool,
  for example `--model claude-sonnet-5-5-high`.
  Pools and prices: `fleet-driver-routing.md` § Cursor pools. `cursor:auto` is **never**
  a formal-review identity. **Gate history #6469:**
  workspace-write defaulted to `--mode plan` (read-only) — fixed in the same utilization PR
  so Auto can execute. If a future adapter regression returns plan-only rc=0, substitute with
  NOTE to AGY / Kimi k3-256k (web, UI and backend paths only) / Z.AI GLM. `composer-2.5-fast` stays retired.
* **deepseek**: excluded from dispatch and review. The catalog retains
  `deepseek-v4.1-flash` for identity and historical evidence; it is not an eligible route.
* **pool** (operator 2026-08-06): default pin is **`laguna-s-2.1`**
  (`poolside/laguna-s-2.1` / `poolside/poolside/laguna-s-2.1` via `ab ask-pool`). Do **not**
  default to XS or M.1. Use **`laguna-xs-2.1` only** when the caller explicitly wants the light
  gen-2 seat; **`laguna-m.1` is prior-gen fallback only**. Never invent `s2`/`m2` orthography.
* **kimi** (operator 2026-08-08 / #6468; CTO GO 2026-08-22 / #7140): **keep and use** — first-class, not a cut candidate.
  **Native `kimi` CLI subscription path only** — never OpenRouter as a Kimi worker bus
  (`kimi` / `kimicc` / `kimi-code/k3*` stay `native_kimi`). Split tiers:
  **`kimi-code/k3-256k`** (aliases `k3-256k`) = **everyday fast coding/impl**;
  **`kimi-code/k3`** (aliases `k3`) @ high/max = **complex coding only** (long-context /
  consequential). Do not burn full-K3 on routine queue when k3-256k fits.
  **Kimi: web, UI and backend coding only — no Ukrainian-language content, no reviews, consults,
  design or rules (until further notice).** Every Kimi seat takes workspace-write implementation of
  allowlisted paths only (`KIMI_OWNED_ROOTS`: site UI components, layouts, pages, styles and assets,
  four named `site/src/lib` helpers, `site/*.config.*`, the verified backend packages
  `scripts/{agent_runtime,api,orchestration,ci,fleet_comms,hygiene,storage}` and their tests, CI
  workflows and `.dagger/`); anything not on the allowlist is refused, as is an owned scope
  covering an excluded file. Kimi content must be plain UTF-8 text (no control characters but tab,
  LF, CR) without Cyrillic: an owned file or scope holding anything else (Cyrillic, UTF-16, another
  encoding, a binary) is refused — read in the tree the worker starts from, a reused worktree on
  disk and at its commit or a new worktree's base commit via git plumbing — and so is a finalized
  Kimi diff whose changed files break the rule, before delegate commits it. One gate,
  `refuse_kimi_if_disallowed`, runs first at every entry point on the effective seats and models,
  before any side effect (`scripts/agent_runtime/kimi_admission.py`); a Kimi launch whose
  credential isolation cannot be established is refused.
  Native `kimi` CLI only — never OpenRouter (Wave 1 fold + #7142).
* **glm / Z.AI** (operator 2026-08-08 / #6468; **Flash workhorse 2026-08-26**): **keep and use**
  — **`glm-5.3-flash` is the GLM workhorse** (`--agent glm`, default Flash, OpenCode
  `zai/glm-5.3-flash`). Coding Plan **`glm-5.3`** is explicit `--model glm-5.3` for
  security / large-context coherence (`zai-coding-plan/glm-5.3`; `ask-glm` keeps this pin).
  Rails unchanged: **LOCAL-ONLY**, bridge-diff, never CI/sensitive, **never OpenRouter**.
  No `--agent ox-alpha`. Not LANGUAGE-LANES. Not CF-of-record (same-family zhipu).
  Route everyday local-rail code/implement work here when fit allows.
* **OpenRouter** (operator 2026-08-08): **mainly Pool + Gemma access.** Can reach more models;
  **we do not need to** — prefer native/first-party seats. Not a general multi-model bus.
  **Never** a Kimi K3 worker bus (`kimi` / `kimicc` / `kimi-code/k3*` stay `native_kimi` only).
  Gemini (AGY) / GLM subscribed seats never OpenRouter.
* **Subscriptions policy (operator 2026-08-08):** **do not trim seats to “simplify.”** Fix
  **utilization** (no-idle free pools, timed pauses with return-at). Cut only after sustained
  measured zero use *and* no differentiator need — default is keep Cursor, DeepSeek Flash,
  Claude, Codex, AGY, Grok, **Kimi**, **Z.AI/GLM**, Pool.

| Task | Tool + model |
| --- | --- |
| Inline code edit ≤5 LOC, fixing a CI failure I just caused | Me, current model |
| Claude-side ROUTINE work — formulaic reviews, config/fixture edits, monitoring-only sessions, mechanical English wiki fixes, mechanical PR babysitting; polished English reports, runbooks, write-ups, PR/issue prose, decks, spreadsheets, and design review of pages/artifacts | **Sonnet 5.5** (user 2026-07-07: "use Sonnet more often for routine work") — dispatch `--model sonnet` / Sonnet session. Route authoring of security-sensitive code (hooks/guards, launchers, credentials/secrets, dispatch admission, sandbox/permissions) to **Opus 5.5 or Codex Sol**, not Sonnet 5.5; Claude-lane Ukrainian curriculum uses **Opus 5.5**. Reserve the frontier Claude tier (Opus 5.5 / whatever frontier model is active) for judgment work: architecture, adversarial review, pedagogy, hard bugs. **Route by TIER-FIT, not model name — the Claude lane rotates** (Fable 5 was temporary). **Motive = SAVE THE FRONTIER WINDOW** (user-confirmed 2026-07-07): if Sonnet is busy, QUEUE routine work or reroute to agy/codex — do not burn the frontier window on it. |
| Code change >5 LOC, mechanical / pattern-applying / fixtures | use **Codex Sol @ `high`** for accountable coding and broader integration, or **Claude Opus 5.5 @ `high`** for hard Claude-lane coding. Clearly bounded work with exact owned paths and an objective scope ceiling uses **Luna @ `high`**. Cursor `grok-4.7-high` is a mechanical/ordinary alternative when fit and live capacity favor it; `auto` only for a well-defined coding dispatch (owned paths, PASS DoR card), never as a model identity. Escalate consequential ambiguity to Opus / Sol @ `high` for advice while Sol retains disposition. |
| Code Review (PR diff) | Low-risk and medium-risk defaults include native AGY Gemini alongside Sol 6.1 and Sonnet 5.5, subject to resolver ordering and cross-family eligibility. High-risk and critical reviews use Opus 5.5, Sol 6.1, or Grok 4.7; security-sensitive paths exclude Gemini. Revisit Gemini eligibility when Gemini 4 qualifies. Resolve the target first with `closeout_cli target` in the same state file (or supply `--owned-path`); code-profile resolution without either refuses. Resolve with `.venv/bin/python -m scripts.review.closeout_cli ... resolve-reviewer --author-model <exact-model> --review-profile code --risk <low\|medium\|high\|critical>`. When the diff governs a seat's adapter or reviewer hooks, also pass repeatable `--owned-path` (inferred when unambiguous) or `--subject-seat` / `--subject-family`; that seat is excluded and the trace records why. Ambiguous paths require the explicit argument. The resolver applies hard filters first, then suitability for the review profile and risk, then the #5293 quality prior within equally suitable candidates. A lower tier can precede an eligible higher tier when it is more suitable; ladder order breaks remaining ties. Execute the returned `invocation`; preserve its concrete model, family, `route`, `transport`, health trace, and `requires_silence_timeout` receipt. Do not hand-pick Flash while an eligible higher-tier reviewer remains usable. |
| Content Review with VESUM verification (load-bearing) | **LANGUAGE-LANES RULE binds (operator 2026-09-27): claude / codex (GPT) / agy (Gemini) only** — dispatch the reviewer on one of these three with the `sources` MCP (`verify_words`, `query_cefr_level`, `check_russian_shadow`). ~~deepseek-v4-pro default (#4358)~~ RETIRED for language seats by the same order; the #2112/# 4358 validation history stands as evidence only |
| Wiki / content writing · content / pedagogy / factual **review** | agy — `delegate.py dispatch --agent agy` (write) or `ab ask-agy --to-model gemini-3.8-flash-high` (review default for routine and deep; `gemini-3.1-pro-high` only on explicit request). **Use agy actively here** (user 2026-06-24): the §7/factual-fabrication fence is LIFTED (cleared 2026-06-13 — it grounds in the `sources` MCP and abstains "NO SOURCE"), and its pedagogy/CEFR review is strong — it LED the 2026-06-24 practice-hub panel. **Metered** → be cost-aware, but do NOT under-use it where it's strong. NOT for cross-file architecture / security-concurrency / auth-heavy git / mass-mechanical (→ codex/claude). Caveat: agy `--data` truncates large/binary attachments → paste trimmed content or use codex `--data`. |
| Ukrainian CONTENT (authoring · russicism/quality review) — **we AUTHOR UK content, we do NOT translate EN→UK** | Written in Ukrainian, immersion-first, grounded in VESUM/`sources` MCP. **Per-profile authoring — BAKEOFF-BACKED (2026-07-04, `audit/2026-07-04-uk-writing-probe/`, deterministic VESUM + russian-shadow, 5 candidates):** all of codex (historical benchmark models: gpt-5.6-terra and gpt-5.5)/agy/claude/deepseek/cursor wrote **0-russicism, 95-100%-VESUM** content on all 3 profiles → **gpt-5.5 is not uniquely best; it can and should delegate.** A1-A2 English-support → **agy** (best immersion teaching-voice) ≈ **codex**; B1-C2 pure → **codex ≈ agy ≈ claude**. **Seminars — FACT-CHECKED (2026-07-04, `audit/2026-07-04-uk-writing-probe/SEMINAR-SCORECARD.md`; tool-backed vs uk.wikipedia + VESUM, cross-verified by an independent 3-family review codex/agy/deepseek):** the probe can't rank seminar content (all clean), so the «Веснянки» sample was fact-verified. **Writers → codex + claude + agy** (all factually clean, mutually cross-family). **deepseek + cursor are NOT seminar writers:** deepseek made 1 hard error (царинні conflated with юр'ївські cattle-drive songs — confident scholarly specificity that was wrong; it conceded on review), cursor made 2 (веснянки «від хати до хати» = over-generalised риндзівки/волочебні; «мелодії легкі, м'які, співочі» = inverted musicology). **Seminar review → claude / codex / agy ONLY (LANGUAGE-LANES RULE, operator 2026-09-27; the former deepseek seat is retired — its царинні hard error stands as supporting evidence)**, **always paired with a source-enforced fact-check gate** (`seminar-content-review` skill + `sources` MCP) — never a bare LLM pass. FOLK pairing stays GPT↔Claude per `docs/folk-epic/folk-review-rubric.md`. **Lesson: "sounds scholarly" ≠ "is accurate" — verify confident specificity, don't trust it.** **Review (russicism/surzhyk/CEFR):** one of the three language lanes + `sources` MCP (`verify_words`, `check_russian_shadow`, `query_cefr_level`); agy strong here. ⚠️ **cursor: EXCLUDED from all language seats (LANGUAGE-LANES RULE)** — its bakeoff history (non-canonical apostrophes U+2019, text-dependent russicism «перекатні») stands as supporting evidence only. **Never pool/glm/gemma/kimi/deepseek for UK content either** (same rule). |
| Adversarial review of design / ADR / architecture / code — the **Claude reviewer seat** | **Prefer IN-SESSION INLINE for cost** — the interactive orchestrator reads the artifact, verifies claims, writes the verdict + fix notes on the main quota (cheapest path; economics below). Use Opus / Sol; Fable is not a reviewer (#9583). Dispatching Claude (`claude -p` / `--agent claude` / `review-deep` / an `Agent` review subagent) **is permitted when it adds value or inline isn't feasible** — the `-p` sunset was cancelled (user 2026-06-22). For routine reviews still prefer inline or a non-Claude lane; reserve dispatched Claude for catches that need it. Context heavy → DEFER to the next interactive session, or dispatch if it must clear now. |
| Q&A or single-shot Ukrainian language/content review without commit | `ab ask-codex` / `ab ask-agy --to-model gemini-3.8-flash-high` for routine AND deep (top AGY default; `gemini-3.1-pro-high` only on explicit request; gemini-cli retired → agy) |
| Live web fact-check (current version / pricing / URL & citation currency, "is this API still live") | **opencode + lightpanda-MCP HARNESS capability — any opencode-hosted model browses** (kubedojo-verified incl. deepseek); it is NOT model-specific. Route by fit: `ab ask-pool` (poolside.ai, **free**) · `ab ask-glm` (⚠️ LOCAL-ONLY, China-egress) · `ask-deepseek` is consult-only for non-language questions; DeepSeek is excluded from dispatch and review. |
| Search / grep / "find me X" across files | Native Codex subagent of a `gpt-6.1-sol` parent (default `gpt-6-luna` @ `high`), with explicit owned paths and an objective scope ceiling set by that parent; a delegated Luna dispatch needs a Sol advisory envelope (`--advisory-task`) |
| Status check on running dispatches | Monitor API curl, never inline file scans |

These allocation rules apply to the accountable orchestrator. If lead work does not match
row 1, dispatch it to the appropriate worker. A bounded worker implements its assigned packet
within its owned paths; it does not redispatch merely because the packet exceeds the inline
threshold. Further delegation requires authorization. Worktree and completion gates still apply.

**Use agy more (user 2026-06-24):** route content / wiki / pedagogy / factual **review** + bounded scripts / fixtures / migrations / docs-near-code to **agy** by default (bounded non-Ukrainian agy work is the bounded fallback and needs a Sol advisory envelope, operator decision 2026-09-30) — its §7-fabrication fence is lifted (cleared 2026-06-13) and its pedagogy/CEFR review is strong (it led the 2026-06-24 practice-hub panel). It is **metered**, so be cost-aware, not absent — don't under-use it where it's strong. Keep cross-file architecture / security-concurrency / auth-heavy git / mass-mechanical on codex/claude. Confirm its model via `ab check-model` / `--help` (changes often; the bridge labels it Gemini-3.5-Flash-High, panels route `--to-model gemini-3.8-flash-high`, Pro only on explicit request).

**Read-only dispatch cwd (#8516, #9094):** `delegate.py dispatch --mode read-only` creates a disposable detached dispatch worktree for every lane when neither `--cwd` nor `--worktree` is given. `--cwd <primary-checkout>` explicitly opts into running on the primary checkout; `--worktree <primary-checkout>` is refused. The agy runner checks that its child settles into the selected cwd at startup (`cwd_unpinned` failure otherwise), because agy headless has no enforceable read-only mode. The post-run checkout-mutation guard (#8516 AC-02) fails any lane's read-only task on a new/modified/deleted path, tracked or untracked, that is not recognized runtime/build noise.

**agy / gemini-flash worker briefs (#5737 — binding):** when AGY runs as a **worker**
(default Flash pin `gemini-3.8-flash-high` for routine and deep, Pro only on explicit request), it receives a
**complete task brief** — one shippable unit (typically one feature / one PR) with
acceptance criteria stated up front. It does **not** self-decompose an open-ended objective
into serial micro-PRs. The accountable orchestrator owns sequencing and fan-out; leaving Flash
to invent its own merge cadence re-starves CI (2026-07-24 queue incident). Catalog membership
in `orchestrator_seats` does not license a Flash worker to plan, design or orchestrate large projects
(#9584), nor self-orchestration of implementation work. Driving an epic is a separate seat: it runs only
through `start-gemini-driver.sh` (2026-10-08 approval), and AGY compaction loses orchestration state, so
the driver re-verifies lease and hydration after compaction.
Brief shape: `workflow.md` § Dispatch brief unit.

**Writer routing refinement (user-confirmed 2026-07-07):** general content writing runs on **codex + agy** (agy = the standout A1-A2 immersion teaching voice per the 2026-07-04 bakeoff — do not forget it exists); the Claude window is SAVED for judgment work (architecture, adversarial review, hard bugs — codex is the primary coder, not Claude). The **V7 PIPELINE writer seat is separate**: it stays `claude-tools` because that seat is in-harness TOOL-CALLING fit, not prose (codex-tools emitted `tool_calls=0`); after any Claude-model rotation, spot-check ONE module before the next batch.

**Native usage pace/reserve (width truth source):** run
`python -m scripts.fleet.usage show` or `python -m scripts.fleet.usage json`.
The default reads the same warm Monitor `/api/state/routing-budget` snapshot;
`refresh` or `--fresh` performs blocking native probes. Inspect `source`,
per-row `freshness` and `age_s`; unavailable data is unknown capacity.
Subscription rows expose `remaining_pct` and compatibility `codexbar` metadata
(`pace_summary`, `weekly_pace_delta_pct`, `will_last_to_reset`) where observed,
and each allotment window line is followed by a `pace:` line (used-vs-expected
delta and whether the window will last to reset) when the window is
computable. Read pace per lane before widening fan-out: a deficit is visible
pace, projected to run out before reset, and more than 2 points ahead of pace
(near_cap ≥ 90% unchanged) — shed that lane to one with reserve; negative delta
means headroom. `capacity_pick` renders
the same reading in its `pace` and `will_last` columns. The AGY lane's quota
is the Gemini subscription row: `PROVIDER_TO_LANE` keys the probe under
`gemini` (`agy` CLI `/usage`, never Google quota APIs) and
`RETIRED_AGENT_ALIASES` routes `gemini` dispatch to `agy`; `capacity_pick`
mirrors that row onto the `agy` lane (`quota:gemini` note). Prepaid API means
OpenRouter + DeepSeek only. Missing pace is partial evidence, never a guessed
reserve. Prepaid DeepSeek uses USD thresholds from `agent_budgets.yaml`;
OpenRouter is a funding account with `pick: n/a`. A key spending cap is
distinct from account balance. Run
`python -m scripts.fleet.usage doctor` for credential path/env presence only.
OpenRouter account balance requires a management key (env, OpenCode's explicit
`openrouter-management` entry, or `~/.secrets/openrouter-management.key`;
`~/.secret/…` is the legacy fallback).
The CLI reports `balance: needs management key` when it cannot read that balance.
Follow-up naming debt: retain `CODEXBAR_*` environment and `codexbar` payload keys
for compatibility; a global rename is outside this change.

**Model-by-harness intent:** operator-authorized Astra/Grok orchestration from Hermes
keeps model family, model ID, harness, and functional role as separate axes. Hermes
is the harness, not a model family or an independent review identity. Resolve the
current supported model and launcher route from the live catalog and launcher help;
this intent does not introduce new model pins. Retiring the individual DeepSeek ACP
transport is not a blanket ban on the Hermes harness. Preserve one driver per stream,
existing stream ownership, dispatch quality floors, and toolful outside-author-family
exact-head review with required CI before merge. A harness change never permits a
competing lease or makes same-family review independent. Required catalog changes
need advisor review; do not speculate new pins.

Kimi K3 is a separate
native `kimi` CLI subscription lane (`kimi-code/k3`, max effort, tool/image/video input; do not publish a
context-size claim until the native provider documents it). **Never OpenRouter** for Kimi workers.
API-billed lanes such as DeepSeek may be absent from CodexBar by design; absence is unknown
headroom, not unavailability. Shed load only to models that meet the same task-risk quality floor.

**Kimi lane:** native `kimi` CLI subscription path only — never OpenRouter, never an
OpenRouter-for-subscribed-models fallback. Dispatch/native default is **`k3-256k`** (`kimi-code/k3-256k`,
everyday coding/impl, no forced effort — operator 2026-08-13). Use K3 (`kimi-code/k3`, high/max
effort) for consequential web, UI and backend coding and long-context debugging within
the allowlisted paths. Use `k2.7-coding` / `k2.7-coding-highspeed` only as legacy routine/bulk pins. Do not demote K3 merely
because the cheaper model exists; risk and fit establish the quality floor first. Kimi is Moonshot
family. Composer 2.5 is Cursor-trained from a Kimi K2.5 checkpoint, so conservatively treat Composer
and Kimi as the same Moonshot independence family. Neither is a Ukrainian factual/folk gate.
K3 is **not a QG judge**; the standing judge pairing remains Gemini↔GPT.
**Supersession (Kimi admission policy):** K3 is a top coding model but is in no review ladder,
advisory panel or consult (web, UI and backend coding only). This supersedes the 2026-07-17 directive
that made it eligible for automatic cross-family code-review ladders; local bakeoffs may still
refine its implementation ordering.

## Fleet topology — orchestrator · advisor · workers (user directive 2026-07-11; multi-orchestrator 2026-07-21)

Standing role assignment for orchestrated sessions (names rotate; route by the role, not the label).
Machine-readable pins: `scripts/config/model_catalog.yaml` → `orchestrator_seats` + `formal_cf_defaults`.

- **Orchestrator seats (fleet-comms stream #5512 / #4707)** — any of these may own a cold-start /
  drive-board loop (prioritize → delegate → request CF → merge-in-lane); `agy` drives through
  `start-gemini-driver.sh` (2026-10-08 approval). Do **not** run worker-level
  implementation on the orchestrator seat — delegate it (>50 LOC non-test, mechanical, fixtures, or
  anything parallelizable → a worker). **Codex was re-added as a driver seat** (user 2026-07-23),
  reversing the 2026-07-22 removal: HydrationCapsuleV1 makes its rollover cost acceptable. Machine
  authority: `model_catalog.yaml` → `orchestrator_seats` (lint: #5642).

  Human-readable summary (pins must match the marked projection below):

  | Seat | Default (loop) | Escalate (deep) | Notes |
  | --- | --- | --- | --- |
  | **claude** | `claude-opus-5-5` @ high (operator 2026-09-22; launcher pins `claude-opus-5-5[1m]`). Opus 5.5 executes hard Claude-lane coding, architecture, and deep code review where relevant | **`gpt-6.1-sol` @ high** | Escalation is CROSS-FAMILY: Claude is a target, not an escalator. Opus / Sol take advice and Ukrainian judgment. Orchestration alone does not confer approval authority |
  | **codex** | `gpt-6.1-sol` @ high | **`gpt-6.1-sol` @ high** | GPT-6.1 Sol orchestrates, does advanced work, and handles ordinary advice (#9275 envelope unchanged). Luna @ high scouts. Never co-owns a live lease |
  | **grok** | `grok-4.7` @ high | same SKU | Cursor **explicit** `grok-4.7` = availability fallback, not quality escalate |
  | **agy** | `gemini-3.8-flash-high` @ high | **`gemini-3.8-flash-high` @ high** | Driver seat through `start-gemini-driver.sh` (2026-10-08 approval): the driver defaults to `gemini-3.1-pro-high` and also accepts `gemini-3.8-flash-high`. As a worker it is not a self-orchestrating implementer; Flash worker briefs must be complete (#5737); Flash is the worker default and deep pin (2026-09-22: 3.8 Flash High outperforms 3.1 Pro) |
  | **cursor** | `grok-4.7` @ high (launcher pin `grok-4.7-high`; `composer-2.5` also allowed; Auto only for a well-defined coding dispatch, operator decision 2026-09-30) | **`gpt-6.1-sol` @ high** | Driver seat never runs Auto; driver-of-record requires attested `resolved_model`; unknown-Auto authors resolve to union family {xAI, Moonshot} (single CF reviewer outside union supersedes #6489 quorum); concurrency 1 |

  <!-- fleet-roster-projection:begin orchestrator_seats -->
  | seat | model_id | effort | escalate_model_id | escalate_effort |
  | --- | --- | --- | --- | --- |
  | agy | gemini-3.8-flash-high | high | gemini-3.8-flash-high | high |
  | claude | claude-opus-5-5 | high | gpt-6.1-sol | high |
  | codex | gpt-6.1-sol | high | gpt-6.1-sol | high |
  | cursor | grok-4.7 | high | gpt-6.1-sol | high |
  | grok | grok-4.7 | high | grok-4.7 | high |
  <!-- fleet-roster-projection:end orchestrator_seats -->

  **Escalate when:** deep single-shot, architecture, hard multi-file judgment, high-stakes synthesis —
  not for routine queue grind. Machine fields: `escalate_model_id` / `escalate_effort` /
  `escalate_when` on each seat in `model_catalog.yaml`.

### Cursor driver seat — identity contract and attestation (#6952 / #6955)

* **Auto scope (operator decision 2026-09-30, #9274):** Cursor Auto runs only a well-defined coding task: a dispatch typed `--research-role implementation` in a write-capable mode with `--owned-path` and a PASS DoR issue card that is not review-typed. A missing or any other role is unclassified and refused. `scripts/delegate.py` admits it only on that positive evidence and records the admission; the Cursor adapter refuses Auto without it and in `plan` or `ask` mode. The driver seat (`start-cursor-driver.sh` → `scripts/lib/launcher_core.sh`), interactive Cursor sessions launched through the same launcher (not a typed implementation dispatch, so no Auto exception; default `grok-4.7-high`), and ACP consults and discussions (`acpx-cursor-shadow`) pin `grok-4.7` or `composer-2.5`. A review on Cursor runs the approved concrete model the reviewer resolver selects (`closeout_cli resolve-reviewer`), never Auto. Catalog: `orchestrator_seats.cursor.model_id: grok-4.7`, `auto_scope: write_implementation_dispatch_with_green_dor`.
* **Driver-of-record requires attested `resolved_model`:** Cursor is an orchestrator seat pinned to the concrete `grok-4.7` (launcher `grok-4.7-high`). A Cursor driver session still requires an attested concrete `resolved_model` extracted from the run (via headless telemetry in `scripts/delegate.py` / `scripts/agent_runtime/adapters/cursor.py`). Driver-of-record can never be unattested or unknown-Auto.
* **Unknown-Auto resolves to allowlist-union family {xAI, Moonshot}:** When an admitted Auto coding dispatch (`cursor:auto`) reports `resolved_model=unknown`, its identity resolves to the **allowlist-union family {xAI, Moonshot}** (`grok-4.7` [xAI] | `composer-2.5` [Moonshot]) instead of unattested-harness-with-quorum.
  * **Cursor-authored PRs:** Require a **single** cross-family reviewer from outside {xAI, Moonshot} (e.g. Claude, Codex/GPT, or GLM under local-only egress). This supersedes the #6489 dual-family quorum as the default for unknown-Auto PRs (#6489 quorum remains valid as fallback history).
  * **Cursor-as-reviewer:** Eligible only against authors outside {xAI, Moonshot}.
  * **Validity condition:** The union bound holds strictly while the Auto allowlist contract holds (~30-day catalog refresh; lint enforces the pair). Allowlist rotation invalidates the bound (refresh first).
* **Auto allowlist and ~30-day refresh contract:** Cursor Auto is permitted only for the coding-dispatch scope above and only within an explicit allowlist (currently `grok-4.7` and `composer-2.5`), refreshed under the catalog's ~30-day freshness contract without freezing a single SKU.
* **Family attribution for CF checks:** When `resolved_model` is attested, cross-family review checks use the **attested** model family (e.g. Cursor `composer-2.5` = Moonshot family, Cursor `grok-4.7` = xAI via Cursor). When `resolved_model=unknown`, the union family {xAI, Moonshot} applies.
* **Operating constraints:** Concurrency is 1 (the driver session is the Cursor lane; do not dispatch `--agent cursor` from inside the session). Canonical driver = launched TUI session (`start-cursor-driver.sh`, #6956); GUI Cursor IDE is human supervision only. Do not vendor pstack, Graphite, Benny, or N-implementation arenas.

## Orchestration operating pattern (operator 2026-07-26 — binding)

The knowledge-monopoly + quota-burn cycle (only the Anthropic frontier seat holds the whole
system; letting it drive daily exhausts the weekly in ~2 days; cheaper drivers then degrade
the system until it returns) is broken by ROLE SPLIT, not by a better single driver:

* **Daily driver: `grok-4.7`** — owns the epic loops (dispatch, babysit, settle, reap,
  re-fire) under the mechanical rails (evidence-mandatory reviews, lease lifecycle,
  merge/stamp guards, delegate origin-sync). Operator-rated the best price/quality
  orchestrator currently available.
* **Claude driver seat: `claude-opus-5-5` @ `high`** (operator 2026-09-22) — what
  `start-claude-driver.sh` launches when a Claude session drives an epic. Same
  dispatch-heavy discipline as below; it is not the advisor and holds no approval authority.
* **Summoned judgment:** Opus 5.5 / Sol 6.1. Keep consultations bounded and read-only; ordinary
  review is independent exact-head work, not an advisory panel.
* **Understudy trial: `glm-5.3`** — sanctioned as a BOUNDED driver trial on one epic under
  the standard capsule/handoff contract (operator 2026-07-26; untested as driver, repeatedly
  the sharpest cheap seat on code review). Evaluate against the same rails; report before
  widening.
* **Codex is a named alternate driver**, using Sol @ `high` for the loop and advanced coding.
  Bounded implementation defaults to Luna @ `high` under a Sol advisory envelope; adversarial reviewer effort is Sol @ `high`.
  Ordinary advice uses GPT-6.1 Sol @ `high`. The #9275 envelope remains mandatory.
* Session-cadence seats stay unchanged for kimi (capable, slow), agy (compaction loses
  orchestration state; a Gemini driver re-verifies lease and hydration after compaction), gemini CLI (retired → agy).

  The review of record is one cross-family review on the pushed branch before
  PR creation: toolful `ask --review --branch <name>` or detached dispatch
  (drive-epic §6). Compare task pin/checkout SHA with the pushed tip and require
  qualified APPROVE; ask stdout is reply text. Continue expiry on the same
  task/nonce, never redispatch. Then create the PR, bind with
  `record_cf_verdict.py`, and require same-head CI.
  **Shielded formal CF
  (`review-pr`, sealed multi-GB `lu-review-*` / `shielded-reviews` isolation) is
  RETIRED (operator 2026-08-07)** — fail-closed in the CLI. Do not reintroduce
  it. Lightweight agent review + green CI + merge + worktree/temp cleanup is
  the path. `ask-<lane> --review --branch <name>` uses the headless native CLI
  with tools, never tool-less ACP (operator 2026-08-23, #7155).

  **Historical projection only — not the live CF gate (#7017).** The table
  below mirrors `scripts/config/fleet_communications.yaml`'s endpoint
  registry, which that file's own header marks legacy: "Sealed formal CF
  always goes through review-pr" — the very path retired above — and "keep
  these endpoint booleans synchronized for legacy endpoint-status consumers;
  reviewer_resolver never reads this copy." `scripts/lint/lint_fleet_roster.py`
  still pins this block byte-exact against that YAML for those legacy
  consumers (`scripts/api/fleet_router.py`, `scripts/fleet_comms/endpoints.py`)
  — keep it in sync, do not delete it — but do not read it as today's review
  routing. For the live formal resolver use the "Code Review (PR diff)" row
  above (`closeout_cli resolve-reviewer`, backed by `model_catalog.yaml` →
  `review_scheduler.endpoints`); for the everyday review of record use the
  lightweight `ask-<lane>` path just above.

  <!-- fleet-roster-projection:begin formal_review_eligible -->
  | endpoint | formal_review_eligible |
  | --- | --- |
  | agy | false |
  | claude | true |
  | codex | true |
  | cursor | true |
  | gemini | false |
  | glm-local | true |
  | grok | true |
  | kimi | false |
  <!-- fleet-roster-projection:end formal_review_eligible -->

* **Advisor = `gpt-6.1-sol` @ `high` (on-demand, NOT a standing worker).** The
  `execution_routing.sol_advised_bounded` catalog route makes the Sol advisor (`gpt-6.1-sol` @ high) produce a bounded
  envelope containing the task contract, exact owned paths, maximum changed-file
  and non-test-LOC ceilings, constraints, risk boundaries, acceptance evidence,
  and escalation triggers. The advisory pin is `high`. The advisor runs read-only with
  `delegate.py dispatch --advisory-role bounded_advisory_envelope --advisory-binding <digest>`,
  where the digest is the worker dispatch's `--print-advisory-binding` output.
* **Bounded execution advised by the Sol advisor (`gpt-6.1-sol` @ high):** with that envelope complete, dispatch
  `gpt-6-luna` @ `high` for bounded implementation or investigation with
  `--advisory-task <advisor task id>`. The worker must
  follow the envelope rather than re-decide its contract, and must escalate
  any owned-path or scope-ceiling overrun, consequential architecture, security,
  release, high-risk go/no-go, unresolved consequential ambiguity, broader
  integration, or final disposition.
* **No direct bounded execution (operator decision 2026-09-30, #9275):** every
  bounded-worker dispatch — `gpt-6-luna`, and the `gemini-3.8-flash-high` fallback
  unless it is classified Ukrainian authoring or review (`--research-task-family
  ukrainian-authoring|ukrainian-review`, or read-only `--review-profile ukrainian`) —
  needs a complete envelope from a finished `gpt-6.1-sol` advisor task, bound to that
  dispatch's arguments and prompt text. This covers bounded implementation/investigation, recon, checks,
  and test/log triage alike; token cost is accepted. `delegate.py` refuses a dispatch
  without it (`BOUNDED_ENVELOPE_REQUIRED`), also after a budget substitution, records the
  envelope's result path and digest in the task record, and fails the worker at finalize
  (`advisory_ceiling_exceeded`) when it exceeds the envelope ceilings; the ceilings are
  a completion gate checked after the worker exits, not a runtime limit. Missing or
  conflicting classification counts as bounded. Work that has no envelope, or is too
  broad for a ceiling, routes to Sol @ `high` instead, with judgment from
  the Sol advisor (`gpt-6.1-sol` @ high) when needed.
* **Routine lockfile, pointer and smoke tasks** take no advisory seat (core `p2-retired`),
  so they take a non-bounded route — `claude-sonnet-5-5`, or Sol @ `high` — never a
  bounded worker without an envelope.
* **Native Codex subagents** (`agents_extensions/codex/config.toml` defaults them to
  `gpt-6-luna` @ `high`) are spawned in-session by a `gpt-6.1-sol` parent and run under
  that parent's own contract: the parent is their advisor and sets their owned paths and
  ceilings. They are not `delegate.py` dispatches and carry no separate envelope.
* **Review boundary:** Codex advisor and worker seats are both OpenAI-family. The Sol advisor's
  output never satisfies the independent cross-family review gate.
* **Workers = every other lane** — `gpt-6-luna` @ `high` (Codex bounded work / scout),
  `gpt-6.1-sol` @ `high` (Codex broader coding / red-team),
  `cursor`, `kimi`, `pool` (**Laguna family exact IDs:** default **`laguna-s-2.1`** gen-2 S; light **`laguna-xs-2.1`** gen-2 XS; fallback only **`laguna-m.1`** gen-1 — never invent s2/m2 orthography),
  `gemma`, `glm` (LOCAL-ONLY), plus non-orchestrating use of the seats above. They do the build /
  implementation / mechanical / review work. Keep lanes busy; queue rather than idle.
  **AGY/gemini-flash as worker (#5737):** always dispatch with a complete brief (one shippable
  unit + acceptance criteria). Do not hand Flash an epic-sized objective and expect it to
  sequence its own micro-PRs — that pattern starved the CI queue even after structural fan-out
  cuts (#5735). Soft merge-cadence check for orchestrators: no lane should routinely land
  **>5 PRs/day against one feature area**; prefer one shippable PR over a spray of intermediates
  (expectation only — not an automated hard gate).

This names who orchestrates vs advises vs works. The cross-family review gate, the per-task routing rows
above, and the Codex role table below retain the same independence boundary — this is the standing topology over them.

### No-idle utilization + transport map (operator 2026-08-08 — binding; builds on #6468)

**Canonical issue:** #6468 (Claude hramatka survey + operator refinements; Grok owns folding
into this topology). **Do not fork a parallel table** — update this section + activity-matrix §2b.

**Cursor mechanical pin (operator 2026-09-22):** pass `--agent cursor --model grok-4.7-high`.
Do not pass Fast, `grok-4.6` or `grok-4.5`; `auto` only for a well-defined coding dispatch
(owned paths, PASS DoR card; operator decision 2026-09-30). Drivers use that pin
for infra/code implement when the work is not language-lane and not advisor/authority.
**First pick when fit allows** for mechanical + ordinary infra/code implement; spread still
required. A review of a Grok author uses an Other Models slug. `cursor:auto` is never
review-of-record. The same `grok-4.7-high` pin is the formal code/infra review seat when the
resolver selects it at any risk (#9769); a bare `grok-4.7` runs the Fast variant, whose verdict is refused.
DeepSeek is excluded from dispatch and review; retained catalog identities are not routing permission.

**Failure mode this prevents:** concurrent drivers default everything to Codex/Claude while
**Cursor (`grok-4.7-high`)**, **AGY**, **Pool**, **Z.AI/GLM**, and **Kimi k3-256k** sit
free — then ask whether subscriptions are "too much." **Operator policy: utilize, do not trim.**
The portfolio is sized for cross-family quality; **idle paid capacity with open in-scope work is
a process defect.** Idle Cursor while mechanical jobs burn other seats is the same
class of defect.

#### Concurrent driver layout (operator seat reality 2026-08-08)

Typical live driver count (names rotate; count is the constraint):

| Driver seat | Typical concurrency | Role |
| --- | --- | --- |
| **Grok** | **~2** concurrent | Daily epic/topology drivers; dispatch-heavy, not solo multi-file |
| **Claude** | **~1** | Judgment / hard epic / Opus |
| **Codex** | **1–4** concurrent | Novel/hard impl + Sol-advised bounded work; **not** the dump for every mechanical job |

**Multi-driver rules:**
1. Drivers share the **same free worker pools** — before dispatch, read `/api/delegate/active`
   and native usage so two Groks + four Codexes do not all stampede one near_cap lane.
2. Claim **disjoint** work (stream epic / issue / owned paths); no duplicate branches.
3. **Timed pause, not permanent neglect:** a lane at near_cap or operator-paused carries an
   explicit **return-at** timestamp from the current usage probe or operator pause.
   Recheck live health and headroom at that time before returning it to rotation.
4. Verify delivery against **git/PR state**, not only task `no_deliverable` flags (#6426 class
   false negatives poison utilization metrics).
5. Cursor mechanical tier is **active** once the #6469 adapter fix is on main; substitute with NOTE only on live adapter regression.

**Before every dispatch / CF spend**, read live headroom (do not cache percentages into policy):

```bash
python -m scripts.fleet.usage show
curl -s http://localhost:8765/api/delegate/active
repo_root=$(dirname "$(git rev-parse --git-common-dir)")
df -h /; du -sh "$repo_root/.worktrees"
```

**Prefer free/behind practical seats before near_cap expensive ones** for work that fits them:

| Prefer when free / behind | Typical fit | Never / caveats |
| --- | --- | --- |
| **cursor** (`--model grok-4.7-high`) | code/infra CI, ruff/fixtures, bounded refactors, mechanical-with-judgment; first pick for mechanical + ordinary infra/code implement when fit allows. `auto` only for a well-defined coding dispatch (owned paths, PASS DoR card) | formal CF identity only as the resolver's `grok-4.7-high` code/infra seat at every risk (#9769); not language seats; not advisor/authority; `concurrency_limit: 1` |
| **deepseek** | No dispatch or review route | Catalog identity retained for historical evidence only |
| **claude** (Sonnet for well-scoped non-security routine work and polished English deliverables; Opus for security-sensitive code; Opus for Ukrainian curriculum) | hard judgment, CF, architecture briefs | don't burn Opus on queue grind |
| **agy** (Gemini 3.8 Flash default) | Ukrainian review and well-defined implementation tasks; **worker with complete briefs** (#5737) — not self-decomposing micro-PR spray | metered — cost-aware, not absent; complete brief required |
| **pool** (`laguna-s-2.1` default) | free CF volume + web-verify volume | not language; bridge `ask-pool` |
| **glm / Z.AI** (`glm-5.3-flash` workhorse; `glm-5.3` explicit) | deep security + large-context coherence audits; **Flash default** for ordinary code/infra (LOCAL-ONLY) | **LOCAL-ONLY** China egress; never CI/sensitive; prefer Flash API workhorse; `--model glm-5.3` for Coding Plan coherence |
| **grok-4.7** | daily driver (native and Cursor code/infra CF at every risk with runtime attestation, operator decision 2026-10-05 (#9769); never a QG judge) | oversight may be native Grok; don't solo multi-file when free workers exist |
| **kimi** (**keep**) | **web, UI and backend coding only:** **`k3-256k` everyday** coding/impl; **`k3` @ high/max** complex coding | native `kimi` CLI only — never OpenRouter; don't burn full k3 on routine; throttle 5h windows when farAhead |
| **glm / Z.AI** (**keep**) | **`glm-5.3-flash` workhorse** (default `--agent glm`); **`glm-5.3` explicit** for Coding Plan security/coherence | LOCAL-ONLY; prefer Flash API for implement; `--model glm-5.3` for Coding Plan |
| **codex** Sol (1–4 drivers) | coding and review; Luna for routine bounded work and scouting under a Sol advisory envelope; Opus / Sol for advice | **throttle mechanical when near_cap / paused unless a verified operator reset reserve applies**; shed implementation to Cursor `grok-4.7-high` / k3-256k / GLM; code/infra review goes to the resolver's pick (native or attested Cursor Grok at every risk, #9769) |

**Throttle (do not feed more mechanical work):** any lane at/ahead of pace, thin reserve, or
timed-paused (e.g. Codex near_cap until return-at). **Widen:** `farBehind` + meaningful reserve +
free disk. **Never convert a timed pause into permanent neglect of that seat.**

#### Transport map — native first; OpenRouter is not a bus

| Path | Use for | Do not use for |
| --- | --- | --- |
| **Native CLIs** (claude, codex, cursor, grok, kimi, agy) | default dispatch + ask for those families | Kimi: web, UI and backend coding only (workspace-write dispatch; no ask) — native `kimi` CLI subscription path only, never OpenRouter |
| **DeepSeek first-party** (`deepseek` via OpenCode) | historical transport evidence only; no dispatch or review route | `openrouter/deepseek/*` is guard-REFUSED |
| **Z.AI / opencode glm** | `glm-5.3` @ high (advisory max) LOCAL-ONLY reviews | general multi-model fallback |
| **OpenRouter** | **mainly Pool + Gemma access** when that is the named path | **not** a general multi-model bus; **not** a Kimi K3 worker bus (`kimi`/`kimicc`/`kimi-code/k3*` = `native_kimi` only); never Gemini (AGY) / GLM subscribed seats |
| **Cursor multi-model pin** | mechanical work: `grok-4.7-high` (or `composer-2.5`); `auto` only for a well-defined coding dispatch. A review of a Grok author: an Other Models slug such as `claude-sonnet-5-5-high` | `auto` outside a well-defined coding dispatch, Fast, `grok-4.6`, `grok-4.5`; formal CF as `auto` |

After merge: reap worktrees and free branch holds so the next free lane can attach (`reap_worktrees`,
no multi-GB shielded `lu-review-*` trees — formal CF is direct `ask-*` only).

### Worker priority ladder — first pick per work type (user standing order 2026-07-11: stop re-deriving this)

Route by FIT, then shed from HOT lanes — fanout WIDTH is decided by native **pace + reserve**
(`python -m scripts.fleet.usage json`; read `agents[lane].codexbar.{pace_summary,weekly_pace_delta_pct,will_last_to_reset}`),
and it is TWO-SIDED (operator 2026-07-26):

- **Lower bound — no idle paid capacity:** a lane sitting at `in_flight=0` while work queues behind
  another lane is waste. Pace stage `farBehind` with meaningful reserve → WIDEN into that lane.
  Headroom says you MAY use an idle lane, not that you should manufacture work for it.
- **Upper bound — DISK, and disk wins every conflict:** every dispatch costs a git worktree
  (hundreds of MB each). Concurrency is capped by worktree disk space regardless of how much
  quota remains; quota headroom never authorises exceeding disk headroom. From inside a dispatch
  worktree `.worktrees` is not a relative child, so resolve the repository root first:
  `repo_root=$(dirname "$(git rev-parse --git-common-dir)")`, then run `df -h /` and
  `du -sh "$repo_root/.worktrees"`. Reaping finished worktrees is what buys room for more
  agents — cleanup is part of capacity management, not housekeeping.
- **At or ahead of pace, or reserve thin →** throttle THAT lane; shed to one with headroom.
- **No data for a lane →** fall back to in-flight count + lane health, and SAY the picture is
  partial rather than guessing.

Never persist a live percentage or a fixed maximum worktree count into routing policy; both become
false as soon as a quota window moves or the disk fills — describe the check, run it live. Each
lane's current strengths/caveats live in the catalog, the per-task table, and the panel notes.

| Work type | 1st pick | 2nd | 3rd | gate / never |
| --- | --- | --- | --- | --- |
| **Coding / impl / fixtures** | **Codex Sol @ `high`** for accountable coding and broader integration; **Claude Opus 5.5 @ `high`** for hard Claude-lane coding. Use **Luna @ `high`** for routine bounded work, always under a complete Sol advisory envelope (`--advisory-task`, #9275). Cursor `grok-4.7-high` is a supported mechanical/ordinary code alternative when live capacity and fit favor it; pin the model (`auto` only for a well-defined coding dispatch) | **agy** `gemini-3.8-flash-high` for well-defined work (bounded fallback: Sol advisory envelope required) · **kimi** `k3-256k` · Cursor when fit allows | grok | LANGUAGE-LANES / advisor / authority never on Cursor; `cursor:auto` never CF identity; when Codex near_cap, shed mechanical work unless a verified operator reset reserve applies; claude seat = only ≤5-LOC CI-fix-I-caused; Workers never sole authority; retired Pro pins are historical only |
| **Code review** (cross-family = outside author's family) | **critical cross-family:** Opus, Sol, or qualified Grok 4.7 | **high:** `gpt-6.1-sol`, `claude-opus-5-5`, or `grok-4.7`, subject to the review admission rules at the top of this file · **medium/low formal CF defaults:** native AGY `gemini-3.8-flash-high` · `gpt-6.1-sol` @ `high` · `claude-opus-5-5` for hard Claude-lane review · `claude-sonnet-5-5` · GLM-5.3 · pool **`laguna-s-2.1`** | **second dissent / volume:** Pool S 2.1 | For the `code` and `infra` review profiles, security-sensitive changed paths automatically raise effective review risk to `critical`, even when the author requests low, medium or high. The shared `scripts/review/security_paths.py` classifier includes both rename names and deletions; owned paths can only add coverage. Resolve the target first. The resolver and every code/infra review-typed dispatch collect target changed paths before admission and require the catalog `critical_review` role, preserve cross-family and subject-seat exclusions, and refuse with a reason when no qualified reviewer is available (#9125). Catalog weaknesses remain descriptive. **Gemini code review (2026-10-08 approval): Gemini-family seats may formally review low-risk and medium-risk code, and Ukrainian work with the Sources MCP; high-risk and critical review use Opus 5.5, Sol 6.1, or Grok 4.7 until Gemini 4 qualifies. Native AGY dispatch is admitted at low/medium risk; the source-blind ACP wrapper remains excluded.** DeepSeek is excluded from formal review; Flash remains an active catalog identity, while Pro is retired |
| **UK content authoring** (author immersion-first, never translate) | **fresh-build lesson writer: codex Sol @ high** (operator default 2026-09-27, pending the pilot's measured writer selection, #8425) · **agy** (A1–A2 voice) ≈ **codex Sol @ high** | **claude** (B1–C2, sparingly — save the window) | — | **LANGUAGE-LANES RULE below binds**: only claude, codex (GPT), agy (Gemini); every other model family excluded |
| **Content / factual / CEFR review** (VESUM-gated) | **agy** (pedagogy/CEFR, + `sources` MCP) | **codex Sol @ high** | **claude** (judgment tier) | **LANGUAGE-LANES RULE below binds**; Grok is excluded from every Ukrainian review and judge seat; FOLK stays cross-family GPT↔Claude per the folk rubric |
| **Research / recon / triage** | **Haiku 5.5 read-only recon/search** alongside **Luna @ `high`** under a complete Sol advisory envelope — always required, never only when the boundaries need judgment (operator decision 2026-09-30) | Sol @ `high` for broader work and ordinary advice | agy (bounded fallback: envelope required) | Workers never sole authority on consequential calls |
| **Live web fact-check** (pricing/URL/citation currency) | eligible opencode models — pool (FREE) · glm (LOCAL); DeepSeek is excluded from dispatch and review (`ask-deepseek` is consult-only for non-language work) | — | — | browsing = harness property, not a model trait |

**Gemini code-review gate — accepted residuals.** Two calls stay outside the path check. `--review-profile ukrainian` without `--pr` or `--branch` is a self-assertion: nothing inspects the changed paths. `delegate --agent agy` with no review-typing flag is an implementation dispatch and is not gated; code-profile review-typed dispatches to AGY apply the low/medium risk and security-path gates. A copy of code into a content path is out of scope: the Ukrainian profile does not grant code-review eligibility, and a file under a content path is content by definition and is not executed.

**LANGUAGE-LANES RULE (HARD, operator order 2026-09-27): “only claude, gpt and gemini should be invlved in ukrainina content. no other models allowed if it is about ukrainina lang. culture, heritage.” Every seat that authors, reviews, critiques, settles, or judges Ukrainian language, culture, or heritage content — including linguistic/content review and CEFR/russicism analysis — routes ONLY to claude, codex (GPT), or agy (Gemini).** Grok, deepseek, glm, kimi, cursor, pool, gemma, and every other model family are excluded from every language seat (deepseek's former VESUM-gated content-review default is retired; gemma's surface-review slice applies to non-language work only). Standing carve-outs still bind on top: NO deepseek for folk (moot under this rule, kept for history), folk review pairing stays GPT↔Claude. Grok remains available for code, infra, and non-language work.

**Sources MCP by dispatch mode (checked 2026-09-22).** A language review that names `mcp__sources__*` has to run in a mode that can call that server. Codex `read-only` keeps the filesystem sandbox and sets `mcp_servers.sources.default_tools_approval_mode="approve"`. Without that approval, `approval_policy=never` cancels the stdio call (`MCP tool call requires approval, but approval policy is never`) before the tool runs. Codex `workspace-write` and `danger` already pass `--dangerously-bypass-approvals-and-sandbox`; the dispatch worktree is the write boundary. The sources server marks every tool `readOnlyHint`, so Codex does not treat a lookup as a destructive approval. Claude `read-only` and `workspace-write` share one invocation and can call sources when the seat's MCP config includes the server. AGY has no per-mode MCP flag; `read-only` sees sources when the AGY catalog lists the server. A Codex plan that names `mcp__sources__*` and can neither approve nor bypass those calls fails before spawn.

**Advisor (on-demand, HARD calls only): `gpt-6.1-sol @ high` by default** — architecture, high-stakes design/ADR review, difficult debugging, final synthesis, or a bounded advisory envelope. Codex workhorse and red-team efforts are Sol `high`; bounded work is Luna `high` under a Sol advisory envelope. **Excluded:** qwen (cost). **LOCAL-ONLY:** glm (China-egress, never CI). **Cross-family review gate holds:** the reviewer must be outside the author's model family.

**Kimi onboarding (native `kimi` CLI only):** dispatch with `.venv/bin/python scripts/delegate.py dispatch --agent kimi` — omitted flags default to **`k3-256k`** (everyday coding/impl; no forced effort, operator 2026-08-13). Explicitly select `--model k3 --effort high|max` whenever the task is consequential. K3 is the frontier-practical Moonshot seat (high/max effort, 1M window); `k2.7-coding` and its high-speed variant remain available as legacy routine workers. Current quota affects selection only among models that clear the task's quality floor. **Never route Kimi K3 workers through OpenRouter.** Kimi: web, UI and backend coding only — no Ukrainian-language content, no reviews, consults, design or rules.

## Fleet discussion panels — actively involve ≥1 other agent before committing (user order 2026-06-23)

Drive high-judgment work (design, architecture, in-the-loop review, brief authoring) YOURSELF in-context — the frontier Claude lane does not brain-rot in-session (canary-verified on Opus 4.8; Fable 5 improvised 10/10 @ ~500K/1M 2026-07-07; a NEWLY rotated model must mint its own canary at cold-start per workflow.md — rot evidence is per-model, names rotate). But for any SUBSTANTIVE design / decision, **actively DISCUSS + cross-verify with the fleet BEFORE committing** — not solo dispatch-and-merge. Default to ≥1 other agent per substantive task; solo only for trivial work. Convene by lane:

* **Module-content panel** (writers, content review — LANGUAGE-LANES RULE binds): **agy** (Gemini 3.8 Flash default for routine and deep; Gemini 3.1 Pro only on explicit request) · **GPT-6.1 Sol @ high** · **claude**. ~~cursor seat~~ removed (excluded from language seats, user 2026-07-17). Prefer a bake-off + cross-family verification. Folk content review stays **cross-family (GPT↔Claude)** per `docs/folk-epic/folk-review-rubric.md` — **NO DeepSeek for folk culture** (lacks intrinsic Ukrainian-culture knowledge).
* **Infra panel** (code, gates, pipeline, tooling, schemas, Atlas/lexicon; CF follows the Code review row): **GPT-6.1 Sol @ high** · **cursor `grok-4.7-high`** (mechanical pin, or concrete `composer-2.5`; never `auto` in review) · **native Grok 4.7** · **Pool Laguna S 2.1** (free review volume) · **GLM-5.3 / Z.AI** (deep security/bug review + large-context coherence audits; LOCAL-ONLY) · **Gemma 4** (surface review only; often via OpenRouter). Pin Cursor's concrete model whenever family independence matters — never `auto` as CF identity.

Invocation (`scripts/ai_agent_bridge/__main__.py`): `ask-codex` · `ask-agy --to-model gemini-3.8-flash-high` (Ukrainian-language review only; `--to-model gemini-3.1-pro-high` only on explicit request; implementation routing above is unchanged) · `ask-cursor --model grok-4.7-high` (a review of a Grok author uses an Other Models slug, not `auto`) · `ask-grok` (alias `ask-grok-build`; code, infra, or other non-language work only) · `ask-pool [--variant high|max]` · `ask-glm` (LOCAL-ONLY) · `ask-gemma` (cheap; ⚠️ not a sole seminar writer / factual reviewer) · `ask-deepseek` (consult-only for non-language work, LOCAL-ONLY; alias `ask-hermes`; first-party Flash @ high via opencode ACP, #6805) · `discuss <channel> "<topic>" --with <a,b,c>` for a bounded multi-round. DeepSeek is excluded from dispatch and review; Pro is retired; Flash remains active in the catalog, with `ask-deepseek` restricted to consultation, never implementation or review. Non-review bridge `ask-*` replies arrive as INBOX MESSAGES (`ab read <id>`); formal review asks use native dispatch/wait and print reply text (drive-epic §6).

**opencode-routed cross-family reviewers (pool · glm · gemma):** opencode is a multi-provider ROUTER — the fleet member is the MODEL, not "opencode". **OpenRouter is mainly for Pool + Gemma access** (operator 2026-08-08); the catalog can reach more models through OpenRouter, but **we do not need to** — prefer native/first-party seats (Cursor, Claude, AGY, Z.AI GLM, Codex, Kimi, Grok). **Kimi K3 workers never ride OpenRouter** (`kimi` / `kimicc` / `kimi-code/k3*` = native `kimi` CLI only). Do not invent OpenRouter as a general multi-model fallback bus when a native lane exists (`ask-opencode <model>` is RETIRED — the bridge fails it closed; `ask-pool`/`ask-glm`/`ask-gemma`/`ask-deepseek` are the named members). **Live web fact-checking is a HARNESS property (opencode + lightpanda MCP), NOT a model trait — any opencode-hosted model browses** (kubedojo-verified incl. deepseek); don't treat it as unique to pool/glm. Since the coding floor is uniformly high across the fleet, route by the DIFFERENTIATOR (kubedojo 5-agent scorecard 2026-07-04): **pool** = **free** cross-family code review + web-verify *volume*; **glm** = deep security/bug review + **large-context cross-file coherence audits**; grok = implementation (native and Cursor code/infra review at every risk with runtime attestation, operator decision 2026-10-05 (#9769)); deepseek = historical harness evidence only; excluded from dispatch and review; **gemma** (Google Gemma 4 via **`google-ais/gemma-4-31b-it`, $0 DEFAULT** — AIS-direct with the user's key, no paid SKU exists for Gemma on the Gemini API; TOOLLESS `chat` agent; paid OR `-it` via `--model` fallback only, note the spend; OR `:free` pool-starved, avoid) = a metered lane for non-language surface review. **Gemma is excluded from Ukrainian language, culture, and heritage work, including russicism checks, wiki drafting, seminar writing, and factual review, under the 2026-09-27 LANGUAGE-LANES RULE.** The 2026-07-05 source-citation probe evidence remains in `docs/projects/qg-quality-gate/model-evidence.md`; Google-family → not a clean reviewer of agy/Gemini work. **pool and glm are NOT for Ukrainian content / prose / pedagogy** — both are code models (glm anglicizes/code-switches, pool is worse); for UK content see the "Ukrainian CONTENT" row above (we author, not translate; cursor is NOT russicism-safe on long UK text). **pool** = poolside.ai **`laguna-s-2.1`** (default gen-2 S; also `laguna-xs-2.1` / fallback `laguna-m.1`), **free** (watch weekly limits on bursts). ⚠️ **glm** = Zhipu `glm-5.3`, **China-hosted (Zhipu/z.ai) → prompt data egresses to China → LOCAL-ONLY: never in CI / automated pipelines or with sensitive data** (`ask-glm` refuses under any CI env var as a backstop); prefer a Western-lab reviewer for top-stakes. Bridge (consult/review) only today — no `delegate.py --agent pool|glm|gemma` dispatch adapter yet, and no V7 `--writer gemma-tools` yet (the opencode→delegate adapter + tool-calling writer harness are scoped follow-ups; a plain OpenRouter chat model has no `sources`-MCP harness).

## Advisor panels — per-area pools · pool-minus-author · size-by-stakes · Opus/Sol anchor (#9394; supersedes #5933 seat defaults)

Advisory panels are a RULE, not a roster. **Per-area advisor assignment is the PRIMARY
structure** — each top model has distinct strengths; the pool modifiers operate WITHIN the
area's pool, with ONE exception: the anchor (modifier 3) is an OVERLAY seat that joins from
outside the pool when the pool contains neither Opus nor Sol. Panels are DISCUSSION/advice
for CONVENED design and judgment work; an ordinary formal PR review is NOT an advisory
panel (the "do not burn advisor seats on routine work" economy rule stands), and a panel
never replaces the independent CROSS-FAMILY review of record (discussion ≠ review), which
composes on top.

**Per-area advisor pools** (the operator's approval surface; the table is REVIEWED when
seats rotate — operator wording; the catalog-refresh contract §above owns name→model):

| Area | Advisor pool | Evidence anchor |
| --- | --- | --- |
| Ukrainian language & pedagogy | Opus · Sol (sanctioned language seats ONLY). Gemini joins only as task-level content reviewer under a fixed brief, never for planning or advice on new design (operator decision 2026-10-03, #9584) | LANGUAGE-LANES RULE binds |
| Architecture & process design | Sol (designer) · Opus (counter-reader); designated approval needs the non-author's approval when Opus or Sol authored the proposal, both otherwise | fleet topology §above |
| Code & infrastructure review | GLM-5.3 · GPT-6.1 Sol | Historical Terra review arcs on #5896/#5925/#5926/#5931 (defect-finding record) |
| Security-sensitive changes | Sol · Opus | ambient-Anthropic-token→z.ai leak caught pre-merge (#5931 arc) |
| Debugging & forensics | Grok · GLM-5.3 | Grok: #5932 root cause (#5950 workaround); GLM: operator statement, #5933 comment 2026-07-28 |
| Long-context sweeps & harness infra | Gemini (sweeps and recon only; not planning or design input, operator decision 2026-10-03, #9584) | model catalog §above (window/tooling) |

Historical Terra findings support the evidence record, not a current routing choice.
The ordinary Codex advisor-panel participant is GPT-6.1 Sol. Routine Codex code review
uses Sol high; legacy results do not establish either model's qualification.

**Modifiers (compose in this order; semantics 2a-2c are DRAFTED DEFAULTS — the operator's
sign-off on this section approves them):**
1. **Pool-minus-author** — the panel is the area pool MINUS whoever authored the work under
   review (self-adjusting when an advisor is the worker). Family-independence accounting
   still binds for the review of record.
2. **Size by stakes** — routine PRs: NO panel (formal cross-family review only) · 2 seats
   for designs/plans · 3 seats at high effort for contested verdicts, architecture,
   learner-facing calls.
   - 2a. The anchor COUNTS toward the size target (panels stay small — operator: big
     panels are slow).
   - 2b. If pool-minus-author cannot reach the target, UNDERFILL and record the shortfall
     on the work item — never manufacture seats; escalate to the operator only when zero
     eligible seats remain.
   - 2c. When the anchor is the SOLE seat, it must be outside the author's model family;
     if neither Opus nor Sol qualifies (both in-family or author), the pool's strongest
     cross-family seat serves instead and the waived anchor is RECORDED on the work item.
3. **ANCHOR RULE** — Opus or Sol sits on EVERY convened advisory panel: whichever of the
   two is available and is NOT the author. In pools lacking both (code/infra, security,
   debugging, long-context), the anchor joins as the outside-pool overlay seat per above.

**Standing constraints (unchanged, restated because they bound the pools):** no Kimi/GLM on
language judgment (#M-13a) · grok is NEVER a language or content judge seat (code/infra review via native and attested Cursor seats at every risk, #9769) · GLM-5.3 is LOCAL-ONLY (China
egress — no CI, no secrets, no sensitive data).

*Operational notes (not #5933 rulings; separate authority cited):* Gemma is not an advisor
seat (§panels above) · Kimi: web, UI and backend coding only, on no panel · on any ask
transport failure, reroute BY SEAT within the pool and record the substitution
(workflow.md substitution rule).

## Driver routing card + breadth floor (operator GO 2026-08-06)

Epic drivers **must** follow `fleet-driver-routing.md` (served immediately after this file
in `/api/rules`):

- **ROUTING_CARD_V1** before every implement dispatch (tier · model×harness · advisor packet · alternatives).
- **Default bounded work:** advisory envelope from the catalog advisor route,
  the Sol advisor (`gpt-6.1-sol` @ high) → bounded worker (Luna @ high, or the Flash fallback) dispatched with
  `--advisory-task`. A design brief that is not a Sol envelope does not admit a
  bounded worker (operator decision 2026-09-30, #9275). A complete envelope defines the work;
  it does not turn the Sol advisor (`gpt-6.1-sol` @ high) into an implementer.
- **Session breadth:** after ≥3 implement dispatches, ≥2 agents and ≥2 tiers, or a tool-backed
  `NOTE: fleet_breadth`. Handoff must attach
  `python -m scripts.fleet.driver_breadth_report`.

This does not replace the ladders below; it stops single-seat fixation.

## Harness vs model — route by BOTH (added 2026-07-05; user order: fleet utilization is paramount)

A fleet member = MODEL × HARNESS. The same model behaves differently in different harnesses, and
several models are reachable through more than one. Know both axes before routing:

| Harness | What it adds to ANY model it hosts | Models routed through it | Entry points¹ |
| --- | --- | --- | --- |
| **hermes** — REMOVED from this host (operator order 2026-08-16); row kept for history only | (was: SOUL.md persona · `sources` MCP · 16 toolsets · session store) | (was: deepseek · zai/GLM · OpenRouter catalog) | DeepSeek is excluded from dispatch and review. `ab ask-deepseek` is consult-only for non-language work (opencode ACP seat, #6805); Pro is retired |
| **opencode** (multi-provider router) | lightpanda MCP configured (`~/.config/opencode/opencode.jsonc`) → **live web browsing/fact-check is a HARNESS property here**, available to tool-capable hosted models (kubedojo-verified for pool·glm·deepseek routes; verify before relying on a new route) | pool (poolside **laguna-s-2.1**, free; m.1 prior-gen fallback) · glm (⚠️ LOCAL-ONLY) · gemma · deepseek (first-party `deepseek/` provider; #4358/#4626 QG bakeoff default) · OpenRouter deepseek/gemma baselines · any OpenRouter model | `ab ask-pool` / `ask-glm` / `ask-gemma` / `ask-deepseek` (consult-only for non-language work; DeepSeek is excluded from dispatch and review; named seats only; generic `ask-opencode` is retired) |
| **native CLIs** (codex, cursor, agy, grok, claude, kimi) | each CLI's own tool loop + repo context; capabilities differ per CLI. GPT/Codex is **native-only**: never route it through Hermes. Grok: never Hermes, never opencode — the native CLI is the ONLY sanctioned grok route for every seat (interactive, orchestrator, ask, dispatch; native and Cursor Grok review code/infra at every risk with runtime attestation, operator decision 2026-10-05 (#9769)) as of operator order 2026-08-16 (#6865, retires the 2026-07-27 opencode-for-orchestrator-seats ruling, see Consequences below). `grok` = the native Grok CLI seat (alias `grok-build` kept permanently); `kimi` = native `kimi` CLI subscription seat only (models `k3` · `k3-256k` · `k2.7-coding` · `k2.7-coding-highspeed`) — **never OpenRouter** as a Kimi worker bus | one primary family each; Cursor is multi-model and must be pinned for review identity | `ab ask-codex` / `ask-cursor` / `ask-agy` / `ask-grok-build` / `ask-claude` · `delegate.py dispatch --agent <a> --mode danger --worktree` (Kimi: web, UI and backend coding only — `--agent kimi --mode workspace-write --worktree`; no `ask-kimi`) · orchestrator grok via `ab ask-grok-build` / native `grok` CLI — never `ab ask-opencode --model xai/grok-*` |

¹ `ab` = the user's shell alias for `.venv/bin/python scripts/ai_agent_bridge/__main__.py`.
In scripts, docs meant for copy-paste, and anything automated, ALWAYS write the full path —
bare `ab` resolves to ApacheBench (`/usr/sbin/ab`) outside the user's shell (AGENTS.md rule).
`ask-deepseek` is consult-only for non-language work (added 2026-08-16, #6805), never implementation or review. Bridge asks ride the
`acpx-deepseek-shadow` ACP seat — native `opencode acp --pure` pinned to first-party
`deepseek/deepseek-flash` (identity `deepseek-v4.1-flash`) at high effort, deny-all tools (the `ask-hermes` alias
resolves to the same seat; Hermes itself was permanently removed 2026-08-16).
The legacy generic `ask-opencode` ACP route stays retired — named consult seats only.
DeepSeek is excluded from dispatch, implementation and review. The active
`deepseek-v4.1-flash` catalog entry does not authorize execution; Pro is retired.
`openrouter/deepseek/*` is **guard-REFUSED** (user order
2026-07-07 — the OR account was drained by deepseek bakeoff cells; deepseek runs FIRST-PARTY only.
The user's OR BYOK now bills deepseek underneath, so transport-comparison runs (#4321/#4358) are
billing-safe behind `LU_ROUTING_GUARD_OVERRIDE=1` — deliberate, user-authorized only).
² Qwen is excluded from routine routing; `glm-5.3` (Zhipu/opencode; default high, advisory max) is used for cross-family code and review.

Consequences:
- **A model "lacking" a capability may just be in the wrong harness** — deepseek can't browse
  natively but browses via opencode; any hermes-hosted model gets VESUM/`sources` tools for free.
- **Limits are per-harness-credential, not per-model**: when a lane quotas out, the same model is
  often reachable through another harness, but
  **GPT/Codex and Claude are hard exceptions**: keep both on their native CLIs (operator
  ruling 2026-07-27 for Claude) and never substitute a Codex OAuth-backed Hermes model or a
  non-native Claude host. **Grok (operator order 2026-08-16, #6865 — retires the 2026-07-27
  ruling below):** never Hermes (`grok-hermes`/`grok-tools` stay banned) and **opencode is no
  longer sanctioned for any grok seat, including orchestrator** — "we have grok cli"
  (operator, verbatim). The native `grok` CLI is the ONLY sanctioned route for every grok
  seat (interactive, orchestrator, ask, dispatch and attested code/infra review, #9769) at `grok-4.7`; Cursor
  explicit `grok-4.7` stays the availability fallback only when native is dark. Never
  route grok via OpenRouter model ids (`openrouter/x-ai/*`) — only the first-party `xai/*`
  provider is sub-backed, and as of this order that first-party access is native-CLI-only,
  not opencode-hosted. Check `/api/orient` headroom.
  For Claude/Codex budget buckets at `near_cap`, substitute per
  `scripts/config/agent_fallback_substitutions.yaml` (that file is the budget-bucket map, not a
  general outage map); Codex substitutions must never use Hermes. ALWAYS note a substitution
  in the artifact — silent rerouting hides
  review-independence, cost, and egress changes.
- **Hermes is also an automation platform** (cron, kanban, insights, session FTS, gateway,
  openai-compat proxy) — study + adoption plan: `docs/references/private/hermes-usage.md`
  § Automation adoption plan (gitignored machine-local doc — operator OPSEC policy 2026-07-05;
  tracked stub at `docs/best-practices/hermes-usage.md`). Prefer harness-level automation over
  hand-rolled polling where it fits.

**Model names are rotating attributes, not constants.** The dated source of truth is
`scripts/config/model_catalog.yaml`; its 30-day lint prevents this prose from being treated as a
permanent capability claim. Confirm exact live strings in native CLI catalogs and bridge probes.

## Gemini 3.8 Flash vs 3.1 Pro (default updated 2026-09-02)

Operator directive: **Gemini 3.8 Flash is the AGY top default** (agentic workhorse).
Operator 2026-09-22: 3.8 Flash High is better than 3.1 Pro; Flash is the deep default.
Gemini 3.7, 3.6 and 3.5 Flash are retired; use Gemini 3.8 Flash.

| Model | Catalog slug | Tier | Use |
| --- | --- | --- | --- |
| Gemini 3.8 Flash (High) | `gemini-3.8-flash-high` | `frontier_practical` | Default AGY dispatch/Q&A for routine AND deep work; subagents; fast tool loops; day-to-day coding |
| Gemini 3.7 Flash (High) | `gemini-3.7-flash-high` | `frontier_practical` | Retired; use `gemini-3.8-flash-high` |
| Gemini 3.6 Flash (High) | `gemini-3.6-flash-high` | `frontier_practical` | Retired; use `gemini-3.8-flash-high` |
| Gemini 3.1 Pro (High) | `gemini-3.1-pro-high` | `frontier_practical` | Only on explicit request (outperformed by 3.8 Flash High; superseded as deep default) |
| Gemini 3.5 Flash (High) | `gemini-3.5-flash-high` | `strong_efficient` | Retired; use `gemini-3.8-flash-high` |

**Tier calibration (operator claim checked):** 3.8 Flash is roughly **Terra / Sonnet 5 class** for agentic coding throughput — **not** Sol/Opus authority, but operator 2026-09-22 confirmed 3.8 Flash High outperforms 3.1 Pro; Flash is the default for routine AND deep work. Escalate cross-family to Opus / Sol when critical authority is required; Pro only on explicit request.

## Codex routing — GPT-6 driver, workers, reviewer, and advisor

| Role | Model id | Effort |
| --- | --- | --- |
| Default driver and advanced coding | `gpt-6.1-sol` | `high` |
| Bounded coding, scouting, and recon (Sol advisory envelope required) | `gpt-6-luna` | `high` |
| Adversarial code review | `gpt-6.1-sol` | `high` |
| Ukrainian content authoring | `gpt-6.1-sol` | `high` |
| Consequential advisor and difficult Ukrainian adjudication | `gpt-6.1-sol` | `high` |

Codex runtime routes accept exactly `gpt-6.1-sol` and `gpt-6-luna`. Omitted implementation and
ordinary `ask-codex` model selections use GPT-6.1 Sol; in-session bounded subagents of a Sol parent default to Luna.
The Ukrainian assignment is a routing starting point, not a GPT-6 language
quality benchmark. Apply VESUM, sources, Russian-shadow, CEFR, and track
immersion checks before accepting content.
Use the live catalog and validated runtime profile for supported effort values, context
capacity, and transport capabilities. A model name or historical context window grants
no filesystem, tool, or driver authority.

The compatibility key `execution_routing.sol_advised_bounded` retains its name.
Its current advisor is the Sol advisor (`gpt-6.1-sol` @ high) and its bounded worker is Luna high, with Sol
high for broader autonomous integration; it has no direct-worker route, and its
`bounded_fallback_worker` (`gemini-3.8-flash-high`) needs the same envelope. Current designated advice uses **Opus / Sol**;
designated approval needs them to agree, and when one authored the proposal the other's approval completes it, and any other author needs both (#9583, #9616). The mandatory #9275 envelope advisor is Sol 6.1 alone; an envelope is not an approval.
Kimi: web, UI and backend coding only — no
Ukrainian-language content, no reviews, consults, design or rules. All GPT-6 models are OpenAI-family and
cannot satisfy independent CF for an OpenAI-authored PR.

## Claude reviewer-seat economics (2026-06-12)

There is ONE Claude Code quota. A dispatched / headless / subagent Claude competes with the interactive
orchestrator's own seat, AND a subagent starts a fresh context that **reloads the full project (~2–3M tokens,
~1000:1 overhead per the global `code-editing-safety` §7 rule)** to return a verdict that inline costs
~15–25k. A subagent therefore *duplicates a session boot you pay for anyway* → ~50–150× the tokens for the
identical verdict. So **prefer** fulfilling the Claude reviewer seat IN-SESSION (dispatching Claude is
permitted — the `-p` sunset was cancelled, user 2026-06-22 — but it costs the multiple above, so route by need):

1. **Default: review INLINE, early in the session** while context is light — cheapest, full faculties, and you
   reuse the read to write the fix.
2. **Context heavy + a Claude review is still needed: DEFER** to the next MANUAL interactive session's start
   (record a top-of-handoff `Claude review PENDING: <artifact>` so cold-start picks it up first). That
   artifact's merge waits one session. Prefer this over cramming it into a depleted session or spawning a
   subagent (cost) — though dispatch IS available when the review must clear now.
3. **Inline-now despite heavy context** only when latency is unacceptable (the review must clear THIS session
   to unblock something).

Non-Claude reviewers are UNAFFECTED for NON-LANGUAGE work (LANGUAGE-LANES RULE binds for anything judging Ukrainian text) — resolve CODE/infra reviews through `closeout_cli resolve-reviewer` on a qualified outside-family route. DeepSeek is excluded from dispatch and review; `ask-deepseek` is consult-only for non-language work. (VESUM/content review = language work → the three language lanes only.) The *Claude* seat is **preferred** in-session for cost.
(The headless `--agent claude` / `claude -p` lane is AVAILABLE again — the mid-June 2026 sunset / "native binary not
installed" fiasco was cancelled, user 2026-06-22; Claude may be used for ANY task, incl. dispatched review, when needed.
The cost economics above stand regardless: dispatched Claude is far pricier than inline, so route by need, not by ban.)

The same table lives in `agents_extensions/shared/memory/MEMORY.md` rule #M0. This file is served at `GET /api/rules`; it is a Claude autoload exclude and is not deployed into `.claude/rules/`.

</critical>

## PR cross-family review (direct only — operator 2026-08-06; sealed formal RETIRED 2026-08-07)

Review: one direct cross-family `ask --review --branch <name>` on the pushed
branch. Delegate admission pins the remote-tracking target; fetch refuses
movement. Compare task `pinned_head`/`worktree_base_sha` with the pushed tip,
not ask reply stdout; require qualified APPROVE before PR, then bind with
`record_cf_verdict.py`, require same-SHA CI, and reap the worktree
(the canonical `workflow.md` § Merge policy / landing and cleanup). Ask waits synchronously without
nonce; continue expiry on the same task/nonce using §6, never repeat the launch.

```bash
printf '%s\n' "Review pushed branch <branch> at its resolved remote head: VERDICT + findings." | \
  .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-<lane> - \
    --task-id review-<id> --review --branch <branch>
# After APPROVE matches the branch SHA, open the PR and bind the completed review:
.venv/bin/python scripts/review/record_cf_verdict.py --task-id review-<id> --pr <N>
```

**Shielded formal CF is RETIRED.** Do not run `review-pr` / `publish-review-verdict`
/ sealed `lu-review-*` / `shielded-reviews` clones — its commands were removed in #8520
and the snapshot flow is refused with no bypass. Cross-family still means outside the author's
model family; discussion and same-family chat are not the gate.

Code/infra formal reviews require a resolvable target before delegate admission
(§ review target admission above); missing targets refuse. Ordinary ACP asks
cannot supply review of record. Use drive-epic §6 for launch and settlement.
