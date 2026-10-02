# Fleet driver routing — mandatory card + breadth (operator GO 2026-08-06)

**Failure prevented:** Epic drivers (especially Grok) fixate on a small subset of
seats (e.g. Claude Sonnet only), under-use heap/economical workers, and rarely
use **advisor → cheap implement** even when a Sol advisory envelope would unlock Luna
or weaker models. Measured incident: atlas night drive 2026-08-06 used 2/9
catalog seats with 33% dispatch `done` rate while free lanes sat idle.

**Enforcement point:** Always-loaded `/api/rules` (this file) + `drive-epic` skill
§ routing card + mechanical breadth report script. Soft-hard: drivers must
attach tool-backed breadth evidence on handoff; missing card is a process defect.

**Owner:** fleet / harness lane; source path this file +
`scripts/fleet/driver_breadth_report.py`.

**False-positive budget:** NOTE with tool-backed reason (near_cap, language-lane
only, PATH/tool outage already substituted) is allowed; silent single-seat
marathons are not.

**Escape:** Operator or advisor (Fable/Astra) may waive breadth for one named
session with a written NOTE on the issue/handoff. Cannot become the default.

**Sunset review:** 2026-09-06 or when breadth report shows median driver
breadth ≥3 agents and ≥2 tiers for 14 consecutive days.

---

## 1. Agent ≠ model; three work tiers

