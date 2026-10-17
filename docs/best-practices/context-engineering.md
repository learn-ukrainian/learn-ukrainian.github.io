# Context engineering best practices

This guide covers context for drivers, workers, and curriculum calls. It explains
how to keep the next action grounded without loading unrelated material. The
[task-scoped reading selector](../../agents_extensions/shared/rules/task-scoped-reading.md)
decides which canonical instructions apply. Smaller context never reduces the
operator contract, safety requirements, or delivery gates.

## Driver context

### Start with a bounded orientation packet

Use the task-prescribed project interpreter with
`-m scripts.driver_state packet --epic <lane>` and `--recipient` for the assigned Fleet recipient's unconsumed order IDs. The
[packet CLI](../../scripts/driver_state.py) calls `render_packet` in
[orientation_packet.py](../../scripts/orientation_packet.py). The packet contains
goals, next steps, holds, stops, order IDs, session metadata, source locators, and
freshness. It is an orientation view, not a replacement for its canonical sources.

`PACKET_MAX_BYTES` bounds the serialized JSON, including metadata and omission
notes, to 16,384 UTF-8 bytes. Oversized content is shortened or omitted with
`complete: false` and retrieval locators. Open PRs and live workers appear as
source locators with unknown freshness rather than fabricated live results. See
`build_packet`, `_fit`, and `render_packet` in
[orientation_packet.py](../../scripts/orientation_packet.py).

The separate [cold-start board](../../scripts/fleet_comms/cold_start_board.py)
uses `MAX_BOARD_BYTES` and `build_cold_start_board` to bound its serialized JSON
to 16 KiB. It caps strings and lists and marks truncation. These are limits on
specific outputs, not a universal context or token cap. Neither a bounded board
nor a complete packet proves that every dependency is healthy.

### Retrieve what the next action needs

Read the handoff and relevant driver state, then select the sources for the
current phase. Follow the driver, routing, intake, review, and rollover rows in
the [reading selector](../../agents_extensions/shared/rules/task-scoped-reading.md)
as those phases apply. Do not recursively load every linked rule, historical
handoff, worker report, or dependency merely because a locator exists. The
[Sol driver row](../../agents_extensions/shared/skills/drive-epic/references/model-deltas.md)
requires task-specific reads, bounded command output, and state files within
10 KB. For an existing larger state file, use bounded excerpts.

