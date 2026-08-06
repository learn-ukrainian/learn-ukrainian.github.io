# Draft: sealed-review MCP access for excluded reviewer seats

**Status:** Draft for independent cross-family review and advisor/operator approval.
**Issue:** #6415

## Scope and non-goals

This is a design-only proposal. It makes no catalog, adapter, routing, or review-integrity change. In particular, it does not make AGY, DeepSeek, or K3 formally eligible. The current catalog intentionally keeps AGY and DeepSeek false because their transports cannot consume the parent-owned reader, and keeps `kimicc` false until an authenticated K3 canary completes (`scripts/config/model_catalog.yaml:103-115`, `scripts/config/model_catalog.yaml:141-177`).

The goal is not to give a reviewer a repository checkout. It is to let a reviewer ask the same sealed reader for the review bundle, then accept a verdict only under the existing exact-target and evidence checks. Provider authentication, reviewer quality, route capacity, and cross-family independence remain separate gates.

## Current security and integrity contract

The runner resolves base and head before materialising a temporary, no-live-Git snapshot outside the repository; it derives the changed set and patch, secret-scans them, and verifies the view again after review (`scripts/ai_agent_bridge/_review_worktree.py:2757-2778`, `scripts/ai_agent_bridge/_review_worktree.py:2806-2880`). The view contains only selected regular tracked context files, hard-linked read-only from that snapshot, and is checked for manifest or byte-identity drift (`scripts/ai_agent_bridge/_review_worktree.py:2616-2695`).

The sealed reader exposes five read/search operations, not shell or arbitrary filesystem capability: list files, read a file, read the required stream, read all required evidence, and search text (`scripts/agent_runtime/adapters/acpx.py:263-268`). A clean review requires the manifest, patch, and every changed regular file (`scripts/ai_agent_bridge/_review_worktree.py:125-141`). It cannot be inferred from a model claim: the validator checks returned chunks, offsets, UTF-8 bytes, full-file and chunk hashes, EOF, and complete interval coverage (`scripts/ai_agent_bridge/_review_worktree.py:649-758`). Missing trace or incomplete coverage fails closed (`scripts/ai_agent_bridge/_review_worktree.py:845-873`).

The parent alone creates the MCP configuration. It pins its interpreter, staged reader helper, and review view, writes owner-read-only, and supplies no environment entries (`scripts/ai_agent_bridge/_review_worktree.py:1108-1158`). Before any ACP adapter permits a tool, it independently requires an absolute private single-server config; expected interpreter and arguments; safe parent-owned roots; review-root markers; and the exact helper-source digest (`scripts/agent_runtime/adapters/acpx.py:308-389`). Its policy remains default-deny and admits only sealed-reader tool names (`scripts/agent_runtime/adapters/acpx.py:1203-1251`).

The authority stores a snapshot artifact and SHA-256 with repository, PR, head, and gate identity, then refuses publication when head, artifact binding, or artifact digest drifts (`scripts/fleet_comms/authority.py:717-796`, `scripts/fleet_comms/authority.py:2004-2028`). The runner validates the canonical response against the same base/head/patch and changed paths before publishing a `SealedVerdict` with the resolved model and family (`scripts/ai_agent_bridge/_review_pr.py:1241-1267`, `scripts/ai_agent_bridge/_review_pr.py:1351-1389`).

For sandboxed native engines, isolation evidence binds snapshot fingerprint, source state, patch, bundle, base/head, changed-path digest, invocation, prompt SHA-256, and prompt transport (`scripts/review/isolation.py:3251-3292`); a mismatching head or prompt digest is rejected (`scripts/review/isolation.py:3481-3509`). The ACP route already passes sealed prompt and parent-owned MCP config together (`scripts/ai_agent_bridge/_review_pr.py:1095-1149`).

| Property | Existing enforcement | Required preservation |
| --- | --- | --- |
| Exact-head binding | Authority seals snapshot artifact to repository, PR, gate, and head. | Bind one proxy session to `review_id`, artifact SHA-256, base/head, patch, bundle, and changed-path digest. Reject child-supplied target or snapshot handles. |
| Prompt binding | Isolation evidence records exact prompt SHA-256 and transport. | Parent computes the complete prompt once; the child cannot substitute, append, or resume it. |
| Least-source access | Temporary no-Git view contains only selected safe files and bundle. | Child gets no checkout, path, MCP config, shell, or ambient tools—only reader replies returned by proxy. |
| Fixed reader semantics | Config validation pins helper hash, interpreter, server, arguments, mode, and roots. | Proxy calls the existing reader contract; no reimplementation or broader tools. |
| Complete-evidence proof | Clean result requires authenticated chunk trace and full required-artifact coverage. | Preserve raw ordered request/result trace in normalized ACP shape and use the existing coverage validator. |
| Verdict binding | Canonical response is validated against sealed target before authority acceptance. | Forward the exact provider response; proxy never synthesizes verdicts or rewrites locations. |
| Isolation provenance | Parent-owned receipt/capabilities/sandbox are required where supported. | Add a proxy receipt and one-shot nonce only as supplemental provenance; never as a replacement. |

