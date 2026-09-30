# Formal review attempt isolation

Issue: #9251. This boundary applies to `delegate.py dispatch --review-attempt`
for plan, lesson and lesson re-review attempts, using AGY, Codex or Claude.
Cursor is explicitly refused at admission and provisioning until it has a
proven boundary. Other unsupported harnesses remain refused.

**Candidate status: BLOCKED; do not merge or run real review attempts with this
candidate.** The filesystem closure is implemented, but shared host networking
allows an HTTP projection of another attempt's return to be read from inside
the sandbox. `test_seat_cannot_read_other_attempt_through_host_http_projection`
reproduces this using synthetic data. The test remains failing; it must not be
skipped or marked expected-failure. Provider traffic currently requires
networking, and a supported isolated provider-egress path has not been
established. Infra owns that blocking exposure and the provider-compatibility
proof. This candidate does not satisfy the issue's authorized-closure outcome.

The authorized manifest closure is the complete set of eligible, hashed file
pins in the manifest: `inputs.*`, plus lesson `module_digest` and
`upstream_lessons`. A lesson re-review additionally admits **exactly** its
`previous_attempt.review`, `previous_attempt.ledger` and `diff` pins. Existing
schema and pin-eligibility rules decide admission; this does not extend the
review contract. References inside an input do not authorize more reads.

Before adapter planning, the runner verifies the manifest against the attempt's
MCP manifest digest, verifies each input hash, and copies the closure into a
private input directory. Relative input paths are preserved, except the previous
receipt ledger, projected as `authorized/previous-ledger.jsonl`. Neither the
original shared state directory nor any neighboring receipt is exposed. The
rendered prompt already contains these inputs, including the re-review evidence.

The real harness process and its tool subprocesses run inside the existing
verified OS sandbox: Bubblewrap on Linux, sandbox-exec on macOS. Linux uses a
private PID namespace and procfs. The input directory is read-only. The writable
directory holds only this attempt's fresh home, configuration, transcript, temp
files and return. The installed executable and its narrow runtime dependencies
are readable; its native binary's parent directory is not granted. No original
checkout, Git objects, original home, prior session, receipt store or review
harness source is mounted. CLI authentication is staged narrowly into the fresh
home; sessions, project instructions, hooks and provider configuration are not
copied. Provider networking remains available. An unavailable sandbox or a failed
capability probe refuses launch; there is no filesystem-isolation fallback.

Runtime access and seat evidence are separate. A parent-owned sources process
runs outside the seat sandbox with the attempt's original receipt environment.
A byte-only stdio client inside the sandbox connects to that process through
one attempt-local Unix socket. The model can call sources tools, but cannot read
the sources implementation, current ledger, sidecar, or receipt directory. The
host worker captures the return and `scripts/review/record.py` records it outside
the seat boundary. Receipt and canonical return layouts are unchanged. The
runner parses the fresh transcript before cleaning up the boundary and sources
processes, including on refusal, timeout or failure. Formal attempts cannot resume
or trigger runner provider failover.

Claude uses an instruction-free home and `--bare --setting-sources ''` under
the OS boundary. Codex uses its fresh sources-only home and bypasses its nested
sandbox, which otherwise cancels stdio MCP calls. AGY uses a fresh home and
app-data directory under the same OS boundary. AGY's separate sealed code-review
`review_isolation` mode remains refused; formal content attempts use the
runner-owned manifest boundary, rather than enabling that unsupported mode.

## Verification and post-merge proof (AC-4)

After the blocking exposure is fixed, set `PROJECT_PYTHON` to the prescribed shared project interpreter. Run from the
merged dispatch checkout. These are scoped foreground tests; no provider/model
request is made by the host probes:

```bash
"$PROJECT_PYTHON" -m pytest tests/agent_runtime/test_attempt_boundary.py -q
LU_REVIEW_HOST_PROBES=1 "$PROJECT_PYTHON" -m pytest \
  tests/agent_runtime/test_attempt_boundary.py -q
```

The second command requires the actual installed AGY, Codex and Claude CLIs.
It fails if their real executables or dependencies cannot launch inside the
boundary. The test matrix exercises each harness and each attempt kind, denying
absolute reads, traversal, symlinks, Git history, prior homes and sessions;
allowing copied inputs, sources calls, receipt recording and the own return.
The normal CI run uses a native executable fixture for adapter startup only;
filesystem probes and sources calls use the real production boundary in both
modes. A separate reviewer should run these probes on the target host at the
merged SHA and retain the output. macOS capability remains host-specific proof,
not a claim established by Linux tests.

The curriculum consumer owns the clean #8425 A1 position-2 plan-review rerun.
Set `MANIFEST` to its current engine-produced plan manifest, `INPUT_ROOT` to
the checkout containing those pinned inputs, and `PROMPT` to an ignored local
prompt file. Use fresh review/attempt IDs; do not reuse any earlier attempt:

```bash
REVIEW_ID=plan-a1-position2-isolation-proof
ATTEMPT_ID=agy-clean-9251
"$PROJECT_PYTHON" -m scripts.review.prompts.render "$MANIFEST" \
  --repo-root "$INPUT_ROOT" --output "$PROMPT" \
  --review-id "$REVIEW_ID" --attempt-id "$ATTEMPT_ID"
"$PROJECT_PYTHON" scripts/delegate.py dispatch \
  --agent agy --model gemini-3.8-flash-high --mode read-only \
  --task-id review-9251-plan-proof --worktree \
  --prompt-file "$PROMPT" --review-attempt "$MANIFEST" \
  --review-id "$REVIEW_ID" --attempt-id "$ATTEMPT_ID"
"$PROJECT_PYTHON" scripts/delegate.py wait review-9251-plan-proof
```

After the current routing/capacity preflight, the consumer runs this once and
records the return through the existing review recorder. Infra independently
checks the transcript and receipt ledger: no forbidden read succeeds, the
sources calls have current-attempt receipts, and the return is attributable to
the same manifest and dispatched head. A provider completion or an APPROVE
string alone is insufficient. Material exposure blocks shipment; two review
rounds then escalate under the issue's stop policy. Infra owns boundary/host
proof failures; the curriculum consumer owns the semantic review rerun. Issue
closeout waits for both proofs, exact-head cross-family approval and landing.
