# DECISION REQUIRED - Multi-UI content-producing participants in `ab discuss` / channels.html

**Status:** PROPOSED (awaiting Gemini cross-review and user signoff)
**Surfaced:** 2026-05-06 morning, while running the writer-lock 3-way discussion
**Source:** GH issue #1731 Part B; revised after Codex REJECT review on PR #1732
**Scope:** Agent bridge channel participation, round claims, multimodal channel messages, and pilot bakeoff dispatch
**Predecessor ADRs:** None. This is the first ADR on multi-UI participation. It touches the `ab` channel-bridge contract from #1190.

---

## Why this needs an ADR

`ab discuss` today is a closed-loop, single-orchestrator protocol. The caller runs `ab discuss --with claude,gemini,codex`, spawns each named agent through `scripts/agent_runtime/adapters/*.py`, reads stdout, posts the result to a channel, threads replies through `parent_id`, aggregates `[AGREE]`, and returns a transcript.

That closed loop currently gives us three implicit guarantees:

- **Identity is fixed at dispatch.** The `--with` list is the participant list.
- **Time is owned by the orchestrator.** A round ends when subprocess replies return.
- **State is one transcript.** The orchestrator is the only writer of round replies.

The user's original ask was that Claude Code, Claude Desktop, Codex CLI, Codex UI, and the user can all participate. The newer, load-bearing framing is broader: "atm cli agents can use the discussion channel, but it would be nice if codex desktop and claude code desktop could also use them, they are another cli agent just ui, and i have a suspicion that better to create the lesson, to add graphical content."

This reframes the ADR from chat participation to **content-producing participants**. Desktop and web surfaces may create better lesson artifacts because they can attach files, inspect images, generate images, render Artifacts-style previews, or use browser APIs. The channel protocol must preserve which family answered, which surface answered, which instance answered, and which artifacts were produced.

Patching `ab discuss` ad hoc would silently change the contract for writer-lock discussions, channel reviews, pipeline reviews, and future bakeoffs. This ADR defines the contract before implementation.

---

## Scope

In scope: participant identity across multiple surfaces, surface capability profiles, discussion discovery, claim/lease/fallback semantics, default user-as-context behavior, explicit user quorum mode, localhost identity assumptions, loopback-binding preflight, idempotent claim retries, atomic round-message validation, dynamic join rules, monotonic event replay, fallback identity, multimodal message attachments, pilot bakeoff design, and the implementation epic split.

Out of scope: remote/cloud auth, multi-user broker federation, voice/video, global task pickup outside discussion threads, final channels.html polish, blob retention/pruning, artifact promotion into curriculum assets, and Desktop vendor preference if both Claude Desktop and Codex Desktop are available.

Implementation should not start until Gemini review and user signoff. The pilot bakeoff should run before the architecture makes Desktop mandatory for graphics-rich module work.

---

## Content-production reframe

The prior ADR treated "participant" as chat identity. The revised contract treats a participant as a possible producer of curriculum content and artifacts. A Codex CLI reply and a Codex Desktop reply may satisfy the same `codex` quorum slot, but they do not have the same production capabilities.

Task routing examples:

- Bug-fix dispatch can use CLI.
- Text-only docs or module prose can use CLI.
- A module needing a color-coded paradigm table may require Desktop.
- A module needing generated or attached images may require Desktop.
- Rendered lesson review may require Web.
- Nightly deterministic checks may require Headless.

The transcript must preserve this distinction. If Desktop was required and CLI fallback answered, the audit trail should show both the required family/surface and the actual participant. If an image was produced, the message should have a persisted attachment row, not an inline prose placeholder.

This is what lets the project later ask whether Desktop actually improved graphics-rich module quality, which artifacts were produced by which surface, and which assignments silently degraded to text-only.

---

## Capability profile per surface

`ui_surface` is a routing signal, not just display metadata.

| `ui_surface` | Input capabilities | Output capabilities | Runtime affordances | Assign these tasks |
| --- | --- | --- | --- | --- |
| `cli` | text stdin, repo files, shell tools | text, file edits, command output | deterministic subprocess, easy logs, low friction | bug fixes, code review, docs edits, text-only module drafts |
| `desktop` | text, image attach, file drop, screenshots, local context | text, file edits through tools, image generation where available, Artifacts-style render | human-in-loop, visual inspection, multimodal context | graphics-rich modules, image-backed pedagogy, paradigm-table design, register blocks with photos |
| `web` | text, browser state, iframe messages, uploaded files where enabled | rich rendering, browser DOM changes, iframe-postMessage integration | browser APIs, live preview, visual QA | channels.html participation, rendered lesson review, browser debugging |
| `headless` | scripted inputs, scheduled files, API payloads | scripted messages, reports, machine-readable logs | no human-in-loop, repeatable automation | nightly checks, status summaries, deterministic validation |

