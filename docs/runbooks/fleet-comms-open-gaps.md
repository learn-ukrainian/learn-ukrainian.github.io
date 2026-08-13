# Fleet communication open gaps — runbook

Status board for the three residual fleet-comms problems after Sol phases 0–5.

## 1. Large ask replies — #5392

**Problem:** Big review/diff replies could land as a short SQLite body with no
marker that transport clipped them.

**Fix (code):** `scripts/ai_agent_bridge/_reply_sidecar.py` + `send_message`.

- Responses over `AB_REPLY_INLINE_MAX_BYTES` (default **12 KiB**), or that match
  mid-deliverable tail heuristics, write the **full** body to
  `batch_state/asks/<task-id>/reply-<agent>-<sha16>.md` (gitignored).
- The messages-table body becomes a head excerpt + explicit footer:

  ```
  TRUNCATED: full reply offloaded to sidecar …
  path: …
  sha256: …
  bytes: …
  ```

- Metadata JSON also carries `reply_sidecar: {path, sha256, bytes, truncated}`.

**Operator:** when you see `TRUNCATED`, open the path — do not re-run the model
just because the inline body looks short.

## 2. Session-stream dual-write (not full cutover)

**Shipped:** SQLite streams + phase-one CLI; live streams include
`epic:4387` (atlas), `epic:4707` (infra), `epic:4542`, `epic:4706`.

**This PR:** dual-write inventory without retiring files:

```bash
.venv/bin/python -m agents_extensions.shared.session_streams dual-write-status
.venv/bin/python -m agents_extensions.shared.session_streams inventory --register
# DB-first projection receipts + drift detection (no file rewrite / no cutover):
.venv/bin/python -m agents_extensions.shared.session_streams project
.venv/bin/python -m agents_extensions.shared.session_streams check-drift
# under an active lease (SESSION_STREAM_* env):
.venv/bin/python -m agents_extensions.shared.session_streams mirror-handoff \
  --stream epic:4387
```

Registry: manifest inventory from `scripts/config/issue_streams.yaml` via
`agents_extensions/shared/session_streams/inventory.py` (Sol PR-H; not a hard-coded
epic subset). Projection receipts land in `legacy_projection_receipts` after
inventory; unrecorded file mutation is flagged as `drift` without flipping modes.

**Still blocked for the session-stream continuity cutover:** operator gate
after per-harness acceptance; session handoff files remain authoritative for
continuity until then. This does not reopen legacy message-plane writes: Fleet
Comms is already authoritative for message-plane coordination.

## 3. Hygiene residuals

| Issue | Fix |
| --- | --- |
| **#5113** dead `gemini` inbox nags | Backlog warnings skip `dead_lane_agents()`; expire via `ab cleanup --expire` (already bulk-expires dead lanes). |
| **#4915** empty body on background process | `assert_ask_content_present` on process paths — empty DB body fails as **transport**, not model stall. |
| **#4956** disk retention | Read-only scanner: `.venv/bin/python scripts/hygiene/lane_disk_retention.py [--include-home] [--json]` |

## Orchestrator seats (fleet-comms stream)

Any of these may own a cold-start / drive-board loop. Pins live in
`scripts/config/model_catalog.yaml` → `orchestrator_seats`. **Codex was re-added as a driver**
(user 2026-07-23), reversing the 2026-07-22 removal because HydrationCapsuleV1 reduces rollover
overhead; it is the named harness / infra / devops alternate, never a concurrent co-owner. Drift
lint: #5642 / `scripts/lint/lint_fleet_roster.py`.

| Seat | Default (loop) | Escalate (deep) | Sealed formal CF as *reviewer* |
| --- | --- | --- | --- |
| **claude** | `claude-fable-5` @ high | **`gpt-5.6-sol` @ xhigh** (cross-family) | yes (`review-pr --reviewer claude`; Sonnet default, Fable explicit) |
| **codex** | `gpt-5.6-terra` @ high | **`gpt-5.6-sol` @ xhigh** | yes (`review-pr --reviewer codex`) |
| **grok** | `grok-4.5` @ high | same SKU (Cursor = avail. fallback) | yes (`review-pr --reviewer grok`) |
| **agy** | `gemini-3.7-flash-high` @ high | **`gemini-3.1-pro-high` @ high** | no until #5555 — still *requests* CF |

<!-- fleet-roster-projection:begin orchestrator_seats -->
| seat | model_id | effort | escalate_model_id | escalate_effort |
| --- | --- | --- | --- | --- |
| agy | gemini-3.7-flash-high | high | gemini-3.1-pro-high | high |
| claude | claude-fable-5 | high | gpt-5.6-sol | xhigh |
| codex | gpt-5.6-terra | high | gpt-5.6-sol | xhigh |
| grok | grok-4.5 | high | grok-4.5 | high |
<!-- fleet-roster-projection:end orchestrator_seats -->

Escalate when: architecture, hard multi-file judgment, high-stakes synthesis — not routine queue.

