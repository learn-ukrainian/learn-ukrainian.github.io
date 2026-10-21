# Harness hook audit (2026-08-06)

**Owner:** fleet / harness
**Operator GO:** side project while atlas continues
**Status:** tooling + Grok/Claude split + measured optimizations landed this PR

## Failure mode

Epic drivers (Grok TUI especially) appeared “slow” and machines ran hot. Investigation
showed **hooks are not the main thermal source** (formal CF + desktop apps dominate CPU),
but the **Claude project hook graph is fat** and **Grok inherits it by default** via
compat scanning of `.claude/settings.json`.

## Surfaces

| Surface | Role | Cost class |
| --- | --- | --- |
| `agents_extensions/shared/hooks/*` | Shared scripts | Source of truth for policy |
| `.claude/settings.json` (deploy copy) | Claude Code wiring | **Fat** PreToolUse Bash ×7 + PostToolUse ×4 |
| `agents_extensions/codex/hooks.json` | Codex lifecycle | SessionStart + serialized pre-tool policy |
| Grok native `~/.grok/hooks` | Optional thin Grok hooks | Empty by default |
| Grok Claude-compat | Merges project Claude hooks when trusted | **On by default** — main footgun |
| `.githooks/*` (via `$GIT_COMMON_DIR/hooks`) | Git lifecycle delegators | Low overhead per git action |

## Git hooks and Entire CLI delegator architecture

Tracked hook source files live in `.githooks/` as the single source of truth across all linked worktrees. Historically, `scripts/install_git_hooks.sh` set `core.hooksPath=.githooks`. However, when Entire CLI is enabled (via `.entire/settings.json`), its session lifecycle auto-installs git hook wrappers into whichever directory `core.hooksPath` points at. If `core.hooksPath` points at `.githooks`, Entire overwrites the tracked files and creates untracked artifacts (`*.pre-entire`, `prepare-commit-msg`, `post-rewrite`), leaving the primary checkout dirty and breaking automated dispatch and handoff gates.