Initial allowed values are `cli`, `desktop`, `web`, and `headless`. Do not add `mobile` until there is a concrete client.

Rationale:

- `claude:cli` and `claude:desktop` can both satisfy a Claude family slot.
- Only Desktop should satisfy an assignment requiring multimodal output.
- Surface routing makes the user's content-production hypothesis testable.

Tradeoffs:

- More schema and orchestration complexity.
- Some tasks need capability requirements in addition to family requirements.
- First implementation can enforce only coarse surface requirements in the claim layer.

Alternative considered:

- Keep all surfaces under flat `from_agent`. Rejected because it cannot distinguish "Claude answered" from "Claude Desktop produced an image-backed answer."

---

## Architectural questions

Each question below includes proposal, rationale, tradeoffs, and alternatives considered. Q1-Q6 preserve and revise the original ADR questions. Q7-Q12 add the missing architectural questions from Codex review and the content-production reframe.

---

## Q1. What is a participant?

### Proposal

A participant is represented by three first-class columns:

- `agent_family`
- `ui_surface`
- `instance_id`

Initial `agent_family` values are `claude`, `codex`, `gemini`, and `user`. Initial `ui_surface` values are `cli`, `desktop`, `web`, and `headless`.

`instance_id` is an ephemeral UUID for one process, browser tab, desktop session, or headless worker run.

`participant_id` may exist only as a generated display/key convenience:

```text
{agent_family}:{ui_surface}:{instance_id_short}
```

Example:

```text
codex:desktop:8f91c2
```

It must not be the only stored identity. The canonical data model is the three separate columns. If SQLite generated columns are awkward, store `participant_id` as denormalized display text while keeping the three identity columns authoritative.

The legacy `from_agent` column remains during migration. Old rows hydrate as `agent_family=from_agent`, `ui_surface=cli`, and `instance_id=legacy`.

The user is a participant with `agent_family=user`. User surface depends on entry point: channels.html is `web`, `ab post` is `cli`, and future Desktop integration is `desktop`.

### Rationale

Tuple-in-text is not first-class schema. Quorum checks need `agent_family`; capability routing needs `ui_surface`; lease renewal needs `instance_id`; UI display can use `participant_id`. Encoding everything in one string makes serious queries depend on parsing conventions and weak indexing.

### Tradeoffs

- Migration touches existing `channel_messages` queries.
- Backfill needs a legacy mapping rule.
- UI code needs to display `participant_id` while filtering by individual columns.
- More indexes are needed, likely on `(channel, thread_id, agent_family)`, `(channel, thread_id, ui_surface)`, and `(channel, thread_id, agent_family, ui_surface, instance_id)`.

### Alternatives considered

- Flat `participant_id` only. Rejected because it repeats the parsing problem.
- Distinct families such as `claude-desktop`. Rejected because Desktop and CLI should satisfy the same Claude family slot.
- Keep only `from_agent` plus `client_app`. Rejected because telemetry is not identity.
- Participant registry table only. Deferred; message rows still need denormalized identity for historical audit.

---

## Q2. How does a UI surface discover a discussion?

### Proposal

Use replayable SSE as the primary discovery channel:

```text
GET /api/comms/channels/{channel}/events?since={event_id}
```

Required semantics: every event has monotonic `event_id`; clients may pass `since`; SSE clients may reconnect with `Last-Event-ID`; server replays events where `event_id > since`; if neither `since` nor `Last-Event-ID` is provided, start at now unless explicit replay mode is requested; keepalive comments emit every 30 seconds; idle connections close server-side after a bounded timeout.

Minimum event types are `discussion_started`, `message_appended`, `claim_created`, `claim_extended`, `claim_released`, `claim_expired`, `discussion_aborted`, `attachment_added`, and `discussion_completed`.

The existing pull/inbox route remains a fallback:

```text
GET /api/comms/inbox?agent_family={family}&since={event_id}
```

MCP decision:

- Do not make `mcp__channels__subscribe` a long-running blocking tool call.
- Implement subscribe as MCP resource registration.
- Return a readable resource URI such as `channels://{channel}/events?since={event_id}`.
- Use separate MCP tools for claim, post, keepalive, release, and attach.

