# DECISION REQUIRED — Multi-UI agent participation in `ab discuss` / channels.html

**Status:** PROPOSED (awaiting cross-agent review by Gemini + Codex, then user signoff)
**Surfaced:** 2026-05-06 morning, while running the writer-lock 3-way discussion
**Source:** GH issue #1731 Part B
**Predecessor ADRs:** None — this is the first ADR on multi-UI participation. Touches the `ab` channel-bridge contract from #1190.

---

## Why this needs an ADR (not just a PR)

`ab discuss` today is a **closed-loop, single-orchestrator** protocol. The agent that calls `ab discuss --with claude,gemini,codex` is a process that:

1. Spawns each named agent as a subprocess (one per round, per agent) via `scripts/agent_runtime/adapters/*.py`.
2. Reads each subprocess's stdout, posts the result to the channel, threads via `parent_id`.
3. Aggregates `[AGREE]` markers; short-circuits when all participants agree, or runs to `--max-rounds`.
4. Returns the transcript to the caller.

Three properties hold today only because of this closed-loop assumption:

- **Identity** is fixed at dispatch. `--with claude,gemini,codex` is the participant list; nothing else can join.
- **Time** is owned by the orchestrator. A round is "Gemini's reply has returned from `gemini -p ...`" — there's no clock outside the subprocess.
- **State** is a single transcript. The orchestrator is the only writer of `parent_id` chains; there is no claim/lock for "who responds next."

The user's ask — "Claude Code, Claude Desktop, Codex CLI, Codex UI, AND user can all participate" — breaks ALL THREE properties:

1. Claude Desktop is a separate process. It does not know `ab discuss` was invoked unless it polls or subscribes. → identity becomes dynamic.
2. Claude Desktop's reply latency is unbounded (user might walk away). → time can no longer be owned by the orchestrator.
3. If two Claude instances see the same channel post, both could reply. → state needs arbitration.

Patching `ab discuss` ad hoc would silently change the contract for every existing caller (the writer-lock discussion, every channel review, every pipeline review). That's the rule-violation we want to avoid. Hence: ADR first.

---

## Scope of THIS ADR

**In scope:** the participation/identity/round-semantics contract for an `ab discuss`-style multi-agent thread that can include Claude Code (CLI), Claude Desktop, Codex CLI, Codex UI, Gemini CLI, and human user.

**Out of scope** (explicitly deferred to follow-up issues, even if the design touches them):

- Real-time UI niceties (typing indicators, presence beyond "live now") — `playgrounds/channels.html` already has the basics, more polish is Part A territory.
- Authentication of remote/3rd-party agents — this ADR assumes all participants run on `localhost` and trust the `ab` broker DB; remote/cloud agents are a separate ADR.
- Action arbitration for non-discussion work (e.g. who picks up a `gh issue` to fix) — this ADR scopes "task pickup" to discussion-internal turn-taking only. Cross-channel work-claiming gets its own ADR if/when needed.
- Voice / video / image sharing in channels — text only.

---

## Six architectural questions (from #1731 Part B)

The questions below are quoted from the issue. Each gets a proposed answer with rationale and a tradeoffs subsection. The whole ADR is gated on user + Gemini + Codex agreement (or counter-proposal) on each.

### Q1. What is a 'participant'?

> "Currently `ab discuss --with claude,gemini,codex` lists *agents* invoked via the runtime adapter. If Claude Desktop is a participant, is it 'claude' (same agent name) or 'claude-desktop' (distinct)? What about user — is that a participant or an external observer?"

#### Proposal

A **participant** is the tuple `(agent_family, ui_surface, instance_id)`.

- `agent_family`: `claude` | `gemini` | `codex` | `user` — the model/identity class.
- `ui_surface`: `cli` | `desktop` | `web` | `mobile` | `headless` — the runtime context.
- `instance_id`: ephemeral UUID for THIS process/session (so two Claude Desktop windows on the same machine don't collide).

Wire format in DB: `agent_id = "{family}:{surface}:{instance_id_short}"`, e.g. `claude:cli:abc123`.

The legacy `from_agent` column stays as `agent_family` (so old queries keep working). New column `participant_id` carries the full tuple. The `ab channel post` API accepts either; the broker normalizes.

**User is a participant.** Family `user`, surface depends on where they post (web for channels.html, cli for `ab post`, desktop later). Treating user as first-class — vs "external observer" — is what makes "user posts mid-discussion" work without a special case.

#### Why this shape (not just a flat string)

Three needs the flat string can't satisfy without re-parsing:

1. **Round arbitration** asks "has every required agent_family replied this round?" That's a family-level question (we don't care if it was `claude:cli` or `claude:desktop`, just that `claude` answered). Family is a first-class column.
2. **Failure recovery** asks "did the SAME instance that started round N also produce reply N?" That's an instance-level question. Instance_id is a first-class column.
3. **UI rendering** asks "show the current participants by surface so user knows which window to look at." Surface is a first-class column.