To prevent dirty checkout drift while preserving Entire CLI functionality:
- `core.hooksPath` is kept **unset** (or cleared if set to `.githooks`).
- `scripts/install_git_hooks.sh` writes untracked delegator scripts into the Git common hooks directory (`$GIT_COMMON_DIR/hooks/`).
- Each delegator dynamically resolves the current worktree root (`git rev-parse --show-toplevel`) and delegates to `$root/.githooks/<name>` if executable.
- When Entire CLI is present, Entire installs its wrapper at `$GIT_COMMON_DIR/hooks/<name>`. Entire (0.11.5) adds its `# Chain: run pre-existing hook` block, which runs `<name>.pre-entire` as the wrapper's last command, only when `<name>.pre-entire` already exists as Entire writes the wrapper; Entire does not rewrite wrappers on later runs unless one is missing or `entire enable --force` / `entire doctor --force` reinstalls them. The installer detects the `# Entire CLI hooks` marker, places the delegator at `$GIT_COMMON_DIR/hooks/<name>.pre-entire`, and appends Entire's chain block when the wrapper lacks it, so the repo hook's exit status decides the commit or push (#9195). An Entire reinstall regenerates the same bytes (verified against the real 0.11.5 binary, #10846).
- The 0.11.5 block differs from the 0.8.42 one, which installed hosts may still carry and the installer still recognizes: the pre-push wrapper exits first when its Entire command fails (inert once guarded, see below), and the chain sets and exports `ENTIRE_CHAINING_<HOOK>` and skips itself while that variable is set. A git command that a chained repo hook runs therefore does not run the same repo hook again, and tests that drive Entire-chained fixture repositories from inside a hook must drop `ENTIRE_CHAINING_*` from the child environment. Unchained wrapper bytes are identical in 0.8.42 and 0.11.5.
- The installer routes every Entire wrapper's `entire hooks git` call (prepare-commit-msg, commit-msg, post-commit, post-rewrite, pre-push) through `scripts/entire/capture_guard.sh` (#10846). The guard runs Entire only after it proves the routing allowlist, the exact accepted CLI version and the private checkpoint route in `entire status --json`, and it always exits 0. A refused capture or an Entire failure therefore never blocks a commit or push, and the repository gate alone decides. Entire treats the guarded line as current. `entire enable --force` rewrites it, and the installer re-guards it on the next run. The installer refuses, before changing anything, when the hooks directory or any hook path it would write is a symlink, dangling or not.
- `scripts/install_git_hooks.sh --check` is read-only. It fails when the hooks directory or a hook path is a symlink, when an Entire wrapper runs Entire without the capture guard (`UNGUARDED`), and when a stage declared in `.pre-commit-config.yaml` (`default_install_hook_types`, `default_stages`, or a hook's `stages`) has no reachable repo delegator in the effective hooks directory. It reads the stages with a YAML parse (`scripts/pre_commit/declared_hook_stages.py`, project interpreter) and fails closed when the config cannot be parsed or names an unknown stage.

## Keep / drop matrix

| Hook / class | Keep for Claude | Keep for Grok | Notes |
| --- | --- | --- | --- |
| `guard-primary-checkout-write` | yes | yes (if any Grok hooks) | Safety |
| `audit-primary-checkout-dirt` Pre/PostToolUse(Failure) (Bash only) | yes | skip for Grok | fail-open attribution of primary dirt (#11253) |
| `guard-secret-print` | yes | yes | Safety |
| `guard-pr-merge` / `guard-admin-merge` | yes (Bash) | optional | gh merge path |
| `guard-branch-switch-in-main` | yes | optional | |
| `enforce-venv` / `heal-core-bare` | yes | optional | cheap |
| `session-setup` | yes (Claude) | thin or skip if no epic | ~1s cold |
| `post-compact` full scan | yes (Claude epic) | **skip** when Grok + no `SESSION_EPIC` | ~2s → ~0 |
| `context-monitor` every tool | yes (Claude) | **skip** for Grok unless `GROK_CONTEXT_MONITOR=1` | high frequency |
| `stamp-pytest` PostToolUse/PostToolUseFailure (Bash only) | keep fire-and-forget | skip for Grok | |
| Entire CLI hooks | no-op if missing | no-op | still spawn shell — OK |
| Auto-audit FileChanged curriculum | Claude only | off | |

## Grok profile (enforced recommendation)

```toml
# ~/.grok/config.toml  (apply with scripts/hooks/apply_grok_hook_profile.py --apply)
[compat.claude]
hooks = false
```

Then restart Grok. Project trust remains for MCP; Claude seats keep their own stack.

Helper:

```bash
.venv/bin/python -m scripts.hooks.apply_grok_hook_profile          # dry-run
.venv/bin/python -m scripts.hooks.apply_grok_hook_profile --apply   # write
```

## Instrumentation

```bash
export HOOK_TIMING=1
export HOOK_TIMING_LOG=batch_state/hook-timing.jsonl   # optional
# wrap any hook:
./scripts/hooks/run_hook_timed.sh path/to/hook.sh
# or:
.venv/bin/python -m scripts.hooks.hook_timing wrap -- bash path/to/hook.sh
```

## Measure harness

```bash
.venv/bin/python -m scripts.hooks.measure_hook_stack --repeats 3 \
  --out batch_state/hook-audit-measure.json
```

Reports median ms per hook and the **Claude Bash PreToolUse tax** (sum of the 7 guards).

## Measured results (2026-08-06, this machine)

### Stack inventory (`measure_hook_stack`, worktree + primary venv)

| Hook | Median ms (after PR) |
| --- | ---: |
| session-setup.sh | ~560–1000 (varies with load) |
| Claude Bash PreToolUse tax (7 guards sum) | **~162** |
| codex_hook_entry pre-tool-use | ~84 |
| Individual guards | ~19–37 each |

### Grok-targeted optimizations (fair compare: `SESSION_EPIC=atlas`, primary `CLAUDE_PROJECT_DIR`)

| Path | Before (ms) | After (ms) | Result |
| --- | ---: | ---: | --- |
| **post-compact** (Grok + epic) | **1213** | **6** | **~199× faster** (~1.2 s saved per compact) |
| **context-monitor** (Grok) | **7.4** | **2.8** | early skip |

These are the high-frequency / high-spike fixes. Disabling Claude-compat hooks for Grok
(`apply_grok_hook_profile --apply`) removes the **~162 ms/Bash** PreTool tax entirely for
the Grok seat (Claude seats unchanged).

## Fail-closed PreToolUse guards (2026-10-16, #10848)

### Policy

Claude Code lets a tool call proceed when its PreToolUse command hook times out, crashes,
cannot start, exits with a code other than 0 or 2, or prints invalid JSON. The hooks
reference says: "To block the call when a `command` or `http` hook times out, set
`onFailure: "block"`" (Claude Code 2.1.295 or later; the default is `"continue"`).
Under host load the guards used to time out, and the tool then ran unguarded.

- Every refusing guard in `agents_extensions/shared/settings.json` sets
  `"onFailure": "block"`: `enforce-venv.sh`, `guard-branch-switch-in-main.py`,
  `guard-admin-merge.py`, `guard-pr-merge.py`, `guard-secret-print.py`,
  `guard-primary-checkout-write.py` (Bash and Write/Edit/MultiEdit) and
  `guard-public-github-text.py`.
- Timeouts are 10 s for the local guards and 30 s for the two merge guards, which call
  GitHub. Both are well above 4 × the loaded p99 below.
- `heal-core-bare.py` stays fail-open. It refuses nothing, and blocking every git command
  because a repair helper stalled would wedge the session. It now reads the shared git
  config in-process and starts the checker only when `core.bare` may be on.
- SessionStart, PostToolUse, UserPromptSubmit, Stop and the Entire hooks stay fail-open.
- `tests/test_hook_failure_policy.py` enforces all of this. A new `guard-*.py` entry fails
  the test until it is added to the fail-closed list.
- A live Claude Code 2.1.301 canary (opt-in test, `LU_LIVE_CLAUDE_HOOK_CANARY=1`) confirmed
  the behaviour. A stub hook that outlived its timeout blocked the Bash call only with
  `onFailure: "block"`; without the field the command ran. Both cases are tests.
- The SchemaStore `claude-code-settings.json` schema (fetched 2026-10-16) predates
  `onFailure` and does not list it, so a strict validator reports these entries as
  unknown. Claude Code itself accepts the field, as the live canary shows.

### Measured latency (ms, spawn to exit, 200 calls per row)

Host: 16 CPUs. "Ambient" is load 12–20. "Loaded" adds 16 busy loops, bringing load to about 40.
"Group" runs the eight Bash hooks of one call in parallel, as Claude Code does. The guards
run through `#!/usr/bin/env python3` (the project venv, Python 3.12) with
`PYTHONDONTWRITEBYTECODE=1` and the agent command shims first on PATH, as in agent sessions.

| Hook | Ambient p50 / p99 before | Ambient p50 / p99 after | Loaded group p99 before | Loaded group p99 after | Loaded seq p99 after |
| --- | ---: | ---: | ---: | ---: | ---: |
| enforce-venv.sh | 13 / 20 | 16 / 33 | 963 | 230 | 111 |
| heal-core-bare.py | 53 / 242 | 49 / 97 | 1299 | 377 | 596 |
| guard-branch-switch-in-main.py | 93 / 129 | 59 / 95 | 1216 | 931 | 417 |
| guard-admin-merge.py | 52 / 75 | 52 / 82 | 830 | 685 | 273 |
| guard-pr-merge.py | 59 / 87 | 64 / 98 | 924 | 679 | 507 |
| guard-secret-print.py | 60 / 93 | 63 / 116 | 1197 | 886 | 286 |
| guard-primary-checkout-write.py (Bash) | 145 / 172 | 151 / 217 | 1190 | 666 | 447 |
| guard-public-github-text.py | 53 / 69 | 60 / 122 | 665 | 510 | 286 |
| Whole Bash group | 173 / 240 | 180 / 294 | 2193 (max 3355) | 1096 (max 1789) | — |

Ambient load rose from 13 to 20 between the before and after runs, so compare the ambient
columns loosely. Interpreter start-up is about 20 ms (`python3 -c pass`), or 11 ms with
`-S`. That flag is not used: under `-S`, `guard-pr-merge.py` loses its merge-readiness
dependency and refuses every merge, and the gain is small next to the tail. A bytecode cache outside the hooks directory
was rejected, because a writable cache would let a same-user process replace guard code.

A second sequential run on the final code (200 calls per guard, no command shims on PATH)
gave these p50 / p99 values. The ambient run had load 15–18. The loaded run added 16 busy
loops, for load 23–33.

| Hook | Ambient p50 / p99 | Loaded p50 / p99 (max) |
| --- | ---: | ---: |
| enforce-venv.sh | 14 / 19 | 32 / 238 (248) |
| heal-core-bare.py | 44 / 64 | 95 / 215 (217) |
| guard-branch-switch-in-main.py | 60 / 86 | 126 / 310 (356) |
| guard-admin-merge.py | 56 / 96 | 107 / 228 (253) |
| guard-pr-merge.py | 74 / 133 | 126 / 258 (807) |
| guard-secret-print.py | 64 / 146 | 118 / 530 (1159) |
| guard-primary-checkout-write.py (Bash) | 100 / 128 | 208 / 582 (907) |
| guard-public-github-text.py | 47 / 69 | 106 / 310 (1185) |

Interpreter start-up was 18 ms in the ambient run and 55 ms in the loaded run.

Changes behind the "after" columns:

- `guard-branch-switch-in-main.py` resolves the protected roots on first use and skips the
  repository probes for git verbs that it can never refuse. A plain `ls` or `git status`
  now spawns no git.
- `guard-primary-checkout-write.py` and the branch guard send their own read-only git
  probes to the real git instead of the agent shim (5 processes per call). If no other git
  is on PATH they keep the shim.
- `enforce-venv.sh` blocks when its payload cannot be read (for example, `jq` is missing).
  Before, it let every command through.

### Incident evidence

In the 2026-10-16 driver session, 35 Bash calls had PreToolUse hooks cancelled. Each
cancellation fired 0.3–2.7 s after its deadline, so the harness itself was late. Ten calls
had a hook still pending after more than 10 s. Six had one pending after more than 30 s,
including the merge guards, which exit in about 60 ms on a non-merge command. Those are
whole-process stalls. Under fail-closed such a call is now refused and the agent retries.
Before, the call ran unguarded.

### Other harnesses

| Harness | Hook surface | Failure semantics (official docs) | Enforced fail-closed | Only documented or unknown |
| --- | --- | --- | --- | --- |
| Claude Code (seats and dispatch workers) | `.claude/settings.json` PreToolUse; workers get the same entries through `adapters/claude.py` | Timeout, crash, failure to start, other exit codes and invalid JSON let the call proceed unless `onFailure: "block"` | Every refusing guard sets `onFailure: "block"`, including the reviewer publish guard that `adapters/claude.py` adds to read-only runs (10 s; loaded p99 226 ms); live canary blocks a timed-out guard | None known for this surface |
| Grok dispatch workers | Agent definitions from `adapters/grok_build.py`, each guard behind `grok_hook_bridge.py` | Grok 1.0.62: "All hook failures (timeouts, crashes, malformed output) are fail-open"; a hook that cannot start fails open "even for a deny hook" | The bridge turns a guard that runs past 10 s, crashes or exits non-zero into a deny, before Grok's 15 s or longer timeout (tested) | A bridge that stalls or cannot start fails open; no Grok setting closes this |
| Grok interactive seats | Project `.claude/settings.json` merged as Claude-compat hooks, or none once `apply_grok_hook_profile` turns compat off | As above; `onFailure` is not a Grok field | Nothing | Residual: guards are fail-open, or absent under the recommended profile (strict-xfail test). No compensating control is verified here |
| Codex | `codex/hooks.json` → `codex_hook_entry.sh` → `codex_hook_policy.py` | No documented rule for a timed-out or crashed command hook | The policy runner turns each guard deadline into exit 2, a refusal (tested); the 45 s entry timeout exceeds the 39 s inner chain (tested) | What Codex does when the 45 s outer timeout fires is undocumented, so an entry-script stall is uncovered |
| Antigravity (AGY) | `agy/hooks.json`, secret guard only | Only a `deny` decision blocks | `secret_print_hook.py` returns a deny at 5 s, before the 10 s hook timeout (tested) | Timeout and crash disposition is unknown; no coverage is claimed for a wrapper stall |
| Cursor | No native guard config is tracked; Cursor can read project `.claude/settings.json` as third-party hooks | Exit codes other than 0 and 2 "fail open by default unless `failClosed: true`" | Contract test: any tracked Cursor `hooks.json` guard must set `failClosed: true` | Whether Cursor honours `onFailure` in the Claude settings is unverified |
| Gemini CLI | Not used (Gemini runs through AGY) | Other exit codes are "Non-fatal ... proceeds" | Not applicable | Not applicable |

## Related

- Runbook: `docs/runbooks/grok-hook-profile.md`
- Guardrail lifecycle: always-load rules unchanged; this is harness-local + docs + opt-in timing
- Atlas remains the primary epic objective; this is a side PR
