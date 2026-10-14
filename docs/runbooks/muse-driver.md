# Muse DevOps and Harness/monitor driver trial

`start-muse-driver.sh` prepares the native Muse CLI through the shared launcher
core for exactly the canonical stream keys `devops` and `monitor`. DevOps accepts
`devops` and `infra.devops`; monitor accepts `monitor`, `infra.monitor`, `ops-api`,
`ops.api` and `operator-api`. The existing taxonomy resolves their streams and
slots to `muse-devops` and `muse-monitor`. The Harness/monitor seat name does not
rename the separate `infra-harness` stream: `harness`, `infra` and
`infra.fleet-comms` remain refused. Every non-Muse roster entry is unchanged.
Legacy Claude, Codex, Gemini, Grok, Kimi and Cursor monitor identities continue
to use their bare-provider inboxes. The dedicated `muse-monitor` inbox remains
separate, and registered slots take precedence over legacy aliases.

The ordered launcher pin is `muse-wonder-full-1.0`, with high effort by default.
The previous `muse-spark-1.3` pin and every other pin refuse. This repair grants
no new review or approval authority and changes no routing ladder, catalog seat
or fallback selection. Provider flags, forced takeovers and lease disabling refuse.

## Installed CLI evidence

These prior CLI inspections describe the interface, not certification of the
ordered full pin. This repair runs no provider probes. The full pin and native
guards remain unproven for real sessions. These read-only commands make no
model request. Set
`MUSE_NO_AUTO_UPDATE=1` to keep the installed executable fixed during inspection.

| Command | Observed result |
| --- | --- |
| `command -v muse` | An installed executable named `muse` resolves. |
| `MUSE_NO_AUTO_UPDATE=1 muse --help` | Interactive TUI by default, with positional prompt; `exec` is headless. Flags include `--provider`, `--model`, `--reasoning-effort`, `--workspace`, `--worktree`, `--config`, `--disable-shell`, `--disable-write`. |
| `MUSE_NO_AUTO_UPDATE=1 muse model-profile --help` | `model-profile show <model> [--effort <tier>]`, with `muse-spark-1.3` as the example catalog id. |
| `MUSE_NO_AUTO_UPDATE=1 muse resume --help` | Picker, `resume --last`, or exact session UUID/name; root options work on either side of `resume`. The launcher refuses resume flags. |
| `MUSE_NO_AUTO_UPDATE=1 muse config --help` | Enterprise defaults/policy validation and `config status`; validation does not accept the user's flat settings document. |

Help lists `none|minimal|low|medium|high|xhigh|max|ultra` for reasoning effort.
The launcher maps these directly to `--reasoning-effort` and refuses other values.
`--config KEY=VALUE` accepts repeatable JSON values and refuses unknown or
clashing keys. The launcher refuses forwarded flags so these cannot replace
its pin, effort or guard configuration. Help exposes no system/append-prompt
option. The planned argv prefixes the positional prompt with the rules core,
then the shared drive-epic binding. Prompt injection is not a guard.

Read the installed bundled documentation without reading saved credentials:

```bash
MUSE_DATA_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/muse"
cat "$MUSE_DATA_ROOT"/plugins/cache/builtin/muse-core/manage-settings/*/SKILL.md
sed -n '80,95p' "$MUSE_DATA_ROOT"/plugins/cache/builtin/muse-core/create-plugin/*/references/native-plugin-contract.md
```

The settings documentation distinguishes saved settings from live runtime
configuration and names the saved `reasoning_effort` key. The native plugin
contract documents a `PreToolUse` hook with structured command argv and a timeout.
It does not establish the hook's forbidden-action refusal contract or prove
compatibility with this repository's hooks. No plugin is installed by this launcher.

## Admission and guard gate

Ukrainian language lanes and curriculum content lanes refuse before any Muse
process. Classification uses the shared lane resolver and driver agent type
classifier that also determines the rules seat. A rules-seat override cannot
hide a curriculum lane.
Only the DevOps and monitor selectors, registered handoff slots and their canonical
streams are admitted.
The checkout's GitHub visibility must resolve to `PUBLIC`; private, internal,
missing and unknown results refuse, including in dry runs.

Every real session currently exits with `MUSE_GUARD_PARITY_UNPROVEN`, before
scope entry, deployment or lease acquisition. The planned argv includes the
native `--disable-shell` and `--disable-write` switches. These advertised switches
do not prove native semantic refusal. Shell, credential, publication, destructive
command and filesystem guard parity remain unproven. Session start, before-prompt,
after-compaction and session-end hook compatibility also remains unproven.
There is no environment override or proof receipt that enables execution.
An adapter's separate admission is not driver certification.

```bash
./start-muse-driver.sh --help
./start-muse-driver.sh --epic monitor --effort high --dry-run
LAUNCHER_DRY_RUN=1 ./start-muse-driver.sh --epic infra.devops
```

Dry runs print the proposed argv and report each unproven guard. They claim no
lease and run no canary. Do not run the printed argv directly.

## Shared lifecycle and recall

The launcher uses the existing core identity, claim, renewal, close and execution
functions; there is no Muse lease implementation. Its identity is `muse-devops`
or `muse-monitor` with harness `muse-cli`. The core writes the session capsule
and lease receipt.
An occupied lease refuses and cannot be forced by this seat. Stub tests exercise
this lifecycle with admission isolated in the fixture; they are not native Muse
guard or runtime certification.

At rollover, `scripts.session_canary.muse_lane mint` and `score` reuse the shared
ten-anchor recall implementation and its fixed 8/10 threshold. The default
handoff preference is `MUSE-DRIVER-HANDOFF.md`, then the interim handoff. A failed
score writes the shared handback and requires driver exit; only the launcher
owns lease closure. The canary never invokes a provider or claims a lease.

Native refusal and lifecycle-hook proof are the remaining prerequisites for a
real supervised trial, owned by the DevOps driver and Muse parity qualification
work under #10511 / #10553. This round makes no model calls. Exact-head independent
cross-family review at critical risk and CI remain landing gates.
