# `needs_finalize` misses committed-but-unpushed dispatches (3/3 this session, not agent-specific)

**Date:** 2026-08-25
**Issue:** #7311
**Category:** agent-dispatch / silent-exit-unpushed
**Tool:** `scripts/delegate.py` (`needs_finalize` finalize gate, ~line 4680-4703)
**Impact:** Every write-capable dispatch in one monitor-epic session (3/3 — two `--agent cursor
--mode danger`, one `--agent agy --mode workspace-write`) settled `status: done` with real work
committed locally but never pushed and no PR opened — caught only by the existing manual "check
the worktree" driver protocol, not by the harness itself. Confirmed NOT agent- or mode-specific.

## What broke

Three consecutive write-capable `scripts/delegate.py dispatch` tasks in the same monitor-epic
session — `monitor-7269-step05-router-inventory` and its follow-up
`monitor-7269-step05-router-inventory-fix1` (both `--agent cursor --mode danger`), then
`monitor-7295-epics-graph-endpoint` (`--agent agy --mode workspace-write`) — all three settled
`status: done` with `pr_url: null`, `pr: null`, `branch: null`. In every case the worker had
actually done the requested work and committed it locally on the dispatch branch, with green
tests confirmed by the driver afterward — but the commit never reached `origin`, and no PR was
ever opened. Two different agents, two different write modes, same failure shape: this rules out
a cursor-specific or danger-mode-specific cause and points at the shared finalize logic. The
driver caught all three only by following the existing manual protocol ("before declaring a
dispatch dead: `gh pr list` first, then check the worktree for finished-but-unpushed work") — a
workaround that exists specifically because this class of failure was already known, but whose
root cause had not been isolated in delegate.py itself.

## Why

`scripts/delegate.py`'s finalize step (~line 4680-4703) decides whether a write-capable dispatch
needs human/driver attention with:

```python
commits_ahead = _count_commits_ahead(Path(worktree_path), base_ref)
if dirty_on_exit in (True, None) and commits_ahead in (0, None):
    needs_finalize = True
```

`_count_commits_ahead` counts commits ahead of the **base branch** (`main`), not ahead of the
dispatch branch's own remote tracking ref. A worker that commits locally but never pushes has:

- `dirty_on_exit = False` — the working tree is clean, everything is committed.
- `commits_ahead >= 1` relative to `main` — the local commit is real, different content than base.

Both conditions read as "real work exists," so `needs_finalize` never fires and the task settles
as plain `done`. The check conflates two genuinely different questions: *does this commit differ
from the base branch* (yes — that's what `commits_ahead` measures) versus *did this commit ever
leave the local worktree* (unmeasured). A worker can satisfy the first without ever attempting
the second.

This reproduced identically three times in one session across two different agent CLIs and two
different write modes, with no code difference in delegate.py between the runs — ruling out a
single worker's idiosyncrasy as the explanation. Both underlying CLIs are configured as
technically capable of `git push` / `gh pr create` in their respective modes (confirmed live for
cursor's danger-mode adapter path in `scripts/agent_runtime/adapters/cursor.py`); each apparently
stopped after the local commit anyway, for reasons outside delegate.py's visibility. Whatever the
worker-side cause, the finalize logic should catch the *symptom* — nothing published — regardless
of which agent or mode produced it, and currently does not.

## Prevention

Filed as [#7311](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/7311)
(infra-lane owned — `scripts/delegate.py` is shared tooling, not monitor-epic scope). Proposed
fix: add a second, independent `needs_finalize` trigger — commits ahead of the branch's own
`@{upstream}` / `origin/<branch>` ref (or local HEAD unreachable from the pushed remote) — that
fires for write-capable modes regardless of the base-branch-ahead count. The two checks are
orthogonal: a dirty tree and a clean-but-unpushed tree are both "not actually shipped" states,
and only the first is currently covered.

Until fixed: **`status: done` from ANY write-capable dispatch is not proof the work was
published**, not just cursor's. Every dispatch finalize must still run `gh pr list --state open`
/ check the worktree branch's push state before treating `done` as terminal-success — the
existing driver protocol note is correct and remains load-bearing until #7311 closes.