```bash
# AGY default / escalate
.venv/bin/python scripts/delegate.py dispatch --agent agy --model gemini-3.7-flash-high ...
.venv/bin/python scripts/delegate.py dispatch --agent agy --model gemini-3.1-pro-high ...
# Claude escalate
.venv/bin/python scripts/delegate.py dispatch --agent claude --model claude-fable-5 ...
# Codex named alternate / formal-CF authority escalate
.venv/bin/python scripts/delegate.py dispatch --agent codex --model gpt-5.6-sol ...
```

## Formal CF defaults (orchestrator-ready)

Machine eligibility and routing SSOT: `scripts/config/model_catalog.yaml` →
`review_scheduler.endpoints`. It binds the exact model, family, sealed ACP
participant, formal eligibility, and quota/credential bucket. The booleans in
`fleet_communications.yaml` are a tested legacy status projection, not a
second policy source.

The orchestrator supplies semantic requirements: author model/family, role,
profile, risk, capabilities, egress, isolation, and whether an exceptional pin
is justified. The deterministic scheduler then applies this order:

1. hard safety, availability, isolation, egress, context, and cross-family gates;
2. task-role suitability and the best acceptable quality tier;
3. only among equally suitable candidates in that tier, normalized rolling
   assigned bytes, reserved bytes, capacity weight, verified quota headroom,
   in-flight work, failures, and finally the exact-head stable hash.

This is not round-robin and no LLM participates in routing. An idle or cheap
model never outranks a stronger model for the requested job. Subscription calls
still consume scarce quota and future optionality, so pressure can choose only
inside an equivalent suitable pool or trigger a documented eligible fallback.
Near-cap and open-circuit buckets receive no automatic work.

<!-- fleet-roster-projection:begin formal_review_eligible -->
| endpoint | formal_review_eligible |
| --- | --- |
| agy | false |
| claude | true |
| codex | true |
| cursor | false |
| gemini | false |
| glm-local | true |
| grok | true |
| kimi | false |
<!-- fleet-roster-projection:end formal_review_eligible -->

Practical seats @ **high** — not Sol/Fable on routine PRs:

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py review-pr <N> \
  --initiator codex/orchestrator \
  --author-model gpt-5.6-sol --author-family openai \
  --review-profile code --risk high

# Exceptional pin: still passes every hard gate and uses the same reservation ledger.
.venv/bin/python scripts/ai_agent_bridge/__main__.py review-pr <N> \
  --initiator codex/orchestrator \
  --author-model gpt-5.6-sol --author-family openai \
  --reviewer claude --model claude-fable-5 --effort high \
  --override-reason "operator-requested Fable dissent"

