# `ab discuss` Filesystem Sandbox Audit

**Issue:** #1702
**Date:** 2026-05-06
**Scope:** `scripts/agent_runtime/adapters/{gemini,claude,codex}.py`
as invoked by `ab discuss` and channel deliveries.

## Finding

Before this change, `ab discuss` requested `mode="read-only"`, but the
three adapters did not provide equivalent filesystem protection:

- `CodexAdapter` mapped read-only to `codex exec -s read-only`, which is
  an explicit Codex sandbox.
- `GeminiAdapter` treated read-only as the Gemini CLI default. The CLI
  supports `--approval-mode plan` for read-only planning, but the adapter
  only used `--approval-mode=yolo` for write modes and did not force plan
  mode for discussion.
- `ClaudeAdapter` documented that read-only and workspace-write used the
  same Claude Code invocation unless the caller supplied restrictive tool
  config. Claude Code now exposes `--permission-mode plan` and tool-set
  restriction flags that were not used for discussion calls.

`ab post` itself stores a message and delivery rows; the actual agent
execution happens later in the inbox worker. Delivery mode defaults to
read-only, and the inbox worker now applies the same discussion read-only
tool config to those default deliveries. Explicit write-capable modes
remain available for messages that are intentionally execution requests.

## Policy

Discussion is read-only. Agents may inspect and recommend; they must not
create, edit, delete, stage, commit, or push files. Write-capable work
belongs in an explicit execution path such as `delegate.py dispatch`.

## Implementation

`ab discuss` now marks runtime calls with discussion read-only tool config.
Adapters honor that signal and the `AB_DISCUSS_READONLY=1` environment
flag:

- Codex rejects non-read-only discussion invocations and propagates the
  environment flag to the child process.
- Gemini rejects non-read-only discussion invocations and adds
  `--approval-mode plan`.
- Claude rejects non-read-only discussion invocations and adds
  `--permission-mode plan --tools Read,Grep,Glob,LS`.

The bridge also snapshots git state before each discussion round and checks
it after all participants return. If the snapshot changed, the bridge posts
a warning into the thread, rejects that round's replies, and exits non-zero.
