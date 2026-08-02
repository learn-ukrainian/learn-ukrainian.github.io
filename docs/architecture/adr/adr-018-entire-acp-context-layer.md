# ADR-018: Entire is an optional context index, not a control plane

**Status**: Accepted
**Date**: 2026-08-01
**Deciders**: Operator; Sol (`gpt-5.6-sol`)
**Advisors**: Kimi K3; GLM-5.2; Codex Terra repository analyst
**Related**: [#4707](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4707),
[#5880](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5880),
[#6162](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6162),
[#6183](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6183),
[#6278](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6278),
[architecture research and advisor receipt](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6162#issuecomment-5150430545),
[rollout plan](../../plans/2026-08-01-entire-acp-context-layer-rollout.md)

## Context

The private Entire pilot proved that stable CLI 0.8.42 can capture a Codex
session, explain its checkpoint, recover a missed attachment idempotently, and
route checkpoint data to the approved private repository without creating
public product refs. That is useful recovery evidence, but recovery alone does
not justify onboarding another system.

Entire's documented product model is broader: agents can search prior work,
explain why code exists, investigate changes, hand sessions to another agent,
review with checkpoint context, and turn repeated work into reusable skills.
The project already has authoritative systems for work and continuity:
GitHub, Fleet Comms, Monitor, fenced session streams, rollover receipts, and
formal cross-family review. ACP adds a bounded discussion transport with
durable, body-free receipts. Making Entire authoritative would duplicate those
systems and enlarge the failure and privacy domains.

The privacy boundary is strict. Checkpoint storage may use only
`learn-ukrainian/entire-checkpoints-private`. Public Entire shadow refs,
transcript or prompt bodies, and AI-generated summaries are forbidden. Entire
documents redaction as best-effort and states that local shadow refs can contain
raw working-tree snapshots. The public checkout's `origin` is the public
product repository, so an explicit private-destination guard is a prerequisite,
not a follow-up.

## Decision

Entire 0.8.42 is an optional, read-only context and provenance index. It never
owns task state, coordination, leases, recovery, review eligibility, or source
content. An LLM may use an Entire search result only as a locator; before any
context is injected, the locator is resolved against the authoritative local
system and its digest is verified.

The automatic fleet workflow remains stricter than the optional product
experience described in Entire's documentation. It uses the repository's
local, body-free projection for shared capsules. Under the operator amendment
below, the accountable root may also use Entire's private native search and
session tools after proving the private boundary; those bodies and generated
findings do not enter shared automatic capsules or become fleet evidence.

### Operator amendment: private native recall (2026-08-02)

The operator authorizes body-bearing Entire retrieval because checkpoint
storage is separated from the public product origin. Native recall is allowed
only after a live preflight proves all of these facts:

- CLI remains pinned to 0.8.42 and Entire authentication is valid;
- `learn-ukrainian/entire-checkpoints-private` is private and contains the
  canonical checkpoint ref;
- the public product origin contains zero `entire/*` branches;
- the checkpoint mirror and public-upstream source mirror are ready and their
  Entire ACLs contain only the operator.

The source code remains public on GitHub by product choice. That does not make
its Entire mirror public to other Entire users: the preflight checks the live
Entire control-plane collaborator list and fails unless only the operator can
pull either mirror.

After that receipt, the accountable root may use bounded repository-scoped
search, explain, recap, local dispatch, and explicit handoff for real session
continuity. Full explain stays within the root's private working context;
raw-transcript flags remain prohibited. Generated summaries and worktree-
mutating resume/rewind remain operator-directed. Native Entire remains optional
and non-authoritative.

### Authority boundary

| Concern | Authority | Entire's permitted role |
| --- | --- | --- |
| Issue, PR, commit, and merge state | GitHub and Git | Locate a checkpoint or commit; never change disposition. |
| Agent messages and ACP lifecycle | Fleet Comms and ACP receipts | Locate a terminal receipt through an opaque identifier. |
| Runtime and build state | Monitor | Locate a run; never infer live state from an old checkpoint. |
| Stream ownership and fencing | Session streams | Record a non-secret locator; never grant, renew, close, or reroute a lease. |
| Cross-session continuity | Rollover receipts and hydration capsules | Rank possible history; canonical receipts still perform hydration. |
| Formal review | Sealed cross-family review receipt | Supply context to a reviewer; never approve or satisfy the gate. |
| Session/checkpoint history | Host-harness session record; Git commit for code | Optionally index a private checkpoint locator; never hydrate session bodies automatically. |

### Active retrieval, not passive capture

Entire does not give an LLM memory merely because hooks captured a session. The
implemented repository-owned `entire-context` workflow makes verified local
history available without automating Entire's cloud CLI:

1. The accountable root checks projection `status` and performs one bounded
   local `search` before prioritization or dispatch.
2. Resolve each selected locator through a project-owned context
   link into GitHub, Fleet/ACP, Monitor, review, or rollover evidence.
3. Verify the canonical identifier and digest. Missing or mismatched evidence
   is dropped and reported; it is never injected.
4. Build at most one capsule of no more than five cards and 8 KiB, then give
   the same capsule to the relevant participants.
5. Record which locator IDs materially informed the task so later audits can distinguish
   capture from actual use.

This path is available to any seat, including Kimi and GLM. A non-native seat
does not need an Entire plugin: its accountable harness can run the workflow
and pass the same verified capsule. Native capture and cross-agent consumption
are separate concerns.

### Context links

The integration uses one-directional, append-only context links from canonical
evidence to an Entire checkpoint. Entire never writes back to a canonical
system.

Each link has these fields:

| Field | Rule |
| --- | --- |
| `schema_version` | Versioned contract; readers support current and previous. |
| `locator_id` | Digest of the kind, canonical namespace, canonical ID, and canonical digest. |
| `kind` | Allowlisted receipt type such as `git_commit`, `github_issue`, `acp_conversation`, `formal_review`, or `rollover`. |
| `canonical_namespace` / `canonical_id` | Exact, never inferred join target. |
| `canonical_digest` | Digest verified before hydration. |
| `entire_checkpoint_id` | Opaque Entire ID when one exists; absence is valid. |
| `git_sha` | Exact commit when the relationship is commit-backed. |
| `facets` | Mechanically copied, allowlisted fields only. |
| `ingested_at` | Projection time, never treated as source event time. |

The first implementation stores these relationships in an existing
authoritative receipt path or a rebuildable local projection after a separate
schema review. It does not invent synthetic Entire sessions. Arbitrary
metadata-card ingestion into Entire itself is optional and may be added only if
a 0.8.42 canary proves a supported body-free path. If native session capture
necessarily stores forbidden transcript or prompt bodies, hooks remain disabled
and the phase is recorded as blocked by the pinned product capability.

### Searchable corpus

The automatic corpus is body-free and mechanically extracted:

- opaque IDs, timestamps, source kind, canonical namespace and identifier,
  canonical digest, repository, commit SHA, actor/model/harness, state, and
  touched paths where the typed resolver admits them; and
- allowlisted non-body routing metadata from verified ACP, rollover, GitHub,
  formal-review, Fleet-receipt, and Monitor-run sources.

The bridge does not compose intent, outcome, rationale, titles, headings, or
summaries. Prompts, transcripts, responses, session bodies, ACP subjects, and
generated recaps remain outside the shared automatic context. The accountable
root may inspect richer private session memory after the live preflight, but it
must re-ground consequential facts in canonical repository evidence before
publishing or distributing them.

### Failure and privacy rules

- CLI absence, version mismatch, authentication failure, timeout, or Entire
  outage cannot block or mutate the calling workflow.
- Any pending outbox entry is an unconfirmed claim. Reconciliation is its only
  reader; hydration never reads it. Duplicate promotion is a no-op, and stale
  claims are tombstoned with evidence.
- The approved private checkpoint repository is hard-coded and verified before
  every push-capable operation. The public `origin` is always rejected as a
  checkpoint destination.
- `checkpoint explain --full` requires a green private preflight and a task
  that needs exact continuity; its output stays in the accountable root's
  private working context. `--raw-transcript` and `--transcript` remain
  prohibited.
- Logged-in semantic search and metadata-only explain may be used by the root
  after preflight. Generated recap/dispatch and worktree-mutating session
  operations require an explicit operator request. None of their output enters
  the shared automatic capsule by default.
- Entire's own review or investigate workflows may assist discussion, but they
  never satisfy the repository formal-review gate.

### ACP plugin boundary

An Entire external-agent plugin for ACP is deferred. The plugin protocol is a
reasonable future lifecycle adapter, but the existing ACP receipts already
provide the metadata required for context links. A plugin becomes worthwhile
only if a proven need requires native, in-turn capture that post-hoc receipts
cannot supply. Reconsideration requires sustained green privacy, outage,
idempotency, and retrieval-utility canaries; it is not blocked merely because a
plugin could technically be written.

## Alternatives considered

- **Entire as the session-memory and hydration authority**: rejected because
  it duplicates rollover and stream authority, makes an optional vendor tool
  load-bearing, and encourages body export.
- **Recovery-only onboarding**: rejected because it leaves search, provenance,
  handoff, active recall, analytics, and reusable workflow memory unused.
- **Metadata-only cards with no canonical-derived headings**: rejected because
  purely structural cards provide faceted lookup, not useful semantic recall.
- **Full ACP external-agent plugin now**: rejected because it adds hook-time
  coupling before the safer receipt-based join has proved value and privacy.
- **Synthetic transcripts as metadata envelopes**: rejected because they
  violate the no-transcript/no-summary boundary and rely on an undocumented
  use of the Entire session model.

## Consequences

**Positive**:

- LLMs gain an explicit, auditable recall path instead of relying on passive
  checkpoint capture.
- Kimi, GLM, and other non-native seats can consume the same verified context
  as native Codex or Claude seats.
- Entire adds ranked cross-system discovery without becoming another source of
  truth.
- Every context byte injected into an agent still comes from a canonical local
  system and carries a verifiable locator.

**Negative / risks**:

- Metadata-only search has intentionally narrower semantic value than indexing
  transcripts; the no-body policy is a real product limitation.
- Search that requires Entire login introduces a cloud-egress decision and may
  remain disabled.
- Context-link reconciliation and digest verification add a new projection to
  operate and test.
- The feature is useful only where the agent or its accountable harness can
  reach the canonical evidence needed for re-grounding.

**Neutral / follow-ups**:

- The rollout plan defines capability canaries, the headers-only corpus,
  utility measurements, and kill criteria.
- The production gate in #5880 remains independent and closed until its full
  atomic/fenced/idempotent closure, traps, successor recovery, and TTL reroute
  contract is proved.
- CLI upgrades require a new compatibility review; this decision does not
  authorize moving beyond 0.8.42.

### Implemented slice (2026-08-02)

The current repository implements the local, non-authoritative slice rather
than the original cloud-search sketch:

| Evidence | Current disposition |
| --- | --- |
| `scripts/entire_context/` | Local projection, typed verification, bounded search/explain/handoff, use receipts, and explicit sanitized provider-status refresh. |
| `scripts/api/entire_context_router.py` | Read-only Monitor status and search at `/api/ops/entire-context/status` and `/api/ops/entire-context/search`; no synchronous Entire call. |
| `tests/test_entire_context.py`, `tests/test_entire_context_recall.py`, `tests/test_entire_context_live.py` | Schema/lifecycle, fail-closed resolution, body-leakage, recall-budget, provider-cache, and live-router coverage. |
| `tests/test_entire_native_onboarding.py` | Composed fail-open capture hooks for the host harnesses `codex`, `claude-code`, and `opencode`, with private routing checks. |
| `scripts/entire/external_agents/entire-agent-kimi/` | Explicit standalone Kimi Code adapter; hosted Kimi/GLM continue to use their host integration. |

Private repository routing, public-ref absence, authenticated access, ready
mirrors, and full checkpoint readability are now proved by the #6278 preflight
and source-blind canary. Cloud result quality, generated-summary accuracy,
arbitrary metadata-card ingestion, and a need for an ACP plugin are distinct
questions; they do not change the authority table.

## Verification

The decision is successful only if staged canaries prove all of the following:

- every push-capable Entire operation targets the approved private repository;
- product repositories retain zero public Entire shadow refs;
- checkpoint samples contain zero forbidden bodies, prompts, summaries, or
  secrets;
- duplicate and retry paths create one context link;
- an Entire outage leaves canonical workflow outputs byte-for-byte unchanged;
- every hydrated item resolves and matches its canonical digest;
- Kimi/GLM and a native seat receive equivalent top results for the same query;
- a judged query set demonstrates that recall is materially better than the
  existing per-system lookups.

Any private-destination or body-leak failure disables the integration and
returns the project to the proven recovery-only posture.
