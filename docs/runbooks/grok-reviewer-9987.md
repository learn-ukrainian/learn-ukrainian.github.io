# Native Grok reviewer permission incompatibility (#9987)

The reviewer retains `auto` plus unconditional `Bash`, `Write` and `Edit`
denies. It never enables `--always-approve`. This is a stop disposition,
not delivery of literal shell inspection: native Bash denial also blocks the
literal commands recognized by the guard. The round-a stop diagnostics and
`permission_cancelled` classification remain intact. The accountable driver,
`claude-infra`, owns the unresolved review-completion outcome and escalation.

## Reproduce without a paid model

Run from the repository import root in the dispatch worktree, with the
prescribed project interpreter and the dispatch-managed `TMPDIR`:

```bash
export LU_PROBE_INTERPRETER=<absolute-project-interpreter>
"$LU_PROBE_INTERPRETER" -m tests.grok_native_permission_probe --matrix
```

For an individual case:

```bash
"$LU_PROBE_INTERPRETER" -m tests.grok_native_permission_probe \
  --mode dontAsk --action literal
"$LU_PROBE_INTERPRETER" -m tests.grok_native_permission_probe \
  --mode bypassPermissions --hook crashing --action write
"$LU_PROBE_INTERPRETER" -m tests.grok_native_permission_probe \
  --mode auto --deny-bash --hook removed --action write
```

The committed harness starts a loopback scripted Chat Completions provider,
uses a separate `GROK_HOME`, disables Claude compatibility and telemetry, and
passes no real credentials or inherited provider configuration. It creates a
scratch Git checkout, stages a public fixture and asks the **native CLI** to
read it, execute the guard's literal Git status command, or execute a scratch-only
`awk` write. A second scripted response completes only after the provider
receives the tool result. Provider requests and native session bodies are not
printed or retained. Scratch directories and the provider are removed on exit.
No OS sandbox is supplied: the test exercises the native permission backstop.

`read_fixture_seen` and `literal_fixture_seen` measure returned fixture output,
independently of assistant narration. `marker_written` proves actual shell
execution. `hook_entered` proves that the deliberately crashing hook started.
`typed_refusal_seen` measures the model-visible guard refusal, and
`permission_denied_seen` measures native or hook refusal. An argument parsing
failure, absent provider request, or missing terminal envelope fails the
harness; CLI exit zero alone proves nothing. The matrix exit code reports that
probes ran, not that any mode satisfies the required outcome.

## Observed evidence

At `2026-10-07T19:56:07Z`, the installed CLI identified itself as
`grok 1.0.46 (2765805b9442) [stable]`. The 29-case matrix produced:

| Native mode/configuration | Tracked read, working hook | Literal Git command, working hook | Disallowed write |
| --- | --- | --- | --- |
| `default` + explicit allows | `end_turn`, fixture read | `cancelled`, no tool result | Working hook: typed refusal, `end_turn`, no marker |
| `acceptEdits` + explicit allows | `end_turn`, fixture read | `cancelled`, no tool result | Working hook: typed refusal, `end_turn`, no marker |
| `auto` + explicit allows | `end_turn`, fixture read | `cancelled`, no tool result | Working hook: typed refusal, `end_turn`, no marker |
| `dontAsk` + explicit allows | `end_turn`, fixture read | `cancelled`, no tool result | Working hook: typed refusal, `end_turn`, no marker; removed/crashing/missing-interpreter hook: `cancelled`, no tool result, no marker |
| `plan` + explicit allows | `end_turn`, fixture read | `cancelled`, no tool result | Working hook: typed refusal, `end_turn`, no marker |
| `bypassPermissions` + explicit allows | `end_turn`, fixture read | `end_turn`, Git fixture returned | Working hook: typed refusal, `end_turn`, no marker; removed/crashing/missing-interpreter hook: **marker written**, `end_turn` |
| Retained `auto` + blanket Bash deny | `end_turn`, fixture read | Native denial, `end_turn`, no Git execution | Removed/crashing/missing-interpreter hook: native denial, `end_turn`, no marker |

Every matrix invocation supplied explicit `Read`, `Grep` and literal `Bash(...)`
allows, even the blanket-deny cases; the blanket Bash deny still won. The
retained adapter omits those ineffective shell allows. The `auto` classifier
may make additional requests to the scripted provider; these probes do not
qualify real model safety-classifier behavior. The blanket native deny proofs
do not depend on a classifier verdict.

Required proofs (a)–(c) cannot all hold in any tested mode. Reads complete;
non-bypass modes cancel the admitted literal Git call. Bypass completes reads
and literal commands and returns a working hook's refusal, but hook loss allows
the disallowed write. A blanket Bash deny supplies the independent backstop
and model-visible native refusal but also prevents literal commands.

The [upstream permission guide](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/22-permissions-and-safety.md)
specifies deny precedence over allow, built-in read handling under `dontAsk`,
and that explicit allow rules do not form a closed allowlist. Native shell
rules also support prefixes and normalized wrappers; they cannot replace the
guard's literal-match contract. This report concerns the observed CLI; rerun
the harness after an upgrade rather than carrying this as global policy.

## Stop and residual

Do not enable reviewer bypass mode to obtain a verdict. The guard now converts
symlink loops, unreadable files and interpreter-level evaluation/input errors
into typed denial (exit 2), and its Git invocations disable lazy fetch. A Python
startup failure cannot be caught by Python guard code; the retained native Bash
deny protects shell execution independently. Native read permissions do not
replicate the guard's tracked-path containment if hooks fail.

One residual remains: an execution-capable read-only reviewer completing
literal shell inspection with an independent fail-closed backstop. Owner:
`claude-infra`. The driver must escalate the observed native incompatibility;
no OS sandbox design, live-model held-out review, independent approval, CI,
merge or deployment is certified by these deterministic probes.
