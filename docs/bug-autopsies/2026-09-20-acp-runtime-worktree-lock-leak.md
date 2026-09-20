# Bug Autopsy: killed ACP ask leaks a locked runtime worktree the reaper cannot clear

Issue: #8344 (reproduced 2026-09-20).

## Symptom

An `ask-kimi` ACP call (task `plan-consult-8329-kimi`) was stopped with
SIGTERM. It left `.worktrees/dispatch/acp/runtime-plan-consult-8329-kimi-a345eedf0e`
behind: detached, no-checkout, 8 KB, **locked** with reason
`active ACP execution plan-consult-8329-kimi`, and no process holding it.
`reap_worktrees --dry-run` reported `skipped … detached HEAD unknown`;
`post_task_reap` no-oped because ACP asks have no delegate task file. The
stub had to be unlocked and removed by hand. Every cancelled ask leaked one.

Sibling of the same class, found the same day: unregistered zero-file
placeholder directories (`.worktrees/dispatch/codex/1476-auto-path`,
`ww-bare` — empty `site/ node_modules/ data/` trees from 2026-08-23) that the
reaper never sees because it iterates `git worktree list`.

## Root cause

`acp_execution_cwd` created and locked the runtime worktree and cleaned it up
only in a `finally`. Python's default SIGTERM disposition terminates the
process **without unwinding**, and SIGKILL/OOM/host reboot never unwind — so
the cleanup was skipped in exactly the cancellation modes it existed for.
`git worktree lock` is persistent by design (it survives the process), so the
lock outlived its owner, and nothing recorded **who** the owner was, so no
later process could prove the owner was dead. The reaper had no class for the
shape: detached + no-checkout reads as "dirty/unknown", and the default
merged-PR mode bailed out with `detached HEAD unknown`.

## Class of failure

Persistent out-of-band resource + in-process-only cleanup + no ownership
evidence. The `finally`-only pattern is load-bearing only for exceptions and
SIGINT; it is dead code for SIGTERM/SIGKILL. Any subsystem that locks or
registers a durable resource and relies solely on a context manager to
release it leaks on every hard termination.

## Why the fix is load-bearing, not cosmetic

Three independent layers, each sufficient alone:

1. **Provable ownership** (`scripts/common/acp_runtime_lock.py`): the lock
   reason now carries `owner pid=<pid> start=<process start time>`, readable
   by any later process without the owner's cooperation. Dead = pid absent,
   or pid recycled with a different start time (field 22 of
   `/proc/<pid>/stat`). Hosts without `/proc` degrade to "unknown", never to
   "dead".
2. **Self-healing sweep**: `acp_execution_cwd` sweeps provably-dead ACP
   runtime worktrees on entry, before creating its own; a sweep failure is
   logged and never blocks the ask.
3. **Reaper classes**: a provably-safe class for detached, no-checkout,
   dead-owner `runtime-*` worktrees (legacy no-owner locks only past 24h with
   a conclusive no-live-cwd probe), plus the zero-file husk rule for
   unregistered placeholder directories. Both fail closed: alive/unknown
   owners, unexpected files, and unavailable probes all preserve.

Defence in depth: the ask entry path converts SIGTERM into an orderly unwind
(`SystemExit(143)`, previous handler restored, signal not swallowed) so the
existing `finally` runs when it can — but correctness no longer depends on it.

## Sibling pattern audit

`git worktree lock` (persistent, survives death) is used **only** in
`scripts/ai_agent_bridge/_acp_execution.py`. The other worktree locks in the
tree — `scripts/orchestration/task_family/git_safety.py` (`worktree_lock`,
flock) and the reaper's own `_ReapLock` (fcntl flock) — are kernel-released
when the holding process dies, so they cannot leak this way.
`scripts/fleet/post_task_reap.py` already unlocks before its bounded
state-bound removal path; it was not a leak source, only blind to ACP asks
because they have no delegate task file.
