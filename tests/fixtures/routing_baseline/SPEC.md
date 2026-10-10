# Routing baseline v1 (#9302), approved Cursor revision (#9951)

## Claude weekly cap help (#10355)

`tests/review/fixtures/claude-cap-10355.json` records the launcher help lines
for the operator Claude cap policy: every Claude launch stops at 99% weekly
used, Opus is always blocked (explicit Opus is refused, a defaulted Opus driver
switches to `claude-sonnet-5-5`), and `LU_CLAUDE_CAP_OVERRIDE=1` bypasses only
the 99% stop. Both configurations were captured with the documented
`capture.py` command against this checkout, using the test module's scoped
`CAPTURE_RUNNER` cache, and compared with every approved surface. Only the
`launchers` `stdout` of the 14 `help` rows differs, identically in both
configurations: rows 4 and 9 (Claude providers) gain the cap environment
paragraph, and every help row gains exit code 7. The fixture is applied after
the other overlays as exact-once literal insertions. Its digest is pinned in
`tests/review/test_model_catalog.py`, and a scope test checks that no other row,
field or surface changes. Historical baselines, inputs, the occurrence ledger,
`SHA256SUMS` and `capture.py` stay byte-identical. Any other difference blocks
regeneration.

## Explicit AGY review risk (#10262)

The fresh capture changes only the refusal field in 32 dispatch rows for AGY
and its Gemini alias when a review attempt omits `--review-risk`. Both CLI
configurations now capture `REVIEW_ROUTE_REFUSED` with the explicit-risk
requirement before attempting to read the review target, replacing the former
`REVIEW_TARGET_UNRESOLVED` refusal. All other dispatch fields and baseline
surfaces, input matrices, occurrence ledgers and approved overlays remain
unchanged. The checksum manifests and independent literal digest pins bind
the refreshed baselines and this specification.

## Worker resource-policy overlay (#10263)

The 2026-10-09 resource-policy order is represented by the hash-pinned
`routing-10263.json.gz` overlay, applied after the review-capacity and Gemini
overlays for both CLI configurations. It replaces only the `fallbacks`
surface. The decompressed comparison removes `post_2026_06_15_hard_rule`,
adds `worker_resource_policy`, and removes the substitution whose
`currently_uses` is `linear_pipeline.invoke_writer(writer='claude-tools')`.
All remaining fields and substitution rows are identical. The replacement
states the Sol default, native Claude eligibility and language-free overflow
policy; it introduces no writer recommendation.

The historical compressed baselines, input matrices, occurrence census,
capture driver and checksum manifests remain byte-identical. Independent
literal digests in `tests/review/test_model_catalog.py` pin this overlay and
the updated specification; its scope test checks the exact decompressed
difference against both historical fallback surfaces. Fresh full captures
must still reproduce every other approved surface unchanged.

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

The executable expectations include the approved #9951 Cursor family change.
The original baseline remains in Git history. Its source-contract and
occurrence census still use the pinned SHA above; this revision does not
regenerate that historical evidence or change the input matrix.

The #9960 regeneration compared every captured surface before accepting the
new bytes. Only two Cursor catalog fields (`unknown_auto_family_resolution`
and `note`) and reviewer rows 21, 205, 389, 573, 757, 941, 1125 and 1309 changed.
Those eight rows are the `cursor:auto` author across four risks and two review
profiles: native Grok becomes eligible, and every Cursor transport stays
excluded. All other reviewer receipts, capacity, dispatch, adapter, launcher,
registry, fallback and source-contract surfaces are unchanged. `inputs.json`
and `occurrences.json.gz` remain byte-identical.

Reproduce the current executable expectations from the #9960 fix checkout
using the same command. The capture loads the runtime source from that checkout
alongside its scripts, so an older installed package cannot supply the family
normalizer. Compare all three hashes, not just the catalog or selected reviewer.
Future regeneration must explain every difference against the approved outcome;
an unexplained difference fails the capture comparison.

## Haiku 5.5 adoption (#9996)