## Failure modes before mechanism selection

The following are integrity failures, not warnings:

1. A child can name a path, config, server, snapshot, or tool, allowing a live checkout or ambient MCP server. Use only parent-stored opaque session state and a fixed allowlist.
2. A proxy starts a second reader implementation or weakens chunk fields, making successful-looking evidence source-ambiguous. Retain helper digest, hashes, offsets, EOF, and existing coverage validation.
3. A wrapper turns tool activity into prose or omits raw calls. A clean verdict then lacks complete-evidence proof and is rejected.
4. Ambient instructions, filesystem, shell, hooks, session resume, or nested agents can alter reviewer/source scope. Sessions must be fresh, read-only, tool-deny by default, and project-instruction isolated.
5. A prompt, head, bundle, model identity, or nonce changes after sealing. Expire and reject; never retry against a new head.
6. A text-only transport is called equivalent merely because the source bytes were put in its prompt. Delivery proof is not the current tool-trace proof.

## AGY / Gemini: recommended parent-held sealed-reader proxy

Implement a parent-owned ACP bridge capability, `sealed_review_proxy.v1`, rather than exposing MCP configuration or snapshot to AGY. The review parent provisions the existing sealed view and reader, seals authority state, then creates one opaque single-use proxy session. The AGY wrapper sees only descriptors for the five existing reader operations; each ACP request returns to the parent. The parent validates session and fixed operation schema, invokes the staged reader, and returns that result unchanged as the tool result.

```text
parent runner
  -> seal {review_id, head, snapshot/bundle/patch, prompt_sha, nonce}
  -> start existing sealed reader + proxy
  -> AGY ACP child: proxy tools only; no workspace tools
  -> proxy: validate nonce + fixed method/args; call reader; append raw trace
  -> existing response + evidence validators -> authority accepts or rejects
```

The child receives neither filesystem path, reader-config contents, authority credentials, raw snapshot artifact, nor general ACP forwarding. The proxy is an adapter boundary, not an evidence source: replies preserve reader path, offsets, byte counts, hashes, chunks, and EOF so `verify_clean_review_evidence_reads` validates unchanged. A proxy receipt binds proxy protocol/version, nonce hash, parent config/helper identity, trace digest, and response digest to the existing review identity; it stores no credentials or duplicate source bytes.

The current AGY runbook correctly remains fail-closed until project instructions, ambient MCP, hooks, nested reviewers, transport registration, and a real non-Google-family smoke review are proven (`docs/runbooks/agy-formal-cf-isolation.md:1-45`). The proxy solves only the source-blind MCP gap; it does not prove those other isolation properties or authorize a catalog flip.

## DeepSeek: retain the bar

### Option A — minimal ACP tool shim (recommended if supported)

Provide the same parent-held proxy through a Hermes/ACP adapter that supports structured tool calls and returns a complete normalized trace. It has the AGY preservation requirements plus an exact concrete model/family identity. Only then can it become formal; otherwise `deepseek.formal_review_eligible` stays false.

### Option B — complete inline bundle (not equivalent; explicit policy trade-off)

The parent can serialize every required artifact into one inert, hash-addressed JSON bundle. An existing helper includes per-file digests, byte counts, complete paths, total-content digest, and size limits (`scripts/ai_agent_bridge/_review_worktree.py:160-217`). It limits source material to the review bundle, but cannot establish that a text-only child called a reader or consumed every byte: it proves only that the parent delivered complete evidence in the prompt.

An inline path must not reuse `hash_bound_byte_chunks` or silently satisfy the current clean-review rule. It needs a separately approved evidence mode such as `parent_bound_inline_complete`, a parent prompt-delivery receipt, and explicit documentation that **observed reader-trace coverage** becomes **parent-proven complete prompt delivery**. Until an operator/advisor explicitly approves that semantic change and acceptance policy changes deliberately, text-only DeepSeek is advisory-only.

### Option C — no formal DeepSeek seat

If the harness cannot provide structured traceable tool calls and isolation, the honest outcome is no formal DeepSeek reviewer. The family remains useful for advisory work; the formal gate retains its meaning.

## K3 exact-head sealed-MCP canary

### What one canary proves

One canary is a real authenticated `kimi-code/k3` run over a dedicated non-sensitive canary PR at fixed base/head. It proves that the resolved K3 identity, through approved sealed transport, received only the parent-held reader; made authenticated required-evidence reads; returned one canonical `code-review-findings.v1` verdict; and that verdict passed normal response, finding-evidence, complete-coverage, and authority exact-head validation. The PR contains a deterministic independently checked review condition so the canary validates a meaningful verdict, not transport or JSON shape.