### Rationale

SSE is the smallest push primitive that fits server-to-client channel updates. Replay matters because Desktop, browser, and CLI clients disconnect and reconnect. `event_id`, `since`, and `Last-Event-ID` prevent clients from guessing whether they missed a claim, message, or abort. MCP resource reads fit Desktop model turns better than an indefinitely open tool call.

### Tradeoffs

- Requires an event log or derivable replay stream.
- Clients must persist last seen `event_id`.
- MCP resource reads are less real-time than a held socket, but more robust for model-driven Desktop turns.
- Replay retention and pruning remain future policy.

### Alternatives considered

- Polling only. Rejected as primary path; acceptable fallback.
- WebSocket. Rejected for first implementation because bidirectional sockets are unnecessary.
- Blocking MCP subscribe. Rejected because cancellation and model-turn semantics are unclear.
- channels.html as source of truth. Rejected; broker DB and API remain canonical.

---

## Q3. Who can claim a turn?

### Proposal

An active discussion round is claim-gated. A participant must hold a valid claim before posting a round reply.

Endpoint:

```text
POST /api/comms/channels/{channel}/threads/{thread_id}/claims
```

Request fields:

- `agent_family`
- `ui_surface`
- `instance_id`
- `round_index`
- `participant_scope`
- `idempotency_key`

Default claim scope is `participant_scope=family`. This means only one participant per `agent_family` can hold the round slot, while any surface of that family may claim it if capability requirements allow.

Reserve `participant_scope=participant` as a future escape hatch for assignments that truly require one exact `(agent_family, ui_surface, instance_id)`. Do not implement it in the first slice unless a concrete test requires it.

Claims return `claim_id`, holder identity, `round_index`, scope, lease kind, and visible `expires_at`. Conflicts return the current holder and `expires_at`.

### Rationale

Family-scoped claims preserve the current `--with claude,codex,gemini` contract while allowing Desktop tag-in. The required slot is "Codex", not "this exact Codex CLI subprocess." First-claim-wins prevents duplicate expensive replies.

### Tradeoffs

- Same-family surfaces must coordinate through the claim table.
- Capability requirements need validation in addition to family matching.
- Participant-scoped behavior is deferred.
- Claims add API and DB complexity.

### Alternatives considered

- First-message-wins, no claim. Rejected because competing agents waste tokens and produce rejected replies.
- Instance-scoped claims only. Rejected as the default because it blocks tag-in.
- Orchestrator-only posting. Rejected because Desktop/Web could not produce channel content.
- One global claim per thread. Rejected because it serializes all families.

---

## Q4. How do user posts interact with round quorum?

### Proposal

Default mode: user posts are context, do not satisfy agent-family quorum slots, `[AGREE]` from the user ends the discussion as user termination rather than agent consensus, and `[OBJECT]` clears convergence and forces another round if budget allows.

User context injection: user posts during round N are injected into round N+1 prompts, prefixed with `[USER_CONTEXT]`, capped by character budget, and visibly marked if truncated.

Explicit quorum mode: `ab discuss --with user` makes `agent_family=user` a required quorum slot. A user post can satisfy the current `user` slot, never a non-user slot, and the transcript records `quorum_role=required_participant`.

For a user post to satisfy the current user slot, the discussion must include `--with user`, the post must reference the active `thread_id`, the post must have the current `round_index`, and the user must hold or be granted the `user` claim.

### Rationale

Default behavior preserves the existing agent-deliberation contract: users steer, object, or terminate, but are not silently counted as model-family consensus. Explicit `--with user` handles real cases where user participation is required, such as sensitive framing choices, private reference input, or approval of a multimodal-to-text fallback.

### Tradeoffs

- Two user modes are more complex than one.
- UI must show whether user input is context or quorum.
- Prompt injection must avoid bloat.
- Claim validation must handle `agent_family=user`.

### Alternatives considered

- User is always context. Rejected as too rigid.
- User is always a quorum participant. Rejected because it changes existing semantics.
- User `[AGREE]` counts toward agent consensus. Rejected because consumer signoff is not cross-agent convergence.
- User posts are ignored until discussion ends. Rejected because it loses steering value.

---

## Q5. What identity and auth model is acceptable on localhost?

### Proposal

Initial implementation is localhost-only. Participants self-identify with `agent_family`, `ui_surface`, `instance_id`, and `client_app`. Examples include `codex-cli/5.x`, `codex-desktop/unknown`, `claude-code/2.x`, `claude-desktop/unknown`, `channels-html/local`, and `ab-headless/1`.

