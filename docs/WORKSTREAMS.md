# Workstreams — V7 Pipeline Era

> **Living document.** The *framework* (streams, pillars, operating rhythm) is stable;
> the *contents* (each stream's current milestone row) refresh whenever a milestone
> lands or the epic board moves. **Rot must be visible, never hidden: a row that no
> longer reflects reality is marked `STALE`, a stream with no set milestone is marked
> `VACANT` — rows are corrected or marked, not deleted.** The GitHub stream epic is the
> real-time source of truth; this page is the once-per-session orientation layer.

| Field | Value |
| --- | --- |
| **Last refreshed** | 2026-08-03 (Foundry engine complete; evidence-bearing prepared-data program active under #6321; training remains prohibited) |
| **Refresh trigger** | Every session handoff that lands a milestone; every stream-epic board change |
| **Curriculum KPI** | Modules passing audit per week (curriculum streams; each milestone carries its own outcome measure) |
| **Mission** | Help people and AI produce measurably better, authentically Ukrainian language through decolonized learning products and reusable, evidence-backed open-model infrastructure. Quality non-negotiable. |
| **Pipeline** | V7 (`scripts/build/v7_build.py` → `linear_pipeline.py`). V5/V6 obsolete, do not extend. |

---

## The goal chain (read top-down before picking work)

The product users are learners and teachers. Ukrainian NLP researchers and
open-weight model teams are the beneficiaries of our public infrastructure. Every
stream must trace to this chain:

1. **Ultimate outcome**: people and AI produce measurably better, authentically
   Ukrainian language without erasing legitimate historical, regional, dialectal,
   or register variation.
2. **Products**: the LU curriculum site (learners) and Hramatka (teachers).
3. **Reusable community infrastructure**: audited, provenance-rich source data;
   the Ukrainian Data Foundry engine, contextual language-contact diagnostics,
   protected/unresolved evidence, and consumer-runnable recipes (completed
   #6164 and #6056), plus evidence-bearing prepared data products under active
   successor #6321; and
   narrow, contamination-resistant public evaluation (closed #2156; frozen
   future design preserved in closed #6057).
4. **Kept honest by**: internal QG machinery (#4913), frozen evidence grades and
   claim boundaries, independent evaluation, optional Ukrainian linguistic
   review, and strict separation of public evaluation gold, private product
   evidence, and future training data.
5. **Which runs on**: the fleet — build pipeline, dispatch, comms, leases, and CI.

**The trace is falsifiable, not vibes:** every queued item names its stream milestone,
the specific done-condition it advances, and the learner/teacher or open-weight
research outcome that condition protects. "Improves the fleet" alone is not a trace.
Exceptions require an owning issue, a reason, and an expiry; an exception living past
one session forces a milestone re-baseline. Pre-approved exception classes (no logging
hesitation): emergency CI/main breakage; green out-of-lane PRs abandoned >1h per
`AGENTS.md`; operator direct orders.

---

## Streams = GitHub Epics (#4708 — supersedes hand-maintained tier rows for scheduling)

Scheduling lives in GitHub stream epics; this doc keeps the framework, the pillars, and
one **current milestone** per stream. The registry `scripts/config/issue_streams.yaml`
is the single source of truth for membership (auditor:
`scripts/orchestration/issue_stream_audit.py`; live view: `GET /api/issues/streams`).

| Stream | Epic(s) | Scope |
| --- | --- | --- |
| atlas-practice | #4387, #4700, #5331 | Word Atlas + Practice Hub product & UX |
| atlas-intake | #4220, #4378, #5224 | Full-corpus intake into the Atlas |
| corpus-channels | #4706 | Acquisition & ingestion (textbooks · ZNO · Ohoiko-media · press · academic) |
| infra-harness | #4707 | Infra & fleet reliability (hooks, dispatch, routing) |
| devops | #5703 | DevOps automation, CI, release & launcher reliability |
| eval-harness | #4913 | Internal QG schemas, validators, quality gates, product adapters, and private calibration |
| open-model-data | #6321 (successor to closed #6164 and #6056) | Build evidence-bearing prepared Ukrainian data products on the completed Foundry engine. Community usefulness is primary; adoption is secondary evidence, not a gate. Every shipped artifact names a concrete consumer decision/use case. Current truth: #6375 is the active Phase 3 v2.1 functional-role and runtime rebinding task; #6333 is historical `ENGINE_READY` evidence only and establishes no linguistic, source, consumer, or completion status; Phase 4 remains blocked. |
| core-quality | #4274 | Deterministic track audits + remediation (A1–B2) |
| seminars-folk | #2836 | FOLK re-research + rebuild |
| seminars-bio | #4431, #4215 | BIO readiness + builds |
| seminars-cross | #3120, #3079 | Cross-seminar gates |
| hramatka | #4542 | Teacher lesson service, production-path qualification, and teacher-ready release |

Rules for every orchestrator (Claude, Codex UI, agy, cursor): work from your stream epic;
link new issues to a stream at creation; orphans get flagged at every cold start.

The completed public benchmark v0.1.1 is owned by closed #2156. Closed #6057
preserves its frozen v0.2 successor design, but reviewer-intensive #6084 is
parked under the solo-operator model. Because that program has no open epic or
active issue, it is not an active registry stream.

---

## Stream milestones (the focus layer)

**Each ACTIVE stream has exactly one outcome milestone. Multiple tasks may contribute,
but each must advance the same done-condition. A milestone does not activate a stream —
activation (`ACTIVE | PAUSED | BLOCKED`) is operator-owned and sized from live
capacity.** The stream's canonical lease holder is the sole editor of its row; edits
ride the driver's normal PRs (never a standalone doc-race — the epic stays the
real-time truth between refreshes). Cross-stream dependencies name ONE owning stream.
Rows below marked *(proposed)* were drafted by the infra driver on 2026-07-27 from
epic-board state and bind only once that stream's driver (State: the operator) confirms.

| Stream | State | Current milestone | Done when |
| --- | --- | --- | --- |
| infra-harness | ACTIVE *(proposed)* | Weak-driver rails T1 (T1.1 slot addressing ✅ #5878; T1.2 lease lifecycle; T1.3 glm canary lane) | T1.2 + T1.3 merged with mutation-checked tests. (The fleet-comms decision packet — dual-write parity + authority-signal evidence for any future plane change, file handoff never dropped unilaterally per `fleet-comms-coordination.md` — is the NEXT milestone, not this one.) |
| eval-harness | *(operator to set)* | Internal product-quality machinery under #4913 *(driver to confirm)* | Current internal milestone is confirmed on #4913 without absorbing public gold or release work |
| open-model-data | ACTIVE | Execute #6375 under combined v2.1 contract `2f3ef840…a907`: migrate task-scoped role, held-out, disposition, textbook, Pravopys, lexical, packet, scorer, and reproduction runtimes; retain #6333 only as historical `ENGINE_READY` provenance. | The v2.1 role graph and every runtime gate are merged and hash-bound; all pre-v2 semantic/source/consumer/completion claims remain invalidated; the four Phase 3 statuses pass on merged-main evidence; Phase 4 remains blocked. |
| atlas-practice | ACTIVE *(proposed)* | Practice Hub deck experience stable after the D10 wave (#5877–#5883) *(driver to confirm)* | A bounded soak: 7 days with no new daily-deck defect filed; then next #4700 item |
| atlas-intake | ACTIVE *(proposed)* | 20k enrichment run with durable storage (#5884) *(driver to confirm)* | Enriched dataset persisted off-repo with a tracked pointer; refetch never needed |
| corpus-channels | *(operator to set)* | *(VACANT — driver to set from #4706; the slot-addressing work formerly listed here is infra-harness scope)* | — |
| devops | *(operator to set)* | Post-#5703 launcher/lease separation soak *(driver to confirm)* | 7 consecutive days, ≥10 real session launches observed in lease telemetry, zero cross-stream lease collisions — zero-traffic days do not count |
| core-quality | *(operator to set)* | *(VACANT — driver to set from #4274)* | — |
| seminars-folk | *(operator to set)* | *(VACANT — driver to set from #2836)* | — |
| seminars-bio | *(operator to set)* | *(VACANT — driver to set from #4431)* | — |
| seminars-cross | *(operator to set)* | *(VACANT — driver to set from #3120/#3079)* | — |
| hramatka | ACTIVE *(proposed)* | Lesson QUALITY floor (gate calibration #5254) *(driver to confirm — exact threshold, sample size, and run id belong on #5254)* | A soak run identified by run-id whose ready-lesson rate meets the #5254 bar at its declared sample size |

Row states: a row contradicted by its epic board is edited or marked `STALE` by the
next driver who notices — never silently deleted; `VACANT` means the stream has no set
milestone and is itself a visible signal. The cold-start auditor SHOULD warn on STALE /
VACANT rows and on milestones whose named issues are closed (tooling follow-up tracked
on the infra board).

---

## Three Quality Pillars

Every shipped module must pass all three:

| Pillar | What | How |
| --- | --- | --- |
| **Structural** | Word count, activities, vocab, formatting, MDX render | Deterministic audit gates (`scripts/audit_module.py`, `python_qg.json`, `wiki_coverage_gate.py`) |
| **Linguistic** | VESUM-verified words, Russianisms/Surzhyk/calques/paronyms clean, citations resolve | MCP `sources` server (`mcp__sources__*` / `mcp_sources_*`) — verify_words, check_russian_shadow, verify_source_attribution, search_style_guide |
| **Pedagogical** | Tone, immersion balance, register, decolonization, sequence | Cross-agent reviewer per the live routing rule (`model-assignment.md` served at `/api/rules`) |

The reviewer-as-fixer rule (ADR-007): reviewer emits `<fixes>` find/replace pairs; pipeline applies deterministically. No LLM regeneration during review. Self-review forbidden (`SELF_REVIEW_DETECTED` gate enforces).

---

## Operating rhythm (the anti-drift ritual)

Per session, every driver:

1. **Cold-start**: orient (Monitor API + handoff), then read YOUR stream's milestone row
   and epic board. The session queue must trace to the milestone per the falsifiable
   goal-trace rule above; non-tracing work is an exception with an owning issue, reason,
   and expiry, logged in the handoff.
2. **Dispatch**: every brief names its stream (the research-registry classification
   already forces this); width per CodexBar pace/reserve + disk headroom, never fixed
   caps.
3. **Merge gate — mechanical, not vibes**: auto-merge is armed only when EVERY
   explicitly requested review of the CURRENT head is terminal and published. A review
   in `sent` / `processing` / timed-out / failed state is unresolved until it returns or
   is explicitly cancelled with a recorded reason; a new head invalidates prior
   verdicts. (2026-07-27 lesson: auto-merge raced a still-running formal CF; the
   finding was real and cost a follow-up PR. The enforcement home for this rule is the
   task-lifecycle / decision-tables layer — this page only states it.)
4. **Session close**: if your milestone moved, the row update rides your normal PR or
   handoff commit — the epic remains the real-time truth between page refreshes.
5. **Inventory hygiene** (weekly or on operator ping): run the stream auditor —
   orphans to zero; issues stale >14 days triaged (close the dead, link the live).

---

## Change control

Framework changes (streams added/removed, ritual changes, pillar changes, stream State
changes) need operator or advisor sign-off. Milestone-row content is each stream
driver's to maintain — that is the point of the layer.