The executable revision adds eight author cases for `claude-haiku-5-5`: code
and infra across low, medium, high and critical risk. This is author-family
resolution evidence; Haiku never becomes a reviewer candidate. All 1,472
pre-existing reviewer cases remain byte-equivalent when joined by input identity.
Current Cursor Auto indices are 22, 207, 392, 577, 762, 947, 1132 and 1317;
their verdicts and traces are unchanged.

The catalog changes are exactly the new Haiku model metadata and the
`routine_mechanical` role added to Sonnet for the task fallback. The additive
mechanical seat/task roles are excluded by the legacy catalog projection and
included by the PR 2 role-holder and role-resolution surfaces.
Fallback configuration adds one routine mechanical substitution description.
Registry, capacity, dispatch, adapters, launchers and source-contract surfaces
remain identical. The occurrence ledger remains byte-identical and pinned to
its historical source census; it does not claim to census the new model. The
reviewer input matrix changes only by those eight author cases. The role matrix
adds the three approved mechanical roles; approval-contract rows add Haiku as
an author, without granting it review or designated-approval authority. `SHA256SUMS` binds the
new executable fixture and inputs, and the unchanged occurrence ledger.

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


## PR 2 strengthening (first commit, untouched production code)

Executable source: `0d98123470b5a6870512571d01590f3e3210b268` (`origin/main`
at intake). The capture driver runs outside a detached checkout of that SHA.
The historical occurrence and source-hash census retains its original SHA.
Resolved holder evidence now includes every seat, role and transport wire id.
Role rows project every reviewer input onto the role API and deduplicate equal
projections (author identity and the review profile are not role API inputs).
The separate catalog digest is omitted because it binds authored catalog bytes;
all resolved candidate fields, order, exclusions and health provenance are kept.
Dispatch rows include every explicit substitution source pin and review-attempt
immutability cases at both budget states.

`no-cli/` is an independent configuration with its own expected bytes and test.
Its closed PATH contains only the three allowlisted system tools and one pinned
`npx` stub. That stub accepts exactly `npx @anthropic-ai/claude-code@latest
--version`, reports the fixed Claude version, and refuses everything else.
HOME is empty. Missing Grok and Cursor refusals, Claude fallback argv and Cursor
model-probe warnings are captured unchanged. No provider is invoked.

The current-tree operator contract is read as bytes and its present two-holder
author/vote truth table is executed by the capture, including absent approval,
dissent and self-approval. There is no production designated-approval evaluator
at this base: this is labeled contract evaluation, not engine proof. Generic
additional-family approval execution stays in PR 5.

`test_frozen_artifacts_are_pinned_independently_of_manifest` contains literal
SHA-256 digests for every baseline file, including the capture and specification.
Those literals never come from the fixture's SHA256SUMS. After this commit no
baseline byte may change; compare the final head against the first commit with
`git diff --exit-code <first-commit> -- tests/fixtures/routing_baseline`.


## PR 2 merge revision (#9302, round b)

The approved PR 2 head `45253e51eb4ca37a206692a2f09d3d2ddfc0776e`
is merged with `2c0b22b6961ea676a48d3fc7b238b405a643f7be` from main.
This separately ordered revision regenerates both configurations using the
capture procedure above against the merged checkout; add `--configuration
no-cli` for the independent no-CLI artifact. The independent digest pins in
`tests/review/test_model_catalog.py` bind this revision.