Retrieve omitted material needed for the next decision from its source. An
incomplete packet is not evidence that an order, hold, or stop is absent. Check
live worker, PR, CI, and queue state through their authoritative interfaces before
making consequential decisions, as required by
[core reporting rules](../../agents_extensions/shared/rules/core.md#p0--tool-backed-claims-honest-reporting).
The [Entire intake skill](../../agents_extensions/shared/skills/entire-context/SKILL.md)
provides bounded body-free locators. They supplement canonical evidence and do
not replace authority or formal review.

Routing context also stays current. Use the live catalog and qualified capacity,
following [core routing rules](../../agents_extensions/shared/rules/core.md#p2--which-model-for-what)
and the applicable roles in the
[agent activity matrix](agent-activity-matrix.md#2-agent-roster).
Do not copy a historical model roster or health snapshot into each packet.

### Recover with a full bounded snapshot

The following is the approved recovery contract documented by
[issue #10932](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/10932).
It extends the [continuity requirements](../../agents_extensions/shared/rules/core.md#p7--continuity)
and [rollover procedures](../../agents_extensions/shared/skills/thread-rollover/SKILL.md).
It is a target contract, not a claim that every harness implements it:

- Load a full bounded snapshot on startup, after compaction, after a provider
  change, or whenever the baseline is unknown. Full means the required context
  for the role and current phase, with retrieval locators for bounded detail.
- Use a delta only against a confirmed session revision and only where injected
  context persistence has been proven for that harness. A disk cache or an
  unchanged-source response alone does not prove that the model retains context.
- If an injector is transient, retain necessary per-call information. Never
  suppress required instructions because an earlier call received them.
- If the revision or persistence evidence is missing, return to the full bounded
  snapshot. Do not infer continuity from a provider label or a prior success.

The [packet implementation](../../scripts/orientation_packet.py) exposes a session
hash and freshness, but those fields alone do not confirm the consuming session's
revision or prove injection persistence. The
[current driver-state CLI](../../scripts/driver_state.py) provides the packet
reader. A validated-update interface remains an approved target here, not a
verified implemented command. This documentation does not add that interface.

Recovery must also re-verify lease authority and hydration. The launcher owns the
lease. Agents never open, resume, claim, renew, release, or replace the lease.
Unknown authority or hydration stops consequential action under the
[core unconditional invariants](../../agents_extensions/shared/rules/core.md#unconditional-invariants).

## Worker context

Give a worker one complete shippable unit with acceptance criteria, owned paths,
out-of-scope boundaries, verification commands, stop conditions, and evidence to
return. Include the canonical excerpts and locators needed for that unit rather
than the driver's entire history. The
[dispatch brief contract](../../agents_extensions/shared/rules/workflow.md#dispatch-brief-unit-binding--5737)
and [worker role](../../agents_extensions/shared/rules/core.md#p1--how-we-work)
define that boundary. The driver retains scope, sequencing, routing, review
judgment, landing, and closeout. Workers do not invent PR sequences, merge,
enqueue, arm auto-merge, or delegate without authorization.

A scoped prompt retains the operator contract and all applicable safety and
delivery gates. Load the [core](../../agents_extensions/shared/rules/core.md),
the [operator contract](../../agents_extensions/shared/rules/operator-expectations.md),
and the task's rows in the
[reading selector](../../agents_extensions/shared/rules/task-scoped-reading.md).
This includes worktree and owned-path discipline, the prescribed interpreter,
secret and private-data protection, honest reporting, and required verification.
Context size never licenses omitting these obligations.

For a change task, the worker's deliverable is a pushed branch with verification
and an honest report of unresolved gaps. It is not full task completion. The
[merge and cleanup recipe](../../agents_extensions/shared/rules/workflow.md#merge-policy--ready-prs-must-not-sit-4703-landing-order-7450)
requires independent exact-head cross-family approval before any PR, same-head
green CI before enqueue, confirmed merge, and common-reaper cleanup. A changed
head voids approval and CI. The accountable driver owns those steps and the
[acceptance and completion evidence](../../agents_extensions/shared/rules/core.md#p3--definition-of-ready-and-definition-of-done).
Author checks are ordinary verification, not independent held-out proof.

## Measurement and budgets

The [cold-start measurement tool](../../scripts/ai_agent_bridge/measure_cold_start.py)
and [transcript token parser](../../scripts/api/telemetry/transcript_tokens.py)
measure different things. Keep the following quantities separate. The
[context-cost baseline definitions](../runbooks/context-cost-baseline.md#frozen-definitions),
including their superseding amendments, govern stored-session accounting.

| Quantity | Meaning and evidence |
| --- | --- |
| UTF-8 bytes | Serialized payload or stored-record length on an explicitly named basis. Packet and board byte limits do not establish token counts. |
| Input tokens and current context occupancy | Tokens presented to a particular model call. Record the model, harness, counting method, and observation boundary. A source estimate is not observed occupancy. |
| Cache contributions | Preserve uncached input, cache creation, and cache read categories under the provider's semantics. Cached input can still contribute to context occupancy. |
| Cumulative usage | Usage across distinct calls, with categories kept separate and duplicate records handled. It is not the current context size. |
| Peak occupancy | The largest observed per-call context occupancy over a stated interval. Neither cumulative usage nor a first-turn sample establishes the session peak. |

For Claude transcript usage, `usage_input_tokens` in the
[token parser](../../scripts/api/telemetry/transcript_tokens.py) sums input,
cache-read input, and cache-creation input for the latest main `message` iteration
when one exists in `iterations`. Otherwise it uses the top-level usage sum.
The main-iteration selection excludes advisor-only passes from that context total.
`parse_transcript_tokens` returns the latest and previous usable observations,
not a cumulative total or a session peak. Do not generalize that provider-specific
calculation to every harness.

`measure_cold_start` reports source bytes, token-count methods, estimated input,
and an optional observed first-turn input/cache count. Its gate uses the larger
of the source estimate and the supplied observation against the selected trusted
profile's budget. Without an observation it describes repository-controlled
startup sources, not end-to-end observed context. See `count_payload_tokens`,
`observe_first_turn`, and `measure` in the
[measurement implementation](../../scripts/ai_agent_bridge/measure_cold_start.py).

Missing telemetry stays unknown, never zero or a passing result, under
[core reporting rules](../../agents_extensions/shared/rules/core.md#p0--tool-backed-claims-honest-reporting).
Use only the session's documented identity and transcript under the
[lease and identity invariants](../../agents_extensions/shared/rules/core.md#unconditional-invariants).
Report coverage and unknown reasons when aggregating, following the
[baseline amendments](../runbooks/context-cost-baseline.md#amendment-1).

Budget targets are targets. They do not prove feasibility, savings, or task
success. Resolve capacity for the actual model and runtime as described in the
[context budget audit](../../agents_extensions/shared/skills/context-budget-audit/SKILL.md#4-context-window-headroom).
Context cost and occupancy can constrain work. Quality also depends on relevant
sources and preserved directives. Do not infer output allowance by subtracting
input from an advertised window, or reuse the former illustrative per-call token
breakdown as a current measurement.

## Curriculum context

The guidance below applies to curriculum calls, especially the Gemini phase
workflow. It does not define driver or worker startup requirements. For prompt
instructions, see [prompt engineering](prompt-engineering.md). Use the active
plan and phase contract when a different build workflow applies.

### Context hierarchy

For a module build, prioritize:

1. The plan file, which defines sections, vocabulary, and objectives.
2. The research file, which supplies facts, quotations, sources, and engagement hooks.
3. The meta file, which supplies section allocations and writing points.
4. The quick reference, which supplies level constraints, immersion, activity types, and vocabulary limits.
5. Track context for consistency across sequential core modules. Omit it for independent seminar topics.

The [seminar phase template](../../agents_extensions/shared/phases/gemini/phase-A-seminar.md)
and [meta-only template](../../agents_extensions/shared/phases/gemini/phase-A-meta-only.md)
show the plan and research inputs. An old meta outline is reference material,
not authority over the plan.

### Research files

Include research for seminar tracks such as hist, bio, istorio, lit, oes, and
ruth. Core tracks may need it for the topic. Useful research contains a dated
timeline where relevant, primary-source quotations, section-mapped notes,
engagement hooks, decolonization framing, and a contested-terms table when needed.

The earlier workflow used 500 words as a research usability threshold. Treat
that as a curriculum workflow heuristic, not proof of factual adequacy. Check
source coverage and the applicable phase contract. When existing research is
adequate, the [meta-only template](../../agents_extensions/shared/phases/gemini/phase-A-meta-only.md)
rebuilds the outline from it without another research phase.

### Meta outlines and section allocation

The meta's `content_outline` gives each section a word allocation and writing
points. Both the [seminar template's meta-outline rules](../../agents_extensions/shared/phases/gemini/phase-A-seminar.md#rules-for-meta-outline)
and the [meta-only template's rules](../../agents_extensions/shared/phases/gemini/phase-A-meta-only.md#rules)
require no section to exceed 25% of the word target and a minimum allocation of
200 words. For targets of at least 4000 words, both say to aim for 8-12 sections minimum.
These are phase-template requirements, not a claim that every current builder
automatically detects violations or reruns research.

Split plan sections with five or more topic bullets into smaller sections as the
template directs. Do not turn many independent topics into one oversized section.
Retain the plan's section identity when adding subtitles.

### Track context

The current [Core vs Seminar contract](track-architecture.md#core-vs-seminar-key-differences)
requires the last five modules as track context for core tracks and omits track
context entirely for seminar tracks. This is a curriculum retrieval scope, not a
universal driver or worker scope or token cap. Avoid unrelated modules that can
contaminate examples or distract from the current plan.

### Placeholders and ordering

Use the phase workflow's placeholders rather than hardcoded module paths or
word targets. The
[seminar template](../../agents_extensions/shared/phases/gemini/phase-A-seminar.md)
uses `{PLAN_PATH}` and `{WORD_TARGET}`, and the
[meta-only template](../../agents_extensions/shared/phases/gemini/phase-A-meta-only.md)
also uses `{RESEARCH_PATH}`. Resolve their values from the active module and
workflow. A sample word target is not an instruction for every level.

Present the plan before research and the old meta. Keep level constraints
explicit. This order makes the source of truth clear without claiming a universal
model preference for earlier tokens. Do not use Russian-language sources as
normative context. Follow the
[Ukrainian source rules](../../agents_extensions/shared/rules/core.md#p5--ukrainian-source-of-truth)
and preserve the level's immersion requirements in
[core mission rules](../../agents_extensions/shared/rules/core.md#p9--mission-and-stance).

### Failure patterns

| Failure | Context check |
| --- | --- |
| The model copies old meta | Put the plan first and label old meta as reference material. |
| A section is thin despite extensive research | Check section allocation and topic splitting against the active template. |
| Facts lack support | Supply verified research and source locators. |
| Section names diverge | Include the current plan and its section names. |
| Core modules use inconsistent vocabulary | Retrieve relevant prior vocabulary and grammar context. |
