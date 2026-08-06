# Grok hook profile runbook

## Why

Grok Build discovers hooks from multiple places. By default it also scans **Claude Code**
project settings (`.claude/settings.json`). This repo’s Claude settings attach a **large**
PreToolUse/PostToolUse graph optimized for Claude epic driving — not for Grok TUI latency.

## Recommended profile (operator 2026-08-06)

1. **Disable Claude-compat hooks for Grok** (does not affect Claude CLI seats).
2. Keep safety where needed via thin native Grok hooks later if required.
3. Restart Grok after config change.

### Apply

```bash
# from repo root
.venv/bin/python -m scripts.hooks.apply_grok_hook_profile           # dry-run
.venv/bin/python -m scripts.hooks.apply_grok_hook_profile --apply    # write ~/.grok/config.toml
```

Manual equivalent — append to `~/.grok/config.toml`:

```toml
[compat.claude]
hooks = false
```

### Verify

- `/hooks` (or Ctrl+L → Hooks) should no longer list the full Claude PreToolUse stack.
- SessionStart should not run the full Claude `session-setup` path unless you re-enable compat.

## Shared script optimizations (all harnesses)

These are **safe for Claude** and help Grok if compat hooks remain on:

| Change | Behavior |
| --- | --- |
| `post-compact.sh` | Exits immediately when `GROK_AGENT` / `SESSION_HANDOFF_AGENT=grok` and no `SESSION_EPIC` |
| `context-monitor.sh` | Skips for Grok unless `GROK_CONTEXT_MONITOR=1` |

## Measure

```bash
.venv/bin/python -m scripts.hooks.measure_hook_stack --repeats 3
# compare post-compact vs post-compact+GROK_SESSION medians in the JSON report
```

## Rollback

Remove or set `hooks = true` under `[compat.claude]`, restart Grok.
