# Per-Task Model Assignment (HARD RULE)

<critical>

Match the EXACT command — not a principle. Memory does not enforce; the dispatch tool does. Established 2026-05-06 after repeated drift on cost discipline.

## Canonical model catalog and refresh contract

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

Selection order is binding: **independence and hard gates → review quality tier → health/quota within
that tier → cost among equivalent fits**. For formal code review, everyday routine PRs use practical seats
(**Sonnet 5 → Terra → Gemini 3.6 Flash → GLM**). Escalatory authority reviews select from the advisor quality prior (**Sol → Opus
→ Fable → Pro**) (#5293). `gpt-5.6-terra` is **not an advisor**: it remains a practical/routine review seat.
Cost never lowers the quality floor. An `unhealthy` route is unavailable; `degraded` and `near_cap`
only break ties inside a quality rung. `cursor:auto` is never an acceptable formal-review identity;
Composer is eligible only with its concrete `composer-2.5` model identity.

**Fable transport order (user directive 2026-07-20):** always dispatch the exact
`claude-fable-5` model through the native Claude harness first:
`.venv/bin/python scripts/delegate.py dispatch --agent claude --model claude-fable-5`.
Use Cursor with the same pinned model only when native Claude does not expose Fable or
rejects that model before inference. Quota pressure alone does not invert this order.
Record the harness fallback explicitly; it is a transport fallback, not a model substitution.

### 2-Tier Formal Review Routing Policy (user directive 2026-07-22)

* **Everyday Routine Formal Reviews** (practical seats @ `high` effort):
  * **Claude seat**: `claude-sonnet-5` (preserves frontier window; fast & efficient)
  * **Codex seat**: `gpt-5.6-terra` (standard practical review)
  * **GLM seat**: `glm-5.2` (local-only)
  * **Gemini seat**: `gemini-3.6-flash-high`
* **Complex Tasks, Deep Reviews & Anthropic Advisory Consultations**:
  * **Anthropic Opus seat**: `claude-opus-5` (complex coding, deep reasoning, and
    non-binding advisory consultation). Operator directive 2026-07-31: when requesting
    Anthropic advisory input, use `ab ask-claude --type advisory --to-model claude-opus-5`;
    never substitute Sonnet. This consultation does not confer designated approval
    authority and does not satisfy the formal cross-family review gate.
* **Escalatory Advisor / Critical Authority Reviews** (reserved for architecture, security, or design escalation):
  * **Top advisors**: `claude-fable-5` · `gpt-5.6-sol` — the ONLY top-tier
    advisor seats. Sol starts at `high`; use `xhigh`/`max` only for an explicit
    escalation, never as the bounded-advisory default. Fable's cost is accepted for advisor turns:
    they are rare, short, and decision-bearing; never spend them on queue grind.
  * **Other advisors**: `gemini-3.1-pro-high` · `gemini-3.6-flash-high` ·
    `kimi-k3-max` · `glm-5.2` · `grok-4.5` @ `high`.
  * `gpt-5.6-terra` is **not an advisor**; it remains the practical/routine
    Codex review seat.
  * `gemini-3.6-flash-high` is currently the strongest lane for Ukrainian.
    Flash 3.6 sometimes outperforms 3.1 Pro; until the next 3.1 Pro ships,
    test Flash in advisor-adjacent roles.

*Everyday routine PRs use practical seats (`sonnet` / `terra`). Do not burn advisor seats on routine work.*

**Three-role boundary (operator directive 2026-07-31):** advisory consultation is
non-binding model input (Anthropic → Opus); designated approval authority is the current
identity roster in `operator-expectations.md`; formal review is selected independently by
the canonical reviewer resolver. A routing-table change must never grant approval authority
or count as a formal review.

**Lane updates (user-reported 2026-07-18):**
- **grok**: the lane now offers **grok-4.5 only**, with selectable reasoning effort
  (`low`/`mid`/`high`) — set effort explicitly per dispatch; authoring/review seats run `high`.
- **cursor**: **composer-2.5-fast is retired** — cursor has no cheap-fast tier; route quick
  mechanical edits to agy/glm instead. Composer 2.5 (standard) remains the pinned-model choice
  where family independence matters.

| Task | Tool + model |
| --- | --- |
| Inline code edit ≤5 LOC, fixing a CI failure I just caused | Me, current model |
| Claude-side ROUTINE work — formulaic reviews, config/fixture edits, monitoring-only sessions, wiki fixes, mechanical PR babysitting | **Sonnet 5** (user 2026-07-07: "use Sonnet more often for routine work") — dispatch `--model sonnet` / Sonnet session. Reserve the frontier Claude tier (Opus 5 / whatever frontier model is active) for judgment work: architecture, adversarial review, pedagogy, hard bugs. **Route by TIER-FIT, not model name — the Claude lane rotates** (Fable 5 was temporary). **Motive = SAVE THE FRONTIER WINDOW** (user-confirmed 2026-07-07): if Sonnet is busy, QUEUE routine work or reroute to agy/codex — do not burn the frontier window on it. |
| Code change >5 LOC, mechanical / pattern-applying / fixtures | Clearly bounded with exact owned paths + an objective scope ceiling → `delegate.py dispatch --agent codex --model gpt-5.6-luna --effort max --mode danger --worktree --base origin/main`. Missing ceiling, broader integration, or consequential ambiguity → omit `--model` and retain the Terra @ `high` default. |
| Code Review (PR diff) | Resolve with `.venv/bin/python -m scripts.review.closeout_cli ... resolve-reviewer --author-model <exact-model> --review-profile code --risk <low\|medium\|high\|critical>`. The resolver applies hard filters first, then the #5293 quality prior above for every formal review; risk remains recorded in the receipt but does not allow a lower tier to leapfrog an eligible higher one. Execute the returned `invocation`; preserve its concrete model, family, `route`, `transport`, health trace, and `requires_silence_timeout` receipt. Do not hand-pick Flash while an eligible higher-tier reviewer remains usable. |
| Content Review with VESUM verification (load-bearing) | **LANGUAGE-LANES RULE binds (user 2026-07-17): agy / codex / claude / grok-4.5 only** — dispatch the reviewer on one of the four with the `sources` MCP (`verify_words`, `query_cefr_level`, `check_russian_shadow`). ~~deepseek-v4-pro default (#4358)~~ RETIRED for language seats by the same order; the #2112/# 4358 validation history stands as evidence only |
| Wiki / content writing · content / pedagogy / factual **review** | agy — `delegate.py dispatch --agent agy` (write) or `ab ask-agy --to-model gemini-3.1-pro-high` (review). **Use agy actively here** (user 2026-06-24): the §7/factual-fabrication fence is LIFTED (cleared 2026-06-13 — it grounds in the `sources` MCP and abstains "NO SOURCE"), and its pedagogy/CEFR review is strong — it LED the 2026-06-24 practice-hub panel. **Metered** → be cost-aware, but do NOT under-use it where it's strong. NOT for cross-file architecture / security-concurrency / auth-heavy git / mass-mechanical (→ codex/claude). Caveat: agy `--data` truncates large/binary attachments → paste trimmed content or use codex `--data`. |
| Ukrainian CONTENT (authoring · russicism/quality review) — **we AUTHOR UK content, we do NOT translate EN→UK** | Written in Ukrainian, immersion-first, grounded in VESUM/`sources` MCP. **Per-profile authoring — BAKEOFF-BACKED (2026-07-04, `audit/2026-07-04-uk-writing-probe/`, deterministic VESUM + russian-shadow, 5 candidates):** all of codex (gpt-5.6-terra default; 5.5 retained for pinned workflows)/agy/claude/deepseek/cursor wrote **0-russicism, 95-100%-VESUM** content on all 3 profiles → **gpt-5.5 is not uniquely best; it can and should delegate.** A1-A2 English-support → **agy** (best immersion teaching-voice) ≈ **codex**; B1-C2 pure → **codex ≈ agy ≈ claude**. **Seminars — FACT-CHECKED (2026-07-04, `audit/2026-07-04-uk-writing-probe/SEMINAR-SCORECARD.md`; tool-backed vs uk.wikipedia + VESUM, cross-verified by an independent 3-family review codex/agy/deepseek):** the probe can't rank seminar content (all clean), so the «Веснянки» sample was fact-verified. **Writers → codex + claude + agy** (all factually clean, mutually cross-family). **deepseek + cursor are NOT seminar writers:** deepseek made 1 hard error (царинні conflated with юр'ївські cattle-drive songs — confident scholarly specificity that was wrong; it conceded on review), cursor made 2 (веснянки «від хати до хати» = over-generalised риндзівки/волочебні; «мелодії легкі, м'які, співочі» = inverted musicology). **Seminar review → agy / codex / grok-4.5 / claude ONLY (LANGUAGE-LANES RULE, user 2026-07-17; the former deepseek seat is retired — its царинні hard error stands as supporting evidence)**, **always paired with a source-enforced fact-check gate** (`seminar-content-review` skill + `sources` MCP) — never a bare LLM pass. FOLK pairing stays GPT↔Claude per `docs/folk-epic/folk-review-rubric.md`. **Lesson: "sounds scholarly" ≠ "is accurate" — verify confident specificity, don't trust it.** **Review (russicism/surzhyk/CEFR):** one of the four language lanes + `sources` MCP (`verify_words`, `check_russian_shadow`, `query_cefr_level`); agy strong here. ⚠️ **cursor: EXCLUDED from all language seats (LANGUAGE-LANES RULE)** — its bakeoff history (non-canonical apostrophes U+2019, text-dependent russicism «перекатні») stands as supporting evidence only. **Never pool/glm/gemma/kimi/deepseek for UK content either** (same rule). |
| Adversarial review of design / ADR / architecture / code — the **Claude reviewer seat** | **Prefer IN-SESSION INLINE for cost** — the interactive orchestrator reads the artifact, verifies claims, writes the verdict + fix notes on the main quota (cheapest path; economics below). When the requested model is Fable, route `claude-fable-5` through native Claude first and use pinned Cursor Fable only if native Claude does not expose it. Dispatching Claude (`claude -p` / `--agent claude` / `review-deep` / an `Agent` review subagent) **is permitted when it adds value or inline isn't feasible** — the `-p` sunset was cancelled (user 2026-06-22). For routine reviews still prefer inline or a non-Claude lane; reserve dispatched Claude for catches that need it. Context heavy → DEFER to the next interactive session, or dispatch if it must clear now. |
| Q&A or single-shot review without commit | `ab ask-codex` / `ab ask-agy --to-model gemini-3.6-flash-high` for routine/agentic (top AGY default), `--to-model gemini-3.1-pro-high` only for deep single-shot (gemini-cli retired → agy) |
| Live web fact-check (current version / pricing / URL & citation currency, "is this API still live") | **opencode + lightpanda-MCP HARNESS capability — any opencode-hosted model browses** (kubedojo-verified incl. deepseek); it is NOT model-specific. Route by fit: `ab ask-pool` (poolside.ai, **free**) · `ab ask-glm` (⚠️ LOCAL-ONLY, China-egress) · or an opencode-hosted deepseek. |
| Search / grep / "find me X" across files | Native Codex subagent, default `gpt-5.6-luna` @ `max`, with explicit owned paths and an objective scope ceiling |
| Status check on running dispatches | Monitor API curl, never inline file scans |

If I'm about to write code inline and it doesn't match row 1, STOP and dispatch instead. Tooling enforces (worktree + commits) — memory does not.

**Use agy more (user 2026-06-24):** route content / wiki / pedagogy / factual **review** + bounded scripts / fixtures / migrations / docs-near-code to **agy** by default — its §7-fabrication fence is lifted (cleared 2026-06-13) and its pedagogy/CEFR review is strong (it led the 2026-06-24 practice-hub panel). It is **metered**, so be cost-aware, not absent — don't under-use it where it's strong. Keep cross-file architecture / security-concurrency / auth-heavy git / mass-mechanical on codex/claude. Confirm its model via `ab check-model` / `--help` (changes often; the bridge labels it Gemini-3.5-Flash-High, panels route `--to-model gemini-3.1-pro-high`).

**Writer routing refinement (user-confirmed 2026-07-07):** general content writing runs on **codex + agy** (agy = the standout A1-A2 immersion teaching voice per the 2026-07-04 bakeoff — do not forget it exists); the Claude window is SAVED for judgment work (architecture, adversarial review, hard bugs — codex is the primary coder, not Claude). The **V7 PIPELINE writer seat is separate**: it stays `claude-tools` because that seat is in-harness TOOL-CALLING fit, not prose (codex-tools emitted `tool_calls=0`); after any Claude-model rotation, spot-check ONE module before the next batch.

**CodexBar pace/reserve (width truth source):** the working command is the CodexBar CLI —
`codexbar usage --json --provider <codex|claude|gemini|cursor|grok|kimi>`. It returns
`usage.{primary,secondary,tertiary}.usedPercent` for every lane it can probe, but
`pace.<window>.{stage,summary,deltaPercent,willLastToReset}` is only available for
**codex** (secondary window only) and **claude** (primary + secondary). Measured right now:

| lane | has `pace` | pace windows | `usage.secondary` |
| --- | --- | --- | --- |
| codex | yes | `secondary` | object |
| claude | yes | `primary`, `secondary` | object |
| gemini | no | — | null |
| cursor | no | — | object |
| grok | no | — | null |
| kimi | no | — | object |

For **codex** and **claude**, read the SIGNAL (`pace.<window>.stage` + reserve /
`willLastToReset`) to decide width. For **gemini/cursor/grok/kimi** the operator is partly
blind to pace: fall back to `usage.<window>.usedPercent`, in-flight count, and lane health,
and SAY the picture is partial rather than guessing. `/api/state/routing-budget` +
`delegate --check-budget` mirror the same signal but have historically dropped it
(`burn_pct_7d: null` / `remaining_pct: null` per lane) — a null there is MISSING DATA, not zero
usage and not zero remaining; when they disagree or return nulls, trust the CLI. It does not list every API/routed model and therefore
must never define the fleet by itself. Grok 4.5 and GPT/Codex never route through Hermes. Kimi K3 is a separate
native OAuth subscription lane (`kimi-code/k3`, max effort, tool/image/video input; do not publish a
context-size claim until the native provider documents it). API-billed lanes such as DeepSeek may be absent from CodexBar by design; absence is unknown
headroom, not unavailability. Shed load only to models that meet the same task-risk quality floor.

**Kimi lane:** native Kimi Code OAuth only. Use K3 (`kimi-code/k3`, always-thinking,
max effort) for consequential coding, strong cross-family review, long-context debugging, and deep
asks. Use `k2.7-coding` / `k2.7-coding-highspeed` for routine or bulk coding. Do not demote K3 merely
because the cheaper model exists; risk and fit establish the quality floor first. Kimi is Moonshot
family. Composer 2.5 is Cursor-trained from a Kimi K2.5 checkpoint, so conservatively treat Composer
and Kimi as the same Moonshot independence family. Neither is currently a Ukrainian factual/folk gate.
K3 is **not a QG judge**; the standing judge pairing remains Gemini↔GPT.
**Supersession (user directive 2026-07-17):** K3 is now operator-classified as a top model and is
eligible for automatic cross-family code-review ladders. This replaces the 2026-07-16 canary-only /
zero-automatic-weight restriction; continued local bakeoffs refine its ordering but do not erase it.

## Fleet topology — orchestrator · advisor · workers (user directive 2026-07-11; multi-orchestrator 2026-07-21)

Standing role assignment for orchestrated sessions (names rotate; route by the role, not the label).
Machine-readable pins: `scripts/config/model_catalog.yaml` → `orchestrator_seats` + `formal_cf_defaults`.

- **Orchestrator seats (fleet-comms stream #5512 / #4707)** — any of these may own a cold-start /
  drive-board loop (prioritize → delegate → request CF → merge-in-lane). Do **not** run worker-level
  implementation on the orchestrator seat — delegate it (>50 LOC non-test, mechanical, fixtures, or
  anything parallelizable → a worker). **Codex was re-added as a driver seat** (user 2026-07-23),
  reversing the 2026-07-22 removal: HydrationCapsuleV1 makes its rollover cost acceptable. Machine
  authority: `model_catalog.yaml` → `orchestrator_seats` (lint: #5642).

  Human-readable summary (pins must match the marked projection below):

  | Seat | Default (loop) | Escalate (deep) | Notes |
  | --- | --- | --- | --- |
  | **claude** | `claude-fable-5` @ high | **`gpt-5.6-sol` @ xhigh** | Escalation is CROSS-FAMILY: Claude is a target, not an escalator. Other lanes escalate **to** Claude (`claude-fable-5` @ xhigh) or to Sol — pick by CodexBar headroom. Fable drives in the SUMMONED cadence only (see § Orchestration operating pattern) |
  | **codex** | `gpt-5.6-terra` @ high | **`gpt-5.6-sol` @ xhigh** | Named alternate for harness / infra / devops; never co-owns a live lease |
  | **grok** | `grok-4.5` @ high | same SKU (no higher pin yet) | Cursor **explicit** `grok-4.5` = availability fallback, not quality escalate |
  | **agy** | `gemini-3.6-flash-high` @ high | **`gemini-3.1-pro-high` @ high** | Flash loop; Pro deep single-shot |

  <!-- fleet-roster-projection:begin orchestrator_seats -->
  | seat | model_id | effort | escalate_model_id | escalate_effort |
  | --- | --- | --- | --- | --- |
  | agy | gemini-3.6-flash-high | high | gemini-3.1-pro-high | high |
  | claude | claude-fable-5 | high | gpt-5.6-sol | xhigh |
  | codex | gpt-5.6-terra | high | gpt-5.6-sol | xhigh |
  | grok | grok-4.5 | high | grok-4.5 | high |
  <!-- fleet-roster-projection:end orchestrator_seats -->

  **Escalate when:** deep single-shot, architecture, hard multi-file judgment, high-stakes synthesis —
  not for routine queue grind. Machine fields: `escalate_model_id` / `escalate_effort` /
  `escalate_when` on each seat in `model_catalog.yaml`.

## Orchestration operating pattern (operator 2026-07-26 — binding)

The knowledge-monopoly + quota-burn cycle (only the Anthropic frontier seat holds the whole
system; letting it drive daily exhausts the weekly in ~2 days; cheaper drivers then degrade
the system until it returns) is broken by ROLE SPLIT, not by a better single driver:

* **Daily driver: `grok-4.5`** — owns the epic loops (dispatch, babysit, settle, reap,
  re-fire) under the mechanical rails (evidence-mandatory reviews, lease lifecycle,
  merge/stamp guards, delegate origin-sync). Operator-rated the best price/quality
  orchestrator currently available.
* **Summoned judgment: `claude-fable-5`** — NOT a resident driver. One or two SHORT
  scheduled sessions per day: read the fleet's verdicts, correct course, lock designs,
  write the next precise briefs, leave. Drive dispatch-heavy, never inline-heavy
  (measured 2026-07-26: a dispatch-heavy Fable orchestration hour costs ~2 weekly-quota
  points; inline-heavy driving is what burns the window in days). Also the escalation
  target and top Anthropic advisor seat.
* **Understudy trial: `glm-5.2`** — sanctioned as a BOUNDED driver trial on one epic under
  the standard capsule/handoff contract (operator 2026-07-26; untested as driver, repeatedly
  the sharpest cheap seat on code review). Evaluate against the same rails; report before
  widening.
* **GPT lane never orchestrates as primary.** If it did, the seat would be Sol — and it is
  not worth it: orientation alone consumes ~33% of the GPT context window before any work
  (operator measurement 2026-07-26). Sol stays advisor/escalation-only; the codex seat
  remains a named ALTERNATE (HydrationCapsuleV1 exists to cut exactly that orientation
  cost), never the daily driver.
* Session-cadence seats stay unchanged for kimi (capable, slow), agy (compaction loses
  orchestration state — not a driver), gemini CLI (retired → agy).

  When an orchestrator needs **formal sealed CF**, request it via
  `review-pr --reviewer codex|claude|glm` (agy|kimi|grok remain `formal_review_eligible: false`
  until #5555–#5557). Authority CF escalate:
  `review-pr <N> --model gpt-5.6-sol --effort xhigh` or
  `review-pr <N> --reviewer claude --model claude-fable-5 --effort xhigh`.

  <!-- fleet-roster-projection:begin formal_review_eligible -->
  | endpoint | formal_review_eligible |
  | --- | --- |
  | agy | false |
  | claude | true |
  | codex | true |
  | cursor | false |
  | gemini | false |
  | glm-local | false |
  | grok | false |
  | kimi | false |
  <!-- fleet-roster-projection:end formal_review_eligible -->

* **Advisor = `gpt-5.6-sol` @ `high` (on-demand, NOT a standing worker).** The
  `execution_routing.sol_advised_bounded` catalog route makes Sol produce a bounded
  envelope containing the task contract, exact owned paths, maximum changed-file
  and non-test-LOC ceilings, constraints, risk boundaries, acceptance evidence,
  and escalation triggers. Do not use Sol for routine work; explicit escalation
  may raise effort to `xhigh`/`max`.
* **Sol-advised bounded execution:** when that envelope is complete, prefer
  `gpt-5.6-luna` @ `max` for bounded implementation or investigation. Luna must
  follow the envelope rather than re-decide its contract, and must escalate
  any owned-path or scope-ceiling overrun, consequential architecture, security,
  release, high-risk go/no-go, unresolved consequential ambiguity, broader
  integration, or final disposition.
* **Direct bounded execution:** use Luna @ `max` without a Sol envelope only
  when the accountable root supplies exact owned paths, an objective scope
  ceiling, and a non-consequential task contract. This covers bounded
  implementation/investigation, recon, checks, and test/log triage. A missing
  ceiling, broader autonomous integration, or unresolved consequential
  ambiguity routes to Terra @ `high`.
* **Review boundary:** Sol and Luna are both OpenAI-family seats. Sol's advisory
  output never satisfies the independent cross-family review gate.
* **Workers = every other lane** — `gpt-5.6-terra` / `gpt-5.6-luna` (codex coding, not driver),
  `cursor`, `kimi`, `deepseek`, `pool` (**Laguna family exact IDs:** default **`laguna-s-2.1`** gen-2 S; light **`laguna-xs-2.1`** gen-2 XS; fallback only **`laguna-m.1`** gen-1 — never invent s2/m2 orthography),
  `gemma`, `glm` (LOCAL-ONLY), plus non-orchestrating use of the seats above. They do the build /
  implementation / mechanical / review work. Keep lanes busy; queue rather than idle.

This names who orchestrates vs advises vs works. The cross-family review gate, the per-task routing rows
above, and the GPT-5.6 Sol/Terra/Luna row below are unchanged — this is the standing topology over them.

### Worker priority ladder — first pick per work type (user standing order 2026-07-11: stop re-deriving this)

Route by FIT, then shed from HOT lanes — fanout WIDTH is decided by CodexBar **pace stage + reserve**
(`codexbar usage --json --provider <lane>`; read `pace.<window>.{stage,summary,deltaPercent,willLastToReset}`),
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
| **Coding / impl / fixtures** | **Luna @ `max`** for bounded work with exact owned paths + an objective scope ceiling; use a complete Sol envelope when consequential boundaries need definition. **Terra @ `high`** for broader autonomous integration or unresolved ambiguity | **agy** — default `gemini-3.6-flash-high` (agentic workhorse ≈ Terra/Sonnet class); Pro only for deep | cursor · grok | claude seat = only ≤5-LOC CI-fix-I-caused; Luna never sole authority |
| **Code review** (cross-family = outside author's family) | **critical only:** Opus/Fable ↔ Sol (authority) | **high/medium/low formal CF defaults:** `gpt-5.6-terra` · `claude-sonnet-5` · `gemini-3.6-flash-high` · native `grok-4.5` (Cursor **`grok-4.5` explicit** if native dark) · Kimi K3 · GLM-5.2 · DeepSeek V4 Pro · pool **`laguna-s-2.1`** | **second dissent / volume:** Pool S 2.1 · DeepSeek Flash · Gemini 3.5 Flash | `review-pr` pins Terra/Sonnet5/GLM @ **high**; resolve-reviewer walks `model_catalog.yaml` ladders; cost never lowers quality floor within a risk rung |
| **UK content authoring** (author immersion-first, never translate) | **agy** (A1–A2 voice) ≈ **codex** | **claude** (B1–C2, sparingly — save the window) | **grok-4.5** | **LANGUAGE-LANES RULE below binds**: only these four; cursor/deepseek/kimi/pool/glm/gemma excluded |
| **Content / factual / CEFR review** (VESUM-gated) | **agy** (pedagogy/CEFR, + `sources` MCP) | **codex** · **grok-4.5** | **claude** (judgment tier) | **LANGUAGE-LANES RULE below binds**; NO grok as a QG judge seat (separate standing ban); FOLK stays cross-family GPT↔Claude per the folk rubric |
| **Research / recon / triage** | **Luna @ `max`** with exact owned paths + an objective scope ceiling; add a Sol envelope when the boundaries themselves need judgment | Terra @ `high` for broader or ambiguous work | agy | Luna never sole authority on consequential calls |
| **Live web fact-check** (pricing/URL/citation currency) | any opencode model — pool (FREE) · glm (LOCAL) · deepseek | — | — | browsing = harness property, not a model trait |

**LANGUAGE-LANES RULE (HARD, user order 2026-07-17): ALL language-related work — Ukrainian authoring, linguistic/content review, CEFR/russicism analysis, anything that judges Ukrainian text — routes ONLY to claude, codex, gemini (agy), or grok-4.5.** deepseek, glm, kimi, cursor, pool, and gemma are excluded from every language seat (deepseek's former VESUM-gated content-review default is retired; gemma's surface-review slice applies to non-language work only). Standing carve-outs still bind on top: NO deepseek for folk (moot under this rule, kept for history), grok is never a QG judge seat, folk review pairing stays GPT↔Claude. Code/infra/tooling work is unaffected.

**Advisor (on-demand, HARD calls only): `gpt-5.6-sol @ high` by default** — architecture, high-stakes design/ADR review, difficult debugging, final synthesis, or a bounded advisory envelope. Raise effort only for an explicit escalation; never use Sol for routine work. **Excluded:** qwen (cost). **LOCAL-ONLY:** glm (China-egress, never CI). **Cross-family review gate holds:** the reviewer must be outside the author's model family.

**Kimi onboarding (native `kimi`):** dispatch with `.venv/bin/python scripts/delegate.py dispatch --agent kimi`; explicitly select `--model k3` whenever the task is consequential. K3 is the frontier-practical Moonshot seat (max-only effort); `k2.7-coding` and its high-speed variant are routine workers. Current quota affects selection only among models that clear the task's quality floor. Kimi is a clean cross-family reviewer for GPT/Google/Claude/xAI authors, but not for Composer 2.5 because both conservatively share Moonshot lineage.

## Fleet discussion panels — actively involve ≥1 other agent before committing (user order 2026-06-23)

Drive high-judgment work (design, architecture, in-the-loop review, brief authoring) YOURSELF in-context — the frontier Claude lane does not brain-rot in-session (canary-verified on Opus 4.8; Fable 5 improvised 10/10 @ ~500K/1M 2026-07-07; a NEWLY rotated model must mint its own canary at cold-start per workflow.md — rot evidence is per-model, names rotate). But for any SUBSTANTIVE design / decision, **actively DISCUSS + cross-verify with the fleet BEFORE committing** — not solo dispatch-and-merge. Default to ≥1 other agent per substantive task; solo only for trivial work. Convene by lane:

- **Module-content panel** (writers, content review — LANGUAGE-LANES RULE binds): **agy** (Gemini 3.6 Flash default; Gemini 3.1 Pro for deep) · **GPT-5.6 Terra/Sol by risk** · **claude** · **grok-4.5**. ~~cursor seat~~ removed (excluded from language seats, user 2026-07-17). Prefer a bake-off + cross-family verification. Folk content review stays **cross-family (GPT↔Claude)** per `docs/folk-epic/folk-review-rubric.md` — **NO DeepSeek for folk culture** (lacks intrinsic Ukrainian-culture knowledge).
- **Infra panel** (code, gates, pipeline, tooling, schemas, Atlas/lexicon): **agy** (Gemini 3.6 Flash top default / agentic / **orchestrator seat**; 3.1 Pro deep; 3.5 Flash back-compat) · **GPT-5.6 Terra/Sol** · **cursor Composer 2.5** · **native Grok 4.5** · **Kimi K3** · **DeepSeek V4 Pro** · **Pool Laguna S 2.1** (free review volume) · **GLM-5.2** (deep security/bug review + large-context coherence; LOCAL-ONLY) · **Gemma 4** (surface review only). Pin Cursor's concrete model whenever family independence matters.

Invocation (`scripts/ai_agent_bridge/__main__.py`): `ask-codex` · `ask-agy --to-model gemini-3.6-flash-high` (orchestrator/routine default; `--to-model gemini-3.1-pro-high` only for deep) · `ask-cursor --model auto` (or `--model composer-2.5`) · `ask-grok` (alias `ask-grok-build`) · `ask-pool [--variant high|max]` · `ask-glm` (LOCAL-ONLY) · `ask-gemma` (cheap; ⚠️ not a sole seminar writer / factual reviewer) · `discuss <channel> "<topic>" --with <a,b,c>` for a bounded multi-round. **deepseek has NO `ask-*`** — route it via `delegate.py dispatch --agent deepseek --model deepseek-v4-pro` (first-party by default; `--provider openrouter` for opt-in per #4358). Bridge `ask-*` replies arrive as INBOX MESSAGES (`ab read <id>`), not stdout.

**opencode-routed cross-family reviewers (pool · glm · gemma):** opencode is a multi-provider ROUTER — the fleet member is the MODEL, not "opencode" (`ask-opencode <model>` is the generic escape hatch; `ask-pool`/`ask-glm`/`ask-gemma` are the named members). **Live web fact-checking is a HARNESS property (opencode + lightpanda MCP), NOT a model trait — any opencode-hosted model browses** (kubedojo-verified incl. deepseek); don't treat it as unique to pool/glm. Since the coding floor is uniformly high across the fleet, route by the DIFFERENTIATOR (kubedojo 5-agent scorecard 2026-07-04): **pool** = **free** cross-family code review + web-verify *volume*; **glm** = deep security/bug review + **large-context cross-file coherence audits**; grok = sharpest final code-review gate; deepseek = cheap all-rounder (+ browses when opencode-hosted); **gemma** (Google Gemma 4 via **`google-ais/gemma-4-31b-it`, $0 DEFAULT** — AIS-direct with the user's key, no paid SKU exists for Gemma on the Gemini API; TOOLLESS `chat` agent; paid OR `-it` via `--model` fallback only, note the spend; OR `:free` pool-starved, avoid) = a metered-lane OFFLOAD for **(a) cheap SURFACE review** — reliably flags russicisms/calques, Latin-letter leakage, imperial/decolonization framing — — **(b) wiki drafting RETIRED from gemma (LANGUAGE-LANES RULE 2026-07-17: wiki prose is language work → agy/codex/claude/grok-4.5 only; the 2026-07-05 source-citation probe evidence stands in `docs/projects/qg-quality-gate/model-evidence.md`). ** ⚠️ it is **NOT a sole seminar writer** (adds unsupported details beyond the source packet) and **NOT a sole factual reviewer** (not trustworthy on accuracy yet) — gate seminar/factual work behind a **non-Gemma** source/factual check; Google-family → not a clean reviewer of agy/Gemini work. **pool and glm are NOT for Ukrainian content / prose / pedagogy** — both are code models (glm anglicizes/code-switches, pool is worse); for UK content see the "Ukrainian CONTENT" row above (we author, not translate; cursor is NOT russicism-safe on long UK text). **pool** = poolside.ai **`laguna-s-2.1`** (default gen-2 S; also `laguna-xs-2.1` / fallback `laguna-m.1`), **free** (watch weekly limits on bursts). ⚠️ **glm** = Zhipu `glm-5.2`, **China-hosted (Zhipu/z.ai) → prompt data egresses to China → LOCAL-ONLY: never in CI / automated pipelines or with sensitive data** (`ask-glm` refuses under any CI env var as a backstop); prefer a Western-lab reviewer for top-stakes. Bridge (consult/review) only today — no `delegate.py --agent pool|glm|gemma` dispatch adapter yet, and no V7 `--writer gemma-tools` yet (the opencode→delegate adapter + tool-calling writer harness are scoped follow-ups; a plain OpenRouter chat model has no `sources`-MCP harness).

## Advisor panels — per-area pools · pool-minus-author · size-by-stakes · Sol/Fable anchor (#5933, operator-ruled 2026-07-28)

Advisory panels are a RULE, not a roster. **Per-area advisor assignment is the PRIMARY
structure** — each top model has distinct strengths; the pool modifiers operate WITHIN the
area's pool, with ONE exception: the anchor (modifier 3) is an OVERLAY seat that joins from
outside the pool when the pool contains neither Sol nor Fable. Panels are DISCUSSION/advice
for CONVENED design and judgment work; an ordinary formal PR review is NOT an advisory
panel (the "do not burn advisor seats on routine work" economy rule stands), and a panel
never replaces the independent CROSS-FAMILY review of record (discussion ≠ review), which
composes on top.

**Per-area advisor pools** (the operator's approval surface; the table is REVIEWED when
seats rotate — operator wording; the catalog-refresh contract §above owns name→model):

| Area | Advisor pool | Evidence anchor |
| --- | --- | --- |
| Ukrainian language & pedagogy | Fable · Sol · Gemini (sanctioned language seats ONLY) | LANGUAGE-LANES RULE binds |
| Architecture & process design | Sol (designer seat) · Fable (counter-reader) | fleet topology §above |
| Code & infrastructure review | Kimi K3 · GLM-5.2 · Terra | Terra review arcs on #5896/#5925/#5926/#5931 (defect-finding record) |
| Security-sensitive changes | Terra/GPT family · Kimi | ambient-Anthropic-token→z.ai leak caught pre-merge (#5931 arc) |
| Debugging & forensics | Grok · GLM-5.2 | Grok: #5932 root cause (#5950 workaround); GLM: operator statement, #5933 comment 2026-07-28 |
| Long-context sweeps & harness infra | Gemini | model catalog §above (window/tooling) |

Terra's presence in area pools is as a practical PANEL PARTICIPANT — it does not promote
`gpt-5.6-terra` to the advisor tier (the "not an advisor" authority rule §topology stands).

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
     if neither Sol nor Fable qualifies (both in-family or author), the pool's strongest
     cross-family seat serves instead and the waived anchor is RECORDED on the work item.
3. **ANCHOR RULE** — Sol or Fable sits on EVERY convened advisory panel: whichever of the
   two is available and is NOT the author. In pools lacking both (code/infra, security,
   debugging, long-context), the anchor joins as the outside-pool overlay seat per above.

**Standing constraints (unchanged, restated because they bound the pools):** no Kimi/GLM on
language judgment (#M-13a) · grok is NEVER a judge seat · GLM-5.2 is LOCAL-ONLY (China
egress — no CI, no secrets, no sensitive data).

*Operational notes (not #5933 rulings; separate authority cited):* Gemma is not an advisor
seat (§panels above) · for code reviews prefer Kimi first per the #5933 issue body's
reliability guidance — noting the GLM transport fix landed 2026-07-28 (#5947) · on any ask
transport failure, reroute BY SEAT within the pool and record the substitution
(workflow.md substitution rule).

## Harness vs model — route by BOTH (added 2026-07-05; user order: fleet utilization is paramount)

A fleet member = MODEL × HARNESS. The same model behaves differently in different harnesses, and
several models are reachable through more than one. Know both axes before routing:

| Harness | What it adds to ANY model it hosts | Models routed through it | Entry points¹ |
| --- | --- | --- | --- |
| **hermes** (v0.18.x — full agent platform, NOT a thin wrapper) | SOUL.md project persona · `sources` MCP (30+ UK tools) auto-attached · 16 built-in toolsets (web, browser, terminal, code-exec, files, delegation, cron, session-search…) · session store w/ FTS5 search · agent loop up to 90 turns | deepseek (API key) · zai/GLM (API key — ⚠️ same China-egress LOCAL-ONLY rule as opencode glm) · OpenRouter catalog (qwen², gemma, …) — probe `hermes auth list` | `ab ask-hermes --model <m>` (one-shot Q&A/review) · `delegate.py dispatch --agent deepseek\|qwen² --mode danger --worktree` (execution — worktree MANDATORY per delegate-must-use-worktree) · V7 `--writer/--reviewer deepseek-tools\|qwen-tools` (all hermes-backed) |
| **opencode** (multi-provider router) | lightpanda MCP configured (`~/.config/opencode/opencode.jsonc`) → **live web browsing/fact-check is a HARNESS property here**, available to tool-capable hosted models (kubedojo-verified for pool·glm·deepseek routes; verify before relying on a new route) | pool (poolside **laguna-s-2.1**, free; m.1 prior-gen fallback) · glm (⚠️ LOCAL-ONLY) · gemma · deepseek-direct (first-party `api.deepseek.com`; #4358/#4626 QG bakeoff default) · OpenRouter deepseek/gemma baselines · any OpenRouter model | `ab ask-pool` / `ask-glm` / `ask-gemma` (named) · `ab ask-opencode <model>` (generic) |
| **native CLIs** (codex, cursor, agy, grok, claude, kimi) | each CLI's own tool loop + repo context; capabilities differ per CLI. GPT/Codex is **native-only**: never route it through Hermes. Grok: never Hermes; native CLI = interactive/operator seat (effort control) + drive wiring; **opencode hosting sanctioned for orchestrator seats** (operator 2026-07-27, see Consequences below). `grok` = the native Grok CLI seat (alias `grok-build` kept permanently); `kimi` = native Kimi Code OAuth seat (models `k3` · `k2.7-coding` · `k2.7-coding-highspeed`) | one primary family each; Cursor is multi-model and must be pinned for review identity | `ab ask-codex` / `ask-cursor` / `ask-agy` / `ask-grok-build` / `ask-claude` / `ask-kimi` · `delegate.py dispatch --agent <a> --mode danger --worktree` (includes `--agent kimi`) · orchestrator grok via `ab ask-opencode --model xai/grok-4.5` |

¹ `ab` = the user's shell alias for `.venv/bin/python scripts/ai_agent_bridge/__main__.py`.
In scripts, docs meant for copy-paste, and anything automated, ALWAYS write the full path —
bare `ab` resolves to ApacheBench (`/usr/sbin/ab`) outside the user's shell (AGENTS.md rule).
There is NO `ask-deepseek`: one-shot deepseek = `ask-hermes --model <deepseek-model>` (first-party
as attributed on 2026-07-07) or `ask-opencode deepseek-direct/<deepseek-model>`; execution =
`delegate.py dispatch --agent deepseek`. `openrouter/deepseek/*` is **guard-REFUSED** (user order
2026-07-07 — the OR account was drained by deepseek bakeoff cells; deepseek runs FIRST-PARTY only.
The user's OR BYOK now bills deepseek underneath, so transport-comparison runs (#4321/#4358) are
billing-safe behind `LU_ROUTING_GUARD_OVERRIDE=1` — deliberate, user-authorized only).
² Qwen is excluded from routine routing; `glm-5.2` (Zhipu/opencode) is used for cross-family code and review.

Consequences:
- **A model "lacking" a capability may just be in the wrong harness** — deepseek can't browse
  natively but browses via opencode; any hermes-hosted model gets VESUM/`sources` tools for free.
- **Limits are per-harness-credential, not per-model**: when a lane quotas out, the same model is
  often reachable through another harness (e.g. deepseek via delegate-hermes ↔ opencode), but
  **GPT/Codex and Claude are hard exceptions**: keep both on their native CLIs (operator
  ruling 2026-07-27 for Claude) and never substitute a Codex OAuth-backed Hermes model or a
  non-native Claude host. **Grok (updated by operator ruling 2026-07-27):** never Hermes
  (`grok-hermes`/`grok-tools` stay banned), but **`opencode` hosting IS sanctioned for
  ORCHESTRATOR seats** — first-party `xai/grok-4.5` on the xAI subscription OAuth
  (probe-verified: tools work; ⚠️ NO effort control on this route — `effort_applied: null`).
  The native `grok` CLI remains the interactive/operator seat (effort control, drive wiring)
  and the preferred seat wherever effort tiering matters; Cursor stays the fallback. Never
  route grok via OpenRouter model ids (`openrouter/x-ai/*`) — only the first-party `xai/*`
  provider is sub-backed. Check `hermes auth list` + `/api/orient` headroom.
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

## Gemini 3.6 Flash vs 3.1 Pro (onboarded 2026-07-21)

Operator directive: **Gemini 3.6 Flash is the AGY top default** (agentic workhorse).

| Model | Catalog slug | Tier | Use |
| --- | --- | --- | --- |
| Gemini 3.6 Flash (High) | `gemini-3.6-flash-high` | `frontier_practical` | Default AGY dispatch/Q&A; subagents; fast tool loops; day-to-day coding |
| Gemini 3.1 Pro (High) | `gemini-3.1-pro-high` | `frontier_practical` | Deep single-shot reasoning, architecture support, high-stakes factual review |
| Gemini 3.5 Flash (High) | `gemini-3.5-flash-high` | `strong_efficient` | Back-compat / volume only |

**Tier calibration (operator claim checked):** 3.6 Flash is roughly **Terra / Sonnet 5 class** for agentic coding throughput — **not** Sol/Fable/Opus authority, and **not** a full replacement for 3.1 Pro on deep one-shot architecture. Prefer 3.6 Flash first; escalate to 3.1 Pro (or Sol/Fable) when depth matters more than loop efficiency.

## GPT-5.6 family (Sol · Terra · Luna) — onboarded 2026-07-09 (user directive)

All three tiers expose **272K context (~258.4K effectively usable before the context-management margin)** on the native Codex route and accept text+image input. This matches the [corrected Codex CLI 0.144.6 model metadata](https://learn.chatgpt.com/docs/changelog#month-2026-07) (2026-07-18). Cursor and the direct OpenAI API may advertise larger windows; do not use those route-specific limits to size native Codex or CLIProxyAPI-over-Codex-OAuth prompts. Tier choice = capability/cost routing, not context size. Effort levels apply on every tier.

| Tier | Model id | Use for | Effort policy |
| --- | --- | --- | --- |
| Sol | `gpt-5.6-sol` | Frontier lead: hard architecture, high-stakes advisory/review, bounded advisory envelopes, difficult debugging, final synthesis | **START = `high`** (never below high); `xhigh`/`max` only for explicit escalation |
| Terra | `gpt-5.6-terra` | Balanced default: normal implementation, scoped planning, investigations, standard reviews (≈5.5-level quality, cheaper) | default `high`; `xhigh` for the hardest cells |
| Luna | `gpt-5.6-luna` | Default high-volume bounded worker: focused implementation/investigation, recon, test/log triage, mechanical checks, and draft summaries with exact owned paths + an objective scope ceiling. **NEVER sole authority** on consequential decisions or release approval | `max` for bounded work; add a Sol envelope when task boundaries need authority judgment |

Policy: **prefer 5.6 for NEW work**; retain 5.5/5.4 only for pinned workflows (qg_bakeoff arms, the V7 pipeline reviewer seat until spot-checked post-reset), proven compatibility, or quota pressure. Codex dispatch + `ask-codex` defaults = `gpt-5.6-terra`.

**Luna economics refresh (operator directive 2026-08-01):** OpenAI cut Luna API
pricing by 80% on 2026-07-30; current standard short-context token rates and
Codex plan limits place it at roughly one tenth of Terra for equivalent usage
units. Promote Luna @ `max` for bounded worker tasks; this cost/throughput
change does not grant advisor, orchestrator, release, or formal-review
authority. Terra remains the autonomous-integration fallback, and independent
cross-family review still binds.

Probe evidence (2026-07-09): `luna@medium` QG 69-item triage PASS (69/69 processed, 5/5 spot-verified verdicts, 160s); `sol@xhigh` (Layer B design) + `terra@high` (#4824 fix) probes ran same day; Sonnet-5-vs-Terra and Haiku-4.5-vs-Luna matched pairs queued for the 07-13 claude reset.

Anthropic tier mapping for cross-family routing: Sol ≈ Fable 5 / Opus 4.8 · Terra ≈ Sonnet 5 · Luna ≈ Haiku 4.5. Claude lanes keep the 1M-context edge — route giant-context work (cross-file coherence audits, corpus reads) to Claude/gemini, not 5.6.

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

Non-Claude reviewers are UNAFFECTED for NON-LANGUAGE work (LANGUAGE-LANES RULE binds for anything judging Ukrainian text) — keep routing the bulk of CODE/infra reviews to them: DeepSeek (rows above) for PR
diffs, Codex for novel-architecture catches. (VESUM/content review = language work → the four language lanes only.) The *Claude* seat is **preferred** in-session for cost.
(The headless `--agent claude` / `claude -p` lane is AVAILABLE again — the mid-June 2026 sunset / "native binary not
installed" fiasco was cancelled, user 2026-06-22; Claude may be used for ANY task, incl. dispatched review, when needed.
The cost economics above stand regardless: dispatched Claude is far pricier than inline, so route by need, not by ban.)

The same table lives in `memory/MEMORY.md` rule #M0; this file is the deploy-rule mirror so it loads via `npm run agents:deploy` into `.claude/rules/`.

</critical>

## Formal PR CF review (fleet-comms Phase 4–5)

For **GitHub PR formal cross-family review**, do **not** use fat `ask-* --review` with a pasted diff or PR URL body.

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py review-pr <N>
# pins: codex→gpt-5.6-terra@high · --reviewer claude→claude-sonnet-5@high · --reviewer glm→glm-5.2
# after sealed review returns a short verdict file:
.venv/bin/python scripts/ai_agent_bridge/__main__.py publish-review-verdict \
  --pr <N> --verdict-file /tmp/verdict.txt --model <model> --family <family> --harness <harness>
```

**AGY orchestrator** (`gemini-3.6-flash-high` @ high) runs the loop and still *requests* CF with
`review-pr` above — do not treat `ask-agy --review` as sealed formal CF until #5555 flips
`formal_review_eligible`.

Bridge steers with a **warning** (not refuse) if `ask-* --review` looks like PR CF
without a sealed target — so agent work is not discarded (#5486 warn-not-reject).
Size caps still fail closed. See `docs/best-practices/agent-bridge.md`.