Against that approved PR 2 head, both configurations change only the Cursor
catalog `unknown_auto_family_resolution` and `note` fields and reviewer rows
21, 205, 389, 573, 757, 941, 1125 and 1309 (zero-based). Each change comes from
`9c233c5eaa` (#9960): Cursor Auto authors use the Cursor family, native Grok
is eligible, and Cursor transports remain excluded. All 672 role rows,
992 dispatch rows, 112 adapter rows, 42 capacity rows and 70 launcher rows,
resolved holders, approval, registry, fallbacks and source contracts remain
unchanged. Inputs and occurrence artifacts remain byte-identical.
`aea2281aa9` (#9972) preserves forced-lane quota/health diagnostics on task
records without changing the captured routing surface, so it changes no rows.
Any difference beyond this attribution blocks regeneration.

A subsequent merge includes `04de11ad89ba25fed59e37be34256e1e518538b9`
(#9968), which anchors the GitHub client cache to its module checkout.
Fresh captures on that final merge must reproduce both configurations exactly;
this cache fix has no attributed routing-row changes.


## Haiku merge revision (#9996, round b)

The approved Haiku head `ee15773294e5b8964c2979b229bf95d7edf033ef` is
merged with `d286629c33e6ddd787802237958f77732fe8706d` from main, including
the PR 2 role-based consumers (#9971). Both configurations are regenerated
against that merged checkout with the procedure above; use `--configuration
no-cli` for the independent no-CLI artifact. Independent digest pins in
`tests/review/test_model_catalog.py` bind this ordered revision.

Comparison with main joins rows by complete input identity, preserving repeated
inputs. Both configurations have the same attribution:

| Surface | Existing rows unchanged | Added rows | Attribution |
| --- | ---: | ---: | --- |
| Reviewer | 1,472 | 8 | Haiku author, code/infra across all four risks |
| Role resolution | 672 | 168 | 56 cases each for routine mechanical, mechanical classification and read-only recon |
| Approval contract | 378 | 9 | Haiku author across the existing two-holder vote matrix |
| Dispatch | 992 | 0 | Identical |
| Adapters | 112 | 0 | Identical |
| Capacity | 42 | 0 | Identical |
| Launchers | 70 | 0 | Identical |

No existing row changes or disappears. Catalog differences are exactly the
Haiku model and Sonnet's routine mechanical eligibility. Holder evidence adds
only the mechanical worker seat and its three approved task roles. Fallbacks
add only the routine mechanical substitution description. Registry, source
contracts and the historical occurrence bytes are unchanged. Main's role-based
consumers resolve Haiku's existing mechanical seat/roles. Mechanical role
constants live in the catalog module so standalone catalog consumers retain
their runtime-independent validation and resolution; admission imports those
same constants. This import fix changes no captured result. Any other difference
blocks regeneration.


## Grok streaming-messages-json argv (#10005, round d)

Both configurations were regenerated with `capture.py` against this checkout.
Use `--configuration no-cli` for the independent artifact. Independent digest
pins in `tests/review/test_model_catalog.py` bind this ordered revision.

The host-CLI baseline changes only the `adapters` surface. Four successful
non-schema rows change the `--output-format` value from `json` to
`streaming-messages-json`:

| Row | Agent | Mode | Isolation |
| --- | --- | --- | --- |
| 28 | `grok` | read-only | false |
| 30 | `grok` | workspace-write | false |
| 32 | `grok-build` | read-only | false |
| 34 | `grok-build` | workspace-write | false |

Those rows have no `--json-schema` flag. The value is argv index 4 on the
read-only rows and index 6 on the workspace-write rows; every other argv token
on those rows is unchanged. Isolation rows 29, 31, 33 and 35 still refuse
before argv (`review_parent_owned_roots_missing`). Every other adapter row is
unchanged. Reviewer, role, approval, capacity, dispatch, launcher, catalog,
registry, fallback, routing-holder and source-contract surfaces are identical.
Inputs and the occurrence ledger stay byte-identical.

The no-CLI configuration is byte-identical, including its baseline. Its Grok
rows still refuse with the missing-CLI PATH error and never reach argv.
Any other difference blocks regeneration.

## Gemini epic driver (#10146)

Both configurations were captured with `capture.py` against this checkout, and
each surface was compared with the frozen baseline plus the
`routing-10016.json.gz` reviewer overlay. Only the `launchers` and `catalog`
surfaces differ; the fixture replaces exactly those two surfaces and keeps its
original `reviewer` surface, so the overlay comparison is unchanged. Inputs and
the occurrence ledger stay byte-identical in both configurations, and the
no-CLI configuration shows the same two-surface difference.

The 2026-10-08 approval admits Gemini as an epic driver on two certified pins:

| Row | Provider | Mode | Variant | Change |
| --- | --- | --- | --- | --- |
| 25 | `gemini` | driver | default | Exit 4 refusal becomes exit 0 with model `gemini-3.1-pro-high` |
| 26 | `gemini` | driver | environment | Still exit 4; the message names `claude-opus-5-5` as not certified for the gemini driver |
| 27 | `gemini` | driver | cli | Still exit 4; the message names `grok-4.7` as not certified for the gemini driver |

Every `help` row (4, 9, 14, 19, 24, 29, 34, 39, 44, 49, 54, 59, 64 and 69)
gains the Gemini driver and interactive model defaults in the `--model`
description. Row 29 also loses the former Gemini refusal text and shows the
shared driver mode and driver examples. Retired-pin row 28 is unchanged. The
catalog changes only `orchestrator_seats.agy.note`. Reviewer, role, approval,
capacity, dispatch, adapter, registry, fallback, routing-holder and
source-contract surfaces are identical. Any other difference blocks
regeneration.


## Cursor wire pin and allowlist (#10205)

Both configurations were regenerated with the documented `capture.py` command
against this checkout, using the test module's scoped `CAPTURE_RUNNER` cache.
The existing `routing-10016.json.gz` reviewer overlay was compared separately;
the frozen reviewer surface remains unchanged. No input or occurrence bytes
changed, and `capture.py` remains byte-pinned.

The host-CLI adapter rows 56–59 change only the Cursor `--model` argument and
its requested-model telemetry from `grok-4.7` to `grok-4.7-high`. No-CLI adapter
rows are unchanged because binary resolution fails before invocation.

In both configurations, dispatch rows 2, 6, 10, 14, 22, 26, 30, 456, 458,
460, 462, 464, 466, 468, 470, 472, 474, 480, 482, 484, 486, 488, 490,
492, 494, 500, 504, 508, 516, 520 and 524 now normalize bare Grok in
worker argv or refuse models outside the approved Cursor allowlist. Catalog
identities remain unchanged. With a native Claude CLI, Claude fallback models
receive `CURSOR_CLAUDE_REFUSED`; without it, unapproved fallback models receive
`CURSOR_MODEL_NOT_APPROVED`. No-CLI probe diagnostics for unapproved models
also disappear because adapter admission now precedes binary resolution.

Launcher rows 42 and 47 normalize an explicit bare Grok selection to the high
wire pin. Rows 41 and 46 preserve exit 4 and add the correct typed Claude
refusal with the native CLI, or the allowlist refusal without it. All other
launchers, dispatch rows, catalog, registry, capacity, role, approval, fallback,
holder and source-contract surfaces remain identical. Any other difference
blocks regeneration.


## Native Grok driver binding overlay (#10267)

`routing-10267.json.gz` is an additive, independently hash-pinned overlay;
the historical captures, input matrices, occurrence census, capture script and
manifests retain their bytes. Reproduce both configurations with the existing
capture runner against this branch. Compare all surfaces before extracting the
changed surfaces into `configurations.host-cli` and `configurations.no-cli`.
Gzip uses modification time zero and JSON uses sorted keys.

The host-CLI adapter surface changes exactly four rows (28, 30, 32 and 34):
non-isolated read-only and workspace-write invocations of `grok` and
`grok-build`. Only `value.env_unsets` changes, from empty to the sorted list
`LU_GROK_DRIVER_SESSION_ID`, `LU_GROK_PROJECT_PYTHON`, `LU_GROK_SOURCE_ROOT`.
These worker processes must not inherit a driver's native process binding.
All other adapter fields and rows, including acpx, retain their values.
The no-CLI adapter surface is unchanged: native Grok construction refuses
before it can produce a plan.

Both configurations change only launcher row 39's stdout (Grok driver help):
the usage line no longer advertises positional prompts, and a native driver
section documents the approved checkout pin, flag allowlist and context
environment refusal. The rest of that row and all other launcher rows retain
their values. Every remaining captured surface, both input matrices and the
occurrence bytes are unchanged relative to the existing approved overlays.
The scope test constructs these exact differences independently of a fresh
capture; unexplained differences still fail. This fixture is regression
evidence, not independent implementation approval.