The broker does not authenticate participants in the first implementation.

Loopback binding is a pre-implementation gate. Before any multi-UI endpoint ships, tests or startup checks must verify:

- API binds to `127.0.0.1` or `::1`
- API does not bind to `0.0.0.0` by default
- docs do not instruct remote exposure
- channel URLs use relative paths or loopback localhost
- no container-only `/app/...` paths are introduced

If the server currently binds broadly, fix that before implementing the rest of this ADR.

### Rationale

The broker is a single-user local development tool. Tokens are premature for the first prototype, but unauthenticated claim/post endpoints are acceptable only if the service is truly loopback-bound. Treating loopback binding as a later fix is too risky.

### Tradeoffs

- Any local process owned by the user can impersonate an agent.
- Future remote support will need a separate auth ADR.
- The preflight may block implementation if current binding is unsafe.

### Alternatives considered

- Token auth now. Deferred until remote or multi-user support.
- No auth and no bind check. Rejected because `:8765` could be exposed accidentally.
- Browser same-origin only. Rejected because CLI and Desktop integrations are not browser-only.
- Per-agent shared secrets in repo config. Rejected for first implementation.

---

## Q6. What happens when a claim holder disappears?

### Proposal

Use stateful claims with leases, keepalives, visible expiry, manual release, and fallback.

| Holder type | Initial lease | Keepalive interval | Extension | Use case |
| --- | ---: | ---: | ---: | --- |
| automated/headless/CLI subprocess | 90 seconds | 30 seconds | now + 90 seconds | spawned agents and scripted workers |
| human/UI/Desktop/Web | 5 minutes | 30 seconds | now + 5 minutes | Desktop, browser, user-in-loop work |

Every claim response and claim event includes `expires_at`. Clients must display or log it.

Endpoints:

```text
POST /api/comms/channels/{channel}/threads/{thread_id}/claims/{claim_id}/keepalive
POST /api/comms/channels/{channel}/threads/{thread_id}/claims/{claim_id}/release
```

Expired claims emit `claim_expired`. Expired holders cannot post round replies. Another participant may claim after expiry. The orchestrator may auto-fallback if configured.

Fallback policy:

- `--auto-fallback=true` remains default for CLI-safe tasks
- multimodal-required tasks must not silently fallback to CLI
- if fallback loses a required capability, abort unless degradation was explicitly allowed

### Rationale

A flat 90-second expiry is too brittle for human/UI work. Desktop users may inspect images, drag in files, or wait for generation. Infinite waits are also unacceptable. Leases make waiting explicit, keepalives keep active claims alive, and manual release avoids waiting out accidental claims.

### Tradeoffs

- Two lease classes add policy complexity.
- Long UI leases can make a discussion feel stuck.
- Keepalives require client implementation.
- Fallback must understand capability requirements.

### Alternatives considered

- Fixed 90 seconds for all holders. Rejected because legitimate UI work expires.
- Fixed five minutes for all holders. Rejected because automated failures become slow.
- Wait forever. Rejected because it can deadlock the discussion.
- No manual release. Rejected because accidental claims become expensive.

---

## Q7. How are claim retries made idempotent?

### Proposal

Claim creation requires an `idempotency_key`. Store each request keyed by at least `(thread_id, idempotency_key)` with canonical request hash, response status, response body, claim ID, and created timestamp.

Semantics:

- same key plus same request returns the original response
- same key plus different request returns `409 idempotency_key_reuse`
- reconnects and HTTP retries reuse the same key
- clients generate a new key only for a new logical claim attempt
- retention lasts at least as long as the discussion plus event replay retention

Compatibility rule: old local CLI callers that omit `idempotency_key` may receive a server-generated key for that request, but new clients must send one.

### Rationale

Desktop and web clients reconnect. HTTP clients retry. Without idempotency, a retry can create ambiguous holder state or a misleading conflict. The broker must distinguish duplicate success, actual race, and client token reuse bug.

### Tradeoffs

- Adds a table or equivalent persisted request log.
- Clients must persist a token across reconnects.
- Server needs canonical request hashing.
- Old clients need temporary compatibility.

### Alternatives considered

- Rely on unique claim constraints only. Rejected because retries can look like conflicts.
- Use `claim_id` as idempotency key. Rejected because the client does not have it before creation.
- Ignore retries because localhost is reliable. Rejected because browser refreshes and Desktop reconnects are normal.

---

## Q8. How is posting a round reply validated atomically?

