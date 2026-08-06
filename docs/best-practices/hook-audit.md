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
| `stamp-pytest` every PostToolUse | keep fire-and-forget | skip for Grok | |
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

## Related

- Runbook: `docs/runbooks/grok-hook-profile.md`
- Guardrail lifecycle: always-load rules unchanged; this is harness-local + docs + opt-in timing
- Atlas remains the primary epic objective; this is a side PR
