# Fleet driver routing — mandatory card + breadth (operator GO 2026-08-06)

**Failure prevented:** Epic drivers (especially Grok) fixate on a small subset of
seats (e.g. Claude Sonnet only), under-use heap/economical workers, and rarely
use **advisor → cheap implement** even when an Astra/Fable brief would unlock Luna
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
| **Big brain / advisor** | `frontier_authority` | One-shot judgment, **briefs**, contested design; high-stakes CF of record only on an eligible non-Astra route | **claude-fable-5** (Fable), **gpt-6-astra** (Astra @ high, advisory only), Opus-class when roster says so |
| **Hard implement / practical** | `frontier_practical` | Autonomous multi-file when scope is clear; standard CF | **GPT-6 Sol @ high** (Codex coding/review), Claude Opus 5.5 for hard Claude-lane coding, Gemini 3.8 Flash for well-defined work, Kimi K3, Grok 4.7 (review/CF, not judge) |
| **Heap / volume** | `economical` / strong_efficient | Bounded routine implementation, scouting, and recon | **GPT-6 Luna @ high**, Flash-class, other volume seats |

**Codex role boundary:** Sol @ `high` is the coding and review seat; Luna @ `high`
handles routine bounded work and scouting; Astra @ `high` is reserved for hard,
consequential advisory judgment. Do not route ordinary implementation or review to Astra.

**Standing operator preference (2026-08-06):** Fable remains the Anthropic
authority seat even if the operator shrinks the Claude subscription. Reach Fable via:

1. Native Claude seat with model pin **claude-fable-5** (preferred when available), or
2. **Cursor** multi-model pin to Fable (use composite identity for CF author/review
   bookkeeping, e.g. `cursor:claude-fable-5` per `resolve_author_family` rules).

Do **not** use the Fable/Astra advisory role on lockfiles, pointer publishes, rsync gates, or smoke
`--limit 5` jobs.

---

### 1b. Free-lane utilization (operator 2026-08-08 / #6468; capacity-first 2026-08-12 / #4707)

**Cursor (operator 2026-09-22):** pass an explicit `--model`. Do not pass `auto`.
Cursor has two monthly pools ([Models & Pricing](https://cursor.com/docs/models-and-pricing)).
For mechanical and ordinary infra/code implement that is not LANGUAGE-LANES and not
advisor/authority, prefer `--agent cursor --model grok-4.7-high` while the Cursor Models
pool has headroom. A review of a Grok author must use an Other Models slug, not a Grok
slug. DeepSeek stays **Flash everyday**; **Pro @ high = hard implement only**.

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
deficit (`will_last_to_reset=False`) or a thinning reserve **and** `capacity_pick`
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
| **Cursor, Other Models** | cross-family review of a Grok author, or a named third-party model | `--agent cursor --model claude-sonnet-5-thinking-high`. Draws the API pool. |
| **DeepSeek V4 Flash** | code/infra CF + tool-heavy implement | `deepseek-v4-flash` default; **Pro @ high = hard implement only** (complex multi-file, hard lookup — operator GO 2026-08-13, canary #6703) |
| **Kimi k3-256k** | everyday fast coding/impl | `--agent kimi --model k3-256k` (or catalog id `kimi-code/k3-256k`) |
| **Kimi k3** | advisory / complex / long-context only | `--model k3` @ high/max — not routine queue |
| **AGY Gemini Flash** | agentic scripts, language-lane content | `gemini-3.8-flash-high` |
| **Pool Laguna S 2.1** | free CF + web-verify volume | `ask-pool` (OpenRouter mainly Pool+Gemma) |
| **Z.AI GLM-5.3** (**keep**) | deep security / large-context coherence | `ask-glm` LOCAL-ONLY; z.ai account; 5h when weekly hot |
| **Claude Sonnet** | routine judgment/CF | save Fable for summoned authority; ~1 Claude driver |

**OpenRouter:** mainly **Pool + Gemma**. Not a general multi-model bus.

**Codex near_cap / timed pause / deficit:** shed mechanical CI to Cursor `grok-4.7-high` / Flash / AGY /
k3-256k / GLM (`capacity_pick` + `dispatch_fallbacks: codex → cursor`). **Return-at example:** Codex weekly window **2026-08-10T19:47Z** → auto-return
to rotation. Novel/hard may stay on Astra/Luna among the 1–4 Codex drivers.

### Cursor pools (checked 2026-09-22)

Source: [cursor.com/docs/models-and-pricing](https://cursor.com/docs/models-and-pricing). Prices are USD per million tokens. Pass the CLI slug with `--model`. Do not send `auto`, a Fast variant, or a previous generation.

**Cursor Models pool.** More included usage. Grok and Composer are exempt from the Teams/Enterprise token rate ($0.25 per million on third-party requests). Our pin in this pool is `grok-4.7-high` (Grok 4.7, not Fast).

| Model | Input | Cache read | Output | Send |
| --- | --- | --- | --- | --- |
| Grok 4.7 | $2 | $0.50 | $6 | `grok-4.7-high` |
| Grok 4.7 Fast | $4 | $1 | $12 | do not send |
| Composer 2.5 | $0.50 | $0.20 | $2.50 | do not send (operator 2026-09-22) |
| Composer 2.5 Fast | $3 | $0.50 | $15 | do not send |
| Grok 4.6, Grok 4.5 | $2 | $0.50 | $6 | do not send |

**Other Models pool.** Included on Pro, Pro Plus, and Ultra, then on-demand at the same API price. Start does not include this pool. Use this pool when the reviewer must be outside xAI.

| Model | Input | Cache write | Cache read | Output | Slug |
| --- | --- | --- | --- | --- | --- |
| Claude Sonnet 5 | $2 | $2.50 | $0.20 | $10 | `claude-sonnet-5-thinking-high` |
| Claude Opus 5 | $5 | $6.25 | $0.50 | $25 | `claude-opus-5-thinking-high` |
| Claude Opus 5.5 | — | — | — | — | `claude-opus-5-5-high` |
| Claude Fable 5.1 | $10 | $12.50 | $0.25 | $50 | `claude-fable-5-1-thinking-high` |
| Gemini 3.8 Flash | $0.75 | — | $0.075 | $3.50 | pass only if `cursor-agent --list-models` shows it |

Cursor's catalog has no GPT-6 slug; GPT-6 Sol and Luna run on the native Codex CLI.
Claude Opus 5.5 hard coding uses the native Claude CLI where applicable, or Cursor's
supported `claude-opus-5-5-high` slug. `claude-fable-5-thinking-high` is Fable 5,
not 5.1.

Full table: `model-assignment.md` § *No-idle utilization + transport map*. Issue: **#6468** / stream **#6943**.

## 2. Default execution shape (binding)

For **bounded** work (clear owned paths, objective acceptance command, no open
architecture decision):

```text
1) AUTHORITY brief (Astra or Fable) → task_contract, owned_paths, scope ceiling,
   acceptance_evidence, escalation_triggers
2) HEAP / PRACTICAL worker(s) execute ONLY that packet
3) Driver integrates; formal CF = independent cross-family (discussion ≠ CF)
```

This is the catalog `execution_routing.sol_advised_bounded` idea generalized to
**Fable or Astra** as advisor. Advisory family **never** satisfies cross-family PR CF.

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
advisor_packet: none | astra | fable | other=<id>  # required for heap
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
| Contested CF / architecture / process | authority (Fable or Astra) |
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
