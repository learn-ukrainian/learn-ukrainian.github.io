# Cycle 007 evidence-compile throughput (design)

Status: resume-only implementation candidate. It requires CI, independent
cross-family exact-head approval, merge, and deployment before a new evidence
compile may start. Packet-parallel execution remains unauthorized.

This document is text-free: counts, hashes, tool names, and pass/fail facts
only. It does not name hosts, addresses, or private row content.

Parent stream: Phase 3 recovery issue `#6375`. Frozen Cycle 007 contract:
`batch_state/phase3-cycle007-source-grounded-amendment-v1.md`.

## Recommendation

Ship **option A first**: durable resume after a sealed packet prefix. Keep
packet compilation serial and keep the frozen query plan unchanged.

Option A is the only change that removes the multi-day restart cost. The
current compiler can already take a long clean run; the dominant loss is
that every stop discards staging and returns to packet 1 of 204.

The previous compile stopped cleanly without installing evidence. This change
may activate only for a later operator-authorized run after the review gates in
[Amendment and review](#amendment-and-review).

## Confirmed current parallelism

Read of
`scripts/projects/open_model_data/phase3_cycle007_evidence_compiler.py` and
the text-free runner
`batch_state/phase3-compile-cycle007-evidence-v1.py` on the reviewed main
head used for this design:

| Layer | What actually runs | What the name sounds like |
| --- | --- | --- |
| Packet loop | Serial `for` over packets `1..N` inside `compile_sidecar_bundle` | Packet-parallel |
| Row loop | Serial `for` over rows inside `compile_packet_sidecar` | — |
| Per-row channels | Sequential Sources calls in `compile_row_evidence` | Amendment step 5 "always-on parallel path" |
| MCP client | One `LocalMcpSourcesClient` / one `RealMcpToolTransport` / one session | N workers |
| Install | Fresh staging directory, validate all sidecars, then atomic claim of `output_dir` | Resume |
| Runner | Starts one reviewed Sources process, compiles, refuses if `output` exists | Checkpoint |

The amendment phrase "always-on parallel path" is a **coverage** rule: style
guide, Antonenko prose, UA-GEC, and heritage run for every row and are not
gated on a VESUM miss. It is not a concurrency rule. Those calls are issued
one after another on one synchronous client.

`RealMcpToolTransport` owns one background asyncio loop and one MCP session.
`call_tool` waits for that session. `LocalMcpSourcesClient._call_text`
mutates the ordered-call commitment without a lock. One client is therefore
single-threaded at the wire.

The public manifest stores `mcp_transport_attestation`, including
`tool_call_count` and `ordered_call_commitment_sha256`. That commitment is a
process-global hash chain over `(ordinal, tool, arguments_sha256,
response_sha256)`. Any resume or fan-out that drops, reorders, or interleaves
calls changes the public manifest even when every sidecar body stays the
same.

`CODE_HASHES` binds `compiler_sha256` to the whole compiler module. Editing
that file changes every new sidecar and therefore prevents an old prefix from
resuming under the new compiler identity. The resume helper is imported by the
compiler and runner only for custody and recovery.

Frozen real-mode denominator, unchanged by this design: `REAL_PACKET_COUNT =
204`, `REAL_ROW_COUNT = 10159`.

## Ranked options

### A. Durable resume after sealed packet N (do this)

**User-visible outcome.** A stopped compile continues at packet `N+1` when
packets `1..N` are already validated, sealed, and identity-bound. Packet
`N+1` that did not finish is discarded, never resumed mid-row.

**Why it is first.** Foundry already observed a 60-packet prefix discarded
with the destination left at `0/204`. Serial MCP cost is real; throwing away
a sealed prefix is the part that turns one long run into several.

**Smallest safe shape.**

1. Keep `output_dir` refuse-if-exists and the final atomic install.
2. Replace *ephemeral* staging (`mkdtemp` + delete on any failure) with a
   durable sibling staging directory, mode `0700`, files mode `0600`.
3. After each packet: `validate_sidecar`, atomic write `sidecar-NNNN.json`,
   fsync, write a text-free progress receipt.
4. Progress receipt fields are a closed set: schema, `text_free`, cycle id,
   sealed count, next index, target `204`/`10159`, last sidecar hashes,
   identity hash, transport attestation, and a complete hash-only MCP call
   ledger. The ledger stores ordinal, fixed tool name, argument SHA-256, and
   response SHA-256 only—never paths, row text, arguments, responses, prompts,
   locators, labels, or provider content.
5. On start: if durable staging is empty, begin at packet 1. If a prefix
   `1..N` exists, re-validate identity and bindings, replay the persisted
   call-chain, continue at `N+1`. A gap, leftover foreign file, or identity
   drift fails closed.
6. Exactly one incomplete `mkstemp` sidecar for `N+1` may be deleted. Gaps,
   multiple temps, foreign entries, symlinks, wrong ownership, or permission
   drift fail closed.
7. A compiler-level nonblocking lock protects the deterministic resume root
   for the full run, independently of any external guardian lock.
8. After packet 204, assemble the same manifest shape, validate it, and install
   the complete `bundle/` with one atomic no-replace directory rename. A crash
   after rename but before metadata cleanup is repaired only after the installed
   output revalidates.
9. Creation and every durable commit point fsync the relevant parent directory.
10. Terminal cleanup first atomically retires the live resume root to an inert
    tombstone while the compiler lock is still held. A crash during tombstone
    removal cannot block idempotent validation of the already-installed bundle;
    a later validated invocation reaps an unlocked leftover tombstone.

**Sidecar bytes.** `compile_packet_sidecar` is already independent per
packet given the same server identity and rows. A resumed serial run with
the *same* compiler module SHA can emit the same sidecar files as a clean
run. A compiler-module edit cannot resume a prefix sealed by a different
`compiler_sha256`.

**Public manifest.** Keep today's attestation schema by recomputing the
persisted hash-only ledger after each sealed packet and continuing ordinals.
Each resumed process performs a real `mcp_server_identity` call, so the final
transport attestation can legitimately differ from a never-interrupted run.
The sidecar bytes remain deterministic; the attestation honestly describes
the actual transport history.

**Contract touch.** Compiler commentary currently calls this "amendment
step 14": the whole bundle is staged and validated before anything is
installed, and failure deletes only that staging directory. Durable
prefix-seal is a material change to that install/custody rule. It does
**not** change the query plan, tokenizer, channels, evidence-ID recipe, or
the `204`/`10159` denominator.

**Risks.** Partial last packet must never be treated as sealed. Identity
drift (compiler, Sources server, `sources.db`, `vesum.db`) must fail
closed rather than mix prefixes. Staging must stay operator-private
(`0700`/`0600`) and off public surfaces. Disk accounting must count sealed
sidecars plus one in-progress atomic temp, which is the estimator Foundry
already uses.

### B. Bounded packet-parallel with N Sources clients (later)

**User-visible outcome.** Up to N packets compile at once, each with its
own `LocalMcpSourcesClient` / `RealMcpToolTransport`. Sidecar `packet_index`
order in the manifest stays `1..204`.

**Why it is second.** It can cut a *clean* run, but it does not save a
restart unless A exists. It also cannot preserve the current process-global
`ordered_call_commitment_sha256` without serializing the wire, which
defeats the fan-out.

**Contract-safe constraints if later authorized.**

- Query plan, evidence IDs, and per-packet sidecar bodies stay serial-equivalent.
- N new clients, not one shared client (the current client is not
  thread-safe).
- Prefer proving N sessions against one reviewed Sources process *or* N
  loopback processes bound to the same reviewed code/data identity. The
  Sources DB helper caches one process-global SQLite connection
  (`check_same_thread=False`). Concurrent `asyncio.to_thread` use of that
  singleton is not a proven read-parallel contract. A public concurrency
  canary is a precondition, not an afterthought.
- Bound N fail-closed (scaffolding default is `1`; a request for `N>1` is
  `packet_workers_not_authorized` until an addendum says otherwise).
- Attestation must become a sorted per-packet composition, or B changes
  the public manifest schema. That is an amendment-visible change.

**Risks.** SQLite/FTS contention, memory of N in-flight sidecars, disk
temp amplification, non-deterministic call order, and mixed identity if
workers attach to different endpoints. Higher CF surface than A.

### C. Other low-risk throughput (supporting, not a substitute)

Ranked under A, and none of these replace sealed-prefix resume:

1. **Text-free sealed-count pulse from durable staging** — operational
   visibility only. Already possible as counts/hashes. Does not save work
   unless A persists the files.
2. **Keep one Sources process for the whole compile** — the runner already
   does this. Do not start/stop per packet.
3. **Process-local form cache** — amendment pre-call language already
   mentions deterministic cache reuse, but today's public attestation is
   an ordered *call* chain. Caching would drop `tool_call_count` and
   change `ordered_call_commitment_sha256`. Safe only after attestation is
   packet-composed (same addendum family as B) or after cache hits are
   folded into the chain with a closed, reviewed record type. Do not
   silently skip MCP calls.
4. **Intra-row channel overlap** — same client-safety and attestation-order
   problems as B, smaller payoff than packet-parallel.
5. **Do not pull a new compiler SHA onto a live run** — `CODE_HASHES` and
   the controller canary bind the compiler file. A mid-run checkout of an
   activation commit cannot resume the prefix it interrupted.

C items 1–2 need no amendment. C item 3 needs the same attestation review
as B. C item 5 is a hard operational rule.

## Amendment and review

Frozen, do-not-edit artifact:

- path: `batch_state/phase3-cycle007-source-grounded-amendment-v1.md`
- SHA-256: `4f2e3e58964cae391c3933ffdce531296a0744808b0154231ca513049602fea0`

Controller, Gemini/Grok runners, adjudication, and completion tooling all
bind that exact hash. Rewriting the frozen file is out of scope.

The frozen amendment already requires:

- exact `204` packets / `10159` rows
- text-free public receipts
- no network fallback during compile
- fail-closed missing/conflicting evidence
- no mid-run validator, taxonomy, source-hierarchy, or custody change
  inside a live run
- pre-call proof that the compiler produced `204` sidecars / `10159` rows

It does not authorize durable prefix-seal or packet-parallel workers.

### Review findings and reconciliation

An independent Anthropic-family design review returned `BLOCK` on the inert
draft. This implementation treats all six findings as required:

1. Fresh and resumed deterministic paths reject preplacement and symlinks.
2. Every resume artifact requires the current UID plus exact `0700`/`0600`.
3. A compiler-level `flock` rejects a concurrent compiler.
4. Final installation is one no-replace directory rename, with terminal-crash
   repair, rather than a sequence of per-file moves.
5. The complete hash-only call ledger makes the aggregate commitment
   independently recomputable.
6. Initial creation and every sealed commit fsync the parent directory.

The trust boundary is explicit: the private writer seat's Unix user controls
the receipt and sidecars. Hashes detect corruption and drift; they are not an
external signature against a malicious same-user actor.

### What needs review

| Change | New addendum? | Review seats |
| --- | --- | --- |
| Resume-only implementation | Yes. Changes step-14 install/custody. | CI + independent cross-family exact-head review. Ukrainian source-authority only if a reviewer claims the query plan moved (it must not). |
| B: N clients / composed attestation | Yes, separate from A. | Scope/circularity + CF. Public Sources concurrency canary. |
| C.3 process-local MCP skip cache | Yes, unless the addendum already redefined attestation. | Same as B |
| C.1–C.2 operational pulse / one server | No | None beyond current text-free pulse rules |

### Resume-only custody addendum

Working title: Cycle 007 compile-throughput addendum (resume-only).

Intended bindings, to be hashed only after the review seats approve the
exact bytes:

- Parent amendment SHA-256 remains
  `4f2e3e58964cae391c3933ffdce531296a0744808b0154231ca513049602fea0`.
- Query plan, tokenizer, compound parser, channels, evidence-ID recipe,
  residual taxonomy, and `204`/`10159` are unchanged.
- Compiler may persist validated `sidecar-NNNN.json` files and one
  text-free progress receipt in a durable private staging directory.
- Resume is authorized only for a consecutive sealed prefix whose
  `code_hashes` and Sources identity match the running compiler.
- Mid-packet state is discarded.
- Final `output_dir` install stays atomic and refuse-if-exists.
- Public `mcp_transport_attestation` stays schema
  `phase3_cycle007_mcp_transport_attestation_v1` and honestly includes each
  resumed process's identity call in the persisted serial chain.
- Packet-parallel workers remain unauthorized.
- Activation against a compile already in flight under another
  `compiler_sha256` is forbidden.

Until CI and an independent cross-family exact-head review approve the PR,
the implementation must not be deployed or used for an evidence run.

## Smallest PR path

1. **This PR.** Resume-only custody implementation, synthetic crash matrix,
   CI, and independent cross-family exact-head review.
2. **After merge/deployment and explicit START.** One clean serial compile;
   a process failure resumes only a fully validated sealed prefix.
3. **Optional later PR.** B, only with a composed-attestation addendum and
   a public concurrency canary.

Success for this PR: a contract-safe serial resume that preserves text-free
Cycle 007 bindings, refuses ambiguous state, survives the tested crash matrix,
and installs a complete bundle atomically.

## Non-goals

- Starting or restarting Foundry before review and deployment.
- Editing the frozen amendment file.
- Packet-parallel activation.
- Changing query plan, validator behavior, endpoint, chunk size, packet/row
  denominator, labeling protocol, or source custody.
- Labeling. Labeling stays off until a later START after evidence seals.