| Operator name | Catalog tier | Role | Examples (confirm live ids in `model_catalog.yaml`) |
| --- | --- | --- | --- |
| **Big brain / advisor** | `frontier_authority` | One-shot judgment, **briefs**, contested design; high-stakes CF of record only on an eligible route, never from an advisory turn | **claude-opus-5-5** (Opus 5.5) / **gpt-6.1-sol** (Sol 6.1 @ high) first; Fable / Astra last resort; bounded envelopes use Sol only (§2) |
| **Hard implement / practical** | `frontier_practical` | Autonomous multi-file when scope is clear; standard CF | **GPT-6.1 Sol @ high** (Codex coding/review), Claude Opus 5.5 for hard Claude-lane coding, Gemini 3.8 Flash for well-defined work, Kimi K3 (web, UI and backend coding only), Grok 4.7 (code/infra CF only through the runtime-attested Cursor seat below critical, #9488; never a content judge) |
| **Heap / volume** | `economical` / strong_efficient | Bounded routine implementation, scouting, and recon | **GPT-6 Luna @ high**, Flash-class, other volume seats |

**Codex role boundary:** GPT-6.1 Sol (`gpt-6.1-sol`) @ `high` is the only Sol: the coding and
review seat and, since operator 2026-09-29 (#9230), also holds the named Astra advisory seat at `high`.
Ordinary advice uses Opus 5.5 / Sol 6.1 first; the named Astra seat is last resort (#9394).
Luna @ `high` handles routine bounded work and scouting under a Sol advisory envelope (§2).
`gpt-6-sol` and `gpt-6-astra` are not routable. Designated approval remains separate
from ordinary advice; do not spend advisory turns on ordinary implementation or review.

**Standing routing preference (#9394):** Opus 5.5 / Sol 6.1 first; Fable / Astra
last resort. Designated approval by Fable, Astra or the operator remains unchanged.
When last-resort Fable is required, use this transport order:

1. Native Claude seat with model pin **claude-fable-5-1** (first transport for last-resort Fable), or
2. **Cursor** multi-model pin to Fable (use composite identity for CF author/review
   bookkeeping, e.g. `cursor:claude-fable-5-1` per `resolve_author_family` rules).

Do **not** use the Fable/Astra advisory role on lockfiles, pointer publishes, rsync gates, or smoke
`--limit 5` jobs.

---

### 1b. Free-lane utilization (operator 2026-08-08 / #6468; capacity-first 2026-08-12 / #4707)

**Cursor (operator 2026-09-22; Auto scope operator decision 2026-09-30):** pass an explicit
`--model`. `auto` is allowed only for a well-defined coding task — a dispatch typed
`--research-role implementation` in a write-capable mode with `--owned-path` and a PASS DoR issue
card; `delegate.py` refuses it otherwise. The driver seat, design, consults, discussions, recon and
unclear work pin `grok-4.7` or `composer-2.5`; a review runs the approved concrete model the reviewer
resolver selects. Cursor has two monthly pools ([Models & Pricing](https://cursor.com/docs/models-and-pricing)).
For mechanical and ordinary infra/code implement that is not LANGUAGE-LANES and not
advisor/authority, prefer `--agent cursor --model grok-4.7-high` while the Cursor Models
pool has headroom. A review of a Grok author must use an Other Models slug, not a Grok
slug. DeepSeek is excluded from dispatch and review; `deepseek-v4.1-flash` remains active in the catalog, and Pro is retired.

**Utilize, do not trim.** Keep **Kimi** and **Z.AI/GLM** as first-class seats. Live check:
`.venv/bin/python -m scripts.fleet.capacity_pick` (preferred) +
`.venv/bin/python -m scripts.fleet.usage show` (per-lane remaining% + pace lines)
+ `/api/delegate/active` + disk. (`codexbar usage` is retired — do not cite it.)

**Mandatory pre-dispatch (binding):** Before every implement `delegate.py dispatch`, run:

```bash
.venv/bin/python -m scripts.fleet.capacity_pick
# pace detail per lane (remaining%, pace lines, will_last, deficit):
.venv/bin/python -m scripts.fleet.usage show
# then dispatch with budget guard (flag or LU_DISPATCH_CHECK_BUDGET=1):
.venv/bin/python scripts/delegate.py dispatch --check-budget ...
```

**Refuse deficit when cooler seats exist.** Do **not** habit-route to Codex (or any
subscription lane) while `usage show` / `routing-budget` shows hot / near_cap /
deficit (visible pace, projected to run out before reset, and more than 2 points
ahead of pace; near_cap ≥ 90% unchanged) or a thinning reserve **and** `capacity_pick`
lists cool/idle free seats
(Cursor, AGY, GLM, Kimi, …). `--check-budget` hard-subs when
`dispatch_fallbacks` has a row (e.g. `codex → cursor`); otherwise it **refuses**
unless `--force-agent` with a written NOTE.

**Concurrent drivers (typical):** ~**2 Grok** + **1 Claude** + **1–4 Codex**. Shared free
worker pools — coordinate via active-delegate + disjoint owned paths so drivers do not
stampede one hot lane.

| Free / behind seat | Prefer for | Pin |
| --- | --- | --- |
| **Cursor, included pool** | code/infra CI, mechanical + ordinary infra/code implement | `--agent cursor --model grok-4.7-high`. Not Fast, not `grok-4.6`, not `grok-4.5`. Not CF of a Grok author |
| **Cursor, Other Models** | cross-family review of a Grok author, or a named third-party model | `--agent cursor --model claude-sonnet-5-5-high`. Draws the API pool. |
| **DeepSeek V4.1 Flash** | Excluded from dispatch and review | `deepseek-v4.1-flash` remains active in the catalog; Pro is retired. `ask-deepseek` is consult-only for non-language work, never implementation or review. |
| **Kimi k3-256k** | everyday fast coding/impl | `--agent kimi --model k3-256k` (or catalog id `kimi-code/k3-256k`) |
| **Kimi k3** | complex / long-context coding only (Kimi: web, UI and backend coding only — no Ukrainian-language content, no reviews, consults, design or rules) | `--model k3` @ high/max — not routine queue |
| **AGY Gemini Flash** | agentic scripts, language-lane content | `gemini-3.8-flash-high` |
| **Pool Laguna S 2.1** | free CF + web-verify volume | `ask-pool` (OpenRouter mainly Pool+Gemma) |
| **Z.AI GLM-5.3** (**keep**) | deep security / large-context coherence | `ask-glm` LOCAL-ONLY; z.ai account; 5h when weekly hot |
| **Claude Sonnet** | routine judgment/CF | Opus 5.5 / Sol 6.1 first for hard judgment; Fable / Astra last resort; ~1 Claude driver |

**OpenRouter:** mainly **Pool + Gemma**. Not a general multi-model bus.

**Codex near_cap / timed pause / deficit:** shed mechanical CI to Cursor `grok-4.7-high` / k3-256k / GLM
(`capacity_pick` + `dispatch_fallbacks: codex → cursor`); code/infra review goes to the
`resolve-reviewer` pick, which may be the attested Cursor Grok seat below critical (#9488). A valid operator reset
reserve can temporarily admit Codex Sol despite a hot or near-cap pace signal. It never overrides
an exhausted or unknown weekly allotment, runtime blockage, stale usage, or unhealthy route.

**Credit-balance lanes (#9518):** a lane in `scripts/config/credit_lanes.yaml` whose plan allowance
is at or below the near-cap threshold and whose fresh probe carries a positive credit balance shows
as `credit_balance_present` in `capacity_pick`: credit balance present; draw not verified by the
router. It is usable only while there is no evidence against it, ranked after plan-backed seats,
with its balance, evidence, coverage and reset advice. The router follows one rule: one or more
`rate_limited` runtime outcomes for the lane within `rate_limit_window_s` (60 minutes) while the
plan window is exhausted read `credit_use_unconfirmed` and keep near_cap/AVOID. Missing, stale,
naive-timestamp or non-numeric credit data also keep near_cap/AVOID. While a lane shows a credit
balance, `delegate.py dispatch` refuses any model outside its allowlist (Codex: `gpt-6.1-sol`,
`gpt-6-luna`) with `CREDIT_PERIOD_MODEL_REFUSED`; a dispatch without `--model` is judged by the lane
default. A broken policy file restricts only Codex, to the built-in copy of that allowlist; other
lanes are unaffected. The reset advice is text only: spending a free full reset stays an operator
decision, and no tool consumes credits or resets.
Luna handles bounded work under a Sol advisory envelope (§2); hard advice uses Opus 5.5 / Sol 6.1
first, Fable / Astra last resort.

The operator records a shared assertion at `batch_state/routing_budget/operator_reset_reserve.json`
in the primary checkout. Its exact JSON fields are `schema_version` (`operator-reset-reserve.v1`),
`provider` (`codex`), positive integer `remaining_resets`, and UTC ISO-8601 `confirmed_at` /
`expires_at`. Expiry must be after confirmation and at most 24 hours later. Dispatch worktrees
read the same assertion; missing, malformed, expired, or unverified input leaves the reserve
unavailable. The assertion is read-only to routing and never decremented automatically. The
operator must confirm and refresh the count and expiry; no agent infers them from usage data.

### Cursor pools (checked 2026-09-22)

Source: [cursor.com/docs/models-and-pricing](https://cursor.com/docs/models-and-pricing). Prices are USD per million tokens. Pass the CLI slug with `--model`. Do not send a Fast variant or a previous generation. Send `auto` only for a well-defined coding dispatch (owned paths, PASS DoR card; operator decision 2026-09-30); it spends the Auto allocation.

**Cursor Models pool.** More included usage. Grok and Composer are exempt from the Teams/Enterprise token rate ($0.25 per million on third-party requests). Our pin in this pool is `grok-4.7-high` (Grok 4.7, not Fast).

| Model | Input | Cache read | Output | Send |
| --- | --- | --- | --- | --- |
| Grok 4.7 | $2 | $0.50 | $6 | `grok-4.7-high` |
| Grok 4.7 Fast | $4 | $1 | $12 | do not send |
| Composer 2.5 | $0.50 | $0.20 | $2.50 | `composer-2.5` (concrete pin; operator decision 2026-09-30) |
| Composer 2.5 Fast | $3 | $0.50 | $15 | do not send |
| Grok 4.6, Grok 4.5 | $2 | $0.50 | $6 | do not send |

**Other Models pool.** Included on Pro, Pro Plus, and Ultra, then on-demand at the same API price. Start does not include this pool. Use this pool when the reviewer must be outside xAI.

| Model | Input | Cache write | Cache read | Output | Slug |
| --- | --- | --- | --- | --- | --- |
| Claude Sonnet 5.5 | $2 | $2.50 | $0.20 | $10 | `claude-sonnet-5-5-high` |
| Claude Opus 5.5 | — | — | — | — | `claude-opus-5-5-high` |
| Claude Fable 5.1 | $10 | $12.50 | $0.25 | $50 | `claude-fable-5-1-thinking-high` |
| Gemini 3.8 Flash | $0.75 | — | $0.075 | $3.50 | pass only if `cursor-agent --list-models` shows it |

Cursor's catalog has no GPT-6 slug; GPT-6.1 Sol and GPT-6 Luna run on the native Codex CLI.
Claude Opus 5.5 hard coding uses the native Claude CLI where applicable, or Cursor's
supported `claude-opus-5-5-high` slug. `claude-fable-5-thinking-high` is Fable 5,
not 5.1.

Full table: `model-assignment.md` § *No-idle utilization + transport map*. Issue: **#6468** / stream **#6943**.

## 2. Default execution shape (binding)

For **bounded** work (clear owned paths, objective acceptance command, no open
architecture decision):

```text
0) Driver fixes the worker dispatch arguments and prints their binding digest:
   delegate.py dispatch <worker args> --print-advisory-binding
1) ADVISOR envelope from the catalog advisor route (the Sol advisor (`gpt-6.1-sol` @ high)):
   delegate.py dispatch --agent codex --model gpt-6.1-sol --mode read-only \
     --advisory-role bounded_advisory_envelope --advisory-binding <digest> ...
   → task_contract, owned_paths, max_changed_files, max_non_test_loc, constraints,
     risk_boundaries, acceptance_evidence, escalation_triggers
2) BOUNDED worker executes ONLY that envelope:
   delegate.py dispatch <worker args> --advisory-task <advisor task id>
3) Driver integrates; formal CF = independent cross-family (discussion ≠ CF)
```

This is the catalog `execution_routing.sol_advised_bounded` route. **Operator decision
2026-09-30 (#9275): there is no direct bounded dispatch.** Every dispatch to the bounded
worker (`gpt-6-luna`), and to its `gemini-3.8-flash-high` fallback unless the dispatch is
classified Ukrainian authoring or review, needs a complete envelope from a finished
`gpt-6.1-sol` advisor task bound to that dispatch's arguments and prompt text; `delegate.py` refuses it
otherwise (`BOUNDED_ENVELOPE_REQUIRED`), including after a budget substitution, and fails
the worker at finalize when it exceeds the envelope ceilings (a completion gate checked after
the worker exits, not a limit on what it does while running). A second completion gate
fails a Ukrainian-classified `gemini-3.8-flash-high` write worker whose changes include a
code file or a path outside the Ukrainian content roots (`advisory_exempt_code_change`),
because admission can only classify the files its owned paths held then. The envelope's `owned_paths`
must equal the worker's `--owned-path` set. A Fable brief is design advice; it is not an
envelope and does not admit a bounded worker (the packet path used to be "Fable or Astra";
it is now the catalog advisor route only). Routine lockfile, pointer and smoke tasks take
no advisory seat, so they go to a non-bounded worker (for example `claude-sonnet-5-5`)
instead of a bounded one. Native Codex subagents spawned in-session by a `gpt-6.1-sol`
parent run under that parent's own contract; the parent is their advisor and sets their
owned paths and ceilings. Advisory family **never** satisfies cross-family PR CF.

For **unbounded / ambiguous** work: practical or authority implementer only after
the routing card records why heap was refused.

---

## 3. Mandatory pre-dispatch routing card

Before **every** `delegate.py dispatch` and before every cross-family review
request that spends a scarce seat, the live driver MUST record (handoff, issue
comment, or `batch_state/` receipt — not only inner monologue):

```text
ROUTING_CARD_V1
task_id: <id>
tier: authority | practical | heap
model_x_harness: <e.g. codex/gpt-6-luna>   # both axes
why_this_tier: <one sentence>
advisor_packet: none | sol=<advisor task id>  # required for heap; delegate refuses Luna/Flash without it
owned_paths: <paths>
acceptance_cmd: <deterministic command that proves done>
alternatives_considered:
  - <seat/model> — free/busy — why not
  - <seat/model> — free/busy — why not
parallel_free_seats: <from /api/orient or delegate list; or "none tool-proved">
NOTE_if_single_seat: <required if only one worker family used this session so far>
```

**Refuse to dispatch** (process defect) if:

- `tier: heap` and `advisor_packet: none`, or
- `alternatives_considered` has fewer than two rows without a tool-backed NOTE, or
- the same practical seat is chosen for the 3rd consecutive implement dispatch
  without a breadth NOTE (near_cap / PATH / language-lane).

---

## 4. Session breadth floor (binding for epic drivers)

Within one driver session (or one calendar day of the same `initiator` prefix,
whichever the breadth script reports):

| After | Minimum |
| --- | --- |
| ≥3 implement dispatches | ≥**2** distinct **agents** AND ≥**2** **tiers** used, **or** a single `NOTE: fleet_breadth` with tool-backed blockers |
| Handoff / FAIL-HANDOFF | Attach `.venv/bin/python -m scripts.fleet.driver_breadth_report --initiator <prefix> --since-hours 24` output (or equivalent). Missing report = incomplete handoff. |

Trivial one-shot (typo, single-file comment) is exempt if labeled
`ROUTING_CARD_V1 tier: heap` with `acceptance_cmd` and **no** multi-file product claim.

---

## 5. Work-class → default tier (atlas / infra examples)

| Work class | Default |
| --- | --- |
| Lockfile / Dependabot / pointer-only publish | heap or bot + light practical CF |
| VPS launcher scripts, health probes, rsync gates | practical |
| Residual lemma EN strategy, morphology policy | **authority brief** → heap fill |
| Routine formal CF | practical cross-family |
| Contested CF / architecture / process | Opus 5.5 / Sol 6.1 first; Fable / Astra last resort; operator escalation unchanged; formal CF remains independent and task-qualified |
| UK content authoring | language-lane only (existing model-assignment) |

---

## 6. Mechanical report

```bash
.venv/bin/python -m scripts.fleet.driver_breadth_report --help
.venv/bin/python -m scripts.fleet.driver_breadth_report --initiator grok --since-hours 24
.venv/bin/python -m scripts.fleet.driver_breadth_report --initiator grok --since-hours 24 --enforce
```

`--enforce` exits **2** when the breadth floor fails without a recorded NOTE file
path (optional `--note-file`), or when idle-settle telemetry contains MISSING
or DISHONEST dispositions. It never fails on raw idle opportunity-seconds.
`--note-file` waives the breadth floor only. Drivers run this before handoff;
CI may call it later in advisory mode. Live Monitor idle dashboard remains
deferred (#6998).

---

## 7. Relationship to other rules

- Does **not** weaken operator-expectations §4 (whole fleet) or §5 (route by fit).
- Does **not** replace model-assignment live ladders — it **forces the card** and
  **advisor→heap default**.
- Cross-family review remains independent (`model-assignment` + direct `ask-*`);
  shielded formal `review-pr` is retired.
- Advisor approval gate for architecture still binds (operator-expectations §12).
