# Durable arc layer — long-term plans per epic, operator-visible, fleet-onboarded

- **Status**: ADOPTED DESIGN (advisor memo, verbatim below) — build sequenced behind the
  operator's #5897 decision; a limited two-epic pilot can proceed independently of #5912.
- **Provenance**: operator directive 2026-07-28 (durable long-term arcs/plans for each area
  and epic so other seats can develop them when the primary driving seat is unavailable;
  fleet onboarded to them; progress visible to the operator via the Monitor API + dashboard).
  Designed by the advisor seat (gpt-5.6-sol @ xhigh, bridge task `arc-layer-design-sol`,
  reply msg 5554, 2026-07-28). Tracking issue: #5921.
- **Operator calls required** (listed verbatim in §Operator calls): #5897 milestone
  semantics · ArcSpec authority model approval · #5912 epic re-parenting timing · review
  cadence + whether fleet-comms events ship in the initial build.
- **Build sequence** (memo's recommendation): #5897 decision → ArcSpec schema + two-epic
  pilot → API/UI + #5898 auditing → portfolio backfill → onboarding → optional derived
  events.

---

## Sol design memo — durable arc layer (gpt-5.6-sol, 2026-07-28, verbatim)

The main failure mode is split-brain: arcs must not become another backlog, handoff diary, or communications authority. The second risk is "fresh-looking aspiration"—dates get bumped while milestones remain unevidenced.

### Recommendation

Use one structured, reviewable ArcSpec per GitHub epic:

`docs/arcs/epics/<epic-number>.arc.yaml`

Do not create a second global arc registry. `scripts/config/issue_streams.yaml` already owns stream-to-epic membership. The API groups ArcSpecs by that registry.

For streams with several epics, exactly one active ArcSpec carries `stream_focus: true`; its current milestone projects into #5897's per-stream milestone line. Other active epics remain visible in the detailed area view.

| Layer | Authority |
|---|---|
| ArcSpec | Long-term destination, phases, evidence, current strategic focus |
| GitHub epic/sub-issues | Executable queue and acceptance criteria |
| `WORKSTREAMS.md` | Framework plus generated/checked focus projection |
| TrailSpec | How a driver executes the loop |
| Driver handoff + session stream | Live session continuity; file handoff remains authoritative |
| Fleet-comms events | Notifications only, never state |

An "area" should remain the stream projection of its epics, not another independently edited plan. If an area genuinely needs its own arc, represent it with an umbrella GitHub epic. This keeps one arc equal to one tracking issue.

### ArcSpec content contract

Require:

- `schema_version`, `epic`, lifecycle state, and `stream_focus`
- `mission`: one durable outcome sentence
- overall success criteria
- explicit guardrails/non-goals
- decision references with short rationale summaries
- ordered phases: stable ID, outcome, state, and evidence-shaped exit criteria
- current phase and milestone: stable IDs, outcome, and `done_when`
- one to three ordered next actions, each with an intent plus typed issue/decision/trail reference
- typed dependencies and unblock conditions
- evidence references for every completed phase
- `reviewed_at` attestation

Derive the owning stream and tracking URL from `issue_streams.yaml` and the epic number. Derive the actual last-change timestamp from Git. Do not manually duplicate lane names, live owners, issue titles, or `last_updated`.

Golden rule: **arcs encode where, why, and what proves arrival; live systems supply who, how, and what is happening now.**

### API and operator UI

Use a read-only file-backed router:

- `GET /api/arcs` — grouped summaries, optionally filtered by stream/state
- `GET /api/arcs/streams/{stream}` — area detail
- `GET /api/arcs/epics/{number}` — complete ArcSpec
- `GET /api/arcs/epics/{number}/capsule` — bounded cold-start summary
- `GET /api/arcs/health` — schema, coverage, drift, and freshness diagnostics

The API should read the live primary checkout, validate YAML, and cache only by file digest/mtime. Return the normalized arc hash and repository SHA. A cache is an optimization, never another registry.

Add an `Arcs` dashboard page showing:

- streams grouped in plain language;
- each epic's mission;
- named phase segments—no misleading percentage because phases are unequal;
- current milestone and next actions;
- blocked, stale, and decision-needed badges;
- last review time;
- secondary links to the epic and ArcSpec.

The dashboard must derive its phase bar from ArcSpec files. It must not reconstruct state from message history.

### Update discipline

Update an ArcSpec when strategy state changes, not at every session close:

- milestone starts, completes, or changes;
- a phase exits;
- the arc blocks or unblocks;
- a dependency or decision changes;
- ordered next actions materially change;
- mission, guardrails, or exit criteria are revised with advisor/operator approval.

Session detail stays in the driver handoff and stream.

Enforcement should distinguish:

- **ERROR:** invalid schema, multiple current phases, completed criteria without evidence, or projection mismatch. CI-blocking.
- **VACANT:** registered epic lacks an ArcSpec, stream focus, milestone, or next action.
- **DRIFT:** referenced action closed/missing while still current, incompatible phase state, or dependency contradiction.
- **STALE:** active arc has exceeded the approved review cadence.

Extend #5898 for scheduled VACANT/DRIFT/STALE warnings and SessionStart summaries. Do not block unrelated PRs merely because another arc aged. Registration of a new epic without its ArcSpec can become a scoped hard failure after backfill is complete.

### Fleet onboarding

Keep cold-start payloads small:

1. `/api/rules` adds one binding pointer: epic drivers must hydrate the exact ArcSpec before choosing work.
2. Launchers already know `epic:N`; inject mission, phase, milestone, age, arc hash, and the capsule endpoint—roughly three lines.
3. `drive-epic` records the consumed arc hash and milestone ID in its first state-at-start handoff/stream entry. A surfaced pointer alone is not evidence of reading.
4. If the API is unavailable, load `docs/arcs/epics/N.arc.yaml`.
5. Delegated briefs carry the arc hash, milestone ID, and selected action reference; children do not load the whole portfolio.
6. Send one fleet announcement only after #5897 sign-off and arc onboarding land. Do not send competing announcements now.

### Fleet-comms verdict

Repo file plus API polling is sufficient for the authoritative MVP.

Fleet-comms is useful afterward for low-latency, derived events such as:

- `arc.milestone.changed`
- `arc.phase.completed`
- `arc.blocked`

Emit these only after the ArcSpec change merges to `main`, with the repo SHA and arc hash. A failed or missing event must not affect correctness; the dashboard refreshes from files. Manual "milestone completed" posts must never advance the arc.

This does not alter plane authority, retention, or cutover. Existing file handoffs remain authoritative in `off`, `shadow`, and `dual_write`.

### Rejected

- Full arcs inside `WORKSTREAMS.md`: monolithic, high-contention, and duplicates #5897.
- One giant YAML registry: one invalid or conflicted file affects every lane.
- Free-form Markdown as API truth: difficult to validate and invites dashboard scraping.
- Named seat/person ownership: freezes a roster and defeats replacement-seat operation.
- Mandatory session-close arc edits: turns strategy into a diary.
- Database/API writes as primary state: creates split-brain with reviewed repo files.
- Fleet-comms messages as progress authority: implies an unsupported cutover.
- Calendar freshness alone: easily gamed; combine review age with evidence/state reconciliation.
- Loading every arc at every cold start: unnecessary context bloat.

### Operator calls required

1. Sign off or reject #5897's milestone semantics; ArcSpec must project into that accepted layer.
2. Approve the ArcSpec authority model: per-epic YAML, stream grouping from `issue_streams.yaml`, read-only API/UI, and no database authority.
3. Decide #5912's epic re-parenting before portfolio-wide completeness becomes mandatory. A limited pilot can proceed independently.
4. Choose the active-arc review cadence and whether fleet-comms events are included in the initial build or a later phase. Recommendation: warnings first; events after the file/API path is proven.

Suggested sequence: #5897 decision → ArcSpec schema and two-epic pilot → API/UI plus #5898 auditing → portfolio backfill → onboarding → optional derived events.