### Proposal

Posting a round reply must be a single DB transaction. The transaction validates:

- `claim_id` exists
- claim is not expired
- holder identity matches `agent_family`, `ui_surface`, and `instance_id`
- `round_index` matches the active round
- `agent_family` is required or allowed for the discussion
- `participant_scope` rules are satisfied
- parent/thread lineage is valid
- no accepted reply already satisfies the same family slot for that round
- surface capability requirements are met
- attachment references exist and belong to the message draft or upload session

Only after validation passes may the broker insert the message row, attachment rows, events, and claim-consumed/released state.

Structured errors should include `claim_missing`, `claim_expired`, `claim_holder_mismatch`, `round_mismatch`, `family_not_required`, `duplicate_round_reply`, `invalid_parent`, `capability_missing`, and `attachment_missing`.

### Rationale

Claims matter only if posting enforces them. Without atomic validation, CLI could post into a slot claimed by Desktop, or a stale UI could post round 1 after round 2 started. Parent lineage alone does not prove claim ownership.

### Tradeoffs

- Post endpoint becomes stricter.
- Older clients may fail until updated.
- Race-condition tests are required.
- Attachment upload may need draft/session state.

### Alternatives considered

- Validate in orchestrator only. Rejected because Desktop/Web can post outside that process.
- Accept all messages and filter later. Rejected because it corrupts transcript audit.
- Use `parent_id` only as guard. Rejected because it does not prove holder identity.

---

## Q9. Can participants join after `discussion_started`?

### Proposal

Dynamic join is allowed but constrained. Participant states are:

- `observer`
- `eligible_claimant`
- `quorum_member`

Default after `discussion_started`:

- a new surface for an already-required `agent_family` may become an `eligible_claimant`
- a new `agent_family` becomes `observer`
- the user becomes context participant unless `--with user` was specified

A late joiner can claim only when its family is already required, the family slot is unclaimed or expired, surface/capability requirements are satisfied, and the discussion is still active.

A late joiner cannot become a new quorum member unless a user or orchestrator explicitly amends the discussion, emits `discussion_quorum_changed`, and all existing participants see that event before the next round. Do not implement quorum expansion in the first slice.

### Rationale

The user wants Desktop tag-in by another surface of the same family. That should work. Adding a new family midstream changes consensus meaning and must be explicit.

### Tradeoffs

- Late tag-in must be visible in UI.
- Blocking new quorum members reduces flexibility but keeps consensus stable.
- Future quorum changes need another implementation slice.

### Alternatives considered

- No dynamic joins. Rejected because it blocks Desktop tag-in.
- Any late participant becomes quorum member. Rejected because it changes consensus silently.
- Late joiners can post only context. Rejected as the sole mode because it does not solve claim handoff.

---

## Q10. How are events ordered and replayed?

### Proposal

Add a monotonic channel event sequence. Every state-changing broker action writes one event row with a strictly increasing `event_id`.

Minimum event shape:

