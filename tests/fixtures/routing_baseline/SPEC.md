# Routing baseline v1 (#9302)

The pinned source-contract/occurrence census is
`dae3d752426d6c11c5dc82260ec07ae8164e7730`. The host-independent executable
capture was reproduced from `019dcde544fe93f5aecf6d0deb6b2fd7352f339b`, the
original fixture commit before any production migration. Its capture driver
imports that checkout's code in a fresh process. `SHA256SUMS` binds the compressed
JSON output, the complete input matrix, and the occurrence ledger. Gzip has a
zero modification time; JSON uses sorted object keys and retains array order.

Reproduce from a scratch clone checked out at `019dcde544`, using the shared
project interpreter and the corrected `capture.py` (outside the clone):

```text
<project-python> capture.py --source-root <untouched-base-checkout> \
  --project-python <project-python> --output <scratch-output>
```

Compare all three hashes, not just the catalog or selected reviewer. Never
replace this fixture with outputs from migrated code. Run the same driver
against a changed checkout to compare behavior, without updating expected data.

## Inputs and captured evidence

- Reviewer: every catalog identity and alias plus ambiguous harness identities,
  all four risks and code/infra profiles; explicit families and conflicts;
  subject seat/family exclusions; pins with and without pressure justification;
  capability, isolation, egress, suitability, complete authorship and advisory
  cases. Full resolution dataclasses include ordered traces, reasons, scores,
  quorum, health, policy version and substitutions. Invalid flat health values
  remain exceptions, rather than being coerced into healthy values.
- Health: absent snapshot and key, unknown, unavailable, stale, healthy,
  degraded, degraded telemetry, near-cap and unhealthy; nested contradictory
  health and stale snapshots. Capacity uses the real credit reader over
  synthetic records, with a fixed clock and an empty usage directory. These
  inputs contain no real account or credit evidence.
- Dispatch: every runtime registry entry, omitted/default/alias/unknown pins,
  cool/near-cap snapshots, the real dispatch parser and admission/route helpers,
  final worker agent/model argv and substitution records (#8855). Unsupported
  registry agents retain argparse refusals. No worker process is started.
- Adapters: every registered adapter, both read-only and workspace-write,
  default model, high effort, with/without review isolation; complete invocation
  plans or construction refusals. Real binary lookup and version gates run
  against staged stub CLIs. Only version probes execute; every other stub
  invocation fails. Unsupported isolation remains a construction refusal.
  These fixed discovery inputs are not production health evidence.
- Launchers: every public provider, interactive/driver defaults, environment
  overrides, CLI precedence, retired pins and help; real shell parse,
  normalization and certification helpers. Lease acquisition and provider
  execution are never called.
- Catalog: the entire validated legacy catalog, including ladders, execution
  routing, escalation, orchestrator seats, formal defaults, endpoint membership,
  risk eligibility and model substitution mappings; complete registry and
  fallback configuration.
- Rules, profiles and approval: byte hashes and sizes of canonical rules,
  serving/hash helpers, budget tests, installed-profile sources and launcher
  adapters. Designated approval remains a source contract at this base, not an
  executable approval engine. The author truth table, disagreement and
  self-approval requirements are bound to the operator contract's exact bytes;
  generic additional-family approval execution belongs to PR 5.

## Isolation and normalization

The environment is replaced with a capture-local PATH, HOME, TMPDIR, logs and
task roots, fixed locale/timezone and child hash seed. PATH contains only
allowlisted system `bash`, `git` and `cat`, plus the stub CLIs enumerated in
`capture.py`; system PATH is never appended. Claude reports `2.1.289` and AGY
reports `1.2.10` as fixed version-probe inputs. Other stubs report `1.0.0`.
The environment contains no credentials or live provider config. Fresh-capture
tests vary ambient CLI presence, HOME, provider/launcher overrides and timezone.
The capacity clock is `2026-10-06T12:00:00+00:00`; adapter UUID generation uses
`00000000-0000-0000-0000-000000000001` as an input, not a post-capture rewrite.
Only the explicitly supplied source checkout and capture scratch root become
`<SOURCE_ROOT>` and `<CAPTURE_ROOT>`. The exact `InvocationPlan.output_file`
paths (also in argv/metadata) become `<ADAPTER_OUTPUT_row>`; this enumerates
random temporary capture filenames without changing any invocation flags.
The exact AGY `AGY_RUNTIME_LOG_FILE` capture path becomes `<ADAPTER_LOG_row>`
wherever that same path occurs; its PID suffix is not routing evidence.
The exact Grok `metadata.write_guard_agent_file` path becomes
`<ADAPTER_WRITE_GUARD_row>` wherever it occurs. Grok's URL-quoted scratch cwd
becomes `<CAPTURE_ROOT_URLENCODED>` in its session-directory component. These
enumerated path rewrites retain all invocation flags and refusal evidence.
The scratch checkout must include `.mcp` alongside scripts, rules and tests.
No model, family, order, health, reason,
policy value, exit status or exception is normalized. Source-contract paths are
repo-relative. Fixture captures are not operational review/telemetry receipts.

## Occurrence denominator

The ledger searches all tracked text in the pinned Git objects, including sparse
paths, for every concrete catalog identity and alias and single-seat Opus/Sol
prose references. Each lexical occurrence has path, line, column, literal,
context digest, disposition, purpose and owner. Candidate live selection and
current-instruction rows require source review during the relevant migration
stage; no broad path exception exempts them from final census closeout. Test,
deployed and frozen-history rows carry occurrence-bound preservation purposes.
This fixture freezes the migration denominator; it does not certify that every
candidate is already migrated or a normative authority rule.

Stop on any unexplained output difference. The baseline is mechanism and
regression evidence, not a real-route qualification or independent PR approval.
