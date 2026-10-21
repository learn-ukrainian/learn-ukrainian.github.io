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
`learn-ukrainian/entire-checkpoints-private`. Public Entire shadow refs and
public disclosure of transcript, prompt, or generated-summary bodies are
forbidden. Entire documents redaction as best-effort and states that local
shadow refs can contain raw working-tree snapshots. The public checkout's
`origin` is the public product repository, so an explicit private-destination
guard is a prerequisite, not a follow-up.

## Decision

Entire (pinned by the 0.11.5 amendment below) is an optional, read-only context
and provenance index. It never owns task state, coordination, leases, recovery,
review eligibility, or source content. An LLM may use an Entire search result only as a locator; before any
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

- CLI remains pinned to the version the 0.11.5 amendment below names, and
  Entire authentication is valid;
- Entire's own status reports the dedicated private checkpoint route;
- `learn-ukrainian/entire-checkpoints-private` is private and contains the
  canonical checkpoint ref;
- the public product origin contains zero `entire/*` branches;
- the checkpoint mirror and public-upstream source mirror are ready and their
  Entire ACLs contain only the operator.

The source code remains public on GitHub by product choice. That does not make
its Entire mirror public to other Entire users: the preflight checks the live
Entire control-plane collaborator list and fails unless only the operator can
pull either mirror.

After that receipt, the accountable root automatically runs bounded,
repository-scoped search and may use explain for real session continuity. Full
explain stays within the root's private working context; raw-transcript flags
remain prohibited. Generated recap/dispatch and worktree-mutating
resume/rewind remain operator-directed. Native Entire remains optional and
non-authoritative.

### Amendment: Entire 0.11.5 (2026-10-16)