```sql
CREATE TABLE channel_events (
  event_id INTEGER PRIMARY KEY AUTOINCREMENT,
  channel TEXT NOT NULL,
  thread_id TEXT,
  event_type TEXT NOT NULL,
  message_id TEXT,
  claim_id TEXT,
  attachment_id TEXT,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

Events include `discussion_started`, `message_appended`, `claim_created`, `claim_extended`, `claim_released`, `claim_expired`, `discussion_aborted`, `attachment_added`, and `discussion_completed`.

Ordering rule: `event_id` is global across the local broker. Clients may filter by channel but retain the global ID. Replay returns `event_id > since`. Timestamps are metadata, not sequence.

### Rationale

SSE without monotonic event IDs is underspecified. Clients need to know whether a claim expired before a message, whether an abort preceded a late post, and where to resume after reconnect. SQLite autoincrement event IDs are simple and deterministic.

### Tradeoffs

- Adds an event log table.
- Every state-changing endpoint must write events.
- Tests must assert event ordering.
- Pruning policy is deferred.

### Alternatives considered

- Use `created_at` timestamps. Rejected because timestamps are not unique and can be skewed.
- Per-channel sequence numbers. Rejected for first implementation; global sequence is simpler for multi-channel clients.
- Derive events from message rows only. Rejected because claims, expiries, aborts, and attachments are not all messages.

---

## Q11. How is fallback identity recorded?

### Proposal

Transcript rows for round replies must record required identity and actual identity:

- `required_agent_family`
- `required_ui_surface` nullable
- `required_capability_profile` nullable
- `actual_agent_family`
- `actual_ui_surface`
- `actual_instance_id`
- `actual_participant_id`
- `fallback_from_participant_id` nullable
- `fallback_reason` nullable

If fallback loses a required capability, the message must not be accepted unless degradation was explicitly allowed. Allowed degradation records `capability_degraded=true`, who allowed it, and the degradation reason.

Example:

```json
{
  "required_agent_family": "codex",
  "required_ui_surface": "desktop",
  "required_capability_profile": "multimodal_output",
  "actual_agent_family": "codex",
  "actual_ui_surface": "cli",
  "actual_participant_id": "codex:cli:2c991a",
  "fallback_from_participant_id": "codex:desktop:8f91c2",
  "fallback_reason": "lease_expired"
}
```

### Rationale

If Desktop was required because the task needed graphical content, CLI fallback is not equivalent. The transcript must show that. This also supports later analysis of Desktop-created modules, CLI-created modules, fallback modules, and graphics-rich tasks degraded to text-only.

### Tradeoffs

- More message metadata.
- UI rendering must preserve audit without clutter.
- Some rows have nullable fields.
- Capability checks must exist before fallback can be safe.

### Alternatives considered

- Overwrite holder with fallback participant. Rejected because it erases fallback.
- Record fallback only as prose in message body. Rejected because it is not queryable.
- Forbid fallback always. Rejected because CLI fallback remains useful for text-only discussions.

---

## Q12. How are graphical and multimodal artifacts produced, attached, and persisted?

### Proposal

Add first-class message attachments.

```sql
CREATE TABLE message_attachments (
  attachment_id TEXT PRIMARY KEY,
  message_id TEXT NOT NULL,
  attachment_type TEXT NOT NULL,
  blob_sha256 TEXT NOT NULL,
  blob_ext TEXT NOT NULL,
  mime_type TEXT NOT NULL,
  byte_size INTEGER NOT NULL,
  alt_text TEXT,
  caption TEXT,
  source_participant_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(message_id) REFERENCES channel_messages(message_id)
);
```

Initial `attachment_type` values are `image`, `document`, `artifact`, and `data`.

Blob storage decision for localhost:

- store blobs on filesystem
- path: `.ab/channels/blobs/{sha256}.{ext}`
- keep metadata in SQLite
- verify hash before linking
- do not use S3-style storage for the local prototype

Markdown image refs in message bodies use:

```markdown
![Color-coded possessive pronoun paradigm](attachment://{attachment_id})
```

The channel renderer resolves `attachment://...` against the blob store. Export may rewrite refs to relative file paths.

MCP tool surface:

```text
mcp__channels__attach(message_id, file_path, alt_text?, caption?)
```

If atomic message plus attachment creation is needed, use a draft flow: begin message, attach to draft, then post draft. A simpler first slice may post then immediately attach, but message state must show incomplete/broken attachments visibly.

Recommended limits:

- image max size: 10 MB
- document max size: 25 MB
- max attachments per message: 10
- alt text required for images

### Rationale

The content-production hypothesis depends on graphical output. A text-only channel cannot test it. Attachments must be persisted, content-addressed, referenced from markdown, rendered in channels.html, exportable, and attributable.

Filesystem blob storage is the right localhost default because it is inspectable, cheap, and credential-free.

### Tradeoffs

- Blob cleanup becomes a maintenance concern.
- Upload needs size and type limits.
- Rendering must avoid silent broken refs.
- Alt text is extra required metadata.
- Draft flow is more robust but more work.

### Alternatives considered

- Inline base64 images in message body. Rejected because it bloats DB rows and transcripts.
- S3-style storage now. Rejected because it adds credentials and network failure modes.
- Commit generated images directly to repo paths. Rejected as the channel default; promotion can be separate.
- Text-only placeholder descriptions. Rejected because it cannot test graphical pedagogy.

---

## Empirical hypothesis: pilot bakeoff before implementation

### Hypothesis

Desktop or UI surfaces may produce better graphics-rich lesson content than CLI surfaces because they can use multimodal input/output and live rendering. This is plausible but not proven. Run a small bakeoff before making Desktop mandatory for graphics-rich routing.

### Input

Use:

```text
docs/references/private/ohoiko-june-a1-book/notes/page-068-module-24-possessive-pronouns.md
```

The file is gitignored and may not exist in all worktrees. The bakeoff runner must fail clearly if it is absent; it must not fabricate the reference.

The brief identifies seven pedagogical anchors from that note:

1. Header structure.
2. Audio scaffolding.
3. Inductive opening.
4. Concept block.
5. Color-coded paradigm.
6. Photo-anchored register block.
7. Q -> A scaffold.

### Task

Produce one A1 module on possessive pronouns matching the pedagogical layout described in the notes. Output must include module markdown, supporting visual artifacts where used, alt text for every visual artifact, and a short design note explaining how each anchor was attempted. Do not copy copyrighted source text; use the notes only as structural/pedagogical observation.

### Writers

Writer A:

- Codex CLI text-only
- no image generation
- no file attach
- no live visual artifact surface

Writer B:

- Claude Code Desktop or Codex Desktop, whichever the user can run
- multimodal input allowed
- image generation allowed where the tool surface supports it
- Artifacts/live-preview rendering allowed

If neither Desktop variant is available, the bakeoff is blocked.

### Measurement

Score seven binary anchors:

| Anchor | Present? | Evidence |
| --- | --- | --- |
| Header structure | yes/no | line refs or artifact refs |
| Audio scaffolding | yes/no | line refs |
| Inductive opening | yes/no | line refs |
| Concept block | yes/no | line refs |
| Color-coded paradigm | yes/no | line refs or attachment refs |
| Photo-anchored register block | yes/no | line refs or attachment refs |
| Q -> A scaffold | yes/no | line refs |

Evidence must cite generated output, not the private notes. Score is `anchors_present / 7`.

### Acceptance gate

Let `CLI_SCORE=N` and `DESKTOP_SCORE=D`.

Desktop locks in graphics-rich routing only if:

```text
D >= N + 2
```

Examples:

- CLI 4/7, Desktop 6/7: Desktop advantage accepted.
- CLI 5/7, Desktop 6/7: insufficient advantage.
- CLI 6/7, Desktop 7/7: insufficient advantage.
- CLI 3/7, Desktop 6/7: Desktop advantage accepted.

If Desktop does not beat CLI by at least two anchors, ship CLI-first channel participation and keep attachment support optional/deferred. If Desktop wins by at least two anchors, implement surface capability routing, include attachment handling in the first multi-UI epic, and allow module-writing dispatch to require Desktop for graphics-rich modules.

### Follow-up issue shape

```text
Title: Run possessive-pronoun multimodal bakeoff for #1731 Part B

Inputs:
- docs/references/private/ohoiko-june-a1-book/notes/page-068-module-24-possessive-pronouns.md

Writers:
- Codex CLI text-only
- Claude Code Desktop or Codex Desktop multimodal

Outputs:
- module markdown per writer
- artifact directory per writer
- checklist report with 7 binary anchors
- summary comparing CLI_SCORE and DESKTOP_SCORE

Gate:
- Desktop must score at least CLI_SCORE + 2 anchors to make Desktop-required routing mandatory for graphics-rich modules.
```

### Rationale

The architecture should follow evidence. The seven-anchor checklist turns the user's hypothesis into a dispatchable test. It is pragmatic rather than statistically complete, but strong enough to decide whether Desktop-required routing belongs in the first implementation.

### Tradeoffs

- A single bakeoff is not statistically strong.
- The private reference limits reproducibility.
- Desktop availability depends on user setup.
- Binary anchors may miss qualitative differences, so reviewers may add notes, but the gate remains binary.

### Alternatives considered

- Implement Desktop routing immediately. Rejected because it assumes the hypothesis.
- Require a large bakeoff suite first. Rejected because it is too slow for this ADR.
- Use subjective holistic review only. Rejected because it is hard to turn into an implementation gate.
- Skip image artifacts. Rejected because graphical output is the hypothesis.

---

## Implementation epic

After acceptance, split implementation into six strands. Each strand should carry focused tests; generated status, audit, and review artifacts must stay out of code PR diffs.

### Strand 1: schema and claim mechanism

Scope: add first-class participant identity columns, preserve legacy `from_agent`, add claims table, add claim-request idempotency table, add lease fields, add claim create/keepalive/release/expire paths, and add loopback preflight if missing.

Questions covered: Q1, Q3, Q5, Q6, Q7.

Test focus: legacy hydration, same-family claim conflicts, idempotent retry, key reuse failure, expired-claim rejection, keepalive extension, manual release, and loopback binding.

### Strand 2: SSE, replay semantics, and MCP shim

Scope: add `channel_events`, emit monotonic events for state changes, add replayable SSE endpoint, support `since`, support `Last-Event-ID`, keep pull endpoint as fallback, and add MCP resource registration for channel events.

Questions covered: Q2, Q10.

Test focus: monotonic event IDs, replay after `since`, `Last-Event-ID` resume, claim/message event order, and MCP readable resource URI.

### Strand 3: discuss orchestrator updates

Scope: route subprocess replies through claims, inject user context into next-round prompts, support `--with user`, handle `[AGREE]` and `[OBJECT]`, enforce fallback policy, record fallback identity, and prevent silent capability degradation.

Questions covered: Q3, Q4, Q6, Q8, Q9, Q11.

Test focus: default user context, explicit user quorum, user stop/object markers, required-vs-actual fallback recording, and multimodal-required fallback abort unless degradation is allowed.

### Strand 4: MCP tool family

Scope: add `mcp__channels__list`, `mcp__channels__observe`, `mcp__channels__claim`, `mcp__channels__keepalive`, `mcp__channels__release`, `mcp__channels__post`, and `mcp__channels__attach`.

Questions covered: Q2, Q3, Q6, Q12.

Test focus: Desktop can list, observe through resource reads, claim, post, release, attach an image with alt text, and receive rejection for missing or unsupported files.

### Strand 5: multimodal artifact handling

Scope: add `message_attachments`, add filesystem blob store, validate sha256 and MIME, support `attachment://{attachment_id}` markdown refs, render attachments in channels.html, export attachments for transcript review, and require alt text for images.

Questions covered: Q12, Q8, Q11.

Test focus: attachment-message links, blob hash verification, visibly broken missing blobs, image alt-text rejection, markdown image-ref resolution, and storage constrained under `.ab/channels/blobs`.

### Strand 6: pilot bakeoff dispatch and checklist tooling

Scope: add bakeoff preflight for the private notes path, dispatch CLI writer, document Desktop writer instructions, collect outputs, score seven anchors, produce comparison report, and apply the acceptance gate.

Questions covered: content-production hypothesis, capability-profile routing, and Q12 implementation priority.

Test focus: missing private notes fail clearly, all seven anchors report, score calculation is deterministic, Desktop accepted/rejected is explicit, and generated artifacts stay out of PR diffs.

---

## What this ADR explicitly does not decide

This ADR does not decide:

- remote agent authentication
- cloud-hosted channels
- whether Desktop output should be trusted without code review
- final UX design for channels.html
- long-term blob retention
- promotion workflow from channel blob to curriculum asset
- whether every graphics-rich module must use generated images
- exact Desktop vendor priority if both Claude Desktop and Codex Desktop are available
- global task-claiming outside discussion threads
- mobile participation

Deferred follow-up ADRs may be needed for remote auth, retention and pruning, cross-channel task pickup, artifact promotion into curriculum assets, and a persistent participant registry.

---

## Review questions for Gemini

Please review this as an architecture gate, not implementation code.

1. Q1 schema: Are three first-class columns enough, or do we need a participant registry table in the first implementation?
2. Q2 discovery: Is replayable SSE plus MCP readable resource the right split, or should MCP expose a blocking subscription tool?
3. Q3 claim scope: Is `participant_scope=family` the correct default, with participant scope reserved as an escape hatch?
4. Q4 user semantics: Does default context mode plus explicit `--with user` quorum mode preserve the current discussion contract?
5. Q5 localhost auth: Is loopback-binding preflight sufficient for the first local prototype, or is token auth mandatory before remote support?
6. Q6 leases: Are 90 seconds for automated holders and 5 minutes for human/UI holders the right starting values?
7. Q7 idempotency: Is request-key idempotency on claim creation enough, or do post endpoints also need explicit client tokens in the first implementation?
8. Q8 atomic validation: Are the listed post-time invariants complete?
9. Q9 dynamic joins: Should late same-family surfaces be eligible claimants by default, or should every late participant be observer-only first?
10. Q10 event IDs: Is a global broker event sequence preferable to per-channel event sequences?
11. Q11 fallback identity: Is required-vs-actual identity sufficient for audit and bakeoff analysis?
12. Q12 attachments: Is filesystem blob storage under `.ab/channels/blobs` the right localhost default, and should image alt text be mandatory at attach time?
13. Pilot bakeoff: Is the `Desktop >= CLI + 2 anchors` gate strong enough to justify Desktop-required routing for graphics-rich modules?
14. Epic split: Is the six-strand split ordered correctly, or should the bakeoff run before any schema work?

Use `[AGREE]` for sections you accept, or `[REVISE Qn: reason]` for sections that need changes before user signoff.
