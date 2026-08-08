# Fleet driver routing — mandatory card + breadth (operator GO 2026-08-06)

**Failure prevented:** Epic drivers (especially Grok) fixate on a small subset of
seats (e.g. Claude Sonnet only), under-use heap/economical workers, and rarely
use **advisor → cheap implement** even when a Sol/Fable brief would unlock Luna
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

**Escape:** Operator or advisor (Fable/Sol) may waive breadth for one named
session with a written NOTE on the issue/handoff. Cannot become the default.

**Sunset review:** 2026-09-06 or when breadth report shows median driver
breadth ≥3 agents and ≥2 tiers for 14 consecutive days.

---

## 1. Agent ≠ model; three work tiers

| Operator name | Catalog tier | Role | Examples (confirm live ids in `model_catalog.yaml`) |
| --- | --- | --- | --- |
| **Big brain / advisor** | `frontier_authority` | One-shot judgment, **briefs**, contested design, high-stakes CF of record | **claude-fable-5** (Fable), **gpt-5.6-sol** (Sol), Opus-class when roster says so |
| **Hard implement / practical** | `frontier_practical` | Autonomous multi-file when scope is clear; standard CF | gpt-5.6-terra, claude-sonnet-5, gemini-3.6-flash-high, kimi K3, grok-4.5 (review/CF not judge) |
| **Heap / volume** | `economical` / strong_efficient | Bounded implement after a complete advisory envelope | **gpt-5.6-luna** (max), Flash-class, other volume seats |

**Standing operator preference (2026-08-06):** Fable remains the Anthropic
authority seat even if the operator shrinks the Claude subscription. Reach Fable via:

1. Native Claude seat with model pin **claude-fable-5** (preferred when available), or  
2. **Cursor** multi-model pin to Fable (use composite identity for CF author/review
   bookkeeping, e.g. `cursor:claude-fable-5` per `resolve_author_family` rules).

Do **not** burn Fable/Sol on lockfiles, pointer publishes, rsync gates, or smoke
`--limit 5` jobs.

---

### 1b. Free-lane utilization (operator 2026-08-08)

Do **not** fixate on Codex/Claude while free seats sit idle. Live check:
`codexbar usage --json --provider <lane>` + `/api/delegate/active` + disk.

| Free / behind seat | Prefer for | Pin |
| --- | --- | --- |
| **Cursor Auto** | code/infra CI, mechanical-with-judgment | `--agent cursor` (default `auto`); never CF identity |
| **DeepSeek V4 Flash** | code/infra CF + tool-heavy implement | `deepseek-v4-flash` **only** — **Pro DO NOT USE** |
| **AGY Gemini Flash** | agentic scripts, language-lane content | `gemini-3.6-flash-high` |
| **Pool Laguna S 2.1** | free CF + web-verify volume | `ask-pool` (often OpenRouter path) |
| **Z.AI GLM-5.2** | deep security / large-context coherence | `ask-glm` LOCAL-ONLY; prefer 5h when weekly hot |
| **Claude Sonnet** | routine judgment/CF | save Fable for summoned authority |

**OpenRouter:** mainly **Pool + Gemma**. Can reach more; **do not** use as a general multi-model bus — native/first-party first.

**Codex near_cap:** shed mechanical CI (ruff, fingerprints, lockfile nits) to Cursor Auto / DeepSeek Flash / AGY. Novel/hard work may stay on Terra/Luna.

Full table + transport map: `model-assignment.md` § *No-idle utilization + transport map*.

## 2. Default execution shape (binding)

For **bounded** work (clear owned paths, objective acceptance command, no open
architecture decision):

```text
1) AUTHORITY brief (Sol or Fable) → task_contract, owned_paths, scope ceiling,
   acceptance_evidence, escalation_triggers
2) HEAP / PRACTICAL worker(s) execute ONLY that packet
3) Driver integrates; formal CF = independent cross-family (discussion ≠ CF)
```

This is the catalog `execution_routing.sol_advised_bounded` idea generalized to
**Fable or Sol** as advisor. Advisory family **never** satisfies cross-family PR CF.

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
model_x_harness: <e.g. codex/gpt-5.6-luna>   # both axes
why_this_tier: <one sentence>
advisor_packet: none | sol | fable | other=<id>  # required for heap
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
| Contested CF / architecture / process | authority (Fable or Sol) |
| UK content authoring | language-lane only (existing model-assignment) |

---

## 6. Mechanical report

```bash
.venv/bin/python -m scripts.fleet.driver_breadth_report --help
.venv/bin/python -m scripts.fleet.driver_breadth_report --initiator grok --since-hours 24
.venv/bin/python -m scripts.fleet.driver_breadth_report --initiator grok --since-hours 24 --enforce
```

`--enforce` exits **2** when the breadth floor fails without a recorded NOTE file
path (optional `--note-file`). Drivers run this before handoff; CI may call it
later in advisory mode.

---

## 7. Relationship to other rules

- Does **not** weaken operator-expectations §4 (whole fleet) or §5 (route by fit).  
- Does **not** replace model-assignment live ladders — it **forces the card** and
  **advisor→heap default**.  
- Cross-family review remains independent (`model-assignment` + direct `ask-*`);
  shielded formal `review-pr` is retired.  
- Advisor approval gate for architecture still binds (operator-expectations §12).