Recorded under [#10846](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/10846);
it replaces the earlier rule that this decision does not authorize moving
beyond 0.8.42.

The last accepted Entire CLI version is recorded in stack_pins.yaml; it is an acceptance record, not an expiry. A newer CLI is allowed only after a compatibility review re-proves the version-sensitive canaries (fail-closed version preflight, private-destination allowlist, zero public entire/* refs, body-leakage scan, fail-open outage behaviour, locator digest checks), with independent cross-family review and a reviewed rollback procedure. Until that review is recorded, automated calls prove the accepted version. A version probe is not that review. After approval, the native-recall preflight and the runtime version guard move to the new version in the same change.

`stack_pins.yaml` does not exist yet (DevOps stack-currency policy v3), so this
ADR records the accepted version until it lands: **Entire CLI 0.11.5**, accepted
by the #10846 compatibility review below. The pin row is added when the file
lands. The runtime version guard is `ACCEPTED_VERSION` in
`scripts/entire/capture_guard.py`; the native-recall preflight imports it.

What the upgrade changes in this repository:

- **Control-plane calls.** 0.11.0 removed `repo mirror collaborators list`
  without an alias, and 0.11.3 removed its successor `repo access list`. The
  preflight now reads each mirror's ACL with
  `entire repo grant list /gh/<owner>/<repo> --json` (rows carry `granteeName`,
  `role` and `source: "github"`) and each mirror's readiness with
  `entire repo view /gh/<owner>/<repo> --json`. The provider takes the dispatch
  jurisdiction from that `repo view` row's ready placements instead of the old
  `repo mirror list` row shape. `search`, `checkpoint explain`,
  `api --jurisdiction`, `status --json`, `recap`, `dispatch` and
  `session resume` keep the shapes `.entire/private-recall.json` lists.
- **Route proof.** The preflight compares the version's first line exactly and
  requires `entire status --json` to report
  `checkpoint_sync_remote_source: "dedicated"` for the private repository with no
  `checkpoint_remote_ignored`. When `checkpoint_remote` is judged not to belong
  to the checkout (for example an `origin` owned by another account), both 0.8.42
  and 0.11.5 push checkpoints to the push remote instead; 0.11.5 reports that in
  `status --json`, so the preflight now fails closed on it.
- **Capture guard.** Recall is not the only place the version and route
  matter: every checkpoint-producing entry point runs Entire through
  `scripts/entire/capture_guard.sh`. That covers the Claude Code and Codex
  lifecycle hooks, the Cursor shim, fleet capture, and all five Entire git hook
  wrappers. Before Entire runs, the guard checks the routing allowlist, the
  exact version line and the same `status --json` route predicate the preflight
  uses. A failed check refuses capture with one `[entire] capture refused (...)`
  stderr line, and Entire is never called. An Entire failure or hang after the
  checks is an outage. The guard exits 0 in both cases, so the host session and
  `git` continue and the repository pre-push gate alone decides a push. The
  pre-push wrapper is the only automatic checkpoint egress in 0.11.5 (Entire's
  `PrePush`; the manual `entire attach` is the other caller), so the route check
  there is what keeps checkpoints off a public remote. The guard adds about one
  `entire version` and one `entire status --json` call per hook. Measured cost is
  in the table below.
- **Checkpoint backend.** It stays `branch`. The settings carry no
  `checkpoints` block, which 0.11.5 resolves to the branch backend, and
  `entire enable --force` did not add one in the canary. Migrating to the
  git-refs backend is a separate decision.
- **Hooks.** Claude Code Stop and post-task timeouts follow the 0.11.5 template
  (120 s); the other Entire hooks keep 30 s, which matches the template. Entire
  git hook wrappers without a chain are byte-identical in both versions; the
  0.11.5 chained form differs, and `scripts/install_git_hooks.sh` now writes
  that form and still recognizes the 0.8.42 form (see `hook-audit.md`). The
  installer also routes each wrapper's `entire hooks git` call through the
  capture guard. Entire 0.11.5 treats the guarded line as current and leaves it
  in place; `entire enable --force` rewrites it, after which
  `scripts/install_git_hooks.sh --check` reports the wrapper `UNGUARDED` until
  the installer is rerun. The installer refuses to write through a symlinked
  hooks directory or hook file.
- **External agents.** Since 0.10.6, `external_agents` is honored only from an
  untracked `.entire/settings.local.json`. No `entire-agent-*` binary is
  installed today, so nothing changes until one is.

Canary evidence (#10846). The receipts are tracked, sanitized text under
[`evidence/entire-0115-canary/`](evidence/entire-0115-canary/) (`round-1/` for
the first upgrade canary, `round-2/` for the capture-guard canary; local paths
are replaced by placeholders and scripts keep a `.txt` suffix). Both rounds
used a throwaway clone of the branch with about 32,600 tracked files and
463,000 gitignored files. Each binary ran with an isolated home directory and
no credentials, inside a network namespace with no route out
(`round-2/tool-cenv.sh.txt`). Every remote was a local bare repository behind
a GitHub-shaped URL, reached through a logging fake `ssh`
(`round-2/tool-fake-ssh.txt`, transfer log `round-2/log-ssh.txt`): a public
`origin`, the private checkpoint store, and a fork owned by another account.
The 0.11.5 release archive matched the pinned checksum. The 0.8.42 archive
matched its release `checksums.txt` (`round-1/CANARY-SUMMARY.txt`,
`round-2/tool-canary-setup.sh.txt`). In round 2 the agent hooks ran the
configured, guarded commands from `agents_extensions/shared/settings.json`, and
the git hooks were the installed, guarded wrappers.

The six version-sensitive canaries (round 2 unless noted):

| Canary | Result | Receipts |
| --- | --- | --- |
| Fail-closed version preflight | Proved. The real 0.11.5 binary captures (trailer, private store advanced). The real 0.8.42 binary and 0.11.5-backed variants reporting `0.11.50`, `0.11.6` or a malformed line are all refused with `cli_version_not_accepted`. A hung `version` call is refused with `guard_probe_timeout`. Each refusal leaves no trailer and no checkpoint, and the push still goes through the gate. | `log-r2-01-accepted.json`, `log-r2-02-version-0.8.42-real.json` … `log-r2-06-version-hang.json`, `log-scenarios.txt` |
| Private-destination allowlist | Proved. The tracked settings were pointed at the public repository, and raw `status --json` then reported a `dedicated` route to it: refused with `routing_allowlist_failed`. A `settings.local.json` override to a foreign repository was refused with `checkpoint_route_not_private`. So was an `origin` owned by another account, which is round 1's S3, where an unguarded push put `entire/checkpoints/v1` on the fork. | `status-r2-07-tampered-tracked.json`, `log-r2-07-…`, `status-r2-08-local-override.json`, `log-r2-08-…`, `status-r2-09-misowned-origin.json`, `log-r2-09-…`, `round-1/log-s3-capture-0115.json.txt` |
| Zero public `entire/*` refs | Proved. Every scenario log records the refs of all three remotes after its push (`refs_after`, `public_entire_refs: []`). The final public and fork remotes hold only `refs/heads/main`. | every `log-r2-*.json`, `refs-final.json`, `log-ssh.txt` |
| Body-leakage scan | Proved. Every object in each bare repository, reachable or not, was read with `git cat-file --batch-all-objects --batch` and searched for three planted strings: one in the prompt, one in an ignored file and one in an untracked file never committed, and one in committed code. Public (34,272 objects) and fork: 0 objects held the prompt or the uncommitted bodies. Private store: 0 objects held the uncommitted bodies. The prompt appears only in `full.jsonl`, `prompt.txt` and `transcript.jsonl`, the transcript kinds the private store exists to hold. | `log-r2-19-leakage-scan.json`, `tool-canary-leakscan.py.txt` |
| Fail-open outage behaviour | Proved. In every case the repository pre-push gate ran and decided the push. Cases: every Entire call failing; `hooks git pre-push` exiting 1; that call hanging (stopped at the 110 s budget, push completed in 110.2 s); the private store unreachable (Entire kept the checkpoint locally, and the next push synced it). With a failing gate and an Entire outage, the push was refused by the gate. | `log-r2-10-…` … `log-r2-14-…`, `log-r2-16-accepted-store-back.json` |
| Locator digest checks | Proved for a 0.11.5 checkpoint and for a checkpoint written by 0.8.42 before the upgrade. The commit's `Entire-Checkpoint` trailer names the checkpoint the locator carries, and 0.11.5 `checkpoint explain <commit-sha>` returns the same id. `reverify_link` accepts the locator, and rejects a tampered digest and a locator moved to another commit with `digest_mismatch`. | `log-r2-18-locator-digest.json`, `log-r2-17-legacy-0842-unguarded.json`, `tool-canary-locator.py.txt` |

Wrapper bytes: Entire's own unchained and chained wrappers, the installer's
guarded output, and the `entire enable --force` → `--check UNGUARDED` →
rerun round trip, which reproduces the first install byte for byte
(`wrapper-*.txt`, `log-hooks-phase.txt`). Entire's `status --json` left the
guarded wrappers unchanged.

| Measurement | 0.8.42 p50 / p95 | 0.11.5 p50 / p95 |
| --- | --- | --- |
| `hooks claude-code user-prompt-submit`, direct (round 1, n = 20) | 8.33 s / 9.31 s | 1.68 s / 1.94 s |
| `hooks claude-code stop`, direct (round 1, n = 20) | 7.20 s / 7.45 s | 2.15 s / 2.36 s |
| `checkpoint explain <id> --json` (round 1) | 0.10 s / 0.16 s | 0.09 s / 0.12 s |
| user-prompt-submit, direct / guarded (round 2, n = 10 each) | — | 1.72 s / 1.72 s (p95 3.76 s / 1.84 s) |
| stop, direct / guarded (round 2, n = 10 each) | — | 2.10 s / 2.25 s (p95 2.76 s / 2.55 s) |

Latency receipts are in `round-1/log-latency-*.json.txt` and
`round-2/log-latency-r2-*.json`. The 1-minute load average was 13.7–17.8.
`status --json` alone took 0.06–0.07 s in that clone. No hook call failed. In
round 1 (`round-1/CANARY-SUMMARY.txt`), 0.11.5 explained a 0.8.42 checkpoint
with the same core fields, and 0.8.42 read a 0.11.5 checkpoint after
rollback. A non-interactive `entire doctor` changed no hook, setting or ref.
The round-2 mutation checks (`round-2/mutation-r2-tests.txt`) show the new
tests fail on the round-1 behaviour.

Not proved: authenticated cloud search. The canary used no credentials,
because a token refresh could rotate the live refresh token. Its JSON count
fields are unchanged in the 0.11.5 source, and the install runbook checks it
live.

Install and rollback:
[`docs/runbooks/entire-cli-upgrade.md`](../../runbooks/entire-cli-upgrade.md).
Rollback reinstalls the kept 0.8.42 binary and reverts the PR. Downgrading
discards pending, uncommitted agent session state, and legacy shadow branches
are not removed automatically (Entire 0.11.5 release notes); leave them for a
separate, operator-approved cleanup.

Residuals, owned by the infra lane: the repository-managed Claude Code hooks
keep the `Task` and `TodoWrite` matchers, which never fire (0.11.5 uses `Agent`
and `Skill`), and add none of the 0.11.5 StopFailure or Subagent hooks; the
OpenCode plugin differs from the 0.11.5 template. `entire doctor` reports both
as "OUT OF DATE". Changing which hooks run is outside this amendment.

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
a canary on the pinned CLI proves a documented path. Native session capture stores
redacted prompt and transcript bodies in the private checkpoint repository;
that is permitted by the operator amendment and remains isolated from the
shared automatic corpus.

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
- Every shared or published context byte still comes from a canonical local
  system and carries a verifiable locator.

**Negative / risks**:

- Native semantic search and full explain increase the private egress and
  access-control surface; the live preflight must remain green before use.
- Provider indexing can return empty or delayed results even when local
  checkpoint explain works, so native search remains optional.
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
- CLI upgrades follow the 0.11.5 amendment below.

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
- checkpoint samples stay only in the approved private repository and contain
  no unredacted secrets;
- duplicate and retry paths create one context link;
- an Entire outage leaves canonical workflow outputs byte-for-byte unchanged;
- every hydrated item resolves and matches its canonical digest;
- Kimi/GLM and a native seat receive equivalent top results for the same query;
- a judged query set demonstrates that recall is materially better than the
  existing per-system lookups.

Any private-destination or body-leak failure disables the integration and
returns the project to the proven recovery-only posture.