#### Tradeoffs

- **Cost:** schema migration on `channel_messages` (add `participant_id` text col, indexed). Backwards-compat-safe (`from_agent` stays).
- **Risk:** instance_id collisions across reboots — solved by UUID4 on every process start. instance_id never persists.
- **Alternative considered (rejected):** "claude-desktop" as a distinct agent_family. Rejected because round-quorum logic ("does Claude agree?") wants the family to be invariant across surfaces — otherwise a `[AGREE]` from `claude-desktop` doesn't satisfy a quorum that listed `claude`.

---

### Q2. Discovery: how does Claude Desktop know a discussion is happening?

> "Polling? Push notification? An MCP server the desktop subscribes to? The desktop is a separate process that doesn't know `ab discuss` was invoked."

#### Proposal

**Three-tier discovery, layered:**

1. **Push (preferred):** Server-Sent Events stream at `GET /api/comms/channels/{name}/events` — open connection, receive `message_appended` and `discussion_started` events as they happen. Already runnable via `curl -N`; trivial to wire from any UI surface.
2. **Pull (fallback):** `GET /api/comms/inbox?agent={family}&since={ts}` — already exists; works for any client that prefers polling. Recommended interval: 5s (matches channels.html auto-refresh; no point going faster than human read speed).
3. **MCP tool (Claude Desktop / Claude Code specifically):** `mcp__channels__subscribe(channel)` thin wrapper over the SSE endpoint. Returns a resource the model can read on each turn. Lets Claude Desktop "see" channel activity without writing browser-automation code.

`ab discuss` itself emits a `discussion_started` event with `{thread_id, channel, participants_invited, max_rounds, initiator}` so subscribers know a structured discussion is open vs an ad-hoc thread.

#### Why all three (not just one)

Different surfaces have different cost profiles:

- **CLI / shell agents** can hold an SSE connection cheaply; push is right.
- **Stateless adapters** (e.g. a one-shot `gemini -p ...` invocation) can't hold a connection across calls; they need pull.
- **Claude Desktop / Code** through MCP is the cleanest — the model sees subscription as a tool, not infrastructure.

Layering doesn't add server complexity: the SSE endpoint and inbox endpoint share the same DB query; MCP is a thin shim over SSE.

#### Tradeoffs