It does not prove general quality, capacity, future credential health, or broader Kimi isolation. Current code still hard-refuses `engine="kimi"` because project instructions, MCP, hooks, and nested-reviewer suppression are unproven (`scripts/review/isolation.py:3542-3548`); the Kimi runbook requires an isolation matrix, positive/negative launch tests, sealed registration, and a real smoke review before eligibility (`docs/runbooks/kimi-formal-cf-isolation.md:1-42`). The canary is necessary evidence, never a substitute for those gates.

### Procedure

1. Parent resolves and seals exact base/head and snapshot through the ordinary authority path.
2. Parent creates a fresh one-shot K3 session with non-secret identity attestation: requested/resolved model ID, provider/harness, CLI version/build digest, credential-session key identifier or rotation epoch, and authentication success.
3. Parent gives K3 only sealed proxy/reader operations and the sealed prompt. K3 reads the full required stream; no clean result is accepted without normalized hash-verified coverage.
4. Parent runs unmodified canonical response and finding validators, then authority accepts against the same head. Missing trace, identity mismatch, response/evidence failure, timeout, or cancellation retains a failed receipt and leaves K3 ineligible.

### Attestation artifact, flip, and re-run policy

Propose body-free `sealed-review-k3-canary.v1` in Authority ArtifactStore with `formal-review-canary` retention. Source remains in the sealed snapshot artifact; raw provider response remains in ordinary sealed-verdict/attempt artifacts. The receipt includes:

- review ID, repository, PR, base/head, gate, snapshot artifact ID/SHA-256, source fingerprint/state, patch, bundle, changed-path digest;
- requested/resolved K3 model IDs, family, participant, adapter/harness, CLI/build digest, non-secret auth-session/rotation attestation, and timestamp;
- reader/proxy version, validated config/helper identity, prompt SHA-256/transport, nonce hash, and tool-policy digest; and
- required-artifact count/digests, trace SHA-256, coverage receipt, canonical response SHA-256, finding-validation and authority outcomes, redaction version, and failure field—never credentials or duplicate source body.

This matches existing authority artifacts: formal jobs retain snapshot and sealed-verdict artifact IDs (`scripts/fleet_comms/formal_review_jobs.py:79-112`) and authority verifies stored snapshot before verdict acceptance (`scripts/fleet_comms/authority.py:1261-1299`).

Only an independently cross-family-reviewed K3 enablement PR may flip `kimicc.formal_review_eligible`. It quotes immutable receipt ID and SHA-256, states full receipt verdict, includes Kimi isolation proof/negative tests, and leaves the exclusion in place for any failed or incomplete run. Console success and fixtures never flip eligibility.

Re-run before retaining eligibility after credential rotation/re-authentication; resolved-model alias change; K3 CLI or adapter change; proxy/reader/config/tool-policy change; sandbox/isolation-policy change; or response/evidence-validator change. A normal PR head change does not invalidate the capability canary—each review has its own exact-head seal—but a failed availability probe is never a successful canary.

## Mutation-checked test strategy

| Mechanism | Positive proof | Mutations that must fail closed |
| --- | --- | --- |
| Shared proxy | Fixture child reads all required artifacts; existing coverage and response validators accept. | Child path/config/server/tool; extra MCP/tool; traversal/symlink; altered helper/config/interpreter/mode; ambient tool/instruction; session replay; proxy-rewritten response/trace. |
| Reader trace | Exact chunks, offsets, hashes, EOF, and coverage survive proxy. | Missing artifact/chunk; changed offset/length/content/hash/EOF/status/order; absent raw tool call; prose substituted for result. |
| Target/prompt | Parent seals one snapshot/prompt only. | Change head/base, snapshot, patch, bundle, changed paths, prompt byte/digest/transport, review ID, model identity, or response. |
| AGY | Calls only proxy; no source path or ambient MCP. | Enable workspace/shell/hooks/nested agents/project instructions; direct config; missing receipt; fail AGY isolation matrix. |
| DeepSeek shim | Structured child emits complete normalized trace. | Text-only/no trace, unknown model identity, direct source access, or missing isolation receipt. |
| DeepSeek inline | Complete inert bundle and delivery digest are produced. | Current formal path rejects it pending explicit policy approval; test truncation, reordered/missing file, digest mismatch, size breach, prompt drift. |
| K3 | Authenticated exact K3 completes canonical path on pinned head. | Missing/expired auth attestation, model mismatch, altered CLI/proxy/helper/config, incomplete trace, bad finding, head drift, timeout, receipt hash mismatch. |

The live K3 canary is separately gated integration evidence, never a fixture promoted as authentication proof. Failed canaries and non-secret incident evidence remain private and do not qualify the catalog.

## Approval and implementation sequence

1. Obtain independent cross-family review and an explicit advisor/operator decision on the proxy and the DeepSeek inline trade-off.
2. Implement the shared proxy with this mutation suite while all excluded seats remain ineligible.
3. Prove separate AGY/K3 isolation matrices and run authenticated exact-head canaries.
4. Submit narrow cross-family-reviewed enablement PRs quoting immutable receipts before changing any `formal_review_eligible` flag.
