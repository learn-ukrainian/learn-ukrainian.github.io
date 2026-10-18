# Claude through the AGY worker route

The adapter accepts `claude-sonnet-5-5-high` and `claude-opus-5-5-high` for
normal implementation dispatches in verified dispatch worktrees. The display
strings `Claude Sonnet 5.5 (High)` and `Claude Opus 5.5 (High)` resolve to
those same slugs. Bare, low, medium and unknown Claude names are refused
before provider execution. Retired Thinking labels keep their retirement
refusal. A pinned Claude variant cannot use a substitute route or AGY's
Gemini default.

Existing model roles apply. Sonnet cannot implement security-sensitive work;
the adapter checks declared owned paths with the existing security-path
classifier and refuses an explicitly critical worker packet. Opus retains
its existing allowed roles. Dispatch and runner worktree checks, startup
hooks and the shell-output guard remain required.

Worker invocations use the established AGY worker permissions. Review
invocations retain their command/write denials and sandbox. This route adds
no reviewer candidate, ladder entry, role or formal-review eligibility.
Formal recorder consumption remains separate under #10924. Do not set
effort separately; the adapter emits the explicit high slug and leaves
effort unwired.

## Identity on the dispatch record

`model` remains the requested selector. `resolved_model`,
`resolved_model_known`, `resolved_model_source`, `resolved_model_family`
and `resolved_model_harness` describe the runtime observation. A matching
Claude observation has family `anthropic` and harness `agy`.
`identity_matches_request` records whether the trusted observation matches
this invocation's pin. It does not claim live qualification.

Only the CLI's normal structured `init` event on the runner-captured stdout
can provide identity. The adapter compares the reported `model` against the
resolved high slug. Response prose, tool turns, terminal-response model
labels, requested/configuration metadata and local model listings do not
provide identity. Missing, contradictory, late, repeated or mismatched
initialization cannot establish a match.

The runner carries the observation through the existing
`ParseResult.model_identity` and `Result.model_identity` path. Its in-memory
custody check rejects arbitrary dictionaries and modified observations.
The persisted `model_identity.provenance` includes:

- The `subprocess.stdout` origin and SHA-256 of the captured initialization
  event line, excluding its line terminator.
- The pinned CLI artifact SHA-256 and CLI version.
- A fresh invocation identifier, dispatch task ID and run nonce.
- The requested resolved pin and provider conversation identifier when supplied.

Dispatch validates the task, nonce and pin before persisting that evidence.
An absent or untrusted observation stays unknown, including on a nominally
successful worker result. Such a Claude worker cannot settle as `done`.
Cancellation and exceptions retain a trusted initialization already captured
from the same invocation. A prior invocation's observation cannot fill a gap.
These are provider-reported identities, not backend or hardware attestations.

The AGY endpoint has the `agy` accounting bucket. Missing allowance or usage
readings remain unknown. The route does not establish a shared Claude/GPT
quota pool. Offline fixtures prove propagation and refusals only.

## Driver qualification after merge and deployment

The implementation author runs no provider generation. The accountable driver
qualifies each of the two variants separately after merge and deployment.

1. Freeze the exact high variant, normal adapter/dispatch entrypoint,
   merged revision, bounded artifact task, semantic oracle, input/oracle
   digests and stop conditions before starting the provider. Keep held-out
   artifact inputs and answers outside the implementation author's context.
2. Run one useful bounded implementation dispatch in a verified worktree.
   Verify the authored artifact against the independent semantic oracle and
   retain its digest. Bind the artifact, dispatch task/run nonce, initialization
   digest, CLI artifact/version and merged revision to that same execution.
3. Verify the task record's trusted identity, requested pin and output guard.
   Include an independently chosen negative identity/guard case on the merged
   revision. Record blindness as declared/unenforced unless validated isolation
   evidence proves enforcement.
4. Record each variant as `QUALIFIED` or `UNAVAILABLE`, with its evidence and
   owner. Capture aggregate allowance readings and UTC timestamps where
   available; leave missing telemetry unknown.

Stop that variant on missing/unverifiable identity, a conflicting or mismatched
initialization, semantic failure, guard or permission failure, an unsupported
runtime or any substitution. Do not infer the other variant's availability or
silently retry through another transport. Model inventory, mock tests and
successful transport cannot qualify either variant.
