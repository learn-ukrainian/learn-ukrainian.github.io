# #1395 — Monitor API /api/git/cleanup endpoint

Read `gh issue view 1395` for full context.

## Goal

Add `GET /api/git/cleanup` to the Monitor API that surfaces stale
branches + removable worktrees + reclaimable disk, so operators catch
rot before it piles up.

Right now we have ~8 stale worktrees on disk tonight that I can see:
`.worktrees/scale-{reading-ukrainian,special-signs,stress-and-melody,holidays,my-day,...}` etc. from merged PRs whose branches couldn't be cleaned (checkout-in-use error). The current state is invisible unless you run `git worktree list` manually.

## Endpoint contract

```
GET /api/git/cleanup

{
  "generated_at": "2026-04-23T...",
  "stale_branches": [
    {
      "name": "agent/scale-holidays",
      "upstream_gone": true,
      "merged_to_main": true,
      "last_commit_at": "2026-04-22T...",
      "last_commit_sha": "5d9cc89f35"
    }
  ],
  "removable_worktrees": [
    {
      "path": ".worktrees/scale-holidays",
      "branch": "agent/scale-holidays",
      "clean": true,
      "upstream_gone": true,
      "merged_to_main": true,
      "disk_bytes": 24000000
    }
  ],
  "protected_worktrees": [
    {"path": "/Users/.../learn-ukrainian", "reason": "primary_checkout"}
  ],
  "dirty_worktrees": [
    {"path": ".worktrees/foo", "branch": "foo", "change_count": 3}
  ],
  "total_reclaimable_bytes": 192000000
}
```

Removable = upstream gone OR merged to main AND working tree clean AND
not in a configurable protected set.

## Implementation

1. Put in `scripts/monitor_api/endpoints/git_cleanup.py` (or wherever
   existing state endpoints live — follow the pattern).
2. Use `git worktree list --porcelain` + `git for-each-ref
   --format='%(refname:short) %(upstream:track) %(committerdate:iso8601)
   %(objectname:short)' refs/heads/` + `du -sk` for disk math.
3. Cache with 60s TTL (matches other state endpoints).
4. Add to `GET /api/state/manifest` so agents discover it.
5. Include in the dashboard — small Operator panel at the bottom of
   `localhost:8765/channels.html` (or wherever the dashboard is
   served). Not required if adding a UI panel pushes scope — endpoint
   alone is acceptable.

## Acceptance criteria

- [ ] `curl -s http://localhost:8765/api/git/cleanup` returns a valid
      JSON payload reflecting current `.worktrees/` state.
- [ ] Merged-but-still-present worktrees are listed in
      `removable_worktrees`.
- [ ] Dirty worktrees (uncommitted changes) are NOT in `removable_worktrees`
      — they go in a separate `dirty_worktrees` list.
- [ ] Primary checkout is in `protected_worktrees`, never in removable.
- [ ] `disk_bytes` and `total_reclaimable_bytes` populated correctly.
- [ ] pytest coverage for each category.
- [ ] Entry added to `/api/state/manifest` response.
- [ ] `docs/MONITOR-API.md` updated with the new endpoint + sample payload.

## Worktree

```
git worktree add -b codex/1395-git-cleanup-endpoint .worktrees/codex-1395-git-cleanup-endpoint
cd .worktrees/codex-1395-git-cleanup-endpoint
```

Do NOT auto-merge.

## Hard timeout

3600s (1h).