.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-pool ...  # default Laguna S 2.1
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-pool ... --model poolside/poolside/laguna-xs-2.1  # XS 2.1 light
```

Automatic selection and admission occur in one `BEGIN IMMEDIATE` transaction
in the shared Fleet Comms authority database. Reservations have a TTL; startup
recovery expires orphaned holders. Retryable automatic transport failures
settle and open the failed quota/credential circuit before another eligible
bucket is selected. Explicit pins never switch provider unless
`--allow-explicit-fallback` was also supplied. A completed identical exact-head
request replays the durable verdict without a provider call or reservation.

### Diagnose quota concentration

- Open `runtime.html` → **Routing overview**. Start with the lifecycle,
  automatic-versus-explicit, route-distribution, and failure-cause cards, then
  filter by lifecycle, mode, route, initiator, model, reviewer, or failure.
- Read the decision path as initiator → request → selected route/model →
  outcome. Expand one assignment for the body-free selection trace, quota and
  credential evidence, retry/failover/replay state, authority IDs, and ordered
  lifecycle events.
- Query `/api/runtime/routing-assignments?limit=100` for the same read-only
  projection. Counts describe the loaded recent window, not all-time fleet
  totals, configured routing weights, provider quotas, or caching.
- Treat “No ledger update” as stale activity evidence only. It is not proof of
  provider liveness and does not authorize early lease reclamation.
- Compare the decision trace's hard-gate and suitability reasons before blaming
  load: a deliberately stronger suitable model may receive more work.
- Confirm provider headroom with CodexBar and inspect the durable authority
  job/reservation state. A timeout or malformed quota probe retains the last
  known good record and exposes failure metadata separately.
- Concentration among truly equivalent suitable candidates indicates stale
  reservations, a shared credential bucket, circuit failures, or bad capacity
  weights—not a reason to weaken the quality floor.

### Migration, restart, and rollback

Fleet Comms migration v7 is additive, idempotent, and applied on authority-store
startup. During rollout, stop old orchestrator processes, restart the Fleet
Comms/Runtime API processes with the repository's existing service launcher,
then verify authority mode and the routing-assignment endpoint before resuming
formal reviews. Do not delete or downgrade the v7 tables.

To roll back, stop formal-review callers, revert the scheduler/bridge application
change, restart those same processes, and leave the additive ledger tables in
place for audit/recovery. The explicit message-plane environment override
remains the separate Fleet Comms authority rollback control; changing it does
not erase routing evidence.

### Poolside Laguna model types (exact IDs)

| Generation | Vendor name | Catalog / API id | Fleet role |
| --- | --- | --- | --- |
| **Gen-2 (current)** | **Laguna S 2.1** | `poolside/laguna-s-2.1` | **Default** pool formal/volume (`ask-pool`, ladder `pool`) |
| **Gen-2 (current)** | **Laguna XS 2.1** | `poolside/laguna-xs-2.1` | Light/fast volume (`pool-xs` ladder; `--model …/laguna-xs-2.1`) |
| **Gen-1 (prior)** | **Laguna M.1** | `poolside/laguna-m.1` | Fallback only — superseded by S/XS 2.1 |
| **Not released** | Laguna M 2.x | — | Do not invent IDs |

Do **not** write `laguna-s2`, `laguna.s2`, or `laguna.m1` as IDs — hyphens and the `m.1` minor are load-bearing.

- Resolve-reviewer: **critical** keeps Sol/Fable authority first; **high/medium/low** walk Terra → Sonnet 5 → **Gemini 3.7 Flash (agy)** → Grok (native then Cursor explicit `grok-4.5`) → K3 → GLM → DS-Pro → pool **S 2.1** → pool **XS 2.1** / 3.5 Flash …
- Grok uses the proven exact-head source-blind ACP path. Kimi K3's adapter is implemented but stays fail-closed until an authenticated sealed canary passes. AGY's text-only ACP wrapper cannot consume the parent-owned sealed MCP; legacy native-isolation helpers stay unsupported.
- Isolation runbooks: `docs/runbooks/agy-formal-cf-isolation.md` · `kimi-formal-cf-isolation.md` · `grok-formal-cf-isolation.md`

## Closeout checklist

- [x] #5392 — green tests for sidecar + TRUNCATED footer (`tests/test_reply_sidecar.py` 8/8, 2026-07-22)
- [x] dual-write-status returns registered streams (`inventory --register` → 17/17 ok, drift=0; cutover still blocked by operator gate)
- [x] backlog warning does not mention `gemini` when it is a dead lane (`fleet_comms backlog` exclude_retired includes gemini; total=0)
- [x] empty-body process-ask records `transport empty-ask-body` (`tests/test_reply_sidecar.py` asserts raise + status)
- [x] formal CF model+effort pins + practical ladders (2026-07-21)
- [x] efficiency CLI: `fleet_comms metrics` / `github-metrics` / `dead-letters` (PR-M on main)
- [x] isolation runbooks AGY/Kimi/Grok; unsupported legacy native-isolation routes remain fail-closed
- [x] historical message-plane **shadow** soak after parity (#5666), superseded
  by the operator-approved `authority` cutover in #6159; `dual_write` is now a
  compatibility rollback mode
- [ ] operator: retention plan dry-run × ≥7 days before scheduled apply (auto-logged by `retention_engine.py plan`; apply still OFF; 3/7 as of 2026-07-23)
- [x] exact-head ACP sealed review: Claude, Codex, GLM, and Grok eligible; Kimi K3 adapter present but fail-closed pending its authenticated canary; AGY structurally fail-closed
- [ ] operator: Claude + Grok + Codex + AGY cold-start stream smoke (launchers dual-aware; live multi-CLI soak optional)
- [x] planned `dual_write`-default step superseded by #6159 authority cutover

## Legacy Broker Ops retirement evidence (#6106)

Use the seat-facing facade from any repository checkout:

```bash
.venv/bin/python -m scripts.fleet_comms fleet help
.venv/bin/python -m scripts.fleet_comms fleet status
.venv/bin/python -m scripts.fleet_comms fleet board
.venv/bin/python -m scripts.fleet_comms fleet backlog
.venv/bin/python -m scripts.fleet_comms fleet dead
.venv/bin/python -m scripts.fleet_comms fleet metrics
.venv/bin/python -m scripts.fleet_comms fleet reap-report
```

`fleet reap-report` is a dry run over merged PR heads. It passes through the
existing reaper's active-worktree, exact-merged-head, and dirty-tree guards.
`--apply` is available only for the same guarded reaper path.

Before proposing deletion of a Broker Ops page or a legacy route, choose a
window between 1 and 90 days and run:

```bash
.venv/bin/python -m scripts.fleet_comms fleet broker-report --days 7
```

The report reads `data/telemetry/legacy_comms_routes.db` without creating or
modifying it. A separate `data/telemetry/legacy_bridge` file is read when
present, and `--bridge-db` selects another explicit bridge store; current
bridge aggregates may be co-located in the route telemetry database. The
report separates direct seat activity, background automation, and `other`
(canary/test/unknown). `other` is not
silently treated as zero use.

An operator declares a zero-use window by adding the exact command, report
timestamp, requested window, and JSON `zero_use_candidate` result to the PR,
then writing present-tense approval such as: “I approve retiring `<slice>`
after the observed `<N>`-day zero-use window.” A deletion PR must retain that
approval text and the report output, and must not delete any page or route when
the report says `eligible: false`.
