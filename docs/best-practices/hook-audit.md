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
- When Entire CLI is present, Entire installs its wrapper at `$GIT_COMMON_DIR/hooks/<name>`. Entire (0.8.42) adds its `# Chain: run pre-existing hook` block, which runs `<name>.pre-entire` as the wrapper's last command, only when `<name>.pre-entire` already exists as Entire writes the wrapper; Entire does not rewrite wrappers on later runs. The installer detects the `# Entire CLI hooks` marker, places the delegator at `$GIT_COMMON_DIR/hooks/<name>.pre-entire`, and appends Entire's chain block when the wrapper lacks it, so the repo hook's exit status decides the commit or push (#9195). An Entire reinstall regenerates the same bytes.
- `scripts/install_git_hooks.sh --check` is read-only and fails when a stage declared in `.pre-commit-config.yaml` (`default_install_hook_types`, `default_stages`, or a hook's `stages`) has no reachable repo delegator in the effective hooks directory. It reads the stages with a YAML parse (`scripts/pre_commit/declared_hook_stages.py`, project interpreter) and fails closed when the config cannot be parsed or names an unknown stage.

## Keep / drop matrix

| Hook / class | Keep for Claude | Keep for Grok | Notes |
| --- | --- | --- | --- |
| `guard-primary-checkout-write` | yes | yes (if any Grok hooks) | Safety |
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
  `onFailure: "block"`; without the field the command ran.

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

| Harness | Hook surface | Failure semantics (official docs) | Fail-closed setting | State |
| --- | --- | --- | --- | --- |
| Claude Code | `.claude/settings.json` PreToolUse | Timeout, crash and other failures let the call proceed | `onFailure: "block"` | Set on every refusing guard |
| Claude and Grok dispatch workers | Built from the shared settings by `adapters/claude.py` | As above / Grok: "timeouts, crashes, malformed output — is fail-open" | Claude: inherited. Grok: none; `grok_hook_bridge.py` denies at 10 s, before Grok's 15 s or longer timeout | Covered. Residual: the reviewer publish guard is added with timeout 5 and no `onFailure` |
| Codex | `codex/hooks.json` → `codex_hook_policy.py` | No documented rule for a timed-out or crashed command hook; managed PreToolUse "error, timeout, or malformed response can fail the hook without blocking the tool" | None documented | The policy runner turns each guard deadline into a refusal; the 45 s entry timeout exceeds the 39 s inner chain (tested). An entry-script stall is uncovered |
| Antigravity (AGY) | `agy/hooks.json`, secret guard only | Only a `deny` decision blocks; failure behaviour is undocumented | None documented | `secret_print_hook.py` denies at 5 s, before the 10 s hook timeout (tested). A wrapper stall is uncovered |
| Cursor | Reads `.claude/settings.json` as third-party hooks | "Other exit codes: Hook failed, action proceeds (fail-open)"; whether `onFailure` is honoured is undocumented | Native `failClosed: true` per script | Unverified. No tracked native Cursor guard config exists |
| Gemini CLI | Not used (Gemini runs through AGY) | Other exit codes are "Non-fatal ... proceeds" | None documented | Not applicable |

## Related

- Runbook: `docs/runbooks/grok-hook-profile.md`
- Guardrail lifecycle: always-load rules unchanged; this is harness-local + docs + opt-in timing
- Atlas remains the primary epic objective; this is a side PR
