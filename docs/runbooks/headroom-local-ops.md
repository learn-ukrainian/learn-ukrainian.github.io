# Headroom Local Operations

This runbook records the local Headroom proxy settings used on the development
machine and the update automation for the pipx-managed `headroom-ai` install.
The proxy is local runtime infrastructure; do not commit files from
`~/.headroom/`.

## Current Intent

Use Headroom as a CPU-sensitive background optimizer:

- keep proxy compression enabled
- keep provider cache alignment enabled
- use explicit MCP compression for large logs, handoffs, and search output
- disable the memory subsystem for now
- disable Kompress ML compression until resource use is stable
- avoid globally aggressive compression profiles for normal Codex/Claude work

Recent observations before this tuning:

- `headroom perf --hours 24` reported about `4.2%` token savings.
- Cache hit rate was about `94.6%`, so cache behavior was already strong.
- macOS process sampling caught a burst around `491%` CPU, meaning roughly five
  cores busy during a compression spike.

## Proxy Settings

The managed LaunchAgent runs:

```bash
~/.headroom/deploy/default/run-headroom.sh
```

That script should normally stay as the managed wrapper around
`headroom install agent run --profile default`. Persist CPU tuning in the
deployment manifest instead:

```bash
~/.headroom/deploy/default/manifest.json
```

The proxy can be re-applied with memory enabled for experiments:

```bash
headroom install apply --profile default --memory
```

For the normal low-resource profile, leave memory disabled and keep these
environment values under `base_env`:

```bash
HEADROOM_ANTHROPIC_PRE_UPSTREAM_CONCURRENCY=3
HEADROOM_ANTHROPIC_PRE_UPSTREAM_MEMORY_CONTEXT_TIMEOUT_SECONDS=1.0
HEADROOM_MIN_TOKENS=5000
HEADROOM_MAX_ITEMS=25
HEADROOM_DISABLE_KOMPRESS=1
```

The manifest also carries the supported proxy args:

```bash
--anthropic-pre-upstream-concurrency 3
--anthropic-pre-upstream-memory-context-timeout-seconds 1.0
--disable-kompress
```

Do not include `--memory` or `HEADROOM_MEMORY_ENABLED=1` in this low-resource
profile. Keeping memory initialized while disabling automatic memory context
and memory tools has little practical value and still increases resource use.

Restart with launchd if `headroom install restart --profile default` fails on
`kickstart`:

```bash
plist="$HOME/Library/LaunchAgents/com.headroom.default.plist"
domain="gui/$(id -u)"
launchctl bootout "$domain/com.headroom.default" 2>/dev/null || true
launchctl bootout "$domain" "$plist" 2>/dev/null || true
sleep 2
launchctl bootstrap "$domain" "$plist"
```

Verify:

```bash
curl -fsS http://127.0.0.1:8787/health |
  jq '{status, ready, version, runtime: .runtime.anthropic_pre_upstream, memory: .checks.memory, config: {disable_kompress: .config.disable_kompress, memory: .config.memory, min_tokens_to_crush: .config.min_tokens_to_crush, max_items_after_crush: .config.max_items_after_crush}}'
```

## Why These Settings

`HEADROOM_ANTHROPIC_PRE_UPSTREAM_CONCURRENCY=3`

Caps simultaneous Anthropic pre-upstream work. The auto default resolved to `8`
on this machine, which allows multi-core CPU spikes when several requests need
compression or memory-context work. Lowering this to `3` favors desktop
responsiveness over maximum burst throughput.

`HEADROOM_MIN_TOKENS=5000`

Raises the compression threshold from the observed default of `500` tokens.
This skips low- and medium-value compression work where CPU overhead can exceed
the benefit. Very large logs, tool outputs, and handoffs still remain eligible.

`HEADROOM_MAX_ITEMS=25`

Keeps list and JSON compression tighter than the observed default of `50`
retained items without going as sparse as aggressive profiles. If an answer
needs omitted detail, CCR retrieval can recover the original content.

`HEADROOM_DISABLE_KOMPRESS=1`

Disables Kompress ML compression. The proxy still does structural/schema/log
compression and cache alignment, but avoids the expensive ML path that can
drive CPU and memory spikes.

Memory disabled

