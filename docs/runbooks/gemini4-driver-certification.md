# Gemini 4 Argon driver launcher certification

Issue #10568 extends `start-gemini-driver.sh` to accept the direct AGY selector
`gemini-4-argon-high` and use it as the driver default. The interactive launcher
still defaults to `gemini-3.8-flash-high`. Explicit driver selections of
`gemini-3.8-flash-high` and the previously certified `gemini-3.1-pro-high` remain
accepted. Certification does not prove that a selector is installed. Check
`agy models` before any authorized provider run.

## Verify the launcher without starting a seat

Run these commands from the dispatch worktree with the prescribed shared project
interpreter. Every launcher command below sets `LAUNCHER_DRY_RUN=1`.

```bash
LAUNCHER_DRY_RUN=1 ./start-gemini-driver.sh --epic monitor --model gemini-4-argon-high
LAUNCHER_DRY_RUN=1 ./start-gemini-driver.sh --epic monitor
LAUNCHER_DRY_RUN=1 ./start-gemini-driver.sh --epic monitor --model gemini-3.8-flash-high
bash -n scripts/lib/launcher_core.sh start-gemini-driver.sh
```

The Argon commands must print `would exec agy --model gemini-4-argon-high`.
The Flash control must print `would exec agy --model gemini-3.8-flash-high`.
Each command must keep the driver binding in the interactive prompt and report
the monitor identity with `agent=gemini harness=agy` and `slot=gemini-monitor`.
The output describes scope entry, deployment and lease acquisition without
performing them. The adapter reports `provider canary: not run`.

For argument-boundary proof, set `LAUNCHER_DRY_RUN_ARGV_FILE` to a private scratch
file. It receives the exact NUL-separated argv, including the rules core and
driver prompt. Treat that file as local evidence and do not publish its contents.

## Refusal checks

The driver must exit with code 4 before scope entry or startup for:

- Argon low, medium, bare or provider-prefixed selectors.
- Unknown models or models from another provider.
- A forwarded `--model` or `--model=...` after `--`, even if its value is certified.

Other provider drivers must also reject `gemini-4-argon-high` and its
`gemini:`-prefixed spelling. The Gemini launcher continues to reject harnesses
other than `agy`. Safe forwarded arguments retain their boundaries after the
driver binding. The launcher does not add `--dangerously-skip-permissions`.

`tests/test_start_gemini_launcher.py` checks the Argon explicit and default paths,
the exact NUL-separated argv, the Flash control, wrong-provider and forwarded
model refusals. Its monitor dry-run fixture traps scope, deployment, supervisor
and AGY execution. `tests/test_launcher_driver_scope.py` checks that unsupported
Argon selectors and provider spoofing refuse before memory-scope entry.

## Integration and actual restart

The launcher unit and the model-data companion belong in one integrated #10568
PR. The driver owns serial publication, final integrated tests and dry-launch
proof, and independent exact-head critical review by qualified Opus through the
supported AGY route. Local launcher tests do not supply that independent review.

Actual driver switching still depends on AGY reliability and read-only hardening
#10563 and the orders hook #10558. Restart and lease handling remain under the
driver and operator's control. This procedure grants no authorization for a real
startup, seat switch, hook change or lease mutation.