- **Cost:** new SSE endpoint (~150 LOC FastAPI), new MCP tool (~80 LOC). Pull endpoint already exists.
- **Risk:** SSE connection leaks if a client crashes — mitigated by a 60s server-side keepalive ping; idle connections auto-close after 10 min.
- **Alternative considered (rejected):** WebSocket. Rejected because SSE is sufficient (server→client only; we don't need bidirectional), simpler to debug (just `curl -N`), and survives proxies that strip WS headers.

---

### Q3. Action arbitration: who picks up tasks?

> "If the channel says 'someone please review module X', what stops 3 agents from picking it up simultaneously? Need a claim mechanism (DB-level lock or first-poster-wins)."

#### Proposal (scoped to in-discussion turn-taking — see "out of scope" above for cross-channel claim)

For an active `ab discuss` thread, **the orchestrator owns the turn schedule**, exactly as today. Discovery tells Desktop/UI/etc. "a discussion is happening" but they don't auto-respond — they observe.

A non-orchestrator participant **must explicitly claim a turn** to contribute. Claim mechanism:

```
POST /api/comms/channels/{name}/threads/{tid}/claim
  body: {participant_id, round_index}
  → 200 {claim_id, expires_at}  on success
  → 409 {current_holder, expires_at}  on conflict
```

Claims are scoped to `(thread_id, round_index, agent_family)`. Two `claude:*` instances cannot both claim round 3 of thread T — first-poster-wins. Claims expire after 90s if no message follows; another instance can re-claim.

The orchestrator's existing subprocess-spawn path **also goes through claim** (no special path), so the contract is uniform: "to post a round-N reply, you hold the claim."

#### Why claim per `(thread, round, family)` not per `(thread, round, instance)`

Family-scoped claim is what makes "Claude Desktop joins instead of Claude Code for round 3" work. The orchestrator says "we need a claude reply in round 3"; whichever claude-instance holds the claim first delivers it. That's the user's mental model: "I'm tagging in for Claude this round."

Instance-scoped would force a deterministic spawner per instance — back to the closed-loop world.

#### Tradeoffs

- **Cost:** new `claims` table (`thread_id, round_index, agent_family, holder_participant_id, claimed_at, expires_at`); `~80 LOC` for the endpoint + claim-expiry sweep.
- **Risk:** claim deadlock if the holder never delivers — solved by 90s expiry + re-claim. Keepalive every 30s extends.
- **Risk:** claim livelock if 5 Claude instances all retry on 409 — solved by exponential backoff + jitter; documented in client lib.
- **Alternative considered (rejected):** "first-message-wins" with no claim. Rejected because two slow agents racing each other waste tokens producing replies that get rejected. Pre-claim is cheap.

---

### Q4. Round semantics with mixed participants

> "If user posts mid-round, does that count as a round-N reply? Does `[AGREE]` from user terminate the discussion? Or is user input always 'context for next round'?"

#### Proposal

**User posts are always round-N+1 context, never count as round-N replies, and `[AGREE]` from user is treated as a HARD STOP (not consensus).**

Concretely:

- A user post during round N (i.e. while ≥1 agent_family hasn't yet posted round N) does NOT satisfy that family's round-N obligation.
- The user post's body IS injected into the round-N+1 prompt for every agent (verbatim, prefixed with `[USER (mid-discussion)]:`), so the next round can react to it.
- `[AGREE]` from a user post terminates the discussion immediately — but it's recorded as `kind: "user_terminate"` in the DB, not aggregated into the consensus quorum. Discussion outcome = "ended by user," not "converged."
- `[OBJECT]` (new marker) from user resets convergence; if all agents had said `[AGREE]`, an `[OBJECT]` from user forces a round N+1 with the objection as injected context.

#### Why user posts aren't replies

Two reasons:

1. **Quorum integrity.** The discussion contract is "agents converge on a recommendation." Counting user as a vote conflates "agents agree" with "agents agree AND user happens to also agree" — fundamentally different signals. The user is the consumer of the recommendation, not a producer of it.
2. **Steering value.** If user posts ARE replies, the user can short-circuit a useful debate by `[AGREE]`-ing with whoever they liked best. We want the user to be able to steer ("I think X is missing, address it") without ending the deliberation.

#### Tradeoffs

- **Cost:** ~30 LOC in the discuss orchestrator to inject user posts into the next round's prompt. Schema is unchanged (already has `kind`, `from_agent`).
- **Risk:** user spam mid-discussion (10 posts in a row) bloats the next round's prompt. Mitigation: cap the injected user-context block at 2000 chars, oldest-first truncate.
- **Alternative considered (rejected):** "user posts ARE first-class replies, just from agent_family=user." Rejected because the round-N quorum was specified as "all agents in `--with`" — and `user` isn't in `--with` by default. Adding user to `--with` opens the abuse vectors above.

---

### Q5. Identity / auth

> "Claude Code, Claude Desktop, Codex CLI, Codex UI — do they share auth tokens? Do they post as distinct identities or as the same 'claude'/'codex'?"

#### Proposal (localhost-only — remote auth deferred)

- All participants run on `localhost`. No auth for now beyond "the broker DB is owned by user `krisztiankoos`."
- A participant **identifies itself** to the broker via `participant_id` (Q1's tuple). The broker does not verify — it's an honour system on localhost.
- A participant **identifies its origin** via a `client_app` field (`claude-cli/2.1.131`, `claude-desktop/0.x`, `codex-cli/y.y`, etc.) for telemetry and debugging.
- Distinct surfaces post under distinct `participant_id`s but share the same `agent_family` for quorum (Q1).

If we later need remote agents or shared multi-user installs, this gets revisited as a separate auth ADR. The localhost-only assumption is explicitly recorded so we don't accidentally expose `:8765` to the network without revisiting.

#### Why no token auth now

Adding auth before we have a working multi-UI prototype is premature optimization. The broker DB is already user-readable only (file mode 0600 in `.ab/broker.db`); an attacker on the same machine has bigger problems. When we go remote, JWT or mutual TLS goes here.

#### Tradeoffs

- **Risk:** any local process can post as anyone. Acceptable on a single-user dev machine; documented in `docs/best-practices/agent-bridge.md`.
- **Risk:** `:8765` is bound to `0.0.0.0` not `127.0.0.1`? Verify and tighten (separate fix).

---

### Q6. Failure semantics

> "If Claude Desktop drops mid-round (user closed the app), does the discussion wait or short-circuit?"

#### Proposal

- A claim expires 90s after issue if no message follows (Q3). If the discussion's `--max-rounds` budget is `M` and we're in round `R`, the orchestrator waits at most `90s × (M − R + 1)` for any pending claim, then either:
  - re-prompts the SAME agent_family (subprocess-spawn path) if `--auto-fallback=true` (default in `ab discuss`),
  - or aborts the discussion with `kind: "discussion_aborted"` and `reason: "claim_expired"` if `--auto-fallback=false`.
- Auto-fallback uses the legacy `agent_runtime` adapter, so a discussion that started with Claude Desktop participating can degrade to Claude CLI without losing thread continuity.
- Aborts are first-class events; the channel sees `discussion_aborted` so observers don't think it converged.

#### Why 90s + auto-fallback (not infinite wait)

Infinite wait makes the channel unusable: a stuck discussion blocks `[AGREE]`-aggregation forever and channels.html's "Discussion live" strip never resolves. 90s is enough for a typical Desktop reply (Anthropic SDK p99 < 30s) plus user think-time; longer human deliberations can be done as multi-thread "post-then-respond" without round semantics.

Auto-fallback to subprocess-spawn preserves the closed-loop as the safety net. We only LOSE the closed-loop when a multi-UI participant successfully claims and replies — exactly the path we want to support.

#### Tradeoffs

- **Cost:** ~60 LOC for claim-expiry sweep + fallback path in `_channels.py`.
- **Risk:** flaky network on Desktop side causes false fallbacks. Mitigation: keepalive every 30s extends claim; stable connections never expire.
- **Alternative considered (rejected):** "wait forever, user kicks the discussion manually." Rejected because UX suffers and the "Discussion live" strip becomes a forever-live ghost.

---

## What this ADR explicitly does NOT decide

These are downstream questions for follow-up ADRs once the contract above is accepted:

- **MCP tool surface for Claude Desktop / Code.** `mcp__channels__subscribe` is sketched in Q2 but the full tool family (post, claim, observe, list) needs its own design.
- **Codex UI integration mechanism.** Codex UI is a web app; whether it polls SSE or uses an iframe-postMessage bridge to channels.html is undecided. Both work; pick after MCP tools land.
- **Cross-channel task pickup** ("someone fix #1234"). Out of scope — see top of doc.
- **Persistence beyond `.ab/broker.db`.** Single-DB single-user is fine for now; multi-user / replicated broker is a separate ADR.

---

## Implementation epic (only after ACCEPTED)

If/when this ADR flips PROPOSED → ACCEPTED, the implementation splits into 4 strands, each filable as its own issue:

1. **Schema + claim mechanism** (Q1, Q3): `participant_id` column, `claims` table, claim/release endpoints, expiry sweep. ~250 LOC + tests.
2. **SSE event stream** (Q2): `/api/comms/channels/{name}/events` + `discussion_started`/`message_appended` events. ~150 LOC + tests.
3. **Discuss orchestrator updates** (Q3, Q4, Q6): claim integration, user-post injection, fallback path. ~200 LOC + tests in `scripts/ai_agent_bridge/_channels.py`.
4. **MCP tool family** (Q2 follow-up, separate ADR): `mcp__channels__*` tools for Claude surfaces.

**channels.html** updates (UI rendering of multi-UI participants, claim status indicator, user-post-as-context visual treatment) layer on top once strands 1+2 land.

---

## Review questions for Gemini + Codex

When this ADR fires for cross-agent review, please critique specifically:

1. **Q1 schema migration:** is `participant_id` as a tuple-encoded string the right wire format, or should it be 3 separate columns? My choice is single-column for migration simplicity; counter-argue if you see a problem.
2. **Q2 push-vs-pull:** is layering all three (SSE + inbox-poll + MCP shim) over-engineering? Could we ship pull-only and add SSE later, or is push fundamental to the user-experience?
3. **Q3 claim scope:** family-scoped vs instance-scoped claim. I argued family-scoped enables the "tag in" use case. Counter-cases?
4. **Q4 user-as-context:** is "user posts are NEVER replies, always context" too rigid? Steel-man the case for letting user be a first-class quorum participant when they explicitly join `--with`.
5. **Q5 localhost auth:** is "no auth on localhost, document the assumption" sufficient, or should we ship a token even now?
6. **Q6 90s claim expiry:** too short (Desktop with slow LLM) or too long (channels.html UI feels frozen)? Propose alternative if you can defend it.
7. **Anything missing.** Are there architectural questions I didn't raise that you'd want answered before implementation?

Use `[AGREE]` to signal acceptance per question, or `[REVISE Q3: <reason>]` to push back on a specific section. The aggregator will collate.