Memory and compression are separate systems. In low-resource mode, disabling
memory is cleaner than keeping the memory database initialized while preventing
memory context and memory tools from being injected. Re-enable memory only for a
specific experiment or after a Headroom release improves resource behavior.

`HEADROOM_ANTHROPIC_PRE_UPSTREAM_MEMORY_CONTEXT_TIMEOUT_SECONDS=1.0`

Shortens memory-context lookup from the observed default of `2.0` seconds.
This is fail-open: under load, Headroom should omit injected memory rather than
hold a pre-upstream slot and worsen latency.

## Settings To Avoid Globally

Do not enable `agent-90` globally for routine work. It sets:

```bash
HEADROOM_COMPRESS_USER_MESSAGES=1
HEADROOM_COMPRESS_SYSTEM_MESSAGES=1
HEADROOM_MIN_TOKENS=120
HEADROOM_MAX_ITEMS=8
HEADROOM_FORCE_KOMPRESS=1
HEADROOM_ACCURACY_GUARD=strict
```

That profile is useful for a deliberate compression experiment, but it is the
wrong default when the primary concern is CPU usage.

Do not run `headroom learn --apply` unless explicitly requested. It can rewrite
agent instruction files such as `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md`.

## Update Automation

The helper script is:

```bash
scripts/launchd/headroom-update.sh
```

It checks PyPI for the latest `headroom-ai` version, runs
`pipx upgrade headroom-ai` only when a newer version exists, restarts the
`default` persistent Headroom profile, falls back to launchd bootout/bootstrap
if the managed restart fails, and verifies `/health`.

Run it manually:

```bash
scripts/launchd/headroom-update.sh
```

For an installed crontab, copy the script to a stable local runtime path first:

```bash
mkdir -p "$HOME/.headroom/bin" "$HOME/.headroom/logs"
install -m 755 scripts/launchd/headroom-update.sh \
  "$HOME/.headroom/bin/headroom-update.sh"
```

### launchd

Use the disabled template:

```bash
scripts/launchd/com.learn-ukrainian.headroom-update.plist.disabled
```

Install it for the current checkout:

```bash
PROJECT_ROOT="$(pwd)"
sed \
  -e "s#__PROJECT_ROOT__#${PROJECT_ROOT}#g" \
  -e "s#__HOME__#${HOME}#g" \
  scripts/launchd/com.learn-ukrainian.headroom-update.plist.disabled \
  > "$HOME/Library/LaunchAgents/com.learn-ukrainian.headroom-update.plist"

launchctl bootout "gui/$(id -u)" \
  "$HOME/Library/LaunchAgents/com.learn-ukrainian.headroom-update.plist" \
  2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" \
  "$HOME/Library/LaunchAgents/com.learn-ukrainian.headroom-update.plist"
launchctl enable "gui/$(id -u)/com.learn-ukrainian.headroom-update"
```

Kick it once without waiting for the daily schedule:

```bash
launchctl kickstart -k "gui/$(id -u)/com.learn-ukrainian.headroom-update"
```

### crontab Alternative

On systems where cron is preferred:

```cron
15 3 * * * $HOME/.headroom/bin/headroom-update.sh >> $HOME/.headroom/logs/headroom-update.cron.log 2>&1
```

Use `crontab -e` and add the line manually so existing entries are not
overwritten. The active local machine currently uses this crontab form.

The updater uses a lock directory under `~/.headroom/` and writes its PID into
that lock. If the previous process is gone, or if the lock is older than
`HEADROOM_UPDATE_LOCK_TIMEOUT_SECONDS` (`21600` seconds by default), the next
run removes the stale lock and continues.

## Validation

After a restart or upgrade:

```bash
headroom --version
headroom install status
curl -fsS http://127.0.0.1:8787/health | jq '{status, ready, version, runtime, config}'
headroom perf --hours 24
```

Watch these fields:

- `runtime.anthropic_pre_upstream.resolved_concurrency` should be `3`.
- `config.disable_kompress` should be `true`.
- `config.memory` should be `false`.
- `memory.status` should be `disabled`.
- `config.min_tokens_to_crush` should be `5000`.
- `config.max_items_after_crush` should be `25`.
- `runtime.compression_executor.queued` should usually be `0`.
- CPU bursts should be lower than the previous multi-core spikes.
